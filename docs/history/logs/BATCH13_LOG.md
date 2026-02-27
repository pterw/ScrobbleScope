# Batch 13 Execution Log

Archived entries for Batch 13 work packages.

### 2026-02-24 - refactor(retry): DRY async retry loop into retry_with_semaphore (Batch 13 WP-5)

- Scope: `scrobblescope/utils.py`, `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`,
  `tests/test_retry_with_semaphore.py` (new).
- Problem: Three nearly-identical retry loops (lastfm `fetch_once`, spotify
  `search_once`, spotify batch `fetch_once`) duplicated semaphore gating,
  retry-after handling, backoff sleep, and exhaustion logging.
- Fix: Extracted `retry_with_semaphore()` to `utils.py` with parameterized
  `is_done`, `get_retry_after`, `extract_result`, `backoff`, `jitter`, and
  `reraise`. Refactored all three call sites. Added 7 adversarial tests.
- Validation: **287 tests passing** (280 + 7 new), pre-commit all 8 hooks passed.

### 2026-02-24 - refactor(tests): split test_orchestrator_service.py into four files (Batch 13 WP-4)

- Scope: `tests/services/test_orchestrator_service.py` (deleted),
  `tests/services/test_orchestrator_process_albums.py` (new, 7 tests),
  `tests/services/test_orchestrator_fetch_spotify.py` (new, 8 tests),
  `tests/services/test_orchestrator_fetch_and_process.py` (new, 10 tests),
  `tests/services/test_orchestrator_helpers.py` (new, 18 tests).
- Problem: Monolith test file (1523 lines, 43 pytest cases) mixed concerns
  across process_albums, fetch_spotify_misses, fetch_and_process, background_task,
  and pure helpers. Slow to navigate and find related tests.
- Fix: Split into four focused files by SUT function group. Verified each file
  in isolation, confirmed full suite count identical (280) before and after
  deleting original.
- Validation: **280 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-24 - refactor(orchestrator): extract five helpers from _fetch_and_process (Batch 13 WP-3)

- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Fix: Extracted `_record_lastfm_stats`, `_apply_pre_slice`,
  `_detect_spotify_total_failure`, `_apply_post_slice`, and
  `_classify_exception_to_error_code` from `_fetch_and_process()`. Coordinator
  reduced from ~230 to ~80 lines. Added 11 adversarial tests. All existing tests
  pass without modification.
- Validation: **280 tests passing** (269 + 11 new), pre-commit all 8 hooks passed.

### 2026-02-24 - refactor(orchestrator): extract search/batch-detail phases (Batch 13 WP-2)

- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Fix: Extracted `_run_spotify_search_phase` and `_run_spotify_batch_detail_phase`
  from `_fetch_spotify_misses()`. Coordinator reduced from ~196 to ~25 lines.
  Added 3 adversarial tests. All existing tests pass without modification.
- Validation: **269 tests passing** (266 + 3 new), pre-commit all 8 hooks passed.

### 2026-02-24 - test(worker): add 6 direct unit tests for worker.py (Batch 13 WP-1)

- Scope: `tests/test_worker.py` (new).
- Problem: `worker.py` (43 lines, 3 functions) had no dedicated test file.
  Coverage was indirect only via orchestrator integration tests. Three distinct
  failure paths were untested: semaphore exhaustion, double-release warning,
  and thread construction failure slot release.
- Fix: Created `tests/test_worker.py` with 6 tests using `unittest.mock.patch`
  to replace `_active_jobs_semaphore` with isolated `BoundedSemaphore` instances.
  Tests cover: acquire success, acquire at capacity, release restores capacity,
  double-release warning via `caplog`, daemon thread creation, and slot release
  on thread construction failure.
- Validation: **266 tests passing** (260 + 6 new), pre-commit all 8 hooks passed.
