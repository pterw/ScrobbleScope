"""Behavioural tests for pure live-document integrity analysis."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from docsync.integrity import collect_integrity_issues, collect_tracked_paths
from docsync.models import SyncError
from docsync.renderer import SIDE_ARCHIVE_PREFIX


def _valid_inputs(tmp_path: Path) -> dict[str, object]:
    """Build one internally consistent active-Batch-21 document set."""
    definition = [
        "# BATCH21",
        "",
        "**Branch:** `wip/batch-21` (lineage lives in PLAYBOOK Section 4).",
    ]
    playbook = [
        "# PLAYBOOK",
        "",
        "## 3. Active batch + next action",
        "",
        "- **Batch 21 is active.** Definition: `BATCH21_DEFINITION.md`.",
        "  Branch: `wip/batch-21`.",
        "",
        "## 4. Execution log",
        "",
        "<!-- DOCSYNC:CURRENT-BATCH-START -->",
        "",
        "### 2026-08-05 - Current work (Batch 21 WP-0)",
        "",
        "Validation: **390 passed**.",
        "",
        "<!-- DOCSYNC:CURRENT-BATCH-END -->",
    ]
    live_documents = {
        "AGENTS.md": ["See `FINDINGS.md`."],
        "HANDOFF_PROMPT.md": ["Read `AGENTS.md`."],
        "AGENT_NOTES.md": ["Rules: `AGENTS.md`."],
        "PLAYBOOK.md": playbook,
        "FINDINGS.md": ["Archive: `docs/history/findings/FINDINGS_ARCHIVE.md`."],
        "BATCH21_DEFINITION.md": definition,
    }
    tracked = frozenset(
        {
            "AGENTS.md",
            "HANDOFF_PROMPT.md",
            "AGENT_NOTES.md",
            "PLAYBOOK.md",
            "FINDINGS.md",
            "BATCH21_DEFINITION.md",
            "docs/history/findings/FINDINGS_ARCHIVE.md",
        }
    )
    return {
        "repo_root": tmp_path,
        "live_documents": live_documents,
        "playbook_lines": playbook,
        "archive_lines": list(SIDE_ARCHIVE_PREFIX),
        "session_lines": None,
        "expected_session_lines": None,
        "tracked_paths": tracked,
    }


def test_dead_concrete_live_reference_is_error(tmp_path: Path):
    """A dead literal document reference blocks the live document set."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = ["See `docs/missing.md`."]

    issues = collect_integrity_issues(**inputs)

    assert [(i.code, i.path, i.line) for i in issues] == [("DOC001", "AGENTS.md", 1)]
    assert "tracked file" in issues[0].remediation


def test_schematic_and_historical_references_are_ignored(tmp_path: Path):
    """Patterns and dated history do not represent live concrete references."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [
        "Use `BATCHN_DEFINITION.md`, `docs/history/logs/*.md`, and ",
        "`docs/history/SWE_<date>.md` as documented patterns.",
    ]
    inputs["playbook_lines"].extend(
        ["", "### 2026-01-01 - Old entry", "", "`docs/deleted-old-file.md`"]
    )

    assert collect_integrity_issues(**inputs) == []


def test_markdown_link_syntax_is_checked(tmp_path: Path):
    """A Markdown link target is checked as well as a backtick path."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENT_NOTES.md"] = ["[Missing](docs/missing.md)"]

    issues = collect_integrity_issues(**inputs)

    assert [(i.code, i.path, i.line) for i in issues] == [
        ("DOC001", "AGENT_NOTES.md", 1)
    ]


def test_windows_reference_is_normalized_before_tracking_lookup(tmp_path: Path):
    """Windows separators never let a missing path evade the gate."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = ["See `docs\\missing.md`."]

    issues = collect_integrity_issues(**inputs)

    assert issues[0].path == "AGENTS.md"
    assert "docs/missing.md" in issues[0].invariant


@pytest.mark.parametrize("reference", ["docs/?.md", "docs/[old].md"])
def test_glob_references_are_ignored(tmp_path: Path, reference: str):
    """Wildcard-like paths are documentation patterns, not concrete files."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [f"See `{reference}`."]

    assert collect_integrity_issues(**inputs) == []


def test_two_broken_references_on_one_line_are_both_reported(tmp_path: Path):
    """Each literal reference has its own actionable diagnostic."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = ["See `docs/one.md` and `docs/two.md`."]

    issues = collect_integrity_issues(**inputs)

    assert [(issue.path, issue.line, issue.code) for issue in issues] == [
        ("AGENTS.md", 1, "DOC001"),
        ("AGENTS.md", 1, "DOC001"),
    ]


def test_issues_have_deterministic_path_line_code_order(tmp_path: Path):
    """Unordered input mappings still produce a stable issue sequence."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["HANDOFF_PROMPT.md"] = ["See `docs/late.md`."]
    inputs["live_documents"]["AGENTS.md"] = ["", "See `docs/early.md`."]

    issues = collect_integrity_issues(**inputs)

    assert [(issue.path, issue.line, issue.code) for issue in issues] == [
        ("AGENTS.md", 2, "DOC001"),
        ("HANDOFF_PROMPT.md", 1, "DOC001"),
    ]


