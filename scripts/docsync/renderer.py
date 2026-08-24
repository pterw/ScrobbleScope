"""Markdown rendering functions for docsync."""

from __future__ import annotations

from typing import Iterable

from docsync.models import ActiveBatchState, Entry
from docsync.parser import (
    CURRENT_BATCH_END_MARKER,
    CURRENT_BATCH_START_MARKER,
    _collect_wp_numbers,
)

SIDE_ARCHIVE_PREFIX = (
    "# PLAYBOOK Execution Log Archive",
    "",
    "Purpose:",
    "- Store dated execution-log entries rotated out of `PLAYBOOK.md` Section 4.",
    "- Keep entries in reverse-chronological order (newest first).",
    "",
    "Read helpers:",
    "- `Get-Content docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`",
    '- `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`',
    '- `rg -n "<keyword>" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`',
)


def _trim_trailing_blank(lines: list[str]) -> list[str]:
    out = list(lines)
    while out and out[-1].strip() == "":
        out.pop()
    return out


def _remove_marker_lines(lines: Iterable[str]) -> list[str]:
    return [
        line
        for line in lines
        if line.strip() not in {CURRENT_BATCH_START_MARKER, CURRENT_BATCH_END_MARKER}
    ]


def _render_section4(
    prefix_lines: list[str],
    current_entries: list[Entry],
    non_current_kept: list[Entry],
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


def _render_archive(prefix_lines: list[str], entries: list[Entry]) -> list[str]:
    out = _trim_trailing_blank(prefix_lines)
    if entries:
        out.append("")
        for entry in entries:
            out.extend(entry.lines)
            out.append("")
    return _trim_trailing_blank(out)


def _render_side_archive(entries: list[Entry]) -> list[str]:
    """Render the side-task archive from its canonical, renderer-owned prefix."""
    return _render_archive(list(SIDE_ARCHIVE_PREFIX), entries)


def _next_wp_number(
    current_entries: list[Entry],
    planned_wp_numbers: Iterable[int] | None = None,
) -> int | None:
    """Return the next positive WP number for the managed status block.

    When an active definition supplies its planned numbers, that finite set is
    authoritative: absorbed, dropped, or merged work packages are not viable
    candidates, and completing the set returns ``None``. Without a usable plan,
    preserve the historical renderer rule by returning the lowest positive
    integer absent from the current-entry headings. Entries with no WP tags and
    no plan provide no basis for a numbered answer.
    """
    completed = set(_collect_wp_numbers(current_entries))
    declared_plan = tuple(planned_wp_numbers or ())
    planned = {number for number in declared_plan if number > 0}
    if declared_plan:
        return next(
            (number for number in sorted(planned) if number not in completed),
            None,
        )
    if not completed:
        return None
    candidate = 1
    while candidate in completed:
        candidate += 1
    return candidate


def _build_status_block(
    section_3_state: ActiveBatchState,
    current_entries: list[Entry],
    latest_test_count: int | None = None,
    count_is_ambiguous: bool = False,
    planned_wp_numbers: Iterable[int] | None = None,
) -> list[str]:
    if current_entries:
        wp_numbers = _collect_wp_numbers(current_entries)
        completed_wp = (
            ", ".join(f"WP-{num}" for num in wp_numbers) if wp_numbers else "none"
        )
        planned = tuple(planned_wp_numbers or ())
        next_wp_number = _next_wp_number(current_entries, planned)
        if next_wp_number is not None:
            next_wp = f"WP-{next_wp_number}"
        elif planned:
            next_wp = "none (all planned work packages complete)"
        else:
            next_wp = "unknown"
        newest_heading = current_entries[-1].heading.removeprefix("### ").strip()
        batch_num = section_3_state.current_batch
        if batch_num is None and section_3_state.last_completed_batch is not None:
            batch_num = section_3_state.last_completed_batch + 1
        batch_label = f"Batch {batch_num}" if batch_num is not None else "unknown"
        # Two different absences render differently. Reporting "no bold count"
        # when the newest entry in fact quotes several sends the reader looking
        # for a missing number instead of the ambiguous entry that caused it.
        if latest_test_count is not None:
            count_line = (
                f"- Latest validated test count: **{latest_test_count} passed**."
            )
        elif count_is_ambiguous:
            count_line = (
                "- Latest validated test count: unknown (newest entry quotes "
                "several counts without a `pytest -q` result)."
            )
        else:
            count_line = (
                "- Latest validated test count: unknown (no bold count in log entries)."
            )
        return [
            "- Source of truth: `PLAYBOOK.md` (Section 3 and Section 4).",
            f"- Current batch: {batch_label}.",
            f"- Current-batch entries in active log block: {len(current_entries)}.",
            f"- Completed work packages in current-batch entries: {completed_wp}.",
            f"- Next expected work package: {next_wp}.",
            count_line,
            f"- Newest current-batch entry: {newest_heading}.",
        ]

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
