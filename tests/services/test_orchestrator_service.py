import logging
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from scrobblescope.cache import _cleanup_stale_metadata
from scrobblescope.errors import SpotifyUnavailableError
from scrobblescope.orchestrator import (
    _PLAYTIME_ALBUM_CAP,
    _fetch_and_process,
    background_task,
    process_albums,
)
from scrobblescope.repositories import JOBS, create_job, get_job_progress, jobs_lock
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
    assert progress is not None
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
    assert progress is not None
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
    assert progress is not None
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
    assert progress is not None
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
    THEN it must store results via set_job_results (not just return them), set job
    progress to 100, and not call fetch_spotify_access_token directly.

    The critical side-effect assertion is that JOBS[job_id]["results"] equals the
    processed list.  background_task ignores _fetch_and_process's return value and
    relies entirely on the stored job state, so a regression that removes the
    set_job_results call would break production but would not be caught by a
    return-value-only assertion.
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
    assert progress is not None
    assert results == expected_results
    assert progress["error"] is False
    assert progress["progress"] == 100
    mock_token.assert_not_awaited()
    # Verify set_job_results was called: background_task reads job state, not the
    # return value.  If this assertion fails, results are returned but not stored.
    with jobs_lock:
        assert JOBS[job_id]["results"] == expected_results


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
    assert progress is not None
    assert results == []
    assert progress["error"] is True
    assert progress["error_code"] == "spotify_unavailable"
    assert progress["error_source"] == "spotify"


@pytest.mark.asyncio
async def test_cleanup_stale_metadata_issues_delete():
    """
    GIVEN a live DB connection
    WHEN _cleanup_stale_metadata is called
    THEN it should execute a DELETE statement parameterised with the TTL value.
    """
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = "DELETE 3"

    await _cleanup_stale_metadata(mock_conn)

    mock_conn.execute.assert_awaited_once()
    sql, ttl = mock_conn.execute.call_args[0]
    assert "DELETE FROM spotify_cache" in sql
    assert "updated_at" in sql
    assert isinstance(ttl, int) and ttl > 0


@pytest.mark.asyncio
async def test_cleanup_stale_metadata_nonfatal(caplog):
    """
    GIVEN conn.execute raises an exception
    WHEN _cleanup_stale_metadata is called
    THEN no exception should propagate and a warning must be logged.

    Previously this test had no assertion at all: it passed vacuously and would
    have passed even if the function body was empty.  The logging.warning call is
    the only observable production side-effect when cleanup fails, so asserting on
    it is the minimum meaningful check for this path.
    """
    import logging

    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = RuntimeError("DB gone away")

    with caplog.at_level(logging.WARNING):
        await _cleanup_stale_metadata(mock_conn)  # must not raise

    assert "Stale cache cleanup failed" in caplog.text


@pytest.mark.asyncio
async def test_playcount_limit_slices_before_spotify_when_scope_is_all():
    """
    GIVEN filtered_albums has 5 entries, limit_results="2", sort_mode="playcount",
    and release_scope="all"
    WHEN _fetch_and_process runs
    THEN process_albums should receive at most 2 albums (pre-sliced by play_count)
    because release_scope="all" means no downstream filter can discard albums from
    the top-N, so the optimisation is safe.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        (f"artist{i}", f"album{i}"): {
            "play_count": i * 10,
            "track_counts": {f"track{i}": i},
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
        }
        for i in range(1, 6)  # 5 albums with play_counts 10..50
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
            return_value=[],
        ) as mock_process,
    ):
        await _fetch_and_process(
            job_id,
            "testuser",
            2025,
            "playcount",
            "all",
            limit_results="2",
        )

    called_albums = mock_process.call_args[0][1]
    assert len(called_albums) <= 2, (
        "process_albums should receive at most 2 albums when release_scope='all' "
        "and limit_results='2': the optimisation is safe with no release filter."
    )
    assert ("artist5", "album5") in called_albums
    assert ("artist4", "album4") in called_albums


@pytest.mark.asyncio
async def test_playcount_limit_not_presliced_with_scoped_release():
    """
    GIVEN filtered_albums has 5 entries, limit_results="2", sort_mode="playcount",
    and release_scope="same" (a release-year filter is active)
    WHEN _fetch_and_process runs
    THEN process_albums should receive all 5 albums -- NOT just 2.

    Pre-slicing is unsafe when release_scope != "all": albums ranked #3-#5 by raw
    play_count might be the only ones matching the release-year filter. Discarding
    them early would silently return fewer results than exist without any warning.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        (f"artist{i}", f"album{i}"): {
            "play_count": i * 10,
            "track_counts": {f"track{i}": i},
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
        }
        for i in range(1, 6)  # 5 albums with play_counts 10..50
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
            return_value=[],
        ) as mock_process,
    ):
        await _fetch_and_process(
            job_id,
            "testuser",
            2025,
            "playcount",
            "same",
            limit_results="2",
        )

    called_albums = mock_process.call_args[0][1]
    assert len(called_albums) == 5, (
        "All 5 albums must reach process_albums when release_scope='same': "
        "the release-year filter inside process_albums may keep albums ranked "
        "outside the top-2 by raw play_count, so pre-slicing is forbidden."
    )


