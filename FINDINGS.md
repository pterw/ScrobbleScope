# ScrobbleScope Findings & Open Issues

Last updated: 2026-09-21
Status: Batch 23 is active, opened 2026-09-21; Batch 22 closed 2026-09-20.
PLAYBOOK Section 3 owns the current work order.
1821 tests across 67 test modules.
**Rotation policy:** resolved and no-action findings rotate to
`docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out or during
findings-cleanup WPs; nothing is deleted. Every item uses an
`F-<context>-<N>:` heading (format: AGENTS.md "Finding-Writing Rules").
Read this file on demand -- when a task or PLAYBOOK entry references an
F-* ID or a P0/P1 item -- not as part of the standard bootstrap order.

---

## Severity Key

| Level | Meaning |
|-------|---------|
| **P0** | Fix before next deploy or next batch |
| **P1** | Next batch |
| **P2** | Scaling roadmap / future consideration |
| **Info** | Documented design choice, no action needed now |

---

## P0 -- Fix before next deploy

None open. The four P0 items open until 2026-09-23 were fixed before PR #238 deployed; see the archive.

## Resolved this batch

## P1 -- Next batch candidates

### F-DOCSYNC-15: a work package reads as complete on its first tagged log entry

`scripts/docsync/parser.py` `_collect_wp_numbers` counts every `WP-<n>` token in a current-batch entry heading as a completed work package, so the first commit of a multi-commit work package already makes the dashboard name the next one. `docs/history/logs/BATCH22_LOG.md` shows it happened: three `(Batch 22 WP-4)` entries landed on 2026-09-20 before WP-4 was done. Nothing went red, because DOC007 compares only against a claim someone wrote, and nobody wrote "WP-5 is next" in that window. Batch 23 WP-0 works around it by logging untagged until the package closes (owner ruling, 2026-09-23). The fix shape is Q4 of `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`. The owner chose the fix shape on 2026-09-23 -- a work package closes only on an entry carrying an explicit `**Status:** WP-N complete` line -- and the control-plane follow-on plan implements it.

- [ ] **Status:** open (P1). Source: Batch 23 WP-0 definition amendment and triage D, 2026-09-23.

### F-DOCSYNC-13: the test count is parsed from prose when it could be measured

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

- [ ] **Status:** open (P1, owner-gated -- needs a decision on the input shape)

Source: Batch 22 close-out, 2026-09-20.

### F-B21-3: 115 dependency advisories, and unused packages ship to production

The Quality Gate's `pip-audit` step reported `Found 115 known vulnerabilities
in 12 packages` (run 32444711411, 2026-08-21). The step is
`continue-on-error: true` in `.github/workflows/test.yml`, so the gate stays
green and the count reaches nobody. That disposition is deliberate and is
recorded in `AGENT_NOTES.md`; the disposition is not the problem, the number
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
Status: open. Source: Quality Gate run 32444711411, 2026-08-21.

### F-B21-9: the findings-to-issues mirror is manual

Open findings were mirrored to GitHub issues #174-#215 on 2026-08-22. The
mirror ran once, from a script that was not committed.

Nothing keeps it current. A new finding does not open an issue. A resolved
finding does not close one. The two lists will drift.

This was deliberate, not an oversight. A sync script is code. It needs tests
and a work package. It did not belong in the documentation PR that created
the mirror.

What a sync needs: open an issue for each finding that has none, close the
issue when its finding resolves, and never write back to `FINDINGS.md`. The
file stays the source of truth. Issues are a read-only mirror.

**Owner ruling, 2026-09-20:** the sync has to run in both directions --
GitHub issues to `FINDINGS.md` as well as out -- so neither side can become
the only place a defect is recorded.

- [ ] **Status:** open, deferred by owner decision
Was recorded as: open, deferred on purpose. The owner accepted the drift on
2026-08-22 and asked that the work be recorded rather than done now.
Source: findings mirror, 2026-08-22.


### F-B21-14: the heatmap has no path to its data that is not colour

Every value in the grid is encoded once, as a fill. The only way to read a
day is a mouse hover: the cells are `<rect>` elements with no `tabindex`, so
a keyboard reader cannot reach any of them, and there is no table view.

The ramp itself is sound. Measured in OKLab, `rocket_r` runs strictly
monotonic in lightness from 0.13 to 0.884 in steps of 0.107 to 0.144 -- a
reader who cannot separate the hues can still separate the values, which is
what a sequential ramp has to do. The `dataviz` skill's validator fails it,
but that validator is scoped to categorical palettes by its own footer, and
lightness monotonicity is the right test here.

The defect is at the ends, against their own surface. `#f9d576` sits at
1.34:1 on the light frame and `#03051a` at 1.12:1 on the dark one, so the
busiest and quietest days both disappear into the background they are drawn
on. The ramp is fixed by the design contract, so the fix is relief and not
re-tinting: make the cells focusable and give each an accessible name, or
ship a table view, or both.

**Owner ruled this critical on 2026-08-24**, while noting that a sighted
mouse user sees no problem. Both halves of that are the finding: it is
severe for the readers it affects and invisible to everyone else, which is
why no review caught it and no gate can.

Status: open. Owner-ruled critical. Not scheduled to a work package.
Source: Batch 21 WP-3, `dataviz` skill pass, 2026-08-24.

### F-B21-18: browser JavaScript has no automated unit coverage

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

Status: open, and **scheduled**. The owner ruled on 2026-08-26 that this
becomes a work package of its own, sequenced before WP-5, and is not folded
into WP-4. Scope is the pure-function seam only -- `rocketColor`,
`countToNorm`, `computeStreak` and the export header layout -- on the
Chromium the frontend gate already owns. No Node, no `package.json`.

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

### F-B21-20: the Tailwind hook and commit procedure disagree on staging order

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

Do not silently reorder the repository-wide commit procedure or rewrite the
hook inside a UI review. The owner needs to choose one contract: stage named
paths before pre-commit, or make `--check` compare the freshly built bytes with
the bytes present before the build instead of comparing the working file with
the index. Either choice needs a regression test for an intentionally changed,
already rebuilt stylesheet.

Status: open. Owner decision required; not assigned to a work package.
Source: PR #218 final verification, 2026-08-25.

### F-B21-22: theme follows the system only until the toggle is first used

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

Status: open, low severity. Owner decision on whether a three-state control is
wanted before WP-8 retires the second theme write.
Source: owner review of the deployed merge, 2026-08-26.

### F-B21-23: the inline marks diverge from the design contract on colour

`docs/design/README.md` "Assets" specifies the two inline variants as
**theme-reactive: text `currentColor`, bars `var(--bars-color)`**. Neither
shipped asset does it. `templates/inline/scrobble_scope_lockup_inline.svg` and
`scrobble_scope_inline.svg` contain zero occurrences of `currentColor`; the
letterforms carry no fill rule at all and the bars are pinned by an embedded
`<style>` to a literal `#6a4baf`.

