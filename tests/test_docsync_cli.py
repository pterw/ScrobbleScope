"""Tests for docsync.cli: _read_lines, argparse, main() end-to-end."""

from __future__ import annotations

from pathlib import Path

import docsync.cli as cli_mod
import pytest
from docsync.cli import (
    _check_root_batch_files,
    _get_batch_log_path,
    _read_lines,
)
from docsync.models import SyncError

# ---------------------------------------------------------------------------
# _read_lines -- missing file
# ---------------------------------------------------------------------------


class TestReadLines:
    def test_missing_file_raises_sync_error(self, tmp_path: Path):
        with pytest.raises(SyncError, match="Required file is missing"):
            _read_lines(tmp_path / "nonexistent.md")


# ---------------------------------------------------------------------------
# main() argument handling
# ---------------------------------------------------------------------------


class TestMainArgs:
    def test_both_check_and_fix_returns_2(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check", "--fix"])
        assert cli_mod.main() == 2

    def test_negative_keep_non_current_returns_2(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(
            "sys.argv", ["doc_state_sync.py", "--fix", "--keep-non-current", "-1"]
        )
        assert cli_mod.main() == 2

    def test_no_mode_defaults_to_check(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py"])
        exit_code = cli_mod.main()
        captured = capsys.readouterr()
        assert "defaulting to --check" in captured.err
        # Fresh fixture has a stale placeholder in SESSION_CONTEXT, so
        # check mode should detect drift (exit 1).
        assert exit_code == 1

    def test_check_detects_drift(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """Dirty SESSION_CONTEXT (status block is stale placeholder) should
        cause --check to return 1."""
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        exit_code = cli_mod.main()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "drift detected" in captured.out

    def test_fix_writes_files(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        exit_code = cli_mod.main()
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "wrote updates" in captured.out or "no changes" in captured.out

    def test_fix_then_check_is_clean(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Running --fix followed by --check should pass (exit 0)."""
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        cli_mod.main()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        assert cli_mod.main() == 0

    def test_cross_validate_warnings_printed(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """Cross-validation warnings should appear on stderr."""
        playbook_path = sync_env / "PLAYBOOK.md"
        content = playbook_path.read_text(encoding="utf-8")
        # Add the count inside the Section 4 log entry body so that
        # _latest_test_count_from_entries (which scans current-batch entries,
        # not Section 3) can find it.
        content = content.replace(
            "Did some work.",
            "Did some work.\n\nValidated: **121 tests passing**",
        )
        playbook_path.write_text(content, encoding="utf-8")
        session_path = sync_env / ".claude" / "SESSION_CONTEXT.md"
        s_content = session_path.read_text(encoding="utf-8")
        s_content += "\n**99 passing**\n"
        session_path.write_text(s_content, encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        cli_mod.main()
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "mismatch" in captured.err.lower()

    def test_missing_playbook_raises_exits_2(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (sync_env / "PLAYBOOK.md").unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        assert cli_mod.main() == 2

    def test_missing_archive_raises_exits_2(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (
            sync_env / "docs" / "history" / "logs" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        ).unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        assert cli_mod.main() == 2


# ---------------------------------------------------------------------------
# Missing SESSION_CONTEXT.md regression tests (CI environment)
# ---------------------------------------------------------------------------


class TestMissingSessionContext:
    def test_check_passes_without_session_context(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """--check must not fail solely because SESSION_CONTEXT.md is missing."""
        (sync_env / ".claude" / "SESSION_CONTEXT.md").unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        exit_code = cli_mod.main()
        assert exit_code == 0

    def test_fix_does_not_create_session_context(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """--fix must not create SESSION_CONTEXT.md when it does not exist."""
        session_path = sync_env / ".claude" / "SESSION_CONTEXT.md"
        session_path.unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        cli_mod.main()
        assert not session_path.exists()


# ---------------------------------------------------------------------------
# _get_batch_log_path and _check_root_batch_files -- unit tests
# ---------------------------------------------------------------------------


class TestBatchLogHelpers:
    def test_get_batch_log_path_returns_correct_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ):
        """GIVEN LOGS_DIR monkeypatched to tmp_path/logs, WHEN _get_batch_log_path(7) is called,
        THEN it returns LOGS_DIR / BATCH7_LOG.md."""
        monkeypatch.setattr(cli_mod, "LOGS_DIR", tmp_path / "logs")
        result = _get_batch_log_path(7)
        assert result == tmp_path / "logs" / "BATCH7_LOG.md"

    def test_check_root_batch_files_warns(self, tmp_path: Path):
        """GIVEN a BATCH14_PROPOSAL.md file in root, WHEN checked,
        THEN a warning mentioning the file is returned."""
        (tmp_path / "BATCH14_PROPOSAL.md").write_text("# Proposal")
        warnings = _check_root_batch_files(tmp_path)
        assert len(warnings) == 1
        assert "BATCH14_PROPOSAL.md" in warnings[0]

    def test_check_root_batch_files_no_warn_when_clean(self, tmp_path: Path):
        """GIVEN no BATCH*.md files in root, WHEN checked,
        THEN no warnings are returned."""
        warnings = _check_root_batch_files(tmp_path)
        assert warnings == []

    def test_fix_creates_batch_log_file_for_stale_tagged_entry(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """GIVEN a PLAYBOOK with a stale Batch 10 entry inside current-batch markers,
        WHEN --fix is run, THEN a BATCH10_LOG.md is created in LOGS_DIR."""
        from textwrap import dedent

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

            This is stale.

            ### 2026-02-20 - Current work (Batch 11 WP-1)

            **294 passed**

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        exit_code = cli_mod.main()
        assert exit_code == 0
        logs_dir = sync_env / "docs" / "history" / "logs"
        batch_log = logs_dir / "BATCH10_LOG.md"
        assert batch_log.exists()
        assert "Batch 10 WP-5" in batch_log.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# --split-archive mode
# ---------------------------------------------------------------------------


class TestSplitArchiveMode:
    def test_split_archive_routes_tagged_entry(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """GIVEN a monolith archive with a tagged entry and an untagged entry,
        WHEN --split-archive runs, THEN the tagged entry is moved to a per-batch
        log and the untagged entry stays in the monolith archive."""
        from textwrap import dedent

        archive_text = dedent(
            """\
            # Archive

            ### 2026-01-10 - Work done (Batch 5 WP-2)

            Tagged content.

            ### 2026-01-05 - Untagged side task

            Untagged content.
        """
        )
        archive_path = (
            sync_env / "docs" / "history" / "logs" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.write_text(archive_text, encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--split-archive"])
        exit_code = cli_mod.main()
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "split-archive" in captured.out.lower()
        batch_log = sync_env / "docs" / "history" / "logs" / "BATCH5_LOG.md"
        assert batch_log.exists()
        assert "Batch 5 WP-2" in batch_log.read_text(encoding="utf-8")
        archive_out = archive_path.read_text(encoding="utf-8")
        assert "Batch 5 WP-2" not in archive_out
        assert "Untagged side task" in archive_out
