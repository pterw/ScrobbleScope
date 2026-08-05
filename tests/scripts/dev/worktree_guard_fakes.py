"""Reusable filesystem and Git doubles for worktree-guard behavior tests."""

import os
from pathlib import Path

from scripts.dev.worktree_guard import CommandResult


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
    else:
        repo.joinpath(".git").mkdir()
        _tools(repo / ".venv", os_name=os_name)
        git_dir_text = common_text = ".git\n"
    responses = {
        ("rev-parse", "--show-toplevel"): ok(f"{repo}\n"),
        ("rev-parse", "--git-dir"): ok(git_dir_text),
        ("rev-parse", "--git-common-dir"): ok(common_text),
        ("symbolic-ref", "--quiet", "--short", "HEAD"): ok("wip/batch-21\n"),
        ("rev-parse", "--verify", f"{base_ref}^{{commit}}"): ok("base\n"),
        ("rev-list", "--left-right", "--count", f"{base_ref}...HEAD"): ok("0\t0\n"),
        ("status", "--porcelain"): ok(),
    }
    return repo, responses


def codes(diagnostics):
    """Return stable diagnostic codes without coupling tests to prose."""
    return [diagnostic.code for diagnostic in diagnostics]


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
        tool.parent.mkdir(parents=True, exist_ok=True)
        tool.touch()
