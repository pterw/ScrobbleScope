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

### 2026-10-25 - UI round 2 backlog: test consolidation, results browser tests

Side task, no batch tag: merge repeated tests in `scripts/dev/results_behavior_tests.py`, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA20): "test for *intended function*, not *written function* and avoid repeatedly testing the same behaviour". Three tests drove the same untimed-and-not-unmatched hidden-note counter through different Hide and ranking orders; they are now three cases of one subTest test, `test_hidden_note_counts_only_rows_the_ranking_alone_drops`, so both callers of the counter (the Hide click after ranking, the listening-time click after Hide) stay guarded while ranked by listening time (RA14). The sort test's loop now runs in `subTest(mode=...)` with a case tuple that carries the other mode, which removes its if/else branch; its assertions are unchanged. The toast assertion of the first merged test is not repeated here: `test_hidden_note_and_toast_carry_the_count_of_dropped_albums` guards the toast.

Deviations: the CSV test `test_csv_while_ranked_by_listening_time_lists_only_ranked_rows` was kept, not merged: its fixture is the only one with matched rows the listening-time rule drops, so a merge would lose that case. Edited existing tests: `test_hidden_note_does_not_count_rows_hide_already_hides` (renamed `test_hidden_note_counts_only_rows_the_ranking_alone_drops`), `test_hide_toggled_while_ranked_by_listening_time_refreshes_the_note` and `test_hide_toggled_on_listening_time_lowers_the_count_to_one` (merged into it), `test_sort_updates_order_ranks_metrics_and_accessibility`. The script is not collected by pytest, so the count is unchanged.

Validation: `pytest -q` -- **2873 passed**.

### 2026-10-25 - UI round 2 backlog: test consolidation, parity family

Side task, no batch tag: remove the frontend gate's module-shape parity tests, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA20): cut repeated and written-function tests to save suite time; the owner approved this removal outright: "you have permission for the parity family to save that 5% of suite time". This reverses the post-split parity guard added under F-B21-51, which checked that every name a gate slice moved out of `scripts/dev/frontend_gate.py` is still defined in its slice and still resolves through the gate module. Those tests are gone from the nine slice files (`test_the_slice_defines_the_name`, `test_the_name_resolves_through_the_gate_module`), from `test_frontend_gate_colour.py` (`TestFacadeStillReExportsTheMovedHelpers`) and from `test_frontend_gate_shared.py` (`test_the_shared_module_defines_the_name`), with the name lists and imports only they used. Collected cases in the eleven edited files plus `test_frontend_gate_split.py` fall from 501 to 307 (-194); the suite falls from 3067 to 2873. Every behaviour test, `tests/scripts/dev/gate_parity.py` and `test_frontend_gate_split.py` (the split's own check) stay.

Deviations: none. Edited existing tests: removed `test_the_slice_defines_the_name` and `test_the_name_resolves_through_the_gate_module` (in the assets, forms, heatmap_access, layout, pipeline, runtime, spotlight_photo, theme and unmatched gate test files), `TestFacadeStillReExportsTheMovedHelpers` and `test_the_shared_module_defines_the_name`.

Validation: `pytest -q` -- **2873 passed**.

### 2026-10-25 - UI round 2 backlog: ranking agreement test

Side task, no batch tag: a browser test that a listening-time run and a switched play-count page agree, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (R6): a run started in listening-time mode and a page switched to it show the same leaderboard. `tests/frontend/test_results_ranking_agreement.py` renders one four-album fixture (two timed, one at 0 seconds, one with no key) as a playtime run and as a play-count run, loads both Flask pages in Chromium (static files served with `page.route`), switches the play-count page through the real toggle, and compares the visible (album, rank) sequence, the Total Albums, Top Artist and Scrobbles text, the hidden-count integer and the CSV rows. It also checks that switching to track plays restores all four albums and that switching back reproduces the first list. The fixture orders timed albums differently by time and by plays, so a client that ranks by the wrong metric fails. Hand-applied defects (the server rendering untimed rows without `hidden`, the client skipping the renumber, the client ranking by plays in listening-time mode) each turn all three tests red.

Deviations: the fixture gives all four albums one artist, because Top Artist follows the first row and legitimately differs between the two paths; this is filed as F-B23-64 (open, P3, owner ruling RA21), and the fixture comment names it. Edited existing tests: none.

Validation: `pytest -q` -- **3067 passed**.

### 2026-10-25 - UI round 2 backlog: listening-time ranking documented

Side task, no batch tag: document the listening-time ranking rule in `DESIGN.md` and close F-B23-46, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (R6, RA3, RA5): albums with no listening time should not rank under listening time, and the design record should say so. `DESIGN.md` gains a "Results Row: Listening-Time Ranking" section after the unmatched variant: the rule, renumbered ranks, header figures that keep describing the whole result (the Hide control recomputes them as it always has, RA18), the note and toast that give the hidden count, the return of the albums under track plays, and one rule on the server and in the browser. F-B23-46 moves from `docs/agents/FINDINGS.md` to the archive as resolved, naming T7 `7e529efc`, T7b `2115e858` and T10 `078ef258`.

Deviations: a sibling `###` section rather than a bullet, because Components holds the unmatched variant as a section. Edited existing tests: none.

Validation: `pytest -q` -- **3064 passed**.
