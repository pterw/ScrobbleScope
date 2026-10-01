"""The unmatched report check: populated contract, disclosure, and width sweep.

A slice of the frontend gate (F-B21-51). The sweep exists because none of the
gate's viewport profiles lands between 1024px and the two-panel breakpoint,
which is how a 20-36px album title shipped at 1024px (owner ruling
2026-09-13). It also covers two phone widths, where a fourth column once left
the title 51px.

The artist portraits are checked as loaded, shown whole and in their slots,
from URLs of their own: the check once passed while no portrait could ever
load (F-B23-14).

The focus rings of the album title link and the provider badge are judged on
painted pixels, reached by Tab: the text column's overflow clip once cut both
while every computed outline value stayed the same.
"""

from __future__ import annotations

import base64
import json
import re
from urllib.parse import parse_qs, urlparse

from scripts.dev._frontend_gate_colour import _contrast_ratio
from scripts.dev._frontend_gate_results import artwork_radius_failures
from scrobblescope import jobs
from scrobblescope.domain import COVER_WASH_COUNT

#: Narrowest window at which two unmatched panels share a row. Below it each
#: panel takes the full width. Owner ruling, 2026-09-13: at 1024px two panels
#: left the album title 20-36px beside a Results-sized cover.
UNMATCHED_TWO_PANEL_MIN = 1280

#: Two phone widths, then either side of the two-panel breakpoint and the old
#: breakpoint. None of the gate's profiles lands between 1024px and 1280px,
#: which is how the 1024px defect shipped; 320px is narrower than any profile.
UNMATCHED_SWEEP_WIDTHS = (
    320,
    390,
    1024,
    UNMATCHED_TWO_PANEL_MIN - 1,
    UNMATCHED_TWO_PANEL_MIN,
)

#: Least width an album title may get beside its cover. At 1280px two panels
#: gave 103-119px with four columns and give 291px with three; the defect
#: gave 20-36px.
UNMATCHED_MIN_TITLE_WIDTH = 96

#: Phone floors for the album title, which override the one above. A fourth
#: "Reason detail" column took 26-30% of the panel and left the title 51px at
#: 390px; three columns give it 144-160px there (RECONCILIATION section 18).
UNMATCHED_PHONE_TITLE_FLOORS = {320: 70, 390: 140}

#: The two portraits the report's fixture serves. Each has a URL no other
#: image on the page uses: Chromium serves an image whose URL is already in
#: the document's image list whatever `loading` says, so a portrait that
#: shared the covers' URL loaded even while `loading="lazy"` kept every real
#: portrait from ever loading (F-B23-14). Neither is square, so a portrait
#: forced into the square slot changes its proportions.
UNMATCHED_PORTRAITS = {
    "Wide Portrait Artist": (
        "wide",
        "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' "
        "height='200'><rect width='300' height='200' fill='%23c43'/></svg>",
    ),
    "Tall Portrait Artist": (
        "tall",
        "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' "
        "height='300'><rect width='200' height='300' fill='%2334c'/></svg>",
    ),
}

#: Least computed size, in px, of the row note and the attribution text: the
#: 12px floor RECONCILIATION section 1 records for small labels.
UNMATCHED_SMALL_TEXT_FLOOR = 12.0

#: How long the portraits get to load once their rows are in view.
_PORTRAIT_WAIT_MS = 5000

#: The links whose focus ring is judged on painted pixels: a label, the
#: link's selector, and the control just before it in the same row, which is
#: focused by script so that one real Tab press reaches the link. The text
#: column once clipped both rings: the title kept only its bottom edge, the
#: badge its top and right.
_FOCUS_RING_TARGETS = (
    ("album title link", ".album-link", ".rank-link"),
    ("provider badge", ".provider-badge", ".album-link"),
)

#: CSS px of margin around the link's box in each screenshot, room for the
#: ring to paint in.
_FOCUS_RING_MARGIN = 8

#: Summed RGB difference above which a pixel counts as changed.
_FOCUS_RING_DIFF = 24

#: Least number of changed pixels a side of the ring must show. A whole ring
#: changes 60 or more on each side at 1280px; a cut side changes none.
_FOCUS_RING_MIN_PIXELS = 4

_RING_SIDES = ("top", "right", "bottom", "left")

#: The release-scope fixture row served from Deezer (23 plays, the panel's
#: third row by plays), so the report renders a provider badge.
_DEEZER_SCOPE_ROW = 4

#: Decodes the two screenshots of the focused link in the page (the gate has
#: no image library) -- one with the browser's focus ring, one with the ring
#: switched off and everything else identical -- and counts the changed pixels
#: in the four bands outside the link's box. Both shots are focused, so a
#: tint the row gains on focus is in both and cancels: only the ring differs.
#: Pixels inside the box are not counted: the link turns orange and gains an
#: underline on focus whether or not its ring paints.
_RING_PIXELS_JS = """async ({ringed, bare, box, clip, threshold}) => {
    const decode = async data => {
        const bytes = Uint8Array.from(atob(data), c => c.charCodeAt(0));
        const bitmap = await createImageBitmap(new Blob([bytes], {type: 'image/png'}));
        const canvas = document.createElement('canvas');
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
        const context = canvas.getContext('2d');
        context.drawImage(bitmap, 0, 0);
        return context.getImageData(0, 0, bitmap.width, bitmap.height);
    };
    const a = await decode(ringed);
    const b = await decode(bare);
    if (a.width !== b.width || a.height !== b.height) {
        return {error: `screenshots differ in size: ${a.width}x${a.height} `
            + `and ${b.width}x${b.height}`};
    }
    const w = a.width;
    const h = a.height;
    // Screenshot pixels are CSS px times the device scale factor. Round the
    // box outward, so no band holds a pixel the box partly covers.
    const scale = w / clip.width;
    const left = Math.floor((box.left - clip.x) * scale);
    const right = Math.ceil((box.right - clip.x) * scale);
    const top = Math.floor((box.top - clip.y) * scale);
    const bottom = Math.ceil((box.bottom - clip.y) * scale);
    const count = (x0, x1, y0, y1) => {
        let changed = 0;
        for (let y = Math.max(0, y0); y < Math.min(h, y1); y++) {
            for (let x = Math.max(0, x0); x < Math.min(w, x1); x++) {
                const i = (y * w + x) * 4;
                const diff = Math.abs(a.data[i] - b.data[i])
                    + Math.abs(a.data[i + 1] - b.data[i + 1])
                    + Math.abs(a.data[i + 2] - b.data[i + 2]);
                if (diff > threshold) changed++;
            }
        }
        return changed;
    };
    return {
        top: count(left, right, 0, top),
        right: count(right, w, top, bottom),
        bottom: count(left, right, bottom, h),
        left: count(0, left, top, bottom),
    };
}"""


