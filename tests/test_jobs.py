# tests/test_jobs.py
"""The job module's lifecycle, tested at its interface only.

Every test drives ``scrobblescope.jobs`` through its public verbs and reads the
outcome back through its public reads, never by reaching into a store's
dict. That is what lets a second storage adapter run this same suite: add its
factory to ``STORE_FACTORIES`` and every rule below is checked against it.
"""

import logging

import pytest

from scrobblescope import jobs
from scrobblescope.config import JOB_TTL_SECONDS
from scrobblescope.errors import ERROR_CODES
from tests.helpers import TEST_JOB_PARAMS

# One entry per storage adapter. The Postgres adapter adds its own here.
STORE_FACTORIES = {"memory": jobs.MemoryJobStore}


@pytest.fixture(autouse=True, params=list(STORE_FACTORIES))
def store(request):
    """Run each test against a fresh store of each adapter."""
    previous = jobs.use_store(STORE_FACTORIES[request.param]())
    yield jobs._store
    jobs.use_store(previous)


class Clock:
    """A settable stand-in for the wall clock the job module reads."""

    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    fake = Clock(1_000_000.0)
    monkeypatch.setattr(jobs, "_now", fake)
    return fake


def _new_job():
    return jobs.create(dict(TEST_JOB_PARAMS))


def _lastfm_phase(current=23, total=102):
    return {
        "key": "lastfm_fetch",
        "label": "Fetching scrobbles",
        "unit": "page",
        "current": current,
        "total": total,
    }


# --- create / delete / reset -------------------------------------------------


def test_create_returns_unique_ids_and_a_pristine_job():
    """
    GIVEN two jobs created with identical params
    THEN their ids differ, and each starts at 0% with no error, no stats, no
    results, no unmatched albums, and its params intact.
    """
    first, second = _new_job(), _new_job()
    assert first != second

    ctx = jobs.context(first)
    assert ctx["progress"] == {
        "progress": 0,
        "message": "Initializing...",
        "error": False,
        "stats": {},
    }
    assert ctx["results"] is None
    assert ctx["unmatched"] == {}
    assert ctx["params"] == TEST_JOB_PARAMS


def test_delete_removes_a_job_and_ignores_a_missing_one(store):
    job_id = _new_job()
    jobs.delete(job_id)
    assert jobs.context(job_id) is None

    jobs.delete("nonexistent_id_xyz")  # must not raise
    assert "nonexistent_id_xyz" not in store.ids()


def test_reset_returns_the_job_to_its_initial_state_and_keeps_params():
    job_id = _new_job()
    jobs.record_stat(job_id, "albums_found", 3)
    jobs.record_unmatched(job_id, "a|b", {"artist": "a"})
    jobs.fail(job_id, "lastfm_unavailable")

    assert jobs.reset(job_id) is True

    ctx = jobs.context(job_id)
    assert ctx["progress"] == {
        "progress": 0,
        "message": "Initializing...",
        "error": False,
        "stats": {},
    }
    assert ctx["results"] is None
    assert ctx["unmatched"] == {}
    assert ctx["params"] == TEST_JOB_PARAMS


def test_reset_can_carry_a_message_and_reports_a_missing_job():
    job_id = _new_job()
    assert jobs.reset(job_id, "Reset successful") is True
    progress = jobs.progress(job_id)
    assert progress["message"] == "Reset successful"
    assert progress["error"] is False
    assert jobs.reset("nonexistent_job_id") is False


# --- advance / start / report_phase -----------------------------------------


def test_advance_updates_only_its_own_job():
    id_a, id_b = _new_job(), _new_job()
    jobs.advance(id_a, 75, "Almost done")
    jobs.advance(id_b, 10, "Starting")

    assert jobs.progress(id_a)["progress"] == 75
    assert jobs.progress(id_a)["message"] == "Almost done"
    assert jobs.progress(id_b)["progress"] == 10
    assert jobs.progress(id_b)["message"] == "Starting"


def test_advance_on_a_missing_job_returns_false():
    assert jobs.advance("nonexistent_job_id", 50, "test") is False


