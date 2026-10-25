"""Chromium harness over heatmap.js's pure-function seam (F-B21-18).

Scope is exactly Q14 answer a
(docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md, "Owner
answers, 2026-09-23"): ``rocketColor``, ``countToNorm`` and the export header
(``exportHeaderModel`` + ``exportHeaderLayout``). The KPI blocks (streak, best
day, daily average) joined with PR #6; their cases live in
``tests/fixtures/heatmap_kpi_cases.json``, shared with the Python tests.

``arrowKeyTarget`` joined the seam with the 2026-09-28 review fix (finding 2):
the grid's arrow keys move by each layout's own steps, so the step
computation is tested here, one layout, one arrow and one edge at a time.
"""

from __future__ import annotations

import re
from datetime import date

import pytest

from scrobblescope.listening_stats import heatmap_statistics
from tests.frontend.conftest import HEATMAP_JS, REPO_ROOT
from tests.helpers import expected_kpi_blocks, kpi_payload, load_kpi_cases

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


# --- the album loading page announces a failed run once (review 4, frontend 2) ---

LOADING_PROGRESS_JS = HEATMAP_JS.parent / "loading-progress.js"
LOADING_JS = HEATMAP_JS.parent / "loading.js"

ALBUM_LOADING_MARKUP = """<!doctype html><html><body>
            <div id="progress-track"><div id="progress-bar"></div></div>
            <p id="step-text" role="status" aria-live="polite"></p>
            <p id="step-details"></p>
            <div id="error-container" role="alert" class="hidden">
              <p id="error-text"></p></div>
            <p id="error-source" class="hidden"></p>
            <button id="retry-button" class="hidden"></button>
            <div class="hidden" id="live-stats">
              <div class="loading-stat hidden"><strong id="stat-cache-hits">0</strong></div>
              <div class="loading-stat hidden"><strong id="stat-to-search">0</strong></div>
            </div>
            </body></html>"""


def test_a_failed_album_run_is_announced_once_by_the_alert(js_browser):
    """
    GIVEN the album loading page markup and a /progress answer that carries a
          failure message (a retryable one, so no redirect is scheduled)
    WHEN loading.js polls and renders it
    THEN the message sits in the role="alert" block and the polite phase line
         is empty, so a screen reader hears it once, not twice
    """
    page = js_browser.new_page()
    try:
        page.set_content(ALBUM_LOADING_MARKUP)
        page.evaluate(
            """() => {
              window.SCROBBLE = {job_id: 'abc'};
              window.fetch = () => Promise.resolve({json: () => Promise.resolve({
                error: true, retryable: true, progress: 40,
                message: 'Spotify is not answering.'})});
            }"""
        )
        page.add_script_tag(path=str(LOADING_PROGRESS_JS))
        page.add_script_tag(path=str(LOADING_JS))
        page.wait_for_function(
            "() => document.getElementById('error-text').textContent !== ''"
        )
        alert_text = page.locator("#error-text").text_content()
        phase_text = page.locator("#step-text").text_content()
    finally:
        page.close()
    assert alert_text == "Spotify is not answering."
    assert phase_text == ""


def _run_album_loading(js_browser, answer):
    """Run loading.js against one /progress answer with timers recorded, not run.

    Returns the details line, the phase line and the delays of the timers whose
    callback is the redirect to the results page. Recording setTimeout keeps
    the redirect from navigating away and shows the reading delay it scheduled.
    """
    page = js_browser.new_page()
    try:
        page.set_content(ALBUM_LOADING_MARKUP)
        page.evaluate(
            """(answer) => {
              window.SCROBBLE = {job_id: 'abc'};
              window.__scheduled = [];
              window.setTimeout = (fn, ms) => {
                window.__scheduled.push({ms, redirect: fn === window.redirectToResults});
                return 0;
              };
              window.fetch = () => Promise.resolve({json: () => Promise.resolve(answer)});
            }""",
            answer,
        )
        page.add_script_tag(path=str(LOADING_PROGRESS_JS))
        page.add_script_tag(path=str(LOADING_JS))
        page.wait_for_function(
            "() => window.__scheduled.some((t) => t.ms === 3000)", timeout=5000
        )
        return (
            page.locator("#step-details").text_content(),
            page.locator("#step-text").text_content(),
            page.evaluate(
                "() => window.__scheduled.filter((t) => t.redirect).map((t) => t.ms)"
            ),
        )
    finally:
        page.close()


