# BATCH19: Heatmap Polish -- Frame, KPIs, Mobile Layout

**Status:** Active (WP-4 committed)
**Branch:** `feat/heatmap`
**Baseline:** 386 tests passing after WP-3 (verified 2026-05-17)

---

## Context

Batch 18 Phase 1 delivered a working end-to-end heatmap. Owner review and
UI analysis identified visual and layout gaps that block the feature from
being demo-ready. This batch resolves those gaps before the `feat/heatmap`
PR is opened to main.

**Scope constraint:** All changes are confined to `heatmap.css`, `heatmap.js`,
`templates/index.html`, `templates/inline/scrobblescope_pinwheel.svg`, and
doc files. No changes to `global.css`, `base.html`, Python modules, or other
pages. The full app palette/font overhaul is explicitly deferred to a
follow-up batch.

**Branch:** `feat/heatmap` continued -- no new branch.

---

## Perf context (measured 2026-05-16)

```
Time elapsed (fetching 103 Last.fm pages): 10.9s   [flounder14, local]
Last.fm: Fetched 103/103 pages
```

`lastfm.py` already uses `limit=200` (max) and concurrent `as_completed`
fetching with `MAX_CONCURRENT_LASTFM=10`. The 10.9s figure is essentially the
rate-limit floor: 103 pages / 10 req/s = 10.3s minimum. The `_GlobalThrottle`
at 10 req/s is the binding constraint. Pushing higher risks 429s from Last.fm
(official limit is 5 req/s averaged; no 429s observed at 10 but margin is
unknown). No further fetch optimization is possible this batch. Documented in
WP-1 and corrected in FINDINGS.md.

---

## 1. Scope and goals

- Correct stale perf documentation across PLAYBOOK, AGENT_NOTES,
  SESSION_CONTEXT, and FINDINGS.md
- Redesign the heatmap result as a self-contained artifact: custom frame,
  headline with accented username, four KPI stats, repositioned legend
- Rename "Album Filtering" pill to "Top Albums"; fix subtitle format
- Fix pinwheel SVG clipping during blade expansion animation
- Implement mobile-optimized vertical heatmap layout (viewports < 768px)

**Out of scope:**
- Global palette/font overhaul (separate batch -- touches every page)
- Dark mode toggle repositioning (deferred by owner)
- HTTP security headers (separate batch)
- Test audit / orchestrator refactor / docstring normalization (separate batch)
- Concurrent user cap reduction (separate batch -- load test data in FINDINGS)
- Last.fm fetch speed (10.9s is the rate-limit floor -- no further headroom)

---

## 2. Work Packages

---

### WP-1: Correct stale perf documentation + update FINDINGS.md

**Goal:** Update all stale perf descriptions to reflect measured reality.
Doc-only WP -- no code changes.

**What is stale and why:**
FINDINGS.md F-B18-11 and the PLAYBOOK/AGENT_NOTES perf notes all describe a
"sequential ~100ms/page" bottleneck from the pre-implementation design.
The actual `lastfm.py` WP-1 implementation is already fully concurrent.
The 10.9s measured time is the rate-limit floor, not a concurrency failure.

**Files:**
- `PLAYBOOK.md` Section 3 -- remove "sequential (~100ms/page)" from perf note;
  replace with: concurrent fetch already implemented, 10.9s measured (rate-limit
  floor at 10 req/s), no further optimization without cache or rate-limit risk
- `AGENT_NOTES.md` -- same correction to "Critical performance bottleneck"
  section; remove optimization options 1 and 2 (already implemented)
- `.claude/SESSION_CONTEXT.md` Section 1 -- update perf note
- `FINDINGS.md` -- F-B18-11: correct "sequential" root cause, add measured
  concurrent data (10.9s, 2026-05-16); update header (381 -> 385 tests,
  Batch 18 Phase 1 complete not "in progress")
- `AGENTS.md` / `HANDOFF_PROMPT.md` -- align no-push commit discipline and
  clarify expected active root batch-definition warnings
- `.gitignore` -- allow `FINDINGS.md` to be tracked as shared cross-agent
  context

