# PLAYBOOK Execution Log Archive

Purpose:
- Store dated execution-log entries rotated out of `PLAYBOOK.md` section 10.
- Keep entries in reverse-chronological order (newest first).

Read helpers:
- `Get-Content docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "<keyword>" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

### 2026-02-22 - refactor(orchestrator): decompose process_albums into helpers (Batch 11 WP-2)

- Scope: `scrobblescope/orchestrator.py`,
  `tests/services/test_orchestrator_service.py`.
- Problem: `process_albums` was ~300 lines with 5 phases, 2 inner closures,
  and interleaved cache/Spotify/filtering logic. Two closures captured outer
  scope needlessly (pure functions). Phase 3 (Spotify fetch for cache misses)
  and Phase 5 (result building + sorting) were inlined blocks that obscured
  the orchestration flow.
- Plan vs implementation: Implemented as planned in 4 incremental commits:
  1. Extracted `_matches_release_criteria` and `_get_user_friendly_reason`
     closures to module-level pure functions (no behavior change).
  2. Extracted `_fetch_spotify_misses` as async helper (mutates
     `cache_hits` in place, returns `new_metadata_rows`).
  3. Extracted `_build_results` as synchronous helper (filters, sorts,
     computes proportions).
  4. Added 4 adversarial test functions (8 parametrized cases): boundary
     inputs for extracted helpers (malformed dates, None values, missing
     keys, zero playtime division).
- Deviations: None. Each commit passed full test suite and pre-commit.
- Validation:
  - `pytest -q`: **210 passed** (was 202; +8 adversarial test cases).
  - `pre-commit run --all-files`: all 8 hooks passed after each commit.
  - All 18 existing orchestrator tests continued to pass unchanged,
    confirming no behavioral regression.
- Forward guidance: Batch 11 is now complete (WP-1, WP-3, WP-2 all done).
  `process_albums` is now a ~40-line thin orchestrator delegating to 4
  named helpers. Future feature work (top songs, heatmap) should follow
  the same pattern of named helpers called from a thin orchestrator.

### 2026-02-21 - refactor(static): theme CSS/JS consolidation + results UX (Batch 11 WP-1)

- Scope: `static/css/global.css` (new), `static/js/theme.js` (new),
  `templates/base.html`, `templates/results.html`,
  `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`,
  `static/css/error.css`, `static/css/unmatched.css`,
  `static/js/index.js`, `static/js/results.js`, `static/js/loading.js`,
  `static/js/error.js`, `static/js/unmatched.js`.
- Problem: Four verified findings from a Gemini 3.1 Pro Priority 2 audit:
  CSS finding -- `:root` vars, `.dark-mode` overrides, `#darkModeToggle` block,
  `#darkSwitch` block, SVG color rules, and media queries duplicated verbatim
  across all five per-page CSS files (~250 lines, 5x). JS finding -- dark-mode
  toggle logic (`localStorage` read, class toggle, `addEventListener`) duplicated
  in all five JS files; `updateSvgColors` in four files redundant because
  `global.css` `.dark-mode svg .cls-1` already handles SVG color via CSS.
  UX finding (owner addition) -- html2canvas JPEG export on mobile captured only
  the visible viewport of the horizontally-overflowed table, not the full table.
  UX finding (owner addition) -- no "Back to top" button on results page.
- Plan vs implementation: implemented as planned. No scope additions.
  `#darkModeToggle { position: fixed; }` preserved in `global.css`; verified
  toggle stays pinned at bottom center on all pages. `error.js` and `unmatched.js`
  reduced to comment stubs (all their logic was dark-mode only). `loading.js`
  module-level dark-mode block removed; progress-polling logic unchanged.
- Deviations: none.
- Validation:
  - `pytest -q`: **121 passed** (no Python changes; suite unchanged).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - html2canvas fix: added `width: el.scrollWidth`, `height: el.scrollHeight`,
    `windowWidth: el.scrollWidth`, `scrollX: 0`, `scrollY: 0` to capture full
    table width on mobile.
  - Back-to-top: fixed bottom-right button, visible after 300px scroll,
    smooth-scrolls to top on click. JS in `results.js`; HTML in `results.html`.
- Forward guidance: WP-2 pending -- decompose `process_albums` in
  `orchestrator.py` (extract closure helpers + `_fetch_spotify_misses` +
  `_build_results`; add 4 adversarial tests). No production behavior change from
  WP-1; pure CSS/JS reorganization.

### 2026-02-21 - style/fix(static): CSS/JS DRY violations, toggle bug, UX polish (Batch 11 WP-3)

- Scope: `static/css/global.css`, `static/css/results.css`,
  `static/css/index.css`, `static/css/loading.css`,
  `static/js/results.js`, `static/js/theme.js`,
  `templates/base.html`.
- Problem: Five findings from a post-WP-1 owner code review:
  (1) DRY/SoC -- `--info-bg` was defined in `results.css` `:root`/
  `.dark-mode` blocks while `loading.css` hard-coded the identical rgba
  values inline; neither could share the variable because loading.css does
  not import results.css. Promoted `--info-bg` to `global.css` and replaced
  loading.css hard-codes with `var(--info-bg)`.
  (2) DRY -- Three `.dark-mode .modal-content/.modal-header/.modal-footer/
  .btn-close` rules were byte-for-byte duplicated in both `index.css` and
  `results.css`. Moved once to `global.css` and removed from both files.
  (3) Bug -- Dark-mode toggle markup used Bootstrap `form-check form-switch`/
  `form-check-input`/`form-check-label` classes while the widget was 100%
  custom-styled with `appearance: none` + `::before`. Bootstrap's
  `.form-switch .form-check-input` injected a conflicting SVG `background-
  image` knob and a `margin-left: -2.5em`, fighting the custom layout.
  Stripped Bootstrap classes from HTML markup in `base.html`; updated CSS
  selectors from `.form-check-input`/`.form-check-label` to bare
  `input`/`label`; added `cursor: pointer` to label (previously inherited
  from Bootstrap). Also fixed dark-mode toggle track color: was purple
  (`var(--bars-color)`); added `.dark-mode #darkSwitch:checked` override
  using `var(--bg-color)` so it blends with the dark background instead.
  (4) UX -- `.step-text` and `.step-details` on the loading page lacked
  `text-align: center`; text was left-aligned inside the centered card.
  (5) Redundant JS -- Mobile release-date shortening block in `results.js`
  (`window.innerWidth < 768` regex-replace on `.release-badge` text)
  duplicated logic already handled server-side by Bootstrap `d-none d-md-
  inline`/`d-md-none` spans in `results.html`. Removed.
  Additionally: `var` -> `const` for `darkSwitch` and `backToTop` in
  `theme.js` (neither is reassigned).
- Plan vs implementation: all findings addressed in-session. No scope
  additions beyond owner-requested dark-mode track color fix.
- Deviations: none.
- Validation:
  - `pytest -q`: **121 passed** (no Python changes; suite unchanged).
  - `pre-commit run --all-files`: all hooks passed.
  - No Python behavior change. Pure CSS/JS/template hygiene.
- Forward guidance: WP-2 (decompose `process_albums` in `orchestrator.py`)
  remains the next pending Batch 11 work package. Claim 3 from the review
  (toggle desync -- hardcoded `#1e1e1e` and `#333` spread across files
  instead of semantic `--surface-color`/`--border-color` variables) is a
  valid architectural observation but is a larger refactor; the current
  values are consistent and functional. Deferred.

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

### 2026-02-21 - refactor/fix: Gemini audit remediation (non-normalization track)

