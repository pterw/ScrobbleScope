"""Tests for docsync.logic: _collect_wp_numbers, _cross_validate, _sync integration."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from docsync.logic import (
    _cross_validate,
    _latest_test_count_from_entries,
    _merge_entries_into_log,
    _split_archive,
    _sync,
)
from docsync.models import ActiveBatchState, Entry, SyncError
from docsync.parser import _collect_wp_numbers, _fingerprint

# ---------------------------------------------------------------------------
# _collect_wp_numbers -- edge cases
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# _cross_validate -- mismatch and stale detection
# ---------------------------------------------------------------------------


class TestCrossValidate:
    def test_no_counts_no_warnings(self):
        warnings = _cross_validate(
            ["# PLAYBOOK", "No counts here"],
            ["# SESSION", "No counts here"],
        )
        assert warnings == []

    def test_matching_counts_no_warning(self):
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-20 - Work (Batch 11 WP-1)",
            "",
            "**121 tests passing**",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]
        warnings = _cross_validate(playbook, ["**121 passing**"])
        assert warnings == []

    def test_mismatched_counts_warns(self):
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-20 - Work (Batch 11 WP-1)",
            "",
            "**121 tests passing**",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]
        warnings = _cross_validate(playbook, ["**119 passing**"])
        assert len(warnings) == 1
        assert "mismatch" in warnings[0].lower()

    def test_stale_header_in_playbook(self):
        warnings = _cross_validate(
            ["# PLAYBOOK: refactor monolithic app.py", "content"],
            ["# SESSION", "content"],
        )
        assert any("Stale header" in w for w in warnings)

    def test_stale_header_in_session_context(self):
        warnings = _cross_validate(
            ["# PLAYBOOK", "content"],
            ["# SESSION: Post-Batch 8 cleanup", "content"],
        )
        assert any("Stale header" in w for w in warnings)

    def test_stale_phrase_beyond_first_5_lines_not_detected(self):
        """Stale phrase detection only scans the first 5 lines."""
        playbook = ["line"] * 6 + ["refactor monolithic mentioned late"]
        warnings = _cross_validate(playbook, ["# SESSION"])
        stale_warnings = [w for w in warnings if "Stale header" in w]
        assert stale_warnings == []

    def test_counts_only_in_one_file_no_warning(self):
        """If only one file has counts, there's nothing to compare."""
        warnings = _cross_validate(
            ["**121 tests passing**"],
            ["No counts here"],
        )
        assert warnings == []

    def test_section4_historical_count_ignored(self):
        """Historical counts in Section 4 should not trigger a mismatch."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Current test count: **199 tests passing**",
            "",
            "## 4. Execution log",
            "",
            "### 2026-02-20 - Some prior commit",
            "",
            "Validated: **185 passed**",
            "",
        ]
        session = ["# SESSION", "", "Test count: **199 tests passing**"]
        warnings = _cross_validate(playbook, session)
        count_warnings = [w for w in warnings if "mismatch" in w.lower()]
        assert count_warnings == []

    def test_current_entry_count_mismatch_warns(self):
        """Count from most-recent current-batch Section 4 entry vs SESSION_CONTEXT warns."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-20 - Recent work (Batch 11 WP-1)",
            "",
            "Validated: **185 passed**",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]
        session = ["# SESSION", "", "Test count: **199 tests passing**"]
        warnings = _cross_validate(playbook, session)
        assert any("mismatch" in w.lower() for w in warnings)

    def test_archive_link_exists_no_warning(self, tmp_path, monkeypatch):
        """No warning when linked archive file exists."""
        archive_dir = tmp_path / "docs" / "history"
        archive_dir.mkdir(parents=True)
        (archive_dir / "BATCH0_DEFINITION.md").write_text("# Batch 0")
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 0 | Title | `docs/history/BATCH0_DEFINITION.md` |",
        ]
        warnings = _cross_validate(playbook, ["# SESSION"])
        archive_warnings = [w for w in warnings if "Broken archive link" in w]
        assert archive_warnings == []

    def test_archive_link_missing_warns(self, tmp_path, monkeypatch):
        """Warning when linked archive file does not exist."""
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 1 | Title | `docs/history/BATCH1_DEFINITION.md` |",
        ]
        warnings = _cross_validate(playbook, ["# SESSION"])
        assert any("Broken archive link" in w for w in warnings)
        assert any("BATCH1_DEFINITION.md" in w for w in warnings)

    def test_archive_link_multiple_missing(self, tmp_path, monkeypatch):
        """Each broken link produces its own warning."""
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 0 | A | `docs/history/BATCH0_DEFINITION.md` |",
            "| 1 | B | `docs/history/BATCH1_DEFINITION.md` |",
        ]
        warnings = _cross_validate(playbook, ["# SESSION"])
        archive_warnings = [w for w in warnings if "Broken archive link" in w]
        assert len(archive_warnings) == 2

    def test_archive_link_multiple_on_same_line(self, tmp_path, monkeypatch):
        """Multiple archive links on one line are all validated."""
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 0 | A | `docs/history/A.md` `docs/history/B.md` |",
        ]
        warnings = _cross_validate(playbook, ["# SESSION"])
        archive_warnings = [w for w in warnings if "Broken archive link" in w]
        assert len(archive_warnings) == 2
        assert "A.md" in archive_warnings[0]
        assert "B.md" in archive_warnings[1]

    def test_cross_validate_skips_session_checks_when_none(self):
        """_cross_validate with session_lines=None should not raise and
        should produce no session-specific warnings."""
        warnings = _cross_validate(["# PLAYBOOK", "content"], None)
        session_warnings = [w for w in warnings if "SESSION_CONTEXT" in w]
        assert session_warnings == []