**Acceptance criteria:**
- No stale current-state "sequential" or "11-13s" perf assertions remain in
  active/bootstrap docs (`PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`,
  `AGENT_NOTES.md`, `FINDINGS.md`). Historical archives and this definition
  may preserve old wording when describing what was stale.
- FINDINGS.md F-B18-11 accurately describes rate-limit floor as the constraint
- FINDINGS.md header test count and batch status current
- Bootstrap files give one canonical push rule: commit after each WP, do not
  push without explicit owner instruction
- Expected docsync root batch-definition warning is documented as non-blocking
  while a batch is active
- `pre-commit run --all-files` passes
- `python scripts/doc_state_sync.py --check` exits 0

**Net tests:** 0
**Commit:** `docs(batch-19): correct stale heatmap perf docs; update FINDINGS`

---

### WP-2: Heatmap result redesign -- frame, headline, KPIs, legend

**Goal:** Redesign the heatmap result card into a self-contained shareable
artifact. Custom frame surface, headline with accent-colored username, four
KPI stats above the grid, legend repositioned to top-right of the frame.
All changes confined to `heatmap.css`, `heatmap.js`, and `templates/index.html`.

**Design reference:** Owner-provided mocks (dark + light mode).
The frame reads as a designed component, not a Bootstrap card widget.

#### 2a. CSS -- heatmap frame

Replace the Bootstrap `.card.shadow` wrapper on `#heatmap-result` with a
custom `.heatmap-frame` class. Scope warm/dark surface colors as
heatmap-specific CSS variables so the future global rollout is a one-line
change per variable:

```css
/* Heatmap-scoped surface tokens (not global -- full rebrand is a future batch) */
:root {
  --hm-surface-light: #faf8f3;      /* warm cream */
  --hm-surface-dark:  #181520;      /* inky purple-dark */
  --hm-text-muted:    #9a9a9a;      /* label opacity substitute */
}

.heatmap-frame {
  background-color: var(--hm-surface-light);
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.07);
  padding: 1.5rem 1.75rem;
  width: 100%;
  box-sizing: border-box;
}

.dark-mode .heatmap-frame {
  background-color: var(--hm-surface-dark);
  border-color: rgba(255, 255, 255, 0.06);
}
```

#### 2b. CSS -- headline

Outside the frame (above it, flush left relative to the frame):

```css
.heatmap-headline {
  font-size: 1.75rem;
  font-weight: 400;
  color: var(--text-color);
  margin-bottom: 1rem;
  line-height: 1.2;
}

.heatmap-headline-username {
  color: var(--bars-color);
  font-style: italic;
}
```

HTML structure (injected by JS into `#heatmap-result`):
```
<p class="heatmap-headline">
  <span class="heatmap-headline-username">{username}</span>'s last 365 days, day by day.
</p>
<div class="heatmap-frame">
  ... KPI row, legend row, grid ...
</div>
```

Username is set via `textContent` on the span -- no innerHTML (XSS criterion
F-B18-9 maintained).

#### 2c. CSS + JS -- KPI stat row

Four stats above the grid, inside the frame. Monospaced labels, large values.

```css
.heatmap-kpi-row {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.25rem;
}

.heatmap-kpi {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.heatmap-kpi-label {
  font-family: ui-monospace, "Cascadia Code", "Fira Mono", monospace;
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-color);
  opacity: 0.5;
}

.heatmap-kpi-value {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-color);
  line-height: 1.1;
}

.heatmap-kpi-sub {
  font-family: ui-monospace, "Cascadia Code", "Fira Mono", monospace;
  font-size: 0.7rem;
  color: var(--text-color);
  opacity: 0.5;
  text-transform: uppercase;
}

@media (max-width: 767.98px) {
  .heatmap-kpi-row {
    gap: 1rem;
    flex-wrap: wrap;
  }
  .heatmap-kpi-value {
    font-size: 1.1rem;
  }
}
```

**Four KPIs -- all computed from `daily_counts` already in JS at render time:**

1. **TOTAL SCROBBLES** -- `data.total_scrobbles.toLocaleString()`
   No sub-label.

