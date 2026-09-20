"""Close-out records for a batch definition, and the diagnostics that police them.

A closure is claimed in several documents at once, but the evidence it leaves
behind has to survive later edits to the document it was written from. This
module owns that evidence: a record, written into the archived definition, that
names every work package the batch planned and the terminal state each reached.

The comparison runs in both directions on purpose. Checking only "every recorded
WP still exists" would let a WP be added after closure and never be accounted
for; checking only "every declared WP is recorded" would let a WP be deleted
after closure and hide that the batch ever planned it. Either way DOC019 fires.

Scope: this is the definition-side half of close-out validation. The other
signals -- the PLAYBOOK claim, the dashboard, the batch index, the archived
location and eligible findings -- are composed by the caller, which is why this
module is handed the batch number and the tracked paths instead of reading
documents itself.
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Sequence

from docsync.declarations import CloseoutConfig
from docsync.markdown import marker_lines, prose_lines
from docsync.models import IntegrityIssue, SyncError
from docsync.parser import (
    SECTION_3_RE,
    _find_section,
    _parse_active_batch_state,
    closed_batch_claims,
    root_definition_pattern,
)

#: The managed block a closure writes into its archived definition. The names
#: follow the `DOCSYNC:<NAME>` shape `markdown.marker_lines` recognizes, so a
#: marker quoted inside a fenced example stays an example and never becomes a
#: boundary the reader trusts.
CLOSEOUT_START_MARKER = "<!-- DOCSYNC:CLOSEOUT -->"
CLOSEOUT_END_MARKER = "<!-- DOCSYNC:CLOSEOUT-END -->"

#: Where a closed batch's definition belongs.
ARCHIVED_DEFINITIONS_DIR = "docs/history/definitions/"

#: The terminal states a work package can reach, as its heading states them.
COMPLETE = "complete"
ACTIVE = "active"
ABSORBED = "absorbed"
DROPPED = "dropped"

#: A work-package heading, struck-through form included: this repository marks a
#: finished package `### ~~WP-0 -- ...~~ -- **DONE**`.
#:
#: The heading shape is deliberately re-derived here rather than imported from
#: `integrity._definition_wp_numbers`, which asks a different question. That one
#: excludes struck headings from the *planned* set, and its rule is what DOC007
#: compares against. A close-out record has to see them, because a struck
#: heading is precisely the terminal record for that package. Consolidating the
#: two would silently change which work packages DOC007 demands.
_WP_HEADING_RE = re.compile(r"^###\s+(?:\*\*)?(~~)?WP-(\d+)\b", re.IGNORECASE)
_WP_ABSORBED_RE = re.compile(r"\b(?:absorbed\s+into|merged\s+into)\b", re.IGNORECASE)
_WP_DROPPED_RE = re.compile(r"\bdropped\b", re.IGNORECASE)
_WP_DONE_RE = re.compile(r"\*\*DONE\*\*", re.IGNORECASE)
_WP_REFERENCE_RE = re.compile(r"\bWP-(\d+)\b", re.IGNORECASE)
_RECORD_HEADER_RE = re.compile(r"^- Batch (\d+) closed (\d{4}-\d{2}-\d{2})\s*$")
_RECORD_ENTRY_RE = re.compile(
    r"^- WP-(\d+) (complete|active|dropped|absorbed into WP-(\d+))\s*$",
    re.IGNORECASE,
)


@dataclasses.dataclass(frozen=True)
class WPDisposition:
    """One work package's state, as its definition heading states it.

    ``line`` is provenance for the diagnostic, not identity: two dispositions
    compare equal when they describe the same package in the same state, which
    is what lets a record be compared against the definition it came from even
    though the two sit at different line numbers.
    """

    number: int
    state: str
    reference: int | None = None
    line: int = dataclasses.field(default=0, compare=False)


@dataclasses.dataclass(frozen=True)
class CloseoutRecord:
    """The recorded closure of one batch: when it closed and what it closed."""

    batch: int
    closed_on: str
    dispositions: tuple[WPDisposition, ...]
    line: int = dataclasses.field(default=0, compare=False)


def _describe(disposition: WPDisposition) -> str:
    """Name a state the way a reader would write it in the record."""
    if disposition.state == ABSORBED:
        return f"absorbed into WP-{disposition.reference}"
    return disposition.state


def _state_of(heading: str, *, struck: bool) -> str:
    """Classify one heading, absorbed and dropped before finished.

    Order matters: Batch 21's absorbed stub is titled
    ``### WP-6 -- ... (ABSORBED INTO WP-3)``, and reading a completion marker
    first would file absorbed work as complete.
    """
    if _WP_ABSORBED_RE.search(heading) is not None:
        return ABSORBED
    if _WP_DROPPED_RE.search(heading) is not None:
        return DROPPED
    if struck or _WP_DONE_RE.search(heading) is not None:
        return COMPLETE
    return ACTIVE


def _reference_of(heading: str, number: int) -> int | None:
    """Return the package an absorbed heading names, if it names one."""
    for match in _WP_REFERENCE_RE.finditer(heading):
        target = int(match.group(1))
        if target != number:
            return target
    return None


def parse_wp_dispositions(
    definition_lines: Sequence[str],
) -> tuple[WPDisposition, ...]:
    """Return every work package a definition declares, with its state.

    Fenced examples are skipped, so a `### WP-9` inside a code block is a sample
    heading rather than a package the batch promised to ship.
    """
    dispositions: list[WPDisposition] = []
    for index, text in prose_lines(definition_lines):
        heading = _WP_HEADING_RE.match(text)
        if heading is None:
            continue
        number = int(heading.group(2))
        dispositions.append(
            WPDisposition(
                number=number,
                state=_state_of(text, struck=heading.group(1) is not None),
                reference=_reference_of(text, number),
                line=index + 1,
            )
        )
    return tuple(dispositions)


def render_closeout_record(
    batch: int, closed_on: str, dispositions: Sequence[WPDisposition]
) -> list[str]:
    """Render the managed block a closure writes into its definition.

    One entry per line, so the block stays readable in a diff and a package that
    was never recorded cannot hide behind a separator. Sorted by number, so the
    record does not depend on the order the headings happened to appear in.
    """
    entries = [
        f"- WP-{item.number} {_describe(item)}"
        for item in sorted(dispositions, key=lambda item: item.number)
    ]
    return [
        CLOSEOUT_START_MARKER,
        f"- Batch {batch} closed {closed_on}",
        *entries,
        CLOSEOUT_END_MARKER,
    ]


def _entry_state(text: str) -> str:
    """Return the state an entry's own words name."""
    lowered = text.casefold()
    return ABSORBED if lowered.startswith("absorbed") else lowered


