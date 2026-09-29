"""Repo Assist's file grant must cover what AGENTS.md's procedure writes.

Repo Assist opens draft PRs through gh-aw's safe outputs, which refuse any
file outside an ``allowed-files`` list. The list once fell behind the
procedure (the test-count pin moved into ``config/docsync.toml`` and the list
did not), so every PR the agent opened was refused. These tests derive the
files a PR must write from docsync's own names and check them against the
COMPILED lock, the file GitHub actually runs, and check that the source
``.md`` and the lock still say the same thing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from docsync.cli import ARCHIVE_PATH, LOGS_DIR
from docsync.declarations import DECLARATIONS_FILENAME, load_documents_config
from docsync.integrity import SESSION_CONTEXT_RELATIVE_PATH

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
SOURCE = WORKFLOWS / "repo-assist.md"
LOCK = WORKFLOWS / "repo-assist.lock.yml"

SAFE_OUTPUTS = ("create_pull_request", "push_to_pull_request_branch")
SOURCE_KEYS = ("create-pull-request", "push-to-pull-request-branch")
CONFIG_VARIABLES = ("GH_AW_SAFE_OUTPUTS_CONFIG", "GH_AW_SAFE_OUTPUTS_HANDLER_CONFIG")


def _glob_matches(pattern: str, path: str) -> bool:
    """Match a path the way gh-aw does: ``**`` spans directories, ``*`` does not."""
    regex = ""
    index = 0
    while index < len(pattern):
        if pattern.startswith("**", index):
            regex += ".*"
            index += 2
        elif pattern[index] == "*":
            regex += "[^/]*"
            index += 1
        elif pattern[index] == "?":
            regex += "[^/]"
            index += 1
        else:
            regex += re.escape(pattern[index])
            index += 1
    return re.fullmatch(regex, path) is not None


def _lock_allowed_files(lock_text: str, variable: str) -> dict[str, list[str]]:
    """Read each safe output's ``allowed_files`` from one JSON config line.

    The line is ``NAME: "<json>"``: a YAML double-quoted scalar whose text is
    itself JSON. ``json.loads`` twice reads it without a YAML dependency.
    """
    matches = re.findall(rf'^\s*{variable}: (".*")\s*$', lock_text, re.MULTILINE)
    assert len(matches) == 1, (
        f"expected one {variable} line in the lock, found {len(matches)}"
    )
    config = json.loads(json.loads(matches[0]))
    grants = {
        name: config[name]["allowed_files"] for name in SAFE_OUTPUTS if name in config
    }
    assert set(grants) == set(SAFE_OUTPUTS), (
        f"{variable} lacks allowed_files for {SAFE_OUTPUTS}"
    )
    for name, patterns in grants.items():
        assert patterns, f"{variable} {name} has an empty allowed_files list"
    return grants


def _source_allowed_files(source_text: str) -> dict[str, list[str]]:
    """Read each safe output's ``allowed-files`` from the frontmatter only."""
    parts = source_text.replace("\r\n", "\n").split("\n---\n", 1)
    assert source_text.startswith("---\n") or source_text.startswith("---\r\n")
    frontmatter = parts[0]
    grants: dict[str, list[str]] = {}
    for key in SOURCE_KEYS:
        block = re.search(
            rf"^  {key}:\n(?P<body>(?:    .*\n|\n)*)", frontmatter + "\n", re.MULTILINE
        )
        assert block, f"no {key} block in the frontmatter"
        listed = re.search(
            r"^    allowed-files:\n(?P<items>(?:      - \".*\"\n)+)",
            block["body"],
            re.MULTILINE,
        )
        assert listed, f"no allowed-files list under {key}"
        grants[key.replace("-", "_")] = re.findall(r'"(.*)"', listed["items"])
    return grants


def _procedure_files() -> list[str]:
    """Every file a Repo Assist PR writes under AGENTS.md's commit procedure."""
    documents = load_documents_config(REPO_ROOT)
    return [
        documents.playbook,
        documents.findings,
        SESSION_CONTEXT_RELATIVE_PATH,
        DECLARATIONS_FILENAME,
        ARCHIVE_PATH.as_posix(),
        (LOGS_DIR / "BATCH1_LOG.md").as_posix(),
    ]


@pytest.mark.parametrize("variable", CONFIG_VARIABLES)
def test_compiled_lock_grants_every_file_the_procedure_writes(variable):
    grants = _lock_allowed_files(LOCK.read_text(encoding="utf-8"), variable)
    for name, patterns in grants.items():
        missing = [
            path
            for path in _procedure_files()
            if not any(_glob_matches(pattern, path) for pattern in patterns)
        ]
        assert not missing, f"{variable} {name} does not allow {missing}: {patterns}"


def test_source_allowed_files_equal_the_compiled_lock():
    source = _source_allowed_files(SOURCE.read_text(encoding="utf-8"))
    lock_text = LOCK.read_text(encoding="utf-8")
    for variable in CONFIG_VARIABLES:
        assert source == _lock_allowed_files(lock_text, variable), (
            "repo-assist.md and the lock disagree: run `gh aw compile repo-assist`"
        )


def test_lock_reader_fails_loudly_on_a_missing_or_empty_config():
    with pytest.raises(AssertionError, match="expected one"):
        _lock_allowed_files("nothing here\n", CONFIG_VARIABLES[0])
    empty = json.dumps(
        json.dumps({name: {"allowed_files": []} for name in SAFE_OUTPUTS})
    )
    with pytest.raises(AssertionError, match="empty allowed_files"):
        _lock_allowed_files(f"  {CONFIG_VARIABLES[0]}: {empty}\n", CONFIG_VARIABLES[0])


def test_source_reader_fails_loudly_without_a_list():
    with pytest.raises(AssertionError, match="no create-pull-request block"):
        _source_allowed_files("---\non: x\n---\nbody\n")


def test_glob_matching_follows_gh_aw():
    assert _glob_matches("docs/logarchive/**", "docs/logarchive/a/b.md")
    assert _glob_matches("tests/**", "tests/x.py")
    assert not _glob_matches("docs/*", "docs/a/b.md")
    assert not _glob_matches("config/docsync.toml", "config/docsync.toml.bak")
    assert not _glob_matches("config/docsync.toml", "config/other.toml")
