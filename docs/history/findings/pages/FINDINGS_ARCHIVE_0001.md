<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0001

### F-B21-40: Task 3's divider-contrast fix did not cover the index page's own well divider

Task 3 raised `--shell-border` to clear 3:1, but `.index-form`'s
`border-left` draws from the separate, still-opaque `--ss-border-default`
token, which measures roughly 1.12:1 (light) and 1.18:1 (dark) against its
adjoining surfaces -- worse than the 1.27:1 that originally opened
F-B21-24. `check_divider_contrast` (`frontend_gate.py`) read only
`--shell-border`, so the gate stayed green while this divider stayed
unreadable.

Status: resolved in this fix. Added a dedicated `--ss-border-divider` token
(`#858179` light, `#6e6a75` dark) applied only to `.index-form`'s
`border-left`; `--ss-border-default` is untouched everywhere else in
index.css. Measured against both adjoining surfaces in both themes: light
vs page 3.65:1, vs sunken well 3.26:1 (binding); dark vs page 3.69:1, vs
sunken well 3.37:1 (binding). `check_divider_contrast` now also reads
`.index-form`'s rendered `border-left-color` in both engines.
Source: Task 3 specification and standards review.

### F-B21-37: PR #223 understates its refactor scope and omits its execution log

PR #223 describes a loading.js-only refactor, but head a38044b also changes
index filter labels and the shared Python retry helper without a PLAYBOOK entry.

Status: Resolved -- PR #223 merged as 123b127 with corrected scope, a side-task
log, and documented helpers. Validation passed 872 tests and the complete
22-check, 31-run frontend gate in Chromium and Firefox. This was a review and
documentation defect; the inspected diff did not establish a functional
regression. GitHub closed issue #222 on merge despite the partial-scope body;
it was reopened because the remaining complexity targets are not addressed.
Source: Owner-requested PR #223 merge-readiness review, 2026-09-04.

### F-B21-34: one captured snapshot kit URL lacked an explicit expectation

The reference design README's URL capture still participated in live-kit
comparison although its prose capture was pinned as historical evidence.

Added the same snapshot expectation to that URL site. This completes the
capture isolation without changing the Adobe kit, its fonts, or provider.

Status: resolved, 2026-09-04.
Source: late PR #221 review thread 3938613706; owner provider clarification.

### F-B21-38: Task 2's fixed gutters and collapsed height could not protect its boundary states

The proposed minimum alone could not fit the longest headline at 1200px, and
the 673px natural-height guard described the collapsed form rather than the
required decade-plus-open-threshold state.

With fixed hero gutters, both engines measured a one-line album headline at
0.63 and wrapping at 0.64, but the width term already selected 0.671875, so a
lower clamp minimum could not change the rendered result. Scaling the hero
gutters with the composition supports both mode headlines at 0.70; 0.71 wraps
the album headline. This is the largest passing tested hundredth, measured
2026-09-04 in Chromium and Firefox with Adobe Fonts loaded. Readability stays
bounded at 12px; coarse-pointer targets and inputs keep their 44px and 16px
lower bounds. Proportional relationships remain required from 1920px upward.

The 2026-09-05 state sweep measured natural form heights of 673.3px collapsed,
776.8px with decades, 812.3px with thresholds, and 915.8px with both. At the
0.70 lower bound, the fully expanded form measures 769.4px because readable
text wraps in the narrower card. The guard must account for reachable state,
header and gutter space, and the lower bounds; multiplying the available
height by the base factor would overrun it again.

Status: resolved, 2026-09-05. The complete two-engine frontend gate passed in
isolation (22 checks, 62 runs, Chromium and Firefox) after the state-sensitive
height bounds landed. An earlier isolated run failed once in Chromium's
pipeline state-machine check (30s timeout waiting for the heatmap hand-off)
and once in Firefox with NS_ERROR_SOCKET_ADDRESS_IN_USE while unrelated
browser work ran concurrently; neither reproduced in the clean isolated run,
and both are attributed to environment contention, not the scale mechanism.
Source: Task 2 implementation measurements, 2026-09-04 and 2026-09-05.

### F-B21-39: Task 2 review found base-geometry drift and an untested gate helper

The explicit-dimension sweep changed three authored `0.25rem` gaps to
`0.375rem` and removed the mode tabs' `9rem` minimum. Because the scale token
falls back to one outside wide desktop, those edits changed the mobile and
unscaled composition rather than only scaling its existing geometry. The new
desktop-boundary helper also had no adversarial unit test, and current-state
documents retained contradictory pre-implementation wording.

