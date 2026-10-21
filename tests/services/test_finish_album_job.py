"""The one publish step both album sources end in (Task 23d).

Whatever produced an ``AlbumSelection`` -- a Last.fm fetch today, a Spotify
export in Batch 23 -- ``finish_album_job`` records its stats and its
exclusions, ends the job at once when nothing is eligible, and otherwise
enriches the eligible albums. These tests call it with a selection and no
Last.fm at all, which is what the export job will do.
"""

import dataclasses
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.album_request import AlbumRequest
from scrobblescope.orchestrator import finish_album_job
from tests.helpers import TEST_JOB_PARAMS, lastfm_albums

ELIGIBLE = {
    ("radiohead", "ok computer"): {
        "play_count": 50,
        "track_counts": {"airbag": 10},
        "original_artist": "Radiohead",
        "original_album": "OK Computer",
    }
}
EXCLUDED = {
    ("quiet artist", "quiet album"): {
        "artist": "Quiet Artist",
        "album": "Quiet Album",
        "play_count": 3,
        "track_count": 1,
        "reason_code": "below_threshold",
        "shortfall": "7 plays and 2 tracks short",
    }
}
# An export job's request: no Last.fm username (PR #3's AlbumRequest allows None).
ALBUM = AlbumRequest(
    username=None,
    year=2025,
    sort_mode="playcount",
    include_unmatched=False,
    release_scope="all",
    decade=None,
    release_year=None,
    min_plays=10,
    min_tracks=3,
    limit_results="all",
)


async def _finish(selection, album=ALBUM):
    """Run the publish step with enrichment and the correction worker mocked."""
    job_id = jobs.create(TEST_JOB_PARAMS)
    process = AsyncMock(return_value=[{"artist": "Radiohead", "album": "OK Computer"}])
    with (
        patch("scrobblescope.orchestrator.process_albums", process),
        patch("scrobblescope.orchestrator.enqueue_release_check") as enqueue,
    ):
        results = await finish_album_job(
            job_id, selection, album, overall_start_time=0.0
        )
    return job_id, results, process, enqueue


@pytest.mark.asyncio
async def test_a_selection_with_albums_is_published_and_enriched():
    """
    GIVEN a selection with one eligible album and one exclusion
    WHEN the publish step runs
    THEN the four stats and the exclusion are on the job, the eligible album
    reaches enrichment, and the finished job is handed to the correction worker.

    Planted defect: skip recording the selection's stats.
    """
    selection, _ = lastfm_albums(ELIGIBLE, EXCLUDED, plays_seen=53)

    job_id, results, process, enqueue = await _finish(selection)

    stats = jobs.progress(job_id)["stats"]
    assert stats["total_scrobbles"] == 53
    assert stats["albums_passing_filter"] == 1
    assert stats["albums_below_threshold"] == 1
    assert stats["unique_albums"] == 2
    assert jobs.unmatched(job_id) == {
        "quiet artist|quiet album": EXCLUDED[("quiet artist", "quiet album")]
    }
    process.assert_awaited_once()
    assert process.await_args.args[1] == ELIGIBLE
    assert results == [{"artist": "Radiohead", "album": "OK Computer"}]
    enqueue.assert_called_once_with(job_id)


@pytest.mark.asyncio
async def test_a_selection_with_nothing_eligible_ends_the_job_once():
    """
    GIVEN a selection whose every album is below a minimum
    WHEN the publish step runs
    THEN the stats and exclusions are recorded, the job ends exactly once at
    100% with the empty-result message and no error, and neither enrichment nor
    the correction worker is reached.

    Planted defects: leave the job running when nothing is eligible; or end it
    twice.
    """
    selection, _ = lastfm_albums(None, EXCLUDED, plays_seen=3)

    with patch("scrobblescope.jobs.succeed", wraps=jobs.succeed) as succeed:
        job_id, results, process, enqueue = await _finish(selection)

    succeed.assert_called_once_with(
        job_id, [], "No albums found for the specified criteria."
    )
    context = jobs.context(job_id)
    assert results == []
    assert context["progress"]["progress"] == 100
    assert context["progress"]["error"] is False
    assert (
        context["progress"]["message"] == "No albums found for the specified criteria."
    )
    assert context["results"] == []
    assert context["progress"]["stats"]["albums_below_threshold"] == 1
    assert len(context["unmatched"]) == 1
    process.assert_not_awaited()
    enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_stats_and_exclusions_are_readable_by_the_time_the_job_ends():
    """
    GIVEN a selection with nothing eligible
    WHEN the job ends
    THEN a page that sees 100% already finds the stats and the exclusions.

    Planted defect: record the exclusions after ending the job.
    """
    selection, _ = lastfm_albums(None, EXCLUDED, plays_seen=3)
    job_id = jobs.create(TEST_JOB_PARAMS)
    seen_at_the_end = {}
    real_succeed = jobs.succeed

    def succeed_and_look(jid, results, message):
        seen_at_the_end["stats"] = jobs.progress(jid)["stats"]
        seen_at_the_end["unmatched"] = jobs.unmatched(jid)
        return real_succeed(jid, results, message)

    with patch("scrobblescope.jobs.succeed", side_effect=succeed_and_look):
        await finish_album_job(job_id, selection, ALBUM, overall_start_time=0.0)

    assert seen_at_the_end["stats"]["albums_below_threshold"] == 1
    assert len(seen_at_the_end["unmatched"]) == 1


@pytest.mark.asyncio
async def test_the_shared_step_writes_no_lastfm_only_stats():
    """
    GIVEN a selection that did not come from Last.fm
    WHEN the publish step runs
    THEN the job carries no page counts or page-loss notice: an export has no pages.

    Planted defect: write ``pages_fetched`` from the shared step.
    """
    selection, _ = lastfm_albums(ELIGIBLE, plays_seen=50)

    job_id, _, _, _ = await _finish(selection)

    stats = jobs.progress(job_id)["stats"]
    assert "pages_fetched" not in stats
    assert "partial_data_warning" not in stats
    assert "pages_dropped" not in stats


@pytest.mark.asyncio
async def test_the_albums_choice_reaches_the_enrichment_tail():
    """
    GIVEN a request that asks for unmatched albums to be listed (include_unmatched)
    WHEN the publish step runs
    THEN the tail that merges them is told so.

    Planted defect: drop the argument on the way to ``_process_filtered_albums``.
    """
    selection, _ = lastfm_albums(ELIGIBLE, plays_seen=50)
    job_id = jobs.create(TEST_JOB_PARAMS)
    tail = AsyncMock(return_value=[])

    with patch("scrobblescope.orchestrator._process_filtered_albums", tail):
        await finish_album_job(
            job_id,
            selection,
            dataclasses.replace(ALBUM, include_unmatched=True),
            overall_start_time=0.0,
        )

    assert tail.await_args.kwargs["include_unmatched"] is True
