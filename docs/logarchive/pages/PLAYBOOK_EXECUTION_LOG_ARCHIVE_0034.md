<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0034

### 2026-10-27 - Record new frontend-gate flake sightings

Side task, no batch tag: adding the gate failures seen during the UI audit v6 PR to F-B23-58, on `feat/ui-audit-v6`, a branch off `main`.

This is new evidence for an existing finding, not a new finding. F-B23-58 asked for new sightings with their timing before any fix. Three kinds were appended from the plan's gate logs: three `net::ERR_NO_BUFFER_SPACE` sightings (a grep of every gate log finds exactly three), `shell text scaling [mobile]` (`shell.css`) and two code-phase `large display scale parity [desktop]` runs (`index.css` in `task-sg8-code-3`, `static/js/theme.js` in `task-row5-code-1`), each failing after an asset failed to load (all passed on the next run); one `cached heatmap restoration painted the loading panel before its result` (passed on the next run); and a non-failing `Job context not found` log line noted as noise. The finding's status box and fix shape are unchanged.

Deviations: the brief called the second `ERR_NO_BUFFER_SPACE` sighting "index.css, 72 large-display checks"; the log shows 72 `large display scale parity [desktop]` failures, each carrying the `index.css` error, so the entry says that. No code changed.

Existing tests edited, by name: none.

Validation: `pytest -q` -- **3023 passed**.

### 2026-10-27 - Parse the canvas font string without a regex

Side task, no batch tag: replacing the `_FONT_SHORTHAND` regular expression in the frontend gate's theme check with plain token parsing, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (U34: "I agree with (b), because a quick fix now is worth it over forgetting it"). Codacy flagged `_FONT_SHORTHAND` (`scripts/dev/_frontend_gate_theme.py`) as an inefficient regular expression. It measured linear, so the flag was a false positive, but plain parsing clears the check for good. `_split_canvas_font` now walks the whitespace tokens up to the first size token (`<n>px`, with an optional `/line-height`), keeping the last weight token (`bold` is 700, `normal` is 400); `_is_size_token` is the new helper and the `re` import is gone. Behaviour is identical on 22 compared inputs and a 400k-string fuzz; the one difference is that size digits are ASCII-only (the old `\d` also took Unicode digits, which `ctx.font` never emits). The parametrized weight cases (`bold`, `normal`, `italic 600` with a line-height, `bold 600`, a string with no size token) close the gap row 1 recorded under R1-F5.

Deviations: none.

Existing tests edited, by name: `tests/scripts/dev/test_frontend_gate_theme.py::test_a_saved_headline_drawn_at_another_weight_is_reported` (extended with a drawn-weight parameter and five cases)

Validation: `pytest -q` -- **3023 passed**.

### 2026-10-27 - Lift the home pause button to the footer's gap

Side task, no batch tag: lifting the home page's "Pause animations" button to the footer button's gap, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (U30: "maybe raise it up by a touch in the index card -- to match the distance from the bottom of the page as is in the results page"). At 860px and wider the home button sat flush with the window bottom (0px); the footer button on the other pages sits 24px above the page foot (`.page-footer-extras` padding-bottom, 1.5rem). `static/css/index.css` now gives `.index-grid .index-hero` a 1.5rem bottom padding, so the button's bottom edge is 24.00px above the viewport foot in both modes at the six desktop sizes, in Firefox and Chromium, centring unchanged. The extra 24px made 1280x720 scroll by 12-13px, so a `@media (max-height: 760px)` rule takes 1rem back from the hero's top padding; windows taller than 760px are unchanged. The layout gate reads the shown button's gap and the footer row's computed padding-bottom and fails when they differ by more than 1px (`_home_pause_failures` in `scripts/dev/_frontend_gate_layout.py`).

Deviations: the gate compares the gap with the footer row's computed padding-bottom, not a seeded results page (a seeded results page agrees to within 1px, measured); 1.5rem is written in both `shell.css` and `index.css` (no shared token, `shell.css` was outside the task), and the gate's equality check fails if either changes alone; the `max-height: 760px` top-padding give-back goes beyond "raise the button". Real laptop windows near 650px tall already scrolled before this change and still do.

Existing tests edited, by name: `tests/scripts/dev/test_frontend_gate_layout.py::test_the_home_page_must_not_scroll_vertically_in_either_mode` (two parametrized cases: gap 0 fails, 24.9 passes) and its `PAUSE_OK` fixture.

Validation: `pytest -q` -- **3018 passed**.

### 2026-10-27 - Make "Pause animations" stop every animation

Side task, no batch tag: making "Pause animations" stop every auto-moving thing, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (U29: "clicking pause animation doesn't stop the top artist carousel"; U31: the loading page's pinwheel should stop too; U33: the unmatched page's button does not pause the header). Row 3's control set `data-motion="still"` but only the header bars honoured it. Now the results spotlight's interval callback in `static/js/results-spotlight.js` returns early while `<html data-motion>` is `still`, so a page loaded paused never advances and Play resumes at the next period from the card shown. In `static/css/shell.css` the still rule also covers `.ss-pinwheel svg > g` and `> g > g`, so the pinwheel rests (drawn artwork, no transform, as reduced motion does) and the phase line still shows progress as text. U31 supersedes row 3's pinwheel exemption. No live doc called the pinwheel exempt, so no doc prose changed.