The review remediation restores the original gap and minimum-width bases while
applying the layout factor, adds a wrapped-headline failure-path test for the
helper, and reconciles the live Task 2 and two-engine statements. Qlty's three
production-code comments are addressed in the same pass. Its Bandit B101
reports target pytest assertions and do not describe production code.

Status: resolved, 2026-09-05.
Source: Task 2 specification and standards review; PR #224 Qlty and Graphify
review comments.

### F-B21-35: the proposed scale height guard ignored root-font enlargement

Task 2's fixed 673px natural-height denominator would not follow its rem-sized
content when the reader enlarged the root font.

The production replacement expresses the measured denominator as 42.0625rem.
The complete Chromium and Firefox gate validates a 20px root and restores page
state after the check.

Status: resolved in Task 2, 2026-09-05.
Source: late PR #221 review thread 3938613711; Task 2 implementation.

### F-B21-31: the remediation plan conflicted on counts and omitted a phase-copy reader

Task 4 prescribed counted phase labels while the batch still prescribed
operation-only copy, and its proposed mutable phase dictionary would leave `get_job_context`
returning that nested object by reference.

The owner reaffirmed visible counts on 2026-09-04, conditional on accurate
polling, as the September 1 owner-remediation plan intended. The batch decision
now records that override. The plan requires mutation-isolation assertions for
both repository readers and the F-B21-33 accuracy prerequisites. This corrects
the execution contract; the phase feature has not been implemented. The gaps
predate the latest review fix, rather than being production regressions from it.

Status: resolved in the plan, 2026-09-04; implementation remains Task 4.
Source: PR #221 review threads 3938450404 and 3938450413.

### F-B21-32: repository-authored PR documentation violated the ASCII rule

The batch definition and reconciliation used a multiplication sign, and the
published Graphify report used non-ASCII punctuation on 89 lines.

Normalized those repository-authored files to ASCII without touching any of
the 61 guarded design imports or the preserved Graphify data. The generated
report introduced most violations; the branch-wide scan covers sibling claims.

Status: resolved, 2026-09-04.
Source: PR #221 review thread 3938450418.

### F-WORKTREE-5: display-unsafe branch candidates were dropped before the conflict check

`parse_batch_branch` filtered candidates through `is_display_safe_ref` and only
then counted them, so a Section 3 naming both `wip/batch-21` and a second,
Git-valid branch holding a non-ASCII letter resolved to the ASCII one instead
of failing closed on conflicting metadata. The guard then reported an aligned
checkout even though the document declared two different branches.

The ordering was deliberate in the PR #170 round-2 remediation, on the
reasoning that a candidate failing the predicate "can name no real branch".
That reasoning did not hold: `is_display_safe_ref` is deliberately narrower
than Git's ref rule, so a rejected candidate can still name a real branch.
What the predicate decides is whether a value may be *rendered*, not whether it
may *exist*.

Fixed by counting distinct candidates before any filtering and raising the
existing `GuardError` on a conflict; the display-safety filter now runs
afterwards, only to decide what may be rendered. Both orderings are covered:
removing the count-before-filter fails
`test_a_display_unsafe_branch_still_counts_as_conflicting_metadata`, and
removing the display-safety filter fails three forgery cases in
`test_a_branch_value_cannot_repaint_the_diagnostic_line`. The superseded
prescription in `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`
carries a correction note so the plan cannot teach the defect again.
Status: resolved 2026-08-14. Source: PR #170 review round 5 (Codex), reported
independently by Copilot in round 6.

### F-WORKTREE-1: Rebase merges leave linked branches history-diverged

GitHub rebase merges rewrite commit identities on `main` without moving the
linked worktree branch, producing a branch that is both ahead and behind even
when its tree is identical; after PRs #163, #165, and #168 this repeatedly
created a risk of phantom PRs, duplicate work, or an incorrect merge.
Status: resolved 2026-08-05. Evidence: the read-only CLI distinguishes
behind-only, identical-tree rebase artifacts, and true divergence; the
canonical bootstrap stops on its errors; and live linked-worktree inspection
reported the expected branch and ancestry without modifying Git. Review
remediation adds final WT013 context to every offline result and keeps
custom-base guidance aligned with the caller-selected ref. Final review
remediation preserves the public facade; WT014 fails closed without traceback or
sensitive runner text, and exact severity plus real CLI tests protect every WT
code. Shared fixtures create host-appropriate tools; host-rendered missing-tool
assertions and simulated POSIX inspection protect the Ubuntu CI boundary.
Source: post-merge lineage investigations for PRs #163, #165, and #168.

