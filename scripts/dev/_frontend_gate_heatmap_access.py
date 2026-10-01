"""Heatmap grid cell keyboard accessibility check (F-B21-14).

A slice of the frontend gate (F-B21-51). Nothing but a mouse hover reached a
heatmap cell before this check existed: the ramp itself is sound, but a
sighted-but-mouseless reader, or a screen reader, got no equivalent of the
tooltip. This drives a real Tab key press and reads what actually receives
focus, because a class name on a `<rect>` says nothing about whether a
keyboard can reach it.

This check also proves four later fixes:

* the SVG carries `role="group"`, not `role="img"`, in the browser's own
  accessibility tree -- an ARIA `img` prunes every presentational child, so
  a screen reader would never hear a cell's own `role="img"` +
  `aria-label` if the SVG kept that role. Proven through
  `Locator.aria_snapshot()`, the browser's computed tree, never
  `getAttribute`.
* the grid uses a roving tabindex (exactly one cell reachable by Tab, the
  arrow keys move it, one more Tab leaves the grid), not every cell at
  once.
* the arrow keys move spatially, by the rendered layout: on the desktop
  grid (one column per week) ArrowRight is 7 days on and ArrowDown the next
  day; on the mobile strip (row-major) ArrowRight is the next day. At an
  edge, focus stays put. The expected cell is read off the rendered `x`/`y`
  attributes, not recomputed from the step arithmetic under test.
* focusing an off-screen cell -- the mobile strip's own scroll, or a page
  scroll a focus jump causes -- repositions the tooltip instead of hiding
  it. The check records that a scroll event actually fired, so it cannot
  pass on a focus that scrolled nothing.

And the second review's fixes:

* the keyboard focus ring is read off painted pixels, never computed
  outline values: a 2px outline 1px outside an SVG `<rect>` held every
  computed value while later cells covered it and the SVG's edge clipped
  it. A screenshot must show `--shell-accent` on all four sides of the
  first, the last and an interior cell, and on none after a mouse click.
  The grid must still span its frame, so room made for the ring cannot
  shrink the cells.
* with Alt, Ctrl, Meta or Shift held, a grid key is left alone: not
  cancelled, focus unmoved (Alt+ArrowLeft is the browser's Back).
* a scroll never brings back the tooltip of a clicked cell the pointer has
  left.

A second check, `check_heatmap_document_listeners_attach_once`, proves the
tooltip's document-level `scroll` and `touchend` listeners are attached once
per page, not once per render. A third,
`check_heatmap_focus_survives_breakpoint`, proves a re-render across the
breakpoint gives focus back to the same day.

The third review's touch and tooltip fixes have two more:
`check_heatmap_touch_swipe_scrolls_and_tap_shows_tooltip` (a swipe that starts
on a cell scrolls the page; a tap shows the tooltip) and
`check_heatmap_tooltip_has_one_owner` (one owner state for the tooltip: no
re-focus after a click, scroll and resize touch the owner only, a hidden
tooltip cannot widen the page, Escape dismisses it, ring and `:focus-visible`
stay in step).
"""

from __future__ import annotations

import base64
import datetime
import time

from scripts.dev._frontend_gate_shared import (
    MIGRATED_PAGES,
    wait_for_scroll_past,
    wait_for_settled,
)
from scrobblescope import jobs

#: The heatmap path this check drives. Looked up rather than hard-coded a
#: second time, so a path that stops being migrated is caught here too.
HEATMAP_PATH = next(path for path in MIGRATED_PAGES if path == "/heatmap")

#: Bounded, because a cell that is never reached should fail fast rather than
#: hang tabbing through hundreds of grid cells.
_MAX_TAB_PRESSES = 5

#: Mirrors static/js/heatmap.js's own arrays exactly, so the expected string
#: below is computed independently of the code under test rather than by
#: re-reading its output.
_WEEKDAYS = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)
_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

#: Reads the currently-focused heatmap cell, or null if focus is elsewhere.
_ACTIVE_CELL_JS = """() => {
    const el = document.activeElement;
    if (!el || !el.classList || !el.classList.contains('heatmap-cell')) {
        return null;
    }
    return {
        ariaLabel: el.getAttribute('aria-label'),
        date: el.getAttribute('data-date'),
        count: el.getAttribute('data-count'),
        tabIndexAttr: el.getAttribute('tabindex'),
    };
}"""

#: Resolves --shell-accent through a throwaway probe element, so the ring
#: is compared with the colour the browser paints, not the property's text.
_ACCENT_COLOUR_JS = """() => {
    const probe = document.createElement('div');
    probe.style.position = 'absolute';
    probe.style.visibility = 'hidden';
    probe.style.color = 'var(--shell-accent)';
    document.body.appendChild(probe);
    const rgb = getComputedStyle(probe).color;
    probe.remove();
    return rgb;
}"""

#: The four sides of a cell, in the order a failure names them.
_SIDES = ("top", "right", "bottom", "left")

#: How far past a cell's edge, in CSS pixels, the ring's paint is looked for;
#: how many points along each side are sampled; and how close, per 0-255
#: channel, a pixel must be to the accent to count as the ring.
_RING_REACH_PX = 5
_RING_SAMPLES_PER_SIDE = 5
_RING_COLOUR_TOLERANCE = 24

#: Reads a viewport screenshot (base64 PNG) back in the page and reports, per
#: side of the cell, the share of sample points along the side's middle 60%
#: that have an accent-coloured pixel within `a.reach` CSS pixels outside the
#: edge. The cell's box (`a.box`) and the viewport width (`a.width`) are the
#: ones read just before the screenshot and confirmed unchanged just after it
#: (`_ring_coverage`): reading them here, after the screenshot, put the box
#: wherever the page had moved to since. Pixels, not styles: a ring a later
#: cell covers, or the SVG clips, scores 0 on that side whatever its computed
#: outline says.
_RING_PAINT_JS = """async (a) => {
    const img = new Image();
    img.src = 'data:image/png;base64,' + a.png;
    await img.decode();
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d', {willReadFrequently: true});
    ctx.drawImage(img, 0, 0);
    const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    const swatch = document.createElement('canvas');
    swatch.width = 1;
    swatch.height = 1;
    const sctx = swatch.getContext('2d');
    sctx.fillStyle = a.accent;
    sctx.fillRect(0, 0, 1, 1);
    const accent = sctx.getImageData(0, 0, 1, 1).data;
    const scale = canvas.width / a.width;
    const isAccent = (x, y) => {
        const px = Math.floor(x * scale);
        const py = Math.floor(y * scale);
        if (px < 0 || py < 0 || px >= canvas.width || py >= canvas.height) {
            return false;
        }
        const i = (py * canvas.width + px) * 4;
        return [0, 1, 2].every(
            (c) => Math.abs(pixels[i + c] - accent[c]) <= a.tolerance);
    };
    const box = a.box;
    const sides = {
        top: (t, d) => [t, box.top - d],
        bottom: (t, d) => [t, box.bottom + d],
        left: (t, d) => [box.left - d, t],
        right: (t, d) => [box.right + d, t],
    };
    const result = {};
    Object.keys(sides).forEach((side) => {
        const horizontal = side === 'top' || side === 'bottom';
        const lo = horizontal ? box.left : box.top;
        const hi = horizontal ? box.right : box.bottom;
        let painted = 0;
        for (let i = 0; i < a.samples; i++) {
            const t = lo + (hi - lo) * (0.2 + 0.6 * i / (a.samples - 1));
            for (let d = 0.5; d <= a.reach; d += 0.5) {
                const [x, y] = sides[side](t, d);
                if (isAccent(x, y)) {
                    painted++;
                    break;
                }
            }
        }
        result[side] = painted / a.samples;
    });
    return result;
}"""


#: Resolves once the web fonts loading now have loaded and two frames have
#: drawn what they changed.
_LAYOUT_SETTLED_JS = """() => document.fonts.ready.then(() => new Promise(
    (r) => requestAnimationFrame(() => requestAnimationFrame(r))))"""

