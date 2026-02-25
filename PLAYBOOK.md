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
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | (inline -- Section 3) |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/BATCH12_PROPOSAL.md` |
| 13 | Internal decomposition and coverage hardening | `BATCH13_PROPOSAL.md` |

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
- **Batch 13 is complete.** All 5 WPs done. Definition: `BATCH13_PROPOSAL.md`.
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

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-02-25 - test(retry): use public semaphore API in semaphore-gates test (side-task)

- Scope: `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer flagged `sem._value == 0` as a private implementation detail
  of `asyncio.Semaphore`, suppressed with `# noqa: SLF001`, making the assertion
  brittle across Python versions.
- Fix: Replaced with `sem.locked()`, the public equivalent (stable since Python 3.4).
  Updated comment; noqa suppression removed. Confirmed only occurrence in suite.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - fix(utils): support constant backoff value in retry_with_semaphore (side-task)

- Scope: `scrobblescope/utils.py`, `scrobblescope/spotify.py`,
  `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer 1 flagged that `backoff` only accepted a callable, requiring
  `backoff=lambda _a: 1` for constant delays. Updating call sites to use a plain
  float was not possible without a utility change.
- Fix: Added `callable(backoff)` guard at line 341 of `utils.py`; updated docstring
  type annotation. Simplified `spotify.py` search call site to `backoff=1`. Added
  `test_constant_float_backoff_accepted` to `test_retry_with_semaphore.py`.
- Validation: 288 passed (+1 vs Batch 13 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - test(orchestrator): use standard asyncio import in fetch_spotify tests (side-task)

- Scope: `tests/services/test_orchestrator_fetch_spotify.py`.
- Problem: Reviewer 2 flagged two `__import__("asyncio").Semaphore(5)` usages
  bypassing Pylance type resolution; root cause was missing top-level `import asyncio`.
- Fix: Added `import asyncio` to stdlib imports block; replaced both
  `__import__("asyncio").Semaphore(5)` occurrences with `asyncio.Semaphore(5)`.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-24 - docs(audit): BATCH13 pre-approval audit report (side-task)

- Scope: `BATCH13_PROPOSAL.md`, `docs/history/BATCH13_AUDIT_2026-02-23.md`.
- Problem: BATCH13 proposal required independent technical verification before
  owner approval. Line references, test coverage claims, retry extraction
  design, and convention compliance needed validation against actual codebase.
- Fix: Completed 4-WP audit. Found 5 discrepancies: `_apply_pre_slice` line
  start off by 2 (L664 -> L666), `_JOB_SEMAPHORE` variable name incorrect
  (actual: `_active_jobs_semaphore`), batch retry missing jitter declaration,
  batch backoff incorrectly stated as fixed 1.0 (actual: `2**attempt`
  exponential). Applied all corrections to the proposal. Created audit report.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed. No source
  code changes -- audit only.
