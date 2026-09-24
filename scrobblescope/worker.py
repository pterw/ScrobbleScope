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


def run_coroutine_in_new_loop(
    coroutine,
    *,
    make_loop=new_thread_event_loop,
    release_slot=release_job_slot,
    on_run_error=None,
):
    """Run one coroutine to completion, then close the loop and release the slot.

    The protocol in one place: the loop is built *inside* the ``try``, so a setup
    failure still reaches the ``finally`` that releases the concurrency slot, and a
    failure to *close* is never swallowed -- a leaked loop must not be reported as a
    failed pipeline.

    The *policy* stays with the caller, through ``on_run_error``. The album and
    heatmap entry points deliberately answer a failed run differently today
    (``F-SWE-5`` records both answers as wrong, and fixing that means changing a
    caller, not this helper), so the helper shares the protocol and takes the
    reaction as a parameter.

    Args:
        coroutine: The coroutine to run, on a loop built for the calling thread. It is
            closed here if the loop is never built, so a setup failure does not leave
            an unstarted coroutine for the garbage collector to complain about.
        make_loop: Builds and installs that thread's event loop. Injected so callers
            keep their own patchable name; defaults to the local helper.
        release_slot: Releases the slot acquired before the job started. Called
            exactly once, even when closing the loop fails.
        on_run_error: Called with the caught exception when loop construction or the
            run itself fails. ``None`` leaves the failure silent, which is what an
            entry point with its own inner handler wants. It is *not* called for a
            close failure, which propagates instead.
    """
    loop = None
    try:
        loop = make_loop()
        loop.run_until_complete(coroutine)
    except Exception as exc:  # noqa: BLE001 - the injected policy decides what to do
        if on_run_error is not None:
            on_run_error(exc)
    finally:
        if loop is None:
            # The loop was never built, so the coroutine never started. Nobody else
            # will close it, and an unstarted coroutine nobody closes raises
            # "RuntimeWarning: coroutine ... was never awaited" on the worker thread.
            coroutine.close()
        try:
            if loop is not None:
                loop.close()
        finally:
            release_slot()
