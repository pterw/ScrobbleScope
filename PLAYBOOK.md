# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/BATCH10_DEFINITION_2026-02-21.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/BATCH11_DEFINITION.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/BATCH12_DEFINITION.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/BATCH13_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batches 10-12 are complete.** See Section 2 table for definitions.
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days
    (Last.fm-only, lighter background task).
- **Batch 13 is complete.** All 5 WPs done. Definition: `docs/history/BATCH13_DEFINITION.md`.
  - WP-1: 6 worker.py tests. WP-2: search/batch-detail extraction. WP-3: 5
    _fetch_and_process helpers. WP-4: test file split (4 files). WP-5: DRY
    retry_with_semaphore utility.
  - **Post-batch note:** orchestrator.py (906 lines, 14 functions) is now
    modularization-ready but splitting into sub-modules is premature. The file
    has clean internal seams; splitting would add inter-module import complexity
    without reducing cognitive load. Revisit when a new feature (top songs,
    heatmap) adds a second pipeline and the file actually needs the room.
- **Side-task (doc hygiene):** The doc archival system has accumulated
  inconsistencies that should be addressed before the next batch:
  1. **Batch definitions not archived:** `BATCH13_PROPOSAL.md` is in the repo
     root instead of `docs/history/`. Batch 11 has no definition file at all
     (marked "inline -- Section 3"). Completed batch definitions should be
     moved to `docs/history/` as `BATCHN_DEFINITION.md` (or `_PROPOSAL.md`) and
     linked in the Section 2 table.
  2. **Monolith execution log archive:** `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
     is 1200+ lines of interleaved log entries from all batches. Should be
     split into per-batch files (e.g., `BATCH13_LOG.md`) so each
     batch's history is self-contained and searchable.
  3. **`doc_state_sync.py` enhancements needed:** The script currently rotates
     log entries into the single archive file. It needs: (a) batch-definition
     archival (move root `BATCHN_*.md` to `docs/history/` on batch close),
     (b) per-batch log splitting instead of appending to the monolith archive,
     (c) Section 2 table link validation for all completed batches.
  4. **`AGENTS.md` update needed:** Add explicit rules for batch close-out:
     definition file must be in `docs/history/`, Section 2 table must link it,
     and log entries route to per-batch log files.
- Do not start feature work (top songs, heatmap) until owner defines scope
  and assigns a batch number.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-02-25 - feat(doc-sync): per-batch log routing and --split-archive migration (Batch 14 WP-3)

- Scope: `scripts/docsync/models.py` (SyncResult +`batch_log_updates`),
  `scripts/docsync/logic.py` (`_merge_entries_into_log`, `_split_archive`, `_sync` routing),
  `scripts/docsync/cli.py` (`LOGS_DIR`, `DEFINITIONS_DIR`, `_get_batch_log_path`,
  `_check_root_batch_files`, `_read_batch_log_lines`, `--split-archive` flag, write/check
  loop for per-batch logs), `tests/conftest.py` (`LOGS_DIR` monkeypatch + `logs/` dir),
  `tests/test_docsync_logic.py` (1 test updated for new routing behaviour).
- Problem: All rotated log entries went to the monolith archive regardless of batch tag.
  Per-batch log routing (one file per batch in `docs/history/logs/`) was needed so each
  batch's history is self-contained and searchable.  A one-time `--split-archive` command
  was needed to migrate existing monolith entries.  Root unarchived `BATCH*.md` files
  were not warned about during `--check`/`--fix`.
- Plan vs implementation: Followed WP-3 spec.  `_sync` now routes tagged
  `(Batch N ...)` rotated entries to `batch_log_updates[N]` via `_merge_entries_into_log`;
  untagged/side-task entries continue to the monolith archive.  `--split-archive` is a
  separate code path (not `--check`/`--fix`) to avoid breaking the pre-commit hook before
  migration is run.  Import chain unchanged (models ← parser ← renderer ← logic ← cli).
  `_check_root_batch_files` added to cli.py; called after `_cross_validate` in main().
  `_write_lines` gained `path.parent.mkdir(parents=True, exist_ok=True)` to auto-create
  `docs/history/logs/` on first write.
- Deviations: `--check` and `--fix` changed to be verified as mutually exclusive via a
  manual `mode_count` check (instead of argparse `add_mutually_exclusive_group`) to preserve
  existing test `test_both_check_and_fix_returns_2` which expects `main()` to return 2
  (not raise SystemExit).  `test_stale_entries_rotated_to_archive` updated to assert
  entry lands in `batch_log_updates[10]` (not monolith) per new routing rules.
- Validation: **294 passed**, all 8 pre-commit hooks passed.
- Forward guidance: WP-3b next — run `--split-archive` to migrate the monolith, then
  move BATCHN_DEFINITION.md files to `docs/history/definitions/`, update ARCHIVE_PATH
  to `docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, update PLAYBOOK Section 2 links.