def _parse_record_block(block: Sequence[str], start: int) -> CloseoutRecord | None:
    """Parse what sits between the markers, or None when it is not a record.

    Strict on purpose: unrecognized text makes the block unreadable rather than
    half-read, because a record the tooling only partly understands is one it
    would compare partly, and the remainder would read as agreement.
    """
    lines = [line.strip() for line in block if line.strip()]
    if not lines:
        return None
    header = _RECORD_HEADER_RE.match(lines[0])
    if header is None:
        return None
    dispositions: list[WPDisposition] = []
    for offset, line in enumerate(lines[1:], start=1):
        entry = _RECORD_ENTRY_RE.match(line)
        if entry is None:
            return None
        dispositions.append(
            WPDisposition(
                number=int(entry.group(1)),
                state=_entry_state(entry.group(2)),
                reference=int(entry.group(3)) if entry.group(3) else None,
                line=start + offset,
            )
        )
    return CloseoutRecord(
        batch=int(header.group(1)),
        closed_on=header.group(2),
        dispositions=tuple(dispositions),
        line=start,
    )


def read_closeout_record(definition_lines: Sequence[str]) -> CloseoutRecord | None:
    """Return the definition's close-out record, or None when it has none.

    An unterminated or malformed block reads as absent, not as agreement. The
    remedy a caller prints for an absent record -- close the batch again, which
    rewrites the block from the definition -- repairs a corrupt one too, so the
    two states need no separate diagnostic.
    """
    markers = marker_lines(definition_lines)
    for position, (line_number, text) in enumerate(markers):
        if text.strip() != CLOSEOUT_START_MARKER:
            continue
        for end_number, end_text in markers[position + 1 :]:
            if end_text.strip() != CLOSEOUT_END_MARKER:
                continue
            block = definition_lines[line_number + 1 : end_number]
            return _parse_record_block(block, line_number + 1)
        return None
    return None