Reproduction: the header bars were already stopping on the results page at the base commit (Firefox and Chromium: `animation-name` none after the click and after a reload with the stored choice), so the first bar report did not reproduce and the bar rule is unchanged. U33 (unmatched page) was reproduced with a real click on a seeded page at 390, 900, 1280 and 1920px in both browsers and also works (bars `ss-bar-pulse` x5 before, `none` x5 after; the controller repeated it on the owner's server), so no code fix; the likeliest cause is a carried-over paused state or a cached stylesheet. A click check was added anyway. The bar rule and the pulse rule have equal specificity and the pause wins by source order only; the new checks guard that.

Deviations: none from the owner rulings. Checks: `_paused_motion_failures` and `_unmatched_pause_failures` in `scripts/dev/_frontend_gate_pipeline.py` (bars and pinwheel rest while paused; the unmatched button click rests the bars), `_pause_hold_failures` in `scripts/dev/_frontend_gate_spotlight_photo.py` (stored pause before load: artist unchanged over 3 periods and bars rest, then Play resumes), and `test_pause_animations_holds_the_rotation_and_play_resumes_it` in `scripts/dev/results_behavior_tests.py`.

Existing tests edited, by name: `tests/scripts/dev/test_frontend_gate_spotlight_photo.py::test_the_hold_check_focuses_then_hovers_and_counts_the_periods` (the check gained a paused phase) and `test_a_timed_out_hold_wait_is_judged_by_the_tick_count` (now three tick failures plus a "did not resume").

Validation: `pytest -q` -- **3016 passed**.

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

### 2026-10-27 - Draw the top-artists streamgraph under the grid

Side task, no batch tag: the top-artists streamgraph drawn under the heatmap grid (streamgraph plan Task 5), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (rulings U18, U23): a desktop-only streamgraph that lines up with the grid's week columns, matching the Claude Design reference; a mobile streamgraph is a later PR.

What changed and why: `static/js/heatmap.js` gains `streamPayloadValid` (in the test seam) and `drawStream`, called at the end of `renderHeatmapDesktop` when the payload is valid and the scale is above 0. It stacks "Everything else" below the top ten artists, adds month gridlines and a muted section label, and keeps its state in module-level `streamState`, reset on every `renderHeatmap`. Every paint is a resolved attribute so the saved image needs no stylesheet; an absent or invalid payload and the mobile layout draw nothing. `static/css/heatmap.css` adds `#heatmap-grid { position: relative }`, `.stream-layer` and `.stream-chart`. The new `scripts/dev/_frontend_gate_stream.py` holds `seed_stream_job` and two gate checks, registered in `frontend_gate.py`: `stream aligns with the grid columns` (1280 and 1000 px, within 1 px) and `stream absent without payload or on mobile`. Per ruling SG5-L1 the gate-module lists in `docs/architecture/documentation-tooling.md` (now sixteen siblings) and `.claude/SESSION_CONTEXT.md` name the new module.

Contrast (rulings S13, S14, U20): section label on the frame 5.05 dark / 4.65 light, passing 4.5. Layer fills 1.52-10.22 dark and 2.02-10.52 light, "Everything else" 1.40 / 1.23, and gridlines 1.30 / 1.12 are exempt from 3:1; the owner's colour values are unchanged. A Firefox probe passed alignment, absence and mobile.

Deviations: none from the brief. A theme flip without a re-render leaves the previous theme's fills until Task 6's `recolourStream`. The landing relied on the nested gate logs (frontend gate 51 checks passed, ruling U19) and did not re-run the frontend gate.

Existing tests edited, by name: none; `tests/frontend/test_heatmap_pure_functions.py` is extended with `test_stream_payload_valid`.

Validation: `pytest -q` -- **3014 passed**.

### 2026-10-27 - Scope the timeline surfaces and empty cells to the heatmap frame

Side task, no batch tag: the streamgraph's timeline surfaces and frame-scoped empty cells (streamgraph plan Task 4), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (ruling U18): the darker timeline surfaces apply inside the chart frame only, so the global dark token and every other page keep `#262230`.

What changed and why: `static/css/heatmap.css` declares the `--stream-*` tokens plus `--heatmap-surface` and `--heatmap-empty` on `.heatmap-frame` (light) and `[data-theme="dark"] .heatmap-frame` (dark); no `:root` block is touched. `zeroFill()` in `static/js/heatmap.js` reads `--heatmap-empty` from `#heatmap-result-frame`, and `resolvedColour(token, scope)` takes an optional scope element (default `document.body`) for the later stream tasks. The frontend gate's `check_heatmap_zero_cells_follow_theme` now reads its expected value from the frame, and the new check "timeline surfaces are page-scoped" pins the frame cell fill (`#2e2939` dark, `#c8bfad` light), the untouched global token and the frame background. A Firefox probe passed all of those assertions.

Contrast (rulings S14 and U20): `--stream-line` (gridlines and the panel border) is decorative and exempt from 3:1: 1.30 / 1.12 against the frame and 1.30 / 1.33 against the panel (dark / light). The empty cells keep the shipped heatmap's look: 1.20 / 1.53 against the frame. Text pairs pass: muted on frame 5.05 / 4.65, muted on panel 5.05 / 5.53, ink on panel 14.43 / 17.57, accent on frame 7.06 / 5.45, "Everything else" swatch on panel 4.65 / 3.63. The owner's colour values are unchanged.

Deviations: the updated theme check was not red on the old code (the frame inherited the root token); only the new check failed red. The saved image's background still reads the body's surface (`#181520` dark); ruling S15 assigns the frame scope there to Task 9.

Existing tests edited, by name: none in `tests/`; the gate check `check_heatmap_zero_cells_follow_theme` was refactored onto shared helpers.

Validation: `pytest -q` -- **3004 passed**.

### 2026-10-27 - Add pure layout functions for the streamgraph

Side task, no batch tag: the streamgraph's pure layout maths (streamgraph plan Task 2), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent: the streamgraph is built to match the Claude Design reference, so its layout maths must be pure, tested functions before any DOM work builds on them.

What changed and why: `static/js/heatmap.js` gains the constants `STREAM_PEAK`, `STREAM_BAND`, `STREAM_LABEL_H` and the functions `streamOrder`, `streamBaseline`, `stackLayers`, `streamScale`, `smoothPath` and `layerColour`, all exposed on `__scrobbleHeatmapTestHooks` and touching no DOM. `tests/frontend/test_heatmap_pure_functions.py` covers them with hand-computed cases (17 new cases). A Firefox probe loaded the hooks and checked one `streamOrder`, `stackLayers` and `layerColour` case.

Contrast (ruling S13, confirmed by owner ruling U20): the layer fills are exempt from the 3:1 non-text floor because the scrubber panel states every layer's name and count as text for every week; the ramp and the "Everything else" fills stay the owner's frozen values. Measured WCAG ratios against the frame: dark frame `#1f1b28` layers 1.53-10.22, "Everything else" `#3a3347` 1.40; light frame `#f0ebe0` layers 2.02-10.52, "Everything else" `#ddd5c5` 1.23.

Deviations: Task 2 lands after Task 3 (disjoint files), so the plan's numeric landing order is not followed.

Existing tests edited, by name: none (new tests appended to `test_heatmap_pure_functions.py`).

Validation: `pytest -q` -- **3004 passed**.

### 2026-10-27 - Store the weekly artist counts with the job result

Side task, no batch tag: the heatmap job wiring for the streamgraph (streamgraph plan Task 3), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent: the streamgraph needs the per-week artist counts from the same fetch as the daily counts, and a caller of the job view must not be able to change stored state.

What changed and why: `scrobblescope/heatmap.py` calls `aggregate_weekly_artist_counts(fetch.plays, from_date, to_date)` right after `aggregate_daily_counts` and stores it under `weekly_artists` in the dict passed to `jobs.succeed`; the zero-scrobble guard still fails the job before anything is stored. `_context_view` in `scrobblescope/jobs.py` copies it (outer dict, `weeks`, `other`, the `artists` list, each artist dict with its `counts` list) the way it copies `daily_counts` (F-B18-8).

Deviations: Task 3 lands before Task 2 (disjoint files; Task 2 is still in its code phase), so the plan's numeric landing order is not followed.

Existing tests edited, by name: `TestFetchAndProcessHeatmap::test_happy_path_stores_correct_result_dict` (weeks start on the Monday on or before `from_date`; per week, artist counts plus `other` equal the daily counts over the column's 7 days); `test_context_isolates_dict_results_from_callers` (mutating `weekly_artists` weeks, a counts entry, a name, the artists list and `other` leaves the stored values unchanged).

Validation: `pytest -q` -- **2987 passed**.

### 2026-10-27 - Aggregate weekly top-artist counts for the streamgraph

Side task, no batch tag: the weekly top-artist aggregation (streamgraph plan Task 1), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent: the streamgraph needs per-week play counts for the ten biggest artists on the heatmap's Monday-first grid, with everything else kept in an `other` series so each week still sums to the daily counts.

What changed and why: `aggregate_weekly_artist_counts(plays, from_date, to_date, top_n=10)` in `scrobblescope/plays.py`, next to `aggregate_daily_counts`. The artist key is `normalize_name(artist, "")[0]` (confirmed in `domain.py`: an empty album leaves the artist key unchanged). Artists rank by window total, ties by key; beyond-top_n artists, empty and punctuation-only artists go to `other`; plays outside the window are ignored. It is a pure function and is not wired into the job yet. Tests: `TestAggregateWeeklyArtistCounts` in `tests/test_plays.py` (Monday grid, grouping and ranking, key-less artists, overflow, and the sum invariant against `aggregate_daily_counts`).

Deviations: none. Existing tests edited: none (the import line was extended only).

Validation: `pytest -q` -- **2987 passed**.

### 2026-10-27 - Plan the listening streamgraph

Side task, no batch tag: the streamgraph implementation plan, on `feat/ui-audit-v6-streamgraph`, a branch stacked on `feat/ui-audit-v6`.

Owner intent: the owner asked for the plan with the writing-plans skill, in discrete slices with checkboxes. It is `docs/superpowers/plans/2026-10-27-streamgraph.md`: ten tasks in eight waves, each with files, interfaces, red/green steps and a Firefox probe.

What changed and why: the plan went through three reviews; findings SP-F1..SP-F12 are recorded in the plan workspace, and the last three were wording Minors fixed without a fourth review. It is desktop only (owner ruling U18): the dark surfaces are declared on the heatmap frame, never on `:root`. No code changes; the plan is a point-in-time record.

Deviations: none. Existing tests edited: none.

Validation: `pytest -q` -- **2978 passed**.

### 2026-10-27 - Keep the home page within one screen

Side task, no batch tag: keeping the desktop home page within one screen, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (U24, after the Firefox pass: "ideally there would be 0 vertical scrolling"; U25/U27 placement: the pause button "at the very bottom" of the left column, "centered"). Row 3's "Pause animations" button made `.page-footer-extras` non-empty on the home page, so the page scrolled 92px at every desktop size below the full-height `.index-grid`. From 860px the button now sits at the foot of the home page's left column (`.index-hero__motion`, a second `.motion-toggle` in `templates/index.html`, centred with `margin-top: auto`), and `body:not(.heatmap-stage-active) .page-footer-extras` is `display: none` in `static/css/index.css`, so the footer takes no space (it returns while the heatmap stage replaces the grid). Below 860px the footer copy stays and the hero copy is `display: none`, so exactly one is focusable at any width. `static/js/theme.js` syncs every copy's label and `aria-pressed` to `data-motion`. Measured (scrollHeight - clientHeight, Firefox and Chromium, album and heatmap modes identical): 1920x1080, 1920x960, 1536x864, 1440x900, 1366x768 and 1280x720 went 92px -> 0; 1536x730 went 106px -> 10px (Firefox) and 108px -> 12px (Chromium). The 10px residual is content taller than the viewport (header, hero padding, hero content and the 44px button), not shrunk, per U24 item 5. Rows 2 and 10 are unchanged (tabs and active key tops identical before and after). No Chromium-only CSS; the button's size, focus ring and contrast are unchanged. The gate (`scripts/dev/_frontend_gate_layout.py`) now fails when the home page scrolls at 1920x1080 or 1366x768 in either mode, or when the pause button count, position or sync is wrong.

Focus order: Pause now precedes the form on the home page from 860px. That follows the visual left-to-right order and is one labelled control, so WCAG 2.4.3 is judged met (U24-L1); one extra Tab stop before the form.

Deviations: (U25) supersedes the brief's shorter-grid items 2 and 3. (U26 was superseded by U27: left column, centred.) (U24-L1) the comment in `static/css/shell.css` and the docstring of `tests/test_template_shell.py::test_every_page_wraps_its_footer_extras` said the wrapper is never empty; both now say it is hidden on the home page from 860px (the docstring edit is outside the brief's Touches, authorised by the controller). The gate does not pin which column holds the button; the owner's Firefox check does.

Existing tests edited, by name: `tests/test_template_shell.py::test_every_page_wraps_its_footer_extras` (docstring only) and the `_run_large_display_check` helper in `tests/scripts/dev/test_frontend_gate_layout.py` (optional `overflow` stub). Added: `test_the_home_page_must_not_scroll_vertically_in_either_mode` (parametrized) and `test_the_large_display_check_measures_the_home_fit_windows`.

Validation: `pytest -q` -- **3015 passed**.

### 2026-10-27 - Move the home page keys to the left column

Side task, no batch tag: UI audit v6 row 10, moving the home page keys to the left column, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 10): the right column holds controls only. The heatmap preview card inside the form stack and the album "Only plays inside this calendar year are counted." hint explained the mode in the form. `templates/index.html` now has an `.index-hero__keys` wrapper under the strip with two keys, `data-mode-key="album"` (rows Year, Plays, Tracks; "How an album makes the list") and `data-mode-key="heatmap"` (the old card markup, `.hm-preview*` names kept as hooks). `static/js/heatmap.js` `switchModeHero` crossfades the keys with the strip through one mechanism (the inactive key gets `aria-hidden="true"` and `visibility:hidden`). `static/js/index.js` `updateKeyCounts` makes the album key's two numbers follow the steppers (singular at 1) and runs in the initial-state sync too, so restored form values show. `static/css/index.css` holds the `.index-key*` rules in `--index-scale` units; `static/css/heatmap.css` lost the card, key and facts rules. `_heatmap_form.html` lost the card. The mode switch moves the tabs 0px (row 2's floor). Contrast (computed, both themes): min 5.17:1 (labels), max 10.61:1; no new colour token. No Chromium-only CSS.

