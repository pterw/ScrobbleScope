import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from scrobblescope import jobs
from scrobblescope.cache import _cleanup_stale_metadata
from scrobblescope.errors import (
    ProviderError,
    SpotifyUnavailableError,
    classify_exception_to_error_code,
)
from scrobblescope.orchestrator import _run_spotify_search_phase
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

    job_id = jobs.create(TEST_JOB_PARAMS)
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
        # sp2's detail fetch failed, so Batch 22 WP-1 Task 5's Deezer
        # fallback gets a turn on ("artist2", "album2"); a clean miss keeps
        # this test about the Spotify malformed-details path, not Deezer's.
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value=None,
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
async def test_batch_detail_fallback_is_logged_once_per_job(caplog):
    """
    GIVEN every Get Several Albums batch in a job falls back to single-album
        calls (F-B21-59)
    WHEN _run_spotify_batch_detail_phase runs three batches
    THEN one warning names the fallback and its status, not one per batch.
    """
    from scrobblescope.orchestrator import _run_spotify_batch_detail_phase

    job_id = jobs.create(TEST_JOB_PARAMS)
    ids = [f"sp{i}" for i in range(45)]  # 3 batches of up to 20

    async def _fallback_every_batch(
        session, batch_ids, token, semaphore=None, on_fallback=None
    ):
        on_fallback(403)
        return {}

    with (
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            side_effect=_fallback_every_batch,
        ),
        caplog.at_level(logging.WARNING),
    ):
        await _run_spotify_batch_detail_phase(
            job_id, MagicMock(), ids, "tok", {}, {}, {}
        )

    fallback_lines = [
        record for record in caplog.records if "single-album" in record.getMessage()
    ]
    assert len(fallback_lines) == 1
    assert "403" in fallback_lines[0].getMessage()


@pytest.mark.asyncio
async def test_fetch_spotify_misses_reports_search_progress():
    """
    GIVEN _fetch_spotify_misses searches for 5 Spotify albums
    WHEN each search completes via asyncio.as_completed
    THEN the job advances with values in the 20%-40% range
    and messages like "Searching Spotify: N/T albums...".

    Arithmetic: pct = 20 + int(20 * searches_done / total_searches)
    For 5 searches: 24, 28, 32, 36, 40.
    """
    from scrobblescope.orchestrator import _fetch_spotify_misses

    job_id = jobs.create(TEST_JOB_PARAMS)

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

    def _batch_details(session, batch_ids, token, semaphore=None, on_fallback=None):
        return {
            sid: {
                "release_date": "2025-01-01",
                "images": [{"url": "https://img.example.com/a.jpg"}],
                "tracks": {"items": []},
            }
            for sid in batch_ids
        }

    progress_calls = []

    real_advance = jobs.advance

    def _tracking_advance(jid, percent, message, phase=None):
        progress_calls.append({"progress": percent, "message": message, "phase": phase})
        return real_advance(jid, percent, message, phase=phase)

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
            "scrobblescope.jobs.advance",
            side_effect=_tracking_advance,
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
    for idx, sc in enumerate(search_calls, start=1):
        assert sc.get("phase") == {
            "key": "spotify_search",
            "label": "Searching Spotify",
            "unit": "album",
            "current": idx,
            "total": 5,
        }


