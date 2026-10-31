<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0031

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

### 2026-10-21 - Cache storage and failure behaviour are pinned end to end

Side task, no batch tag: parity tests with an in-memory fake Postgres that pin album metadata storage, read-back and cache-failure behaviour, on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: tests assert intended behaviour, and the encoding change of PR #5 starts from parity tests that name no function of `cache.py` (AGENTS.md "Refactor requires parity tests").

What changed: `tests/fake_postgres.py` is a fake database (two dicts; it refuses any statement the cache module does not send, records `(verb, table)` per statement, counts connects and closes). `tests/test_album_cache_parity.py` holds 17 tests through the real cache module and the correction worker. Every existing test patches `cache.py`'s own functions, so none could prove the stored row, the read-back or the Results JSON survives the encoding change. The tests pin: stored columns per provider; live search equals cached search; legacy rows read as Spotify albums with the classic link; a stored row carries no listening fact (no play count, no listener name); no database, a sleeping database (bounded attempts), a failing read, a failing write and a failing correction read all degrade to provider calls; one connection and a fixed statement sequence per search (the hosting-cost evidence Tasks 3 and 4 re-run); a MusicBrainz finding is stored and corrects the next search; the exclusion record carries the provider facts.

Deviations: no source file changed. Mutation row 15 (listener's name) and row 5 (play count) were planted as a suffix on the stored `provider_url` (`row[8] + "?u=" + original_data["listener"]`, and `"?plays=" + play_count`), not inside the durations dict as the plan wrote them, because a leak inside the durations dict trips the `json.loads(...) == DURATIONS` assertion first and never proves the `LISTENER not in stored` / `str(PLAY_COUNT) not in stored` assertions. Row 10 doubles the upsert by wrapping `conn.execute` in `batch_persist_metadata`. Edited existing tests: none.

Mutation evidence (15 rows, each planted in the named file, the FAIL line seen, the file restored from a byte copy, the PASS seen): 1 `album_image_url` read from `spotify_id` fails the Spotify round trip; 2 `spotify_id` written for Deezer fails `assert '9' is None`; 3 `_album_provider` without the Spotify fallback fails the older-row test; 4 `_album_url` without the classic link fails both older-row cases; 5 play count in the stored row fails `assert '4242' not in ...`; 6 `raise` after the last connect attempt fails the asleep test with `TimeoutError`; 7 no `DATABASE_URL` branch fails `assert 1 == 0` (a connect was attempted); 8 bare persist fails `[write]` with `OSError`; 9 no `conn.close()` fails both close tests with `(1, 0) == (1, 1)`; 10 upsert issued twice fails the statement sequence; 11 swapped original-release arrays fail the MusicBrainz test; 12 `"provider": None` on the exclusion entry fails both rows; 13 bare metadata read fails `[read]`; 14 bare correction read fails `[correction_read]`; 15 listener's name in the stored `provider_url` fails `assert 'listener_zq' not in ...`.

Validation: `pytest -q` -- **2864 passed**.

### 2026-10-21 - The metadata encoding plan opens its branch

Side task, no batch tag: the approved album metadata encoding plan added as the branch's first commit, with its review and drift fixes folded in and PLAYBOOK Section 3 made true, on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: "All plans should stay for archival purposes" (2026-10-20), so every PR's plan is the first commit of its branch; plan fixes are applied in a brief'd docs task when the branch is cut.

What changed: `docs/superpowers/plans/2026-10-20-metadata-encoding.md` is new. It passed a brief review (plan-review: no Critical, two Important, eight Minor) and a drift review against `main` at eb0db9e (no structural drift). Fixes applied, each in the plan: I1 no mutation step restores with `git checkout -- <file>` any more (Task 1 Step 5, Task 2 Step 5, Task 3 Step 9, Task 4 Step 9 and the Global Constraint now plant in a scratch copy or copy the file aside); I2 Task 2 mutation row 3 plants `album_id = spotify_id`, which the Deezer-row test can fail; M1 the six-tuple assumptions row names `test_batch_persist_metadata_upsert_call_shape` as the second six-element caller; M2 every new test that named no planted defect has one (Task 1 rows 13 and 14, Task 3 rows 8-10, Task 4 rows 8 and 9; one test is covered by Task 3 row 3); M3 `test_a_stored_row_carries_no_listening_fact` now puts the listener's name on the album entry and Task 1 row 15 plants a leak of it; M4 Task 1 Step 1 greps the names `fake_postgres` patches; M5 Task 4 no longer adds the schema remediation text or the `correction_lookup_schema` site (scope stays the P5 list; its deviation note and mutation row are gone); M6 Task 1 row 10 plants a second `conn.execute` with the same arguments; M7 Task 5 Step 2 says the seam is under way; M8 Task 3's entry notes that the first view of a search renders the provider-supplied URL where it used to render a constructed one, so F-B23-32's exposure widens slightly. Drift fixes: 5 renames to the public cache names (the Assumptions table rows and the Task 2 rationale) and the two "unverified until #4 merges" markers resolved as held; cosmetic: heading dated eb0db9e, the worktree path `C:/ssw/meta` is `C:/ssw/me` (2 places), Task 1 carries the test-module-count bookkeeping for its new `test_*.py` module, the Validation line is the exact form, the Task 4 `sed -i` re-point is a byte-safe script, and the Task 4 sweep excludes this file so it does not match its own entry. Section 3's "Before WP-1" bullet was stale: it did not say the include-unmatched control (PR #1) and backend hygiene (PR #2) are done, still listed the metadata encoding as not started, and still called PR #7 round 1 under way after it finished; it now says all three (plan numbers, not GitHub numbers).

Deviations: none from the brief; every proposed fix held at source. Edited existing tests: none (a plan and PLAYBOOK only).

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

### 2026-10-20 - Callers get scrobbles, not Last.fm pages

Side task, no batch tag: `lastfm.fetch_scrobbles` hands back normalized plays and both calculations read them (PR #4 of the pre-Batch-23 tranche, task 23c, F-B23-2, review card B-3), on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: the 2026-09-29 rulings, "tests move to the new interfaces" and `total_scrobbles` counts completed scrobbles only (the now-playing entry is not one). Batch 23 WP-2's Spotify parser must emit the same record, so one aggregator serves both sources.

What changed: new `scrobblescope/plays.py` (a leaf over `domain`) holds the frozen `Play(played_at, artist, album, track)` (`played_at.tzinfo` must be exactly `datetime.UTC`), `Window` (UTC bounds, `Window.year`, `start_ts`, `end_ts`, inclusive `contains`), `AlbumTally`, `AlbumAggregate`, and the pure `aggregate_albums`, `aggregate_daily_counts` and `zero_fill_daily_counts`. `lastfm.py` gains `FetchSummary`, `ScrobbleFetch` and `fetch_scrobbles(username, window, progress_cb)`: pages are sorted by their own number, `date.uts` becomes a UTC datetime, and only the timestamp and the three names survive (a missing name is `""`). `heatmap.py` drops `_aggregate_daily_counts` and `_zero_fill_daily_counts` and reads `fetch_scrobbles`; `orchestrator/__init__.py` rebuilds `fetch_top_albums_async` on `fetch_scrobbles` and `plays.aggregate_albums` (same return tuple until task 23d), loses its status-error branch in `_fetch_job_albums` and the imports nothing uses now (`defaultdict`, `datetime`, `Any`, `normalize_name`, `normalize_track_name`), and exports `fetch_scrobbles` in place of `fetch_all_recent_tracks_async`. `tests/test_module_boundaries.py` gets a rule: nothing outside `lastfm.py` names the page-layer functions.

Behaviour changes, each pinned by task 23a's `tests/test_lastfm_job_results.py` and flipped here: (1) `total_scrobbles` no longer counts the now-playing entry; (2) a track object with no `album`, `artist` or `name` key is skipped by the album calculation instead of being counted under the invented name "..."; (3) an unreadable timestamp or a non-object entry is dropped and counted, with a count-only WARNING line, instead of failing the job; (4) a failed Last.fm fetch writes no listening stats before it raises. A fifth, harmless change: plays leave the fetch in page-number order (pages used to arrive in `as_completed` order, so which casing of an album became `original_album` could differ between runs). Accepted cost of (4): a plain Last.fm outage used to end quietly with `Failed to fetch initial page`; it now raises, so it also logs one class-only ERROR line from the handler (`Error processing request for job ...` for an album job, `Unhandled error in heatmap task for job ...` for a heatmap job), carrying a job id and an exception class and no listener data.

Memory (hosting ceiling, budget 20 MB peak added per 80,000-scrobble job; `tracemalloc`, the plan's probe, 400 pages of 200 scrobbles): raw pages held 104.9 MB; plays added 9.6 MB; peak added 10.4 MB. Within budget, so no trim.

Docs: SESSION_CONTEXT Sections 3 to 5 (module list, dependency graph, background_task flow), `docs/architecture/runtime-system.md` (the `Plays` node and four edges), `docs/architecture/top-albums-sequence.md` and `docs/architecture/heatmap-sequence.md` (the failure branch is now a raise, not a status), F-B23-2 resolved, and `BATCH23_DEFINITION.md` WP-2 (the record, the one aggregator, the daily counts). Every added Mermaid line was checked by script (no `;`, participants declared, blocks balanced); the `validate_and_render_mermaid_diagram` tool was not available to the implementer, so the controller rendered `runtime-system.md`, `top-albums-sequence.md` and `heatmap-sequence.md` with the Mermaid validator at 9a8d79c and all three are valid; the two sequence diagrams render once their pre-existing `;` in Note lines (from main, fixed by the documentation PR) are read as commas.

Deviations: the two sequence-diagram Notes the plan wrote contain a `;`, which Mermaid reads as a statement separator, so each uses a comma instead. In `top-albums-sequence.md` the "Aggregation stats" line moves into the `else Pages available` branch, because a failed fetch now writes no stats (the plan did not name it). Edits were byte-safe Python, not `sed -i` (R9). `tests/test_lastfm_job_results.py`'s module docstring still says the five tests are marked xfail; the plan allows only the five marker deletions there, so the sentence is left for the controller.

Edited existing tests: `tests/services/test_lastfm_logic.py` (9 patch strings re-pointed to `scrobblescope.lastfm.fetch_all_recent_tracks_async`; the UTC-window test patches `scrobblescope.plays.datetime`), `tests/test_heatmap.py` (`TestAggregateDailyCounts` moved to `tests/test_plays.py`; 7 pipeline tests re-pointed to `fetch_scrobbles`; `test_upstream_error_sets_job_error` replaced by `test_a_total_lastfm_failure_propagates_to_the_backstop`; `test_lastfm_outage_crash_publishes_lastfm_unavailable` added), `tests/test_provider_fixtures.py` (2), `tests/test_pipeline_integration.py` (1 patch string), `tests/services/test_orchestrator_fetch_and_process.py::test_fetch_and_process_discards_exclusions_on_lastfm_error` (now a raised `ProviderError`), `tests/test_lastfm_job_results.py` (5 xfail markers removed, nothing else), `tests/test_module_boundaries.py` (one rule added). New: `tests/test_plays.py`, and `fetch_scrobbles` tests in `tests/services/test_lastfm_service.py`.

Mutation evidence (scratch copy, each restored afterwards): all 32 plants of the plan's Step 11 table failed the test it names (for example `Play.__post_init__` with `is UTC` failed the three `TestPlay` tests, `window.contains` skip deleted failed `test_a_play_outside_the_window_is_seen_but_not_counted` and Task 1's `test_scrobbles_outside_the_year_are_not_counted`, `datetime.fromtimestamp(int(uts))` without a zone failed 25 tests including `test_a_play_at_2330_utc_keeps_its_utc_day`, the heatmap `try/except ProviderError` failed `test_a_total_lastfm_failure_propagates_to_the_backstop`, a page-layer import in `heatmap.py` failed `test_nothing_outside_lastfm_reads_the_page_layer`). `tests/test_lastfm_job_results.py` reports `23 passed`, no xfail left.

Validation: `pytest -q` -- **2831 passed**.

### 2026-10-20 - Names that cross modules are public

Side task, no batch tag: seven private names become public and the release-check strings get their own leaf module (PR #4 of the pre-Batch-23 tranche, task 23b, architecture-walk-2 B-7), on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: "seams worth doing before feature work are done now" (2026-09-29); the 2026-09-29 rulings allow a seam commit to edit existing tests.

What changed: seven renames, one new leaf, one guard test. `cache.py`: `_get_db_connection`, `_batch_lookup_metadata`, `_batch_persist_metadata`, `_batch_lookup_original_release`, `_batch_persist_original_release`, `_cleanup_stale_metadata` lose their underscore; `domain.py`: `_matches_release_criteria` likewise. Each had a caller in a second package (the orchestrator and the release worker), so a private name said otherwise. The orchestrator facade no longer re-exports `matches_release_criteria`; its one test file imports it from `domain`. `scrobblescope/release_status.py` (new, a leaf) holds the eight `CHECK_*` and `STATUS_*` wire strings; `release_checks.py` imports them and `routes/api.py` reads them from there, so no route imports the thread-owning worker. `tests/test_module_boundaries.py` (new, three tests) walks the source with `ast`: no module reads another package's underscore name, no route imports `release_checks`, and the strings equal what `static/js/results-release-checks.js` compares. SESSION_CONTEXT Sections 3-4 and the runtime-system diagram follow (node `ReleaseStatus`, edges `Routes --> ReleaseStatus` and `ReleaseChecks --> ReleaseStatus`). The Mermaid validator tool was not available to this implementer; the added lines were checked by hand (no `;`, every node declared, block unchanged in shape).

Config-import re-check: a module-level `ast` walk finds 13 modules importing `scrobblescope.config`; as drawn nodes (`routes/` and `orchestrator/` one node each) that is still eleven, and `release_status.py` imports nothing, so the "eleven nodes" paragraph stays true.

Deviations: the drain item of the design was already done (`utils.cancel_and_drain`); the rename was a byte-safe Python script, not the plan's `sed` (R9); in SESSION_CONTEXT Section 4 `release_status` goes after `precheck` in the `routes/api.py` line (PR #3 added `precheck`; alphabetical order). The guard test's first run listed exactly the ten reads the plan predicted. Edited existing tests (renames only, no assertion changed): `tests/services/test_failure_logging.py`, `tests/services/test_orchestrator_fetch_spotify.py`, `tests/services/test_orchestrator_process_albums.py`, `tests/services/test_release_checks.py`, `tests/test_pipeline_integration.py`, `tests/test_repositories.py`, `tests/services/test_cache.py`, `tests/services/test_enrichment.py` (one docstring), `tests/services/test_orchestrator_helpers.py` (renames, and `matches_release_criteria` is imported from `domain`, not the facade).

Mutation evidence (scratch copy, each restored afterwards): `from scrobblescope.utils import _GlobalThrottle` added to `release_checks.py` failed `test_no_module_reads_another_modules_private_name` (named `release_checks`); `from scrobblescope.release_checks import enqueue_release_check` added to `routes/api.py` failed `test_the_routes_never_import_the_correction_worker`; `CHECK_MOVED_OUT = "moved-out"` failed `test_release_status_strings_are_the_ones_the_browser_compares`. Each time `3 passed` once restored.

Validation: `pytest -q` -- **2797 passed**.

### 2026-10-20 - Last.fm usernames leave the log lines

Side task, no batch tag: nine log lines stop carrying a Last.fm username (finding F-B23-40; PR #4 of the pre-Batch-23 tranche, task 2), on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: F-B23-40 and the tranche spec's "Last.fm usernames leave the logs": a handle paired with a scrobble total is a listener-linked fact, and the export path will share this code. The message a browser user reads ("User 'x' was not found on Last.fm.") is not a log line and stays.

What changed: nine lines in four files. Eight username lines: `lastfm.py` (went-private and not-found lines, now fixed text), `heatmap.py` (fetch timing and `_report_heatmap_failure` now name the job id; "Heatmap ready" now reads "Heatmap job <id> is ready" and the scrobble total is gone) and `orchestrator/__init__.py` (the `fetch_top_albums_async` DEBUG start line drops the user; `_fetch_and_process` and `_report_album_failure` name the job id). The ninth is `utils.get_cached_response`'s cache-hit line, which wrote the cache key (it embeds the query string: the API key and `user:<name>`) and now writes the URL only. The `RedactingFormatter` docstring in `api_logging.py` no longer lists the cache-hit line as a carrier. The three route lines that were also in F-B23-40's sweep (registration-year warning, two heatmap pre-check lines) left with PR #3 and are neither changed nor tested here. New `tests/test_log_privacy.py` (7 tests: heatmap run, album run, both thread-entry backstops, both page-layer refusals, the real cache hit). F-B23-40 is marked resolved in `docs/agents/FINDINGS.md` (with the `**Completed:**` line the checker requires, DOC015/DOC016), and `doc_state_sync.py --fix` then rotated it to `docs/history/findings/FINDINGS_ARCHIVE.md`.

Deviations: three existing tests in `tests/services/test_failure_logging.py` (`test_album_pipeline_crash_logs_the_class_only_at_error`, `test_album_backstop_logs_the_class_only_at_error`, `test_heatmap_backstop_logs_the_class_only_at_error`) now also assert the username is absent, through an optional `listener` argument of `_assert_type_only_at_error`. The plan's Step 1b (`tests/test_lastfm_job_results.py::_run_heatmap_task` calling `heatmap_task(job_id)` after PR #3) was already done by the merge of `main`, so this commit does not touch that file. The RED run of Step 2 was not taken before the edits; the mutation table below stands in for it. No other deviation.

Mutation evidence: each of the nine lines restored to its old form in a scratch copy, and each named test failed (`1 failed`) and passed again once restored: went-private and not-found page-layer cases (rows 1-2), `test_a_heatmap_run_logs_its_job_id_not_its_listener` (rows 3-4), `test_the_heatmap_backstop_logs_the_job_id_not_the_listener` and `test_heatmap_backstop_logs_the_class_only_at_error` (row 5), `test_an_album_run_logs_no_listener` (row 6), `test_album_pipeline_crash_logs_the_class_only_at_error` (row 7), `test_the_album_backstop_logs_the_job_id_not_the_listener` and `test_album_backstop_logs_the_class_only_at_error` (row 8), `test_a_cache_hit_logs_no_listener` (row 9).

Validation: `pytest -q` -- **2794 passed**.

### 2026-10-20 - Last.fm-derived job results are pinned before the seam work

Side task, no batch tag: parity tests for the Last.fm path ahead of the scrobbles-not-pages refactor (PR #4 of the pre-Batch-23 tranche, task 23a, review card B-3), on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: "Any new tests should always test intended behavior and not that the func/code works as written." AGENTS.md "Refactor requires parity tests".

What changed: `tests/test_lastfm_job_results.py` runs the album and heatmap pipelines with only the Last.fm HTTP edge faked (`tests/helpers.py`: `FakeLastfm`, `lastfm_edge`, `lastfm_page`, `lastfm_track`, `lastfm_now_playing`) and asserts on the job each one publishes: aggregation across pages, the year and 365-day windows, the now-playing entry, empty names, casing, the partial-run notice, the below-threshold report, inclusive minimums, and the three failure endings (outage, user not found, unreadable entry). Five tests assert behaviour that Task 4 changes by owner ruling (2026-09-29) and are `xfail(strict=True)` until then (5 xfailed, not counted in N).

Deviations: none. No production file changed; no existing test was edited (`tests/helpers.py` gained imports and helpers only).

Mutation evidence: 19 planted defects, each run in a scratch copy and each failing its named test (the table is in the plan, Task 1 Step 4); every test passed again once restored.

Validation: `pytest -q` -- **2608 passed**.

### 2026-10-20 - The Last.fm scrobbles plan opens its branch

Side task, no batch tag: commit the approved plan for PR #4 (normalized Last.fm scrobbles with one album aggregate) as the branch's first commit, on `refactor/lastfm-scrobbles`, a branch off `main`.

Owner intent: "All plans should stay for archival purposes", so every PR plan is its branch's first commit.

What changed: `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md` is added, and PLAYBOOK Section 3's "Before WP-1" bullet gains one sentence naming it. The plan passed a brief review (plan-review.md), a fix round, and a re-review (plan-rereview-1.md) that approved it. One fix was applied at commit time (re-review Minor N1): Task 1's adaptation table said `_run_heatmap_task` calls `heatmap_task(job_id)` after PR #3 without naming the commit. Task 1 lands before #3 merges, so the table row now names Task 2, Task 2's Touches gains `tests/test_lastfm_job_results.py`, and Task 2 gains Step 1b (the one-line call edit, to be named in its commit body and entry).

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2590 passed**.

### 2026-10-20 - Section 3 says PR #3 is done, not under way

Side task, no batch tag: remove the Section 3 sentence that called PR #3 under way, on `refactor/album-request-module`, a branch off `main`.

Owner intent: Section 3 must not say the album request module is both done and under way.

What changed: the "Before WP-1" bullet carried "PR #3, the album request module, is under way" (added with the plan) and "The album request module is done" (added by Task 7). The PR is complete, so the first sentence is deleted; its plan path moves into the "is done" sentence so the path is still named. PR #4's and PR #7's sentences are untouched.

Deviations: none.

Edited existing tests: none.

Validation: `pytest -q` -- **2769 passed**.

### 2026-10-20 - The entry the import-position fix corrected is named

Side task, no batch tag: name the right entry in the record of the import-position fix, and make one test comment true, on `refactor/album-request-module`, a branch off `main`.

Owner intent: a reader following the entry "Two sentences made true after the admission module" must be sent to the entry that really changed.

What changed: that entry says the `admission` import-position phrase was corrected in "The album form is refused with a reason"; it was corrected in "Jobs start through one admission path" (Task 4's entry), which `--fix` has since rotated into `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. Both headings were checked there with grep. The earlier entry is a dated record and is left as written; this entry is the correction. In `tests/test_routes.py` the comment in the failed-thread-start test said the route calls `jobs.delete`; since Task 4 `admission.admit` does, so the comment now says that. Comment only, no code.

Deviations: none.

Edited existing tests: `test_results_loading_thread_start_failure_renders_error`, comment only.

Validation: `pytest -q` -- **2752 passed**.

### 2026-10-20 - No username reaches a pre-check failure log, pinned

Side task, no batch tag: pin by test that no Last.fm username reaches a pre-check failure log, and correct one sentence of the entry "The heatmap and the blur check use the shared pre-check", on `refactor/album-request-module`, a branch off `main`.

Owner intent: Rule 6 (a failure is logged by exception type, never with listener data) must fail a test when broken, not only hold by reading the code.

What changed: new `test_precheck_failure_never_logs_the_listener_name` in `tests/services/test_failure_logging.py` (nine rows: the validate, heatmap and album routes, each with a raising existence lookup, a malformed existence answer and a raising privacy lookup; username `zz-listener-7`; every DEBUG-and-up record is checked for it in message and args). Review found that planting a username log line on the UNAVAILABLE branch of `heatmap_flow.py` or `api.py` left the suite green. The earlier entry said the username "leaves two more log lines" and then named the blur check's line, which never carried it; only the heatmap route's two lines changed, and that sentence now says so.

Deviations: none. No existing test edited; no production code changed.

Mutation evidence (planted in a scratch copy, restored): an error line carrying the username on the UNAVAILABLE branch of `routes/heatmap_flow.py`, of `routes/api.py` and of `routes/album_flow.py` in turn -> three rows of the new test fail each time (the `existence-answer-malformed` and `privacy-lookup-raises` rows among them), then 9 passed once restored.

Validation: `pytest -q` -- **2752 passed**.

### 2026-10-20 - Two sentences made true after the admission module

Side task, no batch tag: correct two sentences that Task 4 of the album request module left untrue, on `refactor/album-request-module`, a branch off `main`.

Owner intent: the shared documents must describe the code that ships, so a reader of SESSION_CONTEXT Section 5 and of the admission entry is not misled about who cleans up and where the import sits.

What changed: SESSION_CONTEXT Section 5 said that on a failed thread start "the route deletes the newly created job"; since the admission module, `admission.admit` deletes it (it calls `jobs.delete` after `start_job_thread` raises), so the sentence now says so. The 2026-10-20 entry "The album form is refused with a reason" said ruff put the `admission` import "after the other `scrobblescope` imports"; in both `album_flow.py` and `heatmap_flow.py` it sits in alphabetical position, and the entry now says that. Both checked against the code before editing.

Deviations: none. No code or test changed.

Validation: `pytest -q` -- **2743 passed**.

### 2026-10-20 - A job says what kind it is

Side task, no batch tag: make the job kind a record field that is never defaulted when read, and amend WP-4 to match, on `refactor/album-request-module`, a branch off `main`.

Owner intent: a record that forgot its kind must not be served as an album run. This is B-12's server half; every writer now sets `mode`, so the default is a trap rather than a convenience.

What changed: the `"album"` default is gone from three sites -- `routes._get_validated_job_context`, `api.release_checks` and `album_flow._extract_job_params` (its unread `mode` entry is deleted) -- and the literals `"album"` and `"heatmap"` become `jobs.MODE_ALBUM` and `jobs.MODE_HEATMAP` (`expected_mode` in `album_flow`, `release_checks`, `_latest_heatmap_job`). New: `test_a_job_that_never_said_its_kind_is_not_served_as_an_album_job` (four rows: `/results`, `/loading`, `/unmatched`, `/api/release_checks`; before this commit all four failed). Seeds that now say `"mode"`: `TEST_JOB_PARAMS` in `tests/helpers.py`; three literals in `tests/test_routes.py`; and the frontend-gate seeds, three in `_frontend_gate_results.py`, one in `_frontend_gate_include.py`, two in `_frontend_gate_spotify_icon.py`. `BATCH23_DEFINITION.md` WP-4 is amended: a "Scope amended 2026-10-20 (pre-Batch-23 tranche, PR #3)" paragraph says WP-4 reuses the album request module, the pre-check and the admission module; the export route's form fields go through `album_request.parse_album_request(form, current_year=..., require_username=False)`; the admission bullet records that `admit(params, target, *, label)` exists, that the thread entry point takes only the job id, that the kind is `params["mode"]` and an export album job keeps `mode` "album" with its origin in `source`; and Acceptance says PR #3 tests the path the album and heatmap routes share while WP-4 adds the export route's. PLAYBOOK Section 3 ("Before WP-1") now says the album request module is done and the other three seams remain; no "Last verified" date and no `Branch:` line moved.

Deviations: none from the brief. Edited existing fixtures, by name: `TEST_JOB_PARAMS` (`tests/helpers.py`) and, in `tests/test_routes.py`, the album literals in `test_results_complete_renders_no_matches_for_empty_results`, `test_results_complete_with_results_renders_data` and `test_results_complete_links_each_row_to_its_own_provider`; no other test needed a `mode`. `ruff format` wrapped the `_latest_heatmap_job` condition over four lines.

Mutation evidence (planted in a scratch copy, named tests failed, restored): `.get("mode", "album")` back in `_get_validated_job_context` -> the `/results`, `/loading` and `/unmatched` rows; the same default back in `release_checks` -> the `/api/release_checks` row. Gates: `frontend_gate.py` 47 checks passed in 75 runs; `results_behavior_tests.py` OK.

Validation: `pytest -q` -- **2743 passed**.

### 2026-10-20 - The figure font constant stops looking like a password

Side task, no batch tag: rename the figure-face gate's `FIGURE_TOKEN` constant, on `feat/ui-consistency`, a branch off `main`.

Owner intent: PR #260 must pass Codacy without suppressing a scanner.

What changed: Codacy's Bandit check (B105, hardcoded password) read `FIGURE_TOKEN = "--font-figure"` in `scripts/dev/_frontend_gate_figures.py` as a credential because the name contains TOKEN. The value is a CSS custom-property name, so the constant is now `FIGURE_FONT_PROPERTY`; its four uses follow. Behaviour and messages are unchanged. The plan under `docs/superpowers/plans/` keeps the old name as an archival record.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2607 passed**.

Side task, no batch tag: correct the figure-face gate module's ledger citation and the FINDINGS test-module count, on `feat/ui-consistency`, a branch off `main`.

Owner intent: the gate's own prose and the project's counts must be true for what the branch ships.

What changed: the docstring of `scripts/dev/_frontend_gate_figures.py` now cites `docs/design/RECONCILIATION.md` section 26 (the play-count override; Task 1 renumbered it because sections 22 to 25 exist) instead of 22, and states the "cannot drift to the wrong face together" clause once instead of twice. The `docs/agents/FINDINGS.md` header now says 87 tracked test modules, the measured `git ls-files tests | grep -c '/test_[^/]*\.py$'`; the earlier commit added a module and left 86 there.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2607 passed**.

### 2026-10-20 - The gate holds the Results play count to the figure face

Side task, no batch tag: add a frontend-gate check that the Results play count wears the heatmap's figure face, on `feat/ui-consistency`, a branch off `main`.

Owner intent (tranche design, "UI PR (#7)"): a frontend-gate check asserts that the computed font of a results play count equals that of a heatmap KPI value, at every viewport the gate runs.

What changed: new `scripts/dev/_frontend_gate_figures.py` (`check_results_play_count_uses_the_figure_face`, registered in `scripts/dev/frontend_gate.py` as "results play count figure face" for the desktop, mobile and wide-touch profiles, Chromium only) and `tests/scripts/dev/test_frontend_gate_figures.py` (16 tests). Why: the serif count shipped beside a Gotham KPI and nothing could see it. The check reads the computed family and weight of every play count, on load and after the sort is switched (results.js rebuilds the cell), and requires them to equal the heatmap KPI value's; it also requires that KPI value to be the `--font-figure` token at weight 400, so the pair cannot drift to the wrong face together; an empty selection fails instead of passing. At the mobile profile only it also requires the seeded four-digit count to keep its right edge inside its cell (the guard for Task 1's narrow-screen sizing). The module is documented in SESSION_CONTEXT (tree and import lines), `docs/architecture/documentation-tooling.md` (count fifteen, list, Mermaid) and DEVELOPMENT.md.

Mutation (unit, scratch copy, each planted defect failed its named tests): weight branch deleted -> `test_a_bold_play_count_fails_even_in_the_right_face`; family branch -> serif, one-wrong-among-many and rebuilt-cell tests; reference early return -> the two reference tests; both empty-selection returns -> `test_no_kpi_and_no_play_count_each_fail_rather_than_pass_vacuously`; second face call -> `test_a_cell_rebuilt_by_a_sort_switch_is_judged_again`; `>` to `<` -> three fit tests; `if narrow:` guards -> `test_at_a_desktop_width_the_fit_is_not_judged`; second fit call and `jobs.delete(heatmap_job)` -> their named tests.

Live probe (scratch tree, real Chromium; the worktree CSS untouched): old face planted -> at every profile `play count on load is set in 'instrument-serif,corporate-a,Georgia,serif', the heatmap KPI value in 'gotham,ff-din-paneuropean,ui-sans-serif,sans-serif'` and the same `after switching sort`; bold planted -> `play count on load has font weight 700, the heatmap KPI value 400` (and after switching sort) at every profile; the `data-digits="4"` rule removed -> `[mobile] play count 8080 on load ends 10.0px past the cell it sits in` and the same after switching sort, desktop and wide touch PASS. The worktree passes at all three profiles.

Deviations: none in the code. The check adds 3 planned runs (Firefox runs only the assets canary). The Mermaid block was edited by one node line and one class-list entry in the file's existing pattern; no external validator was run.

Edited existing tests: none.

Validation: `pytest -q` -- **2607 passed**. Gate: `[frontend_gate] 48 checks passed in 78 runs across chromium, firefox (static assets & tokens canary on firefox); profiles: desktop, mobile, wide touch`.

### 2026-10-20 - The Results play count is set in the figure face

Side task, no batch tag: set the Results table's play count in the figure face, on `feat/ui-consistency`, a branch off `main`.

Owner intent (tranche design, "UI PR (#7)"): "the results table's play count uses the figure face (`--font-figure`, Gotham, weight 400 -- never bold, as the heatmap KPI rule records)"; `DESIGN.md` gives play counts to the Figure Numerals.

What changed: `.metric-val-plays` in `static/css/results.css` takes `--font-figure` at `--font-weight-normal` with `font-variant-numeric: tabular-nums` (set because `DESIGN.md` decides tabular Figure Numerals); size, line height, colour and letter-spacing are untouched. `docs/design/RECONCILIATION.md` gains a Section 1 row and section 26 recording the override of the snapshot's "mono value". Measured with a scratch script at all three gate profiles, both themes: Gotham served (one face fetched; 357.9px against 321.6px for the fallback); before, every play count computed `instrument-serif`, after, `gotham` at weight 400, colour equal row by row, size equal, every row height unchanged (81.2px desktop and wide touch, 73px mobile). Gotham has `tnum` (default 1111 vs 0000 = 34.4 vs 68.6px, with tabular-nums both 57.6px). Four digits did not fit at full size on mobile: 8080 measured 54px against a 44px room (407: 40.5px, fits), so Step 5b applied by the controller's ruling (one-attribute template edit): the plays span carries `data-digits` (`templates/results.html`, rebuilt by `renderMetric` in `static/js/results.js` on a sort switch), and under 768px only, a 4-digit count is set at 1.093rem and a 5-digit one at 0.874rem (widest digit d = 0.6003em, room R = 44px, S(n) = floor((R - 2) / (n * d) / 16)), 6 or more at the 0.75rem floor. After: 8080 and 88888 measure 41.95px in 44px; 888888 measures 43.2px in 44px at the floor (fits, but with under the 2px spare, so fit is not promised for six digits). Desktop and wide touch widths and sizes, and mobile rows of one to three digits, are identical to the full-size measurement.

Deviations: the master plan named `.metric-value`; the rule is `.metric-val-plays`. The plan numbered the RECONCILIATION section 22, but sections 22 to 25 already exist, so the override is section 26 (row, CSS comment and prose follow). Section 26 includes the plan's conditional narrow-screens paragraph, because Step 5b applied.

Edited existing tests: none. New test: `test_each_play_count_states_how_many_digits_it_has` in `tests/test_routes.py`; with the template's `data-digits` planted as a constant `"4"` in a scratch copy it failed on the 407 assertion, and it passes on the real template.

Validation: `pytest -q` -- **2591 passed**.

### 2026-10-20 - The UI consistency round 1 plan opens its branch

Side task, no batch tag: add the approved UI consistency round 1 plan, on `feat/ui-consistency`, a branch off `main`.

Owner intent (2026-10-20): "All plans should stay for archival purposes", so every PR plan is its branch's first commit.

What changed: `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md` is added, and PLAYBOOK Section 3's "Before WP-1" bullet gains one sentence naming PR #7 and the plan. The plan passed a brief review (plan-review.md), three fix rounds, and two re-reviews (plan-rereview-1.md, plan-rereview-2.md); the last approved it.

Deviations: the plan is committed as approved. The one commit-time fix (plan-rereview-2 Minor 1, Step 5b item 4 must say to replace the single line and keep the `else` braces) was already present in the approved draft, so no further wording change was made. No DOC-driven wording change was needed. No test was edited.

Validation: `pytest -q` -- **2590 passed**.

### 2026-10-20 - The heatmap and the blur check use the shared pre-check

Side task, no batch tag: answer the heatmap start and the blur check from the shared Last.fm pre-check, on `refactor/album-request-module`, a branch off `main`.

Owner intent: the last two hand-written copies of the Last.fm existence and privacy check go, so the album form, the heatmap start and the blur check read one Last.fm answer one way.

What changed: `_validate_heatmap_user` (`routes/heatmap_flow.py`) and `validate_user` (`routes/api.py`) call `precheck.check_lastfm_user` and keep only their own response shapes. No visible behaviour change: statuses and bodies are pinned by the cross-route table in `tests/test_precheck_routes.py`. New there: `test_a_malformed_last_fm_answer_is_unavailable_on_every_route` (nine rows; before this commit the three heatmap rows failed, a bad body being a 500 there, and `validate` read `"yes"` as an existing user). The Last.fm username leaves two more log lines: the heatmap route's two failure lines no longer carry it (the blur check's line never did; it is now the pre-check's class-only line) (note for the lastfm-scrobbles PR: they need not be counted under F-B23-40). SESSION_CONTEXT Sections 3-4 follow; no diagram changes.

Deviations: none from the brief. Edited existing test, by name: `tests/services/test_failure_logging.py::test_validate_user_failure_logs_the_class_only_at_error` now expects the fragment "User existence check failed" (was "Username validation failed").

Mutation evidence (planted in a scratch copy, named tests failed, restored): `Verdict.PRIVATE` mapped to the heatmap 404 branch -> `test_every_route_reads_the_last_fm_answer_the_same_way[private-heatmap]`; `Verdict.UNAVAILABLE` answered 200 `valid: True` in `validate_user` -> `[outage-on-existence-validate]` and `[outage-on-privacy-validate]`; `registered_year` dropped from the success payload -> `test_validate_user_success`; `exists` read outside the `try` in `check_lastfm_user` -> all nine rows of the malformed-answer test.

Validation: `pytest -q` -- **2739 passed**.

### 2026-10-20 - The album form is refused with a reason, never started doomed

Side task, no batch tag: the album route parses the form, pre-checks the Last.fm user, then admits the job, on `refactor/album-request-module`, a branch off `main`.

Owner intent: a listener who submits a value the form never offers, or who submits while Last.fm cannot answer, should be told why on the form instead of seeing "no albums" or a job that fails later.

User-visible changes: (1) a filter value the form never offers is refused on the form with that field's sentence and no Last.fm lookup, including a `custom` scope without a year and a `decade` scope without a decade, which used to widen to every year; (2) an outage or timeout of the Last.fm pre-check, or an existence answer of the wrong shape, is refused with a retryable HTTP 503 ("Validation service unavailable. Try again.") instead of logging "proceeding" and starting a job that fails. Also stricter or different than before: the form's own ranges are now enforced on the server (`min_plays` 1-50, `min_tracks` 1-10, release year 1900 to this year, username up to 64 characters, the `/validate_user` limit; the form input allows 100 but a Last.fm name is far shorter); a blank `min_plays` or `min_tracks` now takes its default (before, the form answered "Year must be a valid number."); the username is stripped of surrounding spaces; a whitespace-only username is refused ("Username and year are required."). The listener's name no longer appears in the album route's log lines (the pre-check logs the exception class only).

What changed: `results_loading` calls `parse_album_request`, `precheck.check_lastfm_user`, `registration_refusal` and `admission.admit`, in that order, through one `_refuse` helper; the job record is written by `AlbumRequest.to_params()`, so it carries `mode: "album"`. New `tests/test_album_request_flow.py` and `tests/test_precheck_routes.py` (the album, heatmap and validate routes read one Last.fm answer the same way, and a stalled Last.fm costs each its budget). SESSION_CONTEXT Sections 4-5, `runtime-system.md` (edge `Routes --> AlbumRequest`) and `top-albums-sequence.md` follow. The Mermaid MCP validator was not available to the implementer; the edited diagram lines contain no `;` and the controller validates the two files.

Deviations: none from the brief. Edited existing tests, by name: `test_results_loading_registration_check_unavailable_proceeds` is replaced by `test_results_loading_lookup_unavailable_refuses_and_starts_nothing`; `test_results_loading_registration_check_failure_logs_no_message` is renamed `test_results_loading_lookup_failure_logs_no_message_and_no_name` and now asserts "User existence check failed" and that `flounder14` is absent from the log; in `tests/test_pipeline_integration.py::test_album_pipeline_runs_on_a_real_thread_end_to_end` the `check_user_exists` mock gains `"exists": True` (the old mock had no `exists` key and passed only because the route swallowed the `KeyError`; a malformed Last.fm answer is now an outage). The Retry contract, `tests/test_loading_retry_contract.py` (PR #256 is in the base), now reads `scrobblescope.album_request.FORM_FIELDS` instead of scanning `results_loading`, drops its `ast` helper and keeps the loading-config and `retryCurrentSearch` checks; `test_route_fields_are_found` asserts `"include_unmatched" in FORM_FIELDS and len(FORM_FIELDS) == 10`. `FORM_FIELDS` is the list that contract reads.

Mutation evidence (each planted defect, then the named tests failed, then restored): the decade membership check removed in `album_request.py` -> `test_a_bad_filter_is_refused_on_the_form_and_starts_nothing[overrides1-Choose a decade from the list.]`; the `UNAVAILABLE` branch removed from `album_flow.py` -> both `test_a_pre_check_outage_refuses_retryably_and_starts_nothing` rows, the three malformed-answer rows and the album outage and stalled rows of `tests/test_precheck_routes.py`; params built without `mode` -> `test_an_album_job_record_says_it_is_an_album_job`; `exists` read outside the `try` in `check_lastfm_user` -> the three malformed-answer rows and `tests/test_precheck.py::test_a_malformed_existence_answer_is_unavailable_never_an_error`; privacy asked first -> `test_every_route_reads_the_last_fm_answer_the_same_way[missing-album]` and `tests/test_precheck.py::test_a_missing_user_is_missing_and_privacy_is_never_asked`; `timeout=` dropped from `_check_user_exists` -> `test_a_stalled_last_fm_costs_a_route_its_budget_not_the_session` (all three rows) and `tests/test_precheck.py::test_a_stalled_last_fm_lookup_gives_up_within_the_precheck_budget`; `"source"` added to `FORM_FIELDS` -> all three tests of `tests/test_loading_retry_contract.py`.

Validation: `pytest -q` -- **2730 passed**.

### 2026-10-20 - Jobs start through one admission path

Side task, no batch tag: start every job through one admission path and let job threads read the job record, on `refactor/album-request-module`, a branch off `main`.

Owner intent: the album and heatmap routes each wrote expire, slot, create, start, delete-on-failure by hand, and the export route (WP-4) would have been a third copy; the ten album parameters were also re-passed positionally to a thread although the job record already holds them.

What changed: new `scrobblescope/routes/admission.py` (`Refused.CAPACITY` / `START_FAILED`, `admit(params, target, *, label)`); `jobs.params(job_id)` (a copy of the params, `None` for a gone job, never renews the lease); `background_task(job_id)` and `heatmap_task(job_id)` read their parameters from the record, through `AlbumRequest.from_params` for the album run (new `_album_request_for`); a job that is gone, or a record that is not a usable request, runs nothing, still frees the slot the route took, and the unusable record ends as `internal_error`. `results_loading` and `_dispatch_heatmap_job` call `admit` and keep their own parsing, session key and HTTP answers; the thread is started as `start_job_thread(target, args=(job_id,))`. No listener-visible change. SESSION_CONTEXT Sections 3-5 and the runtime, top-albums and heatmap architecture files follow. The Mermaid MCP validator was not reachable from this session, so the edited diagram lines were checked by eye (no `;` in any message).

Mutation evidence (each planted defect, then the named test failed, then restored): `jobs.create` before the slot -> `test_a_full_house_refuses_and_creates_nothing`; `jobs.delete` removed -> `test_a_thread_that_will_not_start_leaves_no_orphan_job`; `jobs.expire_stale()` removed -> `test_admission_drops_expired_jobs_first`; min plays/tracks defaults passed -> `test_background_task_runs_the_pipeline_with_the_job_records_parameters`; vanished-job release dropped -> `test_background_task_for_a_vanished_job_runs_nothing_and_frees_its_slot` and `TestHeatmapTask::test_a_vanished_job_runs_nothing_and_frees_its_slot`; `jobs.fail` dropped from `_album_request_for` -> `test_background_task_for_an_unusable_record_fails_the_job_and_frees_its_slot`; a second release in `admit` -> `test_a_real_thread_start_failure_frees_the_slot_once_and_removes_the_job`; the stored dict returned from `jobs.params` -> `test_params_returns_a_copy_and_none_for_a_missing_job`; a literal heatmap name -> `TestHeatmapTask::test_the_username_comes_from_the_job_record`; the flag left out of the album job record -> `test_results_loading_passes_the_include_flag_to_the_job_thread`.

Deviations: the plan's `heatmap_flow` and `album_flow` code was applied as written; `ruff` placed the new `admission` import in alphabetical position among the `scrobblescope` imports in both route modules. Edited existing tests, by name: in `tests/services/test_orchestrator_fetch_and_process.py` the six `background_task` call sites (`test_background_task_runs_single_event_loop`, its call and its name assertion now `testuser`; `test_background_task_releases_slot_on_exception`; `test_background_task_releases_slot_when_event_loop_setup_raises`; `test_background_task_releases_slot_when_loop_close_raises`; `test_background_task_crash_publishes_internal_error`; `test_background_task_stores_unmatched_rows_when_the_flag_is_on`); the seven `heatmap_task(` calls in `tests/test_heatmap.py` `TestHeatmapTask` (`test_release_job_slot_called_on_success`, `..._on_exception`, `..._when_event_loop_setup_raises`, `..._when_loop_close_raises`, `test_unhandled_crash_publishes_internal_error`, `test_user_not_found_crash_publishes_user_not_found`, `test_untyped_not_found_text_is_ours_not_user_not_found`); and `tests/test_routes.py::test_results_loading_passes_the_include_flag_to_the_job_thread` (docstring and the args assertion). The failed-thread-start path is tested for real, not patched, in `tests/test_admission.py`.

Validation: `pytest -q` -- **2699 passed**.

### 2026-10-20 - Last.fm pre-check lookups have a time limit and one answer

Side task, no batch tag: give the Last.fm pre-check one shared answer and a short timeout, on `refactor/album-request-module`, a branch off `main`.

Owner intent: a slow Last.fm must not hold a request thread for a minute, and the three routes must agree on what a failed check means.

What changed: new `scrobblescope/routes/precheck.py` (`Verdict`, `UserCheck`, `check_lastfm_user`, `UNAVAILABLE_MESSAGE`, `not_found_message`); `utils.run_async_in_thread(coro, timeout=None)` cancels the coroutine and raises `TimeoutError` in the calling thread; `config.LASTFM_PRECHECK_TIMEOUT_SECONDS` (default 5, env of the same name); the `routes` facade's `_check_user_exists` and `_check_profile_is_public` pass it. Why: each of the three routes called the same two checks and handled failure its own way, and none had a limit but the HTTP session's 30 seconds per call (two calls: up to 60 seconds of one of four request threads). User-visible change now: the heatmap start and the blur check refuse after at most 5 seconds per lookup; the album route still swallows an outage until the next commit switches it over. The username leaves the pre-check's failure lines (class name only), and a malformed Last.fm existence answer (not a mapping, no boolean `exists`, a non-integer `registered_year`) is an outage (`UNAVAILABLE`), not a 500. SESSION_CONTEXT Sections 3-4 and the key runtime facts name the module and the setting.

Mutation evidence (each planted defect, then the named test failed, then restored): timeout ignored in `run_async_in_thread` -> `test_run_async_in_thread_stops_waiting_when_the_timeout_passes`; `timeout=` dropped in `_check_profile_is_public` -> `test_a_stalled_last_fm_lookup_gives_up_within_the_precheck_budget[_check_profile_is_public-...]`; privacy `except` returns PUBLIC -> `test_an_outage_on_the_privacy_check_is_unavailable_never_public`; existence read outside the `try` -> `test_a_malformed_existence_answer_is_unavailable_never_an_error[none]`; `.get("exists")` truthiness -> the same test, `empty` row; privacy asked before existence -> `test_a_missing_user_is_missing_and_privacy_is_never_asked`; username in the failure line -> `test_a_failed_check_logs_the_class_and_never_the_listeners_name`.

Deviations: none. No existing test was edited; two tests were added to `tests/test_utils.py` and the new module `tests/test_precheck.py` has 17 cases.

Validation: `pytest -q` -- **2688 passed**.

### 2026-10-20 - Task 1's drift note and the module count are corrected

Side task, no batch tag: correct a false drift note and the tracked test-module count, on `refactor/album-request-module`, a branch off `main`.

Owner intent: the log and findings must be true for what the branch ships.

What changed: the Deviations paragraph of the "The request flows are pinned before they are refactored" entry said `_dispatch_heatmap_job` was gone and heatmap job creation was inline. It is not: the function exists in `scrobblescope/routes/heatmap_flow.py` and calls `acquire_job_slot`, so there was no drift for the heatmap mutation; the paragraph now says so (the privacy-outage note was checked and stands: `_validate_heatmap_user`). The `docs/agents/FINDINGS.md` header line said 87 tracked test modules; `git ls-files tests | grep -c '/test_[^/]*\.py$'` measures 88, so it now says 88. The review of Task 1 found both.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2669 passed**.

### 2026-10-20 - The album form has one owner

Side task, no batch tag: add the pure album request module (not yet wired into any route), on `refactor/album-request-module`, a branch off `main`.

Owner intent: the album form needs one Python owner that says what a valid request is, so the Spotify export route (WP-4) can call it too.

What changed: new `scrobblescope/album_request.py` (`AlbumRequest`, `Refusal`, `parse_album_request`, `registration_refusal`, the sets and bounds, `FORM_FIELDS`), `jobs.MODE_ALBUM` and `jobs.MODE_HEATMAP`, and 63 tests in new `tests/test_album_request.py`, which also read `templates/index.html` and fail if the form and the server drift. Why (B-1): the sets lived only in the template, so a bad decade made every album fail the release filter and the listener saw "no albums". Once wired, these refusals are new: unknown release scope, unknown decade, missing or malformed custom release year, unknown ranking, unknown limit, min_plays outside 1-50, min_tracks outside 1-10, username over 64. The bound of 64 is the limit `/validate_user` already enforces; the form's `maxlength` is 100. SESSION_CONTEXT Sections 3-4 and the runtime-system diagram (node, `AlbumRequest --> JobModule` edge) name the module.

Mutation proofs, each planted in a scratch copy and shown failing then passing once restored: year bound `<=` to `<` (year 2025 rows fail), decade membership check removed (decade rows), custom year no longer required (`Enter a release year.` row), include/playtime coercion removed, decade kept for every scope, min_plays upper bound 100 (51 row), blank no longer a missing field (defaults test), unknown registration year refused, `"100"` dropped from `LIMIT_OPTIONS` (limit 100 row), parser reading `source` and `"decade"` dropped from `FORM_FIELDS` (FORM_FIELDS test), `"fortnight"` added to `RELEASE_SCOPES` (release-window test).

Deviations: none from the plan. The runtime-system Mermaid block was not run through the render MCP call (not available to this implementer); the edit adds one node, one edge and one class-list name only. No existing test was edited.

Validation: `pytest -q` -- **2669 passed**.

### 2026-10-20 - The request flows are pinned before they are refactored

Side task, no batch tag: add parity tests for the album, heatmap and validate_user request flows, on `refactor/album-request-module`, a branch off `main`.

Owner intent: tests assert intended behaviour, and AGENTS.md "Refactor requires parity tests" puts them before PR #3 changes the code behind these routes.

What changed: new `tests/test_request_flow_parity.py` (16 tests, tests only, no source change). It pins which form fields land in the job record per release scope, that the values reach the album and heatmap pipelines in the right slots, the inclusive 2002 and current-year bounds, that a full house leaves no job behind, and the bodies of the heatmap privacy-outage and validate_user outage answers. It deliberately does not pin the fail-open pre-check or the positional thread arguments, which later tasks replace. Mutation proofs, each planted in a scratch copy and shown failing then passing once restored: decade kept whatever the scope (custom and previous rows fail), min_plays and min_tracks swapped in the orchestrator call, username no longer stripped in heatmap_loading, `year < 2002` made `<=`, the heatmap job created before the slot is acquired, the heatmap privacy-outage `retryable` set False, and the privacy check asked before existence in validate_user.

Deviations: plan drift only. The plan names `background_task` and `_dispatch_heatmap_job`; the tree has the `_fetch_and_process` call inside `background_task` in `scrobblescope/orchestrator/__init__.py` (found as planned) and `_dispatch_heatmap_job` also exists in `scrobblescope/routes/heatmap_flow.py` (it calls `acquire_job_slot` and then creates the job), so the heatmap mutation was planted there as the plan says and there was no drift for it. The one placement difference found: the heatmap privacy-outage answer lives in `_validate_heatmap_user` in the same file. (This entry first said `_dispatch_heatmap_job` was gone; that was false and is corrected here.) Behaviour and test code are as planned. No existing test was edited.

Validation: `pytest -q` -- **2606 passed**.

### 2026-10-20 - The album request module plan opens its branch

Side task, no batch tag: add the album request module plan as the branch's first commit, on `refactor/album-request-module`, a branch off `main`.

Owner intent: "All plans should stay for archival purposes", so every PR plan is the first commit of its own branch.

What changed: `docs/superpowers/plans/2026-10-20-album-request-module.md` is the owner-approved plan for PR #3, and PLAYBOOK Section 3's "Before WP-1" bullet names it. The plan passed a brief review (plan-review.md), a fix round, and a re-review (plan-rereview-1.md) that approved it. One fix was applied at commit time (re-review Minor N1): the three pointers to the Retry rule now all read "Task 5 Step 4, item 4" (the assumptions row and Task 2 Interfaces said "Task 5 Step 5"; Task 5 Touches said "Step 4, item 3").

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2590 passed**.

### 2026-10-20 - The test-module count counts both sides of the merge

Side task, no batch tag: correct the tracked test-module count in SESSION_CONTEXT and FINDINGS, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: PLAYBOOK, SESSION_CONTEXT and FINDINGS must be up to date, so a hand-kept figure must match the tree.

What changed: both files said 85 tracked test modules. main and this branch each added one module to a base of 84 (PR #256's retry-contract test, and `tests/test_requirements_split.py`), and the merge kept 85. `git ls-tree -r --name-only HEAD tests` counts 86, so both lines now say 86.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2590 passed**.

### 2026-10-20 - The master plan records the agent cap and the #5/#6 order

Side task, no batch tag: record two owner rulings in the tranche master plan, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the plan that orders the tranche must say what the owner ruled, so a later session does not work from the superseded text.

What changed: `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` now allows at most ten subagents at once (the owner's words are quoted), and says PRs #5 and #6 touch disjoint files, so their code phases may overlap, with #5 landing first only if #6 later needs `_results.py`. The design spec is left as written: it is the owner-approved dated design.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2590 passed**.

### 2026-10-20 - Section 3 names the pre-Batch-23 tranche's spec and plan

Side task, no batch tag: point PLAYBOOK Section 3 and SESSION_CONTEXT at the tranche's spec and master plan, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: an agent that reads Section 3's "Before WP-1" bullet should find the design and the PR order without searching.

What changed: PLAYBOOK Section 3's "Before WP-1" bullet gains one sentence naming `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`. SESSION_CONTEXT's Batch 23 status row names the spec path after the existing "side-task PRs runs" sentence. Both documents come from this branch and are committed on it.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2590 passed**.

### 2026-10-20 - Hygiene entries corrected after review

Side task, no batch tag: three wording and count fixes to the hygiene commits, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the per-task reviews found documentation on this unpushed branch that was loose or false, so correct it before the PR rather than leave it.

What changed: (1) `docs/agents/FINDINGS.md` header said 84 tracked test modules; the requirements-split test added a module, so the measured count is 85 (SESSION_CONTEXT's Tests row already said 85). (2) The Task 2 claim that "nine of the ten scripts in `static/js/` already" use hyphens was wrong, since only three names contain a hyphen; it now says `page_motion.js` was the only script name with an underscore, in the `page-motion.js` entry and in the hygiene plan's Task 2 "Why". (3) The Python 3.13 spellings entry now names the edited existing tests and mentions the `except` tuple reorder in `scrobblescope/spotify.py`.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2543 passed**.

### 2026-10-20 - Ruff judges the code as Python 3.13

Side task, no batch tag: ruff's `target-version` set to `py313`, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the Dockerfile and CI run Python 3.13, so ruff should judge the code against it (tranche design, PR #2).

What changed: `pyproject.toml` `[tool.ruff]` gains `target-version = "py313"`, so the UP rules see 3.13 idioms and the import sorter files `tomllib` as standard library. `ruff check --select I001 --fix` moved that import into the stdlib group in `scripts/dev/docsync_preflight.py`, `scripts/dev/frontend_gate.py`, `scripts/docsync/cli.py` and `scripts/docsync/declarations.py`. UP036 then flagged the `sys.version_info < (3, 12)` block in `docsync_preflight.py`; it is a deliberate refusal for an extracted copy of the control plane run on older Python, so it stays, marked `# noqa: UP036` with the reason in the comment above. The change is lint-only: import order and one comment, no behaviour.

Control plane: the commit stages `scripts/dev/docsync_preflight.py`, `scripts/docsync/cli.py` and `scripts/docsync/declarations.py` (with `scripts/dev/frontend_gate.py`), and the docsync preflight refuses control-plane files outside `[test_count]` by design (exit 3). It was committed through the documented escape, `SKIP=doc-state-sync-check git commit`, and `doc_state_sync.py --check` was run straight after (exit 0). `--no-verify` was not used.

Deviations: the brief's trailing `# noqa: UP036 -- reason` would have pushed the line past 88 characters and ruff-format would have split the tuple, so the reason sits in the comment above and the old `# pragma: no cover - CI pins 3.13` text moved there too, ahead of a shortened `# noqa: UP036  # pragma: no cover`. No existing test was edited.

Validation: `pytest -q` -- **2543 passed**.
