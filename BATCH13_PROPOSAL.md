# Batch 13: Internal Decomposition and Coverage Hardening (2026-02-23)

## 1. Scope and goals

Primary goals:
- Fill the `worker.py` direct-unit-test gap before any refactoring begins.
- Decompose two large private functions in `orchestrator.py` into focused,
  named sub-functions without changing any public interface.
- Split the 1,270-line `test_orchestrator_service.py` to track the decomposed
  source structure.
- Eliminate the DRY violation in the async retry loop shared by `lastfm.py`
  and `spotify.py`.

Out of scope for Batch 13:
- Feature additions (Top Songs, Listening Heatmap) -- requires owner scope
  definition and a dedicated batch.
- Jules integration -- no source code changes; purely a GitHub/Google Cloud
  setup task that can be done independently at any time.
- Smoke test CI integration -- `scripts/smoke_cache_check.py` works correctly
  as a manual pre-deploy check; CI integration requires running a live Flask
  server (via `flask run --port 5000 &`) or a Docker-compose harness;
  deferred to a dedicated DevOps batch once the infrastructure approach is
  decided.
- In-memory `REQUEST_CACHE` size cap -- no max-size eviction exists, but at
  the current scale (<=10 concurrent jobs, 512 MB Fly.io VM, 1-hour TTL) the
  risk is low; deferred.
- Cross-agent orchestration methodology (`AGENTS.md`, `doc_state_sync.py`,
  SESSION_CONTEXT) -- stable post-Batch 12; no code changes warranted.
- `routes.py` source decomposition -- already well-factored (all helpers
  extracted in prior batches); no monolith concerns remain.
- Security audit remediation -- zero critical findings (no eval/exec/
  subprocess, no hardcoded secrets, parameterized SQL, env-based keys).

Ordering rationale:
This batch is intentionally placed BEFORE any feature work (Top Songs,
Heatmap). Cleaner, smaller functions are easier to extend; worker unit tests
provide a stronger safety net; the DRY retry utility will be a natural
dependency for any future API client. Feature batches (14+) will build on
the post-Batch-13 codebase.

Execution rules:
- Implement one work package at a time, in order.
- Checkpoint commits at each self-contained, tests-passing change.
- Validation before every commit:
  - `.\venv\Scripts\python.exe -m pytest -q`
  - `.\venv\Scripts\python.exe -m pre_commit run --all-files`
- Follow `AGENTS.md` commit rules (Conventional Commits, no co-author trailers).
- Update `PLAYBOOK.md` Section 3 (status) + Section 4 (dated log entry inside
  current-batch markers) after each WP.
- Update `SESSION_CONTEXT.md` Section 2 (test count, batch status) if changed.
- Run `.\venv\Scripts\python.exe scripts/doc_state_sync.py --fix` after doc
  edits.

---

## 2. Work packages

### WP-1 (P0): Add direct unit tests for worker.py

**Problem:** `worker.py` (43 lines, 3 functions) has no dedicated test file.
Coverage is indirect: `test_orchestrator_service.py` exercises slot
acquisition only through `background_task` integration tests. The three
functions have distinct failure paths that are untested in isolation:
`acquire_job_slot` returns `False` when the semaphore is exhausted;
`release_job_slot` swallows a `ValueError` on double-release and logs a
warning; `start_job_thread` releases the job slot if `Thread()` construction
raises before `.start()` is called.

**Files:**
- `tests/test_worker.py` (new)

**New test functions:**

| Test | Behavior under test |
|------|---------------------|
| `test_acquire_job_slot_succeeds_when_capacity_available` | Fresh semaphore: `acquire_job_slot()` returns `True` |
| `test_acquire_job_slot_fails_when_at_capacity` | Semaphore fully consumed: returns `False`, does not block |
| `test_release_job_slot_restores_capacity` | Acquire then release: subsequent acquire succeeds |
| `test_release_job_slot_logs_warning_on_double_release` | Release without prior acquire: `caplog` captures `WARNING` |
| `test_start_job_thread_creates_daemon_thread` | Thread is alive, `daemon=True`, target called |
| `test_start_job_thread_releases_slot_on_thread_construction_failure` | Patch `threading.Thread.__init__` to raise `RuntimeError`; verify slot released |

