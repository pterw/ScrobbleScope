"""Read-only repository discovery and worktree diagnostic orchestration."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path

from scripts.dev._worktree_guard_diagnostics import (
    base_ref_label,
    finish_diagnostics,
    inspection_failure_diagnostics,
    issue,
    missing_base_remediation,
)
from scripts.dev._worktree_guard_lineage import classify_lineage, parse_batch_branch
from scripts.dev._worktree_guard_runner import (
    optional_output,
    parse_counts,
    recognized_ci,
    resolve_path,
    run_git,
)
from scripts.dev._worktree_guard_types import (
    CommandResult,
    Diagnostic,
    GuardError,
    LineageSnapshot,
)
from scripts.dev._worktree_guard_venv import resolve_venv


def inspect_worktree(
    repo_root: Path,
    *,
    base_ref: str = "origin/main",
    offline: bool = False,
    environ: Mapping[str, str] = os.environ,
    runner: Callable[[Path, tuple[str, ...]], CommandResult] = run_git,
    os_name: str | None = None,
) -> list[Diagnostic]:
    """Collect local state using the host OS unless a test boundary overrides it."""
    try:
        return _inspect_worktree(
            repo_root,
            base_ref=base_ref,
            offline=offline,
            environ=environ,
            runner=runner,
            os_name=os.name if os_name is None else os_name,
        )
    except Exception:
        return inspection_failure_diagnostics(base_ref=base_ref, offline=offline)


def _inspect_worktree(
    repo_root: Path,
    *,
    base_ref: str,
    offline: bool,
    environ: Mapping[str, str],
    runner: Callable[[Path, tuple[str, ...]], CommandResult],
    os_name: str,
) -> list[Diagnostic]:
    """Collect worktree state after the public fail-closed boundary is active."""
    top_level_result = runner(repo_root, ("rev-parse", "--show-toplevel"))
    if top_level_result.returncode != 0:
        return finish_diagnostics(
            [
                issue(
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
    resolved_root = resolve_path(repo_root, top_level_result.stdout)

    git_dir_result = runner(resolved_root, ("rev-parse", "--git-dir"))
    common_dir_result = runner(resolved_root, ("rev-parse", "--git-common-dir"))
    if git_dir_result.returncode != 0 or common_dir_result.returncode != 0:
        return finish_diagnostics(
            [
                issue(
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
    git_dir = resolve_path(resolved_root, git_dir_result.stdout)
    common_dir = resolve_path(resolved_root, common_dir_result.stdout)

    # HEAD topology is resolved before PLAYBOOK is required so that a detached
    # CI checkout still skips cleanly when the document cannot be parsed.
    is_recognized_ci = recognized_ci(environ)
    branch_result = runner(
        resolved_root, ("symbolic-ref", "--quiet", "--short", "HEAD")
    )
    if branch_result.returncode == 1:
        return finish_diagnostics(
            classify_lineage(
                LineageSnapshot(
                    None,
                    None,
                    None,
                    base_ref,
                    0,
                    0,
                    None,
                    None,
                    False,
                    True,
                    is_recognized_ci,
                )
            ),
            offline=offline,
            base_ref=base_ref,
        )
    if branch_result.returncode != 0:
        raise GuardError("Git could not determine whether HEAD names a branch.")
    actual_branch = branch_result.stdout.strip()

    playbook_path = resolved_root / "PLAYBOOK.md"
    try:
        batch = parse_batch_branch(playbook_path.read_text(encoding="utf-8"))
    except (OSError, GuardError) as error:
        return finish_diagnostics(
            [
                issue(
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

    status_result = runner(resolved_root, ("status", "--porcelain"))
    if status_result.returncode != 0:
        raise GuardError("Git could not inspect the worktree status.")

    # Between batches there is no ancestry contract to enforce, so a missing
    # base is not a defect. With an active batch the base is required, but its
    # absence must not suppress the branch-state findings collected below.
    base_available = (
        runner(
            resolved_root, ("rev-parse", "--verify", f"{base_ref}^{{commit}}")
        ).returncode
        == 0
    )
    behind = ahead = 0
    head_tree = base_tree = None
    if base_available:
        counts_result = runner(
            resolved_root,
            ("rev-list", "--left-right", "--count", f"{base_ref}...HEAD"),
        )
        if counts_result.returncode != 0:
            raise GuardError("Git could not compare HEAD with the configured base ref.")
        behind, ahead = parse_counts(counts_result.stdout)
        if behind > 0 and ahead > 0:
            head_tree = optional_output(
                runner(resolved_root, ("rev-parse", "HEAD^{tree}"))
            )
            base_tree = optional_output(
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
        is_recognized_ci,
    )
    diagnostics = classify_lineage(snapshot)
    if not base_available and batch.active_batch is not None:
        label = base_ref_label(base_ref)
        diagnostics.append(
            issue(
                "ERROR",
                "WT007",
                label,
                "comparison base ref is missing from the local repository.",
                missing_base_remediation(label),
            )
        )
    venv, venv_diagnostics = resolve_venv(
        repo_root=resolved_root,
        git_dir=git_dir,
        common_dir=common_dir,
        os_name=os_name,
    )
    diagnostics.extend(venv_diagnostics)
    if venv is not None and not any(
        diagnostic.severity == "ERROR" for diagnostic in diagnostics
    ):
        kind = "linked worktree" if git_dir != common_dir else "primary checkout"
        ancestry = (
            f"branch is {behind} behind and {ahead} ahead of {base_ref_label(base_ref)}"
            if base_available
            else "branch ancestry was not compared"
        )
        message = (
            f"{ancestry}; checkout kind: {kind}; Python: {venv.python}; "
            f"pytest: {venv.pytest}; pre-commit: {venv.pre_commit}."
        )
        diagnostics.append(issue("INFO", "WT000", actual_branch, message))
    return finish_diagnostics(diagnostics, offline=offline, base_ref=base_ref)
