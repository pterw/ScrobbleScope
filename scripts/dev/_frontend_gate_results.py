"""Browser checks for results sorting, export data, and safe text rendering."""

from base64 import b64encode
from pathlib import Path

from scripts.dev._frontend_gate_colour import (
    _composite_over,
    _contrast_ratio,
    _parse_rgb_string,
)
from scrobblescope.domain import format_album_key, normalize_name
from scrobblescope.repositories import (
    create_job,
    delete_job,
    set_job_release_check,
    set_job_results,
)


def check_results_interactions(page, base_url: str) -> list[str]:
    """Exercise real controls with reversed ranks and markup-shaped metric text.

    Reuse the configured page so CDN policy and navigation deadlines survive.
    Remove only this check's route and job afterward. CSV follows visible ranks.
    """
    job_id = create_job({"username": "gate", "year": 2025, "sort_mode": "playcount"})
    probe = page
    failures = []

    def empty_spotlight(route):
        """Keep this fixture independent of Spotify availability."""
        route.fulfill(json={})

    try:
        set_job_results(
            job_id,
            [
                {
                    "artist": "First",
                    "album": "Count winner",
                    "play_count": 30,
                    "play_time_seconds": 60,
                    "play_time": "1m",
                    "release_date": "2025-01-02",
                },
                {
                    "artist": "Second",
                    "album": "Time winner",
                    "play_count": 20,
                    "play_time_seconds": 120,
                    "play_time": "2m",
                    "release_date": "2025-02-03",
                },
            ],
        )
        probe.route("**/api/artist_spotlight?*", empty_spotlight)
        probe.goto(f"{base_url}/results?job_id={job_id}", wait_until="domcontentloaded")
        failures.extend(_check_results_scale(probe))
        probe.locator("#toggle-sort-playtime").click()
        rows = probe.locator("#results-table tbody tr")
        if rows.first.get_attribute("data-album") != "Time winner":
            failures.append("listening-time toggle did not reorder albums")
        with probe.expect_download() as downloaded:
            probe.locator("#export-csv").click()
        csv_text = Path(downloaded.value.path()).read_text(encoding="utf-8")
        if '"1","Time winner","Second","2m","2025-02-03",""' not in csv_text:
            failures.append(
                "CSV lost the visible rank, single metric, or full date after sorting"
            )
        for theme in ("light", "dark"):
            probe.evaluate(
                "theme => document.documentElement.dataset.theme = theme", theme
            )
            failures.extend(_check_jpeg_export(probe, theme))
        weights = probe.locator(".metric-toggle-btn").evaluate_all(
            "nodes => nodes.map(node => getComputedStyle(node).fontWeight)"
        )
        if any(weight not in {"300", "400", "700"} for weight in weights):
            failures.append("metric toggle uses an unsupported font weight")
        probe.locator("#toggle-sort-plays").click()
        if rows.first.get_attribute("data-album") != "Count winner":
            failures.append("track-play toggle did not restore ordering")
        probe.evaluate("""() => {
            document.querySelector('#results-table tbody tr').dataset.playTime =
                '<img src=x onerror=window.__metricInjection=true>';
        }""")
        probe.locator("#toggle-sort-playtime").click()
        if probe.locator(".metric-value-cell img").count():
            failures.append("metric text was interpreted as markup")
        if probe.locator("#toastContainer .alert").count() == 0:
            failures.append("results controls no longer report actions through toasts")
    finally:
        try:
            probe.unroute("**/api/artist_spotlight?*", empty_spotlight)
        finally:
            delete_job(job_id)
    return failures


