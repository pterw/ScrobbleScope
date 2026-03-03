"""Unit tests for scripts.testing._http_client and scripts.testing.smoke_cache_check.

All tests use mocked HTTP sessions or patched imports; no live server is required.
Each test is designed to fail if the function under test is deleted (no vacuous
tests per AGENTS.md anti-pattern rules).
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from scripts.testing._http_client import (
    fetch_csrf_token,
    poll_until_complete,
    submit_job,
)
from scripts.testing.smoke_cache_check import (
    RunResult,
    build_parser,
    main,
    print_run_summary,
    run_once,
)

# ---------------------------------------------------------------------------
# _http_client -- fetch_csrf_token
# ---------------------------------------------------------------------------


def test_fetch_csrf_token_returns_token_from_html():
    """
    GIVEN a mock session whose GET returns HTML with a valid csrf_token input field
    WHEN fetch_csrf_token is called
    THEN the token value is extracted and returned.
    """
    html = '<form><input name="csrf_token" value="abc123" type="hidden"></form>'
    response = MagicMock()
    response.text = html
    response.raise_for_status.return_value = None
    session = MagicMock()
    session.get.return_value = response

    token = fetch_csrf_token(session, "http://localhost")

    assert token == "abc123"


def test_fetch_csrf_token_raises_when_field_absent():
    """
    GIVEN a mock session whose GET returns HTML without a csrf_token input field
    WHEN fetch_csrf_token is called
    THEN RuntimeError is raised.
    """
    html = "<html><body><form></form></body></html>"
    response = MagicMock()
    response.text = html
    response.raise_for_status.return_value = None
    session = MagicMock()
    session.get.return_value = response

    with pytest.raises(RuntimeError, match="csrf_token"):
        fetch_csrf_token(session, "http://localhost")


# ---------------------------------------------------------------------------
# _http_client -- submit_job
# ---------------------------------------------------------------------------


def test_submit_job_returns_job_id():
    """
    GIVEN a mock session that returns a CSRF token on GET and a valid
    scrobble-config script block on POST
    WHEN submit_job is called
    THEN the job_id from the parsed JSON payload is returned.
    """
    csrf_html = '<input name="csrf_token" value="tok123">'
    loading_html = (
        '<script id="scrobble-config" type="application/json">'
        '{"job_id": "xyz-789"}'
        "</script>"
    )
    csrf_response = MagicMock()
    csrf_response.text = csrf_html
    csrf_response.raise_for_status.return_value = None

    post_response = MagicMock()
    post_response.text = loading_html
    post_response.raise_for_status.return_value = None

    session = MagicMock()
    session.get.return_value = csrf_response
    session.post.return_value = post_response

    job_id = submit_job(session, "http://localhost", username="user1", year=2024)

    assert job_id == "xyz-789"


def test_submit_job_raises_when_scrobble_absent():
    """
    GIVEN a POST response that contains no <script id="scrobble-config"> block
    WHEN submit_job is called
    THEN RuntimeError is raised referencing the missing block.
    """
    csrf_html = '<input name="csrf_token" value="tok456">'
    post_html = "<html><body>Unexpected page content</body></html>"

    csrf_response = MagicMock()
    csrf_response.text = csrf_html
    csrf_response.raise_for_status.return_value = None

    post_response = MagicMock()
    post_response.text = post_html
    post_response.raise_for_status.return_value = None

    session = MagicMock()
    session.get.return_value = csrf_response
    session.post.return_value = post_response

    with pytest.raises(RuntimeError, match="scrobble-config"):
        submit_job(session, "http://localhost", username="user1", year=2024)


def test_submit_job_raises_when_job_id_absent():
    """
    GIVEN a POST response containing a scrobble-config block whose JSON has no
    job_id key
    WHEN submit_job is called
    THEN RuntimeError is raised referencing the missing job_id.
    """
    csrf_html = '<input name="csrf_token" value="tok789">'
    # scrobble-config block present but payload has no job_id key
    loading_html = (
        '<script id="scrobble-config" type="application/json">'
        '{"other_key": "some_value"}'
        "</script>"
    )
    csrf_response = MagicMock()
    csrf_response.text = csrf_html
    csrf_response.raise_for_status.return_value = None

    post_response = MagicMock()
    post_response.text = loading_html
    post_response.raise_for_status.return_value = None

    session = MagicMock()
    session.get.return_value = csrf_response
    session.post.return_value = post_response

    with pytest.raises(RuntimeError, match="job_id"):
        submit_job(session, "http://localhost", username="user1", year=2024)


# ---------------------------------------------------------------------------
# _http_client -- poll_until_complete
# ---------------------------------------------------------------------------


def test_poll_returns_on_progress_100():
    """
    GIVEN a mock session whose first poll returns progress=100
    WHEN poll_until_complete is called
    THEN the payload is returned after exactly one GET call (no retry).
    """
    payload = {"progress": 100, "stats": {}, "message": "done"}
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload

    session = MagicMock()
    session.get.return_value = response

    result = poll_until_complete(
        session, "http://localhost", "job-abc", timeout_seconds=60, poll_interval=0
    )

    assert result == payload
    assert session.get.call_count == 1


def test_poll_raises_on_unexpected_status():
    """
    GIVEN a mock session whose GET returns HTTP 500
    WHEN poll_until_complete is called
    THEN RuntimeError is raised immediately referencing the status code.
    """
    response = MagicMock()
    response.status_code = 500
    response.text = "Internal Server Error"

    session = MagicMock()
    session.get.return_value = response

    with pytest.raises(RuntimeError, match="500"):
        poll_until_complete(
            session, "http://localhost", "job-abc", timeout_seconds=60, poll_interval=0
        )


@patch("scripts.testing._http_client.time")
def test_poll_raises_timeout_when_deadline_exceeded(mock_time):
    """
    GIVEN a mock session that always returns progress=50 and a mocked time that
    expires after one poll iteration
    WHEN poll_until_complete is called
    THEN TimeoutError is raised.

    The time.time() side_effect drives the loop:
    - Call 1 (deadline calc): returns 0; deadline = 0 + 0.1 = 0.1
    - Call 2 (while check #1): returns 0; 0 < 0.1 = True (enters loop)
    - One poll: progress=50, no early return; time.sleep mocked
    - Call 3 (while check #2): returns 100; 100 < 0.1 = False (exits loop)
    TimeoutError is raised after the loop.
    """
    mock_time.time.side_effect = [0, 0, 100]
    mock_time.sleep.return_value = None

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"progress": 50}

    session = MagicMock()
    session.get.return_value = response

    with pytest.raises(TimeoutError, match="Timed out"):
        poll_until_complete(
            session,
            "http://localhost",
            "job-abc",
            timeout_seconds=0.1,
            poll_interval=1,
        )


# ---------------------------------------------------------------------------
# smoke_cache_check -- run_once
# ---------------------------------------------------------------------------


def test_run_once_raises_on_job_error():
    """
    GIVEN submit_job and poll_until_complete are patched to return a progress
    payload with error=True
    WHEN run_once is called
    THEN RuntimeError is raised with the error_code in the message.
    """
    error_payload = {
        "progress": 100,
        "error": True,
        "error_code": "UPSTREAM_FAIL",
        "message": "Last.fm is down",
    }
    session = MagicMock()

    with (
        patch("scripts.testing.smoke_cache_check.submit_job", return_value="job-err"),
        patch(
            "scripts.testing.smoke_cache_check.poll_until_complete",
            return_value=error_payload,
        ),
    ):
        with pytest.raises(RuntimeError, match="UPSTREAM_FAIL"):
            run_once(
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
                run_index=1,
            )


# ---------------------------------------------------------------------------
# smoke_cache_check -- print_run_summary
# ---------------------------------------------------------------------------


def test_print_run_summary_includes_key_fields(capsys):
    """
    GIVEN a RunResult with known job_id, elapsed_seconds, and stats
    WHEN print_run_summary is called
    THEN stdout contains db_cache_lookup_hits, elapsed, and job_id.
    """
    result = RunResult(
        run_index=1,
        job_id="test-job-001",
        elapsed_seconds=2.5,
        stats={"db_cache_lookup_hits": 7, "db_cache_persisted": 3},
        message="All done",
    )
    print_run_summary(result)

    captured = capsys.readouterr()
    assert "db_cache_lookup_hits=7" in captured.out
    assert "elapsed=2.50s" in captured.out
    assert "job_id=test-job-001" in captured.out


# ---------------------------------------------------------------------------
# smoke_cache_check -- build_parser
# ---------------------------------------------------------------------------


def test_build_parser_defaults():
    """
    GIVEN no CLI arguments
    WHEN build_parser().parse_args([]) is called
    THEN base_url, username, and runs match their documented defaults.
    """
    args = build_parser().parse_args([])

    assert args.base_url == "http://localhost:5000"
    assert args.username == "flounder14"
    assert args.runs == 2


# ---------------------------------------------------------------------------
# smoke_cache_check -- verdict logic
# ---------------------------------------------------------------------------


def test_main_verdict_pass_when_db_cache_hits_on_run_2(monkeypatch, capsys):
    """
    GIVEN run_once is patched to return a first result with no DB cache hits
    and a second result with db_cache_lookup_hits > 0
    WHEN main() is called with --runs 2
    THEN 'verdict=PASS' appears in stdout.
    """
    monkeypatch.setattr(
        sys,
        "argv",
        ["smoke", "--runs", "2", "--username", "testuser", "--year", "2024"],
    )
    r1 = RunResult(
        run_index=1,
        job_id="j1",
        elapsed_seconds=5.0,
        stats={"db_cache_lookup_hits": 0},
        message="",
    )
    r2 = RunResult(
        run_index=2,
        job_id="j2",
        elapsed_seconds=1.0,
        stats={"db_cache_lookup_hits": 5},
        message="",
    )

    # requests.Session is used as a context manager; mock the CM protocol.
    mock_session_cm = MagicMock()
    mock_session_cm.__enter__.return_value = MagicMock()
    mock_session_cm.__exit__.return_value = False

    with (
        patch(
            "scripts.testing.smoke_cache_check.requests.Session",
            return_value=mock_session_cm,
        ),
        patch("scripts.testing.smoke_cache_check.run_once", side_effect=[r1, r2]),
    ):
        main()

    captured = capsys.readouterr()
    assert "verdict=PASS" in captured.out


def test_main_verdict_inconclusive_when_no_db_cache_hits(monkeypatch, capsys):
    """
    GIVEN run_once is patched to return two results both with db_cache_lookup_hits == 0
    WHEN main() is called with --runs 2
    THEN 'verdict=INCONCLUSIVE' appears in stdout.
    """
    monkeypatch.setattr(
        sys,
        "argv",
        ["smoke", "--runs", "2", "--username", "testuser", "--year", "2024"],
    )
    r1 = RunResult(
        run_index=1,
        job_id="j1",
        elapsed_seconds=5.0,
        stats={"db_cache_lookup_hits": 0},
        message="",
    )
    r2 = RunResult(
        run_index=2,
        job_id="j2",
        elapsed_seconds=4.5,
        stats={"db_cache_lookup_hits": 0},
        message="",
    )

    mock_session_cm = MagicMock()
    mock_session_cm.__enter__.return_value = MagicMock()
    mock_session_cm.__exit__.return_value = False

    with (
        patch(
            "scripts.testing.smoke_cache_check.requests.Session",
            return_value=mock_session_cm,
        ),
        patch("scripts.testing.smoke_cache_check.run_once", side_effect=[r1, r2]),
    ):
        main()

    captured = capsys.readouterr()
    assert "verdict=INCONCLUSIVE" in captured.out
