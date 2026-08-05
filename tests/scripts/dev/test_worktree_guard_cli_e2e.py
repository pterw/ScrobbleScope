"""End-to-end CLI tests with real inspection and only subprocess Git replaced."""

import subprocess

import pytest

from scripts.dev import check_worktree_alignment as cli
from scripts.dev.worktree_guard import CommandResult
from tests.scripts.dev.worktree_guard_fakes import ok, repository


def _install_git(monkeypatch, responses):
    """Route subprocess Git calls through exact controlled command results."""

    def fake_run(command, **kwargs):
        """Return one CompletedProcess while keeping run_git itself real."""
        result = responses[tuple(command[1:])]
        return subprocess.CompletedProcess(
            command, result.returncode, result.stdout, result.stderr
        )

    monkeypatch.setattr(subprocess, "run", fake_run)


def _rendered_pairs(output: str):
    """Read code/severity pairs from primary diagnostic output lines."""
    return [
        (parts[1], parts[0])
        for line in output.splitlines()
        if not line.startswith("Remediation:")
        for parts in [line.split(maxsplit=3)]
    ]


@pytest.mark.parametrize(
    ("state", "expected", "exit_code", "offline"),
    [
        ("blocking", [("WT006", "ERROR")], 1, False),
        ("warning-only", [("WT010", "WARNING"), ("WT000", "INFO")], 0, False),
        ("success", [("WT000", "INFO")], 0, False),
        ("detached-ci", [("WT011", "INFO")], 0, False),
        (
            "offline-failure",
            [("WT006", "ERROR"), ("WT013", "INFO")],
            1,
            True,
        ),
    ],
)
def test_real_inspection_through_cli_preserves_exit_contract(
    tmp_path, monkeypatch, capsys, state, expected, exit_code, offline
):
    """Representative real decisions render and block only on ERROR severity."""
    repo, responses = repository(tmp_path)
    if state in {"blocking", "offline-failure"}:
        responses[("rev-list", "--left-right", "--count", "origin/main...HEAD")] = ok(
            "2\t0\n"
        )
    elif state == "warning-only":
        responses[("status", "--porcelain")] = ok("?? notes.txt\n")
    elif state == "detached-ci":
        responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = CommandResult(
            1, "", ""
        )
        monkeypatch.setenv("CI", "true")
    _install_git(monkeypatch, responses)
    monkeypatch.chdir(repo)

    assert cli.main(["--offline"] if offline else []) == exit_code
    captured = capsys.readouterr()
    assert _rendered_pairs(captured.out) == expected
    assert captured.err == ""


@pytest.mark.parametrize("failure", ["timeout", "os-error", "metadata-parse"])
@pytest.mark.parametrize("offline", [False, True], ids=("online", "offline"))
def test_cli_converts_runtime_failures_without_traceback_or_sensitive_text(
    tmp_path, monkeypatch, capsys, failure, offline
):
    """Collector failures become WT014 and retain final offline context."""
    repo, responses = repository(tmp_path)
    if failure == "metadata-parse":
        responses[("rev-list", "--left-right", "--count", "origin/main...HEAD")] = ok(
            "secret malformed counts\n"
        )
        _install_git(monkeypatch, responses)
    else:
        error = (
            subprocess.TimeoutExpired(["git", "secret-url"], 10)
            if failure == "timeout"
            else OSError("secret-url")
        )

        def fail_run(*args, **kwargs):
            """Raise a process failure from the real run_git boundary."""
            raise error

        monkeypatch.setattr(subprocess, "run", fail_run)
    monkeypatch.chdir(repo)

    assert cli.main(["--offline"] if offline else []) == 1
    captured = capsys.readouterr()
    expected = [("WT014", "ERROR")]
    if offline:
        expected.append(("WT013", "INFO"))
    assert _rendered_pairs(captured.out) == expected
    assert "secret" not in captured.out
    assert "Traceback" not in captured.out + captured.err
    assert captured.err == ""
