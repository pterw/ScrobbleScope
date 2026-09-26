"""Tests for docsync.logic._sync integration."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from docsync.logic import _sync
from docsync.models import SyncError


class TestSyncIntegration:
    def _files(self, sync_env: Path) -> tuple[list[str], list[str], list[str]]:
        """Read the standard three files from the sync_env tmp directory."""
        playbook = (sync_env / "PLAYBOOK.md").read_text(encoding="utf-8").splitlines()
        archive = (
            (sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md")
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
        """An untagged entry already in the monolith archive should not be
        duplicated when the same entry is rotated from PLAYBOOK."""
        # Entry must be UNTAGGED so it routes to untagged_rotated -> monolith dedup.
        entry_text = "### 2026-02-15 - Duplicate side-task entry\n\nSame content.\n"
        playbook_text = dedent(
            f"""\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

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
            sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.write_text(archive_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)
        result = _sync(playbook, archive, session, keep_non_current=0)
        # Tagged entries go to batch_log_updates -- untagged go to archive_lines.
        assert result.batch_log_updates == {}
        archive_out = "\n".join(result.archive_lines)
        assert archive_out.count("Duplicate side-task entry") == 1

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

    def test_session_status_uses_active_definition_plan(self, sync_env: Path):
        """The sync path passes the finite plan through to the renderer."""
        playbook_path = sync_env / "PLAYBOOK.md"
        playbook_text = playbook_path.read_text(encoding="utf-8").replace(
            "Did some work.", "**Status:** WP-1 complete.\n\nDid some work."
        )
        playbook_path.write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)

        result = _sync(
            playbook,
            archive,
            session,
            keep_non_current=4,
            planned_wp_numbers=(1, 3),
        )

        assert "- Next expected work package: WP-3." in result.session_lines
        assert all("WP-2" not in line for line in result.session_lines)

    def test_session_status_uses_newest_side_task_full_suite_count(
        self, sync_env: Path
    ):
        """The renderer mirrors the same full-suite authority used by DOC006."""
        playbook_path = sync_env / "PLAYBOOK.md"
        playbook_text = playbook_path.read_text(encoding="utf-8")
        playbook_text = playbook_text.replace(
            "Did some work.", "`pytest -q` -- **390 passed**."
        )
        playbook_text += (
            "\n### 2026-08-05 - Review remediation (side-task)\n\n"
            "Focused -- **112 passed**. `pytest -q` -- **420 passed**.\n"
        )
        playbook_path.write_text(playbook_text, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)

        result = _sync(playbook, archive, session, keep_non_current=4)

        assert "- Latest validated test count: **420 passed**." in result.session_lines

    def test_three_tagged_commits_do_not_claim_the_package_done_until_the_last(
        self, sync_env: Path
    ):
        """Reproduces docs/history/logs/BATCH22_LOG.md: three (Batch 22 WP-4)
        entries landed before WP-4 was actually finished (F-DOCSYNC-15)."""
        first_two_commits = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 22 is active.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-09-20 - (Batch 22 WP-4) first commit

            Progress.

            ### 2026-09-20 - (Batch 22 WP-4) second commit

            More progress.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(first_two_commits, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)

        # Before the third commit lands, the tag alone must not claim WP-4 done.
        result = _sync(playbook, archive, session, keep_non_current=4)
        status = "\n".join(result.session_lines)
        assert "Completed work packages in current-batch entries: none." in status

        third_commit = first_two_commits.replace(
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
            "### 2026-09-20 - (Batch 22 WP-4) third commit\n\n"
            "**Status:** WP-4 complete\n\n"
            "Done.\n\n"
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        )
        (sync_env / "PLAYBOOK.md").write_text(third_commit, encoding="utf-8")
        playbook, archive, session = self._files(sync_env)

        # Only the explicit completion line on the third commit closes WP-4.
        result = _sync(playbook, archive, session, keep_non_current=4)
        status = "\n".join(result.session_lines)
        assert "Completed work packages in current-batch entries: WP-4." in status

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