#: Everything that tells an unpainted ring from a hidden one, read in the page
#: with the geometry, before and after a screenshot (F-B23-39): the ring's
#: `visibility` attribute and box, the cell's box, what holds focus and whether it matches
#: `:focus-visible`, the ring's computed stroke and the page's theme, the
#: tooltip's box and whether it covers the ring, the scroll offset, the device
#: pixel ratio, and how many cells paint after the ring. Also the result's
#: crossfade (the container's and the SVG's computed `opacity`, the container's
#: `heatmap-fade`, `fading-out` and `is-handing-off` flags, how many animations
#: are running, and whether the page matches `prefers-reduced-motion`): a ring
#: screenshotted under an opacity below 1 is blended toward the page.
_RING_EVIDENCE_JS = """(date) => {
    const cell = document.querySelector('.heatmap-cell[data-date="' + date + '"]');
    const ring = document.querySelector('.heatmap-focus-ring');
    const tip = document.querySelector('.heatmap-tooltip');
    const boxOf = (n) => {
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
    };
    const ringBox = boxOf(ring);
    const tipBox = boxOf(tip);
    const result = document.getElementById('heatmap-result');
    const svg = cell ? cell.closest('svg') : null;
    const opacityOf = (n) => (n ? getComputedStyle(n).opacity : null);
    const flag = (c) => (result ? result.classList.contains(c) : null);
    const active = document.activeElement;
    let focusVisible = null;
    try {
        focusVisible = active ? active.matches(':focus-visible') : null;
    } catch (e) {
        focusVisible = null;
    }
    const hits = !!(ringBox && tipBox && tipBox.left < ringBox.right
        && tipBox.right > ringBox.left && tipBox.top < ringBox.bottom
        && tipBox.bottom > ringBox.top);
    let after = null;
    if (ring) {
        after = Array.from(document.querySelectorAll(
            '.heatmap-cell, .heatmap-cell-placeholder'
        )).filter((n) => ring.compareDocumentPosition(n)
            & Node.DOCUMENT_POSITION_FOLLOWING).length;
    }
    return {
        ringVisibility: ring ? ring.getAttribute('visibility') : null,
        ringBox: ringBox,
        cellBox: boxOf(cell),
        active: active
            ? (active.getAttribute('data-date') || active.tagName) : null,
        focusVisible: focusVisible,
        docFocus: document.hasFocus(),
        stroke: ring ? getComputedStyle(ring).stroke : null,
        theme: document.documentElement.getAttribute('data-theme'),
        tooltipBox: tipBox,
        tooltipShown: !!(tip && tip.classList.contains('visible')),
        tooltipHitsRing: hits,
        scrollX: window.scrollX,
        scrollY: window.scrollY,
        dpr: window.devicePixelRatio,
        cellsAfterRing: after,
        containerOpacity: opacityOf(result),
        svgOpacity: opacityOf(svg),
        fade: flag('heatmap-fade'),
        fadingOut: flag('fading-out'),
        handingOff: flag('is-handing-off'),
        runningAnimations: document.getAnimations().filter(
            (a) => a.playState === 'running'
        ).length,
        reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    };
}"""

#: One read of the cell's box, the focus ring's box and the viewport they sit
#: in, in CSS pixels (the geometry), together with `_RING_EVIDENCE_JS`'s read
#: of the same page state (the evidence), or null when there is no such cell.
#: Read before and after a screenshot: equal geometry means the page held
#: still while it was taken, the ring included; the evidence of the read after
#: it is what a failure reports, the state closest to the pixels.
_CELL_GEOMETRY_JS = (
    """(date) => {
    const el = document.querySelector('.heatmap-cell[data-date="' + date + '"]');
    if (!el) return null;
    const box = el.getBoundingClientRect();
    const ring = document.querySelector('.heatmap-focus-ring');
    const ringBox = ring ? ring.getBoundingClientRect() : null;
    return {
        box: {left: box.left, top: box.top, right: box.right, bottom: box.bottom},
        ring: ringBox && {left: ringBox.left, top: ringBox.top,
            right: ringBox.right, bottom: ringBox.bottom,
            visibility: ring.getAttribute('visibility')},
        width: window.innerWidth,
        height: window.innerHeight,
        evidence: ("""
    + _RING_EVIDENCE_JS
    + """)(date),
    };
}"""
)

#: A settle wait that took longer than this is named in a failure's evidence.
_SLOW_SETTLE_SECONDS = 1.0

#: What the page itself does when the layout may have moved under it: a
#: `scroll` makes heatmap.js reposition the tooltip it is showing. A tooltip
#: left at the position it had before a reflow can sit over the ring, and
#: nothing but a scroll or a resize moves it.
_LAYOUT_MOVED_JS = "() => document.dispatchEvent(new Event('scroll'))"

#: How many times a screenshot is retaken because the page moved while it was
#: taken (a late web font or a scroll settling shifts the cell), before the
#: page is called unsettled.
_RING_SHOT_ATTEMPTS = 5


#: The evidence fields that are not geometry (a change in the geometry retakes
#: the shot), with the key each has in the note.
_EVIDENCE_WATCHED = (
    ("active", "active"),
    ("focusVisible", "active.focus_visible"),
    ("docFocus", "document.has_focus"),
    ("stroke", "ring.stroke"),
    ("theme", "theme"),
    ("tooltipBox", "tooltip.box"),
    ("tooltipShown", "tooltip.shown"),
    ("tooltipHitsRing", "tooltip.hits_ring"),
    ("scrollX", "scroll"),
    ("scrollY", "scroll"),
    ("dpr", "dpr"),
    ("cellsAfterRing", "cells_after_ring"),
    ("containerOpacity", "container.opacity"),
    ("svgOpacity", "svg.opacity"),
    ("fade", "container.heatmap_fade"),
    ("fadingOut", "container.fading_out"),
    ("handingOff", "container.is_handing_off"),
    ("runningAnimations", "animations.running"),
    ("reducedMotion", "prefers_reduced_motion"),
)


