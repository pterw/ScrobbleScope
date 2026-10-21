"""A Last.fm username never reaches a log line (F-B23-40).

Each test runs one pipeline, one thread entry point or the Last.fm page layer
with a distinctive username and fails if that string appears in any record at
any level, in its message or in its formatted exception text. Where a line needs
correlation it names the job id instead. The Last.fm pre-check lines of the
routes are PR #3's and are tested there (``tests/test_precheck.py``).
"""

import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.errors import PrivateProfileError, UserNotFoundError
from scrobblescope.heatmap import _fetch_and_process_heatmap, heatmap_task
from scrobblescope.lastfm import fetch_recent_tracks_page_async
from scrobblescope.orchestrator import _fetch_and_process, background_task
from scrobblescope.utils import REQUEST_CACHE, get_cached_response, set_cached_response
from tests.helpers import (
    TEST_JOB_PARAMS,
    FakeLastfm,
    NoopAsyncContext,
    lastfm_edge,
    lastfm_page,
    lastfm_track,
    make_response_context,
)

LISTENER = "zqx_listener_7"


def _logged(caplog):
    """Every record's message and formatted exception text, as one string."""
    return "\n".join(f"{r.getMessage()}\n{r.exc_text or ''}" for r in caplog.records)


def _assert_listener_unlogged(caplog):
    """Fail if the listener's name is anywhere in the log, or nothing was logged."""
    assert caplog.records, "nothing was logged; the test would pass for any code"
    assert LISTENER not in _logged(caplog)


def _error_lines(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]


@pytest.fixture
def empty_request_cache():
    """The request cache is module state: start and leave it empty."""
    REQUEST_CACHE.clear()
    yield
    REQUEST_CACHE.clear()


@pytest.mark.asyncio
async def test_a_heatmap_run_logs_its_job_id_not_its_listener(caplog):
    """
    GIVEN a heatmap run that succeeds
    WHEN it logs its fetch timing and its completion
    THEN the lines name the job, and neither the username nor the scrobble total.

    Planted defect: log "Heatmap ready for <username>: <total> scrobbles", or
    "Heatmap Last.fm fetch for <username>".
    """
    yesterday = datetime.now(UTC).replace(microsecond=0) - timedelta(days=1)
    page = lastfm_page([lastfm_track("A", "B", "C", yesterday)])
    job_id = jobs.create({"username": LISTENER, "mode": "heatmap"})

    with (
        lastfm_edge(FakeLastfm({1: page})),
        patch("scrobblescope.heatmap.cleanup_expired_cache"),
        caplog.at_level(logging.DEBUG),
    ):
        await _fetch_and_process_heatmap(job_id, LISTENER)

    _assert_listener_unlogged(caplog)
    messages = [r.getMessage() for r in caplog.records]
    assert any("Heatmap job" in m and job_id in m and "ready" in m for m in messages)
    assert any("Heatmap Last.fm fetch" in m and job_id in m for m in messages)


@pytest.mark.asyncio
async def test_an_album_run_logs_no_listener(caplog):
    """
    GIVEN an album run that finds nothing to enrich
    WHEN it runs end to end
    THEN no record carries the username.

    Planted defect: restore the username to the fetch_top_albums_async debug line.
    """
    page = lastfm_page([lastfm_track("A", "B", "C", datetime(2023, 6, 15, tzinfo=UTC))])
    job_id = jobs.create(TEST_JOB_PARAMS)

    with lastfm_edge(FakeLastfm({1: page})), caplog.at_level(logging.DEBUG):
        await _fetch_and_process(job_id, LISTENER, 2023, "playcount", "all")

    _assert_listener_unlogged(caplog)


def test_the_heatmap_backstop_logs_the_job_id_not_the_listener(caplog):
    """
    GIVEN a heatmap job whose record carries the listener's name, and a pipeline
    that dies on an unexpected error
    WHEN heatmap_task(job_id) reads the name from the record and its backstop
    reports the failure
    THEN the ERROR line names the job and the exception class, not the username.

    Planted defect: restore the username to _report_heatmap_failure's line.
    """
    job_id = jobs.create({"username": LISTENER, "mode": "heatmap"})
    assert jobs.params(job_id)["username"] == LISTENER

    with (
        patch("scrobblescope.heatmap.release_job_slot"),
        patch("scrobblescope.jobs.start", side_effect=RuntimeError("boom")),
        caplog.at_level(logging.DEBUG),
    ):
        heatmap_task(job_id)

    assert jobs.progress(job_id)["error_code"] == "internal_error"
    _assert_listener_unlogged(caplog)
    assert any(job_id in line for line in _error_lines(caplog))


def test_the_album_backstop_logs_the_job_id_not_the_listener(caplog):
    """
    GIVEN an album job whose record carries the listener's name, and a crash
    that gets past the pipeline's own handler
    WHEN background_task(job_id) reads the name from the record and its
    backstop reports the failure
    THEN the ERROR line names the job and the exception class, not the username.

    Planted defect: restore the username to _report_album_failure's line.
    """
    job_id = jobs.create({**TEST_JOB_PARAMS, "username": LISTENER})
    assert jobs.params(job_id)["username"] == LISTENER

    async def explode(*args, **kwargs):
        raise RuntimeError("boom")

    with (
        patch("scrobblescope.orchestrator.release_job_slot"),
        patch("scrobblescope.orchestrator._fetch_and_process", explode),
        caplog.at_level(logging.DEBUG),
    ):
        background_task(job_id)

    assert jobs.progress(job_id)["error_code"] == "internal_error"
    _assert_listener_unlogged(caplog)
    assert any(job_id in line for line in _error_lines(caplog))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body", "raises"),
    [(404, None, UserNotFoundError), (403, {"error": 17}, PrivateProfileError)],
    ids=["not-found", "went-private"],
)
async def test_the_page_layer_names_no_listener_when_it_refuses(
    status, body, raises, caplog
):
    """
    GIVEN Last.fm refuses a page mid-job (404, or error 17)
    WHEN the page layer raises its typed failure
    THEN the line it logs does not carry the username.

    Planted defect: restore the username to either refusal line (each case
    catches its own line).
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=body)
    session.get.return_value = make_response_context(resp)

    with (
        patch("scrobblescope.lastfm.get_cached_response", return_value=None),
        patch(
            "scrobblescope.lastfm.get_lastfm_limiter", return_value=NoopAsyncContext()
        ),
        caplog.at_level(logging.DEBUG),
    ):
        with pytest.raises(raises):
            await fetch_recent_tracks_page_async(
                session, LISTENER, 1, 2, page=1, retries=1
            )

    _assert_listener_unlogged(caplog)


def test_a_cache_hit_logs_no_listener(caplog, empty_request_cache):
    """
    GIVEN a Last.fm answer cached under the listener's request, so its cache key
    embeds ``user:<name>``
    WHEN a repeat lookup hits the cache, with ``get_cached_response`` left real
    (every other test here patches it away and cannot reach this line)
    THEN the hit is logged without the key.

    Planted defect: log the key again, ``f"Cache hit for {key}"``.
    """
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {"method": "user.getinfo", "user": LISTENER, "api_key": "k"}
    set_cached_response(url, {"user": {}}, params)

    with caplog.at_level(logging.DEBUG):
        assert get_cached_response(url, params) == {"user": {}}

    assert any(r.getMessage().startswith("Cache hit") for r in caplog.records)
    _assert_listener_unlogged(caplog)
