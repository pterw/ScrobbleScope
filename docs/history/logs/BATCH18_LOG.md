# Batch 18 Execution Log

Archived entries for Batch 18 work packages.

### 2026-05-17 - Batch 18 close-out (Batch 18 WP-5)

- Added 4 new tests across 3 files; all existing 381 tests still pass (385 total).
- `tests/test_heatmap.py` (+2 tests, 19 total):
  - `test_midnight_boundary_attribution`: tracks at 23:59:59 on day D and
    00:00:01 on day D+1 are attributed to their correct calendar days.
    Adversarial for off-by-one in the uts->date conversion.
  - `test_partial_data_with_zero_scrobbles_fires_error`: partial fetch with
    no in-range tracks triggers both the partial-data warning stat and the
    no_scrobbles_in_range error (tests the combined code path).
- `tests/test_repositories.py` (+1 test, 19 total):
  - `test_get_job_context_dict_results_are_shallow_copied`: mutating the dict
    returned by get_job_context does not corrupt the live JOBS entry. Adversarial
    for the `elif isinstance(results, dict): dict(results)` branch added in WP-1.
- `tests/test_routes.py` (+1 test, 65 total):
  - `test_heatmap_loading_whitespace_username`: whitespace-only username is
    stripped and treated as missing (400). Adversarial for absent strip() call.
- **No vacuous tests added.** Each new test fails if the function under test
  or the specific branch being exercised is removed.
- File size note: test_routes.py (65 tests) is the largest in the suite; a
  future split into test_album_routes.py / test_heatmap_routes.py is a
  candidate for a follow-up batch.
- **385 tests passing**, all 10 pre-commit hooks green.
- Phase 1 complete. Next: owner reviews implementation and scopes WP-6+.

### 2026-05-05 - Batch 18 doc update: Phase 2 scoping + perf findings (Batch 18 WP-0)

- BATCH18_DEFINITION.md: added Phase 2 section (owner-review-driven WP-6+ cycle).
- PLAYBOOK.md Section 3: updated WP status (WP-1 through WP-4 done, WP-5 pending),
  added Phase 2 description, documented perf bottleneck (sequential Last.fm fetches,
  ~11-13s for 103 pages) and known UI issues (pill width mismatch).
- SESSION_CONTEXT.md: bumped date to 2026-03-09, updated Batch 18 status row,
  added heatmap perf bottleneck note.
- AGENT_NOTES.md: added Phase 2 two-phase structure description, detailed perf
  bottleneck options (parallel fetches, larger page size, caching, progressive
  rendering), listed known UI issues flagged by owner.

### 2026-03-07 - Batch 18 WP-4: frontend heatmap.js with SVG rendering and polling (Batch 18 WP-4)

