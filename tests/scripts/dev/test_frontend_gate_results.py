"""Behaviour tests for the results slice of the frontend gate: artwork corners."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_results


@pytest.mark.parametrize(
    ("width", "radius"),
    [(320, 4.0), (390, 4.0), (768, 4.0), (1023, 4.0), (1024, 8.0), (1280, 8.0)],
)
def test_expected_radius_steps_up_at_the_large_breakpoint_not_the_tablet(
    width: int, radius: float
) -> None:
    """Spotify: 4px on small and medium devices, 8px on large ones. A tablet
    (768px) is medium, so it keeps 4px."""
    assert _frontend_gate_results.expected_artwork_radius(width) == radius


def _results_page(radius_at):
    """A page whose row covers have `radius_at(width)` corners at each width."""
    page = MagicMock()
    page.viewport_size = {"width": 1280, "height": 800}

    def evaluate(script, *args):
        if "borderTopLeftRadius" in script:
            width = page.set_viewport_size.call_args.args[0]["width"]
            return {kind: [radius_at(width)] for kind in args[0]}
        if "fontSize" in script:
            return 12.0
        return None

    page.evaluate.side_effect = evaluate
    return page


def test_results_row_covers_are_measured_at_a_tablet_width() -> None:
    """The 8px-at-768px defect shipped because no width between 390px and
    1280px was measured; a cover rounded 8px at 768px must be reported."""
    page = _results_page(lambda width: 8.0 if width >= 768 else 4.0)
    failures = _frontend_gate_results._results_artwork_failures(page)
    assert failures
    assert all("expected 4px" in f for f in failures)
    assert {f.split(" at ")[1].split("px")[0] for f in failures} == {"768", "1023"}
    assert page.set_viewport_size.call_args.args[0] == {"width": 1280, "height": 800}


def test_results_row_covers_pass_when_the_step_is_at_1024px() -> None:
    page = _results_page(_frontend_gate_results.expected_artwork_radius)
    assert _frontend_gate_results._results_artwork_failures(page) == []
