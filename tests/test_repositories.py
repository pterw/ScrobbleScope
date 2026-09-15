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
    get_job_context,
    get_job_progress,
    jobs_lock,
    set_job_error,
    set_job_progress,
    set_job_release_check,
    set_job_results,
    set_job_stat,
    update_job_result,
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
    assert progress is not None
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
    assert progress is not None
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
    assert progress_a is not None
    assert progress_b is not None

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
    assert progress is not None
    assert progress["stats"]["scrobbles_fetched"] == 1234
    assert progress["stats"]["albums_found"] == 42


def test_set_job_release_check_stores_state_under_progress_stats():
    """
    GIVEN a job
    WHEN set_job_release_check records the correction worker's state
    THEN it lands at progress.stats.release_check, replacing any earlier
    state, and leaves neighbouring stats untouched.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_stat(job_id, "albums_found", 42)

    running = {
        "status": "running",
        "checked": 1,
        "total": 3,
        "moved_out": 0,
        "moved_in": 0,
    }
    assert set_job_release_check(job_id, running) is True
    assert get_job_progress(job_id)["stats"]["release_check"] == running

    done = {**running, "status": "done", "checked": 3, "moved_out": 1}
    assert set_job_release_check(job_id, done) is True
    progress = get_job_progress(job_id)
    assert progress["stats"]["release_check"] == done
    assert progress["stats"]["albums_found"] == 42


def test_set_job_release_check_on_a_missing_job_returns_false():
    """
    GIVEN a job id that expired while the worker was running
    WHEN set_job_release_check is called
    THEN it returns False and does not resurrect the job in JOBS.
    """
    assert set_job_release_check("nonexistent_job_id", {"status": "done"}) is False
    with jobs_lock:
        assert "nonexistent_job_id" not in JOBS


def test_update_job_result_merges_fields_into_the_matching_result():
    """
    GIVEN a job whose results list holds two albums
    WHEN update_job_result targets one by its normalized key
    THEN only that entry gains the new fields, its existing fields survive,
    and the list keeps its rank order and length.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_results(
        job_id,
        [
            {"artist": "Radiohead", "album": "OK Computer", "play_count": 50},
            {"artist": "Blur", "album": "13", "play_count": 20},
        ],
    )

    assert update_job_result(job_id, ("blur", "13"), {"release_check": "moved_out"})

    results = get_job_context(job_id)["results"]
    assert len(results) == 2
    assert results[1] == {
        "artist": "Blur",
        "album": "13",
        "play_count": 20,
        "release_check": "moved_out",
    }
    assert "release_check" not in results[0]


def test_update_job_result_matches_on_the_normalized_name():
    """
    GIVEN a result whose displayed album title carries edition metadata
    WHEN update_job_result is given the normalized cache key
    THEN it still finds the entry -- result dicts carry no pre-normalized key.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_results(
        job_id, [{"artist": "Radiohead", "album": "OK Computer (Deluxe Edition)"}]
    )

    assert update_job_result(job_id, ("radiohead", "ok computer"), {"x": 1}) is True
    assert get_job_context(job_id)["results"][0]["x"] == 1


def test_update_job_result_returns_false_when_nothing_matches():
    """
    GIVEN a job whose results hold no album with the requested key
    WHEN update_job_result is called
    THEN it returns False and leaves every result unchanged.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_results(job_id, [{"artist": "Blur", "album": "13"}])

    assert update_job_result(job_id, ("oasis", "be here now"), {"y": 1}) is False
    assert get_job_context(job_id)["results"] == [{"artist": "Blur", "album": "13"}]


