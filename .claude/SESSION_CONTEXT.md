# ScrobbleScope Session Context (Post-Batch 8 Modular Refactor)

Last updated: 2026-02-20
Author: Claude Opus 4.6 + Codex + Claude Sonnet 4.6 (multi-agent orchestration)

---

## 1. What is ScrobbleScope?

A Flask web app that fetches a user's Last.fm scrobble history for a given year, enriches album data with Spotify metadata (release dates, artwork, track runtimes), and presents filtered/sorted top-album rankings. Primary use case: building Album of the Year (AOTY) lists.

**Confirmed upcoming features (owner roadmap):**
- **Top songs**: a parallel feature track that ranks a user's most-played tracks for a year (Last.fm + possibly Spotify enrichment). Separate background task type, separate loading/results flow.
- **Listening heatmap**: a calendar-style heatmap of scrobble density across the last 365 days. Last.fm API only (no Spotify), lighter-weight background task.

**Stack:** Python 3.13, Flask, aiohttp/aiolimiter (async API calls), Bootstrap 5, Jinja2 templates, pytest + pytest-asyncio.

**Deployment:** Fly.io (ephemeral VM, shared-cpu-2x @ 512MB). Postgres on Fly for persistent Spotify metadata cache (asyncpg). In-memory job state (`JOBS` dict).

---

## 2. Current state

| Item | Value |
|------|-------|
| Branch | `wip/pc-snapshot` |
| Latest commit | `14f251a` - docs: refresh README for Batch 9 completions and roadmap |
| Tests | **94 passing** across 8 test files |
| Coverage snapshot | **72%** (`pytest --cov=scrobblescope`, 2026-02-20 audit run) |
| Pre-commit | All hooks pass (black, isort, autoflake, flake8, doc-state-sync-check) |
| app.py line count | ~142 lines (factory + logging setup + CSRF init + secret-key guard) |
| Cache fallback logging | `_get_db_connection()` logs classified reasons: `asyncpg-missing`, `missing-env-var`, `db-down` |
| Deploy status | Cold-start validated on 2026-02-19 by manually stopping app+DB machines and running an end-to-end smoke request (`elapsed=18.75s`, `db_cache_enabled=True`, `db_cache_lookup_hits=247`). |
| Batch 9 status | **WP-1 through WP-6 complete**; WP-7 is next. See `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md` |
| Job concurrency cap | `MAX_ACTIVE_JOBS` (default 10, env-tunable). `acquire_job_slot()` / `release_job_slot()` / `start_job_thread()` in `scrobblescope/worker.py`. |
| Request cache thread safety | `_cache_lock = threading.Lock()` in `utils.py` guards all `REQUEST_CACHE` read/write/cleanup ops. |
| Known open risk | None open. Orphan job on thread-start failure closed 2026-02-20 (`delete_job` in repositories.py + routes.py). |

---

## 3. Documents to read (priority order)

| Document | Status | Purpose |
|----------|--------|---------|
| `PLAYBOOK.md` | **Source of truth** | Batch ordering, acceptance criteria, active execution log, next steps. |
| `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md` | **Active execution plan** | Work-package checklist for security/reliability/correctness remediations from the comprehensive audit. |
| `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` | **Historical execution log** | Older dated playbook entries rotated out of the active window. |
| `.claude/SESSION_CONTEXT.md` (this file) | **Current** | Quick orientation for agents. Architecture, key locations, known gaps. |
| `README.md` | **Current** | Product description, roadmap checklist, setup instructions. |
| `docs/history/` | **Historical archive** | Audits/changelogs/refactor notes kept out of repo root for hygiene. |

---

## 4. Execution status (derived from PLAYBOOK)

`PLAYBOOK.md` remains the source of truth. The block below is machine-managed by `scripts/doc_state_sync.py`.

<!-- DOCSYNC:STATUS-START -->
- Source of truth: `PLAYBOOK.md` (Section 9 and Section 10).
- Current batch: Batch 9.
- Current-batch entries in active log block: 13.
- Completed work packages in current-batch entries: WP-1, WP-2, WP-3, WP-4, WP-5, WP-6.
- Next expected work package: WP-7.
- Newest current-batch entry: 2026-02-20 - P1 refactor: extract VALID_FORM_DATA and csrf_app_client fixture.
- Rotated to archive in latest sync run: 0.
<!-- DOCSYNC:STATUS-END -->

