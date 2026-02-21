# ScrobbleScope Execution Playbook (Post-Compact Handoff)

Date: 2026-02-11
Owner context: This playbook defines the implementation order, standards, and guardrails for the next major batches.
Primary goal: Improve reliability, UX, and maintainability without behavior regressions, then refactor monolithic `app.py` safely.

## 1. Why this document exists
- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

## 1b. Document roles (anti-drift contract)
- `PLAYBOOK.md`: active execution contract (batch order, standards, active log window, next actions).
- `.claude/SESSION_CONTEXT.md`: concise current-state snapshot (status, architecture, risks, environment notes).
- `README.md`: product and setup reference for users/developers, not batch execution history.
- `AGENTS.md`: agent behavior rules (bootstrap order, commit style, markdown and update duties).

## 2. Current status snapshot
- `app.py` is a minimal factory (~142 lines): `create_app()` + logging setup + `CSRFProtect` init + secret-key startup guard + `app = create_app()` for Gunicorn compat.
- All application logic lives in the `scrobblescope/` package (11 modules including package marker, acyclic dependency graph).
- Routes use a Flask Blueprint (`scrobblescope/routes.py`).
- Per-job in-memory state in `scrobblescope/repositories.py` (`JOBS` dict).
- Orphan job on thread-start failure: resolved 2026-02-20. `delete_job(job_id)` added to `repositories.py` and called in `routes.results_loading` except block.
- No app-level keep-alive thread is present; `results_loading` spawns one daemon worker per job and `background_task` owns a single event loop on that worker thread.
- Persistent Spotify metadata cache (Postgres via asyncpg, `scrobblescope/cache.py`):
  - `spotify_cache` table with 30-day TTL, batched reads/writes via `unnest()`.
  - DB connection wake-up hardening: `_get_db_connection()` retries with exponential backoff before cache bypass.
  - Graceful fallback: if `DATABASE_URL` is unset, `asyncpg` is unavailable, or DB is unreachable, full Spotify flow runs.
  - `_get_db_connection()` emits classified fallback logs for `missing-env-var`, `asyncpg-missing`, and `db-down`.
  - Full DB cache hits can complete without Spotify availability.
  - If Spotify is unavailable while cache hits exist, cached results still return with `partial_data_warning`.
  - Schema automated via `init_db.py` release_command on Fly deploys.
- Fly cold-start recovery was validated on 2026-02-19 by manually stopping both app and DB machines, then triggering one end-to-end smoke run that auto-started both and completed successfully (`elapsed=18.75s`, `db_cache_lookup_hits=247`).
- `tojson` JS data bridge is in place in templates.
- Unmatched modal has escaping in `static/js/results.js`.
- Nested thread pattern removed:
  - Outer worker thread remains in `results_loading`.
  - `background_task` now owns one event loop directly (no inner thread).
- Dark-mode toggle now uses a compact fixed bottom placement across pages; label auto-hides on extra-small screens.
- `index.html` now renders server-side validation errors (Batch 6).
- Historical audit/changelog/refactor docs are archived under `docs/history/` to reduce repo-root clutter.
- Comprehensive repo audit completed on 2026-02-20; remediation execution plan is documented at `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`.
- Test suite: **92 tests** across 8 files (`test_app_factory.py`, `test_domain.py`, `test_repositories.py`, `test_utils.py`, `test_routes.py`, `tests/services/test_lastfm_service.py`, `tests/services/test_spotify_service.py`, `tests/services/test_orchestrator_service.py`) covering job lifecycle, routes (including unmatched_view + 404/500 handlers + CSRF enforcement on all 4 POST routes + registration-year validation), normalization, error classification, template safety, background task structure, reset flow, async service retry paths, DB helpers, cache integration, orchestrator correctness, DB connect retry/backoff behavior, thread-safe cache operations, concurrency slot lifecycle, and app-factory secret-key startup guard.
- **Product roadmap (confirmed 2026-02-20):** Two new background task types are planned:
  - **Top songs:** Rank user's most-played tracks for a year (Last.fm + possibly Spotify enrichment). Separate background task type, separate loading/results flow.
  - **Listening heatmap:** Calendar-style scrobble density map for the last 365 days. Last.fm API only (no Spotify), lighter background task.
- `scrobblescope/worker.py` (leaf module, imports `config` only) owns `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread()`. `repositories.py` is pure job state CRUD. See architectural rationale in `.claude/SESSION_CONTEXT.md` Section 7b.

## 3. Non-negotiable implementation principles
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

## 4. High-level batch order (strict sequence)
Status note:
- Batches are listed in execution order and kept sequential by batch number.
- Completed batches remain struck through for quick scanning.

### ~~Batch 0: Baseline freeze + approval parity suite~~
Purpose:
- Freeze externally visible behavior before risky internal changes.

