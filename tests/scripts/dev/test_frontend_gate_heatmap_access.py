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


def _ring_page(
    readings: list, coverage: dict | None = None, evidence: dict | None = None
) -> MagicMock:
    """A page that answers each `_CELL_GEOMETRY_JS` read in turn.

    `evidence` is added to every read that has none of its own (the real read
    carries the evidence with the geometry)."""
    page = MagicMock()
    reads = iter(readings)

    def evaluate(script, *args):
        if script is _frontend_gate_heatmap_access._CELL_GEOMETRY_JS:
            reading = next(reads)
            if reading is not None and evidence is not None:
                return {"evidence": dict(evidence)} | reading
            return reading
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


def _order_over_a_reflow() -> tuple[list, list[int]]:
    """Run the ring read on a page that reflows once, so it is shot twice.

    Returns every `evaluate` script and `screenshot` the page saw, in order,
    and the positions of the two screenshots in that list.
    """
    early, late = _geometry(left=10.0), _geometry(left=50.0)
    page = _ring_page([early, late, late, late], coverage={})
    _frontend_gate_heatmap_access._ring_coverage(page, "2026-05-15", "red")
    order = [
        "screenshot" if call[0] == "screenshot" else call.args[0]
        for call in page.method_calls
        if call[0] in ("screenshot", "evaluate")
    ]
    shots = [i for i, item in enumerate(order) if item == "screenshot"]
    assert len(shots) == 2
    return order, shots


def test_the_page_repositions_its_tooltip_before_every_screenshot() -> None:
    """A tooltip left where the cell was before a reflow can sit over the
    ring; only a scroll or a resize moves it, so the gate sends a scroll."""
    order, shots = _order_over_a_reflow()
    nudge = _frontend_gate_heatmap_access._LAYOUT_MOVED_JS
    for shot in shots:
        assert nudge in order[:shot]
    assert order[: shots[1]].count(nudge) == 2


def test_the_settle_wait_runs_before_every_screenshot() -> None:
    """Fonts and two frames must have settled before each shot, not only before
    the first: the box is read from the settled page."""
    order, shots = _order_over_a_reflow()
    settled = _frontend_gate_heatmap_access._LAYOUT_SETTLED_JS
    for number, shot in enumerate(shots, start=1):
        assert order[:shot].count(settled) == number


def _evidence(**overrides) -> dict:
    """What `_RING_EVIDENCE_JS` reads for a ring that was shown and focused."""
    evidence = {
        "ringVisibility": "visible",
        "ringBox": {"left": 8.0, "top": 18.0, "right": 17.0, "bottom": 27.0},
        "cellBox": {"left": 10.0, "top": 20.0, "right": 15.0, "bottom": 25.0},
        "active": "2026-05-15",
        "focusVisible": True,
        "docFocus": True,
        "stroke": "rgb(106, 75, 175)",
        "theme": "light",
        "tooltipBox": {"left": 0.0, "top": 0.0, "right": 5.0, "bottom": 5.0},
        "tooltipShown": True,
        "tooltipHitsRing": False,
        "scrollX": 0,
        "scrollY": 12,
        "dpr": 1,
        "cellsAfterRing": 0,
        "containerOpacity": "1",
        "svgOpacity": "1",
        "fade": False,
        "fadingOut": False,
        "handingOff": False,
        "runningAnimations": 0,
        "reducedMotion": False,
        "settleMs": 40,
        "settleSlow": False,
    }
    evidence.update(overrides)
    return evidence


_BARE = {"top": 0.0, "right": 0.0, "bottom": 0.0, "left": 0.0}


def test_an_unpainted_ring_failure_names_a_hidden_ring_on_one_line() -> None:
    """F-B23-39: the line said only that no pixel was painted, so a ring that
    was never shown could not be told from one that was covered."""
    page = _ring_page(
        [_geometry(), _geometry()],
        coverage=_BARE,
        evidence=_evidence(ringVisibility="hidden", focusVisible=False),
    )
    (failure,) = _frontend_gate_heatmap_access._check_ring_painted(
        page, "desktop", "rgb(106, 75, 175)", "last", "2026-05-15"
    )
    assert "paints no rgb(106, 75, 175) pixel" in failure
    assert "\n" not in failure
    assert "ring.visibility=hidden" in failure
    assert "active.focus_visible=False" in failure
    assert "ring.box=8.0,18.0,17.0,27.0" in failure
    assert "cell.box=10.0,20.0,15.0,25.0" in failure
    assert "active=2026-05-15" in failure
    assert "ring.stroke=rgb(106,75,175)" in failure
    assert "theme=light" in failure
    assert "tooltip.hits_ring=False" in failure
    assert "scroll=0,12" in failure
    assert "dpr=1" in failure
    assert "cells_after_ring=0" in failure
    assert " settle_ms=" in failure and "settle_slow=False" in failure


