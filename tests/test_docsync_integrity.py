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


@pytest.mark.parametrize(
    "line",
    [
        "Upstream: [contributing](https://example.com/CONTRIBUTING.md).",
        "Upstream: [spec](http://example.org/a/b.md).",
        "Mirror: `https://example.com/guide.md`.",
        "Local copy: `/home/peter/repo/PLAYBOOK.md`.",
        "Windows copy: `C:/Users/peter/repo/PLAYBOOK.md`.",
        "Sibling: `../other-repo/AGENTS.md`.",
    ],
    ids=("md-link", "http-link", "backtick-url", "posix-abs", "windows-abs", "parent"),
)
def test_non_repository_targets_are_not_tracked_path_candidates(
    tmp_path: Path, line: str
):
    """DOC001 governs repository-relative references, so nothing else may block."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [line]

    assert collect_integrity_issues(**inputs) == []


def test_fenced_examples_are_not_references(tmp_path: Path):
    """Illustrative blocks describe history, not the current document set.

    Only fenced blocks are excluded. Indentation is ambiguous in this corpus,
    where the canonical documents use four-space continuations inside lists,
    so treating it as a code block would silently disable the check there.
    """
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [
        "Recovering a deleted charter:",
        "",
        "```bash",
        "git show HEAD~50:`docs/OLD_CHARTER.md`",
        "```",
    ]

    assert collect_integrity_issues(**inputs) == []


def test_placeholder_shapes_are_not_reported_as_dead_links(tmp_path: Path):
    """Documented templates must not be mistaken for concrete repository files."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [
        "Templates: `BATCHN.md`, `BATCH{n}_DEFINITION.md`, `path/to/FILE.md`.",
    ]

    assert collect_integrity_issues(**inputs) == []


def test_a_real_dead_repository_reference_still_blocks(tmp_path: Path):
    """Narrowing the extractor must not weaken the invariant it enforces."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = ["See `docs/history/NO_SUCH_FILE.md`."]

    assert [i.code for i in collect_integrity_issues(**inputs)] == ["DOC001"]


def test_inline_shell_command_is_not_a_document_reference(tmp_path: Path):
    """A command that searches a path is not itself a Markdown path reference."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [
        '`rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`',
    ]

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

    assert [
        (issue.path, issue.line, issue.code, issue.invariant) for issue in issues
    ] == [
        (
            "AGENTS.md",
            1,
            "DOC001",
            "Concrete Markdown reference `docs/one.md` names a tracked file.",
        ),
        (
            "AGENTS.md",
            1,
            "DOC001",
            "Concrete Markdown reference `docs/two.md` names a tracked file.",
        ),
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
        return subprocess.CompletedProcess(
            args[0],
            1,
            stdout="",
            stderr=(
                "fatal: https://user:secret-token@example.invalid/private.git "
                r"C:\private\checkout"
            ),
        )

    with pytest.raises(SyncError) as exc_info:
        collect_tracked_paths(tmp_path, runner)

    assert str(exc_info.value) == "Repository tracked-file discovery failed"
    # Exact equality already proves the message itself carries nothing. The
    # chained original is the remaining leak path, so assert it is absent.
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


def test_collect_tracked_paths_sanitizes_git_invocation_oserror(tmp_path: Path):
    """A missing Git executable becomes a stable SyncError without host paths."""

    def runner(*args, **kwargs):
        raise FileNotFoundError(2, "missing", r"C:\private\bin\git.exe")

    with pytest.raises(SyncError) as exc_info:
        collect_tracked_paths(tmp_path, runner)

    assert str(exc_info.value) == "Repository tracked-file discovery failed"
    assert exc_info.value.__cause__ is None
    assert (
        exc_info.value.__suppress_context__
    ), "the original OSError carries the host path and must not be chained"


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


@pytest.mark.parametrize(
    "branch_line",
    [
        "**Branch:** `wip/batch-21-20260805`.",
        "**Branch:** `wip/batch-21` -- see PR #12345678.",
        "**Branch:** `feature/effaced-legacy-ui`.",
    ],
    ids=("dated-branch", "pr-number", "hex-alphabet-word"),
)
def test_branch_metadata_without_a_commit_identity_is_accepted(
    tmp_path: Path, branch_line: str
):
    """A long number or hex-alphabet word is not a pinned commit identity."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = ["# BATCH21", branch_line]

    assert collect_integrity_issues(**inputs) == []


def test_indented_branch_field_is_still_recognized(tmp_path: Path):
    """Reformatting the field as a list item must not change what is reported."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = [
        "# BATCH21",
        "- **Branch:** `wip/batch-21` (lineage lives in PLAYBOOK Section 4).",
    ]

    assert collect_integrity_issues(**inputs) == []


