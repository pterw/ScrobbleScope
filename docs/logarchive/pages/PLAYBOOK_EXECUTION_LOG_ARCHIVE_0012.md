<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0012

### 2026-09-05 - Remediate PR #224 Task 2 review (side-task)

- Scope: restore Task 2's original authored form geometry, harden its browser
  gate, and reconcile live status documents found during owner and bot review.
  Task 3's `3fr 4fr` split and `28rem` base form cap remain untouched.
- Review dispositions: restored the three `0.25rem` gap bases and scaled `9rem`
  mode-tab minimum; added an adversarial wrapped-headline helper test; shared
  the repeated font-ready expression; removed the late-bound browser closure;
  reduced the flagged helper complexity; and repaired the DOCSYNC marker plus
  stale Task 2/two-engine claims. F-B21-39 owns the defect record.
- Declined bot findings: the sixteen Bandit B101 comments target pytest
  assertions, where assertion rewriting is the test framework's contract.
  Graphify's missing-selector and unscaled-headline claims do not match current
  source, and failure when either required browser is unavailable is explicit
  Task 2 acceptance behavior.
- Validation: focused frontend-gate tests passed **24 tests**; `pytest -q` --
  **881 passed**, 5 warnings. The complete gate passed 22 checks in 62 runs
  across Chromium and Firefox. All pre-commit hooks and docsync passed on the
  final document state.
- Forward guidance: Task 2 awaits owner review on PR #224. Task 3 remains the
  next implementation task and owns the final split and form cap.

### 2026-09-05 - Implement layout-aware desktop scaling, Task 2 (side-task)

- Scope: complete Chromium and Firefox gate lifecycle, realistic window
  profiles, and explicit CSS composition dimensions. Task 3's final split and
  base form width are unchanged. Adobe remains the font provider.
- Plan vs implementation: the initial complete gate failed on the old scale
  path in both engines. The first replacement run exposed contracted touch
  inputs and an expanded form taller than the plan's 673px baseline.
  F-B21-38 owns the measured boundary and expanded-state correction.
- Deviations: scale hero gutters with the complete composition and retain
  readable type and coarse-pointer lower bounds below the reference width.
  The entire two-engine gate should take roughly twice its former wall time.
- Validation: the complete two-engine gate passed in isolation -- 22 checks
  in 62 runs across Chromium and Firefox -- after one Chromium pipeline
  timeout and one Firefox socket-in-use failure that appeared only while
  unrelated browser work ran concurrently and never reproduced cleanly.
  Rendered geometry and screenshots were recaptured for both engines at
  1080p, 1440p, the 1200px boundary, mobile, and the 1920x900 expanded fit;
  wrappers compute `transform: none` and `zoom: 1` everywhere. The focused
  runner suite passed 23 tests; full pytest was **880 passed**, 5 warnings.
  All pre-commit hooks and docsync passed. The final gate and suite ran at
  close of this entry.
- Landing: committed as `ac6b1b1`, pushed to `origin/wip/batch-21`, and
  opened as PR #224 with owner authorization on 2026-09-05. All nine Task 2
  plan steps are checked off in the canonical plan.
- Forward guidance: Task 2 awaits PR review and merge. Task 3 is next, as
  its own commit and review cycle. Do not start WP-5 until Task 3 lands.
- After any edit here, run `python scripts/doc_state_sync.py --fix`.

### 2026-09-04 - Preserve owner-plan provenance and late review decisions (side-task)

- Scope: track the original September 1 owner-review proposal with an explicit
  historical/non-executable banner, and identify its superseding execution
  plan. Ignore generated `graphify-out/` while preserving and querying it
  locally. Planning documents remain tracked rather than ignored.
- Review corrections: pin the remaining captured snapshot kit URL; express the
  planned natural-height guard in rem and require enlarged-root browser checks;
  record Adobe Fonts ownership and the loading screenshot corrections.
  F-B21-34 and F-B21-35 record plan/config fixes; F-B21-36 remains implementation
  work. F-B21-37 records PR #223's completed documentation repair.
- Plan vs implementation: no production scaling or loading behavior changed.
  The old proposal stays intact below its supersession notice, including old
  instructions. The active plan owns execution and the owner rulings win.
- Deviations: defer the unfinished Task 2 test-first changes from this commit;
  preserve and restore them locally after validation. The owner approved this
  documentation commit; no push is requested. `.impeccable/` and `PRODUCT.md`
  remain untracked and preserved.
