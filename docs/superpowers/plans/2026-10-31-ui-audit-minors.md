# UI Audit Minors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the triaged UI audit Minors: a safer streamgraph hover panel, consistent chart and key spacing, and sturdier gate helpers.

**Architecture:** Follow the approved [design](../specs/2026-10-31-ui-audit-minors-design.md). No schema change, no new dependency, no new module. Each task is one atomic commit.

**Tech Stack:** Existing browser JavaScript, SVG, CSS, Python pytest and the repository Playwright gate.

## Global Constraints

- The design owns the behaviour, the numbers and the owner's rulings C1-C6. Read it before a task brief; the task text here names tests and commands, not implementation code.
- The SDD workspace `constraints.md` binds every task: Rules R1-R14 (landing, tests, scope, PREVIEW) and the Gates block. This plan cites them and does not restate them.
- Lean tests (R9): extend an existing test before adding one; red against the unchanged code, then green; docstrings in GIVEN/WHEN/THEN form; no wording or constant pins. "No need to excessively guard every UI element" (owner, 2026-10-31).
- A "gate check" below is a function in `scripts/dev/_frontend_gate_*.py` run by `frontend_gate.py`. Its red run is the gate against the unchanged runtime; its green run is the gate after the change.
- PREVIEW tasks follow R14: Firefox screenshots, light and dark, before and after, saved to the scratch directory and listed in the report; the controller shows them to the owner; the task lands only on the owner's word. A rejected one is dropped, not reworked.
- Commit subjects are exact. The landing follows R1-R5 (PLAYBOOK, Section 4 entry, docsync, Validation line); `static/css/tailwind.css` is also Touched when the drift hook rewrites it. A code-phase patch never carries `tailwind.css`: the hook can rewrite it for any CSS or JS task (so for T3, T4, T7 and T8 in the same wave), and the landing, one task at a time, regenerates it and stages it with that task.

## Dispatch

Wave rule: two tasks in the same wave never share a file. `After` is "the predecessor has landed", because the next code phase is cut from the landed head.

| Wave | Tasks (peak agents) | Why this order |
|---|---|---|
| 1 | T1 font parser, T2 pause cleanup, T3 `desktop` query, T4 footer gap (4 agents) | Unrelated files; none is PREVIEW |
| 2 | T5 stream gate hygiene, T6 panel header 13px (2 agents) | T5 opens `_frontend_gate_stream.py` first; T6 is css only |
| 3 | T7 panel behaviour, T8 key ramp spacing (2 agents) | T7 follows T5 (same gate file); T8 follows T6 (same `heatmap.css`) |
| 4 | T9 month labels (1 agent) | Follows T7 (`heatmap.js` and the stream gate) |
| 5 | T10 centring (1 agent) | Follows T9 (`heatmap.js`); the owner decides T9 first |
| 6 | T11 plan record (serial) | Ticks boxes and records commits |

Peak: 4 agents, in wave 1. Waves 2-5 are at most 2, which also keeps the browser lock short.

Landing order: T1, T2, T3, T4, T5, T7 land as their code phases finish (not PREVIEW). T6, T8, T9 and T10 land only after the owner's word on their screenshots. A PREVIEW task that waits blocks only the tasks that name it in `After`: T10 waits for the owner's decision on T9 (landed or dropped) so its code phase starts from the right head, and T8 for T6 for the same reason. All landings run one at a time in `C:/ssw/u8` (constraints, Shared files).

Gates: see the `## Gates` block in the workspace `constraints.md` (`suite-*`, `pre-commit`, `docsync-check`, and `frontend-gate` or `results-behavior` where the task says). Do not copy it.

## Delivery sequence

