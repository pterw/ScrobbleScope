"""The official Spotify icon check: size, file, clear space and link target.

A slice of the frontend gate (F-B21-51), added for F-B21-60 part 2. Spotify's
design guidelines set three rules this module measures in a real browser:
the icon is never smaller than 21px, it keeps a clear space of half its own
height, and it is black on light backgrounds and white on dark ones unless the
background is pure black or white (the app's surfaces are neither). Which file
shows is a theme decision made in CSS, so each theme is measured separately.

Two more checks live here: the "Save image" JPEG must carry the icon at
Spotify's minimum size in both engines (Firefox once shrank it to 12.7px), and
under forced colours the icon file follows the system palette, not the saved
theme.

``spotify_icon_failures`` is shared with the results-list attribution check in
``_frontend_gate_results``; the spotlight check here reuses the spotlight
photo slice's job seed and ``/api/artist_spotlight`` mock.
"""

from __future__ import annotations

from base64 import b64encode
from pathlib import Path

from scripts.dev._frontend_gate_spotlight_photo import (
    RESULTS_PATH,
    SQUARE_PHOTO_DATA_URL,
    _install_spotlight_fetch_mock,
    _seed_spotlight_job,
)
from scrobblescope import jobs

#: Spotify's digital minimum for the icon on its own.
MIN_ICON_PX = 21

#: The minimum touch target (docs/agents/ui-accessibility.md).
MIN_TARGET_PX = 44

#: The official file each theme must show, as committed under
#: static/images/brand/spotify/ with Spotify's own file names.
ICON_FILE_FOR_THEME = {
    "light": "/static/images/brand/spotify/Primary_Logo_Black_RGB.svg",
    "dark": "/static/images/brand/spotify/Primary_Logo_White_RGB.svg",
}

#: The artist URL `_install_spotlight_fetch_mock` answers with.
SPOTLIGHT_ARTIST_URL = "https://open.spotify.com/artist/photo"

#: Measures the visible `.spotify-icon` inside `container` and, when
#: `clearScope` is given, the nearest box inside that scope which is neither
#: the icon nor one of its ancestors -- text beside the icon in the same
#: container counts, because the clear space applies to it too.
_ICON_PROBE = """([containerSelector, clearScopeSelector]) => {
    const container = document.querySelector(containerSelector);
    if (!container) return {missing: true};
    const shown = [...container.querySelectorAll('img.spotify-icon')]
        .filter(img => getComputedStyle(img).display !== 'none');
    const report = {missing: false, shown: shown.length};
    if (shown.length !== 1) return report;
    const icon = shown[0];
    const box = icon.getBoundingClientRect();
    report.width = box.width;
    report.height = box.height;
    report.src = new URL(icon.currentSrc || icon.src).pathname;
    report.loaded = icon.complete && icon.naturalWidth > 0;
    const scope = clearScopeSelector && document.querySelector(clearScopeSelector);
    if (!scope) return report;
    let nearest = null;
    scope.querySelectorAll('*').forEach(el => {
        if (el.contains(icon)) return;
        const other = el.getBoundingClientRect();
        if (other.width === 0 || other.height === 0) return;
        if (getComputedStyle(el).visibility === 'hidden') return;
        const dx = Math.max(other.left - box.right, box.left - other.right, 0);
        const dy = Math.max(other.top - box.bottom, box.top - other.bottom, 0);
        const gap = Math.hypot(dx, dy);
        if (!nearest || gap < nearest.gap) {
            nearest = {gap, name: el.id || String(el.className).slice(0, 60) || el.tagName};
        }
    });
    report.nearest = nearest;
    return report;
}"""

#: True once every icon file that is displayed inside the container has been
#: fetched and decoded. `img.complete` is also true for a file that failed, so
#: a natural width above zero is what says it loaded.
_ICON_LOADED_JS = """containerSelector => {
    const container = document.querySelector(containerSelector);
    if (!container) return true;
    return [...container.querySelectorAll('img.spotify-icon')]
        .filter(img => getComputedStyle(img).display !== 'none')
        .every(img => img.complete && img.naturalWidth > 0);
}"""

