# BATCH18: Scrobble Heatmap -- Iteration 1

**Status:** Pending (audited 2026-03-07)
**Branch:** `feat/heatmap`
**Baseline:** 350 tests passing (verified 2026-03-07)

---

## Audit corrections (2026-03-07)

Corrections applied after full source-code audit of all `scrobblescope/` modules,
`app.py`, all templates (`index.html`, `base.html`, `loading.html`), all static
assets (`css/`, `js/`), and the owner-provided pinwheel SVG.

1. **HIGH -- date parsing must use `uts` (Unix timestamp).** The original plan
   specified `date["#text"]` with strptime. The existing `orchestrator.py`
   (line ~111) uses `t.get("date", {}).get("uts")` exclusively. strptime is
   locale-dependent and fragile. Corrected: heatmap uses `uts` throughout.
2. **HIGH -- upstream Last.fm error path missing.** `fetch_all_recent_tracks_async`
   returns `(pages, metadata)` where `metadata["status"]` can be `"error"`. The
   original plan had no guard for this. Corrected: add explicit check after fetch.
3. **HIGH -- all states on index.html, no page navigation.** The original plan
   implied correct behavior but was ambiguous in places. The heatmap form,
   loading state (pinwheel spinner + text), result state (SVG grid), and error
   state are ALL rendered on index.html via JS state transitions. No separate
   loading.html or results.html. Routes return JSON only.
4. **MEDIUM -- pinwheel SVG replaces progress bar.** The heatmap loading state
   uses the owner-provided animated pinwheel SVG (`docs/images/
   scrobblescope_pinwheel_expanded.svg`) with progress text below it. There is
   NO Bootstrap progress bar for the heatmap. The album search retains its
   existing progress bar on loading.html.
5. **MEDIUM -- `set_job_error` sets `results=[]` (falsy).** `repositories.py`
   `set_job_error()` internally calls `set_job_results(job_id, [])`. So
   `if results:` would be wrong. Route must check `results is not None`.
6. **MEDIUM -- `get_job_context` only copies lists, not dicts.** Heatmap stores
   a dict as results. Boy Scout fix: add `elif isinstance(results, dict)` copy
   in `repositories.py`.
7. **MEDIUM -- partial data path unaddressed.** `fetch_all_recent_tracks_async`
   can return `metadata["status"] == "partial"` with `pages_dropped`. Corrected:
   store warning stat like orchestrator does, continue with available data.
8. **LOW -- SVG asset path.** Owner-provided file is
   `docs/images/scrobblescope_pinwheel_expanded.svg`. It will be included
   inline in index.html via Jinja2 include (same pattern as the main logo
   `{% include 'inline/...' %}`), placed in `templates/inline/` for serving.
9. **LOW -- `set_job_results` docstring says "list".** Boy Scout fix: update
   docstring to "Store the final results payload (list or dict) on a job."
10. **LOW -- CSRF for AJAX POST.** index.html currently has no `<meta
    name="csrf-token">` tag. The heatmap AJAX POST needs a CSRF token. Will
    add a meta tag to `base.html` `head_extra` so all pages have it.
    heatmap.js reads it from the meta tag (same pattern as loading.js).
11. **LOW -- 365-day window exact definition.** `from_date = today - 364 days`
    (inclusive) through `to_date = today` (inclusive) = 365 calendar days.
    On leap-year boundaries this can be 366 keys if the range spans Feb 29.
12. **LOW -- dark mode uses `.dark-mode` class.** The original plan referenced
    `[data-theme="dark"]` selectors. The actual codebase uses `body.dark-mode`
    class toggled by `theme.js`. Corrected.

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
- All states (form, loading, result, error) on index.html -- no page navigation
- GitHub/Last.fm-Labs-style grid: 7 rows x 52-53 columns, rounded cells, gaps
- rocket_r color palette (near-black -> deep purple -> red -> orange -> cream)
- Log-adjusted intensity: `log10(count+1) / log10(max+1)`
- Vanilla SVG rendering -- no JS libraries, no matplotlib
- Hover/tap tooltips: "Sunday 1 March 2026 -- **34 scrobbles**"
- Zero-scrobble days: visible muted cells (grid structure stays apparent)
- Color scale legend at card edge
- No heatmap-specific caching in iteration 1 (REQUEST_CACHE covers pages)
- Owner-provided animated SVG loading spinner (purple pinwheel) -- NO progress bar
- Loading state: pinwheel + progress text (e.g. "Fetching page 3 of 45...")

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
- Add two new route handlers for AJAX-driven heatmap flow (JSON responses only)
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
- `scrobblescope/repositories.py` (MODIFY -- Boy Scout: dict copy in
  `get_job_context`, docstring fix in `set_job_results`)
