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

### 2026-10-28 - Return weekly artists to the top ten

Side task, no batch tag: Task 9 on `feat/streamgraph-bursts`. The owner
requested top ten only and no residual contributor list after live testing.
Reverse this branch's own burst selection and contributor metadata in plays,
job readback and their tests. The four files match origin/main exactly;
none changed upstream since the original branch base. Original normalized
ranking/ties, Monday columns, window filtering, empty-key residuals and
nested-copy isolation coverage remain. README and the sequence diagram
again describe top ten. No UI source changes in this checkpoint.

Plan vs implementation: exact scoped reversal, no history rewrite. Tests
solely for the removed feature are removed; original behavior tests return.
Focused plays/jobs/heatmap: 114 passed. Independent spec/quality review
approved. Fresh full shards: 702 + 1507 + 905. No browser gate is triggered
by these backend-only paths; Task 10 runs the integrated UI gate.

Forward guidance: Task 10 removes remaining contributor UI and unused
styles, caps the client at ten and reduces the chart box. Measured short
viewports cannot fit the original gaps and 268px tooltip together. Owner
choice on compact KPI/bottom spacing is pending; page-scroll assertions
remain strict. Final main integration, live approval and PR remain pending.
Section 3 batch sequencing is unchanged. WT003/WT005/WT010/WT012 are
advisory under the owner's instruction; no lineage repair is attempted.

Validation: `pytest -q` -- **3114 passed**.

### 2026-10-28 - Keep residual counts outside the artist stream

Side task, no batch tag: Task 8 checkpoint on `feat/streamgraph-bursts`.
Only named artist counts feed SVG baseline, fit, stack and hit mapping.
Everything else stays numeric, normal-weight and without a painted swatch;
keyboard selection leaves artist paths undimmed. Residual-only weeks and
payloads remain scrubbable; all-zero data draws no stream. Original rocket
arrays and permutation remain. Four unused residual colour tokens are removed.
README, DESIGN and the original plan/spec distinguish named-only geometry
from full weekly totals. No payload or server changes in this checkpoint.

Existing pure hit-test cases were extended for direct slot/rank mapping,
empty bands, boundaries, empty stack and residual-only weeks. Red: 6 failed,
4 passed; green: 10 passed; whole file: 150 passed. Existing browser families
now check named paths, numeric residual style/count, undimmed keyboard state,
residual-only/all-zero jobs and named JPEG pixels. A metamorphic assertion
proves 10,000x residual volume leaves artist geometry unchanged. Independent
source/runtime review approved. Full locked gate: 58 checks in 89 runs across
Chromium/Firefox. Fresh suite shards: 702 + 1507 + 912. Real-data Firefox
captures pass data/geometry in both themes; the agent did not judge visuals.

Deviations/forward guidance: the owner liked the artist-only preview, then
requested removal of contributor rows, a smaller SVG box without vertical
scrolling and a return to top ten only. This commit preserves Task 8's
reviewed twelve-artist checkpoint; newly defined Tasks 9-10 supersede its
retained contributor block and height reservation before final publication.
Code phases may run in parallel; land backend Task 9 before UI Task 10.
Final owner approval, main integration and PR publication remain pending.
Section 3 batch sequencing is unchanged. No history rewrite.

Validation: `pytest -q` -- **3121 passed**.

### 2026-10-28 - Plan an artist-only stream with numeric residual

Side task, no batch tag: revise the live-review design and plan on
`feat/streamgraph-bursts`. The owner wants Everything else excluded from
SVG geometry, kept numerically in the scrubber, and the original rocket
palette restored. This supersedes unlanded sandwich and navy experiments;
Task 5 spacing and normal residual weight remain complete. Task 8 separates
renderer/pure-test and browser-check ownership for parallel code work, then
one integrated atomic landing. No product code changes in this checkpoint.

Plan vs implementation: revised definition only; no Task 8 box is complete.
Deviations: owner-directed replacement of Tasks 6-7 before either landed.
Existing tests edited: none. Fresh full shards passed 702 + 1503 + 912.
The guard reports WT003, WT010 and WT005; guards are advisory per owner.
WT005 is real divergence, not the content-identical case. Normal reviewed
main integration remains required, with no history rewrite. Section 3 batch
sequencing is unchanged. Forward guidance: execute Task 8 in isolated
worktrees, review and validate, refresh live review and obtain prototype
approval before PR publication.

Validation: `pytest -q` -- **3117 passed**.

### 2026-10-28 - Restore stream result spacing and quiet the residual row

Side task, no batch tag: restore stream result spacing and quiet the residual row, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: restore the original page rhythm and keep Everything else at normal weight even when selected. The page may follow normal document flow beyond a short viewport; only the grid and tooltip must avoid internal vertical scrolling.

What changed: Task 5 removes the temporary stream-specific width, padding, headline and spacing compression. The original desktop focus-padding rule and 25rem initial chart reservation remain. Selected residual rows keep opacity 1 and weight 400 while named artists retain weight 700. The existing hover reader now checks internal grid/panel scrolling only, with diagnostic wording matching that scope; row containment, focus clearance and clipping assertions remain. DESIGN.md follows the restored page flow and residual emphasis. The original design spec links to the follow-up design for the current scrolling contract.

Deviations: the owner superseded the earlier whole-page no-scroll constraint during live review. The gate's document-height rejection is therefore removed intentionally, with no weakening of internal containment. The reviewer-approved diagnostic correction changes "chart, panel or page" to "chart or panel". No new unit test is added for this reversible styling slice; existing full-suite and computed-style browser evidence validate it. The whole 58-check browser gate runs at the integrated Task 7 head per the follow-up plan.

Existing tests edited: none under tests/. Independent Task 5 code review approved the correction; source probe red had 8 failures (compressed 4px gaps, selected residual weight 700) and green had 8 passes across Chromium/Firefox at four desktop sizes (original gaps 40/20/20/24/16px, residual weight 400, 16 rows with zero outside/internal-scroll failures). The fresh locked landing probe passed the same 8 cases on actual u7 source. All three full-suite shards passed: 702 + 1503 + 912. No whole-gate success is claimed for this individual slice.

Validation: `pytest -q` -- **3117 passed**.

Forward guidance: land Tasks 6 and 7 independently, then run the integrated browser gate and refresh the private real-data preview. Owner prototype approval remains pending; no main integration or PR publication yet.
