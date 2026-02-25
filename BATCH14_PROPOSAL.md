# BATCH14_PROPOSAL.md

## Batch 14 — Doc Hygiene

**Status:** Proposed (awaiting audit)
**Branch:** `wip/batch-14-doc-hygiene` (from `main` after Batch 13 PR merges)
**Baseline:** 288 tests passing (post-Batch 13 + PR-review patches)
**Owner sign-off required before execution.**

---

## Goal

Close the four doc-hygiene items explicitly queued in PLAYBOOK Section 3 (lines 71–89)
that accumulated during Batch 13 delivery:

1. `BATCH13_PROPOSAL.md` remains in the repo root; Batch 11 has no definition file.
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
| Batch 13 definition file | `BATCH13_PROPOSAL.md` (root) | **Not archived** |
| Execution log archive | `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` | 1279-line monolith (Batches 10–13 interleaved) |
| Per-batch log files | `docs/history/BATCHN_LOG.md` | **None exist** |
| `doc_state_sync.py` routing | `scripts/doc_state_sync.py` | All entries → monolith; no batch-aware routing |
| `test_doc_state_sync.py` | `tests/test_doc_state_sync.py` | 1149 lines, 84 tests, 18 classes — monolith |
| AGENTS.md close-out rules | `AGENTS.md` | Implicit only; no numbered checklist |
| AGENTS.md doc-sync description | `AGENTS.md` lines 126–127 | Describes monolith only; stale after WP-2 |

Existing definition files for reference: `BATCH0–9_DEFINITION.md`,
`BATCH10_DEFINITION_2026-02-21.md`, `BATCH12_PROPOSAL.md` — all in `docs/history/`.

---

## Work packages

---

### WP-1 — Manual batch-definition archival

**Goal:** Create Batch 11 definition file; move Batch 13 proposal to `docs/history/`;
update PLAYBOOK cross-references. No script changes.

**Deliverables:**

1. **`docs/history/BATCH11_DEFINITION.md`** (new file)
   Synthesised from PLAYBOOK Section 3 inline description and archive entries.
   Minimum content:
   - Batch goal (theme CSS/JS consolidation; orchestrator helper decomposition)
   - WP list: WP-1 theme CSS/JS, WP-2 `process_albums` decomposition, WP-3 CSS/JS DRY
   - Net test delta (from archive evidence)
   - Date range
   - Link to relevant `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` entries

2. **`BATCH13_PROPOSAL.md` → `docs/history/BATCH13_PROPOSAL.md`** (git mv from root)
   Filename kept as `_PROPOSAL` to match `BATCH12_PROPOSAL.md` precedent.
   No content changes.

3. **PLAYBOOK Section 2 table** — add/update rows for Batch 11 and Batch 13 with
   `docs/history/` relative links.

4. **PLAYBOOK Section 3** — update the `BATCH13_PROPOSAL.md` reference to
   `docs/history/BATCH13_PROPOSAL.md`.

**Acceptance criteria:**
- `docs/history/BATCH11_DEFINITION.md` exists and is readable.
- `BATCH13_PROPOSAL.md` no longer in root (`git status` shows it gone).
- `docs/history/BATCH13_PROPOSAL.md` exists.
- PLAYBOOK Section 2 table links both files and the paths resolve on disk.
- `doc_state_sync.py --check` passes (cross-validate: "Broken archive link" check
  currently validates Section 2 links).

**Net tests:** +0
**Commit:** `docs(history): archive Batch 11 and 13 definition files (WP-1)`

---

### WP-2 — `doc_state_sync.py`: per-batch log routing + archive migration

**Goal:** Change ongoing rotation behaviour so entries tagged `(Batch N ...)` route to
`docs/history/BATCHN_LOG.md` instead of the monolith. Add `--split-archive` one-time
migration flag to split the existing 1279-line monolith by batch. Add a root-`BATCH*.md`
warning to `_cross_validate`.

#### Architecture after WP-2

| Entry tag | Destination |
|-----------|------------|
| `(Batch N WP-X)` | `docs/history/BATCHN_LOG.md` |
| `(Batch N ...)` (any other batch tag) | `docs/history/BATCHN_LOG.md` |
| `(side-task)` or untagged | `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (unchanged) |

Per-batch log files use the same entry format as the monolith (reverse-chronological,
same `### YYYY-MM-DD` heading, same Scope/Problem/Fix/Validation fields). Deduplication
by SHA-256 fingerprint applies to per-batch files the same way it applies to the monolith.

#### New / modified functions

