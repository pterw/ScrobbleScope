"""Tests for docsync.logic: _collect_wp_numbers, _cross_validate, _sync integration."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from docsync.logic import _cross_validate, _sync
from docsync.models import ActiveBatchState, Entry, SyncError
from docsync.parser import _collect_wp_numbers

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
        warnings = _cross_validate(
            ["**121 tests passing**"],
            ["**121 passing**"],
        )
        assert warnings == []

    def test_mismatched_counts_warns(self):
        warnings = _cross_validate(
            ["**121 tests passing**"],
            ["**119 passing**"],
        )
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

    def test_section3_mismatch_still_detected(self):
        """A genuine mismatch in Section 3 vs SESSION_CONTEXT still warns."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Current test count: **195 tests passing**",
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
# _sync integration tests -- filesystem-based, isolated via sync_env
# ---------------------------------------------------------------------------


class TestSyncIntegration:
    def _files(self, sync_env: Path) -> tuple[list[str], list[str], list[str]]:
        """Read the standard three files from the sync_env tmp directory."""
        playbook = (sync_env / "PLAYBOOK.md").read_text(encoding="utf-8").splitlines()
        archive = (
            (sync_env / "docs" / "history" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md")
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
        archive_text = "\n".join(result.archive_lines)
        assert "Batch 10 WP-5" in archive_text
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
            sync_env / "docs" / "history" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
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
