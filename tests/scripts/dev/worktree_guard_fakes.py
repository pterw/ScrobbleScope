"""Reusable filesystem and Git doubles for worktree-guard behavior tests."""

import os
from pathlib import Path

from scripts.dev.worktree_guard import CommandResult, LineageSnapshot


class FakeGit:
    """Return exact Git responses while recording every requested command."""

    def __init__(self, responses):
        """Store the response map and initialize the observable call history."""
        self.responses = responses
        self.calls = []

    def __call__(self, cwd, args):
        """Record one exact invocation and return its configured response."""
        self.calls.append((cwd, args))
        return self.responses[args]


def ok(stdout=""):
    """Build a successful immutable command result for a fake Git call."""
    return CommandResult(0, stdout, "")


def fail(stderr="fatal"):
    """Build a failed immutable command result for a fake Git call."""
    return CommandResult(128, "", stderr)


def repository(
    tmp_path: Path,
    *,
    linked: bool = False,
    base_ref: str = "origin/main",
    os_name: str | None = None,
) -> tuple[Path, dict]:
    """Create a host-appropriate repository and its discovery response map."""
    repo = tmp_path / "linked" if linked else tmp_path / "primary"
    repo.mkdir()
    repo.joinpath("PLAYBOOK.md").write_text(
        "# PLAYBOOK\n\n## 3. Active batch + next action\n\n"
        "- **Batch 21 is active.** Branch: `wip/batch-21`.\n\n"
        "## 4. Execution log\n",
        encoding="utf-8",
    )
    if linked:
        primary = tmp_path / "primary"
        common = primary / ".git"
        git_dir = common / "worktrees" / "linked"
        git_dir.mkdir(parents=True)
        _tools(primary / ".venv", os_name=os_name)
        git_dir_text = "../primary/.git/worktrees/linked\n"
        common_text = "../primary/.git\n"
        worktree_list_text = worktree_listing(primary, repo)
    else:
        repo.joinpath(".git").mkdir()
        _tools(repo / ".venv", os_name=os_name)
        git_dir_text = common_text = ".git\n"
        worktree_list_text = worktree_listing(repo)
    responses = {
        ("rev-parse", "--show-toplevel"): ok(f"{repo}\n"),
        ("rev-parse", "--git-dir"): ok(git_dir_text),
        ("rev-parse", "--git-common-dir"): ok(common_text),
        ("worktree", "list", "--porcelain"): ok(worktree_list_text),
        ("symbolic-ref", "--quiet", "--short", "HEAD"): ok("wip/batch-21\n"),
        ("rev-parse", "--verify", f"{base_ref}^{{commit}}"): ok("base\n"),
        ("rev-list", "--left-right", "--count", f"{base_ref}...HEAD"): ok("0\t0\n"),
        ("status", "--porcelain"): ok(),
    }
    return repo, responses


def worktree_listing(*roots: Path) -> str:
    """Render `git worktree list --porcelain` output, main working tree first.

    Git emits one blank-line-separated record per working tree and documents the
    first as the main one, so callers pass the primary checkout first.
    """
    records = [
        f"worktree {root}\nHEAD {'a' * 40}\nbranch refs/heads/branch-{index}\n"
        for index, root in enumerate(roots)
    ]
    return "\n".join(records)


def codes(diagnostics):
    """Return stable diagnostic codes without coupling tests to prose."""
    return [diagnostic.code for diagnostic in diagnostics]


def snapshot(**overrides):
    """Build an aligned active-batch lineage snapshot for classifier tests."""
    values = {
        "active_batch": 21,
        "expected_branch": "wip/batch-21",
        "actual_branch": "wip/batch-21",
        "base_ref": "origin/main",
        "behind": 0,
        "ahead": 0,
        "head_tree": "tree-a",
        "base_tree": "tree-a",
        "dirty": False,
        "detached": False,
        "recognized_ci": False,
    }
    values.update(overrides)
    return LineageSnapshot(**values)


def make_tools(
    venv_root: Path,
    *,
    os_name: str | None = None,
    omit: str | None = None,
    executable: bool = True,
) -> None:
    """Create the host-appropriate tool layout, optionally omitting one file."""
    for tool in venv_tools(venv_root, os_name=os_name).values():
        if tool.name == omit:
            continue
        _write_tool(tool, executable=executable)


def venv_tools(venv_root: Path, *, os_name: str | None = None) -> dict[str, Path]:
    """Return the required virtualenv tools for a host or simulated OS."""
    selected_os = os.name if os_name is None else os_name
    relative = (
        {
            "python": Path("Scripts/python.exe"),
            "pytest": Path("Scripts/pytest.exe"),
            "pre_commit": Path("Scripts/pre-commit.exe"),
        }
        if selected_os == "nt"
        else {
            "python": Path("bin/python"),
            "pytest": Path("bin/pytest"),
            "pre_commit": Path("bin/pre-commit"),
        }
    )
    return {name: venv_root / path for name, path in relative.items()}


def _tools(venv_root: Path, *, os_name: str | None) -> None:
    """Create the three executables required by environment resolution."""
    for tool in venv_tools(venv_root, os_name=os_name).values():
        _write_tool(tool, executable=True)


def _write_tool(tool: Path, *, executable: bool) -> None:
    """Create one tool file, granting the execute bit unless told otherwise.

    `touch()` alone produces a non-executable file, which on POSIX is not a
    usable tool. Every double that stands in for a working environment must
    therefore set the execute bit, or it asserts against a state the guard is
    supposed to reject.
    """
    tool.parent.mkdir(parents=True, exist_ok=True)
    tool.touch()
    mode = tool.stat().st_mode
    tool.chmod(mode | 0o111 if executable else mode & ~0o111)
