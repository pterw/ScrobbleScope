# BATCH21: UI overhaul -- Tailwind + daisyUI migration

**Status:** Active. Owner-approved 2026-07-24 (expanded from the Claude Design audit, ScrobbleScope UI Audit v3). WP-0 committed; WP-1 (toolchain) is next.
**Branch:** `wip/batch-21` (linked worktree; lineage changes are recorded
in PLAYBOOK Section 4 rather than pinned here).
**Baseline:** 390 tests passing. This batch touches production templates, static assets, and (WP-7 only) `routes.py`/`orchestrator.py`; the count may move and each WP records its own validated count.

---

## Context

The owner's UI audit concluded: the heatmap's shipped look (warm cream /
inky-purple surfaces, 14px frame, mono small-caps KPIs) is correct and the
job is to propagate it to every other screen. Stack verdict, endorsed by
agent review: keep Flask + Jinja2, no React; migrate Bootstrap 5.1.3 ->
Tailwind CSS (standalone CLI, no Node project) + daisyUI restricted to
`card`, `modal`, `btn`, `toggle`, `input`, `select`, `tabs`, `toast` +
`alert` (added for the WP-5 toast rewrite), and the `data-theme` system.
Custom surfaces (heatmap, leaderboard, editorial headers) stay raw
Tailwind utilities.

Agent verification against `main` (2026-07-24) confirmed the audit's key
bug claims:

- `_group_unmatched_by_reason` (`routes.py:63`) keys on the interpolated
  prose from `_get_user_friendly_reason` (`orchestrator.py:162`), so
  unmatched groups fragment into one group per release year. Live bug.
- `--bs-primary` is never overridden; every remaining `btn-primary` /
  `btn-outline-primary` renders stock Bootstrap blue.
- Bootstrap JS consumers are the welcome modal, the unmatched quick-view
  modal, AND `bootstrap.Popover` for the "?" form tooltips
  (`index.js:268-271`) -- one more than the audit counted. All three must
  be replaced or deleted before `bootstrap.bundle.min.js` can go.
- `--bars-color` is read via `var()` in six of the seven page CSS files
  (all but `unmatched.css`, which hardcodes its own
  `--header-bg: #6a4baf`) plus the inline pinwheel SVG. The inline
  wordmark hardcodes `stroke: #6a4baf`; only the dark-mode override at
  `global.css:49-50` routes it through the variable, so light-mode
  wordmark recoloring must be handled explicitly during migration --
  aliasing alone does not cover it. The variable must be aliased inside
  both daisyUI themes, never deleted.
- Bootstrap CSS comes from cdnjs while `index.html` pulls the JS bundle
  from jsdelivr (F-B20-3); this batch resolves the split by elimination.

**Fixed assets (not up for redesign):** the breathing pinwheel SVG, the
header wordmark + waveform, both inlined via `{% include %}` (never
`<img>` -- dark-mode recoloring requires inline SVG), and the rocket_r
heatmap data palette.

**Migration strategy:** strangler, page by page (the Batch 8 pattern).
WP-2 moves the Bootstrap CSS `<link>` out of `base.html` into a per-page
block so migrated pages load only Tailwind while unmigrated pages keep
Bootstrap. Theme state dual-writes `data-theme` (html) and `.dark-mode`
(body) until every consumer (`theme.js`, `heatmap.js`, `results.js`
html2canvas clone) is migrated, then `.dark-mode` retires.

---

## Owner decisions (locked 2026-07-24)

1. **Rotating loading messages (WP-4): CUT.** Phase label + live counters
   replace them; keep one threshold-fired big-library notice.
2. **Welcome modal (WP-3): DELETE.** The hero replaces it; Info button
   becomes a small about panel.
3. **`limit_results` control (WP-3): KEEP**, relocated into the
   thresholds disclosure -- `_apply_pre_slice()` is a real Spotify-load
   and cache saving on large libraries. Not dropped, not half-wired.
4. **Fonts (WP-2): SELF-HOSTED** woff2 files under `static/fonts/`
   (Geist, Instrument Serif, JetBrains Mono -- all OFL-licensed). No
   Google Fonts CDN.

