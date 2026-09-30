"""Tests for docsync.logic._split_archive and _dedup_sorted."""

from __future__ import annotations

from docsync.logic import _dedup_sorted, _split_archive
from docsync.models import Entry
from docsync.parser import _fingerprint


class TestSplitArchive:
    def test_tagged_entries_routed_by_batch(self):
        """GIVEN archive with a Batch 10 tagged entry,
        WHEN split, THEN the entry is in batch_groups[10] and not in remaining."""
        monolith = [
            "# Archive",
            "",
            "### 2026-01-05 - Work done (Batch 10 WP-1)",
            "",
            "Some content.",
            "",
        ]
        remaining, batch_groups = _split_archive(monolith)
        assert 10 in batch_groups
        assert len(batch_groups[10]) == 1
        remaining_text = "\n".join(remaining)
        assert "Batch 10 WP-1" not in remaining_text

    def test_untagged_entries_remain_in_monolith(self):
        """GIVEN archive with an untagged entry,
        WHEN split, THEN batch_groups is empty and entry stays in remaining."""
        monolith = [
            "# Archive",
            "",
            "### 2026-01-05 - Side task fix",
            "",
            "Some content.",
            "",
        ]
        remaining, batch_groups = _split_archive(monolith)
        assert batch_groups == {}
        remaining_text = "\n".join(remaining)
        assert "Side task fix" in remaining_text

    def test_mixed_entries_split_correctly(self):
        """GIVEN archive with both tagged and untagged entries,
        WHEN split, THEN each routes to the correct destination."""
        monolith = [
            "# Archive",
            "",
            "### 2026-01-06 - Tagged work (Batch 9 WP-2)",
            "",
            "Tagged content.",
            "",
            "### 2026-01-05 - Untagged side task",
            "",
            "Untagged content.",
            "",
        ]
        remaining, batch_groups = _split_archive(monolith)
        assert 9 in batch_groups
        assert len(batch_groups[9]) == 1
        remaining_text = "\n".join(remaining)
        assert "Untagged side task" in remaining_text
        assert "Tagged work" not in remaining_text


class TestDedupSorted:
    def test_same_fingerprint_keeps_newest(self):
        """When two entries have the same fingerprint, only the newest survives."""
        shared_lines = ("### 2026-01-01 - Duplicate entry", "Same content")
        fp = _fingerprint(shared_lines)
        older = Entry(
            heading="### 2026-01-01 - Duplicate entry",
            date="2026-01-01",
            title="Duplicate entry",
            lines=shared_lines,
            start_idx=0,
            fingerprint=fp,
        )
        newer = Entry(
            heading="### 2026-01-01 - Duplicate entry",
            date="2026-02-15",
            title="Duplicate entry",
            lines=shared_lines,
            start_idx=10,
            fingerprint=fp,
        )
        result = _dedup_sorted([older, newer])
        assert len(result) == 1
        assert result[0].date == "2026-02-15"