**Implementation steps:**
1. Create `tests/test_worker.py` with the 6 tests above. Use
   `unittest.mock.patch` to temporarily replace `_active_jobs_semaphore` with a
   `BoundedSemaphore(n)` of known capacity for isolation. Use `caplog` for
   the warning test. Checkpoint commit.

**Acceptance criteria:**
- 6 new tests pass.
- `worker.py` coverage is direct and explicit, not only inferred from
  orchestrator integration tests.
- No existing tests broken.

---

### WP-2 (P1): Extract search and batch-detail phases from `_fetch_spotify_misses()` in `orchestrator.py`

**Problem:** `_fetch_spotify_misses()` (L192-387, ~196 lines) contains three
sequential concerns separated only by inline comments: (1) token acquisition
with early-exit, (2) a parallel Spotify search loop mapped to progress 20-40%,
and (3) a parallel batch-detail-fetch loop mapped to progress 40-60%. The two
loops are each ~85-90 lines and capture variables (`session`, `token`) from the
enclosing scope via closures that are not named or testable in isolation.

**Files:**
- `scrobblescope/orchestrator.py`
- `tests/services/test_orchestrator_service.py` (new adversarial tests appended)

**New functions (placed immediately before `_fetch_spotify_misses()`):**

```python
async def _run_spotify_search_phase(
    job_id: str,
    session,
    cache_misses: dict,
    token: str,
    search_semaphore: asyncio.Semaphore,
) -> tuple[dict, dict]:
    """Parallel Spotify search for all cache misses.

    Reports progress in the 20-40% range. Registers unmatched albums via
    add_job_unmatched. Returns (spotify_id_to_key, spotify_id_to_original_data).
    """

async def _run_spotify_batch_detail_phase(
    job_id: str,
    session,
    valid_spotify_ids: list,
    token: str,
    spotify_id_to_key: dict,
    spotify_id_to_original_data: dict,
    cache_hits: dict,
) -> list:
    """Batch-fetch Spotify album details for all found IDs.

    Reports progress in the 40-60% range. Promotes enriched albums into
    cache_hits (mutated in place). Returns new_metadata_rows.
    """
```

The token-acquisition block (L199-217) stays inline in `_fetch_spotify_misses()`
-- it is 15 lines with no parallelism and forms a natural early-exit gate.

After extraction, `_fetch_spotify_misses()` becomes a ~25-line coordinator:

```python
async def _fetch_spotify_misses(job_id, cache_misses, cache_hits):
    if not cache_misses:
        return []
    token = await fetch_spotify_access_token()
    if not token:
        # ... token-failure block unchanged ...
        return []
    new_metadata_rows = []
    async with create_optimized_session() as session:
        search_semaphore = asyncio.Semaphore(SPOTIFY_SEARCH_CONCURRENCY)
        spotify_id_to_key, spotify_id_to_original_data = (
            await _run_spotify_search_phase(
                job_id, session, cache_misses, token, search_semaphore
            )
        )
        valid_spotify_ids = list(spotify_id_to_original_data.keys())
        if valid_spotify_ids:
            new_metadata_rows = await _run_spotify_batch_detail_phase(
                job_id, session, valid_spotify_ids, token,
                spotify_id_to_key, spotify_id_to_original_data, cache_hits,
            )
    return new_metadata_rows
```

**New adversarial tests (appended to `test_orchestrator_service.py`, moved in WP-4):**
1. `test_run_spotify_search_phase_all_misses_returns_empty_maps` -- all
   `search_for_spotify_album_id` calls return `None`; expect both dicts empty,
   every album registered as unmatched.
