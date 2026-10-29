# Streamgraph live-review corrections implementation plan

> Superseded on 2026-10-28 by the owner's context-halo direction. The completed
> checkpoint history below remains historical; current work follows the
> [context-halo plan](2026-10-28-streamgraph-context-halo.md).

> **For agentic workers:** Use subagent-driven-development. Parallelize independent
> code and browser-check files, review the integrated change and land atomically.
> Tick steps only after evidence is available.

**Goal:** Preserve original page spacing and show named artists clearly, keeping the
residual count in the scrubber and restoring the original rocket palette. Latest
owner review further reduces the final chart to ten artists without contributor rows.
**Architecture:** Existing SVG and panel, unchanged payload.
Design: [owner-directed live review](../specs/2026-10-28-streamgraph-live-feedback-design.md).
Original Tasks 1-4: [completed plan](2026-10-28-streamgraph-bursts.md).
**Tech Stack:** Existing Python/pytest, hand-built SVG and Playwright gate. No dependency.

## Global constraints

AGENTS.md, global-rules.md and original SDD constraints apply. The owner requires
original page spacing and no internal chart or tooltip scrolling; normal page flow
may exceed a short viewport. Guards are advisory. Tests/hooks/docsync remain required.
Use qualified primary Python and the browser lock. Stage named paths only, no
attribution, no push before prototype sign-off. Current code base: 6ac9147.

## Task 5: Restore spacing and quiet the residual row -- complete

- [x] Restore original stage/header/frame/KPI gaps without viewport compression.
- [x] Keep 25rem grid reservation and desktop focus clearance, no internal scroll.
- [x] Keep selected residual row at normal weight; emphasize selected artists only.
- [x] Verify eight Chromium/Firefox cases at 860/1024/1280/1920 widths, full suite
  3117 passed, hooks/docsync and independent review. Commit: 6ac9147.

## Tasks 6 and 7: Sandwich and categorical burst colours -- superseded, unlanded

The owner replaced these proposals with Task 8 during live review. Private patches
and evidence remain in the ignored SDD workspace for recovery, not as final proof.
Neither proposal landed. Do not execute or mark them complete.

## Task 8: Draw artists only and retain the numeric residual

**Touches:** static/js/heatmap.js; static/css/heatmap.css (unused residual tokens only);
tests/frontend/test_heatmap_pure_functions.py;
scripts/dev/_frontend_gate_stream.py; README.md; DESIGN.md; plan and landing log.
**Consumes:** Existing weeks, artists, other, hiddenArtists, streamOrder and helpers.
**Produces:** Artist-only proportional SVG, unchanged numeric totals and hidden details.

- [x] Extend existing layerAtY cases for named-only slot mapping, order, empty bands
  and shared boundaries. Demonstrate red against the residual-first renderer.
- [x] Build baseline/fit/stack from ordered artist counts only. Remove residual path
  rendering/recolouring and map hit slots through order[k]. Preserve one count scale;
  no caps, damping or independent scales.
- [x] Keep numeric residual row and keyboard position, with blank swatch spacer and
  all artist paths undimmed on its selection. Preserve full week totals, hidden-three
  rows, scrubbing through residual-only weeks and a blank interactive chart for
  globally residual-only data; no chart for all-zero data.
- [x] Retain original rocket arrays/permutation. Replace the private live preview's
  unlanded navy treatment when the reviewed source is copied there. Remove the
  unused residual fill/swatch tokens after checking their consumers.
- [x] Extend existing browser alignment, paint, panel, keyboard, absence and JPEG
  pixel checks for the new contract. Preserve focus, clipping and internal-scroll
  checks. Cover residual-only/all-zero cases without a duplicate check family.
- [x] Run focused red/green and whole frontend test file, independent source review,
  full suite shards, hooks/docsync and locked integrated browser gate.
- [x] Update README/DESIGN to distinguish named-only silhouette from full week totals.
  Tick evidence and land atomically:
  fix(heatmap): Keep the residual count outside the artist stream

Task 8 is a checkpoint of the twelve-artist version. Its retained contributor rows
and height reservation are superseded by the owner's later Tasks 9-10 below.

## Task 9: Return aggregation to the top ten

**Touches:** scrobblescope/plays.py; scrobblescope/jobs.py; tests/test_plays.py;
tests/test_jobs.py; README.md; docs/architecture/heatmap-sequence.md; plan/log.
**Consumes:** Existing Play records and 365-day window; top_n default 10.
**Produces:** Original top-ten weekly payload and residual counts, without bursts
or the now-unwanted contributor metadata. Existing tie and empty-key rules stay.

