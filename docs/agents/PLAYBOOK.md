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
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #3, the album request module, is under way on
  `refactor/album-request-module`; its plan is
  `docs/superpowers/plans/2026-10-20-album-request-module.md`.
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

### 2026-10-20 - Jobs start through one admission path

Side task, no batch tag: start every job through one admission path and let job threads read the job record, on `refactor/album-request-module`, a branch off `main`.

Owner intent: the album and heatmap routes each wrote expire, slot, create, start, delete-on-failure by hand, and the export route (WP-4) would have been a third copy; the ten album parameters were also re-passed positionally to a thread although the job record already holds them.

What changed: new `scrobblescope/routes/admission.py` (`Refused.CAPACITY` / `START_FAILED`, `admit(params, target, *, label)`); `jobs.params(job_id)` (a copy of the params, `None` for a gone job, never renews the lease); `background_task(job_id)` and `heatmap_task(job_id)` read their parameters from the record, through `AlbumRequest.from_params` for the album run (new `_album_request_for`); a job that is gone, or a record that is not a usable request, runs nothing, still frees the slot the route took, and the unusable record ends as `internal_error`. `results_loading` and `_dispatch_heatmap_job` call `admit` and keep their own parsing, session key and HTTP answers; the thread is started as `start_job_thread(target, args=(job_id,))`. No listener-visible change. SESSION_CONTEXT Sections 3-5 and the runtime, top-albums and heatmap architecture files follow. The Mermaid MCP validator was not reachable from this session, so the edited diagram lines were checked by eye (no `;` in any message).

Mutation evidence (each planted defect, then the named test failed, then restored): `jobs.create` before the slot -> `test_a_full_house_refuses_and_creates_nothing`; `jobs.delete` removed -> `test_a_thread_that_will_not_start_leaves_no_orphan_job`; `jobs.expire_stale()` removed -> `test_admission_drops_expired_jobs_first`; min plays/tracks defaults passed -> `test_background_task_runs_the_pipeline_with_the_job_records_parameters`; vanished-job release dropped -> `test_background_task_for_a_vanished_job_runs_nothing_and_frees_its_slot` and `TestHeatmapTask::test_a_vanished_job_runs_nothing_and_frees_its_slot`; `jobs.fail` dropped from `_album_request_for` -> `test_background_task_for_an_unusable_record_fails_the_job_and_frees_its_slot`; a second release in `admit` -> `test_a_real_thread_start_failure_frees_the_slot_once_and_removes_the_job`; the stored dict returned from `jobs.params` -> `test_params_returns_a_copy_and_none_for_a_missing_job`; a literal heatmap name -> `TestHeatmapTask::test_the_username_comes_from_the_job_record`; the flag left out of the album job record -> `test_results_loading_passes_the_include_flag_to_the_job_thread`.

Deviations: the plan's `heatmap_flow` and `album_flow` code was applied as written; `ruff` reordered the new `admission` import after the other `scrobblescope` imports in both route modules. Edited existing tests, by name: in `tests/services/test_orchestrator_fetch_and_process.py` the six `background_task` call sites (`test_background_task_runs_single_event_loop`, its call and its name assertion now `testuser`; `test_background_task_releases_slot_on_exception`; `test_background_task_releases_slot_when_event_loop_setup_raises`; `test_background_task_releases_slot_when_loop_close_raises`; `test_background_task_crash_publishes_internal_error`; `test_background_task_stores_unmatched_rows_when_the_flag_is_on`); the seven `heatmap_task(` calls in `tests/test_heatmap.py` `TestHeatmapTask` (`test_release_job_slot_called_on_success`, `..._on_exception`, `..._when_event_loop_setup_raises`, `..._when_loop_close_raises`, `test_unhandled_crash_publishes_internal_error`, `test_user_not_found_crash_publishes_user_not_found`, `test_untyped_not_found_text_is_ours_not_user_not_found`); and `tests/test_routes.py::test_results_loading_passes_the_include_flag_to_the_job_thread` (docstring and the args assertion). The failed-thread-start path is tested for real, not patched, in `tests/test_admission.py`.

Validation: `pytest -q` -- **2699 passed**.

### 2026-10-20 - Last.fm pre-check lookups have a time limit and one answer

Side task, no batch tag: give the Last.fm pre-check one shared answer and a short timeout, on `refactor/album-request-module`, a branch off `main`.

Owner intent: a slow Last.fm must not hold a request thread for a minute, and the three routes must agree on what a failed check means.

