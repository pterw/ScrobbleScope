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
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
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

### 2026-10-20 - The pre-Batch-23 tranche plans are recorded

Side task, no batch tag: the master plan and the hygiene plan for the side-task PRs before Batch 23 WP-1, on `chore/pre-batch23-hygiene`.

Owner intent: plans written before any code, sliced for parallel subagents, and kept in the repository for the record (owner, 2026-10-20: "All plans should stay for archival purposes").

What changed: `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` orders the eight PRs in waves so no two edit the same lines at once, and defines how each remaining PR's plan is written and reviewed before its code. `docs/superpowers/plans/2026-10-20-pre-batch23-hygiene.md` is this branch's own plan: a test that every static file a page loads exists, `page_motion.js` renamed `page-motion.js`, ruff targeting Python 3.13, and `requests` with its own dependencies moved to the development requirements. Measured for the plans: `pytest -q` collects 2534 tests, 59 of them browser-marked, so the pinned count includes the browser tests that CI runs in its frontend-gate step; pre-commit takes about 9 seconds on this tree.

Deviations: the spec's hygiene item "a check that the pinned test count includes browser-marked tests" is answered by the measurement above rather than a new mechanism; the documentation PR states it where tests are explained.

Validation: `pytest -q` -- **2534 passed**.

### 2026-10-20 - The pre-Batch-23 tranche design is recorded

Side task, no batch tag: the design for the side-task PRs that run before Batch 23 WP-1, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: before the Spotify export import, make the documentation describe the system as it is, check every diagram against the source, make the interface consistent, clear backend hygiene items, and build four of the seams the 2026-09-30 architecture review proposed -- each as its own PR with atomic commits.

What changed: `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` records the design the owner approved section by section on 2026-10-20: the eight PRs and their order, the rules every PR follows (a Section 4 entry per commit, Batch 23 definition amendments when a seam changes what a work package may assume, parity tests before a refactor, tests that assert intended behaviour), the review policy that keeps fix rounds from looping, the documentation PR's content, the UI loop, and the hosting cost ceiling that keeps job persistence out of this tranche. The implementation plans follow in later commits on this branch. PLAYBOOK Section 3 gains its pointer to this spec once the include-unmatched PR, which adds the Section 3 bullet for this tranche, has merged.

Deviations: none. No code change, no test edited.

Validation: `pytest -q` -- **2534 passed**.

### 2026-10-01 - The release command waits for a waking database

Side task, no batch tag: `init_db.py`, the Fly release command, retries its schema step while the database wakes, instead of aborting the deploy on the first dropped connection. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: release v143 failed with "Schema init failed -- connection was closed in the middle of operation" and exit 1. The Postgres app had stopped; the release command's connection woke it, its proxy restarted mid-boot, and the script died on its first statement. Postgres reported ready 4 s later and a plain redeploy passed.

Change: `init_db.py` runs connect plus every statement as `_apply_schema` and retries it up to 6 attempts (sleeps 1, 2, 4, 8, 8 s, about 23 s) on `OSError`, `asyncio.TimeoutError` and asyncpg's `ConnectionDoesNotExistError`, `InterfaceError`, `CannotConnectNowError` and `ConnectionFailureError` only. A SQL error still fails at once. `asyncpg.connect` now has a 10 s timeout. Each retry prints one line naming the attempt and the exception type, never its text (global-rules Rule 6). The final failure keeps the single ERROR line and exit 1; that line also names only the exception type (plus the SQLSTATE code of a Postgres error), never its text. README's Deployment section says so.

Evidence: new `tests/test_init_db.py` (6 tests, no network, sleeps patched): two transient failures then success, a connection that opens then drops on its first statement (the v143 shape), a non-transient error after one attempt, a SQLSTATE suffix for a Postgres error, exhaustion with one ERROR line, and a DSN planted in the exception text absent from the retry and ERROR lines. Each fails under its own mutation in a scratch copy (no retry: 3 failed; OSError not transient; asyncpg error not transient; everything transient; message in the line; no connect timeout; no raise on the last attempt; no SQLSTATE in the ERROR line; retry wrapping only the connect, which fails only the first-statement test).

Validation: `pytest -q` -- **2534 passed**.

### 2026-10-01 - The ring check waits out animations before reading pixels

Side task, no batch tag: the heatmap focus-ring check waits for running animations to finish before it reads the cell's geometry and takes its screenshot, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: the previous step's reproduction showed 8 of 20 last-cell screenshots landing while `#heatmap-result` was still crossfading in (opacity changed between the read before and the read after the shot), and a reading taken mid-animation is invalid by construction. PR #252 applied the same reasoning to every other check that slept through a transition; the ring check still waited only for fonts and two frames.

Change: `_ring_shot` in `scripts/dev/_frontend_gate_heatmap_access.py` calls `wait_for_settled` (`scripts/dev/_frontend_gate_shared.py`, bounded, raises when the page never settles) at the start of each attempt, after the tooltip nudge and before `_LAYOUT_SETTLED_JS` and the geometry read. This removes a confounder; it is not claimed as the fix for F-B23-39, whose status stays open.

Evidence: a new test records the order of the wait and the geometry reads over a two-attempt run; with the call removed it fails (`assert 0 == 2` on the wait count). The existing ring-page helper answers the settle script with an empty result so the real `wait_for_settled` can run against it. The 20-run reproduction (the check alone, fresh desktop context each, `reduced_motion="no-preference"`) passed 20 of 20, with `container.opacity` 1 and nothing changed during the shot on all 80 shots read (4 per run). A ring forced to `visibility=hidden` still fails with `ring.visibility=hidden` in the evidence.

Validation: `pytest -q` -- **2528 passed**.
