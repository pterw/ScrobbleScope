<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0013

### 2026-09-07 - Fix the three CI Quality Gate failures left by the Task-3/4 merge (side-task)

- Scope: diagnosed and fixed the three assertion families failing the
  `quality-gate` run on PR #227 (form centring, theme-toggle height, mobile
  body offset), all of them inherited from the `ebc5145` merge that took
  `test`'s pre-remediation CSS while keeping main's post-remediation gate.
- Plan vs implementation: as planned, after measurement overruled the
  owner's initial 0.5rem-shift hypothesis. The gate reported a constant
  80.0px top/bottom gutter imbalance at every window size, which is
  2 x 40px: the stale `top: -2.5rem` nudge (introduced in `f0acf4d`)
  fighting the `margin-block: auto` centre. Deleting the nudge shifts the
  form down 2.5rem, not 0.5rem, and lets the auto margins centre it -- the
  direction the owner pointed at, with the magnitude measurement dictates.
- Implementation:
  - `static/css/index.css`: removed the `position: relative; top: -2.5rem`
    nudge from the desktop `.index-form__inner` rule; `margin-block: auto`
    now does the centring alone. The nudge contradicted the F-B21-44
    "vertically centre the desktop form composition" owner refinement it
    sat next to -- it predates the flex-centring rule and was superseded,
    not removed, when that rule landed on main.
  - `static/css/shell.css`: reverted the theme-toggle padding from
    `0.25rem` (introduced in `14215d6`) to the ruled `0.2rem`, restoring
    the 8.4px chrome the gate's toggle-height curve adds to the
    theme-choice clamp (46.0 -> 44.4px at 1080p; 50.0 -> 48.4px at 1440p).
    Added a comment pinning the coupling so the next padding tweak does
    not silently break the gate.
  - `scripts/dev/frontend_gate.py`: the `bodyPaddingTop == headerHeight`
    mobile check encoded the fixed-header design that main's CSS still
    has; the merged redesign moved the header in-flow (`position:
    relative`) and dropped body padding, so the equality was false by
    construction. Replaced it with the invariant that design actually
    promises -- the first content pixel sits at or below the header's
    bottom edge -- measured as `contentTop >= headerBottom - 0.5`.
    Extracted the whole mobile-header assertion set into
    `_mobile_header_failures(width, header)` so each invariant has a
    unit-level seam, per the AGENTS.md helper-testing rules.
  - `static/css/tailwind.css`: rebuilt via `scripts/dev/tailwind_build.py`.
  - `tests/scripts/dev/test_frontend_gate.py`: added 7 unit tests for
    `_mobile_header_failures`, one per invariant, each with boundary
    cases (43.9 vs 44.0, 799.0 vs 799.6, 75.0 vs 75.6). Mutation-verified:
    all 6 guard-block removals are killed by the suite (no vacuous tests).
- Deviations: no clean uninterrupted `frontend_gate.py` run was achieved
  locally -- run 2 failed on a firefox theme-click timeout, run 3 on a
  pipeline state-machine timeout, run 4 on a port collision, and run 5
  was interrupted mid-flight. Runs 2-4 each failed on exactly one flaky
  timeout with the three CI families gone, but a single fully green run
  is still owed to the gate; CI's Linux runner provides the authoritative
  verdict for this push.
- Validation: `pytest -q` -- **932 passed**, 5 warnings (was 925; +7
  helper unit tests). `python scripts/doc_state_sync.py --check` exits 0
  (expected root BATCH warning). `pre-commit run --all-files` -- all 12
  hooks pass, including `tailwind-css-drift` on the rebuilt stylesheet.
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.

### 2026-09-06 - Rotate five Artist Spotlight candidates from the aggregate top ten (side-task)

- Scope: corrected the Results Artist Spotlight contract without changing
  album enrichment, Heatmap polling, the database schema, or CSS rules.
- Implementation:
  - Aggregate filtered albums by artist scrobbles, take the top ten, and select
    five unique candidates with a stable job-ID seed.
  - Render the first fallback immediately, hydrate the five artist profiles
    concurrently through the existing endpoint, and rotate locally every seven
    seconds. Reduced-motion readers keep one static candidate.
  - Removed metric sorting's competing top-album mutation and the album-ID
    fallback link. Candidate-slot, active-index, and image-revision guards keep
    late requests from replacing the active card.
  - Added a real-browser gate for five unique post-render requests and a card
    index change. The check failed when the production interval was disabled
    and passed after restoration in Chromium and Firefox.
- Follow-up: F-B21-48 records the separately scoped persistent Last.fm event
  cache. Current page-response caching is process-local, exact-range, and one
  hour only.
- Validation: `pytest -q` -- **925 passed**, 5 warnings. The latest route regression and
  frontend-gate unit subset passes 36 tests. Python/JavaScript syntax and
  docsync checks pass. The revised late-response browser harness still needs a
  clean full frontend-gate run.

