"""Tests for docsync.parser._fingerprint and docsync.parser._extract_entry_batch."""

from __future__ import annotations

import pytest
from docsync.models import Entry
from docsync.parser import _extract_entry_batch, _fingerprint

# ---------------------------------------------------------------------------
# _fingerprint / _normalize_block -- whitespace handling
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
# _extract_entry_batch -- edge cases
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
