# Batch 12: Polish and Observability (2026-02-22)

Audited and finalized: 2026-02-23.

## 1. Scope and goals

Primary goals:
- Eliminate CSS tech debt to ensure consistent theme architecture.
- Optimize mobile presentation (temporal rounding, column widths) without
  breaking desktop data exports (CSV/JPEG).
- Purify `lastfm.py` into a strict infrastructure client (zero business logic,
  zero domain/repositories imports).
- Improve backend progress granularity for smoother user feedback during
  Last.fm and Spotify fetching phases.

Out of scope for Batch 12:
- Feature additions (e.g., Top Songs, Listening Heatmaps).
- Postgres job state migration (deferred to a dedicated architectural batch).
- Route layer DRY (WP-4 from original proposal) -- already completed as a
  side-task on 2026-02-22 (`_get_filter_description` rename,
  `_get_validated_job_context` extraction, `/results_complete` and
  `/unmatched_view` refactored). See PLAYBOOK Section 4 log entry.

Execution rules:
- Implement one work package at a time, in order.
- Checkpoint commits at each self-contained, tests-passing change.
- Validation before every commit:
  - `.\venv\Scripts\python.exe -m pytest -q`
  - `.\venv\Scripts\python.exe -m pre_commit run --all-files`
- Follow `AGENTS.md` commit rules (Conventional Commits, no co-author trailers).
- Update `PLAYBOOK.md` Section 4 + `SESSION_CONTEXT.md` Section 2 after each WP.
- Run `.\venv\Scripts\python.exe scripts/doc_state_sync.py --fix` after doc edits.

---

## 2. Work packages

### WP-1 (P0): Semantic CSS Variable Enforcement

**Problem:** Structural UI elements (backgrounds, borders, form inputs) duplicate
hardcoded hex values across 6 component stylesheets. This violates DRY and
breaks the centralized theme architecture established in Batch 11 WP-1.

**Files:**
- `static/css/global.css`
- `static/css/index.css`
- `static/css/results.css`
- `static/css/loading.css`
- `static/css/error.css`
- `static/css/unmatched.css`

**New variables (`:root` / `.dark-mode` in `global.css`):**

| Variable | Light | Dark | Replaces |
|----------|-------|------|----------|
| `--surface-color` | `#ffffff` | `#1e1e1e` | Card/modal/error-card/toggle backgrounds |
| `--surface-elevated` | `#ffffff` | `#2a2a2a` | Toast headers, table-light backgrounds |
| `--border-color` | `#ccc` | `#444` | Card borders, modal borders, toggle borders |
| `--input-bg` | `#ffffff` | `#333` | Dark-mode form input backgrounds |
| `--error-accent` | `#dc3545` | `#dc3545` | Promoted from orphaned definition in `error.css`; consumed in `error.css` + `loading.css` |

**Implementation steps:**
1. Add the 5 variables (with dark-mode overrides) to `:root` / `.dark-mode` in
   `global.css`. Remove the orphaned `--error-accent` from `error.css`.
   Checkpoint commit.
2. Replace hardcoded hex in `global.css` (toggle widget, card, modal rules).
3. Replace hardcoded hex in `index.css` (dark input bg/border, pill borders).
4. Replace hardcoded hex in `results.css` (dark toast-header, release-badge).
5. Replace hardcoded hex in `loading.css` (error message colors via `--error-accent`).
6. Replace hardcoded hex in `error.css` (dark error-card bg/border, consume `--error-accent`).
7. Replace hardcoded hex in `unmatched.css` (dark card bg/border, dark table bg).
8. Checkpoint commit: all replacements.

**Scope note:** Only structural backgrounds, borders, inputs, and error accent.
Utility/accent colors (`--bars-color`, `--text-color`, `--bg-color`, `--info-bg`)
already exist. Page-specific contextual colors like `#856404` (partial-warning
gold), `#999`/`#aaa` (muted text), and `#5a3d99` (btn-primary hover) are left
alone -- they are contextual, not structural.

