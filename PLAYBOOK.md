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
- Test suite: **110 tests** across 9 files (`test_app_factory.py`, `test_domain.py`, `test_repositories.py`, `test_utils.py`, `test_routes.py`, `tests/services/test_lastfm_service.py`, `tests/services/test_lastfm_logic.py`, `tests/services/test_spotify_service.py`, `tests/services/test_orchestrator_service.py`) covering job lifecycle, routes (including unmatched_view + 404/500 handlers + CSRF enforcement on all 4 POST routes + registration-year validation), normalization (including non-Latin character preservation and artist-name integrity), error classification, template safety, background task structure, reset flow, async service retry paths, DB helpers, cache integration, orchestrator correctness, DB connect retry/backoff behavior, thread-safe cache operations, concurrency slot lifecycle, app-factory secret-key startup guard, and fetch_top_albums_async aggregation/filter/timestamp logic.
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

### ~~Batch 9: Audit remediation execution (WP-1 through WP-8)~~
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
- ~~Batch 9~~: Done

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
- **Batch 10 is complete** (Gemini audit remediation -- non-normalization track,
  extended with Gemini 3.1 Pro P0/P1 audit remediation).
  - WP-1 (Medium): Eager slice for playcount sort before Spotify calls. Done.
  - WP-2 (Low-Medium): DB stale row cleanup (_cleanup_stale_metadata). Done.
  - WP-3 (Low): Consolidate duplicate filter-text translation in routes.py. Done.
  - WP-4 (Low): Extract ERROR_CODES + SpotifyUnavailableError to errors.py. Done.
  - WP-5: Sycophantic test coverage audit. Done. (5 findings: 4 strengthened, 1
    removed. 113 tests passing. See
    `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md`.)
  - WP-6: SoC and duplication audit of routes.py. Done. (4 helpers extracted,
    3 adversarial tests added. 116 tests passing. See
    `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md`.)
  - WP-7: Fix cross-job rate limiting. Done. (_GlobalThrottle + _ThrottledLimiter
    added to utils.py; 2 adversarial tests. 118 tests passing.)
  - WP-8: Fix destructive pre-slice with release_scope != "all". Done. (Gate
    condition tightened; existing test corrected; adversarial test added.
    119 tests passing.)
  - WP-9: Add defensive playtime album cap. Done. (_PLAYTIME_ALBUM_CAP=500 in
    orchestrator.py; warning log on trigger; 2 tests. 121 tests passing.)
- **Batch 11 is not yet defined.** Scope will be set after a third-party audit
  informs findings. The expected focus is ongoing code quality:
  - SoC concerns: front-end JS and back-end route/service layer violations.
  - DRY violations: repeated logic across templates, JS, and Python modules.
  - Data integrity: edge cases in aggregation, filtering, and normalization paths.
  - Logic flaws: silent failure modes, incorrect assumptions, off-by-one errors.
  - Performance bottlenecks: profile hot paths under realistic scrobble loads.
  - General best-practices fixes surfaced by static analysis or audit tooling.
  Batch 11 work packages will be defined when the audit findings are available.
  Do not start implementation until the owner assigns a batch number and scope.
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days (Last.fm-only, lighter background task).
- Do not start feature work (top songs, heatmap) until owner defines scope and assigns a batch number.