Deviations: (U21) supersedes brief item 6: below 860px both keys are hidden like the strip, and the year hint stays in the form as `field__help--phone` (shown below 860px, hidden from 860px up). (U22) the album key also ends with the 1px `--ss-border-divider` rule at the strip's width, like the heatmap key; the rule sits on each key, which stretch to the taller one, so it lands at the same y in both modes. The keys use a new attribute `data-mode-key`, not `data-mode-marks`, so the gate's `[data-mode-marks="{mode}"].is-active` locator keeps selecting only the strip.

Existing tests edited, by name: `tests/frontend/test_heatmap_pure_functions.py::_preview_text` (helper; reads the heatmap key from `templates/index.html`) and the `MODE_SWITCH` constant in `tests/scripts/dev/test_frontend_gate_layout.py` (new fields). Added: `test_the_form_stack_holds_no_key_and_each_mode_shows_its_own` (parametrized) and `test_a_phone_hides_the_keys_and_keeps_the_year_hint`, over new checks in `scripts/dev/_frontend_gate_layout.py` (`_home_key_failures`, `_phone_home_failures`, `_restored_key_text`).

Validation: `pytest -q` -- **3007 passed**.

### 2026-10-27 - Keep the home form centred without the jump

Side task, no batch tag: UI audit v6 row 2, keeping the home form centred without the jump, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 2): the form stack re-centred instantly on every height change, so the tabs jumped when the mode, the release scope or the thresholds changed. `static/css/index.css` gives `.index-form__inner` `min-height: var(--index-card-min, auto)`. `static/js/index.js` `syncFormMinHeight` measures the inner's height in the default album state (scope same/previous/all, thresholds closed) on load, after `document.fonts.ready`, after a resize that changes the resolved `max-width` and across the 860px breakpoint, and sets the floor only on desktop, so the Heatmap tab sits where the Album tab did. `playFlip` glides the remaining shift over 220ms (`translateY` to none, `cubic-bezier(.16, 1, .3, 1)`), skipped under reduced motion; it is triggered by the scope `change`, and by one capture-phase click listener for `.mode-pill` and `.disclosure__summary`. A page loaded in Heatmap mode re-measures the floor on its first switch to the album state. `scripts/dev/_frontend_gate_layout.py` gains `_measure_mode_switch_shift`, `_measure_heatmap_first_shift` and `_mode_switch_failures`, called from `check_large_display_scale_parity` at 1920x1063 (1px tolerance). No template or `heatmap.js` change; Firefox and Chromium both measured 0px; no new colour pairing.

