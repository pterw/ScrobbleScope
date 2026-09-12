# Reconcile WP-7 Extension Plans, Fix 500-Album Cap Defect, and Align Results/Unmatched UI

Reconcile the two WP-7 extension documents ([Spec](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md) and [Plan](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/docs/superpowers/plans/2026-09-11-batch21-wp7-threshold-horizontal-report-extension.md)) using [docs/design/designsystemaudit.md](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/docs/design/designsystemaudit.md) as the canonical design system source of truth. Build multiple stacked horizontal reports sorted by unmatched reason mirroring `results.html`, diagnose and fix the backend 500-album cap issue, and resolve all validation gates.

## User Review Required

> [!IMPORTANT]
> **Multiple Stacked Horizontal Reports Sorted by Unmatched Reason**:
> Per your guidance, the unmatched report is rendered as **multiple stacked horizontal sections**, one per reason group, deterministically sorted in the following order:
> 1. `below_threshold` — Title: `Below your thresholds`. Subtitle: `Played in {{ year }}, but below {{ min_plays }} plays or {{ min_tracks }} unique tracks.`
> 2. `release_scope` — Title: `Outside Release Filter`. Subtitle: `Albums released outside your selected release-date scope.`
> 3. `no_spotify_match` — Title: `No Spotify Match`. Subtitle: `Albums found in your Last.fm history that could not be matched on Spotify.`
> 4. Any historical/legacy reason prose strings sorted alphabetically afterward.

> [!IMPORTANT]
> **Backend 500-Album Cap Unified Across Sort Modes**:
> Currently, `_PLAYTIME_ALBUM_CAP = 500` in `orchestrator.py` only caps playtime sort. When sorting by playcount (default) with `limit_results == "all"` (default), unbounded thousands of albums are enriched and sent to `results.html`. We will enforce `_MAX_ALBUM_CAP = 500` across all sort modes so `results.html` never attempts to render unbounded thousands of rows.

> [!NOTE]
> **Design Snapshot Repository-Owned Exemption**:
> We will add `"designsystemaudit.md"` to `REPOSITORY_OWNED_PATHS` in `tests/test_design_snapshot.py` (joining `RECONCILIATION.md`). This keeps `docs/design/designsystemaudit.md` in its canonical place while allowing `test_design_snapshot.py` to pass.

---

## Canonical Design System Principles (from `designsystemaudit.md`)

[docs/design/designsystemaudit.md](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/docs/design/designsystemaudit.md) establishes the true code-backed design system:
1. **Three-layer Token Architecture**:
   - **daisyUI theme slots**: `--color-base-100` (`#faf7f0` light / `#0e0c12` dark), `--color-base-content` (`#1a1820` / `#f1ede4`), `--color-primary` (`#6a4baf` / `#b39dde`), `--color-primary-content` (`#faf8f3` / `#0e0c12`).
   - **`--ss-*` extension set**: `--ss-surface-card` (`#f9f7f1` / `#181520`), `--ss-surface-sunken` (`#f0ebe0` / `#1a1622`), `--ss-text-body` (`#4a4456` / `#c5bfb1`), `--ss-text-muted` (`#6c6676` / `#908a9a`), `--ss-border-default` (`#e5dfd1` / `#2a2434`), `--ss-accent-soft` (`#efe9fa` / `#2a1f44`).
   - **`@theme static`**: `--font-sans` (Akzidenz-Grotesk Next Pro), `--font-serif` (Instrument Serif), `--font-figure` (Gotham for numerals), `--font-mono` / `--font-mono-narrow` (Input Mono / Narrow), `--radius-xs` (4px), `--radius-sm` (8px).
2. **Surfaces & Radii**:
   - Panel surface: `--results-surface` / `--unmatched-surface`: `color-mix(in srgb, var(--color-base-100) 50%, var(--ss-surface-sunken))`.
   - Section wrapper radius: `8px` (`var(--radius-sm)`).
   - Artwork radius: `4px` (`var(--radius-xs)`).
3. **Geometry & Scaling**:
   - Full measure: `90rem` (1440px), matching Results.
   - Dynamic scaling via `syncResultsScale()` updating `--results-scale` on `.results-page` / `.unmatched-page` from `--results-base-rem: 75`.
   - Rem for type and space; px for hairlines and radii.

---

## Audit: Spec vs. Plan Reconciliation Matrix

