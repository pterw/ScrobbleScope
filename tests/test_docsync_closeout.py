"""Tests for docsync.closeout: the definition-side close-out record (DOC019).

The record exists because a closed batch's evidence has to survive later edits
to the definition it was written from. Deleting a work package after closure
would erase the fact that the batch ever planned it, so the recorded set and the
declared set are compared in both directions rather than trusting either alone.
"""

from __future__ import annotations

from docsync.closeout import (
    ABSORBED,
    ACTIVE,
    CLOSEOUT_END_MARKER,
    CLOSEOUT_START_MARKER,
    COMPLETE,
    DROPPED,
    _claim_issues,
    collect_definition_issues,
    collect_transition_issues,
    parse_wp_dispositions,
    read_closeout_record,
    render_closeout_record,
)
from docsync.declarations import CloseoutConfig

ARCHIVED_PATH = "docs/history/definitions/BATCH9_DEFINITION.md"


def _config(admit_from_batch: int = 1) -> CloseoutConfig:
    return CloseoutConfig(admit_from_batch)


def _definition(*headings: str) -> list[str]:
    """A definition body whose work packages are exactly ``headings``."""
    return [
        "# BATCH9: A batch",
        "",
        "**Status:** Active.",
        "",
        "## Work packages",
        "",
        *headings,
    ]


def _tracked(*extra: str) -> frozenset[str]:
    return frozenset({ARCHIVED_PATH, "PLAYBOOK.md", *extra})


def _issues(
    definition_lines: list[str] | None,
    *,
    batch: int = 9,
    definition_path: str = ARCHIVED_PATH,
    tracked_paths: frozenset[str] | None = None,
    config: CloseoutConfig | None = None,
) -> list:
    return collect_definition_issues(
        batch=batch,
        definition_path=definition_path,
        definition_lines=definition_lines,
        tracked_paths=_tracked() if tracked_paths is None else tracked_paths,
        config=_config() if config is None else config,
    )


def test_legacy_batch_below_the_boundary_is_admitted_as_it_stands() -> None:
    """A batch that closed before the signals existed is not asked for them.

    This is the nonretroactive admission boundary. Batch 21's own definition
    still reads ``**Status:** Active.`` and split WP-8 to Batch 23, so demanding
    a close-out record from it would mean either rewriting history or inventing
    the record the check is supposed to find.
    """
    definition = _definition("### WP-0 -- one", "### WP-1 -- two")
    assert _issues(definition, batch=21, config=_config(22)) == []


def test_managed_closed_batch_without_a_record_is_reported() -> None:
    """A hand-written closure claim is not evidence; the record is."""
    issues = _issues(_definition("### WP-0 -- one"))

    assert [issue.code for issue in issues] == ["DOC019"]
    assert "close-out record" in issues[0].invariant
    assert "--close-batch 9" in issues[0].remediation


def test_exact_record_clears_a_managed_batch() -> None:
    definition = _definition(
        "### ~~WP-0 -- one~~ -- **DONE**",
        "### ~~WP-1 -- two~~ -- **DONE**",
    )
    record = render_closeout_record(9, "2026-09-18", parse_wp_dispositions(definition))

    assert _issues([*definition, "", *record]) == []


def test_record_that_lost_a_work_package_is_reported() -> None:
    """A WP added after closure cannot be covered by the old record."""
    definition = _definition(
        "### ~~WP-0 -- one~~ -- **DONE**",
        "### WP-1 -- added later",
    )
    record = render_closeout_record(9, "2026-09-18", parse_wp_dispositions([]))

    issues = _issues([*definition, "", *record])

    assert [issue.code for issue in issues] == ["DOC019"]
    assert "WP-1" in issues[0].invariant


def test_work_package_deleted_after_closure_cannot_hide() -> None:
    """The recorded set is the guard against a later deletion.

    Deleting WP-1 from the definition shrinks the declared set. Compared only
    one way, that deletion would read as a clean closure.
    """
    closed = _definition(
        "### ~~WP-0 -- one~~ -- **DONE**",
        "### ~~WP-1 -- two~~ -- **DONE**",
    )
    record = render_closeout_record(9, "2026-09-18", parse_wp_dispositions(closed))
    edited = _definition("### ~~WP-0 -- one~~ -- **DONE**")

    issues = _issues([*edited, "", *record])

    assert [issue.code for issue in issues] == ["DOC019"]
    assert "WP-1" in issues[0].invariant


def test_state_changed_after_closure_is_reported() -> None:
    """Reopening a work package silently would leave the record claiming done."""
    closed = _definition("### ~~WP-0 -- one~~ -- **DONE**")
    record = render_closeout_record(9, "2026-09-18", parse_wp_dispositions(closed))
    reopened = _definition("### WP-0 -- one")

    issues = _issues([*reopened, "", *record])

    assert [issue.code for issue in issues] == ["DOC019"]
    assert "WP-0" in issues[0].invariant


