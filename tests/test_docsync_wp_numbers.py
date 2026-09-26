"""Tests for docsync.parser._collect_wp_numbers."""

from __future__ import annotations

from docsync.models import Entry
from docsync.parser import _collect_wp_numbers


class TestCollectWpNumbers:
    def test_no_wp_tags(self):
        entry = Entry(
            heading="### 2026-01-01 - Side fix",
            date="2026-01-01",
            title="Side fix",
            lines=("### 2026-01-01 - Side fix",),
            start_idx=0,
            fingerprint="abc",
        )
        assert _collect_wp_numbers([entry]) == []

    def test_multiple_wp_tags(self):
        e1 = Entry(
            heading="### 2026-01-01 - WP-1 work (Batch 11 WP-1)",
            date="2026-01-01",
            title="WP-1 work (Batch 11 WP-1)",
            lines=("### 2026-01-01 - WP-1 work (Batch 11 WP-1)",),
            start_idx=0,
            fingerprint="a",
        )
        e2 = Entry(
            heading="### 2026-01-02 - WP-3 work (Batch 11 WP-3)",
            date="2026-01-02",
            title="WP-3 work (Batch 11 WP-3)",
            lines=("### 2026-01-02 - WP-3 work (Batch 11 WP-3)",),
            start_idx=0,
            fingerprint="b",
        )
        assert _collect_wp_numbers([e1, e2]) == [1, 3]
