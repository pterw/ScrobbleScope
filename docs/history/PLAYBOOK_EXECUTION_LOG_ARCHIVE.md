# PLAYBOOK Execution Log Archive

Purpose:
- Store dated execution-log entries rotated out of `PLAYBOOK.md` section 10.
- Keep entries in reverse-chronological order (newest first).

Read helpers:
- `Get-Content docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "<keyword>" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

### 2026-02-20 - worker.py architectural decision + product roadmap + CSRF coverage expansion

- Scope: Documentation updates only (`.claude/SESSION_CONTEXT.md`, `EXECUTION_PLAYBOOK_2026-02-11.md`). No runtime code changes yet.
- Decisions made:
  - **Product roadmap confirmed:** Two additional background task types are planned -- "top songs" (Last.fm + possibly Spotify, separate background task/results flow) and "listening heatmap" (Last.fm only, last 365 days, lighter task). This means the `results_loading` acquire->Thread->release pattern will be needed by at least 3 routes.
  - **worker.py chosen as home for concurrency lifecycle:** With multiple background task types incoming, keeping the semaphore and thread-start boilerplate in `repositories.py` would require each new route to duplicate the `acquire -> try Thread.start -> except release` block. A new `scrobblescope/worker.py` leaf module (imports `config` only) will own `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread(target, args=())`. `repositories.py` becomes pure job state CRUD. `start_job_thread()` encapsulates the full try/start/except/release pattern for all callers.
  - **Refactor must precede the 3-commit save-state:** WP-1 originally placed the semaphore in `repositories.py`. The worker.py refactor corrects this before committing; the WP-1 commit will reflect the final architecture.
- CSRF test coverage expansion (also completed this session, before context compaction):
  - Initial WP-3 implementation added 2 CSRF tests covering only `/results_loading`.
  - Expanded to 6 total CSRF tests covering all 4 POST routes:
    - `test_csrf_rejects_post_without_token` (-> `/results_loading` 400)
    - `test_csrf_accepts_post_with_valid_token` (-> `/results_loading` 200)
    - `test_csrf_rejects_results_complete_without_token` (-> 400)
    - `test_csrf_rejects_unmatched_view_without_token` (-> 400)
    - `test_csrf_rejects_reset_progress_without_token` (-> 400)
    - `test_csrf_accepts_reset_progress_with_header_token` (-> `/reset_progress` XHR path with `X-CSRFToken` header, 200)
  - Total tests after expansion: **81 passing**.
- Pending implementation (next agent actions in order):
  1. Create `scrobblescope/worker.py` with semaphore, `acquire_job_slot()`, `release_job_slot()`, `start_job_thread()`.
  2. Remove semaphore/slot functions from `scrobblescope/repositories.py`.
  3. Update imports in `routes.py` and `orchestrator.py` to use `worker`.
  4. Update patch targets in `test_routes.py` and `test_orchestrator_service.py` from `scrobblescope.routes.acquire_job_slot` / `scrobblescope.orchestrator.release_job_slot` -> `scrobblescope.worker.*`.
  5. Run `pre-commit run --all-files` and `pytest -q` (must stay at 81 passing).
  6. Make 3 separate commits: WP-1, WP-2, WP-3.
- Validation: N/A (doc-only session-end update).
- Forward guidance:
  - worker.py is a leaf module -- it must NOT import from `repositories`, `routes`, `orchestrator`, or any higher module (would create cycles).
  - `start_job_thread()` should release the slot and raise on `Thread.start()` failure so routes get a clean exception to handle (mirrors the current try/except pattern in `routes.py`).
  - After the 3 commits are made, next work package is WP-4 (harden app secret and startup safety).

### 2026-02-14 - Frontend responsiveness polish completed (toggle placement + mobile table scaling)
- Scope: `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`, `static/css/unmatched.css`, `static/css/error.css`, `templates/results.html`.
- Plan vs implementation:
  - Standardized dark-mode toggle to a compact fixed bottom control across all page CSS bundles.
  - Improved `index.html` mobile fit by tightening spacing, typography, and card/logo sizing at mobile breakpoints.
  - Improved `results.html` mobile readability by shrinking table density, making actions stack cleanly, and reducing album-art footprint.
  - Added `results-table` class in template for targeted responsive behavior.
  - Centered decade pills in `index` filter UI.
- Deviations and why:
  - To improve fit on common phones, responsive rules were applied up to `max-width: 767.98px` for index/results rather than only `575.98px`.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - If users still report table crowding on very small devices, next step is card-style row rendering for results instead of a dense 5-column table.
  - Consider extracting shared toggle CSS into one common stylesheet to reduce cross-file duplication.

### 2026-02-14 - Post-Batch-8 hardening completed (low-severity gap closure + test layout split)
- Scope: `tests/test_routes.py`, `tests/conftest.py`, `tests/helpers.py` (new), `tests/services/` (new split files), `EXECUTION_PLAYBOOK_2026-02-11.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Closed previously identified low-severity gaps:
    - Added direct route tests for `/unmatched_view` (missing `job_id`, missing job, success render path).
    - Added explicit tests for app-level 404 and 500 handlers.
  - Reduced test coupling to `conftest.py` internals:
    - Moved shared constants/mock helpers into `tests/helpers.py`.
    - Updated tests to import from `tests.helpers` rather than `conftest`.
  - Split monolithic service test file:
    - Removed `tests/test_services.py`.
    - Added `tests/services/test_lastfm_service.py` (4 tests).
    - Added `tests/services/test_spotify_service.py` (3 tests).
    - Added `tests/services/test_orchestrator_service.py` (10 tests).