What changed: new `scrobblescope/routes/precheck.py` (`Verdict`, `UserCheck`, `check_lastfm_user`, `UNAVAILABLE_MESSAGE`, `not_found_message`); `utils.run_async_in_thread(coro, timeout=None)` cancels the coroutine and raises `TimeoutError` in the calling thread; `config.LASTFM_PRECHECK_TIMEOUT_SECONDS` (default 5, env of the same name); the `routes` facade's `_check_user_exists` and `_check_profile_is_public` pass it. Why: each of the three routes called the same two checks and handled failure its own way, and none had a limit but the HTTP session's 30 seconds per call (two calls: up to 60 seconds of one of four request threads). User-visible change now: the heatmap start and the blur check refuse after at most 5 seconds per lookup; the album route still swallows an outage until the next commit switches it over. The username leaves the pre-check's failure lines (class name only), and a malformed Last.fm existence answer (not a mapping, no boolean `exists`, a non-integer `registered_year`) is an outage (`UNAVAILABLE`), not a 500. SESSION_CONTEXT Sections 3-4 and the key runtime facts name the module and the setting.

Mutation evidence (each planted defect, then the named test failed, then restored): timeout ignored in `run_async_in_thread` -> `test_run_async_in_thread_stops_waiting_when_the_timeout_passes`; `timeout=` dropped in `_check_profile_is_public` -> `test_a_stalled_last_fm_lookup_gives_up_within_the_precheck_budget[_check_profile_is_public-...]`; privacy `except` returns PUBLIC -> `test_an_outage_on_the_privacy_check_is_unavailable_never_public`; existence read outside the `try` -> `test_a_malformed_existence_answer_is_unavailable_never_an_error[none]`; `.get("exists")` truthiness -> the same test, `empty` row; privacy asked before existence -> `test_a_missing_user_is_missing_and_privacy_is_never_asked`; username in the failure line -> `test_a_failed_check_logs_the_class_and_never_the_listeners_name`.

Deviations: none. No existing test was edited; two tests were added to `tests/test_utils.py` and the new module `tests/test_precheck.py` has 17 cases.

Validation: `pytest -q` -- **2688 passed**.

### 2026-10-20 - Task 1's drift note and the module count are corrected

Side task, no batch tag: correct a false drift note and the tracked test-module count, on `refactor/album-request-module`, a branch off `main`.

Owner intent: the log and findings must be true for what the branch ships.

What changed: the Deviations paragraph of the "The request flows are pinned before they are refactored" entry said `_dispatch_heatmap_job` was gone and heatmap job creation was inline. It is not: the function exists in `scrobblescope/routes/heatmap_flow.py` and calls `acquire_job_slot`, so there was no drift for the heatmap mutation; the paragraph now says so (the privacy-outage note was checked and stands: `_validate_heatmap_user`). The `docs/agents/FINDINGS.md` header line said 87 tracked test modules; `git ls-files tests | grep -c '/test_[^/]*\.py$'` measures 88, so it now says 88. The review of Task 1 found both.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2669 passed**.

### 2026-10-20 - The album form has one owner

Side task, no batch tag: add the pure album request module (not yet wired into any route), on `refactor/album-request-module`, a branch off `main`.

Owner intent: the album form needs one Python owner that says what a valid request is, so the Spotify export route (WP-4) can call it too.

What changed: new `scrobblescope/album_request.py` (`AlbumRequest`, `Refusal`, `parse_album_request`, `registration_refusal`, the sets and bounds, `FORM_FIELDS`), `jobs.MODE_ALBUM` and `jobs.MODE_HEATMAP`, and 63 tests in new `tests/test_album_request.py`, which also read `templates/index.html` and fail if the form and the server drift. Why (B-1): the sets lived only in the template, so a bad decade made every album fail the release filter and the listener saw "no albums". Once wired, these refusals are new: unknown release scope, unknown decade, missing or malformed custom release year, unknown ranking, unknown limit, min_plays outside 1-50, min_tracks outside 1-10, username over 64. The bound of 64 is the limit `/validate_user` already enforces; the form's `maxlength` is 100. SESSION_CONTEXT Sections 3-4 and the runtime-system diagram (node, `AlbumRequest --> JobModule` edge) name the module.

Mutation proofs, each planted in a scratch copy and shown failing then passing once restored: year bound `<=` to `<` (year 2025 rows fail), decade membership check removed (decade rows), custom year no longer required (`Enter a release year.` row), include/playtime coercion removed, decade kept for every scope, min_plays upper bound 100 (51 row), blank no longer a missing field (defaults test), unknown registration year refused, `"100"` dropped from `LIMIT_OPTIONS` (limit 100 row), parser reading `source` and `"decade"` dropped from `FORM_FIELDS` (FORM_FIELDS test), `"fortnight"` added to `RELEASE_SCOPES` (release-window test).

Deviations: none from the plan. The runtime-system Mermaid block was not run through the render MCP call (not available to this implementer); the edit adds one node, one edge and one class-list name only. No existing test was edited.

Validation: `pytest -q` -- **2669 passed**.
