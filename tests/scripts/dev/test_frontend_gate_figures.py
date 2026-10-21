"""Behaviour tests for the figure-face slice of the frontend gate.

The intended behaviour: a Results play count is set in the same face and
weight as a heatmap KPI value, and that reference is itself the figure face.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_figures as figures
from scripts.dev import frontend_gate
from tests.scripts.dev.gate_parity import defined_names

CHECK = "check_results_play_count_uses_the_figure_face"
FIGURE = "gotham,ff-din-paneuropean,ui-sans-serif,sans-serif"
SERIF = "instrument-serif,corporate-a,Georgia,serif"


def _reading(family: str = FIGURE, weight: str = "400", count: int = 3) -> dict:
    """A FACE_JS reading of `count` elements, with the token the page defines."""
    return {
        "token": FIGURE,
        "faces": [{"family": family, "weight": weight}] * count,
    }


def test_the_slice_defines_the_check_and_it_is_registered_for_every_profile() -> None:
    assert CHECK in defined_names(figures)
    assert CHECK not in defined_names(frontend_gate)
    entry = next(
        entry for entry in frontend_gate.CHECKS if entry[1] is getattr(figures, CHECK)
    )
    assert entry[0] == "results play count figure face"
    assert set(entry[2]) == {
        frontend_gate.DESKTOP,
        frontend_gate.MOBILE,
        frontend_gate.TOUCH_WIDE,
    }
    assert getattr(frontend_gate, CHECK) is getattr(figures, CHECK)


def test_a_play_count_in_the_kpi_face_and_weight_passes() -> None:
    assert figures.figure_face_failures(_reading(), _reading(count=4), "on load") == []


def test_a_serif_play_count_fails_naming_both_faces() -> None:
    """The defect the change removes: the count still set in the serif."""
    failures = figures.figure_face_failures(
        _reading(family=SERIF), _reading(count=4), "on load"
    )
    assert failures == [
        f"play count on load is set in {SERIF!r}, the heatmap KPI value in {FIGURE!r}"
    ]


def test_a_bold_play_count_fails_even_in_the_right_face() -> None:
    """Gotham is never bold: the kit's 700 blobs the numerals."""
    failures = figures.figure_face_failures(
        _reading(weight="700"), _reading(count=4), "on load"
    )
    assert failures == [
        "play count on load has font weight 700, the heatmap KPI value 400"
    ]


def test_a_reference_that_left_the_figure_face_fails_instead_of_agreeing() -> None:
    """Both elements drifting to the serif together must not pass."""
    failures = figures.figure_face_failures(
        _reading(family=SERIF), _reading(family=SERIF, count=4), "on load"
    )
    assert failures == [
        f"heatmap KPI value is set in {SERIF!r} at weight 400, expected the "
        f"figure face {FIGURE!r} at weight 400"
    ]


def test_a_reference_in_a_bold_weight_fails_instead_of_agreeing() -> None:
    failures = figures.figure_face_failures(
        _reading(weight="700"), _reading(weight="700", count=4), "on load"
    )
    assert len(failures) == 1
    assert failures[0].startswith("heatmap KPI value is set in")


def test_no_kpi_and_no_play_count_each_fail_rather_than_pass_vacuously() -> None:
    """A selector that matches nothing must not read as 'all equal'."""
    nothing = _reading(count=0)
    assert figures.figure_face_failures(_reading(), nothing, "on load") == [
        "heatmap renders no KPI value to compare the play count with"
    ]
    assert figures.figure_face_failures(nothing, _reading(), "on load") == [
        "results table renders no play count on load"
    ]


def test_one_wrong_face_among_many_rows_is_reported_once() -> None:
    plays = {
        "token": FIGURE,
        "faces": [
            {"family": FIGURE, "weight": "400"},
            {"family": SERIF, "weight": "400"},
            {"family": SERIF, "weight": "400"},
        ],
    }
    failures = figures.figure_face_failures(plays, _reading(count=4), "on load")
    assert len(failures) == 1
    assert "instrument-serif" in failures[0]


def test_a_four_digit_count_inside_its_cell_passes() -> None:
    reading = {"text": "8080", "right": 300.0, "limit": 302.0}
    assert figures.count_fit_failures(reading, "on load") == []
    edge = {"text": "8080", "right": 302.4, "limit": 302.0}
    assert figures.count_fit_failures(edge, "on load") == []


