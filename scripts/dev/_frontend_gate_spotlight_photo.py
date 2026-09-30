"""The artist spotlight photo check: no crop, no overlay, no animation, no fake.

A slice of the frontend gate (F-B21-51), added for F-B21-60 part 1. The
pre-existing ``check_artist_spotlight_rotation`` in ``_frontend_gate_pipeline``
tests a different property -- that the card stays hidden while a slow
candidate's photo is still unconfirmed, reveals once every hydration has
settled, and then rotates -- not photo geometry. This module therefore owns
its own job seed and its own mocked ``/api/artist_spotlight`` route, which
answers every artist at once with the same photo (or none).
"""

from __future__ import annotations

import json

from scripts.dev._frontend_gate_shared import MIGRATED_PAGES
from scrobblescope import jobs

#: The migrated results page. Derived from the shared inventory rather than a
#: literal, so a future rename of the route is a one-place fix.
RESULTS_PATH = next(path for path in MIGRATED_PAGES if path == "/results")

#: A tiny, explicitly square image so `naturalWidth`/`naturalHeight` read back
#: a known 1:1 ratio in every browser -- the check needs an intrinsic ratio to
#: compare the rendered box against, not just an arbitrary picture.
SQUARE_PHOTO_DATA_URL = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='300' height='300'%3E%3Crect width='300' height='300' "
    "fill='%23888'/%3E%3C/svg%3E"
)

#: A non-square photo (3:2), the shape most real Spotify artist photos are
#: not -- the photo box itself stays square (`.spotlight-image-box`), so this
#: is what actually exercises the "whole photo, letterboxed, never cropped"
#: rule (F-B21-60). The square fixture above cannot: in a square box a
#: square photo looks the same whether it is cropped or contained.
NON_SQUARE_PHOTO_DATA_URL = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='300' height='200'%3E%3Crect width='300' height='200' "
    "fill='%23888'/%3E%3C/svg%3E"
)


def _seed_spotlight_job(artists: tuple[tuple[str, int, int], ...] | None = None) -> str:
    """Create a job with several artists, so `spotlight_artists` samples more
    than one candidate. `artists` is `(name, albums, seconds per album)` for
    each one, when a check needs particular names or text lengths; the default
    is ten artists with one album each. Each album carries a non-empty, distinguishable
    `album_image` -- not a `""` placeholder -- so a check that seeds a job
    this way exercises the real path a live job takes: an album cover exists
    and must never leak into `image_url` as a fake artist photo (F-B21-60).
    What each artist's *confirmed* photo resolves to is decided separately, by
    `_install_spotlight_fetch_mock`."""
    job_id = jobs.create(
        {
            "username": "frontend-gate",
            "year": 2025,
            "sort_mode": "playcount",
            "release_scope": "all",
            "min_plays": 1,
            "min_tracks": 1,
            "limit_results": "all",
            "mode": "album",
        }
    )
    if artists is None:
        artists = tuple(
            (f"Photo Artist {index}", 1, 2520 - index) for index in range(10)
        )
    jobs.succeed(
        job_id,
        [
            {
                "artist": name,
                "album": f"{name} Album {album}",
                "play_count": 200 - 10 * index - album,
                "play_time": "42m",
                "play_time_seconds": seconds,
                "release_date": "2025-01-01",
                "album_image": f"https://example.com/photo-album-{index}-{album}-cover.jpg",
                "spotify_id": f"photo-album-{index}-{album}",
            }
            for index, (name, albums, seconds) in enumerate(artists)
            for album in range(albums)
        ],
        "Done",
    )
    return job_id