@pytest.mark.asyncio
async def test_fetch_spotify_misses_reports_batch_progress():
    """
    GIVEN _fetch_spotify_misses processes 2 batches of Spotify album details
    WHEN each batch completes via asyncio.as_completed
    THEN the job advances with values in the 40%-60% range
    and messages like "Enriched N/T albums from Spotify...".

    Arithmetic: pct = 40 + int(20 * batches_done / num_batches)
    For 2 batches: batch 1 -> 50, batch 2 -> 60.
    """
    from scrobblescope.orchestrator import _fetch_spotify_misses

    job_id = jobs.create(TEST_JOB_PARAMS)

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
    def _batch_details(session, batch_ids, token, semaphore=None, on_fallback=None):
        return {
            sid: {
                "release_date": "2025-01-01",
                "images": [{"url": "https://img.example.com/a.jpg"}],
                "tracks": {"items": []},
            }
            for sid in batch_ids
        }

    progress_calls = []

    real_advance = jobs.advance

    def _tracking_advance(jid, percent, message, phase=None):
        progress_calls.append({"progress": percent, "message": message, "phase": phase})
        return real_advance(jid, percent, message, phase=phase)

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
            "scrobblescope.jobs.advance",
            side_effect=_tracking_advance,
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
    for idx, bc in enumerate(enrich_calls, start=1):
        assert bc.get("phase") == {
            "key": "spotify_details",
            "label": "Fetching Spotify details",
            "unit": "batch",
            "current": idx,
            "total": 2,
        }


# ---------------------------------------------------------------------------
# WP-2 adversarial tests for extracted search/batch-detail helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_spotify_search_phase_all_misses_returns_empty_maps():
    """All search_for_spotify_album_id calls return None: both id maps are
    empty and every key comes back in search_miss_keys. Batch 22 WP-1
    Task 5: the search phase no longer registers unmatched itself -- Deezer
    gets a fallback attempt first, so the caller owns that decision."""
    job_id = jobs.create(TEST_JOB_PARAMS)
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
        patch("scrobblescope.jobs.advance"),
        patch("scrobblescope.jobs.record_unmatched") as mock_unmatched,
    ):
        (
            id_to_key,
            id_to_data,
            search_miss_keys,
            unanswered_keys,
        ) = await _run_spotify_search_phase(
            job_id, session, cache_misses, "fake_token", semaphore
        )

    assert id_to_key == {}
    assert id_to_data == {}
    assert search_miss_keys == {("artist1", "album1"), ("artist2", "album2")}
    assert unanswered_keys == set()
    mock_unmatched.assert_not_called()


@pytest.mark.asyncio
async def test_run_spotify_batch_detail_phase_empty_id_list_skips_api_call():
    """valid_spotify_ids=[]: fetch_spotify_album_details_batch not called.
    Batch 22 WP-1 Task 5: the search miss now falls through to a Deezer
    attempt rather than returning immediately, so Deezer is mocked too."""
    from scrobblescope.orchestrator import _fetch_spotify_misses

    job_id = jobs.create(TEST_JOB_PARAMS)
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
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("scrobblescope.jobs.advance"),
        patch("scrobblescope.jobs.record_unmatched"),
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
    """All advance calls from the search phase have progress in [20, 40]."""
    job_id = jobs.create(TEST_JOB_PARAMS)
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

    def capture_progress(job_id, percent, message, phase=None):
        progress_values.append(percent)

    with (
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value="some_id",
        ),
        patch(
            "scrobblescope.jobs.advance",
            side_effect=capture_progress,
        ),
    ):
        await _run_spotify_search_phase(
            job_id, session, cache_misses, "fake_token", semaphore
        )

    assert len(progress_values) == 5
    for pct in progress_values:
        assert 20 <= pct <= 40, f"Progress {pct} outside [20, 40] range"


@pytest.mark.asyncio
async def test_deezer_fallback_cancels_and_drains_siblings_when_one_album_raises():
    """
    GIVEN one album's Deezer enrichment raises while its siblings are in flight
    WHEN the fallback phase runs
    THEN the exception propagates only after every sibling has been cancelled
    and settled, so none is left running on a session about to close.
    """
    from scrobblescope.orchestrator._deezer_fallback import _run_deezer_fallback_phase

    settled = []

    async def search(session, artist, album):
        if artist == "bad":
            raise TypeError("boom")
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            settled.append(artist)
            raise

    misses = {(a, "alb"): {} for a in ("bad", "s1", "s2", "s3")}
    with (
        patch("scrobblescope.orchestrator.search_deezer_album", side_effect=search),
        patch("scrobblescope.jobs.advance"),
    ):
        with pytest.raises(TypeError, match="boom"):
            await _run_deezer_fallback_phase("job", MagicMock(), misses, {})

    assert sorted(settled) == ["s1", "s2", "s3"]