- `tests/test_heatmap.py` (NEW)

**Implementation detail:**

`heatmap_task(job_id, username)` -- thread entry point:
- Windows ProactorEventLoop guard (same pattern as `orchestrator.py`
  `background_task()` -- `sys.platform == "win32"` check)
- `release_job_slot()` in `finally` block
- Calls `_fetch_and_process_heatmap(job_id, username)` via `loop.run_until_complete`
- Catches unhandled exceptions and logs them (same pattern as `background_task`)

`_fetch_and_process_heatmap(job_id, username)` -- async orchestrator:
1. Phase 0%: `cleanup_expired_cache()`, `cleanup_expired_jobs()`,
   set initial progress with `reset_stats=True`
2. Phase 5-80%: call `lastfm.fetch_all_recent_tracks_async(username,
   from_ts, to_ts, progress_cb=_heatmap_progress)` where date range is
   `from_date = today - 364 days`, `to_date = today` (365 calendar days).
   Progress callback maps page fetching to 5-80% range.
   ```python
   now = datetime.now()
   to_date = now.date()
   from_date = to_date - timedelta(days=364)
   from_ts = int(datetime.combine(from_date, time.min).timestamp())
   to_ts = int(now.timestamp())
   ```
3. **Upstream error guard** (after fetch returns):
   ```python
   if fetch_metadata.get("status") == "error":
       set_job_error(job_id,
           fetch_metadata.get("reason", "lastfm_unavailable"),
           username=username)
       return
   ```
4. **Partial data handling** (non-fatal):
   ```python
   if fetch_metadata.get("status") == "partial":
       dropped = fetch_metadata["pages_dropped"]
       expected = fetch_metadata["pages_expected"]
       pct = round((dropped / expected) * 100)
       set_job_stat(job_id, "partial_data_warning",
           f"Note: {dropped} of {expected} Last.fm pages failed "
           f"({pct}% data loss). Heatmap may be incomplete.")
   ```
5. Phase 80-90%: call `_aggregate_daily_counts(pages, from_date, to_date)`
   to build `{"YYYY-MM-DD": count}` dict.
6. Phase 90%: if 0 total scrobbles across entire range,
   `set_job_error(job_id, "no_scrobbles_in_range")` and return.
7. Phase 100%: store result dict via `set_job_results()`:
   ```python
   {
       "username": username,
       "from_date": str(from_date),   # "2025-03-08"
       "to_date": str(to_date),       # "2026-03-07"
       "total_scrobbles": total,
       "max_count": max_count,
       "daily_counts": {"2025-03-08": 42, "2025-03-09": 0, ...}
   }
   ```

`_aggregate_daily_counts(pages, from_date, to_date)` -- pure function:
- Takes raw Last.fm page data + date range boundaries.
- Returns `{"YYYY-MM-DD": count}` dict with ALL dates in range filled
  (0 for missing days).
- **Uses `uts` field** (NOT `date["#text"]`):
  ```python
  for page in pages:
      for t in page.get("recenttracks", {}).get("track", []):
          uts = t.get("date", {}).get("uts")
          if not uts:  # skip "now playing" tracks
              continue
          ts = int(uts)
          day = datetime.fromtimestamp(ts).date()
          if from_date <= day <= to_date:
              counts[day.isoformat()] += 1
  ```
- Fills all dates in range with 0 where missing:
  ```python
  current = from_date
  while current <= to_date:
      daily_counts.setdefault(current.isoformat(), 0)
      current += timedelta(days=1)
  ```
