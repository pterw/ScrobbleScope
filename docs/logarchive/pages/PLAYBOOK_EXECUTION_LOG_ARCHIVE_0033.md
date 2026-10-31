<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0033

### 2026-10-25 - Close the album-matching findings

Side task, no batch tag: close F-B23-26 and F-B23-59 to F-B23-63 and update the Section 3 sentence for PR #270, on `fix/album-matching`, stacked on PR #269.

Owner intent: each finding the album-matching plan files is closed with the commit that fixed it: F-B23-26 (`7aeafa90`), F-B23-59 (`2561e4cd`, with the cached wrong matches clearing on read by `f546a0bf`, `4892ca8a` and `1cc4d33d`), F-B23-60 (`3c2694c3`), F-B23-61 (`0237a840`), F-B23-62 (`5d9e561a`) and F-B23-63 (`2b7e95ad`). Section 3 now says every plan task has landed on PR #270 and the PR waits on the owner's real run and review, because it is not merged.

Deviations: none.

Edited existing tests: none.

Validation: `pytest -q` -- **2941 passed**.

### 2026-10-25 - Describe exact album matching and the MusicBrainz spacing

Side task, no batch tag: sweep the live prose for the album-matching behaviour and the MusicBrainz request spacing, on `fix/album-matching`, stacked on PR #269.

Owner intent: keep the docs true after PR #270's code changes. Spotify's album search asks for 5 candidates and keeps only an exact title and credited-artist match, a cached Spotify row whose stored names fit another album is dropped as a miss, an older row without names is checked once by its cached ID, two albums sharing a Spotify ID each get their own metadata, and the correction worker starts MusicBrainz requests about 1.1 seconds apart (policy: one per second). Edited: `README.md` (Top Albums feature, listening-time rule and limitation, spotlight artist match, the 1.1 second spacing in four places including the flowchart edge, one cached-match limitation), `docs/architecture/top-albums-sequence.md` (cache lookup and search steps, shared-ID sentence), `docs/architecture/runtime-system.md` (edge label, cache-hit sentence), `docs/agents/AGENT_NOTES.md` (`updated_at` on a stamped row), and the comment in `static/js/results-release-checks.js`. Mermaid blocks edited: the README Architecture flowchart (`flowchart TB` edge to the correction worker), the `top-albums-sequence.md` sequenceDiagram, the `runtime-system.md` MusicBrainzClient edge.

Deviations: none. The MusicBrainz policy lines, other providers' rates and dated entries were left as they are.

Edited existing tests: none.

Validation: `pytest -q` -- **2941 passed**.

### 2026-10-25 - Check an old cached Spotify row by its ID once

Side task, no batch tag: rows cached before the provider-name columns are checked once by their cached Spotify ID (RB1), on `fix/album-matching`, stacked on PR #269.

Owner intent: an old cached row carries no provider names, so a wrong match could not be told from a right one. A job now fetches the unstamped Spotify rows by their cached ID (Get Several Albums, chunks of 20 under `spotify_job_breaker`, never Search), keeps and persists the ones whose names fit the request key, and sends the rest to a miss. When Spotify cannot answer (no token, an unanswered ID) or the cache write fails, the row is used unchanged and not rewritten. One counts-only log line reports kept, stamped, dropped and unanswered. The code is in `scrobblescope/orchestrator/_cache.py`. A fix round added the persist-failure case after review.

Deviations: none from the brief. Accepted review Minor items, not fixed: (1) the use of `spotify_job_breaker` in the stamping fetch has no test; (2) `on_fallback` is not passed to the details batch call, so the single-album fallback is not warned about in this path; (3) the older-row parity test now asserts values from the stamped details, and ID de-duplication before chunking is untested; (4) an unexpected exception in the stamping fetch is not caught and would fail the job rather than fail open.

Edited existing tests: `test_process_albums_cache_hit_skips_spotify`, `test_process_albums_applies_cached_original_release_before_filtering`, `test_process_albums_records_provider_date_on_an_uncorrected_exclusion`, `test_process_albums_partial_cache_token_failure_uses_cached_results` and the `_split_stats` helper (feeds `test_loading_stats_split_the_passed_albums_into_hits_and_misses`) in `tests/services/test_orchestrator_process_albums.py`, and `test_fetch_and_process_loading_stats_count_only_albums_that_passed` in `tests/services/test_orchestrator_fetch_and_process.py`: seeded Spotify rows now carry `provider_artist`/`provider_title` fitting the key. In `tests/test_album_cache_parity.py` the `_spotify()` fake now details each album with name and credit (new `CREDITS` map), `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` expects the stored names, and `test_an_older_spotify_row_reads_as_a_spotify_album_with_the_classic_link` uses `_spotify()` instead of `_providers_forbidden()` because an old row is now stamped by one details call (the intended RB1 change); `test_a_search_costs_one_connection...` and `test_a_musicbrainz_finding...` pass through the fake change only. Each still asserts what it meant. Fix round: new case `persist_fails` added to `test_unstamped_rows_stay_unchanged_and_unwritten_when_spotify_cannot_answer`.

Validation: `pytest -q` -- **2941 passed**.

### 2026-10-25 - Stop shadowing the credits builtin