- Scope: `scrobblescope/orchestrator.py`, `scrobblescope/cache.py`,
  `scrobblescope/routes.py`, `scrobblescope/domain.py`,
  new `scrobblescope/errors.py`, `scrobblescope/repositories.py`,
  `tests/services/test_orchestrator_service.py` (+4 tests),
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md` (new doc).
- Problem: A second Gemini Pro audit pass identified four issues beyond the previously
  fixed normalization bugs. Three were confirmed real against the live codebase:
  1. Late slicing: `limit_results` applied after Spotify calls in `_fetch_and_process`.
     For playcount sort the ranking is fully known from Last.fm data; pre-slicing
     to the requested limit eliminates unnecessary Spotify searches on cache misses.
     (Playtime sort cannot be pre-sliced -- ranking requires track duration data.)
  2. Indefinite DB growth: `_batch_lookup_metadata` filtered stale rows at read time
     but no DELETE ever ran. Stale rows accumulated in `spotify_cache` indefinitely.
  3. ERROR_CODES + SpotifyUnavailableError in `domain.py`: a SoC violation -- domain
     logic should not own user-facing message strings or retryability flags.
  A fourth SoC issue not in the original report was also fixed: duplicate release_scope
  -> human-text translation in `routes.py` (inline block in `unmatched_view`
  duplicating `get_filter_description`). A fifth issue (empty-result hallucination)
  was assessed and deferred as near-false-alarm -- the trigger conditions require
  zero cache hits AND every album absent from Spotify, which is extremely unlikely.
- Plan vs implementation: all four confirmed issues fixed as described in
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **114 passed** (110 pre-existing + 4 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - Import graph: `errors.py` is a leaf module (no package imports). Acyclic structure
    preserved. `domain.py` now contains only normalization logic.
- Forward guidance: next sub-track is "sycophantic test coverage" audit (owner to
  elaborate scope). Feature work (top songs, heatmap) blocked until owner assigns a
  future batch number and defines scope. `_cleanup_stale_metadata` is opportunistic and non-fatal;
  monitor logs for "Stale cache cleanup" entries to confirm it fires in production.
  The playtime late-slicing limitation is documented inline in `_fetch_and_process`.

### 2026-02-21 - fix(domain): fix normalization bugs silently excluding non-Latin albums

- Scope: `scrobblescope/domain.py`, `tests/test_domain.py` (9 new tests),
  `tests/services/test_lastfm_logic.py` (new file, 7 tests),
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md` (new doc).
- Problem: A third-party static analysis review (Gemini Pro) identified four
  defects in `domain.py` and a coverage gap in `lastfm.py`. All four were
  confirmed against the live codebase and three had measurable production impact:
  1. `normalize_track_name` used `NFKD + encode("ascii","ignore")`, stripping all
     non-Latin characters to `""`. Any album with Japanese/Cyrillic/etc. track names
     had `len(track_counts) == 1` regardless of distinct tracks played, silently
     failing the `min_tracks` filter and disappearing from results without an
     unmatched entry or any log warning.
  2. `normalize_name` applied its `album_metadata_words` set to the artist string as
     well as the album string, corrupting proper nouns like "New Edition" -> "new"
     and reducing artists named "Special", "Bonus", or "EP" to an empty string.
     Two artists with all-metadata-word names could collide on the same dict key.
  3. `normalize_track_name` used a 13-character hardcoded list while `normalize_name`
     used `str.maketrans(string.punctuation, ...)` covering all 32 ASCII punctuation
     characters. Characters like `&` were inconsistently handled.
  4. `fetch_top_albums_async` (aggregation, timestamp filtering, min_plays/min_tracks)
     had zero test coverage despite being the core business logic function.
- Plan vs implementation: all four defects addressed as described in
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md`. No scope additions or removals.
- Deviations: none.
- Validation:
  - `pytest -q`: **110 passed** (94 pre-existing + 9 new domain tests + 7 new logic tests).
  - `pre-commit run --all-files`: all hooks passed (black reformatted test_domain.py
    on first pass; clean on second).
  - Owner live test: Japanese-title 2025 album (betcover!!) now appears in results
    for listening year 2025 with "Same as release year" filter. Previously absent with
    no unmatched entry. Second validation: same artist's 2021 album (10 unique tracks,
    68 plays) also appeared correctly.
  - "New Edition" self-titled album test: artist key now "new edition" (not "new");
    album deduplication with "(Deluxe Edition)" suffix confirmed still working.
- Forward guidance: no schema, API contract, or route changes. No migration needed.
  The new `test_lastfm_logic.py` file should be extended if `fetch_top_albums_async`
  logic changes (e.g., top-songs feature). Pre-Batch-10 housekeeping is ongoing;
  Batch 10 scope remains TBD by owner.

### 2026-02-20 - fix(tooling): remove transient rotated field from SESSION_CONTEXT status block
- Scope: `scripts/doc_state_sync.py`, `AGENTS.md`.
- Problem: `_build_status_block` wrote `rotated=N` into the managed SESSION_CONTEXT
  block based on the current run's rotation count. The subsequent `--check` always
  recomputed `rotated=0` from the now-clean playbook, causing permanent drift after
  any `--fix --keep-non-current N` run. The workaround required a two-pass sequence.
- Fix: Removed the `Rotated to archive in latest sync run` line from `_build_status_block`.
  The count is still reported on stdout; it is no longer written to a file that `--check`
  re-derives. `--fix --keep-non-current 0` is now a single idempotent command.
- Updated `AGENTS.md` to document the one-pass rotation pattern for agent handoff.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: tooling is stable. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - docs: rotate 4 stale non-current Section 10 entries to archive
- Scope: `PLAYBOOK.md`, `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, `.claude/SESSION_CONTEXT.md`.
- Problem: Four pre-Batch-9 entries (2026-02-19 x2, 2026-02-14 x2) had accumulated
  below `CURRENT-BATCH-END` as `kept_non_current=4` with `rotated=0`, creating
  visible bloat in Section 10.
- Fix: Ran `python scripts/doc_state_sync.py --fix --keep-non-current 0` to flush
  all non-current entries to the archive. Section 10 now contains only active-batch
  entries.
- Deviations: none (purely mechanical doc maintenance).
- Validation:
  - `python scripts/doc_state_sync.py --check`: passed.
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: run `--fix --keep-non-current 0` at each batch boundary to keep
  Section 10 clean.

### 2026-02-20 - WP-7: frontend safety — showToast DOM construction + non-200 fetch guard
- Scope: `static/js/results.js`.
- Problem 1: `showToast` built its HTML via a template-literal string injected with
  `insertAdjacentHTML`. The `message` argument was interpolated without escaping,
  creating an HTML injection pathway if any caller passed server-sourced content.
- Problem 2: `fetchUnmatchedAlbums` piped `fetch()` directly to `.json()` without
  checking `response.ok`. A non-200 response (404, 500, etc.) would be silently
  treated as valid data, surfacing as "No unmatched albums found" instead of an
  error.
- Fix:
  - Rewrote `showToast` to build the toast element tree with `document.createElement`
    / `textContent` / `setAttribute`; eliminated `insertAdjacentHTML` and the unused
    `toastId`. Message content is now set via `.textContent` (XSS-safe).
  - Added `response.ok` guard before `response.json()` in `fetchUnmatchedAlbums`;
    throws `Error("Server error: <status>")` on non-2xx, which the existing `.catch`
    handler surfaces to the user.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: WP-7 complete. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - P1 refactor: extract VALID_FORM_DATA and csrf_app_client fixture
- Scope: `tests/helpers.py`, `tests/conftest.py`, `tests/test_routes.py`.
- Problem: `VALID_FORM_DATA` (the flounder14/2025 form dict for `/results_loading`
  tests) was copy-pasted verbatim 7 times across `test_routes.py`. The 5-line
  CSRF-enabled app + test-client setup was repeated in every CSRF test function.
