# Comprehensive Audit Report for ScrobbleScope

## Overview
ScrobbleScope is a Python/Flask-based web application that fetches a user's listening history (scrobbles) from Last.fm, enriches the data with metadata (release year, album art, track runtimes) using the Spotify API, and displays top albums filtered by various user-defined criteria. It is designed to be deployed on Fly.io, utilizing `gunicorn`, an optional PostgreSQL database for Spotify metadata caching, and an in-memory job management system to handle background processing of user requests without blocking the main web threads.

This audit focuses on SoC (Separation of Concerns), DRY (Don't Repeat Yourself), Standard Coding Practices, Performance, Security, Repo Hygiene, Code Health, and Deployment Configuration.

---

## 1. SoC (Separation of Concerns) and Application Architecture

**Findings:**
- **Good Patterns:** The project has undergone a significant refactor recently. Route handlers in `routes.py` are mostly thin, delegating complex processing to `orchestrator.py` (`background_task`). External API clients (`lastfm.py`, `spotify.py`) are reasonably decoupled from the orchestration logic. Database access is centralized in `cache.py`.
- **Background Processing:** The application uses an in-memory `JOBS` dictionary (in `repositories.py`) for state management, protected by a `threading.Lock`. Background tasks run in daemon threads (managed by `worker.py`), which is suitable for the `shared-cpu-2x / 512MB` constraint on Fly.io, avoiding the overhead of a separate Celery/Redis worker stack.
- **Concern:** `orchestrator.py` is quite large and handles many different levels of abstraction: managing the job state (`set_job_progress`, `set_job_error`), directing the business logic flow, interacting with the DB cache, and even applying pre/post slicing logic. The `process_albums` function in `orchestrator.py` mixes caching logic (DB lookups/persists) with the business logic of grouping hits/misses and building results.

**Suggestions (Non-Breaking):**
1. **Further Decouple `orchestrator.py`:** While already improved, `orchestrator.py` could be further refined by moving the caching orchestration (Phases 1-4 of `process_albums`) into a dedicated service (e.g., `services/album_enrichment.py`), leaving `orchestrator.py` strictly responsible for high-level pipeline coordination and job state updates.
2. **Abstract Job State Management in Orchestrator:** Currently, `orchestrator.py` calls `set_job_progress`, `set_job_stat`, etc., directly scattered throughout the logic. A dedicated context manager or wrapper class representing the "Job Context" could encapsulate these calls, ensuring consistent state updates and reducing boilerplate in the main flow.

---

## 2. DRY (Don't Repeat Yourself)

**Findings:**
- **Templates:** Jinja2 templates use `base.html` to avoid repeating structural HTML.
- **Error Handling:** The `_classify_exception_to_error_code` function in `orchestrator.py` standardizes error handling, which is good. `scrobblescope.errors` defines `ERROR_CODES` centrally.
- **API Retries:** The `retry_with_semaphore` utility in `utils.py` is an excellent example of DRY, consolidating retry logic, backoff, jitter, and semaphore gating into a single reusable function used by both Last.fm and Spotify clients.
- **Rate Limiting:** `_GlobalThrottle` and `_ThrottledLimiter` in `utils.py` correctly consolidate rate limiting logic.

**Suggestions (Non-Breaking):**
1. **Form Parameter Extraction:** In `routes.py`, `results_complete`, `unmatched_view`, and `results_loading` all manually extract and convert form/job parameters (e.g., year, min_plays, etc.). This could be fully centralized into a single dataclass or validation function (like `_extract_job_params`, but expanded to handle type conversions and defaults consistently for both initial POST and results rendering).

---

## 3. Performance & Concurrency

**Findings:**
- **Concurrency Management:** The app correctly uses `asyncio` for I/O bound tasks (API calls) within background threads. `threading.BoundedSemaphore` (`MAX_ACTIVE_JOBS` = 10) prevents server overload.
- **Connection Pooling:** `create_optimized_session()` in `utils.py` configures `aiohttp.TCPConnector` properly (limits connections, caches DNS), which is crucial for performance.
- **Caching:** In-memory caching for Last.fm responses (`REQUEST_CACHE`) and persistent PostgreSQL caching for Spotify metadata (`spotify_cache`).
- **Memory Management:** `cleanup_expired_cache()` and `cleanup_expired_jobs()` are actively used to prevent memory leaks, critical for the 512MB Fly.io limit.
- **Database Connection Handling:** `cache.py` uses raw `asyncpg` queries rather than an ORM, which is highly performant. The retry/backoff logic for DB connections (`_get_db_connection`) handles Fly.io's "scale-to-zero" wake-up latency well.

**Concerns:**
- **Event Loop Management:** `background_task` in `orchestrator.py` creates a new event loop per thread. While functional, creating and destroying event loops frequently can have slight overhead.
- **Sorting Large Datasets:** When `sort_mode == "playtime"`, the app caps processing at 500 albums (`_PLAYTIME_ALBUM_CAP`). This is a pragmatic, necessary performance optimization to avoid overwhelming the Spotify API with detailed track duration lookups for long tails.

**Suggestions (Non-Breaking):**
1. **Optimize DB Batching:** The `_batch_persist_metadata` and `_batch_lookup_metadata` functions use `unnest` which is highly efficient for Postgres. Ensure appropriate composite indexes exist on `(artist_norm, album_norm)` in the database schema (assumed to be handled in `init_db.py`).
2. **Refine Domain Name Normalization:** In `domain.py`, `normalize_name` currently creates `string.maketrans` inside the function call. Moving `translator = str.maketrans(...)` and `album_metadata_words` to module-level constants will save overhead during tight loops (as noted in Memory context).

---

## 4. Security

**Findings:**
- **CSRF Protection:** Flask-WTF `CSRFProtect` is enabled for all mutating routes.
- **Secret Key Handling:** `_validate_secret_key` in `app.py` enforces a strong secret key in production, refusing to start otherwise. This is excellent practice.
- **XSS Prevention:** The README notes use of Jinja's `|tojson` filter and `escapeHtml()` in JS, standard security practices.
- **Database Injection:** `asyncpg` queries use parameterized inputs (`$1`, `$2`), preventing SQL injection.

**Concerns:**
- No glaring security holes identified in the backend logic.

**Suggestions (Non-Breaking):**
1. **Dependency Scanning:** Ensure a mechanism (like Dependabot or a GitHub Action) is in place to scan `requirements.txt` for known vulnerabilities.

---

## 5. Repo Hygiene and Code Health

**Findings:**
- **Code Quality Tools:** Uses `flake8`, `black`, `isort`, `autoflake`, and `pre-commit`.
- **Documentation:** The `README.md` is exceptional—clear, comprehensive, and up-to-date. `DEVELOPMENT.md`, `DEPLOY.md`, and `PLAYBOOK.md` suggest a highly organized project.
- **Testing:** 350 tests with ~72% coverage is very solid.
- **Logging:** Proper use of the `logging` module throughout instead of `print` statements.

**Concerns:**
- **Test Organization:** Unit tests for DB helpers (in `cache.py`) are placed in `tests/test_repositories.py` (as per Memory context). This is a slight naming mismatch but functional.

**Suggestions (Non-Breaking):**
1. **Type Hinting:** While Python 3.13 is the target, type hints are sparse in core files (e.g., `orchestrator.py`, `routes.py`). Gradually adding `typing` to function signatures will improve editor support and catch bugs earlier without breaking runtime.

---

## 6. Deployment Configuration

**Findings:**
- **Fly.io Settings (`fly.toml`):**
  - `auto_stop_machines = 'stop'` and `auto_start_machines = true` allow scale-to-zero, saving costs.
  - `release_command = "python init_db.py"` ensures the DB schema is up-to-date automatically before the new version goes live.
- **Gunicorn (`Dockerfile`):**
  - Uses `gunicorn --workers 1 --threads 4`. This is the *correct* configuration for an app relying on in-memory shared state (`JOBS` dict). If `workers > 1`, background jobs would be isolated to separate processes, breaking the progress polling mechanism unless a persistent store (Redis) was used.

**Concerns:**
- None. The deployment configuration aligns perfectly with the application's architectural constraints (in-memory job state).

---

## Priority Action Items (Pre-Feature implementations)

1. **Low Hanging Fruit (Performance):** Move the translation table and word sets in `scrobblescope/domain.py` to module-level constants to avoid recompilation on every track/album normalized. (Highest Priority - easy win).
2. **Refactoring (Code Health):** Standardize form parameter extraction in `scrobblescope/routes.py` to reduce boilerplate across the three main result/loading endpoints. (Medium Priority).
3. **Type Hinting (Code Health):** Begin adding basic type hints to `orchestrator.py` function signatures for better maintainability. (Low Priority).