# ---------------------------------------------------------------------------
# _latest_test_count_from_entries -- unit tests
# ---------------------------------------------------------------------------


class TestLatestTestCount:
    def _minimal_playbook(self, entry_body_lines: list[str]) -> list[str]:
        """Wrap entry_body_lines inside a minimal PLAYBOOK with Section 4 markers."""
        return [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-20 - Work (Batch 11 WP-1)",
            "",
            *entry_body_lines,
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]

    def test_no_markers_returns_none(self):
        """Flat playbook with no Section 4 markers returns None."""
        playbook = ["# PLAYBOOK", "", "## 4. Execution log", "", "Some content."]
        assert _latest_test_count_from_entries(playbook) is None

    def test_entry_with_count_returns_count(self):
        """Bold test count in a current-batch entry body is extracted."""
        playbook = self._minimal_playbook(["Validated: **142 passed**"])
        assert _latest_test_count_from_entries(playbook) == 142

    def test_entry_without_count_returns_none(self):
        """Entry with no bold count produces None."""
        playbook = self._minimal_playbook(["No count here."])
        assert _latest_test_count_from_entries(playbook) is None

    def test_multiple_entries_uses_newest(self):
        """With two entries inside markers, the newest (first) entry's count is used."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-21 - Newer work (Batch 11 WP-2)",
            "",
            "**200 tests passing**",
            "",
            "### 2026-02-20 - Older work (Batch 11 WP-1)",
            "",
            "**190 tests passing**",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]
        # Parser returns entries in file order (newest heading is first here);
        # _latest_test_count_from_entries scans in that order.
        result = _latest_test_count_from_entries(playbook)
        assert result == 200


# ---------------------------------------------------------------------------
# _sync integration tests -- filesystem-based, isolated via sync_env
# ---------------------------------------------------------------------------


class TestSyncIntegration:
    def _files(self, sync_env: Path) -> tuple[list[str], list[str], list[str]]:
        """Read the standard three files from the sync_env tmp directory."""
        playbook = (sync_env / "PLAYBOOK.md").read_text(encoding="utf-8").splitlines()
        archive = (
            (
                sync_env
                / "docs"
                / "history"
                / "logs"
                / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
            )
            .read_text(encoding="utf-8")
            .splitlines()
        )
        session = (
            (sync_env / ".claude" / "SESSION_CONTEXT.md")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        return playbook, archive, session

    def test_basic_sync_succeeds(self, sync_env: Path):
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=4)
        assert result.current_batch_entry_count == 1
        assert result.rotated_count == 0

    def test_missing_session_context_succeeds(self, sync_env: Path):
        """Passing None as session_lines should not raise."""
        playbook, archive, _ = self._files(sync_env)
        result = _sync(playbook, archive, None, keep_non_current=4)
        assert result.session_lines is None
        assert result.current_batch_entry_count == 1

    def test_missing_section_3_raises(self, sync_env: Path):
        playbook_path = sync_env / "PLAYBOOK.md"
        playbook_path.write_text(
            "# PLAYBOOK\n\n## 4. Execution log\n\nContent\n"
            "\n<!-- DOCSYNC:CURRENT-BATCH-START -->\n"
            "<!-- DOCSYNC:CURRENT-BATCH-END -->\n",
            encoding="utf-8",
        )
        playbook, archive, session = self._files(sync_env)
        with pytest.raises(SyncError, match="Could not find section heading"):
            _sync(playbook, archive, session, keep_non_current=4)

    def test_missing_markers_in_section_4_raises(self, sync_env: Path):
        playbook_path = sync_env / "PLAYBOOK.md"
        playbook_path.write_text(
            "# PLAYBOOK\n\n## 3. Active batch\n\nBatch 11 is active.\n\n"
            "## 4. Execution log\n\nNo markers here.\n",
            encoding="utf-8",
        )
        playbook, archive, session = self._files(sync_env)
        with pytest.raises(SyncError, match="must contain start marker"):
            _sync(playbook, archive, session, keep_non_current=4)

    def test_stale_entries_rotated_to_archive(self, sync_env: Path):
        """Entries from a completed batch inside current-batch markers
        should be rotated out."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 10 is complete.
            Batch 11 is active.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-18 - Old work (Batch 10 WP-5)

            This is stale -- batch 10 is done.

            ### 2026-02-20 - Current work (Batch 11 WP-1)

            This is current.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=4)
        assert result.rotated_count == 1
        assert result.current_batch_entry_count == 1
        # Tagged (Batch 10 WP-5) entry routes to per-batch log, not monolith.
        assert 10 in result.batch_log_updates
        batch_10_text = "\n".join(result.batch_log_updates[10])
        assert "Batch 10 WP-5" in batch_10_text
        archive_text = "\n".join(result.archive_lines)
        assert "Batch 10 WP-5" not in archive_text
        playbook_text_after = "\n".join(result.playbook_lines)
        assert "Batch 11 WP-1" in playbook_text_after

    def test_deduplication_across_archive(self, sync_env: Path):
        """An entry that already exists in the archive (same fingerprint)
        should not be duplicated on rotation."""
        entry_text = (
            "### 2026-02-15 - Duplicate entry (Batch 10 WP-1)\n\nSame content.\n"
        )
        playbook_text = dedent(
            f"""\
            # PLAYBOOK

            ## 3. Active batch

            Batch 10 is complete.
            Batch 11 is active.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-20 - Current work (Batch 11 WP-1)

            Current content.

            <!-- DOCSYNC:CURRENT-BATCH-END -->

            {entry_text}
        """
        )
        archive_text = f"# Archive\n\n{entry_text}"
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        archive_path = (
            sync_env / "docs" / "history" / "logs" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.write_text(archive_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=0)
        archive_out = "\n".join(result.archive_lines)
        count = archive_out.count("Duplicate entry (Batch 10 WP-1)")
        assert count == 1

    def test_keep_non_current_zero_rotates_all(self, sync_env: Path):
        """With keep_non_current=0, all non-current entries should rotate."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-20 - Current (Batch 11 WP-1)

            Current.

            <!-- DOCSYNC:CURRENT-BATCH-END -->

            ### 2026-02-10 - Old untagged entry

            Should be rotated with keep_non_current=0.
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=0)
        assert result.kept_non_current_count == 0
        assert result.rotated_count == 1

    def test_empty_section_4_no_entries(self, sync_env: Path):
        """Section 4 with markers but no entries (valid at batch boundary)."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 10 is complete. Batch 11 is not yet defined.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=4)
        assert result.current_batch_entry_count == 0
        assert result.rotated_count == 0

    def test_session_context_status_block_updated(self, sync_env: Path):
        """STATUS markers in SESSION_CONTEXT should be refreshed."""
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=4)
        session_text = "\n".join(result.session_lines)
        assert "Batch 11" in session_text
        assert "Section 3 and Section 4" in session_text

    def test_session_context_missing_status_markers_raises(self, sync_env: Path):
        session_path = sync_env / ".claude" / "SESSION_CONTEXT.md"
        session_path.write_text(
            "# SESSION CONTEXT\n\nNo markers here.\n", encoding="utf-8"
        )
        playbook, archive, session = self._files(sync_env)
        with pytest.raises(SyncError, match="must contain start marker"):
            _sync(playbook, archive, session, keep_non_current=4)

    def test_untagged_entries_kept_when_no_current_batch_tags(self, sync_env: Path):
        """When no entries are tagged for the current batch, ambiguous
        untagged entries should be kept (not rotated) to avoid data loss."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-20 - Side task fix

            Untagged entry, no batch number.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=4)
        assert result.current_batch_entry_count == 1
        assert result.rotated_count == 0

    def test_untagged_entries_stale_when_tagged_current_exists(self, sync_env: Path):
        """When tagged current-batch entries exist, untagged entries inside
        the markers should be treated as stale."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-19 - Side task fix

            Untagged entry.

            ### 2026-02-20 - Real work (Batch 11 WP-1)

            Tagged current entry.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=4)
        assert result.current_batch_entry_count == 1
        assert result.kept_non_current_count == 1

    def test_batch_log_lines_parameter_merges_into_existing(self, sync_env: Path):
        """GIVEN existing batch log content passed via batch_log_lines,
        WHEN a stale tagged entry is rotated by _sync,
        THEN the prior log content is preserved alongside the new entry."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 10 is complete.
            Batch 11 is active.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-18 - Old work (Batch 10 WP-3)

            This is stale.

            ### 2026-02-20 - Current work (Batch 11 WP-1)

            This is current.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        prior_log_lines = [
            "# Batch 10 Execution Log",
            "",
            "### 2026-02-01 - Earlier work (Batch 10 WP-1)",
            "",
            "Prior content.",
        ]
        result = _sync(
            playbook,
            archive,
            session,
            keep_non_current=4,
            batch_log_lines={10: prior_log_lines},
        )
        assert 10 in result.batch_log_updates
        batch_10_text = "\n".join(result.batch_log_updates[10])
        assert "Earlier work" in batch_10_text
        assert "Old work" in batch_10_text

    def test_untagged_rotated_entry_stays_in_monolith(self, sync_env: Path):
        """GIVEN a non-current untagged entry below the current-batch markers,
        WHEN _sync rotates it with keep_non_current=0,
        THEN it goes to archive_lines, not batch_log_updates."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-20 - Current (Batch 11 WP-1)

            Current.

            <!-- DOCSYNC:CURRENT-BATCH-END -->

            ### 2026-02-10 - Untagged old entry

            No batch tag here.
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=0)
        assert result.rotated_count == 1
        assert result.batch_log_updates == {}
        archive_text = "\n".join(result.archive_lines)
        assert "Untagged old entry" in archive_text


# ---------------------------------------------------------------------------
# _merge_entries_into_log -- unit tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# _split_archive -- unit tests
# ---------------------------------------------------------------------------


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
