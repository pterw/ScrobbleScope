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
  normalized Last.fm scrobbles with one album aggregate. The include-unmatched
  control (PR #1) and backend hygiene (PR #2) are done. The album request module
  is done (PR #3, branch refactor/album-request-module, plan
  `docs/superpowers/plans/2026-10-20-album-request-module.md`); normalized
  Last.fm scrobbles with one album aggregate is done (PR #4, branch
  refactor/lastfm-scrobbles, plan
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); one album-metadata
  encoding is done (PR #5, branch refactor/metadata-encoding, plan
  `docs/superpowers/plans/2026-10-20-metadata-encoding.md`); the statistics
  module remains. Job persistence waits: a database-backed job store would keep the
  database awake, which the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`. PR #7, UI
  consistency, finished round 1 (plan
  `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`); further rounds
  wait for the owner's screenshots, each with its own plan.
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

### 2026-10-21 - Pin the classic link when external_urls is null

Side task, no batch tag: pin the null `external_urls` guard of `album_metadata_from_details` with a test, on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: a claim in a document is backed by a test that fails without it.

What changed and why: `dfd22dc`'s fallback also guards a payload whose `external_urls` is `null` (`(details.get("external_urls") or {})`) and its entry says "missing or null", but no case passed `{"external_urls": None}`; the old `None` parameter became `details = {}`, the missing key. The parametrized test now takes the whole details payload and gains a `null-object` case (expected: `https://open.spotify.com/album/sp3`). With the guard replaced by `details.get("external_urls", {})` the new case fails with `AttributeError: 'NoneType' object has no attribute 'get'` and the other five pass; restored, all six pass. Review of close-out, Minor 3. No production code changed.

Deviations: none.

Edited existing tests: `test_album_metadata_from_details_keeps_the_classic_link` in `tests/services/test_spotify_service.py` (parameters now carry the details payload; 5 cases became 6).

Validation: `pytest -q` -- **2897 passed**.

### 2026-10-21 - Make the #5 docs true for the merge

Side task, no batch tag: close-out of PR #5, making the docs true for the merge (PLAYBOOK Section 3, the plan's citations, a test docstring, two architecture files, F-B23-47), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: docs follow the code, and nothing a reader needs lives only in an untracked workspace.

What changed and why: PLAYBOOK Section 3's "Before WP-1" bullet now says one album-metadata encoding is done (PR #5) and only the statistics module remains. The committed plan cited the untracked `constraints.md` R9 in three places (the global constraint, Step 6, the mutation step); the citation is dropped and the rule stays inline, with no other plan text changed. The docstring of `test_process_albums_conn_always_closed` said the connection closes "in the finally block"; Task 4 moved the close into `open_album_cache`'s context manager, so it now says so. `top-albums-sequence.md` drew the stale-row cleanup as a separate `Orch->>Cache` call, but `AlbumCache.lookup` runs `cleanup_stale_metadata` itself, so that one message is now `Cache->>Cache: Clean stale rows inside lookup (both lookup outcomes)` (line 111, for the controller to render). One prose line in `runtime-system.md` was re-wrapped. F-B23-47 is filed: `test_job_threads_can_share_the_token_state_dict_without_error` failed once beside other test files in Task 2's run, a switch-interval thread race that is flaky by design and unrelated to the diff (open, P3, no fix in this PR).

Plan-mandated defects, recorded here and not edited in the plan: the brief's mutation row 7 named `test_a_failing_cache_statement_never_fails_the_search[write]`, which checks only `db_cache_warning` and cannot catch the plant, so Task 4 added `test_a_failed_persist_is_reported_as_a_warning_not_as_persisted_rows`; and Step 7's parity-proof command diffed against 2847cd5, before Task 1's fix round c6769b7, so it reported differences in `tests/fake_postgres.py` that came from c6769b7, not from Task 3 or 4.

Deviations: `top-albums-sequence.md` line 101's Note ("No lookup, cleanup, or persistence") is left as drawn, since the brief limits the redraw to the one message.

Edited existing tests: `tests/services/test_orchestrator_process_albums.py` (one docstring line, no code).

Validation: `pytest -q` -- **2896 passed**.

### 2026-10-21 - A live Spotify album keeps its link when Spotify sends none

Side task, no batch tag: restore the classic album link for a Spotify album whose details carry no link (`album_metadata_from_details`), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: a refactor PR must not change behaviour nobody asked it to change.

What changed and why: before this PR a Spotify album whose details payload had `external_urls.spotify` null or `""` still got `https://open.spotify.com/album/<id>`, rebuilt by `_results._album_url`. Task 3 deleted that rebuild, so such an album got `album_url` null (task 3 review, Minor 1). `album_metadata_from_details` now falls back to the canonical URL when `external_urls` is missing or null, or when `spotify` is missing, null or empty; a link Spotify sends is kept as sent.

Deviations: none.

Edited existing tests: none. Added `test_album_metadata_from_details_keeps_the_classic_link` (5 cases) in `tests/services/test_spotify_service.py`; with the fallback removed, 4 of the 5 fail, and with it restored all pass.

Validation: `pytest -q` -- **2896 passed**.

### 2026-10-21 - The cache owns its connection and its failures

Side task, no batch tag: Task 4 of PR #5, the cache owns its connection and its failures (`AlbumCache`, `open_album_cache`, `process_albums`, `orchestrator/_cache.py`, the facade's imports), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent (the spec's hosting ceiling): a missing or sleeping database degrades to provider calls and never fails a job.

Why (F-B23-3): `process_albums` opened the connection, held it across provider work and closed it in a `finally` that did not guard `close()`, while `orchestrator/_cache.py` owned the failure policy, so understanding "the cache is optional" took two modules and a failing `close()` failed a job whose results were built. The connection-closure test also had to configure the provider machinery.

What changed: `cache.AlbumCache(conn)` has `enabled`, `lookup_failed`, `persist_failed`, `lookup`, `persist`, `lookup_original_releases` and `close`; `open_album_cache()` connects through `get_db_connection` and closes when its block ends however it ends. `process_albums` wraps Phases 1 to 4b in `async with open_album_cache()`, and `_lookup_cached_metadata` and `_persist_new_metadata` take the cache and turn its flags into the same job stats and log lines as before (every log line is kept word for word). The facade no longer imports `get_db_connection` or the four batch functions, so tests patch them at `scrobblescope.cache.<name>`. `_lookup_cached_original_release` is gone (its body is `AlbumCache.lookup_original_releases`). A new boundary test pins that only `cache.py` names the metadata read, write and cleanup functions and holds the one INSERT into `spotify_cache`. Docs: SESSION_CONTEXT Sections 3 to 5, `runtime-system.md` (one node and the release-date bullet), `top-albums-sequence.md` (four messages and one note, commas only), `BATCH23_DEFINITION.md` (the PR #5 amendment of WP-3's metadata shape: Data handling and a WP-3 bullet), and F-B23-3 marked resolved.

Deviations: a failing `close()` is now logged by exception class and swallowed, the one behaviour change. `_lookup_cached_original_release` is deleted and its two tests moved to `tests/services/test_cache.py`. Mutation row 7 of the brief (record `db_cache_persisted` after a failed persist) is not caught by `test_a_failing_cache_statement_never_fails_the_search[write]`, which checks only `db_cache_warning`, so a test was added, `test_a_failed_persist_is_reported_as_a_warning_not_as_persisted_rows` in `test_orchestrator_process_albums.py`; Task 1's parity file stays untouched. The re-point script printed 46, 2, 2 and 3 replacements, and `ruff format` then reflowed the lines the longer patch strings overran. The Mermaid validator was not available to the implementer, so the controller renders the two diagram files (`runtime-system.md` flowchart node, `top-albums-sequence.md` sequence).

Hosting evidence: `tests/test_album_cache_parity.py` and `tests/fake_postgres.py` are unchanged by this task and pass (one connection, one close, the same statement sequence, under every injected failure), and the diff of `scrobblescope/` adds no `.execute(`, `.fetch(` or `asyncpg.connect(` line.

Edited existing tests: `tests/services/test_orchestrator_process_albums.py` (patch strings, and two direct `_lookup_cached_metadata` calls now wrap `AlbumCache`), `tests/services/test_orchestrator_fetch_spotify.py` and `tests/test_pipeline_integration.py` (patch strings only), `tests/services/test_orchestrator_helpers.py` (two tests moved to `test_cache.py`), `tests/services/test_failure_logging.py` (four sites re-pointed at `AlbumCache`).

Mutation evidence (each planted in a file kept aside, restored byte for byte, then re-run green): (1) `AlbumCache.close` without its `try`/`except` -> `test_a_failing_close_is_logged_by_class_and_never_raised` (RuntimeError) and `test_process_albums_survives_a_connection_that_fails_to_close` fail; (2) `open_album_cache` without `try`/`finally` -> `test_the_connection_closes_once_however_the_block_ends[True]` (`(1, 0) == (1, 1)`) and `test_the_connection_is_closed_once_when_no_provider_can_answer` fail; (3) `persist` guard without `self._conn is None` -> `test_a_cache_with_no_database_does_nothing_and_fails_nothing` fails; (4) `lookup` without `try`/`except` -> `test_a_failing_cache_statement_never_fails_the_search[read]` fails; (5) a reconnect in `lookup`'s `except` -> the same test fails on `(2, 1) == (1, 1)`; (6) `release_checks.py` importing `batch_persist_metadata` -> `test_only_the_cache_module_reads_or_writes_the_metadata_table` fails; (7) `db_cache_persisted` recorded after a failed persist -> `test_a_failed_persist_is_reported_as_a_warning_not_as_persisted_rows` fails; (8) a bare write in `persist` -> `test_a_failed_read_is_a_miss_and_a_failed_write_is_not_an_error` and `test_a_failing_cache_statement_never_fails_the_search[write]` fail; (9) `lookup` returning `{}` -> `test_what_persist_writes_lookup_reads_back` fails; (10) Task 3's row 3 re-planted (`if metadata is not None:` removed) -> `test_a_stored_row_naming_no_provider_album_is_a_miss_not_an_album` fails.

Validation: `pytest -q` -- **2891 passed**.
