"""Core sync logic and cross-validation for docsync.

All functions in this module are pure (no file I/O). File reading/writing
is handled exclusively by docsync.cli.
"""

from __future__ import annotations

import re
from pathlib import Path

from docsync.models import ActiveBatchState, Entry, SyncError, SyncResult
from docsync.parser import (
    CURRENT_BATCH_END_MARKER,
    CURRENT_BATCH_START_MARKER,
    SECTION_3_RE,
    SECTION_4_RE,
    SESSION_STATUS_END_MARKER,
    SESSION_STATUS_START_MARKER,
    _date_key,
    _extract_entry_batch,
    _find_marker_pair,
    _find_section,
    _fingerprint,
    _parse_active_batch_state,
    _parse_entries,
)
from docsync.renderer import (
    _build_status_block,
    _remove_marker_lines,
    _render_archive,
    _render_section4,
    _trim_trailing_blank,
)


def _sync(
    playbook_lines: list[str],
    archive_lines: list[str],
    session_lines: list[str] | None,
    keep_non_current: int,
) -> SyncResult:
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

    section_3_state = _parse_active_batch_state(
        playbook_lines[section_3_start:section_3_end]
    )

    current_entries = [
        entry
        for entry in cleaned_entries
        if marker_start < entry.start_idx < marker_end
    ]

    non_current_entries = [
        entry
        for entry in cleaned_entries
        if not (marker_start < entry.start_idx < marker_end)
    ]

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
                truly_current.append(entry)
            elif entry_batch is not None:
                stale_in_markers.append(entry)
            elif has_tagged_current:
                stale_in_markers.append(entry)
            else:
                truly_current.append(entry)
        current_entries = truly_current
        non_current_entries = stale_in_markers + non_current_entries

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

    new_session_lines: list[str] | None = None
    if session_lines is not None:
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
            session_lines[: status_start + 1]
            + status_block
            + session_lines[status_end:]
        )

    return SyncResult(
        playbook_lines=new_playbook_lines,
        archive_lines=new_archive_lines,
        session_lines=new_session_lines,
        rotated_count=len(rotated_entries),
        kept_non_current_count=len(non_current_kept),
        current_batch_entry_count=len(current_entries),
    )


def _latest_test_count_from_entries(playbook_lines: list[str]) -> int | None:
    """Return the most recent bold passing-test count from Section 4 log entries.

    Agents record test counts as ``**N passed**`` (or similar) in Validation
    fields of Section 4 log entries.  Section 3 rarely contains such counts.
    Scanning entries newest-first ensures we get the live state, not history.
    """
    test_count_re = re.compile(r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*")
    try:
        s4_start, s4_end = _find_section(
            playbook_lines, SECTION_4_RE, "PLAYBOOK section 4"
        )
        section_4_lines = playbook_lines[s4_start:s4_end]
        marker_start, marker_end = _find_marker_pair(
            section_4_lines,
            CURRENT_BATCH_START_MARKER,
            CURRENT_BATCH_END_MARKER,
            "PLAYBOOK section 4",
        )
        inside = section_4_lines[marker_start + 1 : marker_end]
        entries, _ = _parse_entries(inside)
    except SyncError:
        return None
    # Entries are newest-first in Section 4; scan each in order.
    for entry in entries:
        for line in entry.lines:
            m = test_count_re.search(line)
            if m:
                return int(m.group(1))
    return None


def _cross_validate(
    playbook_lines: list[str], session_lines: list[str] | None
) -> list[str]:
    """Cross-check content across files; return list of warning strings."""
    warnings: list[str] = []

    test_count_re = re.compile(r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*")
    # Extract test count from the most recent Section 4 log entry so that the
    # check fires on real agent output (Section 3 rarely contains these counts).
    playbook_count = _latest_test_count_from_entries(playbook_lines)
    session_counts: set[int] = set()
    if session_lines is not None:
        for line in session_lines:
            for m in test_count_re.finditer(line):
                session_counts.add(int(m.group(1)))
    if (
        playbook_count is not None
        and session_counts
        and playbook_count not in session_counts
    ):
        warnings.append(
            f"Test count mismatch: SESSION_CONTEXT has {session_counts}, "
            f"most recent PLAYBOOK log entry has {playbook_count}."
        )

    archive_link_re = re.compile(r"`(docs/history/[^`]+\.md)`")
    for line in playbook_lines:
        for m in archive_link_re.finditer(line):
            linked_path = Path(m.group(1))
            if not linked_path.exists():
                warnings.append(
                    f"Broken archive link in PLAYBOOK: {linked_path} does not exist."
                )

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
    if session_lines is not None:
        for line in session_lines[:5]:
            for phrase in stale_phrases:
                if phrase.lower() in line.lower():
                    warnings.append(
                        f"Stale header detected in SESSION_CONTEXT: '{phrase}' "
                        f"found in: {line.strip()}"
                    )

    return warnings
