# Context halo streamgraph implementation plan

Owner direction: the supplied A-double-prime mockup and
`ScrobbleScope_A_DoublePrime_Context_Halo_Spec.md`, 2026-10-28. The owner
supplied spec remains an untracked file in the primary checkout. The owner approved the T0 plan on 2026-10-28. Partial work started before
that approval; it was paused and is being reviewed against the approved plan.
This plan supersedes the earlier streamgraph follow-up plan. The ten-artist
weekly payload and current main integration stay unchanged.

**Goal:** Show true artist ribbons over a compressed, optional background halo
for the rest of the listener's plays, with a bottom month axis and faithful export.

**Scope:** Existing heatmap JS/CSS and its directly relevant tests and browser
gate, plus product/design documentation. No new dependency, alternate baseline,
extra artist series, unrelated backend change or new chart framework.

## Steps

- [x] Keep artist ordering, baseline and additive stack independent of residual
  counts. Fit the full-year halo envelope in the existing chart domain, using
  one global count scale shared by both visibility states. For each week extend
  each side of the artist stack by 0.125 times its actual residual. Handle zero
  and residual-only weeks, spikes and partial weeks without clipping.
- [x] Draw the neutral filled halo and subtle outer contour behind the artist
  paths. Add an accessible default-on Other listening control that only changes
  halo visibility; it must not rebuild artist paths or alter counts or scale.
  Resolve theme colours into SVG attributes and preserve the selected visibility
  in the self-contained JPEG export.
- [x] Put month labels on the bottom axis at actual calendar-aligned week positions;
  keep heatmap months above. Use circular tooltip markers and tabular
  right-aligned counts, and
  separate the true residual row with a restrained divider. Preserve hover,
  keyboard, touch, ring, guide, focus, reduced motion and responsive placement.
- [x] Apply ten deterministic rank colours, from orange for the most played to
  purple for the least played, with theme adjustments for dark mode.
  Audit neighbouring colours, including zero-width contacts, in both themes;
  report weak contrasts without asserting a universal 3:1 threshold. Leave the
  heatmap colour ramp unchanged.
- [x] Revise existing tests and browser checks for envelope geometry, exposed
  halo-margin pixels, both visibility states, raw totals, fixed artist paths on
  toggle, bottom month positions and export. Remove superseded assertions; retain
  meaningful coverage and report the test-count change. No new test framework.
- [x] Run focused checks, the full suite, existing hooks/docsync and locked browser
  gate. Capture actual light/dark UI in both visibility states, review against
  the supplied mockup, and record the colour audit and results.
- [ ] Land the focused commit and complete the requested PR using the repo template.

The artist baseline is computed without residuals; fitting includes the halo
envelope so the common scale can shrink when necessary to prevent clipping.
Visibility changes never change that scale or the artist path coordinates.

## Execution notes