def _changed_during_shot(before: dict | None, after: dict | None) -> list[str]:
    """The note keys of the evidence fields that differ between two reads."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        return []
    changed: list[str] = []
    for field, key in _EVIDENCE_WATCHED:
        if before.get(field) != after.get(field) and key not in changed:
            changed.append(key)
    return changed


def _geometry_of(read: dict | None) -> dict | None:
    """A cell read without its evidence: the part compared for equality."""
    if read is None:
        return None
    return {key: value for key, value in read.items() if key != "evidence"}


def _box_text(box: dict | None) -> str:
    """`left,top,right,bottom` to one decimal, or `none`."""
    if not box:
        return "none"
    return ",".join(f"{box[k]:.1f}" for k in ("left", "top", "right", "bottom"))


def _ring_evidence_note(evidence: dict | None) -> str:
    """One line of key=value pairs saying why a ring may have painted nothing.

    The FAIL line used to carry only the per-side shares, so an unpainted ring
    could not be told from a hidden one, a ring that sat elsewhere, one with
    another stroke, or a tooltip over it (F-B23-39). Empty when nothing was
    read."""
    if not evidence:
        return ""
    pairs = (
        ("ring.visibility", evidence.get("ringVisibility")),
        ("ring.box", _box_text(evidence.get("ringBox"))),
        ("cell.box", _box_text(evidence.get("cellBox"))),
        ("active", evidence.get("active")),
        ("active.focus_visible", evidence.get("focusVisible")),
        ("document.has_focus", evidence.get("docFocus")),
        ("ring.stroke", evidence.get("stroke")),
        ("theme", evidence.get("theme")),
        ("tooltip.box", _box_text(evidence.get("tooltipBox"))),
        ("tooltip.shown", evidence.get("tooltipShown")),
        ("tooltip.hits_ring", evidence.get("tooltipHitsRing")),
        ("scroll", f"{evidence.get('scrollX')},{evidence.get('scrollY')}"),
        ("dpr", evidence.get("dpr")),
        ("cells_after_ring", evidence.get("cellsAfterRing")),
        ("container.opacity", evidence.get("containerOpacity")),
        ("svg.opacity", evidence.get("svgOpacity")),
        ("container.heatmap_fade", evidence.get("fade")),
        ("container.fading_out", evidence.get("fadingOut")),
        ("container.is_handing_off", evidence.get("handingOff")),
        ("animations.running", evidence.get("runningAnimations")),
        ("prefers_reduced_motion", evidence.get("reducedMotion")),
        ("settle_ms", evidence.get("settleMs")),
        ("settle_slow", evidence.get("settleSlow")),
    )
    if "changedDuringShot" in evidence:
        changed = ",".join(evidence["changedDuringShot"]) or "none"
        pairs += (("changed_during_shot", changed),)
    text = " ".join(f"{key}={str(value).replace(' ', '')}" for key, value in pairs)
    return f" [evidence: {text}]"


def _ring_shot(
    page, date: str, accent: str
) -> tuple[dict[str, float] | None, dict | None]:
    """The ring's per-side coverage for `date` and the evidence read with it.

    Per side of the cell, the share of its samples showing the accent just
    outside its edge, read off a screenshot of the viewport.

    The cell's box is read before the screenshot and again after it, and the
    screenshot is judged only when the two agree: a page that moved in
    between (for instance the Adobe Fonts kit, which can land after the `load` event and
    reflows the text above the grid) would put the box where the pixels are
    not, and every side would read as bare. Each attempt first has the page
    reposition its tooltip (one left where the cell was can sit over the ring)
    and waits for fonts and frames to settle; a moved page is shot again, and
    one that never holds still raises rather than report a ring. The evidence
    comes with the geometry, so it is read on both sides of the shot; the
    judged one is the read after it, with how long the settle wait took and
    which evidence fields differed from the read before it."""
    page.evaluate(
        "(date) => document.querySelector('.heatmap-cell[data-date=\"' + date"
        " + '\"]').scrollIntoView({block: 'center', inline: 'nearest'})",
        date,
    )
    for _ in range(_RING_SHOT_ATTEMPTS):
        page.evaluate(_LAYOUT_MOVED_JS)
        settle_started = time.monotonic()
        page.evaluate(_LAYOUT_SETTLED_JS)
        settle_seconds = time.monotonic() - settle_started
        first = page.evaluate(_CELL_GEOMETRY_JS, date)
        if first is None:
            return None, None
        before = _geometry_of(first)
        png = base64.b64encode(page.screenshot()).decode("ascii")
        last = page.evaluate(_CELL_GEOMETRY_JS, date)
        if _geometry_of(last) == before:
            evidence = last.get("evidence")
            if isinstance(evidence, dict):
                evidence["settleMs"] = round(settle_seconds * 1000)
                evidence["settleSlow"] = settle_seconds > _SLOW_SETTLE_SECONDS
                evidence["changedDuringShot"] = _changed_during_shot(
                    first.get("evidence"), evidence
                )
            coverage = page.evaluate(
                _RING_PAINT_JS,
                {
                    "png": png,
                    "box": before["box"],
                    "width": before["width"],
                    "accent": accent,
                    "reach": _RING_REACH_PX,
                    "samples": _RING_SAMPLES_PER_SIDE,
                    "tolerance": _RING_COLOUR_TOLERANCE,
                },
            )
            return coverage, evidence
    raise RuntimeError(
        f"the cell for {date!r} kept moving while its screenshot was taken "
        f"({_RING_SHOT_ATTEMPTS} attempts), so its focus ring could not be read"
    )


def _ring_coverage(page, date: str, accent: str) -> dict[str, float] | None:
    """Per side of the cell for `date`, the share of its samples showing the
    accent just outside its edge (see `_ring_shot`), or None without a cell."""
    return _ring_shot(page, date, accent)[0]


def _check_ring_painted(page, layout, accent: str, which: str, date: str) -> list[str]:
    """The keyboard-focused cell for `date` shows the ring on all four sides."""
    coverage, evidence = _ring_shot(page, date, accent)
    if coverage is None:
        return [f"no heatmap cell for {date!r} to read the {which} cell's ring from"]
    missing = [side for side in _SIDES if coverage[side] < 1]
    if not missing:
        return []
    shares = ", ".join(f"{side} {coverage[side]:.0%}" for side in _SIDES)
    return [
        f"the keyboard focus ring round the {which} cell ({date!r}) [{layout}] "
        f"paints no {accent} pixel within {_RING_REACH_PX}px of its "
        f"{', '.join(missing)} edge(s) (samples painted: {shares}); a later "
        "cell or the SVG's edge is hiding it" + _ring_evidence_note(evidence)
    ]


def _expected_cell_label(iso_date: str, count: int) -> str:
    """The exact string `cellAccessibleLabel` produces for one date/count.

    A Python mirror of `static/js/heatmap.js`'s `formatDateLong` and
    `cellAccessibleLabel`, so a regression in either JS function is visible
    here rather than compared against its own (possibly also broken) output.
    """
    year, month, day = (int(part) for part in iso_date.split("-"))
    weekday = _WEEKDAYS[datetime.date(year, month, day).isoweekday() % 7]
    count_str = (
        "No scrobbles"
        if count == 0
        else f"{count} scrobble" + ("" if count == 1 else "s")
    )
    return f"{weekday} {day} {_MONTHS[month - 1]} {year} -- {count_str}"


def _snapshot_root_role(snapshot: str) -> str | None:
    """The role token of an `aria_snapshot()` string's top-level node.

    `Locator.aria_snapshot()` renders `- role "name":`, but wraps the whole
    `role "name"` pair in a single quote when the name needs YAML escaping
    (any heatmap label does, since it embeds a colon) -- `- 'group "...":'`.
    Reads the role out of either form rather than a fixed prefix, so the
    escaping choice is not part of what this check asserts.
    """
    first_line = next(iter(snapshot.strip().splitlines()), "")
    token = first_line[2:] if first_line.startswith("- ") else first_line
    token = token.lstrip("'\"")
    return token.split(" ", 1)[0] or None


def _truncate_snapshot(snapshot: str, limit: int = 300) -> str:
    """The snapshot's first `limit` characters, for a readable failure line.

    A 500-day grid's `aria_snapshot()` is one line per cell; a failure that
    quoted it whole would bury the one line that matters.
    """
    if len(snapshot) <= limit:
        return snapshot
    return snapshot[:limit] + "...(truncated)"


#: The cell an arrow key should reach from the cell for `a.date`, read off the
#: rendered geometry: the nearest cell in the same row (Left/Right) or the
#: same column (Up/Down) in the key's direction, or the same date when there
#: is none (an edge). Independent of heatmap.js's step arithmetic.
_SPATIAL_NEIGHBOUR_JS = """(a) => {
    const cells = Array.from(document.querySelectorAll('.heatmap-cell')).map(
        (el) => ({
            date: el.getAttribute('data-date'),
            x: parseFloat(el.getAttribute('x')),
            y: parseFloat(el.getAttribute('y')),
        })
    );
    const here = cells.find((c) => c.date === a.date);
    if (!here) return null;
    const horizontal = a.key === 'ArrowLeft' || a.key === 'ArrowRight';
    const sign = a.key === 'ArrowRight' || a.key === 'ArrowDown' ? 1 : -1;
    let best = null;
    let bestDistance = Infinity;
    cells.forEach((c) => {
        const inLine = horizontal ? c.y === here.y : c.x === here.x;
        const distance = sign * (horizontal ? c.x - here.x : c.y - here.y);
        if (inLine && distance > 0 && distance < bestDistance) {
            best = c;
            bestDistance = distance;
        }
    });
    return best ? best.date : here.date;
}"""

#: Each arrow key probed from the most recent day's cell, and the key that
#: should bring focus back (None: the probe is an edge, nothing to undo).
_ARROW_PROBES = (
    ("ArrowLeft", "ArrowRight"),
    ("ArrowUp", "ArrowDown"),
    ("ArrowRight", None),
    ("ArrowDown", None),
)

#: The day shift each arrow key makes on the desktop grid, one column per
#: week. Stated here, apart from the spatial read, so the desktop result is
#: also pinned to calendar days (the review's finding 2: ArrowRight used to
#: move one day, down the column).
_DESKTOP_ARROW_DAYS = {"ArrowLeft": -7, "ArrowRight": 7, "ArrowUp": -1, "ArrowDown": 1}


def _days_between(from_iso: str, to_iso: str) -> int:
    """Signed day count from `from_iso` to `to_iso`."""
    start = datetime.date.fromisoformat(from_iso)
    return (datetime.date.fromisoformat(to_iso) - start).days


def _shift_iso_date(iso_date: str, days: int) -> str:
    """`iso_date` plus `days` (negative shifts back), as `YYYY-MM-DD`."""
    year, month, day = (int(part) for part in iso_date.split("-"))
    shifted = datetime.date(year, month, day) + datetime.timedelta(days=days)
    return shifted.isoformat()


def check_heatmap_cells_are_keyboard_accessible(page, base_url: str) -> list[str]:
    """Tab reaches one cell; arrow keys rove it; scroll never hides its tip."""
    failures: list[str] = []
    job_id = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    # A single-day range makes the "exactly one cell carries tabindex=0"
    # audit vacuous (1 of 1 always passes): seed a wide range instead, with
    # one non-zero day so the aria-label assertion still exercises a real
    # count. The mobile strip packs 10-28 columns into its container
    # (MOBILE_MIN_COLUMNS/MOBILE_MAX_COLUMNS in heatmap.js), so it takes a
    # wide range -- 500 days, measured against the MOBILE viewport -- before
    # the strip's own height passes the viewport's, which is what the A3
    # scroll/tooltip assertion below needs: on a shorter range every cell is
    # already on screen and that assertion is vacuous.
    from_date = "2025-01-01"
    to_date = _shift_iso_date(from_date, 499)
    seeded_date = "2025-01-01"
    seeded_count = 5
    jobs.succeed(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": from_date,
            "to_date": to_date,
            "total_scrobbles": seeded_count,
            "max_count": seeded_count,
            "daily_counts": {seeded_date: seeded_count},
        },
        "Done",
    )
    try:
        page.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
        svg = page.locator("#heatmap-result-frame svg")
        svg.wait_for(state="visible")
        page.locator("#heatmap-save-image").focus()

        landed = None
        for _ in range(_MAX_TAB_PRESSES):
            page.keyboard.press("Tab")
            landed = page.evaluate(_ACTIVE_CELL_JS)
            if landed:
                break

        if not landed:
            failures.append(
                "Tab never reaches a focusable heatmap cell "
                f"(gave up after {_MAX_TAB_PRESSES} presses)"
            )
            return failures

        landed_date = landed["date"]
        expected_label = _expected_cell_label(landed_date, int(landed["count"]))
        if landed["ariaLabel"] != expected_label:
            failures.append(
                f"heatmap cell aria-label was {landed['ariaLabel']!r}, "
                f"expected {expected_label!r}"
            )
        if landed_date != to_date:
            failures.append(
                "Tab landed on the cell for "
                f"{landed_date!r}, expected the most recent day in range "
                f"({to_date!r}) to be the grid's one Tab stop"
            )

        # -- A1: the accessibility tree, not getAttribute. --------------
        # role="img" on the SVG would prune every presentational child, so
        # a screen reader would never hear a cell's own role="img" +
        # aria-label. Read what the browser actually computed. A Playwright
        # failure here is a check-level fault, not a result to report:
        # `_run_check` (frontend_gate.py) already reports an uncaught
        # exception as its own failure line.
        svg_snapshot = svg.aria_snapshot()
        svg_role = _snapshot_root_role(svg_snapshot)
        snapshot_head = _truncate_snapshot(svg_snapshot)
        if svg_role != "group":
            failures.append(
                "the heatmap SVG's computed accessibility role is "
                f"{svg_role!r}, expected 'group' (snapshot starts: "
                f"{snapshot_head!r})"
            )
        if f'img "{expected_label}"' not in svg_snapshot:
            failures.append(
                "the focused cell's own accessible name is missing from "
                "the SVG's accessibility tree (snapshot starts: "
                f"{snapshot_head!r}), expected an img node named "
                f"{expected_label!r}"
            )

        # -- A1b: the axis labels are decoration. A cell's own name says its
        # date, so the 15 day and month <text> nodes would only be a loose
        # run of words in the tree ahead of the 365 named cells (S2-18).
        labels = page.evaluate(
            """() => {
                const nodes = Array.from(document.querySelectorAll(
                    '.heatmap-day-label, .heatmap-month-label'));
                return {
                    total: nodes.length,
                    exposed: nodes.filter(
                        (n) => n.getAttribute('aria-hidden') !== 'true'
                    ).length,
                };
            }"""
        )
        if svg.get_attribute("data-layout") == "desktop" and not labels["total"]:
            failures.append("the desktop heatmap rendered no axis labels to audit")
        if labels["exposed"]:
            failures.append(
                f"{labels['exposed']} of {labels['total']} heatmap axis labels "
                'lack aria-hidden="true", so they read as loose text before '
                "the cells"
            )

        # -- A2: roving tabindex, not every cell at once. ----------------
        if landed["tabIndexAttr"] != "0":
            failures.append(
                'heatmap cell reached by Tab does not carry tabindex="0" '
                f"(was {landed['tabIndexAttr']!r})"
            )

        roving_audit = page.evaluate(
            """() => {
                const cells = Array.from(document.querySelectorAll('.heatmap-cell'));
                const zeroTabindex = cells.filter(
                    (c) => c.getAttribute('tabindex') === '0'
                ).length;
                return {total: cells.length, zeroTabindex: zeroTabindex};
            }"""
        )
        if roving_audit["total"] <= 1:
            failures.append(
                "heatmap grid rendered only "
                f"{roving_audit['total']} .heatmap-cell element(s); the "
                "roving-tabindex audit needs more than one cell to be "
                "meaningful (seed a wider date range)"
            )
        if roving_audit["zeroTabindex"] != 1:
            failures.append(
                f"{roving_audit['zeroTabindex']} of {roving_audit['total']} "
                '.heatmap-cell elements carry tabindex="0"; exactly one '
                "should (a roving tabindex, not every cell at once)"
            )

        layout = svg.get_attribute("data-layout")
        failures.extend(_check_arrow_keys(page, layout, landed_date))

        accent_color = page.evaluate(_ACCENT_COLOUR_JS)
        ring_failures, interior_date = _check_ring_on_three_cells(
            page, layout, accent_color, landed_date, from_date
        )
        failures.extend(ring_failures)
        failures.extend(_check_grid_fills_frame(page, layout))
        failures.extend(_check_modifier_keys_left_alone(page, layout))

        page.keyboard.press("Tab")
        left_grid = page.evaluate(
            "() => { const el = document.activeElement; "
            "return !(el && el.classList && el.classList.contains('heatmap-cell')); }"
        )
        if not left_grid:
            failures.append(
                "the next Tab from a heatmap cell stayed inside the grid "
                "(a roving tabindex should cost exactly one Tab to leave)"
            )

        # -- L1: a focus that did not come from Tab/arrow keys (a mouse
        # click, or this programmatic el.focus()) must move the roving Tab
        # stop too, else Tab-out-and-back lands on the stale stop instead of
        # the cell a user just focused. -----------------------------------
        first_cell_locator = page.locator(f'.heatmap-cell[data-date="{from_date}"]')
        first_cell_locator.evaluate("(el) => el.focus()")
        first_cell_tabindex = page.evaluate(
            "(date) => { const el = document.querySelector("
            "'.heatmap-cell[data-date=\"' + date + '\"]'); "
            "return el ? el.getAttribute('tabindex') : null; }",
            from_date,
        )
        if first_cell_tabindex != "0":
            failures.append(
                "focusing a non-stop heatmap cell (e.g. a mouse click) did "
                "not move the roving Tab stop to it "
                f"(tabindex was {first_cell_tabindex!r}, expected '0')"
            )
        else:
            page.keyboard.press("Tab")
            page.keyboard.press("Shift+Tab")
            returned = page.evaluate(_ACTIVE_CELL_JS)
            if not returned or returned["date"] != from_date:
                failures.append(
                    "Tab away and Shift+Tab back after focusing a non-stop "
                    f"cell did not return focus to {from_date!r} (landed on "
                    f"{returned['date'] if returned else None!r}); the "
                    "roving Tab stop was not updated by the programmatic "
                    "focus"
                )

        # -- A3: a scroll while a cell is focused repositions the tooltip,
        # rather than hiding it, on the profile where a focused cell can
        # need to scroll into view (the mobile strip). ------------------
        if layout == "mobile":
            page.evaluate(
                "() => { if (document.activeElement) document.activeElement.blur(); }"
            )
            # Scroll away from wherever the earlier Tab/arrow-key traffic
            # left the viewport, to the opposite end of the page, so
            # re-focusing the cell below is guaranteed to actually move the
            # scroll position (a same-position "scroll" never fires a
            # scroll event at all, which would make this assertion
            # vacuous).
            page.evaluate(_SCROLL_COUNTER_JS)
            page.evaluate("() => window.scrollTo(0, 0)")
            # Let scrollTo's own scroll event land before the count starts.
            page.evaluate(_TWO_FRAMES_JS)
            scroll_before = page.evaluate(_SCROLL_RESET_JS)
            cell_locator = page.locator(f'.heatmap-cell[data-date="{landed_date}"]')
            cell_locator.evaluate("(el) => el.focus()")
            # Let the browser's own scroll-into-view, the tooltip's
            # requestAnimationFrame reposition and its 0.15s CSS opacity
            # transition finish.
            wait_for_settled(page)
            scroll_after = page.evaluate(_SCROLL_READ_JS)
            if scroll_after["events"] == 0:
                failures.append(
                    "focusing the off-screen cell scrolled nothing (no scroll "
                    f"event fired; page scrollY {scroll_before['y']} -> "
                    f"{scroll_after['y']}), so the tooltip assertion below "
                    "proves nothing; seed a range whose strip is taller than "
                    "the viewport"
                )
            tooltip_state = page.evaluate(
                """() => {
                    const tt = document.querySelector('.heatmap-tooltip');
                    if (!tt) return null;
                    return {
                        opacity: getComputedStyle(tt).opacity,
                        text: tt.textContent,
                    };
                }"""
            )
            if not tooltip_state:
                failures.append(
                    "no .heatmap-tooltip element exists after focusing an "
                    "off-screen cell"
                )
            else:
                if tooltip_state["opacity"] != "1":
                    failures.append(
                        "the tooltip was hidden (computed opacity "
                        f"{tooltip_state['opacity']!r}) after a scroll "
                        "brought the focused cell into view; a scroll "
                        "while a heatmap cell is focused should reposition "
                        "the tooltip, not hide it"
                    )
                if tooltip_state["text"] != expected_label:
                    failures.append(
                        "the tooltip visible after the scroll read "
                        f"{tooltip_state['text']!r}, expected "
                        f"{expected_label!r}"
                    )

        # Last, because a click ends :focus-visible for every scripted
        # focus after it (docs/agents/ui-accessibility.md item 4).
        if interior_date:
            failures.extend(
                _check_clicked_cell(page, layout, accent_color, interior_date)
            )
    finally:
        jobs.delete(job_id)
    return failures


#: Counts scroll events anywhere in the page (capture phase, so the mobile
#: strip's own scroll counts too). Installed once per page.
_SCROLL_COUNTER_JS = """() => {
    if (window.__heatmapScrollEvents === undefined) {
        document.addEventListener('scroll', () => {
            window.__heatmapScrollEvents += 1;
        }, true);
    }
    window.__heatmapScrollEvents = 0;
}"""
_SCROLL_RESET_JS = """() => {
    window.__heatmapScrollEvents = 0;
    return {y: window.scrollY};
}"""
_SCROLL_READ_JS = "() => ({events: window.__heatmapScrollEvents, y: window.scrollY})"
_TWO_FRAMES_JS = (
    "() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
)

#: The tooltip's state: shown (its `visible` class) and the focused cell's
#: date, or null when focus is not on a cell.
_TOOLTIP_AND_FOCUS_JS = """() => {
    const tt = document.querySelector('.heatmap-tooltip');
    const el = document.activeElement;
    return {
        shown: !!(tt && tt.classList.contains('visible')),
        focused: el && el.classList && el.classList.contains('heatmap-cell')
            ? el.getAttribute('data-date') : null,
    };
}"""

#: How far, in CSS pixels, the grid may sit inside the edges named below.
_GRID_EDGE_TOLERANCE_PX = 0.5

#: The rendered cells' outer edges against the frame's content box, and one
#: rendered gap between two neighbouring columns.
_GRID_EDGES_JS = """() => {
    const frame = document.querySelector('#heatmap-result-frame');
    const box = frame.getBoundingClientRect();
    const style = getComputedStyle(frame);
    const contentLeft = box.left + parseFloat(style.borderLeftWidth)
        + parseFloat(style.paddingLeft);
    const contentRight = box.right - parseFloat(style.borderRightWidth)
        - parseFloat(style.paddingRight);
    const cells = Array.from(document.querySelectorAll('.heatmap-cell'))
        .map((c) => c.getBoundingClientRect());
    const lefts = Array.from(new Set(cells.map((c) => c.left)))
        .sort((a, b) => a - b);
    return {
        leftInset: Math.min(...cells.map((c) => c.left)) - contentLeft,
        rightInset: contentRight - Math.max(...cells.map((c) => c.right)),
        gap: lefts.length > 1 ? lefts[1] - lefts[0] - cells[0].width : 0,
    };
}"""


def _check_grid_fills_frame(page, layout) -> list[str]:
    """The grid spans the frame: its last column ends one cell gap (the
    grid's own trailing gap) from the frame's content edge, and on the mobile
    strip its first column starts on that edge, level with the KPI text.

    A focus-ring given room inside the SVG's viewBox shrank every cell and
    pulled the grid 3-4px in from both edges; every ring check still passed.
    """
    edges = page.evaluate(_GRID_EDGES_JS)
    failures: list[str] = []
    right_limit = edges["gap"] + _GRID_EDGE_TOLERANCE_PX
    if edges["rightInset"] > right_limit:
        failures.append(
            f"the heatmap grid [{layout}] ends {edges['rightInset']:.1f}px short "
            "of the frame's content edge, expected at most one cell gap "
            f"({edges['gap']:.1f}px) + {_GRID_EDGE_TOLERANCE_PX}px: something "
            "shrank the grid inside its frame"
        )
    if layout == "mobile" and abs(edges["leftInset"]) > _GRID_EDGE_TOLERANCE_PX:
        failures.append(
            f"the heatmap strip [{layout}] starts {edges['leftInset']:.1f}px in "
            "from the frame's content edge, expected 0 (level with the KPI "
            "text above it): something shrank the grid inside its frame"
        )
    return failures


def _check_ring_on_three_cells(
    page, layout, accent: str, last_date: str, first_date: str
) -> tuple[list[str], str | None]:
    """The ring shows whole round the last cell (the Tab stop), the first
    cell and an interior one, each reached by keyboard. Returns the failures
    and the interior cell's date; leaves focus on the last cell."""
    failures = _check_ring_painted(page, layout, accent, "last", last_date)
    page.keyboard.press("Home")
    first = page.evaluate(_ACTIVE_CELL_JS)
    if not first or first["date"] != first_date:
        failures.append(
            f"Home [{layout}] moved focus to "
            f"{first['date'] if first else None!r}, expected the first "
            f"cell {first_date!r}"
        )
        return failures, None
    failures.extend(_check_ring_painted(page, layout, accent, "first", first_date))
    # One right and one down from the first cell has a neighbour on every
    # side in both layouts.
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowDown")
    interior = page.evaluate(_ACTIVE_CELL_JS)
    interior_date = interior["date"] if interior else None
    if interior_date in (None, first_date):
        failures.append(
            f"ArrowRight then ArrowDown [{layout}] from the first cell left "
            f"focus on {interior_date!r}; no interior cell to read a ring from"
        )
        interior_date = None
    else:
        failures.extend(
            _check_ring_painted(page, layout, accent, "interior", interior_date)
        )
    page.keyboard.press("End")
    return failures, interior_date


#: With a modifier held, each key is dispatched to the focused cell; reports
#: every one the grid cancelled or moved focus on, and puts focus back.
_MODIFIER_KEYS_JS = """() => {
    const el = document.activeElement;
    const taken = [];
    ['altKey', 'ctrlKey', 'metaKey', 'shiftKey'].forEach((modifier) => {
        ['ArrowLeft', 'ArrowUp', 'Home', 'End'].forEach((key) => {
            const init = {key: key, bubbles: true, cancelable: true};
            init[modifier] = true;
            const event = new KeyboardEvent('keydown', init);
            el.dispatchEvent(event);
            const now = document.activeElement;
            if (event.defaultPrevented || now !== el) {
                taken.push(modifier.replace('Key', '') + '+' + key
                    + (event.defaultPrevented ? ' cancelled' : '')
                    + (now !== el ? ' moved focus' : ''));
                el.focus();
            }
        });
    });
    return taken;
}"""


def _check_modifier_keys_left_alone(page, layout) -> list[str]:
    """With Alt, Ctrl, Meta or Shift held, a grid key is not cancelled and
    focus stays put: Alt+ArrowLeft is Back, Ctrl+Home the top of the page.

    Dispatched as synthetic events, which the browser never acts on, so an
    uncancelled Alt+ArrowLeft does not navigate the gate's page away.
    """
    taken = page.evaluate(_MODIFIER_KEYS_JS)
    if not taken:
        return []
    return [
        f"the heatmap grid [{layout}] took browser shortcuts it should leave "
        f"alone: {', '.join(taken)}"
    ]


def _check_clicked_cell(page, layout, accent: str, date: str) -> list[str]:
    """A mouse click focuses a cell but draws no ring, and once the pointer
    leaves, a scroll does not bring its tooltip back."""
    failures: list[str] = []
    page.locator(f'.heatmap-cell[data-date="{date}"]').click()
    coverage = _ring_coverage(page, date, accent)
    painted = [side for side in _SIDES if coverage and coverage[side] > 0]
    if painted:
        failures.append(
            f"a mouse click on the cell {date!r} [{layout}] drew the focus "
            f"ring on its {', '.join(painted)} edge(s); the ring is for "
            "keyboard focus only (:focus-visible)"
        )
    page.mouse.move(0, 0)
    wait_for_settled(page)
    before = page.evaluate(_TOOLTIP_AND_FOCUS_JS)
    if before["focused"] != date or before["shown"]:
        failures.append(
            f"after clicking {date!r} and moving the pointer away [{layout}], "
            f"focus was on {before['focused']!r} and the tooltip "
            f"{'shown' if before['shown'] else 'hidden'}; expected the cell "
            "focused and its tooltip hidden, so the scroll probe cannot run"
        )
        return failures
    page.evaluate("() => document.dispatchEvent(new Event('scroll'))")
    page.evaluate(_TWO_FRAMES_JS)
    after = page.evaluate(_TOOLTIP_AND_FOCUS_JS)
    if after["shown"]:
        failures.append(
            f"a scroll brought back the tooltip of the clicked cell {date!r} "
            f"[{layout}] after the pointer had left and hidden it; a scroll "
            "only repositions a tooltip already on show"
        )
    return failures


def _check_arrow_keys(page, layout: str | None, landed_date: str) -> list[str]:
    """Each arrow key from the most recent day's cell reaches its spatial
    neighbour (or stays put at an edge), moves the roving Tab stop with it,
    and its opposite key brings focus back. Leaves focus on `landed_date`."""
    failures: list[str] = []
    landed_cell = page.locator(f'.heatmap-cell[data-date="{landed_date}"]')
    for key, back_key in _ARROW_PROBES:
        expected = page.evaluate(
            _SPATIAL_NEIGHBOUR_JS, {"date": landed_date, "key": key}
        )
        if layout == "desktop" and expected != landed_date:
            days = _days_between(landed_date, expected)
            if days != _DESKTOP_ARROW_DAYS[key]:
                failures.append(
                    f"the desktop grid's rendered {key} neighbour of "
                    f"{landed_date!r} is {days} day(s) away, expected "
                    f"{_DESKTOP_ARROW_DAYS[key]} (one column per week)"
                )
        page.keyboard.press(key)
        moved = page.evaluate(_ACTIVE_CELL_JS)
        moved_date = moved["date"] if moved else None
        if moved_date != expected:
            edge = " (an edge: stay put)" if expected == landed_date else ""
            failures.append(
                f"{key} [{layout}] from {landed_date!r} moved focus to "
                f"{moved_date!r}, expected its spatial neighbour "
                f"{expected!r}{edge}"
            )
            landed_cell.evaluate("(el) => el.focus()")
            continue
        if expected == landed_date:
            continue
        if moved["tabIndexAttr"] != "0":
            failures.append(
                f"{key} moved focus but the new cell does not carry "
                f'tabindex="0" (was {moved["tabIndexAttr"]!r})'
            )
        previous_tabindex = landed_cell.get_attribute("tabindex")
        if previous_tabindex != "-1":
            failures.append(
                f"{key} moved focus but the previously-focused cell still "
                f'carries tabindex={previous_tabindex!r} instead of "-1"'
            )
        page.keyboard.press(back_key)
        back = page.evaluate(_ACTIVE_CELL_JS)
        if not back or back["date"] != landed_date:
            failures.append(
                f"{back_key} [{layout}] from {expected!r} did not move focus "
                f"back to {landed_date!r}; landed on "
                f"{back['date'] if back else None!r}"
            )
            landed_cell.evaluate("(el) => el.focus()")
    return failures


#: Installed before heatmap.js runs: counts the `scroll` and `touchend`
#: listeners heatmap.js itself keeps on `document` (added minus removed,
#: matched by listener and capture flag, as the DOM matches them). A stack
#: that names heatmap.js tells its listeners from any other script's.
_DOCUMENT_LISTENER_SPY_JS = """(() => {
    const live = [];
    const capture = (opts) =>
        typeof opts === 'boolean' ? opts : !!(opts && opts.capture);
    const add = document.addEventListener;
    const remove = document.removeEventListener;
    document.addEventListener = function (type, fn, opts) {
        const stack = new Error().stack || '';
        if ((type === 'scroll' || type === 'touchend')
                && /heatmap\\.js/.test(stack)) {
            const c = capture(opts);
            if (!live.some((e) => e.type === type && e.fn === fn && e.c === c)) {
                live.push({type: type, fn: fn, c: c});
            }
        }
        return add.call(this, type, fn, opts);
    };
    document.removeEventListener = function (type, fn, opts) {
        const c = capture(opts);
        const i = live.findIndex((e) => e.type === type && e.fn === fn && e.c === c);
        if (i >= 0) live.splice(i, 1);
        return remove.call(this, type, fn, opts);
    };
    window.__heatmapDocumentListenerCounts = () => ({
        scroll: live.filter((e) => e.type === 'scroll').length,
        touchend: live.filter((e) => e.type === 'touchend').length,
    });
})();"""

#: Either side of heatmap.js's MOBILE_MAX_WIDTH (860px) breakpoint; each
#: crossing re-renders the grid, as each new search does.
_WIDE_VIEWPORT = {"width": 1280, "height": 720}
_NARROW_VIEWPORT = {"width": 390, "height": 844}


def check_heatmap_document_listeners_attach_once(page, base_url: str) -> list[str]:
    """Three renders leave one `scroll` and one `touchend` listener on
    `document` from heatmap.js, not one pair per render (the review's
    finding 4: each pair also held its render's cells and detached SVG).

    Runs on its own page in the check's context, so the listener spy it
    installs, and the viewport it resizes, end with this check.
    """
    failures: list[str] = []
    job_id = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    jobs.succeed(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": "2025-03-01",
            "total_scrobbles": 3,
            "max_count": 3,
            "daily_counts": {"2025-01-01": 3},
        },
        "Done",
    )
    probe = page.context.new_page()
    try:
        probe.set_viewport_size(_WIDE_VIEWPORT)
        probe.add_init_script(_DOCUMENT_LISTENER_SPY_JS)
        probe.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
        frame_svg = "#heatmap-result-frame svg"
        for viewport, layout in (
            (_WIDE_VIEWPORT, "desktop"),
            (_NARROW_VIEWPORT, "mobile"),
            (_WIDE_VIEWPORT, "desktop"),
        ):
            probe.set_viewport_size(viewport)
            probe.locator(f'{frame_svg}[data-layout="{layout}"]').wait_for(
                state="visible"
            )
        counts = probe.evaluate("() => window.__heatmapDocumentListenerCounts()")
        for event_type in ("scroll", "touchend"):
            if counts[event_type] != 1:
                failures.append(
                    f"after three heatmap renders, heatmap.js holds "
                    f"{counts[event_type]} document {event_type!r} "
                    "listener(s), expected exactly 1 (attach once, not once "
                    "per render)"
                )
    finally:
        probe.close()
        jobs.delete(job_id)
    return failures