- Fix:
  - Added `VALID_FORM_DATA` constant to `tests/helpers.py`.
  - Added `csrf_app_client` pytest fixture to `tests/conftest.py`; it creates a
    CSRF-enabled app client (WTF_CSRF_ENABLED not disabled) for CSRF enforcement
    tests.
  - Updated `tests/test_routes.py`: removed `from app import create_app` (now
    unused); imported `VALID_FORM_DATA` from `tests.helpers`; replaced all 7
    inline form dicts with `VALID_FORM_DATA` (or `{**VALID_FORM_DATA, "year": "X"}`
    for year-override cases); replaced all 6 CSRF test inline app setups with the
    `csrf_app_client` fixture parameter.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; pure refactor, no behaviour
    change).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - P1 perf: remove O(n) cache-size scan from cleanup_expired_cache
- Scope: `scrobblescope/utils.py`.
- Problem: `cache_size_mb = sum(len(str(v)) for v in REQUEST_CACHE.values()) / ...`
  ran inside `_cache_lock` on every cleanup call, even when debug logging was
  disabled. This O(n) string-serialization of all cached values held the lock
  unnecessarily and added CPU overhead proportional to cache size.
- Fix: removed the `cache_size_mb` line and simplified the debug log to
  `f"Cache status: {cache_count} entries"`. Count-only logging is sufficient
  for operational visibility; size estimation is not a runtime requirement.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; no test needed for log format).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next P1 item is test boilerplate extraction in
  `test_routes.py` (VALID_FORM_DATA + csrf_app_client fixture).

### 2026-02-20 - P0 fix: delete orphan JOBS entry on thread-start failure
- Scope: `scrobblescope/repositories.py`, `scrobblescope/routes.py`,
  `tests/test_repositories.py`, `tests/test_routes.py`.
- Problem: `create_job()` was called before `start_job_thread()`; on thread-start
  failure the semaphore slot was correctly released by `worker.py`, but the
  `JOBS[job_id]` entry persisted as an orphan until the 2-hour TTL cleanup.
- Fix:
  - Added `delete_job(job_id)` to `repositories.py`:
    `with jobs_lock: JOBS.pop(job_id, None)`.
  - Imported `delete_job` in `routes.py`; called it in the `except` block after
    thread-start failure, before returning the error page.
  - Added 2 tests to `test_repositories.py`:
    `test_delete_job_removes_existing_job`,
    `test_delete_job_on_missing_job_is_noop`.
  - Strengthened existing `test_results_loading_thread_start_failure_renders_error`
    to assert `mock_delete_job.assert_called_once()`.
- Validation:
  - `pytest -q`: **94 passed** (92 pre-existing + 2 new).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: The known orphan-job open risk (SESSION_CONTEXT.md Section 2)
  is now closed. Remaining P1 items: cache_size_mb in `cleanup_expired_cache`,
  and test boilerplate extraction in `test_routes.py`. Next required work package
  is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - README refreshed (Batch 9 completions and roadmap)
- Scope: `README.md`.
- Changes:
  - Python badge updated from `3.9+` to `3.13+`.
  - Removed stale playtime-sorting caveat from Features section.
  - Tech Stack: `Python 3.x` -> `Python 3.13`; added `Flask-WTF` to Core Python
    Libraries bullet.
  - Key Implementation Highlights: added three bullets (Bounded Job Concurrency,
    CSRF Protection, Startup Secret Guard).
  - Project File Structure: added `worker.py`, `test_app_factory.py`,
    `test_utils.py`, `scripts/doc_state_sync.py`.
  - Current Status checklist: added six new `[x]` items for WP-1 through WP-6
    outcomes.
  - Added "Confirmed upcoming features" subsection (top songs, listening heatmap).
  - Added "UI enrichments (planned, lower priority)" subsection.
- Commit: `14f251a` docs: refresh README for Batch 9 completions and roadmap.
- Forward guidance: README is now accurate as of WP-6 completion. Next step is WP-7.

### 2026-02-20 - doc_state_sync maintenance (remove volatile Last sync commit field)
- Scope: `scripts/doc_state_sync.py`, `.claude/SESSION_CONTEXT.md`.
- Issue: `doc-state-sync-check` pre-commit hook was failing on PR merge to main.
  Root cause: `_build_status_block()` called `git rev-parse --short HEAD` to write
  `Last sync commit: <hash>` into SESSION_CONTEXT.md. On `--check`, the command
  returned the NEW merge commit hash, which did not match the stored hash, causing
  drift detection failure on every merge.
- Fix: Removed `_git_head_short()` function, `subprocess` import, and the
  `Last sync commit` line from `_build_status_block`. The `--check` now validates
  only stable content-level fields (batch number, WP numbers, entry count, newest
  heading). Ran `--fix` to drop the stale `Last sync commit` line from
  SESSION_CONTEXT.md.
- Commit: `cdedd65` fix: remove Last sync commit from doc_state_sync status block.
- Forward guidance: The doc-state-sync-check hook will no longer false-positive on
  merge commits. SESSION_CONTEXT DOCSYNC block is validated on content only.

### 2026-02-20 - WP-6 completed (remove artificial orchestration sleeps)
- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Removed all 5 `await asyncio.sleep(0.5)` calls from `_fetch_and_process`. The
    calls were added as a progress-pacing mechanism but served no functional purpose
    and added a fixed 2.5 s latency overhead to every job.
  - All `set_job_progress` calls and their messages are preserved at the same
    progress values (0, 5, 20, 30, 40, 60, 80, 90, 100), so the loading-page
    progress sequence is unchanged from the user's perspective.
  - `asyncio` import retained: `asyncio.Semaphore`, `asyncio.gather`,
    `asyncio.new_event_loop`, and `asyncio.set_event_loop` are still used.
  - Removed two dead `patch("asyncio.sleep", new_callable=AsyncMock)` lines from
    `test_fetch_and_process_cache_hit_does_not_precheck_spotify` and
    `test_fetch_and_process_sets_spotify_error_from_process_albums` in
    `tests/services/test_orchestrator_service.py`. Those patches were no-ops after
    the sleep removals.
- Deviations and why: none. "Gate with debug-only UX flag" option was not needed;
  the plain removal is simpler and all test coverage is already progress-message
  based, not timing based.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (no count change; two dead patches removed,
    no new tests needed).
- Forward guidance: Next work package is WP-7 (frontend safety and resilience
  polish).

### 2026-02-20 - WP-5 completed (enforce registration-year validation server-side)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added a registration-year guard in `results_loading` immediately after the
    `2002..current_year` bounds check. The guard calls `check_user_exists(username)`
    via `run_async_in_thread` (same helper used by `validate_user`). The result is
    already cached from the blur-validation step, so the call is typically free.
  - If `registered_year` is present and `year < registered_year`, the route
    re-renders `index.html` with an explicit error message citing the registration
    year and the earliest valid year.
  - If the check raises (Last.fm unavailable, network error, etc.), a `WARNING`
    is logged and the route proceeds without blocking the user (fail-open policy).
  - If `registered_year` is `None` (not returned by Last.fm), the check is skipped
    and the route proceeds normally.
  - Updated four existing `results_loading` tests that reach the guard to patch
    `scrobblescope.routes.run_async_in_thread` with a neutral result
    (`{"exists": True, "registered_year": None}`) to avoid live network calls.
  - Added four new tests to `tests/test_routes.py`:
    - `test_results_loading_year_below_registration_year_rejected`
    - `test_results_loading_year_at_registration_year_allowed`
    - `test_results_loading_registration_check_unavailable_proceeds`
    - `test_results_loading_no_registered_year_proceeds`
- Deviations and why: none. Fail-open on service unavailability was the intended
  design from the WP-5 spec (client-side validation already covered the common
  case; server-side guard adds defense-in-depth without blocking on transient errors).
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (88 pre-existing + 4 new).
- Forward guidance: Next work package is WP-6 (remove or gate artificial
  orchestration sleeps).