### F-WORKTREE-2: Linked worktrees cannot use the relative virtualenv path

The sole `.venv` is gitignored under the primary checkout, so a fresh shell in
a linked worktree cannot run the documented relative activation or test
commands; an uninformed agent may create a forbidden second environment or
fall back to bare pip and reproduce dependency drift.
Status: resolved 2026-08-05. Evidence: the live linked-worktree guard reported
Python, pytest, and pre-commit under the primary checkout's existing `.venv`,
and AGENTS now forbids a second environment and requires those qualified paths.
Source: repository-integrity design validation on 2026-08-05.

### F-DOCSYNC-5: Operational doc metadata drifted across path and branch changes

The live archive prologue and active-definition branch metadata drifted while
`doc_state_sync.py --check` and CI remained green because prefixes were opaque,
live-document references were only narrowly checked, and integrity warnings
did not affect the exit code.
Status: resolved 2026-08-05. Evidence: final-state CLI enforcement rejects
conflicting test fields, dead optional-session references, non-unique tracked
root definitions, and sanitized Git discovery failures; `pytest -q` measured
**521 passed** with 3 existing warnings on the final combined remediation.
Approved design:
`docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
Source: PR #168 pre-merge audit and follow-up root-cause investigation.

### F-DOCSYNC-8: TOML array-of-tables scoping detached declaration sites into adjacent values

In `.docsync.toml`, an intervening `[[value]]` table (`the wide-desktop scale cap`)
inserted on 2026-08-28 after the 5th site of `the single 860px breakpoint`
caused TOML's table-scoping rules to attach the remaining 9 breakpoint sites
to the scale cap declaration instead of the breakpoint declaration. Because the
scale cap lacked an `expect` assertion and those 9 sites did not match the
scale cap's pattern, they silently went unvalidated for 9 days.

Fixed by grouping all 14 breakpoint sites contiguously (including missing frontend
files `loading.css`, `empty.css`, and `theme.js`), adding an explicit
`expect` value to every site (`"860"` or `"859.98"`), separating the wide-desktop
scale baseline and cap declarations, and adding a file-level architectural warning
comment in `.docsync.toml` documenting TOML array-of-tables scoping hazards.
Status: resolved 2026-09-06. Evidence: all 14 breakpoint sites validate under
`the single 860px breakpoint` declaration and `pytest -q` is green.
Source: docsync tooling audit, 2026-09-06.

---

### F-DOCSYNC-9: Mixed expect values in value declarations bypassed consistency checks

In `scripts/docsync/declarations.py:check_values`, sites that declared an `expect`
parameter executed `continue` without appending their values to `captured`. When
a declaration had some sites declaring `expect` and other sites omitting `expect`,
the unannotated sites were cross-checked only against each other, completely
ignoring disagreements with the expected value sites.

Fixed by determining whether all `expect` annotations in a declaration share a
uniform value, and if so, registering `(rel_path, expect)` in `captured` so that
any unannotated site that deviates from the uniform expectation triggers a DOC009
mismatch. Covered by unit tests `test_a_captured_site_that_disagrees_with_a_uniform_expected_site_fails`
and `test_a_captured_site_that_agrees_with_a_uniform_expected_site_passes`.
Status: resolved 2026-09-06. Evidence: 2 new unit tests in `tests/test_docsync_declarations.py`
and all 73 declaration tests pass.
Source: docsync tooling audit, 2026-09-06.

---

### F-DOCSYNC-10: Unlabelled next-action claims bypassed Section 3 integrity enforcement

In `scripts/docsync/integrity.py:_check_section3_next_wp`, if Section 3 did not
contain a bullet matching `SECTION_3_NEXT_ACTION_RE` (`- **Next action:** ...`),
`_section3_next_wp_claim()` returned `None`. The check treated this as absence of a
claim and returned `None`, allowing unlabelled claims (e.g. `- Batch 21 WP status: ... WP-5 is next`)
to silently bypass DOC007 next-action validation against Section 4 execution logs
and the active batch definition.

Fixed with a two-fold remediation:
1. Hardened `_check_section3_next_wp` to inspect Section 3 for unlabelled `NEXT_WP_CLAIM_RE`
   matches when `claimed is None`, raising a blocking DOC007 error requiring the
   `- **Next action:**` bullet label. Covered by `test_doc007_section3_unlabelled_claim_blocks`.
2. Restored the canonical `- **Next action:**` bullet label in `PLAYBOOK.md` Section 3.
Status: resolved 2026-09-06. Evidence: `doc_state_sync.py --check` flagged the unlabelled
claim on `PLAYBOOK.md:167` before remediation and passes cleanly after the label was restored.
Source: docsync tooling audit, 2026-09-06.

---

### F-DOCSYNC-4: per-batch logs were undiscoverable; tombstones retained

Until 2026-07-31 the 18 `docs/history/logs/BATCHN_LOG.md` files were
referenced by no working doc (PLAYBOOK Section 2 had no Log column), so
batch history was reachable only via a directory glob. Fixed: Section 2
gained a Log column and the AGENTS.md close-out procedure fills it per
batch. Related disposition: the two ~300-byte
`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
`docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` are deliberate Batch 14
"Moved:" tombstones kept
for backward references -- not cruft, do not delete.
Status: resolved 2026-07-31; rotates to the archive at Batch 21
close-out. Source: PR #163 doc-hygiene pass.

