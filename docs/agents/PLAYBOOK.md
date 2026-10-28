# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. That branch merged into `main` as PR #245 on 2026-09-30 and `origin/test` is
  deleted, so side-task PRs branch from `main` and run the guard against its default
  base. The owner names the branch WP-1 opens.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). The WP-0 close-out below is what remains of WP-0. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition. It runs
  after the tranche, before WP-1 (owner ruling 2026-10-22).
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. The include-unmatched
  control (PR #1) and backend hygiene (PR #2) are done. The album request module
  is done (PR #3, branch refactor/album-request-module, plan
  `docs/superpowers/plans/2026-10-20-album-request-module.md`); normalized
  Last.fm scrobbles with one album aggregate is done (PR #4, branch
  refactor/lastfm-scrobbles, plan
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); one album-metadata
  encoding is done (PR #5, branch refactor/metadata-encoding, plan
  `docs/superpowers/plans/2026-10-20-metadata-encoding.md`); the statistics
  module is done (PR #6, branch refactor/statistics-module, plan
  `docs/superpowers/plans/2026-10-20-statistics-module.md`). Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #7, UI consistency, finished round 1 (plan
  `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`); further rounds
  wait for the owner's screenshots, each with its own plan. A side-task PR of
  cheap fixes from the 2026-10-21 architecture review and the logging audit
  is done (branch `fix/pre-batch23-side-tasks`, plan
  `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md`), and so is a
  CI change that keeps Playwright's Ubuntu packages in the Actions cache
  (branch `ci/playwright-apt-cache`, plan
  `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md`). UI
  consistency round 2 is done (PR #268, branch `feat/ui-consistency-round-2`,
  plan `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md`). Its
  backlog runs now on `feat/ui-round-2-backlog`: the owner settles each item
  in a live session and the accepted changes landed as they were made (PR
  #269). All fourteen tasks of the plan
  `docs/superpowers/plans/2026-10-25-ui-round-2-backlog.md` have landed on
  the same branch (the documentation, the gates that hold the accepted
  changes, the F-B23-46 ranking rule and the stale-copy sweep), followed by a
  test consolidation under the owner's lean-suite ruling. PR #269 merged
  into `main` (merge commit `997f7584`) and is deployed. The album-matching,
  cache re-verification and MusicBrainz fixes are on `fix/album-matching`
  (PR #270, plan `docs/superpowers/plans/2026-10-25-album-matching.md`),
  based on `main`: every plan task has landed there and the six findings it
  files are closed. PR #270 merged into `main` (merge commit `4a2d2406`) and is deployed. The documentation refresh merges last.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.
- **What PR #245 ships (owner ruling 2026-09-29):** the WP-0 foundation and
  every fix from the three reviews, including the job module with its storage
  seam, typed provider failures and provider failure logs that carry no
  listener data. Moved to the follow-up PR: job persistence, the Last.fm
  scrobble seams, the album request module, one album-metadata encoding, the
  statistics module and the tooling package.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam and typed provider failures, job persistence
  (gates WP-3), an album request module (gates WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (gates WP-2), one album-metadata
  encoding (gates WP-3), a statistics module (gates WP-6), and provider
  failure logs that carry no listener data. Which of these #245 ships is
  in the "What PR #245 ships" bullet above; the rest wait for the follow-up
  PR.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-10-27 - Include the streamgraph in Save image

Side task, no batch tag: the streamgraph in the saved image (streamgraph plan Task 9), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (ruling U23): match the Claude Design reference; the saved image shows what the page shows.

What changed and why: `static/js/heatmap.js` `drawHeatmapImage` now calls `clearWeek()` first (S19), serialises the stream SVG through a new `streamAsImage` (a clone without `line.stream-guide`, every `path.stream-layer` at `opacity` 1 with its `style` removed, the section label in `monospace`) and draws it flush under the grid at the grid's width, growing the canvas by the stream's rendered height (SG9-F1: the plan's "plus the section gap" is superseded, the page has no gap and the file now matches it). `gridAsImage` also drops `.stream-column-ring`; `removeAll` and `svgCloneAsImage` are shared helpers. The background is painted from `--heatmap-surface` resolved on the frame (S15), so the file takes the timeline surface (dark `#1f1b28`) and not the body's `#181520`. The header record gains `drawnHeader.stream = {label, height}`, only when a stream exists; with no stream (mobile layout or no payload) the export is unchanged.

Gate: new check `stream is in the saved image` (DESKTOP, THEME_MOTION, dark and light) saves for real and decodes the JPEG in the page. Image growth over the no-payload export is the stream height times the export scale, within an absolute 2 px (SG9-F3, replaces a 4% tolerance); a layer pixel at the tallest week and an "Everything else" pixel match the resolved fills; `drawnHeader.stream` matches the page. SG9-F2: the check saves once at rest, hovers week 30, saves again and compares that week's column in both JPEGs (max per-channel difference 12), so a ring, guide or dimmed layer reaching the file fails; proved red with `clearWeek()` and the clone resets removed (differences 238 and 170 of 255).

Rulings recorded: S15, S19, SG9-F1, SG9-F2, SG9-F3. Firefox probe: the same assertions pass in Firefox, dark and light, and the saved images were viewed; the full gate runs this check in Chromium only.

Deviations: the stacked-branch name replaces `feat/ui-audit-v6` in this entry. Check (b) samples the middle of the layer found on the centre line, not the centre-line pixel, because that pixel can fall on a layer edge. The landing relied on the nested gate-runner's ALL_PASS (frontend gate 57 checks passed) and did not re-run the frontend gate.

Existing tests edited, by name: none (new gate check only, registered in `CHECKS`).

Validation: `pytest -q` -- **3050 passed**.

### 2026-10-27 - Add keyboard access to the streamgraph

Side task, no batch tag: keyboard access to the streamgraph (streamgraph plan Task 8), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (ruling U23): match the Claude Design reference, and the stream must not be pointer-only.

What changed and why: `static/js/heatmap.js` gains the pure helpers `streamKeyTarget`, `streamStartTarget` and `streamPositions` (test seam) and the key and focus handlers on `#stream-chart`, now `tabindex="0"`, `role="application"` with an `aria-label`. The stream is one tab stop: on focus with nothing selected it starts at week 26 (the last week when there are fewer) on the top layer; the arrow keys, Home and End move through the same `showWeek` path as the pointer, edges clamp, ArrowUp and ArrowDown walk the stack positions down to "Everything else", blur calls `clearWeek()`, and Tab is never trapped. `static/css/heatmap.css` adds the `.stream-chart:focus-visible` outline (2px, offset 4px). `scripts/dev/_frontend_gate_stream.py` adds `stream is one keyboard tab stop` (DESKTOP, Chromium), registered in `frontend_gate.py` (THEME_MOTION); the gate went from 55 to 56 checks.

Padding change: `#heatmap-grid` at 860px and wider goes from 4px to 8px padding, with a matching -8px margin and `calc(100% + 16px)` width, so the grid box no longer clips the outline (it paints 6px outside the chart). The layout is unchanged (net content box identical); reviewed and accepted.

Rulings recorded: SG8-F1 (review, Minor, restored as the brief mandates): the gate injects a focusable sentinel after the stream in its own page only and asserts Tab from the stream lands on it, then Shift+Tab twice returns to the grid cell. SG8-F2 (review, Important): the sentinel is injected after the outline, walk and tab-stop measurements, so it cannot add height to the grid and mask a bottom clip; proved red with bottom padding removed. Accepted Minors: a pointer leaving while the stream is focused clears the shown week (keys resume from the last keyboard week), and there is no Escape handling.

Contrast (rendered focus outline against the frame, both themes): min 5.45, max 7.06; nothing fails. Firefox probe: tab stop, arrows, Home / End, blur and resize-blur pass; the full gate runs this check in Chromium only.

Deviations: the stacked-branch name replaces `feat/ui-audit-v6` in this entry. The landing relied on the nested gate-runner's ALL_PASS (frontend gate 56 checks passed) and did not re-run the frontend gate.

Existing tests edited, by name: none (new tests appended to `tests/frontend/test_heatmap_pure_functions.py`).

Validation: `pytest -q` -- **3050 passed**.

### 2026-10-27 - Scrub the streamgraph with a panel and column ring

Side task, no batch tag: hover and touch scrubbing of the streamgraph with a values panel and a heatmap column ring (streamgraph plan Task 7), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (ruling U23): the stream shows one readable value per week, as the Claude Design reference does.

What changed and why: `static/js/heatmap.js` gains the pure helpers `weekFromX`, `layerAtY` and `panelModel` (test seam), the DOM functions `showWeek` and `clearWeek`, and Pointer Events on `#stream-chart` (`pointermove`, `pointerdown`, `pointerleave`, `pointercancel`), one path for mouse and touch. `showWeek` dims the other layers to 0.25, draws the guide line at the column centre, appends one column ring around that week's seven-row column in the grid SVG and fills a panel with the week's artist counts ("Everything else" last, the hovered row marked). `renderHeatmap` calls `clearWeek()` first, so a re-render leaves no stale ring. `static/css/heatmap.css` holds the panel rules (count column in the figure face with tabular numbers). `scripts/dev/_frontend_gate_stream.py` adds three checks, registered in `frontend_gate.py` (THEME_MOTION): `stream hover shows panel and ring` (DESKTOP, weeks 0/30/40 on a window that starts mid-week, the panel flip, re-render clearing, every panel row inside the chart box at 1280x720), `stream touch drag scrubs` (Chromium only by design) and `stream reduced motion` (DESKTOP). The frontend gate went from 52 to 55 checks.

Rulings recorded: S17, `layerAtY` takes an optional fourth argument `order` (maps stack slots to ranks); three-argument callers are unchanged (accepted backward-compatible change of a frozen interface). SG7-F1 (review, Important): the count column uses `font-family: var(--font-figure)` with `font-variant-numeric: tabular-nums`, as the reference draws it. SG7-F2 and the S18 refinement: the panel sits a little above the plot top (`STREAM_PANEL_RISE`, the reference's 372px against the plot's 380px) and lifts only when it would otherwise run past the chart's bottom edge; at 1280px the unlifted panel was clipped by `#heatmap-grid`, hiding the "Everything else" row. The gate proves it red with the lift disabled ("1 of 11 panel rows are outside the chart's visible box").

Contrast (rendered colours, both themes): row ink 8.64 light / 9.20 dark; header on panel 5.53 / 5.05; hovered ink 17.57 / 14.43; "Everything else" swatch 3.63 / 4.65; guide and ring against the frame 14.78 / 14.43. Min text 5.05, min non-text 3.63; nothing fails. Firefox probe: hover, flip, re-render clearing and reduced motion pass; touch drag is Chromium only.

Deviations: the stacked-branch name replaces `feat/ui-audit-v6` in this entry. The panel stays inside the chart box by lifting (S18), a deviation from the reference. Task 9 (Save image) must clear a shown week before serialising (S19). The landing relied on the nested gate-runner's ALL_PASS (frontend gate 55 checks passed, ruling U28) and did not re-run the frontend gate.

Existing tests edited, by name: `test_stream_payload_valid` (three parametrize cases added: non-string week, non-string name, `artists` not a list).

Validation: `pytest -q` -- **3029 passed**.

### 2026-10-27 - Recolour the streamgraph when the theme changes

Side task, no batch tag: the streamgraph recolours on a theme change (streamgraph plan Task 6), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (rulings U18, U20, U23): the streamgraph follows the light and dark themes like the rest of the page, with the owner's colour values unchanged.

What changed and why: the stream paints resolved attribute values so a saved image needs no stylesheet, and a `data-theme` flip left those stale. `static/js/heatmap.js` gains `currentStreamTheme()` (shared with `drawStream`) and `recolourStream()`, which `initThemeObserver()` calls beside `updateZeroFills()`. It rewrites each layer's fill (artists from `layerColour(rank, theme)`, "Everything else" from the frame's `--stream-other`), the gridline strokes (`--stream-line`) and the section label fill (`--stream-muted`) in place, with no re-render. The new gate check `stream colours follow theme and meet contrast` (DESKTOP, THEME_MOTION, registered in `frontend_gate.py`, written in `scripts/dev/_frontend_gate_stream.py`) keeps a handle on the chart node, switches dark, light, dark with no reload, and asserts the node is not replaced, every artist layer equals `layerColour(rank, theme)`, "Everything else" is #3a3347 / #ddd5c5, every gridline and the label match the frame-resolved tokens, and the label clears 4.5:1.

Contrast (rulings S13, S14, U20): section label on the frame 5.05 dark / 4.65 light, asserted at 4.5. Layer fills 1.53-10.22 dark and 2.02-10.52 light are exempt from 3:1 (logged, not asserted); the owner's colour values are unchanged.

Finding SG6-F1 (review of the first patch, closed): the check compared only layer 0 and the first gridline, so a partial recolour would pass. It now compares every layer by its own rank and every gridline, and names an empty layer list or no gridlines. Red against a `recolourStream` that repainted only layer 0 (layers 1-9 reported), green on the real code in chromium and firefox.

Deviations: the brief's 3:1 assertion on layer fills is not made (U20). The mermaid edges for the new imports in `docs/architecture/documentation-tooling.md` are Task 10's (ruling S16a). The landing relied on the nested gate logs (frontend gate 52 checks passed, ruling U19) and did not re-run the frontend gate.

Existing tests edited, by name: none.

Validation: `pytest -q` -- **3014 passed**.