- [x] Task 1: keep a numeric font weight after `normal`.
- [x] Task 2: clear the stored pause choice on every exit.
- [ ] Task 3: reuse the `desktop` media query in `index.js`.
- [ ] Task 4: share the footer gap as one custom property.
- [x] Task 5: stream gate reports an empty stream and always cleans up.
- [ ] Task 6 (PREVIEW): scrubber panel header at 13px.
- [x] Task 7: dismissible, focus-safe stream panel.
- [ ] Task 8 (PREVIEW): heatmap key ramp spacing at the reference's 12px.
- [ ] Task 9 (PREVIEW): stream month labels match the heatmap's.
- [ ] Task 10 (PREVIEW): centre the stream in its plot band.
- [ ] Task 11: record the execution.

## Task 1: Keep a numeric font weight after `normal`

**Wave:** 1. **After:** none. **Mode:** code.
**Touches:** `scripts/dev/_frontend_gate_theme.py`, `tests/scripts/dev/test_frontend_gate_theme.py`.
**Commit:** `fix(gate): Keep a numeric font weight when normal follows it`.
**Closes:** audit row 3.

**Behaviour:** In `_split_canvas_font`, a `normal` token no longer resets an earlier numeric weight. `600 normal 26px x` gives weight 600; `bold` still gives 700; a string with no weight token still gives 400. `_NAMED_WEIGHTS` keeps `bold` only.

**Extends:** the parametrized `test_a_saved_headline_drawn_at_another_weight_is_reported` (the `("drawn", "family", "drawn_weight")` cases).

- [x] Add the case `("600 normal 18px x", "x", "600")` to that parametrize list. Keep `("normal 18px x", "x", "400")` as the neutral check (it cannot fail alone, which is why the new case carries the defect).
- [x] RED: `"<PY>" -m pytest -q -p no:cacheprovider tests/scripts/dev/test_frontend_gate_theme.py -k "another_weight"` fails on the new case with `400 != 600` (or the weight reported as 400). GREEN: the same command passes after the change. Quote both lines.
- [x] Acceptance: the whole file `tests/scripts/dev/test_frontend_gate_theme.py` passes; the three `suite-*` gates, `pre-commit` and `docsync-check` pass (this commit changes only `scripts/dev` and `tests`, so `frontend-gate` is not required).

## Task 2: Clear the stored pause choice on every exit

**Wave:** 1. **After:** none. **Mode:** code.
**Touches:** `scripts/dev/_frontend_gate_spotlight_photo.py`, `tests/scripts/dev/test_frontend_gate_spotlight_photo.py`.
**Commit:** `fix(gate): Clear the stored pause choice on every exit`.
**Closes:** audit row 40.

**Behaviour:** `_pause_hold_failures` stores `ss-motion=still` for the probe page through an init script (`_STORE_PAUSE_JS`); today only the Play click clears it. After the change the probe removes the stored `ss-motion` key in its own `finally`, before it closes the page, whichever path it took. A cleanup that itself raises must not hide the original failure: if the page never navigated there is nothing stored, so the cleanup is skipped or tolerates that case; the implementer picks the shorter of the two and says which. The test asserts the behaviour (the `ss-motion` key is removed before the page closes), not the exact script string.

**Extends:** `test_the_hold_check_focuses_then_hovers_and_counts_the_periods`, whose mock page already records `add_init_script`, `click` and `evaluate` calls. Add one new test beside it, `test_an_early_return_leaves_no_stored_pause_choice`, because the existing test drives the full path (Play clicked) and the early return is a different scenario that cannot be a parametrization of it without hiding which assertion guards what.