2. `test_run_spotify_batch_detail_phase_empty_id_list_skips_api_call` --
   `valid_spotify_ids=[]`; assert `fetch_spotify_album_details_batch` not
   called; returns `[]`.
3. `test_run_spotify_search_phase_progress_stays_in_20_to_40_range` --
   assert all `set_job_progress` calls from this function pass `progress`
   values in `[20, 40]`.

**Implementation steps:**
1. Extract `_run_spotify_search_phase` from the search-phase block (approx.
   L219-290). Thread all captured variables as explicit parameters. Checkpoint
   commit.
2. Extract `_run_spotify_batch_detail_phase` from the batch-detail block
   (approx. L292-385). Thread all captured variables as explicit parameters.
   Checkpoint commit.
3. Add the 3 adversarial tests to `test_orchestrator_service.py`. Checkpoint
   commit.

**Acceptance criteria:**
- All existing `_fetch_spotify_misses` tests pass without modification (patches
  on `search_for_spotify_album_id` and `fetch_spotify_album_details_batch`
  remain valid -- same module).
- 3 new adversarial tests pass.
- `orchestrator.py` line count for `_fetch_spotify_misses` drops from ~196 to
  ~25.

---

### WP-3 (P1): Extract five private helpers from `_fetch_and_process()` in `orchestrator.py`

**Problem:** `_fetch_and_process()` (L579-808, ~230 lines) mixes five
sequential concerns -- Last.fm stat recording, pre-slice/cap logic, Spotify
failure detection, post-slice truncation, and exception-to-error-code
classification -- that are untestable in isolation. The outer `try/except`
wraps all five, making it hard to verify any one branch without triggering the
entire pipeline.

**Files:**
- `scrobblescope/orchestrator.py`
- `tests/services/test_orchestrator_service.py` (new adversarial tests appended)

**New functions (placed immediately before `_fetch_and_process()`):**

```python
def _record_lastfm_stats(job_id: str, fetch_metadata: dict) -> None:
    """Write Last.fm aggregation stats and partial-data warning into the job."""
    # Replaces L632-642. Calls set_job_stat for each stat key.

def _apply_pre_slice(
    filtered_albums: dict,
    sort_mode: str,
    limit_results: str,
    release_scope: str,
) -> dict:
    """Apply pre-Spotify pre-slicing and playtime cap.

    Playcount pre-slice: only when sort_mode='playcount', release_scope='all',
    and limit_results is a valid integer. Playtime cap: fires at
    _PLAYTIME_ALBUM_CAP when sort_mode='playtime'. Returns the (possibly
    reduced) dict.
    """
    # Replaces L666-711.

def _detect_spotify_total_failure(
    job_id: str,
    results: list,
    filtered_albums: dict,
) -> bool:
    """Return True and set job error if all filtered albums had no Spotify match.

    Only fires when results is empty but filtered_albums is non-empty.
    Reads job unmatched state to count 'No Spotify match' entries.
    """
    # Replaces L739-747.

def _apply_post_slice(results: list, limit_results: str) -> list:
    """Truncate results to limit_results if it is a valid integer."""
    # Replaces L759-768. Logs warning on malformed limit_results value.

def _classify_exception_to_error_code(error_message: str) -> str | None:
    """Map an exception message to a classified error code, or None.

    Returns 'spotify_rate_limited', 'lastfm_rate_limited', 'user_not_found',
    or None for unclassified errors.
    """
    # Replaces L783-793. Pure function; no I/O.
```

Note: `_lastfm_progress` closure inside `_fetch_and_process()` stays inline.
It is 3 lines, captures `job_id` from the enclosing scope, and is not repeated
elsewhere. Extracting it would require threading `job_id` as an explicit
parameter for no practical gain.

**New adversarial tests (appended to `test_orchestrator_service.py`, moved in WP-4):**
1. `test_apply_pre_slice_playcount_all_scope_slices` -- 5 albums, limit=2,
   sort_mode='playcount', release_scope='all' -- expect 2 albums returned.
