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


def is_display_safe_ref(ref: str) -> bool:
    """Report whether a ref name is safe to interpolate into a diagnostic.

    Every WT diagnostic prints ref names verbatim, so this is an allowlist
    rather than a list of known-bad characters. A denylist has to anticipate
    each vector -- a line break forges a second diagnostic line, an escape
    sequence repaints the current one, and non-ASCII spaces such as U+00A0
    pad a fake verdict across it without using any ASCII character at all.
    Restricting the value to a conservative ref alphabet refuses all of them,
    including the ones nobody enumerated. The alphabet is deliberately
    narrower than Git's own ref rule -- Git accepts names this rejects, such
    as those holding non-ASCII characters -- because the property being
    enforced is display safety, not Git validity.
    """
    return not (
        not _SAFE_BASE_REF_RE.fullmatch(ref)
        or ".." in ref
        or "//" in ref
        or ref.endswith(("/", ".", ".lock"))
    )


def base_ref_label(base_ref: str) -> str:
    """Return a display-safe ref label without changing the Git argument value."""
    return base_ref if is_display_safe_ref(base_ref) else "configured base ref"


def branch_label(branch: str | None, fallback: str) -> str:
    """Return a display-safe subject for the branch that is checked out.

    WT000, WT003, WT004, WT005, WT006 and WT010 all render this value. The
    expected branch is filtered when Section 3 is parsed and the base ref is
    labelled here, so this was the one rendered ref answering to no rule --
    the same DRY failure that produced the previous round's defect, one value
    further along. Git accepts ref names this guard must never print: it
    rejects control characters and the ASCII space, but permits U+00A0,
    U+2028 and U+202E, which pad, split and reorder a rendered line.

    The value is labelled at render time rather than discarded at collection
    time, because the property enforced is display safety, not Git validity;
    the snapshot goes on naming whatever Git reported. Absent and unprintable
    both mean the guard cannot name the branch, so both degrade to the
    caller's neutral noun while the message and remediation keep carrying the
    actionable text.
    """
    if not branch:
        return fallback
    return branch if is_display_safe_ref(branch) else fallback


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


def metadata_unavailable_diagnostic(detail: str) -> Diagnostic:
    """Report unusable Section 3 metadata without leaking filesystem detail."""
    return issue(
        "ERROR",
        "WT002",
        "PLAYBOOK.md",
        f"active batch metadata is unavailable: {detail}",
        "Correct PLAYBOOK Section 3 before continuing; this guard does not edit it.",
    )


def missing_base_diagnostic(base_ref: str) -> Diagnostic:
    """Report an absent comparison base against the display-safe ref label."""
    label = base_ref_label(base_ref)
    return issue(
        "ERROR",
        "WT007",
        label,
        "comparison base ref is missing from the local repository.",
        missing_base_remediation(label),
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