def _install_spotlight_fetch_mock(
    page,
    image_url: str | None,
    *,
    keep_rotating: bool = False,
    linkless: tuple[str, ...] = (),
) -> None:
    """Mock `/api/artist_spotlight` and speed up the 7s rotation interval.

    Unlike the mock `check_artist_spotlight_rotation` installs (one slow
    candidate among fast ones), this one answers every artist immediately with
    the same `image_url` (a photo, or `null`), which is all these checks need.
    It counts what the page asked for and what it read back
    (`window.__spotlightRequests` / `__spotlightResponses`), so a check can
    prove hydration ran instead of waiting a fixed time and hoping. The sped-up
    interval fires once by default; `keep_rotating` keeps it repeating, for a
    check that must see every candidate, and counts each period in
    `window.__spotlightTicks`. The artists named in `linkless` are answered
    with a photo but no Spotify URL, so the card hides its link for them."""
    page.add_init_script(
        f"""(() => {{
            const nativeInterval = window.setInterval;
            const nativeFetch = window.fetch.bind(window);
            window.__spotlightPhotoUrl = {json.dumps(image_url)};
            window.__spotlightRequests = 0;
            window.__spotlightResponses = 0;
            window.__spotlightTicks = 0;
            const keepRotating = {json.dumps(keep_rotating)};
            const linkless = {json.dumps(list(linkless))};
            window.setInterval = (callback, delay, ...args) => {{
                if (delay === 7000 && keepRotating) {{
                    // Counted, so a check can wait for whole rotation periods
                    // to pass instead of sleeping and hoping.
                    return nativeInterval(() => {{
                        window.__spotlightTicks += 1;
                        callback();
                    }}, 200, ...args);
                }}
                if (delay === 7000) return window.setTimeout(callback, 200, ...args);
                return nativeInterval(callback, delay, ...args);
            }};
            window.fetch = (resource, options) => {{
                const url = String(resource);
                if (!url.includes('/api/artist_spotlight?')) {{
                    return nativeFetch(resource, options);
                }}
                window.__spotlightRequests += 1;
                const artist = decodeURIComponent(url.split('artist=')[1] || '');
                return Promise.resolve({{
                    ok: true,
                    json: async () => {{
                        window.__spotlightResponses += 1;
                        return {{
                            image_url: window.__spotlightPhotoUrl,
                            spotify_url: window.__spotlightPhotoUrl
                                && !linkless.includes(artist)
                                ? 'https://open.spotify.com/artist/photo'
                                : null,
                        }};
                    }},
                }});
            }};
        }})();"""
    )


#: True once the spotlight photo has been fetched and decoded: `complete` alone
#: is also true for an image with no source, and a natural size of zero is what
#: a still-decoding image reports.
_PHOTO_DECODED_JS = """() => {
    const img = document.querySelector('#spotlight-artist-img');
    return Boolean(img && img.src && img.complete && img.naturalWidth > 0
        && img.naturalHeight > 0);
}"""


def _wait_for_decoded_photo(page) -> bool:
    """Wait for the confirmed photo to be decoded; False if it never is."""
    try:
        page.wait_for_function(_PHOTO_DECODED_JS, timeout=5_000)
    except Exception:  # noqa: BLE001 - converted to an actionable gate failure
        return False
    return True


#: Finds what could sit over the photo: another element's box, or a
#: `::before` / `::after` that paints a background.
_PHOTO_OVERLAY_JS = """() => {
    const img = document.querySelector('#spotlight-artist-img');
    const photo = img.getBoundingClientRect();
    const box = img.closest('.spotlight-image-box');
    const card = document.querySelector('#artist-spotlight-card');
    const offenders = [];
    card.querySelectorAll('*').forEach(el => {
        if (el === img || el.contains(img)) return;
        const other = el.getBoundingClientRect();
        if (other.width === 0 || other.height === 0) return;
        const intersects = other.left < photo.right && other.right > photo.left
            && other.top < photo.bottom && other.bottom > photo.top;
        if (intersects) offenders.push(el.id || el.className || el.tagName);
    });
    // A scrim can be a pseudo-element: querySelectorAll never sees it, but it
    // paints over the photo all the same. Only one that generates a box
    // (`content` is neither none nor normal) and paints a background counts.
    const painted = value => value !== 'none' && value !== 'rgba(0, 0, 0, 0)'
        && value !== 'transparent';
    [[box, 'photo box'], [card, 'card'],
        [document.querySelector('#spotlight-card-content'), 'card content']]
        .forEach(([owner, name]) => {
            if (!owner) return;
            ['::before', '::after'].forEach(pseudo => {
                const style = getComputedStyle(owner, pseudo);
                if (style.content === 'none' || style.content === 'normal') return;
                if (painted(style.backgroundColor) || painted(style.backgroundImage)) {
                    offenders.push(`${name} ${pseudo}`);
                }
            });
        });
    return offenders;
}"""

#: Reads every way the photo or what wraps it can move, fade or filter: a
#: running animation, or a transition on transform or filter.
_PHOTO_MOTION_JS = """() => {
    const img = document.querySelector('#spotlight-artist-img');
    const owners = [[img, 'photo'], [img.closest('.spotlight-image-box'), 'photo box'],
        [document.querySelector('#spotlight-card-content'), 'card content'],
        [document.querySelector('#artist-spotlight-card'), 'card']];
    const found = [];
    owners.forEach(([el, name]) => {
        if (!el) return;
        const style = getComputedStyle(el);
        style.animationName.split(',').map(part => part.trim()).forEach(animation => {
            if (animation !== 'none') found.push(`${name} animation ${animation}`);
        });
        const durations = style.transitionDuration.split(',')
            .map(part => Number.parseFloat(part) || 0);
        style.transitionProperty.split(',').map(part => part.trim())
            .forEach((property, index) => {
                const duration = durations[index % durations.length];
                if (duration > 0 && ['transform', 'filter', 'all'].includes(property)) {
                    found.push(`${name} transition ${property}`);
                }
            });
    });
    return found;
}"""