- Deviations and why:
  - No runtime code changes were required. This was a test architecture and coverage hardening pass only.
  - Added one extra test category beyond the initial gap list (500 handler integration path) because this was explicitly untested and low effort/high confidence.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **64 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - Subpackage migration should be sequenced **after** the next feature-heavy batch set (Batch 9+) stabilizes, not before. Keep current flat module layout while churn is high; cut to subpackages once contracts settle.
  - Keep route-handler coverage and helper-module pattern as baseline for future test additions.

### 2026-02-13 - Batch 8 completed (modular refactor -- app factory + blueprints + layered structure)
- Scope: `app.py` (rewritten), `scrobblescope/` package (9 new modules), `tests/` (4 test files + conftest replacing monolithic `test_app.py`).
- Plan vs implementation:
  - Followed the approved 7-slice strangler plan exactly. All 59 tests remained green after every slice.
  - Slice 1: `config.py` + `domain.py` + `conftest.py` + `test_domain.py` (6 tests)
  - Slice 2: `utils.py` (rate limiters, session, caching, helpers)
  - Slice 3: `repositories.py` + `cache.py` + `test_repositories.py` (14 tests)
  - Slice 4: `lastfm.py` + `spotify.py` + partial `test_services.py` (7 tests)
  - Slice 5: `orchestrator.py` + remaining `test_services.py` (10 more tests, 17 total)
  - Slice 6: `routes.py` (Blueprint) + `test_routes.py` (22 tests) + `app.py` factory rewrite
  - Slice 7: Cleanup and documentation updates
- Deviations and why:
  - Plan estimated 19 tests in `test_services.py` and 20 in `test_routes.py`; actual counts are 17 and 22 respectively (same 59 total). Two tests moved between files for better logical grouping.
  - `create_app()` lives in `app.py` (project root) rather than `scrobblescope/__init__.py` -- keeps Flask template/static path resolution simple and `gunicorn app:app` backward compatible.
- Key architectural outcomes:
  - `app.py` reduced from ~2091 lines to ~91 lines (factory pattern only).
  - Acyclic dependency graph: `domain`/`config` -> `utils` -> `cache` -> `repositories` -> `lastfm`/`spotify` -> `orchestrator` -> `routes` -> `app`.
  - No circular imports. Each module imports only from modules above it in the hierarchy.
  - Flask Blueprint (`bp = Blueprint("main", __name__)`) with `@bp.app_errorhandler` for 404/500 and `@bp.app_context_processor` for template injection.
  - `# noqa: F401` re-export pattern used during transitional slices, fully removed in Slice 6.
  - Patch targets updated throughout: `"app.X"` -> `"scrobblescope.<module>.X"` in all test files.
- Validation:
  - `pytest tests/ -q`: 59 passed (6 + 14 + 17 + 22 across 4 test files)
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8)
  - `python -c "from app import app; print(app)"`: Gunicorn import verified
  - Dockerfile (`gunicorn app:app`) and fly.toml (`release_command = "python init_db.py"`) unchanged and compatible