def _issue(
    path: str, line: int | None, invariant: str, remediation: str
) -> IntegrityIssue:
    """Build one DOC019 diagnostic in the shape the gate already renders."""
    return IntegrityIssue(
        code="DOC019",
        severity="error",
        path=path,
        line=line,
        invariant=invariant,
        remediation=remediation,
    )


def _set_mismatch(
    batch: int,
    path: str,
    declared: Sequence[WPDisposition],
    record: CloseoutRecord,
) -> IntegrityIssue | None:
    """Report a recorded set that does not match the declared set, either way."""
    declared_numbers = {item.number for item in declared}
    recorded_numbers = {item.number for item in record.dispositions}
    if declared_numbers == recorded_numbers:
        return None
    parts = [
        f"WP-{number} is declared but not recorded"
        for number in sorted(declared_numbers - recorded_numbers)
    ] + [
        f"WP-{number} is recorded but no longer declared"
        for number in sorted(recorded_numbers - declared_numbers)
    ]
    return _issue(
        path,
        record.line or None,
        f"The close-out record for Batch {batch} covers exactly the work "
        f"packages the definition declares ({'; '.join(parts)}).",
        "Restore the work package, or reopen the batch and close it again so "
        "the record states what was actually planned.",
    )


def _state_mismatch(
    batch: int,
    path: str,
    declared: Sequence[WPDisposition],
    record: CloseoutRecord,
) -> IntegrityIssue | None:
    """Report a package whose state or absorption target moved after closure."""
    recorded_by_number = {item.number: item for item in record.dispositions}
    for item in declared:
        recorded = recorded_by_number.get(item.number)
        if recorded is None or recorded == item:
            continue
        return _issue(
            path,
            item.line,
            f"The recorded state for WP-{item.number} of Batch {batch} matches "
            f"the definition (recorded: {_describe(recorded)}, "
            f"declared: {_describe(item)}).",
            "Restore the recorded state, or reopen the batch so the change is "
            "recorded deliberately rather than silently.",
        )
    return None


def collect_definition_issues(
    *,
    batch: int,
    definition_path: str,
    definition_lines: Sequence[str] | None,
    tracked_paths: frozenset[str],
    config: CloseoutConfig,
) -> list[IntegrityIssue]:
    """Report DOC019 for one batch's definition-side close-out evidence.

    A batch below the configured admission boundary returns nothing. It closed
    before these signals existed, so asking it for a record now would demand
    evidence that was never written rather than check evidence that was, and the
    only ways to satisfy such a demand are to rewrite history or invent the
    record. The boundary is what keeps that from happening; above it, every
    signal is evaluated.
    """
    if batch < config.admit_from_batch:
        return []

    issues: list[IntegrityIssue] = []
    if (
        not definition_path.startswith(ARCHIVED_DEFINITIONS_DIR)
        or definition_path not in tracked_paths
    ):
        issues.append(
            _issue(
                definition_path,
                None,
                "A closed batch's definition is archived under "
                "docs/history/definitions/.",
                f"Move the definition to "
                f"`{ARCHIVED_DEFINITIONS_DIR}BATCH{batch}_DEFINITION.md` and "
                "point PLAYBOOK's batch index at the archived path.",
            )
        )

    root_definition_re = root_definition_pattern(batch)
    for path in sorted(tracked_paths):
        if "/" not in path and root_definition_re.fullmatch(path) is not None:
            issues.append(
                _issue(
                    path,
                    None,
                    "No conflicting root definition remains for a closed batch.",
                    f"Archive `{path}`. A root definition for a closed batch is "
                    "an unfinished transition, not an open batch.",
                )
            )
            break

    if definition_lines is None:
        return [
            *issues,
            _issue(
                definition_path,
                None,
                "The archived definition for a closed batch exists.",
                f"Restore `{definition_path}`, or reopen the batch in PLAYBOOK "
                "Section 3.",
            ),
        ]

    dispositions = parse_wp_dispositions(definition_lines)
    for item in dispositions:
        if item.state == ABSORBED and item.reference is None:
            return [
                *issues,
                _issue(
                    definition_path,
                    item.line or None,
                    "An absorbed work package carries a disposition reference to "
                    "the package that took it on.",
                    f"Name the target, e.g. `### WP-{item.number} -- ... "
                    "(ABSORBED INTO WP-N)`.",
                ),
            ]

    record = read_closeout_record(definition_lines)
    if record is None:
        return [
            *issues,
            _issue(
                definition_path,
                None,
                "A closed batch's definition carries a close-out record.",
                f"Run `python scripts/doc_state_sync.py --close-batch {batch}` "
                "once the completion evidence is written.",
            ),
        ]

    for mismatch in (
        _set_mismatch(batch, definition_path, dispositions, record),
        _state_mismatch(batch, definition_path, dispositions, record),
    ):
        if mismatch is not None:
            return [*issues, mismatch]
    return issues


