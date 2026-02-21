from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.domain import SpotifyUnavailableError
from scrobblescope.orchestrator import (
    _fetch_and_process,
    background_task,
    process_albums,
)
from scrobblescope.repositories import create_job, get_job_progress
from tests.helpers import TEST_JOB_PARAMS


@pytest.mark.asyncio
async def test_process_albums_cache_hit_skips_spotify():
    """
    GIVEN all albums exist in the DB cache
    WHEN process_albums is called
    THEN it should NOT call fetch_spotify_access_token and should
    build results from cached metadata only.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("radiohead", "ok computer"): {
            "play_count": 50,
            "track_counts": {"paranoid android": 10, "karma police": 8},
            "original_artist": "Radiohead",
            "original_album": "OK Computer",
        }
    }

    mock_cached = {
        ("radiohead", "ok computer"): {
            "spotify_id": "abc123",
            "release_date": "1997-06-16",
            "album_image_url": "https://img.example.com/ok.jpg",
            "track_durations": {"paranoid android": 383, "karma police": 264},
        }
    }

    mock_conn = AsyncMock()
    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value=mock_cached,
        ),
        patch(
            "scrobblescope.orchestrator._batch_persist_metadata", new_callable=AsyncMock
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
        ) as mock_token,
    ):
        results = await process_albums(job_id, filtered, 1997, "playcount", "same")

    mock_token.assert_not_awaited()
    mock_conn.close.assert_awaited_once()

    progress = get_job_progress(job_id)
    assert len(results) == 1
    assert results[0]["spotify_id"] == "abc123"
    assert results[0]["play_time_seconds"] == 383 * 10 + 264 * 8
    assert results[0]["artist"] == "Radiohead"
    assert progress["stats"]["db_cache_enabled"] is True
    assert progress["stats"]["db_cache_lookup_hits"] == 1


@pytest.mark.asyncio
async def test_process_albums_cache_miss_fetches_and_persists():
    """
    GIVEN no albums exist in the DB cache
    WHEN process_albums is called
    THEN it should call Spotify search + detail fetch, build results,
    and persist the new metadata to DB.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"track one": 5},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }

    mock_conn = AsyncMock()
    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "scrobblescope.orchestrator._batch_persist_metadata",
            new_callable=AsyncMock,
        ) as mock_persist,
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=mock_session_ctx,
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value="sp1",
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            return_value={
                "sp1": {
                    "release_date": "2025-01-01",
                    "images": [{"url": "https://img.example.com/a.jpg"}],
                    "tracks": {"items": [{"name": "Track One", "duration_ms": 240000}]},
                }
            },
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    mock_persist.assert_awaited_once()
    persist_rows = mock_persist.call_args[0][1]
    assert len(persist_rows) == 1
    assert persist_rows[0][2] == "sp1"

    progress = get_job_progress(job_id)
    mock_conn.close.assert_awaited_once()
    assert len(results) == 1
    assert results[0]["spotify_id"] == "sp1"
    assert results[0]["album_image"] == "https://img.example.com/a.jpg"
    assert progress["stats"]["db_cache_enabled"] is True
    assert progress["stats"]["db_cache_persisted"] == 1


