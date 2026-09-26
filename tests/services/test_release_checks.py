"""Tests for the live MusicBrainz correction worker (Task 9, Batch 22 WP-3).

Every worker test asserts on the shared ``JOBS`` state the frontend actually
reads -- ``progress.stats.release_check`` and the ``release_check`` field on
each result -- rather than on mock call counts alone, per AGENTS.md Test
Quality Rules.
"""

import logging
from contextlib import ExitStack, contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import release_checks
from scrobblescope.domain import normalize_name
from scrobblescope.release_checks import (
    _release_year,
    _select_candidates,
    _window_end,
    enqueue_release_check,
    run_release_checks,
)
from scrobblescope.repositories import (
    create_job,
    delete_job,
    get_job_context,
    get_job_progress,
    set_job_results,
)
from scrobblescope.unmatched import REASON_BELOW_THRESHOLD, REASON_RELEASE_SCOPE
from tests.helpers import TEST_JOB_PARAMS


def _result(artist, album, release_date="2025-01-01"):
    """Build a minimal result dict shaped like ``_build_results`` output.

    ``_normalized_key`` is included because ``update_job_result``
    (``scrobblescope/repositories.py``) now matches results by that
    precomputed key rather than re-deriving one with ``normalize_name`` --
    see ``_build_results`` in ``scrobblescope/orchestrator/_results.py``,
    which is the real producer this fixture stands in for.
    """
    return {
        "artist": artist,
        "album": album,
        "play_count": 10,
        "release_date": release_date,
        "spotify_id": "sp-id",
        "provider": "spotify",
        "album_url": "https://example.com/album",
        "_normalized_key": normalize_name(artist, album),
    }


def _unmatched(artist, album, provider_release_date, reason_code=REASON_RELEASE_SCOPE):
    """Build a minimal release-scope unmatched entry."""
    return {
        "artist": artist,
        "album": album,
        "reason": "Released in the wrong year",
        "reason_code": reason_code,
        "album_image": None,
        "spotify_id": "sp-id",
        "provider": "spotify",
        "album_url": "https://example.com/album",
        "play_count": 3,
        "provider_release_date": provider_release_date,
    }


def _job_with(results=None, unmatched=None, params=None):
    """Create a job carrying *results* and *unmatched*, and return its id."""
    job_id = create_job(dict(params or TEST_JOB_PARAMS))
    if results is not None:
        set_job_results(job_id, results)
    for entry in unmatched or []:
        from scrobblescope.domain import normalize_name
        from scrobblescope.repositories import add_job_unmatched

        key = "|".join(normalize_name(entry["artist"], entry["album"]))
        add_job_unmatched(job_id, key, entry)
    return job_id


def _fake_session():
    """Return a ``(factory, session)`` pair standing in for aiohttp."""
    session = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=ctx), session


_UNSET = object()


@contextmanager
def _worker_patches(lookup, cached=None, conn=_UNSET, persist=None, extra=()):
    """Patch every external seam the worker touches, in one place.

    ``conn=None`` stands for an unreachable cache DB; the default opens a
    mock connection.
    """
    conn = AsyncMock() if conn is _UNSET else conn
    with ExitStack() as stack:
        for patcher in (
            patch("scrobblescope.release_checks.MUSICBRAINZ_ENABLED", True),
            patch("scrobblescope.release_checks.MUSICBRAINZ_CONTACT", "a@b.c"),
            patch(
                "scrobblescope.release_checks._get_db_connection",
                new_callable=AsyncMock,
                return_value=conn,
            ),
            patch(
                "scrobblescope.release_checks._batch_lookup_original_release",
                new_callable=AsyncMock,
                return_value=cached or {},
            ),
            patch(
                "scrobblescope.release_checks._batch_persist_original_release",
                AsyncMock() if persist is None else persist,
            ),
            patch("scrobblescope.release_checks.lookup_original_release", lookup),
            patch(
                "scrobblescope.release_checks.create_optimized_session",
                _fake_session()[0],
            ),
            *extra,
        ):
            stack.enter_context(patcher)
        yield


# --- Pure candidate-selection helpers ---------------------------------------