This is the real cause of F-B21-21, which was fixed at the symptom. Because
the asset does not react to anything, every wrapper that displays it has to be
named explicitly in a stylesheet, and the index hero was the wrapper somebody
forgot. The list will need extending again for every mark WP-4 through WP-8
adds, and the gate check added with F-B21-21 exists only to catch that.

Doing what the contract says removes the class. Give the letterforms
`fill="currentColor"` and the bars `stroke: var(--bars-color)`, then any
wrapper that sets `color` and defines that token gets a correct mark with no
selector naming it. The per-wrapper list in `shell.css` collapses to nothing.

Two reasons it was not done in the F-B21-21 fix. The assets are shared with the
four Bootstrap pages, which currently colour them through `global.css`
`.dark-mode`, and those pages render only from a POST with session state, so no
gate can show the result. And `--bars-color` is a `global.css` token while the
migrated pages use `--shell-accent`; the two carry different dark values
(`#9370DB` against `#b39dde`), so unifying the asset means first deciding which
value wins.

Status: open. Right shape for WP-8, alongside retiring `global.css` and the
second `.dark-mode` theme write. Doing it there makes one change instead of
three.
Source: F-B21-21 follow-up, 2026-08-26.

### F-B21-25: every gate runs at commit time, so the session is unguarded

The documentation integrity gate, the compiled-CSS drift hook and the test
suite all run through `pre-commit`. They work: each was mutation-tested on
2026-08-26 and each caught its defect with the right code. They also share
one blind spot.

**Nothing runs at session time or at filesystem time.** Deleting local
files, removing a worktree, deleting a branch and force-replacing its
remote produce no commit, so no gate is consulted. On 2026-08-25 a session
branched from `origin/main`, made three commits with no PLAYBOOK Section 4
entry, renamed the branch over the retained one and replaced its remote.
Every gate stayed green. A reviewer caught the missing entry, not a check.

Three causes, each fixable on its own:

1. **The worktree guard was wired to nothing.** It exits 1 on an ERROR
   diagnostic and 0 otherwise, so it was built to gate, but it appeared in
   no hook and ran only when somebody chose to run it.
2. **Bootstrap was self-referential.** The rule that says to read
   `AGENTS.md` lives in `AGENTS.md`. A session that does not open it never
   learns it should. `.claude/settings.local.json` carried a permission
   allowlist and no hooks at all.
3. **What was lost was gitignored.** `skills-lock.json` is still missing.
   Git protects tracked files; the workflow depends on untracked ones and
   nothing declares which of them matter.

**Two structural defects in `AGENTS.md` itself.** Its "Session Bootstrap
(in order)" section opens with two fast-path paragraphs that authorise
skipping bootstrap, placed above the numbered list, so a skim finds the
exemption before the obligation. And the file has accumulated origin
narrative: agents editing it explain why a rule came to be written, which
serves the editor and not the reader. A bootstrap ruleset is read cold and
under pressure. Rationale belongs in a finding or a PLAYBOOK entry; the
rule should state the intent and stop. This is the specific mechanism
behind the length problem, and it is narrower than `F-STYLE-1`.

**Partly closed on 2026-08-26.** The guard now runs as the
`worktree-alignment` pre-commit hook, verbose so lineage is visible on a
passing run, and **advisory**: it prints and never gates.

That last word was wrong twice before it was right. The hook first shipped
gating, on the claim that only WT002, WT007 and WT014 are errors. A PR #220
reviewer corrected it: eleven of the fifteen codes are errors -- WT001,
WT002, WT003, WT004, WT005, WT006, WT007, WT008, WT012, WT014, and WT009
inside a linked worktree. WT003 fires for any branch the active batch does
not name, and WT004 for the identical-tree divergence a rebase merge always
leaves, so the gating version would have refused every commit on a feature
branch and every commit after a merge until realignment. The owner ruled it
advisory on 2026-08-26: the problem was that the guard's output was
invisible, not that commits needed a new gate. `--advisory` carries that,
and a test asserts it exits 0 on an ERROR while the same run without the
flag still exits 1.

The claim was wrong because the severity check grepped two of the guard's
six modules and generalised. That is the same incomplete-sweep mistake
`AGENTS.md` names, made while writing this finding about mechanisms that
only hold in one place.

It is skipped in CI, and the reason is worth keeping: the
first push went red on `ERROR WT007`, because `actions/checkout` makes a
shallow single-branch clone with no `origin/main`, so the guard failed
closed on a base ref that is legitimately absent. The guard measures
developer worktree lineage and a runner has no worktree topology to
protect, so the step sets `SKIP: worktree-alignment` rather than fetching
a base ref to satisfy a check that would then measure nothing. The
failure is itself an instance of this finding: a check added without
asking where it runs, whose assumptions held on one machine only. A `SessionStart` hook injects branch, working-tree state,
guard codes and the machine-managed status block into every new Claude
Code session, so the state arrives without depending on effort level,
model, or the model choosing to read. The second virtualenv the allowlist
had been authorising is deleted.

Remaining, and not started: a declared manifest of untracked-but-essential
files, in the shape of `.docsync.toml` so the mechanism carries no
repository facts; and the two `AGENTS.md` defects above. The Codex/Copilot
entry point moved to F-B21-63.

Status: partly closed. The remaining items need an owner ruling, because
two of them edit `AGENTS.md`.
Source: workflow review after the worktree retirement, 2026-08-26.

### F-DOCSYNC-6: known DOC001 and count-derivation boundaries

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
stay as documented. The case-inconsistent glob discovery and the
outside-root `ValueError` stay open; the control-plane plan fixes both.
Status: open. Source: PR #169 independent review.

### F-DOCSYNC-11: same-date precedence hides a batch count recorded after a side task

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

Status: open (P1). Source: Batch 21 WP-7 follow-up, 2026-09-12; reproduced
Batch 22 Task 8, 2026-09-14.

### F-DOCSYNC-12: `--fix` does not rewrite two of the three fields DOC006 checks

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
assuming the mechanism above is the whole story. `FINDINGS.md`'s header
count line has the identical problem under DOC008: also hand-written,
also never rewritten by `--fix`.

Fix candidates: extend the renderer to also rewrite the Section 1 row,
the Section 6 heading, and the FINDINGS header from the same authoritative
count, or fold all three into one place `--fix` actually owns.

Status: open. Source: Batch 22 WP-1, DB-connect-timeout side task,
2026-09-14 (fix commit `c724ebc`).

### F-WORKTREE-3: guard boundaries outside the design decision table

Confirmed but unaddressed: between batches the guard skips every ancestry
check by design, which is exactly when the rebase-merge artifact appears,
so a genuinely diverged branch passes silently; WT010 never fires for a
detached dirty worktree, which returns WT012 alone; and
`missing_base_remediation` receives an already-labelled ref, so an unsafe
ref name renders as "the local base ref configured base ref".