- 2026-10-28: T0 approved by the owner after an earlier unauthorized start was paused. T1 uses an artist-only baseline and stack, with a shared fit enclosing the compressed halo. Focused spike, residual-only and between-week enclosure checks passed (5 cases). The global fit may shrink to contain the halo; toggling never changes it.
- 2026-10-28: T4 audit in progress. For the stable ten-rank stack order 10, 8, 6, 4, 2, 1, 3, 5, 7, 9, the weakest measured adjacent luminance ratios are 1.31:1 light (ranks 10/8) and 1.06:1 dark (ranks 7/9). Adjacent OKLab differences fall to 0.154 light and 0.094 dark. Any pair can meet when intervening bands pinch out; the closest pairs have OKLab differences 0.052 light and 0.053 dark. These metrics do not establish accessibility; tooltip identity remains available. CVD simulation and final visual assessment remain open.
- 2026-10-28: T2-T3: default-on halo, visibility control, tooltip and calendar axis implemented. Chromium exposed clipped label bounds in the full gate; a small axis allowance and raised baseline corrected it. Focused alignment, keyboard toggle and both-state saved-image checks passed in Chromium and Firefox.
- 2026-10-28: A full-severity Machado-matrix approximation found the closest adjacent simulated pairs at OKLab differences 0.070 light and 0.060 dark under protan simulation, 0.123 light and 0.090 dark under deutan, and 0.146 light and 0.092 dark under tritan. These are numerical indications, not a validated visibility threshold or a substitute for users and contextual visual checks; pinched bands can bring still closer pairs together.
- 2026-10-28: T3 reopened for an independent review finding: a month beginning in the last partial week may place its bottom label beyond the SVG edge. Verify the boundary and correct it if reproduced before closing T3 again.
- 2026-10-28: T4 complete. Inspected the real-data ribbons in both themes and retained ten deterministic candidate-derived colours with dark-theme adjustments. The heatmap ramp is unchanged. Luminance, OKLab and numerical colour-vision approximation results and limitations are recorded above; several weak pairs remain, especially where bands pinch out.
- 2026-10-28: T5 test impact: replaced twelve-rank/burst palette assertions with ten stable identities; removed hidden-contributor validation and panel cases because that payload is no longer consumed, retaining acceptance of legacy extra fields. Existing residual-only interaction and artist count checks remain. Added parametrized halo margin and between-week enclosure cases, and revised the existing gate for accessible toggle, bottom-axis alignment and exposed-margin image pixels. Full suite measured 3113 passed (previous verified head 3116); final gate and end-week check remain pending.
- 2026-10-28: T3 reverified. A final partial week ending 2026-01-01 reproduced the clipped January label. The bottom label now anchors inward near the right edge while its calendar coordinate and gridline remain aligned with the heatmap. The existing alignment check covers this first/last partial-week fixture and passes at both widths in Chromium and Firefox; toggle and export checks also pass.
- 2026-10-28: T5 complete. The focused geometry and integration checks pass, and the existing full browser gate passed 58 checks in 89 runs before the final partial-week correction. The final-week case extends the existing alignment check rather than introducing a new harness. A full final-state gate is running; T6 remains open.
- 2026-10-28: T6 evidence in progress. Four matched Firefox application captures were made from the saved representative payload in sgb-proto/halo-{light,dark}-{on,off}.png in the session scratch directory. Reviewed all four against the supplied reference for hierarchy, halo, palette and bottom-axis structure. The full 3113-test suite passed before the final partial-week correction; focused browser checks passed after it. The final full browser gate, hooks and docsync remain pending.
- 2026-10-28: The final-state frontend gate passed 58 checks in 89 runs across Chromium and Firefox, including the final partial-week case. Repository hooks and final docsync remain pending.
- 2026-10-28: T6 verification: suite 3113 passed in three shards before the final partial-week correction; final locked browser gate passed 58 checks in 89 runs, and focused final checks passed in Chromium and Firefox. Pre-commit all-files and docsync check passed. Captures are halo-light-on.png, halo-light-off.png, halo-dark-on.png and halo-dark-off.png in the session scratch sgb-proto directory. WT003 is the known advisory side-task branch warning.
- 2026-10-28: After live review, the owner requested removal of the 0.25x header caption because it was confusing. This supersedes the original caption requirement; the halo, counts and toggle remain unchanged. A hue-grouped palette is being previewed separately and is not approved for the PR.
- 2026-10-28: Reopened timeline and verification steps for the owner-requested caption removal; focused Chromium and Firefox alignment, toggle and export checks pass. Full validation is running.
- 2026-10-28: Caption removal verified with focused Chromium and Firefox alignment, toggle and export checks and a full suite of 3113 passed. The grouped-hue comparison is local only and awaits owner feedback.
- 2026-10-28: The owner approved the local rank-based palette preview. Promote orange for the most-played featured artist through purple for the least played; re-audit and verify theme repaint, export and tests. This supersedes the earlier Extended Rocket + Indigo assignment.
- 2026-10-28: Rank-palette audit: weakest normal-stack adjacent WCAG luminance ratios are 1.25:1 light (ranks 2/1) and 1.03:1 dark (ranks 10/8); minimum adjacent OKLab differences are 0.065 light and 0.047 dark. Pinched bands can produce lower separations. Full-severity Machado-matrix simulations found minimum adjacent OKLab differences of 0.068/0.057/0.055 light and 0.016/0.030/0.055 dark for protan/deutan/tritan respectively. These are approximate, not a visibility threshold. The owner reviewed and approved the rank-based preview; the tooltip supplies names and counts.
- 2026-10-28: Rank palette audit and both-theme repaint checks passed; the measured weak pairs above remain a known tradeoff of the owner-approved sequence. Focused Chromium and Firefox alignment, toggle and export checks passed. Full suite and repository checks remain in progress.
- 2026-10-28: T5 complete. Extended the existing palette test to verify stable, distinct rank colours and orange-to-purple progression in both themes. The full suite passed 3113 tests; final browser gate and repository checks remain running.
- 2026-10-28: T6 verification: full suite 3113 passed; the complete locked frontend gate passed 58 checks in 89 runs across Chromium and Firefox, including theme, interaction and export. Screenshots of both themes are recorded locally. Final hooks and docsync are being run before the focused commit.
- 2026-10-28: The owner noticed a gap at the chart edge. Weekly paths started at column centres while the heatmap boundary begins half a cell earlier. Extend the first and last ribbon and halo values to the corresponding cell edges without moving weekly scrubber coordinates. The existing browser alignment gate was extended and failed before the fix; final verification is in progress.
- 2026-10-28: The edge correction and existing alignment-gate regression pass in Chromium and Firefox. The full suite passed 3113 tests. The complete browser gate and repository checks remain in progress.
- 2026-10-28: Edge fix verified: full suite 3113 passed, complete frontend gate 58 checks in 89 runs passed, and the new edge regression failed before the fix and passed afterward. Final hooks and docsync are being run before commit.