### 2026-02-20 - WP-4 completed (harden app secret and startup safety)
- Scope: `app.py`, `tests/conftest.py`, `tests/test_app_factory.py` (new), `.env.example`, `README.md`.
- Plan vs implementation:
  - Added `_KNOWN_WEAK_SECRETS = frozenset({"dev", "changeme_in_production", ""})` and `_MIN_SECRET_LENGTH = 16` constants in `app.py`.
  - Added `_validate_secret_key(secret_key: str, is_dev_mode: bool) -> None` in `app.py`. Logic: if key is falsy, in weak set, or shorter than 16 chars -> "weak". In production (`debug_mode=False`): raises `RuntimeError("Refusing to start: ...")`. In dev mode (`DEBUG_MODE=1`): logs `WARNING "SECRET_KEY is missing or insecure. ..."`.
  - Updated `create_app()` to read `_raw_secret = os.getenv("SECRET_KEY", "")`, call `_validate_secret_key(_raw_secret, debug_mode)`, then set `application.secret_key = _raw_secret or "dev"`. "dev" is the dev-mode fallback; in production, `_validate_secret_key` raises before it can be used.
  - `tests/conftest.py` updated: added `import os` + `os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")` before `from app import create_app`. This seeds the guard before `app.py`'s module-level `create_app()` call (which runs at import time).
  - New `tests/test_app_factory.py` with 7 tests: production-fail on missing/dev/changeme/too-short keys; dev-mode warning; strong-key success in both modes.
  - `.env.example` `SECRET_KEY` comment updated to say "REQUIRED in production. Startup fails if missing or set to placeholder."
  - `README.md` setup step 4 comment updated from "Recommended" to "Required in production" with note that `DEBUG_MODE=1` suppresses the check for local dev.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black reformatted `app.py` quote style on first run; clean on second).
  - `pytest -q`: **88 passed** (81 pre-existing + 7 new).
- Commit: `eb13a27` feat: refuse startup on weak SECRET_KEY in production.
- Forward guidance: Next work package is WP-5 (enforce registration-year validation server-side).

### 2026-02-20 - WP-1 correctness fix (slot leak on Thread.start failure)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Issue: WP-1 post-audit check found that `acquire_job_slot()` in `results_loading` was not guarded against failure of `Thread.__init__` or `Thread.start()`. If either raises (e.g. `OSError` under OS-level thread exhaustion), the slot is permanently consumed because `background_task`'s `finally` block never runs. This violates WP-1's acceptance criterion "no leaked active slots after worker exceptions."
- Fix:
  - Added `release_job_slot` to imports in `routes.py`.
  - Wrapped `threading.Thread(...)` and `task_thread.start()` in try/except; on exception: `release_job_slot()`, `logging.exception(...)`, return `index.html` with error message.
  - Added `test_results_loading_thread_start_failure_releases_slot`: patches `Thread` to raise `OSError`, asserts slot is released and index re-rendered.
- Validation:
  - `pre-commit run --all-files`: all hooks passed.
  - `pytest -q`: 77 passed.
- Also: added "callers must not mutate" to `get_cached_response` docstring (latent mutable-reference risk; no active bug since no caller mutates the returned object).

### 2026-02-20 - Comprehensive repo audit completed + Batch 9 remediation plan authored
- Scope: full-codebase audit (backend Python, frontend templates/JS/CSS, tests/CI/config/docs), plus operational handoff planning.
- Plan vs implementation:
  - Performed a severity-ranked audit focused on security, reliability, correctness, and optimization pathways.
  - Identified concrete high/medium/low findings with file-level references.
  - Authored actionable execution plan for next agent:
    - `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`
    - Includes WP-1..WP-8, acceptance criteria, and execution order.
  - Updated this playbook and session context to treat Batch 9 as the active next execution track.
- Validation:
  - `venv\Scripts\python -m pytest tests --cov=scrobblescope --cov-report=term-missing -q`: **66 passed**, overall coverage **72%**.
  - Coverage highlighted lower-tested hotspots used to seed Batch 9 work-package ordering (`lastfm.py`, `utils.py`, `spotify.py`, portions of `orchestrator.py`).
- Forward guidance:
  - Execute WP-1 and WP-2 first (highest reliability risk reduction).
  - Keep documentation synchronized after each work package per Section 8.

### 2026-02-20 - Batch 9 WP-8 completed (CI, lint, dependency hygiene)
- Scope: `.pre-commit-config.yaml`, `requirements.txt`, `requirements-dev.txt` (new), `.gitignore`, `.github/workflows/test.yml`.
- Plan vs implementation:
  - Fixed `check-yaml` pre-commit hook: changed `files: ^.*\.py$` to `files: ^.*\.(yaml|yml)$` so the hook validates YAML files rather than Python files. Removed `.github` from the global `exclude` pattern so `.github/workflows/test.yml` is now reachable by `check-yaml`.
  - Split runtime vs dev dependencies: moved `pre-commit`, `pytest`, `pytest-asyncio`, `pytest-cov` from `requirements.txt` into new `requirements-dev.txt`. Added `flake8` explicitly to `requirements-dev.txt`. `requirements-dev.txt` includes `-r requirements.txt` so a single install covers everything for dev.
  - Added `.coverage` to `.gitignore` (coverage artifact from pytest-cov runs).
  - Updated `.github/workflows/test.yml`: install step now uses `requirements-dev.txt`; removed redundant `pip install pre-commit` and `pip install flake8` lines (covered by requirements-dev.txt); added `--cov=scrobblescope --cov-fail-under=70` to pytest invocation.
- Deviations and why:
  - Coverage threshold set at 70% (current measured: ~72%) to provide a realistic floor without false-failing immediately; can be tightened once new feature coverage is added.
  - `flake8` added explicitly to `requirements-dev.txt` so the direct `flake8 --config .flake8` CI step can rely on it rather than pre-commit's isolated env.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (check yaml now runs against .yaml/.yml files and passes for `.pre-commit-config.yaml` and `.github/workflows/test.yml`).
  - `venv\Scripts\python -m pytest tests -q`: 94 passed (no regressions).
- Forward guidance:
  - Batch 9 remediation complete. Next tracks are product feature batches: **Top songs** (rank most-played tracks per year) and **Listening heatmap** (scrobble density calendar, Last.fm-only).
  - Coverage gate starts at 70%; aim to raise the threshold incrementally as new features gain test coverage.

### 2026-02-20 - worker.py architectural decision + product roadmap + CSRF coverage expansion

- Scope: Documentation updates only (`.claude/SESSION_CONTEXT.md`, `EXECUTION_PLAYBOOK_2026-02-11.md`). No runtime code changes yet.
- Decisions made:
  - **Product roadmap confirmed:** Two additional background task types are planned -- "top songs" (Last.fm + possibly Spotify, separate background task/results flow) and "listening heatmap" (Last.fm only, last 365 days, lighter task). This means the `results_loading` acquire->Thread->release pattern will be needed by at least 3 routes.
  - **worker.py chosen as home for concurrency lifecycle:** With multiple background task types incoming, keeping the semaphore and thread-start boilerplate in `repositories.py` would require each new route to duplicate the `acquire -> try Thread.start -> except release` block. A new `scrobblescope/worker.py` leaf module (imports `config` only) will own `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread(target, args=())`. `repositories.py` becomes pure job state CRUD. `start_job_thread()` encapsulates the full try/start/except/release pattern for all callers.
  - **Refactor must precede the 3-commit save-state:** WP-1 originally placed the semaphore in `repositories.py`. The worker.py refactor corrects this before committing; the WP-1 commit will reflect the final architecture.
- CSRF test coverage expansion (also completed this session, before context compaction):
  - Initial WP-3 implementation added 2 CSRF tests covering only `/results_loading`.
  - Expanded to 6 total CSRF tests covering all 4 POST routes:
    - `test_csrf_rejects_post_without_token` (-> `/results_loading` 400)
    - `test_csrf_accepts_post_with_valid_token` (-> `/results_loading` 200)
    - `test_csrf_rejects_results_complete_without_token` (-> 400)
    - `test_csrf_rejects_unmatched_view_without_token` (-> 400)
    - `test_csrf_rejects_reset_progress_without_token` (-> 400)
    - `test_csrf_accepts_reset_progress_with_header_token` (-> `/reset_progress` XHR path with `X-CSRFToken` header, 200)
  - Total tests after expansion: **81 passing**.
