"""Behavior tests for detached and linked worktree inspection outcomes."""

import pytest

from scripts.dev.worktree_guard import CommandResult, inspect_worktree
from tests.scripts.dev.worktree_guard_fakes import (
    FakeGit,
    codes,
    repository,
    venv_tools,
)


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        ({"CI": "YeS"}, "WT011"),
        ({"GITHUB_ACTIONS": "1"}, "WT011"),
        ({}, "WT012"),
    ],
    ids=("recognized-ci", "recognized-github-actions", "local"),
)
def test_detached_checkout_stops_before_local_topology_checks(
    tmp_path, environ, expected
):
    """Detached CI skips cleanly while detached local work fails safely."""
    repo, responses = repository(tmp_path)
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = CommandResult(1, "", "")
    runner = FakeGit(responses)
    diagnostics = inspect_worktree(repo, environ=environ, runner=runner)
    assert codes(diagnostics) == [expected]
    assert [args for _, args in runner.calls][-1] == (
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
    )


@pytest.mark.parametrize("linked", [False, True], ids=("normal", "linked"))
def test_summary_reports_checkout_kind_and_primary_tools(tmp_path, linked):
    """Successful summaries expose topology and the sole qualified tool paths."""
    repo, responses = repository(tmp_path, linked=linked)
    diagnostics = inspect_worktree(repo, offline=True, runner=FakeGit(responses))
    assert codes(diagnostics) == ["WT000", "WT013"]
    summary = diagnostics[0].message
    assert ("linked worktree" if linked else "primary checkout") in summary
    assert "local-ref-only" not in summary
    assert "local-ref-only" in diagnostics[1].message
    tools = venv_tools(tmp_path / "primary" / ".venv")
    for tool in tools.values():
        assert str(tool) in summary


def test_inspection_accepts_simulated_posix_tool_layout(tmp_path):
    """The public inspection boundary honors a deterministic POSIX topology."""
    repo, responses = repository(tmp_path, linked=True, os_name="posix")

    diagnostics = inspect_worktree(
        repo,
        offline=True,
        runner=FakeGit(responses),
        os_name="posix",
    )

    assert codes(diagnostics) == ["WT000", "WT013"]
    summary = diagnostics[0].message
    for tool in venv_tools(tmp_path / "primary" / ".venv", os_name="posix").values():
        assert str(tool) in summary
    assert "Scripts" not in summary