@pytest.mark.parametrize(
    ("definition", "expected"),
    [
        (["# BATCH21", "No branch metadata here."], "Keep one"),
        (
            [
                "# BATCH21",
                "**Branch:** `wip/batch-21`.",
                "**Branch:** `wip/other`.",
            ],
            "Keep one",
        ),
        (["# BATCH21", "**Branch:** `wip/batch-21` off `fa61716`."], "commit hash"),
    ],
    ids=("missing", "duplicate", "pinned-sha"),
)
def test_branch_metadata_remediation_matches_the_actual_violation(
    tmp_path: Path, definition: list[str], expected: str
):
    """Telling an author to remove a hash they never wrote is not actionable."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = definition

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC003"]
    assert expected in issues[0].remediation
    if expected == "Keep one":
        assert "Remove its commit hash" not in issues[0].remediation


def test_batch_handover_remediation_names_the_competing_declarations(tmp_path: Path):
    """Restating a satisfied invariant does not tell the author what to change."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].insert(
        5, "- **Batch 22 is opening.** Definition: `BATCH22_DEFINITION.md`."
    )
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    issues = collect_integrity_issues(**inputs)

    handover = next(issue for issue in issues if issue.code == "DOC002")
    assert "BATCH21_DEFINITION.md" in handover.remediation
    assert "BATCH22_DEFINITION.md" in handover.remediation


def test_missing_declaration_remediation_offers_the_between_batches_state(
    tmp_path: Path,
):
    """Between batches no definition exists, so that must be an offered option."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"][4] = "- **Batch 21 is active.**"
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC002"]
    assert "no batch is open" in issues[0].remediation


def test_pending_batch_log_path_is_not_a_dead_link(tmp_path: Path):
    """--check must not fail on a per-batch log --fix is about to generate."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [
        "Tagged batch history: `docs/history/logs/BATCH21_LOG.md`.",
    ]

    assert collect_integrity_issues(**inputs) == []


def test_active_definition_reference_must_match_batch(tmp_path: Path):
    """The current batch cannot point at a previous batch definition."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"][
        4
    ] = "- **Batch 21 is active.** Definition: `BATCH20_DEFINITION.md`."
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC002"]


def test_active_definition_reference_requires_complete_batch_token(tmp_path: Path):
    """Batch 21 must not accept a Batch 210 definition via prefix matching."""
    inputs = _valid_inputs(tmp_path)
    wrong_path = "BATCH210_DEFINITION.md"
    inputs["playbook_lines"][
        4
    ] = f"- **Batch 21 is active.** Definition: `{wrong_path}`."
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    inputs["live_documents"][wrong_path] = [
        "# BATCH210",
        "**Branch:** `wip/batch-210`.",
    ]
    inputs["tracked_paths"] = inputs["tracked_paths"] | {wrong_path}

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC002", "PLAYBOOK.md", 5)
    ]


def test_other_batch_prefix_is_not_an_active_definition_candidate(tmp_path: Path):
    """A root Batch 210 file cannot make Batch 21's candidate set ambiguous."""
    inputs = _valid_inputs(tmp_path)
    inputs["tracked_paths"] = inputs["tracked_paths"] | {"BATCH210_DEFINITION.md"}

    assert collect_integrity_issues(**inputs) == []


def test_root_batch_token_file_is_an_active_definition_candidate(tmp_path: Path):
    """The exact root Batch 21 token participates in uniqueness checking."""
    inputs = _valid_inputs(tmp_path)
    inputs["tracked_paths"] = inputs["tracked_paths"] | {"BATCH21.md"}

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC002", "PLAYBOOK.md", 5)
    ]
    assert "BATCH21.md, BATCH21_DEFINITION.md" in issues[0].remediation


