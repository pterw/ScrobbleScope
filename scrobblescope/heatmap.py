"""Heatmap background task -- fetches Last.fm scrobbles and aggregates daily counts.

This module owns the heatmap processing pipeline: fetch recent tracks for the
last 365 days, bucket each scrobble into a calendar date, and store a
``{date_str: count}`` dict as the job result.  It reuses the existing Last.fm
fetch infrastructure (``lastfm.fetch_scrobbles``), the job state
machine (``jobs.*``), and the concurrency slot system (``worker.*``).

Dependency chain (leaf-ward):
    heatmap <- errors, jobs, lastfm, plays, utils, worker

No Spotify enrichment, no DB cache, no domain normalization -- iteration 1
deals only with raw scrobble counts per day.
"""

import logging
import time
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time

from scrobblescope import jobs
from scrobblescope.errors import classify_exception_to_error_code
from scrobblescope.lastfm import fetch_scrobbles
from scrobblescope.plays import Window, aggregate_daily_counts
from scrobblescope.utils import cleanup_expired_cache, log_failure
from scrobblescope.worker import (
    new_thread_event_loop,
    release_job_slot,
    run_coroutine_in_new_loop,
)

#: How many calendar days the heatmap covers, today included.
#:
#: This is the source the rest of the window follows. The renderer divides the
#: total by it for the daily average, and six lines of copy say the number out
#: loud, so a change here that does not reach them fetches one range while
#: displaying and averaging another. `config/docsync.toml` declares every copy
#: against this one, and DOC009 fails if they stop agreeing.
HEATMAP_WINDOW_DAYS = 365


async def _fetch_and_process_heatmap(job_id, username):
    """Async orchestrator: fetch Last.fm scrobbles and aggregate daily counts.

    Phases:
        0%      -- housekeeping (cache/job cleanup, initial progress)
        5-80%   -- Last.fm page fetching with progress callback
        80-90%  -- daily count aggregation
        90%     -- zero-scrobble guard
        100%    -- store results

    A total Last.fm failure raises out of this function and is classified by
    ``heatmap_task``'s backstop; zero scrobbles in range ends the job with
    ``no_scrobbles_in_range`` via ``jobs.fail``.
    """
    # Phase 0%: housekeeping --------------------------------------------------
    cleanup_expired_cache()
    jobs.expire_stale()
    jobs.start(job_id, "Initializing heatmap...")

    # Compute the 365-day window (today inclusive). All datetimes are UTC
    # so the fetch range and bucket boundaries agree regardless of the
    # server's local timezone (Fly.io is UTC but local Windows dev is not).
    now = datetime.now(UTC)
    to_date = now.date()
    # Minus one because both ends are inclusive. Written as arithmetic rather
    # than as a literal 364, which read as a different number from every other
    # copy of the window and could not be checked against them.
    from_date = to_date - timedelta(days=HEATMAP_WINDOW_DAYS - 1)
    window = Window(start=datetime.combine(from_date, dt_time.min, tzinfo=UTC), end=now)

    # Phase 5-80%: fetch Last.fm scrobbles -------------------------------------
    def _heatmap_progress(pages_done, total_pages, pages_received):
        """Report page-fetching progress inside the heatmap's fetch band."""
        jobs.record_stat(job_id, "pages_received", pages_received)
        jobs.record_stat(job_id, "pages_expected", total_pages)
        jobs.report_phase(
            job_id,
            jobs.HEATMAP_LASTFM_FETCH,
            pages_done,
            total_pages,
            "Reading your Last.fm history...",
        )

    jobs.advance(job_id, 5, "Fetching your scrobble history from Last.fm...")

    fetch_start = time.time()
    fetch = await fetch_scrobbles(username, window, progress_cb=_heatmap_progress)
    fetch_elapsed = time.time() - fetch_start
    logging.info(f"Heatmap Last.fm fetch for job {job_id}: {fetch_elapsed:.1f}s")

    # Record fetch stats for observability. A total Last.fm failure never gets
    # here: fetch_scrobbles raises, and heatmap_task's backstop classifies it.
    summary = fetch.summary
    jobs.record_stat(job_id, "pages_expected", summary.pages_expected)
    jobs.record_stat(job_id, "pages_received", summary.pages_received)

    # Partial data handling: some pages failed but we got partial data.
    if summary.partial:
        jobs.record_stat(
            job_id,
            "partial_data_warning",
            f"Note: {summary.pages_dropped} of {summary.pages_expected} Last.fm "
            f"pages failed ({summary.data_loss_pct}% data loss). "
            "Heatmap may be incomplete.",
        )

    # Phase 80-90%: aggregate daily counts ------------------------------------
    jobs.advance(job_id, 80, "Counting your daily scrobbles...")
    daily_counts = aggregate_daily_counts(fetch.plays, from_date, to_date)

    total = sum(daily_counts.values())
    max_count = max(daily_counts.values()) if daily_counts else 0
    active_days = sum(1 for count in daily_counts.values() if count)
    jobs.record_stat(job_id, "total_scrobbles", total)
    jobs.record_stat(job_id, "active_days", active_days)

    # Phase 90%: zero-scrobble guard ------------------------------------------
    if total == 0:
        jobs.fail(job_id, "no_scrobbles_in_range", username=username)
        return

    # Phase 100%: store results -----------------------------------------------
    # The progress endpoint is the browser's completion signal. ``succeed``
    # stores the payload and the 100% in one write, so a client that observes
    # 100% can always read a ready result immediately.
    jobs.succeed(
        job_id,
        {
            "username": username,
            "from_date": str(from_date),
            "to_date": str(to_date),
            "total_scrobbles": total,
            "max_count": max_count,
            "daily_counts": daily_counts,
        },
        "Heatmap ready!",
    )
    logging.info("Heatmap job %s is ready", job_id)


