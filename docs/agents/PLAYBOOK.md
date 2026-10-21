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
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); the statistics
  module is done (PR #6, branch refactor/statistics-module, plan
  `docs/superpowers/plans/2026-10-20-statistics-module.md`); one seam
  remains, one album-metadata encoding. Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #7, UI consistency, is under way on `feat/ui-consistency`; round 1's
  plan is `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`.
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

### 2026-10-21 - Say what the #6 tests and diagram prove

Side task, no batch tag: make a test docstring, a sequence diagram and two module docstrings say only what is true, on `refactor/statistics-module`, a branch off `main`.

Owner intent: nothing the close-out wrote should claim more than was proven or draw a step out of order.

What changed: `test_scrobbles_stat_prints_the_figures_it_is_handed` now says its mutation was planted in `data-plays-listed` and in `data-plays-matched` and that the visible Scrobbles text is asserted but was not planted; the dated entry "A test pins that the page prints the Scrobbles figure it is handed" is point-in-time and unedited, but its Proof names the same two attributes only, so the visible text was never mutation-tested. `docs/architecture/heatmap-sequence.md` drew `heatmap_statistics` before the local `total`, `max_count` and `active_days` step, while `heatmap.py` runs the local step first; the two messages swap places (lines 83 and 85 trade). `listening_stats.py`'s module docstring now also names the four `scripts/dev/_frontend_gate_*` importers, and `heatmap.py`'s module docstring says the job result carries the statistics and not only the daily counts.

Recorded, no change: the test pins the filled render block only, the no-matches block also passes `play_stats` and is not pinned (brief asked for one test); the `HEATMAP_WINDOW_DAYS` comment in `heatmap.py` keeps one over-long line, outside this brief.

Deviations: none. Edited existing tests: `test_scrobbles_stat_prints_the_figures_it_is_handed` (docstring only). Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - WP-6 builds on the statistics module

Side task, no batch tag: amend WP-6 in `BATCH23_DEFINITION.md` for the statistics module and mark that seam done in Section 3, on `refactor/statistics-module`, a branch off `main`.

Owner intent: WP-6 must start from the module that exists, not plan to create it.

What changed: WP-6 gains a paragraph after "Statistics contract before implementation" saying `scrobblescope/listening_stats.py` is the pure helper WP-6 extends, what it already computes and publishes with a population, that the JS and template render published values and compute none, and that include-unmatched albums count in plays listed and in no duration figure. Section 3's "Before WP-1" bullet now says the statistics module is done (PR #6, branch and plan named) and one seam, album-metadata encoding, remains; the "under way" sentence is deleted. Nothing else in Section 3 changed. The Batch 23 row of `.claude/SESSION_CONTEXT.md` names no tranche PR, so it is unchanged.

Reconciled: PR #4's WP-2 amendment (the parser yields `plays.Play`; `plays.aggregate_albums` and `plays.aggregate_daily_counts` feed both sources) makes no sentence of the new paragraph untrue, so it needed no correction.

Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - Make the #6 docs true for the merge

Side task, no batch tag: close out PR #6 by making its diagram and plan text true, on `refactor/statistics-module`, a branch off `main`.

Owner intent: nothing the statistics module touches should describe a step or a name that is no longer so.

What changed: `docs/architecture/heatmap-sequence.md` drew `heatmap_statistics` twice (lines 83 and 85); it is now one `Heatmap->>Heatmap` message carrying its figures, and the local step Task 4 removed (`total`, `max_count` and `active_days` computed in `heatmap.py`, `total_scrobbles` and `active_days` recorded as stats) is drawn again as one message after the Note. In the statistics-module plan, "Albums control" is now "Unmatched albums control" (line 22) and the worktree `C:/ssw/stm` is `C:/ssw/st` (line 50), as constraints L2 asks. `top-albums-sequence.md` is left to the documentation PR.

Recorded, no change: the UTC-day test's remaining gap (a host-zone read that skips `astimezone`) has no code path, because the only timestamp-to-date reads are `listening_stats.utc_date` (`astimezone(UTC)`) and `plays.py`'s `play.played_at.date()`, and `Play` requires a UTC `played_at`. Task 5's Minor 2 (a missing `data-plays-*` attribute would render NaN) needs no guard, because the server always renders both. The `config/docsync.toml` window comment stays: the daily average still divides by `len(daily_counts)`, the zero-filled `HEATMAP_WINDOW_DAYS` window, so it is true.

Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - A test pins that the page prints the Scrobbles figure it is handed

Side task, no batch tag: pin that `results.html` prints the Scrobbles figures the route hands it, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the page must show the figure Python decided, and a template that quietly re-adds the rows must fail a test.

What changed: `data` and `play_stats` both come from `filtered_results`, so a template summing `data` for the two `data-plays-*` attributes passed every earlier route test. `test_scrobbles_stat_prints_the_figures_it_is_handed` patches `album_play_statistics` to return 777 listed and 555 matched over one 50-play row and asserts both attributes and the visible figure carry the handed values. Test only; no production code.

Proof: a Jinja sum over `data` planted (scratch copy of `results.html`, restored) in `data-plays-listed` failed on 50 vs 777, and in `data-plays-matched` on 50 vs 555.

Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2898 passed**.