def test_advance_copies_the_phase_and_a_plain_advance_clears_it():
    """
    A phase the caller keeps mutating, or a view a reader mutates, never
    reaches stored state; advancing without a phase drops the old one so a
    stale "page 23 of 102" cannot outlive its step.
    """
    job_id = _new_job()
    phase = _lastfm_phase()
    jobs.advance(job_id, 20, "Fetching scrobbles", phase=phase)
    phase["current"] = 99
    assert jobs.progress(job_id)["phase"]["current"] == 23
    assert jobs.context(job_id)["progress"]["phase"]["current"] == 23

    jobs.progress(job_id)["phase"]["current"] = 77
    jobs.context(job_id)["progress"]["phase"]["current"] = 88
    assert jobs.progress(job_id)["phase"]["current"] == 23

    jobs.advance(job_id, 30, "Counting")
    assert "phase" not in jobs.progress(job_id)
    assert "phase" not in jobs.context(job_id)["progress"]


@pytest.mark.parametrize(
    "phase, done, total, expected",
    [
        (jobs.ALBUM_LASTFM_FETCH, 51, 102, 12),
        (jobs.ALBUM_LASTFM_FETCH, 102, 102, 20),
        (jobs.SPOTIFY_SEARCH, 1, 3, 26),
        (jobs.SPOTIFY_DETAILS, 2, 3, 53),
        (jobs.DEEZER_FALLBACK, 1, 4, 63),
        (jobs.HEATMAP_LASTFM_FETCH, 1, 7, 15),
        (jobs.HEATMAP_LASTFM_FETCH, 7, 7, 80),
        (jobs.SPOTIFY_SEARCH, 0, 0, 20),
    ],
)
def test_report_phase_derives_the_percent_from_the_band(phase, done, total, expected):
    """The band's start plus its span scaled by done/total, floored; a zero
    total counts as one so an empty phase sits at its band's start."""
    job_id = _new_job()
    assert jobs.report_phase(job_id, phase, done, total, "msg") is True

    progress = jobs.progress(job_id)
    assert progress["progress"] == expected
    assert progress["message"] == "msg"
    assert progress["phase"] == {
        "key": phase.key,
        "label": phase.label,
        "unit": phase.unit,
        "current": done,
        "total": total,
    }


def test_the_five_bands_tile_the_bar_without_overlap():
    """Album phases hand the bar on to each other; nothing double-counts."""
    bands = [
        jobs.ALBUM_LASTFM_FETCH.band,
        jobs.SPOTIFY_SEARCH.band,
        jobs.SPOTIFY_DETAILS.band,
        jobs.DEEZER_FALLBACK.band,
    ]
    assert [(b.start, b.start + b.span) for b in bands] == [
        (5, 20),
        (20, 40),
        (40, 60),
        (60, 75),
    ]
    assert jobs.HEATMAP_LASTFM_FETCH.band == (5, 75)


def test_start_clears_stats_phase_and_error_and_sets_the_message():
    job_id = _new_job()
    jobs.record_stat(job_id, "old", 1)
    jobs.report_phase(job_id, jobs.SPOTIFY_SEARCH, 1, 2, "x")
    jobs.fail(job_id, "lastfm_rate_limited")

    assert jobs.start(job_id, "Initializing heatmap...") is True

    progress = jobs.progress(job_id)
    assert progress == {
        "progress": 0,
        "message": "Initializing heatmap...",
        "error": False,
        "stats": {},
    }


# --- stats / unmatched -------------------------------------------------------


def test_record_stat_stores_each_key_and_reports_a_missing_job():
    job_id = _new_job()
    jobs.record_stat(job_id, "scrobbles_fetched", 1234)
    jobs.record_stat(job_id, "albums_found", 42)

    stats = jobs.progress(job_id)["stats"]
    assert stats == {"scrobbles_fetched": 1234, "albums_found": 42}
    assert jobs.record_stat("nonexistent_job_id", "k", 1) is False