def check_results_provider_attribution(page, base_url: str) -> list[str]:
    """A row's link and provider badge follow its own provider (Batch 22 WP-1 Task 6).

    One Spotify-sourced row and one Deezer-sourced row must each link to
    their own provider's album page (not a hardcoded open.spotify.com URL
    built from spotify_id) and carry a visible, provider-labelled
    attribution link -- the interim text form recorded next to the markup
    in templates/results.html pending each provider's official logo asset
    (F-B22-4).
    """
    job_id = create_job({"username": "gate", "year": 2025, "sort_mode": "playcount"})
    probe = page
    failures = []

    def empty_spotlight(route):
        route.fulfill(json={})

    try:
        set_job_results(
            job_id,
            [
                {
                    "artist": "Spotify Artist",
                    "album": "Spotify Album",
                    "play_count": 30,
                    "play_time_seconds": 60,
                    "play_time": "1m",
                    "release_date": "2025-01-02",
                    "album_image": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
                    "spotify_id": "sp-gate-1",
                    "provider": "spotify",
                    "album_url": "https://open.spotify.com/album/sp-gate-1",
                },
                {
                    "artist": "Deezer Artist",
                    "album": "Deezer Album",
                    "play_count": 20,
                    "play_time_seconds": 120,
                    "play_time": "2m",
                    "release_date": "2025-02-03",
                    "album_image": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
                    "spotify_id": "",
                    "provider": "deezer",
                    "album_url": "https://www.deezer.com/album/dz-gate-1",
                },
            ],
        )
        probe.route("**/api/artist_spotlight?*", empty_spotlight)
        probe.goto(f"{base_url}/results?job_id={job_id}", wait_until="domcontentloaded")

        rows = probe.locator("#results-table tbody tr")
        by_provider = {
            row.get_attribute("data-provider"): row
            for row in [rows.nth(i) for i in range(rows.count())]
        }

        for provider, host in (
            ("spotify", "open.spotify.com"),
            ("deezer", "deezer.com"),
        ):
            row = by_provider.get(provider)
            if row is None:
                failures.append(f"results table has no {provider}-sourced row")
                continue
            album_link = row.locator("a.album-link")
            href = album_link.get_attribute("href") or ""
            if host not in href:
                failures.append(
                    f"{provider} row's album link is {href!r}, expected it to contain {host!r}"
                )
            badge = row.locator("a.provider-badge")
            if badge.count() == 0:
                failures.append(f"{provider} row renders no provider attribution badge")
                continue
            if badge.first.is_hidden():
                failures.append(f"{provider} row's provider badge is not visible")
            badge_href = badge.first.get_attribute("href") or ""
            if host not in badge_href:
                failures.append(
                    f"{provider} row's provider badge links to {badge_href!r}, "
                    f"expected it to contain {host!r}"
                )
            if provider not in (badge.first.text_content() or "").strip().lower():
                failures.append(
                    f"{provider} row's provider badge does not name its provider"
                )

        with probe.expect_download() as downloaded:
            probe.locator("#export-csv").click()
        csv_text = Path(downloaded.value.path()).read_text(encoding="utf-8")
        if '"spotify"' not in csv_text or '"deezer"' not in csv_text:
            failures.append("CSV export is missing the Provider column values")
    finally:
        try:
            probe.unroute("**/api/artist_spotlight?*", empty_spotlight)
        finally:
            delete_job(job_id)
    return failures


#: WCAG AA for body text. The correction note is small, muted type, so the
#: large-text allowance does not apply to it.
_TEXT_CONTRAST_FLOOR = 4.5


def _release_check_row(artist, album, release_date):
    """Build a gate result carrying the key the marker is addressed by."""
    return {
        "artist": artist,
        "album": album,
        "play_count": 30,
        "play_time_seconds": 60,
        "play_time": "1m",
        "release_date": release_date,
        "provider": "spotify",
        "album_url": "https://open.spotify.com/album/sp-gate-1",
        "_normalized_key": normalize_name(artist, album),
    }


def _row_tops(page):
    """Return each row's viewport top, keyed by album key."""
    return page.evaluate(
        """() => Object.fromEntries(
            [...document.querySelectorAll('#results-table tbody tr')].map(
                row => [row.dataset.albumKey, row.getBoundingClientRect().top]
            )
        )"""
    )


def _note_contrast_failure(page):
    """Return a failure when the landed note fails the body-text floor."""
    colours = page.evaluate(
        """() => {
            const note = document.querySelector('.release-check-note');
            const row = note.closest('tr');
            const surface = getComputedStyle(row.closest('.results-table-wrapper'));
            return {
                text: getComputedStyle(note).color,
                background: surface.backgroundColor,
                page: getComputedStyle(document.body).backgroundColor,
            };
        }"""
    )
    page_rgb = _parse_rgb_string(colours["page"])[:3]
    surface = _composite_over(_parse_rgb_string(colours["background"]), page_rgb)
    text = _composite_over(_parse_rgb_string(colours["text"]), surface)
    ratio = _contrast_ratio(text, surface)
    if ratio < _TEXT_CONTRAST_FLOOR:
        return [
            "corrected row's note contrasts at "
            f"{ratio:.2f}:1, below the {_TEXT_CONTRAST_FLOOR}:1 body-text floor"
        ]
    return []