---

## 5. Project structure (post-Batch 8)

```
ScrobbleScope/
  app.py                      # create_app() factory + logging setup + CSRF init (~109 lines)
  scrobblescope/
    __init__.py                # package marker
    config.py                  # env var reads, API keys, concurrency constants
    domain.py                  # SpotifyUnavailableError, ERROR_CODES, normalize_*
    utils.py                   # rate limiters, session pooling, request caching, helpers
    repositories.py            # JOBS dict, jobs_lock, all job state functions (pure CRUD)
    worker.py                  # _active_jobs_semaphore, acquire_job_slot(), release_job_slot(), start_job_thread()
    cache.py                   # asyncpg DB helpers (_get_db_connection with retry/backoff, batch lookup/persist)
    lastfm.py                  # check_user_exists, fetch_recent_tracks, fetch_top_albums
    spotify.py                 # fetch_spotify_access_token, search, batch details
    orchestrator.py            # process_albums, _fetch_and_process, background_task
    routes.py                  # Flask Blueprint with all route handlers + error handlers
  tests/
    conftest.py                # pytest fixtures only (client)
    helpers.py                 # shared test constants + async mock helpers
    test_app_factory.py        # 7 tests (WP-4 secret-key validation)
    test_domain.py             # 6 tests
    test_repositories.py       # 16 tests (job state + DB helpers incl retry/backoff)
    test_routes.py             # 39 tests (all route handlers incl unmatched_view + 404/500 + WP-5)
    services/
      test_lastfm_service.py   # 4 tests
      test_spotify_service.py  # 3 tests
      test_orchestrator_service.py # 10 tests
  templates/                   # Jinja2 templates (unchanged)
  static/                      # CSS/JS (unchanged)
  init_db.py                   # Postgres schema setup
  Dockerfile                   # gunicorn app:app (unchanged)
  fly.toml                     # Fly.io config (unchanged)
```

---

## 6. Module dependency graph (acyclic)

```
domain.py        <- (no internal deps)
config.py        <- (no internal deps)
utils.py         <- config
cache.py         <- config
worker.py        <- config
repositories.py  <- config, domain
lastfm.py        <- config, domain, utils, repositories
spotify.py       <- config, utils
orchestrator.py  <- cache, config, domain, lastfm, repositories, spotify, utils, worker
routes.py        <- lastfm, orchestrator, repositories, utils, worker
app.py           <- routes (via Blueprint registration)
```

No circular dependencies.

---

## 7. Architecture overview

### Request flow
```
User submits form (index.html)
  -> POST /results_loading (routes.py)
    -> Creates job (UUID in JOBS dict)
    -> Calls start_job_thread(background_task, args=(...)) [worker.py]
    -> Renders loading.html with job_id via tojson bridge

background_task (orchestrator.py, Thread):
  -> Creates asyncio event loop
  -> loop.run_until_complete(_fetch_and_process(...))
    -> Fetch Last.fm scrobbles (paginated, async)
    -> Group into albums, filter by thresholds
    -> process_albums (5-phase cache flow):
      Phase 1: DB connect + batch lookup (asyncpg, retry/backoff, 30-day TTL)
      Phase 2: Partition into cache_hits / cache_misses
      Phase 3: Spotify fetch for misses only
      Phase 4: DB batch persist new metadata + conn.close() in finally
      Phase 5: Build results
    -> Store results via set_job_results()

loading.js polls GET /progress?job_id=...
  -> On 100% + no error -> POST /results_complete
  -> On error + retryable -> show Retry button

POST /results_complete
  -> Reads job context, renders results.html with tojson bridge
```

---

## 7b. worker.py architectural decision

**Decision (2026-02-20, implemented in WP-1 commit):** Extract concurrency lifecycle into `scrobblescope/worker.py`.

