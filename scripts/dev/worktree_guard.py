"""Pure detection and diagnostics for repository worktree safety."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.dev._worktree_guard_types import (
    BatchBranch,
    Diagnostic,
    GuardError,
    LineageSnapshot,
    Severity,
    VenvPaths,
)

SECTION_3_RE = re.compile(r"^##\s*3\.?\s*Active\s+batch\b.*$", re.IGNORECASE)
GENERIC_SECTION_RE = re.compile(r"^##\s+")
ACTIVE_BATCH_RE = re.compile(
    r"\bBatch\s+(\d+)\s+is\s+(?:active|current|in[\s-]?progress)\b",
    re.IGNORECASE,
)
BRANCH_RE = re.compile(r"\bBranch:\s*`([^`]+)`", re.IGNORECASE)
_ACTIVE_MARKER_RE = re.compile(
    r"\bBatch\b[^\n]*\bis\s+(?:active|current|in[\s-]?progress)\b",
    re.IGNORECASE,
)
WINDOWS_TOOLS = {
    "python": Path("Scripts/python.exe"),
    "pytest": Path("Scripts/pytest.exe"),
    "pre_commit": Path("Scripts/pre-commit.exe"),
}
POSIX_TOOLS = {
    "python": Path("bin/python"),
    "pytest": Path("bin/pytest"),
    "pre_commit": Path("bin/pre-commit"),
}
_WT004_REMEDIATION = (
    "Stop. Reconcile any dirty files, refresh origin/main, verify the trees again, "
    "obtain the explicit owner approval required by AGENTS.md, then realign the "
    "named branch and use force-push with lease. This guard performs none of those "
    "actions."
)
_WT005_REMEDIATION = (
    "Stop and inspect the commit graph and tree diff. This is not the "
    "content-identical rebase-merge case; do not reset, rebase, or force-push from "
    "this diagnostic."
)


def parse_batch_branch(playbook_text: str) -> BatchBranch:
    """Parse the active batch and stable branch from PLAYBOOK Section 3."""
    lines = playbook_text.splitlines()
    starts = [i for i, line in enumerate(lines) if SECTION_3_RE.match(line)]
    if len(starts) != 1:
        raise GuardError("PLAYBOOK must contain exactly one Section 3 heading.")
    start = starts[0] + 1
    end = next(
        (i for i in range(start, len(lines)) if GENERIC_SECTION_RE.match(lines[i])),
        len(lines),
    )
    section = "\n".join(lines[start:end])
    active = list(ACTIVE_BATCH_RE.finditer(section))
    if len(active) != len(list(_ACTIVE_MARKER_RE.finditer(section))):
        raise GuardError("PLAYBOOK Section 3 has malformed active batch metadata.")
    if len(active) > 1:
        raise GuardError("PLAYBOOK Section 3 has duplicate active batch metadata.")
    branches = list(BRANCH_RE.finditer(section))
    if len(branches) > 1:
        raise GuardError("PLAYBOOK Section 3 has duplicate branch metadata.")
    if not active:
        return BatchBranch(None, None)
    branch = branches[0].group(1) if branches else None
    return BatchBranch(int(active[0].group(1)), branch)


def classify_lineage(snapshot: LineageSnapshot) -> list[Diagnostic]:
    """Classify branch ancestry without running or mutating Git."""
    if snapshot.detached:
        if snapshot.recognized_ci:
            return [
                _issue(
                    "INFO",
                    "WT011",
                    "detached HEAD",
                    "recognized CI checkout; live branch topology is skipped.",
                )
            ]
        return [
            _issue(
                "ERROR",
                "WT012",
                "detached HEAD",
                "local work requires a named branch before lineage can be checked.",
                "Stop and ask the owner which existing branch should be used; "
                "this guard does not switch or create branches.",
            )
        ]

    if snapshot.active_batch is None:
        return [_dirty(snapshot)] if snapshot.dirty else []

    issues: list[Diagnostic] = []
    if snapshot.expected_branch is None:
        issues.append(
            _issue(
                "ERROR",
                "WT002",
                f"Batch {snapshot.active_batch}",
                "active batch branch metadata is missing from PLAYBOOK Section 3.",
                "Add the owner-approved stable Branch metadata to PLAYBOOK Section 3 before continuing.",
            )
        )
    elif snapshot.actual_branch != snapshot.expected_branch:
        issues.append(
            _issue(
                "ERROR",
                "WT003",
                snapshot.actual_branch or "unnamed branch",
                f"active Batch {snapshot.active_batch} requires branch {snapshot.expected_branch}.",
                "Stop and move the work to the named branch only with the owner's "
                "direction; this guard does not switch branches.",
            )
        )
    if snapshot.dirty:
        issues.append(_dirty(snapshot))
    if snapshot.expected_branch is None:
        return issues

    subject = snapshot.expected_branch
    if snapshot.behind > 0 and snapshot.ahead == 0:
        issues.append(
            _issue(
                "ERROR",
                "WT006",
                subject,
                f"branch is {snapshot.behind} commit(s) behind {snapshot.base_ref}.",
                "Stop and inspect the branch state before beginning work; this guard "
                "does not merge, rebase, reset, or switch branches.",
            )
        )
    elif snapshot.behind > 0 and snapshot.ahead > 0:
        identical = bool(
            snapshot.head_tree and snapshot.head_tree == snapshot.base_tree
        )
        code, state, remediation = (
            ("WT004", "tree-identical", _WT004_REMEDIATION)
            if identical
            else (
                "WT005",
                "different or unavailable tree identities",
                _WT005_REMEDIATION,
            )
        )
        issues.append(
            _issue(
                "ERROR",
                code,
                subject,
                f"branch and {snapshot.base_ref} are {snapshot.behind}/{snapshot.ahead} diverged but {state}.",
                remediation,
            )
        )
    return issues


def _issue(
    severity: Severity,
    code: str,
    subject: str,
    message: str,
    remediation: str | None = None,
) -> Diagnostic:
    """Build a diagnostic while keeping classifier branches compact."""
    return Diagnostic(severity, code, subject, message, remediation)


def _dirty(snapshot: LineageSnapshot) -> Diagnostic:
    """Return the standard non-blocking dirty-worktree diagnostic."""
    return _issue(
        "WARNING",
        "WT010",
        snapshot.actual_branch or "worktree",
        "tracked or untracked files are present in the worktree.",
        "Reconcile the dirty files before any history repair; this guard does not modify them.",
    )


def resolve_venv(
    *, repo_root: Path, git_dir: Path, common_dir: Path, os_name: str
) -> tuple[VenvPaths | None, list[Diagnostic]]:
    """Resolve the sole allowed environment for a normal or linked checkout."""
    common = common_dir.resolve()
    linked = git_dir.resolve() != common
    candidate = (common.parent if linked else repo_root) / ".venv"
    local_candidate = repo_root / ".venv"
    if (
        linked
        and local_candidate.exists()
        and local_candidate.resolve() != candidate.resolve()
    ):
        issue = _issue(
            "ERROR",
            "WT008",
            str(local_candidate),
            "linked worktree has a distinct forbidden secondary virtualenv.",
            f"Use only the primary checkout environment at {candidate}; do not "
            "install packages or create another environment here.",
        )
        return None, [issue]

    tools = WINDOWS_TOOLS if os_name == "nt" else POSIX_TOOLS
    qualified = {name: candidate / relative for name, relative in tools.items()}
    missing = [
        str(Path(".venv") / tools[name])
        for name in tools
        if not qualified[name].is_file()
    ]
    if missing:
        issue = _issue(
            "ERROR",
            "WT009",
            str(candidate),
            "required virtualenv tools are missing: " + ", ".join(missing) + ".",
            "Follow the AGENTS.md Environment Setup section in the primary checkout; "
            "do not create a secondary environment or use bare pip.",
        )
        return None, [issue]
    return (
        VenvPaths(
            candidate, qualified["python"], qualified["pytest"], qualified["pre_commit"]
        ),
        [],
    )
