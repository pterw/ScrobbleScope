import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.cache import _cleanup_stale_metadata
from scrobblescope.orchestrator import (
    _run_spotify_batch_detail_phase,
    _run_spotify_search_phase,
)
from scrobblescope.repositories import create_job
from scrobblescope.repositories import set_job_progress as real_set
from tests.helpers import TEST_JOB_PARAMS


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
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = RuntimeError("DB gone away")

    with caplog.at_level(logging.WARNING):
        await _cleanup_stale_metadata(mock_conn)  # must not raise

    assert "Stale cache cleanup failed" in caplog.text


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
    semaphore = asyncio.Semaphore(5)

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
    from scrobblescope.orchestrator import _fetch_spotify_misses

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
    semaphore = asyncio.Semaphore(5)

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