**JS fix:** `results.js` L167 has `backgroundColor: '#121212' / '#ffffff'`
hardcoded for `html2canvas`. The light-mode value (`#ffffff`) already mismatches
`--bg-color` (`#f8f9fa`), causing a subtle background color discrepancy in
JPEG exports. `html2canvas` accepts standard CSS color strings, so replace the
ternary with:
`backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-color').trim()`
This ensures the JPEG background always matches the live UI theme and maintains
`global.css` as the single source of truth. Include this fix in WP-1.

**Acceptance criteria:**
- Visual UI is identical to pre-refactor state in both light and dark mode.
- Dark mode toggles cleanly across all pages without visual desync.
- No pre-commit or test regressions.

---

### WP-2 (P1): Responsive Data Formatting & Export Parity

**Problem:**
- Temporal display values ("1 day, 12 hours, 38 min") crowd the mobile viewport
  and cause table geometry spillover.
- The existing CSV export logic (`cell.textContent` scraping) blindly
  concatenates hidden responsive spans. The `release_date` column already uses
  dual `d-none d-md-inline` / `d-md-none` spans, so CSV output corrupts the
  date (e.g., `"2024-03-152024-03"`). Adding play_time responsive spans would
  introduce the same bug there.
- The `html2canvas` JPEG export sets `windowWidth: 1200` but this does **not**
  reliably re-evaluate CSS media queries on cloned elements. `html2canvas`
  captures computed styles from the source document at clone time -- on a
  mobile viewport, `d-none d-md-inline` elements are already computed as
  `display: none` before cloning, and `windowWidth` cannot override that.
  The `onclone` callback must explicitly manipulate the cloned DOM to
  force-show desktop spans, hide mobile spans, and unhide rank columns.

**Files:**
- `scrobblescope/utils.py`
- `scrobblescope/orchestrator.py`
- `templates/results.html`
- `static/css/results.css`
- `static/js/results.js`

**Implementation steps:**
1. Add `format_seconds_mobile(seconds)` in `utils.py` -- max 2 units,
   abbreviated (e.g., "1d 12h", "4h 30m", "38m 15s"). Add unit tests in
   `tests/test_utils.py`. Checkpoint commit.
2. Update `_build_results` in `orchestrator.py` to emit `play_time_mobile`
   using `format_seconds_mobile`. Update existing `_build_results` tests to
   expect the new field. Checkpoint commit.
3. Add responsive `d-none d-md-inline` / `d-inline d-md-none` spans for
   `play_time` in `results.html`, mirroring the existing `release_date`
   pattern. Add `white-space: nowrap` to temporal/date data cells in
   `results.css`. Checkpoint commit.
4. Fix CSV extraction in `results.js`: when a cell contains a `.d-md-inline`
   element, extract only that element's text, ignoring `.d-md-none` spans.
   This fixes the existing `release_date` concatenation bug and prevents the
   same bug for `play_time`. Checkpoint commit.
5. Fix `html2canvas` `onclone` in `results.js`: explicitly hide `.d-md-none`
   elements and force-show `.d-md-inline` elements in the cloned DOM to
   guarantee consistent desktop-layout export regardless of viewport width.
   Checkpoint commit.

**Acceptance criteria:**
- Mobile viewports display truncated time markers without table spillover.
- CSV exports contain a single, clean desktop-formatted string per row (for
  both release dates and play times).
- JPEG export replicates desktop layout with all columns and full-length data.

---

### WP-3 (P1): Backend SoC Extraction

**Problem:** `lastfm.py` houses `fetch_top_albums_async` (business logic: album
aggregation, filtering, normalization) alongside raw HTTP client functions. It
still imports from `domain.py` (`normalize_name`, `normalize_track_name`,
`_extract_registered_year`). The prior side-task removed `repositories` imports
and the stats-dict decoupling is complete, but the function itself and domain
imports remain.

