"""Core sync logic for docsync.

Every function in this module is pure: no file is read or written here.
All file I/O is handled exclusively by docsync.cli, and semantic
validation by docsync.integrity.
"""

from __future__ import annotations

import re
from pathlib import Path

from docsync.models import (
    ActiveBatchState,
    Entry,
    SyncError,
    SyncResult,
    TestCountAuthority,
)
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
        # Read the pre-rotation document. The authoritative count is a fact
        # about the repository, so it must not change with how many entries
        # the retention window happens to keep: the documented close-out
        # command purges that window entirely, which would otherwise revive
        # a superseded count and then fail its own consistency check.
        # The batch logs are part of that fact too -- tagged entries rotate
        # there rather than into the monolith -- so they travel with it.
        count_authority = latest_test_count_authority(
            playbook_lines, new_archive_lines, effective_batch_log_lines
        )
        status_block = _build_status_block(
            section_3_state=section_3_state,
            current_entries=current_entries,
            latest_test_count=count_authority.count,
            count_is_ambiguous=count_authority.ambiguous,
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


class _AmbiguousCount:
    """Sentinel type: the newest entry recording counts quotes several of them.

    Kept distinct from ``None`` (no entry anywhere records a count) because the
    two demand opposite handling. Ambiguity must suppress every older candidate
    -- republishing a superseded number as the current one is worse than
    reporting the count as unknown -- whereas absence may fall through to the
    legacy sole-bold-count pass.
    """

    __slots__ = ()


_AMBIGUOUS_COUNT = _AmbiguousCount()

# Source precedence, applied only to break a same-date tie in the ordering
# below. A side-task entry is written after the batch entry it follows, and a
# side-task entry still live in PLAYBOOK is newer than one that retention has
# already moved into the archive -- so the monolith outranks the current batch
# on a shared date. A per-batch log is different: its entries always belong to
# a completed batch, so even on a shared date they are older work than the
# active batch's entries and sit below them.
_PRECEDENCE_LIVE_SIDE = 3
_PRECEDENCE_ROTATED = 2
_PRECEDENCE_CURRENT_BATCH = 1
_PRECEDENCE_BATCH_LOG = 0


def _monotonic_dates(source: list[Entry]) -> list[int]:
    """Clamp a source's heading dates so they cannot contradict its file order.

    Each source list reaches the ordering already newest-first by its own
    documented convention -- current-batch entries are appended and then
    reversed, side-task entries are written directly below the end marker -- so
    position, not the heading date, is the authority on recency *within* a
    source. Dates are still needed to interleave the sources against one
    another, so each is clamped to the running minimum. A back-dated or
    out-of-order heading can then never lift an entry above one that precedes it
    in its own source.
    """
    clamped: list[int] = []
    running: int | None = None
    for entry in source:
        key = _date_key(entry.date)
        running = key if running is None else min(running, key)
        clamped.append(running)
    return clamped


def _newest_count(
    candidates: list[tuple[Entry, int, int]], *, allow_legacy_fallback: bool
) -> int | _AmbiguousCount | None:
    """Return the first definitive full-suite count in a newest-first ordering.

    ``candidates`` is the single ordering built by
    ``latest_test_count_authority``; this function only walks it, so
    precedence is decided in exactly one place.

    Returns the count, ``None`` when no entry records one, or
    ``_AMBIGUOUS_COUNT`` when the newest entry quoting counts quotes several
    without an explicit ``pytest -q`` result. The third state exists because
    treating ambiguity as absence lets an older entry supply the answer.
    """
    for entry, _precedence, _date_ordering_key in candidates:
        entry_text = "\n".join(entry.lines)
        explicit_matches = re.findall(
            r"`?pytest(?:\.exe)?\s+-q`?\s*(?:--)?\s*"
            r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*",
            entry_text,
            flags=re.IGNORECASE,
        )
        if explicit_matches:
            return int(explicit_matches[-1])
        fallback_matches = [
            int(match.group(1)) for match in TEST_COUNT_RE.finditer(entry_text)
        ]
        if not allow_legacy_fallback:
            if len(fallback_matches) > 1:
                return _AMBIGUOUS_COUNT
            continue
        if len(fallback_matches) == 1:
            return fallback_matches[0]
    return None


def _latest_test_count_from_entries(
    playbook_lines: list[str], archive_lines: list[str] | None = None
) -> int | None:
    """Return the newest full-suite count, discarding why it may be absent.

    Callers that must distinguish "no count recorded" from "the newest
    entry is ambiguous" need ``latest_test_count_authority`` instead. No
    production caller remains; this wrapper is exercised only by its own
    unit tests, and its removal is tracked in FINDINGS as F-DOCSYNC-7.
    """
    return latest_test_count_authority(playbook_lines, archive_lines).count


def latest_test_count_authority(
    playbook_lines: list[str],
    archive_lines: list[str] | None = None,
    batch_log_lines: dict[int, list[str]] | None = None,
) -> TestCountAuthority:
    """Return the newest full-suite count recorded anywhere in the log.

    Authority is decided by one total ordering over every candidate entry --
    date descending, then source precedence descending -- which is walked once.
    The sources are the live side-task entries after the end marker
    (newest-first as written), the rotated entries in ``archive_lines``, the
    rotated entries in the per-batch logs (``batch_log_lines``), and the
    current-batch entries between the markers (append-ordered, so reversed
    here). Precedence breaks same-date ties only, in this order: live side task,
    then rotated monolith, then current batch, then per-batch logs. The
    per-batch logs rank below the current batch because their entries always
    belong to a completed batch -- even on a shared date they are older work
    than the active batch's entries. The monolith ranks above the current
    batch because a rotated side-task entry genuinely can be newer than the
    batch entry it follows.

    Within that ordering, an explicit ``pytest -q`` result wins; an entry
    quoting several bold counts without one is ambiguous and makes the count
    unknown rather than deferring to an older entry; a sole bold count is
    accepted only on a second pass, when no entry anywhere carries an explicit
    result.

    The test count is a fact about the repository, so it must not change when
    the retention window moves an entry out of PLAYBOOK: the documented
    close-out command purges that window entirely, which would otherwise revive
    a superseded count. Tagged entries rotate into their per-batch log rather
    than the monolith, so those logs are part of the same fact and are scanned
    here too.
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
        return TestCountAuthority(count=None, ambiguous=False)

    current_entries = [
        entry for entry in entries if marker_start < entry.start_idx < marker_end
    ]
    side_entries = [entry for entry in entries if entry.start_idx > marker_end]

    current_candidates = list(reversed(current_entries))
    rotated_candidates: list[Entry] = []
    batch_log_candidates: list[Entry] = []
    if archive_lines is not None:
        try:
            archive_entries, _ = _parse_entries(archive_lines)
        except SyncError:
            archive_entries = []
        rotated_candidates = sorted(
            archive_entries, key=lambda entry: _date_key(entry.date), reverse=True
        )
    if batch_log_lines:
        for log_lines in batch_log_lines.values():
            try:
                log_entries, _ = _parse_entries(log_lines)
            except SyncError:
                continue
            batch_log_candidates.extend(log_entries)
        # Per-batch logs are newest-first by their own convention; sort keeps
        # that order within a shared date.
        batch_log_candidates.sort(key=lambda entry: _date_key(entry.date), reverse=True)

    # Build one total ordering over every candidate from every source, newest
    # first: clamped date descending, then source precedence descending.
    # Scanning three sources separately and reconciling their winners afterwards
    # is what produced the tie-break and fallback defects this replaces --
    # precedence now lives in the sort key alone.
    #
    # `sort` is stable and `reverse=True` does not reorder equal keys, so
    # entries sharing a clamped date and a source keep the newest-first order
    # their source list already has.
    # Sources are concatenated in ascending precedence -- the reverse of the
    # order they must come out in -- so that a correct result can only come
    # from the sort key. Were they concatenated newest-source-first, sort
    # stability alone would produce the right answer and the precedence
    # constants would be unobservable dead weight.
    ordered_candidates = [
        (entry, precedence, date_key)
        for source, precedence in (
            (current_candidates, _PRECEDENCE_CURRENT_BATCH),
            (rotated_candidates, _PRECEDENCE_ROTATED),
            (batch_log_candidates, _PRECEDENCE_BATCH_LOG),
            (side_entries, _PRECEDENCE_LIVE_SIDE),
        )
        for entry, date_key in zip(source, _monotonic_dates(source))
    ]
    ordered_candidates.sort(key=lambda item: (item[2], item[1]), reverse=True)

    count = _newest_count(ordered_candidates, allow_legacy_fallback=False)
    if isinstance(count, _AmbiguousCount):
        return TestCountAuthority(count=None, ambiguous=True)
    if count is None:
        # The legacy pass accepts a sole bold count from an entry that predates
        # the `pytest -q` convention. It walks the same ordering, so a legacy
        # entry still resolves after retention moves it into the archive.
        legacy = _newest_count(ordered_candidates, allow_legacy_fallback=True)
        legacy = legacy if isinstance(legacy, int) else None
        return TestCountAuthority(count=legacy, ambiguous=False)
    return TestCountAuthority(count=count, ambiguous=False)
