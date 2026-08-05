"""Stable public facade for read-only worktree-safety diagnostics.

Internal modules separate subprocess execution, repository inspection,
lineage classification, and virtualenv topology. Importers should continue to
use this facade so that those implementation boundaries may evolve safely.
"""

from scripts.dev._worktree_guard_diagnostics import inspection_failure_diagnostics
from scripts.dev._worktree_guard_inspection import inspect_worktree
from scripts.dev._worktree_guard_lineage import (
    ACTIVE_BATCH_RE,
    BRANCH_RE,
    GENERIC_SECTION_RE,
    SECTION_3_RE,
    classify_lineage,
    parse_batch_branch,
)
from scripts.dev._worktree_guard_runner import run_git
from scripts.dev._worktree_guard_types import (
    BatchBranch,
    CommandResult,
    Diagnostic,
    GuardError,
    LineageSnapshot,
    Severity,
    VenvPaths,
)
from scripts.dev._worktree_guard_venv import POSIX_TOOLS, WINDOWS_TOOLS, resolve_venv

__all__ = [
    "ACTIVE_BATCH_RE",
    "BRANCH_RE",
    "BatchBranch",
    "CommandResult",
    "Diagnostic",
    "GENERIC_SECTION_RE",
    "GuardError",
    "LineageSnapshot",
    "POSIX_TOOLS",
    "SECTION_3_RE",
    "Severity",
    "VenvPaths",
    "WINDOWS_TOOLS",
    "classify_lineage",
    "inspect_worktree",
    "inspection_failure_diagnostics",
    "parse_batch_branch",
    "resolve_venv",
    "run_git",
]
