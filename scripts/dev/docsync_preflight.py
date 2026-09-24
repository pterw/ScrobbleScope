"""Commit-candidate documentation preflight for docsync.

Two modes share one checker invocation:

``--staged`` builds a disposable corpus from the Git *index* -- what the
commit would actually record -- and runs the on-disk (trusted) docsync
checker against it. This is what lets a document that is good on disk but
bad as staged fail here, and a document that is bad on disk but not being
committed pass: the candidate is exactly the tree ``git commit`` would write
right now, nothing more.

``--worktree`` runs the same checker directly against the current checkout,
with no Git-index snapshot to build. In CI the checkout already *is* the
commit under test, so there is nothing else to preserve. Locally, though,
under pre-commit's own stash isolation (it stashes unstaged changes before
running hooks and restores them after), the on-disk tree *already is* the
staged content by the time a pre-commit-managed hook runs -- which makes
``--worktree`` the default local commit path whenever the raw Git hook
wrapper (see ``install_docsync_hook.py``) is not the active mechanism. So
``--worktree`` still rejects staged control-plane changes exactly like
``--staged`` does, keyed on the same ``git diff --cached`` (empty, and
therefore a no-op, whenever the index already equals ``HEAD`` -- the CI
case, and any case where a control-plane change is already committed rather
than staged).

Both modes resolve a qualified interpreter rather than trusting PATH (see
``require_python`` and ``resolve_worktree_python``), and both return the
checker's own exit code unmodified -- a caller that collapsed every failure
to 1 could not tell a documentation defect (the checker's own diagnostic
exit) from a tool-resolution failure (this script's own precondition
guard), so this script keeps three distinct exit families instead.

See "Commit preflight" in
docs/superpowers/specs/2026-09-15-docsync-closeout-archives-design.md for
the approved design this implements.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.dev._worktree_guard_venv import (  # noqa: E402
    POSIX_TOOLS,
    WINDOWS_TOOLS,
    is_runnable,
)

Runner = Callable[..., subprocess.CompletedProcess]

#: Where the trusted, already-committed checker lives, relative to whatever
#: checkout is supplying it (the repository being validated, not the
#: candidate corpus itself) -- see ``run_docsync_check``.
DOCSYNC_ENTRY_POINT = Path("scripts/doc_state_sync.py")

# Paths whose staged content changes what the checker's own logic *means*.
# Running the check against a corpus while the checker that grades it is
# mid-change tests a moving target: a stale checker can wave through content
# the new rules would flag, or block content the new rules would accept
# either way. This repository's chosen policy (see the module docstring and
# task-4-report.md "trusted execution policy") is to refuse rather than
# guess which version of the rules should apply.
#
# Files are matched by exact equality, never a prefix: naive prefix
# matching let a name like "config/docsync.tomlx" match against
# "config/docsync.toml".
# Only directory entries (always written with a trailing "/") use
# ``startswith``, since a file nested inside one cannot be enumerated here
# in advance.
CONTROL_PLANE_DIRECTORIES: tuple[str, ...] = ("scripts/docsync/",)
CONTROL_PLANE_FILES: tuple[str, ...] = (
    "scripts/doc_state_sync.py",
    "scripts/dev/docsync_preflight.py",
    "config/docsync.toml",
)


def _is_control_plane_path(path: str) -> bool:
    """Whether ``path`` is part of the checker's own control-plane code."""
    return path in CONTROL_PLANE_FILES or any(
        path.startswith(directory) for directory in CONTROL_PLANE_DIRECTORIES
    )


EXIT_OK = 0
EXIT_PRECONDITION_ERROR = 2
EXIT_CONTROL_PLANE_REJECTED = 3


class PreflightError(RuntimeError):
    """A precondition failed before any docsync check could run."""


# --------------------------------------------------------------------- #
# Git plumbing                                                           #
# --------------------------------------------------------------------- #


def _run_git(
    args: Sequence[str], *, cwd: Path, runner: Runner = subprocess.run
) -> subprocess.CompletedProcess:
    """Run one Git command as text and return its completed process.

    Failures come back as data (a nonzero ``returncode``), never an
    exception, so each call site decides what that means for its own step.
    """
    return runner(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )


