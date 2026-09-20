"""Finding lifecycle parsing and rotation planning regressions."""

from docsync.findings import plan_findings

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
