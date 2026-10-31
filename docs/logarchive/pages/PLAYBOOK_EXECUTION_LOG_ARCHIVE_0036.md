<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0036

### 2026-10-31 - Repoint the archive pointers the split review found

Side task, no batch tag, branch `docs/paginate-archives`: fixes from the
independent review of the two archive commits. Section 4's own read guide
above still sent agents to the side-task archive file, which is now an index;
it now names the pages and says to search the directory.
`docs/AGENT_DOC_MAP.md` said that file "holds content" and that the findings
archive "holds the closed items"; both now say the entries are on the pages.
`AGENTS.md` "Doc Sync Rules" no longer calls the side-task archive a monolith.
The read-helper prologue in `scripts/docsync/renderer.py` no longer states
the 500-line default, since the page target is a setting in
`config/docsync.toml`; `--fix` rewrote the index prologue from it.

One new test, `test_side_archive_read_helpers_reach_the_archive_pages` in
`tests/test_docsync_renderer.py`, checks that every read helper searches a
place that holds the archive's pages. It failed with a helper pointed back
at the archive file and passed with the fix. The review found no gate would
otherwise catch that.

Deviations: none. This stages docsync control-plane code, so it lands alone
through the documented `SKIP=doc-state-sync-check` escape. Existing tests
edited: none.

Validation: `pytest -q` -- **3119 passed**.

### 2026-10-31 - Point the side-task archive's read helpers at its directory

Side task, no batch tag, branch `docs/paginate-archives`, after the archive
split. `SIDE_ARCHIVE_PREFIX` in `scripts/docsync/renderer.py` is the canonical
prologue DOC004 holds the side-task archive to. Its read helpers searched the
archive file itself, which is now an index with no entries, so an agent
following them found nothing. They now search `docs/logarchive/`, and the
prologue says why. The `Get-Content` helper is gone: reading the whole
archive is what the split exists to avoid. `--fix` rewrote the index's
prologue from the new constant.

Deviations: none. This is docsync control-plane code, so it lands as its own
commit through the documented `SKIP=doc-state-sync-check` escape. No test
changed: every test reads the constant by name.

Validation: `pytest -q` -- **3118 passed**.

### 2026-10-31 - Paginate the four archives past the page target

Side task, no batch tag, branch `docs/paginate-archives`. The owner asked for
the split because a 17,000-line archive is hard for an agent to grep or read.
`doc_state_sync.py --paginate-archives` turned four archives into indexes with
numbered pages under a `pages/` folder beside each: the side-task log archive
(36 pages), the findings archive (8), the Batch 21 log (2) and the Batch 22 log
(3). Every page is under 500 lines and none is oversized. The four DOC024
page-target warnings are gone. Two new informational DOC024 warnings name
findings pages 0001 and 0002, whose undated entries can never age into cold
storage. No `--cold-storage` run: that needs an explicit date from the owner.

The split was checked independently of the tool's own verification. Every
non-blank line of each old file is still present across its index and pages,
the only new lines are page headers and index lines, and all 687 dated
entries and 141 F-ID headings are on the pages.

Live instructions that searched an archive file by name now search its
directory: `AGENTS.md` "What to update after a WP or side-task commit",
`docs/logarchive/README.md`, `docs/AGENT_DOC_MAP.md` (a new trap entry),
`docs/SWE_AUDIT_CHARTER.md`, `DEVELOPMENT.md` (the archive section, the search
step and the sample `--check` output) and the cloud kit's expected docsync
warnings. Point-in-time records keep the old paths, which still resolve to
the indexes. The side-task archive's built-in read helpers are control-plane
text and change in the next commit (owner ruling, 2026-10-31).

Deviations: none. No code or test changed.

Validation: `pytest -q` -- **3118 passed**.

### 2026-10-31 - Take main into the UI audit Minors branch after PR #282