def test_window_end_per_release_scope():
    """
    GIVEN each supported release scope
    WHEN the worker computes the target window's last year
    THEN it should match the scope's own upper bound, and be None for "all".
    """
    assert _window_end("same", 2025) == 2025
    assert _window_end("previous", 2025) == 2024
    assert _window_end("decade", 2025, decade="1970s") == 1979
    assert _window_end("custom", 2025, release_year=1991) == 1991
    assert _window_end("all", 2025) is None


def test_window_end_returns_none_on_unusable_inputs():
    """
    GIVEN a scope whose companion parameter is missing or unparseable
    WHEN the worker computes the window
    THEN it should return None rather than raise, disabling move-in checks.
    """
    assert _window_end("decade", 2025, decade=None) is None
    assert _window_end("decade", 2025, decade="nope") is None
    assert _window_end("custom", 2025, release_year=None) is None
    assert _window_end("same", None) is None
    assert _window_end("previous", None) is None


# F-B23-5: `_window_end` restated the same scope table
# `domain._matches_release_criteria` uses; Task 12 moves it to
# `domain.release_window`. This parity test pins `_window_end`'s current
# outputs on every divergence the finding names first, so the refactor has a
# net -- it must keep passing, unchanged.
@pytest.mark.parametrize(
    "release_scope, year, decade, release_year, expected",
    [
        # The four bounded scopes.
        ("same", 2025, None, None, 2025),
        ("previous", 2025, None, None, 2024),
        ("decade", 2025, "1990s", None, 1999),
        ("custom", 2025, None, 1991, 1991),
        # (a) "custom" with no release_year: unbounded.
        ("custom", 2025, None, None, None),
        # (b) "decade" with an unparseable value: unbounded (no window end
        # to move a candidate against).
        ("decade", 2025, "nope", None, None),
        # (c) year as a string: accepted, unlike the filter.
        ("same", "2025", None, None, 2025),
        ("previous", "2025", None, None, 2024),
        # (d) an unknown scope: unbounded.
        ("unknown-scope", 2025, None, None, None),
        # (e) "decade"/"custom" with a falsy companion: unbounded.
        ("decade", 2025, None, None, None),
        ("decade", 2025, "", None, None),
        ("decade", 2025, 0, None, None),
        ("custom", 2025, None, None, None),
        ("custom", 2025, None, "", None),
        ("custom", 2025, None, 0, None),
    ],
)
def test_window_end_parity_before_release_window(
    release_scope, year, decade, release_year, expected
):
    """
    GIVEN every divergence F-B23-5 names plus the four bounded scopes
    WHEN `_window_end` is called before it derives from `domain.release_window`
    THEN it returns today's output -- the net Task 12's refactor must not
        tear, since every case here keeps passing afterward unchanged.
    """
    assert _window_end(release_scope, year, decade, release_year) == expected


def test_release_year_parses_and_rejects():
    """
    GIVEN provider release dates of varying shape
    WHEN the year is extracted
    THEN full dates and bare years parse and anything else returns None.
    """
    assert _release_year("2011-01-31") == 2011
    assert _release_year("1977") == 1977
    assert _release_year("") is None
    assert _release_year(None) is None
    assert _release_year("unknown") is None


def test_select_candidates_takes_results_in_rank_order_then_movable_unmatched():
    """
    GIVEN a finished job with ranked results and a later-dated exclusion
    WHEN candidates are selected
    THEN results come first in rank order, then the movable unmatched album.
    """
    job_id = _job_with(
        results=[_result("Radiohead", "OK Computer"), _result("Blur", "13")],
        unmatched=[_unmatched("Fleetwood Mac", "Rumours", "2031-01-31")],
    )
    candidates = _select_candidates(get_job_context(job_id))

    assert [(c["artist"], c["kind"]) for c in candidates] == [
        ("Radiohead", "result"),
        ("Blur", "result"),
        ("Fleetwood Mac", "unmatched"),
    ]
    assert candidates[0]["key"] == ("radiohead", "ok computer")