---

## Acceptance criteria (batch level)

1. Every page (index, loading, results, unmatched, error) renders from
   Tailwind + daisyUI themes; no Bootstrap CSS or JS is loaded anywhere.
2. Both themes derive from the heatmap token sheet (light `#faf8f3` /
   dark `#0e0c12`-`#181520`, purple primary `#6a4baf` light /`#b39dde`
   dark, warm cream text); no cool-grey `#f8f9fa` / `#121212` surfaces
   remain. The heatmap frame no longer sits on a mismatched background.
3. `--bars-color` aliases the theme primary in both themes; pinwheel and
   wordmark render correctly in both modes on every page.
4. Standing header bar on all pages: wordmark left (~64px), theme toggle
   top-right; footer toggle removed; landing page keeps the large brand
   moment in the hero.
5. CSV export, JPEG export (both modes, mobile + desktop), progress
   polling, username validation, decade pills, and thresholds disclosure
   all still work; the results list remains a semantic `<table>`.
6. Unmatched page groups by stable `reason_code` (release_scope /
   no_spotify_match), not prose strings; the quick-view modal and
   welcome modal are deleted.
7. Long usernames (15 chars) wrap without clipping in results and
   heatmap headlines (`white-space: nowrap` dropped on mobile headline).
8. Mode pills have equal width (closes F-B18-12); toggle meets tap-target
   size (closes F-AUDIT-1).
9. `pytest -q` green and all pre-commit hooks pass at every WP; docs
   (README tech stack + structure, SESSION_CONTEXT, DEVELOPMENT.md build
   step) updated by close-out.

---

## Work packages

### WP-0 -- Batch open

Commit this definition on `wip/batch-21`; PLAYBOOK Section 2/3 rows;
kickoff log entry.
`chore(batch): open Batch 21 (UI overhaul -- Tailwind + daisyUI)`

### WP-1 -- Toolchain + themes (no template changes)

- Tailwind v4 standalone CLI binary lives in gitignored `scripts/bin/`
  (per-platform executable -- committing it bloats the repo or breaks
  other platforms). `scripts/bin/.gitkeep` keeps the directory present
  on clone.
- `scripts/dev/tailwind_build.py`: fetches the correct per-platform
  binary at a pinned version when missing, then builds (`--watch`
  supported). This is the guaranteed rebuild path. `dev_start.py` stays
  untouched -- app startup never needs the toolchain because compiled
  CSS is committed.
- Pin exact Tailwind + daisyUI versions in the fetch script: the WP-8
  drift hook requires byte-identical output across machines and CI.
- Commit per-platform SHA-256 digests alongside the pinned versions;
  `tailwind_build.py` verifies every artifact (CLI binary and daisyUI
  plugin files) against its digest on every use, not only at download
  time -- gitignored `scripts/bin/` persists between runs, so a stale,
  corrupt, or modified cached artifact must be caught too. On mismatch:
  refetch once, re-verify, fail closed if the replacement also
  mismatches. A pinned version alone still trusts whatever asset the
  release serves at fetch time; without digests the WP-8 CI hook would
  execute a silently replaced binary.
- daisyUI v5 bundled plugin files for standalone-CLI use: `daisyui.mjs`
  (components) plus `daisyui-theme.mjs`, which the two custom `@plugin`
  theme definitions below require -- the component bundle alone cannot
  register custom themes.
- `static/css/tailwind.src.css` defining the two themes from the audit
  token sheet, pinned here so any executor can implement without
  re-fetching the audit: light bg `#faf8f3` / bg-2 `#f0ebe0` / ink
  `#1a1820` / primary `#6a4baf`; dark bg `#0e0c12` / surface `#181520` /
  text `#f1ede4` (warm cream) / primary `#b39dde`. Type (self-hosted per
  decision 4): Geist 300-700 (body 14-16px, labels 11.5-13px),
  Instrument Serif 400 + italic (>= 24px only), JetBrains Mono 400-600
  (numerals, eyebrow labels, pills). 4px spacing ladder
  (4/8/12/16/24/32/48 only); radius 8 (inputs/small cards), 14 (large
  cards), 999 (pills); `--bars-color` aliased in both themes.