Side task, no batch tag: merge `main` (`708fb48b`, PR #282) into
`fix/ui-audit-minors`, so the branch carries the F-B23-33 fix and its
bookkeeping. Owner ruling 2026-10-31: a merge commit, not a rebase. Only
PLAYBOOK and the log archive conflicted. Both sides' Section 3 bullets and
Section 4 entries are kept, with PR #282 recorded as merged; `main`'s
pre-merge copy of the weekly chart geometry bullet is superseded by this
branch's merged one. The archive keeps this branch's side, which already
holds the one entry `main` added. No code conflicts.

Validation: `pytest -q` -- **3118 passed**.

### 2026-10-31 - Record the UI audit Minors execution

Side task, no batch tag: close the UI audit Minors plan
(`docs/superpowers/plans/2026-10-31-ui-audit-minors.md`) on
`fix/ui-audit-minors`. Nine tasks landed in nine commits, each approved in
review (the plan had one fix round, and Task 10 had one). The owner dropped
Task 6 (the 13px panel header, "I was not seeing a difference"), kept
Tasks 8, 9 and 10 after previews, and added then dropped Task 9b (the label
colour already matched). The plan ticks its boxes and gains an Execution
record with each task's commit, review outcome, preview decision, the
gate-script landings that went alone, the stack of Tasks 3, 4 and 8, and the
intermittent gate failures that were re-run green. The spec gains a one-line
outcome for Task 6's row. `results-behavior` is still owed at the final head.

Deviations: none. Edited existing tests: none. Docs only.

Validation: `pytest -q` -- **3113 passed**.

### 2026-10-31 - Ignore a malformed artist ID in the spotlight lookup

Side task, no batch tag: `_request_spotlight_artist` in
`scrobblescope/spotify.py` now takes the by-ID path only when the artist ID
is 22 base-62 characters. Before, the ID was spliced straight into
`https://api.spotify.com/v1/artists/{id}`, so a value carrying `/` or `..`
could make the server call another GET route under the app's token. A
malformed ID is now treated like any failed by-ID lookup: no request to the
artists URL, then the existing name fallback, or None without a name. No
client sends the parameter today. Closes F-B23-33 on branch
`fix/spotify-artist-id`.

An outside agent wrote the patch and an independent review approved it.
One new parametrized test covers four malformed IDs and a well-formed one.
Existing tests edited: `test_artist_spotlight_parses_details_and_missing_fields`,
`test_artist_spotlight_falls_back_from_failed_id_lookup` and
`test_artist_spotlight_id_lookup_skips_the_name_check` in
`tests/services/test_spotify_service.py` now pass a well-formed ID instead
of a short placeholder; no assertion changed beyond the ID value. No schema
change, no new dependency.

Validation: `pytest -q` -- **3113 passed**.

### 2026-10-31 - Centre the streamgraph in its plot band

`streamFit` in `static/js/heatmap.js` shifted the baseline only when the
stack's outer envelope overflowed the plot band, so ordinary data sat
about 10px low. It now always shifts by half the sum of the envelope's
high and low edges (halo and Bezier-control margins included), so the
envelope is centred on the band's centre line. The scale rule is
unchanged. The owner viewed this build on their own data and kept it
(C18); it closes audit owner ruling C3 of the UI audit Minors. One review
fix round added a case where a Bezier control point overshoots the
envelope, checked against an independent Python oracle, so a shift that
ignores the control margins fails. No deviations. Existing tests edited:
`test_stream_stack_stays_inside_the_band` (the `moved` flag became
`capped`, every case now asserts `low + high` is zero, and ids were
renamed).

Validation: `pytest -q` -- **3113 passed**.

### 2026-10-31 - Match the stream month labels to the heatmap's

The stream's bottom month labels, created in `drawStream` in
`static/js/heatmap.js`, carried only font-size and the font stack. They
now also take the heatmap labels' `font-variant` small-caps and
`letter-spacing` 0.12em, so the two charts' month rows read the same
(rendered size was already equal: both SVGs share `svgWidth` at
`width: 100%`). The saved image gains the same styling, because
`streamAsImage` already copies those two attributes; the export code is
unedited and the last label stays inside the image. The stream alignment
check in `scripts/dev/_frontend_gate_stream.py` now reads each label's
family, variant, tracking and rendered size, and fails when the stream
differs from the heatmap, failing closed on empty or mismatched label
sets. The owner previewed and kept the change (C16). This closes audit
owner ruling C2 of the UI audit Minors. No deviations. Existing tests
edited: none.

Validation: `pytest -q` -- **3111 passed**.

### 2026-10-31 - Tighten the heatmap key's ramp spacing

`.hm-preview__ramp` in `static/css/heatmap.css` carried its own
`margin-top` of 0.875rem on top of the `.index-key` grid gap, leaving
about 28px under the last key row at 1920. The margin is removed, so the
gap alone (0.75rem times `--index-scale`) remains: 12.9px at 1920, 12px
at scale 1, matching the reference's 12px grid gap. The ramp's height is
unchanged. The owner previewed the change and kept it (C15). This closes
audit row 5 of the UI audit Minors. No deviations. Existing tests
edited: none.

Validation: `pytest -q` -- **3111 passed**.

### 2026-10-31 - Share the footer gap as one custom property

The footer gap was two 1.5rem literals, the footer row's bottom padding in
`static/css/shell.css` and the home hero's `padding-bottom` in
`static/css/index.css`, kept equal only by a gate equality check. One
`--shell-footer-gap` property, declared once in `shell.css`'s `:root`,
now feeds both, and the `index.css` comment names it. Computed values are
unchanged. This closes audit row 17 of the UI audit Minors. No
deviations. Existing tests edited: none.

Validation: `pytest -q` -- **3111 passed**.

### 2026-10-31 - Reuse the desktop media query in index.js

`positionForm` in `static/js/index.js` built the same 860px media query
that the `desktop` const already holds. It now reads `desktop.matches`,
and the const is declared above `positionForm` so it is plainly
initialised before any call. No behaviour change. This closes audit row 13
of the UI audit Minors. No deviations. Existing tests edited: none.

Validation: `pytest -q` -- **3111 passed**.

### 2026-10-31 - Make the stream panel dismissible and focus-safe

The stream panel was always a live region, so a pointer scrub announced
every week. Escape did not dismiss it, a pointer leave dropped the week
while the keys were driving it, and the gate never checked that arrow keys
were consumed. `aria-live` is now set only while the stream has keyboard
focus (`:focus-visible`, so a click or tap does not count), decided on
focus and again at the first key, because Chromium turns `:focus-visible`
on after a click without a focus event. Escape hides the panel, ring,
guide and dimming, keeps focus and stores the position so the next arrow
resumes from it. Pointer leave and cancel clear the week only without
keyboard focus. `showWeek`'s guard lost its missing space. The keyboard
check now watches `window` for each arrow key reaching it with
`defaultPrevented`, and gained the click-then-leave, Escape and
unfocused-hover cases. The gate's three `.focus()` calls already match
`:focus-visible` in Chromium (the only engine the stream checks run on), so
they stay. This closes audit rows 1, 26, 27, 28 and 29 of the UI audit
Minors. Deviation: Escape calls `preventDefault` only when it dismissed a
panel. Existing tests edited: the gate check
`check_stream_is_one_keyboard_tab_stop` (its "after pointer leave"
expectation changed from week 6 to week 26 as the brief requires).

Validation: `pytest -q` -- **3111 passed**.

### 2026-10-31 - Clear the stored pause choice on every exit

The spotlight photo gate's paused-hold probe stores `ss-motion=still`
through an init script, and only the Play click removed it, so an early
return left the choice in the shared browser context. The probe's `finally`
now removes the `ss-motion` key before it closes the page. The removal is
wrapped in `contextlib.suppress(PlaywrightError)` (shorter than tracking
navigation state), so a page that never navigated cannot hide the original
failure. This closes audit row 40 of the UI audit Minors. No deviations.
Existing tests edited: none (one test added,
`test_an_early_return_leaves_no_stored_pause_choice`).

Validation: `pytest -q` -- **3111 passed**.

### 2026-10-30 - Report an empty stream and always run its cleanup

The stream gate's paint check called `min()` on the contrast ratios before
reporting a stream with no drawn layers, so an empty stream raised a
ValueError instead of the named failure. The contrast line is now skipped
when there are no ratios, and the failure "the stream draws no artist
layers" is returned. The keyboard check's cleanup ran its three steps in
sequence, so a raising first step skipped the viewport restore and the job
delete; each step now runs in a nested `finally` and the first error still
surfaces. This closes audit rows 23 and 30 of the UI audit Minors. No
deviations. Existing tests edited: none.

Validation: `pytest -q` -- **3109 passed**.

### 2026-10-30 - Keep a numeric font weight after `normal` in the gate

The frontend gate's canvas font parser read `600 normal 26px x` as weight
400, because the `normal` token reset the weight set just before it. The
saved-image headline check could then report a wrong drawn weight. `normal`
is no longer treated as a weight token, so a numeric weight stands, `bold`
still maps to 700 and a string with no weight stays 400. This closes audit
row 3 of the UI audit Minors. No deviations. Existing test edited:
`test_a_saved_headline_drawn_at_another_weight_is_reported` (one case
added, `600 normal 18px x`).

Validation: `pytest -q` -- **3109 passed**.

### 2026-10-30 - Plan the UI audit Minors bug fixes

The deferred Minors from the 2026-10-27 UI audit's reviews were checked
against `main` by a read-only audit. Of 79 rows, 43 were still true, and the
owner accepted a triage of them on 2026-10-30. The spec records each chosen
row with its evidence and lists the deferred and dropped rows. The plan
slices the fixes into eleven atomic tasks: stream panel keyboard and
screen-reader behaviour, gate-helper fixes, two CSS tidy-ups, and four
visual changes that land only after the owner previews them (panel header
size, key spacing, month labels, vertical centring). One plan review found
two Important issues: a focus rule that also caught pointer focus, and a
false claim about the saved image. Both were fixed with its eight Minors
before this commit. Docs only.

Validation: the full suite measured **3108 passed**; pre-commit on all
files and the final docsync check pass.

### 2026-10-30 - Record the merged chart work and open the UI Minors side task

Section 3 still described the weekly chart geometry branch as awaiting its
PR, although PR #281 merged on 2026-10-30 (merge commit `18a4242d`). This
entry records that merge and opens the UI audit Minors side task on
`fix/ui-audit-minors`, which the owner approved on 2026-10-30. Docs only: no
runtime, test or dependency change. The smoothing defect that headed the
deferred list was checked against `main` first. Codex's case (53 weeks, one
artist with 100 plays in week 26 only) now gives a minimum band thickness of
0 rather than -11.11, so it is not part of this side task's work.

