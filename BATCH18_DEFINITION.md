# BATCH18: Scrobble Heatmap -- Iteration 1

**Status:** Pending
**Branch:** `feat/heatmap`
**Baseline:** 350 tests passing
**Design doc:** `C:\Users\peter\.claude\plans\dreamy-cooking-micali.md`

---

## Context

ScrobbleScope currently supports one feature: album filtering by year with
Spotify enrichment. The owner's roadmap calls for a second feature -- a
scrobble heatmap showing daily listening density over the last 365 days,
rendered as a GitHub/Last.fm-Labs-style calendar grid. This is the first
new feature added since the app's initial build.

The owner provided reference code from a prior Heroku implementation (Flask +
matplotlib/seaborn/pandas + Redis/RQ) and Last.fm Labs screenshots showing the
target visual style. The old implementation generated server-side PNG images --
the new design uses client-side SVG rendering with no new Python dependencies.

This is **iteration 1** -- get the heatmap working end-to-end with clean
separation from the start. The feature may span multiple batches; SoC/DRY
remediation passes (e.g., orchestrator monolith split) and polish (export,
date range) are explicitly deferred to follow-up batches. Code written in
this batch must still respect DRY, SoC, SRP, KISS, Clean Architecture, Boy
Scout Rule, Least Knowledge Principle, Fail Fast, and Composition over
Inheritance -- this is not throwaway code.

**Owner-approved design decisions:**
- Username-only input (always last 365 days from today -- no year picker)
- Pill tabs on index.html: "Album Filtering" (default) | "Heatmap"
- All states (form, loading, result) on index.html -- no page navigation
- GitHub/Last.fm-Labs-style grid: 7 rows x 52-53 columns, rounded cells, gaps
- rocket_r color palette (near-black -> deep purple -> red -> orange -> cream)
- Log-adjusted intensity: `log10(count+1) / log10(max+1)`
- Vanilla SVG rendering -- no JS libraries, no matplotlib
- Hover/tap tooltips: "Sunday 1 March 2026 -- **34 scrobbles**"
- Zero-scrobble days: visible muted cells (grid structure stays apparent)
- Color scale legend at card edge
- No heatmap-specific caching in iteration 1 (REQUEST_CACHE covers pages)
- Owner-provided animated SVG loading spinner (purple pinwheel)

**Out of scope:**
- Orchestrator monolith split (follow-up batch once both pipelines exist)
- Persistent heatmap cache (YAGNI -- rolling 365-day window is complex)
- Save/export heatmap image
- Custom date range or year picker
- Heatmap summary stats (total scrobbles, busiest day, streaks)
- Footer position fix (side-task)
- Cache + bounded semaphore load testing (per load-test-findings.md)

---

## 1. Scope and goals

- Add scrobble heatmap as a second feature on index.html alongside album filtering
- Implement backend task module (`heatmap.py`) that fetches Last.fm scrobbles
  and aggregates daily counts -- reusing existing fetch + job infrastructure
- Add two new route handlers for AJAX-driven heatmap flow
- Implement client-side SVG heatmap rendering with rocket_r palette
- Support desktop and mobile (responsive), light and dark mode
- Comprehensive test suite following the testing pyramid
- All functions documented with docstrings for cross-agent readability

---

## 2. Work Packages

### WP-1: Backend -- heatmap task module + error code

**Goal:** Create `scrobblescope/heatmap.py` with the background task that
fetches Last.fm scrobbles for the last 365 days and aggregates them into
daily counts. Add error code for zero-scrobble edge case.

**Files:**
- `scrobblescope/heatmap.py` (NEW)
- `scrobblescope/errors.py` (MODIFY -- add `no_scrobbles_in_range`)
- `tests/test_heatmap.py` (NEW)

**Implementation detail:**

`heatmap_task(job_id, username)` -- thread entry point:
- Windows ProactorEventLoop guard (same as orchestrator.py `background_task()`)
- `release_job_slot()` in `finally` block
- Calls `_fetch_and_process_heatmap(job_id, username)` via event loop

`_fetch_and_process_heatmap(job_id, username)` -- async orchestrator:
1. Phase 0%: `cleanup_expired_cache()`, set initial progress with
   `reset_stats=True`
2. Phase 0-80%: call `lastfm.fetch_all_recent_tracks_async(username,
   from_ts, to_ts)` where `from_ts = now - 365 days`, `to_ts = now`.
   Progress callback maps page fetching to 0-80% range. Reports
   `pages_fetched`, `total_pages` via `set_job_stat()`.
