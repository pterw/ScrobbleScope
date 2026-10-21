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
  normalized Last.fm scrobbles with one album aggregate. The album request
  module is done (PR #3, branch refactor/album-request-module); the other
  three seams remain. Job persistence
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

### 2026-10-20 - The entry the import-position fix corrected is named

Side task, no batch tag: name the right entry in the record of the import-position fix, and make one test comment true, on `refactor/album-request-module`, a branch off `main`.

Owner intent: a reader following the entry "Two sentences made true after the admission module" must be sent to the entry that really changed.

What changed: that entry says the `admission` import-position phrase was corrected in "The album form is refused with a reason"; it was corrected in "Jobs start through one admission path" (Task 4's entry), which `--fix` has since rotated into `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. Both headings were checked there with grep. The earlier entry is a dated record and is left as written; this entry is the correction. In `tests/test_routes.py` the comment in the failed-thread-start test said the route calls `jobs.delete`; since Task 4 `admission.admit` does, so the comment now says that. Comment only, no code.

Deviations: none.

Edited existing tests: `test_results_loading_thread_start_failure_renders_error`, comment only.

Validation: `pytest -q` -- **2752 passed**.

### 2026-10-20 - No username reaches a pre-check failure log, pinned

Side task, no batch tag: pin by test that no Last.fm username reaches a pre-check failure log, and correct one sentence of the entry "The heatmap and the blur check use the shared pre-check", on `refactor/album-request-module`, a branch off `main`.

Owner intent: Rule 6 (a failure is logged by exception type, never with listener data) must fail a test when broken, not only hold by reading the code.

What changed: new `test_precheck_failure_never_logs_the_listener_name` in `tests/services/test_failure_logging.py` (nine rows: the validate, heatmap and album routes, each with a raising existence lookup, a malformed existence answer and a raising privacy lookup; username `zz-listener-7`; every DEBUG-and-up record is checked for it in message and args). Review found that planting a username log line on the UNAVAILABLE branch of `heatmap_flow.py` or `api.py` left the suite green. The earlier entry said the username "leaves two more log lines" and then named the blur check's line, which never carried it; only the heatmap route's two lines changed, and that sentence now says so.

Deviations: none. No existing test edited; no production code changed.

Mutation evidence (planted in a scratch copy, restored): an error line carrying the username on the UNAVAILABLE branch of `routes/heatmap_flow.py`, of `routes/api.py` and of `routes/album_flow.py` in turn -> three rows of the new test fail each time (the `existence-answer-malformed` and `privacy-lookup-raises` rows among them), then 9 passed once restored.

Validation: `pytest -q` -- **2752 passed**.

### 2026-10-20 - Two sentences made true after the admission module

Side task, no batch tag: correct two sentences that Task 4 of the album request module left untrue, on `refactor/album-request-module`, a branch off `main`.

Owner intent: the shared documents must describe the code that ships, so a reader of SESSION_CONTEXT Section 5 and of the admission entry is not misled about who cleans up and where the import sits.

What changed: SESSION_CONTEXT Section 5 said that on a failed thread start "the route deletes the newly created job"; since the admission module, `admission.admit` deletes it (it calls `jobs.delete` after `start_job_thread` raises), so the sentence now says so. The 2026-10-20 entry "The album form is refused with a reason" said ruff put the `admission` import "after the other `scrobblescope` imports"; in both `album_flow.py` and `heatmap_flow.py` it sits in alphabetical position, and the entry now says that. Both checked against the code before editing.

Deviations: none. No code or test changed.

Validation: `pytest -q` -- **2743 passed**.

### 2026-10-20 - A job says what kind it is

Side task, no batch tag: make the job kind a record field that is never defaulted when read, and amend WP-4 to match, on `refactor/album-request-module`, a branch off `main`.

Owner intent: a record that forgot its kind must not be served as an album run. This is B-12's server half; every writer now sets `mode`, so the default is a trap rather than a convenience.

What changed: the `"album"` default is gone from three sites -- `routes._get_validated_job_context`, `api.release_checks` and `album_flow._extract_job_params` (its unread `mode` entry is deleted) -- and the literals `"album"` and `"heatmap"` become `jobs.MODE_ALBUM` and `jobs.MODE_HEATMAP` (`expected_mode` in `album_flow`, `release_checks`, `_latest_heatmap_job`). New: `test_a_job_that_never_said_its_kind_is_not_served_as_an_album_job` (four rows: `/results`, `/loading`, `/unmatched`, `/api/release_checks`; before this commit all four failed). Seeds that now say `"mode"`: `TEST_JOB_PARAMS` in `tests/helpers.py`; three literals in `tests/test_routes.py`; and the frontend-gate seeds, three in `_frontend_gate_results.py`, one in `_frontend_gate_include.py`, two in `_frontend_gate_spotify_icon.py`. `BATCH23_DEFINITION.md` WP-4 is amended: a "Scope amended 2026-10-20 (pre-Batch-23 tranche, PR #3)" paragraph says WP-4 reuses the album request module, the pre-check and the admission module; the export route's form fields go through `album_request.parse_album_request(form, current_year=..., require_username=False)`; the admission bullet records that `admit(params, target, *, label)` exists, that the thread entry point takes only the job id, that the kind is `params["mode"]` and an export album job keeps `mode` "album" with its origin in `source`; and Acceptance says PR #3 tests the path the album and heatmap routes share while WP-4 adds the export route's. PLAYBOOK Section 3 ("Before WP-1") now says the album request module is done and the other three seams remain; no "Last verified" date and no `Branch:` line moved.

Deviations: none from the brief. Edited existing fixtures, by name: `TEST_JOB_PARAMS` (`tests/helpers.py`) and, in `tests/test_routes.py`, the album literals in `test_results_complete_renders_no_matches_for_empty_results`, `test_results_complete_with_results_renders_data` and `test_results_complete_links_each_row_to_its_own_provider`; no other test needed a `mode`. `ruff format` wrapped the `_latest_heatmap_job` condition over four lines.

Mutation evidence (planted in a scratch copy, named tests failed, restored): `.get("mode", "album")` back in `_get_validated_job_context` -> the `/results`, `/loading` and `/unmatched` rows; the same default back in `release_checks` -> the `/api/release_checks` row. Gates: `frontend_gate.py` 47 checks passed in 75 runs; `results_behavior_tests.py` OK.

Validation: `pytest -q` -- **2743 passed**.