def test_a_four_digit_count_past_its_cell_fails_with_the_overshoot() -> None:
    """The defect the narrow-screen sizing prevents: Gotham's digits running
    out of the 3.75rem column into the release date."""
    reading = {"text": "8080", "right": 305.0, "limit": 302.0}
    assert figures.count_fit_failures(reading, "on load") == [
        "play count 8080 on load ends 3.0px past the cell it sits in"
    ]


def test_a_missing_four_digit_count_fails_rather_than_passes() -> None:
    assert figures.count_fit_failures(None, "on load") == [
        "results table renders no four-digit play count on load"
    ]


class _Page:
    """A page stand-in: answers the face probe and records navigation."""

    def __init__(self, kpi, plays, goto_fails=None, width=1280, fit=None):
        self.viewport_size = {"width": width, "height": 800}
        self.fit = fit or {"text": "8080", "right": 300.0, "limit": 302.0}
        self.kpi = kpi
        self.plays = list(plays)
        self.goto_fails = goto_fails
        self.visited = []
        self.clicked = []
        self.routes = []
        self.unrouted = []

    def route(self, pattern, handler):
        self.routes.append(pattern)

    def unroute(self, pattern, handler=None):
        self.unrouted.append(pattern)

    def goto(self, url, **kwargs):
        if self.goto_fails and self.goto_fails in url:
            raise TimeoutError("navigation stalled")
        self.visited.append(url.split("?")[0].rsplit("/", 1)[-1])

    def wait_for_selector(self, selector, **kwargs):
        self.visited.append(f"wait:{selector}")

    def evaluate(self, script, arg=None):
        if script == figures.FACE_JS:
            return self.kpi if arg[0] == figures.KPI_SELECTOR else self.plays.pop(0)
        if script == figures.FIT_JS:
            return self.fit
        return None

    def locator(self, selector):
        node = MagicMock()
        node.click.side_effect = lambda **kwargs: self.clicked.append(selector)
        return node


def _run(page):
    with patch.object(figures, "jobs") as jobs:
        jobs.create.side_effect = ["results-job", "heatmap-job"]
        failures = getattr(figures, CHECK)(page, "http://gate")
    return failures, jobs


def test_the_check_passes_when_both_reads_agree_and_cleans_up() -> None:
    page = _Page(_reading(count=4), [_reading(), _reading()])
    failures, jobs = _run(page)
    assert failures == []
    assert page.visited == [
        "heatmap",
        f"wait:{figures.KPI_SELECTOR}",
        "results",
    ]
    assert page.clicked == ["#toggle-sort-playtime", "#toggle-sort-plays"]
    jobs.delete.assert_any_call("results-job")
    jobs.delete.assert_any_call("heatmap-job")
    assert page.unrouted == page.routes


def test_a_cell_rebuilt_by_a_sort_switch_is_judged_again() -> None:
    """results.js rebuilds the cell on a sort switch; the rebuilt one must
    wear the face too."""
    page = _Page(_reading(count=4), [_reading(), _reading(family=SERIF)])
    failures, _ = _run(page)
    assert failures == [
        f"play count after switching sort is set in {SERIF!r}, "
        f"the heatmap KPI value in {FIGURE!r}"
    ]


_SPILLS = {"text": "8080", "right": 306.0, "limit": 302.0}


def test_at_the_mobile_profile_a_spilling_count_fails_on_load_and_after_a_switch() -> (
    None
):
    page = _Page(_reading(count=4), [_reading(), _reading()], width=390, fit=_SPILLS)
    failures, _ = _run(page)
    assert failures == [
        "play count 8080 on load ends 4.0px past the cell it sits in",
        "play count 8080 after switching sort ends 4.0px past the cell it sits in",
    ]


def test_at_a_desktop_width_the_fit_is_not_judged() -> None:
    """The narrow-screen sizing is mobile only; wide rows keep the full size."""
    page = _Page(_reading(count=4), [_reading(), _reading()], width=1280, fit=_SPILLS)
    failures, _ = _run(page)
    assert failures == []


def test_both_jobs_are_deleted_even_when_a_page_never_loads() -> None:
    page = _Page(_reading(count=4), [], goto_fails="/results")
    with patch.object(figures, "jobs") as jobs:
        jobs.create.side_effect = ["results-job", "heatmap-job"]
        with pytest.raises(TimeoutError):
            getattr(figures, CHECK)(page, "http://gate")
    jobs.delete.assert_any_call("results-job")
    jobs.delete.assert_any_call("heatmap-job")
