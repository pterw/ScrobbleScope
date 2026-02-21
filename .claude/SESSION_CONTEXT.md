# ScrobbleScope Session Context (Post-Batch 8 Modular Refactor)

Last updated: 2026-02-21
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
| Latest commit | Use `git rev-parse --short HEAD` for current snapshot |
| Tests | **121 passing** across 9 test files |
| Coverage snapshot | **72%** (`pytest --cov=scrobblescope`, 2026-02-20 audit run; not re-measured after 2026-02-21 fixes) |
| Pre-commit | All hooks pass (black, isort, autoflake, flake8, doc-state-sync-check) |
| app.py line count | ~142 lines (factory + logging setup + CSRF init + secret-key guard) |
| Cache fallback logging | `_get_db_connection()` logs classified reasons: `asyncpg-missing`, `missing-env-var`, `db-down` |
| Deploy status | Cold-start validated on 2026-02-19 by manually stopping app+DB machines and running an end-to-end smoke request (`elapsed=18.75s`, `db_cache_enabled=True`, `db_cache_lookup_hits=247`). |
| Batch 9 status | **Complete** (WP-1 through WP-8 all done). See `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md` |
| Batch 10 status | **Complete**. WP-1 through WP-9 done. WP-7 = cross-job rate limiting fix; WP-8 = pre-slice gate fix; WP-9 = playtime album cap. 121 tests. |
| Job concurrency cap | `MAX_ACTIVE_JOBS` (default 10, env-tunable). `acquire_job_slot()` / `release_job_slot()` / `start_job_thread()` in `scrobblescope/worker.py`. |
| Global API rate limiting | `_GlobalThrottle` + `_ThrottledLimiter` in `utils.py` cap aggregate Last.fm and Spotify throughput across all concurrent event loops. |
| Request cache thread safety | `_cache_lock = threading.Lock()` in `utils.py` guards all `REQUEST_CACHE` read/write/cleanup ops. |
| Playtime album cap | `_PLAYTIME_ALBUM_CAP = 500` in `orchestrator.py` limits albums sent to Spotify fetch for playtime sort; logs WARNING when triggered. |
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
- Current batch: Batch 11.
- Current-batch entries in active log block: 4.
- Completed work packages in current-batch entries: WP-5, WP-6, WP-7, WP-8, WP-9.
- Next expected work package: WP-10.
- Newest current-batch entry: 2026-02-21 - fix: Gemini 3.1 Pro P0/P1 audit remediation (Batch 10 WP-7, WP-8, WP-9).
<!-- DOCSYNC:STATUS-END -->

---

## 5. Project structure (post-Batch 8)

```
ScrobbleScope/
  app.py                      # create_app() factory + logging setup + CSRF init + secret-key guard (~142 lines)
  scrobblescope/
    __init__.py                # package marker
    config.py                  # env var reads, API keys, concurrency constants
    errors.py                  # SpotifyUnavailableError, ERROR_CODES (leaf module)
    domain.py                  # normalize_name, normalize_track_name, _extract_registered_year
    utils.py                   # rate limiters, session pooling, request caching, helpers
    repositories.py            # JOBS dict, jobs_lock, all job state functions (pure CRUD)
    worker.py                  # _active_jobs_semaphore, acquire_job_slot(), release_job_slot(), start_job_thread()
    cache.py                   # asyncpg DB helpers (_get_db_connection with retry/backoff, batch lookup/persist)
    lastfm.py                  # check_user_exists, fetch_recent_tracks, fetch_top_albums
    spotify.py                 # fetch_spotify_access_token, search, batch details
    orchestrator.py            # process_albums, _fetch_and_process, background_task
    routes.py                  # Flask Blueprint with all route handlers + error handlers
  tests/
    conftest.py                # pytest fixtures: client (CSRF disabled) + csrf_app_client (CSRF enabled)
    helpers.py                 # shared test constants (TEST_JOB_PARAMS, VALID_FORM_DATA) + async mock helpers
    test_app_factory.py        # 7 tests (WP-4 secret-key validation)
    test_domain.py             # 15 tests (normalize_name, normalize_track_name incl non-Latin + artist-fix, _extract_registered_year)
    test_repositories.py       # 18 tests (job state + DB helpers incl retry/backoff + delete_job)
    test_routes.py             # 42 tests (all route handlers incl unmatched_view + 404/500 + WP-5 + WP-6 adversarial helpers)
    services/
      test_lastfm_service.py   # 4 tests
      test_lastfm_logic.py     # 7 tests (fetch_top_albums_async: aggregation, filters, timestamp bounds, now-playing, non-Latin, job stats)
      test_spotify_service.py  # 3 tests
      test_orchestrator_service.py # 18 tests
  templates/                   # Jinja2 templates (unchanged)
  static/                      # CSS/JS (unchanged)
  init_db.py                   # Postgres schema setup
  Dockerfile                   # gunicorn app:app (unchanged)
  fly.toml                     # Fly.io config (unchanged)
```

