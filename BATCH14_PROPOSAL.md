# BATCH14_PROPOSAL.md

## Batch 14 — Doc Hygiene

**Status:** Proposed (awaiting audit)
**Branch:** `wip/batch-14-doc-hygiene` (from `main` after Batch 13 PR merges)
**Baseline:** 288 tests passing (post-Batch 13 + PR-review patches)
**Owner sign-off required before execution.**

---

## Goal

Close the four doc-hygiene items explicitly queued in PLAYBOOK Section 3 that
accumulated during Batch 13 delivery:

1. `BATCH13_PROPOSAL.md` remains in the repo root; Batch 11 has no definition file;
   `BATCH12_PROPOSAL.md` breaks the `_DEFINITION.md` archive convention.
2. `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` is a 1279-line monolith mixing
   log entries from Batches 10–13 with no per-batch separation.
3. `doc_state_sync.py` routes all rotated entries to the monolith; it needs (a) per-batch
   routing, (b) a one-time archive migration flag, and (c) a root `BATCH*.md` warning.
4. `AGENTS.md` has no formal batch close-out procedure; the post-Batch-14 architecture
   change (per-batch log files) must also be documented there.

No new application features are included. Batch 15 (first new feature — top songs or
heatmap) is explicitly deferred until this batch merges.

---

## Prerequisites

- `wip/pc-snapshot` PR merged to `main` (CI passing, 288 tests green).
- `wip/batch-14-doc-hygiene` branched from `main`.
- Pre-work checklist passes before first WP commit:
  ```
  venv/Scripts/python.exe -m pytest -q                    # 288 passed
  venv/Scripts/python.exe -m pre_commit run --all-files   # all 8 hooks pass
  git branch --show-current                               # wip/batch-14-doc-hygiene
  ```

---

## Current state

| Item | Location | State |
|------|----------|-------|
| Batch 11 definition file | `docs/history/` | **Missing** — inline in PLAYBOOK Section 3 only |
| Batch 12 definition file | `docs/history/BATCH12_PROPOSAL.md` | **Wrong suffix** — should be `BATCH12_DEFINITION.md` |
| Batch 13 definition file | `BATCH13_PROPOSAL.md` (root) | **Not archived; wrong suffix** — should be `BATCH13_DEFINITION.md` |
| Execution log archive | `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` | 1279-line monolith (Batches 10–13 interleaved) |
| Per-batch log files | `docs/history/BATCHN_LOG.md` | **None exist** |
| `doc_state_sync.py` | `scripts/doc_state_sync.py` | ~450-line monolith; all entries → monolith; no batch-aware routing |
| `test_doc_state_sync.py` | `tests/test_doc_state_sync.py` | 1149 lines, 84 tests, 18 classes — monolith |
| AGENTS.md close-out rules | `AGENTS.md` | Implicit only; no numbered checklist |

**Archive naming convention:** BATCH0–BATCH10 all use `_DEFINITION.md`. BATCH12 uses
`_PROPOSAL.md` (anomaly). The standard is `_DEFINITION.md` for any completed batch.

Existing definition files for reference: `BATCH0–9_DEFINITION.md`,
`BATCH10_DEFINITION_2026-02-21.md` — all in `docs/history/`.

---

## Work packages

---

### WP-1 — Manual batch-definition archival

**Goal:** Create Batch 11 definition file; archive and correctly rename Batch 12 and 13
files; update PLAYBOOK cross-references. No script changes.

**Deliverables:**

1. **`docs/history/BATCH11_DEFINITION.md`** (new file)
   Synthesised from PLAYBOOK Section 3 inline description and archive entries.
   Minimum content:
   - Batch goal (theme CSS/JS consolidation; orchestrator helper decomposition)
   - WP list: WP-1 theme CSS/JS, WP-2 `process_albums` decomposition, WP-3 CSS/JS DRY
   - Net test delta (from archive evidence)
   - Date range
   - Link to relevant `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` entries

2. **`docs/history/BATCH12_PROPOSAL.md` → `docs/history/BATCH12_DEFINITION.md`** (git mv)
   Retroactive fix to enforce the `_DEFINITION.md` convention. No content changes.

3. **`BATCH13_PROPOSAL.md` → `docs/history/BATCH13_DEFINITION.md`** (git mv from root)
   Enforces the `_DEFINITION.md` convention. No content changes.