def test_a_finished_album_run_opens_its_results_without_a_second_line(js_browser):
    """
    GIVEN a /progress answer for a finished run (100%, no error)
    WHEN loading.js renders it
    THEN the phase line says the run is done, the details line under it stays
         empty -- "Opening your results..." repeated what the phase line says
         (owner, 2026-10-22) -- and the results page still opens after the
         three-second reading delay.
    """
    done = "Done! Found 21 albums matching your criteria."
    details, phase, redirect_delays = _run_album_loading(
        js_browser, {"progress": 100, "message": done}
    )
    assert details == ""
    assert phase == done
    assert 3000 in redirect_delays


def test_a_failed_run_with_no_retry_still_says_the_results_page_opens(js_browser):
    """
    GIVEN a /progress answer for a failure that cannot be retried
    WHEN loading.js renders it
    THEN the details line still says the results page is opening, and the
         redirect waits the same three seconds: only the finished run's line
         was redundant.
    """
    details, _, redirect_delays = _run_album_loading(
        js_browser,
        {
            "error": True,
            "retryable": False,
            "progress": 40,
            "message": "Last.fm failed.",
        },
    )
    assert details == "Opening the results page\u2026"
    assert 3000 in redirect_delays


def _stat_tiles(js_browser, stats):
    """Render one /progress answer's stats; return (value, shown) per stat tile."""
    page = js_browser.new_page()
    try:
        page.set_content(ALBUM_LOADING_MARKUP)
        page.evaluate(
            """(stats) => {
              window.SCROBBLE = {job_id: 'abc'};
              window.setTimeout = () => 0;
              window.fetch = () => Promise.resolve({json: () => Promise.resolve(
                {progress: 50, stats})});
            }""",
            stats,
        )
        page.add_script_tag(path=str(LOADING_PROGRESS_JS))
        page.add_script_tag(path=str(LOADING_JS))
        page.wait_for_function(
            "() => !document.getElementById('live-stats').classList.contains('hidden')"
        )
        return page.evaluate(
            """() => ['stat-cache-hits', 'stat-to-search'].map((id) => {
              const el = document.getElementById(id);
              return [el.textContent,
                      !el.closest('.loading-stat').classList.contains('hidden')];
            })"""
        )
    finally:
        page.close()


def test_each_loading_stat_tile_shows_its_own_figure_and_only_when_sent(js_browser):
    """
    GIVEN /progress answers carrying cache_hits and albums_to_search, then one
          carrying cache_hits alone
    WHEN loading.js renders their stats
    THEN the cache-hits tile shows 12 and the to-search tile 30; with
         albums_to_search missing, the first tile shows and the second stays
         hidden -- so each tile reads its own key.
    """
    both = _stat_tiles(js_browser, {"cache_hits": 12, "albums_to_search": 30})
    only_hits = _stat_tiles(js_browser, {"cache_hits": 12})
    assert both == [["12", True], ["30", True]]
    assert only_hits == [["12", True], ["0", False]]


def test_the_finished_runs_redirect_replaces_the_loading_entry_in_history(js_browser):
    """
    GIVEN a loading page reached through a real navigation, with a finished run
    WHEN the scheduled redirect to the results page runs
    THEN the page is at /results and history holds no extra entry, so Back
         from the results reaches the form instead of the done job (owner,
         2026-10-25).
    """
    page = js_browser.new_page()
    try:
        page.route(
            "http://loading.test/**",
            lambda route: route.fulfill(
                content_type="text/html",
                body=(
                    ALBUM_LOADING_MARKUP
                    if route.request.url.endswith("/loading")
                    else "<!doctype html><title>x</title>"
                ),
            ),
        )
        page.goto("http://loading.test/form")
        page.goto("http://loading.test/loading")
        before = page.evaluate("() => history.length")
        page.evaluate(
            """() => {
              window.SCROBBLE = {job_id: 'abc'};
              window.setTimeout = (fn) => { window.__redirect = fn; return 0; };
              window.fetch = () => Promise.resolve({json: () => Promise.resolve(
                {progress: 100, message: 'Done'})});
            }"""
        )
        page.add_script_tag(path=str(LOADING_PROGRESS_JS))
        page.add_script_tag(path=str(LOADING_JS))
        page.wait_for_function("() => typeof window.__redirect === 'function'")
        with page.expect_navigation(url="http://loading.test/results"):
            page.evaluate("() => window.__redirect()")
        after = page.evaluate("() => history.length")
        path = page.evaluate("() => location.pathname")
    finally:
        page.close()
    assert path == "/results"
    assert after == before


