"""Markdown rendering functions for docsync."""

from __future__ import annotations

from typing import Iterable

from docsync.models import ActiveBatchState, Entry
from docsync.parser import (
    CURRENT_BATCH_END_MARKER,
    CURRENT_BATCH_START_MARKER,
    TEST_COUNT_RE,
    _collect_wp_numbers,
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


def _build_status_block(
    section_3_state: ActiveBatchState,
    current_entries: list[Entry],
) -> list[str]:
    if current_entries:
        wp_numbers = _collect_wp_numbers(current_entries)
        completed_wp = (
            ", ".join(f"WP-{num}" for num in wp_numbers) if wp_numbers else "none"
        )
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
        # Extract test count from validation line of most recent entry.
        latest_count: int | None = None
        for entry in current_entries:
            for line in entry.lines:
                m = TEST_COUNT_RE.search(line)
                if m:
                    latest_count = int(m.group(1))
                    break
            if latest_count is not None:
                break
        count_line = (
            f"- Latest validated test count: **{latest_count} passed**."
            if latest_count is not None
            else "- Latest validated test count: unknown (no bold count in log entries)."
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
