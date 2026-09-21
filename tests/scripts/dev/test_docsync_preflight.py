"""Tests for scripts/dev/docsync_preflight.py.

Two kinds of test double are used deliberately. Most of the Git-plumbing
unit tests inject a fake ``runner`` (a ``subprocess.run``-shaped callable) so
a single wrong argument or a tool failure can be asserted precisely without
touching a real repository. The staged/unstaged, deleted/renamed, and
unresolved-conflict tests instead drive a *real* temporary Git repository
(via the real ``subprocess.run``): those behaviours -- what Git's index
actually contains, how a rename looks in ``git diff --cached``, what an
unmerged stage looks like -- are exactly what a fake would have to
reimplement to be worth trusting, so they are proven against real Git
instead.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.dev import docsync_preflight as preflight

# --------------------------------------------------------------------- #
# Real-Git helpers                                                        #
# --------------------------------------------------------------------- #


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed in {cwd}: {result.stderr}"
    )
    return result


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "test@example.invalid")
    _git(path, "config", "user.name", "Test")
    return path


FAKE_CHECKER = textwrap.dedent(
    """\
    import sys
    from pathlib import Path

    marker = Path("marker.txt")
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != "GOOD":
        print("BAD content detected", file=sys.stderr)
        sys.exit(1)
    print("checker: OK")
    sys.exit(0)
    """
)


@pytest.fixture
def fake_entry_point(tmp_path_factory) -> Path:
    """A tiny stand-in for scripts/doc_state_sync.py's ``--check`` contract.

    It exits 0 only when ``marker.txt`` in its cwd reads exactly ``GOOD``,
    so tests can control pass/fail by writing that one file into whatever
    directory the preflight ends up pointing the checker at.
    """
    directory = tmp_path_factory.mktemp("fake-entry")
    script = directory / "fake_checker.py"
    script.write_text(FAKE_CHECKER, encoding="utf-8")
    return script


# --------------------------------------------------------------------- #
# Fake-runner unit tests                                                  #
# --------------------------------------------------------------------- #


def _responses(table):
    """Build a fake runner keyed by the Git subcommand tuple after argv[0]."""

    def fake_run(command, **kwargs):
        key = tuple(command[1:])
        if key not in table:
            raise AssertionError(f"unexpected git invocation: {command}")
        returncode, stdout, stderr = table[key]
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    return fake_run


def test_repo_root_wraps_git_failure():
    """A non-repository ``cwd`` raises PreflightError, not a bare CalledProcessError."""
    runner = _responses(
        {("rev-parse", "--show-toplevel"): (128, "", "fatal: not a git repository")}
    )
    with pytest.raises(preflight.PreflightError, match="not a git repository"):
        preflight.repo_root(Path("/nonexistent"), runner=runner)


def test_primary_checkout_root_takes_common_dir_parent():
    """The primary checkout is the common Git directory's parent, always."""
    runner = _responses(
        {
            (
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ): (0, "/primary/.git\n", "")
        }
    )
    assert preflight.primary_checkout_root(
        Path("/linked/worktree"), runner=runner
    ) == Path("/primary")


def test_unresolved_paths_deduplicates_multi_stage_entries():
    """Each conflicted path appears once even though Git lists 2-3 stages."""
    record = (
        "100644 aaa 1\tconflict.md\0"
        "100644 bbb 2\tconflict.md\0"
        "100644 ccc 3\tconflict.md\0"
    )
    runner = _responses({("ls-files", "-u", "-z"): (0, record, "")})
    assert preflight.unresolved_paths(Path("/repo"), runner=runner) == ["conflict.md"]


