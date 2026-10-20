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

### 2026-10-20 - Python 3.13 spellings for UTC and timeouts

Side task, no batch tag: the UP017 and UP041 alias fixes, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the Dockerfile and CI run Python 3.13, so the code should use its spellings (tranche design, PR #2).

What changed: `ruff check --target-version py313 --select UP017,UP041 --fix` rewrote 21 `timezone.utc` uses to `datetime.UTC` and one `asyncio.TimeoutError` to the builtin `TimeoutError` (the same class since 3.11), in `scrobblescope/heatmap.py`, `lastfm.py`, `orchestrator/__init__.py`, `routes/__init__.py`, `spotify.py`, `scripts/dev/graphify_refresh.py`, `tests/services/test_lastfm_logic.py` and `tests/test_heatmap.py`. No behaviour changes; the ruff target itself is the next commit.

Deviations: the `timezone` imports the rewrite left unused were removed (F401, by the ruff hook and two by hand), and ruff-format re-wrapped lines the shorter spelling freed. The two test files changed only by the alias spelling and that wrapping; no assertion was edited.

Validation: `pytest -q` -- **2542 passed**.

### 2026-10-20 - page-motion.js is named like the other scripts

Side task, no batch tag: `static/js/page_motion.js` renamed `page-motion.js`, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: files served as URLs conventionally use hyphens, and nine of the ten scripts in `static/js/` already do (owner, 2026-10-20: "What is best practice here?" -> hyphens).

What changed: `git mv` of the script; `templates/base.html` names `js/page-motion.js` in its one `url_for`; `.claude/SESSION_CONTEXT.md` Section 3 lists `page-motion` in the `js/` line. Run before the template was updated, the Task 1 guard failed all 8 parametrised cases naming `/static/js/page_motion.js`; after it, all 8 pass. The frontend gate reports 45 checks passed in 71 runs across chromium and firefox, with no load fault naming `page-motion.js`. `docs/design/designsystemaudit.md` and dated plans and logs keep the old name as point-in-time records.

Deviations: none. No existing test was edited.

Validation: `pytest -q` -- **2542 passed**.

### 2026-10-20 - A page never loads a static file the repository lacks

Side task, no batch tag: a guard test that every local script and stylesheet a rendered page loads exists, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: nothing fails today when a template names a static file that is not shipped, and the next commit renames `page_motion.js`, so the guard comes first.

What changed: `test_every_local_script_and_stylesheet_a_page_loads_exists` in `tests/test_template_shell.py` renders each template in `TEMPLATE_CONTEXT`, collects every `/static/` script and stylesheet reference (query strings dropped), and asserts each file exists under `static/`. It also asserts a page loads at least one, so a wrong pattern cannot pass vacuously. A missing file otherwise 404s silently in the browser and the frontend gate prints it only as an advisory beside a FAIL.

Mutation evidence: renaming `templates/base.html`'s `filename='js/page_motion.js'` to `page_motionX.js` failed all 8 parametrised cases, for example `index.html loads files the repository lacks: ['/static/js/page_motionX.js']`; restored, all 8 pass.

Deviations: none. No existing test was edited.

Validation: `pytest -q` -- **2542 passed**.

### 2026-10-20 - The pre-Batch-23 tranche plans are recorded

Side task, no batch tag: the master plan and the hygiene plan for the side-task PRs before Batch 23 WP-1, on `chore/pre-batch23-hygiene`.

Owner intent: plans written before any code, sliced for parallel subagents, and kept in the repository for the record (owner, 2026-10-20: "All plans should stay for archival purposes").

What changed: `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` orders the eight PRs in waves so no two edit the same lines at once, and defines how each remaining PR's plan is written and reviewed before its code. `docs/superpowers/plans/2026-10-20-pre-batch23-hygiene.md` is this branch's own plan: a test that every static file a page loads exists, `page_motion.js` renamed `page-motion.js`, ruff targeting Python 3.13, and `requests` with its own dependencies moved to the development requirements. Measured for the plans: `pytest -q` collects 2534 tests, 59 of them browser-marked, so the pinned count includes the browser tests that CI runs in its frontend-gate step; pre-commit takes about 9 seconds on this tree.

Deviations: the spec's hygiene item "a check that the pinned test count includes browser-marked tests" is answered by the measurement above rather than a new mechanism; the documentation PR states it where tests are explained.

Validation: `pytest -q` -- **2534 passed**.
