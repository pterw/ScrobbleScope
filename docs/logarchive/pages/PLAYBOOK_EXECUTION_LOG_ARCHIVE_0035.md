<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0035

### 2026-10-29 - Fit listening and empty pages to the browser viewport

Side task on `feat/streamgraph-bursts`, requested after the earlier viewport
estimate still overflowed at desktop scaling. Fit the shared SVG width against
actual rendered chrome, refit on viewport and font changes, scale the summary
controls, and remove the oversized chart tail. Empty destinations share their
viewport with the actual footer and mobile theme control in normal flow. The
combined mode is now Listening, with copy describing daily plays and weekly
artist trends on desktop; saved-job routes and identifiers remain stable.

Extend existing layout checks rather than adding wording or duplicate tests.
The old result overflow was reproduced at 1536x780, 1280x720 and 1024x768.
Focused Chromium and Firefox probes now fit those viewports, 1080p and 1440p
browser content boxes, with the complete tooltip visible. The full suite measured
**3113 passed**: 2954 non-browser tests in three shards and 159 browser tests.
Fresh-result and late-chrome checks pass in both engines and motion modes.
The final frontend gate passed 58 checks in 89 Chromium and Firefox runs after
correcting scroll and export fixtures whose fixed-layout assumptions no longer
hold. Pre-commit and docsync passed before the final completion record. A review
found that fitting must wait for the outgoing loader to leave; both motion
paths now refit after that transition. Very short windows or enlarged text keep
natural page scrolling instead of clipping controls.

### 2026-10-29 - Scale the heatmap result with viewport height

Side task on `feat/streamgraph-bursts`. The owner requested the pause control
be visible at 1080p, more prominent KPIs and a better placed legend. Limit the
result width by viewport height so its two aligned SVGs scale together, group
the legend beside the context control, and compact the result footer spacing.
The heading and mobile layout remain intact. The full suite measured **3113 passed** in three shards. The browser gate passed 58 checks in 89 Chromium and Firefox runs after
replacing two obsolete fixed-width assumptions with tooltip containment and a
readable cell size check. Shorter desktop viewports can still require page scrolling.

### 2026-10-28 - Align streamgraph paths with the grid edges

Side task on `feat/streamgraph-bursts`. The owner noticed a gap at the
first column: stream ribbons began at the weekly centre, while the heatmap
and month gridline begin at the cell edge. Extend the halo and artist paths
horizontally at both ends, preserving every weekly centre and value. The
existing browser alignment gate now checks both outer edges. Focused checks
passed in Chromium and Firefox; the full suite measured **3113 passed**.
The full frontend gate passed 58 checks in 89 Chromium and Firefox runs.

### 2026-10-28 - Map stream colours to artist rank

Side task on `feat/streamgraph-bursts`. After comparing a local preview, the
owner approved the heatmap convention: orange for the most-played artist,
progressing through red to purple for the least-played artist. Keep ranks and
counts stable, preserve the existing heatmap ramp, and use lighter purple
shades for dark mode. Extend the existing palette test for rank progression.
Focused Chromium and Firefox theme repaint, alignment, toggle and export
checks pass. The full suite measured **3113 passed**. The palette audit and
known weak adjacent colour pairs are recorded in the plan. The full browser
gate passed 58 checks in 89 runs across Chromium and Firefox.

### 2026-10-28 - Remove the streamgraph compression caption

Side task on `feat/streamgraph-bursts`. Following a local review, the owner
requested removal of the 0.25x header explanation because it was confusing.
The halo, toggle, artist colours and actual tooltip counts stay unchanged.
Remove the matching accessible-label wording and obsolete gate assertion.
A separate local hue-grouped palette remains a preview pending owner review;
it is not part of this commit. Focused alignment, toggle and export checks
passed in Chromium and Firefox; the full suite measured **3113 passed**.

### 2026-10-28 - Add the streamgraph context halo

Side task on `feat/streamgraph-bursts`. The owner replaced the earlier
artist-only follow-up with the context-halo direction and approved its T0
plan. Partial implementation started before that approval; it was paused,
disclosed, and reviewed against the approved plan before continuing.

