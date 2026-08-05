"""Immutable value types shared by the worktree guard layers."""

import dataclasses
from pathlib import Path
from typing import Literal

Severity = Literal["INFO", "WARNING", "ERROR"]


class GuardError(ValueError):
    """Report malformed input that cannot be classified deterministically."""


@dataclasses.dataclass(frozen=True)
class CommandResult:
    """Contain sanitized process output returned by the injectable Git runner."""

    returncode: int
    stdout: str
    stderr: str


@dataclasses.dataclass(frozen=True)
class BatchBranch:
    """Describe the active batch and its required worktree branch."""

    active_batch: int | None
    expected_branch: str | None


@dataclasses.dataclass(frozen=True)
class Diagnostic:
    """Describe one stable, actionable worktree guard outcome."""

    severity: Severity
    code: str
    subject: str
    message: str
    remediation: str | None = None


@dataclasses.dataclass(frozen=True)
class LineageSnapshot:
    """Contain immutable branch state collected by the later CLI layer."""

    active_batch: int | None
    expected_branch: str | None
    actual_branch: str | None
    base_ref: str
    behind: int
    ahead: int
    head_tree: str | None
    base_tree: str | None
    dirty: bool
    detached: bool
    recognized_ci: bool


@dataclasses.dataclass(frozen=True)
class VenvPaths:
    """Provide qualified paths to the repository's allowed virtualenv tools."""

    root: Path
    python: Path
    pytest: Path
    pre_commit: Path
