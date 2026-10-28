# Streamgraph live-review corrections implementation plan

> **For agentic workers:** Use subagent-driven-development. Keep the three slices isolated,
> execute their code phases in parallel, review each and land serially. Tick steps only
> after evidence is available.

**Goal:** Restore the original page rhythm, balance the residual band without distorting
counts, and distinguish the two burst-selected artists.

**Architecture:** Three UI corrections on the existing renderer. No payload or schema
change. Design: [owner-directed live review](../specs/2026-10-28-streamgraph-live-feedback-design.md).
Original Tasks 1-4: [completed implementation plan](2026-10-28-streamgraph-bursts.md).
**Tech Stack:** Existing Python/pytest, hand-built SVG and Playwright gate. No dependency.

## Global constraints

AGENTS.md, global-rules.md and the original SDD constraints still apply, with these owner
updates: the chart/tooltip must not scroll internally; original document spacing and normal
page flow are restored. The owner deferred a 4.5:1 colour target during this iteration.
Guards remain advisory. All tests/hooks/docsync remain required. Use the qualified primary
Python and the browser lock. Stage named paths only, no attribution, no push before owner
prototype sign-off. Code base: 92019d214b993005448cf18dfab3abbfb94b9e58.

## Task 5: Restore spacing and quiet the residual row

**Touches:** static/css/heatmap.css; scripts/dev/_frontend_gate_stream.py (internal-scroll
assertion only); DESIGN.md (Placement/Scrubber prose); plan and landing log.
**Consumes:** Task 3's reserved chart room and existing is-hovered/data-rank DOM contract.
**Produces:** Original page spacing with a reserved chart and a normal-weight residual row.

- [x] Remove the stream-only result width/padding, headline size, header/frame/KPI spacing
  compression overrides. Keep the original 860px grid focus-padding rule and the stream
  grid's min-height:25rem and overflow-y:hidden. This restores .heatmap-stage's original
  padding and the original header/frame gaps without altering the global stylesheet.
- [x] Keep opacity:1 on .stream-panel-row.is-hovered; apply font-weight:700 only to
  .stream-panel-row.is-hovered:not([data-rank="other"]). The base row remains 400.
- [x] In the existing hover reader, verticalScroll checks the grid and panel only. Remove
  its document.scrollHeight check because the accepted original document flow may extend
  past a short viewport. Do not weaken rowsOutside, focus clearance or panel clipping.
- [x] Verify computed original top/header/frame gaps and residual font-weight400 in Firefox
  and Chromium, with16rows/no internal scrolling at860/1024/1280/1920 widths. No new unit
  test for this reversible styling change; run the existing browser gate and full landing
  gates. Update DESIGN's temporary compressed-layout wording and record the scope correction.
- [x] Land atomically: fix(heatmap): Restore result spacing and quiet the residual row

## Task 6: Split the residual around the named stack

**Touches:** static/js/heatmap.js (drawStream, layerAtY); tests/frontend/test_heatmap_pure_functions.py
(existing hit-test behaviour); scripts/dev/_frontend_gate_stream.py (existing alignment/export
checks); README.md and DESIGN.md (controller at landing); plan and landing log.
**Consumes:** Unchanged payload.other, artist counts, streamOrder, stackLayers and streamFit.
**Produces:** Two equal residual caps, one logical other path and tooltip row, same linear scale.

- [ ] Extend the existing layerAtY parameter cases for upper/lower residual caps, shared
  edges and empty caps. Prove the new upper-cap case fails against the unchanged renderer.
  Extend the existing browser alignment check to prove two equal caps surround named bands;
  no second helper/check that only asserts DOM shape.
- [ ] In drawStream, make halfOther = payload.other.map(n => n / 2), then stack
  [halfOther, ...ordered artist counts, halfOther] through the existing baseline/fit helpers.
  Render the two caps as two closed subpaths of ONE stream-layer-other path, preserving
  artistCount+1 path count and a single rank="other" logical identity. Keep named artists
  contiguous. No new general-purpose layer model or helper is needed.
