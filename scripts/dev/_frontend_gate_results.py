"""Browser checks for results sorting, export data, and safe text rendering."""

from base64 import b64encode
from pathlib import Path

from scrobblescope.repositories import create_job, delete_job, set_job_results


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
        probe.locator("#toggle-sort-playtime").click()
        rows = probe.locator("#results-table tbody tr")
        if rows.first.get_attribute("data-album") != "Time winner":
            failures.append("listening-time toggle did not reorder albums")
        with probe.expect_download() as downloaded:
            probe.locator("#export-csv").click()
        csv_text = Path(downloaded.value.path()).read_text(encoding="utf-8")
        if '"1","Time winner","Second","2m","2025-02-03"' not in csv_text:
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
    except Exception as exc:
        return [f"{theme} JPEG export failed: {type(exc).__name__}: {exc}"]
    return []