### 2026-09-06 - UI copy clarity, heatmap eyebrow, and graceful page-load fade (side-task)

- Scope: applied /clarify and /audit workflows to the home → results flow; fixed heatmap partial eyebrow; added universal graceful page-load fade.
- Implementation:
  - Updated `templates/partials/_heatmap_result.html`: eyebrow changed from `"Listening heatmap"` to `"Last.fm scrobble heatmap"` to match the index hero copy style.
  - Updated `templates/index.html`: album mode lede rewritten to cut "specialized data visualization", "Enrich your scrobbles with Spotify metadata", and "isolate custom release eras" — replaced with a plain workflow description ("Choose a listening year and a release window…"). Heatmap lede: removed unexplained "rocket scale" jargon; replaced with a direct description of colour = intensity and tap-to-see interaction.
  - Added universal page-load fade to `static/css/shell.css` (`body { opacity: 0 }` + `body.is-ready { opacity: 1; transition: 220ms ease }`) and added the matching `DOMContentLoaded` trigger in `templates/base.html` (sequenced after the existing theme-before-paint inline script so dark/light theme commits before opacity resolves).
- Validation: `pytest -q` -- **924 passed**, 5 warnings.



- Scope: audited docsync tooling files (`scripts/docsync/*.py`, `.docsync.toml`) to verify DOC001-DOC011 integrity checks fire appropriately; identified and remediated three control-plane defects (F-DOCSYNC-8, F-DOCSYNC-9, F-DOCSYNC-10).
- Implementation:
  - F-DOCSYNC-8: Fixed TOML array-of-tables scoping defect in `.docsync.toml` where inserting `[[value]]` for `the wide-desktop scale cap` on 2026-08-28 detached the remaining 9 sites of `the single 860px breakpoint`. Reordered all 14 breakpoint sites contiguously (including missing frontend files `loading.css`, `empty.css`, and `theme.js`), added explicit `expect` values (`"860"` or `"859.98"`) to every site, cleanly separated the scale baseline and cap declarations, and added an architectural warning comment. Completed `expect` attributes on all 11 Adobe Fonts kit sites (`"rwy8ghw"`) and all 15 heatmap window sites (`"365"`).
  - F-DOCSYNC-9: Hardened `scripts/docsync/declarations.py:check_values` to retain `(rel_path, expect)` in `captured` when a declaration declares uniform expected values, eliminating the blind spot where partially annotated declarations skipped consistency checking between unannotated and expected sites. Added 2 regression unit tests in `tests/test_docsync_declarations.py`.
  - F-DOCSYNC-10: Hardened `scripts/docsync/integrity.py:_check_section3_next_wp` to inspect Section 3 for unlabelled `NEXT_WP_CLAIM_RE` matches when `claimed is None`, preventing silent bypass of DOC007 next-action integrity checks. Enforced canonical `- **Next action:**` bullet label in `PLAYBOOK.md` Section 3. Added regression test `test_doc007_section3_unlabelled_claim_blocks` in `tests/test_docsync_integrity.py`.
  - Updated `tests/scripts/dev/test_worktree_guard_playbook.py` `test_the_repository_playbook_parses` to reflect the active authorized worktree branch `test`.
- Validation: `pytest -q` -- **918 passed**, 5 warnings. All 296 docsync tests pass. `python scripts/doc_state_sync.py --check` exits 0 with no integrity errors.
- Forward guidance: resume owner-review remediation Task 6 (accessibility pass) per `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md` before WP-5 begins.

### 2026-09-05 - Add resilient Typekit fallback font stacks, consolidate single-row mobile navigation, and configure editor (side-task)

- Scope: resolved unknown at-rule IDE lint warning on `@custom-variant` in `static/css/tailwind.src.css`, verified Typekit web font integration, reinforced design token font stacks with resilient Typekit fallbacks (`aktiv-grotesk`, `corporate-a`, `ff-din-paneuropean`, `orator-std`), and consolidated mobile header navigation to a unified single-row bar.
- Implementation:
  - Added `.vscode/settings.json` configuring `"css.lint.unknownAtRules": "ignore"` and created `.vscode/tailwind-css-data.json` declaring Tailwind v4 at-rules (`@custom-variant`, `@theme`, `@source`, `@utility`, `@plugin`). Kept git status clean as `.vscode/` is in `.gitignore`.
  - Verified live Adobe Typekit kit (`rwy8ghw`) served by `templates/base.html` and expanded font stacks in `static/css/tailwind.src.css` and `static/css/global.css`: `--font-sans` now includes `"aktiv-grotesk"`, `--font-serif` includes `"corporate-a"`, `--font-figure` includes `"ff-din-paneuropean"` (FF DIN), and `--font-mono` / `--font-mono-narrow` include `"orator-std"`.
  - Consolidated mobile header navigation in `static/css/shell.css` from a dual-row 2x2 grid (`--shell-height: 6.5rem`) to a unified single-row 4-column stack (`--shell-height: 4.25rem`, `grid-template-columns: repeat(4, minmax(0, 1fr))`). Provenance & design rationale: opting for a one-stack bar rather than dual-row saves ~36px of vertical fold space on compact mobile viewports (320px–390px), avoids visual crowding now that the theme toggle sits below page content (F-B21-45), comfortably fits all 4 short route labels ("Index", "Heatmap", "Results", "Unmatched") at compliant >=44px tap targets, and unifies the shell height floor with desktop (`4.25rem`).
  - Synchronized `scripts/dev/frontend_gate.py` (`check_shell_scales_with_text` and `check_large_display_scale_parity` row count assertion to 1 row), updated design token regression lock in `tests/scripts/dev/test_tailwind_build_cli.py`, and rebuilt `static/css/tailwind.css` cleanly.
