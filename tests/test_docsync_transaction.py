"""Recoverable multi-file publication: containment, exclusion, rollback."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from docsync import transaction
from docsync.models import SyncError
from docsync.transaction import JOURNAL_NAME, LOCK_NAME, publish, resolve_within


@pytest.fixture
def root(tmp_path: Path) -> Path:
    archive = tmp_path / "archive"
    (archive / "pages").mkdir(parents=True)
    (archive / "INDEX.md").write_bytes(b"# index\n")
    (archive / "pages" / "one.md").write_bytes(b"# one\n")
    return archive


def _state(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


# ---------------------------------------------------------------------------
# Happy path and byte fidelity
# ---------------------------------------------------------------------------


def test_publish_writes_creates_and_deletes(root):
    index = root / "INDEX.md"
    one = root / "pages" / "one.md"
    two = root / "pages" / "two.md"

    publish(
        root,
        {index: b"# new index\n", two: b"# two\n", one: None},
        {index: b"# index\n", one: b"# one\n"},
    )

    assert index.read_bytes() == b"# new index\n"
    assert two.read_bytes() == b"# two\n"
    assert not one.exists()


def test_publish_preserves_bytes_exactly(root):
    target = root / "pages" / "bytes.md"
    payload = "crlf\r\nnbsp tail  \nemoji ✓\n".encode()

    publish(root, {target: payload}, {})

    assert target.read_bytes() == payload


def test_publish_creates_missing_parent_directories(root):
    target = root / "cold" / "deep" / "page.md"

    publish(root, {target: b"x\n"}, {})

    assert target.read_bytes() == b"x\n"


def test_publish_releases_its_lock(root):
    publish(root, {root / "a.md": b"a\n"}, {})

    assert not (root / LOCK_NAME).exists()
    assert not (root / JOURNAL_NAME).exists()


def test_empty_publication_is_accepted(root):
    before = _state(root)

    publish(root, {}, {root / "INDEX.md": b"# index\n"})

    assert _state(root) == before


# ---------------------------------------------------------------------------
# Containment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "escape",
    ["../outside.md", "pages/../../outside.md", "pages/../../../outside.md"],
)
def test_parent_relative_escape_is_rejected(root, escape):
    with pytest.raises(SyncError):
        publish(root, {root / escape: b"x\n"}, {})


def test_absolute_path_outside_the_root_is_rejected(root, tmp_path):
    outside = tmp_path / "outside.md"

    with pytest.raises(SyncError):
        publish(root, {outside: b"x\n"}, {})

    assert not outside.exists()


def test_escape_in_the_expected_map_is_rejected(root, tmp_path):
    with pytest.raises(SyncError):
        publish(root, {}, {tmp_path / "outside.md": None})


def test_symlinked_target_file_is_rejected(root, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"original\n")
    link = root / "pages" / "link.md"
    try:
        os.symlink(outside, link)
    except OSError:  # pragma: no cover - platform without symlink privilege
        pytest.skip("symlink creation is unavailable in this environment")

    with pytest.raises(SyncError, match="symlink"):
        publish(root, {link: b"hijacked\n"}, {})

    assert outside.read_bytes() == b"original\n"


def test_symlinked_parent_directory_is_rejected(root, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / "linked"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError:  # pragma: no cover - platform without symlink privilege
        pytest.skip("symlink creation is unavailable in this environment")

    with pytest.raises(SyncError, match="symlink"):
        publish(root, {link / "page.md": b"x\n"}, {})

    assert not (outside / "page.md").exists()


def test_resolve_within_accepts_a_contained_path(root):
    assert resolve_within(root, root / "pages" / "one.md") == (
        (root / "pages" / "one.md").resolve()
    )


# ---------------------------------------------------------------------------
# Preimage verification
# ---------------------------------------------------------------------------


def test_expected_absent_file_that_exists_is_rejected(root):
    with pytest.raises(SyncError, match="changed"):
        publish(root, {root / "a.md": b"a\n"}, {root / "INDEX.md": None})

    assert not (root / "a.md").exists()


def test_expected_present_file_that_is_missing_is_rejected(root):
    with pytest.raises(SyncError, match="changed"):
        publish(root, {root / "a.md": b"a\n"}, {root / "gone.md": b"content\n"})

    assert not (root / "a.md").exists()


def test_changed_read_input_that_receives_no_write_is_rejected(root):
    reference = root / "pages" / "one.md"
    reference.write_bytes(b"# edited by someone else\n")

    with pytest.raises(SyncError, match="changed"):
        publish(root, {root / "a.md": b"a\n"}, {reference: b"# one\n"})

    assert not (root / "a.md").exists()
    assert reference.read_bytes() == b"# edited by someone else\n"


# ---------------------------------------------------------------------------
# Writer exclusion
# ---------------------------------------------------------------------------


def test_concurrent_writer_is_rejected(root):
    (root / LOCK_NAME).write_text("4242", encoding="utf-8")
    before = _state(root)

    with pytest.raises(SyncError, match="writer"):
        publish(root, {root / "a.md": b"a\n"}, {})

    assert _state(root) == before
    assert (root / LOCK_NAME).exists()


def test_lock_is_released_after_a_failure(root):
    with pytest.raises(SyncError):
        publish(root, {root / "a.md": b"a\n"}, {root / "gone.md": b"content\n"})

    assert not (root / LOCK_NAME).exists()


# ---------------------------------------------------------------------------
# Failure, interruption, rollback
# ---------------------------------------------------------------------------


def test_publication_failure_rolls_every_file_back(root, monkeypatch):
    original = transaction._atomic_write
    calls = {"n": 0}

    def fake(path, payload):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise OSError("disk full")
        original(path, payload)

    monkeypatch.setattr(transaction, "_atomic_write", fake)
    before = _state(root)

    with pytest.raises(OSError, match="disk full"):
        publish(
            root,
            {
                root / "INDEX.md": b"# new\n",
                root / "pages" / "one.md": b"# new one\n",
                root / "pages" / "two.md": b"# two\n",
            },
            {},
        )

    assert _state(root) == before
    assert not (root / JOURNAL_NAME).exists()
    assert not (root / LOCK_NAME).exists()


def test_interruption_restores_exact_bytes(root, monkeypatch):
    original = transaction._atomic_write
    calls = {"n": 0}

    def fake(path, payload):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise KeyboardInterrupt
        original(path, payload)

    monkeypatch.setattr(transaction, "_atomic_write", fake)
    before = _state(root)

    with pytest.raises(KeyboardInterrupt):
        publish(
            root,
            {
                root / "INDEX.md": b"# new\n",
                root / "pages" / "one.md": b"# new one\n",
            },
            {},
        )

    assert _state(root) == before


def test_a_failed_run_restores_a_file_it_had_already_deleted(root, monkeypatch):
    def fake(path, payload):
        raise OSError("boom")

    monkeypatch.setattr(transaction, "_atomic_write", fake)
    before = _state(root)

    # Deletions are applied before writes, so the delete lands and the write
    # then fails: exactly the partial state rollback has to undo.
    with pytest.raises(OSError, match="boom"):
        publish(
            root,
            {root / "INDEX.md": None, root / "a.md": b"a\n"},
            {},
        )

    assert _state(root) == before
    assert not (root / "a.md").exists()


# ---------------------------------------------------------------------------
# Journal recovery
# ---------------------------------------------------------------------------


def test_stale_journal_is_recovered_before_new_work(root):
    victim = root / "pages" / "one.md"
    transaction._write_journal(root, {victim: b"# one\n"}, {victim: b"# half\n"})
    victim.write_bytes(b"# half\n")

    publish(root, {root / "a.md": b"a\n"}, {})

    assert victim.read_bytes() == b"# one\n"
    assert (root / "a.md").read_bytes() == b"a\n"
    assert not (root / JOURNAL_NAME).exists()


def test_stale_journal_restores_a_file_the_interrupted_run_deleted(root):
    victim = root / "pages" / "one.md"
    transaction._write_journal(root, {victim: b"# one\n"}, {victim: None})
    victim.unlink()

    publish(root, {}, {})

    assert victim.read_bytes() == b"# one\n"
    assert not (root / JOURNAL_NAME).exists()


def test_stale_journal_removes_a_file_the_interrupted_run_created(root):
    created = root / "pages" / "created.md"
    transaction._write_journal(root, {created: None}, {created: b"# new\n"})
    created.write_bytes(b"# new\n")

    publish(root, {}, {})

    assert not created.exists()
    assert not (root / JOURNAL_NAME).exists()


def test_recovery_never_overwrites_an_externally_changed_source(root):
    victim = root / "pages" / "one.md"
    transaction._write_journal(root, {victim: b"# one\n"}, {victim: b"# half\n"})
    victim.write_bytes(b"# a human edited this afterwards\n")

    with pytest.raises(SyncError, match="changed outside"):
        publish(root, {root / "a.md": b"a\n"}, {})

    assert victim.read_bytes() == b"# a human edited this afterwards\n"
    assert (root / JOURNAL_NAME).exists()
    assert not (root / "a.md").exists()
    assert not (root / LOCK_NAME).exists()


def test_recovery_accepts_a_journal_whose_writes_never_landed(root):
    victim = root / "pages" / "one.md"
    transaction._write_journal(root, {victim: b"# one\n"}, {victim: b"# half\n"})

    publish(root, {}, {})

    assert victim.read_bytes() == b"# one\n"
    assert not (root / JOURNAL_NAME).exists()


def test_malformed_journal_is_rejected_rather_than_ignored(root):
    (root / JOURNAL_NAME).write_text("not json", encoding="utf-8")

    with pytest.raises(SyncError, match="journal"):
        publish(root, {root / "a.md": b"a\n"}, {})

    assert not (root / "a.md").exists()


def test_journal_entries_may_not_escape_the_root(root, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"original\n")
    transaction._write_journal(root, {outside: b"original\n"}, {outside: b"x\n"})

    with pytest.raises(SyncError):
        publish(root, {}, {})

    assert outside.read_bytes() == b"original\n"
