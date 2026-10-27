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

### 2026-10-27 - Prove the watchdog is attached to the app and runs as a daemon

Side task, no batch tag: final-review fix round (rulings R-5.1 to R-5.4) of the Fly idle-exit plan, on `feat/fly-idle-exit`. A mutation run found that deleting `watch.attach(application)` in `create_app` passed the whole suite, although it would make requests stop renewing the timer and stop the machine 20 minutes after boot under an active user. The existing `create_app` idle-watch test now also sends one request through the returned app and checks that `IdleWatch.touch` ran exactly when the watch is enabled. New tests check that the watchdog thread is a daemon (a non-daemon thread would hold up worker shutdown) and that an idle machine stops within a minute of the window (a 3000-second check interval would hold it 50 more minutes). `DEPLOY.md` now quotes the two real expiry messages (`album_flow.py`) instead of an invented one. Not fixed, per the rulings: the `// 60` in a log line, and F-MAS-8's stale "always-on machines" premise (the finding's author decides).

Red proofs (one planted defect each): deleting `watch.attach(application)` fails `test_create_app_starts_the_idle_watch_only_when_the_env_var_is_set[20-1]`; `daemon=False` fails `test_start_runs_the_loop_on_a_daemon_thread`; `IDLE_CHECK_INTERVAL_SECONDS = 3000` fails `test_an_idle_machine_is_stopped_within_a_minute_of_the_window`. Each was restored by Edit.

Edited existing tests: `test_create_app_starts_the_idle_watch_only_when_the_env_var_is_set` (extended). Added: two tests in `tests/test_idle_exit.py`.

Validation: `pytest -q` -- **2972 passed**.

### 2026-10-27 - Let the app machine stop itself when idle

Side task, no batch tag: Task 4 of the Fly idle-exit plan, on `feat/fly-idle-exit`. Fly's autostop cannot see background jobs, so `fly.toml` now has `auto_stop_machines = 'off'`, no `min_machines_running`, and `[env] IDLE_EXIT_MINUTES = "20"`; the app exits with code 0 after 20 idle minutes and the next request starts the machine. `[deploy]`, `[build]` and `[[vm]]` are unchanged, and the `scrobblescope-db` app is untouched. Docs: DEPLOY.md gains an "Idle exit" section (what it does, why autostop is off, the results lifetime change from 2 hours to the idle window, production-only, off switch, rollback); `docs/architecture/runtime-system.md` gains the `idle_exit.py` node, its edges and a design bullet; SESSION_CONTEXT Sections 3 and 4 list `idle_exit.py`; the README hosting row and the AGENT_NOTES `REQUEST_CACHE` line name the idle exit. Exit-code probe (run before Task 1): gunicorn 23.0.0 on python:3.13-slim, a worker thread sending SIGTERM to its parent, logged "Handling signal: term" and "Shutting down: Master", and the last line was `EXIT=0`. Sweep of live documents for `min_machines_running`, `auto_stop_machines`, `always on`, `shared-cpu` and `machine sleep`: the only plain sibling copy was the AGENT_NOTES line; FINDINGS F-MAS-8 (title says "always-on machines") and the 2026-10-20 tranche spec are left as records.

Edited existing tests: none.

Validation: `pytest -q` -- **2970 passed**.

### 2026-10-27 - Correct the tracked test-module count to 104

Side task, no batch tag, on `feat/fly-idle-exit`. Task 2 added `tests/test_idle_exit.py`, so `git ls-tree -r --name-only HEAD tests | grep -c '/test_[^/]*\.py$'` gives 104, but `docs/agents/FINDINGS.md` and `.claude/SESSION_CONTEXT.md` still said 103 tracked test modules. Both now say 104 (the module count is hand-edited; `--fix --test-count` writes only the test count). `config/docsync.toml` `[test_count] pinned` already equals `pytest --collect-only -q` (2970). No other live doc states the module count. Docs only.

Validation: `pytest --collect-only -q` -- **2970 passed** (collected, unchanged).

### 2026-10-27 - Harden the idle watchdog tests and log a dead watchdog

Side task, no batch tag: fix round on Task 2 of the Fly idle-exit plan (review rulings R-2.1 to R-2.4), on `feat/fly-idle-exit`. `IdleWatch.run` now logs an exception from the watchdog loop with `logger.exception`, because a silent thread death would leave the machine running all day. The tests now start the fake clock at 1000 (so an initial `_last_activity = 0` fails), call `step()` from inside a request after the window has passed (so the `before_request` hook is needed), check that `IDLE_EXIT_MINUTES=20` means one second short of 20 minutes does not exit and 20 minutes does (a minutes-as-seconds error would stop the machine 20 seconds after a request), and check that `stop_gunicorn` sends SIGTERM to the parent pid.

Red proofs (one planted defect each): `_last_activity = 0` fails `test_exits_once_after_the_idle_window_with_no_work`; deleting the `before_request` hook fails `test_a_recent_request_blocks_exit`; `IdleWatch(minutes)` fails `test_idle_minutes_are_minutes_not_seconds`; `os.getpid()` and `SIGKILL` each fail `test_stop_gunicorn_sends_sigterm_to_the_parent` (on this Windows host `signal.SIGKILL` does not exist, so that case fails with AttributeError).

Edited existing tests: `FakeClock` start value, `test_exits_once_after_the_idle_window_with_no_work` (relative bound), `test_a_recent_request_blocks_exit` (in-request step), and `test_a_positive_idle_minutes_builds_a_watch` replaced by `test_idle_minutes_are_minutes_not_seconds`. Added: `test_stop_gunicorn_sends_sigterm_to_the_parent`, `test_a_dying_watchdog_thread_is_logged`.

Validation: `pytest -q` -- **2970 passed**.