### F-SWE-1: SWE-principles audit -- executed 2026-08-20

No differential check of the ten mandated software principles
(AGENT_NOTES.md Owner Preferences) had run since the 2026-02 audits.
`docs/SWE_AUDIT_CHARTER.md` chartered one on 2026-07-31 and was amended
2026-08-19, after a preflight review found it could not work as the gate its
position implies. The amendment named the 13 graded modules explicitly (130
cells), excluded `scripts/docsync/` and `scripts/dev/` with stated reasons,
defined the A/B/C/D rubric and the Boy Scout history window, read the whole
finding corpus including the archive instead of a closed ID list, required a
provenance block naming the audited SHA, and stated which findings block
Batch 21 WP-1. The permission to cut modules to fit the budget was withdrawn.

Executed 2026-08-20 against `1994673`, whose runtime code is identical to
`bb187ae`. All 130 cells filled in one session: 74 A, 28 B, 8 C, 2 D,
18 N/A. Six net-new findings, F-SWE-2 to F-SWE-7. The weakest principle is
Fail Fast, holding five of the eight C grades. Mutation testing deleted all
81 top-level functions in the graded modules one at a time and the suite
caught every one, so there is no net-new test-vacuity finding. The audit
returned **migration blocked by F-SWE-2** under charter Section 6, which is
an owner decision: fix the two lines, or waive.

The charter was retired in the same commit, per its own output contract.
Status: resolved 2026-08-20; rotates to the archive at Batch 21 close-out.
Report at `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`.
Source: owner request 2026-07-31.

### F-SWE-2: the album year window is built from naive datetimes

`fetch_top_albums_async` (`orchestrator.py` at the time, now
`scrobblescope/orchestrator/__init__.py`) built the Last.fm fetch window with
naive datetimes, so `.timestamp()` applied the host's local zone. The same shifted timestamps
were reused to filter individual scrobbles. On a UTC-5 host, each boundary
moved five hours into the requested year.

This was the twin of F-B19-6 in `heatmap.py`. The standalone pre-WP-1 fix
adds explicit UTC to both constructors. A deterministic regression drives
`fetch_top_albums_async` through a simulated UTC-5 time boundary and asserts
the literal UTC epochs passed to Last.fm; it failed against the naive window
before passing against the corrected one.

Status: resolved 2026-08-20; rotates to the archive at Batch 21 close-out.
Source: SWE_PRINCIPLES_AUDIT.

---

---

## Rotated 2026-07-24 (PR #162 review follow-up)

### F-FEATURE-2: listening heatmap feature -- RESOLVED (shipped in Batches 18/19)

Last.fm-only scrobble density calendar for the last 365 days, no Spotify
calls. Batch 18 delivered the end-to-end feature; Batch 19 polished the
result frame, KPIs, pill labels, pinwheel animation, and mobile layout.
Rotated per the finding-writing rules since the feature shipped;
performance follow-ups continue as F-B18-11 in the active file.

## Rotated 2026-07-24 (Batch 20 WP-7)

### F-B19-6: naive-tz day-attribution bug -- RESOLVED

