# PLAYBOOK Execution Log Archive

Purpose:
- Store dated execution-log entries rotated out of `PLAYBOOK.md` Section 4.
- Keep entries in reverse-chronological order (newest first).

Read helpers:
- `Get-Content docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "<keyword>" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

### 2026-09-01 - Owner-review remediation consolidated (side-task)

- Scope: consolidate the owner-review remediation in one plan and correct the
  active Batch 21 records that described unshipped index behavior as present.
- Evidence: `BATCH21_DEFINITION.md` and `docs/design/RECONCILIATION.md`
  claimed that the form filled its well, while current `static/css/index.css`
  retains its `23.75rem` cap. `FINDINGS.md` also marked the broader refinement
  resolved even though the owner-confirmed remaining work has not shipped.
- Disposition: the **Owner Review Remediation Implementation Plan** (2026-09-01)
  is the sole comprehensive future-work specification. It treats the source
  scale formula as unproven because owner Firefox evidence does not show the
  intended rendered scaling, and adds the required 1080p test of the 1440p
  header-density candidate. Active records refer to it without claiming its
  changes are implemented. Dated history remains unchanged.
- Follow-up: the final annotation review confirmed that the intended shared
  scaling is not implemented. The plan and active Batch 21 records now state
  that source code is not acceptance evidence; Firefox rendering must prove
  the composition before the work can be marked complete. No product code,
  staging, commit, or push occurred in this planning pass.

### 2026-08-29 - Unmatched zero state corrected (side-task)

- Scope: remove the contradiction where the unmatched page says albums were
  excluded and immediately reports a total of zero.
- Implementation: use the existing `total_count` condition in the template.
  A zero count now states that there are no unmatched albums to review while
  retaining the search settings and results navigation. The populated report,
  reason tables, and filter facts are unchanged.
- TDD: the route-backed zero-payload render test failed against the prior
  claim and now protects the empty copy, omitted populated-report copy, and
  results navigation. The populated report test remains green.
- Validation: focused route and template checks -- **91 passed**. Full
  `pytest -q` -- **871 passed**, 5 existing warnings. `doc_state_sync.py
  --check` and all pre-commit hooks pass.
- Forward guidance: this is not a data-pipeline fix. Keep `/unmatched` and
  `/api/unmatched` semantics unchanged for WP-7's separate backend work.

### 2026-08-29 - Wide index form and shell rhythm corrected (side-task)

- Scope: correct the wide form that grows beyond its shared composition and
  give the desktop navigation breathable, uniform control spacing.
- Implementation: wide layouts no longer remove the form's 23.75rem cap, so
  the existing 1.075-to-2.15 composition scale controls the card and its
  fields together. The well's inline padding is symmetric and the form stays
  centred. Desktop shell height is 4.75rem; page links and the theme control
  are 48px tall with one 0.75rem sibling gap. Mobile retains its compact
  shell rules.
- TDD and validation: the rendered frontend check failed before the CSS
  change: 1920px, 2560px, and 3840px form widths were 1099px, 1499px, and
  2299px instead of the shared-scale caps, and their gutters were unequal.
  It now reports 22 checks passed in 31 runs across desktop, mobile, and wide
  touch. Full `pytest -q` -- **870 passed**, 5 existing warnings.
- Forward guidance: keep the header outside the wide composition scale; it
  must remain an independently readable global control strip.

### 2026-08-28 - Cached Heatmap loading handoff clarified (side-task)

- Scope: repair the owner-reported cached Heatmap result snap, redundant
  loading signals, and misleading normal-state return control without
  changing worker cancellation semantics.
- Implementation: the backend still reports real progress, but phase text now
  says `Reading your Last.fm history...` while `Pages fetched` owns its only
  visible fraction. Both fills use `scaleX` rather than layout-width
  animation. The Heatmap renders its complete DOM, then lets the loader paint
  for two frames before one 300ms root opacity handoff. Reduced motion skips
  that handoff. Both workflows now say `Cancel and return home`; each only
  navigates home.
- TDD and validation: the new service and browser-gate assertions failed
  before the implementation because both workflows still emitted counted
  phase text, used a layout fill, lacked the named return control, and the
  cached result had no root-handoff state. Focused tests -- **17 passed**.
  Full `pytest -q` -- **870 passed**, 5 existing warnings. The frontend gate
  reports 22 checks passed in 31 runs, including the warm-cache handoff.
- Forward guidance: deploy this with the existing private-profile and index
  motion fixes. It deliberately does not claim or implement worker
  cancellation.

### 2026-08-28 - Index page-entry fade restored (side-task)

- Scope: restore the Home destination entrance lost when the Tailwind index
  stopped loading the legacy page stylesheet.
- Implementation: the complete index composition now fades from opacity zero
  over 1.2 seconds after a 0.2-second delay. It does not move or resize, and
  the existing light/dark mode transition is unchanged. Reduced-motion readers
  receive the visible final state without an animation.
- Validation: full `pytest -q` -- **870 passed**, 5 existing warnings. The
  frontend gate reports 22 checks passed in 31 runs, including the
  computed-style check in standard and reduced-motion modes.

### 2026-08-28 - Private Last.fm profiles are blocked before jobs start (side-task)

- Scope: stop index submissions for profiles that hide their recent listening,
  rather than reporting a misleading empty result after a job starts.
- Implementation: preflight `user.getrecenttracks` with a one-item request;
  Last.fm's 403/error-17 verdict blocks both index modes in the browser and
  both loading routes on the server. Public accounts with an empty history
  remain eligible.
- Validation: focused service and route tests -- **92 passed**, 5 existing
  warnings. Full `pytest -q` -- **870 passed**, 5 existing warnings. The
  frontend gate reports 21 checks passed in 30 runs, including both forms
  against the same private-profile response.

### 2026-08-28 - Index entrance-motion regression filed (side-task)

- Scope: compared the deployed index, the locally served primary checkout,
  the active PR #220 worktree, source history, computed browser styles, and
  production asset identities after the owner reported a large regression.
- Finding: filed F-B21-26 as P0. The Tailwind index opts out of `global.css`,
  which owned the old card and logo entrance fades, and no Tailwind-owned
  page-entry replacement exists. PR #220's mode-copy cross-fade is separate
  and does not restore the page-entry behaviour.
- Deployment and font disposition: production serves the `1bf888f`
  `origin/main` assets from PR #218, not PR #220. The local server also ran
  the stale primary checkout. Deployed Adobe faces loaded successfully; the
  visible type-scale difference remains F-B21-24 and is corrected in the
  undeployed PR #220 calibration.
- Implementation: documentation only. No application code or deployment was
  changed; F-B21-26 owns the required motion restoration and browser check.

### 2026-08-28 - PR #220 timer-probe review remediated (side-task)

- Scope: audited the frontend pipeline probe after browser evidence showed its
  timeout patch was installed as an unevaluated arrow expression.
- Reproduction: invoking the same body as an IIFE sets a page marker. A page
  init script survives later navigations, so installing it on the shared
  profile page can also alter unrelated checks.
- Implementation: the pipeline state-machine check now runs on a disposable
  page, installs and verifies the invoked timeout patch there, and closes the
  page on both success and failure. The profile page remains clean for the
  later scale checks.
- Validation: focused frontend-gate unit tests -- **15 passed**. Full
  `pytest -q` -- **865 passed**, 3 warnings. The frontend gate reports
  20 checks passed in 29 runs across desktop, mobile, and wide touch.
  All pre-commit hooks and `doc_state_sync.py --check` pass.

### 2026-08-28 - Index width, scale, and small-text refinement (side-task)

- Scope: applied the owner-review amendment to the migrated Home composition
  without changing its content order, navigation, mode transition, or mobile
  layout.
- Implementation: desktop widths from 1200px use a `3fr 4fr` split, a 28rem
  form cap, and the existing shared `1.075` scale. A compact-height desktop
  rule reduces only the form column's outer padding. The small-label floor is
  12px, phrase-length capability text uses 0.04em tracking, and the light
  muted token is `#6c6676` in both framework paths.
- Contract: component sizes remain equal at 1920x1080, 2560x1440, and
  3840x2160; larger canvases change placement, not scale. The imported design
  snapshot remains untouched, with the amendment recorded in
  `docs/design/RECONCILIATION.md` and F-B21-24 resolved.
- Validation: focused template and build tests -- 100 passed. Full `pytest -q`
  -- **864 passed**, 3 warnings. The frontend gate reports 20 checks passed in
  29 runs across desktop, mobile, and wide touch. `doc_state_sync.py --check`
  passes.

### 2026-08-28 - Wide index gap tightened (side-task)

- Scope: corrected the oversized visual void between the scaled hero lockup
  and the form that remained after the proportional large-display repair.
- Implementation: the 1200px-and-wider composition now uses `3fr 5fr` rather
  than `3fr 4fr`. The shared viewport scale and the form's fixed physical
  gutters remain unchanged, so the lockup retains its 1080p, 1440p, and 4K
  scale while the form moves closer to it.
- Reproduction and validation: the browser gate first rejected the prior 4:3
  application-to-hero split, then passed with the new 5:3 split. A rendered
  1920x1080 inspection confirms the reduced visual gap without compressing
  the wordmark or removing header navigation.

### 2026-08-28 - Proportional large-display scale restored (side-task)

- Scope: corrected the index scale regression reported from 2560x1440 local
  browser captures. The previous rule retained a fixed `1.075` zoom and a
  28rem form cap at every desktop size, leaving a large inactive canvas on
  high-resolution displays.
- Implementation: at 1200px and wider, the hero and form calculate one shared
  CSS-viewport factor: `1.075 × max(1, min(viewportWidth / 1920,
  viewportHeight / 1080))`, capped at `2.15`. The form now fills the right
  well to its existing 2.75rem / 3.5rem physical gutters. Navigation remains
  shell-sized; compact-height and mobile rules are unchanged.
- Reproduction and validation: the large-display browser check initially
  failed at 1440p and 4K because both compositions remained at `1.075` and
  the form missed its fixed gutters. It now passes at 1920x1080, 2560x1440,
  and 3840x2160. Browser inspection at 2560x1440 confirmed the `1.433` scale,
  an 803px wordmark, the fixed form gutters, and all four navigation links.
  The full suite reports **865 passed**, 3 warnings, and the frontend gate
  reports 20 checks passed in 29 runs across desktop, mobile, and wide touch.

### 2026-08-27 - PR #220 Graphify findings audited and gate cleanup hardened (side-task)

- Scope: checked every open Codex and Graphify review thread on PR #220
  against current source, callers, tests, Git history, and browser behaviour.
- Review disposition: the five Codex findings are already addressed. The
  thirteen inline Graphify coupling notices are duplicated metrics rather
  than defects. Graphify's missing `logging` import, advisory-exit, result
  redirect, and unmatched-route claims are disproved or deliberate contracts.
  Two cleanup findings were valid: failed frontend-gate setup could leak its
  temporary jobs and routes, and a failed blocked-storage probe could leave
  its browser context open. Concurrent in-process gate contexts could also
  overwrite the shared fixture state.
- Implementation: `serve_app` now serialises its temporary global fixture,
  restores prior state, and cleans jobs, routes, sockets, and threads even
  when application or server setup fails. The blocked-storage context now
  enters its cleanup boundary before either probe setup call.
- Validation: focused frontend-gate unit tests -- 14 passed. `pytest -q` --
  **864 passed**, 3 warnings. The frontend gate reports 20 checks passed in
  29 runs across desktop, mobile, and wide touch.

### 2026-08-27 - Fresh heatmap starts separated from saved destinations (side-task)

- Scope: made Home's Heatmap selector start a new run while the header Heatmap
  and Results destinations continue to reopen the latest valid browser-session
  jobs. Added dedicated empty pages for those two destinations.
- Plan vs implementation: `/?mode=heatmap` now opens a fresh form without
  deleting the saved heatmap pointer. A successful start promotes the URL to
  `/heatmap`. Clean `/heatmap` and `/results` visits resume valid jobs or render
  `heatmap_empty.html` and `results_empty.html`; job access now runs expiry
  cleanup so the documented two-hour idle limit is enforced.
- UX and responsive behavior: the empty pages use one centered, shadow-free
  message group with a route-specific action. The Heatmap state retains a
  short rocket-scale gradient. Mobile actions keep the 44px touch minimum;
  large displays keep the established CSS-pixel scale instead of inflating
  controls independently.
- Deviations: the index selector does not clear the cached job. It ignores the
  pointer for the fresh form, because deletion would also remove the latest
  result that the header destination promises to restore. During live review,
  two stale Flask processes were found on port 5000; both were stopped and one
  current no-reload server was started from this worktree.
- Validation: the TDD red run reported 6 failed and 5 passed. `pytest -q` --
  **862 passed**, 3 warnings. The frontend gate reports 20 checks
  passed in 29 runs across desktop, mobile, and wide touch. Impeccable Detect
  reported no regex findings but was degraded because its optional HTML parser
  modules are unavailable; browser-computed checks provide the stronger UI
  evidence for this change.

### 2026-08-27 - Index mode-copy transition made interruptible (side-task)

- Scope: refined only the index hero copy swap between Top albums and Heatmap.
  The wordmark, shared capability line, form layout, routes, and pipeline
  behaviour are unchanged.
- Implementation: replaced the fixed-delay class swap with cancellable Web
  Animations. The current copy exits in 110 ms, the selected copy enters in
  180 ms, and a new click cancels stale motion before it can win. Reduced-motion
  users and browsers without Web Animations receive an immediate swap.
- Visual evidence: the live browser held the wordmark at `(56, 124)` through
  both modes. A rapid album-heatmap-album sequence settled on the album URL,
  selected tab, copy, opacity, and visibility together.
- Validation: `pytest -q` -- **840 passed**, 3 warnings. Frontend gate --
  19 checks passed in 27 runs across desktop, mobile, and wide touch. All
  pre-commit hooks passed, including compiled-CSS drift and worktree alignment;
  `doc_state_sync.py --check` passed with only the expected active-root warning.

### 2026-08-26 - Canonical page navigation and routes added (side-task)

- Scope: implemented the owner-requested navigation prerequisite before the
  WP-4 loading rebuild. The shared header now offers Home, Results, Heatmap,
  and Unmatched in Input Mono Narrow, plus the segmented Light/Dark control.
  Loading stays transient and has no navigation pill.
- Plan vs implementation: added canonical `GET /loading`, `/results`,
  `/heatmap`, and `/unmatched` routes. New album jobs redirect to the loading
  URL and the loading script opens the results URL at completion. The old
  completion and unmatched POST routes remain compatibility shims during the
  strangler. Unmatched JSON moved to `GET /api/unmatched` so the page owns
  `/unmatched`.
- Deviations: direct Results and Unmatched visits without a job now render a
  friendly pre-search state with a Home action. Heatmap already falls back to
  its form. The owner renamed the prototype's Index pill to Home and removed
  Loading from the destination set.
- Validation: `pytest -q` **833 passed**, 3 warnings. The frontend gate
  reports 17 checks passed in 25 runs across desktop, mobile, and wide touch.
  JavaScript syntax checks and `doc_state_sync.py --check` pass.
- Forward guidance: WP-4 still owns the unified loading-page rebuild and the
  two pipeline state-machine checks in `BATCH21_DEFINITION.md`. Keep the
  canonical route and compatibility shims until the strangler retires them.

### 2026-08-26 - PR #220 review applied, and the theme fallback proved (side-task)

- Scope: remediated the three Codex comments on PR #220. All three were
  verified against the code before any fix; all three were valid.
- **The missing log entry** is the entry below this one, covering `9330ac8`,
  `ebb542b` and `6f8ff98`.
- **The `FINDINGS.md` header** attributed F-B21-21 and F-B21-22 to both WP-3
  and the owner review while omitting F-B21-23 and F-B21-24. Corrected in
  `12cfe25`.
- **`check_mark_follows_theme` was weak in two ways**, and both are closed. A
  part whose selector stopped matching read as null and was skipped, so
  re-cutting the asset would have retired the check silently. And the test
  was only that light differs from dark, so a wrapper wired to the wrong but
  theme-varying token passed. It now compares each mark against the resolved
  `--shell-ink` and `--shell-accent` for that theme, read through a probe
  element so the browser normalises `#1a1820` and `rgb(26, 24, 32)` to the
  same string. Mutation-checked: pointing the letterforms at
  `var(--shell-accent)` -- a wrong value that does vary by theme, which the
  old check accepted -- fails four times with the token named.
- **The uncommitted `base.html` theme fallback is real, and is now proved.**
  It was written on 2026-08-26 at 00:08 and left uncommitted when that
  session hit its spend limit mid-verification. Its own mutation check had
  passed on both the new and the reverted code, so it proved nothing: the
  harness never made storage actually throw. Rerun with `localStorage`
  genuinely throwing, the shipped version renders `light` on a dark system
  when site data is blocked, and the fix corrects it. A sixteenth gate check,
  `check_theme_survives_blocked_storage`, holds it; reverting the fix fails
  it by name. The check opens its own browser context, because blocked
  storage is installed as an init script and cannot be removed from the
  shared page afterwards.
- This does **not** close F-B21-22. A stored `'false'` still outranks the
  system preference forever; that needs the third state and an owner ruling.
- **A fourth comment arrived on the sweep after `3526edd`, and it was
  right.** The `worktree-alignment` hook shipped gating, documented as
  erroring only on WT002, WT007 and WT014. Eleven of the fifteen codes are
  errors: WT001, WT002, WT003, WT004, WT005, WT006, WT007, WT008, WT012,
  WT014, and WT009 inside a linked worktree. WT003 fires for any branch the
  active batch does not name and WT004 for the identical-tree divergence a
  rebase merge always leaves, so the gating version would have refused every
  commit on a feature branch and every commit after a merge until the branch
  was realigned. The claim came from grepping two of the guard's six modules
  and generalising -- the incomplete sweep the Anti-Pattern Registry names,
  committed inside a finding about mechanisms that hold in one place only.
- **The owner ruled the hook advisory on 2026-08-26.** The guard gained
  `--advisory`, which prints every diagnostic and always exits 0, and the
  hook uses it. The problem being solved was that the guard's output was
  invisible unless somebody ran it, not that commits needed a new gate. A
  test asserts `--advisory` exits 0 on an ERROR while the same run without
  the flag still exits 1; removing the short-circuit fails it.
- **F-B21-18 is scheduled**, by owner ruling the same day: the JavaScript
  unit-test seam becomes a work package of its own, sequenced before WP-5 and
  not folded into WP-4, scoped to the pure-function half on the existing
  Chromium. WP-5 and WP-7 are the remaining JavaScript-heavy pages, so a seam
  before WP-5 still guards work this batch does. The number it takes needs
  settling against DOC007 and the absorbed WP-6 before its first commit.
- **DOC012 is new, and it exists because this entry nearly lied.** The count
  authority reads `**823 passed**` and nothing else: written without the
  asterisks, the entry records nothing, an older entry stays authoritative,
  and `--check` exits 0 with every dashboard holding the previous number.
  That happened here -- the count was written unbolded, the figure did not
  move, and the gate stayed green. The owner ruled that bolding the line was
  the wrong fix, because the next agent will make the same mistake. DOC012
  now fails an execution-log entry that claims a pass result with no bold
  count anywhere in it. It is scoped per entry, not per line, so a subset
  claim beside a bold figure -- WP-1's "(35 passed)" for the toolchain
  module -- stays prose and history is not rewritten. Mutation-checked in
  both directions: neutering the check fails the first test, dropping the
  entry-scoping fails the second.
- Validation: `pytest -q` -- **826 passed**, all 12 hooks, docsync exit 0,
  frontend gate 17 checks in 25 runs. The suite grew by four: the
  `--advisory` exit contract and three DOC012 cases.

### 2026-08-26 - Deployed-merge review: wordmark theme fix and doc trim (side-task)

- Scope: the owner reviewed the deployed PR #218 merge and found two defects.
  This entry covers `9330ac8`, `ebb542b` and `6f8ff98`, which shipped without
  one. A PR #220 reviewer raised the omission; the entry is written here
  rather than by amending pushed commits.
- `9330ac8` trimmed the documents a session bootstraps from. SESSION_CONTEXT
  lost 35 lines: eight "Batch N complete" rows that restated the Section 2
  index one batch at a time, and a per-file test table that duplicated forty
  counts from the suite while only the total was gated. It had drifted three
  times during Batch 21, each drift a false fact in a bootstrap document, so
  the command that derives it replaced the table. Two `AGENTS.md` rules were
  restated as intent. AGENT_NOTES gained the wordmark typeface, Oblong
  Regular by WAPType, which took the owner about three hours to recover
  because the mark was converted to paths and no font reference survives in
  the asset. F-B21-21 and F-B21-22 were filed.
- `ebb542b` fixed F-B21-21. The index hero mark shipped with pure black
  letterforms on the `#0e0c12` dark page. Both wrappers include the same
  asset; it pins its own stroke and gives the letterforms no fill rule, so
  any wrapper `shell.css` does not name renders fixed-purple bars and
  user-agent black text, and only `.site-header__mark` was named. The gate
  gained its first check that reads a colour off an inline SVG.
- `6f8ff98` filed F-B21-23 and F-B21-24. F-B21-23 records that the assets
  diverge from the design contract, which specifies `currentColor`
  letterforms and `var(--bars-color)` bars; that divergence is the real
  cause of F-B21-21, which was fixed at the symptom. F-B21-24 rules that the
  index not growing past about 1400px is the contract working as written.
- Validation at the time: 822 tests, all hooks, docsync exit 0, and the
  Quality Gate green on `6f8ff98`.

### 2026-08-26 - Session-time enforcement added after the worktree retirement (side-task)

- Scope: the batch-21 worktree was retired on 2026-08-26. Reviewing how that
  went found that every gate in this repository runs at commit time and
  nothing runs at session time. Filed as F-B21-25 and partly closed here.
- What happened, from the branch reflog. `wip/batch21-doc-trim` was created
  from `origin/main` at 2026-08-25 21:57, took three commits, and was renamed
  to `wip/batch-21` at 2026-08-26 00:07. The rename only succeeds when the
  retained branch of that name is already deleted, and the push four seconds
  later replaced the remote. None of the three commits carried a Section 4
  entry, because the session treated the branch as a quick documentation trim
  rather than batch work, and nothing told it otherwise. A PR #220 reviewer
  raised it; the entry two above this one now covers that work.
- What changed:
  - **`worktree-alignment` is now a pre-commit hook.** The guard already
    exited 1 on an ERROR diagnostic and 0 otherwise, so it was built to gate
    and was simply never wired to one. Only WT002, WT007 and WT014 are
    errors; WT004 and WT010 are not, so the identical-tree state a rebase
    merge always leaves, and a dirty tree, both still commit. It runs verbose
    so branch lineage is visible on a passing run.
  - **The stray `venv/` is deleted.** It carried black 25.1.0 against the
    24.3.0 this repository pins, and two entries in the local permission
    allowlist had been authorising it. Both entries are removed. It came from
    the Batch 12/13 convention, which spelled the directory without the dot;
    the archived definitions still show that spelling, so reading one can
    recreate it. `resolve_venv()` looks only for `.venv` and cannot see a
    second one.
  - **A `SessionStart` hook** injects branch, working-tree state, guard codes
    and the machine-managed status block into every new Claude Code session,
    with the reminder that a tracked-file commit needs its Section 4 entry in
    the same commit. It is local to this machine and does not help Codex or
    Copilot, which is recorded in the finding.
  - **The `FINDINGS.md` header is corrected.** It attributed F-B21-21 and
    F-B21-22 to both WP-3 and the owner review, and omitted F-B21-23 and
    F-B21-24. Raised on PR #220.
- Not done, and deliberately: a manifest of untracked-but-essential files
  (`skills-lock.json` is still missing), and two structural defects in
  `AGENTS.md` -- the fast-paths that authorise skipping bootstrap sit above
  the numbered list, and the file carries origin narrative that serves the
  editor rather than the reader. Both edit `AGENTS.md` and need an owner
  ruling first.
- **The first push went red, and the hook was the cause.** `12cfe25` failed
  the Quality Gate with `ERROR WT007 origin/main -- comparison base ref is
  missing`. `actions/checkout` makes a shallow single-branch clone, so
  `origin/main` does not exist on a runner and the guard fails closed on a
  base ref that is legitimately absent. `WARNING WT009` also fired for the
  `.venv` CI does not use. The step now sets `SKIP: worktree-alignment`,
  with the reason at the step: the guard measures developer worktree
  lineage, and a runner has no worktree topology to protect. Fetching the
  base ref would have silenced WT007 and left the check measuring nothing.
- The lesson is the one this entry is about, applied to its own author. A
  check was added without asking where it runs, and its assumptions held on
  one machine only. Local verification passed and proved nothing about CI.
- Validation: 822 tests, all 12 hooks locally, docsync `--check` exit 0,
  guard exit 0, and the Quality Gate green after the skip landed.

### 2026-08-25 - PR #218 review rounds and post-completion pass applied (side-task)

- Scope: remediated every Codex comment on PR #218 while WP-3 sat open and
  unmerged. Thirty-seven comments across PR #216 and #218 in total -- seven
  on #216 and thirty on #218. Thirty-six were valid; all were actioned.
  All twelve rounds were answered and all thirty threads were resolved. On
  2026-08-25 the owner authorized batched review replies and resolution of
  threads whose fixes are present at the pushed head; GitHub owns the
  resulting live state.
  One was declined on its premise -- it said the closed thresholds disclosure
  gave its controls zero-sized boxes, and deleting their sizing turns the gate
  red, so they were being measured -- and its remedy was applied anyway.
- What changed, beyond the individual fixes:
  - **Touch sizing and the 1rem input size moved off the width query** onto
    `@media (any-pointer: coarse), (max-width: 859.98px)`. A tablet in
    landscape is wide and touched. The two rules were corrected one round
    apart, which is the lesson: a rule moved for a newly understood condition
    is not done until every rule sharing that condition moves with it.
  - **The frontend gate gained a third device profile**, a wide touch screen,
    and `run_checks` now takes a page factory because touch emulation belongs
    to a browser context.
  - **The export header is measured rather than fixed**, after the file it
    produced was opened and looked at.
  - **A `/validate_user` reply is discarded when the field has moved on.**
    The submit guard added earlier in the series had turned a cosmetic stale
    message into a block that no blur clears.
  - **Round six found two blind spots in DOC009 and DOC011 themselves**, one
    day old. DOC009 accepted a file after its first match, so `index.css`
    could state the breakpoint once and contradict it in either of its other
    two media queries; it reads every occurrence now, and a site may declare
    `expect` so two notations of one fact -- `859.98px` and `860` -- can
    differ without the check going blind. DOC011 searched line by line and
    could never match a phrase that wrapped, which in Markdown that wraps at
    about 76 columns is the likely shape rather than an edge case; it matches
    the joined document now and maps back to the starting line, with the
    history and strikethrough exemptions applied after that mapping.
  - **Round seven found the same two blind spots one level further out.**
    DOC010 also searched line by line, and `PLAYBOOK.md` already carried a
    citation of `AGENTS.md` "UI and Accessibility Rules" across two lines, so
    that heading could have moved with the gate green. DOC009 shared the
    shape, quietly: a file that states a value more than once satisfied the
    check on the unwrapped copy while a drifted wrapped one went unread. Both
    read the joined document now. `_joined_text` strips each line before
    joining, without which a correct wrapped citation resolves to a heading
    name with five spaces in the middle of it.
  - **The anchor scan is every Markdown tree**, not the trees someone
    remembered. It had missed `docs/SWE_AUDIT_CHARTER.md`, which cites
    `AGENTS.md` and was never read. Three exemptions are declared with it:
    `docs/history` and `docs/logarchive`, because a dated record is accurate
    at write time and renaming one heading would otherwise turn 70 archived
    files red with no fix but editing history; and `CLAUDE.md`, because it is
    gitignored, so scanning it made the gate's answer depend on which machine
    ran it.
  - **Widening the scan found a checker defect before it found a document
    defect.** The design contract labels some sections as list items, and the
    bold-label pattern insisted the asterisks start the line, so the WP-3
    plan's citation of "Responsive" resolved nowhere. Fixing that first was
    the difference between the widening finding a defect and the widening
    crying wolf.
  - **A year warning that is still true survives a username edit.**
    `clearRegistrationState()` had reset the minimum and the hint and left the
    message naming the previous account's join year. Clearing the message
    outright is the obvious fix and is wrong: "Year cannot be in the future"
    is about the year, not the account. The handler re-derives instead, and a
    ninth gate check holds the half a reader would not notice was broken.
  - **A failing validator no longer locks the form it serves.**
    `/validate_user` answers an outage with 503 and `valid: false`, which both
    blur handlers read as a verdict about the username. Trying again was the
    one thing the message asked for that could not work. Reported against the
    heatmap form, which refuses at its own submit guard; the index form has
    the same defect through native validation, because only the heatmap form
    carries `novalidate`. One comment, two forms.
  - **A declaration with nothing to scan is refused.** `scan` was optional, so
    an anchor carrying only `target` and `pattern` validated, visited no
    documents, and DOC010 reported clean while checking no citations at all.
    That is the same silent end state as the misspelled key closed the round
    before, reached without a typo -- the earlier fix stopped at the way the
    fault had been reported rather than at the condition behind it.
  - **A nonempty scan must resolve to work.** Round eleven found named files
    and globs that resolved nowhere were silently skipped. The sibling sweep
    also found a third route to the same clean no-op: `allow_files` could
    exempt every resolved path. DOC010 and DOC011 now fail loudly for all
    three, rather than validating only the list container.
  - **Declared regexes carry semantic contracts.** A syntactically valid
    anchor with no heading capture crashed at its first match. Anchor patterns
    now require exactly the heading plus optional item captures, validate a
    participating heading and numeric item, and value patterns reject extra,
    missing, optional-empty and empty captures before those assumptions can
    turn into a crash or a false agreement.
  - **Top-level declaration collections validate before iteration.** Round
    twelve found that `value = 1`, `anchor = 1` and `retired = 1` reached their
    collectors as integers and raised `TypeError` before the per-declaration
    schema could report malformed input. All three outer collections now fail
    once at the wiring boundary. The raw collector calls predated round eleven,
    so this was backlog in the new module rather than a regression from that
    round; the earlier class sweep still stopped one boundary too low.
  - **The heatmap window declaration covers the class, not the remembered
    instances.** Its runtime, product, owner, architecture and canonical-design
    copies are now sites. `HEATMAP_WINDOW_DAYS` remains the source and the
    inclusive fetch subtracts one from it. `static/js/loading.js` is
    deliberately excluded because its number is the leap-aware length of a
    calendar year for a different average. The same census widened the older
    breakpoint, touch-target and Adobe-kit declarations across their runtime,
    owner and canonical-design copies, and removed redundant literals where
    the adjacent code already owns the value.
  - **A declared container is checked for what it holds.** `scan = [1]` is a
    list, so the shallow check passed it and the integer reached the glob
    matcher as a `TypeError`. Round eight was the third round on this module
    and each one sat one level further in than the last: wrapped text, then
    missing and misspelled keys, then the contents of a container.
  - **A malformed declarations file is refused, not ignored.** Reading a
    required key straight out of the mapping raised a bare `KeyError`, so an
    anchor with no `target` ended the run in a traceback and exit 1. Looking
    for the siblings found four more, and all four are worse because they are
    silent: a misspelled key, a list written as a bare string, a misspelled
    table, and a misspelled option. Each leaves a check quietly not checking
    while the gate stays green. Every declaration is now held to a declared
    schema, so an unknown key is an error rather than a shrug.
  - **A bad declarations file is reported rather than thrown.** Malformed
    TOML, or a declaration holding an invalid regex, raised
    `DeclarationError` straight through both CLI paths, which catch
    `SyncError` and exit 2. The run ended in a traceback and exit 1 instead.
    It is a `SyncError` now, keeping the distinct class its docstring asks
    for so the reader is not sent to edit the wrong file.
  - **The validators identify requests, not only values.** The first sweep
    found that the album validator discarded stale replies but not stale
    failures. Copying the heatmap sibling's value guard closed A-then-B and
    still failed A-then-B-then-A, where the oldest and newest requests carry
    identical text. Both state machines now use request generations, and the
    browser check holds that ABA sequence. A second check holds the current
    failure path: a network outage replaces an older red invalid verdict with
    an outage message while leaving server-side submission available.
  - **The independent visual sweep closed six contract slips.** Keyboard focus
    opens both ambiguous-field hints without breaking tap; valid usernames use
    the canonical good colour; selected controls and hints raise their shadows
    in dark mode; the lone 6px radius moved onto the 8px ladder step; and both
    text-holding header heights scale in rem. Three browser checks exercise the
    rendered states at both sides of the breakpoint.
- **The final gate found its own procedure contradiction.** The Tailwind drift
  hook compares the generated working file with the index, so a correct
  source-and-output edit cannot pass before staging even though `AGENTS.md`
  requires pre-commit before staging. `F-B21-20` records the owner decision;
  this review validates an exact-name staged candidate and restores the index.
- Two findings came out of reading the comments as a set rather than one at a
  time: `F-B21-17`, that six of nineteen were one fact written twice, and
  `F-B21-18`, that browser JavaScript has no unit runner. `F-B21-17` was
  then built and closed the same day; see the DOC009 entry below.
- Deviations: none against a plan, because there was none -- this is review
  remediation. The canonical mobile-strip, layout-independent export and
  day-detail gaps and the gate-order contradiction were not improvised during
  review; `F-B21-18`, `F-B21-19` and `F-B21-20` record them for an owner ruling
  and a bounded implementation.
- Post-completion review: the root-font mutation was reproduced at `20px`
  instead of the original `17px`, and the theme-persistence check also left
  its saved choice behind. Both now restore state in `finally`. Two earlier
  Graphify findings were also real: declaration paths could traverse outside
  the repository, while joined-document matching had lost the original
  per-line `^`/`$` behavior in DOC009, DOC010 and DOC011. Root confinement and
  a shared dual-representation matcher close those classes. Four claims were
  rejected: F-B21-4's do-not-close instruction does not govern F-B21-5; the
  validator state is reached without aborting; claimed profiles are the only
  planned runs; and `run_checks` deliberately takes a page factory because
  touch capability belongs to the browser context. No Page-object caller
  remains, and Graphify's reproducer passed an integer instead of either valid
  interface. Its duplicated coupling comments supplied counts but no defect;
  the cohesive functions remain in place rather than undergoing a risky late
  refactor.
- The final Graphify pass found one more real boundary defect among four false
  alarms. `_Files` resolved `nested/../PLAYBOOK.md` to the right filesystem
  path but used the unnormalized spelling to look up live documents and its
  cache, so a declaration could grade stale disk instead of the document this
  run had just rendered. Both lookups now use the confined repository-relative
  key. The import, page-factory, generated tab and pruned-utility claims were
  disproved by execution, current callers and source census.
- Validation: `pytest -q` -- **822 passed**, 3 warnings. The declaration seam
  is **71 passed** and `pytest --collect-only` confirms 822 tests across 40
  files. The frontend gate reports **15 checks in 23 runs** across desktop,
  mobile and wide touch. All 11 pre-commit hooks pass.
  `doc_state_sync.py --check` exits 0 with only the expected active-batch
  root-definition warning. Every behavioral fix was red before it was written
  and re-measured after.
- Review completion: `77bb001` closed the original twelve Codex rounds. Both
  Quality Gate runs passed, all thirty threads were resolved, and the Codex
  connector recorded a thumbs-up at 2026-08-25 19:17:45 UTC. `bd49cdb` then
  recorded the documentation-only handoff. The final follow-ups own the five
  developer-gate hardening classes above. PR #218 is the completed WP-3
  integration branch; WP-4 starts from its merged result. The owner selected
  a rebase merge so the individual commit history remains visible without
  adding a merge commit.
- Forward guidance: a quiet round was not treated as completion. The recorded
  thumbs-up was. Rounds four and five found defects that earlier fixes in the
  series had introduced. Round six then found two holes in one-day-old code,
  so review yield tracked new surface area rather than elapsed rounds. Expect
  a fresh review of whatever `F-B21-18` builds. Both round-six holes were of a
  kind a check's own tests cannot find because the tests were written from the
  same understanding as the code. Keep an independent reviewer on tooling as
  well as features.

### 2026-08-25 - DOC009 to DOC011: facts written down more than once (side-task)

- Scope: closed the buildable half of `F-B21-17`. Three declared integrity
  checks in a new `scripts/docsync/declarations.py`, driven by a new
  `.docsync.toml` at the repository root. No new dependency; the declarations
  are TOML read with `tomllib` from the standard library.
