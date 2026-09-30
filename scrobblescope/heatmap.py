"""Heatmap background task -- fetches Last.fm scrobbles and aggregates daily counts.

This module owns the heatmap processing pipeline: fetch recent tracks for the
last 365 days, bucket each scrobble into a calendar date, and store a
``{date_str: count}`` dict as the job result.  It reuses the existing Last.fm
fetch infrastructure (``lastfm.fetch_all_recent_tracks_async``), the job state
machine (``jobs.*``), and the concurrency slot system (``worker.*``).

Dependency chain (leaf-ward):
    heatmap <- errors, jobs, lastfm, utils, worker

No Spotify enrichment, no DB cache, no domain normalization -- iteration 1
deals only with raw scrobble counts per day.
"""

import logging
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from datetime import time as dt_time

from scrobblescope import jobs
from scrobblescope.errors import classify_exception_to_error_code
from scrobblescope.lastfm import fetch_all_recent_tracks_async
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


def _zero_fill_daily_counts(counts, from_date, to_date):
    """Fill every calendar date in ``[from_date, to_date]`` with 0 where missing.

    Extracted from ``_aggregate_daily_counts``'s Phase 2 so it can be reused
    on its own; called by ``_aggregate_daily_counts`` after Phase 1 tallies
    raw per-day counts, and Batch 23's export path will be the second
    caller.

    Args:
        counts: Mapping (dict or ``collections.Counter``) of ``"YYYY-MM-DD"``
            strings to integer counts for dates that had at least one
            scrobble.
        from_date: Inclusive start date (``datetime.date``).
        to_date: Inclusive end date (``datetime.date``).

    Returns:
        New dict with every ISO date in the ``[from_date, to_date]`` range
        present, each mapped to ``counts.get(key, 0)``.
    """
    daily_counts = {}
    current = from_date
    while current <= to_date:
        key = current.isoformat()
        daily_counts[key] = counts.get(key, 0)
        current += timedelta(days=1)
    return daily_counts


def _aggregate_daily_counts(pages, from_date, to_date):
    """Aggregate raw Last.fm page data into a ``{YYYY-MM-DD: count}`` dict.

    This is a pure function (no I/O, no side-effects) extracted from the async
    orchestrator for easy unit testing.

    Args:
        pages: List of raw Last.fm JSON page dicts.  Each page has
            ``recenttracks.track`` containing track objects with an optional
            ``date.uts`` Unix-timestamp field.
        from_date: Inclusive start date (``datetime.date``).
        to_date: Inclusive end date (``datetime.date``).

    Returns:
        Dict mapping ``"YYYY-MM-DD"`` strings to integer scrobble counts.
        Every date in the ``[from_date, to_date]`` range is present; dates
        with no scrobbles map to ``0``.

    Notes:
        - Uses ``date.uts`` (Unix timestamp) for date extraction, NOT
          ``date["#text"]`` which is locale-dependent and fragile.
        - "Now playing" tracks have no ``date`` field and are silently skipped.
        - Tracks outside the ``[from_date, to_date]`` window are excluded
          (Last.fm can return boundary pages with out-of-range entries).
    """
    # Phase 1: count scrobbles per day using the uts timestamp.
    counter = Counter()
    for page in pages:
        for track in page.get("recenttracks", {}).get("track", []):
            uts = track.get("date", {}).get("uts")
            if not uts:
                # "Now playing" tracks lack a date field -- skip them.
                continue
            ts = int(uts)
            # Last.fm UTS values are UTC-anchored; decoding as UTC keeps day
            # attribution consistent across server timezones (lastfm.py:31
            # already follows this pattern for year extraction).
            day = datetime.fromtimestamp(ts, tz=timezone.utc).date()
            if from_date <= day <= to_date:
                counter[day.isoformat()] += 1

    return _zero_fill_daily_counts(counter, from_date, to_date)