2. `test_apply_pre_slice_playcount_scoped_release_no_slice` -- same setup
   but release_scope='same' -- expect all 5 albums returned unchanged.
3. `test_apply_pre_slice_playtime_cap_fires` -- 501 albums, sort_mode='playtime'
   -- expect exactly `_PLAYTIME_ALBUM_CAP` (500) returned.
4. `test_apply_pre_slice_playtime_below_cap_unchanged` -- 5 albums,
   sort_mode='playtime' -- expect 5 returned.
5. `test_apply_post_slice_limits_results` -- 10 results, limit_results='5'
   -- expect 5 returned.
6. `test_apply_post_slice_malformed_limit_no_error` -- limit_results='banana'
   -- expect all results returned, no exception, warning logged.
7. `test_classify_exception_to_error_code_spotify_rate_limited` -- message
   contains "Too Many Requests" -- returns 'spotify_rate_limited'.
8. `test_classify_exception_to_error_code_user_not_found` -- message contains
   "user not found" -- returns 'user_not_found'.
9. `test_classify_exception_to_error_code_unclassified_returns_none` --
   "connection timeout" -- returns None.
10. `test_detect_spotify_total_failure_fires_when_all_unmatched` -- results
    empty, all filtered_albums have "No Spotify match" reason -- returns True,
    `set_job_error` called with 'all_unmatched'.
11. `test_detect_spotify_total_failure_does_not_fire_partial_match` -- results
    empty, only some albums unmatched -- returns False.

**Implementation steps:**
1. Extract `_classify_exception_to_error_code` (pure, no state risk).
   Checkpoint commit.
2. Extract `_apply_pre_slice` and `_apply_post_slice` (pure). Reassign return
   value in `_fetch_and_process`: `filtered_albums = _apply_pre_slice(...)`.
   Checkpoint commit.
3. Extract `_record_lastfm_stats` and `_detect_spotify_total_failure`.
   Checkpoint commit.
4. Add the 11 adversarial tests to `test_orchestrator_service.py`. Checkpoint
   commit.

**Acceptance criteria:**
- All existing `_fetch_and_process` integration tests pass without modification.
- 11 new adversarial tests pass.
- `_fetch_and_process()` line count drops from ~230 to ~80.
- No behavioral change -- all progress callbacks, error codes, and result
  paths are identical.

---

### WP-4 (P1): Split `test_orchestrator_service.py` into four focused files

**Problem:** After WP-2 and WP-3, `test_orchestrator_service.py` (1,270 lines
baseline + 14 new adversarial tests) spans five distinct source concerns in a
single file. Large monolith test files impede navigation, slow pytest collection
error isolation, and obscure where to add new tests when source functions change.

**Prerequisite:** WP-2 and WP-3 must be complete. The new test files import
the extracted private functions (`_run_spotify_search_phase`,
`_run_spotify_batch_detail_phase`, `_apply_pre_slice`, etc.) from
`scrobblescope.orchestrator`.

**Files:**
- `tests/services/test_orchestrator_process_albums.py` (new)
- `tests/services/test_orchestrator_fetch_spotify.py` (new)
- `tests/services/test_orchestrator_fetch_and_process.py` (new)
- `tests/services/test_orchestrator_helpers.py` (new)
- `tests/services/test_orchestrator_service.py` (deleted)

**Target structure:**

| New file | Tests moved | Approx. lines |
|----------|-------------|---------------|
| `test_orchestrator_process_albums.py` | `process_albums` tests (cache hit/miss, DB unavailable, conn cleanup, empty input, token failure, partial cache) | ~400 |
| `test_orchestrator_fetch_spotify.py` | `_fetch_spotify_misses`, `_cleanup_stale_metadata`, WP-2 new adversarial tests | ~450 |
| `test_orchestrator_fetch_and_process.py` | `_fetch_and_process`, `background_task`, pre-slice/cap, progress callback tests, WP-3 new adversarial tests | ~750 |
| `test_orchestrator_helpers.py` | `_matches_release_criteria`, `_get_user_friendly_reason`, `_build_results` tests | ~170 |