def test_record_stat_replaces_a_dict_value_whole_and_copies_it():
    """
    The correction worker records its whole state under one key: each write
    replaces the last, and its own later mutation of the dict it passed
    cannot reach stored state.
    """
    job_id = _new_job()
    jobs.record_stat(job_id, "albums_found", 42)
    state = {"status": "running", "checked": 1, "total": 3}
    jobs.record_stat(job_id, "release_check", state)
    state["checked"] = 99

    assert jobs.progress(job_id)["stats"]["release_check"]["checked"] == 1

    jobs.record_stat(job_id, "release_check", {"status": "done"})
    stats = jobs.progress(job_id)["stats"]
    assert stats["release_check"] == {"status": "done"}
    assert stats["albums_found"] == 42


def test_record_unmatched_keys_entries_and_reports_a_missing_job():
    job_id = _new_job()
    assert jobs.record_unmatched(job_id, "a|b", {"artist": "a"}) is True
    assert jobs.record_unmatched(job_id, "c|d", {"artist": "c"}) is True

    assert jobs.unmatched(job_id) == {"a|b": {"artist": "a"}, "c|d": {"artist": "c"}}
    assert jobs.record_unmatched("nonexistent_job_id", "k", {}) is False


# --- succeed / fail: one ending, never both ---------------------------------


def test_succeed_stores_results_and_the_completion_in_one_write():
    job_id = _new_job()
    jobs.report_phase(job_id, jobs.SPOTIFY_SEARCH, 1, 2, "searching")
    results = [{"artist": "A", "album": "B"}]

    assert jobs.succeed(job_id, results, "Done! Found 1 albums.") is True

    ctx = jobs.context(job_id)
    assert ctx["results"] == results
    assert ctx["progress"]["progress"] == 100
    assert ctx["progress"]["message"] == "Done! Found 1 albums."
    assert ctx["progress"]["error"] is False
    assert "phase" not in ctx["progress"]


def test_succeed_clears_an_earlier_failure():
    """A job holds results or an error, never both."""
    job_id = _new_job()
    jobs.fail(job_id, "lastfm_rate_limited", retry_after=30)
    # The run is under way again (an advance is a write on a failed job's
    # record): only then may it end a second time.
    jobs.advance(job_id, 50, "Retrying")

    jobs.succeed(job_id, [{"artist": "A"}], "Done")

    progress = jobs.progress(job_id)
    assert progress["error"] is False
    for field in ("error_code", "error_source", "retryable", "retry_after"):
        assert field not in progress
    assert jobs.context(job_id)["results"] == [{"artist": "A"}]


def test_succeed_on_a_missing_job_returns_false():
    assert jobs.succeed("nonexistent_job_id", [], "Done") is False


def test_fail_sets_the_classified_fields():
    job_id = _new_job()
    assert jobs.fail(job_id, "lastfm_unavailable") is True

    progress = jobs.progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "lastfm_unavailable"
    assert progress["error_source"] == "lastfm"
    assert progress["retryable"] is True
    assert progress["progress"] == 100
    assert progress["message"] == ERROR_CODES["lastfm_unavailable"]["message"]
    assert "retry_after" not in progress


def test_fail_names_the_user_and_carries_retry_after():
    job_id = _new_job()
    jobs.fail(job_id, "user_not_found", username="ghost", retry_after=12)

    progress = jobs.progress(job_id)
    assert progress["retryable"] is False
    assert "ghost" in progress["message"]
    assert progress["error_code"] == "user_not_found"
    assert progress["retry_after"] == 12


def test_fail_replaces_results_with_an_empty_list_and_clears_the_phase():
    """A job holds results or an error, never both."""
    job_id = _new_job()
    jobs.succeed(job_id, [{"artist": "A"}], "Done")
    jobs.advance(job_id, 50, "again", phase=_lastfm_phase())

    jobs.fail(job_id, "spotify_unavailable")

    ctx = jobs.context(job_id)
    assert ctx["results"] == []
    assert "phase" not in ctx["progress"]


def test_fail_on_a_missing_job_returns_false():
    assert jobs.fail("nonexistent_job_id", "internal_error") is False


