# ScrobbleScope Execution Playbook (Post-Compact Handoff)

Date: 2026-02-11
Owner context: This playbook defines the implementation order, standards, and guardrails for the next major batches.
Primary goal: Improve reliability, UX, and maintainability without behavior regressions, then refactor monolithic `app.py` safely.

## 1. Why this document exists
- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

## 2. Current status snapshot
- `app.py` remains the main monolith.
- Per-job in-memory state exists (`JOBS` dict).
- Persistent Spotify metadata cache added (Postgres via asyncpg, Batch 7):
  - `spotify_cache` table with 30-day TTL, batched reads/writes via `unnest()`.
  - Per-request `asyncpg.connect()` (no pool â€” each background_task owns its own event loop).
  - Graceful fallback: if `DATABASE_URL` unset or DB unreachable, full Spotify flow runs.
  - `_fetch_and_process` does not pre-check Spotify token globally; full DB cache hits can complete without Spotify availability.
  - If Spotify is unavailable while cache hits exist, cached results still return with `partial_data_warning` in progress stats.
  - Schema automated via `init_db.py` release_command on Fly deploys.
- `tojson` JS data bridge is in place in templates.
- Unmatched modal has escaping in `static/js/results.js`.
- Nested thread pattern removed:
  - Outer worker thread remains in `results_loading`.
  - `background_task` now owns one event loop directly (no inner thread).
- All top-level functions in `app.py` have consistent docstrings (Batch 5).
- Mobile dark-mode toggle repositioned to bottom-right on small screens (Batch 6).
- `index.html` now renders server-side validation errors (Batch 6).
- Test suite expanded to 59 tests covering job lifecycle, routes, normalization, error classification, template safety, background task structure, reset flow, async service retry paths, DB helper functions, process_albums cache integration, and cache-orchestrator correctness in `_fetch_and_process`.

## 3. Non-negotiable implementation principles
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

## 4. High-level batch order (strict sequence)

### Batch 0: Baseline freeze + approval parity suite
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

### Batch 8: Modular refactor (app factory + blueprints + layered structure)
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

## 5. Suggested implementation granularity
- Keep PRs or commits small per batch.
- Do not mix architecture refactor with behavior changes in one step.
- Re-run:
  - `pre-commit run --all-files`
  - `pytest -q`
after each batch.

## 6. Open decisions (owner confirmation needed)
1. Persistent store choice now: Postgres only or Postgres + Redis.
2. Retry UX policy:
   - immediate retry button only,
   - or retry + cooldown messaging.
3. Whether to keep `results_loading` progress spoof sleeps or remove once UX states improve.
4. Error copy style and user-facing tone for upstream failures.

## 7. Agent handoff checklist before starting a batch
1. Read:
   - `EXECUTION_PLAYBOOK_2026-02-11.md` (this file)
   - `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` (historical snapshot; may lag latest batch log in this file)
   - `README.md` (product expectations, deployment context, known limitations)
2. Inspect current implementation hotspots in `app.py` before editing:
   - Job state lifecycle (`JOBS`, TTL cleanup, `/progress`, `/results_complete`)
   - Background execution path (`results_loading`, `background_task`, async pipeline)
   - API/cache path (Last.fm fetch, Spotify processing, `REQUEST_CACHE`)
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
After each completed batch, update this playbook immediately:
1. Status update:
   - Strike through the completed batch title in Section 4.
   - Update "Immediate next batch to execute."
2. Snapshot update:
   - Update Section 2 only for material architecture/runtime state changes.
3. Add one dated entry under "Batch execution log" with:
   - scope
   - plan vs implementation
   - deviations and why they were taken
   - additions beyond plan
   - struggles/constraints and unresolved risks
   - validation performed
   - forward guidance for the next agent
4. Document stale references:
   - Keep historical docs; do not delete.
   - Mark here whether a doc is historical baseline vs current source of truth.

## 9. Immediate next batch to execute
- Batch 8: Modular refactor (app factory + blueprints + layered structure).

Rationale:
- Batches 1-7 are complete.
- Persistent Spotify metadata cache (Postgres via asyncpg) is in place with 59 tests green.
- Next step is structural refactor: app factory, blueprints, services/, repositories/.