#: Samples the photo's and its content's opacity every 40ms for a second --
#: five periods of the sped-up rotation -- with the artist shown at each
#: sample.
_PHOTO_SAMPLE_JS = """() => new Promise(resolve => {
    const img = document.querySelector('#spotlight-artist-img');
    const content = document.querySelector('#spotlight-card-content');
    const card = document.querySelector('#artist-spotlight-card');
    const samples = [];
    const sample = () => samples.push({
        opacity: [getComputedStyle(img).opacity, getComputedStyle(content).opacity],
        index: card.dataset.spotlightIndex,
        ticks: window.__spotlightTicks,
    });
    sample();
    const interval = window.setInterval(sample, 40);
    window.setTimeout(() => {
        window.clearInterval(interval);
        resolve(samples);
    }, 1000);
})"""


def spotlight_fade_failures(samples: list[dict]) -> list[str]:
    """Judge the samples of `_PHOTO_SAMPLE_JS`: the artist changed in the
    window, and no opacity did.

    Opacity that holds still proves nothing unless a swap happened while it
    was sampled: a window that missed every rotation tick would read as
    steady whatever the swap does to the photo.
    """
    failures = []
    shown = {sample["index"] for sample in samples}
    if len(shown) < 2:
        failures.append(
            "spotlight rotation never swapped the artist while opacity was "
            f"sampled (only index {sorted(shown, key=str)} shown), so a fade "
            "on the swap would not have been seen"
        )
    if len({tuple(sample["opacity"]) for sample in samples}) > 1:
        failures.append(
            "spotlight photo opacity changed during a rotation tick: "
            f"{[sample['opacity'] for sample in samples]}"
        )
    return failures


def check_artist_spotlight_photo_has_no_crop_overlay_or_animation(
    page, base_url: str
) -> list[str]:
    """A confirmed spotlight photo is shown uncropped, unobscured and still."""
    job_id = _seed_spotlight_job()
    failures = []
    try:
        _install_spotlight_fetch_mock(page, SQUARE_PHOTO_DATA_URL, keep_rotating=True)
        page.goto(
            f"{base_url}{RESULTS_PATH}?job_id={job_id}",
            wait_until="domcontentloaded",
            timeout=10_000,
        )
        if not _wait_for_decoded_photo(page):
            failures.append("spotlight photo never loaded a confirmed image")
            return failures

        # No crop: the rendered box keeps the photo's own aspect ratio.
        geometry = page.evaluate(
            """() => {
                const img = document.querySelector('#spotlight-artist-img');
                const rect = img.getBoundingClientRect();
                return {
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                    width: rect.width,
                    height: rect.height,
                };
            }"""
        )
        natural_ratio = geometry["naturalWidth"] / geometry["naturalHeight"]
        rendered_ratio = geometry["width"] / geometry["height"]
        if abs(rendered_ratio - natural_ratio) > 0.01 * natural_ratio:
            failures.append(
                "spotlight photo is cropped: rendered ratio "
                f"{rendered_ratio:.3f} vs natural ratio {natural_ratio:.3f}"
            )

        # No overlay: no other element's box, and no ::before or ::after that
        # paints a background, sits over the photo.
        overlap = page.evaluate(_PHOTO_OVERLAY_JS)
        if overlap:
            failures.append(
                f"spotlight photo is overlaid by: {', '.join(str(o) for o in overlap)}"
            )

        # No animation: the photo and its wrapping content never fade -- the
        # deleted opacity handoff animated `#spotlight-card-content`,
        # not the <img> itself, so both are sampled -- and none of them runs
        # an animation or transitions transform or filter. The rotation keeps
        # ticking (see `_install_spotlight_fetch_mock`), and each sample
        # records which artist is shown, so `spotlight_fade_failures` can tell
        # a window that held a swap from one that never did.
        samples = page.evaluate(_PHOTO_SAMPLE_JS)
        failures.extend(spotlight_fade_failures(samples))
        # Not cut by any clipping ancestor either: the ratio above reads only
        # the image's own box, which a clipping ancestor leaves whole.
        failures.extend(photo_crop_failures(page.evaluate(_PHOTO_PAINT_JS)))
        motion = page.evaluate(_PHOTO_MOTION_JS)
        if motion:
            failures.append(f"spotlight photo is animated: {', '.join(motion)}")
    finally:
        jobs.delete(job_id)
    return failures