#: The displayed icon files' paths, to name the one that did not load.
_ICON_NAMES_JS = """containerSelector => [...document.querySelector(containerSelector)
    .querySelectorAll('img.spotify-icon')]
    .filter(img => getComputedStyle(img).display !== 'none')
    .map(img => new URL(img.currentSrc || img.src).pathname)"""

#: How long an icon file may take to load before it counts as not loading.
ICON_LOAD_TIMEOUT_MS = 5_000


def spotify_icon_failures(
    page, container: str, where: str, clear_scope: str | None = None
) -> list[str]:
    """Check the Spotify icon inside `container` in both themes.

    Exactly one icon file shows per theme, it is the official file for that
    theme, it has loaded, and it renders at least 21px on both axes. With
    `clear_scope`, no other element inside that scope comes closer to the icon
    than half the icon's rendered height.
    """
    failures = []
    for theme, expected_src in ICON_FILE_FOR_THEME.items():
        page.evaluate(
            "theme => document.documentElement.setAttribute('data-theme', theme)",
            theme,
        )
        label = f"{where} [{theme}]"
        # The theme decides which file shows, and a file that has only just
        # been chosen may still be loading: judge it once it has, not before.
        try:
            page.wait_for_function(
                _ICON_LOADED_JS, arg=container, timeout=ICON_LOAD_TIMEOUT_MS
            )
        except Exception:  # noqa: BLE001 - converted to an actionable gate failure
            names = page.evaluate(_ICON_NAMES_JS, container)
            failures.append(
                f"{label}: Spotify icon file {names!r} did not load within "
                f"{ICON_LOAD_TIMEOUT_MS}ms"
            )
            continue
        report = page.evaluate(_ICON_PROBE, [container, clear_scope])
        if report["missing"]:
            failures.append(f"{label}: no {container} element to hold the Spotify icon")
            return failures
        if report["shown"] != 1:
            failures.append(
                f"{label}: {report['shown']} Spotify icon files are displayed, expected 1"
            )
            continue
        if report["src"] != expected_src:
            failures.append(
                f"{label}: Spotify icon shows {report['src']!r}, expected {expected_src!r}"
            )
        if not report["loaded"]:
            failures.append(
                f"{label}: Spotify icon file {report['src']!r} did not load"
            )
        smaller = min(report["width"], report["height"])
        if smaller < MIN_ICON_PX:
            failures.append(
                f"{label}: Spotify icon renders {report['width']:.1f}x"
                f"{report['height']:.1f}px, below the {MIN_ICON_PX}px minimum"
            )
        nearest = report.get("nearest")
        clear_space = report["height"] / 2
        if nearest and nearest["gap"] + 0.5 < clear_space:
            failures.append(
                f"{label}: {nearest['name']!r} is {nearest['gap']:.1f}px from the "
                f"Spotify icon, inside its {clear_space:.1f}px clear space"
            )
    return failures


