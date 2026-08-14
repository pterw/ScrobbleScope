# Routes SoC and Duplication Audit -- Batch 10 WP-6 (2026-02-21)

Date: 2026-02-21
Triggered by: owner-directed separation-of-concerns review of `routes.py`
Implemented by: Claude Sonnet 4.6

---

## 1. Summary

`scrobblescope/routes.py` (458 lines pre-audit) was read in full. Four
findings were identified: two duplicate code patterns (R1, R2) and two
instances where non-HTTP transform or business logic was embedded in route
handlers (R3, R4). All four were implemented as module-level private
helpers, each in a separate commit.

After implementation, a review found that the route-level tests only
exercised happy paths for two of the new helpers. Three adversarial unit
tests were added.

---

## 2. Findings and resolutions

### R1 -- Duplicate async wrapper for check_user_exists
**Locations:** `validate_user()` lines 46-50, `results_loading()` lines 381-384
**Weakness:** Both handlers defined an inner `async def` wrapping
`check_user_exists(username)` and passed it to `run_async_in_thread`.
Identical pattern, duplicated boilerplate.
**Fix:** Extracted to `_check_user_exists(username)` at module level.
Both call sites replaced with a single call.

---

### R2 -- Duplicate job params extraction from job_context
**Locations:** `results_complete()` lines 200-213, `unmatched_view()` lines 305-312
**Weakness:** Both handlers unpacked the same eight fields from
`job_context["params"]` with the same defaults. Any change to field names
or defaults required edits in two places.
**Fix:** Extracted to `_extract_job_params(job_context)` at module level.
`results_complete()` applies its form fallbacks to the returned dict;
`unmatched_view()` uses the values directly.

---

### R3 -- Reason-grouping data transform in route handler
**Location:** `unmatched_view()` lines 318-325
**Weakness:** A 6-line group-by loop and count dict embedded in the
handler. Data transforms have no business in HTTP response logic.
**Fix:** Extracted to `_group_unmatched_by_reason(unmatched_data)`.
Returns `(reasons, reason_counts)`. The loop was also tightened:
iterated `.values()` directly instead of unpacking `_, item`.

---

### R4 -- Zero-playtime filter business rule in route handler
**Location:** `results_complete()` lines 224-228
**Weakness:** A list comprehension encoding the rule "drop albums with no
`play_time_seconds` when sorting by playtime" was inlined. The rule is
non-trivial and its purpose was not documented at the call site.
**Fix:** Extracted to `_filter_results_for_display(results_data, sort_mode)`
with a docstring explaining the business rule.

---

## 3. Follow-up: adversarial unit tests for extracted helpers

After R1-R4, a review of the route-level tests found that two helpers
were only exercised on the happy path:

- `_filter_results_for_display` was only called with `sort_mode="playcount"`
  and albums with non-zero playtime. The core filtering behaviour (dropping
  zero-playtime albums when `sort_mode="playtime"`) was never triggered.
- `_group_unmatched_by_reason` was only called with items that all had a
  `"reason"` key. The `"Unknown reason"` fallback was untested.

Three direct unit tests added to `tests/test_routes.py`:

1. `test_filter_results_for_display_removes_zero_playtime_when_sorting_by_playtime`
   -- albums with `play_time_seconds=0` or missing key are dropped when
   `sort_mode="playtime"`.
2. `test_filter_results_for_display_keeps_zero_playtime_for_non_playtime_sort`
   -- the same albums are kept when `sort_mode="playcount"`.
3. `test_group_unmatched_by_reason_uses_fallback_for_missing_reason_key`
   -- items without a `"reason"` key are grouped under `"Unknown reason"`.

---

## 4. What was NOT changed

- No route behaviour changed. All changes are pure structural refactors.
- `_extract_job_params` and `_check_user_exists` were not given direct
  unit tests: `_extract_job_params` is a thin dict unpack with defaults
  covered by existing route integration tests; `_check_user_exists` is
  a closure factory covered by 6+ existing route tests.
- No new tests were added for uncovered production paths.

---

## 5. Validation

- `pytest -q`: **116 passed** (113 pre-existing + 3 new adversarial tests).
- `pre-commit run --all-files`: all 8 hooks passed on every commit.
- No production code behaviour changes.

---

## 6. Commits

| Commit | Message |
|--------|---------|
| `609b4c8` | refactor(routes): extract _check_user_exists helper (R1) |
| `8b44b2b` | refactor(routes): extract _extract_job_params helper (R2) |
| `7d51bd5` | refactor(routes): extract _group_unmatched_by_reason helper (R3) |
| `bdbf7e7` | refactor(routes): extract _filter_results_for_display helper (R4) |
| `d893bc9` | test(routes): add adversarial unit tests for extracted helpers |

---

## 7. Files changed

| File | Change |
|------|--------|
| `scrobblescope/routes.py` | 4 module-level helpers extracted; call sites updated |
| `tests/test_routes.py` | 3 adversarial unit tests + helper imports added |
