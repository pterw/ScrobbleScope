"""Behavior tests for primary-checkout virtualenv resolution."""

import os
from pathlib import Path

import pytest

from scripts.dev.worktree_guard import VenvPaths, resolve_venv
from tests.scripts.dev.worktree_guard_fakes import make_tools


def _tools(venv_root: Path, os_name: str = "nt", omit: str | None = None) -> None:
    """Create an explicit tool layout with an optional missing member."""
    make_tools(venv_root, os_name=os_name, omit=omit)


def _checkout(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Create ordinary and linked checkout topology without any environment."""
    primary, linked = tmp_path / "primary", tmp_path / "linked"
    common = primary / ".git"
    git_dir = common / "worktrees" / "linked"
    linked.mkdir()
    git_dir.mkdir(parents=True)
    return primary, linked, common, git_dir


def test_ordinary_windows_checkout_uses_its_own_venv(tmp_path):
    """A primary checkout resolves its repository-local Windows tools."""
    primary = tmp_path / "primary"
    common = primary / ".git"
    common.mkdir(parents=True)
    _tools(primary / ".venv")
    paths, issues = resolve_venv(
        repo_root=primary,
        git_dir=common,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert paths == VenvPaths(
        primary / ".venv",
        primary / ".venv/Scripts/python.exe",
        primary / ".venv/Scripts/pytest.exe",
        primary / ".venv/Scripts/pre-commit.exe",
    )
    assert issues == []


def test_linked_worktree_reuses_primary_checkout_venv(tmp_path):
    """A linked checkout resolves the primary checkout's Windows tools."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    _tools(primary / ".venv")
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert paths.root == primary / ".venv"
    assert not [issue for issue in issues if issue.severity == "ERROR"]


def test_distinct_linked_root_venv_is_rejected(tmp_path):
    """A real secondary environment fails before its tools can be used."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    _tools(primary / ".venv")
    _tools(linked / ".venv")
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert paths is None
    assert [issue.code for issue in issues] == ["WT008"]


def test_linked_posix_checkout_uses_primary_tool_layout(tmp_path):
    """A linked POSIX checkout selects bin executables from the primary venv."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    _tools(primary / ".venv", "posix")
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="posix",
    )
    assert paths.python == primary / ".venv/bin/python"
    assert paths.pytest == primary / ".venv/bin/pytest"
    assert paths.pre_commit == primary / ".venv/bin/pre-commit"
    assert issues == []


def test_missing_primary_environment_lists_every_required_tool(tmp_path):
    """An absent primary environment reports every required Windows path."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert paths is None
    assert [issue.code for issue in issues] == ["WT009"]
    for path in (
        Path(".venv") / "Scripts" / "python.exe",
        Path(".venv") / "Scripts" / "pytest.exe",
        Path(".venv") / "Scripts" / "pre-commit.exe",
    ):
        assert str(path) in issues[0].message
    assert "AGENTS.md Environment Setup" in issues[0].remediation


def test_missing_one_required_executable_names_only_that_tool(tmp_path):
    """A partial environment identifies the exact absent executable."""
    primary = tmp_path / "primary"
    common = primary / ".git"
    common.mkdir(parents=True)
    _tools(primary / ".venv", omit="pre-commit.exe")
    paths, issues = resolve_venv(
        repo_root=primary,
        git_dir=common,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert paths is None
    assert str(Path(".venv") / "Scripts" / "pre-commit.exe") in issues[0].message
    assert str(Path(".venv") / "Scripts" / "python.exe") not in issues[0].message
    assert str(Path(".venv") / "Scripts" / "pytest.exe") not in issues[0].message


def test_secondary_venv_remediation_admits_an_absent_primary(tmp_path):
    """Redirecting to the primary environment requires that it exist."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    _tools(linked / ".venv")
    _, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert [issue.code for issue in issues] == ["WT008"]
    assert "AGENTS.md Environment Setup" in issues[0].remediation
    assert "Use only the primary checkout environment" not in issues[0].remediation


