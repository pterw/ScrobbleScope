"""Unit tests for scripts.dev.ci_jobs, the classifier and aggregator the CI uses."""

from __future__ import annotations

import itertools

import pytest

from scripts.dev.ci_jobs import aggregate, docs_only, main

RESULTS = ("success", "failure", "cancelled", "skipped")
DOCS_ONLY_VALUES = ("true", "false", "")


def _allowed(changes: str, checks: str, browser: str, flag: str) -> bool:
    # An empty docs_only is never a pass, even for three green jobs (O-brief 8).
    if flag not in ("true", "false"):
        return False
    if changes != "success" or checks != "success":
        return False
    return browser == "success" or (browser == "skipped" and flag == "true")


AGGREGATE_CASES = [
    (c, k, b, f, _allowed(c, k, b, f))
    for c, k, b, f in itertools.product(RESULTS, RESULTS, RESULTS, DOCS_ONLY_VALUES)
]


@pytest.mark.parametrize("changes, checks, browser, flag, ok", AGGREGATE_CASES)
def test_aggregate_passes_only_for_the_two_allowed_shapes(
    changes, checks, browser, flag, ok
):
    """GIVEN the three job results and the docs_only output
    WHEN aggregate decides
    THEN it passes only for all-success or a docs-only browser skip.
    """
    code, message = aggregate(changes, checks, browser, flag)
    assert (code == 0) is ok, message


@pytest.mark.parametrize("flag", ["", "maybe", "True", "1"])
def test_aggregate_rejects_an_empty_or_unknown_docs_only_value(flag):
    """GIVEN a skipped browser and a docs_only value that is not true or false
    WHEN aggregate decides
    THEN it fails rather than treating the value as docs-only.
    """
    code, message = aggregate("success", "success", "skipped", flag)
    assert code == 1
    assert "docs_only" in message


@pytest.mark.parametrize(
    "args, culprit",
    [
        (("failure", "success", "success", "false"), "changes"),
        (("cancelled", "success", "success", "false"), "changes"),
        (("success", "failure", "success", "false"), "checks"),
        (("success", "success", "failure", "false"), "browser"),
        (("success", "success", "skipped", "false"), "browser"),
    ],
)
def test_aggregate_failure_message_names_the_offending_job(args, culprit):
    """GIVEN one job that did not pass
    WHEN aggregate decides
    THEN the message names that job.
    """
    code, message = aggregate(*args)
    assert code == 1
    assert culprit in message


def _nul(*paths: str) -> bytes:
    return b"".join(p.encode() + b"\0" for p in paths)


DOCS_ONLY_CASES = [
    (("docs/guide.txt",), True),
    (("docs/a/b/c.png",), True),
    (("README.md",), True),
    (("a/b/c/notes.md",), True),
    ((".superpowers/sdd/x/progress.json",), True),
    (("config/docsync.toml",), True),
    (("docs/my file.txt",), True),
    (("docs/a.md", "README.md", "config/docsync.toml"), True),
    (("docs/a.md", "scrobblescope/app.py"), False),
    (("README.md", "scripts/dev/x.py"), False),
    ((".superpowers/x", "tests/test_a.py"), False),
    (("config/docsync.toml", ".github/workflows/test.yml"), False),
    (("newtop/file.txt",), False),
    (("Dockerfile",), False),
    (("docs_tools/x.py",), False),
    (("app/docs/x.py",), False),
    (("notes.mdx",), False),
    (("sub/config/docsync.toml",), False),
    (("config/docsync.toml.bak",), False),
    ((), False),
]


@pytest.mark.parametrize("paths, expected", DOCS_ONLY_CASES)
def test_docs_only_classifies_changed_paths(paths, expected):
    """GIVEN NUL-separated changed paths
    WHEN docs_only classifies them
    THEN it is true only when every path is a documentation path.
    """
    assert docs_only(_nul(*paths)) is expected


@pytest.mark.parametrize("raw", [b"", b"\0", b"\0\0\0"])
def test_docs_only_is_false_for_empty_input(raw):
    """GIVEN empty input or only NUL separators
    WHEN docs_only classifies it
    THEN it is false (fail closed).
    """
    assert docs_only(raw) is False


def test_main_docs_only_reads_stdin_and_prints_the_verdict(capsys, monkeypatch):
    """GIVEN a docs path on stdin
    WHEN the docs-only command runs
    THEN it prints true and returns 0.
    """

    class _Stdin:
        buffer = type("B", (), {"read": staticmethod(lambda: b"docs/a.md\0")})()

    monkeypatch.setattr("sys.stdin", _Stdin())
    assert main(["docs-only"]) == 0
    assert capsys.readouterr().out.strip() == "true"


def test_main_aggregate_returns_one_and_names_the_failure(capsys):
    """GIVEN a failed checks job
    WHEN the aggregate command runs
    THEN it returns 1 and prints the offending job.
    """
    argv = [
        "aggregate",
        "--changes=success",
        "--checks=failure",
        "--browser=success",
        "--docs-only=false",
    ]
    assert main(argv) == 1
    assert "checks" in capsys.readouterr().out


def test_main_aggregate_accepts_an_empty_docs_only_value(capsys):
    """GIVEN an empty --docs-only (changes failed, so no output)
    WHEN the aggregate command runs
    THEN it returns 1 instead of failing argument parsing.
    """
    argv = [
        "aggregate",
        "--changes=failure",
        "--checks=success",
        "--browser=skipped",
        "--docs-only=",
    ]
    assert main(argv) == 1