def check_release_check_disclosure(page, base_url: str) -> list[str]:
    """A correction lands without moving a row, and polling stops when it ends.

    The owner's progressive-disclosure ruling is the whole point of the
    feature: results render at once, corrections land live, a corrected row
    stays exactly where it is, and the list re-sorts only on reload. The
    first three are geometry, which only a real browser can settle, so the
    replies here are scripted rather than waiting on a MusicBrainz pass that
    runs at one request per second.
    """
    job_id = create_job({"username": "gate", "year": 2025, "sort_mode": "playcount"})
    probe = page
    failures = []
    requests = []
    corrected_key = format_album_key(normalize_name("Fleetwood Mac", "Rumours"))

    def empty_spotlight(route):
        route.fulfill(json={})

    def release_checks(route):
        """Answer running first, then one terminal reply carrying the marker."""
        requests.append(route.request.url)
        if len(requests) == 1:
            route.fulfill(
                json={
                    "status": "running",
                    "checked": 1,
                    "total": 2,
                    "moved_in": 0,
                    "albums": [],
                }
            )
            return
        route.fulfill(
            json={
                "status": "done",
                "checked": 2,
                "total": 2,
                "moved_in": 1,
                "albums": [
                    {
                        "key": corrected_key,
                        "state": "moved_out",
                        "original_release_date": "1977-02-04",
                    }
                ],
            }
        )

    try:
        set_job_results(
            job_id,
            [
                _release_check_row("Fleetwood Mac", "Rumours", "2011-01-24"),
                _release_check_row("Radiohead", "OK Computer", "2025-06-16"),
            ],
        )
        set_job_release_check(
            job_id,
            {
                "status": "running",
                "checked": 0,
                "total": 2,
                "moved_out": 0,
                "moved_in": 0,
            },
        )
        probe.route("**/api/artist_spotlight?*", empty_spotlight)
        probe.route("**/api/release_checks?*", release_checks)
        probe.goto(f"{base_url}/results?job_id={job_id}", wait_until="domcontentloaded")

        probe.wait_for_function(
            """() => (document.querySelector('#release-check-status')
                 ?.textContent || '').includes('1 of 2')""",
            timeout=10_000,
        )
        before = _row_tops(probe)
        if corrected_key not in before:
            failures.append("results rows carry no data-album-key to address")

        probe.wait_for_selector(".release-check-note", timeout=15_000)
        after = _row_tops(probe)
        moved = [
            key
            for key, top in after.items()
            if key in before and abs(top - before[key]) > 0.5
        ]
        if moved:
            failures.append(f"a correction moved {len(moved)} row(s): {moved}")

        row = probe.locator(
            f'#results-table tbody tr[data-album-key="{corrected_key}"]'
        )
        if "1977" not in (row.locator(".release-date-value").text_content() or ""):
            failures.append("corrected row does not show its original release year")
        note = row.locator(".release-check-note")
        if note.count() == 0 or note.first.is_hidden():
            failures.append("corrected row carries no visible correction note")
        elif "unmatched" not in (note.first.get_attribute("href") or ""):
            failures.append("correction note does not link to the unmatched report")
        else:
            failures.extend(_note_contrast_failure(probe))
        if probe.locator("#release-check-reload").is_hidden():
            failures.append("moved-in albums were not announced with a reload action")

        settled = len(requests)
        probe.wait_for_timeout(5_000)
        if len(requests) > settled:
            failures.append(
                "polling continued after the terminal status: "
                f"{len(requests) - settled} further request(s)"
            )

        viewport = probe.viewport_size
        try:
            for width in (390, 1280):
                probe.set_viewport_size({"width": width, "height": 800})
                probe.wait_for_timeout(100)
                if probe.evaluate(
                    "() => document.documentElement.scrollWidth > innerWidth"
                ):
                    failures.append(f"the correction disclosure overflows at {width}px")
        finally:
            if viewport is not None:
                probe.set_viewport_size(viewport)
    finally:
        try:
            probe.unroute("**/api/release_checks?*", release_checks)
            probe.unroute("**/api/artist_spotlight?*", empty_spotlight)
        finally:
            delete_job(job_id)
    return failures