| Symbol | Action | Description |
|--------|--------|-------------|
| `HISTORY_DIR` | New constant | `Path("docs/history")` |
| `_get_batch_log_path(batch_num: int) -> Path` | New | Returns `HISTORY_DIR / f"BATCH{batch_num}_LOG.md"` |
| `_merge_entries_into_log(existing_lines, new_entries) -> list[str]` | New | Reads existing per-batch log lines, prepends new entries at top (after header), deduplicates by fingerprint; creates minimal header if file is new |
| `SyncResult` | Modify | Add `batch_log_updates: dict[int, list[str]]` — maps batch number to computed per-batch log lines |
| `_sync(keep_non_current)` | Modify | After grouping rotated entries, call `_extract_entry_batch(e)` for each; route tagged → `batch_log_updates[N]` via `_merge_entries_into_log`; route untagged → existing monolith merge |
| `_check_root_batch_files(root: Path) -> list[str]` | New | Scans `root` for `BATCH*.md`; returns warning strings for each found (e.g. `"BATCH14_PROPOSAL.md found in root — archive to docs/history/ at batch close"`) |
| `_cross_validate(playbook_lines, session_lines)` | Modify | Call `_check_root_batch_files(Path("."))` and append warnings to result |
| `main()` — `--fix` mode | Modify | Write each `result.batch_log_updates[N]` to `_get_batch_log_path(N)` via `_write_lines`; report written paths in summary |
| `main()` — `--check` mode | Modify | For each batch in `result.batch_log_updates`, compare computed vs. on-disk content; report drift if different |
| `_split_archive(archive_path, get_batch_log_fn)` | New | One-time migration: parse all entries in monolith, group by `_extract_entry_batch()`, write each group to `_get_batch_log_fn(N)` (merge+dedup if file exists), rewrite monolith with only untagged entries remaining |
| `main()` — `--split-archive` flag | New | Calls `_split_archive(ARCHIVE_PATH, _get_batch_log_path)`; prints summary; mutually exclusive with `--check`/`--fix` |

#### WP-2 execution steps (after implementation is committed)

As part of this WP, run the migration against the live archive:
```
venv/Scripts/python.exe scripts/doc_state_sync.py --split-archive
venv/Scripts/python.exe scripts/doc_state_sync.py --check   # must show zero drift
venv/Scripts/python.exe -m pytest -q                        # 288 passed
```

Then commit the resulting archive changes (per-batch files created, monolith slimmed):
`chore(history): split execution log monolith into per-batch log files`

**Acceptance criteria:**
- `docs/history/BATCHN_LOG.md` created for each batch represented in the monolith.
- Monolith retains only untagged/side-task entries.
- Future `--fix` run: an entry tagged `(Batch 15 WP-1)` is written to `BATCH15_LOG.md`,
  not to the monolith.
- `--check` reports zero drift after `--fix`.
- Root `BATCH*.md` warning fires when a `BATCH*.md` is present in root; absent when clean.

**Net tests:** +0 (tests written in WP-4)
**Commits:**
1. `feat(doc-sync): per-batch log routing and --split-archive migration (WP-2)`
2. `chore(history): split execution log monolith into per-batch log files`

---

### WP-3 — Split `test_doc_state_sync.py` into focused files

**Goal:** Decompose the 1149-line, 84-test monolith into focused files. Pure
reorganisation — zero logic changes, zero new tests.

#### Split mapping

| New file | Classes | Tests |
|----------|---------|-------|
| `tests/test_doc_state_sync_parsers.py` | TestReadLines, TestFindSection, TestFindMarkerPair, TestParseEntries, TestParseActiveBatchState | 16 |
| `tests/test_doc_state_sync_metadata.py` | TestExtractEntryBatch, TestCollectWpNumbers, TestTrimTrailingBlank, TestRemoveMarkerLines, TestFingerprintNormalization, TestBuildStatusBlock | 17 |
| `tests/test_doc_state_sync_validation.py` | TestCrossValidate, TestRenderSection4, TestRenderArchive, TestRegexPatterns | 24 |
| `tests/test_doc_state_sync_sync.py` | TestSyncIntegration | 14 |
| `tests/test_doc_state_sync_cli.py` | TestMainArgs, TestMissingSessionContext | 10 |

`tests/test_doc_state_sync.py` — **deleted**.