def test_select_candidates_excludes_unmatched_that_no_correction_could_move_in():
    """
    GIVEN exclusions that are earlier than the window, undated, or excluded
    for a non-release reason
    WHEN candidates are selected
    THEN none of them is a candidate: an original date is never later than
    the provider's, so no correction could move them in.
    """
    job_id = _job_with(
        results=[],
        unmatched=[
            _unmatched("Earlier", "Album", "1999-01-01"),
            _unmatched("Same Year", "Album", "2025-06-01"),
            _unmatched("Undated", "Album", ""),
            _unmatched("Wrong Reason", "Album", "2031-01-01", REASON_BELOW_THRESHOLD),
        ],
    )
    assert _select_candidates(get_job_context(job_id)) == []


def test_select_candidates_ignores_unmatched_when_scope_is_all():
    """
    GIVEN the "all years" scope, under which nothing is filtered by date
    WHEN candidates are selected
    THEN only results are candidates -- there is no window to move into.
    """
    params = {**TEST_JOB_PARAMS, "release_scope": "all"}
    job_id = _job_with(
        results=[_result("Radiohead", "OK Computer")],
        unmatched=[_unmatched("Fleetwood Mac", "Rumours", "2031-01-31")],
        params=params,
    )
    candidates = _select_candidates(get_job_context(job_id))
    assert [c["kind"] for c in candidates] == ["result"]


def test_select_candidates_on_a_job_without_results_is_empty():
    """
    GIVEN a job whose results were never set (still running, or errored)
    WHEN candidates are selected
    THEN the list is empty rather than raising on a None results payload.
    """
    job_id = create_job(dict(TEST_JOB_PARAMS))
    assert _select_candidates(get_job_context(job_id)) == []


# --- The worker -------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_release_checks_confirms_and_moves_out_without_dropping_results():
    """
    GIVEN two ranked results, one of which MusicBrainz dates outside the window
    WHEN the worker runs
    THEN the moved-out result is marked but stays in the results list, and
    the confirmed one is marked confirmed.
    """
    job_id = _job_with(
        results=[
            _result("Fleetwood Mac", "Rumours", "2025-01-31"),
            _result("Radiohead", "OK Computer", "2025-06-16"),
        ]
    )
    lookup = AsyncMock(
        side_effect=[("mbid-rumours", "1977-02-04"), ("mbid-okc", "2025-06-16")]
    )
    with _worker_patches(lookup):
        await run_release_checks(job_id)

    results = get_job_context(job_id)["results"]
    assert [r["album"] for r in results] == ["Rumours", "OK Computer"]
    assert results[0]["release_check"] == "moved_out"
    assert results[1]["release_check"] == "confirmed"
    stats = get_job_progress(job_id)["stats"]["release_check"]
    assert stats["moved_out"] == 1


class _MissingTableError(Exception):
    """What the correction cache raised before its table existed."""

    sqlstate = "42P01"

    def __init__(self):
        super().__init__('relation "original_release_cache" does not exist')


@pytest.mark.asyncio
async def test_a_missing_correction_table_names_the_migration(caplog):
    """The table this worker writes to has to exist before it is useful.

    Observed on the owner's database on 2026-09-20: original_release_cache
    had never been created, so every finding was looked up, not found,
    fetched again from MusicBrainz at one request per second, and thrown
    away. The run still succeeds -- a correction pass must never take a job
    down -- so the log line is the only place this can be said.
    """
    job_id = _job_with(results=[_result("Fleetwood Mac", "Rumours", "2025-01-31")])
    lookup = AsyncMock(return_value=(None, None))
    conn = AsyncMock()
    conn.fetch = AsyncMock(side_effect=_MissingTableError())

    with caplog.at_level(logging.WARNING):
        with _worker_patches(lookup, conn=conn) as _:
            with patch(
                "scrobblescope.release_checks._batch_lookup_original_release",
                new_callable=AsyncMock,
                side_effect=_MissingTableError(),
            ):
                await run_release_checks(job_id)

    logged = " ".join(record.message for record in caplog.records)
    assert "init_db.py" in logged