#: Measures what is painted, and what clips it. The painted content box is what
#: `object-fit: contain` draws, placed by `object-position` inside the image's
#: own content box; the clip is the intersection of the padding boxes of
#: `.spotlight-image-box` and of every ancestor above it whose overflow is not
#: visible (a height cap with `overflow: hidden` on the card content or the
#: card cuts the photo as surely as the box does). A transform, an individual
#: transform property or a `clip-path` on the image or that box scales or cuts
#: the photo without touching `object-fit`, and a `clip-path` on any ancestor
#: cuts it too, so each is reported.
_PHOTO_PAINT_JS = """() => {
    const img = document.querySelector('#spotlight-artist-img');
    const box = img.closest('.spotlight-image-box');
    if (!box) return {noBox: true};
    const px = value => Number.parseFloat(value) || 0;
    const style = getComputedStyle(img);
    const boxStyle = getComputedStyle(box);
    const rect = img.getBoundingClientRect();
    const boxRect = box.getBoundingClientRect();
    const inner = {
        left: rect.left + px(style.borderLeftWidth) + px(style.paddingLeft),
        top: rect.top + px(style.borderTopWidth) + px(style.paddingTop),
        right: rect.right - px(style.borderRightWidth) - px(style.paddingRight),
        bottom: rect.bottom - px(style.borderBottomWidth) - px(style.paddingBottom),
    };
    // What cuts the photo is every ancestor that clips: the photo box always
    // (it is the design's clip), and any other ancestor up to the page whose
    // overflow is not visible, each on the axes it clips. The page itself
    // (body, html) scrolls rather than crops, so it is not counted.
    const clip = {
        left: boxRect.left + px(boxStyle.borderLeftWidth),
        top: boxRect.top + px(boxStyle.borderTopWidth),
        right: boxRect.right - px(boxStyle.borderRightWidth),
        bottom: boxRect.bottom - px(boxStyle.borderBottomWidth),
    };
    const clippedBy = [];
    for (let el = box.parentElement; el && el !== document.body
            && el !== document.documentElement; el = el.parentElement) {
        const own = getComputedStyle(el);
        const clipsX = own.overflowX !== 'visible';
        const clipsY = own.overflowY !== 'visible';
        if (!clipsX && !clipsY) continue;
        const ownRect = el.getBoundingClientRect();
        if (clipsX) {
            clip.left = Math.max(clip.left, ownRect.left + px(own.borderLeftWidth));
            clip.right = Math.min(clip.right, ownRect.right - px(own.borderRightWidth));
        }
        if (clipsY) {
            clip.top = Math.max(clip.top, ownRect.top + px(own.borderTopWidth));
            clip.bottom = Math.min(clip.bottom,
                ownRect.bottom - px(own.borderBottomWidth));
        }
        clippedBy.push(el.id || el.className || el.tagName);
    }
    const innerWidth = inner.right - inner.left;
    const innerHeight = inner.bottom - inner.top;
    const scale = Math.min(innerWidth / img.naturalWidth, innerHeight / img.naturalHeight);
    const paintedWidth = img.naturalWidth * scale;
    const paintedHeight = img.naturalHeight * scale;
    const place = (token, free) => token.endsWith('%')
        ? (px(token) / 100) * free : px(token);
    const [positionX, positionY] = style.objectPosition.split(' ');
    const painted = {
        left: inner.left + place(positionX, innerWidth - paintedWidth),
        top: inner.top + place(positionY, innerHeight - paintedHeight),
    };
    painted.right = painted.left + paintedWidth;
    painted.bottom = painted.top + paintedHeight;
    const moved = [];
    for (let el = img; el && el !== document.documentElement;
            el = el.parentElement) {
        const own = getComputedStyle(el);
        const name = el === img ? 'the photo'
            : el === box ? 'the photo box' : `an ancestor (${el.id || el.tagName})`;
        // A transform only matters on the photo and its box, which scale it;
        // a clip-path cuts it wherever it sits.
        const properties = el === img || el === box
            ? ['transform', 'scale', 'translate', 'rotate', 'clipPath'] : ['clipPath'];
        properties.forEach(property => {
            if (own[property] && own[property] !== 'none') {
                moved.push(`${name} has ${property} ${own[property]}`);
            }
        });
    }
    return {
        noBox: false,
        objectFit: style.objectFit,
        painted,
        clip,
        clippedBy,
        moved,
    };
}"""

#: How far the painted photo may stray outside its clip before it is a crop.
_PAINT_EPSILON = 0.5