def test_subdirectory_and_generic_batch_templates_are_not_candidates(tmp_path: Path):
    """Only concrete matching root files participate in DOC002 uniqueness."""
    inputs = _valid_inputs(tmp_path)
    inputs["tracked_paths"] = inputs["tracked_paths"] | {
        "docs/BATCH21_EXTRA.md",
        "BATCHN_DEFINITION.md",
    }

    assert collect_integrity_issues(**inputs) == []


def test_duplicate_tracked_active_definition_candidate_is_blocking(tmp_path: Path):
    """Every active batch has exactly one tracked matching root definition."""
    inputs = _valid_inputs(tmp_path)
    inputs["tracked_paths"] = inputs["tracked_paths"] | {"BATCH21_EXTRA.md"}

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC002", "PLAYBOOK.md", 5)
    ]
    assert "BATCH21_DEFINITION.md, BATCH21_EXTRA.md" in issues[0].remediation


def test_supplied_untracked_definition_cannot_replace_sole_tracked_candidate(
    tmp_path: Path,
):
    """In-memory content cannot override the repository's sole Batch 21 owner."""
    inputs = _valid_inputs(tmp_path)
    declared = "BATCH21_PROPOSAL.md"
    inputs["playbook_lines"][4] = f"- **Batch 21 is active.** Definition: `{declared}`."
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    inputs["live_documents"][declared] = [
        "# BATCH21",
        "**Branch:** `wip/batch-21`.",
    ]

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC002", "PLAYBOOK.md", 5)
    ]
    assert "BATCH21_DEFINITION.md" in issues[0].remediation


def test_between_batches_skips_root_definition_candidate_uniqueness(tmp_path: Path):
    """Tracked root candidates are irrelevant when no batch is active."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"][4:6] = [
        "- **Batch 21 is complete.**",
        "- **Batch 22 is not yet defined.**",
    ]
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    inputs["tracked_paths"] = inputs["tracked_paths"] | {"BATCH21_EXTRA.md"}

    assert collect_integrity_issues(**inputs) == []


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


def test_definition_label_outside_section_3_is_not_exempt(tmp_path: Path):
    """Only the resolved Section 3 declaration escapes generic DOC001 checks."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].extend(
        ["", "## 5. Notes", "", "Definition: `docs/missing.md`."]
    )
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC001", "PLAYBOOK.md", 20)
    ]


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

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == [
        "DOC002",
        "DOC001",
    ]


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


def test_archive_analysis_does_not_mutate_input_without_entries(tmp_path: Path):
    """Trimming a no-entry archive prefix must operate on a defensive copy."""
    inputs = _valid_inputs(tmp_path)
    archive_lines = [*SIDE_ARCHIVE_PREFIX, ""]
    inputs["archive_lines"] = archive_lines

    assert collect_integrity_issues(**inputs) == []
    assert archive_lines == [*SIDE_ARCHIVE_PREFIX, ""]


def test_present_stale_session_block_is_blocking(tmp_path: Path):
    """A provided managed session rendering must match expected output exactly."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["stale"]
    inputs["expected_session_lines"] = ["fresh"]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC005"]


def test_dead_session_reference_is_reported_at_its_source_line(tmp_path: Path):
    """The optional live session document participates in DOC001 scanning."""
    inputs = _valid_inputs(tmp_path)
    session_lines = ["# Session", "", "See `docs/missing.md`."]
    inputs["session_lines"] = session_lines
    inputs["expected_session_lines"] = list(session_lines)

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC001", ".claude/SESSION_CONTEXT.md", 3)
    ]


def test_absent_session_skips_session_integrity(tmp_path: Path):
    """Repositories without session context do not get a session diagnostic."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = None
    inputs["expected_session_lines"] = None

    assert collect_integrity_issues(**inputs) == []


def test_matching_current_test_counts_do_not_report_contradiction(tmp_path: Path):
    """The same live test count is consistent across both documents."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["| Tests | **390 passing** across 23 test modules |"]
    inputs["expected_session_lines"] = [
        "| Tests | **390 passing** across 23 test modules |"
    ]

    assert collect_integrity_issues(**inputs) == []


def test_mismatching_current_test_counts_are_blocking(tmp_path: Path):
    """Conflicting live test counts are an actionable session contradiction."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["| Tests | **389 passing** across 23 test modules |"]
    inputs["expected_session_lines"] = [
        "| Tests | **389 passing** across 23 test modules |"
    ]

    assert [issue.code for issue in collect_integrity_issues(**inputs)] == ["DOC006"]


