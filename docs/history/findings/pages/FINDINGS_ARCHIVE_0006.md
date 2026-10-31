<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0006

### F-B21-3: 115 dependency advisories, and unused packages ship to production -- RESOLVED

The Quality Gate's `pip-audit` step reported `Found 115 known vulnerabilities
in 12 packages` (run 32444711411, 2026-08-21). The step is
`continue-on-error: true` in `.github/workflows/test.yml`, so the gate stays
green and the count reaches nobody. That disposition is deliberate and is
recorded in `docs/agents/AGENT_NOTES.md`; the disposition is not the problem, the number
is. Nobody reads a green check.

**Unused packages ship to production.** The Dockerfile installs
`requirements.txt`, and that file reads like a `pip freeze` dump: it pins
developer tooling (`virtualenv`, `distlib`, `filelock`, `platformdirs`)
beside real runtime dependencies. Six packages are imported nowhere in
tracked Python: `pypdf`, `pdf2image`, `pillow`, `virtualenv`, `ipinfo`,
`cachetools`. `pypdf` alone carries seven of the advisories. All six
entered in the initial `0ea2313` "Fresh start" commit rather than alongside
any feature, which fits a `pip freeze` taken from a wider environment.

The PDF packages are not the JPEG export, which is entirely client-side --
`static/js/results.js:178-266` uses `html2canvas` and
`canvas.toDataURL('image/jpeg', 0.95)`, and no server-side image or PDF code
exists. Poppler *is* installed on the owner's development machine, so
`pdf2image` could run there; it cannot run in production, because the
`Dockerfile` is a bare `python:3.13-slim` that installs no system packages at
all. Confirm the local workflow before removing them.

**The advisories that matter here sit on the outbound path** to Last.fm and
Spotify. `requests` 2.32.3 can leak `.netrc` credentials on crafted URLs
(PYSEC-2026-1872, fixed in 2.32.4). `urllib3` 2.2.3 forwards headers across
origin on redirect and decompresses without bound (PYSEC-2026-141, -1994,
-1996, -1998). By contrast the `werkzeug` `safe_join` advisories are
Windows-only and `send_from_directory` is never called, so they are noise for
this deployment -- count them out before anyone reacts to the raw 115.

A shape, not a decision: split runtime from developer requirements, drop what
nothing imports, then upgrade the outbound HTTP libraries. Resolve the
dependency graph before removing anything -- `pillow` is plausibly present as
`pdf2image`'s dependency rather than on its own.

- [x] **Status:** resolved
**Completed:** 2026-09-27
the unused PDF-adjacent packages were already removed and `requests`/`urllib3` already
upgraded past their advisories (`0f5b2468`, `c1620a9d`); the remaining unused-tooling
pins (`virtualenv`, `distlib`, `filelock`, `platformdirs`) are now moved to
`requirements-dev.txt`, still pinned; a live `pip-audit` recount on 2026-09-27 reported
no known vulnerabilities against `requirements.txt` alone, and none against both files
together.
Source: Quality Gate run 32444711411, 2026-08-21.

### F-B21-22: theme follows the system only until the toggle is first used -- RESOLVED

`templates/base.html` picks the pre-paint theme with
`saved === 'true' || (saved === null && matchMedia('(prefers-color-scheme: dark)').matches)`.
That is correct for a first visit. But the toggle is a two-state switch that
writes `'true'` or `'false'`, and `saved === null` is then never true again, so
one click permanently detaches the page from the system preference. There is no
way back to "follow the system" short of clearing site data.

Owner reported being served light while their system default is dark, which
this explains: a stored `'false'` from earlier review outranks the media query.
`theme.js` writes only on `change`, so nothing persists a value the reader did
not choose -- the mechanism is working, the model is missing a third state.

Remedy: store `'system'` as a third value and default to it, or drop the key
when the chosen state matches the system so the preference reattaches. Either
needs the pre-paint script and `theme.js` to agree, and a gate check that a
stored choice still survives a reload.

- [x] **Status:** resolved
**Completed:** 2026-09-27
The toggle's change handler clears darkMode when the chosen state matches the system
query, so the pre-paint script's existing saved === null branch reattaches to the system;
check_theme_reattaches_to_system proves it live.
Source: owner review of the deployed merge, 2026-08-26.

### F-MAS-1: mocks may drift from API reality -- RESOLVED

No contract tests or recorded API fixtures; upstream format changes would
pass mocked tests. Source: MULTI_AGENT_SWEEP.

- [x] **Status:** resolved
**Completed:** 2026-09-26
`tests/fixtures/` holds Spotify and Last.fm response shapes transcribed
from each provider's published reference; `tests/test_provider_fixtures.py`
pins the app's own field reads against them and checks one existing mock
for drift -- a weaker guarantee than a live contract test, recorded as
such (Q7 answer a).

### F-LOAD-2: no integration tests in CI -- RESOLVED

All tests mock dependencies; an in-process `/results_loading ->
/progress -> /results_complete` test is on the README roadmap.
Source: load testing 2026-03-04.

- [x] **Status:** resolved
**Completed:** 2026-09-26
`tests/test_pipeline_integration.py` drives the real `/results_loading ->
/progress -> /results_complete` route sequence through the Flask test client, joins
the real `worker.start_job_thread` background thread before trusting anything past
its terminal `/progress` state, and asserts the MusicBrainz hand-off ran under mock,
the job's concurrency slot is fully released, and `/results_complete` renders the
album that survived the Spotify phase.

### F-B21-18: browser JavaScript has no automated unit coverage -- RESOLVED

There are more than 2,400 lines under `static/js/`, with no `package.json`,
test runner or `.test.js` anywhere in the repository.
`docs/SWE_AUDIT_CHARTER.md` also excludes `static/js/` from the audit, on the
grounds that Batch 21 rewrites it -- which is true, and leaves the rewritten
code as the only code in the batch that nothing checks at unit level.

Five of the first nineteen review comments in this batch came from that gap: a
validation message never cleared, a join year leaking between accounts, a
daily average rounding a positive total to zero, a form that submitted a
username it had already been told was invalid, and an export header laid out
for one screen width that painted over itself on another.

The export is the sharpest case. `saveHeatmapImage` draws a canvas by hand,
and it cannot be reached by any check as it stands: it needs a rendered
heatmap, so it needs live Last.fm data and a key, which does not belong in
CI.

Independent PR review confirmed the untested path is already off contract:
`docs/design/components/heatmap/HeatmapFrame.prompt.md` requires JPEG export
to render the desktop 53x7 grid at every viewport, while
`saveHeatmapImage()` serializes whichever mobile or desktop SVG is on screen.
Its own docstring records the deviation, but no owner ruling adds that
deviation to `docs/design/RECONCILIATION.md`. A pure render seam would make the
contract testable without a Last.fm key and let mobile export use the desktop
geometry without changing the visible page.

**Do not add Node.** The batch decided against a `package.json`, and the
repository already owns a JavaScript engine it paid for -- Chromium, through
the pinned Playwright runtime the frontend gate uses. The blocker is only
that every module is an IIFE with no exports. A guarded seam, exposing pure
functions when a test flag is set and nothing otherwise, would put
`rocketColor`, `countToNorm`, `computeStreak` and the export's header layout
under test for about eighty lines of harness.

DOM-state defects are a different half and are already being covered where
they bite: `check_validation_feedback` in the frontend gate was written after
this batch's stale-message defect and fails on both forms when the fix is
removed.

The two username validators are also duplicated state machines:
`static/js/index.js` owns the album version and `static/js/heatmap.js` owns the
heatmap version. Their success work differs, but request freshness, outage and
failure semantics do not. The independent review first found that only the
heatmap catch discarded a stale failed request. The sibling fix compared field
values in both consumers, and the final self-review found that still fails an
A-to-B-to-A sequence because the oldest and newest requests carry the same
text. Both now use request generations, with the browser gate holding the ABA
case. Centralise that shared base only after broader browser parity checks
cover both consumers; refactoring it before then would trade a demonstrated
shotgun-surgery bug for an unproved rewrite.

- [x] **Status:** resolved
**Completed:** 2026-09-26
rocketColor, countToNorm and the export header layout are exercised by a
Chromium harness (tests/frontend/test_heatmap_pure_functions.py) through
window.__scrobbleHeatmapTestHooks, exposed at the module's top level;
computeStreak is WP-6's per Q14 answer a (docs/superpowers/
plans/2026-09-23-batch23-wp0-reconcile-and-clear.md, Owner answers 2026-09-23, Q14 answer a).
Residual items (53x7 export contract, duplicated validators) moved to F-B23-9.

The timing is the reason for that position. WP-5 and WP-7 are the two
remaining JavaScript-heavy pages, so a seam built before WP-5 still guards
work this batch does; built at WP-8 it would guard nothing here. The DOM
half is deliberately excluded, because the frontend gate already covers it
where it bites -- 2026-08-26 is the worked example: a real pre-paint theme
defect was caught by a browser check reading `data-theme` under blocked
storage, which no unit test of a pure function could have seen.

Placing it needs care. `WP_SKIPPED_RE` and the DOC007 derivation read work
package numbers from PLAYBOOK Section 4 headings, and WP-6 is already
absorbed into WP-3, so the number this takes and how the definition records
it must be settled before the first commit rather than discovered by a red
gate.
Source: Batch 21 WP-3 review analysis, 2026-08-25. Scheduled by owner
ruling, 2026-08-26.

### F-B21-20: the Tailwind hook and commit procedure disagree on staging order -- RESOLVED

`AGENTS.md` requires `pre-commit run --all-files` to pass before any path is
staged. The `tailwind-css-drift` hook rebuilds `static/css/tailwind.css`, then
runs `git diff --exit-code` against the index. A correct source-and-output edit
therefore fails before staging for the same reason a stale output fails: both
make the generated file differ from the index. Rebuilding again does not
change that answer.

The hook passes at commit time after the source and generated output are
staged, which is the state its Batch 21 acceptance criterion describes. The
manual commit procedure demands the opposite state. This review had to run
all hooks with an exact-name staged candidate, compare the index tree before
and after, and restore the index afterward; otherwise the final gate could
never be green.

- [x] **Status:** resolved
**Completed:** 2026-09-26
`AGENTS.md`'s commit procedure now stages named paths (step 4) before
`pre-commit run --all-files` (step 5), so the `tailwind-css-drift` hook's
index comparison sees the change being committed instead of the prior
commit's bytes (Q5 = a).

Source: PR #218 final verification, 2026-08-25.

### F-WORKTREE-3: guard boundaries outside the design decision table -- RESOLVED

Confirmed but unaddressed: between batches the guard skips every ancestry
check by design, which is exactly when the rebase-merge artifact appears,
so a genuinely diverged branch passes silently; WT010 never fires for a
detached dirty worktree, which returns WT012 alone; and
`missing_base_remediation` receives an already-labelled ref, so an unsafe
ref name renders as "the local base ref configured base ref".

The fourth item originally listed here -- `resolve_venv` deriving the primary
checkout from the common Git directory's parent -- was fixed in an earlier
PR's round-2 remediation, which discovers the main working tree with
`git worktree list --porcelain` and passes it in. The remaining three were
the between-batch ancestry skip, the missing WT010 on a detached dirty
worktree, and the doubled base-ref label.

**Owner ruling, 2026-09-23:** the between-batch ancestry skip is an accepted
design boundary, not a defect, and stays as documented. WT010 on a
detached, dirty worktree and the doubled base-ref label stayed open until
this fix.

- [x] **Status:** resolved
**Completed:** 2026-09-26
WT010 now fires for a detached, dirty, local (non-CI) worktree:
`classify_lineage` (`scripts/dev/_worktree_guard_lineage.py`) appends the
dirty diagnostic instead of returning early, and the detached, non-CI
branch of `inspect_worktree` (`scripts/dev/_worktree_guard_inspection.py`)
now measures dirtiness with the same status call the attached path uses,
so the fix reaches the real CLI, not only the classifier in isolation.
`missing_base_remediation` now branches on the raw base ref instead of an
already-labelled placeholder, so an unsafe ref's remediation text names the
placeholder once, in the correct branch
(`scripts/dev/_worktree_guard_diagnostics.py`). The between-batch ancestry
skip remains the owner's 2026-09-23 accepted design boundary.

Source: PR #169 independent review.

### F-DOCSYNC-6: known DOC001 and count-derivation boundaries -- RESOLVED

Cases the PR #169 review round confirmed and deliberately left unfixed
because each needs a design decision rather than a patch:
four-space indented blocks are still scanned for references, because the
canonical documents use that indentation for list continuations and
excluding it would silently disable DOC001 across much of AGENTS.md;
prose added after the last Section 4 entry is never reference-checked;
`cli.py` glob discovery is case-insensitive on Windows and case-sensitive
on Linux while candidate matching uses `re.IGNORECASE`; a live document
resolving outside the working directory raises `ValueError` rather than
the documented exit 2; and a file deleted on disk with the deletion
unstaged still counts as tracked.

**Owner ruling, 2026-09-23:** the four-space indentation scan, the no-check
on prose added after the last Section 4 entry, and the deleted-but-unstaged
file counting as tracked are accepted design boundaries, not defects, and
stay as documented. F-DOCSYNC-21 addresses the outside-root `ValueError`.

- [x] **Status:** resolved
**Completed:** 2026-09-25
The case-inconsistent-glob item is fixed by `_batch_filename_candidates`
(`scripts/docsync/cli.py`), matched with the same case-insensitive regex
every other discovery site already uses; the outside-root item was
confirmed already fixed by `88f0514` (F-DOCSYNC-21); the three remaining
items (four-space indentation scan, no-check on trailing prose,
deleted-but-unstaged files) are the owner's 2026-09-23 accepted design
boundaries and stay as documented.

Source: PR #169 independent review.

### F-DOCSYNC-15: a work package reads as complete on its first tagged log entry -- RESOLVED

`scripts/docsync/parser.py` `_collect_wp_numbers` counts every `WP-<n>` token in a current-batch entry heading as a completed work package, so the first commit of a multi-commit work package already makes the dashboard name the next one. `docs/history/logs/BATCH22_LOG.md` shows it happened: three `(Batch 22 WP-4)` entries landed on 2026-09-20 before WP-4 was done. Nothing went red, because DOC007 compares only against a claim someone wrote, and nobody wrote "WP-5 is next" in that window. Batch 23 WP-0 works around it by logging untagged until the package closes (owner ruling, 2026-09-23). The fix shape is Q4 of `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`. The owner chose the fix shape on 2026-09-23 -- a work package closes only on an entry carrying an explicit `**Status:** WP-N complete` line -- and the control-plane follow-on plan implements it.

- [x] **Status:** resolved
**Completed:** 2026-09-25
`_collect_wp_numbers` (`scripts/docsync/parser.py`) now requires an explicit
`**Status:** WP-N complete` line in an entry's body; a heading's
`(Batch N WP-X)` tag alone no longer marks that package done (Q4 = a).

Source: Batch 23 WP-0 definition amendment and triage D, 2026-09-23.

### F-DOCSYNC-7: `_latest_test_count_from_entries` has no production caller -- RESOLVED

The bare-count wrapper lost its last production caller when the integrity gate
moved to `latest_test_count_authority`. It is now exercised only by its own
unit tests in `tests/test_docsync_test_count.py`, which is the same condition
that led to `_cross_validate` being removed rather than kept.

Deliberately not removed in the review round that created the condition:
deleting it also rewrites eight test call sites, which is a refactor rather
than a review fix. Remove it and repoint those tests at
`latest_test_count_authority` in a hygiene pass.

- [x] **Status:** resolved
**Completed:** 2026-09-25
The eight `TestLatestTestCount` call sites now call
`latest_test_count_authority(...).count` directly; the wrapper
`_latest_test_count_from_entries` is deleted from `scripts/docsync/logic.py`.

Source: PR #169 review round 5.

### F-MAS-3: test_docsync_logic.py covers several unrelated seams -- RESOLVED

One module holds WP collection, test-count authority, whole-sync
integration, log merging, archive splitting, dedup, and Section 3 parsing.
Splitting along those class boundaries stays worthwhile. The originally
suggested `cross-validate` seam no longer exists -- that helper and its
tests were removed on this branch. Count authority is now split across two
files rather than extracted from this one: `TestLatestTestCount` still holds
the unit cases here, while `tests/test_docsync_test_count.py` covers the
behaviour through `_sync`. Consolidating them is part of the same split.

No line count is quoted here deliberately: the figure in the original
finding went stale as soon as the file changed, and size was never the
defect. Compare against the largest peer in the directory when deciding
whether the split is due.

- [x] **Status:** resolved
**Completed:** 2026-09-25
`tests/test_docsync_logic.py` is split along its seven seams: WP collection,
test-count authority (consolidated into `tests/test_docsync_test_count.py`),
whole-sync integration, log merging, archive splitting plus dedup, and
Section 3 parsing.

Source: MULTI_AGENT_SWEEP.

### F-DOCSYNC-13: the test count is parsed from prose when it could be measured -- RESOLVED

`--fix` cannot publish a measured test count, and `--check` refuses a
hand-written one. Both follow from the same design: `latest_test_count_authority`
(`scripts/docsync/logic.py`) resolves the count by parsing `**N passed**` out
of dated log entries under a total ordering, and DOC005, DOC006 and DOC008
recompute that ordering and compare the named fields against it. A field
edited to the number a real run produced is therefore drift, and is rejected.

Measured 2026-09-20: the suite was 1522 passing while every dashboard field
read 1497, because two entries dated the same day each carry a count and
same-date precedence ranks the untagged side-task entry above the batch
entries regardless of which was written later. That tie is F-DOCSYNC-11; this
finding is the reason it cannot simply be overridden by hand.

**Why `--fix` does not just run pytest.** `docs/agents/global-rules.md` Rule 7
lets the engine rewrite only what it can derive deterministically from facts a
human already authored. Running a test suite is measuring the world, not
deriving from an authored fact, and it would put a minute of test execution
inside a documentation tool that the pre-commit hook calls.

**Proposed shape, for the owner to rule on.** Let the author supply the
measurement instead of the tool taking it: an explicit input --
`--test-count N`, or a small machine-written artifact a test run drops -- that
`--fix` writes into the managed block *and* the three hand-maintained fields
(SESSION_CONTEXT Section 1's Tests row, its Section 6 heading, and the
FINDINGS header), with `--check` comparing against the same input. The
measurement stays human-authored, the copies stop being hand-typed, and the
same-date tie stops mattering for every field a reader actually looks at.
F-DOCSYNC-12 already records that `--fix` rewrites none of those three today.

- [x] **Status:** resolved
**Completed:** 2026-09-25
An explicit `--fix --test-count N` (`scripts/docsync/cli.py`) pins the count in
`config/docsync.toml`'s `[test_count]` table (`scripts/docsync/declarations.py`
`TestCountConfig`), which `resolved_test_count_authority` (`scripts/docsync/logic.py`)
reads instead of re-deriving from Section 4 prose position; `rewrite_recorded_counts`,
`_rewrite_findings_header_count` and `_rewrite_test_count_pin` write all four sites plus
the pin from it in one `--fix` run; a new DOC025 warns, without blocking, when the newest
dated log entry disagrees with the pin (Q1 ruling).

Source: Batch 22 close-out, 2026-09-20.

### F-DOCSYNC-22: a count corrected in an older same-date entry stays shadowed until the entry is moved -- RESOLVED

`latest_test_count_authority` (`scripts/docsync/logic.py`) orders live
side-task entries newest-first by their position in PLAYBOOK Section 4. When
two entries share a date, the upper one is authoritative. Position records
when an entry was written. It does not record when its count was last edited.
F-DOCSYNC-11 assumes the opposite ("Position within each source already
encodes recency"). Its tie is between two sources; this one is inside one.

Reproduced 2026-09-24, root-cleanup Task 6 fix round 1 (`c959237`). The Task 6
entry and the Task 7 entry above it both recorded **1849 passed**. The fix
round added one test and corrected the Task 6 entry to **1850 passed**. The
authority still read 1849 from the Task 7 entry, so DOC006 and DOC008 rejected
the true count in `.claude/SESSION_CONTEXT.md` and the FINDINGS header. The
only compliant remedy was to move the Task 6 entry above Task 7's. That makes
Section 4 misstate the order in which the work was done.

The Q3 fix for F-DOCSYNC-11, -12 and -13 (an explicit `--fix --test-count N`
input, in `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`)
covers this case only if `--check` stops recomputing the count from entry
position. The control-plane plan fixes it in that same task and tests this
case. It joined WP-0 Part C's set by owner amendment on 2026-09-25.

- [x] **Status:** resolved
**Completed:** 2026-09-25
An explicit `--fix --test-count N` (`scripts/docsync/cli.py`) pins the count in
`config/docsync.toml`'s `[test_count]` table (`scripts/docsync/declarations.py`
`TestCountConfig`), which `resolved_test_count_authority` (`scripts/docsync/logic.py`)
reads instead of re-deriving from Section 4 prose position; `rewrite_recorded_counts`,
`_rewrite_findings_header_count` and `_rewrite_test_count_pin` write all four sites plus
the pin from it in one `--fix` run; a new DOC025 warns, without blocking, when the newest
dated log entry disagrees with the pin (Q1 ruling).

Source: Batch 23 WP-0 root-cleanup ledger, 2026-09-24; filed on owner instruction,
2026-09-25.

### F-DOCSYNC-11: same-date precedence hides a batch count recorded after a side task -- RESOLVED

`latest_test_count_authority` in `scripts/docsync/logic.py` orders candidates by
date, then by source precedence, and ranks a live side-task entry above a
current-batch entry on a shared date. Its docstring states the assumption: "A
side-task entry is written after the batch entry it follows."

The assumption fails whenever batch work resumes on the same day as a side
task. Reproduced 2026-09-12: the side-task entry "Planning records preserved"
recorded **1026 passed** that morning, and the WP-7 entry written hours later
recorded **1028 passed** after two tests were added. The older count stayed
authoritative, so SESSION_CONTEXT and the FINDINGS header, both correct at 1028,
failed DOC006 and DOC008. The only compliant remedies were to publish a
superseded number or to restate the count in a side-task entry.

Position within each source already encodes recency; the cross-source tie-break
is where it is lost. A fix needs a design decision about what "newer" means
across the two lists, so it is recorded rather than patched.

**Reproduced again, 2026-09-14 (Batch 22 Task 8):** the
DB-connect-timeout side-task entry (same day) recorded **1081 passed**;
Task 8's own current-batch entry, written later that day, recorded
**1085 passed**. The authority stayed at 1081. Unlike the 2026-09-12
case, hand-correcting SESSION_CONTEXT/FINDINGS to the true count (1085)
was tried and rejected by `--check` outright (DOC005/DOC006/DOC008
recompute the same authority and compare against it), where the earlier
case's fix (F-DOCSYNC-12) only ever applied to fields the renderer never
recomputes. Confirms the same mechanism generalizes: a current-batch entry
written on a day that already has a side-task entry can have its count
silently shadowed until this is fixed.

- [x] **Status:** resolved
**Completed:** 2026-09-25
An explicit `--fix --test-count N` (`scripts/docsync/cli.py`) pins the count in
`config/docsync.toml`'s `[test_count]` table (`scripts/docsync/declarations.py`
`TestCountConfig`), which `resolved_test_count_authority` (`scripts/docsync/logic.py`)
reads instead of re-deriving from Section 4 prose position; `rewrite_recorded_counts`,
`_rewrite_findings_header_count` and `_rewrite_test_count_pin` write all four sites plus
the pin from it in one `--fix` run; a new DOC025 warns, without blocking, when the newest
dated log entry disagrees with the pin (Q1 ruling).

Source: Batch 21 WP-7 follow-up, 2026-09-12; reproduced Batch 22 Task 8, 2026-09-14.

### F-DOCSYNC-12: `--fix` does not rewrite two of the three fields DOC006 checks -- RESOLVED

`doc_state_sync.py --fix` only ever writes the "Latest validated test
count" line inside `.claude/SESSION_CONTEXT.md`'s `DOCSYNC:STATUS` block
(`scripts/docsync/renderer.py`). DOC006
(`scripts/docsync/integrity.py::SESSION_CURRENT_COUNT_RES`) checks that
line plus two more: the Section 1 "Tests" dashboard row and the Section 6
"Test structure (N tests)" heading. Neither of those two is ever rewritten
by `--fix`, so they can drift indefinitely -- reproduced 2026-09-14: both
sat at a hand-written "1036" untouched since 2026-09-11 through several
`--fix` runs across three later PLAYBOOK entries (1069, 1079, 1081
passed), each of which apparently updated the STATUS block correctly
without tripping DOC006. Why those earlier checks did not already fail on
the same mismatch is not established here -- worth checking before
assuming the mechanism above is the whole story. `docs/agents/FINDINGS.md`'s header
count line has the identical problem under DOC008: also hand-written,
also never rewritten by `--fix`.

Fix candidates: extend the renderer to also rewrite the Section 1 row,
the Section 6 heading, and the FINDINGS header from the same authoritative
count, or fold all three into one place `--fix` actually owns.

- [x] **Status:** resolved
**Completed:** 2026-09-25
An explicit `--fix --test-count N` (`scripts/docsync/cli.py`) pins the count in
`config/docsync.toml`'s `[test_count]` table (`scripts/docsync/declarations.py`
`TestCountConfig`), which `resolved_test_count_authority` (`scripts/docsync/logic.py`)
reads instead of re-deriving from Section 4 prose position; `rewrite_recorded_counts`,
`_rewrite_findings_header_count` and `_rewrite_test_count_pin` write all four sites plus
the pin from it in one `--fix` run; a new DOC025 warns, without blocking, when the newest
dated log entry disagrees with the pin (Q1 ruling).

Source: Batch 22 WP-1, DB-connect-timeout side task, 2026-09-14 (fix commit `c724ebc`).
