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
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); the other two seams
  remain: one album-metadata encoding, under way as PR #5 on
  `refactor/metadata-encoding` (plan
  `docs/superpowers/plans/2026-10-20-metadata-encoding.md`), and the statistics
  module. Job persistence waits: a database-backed job store would keep the
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

### 2026-10-21 - Album metadata is one record from provider to results

Side task, no batch tag: Task 3 of PR #5, album metadata stored and read as one record from provider to results (cache, the three orchestrator phases, the results builder and seven test files), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: card B-5 and the Task 27 brief say it in one line: one `AlbumMetadata.from_row` replaces the repair code, and `_album_provider` and `_album_url` are deleted.

Why (B-5): after the providers an album was re-encoded as a nine-tuple for the database, as a 4-key or 7-key dict for the results and as a 7-key dict from cache reads; two functions in `_results.py` existed only to repair what the shortest of them lacked, and `batch_persist_metadata` kept a six-tuple branch that only a test reached. There is now one record, and one place a stored row is read (`AlbumMetadata.from_row`) and one statement that writes `spotify_cache` (`batch_persist_metadata`).

What changed: `batch_lookup_metadata` returns `{key: AlbumMetadata}` (a row naming no provider album is left out, so it is a miss) and `batch_persist_metadata` takes `{key: AlbumMetadata}`, with the same SQL and the same single statement. `_run_spotify_batch_detail_phase`, `_run_deezer_fallback_phase` and `_fetch_spotify_misses` return `{key: AlbumMetadata}`; `cache_hits[key]["cached"]` holds an `AlbumMetadata` for hits and live fetches alike; `_persist_new_metadata` takes that dict. Deleted: `AlbumMetadata.as_cache_row`, `_album_provider`, `_album_url`, the `len(r) > 6` branches and both inline `cached` dicts. New: `tests/album_metadata.py` (builders `spotify_metadata`, `deezer_metadata`). Docs: `cache.py` now imports `enrichment` (SESSION_CONTEXT module graph and the `Cache --> Enrichment` edge in `runtime-system.md`; the Mermaid validator tool was not available to this implementer, so the edge was checked by hand against the neighbouring edges, and the "eleven nodes import config" count was re-checked with an `ast` walk: this change adds no `config` import, so it stands); F-B23-32 now names `AlbumMetadata.from_row` as the one place a cached link enters.

Deviations: a live Spotify result now shows the link Spotify returned in `external_urls.spotify` rather than a rebuilt classic link (the same string in practice). A stored row naming no provider album is a miss. `cache_hits[key]["cached"]` keeps its key name though it now also holds live fetches. The first view of a search now renders the provider-supplied URL (`external_urls.spotify`) where it used to render a constructed one, so F-B23-32's exposure to unchecked provider URLs widens slightly (the finding is edited in this commit; its status stays open). Beyond the brief's edit list: `test_run_spotify_batch_detail_phase_empty_id_list_skips_api_call` asserted `result == []` and now asserts `result == {}` (the return type changed), and the docstring of `test_an_older_spotify_row_is_a_spotify_album_with_the_classic_link` no longer names the two deleted functions (the sweep greps for them). The sweep regex also matches the brief-named test `test_a_cached_album_with_no_link_has_a_null_album_url` (substring `_album_url`); that is the only hit.

Task 1's `tests/test_album_cache_parity.py` and `tests/fake_postgres.py` are unchanged and pass: this is the parity proof, and the statement sequence and connection count are as before.

