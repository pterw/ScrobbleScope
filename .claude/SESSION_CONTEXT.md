# ScrobbleScope Session Context (Post-Batch 4, Committed)

Last updated: 2026-02-12
Author: Claude Opus 4.6 (for agent handoff / new session bootstrap)

---

## 1. What is ScrobbleScope?

A Flask web app that fetches a user's Last.fm scrobble history for a given year, enriches album data with Spotify metadata (release dates, artwork, track runtimes), and presents filtered/sorted top-album rankings. Primary use case: building Album of the Year (AOTY) lists.

**Stack:** Python 3.13, Flask, aiohttp/aiolimiter (async API calls), Bootstrap 5, Jinja2 templates, pytest + pytest-asyncio.

**Deployment:** Fly.io (ephemeral VM, shared-cpu-2x @ 512MB). In-memory job state (no database yet).

---

## 2. Current state

| Item | Value |
|------|-------|
| Branch | `wip/pc-snapshot` |
| Latest commit | `c4e3dbb` (Batches 3+4: nested thread removal + 43 tests) |
| Working tree | **Clean** — all Batch 3+4 changes committed |
| Untracked files | `nul` (Windows artifact, ignorable) |
| Tests | **43 passing** (`pytest tests/test_app.py -q`) |
| Pre-commit | All hooks pass (black, isort, autoflake, flake8) |
| app.py line count | ~1790 lines (monolith, refactor planned for Batch 8) |

---

## 3. Documents to read (priority order)

| Document | Status | Purpose |
|----------|--------|---------|
| `EXECUTION_PLAYBOOK_2026-02-11.md` | **Source of truth** | Batch ordering, acceptance criteria, execution log, next steps. Read Sections 2, 9, and 10 first. |
| `.claude/SESSION_CONTEXT.md` (this file) | **Current** | Quick orientation for agents. Architecture, key locations, known gaps. |
| `README.md` | **Current** | Product description, roadmap checklist, setup instructions. |
| `.claude/BATCH3_CONTEXT.md` | **Stale** | Was written for Batch 3 implementation. Batch 3 is now complete. Historical reference only. |
| `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` | **Stale baseline** | Pre-Batch 3 audit. Some items it lists as "not done" are now done. Treat as historical context. |

---

## 4. Batch completion status

| Batch | Task | Status | Commit/Notes |
|-------|------|--------|--------------|
| 1 | Upstream failure classification + retry UX | Done | `130c0b8` |
| 2 | Personalized min listening year from registration date | Done | `5d3e25f` |
| 3 | Remove nested thread pattern | Done | `c4e3dbb` |
| 4 | Expand test coverage (12 → 43 tests, gaps closed) | Done | `c4e3dbb` |
| 5 | Docstring + comment normalization | Done | 16 docstrings added, 11 stale comments removed |
| **6** | **Frontend refinement/tweaks** | **Next** | Includes `index.html` error= gap fix |
| 7 | Persistent metadata layer (Postgres) | Pending | |
| 8 | Modular refactor (Blueprints, services/, utils.py) | Pending | |

---

## 5. Known gaps (all prior gaps closed)

All Batch 4 coverage gaps (reset_progress route, service-level retry/error mapping)
were closed in the Batch 4 closure addendum. No outstanding gaps remain for Batch 6.

---

## 6. Architecture overview

### Request flow
```
User submits form (index.html)
  → POST /results_loading
    → Creates job (UUID in JOBS dict)
    → Spawns daemon Thread(target=background_task)
    → Renders loading.html with job_id via tojson bridge

background_task (Thread):
  → Creates asyncio event loop
  → loop.run_until_complete(_fetch_and_process(...))
    → Fetch Last.fm scrobbles (paginated, async)
    → Group into albums, filter by thresholds
    → Search Spotify for each album (async, rate-limited)
    → Fetch Spotify album details batch (async)
    → Store results via set_job_results()

loading.js polls GET /progress?job_id=...
  → On 100% + no error → POST /results_complete
  → On error + retryable → show Retry button
  → On error + not retryable → auto-redirect

POST /results_complete
  → Reads job context, renders results.html with tojson bridge
```

### Key data structures