Validation: the full suite measured **3108 passed**; pre-commit on all
files and the final docsync check pass. Next: collect and triage the deferred
Minors, then write the plan.

### 2026-10-30 - Make weekly chart geometry own drawing and selection

Extract the connected calculation into the approved in-file geometry model.
Drawing, pointer selection and composition tests consume that model; its
numeric stack and coordinate conversion stay private. Migrate existing
behavior tests and remove superseded hooks and a constant-pin assertion.
The suite drops five redundant cases, with no new test module or dependency.
The developer README links to the interface owner. Scope and owner-approved
exceptions remain those in the design; no further deviation is introduced.

The focused harness passed 142 tests. The full suite measured **3108 passed**
in 227.30 seconds; a later unused test-hook removal passed the focused
harness again. Chromium and Firefox each matched the exact old runtime's
paths, ranks, columns, 51 pointer cases and 30 keyboard outcomes across six
seeded fixtures. The full frontend gate passed 58 checks in 89 runs across
both engines and desktop, mobile and wide-touch profiles. The frozen-source
full suite then passed again in 205.55 seconds. Independent final code/spec
and standards reviews completed whole-file reads and found only a stale
README date, now corrected and re-reviewed. Archive rotation preserved
existing dated entries exactly. All hooks and final docsync pass; the
implementation commit is ready for a template PR. CI and publication state
will be recorded there, without merging.
The plan records final review and publication guidance:
`docs/superpowers/plans/2026-10-30-weekly-chart-geometry.md`.