- Compiled `static/css/tailwind.css` committed; build/watch commands
  documented in DEVELOPMENT.md; CI unaffected (no Node).
`feat(ui): add tailwind + daisyui toolchain and theme tokens`

### WP-2 -- base.html shell + strangler enabler

- Fonts (per decision 4) in `base.html`; body font-family finally set.
- Standing header bar (wordmark ~64px + theme toggle); footer toggle
  removed; `theme.js` dual-writes `data-theme` + `.dark-mode`.
- Bootstrap CSS link moved from `base.html` into a per-page block;
  `error.html` (smallest page) migrates fully as the pilot.
- Coexistence isolation: each template loads exactly one framework
  stylesheet through that per-page block -- migrated pages load
  `tailwind.css`, unmigrated pages keep Bootstrap -- because Bootstrap
  and daisyUI both claim `.btn`/`.card`/`.modal` and Tailwind's
  preflight would reset Bootstrap pages if loaded globally. The shared
  shell (header bar, footer) is styled by a small framework-neutral
  `static/css/shell.css` loaded on every page so it renders identically
  during coexistence; WP-8 absorbs it into `tailwind.src.css`. Rejected
  alternative: a daisyUI component prefix -- it permits dual-loading but
  forces prefix-removal churn across every migrated template at WP-8,
  and the one-sheet rule already prevents the collision.
- `global.css` moves out of `base.html` into the same legacy per-page
  stack: it carries Bootstrap-coupled `.card`/`.card-body`/`.modal-*`
  rules (`global.css:141-199`) that would restyle daisyUI components on
  migrated pages if it stayed global. Unmigrated pages keep reading
  their theme tokens from it; migrated pages get tokens from the
  daisyUI themes, and the wordmark recolor plus shared-shell styling
  move to `shell.css`.
`feat(ui): tailwind base shell, header bar, error page pilot`

### WP-3 -- Index page

- Editorial hero; form regrouped (identity / filtering / display /
  thresholds); segmented Albums|Heatmap tabs sharing one card frame.
- Decade pills restyled; year input becomes placeholder + join-year hint
  (front-end only; `/validate_user` already returns `registered_year`).
- "?" popovers replaced: obvious fields get nothing or inline hints,
  ambiguous fields (release scope, sort) get CSS-only hints -- removes
  the `bootstrap.Popover` dependency.
- Thresholds disclosure with +/- steppers over real number inputs,
  "reset to 10 - 3" affordance, expands in place pushing the CTA down.
- Decisions 2 and 3 land here (welcome modal, limit_results placement).
`feat(ui): rebuild index page on tailwind`

### WP-4 -- Unified loading experience

- Shared Jinja2 loading partial used by `loading.html` and the heatmap
  panel: pinwheel + thin determinate hairline bar, mono phase label
  ("FETCHING SCROBBLES - PAGE 23 / 102"), four-KPI stat strip (same
  component shape as heatmap KPIs), parameter chip row replacing the
  table.
- Decision 1 lands here (rotating messages).
- Leaving the page: a quiet "Back home" link only -- no
  `/reset_progress` call and no "Cancel" label. The endpoint cannot
  cancel anything: it clears stored job state only
  (`routes.py:227-238`) while the daemon worker keeps its concurrency
  slot and keeps writing into the same job id afterward, so invoking it
  is misleading and racy. True server-side cancellation stays a
  Batch 22+ candidate.
`feat(ui): unified pinwheel loading screen for both pipelines`

### WP-5 -- Results leaderboard

- Grid-styled rows over a real `<table>`; two-column desktop flow +
  KPI rail (total / top artist / excluded -> view); mobile single
  column, rank kept as inline mono numeral.
- CSV export keeps day precision: date cells carry the full ISO date in
  a `data-export` attribute and the walker prefers `data-export` over
  rendered text. `results.js` currently exports each cell's rendered
  desktop text, so the `MMM YY` restyle below would otherwise silently
  truncate exported release dates to month precision.