3. Phase 80-90%: call `_aggregate_daily_counts(pages, from_date, to_date)`
   to build `{date_str: count}` dict.
4. Phase 90-100%: store result via `set_job_results()`. Result dict
   includes `username`, `from_date`, `to_date`, `max_count`, `daily_counts`.
5. Error path: if 0 total scrobbles, `set_job_error(job_id,
   "no_scrobbles_in_range")`.

`_aggregate_daily_counts(pages, from_date, to_date)` -- pure function:
- Takes raw Last.fm page data, returns `{date_str: count}` with all dates
  in the range filled (0 for missing days).
- Parses each track's `date["#text"]` field (`"%d %b %Y, %H:%M"` format).
- Skips "now playing" tracks (no `date` field -- they have `@attr.nowplaying`).
- Uses `collections.Counter` on date strings.
- Separated from the async orchestrator for testability.

**Reused functions (do not duplicate):**
- `lastfm.fetch_all_recent_tracks_async()` -- page fetching + rate limiting
- `utils.cleanup_expired_cache()` -- cache hygiene
- `repositories.create_job()`, `set_job_progress()`, `set_job_stat()`,
  `set_job_results()`, `set_job_error()` -- job state management
- `worker.release_job_slot()` -- semaphore release

**Cache note:** the heatmap task uses different `from`/`to` timestamps than
album search, producing different REQUEST_CACHE keys. No interference with
existing album cache entries.

**Tests (unit -- base of pyramid):**
- Mock Last.fm page data -> verify `_aggregate_daily_counts()` output
- Date parsing edge cases: midnight boundary, varied date formats
- Leap year: 366 days correctly generated in output dict
- Zero-scrobble range: error path triggered via `set_job_error()`
- "Now playing" tracks (no date field): skipped gracefully
- Progress callback: correct percentages reported at each phase
- Large volume: 50,000+ scrobbles aggregated correctly

**Acceptance criteria:**
- `pytest -q` passes with new tests
- `_aggregate_daily_counts` produces correct dict from mock data
- Error path fires on zero scrobbles
- All functions have comprehensive docstrings
- `pre-commit run --all-files` passes

**Net tests:** +N (estimated 8-12)
**Commit:** `feat(heatmap): add heatmap task module and aggregation logic`

---

### WP-2: Backend -- heatmap routes

**Goal:** Add route handlers for the AJAX-driven heatmap flow. Reuse
existing validation, job management, and concurrency control patterns.

**Files:**
- `scrobblescope/routes.py` (MODIFY)
- `tests/test_routes.py` (MODIFY -- add route tests)

**Implementation detail:**

`POST /heatmap_loading`:
- Extract `username` from form data
- Fail fast: validate presence, then call `_check_user_exists(username)`
- Call `cleanup_expired_jobs()`
- Call `acquire_job_slot()` -- if False, return JSON error with 429 status
- `create_job({"username": username, "mode": "heatmap"})`
- `start_job_thread(heatmap_task, args=(job_id, username))`
- Return JSON `{"job_id": "..."}` with 202 status
- On thread start failure: `delete_job(job_id)`, return JSON error
- CSRF enforced (same hidden field pattern as album form)

`GET /heatmap_data`:
- Extract `job_id` from query params. Fail fast if missing (400).
- `get_job_context(job_id)` -- return 404 if not found.
- If `progress["error"]` is True, return error JSON with appropriate status.
- If `results` exist, return daily_counts payload JSON (200).
- If not ready, return `{"ready": false}` (202).

`/progress` endpoint: NO CHANGES -- already returns the correct structure
for any job type.

**Reused functions (do not duplicate):**
- `_check_user_exists()` -- username validation
- `acquire_job_slot()` / `start_job_thread()` -- concurrency control
- `create_job()` / `get_job_context()` / `delete_job()` -- job lifecycle
- `cleanup_expired_jobs()` -- stale job cleanup

**Tests (integration -- middle of pyramid):**
- `/heatmap_loading` POST: valid username -> 202 + job_id
- `/heatmap_loading` POST: nonexistent username -> error JSON
- `/heatmap_loading` POST: no job slot available -> 429
- `/heatmap_loading` POST: missing CSRF token -> 400
- `/heatmap_loading` POST: missing username -> 400
- `/heatmap_data` GET: completed job -> daily_counts JSON
- `/heatmap_data` GET: missing/expired job -> 404
- `/heatmap_data` GET: job in progress -> 202
- Concurrent heatmap + album requests use separate job slots correctly

**Acceptance criteria:**
- All route tests pass
- CSRF enforced on POST
- Error paths return correct HTTP status codes and JSON bodies
- Docstrings on all handler functions
- `pre-commit run --all-files` passes

