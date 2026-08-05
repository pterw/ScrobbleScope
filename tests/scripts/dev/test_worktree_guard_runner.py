"""Behavior tests for sanitized worktree-guard subprocess execution."""

import subprocess

import pytest

from scripts.dev.worktree_guard import CommandResult, GuardError, run_git


def test_run_git_returns_captured_process_data(monkeypatch, tmp_path):
    """The real runner exposes return code and both captured text streams."""
    observed = {}

    def fake_run(command, **kwargs):
        """Capture subprocess options and return a hand-built Git result."""
        observed.update(command=command, **kwargs)
        return subprocess.CompletedProcess(command, 7, "out", "err")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = run_git(tmp_path, ("status", "--porcelain"))
    assert result == CommandResult(7, "out", "err")
    assert observed == {
        "command": ["git", "status", "--porcelain"],
        "cwd": tmp_path,
        "capture_output": True,
        "text": True,
        "timeout": 10,
        "check": False,
    }


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FileNotFoundError("secret-url"), "Git executable was not found"),
        (OSError("secret-url"), "Git command could not be started"),
        (
            subprocess.TimeoutExpired(["git", "secret-url"], 10),
            "Git command timed out",
        ),
    ],
    ids=("missing-git", "os-error", "timeout"),
)
def test_run_git_sanitizes_process_failures(monkeypatch, tmp_path, error, message):
    """Process-launch failures omit secrets and suppress their exception chain."""

    def fail_run(*args, **kwargs):
        """Raise the controlled process failure without invoking a subprocess."""
        raise error

    monkeypatch.setattr(subprocess, "run", fail_run)
    with pytest.raises(GuardError, match=message) as exc_info:
        run_git(tmp_path, ("fetch", "https://token@example.invalid/repo.git"))
    assert "secret-url" not in str(exc_info.value)
    assert "token" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True
