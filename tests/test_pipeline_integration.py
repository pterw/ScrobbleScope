import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

from scrobblescope import worker
from scrobblescope.config import MAX_ACTIVE_JOBS
from scrobblescope.orchestrator import background_task

#: One shared wall-clock budget for the /progress poll loop and the
#: background-thread join together (not each): long enough for a real
#: (mocked-network) pipeline run, short enough that a genuine hang still
#: fails the test promptly.
_JOB_TIMEOUT_SECONDS = 30


def test_album_pipeline_runs_on_a_real_thread_end_to_end(client):
    """
    GIVEN a real POST to /results_loading, with only network calls mocked
    WHEN the test polls the real GET /progress route through the Flask test
        client, as a browser does, then joins the real background thread
    THEN the job reaches its terminal state through the real thread, event
        loop and job-store lock, the MusicBrainz hand-off runs while the
        network mocks are still active, the job's concurrency slot is fully
        released, and the real POST /results_complete route renders the
        album that survived the Spotify phase (F-LOAD-2).
    """
    # 2025-06-15T12:00:00Z: inside fetch_top_albums_async's year=2025 window
    # (its from/to bounds); an out-of-window uts is silently dropped inside
    # fetch_top_albums_async before albums is ever built.
    lastfm_page = {
        "recenttracks": {
            "track": [
                {
                    "artist": {"#text": "Fleetwood Mac"},
                    "album": {"#text": "Rumours"},
                    "name": "Dreams",
                    "date": {"uts": "1749988800"},
                }
            ],
            "@attr": {"page": "1", "totalPages": "1"},
        }
    }

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
    o = "scrobblescope.orchestrator."

    # Captures the real threading.Thread that start_job_thread creates for
    # *this* job, so the test can join it before leaving the `with` block:
    # the helper itself never returns or exposes the Thread it builds, so this
    # is the least invasive seam that still runs a genuine daemon thread.
    # Patching threading.Thread patches the one process-wide `threading`
    # module, so other real threads started meanwhile (the registration-year
    # check's own worker thread, asyncio's proactor helper) are also
    # constructed through this subclass; filtering on
    # ``target is background_task`` is what picks out the right one.
    created_threads = []
    real_thread = threading.Thread

    class _CapturingThread(real_thread):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if kwargs.get("target") is background_task:
                created_threads.append(self)

    with (
        patch("scrobblescope.worker.threading.Thread", _CapturingThread),
        patch(
            "scrobblescope.routes.check_user_exists",
            return_value={"registered_year": 2000},
        ),
        patch("scrobblescope.routes.check_profile_is_public", return_value=True),
        patch(
            o + "fetch_all_recent_tracks_async",
            new_callable=AsyncMock,
            return_value=(
                [lastfm_page],
                {"status": "ok", "pages_expected": 1, "pages_received": 1},
            ),
        ),
        patch(
            o + "fetch_spotify_access_token", new_callable=AsyncMock, return_value="tok"
        ),
        patch(o + "create_optimized_session", return_value=mock_session_ctx),
        patch(
            o + "search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value="sp1",
        ) as mock_search,
        patch(
            o + "fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            return_value={"sp1": {"release_date": "1977-02-04"}},
        ) as mock_details,
        patch(
            o + "_get_db_connection", new_callable=AsyncMock, return_value=AsyncMock()
        ),
        patch(o + "_batch_lookup_metadata", new_callable=AsyncMock, return_value={}),
        patch(o + "_batch_persist_metadata", new_callable=AsyncMock),
        # Closes the unconditional MusicBrainz call (enqueue_release_check in
        # _process_filtered_albums) by mock, not by accident of
        # MUSICBRAINZ_ENABLED/_CONTACT in this env.
        patch(o + "enqueue_release_check") as mock_enqueue,
    ):
        resp = client.post(
            "/results_loading",
            # min_plays/min_tracks=1: thresholds are inclusive minimums, and one
            # scrobble gives play_count=1 and one unique track -- the route's
            # defaults (10, 3) would exclude it before Spotify is reached.
            data={
                "username": "flounder14",
                "year": "2025",
                "min_plays": "1",
                "min_tracks": "1",
                # "same" (the route's default) would filter Rumours (1977)
                # out of the final results, before /results_complete ever
                # gets a chance to render it.
                "release_scope": "all",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        location = resp.headers["Location"]
        job_id = parse_qs(urlparse(location).query)["job_id"][0]

        deadline = time.monotonic() + _JOB_TIMEOUT_SECONDS
        progress_payload = client.get(
            "/progress", query_string={"job_id": job_id}
        ).get_json()
        while progress_payload.get("progress", 0) < 100 and not progress_payload.get(
            "error"
        ):
            assert time.monotonic() < deadline, (
                "background thread did not finish in time"
            )
            time.sleep(0.05)
            progress_payload = client.get(
                "/progress", query_string={"job_id": job_id}
            ).get_json()

        # jobs.succeed runs before enqueue_release_check in
        # _process_filtered_albums, so /progress reporting 100 does not prove
        # the MusicBrainz hand-off has happened yet. Join the real background
        # thread -- still inside the `with` block, so the network/MusicBrainz
        # mocks are still active for whatever the thread does next -- before
        # trusting anything past this point.
        assert len(created_threads) == 1, (
            "expected exactly one background_task thread for this job, got "
            f"{len(created_threads)}"
        )
        background_thread = created_threads[0]
        background_thread.join(timeout=max(0.0, deadline - time.monotonic()))
        assert not background_thread.is_alive(), (
            "background thread did not finish within "
            f"{_JOB_TIMEOUT_SECONDS}s of /progress reporting completion"
        )

        assert progress_payload.get("error") is not True, progress_payload
        assert progress_payload["progress"] == 100
        # The point of this test: the album survived filtering and actually
        # reached the Spotify phase, not just a job that completed emptily.
        mock_search.assert_awaited_once()
        mock_details.assert_awaited_once()
        # The MusicBrainz hand-off ran on the happy path, and it ran while
        # this mock was still active (the join above is what guarantees
        # that), not after the `with` block tore it down.
        mock_enqueue.assert_called_once_with(job_id)

    # The concurrency slot acquire_job_slot() granted for this job must be
    # fully released by the time the background thread (joined above) has
    # finished -- release_job_slot runs in run_coroutine_in_new_loop's
    # `finally`, on the same thread. Drain the semaphore to prove every slot,
    # including this job's, is free, then give them all back.
    acquired = 0
    while worker.acquire_job_slot():
        acquired += 1
    for _ in range(acquired):
        worker.release_job_slot()
    assert acquired == MAX_ACTIVE_JOBS, (
        f"expected all {MAX_ACTIVE_JOBS} job slots free after the job finished, "
        f"only {acquired} were"
    )

    # Finish the real /results_loading -> /progress -> /results_complete path:
    # request the real completion route and check the album reached the page.
    results_resp = client.post(
        "/results_complete", data={"job_id": job_id}, follow_redirects=False
    )
    assert results_resp.status_code == 200
    assert b"Rumours" in results_resp.data
