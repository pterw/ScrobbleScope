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

### 2026-10-27 - Start the idle watchdog from create_app

Side task, no batch tag: Task 3 of the Fly idle-exit plan (`docs/superpowers/plans/2026-10-27-fly-idle-exit.md`), on `feat/fly-idle-exit`. `create_app` now imports `watch_from_env` from `scrobblescope.idle_exit` after the blueprint is registered (deferred, like the blueprint import, so `load_dotenv` has run) and, when it returns a watch, calls `attach(application)` and `start()`. The watchdog is off unless `IDLE_EXIT_MINUTES` is a positive integer, so local runs, tests and CI never start a thread or exit; the suite never sets the variable.

Red proofs: the `"20"` case failed (`assert 0 == 1`) before the edit; calling `start` unconditionally fails the test (the unset case has no watch to start); calling `watch_from_env` but never `start` fails the `"20"` case.

Edited existing tests: none. Added: `test_create_app_starts_the_idle_watch_only_when_the_env_var_is_set` in `tests/test_app_factory.py` (2 cases).

Validation: `pytest -q` -- **2968 passed**.

### 2026-10-27 - Add the idle watchdog behind IDLE_EXIT_MINUTES

Side task, no batch tag: Task 2 of the Fly idle-exit plan (`docs/superpowers/plans/2026-10-27-fly-idle-exit.md`), on `feat/fly-idle-exit`. Fly's autostop cannot see background jobs, so the new `scrobblescope/idle_exit.py` stops the app itself: `IdleWatch.step()` records activity while `has_active_work()` is true (a held job slot or a pending release check), and otherwise runs the exit action (SIGTERM to the gunicorn master, once) when the last request or work is older than the window. `attach(app)` touches the timer in `before_request` and `teardown_request`; `watch_from_env` returns None unless `IDLE_EXIT_MINUTES` is a positive integer (one warning for a negative or non-integer value). Nothing calls it yet: Task 3 starts it from the app factory.

Red proofs (one planted defect each): not remembering the exit fails `test_exits_once_after_the_idle_window_with_no_work`; not touching on active work fails `test_active_work_blocks_exit_and_restarts_the_window`; dropping the `teardown_request` hook fails `test_a_recent_request_blocks_exit`; treating `"0"` as valid fails `test_unset_or_invalid_idle_minutes_starts_nothing`; dropping the `has_pending_checks` half fails `test_has_active_work_sees_a_held_slot_and_a_pending_check`.

Edited existing tests: none. Added: `tests/test_idle_exit.py` (12 cases).

Validation: `pytest -q` -- **2966 passed**.

### 2026-10-27 - Expose held job slots and pending release checks

Side task, no batch tag: Task 1 of the Fly idle-exit plan (`docs/superpowers/plans/2026-10-27-fly-idle-exit.md`), on `feat/fly-idle-exit`. The owner wants the web machine to stop itself when idle while the DB machine stays on, so an idle watchdog needs one place to ask whether any background work is running. `worker.active_job_slots()` returns the number of held job slots (the semaphore's free count subtracted from `MAX_ACTIVE_JOBS`); `release_checks.has_pending_checks()` is True while `_JOB_QUEUE.unfinished_tasks` is above zero, because the correction worker outlives the slot of the job that queued it. Neither changes existing behaviour.

Exit-code probe (run before this task): gunicorn 23.0.0 on python:3.13-slim, a worker thread sending SIGTERM to its parent, logged "Handling signal: term" then "Shutting down: Master", last line `EXIT=0`, so a clean master shutdown leaves the `on-failure` machine stopped.

Red proofs: `active_job_slots` returning a constant 0 fails `test_active_job_slots_counts_the_slots_held` (`assert 0 == 1`); `has_pending_checks` using `qsize()` instead of `unfinished_tasks` fails `test_pending_checks_stay_true_while_a_queued_job_is_running` at the "job taken, not done" step.

Edited existing tests: none. Added: `test_active_job_slots_counts_the_slots_held` in `tests/test_worker.py`; `test_pending_checks_stay_true_while_a_queued_job_is_running` in `tests/services/test_release_checks.py`.

Validation: `pytest -q` -- **2954 passed** (2874 passed with `-m "not browser"`).

### 2026-10-25 - Make two vacuous service checks honest

Side task, no batch tag: make two vacuous service checks honest and drop one redundant test, on `test/lean-suite-vacuous`, a branch off `main`.

Owner intent: one test per intended behaviour; fix a vacuous test in place and prove it red against a defect a user could ship. The stale-cache cleanup test only checked that some positive integer was passed, so a cleanup using the 365-day original-release TTL, or one that deleted fresh rows instead of stale ones, still passed; it now patches the TTL to 17 and asserts the whole normalized DELETE statement and `ttl == 17`. The out-of-bounds timestamp test only checked that the 2020 artist was absent, so a window that dropped every play passed; it now asserts the eligible artists are exactly `["Artist Y"]`, with a play count of 10 and no exclusions. `test_album_metadata_carries_its_provider_and_url` only read back the fields of a frozen dataclass it had just built, and the stored-row siblings already pin provider and url; it is deleted.

Deviations: none. `test_a_missing_correction_table_names_the_migration` and `test_original_release_lookup_without_a_connection_skips_the_query` are left as they are (the first is pinned exactly in `test_failure_logging.py`, the second by `assert_not_awaited`). Red proofs used scratch edits, restored byte-identical: `cleanup_stale_metadata` passing `ORIGINAL_RELEASE_TTL_DAYS` (`assert 365 == 17`), `Window.contains` always False (empty result, no `Artist Y`). The suite count falls by one (the deleted test).

Edited existing tests: `test_cleanup_stale_metadata_issues_delete` in `tests/services/test_orchestrator_fetch_spotify.py`; `test_fetch_top_albums_skips_out_of_bounds_timestamps` in `tests/services/test_lastfm_logic.py`. Deleted: `test_album_metadata_carries_its_provider_and_url` in `tests/services/test_enrichment.py`.

Validation: `pytest -q` -- **2952 passed**.
