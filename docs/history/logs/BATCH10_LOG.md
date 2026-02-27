# Batch 10 Execution Log

Archived entries for Batch 10 work packages.

### 2026-02-21 - fix: Gemini 3.1 Pro P0/P1 audit remediation (Batch 10 WP-7, WP-8, WP-9)

- Scope: `scrobblescope/utils.py`, `scrobblescope/orchestrator.py`,
  `tests/test_utils.py`, `tests/services/test_orchestrator_service.py`.
- Problem: Three confirmed findings from a Gemini 3.1 Pro audit pass:
  WP-7 -- Per-loop AsyncLimiter design meant each background job (which
  creates its own asyncio event loop) got an independent rate limiter.
  With MAX_ACTIVE_JOBS=10, aggregate throughput could reach 10x the
  configured API rate cap, risking 429s or IP bans.
  WP-8 -- The playcount pre-slice fired before process_albums applied
  the release-year filter. With release_scope != "all", albums outside
  the raw top-N could be the only ones matching the filter; discarding
  them early silently returned fewer results with no warning to the user.
  WP-9 -- No upper bound on filtered_albums for playtime sort. Pre-slicing
  is impossible (ranking requires Spotify track durations), but an extreme
  outlier with 2000+ qualifying albums would force proportional Spotify API
  load with no safety valve.
- Plan vs implementation: all three implemented as one commit each, tests
  first per AGENTS.md adversarial rule. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **121 passed** (116 baseline + 5 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed on every commit.
  - WP-7: _GlobalThrottle.next_wait() serialization test + cross-thread
    identity test confirm the shared throttle is in place.
  - WP-8: adversarial test confirms all 5 albums reach process_albums when
    release_scope="same" and limit_results="2".
  - WP-9: cap fires + warning logged test + below-threshold no-op test.
- Forward guidance: Batch 10 is now complete (WP-1 through WP-9). Batch 11
  is not yet defined. Feature work (top songs, heatmap) and further audit
  work require owner scope definition before implementation begins.
  _PLAYTIME_ALBUM_CAP=500 is conservative; monitor "Playtime album cap
  applied" warnings in production logs to tune if needed.

### 2026-02-21 - refactor/test: routes.py SoC and duplication audit (Batch 10 WP-6)

- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`,
  `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md` (new doc).
- Problem: Four SoC and duplication issues identified in `routes.py`:
  R1 -- two identical inner async wrappers for `check_user_exists` in
  `validate_user()` and `results_loading()`. R2 -- eight-field job params
  extraction duplicated verbatim in `results_complete()` and
  `unmatched_view()`. R3 -- reason-grouping data transform (group-by loop
  + count dict) embedded in `unmatched_view()`. R4 -- zero-playtime filter
  business rule (list comprehension) embedded in `results_complete()`.
  Follow-up: route-level tests only exercised happy paths for two of the
  new helpers; the playtime filter rule never fired in any test and the
  "Unknown reason" fallback was untested.
- Plan vs implementation: all four findings implemented as separate commits
  (R1-R4), then three adversarial unit tests added in a fifth commit.
  No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **116 passed** (113 pre-existing + 3 adversarial tests).
  - `pre-commit run --all-files`: all 8 hooks passed on every commit.
  - No behavior changes. Pure structural refactors + targeted tests.
- Forward guidance: Batch 10 is complete. Batch 11 is not yet defined.
  Feature work (top songs, heatmap) requires owner scope definition before
  implementation begins. No production risk introduced.

### 2026-02-21 - test: sycophantic test coverage audit (Batch 10 WP-5)

- Scope: `tests/test_routes.py`, `tests/services/test_orchestrator_service.py`,
  `tests/test_app_factory.py`, `tests/test_repositories.py`,
  `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md` (new doc).
- Problem: A Gemini 2.5 Pro audit of the 94-test baseline characterised the suite
  as "sycophantic" -- three structural patterns: assumption mirroring (tests use
  the same data shortcuts as production code), circular mocking (orchestrator tests
  return perfect fixture data and confirm perfect results), and interface-only
  validation (route tests patch start_job_thread so background state is never
  verified). Review of the current 114-test suite identified five specific instances:
  1. `test_results_loading_thread_start_failure_renders_error`: patched delete_job
     and only called assert_called_once() -- no arg check, no JOBS state check.
  2. `test_fetch_and_process_cache_hit_does_not_precheck_spotify`: only asserted
     on return value; background_task reads job state not return value, so the
     critical set_job_results side-effect was unchecked.
  3. `test_succeeds_with_strong_key_in_dev_mode`: near-duplicate of the production
     strong-key test; zero unique regression protection.
  4. `test_cleanup_stale_metadata_nonfatal`: no assertion at all.
  5. `test_delete_job_on_missing_job_is_noop`: no assertion at all.
- Plan vs implementation: all five fixed as described in
  `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **113 passed** (114 - 1 removed duplicate).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - No production code changes. Test-only commit.
- Forward guidance: next sub-track is SoC and duplication audit of routes.py.
  The suite-level "circular mocking" concern (no integration layer between
  fetch_top_albums_async aggregation and orchestrator processing) is a valid
  observation but out of scope for this task -- it would require new integration
  tests, not quality fixes to existing ones. Document as a known gap.
