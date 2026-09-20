"""Bounded archive pagination, index integrity, and cold-storage planning."""

from __future__ import annotations

import json
import os
from datetime import date
from hashlib import sha256
from pathlib import Path

import pytest
from docsync.archives import (
    INDEX_END_MARKER,
    INDEX_START_MARKER,
    PAGE_HEADER_LINES,
    ArchiveStore,
    normalize,
)
from docsync.models import SyncError
from docsync.transaction import publish

PROLOGUE = "\n".join(
    [
        "# FINDINGS Archive",
        "",
        "Resolved and no-action findings rotate here. Nothing is deleted.",
        "",
        "---",
    ]
)


def _entry(identifier: str, *, body: int = 6, completed: str | None = None) -> str:
    """Build one entry whose rendered line count is exactly known."""
    lines = [f"### {identifier}: a finding that was closed", ""]
    if completed is not None:
        lines += [f"**Completed:** {completed}", ""]
    lines += [f"body line {number}" for number in range(body)]
    return "\n".join(lines)


def _corpus(entries: list[str]) -> str:
    return PROLOGUE + "\n\n" + "\n\n".join(entries) + "\n"


def _store(tmp_path: Path, **kwargs) -> tuple[ArchiveStore, Path]:
    root = tmp_path / "findings"
    root.mkdir()
    return ArchiveStore(root, **kwargs), root / "FINDINGS_ARCHIVE.md"


def _apply(updates: dict[Path, bytes | None]) -> None:
    """Write a plan without going through the transaction layer."""
    for path, payload in updates.items():
        if payload is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def _manifest(index_path: Path) -> dict:
    text = index_path.read_text(encoding="utf-8")
    body = text.split(INDEX_START_MARKER, 1)[1].split(INDEX_END_MARKER, 1)[0]
    payload = body.strip().removeprefix("<!--").removesuffix("-->").strip()
    return json.loads(payload)


# ---------------------------------------------------------------------------
# Monoliths and flattening
# ---------------------------------------------------------------------------


def test_small_corpus_stays_a_single_monolith(tmp_path):
    store, index = _store(tmp_path)
    text = _corpus([_entry("F-1"), _entry("F-2")])

    updates = store.plan(index, text)
    _apply(updates)

    assert set(updates) == {index}
    assert INDEX_START_MARKER not in index.read_text(encoding="utf-8")
    assert store.read(index) == normalize(text)


def test_legacy_monolith_reads_as_the_same_logical_text(tmp_path):
    store, index = _store(tmp_path)
    text = _corpus([_entry("F-1"), _entry("F-2")])
    index.write_text(text, encoding="utf-8")

    assert store.read(index) == normalize(text)


def test_canonical_legacy_prologue_is_preserved_in_flattened_text(tmp_path):
    store, index = _store(tmp_path, max_lines=20)
    text = _corpus([_entry(f"F-{n}") for n in range(8)])

    _apply(store.plan(index, text))

    assert INDEX_START_MARKER in index.read_text(encoding="utf-8")
    assert store.read(index).startswith(PROLOGUE)
    assert store.read(index) == normalize(text)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


def test_pages_respect_the_500_line_target_including_headers(tmp_path):
    store, index = _store(tmp_path)
    entries = [_entry(f"F-{n}", body=20) for n in range(120)]
    text = _corpus(entries)

    _apply(store.plan(index, text))
    manifest = _manifest(index)

    assert len(manifest["pages"]) > 1
    for page in manifest["pages"]:
        rendered = store.page_path(index, page).read_text(encoding="utf-8")
        assert len(rendered.splitlines()) == page["lines"] <= 500
        assert rendered.splitlines()[:PAGE_HEADER_LINES]
    assert store.read(index) == normalize(text)