- Created `static/js/heatmap.js` (~400 lines, IIFE, strict mode):
  - Pill switching: click/keyboard handlers toggle `.d-none` on album/heatmap
    form sections, update `.active` class on pills.
  - Username validation: blur handler on `#heatmap-username` calls
    `/validate_user` endpoint, shows `is-valid`/`is-invalid` feedback.
  - AJAX form submission: reads CSRF token from `<meta>`, POST to
    `/heatmap_loading` with `URLSearchParams`, handles 202 + error states.
  - Polling: 1-second interval on `/progress?job_id=...`, updates
    `#heatmap-progress-text` with server message. On progress >= 100,
    fetches `/heatmap_data?job_id=...`.
  - SVG grid rendering: 7 rows (Mon-Sun) x 52-53 columns, rounded rects
    with gap, rocket_r palette (7-stop interpolation), log10 color mapping.
    Month labels above first week of each month, day labels (Mon/Wed/Fri).
  - Tooltips: positioned `<div>` on mouseenter/touchstart, "Sunday 1 March
    2026 -- 34 scrobbles" format, viewport-aware positioning, dismiss on
    mouseleave/touchend/scroll.
  - Dark mode observer: MutationObserver on `body.class` updates
    zero-scrobble cell fills (#e0e0e0 light / #2a2a2a dark).
  - Legend: rocket_r CSS gradient on `.heatmap-legend-bar`.
  - State transitions: form -> loading (fade-in), loading -> result
    (fade-in), result -> form (search-again button).
- Added `<script>` tag for heatmap.js in `index.html` `{% block scripts %}`.
- Added `.heatmap-day-label` / `.heatmap-month-label` CSS classes in
  `heatmap.css` for SVG text label font/opacity.
- No `innerHTML` used with user data (`textContent` exclusively, F-B18-9).
- No test changes (+0 tests, JS -- owner tests visually).
- **381 tests passing**, all 10 pre-commit hooks green.
- Next: WP-5 -- expanded backend tests + edge cases.

### 2026-03-07 - Batch 18 WP-3: frontend pill tabs, heatmap form, CSS (Batch 18 WP-3)

- Added CSRF meta tag to `base.html` `<head>` for AJAX POST token access.
- Created `static/css/heatmap.css`: pill tab bar (flex, centered, decade-pill
  style), heatmap form card, loading container with spinner, result container
  with grid/legend/header, tooltip styling (positioned div with dark/light
  variants), fade transitions, responsive mobile rules, SVG grid cell comments.
- Copied pinwheel SVG to `templates/inline/scrobblescope_pinwheel.svg` for
  Jinja2 inline include (animated 4-blade spinner with rotation + expansion).
- Updated `index.html`: pill tabs ("Album Filtering" | "Heatmap") below logo,
  album form wrapped in `#album-form-section`, new `#heatmap-form-section`
  (hidden by default, username-only form), `#heatmap-loading` container
  (pinwheel + progress text + error display), `#heatmap-result` container
  (grid + legend + search-again button). Welcome modal updated with heatmap
  feature description and pill tab tip. Linked `heatmap.css` in stylesheets.
- All containers have correct IDs for WP-4 JS targeting. Pill switching
  JS deferred to WP-4 (WP-3 is markup + CSS only per definition).
- No test changes (HTML/CSS only -- +0 tests, owner tests visually).
- **381 tests passing**, all pre-commit hooks green.
- Next: WP-4 -- frontend heatmap.js (SVG rendering, polling, tooltips).

### 2026-03-07 - Batch 18 WP-2: heatmap route handlers (Batch 18 WP-2)

- Added `POST /heatmap_loading` and `GET /heatmap_data` to `routes.py`.
  Both are JSON-only (no render_template). `/heatmap_loading` validates
  username, checks user existence, acquires slot, starts `heatmap_task`
  thread, returns 202 with `job_id`. Supports both form data and JSON
  body for AJAX. `/heatmap_data` returns completed results (200),
  error details (200), processing-in-progress (202), or missing/expired
  (400/404). Error check before `results is not None` guard ensures
  `set_job_error` result=[] edge case returns error, not ready.
- Added import `from scrobblescope.heatmap import heatmap_task` to routes.py.
- 14 new route tests: valid user (202), missing username (400), nonexistent
  user (404), no slot (429), thread failure (500 + cleanup), user check
  unavailable (503), JSON body path, completed results, completed error,
  missing job_id, expired job, still processing, error-with-empty-results
  edge case, CSRF rejection.
- **381 tests passing**, all pre-commit hooks green.
- Next: WP-3 -- frontend pill tabs + heatmap form + CSS.

### 2026-03-07 - Batch 18 WP-1: heatmap task module + error code (Batch 18 WP-1)

- Created `scrobblescope/heatmap.py`: `heatmap_task` (thread entry),
  `_fetch_and_process_heatmap` (async orchestrator), `_aggregate_daily_counts`
  (pure function). Reuses `lastfm.fetch_all_recent_tracks_async`, job state
  machine, and worker slot system. ProactorEventLoop guard on Windows.
- Added `no_scrobbles_in_range` error code to `errors.py`.
- Boy Scout: `repositories.py` -- `get_job_context` now shallow-copies dict
  results (`elif isinstance(results, dict)`); `set_job_results` docstring
  updated to reflect list-or-dict payload.
- Created `tests/test_heatmap.py` with 17 tests covering aggregation
  (basic, now-playing skip, 365/366-day fill, boundary, out-of-range,
  empty, multi-page), async orchestrator (upstream error, partial data,
  zero scrobbles, happy path, progress), task lifecycle (release on
  success/exception), and error code registry.
- Also added XSS acceptance criterion to WP-4 in BATCH18_DEFINITION.md.
- **367 tests passing**, all pre-commit hooks green.
- Next: WP-2 -- backend heatmap routes.

### 2026-03-06 - Batch 18 WP-0: definition committed (Batch 18 WP-0)

- **Batch 18 started.** Branch `feat/heatmap` (from `main` after Batch 17 merge).
- Definition committed: `BATCH18_DEFINITION.md` (5 WPs: heatmap task module,
  heatmap routes, frontend pill tabs + form, heatmap.js SVG rendering, expanded tests).
- Owner-approved design: GitHub/Last.fm-Labs-style calendar grid, rocket_r palette,
  vanilla SVG, no new Python dependencies, no heatmap caching in iteration 1.
- AGENT_NOTES.md updated with heatmap context, software principles, testing pyramid.
- Baseline: **350 tests passing**, branch clean, all hooks green.
- Next: WP-1 -- backend heatmap task module + error code.
