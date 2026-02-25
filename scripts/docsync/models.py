"""Data classes and exceptions shared across all docsync modules."""

from __future__ import annotations

import dataclasses


class SyncError(RuntimeError):
    """Raised when deterministic sync cannot proceed safely."""


@dataclasses.dataclass(frozen=True)
class Entry:
    """Represents one dated execution-log entry block."""

    heading: str
    date: str
    title: str
    lines: tuple[str, ...]
    start_idx: int
    fingerprint: str


@dataclasses.dataclass(frozen=True)
class ActiveBatchState:
    """Parsed batch state signals from PLAYBOOK Section 3."""

    current_batch: int | None
    last_completed_batch: int | None
    next_undefined_batch: int | None


@dataclasses.dataclass(frozen=True)
class SyncResult:
    """Outputs of a sync pass before write/check decisions."""

    playbook_lines: list[str]
    archive_lines: list[str]
    session_lines: list[str] | None
    rotated_count: int
    kept_non_current_count: int
    current_batch_entry_count: int
