"""Chromium harness over heatmap.js's pure-function seam (F-B21-18).

Scope is exactly Q14 answer a
(docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md, "Owner
answers, 2026-09-23"): ``rocketColor``, ``countToNorm`` and the export header
(``exportHeaderModel`` + ``exportHeaderLayout``). ``computeStreak`` is out of
scope here; Q14 defers it to WP-6.
"""

from __future__ import annotations

import pytest

from tests.frontend.conftest import HEATMAP_JS

pytestmark = pytest.mark.browser

STUB_CTX_JS = "({ font: '', measureText(text) { return { width: text.length * 7 }; } })"
ITEMS_JS = """[
    {label: 'DAILY AVERAGE', sub: 'PER DAY', value: '12.3'},
    {label: 'BEST DAY', sub: 'PEAK', value: '88'},
    {label: 'STREAK', sub: 'DAYS', value: '14'},
    {label: 'TOTAL', sub: 'SCROBBLES', value: '4,491'},
]"""


@pytest.mark.parametrize(
    ("t", "expected"),
    [
        (0, "rgb(3,5,26)"),  # ROCKET_STOPS[0], t clamped to 0
        (1, "rgb(249,213,118)"),  # ROCKET_STOPS[-1], t clamped to 1
        (0.5, "rgb(166,44,92)"),  # ROCKET_STOPS[3], an exact stop
        (-1, "rgb(3,5,26)"),  # clamps low
        (2, "rgb(249,213,118)"),  # clamps high
    ],
)
def test_rocket_color(js_page, t, expected):
    assert (
        js_page.evaluate("(t) => window.__scrobbleHeatmapTestHooks.rocketColor(t)", t)
        == expected
    )


@pytest.mark.parametrize(
    ("count", "max_count", "expected"),
    [
        (0, 100, 0),
        (100, 100, 1),
        (-5, 100, 0),
        (5, 0, 0),  # the two guard clauses, then the ends
        (9, 99, pytest.approx(0.5)),  # log10(10)/log10(100) == 1/2 exactly
        (99, 999, pytest.approx(2 / 3)),  # log10(100)/log10(1000) == 2/3 exactly
    ],
)
def test_count_to_norm(js_page, count, max_count, expected):
    assert (
        js_page.evaluate(
            "(a) => window.__scrobbleHeatmapTestHooks.countToNorm(a[0], a[1])",
            [count, max_count],
        )
        == expected
    )


def _insert_eyebrow(js_page, style: str) -> None:
    js_page.evaluate(
        """(style) => document.body.insertAdjacentHTML('beforeend',
            '<div class="heatmap-head__titles">' +
            '<span class="eyebrow" style="' + style + '">test eyebrow</span>' +
            '</div>')""",
        style,
    )


def _remove_eyebrows(js_page) -> None:
    js_page.evaluate(
        """() => {
            document.querySelectorAll('.heatmap-head__titles').forEach(
                (el) => el.remove()
            );
        }"""
    )


def test_export_header_model_uppercases_only_when_the_css_says_to(js_page):
    _insert_eyebrow(js_page, "text-transform:uppercase")
    try:
        model = js_page.evaluate(
            "() => window.__scrobbleHeatmapTestHooks.exportHeaderModel()"
        )
        assert model["eyebrow"] == "TEST EYEBROW"
    finally:
        _remove_eyebrows(js_page)


def test_export_header_model_leaves_text_as_written_without_text_transform(js_page):
    _insert_eyebrow(js_page, "")
    try:
        model = js_page.evaluate(
            "() => window.__scrobbleHeatmapTestHooks.exportHeaderModel()"
        )
        assert model["eyebrow"] == "test eyebrow"
    finally:
        _remove_eyebrows(js_page)


def test_hooks_absent_without_test_mode_flag(js_browser):
    """A page that never sets ``window.__scrobbleHeatmapTestMode`` before the
    script tag loads never sees the guarded seam (F-B21-18). A second page
    on the shared ``js_browser`` starts with a clean global scope, so this
    does not depend on ``js_page`` never having set the flag."""
    page = js_browser.new_page()
    try:
        page.set_content("<!doctype html><html><body></body></html>")
        page.add_script_tag(path=str(HEATMAP_JS))
        hooks = page.evaluate("() => window.__scrobbleHeatmapTestHooks")
    finally:
        page.close()
    assert hooks is None


@pytest.mark.parametrize(
    ("grid_width", "expected_columns"), [(1280, 4), (340, 2), (150, 1)]
)
def test_export_header_layout_columns(js_page, grid_width, expected_columns):
    columns = js_page.evaluate(
        f"(w) => window.__scrobbleHeatmapTestHooks.exportHeaderLayout({STUB_CTX_JS}, w, {ITEMS_JS}).columns",
        grid_width,
    )
    assert columns == expected_columns