- [ ] Teach layerAtY the terminal cap maps to other; preserve existing named rank mapping,
  zero-thickness skips and boundary ownership. Tooltip totals and keyboard rows remain
  unchanged. Both caps must hover/dim as the same other category.
- [ ] Update existing export probe logic to sample inside each actual residual cap rather
  than the midpoint spanning the named-artist gap. Verify both caps survive theme switches
  and real JPEG export. Keep gate pixel assertions and hover/keyboard checks intact.
- [ ] Run focused red/green, whole frontend test file, file hooks and one locked integrated
  browser gate; review patch. At landing run full shards/hooks/docsync, update README/DESIGN
  with proportional caps/one tooltip count, tick evidence, and commit:
  feat(heatmap): Sandwich named artists between equal residual caps

## Task 7: Give burst artists a separate colour family

**Touches:** static/js/heatmap.js (palette, layerColour, payload cap comment);
tests/frontend/test_heatmap_pure_functions.py (existing layer-colour behaviour); DESIGN.md
(controller at landing); plan and landing log. Separate worktree avoids Task 6 file conflicts.
**Consumes:** Artist rank0..9 top-ten, rank10..11 burst-selected; existing theme argument.
**Produces:** Twelve distinct categorical colours; two cool full-ribbon burst identities.

Palette values are owned here for the implementation; runtime remains the sole rendering
owner. Each array is rank order0..11, so remove STREAM_STEPS and return the array's rank entry.

```text
light: #e85d44 #4a235a #f4a259 #6a4baf #c8335b #e9c46a #3b336a #d97757 #8e2d56 #b39dde #2a9d8f #56cfe1
dark:  #e85d44 #8a5a9b #f4a259 #9574ce #c8335b #e9c46a #7870b3 #d97757 #bb5d8d #b39dde #2a9d8f #56cfe1
```

- [ ] Replace the existing touching-step test with the intended categorical behaviour:
  both themes produce12unique colours; ranks10/11 have distinct cool hues (HSV hue140-220),
  top-ten hues are outside that reserved interval. Read actual layerColour output; do not
  pin literal hex strings or numeric palette indices. Parametrize themes; eliminate the
  now-irrelevant duplicate burst-volume ordering cases. Prove red before palette changes.
- [ ] Type the arrays above, remove the obsolete permutation and LUT sampling comments,
  retain streamPalette hook and cap12 via STREAM_PALETTE.light.length. No CSS tokens,
  algorithmic recolouring, new payload flag or new dependency.
- [ ] Run focused/whole-file tests and scoped hooks. Landing follows Task6 so the one full
  browser gate proves the integrated stack and JPEG colours. Update DESIGN's obsolete
  twelve-rocket-step/permutation description; keep original density-grid ramp unchanged.
- [ ] Land atomically: feat(heatmap): Reserve cool colours for burst-selected artists

## Execution and review

Code phases run in parallel at the stated base: t5 CSS/gate reader, t6 geometry/tests/gate,
t7 palette/test. Controller owns all docs and serial landings in u7. Exact patches may touch
one file in disjoint hunks; every landing uses git apply --check --index first. No three-way
apply or history rewrite. A context failure is resolved from current source before editing.

Land5,6,7 with independent code/landing review and the same full3shards/hook/docsync procedure.
Run the full browser gate at the integrated7head, plus affected checks at each earlier landing.
Then merge current main normally under review, run final gates/results behaviour, refresh the
private live preview and obtain owner sign-off before PR publication using the repo template.
No duplicate detector/context invocation or open-ended colour polishing loop.

## Execution record

- Planning checkpoint: original Tasks1-4 complete at92019d21; follow-up code not started.
- Task5: complete in the atomic `fix(heatmap): Restore result spacing and quiet the residual row`
  checkpoint. Fresh suite: 3117 passed. Actual landing-source locked spacing probe: eight cases passed
  across Chromium/Firefox, four desktop sizes, original gaps and residual weight400, no internal scroll.
  Full browser integration remains at the Task7 head; owner prototype approval is still pending.
- Task6: pending.
- Task7: pending.
- Prototype approval: pending updated live review. No PR/push yet.
