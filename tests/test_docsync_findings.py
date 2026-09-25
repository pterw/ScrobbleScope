"""Finding lifecycle parsing and rotation planning regressions."""

import pytest
from docsync.findings import collect_rot_issues, plan_findings

ARCHIVE_PROLOGUE = "\n".join(
    [
        "# FINDINGS Archive",
        "",
        "Resolved and no-action findings rotate here from `FINDINGS.md`.",
        "Nothing here is deleted.",
        "",
        "---",
        "",
    ]
)


def _active(*blocks: str) -> str:
    header = "\n".join(
        [
            "# ScrobbleScope Findings & Open Issues",
            "",
            "Last updated: 2026-09-15",
            "",
            "## P0 -- Fix before next deploy",
            "",
        ]
    )
    return header + "\n".join(blocks)


def _codes(rotation) -> list[str]:
    return [issue.code for issue in rotation.issues]


RESOLVED = "\n".join(
    [
        "### F-B22-1: the cache connect attempt never timed out",
        "",
        "The connect call blocked forever when the socket stalled.",
        "",
        "- [x] **Status:** resolved",
        "**Completed:** 2026-09-14",
        "",
    ]
)

OPEN = "\n".join(
    [
        "### F-B22-2: the unmatched report omits its provider",
        "",
        "Nothing records which provider produced the miss.",
        "",
        "- [ ] **Status:** open",
        "",
    ]
)


# ---------------------------------------------------------------------------
# Rotation of well-formed records
# ---------------------------------------------------------------------------


def test_valid_checked_record_rotates():
    rotation = plan_findings(_active(RESOLVED, OPEN), ARCHIVE_PROLOGUE)

    assert rotation.issues == ()
    assert rotation.rotated_ids == ("F-B22-1",)
    assert "F-B22-1" not in rotation.active_text
    assert "F-B22-2" in rotation.active_text
    assert (
        "### F-B22-1: the cache connect attempt never timed out -- RESOLVED"
        in rotation.archive_text
    )


def test_rotation_lands_above_older_archived_entries():
    """The archive reads newest first, and a rotation must not bury itself.

    Appending put each new rotation below every older one, contradicting the
    prologue's own 'Newest rotation first' and, once this file paginates,
    putting the newest entries on the oldest page.
    """
    existing = ARCHIVE_PROLOGUE + "\n".join(
        [
            "## Rotated 2026-01-01 (Batch 1 close-out)",
            "",
            "### F-B1-9: an older finding -- RESOLVED",
            "",
            "Body of the older finding.",
            "",
        ]
    )

    rotation = plan_findings(_active(RESOLVED, OPEN), existing)

    assert rotation.rotated_ids == ("F-B22-1",)
    lines = rotation.archive_text.split("\n")
    assert lines[:6] == ARCHIVE_PROLOGUE.split("\n")[:6]
    new_at = next(i for i, line in enumerate(lines) if "F-B22-1" in line)
    old_at = next(i for i, line in enumerate(lines) if "F-B1-9" in line)
    assert new_at < old_at, rotation.archive_text


def test_first_rotation_keeps_a_blank_line_under_the_prologue():
    """An empty archive ends at its rule, with no blank line to sit under.

    The rotated block carries its separator after each entry, which is
    right when it is spliced above an existing entry. Inserted at the end
    of a prologue it needs one in front too, or the heading is glued to the
    `---` above it and reaches disk that way.
    """
    rotation = plan_findings(_active(RESOLVED, OPEN), ARCHIVE_PROLOGUE)

    lines = rotation.archive_text.split("\n")
    heading_at = next(i for i, line in enumerate(lines) if line.startswith("### "))
    assert lines[heading_at - 1] == "", lines[max(0, heading_at - 3) : heading_at + 1]


def test_unchecked_open_record_is_retained():
    rotation = plan_findings(_active(OPEN), ARCHIVE_PROLOGUE)

    assert rotation.issues == ()
    assert rotation.rotated_ids == ()
    assert "F-B22-2" in rotation.active_text
    assert "F-B22-2" not in rotation.archive_text