- Pending implementation (next agent actions in order):
  1. Create `scrobblescope/worker.py` with semaphore, `acquire_job_slot()`, `release_job_slot()`, `start_job_thread()`.
  2. Remove semaphore/slot functions from `scrobblescope/repositories.py`.
  3. Update imports in `routes.py` and `orchestrator.py` to use `worker`.
  4. Update patch targets in `test_routes.py` and `test_orchestrator_service.py` from `scrobblescope.routes.acquire_job_slot` / `scrobblescope.orchestrator.release_job_slot` -> `scrobblescope.worker.*`.
  5. Run `pre-commit run --all-files` and `pytest -q` (must stay at 81 passing).
  6. Make 3 separate commits: WP-1, WP-2, WP-3.
- Validation: N/A (doc-only session-end update).
- Forward guidance:
  - worker.py is a leaf module -- it must NOT import from `repositories`, `routes`, `orchestrator`, or any higher module (would create cycles).
  - `start_job_thread()` should release the slot and raise on `Thread.start()` failure so routes get a clean exception to handle (mirrors the current try/except pattern in `routes.py`).
  - After the 3 commits are made, next work package is WP-4 (harden app secret and startup safety).

### 2026-02-19 - Batch 9 WP-3 completed (CSRF protection for mutating POST routes)
- Scope: `requirements.txt`, `app.py`, `templates/index.html`, `templates/results.html`, `templates/loading.html`, `static/js/loading.js`, `tests/conftest.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added `Flask-WTF>=1.2.0` to `requirements.txt` (installed v1.2.2).
  - Added `CSRFProtect` to `app.py`: `csrf = CSRFProtect()` at module level, `csrf.init_app(application)` in `create_app()`, plus a `CSRFError` handler that returns a 400 with the `error.html` template and a user-facing message.
  - Added `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` inside the `<form>` element in `templates/index.html` and `templates/results.html` (unmatched_view form).
  - Added `<meta name="csrf-token" content="{{ csrf_token() }}">` to the `head_extra` block in `templates/loading.html`.
  - Updated `static/js/loading.js`:
    - Added `const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';` near the top (after the `window.SCROBBLE` destructure).
    - Prepended `form.appendChild(createHiddenInput('csrf_token', csrfToken));` as the first hidden input in both `redirectToResults()` and `retryCurrentSearch()`.
    - Added `'X-CSRFToken': csrfToken` to the headers of the `fetch('/reset_progress', ...)` call in the error handler.
  - Updated `tests/conftest.py`: added `application.config["WTF_CSRF_ENABLED"] = False` so all existing tests continue to pass without supplying tokens.
  - Added two CSRF tests to `tests/test_routes.py`:
    - `test_csrf_rejects_post_without_token`: creates a CSRF-enabled app client, POSTs without a token, asserts 400.
    - `test_csrf_accepts_post_with_valid_token`: GETs `/` to capture the token from the rendered HTML, POSTs with it, asserts 200 and `window.SCROBBLE` in response.
- Deviations and why: none.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8, trim, end-of-file).
  - `pytest -q`: 76 passed (2 new tests added).
- Forward guidance:
  - WP-4 (secret hardening) is the next work package.
  - The `WTF_CSRF_ENABLED = False` fixture override is intentional and standard; it must remain in `conftest.py` to keep all POST route tests free of token boilerplate.
  - Flask-WTF validates the token from `request.form['csrf_token']` for form POSTs and from `X-CSRFToken` header for XHR/fetch POSTs. Both paths are now covered.

### 2026-02-19 - Batch 9 WP-2 completed (thread-safe REQUEST_CACHE)
- Scope: `scrobblescope/utils.py`, `tests/test_utils.py` (new file).
- Plan vs implementation:
  - Added `_cache_lock = threading.Lock()` to guard all `REQUEST_CACHE` access in `utils.py`.
  - Wrapped `get_cached_response` in `_cache_lock` to eliminate TOCTOU between `key in REQUEST_CACHE` and `REQUEST_CACHE[key]`.
  - Wrapped `set_cached_response` in `_cache_lock` for atomic writes.
  - Wrapped the full iterate-and-pop sequence in `cleanup_expired_cache` in `_cache_lock` to prevent `RuntimeError: dictionary changed size during iteration`. Cache count and size captured inside the lock; logging calls happen outside to minimize hold time.
  - Created `tests/test_utils.py` (6 tests): cache hit, absent miss, expired miss, overwrite, cleanup correctness, and a concurrent-write-plus-cleanup stress test with 6 threads.
- Deviations and why: none.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: 74 passed (6 new tests in `test_utils.py`).
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (black auto-reformatted `utils.py` on first run; re-run confirmed clean).
- Forward guidance:
  - WP-3 (CSRF protection for mutating POST routes) is the next work package.
  - `_cache_lock` is importable from `scrobblescope.utils` if future tests or modules need to inspect or clear the cache safely.

### 2026-02-19 - Batch 9 WP-1 completed (bound background job concurrency)
- Scope: `scrobblescope/config.py`, `scrobblescope/repositories.py`, `scrobblescope/routes.py`, `scrobblescope/orchestrator.py`, `tests/test_routes.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Added `MAX_ACTIVE_JOBS = int(os.getenv("MAX_ACTIVE_JOBS", "10"))` to `config.py`.
  - Added `_active_jobs_semaphore = threading.BoundedSemaphore(MAX_ACTIVE_JOBS)` to `repositories.py`.
  - Added `acquire_job_slot()` (non-blocking acquire, returns bool) and `release_job_slot()` (safe release with over-release guard) to `repositories.py`.
  - In `routes.py` `results_loading`: capacity check runs after `cleanup_expired_jobs()` and before `create_job()`; if at capacity, re-renders `index.html` with a retryable error message (no thread spawned, no job created).
  - In `orchestrator.py` `background_task`: `release_job_slot()` called in the `finally` block after `loop.close()`, guaranteeing release on all termination paths (success, handled exception, unhandled exception).
- Deviations and why:
  - Default of 10 (not lower) chosen to match existing concurrency constants and be tunable via `MAX_ACTIVE_JOBS` env var without code changes.
  - Capacity rejection renders `index.html` (same as other input validation errors) rather than a JSON 503, keeping the UX flow consistent with the existing form-submission error pattern.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: 68 passed (2 new tests added: capacity-rejection route test + release-on-exception orchestrator test).
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8, trim, end-of-file).
- Forward guidance:
  - WP-2 (make `REQUEST_CACHE` thread-safe) is the next work package.
  - The `_active_jobs_semaphore` is process-global; it resets on restart. Under Fly.io single-VM deployment this is correct behavior.
  - If the operator wants to verify slot release under real traffic, check logs for `release_job_slot called with no matching acquire` warning (should never appear in normal operation).

### 2026-02-19 - Fly cold-start recovery validation completed (app + Postgres DB)
- Scope: operational validation of deployed services and documentation refresh (`.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`).
- Plan vs implementation:
  - Confirmed both machines were started (`fly status -a scrobblescope`, `fly status -a scrobblescope-db`).
  - Forced cold state by stopping both machines:
    - `fly machine stop 807339f1595248 -a scrobblescope`
    - `fly machine stop 8e7ed9ad205118 -a scrobblescope-db`
  - Verified both reported `State: stopped` via `fly machine status`.
  - Triggered one end-to-end request:
    - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 1 --timeout-seconds 180`
  - Verified smoke run completion and auto-start behavior for both app and DB machines.
  - Rechecked DB health until all checks passed (`pg`, `role`, `vm`).