def check_spotlight_spotify_icon_size_and_link_target(page, base_url: str) -> list[str]:
    """The spotlight's Spotify link shows the official icon at 21px or more,
    with its clear space and a 44px target, and links to the shown artist."""
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
                """() => {
                    const link = document.querySelector('#spotlight-spotify-link');
                    return link && !link.classList.contains('hidden')
                        && [...link.querySelectorAll('img')].every(img => img.complete);
                }""",
                timeout=5_000,
            )
        except Exception:  # noqa: BLE001 - converted to an actionable gate failure
            failures.append("spotlight Spotify link was never revealed")
            return failures

        link = page.evaluate(
            """() => {
                const link = document.querySelector('#spotlight-spotify-link');
                const box = link.getBoundingClientRect();
                return {
                    href: link.getAttribute('href'),
                    target: link.getAttribute('target'),
                    label: link.getAttribute('aria-label') || '',
                    width: box.width,
                    height: box.height,
                };
            }"""
        )
        if link["href"] != SPOTLIGHT_ARTIST_URL:
            failures.append(
                f"spotlight Spotify link targets {link['href']!r}, "
                f"expected the artist's Spotify URL {SPOTLIGHT_ARTIST_URL!r}"
            )
        if link["target"] != "_blank":
            failures.append("spotlight Spotify link does not open a new tab")
        if "on Spotify" not in link["label"]:
            failures.append(
                f"spotlight Spotify link's accessible name {link['label']!r} "
                "does not say it opens Spotify"
            )
        if min(link["width"], link["height"]) < MIN_TARGET_PX:
            failures.append(
                f"spotlight Spotify link target is {link['width']:.1f}x"
                f"{link['height']:.1f}px, below {MIN_TARGET_PX}px"
            )
        failures.extend(
            spotify_icon_failures(
                page,
                "#spotlight-spotify-link",
                "spotlight Spotify link",
                clear_scope="#artist-spotlight-card",
            )
        )
    finally:
        jobs.delete(job_id)
    return failures


#: One Spotify-sourced row, enough for the results list to show its attribution.
_SPOTIFY_ROW = {
    "artist": "Spotify Artist",
    "album": "Spotify Album",
    "play_count": 30,
    "play_time_seconds": 60,
    "play_time": "1m",
    "release_date": "2025-01-02",
    "album_image": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
    "spotify_id": "sp-icon-1",
    "provider": "spotify",
    "album_url": "https://open.spotify.com/album/sp-icon-1",
}

#: The visible icon's box, relative to the export wrapper.
_EXPORT_ICON_BOX_JS = """() => {
    const icon = [...document.querySelectorAll('#results-spotify-attribution img.spotify-icon')]
        .find(img => getComputedStyle(img).display !== 'none');
    const wrapper = document.querySelector('#results-table-wrapper').getBoundingClientRect();
    const rect = icon.getBoundingClientRect();
    return {x: rect.left - wrapper.left, y: rect.top - wrapper.top,
            width: rect.width, height: rect.height};
}"""

#: The size, in page pixels, of the ink inside the icon's box on the saved
#: JPEG: the bounding box of pixels that contrast with the strip's own surface,
#: searched 8px around the on-page box (the clear space keeps text out of it).
_EXPORT_INK_JS = """async ([data, box]) => {
    const image = new Image();
    image.src = 'data:image/jpeg;base64,' + data;
    await image.decode();
    const scale = image.width / 1200;
    const canvas = document.createElement('canvas');
    canvas.width = image.width;
    canvas.height = image.height;
    const context = canvas.getContext('2d');
    context.drawImage(image, 0, 0);
    const tone = (p, i) => (p[i] + p[i + 1] + p[i + 2]) / 3;
    const corner = context.getImageData(Math.round(4 * scale), Math.round(4 * scale), 1, 1).data;
    const surface = tone(corner, 0);
    const margin = 8 * scale;
    const x0 = Math.round(box.x * scale - margin);
    const y0 = Math.round(box.y * scale - margin);
    const w = Math.round(box.width * scale + 2 * margin);
    const h = Math.round(box.height * scale + 2 * margin);
    const pixels = context.getImageData(x0, y0, w, h).data;
    let minX = Infinity, maxX = -1, minY = Infinity, maxY = -1;
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            if (Math.abs(tone(pixels, (y * w + x) * 4) - surface) > 100) {
                minX = Math.min(minX, x); maxX = Math.max(maxX, x);
                minY = Math.min(minY, y); maxY = Math.max(maxY, y);
            }
        }
    }
    if (maxX < 0) return {width: 0, height: 0};
    return {width: (maxX - minX + 1) / scale, height: (maxY - minY + 1) / scale};
}"""