#: The focused cell's date, how many cells are Tab stops, and that date's
#: own tabindex.
_FOCUS_AND_TAB_STOP_JS = """() => {
    const el = document.activeElement;
    const cells = Array.from(document.querySelectorAll('.heatmap-cell'));
    return {
        focused: el && el.classList && el.classList.contains('heatmap-cell')
            ? el.getAttribute('data-date') : null,
        stops: cells.filter((c) => c.getAttribute('tabindex') === '0')
            .map((c) => c.getAttribute('data-date')),
    };
}"""


def check_heatmap_focus_survives_breakpoint(page, base_url: str) -> list[str]:
    """A re-render across the breakpoint gives focus back to the same day.

    The re-render replaces every cell, so a focused cell was destroyed, focus
    fell to `<body>` and the Tab stop reset to the last day. The cell for the
    same date must hold focus afterwards, be the one Tab stop, and still show
    the keyboard ring; with no cell focused, no cell may take focus.

    Runs on its own page, as the listener check does, so the viewport it
    resizes ends with this check.
    """
    failures: list[str] = []
    job_id = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    # The window the app really renders (WINDOW_DAYS in heatmap.js): a short
    # range scales the desktop grid up several times over, and the ring's
    # paint with it, past where _check_ring_painted looks.
    jobs.succeed(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": _shift_iso_date("2025-01-01", 364),
            "total_scrobbles": 3,
            "max_count": 3,
            "daily_counts": {"2025-01-01": 3},
        },
        "Done",
    )
    probe = page.context.new_page()
    try:
        probe.set_viewport_size(_WIDE_VIEWPORT)
        probe.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
        frame_svg = "#heatmap-result-frame svg"
        probe.locator(f'{frame_svg}[data-layout="desktop"]').wait_for(state="visible")
        probe.locator("#heatmap-save-image").focus()
        landed = None
        for _ in range(_MAX_TAB_PRESSES):
            probe.keyboard.press("Tab")
            landed = probe.evaluate(_ACTIVE_CELL_JS)
            if landed:
                break
        if not landed:
            return [
                "Tab never reaches a heatmap cell, so the breakpoint probe cannot run"
            ]
        # Off the default Tab stop, so a reset to the last day shows.
        probe.keyboard.press("ArrowLeft")
        chosen = probe.evaluate(_ACTIVE_CELL_JS)
        if not chosen or chosen["date"] == landed["date"]:
            return ["ArrowLeft did not move off the last day; no probe cell"]
        date = chosen["date"]
        accent = probe.evaluate(_ACCENT_COLOUR_JS)

        for viewport, layout in (
            (_NARROW_VIEWPORT, "mobile"),
            (_WIDE_VIEWPORT, "desktop"),
        ):
            probe.set_viewport_size(viewport)
            probe.locator(f'{frame_svg}[data-layout="{layout}"]').wait_for(
                state="visible"
            )
            probe.evaluate(_TWO_FRAMES_JS)
            state = probe.evaluate(_FOCUS_AND_TAB_STOP_JS)
            if state["focused"] != date:
                failures.append(
                    f"after the re-render into the {layout} layout, focus was "
                    f"on {state['focused']!r}, expected the cell for {date!r}"
                )
                continue
            if state["stops"] != [date]:
                failures.append(
                    f"after the re-render into the {layout} layout, the Tab "
                    f"stop(s) were {state['stops']!r}, expected [{date!r}]"
                )
            failures.extend(
                _check_ring_painted(probe, layout, accent, "re-rendered", date)
            )

        probe.locator("#heatmap-save-image").focus()
        probe.set_viewport_size(_NARROW_VIEWPORT)
        probe.locator(f'{frame_svg}[data-layout="mobile"]').wait_for(state="visible")
        probe.evaluate(_TWO_FRAMES_JS)
        idle = probe.evaluate(_FOCUS_AND_TAB_STOP_JS)
        if idle["focused"] is not None:
            failures.append(
                "with no cell focused, the re-render put focus on the cell for "
                f"{idle['focused']!r}; nothing should take focus"
            )
    finally:
        probe.close()
        jobs.delete(job_id)
    return failures