@pytest.mark.asyncio
async def test_run_release_checks_records_the_date_behind_each_outcome():
    """
    GIVEN results MusicBrainz moves out, confirms, and cannot date
    WHEN the worker runs
    THEN each result carries the original release date the outcome rests on,
    and the undatable one records None rather than keeping a stale value.

    The results page renders "First released 1977" from this field. Without
    it the moved-out row still shows the provider's reissue date, which is
    the date the correction exists to contradict.
    """
    job_id = _job_with(
        results=[
            _result("Fleetwood Mac", "Rumours", "2025-01-31"),
            _result("Radiohead", "OK Computer", "2025-06-16"),
            _result("Boards of Canada", "Geogaddi", "2025-02-18"),
        ]
    )
    lookup = AsyncMock(
        side_effect=[
            ("mbid-rumours", "1977-02-04"),
            ("mbid-okc", "2025-06-16"),
            (None, None),
        ]
    )
    with _worker_patches(lookup):
        await run_release_checks(job_id)

    results = get_job_context(job_id)["results"]
    assert results[0]["release_check"] == "moved_out"
    assert results[0]["original_release_date"] == "1977-02-04"
    assert results[1]["original_release_date"] == "2025-06-16"
    assert results[2]["release_check"] == "unavailable"
    assert results[2]["original_release_date"] is None


@pytest.mark.asyncio
async def test_run_release_checks_records_the_date_from_a_cached_finding():
    """
    GIVEN a result whose original release date is already cached
    WHEN the worker runs
    THEN it settles that result from the cache, with the same date field the
    live path writes and without spending a request.
    """
    job_id = _job_with(results=[_result("Fleetwood Mac", "Rumours", "2025-01-31")])
    cached = {
        normalize_name("Fleetwood Mac", "Rumours"): {
            "mb_release_group": "mbid-rumours",
            "original_release": "1977-02-04",
        }
    }
    lookup = AsyncMock()
    with _worker_patches(lookup, cached=cached):
        await run_release_checks(job_id)

    results = get_job_context(job_id)["results"]
    assert results[0]["release_check"] == "confirmed"
    assert results[0]["original_release_date"] == "1977-02-04"
    lookup.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_release_checks_reports_the_full_stats_shape():
    """
    GIVEN one result and one movable exclusion whose original lands in-window
    WHEN the worker finishes
    THEN progress.stats.release_check carries exactly the documented keys,
    status "done", and the moved-in album is counted but not inserted.
    """
    job_id = _job_with(
        results=[_result("Radiohead", "OK Computer", "2025-06-16")],
        unmatched=[_unmatched("Fleetwood Mac", "Rumours", "2031-01-31")],
    )
    lookup = AsyncMock(
        side_effect=[("mbid-okc", "2025-06-16"), ("mbid-rumours", "2025-02-04")]
    )
    with _worker_patches(lookup):
        await run_release_checks(job_id)

    context = get_job_context(job_id)
    stats = context["progress"]["stats"]["release_check"]
    assert stats == {
        "status": "done",
        "checked": 2,
        "total": 2,
        "moved_out": 0,
        "moved_in": 1,
    }
    assert [r["album"] for r in context["results"]] == ["OK Computer"]


@pytest.mark.asyncio
async def test_run_release_checks_caps_requests_at_checks_per_job():
    """
    GIVEN more candidates than MUSICBRAINZ_CHECKS_PER_JOB allows
    WHEN the worker runs
    THEN only the cap is requested, the total reflects the cap, and the
    uncapped remainder stays marked "unchecked".
    """
    job_id = _job_with(
        results=[_result(f"Artist {index}", f"Album {index}") for index in range(5)]
    )
    lookup = AsyncMock(return_value=("mbid", "2025-01-01"))
    with _worker_patches(
        lookup,
        extra=[patch("scrobblescope.release_checks.MUSICBRAINZ_CHECKS_PER_JOB", 2)],
    ):
        await run_release_checks(job_id)

    assert lookup.await_count == 2
    results = get_job_context(job_id)["results"]
    assert [r["release_check"] for r in results] == [
        "confirmed",
        "confirmed",
        "unchecked",
        "unchecked",
        "unchecked",
    ]
    stats = get_job_progress(job_id)["stats"]["release_check"]
    assert stats["total"] == 2
    assert stats["checked"] == 2