- Uses `collections.Counter` on date strings for counting, then
  merges into the full-range dict.
- Separated from the async orchestrator for testability.

**Error code addition** (`errors.py`):
```python
"no_scrobbles_in_range": {
    "source": "lastfm",
    "retryable": False,
    "message": "No scrobbles found in the last 365 days for '{username}'.",
},
```

**Boy Scout fixes** (`repositories.py`):
- `get_job_context`: add `elif isinstance(results, dict): results = dict(results)`
  to shallow-copy dict results (heatmap stores a dict, not a list).
- `set_job_results`: update docstring from "Store the final album results list"
  to "Store the final results payload (list or dict) on a job."

**Reused functions (do not duplicate):**
- `lastfm.fetch_all_recent_tracks_async()` -- page fetching + rate limiting
- `utils.cleanup_expired_cache()` -- cache hygiene
- `repositories.create_job()`, `set_job_progress()`, `set_job_stat()`,
  `set_job_results()`, `set_job_error()` -- job state management
- `repositories.cleanup_expired_jobs()` -- stale job cleanup
- `worker.release_job_slot()` -- semaphore release

**Not needed by heatmap.py** (do not import):
- `spotify.py` -- heatmap has no Spotify enrichment
- `cache.py` -- no DB cache for heatmap in iteration 1
- `domain.py` -- no normalization needed for daily counts

**Cache note:** the heatmap task uses different `from`/`to` timestamps than
album search, producing different REQUEST_CACHE keys. No interference with
existing album cache entries.

**Tests (unit -- base of pyramid):**
- `_aggregate_daily_counts` with mock page data -> verify correct day counts
- `_aggregate_daily_counts` with "now playing" track (no `uts` field) -> skipped
- `_aggregate_daily_counts` fills 365 keys (or 366 if leap year in range)
- `_aggregate_daily_counts` boundary: track at exactly `from_ts` and `to_ts`
- `_aggregate_daily_counts` with empty pages -> all zeros
- `_fetch_and_process_heatmap` upstream error -> `set_job_error` called
- `_fetch_and_process_heatmap` partial data -> warning stat set, continues
- `_fetch_and_process_heatmap` zero scrobbles -> `no_scrobbles_in_range`
- `_fetch_and_process_heatmap` happy path -> correct result dict stored
- `_fetch_and_process_heatmap` progress callback -> correct percentages
- `heatmap_task` -> release_job_slot called in finally (even on exception)
- `no_scrobbles_in_range` error code exists and has correct fields

**Acceptance criteria:**
- `pytest -q` passes with new tests
- `_aggregate_daily_counts` produces correct dict from mock data
- Error path fires on zero scrobbles and on upstream Last.fm error
- Partial data path stores warning and continues
- Boy Scout fixes applied (dict copy + docstring)
- All functions have comprehensive docstrings
- `pre-commit run --all-files` passes

**SESSION_CONTEXT updates:**
- Section 3: add `heatmap.py` to project structure
- Section 4: add `heatmap.py <- config, lastfm, repositories, utils, worker`

**Net tests:** +N (estimated 10-14)
**Commit:** `feat(heatmap): add heatmap task module and aggregation logic`

---

### WP-2: Backend -- heatmap routes

**Goal:** Add route handlers for the AJAX-driven heatmap flow. Reuse
existing validation, job management, and concurrency control patterns.
All responses are JSON (no render_template for heatmap routes).

**Files:**
- `scrobblescope/routes.py` (MODIFY -- add import for `heatmap_task`,
  add two new route functions)
- `tests/test_routes.py` (MODIFY -- add route tests)

**Import addition** (routes.py top):
```python
from scrobblescope.heatmap import heatmap_task
```
SESSION_CONTEXT Section 4 dependency update: `routes.py <- ..., heatmap`

**Implementation detail:**

`POST /heatmap_loading`:
```python
@bp.route("/heatmap_loading", methods=["POST"])
def heatmap_loading():
```
- Extract `username` from form data (or JSON body -- support both for AJAX)
- Fail fast: if not username, return `{"error": True, "message": "..."}`, 400
- Call `_check_user_exists(username)`:
  - If `not result["exists"]`: return `{"error": True, "error_code":
    "user_not_found", "message": "User '...' was not found on Last.fm.",
    "retryable": False}`, 404
  - If exception: return `{"error": True, "message": "...", "retryable":
    True}`, 503