@pytest.mark.asyncio
async def test_deezer_fallback_reports_progress_inside_its_band():
    """
    GIVEN four albums the Deezer fallback checks
    WHEN each check completes
    THEN the job advances through the 60%-75% band with the Deezer phase
    payload: 60 + int(15 * done / 4) is 63, 67, 71, 75.
    """
    from scrobblescope.orchestrator._deezer_fallback import _run_deezer_fallback_phase

    job_id = jobs.create(TEST_JOB_PARAMS)
    misses = {
        (f"artist{i}", "alb"): {
            "original_artist": f"Artist{i}",
            "original_album": "Alb",
            "play_count": 1,
        }
        for i in range(4)
    }
    seen = []
    real_advance = jobs.advance

    def tracking_advance(jid, percent, message, phase=None):
        seen.append((percent, message, phase))
        return real_advance(jid, percent, message, phase=phase)

    with (
        patch(
            "scrobblescope.orchestrator.search_deezer_album",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("scrobblescope.jobs.advance", side_effect=tracking_advance),
    ):
        await _run_deezer_fallback_phase(job_id, MagicMock(), misses, {})

    assert [percent for percent, _, _ in seen] == [63, 67, 71, 75]
    assert seen[-1][1] == "Checking Deezer: 4/4 albums..."
    assert seen[-1][2] == {
        "key": "deezer_fallback",
        "label": "Checking Deezer",
        "unit": "album",
        "current": 4,
        "total": 4,
    }


@pytest.mark.asyncio
async def test_spotify_search_unanswered_album_does_not_cancel_its_siblings():
    """
    GIVEN one album's Spotify search cannot be answered (ProviderError) while
    its siblings find an id and a miss
    WHEN the search phase runs
    THEN the siblings complete normally and only the unanswered album comes
    back in ``unanswered_keys``, neither found nor a miss: one bad album
    cannot block an account.
    """

    async def search(session, artist, album, token, semaphore=None):
        if artist == "bad":
            raise ProviderError("spotify", "unavailable")
        return "sp-1" if artist == "hit" else None

    job_id = jobs.create(TEST_JOB_PARAMS)
    misses = {(a, "alb"): {} for a in ("bad", "hit", "miss")}
    with patch(
        "scrobblescope.orchestrator.search_for_spotify_album_id", side_effect=search
    ):
        (
            id_to_key,
            _id_to_data,
            miss_keys,
            unanswered_keys,
        ) = await _run_spotify_search_phase(
            job_id, MagicMock(), misses, "tok", asyncio.Semaphore(5)
        )

    assert id_to_key == {"sp-1": ("hit", "alb")}
    assert miss_keys == {("miss", "alb")}
    assert unanswered_keys == {("bad", "alb")}


@pytest.mark.asyncio
async def test_spotify_search_unexpected_error_cancels_siblings_and_propagates():
    """
    GIVEN one album's search raises something that is not a provider failure
    (our bug) while its siblings are in flight
    WHEN the search phase runs
    THEN the error propagates after every sibling has been cancelled and
    settled, so nothing outlives the session and the job fails as ours.
    """
    settled = []

    async def search(session, artist, album, token, semaphore=None):
        if artist == "bad":
            raise KeyError("our bug")
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            settled.append(artist)
            raise

    job_id = jobs.create(TEST_JOB_PARAMS)
    misses = {(a, "alb"): {} for a in ("bad", "s1", "s2")}
    with patch(
        "scrobblescope.orchestrator.search_for_spotify_album_id", side_effect=search
    ):
        with pytest.raises(KeyError):
            await _run_spotify_search_phase(
                job_id, MagicMock(), misses, "tok", asyncio.Semaphore(5)
            )

    assert sorted(settled) == ["s1", "s2"]


@pytest.mark.asyncio
async def test_deezer_throttling_degrades_and_records_the_album_as_unavailable():
    """
    GIVEN Deezer is throttled for one album and matches another
    WHEN the Deezer fallback phase runs
    THEN the matched album is enriched, the throttled one is listed as
    "provider unavailable" (never "No match on Spotify or Deezer"), the job
    carries a partial-data warning and is not in error (Codex 4140219720;
    enrichment never fails the job).
    """
    from scrobblescope.orchestrator._deezer_fallback import _run_deezer_fallback_phase

    job_id = jobs.create(TEST_JOB_PARAMS)
    data = {"original_artist": "A", "original_album": "B", "play_count": 3}
    misses = {("throttled", "alb"): dict(data), ("found", "alb"): dict(data)}
    metadata = MagicMock(
        release_date="2020-01-01",
        image_url="img",
        track_durations={"t": 1},
        provider="deezer",
        album_id="9",
        url="u",
    )
    metadata.as_cache_row.return_value = ("found", "alb")

    async def search(session, artist, album):
        if artist == "throttled":
            raise ProviderError("deezer", "rate_limited")
        return 9

    cache_hits = {}
    with (
        patch("scrobblescope.orchestrator.search_deezer_album", side_effect=search),
        patch(
            "scrobblescope.orchestrator.fetch_deezer_album",
            new_callable=AsyncMock,
            return_value=metadata,
        ),
    ):
        rows = await _run_deezer_fallback_phase(job_id, MagicMock(), misses, cache_hits)

    assert rows == [("found", "alb")]
    assert list(cache_hits) == [("found", "alb")]
    unmatched = jobs.unmatched(job_id)
    assert [v["reason_code"] for v in unmatched.values()] == ["provider_unavailable"]
    assert "No match" not in next(iter(unmatched.values()))["reason"]
    progress = jobs.progress(job_id)
    assert progress["error"] is False
    assert "Deezer" in progress["stats"]["partial_data_warning"]


def _plain_album(name):
    return {
        "original_artist": name.title(),
        "original_album": "Album",
        "play_count": 5,
        "track_counts": {"t": 5},
    }


def _deezer_metadata(key):
    metadata = MagicMock(
        release_date="2020-01-01",
        image_url="img",
        track_durations={"t": 1},
        provider="deezer",
        album_id="9",
        url="u",
    )
    metadata.as_cache_row.return_value = key
    return metadata


def _fake_session_ctx(session=None):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session or MagicMock())
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


