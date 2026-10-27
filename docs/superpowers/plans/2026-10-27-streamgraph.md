# Streamgraph Under the Heatmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The heatmap result page draws a streamgraph of the listener's top 10 artists, per week, directly under the heatmap grid. Each stream point sits under its heatmap week column. Hovering, touching or arrowing to a week shows a scrubber panel (every layer, that week's counts) and rings the matching heatmap column. Save image includes the streamgraph. This is README row 7 of the UI audit v6 design handoff.

**Architecture:** One new pure function in `scrobblescope/plays.py` (`aggregate_weekly_artist_counts`) builds the weekly payload from the plays the heatmap job already fetched (no extra Last.fm calls). The job stores it next to `daily_counts`. In the browser, `static/js/heatmap.js` gains (a) pure functions for layer order, the wiggle baseline, stacking, path smoothing, colours, panel content and keyboard targets, exposed through the existing guarded test seam (`window.__scrobbleHeatmapTestHooks`), and (b) separate DOM drawing, interaction and export code that calls them. Each browser task adds its own frontend-gate checks (the stream checks in one new module, `scripts/dev/_frontend_gate_stream.py`; the page-scoping check beside the existing theme checks) and registers them in `CHECKS`. No charting library, no new dependency, no schema change.

**Tech Stack:** Python 3.13 stdlib (`collections`, `datetime`), vanilla JS in the existing `heatmap.js` IIFE, SVG, Pointer Events and `KeyboardEvent` (both work in Firefox), pytest plus the Playwright browser harness in `tests/frontend/` (Chromium only), the frontend gate `scripts/dev/frontend_gate.py`.

**Branch:** `feat/ui-audit-v6-streamgraph`, cut from `feat/ui-audit-v6` at `92df4699`. A pull request stacked on PR #277 (owner ruling U5). Worktree `C:/ssw/u7`.

## Global Constraints

Every task's requirements include this section.

