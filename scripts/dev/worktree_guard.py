"""Read-only Git discovery and diagnostics for repository worktree safety."""

from __future__ import annotations

import dataclasses
import os
import re
import subprocess
from collections.abc import Callable, Mapping
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
_SAFE_BASE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
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
_WT005_REMEDIATION = (
    "Stop and inspect the commit graph and tree diff. This is not the "
    "content-identical rebase-merge case; do not reset, rebase, or force-push from "
    "this diagnostic."
)


@dataclasses.dataclass(frozen=True)
class CommandResult:
    """Contain sanitized process output returned by the injectable Git runner."""

    returncode: int
    stdout: str
    stderr: str


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
    except FileNotFoundError as error:
        raise GuardError("Git executable was not found.") from error
    except subprocess.TimeoutExpired as error:
        raise GuardError("Git command timed out after 10 seconds.") from error
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def inspect_worktree(
    repo_root: Path,
    *,
    base_ref: str = "origin/main",
    offline: bool = False,
    environ: Mapping[str, str] = os.environ,
    runner: Callable[[Path, tuple[str, ...]], CommandResult] = run_git,
) -> list[Diagnostic]:
    """Collect and classify local worktree state without mutation."""
    top_level_result = runner(repo_root, ("rev-parse", "--show-toplevel"))
    if top_level_result.returncode != 0:
        return _finish_diagnostics(
            [
                _issue(
                    "ERROR",
                    "WT001",
                    str(repo_root),
                    "path is not inside a Git repository.",
                    "Stop and enter the intended ScrobbleScope checkout before continuing.",
                )
            ],
            offline=offline,
            base_ref=base_ref,
        )
    resolved_root = _resolve_path(repo_root, top_level_result.stdout)

    git_dir_result = runner(resolved_root, ("rev-parse", "--git-dir"))
    common_dir_result = runner(resolved_root, ("rev-parse", "--git-common-dir"))
    if git_dir_result.returncode != 0 or common_dir_result.returncode != 0:
        return _finish_diagnostics(
            [
                _issue(
                    "ERROR",
                    "WT001",
                    str(resolved_root),
                    "Git repository metadata could not be resolved.",
                    "Stop and inspect this checkout; the guard does not repair Git metadata.",
                )
            ],
            offline=offline,
            base_ref=base_ref,
        )
    git_dir = _resolve_path(resolved_root, git_dir_result.stdout)
    common_dir = _resolve_path(resolved_root, common_dir_result.stdout)

    playbook_path = resolved_root / "PLAYBOOK.md"
    try:
        batch = parse_batch_branch(playbook_path.read_text(encoding="utf-8"))
    except (OSError, GuardError) as error:
        return _finish_diagnostics(
            [
                _issue(
                    "ERROR",
                    "WT002",
                    str(playbook_path),
                    f"active batch metadata is unavailable: {error}",
                    "Correct PLAYBOOK Section 3 before continuing; this guard does not edit it.",
                )
            ],
            offline=offline,
            base_ref=base_ref,
        )

    recognized_ci = _recognized_ci(environ)
    branch_result = runner(
        resolved_root, ("symbolic-ref", "--quiet", "--short", "HEAD")
    )
    if branch_result.returncode == 1:
        return _finish_diagnostics(
            classify_lineage(
                LineageSnapshot(
                    batch.active_batch,
                    batch.expected_branch,
                    None,
                    base_ref,
                    0,
                    0,
                    None,
                    None,
                    False,
                    True,
                    recognized_ci,
                )
            ),
            offline=offline,
            base_ref=base_ref,
        )
    if branch_result.returncode != 0:
        raise GuardError("Git could not determine whether HEAD names a branch.")
    actual_branch = branch_result.stdout.strip()

    base_result = runner(
        resolved_root, ("rev-parse", "--verify", f"{base_ref}^{{commit}}")
    )
    if base_result.returncode != 0:
        label = _base_ref_label(base_ref)
        return _finish_diagnostics(
            [
                _issue(
                    "ERROR",
                    "WT007",
                    label,
                    "comparison base ref is missing from the local repository.",
                    _missing_base_remediation(label),
                )
            ],
            offline=offline,
            base_ref=base_ref,
        )

    counts_result = runner(
        resolved_root,
        ("rev-list", "--left-right", "--count", f"{base_ref}...HEAD"),
    )
    if counts_result.returncode != 0:
        raise GuardError("Git could not compare HEAD with the configured base ref.")
    behind, ahead = _parse_counts(counts_result.stdout)

    status_result = runner(resolved_root, ("status", "--porcelain"))
    if status_result.returncode != 0:
        raise GuardError("Git could not inspect the worktree status.")

    head_tree = base_tree = None
    if behind > 0 and ahead > 0:
        head_tree = _optional_output(
            runner(resolved_root, ("rev-parse", "HEAD^{tree}"))
        )
        base_tree = _optional_output(
            runner(resolved_root, ("rev-parse", f"{base_ref}^{{tree}}"))
        )

    snapshot = LineageSnapshot(
        batch.active_batch,
        batch.expected_branch,
        actual_branch,
        base_ref,
        behind,
        ahead,
        head_tree,
        base_tree,
        bool(status_result.stdout),
        False,
        recognized_ci,
    )
    diagnostics = classify_lineage(snapshot)
    venv, venv_diagnostics = resolve_venv(
        repo_root=resolved_root,
        git_dir=git_dir,
        common_dir=common_dir,
        os_name=os.name,
    )
    diagnostics.extend(venv_diagnostics)
    if venv is not None and not any(
        diagnostic.severity == "ERROR" for diagnostic in diagnostics
    ):
        kind = "linked worktree" if git_dir != common_dir else "primary checkout"
        message = (
            f"branch is {behind} behind and {ahead} ahead of {base_ref}; "
            f"checkout kind: {kind}; Python: {venv.python}; pytest: {venv.pytest}; "
            f"pre-commit: {venv.pre_commit}."
        )
        diagnostics.append(_issue("INFO", "WT000", actual_branch, message))
    return _finish_diagnostics(diagnostics, offline=offline, base_ref=base_ref)