**Rationale:** The confirmed product roadmap adds at least two new background task types (top songs, listening heatmap). Without `worker.py`, every new route that spawns a background task must duplicate the acquire -> try-Thread-start -> except-release pattern. With `worker.py`, all routes call `start_job_thread(target_fn, args)` -- one call, no duplication.

**What worker.py owns:**
- `_active_jobs_semaphore = threading.BoundedSemaphore(MAX_ACTIVE_JOBS)`
- `acquire_job_slot()` -- non-blocking acquire, returns bool; called in routes.py before `create_job()` to avoid orphaned jobs on capacity rejection
- `release_job_slot()` -- safe release with over-release guard; called in orchestrator.py `background_task` finally block
- `start_job_thread(target, args=())` -- starts daemon Thread(target, args), releases slot and raises on Thread.start() failure

**What repositories.py keeps:** pure job state CRUD only (`create_job`, `set_job_*`, `get_job_*`, `add_job_unmatched`, `reset_job_state`, `cleanup_expired_jobs`, `jobs_lock`, `JOBS`). `jobs_lock` stays in repositories because it guards the JOBS dict (data concern), whereas the semaphore guards worker slots (concurrency concern).

**Patch target convention (as-implemented):** tests patch at the module where the name is looked up. `acquire_job_slot` is imported into `routes.py` via `from scrobblescope.worker import ...`, so the patch target is `scrobblescope.routes.acquire_job_slot`. Similarly, `release_job_slot` is imported into `orchestrator.py`, so the patch target is `scrobblescope.orchestrator.release_job_slot`. Direct `start_job_thread` failures are tested by patching `scrobblescope.routes.start_job_thread`.

---

## 8. Test structure (88 tests)

| File | Count | Scope |
|------|-------|-------|
| test_app_factory.py | 7 | _validate_secret_key: production-fail paths, dev-mode warn, strong-key pass (WP-4) |
| test_domain.py | 6 | normalize_name, normalize_track_name, _extract_registered_year |
| test_repositories.py | 16 | Job state functions (7) + DB cache helpers (9 incl DB connect retry/backoff) |
| test_utils.py | 6 | REQUEST_CACHE hit/miss/expiry/overwrite/cleanup + concurrent-access stress test |
| tests/services/test_lastfm_service.py | 4 | Last.fm user-check and page-retry behavior |
| tests/services/test_spotify_service.py | 3 | Spotify search/details retry and non-200 behavior |
| tests/services/test_orchestrator_service.py | 11 | process_albums, _fetch_and_process, background_task (incl WP-1 slot-release tests) |
| test_routes.py | 39 | All Flask route handlers (incl unmatched_view, 404/500, WP-1 capacity/start-failure, WP-3 CSRF all 4 routes + XHR header path, WP-5 registration-year guard: reject/allow/fail-open/no-year paths) |

**Shared fixtures/helpers:** `conftest.py` provides only pytest fixtures (`client`); `tests/helpers.py` provides `TEST_JOB_PARAMS`, `NoopAsyncContext`, and `make_response_context`.

**Patch target convention:** Tests patch at the module where the name is looked up. E.g., `"scrobblescope.routes.run_async_in_thread"`, `"scrobblescope.orchestrator._get_db_connection"`.

---

## 9. Environment notes