This finding closed in two portions that were rotated separately, leaving two
headings under one ID. They were merged here on 2026-09-19 because an F-ID is
a permanent cross-reference key and must resolve to exactly one record; DOC018
reports the split. Both bodies are preserved verbatim below, and the finding
is filed at the rotation that closed it.

**Code fix, rotated with Batch 20 WP-6.** PR #152 review (Gemini) surfaced
that `scrobblescope/heatmap.py` decoded Last.fm UTS values with naive
`datetime.fromtimestamp` and built the fetch window with naive
`datetime.now()`. On Fly.io (UTC container) this was silently fine; on local
Windows dev or any non-UTC host it shifted day attribution by hours. Code
fixed in PR #152 (commit `ccb000f`) with
`tests/test_heatmap.py::TestAggregateDailyCounts::
test_utc_decode_invariant_against_local_tz_drift` as the canonical
regression test.

**Follow-up, rotated with Batch 20 WP-7.** The remaining open portion was
closed in Batch 20 WP-7: the naive-tz vacuous-datetime-test anti-pattern is
now item 6 in the AGENTS.md Anti-Pattern Registry, citing that same
regression test as its canonical example.

## Rotated 2026-07-24 (Batch 20 WP-6)

### F-B20-1: README/SESSION_CONTEXT test-file count drift -- RESOLVED

`README.md` and `.claude/SESSION_CONTEXT.md` claimed "24 test files" while
the tree held 22 pytest modules. Corrected in Batch 20 WP-1 (README) and
via the machine-managed SESSION_CONTEXT refresh; the stale "389 tests,
24 test files" line in the FINDINGS header was the last occurrence, fixed
in WP-6. Recorded for audit completeness and archived immediately.

### Resolved since last update (2026-03-02)

Items from prior audits that have been addressed:

- ~~MEMORY.md stale~~ -- Deleted. Replaced by `AGENT_NOTES.md` (tracked) in Batch 17 WP-4.
- ~~README.md screenshot placeholders~~ -- Owner replaced with "coming soon".
- ~~CI Python version drift~~ -- Aligned to 3.13 in Batch 15.
- ~~docsync cli.py unconditional rewrite~~ -- Gated on changed set (Batch 14).
- ~~Test-count regex defined 3 times~~ -- Consolidated to single `TEST_COUNT_RE`
  in `parser.py`; renderer and logic import it (Batch 14).
- ~~Dedup-sort pattern copy-pasted~~ -- Extracted `_dedup_sorted()` helper in
  `logic.py` (Batch 14).