- Forward guidance:
  - All batches (1-8) are complete. No further structural refactor is planned.
  - Deployment: `app.py` factory + module-level `app = create_app()` is backward compatible with `gunicorn app:app`.
  - Test convention: patch at the module where the name is looked up (e.g., `"scrobblescope.orchestrator._get_db_connection"`).
  - Adding new routes: add to `scrobblescope/routes.py` using `@bp.route(...)`.
  - Adding new service functions: add to the appropriate module (`lastfm.py`, `spotify.py`, `orchestrator.py`, etc.).

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
  - Initial smoke run (pre-deploy) was inconclusive (`cache_hits=0` both runs) because Fly was still running Batch 6 code. Root cause resolved by deploying with Postgres attached.
- Validation performed:
  - `pytest -q`: 59 passed.
  - `pre-commit run --all-files`: all hooks passed.
  - **Post-deploy smoke test (PASS):**
    - Postgres provisioned: `scrobblescope-db` (unmanaged, yyz region)
    - Attached via `fly postgres attach scrobblescope-db --app scrobblescope` (auto-set `DATABASE_URL`)
    - `python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`:
      - Run 1 (cold): 41.84s, `cache_hits=0`, `db_cache_persisted=243`, `spotify_matched=243`
      - Run 2 (warm): 4.34s, `cache_hits=243`, `db_cache_lookup_hits=243`, `db_cache_persisted=3`
      - **~10x speedup on warm cache. Verdict: PASS.**
  - New tests added:
    - `process_albums` all-miss token failure raises classified exception.
    - `process_albums` partial cache hit + token failure returns cached subset and warning stat.
    - `_fetch_and_process` no longer directly pre-checks Spotify token.
    - `_fetch_and_process` maps `SpotifyUnavailableError` to `spotify_unavailable` job error.
- Forward guidance for next agent:
  - Cache is deployed and verified. No further infra steps needed before Batch 8.
  - Fly Postgres instance `scrobblescope-db` is unmanaged, single-node. Consider auto-stop to save cost when idle.
  - Keep Batch 8 refactor parity tests for the error/warning paths (`SpotifyUnavailableError`, `partial_data_warning`) before moving orchestration into service modules.
  - Local dev has no `DATABASE_URL` -- cache is disabled locally (by design). All cache behavior is tested via mocks in the test suite.

### 2026-02-13 - Operational config fix (Fly machine autostop)
- Scope: `fly.toml`.
- Issue:
  - Fly log showed autostop with `0 out of 1 machines left running` because `min_machines_running` was set to `0`.
- Change:
  - Updated `[http_service] min_machines_running = 1` to keep one machine warm.
- Notes:
  - This log means capacity scaling, not cache overflow.
  - In-memory caches (`REQUEST_CACHE`, `JOBS`) live in RAM on the app VM and are lost on machine stop/restart.
  - Persistent Spotify metadata cache lives in Fly Postgres (`spotify_cache`) via `DATABASE_URL`.

### 2026-02-12 - Batch 7 completed (persistent Spotify metadata cache -- Postgres via asyncpg)
- Scope: `requirements.txt`, `.env.example`, `init_db.py` (new), `fly.toml`, `app.py`, `tests/test_app.py`.
- Implementation:
  - **requirements.txt:** Added `asyncpg>=0.29.0`; removed unused `redis` and `Flask_Caching`.
  - **.env.example:** Added `DATABASE_URL` placeholder with Fly.io context comment.
  - **init_db.py (new):** Standalone schema init script. Reads `DATABASE_URL`, creates `spotify_cache` table via `asyncpg`. Runs as Fly `release_command`. Idempotent; exits 0 on success or no-op, exits 1 on failure (rolls back deploy).
  - **fly.toml:** Added `[deploy] release_command = "python init_db.py"`.
  - **app.py -- 3 new helper functions:**
    - `_get_db_connection()`: Returns `asyncpg.Connection` or `None` (graceful fallback).
    - `_batch_lookup_metadata(conn, keys)`: Single SELECT with `unnest()`, 30-day TTL filter, JSONB deserialization.
    - `_batch_persist_metadata(conn, rows)`: Single INSERT with `unnest() ... ON CONFLICT DO UPDATE`. True single-statement batch (not executemany).
  - **app.py -- `process_albums` rewritten** with 5-phase flow:
    - Phase 1: DB batch lookup (try/except, fallback to empty dict).
    - Phase 2: Partition into cache_hits and cache_misses.
    - Phase 3: Spotify fetch for misses only (entire block guarded by `if cache_misses:` -- zero API calls on full cache hit).
    - Phase 4: DB batch persist + `conn.close()` in `finally`.
    - Phase 5: Build results from unified cache_hits dict -- identical output shape regardless of source.
  - **tests/test_app.py -- 12 new tests (43 -> 55):**
    - 7 DB helper unit tests: `_get_db_connection` (no asyncpg, no URL, connect failure), `_batch_lookup_metadata` (empty keys, JSONB parsing), `_batch_persist_metadata` (empty rows, upsert call shape).
    - 5 process_albums integration tests: full cache hit skips Spotify, full cache miss fetches and persists, DB unavailable falls back, conn always closed, empty input.