- Validation: `pytest -q` -- **914 passed**, 5 warnings. `python scripts/dev/tailwind_build.py --check` and `pre-commit run --all-files` passed cleanly with 0 drift and all hooks green.

### 2026-09-05 - Harden and polish frontend interfaces, align legacy Bootstrap styles, and mute index divider seam (side-task)

- Scope: executed comprehensive frontend hardening (/harden) and polish (/polish) passes across the application, aligned legacy Bootstrap pages (`results.html`, `unmatched.html`) with the Tailwind design system, and muted the index vertical dividing seam.
- Implementation:
  - Added `@media (prefers-reduced-motion: reduce)` overrides to `static/css/global.css` for card and SVG entrance animations (`opacity: 1 !important`, `animation: none !important`) and collapsed button transitions (`0.01ms !important`).
  - Added form submission resilience and double-submit guards to `static/js/index.js` (disabling `#submit-btn` and setting `aria-busy="true"`, with `pageshow` restoration) and `static/js/heatmap.js` (disabling `#heatmap-submit-btn` during active jobs).
  - Wired accessibility and defensive attributes: added `maxlength="100"` to Last.fm username inputs on both modes, bound `aria-describedby="year-hint"` to `#year`, and dynamically synchronized `role="alert"`, `aria-invalid="true"`, and `aria-describedby` across inline error and warning states in `static/js/index.js`.
  - Hardened layout against text overflow in `static/css/results.css` (`flex-shrink: 0` on `.album-cover`, `min-width: 0` and `overflow-wrap: break-word` on `.album-title` and `.album-info`), `templates/results.html` (descriptive `alt="{{ album.album }} cover"` on cover art), and `static/css/unmatched.css` (`overflow-wrap: break-word` on table cells).
  - Reskinned Bootstrap pages in `static/css/global.css`, `static/css/results.css`, and `static/css/unmatched.css`: styled `.btn` variants with mono-narrow typography, uppercase tracking, 0.625rem radius, and brand purple accents (`--shell-accent`); applied Adobe Typekit serif to display headings (`h1`, `h2`); aligned dark palette variables to authentic warm obsidian (`#0e0c12`, `#181520`, `#1f1b29`, `#2a2434`, `#1a1622`).
  - Polished design system tokens and anti-patterns: eliminated resting drop shadows on `.album-cover`, `.reason-section`, and `.action-buttons` in favor of structural hairline borders; enforced the No-Medium Rule on `.album-link` (`font-weight: 400`); replaced inline style on cover placeholder with `.album-cover-placeholder`; promoted results heading to semantic `<h1>`; aligned `.reason-count` to pill radius and 0.75rem mono label.
  - Themed browser surfaces: added custom `::selection` background (`--info-bg` / `--ss-accent-soft`) and subtle hairline `scrollbar-color` across stylesheets.
  - Muted the index vertical dividing seam (`--ss-border-divider`) by ~8% towards adjoining surfaces (`#8a867e` light, `#68646f` dark) while strictly maintaining >= 3.0:1 WCAG non-text contrast against both adjoining surfaces (`check_divider_contrast`); synchronized `static/css/tailwind.src.css`, `static/css/tailwind.css`, `.docsync.toml`, and `tests/test_template_shell.py`.
- Validation: `pytest -q` -- **914 passed**, 5 warnings. `python scripts/dev/tailwind_build.py --check` and `python scripts/doc_state_sync.py --check` pass. Live browser execution verified in Chromium and Firefox with 0 console errors and clean contrast checks.

### 2026-09-05 - Soften high-res desktop scale slope, standardize unmatched empty state, and polish warm light surface

