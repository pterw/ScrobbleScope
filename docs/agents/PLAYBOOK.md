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
  module is done (PR #3, branch refactor/album-request-module, plan
  `docs/superpowers/plans/2026-10-20-album-request-module.md`); normalized
  Last.fm scrobbles with one album aggregate is done (PR #4, branch
  refactor/lastfm-scrobbles, plan
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); the other two
  seams remain, one album-metadata encoding and the statistics module. Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #7, UI consistency, is under way on `feat/ui-consistency`; round 1's
  plan is `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`.
  PR #6, the statistics module, is under way on
  `refactor/statistics-module`; its plan is
  `docs/superpowers/plans/2026-10-20-statistics-module.md`.
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

### 2026-10-21 - The window declaration drops two heatmap.js sites

Side task, no batch tag: retire two docsync value sites that name `static/js/heatmap.js`'s window code, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the 365-day window declaration must stop guarding text that the next commit deletes, so the statistics move is not blocked by a stale pattern (seam B-4).

What changed: `config/docsync.toml` loses the `WINDOW_DAYS = (\d+)` site and the `whole (\d+)-day window` site, both in `static/js/heatmap.js`. Task 4 removes that text because the browser stops dividing by a window length; the average now divides by the zero-filled window in Python. A declaration whose pattern no longer matches fails DOC009, so the sites go first, in their own commit. The Python constant (`HEATMAP_WINDOW_DAYS`), the exported caption (`LAST (\d+) DAYS`) and all copy sites stay guarded. A staged `config/docsync.toml` change outside `[test_count]` is control-plane, so the commit used the documented escape: `--check` exit 0, `SKIP=doc-state-sync-check git commit`, `--check` again. Never `--no-verify`.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2888 passed**.

### 2026-10-21 - Listening statistics have one module

Side task, no batch tag: the pure listening statistics module and its tests, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the streak, best-day, average and plays figures get one home with ordinary pytest coverage and a stated population each (seam B-4), before the heatmap and the Results page are wired to it.

What changed: `scrobblescope/listening_stats.py` (new, standard library only, no clock, no I/O) holds `utc_date` (refuses a naive datetime), `current_streak`, `best_day`, `daily_average`, `heatmap_statistics` and `album_play_statistics`; the two aggregates return `{name: {"value", "population"}}`. UTC is by construction: day keys are the ISO dates the pipeline already attributed in UTC and `today` is passed in. `tests/test_listening_stats.py` (new, 31 tests) covers each rule and runs the eight pinned KPI cases from `tests/fixtures/heatmap_kpi_cases.json` through `heatmap_statistics`, so the Python rules match what readers saw. Nothing imports the module yet; the heatmap and the Results page move onto it in the next commits. `.claude/SESSION_CONTEXT.md` Sections 3 and 4 list the module.

Mutation evidence, each planted in a scratch copy of the module and restored: 24 planted defects (local-day `utc_date`, naive datetime accepted, no yesterday step, two quiet days forgiven, `streak + 1`, a missing day read as a play, indexing instead of `.get`, last-day and `>=` best day, a zero best day, unguarded empty mapping, average over play days, rounded average, no empty guard, streak anchored on the first day, a blank and a shared population, a `"None"` date, `plays_matched` ignoring unmatched rows or minus a fixed 1, `rows[0]`, indexed `play_count`, identical populations) each failed the test the plan names for it. One planted defect was too weak: removing only the parenthesised `(unmatched)` from the matched population still passed, because the sentence also says `include-unmatched`; removing the whole unmatched clause fails `test_each_figure_says_what_it_leaves_out`.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2888 passed**.

### 2026-10-21 - The heatmap KPIs and the Scrobbles figure are pinned before they move

Side task, no batch tag: parity tests for the heatmap KPI blocks and the Results Scrobbles figure, on `refactor/statistics-module`, a branch off `main`.

Owner intent: a refactor starts from parity tests, so the next two commits can move the streak, best-day, average and Scrobbles rules out of the browser and Jinja provably unchanged (seam B-4).