Side task, no batch tag: rename the `credits` local in `matching_credit` (Codacy finding on PR #270, Pylint W0622 redefined-builtin), on `fix/album-matching`, stacked on PR #269.

Owner intent: Codacy flagged `credits = item.get("artists") ...` in `scrobblescope/spotify.py` as shadowing the `credits` builtin that `site` installs; it was introduced by the exact-match search change. The local is now `credited_artists`, used only inside `matching_credit`. Rename only, no behaviour change. A grep for `credits`, `copyright`, `license`, `exit` and `quit` assignments in `scrobblescope` found no other shadowing local.

Deviations: none.

Edited existing tests: none.

Validation: `pytest -q` -- **2932 passed**.

### 2026-10-25 - Give requests sharing a Spotify ID their own metadata

Side task, no batch tag: two requests that resolve to one Spotify ID each get their own metadata (D2, RB3), on `fix/album-matching`, stacked on PR #269.

Owner intent: a collaboration credited under two artists produced two keys mapped to one Spotify ID; the second overwrote the first in the ID-to-key map, so the loser fell to Deezer. `_run_spotify_search_phase` now returns a fifth element, `shared_id_requests` (the extra requests after the first for a mapped ID), and logs one count-only warning. `_run_spotify_batch_detail_phase` takes it and builds metadata per key with `album_metadata_from_details(spotify_id, details, key)`, filing each in `cache_hits` and `new_metadata` so each stored credit matches its own key; when an ID is unanswered, the extras join `detail_unavailable_keys`. `_fetch_spotify_misses` unpacks five values and passes the mapping. One fix round after review added a test guarding the `_fetch_spotify_misses` wiring and a privacy assertion on the warning (no names, no key parts). Recorded, not fixed: the warning fires once per extra request, which no three-key case pins.

Deviations: none. Task 9 (`AlbumCache.lookup` drops a mismatched row) landed first; the files are disjoint and the patch applied cleanly on it. Findings are not closed here; Task 11 closes them.

Edited existing tests: `test_run_spotify_search_phase_all_misses_returns_empty_maps` (also asserts `shared_id_requests == {}`) and `test_spotify_search_unanswered_album_does_not_cancel_its_siblings` (unpacks five values). New: `test_two_requests_sharing_a_spotify_id_each_get_their_own_metadata`, `test_unanswered_details_for_a_shared_spotify_id_mark_every_key`, `test_fetch_spotify_misses_credits_every_key_sharing_a_spotify_id`.

Validation: `pytest -q` -- **2932 passed**.

### 2026-10-25 - Treat a cached row naming another album as a miss

Side task, no batch tag: `AlbumCache.lookup` drops a cached Spotify row whose stored provider names do not fit its key (R2, RB1), on `fix/album-matching`, stacked on PR #269.

Owner intent: a row stored under "xiu xiu|a promise" could hold another album's ID (the old unchecked search), and until now it was served for 30 days. `lookup` now drops every hit whose `match_for(key)` is `MATCH_WRONG` and logs one INFO line with the count only, so the album is searched again and the existing upsert overwrites the row with stamped names. `MATCH_FITS` and `MATCH_UNSTAMPED` rows (including pre-migration Spotify rows with NULL names, and Deezer rows) are returned as before; `lookup_failed` and the fail-open path are unchanged. A dropped hit is not counted in `db_cache_lookup_hits`.

Deviations: none. Landed before Task 8 (disjoint files: Task 8 touches the orchestrator search and details modules; Task 8 was still in review).

Edited existing tests: none. The `_spotify` helper in `tests/test_album_cache_parity.py` gained an optional `credit` argument (details carry name and artists); no existing test changed. New: `test_a_spotify_row_naming_another_album_is_a_miss` (parametrized) in `tests/services/test_cache.py` and `test_a_cached_row_naming_another_album_is_searched_again_and_overwritten` in `tests/test_album_cache_parity.py`.

Validation: `pytest -q` -- **2929 passed**.

### 2026-10-25 - Accept only an exact album match in Spotify search

Side task, no batch tag: Spotify search accepts only a hit whose credited artist and title match the request (D1, RB3, RB4), on `fix/album-matching`, stacked on PR #269.

Owner intent: `search_for_spotify_album_id` took `items[0]` unchecked, so a missing album got another album (wrong track list, "0 secs"). It now asks for 5 hits (`limit` 5) and returns the first whose credited artist and title normalize to the request key; otherwise None. New pure `matching_credit(item, key)` does the comparison (a non-dict hit or non-text field returns None, never raises). `album_metadata_from_details` takes `key` (default None) and stamps `provider_artist` and `provider_title` from the credit that matched, else leaves both None and, given a key, logs one warning line with no names; `orchestrator/_details.py` passes the key. Fix round 1: review found that comparing the title alone went unnoticed, so the exact-match test gains a same-title, different-artist case. The sequence-diagram and README wording for the search step follow in Task 11 (RB13, RB14); F-B23-59 is closed by Task 11, not here.

Deviations: none.

Edited existing tests: `test_search_for_spotify_album_id_retries_429_then_returns_id`, `test_search_succeeds_on_first_try` and `test_search_retries_a_malformed_retry_after` (their fake bodies gain the name and artists a real hit carries), and the helper `_ok_search` (now takes artist and album; callers pass the request's own names: `test_search_401_drops_the_cached_token_and_retries_once_with_a_fresh_one`, the newer-cached-token 401 test, `test_an_answer_between_refusals_keeps_the_breaker_closed`, `test_a_call_given_a_stale_token_sends_the_valid_cached_one_first`, `test_an_expired_cached_token_is_not_adopted`, `test_concurrent_rejections_of_one_token_cost_one_token_request`).

Validation: `pytest -q` -- **2924 passed**.

### 2026-10-25 - Store the provider's own names and add match_for

Side task, no batch tag: store the artist and title the provider returned beside each cached album, and add `AlbumMetadata.match_for(key)`, on `fix/album-matching`, stacked on PR #269.

Owner intent: the cache keyed rows by the request's names, so a wrong Spotify match was indistinguishable from a right one. `spotify_cache` gains nullable `provider_artist` and `provider_title`; `AlbumMetadata` carries them (default None, still frozen), `from_row` reads them, `batch_lookup_metadata` selects them and `batch_persist_metadata` writes them (new array params $10 and $11, existing indexes unchanged). `match_for(key)` is the single re-verify rule (`MATCH_FITS`, `MATCH_WRONG`, `MATCH_UNSTAMPED`) for later tasks; `enrichment.py` now imports `normalize_name` from `domain`. The schema ships through `init_db.py` (the Fly release command) with no manual DB step, no data migration and no purge. Old rows read as unstamped (Spotify) or fits (Deezer). No behaviour change yet: nothing calls `match_for`, and `album_metadata_from_details` still leaves the names None (Tasks 7 and 10 fill them).

Deviations: the two columns are folded into the existing `ALTER TABLE spotify_cache ... ADD COLUMN IF NOT EXISTS` statement rather than a separate one (idempotent, judged so by review; keeps the statement count so `tests/test_init_db.py` needed no edit). Fix round 1: review found that dropping a name column from the upsert's `DO UPDATE SET` list left every test green; the persist-SQL test now requires both `EXCLUDED` assignments (the fake Postgres has no ON CONFLICT handling, so a round trip is not possible).

Edited existing tests: `test_album_metadata_holds_album_facts_only` (field-set pin gains the two names), `test_batch_lookup_metadata_returns_albums_with_their_provider_columns` (row, expected and SQL carry the names), `test_batch_persist_metadata_writes_a_spotify_id_to_both_columns` (asserts the two name arrays and the two `EXCLUDED` assignments), `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` (the stored-row shape in the parity test gains the two None fields).

Validation: `pytest -q` -- **2914 passed**.

### 2026-10-25 - Space MusicBrainz requests 1.1s apart

Side task, no batch tag: space MusicBrainz request starts 1.1s apart (D5, RB6), on `fix/album-matching`, stacked on PR #269.

Owner intent: MusicBrainz's policy is 1 request per second, and the throttle started requests exactly 1.000s apart, which left no margin. `MUSICBRAINZ_REQUESTS_PER_SECOND` (an integer) is replaced by the float setting `MUSICBRAINZ_MIN_INTERVAL_SECONDS` (default 1.1, read through `_positive_seconds` so 0, negative and nan are refused), and `_MUSICBRAINZ_THROTTLE` is now `_GlobalThrottle(1, MUSICBRAINZ_MIN_INTERVAL_SECONDS)`; `_GlobalThrottle` and the other providers are unchanged. The old variable is ignored: setting it logs one import-time warning on `scrobblescope.config` naming the new variable. If Fly secrets set the old variable, it now only logs that warning. New tests: `test_global_throttles_space_request_starts_by_their_interval` (MusicBrainz 1.1 and Spotify 1/rate, controlled clock), `test_musicbrainz_limiter_uses_the_musicbrainz_throttle`, and `test_musicbrainz_spacing_is_the_interval_setting_and_the_old_rate_is_ignored` (child-process import; one fix round after review made it also assert the throttle's spacing equals the setting, so a hard-coded 1.1 fails).

Deviations: none. This task landed after Tasks 5 and 3 (disjoint files). The policy quotes of "1 req/s" in `musicbrainz.py`, `release_checks.py`, `docs/agents/runtime-system.md` and `tests/test_release_checks.py` stay: they cite the policy, not the enforced spacing. Edited existing tests: none.

Validation: `pytest -q` -- **2905 passed**.

### 2026-10-25 - Wait and retry when MusicBrainz throttles

Side task, no batch tag: make the MusicBrainz lookup wait and retry on a 429 or 503 instead of caching a false "no match", on `fix/album-matching`, stacked on PR #269.

Owner intent: `scrobblescope/musicbrainz.py::search_once` treated a 429 as a final "no match" (which then got cached) and waited a fixed second on a 503 (F-B23-62). Both statuses (`_RATE_LIMIT_STATUS = (429, 503)`) now honour `Retry-After` through `parse_retry_after`, else back off `2**attempt` plus a small hash-based jitter (as `spotify.py` does). Exhausted retries raise `musicbrainz_rate_limited` (header seen) or `musicbrainz_unavailable` (none) and cache nothing; a `Retry-After` over the cap raises at once without sleeping. Other 5xx retries and non-200 4xx no-match are unchanged. One fix round after review added 503 coverage to the header, exhaustion and over-cap tests (parametrized, no new tests).

Deviations: this task landed after Task 5 (disjoint files). F-B23-62 is not closed here; Task 11 closes the findings. The test module imports `_check_candidate` from `scrobblescope.release_checks`. Edited existing tests: `test_lookup_raises_when_musicbrainz_stays_throttled_not_no_match` (now asserts `musicbrainz_unavailable`, docstring updated, response `headers = {}`) and `test_lookup_retries_on_503_then_succeeds` (response `headers = {}`; the sleep assertion pins the first exponential wait, 1 <= wait < 1.2, instead of `await_count >= 1`), the other 503 retry tests were checked and needed no change.

Validation: `pytest -q` -- **2899 passed**.

### 2026-10-25 - Check the artist name the spotlight search returns

Side task, no batch tag: make the artist spotlight check the name Spotify returns, on `fix/album-matching`, stacked on PR #269.

Owner intent: `scrobblescope/spotify.py::_request_spotlight_artist` searched `artist:<name>` with `limit: 1` and returned the first hit unchecked, so a short name such as "ear" could show another artist's photo (F-B23-26 / D6). The name-search path now asks for `limit: 5` and returns the first hit whose `normalize_name(hit, "")[0]` equals that of the requested name (case and punctuation ignored). It returns `None` when no hit matches, or when the requested name normalizes to empty ("!!!"), so `/api/artist_spotlight` answers its existing null-image payload. The `artist_id` path is unchanged. New tests: `test_artist_spotlight_name_search_checks_the_returned_name` (4 cases) and `test_artist_spotlight_id_lookup_skips_the_name_check`.

Deviations: this task landed before Tasks 3 and 4 of the plan (disjoint files; those are in fix rounds). F-B23-26 is not closed here; Task 11 closes the findings. Edited existing tests: `test_artist_spotlight_parses_details_and_missing_fields` (the search hit now carries the requested name) and `test_artist_spotlight_falls_back_from_failed_id_lookup` (the hit is named "Requested", not "Search match"); same assertions.

Validation: `pytest -q` -- **2888 passed**.

### 2026-10-25 - Keep an identity for albums that normalize to nothing

Side task, no batch tag: give an album whose title normalizes to nothing its own identity, on `fix/album-matching`, stacked on PR #269.

Owner intent: albums named "?" or "EP" keyed as an empty album half in `normalize_name`, so any two such albums by one artist collided. `scrobblescope/domain.py::normalize_name` now falls back, when the cleaned and edition-stripped album is empty, to the raw text (NFKC, lowercase, whitespace collapsed) with "|" written as "%7c", so the key still splits cleanly in `format_album_key`. The artist half and every non-empty album key are unchanged. Docstrings of `normalize_name` and `format_album_key` say so. Cover wash for such albums changes (accepted). Added tests in `tests/test_domain.py`: `test_normalize_name_empty_remainder_keeps_distinct_pipe_free_identity`, `test_normalize_name_nonempty_remainder_keys_unchanged` (4 params) and `test_format_album_key_round_trips_empty_remainder_titles` (2 params).

Deviations: none. Edited existing tests: `tests/test_domain.py::test_normalize_name_ep_preserved_in_artist_stripped_from_album` (the album half is now "ep", not empty; it still asserts that an artist named EP is kept and an album EP is stripped of the edition word, and its docstring was corrected).

Validation: `pytest -q` -- **2883 passed**.

### 2026-10-25 - File the album-matching findings

Side task, no batch tag: file the five album-matching findings that the plan's later commits cite, on `fix/album-matching`, based on `main`.

Owner intent: the plan (`docs/superpowers/plans/2026-10-25-album-matching.md`) fixes problems the owner's real runs showed on 2026-10-25, and each later commit needs an open finding to close. `docs/agents/FINDINGS.md` now holds F-B23-59 (Spotify album search takes the first result unchecked), F-B23-60 (two albums sharing a Spotify ID overwrite each other; still reachable through collaboration albums), F-B23-61 (an album named "?" or "EP" normalizes to an empty key), F-B23-62 (a MusicBrainz 429 is cached as a final "no match", the P2 that corrupts a cache) and F-B23-63 (MusicBrainz request starts exactly 1.000s apart, P3). The artist spotlight's unchecked first result stays F-B23-26, open. Each names its function and one real case. Only `docs/agents/FINDINGS.md` and this log changed; no code or test.

Deviations: F-B23-64 was already taken (filed on PR #269), so the plan's IDs 59 to 63 were confirmed free in both the active file and the archive; F-B23-26 was not edited because the plan does not change its fix. Edited existing tests: none by this commit; the plan's later commits edit these existing tests, each named in its own entry: `tests/test_domain.py::test_normalize_name_ep_preserved_in_artist_stripped_from_album` (Task 2), `test_lookup_raises_when_musicbrainz_stays_throttled_not_no_match` (now `musicbrainz_unavailable`, response `headers = {}`) and the 503 retry tests that assert a fixed sleep, all in `tests/services/test_musicbrainz_service.py` (Task 3), and the search fakes in `tests/services/test_spotify_service.py` (Task 7).

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - Plan album matching and cache re-verification

Side task, no batch tag: committed the plan for the album-matching fixes, on `fix/album-matching`, a branch stacked on `feat/ui-round-2-backlog` (PR #269).

Owner intent: the owner's real runs on 2026-10-25 showed albums with plays but "0 secs" of listening time, which the session traced to Spotify album search accepting its first result unchecked, a second album silently taking a shared Spotify ID, and album names such as "?" and "EP" normalizing to nothing; and asked for MusicBrainz headroom ("since release checks run in the background it costs nothing") and rate-limit retries. `docs/superpowers/plans/2026-10-25-album-matching.md` (written by a plan-writer agent, reviewed three times, both findings of the last review checked by the controller): Spotify search takes the exact-match rule Deezer already uses over five candidates, any credited artist counts, a shared ID gives every request its own metadata, an empty-normalizing title keeps its raw identity, cached Spotify matches are re-verified on read by looking up their cached ID (two new nullable cache columns through `init_db.py`), MusicBrainz waits about 1.1s between request starts and treats 429 and 503 alike (Retry-After, else exponential backoff with jitter, never a cached "no match"), and F-B23-26 (the artist spotlight's unchecked first result) is fixed the same way. Deviations: none. Edited existing tests: none by this commit; the plan names each later edit. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: Section 3 marks plan A finished

Side task, no batch tag: make PLAYBOOK Section 3 agree with Section 4 about plan A, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: Section 3 and Section 4 must agree (AGENTS.md "Mid-batch handoff discipline"). Codex review round 1 on PR #269 (P1) found the Section 3 bullet still saying the PR is a draft with Task 12 and the final gates outstanding, while Section 4 records Task 12 done and the final verification gate passed at 4ef0e0af. The bullet now says PR #269 is out of draft, all fourteen tasks have landed, the final gate passed and the PR merges once its review is clean.

Deviations: this is the one exception to leaving Section 3 alone for this branch, by controller ruling; only that bullet's sentences changed. Edited existing tests: none.

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - UI round 2 backlog: plan A execution record closed

Side task, no batch tag: record Task 12 and correct the landing-order note in plan A's execution record, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: "keep commits atomic and well-scoped", so the record is its own commit after the sweep fixes (`269433d2`). The record now says all fourteen tasks landed and points the final verification gate at PR #269's "Validation at this head". The landing-order note is corrected: T9 landing before T8 needed no ruling, because the plan's Dispatch section lets T7b, T8 and T9 land in any order, and T11b landing before T11 was a controller call (docs only, landed while T11 had a fix round). A Task 12 row is added, and Task 12's three acceptance boxes are ticked: the remaining sweep hits are listed in the `269433d2` entry as judged current or point-in-time, `--check` exits 0, and for this commit all five gates passed (suite, `frontend-gate`, `results-behavior`, `pre-commit`, `docsync-check`).

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - UI round 2 backlog: hero strip and albums-to-search stale copies

Side task, no batch tag: fix the two live stale copies the Task 12 sweep found, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: plan A's closing sweep for copies still describing the pre-round-2 behaviour. The controller ran the sweep at `4f659b7b` over every term in Task 12 plus `cache_hits`, `albums_to_search` and `section marks`. Two hits were live: the `static/js/heatmap.js` comment that called the term lists "section marks" (they are now the hero strip, `data-mode-marks`), and the cache-split message in `docs/architecture/top-albums-sequence.md`, which named only `cache_hits` although the orchestrator records `cache_hits` and then `albums_to_search` there. Comment and diagram text only, no code.

Judged current or point-in-time and left alone: `DESIGN.md` (:183 the 2.5rem lift, :228 the AA floor), `docs/design/RECONCILIATION.md` (:38, :39, :46, :1256, :1269, :1272, :1276 current or history; :935-936 marked superseded), `static/css/shell.css` (:790, :806), `scripts/dev/_frontend_gate_colour.py` (:206, :263, :300), the "Spotify matched" reasons in `_deezer_fallback.py` and `_details.py`, `scrobblescope/orchestrator/__init__.py:59`, `plays.py:207` (`albums_passing_filter`, a job stat the loading page does not show), `stat-cache-hits` (the current id), `templates/heatmap_empty.html:16` and `templates/partials/_heatmap_form.html:40` (current copy), `config/docsync.toml:526`, every `cache_hits` line in code, `.claude/SESSION_CONTEXT.md`, `docs/agents/FINDINGS.md`, `scripts/testing/smoke_cache_check.py`, and every SVG path-data hit.

Deviations: none; no prose was added below the diagram, none describes the loading stats. Edited existing tests: none.

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - UI round 2 backlog: Section 3 and session context refresh

Side task, no batch tag: refresh PLAYBOOK Section 3's round-2 backlog sentences and the session context, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: "PLAYBOOK.md and SESSION_CONTEXT need to be refreshed". Section 3 now says all the tasks of plan A except the stale-copy sweep (Task 12) have landed on the branch (PR #269, draft) with a test consolidation, that the sweep and the final gates remain before the PR leaves draft, and that the stacked album-matching PR follows. SESSION_CONTEXT's "Last updated" is 2026-10-25. The tracked test-module count moved from 101 to 103 in both copies (SESSION_CONTEXT Section 1 and the FINDINGS.md header, F-DOCSYNC-23), measured the way that finding describes: `git ls-tree -r --name-only HEAD tests | grep -c '/test_[^/]*\.py$'`. The machine-managed sections were left to `doc_state_sync.py --fix`.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2876 passed**.

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

### 2026-10-25 - UI round 2 backlog: test consolidation, route tests

Side task, no batch tag: merge repeated rank and render tests in `tests/test_routes.py`, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA20): "test for *intended function*, not *written function* and avoid repeatedly testing the same behaviour"; "Keep things cheap and narrow". Merged: `test_mark_untimed_for_display_ranks_every_album_for_non_playtime_sort` is now a case of the parametrized `test_mark_untimed_for_display_marks_durationless_albums_only_when_sorting_by_playtime` (renamed from `..._when_sorting_by_playtime`), which keeps both the playtime and the non-playtime case. Removed: `test_playtime_run_treats_missing_none_and_zero_as_durationless`; its missing, None and zero forms are covered by the same parametrized helper test and its page cells by `test_playtime_run_keeps_durationless_albums_as_hidden_unranked_rows`. RA17's page-level rank-cell guard stays in that last test (timed rows read 1 and 2 around a durationless row, hidden rows' cells empty); it lost only its Scrobbles assertion, which `test_scrobbles_figure_counts_albums_a_playtime_ranking_hides` owns. `test_play_count_run_ranks_every_album_and_hides_the_note` is renamed `test_play_count_run_hides_no_row_and_hides_the_note` and no longer re-reads rank cells (the helper test owns the ranking). `test_playtime_run_with_only_durationless_albums_renders_no_matches` keeps its no-rows assertion and drops the `"No Albums Found"` wording pin.