- Scope: owner review of 1440p desktop render identified excessive vertical growth in the index card composition. Standardized the `/unmatched` empty state to match `/results` and `/heatmap`, unified the light-mode surface on warm `#fcfbf8`, and elevated the semantic heatmap headline.
- Plan vs implementation:
  - Added `@media (min-width: 1920px)` in `static/css/index.css` applying a softened slope curve `0.35 + 0.65 * (W / 1920)` above 1080p, reducing 1440p card height from 907px to 828px and 4K card height from 1358px to 1121px while strictly maintaining 1080p scale at 1.075.
  - Standardized `/unmatched` empty state via `templates/unmatched_empty.html` with `.empty-page` and `.empty-state` centered typography, purple signal bar, and primary action button; updated `scrobblescope/routes.py` and test suites.
  - Replaced stark `#ffffff` with warm `#fcfbf8` across `--ss-surface-card` in `static/css/tailwind.src.css` and rebuilt `static/css/tailwind.css`.
  - Promoted heatmap result headline to semantic `<h1>` in `templates/partials/_heatmap_result.html` and elevated desktop font size to `clamp(1.625rem, 3.75vw, 2.5rem)` (40px) while preserving neutral weight and color for usernames.
  - Updated `scripts/dev/frontend_gate.py` scale parity calculations to reflect softened curve and column-tracking wordmark geometry.
- Validation: `pytest -q` -- **914 passed**, 5 warnings. `python scripts/dev/frontend_gate.py` passed all 23 checks in 64 runs across Chromium and Firefox (desktop, mobile, wide touch). `python scripts/dev/tailwind_build.py --check` and `python scripts/doc_state_sync.py --check` pass.

### 2026-09-05 - Move the mobile theme control below page content (side-task)

- Scope: owner review found that the compact horizontal Light/Dark control sat
  midway across the two navigation rows. Its boxes did not intersect, but the
  control visually competed with both rows and made the header read as
  overlapping.
- Implementation: retain one checkbox and label, then move their actions
  wrapper between the desktop header and a mobile slot after page content via
  the existing `859.98px` breakpoint. The four-link grid now uses the full
  mobile header width. Selector scope follows the wrapper so the hidden input,
  selected state, and focus ring survive relocation on migrated and legacy
  pages.
- TDD evidence: the new rendered check failed in Chromium and Firefox at both
  390px and 320px because the control remained in the header and above page
  content. The focused gate passes after relocation and also checks the 44px
  target, two-row navigation, overflow, and body offset.
- Findings: F-B21-45 now records the owner correction and final placement.
- Validation: `pytest -q` -- **904 passed**, 5 warnings. Focused shell and gate
  tests -- **129 passed**. The complete frontend gate reports `23 checks passed
  in 64 runs across chromium, firefox`; JavaScript syntax and diff checks pass.
  All pre-commit hooks pass, including `doc-state-sync-check`; the alignment
  hook reports the expected WT003/WT010 state on the owner-authorized stacked
  Task 4 branch.
- Forward guidance: complete Task 4 review, then proceed to Task 5.

### 2026-09-05 - Refine desktop scale and mobile navigation (side-task)

- Scope: address the owner's final Task 3/4 visual comparison. The 28rem form
  felt slightly too large, its top-anchored composition accumulated much more
  space beneath the card on a realistic 1440p window than at 1080p, the mobile
  header hid report destinations behind horizontal scrolling, and the desktop
  Heatmap result remained at the snapshot's undersized 1100px measure. The
  Heatmap username also carried an unwanted purple italic accent.
- Implementation: refine the form base cap to `27.5rem` and centre its complete
  composition vertically in the available desktop well. Auto margins collapse
  when expanded rows need the space, preserving top padding and natural
  document scroll without state-dependent scaling. Mobile navigation now uses
  two directly visible rows beside a compact theme control. The desktop
  Heatmap stage uses `84vw`, capped at `120rem`, while the username inherits
  the headline's neutral serif treatment.
- TDD evidence: before the CSS changes, both engines measured unequal form
  composition gutters at every realistic desktop profile; 390px and 320px
  headers required horizontal navigation scrolling and exposed only one row;
  and a 1920x945 Heatmap result occupied 57.3% of the viewport with 16.6px
  rendered cells. The extended gate now asserts balanced vertical gutters,
  unchanged expanded-state geometry, two directly visible mobile nav rows,
  a centred Heatmap frame occupying at least 70% of the viewport, 22px-32px
  rendered cells, and a neutral username. The complete frontend gate passes
  all 23 checks in 64 runs across Chromium and Firefox.
- Findings: F-B21-44 records the desktop Heatmap scale and username treatment;
  F-B21-45 records mobile navigation overflow; F-B21-46 records the desktop
  form's top-heavy placement and cap refinement.
- Forward guidance: complete Task 4 review, then proceed to Task 5.

### 2026-09-05 - Remove the cached Heatmap loading flash (side-task)

- Scope: address the owner-observed flash when the Heatmap header link restores
  an already-complete saved job. The client exposed the loading panel before
  its first progress response, then immediately replaced it with cached data.
- Implementation: keep saved-job loading hidden through the first progress and
  data requests. Reveal it only when the response shows ongoing work, a retry,
  or an error; otherwise fade the complete result in directly. Normal Heatmap
  submissions and their polling lifecycle remain distinct and unchanged.