- Lean tests: one test per intended behaviour, parametrized, an existing module extended before a new one. Prove red against the unchanged code, then green, and quote both lines. No planted-defect runs (`mutate.py` is not used in this repository). Fakes for every API; nothing calls Last.fm.
- No code is pasted into this plan beyond signatures, the payload JSON, selectors and test names; the executor writes the implementation (owner's standing rule, ruling S12).
- No schema change, no new dependency. ASCII only in hand-written files and commit messages. A JS comment never contains daisyUI class words (Tailwind scans `static/js`).
- Browser gates only through `C:/ssw/tools/with_browser_lock.py`. The owner browses in Firefox. No Chromium-only API is planned (Pointer Events, `KeyboardEvent`, SVG, `touch-action`, `prefers-reduced-motion` all exist in Firefox); a task that needs one stops and says so.
- **Where Firefox is and is not covered** (verified at 92df4699): `tests/frontend/` runs Chromium only (`tests/frontend/conftest.py`, the `js_browser` fixture). The frontend gate runs Firefox only on group `STATIC_ASSETS` (`scripts/dev/frontend_gate.py:497-505`, `BROWSER_SCOPES`, "a regression canary, not a second acceptance gate"), and the touch-swipe check is Chromium only by design (`scripts/dev/_frontend_gate_heatmap_access.py:1426-1428`, `1488`). This plan does not change `BROWSER_SCOPES`. So every stream check added to the gate and to `tests/frontend/` runs in Chromium only. Firefox coverage comes from the **Firefox probe** each browser task runs as an acceptance step (see "Firefox probe" below), and its output is quoted in the task's report.
- **Firefox probe** (tasks 2, 4, 5, 6, 7, 8, 9): a scratch Python script, not committed, at `C:/ssw/scratch/streamgraph-probe-<TASK>/probe.py` (delete the directory afterwards). It imports `serve_app` and `_launch_browser` from `scripts.dev._frontend_gate_runtime`, builds the job with `seed_stream_job` from `scripts/dev/_frontend_gate_stream.py` (Task 5 creates it; Task 2's probe loads `heatmap.js` directly with `window.__scrobbleHeatmapTestMode` set, and Task 4's probe builds the same plain heatmap job as `check_heatmap_zero_cells_follow_theme`, `scripts/dev/_frontend_gate_theme.py:696`, because no stream exists yet), launches `firefox`, runs the same assertions the task's Chromium check makes, and prints one `PASS`/`FAIL` line per assertion. Run it as `python C:/ssw/tools/with_browser_lock.py <PY> C:/ssw/scratch/streamgraph-probe-<TASK>/probe.py` from the worktree root, with the repository root on `PYTHONPATH`. The report quotes the output. A `FAIL` that only Firefox shows is a task failure, not a note.
- **Scope (owner ruling U18, 2026-10-27):** the streamgraph is desktop-layout only; a mobile streamgraph is a later PR. The timeline dark surfaces apply inside the chart frame (`#heatmap-result-frame`, the `.heatmap-frame` element) only; the page background outside the frame is unchanged. Nothing in this plan edits the `:root` or `[data-theme="dark"]` token blocks.
- Every task that adds a gate check lists `scripts/dev/frontend_gate.py` (its `CHECKS` registration) in Files (ruling SP-F8). Those tasks are serial by wave, so no two touch it at once.
- Contrast floor (U6): every new pairing clears 4.5:1 for text and 3:1 for non-text in both themes. A layer pair that fails is not fixed by editing the owner's ramp: the task stops and returns NEEDS_CONTEXT with the measured pair (ruling S10).
- A file outside a task's `Files` that must change: stop and return NEEDS_CONTEXT.
- Commit step: a `code`-mode task never commits. Its code phase stages the files and writes a patch; the landing (controller or a land-mode implementer) applies the patch and commits with the task's subject line after the Gates block. Each task's last step names that subject.

---

## Verified background (read at 92df4699)

- **Grid columns are Monday-first calendar weeks, not 7-day steps from `from_date`** (ruling S2, S7). `static/js/heatmap.js` `renderHeatmapDesktop`: `startDow = mondayIndex(fromDate)` (line 1243, `mondayIndex` at line 72 maps `getDay()` to Mon=0..Sun=6), `numCols = Math.floor((startDow + totalDays - 1) / 7) + 1` (line 1244), and a day's column is `Math.floor((startDow + i) / 7)` with `i` the day's index from `from_date` (lines 1316-1318). So column 0 starts on the Monday on or before `from_date` and holds `7 - startDow` real days; the last column is partial too. The design agent's "count 7 days from `from_date`" is wrong for this grid and is NOT used. The aggregation puts each play in week `(play_day - week0_monday).days // 7`, where `week0_monday = from_date - timedelta(days=from_date.weekday())` (Python `weekday()` is Mon=0, equal to `mondayIndex`). `weeks[t]` is the ISO date of that column's Monday (for column 0 this can be before `from_date`).
- Column x in the grid SVG: `LEFT_PAD + col * STEP` (line 1320); `CELL_SIZE = 14`, `CELL_GAP = 2`, `STEP = 16`, `LEFT_PAD = 32`, `TOP_PAD = 20` (lines 27-31). The grid SVG uses `viewBox="0 0 svgWidth svgHeight"` with `width="100%"` (lines 1245, 1254-1255), so a second SVG with the same viewBox width and `width="100%"` scales identically and its columns line up with the squares.
- **The mobile layout has no week columns.** `renderHeatmapMobile` (line 1365) lays days row-major with a variable column count (lines 1383-1417). The streamgraph is drawn on the desktop layout only (width at or above `MOBILE_MAX_WIDTH = 860`, line 47); the mobile layout shows none, and Save image on mobile saves what is on screen, as it already does (comment at lines 570-580) (ruling S8, flagged for the owner).
- `daily_counts` counts every play dated inside `[from_date, to_date]` in UTC, whatever its names (`scrobblescope/plays.py:167-183`). `scrobblescope/heatmap.py:112` calls it on `fetch.plays`; results are stored at lines 130-142. `scrobblescope/jobs.py:518-533` (`_context_view`) copies `results` and then `results["daily_counts"]` defensively. The route returns `{"ready": True, **ctx["results"]}` (`scrobblescope/routes/heatmap_flow.py:189-190`), so a new results key reaches the browser with no route change.
- `normalize_name(artist, album)` in `scrobblescope/domain.py:7` takes two arguments. The artist is only punctuation-normalised (a punctuation-only artist such as `!!!` normalises to `""`). The artist key for a play is `normalize_name(artist, "")[0]` (ruling S11; Task 1 confirms against `domain.py` and states the call it used).
- **Colour and export plumbing the stream must respect.** `zeroFill()` (heatmap.js:148-149) reads `--heatmap-empty` from `document.documentElement`, and the zero cells carry it as a `fill` attribute (resolved at draw time) so the saved image needs no stylesheet. `updateZeroFills()` (line 1817) repaints them on a theme change, called from `initThemeObserver()` (line 1797). `gridAsImage(svg, width, height)` (line 353) clones and serialises the SVG with no stylesheet, pinning only the month and day labels to `monospace` with a resolved `fill` (lines 363-369). `resolvedColour(token)` (line 334) resolves a custom property through a probe element appended to `document.body`. `drawHeatmapImage()` (line 596) paints the canvas background with `resolvedColour('--heatmap-surface')` (line 622). So every stream paint (layer fill, "Everything else", label text and font) is written as a resolved attribute at draw time and on a theme change; a rule that depends on a class or a custom property would export unstyled.
- The global tokens are `--heatmap-empty` `#c8bfad` (light, `static/css/tailwind.src.css:222`) and `#262230` (dark, line 298), and `--heatmap-surface` `var(--ss-surface-sunken)` = `#f0ebe0` (light, lines 177-178) and `#181520` (dark, lines 273-274). The reference's dark timeline surfaces differ (`#1f1b28` frame, `#2e2939` empty cells); ruling U5 applies them to this page's frame only, so the plan scopes them to `.heatmap-frame` (see Interfaces, CSS) and never edits the `:root` or `[data-theme="dark"]` blocks. The reference's page background outside the frame (`#15121b` dark, `#faf7f0` light) is not applied: `templates/partials/_heatmap_result.html:11` does have a wrapper (`section#heatmap-result.heatmap-stage`), but the page background is `body` of `index.html`, shared with the form and the other modes, and owner ruling U18 limits the timeline surfaces to the chart frame. The frame therefore sits on the unchanged site background.
- Existing seams: `window.__scrobbleHeatmapTestHooks` (heatmap.js line 1901, only when `window.__scrobbleHeatmapTestMode` is set), `rocketColor(t)` returning an `rgb(r,g,b)` string and `ROCKET_STOPS` (lines 16-24, 120), `saveHeatmapImage` / `drawHeatmapImage` / `gridAsImage` (lines 353, 582-661), `rerenderKeepingFocus` (line 1862), the reduced-motion block at `static/css/heatmap.css:626`, `_contrast_ratio` in `scripts/dev/_frontend_gate_colour.py:137`, `serve_app` and `_launch_browser` in `scripts/dev/_frontend_gate_runtime.py:88,73`, the check registry `CHECKS` in `scripts/dev/frontend_gate.py` (line 249, entries `(name, check, viewports, group)`; the heatmap theme and export checks are in group `THEME_MOTION`, lines 275-283), fixture jobs built with `jobs.create` / `jobs.succeed` plus `heatmap_statistics` (for example `_seed_year_job`, `_frontend_gate_heatmap_access.py:1387`), JPEG decoding inside the page by `Image` + canvas (`_frontend_gate_results.py:743-760`, `790-815`), and `tests/frontend/test_heatmap_pure_functions.py` (module marked `pytest.mark.browser`, fixture `js_page`).

## Interfaces (frozen; every task reads this table, and a name that is not here is not used)

**Payload (S1)** - job results key `weekly_artists`, stored next to `daily_counts`:

```json
{"weeks": ["2025-10-27", "..."],
 "artists": [{"name": "Radiohead", "counts": [0, 3, "..."]}],
 "other": [5, 9, "..."]}
```

- `weeks`: ISO date of each grid column's Monday, length `numCols` (53 or 54 for a 365-day window). `artists`: at most `top_n = 10`, largest total first; ties broken by normalised key ascending; `name` is the first spelling seen. Every `counts` and `other` list has `len(weeks)` non-negative integers. The artist's **rank** is its index in `artists` (volume order, 0 = largest).
- Invariant: for each week, the sum of every artist's count plus `other` equals the sum of `daily_counts` over that column's days inside the window. `other` holds all artists outside the top 10 and every play whose artist key is empty (empty or punctuation-only artist).
- Validity rule used by the browser: `weeks` is an array of `numCols` strings; `artists` is an array of 0..10 objects whose `name` is a string and whose `counts` is an array of `numCols` finite numbers >= 0; `other` is an array of `numCols` finite numbers >= 0. Anything else (absent, older stored result, wrong length) draws no streamgraph, changes nothing else and never throws.
- Python: `aggregate_weekly_artist_counts(plays, from_date, to_date, top_n=10) -> dict` in `scrobblescope/plays.py`, pure, no I/O, no clock, UTC days like `aggregate_daily_counts`.

**JS pure functions** (in `heatmap.js`, no DOM access, all exposed in `__scrobbleHeatmapTestHooks` under the same names). A layer is identified by an **id**: its rank (integer 0..9) or the string `'other'` ("Everything else").

| Name | Signature and meaning | Task |
|---|---|---|
| `streamOrder` | `(volumes: number[]) -> number[]`: indices sorted by volume descending, then placed so the biggest is in the middle and the rest alternate (reference loop: `j % 2 ? unshift : push`). Returns the artist layers bottom to top as indices into `volumes`. | 2 |
| `streamBaseline` | `(layers: number[][]) -> number[]`: Byron-Wattenberg wiggle baseline; `layers` is per-week count arrays bottom to top including "Everything else" at index 0; returns the per-week baseline, centred so the mean midline is 0. | 2 |
| `stackLayers` | `(layers: number[][], baseline: number[], scale: number) -> {y0: number, y1: number}[][]`, indexed `[layer][week]`; values are signed distances above the centre line (up is positive), `y1 - y0 = count * scale`. | 2 |
| `streamScale` | `(weekTotals: number[]) -> number`: `STREAM_PEAK / max(weekTotals)`; `0` when the max is 0. | 2 |
| `smoothPath` | `(top: {x: number, y: number}[], bottom: {x: number, y: number}[]) -> string`: closed SVG path; both arrays run left to right (the function reverses `bottom` itself); Catmull-Rom to Bezier, divisor 6, on both edges. | 2 |
| `layerColour` | `(rank: number, theme: 'light' \| 'dark') -> string` (an `rgb(r,g,b)` string from `rocketColor`): ramp `[.95,.88,.81,.74,.67,.60,.53,.46,.39,.32]` by rank; dark uses it as is; light multiplies every value by `0.83 / 0.95` so the top stop is 0.83 (ruling S9: a rescale, not a clamp, which would give ranks 0 and 1 one colour). | 2 |
| `streamPayloadValid` | `(payload: any, numCols: number) -> boolean`: the validity rule above. | 5 |
| `weekFromX` | `(x: number, weeks: number) -> number`: `x` in stream viewBox units; the nearest week index, clamped to `0..weeks-1`. | 7 |
| `layerAtY` | `(stack: {y0,y1}[][], week: number, y: number) -> string \| number \| null`: the id of the layer whose `[y0, y1]` band holds `y` at `week` (`y` in the same signed units; a boundary belongs to the layer above); `null` when `y` is outside every band. | 7 |
| `panelModel` | `(payload, week: number, hoverId: string \| number \| null) -> {header: string, side: 'left' \| 'right', rows: {id, name: string, count: number, hovered: boolean}[]}`: header `Week of <Mon D> - <N> scrobbles` (`N` is the week total with thousands separators; `1 scrobble` when `N` is 1); rows top of stack first, one per artist layer with a count above zero, then "Everything else" always last; `side` is `'left'` when `week > 34` (the panel flips left past week 34) else `'right'`. | 7 |
| `streamKeyTarget` | `(key: string, state: {week: number, position: number}, dims: {weeks: number, layers: number}) -> {week, position} \| null`: `ArrowLeft`/`ArrowRight` change `week` by one, `ArrowUp`/`ArrowDown` change `position` by one (position 0 is the top of the stack, `layers - 1` is "Everything else"; up is toward 0), `Home`/`End` set `week` to `0` / `weeks - 1`; edges clamp, no wrap; any other key returns `null`. | 8 |
| `streamStartTarget` | `(dims: {weeks, layers}) -> {week, position}`: the state when the stream first takes focus: `week = min(26, dims.weeks - 1)`, `position = 0`. | 8 |
| `streamPositions` | `(order: number[]) -> (number \| 'other')[]`: layer ids from the top of the stack down: the artist ranks of `order` (bottom to top) reversed, then `'other'`. The keyboard `position` indexes this array. | 8 |

**Existing names the stream tasks use** (not new):

| Name | What it is | Task that adds it |
|---|---|---|
| `seed_stream_job(weeks: int = 53, payload: bool = True) -> tuple[str, str]` | in `scripts/dev/_frontend_gate_stream.py`: a finished heatmap job over a window of `weeks` columns whose `weekly_artists` is a valid payload with 10 artists, or without the key when `payload` is false; returns the job id and the last day. Used by the gate checks of Tasks 5-9 and by the Firefox probes of Tasks 5-9. | 5 |
| `.heatmap-cell` | the existing `rect` of each heatmap day (`heatmap.js:1330` desktop, `:1430` mobile); the stream checks read the columns from these. | existing |

Geometry constants (named once in `heatmap.js`, in grid units): lengths are derived from the reference's 27 px pitch by `STEP / 27`; font sizes are NOT scaled (ruling SP-F9). Layer x for week `t` is `LEFT_PAD + t * STEP + CELL_SIZE / 2`; `STREAM_PEAK = 300 * STEP / 27` (about 177.8, the tallest week's total height); `STREAM_BAND = 380 * STEP / 27` (about 225.2, the plot height, centre line at its middle); `STREAM_LABEL_H = 24 * STEP / 27` (the section-label strip above the plot); `STREAM_GUIDE_W = 1.5 * STEP / 27` (about 0.89, guide stroke width); `STREAM_RING_W = 2 * STEP / 27` (about 1.19, ring stroke width); `STREAM_RING_PAD = 4 * STEP / 27` (about 2.37, ring offset and corner radius). The stream is centred on the plot's middle line. **Ink** is the page's own text token `--color-base-content` (`static/css/tailwind.src.css:102` light `#1a1820`, `:234` dark `#f1ede4`, the headline colour at `static/css/heatmap.css:347`; the month and day labels use `currentColor`, which inherits it). It is resolved on the frame like the other tokens; no new colour is introduced. Font sizes (ruling SP-F9): the SVG section label uses font size `9.5`, the same grid-unit size as the day labels (heatmap.js:1273) and the month labels (heatmap.js:1296), unscaled and never smaller; the panel uses the page's existing HTML text tokens (`--text-body-sm`, `--text-label-sm`, `--font-mono`, `static/css/tailwind.src.css:26, 36, 40`).