def _resolve_path(parent: Path, output: str) -> Path:
    """Resolve Git path output relative to the repository top level."""
    candidate = Path(output.strip())
    return (candidate if candidate.is_absolute() else parent / candidate).resolve()


def _recognized_ci(environ: Mapping[str, str]) -> bool:
    """Recognize only explicit truthy CI variables from the stable contract."""
    truthy = {"1", "true", "yes"}
    return any(
        str(environ.get(name, "")).strip().lower() in truthy
        for name in ("CI", "GITHUB_ACTIONS")
    )


def _parse_counts(output: str) -> tuple[int, int]:
    """Parse Git's base-left rev-list result as behind then ahead counts."""
    fields = output.split()
    try:
        if len(fields) != 2:
            raise ValueError
        return int(fields[0]), int(fields[1])
    except ValueError as error:
        raise GuardError("Git returned malformed ancestry counts.") from error


def _optional_output(result: CommandResult) -> str | None:
    """Return stripped Git output when available for conservative classification."""
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _finish_diagnostics(
    diagnostics: list[Diagnostic], *, offline: bool, base_ref: str
) -> list[Diagnostic]:
    """Append the independent offline qualifier after all state diagnostics."""
    if offline:
        diagnostics.append(
            _issue(
                "INFO",
                "WT013",
                _base_ref_label(base_ref),
                "offline mode; any base comparison is local-ref-only and freshness "
                "was not verified.",
            )
        )
    return diagnostics


def _base_ref_label(base_ref: str) -> str:
    """Return a display-safe ref label without changing the Git argument value."""
    invalid = (
        not _SAFE_BASE_REF_RE.fullmatch(base_ref)
        or ".." in base_ref
        or "//" in base_ref
        or base_ref.endswith(("/", ".", ".lock"))
    )
    return "configured base ref" if invalid else base_ref


def _missing_base_remediation(base_ref: str) -> str:
    """Describe recovery for a selected base without inventing a remote command."""
    if "/" not in base_ref or base_ref.startswith("refs/"):
        return (
            f"Verify the local base ref {base_ref} exists and is current, then rerun "
            "the guard. This guard does not fetch."
        )
    return (
        f"Refresh or otherwise verify the selected base ref {base_ref} exists locally "
        "and is current, then rerun the guard. This guard does not fetch."
    )


def _identical_tree_remediation(base_ref: str) -> str:
    """Build WT004 guidance around the selected, display-safe comparison ref."""
    label = _base_ref_label(base_ref)
    refresh = (
        f"refresh {label}"
        if "/" in label and not label.startswith("refs/")
        else f"verify the local base ref {label} is current"
    )
    return (
        f"Stop. Reconcile any dirty files, {refresh}, verify the trees again, "
        "obtain the explicit owner approval required by AGENTS.md, then realign the "
        "named branch and use force-push with lease. This guard performs none of "
        "those actions."
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
    base_ref = _base_ref_label(snapshot.base_ref)
    if snapshot.behind > 0 and snapshot.ahead == 0:
        issues.append(
            _issue(
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
            ("WT004", "tree-identical", _identical_tree_remediation(base_ref))
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
                f"branch and {base_ref} are {snapshot.behind}/{snapshot.ahead} diverged but {state}.",
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