def _unmatched_panel_width_sweep(page) -> list[str]:
    """Resize across the phone widths and the two-panel breakpoint.

    At each width: the panel column count, the album title's room, and the
    corner radius of every cover, placeholder and portrait. Restores the
    original viewport before returning, so later checks on the same page are
    unaffected.
    """
    failures = []
    original = page.viewport_size
    try:
        for width in UNMATCHED_SWEEP_WIDTHS:
            page.set_viewport_size({"width": width, "height": original["height"]})
            # Two frames: one for layout, one for the scale ResizeObserver.
            page.evaluate(
                "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
            )
            sweep = page.evaluate(
                """() => ({
                    columns: getComputedStyle(document.querySelector('.unmatched-groups'))
                        .gridTemplateColumns.split(' ').length,
                    titles: [...document.querySelectorAll('.unmatched-group')].map(group =>
                        group.querySelector('tbody tr .album-info').getBoundingClientRect().width),
                })"""
            )
            expected_columns = 2 if width >= UNMATCHED_TWO_PANEL_MIN else 1
            if sweep["columns"] != expected_columns:
                failures.append(
                    f"unmatched report at {width}px has {sweep['columns']} panel "
                    f"columns, expected {expected_columns}"
                )
            floor = UNMATCHED_PHONE_TITLE_FLOORS.get(width, UNMATCHED_MIN_TITLE_WIDTH)
            narrowest = min(sweep["titles"])
            if narrowest < floor:
                failures.append(
                    f"unmatched album title at {width}px is {narrowest:.0f}px wide, "
                    f"expected at least {floor}px"
                )
            failures.extend(
                artwork_radius_failures(
                    page.evaluate(_ARTWORK_RADII_JS, _UNMATCHED_ARTWORK_SELECTORS),
                    width,
                    "unmatched",
                )
            )
    finally:
        page.set_viewport_size(original)
    return failures


#: Every kind of provider artwork on the unmatched page, by kind. Each kind
#: must be present, so a selector that stops matching cannot pass vacuously.
_UNMATCHED_ARTWORK_SELECTORS = {
    "cover": "img.unmatched-artwork",
    "placeholder": "div.unmatched-artwork:not([data-artist-image])",
    "portrait": ".unmatched-artist-image",
}

#: Kinds whose selector also matches elements the page keeps hidden. The
#: cover's `onerror` fallback is a `div.unmatched-artwork` that stays hidden
#: until its image fails, so the placeholder selector matches it whether or
#: not the visible below-threshold placeholder still exists.
_VISIBLE_ONLY_ARTWORK_KINDS = ("placeholder",)

#: `ARTWORK_RADII_JS` from the results slice, except that a kind in
#: `_VISIBLE_ONLY_ARTWORK_KINDS` counts only the nodes that generate a box.
#: A kind with no visible node is reported absent by `artwork_radius_failures`.
_ARTWORK_RADII_JS = """selectors => Object.fromEntries(
    Object.entries(selectors).map(([kind, selector]) => [kind,
        [...document.querySelectorAll(selector)]
            .filter(node => !VISIBLE_ONLY_KINDS.includes(kind)
                || node.getClientRects().length > 0)
            .map(node =>
            Number.parseFloat(getComputedStyle(node).borderTopLeftRadius) || 0)]))""".replace(
    "VISIBLE_ONLY_KINDS", json.dumps(list(_VISIBLE_ONLY_ARTWORK_KINDS))
)

#: Lets any transition or animation finish, so two screenshots differ only by
#: the focus ring and not by a state still moving toward its final value.
_SETTLE_JS = """() => new Promise(resolve => {
    const deadline = performance.now() + 1500;
    const tick = () => {
        if (document.getAnimations().every(a => a.playState !== 'running')
                || performance.now() > deadline) {
            requestAnimationFrame(() => resolve());
        } else {
            requestAnimationFrame(tick);
        }
    };
    tick();
})"""


#: Reads every coverless placeholder on show: the nodes wearing a wash that
#: have a box and are not a portrait slot already filled by its photograph.
#: A slot whose portrait loaded drops its wash on purpose, so it is not read.
#: A cover <img> wears the wash too (it shows until the picture paints), and a
#: loaded one still has a box and the gradient as its computed background, so
#: it is read like the rest (`tag` tells the judge which is which). The
#: initials' contrast is not read here, but from the tokens.
_COVER_WASH_JS = r"""() => [...document.querySelectorAll('.cover-wash')]
    .filter(node => node.getClientRects().length > 0
        && !node.hasAttribute('data-portrait'))
    .map(node => {
        const style = getComputedStyle(node);
        return {
            image: style.backgroundImage,
            border: Number.parseFloat(style.borderTopWidth) || 0,
            borderColour: style.borderTopColor,
            colour: style.color,
            tag: node.tagName,
            wash: (node.className.match(/cover-wash-(\d+)/) || [])[1] || '?',
        };
    })"""

#: Matches each resolved colour stop in a computed gradient.
_RGB_STOP = re.compile(r"rgba?\([^)]*\)")

#: The initials are small text, so they must clear WCAG AAA (7:1) on both
#: stops of every wash, not just the 4.5:1 floor (owner, 2026-09-30).
_WASH_TEXT_CONTRAST = 7.0

#: Reads the tokens, not the page: the initials' colour (computed on a placeholder
#: node, or the base-content token when none is on show) and both stops of each
#: of the `count` wash pairs, each resolved to a computed ``rgb()`` colour. The
#: hash picks two or three pairs for a page, so judging only the nodes on show
#: would let a pair that is off the page break the line unseen.
_WASH_TOKENS_JS = r"""count => {
    const root = document.documentElement;
    const resolve = value => {
        const probe = document.createElement('span');
        probe.style.color = value;
        root.appendChild(probe);
        const colour = getComputedStyle(probe).color;
        probe.remove();
        return colour;
    };
    const token = name =>
        getComputedStyle(root).getPropertyValue(name).trim();
    const node = [...document.querySelectorAll('.cover-wash')]
        .find(item => item.tagName !== 'IMG' && item.getClientRects().length > 0);
    const stops = [];
    for (let wash = 0; wash < count; wash++) {
        for (const name of ['a', 'b']) {
            const custom = `--ss-wash-${wash}-${name}`;
            stops.push({wash, stop: name, value: resolve(token(custom))});
        }
    }
    return {
        colour: node ? getComputedStyle(node).color
            : resolve(token('--color-base-content')),
        stops,
    };
}"""

