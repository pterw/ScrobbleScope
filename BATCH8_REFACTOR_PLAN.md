# Batch 8: Modular Refactor — Implementation Plan

**Status:** Approved, not yet started. No slices executed.
**Date:** 2026-02-13
**Branch:** `wip/pc-snapshot`
**Prereqs:** 59 tests green, pre-commit hooks pass, Batches 1-7 complete.

---

## Context

`app.py` is a ~2091-line monolith containing all routes, services, repositories, domain logic, and configuration. `tests/test_app.py` is a ~1500-line file with 59 tests. Both need to be decomposed into focused modules. The app is live on Fly.io with Postgres cache.

**Goal:** Decompose `app.py` into a `scrobblescope/` package (8 modules) and split `tests/test_app.py` into 4 test files + `conftest.py`, using a strangler pattern (one slice at a time, 59 tests green after every slice).

---

## Target Structure

```
ScrobbleScope/
├── app.py                     # create_app() factory + logging setup (~80 lines)
├── scrobblescope/
│   ├── __init__.py            # package marker
│   ├── config.py              # env var reads, API keys, concurrency constants
│   ├── domain.py              # SpotifyUnavailableError, ERROR_CODES, normalize_*, _extract_registered_year
│   ├── utils.py               # rate limiters, create_optimized_session, request caching, format_seconds, run_async_in_thread
│   ├── repositories.py        # JOBS, jobs_lock, all job_* state functions
│   ├── cache.py               # _get_db_connection, _batch_lookup_metadata, _batch_persist_metadata
│   ├── lastfm.py              # check_user_exists, fetch_recent_tracks_*, fetch_top_albums_async
│   ├── spotify.py             # fetch_spotify_access_token, search_for_spotify_album_id, fetch_spotify_album_details_batch
│   ├── orchestrator.py        # process_albums, _fetch_and_process, background_task
│   └── routes.py              # Flask Blueprint with all route handlers + error handlers
├── templates/                 # unchanged
├── static/                    # unchanged
├── tests/
│   ├── conftest.py            # client fixture, _TEST_JOB_PARAMS, _NoopAsyncContext, _make_response_context
│   ├── test_domain.py         # 6 tests
│   ├── test_repositories.py   # 14 tests (job state + DB helpers)
│   ├── test_services.py       # 19 tests (Last.fm, Spotify, orchestrator, process_albums)
│   └── test_routes.py         # 20 tests
├── init_db.py                 # unchanged
├── Dockerfile                 # unchanged (gunicorn app:app still works)
└── fly.toml                   # unchanged
```

---

## Key Design Decisions

