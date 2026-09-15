from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.enrichment import AlbumMetadata
from scrobblescope.errors import SpotifyUnavailableError
from scrobblescope.orchestrator import process_albums
from scrobblescope.repositories import (
    create_job,
    get_job_context,
    get_job_progress,
    get_job_unmatched,
)
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
async def test_process_albums_applies_cached_original_release_before_filtering():
    """A normal run must forward cached corrections into result filtering.

    A 1977 original cached against a provider's 2011 reissue date is excluded
    from a 2011 filter, and the unmatched record preserves both dates. This
    guards the Task 8 seam between ``process_albums`` and ``_build_results``.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    album_key = ("fleetwood mac", "rumours")
    filtered = {
        album_key: {
            "play_count": 50,
            "track_counts": {"dreams": 10},
            "original_artist": "Fleetwood Mac",
            "original_album": "Rumours",
        }
    }
    cached_metadata = {
        album_key: {
            "spotify_id": "sp-rumours",
            "release_date": "2011-01-31",
            "album_image_url": "https://img.example.com/rumours.jpg",
            "track_durations": {"dreams": 257},
        }
    }
    cached_original_release = {
        album_key: {
            "mb_release_group": "mbid-rumours",
            "original_release": "1977-02-04",
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
            return_value=cached_metadata,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_original_release",
            new_callable=AsyncMock,
            return_value=cached_original_release,
        ) as mock_original_lookup,
        patch(
            "scrobblescope.orchestrator._batch_persist_metadata", new_callable=AsyncMock
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
        ) as mock_token,
    ):
        results = await process_albums(job_id, filtered, 2011, "playcount", "same")

    assert results == []
    mock_token.assert_not_awaited()
    mock_original_lookup.assert_awaited_once_with(mock_conn, [album_key])
    mock_conn.close.assert_awaited_once()
    unmatched = get_job_unmatched(job_id)
    assert unmatched["fleetwood mac|rumours"]["reason"] == (
        "First released in 1977, not 2011"
    )
    assert unmatched["fleetwood mac|rumours"]["provider_release_date"] == ("2011-01-31")


@pytest.mark.asyncio
async def test_process_albums_records_provider_date_on_an_uncorrected_exclusion():
    """An album excluded on the provider's own date still records that date.

    The correction worker (Task 9) picks its move-in candidates out of
    ``job["unmatched"]`` by comparing each entry's provider year against the
    target window, so the date has to be there even when no correction was
    applied -- an exclusion with no cached correction is exactly the case the
    worker exists to resolve.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    album_key = ("fleetwood mac", "rumours")
    filtered = {
        album_key: {
            "play_count": 50,
            "track_counts": {"dreams": 10},
            "original_artist": "Fleetwood Mac",
            "original_album": "Rumours",
        }
    }
    cached_metadata = {
        album_key: {
            "spotify_id": "sp-rumours",
            "release_date": "2011-01-31",
            "album_image_url": "https://img.example.com/rumours.jpg",
            "track_durations": {"dreams": 257},
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
            return_value=cached_metadata,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_original_release",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "scrobblescope.orchestrator._batch_persist_metadata", new_callable=AsyncMock
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    assert results == []
    entry = get_job_unmatched(job_id)["fleetwood mac|rumours"]
    assert entry["reason"] == "Released in 2011 instead of 2025"
    assert entry["provider_release_date"] == "2011-01-31"


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
    GIVEN all albums are cache misses, Spotify token fetch fails, and
    Deezer (Batch 22 WP-1 Task 5's fallback) also cannot match
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
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
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
    THEN process_albums tries Deezer for the misses (Batch 22 WP-1 Task 5),
    returns cached results plus whatever Deezer found, and sets a
    partial-data warning noting the Deezer fallback.
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
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        results = await process_albums(job_id, filtered, 1997, "playcount", "all")

    progress = get_job_progress(job_id)
    assert progress is not None
    assert len(results) == 1
    assert results[0]["spotify_id"] == "abc123"
    assert "partial_data_warning" in progress["stats"]
    assert "Deezer" in progress["stats"]["partial_data_warning"]
    assert progress["stats"]["db_cache_enabled"] is True
    mock_token.assert_awaited_once()
    mock_conn.close.assert_awaited_once()


###############################################################################
# Deezer fallback (Batch 22 WP-1 Task 5)                                    #
###############################################################################


def _session_ctx():
    mock_session = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


@pytest.mark.asyncio
async def test_process_albums_deezer_not_called_when_spotify_matches_everything():
    """
    GIVEN Spotify search+detail matches every album
    WHEN process_albums runs
    THEN Deezer is never called.
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
            return_value=_session_ctx(),
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
                    "tracks": {"items": []},
                }
            },
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            side_effect=AssertionError(
                "Deezer must not be called when Spotify matched everything"
            ),
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    assert len(results) == 1
    assert results[0]["provider"] == "spotify"
    assert results[0]["album_url"] == "https://open.spotify.com/album/sp1"


@pytest.mark.asyncio
async def test_process_albums_deezer_fallback_for_spotify_misses():
    """
    GIVEN Spotify finds one of two albums and Deezer finds the other
    WHEN process_albums runs
    THEN Deezer is asked for exactly the miss, and its match lands in
    results with provider == "deezer" and a Deezer album_url.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist1", "album1"): {
            "play_count": 20,
            "track_counts": {"t1": 5},
            "original_artist": "Artist1",
            "original_album": "Album1",
        },
        ("artist2", "album2"): {
            "play_count": 10,
            "track_counts": {"t2": 3},
            "original_artist": "Artist2",
            "original_album": "Album2",
        },
    }
    mock_conn = AsyncMock()

    async def _search_spotify(session, artist, album, token, semaphore=None):
        return "sp1" if artist == "artist1" else None

    deezer_search_calls = []

    async def _search_deezer(session, artist, album):
        deezer_search_calls.append((artist, album))
        return "dz1"

    async def _fetch_deezer(session, album_id):
        return AlbumMetadata(
            provider="deezer",
            album_id="dz1",
            url="https://www.deezer.com/album/dz1",
            release_date="2025-02-02",
            image_url="https://cdn.example/dz.jpg",
            track_durations={"t2": 200},
        )

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
            return_value=_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            side_effect=_search_spotify,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            return_value={
                "sp1": {
                    "release_date": "2025-01-01",
                    "images": [{"url": "https://img.example.com/a.jpg"}],
                    "tracks": {"items": []},
                }
            },
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            side_effect=_search_deezer,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_deezer_album",
            new_callable=AsyncMock,
            side_effect=_fetch_deezer,
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    assert deezer_search_calls == [("artist2", "album2")]
    assert len(results) == 2
    deezer_result = next(r for r in results if r["artist"] == "Artist2")
    assert deezer_result["provider"] == "deezer"
    assert deezer_result["album_url"] == "https://www.deezer.com/album/dz1"
    spotify_result = next(r for r in results if r["artist"] == "Artist1")
    assert spotify_result["provider"] == "spotify"


@pytest.mark.asyncio
async def test_process_albums_neither_provider_matches_registers_unmatched():
    """
    GIVEN neither Spotify nor Deezer can find an album
    WHEN process_albums runs
    THEN one unmatched entry is registered with reason_code
    "no_spotify_match" and reason text "No match on Spotify or Deezer".
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"t1": 5},
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
            "scrobblescope.orchestrator._batch_persist_metadata", new_callable=AsyncMock
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    assert results == []
    ctx = get_job_context(job_id)
    unmatched = ctx["unmatched"]
    assert len(unmatched) == 1
    entry = next(iter(unmatched.values()))
    assert entry["reason_code"] == "no_spotify_match"
    assert entry["reason"] == "No match on Spotify or Deezer"


@pytest.mark.asyncio
async def test_process_albums_deezer_only_succeeds_when_no_spotify_token():
    """
    GIVEN no Spotify token and an empty DB cache
    WHEN process_albums runs and Deezer can enrich the album
    THEN the job succeeds using Deezer alone -- no exception raised.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"t1": 5},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }
    mock_conn = AsyncMock()

    async def _fetch_deezer(session, album_id):
        return AlbumMetadata(
            provider="deezer",
            album_id="dz1",
            url="https://www.deezer.com/album/dz1",
            release_date="2025-02-02",
            image_url=None,
            track_durations={"t1": 200},
        )

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
            return_value=None,
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value="dz1",
        ),
        patch(
            "scrobblescope.orchestrator.fetch_deezer_album",
            new_callable=AsyncMock,
            side_effect=_fetch_deezer,
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    assert len(results) == 1
    assert results[0]["provider"] == "deezer"


@pytest.mark.asyncio
async def test_process_albums_raises_when_no_token_and_deezer_also_fails():
    """
    GIVEN no Spotify token, an empty DB cache, and Deezer cannot match either
    WHEN process_albums runs
    THEN SpotifyUnavailableError is raised.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"t1": 5},
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
            "scrobblescope.orchestrator._batch_persist_metadata", new_callable=AsyncMock
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value=None,
        ),
        pytest.raises(SpotifyUnavailableError),
    ):
        await process_albums(job_id, filtered, 2025, "playcount", "same")


@pytest.mark.asyncio
async def test_process_albums_deezer_row_persists_provider_fields():
    """
    GIVEN Spotify misses an album and Deezer finds it
    WHEN process_albums persists new metadata
    THEN the row carries provider, provider_album_id, and provider_url,
    with spotify_id left None per the Task 2 cache-column contract.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"t1": 5},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }
    mock_conn = AsyncMock()

    async def _fetch_deezer(session, album_id):
        return AlbumMetadata(
            provider="deezer",
            album_id="dz1",
            url="https://www.deezer.com/album/dz1",
            release_date="2025-02-02",
            image_url="https://cdn.example/dz.jpg",
            track_durations={"t1": 200},
        )

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
        ) as mock_persist,
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value="dz1",
        ),
        patch(
            "scrobblescope.orchestrator.fetch_deezer_album",
            new_callable=AsyncMock,
            side_effect=_fetch_deezer,
        ),
    ):
        await process_albums(job_id, filtered, 2025, "playcount", "same")

    mock_persist.assert_awaited_once()
    rows = mock_persist.call_args[0][1]
    assert len(rows) == 1
    row = rows[0]
    assert row[2] is None  # spotify_id
    assert row[6] == "deezer"
    assert row[7] == "dz1"
    assert row[8] == "https://www.deezer.com/album/dz1"
