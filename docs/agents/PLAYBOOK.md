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

### 2026-10-25 - UI round 2 backlog: AGENTS.md lean-suite rules

Side task, no batch tag: add the owner's lean-suite rule to AGENTS.md "Test Quality Rules", on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA20): "test for *intended function*, not *written function* and avoid repeatedly testing the same behaviour". The section gains a short "Lean suite" list: one test per intended behaviour, near-duplicates become one parametrized test, no test that pins wording or a constant equal to the code, module-layout ("parity") tests are not added (the gate family was removed on 2026-10-25 with the owner's approval), and a fix round extends an existing test before adding one. The existing "Near-duplicate" forbidden pattern is not repeated. No other section changed.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - UI round 2 backlog: plan A execution record

Side task, no batch tag: record in plan A (`docs/superpowers/plans/2026-10-25-ui-round-2-backlog.md`) which tasks landed, in which commits and with which deviations, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: "Make sure that the plans are being followed and marking where they are finished when things arrive and deviations." The plan's acceptance boxes are ticked for Tasks 1-11 (Task 11b has none), each backed by its land report and an approving review; Task 12 stays open. The plan gains an "Execution record (2026-10-25)" section: a table of task, commit, review rounds and deviation ruling ids (RA6-RA21), plus the landing-order changes (RA9, RA10), the `short_window` interface extension (RA11), Task 10's two edits outside its Touches, the owner copy (RA13), F-B23-46 resolved and F-B23-64 filed, the lean-suite consolidation (RA20, 3067 to 2876 tests) and what still has to run (Task 12, the final gates). Docs only; the plan is a point-in-time record, so no live prose changed.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - UI round 2 backlog: test consolidation, gate unit tests

Side task, no batch tag: merge duplicate and near-duplicate tests in the four frontend-gate unit-test files (`test_frontend_gate_colour.py`, `_forms.py`, `_include.py`, `_layout.py`), on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA20): "test for *intended function*, not *written function* and avoid repeatedly testing the same behaviour"; "Keep things cheap and narrow". Colour: the seven "Carried from test_frontend_gate.py" duplicates (parse_rgb_string, composite_over, contrast_ratio symmetry, worst divider contrast, the 3:1 boundary, the divider token name, clamp_px) are removed, each verified against its surviving class test (`TestParseRgbString`, `TestCompositeOver`, `TestContrastRatio`, `TestWorstDividerContrast`, `TestDividerContrastFailure`, `TestClampPx`); 2.9999 became a case of `test_reports_below_the_threshold`. `test_seg_boundary_at_the_floor_passes_in_both_themes` is removed (`test_selected_text_floor_stays_4_5` and the other-theme half of the under-4.5 cases guard it); the 3.5 case is merged into the renamed `test_seg_boundary_under_4_5_fails_in_the_themes_that_miss_it`; the two unselected-floor tests are one parametrized `test_unselected_text_floor_is_7_to_1_by_default_and_selected_text_keeps_4_5`. The luminance test keeps only the ordering claim. Forms: the mode-switch failure test keeps both state labels and the figure; `test_include_check_runs_the_mode_switch_measure` is now `test_include_check_reports_what_the_mode_switch_measure_finds` and asserts a stubbed failure reaches the returned list (it fails if the `mode_switch_failures` call is removed). Include: the at-the-floor and 4.63 pass tests are removed (each just-under case asserts the other theme passes); the 3.5 case is merged into the renamed `test_card_boundary_under_4_5_fails_in_the_themes_that_miss_it`, keeping the "against the card" fragment. Layout: `test_collapsed_form_keeps_the_full_lift_and_a_shorter_lift_fails` is removed (the form-centring tests guard the same rule); the short-window pair, the 1920x700 and 1920x1063 large-display pair, the strip pass pair and fail pair, and the 879 and 892 loops are parametrized (each case still fails if its own viewport or cell is dropped); the 860 pair is `test_strip_display_follows_the_860_cut`; the sweep test is `test_strip_sweep_reaches_the_widths_below_the_860_cut` and asserts the four sub-860 lines without an event log; the decade-scope test asserts only the reach state.

Deviations: the sweep test no longer asserts the per-width fresh page load order. Two Minor review notes accepted under RA20, no change: the default token (`--shell-border`) of `_divider_contrast_failure` is no longer asserted, and "every width at or above 860 is measured" is no longer guarded. Edited existing tests: those named above.

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - UI round 2 backlog: test consolidation, orchestrator and loading tests

Side task, no batch tag: merge near-duplicate orchestrator loading-stats tests and heatmap loading tests into parametrized tests, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA20): "avoid repeatedly testing the same behaviour"; "Keep things cheap and narrow". Four loading-stats tests in `tests/services/test_orchestrator_process_albums.py` differed only in inputs, so `test_loading_stats_split_the_passed_albums_into_hits_and_misses` now runs them as four cases (mixed, unmatched_miss, all_cached, database_unavailable); `db_cache_enabled` is asserted equal to the database availability in each case, so the database-less case is the only False one. In `tests/frontend/test_heatmap_pure_functions.py`, the two export-header tests are two cases (uppercase, no text-transform) of `test_export_header_model_uppercases_only_when_the_css_says_to`, and `test_each_loading_stat_tile_shows_its_own_figure_and_only_when_sent` runs its two payloads (both_keys, to_search_absent) as two cases. Every case is kept.

Deviations: none. Edited existing tests: the four `test_loading_stats_*` tests in `test_orchestrator_process_albums.py` (one kept as the parametrized test, three merged into it), `test_export_header_model_uppercases_only_when_the_css_says_to` (parametrized, absorbing `test_export_header_model_leaves_text_as_written_without_text_transform`) and `test_each_loading_stat_tile_shows_its_own_figure_and_only_when_sent` (parametrized).

Validation: `pytest -q` -- **2873 passed**.