Deliverables:
- Golden-path approval tests for:
  - `results_loading` -> polling -> `results_complete`.
  - No-match flow.
  - Invalid username flow.
  - Unmatched quick-view flow.
- Stable fixtures/mocks for Last.fm + Spotify responses.
- Snapshot or assertions for key response fields/messages.

Acceptance:
- Approval tests pass consistently in CI/local.
- Documented baseline outputs and constraints.

Risk:
- Flaky network-coupled tests. Mitigation: mock all external APIs.

---

### ~~Batch 1: Proper upstream failure state + retry UX~~
Purpose:
- Distinguish "no data" from "upstream unavailable".

Backend tasks:
- Introduce typed upstream failure classification:
  - `lastfm_upstream_unavailable`
  - `spotify_upstream_unavailable`
  - `user_not_found`
  - `rate_limited`
- Update progress payload to include structured error metadata:
  - `error_code`
  - `source`
  - `retryable`
  - `retry_after` (when known)
- Ensure Last.fm 5xx exhaustion does NOT map to "No albums found."

Frontend tasks:
- Loading page failure panel with explicit CTAs:
  - `Retry now` for retryable failures.
  - `Back home` fallback.
- Preserve existing reset behavior but align messaging to error type.

Acceptance:
- Last.fm repeated 5xx produces explicit upstream-failure message.
- "No albums found" only for legitimate empty-result conditions.
- Retry action works when failure is retryable.

---

### ~~Batch 2: Personalized minimum listening year from registration~~
Purpose:
- Improve input validation UX and reduce impossible queries.

Backend tasks:
- Extend `/validate_user` response with `registered_year` when available.
- Use Last.fm `user.getinfo.registered.unixtime`.
- Add server-side guard for submitted `year < registered_year` with clear error.

Frontend tasks:
- On successful username validation:
  - Set `#year.min` to `registered_year`.
  - Show inline guidance text.
- If user enters lower year:
  - Show inline validation error.
  - Block submission or rely on native validity + custom message.

Acceptance:
- For `flounder14`, min year resolves to 2016.
- Inline and server-side validation both enforce constraints.

---

### ~~Batch 3: Remove nested thread pattern~~
Purpose:
- Eliminate unnecessary thread layering and event-loop confusion risk.

Current anti-pattern:
- `results_loading` starts a thread that calls `background_task`.
- `background_task` calls `run_async_in_thread`.

Target:
- Single background thread runs async coroutine directly once.

Implementation options:
1. Keep thread in `results_loading`, convert `background_task` to run sync wrapper that owns loop directly (no second thread).
2. Or remove outer thread and keep `run_async_in_thread` (less preferred for request lifecycle).

Acceptance:
- No nested thread creation.
- No AsyncLimiter loop warnings.
- Same user-visible behavior.

---

### ~~Batch 4: Expand test coverage significantly~~
Purpose:
- Lock down correctness before larger refactor.

Test additions:
- Service-level tests:
  - Last.fm retry classification and error mapping.
  - Spotify 429 retry path.
  - User not found path.
- Route tests:
  - Structured progress errors.
  - Retry endpoint behavior.
  - Registration-year validation.
- Concurrency/state tests:
  - Multiple job isolation.
  - Expired job handling.
- Frontend-focused tests (where feasible):
  - Escaping for unmatched modal content.
  - Presence of `tojson` bridges in templates.

Docstring requirement for tests:
- Use the existing format style seen in `test_home_page(client)`.

Acceptance:
- Coverage materially increased around async paths and failure states.
- No regressions in approval suite.

---

### ~~Batch 5: Docstring + comment normalization~~
Purpose:
- Standardize maintainability and readability.

Scope:
- Fill missing function docstrings in `app.py`.
- Match style of existing best docstrings (example: `get_spotify_limiter`).
- Add brief comments only where logic is non-obvious.

Docstring format:
- Short summary line.
- Optional detail paragraph.
- Keep concise and consistent; avoid stale claims.

Acceptance:
- All top-level functions documented.
- No misleading or outdated docstrings.

---

### ~~Batch 6: Frontend refinement/tweaks~~
Purpose:
- Close UX debt without major redesign.

Tasks:
- Move fixed dark-mode toggle into mobile-safe header/action region.
- Clean encoding artifacts in JS strings.
- Improve loading-state readability and consistency.
- Ensure retry/error states are visually clear and accessible.
- **Known gap from Batch 4:** `index.html` does not render the `error=` variable passed by `results_loading` on validation failure (missing username, year out of bounds). The index page re-renders but the error message is silently dropped. Add an error alert block to `index.html` that displays `{{ error }}` when set.

