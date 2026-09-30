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


def test_a_credit_that_ends_inside_its_cell_passes() -> None:
    reading = {"credit_right": 320.0, "cell_right": 324.0}
    assert _frontend_gate_results.artist_credit_failures(reading, 1024) == []


def test_a_credit_that_runs_past_its_cell_names_the_width_and_the_overrun() -> None:
    """The defect: a credit ended at x 674 in a cell that ends at 324."""
    reading = {"credit_right": 674.0, "cell_right": 324.0}
    assert _frontend_gate_results.artist_credit_failures(reading, 1024) == [
        "results artist credit at 1024px runs 350px past the cell that holds it"
    ]


def test_a_missing_credit_fails_instead_of_passing() -> None:
    failures = _frontend_gate_results.artist_credit_failures(None, 768)
    assert failures == ["results table at 768px renders no long artist credit"]


def _long_credit_page(credit_right_at):
    """A page whose long credit ends at `credit_right_at(width)` in a cell that
    ends at 324px."""
    page = MagicMock()
    page.viewport_size = {"width": 1280, "height": 800}

    def evaluate(script, *args):
        if args and args[0] == _frontend_gate_results.LONG_ARTIST_CREDIT:
            width = page.set_viewport_size.call_args.args[0]["width"]
            return {"credit_right": credit_right_at(width), "cell_right": 324.0}
        return None

    page.evaluate.side_effect = evaluate
    return page


def test_the_long_credit_is_measured_at_every_width_and_the_viewport_restored() -> None:
    page = _long_credit_page(lambda width: 674.0 if width == 1024 else 300.0)
    failures = _frontend_gate_results._long_artist_failures(page)
    assert failures == [
        "results artist credit at 1024px runs 350px past the cell that holds it"
    ]
    widths = [call.args[0]["width"] for call in page.set_viewport_size.call_args_list]
    assert widths[:-1] == list(_frontend_gate_results.LONG_ARTIST_WIDTHS)
    assert page.set_viewport_size.call_args.args[0] == {"width": 1280, "height": 800}


def _badge(size: float = 12.0, family: str = "Narrow,monospace") -> dict:
    return {"size": size, "family": family, "narrow": "Narrow,monospace"}


def test_a_badge_at_the_floor_in_the_narrow_face_passes() -> None:
    assert _frontend_gate_results.provider_badge_failures(_badge(), "deezer") == []


def test_a_ten_pixel_badge_in_the_wide_face_fails_on_both_counts() -> None:
    failures = _frontend_gate_results.provider_badge_failures(
        _badge(10.0, "Mono,monospace"), "deezer"
    )
    assert failures == [
        "deezer row's provider badge text is 10.0px, expected at least 12px",
        "deezer row's provider badge is set in 'Mono,monospace', expected the "
        "narrow mono face 'Narrow,monospace'",
    ]


def test_a_badge_with_no_narrow_token_to_compare_fails() -> None:
    reading = {"size": 12.0, "family": "", "narrow": ""}
    assert _frontend_gate_results.provider_badge_failures(reading, "deezer") == [
        "deezer row's provider badge is set in '', expected the narrow mono face ''"
    ]
