"""Unit tests for scripts.dev.graphify_refresh.

Every test stubs git and the graphify executable rather than touching the real
checkout. The contract under test is which verdict a given set of counts
produces, and that a rebuild is attempted only when one is due.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.dev.graphify_refresh import (
    DEFAULT_MIN_COMMITS,
    DEFAULT_MIN_FILES,
    GRAPH_DIR_NAME,
    GRAPH_FILE_NAME,
    GRAPHIFY_TIMEOUT_SECONDS,
    STATE_FILE_NAME,
    _parse_args,
    count_changed_files,
    count_commits_since,
    evaluate,
    main,
    read_state,
    refresh,
    write_state,
)

BASELINE = "0123456789abcdef0123456789abcdef01234567"


def _graph_dir(tmp_path: Path, *, with_graph: bool = True) -> Path:
    """Build a graph directory, optionally with the graph file present."""
    graph_dir = tmp_path / GRAPH_DIR_NAME
    graph_dir.mkdir(parents=True, exist_ok=True)
    if with_graph:
        (graph_dir / GRAPH_FILE_NAME).write_text("{}", encoding="utf-8")
    return graph_dir


def _decision(
    tmp_path: Path,
    *,
    commits: int | None,
    files: int | None,
    min_commits: int = 5,
    min_files: int = 25,
    force: bool = False,
):
    """Evaluate with the git counters stubbed to fixed values."""
    graph_dir = _graph_dir(tmp_path)
    write_state(graph_dir / STATE_FILE_NAME, BASELINE)
    with (
        patch("scripts.dev.graphify_refresh.count_commits_since", return_value=commits),
        patch("scripts.dev.graphify_refresh.count_changed_files", return_value=files),
    ):
        return evaluate(
            repo_root=tmp_path,
            graph_dir=graph_dir,
            min_commits=min_commits,
            min_files=min_files,
            force=force,
        )


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------


def test_evaluate_skips_without_a_graph_even_when_forced(tmp_path: Path) -> None:
    """GIVEN the fresh-clone state (no graph.json)
    WHEN a forced refresh is evaluated
    THEN it still skips and points at the /graphify skill, because
    `update` cannot create a first graph.
    """
    graph_dir = _graph_dir(tmp_path, with_graph=False)

    decision = evaluate(repo_root=tmp_path, graph_dir=graph_dir, force=True)

    assert decision.should_refresh is False
    assert "/graphify" in decision.reason


def test_evaluate_records_the_first_baseline_and_skips(tmp_path: Path) -> None:
    """GIVEN a graph that exists and no recorded baseline
    WHEN evaluated
    THEN it asks for a baseline stamp and rebuilds nothing.
    """
    graph_dir = _graph_dir(tmp_path)

    decision = evaluate(repo_root=tmp_path, graph_dir=graph_dir)

    assert decision.should_refresh is False
    assert decision.record_baseline is True


def test_evaluate_skips_below_both_thresholds(tmp_path: Path) -> None:
    """GIVEN four commits and 24 files since the baseline
    WHEN evaluated
    THEN nothing refreshes -- one short of each threshold.
    """
    decision = _decision(tmp_path, commits=4, files=24)

    assert decision.should_refresh is False
    assert decision.commits == 4
    assert decision.files == 24


def test_evaluate_refreshes_at_the_commit_threshold(tmp_path: Path) -> None:
    """GIVEN exactly five commits since the baseline
    WHEN evaluated
    THEN a refresh is due.
    """
    decision = _decision(tmp_path, commits=5, files=1)

    assert decision.should_refresh is True
    assert "threshold" in decision.reason


def test_evaluate_refreshes_at_the_file_threshold_for_one_commit(
    tmp_path: Path,
) -> None:
    """GIVEN one commit that touched exactly 25 files
    WHEN evaluated
    THEN the file count alone triggers the rebuild.
    """
    decision = _decision(tmp_path, commits=1, files=25)

    assert decision.should_refresh is True


def test_evaluate_refreshes_when_the_baseline_left_history(tmp_path: Path) -> None:
    """GIVEN a recorded baseline commit git can no longer resolve
    WHEN evaluated
    THEN it rebuilds rather than reporting zero progress forever.
    """
    decision = _decision(tmp_path, commits=None, files=None)

    assert decision.should_refresh is True
    assert "not in this clone's history" in decision.reason


def test_evaluate_force_overrides_the_thresholds(tmp_path: Path) -> None:
    """GIVEN no commits and no changed files since the baseline
    WHEN a forced refresh is evaluated
    THEN it is due anyway.
    """
    decision = _decision(tmp_path, commits=0, files=0, force=True)

    assert decision.should_refresh is True
    assert decision.reason == "refresh forced"


# ---------------------------------------------------------------------------
# git counters and state file
# ---------------------------------------------------------------------------


def test_count_commits_since_returns_none_when_git_fails(tmp_path: Path) -> None:
    """GIVEN git cannot resolve the baseline
    WHEN the commit count is taken
    THEN None is returned so the caller rebuilds instead of trusting a zero.
    """
    with patch("scripts.dev.graphify_refresh._run_git", return_value=None) as run:
        assert count_commits_since(tmp_path, BASELINE) is None

    run.assert_called_once_with(tmp_path, "rev-list", "--count", f"{BASELINE}..HEAD")


def test_count_commits_since_rejects_non_numeric_output(tmp_path: Path) -> None:
    """GIVEN git exits 0 but prints a diagnostic instead of a number
    WHEN the commit count is taken
    THEN None is returned rather than an exception.
    """
    with patch(
        "scripts.dev.graphify_refresh._run_git",
        return_value="fatal: bad revision",
    ) as run:
        assert count_commits_since(tmp_path, BASELINE) is None

    run.assert_called_once_with(tmp_path, "rev-list", "--count", f"{BASELINE}..HEAD")


def test_count_changed_files_ignores_blank_lines(tmp_path: Path) -> None:
    """GIVEN git lists two files with a blank line between them
    WHEN the changed files are counted
    THEN only the real paths are counted.
    """
    with patch(
        "scripts.dev.graphify_refresh._run_git",
        return_value="a.py\n\nb.py",
    ) as run:
        assert count_changed_files(tmp_path, BASELINE) == 2

    run.assert_called_once_with(tmp_path, "diff", "--name-only", f"{BASELINE}..HEAD")


def test_read_state_treats_a_corrupt_file_as_absent(tmp_path: Path) -> None:
    """GIVEN a truncated state file
    WHEN the baseline is read
    THEN None is returned, so the caller re-stamps instead of raising.
    """
    state_path = tmp_path / STATE_FILE_NAME
    state_path.write_text("{not json", encoding="utf-8")

    assert read_state(state_path) is None


def test_read_state_rejects_json_that_is_not_an_object(tmp_path: Path) -> None:
    """GIVEN a state file holding valid JSON that is not an object
    WHEN the baseline is read
    THEN None is returned. A list is truthy but has no baseline key, so
    returning it would raise AttributeError out of the hook.
    """
    state_path = tmp_path / STATE_FILE_NAME
    state_path.write_text('["not", "an", "object"]', encoding="utf-8")

    assert read_state(state_path) is None


def test_evaluate_force_stamps_an_absent_baseline(tmp_path: Path) -> None:
    """GIVEN a graph with no recorded baseline
    WHEN a forced refresh is evaluated
    THEN it is due and the new baseline is recorded, so the next window
    starts at this rebuild rather than the one before it.
    """
    graph_dir = _graph_dir(tmp_path)

    decision = evaluate(repo_root=tmp_path, graph_dir=graph_dir, force=True)

    assert decision.should_refresh is True
    assert decision.record_baseline is True


# ---------------------------------------------------------------------------
# refresh
# ---------------------------------------------------------------------------


def test_refresh_runs_the_incremental_update_and_stamps_head(tmp_path: Path) -> None:
    """GIVEN graphify succeeds
    WHEN a refresh runs
    THEN it updates incrementally in the repository root and records HEAD.
    """
    graph_dir = _graph_dir(tmp_path)
    with (
        patch(
            "scripts.dev.graphify_refresh.shutil.which",
            return_value="/usr/bin/graphify",
        ),
        patch(
            "scripts.dev.graphify_refresh.subprocess.run",
            return_value=MagicMock(returncode=0),
        ) as run,
        patch("scripts.dev.graphify_refresh._run_git", return_value="newhead"),
    ):
        assert refresh(repo_root=tmp_path, graph_dir=graph_dir) == 0

    run.assert_called_once_with(
        ["/usr/bin/graphify", "update", "."],
        cwd=tmp_path,
        timeout=GRAPHIFY_TIMEOUT_SECONDS,
        check=False,
    )
    state = read_state(graph_dir / STATE_FILE_NAME)
    assert state is not None
    assert state["last_refresh_commit"] == "newhead"


def test_refresh_leaves_the_baseline_unchanged_when_graphify_fails(
    tmp_path: Path,
) -> None:
    """GIVEN graphify exits nonzero
    WHEN a refresh runs
    THEN it reports failure and keeps the old baseline, so the threshold
    stays tripped for the next commit.
    """
    graph_dir = _graph_dir(tmp_path)
    write_state(graph_dir / STATE_FILE_NAME, BASELINE)
    with (
        patch(
            "scripts.dev.graphify_refresh.shutil.which",
            return_value="/usr/bin/graphify",
        ),
        patch(
            "scripts.dev.graphify_refresh.subprocess.run",
            return_value=MagicMock(returncode=2),
        ),
    ):
        assert refresh(repo_root=tmp_path, graph_dir=graph_dir) == 1

    state = read_state(graph_dir / STATE_FILE_NAME)
    assert state is not None
    assert state["last_refresh_commit"] == BASELINE


def test_refresh_skips_when_graphify_is_not_installed(tmp_path: Path, capsys) -> None:
    """GIVEN no graphify executable on PATH
    WHEN a refresh runs
    THEN nothing is executed, the run is not a failure, and it says so.
    """
    with (
        patch("scripts.dev.graphify_refresh.shutil.which", return_value=None),
        patch("scripts.dev.graphify_refresh.subprocess.run") as run,
    ):
        assert refresh(repo_root=tmp_path) == 0

    run.assert_not_called()
    assert "not on PATH" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main_dry_run_writes_nothing(tmp_path: Path, capsys) -> None:
    """GIVEN a due refresh and --dry-run
    WHEN main runs
    THEN it reports the intent, calls nothing, and leaves the baseline alone.
    """
    graph_dir = _graph_dir(tmp_path)
    write_state(graph_dir / STATE_FILE_NAME, BASELINE)
    with (
        patch("scripts.dev.graphify_refresh.count_commits_since", return_value=99),
        patch("scripts.dev.graphify_refresh.count_changed_files", return_value=99),
        patch("scripts.dev.graphify_refresh.refresh") as refresh_mock,
    ):
        assert main(["--repo-root", str(tmp_path), "--dry-run"]) == 0

    refresh_mock.assert_not_called()
    assert "would refresh" in capsys.readouterr().out
    state = read_state(graph_dir / STATE_FILE_NAME)
    assert state is not None
    assert state["last_refresh_commit"] == BASELINE


def test_main_records_the_baseline_on_first_run(tmp_path: Path) -> None:
    """GIVEN a graph with no recorded baseline
    WHEN main runs unforced
    THEN it stamps HEAD and rebuilds nothing.
    """
    graph_dir = _graph_dir(tmp_path)
    with patch("scripts.dev.graphify_refresh._run_git", return_value="headsha"):
        assert main(["--repo-root", str(tmp_path)]) == 0

    state = read_state(graph_dir / STATE_FILE_NAME)
    assert state is not None
    assert state["last_refresh_commit"] == "headsha"


def test_main_quiet_hides_the_skip_line(tmp_path: Path, capsys) -> None:
    """GIVEN the hooks' --quiet invocation
    WHEN the run skips
    THEN it prints nothing, so a commit stays silent.
    """
    _graph_dir(tmp_path, with_graph=False)

    assert main(["--repo-root", str(tmp_path), "--quiet"]) == 0

    assert capsys.readouterr().out == ""


def test_default_thresholds_are_pinned_to_five_commits_or_25_files(
    tmp_path: Path, capsys
) -> None:
    """GIVEN the CLI defaults the hooks actually run with
    WHEN they are read and then exercised at their boundary
    THEN the thresholds are 5 commits or 25 files. cosmic-ray reports
    that mutating either constant otherwise passes unnoticed, because
    every other test passes explicit values.
    """
    args = _parse_args([])
    assert (
        (args.min_commits, args.min_files)
        == (
            DEFAULT_MIN_COMMITS,
            DEFAULT_MIN_FILES,
        )
        == (5, 25)
    )

    graph_dir = _graph_dir(tmp_path)
    write_state(graph_dir / STATE_FILE_NAME, BASELINE)
    with (
        patch("scripts.dev.graphify_refresh.count_commits_since", return_value=5),
        patch("scripts.dev.graphify_refresh.count_changed_files", return_value=0),
        patch("scripts.dev.graphify_refresh.refresh") as refresh_mock,
    ):
        assert main(["--repo-root", str(tmp_path), "--dry-run"]) == 0

    refresh_mock.assert_not_called()
    assert "would refresh" in capsys.readouterr().out
