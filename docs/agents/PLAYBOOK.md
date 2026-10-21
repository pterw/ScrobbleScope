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

### 2026-10-21 - The PR template asks for state and validation

Side task, no batch tag: the PR template gains State and Validation sections, on `chore/pr-template`, a branch off `main`.

Owner intent: "The state format is good, I think the State section and table is worth incorporating into the pull request template which exists in this repo."

What changed: `.github/PULL_REQUEST_TEMPLATE.md` now runs Summary (names the plan file for a tranche or batch PR), State (a Task / What / Commits / Review table for a multi-task PR, kept true at every push), Validation at this head (head SHA, gates and results, CI run), the unchanged six-box Checklist with a note to tick gate boxes only once CI and the final gate pass at the head that leaves draft, and a closing comment forbidding attribution lines. The comments are HTML so GitHub hides them. Template only, so a PR opened from it starts with the right shape.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2847 passed**.

### 2026-10-20 - Make the #4 docs say what the branch now does

Side task, no batch tag: eight stale or untrue sentences the PR #4 task reviews found, fixed, on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: the branch's docs describe the branch as it is when it merges, not as it stood while the tasks were under way.

What changed: Section 3's "Before WP-1" bullet now says PR #4 is done (PR #3's form) and that the two seams remaining are one album-metadata encoding and the statistics module, and drops the "Tasks 2-5 after PR #3 merges" sentence. The `tests/test_lastfm_job_results.py` module docstring no longer says five tests are xfail-marked; they pass since Task 4. `fetch_top_albums_async`'s docstring already describes behaviour only, with no plan label (nothing to change). The "Callers get scrobbles, not Last.fm pages" entry's "so the controller renders them" now records what was done: the controller rendered `runtime-system.md`, `top-albums-sequence.md` and `heatmap-sequence.md` with the Mermaid validator at 9a8d79c and all three are valid. README's "What each module owns" table gains `plays.py` and `release_status.py`. `orchestrator/__init__.py`'s `__all__` is back in sorted order (no name added or removed).

Deviations: none. Edited existing tests: none (docstring only in `tests/test_lastfm_job_results.py`).

Validation: `pytest -q` -- **2847 passed**.

### 2026-10-20 - Close two guard gaps the reviews found

Side task, no batch tag: two test guards the PR #4 task reviews found too weak, on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: a guard test must fail for every way of breaking what it guards, not only the one way its author planted.

What changed: `test_the_routes_never_import_the_correction_worker` now catches all three import forms of `scrobblescope.release_checks` (`from scrobblescope.release_checks import x`, `from scrobblescope import release_checks`, `import scrobblescope.release_checks`); the task 3 review had planted the middle form in `routes/api.py` and the test passed. New `test_each_request_field_reaches_the_enrichment_tail` (six parametrised cases in `tests/services/test_finish_album_job.py`) asserts that `finish_album_job` passes `year`, `sort_mode`, `release_scope`, `decade`, `release_year` and `limit_results` to `_process_filtered_albums` each in its own place, with `overall_start_time` and `include_unmatched`, and that the job's progress was 20 at that call (the task 5 review's Minor 2). `min_plays` and `min_tracks` are not asserted: `finish_album_job` does not read them, `select_albums` applied them before. Proof by planted defect in a scratch copy: all three import forms fail the first test; swapping `decade` and `release_year` fails two cases, `year + 1` fails one, dropping the `jobs.advance(job_id, 20, ...)` call fails all six.

Deviations: none. Edited existing test: `test_the_routes_never_import_the_correction_worker`.

Validation: `pytest -q` -- **2847 passed**.

### 2026-10-20 - One album selection and one publish step

