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

### 2026-10-20 - The request flows are pinned before they are refactored

Side task, no batch tag: add parity tests for the album, heatmap and validate_user request flows, on `refactor/album-request-module`, a branch off `main`.

Owner intent: tests assert intended behaviour, and AGENTS.md "Refactor requires parity tests" puts them before PR #3 changes the code behind these routes.

What changed: new `tests/test_request_flow_parity.py` (16 tests, tests only, no source change). It pins which form fields land in the job record per release scope, that the values reach the album and heatmap pipelines in the right slots, the inclusive 2002 and current-year bounds, that a full house leaves no job behind, and the bodies of the heatmap privacy-outage and validate_user outage answers. It deliberately does not pin the fail-open pre-check or the positional thread arguments, which later tasks replace. Mutation proofs, each planted in a scratch copy and shown failing then passing once restored: decade kept whatever the scope (custom and previous rows fail), min_plays and min_tracks swapped in the orchestrator call, username no longer stripped in heatmap_loading, `year < 2002` made `<=`, the heatmap job created before the slot is acquired, the heatmap privacy-outage `retryable` set False, and the privacy check asked before existence in validate_user.

Deviations: plan drift only. The plan names `background_task` and `_dispatch_heatmap_job`; the tree has the `_fetch_and_process` call inside `background_task` in `scrobblescope/orchestrator/__init__.py` (found as planned) and `_dispatch_heatmap_job` also exists in `scrobblescope/routes/heatmap_flow.py` (it calls `acquire_job_slot` and then creates the job), so the heatmap mutation was planted there as the plan says and there was no drift for it. The one placement difference found: the heatmap privacy-outage answer lives in `_validate_heatmap_user` in the same file. (This entry first said `_dispatch_heatmap_job` was gone; that was false and is corrected here.) Behaviour and test code are as planned. No existing test was edited.

Validation: `pytest -q` -- **2606 passed**.

### 2026-10-20 - The album request module plan opens its branch

Side task, no batch tag: add the album request module plan as the branch's first commit, on `refactor/album-request-module`, a branch off `main`.

Owner intent: "All plans should stay for archival purposes", so every PR plan is the first commit of its own branch.

What changed: `docs/superpowers/plans/2026-10-20-album-request-module.md` is the owner-approved plan for PR #3, and PLAYBOOK Section 3's "Before WP-1" bullet names it. The plan passed a brief review (plan-review.md), a fix round, and a re-review (plan-rereview-1.md) that approved it. One fix was applied at commit time (re-review Minor N1): the three pointers to the Retry rule now all read "Task 5 Step 4, item 4" (the assumptions row and Task 2 Interfaces said "Task 5 Step 5"; Task 5 Touches said "Step 4, item 3").

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2590 passed**.