- Deviations:
  - Plan called for ~14 tests; implemented 12 (skipped init_db.py tests as the script is trivially simple and tested indirectly by the release_command pattern).
  - `METADATA_CACHE_TTL_DAYS` made configurable via env var (default 30) -- not in original plan but natural extension.
- Validation:
  - `pytest -q`: 55 passed
  - `pre-commit run --all-files`: all hooks passed
  - Local dev without `DATABASE_URL`: app functions identically to pre-Batch-7
- Notes:
  - Connection always closed via `finally` block, even on Spotify errors.
  - Full cache hit path: zero Spotify API calls (verified via mock assertions -- no token fetch, no session, no search).
  - Next batch is Batch 8 (modular refactor).

### 2026-02-12 - Batch 6 completed (frontend refinement/tweaks)
- Scope: Templates, CSS, JS, and tests -- no app.py changes.
- Implementation:
  - **index.html error alert:** Added `{% if error %}` block with Bootstrap `alert-danger` component above the form card. Errors from `results_loading` (missing username, bad year) now render visibly.
  - **Dark-mode toggle mobile fix:** Added `@media (max-width: 575.98px)` rules to all 5 CSS files (index, loading, results, unmatched, error) repositioning the toggle from `top: 1rem` to `bottom: 1rem` on small screens.
  - **Username submission guard:** Added `setCustomValidity()` to `index.js` so that a username flagged invalid by the AJAX blur check blocks native form submission. An `input` listener clears the block when the user types a new name. Network errors fall through to server-side validation.
  - **Encoding artifacts:** Investigated all JS files -- no artifacts found. `encodeURIComponent()`, `.textContent`, and `escapeHtml()` are used correctly. No action needed.
  - **Test enhancements:** Updated `test_results_loading_missing_username` and `test_results_loading_year_out_of_bounds` to assert error message text is present in the response, confirming the alert block renders.
- Deviations: Username submission guard was not in the original playbook scope but was a clear UX gap identified during Batch 6 work.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed
- Notes:
  - No new tests added (existing tests enhanced with assertions).
  - Next batch is Batch 7 (persistent metadata layer).

### 2026-02-12 - Batch 5 completed (docstring + comment normalization)
- Scope: `app.py` only -- docstrings and comments; no behavior changes.
- Implementation:
  - **Added docstrings to 16 previously undocumented top-level functions:**
    `_get_loop_limiter`, `run_async_in_thread`, `inject_current_year`,
    `_initial_progress`, `cleanup_expired_jobs`, `create_job`, `set_job_progress`,
    `set_job_stat`, `set_job_results`, `add_job_unmatched`, `reset_job_state`,
    `get_job_progress`, `get_job_unmatched`, `get_job_context`,
    `fetch_recent_tracks_page_async`, `fetch_spotify_access_token`, `results_complete`.
  - **Removed 11 redundant or stale pre-function comments** that duplicated what the docstring already says or used stale language ("improved", "update the ... route").
  - **Relocated one misleading comment** ("Enable ANSI escape codes on Windows cmd") from the `import sys` line to the actual `os.system("")` call where the enabling happens.
  - **Docstring style:** short summary line, optional detail paragraph -- consistent with `get_spotify_limiter` as the reference standard.
  - **Inner/nested functions** (11 closures like `fetch_once`, `clean`, `search_with_semaphore`) were intentionally left without docstrings as they are self-descriptive from naming and parent function context.
- Deviations: None.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed (isort auto-fixed import grouping after comment removal; re-run confirmed clean)
- Notes:
  - `app.py` line count decreased slightly due to comment removal (~1800 -> ~1790).
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
- Scope: `tests/test_app.py` only -- 23 new tests added (12 -> 35 total).
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
  - No changes to `app.py` or any other file -- tests-only batch.
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
