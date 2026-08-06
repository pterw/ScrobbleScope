"""Pure live-document integrity checks used by the docsync command layer."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from docsync.logic import _latest_test_count_from_entries
from docsync.models import IntegrityIssue, SyncError
from docsync.parser import (
    SECTION_3_RE,
    SECTION_4_RE,
    _find_section,
    _parse_active_batch_state,
    _parse_entries,
)
from docsync.renderer import SIDE_ARCHIVE_PREFIX

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


def collect_integrity_issues(
    *,
    repo_root: Path,
    live_documents: Mapping[str, list[str]],
    playbook_lines: list[str],
    archive_lines: list[str],
    session_lines: list[str] | None,
    expected_session_lines: list[str] | None,
    tracked_paths: frozenset[str],
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
        playbook_count = _latest_test_count_from_entries(playbook_lines, archive_lines)
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
            if playbook_count is not None and count != playbook_count
        ]
        if len(session_counts) > 1 or mismatched_fields:
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
                    "latest PLAYBOOK full-suite validation.",
                    "Correct the current PLAYBOOK `pytest -q` result, then "
                    "refresh every named SESSION_CONTEXT test-count field.",
                )
            )

    return sorted(issues, key=lambda issue: (issue.path, issue.line or 0, issue.code))