@pytest.mark.asyncio
async def test_run_release_checks_short_circuits_already_cached_candidates():
    """
    GIVEN one candidate already in original_release_cache (including a
    "checked, nothing found" row) and one that is not
    WHEN the worker runs
    THEN only the uncached album is requested, and the cached rows still
    resolve their release_check without spending a request.
    """
    job_id = _job_with(
        results=[
            _result("Fleetwood Mac", "Rumours", "2025-01-31"),
            _result("Blur", "13", "2025-03-15"),
            _result("Radiohead", "OK Computer", "2025-06-16"),
        ]
    )
    cached = {
        ("fleetwood mac", "rumours"): {
            "mb_release_group": "mbid-rumours",
            "original_release": "2025-01-31",
        },
        ("blur", "13"): {"mb_release_group": None, "original_release": None},
    }
    lookup = AsyncMock(return_value=("mbid-okc", "2025-06-16"))
    persist = AsyncMock()
    with _worker_patches(lookup, cached=cached, persist=persist):
        await run_release_checks(job_id)

    assert lookup.await_count == 1
    assert lookup.await_args[0][1] == "Radiohead"
    results = get_job_context(job_id)["results"]
    assert [r["release_check"] for r in results] == [
        "confirmed",
        "unavailable",
        "confirmed",
    ]
    assert get_job_progress(job_id)["stats"]["release_check"]["total"] == 1


@pytest.mark.asyncio
async def test_run_release_checks_treats_everything_as_pending_when_cache_lookup_fails():
    """
    GIVEN the original-release cache lookup itself raises
    WHEN the worker runs
    THEN it does not abort: every candidate falls back to pending (as if
    nothing were cached) and still gets checked and persisted.
    """
    job_id = _job_with(results=[_result("Radiohead", "OK Computer", "2025-06-16")])
    lookup = AsyncMock(return_value=("mbid-okc", "2025-06-16"))
    with _worker_patches(
        lookup,
        extra=[
            patch(
                "scrobblescope.release_checks._batch_lookup_original_release",
                AsyncMock(side_effect=RuntimeError("cache down")),
            )
        ],
    ):
        await run_release_checks(job_id)

    assert lookup.await_count == 1
    results = get_job_context(job_id)["results"]
    assert results[0]["release_check"] == "confirmed"
    stats = get_job_progress(job_id)["stats"]["release_check"]
    assert stats == {
        "status": "done",
        "checked": 1,
        "total": 1,
        "moved_out": 0,
        "moved_in": 0,
    }


@pytest.mark.asyncio
async def test_run_release_checks_persists_a_nothing_found_row():
    """
    GIVEN MusicBrainz returns no trusted match
    WHEN the worker records the finding
    THEN a null row is still written to original_release_cache so a later
    job skips the album, and the result is marked unavailable.
    """
    job_id = _job_with(results=[_result("Obscure", "Demo", "2025-01-01")])
    lookup = AsyncMock(return_value=(None, None))
    persist = AsyncMock()
    with _worker_patches(lookup, persist=persist):
        await run_release_checks(job_id)

    assert persist.await_args[0][1] == [("obscure", "demo", None, None)]
    results = get_job_context(job_id)["results"]
    assert results[0]["release_check"] == "unavailable"


@pytest.mark.asyncio
async def test_run_release_checks_stops_when_the_job_is_deleted_mid_run():
    """
    GIVEN a job that expires (or is deleted) after the first check
    WHEN the worker reaches the next candidate
    THEN it stops rather than spending the remaining MusicBrainz budget on
    a job nobody can read.
    """
    job_id = _job_with(
        results=[_result(f"Artist {index}", f"Album {index}") for index in range(4)]
    )

    async def _lookup_then_delete(session, artist, album, **kwargs):
        delete_job(job_id)
        return ("mbid", "2025-01-01")

    lookup = AsyncMock(side_effect=_lookup_then_delete)
    with _worker_patches(lookup):
        await run_release_checks(job_id)

    assert lookup.await_count == 1
    assert get_job_context(job_id) is None


@pytest.mark.asyncio
async def test_run_release_checks_marks_skipped_when_musicbrainz_is_disabled():
    """
    GIVEN MUSICBRAINZ_ENABLED is False
    WHEN the worker runs
    THEN the status is "skipped", no request is made, and no DB connection
    is opened.
    """
    job_id = _job_with(results=[_result("Radiohead", "OK Computer")])
    lookup = AsyncMock()
    connect = AsyncMock()
    with (
        patch("scrobblescope.release_checks.MUSICBRAINZ_ENABLED", False),
        patch("scrobblescope.release_checks.lookup_original_release", lookup),
        patch("scrobblescope.release_checks._get_db_connection", connect),
    ):
        await run_release_checks(job_id)

    lookup.assert_not_awaited()
    connect.assert_not_awaited()
    assert get_job_progress(job_id)["stats"]["release_check"] == {
        "status": "skipped",
        "checked": 0,
        "total": 0,
        "moved_out": 0,
        "moved_in": 0,
    }