Acceptance:
- No overlap with primary content on mobile.
- Clean text rendering.
- Error states understandable and actionable.

---

### ~~Batch 7: Persistent metadata layer (performance and cost)~~
Purpose:
- Reduce repeated Spotify lookups across cold starts and users.

Recommended architecture:
- Durable store first (Postgres preferred on Fly).
- Optional Redis as a hot cache in front.

Data model (minimum):
- `artist_norm`
- `album_norm`
- `spotify_id`
- `release_date`
- `album_image_url`
- `track_durations_json`
- `updated_at`

Lookup flow:
1. Check durable metadata store by normalized key.
2. Hit -> return immediately.
3. Miss -> call Spotify -> persist -> return.

Concerns:
- Validate Spotify API terms for metadata persistence.
- Add TTL or refresh policy to avoid stale data.

Acceptance:
- Repeat queries show reduced Spotify calls and latency.
- Cold-start behavior improved over time.

---

### ~~Batch 8: Modular refactor (app factory + blueprints + layered structure)~~
Prerequisite:
- Batches 0-7 complete and green.

Target structure (example):
- `scrobblescope/__init__.py` with `create_app()`
- `scrobblescope/routes/` (web/api blueprints)
- `scrobblescope/services/` (Last.fm, Spotify, orchestration)
- `scrobblescope/repositories/` (job store, metadata store)
- `scrobblescope/domain/` (models/errors)

Refactor method:
- Strangler pattern:
  - Move one slice at a time.
  - Keep route behavior identical.
  - Run approval suite after each slice move.

Acceptance:
- Functional parity preserved.
- No monolithic route/data logic in one file.
- Testability and config management improved.

---

### Batch 9: Audit remediation execution (WP-1 through WP-8)
Purpose:
- Execute the remediation track from `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md` in strict work-package order.

Execution order:
1. WP-1 (P0): Bound background job concurrency.
2. WP-2 (P0): Make request cache thread-safe.
3. WP-3 (P0): Add CSRF protection for mutating POST routes.
4. WP-4 (P1): Harden app secret and startup safety.
5. WP-5 (P1): Enforce registration-year validation server-side.
6. WP-6 (P1): Remove or gate artificial orchestration sleeps.
7. WP-7 (P2): Frontend safety and resilience polish.
8. WP-8 (P2): CI, lint, dependency hygiene.

Acceptance:
- WP-1 through WP-8 are completed and logged in Section 10 with validation evidence.
- Batch 9 outcomes match the acceptance criteria documented in the Batch 9 plan.

### Sequential completion index (Batch 0-9)
- ~~Batch 0~~: Done
- ~~Batch 1~~: Done
- ~~Batch 2~~: Done
- ~~Batch 3~~: Done
- ~~Batch 4~~: Done
- ~~Batch 5~~: Done
- ~~Batch 6~~: Done
- ~~Batch 7~~: Done
- ~~Batch 8~~: Done
- Batch 9: In progress

## 5. Suggested implementation granularity
- Keep PRs or commits small per batch.
- Do not mix architecture refactor with behavior changes in one step.
- Re-run:
  - `pre-commit run --all-files`
  - `pytest -q`
after each batch.

### Commit message standard
All commits must follow the Conventional Commits + imperative-mood convention:

```
<type>(<optional scope>): <subject>   <- max 72 chars, imperative mood

<body>                                 <- wrap at 72 chars; explain WHY
                                         not just what
```

**Types:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `style`, `perf`

**Subject rules (enforced):**
- Imperative mood: "Add", "Fix", "Remove", "Extract" -- NOT "Added", "Fixes", "Introducing"
- No period at the end
- No project-management metadata in the subject (`WP-1 (P0):` belongs in the body)
- Max 72 characters on the subject line

**Body rules:**
- Separated from subject by a blank line
- Explain the motivation and what changed, not just a file list
- File-level bullet lists are acceptable for specificity
- Wrap lines at 72 characters

**Examples:**
```
feat: bound background job concurrency and extract worker module

Introduce MAX_ACTIVE_JOBS (default 10, env-tunable) to cap concurrent
background jobs. Extract concurrency lifecycle into worker.py ahead of
planned top-songs and listening-heatmap features.
```
```
fix: release job slot when Thread.start() raises in results_loading

If Thread.__init__ or Thread.start() raises after acquire_job_slot()
succeeds, the slot was permanently consumed. Wrap thread creation in
try/except and call release_job_slot() before returning the error page.
```

## 6. Open decisions (owner confirmation needed)
1. Persistent store choice now: Postgres only or Postgres + Redis.
2. Retry UX policy:
   - immediate retry button only,
   - or retry + cooldown messaging.
3. ~~Whether to keep `results_loading` progress spoof sleeps or remove once UX states improve.~~ Resolved in WP-6: all 5 `asyncio.sleep(0.5)` calls removed.
4. Error copy style and user-facing tone for upstream failures.

