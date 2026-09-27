"""The artist spotlight photo check: no crop, no overlay, no animation, no fake.

A slice of the frontend gate (F-B21-51), added for F-B21-60 part 1. The
pre-existing ``check_artist_spotlight_rotation`` in ``_frontend_gate_pipeline``
tests a different property -- that hydration replaces a stale response, not
photo geometry -- so this module owns its own job seed and its own mocked
``/api/artist_spotlight`` route, the same way that check already does.
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
    """Mock `/api/artist_spotlight` and speed up the 7s rotation interval, the
    same way `check_artist_spotlight_rotation` does. Every artist resolves to
    the same `image_url` (a photo, or `null`), which is all these checks need."""
    page.add_init_script(
        f"""(() => {{
            const nativeInterval = window.setInterval;
            const nativeFetch = window.fetch.bind(window);
            window.__spotlightPhotoUrl = {json.dumps(image_url)};
            window.setInterval = (callback, delay, ...args) => {{
                if (delay === 7000) return window.setTimeout(callback, 200, ...args);
                return nativeInterval(callback, delay, ...args);
            }};
            window.fetch = (resource, options) => {{
                const url = String(resource);
                if (!url.includes('/api/artist_spotlight?')) {{
                    return nativeFetch(resource, options);
                }}
                return Promise.resolve({{
                    ok: true,
                    json: async () => ({{
                        image_url: window.__spotlightPhotoUrl,
                        spotify_url: window.__spotlightPhotoUrl
                            ? 'https://open.spotify.com/artist/photo'
                            : null,
                    }}),
                }});
            }};
        }})();"""
    )


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
        try:
            page.wait_for_function(
                "() => document.querySelector('#spotlight-artist-img')?.src",
                timeout=5_000,
            )
        except Exception:  # noqa: BLE001 - converted to an actionable gate failure
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

        # No overlay: nothing else's box intersects the photo's box.
        overlap = page.evaluate(
            """() => {
                const img = document.querySelector('#spotlight-artist-img');
                const photo = img.getBoundingClientRect();
                const card = document.querySelector('#artist-spotlight-card');
                const offenders = [];
                card.querySelectorAll('*').forEach(el => {
                    if (el === img || el.contains(img)) return;
                    const box = el.getBoundingClientRect();
                    if (box.width === 0 || box.height === 0) return;
                    const intersects = box.left < photo.right && box.right > photo.left
                        && box.top < photo.bottom && box.bottom > photo.top;
                    if (intersects) offenders.push(el.id || el.className || el.tagName);
                });
                return offenders;
            }"""
        )
        if overlap:
            failures.append(
                f"spotlight photo is overlaid by: {', '.join(str(o) for o in overlap)}"
            )

        # No animation: the photo and its wrapping content never fade -- the
        # deleted opacity handoff (Step 3) animated `#spotlight-card-content`,
        # not the <img> itself, so both are sampled.
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
    finally:
        delete_job(job_id)
    return failures


def check_artist_spotlight_photo_not_cropped_when_non_square(
    page, base_url: str
) -> list[str]:
    """A non-square confirmed photo is shown whole, not cropped to fill the
    square photo box (F-B21-60 / B1): `object-fit` is `contain`, and the
    photo's own aspect ratio -- not the box's -- decides its rendered size."""
    job_id = _seed_spotlight_job()
    failures = []
    try:
        _install_spotlight_fetch_mock(page, NON_SQUARE_PHOTO_DATA_URL)
        page.goto(
            f"{base_url}{RESULTS_PATH}?job_id={job_id}",
            wait_until="domcontentloaded",
            timeout=10_000,
        )
        try:
            page.wait_for_function(
                "() => document.querySelector('#spotlight-artist-img')?.src",
                timeout=5_000,
            )
        except Exception:  # noqa: BLE001 - converted to an actionable gate failure
            failures.append("spotlight photo never loaded a confirmed image")
            return failures

        geometry = page.evaluate(
            """() => {
                const img = document.querySelector('#spotlight-artist-img');
                const rect = img.getBoundingClientRect();
                return {
                    objectFit: getComputedStyle(img).objectFit,
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                    width: rect.width,
                    height: rect.height,
                };
            }"""
        )
        if geometry["objectFit"] != "contain":
            failures.append(
                f"spotlight photo object-fit is {geometry['objectFit']!r}, not 'contain'"
            )

        natural_ratio = geometry["naturalWidth"] / geometry["naturalHeight"]
        box_width = geometry["width"]
        box_height = geometry["height"]
        # The whole-photo content box `object-fit: contain` paints, scaled to
        # fit inside the element's own box while keeping the photo's ratio.
        if natural_ratio >= (box_width / box_height):
            content_width, content_height = box_width, box_width / natural_ratio
        else:
            content_width, content_height = box_height * natural_ratio, box_height
        epsilon = 0.5
        if content_width > box_width + epsilon or content_height > box_height + epsilon:
            failures.append(
                "spotlight photo's whole-image content box "
                f"({content_width:.1f}x{content_height:.1f}) does not fit inside its "
                f"element box ({box_width:.1f}x{box_height:.1f})"
            )
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
        # Give every hydrateCandidate call, and one sped-up rotation tick,
        # time to settle before asserting the card stayed hidden throughout.
        page.wait_for_timeout(600)
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
