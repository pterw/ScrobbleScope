"""Heatmap background task -- fetches Last.fm scrobbles and aggregates daily counts.

This module owns the heatmap processing pipeline: fetch recent tracks for the
last 365 days, bucket each scrobble into a calendar date, and store a
``{date_str: count}`` dict as the job result.  It reuses the existing Last.fm
fetch infrastructure (``lastfm.fetch_all_recent_tracks_async``), the job state
machine (``repositories.*``), and the concurrency slot system (``worker.*``).

Dependency chain (leaf-ward):
    heatmap <- config, lastfm, repositories, utils, worker

No Spotify enrichment, no DB cache, no domain normalization -- iteration 1
deals only with raw scrobble counts per day.
"""

import asyncio
import logging
import sys
import time
from collections import Counter
from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta

from scrobblescope.lastfm import fetch_all_recent_tracks_async
from scrobblescope.repositories import (
    cleanup_expired_jobs,
    set_job_error,
    set_job_progress,
    set_job_results,
    set_job_stat,
)
from scrobblescope.utils import cleanup_expired_cache
from scrobblescope.worker import release_job_slot


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
            day = datetime.fromtimestamp(ts).date()
            if from_date <= day <= to_date:
                counter[day.isoformat()] += 1

    # Phase 2: fill every calendar date in the range with 0 where missing.
    daily_counts = {}
    current = from_date
    while current <= to_date:
        key = current.isoformat()
        daily_counts[key] = counter.get(key, 0)
        current += timedelta(days=1)

    return daily_counts


async def _fetch_and_process_heatmap(job_id, username):
    """Async orchestrator: fetch Last.fm scrobbles and aggregate daily counts.

    Phases:
        0%      -- housekeeping (cache/job cleanup, initial progress)
        5-80%   -- Last.fm page fetching with progress callback
        80-90%  -- daily count aggregation
        90%     -- zero-scrobble guard
        100%    -- store results

    On upstream errors or zero scrobbles the job terminates early with a
    classified error via ``set_job_error``.
    """
    # Phase 0%: housekeeping --------------------------------------------------
    cleanup_expired_cache()
    cleanup_expired_jobs()
    set_job_progress(
        job_id,
        progress=0,
        message="Initializing heatmap...",
        error=False,
        reset_stats=True,
    )

    # Compute the 365-day window (today inclusive).
    now = datetime.now()
    to_date = now.date()
    from_date = to_date - timedelta(days=364)  # 365 calendar days inclusive
    from_ts = int(datetime.combine(from_date, dt_time.min).timestamp())
    to_ts = int(now.timestamp())

    # Phase 5-80%: fetch Last.fm pages ----------------------------------------
    def _heatmap_progress(pages_done, total_pages):
        """Map page-fetching progress into the 5%-80% range."""
        pct = 5 + int(75 * pages_done / max(total_pages, 1))
        set_job_progress(
            job_id,
            progress=pct,
            message=f"Fetching Last.fm page {pages_done}/{total_pages}...",
        )

    set_job_progress(
        job_id,
        progress=5,
        message="Fetching your scrobble history from Last.fm...",
        error=False,
    )

    fetch_start = time.time()
    pages, fetch_metadata = await fetch_all_recent_tracks_async(
        username, from_ts, to_ts, progress_cb=_heatmap_progress
    )
    fetch_elapsed = time.time() - fetch_start
    logging.info(f"Heatmap Last.fm fetch for {username}: {fetch_elapsed:.1f}s")

    # Record fetch stats for observability.
    set_job_stat(job_id, "pages_expected", fetch_metadata.get("pages_expected", 0))
    set_job_stat(job_id, "pages_received", fetch_metadata.get("pages_received", 0))

    # Upstream error guard: Last.fm was unreachable.
    if fetch_metadata.get("status") == "error":
        set_job_error(
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
        set_job_stat(
            job_id,
            "partial_data_warning",
            f"Note: {dropped} of {expected} Last.fm pages failed "
            f"({pct}% data loss). Heatmap may be incomplete.",
        )

    # Phase 80-90%: aggregate daily counts ------------------------------------
    set_job_progress(job_id, progress=80, message="Counting your daily scrobbles...")
    daily_counts = _aggregate_daily_counts(pages, from_date, to_date)

    total = sum(daily_counts.values())
    max_count = max(daily_counts.values()) if daily_counts else 0

    # Phase 90%: zero-scrobble guard ------------------------------------------
    if total == 0:
        set_job_error(job_id, "no_scrobbles_in_range", username=username)
        return

    # Phase 100%: store results -----------------------------------------------
    set_job_progress(job_id, progress=100, message="Heatmap ready!", error=False)
    set_job_results(
        job_id,
        {
            "username": username,
            "from_date": str(from_date),
            "to_date": str(to_date),
            "total_scrobbles": total,
            "max_count": max_count,
            "daily_counts": daily_counts,
        },
    )


def heatmap_task(job_id, username):
    """Thread entry point: run the heatmap pipeline in a dedicated event loop.

    On Windows, explicitly uses ``ProactorEventLoop`` so that asyncpg (if used
    later) sends the correct PostgreSQL startup packet.  Werkzeug's debug
    reloader can leave ``SelectorEventLoop`` as the thread-local policy in
    background threads on Windows, which breaks asyncpg negotiation.

    The concurrency slot acquired by the caller is released in the ``finally``
    block regardless of success or failure.
    """
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_fetch_and_process_heatmap(job_id, username))
    except Exception:
        logging.exception(f"Unhandled error in heatmap task for {username}")
        # Surface the error to the polling client so it does not hang.
        set_job_error(job_id, "lastfm_unavailable", username=username)
    finally:
        loop.close()
        release_job_slot()