- Validation: `pytest -q`: **872 passed**, 5 warnings on the commit candidate
  with the unfinished tests shelved. Run hooks and docsync before commit.
  No production UI changed; PR #223 already passed both browser gates.
- Forward guidance: resume Task 2 of the canonical scaling/remediation plan
  before WP-5. Query the local graph as navigation, then verify current source.
  On 2026-09-04, headed Chrome at DPR 1 measured 2560x1305 content inside
  2560x1392 outer bounds on the 2560x1440 monitor; the second 1920x1200 monitor
  measured 1920x1065 content inside 1920x1152 outer bounds. Other panel profiles
  remain derived rather than physically measured. Both browsers must execute
  the full gate. Late PR #221 threads 3938613706 and 3938613711 have local fixes
  recorded here; reply/resolve only after these fixes are published. PR #223
  is merged; issue #222 stays open for its remaining complexity targets.

### 2026-09-04 - Review three complexity extractions in PR #223 (side-task)

- Scope: split loading progress error/poll/redirect handling, index filter-label
  selection, and optional semaphore/retry timing into focused helpers.
- Plan vs implementation: this is partial issue #222 remediation, not closure
  of its full complexity inventory. Existing behavior and public contracts stay
  unchanged. Added purpose comments to the extracted JavaScript helpers.
- Deviations: the initial PR body described only loading.js and incorrectly
  closed the broader issue. Correct the title/body before merge. The original
  Copilot commits carry prohibited co-author trailers; use a clean squash
  message at integration rather than rewrite the author's branch.
- Validation: `pytest -q`: **872 passed**, 5 warnings. The complete Firefox
  gate passed 22 checks in 31 runs locally; Chromium passed the same 22 checks
  in 31 runs in PR CI. Final pre-commit and docsync checks run before commit.
- Forward guidance: resume the owner-review scaling plan before WP-5. These
  extractions do not implement its loading-count or layout corrections.

### 2026-09-04 - Clear PR #221 plan-review follow-ups (side-task)

- Scope: corrected the execution plan and repository-authored Markdown before
  the owner-authorized PR merge. Production scaling remains Task 2.
- Review dispositions: reaffirmed accurate visible phase counts after checking
  the September 1 owner-remediation plan and obtaining the owner's ruling;
  required
  nested phase-copy isolation through both repository readers, and normalized
  the batch definition, reconciliation and Graphify report to ASCII. Filed
  F-B21-31 and F-B21-32 with the evidence and implementation boundary. The
  polling audit reproduced stale heatmap responses and found received-page
  counts sourced from attempts; F-B21-33 remains open for Task 4. Sharing a
  renderer must preserve the different album and heatmap pipeline state.
- Plan vs implementation: verified completed snapshot work is marked without
  rerunning historical failing steps. The touch-declaration deadlock stays
  deferred until its minimum changes. The header advisory confused 1440p with
  a 1440px width: 2.96875vw reaches 76px at 2560px, as intended.
- Deviations: no production scope added. The broad README refresh stays in
  WP-8; Firefox setup documentation will change with Task 2. Preserve and query
  the local Graphify data; no ignore rule, graph rebuild or plugin update is
  part of this review fix. Older fixed-form and hero-only rulings remain dated
  history and are superseded by the final complete-composition direction.
- Validation: `pytest -q` -- **872 passed**, 5 warnings. The frontend gate
  reports 22 checks passed in 31 runs. All 12 pre-commit hooks and docsync
  pass; the snapshot remains byte-identical and WT000 confirms alignment.
- Forward guidance: refresh the PR body, post one batched review disposition,
  and resolve only addressed threads. The owner authorized merging once review
  is clear, then continuing Task 2 in this same worktree before WP-5.

### 2026-09-04 - Reconcile PR #221 review with final scale direction (side-task)

- Scope: documentation and one provenance test. Audited all nine unresolved
  inline threads on PR #221 plus Graphify's earlier review-body advisory against
  the current files, the stashed scale checkpoints, and the owner's final
  direction. No production CSS, JavaScript, template or browser-gate behavior
  changed in this review-fix commit.
