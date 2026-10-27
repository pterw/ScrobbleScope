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

### 2026-10-27 - State the real total of a capped unmatched group

Side task, no batch tag: UI audit v6 row 9, a capped unmatched group states its real total, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (ruling U12, which supersedes U4): a group that shows fewer albums than it holds says so, "Showing the first 500 of N", with N the real total and no hard-coded 500. `group_unmatched_albums_with_totals` in `scrobblescope/unmatched.py` returns the groups, counts, metadata and a `totals` dict holding only the groups that show fewer than they hold; the total is the pre-slice length, and for the below-threshold group the larger of that and the `albums_below_threshold` stat, which `plays.select_albums` takes before its exclusion cap and which already reaches `progress.stats`, so the orchestrator is unchanged. `group_unmatched_albums` keeps its 3-tuple by delegating. `_render_unmatched_page` in `scrobblescope/routes/album_flow.py` passes `reason_totals`; `templates/unmatched.html` prints the line as a muted `text-xs` note under the group table, above the expander row. No new CSS and no new colour pairing (same muted token and surface as the group's other secondary text). Provisional wording until the impeccable pass; no real-data browser check was done.

Deviations: review finding R12-F1 was fixed at landing: the route test gained a case where the capped group is not the below-threshold group (520 no-match albums), so a template that looked the total up with a fixed `below_threshold` key fails.

Existing tests edited, by name: none; `test_unmatched_view_states_the_real_total_of_a_capped_group` (route, three cases) and the parametrized grouping-totals test in `tests/test_unmatched.py` are new.

Validation: `pytest -q` -- **2986 passed**.

### 2026-10-27 - Drop ellipses from progress and toast messages

Side task, no batch tag: UI audit v6 row 6, no ellipses in progress and toast copy, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: README row 6, no ellipses in the live status copy. Ruling U10 widened it from the loading page to the server's progress messages (`scrobblescope/orchestrator/`, `heatmap.py`, `jobs.py`) and the client strings in `static/js/` (`loading-progress.js`, `loading.js`, `heatmap.js`, `results.js`), including the escaped ellipses in `loading.js`: "Retrying" and "Opening the results page". "Initializing..." (and "Initializing heatmap...") became "Connecting to Last.fm" at all seven sites, the template's first phase line, `jobs._initial_progress`, both fallbacks in `loading-progress.js` and the heatmap start; the leaderboard toast reads "Creating leaderboard image". The pins in `scripts/dev/_frontend_gate_pipeline.py` follow the new strings. Remaining `...` in the tree are docstrings and comments only.

Deviations: none from the rulings. `tests/test_routes.py` is untouched: its "Working..." and "Fetching page 3..." are fixture strings passed to `jobs.advance`, not production copy. The `jobs.start` test uses the arbitrary message "Starting" instead of "Initializing heatmap...".

Existing tests edited, by name: `test_create_returns_unique_ids_and_a_pristine_job` and `test_reset_returns_the_job_to_its_initial_state_and_keeps_params` in `tests/test_jobs.py`, `test_start_clears_stats_phase_and_error_and_sets_the_message` (message string), `test_progress_callback_sends_correct_percentages` and the other `TestFetchAndProcessHeatmap` message asserts in `tests/test_heatmap.py`, `test_fetch_and_process_passes_progress_cb_to_lastfm` in `tests/services/test_orchestrator_fetch_and_process.py`, `test_fetch_spotify_misses_reports_search_progress`, `test_fetch_spotify_misses_reports_batch_progress` and `test_deezer_fallback_reports_progress_inside_its_band` in `tests/services/test_orchestrator_fetch_spotify.py` (full-message equality), and `test_a_failed_run_with_no_retry_still_says_the_results_page_opens` in `tests/frontend/test_heatmap_pure_functions.py`.

Validation: `pytest -q` -- **2978 passed**.

### 2026-10-27 - Rewrite the unmatched page headline and threshold header

Side task, no batch tag: UI audit v6 row 5, the unmatched page headline, subtitle, group description and threshold column header, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: the unmatched page headline says what happened to the albums (ruling U13): "Albums left out of <user>'s results" when nothing is listed, "Unmatched albums in <user>'s results" when an Include unmatched run lists some (`listed_count` > 0), deciding "listed" from result rows, not reason codes. The subtitle is the year and the total, "<year> middle dot <n> albums, grouped by reason" ("album" for 1), in both cases, so the listed / left-out clause and its `left_out` arithmetic are gone; `.unmatched-total` stays as a styling hook. The "Not enough listening" group's count header reads "Plays/trk" on phones and "Plays middle dot tracks" from 768px up, one line each (rulings U15 and U17), with `aria-label="Plays and tracks"` on the `th` so a screen reader never reads "trk"; the two forms are sibling spans toggled by a plain `min-width: 768px` media query in `static/css/unmatched.css` (no Chromium-only CSS), and the column widens at 768px and up for that panel only, while the phone width is unchanged so the album-title floors in the frontend gate hold. Its description drops the year and singularises: "Below N play(s) or M unique track(s)." (ruling U16). Other groups' header stays "Plays".

Deviations: none from the rulings. Measured in Firefox and Chromium at 320, 390, 768, 1024, 1440 and 1920px: the header is one line and not clipped at every width; the album title is 414px at 768 (U15's 454 was the narrower column's figure). Nothing durable pins the 768px swap or the nowrap, only the scratch probe; a gate check belongs with the later accessibility PR. `docs/design/RECONCILIATION.md` (verbatim snapshot) still describes the old count line.

Existing tests edited, by name: `test_unmatched_view_names_track_counts_only_on_the_threshold_panel` (parametrized to (10, 3) and (1, 1); header spans, aria-label, other panels' "Plays", description text); `test_unmatched_page_count_line_names_listed_and_left_out`, renamed `test_unmatched_page_headline_and_subtitle_follow_listed_count` and now asserting both h1 forms and the subtitle across listed, left-out, show-limit and one-album cases; `test_unmatched_view_subtitle_counts_the_albums_left_out`, renamed `test_unmatched_view_filter_bar_states_the_run_settings` (its subtitle assertion and parametrize dropped as covered by the headline test; filter-bar assertions kept).

Validation: `pytest -q` -- **2978 passed**.

### 2026-10-27 - Name the user and year in the results headline

Side task, no batch tag: UI audit v6 row 4, the results headline names the user and the run's year, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent: the results h1 reads "<user>'s top albums of <year>", with the username keeping its accent span and `year` being the run's own year, never the current one. The subtitle `#results-ranking-subtitle` drops the year (ruling U11) and names the source: "Last.fm", a middle dot, then "Ranked by play count" or "Ranked by listening time". `setLeaderboardMetric` in `static/js/results.js` writes the same string on a sort change, so a sort switch and a fresh load agree. This wording is provisional until the impeccable pass. The old phrase "Top Last.fm albums for" appeared only in `templates/results.html`; no `<title>` or meta text repeated it. Deviations: `scripts/dev/results_behavior_tests.py` is touched beyond the brief (review finding R4-F1) so the sort check also covers the subtitle text, which the Python route test cannot see.

Existing tests edited, by name: `test_sort_updates_order_ranks_metrics_and_accessibility` in `scripts/dev/results_behavior_tests.py` (its fixture gains the subtitle element and each sort case asserts the subtitle text); one new parametrized test, `test_results_headline_names_user_and_year_and_subtitle_names_source` in `tests/test_routes.py`.

Validation: `pytest -q` -- **2978 passed**.
