"""Finding lifecycle parsing and deterministic rotation planning.

A finding is archive-eligible only when its own canonical lifecycle record
says so. Historical prose never checks a box on an author's behalf, and a
contradictory record blocks the whole rotation rather than being repaired by
guesswork: losing or mislabelling a finding is worse than refusing to move it.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
from collections.abc import Sequence

from docsync.archives import ENTRY_BOUNDARY_RE
from docsync.markdown import prose_lines
from docsync.models import IntegrityIssue

#: Where the diagnostics point. Both documents are fixed entry points, so the
#: paths travel with the module rather than being threaded through callers
#: that have no other reason to know them.
ACTIVE_PATH = "FINDINGS.md"
ARCHIVE_PATH = "docs/history/findings/FINDINGS_ARCHIVE.md"

#: `### F-<context>-<N>: title` -- the heading shape AGENTS.md mandates. The
#: ID is captured separately from the title so rotation can append the archive
#: outcome suffix without touching the ID every cross-reference relies on.
FINDING_HEADING_RE = re.compile(r"^###\s+(F-[A-Za-z0-9][A-Za-z0-9_.-]*):\s*(.*?)\s*$")

#: Any Markdown heading ends the preceding finding body. Severity sections
#: (`## P0 -- ...`) separate findings in the active file, so a level-2 heading
#: is as much of a boundary as the next `###`.
ANY_HEADING_RE = re.compile(r"^#{1,6}\s")

#: The one checkbox-bearing status line a canonical lifecycle record carries.
STATUS_LINE_RE = re.compile(
    r"^\s*[-*+]\s+\[([ xX])\]\s+\*\*Status:\*\*\s*(.*?)\s*$",
)

#: The completion date line. Written without a bullet in the approved shape,
#: but a bulleted variant is accepted so an author's list formatting does not
#: silently hide the record from the gate.
COMPLETED_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s+)?\*\*Completed:\*\*\s*(.*?)\s*$",
)

#: A strict ISO calendar date. `date.fromisoformat` alone accepts compact and
#: week-date spellings that no reader of this corpus writes, so the shape is
#: checked before the calendar is.
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: Wording that qualifies an outcome as not yet true in the world: the fix
#: exists locally but is undeployed, uncommitted, or unaccepted. Scanned only
#: inside the lifecycle record, never the body -- a body legitimately
#: discusses deployment, and a false block on prose would train authors to
#: work around the gate.
PENDING_QUALIFIER_RE = re.compile(
    r"\b(?:pending|awaiting|await|unreleased|undeployed|uncommitted|"
    r"not\s+yet|deploy|deployed|deployment|acceptance|accepted)\b",
    re.IGNORECASE,
)

#: The accepted terminal outcomes and the archive heading suffix each takes.
#: The suffixes are the ones already present in the archive, so rotation adds
#: no new vocabulary to a document readers already grep.
_TERMINAL_SUFFIXES = {"resolved": "-- RESOLVED", "no action": "-- NO ACTION"}


@dataclasses.dataclass(frozen=True)
class FindingRotation:
    """A validated, fully computed rotation that a caller may publish."""

    active_text: str
    archive_text: str
    rotated_ids: tuple[str, ...]
    issues: tuple[IntegrityIssue, ...]


@dataclasses.dataclass(frozen=True)
class _Finding:
    """One parsed finding block and its located lifecycle record."""

    identifier: str
    title: str
    lines: tuple[str, ...]
    start: int
    checked: bool | None
    outcome: str
    outcome_line: int | None
    completed: str | None
    completed_line: int | None
    duplicate_records: bool
    body_lines: tuple[str, ...]


def _issue(
    code: str, path: str, line: int | None, invariant: str, remediation: str
) -> IntegrityIssue:
    """Build an error-severity lifecycle diagnostic."""
    return IntegrityIssue(code, "error", path, line, invariant, remediation)


def _normalize_outcome(raw: str) -> str:
    """Fold an outcome to the token the terminal set is written in."""
    folded = re.sub(r"\s+", " ", raw.strip().rstrip(".").lower())
    return "no action" if folded == "no-action" else folded


def _parse(text: str) -> tuple[list[_Finding], list[str]]:
    """Split a findings document into its findings and its raw lines."""
    lines = text.split("\n")
    visible = prose_lines(lines)
    heading_positions = [
        index for index, line in visible if FINDING_HEADING_RE.match(line)
    ]
    boundaries = [index for index, line in visible if ANY_HEADING_RE.match(line)]

    findings: list[_Finding] = []
    for start in heading_positions:
        end = next((index for index in boundaries if index > start), len(lines))
        block = list(lines[start:end])
        while block and not block[-1].strip():
            block.pop()
        findings.append(_build(block, start))
    return findings, lines


def _build(block: list[str], start: int) -> _Finding:
    """Assemble one finding from its block, locating its lifecycle record."""
    heading_match = FINDING_HEADING_RE.match(block[0])
    assert heading_match is not None
    identifier, title = heading_match.group(1), heading_match.group(2)

    # Scan the block through the shared scanner so a lifecycle record quoted
    # inside a fenced example cannot become this finding's real record.
    visible = dict(prose_lines(block))
    status_hits = [
        (offset, match)
        for offset, line in visible.items()
        if (match := STATUS_LINE_RE.match(line)) is not None
    ]
    completed_hits = [
        (offset, match)
        for offset, line in visible.items()
        if (match := COMPLETED_LINE_RE.match(line)) is not None
    ]
    status_hits.sort()
    completed_hits.sort()

    checked: bool | None = None
    outcome = ""
    outcome_line: int | None = None
    if status_hits:
        offset, match = status_hits[0]
        checked = match.group(1).lower() == "x"
        outcome = match.group(2)
        outcome_line = start + offset + 1

    completed: str | None = None
    completed_line: int | None = None
    if completed_hits:
        offset, match = completed_hits[0]
        completed = match.group(1)
        completed_line = start + offset + 1

    record_offsets = {offset for offset, _ in status_hits + completed_hits}
    body_lines = tuple(
        line
        for offset, line in visible.items()
        if offset > 0 and offset not in record_offsets and line.strip()
    )
    return _Finding(
        identifier=identifier,
        title=title,
        lines=tuple(block),
        start=start,
        checked=checked,
        outcome=outcome,
        outcome_line=outcome_line,
        completed=completed,
        completed_line=completed_line,
        duplicate_records=len(status_hits) > 1 or len(completed_hits) > 1,
        body_lines=body_lines,
    )


def _valid_date(raw: str | None) -> bool:
    """Whether the value is a real calendar date written as strict ISO."""
    if raw is None or ISO_DATE_RE.match(raw) is None:
        return False
    try:
        dt.date.fromisoformat(raw)
    except ValueError:
        return False
    return True


def _lifecycle_issues(finding: _Finding) -> list[IntegrityIssue]:
    """Return every blocking lifecycle diagnostic for one finding.

    A finding with no canonical record at all is legacy prose. It is reported
    by neither branch here: the specification is explicit that historical
    wording must not be promoted into a completion claim, so an unreconciled
    record simply stays active.
    """
    issues: list[IntegrityIssue] = []
    line = finding.outcome_line or finding.start + 1

    if finding.duplicate_records:
        issues.append(
            _issue(
                "DOC013",
                ACTIVE_PATH,
                line,
                f"{finding.identifier} carries one lifecycle record.",
                "Keep a single `- [ ] **Status:**` line and at most one "
                "`**Completed:**` line; delete the superseded copies.",
            )
        )

    if finding.checked is None:
        if finding.completed is not None:
            issues.append(
                _issue(
                    "DOC016",
                    ACTIVE_PATH,
                    finding.completed_line,
                    f"{finding.identifier} records a completion date only "
                    "alongside a checked status line.",
                    "Add `- [x] **Status:** resolved` (or `no action`), or "
                    "remove the `**Completed:**` line.",
                )
            )
        return issues

    outcome = _normalize_outcome(finding.outcome)
    if finding.checked:
        if outcome not in _TERMINAL_SUFFIXES:
            if PENDING_QUALIFIER_RE.search(finding.outcome):
                issues.append(
                    _issue(
                        "DOC014",
                        ACTIVE_PATH,
                        line,
                        f"{finding.identifier} is checked while still "
                        "qualified by pending deployment or acceptance.",
                        "Uncheck the box until the qualification is gone, then "
                        "record the bare outcome `resolved` or `no action`.",
                    )
                )
            else:
                issues.append(
                    _issue(
                        "DOC015",
                        ACTIVE_PATH,
                        line,
                        f"{finding.identifier} is checked without a reviewed "
                        "terminal outcome.",
                        "Record `resolved` or `no action` as the whole status "
                        "value, or uncheck the box.",
                    )
                )
        if not _valid_date(finding.completed):
            issues.append(
                _issue(
                    "DOC016",
                    ACTIVE_PATH,
                    finding.completed_line or line,
                    f"{finding.identifier} is checked without a valid ISO "
                    "completion date.",
                    "Add `**Completed:** YYYY-MM-DD` naming a real calendar "
                    "date, or uncheck the box.",
                )
            )
        if outcome == "no action" and not finding.body_lines:
            issues.append(
                _issue(
                    "DOC017",
                    ACTIVE_PATH,
                    line,
                    f"{finding.identifier} claims no action without an "
                    "explanation in its body.",
                    "Explain in the finding body why no action is warranted.",
                )
            )
    elif finding.completed is not None:
        issues.append(
            _issue(
                "DOC016",
                ACTIVE_PATH,
                finding.completed_line,
                f"{finding.identifier} is unchecked while recording a completion date.",
                "Check the box and record a terminal outcome, or remove the "
                "`**Completed:**` line.",
            )
        )
    return issues


def _duplicate_issues(
    active: Sequence[_Finding], archived: Sequence[_Finding]
) -> list[IntegrityIssue]:
    """Report every ID that is not unique across both documents."""
    issues: list[IntegrityIssue] = []
    seen: dict[str, int] = {}
    for finding in active:
        if finding.identifier in seen:
            issues.append(
                _issue(
                    "DOC018",
                    ACTIVE_PATH,
                    finding.start + 1,
                    f"Finding ID {finding.identifier} is unique.",
                    "Give the duplicate its own ID, or merge the two bodies "
                    "into the original finding.",
                )
            )
        seen[finding.identifier] = finding.start
    archived_seen: set[str] = set()
    for finding in archived:
        if finding.identifier in archived_seen:
            issues.append(
                _issue(
                    "DOC018",
                    ARCHIVE_PATH,
                    finding.start + 1,
                    f"Archived finding ID {finding.identifier} appears once.",
                    "Merge the duplicated archive entries; IDs are permanent "
                    "cross-reference keys.",
                )
            )
        archived_seen.add(finding.identifier)
        if finding.identifier in seen:
            issues.append(
                _issue(
                    "DOC018",
                    ACTIVE_PATH,
                    seen[finding.identifier] + 1,
                    f"Finding ID {finding.identifier} lives in exactly one of "
                    "the active and archived documents.",
                    "Remove the stale copy; a rotated finding is archived, not "
                    "duplicated.",
                )
            )
    return issues


def _newest_entry_line(lines: Sequence[str]) -> int:
    """Return the line a newly rotated entry belongs on.

    That is the first entry boundary in the archive -- the newest existing
    entry or rotation banner -- so new entries land above it and the
    prologue stays on top. An archive with no entries yet takes them at the
    end, after its prologue. `archives.ENTRY_BOUNDARY_RE` decides what
    counts as a boundary, because that module paginates this same file and
    the two must not disagree about where one entry stops.
    """
    for index, line in prose_lines(list(lines)):
        if ENTRY_BOUNDARY_RE.match(line):
            return index
    return len(lines)


def _archive_heading(finding: _Finding, outcome: str) -> str:
    """Return the archive heading: the original ID and title plus a suffix."""
    suffix = _TERMINAL_SUFFIXES[outcome]
    title = finding.title
    if title.rstrip().endswith(suffix):
        return f"### {finding.identifier}: {title}"
    return f"### {finding.identifier}: {title} {suffix}".rstrip()


def plan_findings(active_text: str, archive_text: str) -> FindingRotation:
    """Plan the rotation of every archive-eligible finding.

    Returns the two documents as they would be written, the rotated IDs in
    document order, and every blocking diagnostic. Any diagnostic at all
    suppresses the entire rotation and returns both inputs untouched: a
    partially trusted corpus is exactly the state in which moving a finding
    can lose it.
    """
    active, active_lines = _parse(active_text)
    archived, _ = _parse(archive_text)

    issues: list[IntegrityIssue] = []
    for finding in active:
        issues.extend(_lifecycle_issues(finding))
    issues.extend(_duplicate_issues(active, archived))

    eligible = [
        finding
        for finding in active
        if finding.checked
        and not finding.duplicate_records
        and _normalize_outcome(finding.outcome) in _TERMINAL_SUFFIXES
        and _valid_date(finding.completed)
        and (_normalize_outcome(finding.outcome) != "no action" or finding.body_lines)
    ]

    if issues or not eligible:
        return FindingRotation(
            active_text=active_text,
            archive_text=archive_text,
            rotated_ids=(),
            issues=tuple(issues),
        )

    removed: set[int] = set()
    for finding in eligible:
        removed.update(range(finding.start, finding.start + len(finding.lines)))
        # Trailing blank lines belonged to the block's separation, not to the
        # neighbour, so they leave with it.
        cursor = finding.start + len(finding.lines)
        while cursor < len(active_lines) and not active_lines[cursor].strip():
            removed.add(cursor)
            cursor += 1

    new_active = "\n".join(
        line for index, line in enumerate(active_lines) if index not in removed
    )

    archive_lines = archive_text.split("\n")
    while archive_lines and not archive_lines[-1].strip():
        archive_lines.pop()

    rotated_block: list[str] = []
    for finding in eligible:
        outcome = _normalize_outcome(finding.outcome)
        rotated_block.append(_archive_heading(finding, outcome))
        rotated_block.extend(finding.lines[1:])
        rotated_block.append("")

    if rotated_block:
        # The archive states its own order in its prologue -- newest rotation
        # first -- and every manual rotation has honoured it. Appending would
        # bury each new rotation beneath every older one, and would also put
        # the newest entries on the oldest page once this file paginates,
        # because `archives.ArchiveStore` reads the same text newest first.
        newest = _newest_entry_line(archive_lines)
        if newest > 0 and archive_lines[newest - 1].strip():
            # An archive with no entries yet ends at its prologue rule, with
            # no blank line to sit under. Without this the first rotation
            # ever written glues its heading to the `---` above it, and a
            # plain archive reaches disk exactly as planned.
            rotated_block.insert(0, "")
        archive_lines[newest:newest] = rotated_block

    return FindingRotation(
        active_text=new_active,
        archive_text="\n".join(archive_lines) + "\n",
        rotated_ids=tuple(finding.identifier for finding in eligible),
        issues=(),
    )