4. **PLAYBOOK Section 2 table** — update rows for Batch 11, 12, and 13 to link the
   standardised `_DEFINITION.md` filenames in `docs/history/`.

5. **PLAYBOOK Section 3** — update the `BATCH13_PROPOSAL.md` reference to
   `docs/history/BATCH13_DEFINITION.md`.

**Acceptance criteria:**
- `docs/history/BATCH11_DEFINITION.md` exists and is readable.
- `BATCH12_PROPOSAL.md` no longer exists in `docs/history/`; `BATCH12_DEFINITION.md` does.
- `BATCH13_PROPOSAL.md` no longer in root; `docs/history/BATCH13_DEFINITION.md` exists.
- PLAYBOOK Section 2 links all three files and the paths resolve on disk.
- `doc_state_sync.py --check` passes.

**Net tests:** +0
**Commit:** `docs(history): archive and rename Batch 11–13 definition files (WP-1)`

---

### WP-2 — `doc_state_sync.py`: structural package extraction

**Goal:** Extract the ~450-line `scripts/doc_state_sync.py` monolith into a proper
Python package (`scripts/docsync/`) with modules scoped by responsibility, and split
the 1149-line test monolith into files that map 1:1 to the new modules. This is a
**pure structural refactor** — zero feature changes, zero logic changes.

This WP must complete before WP-3 adds new features so that the architectural symmetry
(one test file per source module) is established first.

#### Package layout after WP-2

```
scripts/
  doc_state_sync.py          # thin wrapper: from docsync.cli import main; main()
  docsync/
    __init__.py              # empty or minimal
    models.py                # Entry, ActiveBatchState, SyncResult dataclasses
    parser.py                # regex constants; _find_section, _find_marker_pair,
                             #   _parse_entries, _parse_active_batch_state,
                             #   _extract_entry_batch, _collect_wp_numbers
    renderer.py              # _render_section4, _render_archive, _build_status_block,
                             #   _trim_trailing_blank, _remove_marker_lines
    logic.py                 # _sync, _cross_validate, _fingerprint (dedup logic)
    cli.py                   # main(), argparse, _read_lines, _write_lines
```

#### Test split mapping (84 existing tests → 5 files, total unchanged)

| New test file | Source classes | Approx tests |
|---------------|---------------|-------------|
| `tests/test_docsync_models.py` | TestSyncResult (field names/defaults) | ~5 |
| `tests/test_docsync_parser.py` | TestReadLines, TestFindSection, TestFindMarkerPair, TestParseEntries, TestParseActiveBatchState, TestRegexPatterns | ~20 |
| `tests/test_docsync_renderer.py` | TestBuildStatusBlock, TestRenderSection4, TestRenderArchive, TestTrimTrailingBlank, TestRemoveMarkerLines | ~19 |
| `tests/test_docsync_logic.py` | TestExtractEntryBatch, TestCollectWpNumbers, TestFingerprintNormalization, TestCrossValidate, TestSyncIntegration | ~30 |
| `tests/test_docsync_cli.py` | TestMainArgs, TestMissingSessionContext | ~10 |

`tests/test_doc_state_sync.py` — **deleted**.

**`sync_env` fixture:** Move from `test_doc_state_sync.py` to `tests/conftest.py`
(already exists; pytest auto-discovers it for all tests). Used by logic, cli, and
(in WP-4) new archival tests.

**Entrypoint stability:** The thin wrapper at `scripts/doc_state_sync.py` preserves
the existing entrypoint path. The pre-commit `doc-state-sync-check` hook, PLAYBOOK
run commands, and CI pipeline continue to work without change.

**Acceptance criteria:**
- `pytest tests/test_docsync_*.py -v` shows exactly 84 tests across 5 files.
- `tests/test_doc_state_sync.py` does not exist.
- `python scripts/doc_state_sync.py --check` passes (entrypoint wrapper works).
- `sync_env` in `tests/conftest.py`.
- All 8 pre-commit hooks pass.

**Net tests:** +0 (reorganisation only)
**Commit:** `refactor(doc-sync): extract docsync package and split test monolith (WP-2)`

---

### WP-3 — `docsync`: per-batch log routing + archive migration

**Goal:** Implement the per-batch routing, `--split-archive` migration, and
root-`BATCH*.md` warning within the new `docsync/` package, with I/O strictly in
`cli.py` and pure logic strictly in `logic.py`.

#### Architecture after WP-3