def _check_results_scale(page) -> list[str]:
    """Check proportional geometry on resize and recovery to narrow layout.

    Compare rendered ratios, not custom-property formulas: unsupported CSS
    arithmetic and unscaled named spacing tokens must both fail this check.
    Preserve the caller's viewport for sorting and export checks afterward.
    """
    viewport = page.viewport_size
    measurements = []
    failures = []
    try:
        for width in (1200, 1920, 390):
            page.set_viewport_size({"width": width, "height": 800})
            page.wait_for_function(
                """() => {
                    const main = document.querySelector('.results-page');
                    const style = getComputedStyle(main);
                    return parseFloat(style.getPropertyValue('--results-scale')) >= 1;
                }"""
            )
            page.evaluate(
                "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
            )
            measurements.append(
                page.evaluate(
                    """() => {
                    const size = (selector, property) => parseFloat(
                        getComputedStyle(document.querySelector(selector))[property]);
                    window.scrollTo(0, 300);
                    const headerTop = document.querySelector('.site-header').getBoundingClientRect().top;
                    const scrollOffset = window.scrollY;
                    window.scrollTo(0, 0);
                    return {
                        title: size('.results-headline', 'fontSize'),
                        padding: size('#results-table td', 'paddingTop'),
                        artwork: size('#results-table td:nth-child(2) > div > div', 'width'),
                        header: size('.site-header', 'height'),
                        headerTop,
                        scrollOffset,
                        headerPosition: getComputedStyle(document.querySelector('.site-header')).position,
                        bodyOffset: size('body', 'paddingTop'),
                        overflow: document.documentElement.scrollWidth > innerWidth,
                    };
                }"""
                )
            )
        base, wide, mobile = measurements
        ratio = wide["title"] / base["title"]
        if ratio < 1.1:
            failures.append("Results title did not grow on the wider viewport")
        for key in ("padding", "artwork"):
            if base[key] <= 0 or abs(wide[key] / base[key] - ratio) > 0.02:
                failures.append(f"Results {key} did not scale with its typography")
        if abs(wide["header"] - base["header"]) > 1:
            failures.append("Results content scale changed the shared header")
        if any(
            m["headerPosition"] not in {"relative", "static"}
            or abs(m["headerTop"] + m["scrollOffset"]) > 0.5
            or abs(m["bodyOffset"]) > 0.5
            for m in measurements
        ):
            failures.append("Results header does not scroll away in document flow")
        if mobile["title"] >= base["title"] or any(m["overflow"] for m in measurements):
            failures.append("Results did not recover a contained mobile layout")
    finally:
        if viewport is not None:
            page.set_viewport_size(viewport)
    return failures


def _check_jpeg_export(page, theme: str) -> list[str]:
    """Decode the actual download and reject blank or incorrectly sized images."""
    try:
        with page.expect_download(timeout=15_000) as downloaded:
            page.locator("#save-image").click()
        image_bytes = Path(downloaded.value.path()).read_bytes()
        if not image_bytes.startswith(b"\xff\xd8"):
            return [f"{theme} export is not JPEG"]
        dimensions = page.evaluate(
            """async data => {
                const image = new Image();
                image.src = 'data:image/jpeg;base64,' + data;
                await image.decode();
                const canvas = document.createElement('canvas');
                canvas.width = 100;
                canvas.height = 100;
                const context = canvas.getContext('2d');
                context.drawImage(image, 0, 0, 100, 100);
                const pixels = context.getImageData(0, 0, 100, 100).data;
                const tones = new Set();
                for (let i = 0; i < pixels.length; i += 4) {
                    tones.add(pixels[i] + ',' + pixels[i+1] + ',' + pixels[i+2]);
                }
                return {width: image.width, height: image.height, tones: tones.size};
            }""",
            b64encode(image_bytes).decode("ascii"),
        )
        if (
            dimensions["width"] != 3600
            or dimensions["height"] < 100
            or dimensions["tones"] < 10
        ):
            return [f"{theme} JPEG is blank or incorrectly sized: {dimensions}"]
    # Gate boundary: any failure becomes a reported FAIL line, not a crash.
    except Exception as exc:  # noqa: BLE001
        return [f"{theme} JPEG export failed: {type(exc).__name__}: {exc}"]
    return []