def test_no_entry_is_split_across_pages(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    entries = [_entry(f"F-{n}", body=6) for n in range(30)]
    text = _corpus(entries)

    _apply(store.plan(index, text))

    for page in _manifest(index)["pages"]:
        rendered = store.page_path(index, page).read_text(encoding="utf-8")
        body = "\n".join(rendered.splitlines()[PAGE_HEADER_LINES:])
        for block in body.split("\n\n\n"):
            assert block.strip()
        assert body.count("### ") == page["entries"]
    assert store.read(index) == normalize(text)


def test_packing_is_tight_against_the_target(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    text = _corpus([_entry(f"F-{n}", body=6) for n in range(30)])

    _apply(store.plan(index, text))
    pages = _manifest(index)["pages"]

    # Every page but the tail is full: one more entry (8 lines plus its
    # blank separator) would overflow the 40-line target.
    assert len(pages) > 1
    for page in pages[:-1]:
        assert page["lines"] + 1 + 8 > 40


def test_oversized_entry_gets_a_dedicated_page_marked_in_the_index(tmp_path):
    store, index = _store(tmp_path, max_lines=20)
    entries = [_entry("F-1"), _entry("F-BIG", body=60), _entry("F-2")]
    text = _corpus(entries)

    _apply(store.plan(index, text))
    manifest = _manifest(index)
    oversized = [page for page in manifest["pages"] if page["oversized"]]

    assert len(oversized) == 1
    assert oversized[0]["entries"] == 1
    assert oversized[0]["lines"] > 20
    assert "oversized" in index.read_text(encoding="utf-8")
    assert store.read(index) == normalize(text)


def test_nothing_is_truncated(tmp_path):
    store, index = _store(tmp_path, max_lines=20)
    text = _corpus([_entry(f"F-{n}", body=9) for n in range(12)])

    _apply(store.plan(index, text))
    flattened = store.read(index)

    for line in normalize(text).split("\n"):
        assert line in flattened.split("\n")
    assert flattened == normalize(text)


# ---------------------------------------------------------------------------
# Stability, appends and idempotence
# ---------------------------------------------------------------------------


def test_finalized_page_names_are_stable_on_append(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    first = [_entry(f"F-{n}", body=6) for n in range(30)]
    _apply(store.plan(index, _corpus(first)))
    before = [page["name"] for page in _manifest(index)["pages"]]
    finalized_bytes = {
        page["name"]: store.page_path(index, page).read_bytes()
        for page in _manifest(index)["pages"][:-1]
    }

    grown = first + [_entry(f"F-new-{n}", body=6) for n in range(8)]
    updates = store.plan(index, _corpus(grown))
    _apply(updates)
    after = [page["name"] for page in _manifest(index)["pages"]]

    assert after[: len(before) - 1] == before[: len(before) - 1]
    for page in _manifest(index)["pages"]:
        if page["name"] in finalized_bytes:
            assert (
                store.page_path(index, page).read_bytes()
                == (finalized_bytes[page["name"]])
            )
    assert store.read(index) == normalize(_corpus(grown))


def test_writable_tail_receives_entries_up_to_the_target(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    first = [_entry(f"F-{n}", body=6) for n in range(5)]
    _apply(store.plan(index, _corpus(first)))
    tail_before = _manifest(index)["pages"][-1]

    # A tail with only one entry has room for three more before the target.
    assert len(_manifest(index)["pages"]) == 2
    assert tail_before["entries"] == 1
    grown = first + [_entry("F-extra", body=6)]
    _apply(store.plan(index, _corpus(grown)))
    tail_after = _manifest(index)["pages"][-1]

    assert tail_after["name"] == tail_before["name"]
    assert tail_after["entries"] == tail_before["entries"] + 1


def test_repeated_planning_produces_no_further_changes(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    text = _corpus([_entry(f"F-{n}", body=6) for n in range(30)])
    _apply(store.plan(index, text))

    assert store.plan(index, text) == {}
    assert store.plan(index, store.read(index)) == {}


def test_migration_conserves_entry_ids_fingerprints_and_counts(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    entries = [_entry(f"F-{n}", body=6) for n in range(30)]
    text = _corpus(entries)
    index.write_text(text, encoding="utf-8")
    before = sorted(sha256(entry.encode("utf-8")).hexdigest() for entry in entries)

    _apply(store.plan(index, text))
    manifest = _manifest(index)
    flattened = store.read(index)

    assert sum(page["entries"] for page in manifest["pages"]) == len(entries)
    assert flattened.count("### F-") == len(entries)
    for number in range(30):
        assert f"### F-{number}:" in flattened
    # Each entry survives byte for byte, so the fingerprint set is unchanged.
    after = sorted(
        sha256(("### F-" + block.rstrip("\n")).encode("utf-8")).hexdigest()
        for block in flattened.split("### F-")[1:]
    )
    assert after == before
    assert flattened == normalize(text)


def test_a_planned_migration_publishes_atomically(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    text = _corpus([_entry(f"F-{n}", body=6) for n in range(30)])
    index.write_bytes(text.encode("utf-8"))

    publish(index.parent, store.plan(index, text), {index: text.encode("utf-8")})

    assert store.read(index) == normalize(text)
    assert store.plan(index, text) == {}


def test_publication_refuses_a_plan_built_from_a_changed_source(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    text = _corpus([_entry(f"F-{n}", body=6) for n in range(30)])
    index.write_bytes(text.encode("utf-8"))
    updates = store.plan(index, text)
    index.write_bytes((text + "\n### F-late: arrived after planning\n").encode("utf-8"))

    with pytest.raises(SyncError, match="changed"):
        publish(index.parent, updates, {index: text.encode("utf-8")})

    assert not (index.parent / "pages").exists()


def test_legacy_body_is_not_left_beside_the_paginated_copy(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    text = _corpus([_entry(f"F-{n}", body=6) for n in range(30)])
    index.write_text(text, encoding="utf-8")

    _apply(store.plan(index, text))
    rendered_index = index.read_text(encoding="utf-8")

    assert INDEX_START_MARKER in rendered_index
    assert "### F-0:" not in rendered_index
    assert "body line 0" not in rendered_index


# ---------------------------------------------------------------------------
# Index integrity
# ---------------------------------------------------------------------------


def _paginate(tmp_path, **kwargs):
    store, index = _store(tmp_path, max_lines=kwargs.pop("max_lines", 40))
    text = _corpus([_entry(f"F-{n}", body=6) for n in range(30)])
    _apply(store.plan(index, text))
    return store, index, text


def _rewrite_manifest(index: Path, manifest: dict) -> None:
    text = index.read_text(encoding="utf-8")
    head, rest = text.split(INDEX_START_MARKER, 1)
    _, tail = rest.split(INDEX_END_MARKER, 1)
    payload = json.dumps(manifest, separators=(",", ":"))
    index.write_text(
        f"{head}{INDEX_START_MARKER}\n<!-- {payload} -->\n{INDEX_END_MARKER}{tail}",
        encoding="utf-8",
    )


def test_malformed_manifest_is_rejected(tmp_path):
    _, index, _ = _paginate(tmp_path)
    store = ArchiveStore(index.parent, max_lines=40)
    text = index.read_text(encoding="utf-8")
    head, rest = text.split(INDEX_START_MARKER, 1)
    _, tail = rest.split(INDEX_END_MARKER, 1)
    index.write_text(
        f"{head}{INDEX_START_MARKER}\n<!-- not json -->\n{INDEX_END_MARKER}{tail}",
        encoding="utf-8",
    )

    with pytest.raises(SyncError, match="manifest"):
        store.read(index)


def test_unknown_manifest_version_is_rejected(tmp_path):
    store, index, _ = _paginate(tmp_path)
    manifest = _manifest(index)
    manifest["version"] = 99
    _rewrite_manifest(index, manifest)

    with pytest.raises(SyncError, match="version"):
        store.read(index)


def test_missing_page_is_rejected(tmp_path):
    store, index, _ = _paginate(tmp_path)
    manifest = _manifest(index)
    store.page_path(index, manifest["pages"][0]).unlink()

    with pytest.raises(SyncError, match="missing"):
        store.read(index)


def test_duplicate_page_reference_is_rejected(tmp_path):
    store, index, _ = _paginate(tmp_path)
    manifest = _manifest(index)
    manifest["pages"].append(dict(manifest["pages"][0]))
    _rewrite_manifest(index, manifest)

    with pytest.raises(SyncError, match="more than once"):
        store.read(index)


def test_orphaned_managed_page_is_rejected(tmp_path):
    store, index, _ = _paginate(tmp_path)
    manifest = _manifest(index)
    orphan = store.page_path(index, manifest["pages"][0]).with_name(
        "FINDINGS_ARCHIVE_0099.md"
    )
    orphan.write_text("# orphan\n", encoding="utf-8")

    with pytest.raises(SyncError, match="not referenced"):
        store.read(index)


def test_managed_pages_beside_a_legacy_monolith_are_rejected(tmp_path):
    store, index = _store(tmp_path, max_lines=40)
    text = _corpus([_entry(f"F-{n}", body=6) for n in range(3)])
    index.write_text(text, encoding="utf-8")
    stray = index.parent / "pages" / "FINDINGS_ARCHIVE_0001.md"
    stray.parent.mkdir()
    stray.write_text("# a stray paginated copy\n", encoding="utf-8")

    with pytest.raises(SyncError, match="not referenced"):
        store.read(index)
    with pytest.raises(SyncError, match="not referenced"):
        store.plan(index, text)
    assert stray.exists()


def test_unrelated_archive_pages_in_a_shared_root_are_not_orphans(tmp_path):
    store, index, _ = _paginate(tmp_path)
    neighbour = index.parent / "pages" / "BATCH21_LOG_0001.md"
    neighbour.write_text("# another archive\n", encoding="utf-8")

    assert store.read(index)


@pytest.mark.parametrize("escape", ["../outside.md", "/etc/passwd", "sub/../../up.md"])
def test_escaping_page_reference_is_rejected(tmp_path, escape):
    store, index, _ = _paginate(tmp_path)
    manifest = _manifest(index)
    manifest["pages"][0]["name"] = escape
    _rewrite_manifest(index, manifest)

    with pytest.raises(SyncError):
        store.read(index)


def test_symlinked_page_is_rejected(tmp_path):
    store, index, _ = _paginate(tmp_path)
    manifest = _manifest(index)
    target = store.page_path(index, manifest["pages"][0])
    outside = tmp_path / "outside.md"
    outside.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.unlink()
    try:
        os.symlink(outside, target)
    except OSError:  # pragma: no cover - platform without symlink privilege
        pytest.skip("symlink creation is unavailable in this environment")

    with pytest.raises(SyncError, match="symlink"):
        store.read(index)


def test_symlinked_page_directory_is_rejected(tmp_path):
    store, index, _ = _paginate(tmp_path)
    pages = index.parent / "pages"
    moved = tmp_path / "elsewhere"
    pages.rename(moved)
    try:
        os.symlink(moved, pages, target_is_directory=True)
    except OSError:  # pragma: no cover - platform without symlink privilege
        pytest.skip("symlink creation is unavailable in this environment")

    with pytest.raises(SyncError, match="symlink"):
        store.read(index)


def test_index_outside_the_archive_root_is_rejected(tmp_path):
    store, _ = _store(tmp_path)

    with pytest.raises(SyncError):
        store.read(tmp_path / "elsewhere.md")


# ---------------------------------------------------------------------------
# Cold storage
# ---------------------------------------------------------------------------

OLD = "2020-01-01"
NEW = "2026-09-01"


def _dated(tmp_path, dates: list[str], max_lines: int = 30):
    store, index = _store(tmp_path, max_lines=max_lines)
    entries = [
        _entry(f"F-{n}", body=4, completed=value) for n, value in enumerate(dates)
    ]
    text = _corpus(entries)
    return store, index, text


def test_plan_without_as_of_never_moves_anything_cold(tmp_path):
    store, index, text = _dated(tmp_path, [OLD] * 20)

    _apply(store.plan(index, text))
    second = store.plan(index, text)

    assert second == {}
    assert not (index.parent / "cold").exists()
    for page in _manifest(index)["pages"]:
        assert page["location"] == "hot"
    assert store.read(index) == normalize(text)


def test_explicit_as_of_moves_eligible_finalized_pages_cold(tmp_path):
    store, index, text = _dated(tmp_path, [OLD] * 20)
    _apply(store.plan(index, text))
    hot_before = {
        page["name"]: store.page_path(index, page).read_bytes()
        for page in _manifest(index)["pages"]
    }

    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))
    pages = _manifest(index)["pages"]

    assert [page["location"] for page in pages[:-1]] == ["cold"] * (len(pages) - 1)
    assert pages[-1]["location"] == "hot"
    for page in pages:
        assert store.page_path(index, page).read_bytes() == hot_before[page["name"]]
    assert store.read(index) == normalize(text)


def test_cold_pages_move_beneath_the_archives_cold_directory(tmp_path):
    store, index, text = _dated(tmp_path, [OLD] * 20)
    _apply(store.plan(index, text))
    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))

    cold = index.parent / "cold"
    assert cold.is_dir()
    assert list(cold.glob("FINDINGS_ARCHIVE_*.md"))
    for page in _manifest(index)["pages"]:
        if page["location"] == "cold":
            assert not (index.parent / "pages" / page["name"]).exists()
            assert f"cold/{page['name']}" in index.read_text(encoding="utf-8")


def test_mixed_age_page_stays_hot(tmp_path):
    store, index, text = _dated(tmp_path, [OLD] * 9 + [NEW] + [OLD] * 10)
    _apply(store.plan(index, text))
    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))

    pages = _manifest(index)["pages"]
    hot = [page for page in pages if page["location"] == "hot"]

    # The tail is always hot; the page holding the recent entry is the second.
    assert len(hot) >= 2
    fourth = pages[3]
    assert fourth["location"] == "hot"
    assert NEW in store.page_path(index, fourth).read_text(encoding="utf-8")
    assert store.read(index) == normalize(text)


def test_undated_entries_keep_their_page_hot(tmp_path):
    store, index = _store(tmp_path, max_lines=30)
    entries = [_entry(f"F-{n}", body=4, completed=OLD) for n in range(19)]
    entries.insert(1, _entry("F-undated", body=4))
    text = _corpus(entries)
    _apply(store.plan(index, text))

    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))
    pages = _manifest(index)["pages"]

    assert any(page["location"] == "hot" for page in pages[:-1])
    assert store.read(index) == normalize(text)


def test_oversized_page_is_never_moved_cold(tmp_path):
    store, index = _store(tmp_path, max_lines=20)
    entries = [_entry("F-BIG", body=60, completed=OLD)]
    entries += [_entry(f"F-{n}", body=4, completed=OLD) for n in range(10)]
    text = _corpus(entries)
    _apply(store.plan(index, text))

    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))
    oversized = [page for page in _manifest(index)["pages"] if page["oversized"]]

    assert oversized and all(page["location"] == "hot" for page in oversized)