def test_conflicting_named_session_counts_are_blocking_with_side_task_authority(
    tmp_path: Path,
):
    """A stale 390 mirror cannot hide beside the authoritative side-task 420."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].extend(
        [
            "",
            "### 2026-08-05 - Review remediation (side-task)",
            "",
            "Validation: focused -- **112 passed**. `pytest -q` --",
            "**420 passed**.",
        ]
    )
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    session_lines = [
        "| Tests | **420 passing** across 23 test modules |",
        "- Latest validated test count: **390 passed**.",
        "## 6. Test structure (420 tests)",
    ]
    inputs["session_lines"] = session_lines
    inputs["expected_session_lines"] = list(session_lines)

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC006"]


def test_ambiguous_authority_still_blocks_a_named_stale_count(tmp_path: Path):
    """An unresolvable authority must not disable the check it feeds.

    Ambiguity and absence both reach the gate as "no count", so the comparison
    used to be skipped for both: `--fix` rendered the managed block as unknown
    while a named numeric field kept its stale value, and the final pass exited
    0. That is the precise state DOC006 exists to catch.
    """
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].extend(
        [
            "",
            "### 2026-08-06 - Ambiguous side task",
            "",
            "Validation: focused suite **12 passed**; full suite **530 passed**.",
        ]
    )
    session_lines = ["| Tests | **390 passing** across 35 test modules |"]
    inputs["session_lines"] = session_lines
    inputs["expected_session_lines"] = list(session_lines)

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC006"]
    # The remediation must not send the reader to restate a number that no
    # entry establishes; the fix is to record an unambiguous result.
    assert "quotes several counts" in issues[0].remediation


def test_ambiguous_authority_without_named_counts_stays_silent(tmp_path: Path):
    """Ambiguity alone is not a contradiction when nothing claims a number."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].extend(
        [
            "",
            "### 2026-08-06 - Ambiguous side task",
            "",
            "Validation: focused suite **12 passed**; full suite **530 passed**.",
        ]
    )
    inputs["session_lines"] = ["No count here."]
    inputs["expected_session_lines"] = ["No count here."]

    assert collect_integrity_issues(**inputs) == []


def test_count_remediation_admits_a_rotated_authority(tmp_path: Path):
    """The authority can live in the archive, so the fix must not name PLAYBOOK."""
    inputs = _valid_inputs(tmp_path)
    session_lines = ["| Tests | **999 passing** across 35 test modules |"]
    inputs["session_lines"] = session_lines
    inputs["expected_session_lines"] = list(session_lines)

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC006"]
    assert "rotated archive" in issues[0].remediation


def test_test_count_in_only_one_source_is_not_a_contradiction(tmp_path: Path):
    """DOC006 needs two current counts before it can compare them."""
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["No count here."]
    inputs["expected_session_lines"] = ["No count here."]

    assert collect_integrity_issues(**inputs) == []


# ---------------------------------------------------------------------------
# DOC007: the definition's next-work-package claim vs PLAYBOOK Section 4
# ---------------------------------------------------------------------------


def _definition_with_status(status_line: str) -> list[str]:
    return [
        "# BATCH21",
        "",
        status_line,
        "",
        "**Branch:** `wip/batch-21` (lineage lives in PLAYBOOK Section 4).",
    ]


def test_doc007_agreeing_next_wp_claims_are_clean(tmp_path: Path):
    """A definition naming the same next WP as PLAYBOOK raises nothing."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = _definition_with_status(
        "**Status:** Active. WP-0 is complete. **WP-1 (toolchain) is the "
        "next batch work package.**"
    )

    assert collect_integrity_issues(**inputs) == []


def test_doc007_disagreeing_next_wp_claim_is_blocking(tmp_path: Path):
    """A stale claim in the definition blocks at its own line."""
    inputs = _valid_inputs(tmp_path)
    # The fixture's only current-batch entry is tagged WP-0, so PLAYBOOK
    # computes WP-1; a definition still claiming WP-2 must be caught.
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = _definition_with_status(
        "**Status:** Active. **WP-2 (shell) is the next batch work " "package.**"
    )

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC007", "BATCH21_DEFINITION.md", 3)
    ]
    assert "WP-1" in issues[0].invariant
    assert "WP-2" in issues[0].invariant
    assert "WP-1" in issues[0].remediation


def test_doc007_unparseable_next_wp_claim_stays_silent(tmp_path: Path):
    """No parseable claim means no mismatch -- silence beats a false hit."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = _definition_with_status(
        "**Status:** Active. Work continues per PLAYBOOK Section 3."
    )

    assert collect_integrity_issues(**inputs) == []