def photo_crop_failures(geometry: dict) -> list[str]:
    """Judge one reading of `_PHOTO_PAINT_JS`: is the whole photo shown?

    The photo is uncropped when what is painted -- placed by `object-fit` and
    the natural ratio -- lies inside the box its clipping ancestors leave it,
    and nothing scales or clips the image on the way. Deriving the painted box from the
    image element's own box would always fit it; the clipping ancestors are
    the thing that can cut the photo, and every one of them is consulted.
    """
    if geometry.get("noBox"):
        return ["spotlight photo has no .spotlight-image-box ancestor to clip it"]
    failures = []
    if geometry["objectFit"] != "contain":
        failures.append(
            f"spotlight photo object-fit is {geometry['objectFit']!r}, not 'contain'"
        )
    failures.extend(f"spotlight photo is cropped: {item}" for item in geometry["moved"])
    painted, clip = geometry["painted"], geometry["clip"]
    outside = [
        side
        for side, over in (
            ("left", clip["left"] - painted["left"]),
            ("top", clip["top"] - painted["top"]),
            ("right", painted["right"] - clip["right"]),
            ("bottom", painted["bottom"] - clip["bottom"]),
        )
        if over > _PAINT_EPSILON
    ]
    if outside:
        failures.append(
            "spotlight photo is cropped: its painted "
            f"{painted['right'] - painted['left']:.1f}x"
            f"{painted['bottom'] - painted['top']:.1f} content box leaves "
            f"the {clip['right'] - clip['left']:.1f}x"
            f"{clip['bottom'] - clip['top']:.1f} box that clips it on the "
            f"{', '.join(outside)}"
            + (
                f" (clipped by {', '.join(map(str, geometry['clippedBy']))})"
                if geometry.get("clippedBy")
                else ""
            )
        )
    return failures


def check_artist_spotlight_photo_not_cropped_when_non_square(
    page, base_url: str
) -> list[str]:
    """A non-square confirmed photo is shown whole, not cropped to fill the
    square photo box (F-B21-60): `object-fit` is `contain`, the painted
    photo lies inside the box its clipping ancestors leave it, and nothing scales or clips it."""
    job_id = _seed_spotlight_job()
    failures = []
    try:
        _install_spotlight_fetch_mock(page, NON_SQUARE_PHOTO_DATA_URL)
        page.goto(
            f"{base_url}{RESULTS_PATH}?job_id={job_id}",
            wait_until="domcontentloaded",
            timeout=10_000,
        )
        if not _wait_for_decoded_photo(page):
            failures.append("spotlight photo never loaded a confirmed image")
            return failures
        failures.extend(photo_crop_failures(page.evaluate(_PHOTO_PAINT_JS)))
    finally:
        jobs.delete(job_id)
    return failures


def check_artist_spotlight_card_hidden_with_no_photo(page, base_url: str) -> list[str]:
    """A candidate pool with no confirmed photo never reveals the card."""
    job_id = _seed_spotlight_job()
    failures = []
    try:
        _install_spotlight_fetch_mock(page, None)
        page.goto(
            f"{base_url}{RESULTS_PATH}?job_id={job_id}",
            wait_until="domcontentloaded",
            timeout=10_000,
        )
        # Hydration must have run before "still hidden" means anything: every
        # candidate was requested and its answer read. A page whose script
        # never ran would also leave the card hidden.
        try:
            page.wait_for_function(
                """() => {
                    const seeded = window.APP_DATA?.spotlight_artists?.length || 0;
                    return seeded > 0 && window.__spotlightRequests >= seeded
                        && window.__spotlightResponses >= seeded;
                }""",
                timeout=5_000,
            )
        except Exception:  # noqa: BLE001 - converted to an actionable gate failure
            counts = page.evaluate(
                """() => [window.APP_DATA?.spotlight_artists?.length || 0,
                    window.__spotlightRequests, window.__spotlightResponses]"""
            )
            failures.append(
                "spotlight hydration never ran, so a hidden card proves nothing: "
                f"{counts[0]} candidates, {counts[1]} requests, {counts[2]} answers"
            )
            return failures
        # The candidates settle in the microtasks after the last answer; two
        # frames and one sped-up rotation tick (200ms) cover a wrong reveal.
        page.evaluate(
            "() => new Promise(r => requestAnimationFrame(() => "
            "requestAnimationFrame(() => setTimeout(r, 300))))"
        )
        display = page.evaluate(
            "() => getComputedStyle(document.querySelector('#artist-spotlight-card')).display"
        )
        if display != "none":
            failures.append(
                f"spotlight card is visible ({display!r}) with no confirmed photo"
            )
    finally:
        jobs.delete(job_id)
    return failures


