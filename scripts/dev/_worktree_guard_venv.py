"""Primary-checkout virtualenv topology and executable diagnostics."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from scripts.dev._worktree_guard_diagnostics import issue
from scripts.dev._worktree_guard_types import Diagnostic, VenvPaths

WINDOWS_TOOLS = {
    "python": Path("Scripts/python.exe"),
    "pytest": Path("Scripts/pytest.exe"),
    "pre_commit": Path("Scripts/pre-commit.exe"),
}
POSIX_TOOLS = {
    "python": Path("bin/python"),
    "pytest": Path("bin/pytest"),
    "pre_commit": Path("bin/pre-commit"),
}


def is_runnable(path: Path, *, os_name: str, access: Callable[..., bool]) -> bool:
    """Report whether a resolved tool path can actually be executed.

    On POSIX a regular file carrying no execute bit is not runnable, so testing
    existence alone lets WT000 advertise tool paths that fail the moment an
    agent uses them. Windows derives executability from the file extension
    rather than a permission bit, so existence stays the whole test there.

    ``access`` is injected so the POSIX branch is exercisable from any host;
    ``os.access`` reports every existing file as executable on Windows.
    """
    if not path.is_file():
        return False
    if os_name == "nt":
        return True
    return access(path, os.X_OK)


def resolve_venv(
    *,
    repo_root: Path,
    git_dir: Path,
    common_dir: Path,
    main_worktree: Path,
    os_name: str,
    access: Callable[..., bool] = os.access,
) -> tuple[VenvPaths | None, list[Diagnostic]]:
    """Resolve the sole allowed environment for a normal or linked checkout."""
    linked = git_dir.resolve() != common_dir.resolve()
    # The sole environment lives in the main working tree, which cannot be
    # derived from the shared metadata directory: under
    # `git clone --separate-git-dir` that directory sits outside the checkout,
    # so treating its parent as the primary root named a path with no `.venv`
    # and rejected a valid checkout. The caller discovers the main worktree
    # explicitly and passes it here.
    candidate = (main_worktree if linked else repo_root) / ".venv"
    local_candidate = repo_root / ".venv"
    if (
        linked
        and local_candidate.exists()
        and local_candidate.resolve() != candidate.resolve()
    ):
        # Redirecting to the primary environment is only actionable when it
        # exists; otherwise the reader is sent to an empty path with no hint
        # that the real remedy is the documented setup procedure.
        remediation = (
            f"Use only the primary checkout environment at {candidate}; do not "
            "install packages or create another environment here."
            if candidate.exists()
            else f"The primary checkout has no environment at {candidate}. Follow "
            "the AGENTS.md Environment Setup section there; do not install "
            "packages or keep another environment in this worktree."
        )
        diagnostic = issue(
            "ERROR",
            "WT008",
            str(local_candidate),
            "linked worktree has a distinct forbidden secondary virtualenv.",
            remediation,
        )
        return None, [diagnostic]

    tools = WINDOWS_TOOLS if os_name == "nt" else POSIX_TOOLS
    qualified = {name: candidate / relative for name, relative in tools.items()}
    missing = [
        str(Path(".venv") / tools[name])
        for name in tools
        if not is_runnable(qualified[name], os_name=os_name, access=access)
    ]
    if missing:
        # In an ordinary checkout, creating this environment is the documented
        # next step, so blocking here would stop every fresh clone before it
        # could run Environment Setup. In a linked worktree the same state is
        # unrecoverable without the owner, because a second environment there
        # is forbidden.
        diagnostic = issue(
            "ERROR" if linked else "WARNING",
            "WT009",
            str(candidate),
            # "or not executable" because a POSIX file present without its
            # execute bit reaches this branch too, and calling that "missing"
            # sends the reader looking for a file that is already there.
            "required virtualenv tools are missing or not executable: "
            + ", ".join(missing)
            + ".",
            "Follow the AGENTS.md Environment Setup section in the primary checkout; "
            "do not create a secondary environment or use bare pip.",
        )
        return None, [diagnostic]
    return (
        VenvPaths(
            candidate, qualified["python"], qualified["pytest"], qualified["pre_commit"]
        ),
        [],
    )