Deviations: (R2-F1) the `min-height` rule sits inside the existing `min-width: 860px` block, so phones never pad the heatmap form to the album height. (R2-F3) the FLIP triggers are the scope `change` plus the capture-phase click listener (instead of editing `heatmap.js`), and the floor is re-measured in `playFlip`'s frame callback so the tab, scope and disclosure paths all work after a Heatmap-first load.

Existing tests edited, by name, in `tests/scripts/dev/test_frontend_gate_layout.py`: the helper `_run_large_display_check` (stubs the two new measurements). Added: `test_mode_switch_must_stay_put_when_the_mode_changes` and the parametrized `test_large_display_check_reports_a_mode_switch_that_moves` (album-first, heatmap-first).

Validation: `pytest -q` -- **2992 passed**.

### 2026-10-27 - Drop the sort-change toast

Side task, no batch tag: UI audit v6 row 9, dropping the sort-change toast, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 9): switching the leaderboard between play count and play time no longer raises a toast. The hidden-album count already shows in `#playtime-hidden-note`, so the toast repeated the page. `setLeaderboardMetric` in `static/js/results.js` loses its `showToast` block, the `hiddenCount` string built only for it, the now-unused `showNotification` parameter and an unused `dropped` binding; its three callers (the plays and playtime buttons, `setUnmatchedHidden`) are updated. `showToast` stays for the CSV, image export and error callers. No CSS and no new colour pairing.

Deviations: none.

Existing tests edited, by name, in `scripts/dev/results_behavior_tests.py`: `test_hidden_note_and_toast_carry_the_count_of_dropped_albums` (renamed `test_sort_switch_shows_the_count_in_the_note_and_no_toast`, extended to assert no toast, the subtitle and the column header), `test_hidden_note_stays_hidden_when_every_album_has_a_listening_time` (asserts no toast) and `test_hidden_note_counts_only_rows_the_ranking_alone_drops` (tuple unpack only).

Validation: `pytest -q` -- **2986 passed**.

### 2026-10-27 - Add a pause-animations footer control

Side task, no batch tag: UI audit v6 row 3, a pause-animations footer control, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 3): the header mark's bar animation can be paused (WCAG 2.2.2). A `.motion-toggle` button is the first child of `.page-footer-extras` in `templates/base.html` and reads "Pause animations" / "Play animations" with `aria-pressed`. `static/js/theme.js` toggles `data-motion="still"` on `<html>`, syncs the label from that attribute on load and persists the choice in localStorage `ss-motion` (write and remove in a try). The pre-paint script in `base.html` reads `ss-motion` in its own try so a paused page never flashes the animation. `static/css/shell.css` sets `animation: none` on the header mark's bars under `[data-motion="still"]`; the loading-page pinwheel is untouched. Under `prefers-reduced-motion` the bars are already still and the button keeps showing the stored state. The `.page-footer-extras:empty` rule is removed because the wrapper now always holds the button. The focus ring is 2px solid `--shell-accent` with offset 2px, as the header toggle. Contrast: rest text 5.17:1 light and 5.82:1 dark, focus ring 6.06:1 light and 8.14:1 dark (min 5.17, max 8.14); nothing is Chromium-only.

Deviations: (R3-F1) the README hover colour `--rocket-5` (#f0903a) is 2.24:1 on the light footer (#faf7f0), under the 4.5:1 contrast floor, so the contrast floor governs: light hover uses `--shell-accent` (#6a4baf, 6.06:1) and dark keeps `--rocket-5` (8.11:1). The header comment of `static/js/theme.js` also names the new toggle (R3-F2).

Existing tests edited, by name: `test_every_page_wraps_its_footer_extras` (the button opens the wrapper) and `test_every_page_sets_the_theme_before_first_paint` (runs the inline script in node with fake storage; skips when node is missing) in `tests/test_template_shell.py`.

Validation: `pytest -q` -- **2986 passed**.

### 2026-10-27 - Make the favicon follow the theme

Side task, no batch tag: UI audit v6 row 8, a theme-aware favicon with a touch icon and per-scheme theme-color, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 8, favicon option C): the favicon uses the site's own surfaces and purples and follows the browser colour scheme. `static/images/favicon.svg` (1841 bytes) holds a `<style>` block with plate `#faf7f0` / blades `#6a4baf`, and under `prefers-color-scheme: dark` plate `#181520` / blades `#b39dde`; the rounded 32x32 plate (`rx="8"`) carries the four existing blade paths scaled to .86. `favicon-16x16.png`, `favicon-32x32.png` and `favicon.ico` (16 + 32, PNG payloads, written by hand) are regenerated from the light variant, and `apple-touch-icon.png` (180x180, full-bleed cream plate, blades at .86) is new. `templates/base.html` `<head>` gains the apple-touch link and two `theme-color` metas (`#faf7f0` light, `#0e0c12` dark); the four existing icon links stay. Blade against plate contrast is 6.06:1 light and 7.54:1 dark (non-text minimum 3:1). The README's 7.8 kB `c2pa` block was already gone from the file. The PNGs were rendered with Playwright Chromium (Pillow is not a dependency); the SVG itself uses only plain CSS and a media query.

Deviations: none.

Existing tests edited, by name: `test_every_page_carries_the_shared_shell` in `tests/test_template_shell.py` (asserts the apple-touch link and both theme-color metas).

Validation: `pytest -q` -- **2986 passed**.

### 2026-10-27 - State the real total of a capped unmatched group

