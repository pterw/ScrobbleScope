"""Reusable filesystem and Git doubles for worktree-guard behavior tests."""

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


def repository(tmp_path: Path, *, linked: bool = False) -> tuple[Path, dict]:
    """Create a controlled repository layout and its discovery response map."""
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
        _tools(primary / ".venv")
        git_dir_text = "../primary/.git/worktrees/linked\n"
        common_text = "../primary/.git\n"
    else:
        repo.joinpath(".git").mkdir()
        _tools(repo / ".venv")
        git_dir_text = common_text = ".git\n"
    responses = {
        ("rev-parse", "--show-toplevel"): ok(f"{repo}\n"),
        ("rev-parse", "--git-dir"): ok(git_dir_text),
        ("rev-parse", "--git-common-dir"): ok(common_text),
        ("symbolic-ref", "--quiet", "--short", "HEAD"): ok("wip/batch-21\n"),
        ("rev-parse", "--verify", "origin/main^{commit}"): ok("base\n"),
        ("rev-list", "--left-right", "--count", "origin/main...HEAD"): ok("0\t0\n"),
        ("status", "--porcelain"): ok(),
    }
    return repo, responses


def codes(diagnostics):
    """Return stable diagnostic codes without coupling tests to prose."""
    return [diagnostic.code for diagnostic in diagnostics]


def _tools(venv_root: Path) -> None:
    """Create the three Windows executables required by environment resolution."""
    scripts = venv_root / "Scripts"
    scripts.mkdir(parents=True)
    for name in ("python.exe", "pytest.exe", "pre-commit.exe"):
        (scripts / name).touch()
