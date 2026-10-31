<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# BATCH21_LOG -- page 0002

### 2026-09-12 - Unmatched table repaired and the dead-utility class closed (Batch 21 WP-7)

- Scope: WP-7 follow-up, run in the order the owner chose -- documentation
  corrections first, then the unmatched table repair, then the F-B21-52 guard.
  Plan of record: the approved session plan, which found that the Phase 1 file
  table of `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`
  already named "the narrower four-column budget" as an `unmatched.css`
  deliverable that never landed.
- Cause, measured: the page's row padding (`py-2.5`) and all four column widths
  (`w-10`, `w-24`, `w-28`, `md:w-28`, `md:w-32`) were Tailwind utilities the
  theme's spacing reset compiles to nothing. Above 768px every row had 0px
  padding and the four columns were equal quarters -- 74.8px each at 1024px. A
  dead `min-w-0` on the headline row also scrolled the whole document
  horizontally at 768px and 1024px. Below 768px the table borrowed the Results
  mobile block, which is why review missed it.
- Implementation: `static/css/unmatched.css` now owns the column budget
  (`nth-child` from 768px, the reason column at 30%), containment, and the panel
  tracks keyed on a `data-panels` attribute; `templates/unmatched.html` uses
  ladder steps and arbitrary values only, lets the headline and fix hint wrap,
  drops the toolbar's extra `btn-sm sm:btn-md`, and accents the fix hint on the
  `below_threshold` panel only. `--unmatched-surface` is deleted in favour of
  `--results-surface`, and the page width matches Results at 94%. The 14 dead
  tokens in `templates/results.html` were deleted, measured render-neutral at
  four viewports with the compiled sheet unchanged. Measured after, on the
  threshold panel: 12px row padding at every width, the album column widest at
  every width, no document overflow anywhere. Its tightest case was 1024px, where
  that column was 140px. That was not readable once the cover took its share:
  see the 2026-09-13 breakpoint deviation below.
- Inspection round, screenshots at 1440px in both themes and at 390px, found
  what no check covered, all fixed in one batch: the metric header clipped to
  "PLAYS / TRA"; the threshold metric ellipsized to "7 plays ..."; a rank column
  narrower than its link pill, clipping the pill's focus ring; three panels in two
  tracks leaving a hole under the first (the second panel now spans both rows);
  the summary total running on from the last filter value; and a borrowed 4.25rem
  mobile reason column that broke "selected" into letters. The confirmation round
  was clean.
- Deviations:
  - The owner chose two panels at 1024px and three at 1536px. Three tracks
    measured 448px at both 1536px and 1920px because the page stops at 90rem, so
    two is the maximum instead. Recorded in `docs/design/RECONCILIATION.md`
    section 16 for owner confirmation.
  - `2xl:grid-cols-3` did not survive the Tailwind scan, silently, so the tracks
    are authored in CSS rather than as utilities.
  - The owner chose the Results-sized cover. `static/css/unmatched.css` was set
    back to the committed 40px/44px cover at 09:57, outside this session. The
    owner confirmed the Results size on 2026-09-13, and it was re-applied then:
    `.unmatched-artwork` mirrors `.album-cover-img`, and the gate, spec and
    section 16 now describe it. Put back at 40px/44px, the gate failed on every
    profile.
  - Owner rulings on 2026-09-13: two panels is the maximum; the fix-hint accent
    stays; the threshold panel is titled "Not enough listening" (F-B21-58
    resolved). Review nits fixed at the same time: the grid comment no longer
    names utilities, so Tailwind drops two dead rules; `.unmatched-page` no
    longer restates the `.results-page` width; the gate's unused cover fields
    are gone.
  - Two panels now share a row from 1280px, not 1024px (owner ruling,
    2026-09-13). A Playwright pass at 1024px found album titles 20-36px wide,
    broken into columns of two or three letters beside the Results-sized cover.
    From 1024px to 1279px a panel now takes the full width. The gate's profiles
    never land between 390px and 1280px, so `check_unmatched_report` now sweeps
    1024px, 1279px and 1280px for the panel count and a 96px title floor. The
    sweep failed at 1024px and 1279px on every profile before the CSS change and
    passes after it.
  - The fix hint and the per-panel "albums" label are 12px, not 9px (owner
    ruling, 2026-09-13), which decides F-B21-4 item 4. The gate pins both
    sizes. With the label put back at 9px, the new `countLabelSize` pin failed
    on every profile.
  - The untracked `docs/superpowers/plans/2026-09-12-batch21-phase2-design-record-reconciliation.md`,
    corrected at the start of this work, was removed from disk outside this
    session and was never committed, so its corrections are lost with it.
  - The documentation corrections that preceded this repair are logged as their
    own side-task entry, "Documentation reconciled to the shipped unmatched
    page", because they are the design-record reconciliation the Phase 2 plan
    classes as side tasks. `RECONCILIATION.md` section 16 belongs to this entry.