All four files import shared fixtures from `tests/helpers.py`
(`TEST_JOB_PARAMS`, `VALID_FORM_DATA`, `NoopAsyncContext`,
`make_response_context`). Follow the existing pattern in
`tests/services/test_lastfm_service.py` for file structure and import style.

**Implementation steps:**
1. Write `test_orchestrator_helpers.py` (smallest, no async, pure functions).
   Run `pytest tests/services/test_orchestrator_helpers.py -q`. Checkpoint
   commit.
2. Write `test_orchestrator_process_albums.py`. Run its file in isolation.
   Checkpoint commit.
3. Write `test_orchestrator_fetch_spotify.py` (includes WP-2 adversarial tests
   that were appended to the monolith). Run in isolation. Checkpoint commit.
4. Write `test_orchestrator_fetch_and_process.py` (includes WP-3 adversarial
   tests). Run in isolation. Checkpoint commit.
5. Run full `pytest -q` -- count must equal (260 + 6 from WP-1 + 14 from
   WP-2+3) tests passing.
6. Delete `tests/services/test_orchestrator_service.py`.
7. Run full `pytest -q` again -- count must be identical.
8. `pre-commit run --all-files`. Checkpoint commit.

**Acceptance criteria:**
- pytest count before and after deletion is identical.
- No import errors in any of the four new files (collection errors catch this).
- `test_orchestrator_service.py` is removed; no empty-shell file left.

---

### WP-5 (P2): DRY async retry loop shared by `lastfm.py` and `spotify.py`

**Problem:** ~25 lines of near-identical async retry orchestration exist in
three places: `lastfm.py` `fetch_recent_tracks_page_async` (L132-155),
`spotify.py` `search_for_spotify_album_id` (L73-90), and `spotify.py`
`fetch_spotify_album_details_batch` (L138-155). The shared structure is:
semaphore-guarded attempt, Retry-After handling, exponential or fixed backoff.
The only differences are: (a) backoff strategy (linear cap vs. fixed 1s),
(b) jitter on Retry-After (Spotify only), (c) which exception types to
re-raise vs. swallow.

**Files:**
- `scrobblescope/utils.py`
- `scrobblescope/lastfm.py`
- `scrobblescope/spotify.py`
- `tests/test_utils.py` (new tests for the extracted utility)

**New function in `utils.py`:**

```python
async def retry_with_semaphore(
    attempt_fn,
    *,
    retries: int,
    semaphore: asyncio.Semaphore | None = None,
    backoff_fn=None,
    jitter_fn=None,
    re_raise: tuple = (),
):
    """Generic async retry executor with optional semaphore, backoff, and jitter.

    `attempt_fn` is an async callable returning (result, retry_after, done).
    Returns result when done=True, or None after exhausting retries.
    Callers that use a 2-tuple (result, retry_after) should wrap with a
    normalizing lambda: `lambda: (r, ra, r is not None)`.
    """
    for attempt in range(retries):
        try:
            if semaphore is None:
                result, retry_after, done = await attempt_fn()
            else:
                async with semaphore:
                    result, retry_after, done = await attempt_fn()
            if done:
                return result
            if retry_after is not None:
                wait = retry_after + (jitter_fn(attempt) if jitter_fn else 0.0)
                await asyncio.sleep(wait)
                continue
        except re_raise:
            raise
        except Exception as exc:
            logging.error("retry_with_semaphore attempt %d/%d failed: %s",
                          attempt + 1, retries, exc)
        await asyncio.sleep(backoff_fn(attempt) if backoff_fn else 1.0)
    return None
```

Callers:

