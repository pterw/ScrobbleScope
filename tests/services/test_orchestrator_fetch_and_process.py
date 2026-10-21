import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.errors import ProviderError, SpotifyUnavailableError
from scrobblescope.orchestrator import (
    _PLAYTIME_ALBUM_CAP,
    _fetch_and_process,
    _process_filtered_albums,
    background_task,
)
from tests.helpers import TEST_JOB_PARAMS


@pytest.mark.asyncio
async def test_fetch_and_process_cache_hit_does_not_precheck_spotify():
    """
    GIVEN _fetch_and_process receives albums and process_albums returns results
    WHEN _fetch_and_process runs
    THEN it must store results via jobs.succeed (not just return them), set job
    progress to 100, and not call fetch_spotify_access_token directly.

    The critical side-effect assertion is that stored job results equal the
    processed list.  background_task ignores _fetch_and_process's return value and
    relies entirely on the stored job state, so a regression that removes the
    jobs.succeed call would break production but would not be caught by a
    return-value-only assertion.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
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
            return_value=(filtered, {}, {"status": "ok"}),
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

    progress = jobs.progress(job_id)
    assert progress is not None
    assert results == expected_results
    assert progress["error"] is False
    assert progress["progress"] == 100
    mock_token.assert_not_awaited()
    # Verify jobs.succeed was called: background_task reads job state, not the
    # return value.  If this assertion fails, results are returned but not stored.
    assert jobs.context(job_id)["results"] == expected_results


@pytest.mark.asyncio
async def test_fetch_and_process_hands_the_finished_job_to_the_correction_worker():
    """
    GIVEN a run that publishes a non-empty results list
    WHEN _fetch_and_process finishes
    THEN the job is queued for the MusicBrainz correction worker, and only
    after jobs.succeed -- the worker reads the stored results to pick its
    candidates, so an earlier hand-off would find nothing.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    filtered = {
        ("radiohead", "ok computer"): {
            "play_count": 50,
            "track_counts": {"paranoid android": 10},
            "original_artist": "Radiohead",
            "original_album": "OK Computer",
        }
    }
    expected_results = [{"artist": "Radiohead", "album": "OK Computer"}]
    seen_results = []

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(filtered, {}, {"status": "ok"}),
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
            return_value=expected_results,
        ),
        patch(
            "scrobblescope.orchestrator.enqueue_release_check",
            side_effect=lambda queued: seen_results.append(
                jobs.context(queued)["results"]
            ),
        ) as mock_enqueue,
    ):
        await _fetch_and_process(job_id, "flounder14", 2025, "playcount", "same")

    mock_enqueue.assert_called_once_with(job_id)
    assert seen_results == [expected_results]