Edited existing tests: `tests/services/test_enrichment.py` (two `as_cache_row` tests deleted, replaced by Task 1's stored-column tests and the persist tests below), `tests/services/test_cache.py` (four tests replaced by five; the six-tuple test is deleted because no caller builds a six-tuple, its legacy-row rule now lives in `from_row`), `tests/test_repositories.py`, `tests/services/test_orchestrator_process_albums.py` (four fixtures, three persist assertions), `tests/services/test_orchestrator_helpers.py` (three fixtures, one new test), `tests/services/test_orchestrator_fetch_spotify.py` (return type of the phases), `tests/services/test_failure_logging.py` (one argument).

Mutation evidence (each planted in a file kept aside, restored byte for byte, then re-run green): (1) `spotify_ids` from `album_id` -> `test_batch_persist_metadata_writes_a_deezer_album_without_a_spotify_id` and `test_a_deezer_album_is_stored_without_a_spotify_id_and_a_repeat_search_matches_it` fail; (2) `provider_album_ids` and `provider_urls` swapped -> `test_batch_persist_metadata_writes_a_spotify_id_to_both_columns` and `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` fail; (3) `if metadata is not None:` removed -> `test_a_row_naming_no_provider_album_is_a_cache_miss` fails; (4) result `album_url` from `image_url` -> `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` fails; (5) `or None` dropped -> `test_a_cached_album_with_no_link_has_a_null_album_url` fails; (6) `new_metadata[key] = metadata` deleted -> the Spotify parity test fails (the repeat search finds nothing stored); (7) `new_metadata.update(deezer_metadata)` deleted -> the Deezer parity test and `test_spotify_search_outage_degrades_to_deezer_and_lists_the_rest_as_unavailable` fail; (8) provider columns dropped from the `from_row` input -> `test_batch_lookup_metadata_returns_albums_with_their_provider_columns` fails; (9) `provider_url` dropped from the SELECT -> the same test fails on its SQL assertion; (10) `{**r, "provider": r["provider"]}` -> `test_batch_lookup_metadata_reads_a_pre_provider_row_as_a_spotify_album` fails (`KeyError: 'provider'`).

Validation: `pytest -q` -- **2879 passed**.

### 2026-10-21 - A Deezer album with no stored link is pinned

Side task, no batch tag: fix round 1 of Task 2, the album reading itself from a cache row, on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: a test must fail when the code does the wrong thing, so the rule that a Deezer row with no stored link has no link needs a test of its own.

What changed and why: review found that a mutant giving every provider the Spotify classic link (`open.spotify.com/album/<id>`) passed all 14 tests, though it would send a Deezer id to a Spotify page. `test_a_deezer_row_with_no_stored_link_has_no_link` builds a Deezer row with `provider_url` NULL and asserts the link is `""` (the plan and `from_row` agree). Two existing tests also gained `assert album is not None`, so a wrong `from_row` fails on an assertion instead of an AttributeError on None.

Deviations: none. Edited existing tests: `test_a_deezer_row_keeps_the_deezer_id_and_link` and `test_an_older_spotify_row_is_a_spotify_album_with_the_classic_link` (one added assertion each).

Mutation evidence (planted in a file kept aside, restored after): the link fallback made unconditional (`if True` for `provider == "spotify"`) -> `test_a_deezer_row_with_no_stored_link_has_no_link` fails; restored, 18 pass in the file.

Validation: `pytest -q` -- **2879 passed**.

### 2026-10-21 - The fake Postgres refuses what Postgres refuses

Side task, no batch tag: fix round 1 of the cache parity tests' fake database (`tests/fake_postgres.py`), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: the hosting-cost pin and the connection-ownership checks that Tasks 3 and 4 re-run must fail when the code misbehaves, not stay green because the fake is lenient.

What changed and why: review of the first commit planted two defects that left all 17 tests green. (1) A statement naming neither cache table (`SELECT 1` in `cleanup_stale_metadata`) was refused before it was recorded, and every cache caller swallows exceptions, so nothing showed. The fake now records every statement first (`table` is `None` when it names no cache table), then refuses it, lists it in the new `refused` list, and `fake_postgres` asserts `refused` is empty when its block ends; the sequence pin sees the extra entry as well. (2) The fake accepted `fetch`/`execute` after `close()`; asyncpg raises `InterfaceError`. `close()` now sets `closed`, each connect clears it, and a statement on a closed connection is recorded, listed in `refused` and raises `asyncpg.exceptions.InterfaceError`. The module docstring says what is not modelled (TTLs, column types, unique-key rules).

Deviations: none. Edited existing tests: none; `tests/fake_postgres.py` is the only file changed (no new test).

Mutation evidence (planted in a file kept aside, restored after): (16) the `[deezer]` leak case, `provider_url` suffixed with the listener on the Deezer fallback path -> `test_a_stored_row_carries_no_listening_fact[deezer]` fails; (17) `SELECT 1` after the DELETE in `cleanup_stale_metadata` -> `test_a_search_costs_one_connection_and_a_fixed_statement_sequence` and 15 more fail (the refused-statement assertion at the end of `fake_postgres`, and the extra sequence entry); (18) `conn.close()` before `_persist_new_metadata` in `process_albums` -> 16 tests fail (stored row absent, refused assertion). The 15 earlier rows were re-run against the stricter fake and each still fails its named test(s); restored, all 17 pass.

Validation: `pytest -q` -- **2878 passed**.

### 2026-10-21 - An album reads itself from a cache row

Side task, no batch tag: one classmethod, one property and one constant on `AlbumMetadata` that read a `spotify_cache` row as an album, plus one line in `spotify.py`, on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: one album-metadata encoding, so the rules for reading a cache row are written once and tested before anything calls them.

What changed and why: the legacy-row rules lived in two places that disagree about where they live: `cache.batch_lookup_metadata` builds a dict and `_results._album_provider` / `_album_url` finish the job later. `enrichment.py` gains `SPOTIFY_ALBUM_URL`, `AlbumMetadata.spotify_id` (the Spotify album id, `None` for any other provider) and `AlbumMetadata.from_row(row)` (a row with no provider is a Spotify row, a Spotify row with no link gets the classic album page, a NULL release date reads as `""`, `track_durations` reads as a dict whether the driver returned text or a dict). `spotify.album_metadata_from_details` uses the constant for its default link; the link is unchanged. SESSION_CONTEXT Section 3 names the new role. Additive: no caller changes. Task 3 deletes `_album_provider` and `_album_url` and calls `from_row`.

Deviations: a row naming no provider album now reads as `None` (no write path produces one). Edited existing tests: none; the import block of `tests/services/test_enrichment.py` gained `dataclasses`, `pytest` and `SPOTIFY_ALBUM_URL`, and 14 tests (8 functions, parametrized) were appended.

Mutation evidence (each planted in a copy of `enrichment.py` kept aside, restored after, test re-run green): (1) `spotify_id` returns `album_id` for every provider -> `test_only_a_spotify_album_has_a_spotify_id` fails (`'6237061' is None`); (2) release_date/image_url swapped -> `test_a_stored_row_maps_every_field_to_the_album` fails; (3) `album_id = spotify_id` -> `test_a_deezer_row_keeps_the_deezer_id_and_link` fails; (4) provider fallback dropped -> `test_an_older_spotify_row_...[written_before_the_provider_columns]` fails; (5) link fallback deleted -> the same test fails for both rows; (6) `json.loads` and `or {}` dropped -> `test_track_durations_read_as_a_dict_...` fails for json_text, empty_object, empty_text and null; (7) `release_date=row.get("release_date")` -> `test_a_row_with_no_release_date_has_an_empty_one` fails; (8) the `return None` guard deleted -> `test_a_row_that_names_no_provider_album_reads_as_nothing` fails; (9) field `play_count: int = 0` added -> `test_album_metadata_holds_album_facts_only` fails. Every first failing assertion is the one the row names.

Validation: `pytest -q` -- **2878 passed**.