`lastfm.py` `fetch_recent_tracks_page_async` -- replace the manual loop with:
```python
async def _normalized_fetch():
    data, retry_after = await fetch_once()
    return data, retry_after, data is not None

return await retry_with_semaphore(
    _normalized_fetch,
    retries=retries,
    semaphore=semaphore,
    backoff_fn=lambda attempt: min(0.25 * (attempt + 1), 1.0),
    re_raise=(ValueError,),
)
```

`spotify.py` search -- replace with:
```python
return await retry_with_semaphore(
    search_once,
    retries=SPOTIFY_SEARCH_RETRIES,
    semaphore=semaphore,
    backoff_fn=lambda _: 1.0,
    jitter_fn=lambda attempt: (abs(hash((artist, album, attempt))) % 200) / 1000.0,
)
```

`spotify.py` batch -- same pattern, `backoff_fn=lambda attempt: 2**attempt`,
`jitter_fn=lambda attempt: (abs(hash((tuple(album_ids), attempt))) % 200) / 1000.0`.

**New tests in `tests/test_utils.py`:**
1. `test_retry_with_semaphore_returns_on_first_success` -- done=True on
   attempt 1; assert result returned, attempt_fn called once.
2. `test_retry_with_semaphore_retries_on_retry_after` -- first call returns
   done=False with retry_after=0.1; second call returns done=True; assert
   result is second result.
3. `test_retry_with_semaphore_exhausts_and_returns_none` -- all attempts
   return done=False, no retry_after; assert None returned after `retries`
   calls.
4. `test_retry_with_semaphore_reraises_specified_exception` -- attempt_fn
   raises ValueError; `re_raise=(ValueError,)`; assert ValueError propagates.
5. `test_retry_with_semaphore_swallows_non_reraise_exception` -- attempt_fn
   raises RuntimeError; assert None returned after retries.
6. `test_retry_with_semaphore_applies_jitter_on_retry_after` -- jitter_fn
   returns 0.05; assert `asyncio.sleep` called with retry_after + 0.05.
7. `test_retry_with_semaphore_uses_semaphore_when_provided` -- verify
   attempt_fn is called inside semaphore context (mock semaphore's `__aenter__`
   and `__aexit__` to assert invocation).

**Implementation steps:**
1. Add `retry_with_semaphore` to `utils.py`. Add 7 tests to `test_utils.py`.
   Checkpoint commit.
2. Refactor `lastfm.py` `fetch_recent_tracks_page_async` to call
   `retry_with_semaphore`. Run `pytest tests/services/test_lastfm_service.py`
   to verify no behavioral regression. Checkpoint commit.
3. Refactor both retry loops in `spotify.py` to call `retry_with_semaphore`.
   Run `pytest tests/services/test_spotify_service.py`. Checkpoint commit.
4. Run full `pytest -q`. Checkpoint commit.

**Acceptance criteria:**
- All existing `lastfm` and `spotify` service tests pass without modification.
- 7 new `retry_with_semaphore` unit tests pass.
- Manual `retry` loop code is removed from all three call sites.
- `lastfm.py` and `spotify.py` no longer import `asyncio.Semaphore`
  explicitly for the retry guard (it is encapsulated in `utils.py`).

---

## 3. Execution order

1. **WP-1** -- Establish direct worker tests as safety net before any source
   changes. No dependencies.
2. **WP-2** -- Decompose `_fetch_spotify_misses()`. Depends on WP-1 (safe
   baseline).
3. **WP-3** -- Decompose `_fetch_and_process()`. Independent of WP-2; can
   run in parallel if two agents are available, but both touch `orchestrator.py`
   so sequential is safer.
4. **WP-4** -- Split test file. Depends on WP-2 and WP-3 (new test files
   import the extracted private functions).
5. **WP-5** -- DRY retry utility. Fully independent of WP-1 through WP-4;
   touches only `utils.py`, `lastfm.py`, `spotify.py`.

---

## 4. Validation checklist (per checkpoint commit)

