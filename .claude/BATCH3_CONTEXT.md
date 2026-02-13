# Batch 3 Context: Remove Nested Thread Pattern

## Session State (as of commit d1933cf)

**Branch:** `wip/pc-snapshot`
**All tests:** 12/12 passing
**Pre-commit:** All hooks pass (black, isort, autoflake, flake8)
**Working tree:** Clean — no uncommitted changes

### Commits this session (oldest → newest)
```
130c0b8 Add upstream failure classification and retry UX (Batch 1)
5d3e25f Add dynamic year validation from registration date and UX refinements
d1933cf Mark Batch 1 and Batch 2 as complete in README roadmap
```

### Batches completed
- **Batch 1** (commit 130c0b8): Upstream failure classification + retry UX
  - `ERROR_CODES` dict, `set_job_error()` helper, `set_job_progress()` extended with error_code/error_source/retryable/retry_after
  - `fetch_all_recent_tracks_async` returns `(pages, metadata)` tuple
  - `fetch_top_albums_async` returns `(filtered_albums, fetch_metadata)` tuple
  - `background_task` classifies errors instead of silent failures
  - Loading page: retry button for transient errors, auto-redirect for non-retryable, partial-data warning
  - 5 new tests (12 total)

- **Batch 2** (commit 5d3e25f): Dynamic year validation from registration date
  - `check_user_exists()` returns `{"exists": bool, "registered_year": int|None}` (was `True/False`)
  - `_extract_registered_year()` helper parses `user.getinfo` `registered.unixtime`
  - `/validate_user` includes `registered_year` in JSON response
  - `index.js`: full validation rewrite — 4-digit gate, no green styling on valid, clear on empty, non-numeric instant warn
  - Custom Release Year: same validation, min changed from 1950 → 1900
  - Decade cross-validation: pills disable when decade starts after listening year
  - `inputmode="numeric"` on both year inputs for mobile
  - Server-side year bounds guard (2002 to current_year) in `results_loading`
  - `from datetime import datetime, timezone` (fixed `utcfromtimestamp` deprecation)
  - 3 existing tests updated for new `check_user_exists` return type

---

## Batch 3: Remove Nested Thread Pattern

### The problem

The current execution flow for a search request creates **two threads** per request:

```
Flask request (main thread)
  └─ results_loading route (line 1707)
       └─ threading.Thread(target=background_task)     ← Thread 1 (outer)
            └─ background_task (line 670)
                 └─ run_async_in_thread(fetch_and_process)  (line 849)
                      └─ threading.Thread(target=runner)     ← Thread 2 (inner)
                           └─ asyncio.new_event_loop()
                                └─ loop.run_until_complete(fetch_and_process())
```

Thread 1 just blocks on `thread.join()` doing nothing while Thread 2 runs the event loop. This wastes a thread per request.

### Key code locations in app.py

| What | Line | Description |
|------|------|-------------|
| `run_async_in_thread()` | 124-146 | Creates a thread + event loop to run an async coroutine synchronously |
| `validate_user` route | 542-570 | Uses `run_async_in_thread` to call `check_user_exists` — **legitimate use, keep** |
| `background_task()` | 670-849 | Sync wrapper that contains nested `async def fetch_and_process()` |
| `fetch_and_process()` | 682-847 | Nested async closure — does ALL the actual work |
| `return run_async_in_thread(fetch_and_process)` | 849 | The unnecessary inner thread creation |
| `results_loading` route | 1707-1779 | Creates outer `threading.Thread(target=background_task)` |

### The fix (3 changes)

**Change 1: Extract `fetch_and_process` to top-level async function**

Currently `fetch_and_process` is a nested closure inside `background_task`. It captures all parameters from `background_task`'s signature. Extract it as:

```python
async def _fetch_and_process(
    job_id, username, year, sort_mode, release_scope,
    decade=None, release_year=None, min_plays=10, min_tracks=3, limit_results="all",
):
    """Fetch and process albums in the background for a single job."""
    try:
        # ... all the existing async logic unchanged ...
    except Exception as exc:
        # ... existing error handling unchanged ...
```

**Change 2: Rewrite `background_task` to run the loop directly**

