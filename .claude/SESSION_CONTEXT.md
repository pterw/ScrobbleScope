# ScrobbleScope Session Context (Post-Batch 8 Modular Refactor)

Last updated: 2026-02-14
Author: Claude Opus 4.6 + Codex (for agent handoff / new session bootstrap)

---

## 1. What is ScrobbleScope?

A Flask web app that fetches a user's Last.fm scrobble history for a given year, enriches album data with Spotify metadata (release dates, artwork, track runtimes), and presents filtered/sorted top-album rankings. Primary use case: building Album of the Year (AOTY) lists.

**Stack:** Python 3.13, Flask, aiohttp/aiolimiter (async API calls), Bootstrap 5, Jinja2 templates, pytest + pytest-asyncio.

**Deployment:** Fly.io (ephemeral VM, shared-cpu-2x @ 512MB). Postgres on Fly for persistent Spotify metadata cache (asyncpg). In-memory job state (`JOBS` dict).

---

## 2. Current state

| Item | Value |
|------|-------|
| Branch | `wip/pc-snapshot` |
| Latest commit | Batch 8 modular refactor; local cache wake-up hardening is uncommitted |
| Tests | **66 passing** across 6 test files |
| Pre-commit | All hooks pass (black, isort, autoflake, flake8) |
| app.py line count | ~91 lines (factory pattern) |
| Deploy status | Batch 7 live on Fly. Batch 8 + DB connect retry/backoff hardening are local/uncommitted until next deploy. |

---

## 3. Documents to read (priority order)

| Document | Status | Purpose |
|----------|--------|---------|
| `EXECUTION_PLAYBOOK_2026-02-11.md` | **Source of truth** | Batch ordering, acceptance criteria, execution log, next steps. |
| `.claude/SESSION_CONTEXT.md` (this file) | **Current** | Quick orientation for agents. Architecture, key locations, known gaps. |
| `README.md` | **Current** | Product description, roadmap checklist, setup instructions. |

---

## 4. Batch completion status

| Batch | Task | Status |
|-------|------|--------|
| 1 | Upstream failure classification + retry UX | Done |
| 2 | Personalized min listening year from registration date | Done |
| 3 | Remove nested thread pattern | Done |
| 4 | Expand test coverage (12 -> 43 tests, gaps closed) | Done |
| 5 | Docstring + comment normalization | Done |
| 6 | Frontend refinement/tweaks | Done |
| 7 | Persistent metadata layer (Postgres via asyncpg) | Done |
| **8** | **Modular refactor (app.py -> scrobblescope/ package)** | **Done** |

---

## 5. Project structure (post-Batch 8)

```
ScrobbleScope/
  app.py                      # create_app() factory + logging setup (~91 lines)
  scrobblescope/
    __init__.py                # package marker
    config.py                  # env var reads, API keys, concurrency constants
    domain.py                  # SpotifyUnavailableError, ERROR_CODES, normalize_*
    utils.py                   # rate limiters, session pooling, request caching, helpers
    repositories.py            # JOBS dict, jobs_lock, all job state functions
    cache.py                   # asyncpg DB helpers (_get_db_connection with retry/backoff, batch lookup/persist)
    lastfm.py                  # check_user_exists, fetch_recent_tracks, fetch_top_albums
    spotify.py                 # fetch_spotify_access_token, search, batch details
    orchestrator.py            # process_albums, _fetch_and_process, background_task
    routes.py                  # Flask Blueprint with all route handlers + error handlers
  tests/
    conftest.py                # pytest fixtures only (client)
    helpers.py                 # shared test constants + async mock helpers
    test_domain.py             # 6 tests
    test_repositories.py       # 16 tests (job state + DB helpers incl retry/backoff)
    test_routes.py             # 27 tests (all route handlers incl unmatched_view + 404/500)
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
repositories.py  <- config, domain
lastfm.py        <- config, domain, utils, repositories
spotify.py       <- config, utils
orchestrator.py  <- cache, config, domain, lastfm, repositories, spotify, utils
routes.py        <- lastfm, orchestrator, repositories, utils
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
    -> Spawns daemon Thread(target=background_task)
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

## 8. Test structure (66 tests)

| File | Count | Scope |
|------|-------|-------|
| test_domain.py | 6 | normalize_name, normalize_track_name, _extract_registered_year |
| test_repositories.py | 16 | Job state functions (7) + DB cache helpers (9 incl DB connect retry/backoff) |
| tests/services/test_lastfm_service.py | 4 | Last.fm user-check and page-retry behavior |
| tests/services/test_spotify_service.py | 3 | Spotify search/details retry and non-200 behavior |
| tests/services/test_orchestrator_service.py | 10 | process_albums, _fetch_and_process, background_task |
| test_routes.py | 27 | All Flask route handlers (including unmatched_view and 404/500 handlers) |

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