- [x] New test, GIVEN `_open_spotlight_card` returns an error string, WHEN `_pause_hold_failures` runs on the mock page, THEN it returns that error and the page evaluated a removal of `ss-motion` (found by the key name in the mock's `evaluate` calls, without pinning the script text) before closing.
- [x] RED against the unchanged helper: the removal call is absent. GREEN after the change. Quote both. The existing test still passes unchanged.
- [x] Acceptance: `tests/scripts/dev/test_frontend_gate_spotlight_photo.py` passes; `suite-*`, `pre-commit`, `docsync-check` pass. This commit touches `scripts/dev/_frontend_gate*`, so `frontend-gate` also passes.

## Task 3: Reuse the `desktop` media query in `index.js`

**Wave:** 1. **After:** none. **Mode:** code.
**Touches:** `static/js/index.js`.
**Commit:** `refactor(ui): Reuse the desktop media query in index.js`.
**Closes:** audit row 13.

**Behaviour:** `positionForm` reads `desktop.matches` instead of building `matchMedia('(min-width: 860px)')` again. The `const desktop` declaration moves above `positionForm` so it is plainly initialised before any call (every call is at or after the `ResizeObserver` setup today, so this is for the reader, not a fix). No behaviour change, so no new test (R9, C6): the home layout checks of the frontend gate already cross 860px.

- [ ] `git grep -n "min-width: 860px" static/js/index.js` shows the query once.
- [ ] Acceptance: `frontend-gate` passes (record its last line); `suite-*`, `pre-commit`, `docsync-check` pass. No `results-behavior` run needed (the commit touches neither `results.html`, `results.js` nor the behaviour tests).

## Task 4: Share the footer gap as one custom property

**Wave:** 1. **After:** none. **Mode:** code.
**Touches:** `static/css/shell.css`, `static/css/index.css`.
**Commit:** `refactor(css): Share the footer gap as one custom property`.
**Closes:** audit row 17.

**Behaviour:** Declare one custom property for the 1.5rem footer gap in `shell.css`'s `:root` block. `.page-footer-extras` (bottom padding) and `.index-grid .index-hero` (`padding-bottom`) both read it; the comment in `index.css` that names "`static/css/shell.css` (.page-footer-extras, 1.5rem)" now names the property. The computed values do not change (1.5rem = 24px at the root size). No new test: the gate's existing equality check (`footerGap` against the pause button's `gap` in `_measure_home_pause`) is the guard and stays untouched.

- [ ] The two footer-gap declarations (`.page-footer-extras` bottom padding, `.index-grid .index-hero` `padding-bottom`) read the custom property, and the property is declared once. `git grep -n "1.5rem"` still shows unrelated uses, and `shell.css` repeats `1.5rem` in the mobile theme slot's `padding: 1rem 1rem 1.5rem`; those are left alone, so the check is by reading those two declarations, not by counting hits.
- [ ] Acceptance: `frontend-gate` passes and its layout section reports the same pause gap as before (quote the line); `suite-*`, `pre-commit` (re-stage any `tailwind.css` rewrite), `docsync-check` pass.

## Task 5: Stream gate reports an empty stream and always cleans up

**Wave:** 2. **After:** none (starts the stream gate file). **Mode:** code.
**Touches:** `scripts/dev/_frontend_gate_stream.py`.
**Commit:** `fix(gate): Report an empty stream and always run its cleanup`.
**Closes:** audit rows 23 and 30. Merged into one task because both are small fixes to the same file with no browser-behaviour change; the reason to keep them out of Task 7 is L1 (one concern per commit).

**Behaviour (row 23):** In `_paint_failures`, when `reading["fills"]` is empty the contrast line (`min(ratios)`, `max(ratios)`) is not evaluated, and the existing failure "the stream draws no artist layers in the {theme} theme" is returned instead of an exception.

**Behaviour (row 30):** The `finally` in `check_stream_is_one_keyboard_tab_stop` runs all three cleanup steps (remove the sentinel, restore the viewport, delete the seeded job) even when an earlier one raises; the first error still surfaces.

No test file exists for this module and none is added (C6, "no need to excessively guard every UI element"). The evidence is a temporary probe, not retained:

- [x] RED/GREEN for row 23: call `_paint_failures` with a hand-built reading whose `fills` is empty (a one-off script in the scratch directory): it raises `ValueError` before the change and returns the named failure after. Quote both.
- [x] Row 30: read the changed `finally` against the three steps; show with the same kind of probe (a stub page whose first evaluate raises) that the viewport restore and `jobs.delete` still run after the change. Quote the probe output.
- [x] Acceptance: `frontend-gate` passes (its `[stream ...]` lines unchanged); `suite-*`, `pre-commit`, `docsync-check` pass.

## Task 6 (PREVIEW): Scrubber panel header at 13px

**Wave:** 2. **After:** none. **Mode:** code.
**Touches:** `static/css/heatmap.css`.
**Commit:** `fix(ui): Set the scrubber panel header to 13px`.
**Closes:** audit row 25.

**Behaviour:** `.stream-panel-header` changes from `--text-label-sm` (0.75rem = 12px, `tailwind.src.css`) to `--text-label` (0.8125rem = 13px, same file), the size the design reference gives (`.superpowers/sdd/2026-10-27-ui-audit-v6/design/reference-v6-notes.md`, line 107: stream panel "header 13px muted"). The header is `white-space: nowrap; width: max-content`, so the panel's measured width, and therefore where `showWeek` flips or lifts it, grows slightly; the stream gate's panel checks (inside the chart, fixed side at the checked weeks) must still pass. If one fails, report it; do not loosen it.

**Tests:** none new (a font-size value is not a behaviour to pin; C6). The existing stream hover checks are the guard.

- [ ] PREVIEW (R14): save before and after Firefox screenshots, light and dark, of the panel shown at week 30 and week 40 to the scratch directory (suffix `-6`); list the paths in the report.
- [ ] Report the computed header font size from the browser (13px expected) and the contrast of the header colour (`--stream-muted`) against the panel in both themes (min and max; the colour is unchanged, so this must equal the existing `[stream colours]` label line).
- [ ] Acceptance: `frontend-gate` passes; `suite-*`, `pre-commit`, `docsync-check` pass. Lands only on the owner's word.

## Task 7: Dismissible, focus-safe stream panel

**Wave:** 3. **After:** Task 5. **Mode:** code.
**Touches:** `static/js/heatmap.js`, `scripts/dev/_frontend_gate_stream.py`.
**Commit:** `fix(ui): Make the stream panel dismissible and focus-safe`.
**Closes:** audit rows 1, 26, 27, 28 and 29. One task because rows 26-28 live in the same handlers (`handleStreamFocus`, `handleStreamBlur`, `handleStreamKey`, the `pointerleave` wiring) and rows 29 and 1 are the gate check and the typo in that same code; splitting would have two commits fight over the same lines.

**Behaviour:**

- Row 1: `showWeek`'s guard reads `state.shown && state.shown.week`.
- Keyboard focus (rows 26 and 28), decided once: the stream svg matches `:focus-visible` (owner ruling C11). The svg is `tabindex=0`, so a click or tap focuses it too; that focus is not keyboard focus. The heatmap cells already ask the same question the same way (`syncFocusIndicators`, `matches(':focus-visible')`). Chromium turns `:focus-visible` on for a clicked element at the first key without a focus event (the comment at `syncFocusIndicators`), so the live region is also re-decided in `handleStreamKey`, not only in `handleStreamFocus`.
- Row 26: the panel is a live region (`aria-live="polite"`) only while the stream has keyboard focus: set when it gains keyboard focus (before `showStreamCursor` fills the panel), removed when it loses focus, absent at draw. A pointer scrub, or a click or tap focus, announces nothing. The first announcement on focus is not asserted (screen readers differ); the gate checks the attribute only.
- Row 27: Escape, pressed with the stream focused, hides the panel, ring, guide and dimming, keeps focus, and stores the keyboard position first, so the next arrow key shows the panel again from the same week and layer. It does not `preventDefault` for other keys.
- Row 28: `pointerleave` and `pointercancel` clear the week only when the stream does not have keyboard focus (as defined above). With keyboard focus, the shown week stays and the keys continue from it. After a click or tap, the leave still clears the panel, ring and dimming.
- Row 29: the keyboard check records whether each arrow press reached `window` with `defaultPrevented` set, and fails when one did not.

**Extends (no new gate function):** `check_stream_is_one_keyboard_tab_stop` (rows 26-29), and `check_stream_hover_shows_panel_and_ring` (or the existing hover check that reads `_READ_HOVER_JS`; the implementer names the one it extends) for the row 26 unfocused case.

- [x] Focus method (C11): the gate's existing `page.locator(_STREAM).focus()` calls (`_frontend_gate_stream.py` lines about 445, 1328 and 1385) are programmatic, and whether script focus matches `:focus-visible` depends on the browser's last-interaction rule, which reading cannot settle. In each browser the gate runs, read `matches(':focus-visible')` on the stream right after the existing `.focus()` call, in the sequences the checks use (a prior `mouse.move` only, no click). If it is false anywhere, focus that step with `page.keyboard.press("Tab")` instead (the check's first step already tabs in) and say so in the report. Do not weaken the rule to make `.focus()` pass.
- [x] Row 29, in the keyboard check: install a bubbling `keydown` listener on `window` before the first press and keep it through the whole check, so it covers the dense-week-end presses and every key of the `_KEY_STEPS` walk (Home, End and the edge clamps included); assert `defaultPrevented` was true for each. Failure text names the key.
- [x] Click then leave (C11, new case, in the keyboard check or the hover check, the implementer says which): with the stream blurred, `page.locator(_STREAM).click()` on a plotted point, then `page.mouse.move(*_OUTSIDE)`; assert the panel, ring, guide and dimming are cleared (the `_cleared_after` helper, "after a click and a pointer leave") and `aria-live` on `#stream-panel` is not `polite`. Against the unchanged `heatmap.js` this fails on `aria-live` (it is always `polite` today); the panel clear already holds there and is the guard against a "any focus" rule, which would leave it up.
- [x] Row 27: after the dense-week-end step, press Escape: the panel is hidden (`hidden` attribute or no `.stream-panel-row` visible), the ring and guide are gone, `document.activeElement` is still the stream; press `ArrowRight` and assert the panel shows week 7 (one right of the stored week 6) with the same row.
- [x] Row 28: change the existing "after pointer leave" step. The sequence `_hover(page, _START_WEEK)`, `page.mouse.move(*_OUTSIDE)`, `ArrowUp` runs with the stream focused, so after the fix the panel stays on week `_START_WEEK` (26) after the mouse leaves, and `ArrowUp` moves from the pointer's row: expected `_step_failures(page, _START_WEEK, <pointer row - 1, minimum 0>, ...)` where the pointer row is `rows["hovered"]` from `_PANEL_ROWS_JS` read right after the hover. The old expectation (week 6, row `_ARTIST_COUNT - 1`) was the defect. Keep a separate unfocused case: with the stream blurred, a pointer leave still clears everything (the existing `_cleared_after` helper).
- [x] Row 26: unfocused pointer hover, `aria-live` on `#stream-panel` is not `polite`; after `Tab` into the stream it is `polite`; after the blur it is not.
- [x] RED: write the new assertions first, run `"<PY>" C:/ssw/tools/with_browser_lock.py "<PY>" scripts/dev/frontend_gate.py` against the unchanged `heatmap.js`; quote the failing lines (one per row 26, 27, 28, and the click-then-leave case). For row 29, prove the check can fail with a throwaway edit that removes `event.preventDefault()` in `handleStreamKey` in the scratch worktree only; quote the failing line and revert it before the patch.
- [x] GREEN: the same gate passes after the `heatmap.js` change. Quote the last line.
- [x] Acceptance: `frontend-gate` passes (both engines, all profiles); `suite-*`, `pre-commit` (re-stage hook rewrites), `docsync-check` pass. The pure `streamKeyTarget` tests in `tests/frontend/test_heatmap_pure_functions.py` are unchanged and still pass (the key map is not touched).

## Task 8 (PREVIEW): Heatmap key ramp spacing at the reference's 12px

**Wave:** 3. **After:** Task 6 (same file, `static/css/heatmap.css`). **Mode:** code.
**Touches:** `static/css/heatmap.css`.
**Commit:** `fix(ui): Tighten the heatmap key's ramp spacing`.
**Closes:** audit row 5.

**Behaviour:** Remove `.hm-preview__ramp`'s own `margin-top` (`calc(0.875rem * var(--index-scale, 1))`). The ramp is a grid child of `.index-key`, whose `gap` is `calc(0.75rem * var(--index-scale, 1))`, so the space under the last row becomes that gap alone: 12px at scale 1 and about 12.9px at 1920 (scale 1.075), where it is `1.625rem * scale` (26px at scale 1, about 28px at 1920) today. 12px is the reference's `display:grid; gap:12px` (`.superpowers/sdd/2026-10-27-ui-audit-v6/design/reference-v6-notes.md`, line 20); the page's own scaling rule is kept. The ramp's height is untouched.

**Tests:** none new (C6). The home layout checks of the frontend gate must still pass; the key's height changes by about 14px and the album key (`data-mode-key="album"`) shares the grid track, so the gate's stable-height checks are the guard.

- [ ] PREVIEW (R14): before and after Firefox screenshots of the home page in heatmap mode, light and dark, at 1920x1080 and 1280x720; scratch suffix `-8`. Report the measured pixel gap between the last key row and the ramp (before about 28px and after about 12.9px at 1920).
- [ ] Acceptance: `frontend-gate` passes; `suite-*`, `pre-commit`, `docsync-check` pass. Lands only on the owner's word.

## Task 9 (PREVIEW): Stream month labels match the heatmap's

**Wave:** 4. **After:** Task 7. **Mode:** code.
**Touches:** `static/js/heatmap.js`, `scripts/dev/_frontend_gate_stream.py`.
**Commit:** `fix(ui): Match the stream month labels to the heatmap's`.
**Closes:** owner ruling C2.

**Behaviour:** The stream's bottom month labels, created in `drawStream`, get the same four label attributes as the heatmap's month labels: `font-size` 9.5, `LABEL_FONT_STACK`, `font-variant` small-caps, `letter-spacing` 0.12em. The text and `x` stay as now (cloned from the heatmap's labels). The font size was already equal in viewBox units and in rendered size (both SVGs share `svgWidth` and are `width: 100%` in `#heatmap-grid`); what differs on screen is small capitals and tracking, which the change adds. The saved image changes too (C12): `streamAsImage` overwrites only `font-family` and copies `font-variant` and `letter-spacing`, so the saved stream's month labels gain small capitals and tracking, as the saved heatmap's already have. That is the wanted outcome; the export code needs no edit, but it is checked.

**Extends:** the stream alignment reading (`_READ_ALIGNMENT_JS`, which already returns `months` and `gridMonths` per label) and `_alignment_failures` in `check_stream_aligns_with_grid_columns`. Add to the reading each label's `fontFamily`, `fontVariant`, `letterSpacing` and rendered font size in CSS px (computed `font-size` times the SVG's `clientWidth / viewBox width`), and fail when the stream's labels differ from the heatmap's on any of the four. The comparison fails closed: if `gridMonths` is empty, or the two label counts differ, it returns a named failure before comparing per label, never an index error.

- [ ] RED: add the comparison, run the frontend gate against the unchanged `heatmap.js`; quote the failure (variant and tracking differ). GREEN: passes after the change. Quote the last line.
- [ ] PREVIEW (R14): before and after Firefox screenshots, light and dark, of the heatmap with its stream at 1920x1080 and 1280x720, scratch suffix `-9`; report the rendered label size in CSS px at each width for both charts. State whether the end-anchored last label still sits inside the SVG (the existing `inside` field).
- [ ] PREVIEW, saved image (C12): save the stream's image through the page's save control (or run `streamAsImage` the way `check_stream_is_in_saved_image` does), crop the month-label row, and save the crop, light and dark, before and after, at 1920x1080 (suffix `-9`). Report that the labels show small capitals and tracking and that the last label is not clipped at the image edge.
- [ ] Acceptance: `frontend-gate` passes, including `check_stream_is_in_saved_image` (green, last label unclipped); `suite-*`, `pre-commit`, `docsync-check` pass. Lands only on the owner's word. If rejected, drop the task; Task 10 then starts from the head without it.

## Task 10 (PREVIEW): Centre the stream in its plot band

**Wave:** 5. **After:** Task 9. **Mode:** code.
**Touches:** `static/js/heatmap.js`, `tests/frontend/test_heatmap_pure_functions.py`.
**Commit:** `fix(ui): Centre the streamgraph in its plot band`.
**Closes:** owner ruling C3.

**Behaviour:** `streamFit` always shifts the baseline so the outer envelope (`high` and `low`, which already include the halo and Bezier-control margins) is centred on the band's centre line: after the shift `high` and `-low` are equal. The scale rule is unchanged: the tallest week is `STREAM_PEAK` tall, capped so the extent fits `STREAM_BAND`. The current rule (shift only when the stack overflows) is replaced, not kept as a branch.

**Extends (edits, not adds):** `test_stream_stack_stays_inside_the_band`. Its `moved` flag and the `ordinary-data-keeps-its-look` id assert that ordinary data is left unmoved; under C3 that is the defect. Replace the `moved` parameter with a `capped` flag (the scale is the extent cap, not the peak scale) and assert, for every case, that the extent is centred (`low + high` is zero within 1e-9) as well as inside the band. `capped=True` is for the case whose scale is the extent cap: `scale-capped-by-the-stack-extent` for certain. For the other three, the implementer reads `fit["scale"]` against `streamScale(totals)` once on the unchanged code (the shift does not change the scale) and sets `capped` where they differ, naming the result in the report; the plan does not guess it. Add `residual` to the test's `streamFit` call for one case (the existing `test_stream_fit_contains_symmetric_context_halo` parametrization shows a residual that exercises the halo), or add that residual case to the centring assertion, so a shift computed without the halo and Bezier margins fails. Rename the ids to match. `test_stream_fit_contains_symmetric_context_halo` already asserts the halo bounds stay inside the band and must pass unchanged. Other pure tests that hard-code a baseline (`test_smoothed_stream_encloses_artists_without_clipping`, the `hitAt` tests) are run and, where the shift moves a hand-derived number, corrected from first principles, never by copying the new output.

- [ ] RED: edit the test first and run `"<PY>" -m pytest -q -p no:cacheprovider tests/frontend/test_heatmap_pure_functions.py -k "inside_the_band"`; it fails on the ordinary-data case (extent not centred). GREEN: passes after the change. Quote both.
- [ ] Run the whole file `tests/frontend/test_heatmap_pure_functions.py`; list any other test that needed a corrected number and why.
- [ ] PREVIEW (R14): before and after Firefox screenshots, light and dark, of the stream on the owner's data shape (the gate's seeded 53-week job is the stand-in unless the controller supplies the real payload) at 1920x1080; scratch suffix `-10`. Report the measured vertical offset of the stack's centre from the band centre, before (about 10px low expected) and after (0).
- [ ] Acceptance: `frontend-gate` passes (the alignment check's plot-band containment holds); `suite-*`, `pre-commit`, `docsync-check` pass. Lands only on the owner's word; if rejected, drop it.

## Task 11: Record the UI audit Minors execution

**Wave:** 6. **After:** every landed or dropped task above. **Mode:** serial.
**Touches:** `docs/superpowers/plans/2026-10-31-ui-audit-minors.md`, plus the landing bookkeeping files R1 names (the PLAYBOOK Section 4 entry and whatever `doc_state_sync.py --fix` rewrites). The controller's landing makes those, as for every other task; the implementer edits only the plan.
**Commit:** `docs(plan): Record the UI audit Minors execution`.

- [ ] Tick each delivery-sequence box whose task landed. For a dropped PREVIEW task, leave the box unticked and write "dropped on the owner's word, <date>" beside it.
- [ ] Add a short "Execution record" section: one line per task with its commit short SHA and subject, the PREVIEW decisions with the date, and the final head's gate results (`frontend-gate` and `results-behavior` last lines, the `pytest -q` count).
- [ ] The landing's own bookkeeping (R1 Section 4 entry, `doc_state_sync.py --fix`, Validation line) follows the constraints; this commit edits only the plan.
- [ ] Acceptance: the Gates block passes at the final head, with `frontend-gate` and `results-behavior` both run.
