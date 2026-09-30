"""Chromium harness over heatmap.js's pure-function seam (F-B21-18).

Scope is exactly Q14 answer a
(docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md, "Owner
answers, 2026-09-23"): ``rocketColor``, ``countToNorm`` and the export header
(``exportHeaderModel`` + ``exportHeaderLayout``). ``computeStreak`` is out of
scope here; Q14 defers it to WP-6.

``arrowKeyTarget`` joined the seam with the 2026-09-28 review fix (finding 2):
the grid's arrow keys move by each layout's own steps, so the step
computation is tested here, one layout, one arrow and one edge at a time.
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
        # Between two stops, where the interpolation and its rounding show:
        # 0.25 is the midpoint of stops 1 and 2; 0.4 and 0.9 land on x.7
        # channels that Math.round lifts and Math.floor would not (F-B23-31).
        (0.25, "rgb(74,19,94)"),
        (0.4, "rgb(131,32,103)"),
        (0.9, "rgb(244,172,83)"),
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


@pytest.fixture
def header_page(js_browser):
    """A page whose header, eyebrow and legend captions exist before
    heatmap.js loads, with DOMContentLoaded fired by hand (a page set up by
    ``set_content`` never fires it), so ``initForm`` binds the headline node.
    """
    page = js_browser.new_page()
    page.set_content(
        "<!doctype html><html><body>"
        '<h1 id="heatmap-result-headline"> Ann&#39;s last 365 days </h1>'
        '<div class="heatmap-head__titles">'
        '<span class="eyebrow">Eye brow</span></div>'
        '<span class="heatmap-legend__cap" style="text-transform:uppercase">'
        "Less</span>"
        '<span class="heatmap-legend__cap">More</span>'
        "</body></html>"
    )
    page.evaluate("() => { window.__scrobbleHeatmapTestMode = true; }")
    page.add_script_tag(path=str(HEATMAP_JS))
    page.evaluate("() => document.dispatchEvent(new Event('DOMContentLoaded'))")
    yield page
    page.close()


def _layout(page, grid_width):
    return page.evaluate(
        f"(w) => window.__scrobbleHeatmapTestHooks.exportHeaderLayout({STUB_CTX_JS}, w, {ITEMS_JS})",
        grid_width,
    )


def test_export_header_layout_beside_puts_the_legend_next_to_the_kpis(header_page):
    """Worked by hand from heatmap.js's constants, with 7px per character.

    The widest label is "DAILY AVERAGE" (13 x 7 = 91), so a column needs 105
    and four columns fit in 1280. Top is EXPORT_PAD 28 + 76 = 104; one row of
    62 ends at 166. The legend (28 + 28 + 2 x 8 + 90 = 162) sits at
    1336 - 28 - 162 = 1146, level with the KPIs at 104 + 42 = 146, and the
    header ends at max(166, 146 + 8) + 16 = 182.
    """
    assert _layout(header_page, 1280) == {
        "columns": 4,
        "step": 190,
        "kpiTop": 104,
        "kpiBottom": 166,
        "legendX": 1146,
        "legendY": 146,
        "legendMeasured": {"total": 162, "less": 28},
        "headHeight": 182,
    }


def test_export_header_layout_stacked_puts_the_legend_below_the_kpis(header_page):
    """At 340 the four columns need 105 each, so two columns of 170 wrap the
    KPIs onto two rows (104 + 2 x 62 = 228). The legend would sit at
    396 - 28 - 162 = 206, inside the KPIs' 28 + 340 = 368, so it takes its
    own row at 228 + 4 = 232 from the left pad, and the header ends at
    max(228, 232 + 8) + 16 = 256."""
    assert _layout(header_page, 340) == {
        "columns": 2,
        "step": 170,
        "kpiTop": 104,
        "kpiBottom": 228,
        "legendX": 28,
        "legendY": 232,
        "legendMeasured": {"total": 162, "less": 28},
        "headHeight": 256,
    }


def test_export_header_model_carries_the_headline_and_both_legend_captions(
    header_page,
):
    """The export states what the page renders: the trimmed headline, and the
    legend captions each cased by its own CSS (Less uppercased, More not)."""
    model = header_page.evaluate(
        "() => window.__scrobbleHeatmapTestHooks.exportHeaderModel()"
    )
    assert model == {
        "eyebrow": "Eye brow",
        "headline": "Ann's last 365 days",
        "legend": {"less": "LESS", "more": "More"},
    }


#: The desktop grid: one column per week, so one cell right is 7 days on and
#: one cell down is the next day. 20 cells whose first day sits on row 2
#: (a Wednesday): column 0 holds indexes 0-4, column 1 holds 5-11, column 2
#: holds 12-18 and column 3 holds 19 alone.
DESKTOP_GRID = {"across": 7, "down": 1, "lead": 2}
DESKTOP_COUNT = 20

#: The mobile strip: row-major, 10 columns, so one cell right is the next day
#: and one cell down is 10 days on. 25 cells: rows of 0-9, 10-19 and 20-24.
MOBILE_GRID = {"across": 1, "down": 10, "lead": 0}
MOBILE_COUNT = 25


def _arrow_target(js_page, key, index, count, grid):
    return js_page.evaluate(
        "(a) => window.__scrobbleHeatmapTestHooks.arrowKeyTarget("
        "a.key, a.index, a.count, a.grid)",
        {"key": key, "index": index, "count": count, "grid": grid},
    )


@pytest.mark.parametrize(
    ("key", "index", "expected"),
    [
        # An interior cell (column 1, row 3) moves one week or one day.
        ("ArrowRight", 8, 15),
        ("ArrowLeft", 8, 1),
        ("ArrowDown", 8, 9),
        ("ArrowUp", 8, 7),
        # Edges stay put rather than wrap or leave the range.
        ("ArrowLeft", 3, 3),  # first column
        ("ArrowRight", 19, 19),  # last column
        ("ArrowRight", 15, 15),  # 22 is past the last cell
        ("ArrowUp", 5, 5),  # top row (Monday), not column 0's Sunday
        ("ArrowDown", 11, 11),  # bottom row (Sunday), not column 2's Monday
        ("ArrowUp", 0, 0),  # the first cell, below the lead slots
        ("ArrowDown", 19, 19),  # the last cell
    ],
)
def test_arrow_key_target_desktop(js_page, key, index, expected):
    assert _arrow_target(js_page, key, index, DESKTOP_COUNT, DESKTOP_GRID) == expected


@pytest.mark.parametrize(
    ("key", "index", "expected"),
    [
        # An interior cell (row 1, column 3) moves one day or one row.
        ("ArrowRight", 13, 14),
        ("ArrowLeft", 13, 12),
        ("ArrowDown", 13, 23),
        ("ArrowUp", 13, 3),
        # Edges stay put rather than wrap or leave the range.
        ("ArrowLeft", 10, 10),  # first column, not row 0's last cell
        ("ArrowRight", 9, 9),  # last column, not row 1's first cell
        ("ArrowUp", 4, 4),  # top row
        ("ArrowDown", 15, 15),  # 25 is past the last cell
        ("ArrowRight", 24, 24),  # the last cell
        ("ArrowLeft", 0, 0),  # the first cell
    ],
)
def test_arrow_key_target_mobile(js_page, key, index, expected):
    assert _arrow_target(js_page, key, index, MOBILE_COUNT, MOBILE_GRID) == expected


@pytest.mark.parametrize("key", ["Home", "End", "Enter", "a", "toString"])
def test_arrow_key_target_ignores_other_keys(js_page, key):
    assert _arrow_target(js_page, key, 8, DESKTOP_COUNT, DESKTOP_GRID) is None