---

## 6. Module dependency graph (acyclic)

```
errors.py        <- (no internal deps)
domain.py        <- (no internal deps)
config.py        <- (no internal deps)
utils.py         <- config
cache.py         <- config
worker.py        <- config
repositories.py  <- config, errors
lastfm.py        <- config, domain, utils, repositories
spotify.py       <- config, utils
orchestrator.py  <- cache, config, domain, errors, lastfm, repositories, spotify, utils, worker
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

## 8. Test structure (121 tests)

| File | Count | Scope |
|------|-------|-------|
| test_app_factory.py | 6 | _validate_secret_key: production-fail paths, dev-mode warn, strong-key pass (WP-4). Dev-mode strong-key duplicate removed in Batch 10 WP-5. |
| test_domain.py | 15 | normalize_name (incl artist-name preservation, album-only word stripping, collision prevention), normalize_track_name (incl Japanese/Cyrillic preservation, punctuation consistency), _extract_registered_year |
| test_repositories.py | 18 | Job state functions (7) + DB cache helpers (9 incl retry/backoff) + delete_job (2) |
| test_utils.py | 8 | REQUEST_CACHE hit/miss/expiry/overwrite/cleanup + concurrent-access stress test; _GlobalThrottle serialization + cross-thread shared throttle identity |
| tests/services/test_lastfm_service.py | 4 | Last.fm user-check and page-retry behavior |
| tests/services/test_lastfm_logic.py | 7 | fetch_top_albums_async: play-count aggregation, min_plays filter, min_tracks filter, out-of-bounds timestamp exclusion, now-playing sentinel, non-Latin track deduplication, job-stat reporting |
| tests/services/test_spotify_service.py | 3 | Spotify search/details retry and non-200 behavior |
| tests/services/test_orchestrator_service.py | 18 | process_albums, _fetch_and_process, background_task (incl slot-release); _cleanup_stale_metadata (delete + nonfatal); playcount pre-slice (scope=all only); playcount no-preslice when scoped; playtime cap fires + warns; playtime no-cap below threshold |
| test_routes.py | 42 | All Flask route handlers (incl unmatched_view, 404/500, WP-1 capacity/start-failure, WP-3 CSRF all 4 routes + XHR header path, WP-5 registration-year guard: reject/allow/fail-open/no-year paths) + 3 adversarial helper unit tests (WP-6) |

**Shared fixtures/helpers:** `conftest.py` provides `client` (CSRF disabled) and `csrf_app_client` (CSRF enabled) fixtures; `tests/helpers.py` provides `TEST_JOB_PARAMS`, `VALID_FORM_DATA`, `NoopAsyncContext`, and `make_response_context`.

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
- **WP-7 (2026-02-20):** Frontend safety polish. `showToast` in `results.js` converted from `insertAdjacentHTML`+template-literal to safe DOM construction (`createElement`/`textContent`). `fetchUnmatchedAlbums` now throws on non-200 responses via `response.ok` guard before `.json()`. 94 tests still passing.
- **WP-8 (2026-02-20):** CI, lint, and dependency hygiene. `check-yaml` pre-commit hook fixed: `files` pattern changed from `^.*\.py$` to `^.*\.(yaml|yml)$`; `.github` removed from global `exclude` so the workflow YAML is now validated. Dev-only packages (`pre-commit`, `pytest`, `pytest-asyncio`, `pytest-cov`, `flake8`) moved to new `requirements-dev.txt` (`-r requirements.txt` + dev tools); `requirements.txt` is now runtime-only. `.coverage` added to `.gitignore`. CI workflow updated to install `requirements-dev.txt`, drop redundant `pip install` steps, and enforce `--cov-fail-under=70` coverage gate. Batch 9 remediation complete.
- **doc_state_sync fix (2026-02-20):** `_git_head_short()` function and `subprocess` import removed from `scripts/doc_state_sync.py`. The `Last sync commit` field was volatile (merge commits advanced HEAD) and caused `doc-state-sync-check` pre-commit hook to false-positive on every PR merge. The `--check` now validates only stable content-level fields. The transient `rotated=N` field was also removed from the managed SESSION_CONTEXT block to eliminate post-rotation drift.
- **Normalization bug fixes (2026-02-21):** Three production bugs fixed in `scrobblescope/domain.py` following a third-party audit review. (1) `normalize_track_name` used NFKD + encode("ascii","ignore"), silently stripping all non-Latin characters to "" and causing any Japanese/Cyrillic/etc. album to fail the min_tracks filter without an unmatched entry or log warning -- fixed to NFKC. (2) `normalize_name` applied `album_metadata_words` to the artist string as well as album, corrupting proper nouns like "New Edition" and causing empty-key collisions for artists named "Special", "Bonus", or "EP" -- fixed to album-only removal. (3) `normalize_track_name` had a 13-char hardcoded punctuation list vs `str.maketrans(string.punctuation,...)` in `normalize_name` -- fixed to use the same approach. Coverage gap also closed: `fetch_top_albums_async` (aggregation, filtering, timestamp logic) now has 7 tests in new `tests/services/test_lastfm_logic.py`. Owner validated with a real non-Latin-script album that was previously absent from results. Full detail in `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md`. 110 tests passing.
- **Gemini audit remediation (2026-02-21):** Four issues from a second Gemini audit pass fixed. (1) Late slicing: `_fetch_and_process` now pre-slices `filtered_albums` by `play_count` before `process_albums` when `sort_mode="playcount"` and a finite `limit_results` is set -- eliminating unnecessary Spotify searches for albums outside the top N. Playtime sort cannot be pre-sliced (documented). (2) DB stale row cleanup: `_cleanup_stale_metadata(conn)` added to `cache.py`, called opportunistically from `process_albums` after Phase 1 lookup -- DELETEs rows older than `METADATA_CACHE_TTL_DAYS`. Non-fatal. (3) `ERROR_CODES` and `SpotifyUnavailableError` extracted from `domain.py` to new leaf module `scrobblescope/errors.py`; import sites in `orchestrator.py`, `repositories.py`, and the orchestrator test file updated. (4) Duplicate release_scope->text translation in `routes.py:unmatched_view` replaced with call to existing `get_filter_description`. Full detail in `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md`. 114 tests passing.
- **Sycophantic test audit (2026-02-21, Batch 10 WP-5):** Five tests strengthened or removed following a Gemini 2.5 Pro characterisation of the suite as providing "mock-call-only" and "vacuously passing" coverage. (1) `test_results_loading_thread_start_failure_renders_error` -- dropped delete_job mock, replaced with JOBS snapshot diff so orphan-job regressions are caught. (2) `test_fetch_and_process_cache_hit_does_not_precheck_spotify` -- added `JOBS[job_id]["results"]` assertion to verify set_job_results side-effect (background_task reads job state, not return value). (3) `test_succeeds_with_strong_key_in_dev_mode` -- removed as near-duplicate of production strong-key test. (4) `test_cleanup_stale_metadata_nonfatal` -- added caplog warning assertion. (5) `test_delete_job_on_missing_job_is_noop` -- added JOBS membership check. Full detail in `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md`. 113 tests passing.
- **Cross-job rate limiting (2026-02-21, Batch 10 WP-7):** Per-loop `AsyncLimiter` design gave each background job an independent rate limiter; with `MAX_ACTIVE_JOBS=10`, aggregate throughput could reach 10x the configured cap. Fixed by introducing `_GlobalThrottle` (thread-safe token bucket via `threading.Lock`) and `_ThrottledLimiter` (async context manager composing global throttle + per-loop `AsyncLimiter`) in `utils.py`. `_LASTFM_THROTTLE` and `_SPOTIFY_THROTTLE` are module-level singletons shared across all threads. Call sites in `lastfm.py` and `spotify.py` are unchanged. 2 adversarial tests added to `test_utils.py`. 118 tests passing.
- **Pre-slice gate fix (2026-02-21, Batch 10 WP-8):** Playcount pre-slice in `_fetch_and_process` ran before `process_albums` applied the `release_scope` filter. With `release_scope != "all"`, albums outside the raw top-N could be the only ones matching the year filter, silently returning fewer results. Fixed by adding `and release_scope == "all"` to the gate condition. Renamed existing test to document the `scope=all` invariant; added adversarial test confirming all albums pass through for scoped queries. 119 tests passing.
- **Playtime album cap (2026-02-21, Batch 10 WP-9):** No upper bound on `filtered_albums` for playtime sort (pre-slicing impossible without Spotify track durations). Added `_PLAYTIME_ALBUM_CAP = 500` in `orchestrator.py`; cap block sorts by `play_count` (best available proxy) and logs a `WARNING` when triggered. 2 tests added (cap fires + warns; no-op below threshold). 121 tests passing.
- **Routes SoC audit (2026-02-21, Batch 10 WP-6):** Four SoC and duplication findings in `routes.py` resolved. (R1) Duplicate inner async wrappers for `check_user_exists` in `validate_user()` and `results_loading()` extracted to `_check_user_exists(username)`. (R2) Eight-field job params extraction duplicated in `results_complete()` and `unmatched_view()` extracted to `_extract_job_params(job_context)`. (R3) Reason-grouping data transform in `unmatched_view()` extracted to `_group_unmatched_by_reason(unmatched_data)`. (R4) Zero-playtime filter business rule in `results_complete()` extracted to `_filter_results_for_display(results_data, sort_mode)`. Follow-up: three adversarial unit tests added after route tests were found to only exercise happy paths for `_filter_results_for_display` (filter never fired) and `_group_unmatched_by_reason` ("Unknown reason" fallback untested). Full detail in `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md`. 116 tests passing. Batch 10 complete.