- Gate changes: `check_unmatched_report` expects two tracks from 1280px, reads
  covers numerically, and newly measures row padding, the column budget's shape,
  document-level overflow, clipped cell content and 44px coarse-pointer
  controls, and now also runs on the wide touch profile. The clipping check
  compares each cell's rendered contents with its box, because Chromium counts
  end padding into `scrollWidth`; restoring the three clippings failed it at
  every profile they reach. Seen to fail on disk: restoring `py-2.5` and removing
  the budget failed desktop and wide touch on padding and equal columns, while
  mobile passed -- the original desktop-only defect, reproduced.
- Guard: `tests/test_template_shell.py` gained
  `test_no_template_uses_a_spacing_step_the_theme_does_not_declare` and its
  adversarial helper test, closing F-B21-52. Seen to fail on disk naming both
  injected tokens. F-B21-58 filed for the "thresholds" copy conflict; the 9px
  fix-line size stayed with F-B21-4 item 4 until the owner ruled 12px on
  2026-09-13 (see Deviations).
- Design hook: suppressed `broken-image` for `templates/unmatched.html` only,
  with evidence -- the src-less portrait `img` is hidden until hydration and the
  gate asserts on it. The 9px `design-system-font-size` finding was left standing
  as an owner question; the 12px ruling cleared it.
- Validation: `pytest -q` -- **1028 passed**. `python scripts/dev/frontend_gate.py`
  -- **26 checks passed in 48 runs** across chromium and firefox.
- Forward guidance: do not reintroduce numeric spacing utilities; the guard will fail. If three panels
  are wanted, the lever is the 90rem page cap, not the promotion breakpoint.

### 2026-09-11 - PR #231 Linux cleanup tests made portable (Batch 21 WP-7)

- Scope: diagnosed the failed Quality Gate on PR #231 and repaired the two
  worker-cleanup tests without changing production behavior or UI rendering.
- Root cause: GitHub Actions checked the PR merge commit on Ubuntu, where
  `asyncio.ProactorEventLoop` is absent. Both new cleanup tests patched that
  Windows-only attribute unconditionally, so pytest stopped with two
  `AttributeError` failures after pre-commit had passed.
- Implementation: both tests now use `patch(..., create=True)` for the
  platform-specific loop class. Their mocked `run_until_complete` also closes
  the produced coroutine, eliminating the resource warnings from the cleanup
  path under test.
- Pre-commit audit: the hook suite is behaving as configured. It checks Python
  lint/format, document state, generated Tailwind drift, and worktree alignment;
  it does not run pytest or emulate Linux APIs. Adding the local Windows suite
  to pre-commit would still miss this defect, so the repair belongs at the
  cross-platform test seam rather than as a new hook.
- Validation: the two focused tests pass both normally and after removing
  `asyncio.ProactorEventLoop` from the process; `pytest -q` reports **986
  passed** with no warnings. Final pre-commit, docsync, and remote Quality Gate
  evidence follow before completion is claimed.
- Forward guidance: publish this review-fix commit, confirm PR #231 is green,
  then amend the WP-7 scope and plan for the owner-requested threshold reason
  and horizontal report design before implementation.

### 2026-09-11 - Threshold and horizontal report extension approved (Batch 21 WP-7)

- Scope: amended WP-7 before implementation to retain albums rejected at the
  play/unique-track boundary and restyle unmatched groups as full-width
  horizontal report sections.
- Owner decision: one stable `below_threshold` group covers either failed
  minimum. An album failing both appears once and retains its actual plays,
  unique-track count, and failed-threshold list.
- Design authority: current `results.html`, `results.css`, and computed browser
  behavior win over the dated design snapshot. Unmatched will mirror Results'
  composition, scale, surface, actions, and table rhythm while removing its
  own eyebrow and purple italic username.
- Architecture: partition after Last.fm aggregation and before Spotify. Store
  threshold exclusions through the existing unmatched repository, preserving
  the current Spotify cost boundary and the lazy `/api/artist_spotlight`
  fallback for missing art.
- Documentation: added the approved design and supplemental implementation
  plan, amended the active definition, and retained the original WP-7 plan as
  the record of the completed first pass.
- Validation: documentation gates and implementation evidence follow in the
  commits that execute the extension.
- Forward guidance: execute backend Task 1 first, then the horizontal Results-
  aligned UI task. Keep each as an independently revertible commit.