### 2026-10-30 - Protect weekly chart geometry before extraction

Extend the existing browser alignment check with actual path extents,
plot bounds and one shifted-spike fixture. Extend the existing nearest-week
test with the exact midpoint. No runtime, test module or permanent check
family is added. The plan's first implementation step protects current
behavior before its calculation moves.

The pure harness passed 147 tests. Chromium and Firefox passed the affected
alignment check; both rejected a temporary out-of-band halo and passed
again after restoration. The full suite measured **3113 passed** in 210.85
seconds. Final hooks and docsync run before the test-only commit. Also
repoint the current Listening status to its observed merge, preserving the
dated execution records. The owner-approved deviations stay
as recorded in the design. The next step is the geometry module and test
migration in `docs/superpowers/plans/2026-10-30-weekly-chart-geometry.md`.

### 2026-10-30 - Approve the weekly chart geometry side task

The owner selected the first architecture-review proposal and approved the
in-file geometry model. Record the design and two-step implementation plan
before moving runtime calculation: protect the current rendered geometry,
then deepen its calculation and migrate the consumers and composition test.
This is a side task, not a new Batch 23 work package.

The owner explicitly permits this two-copy consolidation as a bounded
exception to global Rule 3, a clean worktree from main with WT003 advisory,
and one final independent review rather than per-commit/task reviews.
All other gates and the PR template still apply. The original preview and
its unrelated owner files remain outside this branch. The clean-worktree
suite measured **3113 passed** in 198.05 seconds. Baseline hooks passed;
final docsync and hooks are rerun after this entry is rendered. Forward
guidance and execution checkboxes live in
`docs/superpowers/plans/2026-10-30-weekly-chart-geometry.md`.

### 2026-10-29 - Reconcile Listening design notes after bot review

The owner authorized opening PR #280 after green CI and fixing bot concerns.
Quality Gate run `40880774113` succeeded at 014c6d75; the PR left draft and the
template checklist was updated. Codex completed without findings. Graphify's
three inline coupling advisories were checked against source and the base;
the shared fixture and interaction assertions remain cohesive. Replied with
that evidence and resolved the threads without metric-driven refactoring.
Its additional helper advisories concern residual-only coverage.