# ----------------------------------------------------------------------
# The transition itself: the signals a close-out is allowed to proceed on,
# and the two managed renderings it writes.
#
# `collect_definition_issues` above polices a closure that has already
# happened, from the archived definition alone. Everything below is the
# other half: what must be true *before* one happens. The two are kept
# apart because they answer to different readers -- the gate runs the first
# on every check, while the second runs only when an operator asks for the
# transition -- but they share one code, because to a reader "the close-out
# is wrong" is a single concern whichever side reported it.
# ----------------------------------------------------------------------

#: One row of PLAYBOOK's batch index: number, title, definition, log. The
#: shape is a four-column table keyed by the batch number, which is all this
#: module assumes; the column *contents* are never parsed, only replaced, so a
#: repository whose titles read differently still closes out correctly.
BATCH_INDEX_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$")

#: The dashboard's per-batch status row. Deliberately the same shape
#: `integrity.SESSION_BATCH_STATUS_ROW_RE` already reads, so the document that
#: satisfies one check satisfies the other.
DASHBOARD_STATUS_ROW_RE = re.compile(
    r"^\|\s*Batch\s+(\d+)\s+status\s*\|\s*(.*?)\s*\|\s*$", re.IGNORECASE
)

#: What a dashboard cell has to say for the batch to count as closed. Narrow
#: on purpose: "complete" is the word this corpus writes, and widening it to
#: anything that merely is not "active" would let an empty cell, a dash, or a
#: half-written "closing" read as agreement.
_DASHBOARD_COMPLETE_RE = re.compile(r"\bcomplete", re.IGNORECASE)


def _section_3(playbook_lines: Sequence[str]) -> list[str]:
    """Return PLAYBOOK Section 3's lines, or nothing when it has none."""
    try:
        start, end = _find_section(list(playbook_lines), SECTION_3_RE, "PLAYBOOK")
    except SyncError:
        return []
    return list(playbook_lines[start:end])


def find_batch_index_row(playbook_lines: Sequence[str], batch: int) -> int | None:
    """Return the zero-based line of this batch's index row, if it has one."""
    for index, text in prose_lines(list(playbook_lines)):
        match = BATCH_INDEX_ROW_RE.match(text)
        if match is not None and int(match.group(1)) == batch:
            return index
    return None


def render_batch_index_row(row: str, definition_path: str, log_path: str) -> str:
    """Return the index row with its definition and log cells repointed.

    Only the two reference cells are rewritten. The batch number and the
    title are the author's words, and a close-out that restated them would be
    writing history rather than recording where it now lives.
    """
    match = BATCH_INDEX_ROW_RE.match(row)
    if match is None:
        raise SyncError(f"Not a batch index row: {row!r}")
    return (
        f"| {match.group(1).strip()} |{match.group(2)}"
        f"| `{definition_path}` | `{log_path}` |"
    )


