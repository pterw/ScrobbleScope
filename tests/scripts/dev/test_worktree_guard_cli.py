"""Behavior tests for worktree-guard CLI rendering and exit status."""

from scripts.dev import check_worktree_alignment as cli
from scripts.dev.worktree_guard import Diagnostic


def test_cli_renders_error_and_remediation_on_separate_lines(monkeypatch, capsys):
    """An error diagnostic renders exactly and makes the CLI fail closed."""
    remediation = "Stop and obtain owner approval; this guard changes nothing."

    def fake_inspect(repo_root, *, base_ref, offline):
        """Return the controlled rebase-artifact diagnostic."""
        assert base_ref == "origin/main"
        assert offline is True
        return [
            Diagnostic(
                "ERROR",
                "WT004",
                "wip/batch-21",
                "branch and origin/main are 3/3 diverged but tree-identical.",
                remediation,
            ),
            Diagnostic(
                "INFO",
                "WT013",
                "origin/main",
                "offline mode; any base comparison is local-ref-only and freshness "
                "was not verified.",
            ),
        ]

    monkeypatch.setattr(cli, "inspect_worktree", fake_inspect)
    assert cli.main(["--offline"]) == 1
    assert capsys.readouterr().out == (
        "ERROR WT004 wip/batch-21 -- branch and origin/main are 3/3 "
        "diverged but tree-identical.\n"
        f"Remediation: {remediation}\n"
        "INFO WT013 origin/main -- offline mode; any base comparison is "
        "local-ref-only and freshness was not verified.\n"
    )


def test_custom_base_ref_does_not_change_the_default(monkeypatch):
    """A one-call override reaches inspection without mutating later defaults."""
    observed = []

    def fake_inspect(repo_root, *, base_ref, offline):
        """Record argument parsing and return one successful summary."""
        observed.append((base_ref, offline))
        return [Diagnostic("INFO", "WT000", "branch", "aligned")]

    monkeypatch.setattr(cli, "inspect_worktree", fake_inspect)
    assert cli.main(["--base-ref", "upstream/trunk"]) == 0
    assert cli.main([]) == 0
    assert observed == [("upstream/trunk", False), ("origin/main", False)]


def test_detached_ci_and_summary_are_non_errors(monkeypatch, capsys):
    """WT000 and WT011 informational paths both exit successfully."""
    diagnostics = iter(
        (
            Diagnostic("INFO", "WT000", "wip/batch-21", "aligned"),
            Diagnostic("INFO", "WT011", "detached HEAD", "recognized CI"),
        )
    )

    def fake_inspect(repo_root, *, base_ref, offline):
        """Return each accepted informational outcome in turn."""
        return [next(diagnostics)]

    monkeypatch.setattr(cli, "inspect_worktree", fake_inspect)
    assert cli.main([]) == 0
    assert cli.main([]) == 0
    assert "INFO WT000" in capsys.readouterr().out