# ---------------------------------------------------------------------------
# Touch scrolling and the tooltip's single owner (review 3: S2-3, S2-6, S2-7,
# S2-8, S2-16, S2-17)
# ---------------------------------------------------------------------------

#: A cell's date, count and centre for every cell whose box lies inside the
#: viewport.
_CELLS_IN_VIEW_JS = """() => Array.from(document.querySelectorAll('.heatmap-cell'))
    .map((c) => ({date: c.getAttribute('data-date'),
                  count: c.getAttribute('data-count'),
                  r: c.getBoundingClientRect()}))
    .filter((c) => c.r.left >= 0 && c.r.right <= window.innerWidth
        && c.r.top >= 0 && c.r.bottom <= window.innerHeight)
    .map((c) => ({date: c.date, count: c.count,
                  x: c.r.left + c.r.width / 2, y: c.r.top + c.r.height / 2}))"""

#: The tooltip's shown state, text and box, next to the page's scroll state.
_TOOLTIP_BOX_JS = """() => {
    const tt = document.querySelector('.heatmap-tooltip');
    const r = tt.getBoundingClientRect();
    const root = document.documentElement;
    return {
        shown: tt.classList.contains('visible'),
        text: tt.textContent,
        cx: r.left + r.width / 2, top: r.top, bottom: r.bottom,
        scrollY: window.scrollY,
        scrollWidth: root.scrollWidth, clientWidth: root.clientWidth,
    };
}"""