#: Five artists that break a narrow name column and a guessed card height:
#: nine-, eleven- and fourteen-letter words, a name long enough to clamp, and
#: many albums with a long play time, which is what wraps the subtitle to
#: four lines. `(name, albums, seconds per album)`.
LAYOUT_ARTISTS = (
    ("Radiohead", 8, 51_000),
    ("Sufjan Stevens", 1, 900),
    ("Godspeed You! Black Emperor", 12, 46_000),
    ("Springsteen", 1, 1_200),
    ("Ludwig van Beethoven", 3, 8_000),
)

#: Widths of the rail card's container at these viewports: a phone, the
#: 1024px breakpoint where the rail is 4/12 of the page (its narrowest
#: desktop card), a 1180px laptop, and a wide monitor.
LAYOUT_VIEWPORTS = (
    {"width": 320, "height": 800},
    {"width": 390, "height": 844},
    {"width": 1024, "height": 768},
    {"width": 1180, "height": 800},
    {"width": 1920, "height": 1000},
)

#: True once the card is revealed, after scrolling it into view.
_REVEAL_CARD_JS = """() => {
    const card = document.querySelector('#artist-spotlight-card');
    if (!card || getComputedStyle(card).display === 'none') return false;
    card.scrollIntoView();
    return true;
}"""

#: Resolves once the page's web fonts have loaded and a frame has drawn them.
_FONTS_SETTLED_JS = """() => document.fonts.ready.then(
    () => new Promise(resolve => requestAnimationFrame(() => resolve(true))))"""

#: Samples the card as the rotation steps through every candidate: which
#: artist is shown, the card's height, and every word of the name the browser
#: has broken in the middle. A word is broken when its own characters sit on
#: more than one line, which a Range over the word shows from its client rects.
_LAYOUT_SAMPLE_JS = """() => new Promise(resolve => {
    const card = document.querySelector('#artist-spotlight-card');
    const name = document.querySelector('#spotlight-artist-name');
    const brokenWords = () => {
        const text = name.firstChild;
        const broken = [];
        for (const match of text.textContent.matchAll(/\\S+/g)) {
            const range = document.createRange();
            range.setStart(text, match.index);
            range.setEnd(text, match.index + match[0].length);
            const lines = new Set([...range.getClientRects()]
                .map(rect => Math.round(rect.top)));
            if (lines.size > 1) broken.push(match[0]);
        }
        return broken;
    };
    const samples = [];
    const sample = () => samples.push({
        artist: card.dataset.artist,
        height: card.getBoundingClientRect().height,
        broken: brokenWords(),
    });
    sample();
    const interval = window.setInterval(sample, 40);
    window.setTimeout(() => {
        window.clearInterval(interval);
        resolve(samples);
    }, 1800);
})"""

#: A rendering tolerance for sub-pixel rounding in either browser.
_LAYOUT_EPSILON = 0.5


def spotlight_layout_failures(
    samples: list[dict], where: str, expected: int
) -> list[str]:
    """Judge the samples of `_LAYOUT_SAMPLE_JS` taken at one width.

    Every candidate must have been on screen (or the rotation never ran and
    nothing was compared), the card must keep one height across them, and the
    artist name's column must be at least as wide as its widest word.
    """
    failures = []
    artists = {sample["artist"] for sample in samples}
    if len(artists) < expected:
        failures.append(
            f"{where}: only {len(artists)} of {expected} spotlight candidates "
            "were on screen, so the card height was not compared"
        )
    heights = sorted({round(sample["height"], 1) for sample in samples})
    if heights and heights[-1] - heights[0] > _LAYOUT_EPSILON:
        failures.append(
            f"{where}: the card height changes between candidates: {heights}"
        )
    broken = sorted(
        {(sample["artist"], word) for sample in samples for word in sample["broken"]}
    )
    failures.extend(
        f"{where}: the name of {artist!r} breaks inside the word {word!r}"
        for artist, word in broken
    )
    return failures


def _open_spotlight_card(page, url: str, viewport: dict, where: str) -> str | None:
    """Load the results page at `viewport` and wait until its spotlight card is
    revealed, its photo decoded and its fonts settled. Returns a failure, or
    None when the card is ready to be sampled."""
    page.set_viewport_size(viewport)
    page.goto(url, wait_until="domcontentloaded", timeout=10_000)
    # On a narrow screen the rail sits far below the fold, and a lazy photo
    # below the fold is never fetched: bring the card into view once it is
    # revealed, as a reader scrolling to it would.
    try:
        page.wait_for_function(_REVEAL_CARD_JS, timeout=5_000)
    except Exception:  # noqa: BLE001 - converted to an actionable gate failure
        return f"{where}: the spotlight card was never revealed"
    if not _wait_for_decoded_photo(page):
        return f"{where}: photo never loaded a confirmed image"
    # Fonts load once the card first draws text and change every line's
    # height; the page settles once they have, and only the rotation is
    # judged from there.
    page.evaluate(_FONTS_SETTLED_JS)
    return None