The fourth item originally listed here -- `resolve_venv` deriving the primary
checkout from the common Git directory's parent -- was fixed in this PR's
round-2 remediation, which discovers the main working tree with
`git worktree list --porcelain` and passes it in. The remaining three are
unchanged.

**Owner ruling, 2026-09-23:** the between-batch ancestry skip is an accepted
design boundary, not a defect, and stays as documented. WT010 on a
detached, dirty worktree and the doubled base-ref label stay open; the
control-plane plan fixes both.
Status: open. Source: PR #169 independent review.

### F-DOCSYNC-7: `_latest_test_count_from_entries` has no production caller

The bare-count wrapper lost its last production caller when the integrity gate
moved to `latest_test_count_authority`. It is now exercised only by its own
unit tests in `tests/test_docsync_logic.py`, which is the same condition that
led to `_cross_validate` being removed rather than kept.

Deliberately not removed in the review round that created the condition:
deleting it also rewrites eight test call sites, which is a refactor rather
than a review fix. Remove it and repoint those tests at
`latest_test_count_authority` in a hygiene pass.
Status: open. Source: PR #169 review round 5.

### F-LOAD-2: no integration tests in CI

All tests mock dependencies; an in-process `/results_loading ->
/progress -> /results_complete` test is on the README roadmap.
Status: open. Source: load testing 2026-03-04.

### F-MAS-1: mocks may drift from API reality

No contract tests or recorded API fixtures; upstream format changes would
pass mocked tests. Status: open. Source: MULTI_AGENT_SWEEP.

### F-MAS-3: test_docsync_logic.py covers several unrelated seams

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
Status: open. Source: MULTI_AGENT_SWEEP.

### F-B21-60: the artist spotlight card breaks Spotify's content guidelines

Spotify's design guidelines ("Using our content",
https://developer.spotify.com/documentation/design#using-our-content) forbid
cropping artwork, putting images or text over it, animating it, and using
Spotify metadata without the Spotify logo or icon and a link back to Spotify.
The results page's artist spotlight (`templates/results.html`
`artist-spotlight-card`, `static/css/results.css` `.spotlight-card-bleed`,
`static/js/results-spotlight.js`) breaks these rules. The app uses the Web API
under Spotify's terms, so this is a compliance defect, not a taste question.

- **Crop:** Spotify artist photos are square, but the card is short and wide.
  `object-cover` cuts off the top and bottom.
- **Overlay:** `.spotlight-scrim-top` and `.spotlight-scrim-bottom` put
  gradients and text (the "Artist Spotlight" title, rank, name and play time)
  over the photo.
- **Animation:** every 7 seconds `renderCandidate` fades the whole card,
  photo included, to 15% opacity and swaps the artist.
- **Album art fallback:** with no artist photo, the card shows the first
  album's cover, cropped and overlaid (`spotlight_fallback_img`).
- **Attribution:** the app shows no Spotify logo or icon anywhere. The
  spotlight's link to Spotify is a plain arrow, shown only after hydration.
  Results rows already link each album to Spotify, but carry no Spotify icon.

Owner ruling, 2026-09-13, on the redesign:
- Show the artist photo whole, square, with 4px corners at small sizes and
  8px at large sizes. Nothing is drawn on top of it.
- Put the name, rank and play time beside or below the photo.
- Change artists without animating the photo. An instant swap is acceptable;
  reduced motion keeps the first artist, as today.
- **There is no text-only card and no album-art fallback.** A candidate with
  no Spotify artist photo is skipped in the rotation. If no candidate has a
  photo, the card is not shown at all. That includes the server render: do
  not render the card until an artist photo is known.
- Add the official Spotify icon, 21px or larger, linking to the artist on
  Spotify. Use Spotify's asset as supplied, not a redrawn glyph.
- Add the same icon next to the album links on results rows, or once as
  attribution for the list, whichever the guidelines' placement rules allow.
- Batch 22 adds Deezer as a fallback provider, so a row's artwork and link may
  come from either service. The attribution follows the album's own provider,
  under that provider's rules.

To check during the fix:
- whether the JPEG export captures Spotify artwork in a way the same rules
  forbid
- the gap where titles shown next to Spotify artwork are Last.fm spellings,
  not Spotify's metadata

Tests: route tests assert that the card is absent when no candidate has a photo
and that `spotlight_fallback_img` is gone. The frontend gate checks the photo
at its natural aspect ratio, no element overlapping the photo, no opacity
change on the photo during rotation, and the icon's rendered size and link
target.

**Partial progress, 2026-09-13 (Batch 22 WP-2 Task 6):** results and
unmatched rows now link to the album's own provider (`album_url`, not a
Spotify URL reconstructed from `spotify_id`) and carry a small text
attribution link naming that provider. This closes the "results rows carry
no Spotify icon" gap in substance but not to the letter -- it is a text
label, not either provider's official logo asset, so the ruling below is
still open. The artist spotlight card is unchanged: still cropped, still
overlaid, still animated. See F-B22-4 for the logo-asset gap.

Status: open (P1), owner ruling recorded. Source: Spotify API review,
2026-09-13.

## P2 -- Scaling roadmap

### F-DOCSYNC-16: docsync silently ignores an `allow_after` marker that matches no line

`check_retired` (`scripts/docsync/declarations.py`) compares a raw file line
against a declared `allow_after` marker with `line.strip() == marker.strip()`
-- exact equality, no prefix match -- and when nothing matches, `exempt_from`
simply stays `None`: the declaration silently loses its whole history
exemption for that file, with no warning that the marker itself is dead. The
three `[[retired]]` declarations in `.docsync.toml` that predate this finding
all declared `[retired.allow_after] "PLAYBOOK.md" = "## 4. Execution log"`,
but the real `PLAYBOOK.md` heading is `## 4. Execution log (for agent
handoff)`, so none of the three matched anything. Reproduced directly against
`check_retired` with the real heading text: a claim placed below the heading
was still reported, not exempted (confirmed 2026-09-24, Task 5's live probe
for the new fourth declaration that task added).

**Impact was latent, not live.** No dated Section 4 entry restated
`limit_results ... thresholds disclosure`, `fonts self-hosted under
static/fonts/` or a bare `DOC001-DOC011`, so `--check` on the real corpus
never actually exercised the mismatch before it was caught. It would have
surfaced as a false-positive DOC011 the day a dated entry legitimately quoted
one of those retired phrases as history.

**The three markers are corrected in `.docsync.toml`** (2026-09-24, Task 5
fix round) to the real heading text, matching the fourth declaration that
task added, which used the correct text from the start. That corrects this
one instance; the finding stays open because the mechanism -- a declared
`allow_after` marker can silently match nothing, for any file, and nobody is
told -- is still unchecked, so the next marker written this way fails the
same way undetected.

**Fix shape, not yet built:** a declaration check that errors when an
`allow_after` marker matches no line in its named file (a new check; not
built here).

