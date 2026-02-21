# tests/test_repositories.py
import json
import logging
import time
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope.cache import (
    _batch_lookup_metadata,
    _batch_persist_metadata,
    _get_db_connection,
)
from scrobblescope.config import JOB_TTL_SECONDS
from scrobblescope.repositories import (
    JOBS,
    cleanup_expired_jobs,
    create_job,
    delete_job,
    get_job_progress,
    jobs_lock,
    set_job_error,
    set_job_progress,
    set_job_stat,
)
from tests.helpers import TEST_JOB_PARAMS

# --- Job state tests ---


def test_set_job_error_sets_classified_fields():
    """
    GIVEN a job
    WHEN set_job_error is called with a retryable error code
    THEN the progress payload should contain error_code, error_source, and retryable fields.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_error(job_id, "lastfm_unavailable")
    progress = get_job_progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "lastfm_unavailable"
    assert progress["error_source"] == "lastfm"
    assert progress["retryable"] is True
    assert progress["progress"] == 100


def test_set_job_error_user_not_found_not_retryable():
    """
    GIVEN a job
    WHEN set_job_error is called with user_not_found and a username
    THEN the error should not be retryable and the message should include the username.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_error(job_id, "user_not_found", username="ghost")
    progress = get_job_progress(job_id)
    assert progress["retryable"] is False
    assert "ghost" in progress["message"]
    assert progress["error_code"] == "user_not_found"


def test_create_job_returns_unique_ids():
    """
    GIVEN two calls to create_job
    WHEN both use identical params
    THEN each should return a different job ID.
    """
    id_a = create_job(TEST_JOB_PARAMS)
    id_b = create_job(TEST_JOB_PARAMS)
    assert id_a != id_b


def test_job_isolation_separate_progress():
    """
    GIVEN two independent jobs
    WHEN progress is updated on one
    THEN the other job's progress should be unaffected.
    """
    id_a = create_job(TEST_JOB_PARAMS)
    id_b = create_job(TEST_JOB_PARAMS)

    set_job_progress(id_a, progress=75, message="Almost done", error=False)
    set_job_progress(id_b, progress=10, message="Starting", error=False)

    progress_a = get_job_progress(id_a)
    progress_b = get_job_progress(id_b)

    assert progress_a["progress"] == 75
    assert progress_a["message"] == "Almost done"
    assert progress_b["progress"] == 10
    assert progress_b["message"] == "Starting"


def test_set_job_progress_missing_job_returns_false():
    """
    GIVEN a nonexistent job ID
    WHEN set_job_progress is called
    THEN it should return False.
    """
    result = set_job_progress("nonexistent_job_id", progress=50, message="test")
    assert result is False


