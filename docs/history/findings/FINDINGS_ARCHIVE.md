# FINDINGS Archive

Resolved and no-action findings rotate here from `FINDINGS.md` at batch
close-out (or during dedicated findings-cleanup WPs) so the active file
stays short while grep history is preserved. Entries keep their original
F-IDs; bodies may be condensed at rotation (full original text remains in
git history and the source audit documents). Nothing here is deleted.
Newest rotation first.

---

## Rotated 2026-09-13 (Batch 21 close-out)

28 findings resolved during Batch 21, the UI overhaul. They are kept whole, with their owner rulings, because several record why a
later change must not undo them.

### F-B21-59: Spotify's February 2026 changelog removes an endpoint the pipeline depends on

`fetch_spotify_album_details_batch` in `scrobblescope/spotify.py` calls Get
Several Albums (`GET /v1/albums?ids=`), and `search_for_spotify_album_id`
calls Search. Spotify's February 2026 Web API changelog lists Get Several
Albums as removed and caps Search at 10 results. The changelog also removes
fields: album `label`, `popularity` and `external_ids`. The package reads none
of those fields, and its searches ask for at most 3 results, so only the batch
call is exposed.

A live probe with the app's client credentials on 2026-09-13 returned HTTP 200
for `GET /v1/albums?ids=`, `GET /v1/albums/{id}`, and Search with `limit=20`
(20 items). The app is not broken today.

The cause is known. The owner confirmed on 2026-09-13 that the app is in
Development Mode. Spotify applied the new rules to new Development Mode apps on
2026-02-11. Existing ones got the Premium requirement, the five-user cap and
the one-Client-ID limit on 2026-03-09, but the endpoint removals were
postponed with no new date
(https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security).
The exemption can therefore end at any time, with notice only on Spotify's
developer blog. When it ends, every album search loses its release dates, and
every album lands in the unmatched report.

Two actions keep the exemption and must be avoided: creating a new Spotify app
or Client ID, which gets the new rules at once, and rotating the secret without
cause.

Fix, **required** (owner ruling, 2026-09-13), implemented the same day.
`fetch_spotify_album_details_batch` in `scrobblescope/spotify.py` treats a
status in `BATCH_ENDPOINT_GONE_STATUSES` (403, 404, 410) as the endpoint being
gone. It then fetches each album through the new
`fetch_spotify_album_details_single` (`GET /v1/albums/{id}`, under the same
Spotify limiter, with 429 retry) and calls `on_fallback(status)`.
- A single album that is unavailable is left out; it does not fail the batch.
- `_run_spotify_batch_detail_phase` in `scrobblescope/orchestrator.py` logs the
  fallback once per job.
- 401 and 5xx do not trigger the fallback: single calls would fail on the same
  token, and an outage is no reason to multiply calls.
- Tests in `tests/services/test_spotify_service.py` and
  `tests/services/test_orchestrator_fetch_spotify.py` pin 403 and 404, a
  single-album 429 retry, a missing album, 500 staying one call, and one log
  line per job. Each failed when its guarded behaviour was mutated.
- A live call confirmed that `GET /v1/albums/{id}` returns the same object
  shape as the batch endpoint.

Batch 22 (enrichment providers) removes the single-provider dependency this
finding describes: Deezer answers when Spotify cannot.

Status: resolved 2026-09-13 (fallback implemented). The exemption itself stays
outside the app's control. Source: Batch 23 planning, 2026-09-13.

### F-B21-58: the unmatched section title says "thresholds", which the copy rules forbid

`scrobblescope/unmatched.py` titles the `below_threshold` panel "Below your
thresholds", and the approved WP-7 extension spec specifies that title
(`docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`,
Presentation section). The design system's copy rules say the opposite:
`docs/design/reference/design-system-readme.md` rules that the play and track
minimums are "what counts as listened" in the UI, **never** "thresholds".

Two approved documents disagree, and the page ships one side. This is a copy
ruling, not a defect an agent can settle by picking the rule it prefers. The
title is also what the reader sees on the one panel they can act on, so the
wording carries more weight here than anywhere else on the page.

Status: resolved 2026-09-13. The owner renamed the panel "Not enough listening"
in `scrobblescope/unmatched.py` `CATEGORY_METADATA`, so the copy rules win and
the spec now states the new title. Source: Batch 21 documentation audit,
2026-09-12.