def render_archived_definition(
    definition_lines: Sequence[str], batch: int, closed_on: str
) -> list[str]:
    """Return the definition as it is archived, carrying its close-out record.

    An existing managed block is replaced rather than appended to, so closing
    a batch twice leaves one record and the operation is idempotent. Nothing
    else in the document is touched: the record states what the headings
    already say, and this function never edits a heading to make them agree.
    """
    lines = list(definition_lines)
    markers = marker_lines(lines)
    start = next(
        (number for number, text in markers if text.strip() == CLOSEOUT_START_MARKER),
        None,
    )
    if start is not None:
        end = next(
            (
                number
                for number, text in markers
                if number > start and text.strip() == CLOSEOUT_END_MARKER
            ),
            len(lines) - 1,
        )
        lines = lines[:start] + lines[end + 1 :]
    while lines and not lines[-1].strip():
        lines.pop()
    record = render_closeout_record(batch, closed_on, parse_wp_dispositions(lines))
    return [*lines, "", *record]


def _admission_issue(batch: int, config: CloseoutConfig) -> IntegrityIssue:
    """Refuse to close a batch the close-out signals do not govern."""
    return _issue(
        "PLAYBOOK.md",
        None,
        f"A batch closed by this command is at or above the [closeout] "
        f"admission boundary (Batch {batch} is below "
        f"{config.admit_from_batch}).",
        f"Batch {batch} closed before these signals existed and is admitted as "
        f"it stands. Lower `admit_from_batch` in .docsync.toml only if the "
        f"evidence for every batch from {batch} onwards genuinely exists; "
        f"never write it in order to satisfy this command.",
    )


def _claim_issues(batch: int, playbook_lines: Sequence[str]) -> list[IntegrityIssue]:
    """Signals 1 and 4: PLAYBOOK claims the closure and can be repointed."""
    section = _section_3(playbook_lines)
    issues: list[IntegrityIssue] = []
    if batch not in closed_batch_claims(section):
        issues.append(
            _issue(
                "PLAYBOOK.md",
                None,
                f"PLAYBOOK Section 3 states that Batch {batch} is complete.",
                f"Write the completion claim yourself once the batch really is "
                f"done, for example `- **Batch {batch} is complete.**`. This "
                f"command records a closure; it never declares one.",
            )
        )
    if _parse_active_batch_state(section).current_batch == batch:
        issues.append(
            _issue(
                "PLAYBOOK.md",
                None,
                f"Batch {batch} is not declared active and complete at once.",
                f"Decide which Batch {batch} is: remove the active declaration, "
                f"or remove the completion claim.",
            )
        )
    if find_batch_index_row(playbook_lines, batch) is None:
        issues.append(
            _issue(
                "PLAYBOOK.md",
                None,
                f"PLAYBOOK's batch index carries a row for Batch {batch}.",
                f"Add the row -- `| {batch} | <title> | <definition> | <log> |` "
                f"-- so the closure has an index reference to repoint at the "
                f"archived definition and the batch log.",
            )
        )
    return issues


def _dashboard_issues(
    batch: int, session_lines: Sequence[str] | None, session_path: str
) -> list[IntegrityIssue]:
    """Signal 3: the managed dashboard agrees the batch reached completion."""
    if session_lines is None:
        return []
    rows = [
        (index + 1, match.group(2))
        for index, text in prose_lines(list(session_lines))
        if (match := DASHBOARD_STATUS_ROW_RE.match(text)) is not None
        and int(match.group(1)) == batch
    ]
    if not rows:
        return [
            _issue(
                session_path,
                None,
                f"The dashboard's Section 1 states Batch {batch}'s state.",
                f"Add a `| Batch {batch} status | Complete |` row to Section 1. "
                f"A dashboard that says nothing about the batch is not a second "
                f"signal, and closing on one document's word alone is the "
                f"failure this check exists for.",
            )
        ]
    disagreeing = [
        (line, value)
        for line, value in rows
        if _DASHBOARD_COMPLETE_RE.search(value) is None
    ]
    if disagreeing:
        return [
            _issue(
                session_path,
                disagreeing[0][0],
                f"The dashboard and PLAYBOOK agree that Batch {batch} is "
                f"complete (the dashboard reads "
                f"{disagreeing[0][1].strip() or 'nothing'}).",
                "Reconcile the two documents by hand. Whichever is wrong, the "
                "disagreement is the evidence that the batch is not finished "
                "being closed.",
            )
        ]
    return []