async def _run_misses_with_spotify_down(
    job_id, cache_misses, *, deezer_finds=(), search=None
):
    """Run _fetch_spotify_misses with a Spotify token but failing searches."""
    from scrobblescope.orchestrator import _fetch_spotify_misses

    async def deezer_search(session, artist, album):
        return 9 if (artist, album) in deezer_finds else None

    async def fetch_deezer(session, album_id):
        return _deezer_metadata(("found", "album"))

    async def down(session, artist, album, token, semaphore=None):
        raise ProviderError("spotify", "unavailable")

    hits = {}
    with (
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            side_effect=lambda: _fake_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            side_effect=search or down,
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album", side_effect=deezer_search
        ),
        patch(
            "scrobblescope.orchestrator.fetch_deezer_album", side_effect=fetch_deezer
        ),
    ):
        rows = await _fetch_spotify_misses(job_id, cache_misses, hits)
    return rows, hits


@pytest.mark.asyncio
async def test_spotify_search_outage_degrades_to_deezer_and_lists_the_rest_as_unavailable():
    """
    GIVEN every Spotify search is unanswered, Deezer matches one album only
    WHEN the misses are enriched
    THEN the job is not failed: the Deezer album is enriched, the other is
    listed with the provider-unavailable reason (never "no match"), and a
    partial-data warning is set.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    misses = {
        ("found", "album"): _plain_album("found"),
        ("lost", "album"): _plain_album("lost"),
    }

    rows, hits = await _run_misses_with_spotify_down(
        job_id, misses, deezer_finds={("found", "album")}
    )

    assert rows == [("found", "album")]
    assert list(hits) == [("found", "album")]
    unmatched = jobs.unmatched(job_id)
    assert [v["reason_code"] for v in unmatched.values()] == ["provider_unavailable"]
    assert next(iter(unmatched.values()))["artist"] == "Lost"
    assert "Spotify" in jobs.progress(job_id)["stats"]["partial_data_warning"]


@pytest.mark.asyncio
async def test_spotify_answering_no_search_and_deezer_matching_nothing_fails_retryable():
    """
    GIVEN no Spotify search is answered and Deezer enriches nothing
    WHEN the misses are enriched
    THEN SpotifyUnavailableError is raised (published as the retryable
    spotify_unavailable) and every album was listed as unavailable first.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    misses = {("a", "album"): _plain_album("a"), ("b", "album"): _plain_album("b")}

    with pytest.raises(SpotifyUnavailableError, match="answered no search") as excinfo:
        await _run_misses_with_spotify_down(job_id, misses)

    codes = [v["reason_code"] for v in jobs.unmatched(job_id).values()]
    assert codes == ["provider_unavailable", "provider_unavailable"]
    assert classify_exception_to_error_code(excinfo.value) == "spotify_unavailable"


