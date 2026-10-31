<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0021

### 2026-09-23 - Close six stale pending-deploy findings

Side task, no batch tag: close the six finding records that still said "resolved locally, pending
deploy", part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope: the reconcile plan's Stage 1 Task 1.** F-B20-3, F-B21-10, F-B21-26, F-B21-27, F-B21-28 and
  F-B21-29 all said "resolved locally, pending deploy" although their fixes were already on
  `origin/main`. `git fetch origin` ran first, then `git merge-base --is-ancestor` confirmed all seven
  named fix commits (`85e7511`, `079c2b0c`, `b1fdb121`, `ee5ee4eb`, `47321b23`, `df28c06d`, `8b37566a`)
  are ancestors of `origin/main`; none printed STOP, so all six records were written.
- **Plan vs implementation: one deviation, forced by the gate.** The brief's canonical Status line put
  the "fixed by \`<sha>\` ... confirmed an ancestor of \`origin/main\`" text on the checked `**Status:**`
  line itself. `scripts/docsync/findings.py`'s DOC014/DOC015 checks require that line's value to
  normalize to the bare word `resolved` (or `no action`); anything else is rejected, and the word
  "deployed" inside the brief's sentence also trips DOC014's pending-qualifier scan, which is why the
  first `--fix` run failed with six errors naming exactly these findings. Every already-archived finding
  in `docs/history/findings/FINDINGS_ARCHIVE.md` uses the bare form for the same reason. Each of the six
  now reads `- [x] **Status:** resolved` / `**Completed:** <date>`, followed immediately by a new prose
  line carrying the brief's exact sentence (the sha(s), "deployed with it", "confirmed an ancestor of
  \`origin/main\` on 2026-09-23") -- that line sits outside the lifecycle record the gate parses, so its
  wording is unconstrained. The rest of each body (the "Was recorded as" and "Source" lines) was kept
  unchanged, per the brief. F-B21-28 and F-B21-29 each have two fix commits in the brief's table, so
  their new prose line names both ("fixed by \`X\`, completed by \`Y\`, and deployed with it"); the
  completion date used is the later commit's date in both cases, as directed. F-B20-3's new prose line
  uses the brief's supplied reason text (Bootstrap and both CDN providers retired by \`85e7511\`, Batch 21
  WP-8) in place of the generic "fixed by" clause. Completion dates came from
  `git log --ancestry-path --merges --reverse --format=%cs "<sha>..origin/main"`, falling back to the fix
  commit's own date when no merge commit exists on that path: 2026-09-19 (F-B20-3), 2026-09-10 (F-B21-10,
  using `079c2b0c`), 2026-09-10 (F-B21-26 and F-B21-28, using `b1fdb121`), and 2026-09-07 (F-B21-27 and
  F-B21-29, using `ee5ee4eb` and `8b37566a` respectively).
  `doc_state_sync.py --fix` then rotated all six resolved records into
  `docs/history/findings/FINDINGS_ARCHIVE.md`, which emptied the `## P0 -- Fix before next deploy`
  section (F-B21-26, F-B21-27, F-B21-28 and F-B21-29 were its only members); a line was added under
  that heading, rather than deleting it, because other documents cite the severity levels.
  `BATCH23_DEFINITION.md` WP-0 Part B's "Stale finding records" checkbox and the reconcile plan's Task 1
  step boxes are ticked, and Section 3's numbered order list now notes Stage 1 Task 1 landed, keeping
  "WP-0 is next." exactly.
- **No test changed.** The task is documentation only; `git diff --stat tests/` is empty, so the test
  count stays at the baseline.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner tests were excluded, since
they are not repository state.

Forward guidance: the reconcile plan's Stage 1 Task 1 (Part B) has landed; Stage 1 Task 2 (the docsync
work-package gap) is still open. The next steps are the rest of Stage 1, then Stage 2 (Part C, including
Task 11 for F-B22-8), then Stage 3, then the foundation plan's Tasks 4-10, per Section 3's order list.

### 2026-09-23 - The release-window rule gets a leaf home