def test_ordinary_checkout_without_an_environment_does_not_block(tmp_path):
    """A fresh clone must reach the documented Environment Setup step."""
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    _, issues = resolve_venv(
        repo_root=primary,
        git_dir=primary / ".git",
        common_dir=primary / ".git",
        main_worktree=primary,
        os_name="nt",
    )
    assert [(issue.code, issue.severity) for issue in issues] == [("WT009", "WARNING")]


def test_linked_worktree_without_an_environment_still_blocks(tmp_path):
    """Creating an environment inside a linked worktree stays forbidden."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    _, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert [(issue.code, issue.severity) for issue in issues] == [("WT009", "ERROR")]


def test_separate_git_dir_layout_resolves_the_real_main_worktree(tmp_path):
    """Shared metadata outside every checkout must not be mistaken for a root.

    Under `git clone --separate-git-dir` the metadata directory's parent holds
    no working tree at all, so deriving the primary root from it named a path
    with no `.venv` and rejected a valid checkout.
    """
    primary, linked = tmp_path / "primary", tmp_path / "linked"
    common = tmp_path / "metadata" / "repo.git"
    git_dir = common / "worktrees" / "linked"
    linked.mkdir()
    git_dir.mkdir(parents=True)
    _tools(primary / ".venv")
    # The old derivation would look here, and finding nothing would raise WT009.
    assert not (common.parent / ".venv").exists()
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert issues == []
    assert paths.root == primary / ".venv"


def test_non_executable_posix_tool_is_reported_as_unusable(tmp_path):
    """A present file with no execute bit is not a runnable tool on POSIX.

    `access` is injected rather than relying on the host, because `os.access`
    reports every existing file as executable on Windows and the assertion
    would pass vacuously there.
    """
    primary = tmp_path / "primary"
    common = primary / ".git"
    common.mkdir(parents=True)
    _tools(primary / ".venv", os_name="posix")
    paths, issues = resolve_venv(
        repo_root=primary,
        git_dir=common,
        common_dir=common,
        main_worktree=primary,
        os_name="posix",
        access=lambda path, mode: False,
    )
    assert paths is None
    assert [issue.code for issue in issues] == ["WT009"]
    assert "not executable" in issues[0].message
    for path in (
        Path(".venv") / "bin" / "python",
        Path(".venv") / "bin" / "pytest",
        Path(".venv") / "bin" / "pre-commit",
    ):
        assert str(path) in issues[0].message


def test_executable_posix_tools_are_accepted(tmp_path):
    """The executability check must not reject a correctly built environment."""
    primary = tmp_path / "primary"
    common = primary / ".git"
    common.mkdir(parents=True)
    _tools(primary / ".venv", os_name="posix")
    paths, issues = resolve_venv(
        repo_root=primary,
        git_dir=common,
        common_dir=common,
        main_worktree=primary,
        os_name="posix",
        access=lambda path, mode: True,
    )
    assert issues == []
    assert paths.python == primary / ".venv/bin/python"


def test_posix_tools_built_by_the_doubles_are_executable_on_the_host(tmp_path):
    """The doubles must build a state the guard accepts, not one it rejects.

    Guards the fixture itself: `touch()` alone produced non-executable files,
    which is what let the missing check go unnoticed. Runs against the real
    `os.access`, so it is only meaningful on POSIX.
    """
    if os.name == "nt":
        pytest.skip("Windows derives executability from the extension")
    primary = tmp_path / "primary"
    common = primary / ".git"
    common.mkdir(parents=True)
    _tools(primary / ".venv", os_name="posix")
    paths, issues = resolve_venv(
        repo_root=primary,
        git_dir=common,
        common_dir=common,
        main_worktree=primary,
        os_name="posix",
    )
    assert issues == []
    assert paths is not None


def test_linked_root_symlink_to_primary_venv_is_allowed(tmp_path):
    """An alias to the sole primary environment is reuse, not duplication."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    primary_venv = primary / ".venv"
    _tools(primary_venv)
    try:
        (linked / ".venv").symlink_to(primary_venv, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory links are unavailable: {error}")
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common,
        main_worktree=primary,
        os_name="nt",
    )
    assert paths.root == primary_venv
    assert issues == []
