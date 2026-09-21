"""Parity and behaviour tests for the unmatched slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_unmatched, frontend_gate
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


def _sweeping_page(columns: int, title_width: float) -> MagicMock:
    """A page whose layout never changes, whatever width it is given."""
    page = MagicMock()
    page.viewport_size = {"width": 1280, "height": 800}

    def evaluate(script, *_args):
        if "gridTemplateColumns" in script:
            return {"columns": columns, "titles": [title_width, 200.0]}
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


def test_sweep_restores_the_viewport_when_measurement_raises() -> None:
    page = _sweeping_page(columns=2, title_width=200.0)
    page.evaluate.side_effect = RuntimeError("page crashed")
    with pytest.raises(RuntimeError):
        _frontend_gate_unmatched._unmatched_panel_width_sweep(page)
    assert page.set_viewport_size.call_args.args[0] == {"width": 1280, "height": 800}