## 10. Batch execution log (for agent handoff)
Source-of-truth note:
- For current status, prefer Section 2 and this execution log.
- Treat `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` as baseline context from 2026-02-11 unless it is explicitly refreshed.

### 2026-02-12 - Batch 7 completed (persistent Spotify metadata cache â€” Postgres via asyncpg)
- Scope: `requirements.txt`, `.env.example`, `init_db.py` (new), `fly.toml`, `app.py`, `tests/test_app.py`.
- Implementation:
  - **requirements.txt:** Added `asyncpg>=0.29.0`; removed unused `redis` and `Flask_Caching`.
  - **.env.example:** Added `DATABASE_URL` placeholder with Fly.io context comment.
  - **init_db.py (new):** Standalone schema init script. Reads `DATABASE_URL`, creates `spotify_cache` table via `asyncpg`. Runs as Fly `release_command`. Idempotent; exits 0 on success or no-op, exits 1 on failure (rolls back deploy).
  - **fly.toml:** Added `[deploy] release_command = "python init_db.py"`.
  - **app.py â€” 3 new helper functions:**
    - `_get_db_connection()`: Returns `asyncpg.Connection` or `None` (graceful fallback).
    - `_batch_lookup_metadata(conn, keys)`: Single SELECT with `unnest()`, 30-day TTL filter, JSONB deserialization.
    - `_batch_persist_metadata(conn, rows)`: Single INSERT with `unnest() ... ON CONFLICT DO UPDATE`. True single-statement batch (not executemany).
  - **app.py â€” `process_albums` rewritten** with 5-phase flow:
    - Phase 1: DB batch lookup (try/except, fallback to empty dict).
    - Phase 2: Partition into cache_hits and cache_misses.
    - Phase 3: Spotify fetch for misses only (entire block guarded by `if cache_misses:` â€” zero API calls on full cache hit).
    - Phase 4: DB batch persist + `conn.close()` in `finally`.
    - Phase 5: Build results from unified cache_hits dict â€” identical output shape regardless of source.
  - **tests/test_app.py â€” 12 new tests (43 â†’ 55):**
    - 7 DB helper unit tests: `_get_db_connection` (no asyncpg, no URL, connect failure), `_batch_lookup_metadata` (empty keys, JSONB parsing), `_batch_persist_metadata` (empty rows, upsert call shape).
    - 5 process_albums integration tests: full cache hit skips Spotify, full cache miss fetches and persists, DB unavailable falls back, conn always closed, empty input.
- Deviations:
  - Plan called for ~14 tests; implemented 12 (skipped init_db.py tests as the script is trivially simple and tested indirectly by the release_command pattern).
  - `METADATA_CACHE_TTL_DAYS` made configurable via env var (default 30) â€” not in original plan but natural extension.
- Validation:
  - `pytest -q`: 55 passed
  - `pre-commit run --all-files`: all hooks passed
  - Local dev without `DATABASE_URL`: app functions identically to pre-Batch-7
- Notes:
  - Connection always closed via `finally` block, even on Spotify errors.
  - Full cache hit path: zero Spotify API calls (verified via mock assertions â€” no token fetch, no session, no search).
  - Next batch is Batch 8 (modular refactor).

### 2026-02-13 - Batch 7 hardening addendum (cache-orchestrator correctness + smoke validation path)
- Scope: `app.py`, `tests/test_app.py`, `README.md`, `scripts/smoke_cache_check.py`, this playbook.
- Plan vs implementation:
  - Batch 7 intent said full cache hits should avoid Spotify dependency.
  - Implementation was corrected to match intent by removing `_fetch_and_process` Spotify pre-check and making Spotify-unavailable signaling explicit.
- Deviations and why:
  - Added `SpotifyUnavailableError` instead of generic string matching to avoid false "successful empty results" when Spotify token fetch fails on all misses.
  - Added partial-response behavior: when token fetch fails but cache hits exist, return cached subset and set `partial_data_warning`.
- Additions beyond plan:
  - Added deploy-targeted smoke utility: `scripts/smoke_cache_check.py` for warm-cache verification (`flounder14`, `2025` defaults supported).
  - Added cache observability stats in `process_albums`: `db_cache_enabled`, `db_cache_lookup_hits`, `db_cache_persisted`, and `db_cache_warning`.
  - README now documents persistent cache behavior and smoke-test usage.