- [x] Verify the four source/test paths have no upstream changes since the original
  branch base. Reverse only this branch's burst/hidden additions, preserving any
  unrelated edits. Do not reset, restore or rewrite history.
- [x] Restore existing top-ten behaviour tests and job-view isolation assertions.
  Remove tests solely for superseded bursts/contributor output; keep adversarial
  top_n, ties, dates, empty names and nested-copy coverage. No new duplicate family.
- [x] Run focused plays/jobs/heatmap tests and independent source review. Update
  README and sequence docs to top ten. Run full suite/hooks/docsync and land:
  refactor(heatmap): Return weekly artists to the top ten

## Task 10: Simplify the panel and reduce the chart box

**Touches:** static/js/heatmap.js; static/css/heatmap.css;
tests/frontend/test_heatmap_pure_functions.py; scripts/dev/_frontend_gate_stream.py;
scripts/dev/frontend_gate.py; README.md; DESIGN.md; original spec/plan; plan/log.
**Consumes:** Task 9's top-ten payload; artist-only geometry and numeric residual.
**Produces:** Ten ribbons, one numeric residual row, no contributor block/divider,
and a smaller desktop chart without vertical scrolling in the validation matrix.

- [ ] Remove hidden-field validation/model/rendering and contributor/divider CSS.
  Trim obsolete pure cases; keep payload validity, selected week counts and total
  coverage. Keep numeric residual weight400, blank spacer and keyboard undimming.
- [ ] Limit named artists to ten while retaining the accepted rocket colours for
  those ranks. Do not reintroduce cool burst colours or residual geometry.
- [ ] Measure page, grid, SVG and tallest panel at 860x720, 1024x768, 1280x720,
  1920x1080, 2560x1440 and 3840x2160. Remove the 25rem grid reservation. Reduce
  existing stream height constants if intrinsic SVG growth still overflows.
  Preserve original header/stage/frame gaps, week alignment, common linear scale,
  focus clearance and readable labels. Do not hide page content to suppress scroll.
- [ ] Remove the obsolete hidden-row browser check and registration. Move its
  residual-only pointer coverage into the existing hover check. Seed ten artists
  and retain numerical residual, empty/only-residual, theme, JPEG and keyboard proof.
  Extend existing layout checks to catch desktop page as well as internal scrolling.
- [ ] Run focused tests, measured layout matrix, full locked browser gate, suite,
  hooks/docsync and independent review. Update current docs and real-data preview
  (fold removed burst counts back into residual; do not fetch history again).
- [ ] Land atomically: fix(heatmap): Simplify the scrubber and reduce chart height

Tasks 9 and 10 code phases may run in parallel in disjoint files. Land 9 before 10;
backend and UI each receive a full landing suite. Controller owns docs and landing.

## Execution and review

Controller owns docs and serial landing in u7. Renderer worker owns JS/pure tests;
gate worker owns _frontend_gate_stream.py in separate worktrees at the stated base.
Code phases start after this revised definition is committed. Apply exact reviewed
patches with --check before --index; no history rewrite or broad staging.

Current main is integrated normally after Task 9 while the owner layout choice is
pending; this advances independent work without a history rewrite. Task 10 patches
must pass fresh apply checks against that merge. After Task 10, run final gates and results
behaviour, refresh real-data live preview and obtain owner sign-off before PR
publication using the repo template. No repeated detector/context invocation or
open-ended colour polishing loop.

## Execution record

- Tasks 1-4: complete at 92019d21; Task 5: complete at 6ac9147.
- Tasks 6-7: superseded before landing by owner's artist-only request.
- Task 8: artist-only checkpoint, 3121 tests and 58 browser checks in 89 runs passed;
  independent source/runtime review approved. Latest UI refinement follows below.
- Task 9: backend checkpoint restores the original four source/test files exactly;
  focused 114 and full 3114 tests passed, independent review approved.
- Task 10: UI simplification patch ready, 141 pure tests passed. Both-browser
  measurements prove that the original gaps plus the 268px panel cannot fit all
  short viewports. Owner choice on compact KPI/bottom spacing is pending; do not
  weaken page-scroll checks or claim the layout complete. Final approval is pending.
- Main integration: advanced before Task 10 while waiting on the layout choice.
  Conflicts are documentation-only; both parent histories are preserved. Fresh
  full suite is 3116 tests. Final UI/browser/results evidence follows Task 10.
- Prototype approval: pending updated live review. No PR/push yet.
