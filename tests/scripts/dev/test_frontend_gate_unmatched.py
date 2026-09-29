"""Parity and behaviour tests for the unmatched slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.dev import (
    _frontend_gate_results,
    _frontend_gate_unmatched,
    frontend_gate,
)
from tests.scripts.dev.gate_parity import defined_names

MOVED = (
    "UNMATCHED_TWO_PANEL_MIN",
    "UNMATCHED_SWEEP_WIDTHS",
    "UNMATCHED_MIN_TITLE_WIDTH",
    "_unmatched_panel_width_sweep",
    "check_unmatched_report",
)
REEXPORTED = (
    "UNMATCHED_TWO_PANEL_MIN",
    "UNMATCHED_SWEEP_WIDTHS",
    "UNMATCHED_MIN_TITLE_WIDTH",
    "check_unmatched_report",
)


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_unmatched)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_unmatched, name)


def _sweeping_page(
    columns: int, title_width: float, radius: float | None = None
) -> MagicMock:
    """A page whose layout never changes, whatever width it is given.

    With no `radius`, every artwork kind reports the radius its current width
    asks for, so only the column and title checks can fail.
    """
    page = MagicMock()
    page.viewport_size = {"width": 1280, "height": 800}

    def evaluate(script, *args):
        if "gridTemplateColumns" in script:
            return {"columns": columns, "titles": [title_width, 200.0]}
        if "borderTopLeftRadius" in script:
            width = page.set_viewport_size.call_args.args[0]["width"]
            value = (
                radius
                if radius is not None
                else _frontend_gate_results.expected_artwork_radius(width)
            )
            return {kind: [value] for kind in args[0]}
        return None

    page.evaluate.side_effect = evaluate
    return page


def test_sweep_reports_wrong_columns_and_a_starved_title_then_restores() -> None:
    page = _sweeping_page(columns=2, title_width=20.0)
    failures = _frontend_gate_unmatched._unmatched_panel_width_sweep(page)
    widths = _frontend_gate_unmatched.UNMATCHED_SWEEP_WIDTHS
    below = [w for w in widths if w < _frontend_gate_unmatched.UNMATCHED_TWO_PANEL_MIN]
    assert sum("panel columns, expected 1" in f for f in failures) == len(below)
    assert sum("album title" in f and "20px wide" in f for f in failures) == len(widths)
    assert page.set_viewport_size.call_args.args[0] == {"width": 1280, "height": 800}


def test_sweep_covers_two_phone_widths_with_their_own_title_floors() -> None:
    """A 100px title clears 320px's 70px floor and the 96px desktop floor,
    and fails only 390px's 140px floor: the room a fourth column took away.
    """
    page = _sweeping_page(columns=1, title_width=100.0)
    failures = _frontend_gate_unmatched._unmatched_panel_width_sweep(page)
    titles = [f for f in failures if "album title" in f]
    assert titles == [
        "unmatched album title at 390px is 100px wide, expected at least 140px"
    ]
    assert {320, 390} <= set(_frontend_gate_unmatched.UNMATCHED_SWEEP_WIDTHS)


def test_sweep_reports_a_desktop_corner_radius_on_a_phone() -> None:
    """8px everywhere is wrong only below 768px, and each artwork kind is named."""
    page = _sweeping_page(columns=1, title_width=300.0, radius=8.0)
    failures = _frontend_gate_unmatched._unmatched_panel_width_sweep(page)
    radius = [f for f in failures if "corner radius" in f]
    kinds = _frontend_gate_unmatched._UNMATCHED_ARTWORK_SELECTORS
    assert len(radius) == 2 * len(kinds)
    assert all("[8.0]px, expected 4px" in f for f in radius)
    assert {f.split(" at ")[1].split("px")[0] for f in radius} == {"320", "390"}


def test_artwork_radius_reports_an_absent_kind_instead_of_passing() -> None:
    """A selector that matches nothing must not pass vacuously."""
    failures = _frontend_gate_results.artwork_radius_failures(
        {"portrait": [], "cover": [4.0]}, 390, "unmatched"
    )
    assert failures == ["unmatched page at 390px renders no portrait artwork"]


def test_sweep_restores_the_viewport_when_measurement_raises() -> None:
    page = _sweeping_page(columns=2, title_width=200.0)
    page.evaluate.side_effect = RuntimeError("page crashed")
    with pytest.raises(RuntimeError):
        _frontend_gate_unmatched._unmatched_panel_width_sweep(page)
    assert page.set_viewport_size.call_args.args[0] == {"width": 1280, "height": 800}