**`sync_env` fixture:** Currently a module-level fixture in `test_doc_state_sync.py`.
Used by `TestSyncIntegration`, `TestMainArgs`, and `TestMissingSessionContext` — and
will be used by the new `test_doc_state_sync_archival.py` in WP-4. Move to
`tests/conftest.py` (already exists; pytest auto-discovers it for all tests in the
directory). No new conftest file needed.

**Acceptance criteria:**
- `pytest tests/test_doc_state_sync_*.py -v` passes with exactly 84 tests across
  5 files.
- `tests/test_doc_state_sync.py` does not exist.
- `sync_env` in `tests/conftest.py` and importable by all 5 split files.

**Net tests:** +0 (reorganisation only)
**Commit:** `refactor(tests): split test_doc_state_sync.py into five focused files (WP-3)`

---

### WP-4 — New tests for WP-2 enhancements

**Goal:** Full test coverage for all new functions introduced in WP-2.

**New file: `tests/test_doc_state_sync_archival.py`** (~150 lines, 12 tests)

Uses `sync_env` fixture from `tests/conftest.py` (established in WP-3).

| Test | Function under test | What it asserts |
|------|--------------------|----|
| `test_get_batch_log_path_returns_correct_path` | `_get_batch_log_path` | Returns `Path("docs/history/BATCH13_LOG.md")` for batch 13 |
| `test_tagged_entry_routed_to_batch_log` | `_sync` integration | Entry tagged `(Batch 13 WP-1)` lands in `BATCH13_LOG.md`, not monolith |
| `test_untagged_entry_stays_in_monolith` | `_sync` integration | `(side-task)` entry lands in monolith, not any batch log |
| `test_two_batches_in_one_sync` | `_sync` integration | Entries for Batch 12 and 13 routed to separate files |
| `test_batch_log_created_on_first_entry` | `_merge_entries_into_log` | File doesn't exist before sync → created with header + entry |
| `test_batch_log_deduplicates_entries` | `_merge_entries_into_log` | Same fingerprint entry not written twice to batch log |
| `test_check_root_batch_files_warns` | `_check_root_batch_files` | `BATCH14_PROPOSAL.md` in root → warning string returned |
| `test_check_root_batch_files_no_warn_when_clean` | `_check_root_batch_files` | Empty root → empty list |
| `test_split_archive_routes_by_batch` | `_split_archive` | Batch 13 entries → `BATCH13_LOG.md` after split |
| `test_split_archive_retains_untagged_in_monolith` | `_split_archive` | Untagged entries remain in monolith after split |
| `test_split_archive_deduplicates_on_merge` | `_split_archive` | Pre-existing `BATCH13_LOG.md` content not duplicated |
| `test_fix_then_check_clean_with_batch_logs` (adversarial) | `main()` end-to-end | `--fix` followed by `--check` reports zero drift when per-batch logs exist |

**Acceptance criteria:**
- `pytest tests/test_doc_state_sync_archival.py -v` shows 12 passed.
- `pytest -q` shows **300 passed** (288 + 12).
- All 8 pre-commit hooks pass.

**Net tests:** +12
**Commit:** `test(doc-sync): add 12 tests for per-batch log routing and split-archive (WP-4)`

---

### WP-5 — `AGENTS.md`: updated doc-sync description + explicit close-out procedure

**Goal:** Make AGENTS.md correct and complete for future agents after the archive
architecture change. Two areas of change: (a) update the existing "What
`doc_state_sync.py` does" section; (b) add a new formal close-out checklist. Also
defines the closing-agent responsibility for MEMORY.md.

#### 5a — Update "What `doc_state_sync.py` does" (AGENTS.md lines 122–170)

1. **Routing description (item 1):** Replace "Rotates overflow dated entries into
   `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`" with:
   - Tagged `(Batch N ...)` entries → `docs/history/BATCHN_LOG.md`
   - Untagged / `(side-task)` entries → `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

2. **Add `--split-archive` note:** one-time migration command (run at Batch 14 close;
   not needed for subsequent batches as ongoing routing handles new entries).

3. **Cross-validate description (line ~169):** Extend "Broken archive link" bullet to
   note that `BATCHN_LOG.md` links in PLAYBOOK are also validated.

4. **Root-BATCH warning:** Add bullet: "Root `BATCH*.md` file detected — warns when
   an unarchived batch definition file is found in the repo root."

#### 5b — Add explicit close-out checklist (new subsection in AGENTS.md)

```
### Batch close-out procedure

After all WP commits for a batch are done and verified:

1. Run `python scripts/doc_state_sync.py --fix --keep-non-current 0`.
   Tagged entries route to BATCHN_LOG.md; side-task entries route to monolith.
