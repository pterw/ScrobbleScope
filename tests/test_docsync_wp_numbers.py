"""Tests for docsync.parser._collect_wp_numbers."""

from __future__ import annotations

from docsync.models import Entry
from docsync.parser import ENTRY_HEADING_RE, _collect_wp_numbers, _fingerprint


def _entry(heading: str, body: str = "") -> Entry:
    """Build a real Entry from a heading and body, matching parser._parse_entries's shape."""
    match = ENTRY_HEADING_RE.match(heading)
    date, title = (match.group(1), match.group(2)) if match else ("2026-01-01", heading)
    lines = (heading, *body.splitlines()) if body else (heading,)
    return Entry(
        heading=heading,
        date=date,
        title=title,
        lines=lines,
        start_idx=0,
        fingerprint=_fingerprint(lines),
    )


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
        e1 = _entry(
            heading="### 2026-01-01 - WP-1 work (Batch 11 WP-1)",
            body="**Status:** WP-1 complete",
        )
        e2 = _entry(
            heading="### 2026-01-02 - WP-3 work (Batch 11 WP-3)",
            body="**Status:** WP-3 complete",
        )
        assert _collect_wp_numbers([e1, e2]) == [1, 3]

    def test_a_heading_tag_alone_does_not_complete_the_work_package(self):
        """F-DOCSYNC-15: the first commit of a multi-commit WP must not claim
        the whole package is done just because its heading names WP-4."""
        entries = [
            _entry(
                heading="### 2026-09-20 - (Batch 22 WP-4)",
                body="Some progress. No explicit completion line.",
            )
        ]
        assert _collect_wp_numbers(entries) == []

    def test_an_explicit_status_line_completes_the_work_package(self):
        entries = [
            _entry(
                heading="### 2026-09-20 - (Batch 22 WP-4)",
                body="**Status:** WP-4 complete\n\nEverything landed.",
            )
        ]
        assert _collect_wp_numbers(entries) == [4]

    def test_the_status_line_is_recognized_case_and_spacing_tolerant(self):
        entries = [
            _entry(
                heading="### 2026-09-20 - untagged", body="**Status:**   wp-7 Complete"
            )
        ]
        assert _collect_wp_numbers(entries) == [7]

    def test_a_status_line_for_a_different_wp_does_not_complete_this_ones_heading_tag(
        self,
    ):
        entries = [
            _entry(
                heading="### 2026-09-20 - (Batch 22 WP-4)",
                body="**Status:** WP-3 complete (an earlier package finished late)",
            )
        ]
        assert _collect_wp_numbers(entries) == [3]

    def test_several_entries_each_contribute_their_own_completion(self):
        entries = [
            _entry(heading="### 2026-09-19 - a", body="**Status:** WP-1 complete"),
            _entry(heading="### 2026-09-20 - b", body="Body with no completion line."),
            _entry(heading="### 2026-09-21 - c", body="**Status:** WP-2 complete"),
        ]
        assert _collect_wp_numbers(entries) == [1, 2]
