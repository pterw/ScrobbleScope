# Batch 11 Execution Log

Archived entries for Batch 11 work packages.

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
