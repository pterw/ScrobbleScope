"""Unit tests for scripts.testing.concurrent_users_test.

All tests use mocked HTTP sessions or patched imports; no live server is
required.  Each test is designed to fail if the function under test is
deleted (no vacuous tests per AGENTS.md anti-pattern rules).
"""

from __future__ import annotations

import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

from scripts.testing.concurrent_users_test import (
    ConcurrentResult,
    build_parser,
    main,
    print_aggregate,
    print_thread_result,
    run_thread,
)

# ---------------------------------------------------------------------------
# ConcurrentResult dataclass
# ---------------------------------------------------------------------------


def test_concurrent_result_dataclass_fields():
    """
    GIVEN a ConcurrentResult instantiated with known values
    WHEN each field is accessed
    THEN the values match what was provided and types are as declared.
    """
    result = ConcurrentResult(
        thread_index=2,
        http_status=200,
        job_id="abc-123",
        elapsed_seconds=1.5,
        final_state="done",
        error=None,
    )

    assert result.thread_index == 2
    assert result.http_status == 200
    assert result.job_id == "abc-123"
    assert result.elapsed_seconds == 1.5
    assert result.final_state == "done"
    assert result.error is None


# ---------------------------------------------------------------------------
# run_thread
# ---------------------------------------------------------------------------


def test_run_thread_records_success():
    """
    GIVEN submit_job returning 'job-1' and poll_until_complete returning a
    progress=100 payload with status='done'
    WHEN run_thread is called
    THEN the result has job_id='job-1', error=None, and elapsed_seconds >= 0.
    """
    session = MagicMock()
    results: list[ConcurrentResult] = []
    # Barrier(1) releases immediately when the single thread calls wait().
    barrier = threading.Barrier(1)

    with (
        patch(
            "scripts.testing.concurrent_users_test.submit_job",
            return_value="job-1",
        ),
        patch(
            "scripts.testing.concurrent_users_test.poll_until_complete",
            return_value={"progress": 100, "status": "done"},
        ),
    ):
        run_thread(
            session=session,
            base_url="http://localhost",
            username="user1",
            year=2024,
            sort_by="playcount",
            release_scope="same",
            min_plays=10,
            min_tracks=3,
            timeout_seconds=60,
            poll_interval=0,
            thread_index=1,
            results=results,
            barrier=barrier,
        )

    assert len(results) == 1
    result = results[0]
    assert result.job_id == "job-1"
    assert result.error is None
    assert result.elapsed_seconds >= 0


def test_run_thread_records_error_on_exception():
    """
    GIVEN submit_job raising RuntimeError('connection refused')
    WHEN run_thread is called
    THEN the result has the error message in result.error and no exception
    propagates out of run_thread.
    """
    session = MagicMock()
    results: list[ConcurrentResult] = []
    barrier = threading.Barrier(1)

    with patch(
        "scripts.testing.concurrent_users_test.submit_job",
        side_effect=RuntimeError("connection refused"),
    ):
        # Must not raise -- exceptions are captured into result.error.
        run_thread(
            session=session,
            base_url="http://localhost",
            username="user1",
            year=2024,
            sort_by="playcount",
            release_scope="same",
            min_plays=10,
            min_tracks=3,
            timeout_seconds=60,
            poll_interval=0,
            thread_index=1,
            results=results,
            barrier=barrier,
        )

    assert len(results) == 1
    assert "connection refused" in results[0].error


# ---------------------------------------------------------------------------
# print_aggregate
# ---------------------------------------------------------------------------


def test_print_aggregate_counts(capsys):
    """
    GIVEN a list of 3 ConcurrentResult objects (2 completed, 1 failed)
    WHEN print_aggregate is called
    THEN stdout reports completed=2 and failed=1.
    """
    results = [
        ConcurrentResult(
            thread_index=1,
            http_status=200,
            job_id="j1",
            elapsed_seconds=1.0,
            final_state="done",
            error=None,
        ),
        ConcurrentResult(
            thread_index=2,
            http_status=200,
            job_id="j2",
            elapsed_seconds=2.0,
            final_state="done",
            error=None,
        ),
        ConcurrentResult(
            thread_index=3,
            http_status=None,
            job_id=None,
            elapsed_seconds=0.5,
            final_state=None,
            error="timeout",
        ),
    ]
    print_aggregate(results)

    captured = capsys.readouterr()
    assert "completed=2" in captured.out
    assert "failed=1" in captured.out


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------


def test_build_parser_concurrency_default():
    """
    GIVEN no CLI arguments
    WHEN build_parser().parse_args([]) is called
    THEN args.concurrency equals the documented default of 3.
    """
    args = build_parser().parse_args([])

    assert args.concurrency == 3


# ---------------------------------------------------------------------------
# main -- thread count
# ---------------------------------------------------------------------------


def test_main_launches_correct_thread_count(monkeypatch, capsys):
    """
    GIVEN threading.Thread and requests.Session are patched
    WHEN main() is called with --concurrency 3
    THEN threading.Thread is instantiated exactly 3 times.
    """
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "concurrent",
            "--concurrency",
            "3",
            "--username",
            "testuser",
            "--year",
            "2024",
        ],
    )

    with (
        patch(
            "scripts.testing.concurrent_users_test.threading.Thread"
        ) as mock_thread_cls,
        patch("scripts.testing.concurrent_users_test.requests.Session"),
    ):
        mock_thread_cls.return_value = MagicMock()
        main()

    assert mock_thread_cls.call_count == 3