2. **BEST DAY** -- value: count on the peak day (`data.max_count`)
   Sub-label: date of that day in format `"FEB 14"` (uppercase mono).
   ```js
   // Find the date key with the highest count
   var bestDate = Object.keys(dailyCounts).reduce(function (a, b) {
     return dailyCounts[a] >= dailyCounts[b] ? a : b;
   });
   var bestCount = dailyCounts[bestDate];
   var bestD = parseLocalDate(bestDate);
   var bestLabel = MONTH_NAMES[bestD.getMonth()].toUpperCase() +
                   ' ' + bestD.getDate();  // e.g. "FEB 14"
   ```

3. **ACTIVE DAYS** -- value: count of days where `count > 0`
   Sub-label: `"/ 365"` (always 365 regardless of leap year in range,
   since we display "last 365 days" to the user).
   ```js
   var activeDays = Object.values(dailyCounts).filter(function (c) {
     return c > 0;
   }).length;
   ```

4. **CURRENT STREAK** -- value: N + `"d"` suffix
   Count backwards from `to_date` (today) until the first zero-count day.
   A zero today means streak is 0. A day with no data is treated as 0.
   ```js
   function computeStreak(dailyCounts, toDate) {
     var streak = 0;
     var d = new Date(toDate);
     while (true) {
       var key = isoDate(d);
       if (!dailyCounts[key] || dailyCounts[key] === 0) break;
       streak++;
       d.setDate(d.getDate() - 1);
     }
     return streak;
   }
   ```
   Displayed as `"19d"` (value) with no sub-label, matching the mock.

#### 2d. CSS + JS -- legend repositioned

Move legend from below the grid to the top-right of the frame, inline with
the KPI row. On mobile it stacks below the KPI row and remains above the
grid, matching the WP-5 mobile-layout dependency.

```css
.heatmap-frame-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 1.25rem;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-family: ui-monospace, "Cascadia Code", "Fira Mono", monospace;
  font-size: 0.65rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-color);
  opacity: 0.6;
}

.heatmap-legend-bar {
  width: 80px;
  height: 8px;
  border-radius: 2px;
}

@media (max-width: 767.98px) {
  .heatmap-frame-top {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
```

HTML layout inside the frame (JS-built):
```
.heatmap-frame
  .heatmap-frame-top
    .heatmap-kpi-row  (left)
    .heatmap-legend   (right: LESS [bar] MORE)
  #heatmap-grid       (SVG)
```

#### 2e. JS -- month label font in SVG

Apply monospaced font-family directly on SVG `<text>` elements for month
and day-of-week labels:

```js
mTxt.setAttribute('font-family',
  'ui-monospace, "Cascadia Code", "Fira Mono", monospace');
mTxt.setAttribute('letter-spacing', '0.04em');
```

#### 2f. index.html -- markup change

Replace the existing `#heatmap-result` inner markup. The outer
`<div class="col-md-8 d-none" id="heatmap-result">` wrapper stays (JS
targets it). Inner content becomes:

```html
<p class="heatmap-headline d-none" id="heatmap-result-headline"></p>
<div class="heatmap-frame d-none" id="heatmap-result-frame">
  <div class="heatmap-frame-top">
    <div class="heatmap-kpi-row" id="heatmap-kpi-row"></div>
    <div class="heatmap-legend">
      <span>Less</span>
      <div class="heatmap-legend-bar" id="heatmap-legend-bar"></div>
      <span>More</span>
    </div>
  </div>
  <div id="heatmap-grid"></div>
</div>
<div class="text-center mt-3">
  <button type="button" class="btn btn-outline-primary btn-sm"
          id="heatmap-search-again">Search Again</button>
</div>
```

The headline and frame are shown via `fadeIn()` on render; the outer
`#heatmap-result` wrapper visibility is managed the same as before.

**JS DOM reference updates:** Add `resultHeadline`, `resultFrame`,
`kpiRow` to the DOM reference block in `initForm()`. Remove `resultTitle`
and `resultSubtitle` (replaced by headline + KPIs).