- TDD evidence: the new mutation observer failed against the prior client in
  Chromium and Firefox even though the final result DOM was correct. It starts
  before production `DOMContentLoaded` handlers, so it records the transient
  loading paint rather than sampling only the settled page.
- Findings: F-B21-43 records the defect and its resolution.
- Validation: `pytest -q` -- **904 passed**, 5 warnings. Focused frontend and
  route tests -- **120 passed**. The complete frontend gate reports `23 checks
  passed in 64 runs across chromium, firefox`; JavaScript syntax and diff checks
  pass. Final hooks and docsync follow before commit.
- Forward guidance: complete Task 4 review, then proceed to Task 5.

### 2026-09-05 - Pin index state geometry and normalize its fades (side-task)

- Scope: address owner review after Task 3. The state-sensitive height
  denominator made a fixed 1920x945 window shrink the 481.6px form to 390.5px
  for a release field, 357.8px for thresholds, and 325.2px when both were
  open; the hero and every scale-authored dimension changed with it. Mode-copy
  motion also ran sequential 110ms and 180ms animations while page entrance
  took 1.2s after a 0.2s delay and Heatmap stage fades took 300ms.
- Implementation: removed the three reachable-state height overrides. The
  fixed window alone now selects `--index-scale`; opening rows adds natural
  document height. A stable root scrollbar gutter prevents Firefox's first
  scrollbar from shifting the 3fr/4fr columns. Both hero descriptions reserve
  one overlaid grid track, expose the active copy with `aria-hidden`, and
  crossfade concurrently. Index entrance, hero copy, and Heatmap stage opacity
  changes now use one 180ms duration with an immediate reduced-motion state.
- TDD evidence: the pre-fix browser run failed in both engines and reported
  every changed form, hero, type, spacing, and control dimension plus the
  expanded state's missing document scroll. The permanent gate now drives six
  states at the realistic 1920x945 content box and compares representative
  rendered dimensions. An adversarial unit test proves material and missing
  measurements fail; a route test pins the stable hero-copy structure.
- Review cleanup: replaced the one implicit string concatenation called out on
  PR #225 and corrected Task 3's stale illustrative commit ID from `c1f10e6`
  to the actual `8b37566`.
- Findings: F-B21-41 records the state-dependent resize and F-B21-42 records
  the inconsistent motion. F-B21-38 now identifies its state-sensitive
  implementation as superseded.
- Validation after stacking on the Task 4 branch: `pytest -q` -- **904 passed**,
  5 warnings. The complete frontend gate reports `23 checks passed in 64 runs
  across chromium, firefox`; hooks and final docsync follow before commit.
- Forward guidance: correct the cached-Heatmap restoration flash on PR #226
  with the loading-progress work, then complete Task 4 review.

### 2026-09-05 - Close out the Task 4 session and stack its PR (side-task)

- Scope: session close-out after Task 4's implementation pass. Corrected the
  dangling pre-amend commit reference (`21b5198` -> `e0219b2`) in Section 3,
  in the Task 4 entry's forward guidance, and in the plan's Task 4 checkpoint
  -- a commit cannot contain its own SHA, so SHA references land after the
  commit they name. Added the dated handoff document
  `docs/superpowers/handoffs/2026-09-05-batch21-task-4-review-handoff.md`.
- Plan vs implementation: as intended by the owner's close-out instruction.
  Task 4's commit and this handoff are published on the stacked branch
  `wip/batch-21-task-4` (base `wip/batch-21`) so PR #225 stays scoped to
  Task 3; local `wip/batch-21` is intentionally ahead of its origin until
  PR #225 merges and the WT004 realign ritual runs.
- Deviations: none of record; the implementer's amend-within-its-own-pass
  produced the dangling SHA this entry corrects.
- Validation: `pytest -q` -- **902 passed** (unchanged by this docs-only
  commit). `pre-commit run --all-files` -- all hooks pass.
  `doc_state_sync.py --check` -- exit 0 (expected root-definition warning).
- Forward guidance: the next session reviews Task 4 (SDD task review, then
  fix loop if needed), then Tasks 5 and 6 per the plan; the handoff doc is
  the map. PR #225 (Task 3) remains draft awaiting owner review.

### 2026-09-05 - Align loading signals with pipeline phases (side-task)

- Scope: Task 4 of the Batch 21 owner-review remediation plan. Align visible
  loading progress with pipeline phases for both Top Albums and Heatmap clients,
  eliminate overlapping interval polls and stale out-of-order response application
  (F-B21-33), decouple received vs attempted Last.fm counts, and implement loading
  composition corrections (F-B21-36).