**Net tests:** +N (estimated 8-10)
**Commit:** `feat(heatmap): add heatmap route handlers`

---

### WP-3: Frontend -- index.html pill tabs + heatmap form + CSS

**Goal:** Add the pill tab UI, heatmap form card, and all container markup
to index.html. Create heatmap CSS. Place loading spinner asset.

**Files:**
- `templates/index.html` (MODIFY)
- `static/css/heatmap.css` (NEW)
- `static/img/loading-spinner.svg` (NEW -- owner-provided or placeholder)

**Implementation detail:**

Pill tab markup above the form card (below info button area):
- Two pills: "Album Filtering" (default active) | "Heatmap"
- Styled with existing decade-pill pattern (rounded, centered, equidistant)
- `data-mode="album"` / `data-mode="heatmap"` attributes for JS targeting

Heatmap form section (hidden by default, `d-none`):
- Same `.card.shadow` pattern as album form card
- No heading text (clean minimal card per owner request)
- Username field: `form-control` input with validation checkmark pattern
- Submit button: same styling as album "Search Albums" button
- Hidden CSRF token field (same pattern as album form)

Loading spinner container (hidden):
- Centered container for the animated SVG pinwheel
- Progress text container beneath: "Fetching page X of Y..."

Heatmap result container (hidden):
- `.card.shadow` for the SVG grid
- Color scale legend slot

CSS (`heatmap.css`):
- Pill tab styles (reusing decade-pill visual language)
- Heatmap form card styles
- Loading/result container styles
- Fade transition classes (`.heatmap-fade-in`, `.heatmap-fade-out`)
- Responsive: all containers use same Bootstrap grid as album card
- Dark mode support via existing `[data-theme="dark"]` selectors

**Note:** Pill switching JS is in WP-4. This WP is markup + CSS only.
Verify by toggling `d-none` classes in browser dev tools.

**Acceptance criteria:**
- Pills render correctly on desktop and mobile
- Album form completely unchanged and functional
- All hidden containers present in DOM
- CSS transitions defined and correct
- Mobile layout matches album card behavior (Firefox Responsive Design Mode)
- Loading spinner SVG in place (owner asset or placeholder)
- `pre-commit run --all-files` passes

**Net tests:** +0 (HTML/CSS only -- owner tests visually)
**Commit:** `feat(heatmap): add pill tabs, heatmap form, and CSS to index.html`

---

### WP-4: Frontend -- heatmap.js (full JS + SVG rendering)

**Goal:** Implement all client-side heatmap logic: pill switching, AJAX form
submission, polling, SVG grid rendering with rocket_r palette, tooltips,
fade transitions, and dark mode support.

**Files:**
- `static/js/heatmap.js` (NEW)
- `static/css/heatmap.css` (MODIFY -- add SVG grid + tooltip styles)
- `templates/index.html` (MODIFY -- add script tag for heatmap.js)

**Implementation detail:**

Pill switching:
- Click handler toggles between album form and heatmap form sections
- Fade-out current form, fade-in new form
- Update active pill styling

Username validation:
- Reuse existing validation checkmark pattern from album form
- Validate on input blur or form submit

Form submission:
- AJAX POST to `/heatmap_loading` with `username` + `csrf_token`
- Fail fast on client-side validation (empty username)
- On success (202 + job_id): show loading spinner + progress text
- On error: show error message in result container

Polling:
- Fetch `/progress?job_id=...` every 1 second
- Update progress text: "Fetching page X of Y..."
- On progress=100 + no error: fetch `/heatmap_data?job_id=...`
- On error: show user-friendly error message

SVG rendering (from `/heatmap_data` JSON):
- Calculate grid layout: 7 rows (Mon-Sun) x 52-53 columns (weeks)
- Start from oldest date, align days to correct day-of-week row
- Create `<svg>` with `viewBox` for responsive scaling, `width="100%"`
- Each day: rounded `<rect>` with gap between cells
- Color mapping: `log10(count+1) / log10(max+1)` -> rocket_r color stops
  (6-8 hardcoded hex values sampled from seaborn rocket_r colormap)
- Zero-scrobble cells: distinct muted fill, subtle border -- visible grid
- Color scale legend at bottom or side of grid
- Month boundaries: subtle column gaps where month changes

Tooltips:
- Positioned `<div>` on mouseover/touchstart
- Content: "Sunday 1 March 2026 -- **34 scrobbles**" (or "No scrobbles")
- Dismiss on mouseout / touch-elsewhere
- Styled with shadow, correct dark/light mode colors

