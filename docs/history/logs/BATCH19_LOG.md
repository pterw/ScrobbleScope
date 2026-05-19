# Batch 19 Execution Log

Archived entries for Batch 19 work packages.

### 2026-05-19 - Batch 19 WP-5 follow-up: owner visual review fixes (Batch 19 WP-5)

- Scope: addressed owner review after WP-5 for heatmap loading, pinwheel
  rendering, desktop heatmap scale, mobile heatmap scale, headline wrapping,
  and front-end/API findings.
- Status: done; owner visual check is the next gate before batch close-out.
- Plan vs implementation:
  - Removed the Bootstrap card wrapper from the heatmap loading state and
    replaced it with an unframed `heatmap-loading-panel`.
  - Restored the original breathing/expanding pinwheel path animation after
    owner review rejected the simplified rotating replacement. The restored
    SVG uses the wrapper for scale, keeps extra viewBox room for expansion,
    and avoids the global `.cls-1` dark-mode stroke override.
  - Widened only `#heatmap-result` on desktop so the heatmap grid uses more
    horizontal space without changing the header/forms/footer layout.
  - Increased desktop cells from 13px to 14px.
  - Replaced the rejected calendar-based mobile layouts with a sequential
    activity strip. The mobile renderer now computes column count from
    viewport/frame width, uses larger squares, and keeps exact dates in
    tooltips instead of preserving month/week columns.
  - Added mobile headline fitting and breakpoint-aware heatmap rerendering so
    responsive design mode can cross between desktop and mobile layouts.
  - Added a rendered-route regression test that prevents the loading state
    from regressing back into a Bootstrap card.
  - Added FINDINGS.md notes for last.timer/API limits, Bootstrap 5.3/theming
    scope, tooltip/font audit, and visual verification tooling.
- Deviations: `tests/test_routes.py` was touched for a focused rendered-markup
  regression; `BATCH19_DEFINITION.md` now explicitly allows this. Browser MCP
  screenshot tools were not exposed in this session, and shell-launched
  headless Chrome did not emit screenshots in the sandbox, so automated visual
  verification was limited to source, syntax, and rendered-template tests.
- Validation: `node --check static/js/heatmap.js` passed. The focused route
  test failed before the loading-template change and passed after it. The full
  pytest gate passed with **387 passed** and 3 existing aiohttp/Python 3.13
  warnings. `pre-commit run --all-files` passed all hooks.
- Forward guidance: owner should visually re-check desktop and mobile heatmap
  sizing plus the loading state. If approved, perform the Batch Close-Out
  Procedure in `AGENTS.md`.

### 2026-05-17 - Batch 19 WP-5: vertical mobile heatmap layout (Batch 19 WP-5)

- Scope: added the narrow-viewport heatmap render path. Desktop remains the
  existing horizontal month/day-labeled SVG; mobile now renders weeks as rows
  and Monday-Sunday as seven columns with compact tappable cells.
- Status: done after owner-feedback pass reduced the mobile grid weight,
  corrected page-level mobile drag, and verified the current app source serves
  "Top Albums" rather than "Album Filtering".
- Plan vs implementation:
  - Split the old `renderHeatmap` body into `renderHeatmapDesktop`.
  - Added `renderHeatmapMobile` and a viewport branch at render time.
  - Mobile render reuses existing date, color, legend, KPI, zero-fill, and
    tooltip helpers.
  - Removed the interim 720px mobile horizontal-scroller fallback from WP-2.
  - Added `data-layout` markers to the generated SVGs for visual/debug probes.
  - Capped mobile cells at 9px with a 1px gap after owner review found the
    initial full-width, 30px, and 18px attempts too heavy.
  - Centered the intrinsic mobile SVG in the frame and avoided height-capping
    that can visually letterbox the grid.
  - Added mobile index row-gutter containment and global modal/overflow
    guards after owner reported page-level horizontal drag on the index page.
- Deviations: mobile viewBox width is calculated as seven cells plus six gaps
  rather than seven full steps, so the grid has no trailing gap. The final
  mobile cell size is capped at 9px instead of filling the frame width.
  The source served by the running local app contains "Top Albums" and no
  "Album Filtering" string; seeing the old label indicates a stale browser
  page/cache or a different running checkout rather than current source.
