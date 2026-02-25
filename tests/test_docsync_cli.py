"""Tests for docsync.cli: _read_lines, argparse, main() end-to-end."""

from __future__ import annotations

from pathlib import Path

import docsync.cli as cli_mod
import pytest
from docsync.cli import _read_lines
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
