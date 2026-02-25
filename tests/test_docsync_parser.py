"""Tests for docsync.parser: section finding, marker pairs, entry/batch parsing,
and regex constant behaviour."""

from __future__ import annotations

import pytest
from docsync.models import Entry, SyncError
from docsync.parser import (
    BATCH_COMPLETE_RE,
    BATCH_CURRENT_RE,
    BATCH_NOT_DEFINED_RE,
    CURRENT_BATCH_END_MARKER,
    CURRENT_BATCH_START_MARKER,
    ENTRY_HEADING_RE,
    SECTION_3_RE,
    SECTION_4_RE,
    _extract_entry_batch,
    _find_marker_pair,
    _find_section,
    _fingerprint,
    _parse_active_batch_state,
    _parse_entries,
)

# ---------------------------------------------------------------------------
# _find_section -- heading not found
# ---------------------------------------------------------------------------


class TestFindSection:
    def test_missing_heading_raises_sync_error(self):
        lines = ["# Title", "", "Some text"]
        with pytest.raises(SyncError, match="Could not find section heading"):
            _find_section(lines, SECTION_3_RE, "test section")

    def test_section_at_end_of_file(self):
        lines = ["# Title", "", "## 3. Active batch", "", "Content here"]
        start, end = _find_section(lines, SECTION_3_RE, "test section")
        assert start == 2
        assert end == len(lines)  # extends to end when no next ##

    def test_section_bounded_by_next_heading(self):
        lines = [
            "## 3. Active batch",
            "Content",
            "## 4. Execution log",
            "More content",
        ]
        start, end = _find_section(lines, SECTION_3_RE, "test section")
        assert start == 0
        assert end == 2  # stops at ## 4


# ---------------------------------------------------------------------------
# _find_marker_pair -- missing or inverted markers
# ---------------------------------------------------------------------------


class TestFindMarkerPair:
    def test_missing_start_marker(self):
        lines = ["some text", CURRENT_BATCH_END_MARKER]
        with pytest.raises(SyncError, match="must contain start marker"):
            _find_marker_pair(
                lines,
                CURRENT_BATCH_START_MARKER,
                CURRENT_BATCH_END_MARKER,
                "test",
            )

    def test_missing_end_marker(self):
        lines = [CURRENT_BATCH_START_MARKER, "some text"]
        with pytest.raises(SyncError, match="must contain start marker"):
            _find_marker_pair(
                lines,
                CURRENT_BATCH_START_MARKER,
                CURRENT_BATCH_END_MARKER,
                "test",
            )

    def test_inverted_markers(self):
        lines = [
            CURRENT_BATCH_END_MARKER,
            "content",
            CURRENT_BATCH_START_MARKER,
        ]
        with pytest.raises(SyncError, match="marker order is invalid"):
            _find_marker_pair(
                lines,
                CURRENT_BATCH_START_MARKER,
                CURRENT_BATCH_END_MARKER,
                "test",
            )

    def test_same_line_markers_raises(self):
        """Start and end on same index (only end marker present once) -- edge case."""
        lines = ["other", CURRENT_BATCH_START_MARKER]
        with pytest.raises(SyncError, match="must contain start marker"):
            _find_marker_pair(
                lines,
                CURRENT_BATCH_START_MARKER,
                CURRENT_BATCH_END_MARKER,
                "test",
            )


# ---------------------------------------------------------------------------
# _parse_entries -- edge cases
# ---------------------------------------------------------------------------


class TestParseEntries:
    def test_no_entries_returns_empty(self):
        lines = ["Some text", "No headings here", ""]
        entries, first_idx = _parse_entries(lines)
        assert entries == []
        assert first_idx is None

    def test_single_entry_with_trailing_blanks(self):
        lines = ["### 2026-01-01 - Test entry", "Content", "", "", ""]
        entries, first_idx = _parse_entries(lines)
        assert len(entries) == 1
        assert first_idx == 0
        # Trailing blanks should be stripped from the entry.
        assert entries[0].lines[-1].strip() != ""

    def test_entries_preserve_order(self):
        lines = [
            "### 2026-01-01 - First",
            "Content A",
            "### 2026-01-02 - Second",
            "Content B",
        ]
        entries, _ = _parse_entries(lines)
        assert len(entries) == 2
        assert entries[0].date == "2026-01-01"
        assert entries[1].date == "2026-01-02"

    def test_fingerprint_ignores_trailing_whitespace(self):
        lines_a = ["### 2026-01-01 - Entry", "Content   "]
        lines_b = ["### 2026-01-01 - Entry", "Content"]
        entries_a, _ = _parse_entries(lines_a)
        entries_b, _ = _parse_entries(lines_b)
        assert entries_a[0].fingerprint == entries_b[0].fingerprint


# ---------------------------------------------------------------------------
# _parse_active_batch_state -- boundary conditions
# ---------------------------------------------------------------------------