## Desktop scaling refinement

- [x] Bound the result width by viewport height while keeping the heatmap and
  streamgraph on the same scale; retain the existing header spacing.
- [x] Increase KPI values and group the legend with the context control.
- [x] Verify desktop visibility, responsive alignment and tooltip placement;
  run the repository gates and record the results.

- 2026-10-28: Owner requested responsive scaling so the pause control remains
  visible at 1080p, larger KPIs, and improved legend placement. The result width
  now responds to viewport height; desktop footer spacing is compacted and the
  chart label scales with the charts. Shorter viewports still need verification.
- 2026-10-29: The owner approved the preview and deferred further tweaks.
  Full suite 3113 passed in three shards; the frontend gate passed 58 checks
  in 89 Chromium and Firefox runs. The old fixed-width gate assumptions were
  updated to check a readable cell size and tooltip containment. The pause
  control fits at 1440x900 and 1920x1080 with the seeded result; shorter
  desktop viewports can still scroll as a page.

## Durable responsive layout follow-up (2026-10-29)

The owner reproduced footer scrolling after the first width-cap refinement and
requested the same fix for all three empty destinations, responsive controls,
less card overhang, and copy reflecting the artist streamgraph.

- [x] Fit the chart to the rendered page chrome and rerun sizing when viewport,
  fonts or toolbar wrapping change; retain alignment, tooltip room and export.
- [x] Let the empty destinations share available height with their actual
  footer and mobile theme control in normal document flow.
- [x] Name the combined view Listening and describe daily plays plus the weekly
  desktop artist streamgraph while preserving saved-job routes and identifiers.
- [x] Extend the existing layout checks for browser-height viewports and resizing,
  validate both engines and record measured limits before atomic commits.

Keep the existing palette, fonts and hierarchy. Prefer measured available space
to physical-screen assumptions. Keep controls reachable when unusually short
windows or enlarged text cannot accommodate the full content.

- 2026-10-29: Reproduced the old overflow at 1536x780 (920px page),
  1280x720 (918px page), and 1024x768 (897px page). The result now measures
  actual footer position and searches a bounded shared SVG width. Container
  units scale headings, KPI values and controls. The tooltip reserve is 20rem
  instead of 25rem, removing the empty tail. Both engines fit those viewports
  and 1920x900/1080 and 2560x1300/1440; the 11-row tooltip stays within the
  visible grid without internal scrolling. The existing alignment check now
  covers shrinking and growing windows, control scaling and bottom overhang.
- 2026-10-29: Empty-state content now shares viewport height with the real footer
  and mobile theme control through normal-flow flex layout. Chromium and Firefox
  probes fit the three empty destinations at desktop browser-height viewports
  and 390x844. At 390x300 with enlarged text the page grows naturally.
- 2026-10-29: The navbar and mode tab now read Listening. Entry, result and empty
  copy describe the daily grid and desktop weekly artists; routes and saved-job
  identifiers stay stable. Removed the semantic test helper's dependency on a
  specific eyebrow phrase; no tests were added for wording.