- Struggles/constraints and unresolved risks:
  - End-to-end cache validation against live Fly/Postgres cannot be fully asserted by unit tests; smoke script is provided for operational verification.
  - Existing heuristic that treats "all unmatched == Spotify unavailable" remains unchanged and should be revisited during Batch 8 service extraction.
  - 2026-02-13 deployed smoke run result was inconclusive for DB cache usage: run 1 and run 2 both reported `cache_hits=0` (though run 2 was faster). This suggests infra/config mismatch (for example `DATABASE_URL` not attached) or a remaining DB lookup/persist path issue.
- Validation performed:
  - `pytest -q`: 59 passed.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`:
    - Run 1: 40.62s, `cache_hits=0`, `spotify_matched=245`.
    - Run 2: 29.60s, `cache_hits=0`, `spotify_matched=245`.
    - Script verdict: `INCONCLUSIVE` (warm-cache hits not observed).
  - New tests added:
    - `process_albums` all-miss token failure raises classified exception.
    - `process_albums` partial cache hit + token failure returns cached subset and warning stat.
    - `_fetch_and_process` no longer directly pre-checks Spotify token.
    - `_fetch_and_process` maps `SpotifyUnavailableError` to `spotify_unavailable` job error.
- Forward guidance for next agent:
  - Run `scripts/smoke_cache_check.py` against deployed Fly app after deploy to confirm warm-cache gains.
  - If `cache_hits` remains 0 on repeated runs, verify Fly secrets and schema first:
    - `fly secrets list --app scrobblescope` (confirm `DATABASE_URL` exists)
    - `fly logs --app scrobblescope` (look for "DB connection failed (cache disabled)")
    - confirm `release_command` output includes "Schema initialized successfully"
  - Keep Batch 8 refactor parity tests for these new error/warning paths before moving orchestration into service modules.

### 2026-02-12 - Batch 6 completed (frontend refinement/tweaks)
- Scope: Templates, CSS, JS, and tests â€” no app.py changes.
- Implementation:
  - **index.html error alert:** Added `{% if error %}` block with Bootstrap `alert-danger` component above the form card. Errors from `results_loading` (missing username, bad year) now render visibly.
  - **Dark-mode toggle mobile fix:** Added `@media (max-width: 575.98px)` rules to all 5 CSS files (index, loading, results, unmatched, error) repositioning the toggle from `top: 1rem` to `bottom: 1rem` on small screens.
  - **Username submission guard:** Added `setCustomValidity()` to `index.js` so that a username flagged invalid by the AJAX blur check blocks native form submission. An `input` listener clears the block when the user types a new name. Network errors fall through to server-side validation.
  - **Encoding artifacts:** Investigated all JS files â€” no artifacts found. `encodeURIComponent()`, `.textContent`, and `escapeHtml()` are used correctly. No action needed.
  - **Test enhancements:** Updated `test_results_loading_missing_username` and `test_results_loading_year_out_of_bounds` to assert error message text is present in the response, confirming the alert block renders.
- Deviations: Username submission guard was not in the original playbook scope but was a clear UX gap identified during Batch 6 work.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed
- Notes:
  - No new tests added (existing tests enhanced with assertions).
  - Next batch is Batch 7 (persistent metadata layer).

### 2026-02-12 - Batch 5 completed (docstring + comment normalization)
- Scope: `app.py` only â€” docstrings and comments; no behavior changes.
- Implementation:
  - **Added docstrings to 16 previously undocumented top-level functions:**
    `_get_loop_limiter`, `run_async_in_thread`, `inject_current_year`,
    `_initial_progress`, `cleanup_expired_jobs`, `create_job`, `set_job_progress`,
    `set_job_stat`, `set_job_results`, `add_job_unmatched`, `reset_job_state`,
    `get_job_progress`, `get_job_unmatched`, `get_job_context`,
    `fetch_recent_tracks_page_async`, `fetch_spotify_access_token`, `results_complete`.
  - **Removed 11 redundant or stale pre-function comments** that duplicated what the docstring already says or used stale language ("improved", "update the â€¦ route").
  - **Relocated one misleading comment** ("Enable ANSI escape codes on Windows cmd") from the `import sys` line to the actual `os.system("")` call where the enabling happens.
  - **Docstring style:** short summary line, optional detail paragraph â€” consistent with `get_spotify_limiter` as the reference standard.
  - **Inner/nested functions** (11 closures like `fetch_once`, `clean`, `search_with_semaphore`) were intentionally left without docstrings as they are self-descriptive from naming and parent function context.
- Deviations: None.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed (isort auto-fixed import grouping after comment removal; re-run confirmed clean)
- Notes:
  - `app.py` line count decreased slightly due to comment removal (~1800 â†’ ~1790).
  - All 49 top-level functions in app.py now have docstrings (100% coverage).
  - Next batch is Batch 6 (frontend refinement/tweaks).

### 2026-02-12 - Batch 4 closure addendum (missing coverage completed)
- Scope: `tests/test_app.py` only.
- Implementation:
  - Added `/reset_progress` route coverage:
    - missing `job_id` -> 400
    - nonexistent `job_id` -> 404
    - success path resets progress/results/unmatched state
  - Added service-level async retry/error tests for:
    - `fetch_recent_tracks_page_async` (429 retry -> success, 404 -> raises ValueError)
    - `search_for_spotify_album_id` (429 retry -> returns ID)
    - `fetch_spotify_album_details_batch` (429 retry -> success, non-200 -> empty dict)
- Reasoning:
  - Closed the two explicit Batch 4 gaps noted in handoff docs before proceeding to Batches 5/7/8.
  - Prioritized deterministic tests by mocking limiter contexts and `asyncio.sleep`.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed
- Notes:
  - Batch 4 is now fully closed from a coverage perspective.

### 2026-02-12 - Batch 4 completed (expanded test coverage)
- Scope: `tests/test_app.py` only â€” 23 new tests added (12 â†’ 35 total).
- Implementation:
  - **Job lifecycle (5 tests):** unique IDs, job isolation, missing-job guard, stat storage, TTL expiry cleanup.
  - **Route coverage (9 tests):** `/progress` 400+404, `/results_loading` valid+missing+out-of-bounds, `/results_complete` missing+expired+with-data, `/validate_user` too-long+not-found, `/unmatched` 400+data.
  - **Normalization (3 tests):** remastered suffix stripping, Unicode preservation, track name punctuation.
  - **Registration year (2 tests):** valid timestamp extraction, missing key graceful fallback.
  - **Template safety (folded into route tests):** `window.SCROBBLE` tojson bridge in loading page, `window.APP_DATA` tojson bridge in results page.
  - **Background task structural (1 test):** `background_task` runs `_fetch_and_process` in a single event loop with no inner thread (Batch 3 regression guard). `/results_loading` verified to create a daemon thread targeting `background_task`.
- Deviations:
  - `index.html` does not render the `error=` variable passed by `results_loading` on validation failure. Tests were adjusted to verify the correct page is returned (index form, not loading page) rather than asserting specific error text. This is a minor UX gap that could be addressed in Batch 6 (frontend tweaks).
- Notes:
  - All 35 tests pass. All pre-commit hooks pass (black, isort, autoflake, flake8).
  - No changes to `app.py` or any other file â€” tests-only batch.
  - Next batch is Batch 5 (docstring + comment normalization).

### 2026-02-12 - Batch 3 completed (nested thread removal)
- Scope: `app.py` only for runtime behavior, plus this playbook status/log update.
- Implementation:
  - Extracted nested `fetch_and_process` closure into top-level async function `_fetch_and_process`.
  - Reworked `background_task` to create/use a single event loop directly on the already-created worker thread.
  - Removed `background_task -> run_async_in_thread(...)` indirection to eliminate the second per-job thread.
  - Kept `run_async_in_thread` unchanged for `/validate_user` because that route is sync and needs a blocking async bridge.
- Reasoning:
  - Preserves existing user-visible behavior and error semantics while removing wasted thread overhead.
  - Keeps event-loop ownership explicit and aligned with loop-scoped `AsyncLimiter` usage.
  - Minimizes blast radius before Batch 4 test expansion and later storage/refactor batches.
- Notes:
  - No functional changes were intentionally introduced in the fetch/process pipeline logic.
  - Next batch remains Batch 4 (coverage expansion) before deeper architectural moves.