| Entry tag | Destination |
|-----------|------------|
| `(Batch N WP-X)` | `docs/history/BATCHN_LOG.md` |
| `(Batch N ...)` (any other batch tag) | `docs/history/BATCHN_LOG.md` |
| `(side-task)` or untagged | `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (unchanged) |

Per-batch log files use the same entry format as the monolith (reverse-chronological,
`### YYYY-MM-DD` heading, Scope/Problem/Fix/Validation fields). Deduplication by
SHA-256 fingerprint applies to per-batch files the same way it applies to the monolith.

#### Changes by module

**`docsync/models.py`:**
- Add `batch_log_updates: dict[int, list[str]]` field to `SyncResult`

**`docsync/logic.py` (pure Python, no Path.write_text):**
- `_merge_entries_into_log(existing_lines, new_entries) -> list[str]` — prepend new
  entries at top (after header), deduplicate by fingerprint; create minimal header if
  content is empty
- Modify `_sync(keep_non_current)` — call `_extract_entry_batch(e)` per entry; route
  tagged → `batch_log_updates[N]` via `_merge_entries_into_log`; route untagged →
  existing monolith merge; return updated `SyncResult`
- `_split_archive(monolith_lines) -> tuple[list[str], dict[int, list[str]]]` — parse
  all entries, group by `_extract_entry_batch()`; return (remaining_untagged_lines,
  batch_groups) without any file I/O

**`docsync/cli.py` (I/O and orchestration):**
- `HISTORY_DIR = Path("docs/history")`
- `_get_batch_log_path(batch_num: int) -> Path` — `HISTORY_DIR / f"BATCH{batch_num}_LOG.md"`
- `_check_root_batch_files(root: Path) -> list[str]` — scan `root` for `BATCH*.md`,
  return warning strings for each found
- Modify `_cross_validate(...)` — call `_check_root_batch_files(Path("."))` and append
  warnings
- `--fix` mode — write each `result.batch_log_updates[N]` to `_get_batch_log_path(N)`
  via `_write_lines`; report paths in summary
- `--check` mode — compare computed `batch_log_updates` vs on-disk content; report drift
- `--split-archive` flag (mutually exclusive with `--check`/`--fix`) — call
  `logic._split_archive(monolith_lines)`, write per-batch files via `_write_lines`,
  rewrite monolith with untagged-only lines, print summary

#### WP-3 execution steps (run after implementation is committed)

```
venv/Scripts/python.exe scripts/doc_state_sync.py --split-archive
venv/Scripts/python.exe scripts/doc_state_sync.py --check   # must show zero drift
venv/Scripts/python.exe -m pytest -q                        # 288 passed
```

Then commit the resulting archive changes:
`chore(history): split execution log monolith into per-batch log files`

**Acceptance criteria:**
- `docs/history/BATCHN_LOG.md` created for each batch represented in the monolith.
- Monolith retains only untagged/side-task entries.
- Future `--fix` run: an entry tagged `(Batch 15 WP-1)` is written to `BATCH15_LOG.md`,
  not to the monolith.
- `--check` reports zero drift after `--fix`.
- Root `BATCH*.md` warning fires when a `BATCH*.md` is present in root.

**Net tests:** +0 (tests in WP-4)
**Commits:**
1. `feat(doc-sync): per-batch log routing and --split-archive migration (WP-3)`
2. `chore(history): split execution log monolith into per-batch log files`

---

### WP-4 — New tests for WP-3 enhancements

**Goal:** Full test coverage for all new functions introduced in WP-3, distributed into
the module test files established in WP-2 (not an orphan feature-based file).

Tests must be added to `test_docsync_logic.py` (pure-logic functions) and
`test_docsync_cli.py` (I/O, path resolution, end-to-end). Uses `sync_env` fixture from
`tests/conftest.py` (established in WP-2).

#### Distribution

**`tests/test_docsync_logic.py`** (+8 tests):