def check_export_icon_keeps_its_size(page, base_url: str) -> list[str]:
    """The saved JPEG shows the Spotify icon at least 21px on both axes.

    Firefox drew the raster the export hands html2canvas at half its size, so
    the image carried Spotify artwork with an icon of 12.7px, under Spotify's
    minimum. The ink inside the icon's box on the decoded download, divided by
    the export's scale, must clear MIN_ICON_PX in whichever engine runs this.
    """
    job_id = jobs.create({"username": "gate", "year": 2025, "sort_mode": "playcount"})
    try:
        jobs.succeed(job_id, [_SPOTIFY_ROW], "Done")
        page.route("**/api/artist_spotlight?*", lambda route: route.fulfill(json={}))
        page.goto(
            f"{base_url}/results?job_id={job_id}",
            wait_until="domcontentloaded",
            timeout=10_000,
        )
        page.evaluate(
            "() => document.documentElement.setAttribute('data-theme', 'light')"
        )
        page.wait_for_function(
            _ICON_LOADED_JS, arg="#results-spotify-attribution", timeout=5_000
        )
        box = page.evaluate(_EXPORT_ICON_BOX_JS)
        with page.expect_download(timeout=20_000) as downloaded:
            page.locator("#save-image").click()
        image_bytes = Path(downloaded.value.path()).read_bytes()
        ink = page.evaluate(
            _EXPORT_INK_JS, [b64encode(image_bytes).decode("ascii"), box]
        )
    # Gate boundary: any failure becomes a reported FAIL line, not a crash.
    except Exception as exc:  # noqa: BLE001
        return [f"JPEG export (Spotify icon size) failed: {type(exc).__name__}: {exc}"]
    finally:
        page.unroute("**/api/artist_spotlight?*")
        jobs.delete(job_id)
    if min(ink["width"], ink["height"]) < MIN_ICON_PX:
        return [
            f"JPEG export shows the Spotify icon at {ink['width']:.1f}x"
            f"{ink['height']:.1f}px, below the {MIN_ICON_PX}px minimum"
        ]
    return []


def check_spotify_icon_follows_system_under_forced_colors(
    page, base_url: str
) -> list[str]:
    """Under forced colours the icon file follows the system palette.

    The saved theme can disagree with the system's palette, and forced colours
    repaint the page in the system's, so the file chosen from the saved theme
    is black on black or white on white and vanishes. Each system scheme is
    paired with the opposite saved theme and must still show its own file.
    """
    job_id = jobs.create({"username": "gate", "year": 2025, "sort_mode": "playcount"})
    failures = []
    try:
        jobs.succeed(job_id, [_SPOTIFY_ROW], "Done")
        page.route("**/api/artist_spotlight?*", lambda route: route.fulfill(json={}))
        page.goto(
            f"{base_url}/results?job_id={job_id}",
            wait_until="domcontentloaded",
            timeout=10_000,
        )
        for scheme, saved_theme in (("light", "dark"), ("dark", "light")):
            page.emulate_media(forced_colors="active", color_scheme=scheme)
            page.evaluate(
                "theme => document.documentElement.setAttribute('data-theme', theme)",
                saved_theme,
            )
            page.wait_for_function(
                _ICON_LOADED_JS, arg="#results-spotify-attribution", timeout=5_000
            )
            report = page.evaluate(_ICON_PROBE, ["#results-spotify-attribution", None])
            label = f"forced colors, system {scheme}, saved theme {saved_theme}"
            if report.get("shown") != 1:
                failures.append(
                    f"{label}: {report.get('shown')} Spotify icon files are "
                    "displayed, expected 1"
                )
            elif report["src"] != ICON_FILE_FOR_THEME[scheme]:
                failures.append(
                    f"{label}: Spotify icon shows {report['src']!r}, expected "
                    f"{ICON_FILE_FOR_THEME[scheme]!r} for the system palette"
                )
    # Gate boundary: any failure becomes a reported FAIL line, not a crash.
    except Exception as exc:  # noqa: BLE001
        failures.append(
            f"forced-colors Spotify icon check failed: {type(exc).__name__}: {exc}"
        )
    finally:
        page.emulate_media(forced_colors="null", color_scheme="null")
        page.unroute("**/api/artist_spotlight?*")
        jobs.delete(job_id)
    return failures