async def _fetch_and_process_heatmap(job_id, username):
    """Async orchestrator: fetch Last.fm scrobbles and aggregate daily counts.

    Phases:
        0%      -- housekeeping (cache/job cleanup, initial progress)
        5-80%   -- Last.fm page fetching with progress callback
        80-90%  -- daily count aggregation
        90%     -- zero-scrobble guard
        100%    -- store results

    On upstream errors or zero scrobbles the job terminates early with a
    classified error via ``jobs.fail``.
    """
    # Phase 0%: housekeeping --------------------------------------------------
    cleanup_expired_cache()
    jobs.expire_stale()
    jobs.start(job_id, "Initializing heatmap...")

    # Compute the 365-day window (today inclusive). All datetimes are UTC
    # so the fetch range and bucket boundaries agree regardless of the
    # server's local timezone (Fly.io is UTC but local Windows dev is not).
    now = datetime.now(timezone.utc)
    to_date = now.date()
    # Minus one because both ends are inclusive. Written as arithmetic rather
    # than as a literal 364, which read as a different number from every other
    # copy of the window and could not be checked against them.
    from_date = to_date - timedelta(days=HEATMAP_WINDOW_DAYS - 1)
    from_ts = int(
        datetime.combine(from_date, dt_time.min, tzinfo=timezone.utc).timestamp()
    )
    to_ts = int(now.timestamp())

    # Phase 5-80%: fetch Last.fm pages ----------------------------------------
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
    pages, fetch_metadata = await fetch_all_recent_tracks_async(
        username, from_ts, to_ts, progress_cb=_heatmap_progress
    )
    fetch_elapsed = time.time() - fetch_start
    logging.info(f"Heatmap Last.fm fetch for {username}: {fetch_elapsed:.1f}s")

    # Record fetch stats for observability.
    jobs.record_stat(job_id, "pages_expected", fetch_metadata.get("pages_expected", 0))
    jobs.record_stat(job_id, "pages_received", fetch_metadata.get("pages_received", 0))

    # Upstream error guard: Last.fm was unreachable.
    if fetch_metadata.get("status") == "error":
        jobs.fail(
            job_id,
            fetch_metadata.get("reason", "lastfm_unavailable"),
            username=username,
        )
        return

    # Partial data handling: some pages failed but we got partial data.
    if fetch_metadata.get("status") == "partial":
        dropped = fetch_metadata["pages_dropped"]
        expected = fetch_metadata["pages_expected"]
        pct = round((dropped / expected) * 100)
        jobs.record_stat(
            job_id,
            "partial_data_warning",
            f"Note: {dropped} of {expected} Last.fm pages failed "
            f"({pct}% data loss). Heatmap may be incomplete.",
        )

    # Phase 80-90%: aggregate daily counts ------------------------------------
    jobs.advance(job_id, 80, "Counting your daily scrobbles...")
    daily_counts = _aggregate_daily_counts(pages, from_date, to_date)

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
    logging.info("Heatmap ready for %s: %s scrobbles", username, total)


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
    that never failed. The inner, status-based Last.fm path inside
    ``_fetch_and_process_heatmap`` still publishes its own code.
    """
    log_failure(f"Unhandled error in heatmap task for {username}")
    error_code = classify_exception_to_error_code(exc) or "internal_error"
    jobs.fail(job_id, error_code, username=username)


def heatmap_task(job_id, username):
    """Thread entry point: run the heatmap pipeline in a dedicated event loop.

    The build-run-close-release protocol, including that the loop is built inside
    the ``try`` so the slot is released in the ``finally``, lives in
    ``worker.run_coroutine_in_new_loop``. What stays here is local: a failed
    run is reported rather than raised, classified by
    ``errors.classify_exception_to_error_code`` first and falling back to
    ``internal_error`` (see ``_report_heatmap_failure``). The album entry
    point's backstop (``_report_album_failure``) does not classify: it always
    publishes ``internal_error`` (F-SWE-5).
    """
    run_coroutine_in_new_loop(
        _fetch_and_process_heatmap(job_id, username),
        # Explicit, for the same reason as the album entry point: these tests patch
        # ``scrobblescope.heatmap.release_job_slot`` and ``scrobblescope.jobs.fail``.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda exc: _report_heatmap_failure(job_id, username, exc),
    )
