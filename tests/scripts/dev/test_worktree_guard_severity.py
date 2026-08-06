"""Decision-table contracts for every stable worktree diagnostic severity."""

import os
from pathlib import Path

import pytest

from scripts.dev.worktree_guard import (
    GuardError,
    classify_lineage,
    inspect_worktree,
    resolve_venv,
)
from tests.scripts.dev.worktree_guard_fakes import (
    FakeGit,
    fail,
    make_tools,
    repository,
)
from tests.scripts.dev.worktree_guard_fakes import snapshot as _snapshot


def _venv_diagnostics(tmp_path: Path, *, secondary: bool):
    """Exercise the two invalid linked-worktree virtualenv topologies."""
    primary, linked = tmp_path / "primary", tmp_path / "linked"
    common = primary / ".git"
    git_dir = common / "worktrees" / "linked"
    linked.mkdir()
    git_dir.mkdir(parents=True)
    if secondary:
        make_tools(primary / ".venv")
        make_tools(linked / ".venv")
    return resolve_venv(
        repo_root=linked, git_dir=git_dir, common_dir=common, os_name=os.name
    )[1]


def _decision_diagnostics(tmp_path: Path, state: str):
    """Run the real production decision path named by one table row."""
    lineage = {
        "metadata-missing": {"expected_branch": None},
        "wrong-branch": {"actual_branch": "review/other"},
        "identical-divergence": {"behind": 2, "ahead": 1},
        "true-divergence": {"behind": 2, "ahead": 1, "base_tree": "tree-b"},
        "behind": {"behind": 2},
        "dirty": {"dirty": True},
        "detached-ci": {
            "actual_branch": None,
            "detached": True,
            "recognized_ci": True,
        },
        "detached-local": {"actual_branch": None, "detached": True},
    }
    if state in lineage:
        return classify_lineage(_snapshot(**lineage[state]))
    if state in {"secondary-venv", "missing-venv"}:
        return _venv_diagnostics(tmp_path, secondary=state == "secondary-venv")
    if state == "not-repository":
        runner = FakeGit({("rev-parse", "--show-toplevel"): fail()})
        return inspect_worktree(tmp_path, runner=runner)
    repo, responses = repository(tmp_path)
    if state == "missing-base":
        responses[("rev-parse", "--verify", "origin/main^{commit}")] = fail()
    runner = FakeGit(responses)
    if state == "runtime-failure":

        def raise_failure(cwd, args):
            """Reproduce a sanitized collector failure at the public boundary."""
            raise GuardError("sensitive command")

        runner = raise_failure
    return inspect_worktree(repo, offline=state == "offline", runner=runner)


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("aligned", [("WT000", "INFO")]),
        ("not-repository", [("WT001", "ERROR")]),
        ("metadata-missing", [("WT002", "ERROR")]),
        ("wrong-branch", [("WT003", "ERROR")]),
        ("identical-divergence", [("WT004", "ERROR")]),
        ("true-divergence", [("WT005", "ERROR")]),
        ("behind", [("WT006", "ERROR")]),
        ("missing-base", [("WT007", "ERROR")]),
        ("secondary-venv", [("WT008", "ERROR")]),
        ("missing-venv", [("WT009", "ERROR")]),
        ("dirty", [("WT010", "WARNING")]),
        ("detached-ci", [("WT011", "INFO")]),
        ("detached-local", [("WT012", "ERROR")]),
        ("offline", [("WT000", "INFO"), ("WT013", "INFO")]),
        ("runtime-failure", [("WT014", "ERROR")]),
    ],
)
def test_every_decision_state_has_exact_code_and_severity(tmp_path, state, expected):
    """A severity mutation cannot silently change whether bootstrap blocks."""
    diagnostics = _decision_diagnostics(tmp_path, state)
    assert [(item.code, item.severity) for item in diagnostics] == expected