- ~~Gunicorn HTTP serialization~~ -- Added `--threads 4` to Dockerfile CMD.
  Merged to `main` as `f8a579f` (#57). Deployed and verified.
- ~~Dark mode ignores browser preference~~ -- `theme.js` falls back to
  `matchMedia('prefers-color-scheme: dark')`. Commit `463282e`.
- ~~Log rotation loses data under load~~ -- Increased to 2MB cap, 10 backups.
  Commit `21a3b4c` on `main`.

### F-B18-6: dark mode uses body.dark-mode class, not data attributes -- RESOLVED

CSS uses `.dark-mode` class toggled by `theme.js`. Original Batch 18
definition referenced `[data-theme="dark"]` which does not exist. Corrected
in the audited definition; informational only since then.

### F-B18-8: get_job_context shallow-copies results but not nested dicts -- RESOLVED

**Status:** resolved during PR #152 review (Gemini Code Review catch).
`get_job_context()` now explicitly does `results["daily_counts"] =
dict(results["daily_counts"])` after the outer dict copy, restoring the
function's stated contract for heatmap result shape. Variant chosen over
`copy.deepcopy` because the polling hot path runs every ~1s per active
job and the nested structure is well known. New regression test:
`tests/test_repositories.py::test_get_job_context_nested_daily_counts_is_isolated`.

Historical context: `repositories.py` `get_job_context()` originally
copied list results via `list(results)` but did not copy dict results at
all (returned the original reference). A Boy Scout fix added an
`elif isinstance(results, dict): results = dict(results)` branch, but
that was still a shallow copy, leaving the nested `daily_counts` shared
by reference. PR #152 review surfaced this; the fix above closes it.

### F-B18-9: username not sanitized for JS/SVG injection -- RESOLVED

Routes validate that a username exists on Last.fm but do no input
sanitization beyond that; usernames are echoed back in JSON and rendered
client-side. Addressed during Batch 18: `heatmap.js` renders all
user-supplied strings via `textContent` (never `innerHTML`), with the
criterion cited at the top of the file ("No innerHTML with user data
(XSS criterion F-B18-9)"). Verified still true 2026-07-24.

### F-B19-1: loading state still read as a card -- RESOLVED

Owner review showed the pinwheel centered inside a large Bootstrap card-like
box. That made the loading state feel broken even after the earlier clipping
fix. The follow-up removed the card wrapper and uses an unframed loading panel
with a larger SVG-bounded pinwheel. The final SVG keeps the original
breathing/expanding blade animation; the simplified rotating replacement was
rejected during owner review. Fixed in Batch 19 owner-review follow-up.

### F-B19-2: heatmap sizing needed separate desktop and mobile treatment -- RESOLVED

Desktop screenshots at 1440p and 1080p showed the heatmap grid taking too
little visual space because the result container was still constrained by the
Bootstrap `col-md-8` width. Mobile review showed calendar-constrained layouts
either left excessive side space or made cells too small. The follow-up
widened only `#heatmap-result` on desktop and replaced the mobile layout with
a sequential activity strip that fills the frame width with larger cells,
plus mobile headline fitting. Fixed in Batch 19 owner-review follow-up.

### F-B19-5: visual-verification tooling -- NO ACTION

The Browser plugin/skill is the right Codex-side tool when its browser MCP
tools are exposed. In the Batch 19 session, deferred tool discovery did not
expose a callable browser screenshot tool, and shell-launched headless Chrome
did not emit screenshots in the sandbox. For future UI-heavy batches, enable
a Browser/Playwright MCP path if available. No new Python or Node package is
recommended solely for visual QA.

### F-B23-46: the Listening Time toggle's durationless rows -- RESOLVED

A Results page switched to Listening Time in the browser ranks matched albums with no Spotify duration last, shown as a dash, while a run that starts in playtime mode drops them server-side (`_filter_results_for_display`), so the same listener sees two different leaderboards for the "same" ranking. This is pre-existing on `main` for play-count runs (`setLeaderboardMetric` sorts every row), and is now also reached after Hide on an include run. What would close it: one rule for both paths (hide durationless rows while the client metric is playtime, with renumbering, or keep them server-side too), decided in the UI-consistency PR.

- [x] **Status:** resolved
**Completed:** 2026-10-25
Resolved by the owner's 2026-10-25 rule: while the Results page ranks by
listening time, albums with no listening time (none or zero) are dropped
from the ranking with ranks renumbered, and they come back when ranking
by track plays; the same rule runs server-side and client-side. Ruling
RA3: Total Albums, Top artist and Scrobbles keep describing the whole
result, and a note and the toast state how many albums are hidden.
Ruling RA5: a run started in playtime mode renders those albums hidden
(`_mark_untimed_for_display`), so switching to track plays brings them
back. Fixed by T7 `7e529efc` (browser rule), T7b `2115e858` (note and
toast) and T10 `078ef258` (server). Documented in `DESIGN.md`.
Source: Codex review on PR #256 (comment 4330862249), 2026-10-20, controller trace.

### Load test data (2026-03-04, local) -- HISTORICAL RECORD

Test environment: Flask dev server (Werkzeug, threaded), local `ss-postgres`
Docker container, all caches cleared between runs.

| Concurrent Users | Per-user elapsed | Wall time | Upstream 429s | Outcome |
|------------------|------------------|-----------|---------------|---------|
| 1 (cached)       | 21s              | 21s       | 0             | OK      |
| 2 (uncached)     | 88-106s          | 107s      | 0             | All OK  |
| 3 (uncached)     | 125-201s         | 202s      | 0             | All OK  |
| 5 (uncached)     | 115-268s         | 269s      | 0             | All OK  |
| 10 (partial)     | 216-353s         | ~6min     | unknown       | 6/10 OK |

**Caveat:** Local tests use Werkzeug (threaded HTTP). Production was single
sync gunicorn worker (no threads) at time of testing.

**Global throttle:** `_GlobalThrottle` serializes all API calls at 10 req/s
across all job threads. Jobs slow linearly: N jobs sharing 10 req/s =
~10/N req/s per job.

**Last.fm rate config:** App configures 10 req/s; official limit is 5 req/s
averaged over 5 minutes. No 429s observed in testing, but aggressive.