Side task, no batch tag: `plays.select_albums` returns one typed `AlbumSelection` and `orchestrator.finish_album_job` is the one publish step after it (PR #4 of the pre-Batch-23 tranche, task 23d, F-B23-1's threshold half, review card B-3), on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: review card B-3, "one typed album aggregate built from normalized plays, the same for a Last.fm job and an export job, and one publish step after aggregation... No sentinel returns from the aggregation" (Task 23 brief), so Batch 23 WP-3's `export_album_task` ends exactly as a Last.fm job does.

What changed: `plays.py` gains the frozen `AlbumSelection(eligible, exclusions, total_below_threshold, plays_seen, unique_albums)` with `stats()` (the four wire-named counts) and the pure `select_albums(aggregate, min_plays, min_tracks, exclusion_cap)`: the one threshold partition and the exclusion cap, ties broken by normalized key. `orchestrator/__init__.py` deletes `_fetch_job_albums` (the `None` sentinel), `_record_lastfm_stats`, `_cap_threshold_exclusions` and Task 4's interim metadata dict. `fetch_top_albums_async` now returns `(AlbumSelection, FetchSummary)`, never `None` and never a status dict. New `finish_album_job(job_id, selection, album, *, overall_start_time)` takes PR #3's `AlbumRequest` (its `username` is `None` for an export), records the four stats and one unmatched record per exclusion, ends with one `jobs.succeed(job_id, [], "No albums found for the specified criteria.")` and no correction-worker hand-off when nothing is eligible, and otherwise runs `_process_filtered_albums`. The Last.fm-only stats (`pages_fetched`, the page-loss notice, `record_partial_source(lastfm)`, `pages_dropped`) move to `_record_fetch_stats`, which `_fetch_and_process` calls before `finish_album_job`; `_fetch_and_process` rebuilds the `AlbumRequest` from its positional parameters. `tests/helpers.py` gains `lastfm_albums` for tests that patch `fetch_top_albums_async`. `_process_filtered_albums`, `_build_results` (F-B23-1's release-scope half stays open) and the two `return []` after a Spotify failure are unchanged.

`BATCH23_DEFINITION.md` amendments, this PR's by the tranche spec's documentation rule (a seam change that alters what a Batch 23 work package may assume amends the definition in the same PR): WP-3's first bullet (the export job calls `aggregate_albums`, `select_albums` and `finish_album_job` with an `AlbumRequest`), WP-3's acceptance start (`process_albums` receives the selection's eligible albums, `lastfm.fetch_scrobbles` is never called) and WP-2's acceptance sentence (the aggregator's output feeds `plays.select_albums`). The unexecuted Spotify-export plan is a dated plan and is not annotated.

Docs: SESSION_CONTEXT Sections 3 and 4 (module list, `plays.py` and `orchestrator/__init__.py` imports re-derived by the `ast` snippet), `docs/architecture/runtime-system.md` (edge `Plays --> Unmatched`), `docs/architecture/top-albums-sequence.md` (three messages and one paragraph), F-B23-1's Status (threshold half landed). Every added Mermaid line was checked by script (no `;`, blocks balanced); the `validate_and_render_mermaid_diagram` tool was not available to the implementer, so the controller renders them.

Deviations: the plan's sequence message ended "...retry); Last.fm only", whose `;` Mermaid reads as a statement separator, so it uses a comma. The plan's `_process_filtered_albums` docstring replacement would have left "It is called by `_fetch_and_process` ... and is called through" with a dangling `fetch_metadata` reference, so the sentence now reads "It is called through `finish_album_job`, which Batch 23's export task also calls". Edits were byte-safe Python, not `sed -i` (R9). Dated Section 4 entries and the logarchive still name the deleted functions, as point-in-time records.

Mutation evidence (scratch copy of the tree, one plant at a time, each restored): (1) `select_albums` sorting without the key tie-break fails `test_the_cap_does_not_depend_on_input_order` and `test_threshold_exclusion_cap_is_independent_of_input_order`; (2) slicing `list(excluded)[:cap]` fails `test_the_cap_keeps_the_most_played_exclusions`; (3) `stats()` reporting `len(self.exclusions)` fails `test_stats_are_the_four_numbers_a_job_records`; (4) `partition_albums_by_threshold` with `play_count <= min_plays` fails `test_it_splits_by_both_minimums_and_counts_each_side`; (5) publishing after the empty-result `jobs.succeed` fails `test_stats_and_exclusions_are_readable_by_the_time_the_job_ends`; (6) deleting the empty-result `jobs.succeed`/`return []` fails `test_a_selection_with_nothing_eligible_ends_the_job_once` and `test_when_every_album_is_below_a_minimum_the_job_ends_with_the_report`; (7) calling `jobs.succeed` twice fails `test_a_selection_with_nothing_eligible_ends_the_job_once`; (8) omitting `include_unmatched=` fails `test_the_albums_choice_reaches_the_enrichment_tail`; (9) `_publish_selection` writing `pages_fetched` fails `test_the_shared_step_writes_no_lastfm_only_stats`; (10) deleting the stats loop fails `test_a_selection_with_albums_is_published_and_enriched` and `test_stats_and_exclusions_are_readable_by_the_time_the_job_ends`; (11) deleting `record_partial_source` fails `test_lastfm_page_loss_is_recorded_as_a_kind_beside_its_sentence` and `test_a_dropped_page_makes_the_album_job_partial_and_says_so`; (12) `if True:` in `_record_fetch_stats` fails `test_a_complete_lastfm_fetch_records_pages_and_no_notice`; (13) skipping `_record_fetch_stats` fails `test_a_dropped_page_makes_the_album_job_partial_and_says_so`.

Edited existing tests: `tests/services/test_lastfm_logic.py` (8 tests unpack `(selection, summary)`; the stats test is renamed `test_fetch_top_albums_returns_stats_in_the_selection` and asserts `summary.pages_received == 1`), `tests/services/test_orchestrator_fetch_and_process.py` (12 patch return values now `lastfm_albums(...)`), `tests/services/test_orchestrator_helpers.py::test_lastfm_page_loss_is_recorded_as_a_kind_beside_its_sentence` (replaced, with `test_a_complete_lastfm_fetch_records_pages_and_no_notice` added), `tests/test_provider_fixtures.py::test_lastfm_fixture_flows_through_fetch_top_albums`. New: `tests/services/test_finish_album_job.py`, `TestSelectAlbums` in `tests/test_plays.py`. `tests/test_lastfm_job_results.py` is unchanged and still passes (the parity suite proves the tail rewrite).

Validation: `pytest -q` -- **2841 passed**.