#: A touchstart on a cell, cancelable as a real one is; true when the page
#: cancelled it. A cancelled touchstart is what stops the browser scrolling.
_TOUCHSTART_CANCELLED_JS = """(date) => {
    const cell = document.querySelector('.heatmap-cell[data-date="' + date + '"]');
    const r = cell.getBoundingClientRect();
    const touch = new Touch({identifier: 1, target: cell,
        clientX: r.left + r.width / 2, clientY: r.top + r.height / 2});
    const event = new TouchEvent('touchstart', {touches: [touch],
        targetTouches: [touch], changedTouches: [touch],
        bubbles: true, cancelable: true});
    cell.dispatchEvent(event);
    return event.defaultPrevented;
}"""

_SEED_DAYS = 365


def _seed_year_job() -> tuple[str, str]:
    """A finished heatmap job over the app's 365-day window, with a spread of
    non-zero days so cells carry different labels. Returns (job id, last day)."""
    job_id = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    from_date = "2025-01-01"
    to_date = _shift_iso_date(from_date, _SEED_DAYS - 1)
    counts = {_shift_iso_date(from_date, n): 1 + n % 9 for n in range(0, _SEED_DAYS, 3)}
    jobs.succeed(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": from_date,
            "to_date": to_date,
            "total_scrobbles": sum(counts.values()),
            "max_count": max(counts.values()),
            "daily_counts": counts,
        },
        "Done",
    )
    return job_id, to_date