_RGB_VALUE = re.compile(
    r"^rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)\s*(?:[,/][^)]*)?\)$"
)


def _channels(colour: str) -> tuple[float, float, float] | None:
    """Return the red, green and blue of a computed ``rgb()``/``rgba()`` colour.

    Anything else (``color(srgb ...)``, a hex string, an empty token) is None, so
    the judge can fail loudly instead of reading its numbers as 0-255 channels.
    """
    found = _RGB_VALUE.match(colour.strip())
    if found is None:
        return None
    red, green, blue = (float(part) for part in found.groups())
    return red, green, blue


def wash_token_failures(reading: dict, label: str) -> list[str]:
    """Judge a `_WASH_TOKENS_JS` reading taken in *label*'s theme.

    Every stop of every wash pair must give the initials 7:1, whether or not the
    pair is on the page.
    """
    text = _channels(reading["colour"])
    if text is None:
        return [f"{label}: unparsed initials colour {reading['colour']!r}"]
    failures = []
    for item in reading["stops"]:
        where = f"{label}: wash {item['wash']} stop {item['stop']}"
        stop = _channels(item["value"])
        if stop is None:
            failures.append(f"{where}: unparsed colour value {item['value']!r}")
            continue
        ratio = _contrast_ratio(text, stop)
        if ratio < _WASH_TEXT_CONTRAST:
            failures.append(
                f"{where} {item['value']} gives the initials {reading['colour']} "
                f"only {ratio:.2f}:1, under {_WASH_TEXT_CONTRAST:g}:1"
            )
    return failures


def cover_wash_failures(readings: list[dict], label: str, forced: bool) -> list[str]:
    """Judge one reading of `_COVER_WASH_JS` taken under *label*'s conditions.

    Normally every coverless placeholder paints a gradient of two different
    colours. Under forced colours the gradient is dropped on purpose (the
    system repaints text and borders, so a pale wash would sit behind light
    text) and the box must stay visible through a painted border. The initials'
    contrast is judged on the tokens, in `wash_token_failures`.
    """
    placeholders = [item for item in readings if item.get("tag") != "IMG"]
    if len(placeholders) < 2:
        return [
            f"{label}: {len(placeholders)} coverless placeholders on show, expected "
            "at least 2 (the below-threshold row and the Deezer row)"
        ]
    failures = []
    seen = {"placeholder": 0, "cover image": 0}
    for reading in readings:
        kind = "cover image" if reading.get("tag") == "IMG" else "placeholder"
        where = f"{label}: {kind} {seen[kind]}"
        seen[kind] += 1
        if reading["border"] < 1 or reading["borderColour"] in (
            "transparent",
            "rgba(0, 0, 0, 0)",
        ):
            failures.append(f"{where} has no visible border")
        stops = _RGB_STOP.findall(reading["image"])
        if forced:
            if stops:
                failures.append(f"{where} still paints a gradient: {reading['image']}")
        elif "linear-gradient" not in reading["image"] or len(set(stops)) < 2:
            failures.append(
                f"{where} does not paint a two-tone gradient: {reading['image']!r}"
            )
    return failures


def _cover_wash_page_failures(page) -> list[str]:
    """Coverless placeholders paint a wash in both themes, a border when forced."""
    failures = []
    original = page.evaluate("document.documentElement.getAttribute('data-theme')")
    washes = {}
    try:
        for theme in ("light", "dark"):
            page.emulate_media(color_scheme=theme)
            page.evaluate(
                "theme => document.documentElement.setAttribute('data-theme', theme)",
                theme,
            )
            readings = page.evaluate(_COVER_WASH_JS)
            failures.extend(cover_wash_failures(readings, f"{theme} theme", False))
            failures.extend(
                wash_token_failures(
                    page.evaluate(_WASH_TOKENS_JS, COVER_WASH_COUNT),
                    f"{theme} theme",
                )
            )
            washes[theme] = [reading["image"] for reading in readings]
            page.emulate_media(forced_colors="active", color_scheme=theme)
            failures.extend(
                cover_wash_failures(
                    page.evaluate(_COVER_WASH_JS), f"forced colours, {theme}", True
                )
            )
            page.emulate_media(forced_colors="null", color_scheme="null")
        if washes["light"] and washes["light"] == washes["dark"]:
            failures.append(
                "coverless washes are identical in the light and dark themes"
            )
    finally:
        page.emulate_media(forced_colors="null", color_scheme="null")
        if original is None:
            page.evaluate("document.documentElement.removeAttribute('data-theme')")
        else:
            page.evaluate(
                "theme => document.documentElement.setAttribute('data-theme', theme)",
                original,
            )
    return failures