Keep the ten featured artists' stack independent of the residual. Draw the
remaining plays as a default-on symmetric halo at one quarter thickness,
with a visibility control that preserves artist paths, counts and scale.
Reuse heatmap month positions on the lower axis, add circular tooltip markers
and a residual divider, and use ten deterministic candidate-derived colours.
A final partial-week label is anchored inward to avoid clipping without
moving its calendar gridline. Save Image keeps the selected halo state.

Superseded burst and hidden-contributor test cases were replaced or removed;
focused coverage checks geometry, empty and spike weeks, interaction, axis
alignment and exposed halo pixels in both export states. The previous suite
had 3116 tests; the fresh suite measured **3113 passed** in three shards.
Focused Chromium and Firefox checks pass after the final-week fix. Four
matched real-data captures and the colour audit are recorded in the context
plan. The final-state browser gate passed 58 checks in 89 runs across
Chromium and Firefox. All pre-commit hooks and the final docsync check pass.
The alignment hook reports the known advisory WT003 side-task branch warning.

### 2026-10-28 - Integrate main before final streamgraph validation

Side task, no batch tag: normal merge of origin/main at f94c490f into
`feat/streamgraph-bursts`, after Task 9 while the owner layout choice waits.
The plan had integration after Task 10; advancing this independent work is
an order deviation, not a scope addition or history rewrite. Main brings
PR #279's Deezer 403 handling, MusicBrainz spacing and operations record.
No stream UI source changes are included in this merge.

Five conflicts concern counts and dated documentation histories. Preserve
both parents' log entries, retain Section 3 unchanged, then refresh the
managed counts from a fresh run. Independent pre-rotation review proved
658 HEAD and 653 main dated entries preserved exactly across PLAYBOOK and
archive, and main's automatic source/test merges match its parent. Docsync
performs the rotation; no log entry is discarded or moved across markers
by hand. Fresh suite shards: 702 + 1509 + 905. Existing test changes are
upstream provider/config cases, unchanged from main.

Forward guidance: Task 10 UI/gate patches stay in isolated worktrees.
The real-data top-ten preview preserves all 53 weekly totals, shows no
contributors and passes both-theme numeric-row checks. Its short-window
page sizing remains pending the owner's KPI/bottom-spacing choice. Run
integrated frontend and results-behavior checks after that final UI patch;
this merge makes no final browser or prototype-approval claim. No PR/push.

Validation: `pytest -q` -- **3116 passed**.

### 2026-10-28 - Return weekly artists to the top ten

Side task, no batch tag: Task 9 on `feat/streamgraph-bursts`. The owner
requested top ten only and no residual contributor list after live testing.
Reverse this branch's own burst selection and contributor metadata in plays,
job readback and their tests. The four files match origin/main exactly;
none changed upstream since the original branch base. Original normalized
ranking/ties, Monday columns, window filtering, empty-key residuals and
nested-copy isolation coverage remain. README and the sequence diagram
again describe top ten. No UI source changes in this checkpoint.

Plan vs implementation: exact scoped reversal, no history rewrite. Tests
solely for the removed feature are removed; original behavior tests return.
Focused plays/jobs/heatmap: 114 passed. Independent spec/quality review
approved. Fresh full shards: 702 + 1507 + 905. No browser gate is triggered
by these backend-only paths; Task 10 runs the integrated UI gate.

Forward guidance: Task 10 removes remaining contributor UI and unused
styles, caps the client at ten and reduces the chart box. Measured short
viewports cannot fit the original gaps and 268px tooltip together. Owner
choice on compact KPI/bottom spacing is pending; page-scroll assertions
remain strict. Final main integration, live approval and PR remain pending.
Section 3 batch sequencing is unchanged. WT003/WT005/WT010/WT012 are
advisory under the owner's instruction; no lineage repair is attempted.

Validation: `pytest -q` -- **3114 passed**.

### 2026-10-28 - Keep residual counts outside the artist stream

Side task, no batch tag: Task 8 checkpoint on `feat/streamgraph-bursts`.
Only named artist counts feed SVG baseline, fit, stack and hit mapping.
Everything else stays numeric, normal-weight and without a painted swatch;
keyboard selection leaves artist paths undimmed. Residual-only weeks and
payloads remain scrubbable; all-zero data draws no stream. Original rocket
arrays and permutation remain. Four unused residual colour tokens are removed.
README, DESIGN and the original plan/spec distinguish named-only geometry
from full weekly totals. No payload or server changes in this checkpoint.

