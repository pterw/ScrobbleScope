"""A failure is logged by its exception type at ERROR; its traceback is DEBUG only.

Owner ruling 2026-09-29: an exception's text can carry a provider's URL and
query string or a listener's artist, album and track names, and a traceback
repeats it, so ERROR names the class and the traceback goes to DEBUG. Each test
raises an exception whose text is a distinctive marker and checks every record
at WARNING or above never carries it, in the message or in ``exc_info``, while
the DEBUG record does (so the diagnosis is still there for whoever turns that
level on). One test per distinct site pattern; every ``logging.exception``
site that was in ``scrobblescope/`` is covered by one of them.
"""

import contextlib
import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.utils import log_failure
from tests.helpers import TEST_JOB_PARAMS, VALID_FORM_DATA

MARKER = "Zqxv Distinctive Artist - Wjkl Distinctive Album"


def _assert_type_only_at_error(caplog, *, error_fragment, exc_name="RuntimeError"):
    """Assert the marker is absent from every ERROR record and present in DEBUG."""
    serious = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert serious, "nothing was logged at WARNING or above"
    for record in serious:
        assert MARKER not in record.getMessage()
        assert record.exc_info is None, "a traceback was attached at ERROR"
        assert record.exc_text is None
    named = [r for r in serious if error_fragment in r.getMessage()]
    assert len(named) == 1
    assert named[0].levelno == logging.ERROR
    assert named[0].getMessage().endswith(f": {exc_name}")
    tracebacks = [
        r for r in caplog.records if r.levelno == logging.DEBUG and r.exc_info
    ]
    assert any(MARKER in str(r.exc_info[1]) for r in tracebacks)


def test_log_failure_names_the_class_at_error_and_keeps_the_traceback_at_debug(
    caplog,
):
    """
    GIVEN an exception whose text is a distinctive marker
    WHEN log_failure runs inside its except block
    THEN the ERROR line is the message plus the class and carries neither the
    marker nor a traceback, and a DEBUG record carries the traceback.
    """
    with caplog.at_level(logging.DEBUG):
        try:
            raise RuntimeError(MARKER)
        except RuntimeError:
            log_failure("Something failed")

    _assert_type_only_at_error(caplog, error_fragment="Something failed")
    assert caplog.records[0].getMessage() == "Something failed: RuntimeError"


def test_log_failure_outside_an_except_block_says_so_instead_of_crashing(caplog):
    """GIVEN no active exception WHEN log_failure runs THEN it still logs one line."""
    with caplog.at_level(logging.DEBUG):
        log_failure("Nothing to report")

    error = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert [r.getMessage() for r in error] == ["Nothing to report: no active exception"]


@pytest.mark.asyncio
async def test_album_pipeline_crash_logs_the_class_only_at_error(caplog):
    """
    GIVEN the album pipeline fails with a marker-carrying exception
    WHEN _fetch_and_process handles it
    THEN the job is published internal_error and the ERROR line names only the
    class.
    """
    from scrobblescope.orchestrator import _fetch_and_process

    job_id = jobs.create(TEST_JOB_PARAMS)
    with (
        patch(
            "scrobblescope.orchestrator.cleanup_expired_cache",
            side_effect=RuntimeError(MARKER),
        ),
        caplog.at_level(logging.DEBUG),
    ):
        await _fetch_and_process(job_id, "testuser", 2025, "playcount", "all")

    assert jobs.progress(job_id)["error_code"] == "internal_error"
    _assert_type_only_at_error(caplog, error_fragment="Error processing request")


def test_album_backstop_logs_the_class_only_at_error(caplog):
    """
    GIVEN the worker's backstop reports a run that died with a marker exception
    WHEN _report_album_failure runs in the except block
    THEN the job is internal_error and ERROR carries the class, not the text.
    """
    from scrobblescope.orchestrator import _report_album_failure

    job_id = jobs.create(TEST_JOB_PARAMS)
    with caplog.at_level(logging.DEBUG):
        try:
            raise RuntimeError(MARKER)
        except RuntimeError:
            _report_album_failure(job_id, "testuser", 2025)

    assert jobs.progress(job_id)["error_code"] == "internal_error"
    _assert_type_only_at_error(caplog, error_fragment="Unhandled error in background")