**Acceptance criteria:**
- Headline renders: username in accent color (italic), rest in text-color
- Four KPI stats render with correct values and mono labels
- Legend is top-right on desktop, stacked below KPIs and above grid on mobile
- Frame has 14px radius, warm cream light / inky purple-dark surface
- No Bootstrap `.card` class on the result frame
- Month labels use monospaced font in SVG
- Mobile interim fallback keeps the desktop SVG in a contained horizontal
  `#heatmap-grid` scroller so the page itself does not drag; full vertical
  mobile rendering remains WP-5
- `textContent`/`createTextNode` used exclusively for user data (no innerHTML)
- No changes to `global.css`, `base.html`, or any Python file
- `pre-commit run --all-files` passes
- Owner tests in Firefox (dark + light mode)

**Net tests:** 0 (JS/CSS -- owner tests visually)
**Commit:** `feat(heatmap): redesign result as artifact with frame, headline, KPIs`

---

### WP-3: Pill rename + subtitle removal

**Goal:** Rename "Album Filtering" pill to "Top Albums". Remove the subtitle
line entirely from the result (headline + KPI row replace it -- the date
range is redundant with "last 365 days" in the headline, and scrobble count
is in the TOTAL SCROBBLES KPI).

**Files:**
- `templates/index.html` -- pill text, Info modal tip
- `static/js/heatmap.js` -- remove subtitle build logic, remove
  `resultSubtitle` DOM reference, remove `formatDateLong` if unused

**Implementation:**

Pill (index.html line 21):
```html
<span class="mode-pill active" data-mode="album" ...>Top Albums</span>
```

Info modal tip: update "Album Filtering" -> "Top Albums" in the tip text.

Subtitle: `#heatmap-result-subtitle` element and `resultSubtitle` JS
reference are removed entirely. The `formatDateLong` helper can be removed
if no other code uses it (check before deleting). `formatDateShort` is not
needed -- the subtitle is gone.

**Acceptance criteria:**
- Pill shows "Top Albums" on desktop and mobile
- Info modal tip updated
- No subtitle element or logic remains in heatmap result
- No dead `formatDateLong`/`formatDateShort` code if unused
- `pre-commit run --all-files` passes

**Net tests:** +1 route regression test for rendered index pill/modal copy
**Commit:** `feat(heatmap): rename pill to Top Albums; remove redundant subtitle`

---

### WP-4: Pinwheel SVG clipping fix

**Goal:** The pinwheel blade expansion animation is clipped because the SVG
element has implicit `overflow: hidden` and the container constrains it too
tightly. Fix by adding `overflow="visible"` to the SVG and giving the
container enough room.

**Root cause:**
`viewBox="-4 -4 40 40"` with blade translations of ±5.4 units. At max
expansion, blades extend to ~viewBox edge, which is clipped by default SVG
overflow. Container `max-width: 80px` / `max-height: 64px` compounds this.

**Files:**
- `templates/inline/scrobblescope_pinwheel.svg` -- add `overflow="visible"`
- `static/css/heatmap.css` -- update `.heatmap-spinner-wrapper` and svg rules

**SVG change (line 3):**
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 40 40" overflow="visible">
```

**CSS change:**
```css
.heatmap-spinner-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 120px;
  height: 120px;
  margin: 0 auto 1rem;
  overflow: visible;
}

.heatmap-spinner-wrapper svg {
  width: 80px;
  height: 80px;
  overflow: visible;
  display: block;
}