Existing pure hit-test cases were extended for direct slot/rank mapping,
empty bands, boundaries, empty stack and residual-only weeks. Red: 6 failed,
4 passed; green: 10 passed; whole file: 150 passed. Existing browser families
now check named paths, numeric residual style/count, undimmed keyboard state,
residual-only/all-zero jobs and named JPEG pixels. A metamorphic assertion
proves 10,000x residual volume leaves artist geometry unchanged. Independent
source/runtime review approved. Full locked gate: 58 checks in 89 runs across
Chromium/Firefox. Fresh suite shards: 702 + 1507 + 912. Real-data Firefox
captures pass data/geometry in both themes; the agent did not judge visuals.

Deviations/forward guidance: the owner liked the artist-only preview, then
requested removal of contributor rows, a smaller SVG box without vertical
scrolling and a return to top ten only. This commit preserves Task 8's
reviewed twelve-artist checkpoint; newly defined Tasks 9-10 supersede its
retained contributor block and height reservation before final publication.
Code phases may run in parallel; land backend Task 9 before UI Task 10.
Final owner approval, main integration and PR publication remain pending.
Section 3 batch sequencing is unchanged. No history rewrite.

Validation: `pytest -q` -- **3121 passed**.

### 2026-10-28 - Plan an artist-only stream with numeric residual

Side task, no batch tag: revise the live-review design and plan on
`feat/streamgraph-bursts`. The owner wants Everything else excluded from
SVG geometry, kept numerically in the scrubber, and the original rocket
palette restored. This supersedes unlanded sandwich and navy experiments;
Task 5 spacing and normal residual weight remain complete. Task 8 separates
renderer/pure-test and browser-check ownership for parallel code work, then
one integrated atomic landing. No product code changes in this checkpoint.

Plan vs implementation: revised definition only; no Task 8 box is complete.
Deviations: owner-directed replacement of Tasks 6-7 before either landed.
Existing tests edited: none. Fresh full shards passed 702 + 1503 + 912.
The guard reports WT003, WT010 and WT005; guards are advisory per owner.
WT005 is real divergence, not the content-identical case. Normal reviewed
main integration remains required, with no history rewrite. Section 3 batch
sequencing is unchanged. Forward guidance: execute Task 8 in isolated
worktrees, review and validate, refresh live review and obtain prototype
approval before PR publication.

Validation: `pytest -q` -- **3117 passed**.

### 2026-10-28 - Restore stream result spacing and quiet the residual row

Side task, no batch tag: restore stream result spacing and quiet the residual row, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: restore the original page rhythm and keep Everything else at normal weight even when selected. The page may follow normal document flow beyond a short viewport; only the grid and tooltip must avoid internal vertical scrolling.

What changed: Task 5 removes the temporary stream-specific width, padding, headline and spacing compression. The original desktop focus-padding rule and 25rem initial chart reservation remain. Selected residual rows keep opacity 1 and weight 400 while named artists retain weight 700. The existing hover reader now checks internal grid/panel scrolling only, with diagnostic wording matching that scope; row containment, focus clearance and clipping assertions remain. DESIGN.md follows the restored page flow and residual emphasis. The original design spec links to the follow-up design for the current scrolling contract.

Deviations: the owner superseded the earlier whole-page no-scroll constraint during live review. The gate's document-height rejection is therefore removed intentionally, with no weakening of internal containment. The reviewer-approved diagnostic correction changes "chart, panel or page" to "chart or panel". No new unit test is added for this reversible styling slice; existing full-suite and computed-style browser evidence validate it. The whole 58-check browser gate runs at the integrated Task 7 head per the follow-up plan.

Existing tests edited: none under tests/. Independent Task 5 code review approved the correction; source probe red had 8 failures (compressed 4px gaps, selected residual weight 700) and green had 8 passes across Chromium/Firefox at four desktop sizes (original gaps 40/20/20/24/16px, residual weight 400, 16 rows with zero outside/internal-scroll failures). The fresh locked landing probe passed the same 8 cases on actual u7 source. All three full-suite shards passed: 702 + 1503 + 912. No whole-gate success is claimed for this individual slice.

Validation: `pytest -q` -- **3117 passed**.

