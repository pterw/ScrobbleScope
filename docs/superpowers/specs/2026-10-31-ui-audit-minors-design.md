# UI audit Minors bug-fix design

Last updated: 2026-10-31

## Decision and authority

The UI audit's deferred Minors were triaged on 2026-10-31 (79 rows, read-only
audit of `main` at 18a4242d). The owner accepted the triage and ruled on the
open questions. This is a side task before Batch 23 WP-1, not a batch work
package. The implementation plan is
[the UI audit Minors plan](../plans/2026-10-31-ui-audit-minors.md).

Every row below was re-read against the code at 9436ff7c (the audit's code
is unchanged: 9436ff7c differs from 18a4242d only in PLAYBOOK and its
archive). Line numbers are for 9436ff7c and will move; the plan cites names.

### Owner rulings

- C1 "Okay, everything looks good to me. Green, row 39 is fine to drop. No
  need to excessively guard every UI element."
- C2 The streamgraph's month labels match the heatmap's: "These should be
  fixed for consistency then. I also noticed the font size for the months is
  different, so that should be standarized."
- C3 Centring: "a preview would be nice before rendering a decision." The
  candidate centres the stack's outer envelope in the plot band. PREVIEW:
  lands only on the owner's word; if rejected it is dropped, not reworked.
- C4 Tooltip row order is "a non-issue"; the Aug-Sep zero-listening hairline
  stays.
- C5 Row 24 (the "Job context not found" warning) is closed in the
  workspace's Gates block, not in app code.
- C6 Lean suites: tests only for behaviour this PR changes; extend existing
  tests first.

PREVIEW items (C2, C3, rows 25 and 5) land only on the owner's word after
before/after Firefox screenshots (workspace rule R14). Each is its own commit,
so a rejection drops it alone.

## In scope

### A. Streamgraph hover panel (`static/js/heatmap.js`, `scripts/dev/_frontend_gate_stream.py`)

**Row 1.** `showWeek`'s duplicate guard reads `state.shown &&state.shown.week`
(`heatmap.js:2091`). Add the space. No behaviour change.

**Row 26.** The panel carries `aria-live="polite"` for its whole life
(`heatmap.js:1959`, set in `drawStream`) and `showWeek` rewrites it for every
week change (`:2133`, `fillStreamPanel`), so a pointer scrub announces
continuously. After the fix the panel is a live region only while the stream
holds keyboard focus: set in `handleStreamFocus`, removed in
`handleStreamBlur`. "Keyboard focus" is defined once for rows 26 and 28: the
stream svg matches `:focus-visible`. The svg is `tabindex="0"`, so a click or
tap focuses it too, and that focus must not count (it would leave the panel
stuck after the pointer leaves, and make pointer scrubbing announce). The
rule is `:focus-visible` rather than "focus that a key produced" because the
heatmap cells already use it for the same question
(`syncFocusIndicators`, `heatmap.js:2474`), and Firefox supports it. Chromium
turns `:focus-visible` on for a clicked element at the first key without a
focus event (the same comment), so the live region is also decided again at
each handled key press, not only in `handleStreamFocus`. The region is set
before the panel is filled (`showStreamCursor`), so the first fill is
announced where the screen reader allows; the first-focus announcement is not
asserted. A pointer scrub with no keyboard focus announces nothing; a keyboard
user hears one polite announcement per key press, which is what they asked
for. Why not drop the region outright: keyboard users would then hear
nothing when they arrow between weeks, and the stream is `role="application"`.
Why not debounce: it adds a timer and a settle rule nothing else needs.

**Row 27.** Escape does not dismiss the panel (`handleStreamKey`,
`heatmap.js:2036-2043`; Escape appears only at `:2516` and `:2572` for
tooltips). Content on hover or focus must be dismissible (WCAG 1.4.13). After
the fix Escape, pressed while the stream has focus, hides the panel, ring,
guide and dimming but keeps focus and remembers the keyboard position, so the
next arrow key shows the panel again from where it was.

**Row 28.** `pointerleave` and `pointercancel` call `clearWeek`
(`heatmap.js:1974-1975`) even while the stream has focus, and
`handleStreamPointer` (`:1980-1988`) never writes `state.cursor`. A keyboard
user whose pointer drifts off loses the panel, ring and dimming, and the keys
resume at the older keyboard week. After the fix a pointer leave while the
stream has keyboard focus (`:focus-visible`, as row 26) changes nothing: the
panel stays on the last shown week and the keys continue from it
(`streamKeyState` already prefers `state.shown`). A pointer leave without
keyboard focus still clears everything, as now. That includes a stream focused
by a click or tap: the pointer leave (a lift ends in one on touch) clears the
panel, ring and dimming, and the live region stays off.