- Owner direction: the earlier hero-only zoom and fixed 600px form rulings are
  superseded. Hero, wordmark, form, type, controls and spacing grow together
  through explicit layout values from 1080p through the 4K ceiling. CSS zoom,
  browser zoom and visual scale transforms are forbidden; the header remains an
  independently sized shell. The plan now treats its untracked predecessor as
  outcome evidence, not executable mechanism.
- Review remediation: Task 2 now retires zoom-property assertions in favor of
  rendered rectangles and ratios, uses realistic window content boxes, runs the
  complete gate in Chromium and Firefox locally and in CI, migrates the root
  `.docsync.toml` declarations when the JavaScript constants disappear, and
  keeps the generic docsync implementation repository-independent. Task 3 uses
  the 3:4 split and a proportional 28rem base form cap, keeps controls in that
  same scale relationship, implements the already-ruled header clamps, and
  mutation-checks that zoom and transform scaling stay absent.
- Snapshot and command guards: `tests/test_design_snapshot.py` now hashes one
  deterministic manifest of all 61 imported design paths and bytes while
  excluding repository-owned `RECONCILIATION.md`; edits, additions, deletions
  and renames all invalidate it. Repository-relative POSIX path sorting keeps
  the aggregate order identical on Windows and Linux. Its pytest assertion
  carries an explicit B101 suppression. The historical restore instruction now
  uses `git restore` instead of a PowerShell pipeline that could concatenate
  lines.
- Test-count check: the observed 871/872 discrepancy crossed two different
  commits while another process advanced the branch. The current tree and all
  live records agree on 872. Docsync validates the latest recorded `pytest -q`
  result but deliberately does not execute pytest, so no same-revision docsync
  defect was reproduced. A future generic control-plane hardening would guard
  that HEAD did not change across a validation run, not encode a
  ScrobbleScope-specific test-count rule.
- Stash audit: `checkpoint/pr220-deferred-loading-progress-build` and
  `checkpoint/pr220-scale-isolated-gates` confirm the complete-composition
  relationship and a wider form, but both use the rejected CSS-zoom mechanism
  and the old 1080px height denominator. Neither stash was applied or changed.
- Validation: the focused snapshot test passes, and a temporary 62nd imported
  file made it fail before removal and a clean rerun. `pytest -q` reports
  **872 passed**, 5 warnings. The frontend gate reports 22 checks passed in 31
  runs across desktop, mobile and wide touch. All 12 pre-commit hooks,
  `doc_state_sync.py --check`, `git diff --check`, and the worktree guard pass;
  WT010 is the expected dirty-tree warning and WT000 confirms branch alignment.

### 2026-09-04 - Graphify knowledge-graph build and audit published (side-task)

- Scope: built a graphify knowledge graph over the worktree corpus (301
  files, ~375k words) and published the report at
  `docs/history/reports/GRAPHIFY_AUDIT_2026-09-04.md`. The graph reflects
  `wip/batch-21` at `ee285ac`, not `origin/main` -- a provenance block in
  the report head says so, so an agent bootstrapping from `origin/main`
  knows the docs-layer nodes describe unmerged work. The graph itself
  stays untracked in `graphify-out/`; the report is the tracked record.
  Built so agents can understand the repository faster at bootstrap.
- Build shape: 3,103 nodes, 5,896 edges, 248 communities (2,387 AST from
  code + 739 semantic from docs). Semantic extraction ran as 18 subagent
  chunks after two full-size chunks repeatedly failed on provider stream
  errors; smaller chunks succeeded. Top 15 communities were named from
  their top node labels; the long tail keeps default names.
- Verification notes are in the report head. Two of its own suggestions
  were traced and disproved as extraction artifacts: the `_reach_state()`
  "bridge" rests on one INFERRED exception-as-callee edge, and the `patch`
  node's 133 INFERRED edges are `unittest.mock.patch` test wiring. The
  verified-genuine findings are the `create_app()` hub bridging factory,
  gate, config and shell-test communities, and the Batch 11-13 log edges
  into the `orchestrator.py` and `utils.py` functions those batches
  shipped.