Forward guidance: land Tasks 6 and 7 independently, then run the integrated browser gate and refresh the private real-data preview. Owner prototype approval remains pending; no main integration or PR publication yet.

### 2026-10-28 - Record the Deezer egress plan's execution

Side task, no batch tag: record in the Deezer egress plan (`docs/superpowers/plans/2026-10-28-deezer-egress-incident.md`) which tasks landed, in which commits and with which deviations, on `fix/deezer-egress-incident`, a branch off `main`.

Owner intent: plans must show their boxes ticked as work lands; several earlier plans lacked the ticks. The plan's 15 step boxes (Tasks 1-3) are ticked, each backed by its land report and an approving review. The plan gains an "Execution record (2026-10-28)" section: each task's commit and review result (T1 `3ed4aaec`, T2 `575d3412`, T3 `ab914965`; plan `80ce99ee`, approved after 2 fix rounds), the deviation rulings (C10, C12, C14-C17), the stacked landing with one gate-runner at the top, the final evidence (ALL_PASS at `ab914965`, CI run 40717261737 green) and the bot triage (qlty and Codacy findings rejected after measurement; Codex pending). Docs only; the plan is a point-in-time record, so no live prose changed.

Deviations: none. Existing tests edited: none.

Validation: `pytest -q` -- **3101 passed**.

### 2026-10-28 - Record the Deezer egress block and its recovery

Side task, no batch tag: document the Deezer egress-address block and how to recover from it, on `fix/deezer-egress-incident`, a branch off `main`.

Owner intent: the production machine's egress IP was blocked by Akamai, so every Deezer call returned 403; keep a runbook so the next occurrence is a probe and a machine clone, not a code hunt.

What changed: `DEPLOY.md` gains the section "Deezer blocks the machine's egress address" (symptom, probe, free fix by machine clone, paid fix by static egress IP, why a restart or deploy does not help). `AGENTS.md` gains Anti-Pattern item 16 and the `OPS` source tag; `docs/agents/issue-tracker.md` lists `OPS`. Finding F-OPS-1 is written resolved and rotated to the findings archive in this commit. The static egress IP was released on the owner's word to test whether a restart would clear the block; it did not.

Deviations: new `OPS` tag for the F-ID (extended in `AGENTS.md` and `issue-tracker.md`); the finding is resolved and rotated in the same commit.

Existing tests edited: none.

Validation: `pytest -q` -- **3101 passed**.

### 2026-10-28 - MusicBrainz request starts 1.2 seconds apart

Side task, no batch tag: space MusicBrainz request starts 1.2 seconds apart instead of 1.1, on `fix/deezer-egress-incident`, a branch off `main`.

Owner intent: add more delay between MusicBrainz requests, and note that MusicBrainz answers a rate limit with HTTP 503 rather than 429, so an occasional 503 is not unusual.

What changed: `MUSICBRAINZ_MIN_INTERVAL_SECONDS` defaults to 1.2 in `scrobblescope/config.py`; every statement of the old 1.1 value is updated (`scrobblescope/utils.py` docstring, `static/js/results-release-checks.js` comment, README, `docs/architecture/runtime-system.md`, `.claude/SESSION_CONTEXT.md`). The README paragraph on provider log lines gains a sentence saying MusicBrainz uses 503 as its rate-limit answer, that the client retries it like a 429, and that an occasional `503` count is normal. No code path changes; `musicbrainz.py` already treats 429 and 503 alike.

Deviations: none.

Existing tests edited: `test_musicbrainz_spacing_is_the_interval_setting_and_the_old_rate_is_ignored` and `test_global_throttles_space_request_starts_by_their_interval` (expected value only, 1.1 to 1.2).

Validation: `pytest -q` -- **3101 passed**.

### 2026-10-28 - A Deezer 403 is one request, not three

Side task, no batch tag: stop retrying a Deezer HTTP 403, on `fix/deezer-egress-incident`, a branch off `main`.

Owner intent: a 403 from Deezer's CDN means the egress address is blocked, so a retry cannot cure it and only triples the traffic to a host that already refuses us.

What changed: `scrobblescope/deezer.py` raises `deezer_unavailable` at once on a 403 (one request, no backoff sleep); 429, 5xx and quota responses are still retried. Both `retry_with_semaphore` calls now pass `reraise=(ProviderError,)`, which only silences a duplicate error log line (no test guards that decision).