### F-B21-56: upstream Spotify failure detection was coupled to written prose reason instead of reason_code

`_detect_spotify_total_failure` in `scrobblescope/orchestrator.py` checked the
English string `"No Spotify match"` instead of the domain contract
`reason_code` (`REASON_NO_SPOTIFY_MATCH`). When the first WP-7 commit
`b3e3e96` introduced `reason_code` to the contract, this detector was missed.
If the prose string varied or changed, Spotify total failure detection would
not fire, preventing the classified `spotify_unavailable` error from being set.

Status: resolved locally in the Batch 21 WP-7 deviation, pending commit;
`_detect_spotify_total_failure` checks
`reason_code == REASON_NO_SPOTIFY_MATCH` with legacy fallback, verified by
mutation testing.
Source: owner review, 2026-09-10.

### F-B21-47: Artist Spotlight rendered one top-album artist and never rotated

The Results side rail described an Artist Spotlight but built no rotation
collection or timer. Both Flask and the metric-toggle client treated the artist
on the highest-ranked single album as the leading artist, so repeated albums by
one artist were not ranked by their aggregate scrobbles. The fallback Spotify
link also labelled an album ID as an artist destination, and its unguarded image
failure handler could apply after a newer portrait request had started.

Status: resolved locally, 2026-09-06. The server aggregates artists by
scrobbles, takes the top ten, and uses the job ID to choose a stable random five
without changing the album or Heatmap pipelines. Results renders the first
fallback immediately, hydrates the five artist records concurrently afterward,
and rotates them every seven seconds. Candidate-slot, active-index, and image
revision checks discard late responses; reduced-motion readers keep one static
spotlight. The browser gate verifies five unique requests and a rendered card
change in Chromium and Firefox.
Source: owner Results review and source/request-flow audit, 2026-09-06.

### F-B21-43: cached Heatmap restoration painted an obsolete loading state

Opening Heatmap from the header after a result was cached called
`fadeIn(heatmapLoading)` before the first progress request. A completed job
therefore painted the loading panel for a fraction of a second, then replaced
it with the cached result. A final DOM assertion could not detect the flash.

Status: resolved, 2026-09-05. Saved-job restoration keeps the loading panel
hidden until the first response proves that work is still running or reports
an error. A ready result fades in directly; a still-running result preserves
the existing Heatmap polling lifecycle and reveals the accurate progress
state. The Chromium and Firefox gate observes loading-panel class mutations
from before production `DOMContentLoaded` listeners run and fails if a cached
result paints that panel.
Source: owner browser review and two-engine rendered state observation,
2026-09-05.

### F-B21-46: the desktop index form stayed top-heavy as the window grew

The fixed index scale correctly grew the form between realistic 1080p and
1440p windows, but the form composition remained anchored to the well's top
padding. At 1920x945, its outer top and bottom space measured 55.9px and
98.2px; at 2560x1305, those values diverged to 74.5px and 193.6px. The 28rem
base cap also left the card slightly wider than the owner's preferred measure.

Status: resolved, 2026-09-05. The owner-refined base cap is `27.5rem`. The
2026-09-09 refinement places the composition up to 2.5rem above centre,
bounded by 0.25rem of header clearance. Expanded content retains natural
scrolling only when it cannot fit. The gate verifies this upward bias
at realistic 1080p, 1440p, and 4K profiles while retaining the
fixed-geometry checks across every reachable form state.
Source: owner 1080p/1440p visual comparison and two-engine rendered
measurements, 2026-09-05.

### F-B21-45: mobile navigation hid report destinations behind scrolling

The mobile header kept all four desktop navigation links in one horizontal
flex row. At 390px its navigation had a 203px visible width but a 345px scroll
width; at 320px only 133px was visible. Results and Unmatched therefore sat
offscreen unless the reader discovered horizontal scrolling.

Status: resolved, 2026-09-05. The first correction put the four destinations
in a two-column, two-row grid beside the compact theme control. Owner review
then found that the control sat across both rows and visually competed with
their buttons. The subsequent owner refinement uses one contained row across
the header width and moves the same Light/Dark input below page content; it
returns to the header at desktop widths without duplicating state. The browser
gate checks both 390px and 320px widths for contained links, no horizontal
overflow, a matching body offset, footer placement, and a retained 44px theme
target. PR #227 review reconciled this description with the current source.
Source: owner mobile review and rendered Chromium/Firefox measurements,
2026-09-05.