**Row 29.** The keyboard gate never asserts an arrow key was consumed, so a
regression that lets arrows scroll the page would pass (no `scrollY` or
`scrollTop` read in `_frontend_gate_stream.py`; `_step_failures` checks
position only). After the fix the keyboard check records, with a bubbling
`keydown` listener on `window`, whether each arrow press arrived with
`defaultPrevented` set, and fails when one did not. This reads the consumption
itself rather than `scrollY`, because the page may not scroll at the gate's
viewport and a scroll read would then pass vacuously. It extends the existing
`check_stream_is_one_keyboard_tab_stop`, and covers every press the check
makes: the dense-week-end presses and the whole `_KEY_STEPS` walk (Home, End
and the edge clamps included), since the listener costs the same either way.

**Row 30.** That check's `finally` (`_frontend_gate_stream.py`, last lines of
`check_stream_is_one_keyboard_tab_stop`) runs `page.evaluate(_REMOVE_SENTINEL_JS)`,
`page.set_viewport_size(original)` and `jobs.delete(job_id)` in sequence, so a
raising first step skips the other two and leaks a seeded job. After the fix
each cleanup step runs even when an earlier one raises.

**Row 23.** `_paint_failures` appends "the stream draws no artist layers in
the {theme} theme" when `reading["fills"]` is empty, then evaluates
`min(ratios)` of an empty list (`_frontend_gate_stream.py`, the `[stream
colours]` print), which raises `ValueError` before the failures return. After
the fix the contrast line is computed only when there are layers, and the
named failure is returned.

### B. Visual consistency (PREVIEW)