| Feature | Spec | Plan | Reconciled Implementation |
| :--- | :--- | :--- | :--- |
| **Reason Sections** | Stacked full-width horizontal sections | Stacked sections | One full-width table section per reason, ordered `below_threshold` -> `release_scope` -> `no_spotify_match`. |
| **Threshold Title** | `Below your thresholds` (sentence case) | Uses `meta.title` | `Below your thresholds` in `CATEGORY_METADATA` and template. |
| **Threshold Description** | Dynamic naming of minimums | Generic string | `Played in {{ year }}, but below {{ min_plays }} plays or {{ min_tracks }} unique tracks.` |
| **Page Max Width** | `90rem` (1440px) | Mentions Results | `.unmatched-page { max-width: 90rem; }` in `unmatched.css`. |
| **Section Surface & Radius** | Warm midpoint surface, 8px radius, no drop shadow | Results-aligned | `.unmatched-group { background: var(--results-surface); border: 1px solid var(--ss-border-default); border-radius: var(--radius-sm); box-shadow: none; }` |
| **Artwork Sizing** | 44px desktop / 40px mobile | 44px / 40px | `.unmatched-artwork { width: 2.5rem; height: 2.5rem; } @media (min-width: 768px) { width: 2.75rem; height: 2.75rem; }` |
| **Metric Column** | Plays/tracks | Plays/tracks | Threshold rows: `{{ item.play_count }} plays / {{ item.track_count }} tracks`. Other rows: `{{ item.play_count }}` under `#metric-header-label` ("Plays / tracks"). |
| **Expander Button** | 10-row disclosure | 10-row disclosure | `.unmatched-expander-btn btn btn-ghost results-action font-mono text-xs text-[var(--color-primary)]` toggling `.unmatched-overflow` hidden rows. |
| **Fix Hint** | 9px purple mono line | 9px mono | `.unmatched-fix-hint text-[0.5625rem] uppercase tracking-wider text-[var(--color-primary)] truncate`. |
| **Scale Custom Property** | Viewport scaling | syncResultsScale | `syncResultsScale()` in `unmatched.js` linked to `ResizeObserver` and window resize. |

---

## Bug Diagnosis: Backend 500 Cap & Results Rendering (`/diagnosing-bugs`)

### Symptom
`results.html` is poorly rendered and can show over thousands of albums that did not meet the cap -- in the backend, there is code for a limit of 500 albums.

### Root Cause
1. In `scrobblescope/orchestrator.py`, `_PLAYTIME_ALBUM_CAP = 500` is applied **only** when `sort_mode == "playtime"`.
2. When `sort_mode == "playcount"`, `_apply_pre_slice` only slices if `limit_results != "all" and release_scope == "all"`.
3. By default on `index.html`: `sort_by == "playcount"`, `limit_results == "all"`, and `release_scope == "same"`.
4. Therefore, when users search albums with default settings, **zero cap is applied**! If a library has 2,500 albums passing `min_plays` and `min_tracks`, all 2,500 albums are fetched, enriched, and passed to `results.html`.
5. Rendering 2,500 table rows in `results.html` causes layout slowdown, client-side reordering freeze (`setLeaderboardMetric`), and canvas overflow crashes during JPEG export.
6. Furthermore, on `results.html`, the sidebar states that unmatched albums were "excluded by release date or missing Spotify data". Now that Task 1 includes `below_threshold` items, `unmatched_count` can be thousands of albums, confusing users.

### Fix
1. Define `_MAX_ALBUM_CAP = 500` in `orchestrator.py` as a universal safety bound before Spotify enrichment across all sort modes.
2. In `_apply_pre_slice`:
   ```python
   # Enforce the 500 cap regardless of sort mode to protect against Spotify API overload and frontend DOM bloat
   if len(filtered_albums) > _MAX_ALBUM_CAP:
       sorted_items = sorted(
           filtered_albums.items(),
           key=lambda kv: cast(int, kv[1]["play_count"]),
           reverse=True,
       )
       filtered_albums = dict(sorted_items[:_MAX_ALBUM_CAP])
   ```
3. In `templates/results.html`: update sidebar copy to accurately reflect that exclusions include thresholds:
   `{{ unmatched_count }} {% if unmatched_count == 1 %}album was{% else %}albums were{% endif %} excluded by your thresholds, release date, or missing Spotify data.`

---

## Proposed Changes

### 1. Backend & Domain
#### [MODIFY] [orchestrator.py](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/scrobblescope/orchestrator.py)
- Replace `_PLAYTIME_ALBUM_CAP = 500` with `_MAX_ALBUM_CAP = 500` (retaining `_PLAYTIME_ALBUM_CAP = _MAX_ALBUM_CAP` for backwards compatibility).
- Apply `_MAX_ALBUM_CAP` in `_apply_pre_slice` across all sort modes.

