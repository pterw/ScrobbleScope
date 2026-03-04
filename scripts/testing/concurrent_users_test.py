#!/usr/bin/env python3
"""Observe concurrent job submission behavior against the MAX_ACTIVE_JOBS semaphore.

Fires N simultaneous requests against a live ScrobbleScope instance and reports
per-thread outcomes (job_id, elapsed time, completion status) plus aggregate
results (submitted, completed, failed, elapsed range).

**Observability tool, not a pass/fail test.**  Results vary by machine, network
conditions, and server load.  The primary signal is whether threads that exceed
``MAX_ACTIVE_JOBS`` block, queue, or fail -- and whether concurrent Postgres
cache access produces races or corrupted results.

``MAX_ACTIVE_JOBS`` is configured in ``scrobblescope/config.py`` (default 10)
and enforced via a semaphore in ``scrobblescope/worker.py``.  Set
``--concurrency`` above 10 to observe queuing and semaphore-limit behavior.

Usage example::

    python scripts/testing/concurrent_users_test.py \\
        --concurrency 3 \\
        --base-url http://localhost:5000 \\
        --username YOUR_USERNAME \\
        --year 2024
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

# When executed directly (python scripts/testing/concurrent_users_test.py)
# Python adds the script directory to sys.path, not the repo root.  Insert the
# repo root so that ``from scripts.testing._http_client import ...`` resolves.
# pytest handles this automatically via pythonpath="." in pyproject.toml.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Shared HTTP transport -- handles CSRF, job submission, and polling.
from scripts.testing._http_client import poll_until_complete, submit_job  # noqa: E402


@dataclass
class ConcurrentResult:
    """Result record for one thread's job submission attempt.

    Attributes
    ----------
    thread_index : int
        1-based thread number assigned by ``main()`` -- used for output
        ordering and as the ``[thread-N]`` label in printed results.
    http_status : int | None
        HTTP status code of the job submission POST.  Set to 200 on
        success (``submit_job`` raises on any non-200 response).
        ``None`` if the submission raised an exception before a response
        was received.
    job_id : str | None
        The server-assigned job UUID.  ``None`` if submission failed.
    elapsed_seconds : float
        Wall-clock seconds from barrier synchronization to job completion
        (or failure).  Includes both submission and polling time.
    final_state : str | None
        The ``status`` key from the final ``/progress`` payload on success.
        ``None`` if the job did not complete (error or timeout).
    error : str | None
        String representation of any exception that aborted this thread.
        ``None`` on success.  Exceptions are captured here so one failing
        thread does not abort the entire test run.
    """

    thread_index: int
    http_status: int | None
    job_id: str | None
    elapsed_seconds: float
    final_state: str | None
    error: str | None


def run_thread(
    session: requests.Session,
    base_url: str,
    username: str,
    year: int,
    sort_by: str,
    release_scope: str,
    min_plays: int,
    min_tracks: int,
    timeout_seconds: int,
    poll_interval: float,
    thread_index: int,
    results: list[ConcurrentResult],
    barrier: threading.Barrier,
) -> None:
    """Submit one job and poll to completion; store the result.

    Waits at the shared ``barrier`` before submitting so that all threads
    fire their POST at the same instant (maximises the chance of exceeding
    the ``MAX_ACTIVE_JOBS`` semaphore limit in ``worker.py`` and observing
    queuing or rejection behavior).

    All exceptions are caught and stored in ``ConcurrentResult.error`` so
    a single failing thread (e.g. CSRF race, network timeout, server error)
    does not abort the rest of the test run.  One result is always appended
    to ``results``.

    ``list.append`` is atomic in CPython under the GIL (executed as a
    single bytecode instruction), so no additional lock is needed for the
    shared ``results`` list.

    Parameters
    ----------
    session : requests.Session
        A dedicated session for this thread.  Sessions must not be shared
        across threads because the connection pool and cookie jar are shared
        mutable state that is not protected by any lock.
    base_url : str
        Root URL of the ScrobbleScope instance (no trailing slash).
    username, year, sort_by, release_scope, min_plays, min_tracks
        Search parameters forwarded to :func:`submit_job`.
    timeout_seconds : int
        Maximum seconds to wait for the background job to complete.
    poll_interval : float
        Seconds between ``/progress`` poll requests.
    thread_index : int
        1-based index used as the ``[thread-N]`` label in printed output.
    results : list[ConcurrentResult]
        Shared accumulator; this function appends exactly one entry.
    barrier : threading.Barrier
        Synchronization point that holds all threads until every thread has
        called ``barrier.wait()``, then releases them simultaneously.
    """
    start = time.time()
    http_status: int | None = None
    job_id: str | None = None
    final_state: str | None = None
    error: str | None = None

    try:
        # Hold here until all threads are ready, then release simultaneously.
        # Inside the try block so BrokenBarrierError (e.g. another thread dies
        # before reaching wait()) is captured and a result is always appended.
        barrier.wait()

        job_id = submit_job(
            session=session,
            base_url=base_url,
            username=username,
            year=year,
            sort_by=sort_by,
            release_scope=release_scope,
            min_plays=min_plays,
            min_tracks=min_tracks,
        )
        # submit_job raises on any non-200 response; reaching here means 200.
        http_status = 200

        payload: dict[str, Any] = poll_until_complete(
            session=session,
            base_url=base_url,
            job_id=job_id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        final_state = payload.get("status")

    except Exception as exc:  # capture all exceptions for reporting
        error = str(exc)

    elapsed = time.time() - start

    results.append(
        ConcurrentResult(
            thread_index=thread_index,
            http_status=http_status,
            job_id=job_id,
            elapsed_seconds=elapsed,
            final_state=final_state,
            error=error,
        )
    )


def print_thread_result(result: ConcurrentResult) -> None:
    """Print one thread's result in a stable, grep-friendly format.

    Lines are prefixed with ``[thread-N]`` so results from individual
    threads can be isolated with ``grep`` or ``rg`` in terminal output.

    Parameters
    ----------
    result : ConcurrentResult
        The completed thread result to print.
    """
    if result.error is not None:
        status_str = f"FAILED error={result.error}"
    else:
        status_str = (
            f"OK job_id={result.job_id} "
            f"final_state={result.final_state} "
            f"http_status={result.http_status}"
        )
    print(
        f"[thread-{result.thread_index}] "
        f"elapsed={result.elapsed_seconds:.2f}s "
        f"{status_str}"
    )


def print_aggregate(results: list[ConcurrentResult]) -> None:
    """Print aggregate statistics for all thread results.

    Summarises total submitted, completed (no error), failed (error set),
    and the elapsed time range across threads.

    Parameters
    ----------
    results : list[ConcurrentResult]
        All thread results collected by ``main()``.
    """
    total = len(results)
    completed = sum(1 for r in results if r.error is None)
    failed = total - completed
    elapsed_values = [r.elapsed_seconds for r in results]

    print(f"\nAggregate: submitted={total} completed={completed} failed={failed}")
    if elapsed_values:
        print(
            f"  elapsed range: "
            f"min={min(elapsed_values):.2f}s "
            f"max={max(elapsed_values):.2f}s"
        )


def build_parser() -> argparse.ArgumentParser:
    """Create and return the CLI argument parser.

    Defaults are tuned for local development (``http://localhost:5000``).
    Override ``--base-url`` for deployed instances.  Set ``--concurrency``
    above ``MAX_ACTIVE_JOBS`` (default 10) to observe semaphore limiting.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser ready for ``parse_args()``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Number of simultaneous threads (default: 3)",
    )
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--username", default="flounder14")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument(
        "--sort-by", default="playcount", choices=["playcount", "playtime"]
    )
    parser.add_argument(
        "--release-scope",
        default="same",
        choices=["same", "previous", "decade", "custom", "all"],
    )
    parser.add_argument("--min-plays", type=int, default=10)
    parser.add_argument("--min-tracks", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    return parser


def main() -> None:
    """Create N threads, fire concurrent job submissions, print results.

    Workflow:
    1. Parse args and strip trailing slash from base URL.
    2. Create one ``requests.Session`` per thread -- sessions must not be
       shared across threads (connection pool and cookie jar are not
       thread-safe for concurrent use).
    3. Create a ``threading.Barrier(n)`` so all threads wait until all are
       ready, then submit simultaneously.
    4. Start all threads; join all threads.
    5. Print per-thread results (sorted by thread index) then aggregate.
    """
    args = build_parser().parse_args()
    base_url = args.base_url.rstrip("/")
    n = args.concurrency

    results: list[ConcurrentResult] = []

    # Barrier releases all n threads simultaneously -- maximises the chance
    # of hitting the MAX_ACTIVE_JOBS semaphore limit in worker.py.
    barrier = threading.Barrier(n)

    sessions: list[requests.Session] = []
    threads = []
    for i in range(n):
        # One session per thread: requests.Session is not thread-safe for
        # concurrent use across multiple threads.
        session = requests.Session()
        sessions.append(session)
        t = threading.Thread(
            target=run_thread,
            kwargs={
                "session": session,
                "base_url": base_url,
                "username": args.username,
                "year": args.year,
                "sort_by": args.sort_by,
                "release_scope": args.release_scope,
                "min_plays": args.min_plays,
                "min_tracks": args.min_tracks,
                "timeout_seconds": args.timeout_seconds,
                "poll_interval": args.poll_interval,
                "thread_index": i + 1,
                "results": results,
                "barrier": barrier,
            },
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Close sessions to release connection pools and avoid socket leaks.
    for s in sessions:
        s.close()

    for result in sorted(results, key=lambda r: r.thread_index):
        print_thread_result(result)

    print_aggregate(results)


if __name__ == "__main__":
    main()
