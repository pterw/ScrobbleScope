# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. That branch merged into `main` as PR #245 on 2026-09-30 and `origin/test` is
  deleted, so side-task PRs branch from `main` and run the guard against its default
  base. The owner names the branch WP-1 opens.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). The WP-0 close-out below is what remains of WP-0. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition. It runs
  after the tranche, before WP-1 (owner ruling 2026-10-22).
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. The include-unmatched
  control (PR #1) and backend hygiene (PR #2) are done. The album request module
  is done (PR #3, branch refactor/album-request-module, plan
  `docs/superpowers/plans/2026-10-20-album-request-module.md`); normalized
  Last.fm scrobbles with one album aggregate is done (PR #4, branch
  refactor/lastfm-scrobbles, plan
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); one album-metadata
  encoding is done (PR #5, branch refactor/metadata-encoding, plan
  `docs/superpowers/plans/2026-10-20-metadata-encoding.md`); the statistics
  module is done (PR #6, branch refactor/statistics-module, plan
  `docs/superpowers/plans/2026-10-20-statistics-module.md`). Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #7, UI consistency, finished round 1 (plan
  `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`); further rounds
  wait for the owner's screenshots, each with its own plan. A side-task PR of
  cheap fixes from the 2026-10-21 architecture review and the logging audit
  is done (branch `fix/pre-batch23-side-tasks`, plan
  `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md`), and so is a
  CI change that keeps Playwright's Ubuntu packages in the Actions cache
  (branch `ci/playwright-apt-cache`, plan
  `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md`). UI
  consistency round 2 is done (PR #268, branch `feat/ui-consistency-round-2`,
  plan `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md`). Its
  backlog runs now on `feat/ui-round-2-backlog`: the owner settles each item
  in a live session and the accepted changes landed as they were made (PR
  #269). All fourteen tasks of the plan
  `docs/superpowers/plans/2026-10-25-ui-round-2-backlog.md` have landed on
  the same branch (the documentation, the gates that hold the accepted
  changes, the F-B23-46 ranking rule and the stale-copy sweep), followed by a
  test consolidation under the owner's lean-suite ruling. PR #269 merged
  into `main` (merge commit `997f7584`) and is deployed. The album-matching,
  cache re-verification and MusicBrainz fixes are on `fix/album-matching`
  (PR #270, plan `docs/superpowers/plans/2026-10-25-album-matching.md`),
  based on `main`: every plan task has landed there and the six findings it
  files are closed. PR #270 merged into `main` (merge commit `4a2d2406`) and is deployed. The documentation refresh merges last.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.
- **What PR #245 ships (owner ruling 2026-09-29):** the WP-0 foundation and
  every fix from the three reviews, including the job module with its storage
  seam, typed provider failures and provider failure logs that carry no
  listener data. Moved to the follow-up PR: job persistence, the Last.fm
  scrobble seams, the album request module, one album-metadata encoding, the
  statistics module and the tooling package.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam and typed provider failures, job persistence
  (gates WP-3), an album request module (gates WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (gates WP-2), one album-metadata
  encoding (gates WP-3), a statistics module (gates WP-6), and provider
  failure logs that carry no listener data. Which of these #245 ships is
  in the "What PR #245 ships" bullet above; the rest wait for the follow-up
  PR.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

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

### 2026-10-27 - Drop ellipses from progress and toast messages

Side task, no batch tag: UI audit v6 row 6, no ellipses in progress and toast copy, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: README row 6, no ellipses in the live status copy. Ruling U10 widened it from the loading page to the server's progress messages (`scrobblescope/orchestrator/`, `heatmap.py`, `jobs.py`) and the client strings in `static/js/` (`loading-progress.js`, `loading.js`, `heatmap.js`, `results.js`), including the escaped ellipses in `loading.js`: "Retrying" and "Opening the results page". "Initializing..." (and "Initializing heatmap...") became "Connecting to Last.fm" at all seven sites, the template's first phase line, `jobs._initial_progress`, both fallbacks in `loading-progress.js` and the heatmap start; the leaderboard toast reads "Creating leaderboard image". The pins in `scripts/dev/_frontend_gate_pipeline.py` follow the new strings. Remaining `...` in the tree are docstrings and comments only.

Deviations: none from the rulings. `tests/test_routes.py` is untouched: its "Working..." and "Fetching page 3..." are fixture strings passed to `jobs.advance`, not production copy. The `jobs.start` test uses the arbitrary message "Starting" instead of "Initializing heatmap...".

Existing tests edited, by name: `test_create_returns_unique_ids_and_a_pristine_job` and `test_reset_returns_the_job_to_its_initial_state_and_keeps_params` in `tests/test_jobs.py`, `test_start_clears_stats_phase_and_error_and_sets_the_message` (message string), `test_progress_callback_sends_correct_percentages` and the other `TestFetchAndProcessHeatmap` message asserts in `tests/test_heatmap.py`, `test_fetch_and_process_passes_progress_cb_to_lastfm` in `tests/services/test_orchestrator_fetch_and_process.py`, `test_fetch_spotify_misses_reports_search_progress`, `test_fetch_spotify_misses_reports_batch_progress` and `test_deezer_fallback_reports_progress_inside_its_band` in `tests/services/test_orchestrator_fetch_spotify.py` (full-message equality), and `test_a_failed_run_with_no_retry_still_says_the_results_page_opens` in `tests/frontend/test_heatmap_pure_functions.py`.

Validation: `pytest -q` -- **2978 passed**.