- Why: six of the nineteen Codex comments across PR #216 and PR #218 were not
  logic defects. They were one fact recorded in several places where the
  copies had drifted. The clinching case was a cross-reference that named its
  target by heading, exactly as `F-STYLE-1` asks, and broke in the same commit
  that moved the heading. A written rule cannot catch that; only something
  that resolves the reference can.
- Plan vs implementation: DOC009 compares a value across its sites, DOC010
  resolves a citation shape against the document it names, DOC011 keeps a
  retired claim out of anything that still prescribes. Four behaviours were
  added after the first run reported false positives on real documents, and
  each is a property of how this repository actually writes: bold lead-ins
  count as citable places, a heading cited without its trailing parenthetical
  resolves, a label's trailing sentence is not part of its name, and
  struck-through text is already marked as not current.
- What the first run found, before any test was written:
  - **`static/css/shell.css` used `max-width: 860px`** where every other
    stylesheet uses `859.98px`. Both the mobile and the desktop rules
    therefore applied at exactly 860px. Fixed.
  - **`AGENTS.md` described the integrity codes as DOC001-DOC006**, four
    checks after that stopped being true. Fixed, and the line now says when
    it went stale, because that is the same class the new checks exist for.
  - Two stale citations, one of them inside the finding that proposed the
    check.
- Deviations: the declarations file is at the repository root as
  `.docsync.toml` rather than under `docs/`. It is configuration, it sits
  beside `.pre-commit-config.yaml` and `.gitattributes`, and keeping the
  repository-specific half out of `scripts/docsync/` is what lets that
  package be lifted into another repository unchanged.
- Validation: `pytest -q` -- **771 passed**, 3 warnings, 22 of them new. All
  11 pre-commit hooks pass with an identical `git write-tree` either side.
  Each of the three checks was proved against the real defect it was built
  for, by restoring that defect and watching the check name it. Five
  mutations of the module each killed exactly one test and no others.
  `doc_state_sync.py --check` exits 0. The frontend gate is unaffected and
  still reports 8 checks in 13 runs.
- Forward guidance: add a declaration when a fact starts living in two
  places, not after it drifts. `F-B21-18` is the other half and is not
  started -- browser JavaScript with no unit runner, to be reached through
  a guarded seam onto the Chromium the frontend gate already pays for, not
  through npm.

### 2026-08-24 - F-B21-13 docsync bootstrap gate remediated (side-task)

- Scope: closed `F-B21-13` with DOC007 and DOC008 on
  `wip/f-b21-13-docsync-gate`, branched from `origin/main` at `658bdb2`;
  WP-3 remains on `wip/batch-21`.
- DOC007 now has one next-WP calculation. The managed SESSION_CONTEXT
  renderer owns `_next_wp_number()`, the integrity check calls that helper,
  and the CLI supplies the active definition's finite plan. Absorbed,
  dropped and merged WP headings are skipped; a fully completed plan
  terminates with no next package instead of looping forever, while any stale
  numeric next-WP claim left at close-out is blocking. The definition Status
  line, PLAYBOOK Section 3's actual Next action bullet, and SESSION_CONTEXT
  Section 1's sole active Batch status row are checked for the same active
  batch and next WP. Historical claims outside the bullet and earlier claims
  superseded inside it cannot steal the comparison.
- DOC008 applies `latest_test_count_authority()` to the FINDINGS.md header
  with findings-specific remediation. Authority includes live entries, the
  side-task archive and per-batch logs; a same-date tie between batch logs is
  resolved by numeric batch chronology rather than filename insertion order.
- Review remediation also repaired two misleading DOC007 fixtures so their
  asserted WP ranges really sit inside the current-batch markers, and made
  DOC008's error invariant say the header count "must agree" instead of
  claiming that a detected mismatch already agrees. Every new edge case was
  observed failing before its minimal fix.
- Deviations: the owner authorized expanding the original PR file set on
  2026-08-24 after the audit proved DOC007 and the renderer computed different
  next-WP values. The expansion is limited to the renderer/sync/CLI data path
  and its directly related docsync tests; no unrelated refactor was taken.
- Validation: `pytest -q` -- **717 passed**, 3 warnings (was 682; 35 new
  tests across the docsync integrity, renderer, logic, CLI and count suites).
  The focused docsync suite is **219 passed**.
- Forward guidance: WP-3 should still update the definition Status line as
  an explicit task. The gate proves agreement; it does not replace writing
  the canonical status correctly.

### 2026-08-23 - PR #216 review round three applied (side-task)

- Scope: two review comments on `e9bac27`, both real rendering defects in
  WP-2's own shell commit. Both were verified in a browser before any edit.
- **The header wordmark ignored `prefers-reduced-motion`.** The lockup
  carried five SMIL `<animate>` elements with `repeatCount="indefinite"`.
  No CSS can pause SMIL, so the media query in `shell.css` never reached
  them. WP-2 made the exposure much worse: the mark moved from per-page
  hero content that scrolls away into a fixed header that is on every page
  and never leaves the viewport. `docs/design/README.md` already prescribed
  the remedy and says the SMIL must be stripped and the bars animated from
  CSS. Done, with the keyframes taken from `docs/design/tokens/base.css`.
- **A wrong assumption was caught by measuring.** The origin looked like it
  needed a 7-unit correction, because this lockup's viewBox starts at y=7
  where the full mark starts at y=0. It does not: `view-box` resolves
  `transform-origin` in the SVG user coordinate system, not from the
  viewBox corner. At `scaleY(3)` the proposed 56.5px slid each bar bottom
  8.4px and the canonical 63.5px held it to 0.2px. Under the shipped 1.10
  scale the gap is under half a pixel, so eyeballing would have missed it.
- **The back-to-top control lost its layout.** `base.html` used to wrap the
  theme toggle and `page_footer_extra` together in `.page-footer-bar`. WP-2
  moved the toggle into the header and removed the wrapper with it, but
  `results.html` still fills that block and `#back-to-top` has no CSS of its
  own anywhere. Centring, gap, padding and entrance all came from the
  wrapper, so the control shipped bare and left-aligned. Restored in
  `shell.css` rather than `global.css`, which only reaches unmigrated pages.
- Both guards were proven able to fail. Putting one `<animate>` back fails
  five tests, reflowing the wrapper onto three lines fails four, and
  dropping the reduced-motion `opacity: 1` fails one.
- Deviations: the frontend gate gained no reduced-motion check. Its checks
  take a page rather than a browser, so a second context needs a signature
  change, and that is a refactor rather than a review fix. The template
  tests cover the markup and the CSS; the computed behaviour was verified
  by hand this round.
- Findings: `F-B21-5` updated rather than closed. The header instance is
  resolved; the pinwheel and the index hero wordmark still carry SMIL and
  belong to WP-3.
- Validation: `pytest -q` -- **682 passed**, 3 warnings. All 11 pre-commit
  hooks pass. The frontend gate reports `5 checks passed`.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: strip the SMIL from the remaining two assets the same
  way. Do not reach for `svg.pauseAnimations()` -- the CSS route is what the
  design contract asks for and it needs no JavaScript.

### 2026-08-23 - PR #216 review round two applied (side-task)

- Scope: two review comments on `4105aef`, both documentation. Both were
  verified against the files and both were valid.
- **The batch definition still said WP-2 was next.** PLAYBOOK Section 3 and
  `SESSION_CONTEXT.md` Section 1 both said WP-3. `AGENTS.md` makes those
  three agreeing the condition for bootstrap to complete, so the next agent
  would have stopped on the disagreement. `git log -S` puts the line's last
  edit in `7c00754`, the WP-1 commit. WP-1's plan listed updating it as a
  task and WP-2's did not.
- **The findings header still published 666 tests.** The round-one commit
  moved PLAYBOOK and SESSION_CONTEXT to 671 and left that copy behind. It is
  the instance-not-class anti-pattern `AGENTS.md` names, committed inside the
  commit that was fixing stale documentation.
- Every other `666` in a tracked document was checked rather than assumed.
  The remaining three are dated log entries that were accurate when written,
  so they stay.
- **`F-B21-13` filed for the class.** Neither line is read by any gate.
  `doc_state_sync.py` derives the next work package from PLAYBOOK and never
  reads the batch definition, and the test-count enforcement in
  `scripts/docsync/integrity.py` covers SESSION_CONTEXT only. The definition
  status line has now gone stale twice -- PR #170 corrected it once for
  WP-1 -- which is the point at which `AGENTS.md` prefers a mechanical check
  over another written rule.
- Deviations: the gate was not extended in this round. It is a change to the
  integrity checks every work package depends on, and scope discipline puts
  that in a finding rather than in an open UI PR.
- Validation: `pytest -q` -- **671 passed**, 3 warnings. All 11 pre-commit
  hooks pass. `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: WP-3 should carry updating the definition status line as
  an explicit task, the way WP-1 did, until `F-B21-13` closes.

### 2026-08-23 - PR #216 review round one applied (side-task)

- Scope: three review comments Codex left on `45fbbe8`. All three were
  verified against the code and all three were valid. None was declined.
- **Tailwind was pruning tokens the handwritten CSS reads.** Tailwind v4
  emits a theme variable only when a generated utility uses it.
  `static/css/error.css` reads `--font-figure`, `--font-weight-bold`,
  `--spacing-8`, `--radius-sm` and `--radius-lg` directly, no utility used
  them, and none reached `static/css/tailwind.css`. An undefined `var()`
  with no fallback voids the whole declaration, so the error page shipped
  with no card rounding and no page padding, and its status number took
  neither the bold weight nor the Gotham face. Nothing failed and nothing
  logged. `@theme static` fixes it and adds 16 declarations to the compiled
  file. A browser now reports 14px card rounding and 32px 16px page
  padding.
- **No page set `font-family` on `body`.** Neither `global.css` nor
  `shell.css` carried one, so the four unmigrated pages downloaded the
  Adobe kit and then rendered in the Bootstrap system stack. The batch
  definition lists the body font as a WP-2 deliverable, so this was a
  missed one rather than a new idea. The declaration went into `shell.css`
  behind a new `--shell-font-sans` token, because an unmigrated page never
  loads the compiled stylesheet and `var(--font-sans)` resolves to nothing
  there.
- **`SESSION_CONTEXT.md` sections 3 and 4 were stale.** They said 9 css and
  7 js files, still listed a deleted `error.js`, and omitted `shell.css`,
  `frontend_gate.py` and the lockup SVG. Real counts are 10 and 6.
- Two gaps closed while in the same files. `tests/test_template_shell.py`
  gains a test that renders each page, reads back the stylesheets it loads,
  and asserts every `var()` without a fallback resolves in one of them.
  Nothing checked that invariant before. The gate gains a fifth check for
  the body font, reading computed style rather than stylesheet text,
  because the failure is a cascade one and only a browser can settle it.
- Deviations: the dependency graph also gained `dev/tailwind_build.py`,
  which WP-1 added and never recorded. It was a one-line omission in the
  block being corrected, so leaving it was worse than fixing it.
- Both fixes were proven able to fail. Reverting `@theme static` fails two
  tests, and removing the body declaration fails the gate on `/` and names
  the system stack it fell back to.
- Validation: `pytest -q` -- **671 passed**, 3 warnings. All 11 pre-commit
  hooks pass. The frontend gate reports `5 checks passed`.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: the compiled stylesheet is 1,650 lines now, so every
  line citation into it is stale again. Cite the block, not the number.

### 2026-08-23 - Node 20 CI deprecation filed as F-B21-12 (side-task)

- Scope: recorded a warning the Quality Gate has started printing. No
  workflow change, no dependency change, no code change.
- Plan vs implementation: `F-B21-12` filed. Four pinned actions in
  `.github/workflows/test.yml` -- `actions/cache`, `actions/checkout`,
  `actions/setup-python` and `actions/upload-artifact` -- target Node 20,
  which GitHub deprecated. Runs are forced onto Node 24 and pass, so nothing
  is broken today.
- Why file it: all four sit in one file and fail together on the day the
  forced fallback is withdrawn. That break would land on whichever work
  package is open, would look unrelated to its diff, and would block every
  PR at once. The finding says to bump them in their own commit and to read
  each action's releases rather than guess the major that carries the new
  runtime.
- Deviations: none.
- Validation: `pytest -q` -- **666 passed**. All 11 pre-commit hooks pass.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: not urgent, but the deadline belongs to GitHub rather
  than to this repository. Do it as a standalone commit, not folded into a
  UI work package, because every other work package depends on that gate.

### 2026-08-22 - Tailwind citations renamed after the rescope (side-task)

- Scope: 13 line citations in `FINDINGS.md` and
  `docs/design/RECONCILIATION.md`. No code changed.
- Codex caught this on PR #173. It is correct.
- The `source(none)` comment moved `tailwind.src.css` down five lines. The
  rescope cut `tailwind.css` from 2,289 lines to 1,576. Every citation into
  either file broke at once. `:root:not([data-theme])` moved from 2042
  to 1335.
- The citations now name the block or the declaration: the two
  `@plugin "daisyui-theme.mjs"` blocks, `--spacing-*`, `--radius-*`,
  `--font-sans`, `--font-mono`, `--font-weight-medium`,
  `@custom-variant dark`, `prefersdark: true`. Named anchors do not drift.
- Checked the citations Codex did not flag. `heatmap.js:14-22`,
  `heatmap.js:25-26`, `theme.js:17`, `base.html:26` and `index.css:158` all
  still resolve. Those files did not change.
- This is `F-STYLE-1` happening again. The rule already exists for
  `AGENTS.md`. It applies to every file. Cite a name, not a number.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**.

### 2026-08-22 - Open findings mirrored to GitHub issues (side-task)

- Scope: created issues #174-#215. Rephrased two rules in `AGENTS.md`. Filed
  `F-B21-9`. No code changed.
- Why: Codex raised `F-B21-7` on PR #173 although the PR body listed it.
  Reviewers do not read `FINDINGS.md`. Issues are cheaper to search.
- 42 open findings are now mirrored: 28 P1, 10 P2, 3 Info, 1 Feature. Seven
  resolved findings were skipped. Labels are `finding` plus the severity.
- Each issue body says `FINDINGS.md` is the source of truth and that the
  issue is a read-only mirror. Nothing writes back to the file.
- `AGENTS.md` changes are rephrases, not additions. Bootstrap item 7 already
  said "read on demand"; it now names the three reasons to open the file and
  says a recorded defect is known and owned. The Markdown log-entry bullet
  now also asks for plain English. No new rule was added.
- `F-B21-9` records the gap. The mirror is manual and will drift. The owner
  accepted that on 2026-08-22 and asked for it to be written down rather
  than built now. A sync script is code and needs its own work package.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**.

### 2026-08-22 - PR #173 review answered, two import defects fixed (side-task)

- Scope: moved `docs/design/styles.css`. Fixed one claim in
  `docs/design/RECONCILIATION.md`. No code changed.
- Codex raised four threads. All four are correct. Claude disputed none.
- `styles.css` went into `docs/design/tokens/`. It belongs one level up.
  The file imports `tokens/fonts.css`. From inside `tokens/` that path does
  not exist. So the entry point loaded no tokens.
- The source project keeps `styles.css` at its root. `DesignSync list_files`
  confirms this. `git mv` fixes the path. The content does not change.
- `RECONCILIATION.md` said every colour in the README tables matches the
  theme. That is wrong. Three tokens match: `--surface-page`, `--text-strong`
  and `--accent`. Four are absent. Dark `--surface-sunken` is `#181520`, not
  `#1a1622`. The status colours are still Bootstrap's.
- A per-token table now replaces the claim.
- This is the second false claim of this shape in that file. `F-B21-8`
  records the first. Both came from a spot check.
- The other two threads repeat `F-B21-7`. Codex found them on its own. They
  stay with WP-2. WP-2 owns that code next.
- Checked this pass: only `RECONCILIATION.md` changed under `docs/design/`.
  The imported files match `fa56cd6`. Claude's Markdown has no non-ASCII.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**. It inherits `F-B21-7` and `F-B21-8`.

### 2026-08-22 - Tailwind source scope corrected after PR #173 went red (side-task)

- Scope: `static/css/tailwind.src.css` (one directive plus a comment), the
  regenerated `static/css/tailwind.css`, `FINDINGS.md` (`F-B21-8`), and the
  false claim in `docs/design/RECONCILIATION.md` section 2. Owner chose the
  fix and the recording from two options each.
- Trigger: PR #173's Quality Gate failed on "Verify committed Tailwind CSS".
  Not a flake. The rebuild added 30 lines the committed file did not have.
- Cause: `@source` **adds** to Tailwind v4's automatic detection instead of
  replacing it, so the whole repository was scanned, not just `templates/`
  and `static/js/`. The extractor turns bare words in Markdown into class
  candidates, so prose compiled into utilities -- `.contents`, `.isolate`,
  `.flex`, `.border`, `.relative`, `.sticky`, `.truncate`, `.italic`.
- The design import did not create this; it exposed it. The committed
  baseline was already contaminated. Scoping the scan removed **713 of 2,289
  lines, 31% of the stylesheet**.
- Fix: `@import "tailwindcss" source(none)`. Rejected alternatives, both
  offered to the owner: regenerate as-is, which would couple the design
  documentation to production CSS permanently; and `@source not "../../docs"`,
  which fixes only `docs/` and leaves `tests/`, `scripts/` and the root
  Markdown feeding the scanner.
- Verified rather than assumed: both theme blocks survive (`--color-base-100`
  is `#faf8f3` light and `#0e0c12` dark, and `data-theme` still appears three
  times), and a second consecutive build reproduces the first byte for byte.
- Deviations: two `@source not` directives are now unreachable and were left
  in place deliberately, as protection if `source(none)` is ever removed.
  Recorded in `F-B21-8`.
- **Process failure worth naming.** Last session's check,
  `git diff --exit-code -- static/css/tailwind.css`, was reported as proof
  that `docs/design/` was outside Tailwind's scope. It proves only that the
  file was not hand-edited. The build has to actually run. `F-B21-8` records
  that nothing local runs it, which is what WP-2's `tailwind-css-drift` hook
  closes.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
  `doc_state_sync.py --check` exits 0. `pre-commit run --all-files` passes.
  Quality Gate re-run on PR #173.
- Forward guidance: **WP-2 is next** and should treat `F-B21-7` and `F-B21-8`
  as its own, since the drift hook it adds runs both code paths.

### 2026-08-22 - Two WP-1 review items filed as F-B21-6 and F-B21-7 (side-task)

- Scope: `FINDINGS.md` only -- two new findings plus the stale status header.
  No code changed. Filed before opening the Batch 21 PR so the branch is
  self-describing rather than leaving a reviewer to rediscover them.
- Both items came out of the five-agent WP-1 review on 2026-08-20 and were
  carried in local notes, unfiled, ever since. Each was re-verified against
  the code before filing; neither was taken on the review's word.
- `F-B21-6`: `routes.py:135,302,436` use naive `datetime.now()`. Line 436
  gates the requested year against host-local time while
  `orchestrator.py:70-71` builds the fetch window in UTC, so gate and window
  disagree by the host offset near New Year. They agreed before F-SWE-2,
  which fixed the window and left the gate. Production runs UTC, so this is
  a developer-host defect.
- `F-B21-7`: two defects in the WP-1 toolchain. The one test naming the
  integrity property patches both `required_artifacts` and `ensure_artifact`,
  so no integrity code runs. **Verified by mutation:** deleting
  `bin_dir=bin_dir` from `tailwind_build.py:293` leaves the full suite at
  633 passed. The review had claimed only the 35 toolchain tests stay green;
  the real blast is the whole suite. Separately,
  `http.client.IncompleteRead` subclasses `HTTPException`, not `OSError`, so
  it escapes both handlers as a raw traceback -- confirmed from the MRO --
  and a cleanly truncated download surfaces as `SHA-256 mismatch`, which
  reads as tampering rather than a network fault.
- Deviations: none. The mutation was reverted with `git checkout --` and the
  working tree confirmed clean before anything was staged.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; the only
  Python touched was the mutation, which was reverted.
  `doc_state_sync.py --check` exits 0. `pre-commit run --all-files` passes.
- Forward guidance: **WP-2 is next.** It should absorb `F-B21-7`, because the
  `tailwind-css-drift` hook it adds runs the same code path. `F-B21-6` is
  independent of the UI batch and needs no WP of its own.

### 2026-08-21 - SESSION_CONTEXT batch status row resynced (side-task)

- Scope: `.claude/SESSION_CONTEXT.md` Section 1 only -- the Batch 21 status
  row and the "Last updated" date. No code, no gate, no Section 3 change.
- Why: the row still read "the owner-approved root-hygiene side task is next,
  then WP-2". That side task closed on 2026-08-20, and two further side tasks
  landed on 2026-08-21. PLAYBOOK Section 3 was correct throughout; only the
  snapshot was stale.
- Three earlier commits caused the drift. Each updated PLAYBOOK and left this
  row alone. `AGENTS.md` "What to update after a WP or side-task commit"
  requires SESSION_CONTEXT Section 1 to move when the batch status changes.
- Not a gate failure, and nothing would have caught it. `doc_state_sync.py`
  manages the STATUS block in Section 2, which was correct the whole time.
  Section 1 prose is hand-maintained and unchecked.
- The row now also names `docs/design/README.md` as the canonical design spec
  and `docs/design/RECONCILIATION.md` as the override list, so a bootstrapping
  agent finds the design tree from the state snapshot.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; no Python
  touched. `doc_state_sync.py --check` exits 0. `pre-commit run --all-files`
  passes.
- Forward guidance: **WP-2 is next**, unchanged. Section 1's batch row is the
  first thing a bootstrapping agent reads for state. Update it in the same
  commit as the PLAYBOOK entry, never afterwards.

### 2026-08-21 - Size rule restated as intent in AGENTS.md (side-task)

- Scope: rewrote Proposal and Design Rules item 3 in `AGENTS.md`. One rule, no
  other rule touched, no code touched. Owner-authorised.
- Plan vs implementation: the rule read "No new file should be larger than the
  largest peer in its directory", which is the proxy metric rather than the
  intent, and it is the example `CLAUDE.md` had been carrying as the model for
  the planned trim. It now states the intent: the rule is against god files,
  not line counts; a file large because its job is large is fine; the peer
  comparison is the check you run when you notice scope creep, not a threshold
  to clear. Owner's framing, given 2026-08-21.
- This also resolved a contradiction inside the same list. Item 5 already said
  "SoC/DRY is the constraint on file content, not line count", which item 3
  denied. They now agree.
- Checked before writing, not after: `F-WORKTREE-4` and `F-MAS-3` are the only
  other places that restate the cap, and both already carry the correct
  reading -- "the rule exists to prevent unmaintainable monoliths" and "size
  was never the defect". Neither was edited; item 3 now cites both.
- Deviations: one, and it matters. The rewrite grew the item from three lines
  to eight, so every `AGENTS.md` line citation past it moved by five. This is
  the same drift that made `F-STYLE-1` cite 254, 262 and 550 when the real
  lines were 255, 263 and 551. One live citation was affected --
  `docs/design/RECONCILIATION.md` pointed at the ASCII rule by line. It now
  names the section instead, and `CLAUDE.md` records the rule: cite
  `AGENTS.md` by section or rule name, never by line.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; no Python
  touched. `doc_state_sync.py --check` exits 0. `pre-commit run --all-files`
  passes.
- Forward guidance: WP-2 is still next. When the wider `AGENTS.md` trim
  happens, do it this way -- one rule at a time, intent replacing the proxy
  metric, and re-grep line citations afterwards because they will move.

### 2026-08-21 - Front-end design handoff imported to docs/design (side-task)

- Scope: imported the owner's Claude Design project
  (`7d95e96a-613b-4017-9dd7-8b74d2db9535`) into `docs/design/`, recorded where
  it diverges from the batch contract, and filed two findings. No runtime code
  changed. WP-2 keeps its own reserved commit.
- Plan vs implementation: the source project holds 207 files; 61 are imported
  verbatim through the design MCP -- the canonical `README.md`, 10 token files,
  24 components as `.prompt.md` plus `.d.ts`, and two subordinate references.
  The import is a curated subset and says so; everything else stays reachable
  through the MCP, and `RECONCILIATION.md` section 2 tables what was left
  behind and why. Claude added a 62nd file,
  `RECONCILIATION.md`, because a verbatim snapshot states the Adobe Typekit
  stack and the `.dark` marker as fact and the owner has overridden both;
  without an override list a later agent reading only the specification would
  implement the wrong thing. `docs/AGENT_DOC_MAP.md` gains a row so the tree is
  discoverable.
- Owner decisions, all made this session: (1) the type stack stays self-hosted,
  so `BATCH21_DEFINITION.md:155-158` decision 4 stands and kit `rwy8ghw` is not
  adopted; (2) `docs/design/README.md` is canonical and is the default over
  both files in `reference/`, but it does not automatically retire an audit
  finding; (3) curated text-only import; (4) import only, one commit.
- Deviations: none against the approved plan, but two of its assumptions were
  corrected by evidence found while importing. The plan treated the mobile
  input size as a live conflict; it is not -- the canonical bundle's own
  `components/forms/Input.prompt.md` mandates 16px or larger on mobile, which
  matches the shipped override at `static/css/index.css:158`. `F-B21-5` records
  it as settled rather than open. The plan also assumed the component layer
  followed the Adobe stack; it does not -- `Button.d.ts` and `Input.d.ts` name
  JetBrains Mono, so the self-hosted mapping agrees with most of the bundle.
- Verified against code, not accepted from the documents: the seven `rocket_r`
  stops in `static/js/heatmap.js:14-22` match the specification exactly; every
  hex value in both colour tables matches `static/css/tailwind.src.css:69-137`;
  the three accessibility defects in `F-B21-5` were each confirmed at the line
  cited. The unmatched-grouping bug the design review names was already in the
  batch contract at `BATCH21_DEFINITION.md:25-27` and is not filed again.
- `docs/` is excluded from every pre-commit hook by `.pre-commit-config.yaml:2`
  and sits outside Tailwind's `@source` scope, so the import cannot rewrite the
  specification's Unicode or move `static/css/tailwind.css`. Both were checked.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; this commit
  touches no Python.
- Forward guidance: WP-2 is still next and its scope is unchanged. Before
  starting it, read `docs/design/RECONCILIATION.md` section 5 -- the theme
  marker resolves to `data-theme="dark"` on `<html>` at `templates/base.html:2`,
  which satisfies daisyUI, the WP-2 contract and the specification at once.
  WP-3 must measure label and hint widths at 9-11px: there is no narrow
  JetBrains Mono, so the clipping regression the specification warns about is
  live here rather than avoided. `F-B21-4` must not be closed by ruling on all
  four screens at once; each is decided at the WP that builds it.

### 2026-08-21 - Dependency advisories filed as F-B21-3 (side-task)

- Scope: filed one finding from the first Quality Gate run that exercised the
  Tailwind steps. No runtime code and no dependency changed.
- Plan vs implementation: pushing `bc9ba80` ran the gate for the first time
  since WP-1 landed. It passed, and "Verify committed Tailwind CSS" succeeded
  on Linux, so the committed digest reproduces in CI and the WP-1 platform
  detection works there. The same run's `pip-audit` step reported 115
  advisories across 12 packages and exited 1 without failing the gate, which
  is its documented `continue-on-error` disposition. Investigation found six
  packages in `requirements.txt` that nothing imports, including a
  `pypdf`/`pdf2image`/`pillow` cluster. The owner asked whether those served
  the JPEG export; they do not. That export is client-side `html2canvas` in
  `static/js/results.js:178-266`. All six unimported packages entered in the
  initial `0ea2313` commit rather than with a feature. The owner has poppler
  installed locally, so `pdf2image` can run on the development machine, but
  not in production: the `Dockerfile` is a bare `python:3.13-slim` with no
  system-package installs.
- Deviations: none. No dependency was upgraded or removed. Dependency changes
  are code and belong in a code batch, not a docs commit.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Quality Gate run
  32444711411 passed in 1m12s.
- Forward guidance: WP-2 is next. `F-B21-3` records a suggested shape --
  split runtime from developer requirements, drop unimported packages, then
  upgrade the outbound HTTP libraries -- but the owner has not ruled on it.

### 2026-08-20 - F-B21-2 deferred to the locked WP-2 remedy (side-task)

- Scope: corrected one finding that prescribed a fix competing with an
  owner-locked decision. No runtime code changed.
- Plan vs implementation: `F-B21-2` was filed from the WP-1 review without
  reading `BATCH21_DEFINITION.md:186-204`, which already prescribes WP-2's
  remedies. It told a reader to layer Bootstrap; the locked decision instead
  moves the Bootstrap link into a per-page block so each template loads
  exactly one framework stylesheet, removing the collision rather than
  re-ordering it. The finding now defers to the definition and says so. Its
  `data-theme` seam likewise points at the locked `theme.js` dual-write. The
  defect descriptions are kept, because they record why those decisions
  matter; only the competing prescription is gone.
- Deviations: none. The batch definition was not edited. A finding must not
  outrank the batch contract, so the finding moved.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next and closes `F-B21-2`. Check a finding against
  the active batch definition before filing a remedy in it.

### 2026-08-20 - README roadmap reconciled with FINDINGS (side-task)

- Scope: removed one stale roadmap item that contradicted an open finding, and
  retitled the finding it pointed at. No runtime code changed.
- Plan vs implementation: the README roadmap still asked a reader to
  consolidate Bootstrap onto one CDN provider. `F-B20-3` already records that
  remedy as dead, because Batch 21 removes Bootstrap at WP-8 and resolves the
  split by elimination. Two live documents disagreed, and the README is the one
  a newcomer reads first. The roadmap line now names the real disposition.
  `F-B20-3`'s heading described the dead remedy rather than the defect; it now
  reads "Bootstrap loads from two CDN providers". Every citation of it is by
  F-ID, so no reference breaks.
- Deviations: none. Three other roadmap items were checked and left alone.
  The integration test (`F-LOAD-2`) and the `ENTRY_BATCH_RE` tightening
  (`F-DOCSYNC-1`) have not been done, so their unchecked boxes are correct.
  `tests/test_routes.py` reaches the three endpoints only under mocks, and no
  test covers the whole chain. `parser.py:37` is unchanged.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next. Note `F-DOCSYNC-1` may overstate the problem
  -- the current regex already requires the parenthesised `(Batch N WP-N)`
  form, so a failing test should justify the change before anyone makes it.

### 2026-08-20 - Root hygiene: config verdict recorded, banners withdrawn (side-task)

- Scope: recorded the root config-file verdict in the document that owns
  deploys, and corrected one false self-description. No runtime code changed.
- Plan vs implementation: the owner rejected the audience-banner scheme in the
  local root-hygiene plan. Its two-label vocabulary restated what the
  `AGENTS.md` Document Roles table and `docs/AGENT_DOC_MAP.md` already own,
  and its rule that no file claims both audiences is false for files that are
  both. `DEVELOPMENT.md` was the worked example: it called itself explanatory
  documentation only while owning the Frontend Asset Build commands that other
  documents cite. That sentence is narrowed rather than banner-stamped.
  `DEPLOY.md` gains "Where the config lives"; `fly.toml` gains a pointer
  comment above its empty `[build]`; the README tree names the co-location
  instead of leaving `Dockerfile` uncommented.
- Deviations: the banner steps, the `AGENTS.md` audience rule, and the README
  audience split are **withdrawn, not deferred**. Verification also corrected
  an earlier claim that the banner would strand agents:
  `BATCH21_DEFINITION.md:448-450` already binds WP-2 through WP-7 to run
  `tailwind_build.py`, so no agent depended on `DEVELOPMENT.md` for the
  obligation. Only the fuller procedure, including watch mode and the worktree
  caveat, lives there.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next. Nothing from this side task blocks it.

### 2026-08-20 - Batch 21 WP-1 test-count authority addendum (side-task)

- Scope: records the post-WP-1 measured suite inventory for docsync's
  same-day source ordering. No runtime implementation changed.
- Plan vs implementation: the new current-batch WP-1 entry remains the owner
  of toolchain evidence. This live addendum supplies its later full-suite
  result because same-date side-task entries take precedence over
  current-batch entries in docsync's authority ordering.
- Deviations: none.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: owner review of the WP-1 commit remains first; the
  root-hygiene side task follows, then WP-2.

### 2026-08-20 - Agent document map added; HANDOFF_PROMPT trimmed (side-task)

- Scope: the owner asked for an instructional that lets an agent other than
  Claude navigate the documentation set -- including the audit and SWE
  documents -- and understand why each document exists. Added
  `docs/AGENT_DOC_MAP.md` and registered it in the `AGENTS.md` Document Roles
  table. Documentation only; no runtime code changed.
- Plan vs implementation: as planned. The map routes rather than summarises.
  It names the owner of each fact and links to it, so it adds no copy that a
  later edit can contradict (`AGENTS.md` Anti-duplication rule). Sections:
  the one-owner rule and why it exists, where to start, the document groups,
  the human-facing documents, how to read an audit, how to read a finding,
  seven navigation traps, the pre-change gates, and the tie-break order when
  two documents disagree. It sits under `docs/` rather than the repository
  root, because a twelfth root Markdown file would worsen the problem the map
  exists to solve, and it is marked optional and outside the bootstrap set so
  it does not inflate the cold-start read. 264 lines, under the 370-line
  largest peer in `docs/`.
- Audit guidance is the part with no prior owner: the charter to report to
  findings to log-entry lifecycle, why a retired charter is kept, why a dated
  report is never edited in place, and that a report is a measurement of one
  day rather than current truth. The SWE report's own "Owner review" section
  is cited as the worked example of an appended correction.
- Owner request mid-task, and the reason it changed shape: delete
  `HANDOFF_PROMPT.md`. That is not a documentation-only delete. The file is
  pinned into the commit gate at `scripts/docsync/cli.py:26` and
  `scripts/docsync/integrity.py:51`. `cli.py:88` loads every
  `LIVE_DOCUMENT_PATHS` entry through `_read_lines`, which raises `SyncError`
  on a missing file and maps to exit 2, and the `doc-state-sync-check` hook
  runs `--check` with `always_run: true`. Deleting the file alone would fail
  every commit in the repository until `cli.py`, `integrity.py`,
  `tests/conftest.py:149` and four assertions in
  `tests/test_docsync_integrity.py` changed with it. The owner chose to trim
  the file instead of deleting it.
- Trim: `HANDOFF_PROMPT.md` went from 66 to 46 lines. Removed three sections
  that carried no requirement of their own and only named an `AGENTS.md`
  section: validation gates, commit discipline, and anti-patterns. Every
  subject those sections named survives in the new opening paragraph, checked
  against the removed text one item at a time per Anti-Pattern 12. The two
  unique parts are untouched: the post-read verification and the handoff
  checklist. Section numbers were replaced with names, so no later edit can
  leave a stale "Section 4)" citation behind. `DEVELOPMENT.md:74-78` already
  claimed the file held only those two things, so the trim closes an existing
  drift rather than creating one.
- Deviations: two stale claims corrected in the same commit, both left behind
  by the 2026-08-20 audit commits. `BATCH21_DEFINITION.md:3` still read that
  the F-SWE-1 audit "comes next" after PR #170; the audit ran on 2026-08-20.
  The `README.md` documentation tree still described
  `docs/SWE_AUDIT_CHARTER.md` as "Standing audit scope and method"; the
  charter is retired. The same tree gained a row for the new map, because it
  enumerates the contents of `docs/`.
- Validation: `pytest -q` **590 passed** (unchanged; no code touched);
  `pre-commit run --all-files` all hooks passed;
  `python scripts/doc_state_sync.py --check` exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning. Every tracked Markdown file
  was checksummed before and after the pre-commit run and compared, because
  that hook has twice reverted files nobody edited, once into a commit.
- Forward guidance: unchanged. The F-SWE-2 fix is still the next action. It
  is a code commit and it moves the test count off 590.
- **Later same-day test-count addendum:** the F-SWE-2 current-batch entry above
  records the subsequent code change and owns its implementation details. Its
  full-suite result was `pytest -q` -- **591 passed**. The earlier 590 result
  in this entry remains point-in-time evidence; this pointer supplies the
  later same-date count to docsync's live-side-first authority order.

### 2026-08-20 - F-SWE-1 SWE principles audit executed (side-task)

- Scope: executed `docs/SWE_AUDIT_CHARTER.md` against `1994673`, whose
  runtime code is byte-identical to `main` at `bb187ae` -- the five commits
  between them are documentation only. Read-only audit; all 130 cells
  (13 graded modules x 10 principles) filled in one session. Report:
  `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`.