def repo_root(cwd: Path, *, runner: Runner = subprocess.run) -> Path:
    """Return the working tree root Git reports for ``cwd``."""
    result = _run_git(["rev-parse", "--show-toplevel"], cwd=cwd, runner=runner)
    if result.returncode != 0:
        raise PreflightError(
            f"git rev-parse --show-toplevel failed: {result.stderr.strip()}"
        )
    return Path(result.stdout.strip())


def primary_checkout_root(cwd: Path, *, runner: Runner = subprocess.run) -> Path:
    """Return the primary checkout for ``cwd``, resolving a linked worktree.

    The common Git directory is always ``<primary checkout>/.git``: in the
    primary checkout it equals the local ``.git``, and in a linked worktree
    Git points it at the shared metadata directory instead. Taking its
    parent gives the primary checkout root in both cases, with no special
    detection of which one ``cwd`` is.
    """
    result = _run_git(
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=cwd,
        runner=runner,
    )
    if result.returncode != 0:
        raise PreflightError(
            f"git rev-parse --git-common-dir failed: {result.stderr.strip()}"
        )
    return Path(result.stdout.strip()).parent


def unresolved_paths(root: Path, *, runner: Runner = subprocess.run) -> list[str]:
    """Return every path with an unresolved merge-conflict stage in the index."""
    result = _run_git(["ls-files", "-u", "-z"], cwd=root, runner=runner)
    if result.returncode != 0:
        raise PreflightError(f"git ls-files -u failed: {result.stderr.strip()}")
    paths: set[str] = set()
    for record in result.stdout.split("\0"):
        if not record:
            continue
        # Format: "<mode> <sha> <stage>\t<path>" -- one line per stage, so a
        # single conflicted file appears up to three times.
        _, _, path = record.partition("\t")
        if path:
            paths.add(path)
    return sorted(paths)


def staged_paths(root: Path, *, runner: Runner = subprocess.run) -> list[str]:
    """Return every path this commit's index changes relative to HEAD.

    A rename or copy contributes both its old and new path, so a control-
    plane rename in either direction is still caught by prefix matching.
    """
    result = _run_git(
        ["diff", "--cached", "--name-status", "-M", "-z"], cwd=root, runner=runner
    )
    if result.returncode != 0:
        raise PreflightError(f"git diff --cached failed: {result.stderr.strip()}")
    fields = [field for field in result.stdout.split("\0") if field]
    paths: list[str] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        if status[:1] in ("R", "C"):
            paths.append(fields[index + 1])
            paths.append(fields[index + 2])
            index += 3
        else:
            paths.append(fields[index + 1])
            index += 2
    return paths


def staged_control_plane_paths(
    root: Path, *, runner: Runner = subprocess.run
) -> list[str]:
    """Return staged paths that would change the checker's own behaviour."""
    return sorted(
        {
            path
            for path in staged_paths(root, runner=runner)
            if _is_control_plane_path(path)
        }
    )


def _print_control_plane_refusal(control_plane: Sequence[str], *, stderr) -> None:
    """Print the shared staged-control-plane refusal for either mode.

    The owner ruling (2026-09-19) forbids ``git commit --no-verify``
    absolutely (AGENTS.md anti-pattern 7 / CLAUDE.md); the one documented
    escape is pre-commit's own ``SKIP``, which by name skips only the
    ``doc-state-sync-check`` hook and still runs every other configured
    check. The operator is then expected to run
    ``doc_state_sync.py --check`` directly; CI's own preflight is the
    backstop either way.
    """
    print(
        "ERROR docsync control-plane code is staged in this commit: "
        + ", ".join(control_plane),
        file=stderr,
    )
    print(
        "Refusing to run the checker against a candidate corpus while the "
        "checker's own logic is part of the same commit -- see 'Commit "
        "preflight' in docs/superpowers/specs/2026-09-15-docsync-closeout"
        "-archives-design.md. The only supported local escape is "
        "'SKIP=doc-state-sync-check git commit', which skips only this "
        "hook and still runs every other configured check. Then run "
        "'doc_state_sync.py --check' directly; CI's preflight is the "
        "backstop for control-plane changes either way.",
        file=stderr,
    )