- [ ] **Status:** open (P2). Source: Batch 23 WP-0 foundation Task 5 live
  probe, 2026-09-24.

### F-B22-5: the release-year lookup has a precision path it does not use

`lookup_original_release` (`scrobblescope/musicbrainz.py`) finds a release
group by searching artist and title text, then guards the result with a score
floor and a normalized identity check. It is one request and it is usually
right. It is not exact, and two measured cases show the edges.

**Measured against the live APIs, 2026-09-20**, five albums, one request per
second:

| Album | Spotify's date | URL path | Search path |
| --- | --- | --- | --- |
| The Beatles (White Album) | 1968-11-22 | 1968-11-22 | top candidate scored 100 with **no** `first-release-date` |
| Rumours | 1977-02-04 | 1977-02-04 | 1977-02-04 |
| Kind of Blue | 1959-08-17 | 1959-08-17 | 1959-08-17 |
| Geogaddi | 2002-02-19 | **not mapped (404)** | **no candidate returned** |
| Stratosphere | 1998-02-24 | 1998-02-24 | 1998-02-24 |

**The URL path.** `GET /ws/2/url?resource=https://open.spotify.com/album/<id>&inc=release-rels`
returns a "free streaming" relation to a MusicBrainz **release** when an
editor has mapped that Spotify album. A second request on that release with
`inc=release-groups` yields the release group's `first-release-date`. It is
exact -- no scoring, no name matching -- and it answered two cases the search
path did not. It costs **two requests where the search costs one**, which at
one request per second is the whole budget doubled, and it needs a Spotify
album id, so it can never serve a Deezer-only album.

Note for anyone implementing it: `inc=release-groups` on the `url` endpoint
returns nothing. The relation include is `release-rels`, and the target is a
release, not a release group. `inc=release-group-rels` returned zero
relations for the same album.

**The ISRC path is not viable as a third option.** `GET /v1/albums/{id}`
returns simplified track objects with **no** `external_ids`, confirmed by
reading the keys off a live response, so every ISRC costs an extra Spotify
request. `GET /ws/2/isrc/{isrc}` then returns *recordings*, and a recording's
earliest release group may be a single or a compilation rather than the album
-- dating an album by its lead single is worse than not correcting it.

**Recommended shape, not yet built:** keep the search as the primary path,
and spend the second request only where it buys something -- when the search
returns no candidate, or a candidate with no `first-release-date`, and the
album has a Spotify id. Cache the outcome under the existing
`(artist_norm, album_norm)` key, never under a Spotify id: 9 of the 10 albums
Spotify could not enrich in the owner's 2026-09-20 run were rescued by
Deezer, and those have no Spotify id at all.

**Also measured:** adding `AND type:album` to the Lucene query, as proposed,
would exclude EPs, which this application ranks alongside albums --
`normalize_name` deliberately strips "ep" from titles. The release-group
search field is `primarytype`, not `type`. If the query is narrowed at all,
it should be to exclude live albums and compilations by secondary type, not
to require a primary type.

- [ ] **Status:** open (P2, owner-gated -- a scope decision, not a defect)

Source: owner proposal and live probes, 2026-09-20.

### F-B22-6: server-sent events would consume the whole thread pool

Replacing the results page's polling with an SSE stream was proposed. It does
not fit this deployment. Gunicorn runs `--workers 1 --threads 4`
(`Dockerfile`), and an SSE response holds its worker thread open for the life
of the connection. Four readers with a results page open would occupy every
thread, and the fifth request -- any request, including the home page --
would wait for one of them to disconnect.

The current design has the opposite shape: a poll every two seconds that
stops at a terminal state, pauses while the tab is hidden, and holds a thread
only for the milliseconds each reply takes.

SSE would become reasonable only alongside a different serving model, which
is a larger change than the feature it would serve.

- [ ] **Status:** open (P2, no action recommended)

Source: owner proposal, measured against the Dockerfile, 2026-09-20.

### F-B21-62: the design system's status colours are documented but undefined

`docs/design/README.md` names three status colour pairs -- `--ss-good`
`#2f7a4a`/`#6fcf97`, `--ss-warn` `#b35a1f`/`#e0a458`, `--ss-bad`
`#b03434`/`#e07070` -- and states what they are for: "3px rules and mono
kickers, never as full-bleed tinted cards". No stylesheet defines any of the
three. `test_every_custom_property_a_page_reads_is_defined_by_a_sheet_it_loads`
fails any page that reads one, so the documented treatment cannot be used at
all, and the first attempt to use it (the release-correction kicker, Batch 22
WP-4 Task 11) had to pick a different token.

This is the `docs/ARCHITECTURE.md` rule in another form: the document is a
claim about the code that nothing checked, and the code wins. Either the
tokens ship in `static/css/tailwind.src.css` for both themes, or the README
stops describing a treatment nothing can apply. Sizing is small; deciding
which way is a design-system call, not an implementation one.

- [ ] **Status:** open (P2, owner-gated)

Source: Batch 22 WP-4 Task 11, 2026-09-20.

### F-SWE-8: the mutation-test runner is written, unadopted, and uncommitted

`scripts/dev/mutation_test.py` and `scripts/dev/mutation_scope.toml` exist in
the working tree and are not committed. They were built during the docsync
close-out side task, run for the first time against `scripts/docsync/`, and
that first run found four real defects in the runner itself, the fourth
needing a rework rather than a patch. The owner's call on 2026-09-20 was that
mutation testing is not adopted on the strength of a tool that had never been
run: finishing it is a work package of its own, and the code stays out of the
corpus until then.

This is recorded here because it was recorded nowhere a clone can read. The
only written copy was a section of the gitignored CLAUDE.md at the repository
root, and that section was deleted the same day once the work it tracked
merged. DOC001 is the reason that file name carries no backticks here: a
concrete Markdown reference has to name a tracked file, and it is not one.

Do not stage those two files as part of another task's commit, and do not
treat the runner's output as evidence until its own defects are fixed.

- [ ] **Status:** open (P2, owner-gated)

Source: docsync close-out side task, 2026-09-20. It is a future work package
rather than a defect in shipped code.

### F-B22-4: provider attribution on results/unmatched rows is text, not each provider's official logo

