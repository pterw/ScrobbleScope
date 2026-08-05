"""CLI entry point, file I/O, and path constants for docsync."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from docsync.integrity import collect_integrity_issues, collect_tracked_paths
from docsync.logic import (
    _merge_entries_into_log,
    _split_archive,
    _sync,
)
from docsync.models import IntegrityIssue, SyncError

REPO_ROOT = Path(".")
PLAYBOOK_PATH = Path("PLAYBOOK.md")
ARCHIVE_PATH = Path("docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md")
SESSION_CONTEXT_PATH = Path(".claude/SESSION_CONTEXT.md")
LOGS_DIR = Path("docs/history/logs")
DEFINITIONS_DIR = Path("docs/history/definitions")
LIVE_DOCUMENT_PATHS = (
    Path("AGENTS.md"),
    Path("HANDOFF_PROMPT.md"),
    Path("AGENT_NOTES.md"),
    PLAYBOOK_PATH,
    Path("FINDINGS.md"),
)

_BATCH_LOG_RE = re.compile(r"^BATCH(\d+)_LOG\.md$", re.IGNORECASE)


def _get_batch_log_path(batch_num: int) -> Path:
    """Return the canonical path for a per-batch execution log file."""
    return LOGS_DIR / f"BATCH{batch_num}_LOG.md"


def _check_root_batch_files(root: Path) -> list[str]:
    """Scan root for unarchived BATCH*.md files and return warning strings."""
    warnings = []
    for f in sorted(root.glob("BATCH*.md")):
        warnings.append(
            f"Root BATCH file detected: {f.name} should be archived under docs/history/definitions/."
        )
    return warnings


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        raise SyncError(f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def _read_lines_optional(path: Path) -> list[str] | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _read_batch_log_lines() -> dict[int, list[str]]:
    """Read all existing per-batch log files from LOGS_DIR."""
    result: dict[int, list[str]] = {}
    if not LOGS_DIR.exists():
        return result
    for batch_log_path in sorted(LOGS_DIR.glob("BATCH*_LOG.md")):
        m = _BATCH_LOG_RE.match(batch_log_path.name)
        if m:
            result[int(m.group(1))] = _read_lines(batch_log_path)
    return result


def _repository_relative(path: Path) -> str:
    """Return a normalized repository-relative key for integrity diagnostics."""
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _read_live_documents() -> dict[str, list[str]]:
    """Load canonical documents and root batch definitions for integrity checks."""
    documents = {
        _repository_relative(path): _read_lines(path) for path in LIVE_DOCUMENT_PATHS
    }
    for definition_path in REPO_ROOT.glob("BATCH*.md"):
        documents[_repository_relative(definition_path)] = _read_lines(definition_path)
    return documents


def _format_issue(issue: IntegrityIssue) -> str:
    """Render one stable, repository-relative integrity diagnostic."""
    location = issue.path
    if issue.line is not None:
        location = f"{location}:{issue.line}"
    return (
        f"{issue.severity.upper()} {issue.code} {location} -- "
        f"{issue.invariant}\nRemediation: {issue.remediation}"
    )


def _changed_paths(result, current_session: list[str] | None) -> list[Path]:
    """Return deterministic outputs whose on-disk state differs from a sync result."""
    changed: list[Path] = []
    if _read_lines(PLAYBOOK_PATH) != result.playbook_lines:
        changed.append(PLAYBOOK_PATH)
    if _read_lines(ARCHIVE_PATH) != result.archive_lines:
        changed.append(ARCHIVE_PATH)
    for batch_num, new_batch_lines in result.batch_log_updates.items():
        batch_log_path = _get_batch_log_path(batch_num)
        if _read_lines_optional(batch_log_path) != new_batch_lines:
            changed.append(batch_log_path)
    if result.session_lines is not None and current_session != result.session_lines:
        changed.append(SESSION_CONTEXT_PATH)
    return changed


def _collect_current_integrity_issues(
    expected_session_lines: list[str] | None,
) -> list[IntegrityIssue]:
    """Collect final-state integrity issues from the repository's live documents."""
    current_playbook = _read_lines(PLAYBOOK_PATH)
    current_archive = _read_lines(ARCHIVE_PATH)
    current_session = _read_lines_optional(SESSION_CONTEXT_PATH)
    return collect_integrity_issues(
        repo_root=REPO_ROOT,
        live_documents=_read_live_documents(),
        playbook_lines=current_playbook,
        archive_lines=current_archive,
        session_lines=current_session,
        expected_session_lines=expected_session_lines,
        tracked_paths=collect_tracked_paths(REPO_ROOT),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync PLAYBOOK/SESSION_CONTEXT/archive state deterministically."
    )
    parser.add_argument(
        "--check", action="store_true", help="Validate state only (no file writes)."
    )
    parser.add_argument(
        "--fix", action="store_true", help="Apply deterministic state updates to files."
    )
    parser.add_argument(
        "--split-archive",
        action="store_true",
        help=(
            "One-time migration: split the monolith archive into per-batch log files. "
            "Mutually exclusive with --check and --fix."
        ),
    )
    parser.add_argument(
        "--keep-non-current",
        type=int,
        default=4,
        help="How many non-current entries to keep in PLAYBOOK section 4 (default: 4).",
    )
    args = parser.parse_args()

    mode_count = sum([args.check, args.fix, args.split_archive])
    if mode_count > 1:
        print(
            "Use exactly one mode: --check, --fix, or --split-archive.",
            file=sys.stderr,
        )
        return 2

    if not args.check and not args.fix and not args.split_archive:
        print("No mode selected; defaulting to --check.", file=sys.stderr)
        args.check = True

    if args.keep_non_current < 0:
        print("--keep-non-current must be >= 0.", file=sys.stderr)
        return 2

    # ------------------------------------------------------------------ #
    # --split-archive mode                                                 #
    # ------------------------------------------------------------------ #
    if args.split_archive:
        try:
            archive_lines = _read_lines(ARCHIVE_PATH)
        except SyncError as exc:
            print(f"doc_state_sync failed: {exc}", file=sys.stderr)
            return 2

        remaining_lines, batch_groups = _split_archive(archive_lines)
        written: list[Path] = []

        for batch_num, new_entries in sorted(batch_groups.items()):
            batch_log_path = _get_batch_log_path(batch_num)
            existing = _read_lines_optional(batch_log_path) or []
            merged = _merge_entries_into_log(existing, new_entries, batch_num)
            current_on_disk = _read_lines_optional(batch_log_path)
            if current_on_disk != merged:
                _write_lines(batch_log_path, merged)
                written.append(batch_log_path)

        current_archive = _read_lines(ARCHIVE_PATH)
        if current_archive != remaining_lines:
            _write_lines(ARCHIVE_PATH, remaining_lines)
            written.append(ARCHIVE_PATH)

        if written:
            print("doc_state_sync --split-archive wrote:")
            for p in written:
                print(f"- {p}")
        else:
            print("doc_state_sync --split-archive: no changes needed.")
        print(
            f"doc_state_sync --split-archive summary: "
            f"{len(batch_groups)} batch(es) found, "
            f"{len(written)} file(s) written."
        )
        return 0

    # ------------------------------------------------------------------ #
    # --check / --fix modes                                                #
    # ------------------------------------------------------------------ #
    try:
        playbook_lines = _read_lines(PLAYBOOK_PATH)
        archive_lines = _read_lines(ARCHIVE_PATH)
        session_lines = _read_lines_optional(SESSION_CONTEXT_PATH)
        batch_log_lines = _read_batch_log_lines()
        result = _sync(
            playbook_lines=playbook_lines,
            archive_lines=archive_lines,
            session_lines=session_lines,
            keep_non_current=args.keep_non_current,
            batch_log_lines=batch_log_lines,
        )
    except SyncError as exc:
        print(f"doc_state_sync failed: {exc}", file=sys.stderr)
        return 2

    current_session = _read_lines_optional(SESSION_CONTEXT_PATH)
    changed = _changed_paths(result, current_session)

    if args.check:
        try:
            issues = _collect_current_integrity_issues(result.session_lines)
        except SyncError as exc:
            print(f"doc_state_sync failed: {exc}", file=sys.stderr)
            return 2
        for issue in issues:
            print(_format_issue(issue), file=sys.stderr)
        for warning in _check_root_batch_files(REPO_ROOT):
            print(f"WARNING: {warning}", file=sys.stderr)
        if changed:
            print("doc_state_sync drift detected:")
            for path in changed:
                print(f"- {path}")
            print("Run: python scripts/doc_state_sync.py --fix")
        if changed or any(issue.severity == "error" for issue in issues):
            return 1
        print(
            "doc_state_sync check passed "
            f"(current_batch_entries={result.current_batch_entry_count}, "
            f"kept_non_current={result.kept_non_current_count}, "
            f"rotated={result.rotated_count})."
        )
        return 0

    # args.fix: write only deterministic renderer output, then validate the
    # resulting disk state. Semantic integrity issues remain for a human fix.
    if changed:
        if PLAYBOOK_PATH in changed:
            _write_lines(PLAYBOOK_PATH, result.playbook_lines)
        if ARCHIVE_PATH in changed:
            _write_lines(ARCHIVE_PATH, result.archive_lines)
        for batch_num, new_batch_lines in result.batch_log_updates.items():
            batch_log_path = _get_batch_log_path(batch_num)
            if batch_log_path in changed:
                _write_lines(batch_log_path, new_batch_lines)
        if SESSION_CONTEXT_PATH in changed and result.session_lines is not None:
            _write_lines(SESSION_CONTEXT_PATH, result.session_lines)
        print("doc_state_sync wrote updates:")
        for path in changed:
            print(f"- {path}")
    else:
        print("doc_state_sync --fix found no changes.")

    try:
        final_playbook = _read_lines(PLAYBOOK_PATH)
        final_archive = _read_lines(ARCHIVE_PATH)
        final_session = _read_lines_optional(SESSION_CONTEXT_PATH)
        final_result = _sync(
            playbook_lines=final_playbook,
            archive_lines=final_archive,
            session_lines=final_session,
            keep_non_current=args.keep_non_current,
            batch_log_lines=_read_batch_log_lines(),
        )
        final_changed = _changed_paths(final_result, final_session)
        issues = _collect_current_integrity_issues(final_result.session_lines)
    except SyncError as exc:
        print(f"doc_state_sync failed: {exc}", file=sys.stderr)
        return 2
    for issue in issues:
        print(_format_issue(issue), file=sys.stderr)
    for warning in _check_root_batch_files(REPO_ROOT):
        print(f"WARNING: {warning}", file=sys.stderr)
    if final_changed or any(issue.severity == "error" for issue in issues):
        return 1

    print(
        "doc_state_sync summary "
        f"(current_batch_entries={result.current_batch_entry_count}, "
        f"kept_non_current={result.kept_non_current_count}, "
        f"rotated={result.rotated_count})."
    )
    return 0
