# Streamgraph live-review corrections implementation plan

> **For agentic workers:** Use subagent-driven-development. Parallelize independent
> code and browser-check files, review the integrated change and land atomically.
> Tick steps only after evidence is available.

**Goal:** Preserve original page spacing and show named artists clearly, keeping the
residual count in the scrubber and restoring the original rocket palette.
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

- [ ] Extend existing layerAtY cases for named-only slot mapping, order, empty bands
  and shared boundaries. Demonstrate red against the residual-first renderer.
- [ ] Build baseline/fit/stack from ordered artist counts only. Remove residual path
  rendering/recolouring and map hit slots through order[k]. Preserve one count scale;
  no caps, damping or independent scales.
- [ ] Keep numeric residual row and keyboard position, with blank swatch spacer and
  all artist paths undimmed on its selection. Preserve full week totals, hidden-three
  rows, scrubbing through residual-only weeks and a blank interactive chart for
  globally residual-only data; no chart for all-zero data.
- [ ] Retain original rocket arrays/permutation. Replace the private live preview's
  unlanded navy treatment when the reviewed source is copied there. Remove the
  unused residual fill/swatch tokens after checking their consumers.
- [ ] Extend existing browser alignment, paint, panel, keyboard, absence and JPEG
  pixel checks for the new contract. Preserve focus, clipping and internal-scroll
  checks. Cover residual-only/all-zero cases without a duplicate check family.
- [ ] Run focused red/green and whole frontend test file, independent source review,
  full suite shards, hooks/docsync and locked integrated browser gate.
- [ ] Update README/DESIGN to distinguish named-only silhouette from full week totals.
  Tick evidence and land atomically:
  fix(heatmap): Keep the residual count outside the artist stream

## Execution and review

Controller owns docs and serial landing in u7. Renderer worker owns JS/pure tests;
gate worker owns _frontend_gate_stream.py in separate worktrees at the stated base.
Code phases start after this revised definition is committed. Apply exact reviewed
patches with --check before --index; no history rewrite or broad staging.

After Task 8, merge current main normally under review, run final gates and results
behaviour, refresh real-data live preview and obtain owner sign-off before PR
publication using the repo template. No repeated detector/context invocation or
open-ended colour polishing loop.

## Execution record

- Tasks 1-4: complete at 92019d21; Task 5: complete at 6ac9147.
- Tasks 6-7: superseded before landing by owner's artist-only request.
- Task 8: pending. Revised definition records the owner's explicit direction.
- Prototype approval: pending updated live review. No PR/push yet.