Batch 22 WP-2 Task 6 added a per-row attribution link (`.provider-badge` in
`templates/results.html` and `templates/unmatched.html`) naming the album's
provider and linking to its `album_url`. Deezer's developer guidelines
require "a clearly visible Deezer Logo" for any app using its API
(developers.deezer.com/guidelines#local, /guidelines/logo); F-B21-60 records
the equivalent Spotify ruling ("Use Spotify's asset as supplied, not a
redrawn glyph"). Neither provider's actual logo file could be sourced from
an agent session: no image-fetch tool was available, and guessing a brand
CDN URL to hotlink was rejected as unsafe. The owner chose the text-badge
interim over blocking Task 6 on asset sourcing (2026-09-13).

Fix shape: replace `.provider-badge`'s text content with each provider's
official logo asset once the owner supplies the files (or an agent gains
image-fetch tooling) -- swap the `<a>`'s text node for an `<img>`/inline
`<svg>` sized per that provider's own minimum-size rule (Spotify: 21px+, per
F-B21-60's owner ruling; Deezer: size unspecified on the guidelines page
itself, deezerbrand.com carries the detail but did not render for an agent
session). Small and self-contained; no test rewrite beyond swapping the
`provider-badge` element type assertions.

Status: open (P2). Source: Batch 22 WP-2 Task 6, 2026-09-13.

### F-B22-3: job endpoints trust an unguessable job ID with no session ownership check

`scrobblescope/routes/api.py` (`unmatched_data`, `progress`) and
`scrobblescope/routes/heatmap_flow.py` (`heatmap_data`) accept `job_id` from
a query parameter and look it up in the process-local `JOBS` dict with no
check that the requesting session originated that job. `create_job`
(`scrobblescope/repositories.py:41`) generates `job_id = uuid4().hex` -- a
128-bit unguessable value -- so the design already relies on the ID itself as
a bearer/capability token rather than session-bound ownership. This is
consistent across every job-polling endpoint, not a WP-0 regression: the
pre-split `routes.py` had the same shape.

Graphify's PR #232 review flagged two instances (`api.py:103`,
`heatmap_flow.py:179`) as missing an "ownership check," unverified
(consensus-only, no reproducing execution). Read as a security question
rather than a bug: is a 128-bit unguessable ID sufficient authorization for
an ephemeral (TTL-bounded, `JOB_TTL_SECONDS`) result set, or should these
endpoints also require the ID to match the requesting session's
`_LATEST_ALBUM_JOB`/`_LATEST_HEATMAP_JOB`? No incident or reported leak
motivates this; filed for owner judgment, not because current behaviour is
demonstrated wrong.

Status: open (P2, owner-gated). Source: Graphify bot review, PR #232,
2026-09-14.

### F-B23-1: album calculation writes its exclusions into the job instead of returning them

`orchestrator/_results._build_results` takes `job_id`, returns the album rows,
and sends each release-scope exclusion out through a hidden
`add_job_unmatched` call on the facade. So a test of a corrected-date
exclusion has to create a real job and read it back
(`tests/services/test_orchestrator_helpers.py` does). The calculation's
answer is also split between its return value and a side effect.

Batch 23 WP-6 adds per-album statistics to this same module. A calculation
that returns rows, exclusions and statistics together, with the caller
publishing them to the job, would give WP-6 a place to land those statistics
that can be tested without a job.

A migration can leave the Last.fm path's tests unmodified: add the pure
calculation, and keep `_build_results(cache_hits, job_id, ...)` as a thin
wrapper that publishes its result. The existing `orchestrator.add_job_unmatched`
patch target then still holds.

Status: open (P2). Owner timing, 2026-09-23: settle it after WP-0's provider
repairs and before WP-6's detailed design. Scheduling it inside Batch 23 needs
an explicit scope amendment, and `BATCH23_DEFINITION.md` WP-6 carries that
decision point. Source: card 01 of
`docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-2: Last.fm's payload shape travels into both calculations

`lastfm.py` returns raw JSON pages. `orchestrator.fetch_top_albums_async`
then reads `recenttracks`, `track`, `album.#text`, `artist.#text` and
`date.uts` itself, and `heatmap._aggregate_daily_counts` reads `recenttracks`
and `date.uts`. A change to Last.fm's payload therefore reaches two
calculations, and WP-6's first-listen and busiest-hour statistics would add
more of the same reads. Global Rule 4 puts that translation inside the
provider module.

The fix is to have `lastfm.py` translate the payload into native listening
facts, keeping completeness explicit. Two differences must survive:
- the heatmap counts dated rows even without album metadata, while album
  aggregation needs artist, album and track;
- the Spotify-export rules (30 seconds, private sessions) must not be imposed
  on Last.fm.

It cannot land inside Batch 23 as-is: `tests/test_heatmap.py` feeds
`_aggregate_daily_counts` raw pages, and Batch 23 keeps the Last.fm path's
tests unmodified. It is separate from F-B22-7, which translates Spotify's
metadata payload.

Status: open (P2). A parity refactor for a batch after Batch 23. Source:
card 02 of `docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-3: the album pipeline runs the cache connection protocol itself

`orchestrator.process_albums` opens the cache connection, holds it across
provider work, and closes it in a `finally`. Meanwhile
`orchestrator/_cache.py` owns the cache-failure policy, including writing job
warnings through the facade. So understanding what "the cache is optional"
means takes both modules. It also makes the connection-closure test in
`tests/services/test_orchestrator_process_albums.py` configure the provider
machinery.

The fix is for the existing cache module to own the operation's lifetime and
its failure classification, while job messages and enrichment decisions stay
with the caller. There is one concrete adapter, so no generic cache-backend
layer. Metadata and release-check cache policy stay separate.

Status: open (P2). F-B22-7 and F-B22-8 have both landed (reconcile Tasks
4-6 and 11); reassess against the code they left. No performance gain is
claimed. Source: card 03 of
`docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-4: the frontend gate's touch-target check failed once on a tree that passes

At `ffbee0e` the frontend gate failed once, and then passed three times on
the same tree. The failure was in `check_touch_targets`
(`scripts/dev/_frontend_gate_layout.py`), in the wide-touch profile, on the
404 page:

```
touch targets [wide touch]: /no-such-page-for-the-gate [as loaded]: a.btn is 124x40, smaller side under 44px
touch targets [wide touch]: /no-such-page-for-the-gate [as loaded]: button.btn is 89x40, smaller side under 44px
```

40px is the plain `.btn` height. On the 404 page the 44px comes from one
rule in `static/css/error.css`:
`@media (any-pointer: coarse), (max-width: 859.98px)`. The wide-touch
profile is 1280px wide, so only the `any-pointer: coarse` half can match
there. The mobile profile also matches on width, which is why it never
failed. So at measurement time that rule was not in effect. Either
`error.css` had not applied yet, or the emulated touch pointer was not yet
reported to the page. The check measures straight after
`page.goto(..., wait_until="load")`, with nothing waiting for either.

Not caused by the commit under test: that commit (reconcile Task 7) did not
touch `error.css`, `templates/error.html` or the gate's layout checks.

Status: open (P2). Non-blocking, by owner ruling 2026-09-23. Until it is
fixed, a frontend-gate failure that the implementer's runs did not show is
re-run once before anyone acts on it. The fix should make the check wait for
the state it measures, not add a retry. Source: the gate-runner's run for
Batch 23 WP-0 reconcile Task 7 (2026-09-23). Its logs are in a git-ignored
SDD workspace on the owner's machine; the failure lines above are quoted
from them.

### F-B21-61: the architecture diagrams are claims about the code that nothing checks

