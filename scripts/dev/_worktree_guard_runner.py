"""Sanitized list-argument subprocess runner for read-only Git inspection."""

import subprocess
from collections.abc import Mapping
from pathlib import Path

from scripts.dev._worktree_guard_types import CommandResult, GuardError


def run_git(repo_root: Path, args: tuple[str, ...]) -> CommandResult:
    """Run one read-only Git command and sanitize process-launch failures."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        raise GuardError("Git executable was not found.") from None
    except subprocess.TimeoutExpired:
        raise GuardError("Git command timed out after 10 seconds.") from None
    except OSError:
        raise GuardError("Git command could not be started.") from None
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def resolve_path(parent: Path, output: str) -> Path:
    """Resolve Git path output relative to the repository top level."""
    candidate = Path(output.strip())
    return (candidate if candidate.is_absolute() else parent / candidate).resolve()


def recognized_ci(environ: Mapping[str, str]) -> bool:
    """Recognize only explicit truthy CI variables from the stable contract."""
    truthy = {"1", "true", "yes"}
    return any(
        str(environ.get(name, "")).strip().lower() in truthy
        for name in ("CI", "GITHUB_ACTIONS")
    )


def parse_counts(output: str) -> tuple[int, int]:
    """Parse Git's base-left rev-list result as behind then ahead counts."""
    fields = output.split()
    try:
        if len(fields) != 2:
            raise ValueError
        return int(fields[0]), int(fields[1])
    except ValueError:
        raise GuardError("Git returned malformed ancestry counts.") from None


def optional_output(result: CommandResult) -> str | None:
    """Return stripped Git output when available for conservative classification."""
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