- **Verdict: migration blocked by F-SWE-2**, per charter Section 6 -- a
  net-new correctness defect in `orchestrator.py`, which WP-7 modifies.
  `orchestrator.py:70-71` builds the listening-year window from naive
  datetimes, so the window shifts by the local offset of the host: measured
  at five hours on this machine. It is the same defect F-B19-6 fixed in
  `heatmap.py`; `git show --stat ccb000f` confirms that fix touched heatmap
  and its tests only, and the twin was never revisited. Production is
  unaffected because the Fly.io container runs UTC. Every non-UTC host is
  affected, including local dev, so local checks of album results have been
  running against a shifted window.
- **Owner decisions, same day.** F-SWE-2: fix, do not waive -- it lands as
  its own commit before WP-1 and moves the test count. F-SWE-3: rescoped
  from P1 to P2, and the audit was partly wrong. It filed the
  `No Spotify match` reason as a user-facing mislabelling; that framing does
  not hold, because thousands of Last.fm-scrobbled albums genuinely have no
  Spotify release, so the label is accurate for the ordinary case. What
  survives is narrower and independent of labelling: `spotify.py:67-68`
  marks every non-200, non-429 response terminal, so a 500 ends the attempt
  loop after one try while `SPOTIFY_SEARCH_RETRIES` is 3. The related UI
  need -- the unmatched modal and page should say plainly that an album had
  no Spotify match -- is already WP-7 scope
  (`BATCH21_DEFINITION.md:297-308`), not new work.
- Grades: 74 A, 28 B, 8 C, 2 D, 18 N/A. The weakest principle is Fail Fast,
  holding five of the eight C grades and only two A grades across 13
  modules. The failures share one shape: the code catches a problem and
  discards what the problem was.
- Six net-new findings, F-SWE-2 to F-SWE-7. Every one of the ten C and D
  cells carries a disposition; two map to open F-B20-2 rather than becoming
  new entries. Each finding was verified by running the code, not by reading
  it -- the TTL renewal, the Spotify retry bypass, the unreachable API-key
  check and the heatmap misattribution were each reproduced.
- Test vacuity: measured, not judged. Each of the 81 top-level functions in
  the graded modules was replaced in turn with a raise, in a copy of the
  tree outside the repository, and the 237 runtime tests were run against
  each mutation. Every deletion was caught, so there is no vacuity finding.
- Broad catches: all 17 were read in context and judged, which F-MAS-4 never
  did. Fifteen are justified. The two that are not are both in F-SWE-5, and
  both are catches that report a cause they never established.
- F-B21-1 keeps its recorded P1 disposition. The gate covers net-new
  findings only, so the audit did not re-triage it and it does not block
  WP-1.
- Deviations: F-SWE-1 moved from the P1 section to Resolved this batch, and
  F-SWE-3 from P1 to P2 -- the charter asked for neither move, but leaving
  either where it was would have made the section heading false.
- **Tooling hazard hit twice, worth recording.** `pre-commit run --all-files`
  stashes unstaged changes and restores them afterwards. That cycle reverted
  files nobody had edited: first `docs/architecture/development-cycle.md`
  and `top-albums-sequence.md` back to a pre-PR-#171 state, then `PLAYBOOK.md`
  itself back to a pre-PR-#170 state, dropping this very entry. Every hook
  reported `Passed`. The first was caught at staging because AGENTS.md
  requires staging by name; the second reached commit `a34c57f` and was
  repaired in the follow-up commit. Check `git status` before and against
  after every `--all-files` run, and compare file mtimes against the files
  you actually edited.
- Validation: `pytest -q` -- 590 passed, unchanged, as expected for a
  docs-only change. `pre-commit run --all-files` and
  `doc_state_sync.py --check` both pass, the latter with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: apply the F-SWE-2 fix as its own commit, then WP-1. Root
  hygiene stays deferred until after WP-1.

### 2026-08-19 - Batch 21 preflight: F-SWE-1 charter and WP gates amended (side-task)

- Scope: owner preflight review before WP-1, raised as six criticisms of
  `docs/SWE_AUDIT_CHARTER.md` and an eight-row table of weak WP gates. Two
  verification agents checked every claim against the files before any edit.
  All six charter criticisms held. Two of the batch claims did not.
- Verification of the owner report:
  - Confirmed: the charter named five docsync modules when the directory has
    seven (`integrity.py`, 474 lines, unnamed) and its LOC figure was stale
    for the five it did name; the differential baseline was a closed ID list
    omitting F-B21-1, F-DATA-1, F-WORKTREE-3/4/5, F-DOCSYNC-6/7 and never
    referenced `FINDINGS_ARCHIVE.md`; A/B/C/D was defined nowhere in the
    repository; the matrix was 190-210 cells with explicit permission to cut
    modules; no severity or stop condition existed anywhere, so finishing the
    audit was the same as passing it; and the post-Batch-21 frontend audit
    was permissive ("can"), not required.
  - Corrected: the excluded set is a proper subset of what Batch 21 rewrites,
    not equal to it -- WP-7 modifies `routes.py` and `orchestrator.py`, which
    are in scope, so those grades also expire at WP-7. The charter never
    addressed that; it now does.
  - Refuted: the claimed AGENT_NOTES-versus-definition contradiction over the
    drift hook. `AGENT_NOTES.md` requires the CI-fetch *decision* at WP-1;
    the definition deferred the *hook* to WP-8. Both could hold. The real
    defect was quieter -- no WP-1 criterion required the decision to be
    recorded, so nothing enforced it.
- Root cause neither side had named: the batch validation gate is three
  Python commands, and pre-commit excludes `static/` and `templates/`. A work
  package could rewrite every template and stylesheet with a fully green
  gate, in a batch that is nothing but template and stylesheet rewriting.
- Plan vs implementation:
  - Charter: 13 graded modules enumerated by name (130 cells, `__init__.py`
    excluded by a stated empty-module rule); docsync and `scripts/dev/`
    excluded with reasons rather than left ambiguous; provenance block
    naming branch, SHA and clean state; symbol-based hotspot discovery
    replacing hardcoded line numbers and counts; baseline widened to the
    whole finding corpus plus the archive and every report from 2026-02 on;
    A/B/C/D rubric with the B/C line defined as exception-versus-pattern;
    Boy Scout window fixed at commits since the February audits; a
    resolved-finding branch for C/D cells; a migration-blocking severity
    policy with a one-line verdict required in the report; an instruction to
    retire the charter at close. The budget escape hatch is withdrawn.
  - Batch 21: new `scripts/dev/frontend_gate.py` added as a fourth gate
    command at WP-2 and grown one page per WP, covering stylesheet
    isolation, computed theme tokens in both themes, theme persistence,
    self-hosted font loading, CSV/JPEG export assertions, and headline
    wrapping. The `tailwind-css-drift` hook moved from WP-8 to WP-2, with
    the `always_run` / `pass_filenames` requirement that AGENT_NOTES gap 2
    had already identified and the definition had not carried. Targeted
    criteria added to WP-3 (keyboard and touch reachability for the CSS-only
    hints, label associations, validation parity), WP-4 (both state machines
    including retryable and non-retryable failures), WP-7 (split into a
    backend contract commit and a UI commit), and WP-8 (required frontend
    and accessibility audit, deterministic Bootstrap-removal grep, recorded
    lint disposition). Browser floor documented; `.dark-mode` retirement
    given an owner; criterion 9 reconciled with the per-WP docsync check.
  - FINDINGS.md: F-STYLE-1 (prose legibility, explicitly never a gate) and
    F-STYLE-2 (docstring convention, the black/flake8 line-length
    disagreement, and the unwritten Ruff plan) added. F-SWE-1 corrected --
    it claimed the charter scoped "Python only until Batch 21 ships", a
    commitment the charter never made.
  - AGENTS.md: the F-ID source-tag list named five tags while nine are in
    use. `SWE`, `WORKTREE`, `DATA` and `STYLE` added, and the list is now
    declared complete so the next coined tag gets documented.
- Deviations: the drift hook landed at WP-2 rather than the WP-1 the owner
  proposed. WP-1 changes no template, so nothing consumes the compiled CSS
  until WP-2; WP-2 is the first point where drift can ship.
- Independent review of the amended charter, same day, and the fixes it drove:
  - The migration gate did not say whether it covered existing findings. Read
    the wide way, F-B21-1 blocks WP-1 today -- a resource-release defect in
    `orchestrator.py`, which WP-7 modifies. The gate is now scoped to net-new
    findings in terms, F-B21-1 is named as the case that forces the
    distinction, and an audit that thinks an existing finding should block
    must recommend rather than act.
  - The A/B/C/D rubric graded by frequency ("one place is B, several is C")
    while its own table graded by cost. One leak can be C; five contained
    exceptions can stay B. Rewritten to grade cost, not count. The
    "when torn, over-raise" instruction is deleted -- it contradicted
    Section 4's rule that the audit's value is not volume.
  - Resolved and no-action findings shared one rule. Split: a recurred
    resolved defect earns a new finding; an unchanged no-action rationale
    does not; materially changed assumptions do, explaining the delta.
  - Provenance permitted grading a dirty tree, which no SHA can reproduce.
    A clean worktree is now required before grading starts.
  - The hotspot command was `awk '...{...}'` -- a placeholder that could not
    run, and a poor Python parser besides. Replaced with a tested `ast`
    script in a new Section 5c, deliberately at the left margin: a heredoc
    terminator indented inside the numbered list fails with
    `IndentationError`, which was verified rather than assumed.
  - Boy Scout used `git log`, which lists commits without showing what they
    left behind. Now `git log -p`, with an instruction to read the patches.
  - "Weakest principle repo-wide" overclaimed: the audit excludes the
    frontend, both script directories, and tests as graded subjects. Scoped
    to the audited runtime modules.
  - Cell arithmetic hardcoded 130 in three places while Section 3 allowed the
    principle count to change. All three now derive from the live count.
  - One review point was stale, not wrong: the claim that WP-8 defines no
    frontend principles audit. It does, in this commit's parent -- the
    reviewer was reading `origin/main`, because the amendment is committed
    locally and deliberately unpushed.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --all-files` --
  all hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  root BATCH warning.
- Forward guidance: execute the amended charter against current `main` and
  publish the migration verdict before WP-1 starts. The verified root-hygiene
  plan (audience banners, README tree, DEPLOY.md) is deferred until after
  WP-1 by owner decision; its line numbers will need re-checking.

### 2026-08-19 - PR #171 round-8 thread fixed: push authorization in the cycle diagram (side-task)

- Scope: one unresolved Codex thread on `docs/architecture/development-cycle.md`,
  raised again by an owner-side human peer on the grounds that this diagram
  purports to govern agents. Checked against the ruleset before editing. Valid.
- Verification: the diagram had a single unconditional edge,
  `Authorize -->|Review-fix commit on an open PR| PR`. `AGENTS.md:234-242`
  grants that standing exception to Claude Code and Codex sessions only and
  says in terms that it does not extend to GitHub Copilot task sessions or
  their subagents, Jules, or any other agent. An agent reading the canonical
  diagram would therefore push a review-fix commit that the ruleset requires
  it to pause on.
- Plan vs implementation: the decision node now carries three edges instead of
  two. WP and batch commits pause in any session; the direct path is labelled
  Claude Code or Codex only; every other agent routes to the same pause. Added
  prose naming `AGENTS.md` as the owner of the rule, and recording the three
  actions that always need explicit instruction whatever the session --
  force-pushes, history rewrites, and anything targeting `main` -- plus the
  Copilot platform-tool requirement at `AGENTS.md:243-244`, neither of which
  the diagram had carried.
- Deviations: none. No code changed.
- Validation: the edited diagram was validated before it was written --
  `valid = true`, type `flowchart`. `pytest -q` -- **590 passed**.
  `doc_state_sync.py --check` -- exit 0 with the expected root BATCH warning.
- Forward guidance: next action unchanged -- the F-SWE-1 audit, then WP-1. A
  preflight amendment to the charter and the Batch 21 WP gates is agreed and
  pending; see the owner decisions recorded with it.

### 2026-08-19 - PR #171 round-7 threads fixed (side-task)

- Scope: the three unresolved Codex threads left on `3d15849` after the
  diagram audit. All three are P2 and all three were checked against the
  source before any edit. All three are correct.
- Verification and fixes:
  - `top-albums-sequence.md` drew `Close connection` unconditionally, but
    `process_albums` closes inside `if conn` (`orchestrator.py:603-604`), so
    the no-connection branch never closes anything. Wrapped in an `opt DB
    connected` block.
  - The same diagram claimed the browser never posts `results_complete` on an
    error payload. `loading.js:209-229` shows only the retryable branch stays
    on the page; a non-retryable error waits three seconds and calls
    `redirectToResults()`, which does post. Split the branch by `retryable`
    and routed the non-retryable case to the processing-error page.
  - `FINDINGS.md` F-B21-1 stated `MAX_ACTIVE_JOBS` is 5 as an absolute.
    `config.py:31` reads it from the environment with 5 as the default, and
    the literal contradicted F-LOAD-1 in the same file. Reworded to name 5 as
    the default and tie the failure count to configured capacity.
- Deviations: none. No code changed; F-B21-1 stays open and unfixed, because
  it is a code change for a code batch.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --files` on both
  edited files -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected root BATCH warning. The edited Mermaid diagram was validated
  through the Mermaid Chart validator: `valid = true`, type `sequence`.
- Forward guidance: the next action is unchanged -- the F-SWE-1 audit, then
  Batch 21 WP-1.

### 2026-08-15 - PR #171 round-6 threads fixed and all five diagrams audited (side-task)

- Scope: the two unresolved Codex threads on `00c0adb`, both on the Top Albums
  sequence. A prior GLM-5.2 session had left uncommitted diagram edits and a
  list of findings, then stopped before it finished. I checked the two threads
  and every edit that session made against the code, then audited all five
  diagrams with three independent verification agents.
- Verification of the two threads: both are correct. `fetch_top_albums_async`
  groups, normalizes, and thresholds the albums before it returns
  (`orchestrator.py:112-116`), so all of that runs before the empty-result
  check at `orchestrator.py:784`. `process_albums` writes to the cache only
  under `if conn and new_metadata_rows` (`orchestrator.py:591`).
- Verification of the prior session: three of its six edits were wrong. It put
  the hit/miss partition inside the DB-connected branch, but the code
  partitions with or without a connection (`orchestrator.py:567`). It drew
  `cleanup_expired_cache()` as a call to `repositories.py`, but that helper
  comes from `utils.py` (`orchestrator.py:40`). It put the total Spotify match
  failure after the store step, but the check runs first
  (`orchestrator.py:824` before `orchestrator.py:842`).
- Plan vs implementation:
  - Top Albums sequence: rewrote the background-task block and the browser
    block. Grouping now sits before every downstream branch. Persistence is
    conditional and records `db_cache_persisted`. The partition sits outside
    the DB branch. New: the connection close and its `finally` ordering
    against `SpotifyUnavailableError`, the `get_job_context` read behind the
    total-match-failure check, the six `results_complete` outcomes, the
    `/progress` 404, and the two unhandled-exception states.
  - Heatmap sequence: added the housekeeping calls, the page-count stats, the
    5% and 80% progress writes, and the unhandled-exception path. Rebuilt the
    render block: the client requests `/heatmap_data` only at 100%, so the 202
    is a narrow race that restarts polling, not a peer alternative.
  - Development cycle: split the merged fast path so the actionability stop
    applies to comment jobs only, added the push-authorization gate that
    `AGENTS.md` requires between commit and PR, and dropped the E2E claim that
    no rule file makes.
  - Runtime diagram and `docs/ARCHITECTURE.md`: named the eight nodes that
    import `config.py`, corrected the arrow-semantics paragraph, and repointed
    the module-graph reference to SESSION_CONTEXT Section 4 alone.
  - Both structural diagrams passed their audit with no change to the graphs.
- Deviations: the prior session said the fix needed a full rewrite of the
  parallel block. It did not. The corrections are local, but they reach more
  branches than that session touched. The audit also found a real code gap and
  it is recorded as F-B21-1 rather than fixed here: `background_task` and
  `heatmap_task` build the event loop outside the `try`, so a failure there
  leaks a job slot. No production code changed in this commit.
- Validation: all four changed diagrams pass Mermaid validation, checked
  against the exact text now in the files. `pytest -q` -- **590 passed**, 3
  known warnings. `pre-commit run --all-files` -- all hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: push, then reply to the two threads and resolve them.
  PR #171 stays open until the owner says otherwise.

### 2026-08-15 - PR #171 round-5 review threads remediated (side-task)

- Scope: three new Codex threads on `37ca4a9` -- one on the development-cycle
  diagram and two on the Top Albums sequence. All three were verified against
  the code before any edit and all three were valid.
- Verification:
  - `AGENTS.md` L29-44 defines the review-comment fast path (fetch the thread
    first, stop if not actionable, else read only the scoped files), but the
    development-cycle diagram routed every review finding through the full
    bootstrap gates. The diagram and the rules it documents were written in
    the same PR and disagreed.
  - `_fetch_and_process()` stores an empty result, marks progress 100%, and
    returns before pre-slicing, cache access, or Spotify enrichment when
    `filtered_albums` is empty. The Top Albums sequence sent every successful
    page fetch into those stages.
  - `process_albums()` catches `_batch_lookup_metadata()` exceptions, records
    `db_cache_warning`, treats every album as a miss, and continues to Spotify
    (possibly persisting via the open connection). The diagram's connected
    path presented lookup as unconditional and its unavailable path said
    persistence was skipped.
- Plan vs implementation: the development-cycle diagram now branches on
  review-finding/comment-job before full bootstrap (fetch thread, stop if not
  actionable, else read scoped files); the Top Albums sequence now stops after
  an empty filtered set and adds a fail-open cache-lookup-error continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the empty-filtered-set and fail-open lookup
  paths.
- Validation: both updated diagrams pass Mermaid validation and open in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this remediation, then resolve the three
  threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 final four review threads remediated (side-task)

- Scope: the four remaining unresolved review threads on `e73540d` -- two
  Codex path-repointing reports and two Codex Top Albums sequence reports.
  All four were verified against the code and the moved files before any
  edit and all four were valid.
- Verification:
  - `docs/superpowers/plans/2026-08-11-pr-170-remediation.md` still cited
    `docs/history/GUARD_HARDENING_2026-08-11.md` and
    `docs/history/REPOSITORY_SYNTHESIS_2026-08-11.md`, both moved to
    `docs/history/reports/` by commit `5865c55`. The links resolved to
    nonexistent files.
  - `docs/history/definitions/BATCH9_DEFINITION.md` pointed twice to
    `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`, and
    `BATCH10_DEFINITION_2026-02-21.md` pointed to the old
    `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md` and
    `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md` paths. All three reports
    now live under `docs/history/reports/`. These are definition-to-report
    references, not exempt point-in-time citations, so they must be repointed.
  - `_fetch_and_process()` returns immediately after `set_job_error` when
    `fetch_metadata["status"] == "error"`, while a `partial` status records
    `partial_data_warning` and continues. The diagram drew an unconditional
    transition from page fetching into grouping.
  - `_fetch_spotify_misses()` raises `SpotifyUnavailableError` when token
    acquisition fails with no cache hits, caught in `_fetch_and_process` as
    `set_job_error("spotify_unavailable"); return []` -- no merge or store.
    The diagram's no-cache-hits branch rejoined the unconditional merge/store
    steps.
- Plan vs implementation: repointed the four report paths in the remediation
  plan and the two batch definitions; the Top Albums sequence now branches on
  Last.fm status (terminal error vs partial-success-with-warning) and
  terminates after the no-cache-hits token failure while retaining the
  cached-success continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the Last.fm error/partial paths and the
  no-cache-hits token failure.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve the
  four threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 final two Codex threads remediated (side-task)

- Scope: the two remaining unresolved Codex threads on `3508c48`, both on the
  Top Albums sequence diagram. Both were verified against the code before any
  edit and both were valid.
- Verification:
  - `_get_db_connection()` returns `None` when `DATABASE_URL` is unset,
    asyncpg is unavailable, or connection attempts fail; `process_albums`
    then sets a `db_cache_warning` stat and skips lookup, cleanup, and
    persistence, so every album becomes a miss. The diagram presented those
    three cache operations as unconditional.
  - `_fetch_spotify_misses()` sets `partial_data_warning` and returns without
    searching when Spotify token acquisition fails and cache hits exist, so
    the pipeline completes successfully with cached albums only; it raises
    `SpotifyUnavailableError` only when no cache hits exist. The diagram sent
    every miss through search and grouped the token failure with the terminal
    path.
- Plan vs implementation: the Top Albums sequence now branches on DB
  availability before the cache lookup and branches the Spotify token-fetch
  failure into a success-with-warning path (cached albums only) versus the
  terminal `spotify_unavailable` path.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the DB-disabled fallback and the partial-cache
  continuation.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview; the tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve both
  threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 post-push review round remediated (side-task)

- Scope: two new visible Codex threads and all five suppressed Copilot
  comments on commit `11c9885`. The seven reports described six distinct
  defects because both reviewers found the omitted heatmap admission check.
  An independent review found one adjacent README polling claim during the
  required sibling sweep.
- Verification and loop check:
  - `routes.py` confirms that heatmap requests reject a missing username,
    unavailable validation service, and unknown user before cleanup or slot
    acquisition. `loading.js` and `heatmap.js` confirm that both browsers poll
    while their background tasks run. `docsync.logic` confirms tagged entries
    rotate to per-batch logs while untagged entries rotate to the side archive.
  - Git blame assigns all three affected diagram owners to the preceding
    review-fix commit. The omitted validation and rotation branch plus both
    serialized pollers are therefore self-inflicted extraction defects, not
    newly reached backlog. The older date headers became stale when this PR
    later changed the live dashboard and findings state without refreshing
    them. README's claim that `heatmap.js` polls `/heatmap_data` predated this
    review round; the script and Batch 18 records show that it polls
    `/progress` and fetches `/heatmap_data` only after completion.
- Plan vs implementation:
  - The tooling graph now distinguishes tagged rotation into
    `docs/history/logs/` from untagged rotation into `docs/logarchive/`.
  - The heatmap sequence now shows required-input and Last.fm user-existence
    validation, including terminal 400, 404, and 503 responses before job
    admission.
  - Both request sequences now use Mermaid parallel blocks for background
    processing and progress polling. SESSION_CONTEXT and FINDINGS carry the
    current 2026-08-15 update date.
  - README now distinguishes heatmap progress polling from the completed-data
    fetch.
- Deviations: no production behavior changed and no tests were added. Existing
  tests already cover heatmap validation responses and task lifecycle behavior.
- Validation: all three edited diagrams passed Mermaid validation and opened
  in preview; each tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass.
- Closure boundary: the pushed remediation commit and its passing Quality Gate
  define done for PR #171. Do not start another patch-review-patch cycle from
  later automated comments; a future agent may scrutinize them during a
  separately scoped deep sweep, but they are not automatic blockers for this
  documentation PR. Do not merge PR #171 without separate owner instruction.
- Forward guidance:
  - Execute the already-chartered Python-only F-SWE-1 audit, then start Batch
    21 WP-1. Keep architecture streamlining found by that audit separate from
    the frontend strangler unless it directly blocks a named WP acceptance
    criterion.
  - At WP-1, decide how CI obtains and caches the pinned, digest-verified
    standalone Tailwind and daisyUI artifacts. At WP-8, make the CSS drift hook
    `always_run` with no filenames or narrow the top-level pre-commit exclude;
    otherwise it cannot see `static/`. Add focused CSS, JS, and HTML checks
    before close-out because those paths currently have no lint coverage.
  - Treat `ruff` as an optional, separately measured Python-tooling migration,
    not a frontend prerequisite. It overlaps Black, isort, autoflake, and
    flake8, would require owner-approved dependency changes, and should land
    only with explicit parity criteria after the F-SWE-1 findings are known.

### 2026-08-15 - PR #171 review findings verified and remediated (side-task)

- Scope: all eight unresolved Codex and Copilot threads on PR #171, checked
  against the current code, tests, repository rules, and sibling documentation
  before any edit. A separate two-axis review found no additional verified
  spec or standards defect in the cumulative `origin/main...HEAD` diff.
- Plan vs implementation:
  - Seven factual comments were confirmed: partial heatmap data is successful
    with a warning; cache hits still write JOBS state; both task entry points
    release their slot unconditionally; `start_job_thread` releases the slot
    before re-raising while the route deletes the new job; README's dotted-edge
    legend omitted dispatch; and `orchestrator.py` was not the import-graph top.
  - The eighth comment was also confirmed against the complete new-file rule:
    the 499-line `docs/ARCHITECTURE.md` exceeded its existing `docs/` peer cap.
    It is now a 49-line index preserving all five section anchors. Five focused
    files under `docs/architecture/` own one diagram each and are 47-101 lines.
  - README, SESSION_CONTEXT, and the Mermaid instruction now point to the
    focused owners without duplicating diagrams. Gitignored `.mmd` sources were
    used for validation and preview only.
- Deviations: no production behavior changed and no tests were added; existing
  regression tests already cover partial-data continuation, startup slot
  release, and unconditional task cleanup.
- Validation: all six published diagrams passed Mermaid validation and opened
  in preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit
  run --all-files` -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0
  with the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit the review remediation, push only with owner
  authorization, then post one batched reply and resolve the eight threads.

### 2026-08-14 - F-DATA-1 filed under P2; stale skill name corrected (side-task)

- Closes the two items the previous entry left as forward guidance.
- `F-DATA-1` self-labelled `Status: open (P2)` while sitting as the last
  entry under the P1 heading. Fixed by moving the `## P2` heading above it
  rather than relocating a 65-line block -- same result, far less churn, and
  the finding's own text is untouched.
- `DEVELOPMENT.md` still named the PR triage skill `gemini-pr-triage`; it was
  renamed `pr-bot-triage`. Real drift, not a snapshot, so it is corrected
  rather than preserved.
- **Scoping correction from the owner, recorded because an agent got it
  wrong today:** `DEVELOPMENT.md` is not an agent document. It is absent from
  docsync's live-document set and from the AGENTS.md bootstrap reading list,
  and belongs with `README.md` as human-facing methodology writing. A line
  added to `AGENT_NOTES.md` earlier the same day pointed agents at it for the
  skills-are-local decision; that line now states the decision directly
  instead. Batch definitions may still direct an agent to *write* a build
  step into it -- writing to it is in scope, treating it as a source of
  operating rules is not.
- Plan vs implementation: these two were dropped from the Phase 5 scope
  reduction and then reinstated by the owner, since both sit in working
  documents rather than in the archive the reduction was about.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0. `check_worktree_alignment.py`
  -- exit 0. Verified exactly one `## P2` heading remains and that `F-MAS-4`
  is still the last P1 entry.
- Forward guidance: nothing outstanding from the remediation. Next is the
  F-SWE-1 audit, then Batch 21 WP-1.

### 2026-08-14 - Batch 21 tooling mapped to its work packages (side-task)

- Scope: `AGENT_NOTES.md` gains a map from the installed skills and MCP
  servers to WP-1 through WP-8, written before WP-1 rather than discovered
  during it. Every entry was verified against the live machine and repository
  on the day rather than carried forward from the plan's older table.
- Structural fact recorded so nobody hunts for what is not there:
  `BATCH21_DEFINITION.md` has **no per-WP acceptance criteria**. It carries
  one batch-level list of 9 plus a per-WP validation gate that every WP runs
  identically, so the map keys on the WP and names the criteria each serves.
- Four separate skill sources are installed and their names collide -- `tdd`
  and `test-driven-development` are different files from different upstreams,
  as are `diagnosing-bugs` and `systematic-debugging`. The map says which
  source each comes from, because naming the wrong one loads the wrong file.
- Seven gaps recorded, all verified. Three of them converge on WP-8 and one
  of those has to be decided at WP-1: the pre-commit top-level exclude covers
  13 directories including `static/` and `templates/`, so the planned
  `tailwind-css-drift` hook could never fire as a file-scoped hook and must
  use the `always_run` pattern; CI has no Node and no Tailwind binary, so the
  headless-Linux fetch is unsolved; and no CSS, JS or HTML hook exists at all,
  leaving the files eight WPs rewrite unreachable by two mechanisms at once.
- Two plan claims were corrected against the live state. The exclude covers
  **13** directories, not the 12 the plan's Phase 6 still said -- an earlier
  phase had already found 13 and the later section was never updated. And the
  `skills-lock.json` drift (22 locked, 20 present) is bookkeeping only: both
  absent skills are supplied by the superpowers plugin, so it is not the
  capability gap it looks like.
- One claim was verified rather than assumed after a false negative:
  `workflow_dispatch` is on `origin/main` and usable. An initial check
  reported it missing, which turned out to be Git Bash rewriting the
  `rev:path` argument on Windows rather than anything about the repository.
- Plan vs implementation: as planned, with the MCP inventory re-enumerated
  live as the plan instructed rather than copied.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0 (expected root warning for the
  active `BATCH21_DEFINITION.md`). `check_worktree_alignment.py` -- exit 0.
- Forward guidance: this closes the post-merge remediation. Next is the
  F-SWE-1 principles audit per `docs/SWE_AUDIT_CHARTER.md`, whose report
  belongs under `docs/history/reports/`, then Batch 21 WP-1. The three open
  PR #170 review threads and the four ruleset settings remain owner-side.

### 2026-08-14 - docs/history one-off documents collected under reports/ (side-task)

- Scope: the 26 loose files at the top of `docs/history/`, which had grown
  into a flat pile beside the three organised subdirectories. Organisation
  only -- the owner scoped this to moving files, not revising them.
- 25 moved into `docs/history/reports/` with `git mv`. Not one of their
  bodies was edited.
- `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` deliberately stayed at the
  top level. It is the Batch 14 "Moved:" tombstone whose only purpose is to
  resolve references to that legacy path, so relocating it would defeat it.
  `FINDINGS.md:115` records the same disposition.
- One folder rather than a split by kind. Three Markdown links exist between
  these files, and they connect an audit, a changelog, a performance summary
  and a refactor plan -- four different kinds. Any by-kind split breaks all
  three and forces edits to files that were explicitly out of scope. A single
  folder keeps every relative link resolving untouched.
- References repointed in the live documents only: `AGENTS.md`,
  `DEVELOPMENT.md`, `FINDINGS.md`, `.claude/SESSION_CONTEXT.md` and
  `docs/SWE_AUDIT_CHARTER.md`. Two of those are forward-looking and mattered
  most: `FINDINGS.md` F-SWE-1 and the charter's output contract both name
  where the pending SWE principles audit must write its report, and both now
  name `reports/`. `AGENTS.md` documentation-touch rule likewise.
- Dated records were left as written, including the ones that now cite a
  path that moved: the archived batch definitions and logs,
  `docs/logarchive/`, the superseded plan under `docs/superpowers/plans/`,
  and PLAYBOOK Section 4's own earlier entries. A point-in-time record
  rewritten to match a later reorganisation stops being a record. This is
  the same reasoning already applied to `SESSION_CONTEXT_REFERENCE.md`.
- Consequence, stated so it is not later mistaken for rot: paths cited inside
  `docs/history/reports/*` and inside the dated archives may name the
  pre-2026-08-14 flat layout. `DEVELOPMENT.md` now says so where it describes
  the archive.
- `DOC001` scans only the live documents, so the archive's internal citations
  never entered the gate; the repointing above was still required because
  five of the moved paths were cited from documents it does scan.
- Plan vs implementation: reduced on owner direction. The planned content
  remediation -- linking the two orphans, repointing three dangling
  `EXECUTION_PLAYBOOK_2026-02-11.md` cites, annotating seven dead `app.py`
  line references in `PERFORMANCE_TIMING.md`, a completion note on
  `BATCH8_REFACTOR_PLAN.md`, collapsing the overlapping 2026-01-04
  performance documents, and a `docs/history/README.md` index -- was dropped
  as out of scope for an organisation pass.
- Deviations: none beyond that reduction.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0 (expected root warning for the
  active `BATCH21_DEFINITION.md`). `check_worktree_alignment.py` -- exit 0.
  Every repointed path was confirmed to resolve on disk.
- Forward guidance: `FINDINGS.md` F-DATA-1 still sits under the P1 heading
  while labelling itself P2, and `DEVELOPMENT.md` still calls the
  `pr-bot-triage` skill by its old `gemini-pr-triage` name. Both were part of
  the dropped remediation and remain open.

### 2026-08-14 - F-WORKTREE-5 closed: count branch candidates before filtering (side-task)

- Scope: the last open guard defect, reported independently by Codex in PR
  #170 round 5 and by Copilot in round 6, and left open across both.
- Defect: `parse_batch_branch` filtered candidates through
  `is_display_safe_ref` and only then counted them. Because that allowlist is
  deliberately narrower than Git's ref rule, a rejected candidate can still
  name a real branch, so a Section 3 declaring two branches -- one of them
  non-ASCII -- had one side discarded and reported the survivor as expected.
  The predicate decides whether a value may be rendered, not whether it exists.
- TDD: the regression test failed first with `DID NOT RAISE`, using
  `wip/b\xe4tch-21` as the second value -- Git accepts non-ASCII letters in a
  ref name, and the escape keeps the test source ASCII. Then counted distinct
  candidates before any filtering and moved the display-safety filter after
  the conflict check, where it only decides what may be rendered.
- Anti-vacuity: both orderings are load-bearing. Deleting the
  count-before-filter fails the new test; deleting the display-safety filter
  fails three cases of
  `test_a_branch_value_cannot_repaint_the_diagnostic_line`.
- Also corrected the stale justifying comment in the source, and added a
  correction note to `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`,
  whose Step 3 still prescribed the defective ordering in prose. Leaving that
  in place would have let the plan teach the defect back into the code.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `check_worktree_alignment.py` -- exit 0.
- Forward guidance: F-WORKTREE-5's two PR #170 threads can now be answered and
  resolved. F-WORKTREE-3 and F-WORKTREE-4 remain open by decision.

### 2026-08-14 - architecture diagrams corrected and given one owner (side-task)

- Scope: newly integrated Mermaid material that contradicted the code, plus
  the three older diagram copies that disagreed with it and each other.
- The central defect, in both sequence diagrams: `create_job` was drawn with
  no preceding `acquire_job_slot`. The real order is the reverse
  (`routes.py:460` then `:478`, and `:570` then `:582`) and is a fail-fast:
  the slot is taken first and the request rejected outright if none is free.
  An agent reconciling code to the diagram would allocate a `JOBS` entry and
  then reject, leaking an orphan job on every throttled call until TTL expiry.
  README already stated the correct order, so the repository contradicted
  itself. The same inversion was present in the synthesis document.
- Nine further defects, each verified against source: `worker.py` drawn as
  importing `orchestrator` and `heatmap` when both import *it* (the dispatch
  is real but runtime-only, through a callable `routes.py` injects); a
  `cache.py -> utils.py` edge that does not exist in any form; the cache
  hit/miss partition attributed to `cache.py` when it happens in
  `orchestrator.py:561-578`, and cannot happen in `cache.py`, which never sees
  the full candidate set; expiry cleanup drawn as cache-internal when the
  orchestrator calls it; `start_job_thread` given the wrong signature; the
  heatmap response typed as a rendered page rather than JSON 202; and missing
  `routes -> orchestrator`, `routes -> heatmap`, `routes -> utils` and
  `repositories -> errors` edges.
- Ownership after this change: `README.md` keeps one high-level diagram and
  now declares its arrow semantics, which was the root defect the wrong
  diagrams shared -- a dependency edge and a control-flow edge were drawn
  identically and read as the same claim. `docs/ARCHITECTURE.md` owns every
  detailed diagram. SESSION_CONTEXT Section 5 keeps a corrected compact
  summary and points there for detail. The synthesis Section 5 diagrams were
  removed with a note recording why, and its Section 6 tooling diagram
  migrated with one edge corrected: `doc_state_sync.py` imports only
  `docsync.cli`, so the fan-out had been attributed one level too high.
- Renamed the incoming doc from a dated filename to `docs/ARCHITECTURE.md`.
  It is a living reference, and `docs/` root holds durable documents while
  `docs/history/` holds dated ones; a date in the name would have become
  false at the first correction.
- Every diagram was validated before being written, per
  `.github/instructions/mermaid.instructions.md` Rule 1. This caught a real
  parse failure: a `;` inside a sequence-diagram message terminates the
  statement. The incoming document had escaped it as `&#59;&#59;`, which
  parsed but rendered as visible garbage and dropped a `%`. Removed the
  semicolon rather than escaping it.