@pytest.mark.asyncio
async def test_playtime_limit_does_not_preslice():
    """
    GIVEN filtered_albums has 5 entries and limit_results="2" with sort_mode="playtime"
    WHEN _fetch_and_process runs
    THEN process_albums should receive all 5 albums because playtime ranking requires
    Spotify track duration data and cannot be determined before the Spotify fetch.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        (f"artist{i}", f"album{i}"): {
            "play_count": i * 10,
            "track_counts": {f"track{i}": i},
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
        }
        for i in range(1, 6)  # 5 albums
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
            return_value=[],
        ) as mock_process,
    ):
        await _fetch_and_process(
            job_id,
            "testuser",
            2025,
            "playtime",
            "same",
            limit_results="2",
        )

    called_albums = mock_process.call_args[0][1]
    assert len(called_albums) == 5, (
        "process_albums should receive all albums for playtime sort -- "
        "pre-slicing is impossible without Spotify track duration data."
    )


@pytest.mark.asyncio
async def test_playtime_cap_fires_and_warns_when_album_count_exceeds_limit(caplog):
    """
    GIVEN filtered_albums has _PLAYTIME_ALBUM_CAP + 1 entries and sort_mode="playtime"
    WHEN _fetch_and_process runs
    THEN process_albums should receive exactly _PLAYTIME_ALBUM_CAP albums (the highest
    by raw play_count) and a WARNING must be logged identifying the cap as the cause.

    The cap is the only protection against unbounded Spotify API load for playtime
    sorts. A regression that removes it would make the test fail on the album count
    assertion; a regression that silences the log would fail on the caplog assertion.
    """
    over_limit = _PLAYTIME_ALBUM_CAP + 1
    filtered = {
        (f"artist{i}", f"album{i}"): {
            "play_count": i,
            "track_counts": {f"track{i}": 1},
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
        }
        for i in range(1, over_limit + 1)
    }
    job_id = create_job(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(filtered, {"status": "ok"}),
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_process,
        caplog.at_level(logging.WARNING),
    ):
        await _fetch_and_process(job_id, "testuser", 2025, "playtime", "all")

    called_albums = mock_process.call_args[0][1]
    assert len(called_albums) == _PLAYTIME_ALBUM_CAP, (
        f"process_albums should receive exactly {_PLAYTIME_ALBUM_CAP} albums "
        f"when the input exceeds the playtime cap, got {len(called_albums)}"
    )
    # The cap should keep the highest play_count entries.
    assert (f"artist{over_limit}", f"album{over_limit}") in called_albums
    assert ("artist1", "album1") not in called_albums
    assert "Playtime album cap applied" in caplog.text


@pytest.mark.asyncio
async def test_playtime_cap_does_not_fire_below_limit():
    """
    GIVEN filtered_albums has fewer than _PLAYTIME_ALBUM_CAP entries
    WHEN _fetch_and_process runs with sort_mode="playtime"
    THEN process_albums should receive all albums unchanged -- the cap must not
    interfere with normal-sized requests.
    """
    filtered = {
        (f"artist{i}", f"album{i}"): {
            "play_count": i * 10,
            "track_counts": {f"track{i}": i},
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
        }
        for i in range(1, 6)  # well below the cap
    }
    job_id = create_job(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(filtered, {"status": "ok"}),
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_process,
    ):
        await _fetch_and_process(job_id, "testuser", 2025, "playtime", "all")

    called_albums = mock_process.call_args[0][1]
    assert len(called_albums) == 5


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