- Plan vs implementation:
  - Repository layer: Added `_UNSET` sentinel to `set_job_progress` for `phase`,
    allowing progress/message updates without clobbering an active phase; updated
    `set_job_error` to clear `phase=None`; isolated phase dicts in
    `get_job_progress` and `get_job_context` via `copy.deepcopy` to prevent caller
    or internal mutations from leaking across boundaries.
  - Route layer: `/progress` returns `phase` when present in progress dictionary.
  - Orchestrator and services: Emitted explicit `lastfm_fetch`, `spotify_search`,
    and `spotify_details` phases with unit, current, total counts in `orchestrator.py`
    and `heatmap.py`. Updated `lastfm.py` to decouple received vs attempted pages via
    `pages_received`. Cleared `phase=None` on uncounted states (initialization,
    counting, filtering, error, 100% completion).
  - Browser helper (`static/js/loading-progress.js`): Non-module global
    `window.ScrobbleProgress` providing `displayPercent(payload)`, `label(payload)`,
    and `update(options)`. Manages instant bar reset on phase change, ARIA attributes
    (`aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext`), and
    formatted phase lines.
  - Polling clients: Integrated `ScrobbleProgress` into `loading.js` and `heatmap.js`.
    Added `pollInFlight`, `pollSeq`, and `latestAppliedPollSeq` to drop out-of-order or
    stale responses and prevent overlapping interval fetches.
  - Loading composition: Removed duplicate phase sentence `<p class="heatmap-loading__detail">`
    and `<li>rocket scale</li>` in `_heatmap_loading_details.html`. Styled stat items in
    flex container with centering, 18rem max-width, and divider rules
    (`:not(.hidden) ~ :not(.hidden)`). Added `@keyframes wait-fade-in` (200ms ease-out)
    with `@media (prefers-reduced-motion: reduce)` cancellation restoring `opacity: 1`.
  - Frontend gate: Added unit tests for new gate helpers (`_parse_matrix_scalex`,
    `_assert_loading_progress_state`) in `test_frontend_gate.py`. Implemented
    `_exercise_loading_progress_phases` testing sequential frames, zero totals,
    100% phase without result navigation, flex centering, and stale response rejection
    across Chromium and Firefox.
- Deviations: none. All requirements from the task brief implemented strictly.
- Validation: `pytest -q` -- **902 passed**, 5 warnings (8 new tests across
  test_repositories, test_routes, test_orchestrator, test_heatmap, test_lastfm_service,
  test_frontend_gate). Frontend gate: `23 checks passed in 64 runs across chromium,
  firefox`. Prohibited animation sweep (`rg -n 'transition:\s*(width|height|padding|margin|max-width)' static\css static\js`)
  returned 0 matches.
- Forward guidance: Task 4 implemented and validated locally in commit e0219b2;
  awaiting task review (spec and quality review is pending as the next action,
  followed by Task 5 per the plan order).

### 2026-09-05 - Remediate Task 3 review feedback, fill the hero to its column (side-task)

- Scope: fix round 2/5 for Task 3 owner-review feedback (not a FINDINGS
  entry -- rendered-evidence feedback, not a review finding): "scale the
  wordmark and hero up to the edge". `.index-hero__inner`'s width (and the
  matching `.index-hero__mark` cap) were bound to `calc(35rem *
  var(--index-scale))`, which the owner's measured evidence showed
  rendering narrower than the padded hero column in every state -- most
  visibly in the height-guard-driven expanded state (decade selected,
  thresholds open), where the hero visibly shrank as the form grew.
- Plan vs implementation: replaced the `35rem * scale` basis on both
  `.index-hero__inner` (`width: 100%`) and `.index-hero__mark` (`max-width:
  100%`) inside the existing `@media (min-width: 1200px)` block, so hero
  content (wordmark, headline, lede, capability marks) fills to the
  padding edge in every state. The two rules stay identical twins, as they
  were before this change (both previously read the same `35rem * scale`
  value), so wordmark width keeps tracking hero-inner width exactly with no
  separate rule needed. Nothing below 1200px, the hero's own padding
  (`3.5rem * scale`), the lede's `38ch` measure, the form side (3fr 4fr
  split, 28rem cap, height bounds), the header clamps, or either divider
  token was touched, per the owner's explicit "do not touch" list.
- TDD evidence: extended `check_large_display_scale_parity` in
  `scripts/dev/frontend_gate.py` (`measure_wide_layout` and
  `measure_compact_height`) to read the hero's own padding, its column
  width, `.index-hero__inner`'s rendered width, and `.index-hero__mark`'s
  rendered width, then assert hero-inner fills its padded column (within
  1px) and mark tracks inner (within 1px), across all four real windows
  (1080p, 1200p measured, 1440p, 4K) plus the driven decade+thresholds
  expanded state. A genuine RED run against the pre-fix CSS produced
  exactly 5 failures: hero inner at 602.0px against a 702.4px column
  (1080p and 1200p measured, same viewport width), 802.7px against 936.6px
  (1440p), 1204.0px against 1404.9px (4K), and 400.3px against 742.8px in
  the expanded state -- confirming the owner's diagnosis empirically (my
  own hand-derivation independently produced the same 602.0px and 702.4px
  figures before the browser run). No "mark not tracking inner" failures
  appeared even pre-fix, because the two rules were already numerically
  identical. Applying the CSS fix produced GREEN in both engines
  individually, then a full gate GREEN: `23 checks passed in 64 runs across
  chromium, firefox` (check count unchanged; this extends two existing
  measurement helpers rather than adding a new check).