- Call `cleanup_expired_jobs()`
- Call `acquire_job_slot()` -- if False:
  return `{"error": True, "message": "Too many requests...",
  "retryable": True}`, 429
- `job_id = create_job({"username": username, "mode": "heatmap"})`
- `start_job_thread(heatmap_task, args=(job_id, username))`
  - On exception: `delete_job(job_id)`, return `{"error": True,
    "message": "Failed to start processing.", "retryable": True}`, 500
- Return `jsonify({"job_id": job_id})`, 202
- CSRF enforced via Flask-WTF (same as all POST routes). AJAX sends
  token via `X-CSRFToken` header read from `<meta name="csrf-token">`.

`GET /heatmap_data`:
```python
@bp.route("/heatmap_data")
def heatmap_data():
```
- `job_id = request.args.get("job_id")`
- If not job_id: return `{"error": True, "message": "Missing job
  identifier."}`, 400
- `ctx = get_job_context(job_id)` -- if None: return 404
- If `ctx["progress"]["error"]`:
  ```python
  return jsonify({
      "error": True,
      "message": ctx["progress"].get("message"),
      "error_code": ctx["progress"].get("error_code"),
      "retryable": ctx["progress"].get("retryable", False),
  }), 200  # 200 because the job completed (with error)
  ```
- If `ctx["results"] is not None`:  **(NOTE: `is not None`, not `if results`)**
  ```python
  return jsonify({"ready": True, **ctx["results"]}), 200
  ```
- Else (still processing):
  return `jsonify({"ready": False})`, 202

`/progress` endpoint: NO CHANGES -- already returns the correct JSON
structure for any job type.

**Reused functions (do not duplicate):**
- `_check_user_exists()` -- username validation (already in routes.py)
- `acquire_job_slot()` / `start_job_thread()` -- concurrency control
- `create_job()` / `get_job_context()` / `delete_job()` -- job lifecycle
- `cleanup_expired_jobs()` -- stale job cleanup

**Tests (integration -- middle of pyramid):**
- `/heatmap_loading` POST: valid username (mock exists) -> 202 + `job_id` in JSON
- `/heatmap_loading` POST: missing username -> 400 + error JSON
- `/heatmap_loading` POST: nonexistent username (mock not exists) -> 404 + error JSON
- `/heatmap_loading` POST: no job slot available -> 429 + error JSON
- `/heatmap_loading` POST: thread start failure -> 500 + error JSON, job cleaned up
- `/heatmap_data` GET: completed job with results -> 200 + daily_counts JSON
- `/heatmap_data` GET: completed job with error -> 200 + error JSON
- `/heatmap_data` GET: missing job_id param -> 400
- `/heatmap_data` GET: expired/missing job -> 404
- `/heatmap_data` GET: job still processing -> 202 + `{"ready": false}`
- `/heatmap_data` GET: job error (set_job_error sets results=[]) ->
  error response (not `{"ready": true, ...}` with empty list)

**Acceptance criteria:**
- All route tests pass
- CSRF enforced on POST (test with `csrf_app_client` fixture)
- Error paths return correct HTTP status codes and JSON bodies
- Results check uses `is not None` (not falsy check)
- Docstrings on all handler functions
- `pre-commit run --all-files` passes

**SESSION_CONTEXT updates:**
- Section 4: `routes.py <- ..., heatmap`

**Net tests:** +N (estimated 10-12)
**Commit:** `feat(heatmap): add heatmap route handlers`

---

### WP-3: Frontend -- index.html pill tabs + heatmap form + CSS

**Goal:** Add the pill tab UI, heatmap form card, loading/result/error
containers, and all markup to index.html. Create heatmap CSS. Place the
pinwheel SVG for inline include.

**Files:**
- `templates/index.html` (MODIFY)
- `templates/base.html` (MODIFY -- add CSRF meta tag to head)
- `templates/inline/scrobblescope_pinwheel.svg` (NEW -- copy from
  `docs/images/scrobblescope_pinwheel_expanded.svg`)