**DOM** (all inside the existing `#heatmap-grid` container, below the grid SVG; the template is unchanged because `#heatmap-grid` already exists at `templates/partials/_heatmap_result.html:33` and gets `position: relative` from CSS):

| Selector | What it is |
|---|---|
| `svg#stream-chart.stream-chart[data-layout="stream"]` | the chart region: `viewBox` width equals the grid SVG's `svgWidth`, `width="100%"`; `data-columns` is a space-separated list of the plotted x of every week in viewBox units (so the gate reads real geometry); Task 8 makes it the one tab stop (`tabindex="0"`, `role="application"`, `aria-label`) |
| `text.stream-section-label` | "TOP ARTISTS - PLAYS PER WEEK" inside the SVG (so Save image carries it), `font-size` `9.5` (as the month labels), letter-spacing `.12em`, muted; `font-family` and `fill` written as attributes |
| `line.stream-gridline` | one per month start, plot-height vertical line, stroke `--stream-line` resolved into the `stroke` attribute |
| `path.stream-layer[data-rank="N"]` | an artist layer, `N` = rank 0..9 |
| `path.stream-layer.stream-layer-other[data-rank="other"]` | "Everything else"; drawn first (bottom); 11 layer paths in all when 10 artists exist |
| `line.stream-guide` | vertical guide at the hovered column centre, plot height, ink stroke at opacity `.55`, `stroke-width` `STREAM_GUIDE_W`; `stroke` written as a resolved attribute |
| `rect.stream-column-ring` | one ring in the grid SVG around a heatmap column: x `LEFT_PAD + week * STEP - STREAM_RING_PAD`, y `TOP_PAD - STREAM_RING_PAD`, width `CELL_SIZE + 2 * STREAM_RING_PAD`, height `7 * STEP - CELL_GAP + 2 * STREAM_RING_PAD` (the seven rows), `rx` `STREAM_RING_PAD`, `fill` none, ink stroke of width `STREAM_RING_W` (resolved attribute); removed by `clearWeek()` |
| `div#stream-panel.stream-panel[aria-live="polite"]` | the scrubber panel, a child of `#heatmap-grid`, hidden when no week is shown; children `.stream-panel-header`, and per row `.stream-panel-row[data-rank]` (class `is-hovered` on the hovered one) holding `.stream-panel-swatch`, `.stream-panel-name`, `.stream-panel-count` |

DOM functions in `heatmap.js` (not in the test seam): `drawStream(data, svgWidth)` appends the chart and returns nothing; it keeps the stacked layers (`stackLayers` output), the validated payload, the `streamOrder` result and the plotted x values in module-level state (reset on every `renderHeatmap`), which `showWeek`, the pointer and key handlers and `recolourStream` read (Task 5); `showWeek(week: number, hoverId: string | number | null)` and `clearWeek()` drive dimming, guide, ring and panel (Task 7); a re-render (`renderHeatmap`, including a resize) clears the shown week: panel, ring, guide and dimming are gone and no stale ring is left in the new grid SVG; the key handler calls `streamKeyTarget` and `showWeek` (Task 8); `recolourStream()` rewrites the resolved fills on a theme change, called from `initThemeObserver()`'s `data-theme` branch next to `updateZeroFills()` (Task 6).

**CSS** (all in `static/css/heatmap.css`; values copied from the reference). Custom properties are declared on `.heatmap-frame` for light and on `[data-theme="dark"] .heatmap-frame` for dark, never on `:root` or in a global `[data-theme]` block:

| Property | Dark | Light |
|---|---|---|
| `--heatmap-surface` (overridden, so the frame takes the timeline surface) | `#1f1b28` | `#f0ebe0` |
| `--heatmap-empty` (overridden, so the empty cells take the timeline value) | `#2e2939` | `#c8bfad` |
| `--stream-other` ("Everything else" fill) | `#3a3347` | `#ddd5c5` |
| `--stream-line` (gridlines, panel border) | `#352e43` | `#e5dfd1` |
| `--stream-muted` (section label, panel header) | `#908a9a` | `#6c6676` |
| `--stream-accent` (focus outline) | `#b39dde` | `#6a4baf` |
| `--stream-panel-bg` | `#1f1b28` | `#ffffff` |
| `--stream-panel-shadow` (a full `box-shadow` colour) | `rgb(0 0 0 / .4)` | `rgb(0 0 0 / .15)` |
| `--stream-swatch-other` (panel swatch for "Everything else") | `#8a867e` | `#8a867e` |
| ink (not a new property: the existing `--color-base-content`, panel row names and counts, guide, ring) | `#f1ede4` | `#1a1820` |

