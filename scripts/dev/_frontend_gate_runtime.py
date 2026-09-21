"""Gate runtime: Playwright loading, browser launch, the served app, routes.

A slice of the frontend gate (F-B21-51). `serve_app` binds the real Flask
app to port 0 on loopback and extends the shared page inventories with a
seeded loading page for the length of a run, restoring them in a `finally`.
The environment this relies on (a throwaway SECRET_KEY, placeholder provider
keys) is set by the facade before any sibling is imported, because
`scrobblescope.config` reads those keys once, at first import.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from werkzeug.serving import make_server

from app import create_app
from scripts.dev._frontend_gate_shared import ALL_PAGES, GATE_JOB_IDS, MIGRATED_PAGES
from scrobblescope.repositories import create_job, delete_job, set_job_progress

SETUP_COMMAND = "python -m playwright install chromium firefox"


def install_cdn_routes(page, live_fonts: bool = False) -> None:
    """Keep developer-only origins out of the gate's pages.

    Impeccable Live is a developer overlay injected into base.html while
    visual review is active; the gate must stay independent of it, so its
    origin is aborted. ``live_fonts`` skips that for a local calibration run.

    The Adobe Fonts kit always loads from its real origin: its families are
    licensed web fonts, and re-hosting or synthesizing them would misdeclare
    licensed typefaces (owner ruling 2026-09-07, no exceptions per family).
    A stall there costs the page its webfonts, never the gate its pass,
    because check_fonts reports misses as advisory WARN lines.

    The cdnjs Bootstrap fixture this used to serve was removed on 2026-09-21:
    no template requests Bootstrap, and check_stylesheet_isolation reads link
    hrefs, so it still catches a page that reintroduces it.
    """
    if live_fonts:
        return
    page.route("http://localhost:8400/**", lambda route: route.abort())


#: ``serve_app`` temporarily extends module-level page inventories for the
#: loading fixture. Serialising that context keeps two in-process gate runs
#: from clearing each other's job IDs or removing each other's route.
_SERVE_APP_LOCK = threading.Lock()


class FrontendGateError(RuntimeError):
    """A gate prerequisite is missing, so no check could run."""


def _load_playwright():
    """Return sync_playwright, or explain exactly how to install it.

    The gate never downloads tooling on its own. Implicit installs turn a
    two-second failure into a silent multi-hundred-megabyte download.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FrontendGateError(
            f"Playwright is not installed. Run: {SETUP_COMMAND}"
        ) from exc
    return sync_playwright


def _launch_browser(playwright, browser_name: str, *, headless: bool = True):
    """Launch the named engine, translating a missing build into guidance.

    Pinning the package does not fetch the browser. The two failures look
    completely different but have the same remedy.
    """
    try:
        return getattr(playwright, browser_name).launch(headless=headless)
    except Exception as exc:
        raise FrontendGateError(
            f"{browser_name} is not available to Playwright. Run: {SETUP_COMMAND}"
        ) from exc


@contextmanager
def serve_app() -> Iterator[str]:
    """Serve the real app on a loopback port for the duration of the block.

    Port 0 asks the OS for a free port, so parallel runs cannot collide. The
    shutdown sits in a finally block: a failing check must never leave a
    listening socket behind.
    """
    with _SERVE_APP_LOCK:
        loading_job_id = None
        heatmap_job_id = None
        loading_path = None
        server = None
        thread = None
        thread_started = False
        previous_job_ids = dict(GATE_JOB_IDS)
        try:
            app = create_app()
            loading_job_id = create_job(
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
            set_job_progress(
                loading_job_id,
                progress=42,
                message="Fetching scrobbles - page 21 / 50",
                error=False,
            )
            loading_path = f"/loading?job_id={loading_job_id}"
            heatmap_job_id = create_job(
                {
                    "username": "frontend-gate",
                    "mode": "heatmap",
                }
            )
            GATE_JOB_IDS.update(album=loading_job_id, heatmap=heatmap_job_id)
            MIGRATED_PAGES.append(loading_path)
            ALL_PAGES.append(loading_path)

            server = make_server("127.0.0.1", 0, app)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            thread_started = True
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            if server is not None:
                if thread_started:
                    server.shutdown()
                if thread is not None:
                    thread.join(timeout=5)
                server.server_close()
            if loading_path is not None:
                if loading_path in MIGRATED_PAGES:
                    MIGRATED_PAGES.remove(loading_path)
                if loading_path in ALL_PAGES:
                    ALL_PAGES.remove(loading_path)
            if loading_job_id is not None:
                delete_job(loading_job_id)
            if heatmap_job_id is not None:
                delete_job(heatmap_job_id)
            GATE_JOB_IDS.clear()
            GATE_JOB_IDS.update(previous_job_ids)
