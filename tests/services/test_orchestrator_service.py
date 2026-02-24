import logging
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from scrobblescope.cache import _cleanup_stale_metadata
from scrobblescope.errors import SpotifyUnavailableError
from scrobblescope.orchestrator import (
    _PLAYTIME_ALBUM_CAP,
    _build_results,
    _fetch_and_process,
    _get_user_friendly_reason,
    _matches_release_criteria,
    _run_spotify_batch_detail_phase,
    _run_spotify_search_phase,
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


# =====================================================================
# Adversarial tests for extracted helpers (Batch 11 WP-2)
# =====================================================================


@pytest.mark.parametrize(
    "release_date, expected",
    [
        ("XXXX-01-01", False),  # unparseable year -> ValueError fallback
        ("not-a-date", False),  # fully non-numeric prefix
        ("", False),  # empty string -> guard returns False
        (None, False),  # None -> guard returns False
        ("2025", True),  # year-only string, no dash, matches year=2025
    ],
)
def test_matches_release_criteria_adversarial(release_date, expected):
    """Edge-case inputs must not crash -- they must return False gracefully
    via the ValueError fallback or the empty-string guard.

    The parametrized cases cover:
    - Unparseable year prefix ("XXXX") -> ValueError -> returns False
    - Non-numeric prefix ("not") -> ValueError -> returns False
    - Empty string -> `if not release_date` guard -> returns False
    - None -> same guard -> returns False
    - Year-only string without dash -> succeeds (no split needed)
    """
    result = _matches_release_criteria(release_date, release_scope="same", year=2025)
    assert result is expected


def test_get_user_friendly_reason_adversarial():
    """When release_scope='decade' but decade=None, the function must not
    raise a TypeError on `decade[:3]`.  It should fall through to the
    generic mismatch message instead.

    Also verifies the ValueError branch for unparseable dates.
    """
    # decade=None: the `if release_scope == "decade" and decade:` guard
    # is False, so it falls through to the generic message.
    reason = _get_user_friendly_reason(
        "2020-01-01", release_scope="decade", year=2025, decade=None
    )
    assert "does not match filter" in reason
    assert "2020" in reason

    # Unparseable date -> ValueError branch
    reason_bad = _get_user_friendly_reason("XXXX", release_scope="same", year=2025)
    assert reason_bad == "Unknown release year: XXXX"


@pytest.mark.asyncio
async def test_fetch_spotify_misses_malformed_album_details():
    """When Spotify returns album details missing the 'tracks' key or with
    a None entry, the extraction loop must not raise KeyError or TypeError.

    The `.get('tracks', {}).get('items', [])` chain handles missing keys;
    the `if not album_details: continue` guard handles None entries.
    Both paths must produce zero track_durations (empty dict) rather than
    crashing the pipeline.
    """
    from scrobblescope.orchestrator import _fetch_spotify_misses

    job_id = create_job(TEST_JOB_PARAMS)
    cache_misses = {
        ("artist1", "album1"): {
            "play_count": 10,
            "track_counts": {"song": 3},
            "original_artist": "Artist1",
            "original_album": "Album1",
        },
        ("artist2", "album2"): {
            "play_count": 5,
            "track_counts": {"tune": 2},
            "original_artist": "Artist2",
            "original_album": "Album2",
        },
    }
    cache_hits = {}

    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    # search returns both IDs; batch details returns one with no 'tracks'
    # key and one as None (simulating a deleted album).
    # Use a side_effect function (not list) to ensure ID assignment is
    # deterministic regardless of asyncio.as_completed scheduling order.
    async def _search_by_artist(session, artist, album, token, semaphore=None):
        return {"artist1": "sp1", "artist2": "sp2"}[artist]

    with (
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
            side_effect=_search_by_artist,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            return_value={
                "sp1": {
                    "release_date": "2025-01-01",
                    "images": [{"url": "https://img.example.com/a.jpg"}],
                    # 'tracks' key deliberately missing
                },
                "sp2": None,  # deleted/unavailable album
            },
        ),
    ):
        new_rows = await _fetch_spotify_misses(job_id, cache_misses, cache_hits)

    # sp1 should be promoted with empty track_durations (missing 'tracks')
    assert ("artist1", "album1") in cache_hits
    promoted = cache_hits[("artist1", "album1")]["cached"]
    assert promoted["track_durations"] == {}
    assert promoted["spotify_id"] == "sp1"

    # sp2 (None details) should be skipped entirely -- not promoted
    assert ("artist2", "album2") not in cache_hits

    # Only sp1 should produce a persist row
    assert len(new_rows) == 1
    assert new_rows[0][2] == "sp1"


