"""Fixture for the Chromium harness over heatmap.js's pure-function seam.

No Flask app, no Node, no build step: the page is a blank document, and
heatmap.js is loaded straight off disk with ``page.add_script_tag``. The
pure functions under test (``rocketColor``, ``countToNorm``,
``exportHeaderModel``, ``exportHeaderLayout``, ``arrowKeyTarget``) need
nothing else to run.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.dev._frontend_gate_runtime import _launch_browser, _load_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
HEATMAP_JS = REPO_ROOT / "static" / "js" / "heatmap.js"


@pytest.fixture(scope="module")
def js_browser() -> Iterator[object]:
    """One Chromium browser, reused across the module.

    Shared so ``test_hooks_absent_without_test_mode_flag`` can open a second,
    independent page on the same browser instead of a second
    ``sync_playwright()`` context -- nesting two of those in one thread
    raises "Playwright Sync API inside the asyncio loop".
    """
    sync_playwright = _load_playwright()
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright, "chromium")
        yield browser
        browser.close()


@pytest.fixture(scope="module")
def js_page(js_browser: object) -> Iterator[object]:
    """One Chromium page with heatmap.js loaded, reused across the module.

    ``page.set_content`` leaves ``document.readyState`` at "complete" before
    ``add_script_tag`` ever runs the file, so a later DOMContentLoaded never
    fires -- the seam this harness exercises must be exposed at heatmap.js's
    module top level, not inside that listener (see Step 1).

    ``window.__scrobbleHeatmapTestMode`` is set before the script tag loads
    heatmap.js, so the guarded seam (F-B21-18) exposes
    ``window.__scrobbleHeatmapTestHooks`` for this page only -- a page that
    never sets the flag never sees it (see
    ``test_hooks_absent_without_test_mode_flag``).
    """
    page = js_browser.new_page()
    page.set_content("<!doctype html><html><body></body></html>")
    page.evaluate("() => { window.__scrobbleHeatmapTestMode = true; }")
    page.add_script_tag(path=str(HEATMAP_JS))
    yield page
    page.close()
