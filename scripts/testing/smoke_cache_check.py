#!/usr/bin/env python3
"""Smoke-test persistent Spotify metadata cache via HTTP endpoints.

Usage example:
    python scripts/testing/smoke_cache_check.py \
        --base-url https://scrobblescope.fly.dev \
        --username flounder14 \
        --year 2025 \
        --runs 2
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

JOB_JSON_RE = re.compile(r"window\.SCROBBLE\s*=\s*(\{.*?\})\s*;", re.DOTALL)


@dataclass
class RunResult:
    """Summary of one end-to-end run."""

    run_index: int
    job_id: str
    elapsed_seconds: float
    stats: dict[str, Any]
    message: str


def start_job(
    session: requests.Session,
    base_url: str,
    username: str,
    year: int,
    sort_by: str,
    release_scope: str,
    min_plays: int,
    min_tracks: int,
) -> str:
    """Start a new job and return its job_id extracted from loading page HTML."""
    response = session.post(
        f"{base_url}/results_loading",
        data={
            "username": username,
            "year": str(year),
            "sort_by": sort_by,
            "release_scope": release_scope,
            "min_plays": str(min_plays),
            "min_tracks": str(min_tracks),
            "limit_results": "all",
        },
        timeout=30,
    )
    response.raise_for_status()

    match = JOB_JSON_RE.search(response.text)
    if not match:
        raise RuntimeError("Could not locate window.SCROBBLE payload in loading page.")

    payload = json.loads(match.group(1))
    job_id = payload.get("job_id")
    if not job_id:
        raise RuntimeError("Loading page payload did not include job_id.")
    return job_id


def poll_job(
    session: requests.Session,
    base_url: str,
    job_id: str,
    timeout_seconds: int,
    poll_interval: float,
) -> dict[str, Any]:
    """Poll /progress until completion or timeout and return final progress payload."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = session.get(
            f"{base_url}/progress",
            params={"job_id": job_id},
            timeout=30,
        )
        if response.status_code not in (200, 404):
            raise RuntimeError(
                f"/progress returned unexpected status {response.status_code}: "
                f"{response.text[:200]}"
            )

        payload = response.json()
        progress = int(payload.get("progress", 0))
        if progress >= 100:
            return payload

        time.sleep(poll_interval)

    raise TimeoutError(
        f"Timed out waiting for job {job_id} after {timeout_seconds} seconds."
    )


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
    """Execute one full search and return completion metrics."""
    start = time.time()
    job_id = start_job(
        session=session,
        base_url=base_url,
        username=username,
        year=year,
        sort_by=sort_by,
        release_scope=release_scope,
        min_plays=min_plays,
        min_tracks=min_tracks,
    )
    progress_payload = poll_job(
        session=session,
        base_url=base_url,
        job_id=job_id,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
    )
    elapsed = time.time() - start

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
    """Print one run summary in a stable, grep-friendly format."""
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
    """Create and return CLI argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://scrobblescope.fly.dev")
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
    """Run cache smoke test and print cache effectiveness hints."""
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

    if len(results) >= 2:
        first = results[0]
        second = results[1]
        hit_delta = second.stats.get("cache_hits", 0) - first.stats.get("cache_hits", 0)
        elapsed_delta = first.elapsed_seconds - second.elapsed_seconds
        print("")
        print("Warm-cache check:")
        print(f"  cache_hits_delta(run2-run1)={hit_delta}")
        print(f"  elapsed_delta(run1-run2)={elapsed_delta:.2f}s")
        if second.stats.get("cache_hits", 0) > 0:
            print("  verdict=PASS (run 2 observed DB cache hits)")
        else:
            print("  verdict=INCONCLUSIVE (no cache hits observed on run 2)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