def _report_heatmap_failure(job_id, username, exc):
    """Log the crash and publish this pipeline's terminal state.

    Called from inside the helper's ``except`` block, so ``log_failure``
    still sees the active exception (its class at ERROR, its traceback at
    DEBUG). ``exc`` is classified the same way the album pipeline classifies
    its own unhandled exceptions, by exception type (one owner,
    ``errors.classify_exception_to_error_code`` -- F-SWE-5), so a known
    upstream failure that escapes ``_fetch_and_process_heatmap`` (a Last.fm
    404, a rate limit) is blamed on its actual source. An exception the
    classifier does not recognize is still ours: it publishes
    ``internal_error``, where ``lastfm_unavailable`` would blame an upstream
    that never failed.
    """
    log_failure(f"Unhandled error in heatmap task for job {job_id}")
    error_code = classify_exception_to_error_code(exc) or "internal_error"
    jobs.fail(job_id, error_code, username=username)


def heatmap_task(job_id):
    """Thread entry point: run the heatmap pipeline in a dedicated event loop.

    The username comes from the job record (``jobs.params``), where admission
    stored it. A job that is gone runs nothing, and the slot the route
    acquired is still released.

    The build-run-close-release protocol, including that the loop is built inside
    the ``try`` so the slot is released in the ``finally``, lives in
    ``worker.run_coroutine_in_new_loop``. What stays here is local: a failed
    run is reported rather than raised, classified by
    ``errors.classify_exception_to_error_code`` first and falling back to
    ``internal_error`` (see ``_report_heatmap_failure``). The album entry
    point's backstop (``_report_album_failure``) does not classify: it always
    publishes ``internal_error`` (F-SWE-5).
    """
    username = (jobs.params(job_id) or {}).get("username")
    if not username:
        logging.warning("Heatmap job %s was gone before its thread started.", job_id)
        release_job_slot()
        return
    run_coroutine_in_new_loop(
        _fetch_and_process_heatmap(job_id, username),
        # Explicit, for the same reason as the album entry point: these tests patch
        # ``scrobblescope.heatmap.release_job_slot`` and ``scrobblescope.jobs.fail``.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda exc: _report_heatmap_failure(job_id, username, exc),
    )
