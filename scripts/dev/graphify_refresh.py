#!/usr/bin/env python3
"""Refresh the local graphify knowledge graph once enough work has accumulated.

``graphify update .`` is incremental: it diffs the corpus against the manifest
inside ``graphify-out/`` and re-extracts only what changed. Running it after
every commit is waste, so the git hooks call this script instead and this
script decides whether a rebuild is due:

* ``--min-commits`` (default 5) commits have landed, or
* ``--min-files`` (default 25) files have changed,

counted from the commit recorded in
``graphify-out/.graphify_refresh_state.json``. ``--force`` ignores both.

Two states are skips rather than rebuilds, on purpose:

* No ``graphify-out/graph.json``: there is no graph to update. That is the
  fresh-clone state, and a first full build is the ``/graphify`` skill's job
  -- over docs, papers and images it needs a backend and API credit -- not a
  commit hook's. ``--force`` does not override this.
* No state file: the baseline is unknown, so the script records ``HEAD`` and
  skips. Refreshing here would charge a rebuild to the next commit for no
  reason; ``--force`` is how you say "now".

Scope
-----
Local development only. By owner decision ``graphify-out/`` is git-ignored
generated data kept on the developer's machine (docs/agents/AGENT_NOTES.md,
Architectural Constraints), so a CI checkout never has the manifest that
``update`` reads.
There is no workflow for this and none can work.

Standard library only, on purpose: a git hook runs on whatever interpreter is
on PATH, not inside the project's virtualenv.

Usage::

    python scripts/dev/graphify_refresh.py            # what the hooks call
    python scripts/dev/graphify_refresh.py --force    # refresh now
    python scripts/dev/graphify_refresh.py --dry-run  # decide, change nothing

Exit codes: 0 when the run skipped or graphify succeeded; 1 when graphify
failed or could not be started. The hook wrapper ignores 1 by design, so a
broken graph can never block a commit.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GRAPH_DIR_NAME = "graphify-out"
GRAPH_FILE_NAME = "graph.json"
STATE_FILE_NAME = ".graphify_refresh_state.json"
DEFAULT_MIN_COMMITS = 5
DEFAULT_MIN_FILES = 25
GIT_TIMEOUT_SECONDS = 30
GRAPHIFY_TIMEOUT_SECONDS = 900


@dataclass(frozen=True, slots=True)
class RefreshDecision:
    """Say whether a rebuild is due, why, and the counts behind the verdict."""

    should_refresh: bool
    reason: str
    commits: int = 0
    files: int = 0
    baseline: str | None = None
    record_baseline: bool = False


def _run_git(repo_root: Path, *args: str) -> str | None:
    """Return the stripped stdout of a git command, or None when it fails.

    A failure here is not exceptional. The recorded baseline commit can be
    gone after a rebase, a squash merge or a garbage collection, and that is a
    reason to refresh rather than a reason to raise: callers treat None as
    "cannot tell, so rebuild".
    """
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def count_commits_since(repo_root: Path, baseline: str) -> int | None:
    """Count commits reachable from HEAD but not from the baseline commit."""
    output = _run_git(repo_root, "rev-list", "--count", f"{baseline}..HEAD")
    if output is None or not output.isdigit():
        return None
    return int(output)


def count_changed_files(repo_root: Path, baseline: str) -> int | None:
    """Count the files that differ between the baseline commit and HEAD."""
    output = _run_git(repo_root, "diff", "--name-only", f"{baseline}..HEAD")
    if output is None:
        return None
    return len([line for line in output.splitlines() if line.strip()])


def read_state(state_path: Path) -> dict[str, object] | None:
    """Read the refresh baseline, or None when it is absent or unreadable.

    A truncated or corrupt state file is treated as absent: the worst outcome
    is one skipped rebuild and a fresh baseline, never a failed commit.
    """
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def write_state(state_path: Path, commit: str, *, now: datetime | None = None) -> None:
    """Stamp the baseline commit that the next threshold window counts from."""
    stamp = now or datetime.now(timezone.utc)
    payload = {
        "last_refresh_commit": commit,
        "last_refresh_at": stamp.replace(microsecond=0).isoformat(),
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def evaluate(
    *,
    repo_root: Path,
    graph_dir: Path | None = None,
    min_commits: int = DEFAULT_MIN_COMMITS,
    min_files: int = DEFAULT_MIN_FILES,
    force: bool = False,
) -> RefreshDecision:
    """Decide whether a refresh is due, changing no repository state.

    The order of these checks is the contract. A graph that does not exist
    outranks ``force``, because ``update`` cannot create one. ``force``
    outranks the baseline and the thresholds, because a person asking for a
    rebuild now should not have to wait for a counter.
    """
    graph_dir = graph_dir if graph_dir is not None else repo_root / GRAPH_DIR_NAME
    if not (graph_dir / GRAPH_FILE_NAME).is_file():
        return RefreshDecision(
            should_refresh=False,
            reason=(
                f"no {GRAPH_DIR_NAME}/{GRAPH_FILE_NAME} to update; build the graph once "
                "with /graphify, then this hook maintains it"
            ),
        )

    state = read_state(graph_dir / STATE_FILE_NAME)
    recorded = state.get("last_refresh_commit") if state else None
    baseline = recorded if isinstance(recorded, str) and recorded else None

    if force:
        return RefreshDecision(
            should_refresh=True,
            reason="refresh forced",
            baseline=baseline,
            record_baseline=baseline is None,
        )

    if baseline is None:
        return RefreshDecision(
            should_refresh=False,
            reason="no refresh baseline yet; recorded HEAD, counting starts here",
            record_baseline=True,
        )

    commits = count_commits_since(repo_root, baseline)
    if commits is None:
        return RefreshDecision(
            should_refresh=True,
            reason=f"baseline {baseline[:8]} is not in this clone's history",
            baseline=baseline,
        )

    files = count_changed_files(repo_root, baseline) or 0
    counts = f"{commits} commit(s) and {files} file(s) since {baseline[:8]}"
    if commits >= min_commits or files >= min_files:
        return RefreshDecision(
            should_refresh=True,
            reason=(
                f"{counts} crossed the {min_commits}-commit or "
                f"{min_files}-file threshold"
            ),
            commits=commits,
            files=files,
            baseline=baseline,
        )
    return RefreshDecision(
        should_refresh=False,
        reason=(
            f"{counts}; {min_commits} commits or {min_files} files trigger a refresh"
        ),
        commits=commits,
        files=files,
        baseline=baseline,
    )


def refresh(*, repo_root: Path, graph_dir: Path | None = None) -> int:
    """Run the incremental rebuild and stamp the baseline only on success.

    Returns 0 when the graph was rebuilt, or when graphify is not installed
    here at all, and 1 when graphify failed. A failure leaves the baseline
    untouched, which keeps the threshold tripped so the next commit retries
    instead of the state claiming a freshness the graph does not have.
    """
    graph_dir = graph_dir if graph_dir is not None else repo_root / GRAPH_DIR_NAME
    executable = shutil.which("graphify")
    if executable is None:
        print("graphify-refresh: graphify is not on PATH; nothing to refresh")
        return 0

    try:
        completed = subprocess.run(
            [executable, "update", "."],
            cwd=repo_root,
            timeout=GRAPHIFY_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(f"graphify-refresh: graphify failed to start: {error}", file=sys.stderr)
        return 1

    if completed.returncode != 0:
        print(
            f"graphify-refresh: graphify exited {completed.returncode}; baseline left "
            "unchanged so the next commit retries",
            file=sys.stderr,
        )
        return 1

    head = _run_git(repo_root, "rev-parse", "HEAD") or ""
    write_state(graph_dir / STATE_FILE_NAME, head)
    print("graphify-refresh: graph rebuilt")
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the thresholds, the action flags, and the repository root."""
    parser = argparse.ArgumentParser(
        description="Refresh the local graphify graph once enough work has accumulated."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="repository to measure and rebuild (default: this checkout)",
    )
    parser.add_argument(
        "--min-commits",
        type=int,
        default=DEFAULT_MIN_COMMITS,
        help="commits since the last refresh that trigger a rebuild",
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=DEFAULT_MIN_FILES,
        help="changed files since the last refresh that trigger a rebuild",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="rebuild now, ignoring the thresholds and the baseline",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="decide and report, but change nothing",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print nothing unless a rebuild runs (used by the git hooks)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Report the verdict and, when one is due, run the incremental rebuild."""
    args = _parse_args(argv)
    repo_root = args.repo_root.resolve()

    decision = evaluate(
        repo_root=repo_root,
        min_commits=args.min_commits,
        min_files=args.min_files,
        force=args.force,
    )

    if not decision.should_refresh:
        if args.dry_run:
            if not args.quiet:
                print(f"graphify-refresh: would skip ({decision.reason})")
            return 0
        if decision.record_baseline:
            head = _run_git(repo_root, "rev-parse", "HEAD") or ""
            write_state(repo_root / GRAPH_DIR_NAME / STATE_FILE_NAME, head)
        if not args.quiet:
            print(f"graphify-refresh: skipped ({decision.reason})")
        return 0

    if args.dry_run:
        if not args.quiet:
            print(f"graphify-refresh: would refresh ({decision.reason})")
        return 0

    if not args.quiet:
        print(f"graphify-refresh: refreshing ({decision.reason})")
    return refresh(repo_root=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