- Validation: full-suite `pytest -q` -- **894 passed**, 5 warnings
  (unchanged; this is a gate-level browser-measurement change with no new
  pytest-collected unit test, since no new Python helper function was
  introduced -- the assertions read directly from browser-measured
  rectangles already exposed by the existing helpers). All pre-commit
  hooks and `doc_state_sync.py --check` passed on the final document
  state.
- Forward guidance: Task 3's remaining review rounds (3/5 through 5/5) and
  the seven parked Minor findings proceed separately; Task 4 remains the
  next batch-order item once Task 3's review is fully closed.

### 2026-09-05 - Remediate Task 3 review finding, raise the index well divider (side-task)

- Scope: fix round 1/5 for the Task 3 owner-review finding "the index
  page's own dividers were not raised, and the new check cannot see them".
  `.index-form`'s `border-left` drew from the shared, still-opaque
  `--ss-border-default` (measured ~1.12:1 light, ~1.18:1 dark against its
  adjoining surfaces), which Task 3's `--shell-border` fix never touched.
  Owner ruling: add a dedicated index-only divider token rather than
  restyling the other 14 `--ss-border-default` uses in `index.css`.
- Plan vs implementation: added `--ss-border-divider` (`#858179` light,
  `#6e6a75` dark) to both daisyUI theme blocks in
  `static/css/tailwind.src.css`, applied only to `.index-form`'s
  `border-left` in `static/css/index.css`, and regenerated
  `static/css/tailwind.css` with the qualified `tailwind_build.py` (this
  time producing a genuine 3-line diff, since the token is new -- unlike
  Task 3, where the same build produced no drift). `check_divider_contrast`
  in `scripts/dev/frontend_gate.py` now also reads `.index-form`'s real
  rendered `border-left-color` against `--color-base-100` and
  `--ss-surface-sunken` in both themes and engines, reusing the existing
  minimum-across-surfaces helper. `_divider_contrast_failure` gained a
  `token` parameter (default `--shell-border`, preserving every existing
  call site) so the new failure message names `--ss-border-divider`
  instead of misattributing it.
- TDD evidence: a genuine RED run against the pre-fix CSS (extended gate
  assertion in place, `.index-form` still on `--ss-border-default`)
  produced exactly 4 failures -- index divider light/dark in both
  Chromium and Firefox, reporting `1.12:1` and `1.18:1`, matching the
  reviewer's hand-computed ratios exactly. Applying the CSS fix produced a
  genuine GREEN run: `23 checks passed in 64 runs across chromium,
  firefox` (check count unchanged; this extends an existing check rather
  than adding a new one).
- Measured divider contrast (both engines agreed): light vs page
  3.65:1, vs sunken well 3.26:1 (binding); dark vs page 3.69:1, vs sunken
  well 3.37:1 (binding). Both clear the 3:1 floor with comparable headroom
  to Task 3's shell-border ratios.
- Test additions: `--ss-border-divider` added to `INDEX_TOKENS` in
  `tests/test_template_shell.py` (covered by the existing parametrized
  token-build test, no new test function needed). One new adversarial unit
  test in `tests/scripts/dev/test_frontend_gate.py` asserting
  `_divider_contrast_failure`'s `token` parameter is honoured and that the
  default stays `--shell-border` for existing callers. A new
  `.docsync.toml` pair of `[[value]]` declarations pins the token's light
  and dark values across `tailwind.src.css` (both theme blocks) and
  `tests/test_template_shell.py`.
- Validation: full-suite `pytest -q` -- **894 passed**, 5 warnings (892
  baseline plus the 2 new tests above). The complete frontend gate passed
  23 checks in 64 runs across Chromium and Firefox. All pre-commit hooks
  and `doc_state_sync.py --check` passed on the final document state.
- Forward guidance: FINDINGS.md F-B21-40 records this defect and its
  resolution. Task 3's broader remaining review rounds (2/5 through 5/5)
  and the seven parked Minor findings are unaffected and proceed
  separately; Task 4 remains the next batch-order item once Task 3's
  review is fully closed.

### 2026-09-05 - Implement remediation Task 3, widen composition and raise divider contrast (side-task)