def _portrait_failures(page, spotlight_requests: list[str]) -> list[str]:
    """Both portraits load, show whole at their own proportions, in their slots.

    The portrait `<img>` starts hidden, and its `load` event is what reveals
    it. It shipped `loading="lazy"`: a hidden lazy image is never fetched, so
    no portrait ever appeared, and this check passed only because its fixture
    reused the covers' URL (F-B23-14).
    """
    failures = []
    slots = page.locator('[data-reason="no_spotify_match"] [data-artist-image]')
    for index in range(slots.count()):
        slots.nth(index).scroll_into_view_if_needed()
    page.evaluate(
        """timeout => new Promise(resolve => {
            const deadline = performance.now() + timeout;
            const tick = () => {
                const slots = [...document.querySelectorAll(
                    '[data-reason="no_spotify_match"] [data-artist-image]')];
                if (slots.every(slot => slot.dataset.portrait)
                        || performance.now() > deadline) {
                    resolve();
                } else {
                    setTimeout(tick, 50);
                }
            };
            tick();
        })""",
        _PORTRAIT_WAIT_MS,
    )
    portraits = slots.evaluate_all(
        """slots => slots.map(slot => {
            const image = slot.querySelector('.unmatched-artist-image');
            const style = getComputedStyle(image);
            const box = image.getBoundingClientRect();
            const frame = slot.getBoundingClientRect();
            const px = side => Number.parseFloat(style[side]) || 0;
            return {
                artist: slot.dataset.artistName,
                portrait: slot.dataset.portrait ?? null,
                alt: image.alt,
                naturalWidth: image.naturalWidth,
                naturalHeight: image.naturalHeight,
                display: style.display,
                fallbackDisplay: getComputedStyle(
                    slot.querySelector('.unmatched-artwork-fallback')).display,
                width: box.width,
                height: box.height,
                // The drawn picture is the content box: the image carries a
                // 1px hairline, which is not part of the photograph.
                contentWidth: box.width - px('borderLeftWidth') - px('borderRightWidth')
                    - px('paddingLeft') - px('paddingRight'),
                contentHeight: box.height - px('borderTopWidth') - px('borderBottomWidth')
                    - px('paddingTop') - px('paddingBottom'),
                inside: box.left >= frame.left - 0.5 && box.right <= frame.right + 0.5
                    && box.top >= frame.top - 0.5 && box.bottom <= frame.bottom + 0.5,
            };
        })"""
    )
    seen = {portrait["artist"] for portrait in portraits}
    if seen != set(UNMATCHED_PORTRAITS):
        failures.append(
            f"unmatched report portrait slots are {sorted(seen)!r}, "
            f"expected {sorted(UNMATCHED_PORTRAITS)!r}"
        )
    for portrait in portraits:
        artist = portrait["artist"]
        if artist not in UNMATCHED_PORTRAITS:
            continue
        shape, _ = UNMATCHED_PORTRAITS[artist]
        if portrait["naturalWidth"] <= 0:
            failures.append(
                f"unmatched portrait for {artist!r} never loaded "
                f"(naturalWidth 0, display {portrait['display']!r})"
            )
            continue
        shown = (
            portrait["display"] != "none"
            and portrait["width"] > 0
            and portrait["height"] > 0
            and portrait["fallbackDisplay"] == "none"
            and portrait["alt"] == f"{artist} artist portrait"
        )
        if not shown:
            failures.append(
                f"unmatched portrait for {artist!r} loaded but is not shown: {portrait!r}"
            )
            continue
        natural = portrait["naturalWidth"] / portrait["naturalHeight"]
        drawn = portrait["contentWidth"] / max(portrait["contentHeight"], 0.01)
        if abs(drawn - natural) > 0.03 * natural:
            failures.append(
                f"unmatched portrait for {artist!r} is drawn "
                f"{portrait['contentWidth']:.1f}x{portrait['contentHeight']:.1f}px "
                f"from a {portrait['naturalWidth']}x{portrait['naturalHeight']} photo; "
                "expected its own proportions"
            )
        if not portrait["inside"]:
            failures.append(
                f"unmatched portrait for {artist!r} spills out of its slot: "
                f"{portrait['width']:.1f}x{portrait['height']:.1f}px"
            )
        if portrait["portrait"] != shape:
            failures.append(
                f"unmatched portrait slot for {artist!r} is marked "
                f"{portrait['portrait']!r}, expected {shape!r}"
            )

    requested = sorted(
        parse_qs(urlparse(url).query).get("artist", [""])[0]
        for url in spotlight_requests
    )
    if requested != sorted(UNMATCHED_PORTRAITS):
        failures.append(
            "unmatched report did not hydrate each missing artwork once through "
            f"/api/artist_spotlight: {requested!r}"
        )
    return failures


def _provider_unavailable_panel_failures(page) -> list[str]:
    """Judge the fourth panel as rendered: its title, hint and row note.

    The note is the row's own reason, since it says which provider was down;
    the panel's title alone would not.
    """
    locator = page.locator('[data-reason="provider_unavailable"]')
    if locator.count() != 1:
        return ["unmatched report renders no could-not-be-checked panel"]
    panel = locator.evaluate(
        """node => ({
            title: node.querySelector('.unmatched-group-title')
                ?.textContent.trim(),
            hint: node.querySelector('.unmatched-fix-hint')?.textContent.trim(),
            note: node.querySelector('tbody tr .unmatched-row-note')
                ?.textContent.trim(),
            album: node.querySelector('tbody tr .album-info')
                ?.textContent.replaceAll(/\\s+/g, ' ').trim(),
            panels: node.parentElement.getAttribute('data-panels'),
        })"""
    )
    expected = {
        "title": "Could not be checked",
        "hint": "Search again in a few minutes; these albums may match then.",
        "note": "Spotify and Deezer were both unavailable",
        "panels": "4",
    }
    failures = [
        f"unmatched could-not-be-checked panel {claim} is {panel[claim]!r}, "
        f"expected {wanted!r}"
        for claim, wanted in expected.items()
        if panel[claim] != wanted
    ]
    if "Unavailable Album" not in (panel["album"] or ""):
        failures.append(
            "unmatched could-not-be-checked panel does not list the album: "
            f"{panel['album']!r}"
        )
    return failures


def _row_layout_failures(page) -> list[str]:
    """The row note, the stacked threshold figures, and the attribution text.

    The fourth "Reason detail" column is gone (RECONCILIATION section 18): what
    is particular to a row is a note under its artist, and a no-match row,
    whose reason only restates its panel, has none.
    """
    failures = []
    layout = page.evaluate(
        """() => {
            const firstRow = reason => document.querySelector(
                `[data-reason="${reason}"] tbody tr`);
            const note = row => {
                const node = row?.querySelector('.unmatched-row-note');
                if (!node) return null;
                const box = node.getBoundingClientRect();
                const artist = node.previousElementSibling;
                return {
                    text: node.textContent.replaceAll(/\\s+/g, ' ').trim(),
                    size: Number.parseFloat(getComputedStyle(node).fontSize),
                    height: box.height,
                    underArtist: !!artist && artist.classList.contains('truncate')
                        && box.top >= artist.getBoundingClientRect().bottom - 0.5,
                };
            };
            const figures = [...document.querySelectorAll(
                '[data-reason="below_threshold"] .unmatched-threshold')]
                .map(node => node.getBoundingClientRect());
            const separator = document.querySelector(
                '[data-reason="below_threshold"] .unmatched-threshold-sep');
            const attribution = document.querySelector(
                '#unmatched-spotify-attribution .provider-attribution__text');
            return {
                threshold: note(firstRow('below_threshold')),
                release: note(firstRow('release_scope')),
                noMatchNotes: document.querySelectorAll(
                    '[data-reason="no_spotify_match"] .unmatched-row-note').length,
                figures: figures.map(box => ({top: box.top, bottom: box.bottom})),
                separatorWidth: separator ? separator.getBoundingClientRect().width : null,
                attributionSize: attribution
                    ? Number.parseFloat(getComputedStyle(attribution).fontSize) : null,
            };
        }"""
    )
    for panel, wanted in (
        ("threshold", "3 plays and 1 track short"),
        ("release", "Outside selected release scope"),
    ):
        note = layout[panel]
        if note is None:
            failures.append(f"unmatched {panel} row prints no row note")
            continue
        if note["text"] != wanted:
            failures.append(
                f"unmatched {panel} row note is {note['text']!r}, expected {wanted!r}"
            )
        if note["size"] < UNMATCHED_SMALL_TEXT_FLOOR or note["height"] <= 0:
            failures.append(
                f"unmatched {panel} row note is {note['size']}px and "
                f"{note['height']:.1f}px high; expected visible and at least "
                f"{UNMATCHED_SMALL_TEXT_FLOOR:.0f}px"
            )
        if not note["underArtist"]:
            failures.append(f"unmatched {panel} row note is not under the artist")
    if layout["noMatchNotes"]:
        failures.append(
            f"unmatched no-match panel prints {layout['noMatchNotes']} row notes; "
            "its reason only restates the panel"
        )

    figures = layout["figures"]
    if len(figures) != 2 or figures[1]["top"] < figures[0]["bottom"] - 0.5:
        failures.append(
            f"unmatched threshold figures do not stack one to a line: {figures!r}"
        )
    if layout["separatorWidth"] is None or layout["separatorWidth"] > 1:
        failures.append(
            "unmatched threshold separator is "
            f"{layout['separatorWidth']!r}px wide, expected hidden (at most 1px)"
        )
    if (
        layout["attributionSize"] is None
        or layout["attributionSize"] < UNMATCHED_SMALL_TEXT_FLOOR
    ):
        failures.append(
            f"unmatched Spotify attribution text is {layout['attributionSize']!r}px, "
            f"expected at least {UNMATCHED_SMALL_TEXT_FLOOR:.0f}px"
        )
    return failures