def test_staged_paths_expands_rename_to_both_names():
    """A rename contributes its old and new path, not just the destination."""
    record = "R100\0old/name.py\0new/name.py\0M\0other.md\0"
    runner = _responses(
        {("diff", "--cached", "--name-status", "-M", "-z"): (0, record, "")}
    )
    assert preflight.staged_paths(Path("/repo"), runner=runner) == [
        "old/name.py",
        "new/name.py",
        "other.md",
    ]


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("scripts/docsync/integrity.py", True),
        ("scripts/docsync/sub/deep.py", True),
        ("scripts/doc_state_sync.py", True),
        ("scripts/dev/docsync_preflight.py", True),
        (".docsync.toml", True),
        ("AGENTS.md", False),
        ("scripts/dev/other_tool.py", False),
        ("docs/docsync/not_code.md", False),
        # Exact-match cases for file entries: a longer filename that merely
        # starts with a control-plane file's name must not match. Directory
        # entries (scripts/docsync/) still match by prefix, since a nested
        # file's exact name cannot be enumerated in advance.
        (".docsync.tomlx", False),
        ("scripts/doc_state_sync.py.bak", False),
        ("scripts/dev/docsync_preflight.py2", False),
    ],
)
def test_control_plane_prefix_matching(path, expected):
    """Only the checker's own code and its config are treated as control-plane."""
    record = f"M\0{path}\0"
    runner = _responses(
        {("diff", "--cached", "--name-status", "-M", "-z"): (0, record, "")}
    )
    result = preflight.staged_control_plane_paths(Path("/repo"), runner=runner)
    assert (path in result) is expected


def test_require_python_fails_closed_when_missing(tmp_path):
    """No fallback to PATH: a missing qualified venv is a hard precondition failure."""
    with pytest.raises(preflight.PreflightError, match="qualified Python"):
        preflight.require_python(tmp_path, os_name="nt", access=lambda *a: True)


def test_require_python_returns_qualified_path_when_runnable(tmp_path):
    python_path = tmp_path / ".venv" / "Scripts" / "python.exe"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("", encoding="utf-8")
    resolved = preflight.require_python(tmp_path, os_name="nt", access=lambda *a: True)
    assert resolved == python_path


def test_resolve_worktree_python_falls_back_to_current_interpreter(tmp_path):
    """CI has no .venv; the running interpreter is used instead, never PATH lookup."""
    resolved = preflight.resolve_worktree_python(
        tmp_path, os_name="nt", access=lambda *a: True, sys_executable="/ci/python"
    )
    assert resolved == Path("/ci/python")


def test_resolve_worktree_python_prefers_qualified_venv_when_present(tmp_path):
    python_path = tmp_path / ".venv" / "Scripts" / "python.exe"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("", encoding="utf-8")
    resolved = preflight.resolve_worktree_python(
        tmp_path, os_name="nt", access=lambda *a: True, sys_executable="/ci/python"
    )
    assert resolved == python_path


@pytest.mark.parametrize(
    "failing_step",
    ["write-tree", "archive", "init", "add"],
)
def test_candidate_corpus_tool_failure_raises(failing_step, tmp_path):
    """Any Git step failing while building the candidate raises, not silently continues."""

    def fake_run(command, **kwargs):
        if command[1] == "write-tree":
            if failing_step == "write-tree":
                return subprocess.CompletedProcess(command, 128, "", "boom write-tree")
            return subprocess.CompletedProcess(command, 0, "deadbeef\n", "")
        if command[1] == "archive":
            if failing_step == "archive":
                return subprocess.CompletedProcess(command, 128, b"", b"boom archive")
            # Minimal valid empty tar stream.
            import io
            import tarfile

            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w"):
                pass
            return subprocess.CompletedProcess(command, 0, buffer.getvalue(), b"")
        if command[1] == "init":
            if failing_step == "init":
                return subprocess.CompletedProcess(command, 1, "", "boom init")
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1] == "add":
            if failing_step == "add":
                return subprocess.CompletedProcess(command, 1, "", "boom add")
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(f"unexpected command {command}")

    with pytest.raises(preflight.PreflightError, match=f"boom {failing_step}"):
        with preflight.candidate_corpus(tmp_path, runner=fake_run):
            pass  # pragma: no cover - must raise before yielding on failure


def test_run_docsync_check_returns_actual_exit_code(fake_entry_point, tmp_path):
    """The checker's own exit code passes through unmodified, not collapsed."""
    (tmp_path / "marker.txt").write_text("BAD", encoding="utf-8")
    returncode, _out, err = preflight.run_docsync_check(
        Path(sys.executable), fake_entry_point, cwd=tmp_path
    )
    assert returncode == 1
    assert "BAD content detected" in err

    (tmp_path / "marker.txt").write_text("GOOD", encoding="utf-8")
    returncode, out, _err = preflight.run_docsync_check(
        Path(sys.executable), fake_entry_point, cwd=tmp_path
    )
    assert returncode == 0
    assert "checker: OK" in out