Deviations: none.

Existing tests edited: `test_deezer_http_403_raises_unavailable_not_no_match` (re-pointed, parametrized over search, album details and album tracks; asserts the request count and that no sleep happens).

Validation: `pytest -q` -- **3101 passed**.

### 2026-10-28 - Plan the Deezer egress incident fixes

Side task, no batch tag: plan the Deezer egress incident fixes, on `fix/deezer-egress-incident`, a branch off `main`.

Owner intent: production Deezer calls were all refused with 403 by Deezer's CDN for one Fly host address, fixed operationally by moving the machine; the owner asked for an incident report, no retries on a Deezer 403, MusicBrainz spacing of 1.2 seconds, and atomic parallel slices.

What the plan holds: three parallel code tasks T1-T3, one commit each, landing in order (`docs/superpowers/plans/2026-10-28-deezer-egress-incident.md`).

Deviations: none.

Existing tests edited: none.

Validation: `pytest -q` -- **3099 passed**.

### 2026-10-28 - Plan the streamgraph live-review corrections

Side task, no batch tag: record the owner-directed prototype corrections, on
`feat/streamgraph-bursts`, a branch off `main`. Original Tasks 1-4 are committed.
The owner requested restored header spacing, normal-weight residual text,
symmetric residual caps and clearer burst colours, with parallel implementation.
The follow-up plan slices spacing, proportional geometry and palette into separate
atomic commits and keeps updated live review before PR publication. Document flow
is restored; the chart and tooltip retain their internal no-scroll constraint.
No application code changes. Tests edited: none. Plan vs implementation: planning
only; no code step is marked complete. Forward guidance: execute Tasks 5-7 in
parallel code worktrees, review and land serially, then refresh the private preview.

Validation: `pytest -q` -- **3117 passed**.

### 2026-10-28 - Verify weekly hidden artists in the browser gate

Side task, no batch tag: verify weekly hidden artists in the browser gate, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: preserve the twelve-layer stream, conditional aligned hidden rows and keyboard access, with the tallest desktop panel visible without vertical scrolling.

What changed: Task 4 seeds twelve artists, including two sparse bursts over weeks 5-7, and Hidden A/B/C in every third week as part of Everything else's count. One new registered check proves exact names, counts, sibling order, one conditional rule and name-column alignment as the pointer changes weeks. Existing hover checks include hidden rows and reject chart, panel or document vertical scrolling; the existing keyboard check now challenges a retained dense cursor after sparse pointer activity. The job fixture still flows through the real job store. No application, template, JS or CSS changed in this task, so product documentation remains true.

Deviations: the existing keyboard and no-scroll assertions were extended to hold the approved Task 3 corrections, with no helper, second check, dependency, schema or weaker assertion. The intentional hidden-block removal failed the new check with zero rules and empty rows; the saved original text was restored before green. Sparse-keyboard, laptop overflow and the intermediate focus-padding source-order regression found during stack validation were corrected in Task 3, not this gate commit. The controller's final code-phase gate and the fresh landing frontend gate each passed 58 checks in 89 runs; independent source/runtime review approved the patch. Fresh suite shards passed 702 + 1503 + 912 cases.

Existing tests edited: none under tests/. Browser checks extended: `check_stream_hover_shows_panel_and_ring` through its shared hover assertions, and `check_stream_is_one_keyboard_tab_stop`; new check: `check_stream_panel_rule_and_hidden_rows_follow_the_week`.

Validation: `pytest -q` -- **3117 passed**.

Forward guidance: the owner has not approved the Firefox prototype. Follow up in a separate small slice on Everything else bolding and burst emphasis; the controller is clarifying whether emphasis applies to the full burst-artist ribbon or its winning 21-day segment. This checkpoint preserves the reviewed gate/source stack. Task 0 sign-off, final integration and PR publication remain pending.

### 2026-10-28 - List hidden artists in the stream tooltip

Side task, no batch tag: list hidden artists in the stream tooltip, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: name the largest artists still pooled each week without indentation, use a divider only when those rows exist, retain twelve named layers (top ten plus two rolling three-week bursts), and fit the desktop chart without vertical scrolling.

