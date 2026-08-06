"""Primary-checkout virtualenv topology and executable diagnostics."""

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


def resolve_venv(
    *, repo_root: Path, git_dir: Path, common_dir: Path, os_name: str
) -> tuple[VenvPaths | None, list[Diagnostic]]:
    """Resolve the sole allowed environment for a normal or linked checkout."""
    common = common_dir.resolve()
    linked = git_dir.resolve() != common
    candidate = (common.parent if linked else repo_root) / ".venv"
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
        if not qualified[name].is_file()
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
            "required virtualenv tools are missing: " + ", ".join(missing) + ".",
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
