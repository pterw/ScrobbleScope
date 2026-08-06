"""Core sync logic for docsync.

Every function in this module is pure: no file is read or written here.
All file I/O is handled exclusively by docsync.cli, and semantic
validation by docsync.integrity.
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
    TEST_COUNT_RE,
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
    _render_side_archive,
    _trim_trailing_blank,
)


def _dedup_sorted(entries: list[Entry]) -> list[Entry]:
    """Sort entries newest-first and deduplicate by fingerprint."""
    annotated = list(enumerate(entries))
    annotated.sort(key=lambda pair: (-_date_key(pair[1].date), pair[0]))
    seen: set[str] = set()
    out: list[Entry] = []
    for _, entry in annotated:
        if entry.fingerprint not in seen:
            seen.add(entry.fingerprint)
            out.append(entry)
    return out


def _merge_entries_into_log(
    existing_lines: list[str],
    new_entries: list[Entry],
    batch_num: int,
) -> list[str]:
    """Merge new_entries into an existing per-batch log, deduplicating by fingerprint.

    If existing_lines is empty a minimal header is generated.  The returned
    content is sorted newest-first and deduplicated.
    """
    if existing_lines:
        existing_entries, first_idx = _parse_entries(existing_lines)
        prefix: list[str] = (
            existing_lines[:first_idx] if first_idx is not None else existing_lines
        )
    else:
        prefix = [
            f"# Batch {batch_num} Execution Log",
            "",
            f"Archived entries for Batch {batch_num} work packages.",
        ]
        existing_entries = []

    deduped = _dedup_sorted(list(new_entries) + list(existing_entries))

    return _render_archive(prefix, deduped)


def _split_archive(
    monolith_lines: list[str],
) -> tuple[list[str], dict[int, list[Entry]]]:
    """Partition all entries in monolith_lines by batch tag.

    Returns:
        remaining_lines: rendered lines for the monolith retaining only
            untagged / side-task entries.
        batch_groups: mapping from batch number to the Entry objects that
            carry that batch tag.  Callers pass these to
            _merge_entries_into_log to produce per-batch log content.
    """
    all_entries, _ = _parse_entries(monolith_lines)

    untagged: list[Entry] = []
    batch_groups: dict[int, list[Entry]] = {}
    for entry in all_entries:
        batch_num = _extract_entry_batch(entry)
        if batch_num is None:
            untagged.append(entry)
        else:
            batch_groups.setdefault(batch_num, []).append(entry)

    remaining_lines = _render_side_archive(untagged)
    return remaining_lines, batch_groups


def _sync(
    playbook_lines: list[str],
    archive_lines: list[str],
    session_lines: list[str] | None,
    keep_non_current: int,
    batch_log_lines: dict[int, list[str]] | None = None,
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

    # Sentinel -1: no real batch is negative.  When current_batch is None,
    # -1 ensures every tagged entry satisfies entry_batch != current_batch_num
    # and routes to always_rotate.
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

    archive_entries, _ = _parse_entries(archive_lines)

    # Route rotated entries: tagged → per-batch log; untagged → monolith.
    tagged_rotated: dict[int, list[Entry]] = {}
    untagged_rotated: list[Entry] = []
    for entry in rotated_entries:
        entry_batch = _extract_entry_batch(entry)
        if entry_batch is not None:
            tagged_rotated.setdefault(entry_batch, []).append(entry)
        else:
            untagged_rotated.append(entry)

    # Monolith archive receives only untagged rotated entries.
    deduped_entries = _dedup_sorted(list(untagged_rotated) + list(archive_entries))

    new_archive_lines = _render_side_archive(deduped_entries)

    # Merge tagged rotated entries into per-batch log files.
    effective_batch_log_lines: dict[int, list[str]] = batch_log_lines or {}
    batch_log_updates: dict[int, list[str]] = {}
    for batch_num, entries in tagged_rotated.items():
        existing = effective_batch_log_lines.get(batch_num, [])
        batch_log_updates[batch_num] = _merge_entries_into_log(
            existing, entries, batch_num
        )

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
            # Read the pre-rotation document. The authoritative count is a fact
            # about the repository, so it must not change with how many entries
            # the retention window happens to keep: the documented close-out
            # command purges the window entirely, which would otherwise revive
            # a superseded count and then fail its own consistency check.
            latest_test_count=_latest_test_count_from_entries(
                playbook_lines, new_archive_lines
            ),
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
        batch_log_updates=batch_log_updates,
    )


def _latest_test_count_from_entries(
    playbook_lines: list[str], archive_lines: list[str] | None = None
) -> int | None:
    """Return the newest full-suite count recorded anywhere in the log.

    Current-batch entries are append-ordered, while side-task entries after the
    end marker are newest-first. A same-date side task is newer than the batch
    entry it follows. Explicit ``pytest -q`` results win over focused counts
    across all live entries; a sole bold count remains supported only when no
    explicit full-suite result exists.

    Rotated entries in ``archive_lines`` are considered too. The test count is a
    fact about the repository, so it must not change when the retention window
    moves an entry out of PLAYBOOK: the documented close-out command purges that
    window entirely, which would otherwise revive a superseded count.
    """
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
        entries, _ = _parse_entries(section_4_lines)
    except SyncError:
        return None

    current_entries = [
        entry for entry in entries if marker_start < entry.start_idx < marker_end
    ]
    side_entries = [entry for entry in entries if entry.start_idx > marker_end]

    def newest_count(
        candidates: list[Entry], *, allow_legacy_fallback: bool
    ) -> tuple[str, int] | None:
        for entry in candidates:
            entry_text = "\n".join(entry.lines)
            explicit_matches = re.findall(
                r"`?pytest(?:\.exe)?\s+-q`?\s*(?:--)?\s*"
                r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*",
                entry_text,
                flags=re.IGNORECASE,
            )
            if explicit_matches:
                return entry.date, int(explicit_matches[-1])
            fallback_matches = [
                int(match.group(1)) for match in TEST_COUNT_RE.finditer(entry_text)
            ]
            if not allow_legacy_fallback:
                # An entry quoting several counts without a `pytest -q` result
                # is ambiguous. Skipping to an older entry would silently
                # republish a superseded number as current, so stop here and
                # let the count read as unknown instead.
                if len(fallback_matches) > 1:
                    return None
                continue
            if len(fallback_matches) == 1:
                return entry.date, fallback_matches[0]
        return None

    current_candidates = list(reversed(current_entries))
    rotated_candidates: list[Entry] = []
    if archive_lines is not None:
        try:
            archive_entries, _ = _parse_entries(archive_lines)
        except SyncError:
            archive_entries = []
        rotated_candidates = sorted(
            archive_entries, key=lambda entry: entry.date, reverse=True
        )

    side_count = newest_count(side_entries, allow_legacy_fallback=False)
    current_count = newest_count(current_candidates, allow_legacy_fallback=False)
    rotated_count = newest_count(rotated_candidates, allow_legacy_fallback=False)
    if side_count is None and current_count is None and rotated_count is None:
        side_count = newest_count(side_entries, allow_legacy_fallback=True)
        current_count = newest_count(
            current_candidates,
            allow_legacy_fallback=True,
        )
    # A same-date non-current entry outranks the batch entry it follows, so
    # rank by date first and let the current-batch entry lose ties.
    ranked = [
        (found[0], rank, found[1])
        for found, rank in (
            (side_count, 1),
            (rotated_count, 1),
            (current_count, 0),
        )
        if found is not None
    ]
    if not ranked:
        return None
    return max(ranked)[2]