| Test | Function under test | What it asserts |
|------|--------------------|----|
| `test_tagged_entry_routed_to_batch_log` | `_sync` integration | Entry tagged `(Batch 13 WP-1)` lands in `batch_log_updates[13]`, not monolith |
| `test_untagged_entry_stays_in_monolith` | `_sync` integration | `(side-task)` entry lands in monolith, not any batch log |
| `test_two_batches_in_one_sync` | `_sync` integration | Entries for Batch 12 and 13 routed to separate batch log groups |
| `test_batch_log_created_on_first_entry` | `_merge_entries_into_log` | Empty existing lines → header + entry created |
| `test_batch_log_deduplicates_entries` | `_merge_entries_into_log` | Same fingerprint entry not added twice |
| `test_split_archive_routes_by_batch` | `_split_archive` | Batch 13 entries appear in `batch_groups[13]` |
| `test_split_archive_retains_untagged_in_monolith` | `_split_archive` | Untagged entries remain in returned monolith lines |
| `test_split_archive_deduplicates_on_merge` | `_split_archive` | Duplicate fingerprints deduplicated in output |

**`tests/test_docsync_cli.py`** (+4 tests):

| Test | Function under test | What it asserts |
|------|--------------------|----|
| `test_get_batch_log_path_returns_correct_path` | `_get_batch_log_path` | Returns `Path("docs/history/BATCH13_LOG.md")` for batch 13 |
| `test_check_root_batch_files_warns` | `_check_root_batch_files` | `BATCH14_PROPOSAL.md` in root → warning string returned |
| `test_check_root_batch_files_no_warn_when_clean` | `_check_root_batch_files` | Empty root → empty list |
| `test_fix_then_check_clean_with_batch_logs` (adversarial) | `main()` end-to-end | `--fix` then `--check` reports zero drift when per-batch logs exist |

**Acceptance criteria:**
- `pytest tests/test_docsync_logic.py tests/test_docsync_cli.py -v` shows +12 new tests
  passing (alongside existing tests in those files).
- `pytest -q` shows **300 passed** (288 + 12).
- No `test_doc_state_sync_archival.py` file exists.
- All 8 pre-commit hooks pass.

**Net tests:** +12
**Commit:** `test(doc-sync): add 12 tests for per-batch routing and split-archive (WP-4)`

---

### WP-5 — `AGENTS.md`: updated doc-sync description + explicit close-out procedure

**Goal:** Make AGENTS.md correct and complete for future agents after the archive
architecture change.

#### 5a — Update "What `doc_state_sync.py` does"

1. **Routing description:** Replace "Rotates overflow dated entries into
   `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`" with:
   - Tagged `(Batch N ...)` entries → `docs/history/BATCHN_LOG.md`
   - Untagged / `(side-task)` entries → `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

2. **Package structure note:** The script is a thin wrapper over `scripts/docsync/`
   (models / parser / renderer / logic / cli); extend any functionality through the
   appropriate module.

3. **Add `--split-archive` note:** One-time migration command run at Batch 14 close;
   not needed for subsequent batches.

4. **Root-BATCH warning:** "Root `BATCH*.md` file detected — warns when an unarchived
   batch definition file is found in the repo root."

#### 5b — Add explicit close-out checklist

```
### Batch close-out procedure

After all WP commits for a batch are done and verified:

1. Run `python scripts/doc_state_sync.py --fix --keep-non-current 0`.
   Tagged entries route to BATCHN_LOG.md; side-task entries route to monolith.
   SESSION_CONTEXT.md Section 3 STATUS block is auto-updated by this step.
2. Move `BATCHN_PROPOSAL.md` (root) to `docs/history/BATCHN_DEFINITION.md`
   via `git mv` (if tracked) or copy-then-delete (if untracked).
3. Update PLAYBOOK Section 2 table: add/update row linking `docs/history/BATCHN_DEFINITION.md`.
4. Update PLAYBOOK Section 3: mark batch complete, update "next action."
5. Run `python scripts/doc_state_sync.py --check` — must report zero drift.
6. Commit: `docs(playbook): close Batch N` (no WP suffix).
7. Verify that AGENTS.md, SESSION_CONTEXT.md, and PLAYBOOK.md are mutually consistent.
   These three files are the canonical state for all future agents.