```python
def background_task(
    job_id, username, year, sort_mode, release_scope,
    decade=None, release_year=None, min_plays=10, min_tracks=3, limit_results="all",
):
    """Run the async fetch-and-process pipeline in a dedicated event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _fetch_and_process(
                job_id, username, year, sort_mode, release_scope,
                decade, release_year, min_plays, min_tracks, limit_results,
            )
        )
    except Exception:
        logging.exception(f"Unhandled error in background task for {username}/{year}")
    finally:
        loop.close()
```

No return value needed — nobody reads it. The outer `threading.Thread` in `results_loading` doesn't capture it. All results are stored via `set_job_results()` inside the async function.

**Change 3: Keep `run_async_in_thread` for `/validate_user` only**

`run_async_in_thread` stays as-is. It's still used by `validate_user` (line 555) which is a synchronous Flask route that needs to call `check_user_exists` (async) and block until it returns. That's a legitimate one-off blocking call during request handling.

### What does NOT change
- All async logic inside `_fetch_and_process` (the ~170 lines of fetch/process pipeline)
- The outer `threading.Thread` in `results_loading` — Flask needs it
- `run_async_in_thread` function itself
- `/validate_user` route's usage of `run_async_in_thread`
- `WeakKeyDictionary` rate limiters (still keyed by event loop, still correct)
- All 12 existing tests — no new tests needed for this batch

### Risk assessment
- **Low risk**: async logic is completely untouched
- **Verify**: error handling works — currently `_fetch_and_process` has its own try/except that calls `set_job_error()`. The outer `background_task` try/except is a safety net for truly unexpected errors
- **Verify**: `asyncio.set_event_loop(loop)` in the new `background_task` — needed for `_get_loop_limiter()` which calls `asyncio.get_running_loop()`

### Verification steps
1. `pytest tests/test_app.py -v` — all 12 pass
2. `pre-commit run --all-files` — all hooks pass
3. Manual: run a normal search — identical behavior
4. Manual: set invalid API keys — error classification still works

---

## What comes next (Batches 4-8 from EXECUTION_PLAYBOOK_2026-02-11.md)

| Batch | Task | Status |
|-------|------|--------|
| ~~1~~ | ~~Upstream failure classification + retry UX~~ | Done (130c0b8) |
| ~~2~~ | ~~Personalized min listening year~~ | Done (5d3e25f) |
| **3** | **Remove nested thread pattern** | **Next** |
| 4 | Expand unit test coverage | Pending |
| 5 | Backend docstrings | Pending |
| 6 | Frontend tweaks (mobile, QA) | Pending |
| 7 | Persistent metadata layer (Postgres) | Pending |
| 8 | Modular refactor (Blueprints, services/, utils.py, tasks.py, config.py) | Pending |

---

## Key architecture notes

- **app.py** is the monolith (~1630 lines). Everything lives here until Batch 8.
- **JOBS dict** (line ~188): `{job_id: {progress, results, unmatched, params, ...}}`, protected by `jobs_lock`, 2-hour TTL
- **Rate limiters**: `WeakKeyDictionary` keyed by event loop. Each background task creates its own loop → gets its own limiter → limiter is GC'd when loop closes.
- **Cache**: `REQUEST_CACHE` with 1-hour TTL, cleaned at start of each background task
- **Error codes**: `ERROR_CODES` dict (line 63), `set_job_error()` helper (line 249)
- **Tests**: 12 tests in `tests/test_app.py`. Test `validate_user` mocks `run_async_in_thread` at `app.run_async_in_thread` — this mock path stays valid since `run_async_in_thread` isn't being removed.

## Files overview

| File | Role |
|------|------|
| `app.py` | Flask app, all routes, all async pipelines, job state, caching |
| `static/js/index.js` | Form validation, dark mode, decade pills, year validation |
| `static/js/loading.js` | Progress polling, error display, retry, live stats |
| `static/js/results.js` | Results page: CSV export, image capture, unmatched modal, escapeHtml |
| `static/js/error.js` | Error page dark mode |
| `templates/index.html` | Search form |
| `templates/loading.html` | Progress bar, live stats, error container, retry button |
| `templates/results.html` | Album results table |
| `templates/base.html` | Master template (dark mode toggle, shared blocks) |
| `tests/test_app.py` | 12 tests: home page, normalize, user exists, validate_user, job errors |
