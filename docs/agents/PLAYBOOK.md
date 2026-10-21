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

### 2026-10-21 - The statistics tests pin the sentences and the UTC day

Side task, no batch tag: make the listening statistics tests fail on a false population sentence, a system-zone date and an unsorted best day, on `refactor/statistics-module`, a branch off `main`.

Owner intent: tests assert intended behaviour, not the code as written, so a wrong module must not pass them.

What changed: in `tests/test_listening_stats.py` the album population test now asserts both published sentences whole (before, rewording the matched sentence to "include-unmatched are counted", or dropping only "(unmatched)", still passed because the word also sits in "include-unmatched"; swapping the two sentences failed only the distinctness check), and the heatmap population test asserts all four sentences whole instead of "not blank and distinct". A new `TestUtcDate` test gives `utc_date` a datetime subclass whose `astimezone()` with no argument answers in Tokyo, so a conversion that uses the host zone returns 2 March instead of 1 March on any host; a UTC host (CI) hid that defect before, since the system zone there is UTC. It does not use `time.tzset`. A new `TestBestDay` test lists the later tied day first, so dropping `sorted()` returns the later day. Mutations (copy-aside, module restored): rewording, dropping "(unmatched)", swapping the album sentences, swapping two heatmap sentences, `astimezone()` with no argument (also with `TZ=UTC0`) and dropping `sorted()` each fail one or more tests; restored, 33 pass. The 24-row mutation table of Task 2 was not re-run: no test it relies on was weakened, the two edited tests only got stricter.

Deviations: none. Edited existing tests: `TestHeatmapStatistics::test_every_figure_states_its_population` and `TestAlbumPlayStatistics::test_each_figure_says_what_it_leaves_out`.

Validation: `pytest -q` -- **2890 passed**.

### 2026-10-21 - The two-quiet-days KPI case catches a lenient streak

Side task, no batch tag: make the shared KPI fixture's two-quiet-days case fail a lenient streak, on `refactor/statistics-module`, a branch off `main`.

Owner intent: a test must fail when the rule it names is broken, so the streak case cannot pass for a port that forgives two quiet days.

What changed: in `tests/fixtures/heatmap_kpi_cases.json` the case `two_quiet_days_make_the_streak_zero` gains a play at day offset 2 (days 0 and 1 stay empty). Before, the only play sat at offset 5, so a streak that ended two days back still found nothing and returned 0; now it finds the offset-2 play and returns 1, and the case fails. The expected values were measured with the JS harness on unchanged `heatmap.js` (scrobbles 5, best day MAR 5 with 4, streak 0). Planting "forgive two quiet days" in `heatmap.js` failed the JS case; the same plant in `scrobblescope/listening_stats.py` failed the Python case. The test-seam comment in `static/js/heatmap.js` called the hooked functions side-effect free, but `renderKpisInto` sets `kpiRow`; it now says they touch only the row they are handed. No empty-window case is added: the JS and Python empty-window outputs differ and that choice belongs to Task 4.

Deviations: none. Edited existing tests: `test_kpi_blocks_show_what_the_window_holds[two_quiet_days_make_the_streak_zero]` and `test_the_published_figures_are_the_ones_the_pinned_kpis_show[two_quiet_days_make_the_streak_zero]` (data only).

Validation: `pytest -q` -- **2888 passed**.

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
