"""Behavior tests for primary-checkout virtualenv resolution."""

from pathlib import Path

import pytest

from scripts.dev.worktree_guard import VenvPaths, resolve_venv


def _tools(venv_root: Path, os_name: str = "nt", omit: str | None = None) -> None:
    """Create a real temporary tool layout with an optional missing member."""
    directory, names = (
        ("Scripts", ("python.exe", "pytest.exe", "pre-commit.exe"))
        if os_name == "nt"
        else ("bin", ("python", "pytest", "pre-commit"))
    )
    tools = venv_root / directory
    tools.mkdir(parents=True)
    for name in names:
        if name != omit:
            (tools / name).touch()


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
        repo_root=primary, git_dir=common, common_dir=common, os_name="nt"
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
        repo_root=linked, git_dir=git_dir, common_dir=common, os_name="nt"
    )
    assert paths.root == primary / ".venv"
    assert not [issue for issue in issues if issue.severity == "ERROR"]


def test_distinct_linked_root_venv_is_rejected(tmp_path):
    """A real secondary environment fails before its tools can be used."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    _tools(primary / ".venv")
    _tools(linked / ".venv")
    paths, issues = resolve_venv(
        repo_root=linked, git_dir=git_dir, common_dir=common, os_name="nt"
    )
    assert paths is None
    assert [issue.code for issue in issues] == ["WT008"]


def test_linked_posix_checkout_uses_primary_tool_layout(tmp_path):
    """A linked POSIX checkout selects bin executables from the primary venv."""
    primary, linked, common, git_dir = _checkout(tmp_path)
    _tools(primary / ".venv", "posix")
    paths, issues = resolve_venv(
        repo_root=linked, git_dir=git_dir, common_dir=common, os_name="posix"
    )
    assert paths.python == primary / ".venv/bin/python"
    assert paths.pytest == primary / ".venv/bin/pytest"
    assert paths.pre_commit == primary / ".venv/bin/pre-commit"
    assert issues == []


def test_missing_primary_environment_lists_every_required_tool(tmp_path):
    """An absent primary environment reports every required Windows path."""
    _, linked, common, git_dir = _checkout(tmp_path)
    paths, issues = resolve_venv(
        repo_root=linked, git_dir=git_dir, common_dir=common, os_name="nt"
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
        repo_root=primary, git_dir=common, common_dir=common, os_name="nt"
    )
    assert paths is None
    assert str(Path(".venv") / "Scripts" / "pre-commit.exe") in issues[0].message
    assert str(Path(".venv") / "Scripts" / "python.exe") not in issues[0].message
    assert str(Path(".venv") / "Scripts" / "pytest.exe") not in issues[0].message


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
        repo_root=linked, git_dir=git_dir, common_dir=common, os_name="nt"
    )
    assert paths.root == primary_venv
    assert issues == []