@pytest.mark.asyncio
async def test_fetch_and_process_does_not_queue_correction_checks_on_an_error():
    """
    GIVEN a run that fails and publishes an empty results list
    WHEN _fetch_and_process unwinds
    THEN the correction worker is never handed the job: there is nothing to
    correction-check, and the queue is a shared, rate-limited resource.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        patch("scrobblescope.orchestrator.enqueue_release_check") as mock_enqueue,
    ):
        results = await _fetch_and_process(
            job_id, "flounder14", 2025, "playcount", "same"
        )

    assert results == []
    mock_enqueue.assert_not_called()
    assert jobs.progress(job_id)["error"] is True


@pytest.mark.asyncio
async def test_fetch_and_process_retains_all_below_threshold_albums():
    """A successful empty eligible set must still publish threshold exclusions."""
    job_id = jobs.create(TEST_JOB_PARAMS)
    threshold_item = {
        "artist": "Lizzy McAlpine",
        "album": "Older",
        "play_count": 7,
        "track_count": 2,
        "failed_thresholds": ["plays", "tracks"],
        "min_plays": 10,
        "min_tracks": 3,
        "reason_code": "below_threshold",
        "reason": (
            "Played 7 times across 2 unique tracks; minimum is 10 plays and "
            "3 unique tracks"
        ),
    }

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(
                {},
                {("lizzy mcalpine", "older"): threshold_item},
                {"status": "ok"},
            ),
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        results = await _fetch_and_process(
            job_id, "flounder14", 2025, "playcount", "same"
        )

    assert results == []
    assert jobs.unmatched(job_id) == {"lizzy mcalpine|older": threshold_item}
    progress = jobs.progress(job_id)
    assert progress is not None
    assert progress["progress"] == 100
    assert progress["error"] is False
    mock_process.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_and_process_discards_exclusions_on_lastfm_error():
    """An upstream failure must not publish a partial unmatched report."""
    job_id = jobs.create(TEST_JOB_PARAMS)
    threshold_item = {
        "artist": "Artist",
        "album": "Album",
        "reason_code": "below_threshold",
    }

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(
                {},
                {("artist", "album"): threshold_item},
                {"status": "error", "reason": "lastfm_unavailable"},
            ),
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        results = await _fetch_and_process(
            job_id, "flounder14", 2025, "playcount", "same"
        )

    assert results == []
    assert jobs.unmatched(job_id) == {}
    progress = jobs.progress(job_id)
    assert progress is not None
    assert progress["error"] is True
    assert progress["error_code"] == "lastfm_unavailable"
    mock_process.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_and_process_sets_spotify_error_from_process_albums():
    """
    GIVEN process_albums raises SpotifyUnavailableError
    WHEN _fetch_and_process runs
    THEN it should set a classified spotify_unavailable job error.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
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
            return_value=(filtered, {}, {"status": "ok"}),
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

    progress = jobs.progress(job_id)
    assert progress is not None
    assert results == []
    assert progress["error"] is True
    assert progress["error_code"] == "spotify_unavailable"
    assert progress["error_source"] == "spotify"


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
    job_id = jobs.create(TEST_JOB_PARAMS)
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
            return_value=(filtered, {}, {"status": "ok"}),
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
    job_id = jobs.create(TEST_JOB_PARAMS)
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
            return_value=(filtered, {}, {"status": "ok"}),
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
async def test_fetch_and_process_lastfm_phase_callback():
    """
    GIVEN _fetch_and_process runs with a simulated Last.fm progress callback
    WHEN progress_cb is invoked with (23, 102, 23)
    THEN the job stores the exact lastfm_fetch phase dict,
    and upon completion, the phase is cleared.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    observed_phase = None

    async def fake_fetch(*args, **kwargs):
        nonlocal observed_phase
        cb = kwargs.get("progress_cb")
        if cb:
            cb(23, 102, 23)
            observed_phase = jobs.progress(job_id).get("phase")
        return {}, {}, {"status": "ok"}

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            side_effect=fake_fetch,
        ),
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        await _fetch_and_process(job_id, "user", 2025, "playcount", "all")

    assert observed_phase == {
        "key": "lastfm_fetch",
        "label": "Fetching scrobbles",
        "unit": "page",
        "current": 23,
        "total": 102,
    }
    final_progress = jobs.progress(job_id)
    assert "phase" not in final_progress


@pytest.mark.asyncio
async def test_playtime_limit_does_not_preslice():
    """
    GIVEN filtered_albums has 5 entries and limit_results="2" with sort_mode="playtime"
    WHEN _fetch_and_process runs
    THEN process_albums should receive all 5 albums because playtime ranking requires
    Spotify track duration data and cannot be determined before the Spotify fetch.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
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
            return_value=(filtered, {}, {"status": "ok"}),
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
    job_id = jobs.create(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(filtered, {}, {"status": "ok"}),
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
    job_id = jobs.create(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            new_callable=AsyncMock,
            return_value=(filtered, {}, {"status": "ok"}),
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
    job_id = jobs.create(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task(job_id)

        mock_fp.assert_awaited_once()
        call_args = mock_fp.call_args
        assert call_args[0][0] == job_id
        assert call_args[0][1] == "testuser"
        mock_release.assert_called_once()


def test_background_task_releases_slot_on_exception():
    """
    GIVEN _fetch_and_process raises an unhandled exception
    WHEN background_task is called
    THEN release_job_slot should still be called in the finally block.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
            side_effect=RuntimeError("unhandled crash"),
        ),
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task(job_id)

    mock_release.assert_called_once()


def test_background_task_releases_slot_when_event_loop_setup_raises():
    """
    GIVEN event loop creation or setup raises an exception
    WHEN background_task is called
    THEN release_job_slot must still be called so the concurrency slot is not leaked (F-B21-1).
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    with (
        patch("asyncio.set_event_loop", side_effect=RuntimeError("loop setup failed")),
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task(job_id)

    mock_release.assert_called_once()


def test_background_task_releases_slot_when_loop_close_raises():
    """
    GIVEN loop.close raises an exception in finally
    WHEN background_task terminates
    THEN release_job_slot must still be called so the concurrency slot is not leaked.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    mock_loop = MagicMock()
    mock_loop.run_until_complete.side_effect = lambda coroutine: coroutine.close()
    mock_loop.close.side_effect = RuntimeError("close failed")

    with (
        patch("asyncio.new_event_loop", return_value=mock_loop),
        patch("asyncio.ProactorEventLoop", return_value=mock_loop, create=True),
        patch("asyncio.set_event_loop"),
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        with pytest.raises(RuntimeError, match="close failed"):
            background_task(job_id)

    mock_release.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_and_process_passes_progress_cb_to_lastfm():
    """
    GIVEN _fetch_and_process is called
    WHEN fetch_top_albums_async invokes progress_cb per page
    THEN the job maps page progress into the 5%-20% range
    with the phase line "Reading your Last.fm history...". The detailed
    fraction belongs exclusively to the visible `Pages fetched` statistic.

    Arithmetic: pct = 5 + int(15 * pages_done / total_pages)
    For 3 pages: (1,3)->10, (2,3)->15, (3,3)->20.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    async def _invoke_cb(*args, **kwargs):
        """Mock fetch_top_albums_async that invokes progress_cb."""
        cb = kwargs.get("progress_cb")
        if cb:
            cb(1, 3, 1)
            cb(2, 3, 2)
            cb(3, 3, 3)
        return {}, {}, {"status": "ok"}

    progress_calls = []

    real_advance = jobs.advance

    def _tracking_advance(jid, percent, message, phase=None):
        progress_calls.append({"progress": percent, "message": message, "phase": phase})
        return real_advance(jid, percent, message, phase=phase)

    with (
        patch(
            "scrobblescope.orchestrator.fetch_top_albums_async",
            side_effect=_invoke_cb,
        ),
        patch(
            "scrobblescope.jobs.advance",
            side_effect=_tracking_advance,
        ),
    ):
        await _fetch_and_process(job_id, "testuser", 2025, "playcount", "all")

    # Keep page depth out of the phase line; the UI has a dedicated stat.
    page_calls = [
        c
        for c in progress_calls
        if c.get("message") == "Reading your Last.fm history..."
    ]
    assert len(page_calls) == 3
    assert page_calls[0] == {
        "progress": 10,
        "message": "Reading your Last.fm history...",
        "phase": {
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 1,
            "total": 3,
        },
    }
    assert page_calls[1] == {
        "progress": 15,
        "message": "Reading your Last.fm history...",
        "phase": {
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 2,
            "total": 3,
        },
    }
    assert page_calls[2] == {
        "progress": 20,
        "message": "Reading your Last.fm history...",
        "phase": {
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 3,
            "total": 3,
        },
    }


def test_background_task_crash_publishes_internal_error():
    """
    GIVEN _fetch_and_process raises something no inner handler classified
    WHEN background_task runs it
    THEN the job ends as internal_error, so a polling page stops waiting
    (F-SWE-5: before this the album backstop only logged).
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
            side_effect=ZeroDivisionError("ours"),
        ),
        patch("scrobblescope.orchestrator.release_job_slot"),
    ):
        background_task(job_id)

    progress = jobs.progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "internal_error"
    assert progress["error_source"] == "internal"


def test_background_task_runs_the_pipeline_with_the_job_records_parameters():
    """
    GIVEN a job whose record holds a value in every slot
    WHEN background_task is given only the job id
    THEN the pipeline is awaited with those values, each in its own slot.

    Mutation: pass the defaults for min_plays and min_tracks and this fails.
    """
    job_id = jobs.create(
        {
            **TEST_JOB_PARAMS,
            "username": "recorded",
            "year": 2023,
            "sort_mode": "playtime",
            "release_scope": "custom",
            "release_year": 1982,
            "min_plays": 7,
            "min_tracks": 4,
            "limit_results": "25",
            "include_unmatched": True,
        }
    )

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot"),
    ):
        background_task(job_id)

    mock_fp.assert_awaited_once_with(
        job_id,
        "recorded",
        2023,
        "playtime",
        "custom",
        None,
        1982,
        7,
        4,
        "25",
        include_unmatched=True,
    )


def test_background_task_for_a_vanished_job_runs_nothing_and_frees_its_slot():
    """
    GIVEN the job expired between admission and the thread's first line
    WHEN background_task runs
    THEN the pipeline is not run and the slot the route took is released once.

    Mutation: drop `release_job_slot()` from the vanished-job branch and the
    slot leaks (the assertion on mock_release fails).
    """
    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task("no-such-job")

    mock_fp.assert_not_called()
    mock_release.assert_called_once()


def test_background_task_for_an_unusable_record_fails_the_job_and_frees_its_slot():
    """
    GIVEN a job record that holds no username or year (not a usable request)
    WHEN background_task runs
    THEN the pipeline is not run, the job ends as internal_error so a polling
    page stops waiting, and the slot the route took is released once.

    Mutation: drop `jobs.fail(job_id, "internal_error")` from
    `_album_request_for` and the job never ends; drop the release in
    background_task and mock_release is not called.
    """
    job_id = jobs.create({"mode": "album"})

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task(job_id)

    mock_fp.assert_not_called()
    mock_release.assert_called_once()
    assert jobs.progress(job_id)["error_code"] == "internal_error"


@pytest.mark.asyncio
async def test_fetch_and_process_unclassified_exception_publishes_internal_error():
    """
    GIVEN the Last.fm fetch raises an exception nothing classifies
    WHEN _fetch_and_process runs
    THEN the job ends as a non-retryable ``internal_error`` with empty results
    and the generic message: the exception's text never reaches the browser.
    This is the heatmap's answer too (F-B23-22).
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    with patch(
        "scrobblescope.orchestrator.fetch_top_albums_async",
        new_callable=AsyncMock,
        side_effect=ZeroDivisionError("boom"),
    ):
        results = await _fetch_and_process(job_id, "user", 2025, "playcount", "all")

    assert results == []
    ctx = jobs.context(job_id)
    assert ctx["results"] == []
    assert ctx["progress"]["error"] is True
    assert ctx["progress"]["error_code"] == "internal_error"
    assert ctx["progress"]["error_source"] == "internal"
    assert ctx["progress"]["retryable"] is False
    assert "boom" not in ctx["progress"]["message"]
    assert ctx["progress"]["message"].startswith("Something went wrong on our side")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "code"),
    [
        ("unavailable", "spotify_unavailable"),
        ("rate_limited", "spotify_rate_limited"),
    ],
)
async def test_fetch_and_process_typed_spotify_failure_publishes_retryable_code(
    kind, code
):
    """
    GIVEN a ProviderError for Spotify escapes the album pipeline (an ordinary
    Spotify search outage no longer does: it degrades per album, and the
    aggregate rule raises SpotifyUnavailableError instead)
    WHEN _fetch_and_process runs
    THEN the classifier wiring answers with that provider's code, retryable,
    blaming Spotify, and never falls through to internal_error.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    with patch(
        "scrobblescope.orchestrator.fetch_top_albums_async",
        new_callable=AsyncMock,
        side_effect=ProviderError("spotify", kind),
    ):
        await _fetch_and_process(job_id, "user", 2025, "playcount", "all")

    progress = jobs.progress(job_id)
    assert progress["error_code"] == code
    assert progress["error_source"] == "spotify"
    assert progress["retryable"] is True


@pytest.mark.asyncio
async def test_fetch_and_process_message_that_reads_like_not_found_is_ours():
    """
    GIVEN an unrelated exception whose text holds "user" and "not found"
    WHEN _fetch_and_process runs
    THEN it is not user_not_found: classification is by type, so the job ends
    as internal_error (F-B23-16).
    """
    job_id = jobs.create(TEST_JOB_PARAMS)

    with patch(
        "scrobblescope.orchestrator.fetch_top_albums_async",
        new_callable=AsyncMock,
        side_effect=KeyError("user row not found"),
    ):
        await _fetch_and_process(job_id, "user", 2025, "playcount", "all")

    assert jobs.progress(job_id)["error_code"] == "internal_error"


# ---------------------------------------------------------------------------
# "Include unmatched albums": the merge inside _process_filtered_albums
# ---------------------------------------------------------------------------

_INCLUDE_FILTERED = {
    ("a", "one"): {"play_count": 50, "track_counts": {"t": 1}},
    ("b", "two"): {"play_count": 40, "track_counts": {"t": 1}},
    ("c", "three"): {"play_count": 10, "track_counts": {"t": 1}},
}


def _include_matched_rows():
    return [
        {"artist": "A", "album": "One", "play_count": 50, "play_time_seconds": 60},
        {"artist": "B", "album": "Two", "play_count": 40, "play_time_seconds": 60},
        {"artist": "C", "album": "Three", "play_count": 10, "play_time_seconds": 60},
    ]


def _record_include_unmatched(job_id):
    for artist, album, reason, plays in (
        ("D", "Four", "no_spotify_match", 30),
        ("E", "Five", "provider_unavailable", 20),
        ("F", "Six", "below_threshold", 100),
    ):
        jobs.record_unmatched(
            job_id,
            f"{artist.lower()}|{album.lower()}",
            {
                "artist": artist,
                "album": album,
                "reason": "x",
                "reason_code": reason,
                "play_count": plays,
            },
        )


@pytest.mark.asyncio
async def test_process_filtered_albums_flag_off_keeps_process_albums_list():
    """
    GIVEN a job with unmatched entries and the include flag left off
    WHEN _process_filtered_albums finishes
    THEN it returns the very list process_albums produced (no merge, no
    second sort) and the stored results hold only matched rows.

    Mutation: merge regardless of the flag and the identity assertion fails.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    _record_include_unmatched(job_id)
    produced = _include_matched_rows()

    with (
        patch(
            "scrobblescope.orchestrator.process_albums",
            new_callable=AsyncMock,
            return_value=produced,
        ),
        patch("scrobblescope.orchestrator.merge_unmatched_rows") as merge,
    ):
        results = await _process_filtered_albums(
            job_id,
            dict(_INCLUDE_FILTERED),
            2025,
            "playcount",
            "same",
            None,
            None,
            "all",
            0.0,
        )

    assert results is produced
    merge.assert_not_called()
    assert [r["album"] for r in jobs.context(job_id)["results"]] == [
        "One",
        "Two",
        "Three",
    ]


@pytest.mark.asyncio
async def test_process_filtered_albums_flag_on_merges_then_slices():
    """
    GIVEN three matched albums (50, 40, 10 plays) and unmatched albums with
    30 and 20 plays plus a below-threshold album with 100
    WHEN _process_filtered_albums runs with include_unmatched and
    limit_results=3
    THEN the stored list is the top three of the combined list by play count
    -- One, Two, then the 30-play unmatched Four -- and the below-threshold
    album is never listed.

    Mutation: slice before merging and Four is missing; merge below_threshold
    and Six leads the list.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    _record_include_unmatched(job_id)

    with patch(
        "scrobblescope.orchestrator.process_albums",
        new_callable=AsyncMock,
        return_value=_include_matched_rows(),
    ):
        results = await _process_filtered_albums(
            job_id,
            dict(_INCLUDE_FILTERED),
            2025,
            "playcount",
            "same",
            None,
            None,
            "3",
            0.0,
            include_unmatched=True,
        )

    assert [r["album"] for r in results] == ["One", "Two", "Four"]
    stored = jobs.context(job_id)["results"]
    assert [r["album"] for r in stored] == ["One", "Two", "Four"]
    assert stored[2]["unmatched_reason"] == "no_spotify_match"
    assert "Found 3 albums" in jobs.progress(job_id)["message"]


def test_background_task_stores_unmatched_rows_when_the_flag_is_on():
    """
    GIVEN a run whose Spotify phase leaves one album unmatched
    WHEN background_task runs with include_unmatched on, and again off
    THEN the job store holds the unmatched row (marked, play count only)
    for the on run and only matched rows for the off run; the "Done" message
    counts the rows listed.

    Mutation: stop passing the flag through background_task and the on run
    stores only the matched row.
    """

    async def fake_process_albums(job_id, *_args):
        jobs.record_unmatched(
            job_id,
            "d|four",
            {
                "artist": "D",
                "album": "Four",
                "reason": "x",
                "reason_code": "no_spotify_match",
                "play_count": 30,
            },
        )
        return _include_matched_rows()[:1]

    stored = {}
    for flag in (True, False):
        job_id = jobs.create({**TEST_JOB_PARAMS, "include_unmatched": flag})
        with (
            patch(
                "scrobblescope.orchestrator.fetch_top_albums_async",
                new_callable=AsyncMock,
                return_value=(dict(_INCLUDE_FILTERED), {}, {"status": "ok"}),
            ),
            patch(
                "scrobblescope.orchestrator.process_albums",
                side_effect=fake_process_albums,
            ),
            patch("scrobblescope.orchestrator.release_job_slot"),
        ):
            background_task(job_id)
        stored[flag] = (
            jobs.context(job_id)["results"],
            jobs.progress(job_id)["message"],
        )

    on_rows, on_message = stored[True]
    assert [(r["album"], r["unmatched_reason"]) for r in on_rows[1:]] == [
        ("Four", "no_spotify_match")
    ]
    assert on_rows[1]["play_time_seconds"] == 0
    assert "Found 2 albums" in on_message
    off_rows, off_message = stored[False]
    assert [r["album"] for r in off_rows] == ["One"]
    assert "Found 1 albums" in off_message