@pytest.mark.asyncio
async def test_run_release_checks_runs_without_a_db_connection(caplog):
    """
    GIVEN the cache DB is unreachable
    WHEN the worker runs
    THEN it still asks MusicBrainz and records the outcome on the open job,
    persisting nothing: the cache is how findings are reused, not a
    precondition for showing one (F-B22-8).
    """
    job_id = _job_with(results=[_result("Radiohead", "OK Computer")])
    lookup = AsyncMock(return_value=("rg-1", "1997-05-21"))
    persist = AsyncMock()
    with (
        caplog.at_level(logging.INFO),
        _worker_patches(lookup, conn=None, persist=persist),
    ):
        await run_release_checks(job_id)

    lookup.assert_awaited_once()
    persist.assert_not_awaited()
    assert get_job_progress(job_id)["stats"]["release_check"] == {
        "status": "done",
        "checked": 1,
        "total": 1,
        "moved_out": 1,
        "moved_in": 0,
    }
    result = get_job_context(job_id)["results"][0]
    assert result["release_check"] == "moved_out"
    assert result["original_release_date"] == "1997-05-21"
    assert "without the cache DB" in caplog.text


@pytest.mark.asyncio
async def test_run_release_checks_without_a_db_connection_survives_a_lookup_error():
    """
    GIVEN no cache connection and MusicBrainz raising part-way through
    WHEN the worker unwinds
    THEN the job still ends "done" and nothing tries to close a connection
    that was never opened.
    """
    job_id = _job_with(results=[_result("Radiohead", "OK Computer")])
    lookup = AsyncMock(side_effect=RuntimeError("boom"))
    with _worker_patches(lookup, conn=None):
        await run_release_checks(job_id)

    assert get_job_progress(job_id)["stats"]["release_check"]["status"] == "done"


@pytest.mark.asyncio
async def test_run_release_checks_finishes_without_a_db_trip_when_nothing_qualifies(
    caplog,
):
    """
    GIVEN a finished job with no results and no movable exclusion
    WHEN the worker runs
    THEN it reports "done" with a zero total and never opens a connection --
    an empty candidate list is a normal outcome, not a skip.
    """
    job_id = _job_with(results=[], unmatched=[_unmatched("Early", "Album", "1999")])
    lookup = AsyncMock()
    connect = AsyncMock()
    with (
        patch("scrobblescope.release_checks.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.release_checks.lookup_original_release", lookup),
        patch("scrobblescope.release_checks._get_db_connection", connect),
    ):
        await run_release_checks(job_id)

    connect.assert_not_awaited()
    lookup.assert_not_awaited()
    assert get_job_progress(job_id)["stats"]["release_check"] == {
        "status": "done",
        "checked": 0,
        "total": 0,
        "moved_out": 0,
        "moved_in": 0,
    }
    assert f"Release checks starting for job {job_id}: 0 candidates" in caplog.text
    assert f"Release checks finished for job {job_id}: 0 checked" in caplog.text


@pytest.mark.asyncio
async def test_run_release_checks_on_a_missing_job_is_a_noop():
    """
    GIVEN a job id that no longer exists
    WHEN the worker runs
    THEN it returns without opening a connection or making a request.
    """
    connect = AsyncMock()
    lookup = AsyncMock()
    with (
        patch("scrobblescope.release_checks._get_db_connection", connect),
        patch("scrobblescope.release_checks.lookup_original_release", lookup),
    ):
        await run_release_checks("does-not-exist")

    connect.assert_not_awaited()
    lookup.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_release_checks_closes_the_connection_when_a_lookup_raises():
    """
    GIVEN MusicBrainz raises part-way through the candidate list
    WHEN the worker unwinds
    THEN the DB connection is still closed and the job keeps a terminal
    status rather than being left "running" forever.
    """
    job_id = _job_with(results=[_result("Radiohead", "OK Computer")])
    conn = AsyncMock()
    lookup = AsyncMock(side_effect=RuntimeError("boom"))
    with _worker_patches(lookup, conn=conn):
        await run_release_checks(job_id)

    conn.close.assert_awaited_once()
    assert get_job_progress(job_id)["stats"]["release_check"]["status"] == "done"