**C2 month labels.** The heatmap's month labels are created with
`font-size 9.5`, `LABEL_FONT_STACK`, `font-variant small-caps` and
`letter-spacing 0.12em` (`heatmap.js:1750-1753`). The stream's bottom labels
get `font-size 9.5` and `LABEL_FONT_STACK` only (`drawStream`, `:1899`). After
the fix both carry the same four attributes. The text is the same string.
Finding that differs from the owner's note: the font size is already equal.
`drawStream` is called with the grid's own `svgWidth` (`:1808`), so both
viewBoxes are as wide as each other, both SVGs are `width: 100%` in
`#heatmap-grid` (`heatmap.css`, `#heatmap-grid svg`), and 9.5 units render at
the same CSS size in both. What the owner sees as a size difference is the
missing `small-caps` (the heatmap's "Jan" draws with small capitals) and
tracking; the fix removes both differences. The gate asserts the rendered size
and the style attributes are equal, so a future scale difference is caught.
The saved image does change (owner ruling C12). `gridAsImage` and
`streamAsImage` overwrite only `font-family` on the month labels
(`heatmap.js:743-749`, `:765-767`) and copy the other attributes, so the saved
stream's month labels gain small capitals and 0.12em tracking, matching the
saved heatmap's labels, which already carry both. That is the wanted outcome.
The tracking also widens the end-anchored last label, so the task checks it is
not clipped in the saved image. Evidence for the on-screen end-anchored last
label: it keeps its existing `inside` check in the alignment reading.

**C3 centring.** `streamFit` shifts the baseline only when the stack overflows
the band: `shift = high > half ? half - high : Math.max(0, -half - low)`
(`heatmap.js:289`), so ordinary data sits wherever the wiggle baseline leaves
it, about 10px low on the owner's data. After the fix the shift always centres
the outer envelope: `high` and `low` already include the halo margins and the
Bezier-control margins, so the shift is the amount that makes `high` and
`-low` equal. The scale rule is unchanged (the tallest week is `STREAM_PEAK`
tall, capped so the extent fits `STREAM_BAND`). The existing test
`test_stream_stack_stays_inside_the_band` asserts that ordinary data is left
unmoved (`ordinary-data-keeps-its-look`); under C3 that expectation is the
defect, so the test is edited, not extended. The centring assertion also
gets one case that passes `residual`, because the production path does, and a
shift computed without the halo and Bezier margins would pass the cases that
do not.

**Row 25.** `.stream-panel-header` uses `--text-label-sm` (12px,
`heatmap.css:568`, `tailwind.src.css:36`). The design reference says 13px
(`.superpowers/sdd/2026-10-27-ui-audit-v6/design/reference-v6-notes.md`, line
107: stream panel "header 13px muted"). `--text-label` is `0.8125rem`, which is 13px
(`tailwind.src.css:37`). After the fix the header uses `--text-label`. The
header is `white-space: nowrap; width: max-content`, so the panel's measured
need in `showWeek` grows with it; the stream gate's panel checks must still
pass.

Outcome (2026-10-30): dropped on the owner's word (C14); the header stays at 12px.

**Row 5.** The heatmap key's ramp keeps `margin-top: calc(0.875rem *
var(--index-scale, 1))` (`heatmap.css:201`) and is also a grid child of
`.index-key`, whose `gap` is `calc(0.75rem * var(--index-scale, 1))`
(`index.css:376`), so it sits `1.625rem * scale` (26px at scale 1, about 28px
at 1920) under the last row where the reference gives 12px
(`.superpowers/sdd/2026-10-27-ui-audit-v6/design/reference-v6-notes.md`, line
20: key block "`display:grid; gap:12px`"). After the fix the ramp's own
margin is removed and only the key's gap remains: 12px at scale 1, about 12.9px
at 1920, which keeps the page's own scaling rule. The ramp's 8px height is
unchanged.

**Row 17 (no visual change).** The 1.5rem footer gap is written twice:
`.index-grid .index-hero { padding-bottom: 1.5rem }` (`index.css:143`, comment
at `:139`) and `.page-footer-extras { padding: 1rem 1rem 1.5rem }`
(`shell.css:615`), guarded only by the gate's equality check. After the fix
one custom property declared in `shell.css`'s `:root` carries the value and
both rules read it. The gate's equality check stays as it is.

### C. Gate helpers

**Row 3.** `_split_canvas_font` (`_frontend_gate_theme.py`, `_NAMED_WEIGHTS =
{"bold": "700", "normal": "400"}`) lets a `normal` token reset an earlier
numeric weight: `600 normal 26px x` gives 400. In the canvas font shorthand
`normal` stands for "no change" in any slot. After the fix `normal` leaves the
weight alone and only `bold` sets one. The existing case `("normal 18px x",
"x", "400")` cannot fail if `normal` were ignored (400 is the default), so it
stays only as the neutral check and the new case carries the defect.

**Row 40.** `_pause_hold_failures` (`_frontend_gate_spotlight_photo.py`)
stores `ss-motion=still` through an init script, and only the Play click
clears it. An early return after `_open_spotlight_card` reports an error, or a
failing click, leaves the choice in the shared context's `localStorage` for
later probes. After the fix the probe clears the stored choice in its own
`finally`, whatever path it took.

### D. Row 13

`positionForm` in `static/js/index.js` writes `matchMedia('(min-width:
860px)')` (`:634`); `const desktop = matchMedia('(min-width: 860px)')` is
declared later at `:652`. After the fix `positionForm` reads `desktop.matches`,
and the declaration moves above `positionForm` so no reader has to check that
every call happens after line 652 (they do: the first call is at `:702`). No
behaviour change.

## Rows not planned

- 4, 19, 43: deferred to the findings triage (owner ruling).
- 21, 22: deferred to the docs rewrite (owner ruling).
- 24: closed in the workspace Gates block (C5).
- 39: dropped by the owner's word (C1); C4 settles the tooltip-order and
  hairline questions.
- 2, 6-12, 14-16, 18, 20, 31-38, 41, 42: dropped as triaged (C1).
- 44-79: FIXED or OBSOLETE in the audit, and the audit's Notes; not in scope.
- No in-scope row was found false against 9436ff7c. One premise is corrected:
  C2's "the two SVGs scale differently" does not hold (see C2); the fix is the
  same.

## Verification and definition of done

1. Each gate or pure test that is new or edited is shown red against the
   unchanged code, then green (workspace R9). Rows 1, 13 and 17 change no
   behaviour and add no test.
2. Gate checks for rows 26-29 and C2 are written before the code that
   satisfies them; the frontend gate is run against the unchanged
   `heatmap.js` to show them red.
3. Every commit passes the workspace Gates block; the final head also passes
   `frontend-gate` and `results-behavior`.
4. PREVIEW tasks save Firefox screenshots, light and dark, before and after,
   and land only on the owner's word (R14). A rejected one is dropped.
5. One whole-branch review is requested after the last landing, if the owner
   asks for it.