def test_heatmap_backstop_logs_the_class_only_at_error(caplog):
    """
    GIVEN the heatmap pipeline died with a marker exception
    WHEN _report_heatmap_failure runs in the except block
    THEN the job is internal_error and ERROR carries the class, not the text.
    """
    from scrobblescope.heatmap import _report_heatmap_failure

    job_id = jobs.create(TEST_JOB_PARAMS)
    with caplog.at_level(logging.DEBUG):
        try:
            raise RuntimeError(MARKER)
        except RuntimeError as exc:
            _report_heatmap_failure(job_id, "testuser", exc)

    assert jobs.progress(job_id)["error_code"] == "internal_error"
    _assert_type_only_at_error(caplog, error_fragment="Unhandled error in heatmap")


@pytest.mark.asyncio
async def test_release_check_failure_logs_the_class_only_at_error(caplog):
    """
    GIVEN the correction pass fails inside its try block with a marker exception
    WHEN run_release_checks handles it
    THEN it returns without raising and ERROR carries the class, not the text.
    """
    from scrobblescope import release_checks

    job_id = jobs.create(TEST_JOB_PARAMS)
    with (
        patch.object(release_checks, "MUSICBRAINZ_ENABLED", True),
        patch.object(
            release_checks,
            "_select_candidates",
            return_value=[{"key": ("a", "b")}],
        ),
        patch.object(release_checks, "_mark_unchecked"),
        patch.object(
            release_checks,
            "_get_db_connection",
            new_callable=AsyncMock,
            return_value=MagicMock(close=AsyncMock()),
        ),
        patch.object(
            release_checks,
            "_lookup_cached",
            new_callable=AsyncMock,
            side_effect=RuntimeError(MARKER),
        ),
        caplog.at_level(logging.DEBUG),
    ):
        await release_checks.run_release_checks(job_id)

    _assert_type_only_at_error(caplog, error_fragment="Release checks failed")


def test_release_worker_crash_logs_the_class_only_at_error(caplog):
    """
    GIVEN the worker loop's job raises a marker exception, then the queue ends
    the loop
    WHEN _worker_loop runs
    THEN ERROR carries the class, not the text, and the job is marked done.
    """
    from scrobblescope import release_checks

    queue = MagicMock()
    queue.get.side_effect = [7, SystemExit]

    async def crash(job_id):
        raise RuntimeError(MARKER)

    with (
        patch.object(release_checks, "_JOB_QUEUE", queue),
        patch.object(release_checks, "run_release_checks", crash),
        caplog.at_level(logging.DEBUG),
        pytest.raises(SystemExit),
    ):
        release_checks._worker_loop()

    queue.task_done.assert_called_once_with()
    _assert_type_only_at_error(caplog, error_fragment="Release-check worker crashed")


def test_validate_user_failure_logs_the_class_only_at_error(client, caplog):
    """
    GIVEN the Last.fm validation call raises a marker exception
    WHEN GET /validate_user runs
    THEN the answer is the retryable 503 and ERROR carries the class only.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=RuntimeError(MARKER),
        ),
        caplog.at_level(logging.DEBUG),
    ):
        response = client.get("/validate_user", query_string={"username": "someone"})

    assert response.status_code >= 500
    _assert_type_only_at_error(caplog, error_fragment="Username validation failed")


def test_album_start_thread_failure_logs_the_class_only_at_error(client, caplog):
    """
    GIVEN the job thread cannot be started and its error text is a marker
    WHEN POST /results_loading runs
    THEN ERROR carries the class only.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch(
            "scrobblescope.routes.start_job_thread", side_effect=RuntimeError(MARKER)
        ),
        caplog.at_level(logging.DEBUG),
    ):
        client.post("/results_loading", data=VALID_FORM_DATA)

    _assert_type_only_at_error(
        caplog, error_fragment="Failed to start background task thread"
    )


def test_heatmap_existence_check_failure_logs_the_class_only_at_error(client, caplog):
    """
    GIVEN the heatmap's user lookup raises a marker exception
    WHEN POST /heatmap_loading runs
    THEN the answer is the retryable 503 and ERROR carries the class only.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=RuntimeError(MARKER),
        ),
        caplog.at_level(logging.DEBUG),
    ):
        response = client.post("/heatmap_loading", data={"username": "someone"})

    assert response.status_code == 503
    _assert_type_only_at_error(caplog, error_fragment="User existence check failed")


def test_heatmap_privacy_check_failure_logs_the_class_only_at_error(client, caplog):
    """
    GIVEN the user exists but the privacy check raises a marker exception
    WHEN POST /heatmap_loading runs
    THEN the answer is the retryable 503 and ERROR carries the class only.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=[
                {"exists": True, "registered_year": None},
                RuntimeError(MARKER),
            ],
        ),
        caplog.at_level(logging.DEBUG),
    ):
        response = client.post("/heatmap_loading", data={"username": "someone"})

    assert response.status_code == 503
    _assert_type_only_at_error(caplog, error_fragment="Profile privacy check failed")