#### [MODIFY] [unmatched.py](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/scrobblescope/unmatched.py)
- Set `CATEGORY_METADATA[REASON_BELOW_THRESHOLD]["title"] = "Below your thresholds"` (sentence case).

### 2. Frontend UI
#### [MODIFY] [unmatched.html](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/templates/unmatched.html)
- Main element: `<main class="results-page unmatched-page mx-auto px-4 pt-4 pb-8 md:pt-6 md:pb-12">`.
- Masthead:
  - Neutral username: `<span class="unmatched-headline__user">{{ username }}</span>` without italics or purple.
  - Subtitle with filter description and minimums.
  - Action buttons: "Back to Results", "New Search" with `btn-primary`.
- Multiple horizontal report sections:
  - `{% for reason_key, albums in reasons.items() %}`: rendered as stacked `.unmatched-group` sections.
  - Section header: Title, dynamic description, and big Gotham count numeral (`.unmatched-count`).
  - Table: Semantic `<table>` with `#`, `Album & Artist` (with 44px/40px artwork and fallback/spotlight), `Plays / tracks` metric, and `Reason detail`.
  - 10-row expander toggle button (`.unmatched-expander-btn`).
  - Fix hint line (`.unmatched-fix-hint`).

#### [MODIFY] [unmatched.css](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/static/css/unmatched.css)
- Set `.unmatched-page { max-width: 90rem; }`.
- Set `.unmatched-group { background-color: var(--results-surface); border: 1px solid var(--ss-border-default); border-radius: var(--radius-sm); box-shadow: none; }`.
- Artwork: `width: 2.5rem; height: 2.5rem; border-radius: var(--radius-xs);` on mobile, `width: 2.75rem; height: 2.75rem;` at `min-width: 768px`.
- Fix hint: `font-size: 0.5625rem;` (9px), uppercase, tracking-wider, truncate.

#### [MODIFY] [unmatched.js](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/static/js/unmatched.js)
- Add `syncResultsScale()` function reading `--results-base-rem: 75` and setting `--results-scale` on `.unmatched-page`.
- Observe with `ResizeObserver` and window `resize`.

#### [MODIFY] [results.html](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/templates/results.html)
- Update sidebar copy to mention thresholds in exclusion reasons.

### 3. Tests & Gates
#### [MODIFY] [test_design_snapshot.py](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/tests/test_design_snapshot.py)
- Add `"designsystemaudit.md"` to `REPOSITORY_OWNED_PATHS` so `docs/design/designsystemaudit.md` is recognized as a repository-owned document.

#### [MODIFY] [frontend_gate.py](file:///c:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/scripts/dev/frontend_gate.py)
- Fix test fixture in `check_unmatched_report`:
  - Ensure `below-threshold` test item has an `album_image` so it does not trigger an unexpected extra spotlight request for Lizzy McAlpine.
  - Update assertions for 90rem width, multiple reason groups (3 groups), scaling, and row metric formatting.

---

## Verification Plan

### Automated Tests
1. **Design Snapshot Test**:
   ```bash
   & 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe' tests/test_design_snapshot.py
   ```
2. **Unmatched & Orchestrator Tests**:
   ```bash
   & 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe' tests/test_unmatched.py tests/services/test_orchestrator_fetch_and_process.py tests/test_routes.py
   ```
3. **Full pytest suite**:
   ```bash
   & 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe' -q
   ```
4. **Tailwind Build & Drift Check**:
   ```bash
   & 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe' scripts/dev/tailwind_build.py
   ```
5. **Two-Engine Frontend Gate (Chromium + Firefox)**:
   ```bash
   & 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe' scripts/dev/frontend_gate.py
   ```
6. **Pre-commit and Docsync**:
   ```bash
   & 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pre-commit.exe' run --all-files
   & 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe' scripts/doc_state_sync.py --check
   ```

### Manual Verification
- Verify multiple stacked horizontal report sections on `/unmatched`:
  - 1st: `Below your thresholds`
  - 2nd: `Outside Release Filter`
  - 3rd: `No Spotify Match`
- Verify section titles, dynamic subtitles, and Gotham counts.
- Verify 10-row disclosure button toggles extra rows cleanly.
- Verify 90rem width, 8px section radii, 44px/40px artwork, and Results midpoint surface.
- Verify `/results` sidebar copy and 500-album cap enforcement.