class TestParseActiveBatchState:
    def test_no_signals_returns_all_none(self):
        state = _parse_active_batch_state(["Nothing relevant here."])
        assert state.current_batch is None
        assert state.last_completed_batch is None
        assert state.next_undefined_batch is None

    def test_completed_only_infers_next(self):
        """When only completed batches exist and no 'not yet defined' guard,
        current_batch should be inferred as last_completed + 1."""
        state = _parse_active_batch_state(
            ["Batch 10 is complete.", "Working on next items."]
        )
        assert state.current_batch == 11
        assert state.last_completed_batch == 10

    def test_current_equals_undefined_clears_current(self):
        """If current_batch matches next_undefined, current should be None."""
        state = _parse_active_batch_state(
            [
                "Batch 10 is complete.",
                "Batch 11 is not yet defined.",
                "Next batch to execute: Batch 11.",
            ]
        )
        assert state.current_batch is None
        assert state.next_undefined_batch == 11

    def test_explicit_current_wins(self):
        state = _parse_active_batch_state(
            [
                "Batch 10 is complete.",
                "Batch 11 is active.",
            ]
        )
        assert state.current_batch == 11
        assert state.last_completed_batch == 10

    def test_multiple_completed_picks_max(self):
        state = _parse_active_batch_state(
            [
                "Batch 8 is complete.",
                "Batch 9 is complete.",
                "Batch 10 is complete.",
            ]
        )
        assert state.last_completed_batch == 10

    def test_undefined_without_completed(self):
        state = _parse_active_batch_state(["Batch 1 is not yet defined."])
        assert state.current_batch is None
        assert state.next_undefined_batch == 1
        assert state.last_completed_batch is None


# ---------------------------------------------------------------------------
# Regex constant behaviour
# ---------------------------------------------------------------------------


class TestRegexPatterns:
    def test_section_3_re_case_insensitive(self):
        assert SECTION_3_RE.match("## 3. ACTIVE BATCH")
        assert SECTION_3_RE.match("## 3 Active batch and more")
        assert not SECTION_3_RE.match("## 4. Execution log")

    def test_section_4_re_case_insensitive(self):
        assert SECTION_4_RE.match("## 4. EXECUTION LOG")
        assert SECTION_4_RE.match("## 4 Execution log details")
        assert not SECTION_4_RE.match("## 3. Active batch")

    def test_entry_heading_re(self):
        m = ENTRY_HEADING_RE.match("### 2026-02-20 - Some title (Batch 11 WP-1)")
        assert m is not None
        assert m.group(1) == "2026-02-20"
        assert "Batch 11" in m.group(2)

    def test_entry_heading_re_rejects_malformed(self):
        assert ENTRY_HEADING_RE.match("### 2026-02-20 No dash separator") is None
        assert ENTRY_HEADING_RE.match("## 2026-02-20 - Wrong level") is None
        assert ENTRY_HEADING_RE.match("### not-a-date - Title") is None

    def test_batch_complete_re(self):
        assert BATCH_COMPLETE_RE.search("Batch 10 is complete.")
        assert BATCH_COMPLETE_RE.search("batch 10 is Complete")
        assert not BATCH_COMPLETE_RE.search("Batch 10 is active")

    def test_batch_current_re(self):
        assert BATCH_CURRENT_RE.search("Batch 11 is active.")
        assert BATCH_CURRENT_RE.search("Batch 11 is current")
        assert BATCH_CURRENT_RE.search("Batch 11 is in-progress")
        assert BATCH_CURRENT_RE.search("Batch 11 is in progress")
        assert not BATCH_CURRENT_RE.search("Batch 11 is complete")

    def test_batch_not_defined_re(self):
        assert BATCH_NOT_DEFINED_RE.search("Batch 12 is not yet defined.")
        assert not BATCH_NOT_DEFINED_RE.search("Batch 12 is active.")


# ---------------------------------------------------------------------------
# _fingerprint -- whitespace normalisation
# ---------------------------------------------------------------------------


class TestFingerprintNormalization:
    def test_trailing_whitespace_ignored(self):
        fp1 = _fingerprint(["line one   ", "line two  "])
        fp2 = _fingerprint(["line one", "line two"])
        assert fp1 == fp2

    def test_different_content_different_fingerprint(self):
        fp1 = _fingerprint(["line one"])
        fp2 = _fingerprint(["line two"])
        assert fp1 != fp2

    def test_empty_input(self):
        fp = _fingerprint([])
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA-256 hex digest


# ---------------------------------------------------------------------------
# _extract_entry_batch -- batch number extraction
# ---------------------------------------------------------------------------


class TestExtractEntryBatch:
    def test_no_batch_tag(self):
        entry = Entry(
            heading="### 2026-01-01 - Side fix",
            date="2026-01-01",
            title="Side fix",
            lines=("### 2026-01-01 - Side fix",),
            start_idx=0,
            fingerprint="abc",
        )
        assert _extract_entry_batch(entry) is None

    def test_batch_tag_extracted(self):
        entry = Entry(
            heading="### 2026-01-01 - Work (Batch 11 WP-1)",
            date="2026-01-01",
            title="Work (Batch 11 WP-1)",
            lines=("### 2026-01-01 - Work (Batch 11 WP-1)",),
            start_idx=0,
            fingerprint="abc",
        )
        assert _extract_entry_batch(entry) == 11