Side task, no batch tag: UI audit v6 row 9, a capped unmatched group states its real total, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (ruling U12, which supersedes U4): a group that shows fewer albums than it holds says so, "Showing the first 500 of N", with N the real total and no hard-coded 500. `group_unmatched_albums_with_totals` in `scrobblescope/unmatched.py` returns the groups, counts, metadata and a `totals` dict holding only the groups that show fewer than they hold; the total is the pre-slice length, and for the below-threshold group the larger of that and the `albums_below_threshold` stat, which `plays.select_albums` takes before its exclusion cap and which already reaches `progress.stats`, so the orchestrator is unchanged. `group_unmatched_albums` keeps its 3-tuple by delegating. `_render_unmatched_page` in `scrobblescope/routes/album_flow.py` passes `reason_totals`; `templates/unmatched.html` prints the line as a muted `text-xs` note under the group table, above the expander row. No new CSS and no new colour pairing (same muted token and surface as the group's other secondary text). Provisional wording until the impeccable pass; no real-data browser check was done.

Deviations: review finding R12-F1 was fixed at landing: the route test gained a case where the capped group is not the below-threshold group (520 no-match albums), so a template that looked the total up with a fixed `below_threshold` key fails.

Existing tests edited, by name: none; `test_unmatched_view_states_the_real_total_of_a_capped_group` (route, three cases) and the parametrized grouping-totals test in `tests/test_unmatched.py` are new.

Validation: `pytest -q` -- **2986 passed**.

### 2026-10-27 - Drop ellipses from progress and toast messages

Side task, no batch tag: UI audit v6 row 6, no ellipses in progress and toast copy, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: README row 6, no ellipses in the live status copy. Ruling U10 widened it from the loading page to the server's progress messages (`scrobblescope/orchestrator/`, `heatmap.py`, `jobs.py`) and the client strings in `static/js/` (`loading-progress.js`, `loading.js`, `heatmap.js`, `results.js`), including the escaped ellipses in `loading.js`: "Retrying" and "Opening the results page". "Initializing..." (and "Initializing heatmap...") became "Connecting to Last.fm" at all seven sites, the template's first phase line, `jobs._initial_progress`, both fallbacks in `loading-progress.js` and the heatmap start; the leaderboard toast reads "Creating leaderboard image". The pins in `scripts/dev/_frontend_gate_pipeline.py` follow the new strings. Remaining `...` in the tree are docstrings and comments only.

Deviations: none from the rulings. `tests/test_routes.py` is untouched: its "Working..." and "Fetching page 3..." are fixture strings passed to `jobs.advance`, not production copy. The `jobs.start` test uses the arbitrary message "Starting" instead of "Initializing heatmap...".

Existing tests edited, by name: `test_create_returns_unique_ids_and_a_pristine_job` and `test_reset_returns_the_job_to_its_initial_state_and_keeps_params` in `tests/test_jobs.py`, `test_start_clears_stats_phase_and_error_and_sets_the_message` (message string), `test_progress_callback_sends_correct_percentages` and the other `TestFetchAndProcessHeatmap` message asserts in `tests/test_heatmap.py`, `test_fetch_and_process_passes_progress_cb_to_lastfm` in `tests/services/test_orchestrator_fetch_and_process.py`, `test_fetch_spotify_misses_reports_search_progress`, `test_fetch_spotify_misses_reports_batch_progress` and `test_deezer_fallback_reports_progress_inside_its_band` in `tests/services/test_orchestrator_fetch_spotify.py` (full-message equality), and `test_a_failed_run_with_no_retry_still_says_the_results_page_opens` in `tests/frontend/test_heatmap_pure_functions.py`.

Validation: `pytest -q` -- **2978 passed**.

### 2026-10-27 - Rewrite the unmatched page headline and threshold header

Side task, no batch tag: UI audit v6 row 5, the unmatched page headline, subtitle, group description and threshold column header, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: the unmatched page headline says what happened to the albums (ruling U13): "Albums left out of <user>'s results" when nothing is listed, "Unmatched albums in <user>'s results" when an Include unmatched run lists some (`listed_count` > 0), deciding "listed" from result rows, not reason codes. The subtitle is the year and the total, "<year> middle dot <n> albums, grouped by reason" ("album" for 1), in both cases, so the listed / left-out clause and its `left_out` arithmetic are gone; `.unmatched-total` stays as a styling hook. The "Not enough listening" group's count header reads "Plays/trk" on phones and "Plays middle dot tracks" from 768px up, one line each (rulings U15 and U17), with `aria-label="Plays and tracks"` on the `th` so a screen reader never reads "trk"; the two forms are sibling spans toggled by a plain `min-width: 768px` media query in `static/css/unmatched.css` (no Chromium-only CSS), and the column widens at 768px and up for that panel only, while the phone width is unchanged so the album-title floors in the frontend gate hold. Its description drops the year and singularises: "Below N play(s) or M unique track(s)." (ruling U16). Other groups' header stays "Plays".

Deviations: none from the rulings. Measured in Firefox and Chromium at 320, 390, 768, 1024, 1440 and 1920px: the header is one line and not clipped at every width; the album title is 414px at 768 (U15's 454 was the narrower column's figure). Nothing durable pins the 768px swap or the nowrap, only the scratch probe; a gate check belongs with the later accessibility PR. `docs/design/RECONCILIATION.md` (verbatim snapshot) still describes the old count line.

Existing tests edited, by name: `test_unmatched_view_names_track_counts_only_on_the_threshold_panel` (parametrized to (10, 3) and (1, 1); header spans, aria-label, other panels' "Plays", description text); `test_unmatched_page_count_line_names_listed_and_left_out`, renamed `test_unmatched_page_headline_and_subtitle_follow_listed_count` and now asserting both h1 forms and the subtitle across listed, left-out, show-limit and one-album cases; `test_unmatched_view_subtitle_counts_the_albums_left_out`, renamed `test_unmatched_view_filter_bar_states_the_run_settings` (its subtitle assertion and parametrize dropped as covered by the headline test; filter-bar assertions kept).

Validation: `pytest -q` -- **2978 passed**.

### 2026-10-27 - Name the user and year in the results headline

Side task, no batch tag: UI audit v6 row 4, the results headline names the user and the run's year, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: the results h1 reads "<user>'s top albums of <year>", with the username keeping its accent span and `year` being the run's own year, never the current one. The subtitle `#results-ranking-subtitle` drops the year (ruling U11) and names the source: "Last.fm", a middle dot, then "Ranked by play count" or "Ranked by listening time". `setLeaderboardMetric` in `static/js/results.js` writes the same string on a sort change, so a sort switch and a fresh load agree. This wording is provisional until the impeccable pass. The old phrase "Top Last.fm albums for" appeared only in `templates/results.html`; no `<title>` or meta text repeated it. Deviations: `scripts/dev/results_behavior_tests.py` is touched beyond the brief (review finding R4-F1) so the sort check also covers the subtitle text, which the Python route test cannot see.

Existing tests edited, by name: `test_sort_updates_order_ranks_metrics_and_accessibility` in `scripts/dev/results_behavior_tests.py` (its fixture gains the subtitle element and each sort case asserts the subtitle text); one new parametrized test, `test_results_headline_names_user_and_year_and_subtitle_names_source` in `tests/test_routes.py`.

Validation: `pytest -q` -- **2978 passed**.

### 2026-10-27 - Set display headings in Degular 600

Side task, no batch tag: UI audit v6 row 1, headings in Degular 600 and two new hero headlines, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: the heading face is Degular at weight 600, replacing Orpheus Pro (the serif is dropped), and the two hero headlines read "The albums that owned your year." (album mode) and "A year of listening by the day." (heatmap mode). `--font-display` replaces `--font-serif` in `static/css/tailwind.src.css`; every heading rule and the `font-display` utility use weight 600, roman, -0.015em; accent spans keep the primary colour and lose italics (including the results h1 username); the spotlight rank is roman mono. The saved heatmap draws its headline in the same face and waits for it to load. Deviations: the token is `"degular", "akzidenz-grotesk-next-pro", sans-serif` (ruling U2), because the Adobe kit serves `degular` and has no `degular-display`, unlike the README's row 1. The `templates/index.html` value site in `config/docsync.toml` is removed (U9) because the heatmap headline no longer states the window. The frontend gate reads the drawn font string (R1-F2, narrowed by R1-F5): `_frontend_gate_theme.py` ignores style, weight and size tokens when comparing families and compares the drawn weight with the headline's computed weight; a dropped `document.fonts.load` wait is not detectable from the string and stays unchecked. Removing Orpheus Pro from the Adobe kit is the owner's later step.

Existing tests edited, by name: `tests/scripts/dev/test_tailwind_build_cli.py` (token line) and `tests/scripts/dev/test_frontend_gate_theme.py` (parametrized weighted and styled canvas font cases added).

Validation: `pytest -q` -- **2976 passed**.

### 2026-10-27 - Log a dead watchdog through log_failure

Side task, no batch tag: Codex review on PR #276 (P1, `scrobblescope/idle_exit.py`). `IdleWatch.run` logged a dying watchdog with `logger.exception`, which writes the exception text and a full traceback at ERROR; exception text can carry provider URLs or listener names, so the repository's rule (owner ruling 2026-09-29, `docs/agents/global-rules.md` Rule 6) is `utils.log_failure`: message plus exception class at ERROR, traceback at DEBUG. `run` now calls `log_failure` with the same message (and the `# noqa: BLE001 -- logged by log_failure` marker the other sites carry). New import edge `idle_exit -> utils` (no cycle: `utils` imports only `api_logging` and `config`), recorded in the `idle_exit.py` docstring, `.claude/SESSION_CONTEXT.md` and `docs/architecture/runtime-system.md`. `test_a_dying_watchdog_thread_is_logged` now asserts one ERROR record that names `RuntimeError`, does not contain the exception text and carries no `exc_info`; it failed against the old `logger.exception` call. The other logging calls in `idle_exit.py` log fixed text only (`logger.info` idle minutes, `logger.warning` for the setting name), and Task 1's seams in `worker.py` and `release_checks.py` add no logging. No test added.

Validation: `pytest -q` -- **2972 passed**.

### 2026-10-27 - Make the watchdog's environ argument required

Side task, no batch tag: Codacy flagged `watch_from_env(environ=os.environ)` in `scrobblescope/idle_exit.py` as Pylint W0102 (dangerous default value) and failed PR #276 with "1 new issue (0 max.)". Every caller already passes the mapping (`app.py` passes `os.environ`; `tests/test_idle_exit.py` passes dicts), so the default was never used. `environ` is now a required parameter with no default; nothing else changed. No test added.

Validation: `pytest -q` -- **2972 passed**.

### 2026-10-27 - Prove the watchdog is attached to the app and runs as a daemon

Side task, no batch tag: final-review fix round (rulings R-5.1 to R-5.4) of the Fly idle-exit plan, on `feat/fly-idle-exit`. A mutation run found that deleting `watch.attach(application)` in `create_app` passed the whole suite, although it would make requests stop renewing the timer and stop the machine 20 minutes after boot under an active user. The existing `create_app` idle-watch test now also sends one request through the returned app and checks that `IdleWatch.touch` ran exactly when the watch is enabled. New tests check that the watchdog thread is a daemon (a non-daemon thread would hold up worker shutdown) and that an idle machine stops within a minute of the window (a 3000-second check interval would hold it 50 more minutes). `DEPLOY.md` now quotes the two real expiry messages (`album_flow.py`) instead of an invented one. Not fixed, per the rulings: the `// 60` in a log line, and F-MAS-8's stale "always-on machines" premise (the finding's author decides).

Red proofs (one planted defect each): deleting `watch.attach(application)` fails `test_create_app_starts_the_idle_watch_only_when_the_env_var_is_set[20-1]`; `daemon=False` fails `test_start_runs_the_loop_on_a_daemon_thread`; `IDLE_CHECK_INTERVAL_SECONDS = 3000` fails `test_an_idle_machine_is_stopped_within_a_minute_of_the_window`. Each was restored by Edit.

Edited existing tests: `test_create_app_starts_the_idle_watch_only_when_the_env_var_is_set` (extended). Added: two tests in `tests/test_idle_exit.py`.

Validation: `pytest -q` -- **2972 passed**.

### 2026-10-27 - Let the app machine stop itself when idle

Side task, no batch tag: Task 4 of the Fly idle-exit plan, on `feat/fly-idle-exit`. Fly's autostop cannot see background jobs, so `fly.toml` now has `auto_stop_machines = 'off'`, no `min_machines_running`, and `[env] IDLE_EXIT_MINUTES = "20"`; the app exits with code 0 after 20 idle minutes and the next request starts the machine. `[deploy]`, `[build]` and `[[vm]]` are unchanged, and the `scrobblescope-db` app is untouched. Docs: DEPLOY.md gains an "Idle exit" section (what it does, why autostop is off, the results lifetime change from 2 hours to the idle window, production-only, off switch, rollback); `docs/architecture/runtime-system.md` gains the `idle_exit.py` node, its edges and a design bullet; SESSION_CONTEXT Sections 3 and 4 list `idle_exit.py`; the README hosting row and the AGENT_NOTES `REQUEST_CACHE` line name the idle exit. Exit-code probe (run before Task 1): gunicorn 23.0.0 on python:3.13-slim, a worker thread sending SIGTERM to its parent, logged "Handling signal: term" and "Shutting down: Master", and the last line was `EXIT=0`. Sweep of live documents for `min_machines_running`, `auto_stop_machines`, `always on`, `shared-cpu` and `machine sleep`: the only plain sibling copy was the AGENT_NOTES line; FINDINGS F-MAS-8 (title says "always-on machines") and the 2026-10-20 tranche spec are left as records.

Edited existing tests: none.

Validation: `pytest -q` -- **2970 passed**.

### 2026-10-27 - Restore the heading of the service-checks log entry

Side task, no batch tag: restore a heading lost in this branch's first commit, on `docs/findings-rotation-rule`, a branch off `main`.

Codex found on PR #275 that the first commit removed the heading of the 2026-10-25 service-checks entry and left its body under the "Rotate findings" entry, so the entry was in neither PLAYBOOK.md nor the log archive. The heading is back above its body, as on `origin/main`; no other entry is touched. A scan of the PLAYBOOK entries found no other body without a heading.

Deviations: none. Docs only; no code or test change; the test count is unchanged.

### 2026-10-27 - Update the Last updated line in every commit that touches its file

Side task, no batch tag: put the date rule in the commit checklist, on `docs/findings-rotation-rule`, a branch off `main`.

Owner ruling: always update the date when updates are made, in the findings and the other files that carry one. `AGENTS.md` "What to update after a WP or side-task commit" now has a bullet setting the `Last updated:` line of `docs/agents/FINDINGS.md` and `.claude/SESSION_CONTEXT.md` to the commit's date in the same commit (docsync does not derive it; FINDINGS.md had sat at 2026-09-21 for five weeks). The bullet also records that the tracked test-module count is measured with `git ls-tree` and edited by hand because `--fix --test-count N` writes the test count only (F-DOCSYNC-23), and that a log entry's test count is written in bold. PLAYBOOK's `Date:` line is left alone pending an owner decision. The `docs/architecture/documentation-tooling.md` diagram label that still said rotation happens at close-out now says it happens at `--fix` once the record is checked.

Deviations: `docs/agents/FINDINGS.md` and `.claude/SESSION_CONTEXT.md` are not touched, so their date lines are unchanged (FINDINGS.md already reads 2026-10-27). No code or test change; the test count is unchanged.

### 2026-10-27 - Rotate findings as soon as their record is checked

Side task, no batch tag: say in the live policy text when findings rotate, on `docs/findings-rotation-rule`, a branch off `main`.

Owner ruling: findings rotate out as soon as docsync runs, not at batch close-out. The code already did this (`doc_state_sync.py --fix` plans the rotation and moves a finding whose active entry carries a checked `RESOLVED` or `NO ACTION` record with a valid `**Completed:**` date; `--check` reports a checked finding left in the active file as drift); only the policy text was stale. `AGENTS.md` "Finding-Writing Rules" (opening sentence and item 3), the `docs/agents/FINDINGS.md` rotation-policy header and `docs/architecture/documentation-tooling.md` now say so, and item 3 adds that the resolving commit writes the lifecycle record and nobody checks a box for another author's finding.

Deviations: the brief's "(Rule 7)" reference is dropped, because no AGENTS.md rule states that principle. No code or test change; the test count is unchanged.

### 2026-10-27 - The pointer-list and slot-leak findings are filed

Side task, no batch tag: file two findings, on `docs/file-findings-docsync-24`, a branch off `main`.

- **Filed F-DOCSYNC-24 at P3.** The "Deferred / future-batch candidates" list mixes item 4 pointers (promoted or absorbed findings) with a resolved record, F-B18-12, that docsync never parses and that has no archived body. Checked before writing: the list has eleven bullets, not twelve, and F-FEATURE-2 is a pointer in the next section ("Feature preparation notes"), not in that list. The finding states the corrected counts.
- **Filed F-B23-65 at P3.** `admit()` in `scrobblescope/routes/admission.py` calls `jobs.create(params)` (line 47) after taking a slot (line 44) and outside its `try`, so a raise there leaks the slot. With the in-memory store little in `jobs.create` can raise, so the finding says so.
- **Scope:** documentation only. No code, test or gate changed, and no existing finding or pointer bullet was edited. Both are proposals, not built.

Validation: test count unchanged (docs only); `pytest -q` was not re-run.

### 2026-10-27 - F-B18-12 is archived with its recorded outcome

Side task, no batch tag: make the stale pointer F-B18-12 consistent, on `docs/file-findings-docsync-24`.

- **Archived F-B18-12.** Its active entry was transcribed from the original `FINDINGS.md` text (before `494f2c7`) and the pointer bullet's own RESOLVED 2026-08-25 paragraph, given `- [x] **Status:** RESOLVED` and `**Completed:** 2026-08-25`, and rotated to `docs/history/findings/FINDINGS_ARCHIVE.md` by `doc_state_sync.py --fix`. The bullet in "Deferred / future-batch candidates" is now a pointer to it.
- **Narrowed F-DOCSYNC-24.** Its F-B18-12 example is fixed. It stays open (P3): nothing checks that a pointer's target heading exists, and item 4 does not say which outcomes a pointer may carry.
- **Pointer targets checked.** F-B18-1, F-B18-7, F-MAS-2, F-FEATURE-2 and F-B18-12 all resolve to a heading in the active file or the archive.
- **Scope:** documentation only. No docsync code or AGENTS.md changed.

Validation: test count unchanged (docs only); `pytest -q` was not re-run.

### 2026-10-27 - The mechanical Last updated dates are filed

Side task, no batch tag: file one finding, on `docs/file-findings-docsync-24`, a branch off `main`.

- **Filed F-DOCSYNC-25 at P3.** The `Last updated:` lines of FINDINGS.md and SESSION_CONTEXT.md and PLAYBOOK's `Date:` line are set by hand and no docsync code reads them. The finding proposes deriving them from the newest dated Section 4 entry, names DOC027 as the next free code, and notes the sibling F-DOCSYNC-23 (module count). Owner ruling 2026-10-27: make the dates mechanical, file it as a follow-up.
- **Set FINDINGS.md `Last updated:` to 2026-10-27** (it read 2026-09-21), under the owner's standing rule to update the date when a file changes.
- **Scope:** documentation only. Nothing was built, and no docsync code, AGENTS.md or config changed.

Validation: test count unchanged (docs only); `pytest -q` was not re-run.

### 2026-10-27 - Patch the pip-audit advisories

Side task, no batch tag: patch the dependency advisories that `pip-audit` reported, on `chore/pip-advisories`, a branch off `main` (PR #273). Files changed: `requirements.txt` and `requirements-dev.txt` (pins only).

Owner intent: `pip-audit` reported 34 findings in 6 packages; it now reports none. Runtime bumps: aiohttp 3.14.3 to 3.14.4, multidict 6.7.1 to 6.9.1, Werkzeug 3.1.6 to 3.1.9, yarl 1.24.5 to 1.25.1 (aiohttp 3.14.4 needs yarl 1.25.1 or newer). Dev-only bumps: certifi 2026.10.19, urllib3 2.8.0, virtualenv 21.14.10 with distlib 0.4.4, filelock 4.2.4, platformdirs 4.13.6 and python-discovery 1.6.5, which virtualenv 21 pulls in.

Deviations: none. The commit for the pins (2acb3fab) landed without this entry; it is logged here.

Validation: a fresh venv install with `--only-binary=:all:` succeeded; `pip check` is clean; `pip-audit` is clean; Linux manylinux wheels exist for all 24 runtime packages; 2872 non-browser tests passed. Full suite pin unchanged: `pytest -q` -- **2952 passed**.

Edited existing tests: none.

### 2026-10-25 - Make two vacuous service checks honest

Side task, no batch tag: make two vacuous service checks honest and drop one redundant test, on `test/lean-suite-vacuous`, a branch off `main`.

Owner intent: one test per intended behaviour; fix a vacuous test in place and prove it red against a defect a user could ship. The stale-cache cleanup test only checked that some positive integer was passed, so a cleanup using the 365-day original-release TTL, or one that deleted fresh rows instead of stale ones, still passed; it now patches the TTL to 17 and asserts the whole normalized DELETE statement and `ttl == 17`. The out-of-bounds timestamp test only checked that the 2020 artist was absent, so a window that dropped every play passed; it now asserts the eligible artists are exactly `["Artist Y"]`, with a play count of 10 and no exclusions. `test_album_metadata_carries_its_provider_and_url` only read back the fields of a frozen dataclass it had just built, and the stored-row siblings already pin provider and url; it is deleted.

Deviations: none. `test_a_missing_correction_table_names_the_migration` and `test_original_release_lookup_without_a_connection_skips_the_query` are left as they are (the first is pinned exactly in `test_failure_logging.py`, the second by `assert_not_awaited`). Red proofs used scratch edits, restored byte-identical: `cleanup_stale_metadata` passing `ORIGINAL_RELEASE_TTL_DAYS` (`assert 365 == 17`), `Window.contains` always False (empty result, no `Artist Y`). The suite count falls by one (the deleted test).

Edited existing tests: `test_cleanup_stale_metadata_issues_delete` in `tests/services/test_orchestrator_fetch_spotify.py`; `test_fetch_top_albums_skips_out_of_bounds_timestamps` in `tests/services/test_lastfm_logic.py`. Deleted: `test_album_metadata_carries_its_provider_and_url` in `tests/services/test_enrichment.py`.

Validation: `pytest -q` -- **2952 passed**.

### 2026-10-25 - Replace vacuous shell and results checks with behaviour checks

Side task, no batch tag: replace four vacuous shell and results checks with behaviour checks, on `test/lean-suite-vacuous`, a branch off `main`.

Owner intent: one test per intended behaviour; fix a vacuous test in place and prove it red against a defect a user could ship. The inline-mark test passed `0 == 0` on a page that lost its header logo; it now also asserts at least one mark renders. The release-check poller test only grepped the script text, so a `skipped` job polled every 2 s forever and still passed; it is deleted and `ResultsBehaviorTests` gains a Chromium test that counts requests over 20 s of frozen-clock time (`running` keeps polling, `done`, `skipped`, `error` and an unknown status stop after one reply). The rotating-card test only checked that a height was written, on markup where both candidates were the same height; it now uses differing candidates and asserts the reserved height is at least the tall one's (80 px). The framework test lost its unreachable Bootstrap branch (every template is in `MIGRATED`) and a stale comment.

Deviations: none. Red proofs used scratch edits, restored byte-identical: base.html header mark removed (7 of 8 pages failed), `'skipped'` added to `LIVE_STATES` (`11 != 1`), `Math.max` to `Math.min` in results-spotlight.js (`0.0 not >= 80`). The suite count falls by one (the deleted test).

Edited existing tests: `test_every_inline_mark_is_wrapped_for_the_css_animation` and `test_each_page_loads_the_framework_its_markup_is_written_for` in `tests/test_template_shell.py`; `test_a_rotating_card_reserves_its_tallest_height` in `scripts/dev/results_behavior_tests.py`. Deleted: `test_the_release_check_poller_stops_on_every_terminal_state`. Added: `test_the_release_check_poller_stops_on_every_status_that_is_not_live`.

Validation: `pytest -q` -- **2953 passed**.

### 2026-10-25 - Make two vacuous domain checks honest

Side task, no batch tag: make two vacuous domain checks honest, on `test/lean-suite-vacuous`, a branch off `main`.

Owner intent: test for the intended function, not the written function; one test per intended behaviour. `test_normalize_name_unicode_preserved` promised that non-Latin text survives but assigned `album` and never asserted it, and its input was one accented artist; it now asserts exact equality on both halves with accented Latin names (Bjork/Debut, Sigur Ros/Agaetis Byrjun, with their diacritics), so an album-only ASCII strip fails it. In `test_cover_wash_index_is_stable_and_ignores_spelling_noise` the loop that called the pure function five times could not fail unless `cover_wash_index` kept call-count state; it is deleted and the docstring no longer promises repetition, since `test_cover_wash_index_is_pinned_across_processes` guards stability.

Deviations: none. `test_normalize_name_remastered_suffix` was reviewed and left as is.

Edited existing tests: `test_normalize_name_unicode_preserved` and `test_cover_wash_index_is_stable_and_ignores_spelling_noise` in `tests/test_domain.py`.

Validation: `pytest -q` -- **2954 passed**.

### 2026-10-25 - Ignore the owner's local files

Side task, no batch tag: ignore the owner's local files and commit `.graphifyignore`, on `chore/ignore-local-files`, a branch stacked on `fix/album-matching` (PR #270).

Owner intent: "RE: .gitignore, yes to all." `.gitignore` gains one block for the owner's handoffs (`scrobblescope-handoff-*.md`, `scratchpad_owner.md`), `/progress_copy.md`, `docs/superpowers/plans/plan.md`, the plans' `architecture-review-*.html`, `docs/history/reports/*.htm` and `Architecture Review*.html`, two audit files and `.github/skills/`. `.graphifyignore` is committed as the owner wrote it. The scripts under `scripts/dev/mutation_*` and their test stay visible.

Deviations: the brief's directory and `*.html` patterns would have ignored four files git already tracks (one handoff, three exported reports), so the patterns are narrowed to the untracked names; `git ls-files -ci --exclude-standard` now lists only `.superpowers/sdd/.gitignore`, which was ignored before. No rule in AGENTS.md, `docs/agents/` or `config/docsync.toml` expects the handoffs to be visible to git.

Edited existing tests: none.

Validation: `pytest -q` -- **2941 passed**.

### 2026-10-25 - Share one Spotify breaker across a job's phases

Side task, no batch tag: fix the Codex review P2 (round 2) on PR #270, where the stamping calls and the miss fetch each opened their own Spotify breaker, on `fix/album-matching`, stacked on PR #269.

Owner intent: a Retry-After above the cap seen while stamping old cached rows tripped only the stamping breaker, so the job's cache misses then searched Spotify as if nothing had happened. `process_albums` now opens one `spotify_job_breaker()` block around the cache lookup, the partition and the miss fetch, and `spotify_job_breaker()` yields the already active breaker unchanged when it is nested (no new breaker, no reset, no log), so the inner blocks in the stamping and the miss fetch reuse the job's. A different job runs in its own context and still gets its own breaker. New tests: `test_a_breaker_tripped_while_stamping_stops_the_jobs_searches` (red before: the miss searched Spotify) and `test_a_nested_job_breaker_block_shares_the_outer_breaker`.

Deviations: none.

Edited existing tests: none. The `_StampingSpotify` fake gained a `trips` option, and its search now refuses at entry on a tripped breaker as the real search does; the existing tests that use it never trip it and still pass unchanged.

Validation: `pytest -q` -- **2954 passed**.

### 2026-10-25 - Make the non-Latin normalization test honest

Side task, no batch tag: make `test_normalize_name_and_track_name_agree_on_non_latin` check what its name says, on `fix/album-matching`, stacked on PR #269.

Owner intent: the owner found the docstring claimed Japanese katakana while the album half normalized the Latin title "BABYMETAL", `album_key` was never asserted and the artist half's length check held for any implementation. The test now passes the katakana title as the album too and asserts the album key and the track key are equal to each other and to the katakana text with the full-width exclamation marks stripped (`\u` escapes, ASCII-only source). Proof it is no longer vacuous: a scratch edit of `normalize_name` that dropped non-ASCII characters from the album made it fail; restored byte-identical, it passes. No production code changed.

Deviations: none.

Edited existing tests: `test_normalize_name_and_track_name_agree_on_non_latin`, which still guards the NFKD + ascii-encode regression.

Validation: `pytest -q` -- **2952 passed**.

### 2026-10-25 - Keep album keys stable under repeated normalization

Side task, no batch tag: fix the Codex review P2 on PR #270, where `normalize_name` was not idempotent, on `fix/album-matching`, stacked on PR #269.

Owner intent: both provider searches normalize the key they are given again, so a key must come back unchanged. The empty-remainder fallback wrote each pipe as `%7c`, and a second pass turned `%7c` into `7c`, so an album titled "|" (or "EP |") could never match. The fallback now writes each pipe as `^`, which is ASCII punctuation, so the fallback text stays made of punctuation, whitespace and edition words only and a second normalization returns it unchanged. The docstrings of `normalize_name` and `format_album_key` say so. No live doc stated the old escape.

Deviations: none.

Edited existing tests: `test_normalize_name_empty_remainder_keeps_distinct_pipe_free_identity` now expects `^^` for "||" where it expected `%7c%7c`; it still asserts distinct, non-empty, pipe-free keys. Added `test_normalize_name_is_idempotent`.

Validation: `pytest -q` -- **2952 passed**.