def test_a_painted_ring_reports_nothing() -> None:
    page = _ring_page(
        [_geometry(), _geometry()],
        coverage={"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0},
        evidence=_evidence(),
    )
    assert (
        _frontend_gate_heatmap_access._check_ring_painted(
            page, "desktop", "red", "last", "2026-05-15"
        )
        == []
    )


def test_a_failure_with_no_evidence_read_keeps_the_old_line() -> None:
    page = _ring_page([_geometry(), _geometry()], coverage=_BARE)
    (failure,) = _frontend_gate_heatmap_access._check_ring_painted(
        page, "desktop", "red", "last", "2026-05-15"
    )
    assert failure.endswith("a later cell or the SVG's edge is hiding it")


def test_a_settle_wait_over_a_second_is_named_slow(monkeypatch) -> None:
    clock = iter([100.0, 101.5])
    monkeypatch.setattr(
        _frontend_gate_heatmap_access.time, "monotonic", lambda: next(clock)
    )
    page = _ring_page([_geometry(), _geometry()], coverage=_BARE, evidence=_evidence())
    _, evidence = _frontend_gate_heatmap_access._ring_shot(page, "2026-05-15", "red")
    assert evidence["settleMs"] == 1500
    assert evidence["settleSlow"] is True
    note = _frontend_gate_heatmap_access._ring_evidence_note(evidence)
    assert "settle_ms=1500 settle_slow=True" in note


def test_a_settle_wait_under_a_second_is_not_slow(monkeypatch) -> None:
    clock = iter([100.0, 100.25])
    monkeypatch.setattr(
        _frontend_gate_heatmap_access.time, "monotonic", lambda: next(clock)
    )
    page = _ring_page([_geometry(), _geometry()], coverage=_BARE, evidence=_evidence())
    _, evidence = _frontend_gate_heatmap_access._ring_shot(page, "2026-05-15", "red")
    assert evidence["settleMs"] == 250
    assert evidence["settleSlow"] is False


def test_one_evaluation_reads_the_geometry_and_the_evidence() -> None:
    script = _frontend_gate_heatmap_access._CELL_GEOMETRY_JS
    assert _frontend_gate_heatmap_access._RING_EVIDENCE_JS in script
    assert "evidence:" in script


def test_the_evidence_reported_is_the_read_after_the_shot() -> None:
    before = _geometry() | {"evidence": _evidence(stroke="rgb(1, 2, 3)")}
    after = _geometry() | {"evidence": _evidence(stroke="rgb(4, 5, 6)")}
    page = _ring_page([before, after], coverage=_BARE)
    (failure,) = _frontend_gate_heatmap_access._check_ring_painted(
        page, "desktop", "red", "last", "2026-05-15"
    )
    assert "ring.stroke=rgb(4,5,6)" in failure
    assert "rgb(1,2,3)" not in failure


def test_a_field_that_changed_during_the_shot_is_named() -> None:
    before = _geometry() | {"evidence": _evidence()}
    after = _geometry() | {
        "evidence": _evidence(focusVisible=False, tooltipShown=False, scrollY=40)
    }
    page = _ring_page([before, after], coverage=_BARE)
    (failure,) = _frontend_gate_heatmap_access._check_ring_painted(
        page, "desktop", "red", "last", "2026-05-15"
    )
    assert "changed_during_shot=active.focus_visible,tooltip.shown,scroll]" in failure
    assert "\n" not in failure


def test_a_page_that_held_still_reports_no_change_during_the_shot() -> None:
    page = _ring_page([_geometry(), _geometry()], coverage=_BARE, evidence=_evidence())
    (failure,) = _frontend_gate_heatmap_access._check_ring_painted(
        page, "desktop", "red", "last", "2026-05-15"
    )
    assert failure.endswith("changed_during_shot=none]")


def test_a_change_during_the_shot_does_not_change_the_judgement() -> None:
    """The change is reported, never judged: a fully painted ring still passes."""
    before = _geometry() | {"evidence": _evidence()}
    after = _geometry() | {"evidence": _evidence(theme="dark")}
    page = _ring_page(
        [before, after],
        coverage={"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0},
    )
    assert (
        _frontend_gate_heatmap_access._check_ring_painted(
            page, "desktop", "red", "last", "2026-05-15"
        )
        == []
    )


def test_a_missing_ring_and_tooltip_read_as_none() -> None:
    note = _frontend_gate_heatmap_access._ring_evidence_note(
        _evidence(
            ringVisibility=None, ringBox=None, tooltipBox=None, cellsAfterRing=None
        )
    )
    assert "ring.visibility=None" in note
    assert "ring.box=none" in note
    assert "tooltip.box=none" in note
    assert "cells_after_ring=None" in note


def test_the_evidence_reads_the_result_crossfade_state() -> None:
    """F-B23-39: a ring shot under an opacity below 1 is blended toward the page,
    so the line says what the result container was doing at the shot."""
    page = _ring_page(
        [_geometry(), _geometry()],
        coverage=_BARE,
        evidence=_evidence(
            containerOpacity="0.42",
            svgOpacity="1",
            fade=True,
            fadingOut=False,
            handingOff=True,
            runningAnimations=2,
            reducedMotion=False,
        ),
    )
    (failure,) = _frontend_gate_heatmap_access._check_ring_painted(
        page, "desktop", "red", "last", "2026-05-15"
    )
    assert "container.opacity=0.42" in failure
    assert "svg.opacity=1" in failure
    assert "container.heatmap_fade=True" in failure
    assert "container.fading_out=False" in failure
    assert "container.is_handing_off=True" in failure
    assert "animations.running=2" in failure
    assert "prefers_reduced_motion=False" in failure
    assert "\n" not in failure


def test_a_crossfade_that_moved_during_the_shot_is_named() -> None:
    before = _geometry() | {"evidence": _evidence(containerOpacity="0.3")}
    after = _geometry() | {
        "evidence": _evidence(containerOpacity="1", runningAnimations=0)
    }
    page = _ring_page([before, after], coverage=_BARE)
    (failure,) = _frontend_gate_heatmap_access._check_ring_painted(
        page, "desktop", "red", "last", "2026-05-15"
    )
    assert "container.opacity=1 " in failure
    assert "changed_during_shot=container.opacity]" in failure


def test_the_evidence_script_reads_opacity_flags_animations_and_motion() -> None:
    script = _frontend_gate_heatmap_access._RING_EVIDENCE_JS
    assert "getElementById('heatmap-result')" in script
    assert "heatmap-fade" in script and "fading-out" in script
    assert "is-handing-off" in script
    assert "document.getAnimations()" in script
    assert "prefers-reduced-motion: reduce" in script