What changed: Task 3 validates optional hidden entries, exposes the selected week's list in the panel model, and renders a conditional rule plus up to three aligned text rows with blank swatch spacers. README and DESIGN.md follow the new UI. Sparse burst weeks now use their visible rows for keyboard selection, including retained-cursor and pointer-to-key transitions. The desktop result reserves chart room at initial render and fits its width, spacing and headline to viewport height.

Deviations: the owner selected existing `--stream-muted` for the divider (5.53:1 light, 5.05:1 dark), replacing the planned low-contrast token. The same-file keyboard and desktop height-budget corrections were required by the final sparse fixture and approved independently. A code-phase CSS order edit briefly let the base 4px grid padding override the existing 8px desktop focus-ring room; the final-stack gate caught clipping, and the existing desktop rule was restored after the base rule without weakening the gate. The controller-approved documentation scope also reconciles the active spec with the divider/layout decisions and clarifies that burst layers keep their full weekly history, with zero counts only in weeks without plays; DESIGN.md now describes only visible layer rows. No selection code changed. No new helper, token, dependency, schema or extra test family was added. The Task 0 named-artist guarantee is replaced with independent measured top-ten plus rolling 21-day peak verification: current outside-top-ten peaks are Slayyyter 134, Magdalena Bay 120 and Cameron Winter 115; Four Tet holds the tenth slot at 271 total, one above Magdalena Bay's 270. The owner reaffirmed the ranking rule; no artist is hardcoded and the dated handoff remains historical.

Existing tests edited: `test_stream_payload_valid`; `test_panel_model_hidden_artists_for_the_week` adds the planned three parametrized model cases. Code-phase red: 7 failed, 19 passed; focused green: 26 passed. Fresh landing focused checks: 26 passed, 120 deselected; whole file: 146 passed. Independent hidden-row, keyboard follow-up and layout reviews approved the scoped source. The controller's final full-stack browser gate passed 58 checks in 89 runs after the focus-room correction; both browsers also passed the eight focused desktop sizes. Fresh final-source suite shards all passed; landing validation follows below.

Validation: `pytest -q` -- **3117 passed**.

Forward guidance: land Task 4's browser proof next, then complete the real-data Firefox prototype. Its owner sign-off still precedes PR publication; Task 0 sign-off remains pending.

### 2026-10-28 - Colour twelve stream layers with the rocket palette

Side task, no batch tag: colour twelve stream layers with the rocket palette, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: give all twelve layers distinct colours, with touching bands separated across the ramp and each theme using its visible range.

What changed: Task 2 installs the frozen seaborn v0.13.2 rocket samples and fixed permutation, exports the palette to the existing test hooks, and accepts up to twelve layers. DESIGN.md follows those values. The stream gate's existing `_rgb` wrapper now accepts the palette's six-digit hex values through its existing decoder. The active design spec now reflects the owner's checkpoint-commit timing override, resolving Task 1's landing-review follow-up.

Deviations: the owner approved the minimal `_rgb` gate compatibility hunk outside the original Task 2 Touches. The palette stays in JS arrays with per-theme sampling windows, as agreed. Stream fills retain their U20 exemption: light contrast min/max 1.89/12.66, dark 1.59/10.83. No helper, test, dependency or schema was added beyond the approved plan.

Existing tests edited: `test_layer_colour_follows_the_ramp_and_light_is_rescaled_not_clamped` became `test_layer_colour_gives_touching_layers_distinct_palette_steps`; `test_stream_payload_valid` covers the twelve/thirteen-layer boundary. Code-phase red: 5 failed, 13 passed; green whole file: 139 passed. The published LUT derivation had 0 differences. Independent palette and approved-exception reviews passed. Fresh landing focused tests: 18 passed, 121 deselected; whole file: 139 passed. The three full-suite shards all passed.

Validation: `pytest -q` -- **3110 passed**.

Forward guidance: land Task 3's tooltip next. Firefox prototype approval still precedes PR publication; Task 0 remains pending.

### 2026-10-28 - Add server burst layers and weekly hidden artists

Side task, no batch tag: add server burst layers and weekly hidden artists, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: make concentrated listening such as Cameron Winter visible beyond the top ten, and name the largest artists still hidden each week.

What changed: Task 1 selects two additional layers by the largest 21-day burst, with deterministic total/key ties, and names up to three non-layer artists per week. The job-store read view copies the optional hidden list without adding it to older payloads. README and the heatmap sequence diagram follow the server contract. The reviewed patch passed independent code review.