- Editorial headline with username wrap rules (min-height reserve,
  `overflow-wrap: anywhere` on the username span, no nowrap).
- Mono numerals, MMM YY dates; one primary + ghost secondaries; art
  fallback = artist-hash tinted gradient; unmatched quick-view modal
  deleted (decision confirmed by audit + agent).
- `results.js`: onclone desktop-forcing rewritten to set the row
  `grid-template-columns`; toasts rewritten on daisyUI; JPEG export
  tested in both modes at mobile + desktop widths.
`feat(ui): results leaderboard rebuild`

### WP-6 -- Heatmap seam removal

- Page background/frame unified with the promoted global themes; the
  `:root` token block leaves `heatmap.css`.
- Month labels to mono small-caps; one warm rocket_r accent pulled into
  the page UI; headline nowrap clip fixed; `.mode-pill` `min-width`
  equalized (F-B18-12).
`feat(ui): unify heatmap page with global theme`

### WP-7 -- Unmatched page + reason_code (only backend WP)

- `orchestrator.py`: stable `reason_code` (release_scope /
  no_spotify_match) stored alongside the prose reason; `routes.py`
  groups on the code, keeps the sentence as per-row detail. Fixes the
  verified grouping bug; unit tests updated in lockstep (this is where
  the test count moves). `below_min_plays` / `below_min_tracks` are
  deliberately not introduced here: `fetch_top_albums_async` drops
  threshold failures before the pipeline sees them
  (`orchestrator.py:112-116`), so those codes only become producible
  once near-miss retention (out of scope below, Batch 22+) lands.
- Two reason cards with human copy, top offenders + expander; same row
  component as the leaderboard; welcome + unmatched modals now gone so
  `bootstrap.bundle.min.js` is removed from all templates.
`feat(unmatched): stable reason codes + card layout`

### WP-8 -- Sweep + close-out

- Remove every remaining Bootstrap reference (closes F-B20-3 by
  elimination); radius/spacing ladder sweep; kill dead CSS.
- Add a `tailwind-css-drift` pre-commit hook: rebuild via
  `tailwind_build.py`, then fail if
  `git diff --exit-code -- static/css/tailwind.css` reports the
  committed compiled CSS dirty. The pathspec scopes the check to the
  generated file so unrelated dirty tracked files (or rewrites left by
  earlier hooks in the same run) cannot produce false drift failures.
  Catches source/output drift without anyone remembering to rebuild.
  Caveat: the hook also runs in CI, so the fetch step must work headless
  on Linux (pinned version; consider caching the binary between runs).
- Docs: README (tech stack, structure, screenshots note), DEVELOPMENT.md
  (build step), SESSION_CONTEXT Sections 1/3.
- Owner E2E pass in Firefox + Responsive Design Mode -- explicitly
  including opening the downloaded save-as-image file in both themes,
  since that failure mode is silent and invisible in normal review.
  Then standard close-out (archive definition, purge log, mark complete).
`chore(close-out): Batch 21 complete; archive definition and purge log`

---

## Validation gate (every WP)

```
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Plus per-WP: owner visual review in both themes before the next WP.

Any WP that changes templates or `tailwind.src.css` (WP-2 through WP-7)
must run `tailwind_build.py` and commit the refreshed `tailwind.css` in
the same commit: production serves the committed file with no runtime
build, and the drift hook only arrives at WP-8, so an intermediate page
could otherwise ship without its generated utilities while every listed
command still passes. (The hook stays in WP-8 rather than moving to
WP-1: that would front-load the headless-CI fetch problem before any
template exists to protect.)

---

## Out of scope (Batch 22+ candidates, from the audit's backend section)

- Near-miss retention in `fetch_top_albums_async` + "loosen filters"
  quantified controls (+58 albums) on the unmatched page (introduces
  the `below_min_plays` / `below_min_tracks` reason codes).
- `GET /unmatched_view` + routing the empty-result state there.
- Shareable heatmap URL (`GET /heatmap/<username>`).
- Purpose-built save-as-image card node (wordmark + top 10 + chips).
- True server-side job cancellation.
- Bootstrap 5.3 upgrade path -- mooted by the Tailwind migration.