def test_cutoff_is_strict(tmp_path):
    store, index, text = _dated(tmp_path, ["2025-09-15"] * 20)
    _apply(store.plan(index, text))

    exactly_at_cutoff = store.plan(index, text, as_of=date(2026, 9, 15))
    assert exactly_at_cutoff == {}

    one_day_later = store.plan(index, text, as_of=date(2026, 9, 16))
    assert one_day_later != {}


def test_cold_days_is_configurable(tmp_path):
    store, index, text = _dated(tmp_path, ["2026-01-01"] * 20)
    _apply(store.plan(index, text))

    assert store.plan(index, text, as_of=date(2026, 9, 15)) == {}
    assert store.plan(index, text, as_of=date(2026, 9, 15), cold_days=30) != {}


def test_cold_migration_is_idempotent_and_preserves_content(tmp_path):
    store, index, text = _dated(tmp_path, [OLD] * 20)
    _apply(store.plan(index, text))
    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))
    flattened = store.read(index)

    assert store.plan(index, text, as_of=date(2026, 9, 15)) == {}
    assert flattened == normalize(text)
    assert store.plan(index, flattened) == {}


def test_cold_and_hot_pages_share_one_reading_authority(tmp_path):
    store, index, text = _dated(tmp_path, [OLD] * 12 + [NEW] * 8)
    _apply(store.plan(index, text))
    hot_only = store.read(index)
    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))

    assert store.read(index) == hot_only == normalize(text)
    assert any(page["location"] == "cold" for page in _manifest(index)["pages"])