Rules: `.stream-layer { transition: opacity 150ms; }`; `.stream-chart { cursor: crosshair; touch-action: pan-y; }` (a vertical swipe still scrolls the page, a horizontal drag scrubs); `.stream-chart:focus-visible { outline: 2px solid var(--stream-accent); outline-offset: 4px; }`; the panel: absolute, `min-width: 260px`, `padding: .6rem .75rem`, `border: 1px solid var(--stream-line)`, `border-radius: 4px`, `background: var(--stream-panel-bg)`, `box-shadow: 0 4px 16px var(--stream-panel-shadow)`, `font-size: var(--text-body-sm)`, `line-height: 1.45`, `font-family: var(--font-mono)`, row text colour `var(--color-base-content)`; header `font-size: var(--text-label-sm)`, colour `--stream-muted`; row grid `12px 1fr auto` gap `10px`; swatch 12x12 radius 2px; count in tabular numerals; a row is weight 400 at opacity `.78`, `.is-hovered` weight 700 at opacity 1; panel offset `translateX(18px)` from the column centre, or `translateX(calc(-100% - 18px))` when `panelModel(...).side` is `'left'`; top aligned with the plot band's top. Reduced motion: inside the existing `@media (prefers-reduced-motion: reduce)` block (heatmap.css:626) `.stream-layer` joins the `transition-duration: 0ms` selector list.

**Layer rules**: the other layers drop to opacity `0.25` while one is hovered; the hovered layer keeps opacity `1`; with a week shown but no layer under the pointer (the key handler or a pointer in a gap) no layer is dimmed. "Everything else" is a hover target and a panel row like the others.

**Keyboard model**: rank is volume order (0 = largest), the stack puts the largest in the middle, so ArrowUp / ArrowDown move by **stack position**, not by rank: `position` indexes `streamPositions(order)` (top of the stack first, "Everything else" last, so ArrowDown from the bottom artist reaches "Everything else"). `showWeek` receives the id at `positions[position]`.