Deviations: none. Edited existing tests: the five named above (one merged, one removed, three edited or renamed).

Validation: `pytest -q` -- **2872 passed**.

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

### 2026-10-25 - UI round 2 backlog: server listening-time rule

Side task, no batch tag: apply the listening-time ranking rule on the server, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (R6, RA3, RA5): a run started in listening-time mode shows the same leaderboard as a page switched to it, and switching to track plays brings the untimed albums back. `_filter_results_for_display` no longer drops rows; `_mark_untimed_for_display` in `scrobblescope/routes/album_flow.py` returns copies carrying `untimed` and `display_rank` (None when untimed, else 1..n skipping them). Durationless means `play_time_seconds` missing, None or <= 0 (RA6: None no longer raises a TypeError). `templates/results.html` renders untimed rows with `hidden` and an empty `data-rank` and rank cell, and shows `#playtime-hidden-note` with N when N > 0, using the same singular/plural copy as `results.js` (RA13). Total Albums, Top artist and Scrobbles are built from the whole result (RA3). The no-matches page stays for a run where every album is untimed. F-B23-46 stays open until the client half and its agreement test land.

Deviations: `scrobblescope/routes/__init__.py` (outside the plan's Touches) re-exports the renamed helper, forced by the rename. `tests/test_template_shell.py` (RA17) gains `display_rank: 1` on its two fixture rows, because the template reads `display_rank` with no `loop.index` fallback. Review fix round (RA17): the route tests read the visible rank cell and a gap between ranked rows.

Edited existing tests: `test_filter_results_for_display_removes_zero_playtime_when_sorting_by_playtime` became `test_mark_untimed_for_display_marks_durationless_albums_when_sorting_by_playtime` and `test_filter_results_for_display_keeps_zero_playtime_for_non_playtime_sort` became `test_mark_untimed_for_display_ranks_every_album_for_non_playtime_sort`, because the helper marks rows instead of removing them (same rule, same three durationless forms); `test_scrobbles_figure_leaves_out_albums_a_playtime_ranking_drops` became `test_scrobbles_figure_counts_albums_a_playtime_ranking_hides` (90, not 50), because the dropped album is now a hidden row and the figure describes the whole result.

Validation: `pytest -q` -- **3064 passed**.

### 2026-10-25 - UI round 2 backlog: gate the mode switch

Side task, no batch tag: gate the index mode switch like the segmented controls, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (RA1, "Keep muted, gate at 4.5"): keep the muted unselected label on the mode switch and hold it at 4.5:1 while the other segmented controls stay at 7:1. `seg_contrast_failures` and `seg_hover_failures` in `scripts/dev/_frontend_gate_colour.py` take an optional `unselected_floor` spec key (default `SEG_TEXT_FLOOR`, 7.0) that replaces the floor for the unselected option text and the unselected-hover cell only. `scripts/dev/_frontend_gate_forms.py` adds `MODE_SWITCH_SEG` and `mode_switch_failures`, called from `check_include_unmatched_control`: it measures Top albums selected and Heatmap selected (a real click on `#mode-tab-heatmap`, restored to Top albums in a `finally`) in both themes, covering option text, selected text, chip boundary and both hover cells.

Deviations: the measure hangs off `check_include_unmatched_control` because `frontend_gate.py` is outside the task's files. Review fix round (RA16): added a stub-page test that the include check runs the mode-switch measure, tests for the hover measure, the selected-chip hover row and the selected-chip hover floor staying at the default, and a restore-on-error test. No test that predates this task is edited. Of this task's own first-phase tests, `test_mode_switch_failures_restore_top_albums_and_keep_light_clear` gains `assert failures` and `test_mode_switch_spec_holds_only_the_unselected_cell_at_4_5`, added by this task's own first phase, was removed (RA16 (f): it pinned a constant equal to the code).

Validation: `pytest -q` -- **3060 passed**.

### 2026-10-25 - UI round 2 backlog: gate the hero strip

Side task, no batch tag: gate the hero strip's layout, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: keep the strip from regressing after the container-query fix. `scripts/dev/_frontend_gate_layout.py` gains `STRIP_ROW_QUERY_EM` (26, mirroring `@container (width < 26em)`), `_measure_strip` and the pure `_strip_layout_failures`, called from `_check_desktop_scale_bounds` beside the headline-wrap check for both modes at 900, 1100, 1200, 1500, 1920 and 2560 (900px height): three columns or stacked rows by 26 x the strip wrap's computed font size, and no wrapped term (height over 1.2 x line height). At 859 and 390 the lists must be hidden. The helper fails closed on a thin measurement (fewer than three items, or no measurable term or line height), and the sweep is pinned to its widths and 900px height by a test. The strip had no gate: the columns/rows switch is a container query and the mobile cut a viewport rule, and terms wrapped unnoticed up to 1179px. The 859/390 failures report under the `[desktop]` profile label because the sweep runs inside the desktop check (RA15, accepted).

Deviations: none. Edited existing test: `test_desktop_scale_bounds_reports_wrapped_headlines_and_closes_context` (its stub now serves a strip measure and its expected failure list gains the strip line, so removing the strip call fails it).

Validation: `pytest -q` -- **3047 passed**.

### 2026-10-25 - UI round 2 backlog: hidden-count note

Side task, no batch tag: show how many albums listening-time ranking leaves out (F-B23-46, client half of the note), on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (R6, RA3): a listener who ranks by listening time should see why albums vanish and how to get them back. `templates/results.html` gains `#playtime-hidden-note` (hidden by default, with `#playtime-hidden-count` and `#playtime-hidden-copy`) after the stat grid, reusing the existing partial-notice style, so nothing moves on load. `applyRowState` in `static/js/results.js` now counts the rows the rule drops, excluding rows Hide already hides, and shows or hides the note with that count; the toast on switching to listening time gains the count when it is above 0. Copy is the owner's choice (RA13, "Count first"): note "N albums with no listening time are hidden. Rank by track plays to show them." (N = 1: "1 album with no listening time is hidden. Rank by track plays to show it."); toast "Leaderboard ranked by Spotify listening time. N albums with no listening time are hidden." (N = 1: "1 album with no listening time is hidden."); with N = 0 and on plays the toast is the existing sentence alone, with one singular/plural switch in `results.js`. New tests in `scripts/dev/results_behavior_tests.py` read the integer and the `hidden` state, never the wording: the count and toast for two durationless rows, the plain path with none, Hide-hidden rows not counted, and the live Hide path refreshing the note at N = 0 and N = 1 (RA14). F-B23-46 stays open: the server half that renders the note on a run started in playtime mode is T10's, and T11b closes it.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **3026 passed**.

### 2026-10-25 - UI round 2 backlog: client listening-time rule

Side task, no batch tag: client half of the listening-time rule (F-B23-46), on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent (R6): ranking the Results page by listening time drops albums with no listening time and renumbers the rest, and ranking by track plays brings them back. `applyRowState` in `static/js/results.js` now sets each row's hidden state as one decision (Hide on an unmatched row, or listening-time ranking on a row whose `data-play-time-seconds` is not above 0), clears `data-rank` and the rank cell of hidden rows, and renumbers the rest 1..n; `setLeaderboardMetric` and `setUnmatchedHidden` both call it, so a metric switch never reveals what Hide hides and never hides what Hide shows. The header figures count rows not hidden by Hide, so Total Albums, Top artist and Scrobbles still describe the whole result (RA3). The CSV exporter already skips hidden rows, so it lists only the ranked rows. New tests in `scripts/dev/results_behavior_tests.py` cover the drop and restore, the Hide round trip, the CSV and the header figures. This does not close F-B23-46: the server half (T10) and the hidden-count note (T7b) follow, and the toast text is unchanged here.

Deviations: none. Edited existing test: `test_sort_updates_order_ranks_metrics_and_accessibility` (the durationless row "C" is now hidden and unranked in listening time, visible ranks `["1","2"]`, back at rank 3 on plays).

Validation: `pytest -q` -- **3026 passed**.

### 2026-10-25 - UI round 2 backlog: gate the expanded form's placement

Side task, no batch tag: gate the expanded form's placement in the layout gate, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: a form with every option open must not leave the mode switch pinned under the header, and a short window must keep the 0.25rem top floor (R3). The graduated lift (`2609f1f`) had no gate, so the old formula (4px gap) passed unnoticed. `check_large_display_scale_parity` now measures the expanded form (decade scope chosen, thresholds open) at 1920x1063, where the gap above the mode switch must be at least 1.5rem (1px tolerance), and at 1920x700, where the form top must sit exactly 0.25rem below the well top. It also re-runs the collapsed centring check at 1920x1063, and the `_form_centring_failures` docstring now describes the graduated lift (collapsed forms keep the full 2.5rem lift). New pure `_expanded_placement_failures` and `_measure_expanded_placement` in `scripts/dev/_frontend_gate_layout.py`; `_expanded_placement_failures` is listed in `HELPERS` of the test module. Stub-page tests cover both viewports and the state asked of `_reach_state`.

Deviations: per ruling RA11, `_expanded_placement_failures` takes a keyword-only `short_window=False` flag beyond the plan's frozen `(label, measured)` interface; the two-argument call keeps its meaning (the roomy window). Edited existing tests: none (`HELPERS` tuple extended).

Validation: `pytest -q` -- **3026 passed**.

### 2026-10-25 - UI round 2 backlog: RECONCILIATION records the overrides

Side task, no batch tag: record the round 2 backlog overrides in `docs/design/RECONCILIATION.md`, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: keep the override list true to what ships (the snapshot stays verbatim, so its overrides live here). Section 20 and the "Segmented control look" row still stated the superseded primary border and base-content ink as current; they now mark the first look superseded and state the shipped tint, primary text and `#775ab5` / `#8a79ab` outline. New Section 29 records the hero strip (R4, the container query, R7), the expanded-form placement (R3), the loading stats (R5), the selected-option look and its two owner exceptions (RA1, RA2), and the AA goal (RA4), citing the landed commits. The "Heatmap H1 copy" row now reads "Your 365 days *mapped by day.*" and a row records the album headline and lede copy.

Deviations: per ruling RA10, the top-table row "Index hero: capability marks" is trimmed to the hero strip only (the outline token and loading labels live in Section 29 and the segmented-control row) and moved to after the Section 24 row; Section 29 also cites T1's commit `406e9b74` beside the RA2 token raise. Edited existing tests: none.

Validation: `pytest -q` -- **3016 passed**.

### 2026-10-25 - UI round 2 backlog: one stronger selected outline

Side task, no batch tag: `--shell-selected-outline` set to `#775ab5` (light) and `#8a79ab` (dark) and both selected-boundary gates raised from 3:1 to 4.5:1, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: one stronger outline that every selected-option boundary gate holds at AA (ruling RA2). The token and `SEG_BOUNDARY_FLOOR` / `INCLUDE_BOUNDARY_FLOOR` changed together, because the old token measured 4.40:1 dark and 4.37:1 light on the Results card (the plan's 4.24:1 is the old dark token on base-200) and would fail a 4.5 floor; the new values clear 4.5:1 on the track, the sunken well, the card and the results surface. The `shell.css` comment and the two gate docstrings were rewritten. New stub-page tests for `seg_contrast_failures` and `card_boundary_failures` (floor value, per-theme failure, fail-closed missing control, translucent border compositing, unselected 7:1 against selected 4.5:1) in `test_frontend_gate_colour.py` and a new `test_frontend_gate_include.py`; six hand mutations were killed. Token RED in the browser gate: floors at 4.5 with the old tokens failed at 4.40:1 and 4.37:1 on the card; GREEN with the new values.

Deviations: none beyond the measured card figures above. Edited existing tests: none (new tests appended to `test_frontend_gate_colour.py`).

Validation: `pytest -q` -- **3016 passed**.

### 2026-10-25 - UI round 2 backlog: DESIGN.md states what ships

Side task, no batch tag: DESIGN.md corrections so it says what the UI round 2 ships, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: the design doc must describe the shipped UI, not the first selected-chip look. Changed in `DESIGN.md` only: the selected option is soft tint, primary text (5.47:1 light, 6.38:1 dark, held at the 4.5:1 AA floor by owner exception) with a 1px `--shell-selected-outline` outline (5.01:1 light, 5.00:1 dark against the track); the stale 6.06/8.14/14.81/13.04 figures are gone; the index mode switch keeps its muted unselected label (5.17:1 light, 5.82:1 dark, a second owner exception); the Fixed Composition Rule states the 2.5rem lift that gives way first, the 1.5rem floor above the mode switch, the plain-centring fallback, the 0.25rem header floor and scrolling in short windows; new bullets for the hero strip and the loading stats. Figures recomputed from the tokens.

Deviations: the Loading Stats bullet names the tiles in the shipped order (Scrobbles and Pages fetched, then Cache hits and Albums to search, as in `templates/loading.html`), per ruling RA7, where the plan wrote "Pages fetched and Scrobbles". Edited existing tests: none.

Validation: `pytest -q` -- **3001 passed**.

### 2026-10-25 - UI round 2 backlog: loading stats and Back test

Side task, no batch tag: browser tests for the loading page's Cache hits and Albums to search tiles and its history-replacing redirect, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: the 2026-10-25 loading page changes (two stat tiles, Back from the results reaching the form) were not held by any test, so a swapped key or a return to `location.assign` would pass. Two tests in `tests/frontend/test_heatmap_pure_functions.py`: one drives a `/progress` answer with both figures (12 and 30 fill their own tiles) and one with `cache_hits` alone (the second tile stays hidden); the other loads the page from a routed URL, lets the scheduled redirect run and asserts the page is at `/results` with `history.length` unchanged. The shared loading markup gained the stats container and two tiles; label wording is not pinned. Two planted defects in `static/js/loading.js` (`location.assign` in `redirectToResults`, the Cache hits tile reading `albums_to_search`) each turned one test red, then the file was restored byte-identical. Deviations: none. Edited existing tests: none (the shared markup constant was extended). Validation: `pytest -q` -- **3001 passed**.

### 2026-10-25 - UI round 2 backlog: loading stats proof

Side task, no batch tag: tests proving `cache_hits + albums_to_search` equals the albums that passed the thresholds, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: the loading page's two figures, Cache hits and Albums to search, must add up to the albums being processed. Five tests, no source change: four at `process_albums` (mixed cached and missing, an unmatched miss still counts as an album to search, all cached, database unavailable) and one through `fetch_and_process_albums` with an album under the thresholds, where the sum is the albums that passed, not the albums fetched. Each ran through the job store, and two planted defects in the orchestrator (`len(cache_misses) + 1`, the `albums_to_search` line dropped) turned all five red, then the source was restored byte-identical. Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2999 passed**.

### 2026-10-25 - Repair the two pipeline sequence diagrams

Side task, no batch tag: repaired the Mermaid renders of the two pipeline sequence diagrams, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: the diagrams explain the pipelines to people, and three `Note` lines held a semicolon, which ends a statement in a Mermaid sequence diagram and broke both renders. The owner's edits replace each semicolon with a full stop or a comma, meaning unchanged: one note in `docs/architecture/heatmap-sequence.md`, two in `docs/architecture/top-albums-sequence.md`. Both diagrams render valid in the Mermaid validator, and no Mermaid block under `docs/architecture/` holds a semicolon. No check was added: the owner keeps the diagrams as reading material, not a gate. Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - Plan the UI round 2 backlog follow-through

Side task, no batch tag: committed the plan for the UI round 2 backlog's follow-through, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: the live session's changes landed before their plan so the state was safe; the plan now covers what they still owe. `docs/superpowers/plans/2026-10-25-ui-round-2-backlog.md` (written by a plan-writer agent, reviewed twice, approved at the second review): DESIGN.md and RECONCILIATION updates, gates that hold the selected-option look at 4.5:1 on every surface (one firmer outline token, `#775ab5` light and `#8a79ab` dark), the mode switch's muted label held at 4.5:1 (owner: "goal is to be AA compliant throughout"), the expanded-form placement, the hero strip and the loading page's stats and Back, and F-B23-46 by the owner's rule (a listening-time ranking hides albums with no listening time, track plays restores them, the header keeps whole-result figures and a note says how many are hidden). Two review Minors on its Task 10 are carried into that task's brief at dispatch. Deviations: the plan follows the commits it documents instead of preceding them, at the owner's request. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: the frontend gate's selected-text floor

Side task, no batch tag: lowered the frontend gate's floor for selected-option text from 7:1 to 4.5:1, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner ruling (2026-10-25), asked after the gate failed 28 checks at `4c0c744` on the violet selected text (5.47:1 light, 6.38:1 dark on the soft tint): "Keep primary, lower the gate", chosen over a deeper violet that reaches 7:1 (`#583f8e` light, `#baa7df` dark). `scripts/dev/_frontend_gate_colour.py`: `SEG_SELECTED_TEXT_FLOOR` is 4.5 with the ruling in its comment, and `seg_hover_failures` holds a hovered selected chip to that floor instead of the 7:1 `SEG_TEXT_FLOOR`, which still holds unselected option text and its hover. The chip boundary stays at 3:1 (the outline measures 4.60:1 and 4.58:1). This is an exception to the owner's 2026-09-30 ruling that 4.5 is a floor, not a goal, for this one cell. It lands alone because it changes a script that decides a gate. Deviations: none. Edited existing tests: none (no unit test covers these two functions). Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: the hero scales again and the heatmap headline fits

Side task, no batch tag: fixed the two layout failures the frontend gate and CI found at PR #269's first head, on `feat/ui-round-2-backlog`, a branch off `main`.

The gate's "large display scale parity" check failed twice at `4c0c744`. First, the hero composition was 948.1px tall at 4K against a proportional 837.6px: the strip's `max-width: 44rem` in `static/css/index.css` was the one hero dimension not multiplied by `--index-scale`, so as the type grew the descriptions wrapped onto more lines (3, 2, 2 at 1080p; 5, 3, 4 at 4K). It now scales, and the hero measures 837px at 4K with the same wrapping at 1080p, 1440p and 4K. Second, the heatmap headline wrapped at 1200px (and at 1500px on CI's fonts). Owner ruling (2026-10-25): it reads "Your 365 days *mapped by day.*" in `templates/index.html`, shorter than the album headline, which fits at both widths. `config/docsync.toml`: the "heatmap window length" site in that template now reads the headline's `Your (\d+) days`, since "last 365 days" no longer appears there. Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: the loading page's stats, Back and entrance

Side task, no batch tag: relabelled the loading page's last two stats, took the finished page out of history and gave the stats an entrance, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: "Albums passing" and "Spotify matched" are unclear and showed the same number (backlog L2); one should be "Cache hits" and the other must not duplicate it (2026-10-25); Back from the results should not land on the loading page; the stats should not just appear. The old pair duplicated because "matched" counted every album given metadata from the cache, Spotify or Deezer, and Spotify search accepted its first result, so nearly all of them matched (that search defect is for the plan). `scrobblescope/orchestrator/__init__.py` records `albums_to_search` (the cache misses) beside `cache_hits` at the cache split; together they make up the albums that passed the thresholds. `templates/loading.html` and `static/js/loading.js` show "Cache hits" and "Albums to search" (first "Albums searched"; renamed because the figure is known before the search ends) and drop the separate "albums loaded from cache" line. `redirectToResults` uses `location.replace`, so Back from the results reaches the form instead of a finished loading page that sent the listener forward again. `static/css/loading.css`: each stat rises 0.375rem and fades in over 360ms as its first figure arrives, 50ms apart when they arrive together; reduced motion shows them at once. The backend still records `albums_passing_filter` and `spotify_matched` for other readers. Deviations: landed before its plan. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: the expanded form keeps clear of the header

Side task, no batch tag: stopped the fully expanded index form pressing its mode switch against the header, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: "the card itself is in the middle ... the mode tabs however, aren't accounted for" (backlog I4, 2026-10-25, from a 1920x1063 screenshot with every option open). `positionForm` in `static/js/index.js` always lifted the centred composition 2.5rem, so with everything open it hit its 0.25rem floor: 4px above the switch, 47px below the card. The lift now gives way first, never taking the gap above the switch below 1.5rem: measured 24px above and 27px below at 1920x1063 expanded, 24px and 63px at 1440x900; collapsed forms are unchanged (115px and 195px at 1920x1063). A window too short for the expanded form still scrolls with the 0.25rem floor; whether to raise it is open for the owner. The function's comment avoids the word daisyUI uses for its tab component, because Tailwind scans `static/js` for class names and that word generated daisyUI's tab styles into the compiled stylesheet. Deviations: landed before its plan; DESIGN.md's Fixed Composition Rule still describes the fixed lift, for the plan's docs task. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: one selected-option look

Side task, no batch tag: gave the mode switch and every segmented control one selected-option look, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: drop the segments' strong outline and keep the controls consistent, "so long as it is WCAG 2.x compliant" (2026-10-24/25, decided in the live session after trying a solid fill, which read as busy). The controller measured the mode switch's old look as failing WCAG 1.4.11: its soft tint is 1.11:1 light and 1.28:1 dark against the track, and its violet label only a hue shift from the grey one. `static/css/shell.css`: a new `--shell-selected-outline` token per theme (`#7d61b7` light, 4.60:1 against the track; `#8373a3` dark, 4.58:1), the primary mixed toward the page ground until it clears 4.5:1 as the owner asked; the checked `.seg__option` and the pressed `.metric-toggle-btn` take the soft tint, that 1px outline and primary text (5.47:1 light, 6.38:1 dark on the tint). `static/css/index.css`: `.mode-pill.active` takes the same three, with a `Highlight` border under forced colours. This covers the index's Rank by and Unmatched albums controls and the Results page's Unmatched albums control and Sort leaderboard buttons. Deviations: landed before its plan (see the entry below); `docs/design/RECONCILIATION.md` section 20 and DESIGN.md's Segmented Controls still give the old outline's figures, for the plan's docs task. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: the index hero

Side task, no batch tag: landed the index hero changes the owner accepted in the round 2 backlog's live session, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: the `§ 01/02/03` lists "feel generic and AI-directed" and should earn their place (backlog I3, H3); the album lede was "lacking" (I2); the heatmap headline "one grid." was "bland" (H1), and the owner later ruled out a comma followed by a one-word punch and "this past year" (the heatmap counts back 365 days from today). `templates/index.html`: both mark lists become a three-column strip, each item a serif term with a line icon (calendar, clock, document; grid, sliders, document) over one plain description; the album lede and both headlines take the accepted copy. `static/css/index.css`: the strip's rules replace the numbered-list rules, the strip sits 0.5rem under the lede, the ledes widen to 48ch with `text-wrap: pretty`, and where the hero column is narrow (windows up to about 1180px) each strip item becomes a row because terms wrapped there. That is a container query on the strip's wrapper in `em` of the term size, not a second viewport breakpoint: docsync's "single 860px breakpoint" declaration (DOC009) holds. The strip stays hidden below 860px (owner ruling). `static/js/heatmap.js`: one comment no longer calls the lists "§". Deviations: the changes landed before their plan, at the owner's request, so the session's state is safe; the plan follows. Edited existing tests: `tests/test_routes.py` `INDEX_HEADLINE` marks the index by `id="index-grid"` instead of headline copy the owner still revises. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-24 - Record UI round 2's outcome in its plan

Side task, no batch tag: recorded UI consistency round 2's outcome in its plan, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent: the plan should say what landed, in what order and with which extras, so the round can be read from the plan alone. `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md`: every step checkbox in Tasks 0-5 is ticked (the controller's "Final checks" boxes stay open), and a new `## Outcome (2026-10-24)` section lists each task's commit and landing extras, then the deviations (landing order T3, T4, T5, T1, T2 rather than the plan's order; the owner's f-swe-7 plan parked outside the worktree for the round's commits and restored; the heatmap export's hard-coded `instrument-serif` folded into Task 1; F-B23-58 filed). The Task 1 entry above gains the `MOVED` parity-tuple change in its "Edited existing tests" field (the Task 1 landing review's Minor 1); nothing else in that entry changed. On review a pointer to an untracked report was removed from the plan's Outcome section. Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-24 - File the frontend gate's intermittent failures

Side task, no batch tag: filed F-B23-58 for the frontend gate's intermittent failures, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent: a gate that fails and then passes on the same tree should be written down with its evidence rather than waved through (the repository's flake rule). `docs/agents/FINDINGS.md` gains F-B23-58 (P2, Scaling roadmap, after F-B23-56) recording the three checks that failed intermittently during UI consistency round 2 (PR #268): `shell text scaling [desktop]` (a `Page.goto` timeout at `b7a0722`, passed on the one re-run), `release check disclosure [desktop]` (a correction moved 2 rows, only in the two code-phase worktrees that held the Orpheus Pro change; `ff91283` awaits `document.fonts.ready`, cause unproven) and `theme persistence [mobile]` (a toggle click timeout, once). The fix shape is to record check, profile and timing before changing the gate, so no gate code changed. The finding's opening sentence was corrected on review (the checks failed intermittently and passed on other runs of a tree holding the same change, not on a later run of the same tree). Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-24 - Results stat values take the figure face

Side task, no batch tag: set the four Results stat values in the figure face, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent: "For each span||stat, use Gotham Book." (2026-10-22, accepted live). The four stat values (total albums, top artist, scrobbles, unmatched) lose `font-serif` in `templates/results.html`; `.results-stat-value > span` in `static/css/results.css` sets `--font-figure`, `--font-weight-normal`, tabular figures, size unchanged. New frontend-gate judge `stat_value_face_failures` (`STAT_VALUES_SELECTOR`) in `scripts/dev/_frontend_gate_figures.py`, called from the existing check against the heatmap KPI reference. DESIGN.md Role Segregation Rule and Do's line name the Top Artist exception; `docs/design/RECONCILIATION.md` section 28 records it and completes the move section 26 deferred. Landing changes on the code review's findings: the DESIGN.md exception sentence moved to the end of the Role Segregation Rule paragraph; the wrong-count test is parametrised over 0, 3 and 5 values; `_reference_failures(kpi, subject)` is the one owner of the empty-KPI message (the duplicate guard in `figure_face_failures` is gone, messages unchanged), with a new test for the stat wording; the serif-stat test asserts the exact failure line. Deviations: none. Edited existing tests: the `_Page` fake in `tests/scripts/dev/test_frontend_gate_figures.py` (answers the stat selector); no existing test body changed. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-24 - Orpheus Pro becomes the display serif

Side task, no batch tag: made Orpheus Pro the display serif, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent: the UI changes accepted live on 2026-10-22 (Orpheus Pro as the words face) are kept and made honest.

What changed and why: the `--font-serif` token now leads with `orpheuspro`, then `instrument-serif` (the owner's accepted WIP patch: `static/css/tailwind.src.css`, `static/css/tailwind.css`, `static/css/index.css`; the hero's letter-spacing is `0`). `REQUIRED_FONT_FAMILIES` in `scripts/dev/_frontend_gate_layout.py` names `orpheuspro` so a missing kit face warns, and a new test ties the first face of every `--font-*` token to that list. The heatmap's saved image reads its headline font from `--font-serif` instead of a hard-coded Instrument Serif (`static/js/heatmap.js`, recorded as `drawnHeader.headlineFont`), and `check_heatmap_export_header_matches_page` compares it with the page headline through the new `headline_font_failures`. DESIGN.md, `docs/design/RECONCILIATION.md` (new section 27, section 4 and the role map), README.md and `docs/agents/AGENT_NOTES.md` follow. Proven red on the unchanged tree and by three planted defects in `heatmap.js` (old hard-coded string, an invalid canvas font, `headlineFont` dropped), each restored.

Changes made at landing: (L1-1) three more unit tests of `headline_font_failures` in `tests/scripts/dev/test_frontend_gate_theme.py` pin the whole-list comparison (a different fallback tail, an empty page family, single against double quotes); the first fails against a first-family-only `_plain_family` and passes on the real code. (L1-2) the new prose lines in RECONCILIATION.md and AGENT_NOTES.md are re-wrapped to each file's hard wrap and the `drawnHeader` literal in `heatmap.js` is split across lines; no behaviour change. (L1-3) `check_release_check_disclosure` in `scripts/dev/_frontend_gate_results.py` now awaits `document.fonts.ready` before its first row measurement, so a late web-font swap of the serif results headline (which moves every row by the same amount) is not read as a correction moving rows; the diagnosis is unproven, because delaying the kit's font responses in a scratch copy did not reproduce the intermittent "a correction moved 2 row(s)" failure, and the await is kept because it is correct regardless. (L1-4) correction carried from Task 5's landing review: the entry "A finished run opens its results without a second line" wrote a literal ellipsis character (now the `\u2026` escape) and its edited-tests field now also names `test_the_heatmap_copy_names_the_shade_the_grid_draws`.

Deviations: none. Edited existing tests: `test_theme_source_locks_the_batch_21_design_tokens`; the `MOVED` parity tuple in `tests/scripts/dev/test_frontend_gate_theme.py` (two names added, `headline_font_failures` and `_plain_family`, which adds two cases to `test_the_slice_defines_the_name`). Validation: `pytest -q` -- **2985 passed**.

### 2026-10-23 - A finished run opens its results without a second line

Side task, no batch tag: dropped the redundant "Opening your results..." details line from a finished album run, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent: the phase line already says the run is done, so a second line repeating it should go (2026-10-22). `static/js/loading.js`: `scheduleResultsRedirect` now takes an optional message and sets the details line only when one is given; the success path calls it with none and keeps the three-second reading delay, and a failure with no retry still says "Opening the results page...". New tests in `tests/frontend/test_heatmap_pure_functions.py` (`test_a_finished_album_run_opens_its_results_without_a_second_line`, `test_a_failed_run_with_no_retry_still_says_the_results_page_opens`, helper `_run_album_loading`) were proven red on the unchanged code and by three planted defects (old success call back, message ignored, `setTimeout` line dropped), each restored. Changes made at landing on the code review's findings: the no-retry test's expected string is written with the `\u2026` escape so the module stays ASCII (L5-1); the `setTimeout` stub records each callback with its delay and the tests assert the timer whose callback is `redirectToResults`, so a timer at 3000 ms that never redirects no longer passes (L5-2; proven by planting `setTimeout(function () {}, 3000)`, which fails both new tests). Carried Task 3 review note (L5-3): the docstring of `test_the_heatmap_copy_names_the_shade_the_grid_draws` now states the clause rule ("more", never "fewer" or "less"); docstring only. Deviations: none. Edited existing tests: `test_a_failed_album_run_is_announced_once_by_the_alert` (its markup moved unchanged to the module constant `ALBUM_LOADING_MARKUP`); `test_the_heatmap_copy_names_the_shade_the_grid_draws` (docstring only, L5-3). Validation: `pytest -q` -- **2974 passed**.

### 2026-10-23 - The unmatched-report links lose their arrows

Side task, no batch tag: removed the trailing arrows from the Results page's two unmatched-report links, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent: "The arrows should go." (2026-10-22). `templates/results.html`: "view breakdown" (under the Unmatched figure) lost its arrow and the side-rail "Open unmatched report" lost its arrow, so both read as plain words. New test `test_results_links_to_the_unmatched_report_read_as_words_alone` in `tests/test_routes.py` reads the two links' text after the site header and asserts exactly those words; proven red on the unchanged tree and by four planted defects (`&rarr;` after either text, an aria-hidden arrow span after either text), each restored. Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2972 passed**.

### 2026-10-23 - The heatmap copy says what the grid draws

Side task, no batch tag: rewrote the heatmap index lede and preview card to say what the grid draws, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent: the copy must describe the grid truthfully (the owner accepted the live UI on 2026-10-22 and 2026-10-23).

What changed and why: the lede and the preview said darker meant more plays while `rocketColor` draws more plays brighter, and the preview promised a longest streak the result does not show. The lede, a dt/dd preview legend and its CSS (`static/css/heatmap.css`, `templates/index.html`, `templates/partials/_heatmap_form.html`) come from the owner's accepted WIP patch, unchanged. Two new tests in `tests/frontend/test_heatmap_pure_functions.py` compare the copy with the luminance the grid really draws and with the rendered KPI labels. Change made at landing on the code review's finding: `test_the_heatmap_copy_names_the_shade_the_grid_draws` also requires the clause that names the shade to tie it to more plays, because "Brighter squares mean fewer plays" named the right word in the wrong direction and passed; planting that in the preview, or "brighter for fewer plays" in the lede, now fails it.

Deviations: none. Edited existing tests: none. Mutations: copy word swapped in either place, `ROCKET_STOPS` reversed, "current" -> "longest", "daily average" dropped, "more" -> "fewer" in either copy -- each fails one new test.

Validation: `pytest -q` -- **2971 passed**.