Side task, no batch tag: move `_matches_release_criteria` into `scrobblescope/domain.py`, part of
Batch 23 WP-0 Part A. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 12** (review A card 3, added to Part A on 2026-09-23). The rule
  had two consumers -- the album filter in `orchestrator/_results.py` and the correction worker's
  `release_checks._matches_window` -- and lived in `orchestrator`, which imports `release_checks` at
  module level, so the worker could only reach the rule through a function-local import. That was the
  one documented exception in the SESSION_CONTEXT Section 4 dependency graph.
- **Plan vs implementation: matched exactly, no deviation.** `domain.py` gained the function verbatim
  (body and docstring unchanged) plus `import logging`, placed after `normalize_track_name`.
  `orchestrator/_results.py` deletes the definition and extends its existing `from scrobblescope.domain
  import normalize_name` line to also import `_matches_release_criteria`, so the facade's re-export
  (`scrobblescope.orchestrator._matches_release_criteria`) and `orchestrator/_results
  ._matches_release_criteria` both still resolve unchanged. `release_checks.py` imports the rule from
  `domain` at module level, next to `normalize_name`, and `_matches_window` lost its function-local
  import and cycle-explaining docstring in favour of one sentence naming the shared home. Both import
  orders (`release_checks` before `orchestrator` and the reverse) were run directly and succeeded, since
  the change is specifically about import order. `.claude/SESSION_CONTEXT.md` Section 4 dropped the
  `; orchestrator (facade, DEFERRED -- see note)` qualifier from the `release_checks.py` line and the
  "The one deferred edge" paragraph; a repo-wide check confirmed nothing else cited it. No new edge was
  added: both consumers already import `domain`. `docs/architecture/runtime-system.md`'s
  correction-worker bullet now says the worker and the album filter both read the rule from
  `domain.py`, instead of describing the function-local import.
  `BATCH23_DEFINITION.md` WP-0 Part A and the foundation plan's Task 12 checkboxes are ticked, and
  Section 3's numbered order list marks this step done, keeping "WP-0 is next." exactly.
- **No test changed.** `git diff --stat tests/` is empty; the task is behaviour-neutral and adds no
  test, so the test count stays at the baseline.
- **Fix round 1 (review finding, Important).** The Mermaid diagram in
  `docs/architecture/runtime-system.md` still drew `ReleaseChecks -.->|imported inside a function|
  Album`, an edge the move made false: `release_checks.py` no longer imports anything from
  `orchestrator` at all. Deleted that one line; `ReleaseChecks --> Domain` already carries the real
  dependency, so nothing replaces it. `Album` stays referenced by several other edges, so no node was
  orphaned. A repo-wide grep for the same edge in any other wording found none. The diagram was
  validated with the Mermaid Chart MCP tool (`valid: true`, `diagramType: flowchart`) after the edit.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner tests were excluded, since
they are not repository state.

Forward guidance: WP-0 Part A's foundation-plan tasks (2 and 12) are both done. The next steps are the
reconcile plan's Stage 1 through Stage 3 (Task 11 included), then the foundation plan's Tasks 4-10, per
Section 3's order list.

### 2026-09-23 - Owner rulings: the release-window leaf and F-B22-8

Side task, no batch tag: records three owner rulings, part of Batch 23 WP-0.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands. No code
changed.

- **Q0 is settled: the Batch 22 MusicBrainz check is done.** The worker logs
  nothing on success, so the logs could not answer it. `original_release_cache`
  could. It held 121 rows, and 60 were written within a minute of each of the
  owner's two runs with Postgres up (06:04 and 16:34 local). Section 3's
  Batch 22 bullet and the definition's Part B box now record both owner items
  as done. The reconcile plan's Task 1 Step 5 is marked as taken over by this
  commit, because Section 3 must stay true at every commit.
- **Review A card 3 joins Part A** as the foundation plan's Task 12. It moves
  `_matches_release_criteria` into `domain.py`, which deletes the one deferred
  edge in the import graph. It is numbered 12, not 2b, because `task-brief`
  would pull a "Task 2b" heading into Task 2's brief. The rest of the
  2026-09-21 review was already dispositioned in the foundation plan's DoD.