def test_appending_after_cold_migration_keeps_cold_pages_in_place(tmp_path):
    store, index, text = _dated(tmp_path, [OLD] * 20)
    _apply(store.plan(index, text))
    _apply(store.plan(index, text, as_of=date(2026, 9, 15)))
    cold_before = {
        page["name"] for page in _manifest(index)["pages"] if page["location"] == "cold"
    }

    grown = normalize(text).rstrip("\n") + "\n\n" + _entry("F-new", body=4) + "\n"
    _apply(store.plan(index, grown))
    cold_after = {
        page["name"] for page in _manifest(index)["pages"] if page["location"] == "cold"
    }

    assert cold_before <= cold_after
    assert store.read(index) == normalize(grown)


# ---------------------------------------------------------------------------
# Task 2 fix round 1: reproduced Important findings
# ---------------------------------------------------------------------------


def test_missing_index_never_schedules_existing_pages_for_delete(tmp_path):
    """A missing index must not make plan() silently delete existing pages.

    Reproduces finding 1: `_load` returns an empty, unpaginated layout for a
    missing index with no orphan check (`_reject_orphans` runs only on the
    monolith-load branch). Planning a small/empty corpus against that empty
    layout takes the single-monolith return path in `plan()`, whose `_diff`
    then schedules every pre-existing managed page -- hot AND cold -- for
    DELETE, because none of them appear in the new single-file `desired` map.
    A hand-deleted or moved index must be reported as an error, never
    silently repaired by discarding every page it used to reference.
    """
    store, index = _store(tmp_path, max_lines=20)
    text = _corpus([_entry(f"F-{n}") for n in range(8)])
    _apply(store.plan(index, text))
    manifest = _manifest(index)
    assert manifest["pages"], "setup must actually paginate"
    existing_pages = [store.page_path(index, page) for page in manifest["pages"]]
    assert all(page.is_file() for page in existing_pages)

    index.unlink()

    with pytest.raises(SyncError):
        store.plan(index, "")

    assert all(page.is_file() for page in existing_pages), (
        "an errored plan() must not have deleted any pre-existing page"
    )