# --- Queue and thread lifecycle ---------------------------------------------


def test_session_starts_with_no_musicbrainz_contact():
    """
    GIVEN the test session, whatever the developer's .env or shell holds
    WHEN a test reads the contact the release-check worker is gated on
    THEN none is configured, so an unpatched happy-path pipeline test is
    skipped rather than starting the real worker thread. conftest.py forces
    this; with it removed, any machine with a configured contact reached the
    network and raced the queue-order test below.
    """
    job_id = create_job(dict(TEST_JOB_PARAMS))
    queued_before = release_checks._JOB_QUEUE.qsize()

    assert not release_checks.MUSICBRAINZ_CONTACT
    with patch("scrobblescope.release_checks._ensure_worker_started") as started:
        assert enqueue_release_check(job_id) is False

    started.assert_not_called()
    assert release_checks._JOB_QUEUE.qsize() == queued_before


def test_enqueue_release_check_queues_jobs_in_order():
    """
    GIVEN MusicBrainz is configured
    WHEN two jobs are enqueued
    THEN both reach the shared queue, in the order they finished, and each
    enqueue asks for the worker thread.
    """
    job_a = create_job(dict(TEST_JOB_PARAMS))
    job_b = create_job(dict(TEST_JOB_PARAMS))
    started = MagicMock()
    with (
        patch("scrobblescope.release_checks.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.release_checks.MUSICBRAINZ_CONTACT", "a@b.c"),
        patch("scrobblescope.release_checks._ensure_worker_started", started),
    ):
        assert enqueue_release_check(job_a) is True
        assert enqueue_release_check(job_b) is True

    assert started.call_count == 2
    assert [release_checks._JOB_QUEUE.get_nowait() for _ in range(2)] == [job_a, job_b]


def test_enqueue_release_check_skips_when_musicbrainz_is_unconfigured():
    """
    GIVEN no MUSICBRAINZ_CONTACT (MusicBrainz requires one in the User-Agent)
    WHEN a finished job is handed to the worker
    THEN nothing is queued, no thread starts, and the job is marked skipped
    so the results page can say so.
    """
    job_id = create_job(dict(TEST_JOB_PARAMS))
    started = MagicMock()
    queued_before = release_checks._JOB_QUEUE.qsize()
    with (
        patch("scrobblescope.release_checks.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.release_checks.MUSICBRAINZ_CONTACT", None),
        patch("scrobblescope.release_checks._ensure_worker_started", started),
    ):
        assert enqueue_release_check(job_id) is False

    started.assert_not_called()
    assert release_checks._JOB_QUEUE.qsize() == queued_before
    assert get_job_progress(job_id)["stats"]["release_check"]["status"] == "skipped"


def test_enqueue_release_check_rejects_an_empty_job_id():
    """
    GIVEN no job id at all
    WHEN enqueue_release_check is called
    THEN it refuses without queueing anything, rather than parking a None
    the worker would have to defend against.
    """
    queued_before = release_checks._JOB_QUEUE.qsize()
    with patch("scrobblescope.release_checks._ensure_worker_started", MagicMock()):
        assert enqueue_release_check(None) is False
    assert release_checks._JOB_QUEUE.qsize() == queued_before


def test_ensure_worker_started_starts_exactly_one_live_thread():
    """
    GIVEN the worker thread is already running
    WHEN another job asks for it
    THEN no second thread is created: one thread serves the whole process,
    because MusicBrainz's one-request-per-second cap is per IP.
    """
    live_thread = MagicMock()
    live_thread.is_alive.return_value = True
    original = release_checks._worker_thread
    try:
        release_checks._worker_thread = None
        with patch(
            "scrobblescope.release_checks.threading.Thread", return_value=live_thread
        ) as thread_cls:
            release_checks._ensure_worker_started()
            release_checks._ensure_worker_started()

        assert thread_cls.call_count == 1
        assert thread_cls.call_args.kwargs["daemon"] is True
        live_thread.start.assert_called_once()
        assert release_checks._worker_thread is live_thread
    finally:
        release_checks._worker_thread = original