- **F-B22-8 is filed and joins Part C at P2.** With the cache DB down,
  `run_release_checks` skips the whole job. The owner ruled that checks run
  regardless, with only persistence skipped. It is P2 because only local
  development reaches the branch: on Fly.io the database wakes with the app.
  The reconcile plan's Task 11 fixes it; one existing test that asserts the
  skip is replaced there, as Part C allows.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The remaining shared extractions

Side task, no batch tag: extract the three remaining shared steps, part of
Batch 23 WP-0 Part A. Untagged by owner ruling 2026-09-23 until the whole
of WP-0 lands.

- **What moved, verbatim (controller ruling R12).** In
  `scrobblescope/orchestrator/__init__.py`: `_cap_threshold_exclusions(threshold_exclusions)`
  is the tie-break-commented cap block from `fetch_top_albums_async`, returning the
  (possibly capped) dict; `total_below_threshold` is still computed from the
  uncapped dict before the call. `_process_filtered_albums(job_id, filtered_albums,
  year, sort_mode, release_scope, decade, release_year, limit_results,
  overall_start_time)` is the tail of `_fetch_and_process`, from the
  `_apply_pre_slice` call through `enqueue_release_check` and `return results`;
  `_fetch_and_process` keeps its outer `try`/`except`, `overall_start_time`, and the
  "Processing your albums..." progress call, and now ends with
  `return await _process_filtered_albums(...)`. In `scrobblescope/heatmap.py`:
  `_zero_fill_daily_counts(counts, from_date, to_date)` is Phase 2 of
  `_aggregate_daily_counts`, which now returns its result.
- Each new function's docstring names the Batch 23 Spotify-export path as its
  second caller.
- No test written or modified: `tests/services/test_orchestrator_fetch_and_process.py`
  and `tests/test_heatmap.py` pass unmodified, and `git diff --stat tests/` was
  empty after each of the three moves.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Session handoff written

Side task, no batch tag: session close for Batch 23 WP-0, by owner request
ahead of a context reset. It adds `docs/history/reports/HANDOFF_2026-09-23.md`
and points Section 3's handoff bullet at it. No code changed, and no task
started.

- **What the handoff records:**
  - the state of WP-0 and the gate results;
  - the four commit ranges of 2026-09-23;
  - the next steps, in the order Section 3 owns;
  - the WP-0-specific rules;
  - the untracked artifacts a cold agent needs: the triage reports, the
    reusable kit for subagent-driven work, and the stale foundation ledger;
  - the traps hit this session.
- **New evidence on Q0.** The owner's second run had Postgres up and still
  logged no MusicBrainz line. That proves nothing: the release-check worker
  logs nothing on a successful run, and the primary checkout sets no
  `MUSICBRAINZ_CONTACT`. The handoff's section 6 says how to settle it.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Owner answers to the reconcile-and-clear plan

Side task, no batch tag: records the owner's answers to Q0-Q16 of
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`,
part of Batch 23 WP-0. No code changed, and no task started: the session
ends here for a context reset, by owner instruction.

- **Every question takes its recommended answer, except three.**
  - **Q0:** no MusicBrainz lines in the log. This is expected, not a result.
    `release_checks._run_release_checks` skips when the cache database is
    down, and Postgres was down on purpose for that run.
    `enqueue_release_check` skips silently when `MUSICBRAINZ_CONTACT` is
    unset. The Batch 22 MusicBrainz check stays owed until a run with
    `ss-postgres` up. The silent skip gets a `logging.info` line in the
    test-infrastructure plan.
  - **Q10 = b:** the UI stays as it is. F-B21-53 becomes no action in Task
    10, and leaves the frontend plan.
  - **Q16 = a:** all the listed rule-outs are approved.
- **What this settles.** Q1 and Q2 confirm Stage 2's Tasks 3-9 as written:
  F-SWE-6 and F-B22-7 join the set.

Next, in order:
1. Part A: the foundation plan's Task 2, by subagent-driven development.
2. This plan's Tasks 1-10.
3. The foundation plan's Tasks 4-10.
4. The three follow-on plans.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Plan of record for reconciling and clearing findings

Side task, no batch tag: planning for Batch 23 WP-0 Parts B and C. It adds
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md` and
points the definition and Section 3 at it. No code changed.