def _tap_shows_tooltip(page, cell: dict) -> list[str]:
    page.touchscreen.tap(cell["x"], cell["y"])
    wait_for_settled(page)
    box = page.evaluate(_TOOLTIP_BOX_JS)
    expected = _expected_cell_label(cell["date"], int(cell["count"]))
    if box["shown"] and box["text"] == expected:
        return []
    seen = f"shown reading {box['text']!r}" if box["shown"] else "hidden"
    return [
        f"a tap on the cell {cell['date']!r} left the tooltip {seen}, "
        f"expected it shown reading {expected!r}"
    ]


def _swipe_scrolls_chromium(page, cell: dict) -> list[str]:
    """A real touch drag (CDP `Input.dispatchTouchEvent`) that starts on a
    cell scrolls the page. Chromium only: Firefox has no such protocol."""
    session = page.context.new_cdp_session(page)
    x, y = cell["x"], cell["y"]
    before = page.evaluate("() => window.scrollY")
    session.send(
        "Input.dispatchTouchEvent",
        {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]},
    )
    for step in range(1, 9):
        session.send(
            "Input.dispatchTouchEvent",
            {"type": "touchMove", "touchPoints": [{"x": x, "y": y - 25 * step}]},
        )
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    # The swipe's fling scrolls on the compositor; wait for it to land. A
    # swipe that never scrolls times out here and is reported below.
    wait_for_scroll_past(page, before)
    wait_for_settled(page)
    after = page.evaluate("() => window.scrollY")
    session.detach()
    if after <= before:
        return [
            f"a touch swipe that began on the cell {cell['date']!r} did not "
            f"scroll the page (scrollY {before} -> {after}): a cell must not "
            "cancel touchstart"
        ]
    box = page.evaluate(_TOOLTIP_BOX_JS)
    if box["shown"]:
        return [
            "a swipe that began on a cell left its tooltip shown "
            f"({box['text']!r}); only a tap shows it"
        ]
    return []