def test_collect_tracked_paths_uses_only_git_tracked_paths(tmp_path: Path):
    """The tracked-path source is git ls-files and normalizes separators."""

    def runner(*args, **kwargs):
        assert args == (["git", "ls-files", "-z"],)
        assert kwargs["cwd"] == tmp_path
        return subprocess.CompletedProcess(
            args[0], 0, stdout="AGENTS.md\0docs\\note.md\0", stderr=""
        )

    assert collect_tracked_paths(tmp_path, runner) == frozenset(
        {"AGENTS.md", "docs/note.md"}
    )


def test_collect_tracked_paths_raises_sanitized_git_error(tmp_path: Path):
    """Git command failures surface safely rather than trusting incomplete paths."""

    def runner(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="bad git")

    with pytest.raises(SyncError, match=r"git ls-files: bad git"):
        collect_tracked_paths(tmp_path, runner)


def test_active_definition_sha_is_blocking(tmp_path: Path):
    """Volatile commit ancestry must not be pinned in active Branch metadata."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = [
        "# BATCH21",
        "**Branch:** `wip/batch-21` off `fa61716`.",
    ]

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC003"]
    assert "PLAYBOOK Section 4" in issues[0].remediation


def test_active_definition_reference_must_match_batch(tmp_path: Path):
    """The current batch cannot point at a previous batch definition."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"][
        4
    ] = "- **Batch 21 is active.** Definition: `BATCH20_DEFINITION.md`."
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC002"]


def test_untracked_active_definition_is_blocking(tmp_path: Path):
    """Supplied content cannot make an untracked active definition valid."""
    inputs = _valid_inputs(tmp_path)
    inputs["tracked_paths"] = inputs["tracked_paths"] - {"BATCH21_DEFINITION.md"}

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC002", "PLAYBOOK.md", 5)
    ]


def test_non_definition_batch_reference_is_still_checked(tmp_path: Path):
    """Only the declared Definition path is exempt from generic reference checks."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].insert(6, "- Previous: `BATCH20_DEFINITION.md`.")
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC001"]


def test_playbook_reference_after_dated_entry_keeps_original_line_number(
    tmp_path: Path,
):
    """Skipping Section 4 history preserves diagnostics for later sections."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].extend(
        ["", "## 5. Follow-up", "", "See `docs/missing.md`."]
    )
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC001", "PLAYBOOK.md", 20)
    ]


def test_missing_active_definition_reference_is_blocking(tmp_path: Path):
    """An active batch requires exactly one definition declaration."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"][4] = "- **Batch 21 is active.**"
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC002"]


def test_duplicate_active_definition_references_are_blocking(tmp_path: Path):
    """Multiple active definitions create ambiguous ownership."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].insert(5, "- Definition: `BATCH21_PROPOSAL.md`.")
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC002"]


@pytest.mark.parametrize(
    "definition",
    [
        ["# BATCH21"],
        ["**Branch:** `wip/batch-21`.", "**Branch:** `other`."],
    ],
)
def test_active_definition_requires_exactly_one_branch_field(
    tmp_path: Path, definition: list[str]
):
    """Missing or duplicate Branch metadata is volatile-document drift."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = definition

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC003"]


def test_noncanonical_archive_prefix_is_blocking(tmp_path: Path):
    """The archive preamble must be the renderer's canonical contract."""
    inputs = _valid_inputs(tmp_path)
    inputs["archive_lines"] = [
        "# PLAYBOOK Execution Log Archive",
        "",
        "Purpose: old Section 10 path",
    ]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC004"]


def test_present_stale_session_block_is_blocking(tmp_path: Path):
    """A provided managed session rendering must match expected output exactly."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["stale"]
    inputs["expected_session_lines"] = ["fresh"]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC005"]


def test_absent_session_skips_session_integrity(tmp_path: Path):
    """Repositories without session context do not get a session diagnostic."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = None
    inputs["expected_session_lines"] = None

    assert collect_integrity_issues(**inputs) == []


def test_matching_current_test_counts_do_not_report_contradiction(tmp_path: Path):
    """The same live test count is consistent across both documents."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["Tests: **390 passed**."]
    inputs["expected_session_lines"] = ["Tests: **390 passed**."]

    assert collect_integrity_issues(**inputs) == []


def test_mismatching_current_test_counts_are_blocking(tmp_path: Path):
    """Conflicting live test counts are an actionable session contradiction."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["Tests: **389 passed**."]
    inputs["expected_session_lines"] = ["Tests: **389 passed**."]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC006"]


def test_test_count_in_only_one_source_is_not_a_contradiction(tmp_path: Path):
    """DOC006 needs two current counts before it can compare them."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["No count here."]
    inputs["expected_session_lines"] = ["No count here."]

    assert collect_integrity_issues(**inputs) == []