def check_artist_spotlight_name_whole_and_card_height_fixed(
    page, base_url: str
) -> list[str]:
    """The spotlight's artist name is never broken inside a word, and the
    card is one height for every candidate, from a phone to a wide monitor
    (S2-1, S2-10). 1024px and 1180px are where the rail is narrowest. The
    card is also judged after a resize with no reload, because its reserved
    height is measured per layout."""
    job_id = _seed_spotlight_job(LAYOUT_ARTISTS)
    url = f"{base_url}{RESULTS_PATH}?job_id={job_id}"
    failures = []
    try:
        _install_spotlight_fetch_mock(page, SQUARE_PHOTO_DATA_URL, keep_rotating=True)
        narrow, wide = LAYOUT_VIEWPORTS[2], LAYOUT_VIEWPORTS[-1]
        steps = [(viewport, f"{viewport['width']}px") for viewport in LAYOUT_VIEWPORTS]
        steps.append(
            (wide, f"{wide['width']}px after a resize from {narrow['width']}px")
        )
        for index, (viewport, label) in enumerate(steps):
            where = f"spotlight card at {label}"
            if index == len(steps) - 1:
                # No reload: the page was left at `wide`, so start it at
                # `narrow` and widen it in place.
                error = _open_spotlight_card(page, url, narrow, where)
                page.set_viewport_size(wide)
                page.evaluate(_FONTS_SETTLED_JS)
            else:
                error = _open_spotlight_card(page, url, viewport, where)
            if error:
                failures.append(error)
                continue
            samples = page.evaluate(_LAYOUT_SAMPLE_JS)
            failures.extend(
                spotlight_layout_failures(samples, where, len(LAYOUT_ARTISTS))
            )
    finally:
        jobs.delete(job_id)
    return failures


#: What the link and the card say now, to compare before and after a hold.
_LINK_STATE_JS = """() => {
    const link = document.getElementById('spotlight-spotify-link');
    const card = document.getElementById('artist-spotlight-card');
    return {
        focused: document.activeElement === link,
        visible: link.getClientRects().length > 0,
        href: link.getAttribute('href'),
        label: link.getAttribute('aria-label'),
        artist: card.dataset.artist,
        ticks: window.__spotlightTicks,
    };
}"""

#: Rotation periods the card must sit through while held (S2-2: at least two).
HOLD_PERIODS = 3


def spotlight_hold_failures(before: dict, after: dict, held_by: str) -> list[str]:
    """Judge one hold: while `held_by` (focus or the pointer) was on the card,
    at least `HOLD_PERIODS` rotation periods passed and nothing changed."""
    failures = []
    passed = after["ticks"] - before["ticks"]
    if passed < HOLD_PERIODS:
        failures.append(
            f"spotlight hold ({held_by}): only {passed} rotation periods passed, "
            "so holding still was not tested"
        )
    for key in ("focused", "visible", "href", "label", "artist"):
        if held_by == "pointer" and key in ("focused", "visible"):
            continue
        if before[key] != after[key]:
            failures.append(
                f"spotlight hold ({held_by}): {key} changed from "
                f"{before[key]!r} to {after[key]!r} while the card was in use"
            )
    return failures


#: The one artist the re-measure hold answers without a Spotify URL, so that
#: measuring the tallest candidate would hide a focused link if it could.
REMEASURE_LINKLESS_ARTIST = "Springsteen"

#: Focuses the link once it is on screen (the current candidate has one);
#: false while the rotation shows the linkless candidate, so it is polled.
_FOCUS_VISIBLE_LINK_JS = """() => {
    const link = document.getElementById('spotlight-spotify-link');
    if (link.getClientRects().length === 0) return false;
    link.focus();
    return document.activeElement === link;
}"""

#: Counts what happens to the link (any attribute write, including one that
#: sets the value it already has) and how often the card's reserved height is
#: set, from now on. `reserveCardHeight` sets `min-height` on every pass.
_OBSERVE_REMEASURE_JS = """() => {
    const link = document.getElementById('spotlight-spotify-link');
    const card = document.getElementById('artist-spotlight-card');
    window.__linkWrites = 0;
    window.__cardMeasures = 0;
    new MutationObserver(records => { window.__linkWrites += records.length; })
        .observe(link, { attributes: true });
    new MutationObserver(records => { window.__cardMeasures += records.length; })
        .observe(card, { attributes: true, attributeFilter: ['style'] });
}"""