### 2026-02-25 - refactor(doc-sync): extract docsync package and split test monolith (Batch 14 WP-2)

- Scope: `scripts/doc_state_sync.py` (thin wrapper), `scripts/docsync/` (new package:
  `__init__.py`, `models.py`, `parser.py`, `renderer.py`, `logic.py`, `cli.py`),
  `tests/conftest.py` (sync_env fixture + MINIMAL_* constants added),
  `tests/test_doc_state_sync.py` (deleted), 5 new test files
  (`test_docsync_models.py`, `test_docsync_parser.py`, `test_docsync_renderer.py`,
  `test_docsync_logic.py`, `test_docsync_cli.py`).
- Problem: `scripts/doc_state_sync.py` was a 679-line monolith with no internal module
  boundaries; `tests/test_doc_state_sync.py` was a 1149-line test monolith with 18
  classes. Both needed structural separation before WP-3 adds new logic.
- Plan vs implementation: Followed WP-2 deliverables exactly. Import chain (models ←
  parser ← renderer ← logic ← cli) is acyclic. `_fingerprint` and `_normalize_block`
  placed in `parser.py` to avoid a circular import (used in `_parse_entries` which builds
  Entry objects, and `logic.py` imports from `parser.py`). `_sync` signature changed from
  `_sync(keep_non_current)` to `_sync(playbook_lines, archive_lines, session_lines,
  keep_non_current)` -- I/O responsibility moved entirely to `cli.py`. Test split:
  models(5) + parser(24) + renderer(15) + logic(28) + cli(12) = 84. TestSyncIntegration
  tests restructured to read files from sync_env and pass lines to logic._sync() directly.
  Two missing-file tests (previously in TestSyncIntegration) restructured to test via
  cli.main() and moved to TestMainArgs.
- Deviations: BATCH14_PROPOSAL.md listed `_fingerprint` in `logic.py`; placed in
  `parser.py` instead to break a circular import between parser and logic. No logic
  changes; purely a placement decision. Test distribution differs slightly from proposal
  table (~19 renderer → 15, ~30 logic → 28, ~10 cli → 12); total 84 unchanged.
- Validation: **288 passed**, all 8 pre-commit hooks passed.
- Forward guidance: WP-3 next -- add per-batch log routing and `--split-archive` flag
  to `docsync/logic.py` and `docsync/cli.py`.

### 2026-02-25 - docs(history): archive and rename definition files for batches 11/12/13 (Batch 14 WP-1)

- Scope: `docs/history/BATCH11_DEFINITION.md` (new), `docs/history/BATCH12_DEFINITION.md`
  (renamed from BATCH12_PROPOSAL.md), `docs/history/BATCH13_DEFINITION.md`
  (moved from root BATCH13_PROPOSAL.md), `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`.
- Problem: Three archival inconsistencies accumulated during Batch 13 delivery:
  BATCH11 had no definition file (inline PLAYBOOK only); BATCH12 used a
  `_PROPOSAL.md` suffix breaking the `_DEFINITION.md` convention; BATCH13 was
  in the repo root, not archived, and also used `_PROPOSAL.md`.
- Plan vs implementation: Followed WP-1 deliverables exactly. Created
  BATCH11_DEFINITION.md synthesised from archive log entries (WP-1, WP-3,
  WP-2 entries, date range 2026-02-21 to 2026-02-22, net +8 tests from WP-2).
  Renamed BATCH12 and moved/renamed BATCH13 via `git mv`. Updated PLAYBOOK
  Section 2 table (all three rows) and Section 3 BATCH13 reference; updated
  SESSION_CONTEXT Batch 13 status row, Batch 14 status, and Branch rows.
- Deviations: Discovered that log entry headings containing "Batch N" for
  old batches (e.g. "Batch 11-13") cause `_extract_entry_batch` to match the
  old number before the "(Batch 14 WP-X)" suffix tag, mis-classifying the
  entry as stale and rotating it to the archive. Fixed by using "batches
  11/12/13" (plural form -- regex requires "Batch \\d+") in the heading body.
