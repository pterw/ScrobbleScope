"""Last.fm in, job results out: both pipelines pinned at their one stable seam.

Every test fakes only the Last.fm HTTP edge (``tests.helpers.lastfm_edge``) and
reads the answer from the job the pipeline publishes. Nothing here imports a
function that sits between the page layer and the job, so the suite means the
same thing before and after the scrobbles-not-pages refactor (Batch 23 WP-0,
Task 23). Five tests assert a behaviour the refactor changed by owner ruling
(2026-09-29). They were ``xfail(strict=True)`` until the refactor landed and
now pass as ordinary tests.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.domain import normalize_name, normalize_track_name
from scrobblescope.heatmap import _fetch_and_process_heatmap, heatmap_task
from scrobblescope.orchestrator import _fetch_and_process
from tests.helpers import (
    TEST_JOB_PARAMS,
    FakeLastfm,
    lastfm_edge,
    lastfm_now_playing,
    lastfm_page,
    lastfm_track,
)

YEAR = 2023


def _at(month, day, hour=12, minute=0, second=0, year=YEAR):
    """A UTC moment inside (by default) the year the album job asks for."""
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def _album_plays(artist, album, titles, each, day=15):
    """``each`` scrobbles of every title, on June ``day`` 2023, at distinct seconds."""
    sequence = [title for title in titles for _ in range(each)]
    return [
        lastfm_track(artist, album, title, _at(6, day, minute=n // 60, second=n % 60))
        for n, title in enumerate(sequence)
    ]


async def _run_album_job(fake, *, min_plays=10, min_tracks=3, year=YEAR):
    """Run the album pipeline up to enrichment and return what it published.

    ``process_albums`` (Spotify, Deezer and the cache) is replaced by a mock
    that records the albums it was handed. PR #3 (the album request module)
    leaves ``_fetch_and_process``'s signature alone, so this helper needs no
    edit when it merges.
    """
    job_id = jobs.create({**TEST_JOB_PARAMS, "year": year})
    process = AsyncMock(return_value=[])
    with (
        lastfm_edge(fake),
        patch("scrobblescope.orchestrator.process_albums", process),
        patch("scrobblescope.orchestrator.enqueue_release_check") as enqueue,
    ):
        await _fetch_and_process(
            job_id,
            "parity_user",
            year,
            "playcount",
            "all",
            min_plays=min_plays,
            min_tracks=min_tracks,
        )
    return job_id, process, enqueue


def _handed_to_enrichment(process):
    """The eligible albums ``process_albums`` was awaited with (exactly once)."""
    process.assert_awaited_once()
    return process.await_args.args[1]


# ---------------------------------------------------------------------------
# Album pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_album_counts_come_from_the_scrobbles_on_every_page():
    """
    GIVEN one album scrobbled across two pages
    WHEN the album job runs
    THEN the album carries every scrobble from both pages, its distinct tracks
    and the names as Last.fm spelled them, and the job stats agree.

    Planted defect: aggregate only the first page.
    """
    titles = ["Paranoid Android", "Karma Police", "Airbag", "Exit Music"]
    first = _album_plays("Radiohead", "OK Computer", titles, 4)
    second = _album_plays("Radiohead", "OK Computer", titles[:1], 2, day=16)
    fake = FakeLastfm({1: lastfm_page(first, 1, 2), 2: lastfm_page(second, 2, 2)})

    job_id, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Radiohead", "OK Computer")]
    assert album["play_count"] == 18
    assert dict(album["track_counts"]) == {
        normalize_track_name("Paranoid Android"): 6,
        normalize_track_name("Karma Police"): 4,
        normalize_track_name("Airbag"): 4,
        normalize_track_name("Exit Music"): 4,
    }
    assert (album["original_artist"], album["original_album"]) == (
        "Radiohead",
        "OK Computer",
    )
    stats = jobs.progress(job_id)["stats"]
    assert stats["unique_albums"] == 1
    assert stats["albums_passing_filter"] == 1
    assert stats["albums_below_threshold"] == 0
    assert stats["pages_fetched"] == 2


@pytest.mark.asyncio
async def test_a_lone_track_object_counts_as_one_scrobble():
    """
    GIVEN Last.fm serves a page's only scrobble as a bare object, not a list
    WHEN the album job runs
    THEN that scrobble is counted once.

    Planted defect: stop normalizing the lone object, so the page is refused.
    """
    lone = lastfm_track("Mitski", "Laurel Hell", "Working for the Knife", _at(6, 15))
    fake = FakeLastfm({1: lastfm_page(lone)})

    _, process, _ = await _run_album_job(fake, min_plays=1, min_tracks=1)

    album = _handed_to_enrichment(process)[normalize_name("Mitski", "Laurel Hell")]
    assert album["play_count"] == 1


@pytest.mark.asyncio
async def test_the_now_playing_entry_is_not_an_album_play():
    """
    GIVEN a now-playing entry followed by twelve completed scrobbles
    WHEN the album job runs
    THEN the album has twelve plays, not thirteen.

    Planted defect: count the entry that has no date.
    """
    tracks = [lastfm_now_playing("Artist Z", "Album Z", "Playing Now")]
    tracks += _album_plays("Artist Z", "Album Z", ["One", "Two", "Three"], 4)
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Artist Z", "Album Z")]
    assert album["play_count"] == 12


@pytest.mark.asyncio
async def test_the_scrobble_total_counts_completed_scrobbles_only():
    """
    GIVEN a now-playing entry followed by twelve completed scrobbles
    WHEN the album job runs
    THEN the job's scrobble total is twelve.

    Planted defect: count the entry that has no date.
    """
    tracks = [lastfm_now_playing("Artist Z", "Album Z", "Playing Now")]
    tracks += _album_plays("Artist Z", "Album Z", ["One", "Two", "Three"], 4)
    fake = FakeLastfm({1: lastfm_page(tracks)})

    job_id, _, _ = await _run_album_job(fake)

    assert jobs.progress(job_id)["stats"]["total_scrobbles"] == 12


@pytest.mark.asyncio
async def test_scrobbles_outside_the_year_are_not_counted():
    """
    GIVEN a page holding twelve scrobbles from three years earlier and twelve
    from the year asked for
    WHEN the album job runs for that year
    THEN only the album listened to in that year reaches enrichment, while the
    job's scrobble total still counts every dated entry Last.fm returned.

    Planted defects: skip the window filter; or count only the entries inside
    the window in the scrobble total.
    """
    earlier = [
        lastfm_track("Artist X", "Album X", f"t{n}", _at(6, 15, second=n, year=2020))
        for n in range(12)
    ]
    current = _album_plays("Artist Y", "Album Y", ["a", "b", "c"], 4)
    fake = FakeLastfm({1: lastfm_page(earlier + current)})

    job_id, process, _ = await _run_album_job(fake)

    assert set(_handed_to_enrichment(process)) == {
        normalize_name("Artist Y", "Album Y")
    }
    assert jobs.progress(job_id)["stats"]["total_scrobbles"] == 24


@pytest.mark.asyncio
async def test_the_year_window_includes_its_first_and_last_second():
    """
    GIVEN scrobbles at the last second before the year, its first second, its
    last second and the first second after it
    WHEN the album job runs for that year
    THEN exactly the two inside it are counted, both ends inclusive.

    Planted defect: treat the window's start as exclusive.
    """
    moments = {
        "Before": datetime(YEAR - 1, 12, 31, 23, 59, 59, tzinfo=UTC),
        "Edge Start": datetime(YEAR, 1, 1, 0, 0, 0, tzinfo=UTC),
        "Edge End": datetime(YEAR, 12, 31, 23, 59, 59, tzinfo=UTC),
        "After": datetime(YEAR + 1, 1, 1, 0, 0, 0, tzinfo=UTC),
    }
    tracks = [
        lastfm_track("Edge Artist", name, "Song", when)
        for name, when in moments.items()
    ]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake, min_plays=1, min_tracks=1)

    kept = {a["original_album"] for a in _handed_to_enrichment(process).values()}
    assert kept == {"Edge Start", "Edge End"}


@pytest.mark.asyncio
async def test_an_entry_with_no_album_artist_or_track_name_is_not_an_album_play():
    """
    GIVEN twelve scrobbles with an empty album, twelve with an empty artist and
    twelve with an empty track name, beside one real album
    WHEN the album job runs
    THEN only the real album is aggregated: an album needs all three names.

    Planted defect: drop the guard that requires all three names.
    """
    no_album = [
        lastfm_track("Someone", "", f"t{n}", _at(6, 15, second=n)) for n in range(12)
    ]
    no_artist = [
        lastfm_track("", "Orphan", f"t{n}", _at(6, 16, second=n)) for n in range(12)
    ]
    no_track = [
        lastfm_track("Someone", "Untitled", "", _at(6, 17, second=n)) for n in range(12)
    ]
    real = _album_plays("Real Artist", "Real Album", ["a", "b", "c"], 4)
    fake = FakeLastfm({1: lastfm_page(no_album + no_artist + no_track + real)})

    _, process, _ = await _run_album_job(fake)

    assert set(_handed_to_enrichment(process)) == {
        normalize_name("Real Artist", "Real Album")
    }


@pytest.mark.asyncio
async def test_an_entry_with_no_album_field_is_not_an_album_play():
    """
    GIVEN twelve scrobbles whose JSON has no ``album`` key at all
    WHEN the album job runs
    THEN no album is aggregated from them.

    Planted defect: invent an album named "..." for an entry that has none.
    """
    tracks = [
        {
            "artist": {"#text": "Keyless"},
            "name": f"t{n}",
            "date": {"uts": str(int(_at(6, 15, second=n).timestamp()))},
        }
        for n in range(12)
    ]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    job_id, _, _ = await _run_album_job(fake)

    assert jobs.progress(job_id)["stats"]["unique_albums"] == 0


@pytest.mark.asyncio
async def test_the_first_casing_seen_names_the_album():
    """
    GIVEN one album scrobbled under two casings
    WHEN the album job runs
    THEN it is one album, and the casing of its first scrobble is its name.

    Planted defect: let the last casing seen replace the first.
    """
    tracks = [
        lastfm_track("Mitski", "Be The Cowboy", f"t{n}", _at(6, 15, second=n))
        for n in range(6)
    ] + [
        lastfm_track("MITSKI", "be the cowboy", f"u{n}", _at(6, 16, second=n))
        for n in range(6)
    ]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake)

    albums = _handed_to_enrichment(process)
    assert len(albums) == 1
    album = next(iter(albums.values()))
    assert album["play_count"] == 12
    assert (album["original_artist"], album["original_album"]) == (
        "Mitski",
        "Be The Cowboy",
    )


@pytest.mark.asyncio
async def test_a_dropped_page_makes_the_album_job_partial_and_says_so():
    """
    GIVEN a three-page fetch whose third page never answers
    WHEN the album job runs
    THEN the job still produces its albums from the two pages it read, and
    records the notice the Results page shows, the number of pages dropped and
    fetched, and that the loss came from Last.fm.

    Planted defect: forget to record that the loss came from Last.fm.
    """
    titles = ["a", "b", "c"]
    fake = FakeLastfm(
        {
            1: lastfm_page(_album_plays("Artist", "Album", titles, 3), 1, 3),
            2: lastfm_page(_album_plays("Artist", "Album", titles, 1, day=16), 2, 3),
        }
    )

    job_id, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Artist", "Album")]
    assert album["play_count"] == 12
    stats = jobs.progress(job_id)["stats"]
    assert stats["partial_data_warning"] == (
        "Note: 1 of 3 Last.fm pages failed to load (33% data loss). "
        "Results may be incomplete."
    )
    assert stats["pages_dropped"] == 1
    assert stats["pages_fetched"] == 2
    assert stats["partial_data_sources"] == ["lastfm"]


@pytest.mark.asyncio
async def test_when_every_album_is_below_a_minimum_the_job_ends_with_the_report():
    """
    GIVEN two albums, one two plays short and one a track short
    WHEN the album job runs
    THEN each is recorded as a below-threshold exclusion with its shortfall,
    the job ends at 100% with the empty-result message and no error, and
    enrichment and the correction worker are never reached.

    Planted defect: leave the job running when nothing passes.
    """
    short_plays = _album_plays("Quiet Artist", "Quiet Album", ["a", "b", "c"], 3)[:8]
    short_tracks = _album_plays("Narrow Artist", "Narrow Album", ["a", "b"], 6)
    fake = FakeLastfm({1: lastfm_page(short_plays + short_tracks)})

    job_id, process, enqueue = await _run_album_job(fake)

    context = jobs.context(job_id)
    assert context["progress"]["progress"] == 100
    assert context["progress"]["error"] is False
    assert (
        context["progress"]["message"] == "No albums found for the specified criteria."
    )
    assert context["results"] == []
    quiet = context["unmatched"][
        "|".join(normalize_name("Quiet Artist", "Quiet Album"))
    ]
    narrow = context["unmatched"][
        "|".join(normalize_name("Narrow Artist", "Narrow Album"))
    ]
    assert quiet["reason_code"] == "below_threshold"
    assert quiet["shortfall"] == "2 plays short"
    assert narrow["shortfall"] == "1 track short"
    stats = context["progress"]["stats"]
    assert stats["albums_below_threshold"] == 2
    assert stats["albums_passing_filter"] == 0
    process.assert_not_awaited()
    enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_an_album_exactly_at_both_minimums_is_eligible():
    """
    GIVEN an album with exactly ten plays on exactly three tracks and another
    with nine
    WHEN the album job runs with the default minimums
    THEN the first is eligible and the second is excluded: the minimums are inclusive.

    Planted defect: make the play minimum exclusive.
    """
    exact = _album_plays("Exact", "At Limit", ["a", "b", "c"], 4)[:10]
    short = _album_plays("Short", "One Short", ["a", "b", "c"], 3)
    fake = FakeLastfm({1: lastfm_page(exact + short)})

    job_id, process, _ = await _run_album_job(fake)

    assert set(_handed_to_enrichment(process)) == {normalize_name("Exact", "At Limit")}
    assert "|".join(normalize_name("Short", "One Short")) in jobs.unmatched(job_id)


@pytest.mark.asyncio
async def test_an_unusable_first_page_ends_the_album_job_as_lastfm_unavailable():
    """
    GIVEN Last.fm never answers the first page
    WHEN the album job runs
    THEN it ends in a retryable lastfm_unavailable error with no results, no
    unmatched report, no enrichment and no correction-worker hand-off.

    Planted defect: carry on as if the fetch had succeeded.
    """
    job_id, process, enqueue = await _run_album_job(FakeLastfm({}))

    context = jobs.context(job_id)
    assert context["progress"]["error"] is True
    assert context["progress"]["error_code"] == "lastfm_unavailable"
    assert context["progress"]["retryable"] is True
    assert context["results"] == []
    assert context["unmatched"] == {}
    process.assert_not_awaited()
    enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_a_failed_lastfm_job_records_no_listening_stats():
    """
    GIVEN Last.fm never answers the first page
    WHEN the album job runs
    THEN the job carries no listening totals: it has nothing to report.

    Planted defect: write zeroed totals before checking the fetch.
    """
    job_id, _, _ = await _run_album_job(FakeLastfm({}))

    stats = jobs.progress(job_id)["stats"]
    assert "total_scrobbles" not in stats
    assert "unique_albums" not in stats


@pytest.mark.asyncio
async def test_a_user_not_found_on_a_later_page_ends_the_album_job_as_user_not_found():
    """
    GIVEN the first page answers and a later page is a 404
    WHEN the album job runs
    THEN the job ends as user_not_found, not as a partial run.

    Planted defect: retry a 404 like an outage and drop the page.
    """
    fake = FakeLastfm(
        {1: lastfm_page(_album_plays("Artist", "Album", ["a", "b", "c"], 4), 1, 3)},
        statuses={3: 404},
    )

    job_id, process, _ = await _run_album_job(fake)

    progress = jobs.progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "user_not_found"
    process.assert_not_awaited()


@pytest.mark.asyncio
async def test_one_unreadable_timestamp_does_not_fail_the_album_job():
    """
    GIVEN twelve good scrobbles and one whose timestamp is not a number
    WHEN the album job runs
    THEN the twelve are counted and the job succeeds.

    Planted defect: let the unreadable entry raise out of the aggregation.
    """
    bad = lastfm_track("Artist", "Album", "bad", _at(6, 15))
    bad["date"]["uts"] = "not-a-number"
    tracks = _album_plays("Artist", "Album", ["a", "b", "c"], 4) + [bad]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Artist", "Album")]
    assert album["play_count"] == 12


# ---------------------------------------------------------------------------
# Heatmap pipeline
# ---------------------------------------------------------------------------


def _utc_noon(days_ago):
    """Noon UTC, ``days_ago`` days before today (UTC)."""
    day = datetime.now(UTC).date() - timedelta(days=days_ago)
    return datetime(day.year, day.month, day.day, 12, tzinfo=UTC)


async def _run_heatmap_job(fake):
    """Run the heatmap pipeline against ``fake`` and return its job id."""
    job_id = jobs.create({"username": "parity_user", "mode": "heatmap"})
    with lastfm_edge(fake), patch("scrobblescope.heatmap.cleanup_expired_cache"):
        await _fetch_and_process_heatmap(job_id, "parity_user")
    return job_id


def _run_heatmap_task(fake):
    """Run the heatmap thread entry point, its failure backstop included."""
    job_id = jobs.create({"username": "parity_user", "mode": "heatmap"})
    with (
        lastfm_edge(fake),
        patch("scrobblescope.heatmap.cleanup_expired_cache"),
        patch("scrobblescope.heatmap.release_job_slot"),
    ):
        heatmap_task(job_id)
    return job_id


@pytest.mark.asyncio
async def test_each_scrobble_is_counted_on_its_utc_day():
    """
    GIVEN two scrobbles yesterday, one today and a now-playing entry
    WHEN the heatmap job runs
    THEN the 365-day result counts them per UTC day, with the busiest day, the
    active days and the total.

    Planted defect: leave today out of the window.
    """
    yesterday, today = _utc_noon(1), _utc_noon(0)
    tracks = [
        lastfm_track("A", "B", "C", yesterday),
        lastfm_track("A", "B", "C", yesterday + timedelta(minutes=1)),
        lastfm_track("A", "B", "C", today),
        lastfm_now_playing("A", "B", "Playing Now"),
    ]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    result = jobs.context(job_id)["results"]
    assert len(result["daily_counts"]) == 365
    assert result["daily_counts"][yesterday.date().isoformat()] == 2
    assert result["daily_counts"][today.date().isoformat()] == 1
    assert (result["total_scrobbles"], result["max_count"]) == (3, 2)
    assert jobs.progress(job_id)["stats"]["active_days"] == 2


@pytest.mark.asyncio
async def test_a_scrobble_with_no_album_or_artist_still_counts_on_the_heatmap():
    """
    GIVEN a scrobble whose album and artist are empty
    WHEN the heatmap job runs
    THEN it is counted: the heatmap needs only the date.

    Planted defect: require an album name, as the album calculation does.
    """
    tracks = [lastfm_track("", "", "Untitled", _utc_noon(2))]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    assert jobs.context(job_id)["results"]["total_scrobbles"] == 1


@pytest.mark.asyncio
async def test_the_heatmap_window_is_365_days_ending_today():
    """
    GIVEN a scrobble on the window's first day and one the day before it
    WHEN the heatmap job runs
    THEN only the first is counted.

    Planted defect: start the window one day late.
    """
    first_day, before = _utc_noon(364), _utc_noon(365)
    tracks = [
        lastfm_track("A", "B", "C", first_day),
        lastfm_track("A", "B", "C", before),
    ]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    result = jobs.context(job_id)["results"]
    assert result["total_scrobbles"] == 1
    assert result["daily_counts"][first_day.date().isoformat()] == 1
    assert result["from_date"] == first_day.date().isoformat()


@pytest.mark.asyncio
async def test_a_dropped_page_makes_the_heatmap_partial_and_says_so():
    """
    GIVEN a three-page fetch whose third page never answers
    WHEN the heatmap job runs
    THEN it succeeds from the two pages read, with the heatmap's notice and the
    page counts recorded.

    Planted defect: change the notice's wording.
    """
    fake = FakeLastfm(
        {
            1: lastfm_page([lastfm_track("A", "B", "C", _utc_noon(1))], 1, 3),
            2: lastfm_page([lastfm_track("A", "B", "C", _utc_noon(2))], 2, 3),
        }
    )

    job_id = await _run_heatmap_job(fake)

    context = jobs.context(job_id)
    assert context["results"]["total_scrobbles"] == 2
    stats = context["progress"]["stats"]
    assert stats["partial_data_warning"] == (
        "Note: 1 of 3 Last.fm pages failed (33% data loss). Heatmap may be incomplete."
    )
    assert (stats["pages_expected"], stats["pages_received"]) == (3, 2)


def test_an_unusable_first_page_ends_the_heatmap_as_lastfm_unavailable():
    """
    GIVEN Last.fm never answers the first page
    WHEN the heatmap thread entry point runs
    THEN the job ends in a retryable lastfm_unavailable error with no results.

    Planted defect: report the outage as our own internal error.
    """
    job_id = _run_heatmap_task(FakeLastfm({}))

    progress = jobs.progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "lastfm_unavailable"
    assert progress["retryable"] is True
    assert jobs.context(job_id)["results"] == []


def test_a_user_not_found_on_a_later_page_ends_the_heatmap_as_user_not_found():
    """
    GIVEN the first page answers and a later page is a 404
    WHEN the heatmap thread entry point runs
    THEN the job ends as user_not_found, from Last.fm, not retryable.

    Planted defect: classify every escaped exception as internal_error.
    """
    fake = FakeLastfm(
        {1: lastfm_page([lastfm_track("A", "B", "C", _utc_noon(1))], 1, 3)},
        statuses={3: 404},
    )

    job_id = _run_heatmap_task(fake)

    progress = jobs.progress(job_id)
    assert progress["error_code"] == "user_not_found"
    assert progress["error_source"] == "lastfm"
    assert progress["retryable"] is False


@pytest.mark.asyncio
async def test_one_unreadable_timestamp_does_not_fail_the_heatmap():
    """
    GIVEN a good scrobble and one whose timestamp is not a number
    WHEN the heatmap job runs
    THEN the good one is counted and the job succeeds.

    Planted defect: let the unreadable entry raise out of the aggregation.
    """
    bad = lastfm_track("A", "B", "C", _utc_noon(1))
    bad["date"]["uts"] = "not-a-number"
    tracks = [lastfm_track("A", "B", "C", _utc_noon(2)), bad]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    assert jobs.context(job_id)["results"]["total_scrobbles"] == 1