- Deviations and why:
  - No code changes were required; this was an operational verification step requested by the owner.
- Validation:
  - Smoke output: `elapsed=18.75s`, `db_cache_enabled=True`, `db_cache_lookup_hits=247`, `db_cache_persisted=0`, `spotify_matched=247`, message `Done! Found 57 albums matching your criteria.`
  - Post-run status: app machine `started`, DB machine `started`, DB checks all passing.
- Forward guidance:
  - Keep this cold-start check as a regression smoke pattern after infra/config changes.
  - If cold-start latency grows, tune DB wake-up retry knobs (`DB_CONNECT_MAX_ATTEMPTS`, `DB_CONNECT_BASE_DELAY_SECONDS`) and/or Fly machine warmness settings.

### 2026-02-19 - Context reconciliation completed (docs parity + cache fallback logging classification)
- Scope: `.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`, `scrobblescope/cache.py`, `tests/test_repositories.py`.
- Plan vs implementation:
  - Re-verified playbook/session claims against the active repo for `init_db.py`, thread model, and cache fallback behavior.
  - Refreshed stale status fields (latest commit snapshot, app.py line count, and current runtime notes).
  - Updated `_get_db_connection()` to log explicit fallback categories:
    - `asyncpg-missing`
    - `missing-env-var`
    - `db-down`
  - Extended DB helper tests to assert those log categories are emitted on each path.
- Deviations and why:
  - No keep-alive thread was added to `app.py`; this is intentional because the current architecture uses per-job daemon worker threads from `results_loading` and avoids additional idle background loops.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed** (2 deprecation warnings from aiohttp connector behavior on Python 3.13.3).
- Forward guidance:
  - Keep Section 2 and `.claude/SESSION_CONTEXT.md` synchronized whenever runtime snapshots (line counts, branch/commit status, logging behavior) change.

### 2026-02-14 - Repository hygiene completed (historical docs archive + README refresh)
- Scope: `docs/history/` (new folder), historical markdown moves, `PLAYBOOK.md`, `README.md`.
- Plan vs implementation:
  - Moved historical docs from repo root into `docs/history/`:
    - `AUDIT_2026-01-10.md`
    - `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`
    - `CHANGELOG_2026-01-04.md`
    - `CHANGELOG_2026-02-10.md`
    - `OPTIMIZATION_SUMMARY.md`
    - `PERFORMANCE_TIMING.md`
    - `Refactor_Plan.md`
    - `TEMPLATE_REFACTOR_SUMMARY.md`
  - Updated playbook references to `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`.
  - Refreshed `README.md`:
    - run instructions now show `python app.py` (recommended) and `python run.py` (optional launcher)
    - project structure updated to current modular layout + `docs/history/`
    - roadmap/status text updated to reflect current post-refactor state
- Deviations and why:
  - Keep a shim at `EXECUTION_PLAYBOOK_2026-02-11.md` to preserve a stable handoff entrypoint.
- Forward guidance:
  - Keep new planning/audit/changelog docs in `docs/history/` unless a document is an active operator runbook.
  - Keep playbook and session-context docs at predictable top-level locations for fast bootstrap.

### 2026-02-14 - Cache wake-up hardening completed (DB connect retry/backoff + docs refresh)
- Scope: `scrobblescope/cache.py`, `tests/test_repositories.py`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Added exponential-backoff DB connection retries in `_get_db_connection()` to reduce false cache bypass during Fly Postgres wake-up windows.
  - Added two DB helper tests:
    - retry-then-success path
    - retry-exhaustion path
  - Updated existing connect-failure test to force single-attempt behavior (`DB_CONNECT_MAX_ATTEMPTS=1`) for deterministic assertions.
  - Refreshed handoff docs for the new test count and operational behavior.
- Deviations and why:
  - No orchestration/routing behavior changes were needed; hardening was isolated to cache connection setup and DB helper tests.
- Additions beyond plan:
  - Added env-tunable retry knobs:
    - `DB_CONNECT_MAX_ATTEMPTS` (default `3`)
    - `DB_CONNECT_BASE_DELAY_SECONDS` (default `0.25`)
  - Live Fly verification confirmed:
    - app cache hits persisted after DB stop/start
    - DB app `scrobblescope-db` uses `FLY_SCALE_TO_ZERO=1h`, explaining suspended/stopped state after idle periods.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
  - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`: **PASS** (`db_cache_enabled=True`, `db_cache_lookup_hits=247`).
- Forward guidance:
  - If first-request latency after idle is a concern, either increase retry knobs or adjust/remove DB `FLY_SCALE_TO_ZERO`.
  - Keep periodic smoke checks as operational validation for cache persistence and warm-hit behavior.
  - Resolve DB app staged secrets drift (`fly secrets deploy -a scrobblescope-db`) to avoid config ambiguity.

### 2026-02-14 - Frontend responsiveness polish completed (toggle placement + mobile table scaling)
- Scope: `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`, `static/css/unmatched.css`, `static/css/error.css`, `templates/results.html`.
- Plan vs implementation:
  - Standardized dark-mode toggle to a compact fixed bottom control across all page CSS bundles.
  - Improved `index.html` mobile fit by tightening spacing, typography, and card/logo sizing at mobile breakpoints.
  - Improved `results.html` mobile readability by shrinking table density, making actions stack cleanly, and reducing album-art footprint.
  - Added `results-table` class in template for targeted responsive behavior.
  - Centered decade pills in `index` filter UI.
- Deviations and why:
  - To improve fit on common phones, responsive rules were applied up to `max-width: 767.98px` for index/results rather than only `575.98px`.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - If users still report table crowding on very small devices, next step is card-style row rendering for results instead of a dense 5-column table.
  - Consider extracting shared toggle CSS into one common stylesheet to reduce cross-file duplication.

### 2026-02-14 - Post-Batch-8 hardening completed (low-severity gap closure + test layout split)
- Scope: `tests/test_routes.py`, `tests/conftest.py`, `tests/helpers.py` (new), `tests/services/` (new split files), `EXECUTION_PLAYBOOK_2026-02-11.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Closed previously identified low-severity gaps:
    - Added direct route tests for `/unmatched_view` (missing `job_id`, missing job, success render path).
    - Added explicit tests for app-level 404 and 500 handlers.
  - Reduced test coupling to `conftest.py` internals:
    - Moved shared constants/mock helpers into `tests/helpers.py`.
    - Updated tests to import from `tests.helpers` rather than `conftest`.
  - Split monolithic service test file:
    - Removed `tests/test_services.py`.
    - Added `tests/services/test_lastfm_service.py` (4 tests).
    - Added `tests/services/test_spotify_service.py` (3 tests).
    - Added `tests/services/test_orchestrator_service.py` (10 tests).
- Deviations and why:
  - No runtime code changes were required. This was a test architecture and coverage hardening pass only.
  - Added one extra test category beyond the initial gap list (500 handler integration path) because this was explicitly untested and low effort/high confidence.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **64 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - Subpackage migration should be sequenced **after** the next feature-heavy batch set (Batch 9+) stabilizes, not before. Keep current flat module layout while churn is high; cut to subpackages once contracts settle.
  - Keep route-handler coverage and helper-module pattern as baseline for future test additions.

### 2026-02-13 - Batch 8 completed (modular refactor -- app factory + blueprints + layered structure)
- Scope: `app.py` (rewritten), `scrobblescope/` package (9 new modules), `tests/` (4 test files + conftest replacing monolithic `test_app.py`).
- Plan vs implementation:
  - Followed the approved 7-slice strangler plan exactly. All 59 tests remained green after every slice.
  - Slice 1: `config.py` + `domain.py` + `conftest.py` + `test_domain.py` (6 tests)
  - Slice 2: `utils.py` (rate limiters, session, caching, helpers)
  - Slice 3: `repositories.py` + `cache.py` + `test_repositories.py` (14 tests)
  - Slice 4: `lastfm.py` + `spotify.py` + partial `test_services.py` (7 tests)
  - Slice 5: `orchestrator.py` + remaining `test_services.py` (10 more tests, 17 total)
  - Slice 6: `routes.py` (Blueprint) + `test_routes.py` (22 tests) + `app.py` factory rewrite
  - Slice 7: Cleanup and documentation updates
