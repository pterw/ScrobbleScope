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
  #269, draft). Their documentation, the gates that hold them and the
  F-B23-46 ranking rule follow the plan
  `docs/superpowers/plans/2026-10-25-ui-round-2-backlog.md` on the same
  branch. The album-matching, cache re-verification and MusicBrainz fixes the
  session found go to a PR stacked on it (branch `fix/album-matching`, which
  carries its own plan). The documentation refresh merges last.
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

### 2026-10-25 - UI round 2 backlog: gate the mode switch

Side task, no batch tag: gate the index mode switch like the segmented controls, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA1, "Keep muted, gate at 4.5"): keep the muted unselected label on the mode switch and hold it at 4.5:1 while the other segmented controls stay at 7:1. `seg_contrast_failures` and `seg_hover_failures` in `scripts/dev/_frontend_gate_colour.py` take an optional `unselected_floor` spec key (default `SEG_TEXT_FLOOR`, 7.0) that replaces the floor for the unselected option text and the unselected-hover cell only. `scripts/dev/_frontend_gate_forms.py` adds `MODE_SWITCH_SEG` and `mode_switch_failures`, called from `check_include_unmatched_control`: it measures Top albums selected and Heatmap selected (a real click on `#mode-tab-heatmap`, restored to Top albums in a `finally`) in both themes, covering option text, selected text, chip boundary and both hover cells.

Deviations: the measure hangs off `check_include_unmatched_control` because `frontend_gate.py` is outside the task's files. Review fix round (RA16): added a stub-page test that the include check runs the mode-switch measure, tests for the hover measure, the selected-chip hover row and the selected-chip hover floor staying at the default, and a restore-on-error test. No test that predates this task is edited. Of this task's own first-phase tests, `test_mode_switch_failures_restore_top_albums_and_keep_light_clear` gains `assert failures` and `test_mode_switch_spec_holds_only_the_unselected_cell_at_4_5`, added by this task's own first phase, was removed (RA16 (f): it pinned a constant equal to the code).

Validation: `pytest -q` -- **3060 passed**.

### 2026-10-25 - UI round 2 backlog: gate the hero strip

Side task, no batch tag: gate the hero strip's layout, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: keep the strip from regressing after the container-query fix. `scripts/dev/_frontend_gate_layout.py` gains `STRIP_ROW_QUERY_EM` (26, mirroring `@container (width < 26em)`), `_measure_strip` and the pure `_strip_layout_failures`, called from `_check_desktop_scale_bounds` beside the headline-wrap check for both modes at 900, 1100, 1200, 1500, 1920 and 2560 (900px height): three columns or stacked rows by 26 x the strip wrap's computed font size, and no wrapped term (height over 1.2 x line height). At 859 and 390 the lists must be hidden. The helper fails closed on a thin measurement (fewer than three items, or no measurable term or line height), and the sweep is pinned to its widths and 900px height by a test. The strip had no gate: the columns/rows switch is a container query and the mobile cut a viewport rule, and terms wrapped unnoticed up to 1179px. The 859/390 failures report under the `[desktop]` profile label because the sweep runs inside the desktop check (RA15, accepted).

Deviations: none. Edited existing test: `test_desktop_scale_bounds_reports_wrapped_headlines_and_closes_context` (its stub now serves a strip measure and its expected failure list gains the strip line, so removing the strip call fails it).

Validation: `pytest -q` -- **3047 passed**.

### 2026-10-25 - UI round 2 backlog: hidden-count note

Side task, no batch tag: show how many albums listening-time ranking leaves out (F-B23-46, client half of the note), on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (R6, RA3): a listener who ranks by listening time should see why albums vanish and how to get them back. `templates/results.html` gains `#playtime-hidden-note` (hidden by default, with `#playtime-hidden-count` and `#playtime-hidden-copy`) after the stat grid, reusing the existing partial-notice style, so nothing moves on load. `applyRowState` in `static/js/results.js` now counts the rows the rule drops, excluding rows Hide already hides, and shows or hides the note with that count; the toast on switching to listening time gains the count when it is above 0. Copy is the owner's choice (RA13, "Count first"): note "N albums with no listening time are hidden. Rank by track plays to show them." (N = 1: "1 album with no listening time is hidden. Rank by track plays to show it."); toast "Leaderboard ranked by Spotify listening time. N albums with no listening time are hidden." (N = 1: "1 album with no listening time is hidden."); with N = 0 and on plays the toast is the existing sentence alone, with one singular/plural switch in `results.js`. New tests in `scripts/dev/results_behavior_tests.py` read the integer and the `hidden` state, never the wording: the count and toast for two durationless rows, the plain path with none, Hide-hidden rows not counted, and the live Hide path refreshing the note at N = 0 and N = 1 (RA14). F-B23-46 stays open: the server half that renders the note on a run started in playtime mode is T10's, and T11b closes it.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **3026 passed**.

### 2026-10-25 - UI round 2 backlog: client listening-time rule

Side task, no batch tag: client half of the listening-time rule (F-B23-46), on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (R6): ranking the Results page by listening time drops albums with no listening time and renumbers the rest, and ranking by track plays brings them back. `applyRowState` in `static/js/results.js` now sets each row's hidden state as one decision (Hide on an unmatched row, or listening-time ranking on a row whose `data-play-time-seconds` is not above 0), clears `data-rank` and the rank cell of hidden rows, and renumbers the rest 1..n; `setLeaderboardMetric` and `setUnmatchedHidden` both call it, so a metric switch never reveals what Hide hides and never hides what Hide shows. The header figures count rows not hidden by Hide, so Total Albums, Top artist and Scrobbles still describe the whole result (RA3). The CSV exporter already skips hidden rows, so it lists only the ranked rows. New tests in `scripts/dev/results_behavior_tests.py` cover the drop and restore, the Hide round trip, the CSV and the header figures. This does not close F-B23-46: the server half (T10) and the hidden-count note (T7b) follow, and the toast text is unchanged here.

Deviations: none. Edited existing test: `test_sort_updates_order_ranks_metrics_and_accessibility` (the durationless row "C" is now hidden and unranked in listening time, visible ranks `["1","2"]`, back at rank 3 on plays).

Validation: `pytest -q` -- **3026 passed**.