### F-B21-44: the desktop Heatmap result retained the prototype's small measure

The result stage remained capped at about 1100px on a realistic 1920x945
content box, occupying only 57.3% of the viewport. Its authored 14px SVG cells
rendered at 16.6px, making the year grid visually slight beside the scaled
index composition. The headline also singled out the username in purple
italics even though it is data rather than an interactive accent.

Status: resolved, 2026-09-05. At widths from 860px, the centred stage now uses
`84vw` with a `120rem` ceiling; the same realistic 1080p content box renders a
1544.8px frame and 23.7px cells. Mobile retains the bounded base measure. The
username inherits the headline's neutral serif colour and normal style. The
two-engine browser gate asserts the frame ratio, centring, rendered cell range,
and headline treatment against a full-year fixture.
Source: owner side-by-side visual review and two-engine rendered measurements,
2026-09-05.

### F-B21-42: index motion used three unrelated timings and blanked mode copy between animations

The index composition entered over 1.2 seconds after a 0.2-second delay,
Heatmap stage changes used 300ms, and `switchModeHero()` ran a sequential
110ms exit followed by a 180ms entrance. Switching modes therefore removed
the current heading before presenting its replacement and made the hero feel
slower than the surrounding page states.

Status: resolved, 2026-09-05. The two mode descriptions now share one grid
track and crossfade concurrently over 180ms, so the taller copy reserves the
same height in both states. Heatmap stage changes retain 180ms; the 2026-09-09
owner refinement gives page navigation a shared 220ms entry and 140ms exit.
The 2026-09-10 delayed-script probe reproduced a first-paint flash in both
engines: DOM readiness restarted already-visible content from zero opacity.
Entry now starts in CSS without waiting for JavaScript; the regression probe
confirms no visible-to-transparent dip.
The reduced-motion media query restores immediate,
fully opaque states.
Source: owner browser review, 2026-09-05.

### F-B21-41: reachable form states rescaled the entire index composition

Task 2's state-sensitive height bounds made the shared `--index-scale`
depend on which form rows were open. At a fixed 1920x945 content box, both
engines measured the 481.6px form shrinking to 390.5px for a decade or custom
release field, 357.8px for open thresholds, and 325.2px when both were open.
Hero padding, wordmark, headline type, card padding, inputs, and mode controls
all changed with it. The gate required the expanded form to avoid document
scrolling, so it enforced the defect.

Status: resolved, 2026-09-05. Reachable states no longer replace the fixed
window's natural-height reference. Additional rows extend the document while
the composition keeps its initial dimensions. The Chromium and Firefox gate
now compares representative dimensions across album, Heatmap, decade,
custom-year, thresholds, and combined states, and requires the combined state
to produce normal document scrolling at the realistic 1080p content box.
`scrollbar-gutter: stable` prevents Firefox from shifting the columns when
that scrollbar first becomes necessary.
Source: owner browser review and two-engine rendered measurements, 2026-09-05.

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

`orchestrator.py:70-71` built the Last.fm fetch window with naive datetimes,
so `.timestamp()` applied the host's local zone. The same shifted timestamps
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

### F-B19-6: register naive-tz anti-pattern in AGENTS.md (follow-up portion) -- RESOLVED

The remaining open portion of F-B19-6 (the code fix was archived in WP-6
below) was closed in Batch 20 WP-7: the naive-tz vacuous-datetime-test
anti-pattern is now item 6 in the AGENTS.md Anti-Pattern Registry, citing
`tests/test_heatmap.py::TestAggregateDailyCounts::
test_utc_decode_invariant_against_local_tz_drift` as the canonical
regression example.

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

### F-B19-6: naive-tz day-attribution bug (code-fix portion) -- RESOLVED

PR #152 review (Gemini) surfaced that `scrobblescope/heatmap.py` decoded
Last.fm UTS values with naive `datetime.fromtimestamp` and built the fetch
window with naive `datetime.now()`. On Fly.io (UTC container) this was
silently fine; on local Windows dev or any non-UTC host it shifted day
attribution by hours. Code fixed in PR #152 (commit `ccb000f`) with
`tests/test_heatmap.py::TestAggregateDailyCounts::
test_utc_decode_invariant_against_local_tz_drift` as the canonical
regression test. The follow-up (register the naive-tz vacuous-test
anti-pattern in AGENTS.md) was closed in Batch 20 WP-7; see the WP-7
rotation block above.
