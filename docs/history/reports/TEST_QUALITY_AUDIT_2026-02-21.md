# Test Quality Audit -- Sycophantic Coverage (Batch 10, 2026-02-21)

Date: 2026-02-21
Triggered by: Gemini 2.5 Pro static analysis review of test_*.py files (94-test
              baseline) + manual review of current 114-test suite
Implemented by: Claude Sonnet 4.6

---

## 1. Summary

A Gemini 2.5 Pro audit characterised the test suite as "sycophantic": providing
high coverage metrics while failing to challenge the code with adversarial data
or verify real side-effects.  Three structural anti-patterns were identified:

1. **Assumption Mirroring** -- tests use the same logical shortcuts as the
   production code (e.g. always ASCII-safe input, always perfectly structured
   fixture dicts), so both code and test agree on the same incorrect assumption.

2. **Circular Mocking** -- orchestrator tests mock primary dependencies to return
   pre-crafted "correct" data, then confirm the orchestrator processes correct
   data correctly.  The most complex domain logic (aggregation, filtering) runs
   in a different test file; the orchestrator tests only verify plumbing.

3. **Interface-Only Validation** -- route tests patch `start_job_thread` so the
   background task never runs; assertions only confirm that the route invoked a
   function, not that any meaningful state change resulted.

Five specific tests were identified and fixed in the current 114-test suite.

---

## 2. Findings and resolutions

### Finding 1 (mock-call-only, no argument check, no JOBS state)
**Test:** `test_results_loading_thread_start_failure_renders_error`
**File:** `tests/test_routes.py`

**Weakness:** `delete_job` was fully patched out so the actual JOBS dict was not
cleaned up.  The only cleanup assertion was `mock_delete_job.assert_called_once()`
which verified the mock was invoked but not which `job_id` was passed.  Replacing
`delete_job(job_id)` with `delete_job("wrong_id")` or `delete_job(None)` in the
production route would have left the test green.

**Fix:** Dropped the `delete_job` mock.  The test now snapshots `set(JOBS.keys())`
before the POST and asserts the set is identical after -- any orphan job left
behind (wrong id, missing call, wrong branch) causes the assertion to fail.

---

### Finding 2 (return-value assertion missing side-effect assertion)
**Test:** `test_fetch_and_process_cache_hit_does_not_precheck_spotify`
**File:** `tests/services/test_orchestrator_service.py`

**Weakness:** `_fetch_and_process` calls `set_job_results(job_id, results)` at
orchestrator.py:568 -- the side-effect that `background_task` actually relies on
(it ignores the coroutine's return value entirely and reads from the JOBS dict).
The test only asserted `results == expected_results` (return-value assertion),
which is trivially true because `_fetch_and_process` returns the `process_albums`
mock return value unchanged.  Removing `set_job_results` from the production
function would have broken the real application but left this test green.

**Fix:** Added `assert JOBS[job_id]["results"] == expected_results` (with
`jobs_lock`) to verify the side-effect, not just the return value.

---

### Finding 3 (near-duplicate, zero unique protection)
**Test:** `test_succeeds_with_strong_key_in_dev_mode`
**File:** `tests/test_app_factory.py`

**Weakness:** Near-duplicate of `test_succeeds_with_strong_key_in_production`.
Both assert "strong key raises nothing".  For a strong key, dev mode and
production mode follow the same accept path -- the dev-mode code path (log
warning for weak keys) is already exercised by `test_warns_in_dev_mode_when_key_is_weak`.
This test added no unique regression protection.

**Fix:** Removed.

---

### Finding 4 (no assertion -- vacuously passing)
**Test:** `test_cleanup_stale_metadata_nonfatal`
**File:** `tests/services/test_orchestrator_service.py`

**Weakness:** No assertion at all.  The test would pass even if
`_cleanup_stale_metadata` was replaced with an empty coroutine.  The production
function logs `logging.warning("Stale cache cleanup failed (non-fatal): %s", exc)`
when an exception is swallowed -- that log entry is the only observable
side-effect of the failure path and it was not being asserted.

**Fix:** Added `caplog.at_level(logging.WARNING)` context and asserted
`"Stale cache cleanup failed" in caplog.text`.

---

### Finding 5 (no assertion -- minor)
**Test:** `test_delete_job_on_missing_job_is_noop`
**File:** `tests/test_repositories.py`

**Weakness:** No assertion at all.  The test would pass vacuously for a completely
empty `delete_job` implementation.  The documented contract is "calling delete_job
on a nonexistent id is a noop" -- two components of that contract can be verified:
(a) no exception raised, (b) JOBS dict not corrupted.  Only (a) was implicitly
verified.

**Fix:** Added `assert "nonexistent_id_xyz" not in JOBS` (with `jobs_lock`) to
make the noop contract explicit and guard against accidental key insertion.

---

## 3. What was NOT changed

The Gemini audit also flagged "circular mocking" as a suite-level structural
concern: orchestrator tests always mock `fetch_top_albums_async` with
pre-normalised, perfectly structured dicts, creating a separation where the
aggregation logic is tested in `test_lastfm_logic.py` and the orchestrator
plumbing is tested in `test_orchestrator_service.py`, but no test exercises them
together.  This is a valid observation but is:

- An integration test gap, not a quality problem with existing tests
- Out of scope for this task ("do not add new tests for un-covered paths")
- Already partially addressed: `test_lastfm_logic.py` was added specifically to
  cover `fetch_top_albums_async` aggregation and filtering logic end-to-end.

---

## 4. Validation

- `pytest -q`: **113 passed** (114 - 1 removed duplicate).
- `pre-commit run --all-files`: all 8 hooks passed.
- No behavior changes.  No production code changes.  Test-only commit.

---

## 5. Files changed

| File | Change |
|------|--------|
| `tests/test_routes.py` | Finding 1: dropped delete_job mock, JOBS snapshot assertion |
| `tests/services/test_orchestrator_service.py` | Finding 2: added JOBS results assertion; Finding 4: added caplog assertion; import updated |
| `tests/test_app_factory.py` | Finding 3: removed duplicate test |
| `tests/test_repositories.py` | Finding 5: added JOBS membership assertion |
