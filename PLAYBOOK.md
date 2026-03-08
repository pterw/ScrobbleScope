# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` |
| 18 | Scrobble heatmap -- iteration 1 | `BATCH18_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 18 is active.** Branch: `feat/heatmap`. Definition: `BATCH18_DEFINITION.md`.
- **Next action:** WP-5 -- expanded backend tests + edge cases.
- WP status:
  - WP-1: Backend heatmap task module + error code -- **done**
  - WP-2: Backend heatmap routes -- **done**
  - WP-3: Frontend pill tabs + heatmap form + CSS -- **done**
  - WP-4: Frontend heatmap.js (SVG rendering, polling, tooltips) -- **done**
  - WP-5: Expanded tests + edge cases -- **pending**
- Future feature candidates (confirmed by owner roadmap):
  - **Top songs** (future): rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

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

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-03-05 - Post-Batch-17 doc staleness fix

- PLAYBOOK Section 3 still said "Batch 17 is active" and listed all WP
  statuses after the close-out commit (743f8ae). Updated to "Between batches"
  with heatmap feature noted as next action on branch `feat/heatmap`.
- SESSION_CONTEXT Section 1 branch updated from `wip/batch-17` to
  `feat/heatmap`; date bumped to 2026-03-05.
- STATUS block refreshed by `doc_state_sync --fix`.
- Batch 17 log entries remain inside CURRENT-BATCH markers per docsync
  design -- they will auto-rotate to `BATCH17_LOG.md` when the next batch
  is declared active in Section 3.
- **350 tests passing**, all hooks green.