Deviations: no unused `burst` flag, as agreed in G4. The owner's 2026-10-28 override of G5 permits atomic checkpoint commits before prototype sign-off; Firefox prototype approval still precedes PR publication. The active plan now reflects that timing; Task 0 remains pending.

Existing tests edited: `test_artists_without_a_key_land_in_other`, `test_artists_beyond_top_n_fold_into_other_and_stray_plays_are_ignored`, and `test_context_isolates_dict_results_from_callers`. Five new aggregate behaviours cover cross-Monday bursts, the 21-day boundary, tie order, fewer than twelve artists and weekly hidden ranking. Fresh focused checks: 35 passed, 64 deselected; related regression files: 121 passed.

Validation: `pytest -q` -- **3106 passed**.

Forward guidance: land Task 2 next; review the Firefox prototype before publishing the PR. No frontend change is included in this checkpoint.

### 2026-10-28 - Plan the streamgraph burst layers

Side task, no batch tag: plan the streamgraph burst layers, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: the owner's streamgraph buried short listening bursts in "Everything else". The approved design has 12 layers, a hidden-artist tooltip and a per-theme rocket palette.

What changed: the design spec (`docs/superpowers/specs/2026-10-28-streamgraph-bursts-design.md`) and the sliced, parallelizable plan (`docs/superpowers/plans/2026-10-28-streamgraph-bursts.md`) are committed together, so the plan no longer lacks its spec. The plan was reviewed twice; the last fixes were folded in under ruling G8. Documentation only, no code.

Deviations: none.

Existing tests edited: none.

Validation: `pytest -q` -- **3099 passed**.

### 2026-10-28 - Fit the streamgraph stack inside its band

Side task, no batch tag: fixing Codex's P2 finding on PR #278 (the streamgraph saved image clipped), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Root cause: the scale came from the largest weekly total alone, but the wiggle baseline shifts each week's stack, so a stack could leave the fixed viewBox and the saved image clipped it.

What changed: `streamFit` in `static/js/heatmap.js` caps the scale by the stack's extent and shifts the baseline only when the stack would leave the band; ordinary data keeps its baseline and scale unchanged. Test rows from the review (two data sets that catch the missing scale cap and the high-side shift sign) were added to `test_stream_stack_stays_inside_the_band`, plus a pin that unmoved data keeps `streamScale` of its totals.

Deviations: none.

Existing tests edited: none (`test_stream_stack_stays_inside_the_band` is new in this change).

Validation: `pytest -q` -- **3099 passed**.

### 2026-10-28 - Keep the scrubber panel inside the chart

Side task, no batch tag: keeping the streamgraph scrubber panel inside the chart after PR #278's Linux CI failed, on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (ruling U23): the streamgraph matches the Claude Design reference in look and behaviour; the panel must also stay visible inside the chart frame when a fallback face renders it.

Root cause: CI has no Adobe kit fonts, so a wider fallback face draws the panel. The panel was sized by the room right of its anchor. Week 40 (the only week with a two-digit day, "Oct 13") opens leftwards into 225px of room, so it was squeezed to its 260px minimum, the wider face wrapped its header, and the panel ran past the chart's bottom (+9.8px against a 0.5px tolerance). Weeks 0 and 30 had room and passed. Blocking the kit alone does not reproduce it on Windows (the Windows fallback face is narrow), so the gate adds a wide-face pass.

What changed: `.stream-panel` sizes to its content (`width: max-content`) up to 360px and no further than the room on its side (`--stream-panel-room`, set by `showWeek` in `static/js/heatmap.js`); the header never wraps and a long artist name ends in an ellipsis. `showWeek` also measures the room on both sides of the column and opens toward the side with room when the reference side lacks it. The hover check in `scripts/dev/_frontend_gate_stream.py` (one check, more passes) gains a pass with the kit refused and wider tracking (checked as in effect), a 60-character artist name, weeks 0, 30, 33 and 40, containment on both axes, and a 1024x768 pass over weeks 0, 34 and 52. Proven red against the earlier code in Chromium and Firefox, then green.