def test_absorbed_work_package_needs_a_reference() -> None:
    """An absorbed WP must say where it went, or the work is untraceable."""
    absorbed = "### WP-6 -- seam removal (ABSORBED INTO WP-3, 2026-08-23)"
    without = _issues(_definition("### WP-6 -- absorbed into another place"))
    with_reference = _issues(
        [
            *_definition(absorbed),
            "",
            *render_closeout_record(
                9, "2026-09-18", parse_wp_dispositions(_definition(absorbed))
            ),
        ]
    )

    assert [issue.code for issue in without] == ["DOC019"]
    assert "reference" in without[0].invariant
    assert with_reference == []


def test_conflicting_root_definition_is_reported() -> None:
    """A closed batch keeping a root definition is an unfinished transition."""
    definition = _definition("### ~~WP-0 -- one~~ -- **DONE**")
    record = render_closeout_record(9, "2026-09-18", parse_wp_dispositions(definition))

    issues = _issues(
        [*definition, "", *record],
        tracked_paths=_tracked("BATCH9_DEFINITION.md"),
    )

    assert [issue.code for issue in issues] == ["DOC019"]
    assert "root" in issues[0].invariant


def test_definition_outside_the_archived_location_is_reported() -> None:
    root_path = "BATCH9_DEFINITION.md"
    definition = _definition("### ~~WP-0 -- one~~ -- **DONE**")
    record = render_closeout_record(9, "2026-09-18", parse_wp_dispositions(definition))

    issues = _issues([*definition, "", *record], definition_path=root_path)

    assert [issue.code for issue in issues] == ["DOC019"]
    assert "docs/history/definitions/" in issues[0].remediation


def test_missing_definition_is_reported_once() -> None:
    issues = _issues(None)

    assert [issue.code for issue in issues] == ["DOC019"]
    assert "archived definition" in issues[0].invariant


def test_wp_states_are_read_from_the_heading_itself() -> None:
    dispositions = parse_wp_dispositions(
        _definition(
            "### ~~WP-0 -- done by strikethrough~~",
            "### WP-1 -- done by marker -- **DONE**",
            "### WP-2 -- still going",
            "### WP-6 -- seam removal (ABSORBED INTO WP-3, 2026-08-23)",
            "### WP-7 -- dropped",
        )
    )

    assert [(item.number, item.state) for item in dispositions] == [
        (0, COMPLETE),
        (1, COMPLETE),
        (2, ACTIVE),
        (6, ABSORBED),
        (7, DROPPED),
    ]
    assert dispositions[3].reference == 3


def test_fenced_work_package_example_is_not_a_declaration() -> None:
    """A fenced sample heading is an example, never a planned work package."""
    definition = [
        *_definition("### WP-0 -- one"),
        "",
        "```markdown",
        "### WP-9 -- an example heading",
        "```",
    ]

    assert [item.number for item in parse_wp_dispositions(definition)] == [0]


def test_record_round_trips() -> None:
    """Rendering then reading reproduces the dispositions exactly.

    A record the tooling cannot read back is one it cannot compare, so the
    round trip is the property that makes the snapshot usable.
    """
    dispositions = parse_wp_dispositions(
        _definition(
            "### ~~WP-0 -- one~~ -- **DONE**",
            "### WP-6 -- seam removal (ABSORBED INTO WP-3, 2026-08-23)",
        )
    )
    record = render_closeout_record(9, "2026-09-18", dispositions)

    body = [*_definition("### WP-0 -- one"), "", *record]
    parsed = read_closeout_record(body)

    assert parsed is not None
    assert parsed.batch == 9
    assert parsed.closed_on == "2026-09-18"
    assert parsed.dispositions == dispositions
    assert CLOSEOUT_START_MARKER in record
    assert CLOSEOUT_END_MARKER in record


def test_absent_record_reads_as_none() -> None:
    assert read_closeout_record(_definition("### WP-0 -- one")) is None


# ---------------------------------------------------------------------------
# Task 8: the pre-transition refusals name the playbook's declared path.
# ---------------------------------------------------------------------------


def test_claim_issues_use_the_declared_playbook_path() -> None:
    """DOC019's PLAYBOOK-side pre-transition signals print the declared path."""
    playbook_lines = [
        "## 3. Active batch + next action",
        "",
        "- **Batch 9 is active.** Definition: `BATCH9_DEFINITION.md`.",
    ]

    issues = _claim_issues(
        9, playbook_lines, playbook_relative_path="docs/agents/PLAYBOOK.md"
    )

    assert len(issues) == 3
    assert all(issue.path == "docs/agents/PLAYBOOK.md" for issue in issues)


def test_admission_issue_uses_the_declared_playbook_path() -> None:
    """A batch below the admission boundary is refused at its declared path."""
    issues = collect_transition_issues(
        batch=9,
        playbook_lines=["# PLAYBOOK"],
        session_lines=None,
        session_path=".claude/SESSION_CONTEXT.md",
        definition_path=ARCHIVED_PATH,
        definition_lines=None,
        tracked_paths=_tracked(),
        config=_config(30),
        playbook_relative_path="docs/agents/PLAYBOOK.md",
    )

    assert [(issue.code, issue.path) for issue in issues] == [
        ("DOC019", "docs/agents/PLAYBOOK.md")
    ]