def test_doc007_missing_status_line_stays_silent(tmp_path: Path):
    """A definition without a Status line at all is not a DOC007 defect."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = [
        "# BATCH21",
        "**Branch:** `wip/batch-21` (lineage lives in PLAYBOOK Section 4).",
    ]

    assert collect_integrity_issues(**inputs) == []


def test_doc007_between_batches_never_reports(tmp_path: Path):
    """With no current-batch entries there is no computed value to compare."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"][4:6] = [
        "- **Batch 21 is complete.**",
        "- **Batch 22 is not yet defined.**",
    ]
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = _definition_with_status(
        "**Status:** Complete. **WP-9 (sweep) is the next batch work " "package.**"
    )

    assert collect_integrity_issues(**inputs) == []


def test_doc007_gap_in_completed_wps_picks_lowest_missing(tmp_path: Path):
    """The renderer's lowest-missing rule decides what 'next' means."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].extend(
        [
            "",
            "### 2026-08-06 - Another step (Batch 21 WP-2)",
            "",
            "Validation: `pytest -q` -- **400 passed**.",
        ]
    )
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    # WP-0 and WP-2 are tagged, so the lowest missing number is WP-1.
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = _definition_with_status(
        "**Status:** Active. **WP-3 (index) is the next batch work " "package.**"
    )

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC007"]
    assert "WP-1" in issues[0].invariant


# ---------------------------------------------------------------------------
# DOC008: the FINDINGS.md header test count
# ---------------------------------------------------------------------------


def test_doc008_agreeing_findings_header_count_is_clean(tmp_path: Path):
    """The header repeating the authoritative count raises nothing."""
    inputs = _valid_inputs(tmp_path)
    # The fixture's newest full-suite entry records **390 passed**.
    inputs["live_documents"]["FINDINGS.md"] = [
        "# Findings",
        "390 tests across 39 test modules.",
    ]

    assert collect_integrity_issues(**inputs) == []


def test_doc008_stale_findings_header_count_is_blocking(tmp_path: Path):
    """A header publishing an old total blocks at that line."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["FINDINGS.md"] = [
        "# Findings",
        "666 tests across 39 test modules.",
    ]

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC008", "FINDINGS.md", 2)
    ]
    assert "666" not in issues[0].remediation


def test_doc008_unparseable_findings_header_stays_silent(tmp_path: Path):
    """No header count line means nothing to compare against."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["FINDINGS.md"] = [
        "# Findings",
        "The suite grows every week.",
    ]

    assert collect_integrity_issues(**inputs) == []


def test_doc008_ambiguous_authority_blocks_a_named_header_count(tmp_path: Path):
    """Ambiguity suppresses older entries but must not disable this check."""
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"].extend(
        [
            "",
            "### 2026-08-06 - Ambiguous side task",
            "",
            "Validation: focused suite **12 passed**; full suite **530 passed**.",
        ]
    )
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    inputs["live_documents"]["FINDINGS.md"] = [
        "# Findings",
        "682 tests across 39 test modules.",
    ]

    issues = collect_integrity_issues(**inputs)

    assert [issue.code for issue in issues] == ["DOC008"]
    assert "quotes several counts" in issues[0].remediation


def test_collect_tracked_paths_reads_real_git_output(tmp_path: Path):
    """The default runner is never exercised through the CLI fixtures."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    tmp_path.joinpath("tracked.md").write_text("tracked\n", encoding="utf-8")
    tmp_path.joinpath("untracked.md").write_text("untracked\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.md"], cwd=tmp_path, check=True)

    tracked = collect_tracked_paths(tmp_path)

    assert "tracked.md" in tracked
    assert "untracked.md" not in tracked