**Source of the values**: reference section 2 of the v6 design handoff (`design/reference-v6-notes.md` in the v6 SDD workspace, an untracked file). The panel and chart values in the CSS and DOM tables above are copied verbatim from it; the pixel-length values are converted by `STEP / 27` (the panel's CSS lengths in `rem`/`px` are used as written; only SVG lengths are converted) and the font sizes are the page's own, as stated (ruling SP-F9). No task needs access to that file.

---

## Task list

Every task: `Wave` is the earliest wave it can start; `After` lists tasks whose code it builds on (their landing must be in the BASE; where `After` names a task only for file serialisation, it says so); `Mode` is `code` (parallel code phase in a scratch worktree, then a landing) or `serial`. Two tasks in the same wave never touch the same file.

### Task 1: Weekly artist aggregation (data)

**Wave:** 1 | **After:** none | **Mode:** code

**Files:**
- Modify: `scrobblescope/plays.py` (next to `aggregate_daily_counts`, lines 167-183)
- Test: `tests/test_plays.py` (extend the daily-counts area; no new module)

**Interfaces:**
- Consumes: `normalize_name(artist, album)` from `scrobblescope/domain.py:7`; the play objects `aggregate_daily_counts` already reads.
- Produces: `aggregate_weekly_artist_counts(plays, from_date, to_date, top_n=10) -> dict` with the payload shape in Interfaces.

- [x] **Step 1: Write the failing cases** in `tests/test_plays.py`, parametrized:
  - week boundaries follow the Monday grid: a Wednesday `from_date` gives `weeks[0]` equal to the previous Monday and the first column holds only plays from `from_date` on; a `to_date` mid-week gives a partial last column; `len(weeks)` equals `(from_date.weekday() + days - 1) // 7 + 1`.
  - grouping and ranking: two spellings of one artist (case or punctuation) become one layer named by the first spelling seen; artists ordered by window total descending, a tie broken by normalised key; fewer than `top_n` artists gives a shorter `artists` list.
  - `other`: artists beyond `top_n`, plays with an empty artist and plays with a punctuation-only artist (`"!!!"`, key `""`) land in `other`; plays outside `[from_date, to_date]` are ignored.
  - the sum invariant: for a mixed input, each week's artist counts plus `other` equals the matching sum taken from `aggregate_daily_counts` over the same days (the test builds the expected figure from the daily function so the two cannot drift).
- [x] **Step 2: Run red.** Run `pytest -q tests/test_plays.py`. Expected: FAIL with `ImportError` / `AttributeError` for the missing name. Quote the last line.
- [x] **Step 3: Implement** `aggregate_weekly_artist_counts` (standard library only). Use `normalize_name(artist, "")[0]` as the artist key after confirming in `domain.py` that an empty album returns the artist key unchanged; if it does not, stop and return NEEDS_CONTEXT. Report the exact call used.
- [x] **Step 4: Run green.** `pytest -q tests/test_plays.py` passes. Quote the last line.
- [x] **Step 5: Gates and commit.** Stage `scrobblescope/plays.py` and `tests/test_plays.py` by name. The landing commits with the subject `feat(plays): Aggregate weekly top-artist counts for the streamgraph` after the Gates block (no frontend gate: no `static/` or `templates/` change).

### Task 2: JS pure layout functions

**Wave:** 1 | **After:** none | **Mode:** code

**Files:**
- Modify: `static/js/heatmap.js` (new functions and constants near the other pure helpers, before the DOM sections; the test hooks object at line 1901)
- Test: `tests/frontend/test_heatmap_pure_functions.py` (same module, parametrized, `js_page` fixture)

**Interfaces:**
- Consumes: `rocketColor(t)` (heatmap.js:120), the grid constants `CELL_SIZE`, `STEP`, `LEFT_PAD` (lines 27-30).
- Produces: `streamOrder`, `streamBaseline`, `stackLayers`, `streamScale`, `smoothPath`, `layerColour`, and the constants `STREAM_PEAK`, `STREAM_BAND`, `STREAM_LABEL_H`, exactly as in Interfaces, all added to `window.__scrobbleHeatmapTestHooks`. No DOM access.

- [x] **Step 1: Write the failing cases** in `tests/frontend/test_heatmap_pure_functions.py`:
  - `streamOrder`: ten volumes put the biggest at the middle position and ranks 1 and 2 on opposite sides of it; an odd and an even count; one layer; ties keep a stable order.
  - `streamBaseline` / `stackLayers` / `streamScale`: one hand-computed example (two layers, three weeks) matches the reference formula `g[t] = g[t-1] - q / (n + 1)` with `q = sum((n - i) * (L[i][t] - L[i][t-1]))`; the stacked midline averages 0; a constant-height stream stays flat; each week's stack height equals `total * scale`; an all-zero week has zero height; `streamScale` of all zeros is `0`.
  - `smoothPath`: the path starts at the first top point, passes through every top and bottom point, closes, and a single point or all-zero input does not throw.
  - `layerColour`: dark rank 0 equals `rocketColor(.95)`, rank 9 equals `rocketColor(.32)`; light rank 0 equals `rocketColor(.83)`; light ranks 0..9 are ten distinct colours.
- [x] **Step 2: Run red.** `pytest -q tests/frontend/test_heatmap_pure_functions.py`. Expected: FAIL, the hooks are undefined. Quote the failing lines.
- [x] **Step 3: Implement** the functions and constants; expose them in the hooks object.
- [x] **Step 4: Run green.** Same command passes. Quote the last line.
- [x] **Step 5: Contrast report (U6).** Compute the WCAG ratio (use `_contrast_ratio` from `scripts/dev/_frontend_gate_colour.py:137` in a throwaway script) of all ten `layerColour` values against the dark frame `#1f1b28` and the light frame `#f0ebe0`, and of the two "Everything else" fills (`#3a3347`, `#ddd5c5`) against the same frames; report min and max per theme in the task report. A pair under 3:1 is raised (NEEDS_CONTEXT with the pair), not tuned.
- [x] **Step 6: Firefox probe.** The probe loads `static/js/heatmap.js` with `window.__scrobbleHeatmapTestMode` set in Firefox and evaluates one hand-computed `streamOrder`, `stackLayers` and `layerColour` case through the hooks; quote the output. (The pure module in `tests/frontend/` is Chromium only.)
- [x] **Step 7: Gate and commit.** The task changes `static/`, so run the frontend gate (Gates block); it is expected green and unchanged. Stage by name; the landing commits with the subject `feat(heatmap): Add pure layout functions for the streamgraph`.

### Task 3: Job wiring and defensive copy

**Wave:** 2 | **After:** Task 1 | **Mode:** code

**Files:**
- Modify: `scrobblescope/heatmap.py` (after the `aggregate_daily_counts` call at line 112; results at lines 130-142)
- Modify: `scrobblescope/jobs.py` (`_context_view`, lines 518-533)
- Test: `tests/test_heatmap.py` (the stored-result test near line 225), `tests/test_jobs.py` (the F-B18-8 defensive-copy test near line 508)

**Interfaces:**
- Consumes: `aggregate_weekly_artist_counts` (Task 1).
- Produces: the job result key `weekly_artists` (payload in Interfaces) stored next to `daily_counts`; `_context_view` returns a deep-enough copy of it.

- [x] **Step 1: Write the failing cases.** In `tests/test_heatmap.py`: the stored result carries `weekly_artists` whose `weeks` align with the daily window and whose week totals equal the daily totals (the S1 invariant, end to end through the job with a fake fetch); the zero-scrobble guard still fails the job before storing anything. In `tests/test_jobs.py`: mutating `weeks`, an artist `counts` entry, an artist `name` and `other` in a returned view leaves the stored values unchanged.
- [x] **Step 2: Run red.** `pytest -q tests/test_heatmap.py tests/test_jobs.py`. Expected: the new heatmap case fails on the missing key and the jobs case fails because the view shares the stored lists. Quote the failing lines.
- [x] **Step 3: Implement.** `heatmap.py` calls `aggregate_weekly_artist_counts(fetch.plays, from_date, to_date)` right after `aggregate_daily_counts` and stores it under `weekly_artists` in the dict passed to `jobs.succeed`. `_context_view` copies it the way it copies `daily_counts`: the outer dict, the `weeks`, `other` and `artists` lists, and each artist dict with its `counts` list.
- [x] **Step 4: Run green.** `pytest -q tests/test_heatmap.py tests/test_jobs.py tests/test_lastfm_job_results.py` passes. Quote the last line.
- [x] **Step 5: Gates and commit.** Stage by name. Subject: `feat(heatmap): Store the weekly artist counts with the job result`. No frontend gate (no `static/` or `templates/` change).

### Task 4: Timeline surfaces and frame-scoped empty cells

**Wave:** 2 | **After:** Task 2 (file serialisation on `static/js/heatmap.js` only; no code dependence) | **Mode:** code

**Files:**
- Modify: `static/css/heatmap.css` (every custom property in Interfaces, CSS, declared on `.heatmap-frame` (line 355) for light and on `[data-theme="dark"] .heatmap-frame` for dark; no rule yet uses the `--stream-*` ones beyond the frame itself)
- Modify: `static/js/heatmap.js` (`zeroFill`, line 148; `resolvedColour`, line 334)
- Modify: `scripts/dev/_frontend_gate_theme.py` (`check_heatmap_zero_cells_follow_theme`, line 696, expected value read at lines 738-739; the new check `timeline surfaces are page-scoped` is added beside it)
- Modify: `scripts/dev/frontend_gate.py` (import and register the new check in `CHECKS`, group `THEME_MOTION`, viewport DESKTOP)

**Interfaces:**
- Consumes: nothing from other tasks (the job fixture is a plain heatmap job built as `check_heatmap_zero_cells_follow_theme` builds it, `_frontend_gate_theme.py:700-720`; no stream payload yet).
- Produces: the frame-scoped custom properties of Interfaces, CSS; `resolvedColour(token, scope?)` (optional scope element, default `document.body`); `zeroFill()` reading `--heatmap-empty` from `#heatmap-result-frame`.

Scoping (SP-F6, owner ruling U18): the timeline values are declared on `.heatmap-frame` only, so the global dark token and every other page stay `#262230`. `zeroFill()` reads `--heatmap-empty` from the frame element (`getComputedStyle` of a hidden element still resolves custom properties) instead of `document.documentElement`; `updateZeroFills()` (line 1817) keeps working through `zeroFill()`. `resolvedColour` gains the optional scope so later tasks resolve layer, "Everything else" and export-background reads against the frame. The page background outside the frame is not touched.

- [x] **Step 1: Update the existing theme check and write the new gate check.** `check_heatmap_zero_cells_follow_theme` reads its expected value from `#heatmap-result-frame` (the resolved `--heatmap-empty` on the frame), not `document.documentElement`. The new check `timeline surfaces are page-scoped` (DESKTOP, dark and light): a zero-count cell's `fill` equals the frame's resolved `--heatmap-empty` (`#2e2939` dark, `#c8bfad` light); `getComputedStyle(document.documentElement).getPropertyValue('--heatmap-empty')` is still `#262230` in dark (the global token is untouched); the frame's background colour equals its resolved `--heatmap-surface` (`#1f1b28` dark, `#f0ebe0` light). Register it in `frontend_gate.py`.
- [x] **Step 2: Run red.** Run the frontend gate (Gates block). Expected: FAIL on the new check and on the updated theme check (the empty cell is `#262230` where `#2e2939` is expected). Quote the failing check names and one failing line.
- [x] **Step 3: Implement** the custom properties, the `zeroFill` scope change and the `resolvedColour` scope parameter.
- [x] **Step 4: Run green.** The frontend gate passes; quote the last line and both check names in its output.
- [x] **Step 5: Contrast report.** From the declared custom-property values, report min and max ratios (both themes, via `_contrast_ratio`, `scripts/dev/_frontend_gate_colour.py:137`) for: `--stream-muted` text on the frame and on `--stream-panel-bg`, ink (`--color-base-content`) on `--stream-panel-bg`, `--stream-accent` against the frame, `--stream-swatch-other` against `--stream-panel-bg`, `--stream-line` against the frame, the empty cell against the frame. Text pairs 4.5:1, non-text 3:1. A failing pair is raised (S10). (Task 7 reports the rendered panel pairs and Task 8 the rendered focus outline.)
- [x] **Step 6: Firefox probe.** The dark and light empty-cell assertions and the untouched global token, in Firefox. Quote the output.
- [x] **Step 7: Commit.** Stage by name; the landing runs the frontend gate. Subject: `feat(heatmap): Scope the timeline surfaces and empty cells to the heatmap frame`.

### Task 5: Draw the streamgraph

**Wave:** 3 | **After:** Task 4, Task 2 | **Mode:** code

**Files:**
- Modify: `static/js/heatmap.js` (`renderHeatmapDesktop`, line 1239; new `drawStream`, `streamPayloadValid`; the hooks object, line 1901)
- Modify: `static/css/heatmap.css` (`.stream-layer`, `.stream-chart` and `#heatmap-grid { position: relative }` from Interfaces, CSS)
- Create: `scripts/dev/_frontend_gate_stream.py` (`seed_stream_job` and the two checks below)
- Modify: `scripts/dev/frontend_gate.py` (import and register the two checks in `CHECKS`, group `THEME_MOTION`, viewports as stated)
- Test: `tests/frontend/test_heatmap_pure_functions.py` (the `streamPayloadValid` cases)

**Interfaces:**
- Consumes: Task 2's pure functions and constants; Task 4's `resolvedColour(token, scope)` and frame-scoped custom properties; the payload shape (the job fixture is built directly with `jobs.succeed`, so this task does not need Task 3).
- Produces: `streamPayloadValid(payload, numCols) -> boolean` (in the test seam); the DOM and CSS names `svg#stream-chart`, `text.stream-section-label`, `line.stream-gridline`, `path.stream-layer[data-rank]`; `drawStream`; `seed_stream_job` as defined in Interfaces ("Existing names the stream tasks use"), reused by Tasks 6-9 and by their Firefox probes.

Colour handling (SP-F4): every stream paint is a resolved attribute so the saved image needs no stylesheet: layer `fill` from `layerColour` (an `rgb()` string) for the current theme, "Everything else" `fill` from `--stream-other` resolved on the frame, gridline `stroke` from `--stream-line`, section-label `fill` (from `--stream-muted`) and `font-family` (`LABEL_FONT_STACK`, line 53). Task 6 rewrites them on a theme change. Mobile layout and an invalid or absent payload draw nothing.

- [ ] **Step 1: Write the failing JS cases** (`streamPayloadValid`): a valid payload; each invalid shape in the validity rule (wrong `weeks` length, an artist `counts` of the wrong length, a negative or non-numeric count, `other` missing, 11 artists, `null`, a string); zero artists is valid. Run `pytest -q tests/frontend/test_heatmap_pure_functions.py`; expected FAIL (hook undefined).
- [ ] **Step 2: Write the failing gate checks** in `scripts/dev/_frontend_gate_stream.py`, registered in `CHECKS`, each returning failure strings like its neighbours:
  - `stream aligns with the grid columns` (DESKTOP, and a second viewport width set inside the check): with `seed_stream_job()`, `svg#stream-chart` exists, contains 11 `path.stream-layer`, its `viewBox` width equals the grid SVG's, and for every week `t` the on-screen x of entry `t` of `data-columns` (viewBox x scaled by the SVG's rendered width) equals the on-screen centre of the heatmap column `t` (the grid's `.heatmap-cell` rects, x + `CELL_SIZE / 2`, scaled the same way) within 1px at both widths.
  - `stream absent without payload or on mobile` (DESKTOP and MOBILE): control first, desktop with `seed_stream_job()` has exactly one `#stream-chart` (so the check is red against the unchanged code); with `seed_stream_job(payload=False)` none exists; at MOBILE with a payload none exists either; resizing across 860px re-renders without a stray or duplicate stream.
- [ ] **Step 3: Run red.** Run the JS cases and the frontend gate; expected FAIL on the new cases and both new checks (the control finds no stream). Quote the failing names.
- [ ] **Step 4: Implement** `streamPayloadValid`; `drawStream` (called at the end of `renderHeatmapDesktop` when the payload is valid and the scale is above 0; layers bottom to top: "Everything else" then the artists in `streamOrder`, coloured through `layerColour`; section label; one gridline per month start; no in-stream labels, no legend; it stores the module-level state named in Interfaces, DOM functions); `seed_stream_job`; and the CSS. The stream is also drawn after `rerenderKeepingFocus()` re-renders (it goes through `renderHeatmap`).
- [ ] **Step 5: Run green.** `pytest -q tests/frontend/test_heatmap_pure_functions.py` and the frontend gate pass; quote both last lines and the new check names in the gate output.
- [ ] **Step 6: Firefox probe.** The aligned and absent assertions in Firefox, built with `seed_stream_job`. Take a screenshot in both themes for the report (viewed, not committed). Quote the output.
- [ ] **Step 7: Commit.** Stage by name; the task changes `static/` and `scripts/dev/_frontend_gate*`, so the landing runs the frontend gate. Subject: `feat(heatmap): Draw the top-artists streamgraph under the grid`.

### Task 6: Recolour the streamgraph on a theme change

**Wave:** 4 | **After:** Task 5 | **Mode:** code

**Files:**
- Modify: `static/js/heatmap.js` (new `recolourStream`; `initThemeObserver`, line 1797, calls it beside `updateZeroFills()`)
- Modify: `scripts/dev/_frontend_gate_stream.py` (add the colour check)
- Modify: `scripts/dev/frontend_gate.py` (register it in `CHECKS`, group `THEME_MOTION`, viewport DESKTOP)

**Interfaces:**
- Consumes: Task 5's DOM and module-level state, `layerColour` (Task 2), `resolvedColour(token, scope)` (Task 4), `seed_stream_job` (Task 5).
- Produces: `recolourStream()` (DOM, not in the test seam).

Behaviour: on a `data-theme` change `recolourStream()` rewrites the layer `fill`, "Everything else" `fill`, gridline `stroke` and section-label `fill` attributes for the new theme, without a re-render.

- [ ] **Step 1: Write the failing gate check** `stream colours follow theme and meet contrast` (DESKTOP, dark and light): layer 0's `fill` equals `layerColour(0, theme)` in both themes and changes when the theme is switched without a re-render; "Everything else" `fill` equals `#3a3347` / `#ddd5c5`; gridline `stroke` equals the resolved `--stream-line`; every layer fill against the frame, and the section label against the frame, clears the floor (3:1 non-text, 4.5:1 text), via `_contrast_ratio`, min and max logged. A failing pair is raised (S10); the check does not tune colours. Register it.
- [ ] **Step 2: Run red.** Run the frontend gate; expected FAIL: after the theme switch the fills still carry the old theme's values. Quote the failing check name and line.
- [ ] **Step 3: Implement** `recolourStream` and its call.
- [ ] **Step 4: Run green.** The frontend gate passes; quote the last line and the check name.
- [ ] **Step 5: Contrast report.** Quote the min and max layer-vs-frame and label-vs-frame ratios per theme from the check's log into the task report.
- [ ] **Step 6: Firefox probe.** Recolour in both themes (switch the theme with no reload, read the layer 0 and "Everything else" fills) plus a screenshot each, viewed and not committed. Quote the output.
- [ ] **Step 7: Commit.** Stage by name; the landing runs the frontend gate. Subject: `feat(heatmap): Recolour the streamgraph when the theme changes`.

### Task 7: Hover, scrubber panel and column ring

**Wave:** 5 | **After:** Task 6 | **Mode:** code

**Files:**
- Modify: `static/js/heatmap.js` (new `weekFromX`, `layerAtY`, `panelModel`, `showWeek`, `clearWeek`, Pointer Events wiring; the hooks object)
- Modify: `static/css/heatmap.css` (panel, ring, guide, hover and reduced-motion rules from Interfaces, CSS)
- Modify: `scripts/dev/_frontend_gate_stream.py` (add the hover checks)
- Modify: `scripts/dev/frontend_gate.py` (register them in `CHECKS`, group `THEME_MOTION`)
- Test: `tests/frontend/test_heatmap_pure_functions.py`

**Interfaces:**
- Consumes: Task 5's DOM (`svg#stream-chart`, `path.stream-layer[data-rank]`, `data-columns`) and module-level state (the stacked layers, the validated payload), `streamPayloadValid`; `seed_stream_job`.
- Produces: `weekFromX`, `layerAtY`, `panelModel` (test seam); `showWeek(week, hoverId)` / `clearWeek()` (DOM, used by Task 8); `rect.stream-column-ring`, `line.stream-guide`, `div#stream-panel`.

Behaviour (README row 7). Pointer Events on `#stream-chart` (`pointermove`, `pointerdown`, `pointerleave`, `pointercancel`) map the pointer x to a week with `weekFromX` and the y to a layer id with `layerAtY`; mouse hover and touch drag use the same path. `showWeek` sets every other layer to opacity `0.25` (150ms transition), shows `line.stream-guide` at the column centre, appends one `rect.stream-column-ring` to the grid SVG around that week's seven-row column, and fills and positions `#stream-panel` from `panelModel` (rows are listed top of the stack first, so "Everything else" is last; the hovered row is `is-hovered`; the panel sits right of the column and flips left when `side` is `'left'`, that is past week 34). `clearWeek()` removes all of it; pointer leave and cancel call it. A re-render (`renderHeatmap`, including a resize across the layout width) clears the shown week: panel, ring, guide and dimming are gone, no stale ring remains in the new grid SVG, and the next pointer move shows it again.

- [ ] **Step 1: Write the failing JS cases**: `weekFromX` clamps at both ends and picks the nearest week on a midpoint; `layerAtY` returns the layer inside a band, the upper layer on a shared boundary, `null` outside; `panelModel`: rows omit zero artist counts and keep "Everything else" last, the header string with thousands separators and the `1 scrobble` form, `side` is `'right'` at week 34 and `'left'` at week 35, `hovered` marks only the hovered id. Run `pytest -q tests/frontend/test_heatmap_pure_functions.py`; expected FAIL (hooks undefined).
- [ ] **Step 2: Write the failing gate checks** (`stream hover shows panel and ring`, DESKTOP; `stream touch drag scrubs`, Chromium only by design, skipped on other engines as `check_heatmap_touch_swipe_scrolls_and_tap_shows_tooltip` does at `_frontend_gate_heatmap_access.py:1488`, on a coarse-pointer profile; `stream reduced motion`, DESKTOP): moving to a point inside a layer sets that layer's siblings to opacity `0.25`, shows the panel with one `is-hovered` row, places `rect.stream-column-ring` at the matching heatmap column, and leaving removes all three; with a week shown, a resize that re-renders leaves no `rect.stream-column-ring` and a hidden panel; a touch-type drag across weeks updates the panel header; with `prefers-reduced-motion: reduce` emulated, the computed `transition-duration` of `.stream-layer` is `0s`; the panel flips left past week 34 (compare the panel's bounding box with the column centre at week 30 and week 40). Register them.
- [ ] **Step 3: Run red.** Run the JS cases and the frontend gate; expected FAIL on the new cases and checks. Quote the failing names.
- [ ] **Step 4: Implement** the helpers, `showWeek` / `clearWeek`, the pointer wiring and the CSS, with the re-render rule above.
- [ ] **Step 5: Run green.** The JS cases and the frontend gate pass; quote both last lines.
- [ ] **Step 6: Contrast report.** Rendered panel text (ink) on `--stream-panel-bg`, the header on the panel, the swatch of "Everything else" and the guide line and ring against the frame, both themes, min and max (4.5:1 text, 3:1 non-text; a failing pair is raised).
- [ ] **Step 7: Firefox probe.** Hover (mouse) assertions, the panel flip, reduced motion via `emulate_media`, the re-render clearing; touch drag is Chromium only (state this in the report). Quote the output.
- [ ] **Step 8: Commit.** Stage by name; the landing runs the frontend gate. Subject: `feat(heatmap): Scrub the streamgraph with a panel and column ring`.