## 7. Agent handoff checklist before starting a batch
1. Read:
   - `.claude/SESSION_CONTEXT.md`
   - `PLAYBOOK.md` (this file)
   - `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` (historical snapshot; may lag latest batch log in this file)
   - `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (when active-window history is insufficient)
   - `README.md` (product expectations, deployment context, known limitations)
2. Inspect current implementation hotspots in modular files before editing:
   - `scrobblescope/repositories.py` (job state lifecycle: `JOBS`, TTL cleanup)
   - `scrobblescope/routes.py` (`/progress`, `/results_complete`, `/unmatched_view`, error handlers)
   - `scrobblescope/orchestrator.py` (`background_task`, async pipeline, cache-hit/miss flow)
   - `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`, `scrobblescope/cache.py` (API/cache path)
3. Confirm latest completed batches in this playbook before trusting older docs.
4. Confirm repo is green:
   - `pre-commit run --all-files`
   - `pytest -q`
5. Confirm no unrelated local edits are reverted.
6. Implement one batch only.
7. Provide post-batch summary:
   - behavior change
   - files touched
   - tests added/updated
   - verification results

## 8. Batch completion logging standard
After each completed batch, update this playbook immediately.
All commits must comply with the commit message standard in Section 5.
1. Status update:
   - Strike through the completed batch title in Section 4.
   - Update "Immediate next batch to execute."
2. Snapshot update:
   - Update Section 2 only for material architecture/runtime state changes.
3. Required cross-doc sync after behavior/config/process changes:
   - Update `.claude/SESSION_CONTEXT.md` for current-state accuracy and risk notes.
   - Update `README.md` for setup, runtime, or user-visible behavior changes.
   - Keep `PLAYBOOK.md` as the active execution contract and log source.
4. Add one dated entry under "Batch execution log" with:
   - scope
   - plan vs implementation
   - deviations and why they were taken
   - additions beyond plan
   - struggles/constraints and unresolved risks
   - validation performed
   - forward guidance for the next agent
5. Document stale references:
   - Keep historical docs; do not delete.
   - Mark here whether a doc is historical baseline vs current source of truth.

### Markdown authoring rules (agent-facing)
- Use ASCII-only characters in markdown files. Replace smart punctuation with plain ASCII (`--`, `->`, `<-`, quotes).
- Use ISO dates: `YYYY-MM-DD`.
- Batch/execution log entries must include: scope, plan vs implementation, deviations (if any), validation, and forward guidance.
- If requirements are ambiguous, ask clarifying questions before writing docs that change process/state contracts.
- When adding new dated entries, archive-rotate old non-active entries into `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` to maintain the active-window policy in Section 10.
- After any Section 10 update, run `python scripts/doc_state_sync.py --fix`, then re-run checks.

## 9. Immediate next batch to execute
- Batch 9 is now defined as a risk-remediation sequence based on the 2026-02-20 comprehensive audit.
- Execute `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md` in order (WP-1 through WP-8), one package at a time.
- Keep all Batch 9 changes scoped, validated, and logged in Section 10 after each completed work package.


## 10. Batch execution log (for agent handoff)
Source-of-truth note:
- For current status, prefer Section 2 and this execution log.
- Keep only the active window here: current batch entries plus the latest 4 non-current operational logs.
- Older dated entries live in `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

### How to read dated entries
- Each heading in the form `YYYY-MM-DD - Batch X ...` is a historical completion/addendum log.
- Active-window policy: this section keeps current Batch 9 logs and only 4 non-current historical logs.
- Archive location: `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (reverse-chronological order, newest first).
- Open/archive search commands:
  - `Get-Content docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  - `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  - `rg -n "<keyword>" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- If current context is insufficient, agents must follow archive links and read relevant dated entries before changing code/docs.
- New entries must use ISO dates (`YYYY-MM-DD`) and include scope, deviations, validation, and forward guidance.
- Current-batch boundaries are explicit and machine-managed:
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- Do not manually move entries across these markers; run `python scripts/doc_state_sync.py --fix`.

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-02-20 - WP-7: frontend safety — showToast DOM construction + non-200 fetch guard
- Scope: `static/js/results.js`.
- Problem 1: `showToast` built its HTML via a template-literal string injected with
  `insertAdjacentHTML`. The `message` argument was interpolated without escaping,
  creating an HTML injection pathway if any caller passed server-sourced content.
- Problem 2: `fetchUnmatchedAlbums` piped `fetch()` directly to `.json()` without
  checking `response.ok`. A non-200 response (404, 500, etc.) would be silently
  treated as valid data, surfacing as "No unmatched albums found" instead of an
  error.