def test_no_action_with_explanation_rotates_with_its_own_suffix():
    block = "\n".join(
        [
            "### F-B22-3: the mutation runner misreports its scope",
            "",
            "The owner ruled the runner stays audit-only for this batch, so no",
            "code change is warranted.",
            "",
            "- [x] **Status:** no action",
            "**Completed:** 2026-09-13",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert rotation.issues == ()
    assert rotation.rotated_ids == ("F-B22-3",)
    assert (
        "### F-B22-3: the mutation runner misreports its scope -- NO ACTION"
        in rotation.archive_text
    )


def test_rotation_preserves_body_comments_and_lifecycle_record_exactly():
    block = "\n".join(
        [
            "### F-B22-4: a body worth preserving",
            "",
            "<!-- owner ruling 2026-09-02: keep this note verbatim -->",
            "",
            "```markdown",
            "### F-FAKE-1: a fenced example that is not a finding",
            "```",
            "",
            "    indented block that must survive",
            "",
            "- [x] **Status:** resolved",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert rotation.rotated_ids == ("F-B22-4",)
    body = block.strip("\n").split("\n")[1:]
    for line in body:
        assert line in rotation.archive_text.split("\n")
    assert "<!-- owner ruling 2026-09-02: keep this note verbatim -->" in (
        rotation.archive_text
    )
    assert "- [x] **Status:** resolved" in rotation.archive_text
    assert "**Completed:** 2026-09-10" in rotation.archive_text


def test_fenced_example_heading_is_never_a_finding():
    block = "\n".join(
        [
            "### F-B22-5: documents the heading format",
            "",
            "```markdown",
            "### F-EXAMPLE-9: not a real finding",
            "```",
            "",
            "- [ ] **Status:** open",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert rotation.issues == ()
    assert rotation.rotated_ids == ()


def test_eligible_ids_follow_document_order():
    second = RESOLVED.replace("F-B22-1", "F-B22-7")
    third = RESOLVED.replace("F-B22-1", "F-B22-6")
    rotation = plan_findings(_active(RESOLVED, second, third), ARCHIVE_PROLOGUE)

    assert rotation.rotated_ids == ("F-B22-1", "F-B22-7", "F-B22-6")


# ---------------------------------------------------------------------------
# Legacy prose and legacy archives
# ---------------------------------------------------------------------------


def test_legacy_prose_finding_stays_active_and_unreconciled():
    block = "\n".join(
        [
            "### F-B21-26: the Tailwind index dropped its page-entry motion",
            "",
            "Status: resolved locally; deploy before the next production release.",
            "Source: owner report, 2026-08-28.",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert rotation.issues == ()
    assert rotation.rotated_ids == ()
    assert "F-B21-26" in rotation.active_text
    assert "F-B21-26" not in rotation.archive_text


def test_archived_records_without_lifecycle_metadata_remain_readable():
    archive = ARCHIVE_PROLOGUE + "\n".join(
        [
            "## Rotated 2026-09-13 (Batch 21 close-out)",
            "",
            "### F-B19-5: visual-verification tooling -- NO ACTION",
            "",
            "Closed with no lifecycle record; historical shape.",
            "",
        ]
    )
    rotation = plan_findings(_active(RESOLVED), archive)

    assert rotation.issues == ()
    assert rotation.rotated_ids == ("F-B22-1",)
    assert "### F-B19-5: visual-verification tooling -- NO ACTION" in (
        rotation.archive_text
    )
    assert rotation.archive_text.startswith("# FINDINGS Archive")


# ---------------------------------------------------------------------------
# Blocking lifecycle errors
# ---------------------------------------------------------------------------


def test_duplicate_lifecycle_records_block_rotation():
    block = "\n".join(
        [
            "### F-B22-8: two status lines",
            "",
            "- [x] **Status:** resolved",
            "- [x] **Status:** resolved",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC013" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_duplicate_completion_records_block_rotation():
    block = "\n".join(
        [
            "### F-B22-9: two completion lines",
            "",
            "- [x] **Status:** resolved",
            "**Completed:** 2026-09-10",
            "**Completed:** 2026-09-11",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC013" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_checked_record_pending_deployment_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-10: fixed locally, not deployed",
            "",
            "- [x] **Status:** resolved, pending deployment",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC014" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_checked_record_awaiting_acceptance_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-11: awaiting owner acceptance",
            "",
            "- [x] **Status:** resolved, awaiting owner acceptance",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC014" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_checked_open_record_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-12: checked but open",
            "",
            "- [x] **Status:** open",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC015" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_checked_nonterminal_outcome_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-13: checked with an invented outcome",
            "",
            "- [x] **Status:** mitigated",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC015" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_invalid_completion_date_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-14: an impossible date",
            "",
            "- [x] **Status:** resolved",
            "**Completed:** 2026-02-31",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC016" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_non_iso_completion_date_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-15: a non-ISO date",
            "",
            "- [x] **Status:** resolved",
            "**Completed:** 14 September 2026",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC016" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_checked_record_without_completion_date_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-16: no completion date",
            "",
            "- [x] **Status:** resolved",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC016" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_unchecked_record_with_completion_date_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-17: unchecked yet dated",
            "",
            "- [ ] **Status:** open",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC016" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_no_action_without_explanation_blocks_rotation():
    block = "\n".join(
        [
            "### F-B22-18: no action and no reason",
            "",
            "- [x] **Status:** no action",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert "DOC017" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_duplicate_ids_within_the_active_file_block_rotation():
    rotation = plan_findings(_active(RESOLVED, RESOLVED), ARCHIVE_PROLOGUE)

    assert "DOC018" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_active_and_archive_duplicate_ids_block_rotation():
    archive = ARCHIVE_PROLOGUE + "### F-B22-1: an older copy -- RESOLVED\n\nBody.\n"
    rotation = plan_findings(_active(RESOLVED), archive)

    assert "DOC018" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_duplicate_archived_ids_block_rotation():
    archive = ARCHIVE_PROLOGUE + "\n".join(
        [
            "### F-B20-1: one -- RESOLVED",
            "",
            "Body.",
            "",
            "### F-B20-1: two -- RESOLVED",
            "",
            "Body.",
            "",
        ]
    )
    rotation = plan_findings(_active(OPEN), archive)

    assert "DOC018" in _codes(rotation)
    assert rotation.rotated_ids == ()


def test_one_blocking_error_prevents_every_rotation():
    broken = "\n".join(
        [
            "### F-B22-19: broken neighbour",
            "",
            "- [x] **Status:** open",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    active = _active(RESOLVED, broken)
    rotation = plan_findings(active, ARCHIVE_PROLOGUE)

    assert rotation.rotated_ids == ()
    assert rotation.active_text == active
    assert rotation.archive_text == ARCHIVE_PROLOGUE


def test_every_issue_is_an_error_severity_diagnostic_with_a_location():
    block = "\n".join(
        [
            "### F-B22-20: checked but open",
            "",
            "- [x] **Status:** open",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert rotation.issues
    for issue in rotation.issues:
        assert issue.severity == "error"
        assert issue.path == "FINDINGS.md"
        assert issue.line is not None and issue.line > 0
        assert issue.invariant and issue.remediation


def test_planning_is_idempotent():
    first = plan_findings(_active(RESOLVED, OPEN), ARCHIVE_PROLOGUE)
    second = plan_findings(first.active_text, first.archive_text)

    assert second.rotated_ids == ()
    assert second.issues == ()
    assert second.active_text == first.active_text
    assert second.archive_text == first.archive_text


def test_existing_archive_suffix_is_not_appended_twice():
    block = "\n".join(
        [
            "### F-B22-21: already suffixed -- RESOLVED",
            "",
            "- [x] **Status:** resolved",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(_active(block), ARCHIVE_PROLOGUE)

    assert rotation.rotated_ids == ("F-B22-21",)
    assert "-- RESOLVED -- RESOLVED" not in rotation.archive_text


# ---------------------------------------------------------------------------
# DOC023 -- findings that read as finished but carry no lifecycle record
# ---------------------------------------------------------------------------

ROTTED = "\n".join(
    [
        "### F-B21-9: the archive grew without bound",
        "",
        "Resolved in WP-3; rotates at close-out.",
        "",
    ]
)

ROTTED_TAGGED = "\n".join(
    [
        "### F-DOCSYNC-9: the preflight skipped staged deletions",
        "",
        "No action -- the guard covers it already.",
        "",
    ]
)

STILL_OPEN = "\n".join(
    [
        "### F-B21-10: the report omits its provider",
        "",
        "Nothing records which provider produced the miss.",
        "",
    ]
)


def test_rot_is_reported_for_a_finding_with_no_lifecycle_record():
    issues = collect_rot_issues(_active(ROTTED))

    assert [issue.code for issue in issues] == ["DOC023"]
    assert issues[0].severity == "error"
    assert "F-B21-9" in issues[0].remediation


def test_rot_ignores_a_finding_that_carries_its_record():
    """DOC013-DOC018 own a finding once it is written in the canonical shape."""
    assert collect_rot_issues(_active(RESOLVED, OPEN)) == []


def test_rot_ignores_prose_that_claims_no_outcome():
    assert collect_rot_issues(_active(STILL_OPEN)) == []


def test_a_grandfathered_finding_warns_once_with_a_live_count():
    issues = collect_rot_issues(_active(ROTTED, ROTTED_TAGGED), ["F-B21-9"])

    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    assert [issue.remediation.split()[0] for issue in errors] == ["F-DOCSYNC-9"]
    assert len(warnings) == 1
    assert warnings[0].remediation.startswith("1 grandfathered")


def test_a_source_tagged_id_cannot_escape_by_being_tagged():
    """The hole a batch-number boundary would leave open.

    `F-DOCSYNC-9` carries no batch number, so any boundary drawn over batch
    numbers has to put it on one side by default. Admission is by absence
    from an explicit list instead, so a new tag is admitted, not exempt.
    """
    issues = collect_rot_issues(_active(ROTTED_TAGGED))

    assert [issue.severity for issue in issues] == ["error"]
    assert "F-DOCSYNC-9" in issues[0].remediation


def test_the_count_is_derived_not_declared():
    """Shrinking the list is the only way to shrink the reported number."""
    both = collect_rot_issues(
        _active(ROTTED, ROTTED_TAGGED), ["F-B21-9", "F-DOCSYNC-9"]
    )
    one = collect_rot_issues(_active(ROTTED), ["F-B21-9", "F-DOCSYNC-9"])

    assert both[-1].remediation.startswith("2 grandfathered")
    assert one[-1].remediation.startswith("1 grandfathered")


NOT_YET = "\n".join(
    [
        "### F-B21-11: the limiter starves under load",
        "",
        "This is **not yet resolved** -- the fix is written but undeployed.",
        "",
    ]
)


def test_a_finding_saying_it_is_not_resolved_is_not_a_claim():
    """Blocking an honest open finding would teach authors to avoid the word.

    DOC023 reads prose for a terminal outcome, so the one wording it must
    not misread is the negation of that outcome.
    """
    assert collect_rot_issues(_active(NOT_YET)) == []


def test_negation_does_not_reach_across_a_sentence():
    """A 'not' elsewhere in the line cannot suppress a real claim."""
    finding = "\n".join(
        [
            "### F-B21-12: the cache stalls",
            "",
            "We do not know why it happened. Resolved in WP-3.",
            "",
        ]
    )

    assert [issue.code for issue in collect_rot_issues(_active(finding))] == ["DOC023"]


def test_a_deployed_resolution_still_reads_as_a_claim():
    """The lifecycle record's pending vocabulary must not be reused here.

    `PENDING_QUALIFIER_RE` covers 'deploy', which is correct inside a record
    and wrong in a body: this line is a claim, and suppressing it would let
    a resolved finding sit unrecorded.
    """
    finding = "\n".join(
        [
            "### F-B21-13: the worker leaked connections",
            "",
            "Resolved and deployed in WP-3.",
            "",
        ]
    )

    assert [issue.code for issue in collect_rot_issues(_active(finding))] == ["DOC023"]


# DOC023 and the word "closed": read on a legacy status line only.


def _legacy(identifier, *body):
    """Build one finding with no lifecycle record from *body* lines."""
    return "\n".join([f"### {identifier}: a legacy finding", "", *body, ""])


@pytest.mark.parametrize(
    "line",
    [
        "Status: closed. DOC007 and the renderer now share one helper.",
        "Status: Closed -- the check landed in `8ed1650`.",
        "- **Status:** closed",
        "No contract tests exist yet. Status: closed. Source: sweep.",
    ],
    ids=["plain", "capitalised", "bold-bullet", "after-a-sentence"],
)
def test_a_legacy_status_line_opening_with_closed_is_a_claim(line):
    """F-B21-13 said "Status: closed." and sat unrotated, because DOC023
    only knew `resolved` and `no action`. A status label opening with
    "closed" is its author saying the finding is finished."""
    issues = collect_rot_issues(_active(_legacy("F-B21-13", line)))

    assert [issue.code for issue in issues] == ["DOC023"]
    assert "F-B21-13" in issues[0].remediation


# ---------------------------------------------------------------------------
# Task 8: every lifecycle diagnostic prints the declared active-findings path.
# ---------------------------------------------------------------------------

DECLARED_ACTIVE_PATH = "docs/agents/FINDINGS.md"


def test_duplicate_lifecycle_record_uses_declared_active_path():
    block = "\n".join(
        [
            "### F-B22-8: two status lines",
            "",
            "- [x] **Status:** resolved",
            "- [x] **Status:** resolved",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(
        _active(block), ARCHIVE_PROLOGUE, active_path=DECLARED_ACTIVE_PATH
    )

    doc013 = [issue for issue in rotation.issues if issue.code == "DOC013"]
    assert len(doc013) == 1
    assert doc013[0].path == DECLARED_ACTIVE_PATH


def test_pending_deployment_issue_uses_declared_active_path():
    block = "\n".join(
        [
            "### F-B22-10: fixed locally, not deployed",
            "",
            "- [x] **Status:** resolved, pending deployment",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(
        _active(block), ARCHIVE_PROLOGUE, active_path=DECLARED_ACTIVE_PATH
    )

    doc014 = [issue for issue in rotation.issues if issue.code == "DOC014"]
    assert len(doc014) == 1
    assert doc014[0].path == DECLARED_ACTIVE_PATH


def test_checked_open_record_issue_uses_declared_active_path():
    block = "\n".join(
        [
            "### F-B22-12: checked but open",
            "",
            "- [x] **Status:** open",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(
        _active(block), ARCHIVE_PROLOGUE, active_path=DECLARED_ACTIVE_PATH
    )

    doc015 = [issue for issue in rotation.issues if issue.code == "DOC015"]
    assert len(doc015) == 1
    assert doc015[0].path == DECLARED_ACTIVE_PATH


def test_invalid_completion_date_issue_uses_declared_active_path():
    block = "\n".join(
        [
            "### F-B22-14: an impossible date",
            "",
            "- [x] **Status:** resolved",
            "**Completed:** 2026-02-31",
            "",
        ]
    )
    rotation = plan_findings(
        _active(block), ARCHIVE_PROLOGUE, active_path=DECLARED_ACTIVE_PATH
    )

    doc016 = [issue for issue in rotation.issues if issue.code == "DOC016"]
    assert len(doc016) == 1
    assert doc016[0].path == DECLARED_ACTIVE_PATH


def test_no_action_without_explanation_issue_uses_declared_active_path():
    block = "\n".join(
        [
            "### F-B22-18: no action and no reason",
            "",
            "- [x] **Status:** no action",
            "**Completed:** 2026-09-10",
            "",
        ]
    )
    rotation = plan_findings(
        _active(block), ARCHIVE_PROLOGUE, active_path=DECLARED_ACTIVE_PATH
    )

    doc017 = [issue for issue in rotation.issues if issue.code == "DOC017"]
    assert len(doc017) == 1
    assert doc017[0].path == DECLARED_ACTIVE_PATH


def test_duplicate_id_issue_uses_declared_active_path():
    rotation = plan_findings(
        _active(RESOLVED, RESOLVED),
        ARCHIVE_PROLOGUE,
        active_path=DECLARED_ACTIVE_PATH,
    )

    doc018 = [issue for issue in rotation.issues if issue.code == "DOC018"]
    assert doc018
    assert all(issue.path == DECLARED_ACTIVE_PATH for issue in doc018)


def test_rot_issue_uses_declared_active_path():
    issues = collect_rot_issues(_active(ROTTED), active_path=DECLARED_ACTIVE_PATH)

    assert [issue.code for issue in issues] == ["DOC023"]
    assert issues[0].path == DECLARED_ACTIVE_PATH


@pytest.mark.parametrize(
    "line",
    [
        "Status: partly closed. The rest needs an owner ruling.",
        "Status: not closed; the WP-2 half is still open.",
        "Status: open; closes at Batch 21 WP-8.",
        "Batch 21 closed on 2026-09-13 without this work package.",
        "The PR was closed, and its status: closed is only the PR's.",
        "WP-3 closed the gap the audit named; this finding tracks the rest.",
    ],
    ids=[
        "partly",
        "negated",
        "future-tense",
        "batch-closed-in-prose",
        "lower-case-label-in-a-sentence",
        "wp-closed-in-prose",
    ],
)
def test_closed_elsewhere_in_a_finding_is_not_a_claim(line):
    """The owner's concern, 2026-09-21: findings talk about closed batches,
    work packages and PRs all the time. Only the status label is read, and
    only when "closed" is the first thing it says."""
    assert collect_rot_issues(_active(_legacy("F-B21-25", line))) == []