@contextlib.contextmanager
def candidate_corpus(root: Path, *, runner: Runner = subprocess.run) -> Iterator[Path]:
    """Materialize the staged index as a disposable, self-contained checkout.

    Building it from a ``git write-tree`` / ``git archive`` pair, rather
    than copying the working tree, is what makes a document good on disk
    but bad as staged fail, and a document bad on disk but not staged pass:
    the tree this produces is exactly what ``git commit`` would record right
    now -- no untracked files, no local ``.env``, no credentials, because
    ``git archive`` only ever emits tracked blobs from the given tree.

    ``git write-tree`` and ``git archive`` are read-only plumbing against
    the *real* repository: no ref moves, nothing is committed, and neither
    the real working tree nor the real index is touched. ``git init`` and
    ``git add`` run only inside the fresh temporary directory this yields,
    never against the real repository, purely so the candidate has its own
    disposable index: ``docsync.integrity.collect_tracked_paths`` shells out
    to ``git ls-files`` wherever the checker's ``cwd`` is, and an empty
    index there would make every tracked-path check see zero files. ``-f``
    on the candidate's own ``git add`` bypasses any ``.gitignore`` the
    committed tree itself carries, so an ignore pattern cannot silently
    shrink what the checker considers tracked relative to what was staged.
    """
    tree_result = _run_git(["write-tree"], cwd=root, runner=runner)
    if tree_result.returncode != 0:
        raise PreflightError(f"git write-tree failed: {tree_result.stderr.strip()}")
    tree_sha = tree_result.stdout.strip()

    archive = runner(
        ["git", "archive", "--format=tar", tree_sha],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    if archive.returncode != 0:
        stderr = archive.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        raise PreflightError(f"git archive failed: {stderr.strip()}")

    payload = archive.stdout
    if isinstance(payload, str):
        # A tar is bytes. Reaching here means a caller passed a text-mode
        # runner, and whatever decoding produced this string has already
        # lost bytes no encode can restore -- re-encoding it would hand the
        # extractor a corrupted archive that still looks like one. The
        # production call sets no `text=True`, so this is a wiring error.
        raise PreflightError(
            "git archive returned text, not bytes: the runner must not "
            "decode output for this call, or the tar payload is corrupted."
        )

    with tempfile.TemporaryDirectory(prefix="docsync-preflight-") as handle:
        dest = Path(handle)
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r|") as tar:
            # Python 3.12+ defaults extraction filtering off but supports an
            # explicit one; older interpreters lack the parameter entirely.
            # The archive only ever contains this repository's own tracked
            # paths, but passing the strict filter where it exists costs
            # nothing and rejects anything unexpected (symlinks escaping
            # ``dest``, device files) before it can land on disk.
            if sys.version_info < (3, 12):  # pragma: no cover - CI pins 3.13
                # Extracting unfiltered would accept members this code never
                # inspects -- paths climbing out of `dest`, symlinks, device
                # nodes. Refusing is correct rather than cautious: nothing
                # supported runs here, CI pins 3.13, and a preflight that
                # cannot extract safely must not extract at all.
                raise PreflightError(
                    "building the candidate corpus needs Python 3.12 or newer "
                    "for filtered tar extraction; this interpreter is "
                    f"{sys.version_info.major}.{sys.version_info.minor}."
                )
            tar.extractall(dest, filter="data")

        init = _run_git(["init", "-q"], cwd=dest, runner=runner)
        if init.returncode != 0:
            raise PreflightError(f"git init on candidate failed: {init.stderr.strip()}")
        add = _run_git(["add", "-A", "-f"], cwd=dest, runner=runner)
        if add.returncode != 0:
            raise PreflightError(f"git add on candidate failed: {add.stderr.strip()}")
        yield dest


# --------------------------------------------------------------------- #
# Interpreter resolution                                                 #
# --------------------------------------------------------------------- #


def _qualified_python_path(root: Path, *, os_name: str) -> Path:
    table = WINDOWS_TOOLS if os_name == "nt" else POSIX_TOOLS
    return root / ".venv" / table["python"]


def require_python(
    root: Path, *, os_name: str = None, access: Callable[..., bool] = None
) -> Path:
    """Return the primary checkout's qualified Python, or fail closed.

    Trusting PATH, or any interpreter that is not this repository's own
    pinned virtualenv, is exactly the retired-environment failure AGENTS.md
    Environment Setup warns about (incident 2026-03-04): the wrong
    interpreter can silently run against the wrong package set. Unlike
    ``resolve_worktree_python``, this never falls back -- the staged
    preflight is a local, interactive commit-time check where the qualified
    environment is expected to already exist.
    """
    import os as _os

    os_name = _os.name if os_name is None else os_name
    access = _os.access if access is None else access
    candidate = _qualified_python_path(root, os_name=os_name)
    if not is_runnable(candidate, os_name=os_name, access=access):
        raise PreflightError(
            f"No qualified Python interpreter at {candidate}. Follow the "
            "AGENTS.md Environment Setup section in the primary checkout; "
            "this preflight refuses to fall back to PATH."
        )
    return candidate


def resolve_worktree_python(
    root: Path,
    *,
    os_name: str = None,
    access: Callable[..., bool] = None,
    sys_executable: str = None,
) -> Path:
    """Prefer the primary checkout's qualified interpreter; else the current one.

    CI has no repository virtualenv -- dependencies land in the runner's
    system Python -- so demanding ``.venv`` there would fail every workflow
    run. ``sys.executable`` is still qualified in the sense that matters
    here: it is the exact interpreter already running this process, not a
    second PATH lookup that could silently resolve to something else.
    """
    import os as _os

    os_name = _os.name if os_name is None else os_name
    access = _os.access if access is None else access
    sys_executable = sys.executable if sys_executable is None else sys_executable
    candidate = _qualified_python_path(root, os_name=os_name)
    if is_runnable(candidate, os_name=os_name, access=access):
        return candidate
    return Path(sys_executable)


# --------------------------------------------------------------------- #
# Running the checker                                                    #
# --------------------------------------------------------------------- #


def run_docsync_check(
    python_exe: Path,
    entry_point: Path,
    *,
    cwd: Path,
    runner: Runner = subprocess.run,
) -> tuple[int, str, str]:
    """Invoke the on-disk docsync CLI's ``--check`` mode against ``cwd``.

    ``entry_point`` is always a path the caller resolved against the real
    repository being validated, never against ``cwd`` when ``cwd`` is a
    candidate: the script executed here must be the trusted,
    already-committed checker, not a copy that might live inside a
    candidate this same commit is trying to validate. This alone does not
    authorize running a checker a commit is simultaneously changing -- see
    ``_is_control_plane_path``, which is the complementary guard that
    refuses before this function is ever called.

    An ``OSError`` (most commonly ``FileNotFoundError``, when the resolved
    interpreter or entry point no longer exists at invocation time) is
    caught and re-raised as ``PreflightError``, so both callers' existing
    ``except PreflightError`` handling turns it into
    ``EXIT_PRECONDITION_ERROR`` instead of an uncaught traceback.
    """
    try:
        result = runner(
            [str(python_exe), str(entry_point), "--check"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise PreflightError(
            f"failed to invoke the docsync checker ({python_exe} "
            f"{entry_point} --check): {exc}"
        ) from None
    return result.returncode, result.stdout, result.stderr


# --------------------------------------------------------------------- #
# Orchestration                                                          #
# --------------------------------------------------------------------- #


def run_staged(
    cwd: Path,
    *,
    runner: Runner = subprocess.run,
    python_exe: Path | None = None,
    entry_point: Path | None = None,
    stdout=None,
    stderr=None,
) -> int:
    """Validate the commit candidate the Git index currently describes."""
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    try:
        root = repo_root(cwd, runner=runner)

        unresolved = unresolved_paths(root, runner=runner)
        if unresolved:
            print(
                "ERROR unresolved merge-conflict stage(s) in the index: "
                + ", ".join(unresolved),
                file=stderr,
            )
            print(
                "Resolve every conflict before this preflight can build a "
                "commit candidate from the index.",
                file=stderr,
            )
            return EXIT_PRECONDITION_ERROR

        control_plane = staged_control_plane_paths(root, runner=runner)
        if control_plane:
            _print_control_plane_refusal(control_plane, stderr=stderr)
            return EXIT_CONTROL_PLANE_REJECTED

        primary_root = primary_checkout_root(cwd, runner=runner)
        resolved_python = (
            python_exe if python_exe is not None else require_python(primary_root)
        )
        # The checker script itself is resolved against `root` (the
        # worktree actually being committed to), not `primary_root`: a
        # linked worktree can legitimately sit on a different branch, with
        # a different docsync schema, than the primary checkout its .venv
        # lives in. `primary_root` supplies only the shared interpreter;
        # the code that interprets *this* worktree's documents must be
        # *this* worktree's own on-disk (already-committed, non-staged)
        # copy.
        resolved_entry = (
            entry_point if entry_point is not None else root / DOCSYNC_ENTRY_POINT
        )

        with candidate_corpus(root, runner=runner) as candidate:
            returncode, out, err = run_docsync_check(
                resolved_python, resolved_entry, cwd=candidate, runner=runner
            )
    except PreflightError as exc:
        print(f"ERROR {exc}", file=stderr)
        return EXIT_PRECONDITION_ERROR

    if out:
        print(out, end="", file=stdout)
    if err:
        print(err, end="", file=stderr)
    return returncode


def run_worktree(
    cwd: Path,
    *,
    runner: Runner = subprocess.run,
    python_exe: Path | None = None,
    entry_point: Path | None = None,
    stdout=None,
    stderr=None,
) -> int:
    """Validate the current checkout directly (the CI check).

    Also rejects staged control-plane changes, exactly like ``run_staged``:
    under pre-commit's own stash isolation, the on-disk tree already *is*
    the staged content by the time a pre-commit-managed hook runs, which
    makes this the default *local* commit path whenever the raw Git hook
    wrapper is not installed -- not only the CI path. The same
    ``git diff --cached`` call this reuses is empty (and therefore a no-op)
    whenever the index already equals ``HEAD``, which is always true in CI
    and in any case where a control-plane change is already committed
    rather than staged, so no separate CI-vs-local branch is needed.
    """
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    try:
        root = repo_root(cwd, runner=runner)

        control_plane = staged_control_plane_paths(root, runner=runner)
        if control_plane:
            _print_control_plane_refusal(control_plane, stderr=stderr)
            return EXIT_CONTROL_PLANE_REJECTED

        primary_root = primary_checkout_root(cwd, runner=runner)
        resolved_python = (
            python_exe
            if python_exe is not None
            else resolve_worktree_python(primary_root)
        )
        # As in run_staged: the checker script comes from `root` (this
        # checkout), the interpreter from `primary_root` (the shared venv).
        # In CI the two are identical (a single fresh checkout is its own
        # primary), so this only matters for a linked worktree run locally.
        resolved_entry = (
            entry_point if entry_point is not None else root / DOCSYNC_ENTRY_POINT
        )
        returncode, out, err = run_docsync_check(
            resolved_python, resolved_entry, cwd=root, runner=runner
        )
    except PreflightError as exc:
        print(f"ERROR {exc}", file=stderr)
        return EXIT_PRECONDITION_ERROR

    if out:
        print(out, end="", file=stdout)
    if err:
        print(err, end="", file=stderr)
    return returncode


# --------------------------------------------------------------------- #
# CLI                                                                     #
# --------------------------------------------------------------------- #


def _build_parser() -> argparse.ArgumentParser:
    """Declare the two mutually exclusive, required preflight modes."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the docsync checker against a commit candidate (--staged) "
            "or the current checkout (--worktree)."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--staged",
        action="store_true",
        help="Validate the Git index as the next commit would record it.",
    )
    mode.add_argument(
        "--worktree",
        action="store_true",
        help="Validate the current checkout directly (the CI check).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the selected preflight mode."""
    args = _build_parser().parse_args(argv)
    cwd = Path.cwd()
    if args.staged:
        return run_staged(cwd)
    return run_worktree(cwd)


if __name__ == "__main__":
    raise SystemExit(main())