- Deviations and why:
  - Plan estimated 19 tests in `test_services.py` and 20 in `test_routes.py`; actual counts are 17 and 22 respectively (same 59 total). Two tests moved between files for better logical grouping.
  - `create_app()` lives in `app.py` (project root) rather than `scrobblescope/__init__.py` -- keeps Flask template/static path resolution simple and `gunicorn app:app` backward compatible.
- Key architectural outcomes:
  - `app.py` reduced from ~2091 lines to ~91 lines (factory pattern only).
  - Acyclic dependency graph: `domain`/`config` -> `utils` -> `cache` -> `repositories` -> `lastfm`/`spotify` -> `orchestrator` -> `routes` -> `app`.
  - No circular imports. Each module imports only from modules above it in the hierarchy.
  - Flask Blueprint (`bp = Blueprint("main", __name__)`) with `@bp.app_errorhandler` for 404/500 and `@bp.app_context_processor` for template injection.
  - `# noqa: F401` re-export pattern used during transitional slices, fully removed in Slice 6.
  - Patch targets updated throughout: `"app.X"` -> `"scrobblescope.<module>.X"` in all test files.
- Validation:
  - `pytest tests/ -q`: 59 passed (6 + 14 + 17 + 22 across 4 test files)
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8)
  - `python -c "from app import app; print(app)"`: Gunicorn import verified
  - Dockerfile (`gunicorn app:app`) and fly.toml (`release_command = "python init_db.py"`) unchanged and compatible
- Forward guidance:
  - All batches (1-8) are complete. No further structural refactor is planned.
  - Deployment: `app.py` factory + module-level `app = create_app()` is backward compatible with `gunicorn app:app`.
  - Test convention: patch at the module where the name is looked up (e.g., `"scrobblescope.orchestrator._get_db_connection"`).
  - Adding new routes: add to `scrobblescope/routes.py` using `@bp.route(...)`.
  - Adding new service functions: add to the appropriate module (`lastfm.py`, `spotify.py`, `orchestrator.py`, etc.).

### 2026-02-13 - Batch 7 hardening addendum (cache-orchestrator correctness + smoke validation path)
- Scope: `app.py`, `tests/test_app.py`, `README.md`, `scripts/smoke_cache_check.py`, this playbook.
- Plan vs implementation:
  - Batch 7 intent said full cache hits should avoid Spotify dependency.
  - Implementation was corrected to match intent by removing `_fetch_and_process` Spotify pre-check and making Spotify-unavailable signaling explicit.
- Deviations and why:
  - Added `SpotifyUnavailableError` instead of generic string matching to avoid false "successful empty results" when Spotify token fetch fails on all misses.
  - Added partial-response behavior: when token fetch fails but cache hits exist, return cached subset and set `partial_data_warning`.
- Additions beyond plan:
  - Added deploy-targeted smoke utility: `scripts/smoke_cache_check.py` for warm-cache verification (`flounder14`, `2025` defaults supported).
  - Added cache observability stats in `process_albums`: `db_cache_enabled`, `db_cache_lookup_hits`, `db_cache_persisted`, and `db_cache_warning`.
  - README now documents persistent cache behavior and smoke-test usage.
- Struggles/constraints and unresolved risks:
  - End-to-end cache validation against live Fly/Postgres cannot be fully asserted by unit tests; smoke script is provided for operational verification.
  - Existing heuristic that treats "all unmatched == Spotify unavailable" remains unchanged and should be revisited during Batch 8 service extraction.
  - Initial smoke run (pre-deploy) was inconclusive (`cache_hits=0` both runs) because Fly was still running Batch 6 code. Root cause resolved by deploying with Postgres attached.
- Validation performed:
  - `pytest -q`: 59 passed.
  - `pre-commit run --all-files`: all hooks passed.
  - **Post-deploy smoke test (PASS):**
    - Postgres provisioned: `scrobblescope-db` (unmanaged, yyz region)
    - Attached via `fly postgres attach scrobblescope-db --app scrobblescope` (auto-set `DATABASE_URL`)
    - `python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`:
      - Run 1 (cold): 41.84s, `cache_hits=0`, `db_cache_persisted=243`, `spotify_matched=243`
      - Run 2 (warm): 4.34s, `cache_hits=243`, `db_cache_lookup_hits=243`, `db_cache_persisted=3`
      - **~10x speedup on warm cache. Verdict: PASS.**
  - New tests added:
    - `process_albums` all-miss token failure raises classified exception.
    - `process_albums` partial cache hit + token failure returns cached subset and warning stat.
    - `_fetch_and_process` no longer directly pre-checks Spotify token.
    - `_fetch_and_process` maps `SpotifyUnavailableError` to `spotify_unavailable` job error.
- Forward guidance for next agent:
  - Cache is deployed and verified. No further infra steps needed before Batch 8.
  - Fly Postgres instance `scrobblescope-db` is unmanaged, single-node. Consider auto-stop to save cost when idle.
  - Keep Batch 8 refactor parity tests for the error/warning paths (`SpotifyUnavailableError`, `partial_data_warning`) before moving orchestration into service modules.
  - Local dev has no `DATABASE_URL` -- cache is disabled locally (by design). All cache behavior is tested via mocks in the test suite.

### 2026-02-13 - Operational config fix (Fly machine autostop)
- Scope: `fly.toml`.
- Issue:
  - Fly log showed autostop with `0 out of 1 machines left running` because `min_machines_running` was set to `0`.
- Change:
  - Updated `[http_service] min_machines_running = 1` to keep one machine warm.
- Notes:
  - This log means capacity scaling, not cache overflow.
  - In-memory caches (`REQUEST_CACHE`, `JOBS`) live in RAM on the app VM and are lost on machine stop/restart.
  - Persistent Spotify metadata cache lives in Fly Postgres (`spotify_cache`) via `DATABASE_URL`.

### 2026-02-12 - Batch 7 completed (persistent Spotify metadata cache -- Postgres via asyncpg)
- Scope: `requirements.txt`, `.env.example`, `init_db.py` (new), `fly.toml`, `app.py`, `tests/test_app.py`.
- Implementation:
  - **requirements.txt:** Added `asyncpg>=0.29.0`; removed unused `redis` and `Flask_Caching`.
  - **.env.example:** Added `DATABASE_URL` placeholder with Fly.io context comment.
  - **init_db.py (new):** Standalone schema init script. Reads `DATABASE_URL`, creates `spotify_cache` table via `asyncpg`. Runs as Fly `release_command`. Idempotent; exits 0 on success or no-op, exits 1 on failure (rolls back deploy).
  - **fly.toml:** Added `[deploy] release_command = "python init_db.py"`.
  - **app.py -- 3 new helper functions:**
    - `_get_db_connection()`: Returns `asyncpg.Connection` or `None` (graceful fallback).
    - `_batch_lookup_metadata(conn, keys)`: Single SELECT with `unnest()`, 30-day TTL filter, JSONB deserialization.
    - `_batch_persist_metadata(conn, rows)`: Single INSERT with `unnest() ... ON CONFLICT DO UPDATE`. True single-statement batch (not executemany).
  - **app.py -- `process_albums` rewritten** with 5-phase flow:
    - Phase 1: DB batch lookup (try/except, fallback to empty dict).
    - Phase 2: Partition into cache_hits and cache_misses.
    - Phase 3: Spotify fetch for misses only (entire block guarded by `if cache_misses:` -- zero API calls on full cache hit).
    - Phase 4: DB batch persist + `conn.close()` in `finally`.
    - Phase 5: Build results from unified cache_hits dict -- identical output shape regardless of source.
  - **tests/test_app.py -- 12 new tests (43 -> 55):**
    - 7 DB helper unit tests: `_get_db_connection` (no asyncpg, no URL, connect failure), `_batch_lookup_metadata` (empty keys, JSONB parsing), `_batch_persist_metadata` (empty rows, upsert call shape).
    - 5 process_albums integration tests: full cache hit skips Spotify, full cache miss fetches and persists, DB unavailable falls back, conn always closed, empty input.
