"""Parity and behaviour tests for the assets slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_assets, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

MOVED = (
    "BOOTSTRAP_MARKER",
    "TAILWIND_MARKER",
    "_stylesheet_hrefs",
    "check_stylesheet_isolation",
)
REEXPORTED = (
    "BOOTSTRAP_MARKER",
    "TAILWIND_MARKER",
    "check_stylesheet_isolation",
    "check_inline_marks_need_no_wrapper_list",
)


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_assets)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_assets, name)


def _page_with(hrefs: list[str]) -> MagicMock:
    page = MagicMock()
    page.eval_on_selector_all.return_value = hrefs
    return page


@pytest.mark.parametrize(
    ("hrefs", "count"),
    [
        ([], 0),
        (
            [
                "/static/css/tailwind.css",
                "https://cdnjs.cloudflare.com/x/bootstrap.min.css",
            ],
            2,
        ),
    ],
)
def test_isolation_fails_unless_exactly_one_framework_sheet(hrefs, count) -> None:
    with patch("scripts.dev._frontend_gate_assets.ALL_PAGES", ["/"]):
        failures = _frontend_gate_assets.check_stylesheet_isolation(
            _page_with(hrefs), "http://127.0.0.1:0"
        )
    assert failures == [
        f"/ loads {count} framework stylesheets, expected exactly 1: {hrefs}"
    ]


def test_isolation_passes_one_tailwind_sheet_beside_other_css() -> None:
    hrefs = ["/static/css/tailwind.css", "https://use.typekit.net/rwy8ghw.css"]
    with patch("scripts.dev._frontend_gate_assets.ALL_PAGES", ["/"]):
        assert (
            _frontend_gate_assets.check_stylesheet_isolation(
                _page_with(hrefs), "http://127.0.0.1:0"
            )
            == []
        )


def _paint(host="rgb(10, 120, 30)", bars="rgb(200, 30, 90)", **overrides) -> dict:
    """What the browser reports for a mark that colours itself correctly."""
    report = {
        "expected": {"color": host, "bars": bars},
        "hostColor": host,
        "rootFill": host,
        "letterFills": [host],
        "barStrokes": [bars],
        "letterCount": 40,
        "barCount": 5,
    }
    report.update(overrides)
    return report


def _fake_page(*reports: dict) -> MagicMock:
    page = MagicMock()
    page.evaluate.return_value = list(reports)
    return page


def test_inline_marks_render_each_template_inside_two_different_wrappers() -> None:
    page = _fake_page(_paint(), _paint("rgb(240, 200, 20)", "rgb(20, 60, 220)"))
    failures = _frontend_gate_assets.check_inline_marks_need_no_wrapper_list(
        page, "http://127.0.0.1:0"
    )
    assert failures == []
    calls = page.evaluate.call_args_list
    assert len(calls) == len(_frontend_gate_assets.INLINE_MARK_TEMPLATES)
    for call, template in zip(
        calls, _frontend_gate_assets.INLINE_MARK_TEMPLATES, strict=True
    ):
        markup, wrappers = call.args[1]
        assert markup == template.read_text(encoding="utf-8")
        assert len({w["color"] for w in wrappers}) == len(wrappers) >= 2
        assert len({w["bars"] for w in wrappers}) == len(wrappers)


def test_a_mark_that_follows_its_wrapper_passes() -> None:
    reports = [_paint(), _paint("rgb(240, 200, 20)", "rgb(20, 60, 220)")]
    assert _frontend_gate_assets.mark_paint_failures("mark.svg", reports) == []


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        # currentColor only in a comment, with a literal root fill.
        ({"rootFill": "rgb(0, 0, 0)"}, "root fill paints rgb(0, 0, 0)"),
        # A child path that sets its own fill.
        ({"letterFills": ["rgb(10, 120, 30)", "rgb(0, 0, 0)"]}, "letterforms paint"),
        # An rgb() stroke later in the style rule beats var(--bars-color).
        ({"barStrokes": ["rgb(1, 2, 3)"]}, "bars stroke ['rgb(1, 2, 3)']"),
    ],
)
def test_a_mark_that_ignores_its_wrapper_fails(override, fragment) -> None:
    failures = _frontend_gate_assets.mark_paint_failures(
        "mark.svg", [_paint(**override)]
    )
    assert len(failures) == 1
    assert failures[0].startswith("mark.svg ")
    assert fragment in failures[0]


def test_a_mark_with_no_letterforms_or_no_bars_fails_instead_of_passing() -> None:
    failures = _frontend_gate_assets.mark_paint_failures(
        "mark.svg", [_paint(letterCount=0), _paint(barCount=0)]
    )
    assert len(failures) == 2
    assert all("expected both" in failure for failure in failures)


def test_a_failing_wrapper_is_named_by_its_own_colours() -> None:
    good = _paint()
    bad = _paint("rgb(240, 200, 20)", "rgb(20, 60, 220)", rootFill="rgb(0, 0, 0)")
    failures = _frontend_gate_assets.mark_paint_failures("mark.svg", [good, bad])
    assert failures == [
        "mark.svg root fill paints rgb(0, 0, 0) inside a wrapper whose color "
        "is rgb(240, 200, 20)"
    ]