**Files:**
- `scrobblescope/lastfm.py`
- `scrobblescope/domain.py`
- `scrobblescope/orchestrator.py`
- `tests/test_domain.py`
- `tests/services/test_lastfm_logic.py`
- `tests/services/test_lastfm_service.py`

**Implementation steps:**
1. Inline the 5 lines of `_extract_registered_year` logic directly into
   `check_user_exists` in `lastfm.py`. Remove the import from `domain.py`.
   Remove `_extract_registered_year` from `domain.py`. Delete the 2 tests in
   `test_domain.py` (`test_extract_registered_year_valid`,
   `test_extract_registered_year_missing_key`). Add one new test to
   `test_lastfm_service.py`: `test_check_user_exists_missing_registration_data`
   -- mock a 200 OK with `{}` body, assert `result["registered_year"] is None`.
   (Valid-path coverage already exists via `test_check_user_exists_success`
   which asserts `registered_year == 2016`.) Checkpoint commit.
2. Move `fetch_top_albums_async` (~66 lines) from `lastfm.py` to
   `orchestrator.py`. Add `from scrobblescope.lastfm import
   fetch_all_recent_tracks_async` to orchestrator's imports. Remove
   `normalize_name`, `normalize_track_name` imports from `lastfm.py` (they
   move with the function; orchestrator already imports them from `domain`).
   Checkpoint commit.
3. Update `tests/services/test_lastfm_logic.py`: change import from
   `scrobblescope.lastfm` to `scrobblescope.orchestrator` for
   `fetch_top_albums_async`. Update internal mock paths
   (`scrobblescope.orchestrator.fetch_all_recent_tracks_async`).
   `test_orchestrator_service.py` already mocks `scrobblescope.orchestrator.
   fetch_top_albums_async` -- verify it works naturally. Checkpoint commit.

**Post-state:** `lastfm.py` is a pure HTTP client with zero `domain` imports
and zero `repositories` imports. `check_user_exists` inlines the 5-line
vendor-specific JSON parsing for registration year (it was Last.fm DTO
parsing, not domain logic). `orchestrator.py` grows to ~796 lines.

**Acceptance criteria:**
- `lastfm.py` contains zero business logic, zero `domain` imports, zero
  `repositories` imports.
- All 210+ tests pass after relocation and import rewiring.
- No behavioral change -- identical runtime behavior.

---

### WP-4 (P2): Granular Backend Progress Pipeline

**Problem:** Progress polling jumps from 5% to ~40% (entire Last.fm fetch) and
from 40% to 60% (entire Spotify batch). Users lack visibility into the longest
phases. The existing frontend (`loading.js`) consumes `progressData.progress`
(numeric) and `progressData.message` (text via `stepText`) from the polling
response -- smoother backend increments and more descriptive messages will be
consumed automatically.

**Files:**
- `scrobblescope/lastfm.py`
- `scrobblescope/orchestrator.py`
- `static/js/loading.js` (minimal changes if any)

**Implementation steps:**
1. Add an optional `progress_cb: Callable[[int, int], None] | None = None`
   parameter to `fetch_all_recent_tracks_async` in `lastfm.py`. After page 1
   resolves (which reveals `total_pages`), invoke `progress_cb(1, total_pages)`
   if provided. Invoke again after each subsequent page completes. Checkpoint
   commit.
2. In `_fetch_and_process` in `orchestrator.py`, pass a `progress_cb` lambda
   that calls `set_job_progress` to map page-fetching progress into the 5%-20%
   range (currently a single jump). Message: "Fetching Last.fm page
   {n}/{total}...". Checkpoint commit.
3. In `_fetch_spotify_misses` (or the calling code in `_fetch_and_process`),
   replace `asyncio.gather` for the batch detail fetch with
   `asyncio.as_completed`. After each batch of 20 resolves, call
   `set_job_progress` to increment within the 40%-60% range. Message:
   "Enriched {n}/{total} albums from Spotify...". Add/update tests.
   Checkpoint commit.

