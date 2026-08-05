"""Shared diagnostic construction and safe base-ref presentation."""

import re

from scripts.dev._worktree_guard_types import Diagnostic, Severity

_SAFE_BASE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
WT005_REMEDIATION = (
    "Stop and inspect the commit graph and tree diff. This is not the "
    "content-identical rebase-merge case; do not reset, rebase, or force-push from "
    "this diagnostic."
)


def issue(
    severity: Severity,
    code: str,
    subject: str,
    message: str,
    remediation: str | None = None,
) -> Diagnostic:
    """Build one immutable diagnostic from the stable public value type."""
    return Diagnostic(severity, code, subject, message, remediation)


def base_ref_label(base_ref: str) -> str:
    """Return a display-safe ref label without changing the Git argument value."""
    invalid = (
        not _SAFE_BASE_REF_RE.fullmatch(base_ref)
        or ".." in base_ref
        or "//" in base_ref
        or base_ref.endswith(("/", ".", ".lock"))
    )
    return "configured base ref" if invalid else base_ref


def missing_base_remediation(base_ref: str) -> str:
    """Preserve default recovery while keeping custom-base guidance neutral."""
    if base_ref == "origin/main":
        return (
            "When network access is available, run git fetch --prune origin, "
            "then rerun the guard. Offline, ensure the required local ref exists; "
            "this guard does not fetch."
        )
    if "/" not in base_ref or base_ref.startswith("refs/"):
        return (
            f"Verify the local base ref {base_ref} exists and is current, then rerun "
            "the guard. This guard does not fetch."
        )
    return (
        f"Refresh or otherwise verify the selected base ref {base_ref} exists locally "
        "and is current, then rerun the guard. This guard does not fetch."
    )


def identical_tree_remediation(base_ref: str) -> str:
    """Build WT004 guidance around the selected, display-safe comparison ref."""
    label = base_ref_label(base_ref)
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


def finish_diagnostics(
    diagnostics: list[Diagnostic], *, offline: bool, base_ref: str
) -> list[Diagnostic]:
    """Append the independent offline qualifier after all state diagnostics."""
    if offline:
        diagnostics.append(
            issue(
                "INFO",
                "WT013",
                base_ref_label(base_ref),
                "offline mode; any base comparison is local-ref-only and freshness "
                "was not verified.",
            )
        )
    return diagnostics


def inspection_failure_diagnostics(*, base_ref: str, offline: bool) -> list[Diagnostic]:
    """Return the stable fail-closed result for unexpected inspection failures."""
    return finish_diagnostics(
        [
            issue(
                "ERROR",
                "WT014",
                "worktree inspection",
                "repository inspection failed safely.",
                "Stop and inspect local Git and repository metadata, then rerun the "
                "guard; no state was modified.",
            )
        ],
        offline=offline,
        base_ref=base_ref,
    )