- Fix:
  - Rewrote `showToast` to build the toast element tree with `document.createElement`
    / `textContent` / `setAttribute`; eliminated `insertAdjacentHTML` and the unused
    `toastId`. Message content is now set via `.textContent` (XSS-safe).
  - Added `response.ok` guard before `response.json()` in `fetchUnmatchedAlbums`;
    throws `Error("Server error: <status>")` on non-2xx, which the existing `.catch`
    handler surfaces to the user.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: WP-7 complete. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - P1 refactor: extract VALID_FORM_DATA and csrf_app_client fixture
- Scope: `tests/helpers.py`, `tests/conftest.py`, `tests/test_routes.py`.
- Problem: `VALID_FORM_DATA` (the flounder14/2025 form dict for `/results_loading`
  tests) was copy-pasted verbatim 7 times across `test_routes.py`. The 5-line
  CSRF-enabled app + test-client setup was repeated in every CSRF test function.
- Fix:
  - Added `VALID_FORM_DATA` constant to `tests/helpers.py`.
  - Added `csrf_app_client` pytest fixture to `tests/conftest.py`; it creates a
    CSRF-enabled app client (WTF_CSRF_ENABLED not disabled) for CSRF enforcement
    tests.
  - Updated `tests/test_routes.py`: removed `from app import create_app` (now
    unused); imported `VALID_FORM_DATA` from `tests.helpers`; replaced all 7
    inline form dicts with `VALID_FORM_DATA` (or `{**VALID_FORM_DATA, "year": "X"}`
    for year-override cases); replaced all 6 CSRF test inline app setups with the
    `csrf_app_client` fixture parameter.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; pure refactor, no behaviour
    change).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - P1 perf: remove O(n) cache-size scan from cleanup_expired_cache
- Scope: `scrobblescope/utils.py`.
- Problem: `cache_size_mb = sum(len(str(v)) for v in REQUEST_CACHE.values()) / ...`
  ran inside `_cache_lock` on every cleanup call, even when debug logging was
  disabled. This O(n) string-serialization of all cached values held the lock
  unnecessarily and added CPU overhead proportional to cache size.
- Fix: removed the `cache_size_mb` line and simplified the debug log to
  `f"Cache status: {cache_count} entries"`. Count-only logging is sufficient
  for operational visibility; size estimation is not a runtime requirement.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; no test needed for log format).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next P1 item is test boilerplate extraction in
  `test_routes.py` (VALID_FORM_DATA + csrf_app_client fixture).

### 2026-02-20 - P0 fix: delete orphan JOBS entry on thread-start failure
- Scope: `scrobblescope/repositories.py`, `scrobblescope/routes.py`,
  `tests/test_repositories.py`, `tests/test_routes.py`.
- Problem: `create_job()` was called before `start_job_thread()`; on thread-start
  failure the semaphore slot was correctly released by `worker.py`, but the
  `JOBS[job_id]` entry persisted as an orphan until the 2-hour TTL cleanup.
- Fix:
  - Added `delete_job(job_id)` to `repositories.py`:
    `with jobs_lock: JOBS.pop(job_id, None)`.
  - Imported `delete_job` in `routes.py`; called it in the `except` block after
    thread-start failure, before returning the error page.
  - Added 2 tests to `test_repositories.py`:
    `test_delete_job_removes_existing_job`,
    `test_delete_job_on_missing_job_is_noop`.
  - Strengthened existing `test_results_loading_thread_start_failure_renders_error`
    to assert `mock_delete_job.assert_called_once()`.
- Validation:
  - `pytest -q`: **94 passed** (92 pre-existing + 2 new).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: The known orphan-job open risk (SESSION_CONTEXT.md Section 2)
  is now closed. Remaining P1 items: cache_size_mb in `cleanup_expired_cache`,
  and test boilerplate extraction in `test_routes.py`. Next required work package
  is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - README refreshed (Batch 9 completions and roadmap)
- Scope: `README.md`.
- Changes:
  - Python badge updated from `3.9+` to `3.13+`.
  - Removed stale playtime-sorting caveat from Features section.
  - Tech Stack: `Python 3.x` -> `Python 3.13`; added `Flask-WTF` to Core Python
    Libraries bullet.
  - Key Implementation Highlights: added three bullets (Bounded Job Concurrency,
    CSRF Protection, Startup Secret Guard).
  - Project File Structure: added `worker.py`, `test_app_factory.py`,
    `test_utils.py`, `scripts/doc_state_sync.py`.
  - Current Status checklist: added six new `[x]` items for WP-1 through WP-6
    outcomes.
  - Added "Confirmed upcoming features" subsection (top songs, listening heatmap).
  - Added "UI enrichments (planned, lower priority)" subsection.