- Validation: **288 passed**, all 8 pre-commit hooks passed.
- Forward guidance: WP-2 next -- extract `scripts/doc_state_sync.py` into
  `scripts/docsync/` package (pure structural refactor, zero logic changes).

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-02-25 - fix(doc-sync): remediate SESSION_CONTEXT staleness in _cross_validate and _build_status_block (side-task)

- Scope: `scripts/docsync/logic.py`, `scripts/docsync/renderer.py`, `scripts/docsync/cli.py`,
  `tests/test_docsync_logic.py` (+6 tests: 4 TestLatestTestCount + 2 rewritten + 1 renamed),
  `tests/test_docsync_renderer.py` (+2 TestBuildStatusBlock count tests),
  `tests/test_docsync_cli.py` (1 test updated).
- Problem: Two root causes for SESSION_CONTEXT staleness: (1) `_cross_validate` scanned
  PLAYBOOK Section 3 for `**N passed**` counts, but agents write test counts in Section 4
  log entry Validation fields — Section 3 is narrative prose. `playbook_counts` was always
  empty so the mismatch warning never fired. (2) `_build_status_block` did not include the
  test count in the STATUS block output, forcing agents to check stale manual rows.
  Additionally, `_cross_validate` was called with `result.session_lines` (post-sync), which
  already had the correct count injected by `_build_status_block`, laundering mismatch away.
- Fix: Added `_latest_test_count_from_entries(playbook_lines)` to `logic.py` — parses
  Section 4 current-batch entries newest-first and returns the first `**N passed**` count.
  Updated `_cross_validate` to call this function (scalar comparison) instead of scanning
  Section 3. Added `_TEST_COUNT_RE` to `renderer.py`; `_build_status_block` now emits
  `"- Latest validated test count: **N passed**."` using the most-recent entry body count.
  Fixed `cli.py` to call `_cross_validate(playbook_lines, session_lines)` (original, pre-sync
  lines) so the STATUS block update cannot launder a pre-existing mismatch.
- Deviations: None. All changes additive; no logic in `_sync` was touched.
- Validation: **294 passed** (+6 vs WP-2 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - docs(audit): add BATCH14 pre-approval audit report and apply corrections to proposal (side-task)

- Scope: `BATCH14_PROPOSAL.md`, `docs/history/BATCH14_AUDIT_2026-02-25.md`.
- Purpose: Pre-batch audit of BATCH14_PROPOSAL.md before owner sign-off. Verified
  all five structural checks (WP-1 naming conventions, WP-2 package extraction
  symmetry, WP-3 feature isolation, WP-4 test distribution, WP-5 AGENTS.md
  close-out / MEMORY.md hallucination check). All five checks confirmed correct.
- Correction: "~450-line" description for `doc_state_sync.py` corrected to "~679-line"
  in two places (Current state table and WP-2 goal). Actual measured line count: 679.
- Verdict: APPROVED WITH CORRECTIONS.
- Validation: 288 passed (unchanged -- audit makes no code changes), all 8 pre-commit
  hooks passed.

### 2026-02-25 - test(worker): assert daemon=True via Thread patch, expand docstrings (side-task)

- Scope: `tests/test_worker.py`.
- Problem: `test_start_job_thread_creates_daemon_thread` only asserted the target
  was called; it never verified `threading.Thread` was constructed with `daemon=True`,
  despite the test name and docstring claiming otherwise. Tests 1–4 had minimal
  single-line docstrings inconsistent with the GIVEN/WHEN/THEN standard.
- Fix: Introduced `DummyThread` class, patched at `scrobblescope.worker.threading.Thread`;
  asserts `daemon=True` and target invocation. Dropped `*args` from `DummyThread.__init__`
  (Pylance hint; Thread is called with keyword args only). Expanded tests 1–4 docstrings
  to GIVEN/WHEN/THEN inline format.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - test(retry): use public semaphore API in semaphore-gates test (side-task)

- Scope: `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer flagged `sem._value == 0` as a private implementation detail
  of `asyncio.Semaphore`, suppressed with `# noqa: SLF001`, making the assertion
  brittle across Python versions.
- Fix: Replaced with `sem.locked()`, the public equivalent (stable since Python 3.4).
  Updated comment; noqa suppression removed. Confirmed only occurrence in suite.
- Validation: 288 passed, all 8 pre-commit hooks passed.