1. **`create_app()` lives in `app.py`** (project root) — keeps template/static path resolution simple (Flask resolves relative to `app.py`'s directory)
2. **Module-level `app = create_app()`** at bottom of `app.py` — backward compatible with `gunicorn app:app`
3. **Routes use a single Flask Blueprint** registered in `create_app()`
4. **Error handlers use `@bp.app_errorhandler`** (not `@bp.errorhandler`) for application-wide 404/500 handling
5. **`inject_current_year` context processor** moves to routes.py as `@bp.app_context_processor`

---

## Critical Risks

### Risk 1: Re-exports and autoflake
During slices 1-5, `app.py` re-imports extracted symbols so that un-moved tests still find them via `from app import X`. **Autoflake (`--remove-all-unused-imports` in `.pre-commit-config.yaml`) will strip these re-exports.** Every transitional re-export must have `# noqa: F401` until slice 6 removes them.

### Risk 2: Patch Targets
Tests that `patch("app.X")` patch the name binding in the `app` module. The rule: **patch where the name is looked up at call time, not where it's defined.** During the strangler phase, re-exports in `app.py` keep `"app.X"` patch targets working for un-moved tests. When a test moves to a new file, its patch targets update to the new module path simultaneously.

---

## Dependency Graph (acyclic, verified)

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

No circular dependencies. Each module only imports from modules above it in the hierarchy.

---

## Slice Execution Plan

### Slice 1: Foundations — conftest.py + config.py + domain.py + test_domain.py

**New files:** `scrobblescope/__init__.py`, `scrobblescope/config.py`, `scrobblescope/domain.py`, `tests/conftest.py`, `tests/test_domain.py`

**Extract to `config.py`:**
- `LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` (app.py line 410-412)
- `MAX_CONCURRENT_LASTFM`, `LASTFM_REQUESTS_PER_SECOND`, all `SPOTIFY_*` concurrency constants (lines 51-58)
- `JOB_TTL_SECONDS`, `REQUEST_CACHE_TIMEOUT`, `METADATA_CACHE_TTL_DAYS` (lines 46-48, 533)
- `spotify_token_cache` (line 421)
- `ensure_api_keys()` (lines 415-418)

**Extract to `domain.py`:**
- `SpotifyUnavailableError` (line 97)
- `ERROR_CODES` dict (lines 68-94)
- `normalize_name()` (lines 615-652)
- `normalize_track_name()` (lines 655-661)
- `_extract_registered_year()` (lines 1003-1009)

**Extract to `conftest.py`:**
- `client` fixture (test_app.py lines 40-45) — initially imports `app` from `app` module
- `_TEST_JOB_PARAMS` constant (test_app.py lines 159-169)
- `_NoopAsyncContext` class (test_app.py lines 711-718)
- `_make_response_context()` helper (test_app.py lines 721-725)

**Move to `test_domain.py` (6 tests, 0 patch targets):**
- `test_normalize_name_simple`, `test_normalize_name_remastered_suffix`, `test_normalize_name_unicode_preserved`
- `test_normalize_track_name_strips_punctuation`
- `test_extract_registered_year_valid`, `test_extract_registered_year_missing_key`
- Import directly from `scrobblescope.domain` (no `app.X` patches needed)

**Changes to `app.py`:** Delete original definitions. Add re-exports with `# noqa: F401`:
```python
from scrobblescope.config import (  # noqa: F401
    JOB_TTL_SECONDS, LASTFM_API_KEY, LASTFM_REQUESTS_PER_SECOND,
    MAX_CONCURRENT_LASTFM, METADATA_CACHE_TTL_DAYS, REQUEST_CACHE_TIMEOUT,
    SPOTIFY_BATCH_CONCURRENCY, SPOTIFY_BATCH_RETRIES, SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET, SPOTIFY_REQUESTS_PER_SECOND,
    SPOTIFY_SEARCH_CONCURRENCY, SPOTIFY_SEARCH_RETRIES,
    ensure_api_keys, spotify_token_cache,
)
from scrobblescope.domain import (  # noqa: F401
    ERROR_CODES, SpotifyUnavailableError, _extract_registered_year,
    normalize_name, normalize_track_name,
)
```

**Changes to `test_app.py`:** Remove 6 moved tests, remove `client` fixture, remove `_TEST_JOB_PARAMS` / helpers. Remove `normalize_name`, `normalize_track_name`, `_extract_registered_year` from `from app import (...)` block. Keep `SpotifyUnavailableError` (still used by 2 remaining orchestrator tests).

**Verify:** `pytest tests/ -q` (59 = 6 + 53), `pre-commit run --all-files`

---

### Slice 2: utils.py — Rate Limiters, Session, Caching, Helpers

**New file:** `scrobblescope/utils.py`

**Extract:**
- `REQUEST_CACHE` dict (line 45)
- `_LASTFM_LIMITERS`, `_SPOTIFY_LIMITERS`, `_LIMITER_LOCK` (lines 62-64)
- `_get_loop_limiter()`, `get_lastfm_limiter()`, `get_spotify_limiter()` (lines 101-129)
- `run_async_in_thread()` (lines 132-158)
- `create_optimized_session()` (lines 424-457)
- `get_cache_key()`, `get_cached_response()`, `set_cached_response()`, `cleanup_expired_cache()` (lines 461-510)
- `format_seconds()` (lines 1411-1429)

**No tests move.** All un-moved tests that patch `"app.get_lastfm_limiter"` etc. still work because `app.py` re-exports these names and the calling functions are still in `app.py`.

**Changes to `app.py`:** Delete originals, add re-exports with `# noqa: F401`.

**Verify:** `pytest tests/ -q` (59), `pre-commit run --all-files`

---

### Slice 3: repositories.py + cache.py + test_repositories.py

**New files:** `scrobblescope/repositories.py`, `scrobblescope/cache.py`, `tests/test_repositories.py`

**Extract to `repositories.py`:**
- `JOBS`, `jobs_lock` (lines 214-215)
- `_initial_progress()`, `cleanup_expired_jobs()`, `create_job()`, `set_job_progress()`, `set_job_error()`, `set_job_stat()`, `set_job_results()`, `add_job_unmatched()`, `reset_job_state()`, `get_job_progress()`, `get_job_unmatched()`, `get_job_context()` (lines 218-406)
- Internal imports: `from scrobblescope.config import JOB_TTL_SECONDS` and `from scrobblescope.domain import ERROR_CODES`

**Extract to `cache.py`:**
- `_get_db_connection()`, `_batch_lookup_metadata()`, `_batch_persist_metadata()` (lines 513-612)
- Owns its own `try: import asyncpg` block
- Internal imports: `from scrobblescope.config import METADATA_CACHE_TTL_DAYS`

**Move to `test_repositories.py` (14 tests):**

7 job state tests (0 patch target changes — direct function calls):
- `test_set_job_error_sets_classified_fields`, `test_set_job_error_user_not_found_not_retryable`
- `test_create_job_returns_unique_ids`, `test_job_isolation_separate_progress`
- `test_set_job_progress_missing_job_returns_false`, `test_set_job_stat_stores_and_retrieves`
- `test_expired_job_cleanup`
- Import from `scrobblescope.repositories`

7 DB helper tests (2 patch target changes):
- `test_get_db_connection_no_asyncpg` — patch: `"app.asyncpg"` -> `"scrobblescope.cache.asyncpg"`
- `test_get_db_connection_connect_failure` — patch: `"app.asyncpg"` -> `"scrobblescope.cache.asyncpg"`
- `test_get_db_connection_no_database_url` — `patch.dict("os.environ", ...)` unchanged
- 4 others — no patches (mock connection objects)
- Import from `scrobblescope.cache`

**Changes to `app.py`:** Delete originals, add re-exports with `# noqa: F401`. Remove `try: import asyncpg` block.

**Changes to `test_app.py`:** Remove 14 tests. Remove `_batch_lookup_metadata`, `_batch_persist_metadata`, `_get_db_connection`, `cleanup_expired_jobs` from imports. Keep `JOBS`, `jobs_lock` (still used by route tests).

**Verify:** `pytest tests/ -q` (59 = 6 + 14 + 39), `pre-commit run --all-files`

---

### Slice 4: lastfm.py + spotify.py + test_services.py (9 tests)

**New files:** `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`, `tests/test_services.py`

**Extract to `lastfm.py`:**
- `check_user_exists()`, `fetch_recent_tracks_page_async()`, `fetch_pages_batch_async()`, `fetch_all_recent_tracks_async()`, `fetch_top_albums_async()`
- Internal imports from `config`, `domain`, `utils`, `repositories`

**Extract to `spotify.py`:**
- `fetch_spotify_access_token()`, `search_for_spotify_album_id()`, `fetch_spotify_album_details_batch()`
- Internal imports from `config`, `utils`

**Move to `test_services.py` (9 tests):**

4 Last.fm tests — patch target changes:
| Old | New |
|-----|-----|
| `"app.get_cached_response"` | `"scrobblescope.lastfm.get_cached_response"` |
| `"app.get_lastfm_limiter"` | `"scrobblescope.lastfm.get_lastfm_limiter"` |
| `"app.asyncio.sleep"` | `"asyncio.sleep"` |
| `"aiohttp.ClientSession.get"` | unchanged (global mock) |

3 Spotify tests — patch target changes:
| Old | New |
|-----|-----|
| `"app.get_spotify_limiter"` | `"scrobblescope.spotify.get_spotify_limiter"` |
| `"app.asyncio.sleep"` | `"asyncio.sleep"` |

2 `check_user_exists` tests — `"aiohttp.ClientSession.get"` unchanged.

**Changes to `app.py`:** Delete originals, add re-exports with `# noqa: F401`.

**Verify:** `pytest tests/ -q` (59 = 6 + 14 + 9 + 30), `pre-commit run --all-files`

---

### Slice 5: orchestrator.py + remaining service tests (10 tests -> test_services.py)

**New file:** `scrobblescope/orchestrator.py`

**Extract:**
- `process_albums()` (lines 1432-1803)
- `_fetch_and_process()` (lines 796-964)
- `background_task()` (lines 967-1000)
- Internal imports from `cache`, `config`, `domain`, `lastfm`, `repositories`, `spotify`, `utils`

**Move to `test_services.py` (10 more tests, total 19):**

All 10 tests require patch target changes from `"app.X"` to `"scrobblescope.orchestrator.X"`:

7 `process_albums` tests — example changes:
| Old | New |
|-----|-----|
| `"app._get_db_connection"` | `"scrobblescope.orchestrator._get_db_connection"` |
| `"app._batch_lookup_metadata"` | `"scrobblescope.orchestrator._batch_lookup_metadata"` |
| `"app._batch_persist_metadata"` | `"scrobblescope.orchestrator._batch_persist_metadata"` |
| `"app.fetch_spotify_access_token"` | `"scrobblescope.orchestrator.fetch_spotify_access_token"` |
| `"app.create_optimized_session"` | `"scrobblescope.orchestrator.create_optimized_session"` |
| `"app.search_for_spotify_album_id"` | `"scrobblescope.orchestrator.search_for_spotify_album_id"` |
| `"app.fetch_spotify_album_details_batch"` | `"scrobblescope.orchestrator.fetch_spotify_album_details_batch"` |

2 `_fetch_and_process` tests — additional changes:
| Old | New |
|-----|-----|
| `"app.fetch_top_albums_async"` | `"scrobblescope.orchestrator.fetch_top_albums_async"` |
| `"app.process_albums"` | `"scrobblescope.orchestrator.process_albums"` |
| `"app.asyncio.sleep"` | `"asyncio.sleep"` |

1 `background_task` structural test:
| Old | New |
|-----|-----|
| `"app._fetch_and_process"` | `"scrobblescope.orchestrator._fetch_and_process"` |
| `"app.threading.Thread"` | `"scrobblescope.orchestrator.threading.Thread"` |

**Changes to `app.py`:** Delete originals, add re-exports with `# noqa: F401`.

**Verify:** `pytest tests/ -q` (59 = 6 + 14 + 19 + 20), `pre-commit run --all-files`

---

### Slice 6: routes.py (Blueprint) + test_routes.py + app.py -> create_app()

**New files:** `scrobblescope/routes.py`, `tests/test_routes.py`

**Extract to `routes.py`:**
```python
from flask import Blueprint
bp = Blueprint("main", __name__)
```
- All 8 route handlers: `home`, `validate_user`, `progress`, `unmatched`, `reset_progress`, `results_complete`, `unmatched_view`, `results_loading`
- `get_filter_description()` helper
- `@bp.app_context_processor inject_current_year()`
- `@bp.app_errorhandler(404)` and `@bp.app_errorhandler(500)`
- Internal imports from `lastfm`, `orchestrator`, `repositories`, `utils`

**Transform `app.py` into factory:**
```python
from dotenv import load_dotenv
load_dotenv()
# ... logging setup (stays at module level) ...

import os
from flask import Flask

def create_app():
    application = Flask(__name__)
    application.secret_key = os.getenv("SECRET_KEY", "dev")
    from scrobblescope.routes import bp
    application.register_blueprint(bp)
    return application

app = create_app()  # Gunicorn backward compat

if __name__ == "__main__":
    from scrobblescope.config import ensure_api_keys
    ensure_api_keys()
    import webbrowser
    url = "http://127.0.0.1:5000/"
    print(f"Your app is live at: {url}")
    webbrowser.open(url)
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
```

**Remove ALL `# noqa: F401` re-exports from `app.py`.** They are no longer needed because `test_app.py` is being deleted.

**Update `tests/conftest.py` fixture:**
```python
from app import create_app

@pytest.fixture
def client():
    test_app = create_app()
    test_app.config["TESTING"] = True
    with test_app.test_client() as c:
        yield c
```

**Move to `test_routes.py` (20 tests) — patch target changes:**

Only 3 tests have `app.X` patches:
| Test | Old | New |
|------|-----|-----|
| `test_validate_user_success` | `"app.run_async_in_thread"` | `"scrobblescope.routes.run_async_in_thread"` |
| `test_validate_user_not_found` | `"app.run_async_in_thread"` | `"scrobblescope.routes.run_async_in_thread"` |
| `test_results_loading_valid_post` | `"app.threading.Thread"` | `"scrobblescope.routes.threading.Thread"` |

The `test_results_loading_valid_post` identity check `call_kwargs["target"] is background_task` still works because `routes.py` imports `background_task` from `scrobblescope.orchestrator` — same function object.

17 other route tests have no `app.X` patches (they use the test client + direct repository calls).

**Delete `tests/test_app.py`.**

**Verify:** `pytest tests/ -q` (59 = 6 + 14 + 19 + 20), `pre-commit run --all-files`, `python -c "from app import app; print(app)"`

---

### Slice 7: Cleanup and Documentation

1. **Verify `app.py` is minimal** (~80 lines: dotenv, logging, `create_app()`, `app = create_app()`, `__main__` block)
2. **Verify Dockerfile** — `gunicorn app:app` unchanged, works
3. **Verify fly.toml** — `release_command = "python init_db.py"` unchanged
4. **Verify `.flake8`** — `scrobblescope/` not excluded (correct)
5. **Update `EXECUTION_PLAYBOOK_2026-02-11.md`** — mark Batch 8 complete, add execution log entry
6. **Update `.claude/SESSION_CONTEXT.md`** — update batch status, code locations, test structure
7. **Update `README.md`** — update project file structure section

---

## Verification Checklist (after each slice)

```
pytest tests/ -q                       # 59 tests pass
pre-commit run --all-files             # black, isort, autoflake, flake8 pass
python -c "from app import app"        # Gunicorn import works
```

---

## Key Files Reference

| File | Role |
|------|------|
| `app.py` | Monolith being decomposed (~2091 lines currently) |
| `tests/test_app.py` | Monolith test file being split (~1500 lines, 59 tests) |
| `pyproject.toml` | pytest config (`pythonpath = "."`) |
| `Dockerfile` | Production entry: `gunicorn app:app` |
| `.pre-commit-config.yaml` | autoflake with `--remove-all-unused-imports` (re-export risk) |
| `.flake8` | `F401` ignored (helps during transition) |
| `init_db.py` | DB schema init (independent, unchanged) |
| `fly.toml` | Fly.io deployment config (unchanged) |

---

## Notes for Resuming Agent

- Read this file first, then `SESSION_CONTEXT.md` and `EXECUTION_PLAYBOOK_2026-02-11.md`
- Check `git status` — working tree should be clean (only `nul` artifact untracked)
- Run `pytest tests/ -q` and `pre-commit run --all-files` before starting
- Execute slices **one at a time**, verifying after each
- The `# noqa: F401` pattern is critical — autoflake WILL strip re-exports without it
- When moving tests, update patch targets simultaneously (this is the #1 risk area)
- The `asyncio.sleep` patches: `"app.asyncio.sleep"` patches the singleton module object, so `"asyncio.sleep"` is the cleanest form when moving tests