- Commit: `14f251a` docs: refresh README for Batch 9 completions and roadmap.
- Forward guidance: README is now accurate as of WP-6 completion. Next step is WP-7.

### 2026-02-20 - doc_state_sync maintenance (remove volatile Last sync commit field)
- Scope: `scripts/doc_state_sync.py`, `.claude/SESSION_CONTEXT.md`.
- Issue: `doc-state-sync-check` pre-commit hook was failing on PR merge to main.
  Root cause: `_build_status_block()` called `git rev-parse --short HEAD` to write
  `Last sync commit: <hash>` into SESSION_CONTEXT.md. On `--check`, the command
  returned the NEW merge commit hash, which did not match the stored hash, causing
  drift detection failure on every merge.
- Fix: Removed `_git_head_short()` function, `subprocess` import, and the
  `Last sync commit` line from `_build_status_block`. The `--check` now validates
  only stable content-level fields (batch number, WP numbers, entry count, newest
  heading). Ran `--fix` to drop the stale `Last sync commit` line from
  SESSION_CONTEXT.md.
- Commit: `cdedd65` fix: remove Last sync commit from doc_state_sync status block.
- Forward guidance: The doc-state-sync-check hook will no longer false-positive on
  merge commits. SESSION_CONTEXT DOCSYNC block is validated on content only.

### 2026-02-20 - WP-6 completed (remove artificial orchestration sleeps)
- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Removed all 5 `await asyncio.sleep(0.5)` calls from `_fetch_and_process`. The
    calls were added as a progress-pacing mechanism but served no functional purpose
    and added a fixed 2.5 s latency overhead to every job.
  - All `set_job_progress` calls and their messages are preserved at the same
    progress values (0, 5, 20, 30, 40, 60, 80, 90, 100), so the loading-page
    progress sequence is unchanged from the user's perspective.
  - `asyncio` import retained: `asyncio.Semaphore`, `asyncio.gather`,
    `asyncio.new_event_loop`, and `asyncio.set_event_loop` are still used.
  - Removed two dead `patch("asyncio.sleep", new_callable=AsyncMock)` lines from
    `test_fetch_and_process_cache_hit_does_not_precheck_spotify` and
    `test_fetch_and_process_sets_spotify_error_from_process_albums` in
    `tests/services/test_orchestrator_service.py`. Those patches were no-ops after
    the sleep removals.
- Deviations and why: none. "Gate with debug-only UX flag" option was not needed;
  the plain removal is simpler and all test coverage is already progress-message
  based, not timing based.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (no count change; two dead patches removed,
    no new tests needed).
- Forward guidance: Next work package is WP-7 (frontend safety and resilience
  polish).

### 2026-02-20 - WP-5 completed (enforce registration-year validation server-side)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added a registration-year guard in `results_loading` immediately after the
    `2002..current_year` bounds check. The guard calls `check_user_exists(username)`
    via `run_async_in_thread` (same helper used by `validate_user`). The result is
    already cached from the blur-validation step, so the call is typically free.
  - If `registered_year` is present and `year < registered_year`, the route
    re-renders `index.html` with an explicit error message citing the registration
    year and the earliest valid year.
  - If the check raises (Last.fm unavailable, network error, etc.), a `WARNING`
    is logged and the route proceeds without blocking the user (fail-open policy).
  - If `registered_year` is `None` (not returned by Last.fm), the check is skipped
    and the route proceeds normally.
  - Updated four existing `results_loading` tests that reach the guard to patch
    `scrobblescope.routes.run_async_in_thread` with a neutral result
    (`{"exists": True, "registered_year": None}`) to avoid live network calls.
  - Added four new tests to `tests/test_routes.py`:
    - `test_results_loading_year_below_registration_year_rejected`
    - `test_results_loading_year_at_registration_year_allowed`
    - `test_results_loading_registration_check_unavailable_proceeds`
    - `test_results_loading_no_registered_year_proceeds`
- Deviations and why: none. Fail-open on service unavailability was the intended
  design from the WP-5 spec (client-side validation already covered the common
  case; server-side guard adds defense-in-depth without blocking on transient errors).
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (88 pre-existing + 4 new).
- Forward guidance: Next work package is WP-6 (remove or gate artificial
  orchestration sleeps).