def test_update_job_result_returns_false_when_results_are_absent():
    """
    GIVEN a job that has not finished (results is still None) and one that
    no longer exists
    WHEN update_job_result is called
    THEN both return False rather than raising on the missing list.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    assert update_job_result(job_id, ("blur", "13"), {"z": 1}) is False
    assert update_job_result("nonexistent_job_id", ("blur", "13"), {"z": 1}) is False


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
    with patch("scrobblescope.cache._DATABASE_URL", None):
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
    with patch("scrobblescope.cache._DATABASE_URL", "postgres://bad:bad@localhost/bad"):
        with patch.dict(
            "os.environ",
            {
                "DB_CONNECT_MAX_ATTEMPTS": "1",
                "DB_CONNECT_BASE_DELAY_SECONDS": "0",
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
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://good:good@localhost/good",
    ):
        with patch.dict(
            "os.environ",
            {
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
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://bad:bad@localhost/bad",
    ):
        with patch.dict(
            "os.environ",
            {
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
async def test_get_db_connection_passes_explicit_timeout_to_asyncpg():
    """
    GIVEN DATABASE_URL is set and DB_CONNECT_TIMEOUT_SECONDS is configured
    WHEN _get_db_connection calls asyncpg.connect
    THEN it passes that value as the timeout kwarg -- asyncpg.connect has no
        caller-set timeout otherwise, so an unreachable host (a paused
        container answers no SYN-ACK, rather than refusing) hangs for
        asyncpg's own 60s default per attempt instead of failing fast.
    """
    mock_conn = AsyncMock()
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://good:good@localhost/good",
    ):
        with patch.dict(
            "os.environ",
            {"DB_CONNECT_TIMEOUT_SECONDS": "2.5"},
        ):
            with patch("scrobblescope.cache.asyncpg") as mock_asyncpg:
                mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
                result = await _get_db_connection()
    assert result is mock_conn
    mock_asyncpg.connect.assert_awaited_once_with(
        "postgres://good:good@localhost/good", timeout=2.5
    )


@pytest.mark.asyncio
async def test_get_db_connection_treats_timeout_as_an_ordinary_failure(caplog):
    """
    GIVEN every asyncpg.connect attempt raises asyncio.TimeoutError (what a
        capped, unreachable connection raises once the timeout kwarg fires)
    WHEN _get_db_connection exhausts its retry budget
    THEN it returns None and logs db-down, the same as any other connect
        failure -- a timeout is not a special case the caller must handle.
    """
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://bad:bad@localhost/bad",
    ):
        with patch.dict(
            "os.environ",
            {
                "DB_CONNECT_MAX_ATTEMPTS": "2",
                "DB_CONNECT_BASE_DELAY_SECONDS": "0",
                "DB_CONNECT_TIMEOUT_SECONDS": "1",
            },
        ):
            with (
                patch("scrobblescope.cache.asyncpg") as mock_asyncpg,
                patch("scrobblescope.cache.asyncio.sleep", new_callable=AsyncMock),
            ):
                mock_asyncpg.connect = AsyncMock(side_effect=TimeoutError())
                with caplog.at_level(logging.INFO):
                    result = await _get_db_connection()
    assert result is None
    assert mock_asyncpg.connect.await_count == 2
    assert "db-down" in caplog.text


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


def test_get_job_context_dict_results_are_shallow_copied():
    """get_job_context returns a shallow copy of dict results.

    Adversarial: if the ``elif isinstance(results, dict): results = dict(results)``
    branch were absent, mutating the returned dict would silently corrupt the
    live JOBS entry -- a thread-safety hazard for heatmap jobs whose results
    are stored as dicts rather than lists.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    original = {"username": "testuser", "total_scrobbles": 100, "daily_counts": {}}
    set_job_results(job_id, original)

    ctx = get_job_context(job_id)
    assert ctx is not None
    assert ctx["results"]["total_scrobbles"] == 100

    # Mutate the returned copy -- the JOBS entry must be unchanged.
    ctx["results"]["total_scrobbles"] = 999

    ctx2 = get_job_context(job_id)
    assert ctx2["results"]["total_scrobbles"] == 100


def test_get_job_context_nested_daily_counts_is_isolated():
    """get_job_context isolates the nested daily_counts dict from callers.

    Adversarial: a shallow dict copy leaves daily_counts shared by reference;
    a caller that did ``ctx["results"]["daily_counts"][key] = N`` would
    silently mutate the live JOBS entry.  Closes F-B18-8.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    original = {
        "username": "testuser",
        "total_scrobbles": 5,
        "daily_counts": {"2026-05-01": 3, "2026-05-02": 2},
    }
    set_job_results(job_id, original)

    ctx = get_job_context(job_id)
    assert ctx is not None
    assert ctx["results"]["daily_counts"]["2026-05-01"] == 3

    # Mutate the nested dict through the returned reference.
    ctx["results"]["daily_counts"]["2026-05-01"] = 999
    ctx["results"]["daily_counts"]["2026-05-03"] = 7  # add a new key too

    # A fresh context must observe the original values, not the mutations.
    ctx2 = get_job_context(job_id)
    assert ctx2 is not None
    assert ctx2["results"]["daily_counts"]["2026-05-01"] == 3
    assert "2026-05-03" not in ctx2["results"]["daily_counts"]


def test_set_job_progress_phase_isolation_and_update_modes():
    """set_job_progress copies phase, isolates nested mutation, and supports three modes.

    1. phase=dict copies input dict and isolates both get_job_progress and get_job_context.
    2. Omitted phase preserves existing phase across progress updates.
    3. phase=None explicitly clears the phase.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    phase = {
        "key": "lastfm_fetch",
        "label": "Fetching scrobbles",
        "unit": "page",
        "current": 23,
        "total": 102,
    }
    set_job_progress(job_id, progress=20, message="Fetching scrobbles", phase=phase)
    phase["current"] = 99
    assert get_job_progress(job_id)["phase"]["current"] == 23
    assert get_job_context(job_id)["progress"]["phase"]["current"] == 23

    progress_view = get_job_progress(job_id)
    context_view = get_job_context(job_id)
    progress_view["phase"]["current"] = 77
    context_view["progress"]["phase"]["current"] = 88
    assert get_job_progress(job_id)["phase"]["current"] == 23
    assert get_job_context(job_id)["progress"]["phase"]["current"] == 23

    set_job_progress(job_id, message="Still fetching")
    assert get_job_progress(job_id)["phase"]["key"] == "lastfm_fetch"

    set_job_progress(job_id, phase=None)
    assert "phase" not in get_job_progress(job_id)
    assert "phase" not in get_job_context(job_id)["progress"]


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
