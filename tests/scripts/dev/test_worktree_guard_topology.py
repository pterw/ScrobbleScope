"""Behavior tests for detached and linked worktree inspection outcomes."""

import pytest

from scripts.dev.worktree_guard import CommandResult, inspect_worktree
from tests.scripts.dev.worktree_guard_fakes import (
    FakeGit,
    codes,
    ok,
    repository,
    venv_tools,
)


@pytest.mark.parametrize(
    ("environ", "expected", "last_call"),
    [
        (
            {"CI": "YeS"},
            "WT011",
            ("symbolic-ref", "--quiet", "--short", "HEAD"),
        ),
        (
            {"GITHUB_ACTIONS": "1"},
            "WT011",
            ("symbolic-ref", "--quiet", "--short", "HEAD"),
        ),
        ({}, "WT012", ("status", "--porcelain")),
    ],
    ids=("recognized-ci", "recognized-github-actions", "local"),
)
def test_detached_checkout_stops_before_local_topology_checks(
    tmp_path, environ, expected, last_call
):
    """Detached CI skips cleanly while detached local work is measured for
    dirtiness (F-WORKTREE-3) before failing safely."""
    repo, responses = repository(tmp_path)
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = CommandResult(1, "", "")
    runner = FakeGit(responses)
    diagnostics = inspect_worktree(repo, environ=environ, runner=runner)
    assert codes(diagnostics) == [expected]
    assert [args for _, args in runner.calls][-1] == last_call


def test_detached_dirty_local_reports_wt012_and_wt010(tmp_path):
    """F-WORKTREE-3: a detached, dirty, non-CI worktree must not hide its
    dirty state behind WT012 alone through the real inspection path."""
    repo, responses = repository(tmp_path)
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = CommandResult(1, "", "")
    responses[("status", "--porcelain")] = ok(" M scripts/dev/foo.py\n")
    diagnostics = inspect_worktree(repo, environ={}, runner=FakeGit(responses))
    assert codes(diagnostics) == ["WT012", "WT010"]


def test_detached_ci_skips_before_playbook_metadata_is_required(tmp_path):
    """A CI checkout skips topology even when PLAYBOOK cannot be parsed."""
    repo, responses = repository(tmp_path)
    repo.joinpath("docs", "agents", "PLAYBOOK.md").write_text(
        "# PLAYBOOK\n\nno sections\n", "utf-8"
    )
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = CommandResult(1, "", "")

    diagnostics = inspect_worktree(
        repo, environ={"CI": "true"}, runner=FakeGit(responses)
    )

    assert codes(diagnostics) == ["WT011"]


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