Deviations (U23, for the owner): the content-sized panel with a 360px cap, the ellipsis on long names and the room-based side choice (instead of the reference's fixed flip at week 34, which still applies whenever the room allows) are not in the reference. Lifting the panel above the grid's top was weighed and skipped: the panel is 267px in a 417px grid.

Existing tests edited: none (the gate's hover check was extended; `tests/` is untouched).

Validation: `pytest -q` -- **3095 passed**.

### 2026-10-27 - Take main into the streamgraph branch

Side task, no batch tag: taking `origin/main` (PR #277 merged, 9e4120ae) into `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (ruling U37): PR #278 is retargeted to `main` after #277 merges, so its diff is its own. The branch takes #277 first, by a merge commit and not a rebase (AGENTS.md).

What changed and why: a plain `git merge`. Five docs conflicted and nothing else: `.claude/SESSION_CONTEXT.md`, `config/docsync.toml` and `docs/agents/FINDINGS.md` differed only in the test count (re-measured, then `--fix`); `docs/agents/PLAYBOOK.md` Section 4 and `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` keep every dated entry from both sides, none lost. The code files merged without conflict; `static/js/heatmap.js` (saveHeatmapImage/drawHeatmapImage split, mode-key crossfade) and `scripts/dev/_frontend_gate_theme.py` (token-parsed `_split_canvas_font`, no `re` import) were read for clashes with the branch's Save image and theme-scope work and none was found.

Deviations: none.

Existing tests edited: none.

Validation: `pytest -q` -- **3095 passed**.

### 2026-10-27 - Bring the job and module docs up to the streamgraph

Side task, no batch tag: the follow-up to the streamgraph docs commit (review ruling SG10-F1), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (rule R10): docs that the streamgraph makes untrue are fixed on the branch, not left for later.

What changed and why: `docs/architecture/heatmap-sequence.md` gains the `plays.aggregate_weekly_artist_counts` step, `weekly_artists` in the single success write, and a note that desktop widths draw the streamgraph under the grid when `weekly_artists` is valid. `.claude/SESSION_CONTEXT.md` gives the stream gate module its three real imports (`_frontend_gate_colour`, `_frontend_gate_shared`, `_frontend_gate_theme`) and adds the weekly artist counts to the `plays.py` and `heatmap.py` rows. This also closes the heatmap-sequence concern left open by the previous entry.

Deviations: the stacked-branch name replaces `feat/ui-audit-v6` in this entry. The previous entry (Describe the listening streamgraph) missed two deviations, recorded here: its commit subject `docs(heatmap): Describe the listening streamgraph` replaced the brief's `docs: Describe the top-artists streamgraph`, and the bare `--fix` rotated one older entry (Recolour the streamgraph) into the PLAYBOOK execution log archive.

Existing tests edited: none.

Validation: `pytest -q` -- **3050 passed**.

### 2026-10-27 - Describe the listening streamgraph

Side task, no batch tag: the streamgraph docs (streamgraph plan Task 10), on `feat/ui-audit-v6-streamgraph`, a branch off `main`.

Owner intent (rulings U18, U20): describe the streamgraph as it ships, desktop layout only, with the dark timeline surfaces inside the chart frame only.

What changed and why: `README.md` gains a streamgraph bullet in the Scrobble Heatmap list, a hand-built SVG paragraph, the keyboard note, and the weekly artist counts in the `plays.py` and `heatmap.py` rows; the Save image bullet now says the image includes the stream. `DESIGN.md` "Heatmap & Status" gains the frame-scoped timeline surfaces and the stream layer ramp with the light-theme 0.83 rescale, plus a "Heatmap Streamgraph" component section. `docs/architecture/documentation-tooling.md` gains the `_frontend_gate_stream` edges to `_frontend_gate_shared`, `_frontend_gate_colour` and `_frontend_gate_theme` and its `tool` class entry (the diagram needs a render). `.claude/SESSION_CONTEXT.md` lists the stream gate checks. The plan's Task 10 boxes are ticked.

Deviations: the stacked-branch name replaces `feat/ui-audit-v6` in this entry. No "Pause animations" control exists at this base, so the docs say only that `prefers-reduced-motion` zeroes the layer fade. `docs/architecture/heatmap-sequence.md` line 89 still lists `daily_counts` and statistics as what the job stores; it is outside this task's files and is left for the controller.

Existing tests edited: none.

Validation: `pytest -q` -- **3050 passed**.

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