def test_heatmap_start_thread_failure_logs_the_class_only_at_error(client, caplog):
    """
    GIVEN the heatmap thread cannot be started and its error text is a marker
    WHEN POST /heatmap_loading runs
    THEN the answer is 500 and ERROR carries the class only.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=[
                {"exists": True, "registered_year": None},
                True,
            ],
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch(
            "scrobblescope.routes.start_job_thread", side_effect=RuntimeError(MARKER)
        ),
        caplog.at_level(logging.DEBUG),
    ):
        response = client.post("/heatmap_loading", data={"username": "someone"})

    assert response.status_code == 500
    _assert_type_only_at_error(caplog, error_fragment="Failed to start heatmap task")


def _failing_conn():
    conn = MagicMock()
    conn.execute = AsyncMock(side_effect=RuntimeError(MARKER))
    return conn


class _SchemaError(RuntimeError):
    """A driver error saying the table or a column is missing (SQLSTATE 42P01)."""

    sqlstate = "42P01"


def _remedy():
    from scrobblescope.cache import SCHEMA_OUT_OF_DATE_REMEDIATION

    return f" ({SCHEMA_OUT_OF_DATE_REMEDIATION})"


@contextlib.contextmanager
def _all(*managers):
    """Enter every context manager in *managers* as one, on ``with`` only."""
    with contextlib.ExitStack() as stack:
        for manager in managers:
            stack.enter_context(manager)
        yield


def _database_site(name):
    """Return (guard, call, expected messages, exception class name) for a site.

    Each expected message is the whole WARNING line minus the ``: <class>``
    suffix, so a site that regresses to ``{exc}`` or loses its remediation
    text changes the line and fails the equality.
    """
    from scrobblescope import cache, release_checks
    from scrobblescope import orchestrator as orch

    def patched(target, attr, exc=None):
        return patch.object(
            target,
            attr,
            new_callable=AsyncMock,
            side_effect=exc or RuntimeError(MARKER),
        )

    def no_musicbrainz_answer():
        return patch.object(
            release_checks,
            "lookup_original_release",
            new_callable=AsyncMock,
            return_value=(None, None),
        )

    async def persist_one_finding():
        await release_checks._check_candidate(
            MagicMock(),
            MagicMock(),
            jobs.create(TEST_JOB_PARAMS),
            {"key": ("a", "b"), "artist": "A", "album": "B", "kind": "other"},
            {},
            release_checks._state(release_checks.STATUS_RUNNING),
        )

    async def run_and_close_badly():
        await release_checks.run_release_checks(jobs.create(TEST_JOB_PARAMS))

    def metadata_lookup():
        return orch._lookup_cached_metadata(
            # AsyncMock: the stale-row cleanup that follows must succeed.
            AsyncMock(),
            jobs.create(TEST_JOB_PARAMS),
            [("a", "b")],
        )

    def release_check_lookup():
        return release_checks._lookup_cached(MagicMock(), [{"key": ("a", "b")}])

    sites = {
        "metadata_lookup": (
            patched(orch, "_batch_lookup_metadata"),
            metadata_lookup,
            ["DB lookup failed, proceeding without cache"],
            "RuntimeError",
        ),
        "metadata_lookup_schema": (
            patched(orch, "_batch_lookup_metadata", _SchemaError(MARKER)),
            metadata_lookup,
            ["DB lookup failed, proceeding without cache" + _remedy()],
            "_SchemaError",
        ),
        "metadata_persist": (
            patched(orch, "_batch_persist_metadata"),
            lambda: orch._persist_new_metadata(
                MagicMock(), jobs.create(TEST_JOB_PARAMS), [("row",)]
            ),
            ["DB persist failed (non-fatal)"],
            "RuntimeError",
        ),
        "correction_lookup": (
            patched(orch, "_batch_lookup_original_release"),
            lambda: orch._lookup_cached_original_release(MagicMock(), [("a", "b")]),
            ["Original-release cache lookup failed (non-fatal)"],
            "RuntimeError",
        ),
        "stale_cleanup": (
            patch.object(cache, "METADATA_CACHE_TTL_DAYS", 30),
            lambda: cache._cleanup_stale_metadata(_failing_conn()),
            ["Stale cache cleanup failed (non-fatal)"],
            "RuntimeError",
        ),
        "release_check_lookup": (
            patched(release_checks, "_batch_lookup_original_release"),
            release_check_lookup,
            ["Original-release cache lookup failed"],
            "RuntimeError",
        ),
        "release_check_lookup_schema": (
            patched(
                release_checks, "_batch_lookup_original_release", _SchemaError(MARKER)
            ),
            release_check_lookup,
            ["Original-release cache lookup failed" + _remedy()],
            "_SchemaError",
        ),
        "release_check_persist": (
            _all(
                patched(release_checks, "_batch_persist_original_release"),
                no_musicbrainz_answer(),
            ),
            persist_one_finding,
            ["Original-release persist failed (non-fatal)"],
            "RuntimeError",
        ),
        "release_check_persist_schema": (
            _all(
                patched(
                    release_checks,
                    "_batch_persist_original_release",
                    _SchemaError(MARKER),
                ),
                no_musicbrainz_answer(),
            ),
            persist_one_finding,
            ["Original-release persist failed (non-fatal)" + _remedy()],
            "_SchemaError",
        ),
        "release_check_connection_close": (
            _all(
                patch.object(release_checks, "MUSICBRAINZ_ENABLED", True),
                patch.object(
                    release_checks, "_select_candidates", return_value=[{"key": 1}]
                ),
                patch.object(release_checks, "_mark_unchecked"),
                patch.object(
                    release_checks,
                    "_get_db_connection",
                    new_callable=AsyncMock,
                    return_value=MagicMock(
                        close=AsyncMock(side_effect=RuntimeError(MARKER))
                    ),
                ),
                patch.object(
                    release_checks,
                    "_lookup_cached",
                    new_callable=AsyncMock,
                    return_value={},
                ),
                patch.object(release_checks, "_resolve_cached", return_value=[]),
            ),
            run_and_close_badly,
            ["Closing the release-check DB connection failed"],
            "RuntimeError",
        ),
        "connect_retry_and_give_up": (
            _all(
                patch.object(
                    cache,
                    "asyncpg",
                    MagicMock(connect=AsyncMock(side_effect=RuntimeError(MARKER))),
                ),
                patch.object(cache, "_DATABASE_URL", "postgresql://db.invalid/x"),
                patch.dict(
                    os.environ,
                    {
                        "DB_CONNECT_MAX_ATTEMPTS": "2",
                        "DB_CONNECT_BASE_DELAY_SECONDS": "0",
                    },
                ),
            ),
            cache._get_db_connection,
            [
                "DB connection attempt 1/2 failed (db-down), retrying in 0.00s",
                "DB cache unavailable (db-down): connection failed after 2 "
                "attempts (cache disabled)",
            ],
            "RuntimeError",
        ),
    }
    return sites[name]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "site",
    [
        "metadata_lookup",
        "metadata_lookup_schema",
        "metadata_persist",
        "correction_lookup",
        "stale_cleanup",
        "release_check_lookup",
        "release_check_lookup_schema",
        "release_check_persist",
        "release_check_persist_schema",
        "release_check_connection_close",
        "connect_retry_and_give_up",
    ],
)
async def test_fail_open_database_sites_log_the_class_only_at_warning(caplog, site):
    """
    GIVEN a database call whose exception text carries a marker (a driver
    message can echo a DSN or query parameters)
    WHEN the fail-open site handles it
    THEN it returns normally, each WARNING line is the message plus the class,
    with no marker and no traceback (and the remediation text where the schema
    is out of date), and the DEBUG records keep the traceback.
    """
    guard, call, messages, exc_name = _database_site(site)
    with guard, caplog.at_level(logging.DEBUG):
        await call()

    serious = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert [r.getMessage() for r in serious] == [
        f"{message}: {exc_name}" for message in messages
    ]
    for record in serious:
        assert record.levelno == logging.WARNING
        assert MARKER not in record.getMessage()
        assert record.exc_info is None
    debug = [r for r in caplog.records if r.levelno == logging.DEBUG and r.exc_info]
    assert any(MARKER in str(r.exc_info[1]) for r in debug)