- Scope: land the final desktop index composition and divider-contrast fix
  from the canonical remediation plan. Widen `static/css/index.css`'s
  `min-width: 1200px` split from `3fr 5fr` to `3fr 4fr` and raise the form's
  unscaled base cap from `23.75rem` to `28rem` (both scaled by the shared
  `--index-scale` factor). Raise `static/css/shell.css`'s `--shell-border`
  alpha in both themes so the composited divider clears 3:1 against every
  adjacent surface, and apply the recorded header ruling: a
  `--shell-height: clamp(4.25rem, 2.96875vw, 4.75rem)` bar, a shared
  `--shell-control-gap: 0.75rem` token on `.site-header` and
  `.site-header__nav`, and matching size clamps on the nav link and theme
  controls.
- Plan vs implementation: `check_large_display_scale_parity` in
  `scripts/dev/frontend_gate.py` gained a divider-contrast check (the
  composited colour, not the token string), ruled header-geometry
  assertions at real 1080p/1440p windows, and zoom/transform prohibitions on
  the form wrapper; the retuned split and form-cap assertions replaced the
  Task 2 originals in place, matching the plan's instruction not to leave
  the old assertions standing. A genuine RED run against the pre-fix CSS
  produced 28 failures (14 per engine, both Chromium and Firefox): divider
  contrast (1.27:1 light, 1.40:1 dark), the 5:3 split, the 23.75rem-based
  form cap at 1080p/1440p/4K, the unruled 76px header bar and 48px/116px
  nav-link geometry, the 48.4px theme control, and mismatched header/nav
  gap tokens. Applying the CSS produced a genuine GREEN run: `23 checks
  passed in 64 runs across chromium, firefox`. Mutation-checks confirmed the
  zoom and transform prohibitions are load-bearing: temporarily adding
  `zoom: 1.1` and then `transform: scale(1.1)` to `.index-form__inner` each
  reproduced the gate failure; both were reverted before commit.
- Measured divider contrast: light `rgba(26, 24, 32, 0.5)` composites to
  3.23:1 against the light surface token (worst adjacent case, up from
  1.27:1); dark `rgba(241, 237, 228, 0.4)` composites to 3.42:1 (up from
  1.40:1). Both clear the 3:1 floor with headroom.
- Test additions: 7 adversarial unit tests in
  `tests/scripts/dev/test_frontend_gate.py` for the new colour-math helpers
  (`_parse_rgb_string`, `_composite_over`, `_relative_luminance`,
  `_contrast_ratio`, `_worst_divider_contrast`, `_divider_contrast_failure`,
  `_clamp_px`), including an exact-3.0-passes/2.9999-fails boundary case;
  the existing wrapped-headline test was updated for the new per-width
  `_headline_wrap_failures(probe, width)` signature (1200, 1500, 1920,
  2560px, both modes). 4 source-level tests were added to
  `tests/test_template_shell.py` for the shared control-gap token, the
  `--shell-height` clamp, the nav-link/theme-control size clamps, and the
  new divider alphas.
- Deviations: a background gate run was started immediately after the CSS
  was already in its final (GREEN) state, before any genuine RED evidence
  had been captured -- a TDD-ordering slip. Corrected before proceeding:
  `git stash push --keep-index` reverted only the two CSS files to their
  pre-fix state while keeping the new gate assertions in the working tree,
  the RED run above was captured against that state, then `git stash pop`
  restored the GREEN CSS and the gate was re-run clean. No code was
  rewritten; only the evidence-capture order was corrected.
- Validation: `pytest -q tests/scripts/dev/test_frontend_gate.py` --
  **31 passed**; `pytest -q tests/test_template_shell.py` -- **93 passed**;
  full-suite `pytest -q` -- **892 passed**, 5 warnings (881 baseline plus
  the 11 new tests above). The complete frontend gate passed 23 checks in
  64 runs across Chromium and Firefox. All pre-commit hooks and
  `doc_state_sync.py --check` passed on the final document state.
- Forward guidance: Task 4 (align visible loading progress with pipeline
  phases) is next per the canonical plan. Tasks 5 and 6 remain open. PR #224
  (Task 2) merged; PLAYBOOK Section 3 corrected the stale "awaits owner
  review" framing.

### 2026-09-05 - Close PR #224 complexity follow-up (side-task)

- Scope: address Qlty's fresh analysis of the first Task 2 review-fix commit.
  The shared font expression and browser closure findings cleared, while the
  desktop-boundary helper remained one point over its complexity threshold.
- Review remediation: extracted the headline-wrap branch into a focused helper
  and exercised that helper directly through the existing adversarial boundary
  test. This removes nested control flow from the browser orchestration without
  changing its rendered assertions.
- Validation: focused frontend-gate tests passed **24 tests**; `pytest -q` --
  **881 passed**, 5 warnings. The complete gate passed 22 checks in 62 runs
  across Chromium and Firefox. All pre-commit hooks and docsync passed on the
  final document state.
- Forward guidance: await the refreshed Qlty and Quality Gate checks on PR
  #224. Task 3 remains next after owner review.