### 2026-09-11 - Below-threshold albums retained (Batch 21 WP-7)

- Scope: completed backend Task 1 of the approved WP-7 extension without
  changing UI rendering.
- Implementation: Last.fm aggregation now partitions eligible albums from
  exclusions that fail plays, unique tracks, or both. Each excluded album is
  stored once with the `below_threshold` reason code, actual counts, configured
  minimums, and failed-threshold list.
- Pipeline boundary: exclusions are persisted only after a successful Last.fm
  response and before the eligible-empty terminal state. They never enter
  Spotify processing; an all-excluded job completes normally with empty Results
  and a populated unmatched report.
- Validation: focused partition, Last.fm, orchestrator, and route coverage
  passes. `pytest -q` -- **989 passed**. Repository gate evidence is refreshed
  before commit.
- Forward guidance: execute Task 2, using current Results source and computed
  output as the visual authority for the horizontal unmatched report.

### 2026-09-11 - Side-by-side unmatched horizontal reports and 500-album cap unified (Batch 21 WP-7)

- Scope: completed Task 2 of the WP-7 extension. Reconciled two extension documents
  (`2026-09-11-batch21-wp7-threshold-horizontal-report-extension.md` and
  `2026-09-11-unmatched-threshold-horizontal-report-design.md`) against
  `docs/design/designsystemaudit.md` (canonical source of truth) and owner directives.
  Replaced stacked reason sections with responsive side-by-side horizontal report panels
  sorted by unmatched reason, reconciled design tokens against `results.html`, and
  diagnosed and resolved the unbounded 500-album cap defect in `orchestrator.py`.
- Architectural context & plan reconciliation:
  - Spec Reconciliation: The initial design spec proposed full-width stacked reason sections
    ("stacked, full-width reason sections instead of the current three-column card grid").
    The owner explicitly superseded this layout directive: "There should be more than one
    horizontal report; they should be sorted by the unmatched reason. The UI should be like
    results.html, and do considere the designsystemaudit.md as cannonical source of truth.
    They should not be stacked, but side-by-side".
  - Canonical Design System (`docs/design/designsystemaudit.md`): Live styles do not use
    the unmigrated Claude Design token layer (`--surface-page`, `--text-body`, etc., which
    collide with Tailwind v4 namespaces). The live design system uses three layers: daisyUI
    slots, the `--ss-*` extension set, and Tailwind `@theme static`.
- Implementation details:
  - Side-by-Side Responsive Layout: The `.unmatched-groups` container arranges reason reports
    side-by-side in a responsive grid (`grid-cols-1 lg:grid-cols-3` or `lg:grid-cols-2`
    depending on reason count, `gap-6 items-start`). Order is deterministic: `below_threshold`
    -> `release_scope` -> `no_spotify_match`. On desktop (>=1024px), reports sit side-by-side
    sharing identical top offsets; on mobile (<1024px), the grid collapses to a single column
    preventing horizontal page scroll.
  - Results Design Tokens & Typography:
    - Surface: `--results-surface` (`color-mix(in srgb, var(--color-base-100) 50%, var(--ss-surface-sunken))`).
    - Borders & Radius: 1px hairline `var(--ss-border-default)`, `--radius-sm` (8px / 0.5rem) on panels,
      and `--radius-xs` (4px / 0.25rem) on artwork.
    - Artwork Dimensions: 44px desktop (`2.75rem`), 40px mobile (`2.5rem`) with explicit
      containment (`aspect-ratio: 1/1; object-fit: cover`).
    - Typography Roles: Instrument Serif (`font-serif`) for page title, Gotham figure numerals
      (`--font-figure`) for album counts adhering to the Role Segregation Rule (audit L943-L950,
      D-17), Input Mono (`--font-mono-narrow`) for ranks and 9px uppercase fix hints, Akzidenz
      Grotesk (`font-sans`) for table body/labels, and neutral headline username without italics
      or purple accent.
    - Proportional Scaling: `syncResultsScale()` reading `--results-base-rem: 75` on
      `.unmatched-page`, scaling `--results-scale` with window resizing / `ResizeObserver`
      (matching Results dynamic scaling in audit L228-L232).
  - Disclosure & Async House Pattern:
    - Preserved 10-row disclosure with Results-style ghost buttons and album counts.
    - Artist portrait progressive hydration via `/api/artist_spotlight` fallbacks. Hardened
      with post-`await` name verification (`artwork.dataset.artistName?.trim() === artistName`)
      to strictly uphold the house stale-response guard pattern identified in `designsystemaudit.md`
      L1011-L1021.
    - Noted for WP-8: `.dark-mode` class write on `<body>` is actively observed by `heatmap.js`
      (audit L841-L868) and is preserved intact.
  - Backend Safety Cap:
    - Diagnosed defect via `/diagnosing-bugs`: `_PLAYTIME_ALBUM_CAP = 500` was only applied
      when `sort_mode == "playtime"`. In default playcount mode, unbounded thousands of
      albums bypassed slicing, exhausting Spotify API rate limits and freezing the DOM on
      `results.html`.
    - Defined `_MAX_ALBUM_CAP = 500` in `scrobblescope/orchestrator.py` (aliasing
      `_PLAYTIME_ALBUM_CAP`) and enforced it unconditionally in `_apply_pre_slice` across all
      sort modes (`playcount` and `playtime`).
  - Design Snapshot Test: Added `"designsystemaudit.md"` to `REPOSITORY_OWNED_PATHS` in
    `tests/test_design_snapshot.py` to preserve the 61-file design manifest digest.