def test_set_job_stat_stores_and_retrieves():
    """
    GIVEN a job
    WHEN set_job_stat is called with a key/value
    THEN get_job_progress should include that stat.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_stat(job_id, "scrobbles_fetched", 1234)
    set_job_stat(job_id, "albums_found", 42)

    progress = get_job_progress(job_id)
    assert progress["stats"]["scrobbles_fetched"] == 1234
    assert progress["stats"]["albums_found"] == 42


def test_expired_job_cleanup():
    """
    GIVEN a job whose timestamps are older than JOB_TTL_SECONDS
    WHEN cleanup_expired_jobs is called
    THEN the expired job should be removed.
    """
    job_id = create_job(TEST_JOB_PARAMS)

    # Manually backdate the job timestamps so it looks expired
    expired_time = time.time() - JOB_TTL_SECONDS - 60
    with jobs_lock:
        JOBS[job_id]["created_at"] = expired_time
        JOBS[job_id]["updated_at"] = expired_time

    cleanup_expired_jobs()

    assert get_job_progress(job_id) is None


def test_delete_job_removes_existing_job():
    """delete_job removes a job that exists in JOBS."""
    job_id = create_job(TEST_JOB_PARAMS)
    with jobs_lock:
        assert job_id in JOBS
    delete_job(job_id)
    with jobs_lock:
        assert job_id not in JOBS


def test_delete_job_on_missing_job_is_noop():
    """
    GIVEN a job_id that does not exist in JOBS
    WHEN delete_job is called with that id
    THEN it must not raise AND must not corrupt JOBS by inserting a new key.

    Previously no assertion existed, so the test would pass vacuously even if
    delete_job was completely empty.  Adding the JOBS-membership check makes the
    implicit contract explicit.
    """
    delete_job("nonexistent_id_xyz")  # must not raise
    with jobs_lock:
        assert "nonexistent_id_xyz" not in JOBS


# --- DB helper tests ---


@pytest.mark.asyncio
async def test_get_db_connection_no_asyncpg(caplog):
    """
    GIVEN asyncpg is None (not installed)
    WHEN _get_db_connection is called
    THEN it should return None immediately.
    """
    with patch("scrobblescope.cache.asyncpg", None):
        with caplog.at_level(logging.INFO):
            result = await _get_db_connection()
    assert result is None
    assert "asyncpg-missing" in caplog.text


@pytest.mark.asyncio
async def test_get_db_connection_no_database_url(caplog):
    """
    GIVEN asyncpg is available but DATABASE_URL is not set
    WHEN _get_db_connection is called
    THEN it should return None.
    """
    with patch.dict("os.environ", {}, clear=True):
        with caplog.at_level(logging.INFO):
            result = await _get_db_connection()
    assert result is None
    assert "missing-env-var" in caplog.text


@pytest.mark.asyncio
async def test_get_db_connection_connect_failure(caplog):
    """
    GIVEN DATABASE_URL is set but the connection fails
    WHEN _get_db_connection is called
    THEN it should return None and log a warning.
    """
    with patch.dict(
        "os.environ",
        {
            "DATABASE_URL": "postgres://bad:bad@localhost/bad",
            "DB_CONNECT_MAX_ATTEMPTS": "1",
        },
    ):
        with patch("scrobblescope.cache.asyncpg") as mock_asyncpg:
            mock_asyncpg.connect = AsyncMock(
                side_effect=Exception("connection refused")
            )
            with caplog.at_level(logging.INFO):
                result = await _get_db_connection()
    assert result is None
    assert "db-down" in caplog.text


@pytest.mark.asyncio
async def test_get_db_connection_retries_then_succeeds():
    """
    GIVEN DATABASE_URL is set and the first connection attempt fails
    WHEN a subsequent retry succeeds
    THEN _get_db_connection should return the connection object.
    """
    mock_conn = AsyncMock()
    with patch.dict(
        "os.environ",
        {
            "DATABASE_URL": "postgres://good:good@localhost/good",
            "DB_CONNECT_MAX_ATTEMPTS": "3",
            "DB_CONNECT_BASE_DELAY_SECONDS": "0",
        },
    ):
        with (
            patch("scrobblescope.cache.asyncpg") as mock_asyncpg,
            patch(
                "scrobblescope.cache.asyncio.sleep", new_callable=AsyncMock
            ) as mock_sleep,
        ):
            mock_asyncpg.connect = AsyncMock(
                side_effect=[Exception("temporary fail"), mock_conn]
            )
            result = await _get_db_connection()
    assert result is mock_conn
    assert mock_asyncpg.connect.await_count == 2
    mock_sleep.assert_awaited_once_with(0.0)


@pytest.mark.asyncio
async def test_get_db_connection_retry_exhaustion_returns_none():
    """
    GIVEN DATABASE_URL is set but all connection attempts fail
    WHEN retry budget is exhausted
    THEN _get_db_connection should return None.
    """
    with patch.dict(
        "os.environ",
        {
            "DATABASE_URL": "postgres://bad:bad@localhost/bad",
            "DB_CONNECT_MAX_ATTEMPTS": "3",
            "DB_CONNECT_BASE_DELAY_SECONDS": "0",
        },
    ):
        with (
            patch("scrobblescope.cache.asyncpg") as mock_asyncpg,
            patch(
                "scrobblescope.cache.asyncio.sleep", new_callable=AsyncMock
            ) as mock_sleep,
        ):
            mock_asyncpg.connect = AsyncMock(
                side_effect=Exception("connection refused")
            )
            result = await _get_db_connection()
    assert result is None
    assert mock_asyncpg.connect.await_count == 3
    assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_batch_lookup_metadata_empty_keys():
    """
    GIVEN an empty list of keys
    WHEN _batch_lookup_metadata is called
    THEN it should return an empty dict without making a DB call.
    """
    mock_conn = AsyncMock()
    result = await _batch_lookup_metadata(mock_conn, [])
    assert result == {}
    mock_conn.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_lookup_metadata_parses_track_durations():
    """
    GIVEN DB rows with track_durations as a JSON string
    WHEN _batch_lookup_metadata processes the results
    THEN it should parse them into Python dicts.
    """
    mock_row = {
        "artist_norm": "radiohead",
        "album_norm": "ok computer",
        "spotify_id": "abc123",
        "release_date": "1997-06-16",
        "album_image_url": "https://img.example.com/ok.jpg",
        "track_durations": '{"paranoid android": 383, "karma police": 264}',
    }
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[mock_row])

    result = await _batch_lookup_metadata(mock_conn, [("radiohead", "ok computer")])

    assert ("radiohead", "ok computer") in result
    td = result[("radiohead", "ok computer")]["track_durations"]
    assert isinstance(td, dict)
    assert td["paranoid android"] == 383
    assert td["karma police"] == 264


@pytest.mark.asyncio
async def test_batch_persist_metadata_empty_rows():
    """
    GIVEN an empty list of rows
    WHEN _batch_persist_metadata is called
    THEN it should return immediately without making a DB call.
    """
    mock_conn = AsyncMock()
    await _batch_persist_metadata(mock_conn, [])
    mock_conn.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_persist_metadata_upsert_call_shape():
    """
    GIVEN a list of metadata rows
    WHEN _batch_persist_metadata is called
    THEN it should execute a single INSERT ... unnest() statement
    with the correct array parameters.
    """
    mock_conn = AsyncMock()
    rows = [
        (
            "artist1",
            "album1",
            "sp1",
            "2025-01-01",
            "https://img/1.jpg",
            {"track a": 200},
        ),
        ("artist2", "album2", "sp2", "2024-06-15", None, {}),
    ]

    await _batch_persist_metadata(mock_conn, rows)

    mock_conn.execute.assert_awaited_once()
    call_args = mock_conn.execute.call_args
    sql = call_args[0][0]
    assert "INSERT INTO spotify_cache" in sql
    assert "unnest" in sql
    assert "ON CONFLICT" in sql
    # Verify array parameters
    assert call_args[0][1] == ["artist1", "artist2"]
    assert call_args[0][2] == ["album1", "album2"]
    assert call_args[0][3] == ["sp1", "sp2"]
    # track_durations should be JSON strings
    td_param = call_args[0][6]
    assert json.loads(td_param[0]) == {"track a": 200}
    assert json.loads(td_param[1]) == {}