def test_build_results_zero_playtime_no_division_error():
    """When all albums have zero play_time_seconds and sort_mode='playtime',
    the `or 1` guard in proportion calculation must prevent ZeroDivisionError.

    Also verifies that missing track_durations (None) defaults to an empty
    dict, producing play_time_seconds=0 rather than a TypeError.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    cache_hits = {
        ("artist", "album"): {
            "cached": {
                "spotify_id": "sp1",
                "release_date": "2025-01-01",
                "album_image_url": "https://img.example.com/a.jpg",
                "track_durations": None,  # missing durations
            },
            "original": {
                "play_count": 20,
                "track_counts": {"song a": 5, "song b": 3},
                "original_artist": "Artist",
                "original_album": "Album",
            },
        }
    }

    results = _build_results(
        cache_hits, job_id, year=2025, sort_mode="playtime", release_scope="same"
    )

    assert len(results) == 1
    assert results[0]["play_time_seconds"] == 0
    assert results[0]["play_time"] == "0 secs"
    assert results[0]["play_time_mobile"] == "0s"
    # proportion_of_max uses `or 1` guard: 0 / 1 * 100 = 0.0
    assert results[0]["proportion_of_max"] == 0.0
    assert results[0]["proportion_of_total"] == 0.0


@pytest.mark.asyncio
async def test_fetch_and_process_passes_progress_cb_to_lastfm():
    """
    GIVEN _fetch_and_process is called
    WHEN fetch_top_albums_async invokes progress_cb per page
    THEN set_job_progress maps page progress into the 5%-20% range
    with messages like "Fetching Last.fm page N/T...".

    Arithmetic: pct = 5 + int(15 * pages_done / total_pages)
    For 3 pages: (1,3)->10, (2,3)->15, (3,3)->20.
    """
    from scrobblescope.repositories import set_job_progress as real_set

    job_id = create_job(TEST_JOB_PARAMS)

    async def _invoke_cb(*args, **kwargs):
        """Mock fetch_top_albums_async that invokes progress_cb."""
        cb = kwargs.get("progress_cb")
        if cb:
            cb(1, 3)
            cb(2, 3)
            cb(3, 3)
        return {}, {"status": "ok"}

    progress_calls = []

    def _tracking_set(jid, **kwargs):
        progress_calls.append(kwargs)
        return real_set(jid, **kwargs)

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            side_effect=_invoke_cb,
        ),
        patch(
            "scrobblescope.orchestrator.set_job_progress",
            side_effect=_tracking_set,
        ),
    ):
        await _fetch_and_process(job_id, "testuser", 2025, "playcount", "all")

    # Filter for the page-fetching progress calls
    page_calls = [
        c
        for c in progress_calls
        if "message" in c and "Fetching Last.fm page" in c["message"]
    ]
    assert len(page_calls) == 3
    assert page_calls[0] == {"progress": 10, "message": "Fetching Last.fm page 1/3..."}
    assert page_calls[1] == {"progress": 15, "message": "Fetching Last.fm page 2/3..."}
    assert page_calls[2] == {"progress": 20, "message": "Fetching Last.fm page 3/3..."}


@pytest.mark.asyncio
async def test_fetch_spotify_misses_reports_search_progress():
    """
    GIVEN _fetch_spotify_misses searches for 5 Spotify albums
    WHEN each search completes via asyncio.as_completed
    THEN set_job_progress is called with values in the 20%-40% range
    and messages like "Searching Spotify: N/T albums...".

    Arithmetic: pct = 20 + int(20 * searches_done / total_searches)
    For 5 searches: 24, 28, 32, 36, 40.
    """
    from scrobblescope.orchestrator import _fetch_spotify_misses
    from scrobblescope.repositories import set_job_progress as real_set

    job_id = create_job(TEST_JOB_PARAMS)

    cache_misses = {
        (f"artist{i}", f"album{i}"): {
            "play_count": 10,
            "track_counts": {"song": 3},
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
        }
        for i in range(5)
    }
    cache_hits = {}

    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    # All 5 searches return IDs; batch detail returns minimal data
    spotify_ids = [f"sp{i}" for i in range(5)]

    def _batch_details(session, batch_ids, token, semaphore=None):
        return {
            sid: {
                "release_date": "2025-01-01",
                "images": [{"url": "https://img.example.com/a.jpg"}],
                "tracks": {"items": []},
            }
            for sid in batch_ids
        }

    progress_calls = []

    def _tracking_set(jid, **kwargs):
        progress_calls.append(kwargs)
        return real_set(jid, **kwargs)

    with (
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
            side_effect=spotify_ids,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            side_effect=_batch_details,
        ),
        patch(
            "scrobblescope.orchestrator.set_job_progress",
            side_effect=_tracking_set,
        ),
    ):
        await _fetch_spotify_misses(job_id, cache_misses, cache_hits)

    # Filter for search-phase progress calls
    search_calls = [
        c
        for c in progress_calls
        if "message" in c and "Searching Spotify:" in c["message"]
    ]
    assert len(search_calls) == 5
    # All progress values must be in the 20-40% range
    for sc in search_calls:
        assert 20 <= sc["progress"] <= 40
    # Final search call reaches 40%
    assert search_calls[-1]["progress"] == 40
    # Messages reference the total album count
    assert "/5 albums..." in search_calls[-1]["message"]


@pytest.mark.asyncio
async def test_fetch_spotify_misses_reports_batch_progress():
    """
    GIVEN _fetch_spotify_misses processes 2 batches of Spotify album details
    WHEN each batch completes via asyncio.as_completed
    THEN set_job_progress is called with values in the 40%-60% range
    and messages like "Enriched N/T albums from Spotify...".

    Arithmetic: pct = 40 + int(20 * batches_done / num_batches)
    For 2 batches: batch 1 -> 50, batch 2 -> 60.
    """
    from scrobblescope.orchestrator import _fetch_spotify_misses
    from scrobblescope.repositories import set_job_progress as real_set

    job_id = create_job(TEST_JOB_PARAMS)

    # Build 25 cache misses to produce 2 batches (batch_size=20)
    cache_misses = {
        (f"artist{i}", f"album{i}"): {
            "play_count": 10,
            "track_counts": {"song": 3},
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
        }
        for i in range(25)
    }
    cache_hits = {}

    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    # All 25 searches succeed
    spotify_ids = [f"sp{i}" for i in range(25)]

    # Batch detail responses: batch 1 (20 albums), batch 2 (5 albums)
    def _batch_details(session, batch_ids, token, semaphore=None):
        return {
            sid: {
                "release_date": "2025-01-01",
                "images": [{"url": "https://img.example.com/a.jpg"}],
                "tracks": {"items": []},
            }
            for sid in batch_ids
        }

    progress_calls = []

    def _tracking_set(jid, **kwargs):
        progress_calls.append(kwargs)
        return real_set(jid, **kwargs)

    with (
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
            side_effect=spotify_ids,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            side_effect=_batch_details,
        ),
        patch(
            "scrobblescope.orchestrator.set_job_progress",
            side_effect=_tracking_set,
        ),
    ):
        await _fetch_spotify_misses(job_id, cache_misses, cache_hits)

    # Filter for Spotify enrichment progress calls
    enrich_calls = [
        c
        for c in progress_calls
        if "message" in c and "albums from Spotify" in c["message"]
    ]
    assert len(enrich_calls) == 2
    # Batch 1: 40 + int(20 * 1/2) = 50
    assert enrich_calls[0]["progress"] == 50
    # Batch 2: 40 + int(20 * 2/2) = 60
    assert enrich_calls[1]["progress"] == 60
    # Both messages should reference total album count
    assert "/25 albums from Spotify..." in enrich_calls[0]["message"]
    assert "/25 albums from Spotify..." in enrich_calls[1]["message"]


# ---------------------------------------------------------------------------
# WP-2 adversarial tests for extracted search/batch-detail helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_spotify_search_phase_all_misses_returns_empty_maps():
    """All search_for_spotify_album_id calls return None: both dicts empty,
    every album registered as unmatched."""
    job_id = create_job(TEST_JOB_PARAMS)
    cache_misses = {
        ("artist1", "album1"): {
            "original_artist": "Artist1",
            "original_album": "Album1",
            "play_count": 10,
            "track_counts": {"t1": 5},
        },
        ("artist2", "album2"): {
            "original_artist": "Artist2",
            "original_album": "Album2",
            "play_count": 8,
            "track_counts": {"t2": 4},
        },
    }
    session = AsyncMock()
    semaphore = __import__("asyncio").Semaphore(5)

    with (
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("scrobblescope.orchestrator.set_job_progress"),
        patch("scrobblescope.orchestrator.add_job_unmatched") as mock_unmatched,
    ):
        id_to_key, id_to_data = await _run_spotify_search_phase(
            job_id, session, cache_misses, "fake_token", semaphore
        )

    assert id_to_key == {}
    assert id_to_data == {}
    assert mock_unmatched.call_count == 2


@pytest.mark.asyncio
async def test_run_spotify_batch_detail_phase_empty_id_list_skips_api_call():
    """valid_spotify_ids=[]: fetch_spotify_album_details_batch not called."""
    job_id = create_job(TEST_JOB_PARAMS)
    with (
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="token",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=AsyncMock(),
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
        ) as mock_batch,
        patch("scrobblescope.orchestrator.set_job_progress"),
        patch("scrobblescope.orchestrator.add_job_unmatched"),
    ):
        from scrobblescope.orchestrator import _fetch_spotify_misses

        result = await _fetch_spotify_misses(
            job_id,
            {
                ("a", "b"): {
                    "original_artist": "A",
                    "original_album": "B",
                    "play_count": 5,
                    "track_counts": {},
                }
            },
            {},
        )

    assert result == []
    mock_batch.assert_not_called()


@pytest.mark.asyncio
async def test_run_spotify_search_phase_progress_stays_in_20_to_40_range():
    """All set_job_progress calls from search phase have progress in [20, 40]."""
    job_id = create_job(TEST_JOB_PARAMS)
    cache_misses = {
        (f"artist{i}", f"album{i}"): {
            "original_artist": f"Artist{i}",
            "original_album": f"Album{i}",
            "play_count": 10,
            "track_counts": {f"t{i}": 5},
        }
        for i in range(5)
    }
    session = AsyncMock()
    semaphore = __import__("asyncio").Semaphore(5)

    progress_values = []

    def capture_progress(job_id, **kwargs):
        if "progress" in kwargs:
            progress_values.append(kwargs["progress"])

    with (
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value="some_id",
        ),
        patch(
            "scrobblescope.orchestrator.set_job_progress",
            side_effect=capture_progress,
        ),
    ):
        await _run_spotify_search_phase(
            job_id, session, cache_misses, "fake_token", semaphore
        )

    assert len(progress_values) == 5
    for pct in progress_values:
        assert 20 <= pct <= 40, f"Progress {pct} outside [20, 40] range"
