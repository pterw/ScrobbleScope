"""Warn about a missing, gitignored file the workflow depends on (F-B21-25).

These files are gitignored by design -- `skills-lock.json` is the first one
-- so every gate that runs before this one is looking at tracked content and
never even sees them go missing. This check is WARNING only: unlike a
tracked file, the worktree guard cannot restore or fetch a missing one
either, so it can only tell the reader it is gone. A malformed
`[untracked_essentials]` table is WARNING-only for the same reason: it is
still not something this guard can repair, so it must not escalate to the
fail-closed WT014 that `inspect_worktree` raises for an unexpected
exception.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.dev._worktree_guard_diagnostics import issue
from scripts.dev._worktree_guard_types import Diagnostic

# `scripts/docsync/declarations.py` imports its sibling modules by the bare
# `docsync.` package name, so loading it requires `scripts/` itself on
# sys.path -- the same shape `scripts/doc_state_sync.py` already uses for the
# same reason. Without this, the bare import below fails whenever this
# module is reached through an entry point (the CLI, pre-commit) that has
# only put the repository root on sys.path.
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from docsync.declarations import (  # noqa: E402
    DeclarationError,
    load_untracked_essentials_config,
)


def essentials_diagnostics(repo_root: Path) -> list[Diagnostic]:
    """Return WT015 WARNINGs for declared untracked-essential files.

    One per declared path that is missing, or that exists but is not a file
    (CR10) -- a directory reported as "missing" sent the reader to restore
    something already there. Silent when nothing is declared, and silent for
    any declared path that is a present file. Never ERROR: this guard has no
    way to create, fetch or reshape a declared path, so it never blocks on
    one. A malformed `[untracked_essentials]` table itself is reported the
    same way, as a single WT015 WARNING naming the config problem, rather
    than escaping to `inspect_worktree`'s fail-closed WT014.

    Every message that names the declared path renders it with `repr()`
    (CR5): declarations.py's own containment check keeps the path inside the
    repository, but the string itself is still author-controlled text this
    guard did not choose, and a raw control character in it could otherwise
    forge or repaint a line of the guard's own output. The `Diagnostic`'s
    `path` field keeps the plain declared string -- callers that key off it
    programmatically, rather than print it, need the value undecorated.
    """
    try:
        config = load_untracked_essentials_config(repo_root)
    except DeclarationError as error:
        return [
            issue(
                "WARNING",
                "WT015",
                "config/docsync.toml",
                f"the [untracked_essentials] declaration could not be read: {error}",
                "Fix the [untracked_essentials] table; this guard cannot "
                "check declared paths until it parses.",
            )
        ]
    diagnostics: list[Diagnostic] = []
    for relative in config.paths:
        target = repo_root / relative
        if not target.exists():
            diagnostics.append(
                issue(
                    "WARNING",
                    "WT015",
                    relative,
                    "declared untracked-essential file is missing.",
                    "Restore it or ask the owner where its current copy lives; "
                    "this guard does not create or fetch it.",
                )
            )
        elif not target.is_file():
            diagnostics.append(
                issue(
                    "WARNING",
                    "WT015",
                    relative,
                    f"declared untracked-essential path {relative!r} is a "
                    "directory, not a file.",
                    "Point [untracked_essentials] at the file this workflow "
                    "depends on, not its containing directory.",
                )
            )
    return diagnostics
