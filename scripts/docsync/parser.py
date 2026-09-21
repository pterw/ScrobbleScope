"""Regex constants, marker strings, and all parsing functions for docsync."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from docsync.markdown import marker_lines, prose_lines
from docsync.models import ActiveBatchState, Entry, SyncError

# ---------------------------------------------------------------------------
# Section heading patterns
# ---------------------------------------------------------------------------

SECTION_3_RE = re.compile(
    r"^##\s*3\.?\s*Active\s+batch\b.*$",
    re.IGNORECASE,
)
SECTION_4_RE = re.compile(
    r"^##\s*4\.?\s*Execution\s+log\b.*$",
    re.IGNORECASE,
)
GENERIC_SECTION_RE = re.compile(r"^##\s+")

# ---------------------------------------------------------------------------
# Entry heading and batch-tag patterns
# ---------------------------------------------------------------------------

ENTRY_HEADING_RE = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})\s+-\s+(.+?)\s*$")
BATCH_COMPLETE_RE = re.compile(r"\bBatch\s+(\d+)\s+is\s+complete\b", re.IGNORECASE)
BATCH_NOT_DEFINED_RE = re.compile(
    r"\bBatch\s+(\d+)\s+is\s+not\s+yet\s+defined\b", re.IGNORECASE
)
BATCH_CURRENT_RE = re.compile(
    r"\bBatch\s+(\d+)\s+is\s+(?:active|current|in[\s-]?progress)\b", re.IGNORECASE
)
ENTRY_BATCH_RE = re.compile(r"\(Batch\s+(\d+)\s+WP-\d+\)", re.IGNORECASE)
TEST_COUNT_RE = re.compile(r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*")
BATCH_NEXT_RE = re.compile(
    r"\bnext\s+batch(?:\s+to\s+execute)?[^0-9]*Batch\s+(\d+)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# HTML comment markers
# ---------------------------------------------------------------------------

CURRENT_BATCH_START_MARKER = "<!-- DOCSYNC:CURRENT-BATCH-START -->"
CURRENT_BATCH_END_MARKER = "<!-- DOCSYNC:CURRENT-BATCH-END -->"
SESSION_STATUS_START_MARKER = "<!-- DOCSYNC:STATUS-START -->"
SESSION_STATUS_END_MARKER = "<!-- DOCSYNC:STATUS-END -->"


# ---------------------------------------------------------------------------
# Fingerprinting (placed here to avoid circular imports with logic.py)
# ---------------------------------------------------------------------------


def _normalize_block(lines: Iterable[str]) -> str:
    normalized = "\n".join(line.rstrip() for line in lines).strip() + "\n"
    return normalized


def _fingerprint(lines: Iterable[str]) -> str:
    normalized = _normalize_block(lines)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Section and marker utilities
# ---------------------------------------------------------------------------


def _find_section(
    lines: list[str], heading_re: re.Pattern[str], label: str
) -> tuple[int, int]:
    start = None
    for idx, line in prose_lines(lines):
        if heading_re.match(line.strip()):
            start = idx
            break
    if start is None:
        raise SyncError(f"Could not find section heading for {label}.")

    end = len(lines)
    for idx, line in prose_lines(lines):
        if idx > start and GENERIC_SECTION_RE.match(line):
            end = idx
            break
    return start, end


def _find_marker_pair(
    lines: list[str], start_marker: str, end_marker: str, label: str
) -> tuple[int, int]:
    visible = marker_lines(lines)
    starts = [i for i, line in visible if line.strip() == start_marker]
    ends = [i for i, line in visible if line.strip() == end_marker]
    if not starts or not ends:
        raise SyncError(
            f"{label} must contain start marker ({start_marker}) and end marker"
            f" ({end_marker})."
        )
    if len(starts) > 1 or len(ends) > 1:
        raise SyncError(
            f"{label} has duplicate markers: "
            f"{len(starts)} start(s), {len(ends)} end(s). "
            f"Expected exactly 1 of each."
        )
    start_idx = starts[0]
    end_idx = ends[-1]
    if start_idx >= end_idx:
        raise SyncError(
            f"{label} marker order is invalid: start marker is after end marker."
        )
    return start_idx, end_idx


# ---------------------------------------------------------------------------
# Entry parsing
# ---------------------------------------------------------------------------


def _parse_entries(lines: list[str]) -> tuple[list[Entry], int | None]:
    heading_idxs: list[int] = []
    for idx, line in prose_lines(lines):
        if ENTRY_HEADING_RE.match(line):
            heading_idxs.append(idx)
        elif re.match(r"^###\s+", line):
            raise SyncError(
                f"Malformed entry heading at line {idx + 1}: {line.rstrip()!r}. "
                f"Expected format: '### YYYY-MM-DD - <title>'"
            )

    if not heading_idxs:
        return [], None

    entries: list[Entry] = []
    for pos, start_idx in enumerate(heading_idxs):
        end_idx = heading_idxs[pos + 1] if pos + 1 < len(heading_idxs) else len(lines)
        block = list(lines[start_idx:end_idx])
        while block and block[-1].strip() == "":
            block.pop()
        block_lines = tuple(block)
        heading = block_lines[0]
        match = ENTRY_HEADING_RE.match(heading)
        if not match:
            raise SyncError(f"Malformed entry heading: {heading}")
        date, title = match.group(1), match.group(2)
        entries.append(
            Entry(
                heading=heading,
                date=date,
                title=title,
                lines=block_lines,
                start_idx=start_idx,
                fingerprint=_fingerprint(block_lines),
            )
        )

    return entries, heading_idxs[0]


# ---------------------------------------------------------------------------
# Batch state parsing
# ---------------------------------------------------------------------------


def _parse_active_batch_state(section_lines: list[str]) -> ActiveBatchState:
    completed: list[int] = []
    not_defined: list[int] = []
    explicit_current: list[int] = []
    explicit_next: list[int] = []

    for _, line in prose_lines(section_lines):
        completed.extend(int(m.group(1)) for m in BATCH_COMPLETE_RE.finditer(line))
        not_defined.extend(int(m.group(1)) for m in BATCH_NOT_DEFINED_RE.finditer(line))
        explicit_current.extend(
            int(m.group(1)) for m in BATCH_CURRENT_RE.finditer(line)
        )
        explicit_next.extend(int(m.group(1)) for m in BATCH_NEXT_RE.finditer(line))

    last_completed = max(completed) if completed else None
    next_undefined = max(not_defined) if not_defined else None

    current_batch = explicit_current[-1] if explicit_current else None
    if current_batch is None and explicit_next:
        candidate = explicit_next[-1]
        if next_undefined != candidate:
            current_batch = candidate

    if current_batch is None and last_completed is not None and next_undefined is None:
        current_batch = last_completed + 1

    if next_undefined is not None and current_batch == next_undefined:
        current_batch = None

    return ActiveBatchState(
        current_batch=current_batch,
        last_completed_batch=last_completed,
        next_undefined_batch=next_undefined,
    )


def closed_batch_claims(section_lines: list[str]) -> list[int]:
    """Return every batch number Section 3 claims complete, in document order.

    A bullet reading ``**Batch N is complete.**`` is the close-out claim this
    corpus writes in PLAYBOOK Section 3, and the claim is what the DOC019 gate
    responds to: for each returned batch at or above the admission boundary,
    the definition-side close-out evidence is evaluated. Fenced examples and
    HTML comments are excluded, so a sample sentence inside a code block is an
    example, not a claim. Duplicate claims of the same batch are collapsed: the
    gate evaluates a batch once no matter how many bullets say it completed.
    """
    claims: list[int] = []
    seen: set[int] = set()
    for _, line in prose_lines(section_lines):
        for match in BATCH_COMPLETE_RE.finditer(line):
            number = int(match.group(1))
            if number not in seen:
                seen.add(number)
                claims.append(number)
    return claims


# ---------------------------------------------------------------------------
# Entry metadata helpers
# ---------------------------------------------------------------------------


def _extract_entry_batch(entry: Entry) -> int | None:
    """Extract the batch number from an entry heading, if present."""
    match = ENTRY_BATCH_RE.search(entry.title)
    return int(match.group(1)) if match else None


def _collect_wp_numbers(entries: list[Entry]) -> list[int]:
    numbers: set[int] = set()
    for entry in entries:
        for raw in re.findall(r"\bWP-(\d+)\b", entry.heading):
            numbers.add(int(raw))
    return sorted(numbers)


def _date_key(date_str: str) -> int:
    return int(date_str.replace("-", ""))


# ---------------------------------------------------------------------------
# Root definition naming convention
# ---------------------------------------------------------------------------


def root_definition_pattern(batch: int) -> re.Pattern[str]:
    """Return the compiled pattern for batch ``N``'s root definition filename.

    Encodes this repository's one naming convention for an unarchived batch
    definition living at the repository root: ``BATCHN.md`` on its own, or
    ``BATCHN_<anything>.md`` with a free-form suffix (for example
    ``BATCH22_DEFINITION.md`` or ``BATCH22_PROPOSAL.md``), matched
    case-insensitively so ``batch22_definition.md`` also counts. The suffix
    excludes ``/`` so a path under a subdirectory never matches -- this
    pattern is for root-level candidates only. Five call sites across
    `cli.py`, `integrity.py`, and `closeout.py` built this same regex
    independently; a change to the convention now has one place to make it.
    """
    return re.compile(rf"^BATCH{batch}(?:_[^/]+)?\.md$", re.IGNORECASE)