@pytest.mark.asyncio
async def test_process_albums_db_unavailable_falls_back():
    """
    GIVEN _get_db_connection returns None (no DATABASE_URL)
    WHEN process_albums is called
    THEN it should proceed with full Spotify calls and return results.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"track one": 5},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }

    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=mock_session_ctx,
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value="sp1",
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            return_value={
                "sp1": {
                    "release_date": "2025-01-01",
                    "images": [{"url": "https://img.example.com/a.jpg"}],
                    "tracks": {"items": [{"name": "Track One", "duration_ms": 240000}]},
                }
            },
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    progress = get_job_progress(job_id)
    assert len(results) == 1
    assert results[0]["spotify_id"] == "sp1"
    assert progress["stats"]["db_cache_enabled"] is False
    assert "db_cache_warning" in progress["stats"]


@pytest.mark.asyncio
async def test_process_albums_conn_always_closed():
    """
    GIVEN a DB connection is established but Spotify search raises
    WHEN process_albums is called
    THEN the connection should still be closed in the finally block.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"track one": 5},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }

    mock_conn = AsyncMock()
    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "scrobblescope.orchestrator._batch_persist_metadata", new_callable=AsyncMock
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=mock_session_ctx,
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Spotify exploded"),
        ),
    ):
        with pytest.raises(RuntimeError, match="Spotify exploded"):
            await process_albums(job_id, filtered, 2025, "playcount", "same")

    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_albums_empty_input():
    """
    GIVEN an empty filtered_albums dict
    WHEN process_albums is called
    THEN it should return an empty list and close the connection cleanly.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    mock_conn = AsyncMock()

    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "scrobblescope.orchestrator._batch_persist_metadata", new_callable=AsyncMock
        ),
    ):
        results = await process_albums(job_id, {}, 2025, "playcount", "same")

    assert results == []
    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_albums_all_misses_token_failure_raises():
    """
    GIVEN all albums are cache misses and Spotify token fetch fails
    WHEN process_albums is called
    THEN it should raise SpotifyUnavailableError and close DB connection.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 10,
            "track_counts": {"song": 3},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }

    mock_conn = AsyncMock()
    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with pytest.raises(SpotifyUnavailableError, match="token fetch failed"):
            await process_albums(job_id, filtered, 2025, "playcount", "same")

    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_albums_partial_cache_token_failure_uses_cached_results():
    """
    GIVEN some cache hits and some cache misses
    WHEN Spotify token fetch fails
    THEN process_albums should return cached results and set a partial-data warning.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("radiohead", "ok computer"): {
            "play_count": 50,
            "track_counts": {"paranoid android": 10, "karma police": 8},
            "original_artist": "Radiohead",
            "original_album": "OK Computer",
        },
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"track one": 5},
            "original_artist": "Artist",
            "original_album": "Album",
        },
    }
    mock_cached = {
        ("radiohead", "ok computer"): {
            "spotify_id": "abc123",
            "release_date": "1997-06-16",
            "album_image_url": "https://img.example.com/ok.jpg",
            "track_durations": {"paranoid android": 383, "karma police": 264},
        }
    }

    mock_conn = AsyncMock()
    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value=mock_cached,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_token,
    ):
        results = await process_albums(job_id, filtered, 1997, "playcount", "all")

    progress = get_job_progress(job_id)
    assert len(results) == 1
    assert results[0]["spotify_id"] == "abc123"
    assert "partial_data_warning" in progress["stats"]
    assert "cached albums only" in progress["stats"]["partial_data_warning"]
    assert progress["stats"]["db_cache_enabled"] is True
    mock_token.assert_awaited_once()
    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_and_process_cache_hit_does_not_precheck_spotify():
    """
    GIVEN _fetch_and_process receives albums and process_albums returns results
    WHEN _fetch_and_process runs
    THEN it should not call fetch_spotify_access_token directly.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("radiohead", "ok computer"): {
            "play_count": 50,
            "track_counts": {"paranoid android": 10},
            "original_artist": "Radiohead",
            "original_album": "OK Computer",
        }
    }
    expected_results = [
        {
            "artist": "Radiohead",
            "album": "OK Computer",
            "play_count": 50,
            "play_time": "63 mins, 50 secs",
            "play_time_seconds": 3830,
            "different_songs": 1,
            "release_date": "1997-06-16",
            "album_image": "https://img.example.com/ok.jpg",
            "spotify_id": "abc123",
        }
    ]

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(filtered, {"status": "ok"}),
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
            return_value=expected_results,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
        ) as mock_token,
    ):
        results = await _fetch_and_process(
            job_id, "flounder14", 2025, "playcount", "same"
        )

    progress = get_job_progress(job_id)
    assert results == expected_results
    assert progress["error"] is False
    assert progress["progress"] == 100
    mock_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_and_process_sets_spotify_error_from_process_albums():
    """
    GIVEN process_albums raises SpotifyUnavailableError
    WHEN _fetch_and_process runs
    THEN it should set a classified spotify_unavailable job error.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 10,
            "track_counts": {"song": 3},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(filtered, {"status": "ok"}),
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
            side_effect=SpotifyUnavailableError("Spotify token fetch failed"),
        ),
    ):
        results = await _fetch_and_process(
            job_id, "flounder14", 2025, "playcount", "same"
        )

    progress = get_job_progress(job_id)
    assert results == []
    assert progress["error"] is True
    assert progress["error_code"] == "spotify_unavailable"
    assert progress["error_source"] == "spotify"


def test_background_task_runs_single_event_loop():
    """
    GIVEN a job ID and valid parameters
    WHEN background_task is called
    THEN it should create one event loop, run _fetch_and_process via that loop,
    and NOT spawn a second thread (Batch 3 regression guard).
    """
    job_id = create_job(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task(job_id, "flounder14", 2025, "playcount", "same")

        mock_fp.assert_awaited_once()
        call_args = mock_fp.call_args
        assert call_args[0][0] == job_id
        assert call_args[0][1] == "flounder14"
        mock_release.assert_called_once()


def test_background_task_releases_slot_on_exception():
    """
    GIVEN _fetch_and_process raises an unhandled exception
    WHEN background_task is called
    THEN release_job_slot should still be called in the finally block.
    """
    job_id = create_job(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
            side_effect=RuntimeError("unhandled crash"),
        ),
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task(job_id, "flounder14", 2025, "playcount", "same")

    mock_release.assert_called_once()