- Now tracked, with the disposition rule recorded in the previous entry:
  `docs/ARCHITECTURE.md`, the two `.github` instruction files (converted to
  ASCII, with a ScrobbleScope scoping section reconciling their `.mmd` rule
  against this repository's tracked-Markdown layout), the corrected synthesis,
  and the PR #170 remediation plan under a superseded header naming the four
  ways it must not be executed.
- Plan vs implementation: the plan called for deleting `sequenceDiagram.mmd`
  as a duplicate. Kept instead and moved to `diagrams/`, with `*.mmd`
  gitignored -- deleting the only `.mmd` would contradict Rule 5 of the
  instruction file being tracked in the same change.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed**. All six diagrams return
  `valid: true` from the Mermaid validator. `doc_state_sync.py --check` --
  passed with the expected root-BATCH warning.
- Forward guidance: `docs/history/` still needs an index and its dead
  references repointed, and `AGENT_NOTES.md` still needs the tooling map.

### 2026-08-14 - dependency-graph and pytest-config claims corrected (side-task)

- Scope: four documentation claims that contradict the code, plus the
  ordering statements left stale by the PR #170 merge.
- Dependency graph, SESSION_CONTEXT Section 4. `heatmap.py <- config` was
  false -- `heatmap.py` imports lastfm, repositories, utils and worker, and
  reaches config only transitively through those. The same wrong chain was
  repeated in the `heatmap.py` module docstring, so fixing one source alone
  would have left the other. `app.py <- routes` omitted the `config` edge at
  `app.py:143` (`ensure_api_keys`), which exists only under the `__main__`
  guard; recorded with that scope rather than as an unconditional import.
  Added `dev/dev_start.py`, documented in Section 3 but absent from the
  graph. Every other edge was re-derived from the imports and is correct.
- Pytest config, SESSION_CONTEXT Section 7. The claimed
  `asyncio_mode = "strict"` is not configured anywhere: `pyproject.toml`
  contains only `pythonpath = "."`, and no `pytest.ini`, `setup.cfg` or
  `tox.ini` exists. `git log -S` shows the key was never in the file, so
  this was wrong when written rather than drift. The same sentence appears
  in `docs/history/SESSION_CONTEXT_REFERENCE.md`, which is left as written:
  that file is a labelled 2026-02-23 snapshot of SESSION_CONTEXT.md, and a
  snapshot that silently corrects its original stops being a snapshot.
- Ordering. PR #170 merged, so PLAYBOOK Section 3, BATCH21_DEFINITION,
  SESSION_CONTEXT Section 1 and FINDINGS all still said it must land first.
  All four now name the merge and give the F-SWE-1 audit as the next action.
  The batch-open baseline in BATCH21_DEFINITION gained its date so the 390
  is not misread as current.
- README cross-reference. "See `AGENTS.md` for the full dependency graph"
  pointed at a file that has no graph; repointed to SESSION_CONTEXT
  Section 4, which is where it lives.
- AGENTS.md gained a note that WT004 after a merge is expected and routine,
  with the tree-equality precondition that separates it from a real
  divergence. Without it the guard's stop-and-escalate remediation reads as
  alarming for what is now a per-merge occurrence.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0.
  `doc_state_sync.py --check` -- passed with the expected root-BATCH warning.
- Forward guidance: the architecture diagrams still contradict the code they
  describe, most seriously by drawing `create_job` with no preceding
  `acquire_job_slot`. That is the next side-task, followed by F-WORKTREE-5.

### 2026-08-14 - post-merge realignment and untracked-artifact disposition (side-task)

- Scope: restore a green bootstrap after PR #170 merged, and give every
  untracked path an explicit disposition. Two gates were failing at once.
- Gate 1, the worktree guard. `main` requires linear history and its ruleset
  permits only squash and rebase merges, so the merge rebased the branch and
  left `wip/batch-21` 9/9 diverged from `origin/main` with byte-identical
  trees (`dedd776` both) -- `ERROR WT004`, exit 1. Verified the two tree
  hashes matched and `git diff HEAD origin/main` was empty, then reset the
  branch onto `origin/main` and force-pushed with lease under the owner
  approval the guard's remediation requires. No file changed; only the
  commit objects the branch points at. This state will recur after every
  merge, since it follows from the ruleset rather than from any mistake.
- Gate 2, the integrity gate. The `setup-matt-pocock-skills` skill had
  appended an `## Agent skills` section to `AGENTS.md` pointing at a new
  untracked `docs/agents/`, which produced three `DOC001` errors and would
  have failed `pre-commit` and CI. Reverted. The skill followed its own
  file-selection rule (no `CLAUDE.md` exists, so `AGENTS.md` was its
  fallback); the mismatch is that it treats `AGENTS.md` as an appendable
  conventions file while this repository treats it as a governed ruleset.
- Disposition: untracked files went from 73 to 5, all five of which are
  slated for tracking in later side-tasks. Ignored with recorded reasons:
  `.agents/` and `skills-lock.json` (vendored from two upstream skill
  repositories, already drifting -- the lock names 22 skills, the tree holds
  20); `docs/agents/` (unedited vendor templates describing a layout this
  repository does not use); and `*.mmd` (Mermaid authoring scratch, kept
  separate so no diagram has a second copy free to drift).
- Note for future audits: `git status` collapses directories, so the set
  read as 8 paths and was actually 73 files. Use `-uall`. Separately,
  `git check-ignore -v <path>/` reports a spurious match against a blank
  `.gitignore` line for any path given a trailing slash -- a nonexistent
  directory and a fully tracked one both "match" it.
- Plan vs implementation: as planned. `sequenceDiagram.mmd` was slated for
  deletion as a duplicate; kept instead and moved to
  `diagrams/top-albums-sequence.mmd`, because
  `.github/instructions/mermaid.instructions.md` requires diagrams be
  written to `.mmd` files. Ignoring the pattern satisfies both that rule and
  single-source-of-truth.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0
  (WT010 only). `doc_state_sync.py --check` -- passed with the expected
  root-BATCH warning.
- Forward guidance: the four documents still describe PR #170 as pending;
  correcting them is the next side-task. Then the architecture diagrams,
  which contradict the code they describe, and F-WORKTREE-5, which two
  reviewers filed independently and which still has two open threads.

### 2026-08-12 - PR #170 round 6; reviewed, cross-references repointed (side-task)

- Scope: two visible review comments and four suppressed Copilot comments
  against the round-5 head `d8d3e0d`; one visible finding was already
  recorded, the other was a doc-currency correction.
- The F-WORKTREE-5 restatement (Copilot `r3766306027`). Valid mechanism:
  `parse_batch_branch` filters candidates through `is_display_safe_ref`
  before counting them, so a Section 3 naming one display-safe and one
  display-unsafe branch resolves to the safe one instead of raising the
  conflict error. Already recorded in the exact head being reviewed --
  `d8d3e0d` created F-WORKTREE-5 with the fix prescribed (count candidates
  before filtering). Reversing a deliberate round-2 ordering decision in a
  review round was declined then and still is; the finding stays the owner
  of that decision. Acknowledged on the thread rather than patched.
- The hardening-doc cross-references (Codex `r3766308198`). Verified valid
  against the live tree: the dated-entries pointer claimed all three
  `2026-08-11` entries lived in PLAYBOOK Section 4, but the round-1 and
  PR #169 round-6 entries had rotated to the monolith archive, and the
  open-gap list omitted F-WORKTREE-5, which `d8d3e0d` had just added.
  Repointed the pointer at the live plus archive locations and added
  F-WORKTREE-5 to the gap list, with the recorded-in commit named.
- Suppressed comments: the plan-doc observation (the Step 3 snippet
  prescribes filter-before-count) is a true statement about a historical
  implementation plan and is left as written -- the plan documents the
  as-shipped ordering and F-WORKTREE-5 carries the forward fix; the README
  badge claim (588 vs 589) was already resolved on the reviewed head, which
  shows 589.
- Plan vs implementation: doc-only change; no code and no test changed.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `doc_state_sync.py --check` -- passed with
  the expected root-BATCH warning.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1.
  F-WORKTREE-5 remains the owner's call to reverse or leave.

### 2026-08-12 - PR #170 round 5; a normalizer undid the check above it (side-task)

- Scope: three findings on the round-4 head, two acted on and one recorded.
- The one that mattered. `actual_branch` was normalized with a bare
  `strip()`, which removes Unicode whitespace, and Python counts U+00A0 as
  whitespace while Git accepts it in a ref name. So `wip/batch-21` plus a
  trailing U+00A0 -- a genuinely different ref -- folded onto the expected
  branch, matched the comparison, and produced no wrong-branch verdict at
  all. On a clean checkout that is an exit-zero run reporting alignment while
  HEAD sits on another branch. Round 4 had just closed the display half of
  this class; the normalizer one line above quietly reopened the identity
  half.
- Worth recording because the first reproduction attempt said the bug was not
  there. On this host the locale codec is cp1252, so the UTF-8 bytes arrive
  mojibaked as a non-whitespace character that survives `strip()` and trips
  the comparison by accident. Under a UTF-8 locale -- Linux, and therefore CI
  -- the decode is clean and the fold happens. A Windows-only check would
  have cleared it.
- Plan vs implementation: only Git's record terminator is trimmed now. Git
  rejects CR and LF inside a ref name, so trimming exactly those cannot
  damage a legitimate value, while every other codepoint reaches the
  comparison and the render check intact.
- The second finding was a stale count in a place the round-4 sweep did not
  know existed: the README project-structure tree carries its own per-file
  test inventory, separate from the SESSION_CONTEXT table. That sweep was
  scoped to the literal total and missed it. All 35 rows were checked this
  time, not just the row reported; one was wrong.
- Deviations: the third finding is real and not fixed. Section 3 candidates
  are filtered for display safety before the conflict check, so a document
  naming one safe and one unsafe branch resolves instead of failing closed.
  Reversing that needs its own reasoning rather than a review-round patch,
  and the round-2 justification for it is itself wrong, so it is recorded as
  F-WORKTREE-5 rather than patched here.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Re-verified end to end under a UTF-8 locale against a real trailing-U+00A0
  branch: WT003 now fires where the run previously reported the wrong branch
  as aligned.
- Forward guidance: unchanged -- land PR #170, then F-SWE-1, then Batch 21
  WP-1.

### 2026-08-12 - PR #170 round 4; the third rendered ref answered to no rule (side-task)

- Scope: one finding, reported independently by both reviewers against the
  current head, and confirmed from the code before either review was read.
  `actual_branch` was the last of the three refs these diagnostics render that
  no rule governed.
- Why it outranks its predecessors. The previous two rounds closed this class
  for the ref that comes from PLAYBOOK prose; this one comes from
  `git symbolic-ref --quiet --short HEAD`, so the attacker surface is a branch
  name rather than a document. Enumerating every `issue()` call in
  `scripts/dev/` by walking the syntax tree -- rather than trusting either
  review's list -- gives six codes that print it: WT000, WT003, WT004, WT005,
  WT006 and WT010. The dangerous one is WT000, which is only reached when the
  run is otherwise clean: between batches with no dirty files the guard exits
  zero and prints a subject the branch name controls, on the line the design
  document says a less capable agent may stop on.
- What Git actually permits, established with `git check-ref-format` and real
  branches in a disposable repository rather than assumed: ESC, DEL, CR, LF
  and the ASCII space are all rejected, so a fixture built from them describes
  a checkout that cannot exist. U+00A0, U+2028, U+202E, U+200B, U+3000 and
  U+0085 are accepted, and `symbolic-ref` returns them verbatim.
- A second, narrower fact decided the fixture. `run_git` calls
  `subprocess.run(..., text=True)` with no encoding, so Git output is decoded
  with the locale codec. Under cp1252 U+00A0 survives and pads the line while
  U+2028 arrives mangled; under a UTF-8 locale U+2028 survives and splits the
  diagnostic into two. Only U+00A0 asserts the same thing on both, so it is
  the payload the tests use.
- Plan vs implementation: `branch_label` joins `base_ref_label` in the
  diagnostics module, so all three rendered refs now answer to
  `is_display_safe_ref`. The four render sites call it; the wrong-branch
  comparison keeps the raw Git value, because labelling there would compare a
  display string against a branch name. Labelling happens at render time, not
  collection time -- the snapshot goes on naming whatever Git reported.
- Deviations: the predicate had no direct test, and a mutation matrix showed
  three of its four clauses were vacuous -- deleting the `..` rule, the `//`
  rule, or the trailing `/`, `.` and `.lock` rule each left the whole suite
  green. That is why this change adds predicate tests it did not strictly
  need: without them the new docstring's claim that those boundaries are
  covered would have been false. Every clause now fails at least one test,
  and each member of the suffix tuple fails exactly one.
- `_worktree_guard_inspection.py` remains over its directory peer cap
  (F-WORKTREE-4, accepted); this change is net zero lines there and adds no
  new deviation.
- Validation: `pytest -q` -- **588 passed** with the 3 existing
  aiohttp/Python 3.13 warnings, up 12 in one existing file, so the module
  count stays 35. All 10 pre-commit hooks pass. `doc_state_sync.py --check`
  -- exit 0 with the expected root-BATCH warning. Verified end to end
  afterwards: a real branch carrying U+00A0 was created in a scratch
  repository and the shipped CLI rendered `unnamed branch` and `worktree`,
  with no payload byte anywhere in its output.
- Forward guidance: this clears the last open PR #170 item. Land the PR, then
  F-SWE-1, then Batch 21 WP-1.

### 2026-08-12 - PR #170 round 3; the gate was ordered behind what it gates (side-task)

- Scope: two document defects found by an independent clean-room audit of the
  live repository, both still live on the current head. Neither changes code
  and neither moves the test count.
- The first is the wider one. PLAYBOOK Section 3 opened with the F-SWE-1 audit
  as the next action while its own closing sentence said PR #170 must land
  before that audit begins. Section 3 is the canonical bootstrap instruction,
  so an agent reading it top-down would start the audit against the guard and
  docsync sources this PR still changes. SESSION_CONTEXT Section 1 and
  FINDINGS already carried the correct order; `BATCH21_DEFINITION.md` carried
  a third one, naming WP-1 as next with no mention of either gate. All three
  now agree.
- The second is a false statement in the round-2 entry below. "Four cases were
  added and three trimmed" is a net increase of one, which cannot explain an
  unchanged count, and it does not describe what happened: the change swapped
  a single parametrized case for another -- the DEL payload for the U+00A0
  one -- leaving six test functions and fourteen cases on either side.
  Corrected in place rather than annotated. A dated entry is a point-in-time
  record, but that protects a claim which was accurate when written and later
  went stale; it does not preserve one that was wrong at the time. That
  distinction is the same one already applied to archived citations.
- Deviations: none.
- Validation: `pytest -q` -- **576 passed** with the 3 existing aiohttp/Python
  3.13 warnings; no test changed. All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
- Forward guidance: the remaining PR #170 item is the `actual_branch` display
  gap both reviewers reported against this head. It lands next, then the PR,
  then F-SWE-1, then Batch 21 WP-1.

### 2026-08-11 - PR #170 round 2; a denylist next door to an allowlist (side-task)

- Scope: six findings from a dispatched adversarial review of the round-1
  commit -- one blocking, four should-fix, one nit. All six were reproduced
  independently before any code changed. All six were valid.
- The blocking finding: the round-1 class `[^\x00-\x20\x7f-\x9f`]+` is an
  ASCII denylist, so everything from U+00A0 upward passed. Reproduced through
  the real parser: U+00A0, U+3000, U+2000, U+202E and U+200B all resolved to
  an `expected_branch`. A value padded with U+00A0 renders in WT003 exactly
  as one padded with the ASCII space that class excluded -- the same attack
  round 1 claimed to have closed, in a different codepoint. U+200B is worse
  than cosmetic: it renders as nothing, so WT003 demands a move to the branch
  already checked out, with no exit from that state.
- Root cause, and the part worth keeping: the guard already had the right
  control. `_SAFE_BASE_REF_RE` in `_worktree_guard_diagnostics.py` is an
  allowlist, and `base_ref_label` applies it to the other ref these same
  diagnostics interpolate. Round 1 wrote a second, weaker, differently shaped
  check in another module instead of reusing it. Two values reaching one
  rendered line answered to two rules, and only one of them had been thought
  through. This is a DRY failure that produced a security defect, not a
  style complaint.
- Plan vs implementation: the shared rule is now `is_display_safe_ref`,
  extracted from the body of `base_ref_label` so both call sites share one
  definition rather than one copying the other. `BRANCH_RE` returns to
  delimiting a candidate; `parse_batch_branch` discards candidates that fail
  the predicate before the duplicate check, so an unusable value never
  becomes a branch. No dependency-graph change: lineage already imported from
  diagnostics.
- Corrections to the round-1 entry below, which stands as written because
  dated entries are point-in-time records. Two claims in it are false. The
  class was never "what Git actually permits in a ref name": Git rejects
  `..`, `^`, `:`, `?`, `*`, `[`, `\`, `@{`, a `.lock` suffix and a trailing
  `/`, all of which that class accepted, and Git accepts non-ASCII names the
  new alphabet rejects. The current alphabet is deliberately narrower than
  Git's rule because the property enforced is display safety, not ref
  validity. Separately, "all four documented Section 3 branch styles" names a
  set that does not exist; the suite pins three, and the fourth shape the
  pattern admits is documented nowhere.
- Deviations: replacing the denylist with one shared allowlist collapsed the
  test distinctions round 1 had established. Under a single control, DEL is
  indistinguishable from the escape sequence, and U+3000, U+202E and U+200B
  from U+00A0 -- every mutation that leaks one leaks its whole group. Adding
  a case per vector would have reinstated the near-duplicate rule breach the
  review had just cleared, so the parametrization keeps one representative
  per boundary the allowlist draws and names the rest in the docstring. The
  line-break case now carries no other rejected character, which is the fix
  the review asked for and which round 1 documented as a knowing breach
  rather than repairing.
- Validation: `pytest -q` -- **576 passed** with the 3 existing
  aiohttp/Python 3.13 warnings; the count is unchanged because the
  parametrization swapped one case for another -- the DEL payload was
  replaced by the U+00A0 one -- and no test function was added or removed.
  All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Every previously bypassing codepoint was re-run against the shipped parser
  and now resolves to no branch, while `wip/batch-21` still resolves and the
  live PLAYBOOK still parses.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  narrative of this remediation, including why each round produced the next,
  is written up in `docs/history/GUARD_HARDENING_2026-08-11.md` rather than
  as new rules, since three rounds of evidence is a thin basis for amending
  a ruleset every agent follows.

### 2026-08-11 - PR #170 round 1; the forgery class was wider than the line break (side-task)

- Scope: three findings from two independent reviewers on the open PR -- two
  from Copilot review `4902230481`, raised against the current head rather
  than an earlier one, and one from Codex (`r3754609766`). All three were
  reproduced before any code changed, and all three were valid.
- The fix shipped earlier the same day was incomplete. Excluding CR and LF
  stopped a forged *second line*, but WT003 renders the captured value into a
  terminal, and an escape sequence repaints the existing line without ever
  needing one: `ESC[2J ESC[H` clears the screen and redraws a clean verdict.
  DEL erases what was already written, and padding spaces push a fake result
  across the visible line. Reproduced directly: the previous pattern returned
  an `expected_branch` still carrying a raw `\x1b`. The commit message claimed
  PLAYBOOK prose could no longer forge guard output, and that claim was
  broader than the fix behind it.
- Plan vs implementation: rather than enumerate control characters, the value
  is now restricted to what Git actually permits in a ref name -- no control
  characters, no DEL or C1 range, no spaces. That subsumes the line-break case
  instead of sitting beside it, and every rejection still fails closed to
  WT002. Verified against all four documented Section 3 branch styles and the
  live PLAYBOOK, so the narrowing costs no legitimate form.
- The second finding was a test-quality defect in the same commit. The three
  parametrized line endings were near-duplicates: `parse_batch_branch` splits
  and rejoins the section, so LF, CRLF, and CR arrive at the pattern already
  normalized to LF, and deleting `\r` from the pattern left all three green.
  That is the prohibited near-duplicate pattern, shipped in the very change
  that added an adversarial test. Replaced with one parser-level line-break
  case plus three cases that survive normalization.
- The third finding was a blast-radius miss in the previous commit, and the
  more instructive one. Step 3 of the guard implementation plan still
  prescribed the original `[^`]+` value class as a normative instruction, so
  the plan remained a working recipe for rebuilding the vulnerability the
  production fix had just closed. The earlier commit had edited that same
  plan file -- for the `debug` parameter -- without sweeping it for the
  pattern actually being changed. The snippet now carries the shipped class
  plus a note saying why it must not be relaxed, so the reason travels with
  the instruction rather than living only in production code.
- Deviations: the first attempt at the DEL case did not isolate what it
  claimed. Its payload also contained spaces, so the space rule blocked it and
  a mutant permitting DEL still passed. Found by running a mutation matrix
  over the exclusion ranges rather than by rereading the test, and corrected
  by removing the spaces from that payload. Recorded because it is the same
  defect class the finding reported, reintroduced while fixing it.
- Validation: `pytest -q` -- **576 passed** with the 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Each new case was
  mutation-checked: permitting the space boundary leaks only the padding case,
  permitting the DEL/C1 range leaks only the DEL case, and the previously
  shipped pattern leaks all three non-newline cases. The retained line-break
  case adds no unique range coverage and is kept only as the single
  parser-level case the review asked for.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  lesson generalizes the one recorded below: a fix aimed at the reported
  instance rather than the class leaves the class open, and here the reported
  instance was a line break while the class was anything a terminal
  interprets.

### 2026-08-11 - PR #169 round 6 landed after the merge; the guard could be made to lie (side-task)

- Scope: four findings from Copilot review `4877974867`'s successor,
  `4888134055`. The review was submitted 2026-08-08 04:38 UTC against head
  `6ed9d7c`; the PR merged at 07:57 UTC with no commit in between. All four
  were re-verified as still live on `main` before any work started -- the
  merged head is tree-identical to `main`, so nothing had superseded them.
- Why one of them mattered more than its "suppressed" label suggested:
  `BRANCH_RE` captured `[^`]+`, a negated class that matches newlines, while
  Section 3 is parsed as one newline-joined block. A backticked Branch value
  spanning lines was therefore captured whole, and WT003 prints that value
  verbatim. Ordinary PLAYBOOK prose could forge a second diagnostic line in
  the guard's own output -- the output the design document says a less
  capable agent can stop safely on, knowing only the exit status and the
  remediation text. Reproduced before fixing, for all three line endings.
- Plan vs implementation: the label and value are now pinned to one line
  (`[ \t]*` for the separator, `[^`\r\n]+` for the value). A rejected value
  leaves no branch to resolve, which `classify_lineage` already reports as
  WT002 -- so the fix fails closed rather than silently skipping the branch
  comparison. That mattered to the choice: making malformed metadata mean
  "no branch declared" would have repeated round 4's defect, where an
  ambiguous state switched a check off instead of blocking on it.
- The other three were documentation currency: the `inspect_worktree`
  interface in the guard plan omitted the shipped keyword-only `debug`
  parameter, and SESSION_CONTEXT and FINDINGS both carried a
  `Last updated: 2026-08-06` that predated their own 2026-08-07 content.
  PLAYBOOK Section 3 was additionally stale on its own terms: it still
  directed the reader to merge PR #169, three days after the merge, and
  carried a pre-merge caveat about a missing Quality Gate run that now
  exists and is green for `5bc6294`.
- Deviations, recorded rather than taken silently:
  - **`wip/batch-21` was realigned with an owner-authorized force-push.**
    It sat 39 ahead / 39 behind `origin/main` with an identical tree -- the
    WT004 rebase-merge artifact this guard was built to catch, and the first
    live instance of it. `git cherry` confirmed zero commits without an
    equivalent patch on `main`, so the reset was lossless. Done before any
    work so the Pre-Work Checklist could pass honestly rather than be waived.
  - The session ran in a linked worktree under `.claude/worktrees/`, already
    covered by the `.claude/*` ignore rule, reusing the primary checkout's
    sole `.venv` through the qualified paths the guard printed. This is the
    first live exercise of the F-WORKTREE-2 path: the guard reported WT000
    and resolved all three tools from the primary checkout.
- Validation: `pytest -q` -- **575 passed** with the 3 existing
  aiohttp/Python 3.13 warnings (572 before; the three new cases are the
  line-ending variants). All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Mutation-checked: the new test was watched failing on all three variants
  before the pattern was narrowed, and the existing bold-label and
  prose-tolerance cases still pass, so the pattern was not over-narrowed.
- Submitted as PR #170 against `main` after owner instruction to push and
  open one. Both Quality Gate triggers fired on the new head, `push` and
  `pull_request` -- the dropped-dispatch gap recorded against `8463ca4` did
  not recur.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  process lesson is narrower than round 5's: every remediation round here is
  triggered by a push, so a review submitted after the final push falls
  outside all of them and reaches the merge unswept. This entry records the
  gap; it does not create a rule, because round 5 established that a rule
  living in a dated entry has no force. Whether the pre-merge check belongs
  in the canonical ruleset is an owner decision, still open.

### 2026-08-07 - PR #169 round 5; contradicting a claim is itself a change (side-task)

- Scope: five suppressed findings, all valid, all self-inflicted. Four were
  caused by round 4 recording F-WORKTREE-4 without sweeping for the claims
  that finding contradicts; the fifth by round 4 repointing a resolver name at
  one site while an identical literal sat 300 lines earlier in the same file.
- Root cause, and the reason it recurs: the pre-push sweep had no pinned base,
  so each round swept only its own commits and inherited nothing. Round 2
  diagnosed this and fixed it by sweeping `git diff origin/main...HEAD`, but
  recorded the fix only in a dated log entry, which this repository treats as
  non-normative. Rounds 3 and 4 duly regressed. Both rules are now in the
  pre-push checklist rather than in a log entry: pin the sweep base to the
  branch, and treat recording a deviation as a change whose blast radius must
  be swept -- grepping the vocabulary of the property being deviated from, not
  the words of the new finding, which appear nowhere else.
- Plan vs implementation: five affirmative peer-cap claims repointed across
  the plan, the spec, and FINDINGS; the DOC003 description corrected to
  describe the check that shipped rather than a bare regex the implementation
  deliberately avoids; the interface inventory repointed to the authority API.
- Deviations, logged rather than silently taken:
  - **Round 3 shipped without a Section 4 entry.** Commits `14b3eac` and
    `1c783a9` carried no dated log entry, breaching the missing-log-entries
    anti-pattern in the very PR that ships a documentation-integrity gate.
    Recorded here retroactively rather than back-dated: round 3 fixed seven
    findings across the plan, the spec, AGENTS, and FINDINGS, and narrowed
    F-WORKTREE-3 after re-verifying its remaining clauses.
  - `_latest_test_count_from_entries` is left in place though no production
    caller remains, because deleting it rewrites eight test call sites --
    a refactor, not a review fix. Tracked as F-DOCSYNC-7.
- Peer-agent correction: a concurrent session had staged a partial fix that
  introduced two new false statements -- a docstring naming `_build_candidates`,
  which exists nowhere in the repository, and an attribution of the
  `_cross_validate` removal to round 2 when `a3c923f` did it in round 1. Both
  corrected here. Worth recording because it is the same defect class the
  round was fixing, produced independently by a different writer.
- Validation: `pytest -q` -- **572 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning.
- Forward guidance: merge. Round 5 was entirely documentation currency, and
  the remaining backlog is scoped as a hygiene batch rather than another round.

### 2026-08-07 - PR #169 round 4; the integrity gate could be switched off (side-task)

- Scope: eight findings from review round 4 -- one visible, seven suppressed.
  Six valid and fixed, one declined as an accepted deviation, one refuted.
- The material defect was self-inflicted by round 2. Making ambiguity an
  explicit state fixed the renderer but left `None` meaning two things at the
  integrity boundary, and DOC006 skips its comparison on `None`. Reproduced
  before fixing: with an unambiguous authority a stale dashboard value raises
  DOC006; with an ambiguous newest entry the same stale value passes and the
  gate exits 0. Writing one ambiguous log entry therefore disabled the check
  that exists to catch exactly that state.
- Plan vs implementation: the resolver now returns `TestCountAuthority`
  (count plus whether the newest entry was ambiguous) so the reason travels
  with the value instead of each consumer re-deriving it. DOC006 treats an
  ambiguous authority beside a named numeric field as blocking. Its
  remediation no longer names PLAYBOOK unconditionally, because the authority
  may be a rotated archive entry, and says to record an unambiguous result
  when there is no number to agree with. The status block distinguishes "no
  bold count" from "several counts without a `pytest -q` result", which sends
  the reader to the entry that caused it rather than to a missing number.
- Deliberate non-action: three guard files now exceed their directory peer
  caps (256/236 for the collector, 270/184 and 192/184 for two guard test
  modules). All were compliant before the review rounds and crossed while
  fixing confirmed defects. Splitting them was declined -- the rule prevents
  unmaintainable monoliths and none of these approaches that -- and recorded
  as F-WORKTREE-4 rather than left implicit, since Section 3 had described
  the guard as peer-sized and that had stopped being true.
- Refuted: the review claimed the SESSION_CONTEXT per-file table sums to 573
  against a stated 568. It sums to 568 across 35 rows, verified two ways and
  reconciled row-by-row against `pytest --collect-only` with no drift. First
  incorrect finding in four rounds; the others were all valid.
- Validation: `pytest -q` -- **572 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Both new behaviours were
  mutation-checked: neutralizing the ambiguity branch in the gate and in the
  renderer each fails its own regression.
- Forward guidance: merge. Four rounds in, the findings are now generated by
  the previous round's fixes rather than by the original work, and this round
  produced the first refuted item -- both are diminishing-returns signals.

### 2026-08-07 - PR #169 round 2; ordering, discovery, and a diff-derived sweep (side-task)

- Scope: thirteen findings from Copilot review 4877974867 -- one visible,
  twelve suppressed, all verified valid. Eleven were caused by the previous
  round's own fixes, so the round was treated as a remediation of that
  remediation rather than as new review traffic.
- Cause, established before fixing: the round-1 checklist was generated from
  the reviewers' findings, which by construction described the pre-change
  tree. Nothing was ever swept against the branch's own diff, so every
  citation that round 1 invalidated survived. Three local patches to one
  ordering question produced three interacting defects for the same reason.
- Plan vs implementation:
  - Test-count authority. Three findings were one defect: authority was
    decided by scanning three sources independently and reconciling the
    winners, so each rule was restated per source and their interactions were
    never modelled. Replaced by one total ordering -- clamped date, then
    source precedence -- walked once. Ambiguity became an explicit state
    rather than `None`, so it suppresses older candidates instead of falling
    through to them; a live side-task entry now outranks a same-date archived
    one; and the legacy sole-bold-count pass walks the same ordering, so such
    a count survives rotation. Heading dates are clamped to a running minimum
    within each source because position, not the date, is the authority on
    recency there -- which is what the existing append-convention tests
    already pinned.
  - Guard discovery. `--git-common-dir` names shared Git metadata, not a
    checkout, so deriving the primary root from its parent is wrong under
    `git clone --separate-git-dir`; the collector now asks Git directly with
    `worktree list --porcelain`. On POSIX a file without an execute bit is
    not a runnable tool, but existence was the whole test, so WT000 could
    advertise unusable paths; the doubles hid it by building tools with
    `touch()`. The base ref is no longer consulted at all between batches,
    where the contract says ancestry is not enforced.
  - Citation sweep, derived from `git diff origin/main...HEAD` rather than
    from the findings list. That derivation is what found the class the
    findings only sampled: nineteen further copies of the broken
    primary-checkout derivation sat in per-step snippets across both
    implementation plans, and the documented `resolve_venv` signature had
    drifted from production. Also repointed the WT-code location claim, both
    test inventories, and F-MAS-3.
- Deviations: added `workflow_dispatch` to `.github/workflows/test.yml` (two
  lines, urgent, logged here rather than deferred). GitHub created no Quality
  Gate run for the push of `8463ca4` although the push event was delivered
  and recorded, Actions was enabled, the workflow was active, its triggers
  matched, no path filter or skip-ci marker applied, and Copilot's own
  workflow ran on that same SHA eight seconds later. Evidence points to a
  one-off dispatch drop rather than a configuration fault, so the trigger is
  a durable escape hatch, not the fix. It cannot help this PR -- GitHub
  resolves dispatchable workflows from the default branch -- so the unblock
  is this push itself, which re-arms both `push` and `synchronize`.
- Numbers were re-measured from a live collection run, not transcribed: the
  README tree and the SESSION_CONTEXT table were regenerated mechanically
  from `pytest --collect-only`. A host-dependent skip introduced during this
  round was removed rather than kept, because it made the canonical test
  count differ between Windows and Ubuntu CI and would have desynchronized
  the documents permanently.
- Validation: `pytest -q` -- **568 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Coverage 89% via
  `pytest --cov=scrobblescope`.
- Forward guidance: the review-fix loop on this PR is at the point where
  findings come from the fixes rather than from the original work, so merge
  rather than iterate. Confirm a Quality Gate run exists for the new head
  before merging; if none appears, close and reopen the PR to fire
  `pull_request` again.

### 2026-08-06 - PR #169 review remediation: guard and integrity defects (side-task)

- Scope: fixed every defect confirmed by the PR #169 review round -- three
  GitHub Copilot comments plus an independent audit of the guard subsystem,
  the docsync integrity subsystem, and the canonical document corpus.
- Plan vs implementation:
  - Worktree guard. Lineage verdicts named PLAYBOOK's expected branch while
    the ancestry counts and tree identities were measured from HEAD, so
    WT004's lease-protected force-push guidance could point at a branch the
    guard never inspected; they now name the checked-out branch. Branch state
    is classified before base-ref collection, so a missing `origin/main` no
    longer masks the wrong-checkout finding and no longer errors between
    batches. Section 3 parsing accepts ordinary prose and the bold
    `**Branch:**` style instead of failing closed on them. WT008 stops naming
    a primary environment that does not exist, WT009 warns rather than blocks
    in an ordinary checkout so a fresh clone can reach Environment Setup, and
    WT002 no longer republishes raw `OSError` text or absolute paths. A
    `--debug` flag separates a guard defect from an environment failure.
  - Docsync. The documented close-out command `--fix --keep-non-current 0`
    left the repository unrepairable: the authoritative count was read after
    rotation had emptied the live window, so a superseded value was written
    and then failed DOC006, with `--fix` reporting no changes and still
    exiting 1. The count is now derived from the pre-rotation document and
    from rotated archive entries, so retention settings cannot change it.
    DOC001 was narrowed to repository-relative references and now skips fenced
    blocks; DOC003 requires a backticked all-hexadecimal token and reports the
    violation that actually occurred; DOC002 names the competing declarations;
    generated per-batch logs are no longer reported as dead links.
  - Documents. The new qualified-tool rule shipped with eighteen pre-existing
    violations in its own corpus, now covered by one conversion rule rather
    than eighteen rewrites. Corrected references to the removed
    cross-validation, restored AGENTS ownership of the test-count rule,
    documented exit code 2 and the guard's non-blocking edge states, and
    removed a restatement and a normative claim that crossed document roles.
- Deviations: `_cross_validate` and its thirteen tests were removed rather
  than repaired -- the function lost its only production caller when the CLI
  moved to the integrity layer, and both checks it performed are now enforced
  more strictly by DOC006 and DOC001. This also reduces
  `tests/test_docsync_logic.py` from 904 to 725 lines against F-MAS-3. No
  dependency, installation, destructive Git action, history rewrite, or push
  beyond the standing review-fix authorization was required.
- Validation: `pytest -q` -- **561 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Mutation-checked: the guard
  suite now fails when the diagnostic subject is wrong, where previously both
  the defect and its fix left it fully green. The close-out command was
  rehearsed end to end on a throwaway clone -- exit 1 with a corrupted count
  before, exit 0 with the correct count after. Every guard production file is
  at or below the measured 236-line peer cap.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep. After the rebase merge,
  expect the tree-identical ahead/behind artifact on `wip/batch-21` and use
  the guard's WT004 output as the first live confirmation of that path.

### 2026-08-05 - Combined integrity and guard final-review fixes (side-task)

- Scope: resolved the four final combined-branch review blockers in the
  docsync integrity gate and read-only worktree guard tests.
- Plan vs implementation:
  - Replaced Windows-separator literals with host-rendered `Path` expectations
    while retaining explicit Windows/POSIX selection, symlink reuse, and the
    simulated POSIX inspection boundary.
  - Added optional SESSION_CONTEXT DOC001 scanning with original line numbers;
    absent-session behavior, schematic exclusions, and deterministic ordering
    remain unchanged.
  - Made the Section 3 declaration the sole normalized tracked root candidate
    for the exact current batch token, covering duplicates, `BATCH210`, root
    `BATCH21.md`, subdirectories, generic templates, untracked supplied content,
    and between-batches state.
  - Sanitized every tracked-file Git failure to one stable invocation error;
    CLI exit 2 contains no stderr, traceback, credential, path, or command text.
  - Marked the approved design implemented and aligned both implementation
    plans with the verified final contracts.
- Deviations: none. No dependency, installation, destructive Git action,
  environment creation, history rewrite, push, or DEVELOPMENT workflow change
  was required.
- Validation: platform-path RED -- 1 expected failure; behavioral RED -- 5
  expected failures; focused GREEN -- **68 passed**; complete docsync suite --
  **164 passed**; complete guard suite -- **84 passed**; full `pytest -q` --
  **521 passed** with 3 existing aiohttp/Python 3.13 warnings. Production and
  guard-test files remain within their measured peer caps.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard POSIX fixture remediation (side-task)

- Scope: corrected the final-review test fixture so host-neutral guard tests
  exercise the virtualenv layout selected on Windows and POSIX runners.
- Plan vs implementation:
  - Made the shared repository fixture derive its default tool layout from the
    host OS and removed sibling `Scripts/*.exe` assumptions from inspection and
    topology tests. Direct resolver tests retain explicit Windows, POSIX,
    primary-only, missing-tool, and symlink cases.
  - Added an optional `os_name` inspection boundary whose default remains
    host-derived, then drove the public inspection-to-virtualenv path with a
    deterministic simulated POSIX linked-worktree acceptance test.
  - Updated the authoritative plan interface and fixture/topology expectations;
    the stable `scripts.dev.worktree_guard` facade exports are unchanged.
- Deviations: none. No new file, dependency, Git mutation, environment creation,
  package installation, amend, or push was required.
- Validation: simulated-POSIX RED -- 1 expected failure; focused GREEN -- **1
  passed**; all shared-fixture consumers -- **46 passed**; complete guard suite
  -- **84 passed**; full `pytest -q` -- **513 passed** with 3 existing
  aiohttp/Python 3.13 warnings. All hooks and final docsync checks pass. File
  caps, facade smoke, and live online/offline guard acceptance remain green.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard final-review remediation (side-task)

- Scope: resolved all five final plan-review findings without changing the
  guard's read-only Git contract, selected-base behavior, or public facade.
- Plan vs implementation:
  - Split the 522-line `worktree_guard.py` into a 50-line stable facade plus
    diagnostics, inspection, lineage, runner/discovery, types, and virtualenv
    modules. Every guard production file is at or below the measured 236-line and
    8,754-byte pre-existing peer caps; every new test file is at or below the
    measured 184-line and 6,615-byte test peer caps.
  - Added ERROR WT014 for unexpected inspection/runtime failures, suppressed
    subprocess exception chains, caught generic `OSError`, kept explicit
    offline WT013 final, and added a second fail-closed CLI boundary. Output
    contains neither traceback nor sensitive command/URL text.
  - Added exact `(code, severity)` coverage for WT000 through WT014 and real
    inspection-through-CLI blocking, warning-only, success, detached-CI, and
    offline-failure paths. A temporary WT006 severity downgrade produced three
    expected failures and changed both blocking CLI exits from 1 to 0.
  - Clarified the sole initial stdlib-only guard-launch exception, retained
    DEVELOPMENT as human-only rationale, and refreshed the authoritative plan
    file map and reproducible split-suite RED/GREEN commands. Aligned the design
    spec's failure contract and split test map, then refreshed README and
    SESSION_CONTEXT structure, dependency, and test inventories from the
    measured final state.
- Deviations: the final review required a plan-wide SRP split after Task 2 had
  shipped; the facade preserves every accepted import and behavior. No
  destructive Git action, environment creation, dependency install, or push
  was performed.
- Validation: pre-split facade parity -- **55 passed**; new RED suite -- 11
  expected failures and 23 passes; minimal GREEN -- **34 passed**; post-split
  original parity -- **55 passed** with 2 new cases deselected; complete focused
  suite -- **83 passed**; severity mutation restore -- **26 passed**. Full
  `pytest -q` -- **512 passed** with 3 existing aiohttp/Python
  3.13 warnings. Pre-commit and final docsync gates pass. Dirty offline live
  acceptance reports WT010, WT000 (0 behind/12 ahead, linked primary tools),
  then final WT013.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep. Use the stable
  `scripts.dev.worktree_guard` facade for all imports.

### 2026-08-05 - Worktree guard default remediation compatibility (side-task)

- Scope: restored the established WT007 operator guidance for the canonical
  `origin/main` base without changing the review-approved behavior for custom
  or local refs.
- Plan vs implementation:
  - Added an exact regression that failed against the neutralized default
    wording and protects both the explicit `git fetch --prune origin` action
    and the offline local-ref fallback.
  - Added one exact-default branch to missing-base remediation. Custom
    `upstream/trunk` and local `main` retain their selected-ref-specific,
    command-neutral guidance; WT013 ordering and exit behavior are unchanged.
- Deviations: none; this is a compatibility correction only, with no Git
  command, collector sequence, diagnostic code, or dependency change.
- Validation: focused guard suite -- **55 passed**. `pytest -q` -- **484
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard review remediation (side-task)

- Scope: corrected the two Task 2 review findings without changing the
  guard's read-only architecture or Git command sequence.
- Plan vs implementation:
  - Added final informational WT013 to every offline result, after state and
    environment diagnostics. WT000 remains success-only; offline lineage and
    virtualenv errors now retain explicit local-ref-only context.
  - Replaced hard-coded origin recovery prose with selected-base guidance.
    WT004 names the display-safe comparison ref, while WT007 uses neutral
    selected-ref or local-ref wording and never constructs a shell command.
  - Added exact inspection and CLI regressions for error-path WT013 ordering,
    custom `upstream/trunk` guidance, and the local-only `main` edge.
- Deviations: added stable code WT013 and corrected the approved plan's
  detached-CI wording so WT011 remains its only topology diagnostic while
  explicit offline mode can add the independent qualifier. Custom-base tests
  live in a new peer-sized file rather than overgrowing an existing peer.
- Validation: focused guard suite -- **54 passed**. `pytest -q` -- **483
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Read-only worktree bootstrap guard (side-task)

- Scope: completed the repository-integrity worktree safeguard before the
  F-SWE-1 audit and Batch 21 WP-1.
- Plan vs implementation:
  - Added sanitized, injectable Git collection for repository topology,
    PLAYBOOK branch metadata, base ancestry, dirty state, and tree identity.
    Missing repositories/refs, wrong or detached local branches, behind-only
    branches, and both forms of divergence fail without changing Git.
  - Added a thin CLI with stable diagnostic rendering, explicit offline
    labeling, recognized detached-CI skip behavior, and qualified primary
    checkout Python, pytest, and pre-commit paths for linked worktrees.
  - Made the read-only command a canonical post-document bootstrap gate;
    HANDOFF points to that owner, while DEVELOPMENT records only the human
    rationale and the deliberate separation from CI topology enforcement.
  - Exercised the live linked worktree offline: WT010 identified the
    intentional dirty candidate, WT000 reported 0 behind/9 ahead, and all
    three tools resolved under the primary checkout's existing `.venv`.
- Deviations: split collector acceptance across peer-sized inspection,
  topology, runner, and CLI files instead of expanding the existing classifier
  file past its directory peers; no dependencies, environment creation,
  package installs, or Git mutation.
- Validation: focused guard suite -- **49 passed**. `pytest -q` -- **478
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree classifier review remediation (side-task)

- Scope: resolved the first review round for Task 1 without expanding the
  pure classifier into Task 2's Git discovery or bootstrap integration.
- Plan vs implementation:
  - Restored Steps 2, 4, and 6 of the authoritative plan to run only the
    parser/lineage test file that exists at those stages; Step 10 onward keeps
    both focused paths after the venv test file is created.
  - Added parameterized both-sided-divergence coverage for a missing head tree,
    missing base tree, and both trees missing. Every unavailable-tree state now
    asserts WT005, while only two present matching IDs assert WT004.
  - Replaced remediation-fragment checks with the full mandated WT004 and WT005
    strings, protecting dirty reconciliation, refreshed-base/tree verification,
    owner authorization, force-push-with-lease boundaries, and the explicit
    prohibition on reset, rebase, or force-push for true divergence.
  - Mutation verification weakened both remediation constants and treated two
    missing IDs as equal; the strengthened suite produced five expected
    failures before the original correct behavior was restored.
- Deviations: none; production behavior was already correct, so this round
  strengthens regression protection and repairs plan execution order only.
- Validation: parser/lineage suite -- **23 passed**; complete focused guard
  suite -- **30 passed**. `pytest -q` -- **459 passed** with 3 existing
  aiohttp/Python 3.13 warnings. Final hooks and docsync gates pass.
- Forward guidance: proceed to Task 2's read-only CLI and bootstrap wiring;
  F-WORKTREE-1 and F-WORKTREE-2 remain open until its live linked-worktree
  acceptance passes.

### 2026-08-05 - Pure worktree safety classification (side-task)

- Scope: implemented the pure, read-only classification layer for the
  worktree-safety guard without wiring it into bootstrap or running Git.
- Plan vs implementation:
  - Added strict PLAYBOOK Section 3 parsing that ignores historical log text,
    preserves missing active-branch metadata, and rejects missing, duplicate,
    or malformed active state rather than guessing.
  - Added deterministic lineage diagnostics for detached CI/local states,
    missing or wrong active branches, dirty trees, behind-only state, and both
    content-identical rebase artifacts and true divergence. Remediation is
    diagnostic only and performs no repository mutation.
  - Added platform-aware environment resolution for ordinary and linked
    checkouts. Linked worktrees reuse the primary checkout `.venv`; distinct
    secondary environments and missing required tools fail with actionable
    diagnostics, while a symlink/junction alias to the primary environment is
    accepted.
  - Corrected two plan-interface contradictions while preserving its safety
    policy: lineage snapshots now carry the parsed active-batch discriminator,
    and the WT005 test verifies that remediation explicitly prohibits reset
    without contradicting the mandated `do not reset` wording.
  - Split immutable value types and virtualenv tests into focused peer-sized
    files to satisfy the repository's new-file size gate; the public imports
    and focused test command remain explicit in the corrected plan.
- Deviations: specification-preserving interface/test corrections only; no
  dependencies, package installs, Git commands, automatic repairs, or
  bootstrap enforcement were added.
- Validation: focused worktree-guard suite -- **27 passed**. `pytest -q` --
  **456 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: Task 2 must add the thin read-only CLI, canonical bootstrap
  rule, and real linked-worktree acceptance before F-WORKTREE-1 and
  F-WORKTREE-2 can close. The pure classifier is testable but is not yet a
  mandatory bootstrap command.

### 2026-08-05 - Docsync content-integrity plan final remediation (side-task)

- Scope: closed the plan-wide final review findings without changing the
  approved deterministic-only enforcement architecture.
- Plan vs implementation:
  - Made the newest live full-suite `pytest -q` validation in PLAYBOOK the
    authoritative test count, including side-task entries outside the
    current-batch markers; the renderer and DOC006 now share that result and
    reject conflicting named SESSION_CONTEXT count fields.
  - Tightened active-definition matching to a complete numeric batch token
    and limited DOC001's exemption to the exact Section 3 declaration.
  - Converted Git invocation `OSError` failures to sanitized `SyncError`
    diagnostics so the CLI returns 2 without a traceback, preserved analyzer
    input immutability, and strengthened the two-reference regression.
  - Refreshed the docsync package/dependency inventory and all measured test
    counts; DEVELOPMENT remains explanatory human documentation only.
- Deviations: none; no dependencies, semantic auto-fixes, or Git history
  changes.
- Validation: focused docsync suite -- **156 passed**. `pytest -q` --
  **429 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.

### 2026-08-05 - Docsync integrity review remediation (side-task)

- Scope: addressed the first Task 2 review round without changing the
  approved enforcement design.
- Plan vs implementation:
  - Added CLI regression coverage proving `--fix` returns 1 with DOC001 for
    an unresolved dead live reference and emits no stale DOC005 after it
    repairs the session block.
  - Moved resolved F-DOCSYNC-5 out of the active P0 section, leaving only the
    two worktree safeguards as open P0 gates.
  - Corrected the Task 2 focused-suite record to the measured post-remediation
    count.
- Deviations: none.
- Validation: specified docsync suite -- **112 passed**. `pytest -q` --
  **420 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.

### 2026-08-05 - Docsync content-integrity enforcement (side-task)

- Scope: wired the reviewed pure live-document integrity analyzer into the
  local and CI docsync gate, closing F-DOCSYNC-5 before Batch 21 WP-1.
- Plan vs implementation:
  - Made the side-task archive prologue renderer-owned, so `--check` detects
    a stale prefix and `--fix` restores it without changing dated entries.
  - Added stable blocking `ERROR DOC...` CLI diagnostics for live integrity
    defects. `--fix` writes deterministic output first and revalidates the
    final on-disk state; unresolved semantic defects still exit 1.
  - Retained missing optional SESSION_CONTEXT support and the existing root
    BATCH-file warnings, while removing legacy warning-only CLI validation.
- Deviations: none.
- Validation: targeted docsync suite -- **111 passed**. `pytest -q` --
  **419 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the separate read-only worktree-safety guard;
  F-WORKTREE-1 and F-WORKTREE-2 remain the P0 gate before Batch 21 WP-1.

### 2026-08-05 - Docsync integrity analyzer review remediation (side-task)

- Scope: corrected two review findings in the pure analyzer before its
  deferred CLI/CI wiring task.
- Plan vs implementation:
  - Active definitions now require both supplied live-document content and a
    tracked path; an untracked declaration reports DOC002 at its Section 3
    declaration line rather than being masked by the DOC001 exemption.
  - Replaced ignored dated Section 4 entry lines with blank placeholders, so
    later PLAYBOOK diagnostics retain their original file line numbers.
  - Added separate regression tests that first reproduced both defects.
- Deviations: none; integration remains intentionally out of scope.
- Validation: `pytest -q` -- **415 passed** with 3 existing aiohttp/Python
  3.13 warnings. Final hook and docsync gates pass.
- Forward guidance: Task 2 can consume the corrected pure analyzer without
  reimplementing its active-definition or PLAYBOOK source-location rules.

### 2026-08-05 - Docsync live-document integrity analyzer (side-task)

- Scope: added the pure live-document integrity analyzer for the P0
  repository-content safeguard; enforcement is intentionally deferred to the
  next ordered task.
- Plan vs implementation:
  - Added deterministic `IntegrityIssue` diagnostics DOC001 through DOC006
    for dead concrete references, active-definition drift, volatile Branch
    metadata, archive-prologue drift, stale managed session content, and
    contradictory current test counts.
  - Added adversarial pure-unit coverage for literal-reference extraction,
    tracked-path normalization, active-definition metadata, archive/session
    comparison, and deterministic ordering. The analyzer is not yet wired
    into the docsync hook or CI gate, so F-DOCSYNC-5 remains open.
- Deviations: none; CLI integration and severity changes remain the next task.
- Validation: `pytest -q` -- **413 passed** with 3 existing aiohttp/Python
  3.13 warnings. Final hook and docsync gates pass.
- Forward guidance: integrate the pure analyzer without duplicating its
  parsing or changing the established sync behavior before enforcement.

### 2026-08-05 - P0 integrity/worktree implementation plans (side-task)

- Scope: translated the owner-approved repository-integrity/worktree-safety
  specification into executable, test-first implementation plans.
- Plan vs implementation:
  - Split the two independent safeguards into ordered plans so each produces
    a reviewable, independently testable result: CI-blocking docsync content
    integrity first, then local worktree lineage and shared-virtualenv safety.
  - Mapped exact files, interfaces, diagnostic codes, adversarial tests,
    canonical documentation ownership, fault-injection evidence, validation
    gates, and commit boundaries. Each code step includes concrete signatures
    or snippets rather than delegating design decisions to the executor.
  - Self-reviewed both plans against every approved-spec section, checked type
    and diagnostic-name consistency, removed placeholders, balanced Markdown
    code fences, and kept the second plan smaller than its peer per the new-file
    size rule.
- Deviations: the single specification becomes two sequential plans because
  repository-content integrity and local Git topology are independent failure
  domains. Scope and execution order are unchanged.
- Validation: plan self-review -- pass. `pytest -q` -- **390 passed** with 3
  existing aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all
  10 hooks pass. Final `doc_state_sync.py --check` -- exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: choose Subagent-Driven execution (recommended) or Inline
  Execution. Complete both plans before F-SWE-1; Batch 21 WP-1 remains gated.

### 2026-08-05 - Repository-integrity and worktree-guard design (side-task)

- Scope: investigated why canonical documentation drift and repeated
  post-rebase worktree divergence survived green local and CI gates, then
  captured the owner-approved remediation as a written design.
- Plan vs implementation:
  - Realigned the clean, tree-identical `wip/batch-21` branch from the
    post-PR-#168 3/3 divergence to `origin/main` and force-pushed with lease
    after explicit owner authorization.
  - Split the remediation into a blocking repository-content integrity layer
    inside docsync and a separate read-only local worktree alignment guard;
    detached CI runs the former and unit-tests the latter, but does not
    pretend to validate local worktree topology.
  - Logged F-WORKTREE-1 and F-WORKTREE-2, and reopened F-DOCSYNC-5 as P0
    items until mechanical prevention lands. The second worktree finding was
    reproduced during validation: a linked root has no gitignored `.venv`, so
    the test gate must reuse the qualified environment under the primary
    checkout. Updated DEVELOPMENT.md with the human-readable incidents and
    design rationale while preserving AGENTS.md as the future owner of
    agent-facing rules.
  - Wrote the approved design at
    `docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
- Deviations: implementation is deliberately deferred until the owner reviews
  the written specification, as required by the selected design workflow.
- Validation: written-spec self-review -- pass. Qualified shared-venv
  `pytest -q` -- **390 passed** with 3 existing aiohttp/Python 3.13 warnings.
  `pre-commit run --all-files` -- all 10 hooks pass. Final
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: review the written specification. After approval, create
  the implementation plan, land both P0 safeguards, then execute the full
  F-SWE-1 sweep; Batch 21 WP-1 remains gated behind the remediation.

### 2026-08-03 - PR #168 pre-merge canonical-doc audit (side-task)

- Scope: audited the PR head against the canonical documentation and
  handoff rules before rebase merge; found and fixed two P1 operational
  documentation defects that could misdirect the next agent.
- Plan vs implementation:
  - Removed the superseded `fa61716` fork point from the active Batch 21
    definition. Branch lineage is volatile during review-remediation
    rebases, so the definition now delegates that state to PLAYBOOK
    Section 4 instead of pinning another copy.
  - Corrected the live side-task archive header from obsolete PLAYBOOK
    Section 10 to Section 4 and repointed all three read helpers from the
    `docs/history/` tombstone to `docs/logarchive/`.
  - Recorded the resolved P1 issue as FINDINGS.md F-DOCSYNC-5 under the
    repository's source-tag nomenclature and refreshed the file's
    last-updated date.
  - Replaced the SWE audit charter's fixed F-DOCSYNC numeric range with
    a FINDINGS-owned category pointer so new or resolved F-DOCSYNC items
    remain in the do-not-re-report baseline.
- Deviations: none. PR #168 contains no runtime behavior change, and no
  GitHub thread or PR state was changed.
- Validation: targeted documentation regression check -- pass.
  `pytest -q` -- **390 passed** with 3 existing aiohttp/Python 3.13
  warnings. `pre-commit run --all-files` -- all 10 hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: after PR #168 merges, realign `wip/batch-21` with
  `main`, then continue Batch 21 WP-1. F-SWE-1 remains a separate,
  chartered audit whose execution is still pending.

### 2026-08-03 - PR #168 Copilot review round 1 (side-task)

- Scope: assessed both Copilot review comments on PR #168; both were
  technically valid and addressed.
- Plan vs implementation:
  - Replaced the canonical `Registry entries 4 and 5` example in
    `AGENTS.md` with symbolic placeholders. The numeric example matched
    the expanded sweep it was explaining, so the rule created its own
    violation and made the related no-current-hits claim false.
  - Corrected the prior side-task's forward guidance. The branch was
    level with `main` immediately after realignment, but applying the
    review-fix commit left it directly based on `main` and one commit
    ahead, not equal to it.
- Deviations: none. Dated point-in-time log references remain unchanged
  under the canonical rule's explicit historical-record exception.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: wait for the next PR #168 review round before WP-1.

### 2026-08-02 - Post-merge branch realign; PR #166 review fixes (side-task)

- Scope: PR #165 was rebase-merged (main tip `458f9ad`). The rebase
  produced the usual 23/23 ahead-behind artifact with an identical tree,
  and PR #166 was opened from it in the reverse direction
  (`main` -> `wip/batch-21`); #167 was opened from a separate Copilot
  branch to fix review comments. The owner closed both.
- Plan vs implementation:
  - `wip/batch-21` reset to `origin/main` and force-pushed with lease;
    ahead-behind is 0/0. Commit history on `main` is intact -- all 23
    commits landed individually. The apparent bunching is rebase
    rewriting committer dates while author dates stay distinct.
  - Reapplied the three valid PR #166 findings here so they arrive
    validated and on one lineage: the `MAX_ACTIVE_JOBS` comment no
    longer claims arrival-order serialization (`threading.Lock` gives no
    FIFO guarantee -- it now says each throttle serializes reservations
    behind a shared lock with no ordering guarantee); the canonical
    numeric-citation sweep covers plural and alternate forms, since a
    pattern written as `Registry #\d` cannot match
    `Registry entries 4 and 5`; and the round-9 entry's "returns
    nothing" claim is qualified to exclude dated point-in-time records,
    which legitimately contain such citations.
  - Third occurrence of a countermeasure scoped to the instance that
    prompted it rather than the class. The rule now says explicitly to
    match plural and alternate forms.
- Deviations: none. PR #167 additionally proposed merging #166; that was
  wrong -- #166 pointed `main` at `wip/batch-21`, so merging it would
  have produced the merge commit the rebase-merge workflow exists to
  avoid.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: branch is directly based on `main`, with this one
  review-fix commit ahead, and is ready for WP-1 after PR review.

### 2026-08-01 - PR #165 round 9; new rules are not retroactive (side-task)

- Scope: three suppressed comments, all valid -- numeric citations into
  ordered lists (`Anti-Pattern Registry entries 4 and 5`, two
  `acceptance criterion 8` references) that the registry's own
  name-based citation rule prohibits.
- Cause, established from history rather than assumed: the citations
  were written in the SSOT pass and the FINDINGS refresh; the rule
  banning them was written two commits later. Nothing swept the
  existing corpus against the new rule, so the rule shipped with a
  backlog of its own violations. The pre-push checklist greps the blast
  radius of *the change*; when the change is a rule, the blast radius is
  the whole repository, and that leap was never made.
- Plan vs implementation: all three citations repointed by name. A
  repo-wide sweep for `entries N`, `Registry #N`, `criterion N`,
  `step N`, `rule N`, `item N` across every canonical doc returns no
  matches outside dated point-in-time log records, which stay as
  written. The lesson was folded into the existing blast-radius
  anti-pattern as one sentence rather than becoming a fifteenth
  registry entry -- see the verbosity note below.
- Deliberate non-action: folded into an existing entry rather than added
  as a fifteenth, because rule text has begun causing findings as well
  as preventing them -- the registry grew long enough to need numbers,
  and the numbers became the defect.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: merge rather than iterate further.

### 2026-08-01 - PR #165 round 8; over-broad claims narrowed (side-task)

- Scope: three suppressed comments, all valid, all fixed.
- Plan vs implementation:
  - The Section 2 note claimed close-out entries for *each* batch live
    in the monolith archive. False: `BATCH18_LOG.md` holds its own
    close-out because that heading carried a `(Batch 18 WP-5)` tag;
    only the `(Batch N close-out)` spelling misroutes. Narrowed here
    and in F-DOCSYNC-3, which carried the same over-broad framing.
  - The Section 2 subsection heading still read "Completed batches
    (definitions archived)" while the table lists the active batch with
    a root definition. Retitled to cover both.
  - `AGENT_NOTES.md` asserted a batch was active and where its
    definition sits in the same breath as declaring that the file does
    not track batch state -- self-contradictory, and false between
    batches. Reduced to the pointer alone.
  - Anti-Pattern Registry, assertions entry: broadened from the one
    phrasing that had failed before (`all N`, ranges) to the full
    quantifier vocabulary, since the narrow sweep is what let "each
    batch" through.
- Assessment of the review loop: none of these three were caused by the
  previous round's fixes -- the fix-causes-finding chain that drove
  rounds 5 through 7 did not repeat. What remains is pre-existing
  over-broad wording in text the sweep touched. On that basis the
  pre-push checklist is working and mechanical enforcement is not yet
  warranted; a consistency-lint hook stays a docsync-WP candidate rather
  than scope creep into this PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: findings have narrowed to wording precision rather
  than correctness; this is the diminishing-returns point. Recommend
  merging rather than requesting another round.

### 2026-08-01 - PR #165 round 7 + review-loop pattern sweep (side-task)

- Scope: owner asked for the round-7 findings to be verified but not
  fixed until a sweep across every review round on PRs #163/#164/#165
  identified why fixes keep producing new findings. Corpus: ~40
  findings over 12 rounds.
- Round 7 findings (all three valid):
  - `AGENTS.md` close-out step 3 said "add a row" to PLAYBOOK Section 2,
    but the active batch already has one -- following it literally
    duplicates the row. Now says repoint the existing row, add only if
    absent.
  - The sufficiency gate required agreement with "the batch definition"
    while bootstrap step 3 states no definition exists between batches,
    so the gate was unsatisfiable in that state. Both states now
    stated.
  - `docs/SWE_AUDIT_CHARTER.md` labelled its differential baseline
    "Open findings" while including F-DOCSYNC-4, resolved earlier in
    this same PR. Relabelled as already-tracked regardless of status,
    with an instruction to check each `Status:` line.
- Sweep results -- four recurring classes, now in the Anti-Pattern
  Registry. Two were already logged; two are new:
  - *Fixing the instance instead of the class* (logged previously): the
    dominant cause. Rounds 6 and 7 findings were created almost
    entirely by rounds 5 and 6 fixes.
  - *Lossy or contradictory consolidation* (new): collapsing duplicated
    rules to one owner while leaving copies, dropping a specific
    prohibition (the `git add -A` ban nearly vanished this way), or
    contradicting another section of the same file.
  - *Assertions over sets, ranges, and citations* (new): "all seven CSS
    files", "F-DOCSYNC-1 through F-DOCSYNC-4", citing a gitignored
    file, citing an anti-pattern that does not cover the case.
  - *Happy-path-only procedures* (new): steps that break in an edge
    state -- row already present, no definition between batches, gate
    ordered before the work it validates.
- Why the loop exists, and the structural fix: the validation gates
  check mechanics only -- nothing verifies that one document still
  agrees with another, so each fix's damage is discoverable only by the
  next review round. Added a "Pre-push self-review" block to Commit
  Rules: read changed files whole rather than as diffs, run the
  blast-radius greps, walk procedures through edge states, and prefer
  deletion to addition because every added sentence is new surface area.
- Deviations: none. The new checklist caught its own first violation --
  the draft cited registry entries by number, which the same registry
  forbids; now cited by name.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the honest test is round 8. If it finds fresh
  self-inflicted drift, the checklist is not enough and the next step is
  mechanical enforcement (a consistency-lint hook) rather than more
  prose.

### 2026-08-01 - PR #165 review round 6; self-inflicted-drift anti-pattern (side-task)

- Scope: round 6 returned three suppressed comments, zero visible. All
  three verified valid -- and all three were created by round 5's own
  fixes, which is the finding that matters more than the fixes.
- Plan vs implementation:
  - Acted: `AGENTS.md` Side-Task Handling and `HANDOFF_PROMPT.md` both
    cited "Commit Rules step 4" for the documentation requirement; the
    round-5 reorder moved it to step 1. Repointed **by name** ("the
    documentation step", "Missing log entries") rather than by number,
    so a future reorder cannot re-stale them.
  - Acted: `AGENT_NOTES.md` load-testing bullet still asserted the
    per-job guarantee and single-throttle model that round 5 corrected
    in `config.py`. Rewritten to match and to point at `config.py` as
    the single owner of the rationale.
  - Declined (precedent): PLAYBOOK Section 4 entries at :163 and :262
    also contain "step 3/4/6" references that no longer match the
    current numbering. They are dated point-in-time records of what was
    true when written; retro-editing rotated log content was declined
    and accepted in PR #162 round 3 and PR #163 round 3.
  - Root-cause fix: new Anti-Pattern Registry entry 11, "Fixing the
    instance instead of the class" -- requires a blast-radius grep
    before the gates (references to anything renumbered/renamed, and
    sibling copies of any corrected claim), and prefers name-based
    cross-references over numeric ones.
  - Swept beyond the three findings: verified the remaining numeric
    references (`AGENTS.md` close-out step 2, charter bootstrap step 1)
    still resolve correctly, and that the `req/s` claims in F-B18-11 and
    F-B18-10 are accurate because the heatmap and album pipelines are
    both Last.fm-only.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply.

### 2026-08-01 - PR #165 Copilot review round 5 (side-task)

- Scope: round 5 returned "not ready to approve" with four suppressed
  comments and zero visible ones. All four verified valid against the
  code; all four acted on.
- Plan vs implementation:
  - `config.py`: the MAX_ACTIVE_JOBS rationale claimed "one global
    10 req/s API throttle". Wrong -- `utils.py:81-82` builds separate
    `_LASTFM_THROTTLE` and `_SPOTIFY_THROTTLE`. Comment now names the
    Last.fm scrobble-fetch phase as the binding constraint.
  - `AGENTS.md` commit procedure: the docsync `--check` gate sat at
    step 3 while the PLAYBOOK update was step 4, so the gate ran before
    the documentation it validates (and `pre-commit` carries the
    `doc-state-sync-check` hook). Reordered: write docs, `--fix`, then
    the three gates on the final state. This matches what sessions
    already do in practice; only the written rule was wrong. Fixed a
    duplicate step number introduced by the renumber.
  - `FINDINGS.md` F-DATA-1 open question 2 proposed grouping
    `spotify_cache` by `artist_norm + album_norm` -- which is the
    primary key (`init_db.py:42`), so every group holds exactly one row
    and the upsert has already overwritten any rival date. Replaced
    with the two methods that can actually work (re-run the Spotify
    search and compare against the earliest fresh candidate, or
    cross-check MusicBrainz).
  - `docs/SWE_AUDIT_CHARTER.md`: prescribed commit subject was a noun
    phrase, violating the imperative-subject rule the charter tells
    executors to follow. Now imperative.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply. PR #165 remains merge-ready pending the next
  auto-review.

### 2026-07-31 - FINDINGS: record reissue cache-key collapse (side-task)

- Scope: capture a data-quality mechanism found while discussing the
  DEVELOPMENT.md rewrite, before the reasoning was lost to chat. No code
  change -- this is a finding, not a fix.
- Plan vs implementation: added `F-DATA-1` under P2.
  `normalize_name()` strips `deluxe`/`edition`/`remastered` and eight
  more words, so a reissue and its original normalize identically; since
  the `spotify_cache` PK is `artist_norm + album_norm`, they share one
  row and whichever populated it first serves its `release_date` for 30
  days. Owner observed this with Viagra Boys "viagr aboys" (2025)
  surfacing under 2026 via the JP deluxe released 2026-01-09, on an
  account that never played it.
- The finding records why the collapse is nonetheless correct (Last.fm
  scrobbles the same record under inconsistent album strings; keying
  editions apart would split one album into several leaderboard rows
  with divided playcounts), the candidate fix (decouple counting from
  dating -- keep the collapse for aggregation, take the *earliest*
  candidate release date when resolving the year, no schema change), the
  rejected boolean discriminator and why, three questions answerable by
  querying the cache, and the note that Spotify exposes no
  original-release-date field at all.
- Deviations: earlier in the session an agent claim that release-date
  drift was a systemic risk was walked back. The owner has ~14 years of
  scrobbles and one recalled instance; the claim had been reasoned from
  a plausible mechanism rather than measured. Filed P2 with low user
  impact stated explicitly, and `release_scope: all` already bypasses
  date filtering. Recording the correction so the finding is not read as
  more urgent than the evidence supports.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: question 2 (which other albums) is a cache query, not
  an investigation -- run it before designing any fix. Sequenced behind
  Batch 21, the F-B20-2 orchestrator split, and the test/docstring pass
  per owner priority.

### 2026-07-31 - DEVELOPMENT.md: correct HANDOFF_PROMPT description (side-task)

- Scope: DEVELOPMENT.md described `HANDOFF_PROMPT.md` as a condensed
  checklist of rules, gates, read order, and commit discipline. That was
  accurate until this branch, which reduced the file to post-read
  verification plus the handoff checklist and replaced everything else
  with pointers. The description was left describing the architecture
  this PR removed.
- Plan vs implementation: two passages corrected -- the architecture
  overview and the per-file section, which was also retitled from
  "Bootstrap Procedure" to "Session Start and Handoff" to match what the
  file now contains. Both now state why the summaries were removed
  (each restatement drifted from its source), which is the reasoning the
  rest of the document uses.
- Deviations: scope-limited on purpose. Only the passages this branch
  made wrong were touched. DEVELOPMENT.md has other known staleness --
  the `gemini-pr-triage` skill is now `pr-bot-triage`, the
  review-suggestions section predates repo-aware review tooling, and the
  closing paragraph needs a rewrite -- all deferred to a post-merge
  documentation pass, per the same in-scope test applied to
  `concurrent_users_test.py` in review round 1.
- Note: this class of staleness is invisible to diff-scoped review.
  Copilot reported "13/13 changed files" across four rounds and
  DEVELOPMENT.md was never among them, so a file made wrong by the diff
  but not part of it cannot be flagged. Worth remembering when relying on
  automated review for consistency.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the post-merge pass should reframe the review section
  around how the tooling changed rather than around rejection, and
  `README.md:492` must move with it -- it currently promises a section on
  suggestions "evaluated and rejected".

### 2026-07-31 - Push rule: standing exception for review-fix commits (side-task)

- Scope: owner-directed policy change, not a review finding. During PR
  #165 triage the owner granted a standing authorization to push
  review-driven commits without asking per round, on the reasoning that
  the agent reaches the diminishing-returns point on its own and a
  per-round approval round-trip only stalls the loop.
- Plan vs implementation: encoded in AGENTS.md Commit Rules step 6 rather
  than left as an agent-side preference, because AGENTS.md is the rules
  SSOT and a spoken rule that contradicts the written one is exactly the
  defect this PR spent four rounds removing. Scoped per owner: **Claude
  Code and Codex sessions only.** GitHub Copilot task sessions and their
  subagents, Jules, and any other agent follow the unmodified rule --
  the owner does not extend equal trust to agents of varying quality
  that it cannot inspect per-invocation. Step 6 already carried a
  Copilot-specific clause, so per-agent scoping had precedent.
- Deviations: the exception is deliberately narrow. Review-fix commits on
  an open PR only; batch and WP commits still pause, and force-pushes,
  history rewrites, and anything touching `main` still require explicit
  instruction.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: if the agent roster changes, this clause names
  specific agents and will need revisiting -- it is an allowlist, not a
  capability test.

### 2026-07-31 - PR #165 Copilot review round 4 (side-task)

- Scope: zero visible comments, two suppressed, both valid and both real
  defects rather than the judgement-call trade-offs round 3 predicted.
  The convergence call made after round 3 was wrong; recorded here
  because the wrong prediction is the useful part. Tally 18/18.
- Plan vs implementation:
  - **A rule was silently deleted by this PR, and round 1 removed the
    last copy.** The prohibition on `git add -A` / `git add .` lived in
    two places before this branch: AGENT_NOTES.md Owner Preferences and
    the old HANDOFF_PROMPT anti-pattern list. The PR's HANDOFF_PROMPT
    rewrite dropped its copy, and the round-1 dedup replaced the
    AGENT_NOTES copy with a pointer to AGENTS.md Commit Rules -- which
    never contained the prohibition. Step 5 only said "stage only files
    changed for this work package", which `git add -A` can satisfy when
    every changed file happens to belong to the WP. Restored explicitly
    in Commit Rules step 5, the canonical location the pointer targets.
  - Lesson: verifying that a pointer's target "covers it in substance"
    is not enough. Round 1 checked AGENTS.md:167 and accepted a
    paraphrase as equivalent when it dropped a prohibition. Before
    deleting a rule copy, diff the *specific obligations*, not the topic.
  - `scripts/testing/concurrent_users_test.py` promised queuing in three
    places. `acquire_job_slot()` uses `acquire(blocking=False)` and both
    call sites (`routes.py:460`, `routes.py:570`) return an error
    immediately, so excess submissions are rejected and never queued.
    Round 1 edited one of those lines for the cap change without
    questioning the surrounding claim. Now describes rejection, matching
    README's "capacity rejections" wording.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: do not call convergence from the *shape* of a round's
  findings. Rounds 2 and 3 returned zero visible comments and were still
  productive; round 4 found a deleted rule. Stop when a round returns
  nothing, not when the findings look minor.

### 2026-07-31 - PR #165 Copilot review round 3 (side-task)

- Scope: round 3 again returned zero visible comments and three
  suppressed ones. Two acted on in full, one acted on in part.
  Suppressed-block tally now 16/16 across #163, #164, and #165.
- Plan vs implementation:
  - `docs/SWE_AUDIT_CHARTER.md` Section 3 copied the ten principle names
    from AGENT_NOTES.md and **had already drifted**: the copy dropped the
    definitions for Dependency Inversion, Least Knowledge, and Fail Fast,
    and truncated SRP from "single responsibility per module/function".
    This is the rare case where the drift was demonstrable rather than
    hypothetical, so the copy is gone. The section now points at
    AGENT_NOTES.md and keeps only the two audit-specific methods (Clean
    Architecture via the SESSION_CONTEXT Section 4 acyclic graph, Boy
    Scout via git history).
  - `docs/SWE_AUDIT_CHARTER.md` Section 6 restated side-task entry
    placement that AGENTS.md Side-Task Handling owns -- and round 2 had
    just renumbered that section, so the charter was already a rewrite
    away from being wrong. Delegated.
  - `HANDOFF_PROMPT.md` Section 1 restated the bootstrap-conflict rule
    verbatim from AGENTS.md:64-65 inside a paragraph that claims rules
    "are not restated here". Removed.
- Deviations: **partially declined** the reviewer's request to also strip
  "Do not push without owner instruction" from the charter's commit step.
  Verified AGENTS.md:171 owns it, so the SSOT argument is technically
  right, but that line sits at the point of action for a cold-start
  executor (the charter is written so Codex can run it without prior
  context) and a push is not reversible. Deliberate safety redundancy is
  worth one line. Removed the same sentence from HANDOFF_PROMPT Section 1
  by contrast, because there the reader is being sent to AGENTS.md in the
  very same paragraph, so the copy buys nothing.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: watch for diminishing returns. Rounds 1-3 were all
  genuine, but the remaining duplication is increasingly load-bearing
  context for cold-start executors; judge each on whether the copy can
  drift *and* whether losing it costs a reader who cannot see the source.
  Batch 21 WP-1 remains the next action.

### 2026-07-31 - PR #165 Copilot review round 2 (side-task)

- Scope: round 2 returned **zero visible comments and five suppressed
  ones**. All five were valid. The suppressed-block hit rate is now 13/13
  across PRs #163, #164, and #165 while the visible stream has gone dry
  twice; treat that block as the primary signal, not an appendix.
- Plan vs implementation:
  - `AGENTS.md` Side-Task Handling read as an ordered procedure whose
    step 1 was "commit" and step 2 "add the log entry", contradicting
    Commit Rules step 4 and Anti-Pattern Registry #9, which require the
    entry to be in the same commit. Since AGENTS.md is now the rules
    SSOT, an internal contradiction there is load-bearing. Reworded so
    side-tasks inherit the commit rules unchanged and differ only in
    entry placement and tagging; the remaining steps renumbered.
  - `HANDOFF_PROMPT.md` Section 5 told agents to document completion
    *after* committing and to commit the docs separately -- the same
    conflict, one level down. Now states that docs land in the commit.
  - Resolution was evidence-based, not a judgement call: registry #9
    forbids a commit without its entry, and all four recent side-task
    commits (`2559f39`, `2b9b095`, `98cc50c`, `900d0e6`) bundle
    PLAYBOOK + archive with the change. Docs were wrong; practice was
    right.
  - `FINDINGS.md` F-LOAD-1 proposed an "N/5 slots in use" hint, which
    hard-codes a value that is env-configurable. This PR had changed it
    from "N/10" -- swapping one literal for another. Now specifies
    reading the cap from `MAX_ACTIVE_JOBS` at render time.
  - `.claude/SESSION_CONTEXT.md` header said 2026-07-28 while the body
    recorded a 2026-07-31 runtime change. Header updated.
  - `docs/SWE_AUDIT_CHARTER.md` cited "AGENTS.md registry #10" for
    silent scope reduction; #10 is about re-measuring canonical figures
    and says nothing about audit coverage. The charter was added in this
    PR, so this was a sourcing error at write time, not staleness --
    corrected rather than left as a point-in-time record. Now states the
    requirement directly.
- Deviations: round 1 split its fixes across two commits, and `07c4f5b`
  therefore landed without its own Section 4 entry -- a violation of
  Anti-Pattern Registry #9, the rule this round clarifies. Not rewritten:
  both commits were already pushed and history rewrites need owner
  instruction. Round 2 is a single commit. Standing lesson: this repo's
  #9 outranks the generic "prefer small atomic commits" heuristic, and
  the one-commit-per-review-round precedent from PR #163 was correct.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: Batch 21 WP-1 remains the next action. `gh` writes
  are still unavailable this session, so the round-2 reply is unposted.

### 2026-07-31 - PR #165 Copilot review round 1 (side-task)

- Scope: triaged the five comments on PR #165 (four inline, one inside
  the suppressed low-confidence block). All five were valid; none were
  declined. Two themes: an overstated concurrency claim and three
  leftover copies of rules AGENTS.md now owns.
- Plan vs implementation:
  - `config.py`: the MAX_ACTIVE_JOBS rationale claimed a cap of 5 "keeps
    >=2 req/s per job". `_GlobalThrottle.next_wait()` (utils.py) advances
    a single next-allowed timestamp under one lock, serializing callers
    in arrival order with no per-job accounting, so a busy job can take
    more slots than an idle one. Reworded as an average, matching the
    "~10/N req/s" framing already used in AGENT_NOTES.md.
  - `scripts/testing/concurrent_users_test.py`: module docstring and
    `build_parser()` still said the default was 10 and told operators to
    set `--concurrency` above 10. Both now say 5. A repo-wide sweep found
    no other live stale reference; remaining "default 10" hits are all
    under `docs/history/` and stay as written (point-in-time records).
  - `AGENT_NOTES.md`: the Owner Preferences commit-mechanics bullet and
    the Venv "In short:" line each pointed at AGENTS.md and then restated
    its content anyway. Both reduced to pointers after verifying AGENTS.md
    genuinely carries every rule involved.
  - `HANDOFF_PROMPT.md`: Section 2 restated the full three-command gate
    and the root-BATCH warning, contradicting the Document Roles contract
    added by this same PR, which assigns gates to AGENTS.md. Collapsed to
    a pointer matching the wording Sections 3 and 4 already use.
- Deviations: none. No test changes -- all five edits are comment or
  documentation text with no behavior change.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the suppressed-comment block again held a real
  finding (8/8 across PRs #163/#164/#165), so keep expanding it. Batch 21
  WP-1 remains the next action.

### 2026-07-31 - WP-1 token values pinned in the definition (side-task)

- Scope: make WP-1 executor-agnostic. The definition referenced "the
  audit token sheet" but only carried headline values; the full sheet
  lived in the Claude Design project and one agent's session notes,
  blocking a cold-start executor (e.g. a Codex session) from
  implementing WP-1 faithfully.
- Plan vs implementation: the WP-1 theme bullet now pins the complete
  sheet -- all eight colors (light bg/bg-2/ink/primary, dark
  bg/surface/text/primary), the three-family type system with sizes,
  the 4px spacing ladder, and the radius set. Values transcribed from
  "ScrobbleScope UI Audit v3" section "A starter palette and type
  system you can ship today" (2026-07-28 fetch).
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 can now be executed by any agent from the
  definition alone; compiled CSS remains the WP-1 deliverable.

### 2026-07-31 - Owner-preferences commit-rule dedup (side-task)

- Scope: final SSOT sweep found AGENT_NOTES.md Owner Preferences still
  restating three commit-mechanics rules AGENTS.md now owns
  (incremental staging, no co-author trailers, push/pause discipline).
- Plan vs implementation: the four bullets collapsed into one pointer at
  AGENTS.md Commit Rules; preference-only items (concise responses,
  Docker/MCP pause, explain-why, Firefox testing, principles, testing
  pyramid) stay -- they are owner context, not rules.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: hygiene plan complete (6 commits); Batch 21 WP-1 is
  next. SSOT sweep contract now holds: commit-rule keywords, venv rules,
  the heatmap perf figure, and batch state each have exactly one owner.

### 2026-07-31 - SWE-principles audit charter (side-task)

- Scope: charter the owner-requested audit of the ten mandated software
  principles so a dedicated single-purpose session (Claude or Codex) can
  execute it cold, without this session's context.
- Plan vs implementation: new `docs/SWE_AUDIT_CHARTER.md` front-loads
  all judgment -- Python-only scope (JS/templates excluded until
  Batch 21 ships them), a do-not-re-report differential baseline
  (F-MAS-*, F-B20-2, prior 2026-02 audits, standing design decisions),
  pre-identified hotspots (the three ~110-150 line functions and the 17
  `except Exception` sites), a 10-principle x module grading matrix
  with per-cell evidence, and a strict output contract (a dated
  SWE_PRINCIPLES_AUDIT report under the history archive plus net-new
  F-SWE-N findings only; read-only, no code changes). Tracked as
  F-SWE-1.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: execution is decoupled -- run whenever convenient
  (Codex costs no Claude tokens). Batch 21 WP-1 is unblocked and next.

### 2026-07-31 - MAX_ACTIVE_JOBS default 10 -> 5 (side-task)

- Scope: owner decision. The 2026-03-04 load test ran 2/3/5 concurrent
  users clean while the 10-user run never completed; all jobs share the
  global 10 req/s API throttle, so 10 slots starve each job below
  1 req/s on the single small Fly.io machine.
- Plan vs implementation: `scrobblescope/config.py` default changed to
  `"5"` with a rationale comment (still env-overridable); README (three
  mentions), SESSION_CONTEXT key-runtime-facts line, and FINDINGS
  F-LOAD-1 phrasing updated to match. `fly.toml` sets no
  `MAX_ACTIVE_JOBS` override, so the new default takes effect on next
  deploy.
- Deviations: pre-change scouting claimed no test depends on the
  default (capacity tests inject their own semaphores) -- true for
  assertions but not for shared state. Route tests that mock
  start_job_thread acquire a real slot that is never released, and the
  session's accumulated leaks crossed the new cap of 5, failing
  `test_heatmap_loading_json_body` with a real 429. Fixed properly: a
  new autouse `fresh_job_slots` fixture in `tests/conftest.py` resets
  the semaphore per test, removing the hidden inter-test ordering
  coupling the lower cap exposed.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner can observe the 5-slot cap locally; the
  "N/5 slots in use" occupancy hint remains open as F-LOAD-1.

### 2026-07-31 - FINDINGS refresh: batch-closure pointers, F-DOCSYNC-4, F-SWE-1 (side-task)

- Scope: owner-flagged staleness in FINDINGS.md -- open P1 items that
  Batch 21's definition already promises to close carried no pointer,
  and F-B20-4 paraphrased the whole definition.
- Plan vs implementation:
  - F-B20-3: remedy rewritten -- the 5.1->5.3 CDN-consolidation path is
    dead; Batch 21 resolves the split by eliminating Bootstrap (closes
    at WP-8). F-AUDIT-1: closes at Batch 21 WP-2 via acceptance
    criterion 8. F-B18-12 deferred-block line marked as in-batch scope
    (WP-6). F-B20-4 compressed to a pointer at `BATCH21_DEFINITION.md`.
    F-FEATURE-2 line reformatted as a greppable cross-ref bullet.
  - New F-DOCSYNC-4 (resolved): per-batch logs were undiscoverable until
    the Section 2 Log column landed; records the tombstone disposition.
  - New F-SWE-1 (open P1): SWE-principles audit chartered via
    `docs/SWE_AUDIT_CHARTER.md` (next commit), executable cold by a
    dedicated Claude or Codex session; closes by pointing at the report.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: F-LOAD-1's "N/10" phrasing updates with the
  MAX_ACTIVE_JOBS default change (next commit); charter follows.

### 2026-07-31 - PLAYBOOK Section 2 log column; tombstone disposition (side-task)

- Scope: the 18 per-batch logs under `docs/history/logs/` were referenced
  from no working doc (Section 2 had no Log column), making batch history
  discoverable only via a directory glob.
- Plan vs implementation: Section 2 table gained a Log column linking
  `BATCH3_LOG.md` through `BATCH20_LOG.md` (batches 0-2 predate per-batch
  logging); a note under the table points close-out-entry seekers at the
  monolith archive per F-DOCSYNC-3. AGENTS.md Batch Close-Out step 3 now
  requires filling the Log column at close-out so the column cannot go
  stale. Investigated the two 300-byte `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  files under `docs/history/` and `docs/history/logs/`: they are
  deliberate "Moved:" tombstones from the Batch 14 restructure kept for
  backward references -- retained, disposition recorded in F-DOCSYNC-4.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: hygiene commits 3-5 follow (FINDINGS refresh,
  MAX_ACTIVE_JOBS 5, SWE audit charter).

### 2026-07-31 - Bootstrap-doc SSOT pass: single-source rules and state (side-task)

- Scope: owner-requested hygiene sweep before Batch 21 WP-1. Exploration
  confirmed AGENTS.md and HANDOFF_PROMPT.md contradicted each other
  (bootstrap order, sufficiency gate, pre-commit gate, ownership map),
  commit discipline existed in 3-4 copies, the heatmap perf measurement
  in 4 copies, and AGENT_NOTES.md carried live batch state under a
  shipped-feature heading plus Batch 19 residue and a pointer to a
  non-repo file.
- Plan vs implementation:
  - AGENTS.md is now the single owner of rules: canonical 7-step
    bootstrap order (AGENTS.md itself is step 1), the stricter 3-way
    sufficiency gate, a 6-step pre-commit procedure including the
    doc_state_sync --check gate, the conflict-resolution rule, and four
    new anti-patterns (never --no-verify; stale Section 3; missing log
    entries; stale dashboard figures -- the ~72% coverage figure
    survived five months while reality was 89%). Docstring mandate moved
    into Proposal and Design Rules.
  - HANDOFF_PROMPT.md reduced to what it uniquely owns: post-read
    verification (git status/log + pytest count reconciliation) and the
    end-of-session handoff checklist; all rule sections now link to
    AGENTS.md instead of restating.
  - AGENT_NOTES.md: batch state moved out (PLAYBOOK Section 3 declared
    the single source); Heatmap section retitled shipped and trimmed of
    Batch 19 residue; venv rules and runtime constants replaced with
    links to their owners; load-test pointer now inlines the conclusion
    (2/3/5 clean, 10 never completed) and flags the raw data as
    agent-side; Talisman note repointed to the archived Batch 17 log;
    orchestrator-split note repointed to F-B20-2; the ten software
    principles expanded from bare acronyms.
  - SESSION_CONTEXT: Section 3 now lists all 7 CSS / 7 JS files and the
    template set (Batch 21 touches exactly these); heatmap perf trimmed
    to an F-B18-11 pointer here and in PLAYBOOK Section 3 -- F-B18-11 is
    the only full copy of the measurement.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: commits 2-5 of the approved hygiene plan follow
  (PLAYBOOK log column, FINDINGS refresh, MAX_ACTIVE_JOBS 5, SWE audit
  charter); then Batch 21 WP-1.

### 2026-07-29 - PR #164 phantom cleanup + review response (side-task)

- Scope: PR #163 was rebase-merged, leaving `wip/batch-21` "8 ahead /
  8 behind" (identical content, different SHAs -- normal rebase-merge
  artifact). The owner opened PR #164 from the stale branch; Copilot
  re-reviewed the phantom diff and left three NEW valid comments that
  four prior rounds missed. PR #164 closed with explanation; branch
  force-pushed to match `main`; all three fixes applied here.
- Plan vs implementation:
  - WP-4: leaving the loading page is now a plain "Back home" link with
    no `/reset_progress` call -- the endpoint clears stored job state
    only (`routes.py:227-238`); the daemon worker keeps its slot and
    rewrites the job afterward, so a "Cancel" label would be misleading
    and the reset racy.
  - WP-1: digest verification extended to cached artifacts (verify on
    every use, refetch once on mismatch, fail closed) -- gitignored
    `scripts/bin/` persists between runs, so download-time-only checks
    leave a bypass.
  - AGENTS.md: rotation note qualified -- bottom-appended entries are
    archived on the next `--fix` only once the non-current window is at
    capacity; placement rule unchanged.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 next on the realigned branch; open a fresh PR
  for the next review cycle when WP work lands.

### 2026-07-29 - PR #163 review response, round 4 (side-task)

- Scope: Copilot round 4 -- one suppressed comment. Verified valid and
  acted on.
- Plan vs implementation: the archived coverage-refresh entry cited
  "the CLAUDE.md canonical command", but CLAUDE.md is gitignored
  (`.gitignore:49`) and repo-invisible; the command is documented at
  README.md "Running Tests". Reference corrected in the monolith
  archive entry.
- Deviations: none. Distinction from the PR #162 round-3 decline on
  editing rotated entries: that citation was accurate at write time and
  went stale (point-in-time record, left alone); this one was
  repo-invisible at write time -- a sourcing error that defeats the
  record's verifiability, so it is corrected rather than preserved.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds have reached citation polish;
  recommend merging or pausing auto-review re-requests. WP-1 next.

### 2026-07-28 - PR #163 review response, round 3 (side-task)

- Scope: Copilot round 3 -- three suppressed low-confidence comments.
  Two acted on, one deferred to FINDINGS with a decline on the PR.
- Plan vs implementation:
  - Acted: `global.css` joins the WP-2 legacy per-page stack -- verified
    it carries Bootstrap-coupled `.card`/`.card-body`/`.modal-*` rules
    (`global.css:141-199`) that would restyle daisyUI components if it
    stayed in `base.html`; token/wordmark/shell concerns redistributed
    (daisyUI themes + `shell.css`).
  - Acted: WP-8 drift hook diff scoped with a pathspec
    (`git diff --exit-code -- static/css/tailwind.css`) so unrelated
    dirty files or rewrites from earlier hooks in the same run cannot
    produce false drift failures.
  - Deferred: retagging the Batch 20 close-out entry in the monolith
    archive. The routing claim is correct, but it is consistent tool
    behavior (`(Batch N close-out)` is not parser-recognized;
    BATCH19_LOG.md lacks its close-out too), and hand-editing
    machine-rotated archive content in a docs PR was declined and
    accepted in PR #162 round 3. Logged as F-DOCSYNC-3 (open P2) for a
    docsync WP alongside F-DOCSYNC-1/2.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 remains next; batched reply posted on PR #163.

### 2026-07-28 - PR #163 review response, round 2 (side-task)

- Scope: Copilot round 2 -- no new top-level comments, four suppressed
  low-confidence comments. All four verified valid (same pattern as
  PR #162: the suppression filter is too conservative); all acted on.
- Plan vs implementation:
  - Stale bootstrap docs: AGENT_NOTES.md still called Batch 21 a TBD
    stub with "no WP work until scope lands"; FINDINGS.md header said
    scope pending; README roadmap listed scoping as open. All three now
    reflect the active batch (the definition's own Status line already
    carried Active from WP-0).
  - Compiled-CSS drift window: validation gate now requires any WP
    touching templates or `tailwind.src.css` (WP-2..WP-7) to rebuild
    and commit `tailwind.css` in the same commit; the drift hook
    deliberately stays in WP-8 (moving it to WP-1 would front-load the
    headless-CI fetch problem before any template exists to protect).
  - Stack-restriction conflict: `toast` + `alert` added to the
    permitted daisyUI set for the WP-5 toast rewrite.
  - `--bars-color` inventory corrected: six of seven page CSS files
    (`unmatched.css` hardcodes its own `--header-bg`), pinwheel via
    `var()`; the wordmark hardcodes `#6a4baf` and only the dark-mode
    override (`global.css:49-50`) uses the variable, so light-mode
    wordmark recoloring is explicit migration work.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 remains next; batched reply posted on PR #163.

### 2026-07-28 - PR #163 review response (side-task)

- Scope: address the Copilot auto-review on PR #163 (Batch 21 open +
  doc refreshes). Five inline comments, all on `BATCH21_DEFINITION.md`;
  all five verified valid against the code and acted on.
- Plan vs implementation:
  - WP-1: per-platform SHA-256 digests committed alongside pinned
    versions; `tailwind_build.py` must verify every downloaded artifact
    before executing it (pin-only trusts the release asset at fetch
    time, and the WP-8 CI hook executes that binary headless).
  - WP-1: daisyUI standalone needs both `daisyui.mjs` and
    `daisyui-theme.mjs`; the component bundle alone cannot register the
    two custom `@plugin` themes.
  - WP-2: explicit coexistence isolation -- one framework stylesheet
    per template via the per-page block, shared shell styled by a
    framework-neutral `shell.css` absorbed at WP-8. Rejected daisyUI
    prefix alternative (WP-8 removal churn) with reasoning recorded.
  - WP-5: dropped "CSV walker untouched" -- `results.js` exports
    rendered cell text, so `MMM YY` display dates would truncate CSV
    release dates; date cells keep ISO in `data-export`, walker
    prefers it.
  - WP-7 + acceptance criterion 6: `below_min_plays`/`below_min_tracks`
    removed from the reason-code set -- `fetch_top_albums_async` drops
    threshold failures before the pipeline (`orchestrator.py:112-116`),
    and near-miss retention is explicitly Batch 22+. Two reason cards,
    not three; out-of-scope entry cross-references the deferred codes.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 implementation must honor the amended digest
  and dual-plugin-file requirements; batched reply posted on PR #163.

### 2026-07-28 - Side-task entry placement rule in AGENTS.md (side-task)

- Scope: document the doc_state_sync rotation gotcha discovered during
  the coverage-figure refresh so any agent places side-task entries
  correctly on the first try.
- Plan vs implementation: AGENTS.md Side-Task Handling step 2 now
  states that new entries must be inserted directly after the
  CURRENT-BATCH-END marker (top of the non-current list). The list is
  ordered newest-first; rotation keeps the first `--keep-non-current`
  entries positionally and rotates the rest, so a bottom-appended entry
  is treated as oldest and archived by the next `--fix` run instead of
  staying in the active window.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: next work remains Batch 21 WP-1 (Tailwind + daisyUI
  toolchain).

### 2026-07-28 - Coverage figure refresh in SESSION_CONTEXT (side-task)

- Scope: replace the stale coverage figure in SESSION_CONTEXT Section 1.
  The row still carried ~72% from the 2026-02-20 audit run; coverage has
  not been re-measured in a canonical doc since.
- Plan vs implementation: ran the canonical coverage command documented
  in README.md "Running Tests"
  (`pytest --cov=scrobblescope --cov-report=term`) on `wip/batch-21`
  (equal to `main` + WP-0, which touched no Python). Result: 89% total
  (1260 stmts, 134 miss). Lowest modules: `lastfm.py` 77%, `utils.py`
  81%, `orchestrator.py` 85%; four modules at 100%. Updated the
  Section 1 Coverage row with the new figure, measurement date, and
  scope (`--cov=scrobblescope`).
- Deviations: none. The owner's `main` checkout keeps the old figure
  until this branch merges; no fix applied there by design.
- Addendum (same day, owner-requested): the README tech-stack Testing
  row also said ~72%; updated to 89% in a follow-up commit.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: next work remains Batch 21 WP-1 (Tailwind + daisyUI
  toolchain). Re-measure coverage at future batch close-outs so the
  Section 1 row does not go stale again.

### 2026-07-24 - Batch 20 complete; definition archived, log purged (Batch 20 close-out)

- Scope: Batch 20 WP-8 close-out per the AGENTS.md procedure.
- Plan vs implementation:
  - `doc_state_sync.py --fix --keep-non-current 0` purged the 4 rotated
    non-current side-task entries into the monolith archive.
  - `git mv BATCH20_DEFINITION.md docs/history/definitions/` and marked
    the archived definition header Complete.
  - PLAYBOOK Section 2: Batch 20 row now links to the archived
    definition. Section 3: Batch 20 marked complete; Batch 21 (UI
    overhaul) flagged as next, awaiting the owner's in-progress UI
    proposal.
  - `.claude/SESSION_CONTEXT.md` Section 1: Batch 20 row set to
    Complete (all 9 WPs); Batch 21 row set to next-batch status. The
    "22 test modules" wording was already correct from earlier WPs.
- Deviations: none. Batch ran WP-0..WP-5 via Copilot PRs (#153/#155/
  #156/#159), then a post-merge audit follow-up commit plus WP-6, WP-7,
  and this close-out on `wip/batch-20` in a worktree.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with only the
  expected `BATCH21_DEFINITION.md` root warning remaining.
- Forward guidance: next batch is Batch 21 (UI overhaul); expand
  `BATCH21_DEFINITION.md` into WPs once the owner's proposal lands.
  `wip/batch-20` holds four unpushed commits awaiting owner review and
  push/PR instruction.

### 2026-07-24 - PR #162 review response (side-task)

- Scope: address the Copilot review on PR #162 (Batch 20 completion).
  All six comments (four inline + two suppressed low-confidence) were
  valid doc-consistency catches; five acted on fully, one partially.
- Plan vs implementation:
  - `FINDINGS.md`: header status updated to Batch 20 complete / Batch 21
    next; `Source:` added to F-B20-4 and F-B18-11; `Status:` lines added
    to all P2, Info, and feature items; shipped F-FEATURE-2 rotated to
    the archive with a cross-reference note.
  - `AGENTS.md` Finding-Writing Rules: rotation rule clarified --
    standing design-decision Info items (F-LOAD-3..5) keep their F-IDs
    in the active file and rotate only when superseded. This is the
    partial decline: archiving them would contradict the Batch 20
    definition's WP-6 intent.
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: header claim narrowed
    to ID/history preservation (bodies may be condensed at rotation).
  - `PLAYBOOK.md` Section 3: "unpushed pending owner instruction"
    replaced with "submitted as PR #162" (the Section 4 close-out entry
    keeps the original wording as a point-in-time record).
  - `AGENT_NOTES.md`: stale "Batch 20 is now active" block updated to
    complete/archived status with Batch 21 next.
  - `BATCH21_DEFINITION.md`: baseline refreshed 389 -> 390.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: batched reply posted on PR #162; awaiting merge.
  Batch 21 scope expansion remains next once the owner's UI proposal
  lands.

### 2026-07-24 - PR #162 review response, round 2 (side-task)

- Scope: address Copilot's second review round on PR #162 (four inline
  comments + one suppressed). All five verified valid; all acted on.
- Plan vs implementation:
  - `FINDINGS.md` F-MAS-4: `except Exception` count updated 14 -> 17
    (verified by grep; Copilot's per-file breakdown was exact) with the
    recount date noted.
  - `FINDINGS.md` deferred-block pointer corrected: detailed bodies live
    in pre-Batch-20 FINDINGS.md via git history (before `494f2c7`), not
    under `docs/history/` as previously claimed.
  - `FINDINGS.md` F-FEATURE-2 cross-reference recast as a direct
    sentence (grammar).
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: F-FEATURE-2 heading
    suffix normalized to `-- RESOLVED (shipped in Batches 18/19)` per
    the AGENTS.md suffix rule.
  - Archived `BATCH20_DEFINITION.md` header relabeled `Baseline:` ->
    `Final count:` so it no longer conflicts with the definition's
    unchanged 389-baseline plan text.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: PR #162 ready for merge; Batch 21 definition draft
  sits uncommitted in the worktree awaiting owner approval.

### 2026-07-24 - PR #162 review response, round 3 (side-task)

- Scope: Copilot round 3 (two comments + one suppressed duplicate).
  One acted on, one declined.
- Plan vs implementation:
  - Acted: both F-B19-6 archive headings moved their portion qualifier
    after the colon to match the `F-<context>-<N>: <title>` format the
    batch itself established (AGENTS.md Finding-Writing Rules).
  - Declined: updating the `BATCH20_DEFINITION.md:107-108` citation
    inside the archived `docs/history/logs/BATCH20_LOG.md` WP-3 entry.
    Rotated log entries are point-in-time records (same principle as
    the round-1 "unpushed" decline, which the reviewer accepted), they
    are machine-rotated content the docsync tooling owns, and the
    filename remains uniquely greppable at its archived location.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds are now in pure-style territory;
  recommend merging PR #162.

### 2026-07-24 - PR #162 review response, round 4 (side-task)

- Scope: Copilot round 4 -- one comment on PLAYBOOK Section 3 batch-state
  wording. Acted on, with a corrected mechanism note.
- Plan vs implementation:
  - Section 3 now uses the parser-recognized marker "Batch 21 is not yet
    defined"; the Section 3 parse verifiably returns the between-batches
    state with that wording in place.
  - Verified the comment's mechanism was doubly off: `BATCH_NEXT_RE`
    does not match "Batch 21 is next" (the attribution came from the
    `last_completed + 1` fallback at `parser.py:198-199`), and the
    wording fix alone cannot change the rendered STATUS -- with the
    close-out entry still inside the CURRENT-BATCH markers,
    `renderer.py:85-86` applies its own `last_completed + 1` fallback.
    Batch 19 precedent shows this is transient: its identically-tagged
    close-out entry rotated out automatically when Batch 20 WP-0 landed,
    and the same will happen at Batch 21 WP-0.
  - Logged the renderer gap as F-DOCSYNC-2 (open P2) rather than
    hand-moving machine-managed marker content or patching docsync code
    inside a docs-only PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner is merging PR #162; Batch 21 opens next.

### 2026-07-24 - Post-merge audit gap fixes (Batch 20 audit follow-up)

- Scope: close gaps found by the owner-requested audit of PR #159 (WP-1
  through WP-5 were executed via Copilot + PR reviews; audit compared the
  merged result against `BATCH20_DEFINITION.md` acceptance criteria).
  Work continues in a `wip/batch-20` worktree off `main` for isolation.
- Plan vs implementation:
  - `README.md`: deleted the "Doc-State Sync Tooling" bullet from Key
    Implementation Highlights (WP-1 acceptance item; the WP-1 log entry
    claimed removal but no commit ever removed it). Fixed the Project
    Structure tree so the agent-docs cluster is a comment row instead of
    a fake directory nesting five root-level files, and moved `AGENTS.md`
    and `PLAYBOOK.md` into that cluster. Added the missing prose note that
    `BATCHN_DEFINITION.md` sits at the root only while a batch is active.
  - `DEVELOPMENT.md`: corrected the `scrobblescope-bootstrap` description
    to the skill's actual read order (AGENTS.md -> PLAYBOOK 3-4 -> active
    batch definition -> SESSION_CONTEXT 1-2 -> AGENT_NOTES, then git/test
    verification) replacing the inaccurate SESSION_CONTEXT-first
    early-stop description.
  - `BATCH20_DEFINITION.md` header: refreshed stale status ("awaiting
    owner audit"), branch, and 389 baseline (390 since the WP-5 deviation).
  - `PLAYBOOK.md` Section 3 + `.claude/SESSION_CONTEXT.md` Section 1:
    branch updated from merged `file-hygeine` to `wip/batch-20`.
- Deviations: Getting Started length (WP-3 target ~95-100 lines, actual
  155 after review iterations added a full `docker run` block and 3-OS
  schema-init instructions) left as-is pending owner decision:
  re-compress vs accept the expanded setup detail.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-6 (FINDINGS.md cleanup and archive) is next.

### 2026-07-24 - README CSRF and UX cleanup (side-task)

- Scope: PR-review-comment-driven fixes to `README.md` and `AGENTS.md`.
- Plan vs implementation:
  - `README.md`: updated CSRF description to document three distinct injection
    mechanisms -- form-submit body token (`/results_loading`, `/results_complete`,
    `/unmatched_view`), header-only fetch (`/reset_progress`), and both body and
    header (`/heatmap_loading`). Added `/unmatched_view` to the form-submit route
    list after reviewer confirmed the hidden `csrf_token` input at
    `templates/results.html:177-178`.
  - `README.md`: removed three duplicate UX entries from the Styling & UX details
    block (rotating messages, personalized stats, onboarding) that were already
    covered in the Features section above.
  - `AGENTS.md`: removed a non-ASCII section symbol (replaced with plain text
    "Section") to comply with the ASCII-only markdown authoring rule.
- Deviations: none -- all changes are documentation-only PR review responses
  outside Batch 20 WPs; Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --check` -- exit 0.
- Forward guidance: Batch 20 WP-6 (FINDINGS.md cleanup) is still the next
  work package.

### 2026-07-24 - DEVELOPMENT.md file-count follow-up

- Scope: side-task follow-up to close the missed Batch 20 WP-5 documentation
  requirement in `DEVELOPMENT.md` by acknowledging `FINDINGS.md` as the sixth
  advisory, read-on-demand file in the external-memory description.
- Plan vs implementation:
  - Reworded the file-count paragraph to distinguish the five core tracked
    files from advisory `FINDINGS.md`, while keeping the archive-directory
    count unchanged.
  - Kept the wording explicit so IDE-based agents (for example Claude Code
    and Codex in VS Code) do not misread `FINDINGS.md` as part of the
    mandatory bootstrap set.
- Deviations: none -- this closes a missed WP-5 acceptance item flagged in PR
  review and leaves Batch 20 WP-6 as the next unstarted work package.
- Validation: `.venv/bin/pytest -q` -- **390 passed**. `.venv/bin/pre-commit
  run --all-files` -- all hooks pass. `.venv/bin/python scripts/doc_state_sync.py
  --check` -- exit 0 with the two expected root-BATCH warnings.
- Forward guidance: WP-6 still cleans up and archives `FINDINGS.md`.

### 2026-07-24 - Restore out-of-scope README edits (side-task)

- Scope: revert the Features-section rewrite and the Acknowledgements removal
  made in PR #159 outside Batch 20 WP-1 through WP-3; keep Screenshots removal
  as intentional.
- Plan vs implementation:
  - `README.md`: restored the original flat-list Features section (removed the
    "As mentioned above" intro and the `<details>` wrapper added out-of-scope).
  - `README.md`: restored the Acknowledgements section before Author & Contact.
  - `README.md`: updated Table of Contents to re-include only the
    Acknowledgements link.
- Deviations: none -- pure restoration of pre-PR content flagged by code review
  at PR #159 discussion_r3644787390.
- Validation: `pre-commit run --all-files` -- pass. `pytest -q` -- not
  applicable (documentation-only change). `python scripts/doc_state_sync.py
  --check` -- pass.
- Forward guidance: Features and Acknowledgements now match the intended PR
  state, with Screenshots intentionally removed; any future changes to those
  sections require an explicit batch WP or deviation log entry.

### 2026-07-24 - Copilot comment-job bootstrap trim (side-task)

- Scope: reduce unnecessary bootstrap for Copilot PR comment/review-comment
  jobs after the `copilot` Actions run failed in request processing with a
  monthly-quota error before reaching the linked review thread.
- Plan vs implementation:
  - `AGENTS.md`: added a targeted review-comment fast-path for prompts that
    link to a single `discussion_r...` thread, limiting reads to the linked
    file/lines plus only the bootstrap context that thread actually needs.
  - `HANDOFF_PROMPT.md`: removed the unconditional "read all bootstrap
    files" mandate for comment jobs and aligned the startup procedure with
    the lighter fast-path in `AGENTS.md`.
- Deviations: none -- this is a side-task CI reliability fix outside Batch 20;
  Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --fix` -- no changes.
  `python scripts/doc_state_sync.py --check` -- pass, with the two expected
  active-root-BATCH warnings. `pytest -q` and `pre-commit run --all-files`
  could not run in this sandbox because the repo-local `.venv` and those
  executables are not present here.
- Forward guidance: if future comment jobs still hit quota, inspect whether
  the prompt is fetching full PR comment lists when a direct review-comment
  URL is already supplied.

### 2026-07-22 - Link-preview image + Open Graph meta tags (side-task)

- Scope: LinkedIn (and Slack/Discord/etc.) show no image when the app URL
  is shared, since no og:image or companion meta tags existed.
- Plan vs implementation:
  - New `static/images/social-card.png` (1200x630, standard OG/Twitter
    card size): dark gradient background, the real favicon.svg pinwheel
    mark, wordmark, and tagline. Generated by rendering an HTML page that
    embeds the actual favicon.svg markup (not a hand-approximated
    redraw) and screenshotting it at 2x via the Chrome DevTools Protocol
    browser tool, then downsampled with Pillow (already pinned in
    requirements.txt; no new dependency).
  - `templates/base.html`: added `og:type`, `og:site_name`, `og:title`,
    `og:description`, `og:image` (+width/height), `og:url`, and the
    `twitter:card`/`title`/`description`/`image` equivalents. Title and
    description are Jinja blocks (`og_title`, `og_description`) so child
    templates can override per-page; default to the existing site title
    and meta-description text. `og:image` uses
    `url_for(..., _external=True)` so it resolves to an absolute URL
    against whatever host serves the request (required -- OG scrapers
    reject relative image URLs).
- Deviations: none. Out of scope for the active Batch 20 (file-hygiene,
  no production-code changes per `BATCH20_DEFINITION.md`), so logged as
  a side-task per `AGENTS.md` Side-Task Handling rather than a Batch 20 WP.
- Validation: `pytest -q` -- **389 passed**, no change (docs/template/asset
  only, no Python logic touched). `pre-commit run --files templates/base.html
  static/images/social-card.png` -- doc-state-sync-check passed (only
  applicable hook). Verified rendered output via Flask test client: all
  12 meta tags present, `og:image` resolves to an absolute URL.
- Forward guidance: none pending. Owner should verify the card renders
  correctly on LinkedIn's actual link-preview (some platforms cache
  previews aggressively per-URL; may need LinkedIn's Post Inspector to
  force a re-scrape after first deploy).

### 2026-05-19 - Batch 19 close-out (Batch 19 close-out)

- Scope: archived the Batch 19 definition, refreshed README for the PR to
  main, and finalized PLAYBOOK + SESSION_CONTEXT to reflect Batch 19 complete.
- Plan vs implementation:
  - `git mv BATCH19_DEFINITION.md docs/history/definitions/BATCH19_DEFINITION.md`.
  - PLAYBOOK Section 2 table now links to the archived definition.
  - PLAYBOOK Section 3 marks Batch 19 complete; next action is the
    `feat/heatmap` PR to `main`.
  - SESSION_CONTEXT Batch 19 row flipped to **Complete**.
  - README bumped to 387 tests, "Top Albums" mode rename in the intro,
    framed heatmap result + KPIs + desktop calendar vs. mobile activity
    strip described, `.venv/` venv guidance aligned with AGENTS.md, and
    heatmap roadmap line updated to cover both Batch 18 and Batch 19.
- Deviations: owner kept screenshots as "coming soon" placeholders since
  the saved ones in `docs/images/` no longer reflect the current UI.
  Owner will refresh them out of band.
- Validation: `pytest -q` passed with **387 passed** and 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` passed all 10
  hooks. `python scripts/doc_state_sync.py --check` exited 0 with the
  expected root warning gone after archiving the definition.
- Forward guidance: open the PR for `feat/heatmap` -> `main`, address any
  reviewer comments, merge, and deploy. Batch 20 (heavy UI refactor) is
  to be scoped later and is explicitly out of this PR.

### 2026-05-19 - PR #152 Gemini Code Review fixes (side-task)

- Scope: addressed three substantive Gemini Code Review comments on the
  open `feat/heatmap` PR.  Deferred three "broad except Exception"
  comments to the future error-handling batch (already tracked as
  FINDINGS.md P1 item 9).
- Plan vs implementation:
  - **Commit `ccb000f`** -- `fix(heatmap): use UTC for scrobble
    timestamps and fetch window`. Brought `heatmap.py` in line with
    `lastfm.py:31`'s established UTC convention. Updated every UTS-
    building call site in `tests/test_heatmap.py` to `tzinfo=timezone.utc`
    so the boundary tests are not vacuous against tz bugs. Added a new
    adversarial test (`test_utc_decode_invariant_against_local_tz_drift`)
    that pins a UTS at 23:30 UTC and asserts the bucket lands on the UTC
    day, not the local-tz day.
  - **Commit `01a7904`** -- `fix(repositories): isolate nested
    daily_counts in get_job_context`. Explicit
    `dict(results["daily_counts"])` after the outer shallow copy.
    Chosen over `copy.deepcopy` for the polling hot path. Closes
    F-B18-8. New regression test in `test_repositories.py`.
  - **Commit `53919c2`** -- `fix(heatmap): keep streak alive when today
    has no scrobble yet`. Stepping back one day when today is zero
    matches GitHub-contributions/Duolingo convention and was the
    pattern Gemini suggested.
  - FINDINGS.md gained F-B19-6 (naive-tz vacuous-test anti-pattern,
    forward-TODO for AGENTS.md update) and a resolved entry for F-B18-8.
- Deviations: declined Gemini's three "narrow the bare
  `except Exception`" comments. Those are all instances of FINDINGS.md
  P1 item 9 (14 sites total); narrowing 3 of 14 piecemeal without a
  test matrix per error class is a regression risk that violates
  AGENTS.md scope discipline. Belongs in the dedicated error-handling
  batch the FINDINGS entry already calls for.
- Validation: `pytest -q` passes with **389 passed** and 3 existing
  aiohttp/Python 3.13 warnings (387 -> 389; +1 UTC adversarial test,
  +1 nested-copy regression test). `pre-commit run --all-files` passes
  all 10 hooks. `node --check static/js/heatmap.js` clean.
- Forward guidance: push the three fix commits + this log entry,
  reply to Gemini via `gh pr review` declining the broad-Exception
  comments with a FINDINGS-item-9 pointer, and wait for re-review.

### 2026-05-16 - Remove dependabot.yml (side-task)

- Removed `.github/dependabot.yml`: all packages are pinned with `==` so
  dependabot can only open PRs that break the pinning policy. Pure noise for
  this project. No functional change.
- **385 tests passing**, all hooks green.

### 2026-05-16 - README update: heatmap feature + stale data

- Added heatmap feature description to intro paragraph (was album-only).
- Added Scrobble Heatmap bullet to Features section (grid, palette, tooltips,
  dark mode, responsive, pinwheel spinner).
- Updated project structure: heatmap.py, heatmap.css, heatmap.js,
  scrobblescope_pinwheel.svg, test_heatmap.py all added; stale test counts
  corrected (test_repositories.py 18->19, test_routes.py 50->65).
- Updated tech stack table: test count 350/23 -> 385/24; APIs note that
  heatmap uses Last.fm only (no Spotify).
- Roadmap: checked off heatmap (Batch 18 Phase 1 complete, Phase 2 in progress);
  corrected "350 tests / 23 files" to "385 / 24".
- Test badge: 350 -> 385.

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

### 2026-03-05 - side-task: PR review fixes (CI cache, DEVELOPMENT.md, README, doc tidiness, SDLC table)

- **`.github/workflows/test.yml`**: fixed `cache-dependency-path` from
  `requirements-dev.txt` to `requirements*.txt`. The dev file starts with
  `-r requirements.txt` but pip's cache key computation does not follow
  transitive includes; changes to `requirements.txt` alone would not
  invalidate the cache. Fix ensures both files are hashed for the key.
- **`DEVELOPMENT.md`**: corrected the SESSION_CONTEXT.md CI presence
  claim. Previous text said the file is "absent in GitHub Actions" --
  inaccurate since SESSION_CONTEXT.md is now committed and a standard
  `actions/checkout@v4` includes it. Updated to say "normally present;
  `_read_lines_optional()` is a fallback for edge cases (sparse checkout
  or custom workflow)."
- **`README.md`**: three stale items corrected from Batch 17 changes:
  (1) CI/CD table row updated -- standalone flake8 removed in WP-2; pip-audit
  added in WP-2; description now reads "Quality Gate (pre-commit, pytest +
  coverage gate, pip-audit)"; (2) Code Quality row: added
  check-merge-conflict and detect-private-key (added in WP-2 addendum);
  (3) Local Dev section: SESSION_CONTEXT.md Section 8 ref (broken after
  WP-4 renumbering + Docker setup moved to AGENT_NOTES.md) -> AGENT_NOTES.md.
- **`BATCH17_DEFINITION.md`**: removed duplicate `---` separator between
  "## 6. Deferred" and "## Supplementary Info" (double rule was redundant).
- **`PLAYBOOK.md` WP-4 note**: updated "Candidate for a future cleanup
  pass" -> "Subsequently fixed in a side-task (see logarchive)" so PR
  reviewers do not see the WP-4 note as an open item that is also fixed
  in the same PR diff.
- **`DEVELOPMENT.md` SDLC table**: CI gate row updated from stale
  "GitHub Actions: pre-commit + flake8 + pytest + coverage" to "Quality
  Gate (pre-commit, pytest + coverage gate, pip-audit)" to match the
  README change and the WP-2 workflow rename.
- **350 tests passing**, all hooks green.

### 2026-03-05 - side-task: doc accuracy fixes (AGENTS.md, HANDOFF_PROMPT.md)

- **AGENTS.md**: "these doc files" -> "the doc files listed below" (dangling pronoun
  with no referent; table follows the section break, not the sentence).
- **HANDOFF_PROMPT.md**: SESSION_CONTEXT step 4 now reads "Sections 3-5" instead of
  "Sections 3-4". Section 5 is the dedicated Architecture overview; "Sections 3-4"
  would have left agents one section short when looking for architecture detail.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: requirements pinning + venv/agent safety rules

- **Pin previously unpinned packages**: `asyncpg>=0.29.0` -> `==0.31.0` and
  `Flask-WTF>=1.2.0` -> `==1.2.2` in `requirements.txt`. All five packages in
  `requirements-dev.txt` pinned to exact installed versions (flake8==7.3.0,
  pre-commit==4.5.1, pytest==9.0.2, pytest-asyncio==1.3.0, pytest-cov==7.0.0).
  Eliminates version drift on venv reinstall.
- **Incident root cause (2026-03-04):** Prior agent session ran
  `source venv/Scripts/activate && pip install flask-talisman` targeting the
  wrong `venv/` directory instead of `.venv/`. The `.venv/` was subsequently
  found empty (likely drained by the same session); reinstall from requirements
  files brought packages back at new versions for previously unpinned entries.
  Multiple background `python app.py` processes were also started via Bash tool
  and not cleaned up, blocking the owner terminal. User touched zero code.
- **AGENTS.md updated**: Environment Setup section corrected (`venv/` -> `.venv/`,
  bare `pip` -> `.venv/Scripts/pip`, added pinning requirement). Anti-Pattern
  Registry entries 4 and 5 added (wrong venv / bare pip, background server
  processes).
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: gunicorn threading + dark mode browser preference

- **Gunicorn threading**: added `--threads 4` to Dockerfile CMD. Single sync worker
  was serializing all HTTP requests in production; threads allow concurrent request
  handling while keeping JOBS dict in shared process memory.
- **Dark mode fix**: `theme.js` now falls back to `window.matchMedia('(prefers-color-scheme: dark)')`
  when no localStorage preference is saved. First-visit users with browser dark mode
  enabled will see dark theme automatically. Explicit toggle still overrides.
- Load test findings (local, 1-5 concurrent users) documented in agent memory.
  Spotify cache TTL verified correct (ToS compliant). No upstream 429s at 2-5 users.

### 2026-03-04 - side-task: log rotation fix

- **Log rotation**: changed `RotatingFileHandler` to 2MB files / 10 backups (was 1MB / 5).
  Small files stay granular and parseable; 10 backups cover a full load test session.
  No production impact -- file is ephemeral on Fly.io; stdout is the prod log channel.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: PR code review fixes

- **theme.js**: `var` -> `const` for `saved` and `prefersDark` (neither reassigned;
  aligns with `const`/`let` convention in all other JS files).
- **Dockerfile**: added comment explaining `--workers 1 --threads 4` rationale for
  Fly.io deployment (shared-cpu-2x / 512MB, JOBS dict requires single process).
- **350 tests passing**, all hooks green.

### 2026-03-03 - Review-driven fixes: barrier safety, session cleanup, Docker error handling, dev_start tests

**Scope:** Side-task -- address Co-Pilot code review findings from PR #56, add
subprocess timeout guards, and add the deferred `dev_start.py` unit tests (now
warranted by increased error-handling complexity).

**Fixes applied:**
1. `concurrent_users_test.py` -- moved `barrier.wait()` inside `try` block so
   `BrokenBarrierError` is captured and a `ConcurrentResult` is always appended
   (docstring guarantee upheld).
2. `concurrent_users_test.py` -- track sessions in a list, call `session.close()`
   after `join()` to prevent connection/socket leaks.
3. `dev_start.py` -- `check_container_status()` now distinguishes "No such object"
   (returns `None`) from Docker daemon errors (raises `RuntimeError` with actionable
   message) and unexpected errors (raises with stderr details).
4. `dev_start.py` -- added `timeout=10` to `docker inspect` and `timeout=30` to
   `docker start` subprocess calls; catches `subprocess.TimeoutExpired` and raises
   `RuntimeError` with clear messaging.

**New tests:** 11 unit tests in `tests/scripts/dev/test_dev_start.py` covering
`check_container_status` (6 paths: running, absent, docker-not-found, timeout,
daemon-not-running, unexpected error), `start_container` (success, failure, timeout),
`main` (absent container exit, exited container start+exec).

**Validation:** `pytest -q` -- **350 passed**. `pre-commit run --all-files` -- all
hooks pass.

### 2026-03-03 - Fix Windows asyncpg startup packet (ProactorEventLoop) (side-task)

**Scope:** Side-task -- two-stage Windows-only cache fix. No code changes for
the Fly.io (Linux) deployment path.

**Errors encountered and resolved (session log):**

1. `.env` typo `DDATABASE_URL` (double-D prefix) -- cache silently disabled.
   Fixed by correcting the typo in `.env`.

2. `os.environ.get("DATABASE_URL")` returned `None` in background worker threads
   on Windows. Werkzeug debug reloader spawns a child process; `load_dotenv()`
   ran in the parent but environment variables were not reliably inherited.
   Fixed in `468b519`: capture `_DATABASE_URL = os.environ.get("DATABASE_URL")`
   at module import time in `cache.py` (runs once after `app.py` calls
   `load_dotenv()`). Also path-anchored `load_dotenv()` in `app.py` so it
   finds `.env` regardless of working directory.

3. `_DATABASE_URL` confirmed set (len=59) but asyncpg still failed silently.
   Docker logs revealed: `invalid length of startup packet` (10 rapid rejections
   -- matching 3 retries x multiple test runs). Root cause: `asyncio.new_event_loop()`
   in a daemon thread under Werkzeug's debug reloader on Windows creates a
   `SelectorEventLoop`, not a `ProactorEventLoop`. asyncpg uses Windows IOCP
   via `ProactorEventLoop`; with `SelectorEventLoop` it sends incorrect startup
   bytes and Postgres rejects the connection immediately.
   Fixed in `97db0c9`: `background_task()` in `orchestrator.py` now calls
   `asyncio.ProactorEventLoop()` when `sys.platform == "win32"`, falling back to
   `asyncio.new_event_loop()` on all other platforms (Linux/Fly.io unchanged).

4. `RotatingFileHandler` fails with `PermissionError: [WinError 32]` when
   multiple Flask processes hold the log file open simultaneously (Werkzeug
   debug reloader + interleaved restarts). Cosmetic only -- Flask continues to
   serve. Not fixed; documented here for future reference.

**Deploy safety:** Fix 3 uses `if sys.platform == "win32":` guard exclusively.
Fly.io (Linux) takes `asyncio.new_event_loop()` unchanged.

**Implementation:**
- `scrobblescope/orchestrator.py` -- `background_task()` updated (`97db0c9`)
- `scrobblescope/cache.py` -- `_DATABASE_URL` captured at module level (`468b519`)
- `app.py` -- path-anchored `load_dotenv()` (`468b519`)
- `tests/test_repositories.py` -- 4 tests updated to patch
  `scrobblescope.cache._DATABASE_URL` directly instead of `os.environ` (`468b519`)

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. Smoke test: `verdict=PASS`, `db_cache_lookup_hits=44`, elapsed ~1.05s
(vs ~6s cold Spotify fetch). Fly.io deploy path confirmed unaffected by guard.

**Forward guidance:** Cache subsystem is fully working locally. WP-2 is next:
13 unit tests for `_http_client` and `smoke_cache_check` in
`tests/test_smoke_cache_check.py`.

### 2026-03-03 - Improve agent orientation docs (side-task)

**Scope:** Side-task -- documentation only, no code changes. Improve agent
bootstrap reliability by fixing stale references and adding missing setup steps.

**Changes:**
- DEVELOPMENT.md: replaced stale "SESSION_CONTEXT is gitignored/ephemeral" text
  (lines 83-93) with accurate description of committed+tracked status, explicit
  `.gitignore` exception, and rationale for sharing across agents.
- AGENTS.md Environment Setup: added venv activation commands (Windows + Linux)
  so agents can run `pytest` and `pre-commit` without trial-and-error.
- AGENTS.md "What to update after a WP": added README deferral exception noting
  that README updates may be batched into a dedicated WP when the batch definition
  specifies one (e.g., Batch 16 WP-5).

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-1 is next. README will be stale during intermediate WPs;
updates deferred to WP-5 per batch definition.

### 2026-03-03 - Batch 16 definition written and activated (Batch 16 activation)

**Scope:** Define Batch 16 and activate it in PLAYBOOK + SESSION_CONTEXT.

**Plan:** Write `BATCH16_DEFINITION.md` incorporating audit corrections (stat key
fix, size caps removed, MEMORY.md references clarified as agent-private). Move to
`docs/history/definitions/`. Activate Batch 16 in PLAYBOOK Section 3. Update
SESSION_CONTEXT Section 2. Update HANDOFF_PROMPT.md and MEMORY.md for handoff.

**Implementation:** Definition written; audit findings applied (verdict key
`cache_hits` corrected to `db_cache_lookup_hits`, size caps removed per owner
instruction, `memory/MEMORY.md` removed from formal acceptance criteria). Definition
placed at `BATCH16_DEFINITION.md` (root; moves to archive at batch close-out). PLAYBOOK and
SESSION_CONTEXT activated. HANDOFF_PROMPT and MEMORY updated for clean handoff.

**Deviations:** None.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-0 is next: create `scripts/testing/` and `scripts/dev/`
directories, move `smoke_cache_check.py` via `git mv`, update AGENTS.md and
SESSION_CONTEXT path references. No logic changes in WP-0.

### 2026-03-03 - Fix SESSION_CONTEXT.md commit convention and stage accumulated changes

**Scope:** Side-task -- documentation and gitignore fix, no code changes.

**What:** SESSION_CONTEXT.md was never staged in the two previous side-task commits
(`c4bf737`, `4f1cf6a`) despite commit messages implying it. SESSION_CONTEXT.md has
been git-tracked since before `edee612` (when `.claude/` was added to .gitignore).
The `.gitignore` entry `.claude/` is misleading -- SESSION_CONTEXT.md is grandfathered
in as a tracked file. Fix: update `.gitignore` to `.claude/*` + `!.claude/SESSION_CONTEXT.md`
so the exception is explicit. Fix AGENTS.md: remove incorrect "SESSION_CONTEXT is
gitignored" language. Stage the accumulated SESSION_CONTEXT.md changes (Batch 15 state
update, Section 8 browser MCP note, Section 8 local Postgres note).

**Why:** SESSION_CONTEXT.md is the shared cross-agent dashboard. All agents (Gemini,
Copilot, Codex, Claude Code) bootstrap from it. Leaving it uncommitted means every agent
starts with stale branch, test count, and batch status. The gitignore fix makes the
tracked-exception visible and prevents future agents from falsely concluding the file
is machine-local.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. BATCH16_PROPOSAL.md written; awaiting owner review.

### 2026-03-03 - Add local DB setup and init_db.py caveat to env docs

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added local Postgres DB setup details and `init_db.py` load_dotenv caveat
to AGENTS.md Environment Setup and SESSION_CONTEXT Section 8. These facts apply to
all agents (Gemini CLI, Copilot, Codex, Claude Code) running local DB tests.

**Why:** `init_db.py` has no `load_dotenv()` call. Any agent running it will get
"DATABASE_URL not set" unless the env var is set directly in the shell. Absent from
canonical docs, every agent would hit this silently and assume cache is unavailable.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

### 2026-03-03 - Add browser MCP environment note to SESSION_CONTEXT

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added one line to SESSION_CONTEXT Section 8 (Environment notes) documenting
that the browser MCP accesses the local Flask app via `http://host.docker.internal:5000/`
rather than `localhost`, because the MCP browser runs inside a Docker container.

**Why:** This is a runtime fact that future agent sessions need to reproduce local
browser testing correctly. Absent from SESSION_CONTEXT, an agent would attempt
`localhost` and get a connection refused error with no clear diagnosis path.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

### 2026-03-02 - Session findings and handoff notes (side-task)

**Scope:** Observations from Batch 15 WP-1 execution session, documented for
next-agent orientation.

**Findings:**
1. **docsync `--fix` SESSION_CONTEXT write bug (fixed):** `cli.py` computed the
   correct STATUS block but never wrote it. Fixed in commit `67fa1dc`. AGENTS.md
   cross-validation section updated to reflect corrected behavior.
2. **Deviation tag routing:** Headings with non-standard tags like
   `(Batch 15 WP-1 deviation)` do NOT match `ENTRY_BATCH_RE` regex
   (`\(Batch\s+(\d+)\s+WP-\d+\)`). They are routed outside CURRENT-BATCH
   markers as untagged entries. This is correct behavior -- use standard
   `(Batch N WP-X)` tags only for entries that should stay inside markers.
3. **Mid-batch handoff discipline (added):** AGENTS.md now requires PLAYBOOK
   Section 3 to reflect true state at all times, not just after commits.
4. **SESSION_CONTEXT Section 7 is stale:** Shows 307 tests across old counts.
   Actual: 311 tests across 18 files. WP-2 will fix this.
5. **README.md is stale:** Says 257 tests, lists incomplete pre-commit hooks,
   project structure test section outdated. WP-2 will fix this.
6. **HANDOFF_PROMPT.md is stale:** References deleted branch, old audit, old
   tasks. WP-5 will replace it; interim handoff written for this transition.

**Forward guidance:**
- Next agent should start with WP-2 per BATCH15_DEFINITION.md execution order.
- Always use standard `(Batch N WP-X)` tags for batch log entries.
- Run `doc_state_sync.py --fix` after every PLAYBOOK Section 4 edit.

### 2026-03-02 - Fix docsync --fix not writing SESSION_CONTEXT STATUS block (Batch 15 WP-1 deviation)

**Scope:** `scripts/docsync/cli.py`, `tests/test_docsync_cli.py`, `AGENTS.md`.

**Plan vs implementation:**
- Planned: during WP-1 execution, discovered that `doc_state_sync.py --fix`
  computes the correct STATUS block for SESSION_CONTEXT but never writes it
  to disk. AGENTS.md line 138-139 claimed the script "Refreshes the
  machine-managed DOCSYNC:STATUS block" but the code only warned on staleness
  without writing. This was a bug, not a design choice.
- Implemented: modified `cli.py` so `--fix` writes the refreshed STATUS block
  to SESSION_CONTEXT when stale. `--check` continues to warn-only (does not
  fail) because SESSION_CONTEXT is gitignored and should not block commits.
  Updated AGENTS.md cross-validation section to reflect corrected behavior.
  Added 1 new test (`test_fix_refreshes_session_context_status_block`) and
  updated the stale-warning assertion text in existing test.

**Deviations:**
- This fix was not in the Batch 15 definition. It was discovered during WP-1
  when the agent attempted to run `--fix` and found SESSION_CONTEXT unchanged.
  The fix is scoped to the bug and does not change any other docsync behavior.

**Validation:**
- `pytest tests/test_docsync_cli.py -v` (**19 passed**)
- `pytest -q` (**311 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --fix` (wrote SESSION_CONTEXT)
- `python scripts/doc_state_sync.py --check` (pass, no stale warning)
- `pre-commit run --all-files` (pass, all 8 hooks)

**Forward guidance:**
- After any PLAYBOOK Section 4 edit, run `doc_state_sync.py --fix` and verify
  SESSION_CONTEXT STATUS block was updated. The script now handles this
  automatically.

### 2026-02-27 - Revalidate audit findings and prepare next-agent packet (side-task)

**Scope:** `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md`,
`tests/test_docsync_logic.py` (format-only), repo-wide quality gates.

**Plan vs implementation:**
- Planned: verify previously reported findings against current branch state,
  refresh stale assertions, and produce implementation-ready guidance for the
  next agent handoff.
- Implemented: re-ran full validations, updated stale test baseline and
  resolved-item status in the audit report, and added a scoped next-agent
  implementation packet with acceptance criteria.

**Deviations:**
- No behavioral code changes were required; only audit/report updates plus
  formatter-normalized whitespace in `tests/test_docsync_logic.py`.

**Validation:**
- `pre-commit run --all-files` (pass)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Execute the next-agent packet in commit-sized slices: test-module split,
  low-risk orchestrator extraction, then CI/session policy wording alignment.

### 2026-02-27 - Harden docsync non-happy-path coverage + path guidance (side-task)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`AGENTS.md`, `PLAYBOOK.md`.

**Plan vs implementation:**
- Planned: enforce anti-happy-path discipline for docsync archive-link and
  migration handling, and remove path ambiguity between untagged archive,
  per-batch logs, and definitions.
- Implemented: added adversarial tests for `docs/logarchive` link validation
  (exists/missing) and for `--split-archive` missing-input failure (`exit 2`),
  plus explicit archive/log/definition lookup guidance in AGENTS and PLAYBOOK.

**Deviations:**
- One assertion was adjusted to be path-separator-agnostic on Windows
  (`PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` substring) after first run exposed
  slash-vs-backslash brittleness.

**Validation:**
- `pytest -q tests/test_docsync_logic.py tests/test_docsync_cli.py`
  (**57 passed**)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Keep new docsync tests behavior-focused (real inputs + failure paths), not
  mock-call-only checks, when adding future archive-routing rules.

### 2026-02-27 - Migrate monolith archive path to docs/logarchive (side-task)

**Scope:** `scripts/docsync` path canonicalization, pointer compatibility docs,
doc references, regression validation.

**Plan vs implementation:**
- Planned: stop using the legacy history monolith paths
  (`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
  `docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`) as the
  canonical monolith location and move to a dedicated `docs/logarchive/`
  folder with clear pointers from legacy paths.
- Implemented: switched docsync `ARCHIVE_PATH` to
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, copied canonical
  archive content there, converted both legacy monolith files into pointer
  documents, and added `docs/logarchive/README.md` lookup guidance.

**Deviations:**
- Historical documents under `docs/history/definitions/` and batch logs were
  left unchanged to preserve historical wording; compatibility pointers prevent
  breakage for legacy references.

**Validation:**
- `python scripts/doc_state_sync.py --fix`
- `python scripts/doc_state_sync.py --check`
- `pytest -q tests/test_docsync_cli.py tests/test_docsync_logic.py`
  `tests/test_docsync_parser.py tests/test_docsync_renderer.py` (**103 passed**)
- `pytest -q` (**307 passed**, 3 deprecation warnings from aiohttp connector)

**Forward guidance:**
- Use `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for untagged archive
  search and keep per-batch logs under `docs/history/logs/` as the tagged route.

### 2026-02-27 - Branch hygiene cleanup after main diff review (side-task)

**Scope:** orchestration hygiene (`.gitignore`, PLAYBOOK state consistency,
root audit-file placement), docsync warning cleanup.

**Plan vs implementation:**
- Planned: remove non-actionable docsync warning noise and align tracked state
  with the "local-only" `.claude/SESSION_CONTEXT.md` policy.
- Implemented: scoped `BATCH*_AUDIT*.md` ignore rule to repo root only,
  moved `BATCH14_PROPOSAL_AUDIT1.md` from root into `docs/history/`, and
  recorded the side-task in Section 4.

**Deviations:**
- `git mv` could not be used for `BATCH14_PROPOSAL_AUDIT1.md` because the file
  was not under version control; file-system move was used instead.

**Validation:**
- Ran `python scripts/doc_state_sync.py --fix` and
  `python scripts/doc_state_sync.py --check` after edits.

**Forward guidance:**
- Keep root-only draft/audit patterns scoped with leading `/` in `.gitignore`
  so archive destinations under `docs/history/` remain trackable.

### 2026-02-26 - Remediate docsync audit findings (side-task)

**Scope:** `scripts/docsync/` (cli, parser, renderer, logic),
test suite (parser, renderer, logic), `AGENTS.md`.

**Changes:**
- Fixed unconditional PLAYBOOK/ARCHIVE writes in --fix mode (F1).
- Consolidated SyncError import to top-level in cli.py (F11).
- Defined TEST_COUNT_RE once in parser.py (F2).
- Extracted _dedup_sorted() helper in logic.py (F3).
- Tightened ENTRY_BATCH_RE to require (Batch N WP-X) format (F6).
- Added duplicate-marker detection in _find_marker_pair (F7).
- Added sentinel -1 comment (F5).
- Removed dead stale-phrase detection + 3 tests (F8).
- Fixed misleading docstring (9a), weak assertion (9b).
- Added 4 tests: duplicate headings (9c), adversarial regex (9d),
  duplicate markers (F7), file-order dependency (9e).

**Test count:** **307 passed** (net +1: -3 removed, +4 added).
**Validation:** `pytest -q` 307 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - Post-batch test suite audit (doc hygiene)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`tests/test_docsync_parser.py`; deleted `tests/test_docsync_models.py`.

**Changes:**
- Fixed `test_deduplication_across_archive`: was passing vacuously -- tagged
  entry routed to `batch_log_updates`, bypassing monolith dedup entirely;
  rewrite uses untagged entry and asserts `batch_log_updates == {}`.
- Dropped `test_current_entry_count_mismatch_warns`: near-duplicate of
  `test_mismatched_counts_warns` (identical `_cross_validate` code path).
- Rewrote `test_section4_historical_count_ignored`: old version had no
  CURRENT-BATCH markers so `_latest_test_count_from_entries` returned None
  vacuously; new version confirms below-end-marker counts are ignored while
  inside-marker count is used for comparison.
- Removed unused `LOGS_DIR` name import from `test_docsync_cli.py`.
- Merged 5 `_fingerprint`/`_extract_entry_batch` tests from misnamed
  `test_docsync_models.py` into `test_docsync_parser.py`; deleted old file.
- Added `TestSplitArchiveMode.test_split_archive_routes_tagged_entry` for
  the previously uncovered `--split-archive` CLI branch.

**Test count:** **306 passed** (net zero: -6 removed, +6 added).
**Validation:** `pytest -q` 306 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - fix(doc-sync): remediate SESSION_CONTEXT staleness in _cross_validate and _build_status_block (side-task)

- Scope: `scripts/docsync/logic.py`, `scripts/docsync/renderer.py`, `scripts/docsync/cli.py`,
  `tests/test_docsync_logic.py` (+6 tests: 4 TestLatestTestCount + 2 rewritten + 1 renamed),
  `tests/test_docsync_renderer.py` (+2 TestBuildStatusBlock count tests),
  `tests/test_docsync_cli.py` (1 test updated).
- Problem: Two root causes for SESSION_CONTEXT staleness: (1) `_cross_validate` scanned
  PLAYBOOK Section 3 for `**N passed**` counts, but agents write test counts in Section 4
  log entry Validation fields — Section 3 is narrative prose. `playbook_counts` was always
  empty so the mismatch warning never fired. (2) `_build_status_block` did not include the
  test count in the STATUS block output, forcing agents to check stale manual rows.
  Additionally, `_cross_validate` was called with `result.session_lines` (post-sync), which
  already had the correct count injected by `_build_status_block`, laundering mismatch away.
- Fix: Added `_latest_test_count_from_entries(playbook_lines)` to `logic.py` — parses
  Section 4 current-batch entries newest-first and returns the first `**N passed**` count.
  Updated `_cross_validate` to call this function (scalar comparison) instead of scanning
  Section 3. Added `_TEST_COUNT_RE` to `renderer.py`; `_build_status_block` now emits
  `"- Latest validated test count: **N passed**."` using the most-recent entry body count.
  Fixed `cli.py` to call `_cross_validate(playbook_lines, session_lines)` (original, pre-sync
  lines) so the STATUS block update cannot launder a pre-existing mismatch.
- Deviations: None. All changes additive; no logic in `_sync` was touched.
- Validation: **294 passed** (+6 vs WP-2 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - docs(audit): add BATCH14 pre-approval audit report and apply corrections to proposal (side-task)

- Scope: `BATCH14_PROPOSAL.md`, `docs/history/BATCH14_AUDIT_2026-02-25.md`.
- Purpose: Pre-batch audit of BATCH14_PROPOSAL.md before owner sign-off. Verified
  all five structural checks (WP-1 naming conventions, WP-2 package extraction
  symmetry, WP-3 feature isolation, WP-4 test distribution, WP-5 AGENTS.md
  close-out / MEMORY.md hallucination check). All five checks confirmed correct.
- Correction: "~450-line" description for `doc_state_sync.py` corrected to "~679-line"
  in two places (Current state table and WP-2 goal). Actual measured line count: 679.
- Verdict: APPROVED WITH CORRECTIONS.
- Validation: 288 passed (unchanged -- audit makes no code changes), all 8 pre-commit
  hooks passed.

### 2026-02-25 - test(worker): assert daemon=True via Thread patch, expand docstrings (side-task)

- Scope: `tests/test_worker.py`.
- Problem: `test_start_job_thread_creates_daemon_thread` only asserted the target
  was called; it never verified `threading.Thread` was constructed with `daemon=True`,
  despite the test name and docstring claiming otherwise. Tests 1–4 had minimal
  single-line docstrings inconsistent with the GIVEN/WHEN/THEN standard.
- Fix: Introduced `DummyThread` class, patched at `scrobblescope.worker.threading.Thread`;
  asserts `daemon=True` and target invocation. Dropped `*args` from `DummyThread.__init__`
  (Pylance hint; Thread is called with keyword args only). Expanded tests 1–4 docstrings
  to GIVEN/WHEN/THEN inline format.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - test(retry): use public semaphore API in semaphore-gates test (side-task)

- Scope: `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer flagged `sem._value == 0` as a private implementation detail
  of `asyncio.Semaphore`, suppressed with `# noqa: SLF001`, making the assertion
  brittle across Python versions.
- Fix: Replaced with `sem.locked()`, the public equivalent (stable since Python 3.4).
  Updated comment; noqa suppression removed. Confirmed only occurrence in suite.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - fix(utils): support constant backoff value in retry_with_semaphore (side-task)

- Scope: `scrobblescope/utils.py`, `scrobblescope/spotify.py`,
  `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer 1 flagged that `backoff` only accepted a callable, requiring
  `backoff=lambda _a: 1` for constant delays. Updating call sites to use a plain
  float was not possible without a utility change.
- Fix: Added `callable(backoff)` guard at line 341 of `utils.py`; updated docstring
  type annotation. Simplified `spotify.py` search call site to `backoff=1`. Added
  `test_constant_float_backoff_accepted` to `test_retry_with_semaphore.py`.
- Validation: 288 passed (+1 vs Batch 13 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - test(orchestrator): use standard asyncio import in fetch_spotify tests (side-task)

- Scope: `tests/services/test_orchestrator_fetch_spotify.py`.
- Problem: Reviewer 2 flagged two `__import__("asyncio").Semaphore(5)` usages
  bypassing Pylance type resolution; root cause was missing top-level `import asyncio`.
- Fix: Added `import asyncio` to stdlib imports block; replaced both
  `__import__("asyncio").Semaphore(5)` occurrences with `asyncio.Semaphore(5)`.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-24 - docs(audit): BATCH13 pre-approval audit report (side-task)

- Scope: `BATCH13_PROPOSAL.md`, `docs/history/BATCH13_AUDIT_2026-02-23.md`.
- Problem: BATCH13 proposal required independent technical verification before
  owner approval. Line references, test coverage claims, retry extraction
  design, and convention compliance needed validation against actual codebase.
- Fix: Completed 4-WP audit. Found 5 discrepancies: `_apply_pre_slice` line
  start off by 2 (L664 -> L666), `_JOB_SEMAPHORE` variable name incorrect
  (actual: `_active_jobs_semaphore`), batch retry missing jitter declaration,
  batch backoff incorrectly stated as fixed 1.0 (actual: `2**attempt`
  exponential). Applied all corrections to the proposal. Created audit report.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed. No source
  code changes -- audit only.

### 2026-02-23 - chore(merge): integrate main into wip/pc-snapshot (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py` (merge
  resolution only -- no net change from branch perspective).
- Problem: `main` had one commit ahead (`05c7b19`) that was already
  cherry-picked into `wip/pc-snapshot` as part of `4e4c9a1`. The branch
  needed to formally integrate `main` before PR #36 could merge cleanly.
- Fix: `git merge origin/main --no-edit`; ort strategy resolved cleanly
  (identical content on both sides for the two touched files). Merge commit
  `d98c90b` amended to conventional format.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-23 - fix/docs: cherry-pick SESSION_CONTEXT optional + DEVELOPMENT.md (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py`,
  `DEVELOPMENT.md`, `docs/history/SESSION_CONTEXT_REFERENCE.md`, `README.md`.
- Problem: (1) CI failed on `main` when `.claude/SESSION_CONTEXT.md` was
  absent (gitignored). The script called `_read_lines()` unconditionally,
  raising `SyncError`. (2) No documentation existed for the multi-agent
  orchestration methodology implemented during this sprint.
- Fix:
  (1) Cherry-picked commit `05c7b19` from `main`: added `_read_lines_optional()`
  returning `None` when the file is absent; gated all SESSION_CONTEXT
  operations in `_sync()`, `_cross_validate()`, and `main()` behind
  presence check; `SyncResult.session_lines` typed as `list[str] | None`;\
  renamed `test_missing_session_context_raises` to `_succeeds`; added
  `TestMissingSessionContext` class (3 regression tests).
  (2) Created `DEVELOPMENT.md` explaining the orchestration architecture,
  why `doc_state_sync.py` is a deterministic script, the batch/WP SDLC
  mapping, review-rejection rationale, and what failed before the current
  system stabilized. Created `docs/history/SESSION_CONTEXT_REFERENCE.md`
  as a tracked reference snapshot of the gitignored live file. Linked
  both from `README.md` (new "Development Methodology" section in ToC).
- Validation: **260 tests passing** (3 new from cherry-pick),
  pre-commit all 8 hooks passed.

### 2026-02-23 - chore/docs: repo hygiene and README rewrite (side-task)

- Scope: root directory, `.gitignore`, `README.md`, `.claude/`.
- Problem: (1) Root directory cluttered with completed batch definitions
  (`BATCH12_PROPOSAL.md`, `BATCH8_REFACTOR_PLAN.md`) and an obsolete
  playbook compatibility shim (`EXECUTION_PLAYBOOK_2026-02-11.md`).
  (2) `.claude/` tracked in git (agent-local state, stale `BATCH3_CONTEXT.md`,
  machine-specific `settings.local.json`). (3) `README.md` outdated --
  "work in progress" status badge, 30+ completed checkbox items, missing
  Architecture/Deployment sections, stale Tech Stack section.
- Fix:
  (1) `git mv` both batch definitions to `docs/history/`. `git rm`
  the playbook shim. Deleted untracked stale files (`backup.py`,
  `Backup_batch`, empty `app/` directory).
  (2) Added `.claude/` to `.gitignore`, `git rm --cached` all 3 tracked files,
  deleted stale `BATCH3_CONTEXT.md` locally.
  (3) Comprehensive README rewrite: active status badge + test count badge,
  new Architecture section with pipeline diagram + design decisions, Tech
  Stack table, Deployment section with Fly.io commands + smoke test,
  condensed Roadmap (upcoming + recent completions only), accurate Project
  Structure tree with per-file annotations and test counts, Running Tests
  section, trimmed Contributing/License/Acknowledgements.
- Validation: **257 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-22 - fix(app): guard sys.stderr.reconfigure with isinstance check

- Scope: `app.py`.
- Problem: Pyright/Pylance reported "Cannot access attribute reconfigure for
  class TextIO" because `sys.stderr` is typed as `TextIO`, which lacks
  `reconfigure`. The method exists at runtime on `io.TextIOWrapper`.
- Fix: Added `import io` and wrapped the call in
  `if isinstance(sys.stderr, io.TextIOWrapper):` -- a type-narrowing guard
  that satisfies both the type checker and runtime safety.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all hooks passed.

### 2026-02-22 - refactor(routes,lastfm): SoC/DRY cleanup from third-party audit

- Scope: `scrobblescope/routes.py`, `scrobblescope/lastfm.py`,
  `scrobblescope/orchestrator.py`, `tests/services/test_lastfm_logic.py`.
- Problem: Three findings from a third-party structural audit:
  (1) SoC -- `get_filter_description` was a public helper placed between HTTP
  handlers; lacked `_` prefix used by the other private helpers.
  (2) DRY -- `/results_complete` and `/unmatched_view` duplicated ~10 lines
  of identical `job_id`/`job_context` guard logic.
  (3) SoC -- `fetch_top_albums_async` in `lastfm.py` imported `set_job_stat`
  from `repositories.py` and made 5 direct job-state mutations. An API client
  module should return pure data, not mutate application state. `spotify.py`
  already follows this pattern correctly.
- Fix:
  (1) Renamed to `_get_filter_description` and hoisted above HTTP handlers,
  below `_group_unmatched_by_reason`.
  (2) Extracted `_get_validated_job_context(missing_id_message, expired_error,
  expired_message, expired_details)` returning `(job_id, job_context, None)`
  or `(None, None, error_response)`.
  (3) Removed `job_id` param and `set_job_stat` import from
  `fetch_top_albums_async`. Stats now returned in `fetch_metadata["stats"]`
  dict. `orchestrator._fetch_and_process` extracts and records them.
  Partial-data warning also moved to `fetch_metadata` return path.
- Deviations: Audit claimed ~15-20 lines of duplication; actual overlap was
  ~10 lines. Error titles intentionally differ between routes, so
  `expired_error` was parameterized rather than hardcoded.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-22 - fix(types): resolve 10 Pylance type errors in production code

- Scope: `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`,
  `scrobblescope/utils.py`.
- Problem: Pylance reported 10 type errors across 3 production files:
  (1) `lastfm.py` (7): `metadata` dict inferred as `dict[str, str | int]`
  caused arithmetic and nested-dict assignment failures; `albums` defaultdict
  inferred heterogeneous union on all value accesses.
  (2) `spotify.py` (2): `SPOTIFY_CLIENT_ID/SECRET` typed `str | None` from
  `os.getenv()` but `aiohttp.BasicAuth` requires `str`.
  (3) `utils.py` (1): `loop` assigned inside `try:` block, referenced in
  `finally:` -- possibly unbound if `new_event_loop()` raises.
- Fix: Annotated `metadata: dict[str, Any]` and
  `albums: defaultdict[str, dict[str, Any]]` in lastfm.py; added assert
  guards for Spotify credentials in spotify.py; initialized `loop = None`
  with `if loop is not None:` guard in utils.py.
- Test file type errors (25 across 3 files) assessed as low-impact
  mock-related noise -- deferred.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-21 - refactor/fix: Gemini audit remediation (non-normalization track)

- Scope: `scrobblescope/orchestrator.py`, `scrobblescope/cache.py`,
  `scrobblescope/routes.py`, `scrobblescope/domain.py`,
  new `scrobblescope/errors.py`, `scrobblescope/repositories.py`,
  `tests/services/test_orchestrator_service.py` (+4 tests),
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md` (new doc).
- Problem: A second Gemini Pro audit pass identified four issues beyond the previously
  fixed normalization bugs. Three were confirmed real against the live codebase:
  1. Late slicing: `limit_results` applied after Spotify calls in `_fetch_and_process`.
     For playcount sort the ranking is fully known from Last.fm data; pre-slicing
     to the requested limit eliminates unnecessary Spotify searches on cache misses.
     (Playtime sort cannot be pre-sliced -- ranking requires track duration data.)
  2. Indefinite DB growth: `_batch_lookup_metadata` filtered stale rows at read time
     but no DELETE ever ran. Stale rows accumulated in `spotify_cache` indefinitely.
  3. ERROR_CODES + SpotifyUnavailableError in `domain.py`: a SoC violation -- domain
     logic should not own user-facing message strings or retryability flags.
  A fourth SoC issue not in the original report was also fixed: duplicate release_scope
  -> human-text translation in `routes.py` (inline block in `unmatched_view`
  duplicating `get_filter_description`). A fifth issue (empty-result hallucination)
  was assessed and deferred as near-false-alarm -- the trigger conditions require
  zero cache hits AND every album absent from Spotify, which is extremely unlikely.
- Plan vs implementation: all four confirmed issues fixed as described in
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **114 passed** (110 pre-existing + 4 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - Import graph: `errors.py` is a leaf module (no package imports). Acyclic structure
    preserved. `domain.py` now contains only normalization logic.
- Forward guidance: next sub-track is "sycophantic test coverage" audit (owner to
  elaborate scope). Feature work (top songs, heatmap) blocked until owner assigns a
  future batch number and defines scope. `_cleanup_stale_metadata` is opportunistic and non-fatal;
  monitor logs for "Stale cache cleanup" entries to confirm it fires in production.
  The playtime late-slicing limitation is documented inline in `_fetch_and_process`.

### 2026-02-21 - fix(domain): fix normalization bugs silently excluding non-Latin albums

- Scope: `scrobblescope/domain.py`, `tests/test_domain.py` (9 new tests),
  `tests/services/test_lastfm_logic.py` (new file, 7 tests),
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md` (new doc).
- Problem: A third-party static analysis review (Gemini Pro) identified four
  defects in `domain.py` and a coverage gap in `lastfm.py`. All four were
  confirmed against the live codebase and three had measurable production impact:
  1. `normalize_track_name` used `NFKD + encode("ascii","ignore")`, stripping all
     non-Latin characters to `""`. Any album with Japanese/Cyrillic/etc. track names
     had `len(track_counts) == 1` regardless of distinct tracks played, silently
     failing the `min_tracks` filter and disappearing from results without an
     unmatched entry or any log warning.
  2. `normalize_name` applied its `album_metadata_words` set to the artist string as
     well as the album string, corrupting proper nouns like "New Edition" -> "new"
     and reducing artists named "Special", "Bonus", or "EP" to an empty string.
     Two artists with all-metadata-word names could collide on the same dict key.
  3. `normalize_track_name` used a 13-character hardcoded list while `normalize_name`
     used `str.maketrans(string.punctuation, ...)` covering all 32 ASCII punctuation
     characters. Characters like `&` were inconsistently handled.
  4. `fetch_top_albums_async` (aggregation, timestamp filtering, min_plays/min_tracks)
     had zero test coverage despite being the core business logic function.
- Plan vs implementation: all four defects addressed as described in
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md`. No scope additions or removals.
- Deviations: none.
- Validation:
  - `pytest -q`: **110 passed** (94 pre-existing + 9 new domain tests + 7 new logic tests).
  - `pre-commit run --all-files`: all hooks passed (black reformatted test_domain.py
    on first pass; clean on second).
  - Owner live test: Japanese-title 2025 album (betcover!!) now appears in results
    for listening year 2025 with "Same as release year" filter. Previously absent with
    no unmatched entry. Second validation: same artist's 2021 album (10 unique tracks,
    68 plays) also appeared correctly.
  - "New Edition" self-titled album test: artist key now "new edition" (not "new");
    album deduplication with "(Deluxe Edition)" suffix confirmed still working.
- Forward guidance: no schema, API contract, or route changes. No migration needed.
  The new `test_lastfm_logic.py` file should be extended if `fetch_top_albums_async`
  logic changes (e.g., top-songs feature). Pre-Batch-10 housekeeping is ongoing;
  Batch 10 scope remains TBD by owner.

### 2026-02-20 - fix(tooling): remove transient rotated field from SESSION_CONTEXT status block
- Scope: `scripts/doc_state_sync.py`, `AGENTS.md`.
- Problem: `_build_status_block` wrote `rotated=N` into the managed SESSION_CONTEXT
  block based on the current run's rotation count. The subsequent `--check` always
  recomputed `rotated=0` from the now-clean playbook, causing permanent drift after
  any `--fix --keep-non-current N` run. The workaround required a two-pass sequence.
- Fix: Removed the `Rotated to archive in latest sync run` line from `_build_status_block`.
  The count is still reported on stdout; it is no longer written to a file that `--check`
  re-derives. `--fix --keep-non-current 0` is now a single idempotent command.
- Updated `AGENTS.md` to document the one-pass rotation pattern for agent handoff.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: tooling is stable. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - docs: rotate 4 stale non-current Section 10 entries to archive
- Scope: `PLAYBOOK.md`, `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, `.claude/SESSION_CONTEXT.md`.
- Problem: Four pre-Batch-9 entries (2026-02-19 x2, 2026-02-14 x2) had accumulated
  below `CURRENT-BATCH-END` as `kept_non_current=4` with `rotated=0`, creating
  visible bloat in Section 10.
- Fix: Ran `python scripts/doc_state_sync.py --fix --keep-non-current 0` to flush
  all non-current entries to the archive. Section 10 now contains only active-batch
  entries.
- Deviations: none (purely mechanical doc maintenance).
- Validation:
  - `python scripts/doc_state_sync.py --check`: passed.
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: run `--fix --keep-non-current 0` at each batch boundary to keep
  Section 10 clean.

### 2026-02-20 - WP-7: frontend safety — showToast DOM construction + non-200 fetch guard
- Scope: `static/js/results.js`.
- Problem 1: `showToast` built its HTML via a template-literal string injected with
  `insertAdjacentHTML`. The `message` argument was interpolated without escaping,
  creating an HTML injection pathway if any caller passed server-sourced content.
- Problem 2: `fetchUnmatchedAlbums` piped `fetch()` directly to `.json()` without
  checking `response.ok`. A non-200 response (404, 500, etc.) would be silently
  treated as valid data, surfacing as "No unmatched albums found" instead of an
  error.
- Fix:
  - Rewrote `showToast` to build the toast element tree with `document.createElement`
    / `textContent` / `setAttribute`; eliminated `insertAdjacentHTML` and the unused
    `toastId`. Message content is now set via `.textContent` (XSS-safe).
  - Added `response.ok` guard before `response.json()` in `fetchUnmatchedAlbums`;
    throws `Error("Server error: <status>")` on non-2xx, which the existing `.catch`
    handler surfaces to the user.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: WP-7 complete. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - P1 refactor: extract VALID_FORM_DATA and csrf_app_client fixture
- Scope: `tests/helpers.py`, `tests/conftest.py`, `tests/test_routes.py`.
- Problem: `VALID_FORM_DATA` (the flounder14/2025 form dict for `/results_loading`
  tests) was copy-pasted verbatim 7 times across `test_routes.py`. The 5-line
  CSRF-enabled app + test-client setup was repeated in every CSRF test function.
- Fix:
  - Added `VALID_FORM_DATA` constant to `tests/helpers.py`.
  - Added `csrf_app_client` pytest fixture to `tests/conftest.py`; it creates a
    CSRF-enabled app client (WTF_CSRF_ENABLED not disabled) for CSRF enforcement
    tests.
  - Updated `tests/test_routes.py`: removed `from app import create_app` (now
    unused); imported `VALID_FORM_DATA` from `tests.helpers`; replaced all 7
    inline form dicts with `VALID_FORM_DATA` (or `{**VALID_FORM_DATA, "year": "X"}`
    for year-override cases); replaced all 6 CSRF test inline app setups with the
    `csrf_app_client` fixture parameter.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; pure refactor, no behaviour
    change).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - P1 perf: remove O(n) cache-size scan from cleanup_expired_cache
- Scope: `scrobblescope/utils.py`.
- Problem: `cache_size_mb = sum(len(str(v)) for v in REQUEST_CACHE.values()) / ...`
  ran inside `_cache_lock` on every cleanup call, even when debug logging was
  disabled. This O(n) string-serialization of all cached values held the lock
  unnecessarily and added CPU overhead proportional to cache size.
- Fix: removed the `cache_size_mb` line and simplified the debug log to
  `f"Cache status: {cache_count} entries"`. Count-only logging is sufficient
  for operational visibility; size estimation is not a runtime requirement.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; no test needed for log format).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next P1 item is test boilerplate extraction in
  `test_routes.py` (VALID_FORM_DATA + csrf_app_client fixture).

### 2026-02-20 - P0 fix: delete orphan JOBS entry on thread-start failure
- Scope: `scrobblescope/repositories.py`, `scrobblescope/routes.py`,
  `tests/test_repositories.py`, `tests/test_routes.py`.
- Problem: `create_job()` was called before `start_job_thread()`; on thread-start
  failure the semaphore slot was correctly released by `worker.py`, but the
  `JOBS[job_id]` entry persisted as an orphan until the 2-hour TTL cleanup.
- Fix:
  - Added `delete_job(job_id)` to `repositories.py`:
    `with jobs_lock: JOBS.pop(job_id, None)`.
  - Imported `delete_job` in `routes.py`; called it in the `except` block after
    thread-start failure, before returning the error page.
  - Added 2 tests to `test_repositories.py`:
    `test_delete_job_removes_existing_job`,
    `test_delete_job_on_missing_job_is_noop`.
  - Strengthened existing `test_results_loading_thread_start_failure_renders_error`
    to assert `mock_delete_job.assert_called_once()`.
- Validation:
  - `pytest -q`: **94 passed** (92 pre-existing + 2 new).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: The known orphan-job open risk (SESSION_CONTEXT.md Section 2)
  is now closed. Remaining P1 items: cache_size_mb in `cleanup_expired_cache`,
  and test boilerplate extraction in `test_routes.py`. Next required work package
  is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - doc_state_sync maintenance (remove volatile Last sync commit field)
- Scope: `scripts/doc_state_sync.py`, `.claude/SESSION_CONTEXT.md`.
- Issue: `doc-state-sync-check` pre-commit hook was failing on PR merge to main.
  Root cause: `_build_status_block()` called `git rev-parse --short HEAD` to write
  `Last sync commit: <hash>` into SESSION_CONTEXT.md. On `--check`, the command
  returned the NEW merge commit hash, which did not match the stored hash, causing
  drift detection failure on every merge.
- Fix: Removed `_git_head_short()` function, `subprocess` import, and the
  `Last sync commit` line from `_build_status_block`. The `--check` now validates
  only stable content-level fields (batch number, WP numbers, entry count, newest
  heading). Ran `--fix` to drop the stale `Last sync commit` line from
  SESSION_CONTEXT.md.
- Commit: `cdedd65` fix: remove Last sync commit from doc_state_sync status block.
- Forward guidance: The doc-state-sync-check hook will no longer false-positive on
  merge commits. SESSION_CONTEXT DOCSYNC block is validated on content only.

### 2026-02-20 - WP-6 completed (remove artificial orchestration sleeps)
- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Removed all 5 `await asyncio.sleep(0.5)` calls from `_fetch_and_process`. The
    calls were added as a progress-pacing mechanism but served no functional purpose
    and added a fixed 2.5 s latency overhead to every job.
  - All `set_job_progress` calls and their messages are preserved at the same
    progress values (0, 5, 20, 30, 40, 60, 80, 90, 100), so the loading-page
    progress sequence is unchanged from the user's perspective.
  - `asyncio` import retained: `asyncio.Semaphore`, `asyncio.gather`,
    `asyncio.new_event_loop`, and `asyncio.set_event_loop` are still used.
  - Removed two dead `patch("asyncio.sleep", new_callable=AsyncMock)` lines from
    `test_fetch_and_process_cache_hit_does_not_precheck_spotify` and
    `test_fetch_and_process_sets_spotify_error_from_process_albums` in
    `tests/services/test_orchestrator_service.py`. Those patches were no-ops after
    the sleep removals.
- Deviations and why: none. "Gate with debug-only UX flag" option was not needed;
  the plain removal is simpler and all test coverage is already progress-message
  based, not timing based.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (no count change; two dead patches removed,
    no new tests needed).
- Forward guidance: Next work package is WP-7 (frontend safety and resilience
  polish).

### 2026-02-20 - WP-5 completed (enforce registration-year validation server-side)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added a registration-year guard in `results_loading` immediately after the
    `2002..current_year` bounds check. The guard calls `check_user_exists(username)`
    via `run_async_in_thread` (same helper used by `validate_user`). The result is
    already cached from the blur-validation step, so the call is typically free.
  - If `registered_year` is present and `year < registered_year`, the route
    re-renders `index.html` with an explicit error message citing the registration
    year and the earliest valid year.
  - If the check raises (Last.fm unavailable, network error, etc.), a `WARNING`
    is logged and the route proceeds without blocking the user (fail-open policy).
  - If `registered_year` is `None` (not returned by Last.fm), the check is skipped
    and the route proceeds normally.
  - Updated four existing `results_loading` tests that reach the guard to patch
    `scrobblescope.routes.run_async_in_thread` with a neutral result
    (`{"exists": True, "registered_year": None}`) to avoid live network calls.
  - Added four new tests to `tests/test_routes.py`:
    - `test_results_loading_year_below_registration_year_rejected`
    - `test_results_loading_year_at_registration_year_allowed`
    - `test_results_loading_registration_check_unavailable_proceeds`
    - `test_results_loading_no_registered_year_proceeds`
- Deviations and why: none. Fail-open on service unavailability was the intended
  design from the WP-5 spec (client-side validation already covered the common
  case; server-side guard adds defense-in-depth without blocking on transient errors).
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (88 pre-existing + 4 new).
- Forward guidance: Next work package is WP-6 (remove or gate artificial
  orchestration sleeps).

### 2026-02-20 - WP-4 completed (harden app secret and startup safety)
- Scope: `app.py`, `tests/conftest.py`, `tests/test_app_factory.py` (new), `.env.example`, `README.md`.
- Plan vs implementation:
  - Added `_KNOWN_WEAK_SECRETS = frozenset({"dev", "changeme_in_production", ""})` and `_MIN_SECRET_LENGTH = 16` constants in `app.py`.
  - Added `_validate_secret_key(secret_key: str, is_dev_mode: bool) -> None` in `app.py`. Logic: if key is falsy, in weak set, or shorter than 16 chars -> "weak". In production (`debug_mode=False`): raises `RuntimeError("Refusing to start: ...")`. In dev mode (`DEBUG_MODE=1`): logs `WARNING "SECRET_KEY is missing or insecure. ..."`.
  - Updated `create_app()` to read `_raw_secret = os.getenv("SECRET_KEY", "")`, call `_validate_secret_key(_raw_secret, debug_mode)`, then set `application.secret_key = _raw_secret or "dev"`. "dev" is the dev-mode fallback; in production, `_validate_secret_key` raises before it can be used.
  - `tests/conftest.py` updated: added `import os` + `os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")` before `from app import create_app`. This seeds the guard before `app.py`'s module-level `create_app()` call (which runs at import time).
  - New `tests/test_app_factory.py` with 7 tests: production-fail on missing/dev/changeme/too-short keys; dev-mode warning; strong-key success in both modes.
  - `.env.example` `SECRET_KEY` comment updated to say "REQUIRED in production. Startup fails if missing or set to placeholder."
  - `README.md` setup step 4 comment updated from "Recommended" to "Required in production" with note that `DEBUG_MODE=1` suppresses the check for local dev.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black reformatted `app.py` quote style on first run; clean on second).
  - `pytest -q`: **88 passed** (81 pre-existing + 7 new).
- Commit: `eb13a27` feat: refuse startup on weak SECRET_KEY in production.
- Forward guidance: Next work package is WP-5 (enforce registration-year validation server-side).

### 2026-02-20 - WP-1 correctness fix (slot leak on Thread.start failure)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Issue: WP-1 post-audit check found that `acquire_job_slot()` in `results_loading` was not guarded against failure of `Thread.__init__` or `Thread.start()`. If either raises (e.g. `OSError` under OS-level thread exhaustion), the slot is permanently consumed because `background_task`'s `finally` block never runs. This violates WP-1's acceptance criterion "no leaked active slots after worker exceptions."
- Fix:
  - Added `release_job_slot` to imports in `routes.py`.
  - Wrapped `threading.Thread(...)` and `task_thread.start()` in try/except; on exception: `release_job_slot()`, `logging.exception(...)`, return `index.html` with error message.
  - Added `test_results_loading_thread_start_failure_releases_slot`: patches `Thread` to raise `OSError`, asserts slot is released and index re-rendered.
- Validation:
  - `pre-commit run --all-files`: all hooks passed.
  - `pytest -q`: 77 passed.
- Also: added "callers must not mutate" to `get_cached_response` docstring (latent mutable-reference risk; no active bug since no caller mutates the returned object).

### 2026-02-20 - worker.py architectural decision + product roadmap + CSRF coverage expansion

- Scope: Documentation updates only (`.claude/SESSION_CONTEXT.md`, `EXECUTION_PLAYBOOK_2026-02-11.md`). No runtime code changes yet.
- Decisions made:
  - **Product roadmap confirmed:** Two additional background task types are planned -- "top songs" (Last.fm + possibly Spotify, separate background task/results flow) and "listening heatmap" (Last.fm only, last 365 days, lighter task). This means the `results_loading` acquire->Thread->release pattern will be needed by at least 3 routes.
  - **worker.py chosen as home for concurrency lifecycle:** With multiple background task types incoming, keeping the semaphore and thread-start boilerplate in `repositories.py` would require each new route to duplicate the `acquire -> try Thread.start -> except release` block. A new `scrobblescope/worker.py` leaf module (imports `config` only) will own `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread(target, args=())`. `repositories.py` becomes pure job state CRUD. `start_job_thread()` encapsulates the full try/start/except/release pattern for all callers.
  - **Refactor must precede the 3-commit save-state:** WP-1 originally placed the semaphore in `repositories.py`. The worker.py refactor corrects this before committing; the WP-1 commit will reflect the final architecture.
- CSRF test coverage expansion (also completed this session, before context compaction):
  - Initial WP-3 implementation added 2 CSRF tests covering only `/results_loading`.
  - Expanded to 6 total CSRF tests covering all 4 POST routes:
    - `test_csrf_rejects_post_without_token` (-> `/results_loading` 400)
    - `test_csrf_accepts_post_with_valid_token` (-> `/results_loading` 200)
    - `test_csrf_rejects_results_complete_without_token` (-> 400)
    - `test_csrf_rejects_unmatched_view_without_token` (-> 400)
    - `test_csrf_rejects_reset_progress_without_token` (-> 400)
    - `test_csrf_accepts_reset_progress_with_header_token` (-> `/reset_progress` XHR path with `X-CSRFToken` header, 200)
  - Total tests after expansion: **81 passing**.
- Pending implementation (next agent actions in order):
  1. Create `scrobblescope/worker.py` with semaphore, `acquire_job_slot()`, `release_job_slot()`, `start_job_thread()`.
  2. Remove semaphore/slot functions from `scrobblescope/repositories.py`.
  3. Update imports in `routes.py` and `orchestrator.py` to use `worker`.
  4. Update patch targets in `test_routes.py` and `test_orchestrator_service.py` from `scrobblescope.routes.acquire_job_slot` / `scrobblescope.orchestrator.release_job_slot` -> `scrobblescope.worker.*`.
  5. Run `pre-commit run --all-files` and `pytest -q` (must stay at 81 passing).
  6. Make 3 separate commits: WP-1, WP-2, WP-3.
- Validation: N/A (doc-only session-end update).
- Forward guidance:
  - worker.py is a leaf module -- it must NOT import from `repositories`, `routes`, `orchestrator`, or any higher module (would create cycles).
  - `start_job_thread()` should release the slot and raise on `Thread.start()` failure so routes get a clean exception to handle (mirrors the current try/except pattern in `routes.py`).
  - After the 3 commits are made, next work package is WP-4 (harden app secret and startup safety).

### 2026-02-19 - Fly cold-start recovery validation completed (app + Postgres DB)
- Scope: operational validation of deployed services and documentation refresh (`.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`).
- Plan vs implementation:
  - Confirmed both machines were started (`fly status -a scrobblescope`, `fly status -a scrobblescope-db`).
  - Forced cold state by stopping both machines:
    - `fly machine stop 807339f1595248 -a scrobblescope`
    - `fly machine stop 8e7ed9ad205118 -a scrobblescope-db`
  - Verified both reported `State: stopped` via `fly machine status`.
  - Triggered one end-to-end request:
    - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 1 --timeout-seconds 180`
  - Verified smoke run completion and auto-start behavior for both app and DB machines.
  - Rechecked DB health until all checks passed (`pg`, `role`, `vm`).
- Deviations and why:
  - No code changes were required; this was an operational verification step requested by the owner.
- Validation:
  - Smoke output: `elapsed=18.75s`, `db_cache_enabled=True`, `db_cache_lookup_hits=247`, `db_cache_persisted=0`, `spotify_matched=247`, message `Done! Found 57 albums matching your criteria.`
  - Post-run status: app machine `started`, DB machine `started`, DB checks all passing.
- Forward guidance:
  - Keep this cold-start check as a regression smoke pattern after infra/config changes.
  - If cold-start latency grows, tune DB wake-up retry knobs (`DB_CONNECT_MAX_ATTEMPTS`, `DB_CONNECT_BASE_DELAY_SECONDS`) and/or Fly machine warmness settings.

### 2026-02-19 - Context reconciliation completed (docs parity + cache fallback logging classification)
- Scope: `.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`, `scrobblescope/cache.py`, `tests/test_repositories.py`.
- Plan vs implementation:
  - Re-verified playbook/session claims against the active repo for `init_db.py`, thread model, and cache fallback behavior.
  - Refreshed stale status fields (latest commit snapshot, app.py line count, and current runtime notes).
  - Updated `_get_db_connection()` to log explicit fallback categories:
    - `asyncpg-missing`
    - `missing-env-var`
    - `db-down`
  - Extended DB helper tests to assert those log categories are emitted on each path.
- Deviations and why:
  - No keep-alive thread was added to `app.py`; this is intentional because the current architecture uses per-job daemon worker threads from `results_loading` and avoids additional idle background loops.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed** (2 deprecation warnings from aiohttp connector behavior on Python 3.13.3).
- Forward guidance:
  - Keep Section 2 and `.claude/SESSION_CONTEXT.md` synchronized whenever runtime snapshots (line counts, branch/commit status, logging behavior) change.

### 2026-02-14 - Repository hygiene completed (historical docs archive + README refresh)
- Scope: `docs/history/` (new folder), historical markdown moves, `PLAYBOOK.md`, `README.md`.
- Plan vs implementation:
  - Moved historical docs from repo root into `docs/history/`:
    - `AUDIT_2026-01-10.md`
    - `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`
    - `CHANGELOG_2026-01-04.md`
    - `CHANGELOG_2026-02-10.md`
    - `OPTIMIZATION_SUMMARY.md`
    - `PERFORMANCE_TIMING.md`
    - `Refactor_Plan.md`
    - `TEMPLATE_REFACTOR_SUMMARY.md`
  - Updated playbook references to `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`.
  - Refreshed `README.md`:
    - run instructions now show `python app.py` (recommended) and `python run.py` (optional launcher)
    - project structure updated to current modular layout + `docs/history/`
    - roadmap/status text updated to reflect current post-refactor state
- Deviations and why:
  - Keep a shim at `EXECUTION_PLAYBOOK_2026-02-11.md` to preserve a stable handoff entrypoint.
- Forward guidance:
  - Keep new planning/audit/changelog docs in `docs/history/` unless a document is an active operator runbook.
  - Keep playbook and session-context docs at predictable top-level locations for fast bootstrap.

### 2026-02-14 - Cache wake-up hardening completed (DB connect retry/backoff + docs refresh)
- Scope: `scrobblescope/cache.py`, `tests/test_repositories.py`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Added exponential-backoff DB connection retries in `_get_db_connection()` to reduce false cache bypass during Fly Postgres wake-up windows.
  - Added two DB helper tests:
    - retry-then-success path
    - retry-exhaustion path
  - Updated existing connect-failure test to force single-attempt behavior (`DB_CONNECT_MAX_ATTEMPTS=1`) for deterministic assertions.
  - Refreshed handoff docs for the new test count and operational behavior.
- Deviations and why:
  - No orchestration/routing behavior changes were needed; hardening was isolated to cache connection setup and DB helper tests.
- Additions beyond plan:
  - Added env-tunable retry knobs:
    - `DB_CONNECT_MAX_ATTEMPTS` (default `3`)
    - `DB_CONNECT_BASE_DELAY_SECONDS` (default `0.25`)
  - Live Fly verification confirmed:
    - app cache hits persisted after DB stop/start
    - DB app `scrobblescope-db` uses `FLY_SCALE_TO_ZERO=1h`, explaining suspended/stopped state after idle periods.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
  - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`: **PASS** (`db_cache_enabled=True`, `db_cache_lookup_hits=247`).
- Forward guidance:
  - If first-request latency after idle is a concern, either increase retry knobs or adjust/remove DB `FLY_SCALE_TO_ZERO`.
  - Keep periodic smoke checks as operational validation for cache persistence and warm-hit behavior.
  - Resolve DB app staged secrets drift (`fly secrets deploy -a scrobblescope-db`) to avoid config ambiguity.

### 2026-02-14 - Frontend responsiveness polish completed (toggle placement + mobile table scaling)
- Scope: `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`, `static/css/unmatched.css`, `static/css/error.css`, `templates/results.html`.
- Plan vs implementation:
  - Standardized dark-mode toggle to a compact fixed bottom control across all page CSS bundles.
  - Improved `index.html` mobile fit by tightening spacing, typography, and card/logo sizing at mobile breakpoints.
  - Improved `results.html` mobile readability by shrinking table density, making actions stack cleanly, and reducing album-art footprint.
  - Added `results-table` class in template for targeted responsive behavior.
  - Centered decade pills in `index` filter UI.
- Deviations and why:
  - To improve fit on common phones, responsive rules were applied up to `max-width: 767.98px` for index/results rather than only `575.98px`.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - If users still report table crowding on very small devices, next step is card-style row rendering for results instead of a dense 5-column table.
  - Consider extracting shared toggle CSS into one common stylesheet to reduce cross-file duplication.

### 2026-02-14 - Post-Batch-8 hardening completed (low-severity gap closure + test layout split)
- Scope: `tests/test_routes.py`, `tests/conftest.py`, `tests/helpers.py` (new), `tests/services/` (new split files), `EXECUTION_PLAYBOOK_2026-02-11.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Closed previously identified low-severity gaps:
    - Added direct route tests for `/unmatched_view` (missing `job_id`, missing job, success render path).
    - Added explicit tests for app-level 404 and 500 handlers.
  - Reduced test coupling to `conftest.py` internals:
    - Moved shared constants/mock helpers into `tests/helpers.py`.
    - Updated tests to import from `tests.helpers` rather than `conftest`.
  - Split monolithic service test file:
    - Removed `tests/test_services.py`.
    - Added `tests/services/test_lastfm_service.py` (4 tests).
    - Added `tests/services/test_spotify_service.py` (3 tests).
    - Added `tests/services/test_orchestrator_service.py` (10 tests).
- Deviations and why:
  - No runtime code changes were required. This was a test architecture and coverage hardening pass only.
  - Added one extra test category beyond the initial gap list (500 handler integration path) because this was explicitly untested and low effort/high confidence.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **64 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - Subpackage migration should be sequenced **after** the next feature-heavy batch set (Batch 9+) stabilizes, not before. Keep current flat module layout while churn is high; cut to subpackages once contracts settle.
  - Keep route-handler coverage and helper-module pattern as baseline for future test additions.

### 2026-02-13 - Operational config fix (Fly machine autostop)
- Scope: `fly.toml`.
- Issue:
  - Fly log showed autostop with `0 out of 1 machines left running` because `min_machines_running` was set to `0`.
- Change:
  - Updated `[http_service] min_machines_running = 1` to keep one machine warm.
- Notes:
  - This log means capacity scaling, not cache overflow.
  - In-memory caches (`REQUEST_CACHE`, `JOBS`) live in RAM on the app VM and are lost on machine stop/restart.
  - Persistent Spotify metadata cache lives in Fly Postgres (`spotify_cache`) via `DATABASE_URL`.
