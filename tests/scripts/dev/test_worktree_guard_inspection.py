"""Behavior tests for read-only Git discovery and lineage orchestration."""

import pytest

from scripts.dev.worktree_guard import inspect_worktree
from tests.scripts.dev.worktree_guard_fakes import (
    FakeGit,
    codes,
    fail,
    ok,
    repository,
    venv_tools,
)


def test_missing_repository_fails_before_other_git_discovery(tmp_path):
    """A non-repository path yields WT001 and performs no follow-up commands."""
    runner = FakeGit({("rev-parse", "--show-toplevel"): fail()})
    diagnostics = inspect_worktree(tmp_path, runner=runner)
    assert codes(diagnostics) == ["WT001"]
    assert [args for _, args in runner.calls] == [("rev-parse", "--show-toplevel")]


def test_missing_base_fails_before_ancestry_or_status(tmp_path):
    """An unavailable comparison ref yields WT007 before lineage collection."""
    repo, responses = repository(tmp_path)
    responses[("rev-parse", "--verify", "origin/main^{commit}")] = fail()
    runner = FakeGit(responses)
    diagnostics = inspect_worktree(repo, runner=runner)
    assert codes(diagnostics) == ["WT007"]
    assert ("rev-list", "--left-right", "--count", "origin/main...HEAD") not in [
        args for _, args in runner.calls
    ]


def test_offline_wrong_branch_includes_local_ref_context(tmp_path):
    """A lineage error still discloses that offline ancestry is local-only."""
    repo, responses = repository(tmp_path)
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = ok("review/other\n")
    diagnostics = inspect_worktree(repo, offline=True, runner=FakeGit(responses))
    assert codes(diagnostics) == ["WT003", "WT013"]
    assert diagnostics[-1].message == (
        "offline mode; any base comparison is local-ref-only and freshness was "
        "not verified."
    )


def test_offline_venv_error_includes_local_ref_context(tmp_path):
    """An environment error does not suppress the independent offline qualifier."""
    repo, responses = repository(tmp_path)
    venv_tools(repo / ".venv")["pre_commit"].unlink()
    diagnostics = inspect_worktree(repo, offline=True, runner=FakeGit(responses))
    assert codes(diagnostics) == ["WT009", "WT013"]


@pytest.mark.parametrize(
    ("branch", "counts", "status", "expected"),
    [
        ("wip/batch-21", "0\t4\n", "", ["WT000"]),
        ("wip/batch-21", "2\t0\n", "", ["WT006"]),
        ("review/other", "0\t0\n", "", ["WT003"]),
        ("wip/batch-21", "0\t0\n", "?? notes.txt\n", ["WT010", "WT000"]),
    ],
    ids=("ahead-only", "behind-only", "wrong-branch", "dirty"),
)
def test_inspection_preserves_nondivergent_lineage_states(
    tmp_path, branch, counts, status, expected
):
    """Live collection forwards distinct ordinary states to the classifier."""
    repo, responses = repository(tmp_path)
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = ok(f"{branch}\n")
    responses[("rev-list", "--left-right", "--count", "origin/main...HEAD")] = ok(
        counts
    )
    responses[("status", "--porcelain")] = ok(status)
    runner = FakeGit(responses)
    diagnostics = inspect_worktree(repo, runner=runner)
    assert codes(diagnostics) == expected
    assert not any("^{tree}" in arg for _, args in runner.calls for arg in args)


@pytest.mark.parametrize(
    ("base_tree", "expected"),
    [("same-tree\n", "WT004"), ("other-tree\n", "WT005")],
    ids=("identical", "different"),
)
def test_divergence_reads_trees_and_never_runs_mutating_git(
    tmp_path, base_tree, expected
):
    """Only divergence reads tree IDs, and no diagnostic path mutates Git."""
    repo, responses = repository(tmp_path)
    responses[("rev-list", "--left-right", "--count", "origin/main...HEAD")] = ok(
        "3\t3\n"
    )
    responses[("rev-parse", "HEAD^{tree}")] = ok("same-tree\n")
    responses[("rev-parse", "origin/main^{tree}")] = ok(base_tree)
    runner = FakeGit(responses)
    diagnostics = inspect_worktree(repo, runner=runner)
    assert codes(diagnostics) == [expected]
    assert [args for _, args in runner.calls][-2:] == [
        ("rev-parse", "HEAD^{tree}"),
        ("rev-parse", "origin/main^{tree}"),
    ]
    assert [args for _, args in runner.calls] == [
        ("rev-parse", "--show-toplevel"),
        ("rev-parse", "--git-dir"),
        ("rev-parse", "--git-common-dir"),
        ("symbolic-ref", "--quiet", "--short", "HEAD"),
        ("status", "--porcelain"),
        ("rev-parse", "--verify", "origin/main^{commit}"),
        ("rev-list", "--left-right", "--count", "origin/main...HEAD"),
        ("rev-parse", "HEAD^{tree}"),
        ("rev-parse", "origin/main^{tree}"),
    ]
    forbidden = (
        "fetch",
        "reset",
        "rebase",
        "switch",
        "checkout",
        "push",
        "clean",
        "worktree remove",
    )
    commands = [" ".join(args) for _, args in runner.calls]
    assert not any(word in command for word in forbidden for command in commands)
