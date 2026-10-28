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

### 2026-10-28 - Restore stream result spacing and quiet the residual row

Side task, no batch tag: restore stream result spacing and quiet the residual row, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: restore the original page rhythm and keep Everything else at normal weight even when selected. The page may follow normal document flow beyond a short viewport; only the grid and tooltip must avoid internal vertical scrolling.

What changed: Task 5 removes the temporary stream-specific width, padding, headline and spacing compression. The original desktop focus-padding rule and 25rem initial chart reservation remain. Selected residual rows keep opacity 1 and weight 400 while named artists retain weight 700. The existing hover reader now checks internal grid/panel scrolling only, with diagnostic wording matching that scope; row containment, focus clearance and clipping assertions remain. DESIGN.md follows the restored page flow and residual emphasis. The original design spec links to the follow-up design for the current scrolling contract.

Deviations: the owner superseded the earlier whole-page no-scroll constraint during live review. The gate's document-height rejection is therefore removed intentionally, with no weakening of internal containment. The reviewer-approved diagnostic correction changes "chart, panel or page" to "chart or panel". No new unit test is added for this reversible styling slice; existing full-suite and computed-style browser evidence validate it. The whole 58-check browser gate runs at the integrated Task 7 head per the follow-up plan.

Existing tests edited: none under tests/. Independent Task 5 code review approved the correction; source probe red had 8 failures (compressed 4px gaps, selected residual weight 700) and green had 8 passes across Chromium/Firefox at four desktop sizes (original gaps 40/20/20/24/16px, residual weight 400, 16 rows with zero outside/internal-scroll failures). The fresh locked landing probe passed the same 8 cases on actual u7 source. All three full-suite shards passed: 702 + 1503 + 912. No whole-gate success is claimed for this individual slice.

Validation: `pytest -q` -- **3117 passed**.

Forward guidance: land Tasks 6 and 7 independently, then run the integrated browser gate and refresh the private real-data preview. Owner prototype approval remains pending; no main integration or PR publication yet.

### 2026-10-28 - Plan the streamgraph live-review corrections

Side task, no batch tag: record the owner-directed prototype corrections, on
`feat/streamgraph-bursts`, a branch off `main`. Original Tasks 1-4 are committed.
The owner requested restored header spacing, normal-weight residual text,
symmetric residual caps and clearer burst colours, with parallel implementation.
The follow-up plan slices spacing, proportional geometry and palette into separate
atomic commits and keeps updated live review before PR publication. Document flow
is restored; the chart and tooltip retain their internal no-scroll constraint.
No application code changes. Tests edited: none. Plan vs implementation: planning
only; no code step is marked complete. Forward guidance: execute Tasks 5-7 in
parallel code worktrees, review and land serially, then refresh the private preview.

Validation: `pytest -q` -- **3117 passed**.

### 2026-10-28 - Verify weekly hidden artists in the browser gate

Side task, no batch tag: verify weekly hidden artists in the browser gate, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: preserve the twelve-layer stream, conditional aligned hidden rows and keyboard access, with the tallest desktop panel visible without vertical scrolling.

What changed: Task 4 seeds twelve artists, including two sparse bursts over weeks 5-7, and Hidden A/B/C in every third week as part of Everything else's count. One new registered check proves exact names, counts, sibling order, one conditional rule and name-column alignment as the pointer changes weeks. Existing hover checks include hidden rows and reject chart, panel or document vertical scrolling; the existing keyboard check now challenges a retained dense cursor after sparse pointer activity. The job fixture still flows through the real job store. No application, template, JS or CSS changed in this task, so product documentation remains true.

Deviations: the existing keyboard and no-scroll assertions were extended to hold the approved Task 3 corrections, with no helper, second check, dependency, schema or weaker assertion. The intentional hidden-block removal failed the new check with zero rules and empty rows; the saved original text was restored before green. Sparse-keyboard, laptop overflow and the intermediate focus-padding source-order regression found during stack validation were corrected in Task 3, not this gate commit. The controller's final code-phase gate and the fresh landing frontend gate each passed 58 checks in 89 runs; independent source/runtime review approved the patch. Fresh suite shards passed 702 + 1503 + 912 cases.

Existing tests edited: none under tests/. Browser checks extended: `check_stream_hover_shows_panel_and_ring` through its shared hover assertions, and `check_stream_is_one_keyboard_tab_stop`; new check: `check_stream_panel_rule_and_hidden_rows_follow_the_week`.

Validation: `pytest -q` -- **3117 passed**.

Forward guidance: the owner has not approved the Firefox prototype. Follow up in a separate small slice on Everything else bolding and burst emphasis; the controller is clarifying whether emphasis applies to the full burst-artist ribbon or its winning 21-day segment. This checkpoint preserves the reviewed gate/source stack. Task 0 sign-off, final integration and PR publication remain pending.

### 2026-10-28 - List hidden artists in the stream tooltip

Side task, no batch tag: list hidden artists in the stream tooltip, on `feat/streamgraph-bursts`, a branch off `main`.

Owner intent: name the largest artists still pooled each week without indentation, use a divider only when those rows exist, retain twelve named layers (top ten plus two rolling three-week bursts), and fit the desktop chart without vertical scrolling.

What changed: Task 3 validates optional hidden entries, exposes the selected week's list in the panel model, and renders a conditional rule plus up to three aligned text rows with blank swatch spacers. README and DESIGN.md follow the new UI. Sparse burst weeks now use their visible rows for keyboard selection, including retained-cursor and pointer-to-key transitions. The desktop result reserves chart room at initial render and fits its width, spacing and headline to viewport height.

Deviations: the owner selected existing `--stream-muted` for the divider (5.53:1 light, 5.05:1 dark), replacing the planned low-contrast token. The same-file keyboard and desktop height-budget corrections were required by the final sparse fixture and approved independently. A code-phase CSS order edit briefly let the base 4px grid padding override the existing 8px desktop focus-ring room; the final-stack gate caught clipping, and the existing desktop rule was restored after the base rule without weakening the gate. The controller-approved documentation scope also reconciles the active spec with the divider/layout decisions and clarifies that burst layers keep their full weekly history, with zero counts only in weeks without plays; DESIGN.md now describes only visible layer rows. No selection code changed. No new helper, token, dependency, schema or extra test family was added. The Task 0 named-artist guarantee is replaced with independent measured top-ten plus rolling 21-day peak verification: current outside-top-ten peaks are Slayyyter 134, Magdalena Bay 120 and Cameron Winter 115; Four Tet holds the tenth slot at 271 total, one above Magdalena Bay's 270. The owner reaffirmed the ranking rule; no artist is hardcoded and the dated handoff remains historical.

Existing tests edited: `test_stream_payload_valid`; `test_panel_model_hidden_artists_for_the_week` adds the planned three parametrized model cases. Code-phase red: 7 failed, 19 passed; focused green: 26 passed. Fresh landing focused checks: 26 passed, 120 deselected; whole file: 146 passed. Independent hidden-row, keyboard follow-up and layout reviews approved the scoped source. The controller's final full-stack browser gate passed 58 checks in 89 runs after the focus-room correction; both browsers also passed the eight focused desktop sizes. Fresh final-source suite shards all passed; landing validation follows below.

Validation: `pytest -q` -- **3117 passed**.

Forward guidance: land Task 4's browser proof next, then complete the real-data Firefox prototype. Its owner sign-off still precedes PR publication; Task 0 sign-off remains pending.
