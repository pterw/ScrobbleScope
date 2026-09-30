"""Tests for docsync.logic._merge_entries_into_log."""

from __future__ import annotations

from docsync.logic import _merge_entries_into_log
from docsync.models import Entry
from docsync.parser import _fingerprint


class TestMergeEntriesIntoLog:
    def _make_entry(self, date: str, batch: int, wp: int, body: str) -> Entry:
        """Build a minimal Entry with a properly computed fingerprint."""
        heading = f"### {date} - Work done (Batch {batch} WP-{wp})"
        lines = (heading, "", body)
        return Entry(
            heading=heading,
            date=date,
            title=f"Work done (Batch {batch} WP-{wp})",
            lines=lines,
            start_idx=0,
            fingerprint=_fingerprint(lines),
        )

    def test_empty_existing_creates_header(self):
        """GIVEN no existing log, WHEN an entry is merged,
        THEN a batch header line is created."""
        entry = self._make_entry("2026-01-01", 5, 1, "Some work.")
        result = _merge_entries_into_log([], [entry], 5)
        result_text = "\n".join(result)
        assert "# Batch 5 Execution Log" in result_text
        assert "Batch 5 WP-1" in result_text

    def test_deduplicates_by_fingerprint(self):
        """GIVEN an entry already in the log, WHEN merged again with same entry,
        THEN the heading appears exactly once."""
        entry = self._make_entry("2026-01-01", 5, 1, "Unique content.")
        first_pass = _merge_entries_into_log([], [entry], 5)
        result = _merge_entries_into_log(first_pass, [entry], 5)
        result_text = "\n".join(result)
        assert result_text.count("Batch 5 WP-1") == 1

    def test_newest_entry_appears_first(self):
        """GIVEN an older and a newer entry, WHEN merged,
        THEN the newer date appears before the older date in the output."""
        older = self._make_entry("2026-01-01", 5, 1, "Older work.")
        newer = self._make_entry("2026-01-02", 5, 2, "Newer work.")
        result = _merge_entries_into_log([], [older, newer], 5)
        text = "\n".join(result)
        assert text.index("2026-01-02") < text.index("2026-01-01")