# --------------------------------------------------------------------- #
# Real-Git integration tests                                             #
# --------------------------------------------------------------------- #


def test_staged_good_unstaged_bad_passes(tmp_path, fake_entry_point, capsys):
    """A document good in the index but bad on disk must still pass."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")
    _git(repo, "add", "marker.txt")
    # Working tree now disagrees with what is staged.
    (repo / "marker.txt").write_text("BAD", encoding="utf-8")

    code = preflight.run_staged(
        repo, python_exe=Path(sys.executable), entry_point=fake_entry_point
    )
    assert code == 0
    assert "checker: OK" in capsys.readouterr().out


def test_staged_bad_unstaged_good_fails(tmp_path, fake_entry_point, capsys):
    """A document bad in the index but good on disk must still fail."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "marker.txt").write_text("BAD", encoding="utf-8")
    _git(repo, "add", "marker.txt")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")

    code = preflight.run_staged(
        repo, python_exe=Path(sys.executable), entry_point=fake_entry_point
    )
    assert code == 1
    assert "BAD content detected" in capsys.readouterr().err


def test_deleted_path_absent_from_candidate(tmp_path, fake_entry_point):
    """A file removed from the index must not appear in the candidate corpus."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")
    (repo / "doomed.md").write_text("will be deleted", encoding="utf-8")
    _git(repo, "add", "marker.txt", "doomed.md")
    _git(repo, "commit", "-q", "-m", "initial")
    _git(repo, "rm", "-q", "doomed.md")

    seen = {}

    def spying_runner(command, **kwargs):
        result = subprocess.run(command, **kwargs)
        return result

    with preflight.candidate_corpus(repo) as candidate:
        seen["files"] = sorted(p.name for p in candidate.iterdir() if p.is_file())

    assert "doomed.md" not in seen["files"]
    assert "marker.txt" in seen["files"]


def test_renamed_path_reflected_in_candidate(tmp_path):
    """A rename staged in the index shows the new name, never the old one."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "old_name.md").write_text("content", encoding="utf-8")
    _git(repo, "add", "old_name.md")
    _git(repo, "commit", "-q", "-m", "initial")
    _git(repo, "mv", "old_name.md", "new_name.md")

    with preflight.candidate_corpus(repo) as candidate:
        names = sorted(p.name for p in candidate.iterdir() if p.is_file())

    assert "new_name.md" in names
    assert "old_name.md" not in names


def test_candidate_corpus_cleans_up_after_use(tmp_path):
    """The temporary directory is gone once the context manager exits."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")
    _git(repo, "add", "marker.txt")

    with preflight.candidate_corpus(repo) as candidate:
        recorded = candidate
        assert recorded.is_dir()
    assert not recorded.exists()


def test_candidate_corpus_cleans_up_after_failure_inside_the_with_block(tmp_path):
    """Cleanup still happens when the caller's own code raises inside the block."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")
    _git(repo, "add", "marker.txt")

    recorded = None
    with pytest.raises(ValueError, match="caller failure"):
        with preflight.candidate_corpus(repo) as candidate:
            recorded = candidate
            raise ValueError("caller failure")
    assert recorded is not None
    assert not recorded.exists()