### Task 8: Keyboard access

**Wave:** 6 | **After:** Task 7 | **Mode:** code

**Files:**
- Modify: `static/js/heatmap.js` (new `streamKeyTarget`, `streamStartTarget`, `streamPositions`, the key and focus handlers; the hooks object)
- Modify: `static/css/heatmap.css` (the `.stream-chart:focus-visible` outline rule)
- Modify: `scripts/dev/_frontend_gate_stream.py`
- Modify: `scripts/dev/frontend_gate.py` (register the check in `CHECKS`, group `THEME_MOTION`)
- Test: `tests/frontend/test_heatmap_pure_functions.py`

**Interfaces:**
- Consumes: `showWeek`, `clearWeek`, `panelModel` (Task 7), `streamOrder` (Task 2), the DOM in Interfaces, the module-level state of Task 5.
- Produces: `streamKeyTarget`, `streamStartTarget`, `streamPositions` (test seam); `svg#stream-chart` with `tabindex="0"`, `role="application"`, `aria-label` "Top artists by week. Left and right arrows move between weeks, up and down move between artists."

Behaviour: the stream is one tab stop. On focus with nothing selected the state is `streamStartTarget(dims)` (week 26, or the last week when there are fewer; the top layer) and `showWeek` runs with `positions[position]`. `ArrowLeft` / `ArrowRight` / `ArrowUp` / `ArrowDown` / `Home` / `End` call `streamKeyTarget` and then `showWeek`; edges clamp, they do not wrap; ArrowUp / ArrowDown move by stack position (see Keyboard model) and reach "Everything else". `blur` calls `clearWeek()`. The handler calls `preventDefault` only for the handled keys and never traps Tab. The panel (`aria-live="polite"`) is the announcement. A re-render replaces the chart, and `rerenderKeepingFocus` (heatmap.js:1862) restores focus only to a `.heatmap-cell`, so a stream that had focus is blurred by a resize re-render; that is accepted: the shown week is cleared (Task 7's rule), focus returns to the page, and the user tabs back in. The plan does not extend `rerenderKeepingFocus`.

- [ ] **Step 1: Write the failing JS cases**: `streamKeyTarget` for every key, both edges in each axis, a one-week payload (`weeks: 1`), and the start-to-bottom walk reaching `layers - 1`; `streamStartTarget` with 53 weeks (26) and 10 weeks (9); `streamPositions` for an `order` of five ranks (top first, `'other'` last).
- [ ] **Step 2: Write the failing gate check** (`stream is one keyboard tab stop`, DESKTOP): Tab reaches the grid's own cell stop, then the stream exactly once (a further Tab leaves it); on focus the panel appears; ArrowRight changes the panel header and moves the ring to the next column; ArrowDown from the bottom artist reaches "Everything else" (its row `is-hovered`); Home / End jump; blur clears ring and panel; a resize that re-renders while the stream has focus leaves no ring, a hidden panel and focus off the removed chart (blur accepted); the grid's own arrow handling (`check_heatmap_cells_are_keyboard_accessible`, `_frontend_gate_heatmap_access.py:609`) still passes unchanged; the focus outline is 2px with offset 4px and clears 3:1 against the frame in both themes (min and max logged). Register it.
- [ ] **Step 3: Run red.** Run the JS cases and the frontend gate; expected FAIL. Quote the failing names.
- [ ] **Step 4: Implement** the helpers and the handlers.
- [ ] **Step 5: Run green.** Both pass; quote the last lines.
- [ ] **Step 6: Firefox probe.** The tab-stop, arrow, Home / End, blur and resize-blur assertions in Firefox (Firefox skips links by default; the stream has `tabindex="0"`, so it should be reached; report any difference). Quote the output.
- [ ] **Step 7: Commit.** Stage by name; the landing runs the frontend gate. Subject: `feat(heatmap): Add keyboard access to the streamgraph`.

### Task 9: Save image includes the streamgraph

**Wave:** 7 | **After:** Task 8 (and Tasks 4 and 5; the wave comes from `heatmap.js`, `_frontend_gate_stream.py` and `frontend_gate.py` being edited by Tasks 4-8) | **Mode:** code

**Files:**
- Modify: `static/js/heatmap.js` (`drawHeatmapImage`, line 596; `gridAsImage`, line 353)
- Modify: `scripts/dev/_frontend_gate_stream.py`
- Modify: `scripts/dev/frontend_gate.py` (register the check in `CHECKS`, group `THEME_MOTION`)

**Interfaces:**
- Consumes: `svg#stream-chart` with its resolved fills (Task 5), `resolvedColour(token, scope)` (Task 4), `clearWeek()` (Task 7), `seed_stream_job` (Task 5).
- Produces: an export that carries the stream; no new public name.

Behaviour (SP-F4): `drawHeatmapImage` serialises the stream SVG the way `gridAsImage` serialises the grid (a clone; the stream's `font-family` and `fill` are already attributes, but the clone sets `font-family` to `monospace` on `.stream-section-label` like the month labels, line 363-368) and draws it below the grid, growing the canvas height by the stream's rendered height plus the section gap. The export shows the resting state: the clone drops `line.stream-guide`, sets every `path.stream-layer` `opacity` to `1`, and the grid clone drops `rect.stream-column-ring`; the panel is not part of the SVG. The canvas background stays `resolvedColour('--heatmap-surface')` resolved against the frame (Task 4), so the saved image takes the timeline surface. When no stream exists (mobile layout or no payload) the export is unchanged. The fallback-font note at heatmap.js:560-575 applies.

- [ ] **Step 1: Write the failing gate check** (`stream is in the saved image`, DESKTOP, dark and light): save for real (`page.expect_download`, as `check_heatmap_export_header_matches_page`, `_frontend_gate_theme.py:817`), decode the JPEG in the page (the `Image` + canvas pattern at `_frontend_gate_results.py:790-815`), and assert (a) the image is taller than the export of `seed_stream_job(payload=False)` by about the stream's rendered height times the export scale (within 4%), (b) the pixel at the stream's tallest week, on the centre line, matches the resolved fill of the layer there (`layerColour` for that rank) per channel within 12 (JPEG tolerance) in both themes, (c) a pixel inside the "Everything else" band at its widest point matches `--stream-other` within 12, and (d) the section label is present in the serialised markup the export draws (the gate reads it through the same record `window.__scrobbleHeatmapDrawnHeader` exposes, extended by this task with a `stream` field `{label, height}`; extend the record in `drawHeatmapImage`, line 596+, and keep the existing fields). Register it.
- [ ] **Step 2: Run red.** Run the frontend gate. Expected: FAIL on the new check (no stream in the saved canvas). Quote the failure.
- [ ] **Step 3: Implement** the export change.
- [ ] **Step 4: Run green.** The frontend gate passes; quote the last line and the new check name.
- [ ] **Step 5: Firefox probe.** Save for real in Firefox, decode the JPEG, and run assertions (a)-(c) there (this is the browser the owner uses; the canvas SVG-image path differs per engine). Quote the output and view the saved image once in each theme (not committed).
- [ ] **Step 6: Commit.** Stage by name; the landing runs the frontend gate. Subject: `feat(heatmap): Include the streamgraph in Save image`.

### Task 10: Docs after code

**Wave:** 8 | **After:** Tasks 1, 3, 4, 5, 6, 7, 8, 9 | **Mode:** serial

**Files:**
- Modify: `README.md` ("Scrobble Heatmap" features list near line 147; "The heatmap is a hand-built SVG" near line 443; module table row for `plays.py` / `heatmap.py` near line 363)
- Modify: `DESIGN.md` ("Heatmap & Status")
- Check, edit only if they name the changed things: `docs/architecture/documentation-tooling.md` (lists the frontend gate modules, line 120 and 533) and `docs/agents/PLAYBOOK.md`

**Interfaces:**
- Consumes: the landed behaviour of Tasks 1-9.
- Produces: no behaviour change.

- [ ] **Step 1: Re-measure** the facts the docs will state (line numbers, module names, the gate module `scripts/dev/_frontend_gate_stream.py`) against the final head with `grep`; do not copy numbers from this plan.
- [ ] **Step 2: README.** Features list: add the top-artists streamgraph (weekly top 10 under the grid on desktop, scrubber panel, keyboard, touch, included in Save image, desktop layout only). Fix any line the change makes untrue (for example the "Save the heatmap as a JPEG" bullet if it implies the grid alone). "Hand-built SVG": one short paragraph that the streamgraph is also hand-built SVG with no library, aligned to the same Monday-first week columns. Module table: `plays.py` / `heatmap.py` mention the weekly artist aggregation.
- [ ] **Step 3: DESIGN.md** "Heatmap & Status": add the timeline surfaces (frame-scoped, not the global dark theme) and the stream layer ramp with the light-theme 0.83 rescale, only if the document names the page's parts (it does under that heading).
- [ ] **Step 4: Gate-module mentions.** If `docs/architecture/documentation-tooling.md` lists the frontend gate modules by name, add `_frontend_gate_stream`; if it enumerates them in a diagram (line 120), follow the existing pattern.
- [ ] **Step 5: Last updated.** Update `Last updated:` in every doc the commit changes. Point-in-time records (`docs/history/`, `docs/logarchive/`, `docs/superpowers/`, dated Section 4 entries) are not edited, except the landing's own Section 4 entry as the stacked workspace's constraints require.
- [ ] **Step 6: Gates and commit.** Docsync check and pre-commit pass (landing gates). Subject: `docs: Describe the top-artists streamgraph`.

## Dispatch

| Wave | Tasks | Mode | Parallel agents |
|---|---|---|---|
| 1 | Task 1 (data), Task 2 (JS pure) | code | 2 |
| 2 | Task 3 (job wiring), Task 4 (timeline surfaces, frame-scoped empty cells) | code | 2 |
| 3 | Task 5 (draw the streamgraph, gate module) | code | 1 |
| 4 | Task 6 (recolour on theme change) | code | 1 |
| 5 | Task 7 (hover, panel, ring) | code | 1 |
| 6 | Task 8 (keyboard) | code | 1 |
| 7 | Task 9 (Save image) | code | 1 |
| 8 | Task 10 (docs) | serial | 1 |

Peak parallel agents: 2 (waves 1 and 2). Each parallel agent also spawns one nested gate-runner at a time, so the peak of live agents is 4. Tasks 4 to 9 all edit `static/js/heatmap.js` (Task 4 only for `zeroFill` / `resolvedColour`) or `scripts/dev/frontend_gate.py`, and Tasks 5 to 9 also edit `scripts/dev/_frontend_gate_stream.py`, so they are one chain, one wave each; patches from one wave must apply to the BASE the next wave starts from. Tasks 4, 5, 6, 7, 8 and 9 each touch `scripts/dev/frontend_gate.py` (the `CHECKS` registration, ruling SP-F8) and are serial with each other by wave; only Task 4 touches `scripts/dev/_frontend_gate_theme.py`. Browser gates (the frontend gate and the Firefox probes) go through `with_browser_lock.py`, so two live agents queue for the browser, they do not collide.

Landing order (one commit per task, the controller or a land-mode implementer applies each patch in `C:/ssw/u7`): 1, 2, 3, 4, 5, 6, 7, 8, 9, 10. Within a wave the order is numeric, and a later patch in the same wave is re-checked with `git apply --check --index` against the HEAD the earlier landing left. Each landing runs the commit procedure of the stacked branch's constraints (the three `suite-*` gates, `doc_state_sync.py --fix --test-count N`, `pre-commit`, `docsync-check`), and a landing of a task that changes `templates/`, `static/` or `scripts/dev/_frontend_gate*` also runs `frontend-gate`; the final head runs every gate, including `results-behavior`.

### Gates

Run from the worktree root. Start the three `suite-*` shards at once in the background and wait for all three. `PY` below is the absolute path shown.

```gates
- name: suite-docsync
  run: "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider tests/test_docsync_*.py
  pass: exit 0
  quote: last line
  when: every commit

- name: suite-subdirs
  run: "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider tests/scripts tests/frontend tests/services --ignore=tests/scripts/dev/test_mutation_test.py
  pass: exit 0
  quote: last line
  when: every commit

- name: suite-core
  run: "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider tests --ignore-glob=tests/test_docsync_* --ignore=tests/scripts --ignore=tests/frontend --ignore=tests/services
  pass: exit 0
  quote: last line
  when: every commit

- name: pre-commit
  run: "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe" run --all-files
  pass: exit 0
  quote: last line
  expected: "ERROR WT003" ; "WARNING WT010" ; "WARNING WT006"
  when: every commit

- name: docsync-check
  run: "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
  pass: exit 0
  quote: last line
  expected: "WARNING: Root BATCH file detected: BATCH23_DEFINITION.md" ; "WARNING DOC024" (each with its Remediation line)
  when: every commit

- name: frontend-gate
  run: "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" C:/ssw/tools/with_browser_lock.py "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/frontend_gate.py
  pass: exit 0
  quote: last line
  expected: "[ERROR] Failed to fetch Spotify token" ; "loaded no faces from the kit"
  when: a commit that changes templates/, static/ or scripts/dev/_frontend_gate*; and the final head

- name: results-behavior
  run: "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" C:/ssw/tools/with_browser_lock.py "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/results_behavior_tests.py
  pass: exit 0
  quote: last line
  when: a commit that changes templates/results.html, static/js/results.js or scripts/dev/results_behavior_tests.py; and the final head
```

(The suite shard sizes in the stacked branch differ from the v6 branch's `2972` by the tests this plan adds; the count N comes from the gates at each landing, never from this document.)

## Open items for the owner (raised in the planning report)

Settled, not open: desktop-layout only and the frame-only timeline surfaces (owner ruling U18; a mobile streamgraph is a later PR).

- [ ] Light-theme ramp is rescaled so its top is 0.83 rather than clamped at 0.83, to keep adjacent layers distinct.
- [ ] If a layer colour fails the 3:1 floor against its frame in either theme, Task 2, 4, 6, 7 or 8 raises the pair; the ramp is the owner's and is not changed by an executor.
- [ ] Stream checks run in Chromium only in the frontend gate (the gate's Firefox scope is the static-assets canary); Firefox is covered by a probe per task, not a permanent gate. Widening `BROWSER_SCOPES` is a separate ruling.
