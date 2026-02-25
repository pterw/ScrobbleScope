"""CLI entry point, file I/O, and path constants for docsync."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from docsync.logic import (
    _cross_validate,
    _merge_entries_into_log,
    _split_archive,
    _sync,
)

PLAYBOOK_PATH = Path("PLAYBOOK.md")
ARCHIVE_PATH = Path("docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md")
SESSION_CONTEXT_PATH = Path(".claude/SESSION_CONTEXT.md")
LOGS_DIR = Path("docs/history/logs")
DEFINITIONS_DIR = Path("docs/history/definitions")

_BATCH_LOG_RE = re.compile(r"^BATCH(\d+)_LOG\.md$", re.IGNORECASE)


def _get_batch_log_path(batch_num: int) -> Path:
    """Return the canonical path for a per-batch execution log file."""
    return LOGS_DIR / f"BATCH{batch_num}_LOG.md"


def _check_root_batch_files(root: Path) -> list[str]:
    """Scan root for unarchived BATCH*.md files and return warning strings."""
    warnings = []
    for f in sorted(root.glob("BATCH*.md")):
        warnings.append(
            f"Root BATCH file detected: {f.name} should be archived under docs/history/."
        )
    return warnings


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

    from docsync.models import SyncError

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

    current_playbook = _read_lines(PLAYBOOK_PATH)
    current_archive = _read_lines(ARCHIVE_PATH)
    current_session = _read_lines_optional(SESSION_CONTEXT_PATH)

    xv_warnings = _cross_validate(playbook_lines, session_lines)
    xv_warnings += _check_root_batch_files(Path("."))
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
    for batch_num, new_batch_lines in result.batch_log_updates.items():
        batch_log_path = _get_batch_log_path(batch_num)
        current_batch = _read_lines_optional(batch_log_path)
        if current_batch != new_batch_lines:
            changed.append(batch_log_path)

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
        for batch_num, new_batch_lines in result.batch_log_updates.items():
            batch_log_path = _get_batch_log_path(batch_num)
            if batch_log_path in changed:
                _write_lines(batch_log_path, new_batch_lines)
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