def test_unresolved_merge_conflict_rejected_before_building_candidate(
    tmp_path, fake_entry_point, capsys
):
    """A real unmerged index is refused before any tree/archive work happens."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "file.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "file.txt")
    _git(repo, "commit", "-q", "-m", "base")

    _git(repo, "checkout", "-q", "-b", "branch-a")
    (repo / "file.txt").write_text("branch-a\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "a")

    _git(repo, "checkout", "-q", "-b", "branch-b", "master")
    (repo / "file.txt").write_text("branch-b\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "b")

    subprocess.run(
        ["git", "merge", "-q", "branch-a"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )  # Expected to conflict; do not assert its own (nonzero) exit here.

    code = preflight.run_staged(
        repo, python_exe=Path(sys.executable), entry_point=fake_entry_point
    )
    assert code == preflight.EXIT_PRECONDITION_ERROR
    err = capsys.readouterr().err
    assert "unresolved merge-conflict" in err
    assert "file.txt" in err


def test_control_plane_change_rejected_before_building_candidate(tmp_path, capsys):
    """Staging scripts/docsync/ code refuses before any tree/archive work runs."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "scripts" / "docsync").mkdir(parents=True)
    (repo / "scripts" / "docsync" / "integrity.py").write_text(
        "# v1\n", encoding="utf-8"
    )
    _git(repo, "add", "scripts/docsync/integrity.py")
    _git(repo, "commit", "-q", "-m", "initial")
    (repo / "scripts" / "docsync" / "integrity.py").write_text(
        "# v2\n", encoding="utf-8"
    )
    _git(repo, "add", "scripts/docsync/integrity.py")

    calls = []

    def spying_runner(command, **kwargs):
        calls.append(tuple(command))
        return subprocess.run(command, **kwargs)

    code = preflight.run_staged(repo, runner=spying_runner)
    assert code == preflight.EXIT_CONTROL_PLANE_REJECTED
    err = capsys.readouterr().err
    assert "scripts/docsync/integrity.py" in err
    # The owner ruling forbids --no-verify absolutely (AGENTS.md anti-pattern
    # 7 / CLAUDE.md); the one named escape is pre-commit's own SKIP, which
    # skips only this hook by id and still runs every other check.
    assert "SKIP=doc-state-sync-check" in err
    assert "--no-verify" not in err
    assert not any(call[1] == "write-tree" for call in calls)
    assert not any(call[1] == "archive" for call in calls)