**JOBS dict** (in-memory, `jobs_lock` for thread safety):
```python
JOBS[job_id] = {
    "created_at": float,
    "updated_at": float,
    "progress": {
        "progress": int,       # 0-100
        "message": str,
        "error": bool,
        "stats": dict,         # scrobbles_fetched, albums_found, spotify_matched
        # On error only:
        "error_code": str,     # e.g. "lastfm_unavailable"
        "error_source": str,   # "lastfm" or "spotify"
        "retryable": bool,
        "retry_after": int,    # seconds (optional)
    },
    "results": list | None,    # Album dicts when done
    "unmatched": dict,         # Keyed by "artist::album"
    "params": dict,            # Original search parameters
}
```

**ERROR_CODES dict** (line 63): Maps error codes to source, retryability, message template.

**Rate limiters:** `WeakKeyDictionary` keyed by event loop. Each background task creates its own loop → gets its own limiter → limiter is GC'd when loop closes.

**REQUEST_CACHE:** In-memory dict with 1-hour TTL, cleaned at start of each background task.

---

## 7. Key code locations in app.py

| What | Line(s) | Notes |
|------|---------|-------|
| `ERROR_CODES` dict | ~63-89 | Error classification for upstream failures |
| `_get_loop_limiter` / `get_lastfm_limiter` / `get_spotify_limiter` | ~92-120 | Loop-scoped rate limiters |
| `run_async_in_thread` | ~124-146 | Used ONLY by `/validate_user`. NOT used by background_task anymore (Batch 3). |
| Job state functions | ~200-378 | `create_job`, `set_job_progress`, `set_job_error`, `set_job_stat`, `set_job_results`, `add_job_unmatched`, `get_job_progress`, `get_job_context`, etc. |
| `normalize_name` | ~485-522 | Artist/album name normalization (strips suffixes, punctuation, preserves Unicode) |
| `normalize_track_name` | ~526-532 | Track name normalization for cross-service matching |
| `/` (home) | 535 | GET → renders index.html |
| `/validate_user` | 542-573 | GET → async check via `run_async_in_thread` |
| `/progress` | 576-607 | GET → returns job progress JSON |
| `/unmatched` | 610-624 | GET → returns unmatched albums JSON |
| `/reset_progress` | 627-638 | POST → resets job state (NO TESTS - Gap 1) |
| `_fetch_and_process` | ~670-840 | Top-level async function (extracted in Batch 3). ALL the actual work. |
| `background_task` | ~843-876 | Creates event loop, runs `_fetch_and_process`. Called by Thread from `results_loading`. |
| `_extract_registered_year` | ~880-886 | Parses Last.fm registration timestamp |
| `check_user_exists` | ~889-930 | Async user check with registration year |
| `fetch_recent_tracks_page_async` | ~932+ | Last.fm page fetch with retry (NO TESTS - Gap 2) |
| `search_for_spotify_album_id` | ~1168+ | Spotify album search with 429 retry (NO TESTS - Gap 2) |
| `fetch_spotify_album_details_batch` | ~1222+ | Spotify batch details with retry (NO TESTS - Gap 2) |
| `/results_complete` | ~1539-1640 | POST → renders results.html or error.html |
| `get_filter_description` | ~1644-1657 | Human-readable filter description |
| `/unmatched_view` | ~1661-1724 | POST → renders unmatched.html |
| `/results_loading` | ~1729-1798 | POST → creates job, spawns background thread, renders loading.html |

---

## 8. Test file structure (tests/test_app.py)

43 tests organized in sections:

