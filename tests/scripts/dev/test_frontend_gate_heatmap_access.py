"""Parity and unit tests for the heatmap-access slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_heatmap_access, frontend_gate
from scripts.dev._frontend_gate_heatmap_access import _expected_cell_label
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_heatmap_cells_are_keyboard_accessible",
    "check_heatmap_document_listeners_attach_once",
    "check_heatmap_focus_survives_breakpoint",
    "check_heatmap_touch_swipe_scrolls_and_tap_shows_tooltip",
    "check_heatmap_tooltip_has_one_owner",
)
CONSTANTS = ("HEATMAP_PATH",)
HELPERS = ("_expected_cell_label",)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS, *HELPERS))
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_heatmap_access)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", CHECKS)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    # Only the check itself is re-exported by frontend_gate.py's one-line
    # registration import; HEATMAP_PATH stays private to this slice.
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_heatmap_access, name)


@pytest.mark.parametrize(
    ("iso_date", "count", "expected"),
    [
        ("2025-01-01", 5, "Wednesday 1 January 2025 -- 5 scrobbles"),
        ("2025-01-01", 1, "Wednesday 1 January 2025 -- 1 scrobble"),
        ("2025-01-01", 0, "Wednesday 1 January 2025 -- No scrobbles"),
        ("2026-03-01", 2, "Sunday 1 March 2026 -- 2 scrobbles"),
    ],
)
def test_expected_cell_label_matches_the_js_helper(
    iso_date: str, count: int, expected: str
) -> None:
    assert _expected_cell_label(iso_date, count) == expected


def _geometry(left: float = 10.0, ring_left: float = 8.0) -> dict:
    return {
        "box": {"left": left, "top": 20.0, "right": left + 5, "bottom": 25.0},
        "ring": {
            "left": ring_left,
            "top": 18.0,
            "right": ring_left + 9,
            "bottom": 27.0,
            "visibility": "visible",
        },
        "width": 390,
        "height": 844,
    }


def _ring_page(readings: list, coverage: dict | None = None) -> MagicMock:
    """A page that answers each `_CELL_GEOMETRY_JS` read in turn."""
    page = MagicMock()
    reads = iter(readings)

    def evaluate(script, *args):
        if script is _frontend_gate_heatmap_access._CELL_GEOMETRY_JS:
            return next(reads)
        if script is _frontend_gate_heatmap_access._RING_PAINT_JS:
            return coverage
        return None

    page.evaluate.side_effect = evaluate
    page.screenshot.return_value = b"png"
    return page


def _painted(page: MagicMock) -> list:
    return [
        call.args[1]
        for call in page.evaluate.call_args_list
        if call.args[0] is _frontend_gate_heatmap_access._RING_PAINT_JS
    ]


def test_a_page_that_holds_still_is_shot_once_and_read_at_the_box_it_had() -> None:
    same = _geometry()
    page = _ring_page([same, same], coverage={"top": 1.0})
    result = _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red")
    assert result == {"top": 1.0}
    assert page.screenshot.call_count == 1
    (args,) = _painted(page)
    assert args["box"] == same["box"] and args["width"] == 390


def test_a_page_that_moves_during_the_shot_is_shot_again_and_read_at_the_new_box() -> (
    None
):
    """The Adobe Fonts kit can reflow the page after `load`: the box read after
    the screenshot was then where the pixels were not, and every side read as
    bare (the 2026-09-29 flake)."""
    early, late = _geometry(left=10.0), _geometry(left=10.0 + 40)
    page = _ring_page([early, late, late, late], coverage={"top": 1.0})
    _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red")
    assert page.screenshot.call_count == 2
    (args,) = _painted(page)
    assert args["box"] == late["box"]


def test_a_ring_that_moves_during_the_shot_is_shot_again() -> None:
    page = _ring_page(
        [_geometry(ring_left=0.0), _geometry(), _geometry(), _geometry()],
        coverage={},
    )
    _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red")
    assert page.screenshot.call_count == 2


def test_a_page_that_never_holds_still_raises_instead_of_reporting_a_ring() -> None:
    attempts = _frontend_gate_heatmap_access._RING_SHOT_ATTEMPTS
    readings = [_geometry(left=float(n)) for n in range(2 * attempts + 2)]
    page = _ring_page(readings)
    with pytest.raises(RuntimeError, match="kept moving while its screenshot"):
        _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red")
    assert page.screenshot.call_count == attempts
    assert _painted(page) == []


def test_a_missing_cell_reads_no_ring_and_takes_no_screenshot() -> None:
    page = _ring_page([None])
    assert (
        _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red") is None
    )
    page.screenshot.assert_not_called()


def test_the_ring_is_read_after_fonts_and_frames_have_settled() -> None:
    script = _frontend_gate_heatmap_access._LAYOUT_SETTLED_JS
    assert "document.fonts.ready" in script
    assert script.count("requestAnimationFrame") == 2


def test_the_page_repositions_its_tooltip_before_every_screenshot() -> None:
    """A tooltip left where the cell was before a reflow can sit over the
    ring; only a scroll or a resize moves it, so the gate sends a scroll."""
    early, late = _geometry(left=10.0), _geometry(left=50.0)
    page = _ring_page([early, late, late, late], coverage={})
    _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red")
    order = [
        "screenshot" if call[0] == "screenshot" else call.args[0]
        for call in page.method_calls
        if call[0] in ("screenshot", "evaluate")
    ]
    nudge = _frontend_gate_heatmap_access._LAYOUT_MOVED_JS
    shots = [i for i, item in enumerate(order) if item == "screenshot"]
    assert len(shots) == 2
    for shot in shots:
        assert nudge in order[:shot]
    assert order[: shots[1]].count(nudge) == 2


def test_the_settle_wait_runs_before_every_screenshot() -> None:
    """Fonts and two frames must have settled before each shot, not only before
    the first: the box is read from the settled page."""
    early, late = _geometry(left=10.0), _geometry(left=50.0)
    page = _ring_page([early, late, late, late], coverage={})
    _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red")
    order = [
        "screenshot" if call[0] == "screenshot" else call.args[0]
        for call in page.method_calls
        if call[0] in ("screenshot", "evaluate")
    ]
    settled = _frontend_gate_heatmap_access._LAYOUT_SETTLED_JS
    shots = [i for i, item in enumerate(order) if item == "screenshot"]
    assert len(shots) == 2
    for number, shot in enumerate(shots, start=1):
        assert order[:shot].count(settled) == number