### 2026-02-20 - WP-4 completed (harden app secret and startup safety)
- Scope: `app.py`, `tests/conftest.py`, `tests/test_app_factory.py` (new), `.env.example`, `README.md`.
- Plan vs implementation:
  - Added `_KNOWN_WEAK_SECRETS = frozenset({"dev", "changeme_in_production", ""})` and `_MIN_SECRET_LENGTH = 16` constants in `app.py`.
  - Added `_validate_secret_key(secret_key: str, is_dev_mode: bool) -> None` in `app.py`. Logic: if key is falsy, in weak set, or shorter than 16 chars -> "weak". In production (`debug_mode=False`): raises `RuntimeError("Refusing to start: ...")`. In dev mode (`DEBUG_MODE=1`): logs `WARNING "SECRET_KEY is missing or insecure. ..."`.
  - Updated `create_app()` to read `_raw_secret = os.getenv("SECRET_KEY", "")`, call `_validate_secret_key(_raw_secret, debug_mode)`, then set `application.secret_key = _raw_secret or "dev"`. "dev" is the dev-mode fallback; in production, `_validate_secret_key` raises before it can be used.
  - `tests/conftest.py` updated: added `import os` + `os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")` before `from app import create_app`. This seeds the guard before `app.py`'s module-level `create_app()` call (which runs at import time).
  - New `tests/test_app_factory.py` with 7 tests: production-fail on missing/dev/changeme/too-short keys; dev-mode warning; strong-key success in both modes.
  - `.env.example` `SECRET_KEY` comment updated to say "REQUIRED in production. Startup fails if missing or set to placeholder."
  - `README.md` setup step 4 comment updated from "Recommended" to "Required in production" with note that `DEBUG_MODE=1` suppresses the check for local dev.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black reformatted `app.py` quote style on first run; clean on second).
  - `pytest -q`: **88 passed** (81 pre-existing + 7 new).
- Commit: `eb13a27` feat: refuse startup on weak SECRET_KEY in production.
- Forward guidance: Next work package is WP-5 (enforce registration-year validation server-side).

### 2026-02-20 - WP-1 correctness fix (slot leak on Thread.start failure)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Issue: WP-1 post-audit check found that `acquire_job_slot()` in `results_loading` was not guarded against failure of `Thread.__init__` or `Thread.start()`. If either raises (e.g. `OSError` under OS-level thread exhaustion), the slot is permanently consumed because `background_task`'s `finally` block never runs. This violates WP-1's acceptance criterion "no leaked active slots after worker exceptions."
- Fix:
  - Added `release_job_slot` to imports in `routes.py`.
  - Wrapped `threading.Thread(...)` and `task_thread.start()` in try/except; on exception: `release_job_slot()`, `logging.exception(...)`, return `index.html` with error message.
  - Added `test_results_loading_thread_start_failure_releases_slot`: patches `Thread` to raise `OSError`, asserts slot is released and index re-rendered.
- Validation:
  - `pre-commit run --all-files`: all hooks passed.
  - `pytest -q`: 77 passed.
- Also: added "callers must not mutate" to `get_cached_response` docstring (latent mutable-reference risk; no active bug since no caller mutates the returned object).

### 2026-02-20 - Comprehensive repo audit completed + Batch 9 remediation plan authored
- Scope: full-codebase audit (backend Python, frontend templates/JS/CSS, tests/CI/config/docs), plus operational handoff planning.
- Plan vs implementation:
  - Performed a severity-ranked audit focused on security, reliability, correctness, and optimization pathways.
  - Identified concrete high/medium/low findings with file-level references.
  - Authored actionable execution plan for next agent:
    - `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`
    - Includes WP-1..WP-8, acceptance criteria, and execution order.
  - Updated this playbook and session context to treat Batch 9 as the active next execution track.
- Validation:
  - `venv\Scripts\python -m pytest tests --cov=scrobblescope --cov-report=term-missing -q`: **66 passed**, overall coverage **72%**.
  - Coverage highlighted lower-tested hotspots used to seed Batch 9 work-package ordering (`lastfm.py`, `utils.py`, `spotify.py`, portions of `orchestrator.py`).
- Forward guidance:
  - Execute WP-1 and WP-2 first (highest reliability risk reduction).
  - Keep documentation synchronized after each work package per Section 8.

### 2026-02-19 - Batch 9 WP-3 completed (CSRF protection for mutating POST routes)
- Scope: `requirements.txt`, `app.py`, `templates/index.html`, `templates/results.html`, `templates/loading.html`, `static/js/loading.js`, `tests/conftest.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added `Flask-WTF>=1.2.0` to `requirements.txt` (installed v1.2.2).
  - Added `CSRFProtect` to `app.py`: `csrf = CSRFProtect()` at module level, `csrf.init_app(application)` in `create_app()`, plus a `CSRFError` handler that returns a 400 with the `error.html` template and a user-facing message.
  - Added `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` inside the `<form>` element in `templates/index.html` and `templates/results.html` (unmatched_view form).
  - Added `<meta name="csrf-token" content="{{ csrf_token() }}">` to the `head_extra` block in `templates/loading.html`.
  - Updated `static/js/loading.js`:
    - Added `const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';` near the top (after the `window.SCROBBLE` destructure).
    - Prepended `form.appendChild(createHiddenInput('csrf_token', csrfToken));` as the first hidden input in both `redirectToResults()` and `retryCurrentSearch()`.
    - Added `'X-CSRFToken': csrfToken` to the headers of the `fetch('/reset_progress', ...)` call in the error handler.
  - Updated `tests/conftest.py`: added `application.config["WTF_CSRF_ENABLED"] = False` so all existing tests continue to pass without supplying tokens.
  - Added two CSRF tests to `tests/test_routes.py`:
    - `test_csrf_rejects_post_without_token`: creates a CSRF-enabled app client, POSTs without a token, asserts 400.
    - `test_csrf_accepts_post_with_valid_token`: GETs `/` to capture the token from the rendered HTML, POSTs with it, asserts 200 and `window.SCROBBLE` in response.