@media (max-width: 767.98px) {
  .heatmap-spinner-wrapper {
    width: 96px;
    height: 96px;
  }
  .heatmap-spinner-wrapper svg {
    width: 64px;
    height: 64px;
  }
}
```

**Acceptance criteria:**
- Pinwheel blades expand fully without clipping on desktop and mobile
- Spinner is visually centered in the loading card
- Loading card does not shift or overflow during animation
- Owner tests in Firefox (dark + light mode, desktop + Responsive Design Mode)
- `pre-commit run --all-files` passes

**Net tests:** 0
**Commit:** `fix(heatmap): fix pinwheel SVG clipping during blade expansion`

---

### WP-5: Mobile vertical heatmap layout

**Goal:** On viewports narrower than 768px, render the heatmap in a vertical
orientation -- weeks as rows (oldest at top, newest at bottom), 7 columns
(Mon-Sun). No day-of-week or month labels. Cell size fills available width.
Desktop horizontal layout unchanged.

**Design rationale:**
Horizontal grid (54 cols x 7 rows) at 360px viewport: 54 * (13+3) = 864px
mapped into ~300px = cells render at ~5px. Illegible and untappable.

Vertical grid (7 cols x ~54 rows) at 360px: (320px - 6*3px) / 7 = ~43px
per cell. Tappable, readable. Time flows top-to-bottom, which is a natural
mobile reading pattern (Apple Calendar month view, Google Calendar week).
No labels needed -- tooltips on tap provide full date + count.

**Files:**
- `static/js/heatmap.js` -- add `renderHeatmapMobile()`, rename current
  render body to `renderHeatmapDesktop()`, branch in `renderHeatmap()`
- `static/css/heatmap.css` -- mobile grid container adjustments

**JS implementation:**

```js
function renderHeatmap(data) {
  if (window.innerWidth < 768) {
    renderHeatmapMobile(data);
  } else {
    renderHeatmapDesktop(data);
  }
}
```

Rename current `renderHeatmap` body -> `renderHeatmapDesktop` (no behavior
change). Add `renderHeatmapMobile`:

```js
function renderHeatmapMobile(data) {
  var fromDate    = parseLocalDate(data.from_date);
  var toDate      = parseLocalDate(data.to_date);
  var dailyCounts = data.daily_counts;
  var maxCount    = data.max_count || 0;
  var totalDays   = Math.round((toDate - fromDate) / 86400000) + 1;

  var MOBILE_GAP  = 3;
  var containerWidth = gridContainer.clientWidth || 300;
  var mCellSize   = Math.floor((containerWidth - 6 * MOBILE_GAP) / 7);
  var mStep       = mCellSize + MOBILE_GAP;
  var startDow    = mondayIndex(fromDate);

  // Total grid slots = startDow offset + totalDays, rounded up to full weeks
  var totalSlots  = startDow + totalDays;
  var numWeeks    = Math.ceil(totalSlots / 7);
  var svgW        = 7 * mStep;
  var svgH        = numWeeks * mStep;

  gridContainer.innerHTML = '';
  var svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 ' + svgW + ' ' + svgH);
  svg.setAttribute('width', '100%');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label',
    'Scrobble heatmap for ' + data.username);

  var cellData = [];
  for (var i = 0; i < totalDays; i++) {
    var d      = addDays(fromDate, i);
    var key    = isoDate(d);
    var count  = dailyCounts[key] || 0;
    var offset = startDow + i;
    var col    = offset % 7;        // Mon=0 .. Sun=6 (left to right)
    var row    = Math.floor(offset / 7);  // week index (top to bottom)

    var x = col * mStep;
    var y = row * mStep;

    var rect = document.createElementNS(SVG_NS, 'rect');
    rect.setAttribute('x', x);
    rect.setAttribute('y', y);
    rect.setAttribute('width', mCellSize);
    rect.setAttribute('height', mCellSize);
    rect.setAttribute('rx', CORNER_R);
    rect.setAttribute('ry', CORNER_R);
    rect.setAttribute('class', 'heatmap-cell');
    rect.setAttribute('fill',
      count > 0 ? rocketColor(countToNorm(count, maxCount)) : zeroFill());
    rect.setAttribute('data-date', key);
    rect.setAttribute('data-count', count);
    cellData.push({ el: rect, date: d, count: count, x: x, y: y });
    svg.appendChild(rect);
  }

  gridContainer.appendChild(svg);
  legendBar.style.background = legendGradient();
  hideElement(heatmapLoading);
  fadeIn(heatmapResult);
  initTooltips(svg, cellData);
}
```

**Shared helpers reused (no duplication):**
`parseLocalDate`, `mondayIndex`, `addDays`, `isoDate`, `rocketColor`,
`countToNorm`, `zeroFill`, `legendGradient`, `initTooltips`, `CORNER_R`,
`SVG_NS`, `ROCKET_STOPS`.

**Mobile CSS:**
```css
@media (max-width: 767.98px) {
  .heatmap-frame {
    padding: 1rem 0.75rem;
  }

  #heatmap-grid svg {
    /* Allow vertical scroll if grid is taller than viewport */
    max-height: none;
  }
}
```

**Acceptance criteria:**
- At 360px viewport: vertical grid renders, cells are ~40px+, tappable
- No day-of-week or month labels on mobile layout
- `from_date` aligned to correct Mon-Sun column
- Tooltips work on tap: show full date + count, dismiss on touchend/scroll
- KPI row and legend render correctly above the mobile grid (from WP-2)
- Desktop layout (>= 768px) unchanged
- Dark mode zero-cell fill correct on mobile
- Owner tests in Firefox Responsive Design Mode (360x800, iPhone UA)
- `pre-commit run --all-files` passes

**Net tests:** 0 (JS/visual -- owner tests; no backend change)
**Commit:** `feat(heatmap): add vertical mobile layout for narrow viewports`

---

## 3. WP execution order and gates

```
WP-1 (doc) -> WP-2 (frame/KPIs) -> WP-3 (pill/subtitle) -> WP-4 (pinwheel) -> WP-5 (mobile)
```

Owner visual-check gate after each WP before the next begins.
WP-3 through WP-5 are independent of each other but depend on WP-2 being
committed (the frame structure must exist before mobile layout is built on it).

---

## 4. Validation gate (every WP)

```bash
pytest -q                                  # must stay at 386 passing
pre-commit run --all-files                 # all 10 hooks green
python scripts/doc_state_sync.py --check   # exit 0
```

---

## 5. Software principles

| Principle | Application |
|-----------|-------------|
| KISS | KPIs computed in JS from already-loaded data -- no new API calls, no backend changes. |
| SoC | `renderHeatmapDesktop` / `renderHeatmapMobile` -- separate render paths, all color/date helpers shared. |
| DRY | `rocketColor`, `countToNorm`, `zeroFill`, `initTooltips`, `CORNER_R` reused by both paths. |
| Fail Fast | Mobile detection at render call time, not at page load -- no stale viewport state. |
| Least Knowledge | KPI computation touches only `daily_counts` and `total_scrobbles` already in the result payload. |
| Boy Scout | Stale perf notes and FINDINGS.md header corrected in WP-1. |
| No innerHTML with user data | Username set via `textContent`/`createTextNode` throughout (F-B18-9). |

---

## 6. Acceptance criteria summary

| WP | Criterion |
|----|-----------|
| WP-1 | No stale current-state "sequential/11-13s" assertions in active/bootstrap docs; FINDINGS.md F-B18-11 and header current |
| WP-2 | Frame, headline, KPIs, legend render correctly in dark and light mode |
| WP-3 | Pill shows "Top Albums"; subtitle element and logic fully removed |
| WP-4 | Pinwheel blades expand without clipping on desktop and mobile |
| WP-5 | Mobile shows vertical grid with ~40px tappable cells; desktop unchanged |

After WP-5 owner sign-off, `feat/heatmap` is ready for the PR to main.

---

## 7. Files changed per WP

| WP | Files |
|----|-------|
| WP-1 | `PLAYBOOK.md`, `AGENT_NOTES.md`, `.claude/SESSION_CONTEXT.md`, `FINDINGS.md`, `AGENTS.md`, `HANDOFF_PROMPT.md`, `.gitignore`, `BATCH19_DEFINITION.md` |
| WP-2 | `static/css/heatmap.css`, `static/js/heatmap.js`, `templates/index.html`, `BATCH19_DEFINITION.md` |
| WP-3 | `templates/index.html`, `static/js/heatmap.js`, `tests/test_routes.py` |
| WP-4 | `templates/inline/scrobblescope_pinwheel.svg`, `static/css/heatmap.css` |
| WP-5 | `static/js/heatmap.js`, `static/css/heatmap.css` |