def test_run_worktree_uses_current_checkout_directly(
    tmp_path, fake_entry_point, capsys
):
    """--worktree mode runs the checker against cwd with no candidate build."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")

    code = preflight.run_worktree(
        repo, python_exe=Path(sys.executable), entry_point=fake_entry_point
    )
    assert code == 0
    assert "checker: OK" in capsys.readouterr().out


def test_run_worktree_reports_precondition_failure(tmp_path, capsys):
    """A worktree-mode Git failure fails closed with EXIT_PRECONDITION_ERROR."""

    def failing_runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 128, "", "fatal: no such repo")

    code = preflight.run_worktree(tmp_path, runner=failing_runner)
    assert code == preflight.EXIT_PRECONDITION_ERROR
    assert "fatal: no such repo" in capsys.readouterr().err


def test_run_worktree_rejects_staged_control_plane_changes(tmp_path, capsys):
    """--worktree must guard too: pre-commit's stash isolation means the
    on-disk tree already *is* the staged content whenever the raw wrapper
    is not the active mechanism, so this is the default local commit path
    in that configuration, not just the CI path. A commit staging changes
    to scripts/docsync/* must be refused here exactly as it is under
    --staged, before the checker itself is ever invoked.
    """
    repo = _init_repo(tmp_path / "repo")
    (repo / "scripts" / "docsync").mkdir(parents=True)
    (repo / "scripts" / "docsync" / "integrity.py").write_text(
        "# v1\n", encoding="utf-8"
    )
    _git(repo, "add", "scripts/docsync/integrity.py")
    _git(repo, "commit", "-q", "-m", "initial")
    (repo / "scripts" / "docsync" / "integrity.py").write_text(
        "# v2\n", encoding="utf-8"
    )
    _git(repo, "add", "scripts/docsync/integrity.py")

    calls = []

    def spying_runner(command, **kwargs):
        calls.append(tuple(command))
        return subprocess.run(command, **kwargs)

    code = preflight.run_worktree(repo, runner=spying_runner)
    assert code == preflight.EXIT_CONTROL_PLANE_REJECTED
    err = capsys.readouterr().err
    assert "scripts/docsync/integrity.py" in err
    assert "SKIP=doc-state-sync-check" in err
    assert "--no-verify" not in err
    # The checker itself (a non-git command) must never have been invoked.
    assert not any(call[0] != "git" for call in calls)


def test_run_worktree_does_not_reject_when_control_plane_change_is_already_committed(
    tmp_path, fake_entry_point
):
    """The CI case: nothing is staged (index == HEAD), even though the most
    recent commit changed control-plane code relative to its parent. `git
    diff --cached` is empty here, so the guard is a correct no-op -- no
    separate CI-vs-local branch is needed in the implementation.
    """
    repo = _init_repo(tmp_path / "repo")
    (repo / "scripts" / "docsync").mkdir(parents=True)
    (repo / "scripts" / "docsync" / "integrity.py").write_text(
        "# v1\n", encoding="utf-8"
    )
    _git(repo, "add", "scripts/docsync/integrity.py")
    _git(repo, "commit", "-q", "-m", "initial")
    (repo / "scripts" / "docsync" / "integrity.py").write_text(
        "# v2\n", encoding="utf-8"
    )
    _git(repo, "add", "scripts/docsync/integrity.py")
    _git(repo, "commit", "-q", "-m", "control-plane change now in HEAD")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")

    code = preflight.run_worktree(
        repo, python_exe=Path(sys.executable), entry_point=fake_entry_point
    )
    assert code == 0


def test_run_docsync_check_maps_missing_executable_to_preflight_error(tmp_path):
    """A FileNotFoundError raised by the subprocess call itself (the
    interpreter or entry point vanished between resolution and invocation)
    must become a PreflightError, not an uncaught traceback.
    """

    def raising_runner(command, **kwargs):
        raise FileNotFoundError("no such file or directory")

    with pytest.raises(preflight.PreflightError, match="no such file or directory"):
        preflight.run_docsync_check(
            Path("/missing/python"),
            Path("/missing/entry.py"),
            cwd=tmp_path,
            runner=raising_runner,
        )


def test_run_staged_maps_invocation_oserror_to_precondition_error(
    tmp_path, fake_entry_point
):
    """End-to-end (real subprocess, no mock): a python_exe that does not
    exist at invocation time must fail closed with EXIT_PRECONDITION_ERROR,
    not crash with an unhandled FileNotFoundError traceback.
    """
    repo = _init_repo(tmp_path / "repo")
    (repo / "marker.txt").write_text("GOOD", encoding="utf-8")
    _git(repo, "add", "marker.txt")
    missing_python = tmp_path / "does-not-exist" / "python.exe"

    code = preflight.run_staged(
        repo, python_exe=missing_python, entry_point=fake_entry_point
    )
    assert code == preflight.EXIT_PRECONDITION_ERROR


# --------------------------------------------------------------------- #
# CLI wiring                                                              #
# --------------------------------------------------------------------- #


def test_main_requires_exactly_one_mode(capsys):
    with pytest.raises(SystemExit):
        preflight.main([])
    with pytest.raises(SystemExit):
        preflight.main(["--staged", "--worktree"])


def test_main_dispatches_to_run_staged(monkeypatch, tmp_path):
    called = {}

    def fake_run_staged(cwd, **kwargs):
        called["cwd"] = cwd
        return 0

    monkeypatch.setattr(preflight, "run_staged", fake_run_staged)
    monkeypatch.chdir(tmp_path)
    assert preflight.main(["--staged"]) == 0
    assert called["cwd"] == tmp_path


def test_main_dispatches_to_run_worktree(monkeypatch, tmp_path):
    called = {}

    def fake_run_worktree(cwd, **kwargs):
        called["cwd"] = cwd
        return 0

    monkeypatch.setattr(preflight, "run_worktree", fake_run_worktree)
    monkeypatch.chdir(tmp_path)
    assert preflight.main(["--worktree"]) == 0
    assert called["cwd"] == tmp_path


# --------------------------------------------------------------------- #
# Genuine end-to-end test against the real docsync checker                #
# --------------------------------------------------------------------- #


def test_staged_preflight_against_real_docsync_checker(tmp_path):
    """The real scripts/doc_state_sync.py, run through the candidate corpus,
    catches a staged PLAYBOOK.md that drops a required section even though
    the working tree still has a valid copy on disk.

    This is the load-bearing proof for the whole module: every other test
    uses a fake entry point so failures are attributable to this module's
    own logic, but a fake checker could not tell us the *real* checker
    actually runs correctly against a materialized index snapshot.
    """
    real_repo_root = preflight.REPOSITORY_ROOT
    real_entry_point = real_repo_root / preflight.DOCSYNC_ENTRY_POINT
    assert real_entry_point.is_file()

    repo = _init_repo(tmp_path / "repo")
    (repo / "docs" / "logarchive").mkdir(parents=True)
    (repo / "docs" / "history" / "logs").mkdir(parents=True)
    (repo / ".claude").mkdir(parents=True)

    from tests.conftest import (
        MINIMAL_ARCHIVE,
        MINIMAL_PLAYBOOK,
        MINIMAL_SESSION_CONTEXT,
    )

    good_playbook = MINIMAL_PLAYBOOK
    broken_playbook = "# PLAYBOOK\n\nThis document is missing every required section.\n"

    (repo / "PLAYBOOK.md").write_text(good_playbook, encoding="utf-8")
    (repo / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md").write_text(
        MINIMAL_ARCHIVE, encoding="utf-8"
    )
    (repo / ".claude" / "SESSION_CONTEXT.md").write_text(
        MINIMAL_SESSION_CONTEXT, encoding="utf-8"
    )
    (repo / ".docsync.toml").write_text(
        "[closeout]\nadmit_from_batch = 22\n", encoding="utf-8"
    )
    (repo / "BATCH11_DEFINITION.md").write_text(
        "# BATCH11\n\n**Branch:** `wip/batch-11`.\n", encoding="utf-8"
    )
    (repo / "AGENTS.md").write_text("See `FINDINGS.md`.\n", encoding="utf-8")
    (repo / "HANDOFF_PROMPT.md").write_text("Read `AGENTS.md`.\n", encoding="utf-8")
    (repo / "AGENT_NOTES.md").write_text(
        "Rules live in `AGENTS.md`.\n", encoding="utf-8"
    )
    (repo / "FINDINGS.md").write_text("# Findings\n", encoding="utf-8")

    _git(
        repo,
        "add",
        "PLAYBOOK.md",
        "docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md",
        ".claude/SESSION_CONTEXT.md",
        ".docsync.toml",
        "BATCH11_DEFINITION.md",
        "AGENTS.md",
        "HANDOFF_PROMPT.md",
        "AGENT_NOTES.md",
        "FINDINGS.md",
    )
    _git(repo, "commit", "-q", "-m", "initial good state")

    # MINIMAL_SESSION_CONTEXT's placeholder status block is deliberately
    # stale (tests/conftest.py's sync_env fixture relies on this too): a
    # real --fix run computes the managed block this exact PLAYBOOK.md
    # renders, which is the only self-consistent "good" state --check can
    # ever accept. Do that once, for real, before using this corpus as the
    # good/broken baseline below.
    fix_result = subprocess.run(
        [sys.executable, str(real_entry_point), "--fix"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert fix_result.returncode == 0, fix_result.stdout + fix_result.stderr
    good_playbook = (repo / "PLAYBOOK.md").read_text(encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "post-fix good state")

    # Confirm the good corpus actually passes before using it as a baseline,
    # so a later failure is attributable to the broken/good swap below and
    # not to this fixture corpus being wrong in the first place.
    baseline = preflight.run_staged(
        repo, python_exe=Path(sys.executable), entry_point=real_entry_point
    )
    assert baseline == 0

    # Stage a broken PLAYBOOK.md, but leave a *valid* copy on disk. A
    # worktree-only check would see the good copy and pass; the staged
    # preflight must see the broken one instead.
    (repo / "PLAYBOOK.md").write_text(broken_playbook, encoding="utf-8")
    _git(repo, "add", "PLAYBOOK.md")
    (repo / "PLAYBOOK.md").write_text(good_playbook, encoding="utf-8")

    code = preflight.run_staged(
        repo, python_exe=Path(sys.executable), entry_point=real_entry_point
    )
    assert code != 0

    # Reverse: staged copy is good, working tree is broken. The commit
    # candidate must still pass.
    _git(repo, "add", "PLAYBOOK.md")  # re-stage the good on-disk copy
    (repo / "PLAYBOOK.md").write_text(broken_playbook, encoding="utf-8")

    code = preflight.run_staged(
        repo, python_exe=Path(sys.executable), entry_point=real_entry_point
    )
    assert code == 0