- `static/css/heatmap.css` (NEW)

**Implementation detail:**

CSRF meta tag in `base.html` `<head>` (needed for AJAX POST from any page):
```html
<meta name="csrf-token" content="{{ csrf_token() }}">
```
This follows the same pattern as loading.html's existing meta tag.

Pill tab markup (above the form card, below info button):
- Two pills: "Album Filtering" (default active) | "Heatmap"
- Styled with existing decade-pill visual language (rounded, centered)
- `data-mode="album"` / `data-mode="heatmap"` attributes for JS targeting
- Active state: `--bars-color` background, white text

Heatmap form section (hidden by default, `d-none`):
- Same `.card.shadow` pattern as album form card
- Username field: `form-control` with same validation pattern as album form
- Submit button: same styling as album "Search Albums" button
- Hidden CSRF token field (same pattern as album form)
- `id="heatmap-form-section"` for JS targeting

Heatmap loading container (hidden, `d-none`):
- `id="heatmap-loading"` for JS targeting
- Centered pinwheel SVG: `{% include 'inline/scrobblescope_pinwheel.svg' %}`
  inside a container div with max-width constraint
- Progress text: `<p id="heatmap-progress-text">Initializing...</p>`
- Error container within: message + retry button + home link

Heatmap result container (hidden, `d-none`):
- `id="heatmap-result"` for JS targeting
- `.card.shadow` wrapper for the SVG grid
- `<div id="heatmap-grid"></div>` -- JS injects SVG here
- Color scale legend container
- "Search again" button to return to form state

CSS (`heatmap.css`):
- Pill tab bar: flex, centered, gap matching decade pills
- Active pill: `background-color: var(--bars-color); color: #fff`
- Inactive pill: `border: 1px solid var(--border-color)`
- `.dark-mode` overrides for pill colors (uses `var()` so mostly automatic)
- Heatmap form card: inherits `.card.shadow` from global.css
- Loading container: centered, max-width for pinwheel
- Pinwheel SVG sizing: `max-height: 64px` on desktop, `48px` on mobile
- Progress text: centered, muted color, small font
- Fade transitions: `opacity` + `transition: opacity 0.3s ease`
- Heatmap result card: full width within col-md-8 (wider than form col-md-6)
- Responsive mobile rules matching existing index.css patterns
- Grid rect styles: `rx`/`ry` for rounded corners (set via JS on SVG)
- Tooltip styles (positioned div): shadow, dark/light variants

**Note:** Pill switching JS is in WP-4. This WP is markup + CSS only.
Verify by toggling `d-none` classes in browser dev tools.

**Acceptance criteria:**
- Pills render correctly on desktop and mobile
- Album form completely unchanged and functional
- All hidden containers present in DOM with correct IDs
- CSS transitions defined and working
- Mobile layout matches album card behavior (Firefox Responsive Design Mode)
- Pinwheel SVG renders inline (animated) in loading container
- CSRF meta tag present in page head
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
- `static/css/heatmap.css` (MODIFY -- add SVG grid + tooltip styles if needed)
- `templates/index.html` (MODIFY -- add script tag for heatmap.js)

**Implementation detail:**

Pill switching:
- Click handler on pill elements toggles `.d-none` on form sections
- Album form visible by default; heatmap form hidden
- Update active pill class (add/remove active background)
- No fade transition on pill switch (instant swap, KISS)

Username validation:
- On blur: same `/validate_user` fetch as album form (reuse existing endpoint)
- Show green checkmark / red X via `is-valid` / `is-invalid` classes

Form submission (AJAX):
- Prevent default form submit
- Read CSRF token from `<meta name="csrf-token">` (added in WP-3)
- POST to `/heatmap_loading` with `FormData` or `URLSearchParams`
  including `username` + `csrf_token`
- Headers: `X-CSRFToken: <token>`
- On success (202 + `job_id`): hide form, show loading container, start polling
- On error (4xx/5xx): show error in heatmap error container
- Fail fast on client-side validation (empty username)