- Deviations:
  - Plan called for ~14 tests; implemented 12 (skipped init_db.py tests as the script is trivially simple and tested indirectly by the release_command pattern).
  - `METADATA_CACHE_TTL_DAYS` made configurable via env var (default 30) -- not in original plan but natural extension.
- Validation:
  - `pytest -q`: 55 passed
  - `pre-commit run --all-files`: all hooks passed
  - Local dev without `DATABASE_URL`: app functions identically to pre-Batch-7
- Notes:
  - Connection always closed via `finally` block, even on Spotify errors.
  - Full cache hit path: zero Spotify API calls (verified via mock assertions -- no token fetch, no session, no search).
  - Next batch is Batch 8 (modular refactor).

### 2026-02-12 - Batch 6 completed (frontend refinement/tweaks)
- Scope: Templates, CSS, JS, and tests -- no app.py changes.
- Implementation:
  - **index.html error alert:** Added `{% if error %}` block with Bootstrap `alert-danger` component above the form card. Errors from `results_loading` (missing username, bad year) now render visibly.
  - **Dark-mode toggle mobile fix:** Added `@media (max-width: 575.98px)` rules to all 5 CSS files (index, loading, results, unmatched, error) repositioning the toggle from `top: 1rem` to `bottom: 1rem` on small screens.
  - **Username submission guard:** Added `setCustomValidity()` to `index.js` so that a username flagged invalid by the AJAX blur check blocks native form submission. An `input` listener clears the block when the user types a new name. Network errors fall through to server-side validation.
  - **Encoding artifacts:** Investigated all JS files -- no artifacts found. `encodeURIComponent()`, `.textContent`, and `escapeHtml()` are used correctly. No action needed.
  - **Test enhancements:** Updated `test_results_loading_missing_username` and `test_results_loading_year_out_of_bounds` to assert error message text is present in the response, confirming the alert block renders.
- Deviations: Username submission guard was not in the original playbook scope but was a clear UX gap identified during Batch 6 work.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed
- Notes:
  - No new tests added (existing tests enhanced with assertions).
  - Next batch is Batch 7 (persistent metadata layer).

### 2026-02-12 - Batch 5 completed (docstring + comment normalization)
- Scope: `app.py` only -- docstrings and comments; no behavior changes.
- Implementation:
  - **Added docstrings to 16 previously undocumented top-level functions:**
    `_get_loop_limiter`, `run_async_in_thread`, `inject_current_year`,
    `_initial_progress`, `cleanup_expired_jobs`, `create_job`, `set_job_progress`,
    `set_job_stat`, `set_job_results`, `add_job_unmatched`, `reset_job_state`,
    `get_job_progress`, `get_job_unmatched`, `get_job_context`,
    `fetch_recent_tracks_page_async`, `fetch_spotify_access_token`, `results_complete`.
  - **Removed 11 redundant or stale pre-function comments** that duplicated what the docstring already says or used stale language ("improved", "update the ... route").
  - **Relocated one misleading comment** ("Enable ANSI escape codes on Windows cmd") from the `import sys` line to the actual `os.system("")` call where the enabling happens.
  - **Docstring style:** short summary line, optional detail paragraph -- consistent with `get_spotify_limiter` as the reference standard.
  - **Inner/nested functions** (11 closures like `fetch_once`, `clean`, `search_with_semaphore`) were intentionally left without docstrings as they are self-descriptive from naming and parent function context.
- Deviations: None.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed (isort auto-fixed import grouping after comment removal; re-run confirmed clean)
- Notes:
  - `app.py` line count decreased slightly due to comment removal (~1800 -> ~1790).
  - All 49 top-level functions in app.py now have docstrings (100% coverage).
  - Next batch is Batch 6 (frontend refinement/tweaks).

### 2026-02-12 - Batch 4 closure addendum (missing coverage completed)
- Scope: `tests/test_app.py` only.
- Implementation:
  - Added `/reset_progress` route coverage:
    - missing `job_id` -> 400
    - nonexistent `job_id` -> 404
    - success path resets progress/results/unmatched state
  - Added service-level async retry/error tests for:
    - `fetch_recent_tracks_page_async` (429 retry -> success, 404 -> raises ValueError)
    - `search_for_spotify_album_id` (429 retry -> returns ID)
    - `fetch_spotify_album_details_batch` (429 retry -> success, non-200 -> empty dict)
- Reasoning:
  - Closed the two explicit Batch 4 gaps noted in handoff docs before proceeding to Batches 5/7/8.
  - Prioritized deterministic tests by mocking limiter contexts and `asyncio.sleep`.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed
- Notes:
  - Batch 4 is now fully closed from a coverage perspective.

### 2026-02-12 - Batch 4 completed (expanded test coverage)
- Scope: `tests/test_app.py` only -- 23 new tests added (12 -> 35 total).
- Implementation:
  - **Job lifecycle (5 tests):** unique IDs, job isolation, missing-job guard, stat storage, TTL expiry cleanup.
  - **Route coverage (9 tests):** `/progress` 400+404, `/results_loading` valid+missing+out-of-bounds, `/results_complete` missing+expired+with-data, `/validate_user` too-long+not-found, `/unmatched` 400+data.
  - **Normalization (3 tests):** remastered suffix stripping, Unicode preservation, track name punctuation.
  - **Registration year (2 tests):** valid timestamp extraction, missing key graceful fallback.
  - **Template safety (folded into route tests):** `window.SCROBBLE` tojson bridge in loading page, `window.APP_DATA` tojson bridge in results page.
  - **Background task structural (1 test):** `background_task` runs `_fetch_and_process` in a single event loop with no inner thread (Batch 3 regression guard). `/results_loading` verified to create a daemon thread targeting `background_task`.
- Deviations:
  - `index.html` does not render the `error=` variable passed by `results_loading` on validation failure. Tests were adjusted to verify the correct page is returned (index form, not loading page) rather than asserting specific error text. This is a minor UX gap that could be addressed in Batch 6 (frontend tweaks).
- Notes:
  - All 35 tests pass. All pre-commit hooks pass (black, isort, autoflake, flake8).
  - No changes to `app.py` or any other file -- tests-only batch.
  - Next batch is Batch 5 (docstring + comment normalization).

### 2026-02-12 - Batch 3 completed (nested thread removal)
- Scope: `app.py` only for runtime behavior, plus this playbook status/log update.
- Implementation:
  - Extracted nested `fetch_and_process` closure into top-level async function `_fetch_and_process`.
  - Reworked `background_task` to create/use a single event loop directly on the already-created worker thread.
  - Removed `background_task -> run_async_in_thread(...)` indirection to eliminate the second per-job thread.
  - Kept `run_async_in_thread` unchanged for `/validate_user` because that route is sync and needs a blocking async bridge.
- Reasoning:
  - Preserves existing user-visible behavior and error semantics while removing wasted thread overhead.
  - Keeps event-loop ownership explicit and aligned with loop-scoped `AsyncLimiter` usage.
  - Minimizes blast radius before Batch 4 test expansion and later storage/refactor batches.
- Notes:
  - No functional changes were intentionally introduced in the fetch/process pipeline logic.
  - Next batch remains Batch 4 (coverage expansion) before deeper architectural moves.