# --- Task 13: the three worker log lines (F-B23-6) --------------------------


@pytest.mark.asyncio
async def test_run_release_checks_logs_its_start_with_the_candidate_count(caplog):
    """
    GIVEN a job with two results
    WHEN the worker starts
    THEN it logs the candidate count at INFO before any lookup, naming no
    artist or album.
    """
    job_id = _job_with(
        results=[
            _result("Radiohead", "OK Computer"),
            _result("Pulp", "Different Class"),
        ]
    )
    lookup = AsyncMock(return_value=(None, None))
    with caplog.at_level(logging.INFO), _worker_patches(lookup):
        await run_release_checks(job_id)

    start_lines = [r for r in caplog.records if "starting" in r.getMessage()]
    assert len(start_lines) == 1
    assert start_lines[0].levelno == logging.INFO
    message = start_lines[0].getMessage()
    assert "2 candidates" in message
    assert "Radiohead" not in message
    assert "OK Computer" not in message


@pytest.mark.asyncio
async def test_run_release_checks_logs_its_finish_with_moved_out_and_moved_in_counts(
    caplog,
):
    """
    GIVEN a job with two results that both move out of the window and one
    excluded album whose original release moves it back in
    WHEN the worker finishes
    THEN it logs the checked, moved-out and moved-in counts at INFO -- as
    distinct, non-zero numbers, so the two corrected findings MusicBrainz
    can return (a result rewritten in place, and an exclusion that would now
    qualify) are both visible, not just the one the worker rewrote -- naming
    no artist or album.
    """
    job_id = _job_with(
        results=[
            _result("Radiohead", "OK Computer"),
            _result("Pulp", "Different Class"),
        ],
        unmatched=[_unmatched("Fleetwood Mac", "Rumours", "2031-01-31")],
    )
    lookup = AsyncMock(
        side_effect=[
            ("mbid-okc", "1990-01-01"),
            ("mbid-diffclass", "1985-01-01"),
            ("mbid-rumours", "2025-02-04"),
        ]
    )
    with caplog.at_level(logging.INFO), _worker_patches(lookup):
        await run_release_checks(job_id)

    finish_lines = [r for r in caplog.records if "finished" in r.getMessage()]
    assert len(finish_lines) == 1
    assert finish_lines[0].levelno == logging.INFO
    message = finish_lines[0].getMessage()
    assert "3 checked" in message
    assert "2 moved out" in message
    assert "1 moved in" in message
    assert "Radiohead" not in message
    assert "OK Computer" not in message
    assert "Pulp" not in message
    assert "Different Class" not in message
    assert "Fleetwood Mac" not in message
    assert "Rumours" not in message


def test_enqueue_release_check_names_musicbrainz_disabled_in_the_skip_line(caplog):
    """
    GIVEN MusicBrainz is disabled
    WHEN a job is handed to the worker
    THEN the skip line names MusicBrainz as disabled, not the contact.
    """
    job_id = create_job(dict(TEST_JOB_PARAMS))
    with (
        caplog.at_level(logging.INFO),
        patch("scrobblescope.release_checks.MUSICBRAINZ_ENABLED", False),
        patch("scrobblescope.release_checks.MUSICBRAINZ_CONTACT", "a@b.c"),
    ):
        assert enqueue_release_check(job_id) is False

    assert "MusicBrainz is disabled" in caplog.text
    assert "MUSICBRAINZ_CONTACT" not in caplog.text


def test_enqueue_release_check_names_the_missing_contact_in_the_skip_line(caplog):
    """
    GIVEN MusicBrainz is enabled but MUSICBRAINZ_CONTACT is unset
    WHEN a job is handed to the worker
    THEN the skip line names the missing contact setting, not "disabled".
    """
    job_id = create_job(dict(TEST_JOB_PARAMS))
    with (
        caplog.at_level(logging.INFO),
        patch("scrobblescope.release_checks.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.release_checks.MUSICBRAINZ_CONTACT", None),
    ):
        assert enqueue_release_check(job_id) is False

    assert "MUSICBRAINZ_CONTACT is unset" in caplog.text