`docs/architecture/` holds five mermaid diagrams, one each in
`docs/architecture/runtime-system.md`,
`docs/architecture/development-cycle.md`,
`docs/architecture/documentation-tooling.md`,
`docs/architecture/top-albums-sequence.md` and
`docs/architecture/heatmap-sequence.md`. Their nodes name real modules and
functions -- `orchestrator.py`, `create_job()`, `cleanup_expired_jobs()` -- so
each diagram states facts about the code. Nothing verifies them: no pre-commit
hook, no CI step, no test. Every symbol resolves today, verified 2026-09-13, so
this is drift prevention rather than a repair.

Every other repeated fact in this repository has a control plane: docsync
carries a generic mechanism plus `.docsync.toml` declarations plus a gate, and
the worktree guard reads PLAYBOOK Section 3. A diagram node is the same kind of
claim as a `[[anchor]]`, and it is the only one with no owner.

Fix shape (owner ruling, 2026-09-13): extend docsync rather than add a tool.
- Mechanism: `scripts/docsync/diagrams.py` finds fenced mermaid blocks, reads
  their labels, and resolves any label naming a code symbol against the tree.
  It holds no repository-specific value, so it lifts with the rest of the
  package.
- Declarations: a `[[diagram]]` kind in `.docsync.toml` naming each diagram's
  claimed symbols and the labels that are prose, not code ("Last.fm API"). The
  prose exemption is a local convention, like `strikethrough_exempt`.
- Gate: the existing `doc-state-sync-check` hook, reporting a new `DOC013`
  with a path, a line and a remedy. Record the code in
  `docs/architecture/documentation-tooling.md` beside `DOC001`-`DOC012`.
- Standard library only: `re` and `pathlib`. Mermaid syntax validation needs a
  parser, so if it is wanted, add it as a CI-only step using the Node
  toolchain the Tailwind build already requires, never as a pre-commit hook.
- AGENT_NOTES.md "This repository is also a template being extracted" gains a
  line naming diagrams as a third declared surface beside values and anchors.

Note (2026-09-19): DOC013 is taken (docsync finding-lifecycle codes).

Note (2026-09-24): DOC023 is also taken (docsync finding-lifecycle
grandfathered-finding count, `scripts/docsync/findings.py`). A new invariant
for this finding starts at the next free code named in
`docs/architecture/documentation-tooling.md`'s catalogue; DOC021 and DOC022
are reserved by
`docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`.

Status: open (P2). Not scheduled; it belongs with docsync work, not with
Batch 21. Source: architecture review, 2026-09-13.

### F-B21-54: PR 227 still reports test assertions through a separate scanner

The 2026-09-09 PR snapshot contains 268 inline Bandit B101-bearing comments
across seven pytest files. The published `.codacy.yml` excludes `tests/**`
from Codacy, but those B101 comments are from Qlty. The local
`.qlty/qlty.toml` is untracked and names test patterns without a targeted
B101 exclusion. Changing Codacy does not configure the other reviewer.

This is P2 review-tooling debt, not 268 production vulnerabilities. Keep
test assertions and preserve production analysis. A future tooling change
should scope only the noisy rule to test paths and validate the actual
review provider; do not hide whole production modules or suppress other
findings bundled in the same comment. The float and callback-comparison
claims were checked separately in
[PR 227 priority triage](docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md).

Status: open, deferred. No scanner configuration changed in this priority pass.
Source: PR #227 live comments and local scanner configuration, 2026-09-09.


### F-DATA-1: reissue editions collapse onto the original's cache row

`normalize_name()` strips `deluxe`/`edition`/`remastered`/`anniversary`
and seven more words from the album string, so
`"viagr aboys (Deluxe Edition)"` and `"viagr aboys"` both normalize to
`viagr aboys`. The `spotify_cache` primary key is
`artist_norm + album_norm`, so **both editions share one row** holding
whichever release populated it first, for the 30-day TTL. When the
reissue wins that race its `release_date` is served for the original.

Observed 2026-07-31: Viagra Boys "viagr aboys" (2025) appears under
`release_scope: same` for 2026, matching the JP deluxe released
2026-01-09, on an account that never played the deluxe.

The collapse is not a bug on its own -- it is what makes matching work
across Last.fm's inconsistent album strings, where the same record is
scrobbled as `Album`, `Album (Deluxe Edition)`, and `Album - Deluxe`
depending on the reporting client. Keying editions apart would fragment
one album into several leaderboard rows with split playcounts, which is
a worse defect than an occasional wrong year. Collapsing is correct for
*counting* and wrong for *dating*; the two need decoupling, not one
shared key.

Candidate fix (untested): keep the collapse for aggregation, but when
resolving `release_date`, select the **earliest** date among candidate
Spotify matches instead of whichever cached first. The original predates
its reissues by construction, and this approximates the "Original
Release Date" that Deezer's API team confirmed is a separate field from
the digital release date labels supply. No schema change required.

Rejected: a boolean `is_deluxe` discriminator. The stopword list has 11
entries that combine freely (deluxe, expanded, anniversary, JP deluxe),
so a boolean still collides variant-against-variant. Retaining the
stripped tokens as a variant tag would work but reintroduces the
fragmentation above.

Open questions, answerable by investigation rather than speculation:
1. Do the scrobbles themselves carry the deluxe title? Last.fm stores
   whatever album metadata the player reported, which is a second
   independent path to the same result.
2. Which other albums are affected? **Not answerable from the cache
   alone:** `(artist_norm, album_norm)` is the primary key
   (`init_db.py:42`) and the upsert overwrites the single stored
   `release_date`, so there are no sibling rows and no losing candidate
   dates to compare against. Detection requires re-running the Spotify
   search for each cached album and flagging rows whose stored date is
   later than the earliest candidate in the fresh result set, or
   cross-checking against an external original-release source
   (MusicBrainz, per the note below).
3. Can both a Latin-script deluxe and a JP deluxe surface at once? Only
   if the JP title carries Japanese characters -- NFKC preserves those,
   so it would not collapse; a Latin-script `(Deluxe Edition)` always
   merges to one row.

Note: Spotify exposes no original-release-date field. `release_date`
belongs to the matched release object, and `release_date_precision`
(`year`/`month`/`day`) only reports granularity. Disambiguation must
come from the search result set, the discarded `(Deluxe Edition)`
suffix, or `total_tracks`. MusicBrainz does carry original release
dates -- a lookup narrowed to that single field, cached, is far smaller
than the full-enrichment attempt abandoned in 2025.

Status: open (P2). Low user impact -- one recalled instance across ~14
years of scrobbles, and `release_scope: all` bypasses date filtering
entirely. Source: session 2026-07-31.

### F-DOCSYNC-2: STATUS block misreports current batch between batches

