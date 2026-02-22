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
| 0 | Baseline freeze + approval parity suite | `docs/history/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/BATCH10_DEFINITION_2026-02-21.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 10 is complete.** Definition: `docs/history/BATCH10_DEFINITION_2026-02-21.md`.
- **Batch 11 is in progress** (Gemini 3.1 Pro Priority 2 audit remediation --
  SoC, DRY, and architectural findings).
  - WP-1 (Low): CSS/JS theme consolidation. Done. (Created `global.css` +
    `theme.js`; stripped ~250 lines of duplicate CSS from 5 per-page files;
    removed dark-mode toggle JS from 5 JS files; fixed html2canvas mobile
    export; added back-to-top button on results page. 121 tests passing.)
  - WP-2 (Medium): Decompose `process_albums` in `orchestrator.py`. Pending.
  - WP-3 (Low): CSS/JS DRY violations, toggle markup bug, and UX polish.
    Done. (Promoted `--info-bg` to `global.css`, removing split `:root`/
    `.dark-mode` blocks from `results.css` and hard-coded rgba from
    `loading.css`; moved duplicate modal dark-mode block from `index.css`
    and `results.css` to `global.css`; stripped Bootstrap `form-check
    form-switch` classes from toggle markup that conflicted with custom CSS
    via Bootstrap's injected SVG background-image knob; added `text-align:
    center` to loading-page `.step-text`/`.step-details`; removed redundant
    mobile release-date shortening JS from `results.js`; `var`->`const` for
    `darkSwitch`/`backToTop` in `theme.js`; dark-mode toggle track changed
    from `var(--bars-color)` to `var(--bg-color)` when checked. 121 tests
    passing.)
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days
    (Last.fm-only, lighter background task).
- Do not start feature work (top songs, heatmap) until owner defines scope
  and assigns a batch number.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

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

<!-- DOCSYNC:CURRENT-BATCH-END -->