- **Evidence.** Four read-only triage passes checked all 38 IDs in Part C's
  set against `167e650`. Results:
  - six records are already fixed on `main`;
  - several findings are partly fixed (F-B21-3, F-B21-4, F-B21-24,
    F-STYLE-2);
  - three findings share one mechanism (F-DOCSYNC-11, -12, -13);
  - two are one defect (F-B21-18 and F-MAS-2).
  The controller re-ran the load-bearing checks, including the ancestry of
  all seven fix commits.
- **F-B22-7 is wider than filed.** The orchestrator parses Spotify's album
  JSON itself, against global rule 4, and `enrich_albums` has no production
  caller either. `as_cache_row` would also write a Deezer id into
  `spotify_id` if anything called it, and its own tests pin that wrong value.
- **Triage missed one defect.** `loading.js` `showFailure` labels every
  non-Last.fm source "Spotify". F-SWE-5's `internal_error` source would show
  that label, and so would WP-1's export source. Task 7 fixes it and pins it
  in the gate.
- **F-LOAD-1 needs no occupancy counter.** The refusal only appears when
  every slot is full, so a count would always read cap/cap. The fix states
  the configured cap instead.
- **The plan's shape.**
  - Stages 1 and 2 are written in full: records, then the five pipeline
    fixes.
  - Stage 3 records the owner's rulings.
  - The control-plane and frontend clusters get follow-on plans once the
    rulings land.
  - Owner questions Q0-Q16 are batched in the plan, each with a
    recommendation.

Deviation: none. The owner asked for the plan and for a view on F-SWE-6;
that view is in the plan's "Controller's view on F-SWE-6".

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Batch 23 definition: the foundation package widened

Side task, no batch tag: this is a definition amendment, not work-package
work. It follows the owner's rulings of 2026-09-23. It lands after the
worker run-coroutine wrapper plan, all four tasks of which are done
(`ad2d078`..`54ab72b`).

- `BATCH23_DEFINITION.md` WP-0 now has three parts:
  - Part A: the behaviour-neutral extractions, with the loop protocol ticked
    and its deviations recorded.
  - Part B: reconciling what earlier batches left open. This covers six
    findings still marked "pending deploy" after `main` deployed, the
    foundation plan's Tasks 4-10, a Section 3 pruned to the current work
    order, the owed Batch 22 owner checks, and a new docsync finding.
  - Part C: fixing every finding open at P0 or P1 unless the owner rules one
    out. That is 38 IDs, listed in the definition and checked one by one
    against `FINDINGS.md`.
- Owner rulings, each with its reason in the definition:
  - WP-0 logs untagged until one tagged entry closes it, because docsync
    reads a work package as complete on its first tagged heading.
  - Part A keeps strict test parity.
  - Part C may change behaviour, and may edit a test only where its finding
    requires it. The batch acceptance and the intended outcome's "Last.fm
    path is untouched" line are amended to match.
  - F-SWE-5 lands before WP-3.
- Section 3's Next action now describes the widened WP-0 and the logging
  rule. The old line saying WP-0 work logs tagged entries contradicted the
  ruling.
- Plan bookkeeping:
  - The wrapper plan's steps are ticked, and it gains an Outcome section.
  - The foundation plan records that its Tracks 2 and 3 fold into WP-0, and
    its superseded Track 1 logging line is struck through.

Deviation: none from the rulings. Proposal Rule 2 is met, because the owner
added the scope, and Rule 1 is met, because the amendment lands before any
Part B or Part C work. Part C and the uncovered parts of Part B still need a
plan of record.

Forward guidance:
- Part A's three extractions can proceed now under the foundation plan's
  Task 2.
- Before Part C starts, collect every owner-gated question in the set in a
  single batch.
- Raise F-SWE-6 and F-B22-7 with the owner. They are P2, outside the set,
  but under this batch's code.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 4 of 4

Side task, no batch tag: Task 4 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- Documentation only, no code changed. `.claude/SESSION_CONTEXT.md` Section 3's
  `worker.py` structure line now names `run_coroutine_in_new_loop` alongside
  the functions it already listed; Section 4's dependency graph needed no
  change, since `worker.py`'s dependencies are unchanged.
