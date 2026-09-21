"""Parity and behaviour tests for the pipeline slice of the frontend gate."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_pipeline, frontend_gate
from scripts.dev._frontend_gate_pipeline import (
    _assert_loading_progress_state,
    _parse_matrix_scalex,
    check_pipeline_state_machines,
)
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_loading_composition",
    "check_pipeline_state_machines",
    "check_artist_spotlight_rotation",
)
CONSTANTS = (
    "ALBUM_PROGRESS_TRACK",
    "ALBUM_PROGRESS_BAR",
    "ALBUM_PROGRESS_TEXT",
    "HEATMAP_PROGRESS_TRACK",
    "HEATMAP_PROGRESS_BAR",
    "HEATMAP_PROGRESS_TEXT",
    "FETCHING_SCROBBLES",
    "COUNTING_SCROBBLES",
    "PAGE_23_OF_102",
    "PAGE_90_OF_100",
)
HELPERS = (
    "_parse_matrix_scalex",
    "_assert_loading_progress_state",
    "_exercise_loading_progress_phases",
    "_check_phase_repository_isolation",
    "_exercise_counted_progress",
    "_exercise_album_progress",
    "_exercise_heatmap_progress",
    "_exercise_replaced_job_progress",
    "_exercise_pipeline_state_machines",
)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS, *HELPERS))
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_pipeline)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS))
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_pipeline, name)


def test_pipeline_state_machine_uses_a_disposable_page() -> None:
    """Its page-level timer patch must not reach later checks."""
    page = MagicMock()
    probe = page.context.new_page.return_value

    with (
        patch.dict(
            "scripts.dev.frontend_gate.GATE_JOB_IDS",
            {"album": "album-job", "heatmap": "heatmap-job"},
            clear=True,
        ),
        patch("scripts.dev._frontend_gate_pipeline.reset_job_state"),
        patch("scripts.dev._frontend_gate_pipeline.set_job_progress"),
        patch(
            "scripts.dev._frontend_gate_pipeline._exercise_pipeline_state_machines",
            side_effect=RuntimeError("pipeline failed"),
        ) as exercise,
    ):
        with pytest.raises(RuntimeError, match="pipeline failed"):
            check_pipeline_state_machines(page, "http://127.0.0.1:0")

    exercise.assert_called_once_with(probe, "http://127.0.0.1:0")
    probe.close.assert_called_once()


def test_parse_matrix_scalex_recovers_scale_and_handles_boundaries() -> None:
    """The matrix parser must extract scaleX, support zero/identity, and handle invalid strings."""
    assert _parse_matrix_scalex("matrix(0.2255, 0, 0, 1, 0, 0)") == pytest.approx(
        0.2255
    )
    assert _parse_matrix_scalex("matrix(0.9, 0, 0, 1, 0, 0)") == pytest.approx(0.9)
    assert _parse_matrix_scalex("matrix(1, 0, 0, 1, 0, 0)") == pytest.approx(1.0)
    assert _parse_matrix_scalex("none") == 0.0
    assert _parse_matrix_scalex(None) == 0.0
    assert _parse_matrix_scalex("") == 0.0
    assert _parse_matrix_scalex("invalid") is None
    assert _parse_matrix_scalex("matrix()") is None


def test_assert_loading_progress_state_reports_mismatches() -> None:
    """The progress state assertion must report any discrepancy in valuenow, valuetext, visible text, or scale."""
    page = MagicMock()
    valid_state = {
        "valuenow": "23",
        "valuetext": "FETCHING SCROBBLES · PAGE 23 / 102",
        "transform": "matrix(0.2255, 0, 0, 1, 0, 0)",
        "phaseText": "FETCHING SCROBBLES · PAGE 23 / 102",
    }
    page.evaluate.return_value = dict(valid_state)

    # Clean match produces no failures
    assert (
        _assert_loading_progress_state(
            page,
            "#track",
            "#bar",
            "#text",
            expected_valuenow=23,
            expected_scalex=0.2255,
            expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
        )
        == []
    )

    # Mismatched valuenow
    page.evaluate.return_value = dict(valid_state, valuenow="99")
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "aria-valuenow was '99'" in failures[0]

    # Mismatched valuetext
    page.evaluate.return_value = dict(valid_state, valuetext="Wrong")
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "aria-valuetext was 'Wrong'" in failures[0]

    # Mismatched visible text
    page.evaluate.return_value = dict(valid_state, phaseText="Stale text")
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "visible text was 'Stale text'" in failures[0]

    # Mismatched scale
    page.evaluate.return_value = dict(
        valid_state, transform="matrix(0.5, 0, 0, 1, 0, 0)"
    )
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "scaleX was 0.5" in failures[0]


def test_phase_repository_probe_checks_real_isolation_and_invalid_views() -> None:
    """The extracted diagnostic exercises real storage and detects missing snapshots."""
    job = _frontend_gate_pipeline.create_job({"username": "probe"})
    try:
        assert _frontend_gate_pipeline._check_phase_repository_isolation(job) == []
        assert _frontend_gate_pipeline.get_job_progress(job)["phase"]["current"] == 23
        with (
            patch.object(
                _frontend_gate_pipeline, "get_job_progress", return_value=None
            ),
            patch.object(_frontend_gate_pipeline, "get_job_context", return_value=None),
        ):
            failures = _frontend_gate_pipeline._check_phase_repository_isolation(job)
        assert len(failures) == 6
    finally:
        _frontend_gate_pipeline.delete_job(job)


def test_replaced_job_probe_reports_stale_delivery_and_cleans_up() -> None:
    """Late old-job data is checked and temporary job/routes are removed on faults."""
    page = MagicMock()
    held = MagicMock()
    held.request.url = "http://local/progress?job_id=old-job"
    page.route.side_effect = lambda pattern, handler: handler(held)
    page.locator.return_value.get_attribute.return_value = "20"
    page.locator.return_value.inner_text.return_value = "PAGE 20 / 100"
    with (
        patch.object(_frontend_gate_pipeline, "create_job", return_value="replacement"),
        patch.object(_frontend_gate_pipeline, "set_job_progress"),
        patch.object(_frontend_gate_pipeline, "delete_job") as delete,
    ):
        failures = _frontend_gate_pipeline._exercise_replaced_job_progress(
            page, "http://local", "old-job", "/heatmap?job_id=old-job"
        )
        assert failures == [
            "stale out-of-order progress response regressed aria-valuenow",
            "stale out-of-order progress response regressed visible text",
        ]
        assert held.fulfill.call_args.kwargs["status"] == 200
        response = held.fulfill.call_args.kwargs
        payload = response.get("json") or json.loads(response["body"])
        assert payload == {
            "progress": 20,
            "phase": {
                "key": "lastfm_fetch",
                "label": "Fetching scrobbles",
                "unit": "page",
                "current": 20,
                "total": 100,
            },
        }
        delete.assert_called_once_with("replacement")
        page.unroute.assert_called_once_with("**/progress?job_id=*")
        page.goto.side_effect = RuntimeError("navigation broke")
        with pytest.raises(RuntimeError, match="navigation broke"):
            _frontend_gate_pipeline._exercise_replaced_job_progress(
                page, "http://local", "old-job", "/heatmap?job_id=old-job"
            )
        assert delete.call_count == 2
        assert page.unroute.call_count == 2


@pytest.mark.parametrize("client", ("album", "heatmap"))
def test_counted_sequence_updates_real_storage_and_detects_stale_text(client) -> None:
    """Both clients receive the same phase transitions and report an uncleared fraction."""
    job = _frontend_gate_pipeline.create_job({"username": "probe"})
    page = MagicMock()
    snapshots = []
    expected = [
        (
            "23",
            "FETCHING SCROBBLES · PAGE 23 / 102",
            "matrix(0.2255, 0, 0, 1, 0, 0)",
        ),
        ("90", "FETCHING SCROBBLES · PAGE 90 / 100", "matrix(0.9, 0, 0, 1, 0, 0)"),
        ("92", "Counting daily scrobbles", "matrix(0.92, 0, 0, 1, 0, 0)"),
    ]

    def read_state(script, selectors):
        """Capture the producer state before returning the simulated browser frame."""
        snapshots.append(_frontend_gate_pipeline.get_job_progress(job))
        value, text, transform = expected[len(snapshots) - 1]
        return {
            "valuenow": value,
            "valuetext": text,
            "phaseText": text,
            "transform": transform,
        }

    page.evaluate.side_effect = read_state
    page.locator.return_value.inner_text.return_value = "PAGE 90 / 100"
    try:
        failures = _frontend_gate_pipeline._exercise_counted_progress(
            page, "http://local", job, "/loading", ("#track", "#bar", "#text"), client
        )
        assert failures == [f"{client} uncounted frame retained stale phase fraction"]
        assert [snapshot["progress"] for snapshot in snapshots] == [20, 90, 92]
        assert [snapshot.get("phase") for snapshot in snapshots] == [
            {
                "key": "lastfm_fetch",
                "label": "Fetching scrobbles",
                "unit": "page",
                "current": 23,
                "total": 102,
            },
            {
                "key": "lastfm_fetch",
                "label": "Fetching scrobbles",
                "unit": "page",
                "current": 90,
                "total": 100,
            },
            None,
        ]
    finally:
        _frontend_gate_pipeline.delete_job(job)
