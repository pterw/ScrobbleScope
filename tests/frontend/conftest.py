"""Fixture for the Chromium harness over heatmap.js's pure-function seam.

No Flask app, no Node, no build step: the page is a blank document, and
heatmap.js is loaded straight off disk with ``page.add_script_tag``. The
pure functions under test (``rocketColor``, ``countToNorm``,
``exportHeaderModel``, ``exportHeaderLayout``) need nothing else to run.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.dev._frontend_gate_runtime import _load_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
HEATMAP_JS = REPO_ROOT / "static" / "js" / "heatmap.js"


@pytest.fixture(scope="module")
def js_page() -> Iterator[object]:
    """One Chromium page with heatmap.js loaded, reused across the module.

    ``page.set_content`` leaves ``document.readyState`` at "complete" before
    ``add_script_tag`` ever runs the file, so a later DOMContentLoaded never
    fires -- the seam this harness exercises must be exposed at heatmap.js's
    module top level, not inside that listener (see Step 1).
    """
    sync_playwright = _load_playwright()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content("<!doctype html><html><body></body></html>")
        page.add_script_tag(path=str(HEATMAP_JS))
        yield page
        browser.close()