def _disposition_issues(
    batch: int, definition_path: str, definition_lines: Sequence[str] | None
) -> list[IntegrityIssue]:
    """Signal 2: every declared work package has reached a terminal state."""
    if definition_lines is None:
        return [
            _issue(
                definition_path,
                None,
                f"Batch {batch}'s definition exists and can be read.",
                f"Restore `{definition_path}` before closing the batch.",
            )
        ]
    dispositions = parse_wp_dispositions(definition_lines)
    if not dispositions:
        return [
            _issue(
                definition_path,
                None,
                f"Batch {batch}'s definition declares at least one work package.",
                "A definition with no `### WP-N` heading records no plan, so a "
                "close-out record built from it would attest to nothing. Write "
                "the plan the batch actually executed.",
            )
        ]
    issues: list[IntegrityIssue] = []
    for item in dispositions:
        if item.state == ACTIVE:
            issues.append(
                _issue(
                    definition_path,
                    item.line or None,
                    f"Every work package of Batch {batch} has an explicit "
                    f"terminal state (WP-{item.number} is still active).",
                    f"State WP-{item.number}'s outcome in its own heading -- "
                    f"strike it through with `-- **DONE**`, or mark it "
                    f"`(ABSORBED INTO WP-N)` or dropped. This command will not "
                    f"mark a package complete on your behalf.",
                )
            )
        elif item.state == ABSORBED and item.reference is None:
            issues.append(
                _issue(
                    definition_path,
                    item.line or None,
                    "An absorbed work package carries a disposition reference to "
                    "the package that took it on.",
                    f"Name the target, e.g. `### WP-{item.number} -- ... "
                    "(ABSORBED INTO WP-N)`.",
                )
            )
    return issues


def _root_definition_issues(
    batch: int, definition_path: str, tracked_paths: frozenset[str]
) -> list[IntegrityIssue]:
    """Signal 5: exactly one root definition, the one about to be archived."""
    root_re = root_definition_pattern(batch)
    extra = sorted(
        path
        for path in tracked_paths
        if "/" not in path
        and root_re.fullmatch(path) is not None
        and path != definition_path
    )
    return [
        _issue(
            path,
            None,
            f"One root definition remains for Batch {batch}, the one being archived.",
            f"Archive or delete `{path}` first. Two root definitions for one "
            f"batch means the closure would leave a second, unarchived copy "
            f"behind.",
        )
        for path in extra
    ]


def collect_transition_issues(
    *,
    batch: int,
    playbook_lines: Sequence[str],
    session_lines: Sequence[str] | None,
    session_path: str,
    definition_path: str,
    definition_lines: Sequence[str] | None,
    tracked_paths: frozenset[str],
    config: CloseoutConfig,
) -> list[IntegrityIssue]:
    """Return every reason this batch may not be closed right now.

    The signals are evaluated together and reported together: an operator who
    fixes one refusal and reruns should not discover a second one that was
    always true. The one exception is the admission boundary, which short-
    circuits -- below it, asking for the remaining evidence would be asking
    for evidence that was never meant to exist.

    Nothing here is repairable by the tool. Every refusal names a document a
    person has to edit, because each signal is an author's statement about
    work that happened outside this repository's reach.
    """
    if batch < config.admit_from_batch:
        return [_admission_issue(batch, config)]
    return [
        *_claim_issues(batch, playbook_lines),
        *_dashboard_issues(batch, session_lines, session_path),
        *_disposition_issues(batch, definition_path, definition_lines),
        *_root_definition_issues(batch, definition_path, tracked_paths),
    ]