- Both sequence diagrams that described the build-run-close-release
  protocol are now corrected. `docs/architecture/top-albums-sequence.md`
  owned a now-inaccurate claim in two places: its intro paragraph and a
  sequence Note both said the protocol -- event-loop setup inside the
  `try` that `finally` guards -- lived directly in `background_task`. Both
  now say the protocol lives in `worker.run_coroutine_in_new_loop`, which
  `background_task` calls, supplying only the reaction to a failed run.
  `docs/architecture/heatmap-sequence.md` carried the identical stale Note
  for `heatmap_task`; added in review fix round 1 after the first pass
  missed it as a sibling of the top-albums file, it now attributes the
  same `finally` to `worker.run_coroutine_in_new_loop`, called from
  `heatmap_task`, which injects `_report_heatmap_failure` as its
  `on_run_error`. Neither file carries a "Last verified" date to update.
- `docs/architecture/runtime-system.md` was read in full; it does not
  describe the build-run-close-release protocol anywhere (its `worker.py`
  node label and prose stay at the module level), so it needed no edit.
- `AGENT_NOTES.md`'s Windows-asyncio bullet still holds: it names
  `worker.new_thread_event_loop` as the seam every background thread builds
  its loop through, which is still true and unrelated to which function owns
  the run-close-release wrapping, so it was left alone.

Deviations: none from the brief. Review fix round 1 extended the
correction from `top-albums-sequence.md` to its sibling
`heatmap-sequence.md`, which the brief's Files list had not predicted as a
hit but which Step 1/Step 3 cover on their own terms.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 3 of 4

Side task, no batch tag: Task 3 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- `heatmap_task` in `scrobblescope/heatmap.py` now delegates its
  build-run-close-release protocol to `worker.run_coroutine_in_new_loop`,
  added in Task 1, instead of carrying its own `loop = None` / `try` /
  `except Exception` / nested `finally` block. `make_loop` and
  `release_slot` are passed explicitly as `new_thread_event_loop` and
  `release_job_slot` rather than left to the helper's own defaults,
  because the existing tests patch `scrobblescope.heatmap.release_job_slot`
  and `scrobblescope.heatmap.set_job_error`. The failure reaction moved into
  a new named module-private helper, `_report_heatmap_failure(job_id,
  username)`, placed immediately above `heatmap_task`; it keeps the
  `lastfm_unavailable` error code deliberately, since `F-SWE-5` records that
  code as wrong for a fault that is not the user's, and changing it is a
  separate, now one-line, commit. The import at the top of the module gains
  `run_coroutine_in_new_loop` alongside the two names it already carried.
- No test was written or edited: the four existing guard tests in
  `tests/test_heatmap.py::TestHeatmapTask`
  (`test_release_job_slot_called_on_success`,
  `test_release_job_slot_called_on_exception`,
  `test_release_job_slot_called_when_event_loop_setup_raises`,
  `test_release_job_slot_called_when_loop_close_raises`) are the acceptance
  criterion and pass unmodified, including the one that asserts a
  `loop.close()` failure still propagates out of `heatmap_task` while the
  slot is released.
- `background_task` and `heatmap_task` now share exactly one protocol; the
  only remaining difference between the two entry points is the injected
  `on_run_error` (silent logging for the album path, versus logging plus a
  published terminal job error for the heatmap path) -- the remaining half
  of `F-SWE-5`.

Deviations: none from the brief.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 2 of 4

Side task, no batch tag: Task 2 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- `background_task` in `scrobblescope/orchestrator/__init__.py` now
  delegates its build-run-close-release protocol to
  `worker.run_coroutine_in_new_loop`, added in Task 1, instead of carrying
  its own `loop = None` / `try` / `except Exception` / nested `finally`
  block. `make_loop` and `release_slot` are passed explicitly as
  `new_thread_event_loop` and `release_job_slot` rather than left to the
  helper's own defaults, because the existing tests patch
  `scrobblescope.orchestrator.release_job_slot`, and a default taken from
  the helper's module would move that patch target without failing.
  `on_run_error` reproduces the prior log line exactly. The import at the
  top of the module gains `run_coroutine_in_new_loop` alongside the two
  names it already carried.