def test_fail_internal_error_replaces_results_and_is_not_retryable():
    job_id = _new_job()
    jobs.succeed(job_id, [{"artist": "A"}], "Done")
    jobs.advance(job_id, 50, "again")

    assert jobs.fail(job_id, "internal_error") is True

    ctx = jobs.context(job_id)
    assert ctx["results"] == []
    progress = ctx["progress"]
    assert progress["message"].startswith("Something went wrong on our side")
    assert progress["error"] is True
    assert progress["error_code"] == "internal_error"
    assert progress["retryable"] is False
    assert progress["progress"] == 100
    assert progress["error_source"] == "internal"


# --- update_result -----------------------------------------------------------


def _two_albums():
    return [
        {
            "artist": "Radiohead",
            "album": "OK Computer",
            "play_count": 50,
            "_normalized_key": ("radiohead", "ok computer"),
        },
        {
            "artist": "Blur",
            "album": "13",
            "play_count": 20,
            "_normalized_key": ("blur", "13"),
        },
    ]


def test_update_result_merges_into_the_matching_result_and_renews_the_lease(clock):
    """
    Only the matching entry gains the fields; order and length are kept; the
    job's lease renews, so the job is still alive a whole TTL after the update
    rather than after its previous write.
    """
    job_id = _new_job()
    jobs.succeed(job_id, _two_albums(), "Done")

    clock.now += JOB_TTL_SECONDS - 10
    assert jobs.update_result(job_id, ("blur", "13"), {"release_check": "moved_out"})

    results = jobs.context(job_id)["results"]
    assert len(results) == 2
    assert results[1] == {
        "artist": "Blur",
        "album": "13",
        "play_count": 20,
        "_normalized_key": ("blur", "13"),
        "release_check": "moved_out",
    }
    assert "release_check" not in results[0]

    clock.now += JOB_TTL_SECONDS - 10  # past the first lease, inside the renewed one
    jobs.expire_stale()
    assert jobs.context(job_id) is not None


def test_update_result_matches_the_precomputed_key_not_the_displayed_name():
    job_id = _new_job()
    jobs.succeed(
        job_id,
        [
            {
                "artist": "Radiohead",
                "album": "OK Computer (Deluxe Edition)",
                "_normalized_key": ("radiohead", "ok computer"),
            }
        ],
        "Done",
    )

    assert jobs.update_result(job_id, ("radiohead", "ok computer"), {"x": 1}) is True
    assert jobs.context(job_id)["results"][0]["x"] == 1


def test_update_result_accepts_a_list_key():
    """A key that came back through JSON is a list; it still matches."""
    job_id = _new_job()
    jobs.succeed(job_id, _two_albums(), "Done")
    assert jobs.update_result(job_id, ["blur", "13"], {"x": 1}) is True


def test_update_result_with_no_match_changes_nothing_and_does_not_renew(clock):
    """
    A miss over a full 500-entry list leaves every result unchanged and
    leaves the lease where it was, so a worker that keeps missing cannot keep
    a job alive.
    """
    job_id = _new_job()
    results = [
        {
            "artist": f"Artist {i}",
            "album": f"Album {i}",
            "play_count": i,
            "_normalized_key": (f"artist {i}", f"album {i}"),
        }
        for i in range(500)
    ]
    jobs.succeed(job_id, results, "Done")
    expected = [dict(r) for r in results]

    clock.now += JOB_TTL_SECONDS - 10
    assert jobs.update_result(job_id, ("nobody", "nothing at all"), {"z": 1}) is False
    assert jobs.context(job_id)["results"] == expected

    clock.now += 20  # past the original lease
    jobs.expire_stale()
    assert jobs.context(job_id) is None


def test_update_result_without_a_results_list_or_job_returns_false():
    job_id = _new_job()  # results is still None

    assert jobs.update_result(job_id, ("blur", "13"), {"z": 1}) is False
    assert jobs.update_result("nonexistent_job_id", ("blur", "13"), {"z": 1}) is False
    assert jobs.context(job_id)["results"] is None