- Validation: `node --check static/js/heatmap.js` passed. Temporary headless
  Chrome checks loaded the actual local app and a heatmap probe page for
  mobile visual review; the local app response contains "Top Albums" and does
  not contain "Album Filtering". The pytest gate passed with **386 passed**
  and 3 existing aiohttp/Python 3.13 warnings. `doc_state_sync.py --check`
  passed with the expected active-root-definition warning, and
  `pre-commit run --all-files` passed all hooks.
- Forward guidance: all Batch 19 WPs are implemented. Owner visual check is
  the next gate; if approved, perform the Batch Close-Out Procedure in
  `AGENTS.md`.

### 2026-05-17 - Batch 19 WP-4: pinwheel SVG clipping fix (Batch 19 WP-4)

- Scope: fixed heatmap loading pinwheel clipping during blade expansion on
  desktop and mobile.
- Plan vs implementation:
  - Added `overflow="visible"` to the inline pinwheel SVG root.
  - Changed `.heatmap-spinner-wrapper` from an inline-block max-width shell to
    a fixed flex centering box: 120x120 desktop, 96x96 mobile.
  - Set the spinner SVG itself to 80x80 desktop and 64x64 mobile with visible
    overflow.
- Deviations: none.
- Validation: temporary headless Chrome probes using the actual heatmap CSS
  confirmed computed desktop dimensions of wrapper 120x120 / SVG 80x80 with
  visible overflow, and mobile dimensions of wrapper 96x96 / SVG 64x64 with
  visible overflow. The temporary probe file was removed before commit. The
  pytest gate passed with **386 passed** and 3 existing aiohttp/Python 3.13
  warnings. The pre-commit gate passed with all 10 hooks green.
- Forward guidance: WP-5 is next and should replace the interim mobile
  horizontal-scroller fallback with the vertical mobile heatmap renderer.

### 2026-05-17 - Batch 19 WP-3: Top Albums pill and subtitle cleanup (Batch 19 WP-3)

- Scope: renamed the album-mode pill and modal guidance from "Album Filtering"
  to "Top Albums" and verified the heatmap subtitle cleanup from WP-2.
- Plan vs implementation:
  - Updated `templates/index.html` pill text, comments, and welcome-modal tip.
  - Confirmed the old `#heatmap-result-subtitle`, `resultSubtitle`, and
    `heatmap-subtitle` result logic were already removed by WP-2.
  - Kept `formatDateLong` because tooltip rendering still calls it.
- Deviations: added a focused route regression test for the rendered index
  page label and modal copy, increasing the expected test count by 1.
- Validation so far: the new regression test failed before the template
  change, then passed after the copy update. The full pytest gate passed with
  **386 passed** and 3 existing aiohttp/Python 3.13 warnings.
- Forward guidance: WP-4 can proceed next. Do not remove `formatDateLong`
  unless tooltip date formatting is replaced too.

### 2026-05-17 - Batch 19 WP-2 follow-up: contain mobile heatmap scrolling (Batch 19 WP-2)

- Scope: owner review of WP-2 found that responsive design mode could drag the
  heatmap page and that the actual heatmap grid was too small to read on
  mobile-width viewports.
- Plan vs implementation: kept the full vertical mobile renderer scoped to
  WP-5, and added a narrow WP-2 CSS containment fix:
  - `.heatmap-frame` now clips its own contents.
  - `#heatmap-grid` remains the horizontal scroll container and contains
    horizontal overscroll.
  - Mobile CSS gives the desktop SVG a 720px rendered width so cells remain
    legible until WP-5 replaces the render path with a vertical grid.
- Deviations: updated `BATCH19_DEFINITION.md` acceptance to record the
  interim mobile fallback explicitly, avoiding drift between owner review,
  CSS behavior, and the later WP-5 scope.
- Validation: temporary headless Chrome probe reproduced the pre-fix
  state (`gridIsContainedScroller=false`, SVG height 62px) and passed after
  the CSS fix (`gridIsContainedScroller=true`, SVG height 106px). The
  temporary probe file was removed before commit. The pytest gate passed with
  **385 passed** and 3 existing aiohttp/Python 3.13 warnings. The pre-commit
  gate passed with all 10 hooks green.
- Forward guidance: WP-3 remains next. WP-5 should replace or override the
  interim `#heatmap-grid svg { width: 720px; }` mobile fallback when the
  vertical mobile renderer lands.

### 2026-05-17 - Batch 19 WP-2: heatmap frame, headline, KPIs, and legend (Batch 19 WP-2)

- Scope: redesigned the heatmap result surface into a shareable artifact with
  a custom frame, accent username headline, four KPI stats, and a frame-top
  legend.
