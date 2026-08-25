"""Tests for docsync.declarations: DOC009, DOC010 and DOC011.

Each check exists because a real fact drifted and a reviewer caught it rather
than a gate. The first test in each group reproduces that original defect from
the batch record, so the check is anchored to something that actually happened
and not only to a case invented to make it pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from docsync.declarations import (
    DECLARATIONS_FILENAME,
    DeclarationError,
    _Files,
    check_anchors,
    check_retired,
    check_values,
    collect_declaration_issues,
    load_declarations,
)
from docsync.models import SyncError


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    """Write a throwaway repository and return its root."""
    for rel_path, text in files.items():
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def _files(tmp_path: Path, live: dict[str, list[str]] | None = None) -> _Files:
    return _Files(tmp_path, live or {})


# ----------------------------------------------------------------------
# DOC009 -- values
# ----------------------------------------------------------------------


def test_a_breakpoint_that_drifts_between_a_stylesheet_and_a_script_fails(
    tmp_path: Path,
) -> None:
    """The original defect: CSS moved to 860 and the renderer stayed at 768.

    Widths from 768 to 859 got the mobile frame with the desktop grid scaled
    into it, and no gate could see it because each file was internally
    consistent.
    """
    root = _repo(
        tmp_path,
        {
            "app.css": "@media (max-width: 859.98px) { .x { color: red } }\n",
            "app.js": "const MOBILE_MAX_WIDTH = 768;\n",
        },
    )
    declaration = {
        "name": "the breakpoint",
        "sites": [
            {"file": "app.css", "pattern": r"max-width: 859\.98px"},
            {"file": "app.js", "pattern": r"MOBILE_MAX_WIDTH = 860\b"},
        ],
    }

    issues = check_values(_files(root), [declaration])

    assert [issue.code for issue in issues] == ["DOC009"]
    assert issues[0].path == "app.js"
    assert "no longer states" in issues[0].invariant


def test_sites_that_all_state_the_value_report_nothing(tmp_path: Path) -> None:
    """The check must be silent on correct code, or it stops being read."""
    root = _repo(
        tmp_path,
        {
            "app.css": "@media (max-width: 859.98px) { }\n",
            "app.js": "const MOBILE_MAX_WIDTH = 860;\n",
        },
    )
    declaration = {
        "name": "the breakpoint",
        "sites": [
            {"file": "app.css", "pattern": r"max-width: 859\.98px"},
            {"file": "app.js", "pattern": r"MOBILE_MAX_WIDTH = 860\b"},
        ],
    }

    assert check_values(_files(root), [declaration]) == []


def test_captured_values_that_disagree_are_reported_with_both_readings(
    tmp_path: Path,
) -> None:
    """A pattern with a group compares what it captured, not just presence.

    Both files state a version; they simply state different ones. Presence
    alone would pass this, which is why the capturing form exists.
    """
    root = _repo(
        tmp_path,
        {
            "a.txt": "playwright==1.62.0\n",
            "b.txt": "pinned to playwright==1.55.1 here\n",
        },
    )
    declaration = {
        "name": "the playwright pin",
        "sites": [
            {"file": "a.txt", "pattern": r"playwright==([\d.]+)"},
            {"file": "b.txt", "pattern": r"playwright==([\d.]+)"},
        ],
    }

    issues = check_values(_files(root), [declaration])

    assert len(issues) == 1
    assert "a.txt says 1.62.0" in issues[0].invariant
    assert "b.txt says 1.55.1" in issues[0].invariant
    assert issues[0].line == 1


def test_captured_values_that_agree_report_nothing(tmp_path: Path) -> None:
    """The adversary for the test above: same value, two spellings around it."""
    root = _repo(
        tmp_path,
        {
            "a.txt": "playwright==1.62.0\n",
            "b.txt": "we pin playwright==1.62.0 deliberately\n",
        },
    )
    declaration = {
        "name": "the playwright pin",
        "sites": [
            {"file": "a.txt", "pattern": r"playwright==([\d.]+)"},
            {"file": "b.txt", "pattern": r"playwright==([\d.]+)"},
        ],
    }

    assert check_values(_files(root), [declaration]) == []


def test_a_site_naming_a_file_that_does_not_exist_is_reported(
    tmp_path: Path,
) -> None:
    """A declaration pointing at a deleted file must not pass silently.

    Reported against the declarations file, not the missing one, because that
    is the file the reader has to edit.
    """
    root = _repo(tmp_path, {"a.txt": "value 1\n"})
    declaration = {
        "name": "a value",
        "sites": [
            {"file": "a.txt", "pattern": "value 1"},
            {"file": "gone.txt", "pattern": "value 1"},
        ],
    }

    issues = check_values(_files(root), [declaration])

    assert len(issues) == 1
    assert issues[0].path == DECLARATIONS_FILENAME
    assert "gone.txt" in issues[0].invariant


def test_a_value_declared_at_one_site_is_a_declaration_error(
    tmp_path: Path,
) -> None:
    """One copy cannot disagree with itself, so the declaration is the defect."""
    root = _repo(tmp_path, {"a.txt": "value\n"})
    declaration = {"name": "lonely", "sites": [{"file": "a.txt", "pattern": "value"}]}

    with pytest.raises(DeclarationError, match="cannot disagree with itself"):
        check_values(_files(root), [declaration])


def test_an_unparseable_pattern_blames_the_declaration(tmp_path: Path) -> None:
    """A bad regex is a defect in the gate, not in the document it scanned."""
    root = _repo(tmp_path, {"a.txt": "x\n", "b.txt": "x\n"})
    declaration = {
        "name": "broken",
        "sites": [
            {"file": "a.txt", "pattern": "("},
            {"file": "b.txt", "pattern": "x"},
        ],
    }

    with pytest.raises(DeclarationError, match="not a valid regex"):
        check_values(_files(root), [declaration])


def test_a_later_occurrence_that_drifts_is_caught(tmp_path: Path) -> None:
    """The check reads every occurrence, not the first one it finds.

    index.css carries the breakpoint in three media queries. The first version
    of this check stopped at the first match, so a file could state the value
    once and contradict itself further down and still pass -- which is exactly
    the drift the check exists to catch.
    """
    root = _repo(
        tmp_path,
        {
            "app.css": (
                "@media (max-width: 859.98px) { .a { color: red } }\n"
                ".card { max-width: 380px }\n"
                "@media (max-width: 860px) { .b { color: blue } }\n"
            ),
            "app.js": "const MOBILE_MAX_WIDTH = 860;\n",
        },
    )
    declaration = {
        "name": "the breakpoint",
        "sites": [
            {
                "file": "app.css",
                "pattern": r"@media[^{]*max-width: ([\d.]+)px",
                "expect": "859.98",
            },
            {
                "file": "app.js",
                "pattern": r"MOBILE_MAX_WIDTH = (\d+)",
                "expect": "860",
            },
        ],
    }

    issues = check_values(_files(root), [declaration])

    assert len(issues) == 1
    assert issues[0].line == 3, "must name the drifted query, not the first one"
    assert "expects 859.98" in issues[0].invariant


def test_the_media_prefix_keeps_ordinary_widths_out(tmp_path: Path) -> None:
    """A max-width on an element is a width, not a breakpoint.

    Without the @media prefix the 380px card cap above would read as a third
    breakpoint and fail a correct file.
    """
    root = _repo(
        tmp_path,
        {
            "app.css": (
                "@media (max-width: 859.98px) { .a { color: red } }\n"
                ".card { max-width: 380px }\n"
            ),
            "app.js": "const MOBILE_MAX_WIDTH = 860;\n",
        },
    )
    declaration = {
        "name": "the breakpoint",
        "sites": [
            {
                "file": "app.css",
                "pattern": r"@media[^{]*max-width: ([\d.]+)px",
                "expect": "859.98",
            },
            {
                "file": "app.js",
                "pattern": r"MOBILE_MAX_WIDTH = (\d+)",
                "expect": "860",
            },
        ],
    }

    assert check_values(_files(root), [declaration]) == []


def test_a_file_that_contradicts_itself_is_caught_without_expect(
    tmp_path: Path,
) -> None:
    """Two readings in one file are settled before comparing across files."""
    root = _repo(
        tmp_path,
        {
            "a.txt": "playwright==1.62.0\nand also playwright==1.55.1\n",
            "b.txt": "playwright==1.62.0\n",
        },
    )
    declaration = {
        "name": "the playwright pin",
        "sites": [
            {"file": "a.txt", "pattern": r"playwright==([\d.]+)"},
            {"file": "b.txt", "pattern": r"playwright==([\d.]+)"},
        ],
    }

    issues = check_values(_files(root), [declaration])

    assert len(issues) == 1
    assert "contradicts itself" in issues[0].invariant
    assert "1.55.1, 1.62.0" in issues[0].invariant


def test_expect_without_a_capture_group_is_a_declaration_error(
    tmp_path: Path,
) -> None:
    """Declaring what to expect from a pattern that captures nothing is a typo."""
    root = _repo(tmp_path, {"a.txt": "value\n", "b.txt": "value\n"})
    declaration = {
        "name": "a value",
        "sites": [
            {"file": "a.txt", "pattern": "value", "expect": "value"},
            {"file": "b.txt", "pattern": "value"},
        ],
    }

    with pytest.raises(DeclarationError, match="captures nothing"):
        check_values(_files(root), [declaration])


def test_a_value_that_wraps_across_two_lines_is_still_read(tmp_path: Path) -> None:
    """A media query broken over two lines states the same breakpoint.

    Wrapping is the one edit a file gets for free, from a formatter or from a
    condition growing too long. Reporting it as "no longer states" would send
    the reader to restore a value that is already there.
    """
    root = _repo(
        tmp_path,
        {
            "a.css": "@media (any-pointer: coarse),\n  (max-width: 859.98px) {\n}\n",
            "b.js": "const MOBILE_MAX_WIDTH = 860;\n",
        },
    )
    declaration = {
        "name": "the breakpoint",
        "sites": [
            {
                "file": "a.css",
                "pattern": r"@media[^{]*max-width: ([\d.]+)px",
                "expect": "859.98",
            },
            {"file": "b.js", "pattern": r"MOBILE_MAX_WIDTH = (\d+)", "expect": "860"},
        ],
    }

    assert check_values(_files(root), [declaration]) == []


def test_a_wrapped_occurrence_that_drifts_is_not_hidden_by_an_unwrapped_one(
    tmp_path: Path,
) -> None:
    """The quiet half of the per-line defect, and the reason it matters.

    A file that states the value twice satisfied the check on the unwrapped
    copy while the wrapped one went unread. That is the hole "every
    occurrence" was added to close, still open for any file that wraps.
    """
    root = _repo(
        tmp_path,
        {
            "a.css": (
                "@media (max-width: 859.98px) {\n}\n"
                "@media (any-pointer: coarse),\n  (max-width: 768px) {\n}\n"
            ),
            "b.js": "const MOBILE_MAX_WIDTH = 860;\n",
        },
    )
    declaration = {
        "name": "the breakpoint",
        "sites": [
            {
                "file": "a.css",
                "pattern": r"@media[^{]*max-width: ([\d.]+)px",
                "expect": "859.98",
            },
            {"file": "b.js", "pattern": r"MOBILE_MAX_WIDTH = (\d+)", "expect": "860"},
        ],
    }

    issues = check_values(_files(root), [declaration])

    assert len(issues) == 1
    assert issues[0].path == "a.css"
    assert "768" in issues[0].invariant
    # The line the drifted query starts on, not the line the number sits on.
    assert issues[0].line == 3


# ----------------------------------------------------------------------
# DOC010 -- anchors
# ----------------------------------------------------------------------


ANCHOR_PATTERN = r'`RULES\.md` "([^"]+)"(?: item (\d+))?'


def test_a_citation_of_a_heading_that_moved_is_reported(tmp_path: Path) -> None:
    """The original defect, and the reason a written rule could not catch it.

    The pointer cited the rule by name, which is what the style rule asks for.
    Then the rule moved to a new section in the same commit, so the name
    itself changed and the citation was left resolving to nothing.
    """
    root = _repo(
        tmp_path,
        {
            "RULES.md": "## UI and Accessibility Rules\n\n1. Units.\n",
            "notes.md": 'See `RULES.md` "Proposal and Design Rules" item 6.\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    issues = check_anchors(_files(root), [declaration])

    assert len(issues) == 1
    assert issues[0].code == "DOC010"
    assert issues[0].path == "notes.md"
    assert issues[0].line == 1
    assert "no such heading" in issues[0].invariant


def test_a_citation_of_an_item_beyond_the_list_is_reported(tmp_path: Path) -> None:
    """Renumbering a list breaks every citation of it, silently."""
    root = _repo(
        tmp_path,
        {
            "RULES.md": "## Design Rules\n\n1. One.\n2. Two.\n",
            "notes.md": 'See `RULES.md` "Design Rules" item 6.\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    issues = check_anchors(_files(root), [declaration])

    assert len(issues) == 1
    assert "which has 2 item(s)" in issues[0].invariant


def test_a_citation_that_resolves_reports_nothing(tmp_path: Path) -> None:
    """Non-vacuous partner: the same shape, pointing somewhere real."""
    root = _repo(
        tmp_path,
        {
            "RULES.md": "## Design Rules\n\n1. One.\n2. Two.\n",
            "notes.md": 'See `RULES.md` "Design Rules" item 2.\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    assert check_anchors(_files(root), [declaration]) == []


def test_a_heading_cited_without_its_parenthetical_still_resolves(
    tmp_path: Path,
) -> None:
    """ "Session Bootstrap" must resolve to "Session Bootstrap (in order)".

    Dropping the parenthetical is normal prose, not a broken reference, and
    reporting it would train the reader to ignore this check.
    """
    root = _repo(
        tmp_path,
        {
            "RULES.md": "## Session Bootstrap (in order)\n\n1. One.\n",
            "notes.md": 'See `RULES.md` "Session Bootstrap".\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    assert check_anchors(_files(root), [declaration]) == []


def test_a_bold_lead_in_counts_as_a_citable_place(tmp_path: Path) -> None:
    """The design contract marks its sections in bold rather than with hashes.

    Both spellings are real places in the file, and the trailing sentence
    after the label is not part of the name anyone cites.
    """
    root = _repo(
        tmp_path,
        {
            "RULES.md": "**Wordmark animation -- read this first.** The bars move.\n",
            "notes.md": 'See `RULES.md` "Wordmark animation".\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    assert check_anchors(_files(root), [declaration]) == []


def test_a_bold_lead_in_inside_a_list_item_counts_as_a_citable_place(
    tmp_path: Path,
) -> None:
    """The design contract labels sections both ways, bulleted and not.

    "- **Responsive.** Single breakpoint at 860px." is a section of that
    document. Insisting the asterisks start the line made the WP-3 plan's
    citation of it resolve nowhere, so widening the scan would have reported
    a correct citation as broken.
    """
    root = _repo(
        tmp_path,
        {
            "RULES.md": "- **Responsive.** Single breakpoint at 860px.\n",
            "notes.md": 'See `RULES.md` "Responsive".\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    assert check_anchors(_files(root), [declaration]) == []


def test_a_citation_that_wraps_across_two_lines_is_still_checked(
    tmp_path: Path,
) -> None:
    """A citation broken over two lines is invisible to a per-line search.

    PLAYBOOK.md already carried one, so the gate could not have caught that
    heading moving. The reported line is where the citation starts, which is
    where the reader has to go to fix it.
    """
    root = _repo(
        tmp_path,
        {
            "RULES.md": "## Commit Rules\n\n1. One.\n",
            "notes.md": 'Follow `RULES.md` "UI and\n    Accessibility Rules".\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    issues = check_anchors(_files(root), [declaration])

    assert len(issues) == 1
    assert issues[0].line == 1
    assert "UI and Accessibility Rules" in issues[0].invariant


def test_a_wrapped_citation_that_resolves_reports_nothing(tmp_path: Path) -> None:
    """Joining must not turn correct wrapped prose into a false alarm.

    The continuation line carries the indentation of whatever block it sits
    in. Joining raw lines puts that indentation inside the heading name, so a
    correct citation would resolve nowhere.
    """
    root = _repo(
        tmp_path,
        {
            "RULES.md": "## UI and Accessibility Rules\n\n1. One.\n",
            "notes.md": 'Follow `RULES.md` "UI and\n        Accessibility Rules".\n',
        },
    )
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    assert check_anchors(_files(root), [declaration]) == []


def test_an_anchor_target_that_is_missing_is_reported_once(tmp_path: Path) -> None:
    """A citation into a file that is gone is one declaration defect, not many."""
    root = _repo(tmp_path, {"notes.md": 'See `RULES.md` "Anything".\n'})
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": ["notes.md"],
    }

    issues = check_anchors(_files(root), [declaration])

    assert len(issues) == 1
    assert issues[0].path == DECLARATIONS_FILENAME


# ----------------------------------------------------------------------
# DOC011 -- retired claims
# ----------------------------------------------------------------------


RETIRED = {
    "name": "the old placement",
    "reason": "Reversed on 2026-08-24.",
    "pattern": r"limit_results.{0,80}?(?:inside|into) the thresholds disclosure",
    "scan": ["spec.md", "log.md", "plan.md"],
}


def test_a_reversed_decision_still_prescribed_is_reported(tmp_path: Path) -> None:
    """The original defect: recorded as reversed in one file, live in five.

    An agent reading the canonical bootstrap would have moved the field back.
    """
    root = _repo(
        tmp_path,
        {
            "spec.md": "limit_results is relocated into the thresholds disclosure.\n",
            "log.md": "nothing here\n",
            "plan.md": "nothing here\n",
        },
    )

    issues = check_retired(_files(root), [dict(RETIRED)])

    assert len(issues) == 1
    assert issues[0].code == "DOC011"
    assert issues[0].path == "spec.md"
    assert issues[0].line == 1
    assert "Reversed on 2026-08-24." in issues[0].invariant


def test_a_claim_wrapped_across_two_lines_is_still_found(tmp_path: Path) -> None:
    """Wrapping is the one edit a document gets for free.

    A per-line search can never match a phrase that ends one line and resumes
    on the next, so a normative copy could hide behind ordinary reflow. The
    reported line must be where the phrase starts, not where it finishes.
    """
    root = _repo(
        tmp_path,
        {
            "spec.md": "clean\n",
            "log.md": "clean\n",
            "plan.md": (
                "Some preamble that pushes the phrase onto its own line.\n"
                "The field limit_results is relocated\n"
                "into the thresholds disclosure by decision 3.\n"
            ),
        },
    )

    issues = check_retired(_files(root), [dict(RETIRED)])

    assert len(issues) == 1
    assert issues[0].path == "plan.md"
    assert issues[0].line == 2, "report where the phrase starts"


def test_a_wrapped_claim_below_the_marker_is_still_exempt(tmp_path: Path) -> None:
    """Matching across lines must not defeat the history exemption.

    The adversary for the test above: a wrapped phrase in a dated log entry is
    still history, and joining the document must not move it above the marker.
    """
    root = _repo(
        tmp_path,
        {
            "spec.md": "clean\n",
            "log.md": (
                "## 4. Execution log\n"
                "- 2026-07-24: limit_results kept\n"
                "  inside the thresholds disclosure.\n"
            ),
            "plan.md": "clean\n",
        },
    )
    declaration = dict(RETIRED, allow_after={"log.md": "## 4. Execution log"})

    assert check_retired(_files(root), [declaration]) == []


def test_a_dated_log_entry_below_its_marker_is_left_alone(tmp_path: Path) -> None:
    """History is exempt. What it said that day was true that day.

    Only the part of the file below the marker is exempt, so a stale copy in
    the same file's live prose is still reported -- which is exactly the shape
    PLAYBOOK.md has.
    """
    root = _repo(
        tmp_path,
        {
            "spec.md": "clean\n",
            "plan.md": "clean\n",
            "log.md": (
                "- Next action: limit_results moves into the thresholds "
                "disclosure.\n"
                "## 4. Execution log\n"
                "- 2026-07-24: limit_results kept inside the thresholds "
                "disclosure.\n"
            ),
        },
    )
    declaration = dict(RETIRED, allow_after={"log.md": "## 4. Execution log"})

    issues = check_retired(_files(root), [declaration])

    assert len(issues) == 1, "the live prose above the marker must still fail"
    assert issues[0].line == 1


def test_a_struck_through_claim_is_left_alone(tmp_path: Path) -> None:
    """~~this~~ already says the claim is not current.

    A superseded plan step is often kept struck through with the reversal
    written above it, and deleting it would lose why the step existed.
    """
    root = _repo(
        tmp_path,
        {
            "spec.md": "clean\n",
            "log.md": "clean\n",
            "plan.md": (
                "**REVERSED, do not do this.**\n"
                "~~Move limit_results inside the thresholds disclosure.~~\n"
            ),
        },
    )

    assert check_retired(_files(root), [dict(RETIRED)]) == []


def test_the_strikethrough_exemption_can_be_switched_off(tmp_path: Path) -> None:
    """The exemption is a guess about intent, so it must be declarable.

    Treating ~~this~~ as retired holds in this repository and is a convention
    rather than a rule of Markdown. A corpus that strikes text through
    rhetorically would get a silent blind spot, so the tool must be able to
    stop assuming rather than carry the doctrine into every repository it is
    lifted into.
    """
    root = _repo(
        tmp_path,
        {
            "spec.md": "clean\n",
            "log.md": "clean\n",
            "plan.md": "~~limit_results inside the thresholds disclosure~~\n",
        },
    )

    assert check_retired(_files(root), [dict(RETIRED)]) == []
    assert (
        check_retired(_files(root), [dict(RETIRED)], strikethrough_exempt=False)[0].path
        == "plan.md"
    )


def test_one_declaration_can_override_the_global_strikethrough_option(
    tmp_path: Path,
) -> None:
    """A single claim can be held to a stricter reading than the corpus."""
    root = _repo(
        tmp_path,
        {
            "spec.md": "clean\n",
            "log.md": "clean\n",
            "plan.md": "~~limit_results inside the thresholds disclosure~~\n",
        },
    )
    strict = dict(RETIRED, strikethrough_exempt=False)

    issues = check_retired(_files(root), [strict], strikethrough_exempt=True)

    assert [issue.path for issue in issues] == ["plan.md"]


def test_a_file_exempted_by_glob_is_not_scanned(tmp_path: Path) -> None:
    """The archive keeps grep history and must not be rewritten."""
    root = _repo(
        tmp_path,
        {
            "spec.md": "clean\n",
            "log.md": "clean\n",
            "plan.md": "clean\n",
            "archive/old.md": ("limit_results moves into the thresholds disclosure\n"),
        },
    )
    declaration = dict(
        RETIRED,
        scan=["spec.md", "log.md", "plan.md", "archive/*.md"],
        allow_files=["archive/*"],
    )

    assert check_retired(_files(root), [declaration]) == []


def test_the_exemption_is_scoped_and_does_not_hide_a_live_copy(
    tmp_path: Path,
) -> None:
    """Adversarial: the glob must not be so broad it silences everything.

    Without this, an exemption written to cover the archive could be widened
    to cover the document it was meant to protect the reader from.
    """
    root = _repo(
        tmp_path,
        {
            "spec.md": "limit_results moves into the thresholds disclosure\n",
            "log.md": "clean\n",
            "plan.md": "clean\n",
            "archive/old.md": "limit_results into the thresholds disclosure\n",
        },
    )
    declaration = dict(
        RETIRED,
        scan=["spec.md", "log.md", "plan.md", "archive/*.md"],
        allow_files=["archive/*"],
    )

    issues = check_retired(_files(root), [declaration])

    assert [issue.path for issue in issues] == ["spec.md"]


# ----------------------------------------------------------------------
# Loading and wiring
# ----------------------------------------------------------------------


def test_a_repository_with_no_declarations_file_reports_nothing(
    tmp_path: Path,
) -> None:
    """Every repository starts here, and that is not a failure."""
    assert load_declarations(tmp_path) == {}
    assert collect_declaration_issues(repo_root=tmp_path, live_documents={}) == []


def test_a_malformed_declarations_file_is_a_declaration_error(
    tmp_path: Path,
) -> None:
    """Invalid TOML must name itself rather than surface as a document fault."""
    (tmp_path / DECLARATIONS_FILENAME).write_text("[[value\n", encoding="utf-8")

    with pytest.raises(DeclarationError, match="not valid TOML"):
        load_declarations(tmp_path)


def test_a_declaration_fault_reaches_the_cli_as_a_sync_error() -> None:
    """The CLI has to be able to report it, or the gate ends in a traceback.

    Both `--check` and `--fix` catch SyncError and exit 2. A declaration fault
    raised as anything else ended the run with an unhandled traceback and exit
    1, which reads as "the gate crashed" rather than "the declarations file
    has a typo, and here is the line".
    """
    assert issubclass(DeclarationError, SyncError)


def test_a_declaration_missing_a_required_key_names_the_key(tmp_path: Path) -> None:
    """Reading the key straight out of the mapping raised a bare KeyError.

    That ends the run in a traceback and exit 1, and tells the reader neither
    which declaration is wrong nor what is missing from it.
    """
    root = _repo(tmp_path, {"notes.md": "text\n"})
    declaration = {"name": "rule citations", "pattern": ANCHOR_PATTERN}

    with pytest.raises(DeclarationError, match="has no 'target'"):
        check_anchors(_files(root), [declaration])


def test_a_site_missing_a_key_is_named_by_the_value_that_holds_it(
    tmp_path: Path,
) -> None:
    """A site carries no name, so it is named by its position and its parent."""
    root = _repo(tmp_path, {"a.txt": "value\n", "b.txt": "value\n"})
    declaration = {
        "name": "the breakpoint",
        "sites": [{"pattern": "value"}, {"file": "b.txt", "pattern": "value"}],
    }

    with pytest.raises(DeclarationError, match="site 0 of value 'the breakpoint'"):
        check_values(_files(root), [declaration])


def test_a_misspelled_key_is_refused_rather_than_ignored(tmp_path: Path) -> None:
    """The quietest way this file can be wrong, and the reason for a schema.

    `scans` instead of `scan` parses as valid TOML, is never read, and leaves
    the declaration scanning nothing with the gate green. A check that
    silently stops checking is the failure this whole module exists to
    prevent, so an unknown key is an error rather than a shrug.
    """
    root = _repo(tmp_path, {"RULES.md": "## A\n", "notes.md": "text\n"})
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scans": ["notes.md"],
    }

    with pytest.raises(DeclarationError, match="unknown key 'scans'"):
        check_anchors(_files(root), [declaration])


def test_a_list_written_as_a_bare_string_is_refused(tmp_path: Path) -> None:
    """A string where a list belongs is read one character at a time.

    Every character becomes a path that does not exist, so the declaration
    matches nothing and reports nothing. Silent, like the misspelled key.
    """
    root = _repo(tmp_path, {"RULES.md": "## A\n", "notes.md": "text\n"})
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": "notes.md",
    }

    with pytest.raises(DeclarationError, match="'scan' as str, not a list of str"):
        check_anchors(_files(root), [declaration])


def test_a_non_string_inside_a_list_is_refused(tmp_path: Path) -> None:
    """The container being right does not make its contents right.

    `scan = [1]` is a list, so a shallow check passed it, and the integer then
    reached the glob matcher as a TypeError far from the declaration that
    caused it. Same for a path inside `allow_files`.
    """
    root = _repo(tmp_path, {"RULES.md": "## A\n", "notes.md": "text\n"})
    declaration = {
        "name": "rule citations",
        "target": "RULES.md",
        "pattern": ANCHOR_PATTERN,
        "scan": [1],
    }

    with pytest.raises(DeclarationError, match="item 0 is int, not str"):
        check_anchors(_files(root), [declaration])


def test_a_non_string_allow_after_marker_is_refused(tmp_path: Path) -> None:
    """A marker is searched for inside a line, so it has to be a string."""
    root = _repo(tmp_path, {"notes.md": "text\n"})
    declaration = {
        "name": "r",
        "pattern": "x",
        "scan": ["notes.md"],
        "allow_after": {"notes.md": 5},
    }

    with pytest.raises(DeclarationError, match="'notes.md' is int, not str"):
        check_retired(_files(root), [declaration])


def test_a_site_that_is_not_a_table_is_refused(tmp_path: Path) -> None:
    """`sites` holds tables. An integer in it never reaches a key lookup."""
    root = _repo(tmp_path, {"a.txt": "value\n"})
    declaration = {"name": "a value", "sites": [1, 2]}

    with pytest.raises(DeclarationError, match="item 0 is int, not dict"):
        check_values(_files(root), [declaration])


def test_a_retired_declaration_is_held_to_the_schema_too(tmp_path: Path) -> None:
    """All three kinds validate, so a typo cannot hide in the third one."""
    root = _repo(tmp_path, {"notes.md": "text\n"})
    declaration = {"name": "r", "pattern": "x", "allow_file": ["notes.md"]}

    with pytest.raises(DeclarationError, match="unknown key 'allow_file'"):
        check_retired(_files(root), [declaration])


def test_an_unknown_table_name_is_refused(tmp_path: Path) -> None:
    """A misspelled [[ancor]] parses, is never read, and runs one fewer check."""
    (tmp_path / DECLARATIONS_FILENAME).write_text(
        '[[ancor]]\nname = "x"\n', encoding="utf-8"
    )

    with pytest.raises(DeclarationError, match="unknown table 'ancor'"):
        collect_declaration_issues(repo_root=tmp_path, live_documents={})


def test_a_misspelled_option_is_refused(tmp_path: Path) -> None:
    """The quietest fault of all: the real option keeps its default.

    `strikethough_exempt` leaves every retired claim exempt that the author
    meant to expose, and nothing anywhere says so.
    """
    (tmp_path / DECLARATIONS_FILENAME).write_text(
        "[options]\nstrikethough_exempt = true\n", encoding="utf-8"
    )

    with pytest.raises(DeclarationError, match="unknown key 'strikethough_exempt'"):
        collect_declaration_issues(repo_root=tmp_path, live_documents={})


def test_the_in_memory_copy_wins_over_the_file_on_disk(tmp_path: Path) -> None:
    """The gate grades documents it may have just rewritten in memory.

    Reading from disk here would grade the previous version and pass a
    document the run itself had already fixed, or fail one it had broken.
    """
    root = _repo(tmp_path, {"a.md": "stale text\n", "b.md": "fresh text\n"})
    declaration = {
        "name": "a value",
        "sites": [
            {"file": "a.md", "pattern": "fresh text"},
            {"file": "b.md", "pattern": "fresh text"},
        ],
    }

    on_disk = check_values(_files(root), [declaration])
    in_memory = check_values(_files(root, {"a.md": ["fresh text"]}), [declaration])

    assert [issue.path for issue in on_disk] == ["a.md"]
    assert in_memory == []


def test_collect_runs_all_three_kinds_and_sorts_them(tmp_path: Path) -> None:
    """One malformed fact of each kind, reported together in a stable order."""
    root = _repo(
        tmp_path,
        {
            DECLARATIONS_FILENAME: (
                "[[value]]\n"
                'name = "a value"\n'
                "[[value.sites]]\n"
                'file = "a.md"\n'
                "pattern = 'present'\n"
                "[[value.sites]]\n"
                'file = "b.md"\n'
                "pattern = 'present'\n"
                "\n"
                "[[anchor]]\n"
                'name = "citations"\n'
                'target = "RULES.md"\n'
                'pattern = \'`RULES\\.md` "([^"]+)"\'\n'
                'scan = ["a.md"]\n'
                "\n"
                "[[retired]]\n"
                'name = "an old claim"\n'
                "pattern = 'old claim'\n"
                'scan = ["b.md"]\n'
            ),
            "RULES.md": "## Real Heading\n",
            "a.md": 'present, and see `RULES.md` "Missing Heading"\n',
            "b.md": "an old claim lives here\n",
        },
    )

    issues = collect_declaration_issues(repo_root=root, live_documents={})

    assert [issue.code for issue in issues] == ["DOC010", "DOC009", "DOC011"]
    assert [issue.path for issue in issues] == ["a.md", "b.md", "b.md"]