def test_update_result_never_normalizes_names(monkeypatch):
    """The lookup compares precomputed tuples; no per-entry normalization."""
    from scrobblescope import domain

    calls = []
    real = domain.normalize_name
    monkeypatch.setattr(
        domain, "normalize_name", lambda *a: calls.append(a) or real(*a)
    )
    job_id = _new_job()
    jobs.succeed(job_id, _two_albums(), "Done")

    assert jobs.update_result(job_id, ("blur", "13"), {"hit": True}) is True
    assert jobs.update_result(job_id, ("nobody", "nothing"), {"miss": True}) is False
    assert calls == []


# --- reads -------------------------------------------------------------------


def test_reads_of_a_missing_job_return_none():
    assert jobs.progress("nonexistent_job_id") is None
    assert jobs.unmatched("nonexistent_job_id") is None
    assert jobs.context("nonexistent_job_id") is None


def test_context_isolates_dict_results_from_callers():
    """
    Heatmap results are a dict: mutating the returned one, or its nested
    daily_counts, must not reach stored state (F-B18-8).
    """
    job_id = _new_job()
    jobs.succeed(
        job_id,
        {
            "username": "testuser",
            "total_scrobbles": 5,
            "daily_counts": {"2026-05-01": 3, "2026-05-02": 2},
        },
        "Heatmap ready!",
    )

    ctx = jobs.context(job_id)
    ctx["results"]["total_scrobbles"] = 999
    ctx["results"]["daily_counts"]["2026-05-01"] = 999
    ctx["results"]["daily_counts"]["2026-05-03"] = 7

    fresh = jobs.context(job_id)["results"]
    assert fresh["total_scrobbles"] == 5
    assert fresh["daily_counts"] == {"2026-05-01": 3, "2026-05-02": 2}


def test_context_isolates_the_results_list_and_unmatched_and_params():
    job_id = _new_job()
    jobs.succeed(job_id, [{"artist": "A"}], "Done")
    jobs.record_unmatched(job_id, "a|b", {"artist": "a"})

    ctx = jobs.context(job_id)
    ctx["results"].append({"artist": "intruder"})
    ctx["unmatched"]["x|y"] = {}
    ctx["params"]["username"] = "changed"
    jobs.progress(job_id)["stats"]["injected"] = 1

    fresh = jobs.context(job_id)
    assert fresh["results"] == [{"artist": "A"}]
    assert list(fresh["unmatched"]) == ["a|b"]
    assert fresh["params"] == TEST_JOB_PARAMS
    assert fresh["progress"]["stats"] == {}


# --- lease: TTL, writers renew, readers do not -------------------------------


def test_expire_stale_removes_a_job_past_its_ttl_and_keeps_a_fresh_one(clock):
    old, fresh = _new_job(), None
    clock.now += JOB_TTL_SECONDS + 60
    fresh = _new_job()

    jobs.expire_stale()

    assert jobs.progress(old) is None
    assert jobs.progress(fresh) is not None


def test_a_write_renews_the_lease(clock):
    job_id = _new_job()
    clock.now += JOB_TTL_SECONDS - 10
    jobs.advance(job_id, 10, "still working")

    clock.now += JOB_TTL_SECONDS - 10  # past the creation lease, inside the new one
    jobs.expire_stale()

    assert jobs.progress(job_id) is not None


@pytest.mark.parametrize(
    "read",
    [jobs.progress, jobs.unmatched, jobs.context],
    ids=["progress", "unmatched", "context"],
)
def test_reading_a_job_does_not_renew_its_lease(read, clock):
    """
    GIVEN a job whose last write is older than JOB_TTL_SECONDS
    WHEN a reader reads it and cleanup then runs
    THEN the job is reaped: reading is not activity (F-SWE-6).
    """
    job_id = _new_job()
    clock.now += JOB_TTL_SECONDS + 60

    assert read(job_id) is not None  # the read itself still works

    jobs.expire_stale()

    assert jobs.progress(job_id) is None


# --- mark_interrupted --------------------------------------------------------


