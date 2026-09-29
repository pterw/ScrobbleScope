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
from scrobblescope.repositories import (
    create_job,
    delete_job,
    set_job_progress,
    set_job_results,
)

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
#: rule (F-B21-60 / B1). The square fixture above cannot: in a square box a
#: square photo looks the same whether it is cropped or contained.
NON_SQUARE_PHOTO_DATA_URL = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='300' height='200'%3E%3Crect width='300' height='200' "
    "fill='%23888'/%3E%3C/svg%3E"
)


def _seed_spotlight_job() -> str:
    """Create a job with several artists, so `spotlight_artists` samples more
    than one candidate. Each album carries a non-empty, distinguishable
    `album_image` -- not a `""` placeholder -- so a check that seeds a job
    this way exercises the real path a live job takes: an album cover exists
    and must never leak into `image_url` as a fake artist photo (F-B21-60,
    Round 2 V1). What each artist's *confirmed* photo resolves to is decided
    separately, by `_install_spotlight_fetch_mock`."""
    job_id = create_job(
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
    set_job_results(
        job_id,
        [
            {
                "artist": f"Photo Artist {index}",
                "album": f"Photo Album {index}",
                "play_count": 20 - index,
                "play_time": "42m",
                "play_time_seconds": 2520 - index,
                "release_date": "2025-01-01",
                "album_image": f"https://example.com/photo-album-{index}-cover.jpg",
                "spotify_id": f"photo-album-{index}",
            }
            for index in range(10)
        ],
    )
    set_job_progress(job_id, progress=100, message="Done", error=False)
    return job_id


def _install_spotlight_fetch_mock(page, image_url: str | None) -> None:
    """Mock `/api/artist_spotlight` and speed up the 7s rotation interval.

    Unlike the mock `check_artist_spotlight_rotation` installs (one slow
    candidate among fast ones), this one answers every artist immediately with
    the same `image_url` (a photo, or `null`), which is all these checks need.
    It counts what the page asked for and what it read back
    (`window.__spotlightRequests` / `__spotlightResponses`), so a check can
    prove hydration ran instead of waiting a fixed time and hoping."""
    page.add_init_script(
        f"""(() => {{
            const nativeInterval = window.setInterval;
            const nativeFetch = window.fetch.bind(window);
            window.__spotlightPhotoUrl = {json.dumps(image_url)};
            window.__spotlightRequests = 0;
            window.__spotlightResponses = 0;
            window.setInterval = (callback, delay, ...args) => {{
                if (delay === 7000) return window.setTimeout(callback, 200, ...args);
                return nativeInterval(callback, delay, ...args);
            }};
            window.fetch = (resource, options) => {{
                const url = String(resource);
                if (!url.includes('/api/artist_spotlight?')) {{
                    return nativeFetch(resource, options);
                }}
                window.__spotlightRequests += 1;
                return Promise.resolve({{
                    ok: true,
                    json: async () => {{
                        window.__spotlightResponses += 1;
                        return {{
                            image_url: window.__spotlightPhotoUrl,
                            spotify_url: window.__spotlightPhotoUrl
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


def check_artist_spotlight_photo_has_no_crop_overlay_or_animation(
    page, base_url: str
) -> list[str]:
    """A confirmed spotlight photo is shown uncropped, unobscured and still."""
    job_id = _seed_spotlight_job()
    failures = []
    try:
        _install_spotlight_fetch_mock(page, SQUARE_PHOTO_DATA_URL)
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
        # deleted opacity handoff (Step 3) animated `#spotlight-card-content`,
        # not the <img> itself, so both are sampled -- and none of them runs
        # an animation or transitions transform or filter.
        opacity_samples = page.evaluate(
            """() => new Promise(resolve => {
                const img = document.querySelector('#spotlight-artist-img');
                const content = document.querySelector('#spotlight-card-content');
                const samples = [];
                const sample = () => samples.push([
                    getComputedStyle(img).opacity,
                    getComputedStyle(content).opacity,
                ]);
                sample();
                const interval = window.setInterval(sample, 40);
                window.setTimeout(() => {
                    window.clearInterval(interval);
                    resolve(samples);
                }, 400);
            })"""
        )
        distinct = {tuple(sample) for sample in opacity_samples}
        if len(distinct) > 1:
            failures.append(
                f"spotlight photo opacity changed during a rotation tick: {opacity_samples}"
            )
        motion = page.evaluate(_PHOTO_MOTION_JS)
        if motion:
            failures.append(f"spotlight photo is animated: {', '.join(motion)}")
    finally:
        delete_job(job_id)
    return failures


#: Measures what is painted, and what clips it. The painted content box is what
#: `object-fit: contain` draws, placed by `object-position` inside the image's
#: own content box; the clip is the padding box of `.spotlight-image-box`,
#: which is what its `overflow: hidden` cuts to. A transform, an individual
#: transform property or a `clip-path` on the image or that box scales or cuts
#: the photo without touching `object-fit`, so each is reported.
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
    const clip = {
        left: boxRect.left + px(boxStyle.borderLeftWidth),
        top: boxRect.top + px(boxStyle.borderTopWidth),
        right: boxRect.right - px(boxStyle.borderRightWidth),
        bottom: boxRect.bottom - px(boxStyle.borderBottomWidth),
    };
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
    for (let el = img; el; el = el === box ? null : el.parentElement) {
        const own = getComputedStyle(el);
        const name = el === img ? 'the photo' : 'the photo box';
        ['transform', 'scale', 'translate', 'rotate', 'clipPath'].forEach(property => {
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
        moved,
    };
}"""

#: How far the painted photo may stray outside its clip before it is a crop.
_PAINT_EPSILON = 0.5


def photo_crop_failures(geometry: dict) -> list[str]:
    """Judge one reading of `_PHOTO_PAINT_JS`: is the whole photo shown?

    The photo is uncropped when what is painted -- placed by `object-fit` and
    the natural ratio -- lies inside the box that clips it, and nothing
    scales or clips the image on the way. Deriving the painted box from the
    image element's own box would always fit it; the clipping ancestor is the
    thing that can cut the photo.
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
        )
    return failures


def check_artist_spotlight_photo_not_cropped_when_non_square(
    page, base_url: str
) -> list[str]:
    """A non-square confirmed photo is shown whole, not cropped to fill the
    square photo box (F-B21-60 / B1): `object-fit` is `contain`, the painted
    photo lies inside the box that clips it, and nothing scales or clips it."""
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
        delete_job(job_id)
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
        delete_job(job_id)
    return failures