Polling:
- Fetch `GET /progress?job_id=...` every 1 second
- Update progress text: use `stats.pages_fetched` and `stats.total_pages`
  from progress stats when available; otherwise show `message`
- On `progress === 100` + `error === false`: fetch `GET /heatmap_data?job_id=...`
- On `error === true`: show error message, retry button if retryable
- On network error: show generic error with retry option

SVG rendering (from `/heatmap_data` JSON):
- Parse `daily_counts`, `from_date`, `to_date`, `max_count` from response
- Calculate grid layout: 7 rows (Mon-Sun) x 52-53 columns (weeks)
- Start from `from_date`, align first day to correct day-of-week row
- Create `<svg>` with `viewBox` for responsive scaling, `width="100%"`
- Each day: `<rect>` with `rx`/`ry` for rounded corners, gap between cells
- Color mapping: `log10(count+1) / log10(max+1)` maps to rocket_r stop index
- rocket_r stops (hardcoded hex, 7 stops):
  ```
  0.00: #03051a  (near-black)
  0.17: #2a0f4e  (deep purple)
  0.33: #6a176e  (purple-red)
  0.50: #a62c5c  (red)
  0.67: #d44e41  (orange-red)
  0.83: #f0903a  (orange)
  1.00: #f9d576  (cream-gold)
  ```
  (Agent will sample exact values from seaborn rocket_r and propose for
  owner approval before hardcoding.)
- Zero-scrobble cells: distinct muted fill (`#e0e0e0` light / `#2a2a2a` dark)
- Color scale legend: horizontal bar at bottom with labels (0, max)
- Month labels: short month names above the first column of each month

Tooltips:
- Positioned `<div>` added to DOM on first hover, reused thereafter
- Show on `mouseover` / `touchstart` on each `<rect>`
- Content: "Sunday 1 March 2026 -- **34 scrobbles**" (or "No scrobbles")
- Position: above or below the cell (flip if near top edge)
- Dismiss on `mouseout` / `touchend` / scroll
- Styled with shadow, `var(--surface-elevated)` background, correct
  dark/light mode colors

State transitions (all within index.html):
- **Form -> Loading**: hide form card, show loading container with fade-in
- **Loading -> Result**: hide loading container, show result card with fade-in
- **Loading -> Error**: show error within loading container (no transition)
- **Result -> Form**: "Search again" button hides result, shows form

Dark mode:
- Respect existing `.dark-mode` class on body (toggled by theme.js)
- Zero-scrobble cell fill adapts to dark/light
- Tooltip background uses `var(--surface-elevated)`
- Pill tabs use `var(--bars-color)` and `var(--border-color)`
- rocket_r palette works on both backgrounds naturally

**Acceptance criteria:**
- Full end-to-end flow: pill switch -> form -> loading -> heatmap renders
- Tooltips work on hover (desktop) and tap (mobile)
- Dark mode toggle works with heatmap visible
- SVG scales responsively (fill card width on any screen)
- Aesthetically pleasing grid with rounded cells and gaps
- Month labels visible and correctly positioned
- Color scale legend renders
- No `innerHTML` used with user-supplied data (`textContent` exclusively)
- Owner tests in Firefox + Responsive Design Mode
- `pre-commit run --all-files` passes

**Net tests:** +0 (JS -- owner tests visually; unit testing JS is out of
scope for iteration 1)
**Commit:** `feat(heatmap): add heatmap.js with SVG rendering and polling`

---

### WP-5: Expanded backend tests + edge cases

**Goal:** Strengthen the test suite with additional edge cases and
integration scenarios discovered during implementation. Verify no regressions.

**Files:**
- `tests/test_heatmap.py` (MODIFY -- expand)
- `tests/test_routes.py` (MODIFY -- expand if needed)
- `tests/test_repositories.py` (MODIFY -- add dict copy test if not covered)

**Scope:**
- Aggregation with tracks spanning midnight boundary (23:59 -> 00:01)
- Leap year: range spanning Feb 29 produces correct day count
- User with exactly 1 scrobble in 365 days
- "Now playing" tracks: verified skipped (no crash, no phantom counts)
- Large volume: 50,000+ track entries aggregated correctly
- `_aggregate_daily_counts` with tracks outside the date range -> ignored
- Route: `/heatmap_data` when `set_job_error` has set results=[] ->
  returns error JSON (not `{"ready": true}` with empty payload)
