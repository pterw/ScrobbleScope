import asyncio
import logging
import sys
import threading

from scrobblescope.config import MAX_ACTIVE_JOBS

# Bounded semaphore to cap concurrent background jobs
_active_jobs_semaphore = threading.BoundedSemaphore(MAX_ACTIVE_JOBS)


def acquire_job_slot():
    """Try to acquire a concurrency slot for a new background job.

    Returns True if the slot was acquired (job may proceed), or False if all
    slots are occupied (caller should reject the request).
    """
    return _active_jobs_semaphore.acquire(blocking=False)


def release_job_slot():
    """Release a previously acquired background job concurrency slot.

    Safe to call from any thread; logs a warning if called without a matching
    acquire (should not happen in normal operation).
    """
    try:
        _active_jobs_semaphore.release()
    except ValueError:
        logging.warning("release_job_slot called with no matching acquire")


def start_job_thread(target, args=()):
    """Start a daemon thread for a background job.

    Releases the acquired concurrency slot and re-raises on Thread construction
    or start failure, so the caller can render an error without leaking the slot.
    """
    try:
        t = threading.Thread(target=target, args=args, daemon=True)
        t.start()
    except Exception:
        release_job_slot()
        raise


def new_thread_event_loop():
    """Create an event loop for the calling background thread and install it.

    Every background thread here -- the album and heatmap job threads and
    the release-check worker -- runs its async pipeline in a loop of its own,
    and all three need the same Windows exception, which is why it lives here
    once rather than in each of them.

    On Windows the loop must be a ``ProactorEventLoop`` explicitly. Werkzeug's
    debug reloader can leave a ``SelectorEventLoop`` as the policy in child
    threads, and under it asyncpg mis-negotiates the connection: Postgres logs
    "invalid length of startup packet".

    The caller owns closing the returned loop. The one exception is a failure
    to install it: the loop is closed here before the error propagates,
    because the caller never received it and cannot.
    """
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
    except BaseException:
        loop.close()
        raise
    return loop
