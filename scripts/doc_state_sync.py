#!/usr/bin/env python3
"""Deterministically sync playbook execution state and archive rotation.

This tool makes markdown-state updates reproducible across agents:
- Enforces the PLAYBOOK Section 4 active-window policy.
- Rotates overflow dated entries into the archive file.
- Deduplicates archive entries by SHA-256 fingerprint of full entry blocks.
- Refreshes a managed status block in SESSION_CONTEXT from PLAYBOOK truth.

Usage:
  python scripts/doc_state_sync.py --check
  python scripts/doc_state_sync.py --fix
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import re
import sys
from pathlib import Path
from typing import Iterable

PLAYBOOK_PATH = Path("PLAYBOOK.md")
ARCHIVE_PATH = Path("docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md")
SESSION_CONTEXT_PATH = Path(".claude/SESSION_CONTEXT.md")

SECTION_3_RE = re.compile(
    r"^##\s*3\.?\s*Active\s+batch\b.*$",
    re.IGNORECASE,
)
SECTION_4_RE = re.compile(
    r"^##\s*4\.?\s*Execution\s+log\b.*$",
    re.IGNORECASE,
)
GENERIC_SECTION_RE = re.compile(r"^##\s+")
ENTRY_HEADING_RE = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})\s+-\s+(.+?)\s*$")
BATCH_COMPLETE_RE = re.compile(r"\bBatch\s+(\d+)\s+is\s+complete\b", re.IGNORECASE)
BATCH_NOT_DEFINED_RE = re.compile(
    r"\bBatch\s+(\d+)\s+is\s+not\s+yet\s+defined\b", re.IGNORECASE
)
BATCH_CURRENT_RE = re.compile(
    r"\bBatch\s+(\d+)\s+is\s+(?:active|current|in[\s-]?progress)\b", re.IGNORECASE
)
ENTRY_BATCH_RE = re.compile(r"\bBatch\s+(\d+)\b", re.IGNORECASE)
BATCH_NEXT_RE = re.compile(
    r"\bnext\s+batch(?:\s+to\s+execute)?[^0-9]*Batch\s+(\d+)\b",
    re.IGNORECASE,
)

CURRENT_BATCH_START_MARKER = "<!-- DOCSYNC:CURRENT-BATCH-START -->"
CURRENT_BATCH_END_MARKER = "<!-- DOCSYNC:CURRENT-BATCH-END -->"
SESSION_STATUS_START_MARKER = "<!-- DOCSYNC:STATUS-START -->"
SESSION_STATUS_END_MARKER = "<!-- DOCSYNC:STATUS-END -->"


class SyncError(RuntimeError):
    """Raised when deterministic sync cannot proceed safely."""


@dataclasses.dataclass(frozen=True)
class Entry:
    """Represents one dated execution-log entry block."""

    heading: str
    date: str
    title: str
    lines: tuple[str, ...]
    start_idx: int
    fingerprint: str


@dataclasses.dataclass(frozen=True)
class ActiveBatchState:
    """Parsed batch state signals from PLAYBOOK Section 3."""

    current_batch: int | None
    last_completed_batch: int | None
    next_undefined_batch: int | None


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        raise SyncError(f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: Iterable[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _find_section(
    lines: list[str], heading_re: re.Pattern[str], label: str
) -> tuple[int, int]:
    start = None
    for idx, line in enumerate(lines):
        if heading_re.match(line.strip()):
            start = idx
            break
    if start is None:
        raise SyncError(f"Could not find section heading for {label}.")

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if GENERIC_SECTION_RE.match(lines[idx]):
            end = idx
            break
    return start, end


def _find_marker_pair(
    lines: list[str], start_marker: str, end_marker: str, label: str
) -> tuple[int, int]:
    starts = [i for i, line in enumerate(lines) if line.strip() == start_marker]
    ends = [i for i, line in enumerate(lines) if line.strip() == end_marker]
    if not starts or not ends:
        raise SyncError(
            f"{label} must contain start marker ({start_marker}) and end marker ({end_marker})."
        )
    start_idx = starts[0]
    end_idx = ends[-1]
    if start_idx >= end_idx:
        raise SyncError(
            f"{label} marker order is invalid: start marker is after end marker."
        )
    return start_idx, end_idx


def _normalize_block(lines: Iterable[str]) -> str:
    normalized = "\n".join(line.rstrip() for line in lines).strip() + "\n"
    return normalized


def _fingerprint(lines: Iterable[str]) -> str:
    normalized = _normalize_block(lines)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _parse_entries(lines: list[str]) -> tuple[list[Entry], int | None]:
    heading_idxs: list[int] = []
    for idx, line in enumerate(lines):
        if ENTRY_HEADING_RE.match(line):
            heading_idxs.append(idx)

    if not heading_idxs:
        return [], None

    entries: list[Entry] = []
    for pos, start_idx in enumerate(heading_idxs):
        end_idx = heading_idxs[pos + 1] if pos + 1 < len(heading_idxs) else len(lines)
        block = list(lines[start_idx:end_idx])
        while block and block[-1].strip() == "":
            block.pop()
        block_lines = tuple(block)
        heading = block_lines[0]
        match = ENTRY_HEADING_RE.match(heading)
        if not match:
            raise SyncError(f"Malformed entry heading: {heading}")
        date, title = match.group(1), match.group(2)
        entries.append(
            Entry(
                heading=heading,
                date=date,
                title=title,
                lines=block_lines,
                start_idx=start_idx,
                fingerprint=_fingerprint(block_lines),
            )
        )

    return entries, heading_idxs[0]


def _trim_trailing_blank(lines: list[str]) -> list[str]:
    out = list(lines)
    while out and out[-1].strip() == "":
        out.pop()
    return out


def _render_section4(
    prefix_lines: list[str], current_entries: list[Entry], non_current_kept: list[Entry]
) -> list[str]:
    out = _trim_trailing_blank(prefix_lines)
    out.append("")
    out.append(CURRENT_BATCH_START_MARKER)
    out.append("")

    for entry in current_entries:
        out.extend(entry.lines)
        out.append("")

    out.append(CURRENT_BATCH_END_MARKER)

    if non_current_kept:
        out.append("")
        for entry in non_current_kept:
            out.extend(entry.lines)
            out.append("")

    return _trim_trailing_blank(out)


def _remove_marker_lines(lines: Iterable[str]) -> list[str]:
    return [
        line
        for line in lines
        if line.strip() not in {CURRENT_BATCH_START_MARKER, CURRENT_BATCH_END_MARKER}
    ]


def _render_archive(prefix_lines: list[str], entries: list[Entry]) -> list[str]:
    out = _trim_trailing_blank(prefix_lines)
    if entries:
        out.append("")
        for entry in entries:
            out.extend(entry.lines)
            out.append("")
    return _trim_trailing_blank(out)


def _parse_active_batch_state(section_lines: list[str]) -> ActiveBatchState:
    completed: list[int] = []
    not_defined: list[int] = []
    explicit_current: list[int] = []
    explicit_next: list[int] = []

    for line in section_lines:
        completed.extend(int(m.group(1)) for m in BATCH_COMPLETE_RE.finditer(line))
        not_defined.extend(int(m.group(1)) for m in BATCH_NOT_DEFINED_RE.finditer(line))
        explicit_current.extend(
            int(m.group(1)) for m in BATCH_CURRENT_RE.finditer(line)
        )
        explicit_next.extend(int(m.group(1)) for m in BATCH_NEXT_RE.finditer(line))

    last_completed = max(completed) if completed else None
    next_undefined = max(not_defined) if not_defined else None

    current_batch = explicit_current[-1] if explicit_current else None
    if current_batch is None and explicit_next:
        candidate = explicit_next[-1]
        if next_undefined != candidate:
            current_batch = candidate

    if current_batch is None and last_completed is not None and next_undefined is None:
        # No explicit "current" signal and no "not yet defined" guard; this can
        # happen when Section 3 is terse while Section 4 already has active logs.
        current_batch = last_completed + 1

    if next_undefined is not None and current_batch == next_undefined:
        current_batch = None

    return ActiveBatchState(
        current_batch=current_batch,
        last_completed_batch=last_completed,
        next_undefined_batch=next_undefined,
    )


def _extract_entry_batch(entry: Entry) -> int | None:
    """Extract the batch number from an entry heading, if present."""
    match = ENTRY_BATCH_RE.search(entry.title)
    return int(match.group(1)) if match else None


def _collect_wp_numbers(entries: list[Entry]) -> list[int]:
    numbers: set[int] = set()
    for entry in entries:
        for raw in re.findall(r"\bWP-(\d+)\b", entry.heading):
            numbers.add(int(raw))
    return sorted(numbers)


def _date_key(date_str: str) -> int:
    return int(date_str.replace("-", ""))


@dataclasses.dataclass(frozen=True)
class SyncResult:
    """Outputs of a sync pass before write/check decisions."""

    playbook_lines: list[str]
    archive_lines: list[str]
    session_lines: list[str]
    rotated_count: int
    kept_non_current_count: int
    current_batch_entry_count: int


def _build_status_block(
    section_3_state: ActiveBatchState,
    current_entries: list[Entry],
) -> list[str]:
    if current_entries:
        wp_numbers = _collect_wp_numbers(current_entries)
        completed_wp = (
            ", ".join(f"WP-{num}" for num in wp_numbers) if wp_numbers else "none"
        )
        # Find the first gap in the WP sequence (e.g., [1, 3] -> next is 2).
        if wp_numbers:
            wp_set = set(wp_numbers)
            candidate = 1
            while candidate in wp_set:
                candidate += 1
            next_wp = f"WP-{candidate}"
        else:
            next_wp = "unknown"
        newest_heading = current_entries[0].heading.removeprefix("### ").strip()
        batch_num = section_3_state.current_batch
        if batch_num is None and section_3_state.last_completed_batch is not None:
            batch_num = section_3_state.last_completed_batch + 1
        batch_label = f"Batch {batch_num}" if batch_num is not None else "unknown"
        return [
            "- Source of truth: `PLAYBOOK.md` (Section 3 and Section 4).",
            f"- Current batch: {batch_label}.",
            f"- Current-batch entries in active log block: {len(current_entries)}.",
            f"- Completed work packages in current-batch entries: {completed_wp}.",
            f"- Next expected work package: {next_wp}.",
            f"- Newest current-batch entry: {newest_heading}.",
        ]

    # Valid between-batch state: no entries inside the current-batch markers.
    last_completed = section_3_state.last_completed_batch
    lines = [
        "- Source of truth: `PLAYBOOK.md` (Section 3 and Section 4).",
        "- Current batch: none (between batches).",
        f"- Last completed batch in PLAYBOOK Section 3: "
        f"{f'Batch {last_completed}' if last_completed is not None else 'unknown'}.",
        "- Current-batch entries in active log block: 0.",
        "- Completed work packages in current-batch entries: n/a (no active batch).",
        "- Next expected work package: n/a (next batch not defined).",
        "- Newest current-batch entry: none.",
    ]
    if section_3_state.next_undefined_batch is not None:
        lines.insert(
            3,
            "- Next batch definition status: "
            f"Batch {section_3_state.next_undefined_batch} is not yet defined.",
        )
    return lines


def _sync(keep_non_current: int) -> SyncResult:
    playbook_lines = _read_lines(PLAYBOOK_PATH)
    archive_lines = _read_lines(ARCHIVE_PATH)
    session_lines = _read_lines(SESSION_CONTEXT_PATH)

    section_3_start, section_3_end = _find_section(
        playbook_lines, SECTION_3_RE, "PLAYBOOK section 3"
    )
    section_4_start, section_4_end = _find_section(
        playbook_lines, SECTION_4_RE, "PLAYBOOK section 4"
    )

    section_4_lines = playbook_lines[section_4_start:section_4_end]
    marker_start, marker_end = _find_marker_pair(
        section_4_lines,
        CURRENT_BATCH_START_MARKER,
        CURRENT_BATCH_END_MARKER,
        "PLAYBOOK section 4",
    )

    section_4_entries, first_entry_idx = _parse_entries(section_4_lines)
    # first_entry_idx may be None when section 4 has no dated entries (valid
    # at a batch boundary after all entries have been rotated to archive).
    prefix_lines = _remove_marker_lines(
        section_4_lines[:first_entry_idx]  # [:None] == [:] when no entries
    )
    cleaned_entries: list[Entry] = []
    for entry in section_4_entries:
        cleaned_list = _trim_trailing_blank(_remove_marker_lines(entry.lines))
        cleaned_lines = tuple(cleaned_list)
        if not cleaned_lines:
            continue
        cleaned_entries.append(
            Entry(
                heading=entry.heading,
                date=entry.date,
                title=entry.title,
                lines=cleaned_lines,
                start_idx=entry.start_idx,
                fingerprint=_fingerprint(cleaned_lines),
            )
        )

    # Parse Section 3 batch state early -- needed for batch-aware filtering.
    section_3_state = _parse_active_batch_state(
        playbook_lines[section_3_start:section_3_end]
    )

    current_entries = [
        entry
        for entry in cleaned_entries
        if marker_start < entry.start_idx < marker_end
    ]
    # Empty current-batch block is valid at a batch boundary (all entries
    # rotated, new batch not yet started).

    non_current_entries = [
        entry
        for entry in cleaned_entries
        if not (marker_start < entry.start_idx < marker_end)
    ]

    # Batch-aware filtering: entries inside the current-batch markers that
    # belong to a different (completed) batch are stale and should be
    # rotated out rather than kept as current.
    if section_3_state.current_batch is not None:
        truly_current: list[Entry] = []
        stale_in_markers: list[Entry] = []
        has_tagged_current = any(
            _extract_entry_batch(e) == section_3_state.current_batch
            for e in current_entries
        )
        for entry in current_entries:
            entry_batch = _extract_entry_batch(entry)
            if entry_batch == section_3_state.current_batch:
                # Explicitly tagged for the current batch -- keep.
                truly_current.append(entry)
            elif entry_batch is not None:
                # Explicitly tagged for a different batch -- stale.
                stale_in_markers.append(entry)
            elif has_tagged_current:
                # No batch tag but tagged current entries exist -- stale.
                stale_in_markers.append(entry)
            else:
                # No batch tag and no tagged current entries -- ambiguous,
                # keep to avoid losing entries during a transition.
                truly_current.append(entry)
        current_entries = truly_current
        non_current_entries = stale_in_markers + non_current_entries

    # Separate non-current entries into two groups:
    # 1. Completed-batch entries (tagged for a batch != current) -- always rotate.
    # 2. Ambiguous/untagged entries -- subject to --keep-non-current limit.
    current_batch_num = (
        section_3_state.current_batch
        if section_3_state.current_batch is not None
        else -1
    )
    always_rotate: list[Entry] = []
    keepable: list[Entry] = []
    for entry in non_current_entries:
        entry_batch = _extract_entry_batch(entry)
        if entry_batch is not None and entry_batch != current_batch_num:
            always_rotate.append(entry)
        else:
            keepable.append(entry)
    non_current_kept = keepable[:keep_non_current]
    rotated_entries = always_rotate + keepable[keep_non_current:]

    new_section_4_lines = _render_section4(
        prefix_lines, current_entries, non_current_kept
    )
    new_playbook_lines = (
        playbook_lines[:section_4_start]
        + new_section_4_lines
        + playbook_lines[section_4_end:]
    )

    archive_entries, archive_first_entry_idx = _parse_entries(archive_lines)
    archive_prefix = (
        archive_lines[:archive_first_entry_idx]
        if archive_first_entry_idx is not None
        else archive_lines
    )

    combined = list(rotated_entries) + list(archive_entries)
    combined_annotated = list(enumerate(combined))
    combined_annotated.sort(key=lambda pair: (-_date_key(pair[1].date), pair[0]))

    deduped_entries: list[Entry] = []
    seen_fingerprints: set[str] = set()
    for _, entry in combined_annotated:
        if entry.fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(entry.fingerprint)
        deduped_entries.append(entry)

    new_archive_lines = _render_archive(archive_prefix, deduped_entries)

    status_start, status_end = _find_marker_pair(
        session_lines,
        SESSION_STATUS_START_MARKER,
        SESSION_STATUS_END_MARKER,
        "SESSION_CONTEXT",
    )
    status_block = _build_status_block(
        section_3_state=section_3_state,
        current_entries=current_entries,
    )
    new_session_lines = (
        session_lines[: status_start + 1] + status_block + session_lines[status_end:]
    )

    return SyncResult(
        playbook_lines=new_playbook_lines,
        archive_lines=new_archive_lines,
        session_lines=new_session_lines,
        rotated_count=len(rotated_entries),
        kept_non_current_count=len(non_current_kept),
        current_batch_entry_count=len(current_entries),
    )


def _cross_validate(playbook_lines: list[str], session_lines: list[str]) -> list[str]:
    """Cross-check content across files; return list of warning strings."""
    warnings: list[str] = []

    # 1. Test count consistency: look for "**N passing**" in SESSION_CONTEXT
    #    and PLAYBOOK and warn if they disagree.
    test_count_re = re.compile(r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*")
    session_counts: set[int] = set()
    playbook_counts: set[int] = set()
    for line in session_lines:
        for m in test_count_re.finditer(line):
            session_counts.add(int(m.group(1)))
    for line in playbook_lines:
        for m in test_count_re.finditer(line):
            playbook_counts.add(int(m.group(1)))
    if session_counts and playbook_counts and session_counts != playbook_counts:
        warnings.append(
            f"Test count mismatch: SESSION_CONTEXT has {session_counts}, "
            f"PLAYBOOK has {playbook_counts}."
        )

    # 2. Stale header detection: warn if PLAYBOOK header still mentions
    #    completed milestones (e.g., "refactor monolithic app.py").
    stale_phrases = [
        "refactor monolithic",
        "Post-Batch 8",
    ]
    for line in playbook_lines[:5]:
        for phrase in stale_phrases:
            if phrase.lower() in line.lower():
                warnings.append(
                    f"Stale header detected in PLAYBOOK: '{phrase}' "
                    f"found in: {line.strip()}"
                )
    for line in session_lines[:5]:
        for phrase in stale_phrases:
            if phrase.lower() in line.lower():
                warnings.append(
                    f"Stale header detected in SESSION_CONTEXT: '{phrase}' "
                    f"found in: {line.strip()}"
                )

    return warnings


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

    try:
        result = _sync(keep_non_current=args.keep_non_current)
    except SyncError as exc:
        print(f"doc_state_sync failed: {exc}", file=sys.stderr)
        return 2

    current_playbook = _read_lines(PLAYBOOK_PATH)
    current_archive = _read_lines(ARCHIVE_PATH)
    current_session = _read_lines(SESSION_CONTEXT_PATH)

    # Cross-validation warnings (non-blocking).
    xv_warnings = _cross_validate(result.playbook_lines, result.session_lines)
    if xv_warnings:
        for w in xv_warnings:
            print(f"WARNING: {w}", file=sys.stderr)

    changed: list[Path] = []
    if current_playbook != result.playbook_lines:
        changed.append(PLAYBOOK_PATH)
    if current_archive != result.archive_lines:
        changed.append(ARCHIVE_PATH)
    if current_session != result.session_lines:
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
        _write_lines(SESSION_CONTEXT_PATH, result.session_lines)
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


if __name__ == "__main__":
    raise SystemExit(main())