```
# Existing (12, from Batches 1-2):
  test_home_page
  test_normalize_name_simple
  test_check_user_exists_success          (async)
  test_check_user_does_not_exist          (async)
  test_validate_user_success
  test_validate_user_missing_username
  test_results_complete_renders_no_matches_for_empty_results
  test_set_job_error_sets_classified_fields
  test_set_job_error_user_not_found_not_retryable
  test_results_complete_error_with_error_code
  test_progress_endpoint_returns_error_metadata
  test_progress_endpoint_no_error_metadata_on_success

# Job lifecycle (5, Batch 4):
  test_create_job_returns_unique_ids
  test_job_isolation_separate_progress
  test_set_job_progress_missing_job_returns_false
  test_set_job_stat_stores_and_retrieves
  test_expired_job_cleanup

# Route coverage (15, Batch 4 + closure addendum):
  test_progress_missing_job_id_returns_400
  test_progress_invalid_job_id_returns_404
  test_results_loading_valid_post          (verifies Thread target + tojson bridge)
  test_results_loading_missing_username
  test_results_loading_year_out_of_bounds
  test_results_complete_missing_job_id
  test_results_complete_expired_job
  test_results_complete_with_results_renders_data  (verifies tojson bridge)
  test_validate_user_too_long_username
  test_validate_user_not_found
  test_unmatched_endpoint_missing_job_id
  test_unmatched_endpoint_returns_data
  test_reset_progress_missing_job_id_returns_400
  test_reset_progress_nonexistent_job_returns_404
  test_reset_progress_success_resets_job_state

# Normalization (3, Batch 4):
  test_normalize_name_remastered_suffix
  test_normalize_name_unicode_preserved
  test_normalize_track_name_strips_punctuation

# Registration year (2, Batch 4):
  test_extract_registered_year_valid
  test_extract_registered_year_missing_key

# Background task structural (1, Batch 4):
  test_background_task_runs_single_event_loop  (Batch 3 regression guard)

# Service-level retry/error mapping (5, Batch 4 closure addendum):
  test_fetch_recent_tracks_page_retries_429_then_succeeds
  test_fetch_recent_tracks_page_404_raises_user_not_found
  test_search_for_spotify_album_id_retries_429_then_returns_id
  test_fetch_spotify_album_details_batch_retries_429_then_succeeds
  test_fetch_spotify_album_details_batch_non_200_returns_empty_dict
```

**Shared fixture:** `_TEST_JOB_PARAMS` dict for creating test jobs.
**Test username:** `flounder14` (real user, registered 2016).
**Mock patterns:**
- `patch("app.run_async_in_thread")` for `/validate_user` tests
- `patch("app.threading.Thread")` for `/results_loading` tests
- `patch("app._fetch_and_process", new_callable=AsyncMock)` for `background_task` structural test
- `patch("aiohttp.ClientSession.get")` for async `check_user_exists` tests

---

## 9. Template tojson bridges

Two templates inject server data into JS via Jinja2 `|tojson`:

**loading.html** (line 14-25):
```html
<script>
  window.SCROBBLE = {{ { "job_id": ..., "username": ..., ... } | tojson }};
</script>
```

**results.html** (line 13-17):
```html
<script>
  window.APP_DATA = {{ { "username": ..., "year": ..., "job_id": ... } | tojson }};
</script>
```

Both are verified by route tests (`test_results_loading_valid_post`, `test_results_complete_with_results_renders_data`).

---

## 10. Known UX gaps for Batch 6

1. **`index.html` doesn't render `error=` variable** — `results_loading` passes `error="Username and year are required."` but the template has no block to display it. The page re-renders silently. Noted in playbook Batch 6 tasks.

2. **Mobile dark-mode toggle overlap** — Fixed position toggle can overlap content on small screens.

3. **Encoding artifacts in JS strings** — Minor cleanup needed.

---

## 11. Environment notes

- **Python 3.13.3** on Windows 11
- **Pre-commit hooks:** black, isort, autoflake, flake8, trailing whitespace, end-of-file, check yaml
- **pytest config** in `pyproject.toml` with `asyncio_mode = "strict"`
- **API keys** in `.env` (not committed): `LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`
- The `nul` file in the repo root is a Windows artifact (can be ignored/deleted)

---

## 12. Agent checklist before starting work

1. Read this file and `EXECUTION_PLAYBOOK_2026-02-11.md` (Sections 2, 9, 10)
2. Confirm repo is green: `pre-commit run --all-files` && `pytest tests/test_app.py -q`
3. Check `git status` for uncommitted work — Batches 3+4 may still be uncommitted
4. Read the relevant section(s) of `app.py` before editing
5. Implement one batch at a time
6. After each batch: update playbook (Section 2, 9, 10), update README checklist
7. Follow docstring style from existing tests (GIVEN/WHEN/THEN pattern)