```

**Acceptance criteria:**
- AGENTS.md routing description matches post-WP-3 behaviour.
- Close-out checklist is present and numbered.
- Checklist references SESSION_CONTEXT.md (auto-updated by `--fix`) and PLAYBOOK.md
  as the two canonical state files; no external files required.

**Net tests:** +0
**Commit:** `docs(agents): update doc-sync architecture and add close-out procedure (WP-5)`

---

## Batch summary

| WP | Deliverable | Net tests |
|----|------------|-----------|
| WP-1 | BATCH11/12/13 archived as `_DEFINITION.md` + PLAYBOOK links | +0 |
| WP-2 | `doc_state_sync.py` → `scripts/docsync/` package + 5 test files | +0 |
| WP-3 | Per-batch log routing + `--split-archive` in `docsync/` modules | +0 |
| WP-4 | 12 new tests distributed into `test_docsync_logic.py` / `test_docsync_cli.py` | +12 |
| WP-5 | AGENTS.md updated + close-out procedure | +0 |

**Total tests after Batch 14:** 288 + 12 = **300 passing**

---

## Key files

| File | Action | WP |
|------|--------|-----|
| `BATCH13_PROPOSAL.md` (root) | `git mv` → `docs/history/BATCH13_DEFINITION.md` | WP-1 |
| `docs/history/BATCH12_PROPOSAL.md` | `git mv` → `docs/history/BATCH12_DEFINITION.md` | WP-1 |
| `docs/history/BATCH11_DEFINITION.md` | New | WP-1 |
| `PLAYBOOK.md` | Section 2 table + Section 3 reference updates | WP-1 |
| `scripts/doc_state_sync.py` | Thin wrapper (`from docsync.cli import main; main()`) | WP-2 |
| `scripts/docsync/__init__.py` | New (empty) | WP-2 |
| `scripts/docsync/models.py` | New — Entry, ActiveBatchState, SyncResult | WP-2 |
| `scripts/docsync/parser.py` | New — regex, parsing functions | WP-2 |
| `scripts/docsync/renderer.py` | New — markdown formatting functions | WP-2 |
| `scripts/docsync/logic.py` | New — _sync, _cross_validate, dedup | WP-2 |
| `scripts/docsync/cli.py` | New — main(), argparse, file I/O | WP-2 |
| `tests/test_doc_state_sync.py` | Deleted | WP-2 |
| `tests/test_docsync_models.py` | New split file | WP-2 |
| `tests/test_docsync_parser.py` | New split file | WP-2 |
| `tests/test_docsync_renderer.py` | New split file | WP-2 |
| `tests/test_docsync_logic.py` | New split file | WP-2 |
| `tests/test_docsync_cli.py` | New split file | WP-2 |
| `tests/conftest.py` | `sync_env` fixture added | WP-2 |
| `scripts/docsync/models.py` | `batch_log_updates` field added to SyncResult | WP-3 |
| `scripts/docsync/logic.py` | `_merge_entries_into_log`, `_split_archive`, `_sync` routing | WP-3 |
| `scripts/docsync/cli.py` | `_get_batch_log_path`, `_check_root_batch_files`, `--split-archive`, `_cross_validate` warning | WP-3 |
| `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` | Slimmed (untagged entries only after split) | WP-3 execution |
| `docs/history/BATCH10_LOG.md` … `BATCH13_LOG.md` | New (created by `--split-archive`) | WP-3 execution |
| `tests/test_docsync_logic.py` | +8 new tests for WP-3 logic | WP-4 |
| `tests/test_docsync_cli.py` | +4 new tests for WP-3 I/O | WP-4 |
| `AGENTS.md` | Updated doc-sync description + close-out procedure | WP-5 |

---

## Verification

After each WP:
```
venv/Scripts/python.exe -m pytest -q                      # must show 288+ passed
venv/Scripts/python.exe -m pre_commit run --all-files     # all 8 hooks pass
```

After WP-2:
```
venv/Scripts/python.exe -m pytest tests/test_docsync_*.py -v   # 84 passed, 5 files
venv/Scripts/python.exe scripts/doc_state_sync.py --check      # entrypoint works
```

After WP-3 migration run:
```
venv/Scripts/python.exe scripts/doc_state_sync.py --split-archive
venv/Scripts/python.exe scripts/doc_state_sync.py --check   # zero drift
```

After WP-4:
```
venv/Scripts/python.exe -m pytest tests/test_docsync_logic.py tests/test_docsync_cli.py -v
venv/Scripts/python.exe -m pytest -q                        # 300 passed
```

Final batch close-out (per AGENTS.md WP-5 checklist):
```
venv/Scripts/python.exe scripts/doc_state_sync.py --fix --keep-non-current 0
venv/Scripts/python.exe scripts/doc_state_sync.py --check
```

---

## Deferred

- **Batch 15 — new feature** (top songs or heatmap): scope to be defined by owner;
  assigned a batch number before work begins.
- **Orchestrator modularisation**: still premature; revisit when a new feature (Batch 15)
  adds a second pipeline and `orchestrator.py` needs the room.
