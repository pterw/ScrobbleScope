#!/usr/bin/env python3
"""Smoke-test persistent Spotify metadata cache via HTTP endpoints.

Runs one or more end-to-end searches against a live ScrobbleScope instance
and checks whether the Postgres metadata cache is functioning.  The primary
signal is the ``db_cache_lookup_hits`` stat -- on a second run the app
should find cached metadata in the database rather than re-fetching from
Spotify.

Usage example::

    python scripts/testing/smoke_cache_check.py \\
        --base-url http://localhost:5000 \\
        --username YOUR_USERNAME \\
        --year 2025 \\
        --runs 2

**CSRF handling:** The script obtains a CSRF token from the index page
before POSTing, so the app can run with standard Flask-WTF CSRF protection
enabled (no need for ``WTF_CSRF_ENABLED=False``).

Exit code 0 on success; non-zero on failure.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Any

import requests

# Shared HTTP transport -- handles CSRF, job submission, and polling.
from scripts.testing._http_client import poll_until_complete, submit_job


@dataclass
class RunResult:
    """Summary of one end-to-end smoke-test run.

    Attributes
    ----------
    run_index : int
        1-based index identifying which run this is (e.g. 1 for first run).
    job_id : str
        The server-assigned UUID for the background task.
    elapsed_seconds : float
        Wall-clock time from job submission to completion.
    stats : dict[str, Any]
        The ``stats`` dict from the final ``/progress`` payload.  Contains
        cache counters (``db_cache_lookup_hits``, ``db_cache_persisted``,
        ``cache_hits``) and match counters (``spotify_matched``, etc.).
    message : str
        Human-readable completion message from the server.
    """

    run_index: int
    job_id: str
    elapsed_seconds: float
    stats: dict[str, Any]
    message: str


def run_once(
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
    run_index: int,
) -> RunResult:
    """Execute one full search cycle and return completion metrics.

    Delegates HTTP work to :mod:`scripts.testing._http_client`:
    ``submit_job`` handles CSRF + POST, ``poll_until_complete`` waits for
    the background task to finish.

    Parameters
    ----------
    session : requests.Session
        Persistent session (cookies survive across the CSRF fetch, POST,
        and polling).
    base_url : str
        Root URL of the ScrobbleScope instance (no trailing slash).
    username, year, sort_by, release_scope, min_plays, min_tracks
        Search parameters forwarded to ``submit_job``.
    timeout_seconds : int
        Maximum seconds to wait for job completion.
    poll_interval : float
        Seconds between ``/progress`` polls.
    run_index : int
        1-based run counter for labelling output.

    Returns
    -------
    RunResult
        Metrics and stats for this run.

    Raises
    ------
    RuntimeError
        If the job finishes with an error flag in the progress payload.
    """
    start = time.time()

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

    progress_payload = poll_until_complete(
        session=session,
        base_url=base_url,
        job_id=job_id,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
    )

    elapsed = time.time() - start

    # Check for server-side job error (e.g. upstream API failure).
    if progress_payload.get("error"):
        raise RuntimeError(
            "Job failed: "
            f"error_code={progress_payload.get('error_code')} "
            f"message={progress_payload.get('message')}"
        )

    return RunResult(
        run_index=run_index,
        job_id=job_id,
        elapsed_seconds=elapsed,
        stats=progress_payload.get("stats", {}),
        message=progress_payload.get("message", ""),
    )


def print_run_summary(result: RunResult) -> None:
    """Print one run's results in a stable, grep-friendly format.

    Output includes all cache-relevant counters so that automated tooling
    or human operators can quickly assess cache behavior at a glance.

    Parameters
    ----------
    result : RunResult
        The completed run to summarise.
    """
    stats = result.stats
    print(
        f"Run {result.run_index}: "
        f"job_id={result.job_id} "
        f"elapsed={result.elapsed_seconds:.2f}s "
        f"db_cache_enabled={stats.get('db_cache_enabled')} "
        f"db_cache_lookup_hits={stats.get('db_cache_lookup_hits', 0)} "
        f"db_cache_persisted={stats.get('db_cache_persisted', 0)} "
        f"cache_hits={stats.get('cache_hits', 0)} "
        f"spotify_matched={stats.get('spotify_matched', 0)} "
        f"spotify_unmatched={stats.get('spotify_unmatched', 0)}"
    )
    if stats.get("db_cache_warning"):
        print(f"  db_cache_warning={stats['db_cache_warning']}")
    if stats.get("partial_data_warning"):
        print(f"  partial_data_warning={stats['partial_data_warning']}")
    print(f"  message={result.message}")


def build_parser() -> argparse.ArgumentParser:
    """Create and return the CLI argument parser.

    Defaults are tuned for local development (``http://localhost:5000``).
    Override ``--base-url`` for deployed instances.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser ready for ``parse_args()``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    return parser


def main() -> int:
    """Run the cache smoke test and print cache effectiveness hints.

    Executes ``--runs`` sequential searches (default 2).  After the second
    run, compares ``db_cache_lookup_hits`` between runs to determine whether
    the Postgres cache layer is functioning:

    - **PASS**: Run 2 shows ``db_cache_lookup_hits > 0`` -- the DB cache
      returned previously persisted metadata.
    - **INCONCLUSIVE**: Run 2 shows ``db_cache_lookup_hits == 0`` -- the
      cache may not be populated, the DB may be unreachable, or the TTL
      may have expired.

    Returns
    -------
    int
        Exit code (0 = success).
    """
    args = build_parser().parse_args()
    base_url = args.base_url.rstrip("/")

    results: list[RunResult] = []
    with requests.Session() as session:
        for run_index in range(1, args.runs + 1):
            result = run_once(
                session=session,
                base_url=base_url,
                username=args.username,
                year=args.year,
                sort_by=args.sort_by,
                release_scope=args.release_scope,
                min_plays=args.min_plays,
                min_tracks=args.min_tracks,
                timeout_seconds=args.timeout_seconds,
                poll_interval=args.poll_interval,
                run_index=run_index,
            )
            results.append(result)
            print_run_summary(result)

    # --- Verdict: compare run 1 vs run 2 cache counters ---
    if len(results) >= 2:
        first = results[0]
        second = results[1]

        # db_cache_lookup_hits is the Postgres-specific counter -- the
        # correct signal for DB cache validation (not the broader
        # cache_hits which may include in-memory hits).
        db_hits_r1 = first.stats.get("db_cache_lookup_hits", 0)
        db_hits_r2 = second.stats.get("db_cache_lookup_hits", 0)
        hit_delta = db_hits_r2 - db_hits_r1
        elapsed_delta = first.elapsed_seconds - second.elapsed_seconds

        print("")
        print("Warm-cache check:")
        print(f"  db_cache_lookup_hits_delta(run2-run1)={hit_delta}")
        print(f"  elapsed_delta(run1-run2)={elapsed_delta:.2f}s")

        if db_hits_r2 > 0:
            print("  verdict=PASS (run 2 observed DB cache hits)")
        else:
            print("  verdict=INCONCLUSIVE (no DB cache hits observed on run 2)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