KPI_CASES = load_kpi_cases()

RENDER_KPIS_JS = """(data) => {
    const row = document.createElement('div');
    window.__scrobbleHeatmapTestHooks.renderKpisInto(row, data);
    return Array.from(row.querySelectorAll('.heatmap-kpi')).map((item) => ({
        label: item.querySelector('.heatmap-kpi-label').textContent,
        value: item.querySelector('.heatmap-kpi-value').textContent,
        sub: (item.querySelector('.heatmap-kpi-sub') || { textContent: '' }).textContent,
    }));
}"""


def _published(case):
    """Return *case*'s stored result with the statistics the job publishes."""
    payload = kpi_payload(case)
    payload["statistics"] = heatmap_statistics(
        payload["daily_counts"], date.fromisoformat(payload["to_date"])
    )
    return payload


@pytest.mark.parametrize("case", KPI_CASES, ids=lambda c: c["name"])
def test_kpi_blocks_show_what_the_window_holds(js_page, case):
    """The four KPI blocks state the window's total, daily average, best day
    and current streak, as the case name says they must. The rules now live
    in ``listening_stats``; the blocks read the same as when the browser
    computed them.

    Mutation: format the published streak or total wrongly in ``kpiModel``
    (for instance drop ``toLocaleString`` from the total) and the matching
    cases fail.
    """
    assert js_page.evaluate(RENDER_KPIS_JS, _published(case)) == expected_kpi_blocks(
        case
    )


def test_kpi_blocks_render_the_published_figures_and_compute_nothing(js_page):
    """
    GIVEN a payload whose statistics disagree with its own daily counts
    WHEN the KPI row renders
    THEN it shows the published figures, not figures worked out from the
    counts: the page states what the server decided. Every published figure
    differs from what its counts give (total 3, average 0.3, best day 2 on
    Mar 9, streak 2), so a recompute of any one of them fails.

    Mutation: bring back a browser-side total, average, streak or best-day
    computation and that block shows the counts' figure instead of 14,
    12.3, 9 / MAR 5 or 7.
    """
    published = {
        "total_plays": {"value": 14, "population": "p"},
        "daily_average": {"value": 12.3, "population": "p"},
        "best_day": {"value": {"date": "2026-03-05", "count": 9}, "population": "p"},
        "current_streak": {"value": 7, "population": "p"},
    }
    data = {
        "from_date": "2026-03-01",
        "to_date": "2026-03-10",
        "daily_counts": {"2026-03-09": 2, "2026-03-10": 1},
        "statistics": published,
    }
    assert js_page.evaluate(RENDER_KPIS_JS, data) == [
        {"label": "SCROBBLES", "value": "14", "sub": ""},
        {"label": "DAILY AVERAGE", "value": "12.3", "sub": ""},
        {"label": "BEST DAY", "value": "9", "sub": "MAR 5"},
        {"label": "CURRENT STREAK", "value": "7", "sub": "DAYS"},
    ]


INDEX_HTML = REPO_ROOT / "templates" / "index.html"
HEATMAP_FORM_HTML = REPO_ROOT / "templates" / "partials" / "_heatmap_form.html"


def _text(fragment: str) -> str:
    """The words of an HTML fragment: tags dropped, whitespace collapsed."""
    return " ".join(re.sub(r"<[^>]+>", " ", fragment).split())