Fade transitions:
- Loading spinner fades in on submit
- Spinner + progress fade out when data arrives
- Heatmap card fades in after spinner fades out

Dark mode:
- Respect existing `[data-theme="dark"]` toggle
- Adjust tooltip background, text, and border for dark/light
- rocket_r palette works on both backgrounds (near-black cells blend into
  dark mode naturally)

CSS additions (`heatmap.css`):
- SVG rect styles (rounded corners via `rx`/`ry`)
- Tooltip positioning and appearance
- rocket_r color variables as CSS custom properties
- Dark mode overrides

**Acceptance criteria:**
- Full end-to-end flow: username -> submit -> loading -> heatmap renders
- Tooltips work on hover (desktop) and tap (mobile)
- Dark mode toggle works with heatmap visible
- SVG scales responsively (fill card width on any screen)
- Aesthetically pleasing grid with rounded cells and gaps
- Owner tests in Firefox + Responsive Design Mode
- `pre-commit run --all-files` passes

**Net tests:** +0 (JS -- owner tests visually; unit testing JS is out of
scope for iteration 1)
**Commit:** `feat(heatmap): add heatmap.js with SVG rendering and polling`

---

### WP-5: Expanded backend tests + edge cases

**Goal:** Strengthen the test suite with additional edge cases and
integration scenarios. Verify no regressions.

**Files:**
- `tests/test_heatmap.py` (MODIFY -- expand)
- `tests/test_routes.py` (MODIFY -- expand if needed)

**Scope:**
- Aggregation with tracks spanning midnight boundary
- Leap year: 366-day range produces 366 entries
- User with exactly 1 scrobble in 365 days
- "Now playing" tracks: verified skipped (no crash, no phantom counts)
- Large volume: 50,000+ scrobbles aggregated correctly and quickly
- Route: concurrent heatmap + album requests using separate job slots
- Route: job expiry during heatmap polling
- Route: malformed/empty username variants
- Verify all 350 existing tests still pass (no regressions)
- Every new test fails if the function under test is deleted

**Acceptance criteria:**
- All tests pass (350 existing + new heatmap/route tests)
- No test duplicates existing coverage
- No vacuous tests (per AGENTS.md anti-pattern registry)
- `pre-commit run --all-files` passes

**Net tests:** +N (estimated 6-10 additional)
**Commit:** `test(heatmap): expand edge case and integration tests`

---

## 3. Testing strategy (pyramid)

**Unit tests (base -- most tests):**
- `tests/test_heatmap.py`: aggregation logic, date parsing, edge cases,
  progress reporting, error paths. All with mock data.

**Integration tests (middle):**
- `tests/test_routes.py`: heatmap route handlers with Flask test client.
  CSRF, error codes, job lifecycle, concurrent requests.

**E2E tests (top -- owner-driven):**
- Owner tests locally in Firefox + Responsive Design Mode between WPs.
- Full flow: pill switch -> form -> loading -> heatmap display
- Tooltips, dark mode, mobile responsiveness
- Error cases (bad username, no scrobbles)
- Browser MCP can verify deployed behavior post-deploy

---

## 4. Software principles (enforced)

| Principle | Application |
|-----------|-------------|
| DRY | Call existing functions in lastfm.py, repositories.py, worker.py. No fetch/job duplication. |
| SoC / SRP | heatmap.py = orchestration. routes.py = HTTP. heatmap.js = rendering. One reason to change each. |
| KISS | Counter aggregation, hardcoded colors, vanilla SVG. No frameworks. |
| DSP (Dependency Inversion) | heatmap.py depends on function signatures, not concrete internals. |
| Composition over Inheritance | No class hierarchies. Compose via function calls. |
| Least Knowledge | heatmap.py never touches JOBS dict directly -- only via repositories helpers. |
| Fail Fast | Validate username before job creation. Check empty scrobbles early. Clear errors immediately. |
| Boy Scout Rule | Minor cleanups in touched files, documented as deviations. |
| Clean Architecture | Data flows one direction: HTTP -> route -> task -> repositories -> HTTP. No cycles. |

---

## 5. Open items requiring owner input

1. **Loading spinner SVG asset**: owner will provide the animated purple
   pinwheel SVG file. Can stub with placeholder during dev. Needed before
   WP-3 is final.

2. **rocket_r color stops**: agent will extract hex values from seaborn's
   rocket_r colormap and propose for owner approval before hardcoding.

---

## 6. Verification gates (per WP)

```bash
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Owner tests locally in Firefox (+ Responsive Design Mode) before
approving the next WP.
