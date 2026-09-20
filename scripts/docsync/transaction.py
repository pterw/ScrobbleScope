"""Recoverable multi-file publication for the managed documentation corpus.

A close-out rewrites several documents at once. Half of that transition is
worse than none of it: an index that names pages nobody wrote, or a rotated
finding deleted from the active file and never appended to the archive, loses
history silently. So publication takes an exclusive lock, proves every source
it read is still byte-identical, journals the before-image of every file it
will touch, writes through same-directory temporaries, and restores the exact
prior bytes when anything at all goes wrong -- including an interrupt.

The journal survives the process. A run killed between two writes leaves it
behind, and the next publication replays it before accepting new work. If a
journalled file no longer matches either the before-image or the content the
interrupted run wrote, someone edited it in the meantime: recovery refuses
rather than overwriting that edit.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
from collections.abc import Iterator, Mapping
from pathlib import Path

from docsync.models import SyncError

#: Runtime state, written beside the archive it guards. Both are ignored by
#: Git: a lock or a half-finished journal is machine state for one run, not
#: repository content, and committing either would publish a stale claim that
#: a writer is active.
LOCK_NAME = ".docsync.lock"
JOURNAL_NAME = ".docsync.journal"

#: Suffix for the staged write. It lands in the destination directory so the
#: final `os.replace` is a same-filesystem rename, which is atomic; a system
#: temporary directory can be on another volume, where the replace degrades
#: to a copy and stops being atomic.
_STAGE_SUFFIX = ".docsync-stage"

_JOURNAL_VERSION = 1


def resolve_within(root: Path, candidate: Path | str) -> Path:
    """Return ``candidate`` resolved under ``root``, rejecting every escape.

    This is a real security boundary, not a tidiness check: a page reference
    or a managed path comes out of a Markdown index that anyone can edit, and
    a `..`, an absolute path, or a symlink would let that text direct a write
    anywhere the process can reach. Each component between the root and the
    target is inspected, because a symlinked *directory* redirects a path
    whose own final component is perfectly ordinary.
    """
    root_real = Path(root).resolve()
    if not root_real.is_dir():
        raise SyncError(f"Archive root is not a directory: {root}")

    target = Path(candidate)
    if not target.is_absolute():
        target = root_real / target
    if ".." in target.parts:
        raise SyncError(f"Path escapes the archive root: {candidate}")

    # Walk down from the root so a symlinked ancestor is caught even when the
    # leaf does not exist yet.
    try:
        relative = target.relative_to(root_real)
    except ValueError:
        relative = None
    if relative is None:
        # The path may still be inside once the root's own symlinks resolve.
        resolved = target.resolve()
        if not resolved.is_relative_to(root_real):
            raise SyncError(f"Path escapes the archive root: {candidate}")
        relative = resolved.relative_to(root_real)

    walked = root_real
    for part in relative.parts:
        walked = walked / part
        if walked.is_symlink():
            raise SyncError(
                f"Refusing to follow a symlink inside the archive: {walked}"
            )
    if walked.exists() and not walked.resolve().is_relative_to(root_real):
        raise SyncError(f"Path escapes the archive root: {candidate}")
    return walked


def _read(path: Path) -> bytes | None:
    """Return the file's bytes, or None when it does not exist."""
    return path.read_bytes() if path.is_file() else None


def _digest(payload: bytes | None) -> str | None:
    return None if payload is None else hashlib.sha256(payload).hexdigest()


def _b64encode(payload: bytes | None) -> str | None:
    """Base64-encode ``payload`` for journal storage, or None when absent.

    Kept as its own helper (mirroring `_digest`) so the None-check happens on
    a plain parameter: narrowing a dict subscript expression like
    `before[path]` inside a ternary does not carry across branches for a
    type checker, but narrowing a local parameter does.
    """
    return None if payload is None else base64.b64encode(payload).decode("ascii")


