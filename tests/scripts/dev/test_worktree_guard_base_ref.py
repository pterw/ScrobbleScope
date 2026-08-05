"""Behavior tests for caller-selected worktree comparison references."""

import pytest

from scripts.dev.worktree_guard import inspect_worktree
from tests.scripts.dev.worktree_guard_fakes import (
    FakeGit,
    codes,
    fail,
    ok,
    repository,
)


def test_default_missing_base_preserves_fetch_and_offline_remediation(tmp_path):
    """WT007 keeps the established actionable default-base guidance."""
    repo, responses = repository(tmp_path)
    responses[("rev-parse", "--verify", "origin/main^{commit}")] = fail()
    diagnostics = inspect_worktree(repo, runner=FakeGit(responses))
    assert codes(diagnostics) == ["WT007"]
    assert diagnostics[0].remediation == (
        "When network access is available, run git fetch --prune origin, then rerun "
        "the guard. Offline, ensure the required local ref exists; this guard does "
        "not fetch."
    )


@pytest.mark.parametrize(
    ("base_ref", "remediation"),
    [
        (
            "upstream/trunk",
            "Refresh or otherwise verify the selected base ref upstream/trunk exists "
            "locally and is current, then rerun the guard. This guard does not fetch.",
        ),
        (
            "main",
            "Verify the local base ref main exists and is current, then rerun the "
            "guard. This guard does not fetch.",
        ),
    ],
    ids=("custom-remote", "local-ref"),
)
def test_missing_base_remediation_matches_selected_ref(tmp_path, base_ref, remediation):
    """Missing custom and local bases never prescribe the origin remote."""
    repo, responses = repository(tmp_path, base_ref=base_ref)
    responses[("rev-parse", "--verify", f"{base_ref}^{{commit}}")] = fail()
    diagnostics = inspect_worktree(repo, base_ref=base_ref, runner=FakeGit(responses))
    assert codes(diagnostics) == ["WT007"]
    assert diagnostics[0].remediation == remediation


def test_custom_base_divergence_remediation_names_selected_ref(tmp_path):
    """WT004 refresh guidance follows the configured remote-tracking base."""
    base_ref = "upstream/trunk"
    repo, responses = repository(tmp_path, base_ref=base_ref)
    responses[("rev-list", "--left-right", "--count", f"{base_ref}...HEAD")] = ok(
        "2\t1\n"
    )
    responses[("rev-parse", "HEAD^{tree}")] = ok("same-tree\n")
    responses[("rev-parse", f"{base_ref}^{{tree}}")] = ok("same-tree\n")
    diagnostics = inspect_worktree(repo, base_ref=base_ref, runner=FakeGit(responses))
    assert codes(diagnostics) == ["WT004"]
    assert diagnostics[0].remediation == (
        "Stop. Reconcile any dirty files, refresh upstream/trunk, verify the trees "
        "again, obtain the explicit owner approval required by AGENTS.md, then "
        "realign the named branch and use force-push with lease. This guard performs "
        "none of those actions."
    )