def test_page_content_before_the_first_entry_heading_is_rejected(tmp_path):
    """Extra text before a page's first entry must error, never vanish.

    Reproduces finding 2: `_read_page` used to slice off exactly
    `PAGE_HEADER_LINES` from the front of a page and hand the remainder to
    `_split`, silently discarding any additional owner-authored prologue
    between the header and the first `### ` entry with no diagnostic. The
    next `plan()`/`publish()` cycle would then write the truncated page
    back permanently. That content must now be reported, not lost.
    """
    store, index = _store(tmp_path, max_lines=20)
    text = _corpus([_entry(f"F-{n}") for n in range(8)])
    _apply(store.plan(index, text))
    manifest = _manifest(index)
    first_page = store.page_path(index, manifest["pages"][0])
    original_lines = first_page.read_text(encoding="utf-8").split("\n")
    header = original_lines[:PAGE_HEADER_LINES]
    remainder = original_lines[PAGE_HEADER_LINES:]
    injected = "\n".join(
        [*header, "An owner note that does not belong here.", "", *remainder]
    )
    first_page.write_text(injected, encoding="utf-8")

    with pytest.raises(SyncError, match="discard"):
        store.read(index)


def test_page_without_the_required_header_is_rejected(tmp_path):
    """A page missing its `PAGE_MARKER` header must error, not be truncated.

    Reproduces the header-missing half of finding 2: `_read_page` only
    stripped the header when the first line matched `PAGE_MARKER`; when it
    did not match, the whole file -- including whatever the caller intended
    as a header -- was fed straight to `_split` with no diagnostic.
    """
    store, index = _store(tmp_path, max_lines=20)
    text = _corpus([_entry(f"F-{n}") for n in range(8)])
    _apply(store.plan(index, text))
    manifest = _manifest(index)
    first_page = store.page_path(index, manifest["pages"][0])
    first_page.write_text("# Not a real page header\n\nsome text\n", encoding="utf-8")

    with pytest.raises(SyncError, match="header"):
        store.read(index)