**Frontend impact:** Minimal. `loading.js` already reads `progressData.progress`
and `progressData.message`. The smoother % increments and more descriptive
messages are consumed automatically by `stepText`. The percentage-bucket
`stepDetails` text remains frontend-driven (cosmetic) and unchanged. The
`updateLiveStats` function reads structured stat fields -- no changes needed
unless new stats are emitted (additive). If the frontend percentage
bucket boundaries (e.g., 40-59% rotator) need tuning for the new granular
increments, adjust the thresholds in `loading.js`.

**Acceptance criteria:**
- Progress bar moves incrementally during Last.fm page fetching (5%-20% range).
- Progress bar moves incrementally during Spotify batch enrichment (40%-60%).
- All tests pass.
- No behavioral change to final results.

---

## 3. Execution order

1. **WP-1** -- Isolate CSS variable changes before any DOM changes.
2. **WP-2** -- Presentation formatting + JS export fixes (depends on stable CSS).
3. **WP-3** -- Backend SoC extraction (must precede WP-4 since WP-4 modifies
   functions that WP-3 relocates).
4. **WP-4** -- Granular progress pipeline (builds on WP-3's relocated code).

---

## 4. Validation checklist (per checkpoint commit)

- `.\venv\Scripts\python.exe -m pytest -q` -- all tests pass.
- `.\venv\Scripts\python.exe -m pre_commit run --all-files` -- all hooks pass.
- Stage only files changed for this checkpoint.
- Conventional Commits format, no co-author trailers.

Per-WP completion:
- Update `PLAYBOOK.md` Section 3 (status) + Section 4 (dated log entry inside
  current-batch markers).
- Update `SESSION_CONTEXT.md` Section 2 (test count, batch status) if changed.
- Run `.\venv\Scripts\python.exe scripts/doc_state_sync.py --fix`.

---

## 5. Audit notes

**WP-4 from original proposal (Route Layer DRY) removed:** All 4 implementation
steps were already completed by the 2026-02-22 side-task
`refactor(routes,lastfm)`. `_get_filter_description` renamed and hoisted,
`_get_validated_job_context` extracted, both routes consume it, tests pass.

**WP-3 split from original proposal:** The original WP-3 conflated two distinct
risk profiles (architectural refactor vs. new UX behavior). Split into WP-3
(SoC extraction, no behavioral change) and WP-4 (progress pipeline, new
behavior). This ensures a clean rollback boundary.

**`_extract_registered_year` disposition:** The function in `domain.py` is
vendor-specific Last.fm JSON DTO parsing (`data["user"]["registered"]
["unixtime"]`), not domain logic. Inlining into `check_user_exists` purifies
both `domain.py` (no API schema knowledge) and `lastfm.py` (no domain import
for this function). Existing test coverage: `test_check_user_exists_success`
covers the valid path; a new `test_check_user_exists_missing_registration_data`
covers the missing-key path.

**One `domain` import remains after WP-3:** If `fetch_top_albums_async` is
relocated and `_extract_registered_year` is inlined, `lastfm.py` will have
zero `domain` imports. This is achievable.

**JS hardcoded colors fixed in WP-1:** `results.js` L167 had `'#121212'` /
`'#ffffff'` hardcoded for `html2canvas` `backgroundColor`. The light-mode value
(`#ffffff`) mismatched `--bg-color` (`#f8f9fa`). WP-1 replaces the ternary with
`getComputedStyle(document.documentElement).getPropertyValue('--bg-color').trim()`
to maintain `global.css` as the single source of truth.

**CSV dual-span bug (existing):** The `release_date` column already has
responsive spans, and `cell.textContent` concatenates both (e.g.,
`"2024-03-152024-03"`). WP-2 fixes this for both `release_date` (existing)
and `play_time` (new).