_REMEASURED_JS = "() => window.__cardMeasures > 0"

_REMEASURE_STATE_JS = """() => {
    const link = document.getElementById('spotlight-spotify-link');
    return {
        focused: document.activeElement === link,
        visible: link.getClientRects().length > 0,
        writes: window.__linkWrites,
        measures: window.__cardMeasures,
    };
}"""


def spotlight_remeasure_failures(state: dict) -> list[str]:
    """Judge a re-measure that ran while the reader had focus on the link.

    The card measures every candidate to reserve its height; a candidate with
    no Spotify URL hides the link while it is rendered. With focus on the
    link that pass must leave the link alone (`keepLink`), or focus drops to
    the page body (S2-2).
    """
    if not state["measures"]:
        return [
            "spotlight re-measure: the card's height was never re-measured "
            "after the resize, so the focused link was not tested"
        ]
    failures = []
    if not (state["focused"] and state["visible"]):
        failures.append(
            "spotlight re-measure: the link lost focus or was hidden while "
            "the card's height was re-measured"
        )
    if state["writes"]:
        failures.append(
            f"spotlight re-measure: the focused link was rewritten "
            f"{state['writes']} times while the card's height was re-measured"
        )
    return failures


def _remeasure_hold_failures(page, url: str) -> list[str]:
    """Focus the link, resize the card so it is re-measured, and judge it.

    Runs on a page of its own (same browser context), because it needs a
    candidate with no link and the hold check's other phases must never
    focus a link that a rotation step could hide.
    """
    # Imported here for the reason given in the check that calls this.
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    probe = page.context.new_page()
    try:
        _install_spotlight_fetch_mock(
            probe,
            SQUARE_PHOTO_DATA_URL,
            keep_rotating=True,
            linkless=(REMEASURE_LINKLESS_ARTIST,),
        )
        error = _open_spotlight_card(
            probe, url, LAYOUT_VIEWPORTS[3], "spotlight re-measure"
        )
        if error:
            return [error]
        probe.wait_for_function(_FOCUS_VISIBLE_LINK_JS, timeout=5_000)
        probe.evaluate(_OBSERVE_REMEASURE_JS)
        probe.set_viewport_size(LAYOUT_VIEWPORTS[2])
        try:
            probe.wait_for_function(_REMEASURED_JS, timeout=5_000)
        except PlaywrightTimeoutError:
            # Reported below by the measure count. Only a timeout is
            # tolerated: a crashed page or a script error propagates.
            pass
        return spotlight_remeasure_failures(probe.evaluate(_REMEASURE_STATE_JS))
    finally:
        probe.close()


def check_artist_spotlight_holds_still_while_focused_or_hovered(
    page, base_url: str
) -> list[str]:
    """The rotation never moves a link the reader is using: with keyboard
    focus on the Spotify link, or the pointer over the card, the link keeps
    its focus, its target and its name across several rotation periods, and
    a re-measure of the card's height leaves a focused link alone (S2-2)."""
    # Imported here, not at module level: the gate reports a missing
    # Playwright with the install command (`_load_playwright`), which a
    # module-level import would pre-empt with a bare ImportError.
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    job_id = _seed_spotlight_job(LAYOUT_ARTISTS)
    url = f"{base_url}{RESULTS_PATH}?job_id={job_id}"
    failures = []
    try:
        _install_spotlight_fetch_mock(page, SQUARE_PHOTO_DATA_URL, keep_rotating=True)
        error = _open_spotlight_card(page, url, LAYOUT_VIEWPORTS[3], "spotlight hold")
        if error:
            return [error]
        for held_by in ("focus", "pointer"):
            if held_by == "focus":
                page.focus("#spotlight-spotify-link")
            else:
                page.evaluate("() => document.activeElement.blur()")
                page.hover("#artist-spotlight-card")
            before = page.evaluate(_LINK_STATE_JS)
            try:
                page.wait_for_function(
                    f"() => window.__spotlightTicks >= {before['ticks'] + HOLD_PERIODS}",
                    timeout=5_000,
                )
            except PlaywrightTimeoutError:
                # Reported below by the tick count. Only a timeout is
                # tolerated: a crashed page or a script error propagates.
                pass
            failures.extend(
                spotlight_hold_failures(before, page.evaluate(_LINK_STATE_JS), held_by)
            )
        failures.extend(_remeasure_hold_failures(page, url))
    finally:
        jobs.delete(job_id)
    return failures