def test_mark_interrupted_fails_only_the_unfinished_jobs():
    """
    A restart strands jobs that were mid-run: they end as a retryable
    ``job_interrupted`` failure with empty results. A job that already
    succeeded, or already failed, is left exactly as it was.
    """
    running = _new_job()
    jobs.report_phase(running, jobs.SPOTIFY_SEARCH, 1, 2, "searching")
    fresh = _new_job()
    succeeded = _new_job()
    jobs.succeed(succeeded, [{"artist": "A"}], "Done")
    failed = _new_job()
    jobs.fail(failed, "lastfm_unavailable")
    before = {job_id: jobs.context(job_id) for job_id in (succeeded, failed)}

    assert jobs.mark_interrupted() == 2

    for job_id in (running, fresh):
        ctx = jobs.context(job_id)
        info = ERROR_CODES["job_interrupted"]
        assert ctx["results"] == []
        assert ctx["progress"]["error"] is True
        assert ctx["progress"]["error_code"] == "job_interrupted"
        assert ctx["progress"]["error_source"] == info["source"]
        assert ctx["progress"]["retryable"] is True
        assert ctx["progress"]["progress"] == 100
        assert ctx["progress"]["message"] == info["message"]
        assert "phase" not in ctx["progress"]
    for job_id, ctx in before.items():
        assert jobs.context(job_id) == ctx


def test_mark_interrupted_on_an_empty_store_is_a_noop():
    assert jobs.mark_interrupted() == 0


def test_use_store_returns_the_store_it_replaced(store):
    other = jobs.MemoryJobStore()
    assert jobs.use_store(other) is store
    job_id = _new_job()
    assert other.ids() == [job_id]
    assert store.ids() == []
    jobs.use_store(store)


# --- a job ends exactly one way (R4-backend-7) -------------------------------


def test_a_failure_after_succeed_is_refused_and_logged(caplog):
    """A late failure cannot turn a finished results page into an error."""
    job_id = _new_job()
    results = [{"artist": "A"}]
    jobs.succeed(job_id, results, "Done")

    with caplog.at_level(logging.WARNING):
        assert jobs.fail(job_id, "internal_error") is False

    ctx = jobs.context(job_id)
    assert ctx["results"] == results
    assert ctx["progress"]["error"] is False
    assert ctx["progress"]["message"] == "Done"
    assert f"Job {job_id} has already ended; fail refused" in caplog.text


def test_a_success_after_fail_is_refused_and_logged(caplog):
    """The first ending stands: a job that failed is not later turned into a success."""
    job_id = _new_job()
    jobs.fail(job_id, "lastfm_unavailable")

    with caplog.at_level(logging.WARNING):
        assert jobs.succeed(job_id, [{"artist": "A"}], "Done") is False

    ctx = jobs.context(job_id)
    assert ctx["results"] == []
    assert ctx["progress"]["error_code"] == "lastfm_unavailable"
    assert f"Job {job_id} has already ended; succeed refused" in caplog.text


def test_a_second_failure_keeps_the_first_error():
    job_id = _new_job()
    jobs.fail(job_id, "lastfm_unavailable")

    assert jobs.fail(job_id, "internal_error") is False

    assert jobs.progress(job_id)["error_code"] == "lastfm_unavailable"


def test_a_refused_ending_does_not_renew_the_lease(clock):
    job_id = _new_job()
    jobs.succeed(job_id, [], "Done")
    clock.now += JOB_TTL_SECONDS - 10

    jobs.fail(job_id, "internal_error")
    clock.now += 20
    jobs.expire_stale()

    assert jobs.exists(job_id) is False


def test_start_lets_a_finished_job_end_again():
    """A restarted run (start) is a new life, so its ending is accepted."""
    job_id = _new_job()
    jobs.fail(job_id, "lastfm_unavailable")

    jobs.start(job_id, "Retrying")

    assert jobs.succeed(job_id, [{"artist": "A"}], "Done") is True
    assert jobs.progress(job_id)["error"] is False


def test_exists_is_true_for_a_live_job_and_false_for_a_gone_one():
    job_id = _new_job()

    assert jobs.exists(job_id) is True
    assert jobs.exists("nonexistent_job_id") is False
    jobs.delete(job_id)
    assert jobs.exists(job_id) is False