- **Python 3.13.3** on Windows 11
- **Pre-commit hooks:** black, isort, autoflake, flake8, trailing whitespace, end-of-file, check yaml
- **pytest config** in `pyproject.toml` with `asyncio_mode = "strict"`
- **API keys** in `.env` (not committed): `LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `DATABASE_URL`
- **DB connect tuning env vars** (optional): `DB_CONNECT_MAX_ATTEMPTS` (default `3`), `DB_CONNECT_BASE_DELAY_SECONDS` (default `0.25`)
- **Frontend baseline (2026-02-14):** compact fixed-bottom dark-mode toggle across pages; `index` and `results` mobile spacing/typography tightened; decade pills centered.
- **Gunicorn:** `gunicorn app:app` still works (module-level `app = create_app()`)
- **Fly DB behavior:** unmanaged `scrobblescope-db` currently uses `FLY_SCALE_TO_ZERO=1h`; stopped/suspended state after idle is expected and DB wakes on demand.
- **Fly cold-start validation (2026-02-19):** `fly machine stop` was used for both `scrobblescope` and `scrobblescope-db`, then `scripts/smoke_cache_check.py` against `https://scrobblescope.fly.dev` (`flounder14`, `2025`, `--runs 1`) succeeded; both machines auto-started and DB checks converged to passing.
- **Audit focus (2026-02-20):** highest-priority risks are unbounded job concurrency, non-thread-safe in-memory request cache, and missing CSRF protection on POST routes. Execution sequence is documented in `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`.
- **WP-1 (2026-02-20):** Bounded job concurrency implemented. `MAX_ACTIVE_JOBS` (default 10) in `config.py`. `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread()` in `worker.py` (leaf module, imports `config` only). Slot acquired via `acquire_job_slot()` before `create_job()` in `routes.py`; thread started via `start_job_thread()` which releases slot and re-raises on failure; slot released in `background_task` `finally` block in `orchestrator.py`.
- **WP-2 (2026-02-19):** `REQUEST_CACHE` thread-safe. `_cache_lock = threading.Lock()` in `utils.py` wraps all read/write/cleanup operations. 6 tests in new `tests/test_utils.py` including concurrent-access stress test.
- **WP-3 (2026-02-19):** CSRF protection on all mutating POST routes. `Flask-WTF>=1.2.0` installed; `CSRFProtect` initialized in `app.py` with a `CSRFError` 400 handler. Hidden `csrf_token` input added to `index.html` and `results.html` forms. `csrf-token` meta tag added to `loading.html`; `loading.js` reads it and injects token into all programmatic form POSTs (`redirectToResults`, `retryCurrentSearch`) and the `fetch('/reset_progress')` XHR header (`X-CSRFToken`). `conftest.py` sets `WTF_CSRF_ENABLED=False` for test isolation; 6 CSRF tests added to `test_routes.py`: reject-without-token and accept-with-token for `/results_loading`; reject-without-token for `/results_complete`, `/unmatched_view`, `/reset_progress`; accept-with-`X-CSRFToken`-header for `/reset_progress` (XHR path). 81 tests passing.
- **WP-4 (2026-02-20):** App secret hardened. `_validate_secret_key(secret_key, is_dev_mode)` added to `app.py`; called inside `create_app()`. Raises `RuntimeError` in production when `SECRET_KEY` is absent, in known-weak set (`"dev"`, `"changeme_in_production"`, `""`), or shorter than 16 chars. Logs a warning in dev mode (`DEBUG_MODE=1`) instead of failing. `conftest.py` seeds `os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")` before importing `app` so module-level `create_app()` does not trip the guard. 7 tests in new `tests/test_app_factory.py`. `.env.example` and `README.md` updated to document the requirement. 88 tests passing.
- **WP-5 (2026-02-20):** Server-side registration-year validation added. In `results_loading`, after the `2002..current_year` bounds check, calls `check_user_exists(username)` via `run_async_in_thread` (typically a free cache hit from the blur-validation step). If `registered_year` is present and `year < registered_year`, re-renders `index.html` with an explicit error. Fail-open on service unavailability. 4 new tests in `test_routes.py` (reject, allow at boundary, fail-open, no-registered-year). 92 tests passing.
- **WP-6 (2026-02-20):** All 5 `await asyncio.sleep(0.5)` calls removed from `_fetch_and_process` in `orchestrator.py`. Eliminated 2.5 s fixed latency overhead per job. `asyncio` import retained (still used for Semaphore, gather, new_event_loop, set_event_loop). Removed 2 dead `patch("asyncio.sleep", ...)` lines from `test_orchestrator_service.py`. 92 tests still passing.
- **doc_state_sync fix (2026-02-20):** `_git_head_short()` function and `subprocess` import removed from `scripts/doc_state_sync.py`. The `Last sync commit` field was volatile (merge commits advanced HEAD) and caused `doc-state-sync-check` pre-commit hook to false-positive on every PR merge. The `--check` now validates only stable content-level fields.