#: Switches off every focus indicator the link draws for the second shot: the
#: outline, and a box-shadow some designs use instead. Nothing else changes,
#: so the two shots differ by the ring alone.
_RING_OFF_JS = """selector => {
    const style = document.createElement('style');
    style.id = 'gate-focus-ring-off';
    style.textContent = `${selector}:focus { outline: none !important; `
        + 'box-shadow: none !important; }';
    document.head.appendChild(style);
}"""
_RING_BACK_JS = """() => document.getElementById('gate-focus-ring-off')?.remove()"""


def _ring_side_failures(label: str, width: int, counts: dict) -> list[str]:
    """Name the sides of a focus ring that painted nothing.

    `counts` holds the changed pixels per side, or an `error` from decoding.
    """
    if "error" in counts:
        return [f"unmatched {label} at {width}px: {counts['error']}"]
    bare = [
        side for side in _RING_SIDES if counts.get(side, 0) < _FOCUS_RING_MIN_PIXELS
    ]
    if not bare:
        return []
    return [
        f"unmatched {label} at {width}px: its focus ring paints nothing on its "
        f"{', '.join(bare)} side(s); changed pixels by side {counts!r}"
    ]


def _focus_ring_failures(page) -> list[str]:
    """The album title link's and the provider badge's focus rings paint whole.

    Judged on pixels: each link is reached by a real Tab press and
    screenshotted focused, then screenshotted again, still focused, with its
    focus ring switched off, and every side outside its box must differ
    between the two. Blurring for the second shot would count any tint the
    row gains on focus as a ring. A computed outline cannot see this defect: a ring that a clipping ancestor
    cuts computes the same as one that is whole, and the text column's
    `overflow-hidden` once cut both. The ring is the browser's own, so no
    colour is tested.
    """
    failures = []
    width = page.viewport_size["width"]
    for label, selector, before in _FOCUS_RING_TARGETS:
        found = page.evaluate(
            """([selector, before]) => {
                const target = document.querySelector(selector);
                const start = target?.closest('tr')?.querySelector(before);
                if (!target || !start) return {target: !!target, start: !!start};
                target.scrollIntoView({block: 'center', inline: 'nearest'});
                start.focus({preventScroll: true});
                return {target: true, start: document.activeElement === start};
            }""",
            [selector, before],
        )
        if not (found["target"] and found["start"]):
            failures.append(
                f"unmatched report at {width}px has no {label} ({selector}) "
                f"with a focusable {before} before it in its row: {found!r}"
            )
            continue
        page.keyboard.press("Tab")
        state = page.evaluate(
            """selector => {
                const target = document.querySelector(selector);
                const box = target.getBoundingClientRect();
                const active = document.activeElement;
                return {
                    reached: active === target,
                    active: `${active?.tagName} ${active?.className}`.slice(0, 80),
                    visible: target.matches(':focus-visible'),
                    box: {left: box.left, top: box.top, right: box.right,
                        bottom: box.bottom},
                    viewport: {width: document.documentElement.clientWidth,
                        height: document.documentElement.clientHeight},
                };
            }""",
            selector,
        )
        if not (state["reached"] and state["visible"]):
            failures.append(
                f"unmatched {label} at {width}px is not reached with a visible "
                f"focus by Tab from its row's {before}: focus is on "
                f"{state['active']!r}, :focus-visible {state['visible']!r}"
            )
            continue
        box = state["box"]
        view = state["viewport"]
        x0 = max(0.0, box["left"] - _FOCUS_RING_MARGIN)
        y0 = max(0.0, box["top"] - _FOCUS_RING_MARGIN)
        x1 = min(float(view["width"]), box["right"] + _FOCUS_RING_MARGIN)
        y1 = min(float(view["height"]), box["bottom"] + _FOCUS_RING_MARGIN)
        clip = {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
        # The pointer would otherwise rest wherever the last click left it,
        # and a row's hover state changing between the two shots would be
        # counted as a ring. Park it away from the table and let any
        # transition settle before each shot.
        page.mouse.move(0, 0)
        page.evaluate(_SETTLE_JS)
        ringed = page.screenshot(clip=clip, animations="disabled")
        page.evaluate(_RING_OFF_JS, selector)
        try:
            page.evaluate(_SETTLE_JS)
            bare = page.screenshot(clip=clip, animations="disabled")
        finally:
            page.evaluate(_RING_BACK_JS)
        counts = page.evaluate(
            _RING_PIXELS_JS,
            {
                "ringed": base64.b64encode(ringed).decode("ascii"),
                "bare": base64.b64encode(bare).decode("ascii"),
                "box": box,
                "clip": clip,
                "threshold": _FOCUS_RING_DIFF,
            },
        )
        failures.extend(_ring_side_failures(label, width, counts))
    return failures


def four_panel_stack_failures(boxes: list[dict], max_gap: float) -> list[str]:
    """Judge the boxes of four panels laid out in two tracks: the third panel
    sits directly under the first, and the fourth directly under the third,
    each within `max_gap` px. In a plain two-by-two the tall second panel sets
    the first row's height and leaves a hole under the short first panel."""
    if len(boxes) != 4:
        return [f"unmatched four-panel layout was given {len(boxes)} panels"]
    failures = []
    for lower, upper in ((2, 0), (3, 2)):
        gap = boxes[lower]["top"] - boxes[upper]["bottom"]
        if abs(boxes[lower]["left"] - boxes[upper]["left"]) > 1 or not (
            0 <= gap <= max_gap
        ):
            failures.append(
                f"unmatched panel {lower + 1} is not stacked under panel "
                f"{upper + 1}: {gap:.0f}px below it (at most {max_gap:.0f}px), "
                f"{boxes[lower]['left'] - boxes[upper]['left']:.0f}px to the side"
            )
    return failures


def _four_panel_stack_failures(page) -> list[str]:
    boxes = page.locator(".unmatched-group").evaluate_all(
        """groups => groups.map(group => {
            const box = group.getBoundingClientRect();
            return {left: box.left, top: box.top, bottom: box.bottom};
        })"""
    )
    return four_panel_stack_failures(boxes, max_gap=48)


def check_unmatched_report(page, base_url: str) -> list[str]:
    """Exercise the populated report contract and its ten-row disclosure."""
    job_id = jobs.create(
        {
            "username": "frontend-gate",
            "year": 2025,
            "sort_mode": "playcount",
            "release_scope": "same",
            "min_plays": 10,
            "min_tracks": 3,
            "limit_results": "all",
            "mode": "album",
        }
    )
    failures = []
    spotlight_requests = []

    def fulfill_spotlight(route):
        """Return each artist's own portrait without contacting Spotify."""
        spotlight_requests.append(route.request.url)
        artist = parse_qs(urlparse(route.request.url).query).get("artist", [""])[0]
        _, image_url = UNMATCHED_PORTRAITS.get(artist, (None, None))
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "name": artist,
                    "artist_id": f"artist-{len(spotlight_requests)}",
                    "image_url": image_url,
                    "spotify_url": "https://open.spotify.com/artist/artist-1",
                }
            ),
        )

    spotlight_pattern = "**/api/artist_spotlight?*"
    page.route(spotlight_pattern, fulfill_spotlight)
    try:
        jobs.record_unmatched(
            job_id,
            "below-threshold",
            {
                "album": "Older",
                "artist": "Lizzy McAlpine",
                "reason": (
                    "Played 1234 times across 2 unique tracks; minimum is 1237 "
                    "plays and 3 unique tracks"
                ),
                "reason_code": "below_threshold",
                "shortfall": "3 plays and 1 track short",
                "album_image": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
                "spotify_id": None,
                # Four digits: the widest figure the metric column has to
                # hold ("1234 plays" clipped by 8px on a phone, F-B23-28).
                "play_count": 1234,
                "track_count": 2,
                "failed_thresholds": ["plays", "tracks"],
                "min_plays": 1237,
                "min_tracks": 3,
            },
        )
        play_counts = (5, 29, 11, 23, 7, 17, 13, 19, 3, 2, 27, 9)
        for index in range(1, 13):
            # One Deezer row, third by plays, so a provider badge renders in
            # the ten rows shown before the disclosure.
            # The Deezer row has no cover, so a coverless row from another
            # provider renders its wash for the cover-wash check.
            album_image = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>"
            if index == _DEEZER_SCOPE_ROW:
                provider, spotify_id = "deezer", None
                album_url = f"https://www.deezer.com/album/{9000 + index}"
                album_image = None
            else:
                provider, spotify_id = "spotify", f"scope-album-{index}"
                album_url = f"https://open.spotify.com/album/scope-album-{index}"
            jobs.record_unmatched(
                job_id,
                f"scope-{index}",
                {
                    "album": f"Scope Album {index}",
                    "artist": f"Scope Artist {index}",
                    "reason": "Outside selected release scope",
                    "reason_code": "release_scope",
                    "album_image": album_image,
                    "spotify_id": spotify_id,
                    "provider": provider,
                    "album_url": album_url,
                    "play_count": play_counts[index - 1],
                },
            )
        for index, artist in enumerate(UNMATCHED_PORTRAITS):
            jobs.record_unmatched(
                job_id,
                f"missing-spotify-{index}",
                {
                    "album": f"Missing Spotify Album {index}",
                    "artist": artist,
                    "reason": "No match on Spotify or Deezer",
                    "reason_code": "no_spotify_match",
                    "album_image": None,
                    "spotify_id": None,
                    "play_count": 7 - index,
                },
            )

        # The fourth reason: an album a provider outage kept from being
        # checked. Seeded so the four-panel layout, its row note and its hint
        # render in a browser (Task 18 added the reason).
        jobs.record_unmatched(
            job_id,
            "unavailable-0",
            {
                "album": "Unavailable Album",
                "artist": "Unavailable Artist",
                "reason": "Spotify and Deezer were both unavailable",
                "reason_code": "provider_unavailable",
                # A cover, so the row asks the spotlight API for no portrait
                # and the hydration check keeps counting only its own rows.
                "album_image": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
                "spotify_id": None,
                "play_count": 4,
            },
        )

        page.goto(f"{base_url}/unmatched?job_id={job_id}", wait_until="load")
        groups = page.locator(".unmatched-group")
        if groups.count() != 4:
            failures.append(
                f"unmatched report rendered {groups.count()} reason groups instead of 4"
            )
            return failures
        failures.extend(_provider_unavailable_panel_failures(page))

        scope_group = page.locator('[data-reason="release_scope"]')
        state = scope_group.evaluate(
            """node => {
                const rows = [...node.querySelectorAll('tbody tr')];
                const overflow = rows.filter(row => row.classList.contains('unmatched-overflow'));
                const button = node.querySelector('.unmatched-expander-btn');
                const count = node.querySelector('.unmatched-count');
                const page = document.querySelector('.unmatched-page');
                const grid = node.parentElement;
                const fixHint = node.querySelector('.unmatched-fix-hint');
                const root = getComputedStyle(document.documentElement);
                const headline = page.querySelector('h1');
                const username = page.querySelector('.unmatched-headline__user');
                const normalizeFont = value => value.replaceAll('"', '').replaceAll(' ', '');
                return {
                    rows: rows.length,
                    visibleRows: rows.filter(row => getComputedStyle(row).display !== 'none').length,
                    hiddenOverflow: overflow.filter(row => getComputedStyle(row).display === 'none').length,
                    buttonText: button?.textContent.trim(),
                    expanded: button?.getAttribute('aria-expanded'),
                    spotifyHref: node.querySelector('a[href*="open.spotify.com/album/"]')?.href,
                    plays: rows[0]?.querySelector('td:nth-child(3)')?.textContent.trim(),
                    countFont: normalizeFont(getComputedStyle(count).fontFamily),
                    figureFont: normalizeFont(root.getPropertyValue('--font-figure').trim()),
                    pageMaxWidth: getComputedStyle(page).maxWidth,
                    gridColumns: getComputedStyle(grid).gridTemplateColumns.split(' ').length,
                    scale: Number.parseFloat(getComputedStyle(page).getPropertyValue('--results-scale')),
                    reportOverflow: grid.scrollWidth - grid.clientWidth,
                    headingFirstTag: headline.parentElement.firstElementChild?.tagName,
                    usernameFontStyle: username ? getComputedStyle(username).fontStyle : null,
                    usernameMatchesHeadlineColor: username
                        ? getComputedStyle(username).color === getComputedStyle(headline).color
                        : false,
                    resultsStylesheet: [...document.styleSheets].some(sheet =>
                        sheet.href?.endsWith('/static/css/results.css')),
                    fixHint: fixHint?.textContent.trim(),
                    fixHintSize: getComputedStyle(fixHint).fontSize,
                    countLabelSize: getComputedStyle(node.querySelector('span.unmatched-label')).fontSize,
                    coarsePointer: matchMedia('(any-pointer: coarse)').matches,
                    controlShortSides: [...document.querySelectorAll(
                        '.results-toolbar-action, .unmatched-expander-btn, .unmatched-back-to-top-btn')]
                        .map(el => {
                            const r = el.getBoundingClientRect();
                            return Math.min(r.width, r.height);
                        }),
                    rowPadTop: Number.parseFloat(
                        getComputedStyle(rows[0].querySelector('td')).paddingTop),
                    rowPadBottom: Number.parseFloat(
                        getComputedStyle(rows[0].querySelector('td')).paddingBottom),
                    thWidths: [...node.querySelectorAll('thead th')]
                        .map(th => Number.parseFloat(getComputedStyle(th).width)),
                    // Compare the rendered extent of a cell's contents with the
                    // cell's own box. scrollWidth is not usable here: Chromium
                    // counts end padding into it, so content that is fully
                    // visible inside the padding would be reported as clipped.
                    clippedCells: [...document.querySelectorAll(
                        '.unmatched-table th, .unmatched-table td')]
                        .filter(cell => {
                            if (getComputedStyle(cell).display === 'none') return false;
                            const range = document.createRange();
                            range.selectNodeContents(cell);
                            const inner = range.getBoundingClientRect();
                            const outer = cell.getBoundingClientRect();
                            return inner.width > 0
                                && (inner.left < outer.left - 1 || inner.right > outer.right + 1);
                        })
                        .map(cell => cell.textContent.replaceAll(/\\s+/g, ' ').trim()
                            .slice(0, 40)),
                    docOverflow: document.documentElement.scrollWidth
                        - document.documentElement.clientWidth,
                    unsupportedWeights: [...node.querySelectorAll('*')]
                        .map(element => getComputedStyle(element).fontWeight)
                        .filter(weight => weight === '500' || weight === '600'),
                };
            }"""
        )
        expected = {
            "rows": 12,
            "visibleRows": 10,
            "hiddenOverflow": 2,
            "buttonText": "Show all 12 albums",
            "expanded": "false",
            "plays": "29",
            "pageMaxWidth": "1440px",
            # Two panels share a row from 1280px, never three: the 90rem page
            # cap holds a third track to about 448px, the width that made
            # three-up unreadable in the first place.
            "gridColumns": 2
            if page.viewport_size["width"] >= UNMATCHED_TWO_PANEL_MIN
            else 1,
            "headingFirstTag": "H1",
            "usernameFontStyle": "normal",
            "usernameMatchesHeadlineColor": True,
            "resultsStylesheet": True,
            "fixHint": 'Choose "All years (no filter)" on a new search to include these releases.',
            # Owner ruling, 2026-09-13 (F-B21-4 item 4): 12px, not the
            # README's 9px, for the fix hint and the per-panel count label.
            "fixHintSize": "12px",
            "countLabelSize": "12px",
        }
        for claim, wanted in expected.items():
            if state[claim] != wanted:
                failures.append(
                    f"unmatched report {claim} is {state[claim]!r}, expected {wanted!r}"
                )
        group_covers = page.locator(".unmatched-group").evaluate_all(
            """groups => groups.map(group => {
                const cover = group.querySelector('.unmatched-artwork');
                if (!cover) return null;
                const style = getComputedStyle(cover);
                return { width: style.width, height: style.height };
            })"""
        )
        # Geometry is compared numerically rather than as strings: row padding
        # follows the width-derived --results-scale, so an exact pixel string
        # would only hold at one window. Tolerance covers subpixel rounding.
        width = page.viewport_size["width"]
        scale = state["scale"] if width >= 768 else 1
        # The cover matches the Results row, and scales at every width.
        expected_cover = (64.0 if width < 768 else 72.0) * state["scale"]
        for index, cover in enumerate(group_covers):
            if cover is None:
                failures.append(f"unmatched group {index} renders no artwork container")
                continue
            cover_w = float(cover["width"].removesuffix("px"))
            cover_h = float(cover["height"].removesuffix("px"))
            if (
                abs(cover_w - expected_cover) > 0.75
                or abs(cover_h - expected_cover) > 0.75
            ):
                failures.append(
                    f"unmatched group {index} artwork is {cover_w:.1f}x{cover_h:.1f}px, "
                    f"expected {expected_cover:.1f}px"
                )

        # Row padding. It compiled to nothing once (`py-2.5`), leaving every row
        # with zero vertical padding above 768px while presence checks passed.
        expected_pad = 12.0 * scale
        for side in ("rowPadTop", "rowPadBottom"):
            if abs(state[side] - expected_pad) > 0.75:
                failures.append(
                    f"unmatched report {side} is {state[side]:.2f}px, "
                    f"expected {expected_pad:.2f}px"
                )

        # Column budget. Lost widths fall back to equal columns under
        # `table-layout: fixed` and truncate silently, so assert the shape: the
        # album column leads and has room for a cover plus a title. Three
        # columns: the fourth, "Reason detail", is now the row note.
        th_widths = state["thWidths"]
        if len(th_widths) != 3:
            failures.append(
                f"unmatched table has {len(th_widths)} header cells, expected 3"
            )
        else:
            if max(th_widths) - min(th_widths) < 1:
                failures.append(
                    f"unmatched table columns are equal widths {th_widths!r}; "
                    "the column budget did not apply"
                )
            if th_widths[1] != max(th_widths) or th_widths[1] < 150:
                failures.append(
                    f"unmatched album column is {th_widths[1]:.1f}px of {th_widths!r}; "
                    "expected it to be the widest and at least 150px"
                )

        # Document-level overflow. The grid check below cannot see it: a header
        # row that refused to shrink scrolled the whole page at 768px and 1024px.
        if state["docOverflow"] > 1:
            failures.append(
                f"unmatched page scrolls horizontally by {state['docOverflow']!r}px"
            )

        # Cells keep `overflow: hidden`, so text that cannot wrap is cut without
        # an ellipsis or an error. The metric header shipped as "PLAYS / TRA" and
        # the threshold metric as "7 plays ...", then as "1234 play", while every
        # other check passed.
        if state["clippedCells"]:
            failures.append(
                f"unmatched table clips cell content: {state['clippedCells']!r}"
            )

        if state["coarsePointer"]:
            small = [round(side, 1) for side in state["controlShortSides"] if side < 44]
            if small:
                failures.append(
                    f"unmatched report controls under 44px on a coarse pointer: {small!r}"
                )

        group_tops = page.locator(".unmatched-group").evaluate_all(
            "groups => groups.map(g => Math.round(g.getBoundingClientRect().top))"
        )
        if page.viewport_size["width"] >= UNMATCHED_TWO_PANEL_MIN:
            if len(group_tops) >= 2 and group_tops[0] != group_tops[1]:
                failures.append(
                    "unmatched reports are not arranged side-by-side on desktop"
                )
        else:
            if len(group_tops) >= 2 and group_tops[0] == group_tops[1]:
                failures.append(
                    "unmatched reports should wrap to single column on mobile"
                )

        if page.viewport_size["width"] >= UNMATCHED_TWO_PANEL_MIN:
            failures.extend(_four_panel_stack_failures(page))

        if state["reportOverflow"] > 1:
            failures.append(
                f"unmatched report overflows horizontally by {state['reportOverflow']!r}px"
            )
        if state["scale"] < 1:
            failures.append(
                f"unmatched report has invalid Results scale {state['scale']!r}"
            )

        threshold_state = page.locator('[data-reason="below_threshold"]').evaluate(
            r"""node => ({
                rows: node.querySelectorAll('tbody tr').length,
                metric: node.querySelector('.unmatched-thresholds')?.textContent
                    .replaceAll(/\s+/g, ' ').trim(),
            })"""
        )
        if threshold_state != {"rows": 1, "metric": "1234 plays / 2 tracks"}:
            failures.append(
                f"unmatched threshold row is incorrect: {threshold_state!r}"
            )
        if not (state["spotifyHref"] or "").endswith("/scope-album-2"):
            failures.append("unmatched report did not render the Spotify album link")
        if state["countFont"] != state["figureFont"]:
            failures.append(
                "unmatched report count does not use the figure typeface token"
            )
        if state["unsupportedWeights"]:
            failures.append("unmatched report renders unsupported 500/600 font weights")

        failures.extend(_row_layout_failures(page))
        failures.extend(_portrait_failures(page, spotlight_requests))
        # After the portraits load, so the portrait image is measured with
        # its slot marked, as a reader sees it.
        failures.extend(
            artwork_radius_failures(
                page.evaluate(_ARTWORK_RADII_JS, _UNMATCHED_ARTWORK_SELECTORS),
                width,
                "unmatched",
            )
        )
        # Before the first click below, and after the portraits have loaded,
        # so nothing else on the page changes between the two screenshots.
        failures.extend(_focus_ring_failures(page))
        failures.extend(_cover_wash_page_failures(page))

        button = scope_group.locator(".unmatched-expander-btn")
        button.click()
        expanded = scope_group.evaluate(
            """node => ({
                visibleRows: [...node.querySelectorAll('tbody tr')]
                    .filter(row => getComputedStyle(row).display !== 'none').length,
                buttonText: node.querySelector('.unmatched-expander-btn')?.textContent.trim(),
                expanded: node.querySelector('.unmatched-expander-btn')?.getAttribute('aria-expanded'),
            })"""
        )
        if expanded != {
            "visibleRows": 12,
            "buttonText": "Show fewer",
            "expanded": "true",
        }:
            failures.append(
                f"unmatched report expanded state is incorrect: {expanded!r}"
            )

        button.click()
        collapsed = scope_group.evaluate(
            """node => ({
                visibleRows: [...node.querySelectorAll('tbody tr')]
                    .filter(row => getComputedStyle(row).display !== 'none').length,
                expanded: node.querySelector('.unmatched-expander-btn')?.getAttribute('aria-expanded'),
            })"""
        )
        if collapsed != {"visibleRows": 10, "expanded": "false"}:
            failures.append(
                f"unmatched report collapsed state is incorrect: {collapsed!r}"
            )

        # Owner ruling, 2026-09-11: a 50-row reveal is too much, so the step is
        # 25. The route test pins the rendered attribute; this pins the value the
        # running script actually reads.
        step = button.get_attribute("data-step")
        if step != "25":
            failures.append(
                f"unmatched report expander step is {step!r}, expected '25'"
            )

        # Owner ruling, 2026-09-11: returning to the top must also collapse the
        # report, so the reader is not left under a table they had just padded
        # with rows. Expand first, so the collapse has something to undo.
        if scope_group.locator(".unmatched-back-to-top-btn").count():
            button.click()
            scope_group.locator(".unmatched-back-to-top-btn").click()
            collapsed_by_top = scope_group.evaluate(
                """node => ({
                    visibleRows: [...node.querySelectorAll('tbody tr')]
                        .filter(row => getComputedStyle(row).display !== 'none').length,
                    expanded: node.querySelector('.unmatched-expander-btn')?.getAttribute('aria-expanded'),
                })"""
            )
            if collapsed_by_top != {"visibleRows": 10, "expanded": "false"}:
                failures.append(
                    "unmatched report back-to-top did not collapse the panel: "
                    f"{collapsed_by_top!r}"
                )

        failures.extend(_unmatched_panel_width_sweep(page))
    finally:
        page.unroute(spotlight_pattern, fulfill_spotlight)
        jobs.delete(job_id)
    return failures