## 10. Batch execution log (for agent handoff)
Source-of-truth note:
- For current status, prefer Section 2 and this execution log.
- Keep only the active window here: current batch entries plus the latest 4 non-current operational logs.
- Older dated entries live in `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

### How to read dated entries
- Each heading in the form `YYYY-MM-DD - Batch X ...` is a historical completion/addendum log.
- Active-window policy: this section keeps current-batch logs (inside the CURRENT-BATCH markers) and only 4 non-current historical logs. Between batches the current-batch block may be empty.
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

### 2026-02-21 - fix: Gemini 3.1 Pro P0/P1 audit remediation (Batch 10 WP-7, WP-8, WP-9)

- Scope: `scrobblescope/utils.py`, `scrobblescope/orchestrator.py`,
  `tests/test_utils.py`, `tests/services/test_orchestrator_service.py`.
- Problem: Three confirmed findings from a Gemini 3.1 Pro audit pass:
  WP-7 -- Per-loop AsyncLimiter design meant each background job (which
  creates its own asyncio event loop) got an independent rate limiter.
  With MAX_ACTIVE_JOBS=10, aggregate throughput could reach 10x the
  configured API rate cap, risking 429s or IP bans.
  WP-8 -- The playcount pre-slice fired before process_albums applied
  the release-year filter. With release_scope != "all", albums outside
  the raw top-N could be the only ones matching the filter; discarding
  them early silently returned fewer results with no warning to the user.
  WP-9 -- No upper bound on filtered_albums for playtime sort. Pre-slicing
  is impossible (ranking requires Spotify track durations), but an extreme
  outlier with 2000+ qualifying albums would force proportional Spotify API
  load with no safety valve.
- Plan vs implementation: all three implemented as one commit each, tests
  first per AGENTS.md adversarial rule. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **121 passed** (116 baseline + 5 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed on every commit.
  - WP-7: _GlobalThrottle.next_wait() serialization test + cross-thread
    identity test confirm the shared throttle is in place.
  - WP-8: adversarial test confirms all 5 albums reach process_albums when
    release_scope="same" and limit_results="2".
  - WP-9: cap fires + warning logged test + below-threshold no-op test.
- Forward guidance: Batch 10 is now complete (WP-1 through WP-9). Batch 11
  is not yet defined. Feature work (top songs, heatmap) and further audit
  work require owner scope definition before implementation begins.
  _PLAYTIME_ALBUM_CAP=500 is conservative; monitor "Playtime album cap
  applied" warnings in production logs to tune if needed.

### 2026-02-21 - refactor/test: routes.py SoC and duplication audit (Batch 10 WP-6)

- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`,
  `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md` (new doc).
- Problem: Four SoC and duplication issues identified in `routes.py`:
  R1 -- two identical inner async wrappers for `check_user_exists` in
  `validate_user()` and `results_loading()`. R2 -- eight-field job params
  extraction duplicated verbatim in `results_complete()` and
  `unmatched_view()`. R3 -- reason-grouping data transform (group-by loop
  + count dict) embedded in `unmatched_view()`. R4 -- zero-playtime filter
  business rule (list comprehension) embedded in `results_complete()`.
  Follow-up: route-level tests only exercised happy paths for two of the
  new helpers; the playtime filter rule never fired in any test and the
  "Unknown reason" fallback was untested.
- Plan vs implementation: all four findings implemented as separate commits
  (R1-R4), then three adversarial unit tests added in a fifth commit.
  No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **116 passed** (113 pre-existing + 3 adversarial tests).
  - `pre-commit run --all-files`: all 8 hooks passed on every commit.
  - No behavior changes. Pure structural refactors + targeted tests.
- Forward guidance: Batch 10 is complete. Batch 11 is not yet defined.
  Feature work (top songs, heatmap) requires owner scope definition before
  implementation begins. No production risk introduced.

### 2026-02-21 - test: sycophantic test coverage audit (Batch 10 WP-5)

- Scope: `tests/test_routes.py`, `tests/services/test_orchestrator_service.py`,
  `tests/test_app_factory.py`, `tests/test_repositories.py`,
  `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md` (new doc).
- Problem: A Gemini 2.5 Pro audit of the 94-test baseline characterised the suite
  as "sycophantic" -- three structural patterns: assumption mirroring (tests use
  the same data shortcuts as production code), circular mocking (orchestrator tests
  return perfect fixture data and confirm perfect results), and interface-only
  validation (route tests patch start_job_thread so background state is never
  verified). Review of the current 114-test suite identified five specific instances:
  1. `test_results_loading_thread_start_failure_renders_error`: patched delete_job
     and only called assert_called_once() -- no arg check, no JOBS state check.
  2. `test_fetch_and_process_cache_hit_does_not_precheck_spotify`: only asserted
     on return value; background_task reads job state not return value, so the
     critical set_job_results side-effect was unchecked.
  3. `test_succeeds_with_strong_key_in_dev_mode`: near-duplicate of the production
     strong-key test; zero unique regression protection.
  4. `test_cleanup_stale_metadata_nonfatal`: no assertion at all.
  5. `test_delete_job_on_missing_job_is_noop`: no assertion at all.