- No test was written or edited: the four existing guard tests in
  `tests/services/test_orchestrator_fetch_and_process.py`
  (`test_background_task_runs_single_event_loop`,
  `test_background_task_releases_slot_on_exception`,
  `test_background_task_releases_slot_when_event_loop_setup_raises`,
  `test_background_task_releases_slot_when_loop_close_raises`) are the
  acceptance criterion and pass unmodified, including the one that asserts
  a `loop.close()` failure still propagates out of `background_task` while
  the slot is released.

Deviations: none from the brief.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 1 of 4

Side task, no batch tag: Task 1 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- Added `run_coroutine_in_new_loop(coroutine, *, make_loop=new_thread_event_loop,
  release_slot=release_job_slot, on_run_error=None)` to the end of
  `scrobblescope/worker.py`, after `new_thread_event_loop`. It builds the loop
  inside the `try` so a setup failure still reaches the `finally` that
  releases the concurrency slot; closes a coroutine that never got a loop, so
  a setup failure does not leak an unstarted coroutine; never swallows a
  `loop.close()` failure; and routes a run failure through the caller's
  `on_run_error`, which stays `None`-safe (silent) by default. Tasks 2 and 3
  will point the album and heatmap entry points at it.
- Six unit tests appended to `tests/test_worker.py`, each with an in-function
  import of the helper (matching this repository's existing convention, e.g.
  `tests/test_heatmap.py`), so a pre-implementation run fails once per test
  rather than once per file. Covered: one loop built, run once, closed, and
  the slot released; a run failure reaching a supplied `on_run_error` while
  the loop still closes; a run failure staying silent with no policy given;
  the slot released when loop construction itself fails; the coroutine closed
  when the loop is never built (the regression the old inline code could not
  hit, since it used to build the coroutine and the loop in the same line);
  and a `loop.close()` failure propagating, never routed through
  `on_run_error`, with the slot still released.
- Verified the mutation-kill property directly: with the helper's body
  replaced by `raise NotImplementedError`, all six new tests failed; restored,
  all six passed again.

Deviations: none from the brief. The brief's baseline count (1,717) was
already stale at dispatch; this entry measures and quotes the current count
per controller ruling, and the two other count sites it names.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-21 - Batch 23 opened on feat/batch23-wp0-hygiene

Side task, no batch tag: this entry records the opening itself and is not
WP work, so it does not count as WP-0 being done. Task 3b of the Batch 23
WP-0 foundation plan, done under the owner's instruction that the opening be
explicit rather than silent.

- Section 3 now declares `**Batch 23 is active.**` with its definition and
  its branch, and names WP-0 as next. The Section 2 index gains the Batch 23
  row, SESSION_CONTEXT Section 1 marks Batch 23 active, and the
  `FINDINGS.md` header no longer says no batch is active.
- The definition records the branch, the status and the 2026-09-21 owner
  rulings, and folds job admission into WP-4 with its own acceptance
  clause. WP-0's wrapper bullet names where the wrapper lands.
- The first `--fix` rendered `Current batch: Batch 23.` and
  `Next expected work package: WP-0.`, which confirms the D1 fix on the
  real corpus.

Deviations. The Batch 22 bullet's `Branch:` label was reworded, because
the worktree guard refuses two Branch values in Section 3. Once the batch
was active, the guard compared ancestry and reported WT005 against its
default `origin/main`, which carries merges of `test` the branch does not.
Against `origin/test`, the branch's parent, it exits 0, and the trees of
`e6ce9d7` and `origin/main` are identical. `HANDOFF_PROMPT.md` now carries
that edge case, and its WT004 premise that `main` only squashes or rebases
was corrected against the live rulesets, which allow all three merge
methods. No history was changed.

Live check (throwaway copy of this working tree): a false `WP-3 is next`
went red with DOC007 in Section 3, on the dashboard and in the definition.
The definition leg only went red once its claim was moved onto the
`**Status:**` line itself.

Validation: `pytest -q` -- **1729 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.