def _stage_and_replace(path: Path, payload: bytes) -> None:
    """Write ``payload`` through a staged same-directory temporary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_name(path.name + _STAGE_SUFFIX)
    with open(stage, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(stage, path)


def _atomic_write(path: Path, payload: bytes) -> None:
    """Forward-pass write. Kept separate from `_restore` on purpose.

    Undoing a write must not share a failure seam with the write itself, so
    rollback and recovery reach `_stage_and_replace` directly rather than
    through this function.
    """
    _stage_and_replace(path, payload)


def _apply(path: Path, payload: bytes | None) -> None:
    """Write or delete one path during the forward pass."""
    if payload is None:
        if path.exists():
            path.unlink()
        return
    _atomic_write(path, payload)


def _restore(path: Path, payload: bytes | None) -> None:
    """Put one file back to a recorded before-image."""
    if payload is None:
        if path.exists():
            path.unlink()
        return
    _stage_and_replace(path, payload)


def _write_journal(
    root: Path,
    before: Mapping[Path, bytes | None],
    after: Mapping[Path, bytes | None],
) -> None:
    """Record every before-image durably before the first write lands."""
    entries = [
        {
            "path": os.path.relpath(path, root).replace("\\", "/"),
            "before": _b64encode(before[path]),
            "after": _digest(after.get(path)),
        }
        for path in sorted(before)
    ]
    payload = json.dumps(
        {"version": _JOURNAL_VERSION, "entries": entries}, separators=(",", ":")
    ).encode("utf-8")
    journal = Path(root) / JOURNAL_NAME
    with open(journal, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _recover(root: Path) -> None:
    """Replay an interrupted run's journal, or refuse to proceed.

    Recovery is deliberately unforgiving. A file that matches neither the
    before-image nor the bytes the interrupted run wrote was changed by
    something else, and silently reverting that change would destroy work no
    journal knows about. The journal stays on disk so the operator can see
    what was in flight.
    """
    journal = Path(root) / JOURNAL_NAME
    if not journal.is_file():
        return
    try:
        document = json.loads(journal.read_text(encoding="utf-8"))
        version = int(document["version"])
        entries = list(document["entries"])
    except (ValueError, KeyError, TypeError) as error:
        raise SyncError(
            f"Unreadable publication journal at {journal}: {error}"
        ) from None
    if version != _JOURNAL_VERSION:
        raise SyncError(
            f"Publication journal at {journal} has unsupported version {version}."
        )

    restores: dict[Path, bytes | None] = {}
    for entry in entries:
        path = resolve_within(root, entry["path"])
        raw = entry.get("before")
        before = None if raw is None else base64.b64decode(raw)
        current = _read(path)
        if current == before:
            continue
        if _digest(current) != entry.get("after"):
            raise SyncError(
                f"{path} changed outside docsync after an interrupted "
                f"publication. Reconcile it by hand, then remove {journal}."
            )
        restores[path] = before

    for path, payload in restores.items():
        _restore(path, payload)
    journal.unlink()


@contextlib.contextmanager
def _exclusive_lock(root: Path) -> Iterator[None]:
    """Hold the archive's single-writer lock for the duration of the block."""
    lock = Path(root) / LOCK_NAME
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SyncError(
            f"Another docsync writer holds {lock}. Wait for it to finish, or "
            f"remove the lock if no publication is running."
        ) from None
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def publish(
    root: Path,
    updates: Mapping[Path, bytes | None],
    expected: Mapping[Path, bytes | None],
) -> None:
    """Apply ``updates`` atomically, or leave every file exactly as it was.

    ``updates`` maps a path to its new bytes, or to None to delete it.
    ``expected`` maps every path the plan *read* -- not only the ones it
    writes -- to the bytes it held when the plan was computed. A plan built
    from a document someone has since edited is stale, and publishing it
    would overwrite that edit with a decision made about different content.
    """
    root = Path(root)
    targets = {resolve_within(root, path): payload for path, payload in updates.items()}
    sources = {
        resolve_within(root, path): payload for path, payload in expected.items()
    }

    with _exclusive_lock(root):
        _recover(root)

        for path, before in sources.items():
            current = _read(path)
            if current != before:
                raise SyncError(f"Source changed before publication: {path}")

        before_images = {path: _read(path) for path in targets}
        if not targets:
            return
        _write_journal(root, before_images, targets)
        journal = root / JOURNAL_NAME
        try:
            # Deletions first, then writes. The order is fixed so a failure
            # mid-run always has the same shape, and so a rollback replaying
            # before-images cannot race a delete against a re-creation.
            for path in sorted(path for path, new in targets.items() if new is None):
                _apply(path, None)
            for path in sorted(
                path for path, new in targets.items() if new is not None
            ):
                _apply(path, targets[path])
        except BaseException:
            # A rollback that itself fails must leave the journal behind: the
            # next publication replays it, which is the only remaining way
            # back to a consistent corpus.
            for path, payload in before_images.items():
                _restore(path, payload)
            journal.unlink(missing_ok=True)
            raise
        journal.unlink(missing_ok=True)