- Validation:
  - `frontend_gate.py` updated to verify desktop side-by-side layout (`groupTops[0] === groupTops[1]`,
    `gridColumns === 3`) and mobile single-column stacking; passed all 26 checks across 47 runs
    in Chromium and Firefox.
  - `pytest -q` -- **990 passed** (up from 989; added tests for unified `_MAX_ALBUM_CAP` in
    `tests/services/test_orchestrator_helpers.py` and `tests/test_routes.py`).
  - Pre-commit hooks (`ruff check`, `ruff format`, `whitespace`, `tailwind-css-drift`,
    `doc-state-sync-check`, `worktree-alignment`) passed.
- Forward guidance: Batch 21 WP-7 extension is complete and verified across both browser engines.
  Pause for owner review before beginning WP-8.

### 2026-09-11 - Unmatched disclosure refined: 25-row step and collapse on return (Batch 21 WP-7)

- Scope: `templates/unmatched.html`, `static/js/unmatched.js`,
  `static/css/unmatched.css`, the rebuilt `static/css/tailwind.css`,
  `scripts/dev/frontend_gate.py` (the two new assertions, which landed later
  with the F-B21-51 slice-1 commit), and `tests/test_routes.py`. No server-side
  change; the Task 1 contract stands.
- Owner rulings applied, both from the 2026-09-11 review:
  1. a 50-row reveal is too much, so `data-step` and the server-rendered label
     become 25 (the owner allowed 20 or 25; 25 is recorded as the choice);
  2. the back-to-top control now collapses its panel as well as scrolling, so
     the reader is not left above a table they had just padded.
- Implementation: the expander's row visibility, button copy and
  `aria-expanded` were three copies of one state machine spread across two
  handlers. They collapse to a single `applyVisibleCount(count, isCollapsed)`
  writer that both the expander and the back-to-top control call.
- Design refinement, applying the `daisyui` skill's colour rule 10 ("use
  `primary` only for the most important element on the page. Use it only
  once") and its usage rules 2 and 7 (prefer utilities over custom CSS):
  - the panel album count moves off `primary` to `base-content`, matching the
    filter-bar summary count and leaving the page's one primary to the New
    Search action;
  - the panel header takes Results' scale-aware padding,
    `p-4 md:p-[calc(1.25rem*var(--results-scale))]`, so the panel block rhythm
    scales as Results' own surfaces do;
  - the reason-detail cell stops truncating and wraps instead: a side-by-side
    panel is narrower than a full-width row, and an ellipsis there would hide
    the sentence that explains the exclusion.
- The layout is unchanged. The owner ruled side-by-side on 2026-09-11; the
  spec's earlier "stacked, full-width" wording is superseded and is corrected in
  the documentation pass.
- Deviation, resolved rather than carried: the committed `tailwind.css` held a
  stale `.collapse { visibility: collapse; }` utility that no source produces
  (only `border-collapse` appears anywhere). The rebuild drops it, and this
  commit lands the rebuilt file so the drift hook is clean. That rule entered
  with the previous WP-7 commit, not with this change.
- Validation: `pytest -q` -- **1020 passed**; the two-engine frontend gate --
  "26 checks passed in 47 runs across chromium, firefox (static assets & tokens
  canary on firefox); profiles: desktop, mobile, wide touch". Pre-commit runs
  after this entry, per the documentation-first commit order.
- Forward guidance: the panel padding now scales with `--results-scale`, so a
  later edit to that curve moves the panel rhythm with it. WP-8 still owns
  retiring `global.css` and the `.dark-mode` write, with `heatmap.js`'s
  observer moved to `data-theme` in the same change.
