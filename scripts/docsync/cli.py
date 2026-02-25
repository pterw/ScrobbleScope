"""CLI entry point, file I/O, and path constants for docsync."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docsync.logic import _cross_validate, _sync

PLAYBOOK_PATH = Path("PLAYBOOK.md")
ARCHIVE_PATH = Path("docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md")
SESSION_CONTEXT_PATH = Path(".claude/SESSION_CONTEXT.md")


def _read_lines(path: Path) -> list[str]:
    from docsync.models import SyncError

    if not path.exists():
        raise SyncError(f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def _read_lines_optional(path: Path) -> list[str] | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: list[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


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
        "--keep-non-current",
        type=int,
        default=4,
        help="How many non-current entries to keep in PLAYBOOK section 4 (default: 4).",
    )
    args = parser.parse_args()

    if args.check and args.fix:
        print("Use exactly one mode: --check or --fix.", file=sys.stderr)
        return 2
    if not args.check and not args.fix:
        print("No mode selected; defaulting to --check.", file=sys.stderr)
        args.check = True

    if args.keep_non_current < 0:
        print("--keep-non-current must be >= 0.", file=sys.stderr)
        return 2

    from docsync.models import SyncError

    try:
        playbook_lines = _read_lines(PLAYBOOK_PATH)
        archive_lines = _read_lines(ARCHIVE_PATH)
        session_lines = _read_lines_optional(SESSION_CONTEXT_PATH)
        result = _sync(
            playbook_lines=playbook_lines,
            archive_lines=archive_lines,
            session_lines=session_lines,
            keep_non_current=args.keep_non_current,
        )
    except SyncError as exc:
        print(f"doc_state_sync failed: {exc}", file=sys.stderr)
        return 2

    current_playbook = _read_lines(PLAYBOOK_PATH)
    current_archive = _read_lines(ARCHIVE_PATH)
    current_session = _read_lines_optional(SESSION_CONTEXT_PATH)

    xv_warnings = _cross_validate(playbook_lines, session_lines)
    if xv_warnings:
        for w in xv_warnings:
            print(f"WARNING: {w}", file=sys.stderr)

    changed: list[Path] = []
    if current_playbook != result.playbook_lines:
        changed.append(PLAYBOOK_PATH)
    if current_archive != result.archive_lines:
        changed.append(ARCHIVE_PATH)
    if result.session_lines is not None and current_session != result.session_lines:
        changed.append(SESSION_CONTEXT_PATH)

    if args.check:
        if changed:
            print("doc_state_sync drift detected:")
            for path in changed:
                print(f"- {path}")
            print("Run: python scripts/doc_state_sync.py --fix")
            return 1
        print(
            "doc_state_sync check passed "
            f"(current_batch_entries={result.current_batch_entry_count}, "
            f"kept_non_current={result.kept_non_current_count}, "
            f"rotated={result.rotated_count})."
        )
        return 0

    # args.fix
    if changed:
        _write_lines(PLAYBOOK_PATH, result.playbook_lines)
        _write_lines(ARCHIVE_PATH, result.archive_lines)
        if SESSION_CONTEXT_PATH in changed:
            _write_lines(SESSION_CONTEXT_PATH, result.session_lines)  # type: ignore[arg-type]
        print("doc_state_sync wrote updates:")
        for path in changed:
            print(f"- {path}")
    else:
        print("doc_state_sync --fix found no changes.")

    print(
        "doc_state_sync summary "
        f"(current_batch_entries={result.current_batch_entry_count}, "
        f"kept_non_current={result.kept_non_current_count}, "
        f"rotated={result.rotated_count})."
    )
    return 0