- 2026-10-29: Independent review identified that a fresh result could be fitted
  while its outgoing loader still occupied space. Fitting now waits for the
  loader's final removal, including reduced-motion rendering. Full validation
  is in progress; no new dependencies or chart geometry changes.
- 2026-10-29: A late-padding probe exposed that content-box observation misses
  added chrome spacing. Observe border boxes instead. Fresh and cached results
  now match in both engines, with normal and reduced motion; adding 3rem to the
  header triggers a fit while keeping the pause control visible.
- 2026-10-29: The full gate exposed two stale fixture assumptions. Its scroll
  probe waited indefinitely for a page that now fits; explicit test scroll room
  and a bounded event wait preserve the original tooltip tracking assertion.
  The export comparison used different grid widths; matching the baseline width
  preserves its additive image-height and pixel assertions. Focused checks pass;
  the complete final gate is running.
- 2026-10-29: The final display-size sweep found the new Weekly artists strip
  label wrapping at 900px and 1100px. Shorten the label to Artists; retain the
  weekly streamgraph explanation in its description. The existing wrap check
  stays unchanged. All other checks passed; rerunning the complete final gate.
- 2026-10-29: Final validation passed: 3113 tests total, the complete frontend
  gate 58 checks in 89 Chromium/Firefox runs, and 116 focused gate-unit tests
  after the fixture corrections. Both-engine fresh/cached and late-header probes
  pass with normal and reduced motion. Reviewed the 1920x900 application capture.
  Repository hooks and docsync passed; the final completion record is staged
  for the responsive follow-up commit.

## Listening entry whitespace refinement (2026-10-29)

The owner confirmed the index form when Listening is selected. Preserve the
existing form and stable mode-tab position. Add one unboxed desktop-only
illustration beneath the short form, showing daily cells, artist ribbons and
a neutral context halo. Keep the schematic decorative and free of invented
user statistics, controls, dependencies or looping animation. The later
Listening mode transition section records the owner-authorized switch motion.

- [x] Add the compact example using existing palette owners and theme tokens.
- [x] Inspect desktop themes, short windows and mobile; preserve submission
  priority, tab stability and reachable motion controls.
- [x] Run the relevant checks and repository gates, record evidence, and commit
  this bounded refinement separately.

- 2026-10-29: Independent spatial review supports an unboxed visual example
  rather than another card or repeated explanatory copy. The existing shared
  album-form height remains the reference for mode switching.
- 2026-10-29: Owner requested no visible illustration caption and tapered
  ribbon ends. Removed the caption and marked the entire schematic decorative
  for assistive technology; every ribbon and halo now meet at each tip.
- 2026-10-29: After viewing the tapered variant, the owner preferred the
  original straight ends. Restored those boundaries while keeping the caption
  removed. The existing page entrance remains the only fade; no extra motion.
- 2026-10-29: Final straight-end preview verified in Chromium and Firefox at
  1920x1080, 1280x720, 1024x768 and 390x844 in both themes. Theme paints change,
  mode tabs stay within 1px, and mobile adds no illustration height. Desktop
  examples fit without increasing the album composition's page height. The
  existing text-heavy home layout still scrolls at 1024x768 (939/940px page);
  the example itself remains inside that viewport. Reviewed final Firefox
  light/dark captures in sgb-proto/listening-space-final-{light,dark}.png.
- 2026-10-29: Full suite measured 3113 passed (2954 non-browser in three
  shards plus 159 browser tests). The complete frontend gate passed 58 checks
  in 89 runs. No tests or dependencies were added for this decorative change.
  Independent whole-file review found no material concern. Hooks and final
  docsync are running before the focused commit.
- 2026-10-29: Repository hooks and final docsync passed. The completion
  record is staged with the focused illustration commit; local preview files
  match the reviewed source. The optional detector's degraded-mode limitation
  is recorded in PLAYBOOK. PR #280 remains draft for owner review.

## Listening mode transition (2026-10-29)

The owner requests an upward collapse when changing from Top albums to
Listening, followed by a fade of the illustration. Preserve the form top and
shared desktop height. Use one short CSS-driven card-height transition and
a delayed illustration fade; add no loop or dependency. Reduced motion and
the existing Pause animations choice show the final state immediately.

