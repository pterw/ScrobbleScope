<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0011

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