- Corpus exclusion recorded in the report:
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` was excluded from
  semantic extraction as too large to parse; its durable content is
  represented by the batch definitions and per-batch logs, which were
  extracted.
- Plan vs implementation: no production code changed. This is a read-only
  research artifact plus its publication commit. The pipeline integration
  question (docsync declarations pinning graph facts, automated rebuilds)
  is deferred to the future extraction batch described in `AGENT_NOTES.md`;
  nothing was wired into any gate.
- Deviations: none.
- Validation: `pytest -q` -- **872 passed**. All 12 pre-commit hooks pass.
  Worktree guard exits 0. `doc_state_sync.py --check` exits 0.
- Forward guidance: future agents can query the graph with
  `graphify query "<question>"` from the worktree; `graphify --update`
  re-extracts only changed files. Read the report head before trusting any
  "surprising connection" it suggests -- two of five were artifacts.

### 2026-09-02 - Remediate PR #221 review round one (side-task)

- Scope: documentation and tests. Six bot findings on PR #221, from Codex, qlty
  and Graphify. All six were verified against the code before any edit; none was
  a hallucinated line range.
- Gate assertions: the remediation plan told an executor to add gate checks
  without retiring the ones they contradict, so its own Task 2 Step 5 could not
  pass. `check_large_display_scale_parity` still required the form composition
  to carry `zoom`, treated the input and mode-tab heights as scalable, and
  derived the form width from the superseded `23.75rem` cap times a scale the
  form no longer carries. Task 2 Step 2 now names all four assertions to retire
  and why.
- Sweep beyond the reported instance: the same defect class appeared twice more
  in the plan and neither was reported. Task 3 Step 1 added a `3fr 4fr` split
  check alongside the existing 5:3 assertion instead of retuning it, and did so
  through `grid_left` and `grid_right` keys that `measure_wide_layout` does not
  return. Both expected-FAIL messages also named stale figures. Fixed together,
  per `AGENTS.md` Anti-Pattern 11.
- Step numbering was left alone deliberately. This plan cites its own
  "Task 2 Step 6", so the retirement instructions extend Step 2 in place rather
  than inserting a step and breaking that citation.
- Plan vs implementation: no implementation. No production code, CSS or gate
  code changed in this commit; the plan describes the gate edits for Task 2.
- Deviations: none.
- Validation: **872 passed**. All 12 pre-commit hooks pass. Worktree guard
  exits 0. `doc_state_sync.py --check` exits 0.
- Forward guidance: three findings from the same round remain -- the `clamp()`
  floor, the acceptance contradiction, and the snapshot digest set. They are
  separate commits because each is independently revertable.

### 2026-09-02 - Record the header, H1 and browser-baseline rulings (side-task)

- Scope: documentation only. Three owner rulings and one measured defect class,
  added to the remediation plan before its Task 2 begins.
- Header: it scales with the viewport, and the baseline is the 1440p rendering
  rather than the 1080p one, so the header becomes smaller at 1080p than it is
  today. Floor is 44px on the smaller side, because a strict viewport fraction
  takes the 48px link to 36px at 1080p, under the minimum in `AGENTS.md` "UI
  and Accessibility Rules" item 2 and reversing the 48px desktop target from
  F-B21-29. The header keeps its own sizing and stays outside the composition
  scale.
- H1: it must not wrap at any desktop width, not only when maximised. The cause
  is that the composition scale is floored at its base and can only grow, so a
  narrowing hero column starves the headline. The remedy is a lower bound on
  the composition scale, not a fluid headline, because the annotation requires
  the logo-to-H1 ratio to stay fixed and scaling the composition preserves it.
- Browser baseline: a default fresh Chrome install, maximised, no extensions,
  no bookmarks bar, 100% zoom. Measure it with `channel="chrome"` and a fresh
  temporary profile; do not measure the owner's daily profile and do not infer
  a chrome height from whether a bookmarks bar is showing.
- Defect class worth naming: three declarations in this page read as responsive
  and are pinned where it matters. The composition's `min()` discards the width
  term, the header's `7.25vw` saturates near 1600px, and the H1's `6vw`
  saturates near 700px. Compute where a `clamp()` or `min()` saturates before
  trusting it.
- Form card width: the `28rem` cap is superseded. The owner widened the card in
  Chrome DevTools, source untouched, and ruled the wider card the better
  default. The card widens past `28rem` and then locks, still never zoomed; the
  controls do not inherit that width. The card caps at `37.5rem` (600px),
  the value the owner reached in DevTools. It locks at 1920px, so 1080p and
  1440p both render a 600px card -- the same visual size on both. Whether to pair fields at
  the wider card is open and needs an owner ruling.
- Correction: `docs/design/RECONCILIATION.md` still carried the disproved
  Firefox premise and cited the superseded plan. The earlier commit corrected
  `FINDINGS.md` and `BATCH21_DEFINITION.md` and missed this third copy --
  Anti-Pattern 11 in the same session that quoted it. Swept and fixed here.
- Plan vs implementation: no implementation. No production code, CSS or gate
  code changed.
- Deviations: none.
- Validation: **872 passed**. All 12 pre-commit hooks pass. Worktree guard
  exits 0. `doc_state_sync.py --check` exits 0.
- Forward guidance: Task 2 is next and must take two measurements before it
  writes any number -- the fresh-Chrome window geometry, and the largest
  composition scale at which the H1 holds one line at the 1200px breakpoint.

### 2026-09-01 - Diagnose the large-display scale defect and supersede its plan (side-task)

- Scope: documentation only. No production code, CSS or gate code changed.
  Measured the large-display scale defect, replaced the remediation plan that
  rested on a disproved premise, and corrected every live document that
  repeated it.
- Cause found: `syncWideDesktopScale` divides window height by the 1080px
  design viewport instead of by the composition's own 673px height. The
  `min()` is unconditional, so browser chrome -- which costs 130-330px of
  height and almost no width -- makes the height term win on every real
  window and the width term is discarded.
- Why no gate caught it: `check_large_display_scale_parity` measures
  1920x1080, 2560x1440 and 3840x2160. `page.set_viewport_size` sets the
  content box to exactly those numbers, so the gate tests a geometry no
  maximised browser reports. The gate saw 33% growth; the owner saw 2.9%.
- Premise disproved: the superseded plan gated acceptance on Firefox.
  Chromium and Firefox measured the same composition width to within 0.1px at
  four window sizes, so the defect is engine-independent. Playwright's Firefox
  build is installed and launches at version 153.0, so dual-engine checks are
  available without a download; the owner adopted them for the scale check.
- Plan vs implementation: no implementation. The plan at
  `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`
  supersedes `docs/superpowers/plans/2026-09-01-owner-review-remediation.md`,
  whose Task 1 rested on four claims measurement disproved. Its Task 1 is
  already complete: it landed as `eeaa1a8` on this branch, unpushed, from a
  concurrent session. Work starts at Task 2.
- Deviations: none. The branch was moved from `wip/batch-21-owner-review` to
  `wip/batch-21` on the owner's ruling, because PLAYBOOK Section 3 names the
  latter and the guard raised WT003. Local `wip/batch-21` was reset to
  `origin/main`; `aadf2b7` is unchanged on `origin/wip/batch-21` and its
  content is already in `origin/main`. A later push needs
  `--force-with-lease` and a separate owner ruling.
- Validation: **872 passed**. All 12 pre-commit hooks pass. Worktree guard exits 0.
  `doc_state_sync.py --check` exits 0.
- Forward guidance: start at Task 2, which fixes the gate geometry and the
  scale together because the gate change alone turns the suite red. Two owner
  rulings are recorded in the plan and must not be re-derived: the hero scales
  proportionally while the form widens and then locks, never zoomed; and
  ultrawide is out of scope. The nested-card slider and any widening past
  `28rem` stay behind a fresh owner review.

### 2026-09-01 - Restore design snapshot provenance and re-home overrides (side-task)

- Scope: restore `docs/design/README.md` to its verbatim import at `b4e23bf` and
  move the seven decisions its edits carried into `docs/design/RECONCILIATION.md`
  as override rows, so the snapshot can disagree with the implementation again.
- Decisions re-homed: header pills are production navigation, loading progress is
  a hairline with pinwheel status, heatmap H1 and mode card copy are owner
  changes, release filter label is WP-4 scoping, runs expire after two idle
  hours, form help affordance is no `?` control.
- Defect being prevented: three `.docsync.toml` declarations (44px touch target,
  Adobe Fonts kit, heatmap window) had snapshot sites with no `expect` value,
  allowing docsync to satisfy drift by editing the import instead of the code.
  Added explicit `expect` values to close that deadlock. Sites without capturing
  groups remain unmatched and satisfied by agreement; sites with groups now
  demand the expected value.
- Validation: snapshot test created and passes at the restored digest. `pytest
  -q` -- **871 passed**. `pre-commit run --all-files` -- all 12 hooks pass.
  `doc_state_sync.py --check` -- exit 0. No drift in binary files or structure.
- Deviations: none.

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