- Route: malformed/empty username variants
- `get_job_context` dict copy: verify heatmap dict result is copied
- `no_scrobbles_in_range` error code: verify it exists in ERROR_CODES
  with correct source, retryable, and message fields
- Verify all 350+ existing tests still pass (no regressions)
- Every new test fails if the function under test is deleted

**Acceptance criteria:**
- All tests pass (350 existing + all new heatmap/route tests)
- No test duplicates existing coverage
- No vacuous tests (per AGENTS.md anti-pattern registry)
- `pre-commit run --all-files` passes

**Net tests:** +N (estimated 6-10 additional)
**Commit:** `test(heatmap): expand edge case and integration tests`

---

## 3. Testing strategy (pyramid)

**Unit tests (base -- most tests):**
- `tests/test_heatmap.py`: aggregation logic, date parsing (uts-based),
  edge cases, progress reporting, error paths, partial data. All with
  mock page data.

**Integration tests (middle):**
- `tests/test_routes.py`: heatmap route handlers with Flask test client.
  CSRF, error codes, job lifecycle, results-None-vs-empty-list distinction.

**E2E tests (top -- owner-driven):**
- Owner tests locally in Firefox + Responsive Design Mode between WPs.
- Full flow: pill switch -> form -> loading (pinwheel) -> heatmap display
- Tooltips, dark mode, mobile responsiveness
- Error cases (bad username, no scrobbles in range)
- Browser MCP can verify deployed behavior post-deploy

---

## 4. Software principles (enforced)

| Principle | Application |
|-----------|-------------|
| DRY | Call existing functions in lastfm.py, repositories.py, worker.py. No fetch/job duplication. |
| SoC / SRP | heatmap.py = orchestration. routes.py = HTTP. heatmap.js = rendering. One reason to change each. |
| KISS | Counter aggregation, hardcoded colors, vanilla SVG. No frameworks. |
| Dependency Inversion | heatmap.py depends on function signatures, not concrete internals. |
| Composition over Inheritance | No class hierarchies. Compose via function calls. |
| Least Knowledge | heatmap.py never touches JOBS dict directly -- only via repositories helpers. |
| Fail Fast | Validate username before job creation. Check empty scrobbles early. Error guard on upstream status. |
| Boy Scout Rule | Dict copy fix + docstring fix in repositories.py (WP-1). |
| Clean Architecture | Data flows one direction: HTTP -> route -> task -> repositories -> HTTP. No cycles. |

---

## 5. Open items requiring owner input

1. **rocket_r color stops**: agent will extract hex values from seaborn's
   rocket_r colormap and propose for owner approval before hardcoding.
   (Pinwheel SVG is already provided -- item 1 from original plan resolved.)

---

## 6. Verification gates (per WP)

```bash
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Owner tests locally in Firefox (+ Responsive Design Mode) before
approving the next WP.

---

## 7. UI/UX flow (all on index.html)

```
index.html loads
  -> Pill tabs: [Album Filtering (active)] [Heatmap]
  -> Album form card visible (default)

User clicks "Heatmap" pill:
  -> Album form card hides (d-none)
  -> Heatmap form card shows (username input + submit button)

User submits heatmap form:
  -> JS intercepts, AJAX POST to /heatmap_loading
  -> Heatmap form hides
  -> Loading container shows: animated pinwheel SVG + progress text
  -> JS polls GET /progress?job_id=... every 1 second
  -> Progress text updates: "Fetching page 3 of 45..."

Poll returns progress=100, error=false:
  -> JS fetches GET /heatmap_data?job_id=...
  -> Loading container hides
  -> Result container shows: SVG heatmap grid + color legend
  -> "Search again" button returns to heatmap form

Poll returns error=true:
  -> Loading container shows error message
  -> Retry button (if retryable) or "Back" button

User clicks "Album Filtering" pill at any time:
  -> Heatmap state resets, album form shows
```