What changed: `tests/fixtures/heatmap_kpi_cases.json` holds eight 365-day windows ending 2026-03-10 (streak ends today, streak may end yesterday, a gap ends it, two quiet days make it zero, a tie for best day goes to the earlier day, the average is over every day, one decimal with a thousands separator, a streak stops at the window's first day), each with the KPI text worked out by hand. `tests/helpers.py` gains `load_kpi_cases`, `kpi_window`, `kpi_payload` and `expected_kpi_blocks`. `static/js/heatmap.js` gains the test-seam hook `renderKpisInto(row, data)`, present only when `window.__scrobbleHeatmapTestMode` is set, so a real page is unchanged. `tests/frontend/test_heatmap_pure_functions.py` runs each case through it (8 tests). `tests/test_routes.py` gains two tests: Scrobbles is the plays of every album the page lists (120 matched, 200 with unmatched rows), and a playtime ranking leaves out an album with no listening time (50). SESSION_CONTEXT Section 6 names the new fixture.

Mutation evidence, each planted in the working file and restored: `while (dailyCounts[isoDate(d)])` to `while (false)` failed `streak_ends_today`, `streak_may_end_yesterday`, `a_gap_ends_the_streak`, `average_is_over_every_day_of_the_window`, `average_shows_one_decimal_and_thousands_separator` and `a_streak_stops_at_the_first_day_of_the_window`; `>=` to `>` in the best-day reduce failed `a_tie_for_best_day_goes_to_the_earlier_day`, `average_is_over_every_day_of_the_window` and `a_streak_stops_at_the_first_day_of_the_window`; `sum(attribute='play_count')` to `sum(attribute='play_time_seconds')` in `results.html` failed both route tests.

Deviations: none. Edited existing tests: none (the module docstring of `tests/frontend/test_heatmap_pure_functions.py` changed, no test).

Validation: `pytest -q` -- **2857 passed**.

### 2026-10-21 - The statistics module plan opens its branch

Side task, no batch tag: the approved statistics module plan, committed as the branch's first commit, on `refactor/statistics-module`, a branch off `main`.

Owner intent: "All plans should stay for archival purposes" (2026-10-20), so every PR's plan is its branch's first commit.

What changed: `docs/superpowers/plans/2026-10-20-statistics-module.md` is added (six tasks: pin the heatmap KPIs and the Scrobbles figure, the pure `listening_stats` module, retire two docsync sites, publish the heatmap statistics, compute the Scrobbles figure in Python, amend WP-6). PLAYBOOK Section 3's "Before WP-1" bullet gains one sentence naming PR #6, its branch and the plan. The plan passed the brief review (`plan-review.md`), two fix rounds and two re-reviews (`plan-rereview-1.md`, `plan-rereview-2.md`; approved); owner Q1 is approved ("Yes, that sounds good."): the Scrobbles figure is computed at render time in the Results route. It was then drift-reviewed against `eb0db9e` (`main` after PRs #256-#260) and the fixes were folded in as its Revision 3. Structural: S1, the publication test in Task 4 Step 1 now patches `fetch_scrobbles` and uses `_fetch`, `_play` and `UTC` (the page-layer patch target and helpers are gone); S2, Task 5 Step 3 builds the `include_run` span from the rows rendered, so `test_hiding_every_row_clears_the_top_artist_and_including_restores_it` keeps passing; S3, `scripts/dev/_frontend_gate_figures.py` (`_HEATMAP_RESULT`) joins Task 4's Touches, Step 5 and the Section 4 line, making eight gate payloads, not seven. Renames (7): `plays.aggregate_daily_counts`, `_play`/`_fetch`, `fetch_scrobbles`, `UTC` for `timezone.utc` in Task 2, the `heatmap` docstring dependency line, the SESSION_CONTEXT current-text quotes, and the `listening_stats` docstring wording. Cosmetic (9, C1-C9; C3 and C7 needed no change): helper imports, the `HEATMAP_WINDOW_DAYS` comment, the `class` line, the sequence-diagram anchor, Hide/Include wording, entry headings take the commit date, Task 6's moot conflict note, and one `_context_view` sentence for Task 4's commit body. The "unverified until #4 merges" rows of the PR #4 table are rewritten as checked.

Deviations: the drift review said `test_utc_midnight_decides...` has three `timezone.utc` uses; the plan has two (`NEW_YORK` is a fixed offset), so two were changed. No DOC citation error needed a wording change in the plan. Edited existing tests: none.

Validation: `pytest -q` -- **2847 passed**.