2. Move `BATCHN_PROPOSAL.md` (root) to `docs/history/` via `git mv` (if tracked)
   or copy-then-delete (if untracked).
3. Update PLAYBOOK Section 2 table: add/update row with link to the docs/history/ file.
4. Update PLAYBOOK Section 3: mark batch complete, update "next action."
5. Run `python scripts/doc_state_sync.py --check` — must report zero drift.
6. Commit: `docs(playbook): close Batch N` (no WP suffix).
7. Update MEMORY.md: new test count, completed batch, next batch plan, any
   architecture changes. This is the outgoing agent's final task.
```

#### 5c — Closing-agent MEMORY.md update (batch close task, not a code change)

After WP-5 is committed, the closing agent must update `MEMORY.md` to reflect:
- Test count: 300 passing
- Batch 14 complete; Batch 15 (new feature) next
- Post-Batch-14 archive architecture: per-batch `BATCHN_LOG.md` in `docs/history/`;
  monolith retained for side-task/untagged entries only
- `--split-archive` already run; not needed again

**Acceptance criteria:**
- AGENTS.md routing description matches post-WP-2 behaviour.
- Close-out checklist is present and numbered.
- MEMORY.md updated by closing agent at batch end.

**Net tests:** +0
**Commit:** `docs(agents): update doc-sync architecture description and add close-out procedure (WP-5)`

---

## Batch summary

| WP | Deliverable | Net tests |
|----|------------|-----------|
| WP-1 | BATCH11_DEFINITION.md + BATCH13 archived + PLAYBOOK links | +0 |
| WP-2 | `doc_state_sync.py` per-batch routing + `--split-archive` + root warning | +0 |
| WP-3 | `test_doc_state_sync.py` → 5 focused files | +0 |
| WP-4 | 12 new tests for WP-2 in `test_doc_state_sync_archival.py` | +12 |
| WP-5 | AGENTS.md updated + close-out procedure | +0 |

**Total tests after Batch 14:** 288 + 12 = **300 passing**

---

## Key files

| File | Action | WP |
|------|--------|-----|
| `BATCH13_PROPOSAL.md` (root) | `git mv` → `docs/history/BATCH13_PROPOSAL.md` | WP-1 |
| `docs/history/BATCH11_DEFINITION.md` | New | WP-1 |
| `PLAYBOOK.md` | Section 2 table + Section 3 reference updates | WP-1 |
| `scripts/doc_state_sync.py` | New functions + `SyncResult` field + `--split-archive` flag | WP-2 |
| `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` | Slimmed (only untagged entries remain post-split) | WP-2 execution |
| `docs/history/BATCH10_LOG.md` … `BATCH13_LOG.md` | New (created by `--split-archive`) | WP-2 execution |
| `tests/test_doc_state_sync.py` | Deleted | WP-3 |
| `tests/test_doc_state_sync_parsers.py` | New split file | WP-3 |
| `tests/test_doc_state_sync_metadata.py` | New split file | WP-3 |
| `tests/test_doc_state_sync_validation.py` | New split file | WP-3 |
| `tests/test_doc_state_sync_sync.py` | New split file | WP-3 |
| `tests/test_doc_state_sync_cli.py` | New split file | WP-3 |
| `tests/conftest.py` | `sync_env` fixture added | WP-3 |
| `tests/test_doc_state_sync_archival.py` | New — 12 tests for WP-2 | WP-4 |
| `AGENTS.md` | Updated doc-sync description + close-out procedure | WP-5 |
| `MEMORY.md` | Updated at batch close by closing agent | WP-5c |

---

## Verification

After each WP:
```
venv/Scripts/python.exe -m pytest -q                      # must show 288+ passed
venv/Scripts/python.exe -m pre_commit run --all-files     # all 8 hooks pass
```

After WP-2 migration run:
```
venv/Scripts/python.exe scripts/doc_state_sync.py --split-archive
venv/Scripts/python.exe scripts/doc_state_sync.py --check   # zero drift
```

After WP-3 split:
```
venv/Scripts/python.exe -m pytest tests/test_doc_state_sync_*.py -v   # 84 passed, 5 files
```

After WP-4:
```
venv/Scripts/python.exe -m pytest tests/test_doc_state_sync_archival.py -v  # 12 passed
venv/Scripts/python.exe -m pytest -q                                         # 300 passed
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
- **Orchestrator modularisation**: still premature; revisit when a second pipeline
  (Batch 15 feature) justifies splitting `orchestrator.py`.