- Plan vs implementation:
  - Replaced the Bootstrap result `.card` wrapper with `heatmap-headline`,
    `heatmap-frame`, `heatmap-frame-top`, `heatmap-kpi-row`, and the existing
    grid/legend elements.
  - Added heatmap-scoped surface tokens and responsive frame/KPI/legend CSS
    without touching `global.css`, `base.html`, or Python files.
  - Added JS helpers for headline building, KPI rendering, best-day/active-day
    counts, current streak, and safe DOM clearing.
  - Kept user-provided username rendering on `textContent` plus
    `createTextNode`; no user data is written through HTML parsing.
  - Applied monospaced font attributes directly to SVG month/day labels.
- Deviations: clarified `BATCH19_DEFINITION.md` wording for the mobile legend.
  The original line contradicted the provided WP-2 markup and WP-5 dependency;
  the canonical behavior is now legend top-right on desktop and stacked below
  KPIs above the grid on mobile.
- Validation: `.venv\Scripts\python.exe -m pytest -q` passed with
  **385 passed** and 3 existing aiohttp/Python 3.13 warnings.
  `node --check static/js/heatmap.js` exited 0. Headless Chrome rendered a
  temporary local light/dark fixture using the actual heatmap CSS at desktop
  and mobile widths; the temporary fixture was removed before commit.
  `pre-commit run --all-files` passed with all 10 hooks green.
- Forward guidance: WP-3 can remove the old subtitle references next. Keep
  `formatDateLong` unless a fresh search proves it is unused, because tooltip
  copy still depends on it after WP-2.

### 2026-05-17 - Batch 19 WP-1: stale perf docs and bootstrap drift controls (Batch 19 WP-1)

- Scope: corrected stale heatmap performance documentation and tightened
  cross-agent bootstrap rules before UI polish begins.
- Plan vs implementation: kept the WP doc-only intent, then folded in
  owner-requested drift-control fixes discovered during audit:
  - `AGENT_NOTES.md` now points to archived Batch 18 and active Batch 19
    definitions, removes the obsolete sequential-fetch diagnosis, and records
    the measured 10.9s rate-limit floor.
  - `FINDINGS.md` is now current for Batch 19, tracks 385 tests, and reframes
    F-B18-11 as rate-limit bound rather than sequential.
  - `.gitignore` no longer ignores `FINDINGS.md`; it is shared cross-agent
    context because PLAYBOOK and Batch 19 reference it.
  - `AGENTS.md` and `HANDOFF_PROMPT.md` now align on the no-push rule and
    document the expected non-blocking root batch-definition warning while a
    batch is active.
  - `BATCH19_DEFINITION.md` acceptance criteria now distinguish active docs
    from historical archives, and WP-2/WP-5 wording was clarified.
- Deviations: added `AGENTS.md`, `HANDOFF_PROMPT.md`, `.gitignore`, and
  `BATCH19_DEFINITION.md` to WP-1 because the audit found they directly
  affected turn-one orientation and cross-agent drift mitigation.
- Validation: `.venv\Scripts\python.exe -m pytest -q` initially hit sandboxed
  Windows temp permissions, then passed with approval: **385 passed**.
  `pre-commit run --all-files` passed with all 10 hooks green after using the
  per-command Git safe-directory override required by this workspace.
- Forward guidance: WP-2 can start next. Browser visual verification will be
  most useful after WP-2, WP-4, and WP-5 if the local app is running.

### 2026-05-17 - Batch 19 WP-0: definition committed (Batch 19 WP-0)

- **Batch 19 started.** Branch `feat/heatmap` continued from Batch 18.
- Definition committed: `BATCH19_DEFINITION.md` (5 WPs: perf doc corrections,
  heatmap frame/headline/KPIs redesign, pill rename + subtitle removal,
  pinwheel clipping fix, mobile vertical layout).
- Batch 18 closed out: definition archived to
  `docs/history/definitions/BATCH18_DEFINITION.md`, Section 2 table updated,
  Section 3 updated to Batch 19 active, perf note corrected.
- Scope constraint: all Batch 19 changes confined to `heatmap.css`,
  `heatmap.js`, `templates/index.html`, pinwheel SVG, and doc files.
  No global.css, no Python changes. Full app palette/font rebrand deferred.
- **385 tests passing**, all 10 pre-commit hooks green.
- Next: WP-1 -- correct stale perf docs + update FINDINGS.md.