def check_heatmap_touch_swipe_scrolls_and_tap_shows_tooltip(
    page, base_url: str
) -> list[str]:
    """On a touch screen a swipe that starts on a cell scrolls the page and a
    tap on a cell shows its tooltip (S2-3: every cell cancelled touchstart, so
    a swipe over the strip never scrolled)."""
    failures: list[str] = []
    job_id, _last = _seed_year_job()
    try:
        page.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
        page.locator("#heatmap-result-frame svg").wait_for(state="visible")
        cells = page.evaluate(_CELLS_IN_VIEW_JS)
        if len(cells) < 3:
            return [f"only {len(cells)} heatmap cell(s) in view; no touch probe"]
        cell = cells[len(cells) // 2]
        if page.evaluate(_TOUCHSTART_CANCELLED_JS, cell["date"]):
            failures.append(
                "a touchstart on a heatmap cell was cancelled (preventDefault): "
                "the browser then never scrolls a swipe that starts there"
            )
        failures.extend(_tap_shows_tooltip(page, cell))
        page.touchscreen.tap(2, 2)
        wait_for_settled(page)
        if page.evaluate(_TOOLTIP_BOX_JS)["shown"]:
            failures.append("a tap outside the grid left the cell's tooltip shown")
        if page.context.browser.browser_type.name == "chromium":
            failures.extend(_swipe_scrolls_chromium(page, cell))
    finally:
        jobs.delete(job_id)
    return failures


def _open_year(page, base_url: str, job_id: str, viewport: dict) -> None:
    page.set_viewport_size(viewport)
    page.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
    layout = "desktop" if viewport["width"] >= 860 else "mobile"
    page.locator(f'#heatmap-result-frame svg[data-layout="{layout}"]').wait_for(
        state="visible"
    )
    page.evaluate(_TWO_FRAMES_JS)


def _cell_box(page, date: str) -> dict:
    return page.evaluate(
        """(date) => {
            const r = document.querySelector(
                '.heatmap-cell[data-date="' + date + '"]').getBoundingClientRect();
            return {x: r.left + r.width / 2, y: r.top + r.height / 2,
                    top: r.top, bottom: r.bottom};
        }""",
        date,
    )


def _tab_into_grid(page) -> str | None:
    page.locator("#heatmap-save-image").focus()
    for _ in range(_MAX_TAB_PRESSES):
        page.keyboard.press("Tab")
        landed = page.evaluate(_ACTIVE_CELL_JS)
        if landed:
            return landed["date"]
    return None


def _escape_dismisses_hover_tooltip(page, base_url: str, job_id: str) -> list[str]:
    """Escape hides a tooltip the pointer is holding open while focus is
    elsewhere (WCAG 1.4.13: dismissible without moving the pointer)."""
    _open_year(page, base_url, job_id, _WIDE_VIEWPORT)
    cells = page.evaluate(_CELLS_IN_VIEW_JS)
    hovered = cells[len(cells) // 2]
    over = _cell_box(page, hovered["date"])
    page.mouse.move(over["x"], over["y"])
    wait_for_settled(page)
    if not page.evaluate(_TOOLTIP_BOX_JS)["shown"]:
        return ["a hovered cell showed no tooltip; the Escape probe proves nothing"]
    page.keyboard.press("Escape")
    if page.evaluate(_TOOLTIP_BOX_JS)["shown"]:
        return [
            "Escape left a hover tooltip shown while the pointer stayed on "
            f"the cell {hovered['date']!r} and focus was elsewhere"
        ]
    return []


#: Scrolls the page and reads the tooltip and the focused cell in the scroll
#: event itself, which a frame-late reposition has not yet answered.
_SCROLL_AND_READ_JS = """() => new Promise((resolve) => {
    const cell = document.activeElement;
    const tt = document.querySelector('.heatmap-tooltip');
    const before = window.scrollY;
    window.addEventListener('scroll', () => {
        const c = cell.getBoundingClientRect();
        const t = tt.getBoundingClientRect();
        resolve({moved: window.scrollY - before, shown: tt.classList.contains('visible'),
                 above: c.top - t.bottom, below: t.top - c.bottom});
    }, {once: true});
    window.scrollBy(0, 40);
})"""


def _keyboard_tooltip_follows_scroll_at_once(
    page, base_url: str, job_id: str
) -> list[str]:
    """A keyboard-focus tooltip is fixed, so a scroll moves it with its cell in
    the same frame; repositioned a frame late it visibly trails the cell."""
    _open_year(page, base_url, job_id, {"width": 1280, "height": 500})
    if _tab_into_grid(page) is None:
        return ["Tab never reaches a heatmap cell; no scroll-lag probe"]
    wait_for_settled(page)
    reading = page.evaluate(_SCROLL_AND_READ_JS)
    if not reading["moved"]:
        return ["the page did not scroll; the scroll-lag probe proves nothing"]
    # The tooltip sits 8px above its cell, or 8px below when there is no room.
    if not reading["shown"] or not (
        abs(reading["above"] - 8) <= 3 or abs(reading["below"] - 8) <= 3
    ):
        return [
            "a scroll left the keyboard tooltip behind its cell for a frame "
            f"(shown {reading['shown']}, {reading['above']:.0f}px above the "
            f"cell, {reading['below']:.0f}px below it; expected 8)"
        ]
    return []


def check_heatmap_tooltip_has_one_owner(page, base_url: str) -> list[str]:
    """One owner state decides who shows the tooltip: a re-focus after a click
    shows none (S2-6), a scroll or a resize touches its owner only (S2-7), a
    hidden one cannot widen the page (S2-16), Escape dismisses it (S2-17) and
    a key after a click keeps ring and :focus-visible in step (S2-8)."""
    failures: list[str] = []
    job_id, last_date = _seed_year_job()
    try:
        # S2-6: a clicked cell the pointer left, re-focused by a re-render at
        # the other layout, must not bring its tooltip back.
        _open_year(page, base_url, job_id, _WIDE_VIEWPORT)
        cells = page.evaluate(_CELLS_IN_VIEW_JS)
        clicked = cells[len(cells) // 3]
        page.locator(f'.heatmap-cell[data-date="{clicked["date"]}"]').click()
        page.mouse.move(0, 0)
        wait_for_settled(page)
        page.set_viewport_size({"width": 700, "height": 800})
        page.locator('#heatmap-result-frame svg[data-layout="mobile"]').wait_for(
            state="visible"
        )
        wait_for_settled(page, after_timer_ms=100)
        if page.evaluate(_TOOLTIP_BOX_JS)["shown"]:
            failures.append(
                "after a click, the pointer leaving and a re-render into the "
                "mobile layout re-focused the cell, its tooltip came back "
                "though nothing but a mouse click had focused it"
            )

        # S2-7 (a): a scroll never moves a hover tooltip to the focused cell.
        # A short window, so the page is sure to have somewhere to scroll.
        _open_year(page, base_url, job_id, {"width": 1280, "height": 500})
        cells = page.evaluate(_CELLS_IN_VIEW_JS)
        clicked = cells[len(cells) // 3]
        hovered = cells[2 * len(cells) // 3]
        page.locator(f'.heatmap-cell[data-date="{clicked["date"]}"]').click()
        over = _cell_box(page, hovered["date"])
        page.mouse.move(over["x"], over["y"])
        wait_for_settled(page)
        clicked_label = _expected_cell_label(clicked["date"], int(clicked["count"]))
        before = page.evaluate("() => window.scrollY")
        page.mouse.wheel(0, 300)
        wait_for_scroll_past(page, before)  # no scroll is reported below
        wait_for_settled(page)
        box = page.evaluate(_TOOLTIP_BOX_JS)
        if box["scrollY"] == 0:
            failures.append(
                "the wheel scrolled nothing; the scroll probe proves nothing"
            )
        if box["shown"] and box["text"] == clicked_label:
            failures.append(
                "a scroll moved the hover tooltip onto the clicked, focused "
                f"cell ({box['text']!r}) while the pointer was over another"
            )

        # S2-7 (b): a resize inside the desktop layout moves the keyboard
        # tooltip with its cell.
        _open_year(page, base_url, job_id, _WIDE_VIEWPORT)
        if _tab_into_grid(page) is None:
            return failures + ["Tab never reaches a heatmap cell; no owner probe"]
        for _ in range(10):
            page.keyboard.press("ArrowLeft")
        focused = page.evaluate(_ACTIVE_CELL_JS)["date"]
        wait_for_settled(page)
        page.set_viewport_size({"width": 1000, "height": 720})
        wait_for_settled(page, after_timer_ms=100)
        box = page.evaluate(_TOOLTIP_BOX_JS)
        cell = _cell_box(page, focused)
        overlaps = box["top"] < cell["bottom"] and box["bottom"] > cell["top"]
        if not box["shown"] or abs(box["cx"] - cell["x"]) > 3 or overlaps:
            failures.append(
                "after a resize inside the desktop layout the keyboard "
                f"tooltip stayed behind (shown {box['shown']}, centre "
                f"{box['cx']:.0f} vs cell {cell['x']:.0f}, tooltip "
                f"{box['top']:.0f}-{box['bottom']:.0f} vs cell "
                f"{cell['top']:.0f}-{cell['bottom']:.0f})"
            )

        # S2-17: Escape dismisses the keyboard tooltip and leaves focus be.
        page.keyboard.press("Escape")
        state = page.evaluate(_TOOLTIP_AND_FOCUS_JS)
        if state["shown"] or state["focused"] != focused:
            failures.append(
                "Escape left the keyboard tooltip "
                f"{'shown' if state['shown'] else 'hidden'} with focus on "
                f"{state['focused']!r}; expected it hidden and focus on "
                f"{focused!r}"
            )

        failures.extend(_escape_dismisses_hover_tooltip(page, base_url, job_id))
        failures.extend(
            _keyboard_tooltip_follows_scroll_at_once(page, base_url, job_id)
        )

        # S2-16: a tooltip hovered on the right, then hidden, does not widen
        # the page once the window narrows.
        _open_year(page, base_url, job_id, _WIDE_VIEWPORT)
        far = _cell_box(page, last_date)
        page.mouse.move(far["x"], far["y"])
        wait_for_settled(page)
        page.mouse.move(0, 0)
        wait_for_settled(page)
        page.set_viewport_size(_NARROW_VIEWPORT)
        page.locator('#heatmap-result-frame svg[data-layout="mobile"]').wait_for(
            state="visible"
        )
        wait_for_settled(page, after_timer_ms=100)
        box = page.evaluate(_TOOLTIP_BOX_JS)
        if box["scrollWidth"] > box["clientWidth"]:
            failures.append(
                "a hidden tooltip left over from a right-hand cell widened the "
                f"page at 390px (scrollWidth {box['scrollWidth']} > "
                f"clientWidth {box['clientWidth']})"
            )

        # S2-8: after a click, a key that moves nothing must not leave a
        # :focus-visible cell without its ring.
        _open_year(page, base_url, job_id, _WIDE_VIEWPORT)
        first = page.evaluate(
            "() => document.querySelector('.heatmap-cell').getAttribute('data-date')"
        )
        page.locator(f'.heatmap-cell[data-date="{first}"]').click()
        page.mouse.move(0, 0)
        page.keyboard.press("ArrowLeft")
        ring = page.evaluate(
            """() => ({
                fv: document.activeElement.matches(':focus-visible'),
                ring: document.querySelector('.heatmap-focus-ring')
                    .getAttribute('visibility'),
            })"""
        )
        if ring["fv"] != (ring["ring"] == "visible"):
            failures.append(
                "after a click and a key that moved nothing, the cell's "
                f":focus-visible is {ring['fv']} but its ring is {ring['ring']!r}"
            )
    finally:
        jobs.delete(job_id)
    return failures