When a close-out entry (untagged `(Batch N close-out)` suffix) still sits
inside the CURRENT-BATCH markers, `renderer.py:85-86` falls back to
`last_completed + 1` even though the Section 3 parse correctly returns
the between-batches state. Transient: rotation self-corrects it when the
next batch's WP-0 entry lands. Fix candidates: prefer the between-batches
branch whenever the parse returns none, or make close-out tags parseable.
Status: open (P2). Source: PR #162 review round 4.

### F-DOCSYNC-3: close-out entries route to the monolith, not the batch log

Close-out headings use a `(Batch N close-out)` suffix that `ENTRY_BATCH_RE`
does not recognize as batch-tagged, so rotation routes them into the
untagged monolith archive instead of `docs/history/logs/BATCHN_LOG.md`.
Affects only close-outs written with that suffix: BATCH19_LOG.md and
BATCH20_LOG.md lack their close-out entries (both sit in the monolith),
while Batch 18's close-out was tagged `(Batch 18 WP-5)` and routed
correctly. Per-batch history is therefore incomplete for the affected
batches without a monolith grep. Fix belongs in a docsync
WP together with F-DOCSYNC-1/F-DOCSYNC-2 (make close-out tags parseable,
then one-time re-route of the existing close-out entries); hand-retagging
machine-rotated archive content was declined in PR #162 round 3 and again
in PR #163 round 3 on the same point-in-time principle.

**Another instance, found 2026-09-20.** Batch 22's Task 4 entry was headed
`(Batch 22 WP-1, Phase 2 begins)`. `ENTRY_BATCH_RE` requires the closing
parenthesis immediately after the work-package number, so the trailing
clause made the heading unparseable as batch-tagged and rotation sent the
entry to the monolith. Batch 22's own per-batch log will therefore be
missing its Task 4 entry unless the routing is corrected first. The entry
itself stays where the tool put it, per the declines above. What this adds
is that the defect is not limited to the `(Batch N close-out)` suffix: any
extra text inside the parentheses does it, and the tool reports nothing.
Status: open (P2). Source: PR #163 review round 3; second instance
2026-09-20.

### F-B21-57: `check_retired` uses one variable for the declaration index and the line number

`scripts/docsync/declarations.py:743` names the outer loop's target `index`
(`for index, declaration in enumerate(declarations)`), and `:763` rebinds the
same name to a line number inside the scan (`for index, line in enumerate(lines,
start=1)`), so one name carries two meanings in one function.

Measured 2026-09-11: the reuse is latent, not live. `_validate("retired", index,
declaration)` at `:744` runs before the inner loop of its own iteration, and the
`for` statement reassigns `index` at the top of each outer iteration, so the
declaration index is restored before it is read again. Calling `check_retired`
with two declarations -- the first scanning `PLAYBOOK.md` behind an
`allow_after` marker, so its inner loop ran and rebound the name, and the second
carrying an unknown key -- named the fault `retired 1`, the declaration index
rather than a line. Nothing reads `index` after `:765`.

It is filed anyway, because the message is correct only by statement order:
moving `_validate` below the scan, or reading `index` after it, turns a
declaration-shaped diagnostic into a line number, and a reader sent to the wrong
line of a long TOML file is the cost. Renaming the inner target to
`line_number` closes it.

Status: open (P2). No behaviour change; the current message is correct.
Source: Task 7 fix round 1, 2026-09-11, from that task's implementer report.

### F-MAS-5: in-memory JOBS dict limits horizontal scaling

Process-local dict breaks polling under multiple workers/machines;
migration path is Redis or a Postgres-backed job table.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-6: Celery/Redis RQ for task queue

**Owner decision:** out of scope until features complete.
Status: open (P2, owner-gated). Source: MULTI_AGENT_SWEEP.

### F-MAS-7: process-local Spotify token cache

Redundant refreshes under multiple workers; acceptable at current scale.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-8: REQUEST_CACHE growth with always-on machines

Cleanup is opportunistic (at job start); TTL mitigates, does not cap.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-SWE-3: a Spotify server error bypasses the configured retries

`spotify.py:67-68` returns `(None, None, True)` for every non-200, non-429
response, and `is_done=lambda t: t[2]` treats that `True` as terminal. A 500
or 503 therefore ends the attempt loop after one try, while
`SPOTIFY_SEARCH_RETRIES` is set to 3 -- verified by running it. The retries
only ever fire for 429. `fetch_spotify_album_details_batch` has the same
shape at `spotify.py:129-132`.

The consequence is narrow: an album that _is_ on Spotify can be recorded as
unmatched when a second attempt would have found it.

**Rescoped by the owner, 2026-08-20, and the correction is worth keeping.**
The audit first filed this as a user-facing mislabelling -- `spotify.py:75`
returns the same value for a genuine empty result, so
`orchestrator.py:250-262` records the album with the reason
`No Spotify match`, and the report treated that label as wrong. It is not.
Thousands of Last.fm-scrobbled albums genuinely have no Spotify release, so
the label is accurate for the ordinary case and what the user sees is
correct. What survives is the defect above -- configured retries that never
run -- which is a smaller thing than the audit claimed. Severity drops from
P1 to P2 and the finding moved from the P1 section to this one.

The related UI need -- the unmatched modal and page should say plainly that
an album had no Spotify match -- is already Batch 21 WP-7 scope
(the `WP-7 -- Unmatched page + reason_code` section of
`docs/history/definitions/BATCH21_DEFINITION.md`: the `no_spotify_match` reason code and the reason
panels with human copy). It is not extra work and is not tracked here.
Status: open (P2). Source: SWE_PRINCIPLES_AUDIT, rescoped by owner review.

### F-SWE-7: utils.py holds five unrelated concerns

One 346-line module carries API rate limiting (`utils.py:29-121`), aiohttp
session construction (`:155-188`), an in-memory response cache
(`:192-242`), duration formatting for display (`:245-283`) and a generic
async retry loop (`:286-346`). Nothing binds them together except the file
name, and `utils` is the name that accretes.

Each function is individually clean, which is why SRP grades B while SoC
grades C. The cost is discoverability: the response cache that F-MAS-8
tracks lives in the same file as `format_seconds`, and a reader looking for
either has no reason to look here.

A split into rate limiting, HTTP and caching, and formatting is a sibling
of the F-B20-2 orchestrator decomposition, archived on 2026-09-21. It is a
structural change with its own parity-test cost, so it wants a work
package of its own rather than a side task.
Status: open (P2). Source: SWE_PRINCIPLES_AUDIT.

### F-B21-48: Last.fm history is re-fetched because only page responses are cached

Every album and Heatmap job calls `user.getrecenttracks` for its requested
range. `scrobblescope.utils.REQUEST_CACHE` retains an exact URL-and-parameter
page response for one hour, in process memory only. A restart clears it, and
different `from`/`to` ranges cannot reuse their overlapping listening history.
PostgreSQL stores Spotify album metadata but no Last.fm scrobble events.

