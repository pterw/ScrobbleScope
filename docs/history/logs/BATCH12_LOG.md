# Batch 12 Execution Log

Archived entries for Batch 12 work packages.

### 2026-02-23 - Post-Batch 12 audit improvements (side-task, 5 commits)

**Scope:** Comprehensive audit of Batch 12 implementation identified 5
priority actions: untested functions, missing branch coverage, and a
Spotify search progress feedback gap.

**Commits (incremental, each green):**

1. `2fbbe99` `test(spotify): add fetch_spotify_access_token coverage`
   -- 4 tests: cached reuse, expired refresh, non-200 returns None,
   missing credentials assertion. (228 -> 232 tests)
2. `ec5a00c` `test(utils): add format_seconds parametrized coverage`
   -- 13 parametrised cases mirroring `format_seconds_mobile`. (232 -> 245)
3. `6db66a4` `feat(orchestrator): add granular Spotify search progress feedback`
   -- Converted `_fetch_spotify_misses` search phase from `asyncio.gather`
   to `asyncio.as_completed` with per-album progress in 20-40% range.
   Fixed order-dependent mock side_effect. +1 test. (245 -> 246)
4. `497bf1e` `test(spotify): add search_for_spotify_album_id unhappy-path coverage`
   -- 3 tests: empty results, non-200/non-429, successful first-try. (246 -> 249)
5. `3de537f` `test(routes): add _get_filter_description branch coverage`
   -- 8 parametrised cases covering all 5 release_scope branches + 3
   fallback paths. (249 -> 257)

**Validation:** 257 tests passing, pre-commit clean.

### 2026-02-23 - style(css): semantic CSS variable enforcement (Batch 12 WP-1)

- Scope: `static/css/global.css`, `static/css/index.css`, `static/css/results.css`,
  `static/css/loading.css`, `static/css/error.css`, `static/css/unmatched.css`,
  `static/js/results.js`.
- Problem: Structural UI elements (backgrounds, borders, form inputs, error
  accent) duplicated hardcoded hex values across 6 CSS files and 1 JS file,
  violating DRY and breaking the centralized theme architecture.
- Fix: Added 5 semantic CSS variables (`--surface-color`, `--surface-elevated`,
  `--border-color`, `--input-bg`, `--error-accent`) to `:root`/`.dark-mode` in
  `global.css`. Replaced all structural hardcoded hex across 6 CSS files.
  Promoted orphaned `--error-accent` from `error.css` to `global.css`. Fixed
  `results.js` `html2canvas` `backgroundColor` to use `getComputedStyle` for
  `--bg-color` instead of hardcoded `#121212`/`#ffffff` ternary (light-mode
  JPEG export was `#ffffff` vs actual `--bg-color` of `#f8f9fa`).
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all hooks passed.

### 2026-02-23 - feat(templates,js): responsive table formatting and export parity (Batch 12 WP-2)

- Scope: `scrobblescope/utils.py`, `scrobblescope/orchestrator.py`,
  `templates/results.html`, `static/css/results.css`, `static/js/results.js`,
  `tests/test_utils.py`, `tests/services/test_orchestrator_service.py`.
- Problem: (1) Long time strings ('1 day, 12 hrs, 38 mins') caused table
  spillover on mobile. (2) CSV export concatenated both responsive spans
  (e.g. '2024-03-152024-03'). (3) html2canvas JPEG export did not force
  desktop layout on mobile viewports.
- Fix: (1) Added `format_seconds_mobile()` (max 2 units, abbreviated) with
  14 parametrized tests. `_build_results` emits `play_time_mobile`. Template
  uses dual d-none/d-md-inline spans. (2) CSV extraction reads `.d-md-inline`
  text when present, fixing existing release_date and new play_time bugs.
  (3) `onclone` callback explicitly shows desktop spans, hides mobile spans,
  and unhides rank columns in cloned DOM.
- Validation: `pytest -q`: **223 passed**. `pre-commit`: all hooks passed.

### 2026-02-23 - refactor(lastfm,orchestrator): backend SoC extraction (Batch 12 WP-3)

- Scope: `scrobblescope/lastfm.py`, `scrobblescope/domain.py`,
  `scrobblescope/orchestrator.py`, `tests/test_domain.py`,
  `tests/services/test_lastfm_logic.py`, `tests/services/test_lastfm_service.py`.
- Problem: `lastfm.py` housed business logic (`fetch_top_albums_async`: album
  aggregation, filtering, normalization) alongside raw HTTP client functions.
  It imported `domain.py` functions and was not a pure infrastructure client.
- Fix: (1) Inlined `_extract_registered_year` (vendor-specific JSON parsing)
  into `check_user_exists`. Removed from `domain.py`. (2) Moved
  `fetch_top_albums_async` (~66 lines) to `orchestrator.py`. (3) Updated
  `test_lastfm_logic.py` imports and mock paths.
- Post-state: `lastfm.py` has zero `domain` imports, zero `repositories`
  imports. Pure HTTP client. `orchestrator.py` grew to ~800 lines.
- Validation: `pytest -q`: **222 passed**. `pre-commit`: all hooks passed.

### 2026-02-23 - feat(lastfm,orchestrator): granular backend progress pipeline (Batch 12 WP-4)

- Scope: `scrobblescope/lastfm.py`, `scrobblescope/orchestrator.py`,
  `tests/services/test_lastfm_service.py`,
  `tests/services/test_orchestrator_service.py`.
- Problem: Progress polling jumped 5% -> 40% (entire Last.fm fetch) and
  40% -> 60% (entire Spotify batch) with no intermediate updates.
- Fix: (1) Added `progress_cb: Callable[[int, int], None] | None` parameter
  to `fetch_all_recent_tracks_async`. When provided, uses
  `asyncio.as_completed` for per-page callbacks; when None, preserves
  existing `asyncio.gather` path. (2) `_fetch_and_process` passes a
  `_lastfm_progress` closure mapping page completion into 5%-20% range with
  messages "Fetching Last.fm page N/T...". (3) Replaced `asyncio.gather`
  with `asyncio.as_completed` for Spotify batch detail fetch in
  `_fetch_spotify_misses`, incrementing within 40%-60% range with messages
  "Enriched N/T albums from Spotify...".
- Tests: 4 new `progress_cb` tests in `test_lastfm_service.py`, 1 wiring test
  for `_lastfm_progress` arithmetic, 1 Spotify batch progress test.
- Validation: `pytest -q`: **228 passed**. `pre-commit`: all hooks passed.