def _heatmap_lede() -> str:
    """The heatmap-mode lede on the index page (the paragraph under its eyebrow)."""
    source = INDEX_HTML.read_text(encoding="utf-8")
    match = re.search(
        r'Listening heatmap</p>\s*<p class="index-hero__lede">(.*?)</p>', source, re.S
    )
    assert match, "index.html has no heatmap-mode lede under its eyebrow"
    return _text(match.group(1))


def _preview_text() -> str:
    """The words of the heatmap mode's preview card, up to its ramp."""
    source = HEATMAP_FORM_HTML.read_text(encoding="utf-8")
    match = re.search(
        r'<div class="hm-preview">(.*?)<span class="hm-preview__ramp"', source, re.S
    )
    assert match, "_heatmap_form.html has no preview card"
    return _text(match.group(1))


#: Relative luminance (WCAG) of the colour the grid gives a quiet day and of
#: the window's busiest day.
SHADE_LUMINANCE_JS = """([quiet, busiest]) => {
    const hooks = window.__scrobbleHeatmapTestHooks;
    const luminance = (css) => {
        const [r, g, b] = css.match(/\\d+/g).map(Number).map((v) => v / 255)
            .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    return [quiet, busiest].map((n) => luminance(hooks.rocketColor(hooks.countToNorm(n, busiest))));
}"""


def test_the_heatmap_copy_names_the_shade_the_grid_draws(js_page):
    """
    GIVEN the colours the grid gives a quiet day and the window's busiest day
    WHEN the index lede and the preview card describe the shading
    THEN both name the direction the grid really draws -- "brighter" when the
         busiest day is the lighter colour, "darker" when it is the darker one
         -- and never the opposite word. The clause that names the shade also
         says the busier days get it ("more"), never "fewer" or "less". The old
         copy said darker meant more while rocketColor drew more plays
         brighter, and nothing caught it.

    Mutation: swap the word in either copy, or reverse ROCKET_STOPS, and this
    fails.
    """
    quiet, busiest = js_page.evaluate(SHADE_LUMINANCE_JS, [1, 100])
    assert quiet != busiest
    true_word, false_word = (
        ("brighter", "darker") if busiest > quiet else ("darker", "brighter")
    )
    for name, copy in (
        ("heatmap lede", _heatmap_lede()),
        ("preview card", _preview_text()),
    ):
        words = copy.lower()
        assert false_word not in words, f"{name} says {false_word}: {copy!r}"
        # The clause naming the shade must tie it to MORE plays: "brighter
        # squares mean fewer plays" names the right word and the wrong
        # direction.
        clauses = [c for c in re.split(r"[.;:]", words) if true_word in c]
        assert clauses, f"{name} does not say {true_word}: {copy!r}"
        assert all(
            re.search(r"\bmore\b", c) and not re.search(r"\b(fewer|less)\b", c)
            for c in clauses
        ), f"{name} does not tie {true_word} to more plays: {copy!r}"


def test_the_preview_card_promises_only_figures_the_result_shows(js_page):
    """
    GIVEN the KPI labels a heatmap result renders
    WHEN the mode's preview card says what a run produces
    THEN it names each of them, and no streak the result does not show (the
         old card promised a longest streak; the result shows the current one).
    """
    labels = [
        block["label"].lower()
        for block in js_page.evaluate(RENDER_KPIS_JS, _published(KPI_CASES[0]))
    ]
    preview = _preview_text().lower()
    assert labels, "the KPI row rendered no blocks"
    assert [label for label in labels if label not in preview] == []
    assert "longest" not in preview


def test_a_window_with_no_best_day_shows_no_date(js_page):
    """A window with no plays has no best day: the block shows 0 and no date.

    Mutation: format ``best.date`` without the null guard and the block shows
    'NaN' or the render throws instead of an empty label.
    """
    published = {
        "total_plays": {"value": 0, "population": "p"},
        "daily_average": {"value": 0, "population": "p"},
        "best_day": {"value": {"date": None, "count": 0}, "population": "p"},
        "current_streak": {"value": 0, "population": "p"},
    }
    data = {"from_date": "2026-03-01", "to_date": "2026-03-10", "statistics": published}
    blocks = js_page.evaluate(RENDER_KPIS_JS, data)
    assert blocks[2] == {"label": "BEST DAY", "value": "0", "sub": ""}
