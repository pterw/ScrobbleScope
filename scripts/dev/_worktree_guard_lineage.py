"""PLAYBOOK parsing and pure worktree-lineage classification."""

import re

from scripts.dev._worktree_guard_diagnostics import (
    WT005_REMEDIATION,
    base_ref_label,
    identical_tree_remediation,
    issue,
)
from scripts.dev._worktree_guard_types import (
    BatchBranch,
    Diagnostic,
    GuardError,
    LineageSnapshot,
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
                issue(
                    "INFO",
                    "WT011",
                    "detached HEAD",
                    "recognized CI checkout; live branch topology is skipped.",
                )
            ]
        return [
            issue(
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
            issue(
                "ERROR",
                "WT002",
                f"Batch {snapshot.active_batch}",
                "active batch branch metadata is missing from PLAYBOOK Section 3.",
                "Add the owner-approved stable Branch metadata to PLAYBOOK Section 3 before continuing.",
            )
        )
    elif snapshot.actual_branch != snapshot.expected_branch:
        issues.append(
            issue(
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
    base_ref = base_ref_label(snapshot.base_ref)
    if snapshot.behind > 0 and snapshot.ahead == 0:
        issues.append(
            issue(
                "ERROR",
                "WT006",
                subject,
                f"branch is {snapshot.behind} commit(s) behind {base_ref}.",
                "Stop and inspect the branch state before beginning work; this guard "
                "does not merge, rebase, reset, or switch branches.",
            )
        )
    elif snapshot.behind > 0 and snapshot.ahead > 0:
        identical = bool(
            snapshot.head_tree and snapshot.head_tree == snapshot.base_tree
        )
        code, state, remediation = (
            ("WT004", "tree-identical", identical_tree_remediation(base_ref))
            if identical
            else (
                "WT005",
                "different or unavailable tree identities",
                WT005_REMEDIATION,
            )
        )
        issues.append(
            issue(
                "ERROR",
                code,
                subject,
                f"branch and {base_ref} are {snapshot.behind}/{snapshot.ahead} diverged but {state}.",
                remediation,
            )
        )
    return issues


def _dirty(snapshot: LineageSnapshot) -> Diagnostic:
    """Return the standard non-blocking dirty-worktree diagnostic."""
    return issue(
        "WARNING",
        "WT010",
        snapshot.actual_branch or "worktree",
        "tracked or untracked files are present in the worktree.",
        "Reconcile the dirty files before any history repair; this guard does not modify them.",
    )