def test_page_path_is_contained_within_its_own_index_directory(tmp_path):
    """Pages for a nested index must live beside that index, not at the root.

    Reproduces finding 3: `page_path` always resolves under `self.root`,
    ignoring `index_path` entirely. Two archives that share one
    `ArchiveStore.root` but live in different subdirectories (the real
    topology: `docs/history/findings/` vs `docs/logarchive/`) would collide
    on `pages/<stem>_NNNN.md`, and pages for a nested index would be written
    to the wrong directory with links that do not resolve from the index.
    """
    root = tmp_path / "shared-root"
    root.mkdir()
    store = ArchiveStore(root, max_lines=20)
    nested_index = root / "sub" / "ARCHIVE.md"
    nested_index.parent.mkdir(parents=True)
    text = _corpus([_entry(f"F-{n}") for n in range(8)])

    updates = store.plan(nested_index, text)
    _apply(updates)

    page_paths = [path for path in updates if path != nested_index and path.exists()]
    assert page_paths, "expected at least one page to be written"
    for page_path in page_paths:
        assert page_path.is_relative_to(nested_index.parent), (
            f"{page_path} is not contained within {nested_index.parent}"
        )
    rendered_index = nested_index.read_text(encoding="utf-8")
    for page_path in page_paths:
        relative = page_path.relative_to(nested_index.parent).as_posix()
        assert relative in rendered_index
    assert store.read(nested_index) == normalize(text)
