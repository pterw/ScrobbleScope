"""Pure live-document integrity checks used by the docsync command layer."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from docsync.logic import latest_test_count_authority
from docsync.models import IntegrityIssue, SyncError, TestCountAuthority
from docsync.parser import (
    CURRENT_BATCH_END_MARKER,
    CURRENT_BATCH_START_MARKER,
    SECTION_3_RE,
    SECTION_4_RE,
    _extract_entry_batch,
    _find_marker_pair,
    _find_section,
    _parse_active_batch_state,
    _parse_entries,
)
from docsync.renderer import SIDE_ARCHIVE_PREFIX, _next_wp_number

BACKTICK_MD_RE = re.compile(r"`([^`\n]+\.md)`")
BACKTICK_MD_TOKEN_RE = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s#]+\.md)(?:#[^)]+)?\)")
SCHEMATIC_RE = re.compile(
    r"[<>*?\[\]{}%]|\bBATCHN(?![0-9A-Za-z])|\bpath/to/",
    re.IGNORECASE,
)
# DOC001 governs repository-relative references only. A URI scheme, a POSIX
# absolute path, a Windows drive letter, or a parent-relative path all name
# something outside the repository, which `git ls-files` can never list.
NON_REPOSITORY_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|/|\.\./)")
# docsync creates the per-batch logs itself during rotation, so a reference to
# one is a forward declaration rather than a dead link. Without this, running
# `--check` before `--fix` failed on the tool's own pending output.
GENERATED_LOG_RE = re.compile(r"^docs/history/logs/BATCH\d+_LOG\.md$", re.IGNORECASE)
DEFINITION_REFERENCE_RE = re.compile(r"Definition:\s*`([^`\n]+\.md)`")
BRANCH_FIELD_RE = re.compile(r"^\s*(?:[-*+]\s+)?\*\*Branch:\*\*")
DEFINITION_STATUS_LINE_RE = re.compile(r"^\*\*Status:\*\*")
DEFINITION_WP_HEADING_RE = re.compile(r"^###\s+WP-(\d+)\b", re.IGNORECASE)
WP_SKIPPED_RE = re.compile(
    r"\b(?:absorbed\s+into|dropped|merged\s+into)\b", re.IGNORECASE
)


def _definition_wp_numbers(definition_lines: list[str]) -> tuple[int, ...]:
    """Return the work-package numbers the definition actually plans.

    Read from the definition's own `### WP-N` headings rather than assumed
    contiguous: batches drop or absorb work packages (Batch 17 shipped with
    WP-5 dropped; Batch 21 absorbs WP-6 into WP-3), and a lowest-missing-
    integer rule would then demand a number that no work package will ever
    satisfy. A heading whose section is marked absorbed or dropped is
    excluded when its heading says so, so an honestly stubbed-out package never
    blocks the gate.
    """
    numbers: list[int] = []
    for line in definition_lines:
        heading_match = DEFINITION_WP_HEADING_RE.match(line)
        if heading_match is not None and WP_SKIPPED_RE.search(line) is None:
            numbers.append(int(heading_match.group(1)))
    return tuple(numbers)


FINDINGS_HEADER_COUNT_RE = re.compile(
    r"^>?\s*\*{0,2}(\d+)\s+tests\s+across\s+(\d+)\s+test\s+modules\.\*{0,2}\s*$"
)
# The count line lives in FINDINGS.md's header block, before the first
# section heading. Scanning the whole file let a historical example or an
# archived finding's prose become a live count assertion; scoping to the
# region also makes a formatting change to the real header a visible
# failure instead of a silent skip.
_FINDINGS_HEADER_END_RE = re.compile(r"^#{1,6}\s+")
NEXT_WP_CLAIM_RE = re.compile(
    r"\bWP-(\d+)\b(?:\s*\([^)]*\))?\s+is\s+(?:the\s+)?next",
    re.IGNORECASE,
)
SECTION3_NEXT_ACTION_RE = re.compile(r"^\s*-\s+\*\*Next action:\*\*", re.IGNORECASE)
TOP_LEVEL_BULLET_RE = re.compile(r"^-\s+")
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
SESSION_CURRENT_COUNT_RES = (
    re.compile(r"^\|\s*Tests\s*\|\s*\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*"),
    re.compile(
        r"^- Latest validated test count:\s*\*\*(\d+)\s+"
        r"(?:tests?\s+)?pass(?:ing|ed)\*\*\.\s*$"
    ),
    re.compile(r"^##\s+\d+\.\s+Test structure\s+\((\d+)\s+tests\)\s*$"),
)

_LIVE_DOCUMENT_PATHS = frozenset(
    {
        "AGENTS.md",
        "HANDOFF_PROMPT.md",
        "AGENT_NOTES.md",
        "PLAYBOOK.md",
        "FINDINGS.md",
    }
)
_SESSION_CONTEXT_PATH = ".claude/SESSION_CONTEXT.md"
_TRACKED_PATH_DISCOVERY_ERROR = "Repository tracked-file discovery failed"


def _pinned_commit_identity(line: str) -> bool:
    """Return whether the line quotes a literal commit hash.

    Only a backticked token that is entirely hexadecimal counts. A bare
    hex-range scan over prose matched a dated branch suffix, a pull-request
    number, and ordinary words spelled from the hex alphabet, each of which
    blocked the gate with no way to repair it. An all-decimal token is
    excluded for the same reason: dates and issue numbers are not lineage.
    """
    for token in BACKTICK_MD_TOKEN_RE.findall(line):
        candidate = token.strip()
        if (
            7 <= len(candidate) <= 40
            and set(candidate) <= _HEX_DIGITS
            and not candidate.isdigit()
        ):
            return True
    return False


def _normalize_reference(raw: str) -> str:
    """Normalize a Markdown path for Git."""
    return raw.strip().replace("\\", "/").removeprefix("./")


def _concrete_references(lines: list[str]) -> list[tuple[int, str]]:
    """Extract literal repository-relative Markdown references and their lines."""
    references: list[tuple[int, str]] = []
    in_code_block = False
    for line_number, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        # A fenced block illustrates a command or a historical state rather
        # than asserting that a file exists now.
        if in_code_block:
            continue
        for pattern in (BACKTICK_MD_RE, MARKDOWN_LINK_RE):
            for match in pattern.finditer(line):
                reference = _normalize_reference(match.group(1))
                if (
                    not any(char.isspace() for char in reference)
                    and not SCHEMATIC_RE.search(reference)
                    and not NON_REPOSITORY_RE.match(reference)
                ):
                    references.append((line_number, reference))
    return references


def collect_tracked_paths(
    repo_root: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> frozenset[str]:
    """Return normalized repository-relative paths from git ls-files."""
    command = ["git", "ls-files", "-z"]
    try:
        result = runner(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        raise SyncError(_TRACKED_PATH_DISCOVERY_ERROR) from None
    if result.returncode != 0:
        raise SyncError(_TRACKED_PATH_DISCOVERY_ERROR)
    return frozenset(
        _normalize_reference(path) for path in result.stdout.split("\0") if path
    )


def _playbook_lines_without_entry_blocks(playbook_lines: list[str]) -> list[str]:
    """Blank dated Section 4 history without shifting source lines."""
    section_start, section_end = _find_section(
        playbook_lines, SECTION_4_RE, "PLAYBOOK section 4"
    )
    section_lines = playbook_lines[section_start:section_end]
    entries, _ = _parse_entries(section_lines)
    entry_ranges = [
        (
            entry.start_idx,
            (
                entries[index + 1].start_idx
                if index + 1 < len(entries)
                else len(section_lines)
            ),
        )
        for index, entry in enumerate(entries)
    ]
    retained_section_lines = [
        "" if any(start <= index < end for start, end in entry_ranges) else line
        for index, line in enumerate(section_lines)
    ]
    return (
        playbook_lines[:section_start]
        + retained_section_lines
        + playbook_lines[section_end:]
    )


def _active_definition_reference(
    playbook_lines: list[str],
) -> tuple[int | None, str | None, int | None, IntegrityIssue | None]:
    """Resolve the active definition or return its diagnostic."""
    section_start, section_end = _find_section(
        playbook_lines, SECTION_3_RE, "PLAYBOOK section 3"
    )
    section_lines = playbook_lines[section_start:section_end]
    current_batch = _parse_active_batch_state(section_lines).current_batch
    if current_batch is None:
        return None, None, None, None

    references: list[tuple[int, str]] = []
    for offset, line in enumerate(section_lines):
        for match in DEFINITION_REFERENCE_RE.finditer(line):
            reference = _normalize_reference(match.group(1))
            if "/" not in reference and not SCHEMATIC_RE.search(reference):
                references.append((section_start + offset + 1, reference))

    if len(references) != 1:
        # Name what was found. Restating the invariant left the two states a
        # handover actually produces -- a closing and an opening batch declared
        # together, or a completed batch with nothing declared -- without an
        # actionable instruction.
        if references:
            found = ", ".join(reference for _, reference in references)
            remediation = (
                f"Section 3 declares {len(references)} root definitions ({found}). "
                "Keep only the current batch's; reference any archived definition "
                "by its `docs/history/definitions/` path."
            )
        else:
            remediation = (
                f"Declare `Definition: \\`BATCH{current_batch}_DEFINITION.md\\`` in "
                "PLAYBOOK Section 3, or state that no batch is open if the last "
                "one closed."
            )
        return (
            current_batch,
            None,
            None,
            IntegrityIssue(
                code="DOC002",
                severity="error",
                path="PLAYBOOK.md",
                line=references[0][0] if references else section_start + 1,
                invariant="An active batch has one root definition declaration.",
                remediation=remediation,
            ),
        )

    line, reference = references[0]
    batch_token_re = re.compile(
        rf"^BATCH{current_batch}(?:_[^/]+)?\.md$", re.IGNORECASE
    )
    if batch_token_re.fullmatch(reference) is None:
        return (
            current_batch,
            reference,
            line,
            IntegrityIssue(
                code="DOC002",
                severity="error",
                path="PLAYBOOK.md",
                line=line,
                invariant="The definition matches the current batch token.",
                remediation="Point Section 3 at the current batch definition.",
            ),
        )
    return current_batch, reference, line, None


def _active_definition_candidates(
    current_batch: int, tracked_paths: frozenset[str]
) -> tuple[str, ...]:
    """Return tracked root definitions for one exact batch token."""
    candidate_re = re.compile(rf"^BATCH{current_batch}(?:_[^/]+)?\.md$", re.IGNORECASE)
    candidates = {
        normalized
        for path in tracked_paths
        if "/" not in (normalized := _normalize_reference(path))
        and candidate_re.fullmatch(normalized) is not None
    }
    return tuple(sorted(candidates, key=lambda path: (path.casefold(), path)))


def _issue(
    code: str,
    path: str,
    line: int | None,
    invariant: str,
    remediation: str,
) -> IntegrityIssue:
    """Build an error-severity integrity diagnostic."""
    return IntegrityIssue(code, "error", path, line, invariant, remediation)


def _count_remediation(authority: TestCountAuthority) -> str:
    """Point the reader at the document that actually decides the count.

    The authority can be a rotated archive entry rather than the live
    PLAYBOOK, so naming PLAYBOOK unconditionally sends the reader to edit a
    file that may not hold the number at all. When the newest entry is
    ambiguous there is no number to agree with, and the fix is to record an
    unambiguous result rather than to restate a stale one.
    """
    if authority.ambiguous:
        return (
            "The newest count-bearing log entry quotes several counts without "
            "a `pytest -q` result, so no count is authoritative. Record an "
            "explicit `pytest -q` result in a new log entry, then refresh "
            "every named SESSION_CONTEXT test-count field."
        )
    return (
        "Correct the authoritative `pytest -q` result -- the newest full-suite "
        "entry, which may be in PLAYBOOK or in the rotated archive -- then "
        "refresh every named SESSION_CONTEXT test-count field."
    )


def _findings_count_remediation(authority: TestCountAuthority) -> str:
    """Point the reader at the FINDINGS header, the document DOC008 owns.

    ``_count_remediation`` names SESSION_CONTEXT fields because that is what
    DOC006 governs; following it for DOC008 would edit a correct dashboard
    and leave the stale findings header in place. The ambiguous case keeps
    the shared guidance: with no authoritative number at all, recording one
    is the only repair either document can follow.
    """
    if authority.ambiguous:
        return _count_remediation(authority)
    return (
        "Update the FINDINGS.md header count line to match the authoritative "
        "`pytest -q` result -- the newest full-suite entry, which may be in "
        "PLAYBOOK or in a rotated archive."
    )


def _computed_next_wp(
    playbook_lines: list[str], definition_lines: list[str] | None = None
) -> int | None:
    """Return the next work package number derived from PLAYBOOK Section 4.

    Parse the current-batch entries, then delegate to the renderer's shared
    plan-aware rule. This keeps DOC007 and the managed SESSION_CONTEXT block on
    the same value, including absorbed gaps and the all-complete close-out
    state. Return ``None`` when there are no current entries.
    """
    try:
        s4_start, s4_end = _find_section(
            playbook_lines, SECTION_4_RE, "PLAYBOOK section 4"
        )
        section_4_lines = playbook_lines[s4_start:s4_end]
        marker_start, marker_end = _find_marker_pair(
            section_4_lines,
            CURRENT_BATCH_START_MARKER,
            CURRENT_BATCH_END_MARKER,
            "PLAYBOOK section 4",
        )
        entries, _ = _parse_entries(section_4_lines)
    except SyncError:
        return None
    current_entries = [
        entry for entry in entries if marker_start < entry.start_idx < marker_end
    ]
    if not current_entries:
        return None
    planned_wp_numbers = (
        _definition_wp_numbers(definition_lines)
        if definition_lines is not None
        else None
    )
    return _next_wp_number(current_entries, planned_wp_numbers)


def _definition_next_wp_claim(
    definition_lines: list[str],
) -> tuple[int | None, int | None]:
    """Return (claimed next WP number, its line) from a definition status line.

    The claim is recognized only in the sentence shape the definitions use:
    a `WP-<N>` token followed by "is the next" wording. A status line with no
    such claim returns (None, None) and DOC007 stays silent rather than
    reporting a false mismatch -- an absent claim is a different defect than
    a wrong one, and inventing a mismatch would train readers to ignore the
    diagnostic. A second distinct problem, a malformed or missing status
    line entirely, is likewise left to future work rather than guessed at.
    """
    for line_number, line in enumerate(definition_lines, start=1):
        if DEFINITION_STATUS_LINE_RE.match(line) is None:
            continue
        match = NEXT_WP_CLAIM_RE.search(line)
        if match is not None:
            return int(match.group(1)), line_number
    return None, None


def _section3_next_wp_claim(
    playbook_lines: list[str],
) -> tuple[int | None, int | None]:
    """Return (claimed next WP number, its line) from PLAYBOOK Section 3.

    Bootstrap requires Section 3, the definition, and SESSION_CONTEXT to
    agree on the next work package. The renderer derives its value from
    Section 4 headings, but Section 3's own "Next action" prose restates
    the claim by hand -- `**WP-3 is next**` is the shape this corpus uses.
    A stale Section 3 beside a fresh definition would otherwise pass every
    check while an arriving agent reads a contradictory next action from the
    canonical status section. Only the final parseable claim inside the actual
    Next action bullet is current; historical prose elsewhere in Section 3 and
    superseded text earlier in that bullet cannot steal it. No parseable claim
    stays silent, for the same reason as the definition side: a false mismatch
    is worse than no check.
    """
    try:
        s3_start, s3_end = _find_section(
            playbook_lines, SECTION_3_RE, "PLAYBOOK section 3"
        )
    except SyncError:
        return None, None
    action_starts = [
        line_number
        for line_number in range(s3_start + 1, s3_end)
        if SECTION3_NEXT_ACTION_RE.match(playbook_lines[line_number])
    ]
    if not action_starts:
        return None, None

    action_start = action_starts[-1]
    action_end = s3_end
    for line_number in range(action_start + 1, s3_end):
        if TOP_LEVEL_BULLET_RE.match(playbook_lines[line_number]):
            action_end = line_number
            break

    claims = [
        (int(match.group(1)), line_number + 1)
        for line_number in range(action_start, action_end)
        for match in NEXT_WP_CLAIM_RE.finditer(playbook_lines[line_number])
    ]
    return claims[-1] if claims else (None, None)


def _check_definition_next_wp(
    playbook_lines: list[str],
    definition_path: str,
    definition_lines: list[str] | None,
) -> IntegrityIssue | None:
    """DOC007: the active definition must agree on the next work package.

    PLAYBOOK Section 4 decides which work package comes next; the batch
    definition's status line restates it by hand. Twice that hand copy went
    stale during Batch 21 and both times a human reviewer caught it, so this
    check compares the two mechanically. When the definition makes no
    parseable claim the check stays silent: a false mismatch is worse than
    no check, and an unparseable status line is a separate finding.
    """
    if definition_lines is None:
        return None
    computed = _computed_next_wp(playbook_lines, definition_lines)
    claimed, claimed_line = _definition_next_wp_claim(definition_lines)
    if computed is None or claimed is None:
        return None
    if computed == claimed:
        return None
    return _issue(
        "DOC007",
        definition_path,
        claimed_line,
        f"The definition claims WP-{claimed} is next; PLAYBOOK Section 4 "
        f"entries make WP-{computed} next.",
        "Update the definition's Status line to name WP-"
        f"{computed} as the next batch work package.",
    )


def _check_section3_next_wp(
    playbook_lines: list[str], definition_lines: list[str] | None = None
) -> IntegrityIssue | None:
    """DOC007: PLAYBOOK Section 3 must agree on the next work package.

    The same bootstrap leg as the definition check, on the Section 3 side.
    Section 4 headings decide what is actually next; Section 3's Next
    action prose restates it by hand and has drifted before. Silence when
    Section 3 makes no parseable claim, matching the definition side.
    """
    computed = _computed_next_wp(playbook_lines, definition_lines)
    claimed, claimed_line = _section3_next_wp_claim(playbook_lines)
    if computed is None or claimed is None:
        return None
    if computed == claimed:
        return None
    return _issue(
        "DOC007",
        "PLAYBOOK.md",
        claimed_line,
        f"Section 3 claims WP-{claimed} is next; PLAYBOOK Section 4 "
        f"entries make WP-{computed} next.",
        "Update the Section 3 Next action to name WP-"
        f"{computed} as the next batch work package.",
    )


def _check_findings_header_count(
    findings_lines: list[str] | None, authority: TestCountAuthority
) -> IntegrityIssue | None:
    """DOC008: the FINDINGS.md header must carry the authoritative count.

    The header publishes the suite total to every reader who opens the file,
    but nothing gated it, and it published 666 for a full day after PLAYBOOK
    and SESSION_CONTEXT had moved on. This applies the same authority DOC006
    uses for SESSION_CONTEXT to that one header line. An ambiguous authority
    blocks here too, exactly as it does for SESSION_CONTEXT: ambiguity let a
    stale dashboard survive once already.

    A merely absent authority -- no entry anywhere records a count -- is not
    a mismatch: there is nothing to agree with, and blocking would demand a
    repair that cannot satisfy the gate. Only ambiguity, which suppresses
    older entries, still blocks.
    """
    if findings_lines is None:
        return None
    header_end = len(findings_lines)
    for line_number, line in enumerate(findings_lines, start=1):
        if line_number > 1 and _FINDINGS_HEADER_END_RE.match(line):
            header_end = line_number - 1
            break
    fields = [
        (line_number, int(match.group(1)))
        for line_number, line in enumerate(findings_lines[:header_end], start=1)
        if (match := FINDINGS_HEADER_COUNT_RE.match(line)) is not None
    ]
    if not fields:
        return None
    mismatched = [
        (line_number, count)
        for line_number, count in fields
        if authority.count is not None and count != authority.count
    ]
    if not mismatched and not authority.ambiguous:
        return None
    issue_line = mismatched[0][0] if mismatched else fields[0][0]
    return _issue(
        "DOC008",
        "FINDINGS.md",
        issue_line,
        "The findings header test count must agree with the authoritative "
        "full-suite validation in the log.",
        _findings_count_remediation(authority),
    )


def collect_integrity_issues(
    *,
    repo_root: Path,
    live_documents: Mapping[str, list[str]],
    playbook_lines: list[str],
    archive_lines: list[str],
    session_lines: list[str] | None,
    expected_session_lines: list[str] | None,
    tracked_paths: frozenset[str],
    batch_log_lines: Mapping[int, list[str]] | None = None,
) -> list[IntegrityIssue]:
    """Return deterministic live-document integrity issues."""
    issues: list[IntegrityIssue] = []
    (
        current_batch,
        definition_path,
        definition_line,
        definition_issue,
    ) = _active_definition_reference(playbook_lines)
    if definition_issue is not None:
        issues.append(definition_issue)
    elif current_batch is not None and definition_path is not None:
        candidates = _active_definition_candidates(current_batch, tracked_paths)
        if candidates != (definition_path,):
            candidate_list = ", ".join(candidates) if candidates else "none"
            issues.append(
                _issue(
                    "DOC002",
                    "PLAYBOOK.md",
                    definition_line,
                    "The declaration names the sole tracked root candidate.",
                    f"Keep and declare one root Batch {current_batch} file in Section 3. "
                    f"Candidates: {candidate_list}.",
                )
            )
        elif definition_path not in live_documents:
            issues.append(
                _issue(
                    "DOC002",
                    "PLAYBOOK.md",
                    definition_line,
                    "The tracked definition has supplied live content.",
                    "Supply its content to the integrity pass.",
                )
            )

    documents_to_scan = set(_LIVE_DOCUMENT_PATHS)
    if definition_path is not None:
        documents_to_scan.add(definition_path)
    if session_lines is not None:
        documents_to_scan.add(_SESSION_CONTEXT_PATH)
    for path in sorted(documents_to_scan):
        lines = (
            session_lines if path == _SESSION_CONTEXT_PATH else live_documents.get(path)
        )
        if lines is None:
            continue
        scan_lines = (
            _playbook_lines_without_entry_blocks(playbook_lines)
            if path == "PLAYBOOK.md"
            else lines
        )
        for line, reference in _concrete_references(scan_lines):
            if (
                path == "PLAYBOOK.md"
                and line == definition_line
                and reference == definition_path
            ):
                # DOC002 owns root Batch definition declarations in Section 3.
                continue
            if reference not in tracked_paths and not GENERATED_LOG_RE.match(reference):
                issues.append(
                    _issue(
                        "DOC001",
                        path,
                        line,
                        f"Concrete Markdown reference `{reference}` names a tracked file.",
                        "Update it to a tracked file or documented pattern.",
                    )
                )

    if (
        current_batch is not None
        and definition_path is not None
        and definition_issue is None
    ):
        definition_lines = live_documents.get(definition_path)
        branch_lines = (
            [
                (index + 1, line)
                for index, line in enumerate(definition_lines)
                if BRANCH_FIELD_RE.match(line)
            ]
            if definition_lines is not None
            else []
        )
        # Report the violation that actually occurred. Telling an author to
        # remove a commit hash from a field that has none, or that is missing
        # entirely, is not actionable.
        if len(branch_lines) != 1:
            issues.append(
                _issue(
                    "DOC003",
                    definition_path,
                    branch_lines[0][0] if branch_lines else None,
                    "The active definition declares exactly one Branch field.",
                    "Keep one `**Branch:**` field naming the stable branch; "
                    "record lineage in PLAYBOOK Section 4.",
                )
            )
        elif _pinned_commit_identity(branch_lines[0][1]):
            issues.append(
                _issue(
                    "DOC003",
                    definition_path,
                    branch_lines[0][0],
                    "The Branch field names a stable branch without a commit hash.",
                    "Remove its commit hash; keep lineage in PLAYBOOK Section 4.",
                )
            )

    archive_entries, first_entry_index = _parse_entries(archive_lines)
    del archive_entries
    archive_prefix = (
        list(archive_lines[:first_entry_index])
        if first_entry_index is not None
        else list(archive_lines)
    )
    while archive_prefix and not archive_prefix[-1].strip():
        archive_prefix.pop()
    if tuple(archive_prefix) != SIDE_ARCHIVE_PREFIX:
        issues.append(
            _issue(
                "DOC004",
                "docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md",
                1,
                "The side-task archive uses its canonical prologue.",
                "Regenerate it from docsync.renderer.SIDE_ARCHIVE_PREFIX.",
            )
        )

    if session_lines is not None:
        if (
            expected_session_lines is not None
            and session_lines != expected_session_lines
        ):
            issues.append(
                _issue(
                    "DOC005",
                    ".claude/SESSION_CONTEXT.md",
                    None,
                    "The managed session document matches docsync's expected rendering.",
                    "Run doc_state_sync.py --fix to refresh the managed session block.",
                )
            )
        authority = latest_test_count_authority(
            playbook_lines, archive_lines, batch_log_lines
        )
        session_count_fields = [
            (line_number, int(match.group(1)))
            for line_number, line in enumerate(session_lines, start=1)
            for pattern in SESSION_CURRENT_COUNT_RES
            if (match := pattern.match(line)) is not None
        ]
        session_counts = {count for _, count in session_count_fields}
        mismatched_fields = [
            (line_number, count)
            for line_number, count in session_count_fields
            if authority.count is not None and count != authority.count
        ]
        # An ambiguous authority is not "nothing to compare against". Treating
        # it that way let a stale dashboard survive the gate: `--fix` renders
        # the managed block as unknown while the named numeric fields keep
        # their old value, and the final check exits 0.
        if (
            len(session_counts) > 1
            or mismatched_fields
            or (authority.ambiguous and session_count_fields)
        ):
            issue_line = (
                mismatched_fields[0][0]
                if mismatched_fields
                else session_count_fields[0][0]
            )
            issues.append(
                _issue(
                    "DOC006",
                    ".claude/SESSION_CONTEXT.md",
                    issue_line,
                    "Every named session current-test field agrees with the "
                    "authoritative full-suite validation in the log.",
                    _count_remediation(authority),
                )
            )

    if (
        current_batch is not None
        and definition_path is not None
        and definition_issue is None
    ):
        definition_next_wp_issue = _check_definition_next_wp(
            playbook_lines,
            definition_path,
            live_documents.get(definition_path),
        )
        if definition_next_wp_issue is not None:
            issues.append(definition_next_wp_issue)

        section3_next_wp_issue = _check_section3_next_wp(
            playbook_lines, live_documents.get(definition_path)
        )
        if section3_next_wp_issue is not None:
            issues.append(section3_next_wp_issue)

    findings_count_issue = _check_findings_header_count(
        live_documents.get("FINDINGS.md"),
        latest_test_count_authority(playbook_lines, archive_lines, batch_log_lines),
    )
    if findings_count_issue is not None:
        issues.append(findings_count_issue)

    return sorted(issues, key=lambda issue: (issue.path, issue.line or 0, issue.code))
