import time
from unittest.mock import AsyncMock, MagicMock, patch

from scrobblescope.repositories import get_job_progress


def test_album_pipeline_runs_on_a_real_thread_end_to_end(client):
    """
    GIVEN a real POST to /results_loading, with only network calls mocked
    WHEN the test polls the real /progress endpoint, as a browser does
    THEN the job reaches its terminal state through the real thread, event
    loop and job-store lock, and actually reaches the Spotify phase (F-LOAD-2).
    """
    # 2025-06-15T12:00:00Z: inside fetch_top_albums_async's year=2025 window
    # (orchestrator/__init__.py:118-119); an out-of-window uts is silently
    # dropped at :144-149 before albums is ever built.
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

    with (
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
        # Closes the unconditional MusicBrainz call (orchestrator/__init__.py:619)
        # by mock, not by accident of MUSICBRAINZ_ENABLED/_CONTACT in this env.
        patch(o + "enqueue_release_check"),
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
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        job_id = resp.headers["Location"].rsplit("job_id=", 1)[-1]

        deadline = time.time() + 10
        progress = get_job_progress(job_id)
        while (
            progress is not None
            and progress.get("progress", 0) < 100
            and not progress.get("error")
        ):
            assert time.time() < deadline, "background thread did not finish in time"
            time.sleep(0.05)
            progress = get_job_progress(job_id)

    assert progress is not None
    assert progress.get("error") is not True, progress
    assert progress["progress"] == 100
    # The point of this test: the album survived filtering and actually
    # reached the Spotify phase, not just a job that completed emptily.
    mock_search.assert_awaited_once()
    mock_details.assert_awaited_once()