The documentation check found old Heatmap copy and a width-only result
description in the current reconciliation table. Correct four current rows
to reference source owners and the approved Listening follow-up. Preserve
the frozen snapshots and dated sections. The full suite measured
**3113 passed** in 145.79 seconds; no tests or runtime code changed. Repository
hooks and final docsync passed before the focused documentation commit.
After pushing, verify the new head's CI and bot feedback and fast-forward
the owner preview. Qlty's status passes but its description reports 13
blocking issues; the detailed list requires separate login and has not been
validated. The execution record is
`docs/superpowers/plans/2026-10-28-streamgraph-context-halo.md`.

### 2026-10-29 - Verify Listening profile guards and prepare the handoff

The owner requested Listening blur verification, review of uncommitted files
and a durable close-out handoff. Listening already uses the same validator
endpoint as Top albums, sets custom validity for missing/private profiles,
and checks it before AJAX submission. No production validation refactor was
needed. Extend the existing profile gate to challenge Enter and button
submission at the request boundary, then prove a corrected public name can
submit. Chromium and Firefox pass against the feature server and actual
owner preview; removing Listening's guard produces rejected POSTs and fails
the check. The full suite measured **3113 passed** (2954 non-browser tests
in three shards plus 159 browser tests). The frontend gate passed 58 checks
in 89 runs. Pre-commit and docsync passed; no test modules or dependencies
were added.

The independent uncommitted-file audit is recorded in
`docs/history/reports/UNCOMMITTED_WORKTREE_AUDIT_2026-10-29.md`. Its product
preview hashes match the pushed feature commit. Independent owner files and
dirty scratch worktrees remain preserved. Fresh unfinished-tool evidence is
linked under existing F-SWE-8; that tooling remains owner-gated and unadopted,
and was not staged or used as test evidence. The requested OS-temp handoff
is written and receives the final pushed commit and validation checkpoint
at close-out. Whole-file review found no material issue. Archive rotation
was verified mechanically against dd69ddd7 without claiming a semantic
reread of unrelated historical content.

### 2026-10-29 - Animate the transition into the Listening form

Side task on `feat/streamgraph-bursts`. The owner requested an upward card
collapse from Top albums to Listening, followed by the supporting illustration
fading in. Reuse the existing capture listener and measured card geometry,
reserve the destination panel height, and restore natural sizing after the
CSS animation ends or is cancelled. Reduced motion and Pause animations both
show the final state immediately, including preference changes mid-effect.

Extend the existing entrance-motion gate rather than adding a test family.
Focused Chromium and Firefox checks pass for actual geometry and opacity,
rapid switches, subsequent content growth and preference cancellation. The
existing display-scale gate also passes in both engines. Replacing the new
CSS with the previous revision makes the motion check fail. The full suite
measured **3113 passed**: 2954 non-browser tests in three shards plus 159
browser tests. The complete browser gate passed 58 checks in 89 runs. Final
Chromium/Firefox checks also pass with a saved pause choice and real keyboard
switching. A stylesheet-contract failure required local auto defaults for the
measured height properties; the 126 template checks and affected shard pass
after that correction. Pre-commit and final docsync passed. The execution
checklist and rationale are in
`docs/superpowers/plans/2026-10-28-streamgraph-context-halo.md`.

### 2026-10-29 - Balance the Listening entry form with an output illustration

Side task on `feat/streamgraph-bursts`. The owner requested a restrained use
of the empty desktop area below the Listening username card. Add an unboxed,
decorative daily-grid and artist-ribbon schematic inside the existing mode
panel. Reuse the chart palette helpers and theme tokens; keep it desktop-only
and preserve the shared album-form height and submission path.

Independent spatial and source reviews found no material issue. After a local
comparison, the owner requested removal of the caption and preferred the
original straight ribbon ends over a tapered variant. Those preferences are
applied. The existing page entrance remains the only fade; no animation or
control was added. The full suite measured **3113 passed** (2954 non-browser
tests in three shards plus 159 browser tests); the complete frontend gate
passed 58 checks in 89 runs. Focused Chromium/Firefox probes verify both themes,
stable mode-tab positions and no added page height. The existing home layout
still scrolls at 1024x768 because of its left-column text; the example fits.
Pre-commit and docsync passed. The optional design detector
ran in degraded regex mode because its parser modules are unavailable; its
findings concern existing styles, so it is not evidence of computed contrast.
The execution checklist is in
`docs/superpowers/plans/2026-10-28-streamgraph-context-halo.md`.
