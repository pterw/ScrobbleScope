"""Diagnostics must name the branch whose lineage was actually measured."""

import pytest

from scripts.dev.worktree_guard import (
    LineageSnapshot,
    classify_lineage,
    inspect_worktree,
)
from tests.scripts.dev.worktree_guard_fakes import FakeGit, ok, repository

EXPECTED = "wip/batch-21"
ACTUAL = "review/other"


def _snapshot(**overrides):
    """Build a wrong-branch snapshot whose counts describe the checkout."""
    values = {
        "active_batch": 21,
        "expected_branch": EXPECTED,
        "actual_branch": ACTUAL,
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


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"behind": 2}, "WT006"),
        ({"behind": 3, "ahead": 3}, "WT004"),
        ({"behind": 2, "ahead": 1, "base_tree": "tree-b"}, "WT005"),
        ({"dirty": True}, "WT010"),
    ],
    ids=("behind", "identical-tree", "true-divergence", "dirty"),
)
def test_lineage_diagnostics_name_the_inspected_branch(overrides, code):
    """Ancestry comes from HEAD, so its verdict may not name another branch."""
    issue = next(
        issue
        for issue in classify_lineage(_snapshot(**overrides))
        if issue.code == code
    )
    assert issue.subject == ACTUAL
    assert issue.subject != EXPECTED


def test_no_diagnostic_attributes_head_state_to_the_expected_branch():
    """No wrong-branch verdict may cite PLAYBOOK's branch as its subject."""
    issues = classify_lineage(_snapshot(behind=3, ahead=3, dirty=True))
    assert [issue.code for issue in issues] == ["WT003", "WT010", "WT004"]
    assert {issue.subject for issue in issues} == {ACTUAL}


def test_aligned_branch_still_names_itself():
    """Correct alignment keeps naming the single branch under inspection."""
    issue = classify_lineage(
        _snapshot(actual_branch=EXPECTED, behind=2),
    )[0]
    assert (issue.code, issue.subject) == ("WT006", EXPECTED)


def test_wrong_branch_divergence_reported_through_real_inspection(tmp_path):
    """The collector must not relabel HEAD ancestry with PLAYBOOK's branch."""
    repo, responses = repository(tmp_path)
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = ok(f"{ACTUAL}\n")
    responses[("rev-list", "--left-right", "--count", "origin/main...HEAD")] = ok(
        "3\t3\n"
    )
    responses[("rev-parse", "HEAD^{tree}")] = ok("same-tree\n")
    responses[("rev-parse", "origin/main^{tree}")] = ok("same-tree\n")

    diagnostics = inspect_worktree(repo, runner=FakeGit(responses), environ={})

    artifact = next(issue for issue in diagnostics if issue.code == "WT004")
    assert artifact.subject == ACTUAL, (
        "WT004 advises a lease-protected force-push; naming a branch the guard "
        "never measured points that advice at unrelated history."
    )