- Plan vs implementation: all five fixed as described in
  `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **113 passed** (114 - 1 removed duplicate).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - No production code changes. Test-only commit.
- Forward guidance: next sub-track is SoC and duplication audit of routes.py.
  The suite-level "circular mocking" concern (no integration layer between
  fetch_top_albums_async aggregation and orchestrator processing) is a valid
  observation but out of scope for this task -- it would require new integration
  tests, not quality fixes to existing ones. Document as a known gap.

### 2026-02-21 - refactor/fix: Gemini audit remediation (non-normalization track)

- Scope: `scrobblescope/orchestrator.py`, `scrobblescope/cache.py`,
  `scrobblescope/routes.py`, `scrobblescope/domain.py`,
  new `scrobblescope/errors.py`, `scrobblescope/repositories.py`,
  `tests/services/test_orchestrator_service.py` (+4 tests),
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md` (new doc).
- Problem: A second Gemini Pro audit pass identified four issues beyond the previously
  fixed normalization bugs. Three were confirmed real against the live codebase:
  1. Late slicing: `limit_results` applied after Spotify calls in `_fetch_and_process`.
     For playcount sort the ranking is fully known from Last.fm data; pre-slicing
     to the requested limit eliminates unnecessary Spotify searches on cache misses.
     (Playtime sort cannot be pre-sliced -- ranking requires track duration data.)
  2. Indefinite DB growth: `_batch_lookup_metadata` filtered stale rows at read time
     but no DELETE ever ran. Stale rows accumulated in `spotify_cache` indefinitely.
  3. ERROR_CODES + SpotifyUnavailableError in `domain.py`: a SoC violation -- domain
     logic should not own user-facing message strings or retryability flags.
  A fourth SoC issue not in the original report was also fixed: duplicate release_scope
  -> human-text translation in `routes.py` (inline block in `unmatched_view`
  duplicating `get_filter_description`). A fifth issue (empty-result hallucination)
  was assessed and deferred as near-false-alarm -- the trigger conditions require
  zero cache hits AND every album absent from Spotify, which is extremely unlikely.
- Plan vs implementation: all four confirmed issues fixed as described in
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **114 passed** (110 pre-existing + 4 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - Import graph: `errors.py` is a leaf module (no package imports). Acyclic structure
    preserved. `domain.py` now contains only normalization logic.
- Forward guidance: next sub-track is "sycophantic test coverage" audit (owner to
  elaborate scope). Feature work (top songs, heatmap) blocked until owner assigns a
  future batch number and defines scope. `_cleanup_stale_metadata` is opportunistic and non-fatal;
  monitor logs for "Stale cache cleanup" entries to confirm it fires in production.
  The playtime late-slicing limitation is documented inline in `_fetch_and_process`.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-02-21 - fix(domain): fix normalization bugs silently excluding non-Latin albums

- Scope: `scrobblescope/domain.py`, `tests/test_domain.py` (9 new tests),
  `tests/services/test_lastfm_logic.py` (new file, 7 tests),
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md` (new doc).
- Problem: A third-party static analysis review (Gemini Pro) identified four
  defects in `domain.py` and a coverage gap in `lastfm.py`. All four were
  confirmed against the live codebase and three had measurable production impact:
  1. `normalize_track_name` used `NFKD + encode("ascii","ignore")`, stripping all
     non-Latin characters to `""`. Any album with Japanese/Cyrillic/etc. track names
     had `len(track_counts) == 1` regardless of distinct tracks played, silently
     failing the `min_tracks` filter and disappearing from results without an
     unmatched entry or any log warning.
  2. `normalize_name` applied its `album_metadata_words` set to the artist string as
     well as the album string, corrupting proper nouns like "New Edition" -> "new"
     and reducing artists named "Special", "Bonus", or "EP" to an empty string.
     Two artists with all-metadata-word names could collide on the same dict key.
  3. `normalize_track_name` used a 13-character hardcoded list while `normalize_name`
     used `str.maketrans(string.punctuation, ...)` covering all 32 ASCII punctuation
     characters. Characters like `&` were inconsistently handled.
  4. `fetch_top_albums_async` (aggregation, timestamp filtering, min_plays/min_tracks)
     had zero test coverage despite being the core business logic function.
- Plan vs implementation: all four defects addressed as described in
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md`. No scope additions or removals.
- Deviations: none.
- Validation:
  - `pytest -q`: **110 passed** (94 pre-existing + 9 new domain tests + 7 new logic tests).
  - `pre-commit run --all-files`: all hooks passed (black reformatted test_domain.py
    on first pass; clean on second).
  - Owner live test: Japanese-title 2025 album (betcover!!) now appears in results
    for listening year 2025 with "Same as release year" filter. Previously absent with
    no unmatched entry. Second validation: same artist's 2021 album (10 unique tracks,
    68 plays) also appeared correctly.
  - "New Edition" self-titled album test: artist key now "new edition" (not "new");
    album deduplication with "(Deluxe Edition)" suffix confirmed still working.
- Forward guidance: no schema, API contract, or route changes. No migration needed.
  The new `test_lastfm_logic.py` file should be extended if `fetch_top_albums_async`
  logic changes (e.g., top-songs feature). Pre-Batch-10 housekeeping is ongoing;
  Batch 10 scope remains TBD by owner.