A persistent cache should store normalized scrobble events by user and played
timestamp, with explicit coverage ranges and a short refresh window for recent
history. That model lets album-year and rolling Heatmap requests reuse overlap
without treating Last.fm page numbers as stable storage. Its definition must
also set retention and invalidation behavior for edited or deleted scrobbles.
Keep this out of F-B21-47: it changes shared pipeline data and needs its own
schema, completeness rules, and parity tests.

- [ ] **Status:** open (P2), re-graded 2026-09-23 by owner ruling: a persistent scrobble cache is a feature, not a defect

Source: owner pipeline-performance observation and source cache audit,
2026-09-06.

### F-B18-11: heatmap Last.fm page fetch is rate-limit bound

Fetch time is bound by page count and the shared 10 req/s throttle
(2026-05-16: 103 pages, 10.9s vs a 10.3s floor; fetching is already
concurrent at `limit=200`). Options: heatmap-specific caching,
progressive rendering, or a higher rate limit (not recommended).

- [ ] **Status:** open (P2), re-graded 2026-09-23 by owner ruling: a persistent scrobble cache is a feature, not a defect; its only unrejected remedy is F-B21-48

Source: Batch 18 audit + perf session 2026-05-16.

### F-B21-63: Codex and Copilot have no equivalent of the session-start hook

`AGENTS.md`'s "Session Bootstrap" is enforced for Claude Code sessions by a
`SessionStart` hook that injects branch, working-tree state, guard codes and
the machine-managed status block into every new session. Codex and Copilot
have no comparable entry point: for them, the top of `AGENTS.md` is the only
forcing function there is, and a session that does not open the file never
learns the rule that says to open it.

- [ ] **Status:** open (P2)

Source: F-B21-25, re-graded by owner ruling 2026-09-23.

---

## Info -- Design decisions (no action needed)

### F-LOAD-3: in-memory REQUEST_CACHE is intentional

Avoids re-fetching Last.fm on re-searches; clears on machine sleep.
Status: standing design decision. Source: load testing 2026-03-04.

### F-LOAD-4: Spotify cache TTL is ToS-compliant

Hits do NOT refresh `updated_at`; 30-day expiry from last API call.
Status: standing design decision. Source: cache verification 2026-03-04.

### F-LOAD-5: pre-slicing reduces Spotify API load

Playcount filter + 500-album playtime cap applied before cache lookup.
Status: standing design decision. Source: load testing 2026-03-04.

### F-DOCSYNC-14: DOC023 fires on prose that quotes the outcome vocabulary

`_claims_a_terminal_outcome` (`scripts/docsync/findings.py:371`) suppresses a
claim when a `not` directly qualifies the outcome word, including the
tab-separated and uppercase spellings and the Markdown-emphasised form. Two
classes of prose therefore still block, and both are deliberate.

First, a `not` earlier in the sentence does not suppress a later claim. The
negation rule is anchored to the outcome word, so prose that says it does not
know something and then states an outcome still reads as a claim. That is
asserted by `test_negation_does_not_reach_across_a_sentence`.

Second, a compound that takes the vocabulary's `no` branch and appends a
trailing qualifier carries no `not` for the rule to find, so it blocks as
well.

There is a practical consequence worth recording, because it was learned the
hard way: this file cannot quote a sentence that trips the gate. The first two
drafts of this very entry quoted the trigger sentences in order to explain
them, and DOC023 blocked both -- the first on a `no`-branch compound, the
second on the sentence the boundary rule above describes. The quoted sentences
and the 14-case measurement live in
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`, which sits
outside DOC023's scan. This file does not, so it describes the shapes instead
of spelling them.

Measured 2026-09-20 against 14 synthetic findings run through the real gate,
`collect_rot_issues` (probe: `tmp/_zG_doc023_verdict.py`). Every negation
spelling the rule was written for is handled, and the boundary case above
still blocks, as documented. `tests/test_docsync_findings.py` already covers
the intended behaviour --
`test_a_finding_saying_it_is_not_resolved_is_not_a_claim`,
`test_negation_does_not_reach_across_a_sentence`,
`test_a_deployed_resolution_still_reads_as_a_claim`.

Recorded so a later agent does not "fix" either boundary by widening the
negation window. That trade buys silence on a couple of phrases and pays for
it by missing real completion claims, which is the failure DOC023 exists to
prevent. Blocking is the safe direction -- Rule 7's "a wrong green is worse
than a red" -- and the cost is one reword by an author whose open finding
happens to use the phrase.

Status: standing design decision. Source: PR #234 advisory verification,
2026-09-20.

---

## Deferred / future-batch candidates (Batch 18/19 audits)

One-line cross-references; detailed bodies live in pre-Batch-20
`FINDINGS.md` (git history before `494f2c7`) or the `docs/history/`
audits; 2026-03-04 load-test data is in the findings archive.

- F-B18-1: orchestrator monolith -- promoted to F-B20-2, resolved 2026-09-21.
- F-B18-2: JOBS dict lacks TypedDict/dataclass annotations.
- F-B18-3: `loading.js` album messaging; extract shared polling utility
  if a third feature emerges.
- F-B18-4: `_check_user_exists` creates a throwaway event loop per call.
- F-B18-5: inline SVG payload growth; lazy-load or sprite if more added.
- F-B18-7: duplicated win32 event-loop guard -- absorbed into F-B20-2,
  resolved 2026-09-21 as `worker.new_thread_event_loop`.
- F-B18-10: heatmap + album jobs share the 10 req/s throttle (by design).
- F-B18-12: mode pills differ in width (no `min-width` on `.mode-pill`)
  -- RESOLVED 2026-08-25 by Batch 21 WP-3. They are equal-width `<button>`
  elements in a two-column grid, which also closes the `span[role="button"]`
  item in F-B21-5.
- F-B19-3: last.timer aggregate endpoints are not a drop-in heatmap
  speedup; future perf experiments listed in the archive.
- F-B19-4: front-end UI audit notes -- basis of `docs/history/definitions/BATCH21_DEFINITION.md`.
- F-MAS-2: no automated JS tests -- absorbed into F-B21-18.

---

## Feature preparation notes

### F-FEATURE-1: top songs feature

Rank most-played tracks for a year (separate task type + loading/results
flow). Status: deferred; on the README roadmap. Source: owner roadmap.

- F-FEATURE-2: listening heatmap -- shipped in Batches 18/19, archived;
  perf follow-ups continue as F-B18-11.

---

## Source documents

- `docs/history/reports/DOCSYNC_AUDIT_2026-02-25.md` -- 11 findings, detailed code refs
- `docs/history/reports/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md` -- Full architecture sweep
- `docs/history/reports/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` -- Earlier audit
- `docs/history/reports/AUDIT_2026-01-10.md` -- Rate limit regression audit
- `docs/history/findings/FINDINGS_ARCHIVE.md` -- Rotated resolved/no-action items
- Agent memory: load-test-findings.md (not a repository file) -- raw load
  test data and analysis