@pytest.mark.asyncio
async def test_one_answered_spotify_search_keeps_the_job_alive_when_deezer_has_nothing():
    """
    GIVEN one Spotify search is answered (a miss) and one is unanswered, and
    Deezer matches neither
    WHEN the misses are enriched
    THEN no error is raised (Spotify did answer something) and the two albums
    carry different reasons: no match for the answered miss, unavailable for
    the other.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    misses = {
        ("miss", "album"): _plain_album("miss"),
        ("bad", "album"): _plain_album("bad"),
    }

    async def search(session, artist, album, token, semaphore=None):
        if artist == "bad":
            raise ProviderError("spotify", "rate_limited")
        return None

    rows, hits = await _run_misses_with_spotify_down(job_id, misses, search=search)

    assert rows == [] and hits == {}
    reasons = {v["artist"]: v["reason_code"] for v in jobs.unmatched(job_id).values()}
    assert reasons == {"Miss": "no_spotify_match", "Bad": "provider_unavailable"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "deezer_finds", [True, False], ids=["deezer_matches", "deezer_empty"]
)
@pytest.mark.parametrize(
    "failure",
    [TimeoutError(), aiohttp.ClientConnectionError("no route")],
    ids=["timeout", "connection_error"],
)
async def test_spotify_token_transport_failure_degrades_and_fails_only_if_deezer_finds_nothing(
    failure, deezer_finds
):
    """
    GIVEN the Spotify token request times out or is refused
    WHEN the misses are enriched
    THEN a Deezer match keeps the job alive, and with no Deezer match at all
    SpotifyUnavailableError (retryable spotify_unavailable) is raised, never a
    raw timeout (which would publish the non-retryable internal_error).
    """
    from scrobblescope.orchestrator import _fetch_spotify_misses

    token_session = MagicMock()
    token_session.post.side_effect = failure
    misses = {("found", "album"): _plain_album("found")}

    async def deezer_search(session, artist, album):
        return 9 if deezer_finds else None

    async def fetch_deezer(session, album_id):
        return _deezer_metadata(("found", "album"))

    job_id = jobs.create(TEST_JOB_PARAMS)
    with (
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": None, "expires_at": 0},
        ),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "id"),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "secret"),
        patch(
            "scrobblescope.spotify.create_optimized_session",
            return_value=_fake_session_ctx(token_session),
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            side_effect=lambda: _fake_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album", side_effect=deezer_search
        ),
        patch(
            "scrobblescope.orchestrator.fetch_deezer_album", side_effect=fetch_deezer
        ),
    ):
        if deezer_finds:
            rows = await _fetch_spotify_misses(job_id, misses, {})
            assert rows == [("found", "album")]
        else:
            with pytest.raises(SpotifyUnavailableError, match="token fetch failed"):
                await _fetch_spotify_misses(job_id, misses, {})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("spotify_search_down", "spotify_details_down", "deezer_down", "expected"),
    [
        (
            True,
            False,
            False,
            "Spotify was unavailable and Deezer had no match",
        ),
        (True, False, True, "Spotify and Deezer were both unavailable"),
        (
            False,
            True,
            False,
            "Spotify matched it but could not load its details, "
            "and Deezer had no match",
        ),
        (
            False,
            True,
            True,
            "Spotify matched it but could not load its details, "
            "and Deezer was unavailable",
        ),
        (
            False,
            False,
            True,
            "Deezer was unavailable and Spotify had no match",
        ),
    ],
    ids=[
        "spotify_search_down_deezer_no_match",
        "spotify_search_down_deezer_down",
        "spotify_details_down_deezer_no_match",
        "spotify_details_down_deezer_down",
        "spotify_no_match_deezer_down",
    ],
)
async def test_unavailable_row_text_names_what_each_provider_said(
    spotify_search_down, spotify_details_down, deezer_down, expected
):
    """
    GIVEN an album neither provider matched, with each provider either not
    answering or answering "no match"
    WHEN the Deezer fallback phase records it
    THEN the row carries the provider-unavailable reason and exactly the text
    for that combination, never claiming a provider "had no match" when it
    did not answer.
    """
    from scrobblescope.orchestrator._deezer_fallback import _run_deezer_fallback_phase

    job_id = jobs.create(TEST_JOB_PARAMS)
    key = ("artist", "album")

    async def search(session, artist, album):
        if deezer_down:
            raise ProviderError("deezer", "unavailable")
        return None

    with patch("scrobblescope.orchestrator.search_deezer_album", side_effect=search):
        await _run_deezer_fallback_phase(
            job_id,
            MagicMock(),
            {key: _plain_album("artist")},
            {},
            spotify_unavailable_keys={key} if spotify_search_down else frozenset(),
            spotify_detail_unavailable_keys=(
                {key} if spotify_details_down else frozenset()
            ),
        )

    (row,) = jobs.unmatched(job_id).values()
    assert row["reason_code"] == "provider_unavailable"
    assert row["reason"] == expected


@pytest.mark.asyncio
async def test_a_spotify_detail_outage_for_a_matched_album_is_unavailable_not_no_match():
    """
    GIVEN Spotify's search matches two albums, its detail call answers for one
    and cannot be answered for the other, and Deezer matches neither
    WHEN the misses are enriched
    THEN the job is not failed, the album with details is enriched, and the
    other is listed provider_unavailable (never no_spotify_match) with a
    partial-data warning.
    """
    from scrobblescope.orchestrator import _fetch_spotify_misses
    from scrobblescope.spotify import AlbumDetails

    job_id = jobs.create(TEST_JOB_PARAMS)
    misses = {
        ("good", "album"): _plain_album("good"),
        ("bad", "album"): _plain_album("bad"),
    }

    async def search(session, artist, album, token, semaphore=None):
        return f"sp-{artist}"

    async def batch(session, ids, token, semaphore=None, on_fallback=None):
        return AlbumDetails(
            {"sp-good": {"release_date": "2020-01-01"}}, unanswered={"sp-bad"}
        )

    async def deezer_search(session, artist, album):
        return None

    hits = {}
    with (
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            side_effect=lambda: _fake_session_ctx(),
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            side_effect=search,
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            side_effect=batch,
        ),
        patch(
            "scrobblescope.orchestrator.search_deezer_album", side_effect=deezer_search
        ),
    ):
        rows = await _fetch_spotify_misses(job_id, misses, hits)

    assert list(hits) == [("good", "album")]
    assert len(rows) == 1
    (row,) = jobs.unmatched(job_id).values()
    assert row["artist"] == "Bad"
    assert row["reason_code"] == "provider_unavailable"
    assert row["reason"].startswith("Spotify matched it but could not load")
    assert "Spotify" in jobs.progress(job_id)["stats"]["partial_data_warning"]