- [x] Animate the measured card collapse and supporting illustration fade.
- [x] Verify keyboard switching, repeat clicks, interruption, pause and reduced
  motion; extend the existing motion check without a new test family.
- [x] Record verification, update the local preview and commit separately.

- 2026-10-29: Reuse index.js's capture listener and measured placement. Keep
  the illustration at its final position during the collapse so it cannot
  push the desktop composition down. CSS cancellation must leave natural
  card height and visible content, including preference changes mid-motion.
- 2026-10-29: Implemented a 320ms CSS card-height collapse and a 160ms
  illustration fade starting halfway through. The destination panel reserves
  its natural height, so the illustration cannot push the card or page down.
  Natural sizing returns on completion or cancellation. A request counter
  discards older switches queued in the same frame. Reverse switching retains
  the existing placement behavior. The local preview is updated.
- 2026-10-29: Extended the existing entrance-motion check to sample actual
  top-anchored height change and illustration opacity, rapid interruption,
  post-transition content growth, and both prevented and cancelled effects
  for reduced motion and Pause animations. Chromium and Firefox pass, as do
  the existing display-scale checks. Serving the pre-change CSS makes the
  new behavior checks fail; no new test family or dependency was introduced.
  Full validation is running.
- 2026-10-29: A stylesheet-contract test required explicit defaults for the
  measured height properties. Added local auto defaults; the 126 template
  checks and the repeated affected suite shard pass. The final full browser
  gate passed 58 checks in 89 runs. The motion probe clears a saved pause
  state after navigation and restores it afterward, so diagnostic order cannot
  suppress the normal-motion case.
- 2026-10-29: Final verification measured 3113 passed (2954 non-browser in
  three shards plus 159 browser tests). Full frontend gate: 58 checks in 89
  runs. The final motion check also passes in both engines with a saved Pause
  choice, restores that choice, and verifies arrow-key mode selection.
  Independent whole-file review found no material product issue. The optional
  design detector reports the existing untouched style advisories; repository
  hooks and docsync are running before the focused commit.
- 2026-10-29: All repository hooks and final docsync passed. The local
  preview matches the reviewed motion implementation. The completed record
  is staged with this separate motion commit; PR #280 stays draft for review.

## Listening validation and session close-out (2026-10-29)

The owner requested the same blur verification as Top albums, a check of
uncommitted files, and a durable handoff. Listening already calls the shared
validation endpoint on blur and checks custom validity before starting a job.
Verify actual rejected requests and correction recovery instead of copying
working validation code. Keep independent owner tooling out of this PR.

- [x] Extend the existing profile check for missing/private verdicts, actual
  blocked submissions, and a corrected public profile that can submit.
- [x] Verify both engines and backend prechecks; run the required gates.
- [x] Record the uncommitted-file audit under existing F-SWE-8, update the
  ledger, and write the requested OS-temp handoff with suggested skills.

- 2026-10-29: Source inspection confirms Listening's existing blur validator,
  stale-response protection and submission validity guard. The previous
  browser check only observed field validity, so it could stay green if the
  Listening submission guard were removed. Strengthen that existing check.
- 2026-10-29: Both browsers pass rejected-profile blocking and corrected-name
  submission in the feature server and the actual owner preview. The virtual
  removal of Listening's custom-validity guard produces captured rejected
  POSTs and fails the check. Outage recovery and stale-verdict checks also
  pass. No production validation code changed. A one-argument route closure
  binds each verdict without Playwright replacing it with Request.
- 2026-10-29: The uncommitted-file audit reconciles eleven product previews
  with dd69ddd7 and preserves thirteen independent owner files. Fresh source
  evidence is linked under existing F-SWE-8 without adopting the tooling.
  Other dirty worktree status is inventoried, with ownership/content review
  explicitly left for a later cleanup. The requested OS-temp handoff exists.
- 2026-10-29: Close-out verification passed: 3113 tests total (2954
  non-browser in three shards plus 159 browser), frontend gate 58 checks in
  89 runs, and all repository hooks. The backend precheck cases remain in
  the full suite. Whole-file source/document review found no material issue;
  archive rotation was proved mechanically against dd69ddd7. The completed
  record is staged with the focused validation/close-out commit. The OS-temp
  handoff will carry its final pushed SHA and current CI state.