- `.\venv\Scripts\python.exe -m pytest -q` -- all tests pass.
- `.\venv\Scripts\python.exe -m pre_commit run --all-files` -- all 8 hooks
  pass.
- Stage only files changed for this checkpoint.
- Conventional Commits format, no co-author trailers.

Per-WP completion:
- Update `PLAYBOOK.md` Section 3 (status) + Section 4 (dated log entry inside
  current-batch markers).
- Update `SESSION_CONTEXT.md` Section 2 (test count, batch status row,
  Section 7 test-file table) if changed.
- Run `.\venv\Scripts\python.exe scripts/doc_state_sync.py --fix`.

At batch close-out (all WPs done):
- `.\venv\Scripts\python.exe scripts/doc_state_sync.py --fix --keep-non-current 0`
- Move this file to `docs/history/BATCH13_DEFINITION.md`.
- Update `PLAYBOOK.md` Section 2 batch table.

---

## 5. Audit notes

**Why WP-1 is P0:** The absence of direct `worker.py` tests means a regression
in slot acquisition or thread lifecycle would only surface as a confusing
orchestrator integration failure. WP-1 fills this gap before WP-2/WP-3 touch
the most complex code in the repo. Estimated 6 tests, ~80 lines.

**WP-2/WP-3 do not change any public interface.** All extracted functions
carry the `_` prefix (private by convention). Patches in the existing test
suite target module-level public names (`search_for_spotify_album_id`,
`fetch_spotify_album_details_batch`, `fetch_top_albums_async`,
`process_albums`) which remain unchanged. No test file needs modification
until WP-4 performs the physical split.

**`_fetch_and_process` `_lastfm_progress` closure disposition:** This 3-line
closure captures `job_id` from the enclosing scope and is passed as a
callback to `fetch_top_albums_async`. Extracting it to a module-level helper
would require `job_id` as a parameter, creating a partial-application pattern
with no practical gain. It stays inline.

**WP-4 deletion protocol:** The original `test_orchestrator_service.py` must
be deleted (not emptied). An empty file causes conftest fixture discovery
confusion and signals that testing for the module is optional. The pytest
count check before and after deletion is the key regression guard.

**WP-5 behavioral risk:** The retry abstraction normalizes three slightly
different loop implementations. The highest-risk change is in `lastfm.py`
where `ValueError` is re-raised (signaling user-not-found vs. rate-limit
ambiguity). The `re_raise=(ValueError,)` parameter preserves this behavior.
Existing `test_lastfm_service.py` tests (`test_fetch_recent_tracks_page_user_not_found`,
`test_check_user_exists_*`) provide full regression coverage. Run these tests
in isolation after step 2 before proceeding.

**Items deferred with explicit rationale:**

- **Smoke test CI:** `scripts/smoke_cache_check.py` is a 2-run HTTP comparison
  script. Running it in CI requires a live Flask server. The cleanest approach
  is a `flask run --port 5000 &` + `sleep 2` step in the GitHub Actions
  workflow (no Docker needed for basic smoke). However, this also requires
  test API keys injected as GitHub Actions secrets (`LASTFM_API_KEY`,
  `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`) and a real Last.fm username
  with scrobble history. The infrastructure decision (mock credentials vs.
  real API keys in CI) should be made by the owner before implementation.

- **Jules:** No source code changes required. Integration is: (1) connect
  the GitHub repo to Jules at jules.google.com, (2) create issue templates
  that provide enough context for Jules to act on. The multi-agent PLAYBOOK
  system already provides the context Jules would need. This is a side-task
  that can be done any time without a batch.

- **`REQUEST_CACHE` size cap:** The in-memory dict grows until
  `cleanup_expired_cache()` runs at job start. At 10 concurrent jobs and a
  1-hour TTL, the worst-case cache size is bounded by API response payload
  size. No immediate action needed; revisit if Fly.io memory pressure is
  observed in production logs.
