"""Render the read-only ScrobbleScope worktree bootstrap diagnostic.

The command delegates repository inspection to :mod:`worktree_guard`, prints
stable diagnostics for agents and humans, and exits nonzero when continuing
would be unsafe. It never refreshes refs or modifies Git, worktrees, or Python
environments; callers control base-ref freshness as documented in AGENTS.md.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.dev.worktree_guard import Diagnostic, inspect_worktree  # noqa: E402


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the comparison ref and explicit offline-mode contract."""
    parser = argparse.ArgumentParser(
        description="Diagnose local worktree lineage without changing repository state."
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="local comparison ref (default: origin/main)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="label the base result as local-ref-only",
    )
    return parser.parse_args(argv)


def _render(diagnostic: Diagnostic) -> str:
    """Render one stable diagnostic and its optional remediation."""
    line = (
        f"{diagnostic.severity} {diagnostic.code} "
        f"{diagnostic.subject} -- {diagnostic.message}"
    )
    if diagnostic.remediation:
        line += f"\nRemediation: {diagnostic.remediation}"
    return line


def main(argv: Sequence[str] | None = None) -> int:
    """Print worktree diagnostics and return nonzero when errors exist."""
    args = _parse_args(argv)
    diagnostics = inspect_worktree(
        Path.cwd(), base_ref=args.base_ref, offline=args.offline
    )
    for diagnostic in diagnostics:
        print(_render(diagnostic))
    return 1 if any(d.severity == "ERROR" for d in diagnostics) else 0


if __name__ == "__main__":
    raise SystemExit(main())
