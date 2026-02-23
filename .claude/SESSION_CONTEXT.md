# ScrobbleScope Session Context

Last updated: 2026-02-23

---

## 1. What is ScrobbleScope?

A Flask web app that fetches a user's Last.fm scrobble history for a given
year, enriches album data with Spotify metadata (release dates, artwork,
track runtimes), and presents filtered/sorted top-album rankings.

**Confirmed upcoming features (owner roadmap):**
- **Top songs**: rank most-played tracks for a year (separate background task).
- **Listening heatmap**: scrobble density calendar (Last.fm only, lighter task).

**Stack:** Python 3.13, Flask, aiohttp/aiolimiter, Bootstrap 5, Jinja2, pytest.

**Deployment:** Fly.io (shared-cpu-2x @ 512MB). Postgres for Spotify metadata
cache (asyncpg). In-memory job state (`JOBS` dict).

---

## 2. Current state

| Item | Value |
|------|-------|
| Branch | `wip/pc-snapshot` |
| Tests | **257 passing** across 10 test files |
| Coverage | ~72% (2026-02-20 audit run) |
| Pre-commit | All hooks pass |
| Batch 11 status | **Complete**. WP-1 done, WP-2 done, WP-3 done. |
| Batch 12 status | **Complete**. WP-1 done, WP-2 done, WP-3 done, WP-4 done. |
| Known open risk | None. |

**Key runtime facts:**
- `MAX_ACTIVE_JOBS` (default 10) caps concurrent background jobs via `worker.py`.
- `_GlobalThrottle` in `utils.py` caps aggregate API throughput across all threads.
- `_cache_lock` in `utils.py` guards `REQUEST_CACHE` thread safety.
- `_PLAYTIME_ALBUM_CAP = 500` in `orchestrator.py` limits Spotify fetch for playtime sort.
- Cold-start validated 2026-02-19 (both app + DB auto-wake on demand).

---

## 3. Execution status (machine-managed)

`PLAYBOOK.md` is the source of truth. Block below managed by `doc_state_sync.py`.

<!-- DOCSYNC:STATUS-START -->
- Source of truth: `PLAYBOOK.md` (Section 3 and Section 4).
- Current batch: none (between batches).
- Last completed batch in PLAYBOOK Section 3: Batch 12.
- Current-batch entries in active log block: 0.
- Completed work packages in current-batch entries: n/a (no active batch).
- Next expected work package: n/a (next batch not defined).
- Newest current-batch entry: none.
<!-- DOCSYNC:STATUS-END -->

---

## 4. Project structure

```
app.py                      # create_app() factory (~142 lines)
scrobblescope/
  config.py                 # env var reads, API keys, concurrency constants
  errors.py                 # SpotifyUnavailableError, ERROR_CODES
  domain.py                 # normalize_name, normalize_track_name
  utils.py                  # rate limiters, session pooling, request caching
  repositories.py           # JOBS dict, jobs_lock, job state CRUD
  worker.py                 # semaphore, acquire/release_job_slot, start_job_thread
  cache.py                  # asyncpg DB helpers (retry/backoff, batch lookup/persist)
  lastfm.py                 # check_user_exists, fetch_recent_tracks (pure HTTP client)
  spotify.py                # fetch_spotify_access_token, search, batch details
  orchestrator.py           # process_albums, _fetch_and_process, background_task, fetch_top_albums_async
  routes.py                 # Flask Blueprint, all route + error handlers
```

---

## 5. Module dependency graph (acyclic)

```
errors.py        <- (leaf)
domain.py        <- (leaf)
config.py        <- (leaf)
utils.py         <- config
cache.py         <- config
worker.py        <- config
repositories.py  <- config, errors
lastfm.py        <- config, utils
spotify.py       <- config, utils
orchestrator.py  <- cache, config, domain, errors, lastfm, repositories, spotify, utils, worker
routes.py        <- lastfm, orchestrator, repositories, utils, worker
app.py           <- routes (Blueprint)
```

---

## 6. Architecture overview

```
User submits form (index.html)
  -> POST /results_loading (routes.py)
    -> Creates job (UUID in JOBS dict)
    -> start_job_thread(background_task, ...) [worker.py]
    -> Renders loading.html with job_id

background_task (orchestrator.py, daemon Thread):
  -> asyncio event loop -> _fetch_and_process(...)
    -> Fetch Last.fm scrobbles (paginated, async)
    -> Group into albums, filter by thresholds
    -> process_albums (5-phase cache flow):
      1: DB connect + batch lookup (30-day TTL)
      2: Partition cache_hits / cache_misses
      3: Spotify fetch for misses only
      4: DB batch persist + conn.close() in finally
      5: Build results -> set_job_results()

loading.js polls GET /progress?job_id=...
  -> 100% + no error -> POST /results_complete -> renders results.html
  -> error + retryable -> show Retry button
```

---

## 7. Test structure (257 tests)

| File | Count |
|------|-------|
| test_app_factory.py | 6 |
| test_doc_state_sync.py | 81 |
| test_domain.py | 13 |
| test_repositories.py | 18 |
| test_utils.py | 34 |
| test_routes.py | 50 |
| services/test_lastfm_service.py | 9 |
| services/test_lastfm_logic.py | 7 |
| services/test_spotify_service.py | 10 |
| services/test_orchestrator_service.py | 29 |

---

## 8. Environment notes

- Python 3.13.3, Windows 11, venv.
- Pre-commit: black, isort, autoflake, flake8, trailing whitespace, end-of-file, check yaml, doc-state-sync-check.
- pytest in `pyproject.toml` with `asyncio_mode = "strict"`.
- API keys in `.env` (git-ignored); template: `.env.example`.
- Gunicorn compat: `app = create_app()` at module level in `app.py`.
- worker.py ADR archived at `docs/history/WORKER_ADR_2026-02-20.md`.