- Deviations and why: none.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8, trim, end-of-file).
  - `pytest -q`: 76 passed (2 new tests added).
- Forward guidance:
  - WP-4 (secret hardening) is the next work package.
  - The `WTF_CSRF_ENABLED = False` fixture override is intentional and standard; it must remain in `conftest.py` to keep all POST route tests free of token boilerplate.
  - Flask-WTF validates the token from `request.form['csrf_token']` for form POSTs and from `X-CSRFToken` header for XHR/fetch POSTs. Both paths are now covered.

### 2026-02-19 - Batch 9 WP-2 completed (thread-safe REQUEST_CACHE)
- Scope: `scrobblescope/utils.py`, `tests/test_utils.py` (new file).
- Plan vs implementation:
  - Added `_cache_lock = threading.Lock()` to guard all `REQUEST_CACHE` access in `utils.py`.
  - Wrapped `get_cached_response` in `_cache_lock` to eliminate TOCTOU between `key in REQUEST_CACHE` and `REQUEST_CACHE[key]`.
  - Wrapped `set_cached_response` in `_cache_lock` for atomic writes.
  - Wrapped the full iterate-and-pop sequence in `cleanup_expired_cache` in `_cache_lock` to prevent `RuntimeError: dictionary changed size during iteration`. Cache count and size captured inside the lock; logging calls happen outside to minimize hold time.
  - Created `tests/test_utils.py` (6 tests): cache hit, absent miss, expired miss, overwrite, cleanup correctness, and a concurrent-write-plus-cleanup stress test with 6 threads.
- Deviations and why: none.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: 74 passed (6 new tests in `test_utils.py`).
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (black auto-reformatted `utils.py` on first run; re-run confirmed clean).
- Forward guidance:
  - WP-3 (CSRF protection for mutating POST routes) is the next work package.
  - `_cache_lock` is importable from `scrobblescope.utils` if future tests or modules need to inspect or clear the cache safely.

### 2026-02-19 - Batch 9 WP-1 completed (bound background job concurrency)
- Scope: `scrobblescope/config.py`, `scrobblescope/repositories.py`, `scrobblescope/routes.py`, `scrobblescope/orchestrator.py`, `tests/test_routes.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Added `MAX_ACTIVE_JOBS = int(os.getenv("MAX_ACTIVE_JOBS", "10"))` to `config.py`.
  - Added `_active_jobs_semaphore = threading.BoundedSemaphore(MAX_ACTIVE_JOBS)` to `repositories.py`.
  - Added `acquire_job_slot()` (non-blocking acquire, returns bool) and `release_job_slot()` (safe release with over-release guard) to `repositories.py`.
  - In `routes.py` `results_loading`: capacity check runs after `cleanup_expired_jobs()` and before `create_job()`; if at capacity, re-renders `index.html` with a retryable error message (no thread spawned, no job created).
  - In `orchestrator.py` `background_task`: `release_job_slot()` called in the `finally` block after `loop.close()`, guaranteeing release on all termination paths (success, handled exception, unhandled exception).
- Deviations and why:
  - Default of 10 (not lower) chosen to match existing concurrency constants and be tunable via `MAX_ACTIVE_JOBS` env var without code changes.
  - Capacity rejection renders `index.html` (same as other input validation errors) rather than a JSON 503, keeping the UX flow consistent with the existing form-submission error pattern.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: 68 passed (2 new tests added: capacity-rejection route test + release-on-exception orchestrator test).
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8, trim, end-of-file).
- Forward guidance:
  - WP-2 (make `REQUEST_CACHE` thread-safe) is the next work package.
  - The `_active_jobs_semaphore` is process-global; it resets on restart. Under Fly.io single-VM deployment this is correct behavior.
  - If the operator wants to verify slot release under real traffic, check logs for `release_job_slot called with no matching acquire` warning (should never appear in normal operation).

<!-- DOCSYNC:CURRENT-BATCH-END -->
