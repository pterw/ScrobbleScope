"""Tests for docsync.cli: _read_lines, argparse, main() end-to-end.

The second half of this module drives the real `scripts/doc_state_sync.py`
through `subprocess` inside temporary, tracked Git repositories. That is
deliberate: the close-out and archive-maintenance modes move files, publish
several documents in one transaction, and read `git ls-files`, and an
in-process call with patched path constants cannot show that the shipped
entry point does those things in the shipped order.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import docsync.cli as cli_mod
import pytest
from docsync.archives import COLD_DIRECTORY, HOT_DIRECTORY, INDEX_START_MARKER
from docsync.cli import (
    _check_root_batch_files,
    _get_batch_log_path,
    _read_lines,
)
from docsync.integrity import collect_tracked_paths as collect_real_tracked_paths
from docsync.models import SyncError
from docsync.renderer import SIDE_ARCHIVE_PREFIX

# ---------------------------------------------------------------------------
# _read_lines -- missing file
# ---------------------------------------------------------------------------


class TestReadLines:
    def test_missing_file_raises_sync_error(self, tmp_path: Path):
        with pytest.raises(SyncError, match="Required file is missing"):
            _read_lines(tmp_path / "nonexistent.md")


# ---------------------------------------------------------------------------
# LIVE_DOCUMENT_PATHS / SESSION_CONTEXT_PATH -- single source of truth
#
# cli.py once restated integrity.py's own `_LIVE_DOCUMENT_PATHS` and
# `_SESSION_CONTEXT_PATH` verbatim, so editing one silently left the other
# disagreeing about which documents get scanned. cli.py now derives its Path
# constants from integrity.py's canonical relative-path strings instead of
# declaring a second list, so this test fails if a future edit reintroduces
# an independent literal in either module.
# ---------------------------------------------------------------------------


class TestLiveDocumentPathsSingleSource:
    def test_cli_paths_are_built_from_integritys_canonical_relative_paths(self):
        import docsync.integrity as integrity_mod

        assert [p.as_posix() for p in cli_mod.LIVE_DOCUMENT_PATHS] == list(
            integrity_mod.LIVE_DOCUMENT_RELATIVE_PATHS
        )
        assert (
            cli_mod.SESSION_CONTEXT_PATH.as_posix()
            == integrity_mod.SESSION_CONTEXT_RELATIVE_PATH
        )

    def test_findings_path_is_not_a_second_hardcoded_literal(self):
        """The FINDINGS.md entry traces back to findings.ACTIVE_PATH, not a
        second literal spelling of the filename."""
        import docsync.findings as findings_mod
        import docsync.integrity as integrity_mod

        assert findings_mod.ACTIVE_PATH in integrity_mod.LIVE_DOCUMENT_RELATIVE_PATHS


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
        assert exit_code == 1

    def test_check_fails_on_stale_session_context(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """A stale managed session rendering is a blocking integrity error."""
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        exit_code = cli_mod.main()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "ERROR DOC005" in captured.err

    def test_fix_revalidates_and_clears_fixable_session_error(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """--fix clears deterministic session drift before final validation."""
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        exit_code = cli_mod.main()
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SESSION_CONTEXT" in captured.out or "wrote updates" in captured.out
        assert "ERROR DOC005" not in captured.err
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        exit_code = cli_mod.main()
        assert exit_code == 0

    def test_check_fails_on_dead_live_reference(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """A dead reference in a canonical live document exits one with DOC001."""
        agents = sync_env / "AGENTS.md"
        agents.write_text("See `docs/missing.md`.\n", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])

        assert cli_mod.main() == 1

        assert "ERROR DOC001 AGENTS.md:1" in capsys.readouterr().err

    def test_fix_fails_on_dead_live_reference(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """Final-state validation keeps an unresolved DOC001 blocking after --fix."""
        agents = sync_env / "AGENTS.md"
        agents.write_text("See `docs/missing.md`.\n", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])

        assert cli_mod.main() == 1

        assert "ERROR DOC001 AGENTS.md:1" in capsys.readouterr().err

    def test_fix_normalizes_archive_then_passes(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """--fix repairs renderer-owned archive formatting without moving entries."""
        archive = sync_env / "docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        archive.write_text("# stale prefix\n", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])

        assert cli_mod.main() == 0

        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        assert cli_mod.main() == 0

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

    def test_fix_renders_next_wp_from_active_definition_plan(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """The CLI supplies the active definition's finite plan to sync."""
        (sync_env / "BATCH11_DEFINITION.md").write_text(
            "# BATCH11\n\n"
            "**Branch:** `wip/batch-11`.\n\n"
            "### WP-1 -- Complete\n\n"
            "### WP-2 -- Absorbed into WP-1\n\n"
            "### WP-3 -- Next\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])

        assert cli_mod.main() == 0

        session = (sync_env / ".claude" / "SESSION_CONTEXT.md").read_text(
            encoding="utf-8"
        )
        assert "- Next expected work package: WP-3." in session
        assert "- Next expected work package: WP-2." not in session

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
            sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        ).unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        assert cli_mod.main() == 2

    def test_git_invocation_oserror_exits_2_without_traceback(
        self,
        sync_env: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys,
    ):
        """The CLI preserves its malformed-environment exit contract for Git OSErrors."""

        def failing_runner(*args, **kwargs):
            raise FileNotFoundError(2, "missing", r"C:\private\bin\git.exe")

        def collect_with_missing_git(repo_root: Path):
            return collect_real_tracked_paths(repo_root, runner=failing_runner)

        monkeypatch.setattr(cli_mod, "collect_tracked_paths", collect_with_missing_git)
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])

        assert cli_mod.main() == 2

        captured = capsys.readouterr()
        assert (
            "doc_state_sync failed: Repository tracked-file discovery failed"
            in captured.err
        )
        assert "Traceback" not in captured.err
        assert "private" not in captured.err
        assert "git ls-files" not in captured.err

    def test_git_nonzero_exits_2_without_stderr_or_traceback(
        self,
        sync_env: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys,
    ):
        """A failed tracked-file query cannot render credential-like stderr."""

        def failing_runner(*args, **kwargs):
            return subprocess.CompletedProcess(
                args[0],
                128,
                stdout="",
                stderr=(
                    "fatal: https://user:secret-token@example.invalid/private.git "
                    r"C:\private\checkout"
                ),
            )

        def collect_with_failed_git(repo_root: Path):
            return collect_real_tracked_paths(repo_root, runner=failing_runner)

        monkeypatch.setattr(cli_mod, "collect_tracked_paths", collect_with_failed_git)
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])

        assert cli_mod.main() == 2

        captured = capsys.readouterr()
        assert (
            "doc_state_sync failed: Repository tracked-file discovery failed"
            in captured.err
        )
        for secret in (
            "Traceback",
            "secret-token",
            "example.invalid",
            "private",
            "git ls-files",
        ):
            assert secret not in captured.err


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
            Batch 11 is active. Definition: `BATCH11_DEFINITION.md`.

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
    def test_split_archive_missing_archive_returns_2(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """GIVEN no archive file, WHEN --split-archive runs,
        THEN it exits with code 2 (SyncError surfaced)."""
        archive_path = (
            sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--split-archive"])
        assert cli_mod.main() == 2

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
            sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
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

    def test_split_archive_refuses_while_another_writer_holds_the_lock(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """`--split-archive` must take the same single-writer lock every other
        publishing mode takes, so it can never race a concurrent `--fix` or
        `--close-batch` that is already writing the same archive paths.

        Before the fix, `--split-archive` wrote through a bare
        `path.write_text` with no `_exclusive_lock` at all, so this scenario
        would previously succeed (exit 0) while another writer held the lock
        -- the exact hazard the lock exists to prevent.
        """
        from textwrap import dedent

        archive_text = dedent(
            """\
            # Archive

            ### 2026-01-10 - Work done (Batch 5 WP-2)

            Tagged content.
        """
        )
        archive_path = (
            sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.write_text(archive_text, encoding="utf-8")
        before_archive = archive_path.read_bytes()
        batch_log = sync_env / "docs" / "history" / "logs" / "BATCH5_LOG.md"
        (sync_env / ".docsync.lock").write_text("999", encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--split-archive"])
        exit_code = cli_mod.main()

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "docsync writer" in captured.err
        assert archive_path.read_bytes() == before_archive
        assert not batch_log.exists()

    def test_split_archive_failure_partway_through_changes_nothing(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """A crash between writing the per-batch log and rewriting the
        trimmed monolith must not leave an entry duplicated in both, or
        removed from the monolith before it exists anywhere else.
        Publication is atomic or it changes nothing on disk at all --
        checked here against the actual file bytes, not merely that an
        exception propagated.
        """
        from textwrap import dedent

        from docsync import transaction

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
            sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.write_text(archive_text, encoding="utf-8")
        before_archive = archive_path.read_bytes()
        batch_log = sync_env / "docs" / "history" / "logs" / "BATCH5_LOG.md"
        assert not batch_log.exists()

        original = transaction._atomic_write
        calls = {"n": 0}

        def fake(path, payload):
            calls["n"] += 1
            if calls["n"] >= 2:
                raise OSError("disk full")
            original(path, payload)

        monkeypatch.setattr(transaction, "_atomic_write", fake)

        with pytest.raises(OSError, match="disk full"):
            cli_mod._split_archive_mode()

        # The first of the two writes (the new per-batch log, sorted first)
        # landed before the injected failure on the second. Rollback must
        # have undone that half too: the archive keeps its exact starting
        # bytes and the log this run would have created does not exist.
        assert archive_path.read_bytes() == before_archive
        assert not batch_log.exists()
        assert not (sync_env / ".docsync.lock").exists()
        assert not (sync_env / ".docsync.journal").exists()

    def test_split_archive_rejects_a_source_changed_before_publication(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """A source this mode read while planning the split, then edited
        before the transaction actually writes, must sink the run rather
        than publish a decision made about content that no longer matches
        disk. Reproduces the review's staleness concern for `--split-archive`
        specifically (no source in this mode was staleness-checked at all
        before the fix, since it never called `transaction.publish`)."""
        from textwrap import dedent

        archive_text = dedent(
            """\
            # Archive

            ### 2026-01-10 - Work done (Batch 5 WP-2)

            Tagged content.
        """
        )
        archive_path = (
            sync_env / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.write_text(archive_text, encoding="utf-8")
        batch_log = sync_env / "docs" / "history" / "logs" / "BATCH5_LOG.md"

        real_publish = cli_mod.publish

        def spy(root, updates, expected):
            archive_path.write_text(
                archive_text + "\nEdited mid-flight.\n", encoding="utf-8"
            )
            return real_publish(root, updates, expected)

        monkeypatch.setattr(cli_mod, "publish", spy)

        with pytest.raises(SyncError, match="Source changed before publication"):
            cli_mod._split_archive_mode()

        # The refusal must have written nothing: no per-batch log appeared.
        assert not batch_log.exists()


# ---------------------------------------------------------------------------
# Real-CLI tests in temporary tracked Git corpora
#
# Everything below runs `scripts/doc_state_sync.py` as a subprocess. The
# corpus is a throwaway Git repository under `tmp_path`, with its own
# `core.hooksPath` so no hook configured on this machine can run inside it.
# ---------------------------------------------------------------------------

DOCSYNC_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "doc_state_sync.py"

CORPUS_PLAYBOOK = """\
# PLAYBOOK

## 2. Batch order (strict sequence)

### Batch index

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 22 | Enrichment | `BATCH22_DEFINITION.md` | -- |

## 3. Active batch + next action

- **Batch 22 is complete.**
- Batch 23 is not yet defined.

## 4. Execution log

Preamble.

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-09-10 - Closing work (Batch 22 WP-1)

Ran `pytest -q` -- **1234 passed**.

<!-- DOCSYNC:CURRENT-BATCH-END -->
"""

CORPUS_DEFINITION = """\
# Batch 22 -- Enrichment

**Branch:** `feat/batch22-enrichment`.

### ~~WP-1 -- Cache layer~~ -- **DONE**

Shipped and reviewed.

### WP-2 -- Correction worker (ABSORBED INTO WP-1)

Folded into WP-1 during review.
"""

CORPUS_SESSION = """\
# SESSION_CONTEXT

## 1. Current state

| Field | Value |
|-------|-------|
| Batch 22 status | Complete |

<!-- DOCSYNC:STATUS-START -->
- placeholder
<!-- DOCSYNC:STATUS-END -->

## 5. Notes

Nothing else.
"""

CORPUS_FINDINGS = """\
# Findings

## P2 -- Open

### F-B22-1: Correction worker retries too eagerly

- [ ] **Status:** open

The worker retries without a cap.
"""

CORPUS_FINDINGS_ARCHIVE = """\
# Findings archive

Rotated findings live here.
"""

CORPUS_TOML = """\
[archives]
max_lines = 500
cold_days = 365

[closeout]
admit_from_batch = 22
"""

ARCHIVED_DEFINITION = "docs/history/definitions/BATCH22_DEFINITION.md"
SIDE_ARCHIVE = "docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
FINDINGS_ARCHIVE = "docs/history/findings/FINDINGS_ARCHIVE.md"


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run one Git command inside the throwaway corpus."""
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _write(root: Path, relative: str, text: str) -> None:
    """Write one corpus file, creating its directory."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _make_corpus(root: Path, **overrides: str) -> Path:
    """Build and commit a minimal tracked corpus the gate understands.

    Every document is an override point, so a test states only the one edit
    that matters to it and the rest of the corpus keeps its known shape.
    ``core.hooksPath`` is redirected into the corpus so no hook configured on
    the machine running the suite can execute inside it.
    """
    files = {
        "PLAYBOOK.md": CORPUS_PLAYBOOK,
        "BATCH22_DEFINITION.md": CORPUS_DEFINITION,
        ".claude/SESSION_CONTEXT.md": CORPUS_SESSION,
        "FINDINGS.md": CORPUS_FINDINGS,
        FINDINGS_ARCHIVE: CORPUS_FINDINGS_ARCHIVE,
        SIDE_ARCHIVE: "\n".join(SIDE_ARCHIVE_PREFIX) + "\n",
        ".docsync.toml": CORPUS_TOML,
        "AGENTS.md": "# AGENTS\n\nSee `FINDINGS.md`.\n",
        "HANDOFF_PROMPT.md": "# Handoff\n\nRead `AGENTS.md`.\n",
        "AGENT_NOTES.md": "# Notes\n\nRules live in `AGENTS.md`.\n",
    }
    files.update(overrides)
    for relative, text in files.items():
        _write(root, relative, text)
    _git(root, "init", "-q")
    _git(root, "config", "core.hooksPath", str(root / ".nohooks"))
    _git(root, "config", "user.email", "docsync@example.invalid")
    _git(root, "config", "user.name", "docsync tests")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "corpus")
    return root


def _run_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the shipped entry point exactly as an operator would."""
    return subprocess.run(
        [sys.executable, str(DOCSYNC_SCRIPT), *args],
        cwd=root,
        capture_output=True,
        text=True,
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    """Return every corpus file's exact bytes, Git's own directory excluded."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


class TestCloseBatchMode:
    """`--close-batch N` validates every close-out signal before it writes."""

    def test_check_reports_the_missing_close_out_evidence(self, tmp_path: Path):
        """A claimed-complete batch with a root definition fails --check."""
        _make_corpus(tmp_path)

        result = _run_cli(tmp_path, "--check")

        assert result.returncode == 1
        assert "DOC019" in result.stderr
        assert "Traceback" not in result.stderr

    def test_ordinary_fix_never_performs_the_transition(self, tmp_path: Path):
        """--fix repairs rendering but leaves the definition where it is."""
        _make_corpus(tmp_path)

        result = _run_cli(tmp_path, "--fix")

        assert result.returncode == 1
        assert "DOC019" in result.stderr
        assert (tmp_path / "BATCH22_DEFINITION.md").is_file()
        assert not (tmp_path / ARCHIVED_DEFINITION).exists()

    def test_close_batch_refuses_an_unfinished_work_package(self, tmp_path: Path):
        """An active WP blocks closure, and nothing at all is written."""
        _make_corpus(
            tmp_path,
            **{
                "BATCH22_DEFINITION.md": CORPUS_DEFINITION
                + "\n### WP-3 -- Release checks\n\nStill in progress.\n"
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert "WP-3" in result.stderr
        assert _snapshot(tmp_path) == before

    def test_close_batch_refuses_an_absorbed_wp_without_a_reference(
        self, tmp_path: Path
    ):
        """An absorbed package must name the package that took it on."""
        _make_corpus(
            tmp_path,
            **{
                "BATCH22_DEFINITION.md": CORPUS_DEFINITION.replace(
                    "(ABSORBED INTO WP-1)", "(absorbed into another package)"
                )
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert "WP-2" in result.stderr
        assert _snapshot(tmp_path) == before

    def test_close_batch_refuses_a_disagreeing_dashboard(self, tmp_path: Path):
        """SESSION_CONTEXT Section 1 must agree that the batch is complete."""
        _make_corpus(
            tmp_path,
            **{
                ".claude/SESSION_CONTEXT.md": CORPUS_SESSION.replace(
                    "| Batch 22 status | Complete |",
                    "| Batch 22 status | Active |",
                )
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert "SESSION_CONTEXT.md" in result.stderr
        assert _snapshot(tmp_path) == before

    def test_close_batch_refuses_an_absent_dashboard_row(self, tmp_path: Path):
        """A dashboard that says nothing about the batch is not agreement."""
        _make_corpus(
            tmp_path,
            **{
                ".claude/SESSION_CONTEXT.md": CORPUS_SESSION.replace(
                    "| Batch 22 status | Complete |\n", ""
                )
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert _snapshot(tmp_path) == before

    def test_close_batch_refuses_without_the_playbook_claim(self, tmp_path: Path):
        """The completion claim is author-authored; the tool never writes it."""
        _make_corpus(
            tmp_path,
            **{
                "PLAYBOOK.md": CORPUS_PLAYBOOK.replace(
                    "- **Batch 22 is complete.**",
                    "- Batch 22 is active. Definition: `BATCH22_DEFINITION.md`.",
                )
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert "PLAYBOOK.md" in result.stderr
        assert _snapshot(tmp_path) == before

    def test_close_batch_refuses_a_missing_batch_index_row(self, tmp_path: Path):
        """Without an index row there is no reference to repoint."""
        _make_corpus(
            tmp_path,
            **{
                "PLAYBOOK.md": CORPUS_PLAYBOOK.replace(
                    "| 22 | Enrichment | `BATCH22_DEFINITION.md` | -- |\n", ""
                )
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert _snapshot(tmp_path) == before

    def test_close_batch_refuses_below_the_admission_boundary(self, tmp_path: Path):
        """A grandfathered batch is never closed retroactively by this command."""
        _make_corpus(
            tmp_path,
            **{
                ".docsync.toml": CORPUS_TOML.replace(
                    "admit_from_batch = 22", "admit_from_batch = 30"
                )
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert "boundary" in result.stderr.lower()
        assert _snapshot(tmp_path) == before

    def test_close_batch_refuses_a_contradictory_finding_record(self, tmp_path: Path):
        """A blocked rotation blocks the closure that depends on it."""
        _make_corpus(
            tmp_path,
            **{
                "FINDINGS.md": CORPUS_FINDINGS.replace(
                    "- [ ] **Status:** open",
                    "- [x] **Status:** resolved pending deployment",
                )
            },
        )
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 1
        assert "DOC014" in result.stderr
        assert _snapshot(tmp_path) == before

    def test_close_batch_publishes_the_whole_transition(self, tmp_path: Path):
        """The successful path archives, repoints, rotates and refreshes."""
        _make_corpus(
            tmp_path,
            **{
                "FINDINGS.md": CORPUS_FINDINGS + "\n### F-B22-2: Stale cache key\n\n"
                "- [x] **Status:** resolved\n**Completed:** 2026-09-12\n\n"
                "Fixed in WP-1.\n",
            },
        )

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 0, result.stderr
        archived = (tmp_path / ARCHIVED_DEFINITION).read_text(encoding="utf-8")
        assert "<!-- DOCSYNC:CLOSEOUT -->" in archived
        assert "- Batch 22 closed 2026-09-19" in archived
        assert "- WP-1 complete" in archived
        assert "- WP-2 absorbed into WP-1" in archived
        assert not (tmp_path / "BATCH22_DEFINITION.md").exists()

        playbook = (tmp_path / "PLAYBOOK.md").read_text(encoding="utf-8")
        assert f"`{ARCHIVED_DEFINITION}`" in playbook
        assert "| 22 | Enrichment | `BATCH22_DEFINITION.md` |" not in playbook
        assert "`docs/history/logs/BATCH22_LOG.md`" in playbook

        batch_log = tmp_path / "docs/history/logs/BATCH22_LOG.md"
        assert "Closing work (Batch 22 WP-1)" in batch_log.read_text(encoding="utf-8")

        findings = (tmp_path / "FINDINGS.md").read_text(encoding="utf-8")
        archive = (tmp_path / FINDINGS_ARCHIVE).read_text(encoding="utf-8")
        assert "F-B22-2" not in findings
        assert "F-B22-2" in archive
        assert "Fixed in WP-1." in archive
        assert "F-B22-1" in findings

    def test_closure_then_check_is_clean_and_repeating_it_changes_nothing(
        self, tmp_path: Path
    ):
        """Closure produces a corpus the ordinary gate accepts, and is idempotent."""
        _make_corpus(tmp_path)

        first = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")
        assert first.returncode == 0, first.stderr
        _git(tmp_path, "add", "-A")

        check = _run_cli(tmp_path, "--check")
        assert check.returncode == 0, check.stderr

        after_first = _snapshot(tmp_path)
        again = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")
        assert again.returncode == 0, again.stderr
        assert _snapshot(tmp_path) == after_first

        assert _run_cli(tmp_path, "--fix").returncode == 0
        assert _run_cli(tmp_path, "--check").returncode == 0

    def test_reclosing_without_as_of_keeps_the_recorded_date(self, tmp_path: Path):
        """The clock cannot restate when a closed batch was closed.

        The sibling test above repeats the same --as-of on both runs, so it
        proves idempotence only for the date it supplies. The dangerous path
        is the other one: an operator who re-runs the close without --as-of
        on a later day, whose closure date then comes from today's clock and
        silently overwrites the archived record.
        """
        _make_corpus(tmp_path)
        first = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-10")
        assert first.returncode == 0, first.stderr
        _git(tmp_path, "add", "-A")
        before = _snapshot(tmp_path)

        again = _run_cli(tmp_path, "--close-batch", "22")

        assert again.returncode == 0, again.stderr
        assert "2026-09-10" in again.stderr
        changed = [
            key for key in before if before.get(key) != _snapshot(tmp_path).get(key)
        ]
        assert not changed, f"re-close rewrote {changed}"

    def test_restoring_the_root_definition_cannot_restate_the_closure(
        self, tmp_path: Path
    ):
        """The record is read from the archive, not from the close's source.

        After a close the root definition is gone, so the source resolves to
        the archived copy that carries the record. Restore the root -- from
        history, or from a branch that still has it -- and the source is a
        document with no record at all, which would hand the date back to
        the clock on a batch that was closed months ago.
        """
        _make_corpus(tmp_path)
        root = tmp_path / "BATCH22_DEFINITION.md"
        root_text = root.read_text(encoding="utf-8")
        archived = tmp_path / "docs/history/definitions/BATCH22_DEFINITION.md"

        first = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-10")
        assert first.returncode == 0, first.stderr
        _git(tmp_path, "add", "-A")
        assert "2026-09-10" in archived.read_text(encoding="utf-8")

        root.write_text(root_text, encoding="utf-8")
        _git(tmp_path, "add", "-A")
        again = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-12-25")

        assert again.returncode == 0, again.stderr
        assert "2026-09-10" in archived.read_text(encoding="utf-8")
        assert "2026-12-25" not in archived.read_text(encoding="utf-8")
        assert "2026-09-10" in again.stderr

    def test_opening_another_batch_does_not_mask_an_incomplete_closure(
        self, tmp_path: Path
    ):
        """Starting Batch 23 cannot hide that Batch 22 never finished closing."""
        playbook = CORPUS_PLAYBOOK.replace(
            "- Batch 23 is not yet defined.",
            "- Batch 23 is active. Definition: `BATCH23_DEFINITION.md`.",
        )
        _make_corpus(
            tmp_path,
            **{
                "PLAYBOOK.md": playbook,
                "BATCH23_DEFINITION.md": (
                    "# Batch 23\n\n**Branch:** `feat/batch-23`.\n\n### WP-1 -- Start\n"
                ),
            },
        )

        result = _run_cli(tmp_path, "--check")

        assert result.returncode == 1
        assert "DOC019" in result.stderr

    def test_close_batch_scans_declarations_against_the_candidate_corpus(
        self, tmp_path: Path
    ):
        """A declaration naming the archived path resolves during closure.

        The site does not exist before the move. If the candidate corpus were
        validated from disk rather than from the documents about to be
        published, the closure would refuse on its own pending output.
        """
        declaration = CORPUS_TOML + (
            "\n[[value]]\n"
            'name = "the batch 22 branch"\n'
            "[[value.sites]]\n"
            'file = "AGENTS.md"\n'
            "pattern = '`(feat/batch22-enrichment)`'\n"
            "[[value.sites]]\n"
            f'file = "{ARCHIVED_DEFINITION}"\n'
            "pattern = '`(feat/batch22-enrichment)`'\n"
        )
        _make_corpus(
            tmp_path,
            **{
                ".docsync.toml": declaration,
                "AGENTS.md": (
                    "# AGENTS\n\nSee `FINDINGS.md`.\n\n"
                    "Batch 22 shipped from `feat/batch22-enrichment`.\n"
                ),
            },
        )

        assert "DOC009" in _run_cli(tmp_path, "--check").stderr

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")
        assert result.returncode == 0, result.stderr

        _git(tmp_path, "add", "-A")
        assert _run_cli(tmp_path, "--check").returncode == 0

    def test_close_batch_rejects_a_changed_source_before_publication(
        self, tmp_path: Path
    ):
        """An interrupted publication plus an outside edit refuses to proceed."""
        _make_corpus(tmp_path)
        playbook = tmp_path / "PLAYBOOK.md"
        journal = {
            "version": 1,
            "entries": [{"path": "PLAYBOOK.md", "before": "", "after": "0" * 64}],
        }
        (tmp_path / ".docsync.journal").write_text(
            json.dumps(journal), encoding="utf-8"
        )
        before = playbook.read_bytes()

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 2
        assert "changed outside docsync" in result.stderr
        assert "Traceback" not in result.stderr
        assert playbook.read_bytes() == before
        assert (tmp_path / "BATCH22_DEFINITION.md").is_file()

    def test_close_batch_proves_every_read_source_before_publishing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Every path `_Corpus.__init__` reads is named in `expected`.

        Run in-process because the race it describes cannot be staged from
        outside: the edit has to land between the plan and the write. The spy
        makes that instant reachable and then delegates to the real
        publication, so what is proved is the shipped guard, not a stand-in.

        The assertion is the actual relationship, not a hand-picked subset: a
        prior version of this test asserted only that four names were
        present, which could never fail no matter how much coverage
        regressed elsewhere. Here `Path.read_text` is instrumented for the
        lifetime of `_Corpus.__init__` alone, so `actually_read` is exactly
        the set of files that construction opened -- AGENTS.md,
        HANDOFF_PROMPT.md and AGENT_NOTES.md among them, none of which the
        pre-fix `sources` list here ever named. If a future document is
        added to the corpus but the call site's `expected` is not updated to
        match, `actually_read <= seen["expected"]` fails without anyone
        having to remember to extend an example list.
        """
        _make_corpus(tmp_path)
        monkeypatch.chdir(tmp_path)
        root = tmp_path.resolve()
        real_publish = cli_mod.publish
        real_corpus_init = cli_mod._Corpus.__init__
        real_read_text = Path.read_text
        actually_read: set[Path] = set()
        recording = {"on": False}

        def recording_read_text(self: Path, *args, **kwargs):
            if recording["on"]:
                actually_read.add(self.resolve())
            return real_read_text(self, *args, **kwargs)

        def recording_init(self, store):
            recording["on"] = True
            try:
                real_corpus_init(self, store)
            finally:
                recording["on"] = False

        monkeypatch.setattr(Path, "read_text", recording_read_text)
        monkeypatch.setattr(cli_mod._Corpus, "__init__", recording_init)

        seen: dict[str, set[Path]] = {}

        def spy(pub_root, updates, expected):
            seen["expected"] = {Path(path).resolve() for path in expected}
            (tmp_path / "FINDINGS.md").write_text(
                "# Findings\n\nEdited mid-flight.\n", encoding="utf-8"
            )
            return real_publish(pub_root, updates, expected)

        monkeypatch.setattr(cli_mod, "publish", spy)

        with pytest.raises(SyncError, match="Source changed before publication"):
            cli_mod._close_batch(22, 4, "2026-09-19")

        assert actually_read, "the recording hook on _Corpus.__init__ never fired"
        assert actually_read <= seen["expected"]
        assert {
            root / "AGENTS.md",
            root / "HANDOFF_PROMPT.md",
            root / "AGENT_NOTES.md",
            root / "PLAYBOOK.md",
            root / ".claude" / "SESSION_CONTEXT.md",
            root / "FINDINGS.md",
            root / "BATCH22_DEFINITION.md",
        } <= actually_read
        assert (tmp_path / "BATCH22_DEFINITION.md").is_file()
        assert not (tmp_path / ARCHIVED_DEFINITION).exists()

    def test_close_batch_rejects_a_concurrent_edit_to_a_read_only_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """The review's exact scenario: AGENTS.md edited mid-closure.

        Before the fix, `_close_batch`'s `sources` list named only PLAYBOOK,
        SESSION_CONTEXT, FINDINGS.md, the findings archive, the batch's own
        definition and the side archive's members -- never AGENTS.md,
        HANDOFF_PROMPT.md, AGENT_NOTES.md, another root BATCH*.md file, or an
        archived definition, even though `_Corpus.__init__` reads all of
        them and `collect_integrity_issues` grades the closure candidate
        against that content. An agent editing AGENTS.md while
        `--close-batch` runs went unnoticed, and the closure published a
        decision made about content that no longer matched disk.

        This must fail against the pre-fix code (the publish call succeeds,
        so `pytest.raises` reports "DID NOT RAISE") and pass once AGENTS.md
        is covered by `expected`.
        """
        _make_corpus(tmp_path)
        monkeypatch.chdir(tmp_path)
        real_publish = cli_mod.publish

        def spy(root, updates, expected):
            (tmp_path / "AGENTS.md").write_text(
                "# AGENTS\n\nSee `FINDINGS.md`.\n\nEdited mid-flight.\n",
                encoding="utf-8",
            )
            return real_publish(root, updates, expected)

        monkeypatch.setattr(cli_mod, "publish", spy)

        with pytest.raises(SyncError, match="Source changed before publication"):
            cli_mod._close_batch(22, 4, "2026-09-19")

        # The refusal must have written nothing: the batch definition is
        # still at the root and the archived copy was never created.
        assert (tmp_path / "BATCH22_DEFINITION.md").is_file()
        assert not (tmp_path / ARCHIVED_DEFINITION).exists()

    def test_close_batch_refuses_while_another_writer_holds_the_lock(
        self, tmp_path: Path
    ):
        """Multi-document publication takes the single-writer lock."""
        _make_corpus(tmp_path)
        (tmp_path / ".docsync.lock").write_text("999", encoding="utf-8")
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--close-batch", "22", "--as-of", "2026-09-19")

        assert result.returncode == 2
        assert "docsync writer" in result.stderr
        assert _snapshot(tmp_path) == before

    def test_close_batch_rejects_a_bad_invocation(self, tmp_path: Path):
        """Mode conflicts and malformed dates are invocation errors."""
        _make_corpus(tmp_path)

        assert _run_cli(tmp_path, "--close-batch", "22", "--fix").returncode == 2
        assert (
            _run_cli(
                tmp_path, "--close-batch", "22", "--as-of", "19-09-2026"
            ).returncode
            == 2
        )


class TestOrdinaryMidBatchCompatibility:
    """A mid-batch corpus keeps every documented behaviour it had before."""

    def _mid_batch(self, tmp_path: Path) -> Path:
        playbook = CORPUS_PLAYBOOK.replace(
            "- **Batch 22 is complete.**\n- Batch 23 is not yet defined.",
            "- Batch 21 is complete.\n"
            "- Batch 22 is active. Definition: `BATCH22_DEFINITION.md`.",
        )
        return _make_corpus(
            tmp_path,
            **{
                "PLAYBOOK.md": playbook,
                "BATCH22_DEFINITION.md": CORPUS_DEFINITION
                + "\n### WP-3 -- Release checks\n\nIn progress.\n",
                ".claude/SESSION_CONTEXT.md": CORPUS_SESSION.replace(
                    "| Batch 22 status | Complete |", "| Batch 22 status | Active |"
                ),
            },
        )

    def test_fix_then_check_passes_mid_batch(self, tmp_path: Path):
        """The active-root reminder stays a warning, and the gate passes."""
        self._mid_batch(tmp_path)

        fix = _run_cli(tmp_path, "--fix")
        assert fix.returncode == 0, fix.stderr

        check = _run_cli(tmp_path, "--check")
        assert check.returncode == 0, check.stderr
        assert "WARNING: Root BATCH file detected" in check.stderr
        assert (tmp_path / "BATCH22_DEFINITION.md").is_file()

    def test_repeated_fix_is_idempotent(self, tmp_path: Path):
        """A second --fix writes nothing further."""
        self._mid_batch(tmp_path)
        assert _run_cli(tmp_path, "--fix").returncode == 0
        settled = _snapshot(tmp_path)

        again = _run_cli(tmp_path, "--fix")

        assert again.returncode == 0
        assert _snapshot(tmp_path) == settled


def _dated_archive(count: int, *, year: int) -> str:
    """Render a side-task archive of ``count`` dated entries, newest first."""
    entries = []
    for index in range(count, 0, -1):
        day = f"{index:02d}"
        entries.append(
            f"### {year}-03-{day} - Side task {index}\n\nBody line for entry {index}."
        )
    return "\n".join(SIDE_ARCHIVE_PREFIX) + "\n\n" + "\n\n".join(entries) + "\n"


class TestArchiveMaintenanceModes:
    """Pagination and cold storage are explicit, bounded maintenance runs."""

    def _paginated_corpus(
        self,
        tmp_path: Path,
        *,
        entries: int = 12,
        year: int = 2020,
        **overrides: str,
    ) -> Path:
        return _make_corpus(
            tmp_path,
            **{
                ".docsync.toml": CORPUS_TOML.replace(
                    "max_lines = 500", "max_lines = 24"
                ),
                SIDE_ARCHIVE: _dated_archive(entries, year=year),
                **overrides,
            },
        )

    def test_ordinary_fix_never_paginates_a_legacy_monolith(self, tmp_path: Path):
        """An oversized monolith stays one file until pagination is asked for."""
        self._paginated_corpus(tmp_path)

        _run_cli(tmp_path, "--fix")

        text = (tmp_path / SIDE_ARCHIVE).read_text(encoding="utf-8")
        assert INDEX_START_MARKER not in text
        assert not (tmp_path / "docs/logarchive" / HOT_DIRECTORY).exists()

    def test_paginate_migrates_and_preserves_every_entry(self, tmp_path: Path):
        """Migration turns the entry point into an index without losing entries."""
        self._paginated_corpus(tmp_path)

        result = _run_cli(tmp_path, "--paginate-archives")

        assert result.returncode == 0, result.stderr
        index_text = (tmp_path / SIDE_ARCHIVE).read_text(encoding="utf-8")
        assert INDEX_START_MARKER in index_text
        pages = sorted((tmp_path / "docs/logarchive" / HOT_DIRECTORY).glob("*.md"))
        assert len(pages) > 1
        body = "".join(page.read_text(encoding="utf-8") for page in pages)
        for number in range(1, 13):
            assert f"Side task {number}\n" in body

    def test_paginate_is_idempotent(self, tmp_path: Path):
        """A second migration run produces no further writes."""
        self._paginated_corpus(tmp_path)
        assert _run_cli(tmp_path, "--paginate-archives").returncode == 0
        settled = _snapshot(tmp_path)

        again = _run_cli(tmp_path, "--paginate-archives")

        assert again.returncode == 0
        assert _snapshot(tmp_path) == settled

    def test_cold_storage_requires_an_explicit_as_of_date(self, tmp_path: Path):
        """Ordinary maintenance never ages history from the wall clock."""
        self._paginated_corpus(tmp_path)
        _run_cli(tmp_path, "--paginate-archives")
        before = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--cold-storage")

        assert result.returncode == 2
        assert "--as-of" in result.stderr
        assert _snapshot(tmp_path) == before

    def test_as_of_without_a_maintenance_mode_is_an_invocation_error(
        self, tmp_path: Path
    ):
        """An as-of date only means something to a mode that ages or records."""
        _make_corpus(tmp_path)

        result = _run_cli(tmp_path, "--check", "--as-of", "2026-09-19")

        assert result.returncode == 2

    def test_check_writes_nothing_against_a_paginated_corpus(self, tmp_path: Path):
        """Reading flattened history stays a read, pages and all."""
        self._paginated_corpus(tmp_path)
        assert _run_cli(tmp_path, "--paginate-archives").returncode == 0
        _git(tmp_path, "add", "-A")
        settled = _snapshot(tmp_path)

        _run_cli(tmp_path, "--check")

        assert _snapshot(tmp_path) == settled

    def test_an_indexed_archive_stays_indexed_when_an_entry_arrives(
        self, tmp_path: Path
    ):
        """A rotation into a paginated archive appends to a page, not the index."""
        self._paginated_corpus(
            tmp_path,
            **{
                "PLAYBOOK.md": CORPUS_PLAYBOOK.replace(
                    "- **Batch 22 is complete.**\n- Batch 23 is not yet defined.",
                    "- Batch 21 is complete.\n"
                    "- Batch 22 is active. Definition: `BATCH22_DEFINITION.md`.",
                ),
                ".claude/SESSION_CONTEXT.md": CORPUS_SESSION.replace(
                    "| Batch 22 status | Complete |", "| Batch 22 status | Active |"
                ),
            },
        )
        assert _run_cli(tmp_path, "--paginate-archives").returncode == 0
        playbook = (tmp_path / "PLAYBOOK.md").read_text(encoding="utf-8")
        _write(
            tmp_path,
            "PLAYBOOK.md",
            playbook + "\n### 2026-09-12 - Late side task\n\nAn untagged rotation.\n",
        )
        _git(tmp_path, "add", "-A")

        result = _run_cli(tmp_path, "--fix", "--keep-non-current", "0")

        assert result.returncode == 0, result.stderr
        index_text = (tmp_path / SIDE_ARCHIVE).read_text(encoding="utf-8")
        assert INDEX_START_MARKER in index_text
        assert "Late side task" not in index_text
        pages = sorted((tmp_path / "docs/logarchive" / HOT_DIRECTORY).glob("*.md"))
        body = "".join(page.read_text(encoding="utf-8") for page in pages)
        assert "Late side task" in body

    def test_cold_storage_moves_only_finalized_fully_aged_pages(self, tmp_path: Path):
        """A wholly old finalized page moves; the writable tail stays hot."""
        self._paginated_corpus(tmp_path)
        assert _run_cli(tmp_path, "--paginate-archives").returncode == 0

        result = _run_cli(tmp_path, "--cold-storage", "--as-of", "2026-09-19")

        assert result.returncode == 0, result.stderr
        cold = sorted((tmp_path / "docs/logarchive" / COLD_DIRECTORY).glob("*.md"))
        hot = sorted((tmp_path / "docs/logarchive" / HOT_DIRECTORY).glob("*.md"))
        assert cold, "no finalized page aged into cold storage"
        assert hot, "the writable tail must stay hot"
        index_text = (tmp_path / SIDE_ARCHIVE).read_text(encoding="utf-8")
        assert f"{COLD_DIRECTORY}/{cold[0].name}" in index_text

    def test_recent_history_never_ages(self, tmp_path: Path):
        """An as-of date inside the retention window moves nothing."""
        self._paginated_corpus(tmp_path, year=2026)
        assert _run_cli(tmp_path, "--paginate-archives").returncode == 0
        settled = _snapshot(tmp_path)

        result = _run_cli(tmp_path, "--cold-storage", "--as-of", "2026-09-19")

        assert result.returncode == 0
        assert _snapshot(tmp_path) == settled

    def test_latest_count_authority_survives_pagination_and_cold_moves(
        self, tmp_path: Path
    ):
        """Retention and layout must never decide which test count is current.

        The authoritative count sits in the oldest entry of a corpus large
        enough to paginate, so it lands on a page that cold storage then
        moves. A reader that stopped at the index, or at the hot pages, would
        report a different number after each maintenance run.
        """
        archive = _dated_archive(12, year=2020).replace(
            "Body line for entry 1.",
            "Ran `pytest -q`: **777 passed**.",
        )
        session = CORPUS_SESSION.replace(
            "| Batch 22 status | Complete |",
            "| Batch 22 status | Active |\n| Tests | **777 tests passing** |",
        )
        # Mid-batch on purpose: this test is about archive layout deciding a
        # count, and a claimed-complete batch would raise close-out
        # diagnostics that have nothing to do with the question.
        playbook = CORPUS_PLAYBOOK.replace(
            "Ran `pytest -q` -- **1234 passed**.", "Reviewed the enrichment work."
        ).replace(
            "- **Batch 22 is complete.**\n- Batch 23 is not yet defined.",
            "- Batch 21 is complete.\n"
            "- Batch 22 is active. Definition: `BATCH22_DEFINITION.md`.",
        )
        _make_corpus(
            tmp_path,
            **{
                ".docsync.toml": CORPUS_TOML.replace(
                    "max_lines = 500", "max_lines = 24"
                ),
                SIDE_ARCHIVE: archive,
                ".claude/SESSION_CONTEXT.md": session,
                "PLAYBOOK.md": playbook,
            },
        )
        _run_cli(tmp_path, "--fix")
        _git(tmp_path, "add", "-A")
        baseline = _run_cli(tmp_path, "--check")
        assert baseline.returncode == 0, baseline.stderr

        assert _run_cli(tmp_path, "--paginate-archives").returncode == 0
        _git(tmp_path, "add", "-A")
        after_pagination = _run_cli(tmp_path, "--check")
        assert after_pagination.returncode == 0, after_pagination.stderr

        cold = _run_cli(tmp_path, "--cold-storage", "--as-of", "2026-09-19")
        assert cold.returncode == 0, cold.stderr
        _git(tmp_path, "add", "-A")
        after_cold = _run_cli(tmp_path, "--check")
        assert after_cold.returncode == 0, after_cold.stderr
        session_text = (tmp_path / ".claude/SESSION_CONTEXT.md").read_text(
            encoding="utf-8"
        )
        assert "**777 tests passing**" in session_text


class TestArchiveStructureDiagnostics:
    """DOC020 reports a broken archive layout as a diagnostic, not a crash."""

    def test_missing_indexed_page_reports_doc020(self, tmp_path: Path):
        """Deleting a page an index names is an error the gate explains."""
        _make_corpus(
            tmp_path,
            **{
                ".docsync.toml": CORPUS_TOML.replace(
                    "max_lines = 500", "max_lines = 24"
                ),
                SIDE_ARCHIVE: _dated_archive(12, year=2020),
            },
        )
        assert _run_cli(tmp_path, "--paginate-archives").returncode == 0
        pages = sorted((tmp_path / "docs/logarchive" / HOT_DIRECTORY).glob("*.md"))
        pages[0].unlink()

        result = _run_cli(tmp_path, "--check")

        assert result.returncode == 1
        assert "ERROR DOC020" in result.stderr
        assert "Traceback" not in result.stderr

    def test_unreferenced_managed_page_reports_doc020(self, tmp_path: Path):
        """A page no index names is unreachable history, not a stray file."""
        _make_corpus(tmp_path)
        orphan = (
            tmp_path
            / "docs/history/findings"
            / HOT_DIRECTORY
            / "FINDINGS_ARCHIVE_0001.md"
        )
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("stray\n", encoding="utf-8")

        result = _run_cli(tmp_path, "--check")

        assert result.returncode == 1
        assert "ERROR DOC020" in result.stderr
        assert "Traceback" not in result.stderr


class TestFindingRotationThroughTheCli:
    """Rotation is planned by --check and published by --fix."""

    def _active_batch_corpus(self, tmp_path: Path, findings: str) -> Path:
        return _make_corpus(
            tmp_path,
            **{
                "PLAYBOOK.md": CORPUS_PLAYBOOK.replace(
                    "- **Batch 22 is complete.**\n- Batch 23 is not yet defined.",
                    "- Batch 21 is complete.\n"
                    "- Batch 22 is active. Definition: `BATCH22_DEFINITION.md`.",
                ),
                ".claude/SESSION_CONTEXT.md": CORPUS_SESSION.replace(
                    "| Batch 22 status | Complete |", "| Batch 22 status | Active |"
                ),
                "FINDINGS.md": findings,
            },
        )

    def test_check_reports_an_eligible_finding_that_is_still_active(
        self, tmp_path: Path
    ):
        """An archive-eligible finding left in the active file is drift."""
        self._active_batch_corpus(
            tmp_path,
            CORPUS_FINDINGS + "\n### F-B22-3: Duplicate cache write\n\n"
            "- [x] **Status:** resolved\n**Completed:** 2026-09-11\n\n"
            "Removed the duplicate write.\n",
        )

        result = _run_cli(tmp_path, "--check")

        assert result.returncode == 1
        assert "FINDINGS.md" in result.stdout

    def test_fix_rotates_an_eligible_finding(self, tmp_path: Path):
        """--fix publishes the rotation and preserves the whole body."""
        self._active_batch_corpus(
            tmp_path,
            CORPUS_FINDINGS + "\n### F-B22-3: Duplicate cache write\n\n"
            "- [x] **Status:** resolved\n**Completed:** 2026-09-11\n\n"
            "Removed the duplicate write.\n",
        )

        result = _run_cli(tmp_path, "--fix")

        assert result.returncode == 0, result.stderr
        findings = (tmp_path / "FINDINGS.md").read_text(encoding="utf-8")
        archive = (tmp_path / FINDINGS_ARCHIVE).read_text(encoding="utf-8")
        assert "F-B22-3" not in findings
        assert "F-B22-3: Duplicate cache write -- RESOLVED" in archive
        assert "Removed the duplicate write." in archive

    def test_check_reports_a_duplicate_archived_id(self, tmp_path: Path):
        """DOC018 reaches the gate's normal output through the CLI."""
        _make_corpus(
            tmp_path,
            **{
                FINDINGS_ARCHIVE: CORPUS_FINDINGS_ARCHIVE
                + "\n### F-OLD-1: First -- RESOLVED\n\nOne.\n"
                "\n### F-OLD-1: Second -- RESOLVED\n\nTwo.\n",
            },
        )

        result = _run_cli(tmp_path, "--check")

        assert result.returncode == 1
        assert "DOC018" in result.stderr
