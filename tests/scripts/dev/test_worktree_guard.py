"""Behavior tests for PLAYBOOK parsing and lineage classification."""

import pytest

from scripts.dev.worktree_guard import (
    BatchBranch,
    GuardError,
    LineageSnapshot,
    classify_lineage,
    parse_batch_branch,
)


def _playbook(section_three: str, section_four: str = "") -> str:
    """Wrap controlled Section 3 and Section 4 content in a PLAYBOOK."""
    return (
        "# PLAYBOOK\n\n## 3. Active batch + next action\n\n"
        f"{section_three}\n\n## 4. Execution log\n\n{section_four}"
    )


@pytest.mark.parametrize(
    ("section_three", "section_four", "expected"),
    [
        (
            "- **Batch 21 is active.**\n  Branch: `wip/batch-21`.",
            "Branch: `stale/review-branch`.",
            BatchBranch(21, "wip/batch-21"),
        ),
        (
            "- **Batch 21 is complete.**\n- **Batch 22 is not yet defined.**",
            "",
            BatchBranch(None, None),
        ),
        ("- **Batch 21 is active.**", "", BatchBranch(21, None)),
        (
            "- **Batch 21 is active.**",
            "Branch: `stale/review-branch`.",
            BatchBranch(21, None),
        ),
    ],
    ids=("active", "between-batches", "missing-branch", "section-four-branch"),
)
def test_parse_batch_branch_uses_section_three_only(
    section_three, section_four, expected
):
    """Valid states parse literally without reading historical branch text."""
    assert parse_batch_branch(_playbook(section_three, section_four)) == expected


@pytest.mark.parametrize(
    ("playbook", "message"),
    [
        (
            _playbook(
                "- **Batch 21 is active.**\n  Branch: `wip/batch-21`.\n"
                "  Branch: `wip/other`."
            ),
            "branch",
        ),
        (
            _playbook(
                "- **Batch 21 is active.**\n- **Batch 22 is current.**\n"
                "  Branch: `wip/batch-22`."
            ),
            "active batch",
        ),
        (
            _playbook("- **Batch twenty-one is active.**\n  Branch: `wip/batch-21`."),
            "active batch",
        ),
        ("# PLAYBOOK\n\n## 4. Execution log\n\n- **Batch 21 is active.**", "Section 3"),
    ],
    ids=("two-branches", "two-active", "malformed-active", "missing-section"),
)
def test_malformed_playbook_state_fails_closed(playbook, message):
    """Ambiguous or malformed active state raises instead of choosing a value."""
    with pytest.raises(GuardError, match=message):
        parse_batch_branch(playbook)


def _snapshot(**overrides):
    """Build a lineage snapshot with an explicitly safe active-batch state."""
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


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, []),
        ({"ahead": 3}, []),
        ({"expected_branch": None}, ["WT002"]),
        (
            {
                "active_batch": None,
                "expected_branch": None,
                "actual_branch": "maintenance/docs",
                "behind": 4,
                "ahead": 2,
            },
            [],
        ),
        ({"actual_branch": "review/other"}, ["WT003"]),
        ({"dirty": True}, ["WT010"]),
        ({"behind": 2}, ["WT006"]),
    ],
    ids=("aligned", "ahead", "missing-metadata", "between", "wrong", "dirty", "behind"),
)
def test_classify_lineage_basic_decision_table(overrides, expected):
    """Each non-divergent state maps to its deterministic diagnostic codes."""
    assert [
        issue.code for issue in classify_lineage(_snapshot(**overrides))
    ] == expected


def test_identical_tree_divergence_is_rebase_artifact():
    """Matching trees require approval and lease-protected realignment."""
    issues = classify_lineage(_snapshot(behind=3, ahead=3))
    assert [issue.code for issue in issues] == ["WT004"]
    assert "owner approval" in issues[0].remediation
    assert "force-push with lease" in issues[0].remediation


def test_true_divergence_explicitly_prohibits_reset():
    """Different trees direct inspection and contain no reset command."""
    issue = classify_lineage(_snapshot(behind=2, ahead=1, base_tree="tree-b"))[0]
    assert issue.code == "WT005"
    assert "do not reset" in issue.remediation.lower()
    assert "git reset" not in issue.remediation.lower()


def test_detached_ci_skips_and_detached_local_fails():
    """Only recognized CI may skip branch checks from detached HEAD."""
    ci = classify_lineage(
        _snapshot(actual_branch=None, detached=True, recognized_ci=True)
    )
    local = classify_lineage(_snapshot(actual_branch=None, detached=True))
    assert [issue.code for issue in ci] == ["WT011"]
    assert [issue.code for issue in local] == ["WT012"]


def test_dirty_identical_divergence_keeps_lineage_error():
    """Dirty state warns first without erasing the rebase-artifact error."""
    issues = classify_lineage(_snapshot(dirty=True, behind=3, ahead=3))
    assert [issue.code for issue in issues] == ["WT010", "WT004"]


def test_diagnostic_order_is_wrong_branch_dirty_then_behind():
    """Independent diagnostics remain stable in the documented order."""
    issues = classify_lineage(
        _snapshot(actual_branch="review/other", dirty=True, behind=2)
    )
    assert [issue.code for issue in issues] == ["WT003", "WT010", "WT006"]
