"""Tests for docsync.renderer: trim/remove helpers, section rendering, status block."""

from __future__ import annotations

import pytest
from docsync.models import ActiveBatchState, Entry
from docsync.parser import CURRENT_BATCH_END_MARKER, CURRENT_BATCH_START_MARKER
from docsync.renderer import (
    _build_status_block,
    _remove_marker_lines,
    _render_archive,
    _render_section4,
    _trim_trailing_blank,
)

# ---------------------------------------------------------------------------
# _trim_trailing_blank -- edge cases
# ---------------------------------------------------------------------------


class TestTrimTrailingBlank:
    def test_empty_list(self):
        assert _trim_trailing_blank([]) == []

    def test_all_blank_lines(self):
        assert _trim_trailing_blank(["", "  ", "   "]) == []

    def test_preserves_internal_blanks(self):
        result = _trim_trailing_blank(["a", "", "b", ""])
        assert result == ["a", "", "b"]


# ---------------------------------------------------------------------------
# _remove_marker_lines
# ---------------------------------------------------------------------------


class TestRemoveMarkerLines:
    def test_removes_both_markers(self):
        lines = [
            "before",
            CURRENT_BATCH_START_MARKER,
            "content",
            CURRENT_BATCH_END_MARKER,
            "after",
        ]
        result = _remove_marker_lines(lines)
        assert CURRENT_BATCH_START_MARKER not in result
        assert CURRENT_BATCH_END_MARKER not in result
        assert result == ["before", "content", "after"]

    def test_no_markers_unchanged(self):
        lines = ["a", "b", "c"]
        assert _remove_marker_lines(lines) == lines


# ---------------------------------------------------------------------------
# _build_status_block -- boundary conditions
# ---------------------------------------------------------------------------


class TestBuildStatusBlock:
    def test_no_entries_between_batches(self):
        state = ActiveBatchState(
            current_batch=None,
            last_completed_batch=10,
            next_undefined_batch=None,
        )
        block = _build_status_block(state, [])
        text = "\n".join(block)
        assert "between batches" in text
        assert "Batch 10" in text
        assert "entries in active log block: 0" in text

    def test_no_entries_with_undefined_next(self):
        state = ActiveBatchState(
            current_batch=None,
            last_completed_batch=10,
            next_undefined_batch=11,
        )
        block = _build_status_block(state, [])
        text = "\n".join(block)
        assert "Batch 11 is not yet defined" in text

    def test_no_entries_all_none(self):
        state = ActiveBatchState(
            current_batch=None,
            last_completed_batch=None,
            next_undefined_batch=None,
        )
        block = _build_status_block(state, [])
        text = "\n".join(block)
        assert "unknown" in text

    def test_entries_with_wp_gap(self):
        """WP-1 and WP-3 present -- next expected should be WP-2."""
        e1 = Entry(
            heading="### 2026-02-20 - Work (Batch 11 WP-1)",
            date="2026-02-20",
            title="Work (Batch 11 WP-1)",
            lines=("### 2026-02-20 - Work (Batch 11 WP-1)", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        e2 = Entry(
            heading="### 2026-02-21 - Work (Batch 11 WP-3)",
            date="2026-02-21",
            title="Work (Batch 11 WP-3)",
            lines=("### 2026-02-21 - Work (Batch 11 WP-3)", "Content"),
            start_idx=0,
            fingerprint="b",
        )
        state = ActiveBatchState(
            current_batch=11, last_completed_batch=10, next_undefined_batch=None
        )
        block = _build_status_block(state, [e1, e2])
        text = "\n".join(block)
        assert "WP-2" in text
        assert "Batch 11" in text

    def test_entries_without_wp_tags(self):
        """Entries with no WP- tags -- completed should say 'none'."""
        entry = Entry(
            heading="### 2026-02-20 - Side task fix",
            date="2026-02-20",
            title="Side task fix",
            lines=("### 2026-02-20 - Side task fix", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        state = ActiveBatchState(
            current_batch=11, last_completed_batch=10, next_undefined_batch=None
        )
        block = _build_status_block(state, [entry])
        text = "\n".join(block)
        assert "none" in text.lower() or "unknown" in text.lower()

    def test_current_batch_none_infers_from_completed(self):
        """When current_batch is None but last_completed_batch exists,
        the label should still resolve via fallback."""
        entry = Entry(
            heading="### 2026-02-20 - Work (Batch 11 WP-1)",
            date="2026-02-20",
            title="Work (Batch 11 WP-1)",
            lines=("### 2026-02-20 - Work (Batch 11 WP-1)", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        state = ActiveBatchState(
            current_batch=None, last_completed_batch=10, next_undefined_batch=None
        )
        block = _build_status_block(state, [entry])
        text = "\n".join(block)
        # Should infer Batch 11 from last_completed_batch + 1.
        assert "Batch 11" in text


# ---------------------------------------------------------------------------
# _render_section4 -- edge and empty cases
# ---------------------------------------------------------------------------


class TestRenderSection4:
    def test_empty_current_and_non_current(self):
        prefix = ["## 4. Execution log", "", "Preamble text."]
        result = _render_section4(prefix, [], [])
        text = "\n".join(result)
        assert CURRENT_BATCH_START_MARKER in text
        assert CURRENT_BATCH_END_MARKER in text
        # No entries between markers.
        start_idx = result.index(CURRENT_BATCH_START_MARKER)
        end_idx = result.index(CURRENT_BATCH_END_MARKER)
        between = [line for line in result[start_idx + 1 : end_idx] if line.strip()]
        assert between == []

    def test_non_current_entries_after_end_marker(self):
        prefix = ["## 4. Execution log"]
        entry = Entry(
            heading="### 2026-01-01 - Old entry",
            date="2026-01-01",
            title="Old entry",
            lines=("### 2026-01-01 - Old entry", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        result = _render_section4(prefix, [], [entry])
        end_marker_idx = result.index(CURRENT_BATCH_END_MARKER)
        # The old entry should appear after the end marker.
        assert any("Old entry" in line for line in result[end_marker_idx + 1 :])


# ---------------------------------------------------------------------------
# _render_archive -- edge cases
# ---------------------------------------------------------------------------


class TestRenderArchive:
    def test_empty_entries(self):
        prefix = ["# Archive", "", "Prefix text."]
        result = _render_archive(prefix, [])
        assert result == ["# Archive", "", "Prefix text."]

    def test_entries_appended_after_prefix(self):
        prefix = ["# Archive"]
        entry = Entry(
            heading="### 2026-01-01 - Entry",
            date="2026-01-01",
            title="Entry",
            lines=("### 2026-01-01 - Entry", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        result = _render_archive(prefix, [entry])
        assert any("Entry" in line for line in result)
