<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0029

### 2026-09-30 - Partial runs disclosed on Results; forms gate waits for requests

Side task, no batch tag: partial runs disclosed on Results and a forms gate that waits for requests, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Results: a run degraded by dropped Last.fm pages or a Spotify/Deezer outage says so in one `role="status"` line above the stat block and table. The orchestrator now records the kind as data beside the sentence (`jobs.record_partial_source`, stat `partial_data_sources`, values `lastfm` and `provider`), and `_partial_run_notice` in `routes/album_flow.py` reads that, never the wording. Last.fm's own sentence is shown as written; the provider case is reworded for the results page. The link to Unmatched appears only when an album is filed as `provider_unavailable` ("could not be checked"), not for any unmatched album. The link has the focus ring and, under `any-pointer: coarse`, a 44px height. The loading page's `#partial-warning` is `role="status"`.

Announcements: `.wait-panel__error` (shared by both loading pages) is `role="alert"`, chosen over keeping the text in a live region because the heatmap page clears its phase line on error. On the album loading page `showFailure` also empties the polite phase line, so a failure is read out once.

Forms gate: the sleep-then-count waits are a bounded poll on the request count (`_wait_for_held`: 5 s bound, 150 ms settle so a surplus request is still caught), and the 503 check and the network-failure check wait, bounded, for the page's message instead of a fixed 100 ms. The remaining 100 ms wait is a negative proof (the verdict must not change). `record_load_faults` in `frontend_gate.py` prints app stylesheets, scripts and fonts that failed to load beside any FAIL (advisory; it never changes pass or fail). Live probes: with the debounce raised to 1200 ms the old module failed three checks and the new one none; with the message written 600 ms late the check passes, and with the wait removed it fails.

Smaller: both privacy route tests assert the real message; the CI no-secrets guard reads the whole workflow; comments that cited review ids or described the spotlight wrongly say the reason in words. `routes/album_flow.py` now imports `unmatched` (SESSION_CONTEXT dependency graph updated). The Task 30 breaker test also asserts that every album still went to Deezer after the breaker tripped.

Bookkeeping: F-B23-41 (row links under 44px, the gate measures no populated row) and F-B23-42 (spotlight rotation has no pause control for touch or keyboard readers) are filed; F-B23-39 names the forms gate's sleep against the 300 ms debounce as the cause of its "held 0" flake.

Edited existing tests: `test_results_loading_private_profile_does_not_start_a_job`, `test_results_loading_existing_private_user_is_refused_after_the_exists_check`, `test_test_job_env_passes_no_secret`, `test_deezer_throttling_degrades_and_records_the_album_as_unavailable`, `test_spotify_search_outage_degrades_to_deezer_and_lists_the_rest_as_unavailable`, `test_a_spotify_detail_outage_for_a_matched_album_is_unavailable_not_no_match`, `test_one_over_cap_retry_after_stops_the_jobs_remaining_spotify_searches` and `test_process_albums_partial_cache_token_failure_uses_cached_results` (each also asserts the recorded kind, the breaker test also that Deezer was asked for every album).

Validation: `pytest -q` -- **2487 passed**.

### 2026-09-30 - Provider refusals read as outages; an all-miss run finishes

Side task, no batch tag: provider refusals read as outages and an all-miss run finishing, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Refusals: a Spotify 400 or 403, a 401 that a freshly fetched token does not cure, and a Deezer HTTP 429 (with its Retry-After) or 403 are "could not answer" (`ProviderError`), never "answered, no match"; a genuine empty search and an album-details 404 stay answers. Spotify tokens are cached with a 60 s margin, a 401 drops the cached token once and retries once, and every call adopts a valid cached token before its first request, so a refresh is paid once per job (the batch one-by-one fallback is handed the refreshed token too). An in-job Last.fm 403 reads the body: only error 17 raises `PrivateProfileError`; any other 403 logs the status and error number (no body, no username) and follows the existing unavailable path. Last.fm's error-code page names no HTTP status per error code, so "403 means private" was never documented.

Per-job breaker: `SpotifyBreaker` in `spotify.py`, carried in a `ContextVar` set by `spotify_job_breaker()` around the Spotify phases of `_fetch_spotify_misses`, so signatures are unchanged and a concurrent job has its own. It trips on a Retry-After above the cap, on three refusals in a row with no answer between, or on a second 401 after a fresh token. It is checked at each function's entry and again inside every attempt, right after the semaphore and the rate limiter are held and immediately before the request: at entry alone every queued task had already passed the check before the first 429 came back (a reviewer's run sent 100 of 100 requests). A tripped breaker ends the retry loop at once and the call is unanswered without a request; Deezer still runs. A refusal logs one WARNING per kind per job (operation and status) and one summary line when the job's block ends; the retry helper no longer logs it as an ERROR. Concurrent first 401s can fetch the token up to the number of in-flight calls times (no lock); accepted, bounded by the search concurrency.

All-miss run: owner ruling 2026-09-30, "Finish, show Unmatched": a run where every album is "no match" on both providers succeeds with no albums and each album listed as `no_spotify_match`. `_detect_enrichment_total_failure`, its call and its seven tests are gone; the outage rule in `_fetch_spotify_misses` (Spotify answered nothing and Deezer enriched nothing) is unchanged, and "Spotify said no match for every album, Deezer could not answer for any" now has an end-to-end test (it succeeds; each album is listed unavailable). `top-albums-sequence.md` no longer draws the removed branch. The Results-page copy for this outcome is the frontend task's.

Smaller: `jobs.succeed` and `jobs.fail` refuse a second ending and log it (`start` and `reset` reopen a job); `jobs.exists` replaces a `context(...) is None` probe in `release_checks`; a Deezer `/tracks` call that ends in a terminal error makes the album a miss (not persisted with empty durations), while a body of JSON null keeps it with no durations; the `worker.py` docstring says what each caller publishes. `spotify_rate_limited`, `lastfm_rate_limited` and `job_interrupted` remain valid codes that no pipeline publishes (`spotify_rate_limited` is only a per-call code, `lastfm_rate_limited` is never raised, `jobs.mark_interrupted` has no caller); none is deleted, the UI maps them.

Bookkeeping: F-SWE-3 (a Spotify 5xx "ends the attempt loop after one try") is closed, since a 5xx is retried and raised as `ProviderError`; F-B23-40 files the Last.fm username in log lines.

Edited existing tests: `test_page_fetch_reports_a_private_profile_without_retrying`, `test_succeed_clears_an_earlier_failure`, `test_fail_internal_error_replaces_results_and_is_not_retryable`, `test_fetch_spotify_album_details_batch_non_200_returns_empty_dict`, `test_fetch_spotify_access_token_refreshes_expired_token` and `test_fetch_deezer_album_keeps_the_album_when_the_track_list_is_unreadable` (a JSON-null case added). Removed with the function: the seven `test_detect_enrichment_total_failure_*` tests.

Validation: `pytest -q` -- **2462 passed**.

### 2026-09-30 - Diagrams and README checked against what the PR ships

Side task, no batch tag: the pre-merge pass over the diagrams and README, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Diagrams: every module-level import in `scrobblescope/`, `scripts/docsync/`, the worktree guard and the frontend-gate slices was read by an `ast` walk and compared with the drawn edges; the call paths of both sequence diagrams were read against `orchestrator/`, `heatmap.py` and `routes/`. `runtime-system.md` gained two missing edges (`lastfm.py` to `errors.py`, `cache.py` to `utils.py`) and `delete` in the `jobs.py` interface list. `top-albums-sequence.md` no longer shows `enqueue_release_check` as a `jobs.py` call (it is `release_checks.py`) and records the below-threshold exclusions only after the Last.fm failure check, as `_fetch_job_albums` does. `heatmap-sequence.md`, `development-cycle.md` and `documentation-tooling.md` needed no change. "Last verified" in `docs/ARCHITECTURE.md` is now 2026-09-30.

README: the section on the foundation work describes what the PR ships, in plain prose with no ids or pointers (provider throttling no longer read as "no match", names out of provider failure lines, the fourth Unmatched group, the keyboard heatmap, the spotlight pause, the job module, Repo Assist removed); it says in one sentence that job persistence and the Last.fm restructuring come next. The bare worktree-guard bullet has a body, "Three reasons have shipped" says a fourth comes with this work, and the work-package wording elsewhere in the page is plain.

Dashboard: SESSION_CONTEXT Sections 3 and 4 were compared with source; the `utils.py` line names `log_failure` and `cancel_and_drain`, and "Last updated" is 2026-09-30. The `_search` and `_details` edges the task-18 review flagged were already correct. DEVELOPMENT.md: `--check`, the preflight, the worktree guard and `tailwind_build.py --check` were run and behave as written; the planted-defect demonstrations are scratch-copy runs and were not repeated.

Validation: `pytest -q` -- **2424 passed**.

### 2026-09-30 - Doc and hygiene findings from the third review cleared

Side task, no batch tag: the doc and hygiene findings, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Code: `cli._snapshot` (the staleness baseline of `--close-batch`) raises `SyncError` on an unreadable file, like `_read_text`, instead of a bare `OSError` traceback. The orphaned gh-aw lock file `.github/aw/actions-lock.json` and its `.gitattributes` line are deleted. Comments only: "for every miss" in the `orchestrator/__init__.py` docstring, and two over-long comment blocks in `tests/test_pipeline_integration.py` rewrapped.

Docs: how an album gets its release date is explained once, in `docs/architecture/runtime-system.md` (it now also holds the old "displayed release year" bullet and names `process_albums` and `_persist_new_metadata`); `_build_results` links to it; the README keeps its own plain summary (owner rule: no pointers in the README). `docs/design/RECONCILIATION.md` still retells the release-date rationale; it is a dated design record, seen and left. The release-scope table is written once, in `domain.release_window`'s docstring, which names the wording sites and says its list is not exhaustive; `_get_user_friendly_reason` and `_get_filter_description` say "wording only" and link to it. The finished plan `docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md` (about line 27) says a commit on another branch is refused by the worktree guard; it was seen and left as point-in-time. The ignored local `CLAUDE.md` of the batch worktree was corrected (the guard reports WT003 but the hook is advisory); it is not in the commit.

Bookkeeping: the log archive's heading date is corrected to 2026-09-29 (no DOC025); F-B23-33's problem statement is one sentence; F-B23-29 is closed and its leftovers are F-B23-38; F-B23-39 records the gate's intermittent failures.

New test: `test_snapshot_raises_sync_error_for_an_unreadable_file` (in `TestPublicationSafety`); no existing test was edited or moved.

Validation: `pytest -q` -- **2424 passed**.

### 2026-09-30 - Small frontend findings from the third review cleared

Side task, no batch tag: small frontend findings F-B23-27, F-B23-28 and the frontend part of F-B23-29, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Layout: long artist credits shrink inside their Results cell (`.album-info { min-width: 0 }`); the below-threshold figures wrap below 768px instead of clipping "1234 plays"; four unmatched panels stack in two columns, the release-scope panel spanning the right column and the first, third and fourth panels down the left (a new gate check, `four_panel_stack_failures`, holds the stacking; screenshots at 1280px and 1920px checked).

Behaviour: Escape closes hover and tap heatmap tooltips, and the keyboard tooltip follows a scroll at once (no animation-frame lag); a reduced-motion or single-candidate spotlight card reserves no height, and a rotating one measures without a link it does not own; `pointerenter` needed no seed (Chromium fires it after a layout change; the test says Chromium only, as the behaviour runner drives no other engine). Markup and style: axis labels are `aria-hidden`; one 12px `.provider-badge` rule in the narrow face (gate judge `provider_badge_failures`); `default('', true)` on two data attributes; results.js block-level functions are `const` arrows; dead `content` lookup, `img` reset, per-call `reducedMotion` read and `formatDurationMobile` removed; unresolvable comments rewritten.

Tests: three gate tests that launch Chromium (`test_the_layout_check_keeps_the_rotation_going_and_sees_every_width`, `test_the_hold_check_focuses_then_hovers_and_counts_the_periods`, `test_the_opacity_sampler_records_the_artist_and_runs_across_rotation_periods`) were unmarked and would have failed CI's `-m "not browser"` coverage step; they carry `@pytest.mark.browser` (with Playwright made to raise, `-m "not browser"` ran 3 failures before and none after). The stale "43 tests" comment in `test.yml` holds no number now.

Edited existing tests: `test_unmatched_view_renders_artwork_in_every_reason_group` (fourth reason, order pinned); `test_reduced_motion_keeps_first_confirmed_artist_after_failed_hydration` and the `spotlight()` helper in `results_behavior_tests.py`; `test_the_layout_probe_reads_words_by_the_lines_their_characters_sit_on` (deleted, replaced by a Chromium test of the probe); the `keepRotating` text assertions in three spotlight-photo gate tests (now run the mock in Chromium); `test_a_badge_with_no_narrow_token_to_compare_fails` (pins the message). The gate's `check_unmatched_report` seed carries four digits of plays and its threshold expectation changed with it.

Validation: `pytest -q` -- **2423 passed**.

### 2026-09-30 - One rule decides a failed run; tracebacks kept at DEBUG

Side task, no batch tag: one rule for a failed run and tracebacks kept at DEBUG, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Run failure: a Top Albums run fails as the retryable `spotify_unavailable` only when Spotify gave nothing for every miss (no token, or every miss a search it did not answer or a matched album whose details it did not answer), nothing was cached before, and Deezer enriched nothing; `_detect_enrichment_total_failure` keeps only the case its rows prove (every album `no_spotify_match`), and a mix with zero results follows the ruling's letter and ends as a success with no albums. A Deezer album body that cannot be read is a miss; a track list that is missing or unreadable keeps the album with no durations. `utils.cancel_and_drain` is public (the private `lastfm` name is deleted); lastfm, the Deezer fallback and the search phase use it, and the details fan-out and the one-by-one details gather in `spotify.py`, which lacked it, now drain too (the search fan-out already did), so no remainder of F-B23-24 is left.

Tracebacks (owner ruling 2026-09-29, "Extend the rule"): `utils.log_failure(message, level)` logs the exception's class at the level and the traceback at DEBUG; it replaces all ten `logging.exception` sites, and the `{exc}` database messages at WARNING (`orchestrator/_cache.py`, `release_checks.py`, `cache.py` incl. the connect retries) follow it. Eight new `# noqa: BLE001` mark the sites ruff no longer sees as logged (two more sit inside `worker.py`'s existing noqa'd except). The rule is added to `docs/agents/global-rules.md` Rule 6. Task 25's "owner question pending" is answered here. Also: `RedactingFormatter`'s docstring is an open list, `retry_with_semaphore`'s docstring is corrected, `api_logging._record` derives elapsed itself, the dead gather path of `fetch_pages_batch_async` is deleted, `test_pipeline_integration.py` cites functions and F-ids instead of stale line numbers, and `docs/architecture/top-albums-sequence.md` states the one rule.

Edited existing tests: `test_progress_cb_none_uses_gather_path` (deleted, replaced by `test_fetch_all_without_a_progress_callback_still_fetches_every_page`), `test_fetch_all_cancels_sibling_fetches_when_one_page_raises` (parametrize ids only), the `_record` call sites of four `test_api_logging.py` span tests, and `test_lookup_cached_original_release_failure_is_non_fatal` (asserts the class, not the text).

New tests: `test_fetch_deezer_album_reads_a_strange_body_as_a_miss` (album bodies only), a keep-the-album test for an unreadable track list, `test_one_by_one_details_cancel_and_settle_siblings_on_an_unexpected_error`, and six more sites (both cache.py connect-retry lines, the release_checks persist and connection-close lines, and the schema-out-of-date variants of the three remediation messages) in `test_fail_open_database_sites_log_the_class_only_at_warning`.

Validation: `pytest -q` -- **2410 passed**.

### 2026-09-30 - Tests that fail on the defect they guard

Side task, no batch tag: tests that fail on the defect they guard, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Closes F-B23-31, whose five tests survived the mutant they exist for, and four review minors. Each mutant was planted in a scratch copy and the test shown red; the decisive line of each is in the commit body. S1-7: the results-route spotlight test asserts every seed `image_url` is empty. S1-8: a new test starts the clock at 100, records the later-starting call first and expects a 6.0s span. S1-9: the fetch ledger counts `CancelledError` (four) under `asyncio.timeout(2)`. S1-10: the fixture's Spotify URL is no longer the code's fallback, and two orchestrator tests take `SPOTIFY_ALBUM_DETAILS_MOCK`. S2-24: whole layout objects for a beside and a stacked header, `rocketColor` between stops, and the headline and legend captions. Also: the `private_profile` 403 route case; the frontend gate's spotlight hold check now resizes the card with focus on the link and a linkless candidate (a `keepLink` guard); the unmatched check seeds the fourth reason, `provider_unavailable`, and asserts four panels, its hint and its row note (both run in Chromium only, where the gate runs them; the R6 live probe was red on the planted defect and green, in Chromium and in Firefox by direct run); the docsync close-batch test fails when `_snapshot` reads through `Path.read_bytes`; the `run_async_in_thread` DEBUG record is selected by its message; the two heatmap ordering tests share one helper.

Edited existing tests: `test_results_page_samples_five_unique_artists_from_aggregate_top_ten`, `test_results_job_state_matches_http_status` (a fourth parameter), `test_fetch_all_cancels_sibling_fetches_when_one_page_raises` (through `_PageFetchLedger` and `_run_fetch_all_with_raising_page`), `test_run_async_in_thread_error_line_carries_the_class_never_the_message`, `test_process_albums_cache_miss_fetches_and_persists`, `test_process_albums_db_unavailable_falls_back`, `test_close_batch_proves_every_read_source_before_publishing`, `test_the_page_repositions_its_tooltip_before_every_screenshot`, `test_the_settle_wait_runs_before_every_screenshot`, `test_the_hold_check_focuses_then_hovers_and_counts_the_periods`, `test_a_timed_out_hold_wait_is_judged_by_the_tick_count` and `test_a_crashed_page_during_the_hold_wait_propagates` (through `_run_hold`); the fixture `tests/fixtures/spotify_get_album.json` changed its URL, read by `test_spotify_fixture_has_every_field_the_app_reads`.

Validation: `pytest -q` -- **2365 passed**.

### 2026-09-30 - Errors classified by type in both pipelines; an unrecognised error is ours

Side task, no batch tag: typed error classification, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Typed `UserNotFoundError`, `PrivateProfileError` and `ProviderError(source, kind)` replace message substrings: the classifier reads the exception's type only. The album pipeline publishes `internal_error` (not retryable, no exception text) for an exception nothing classifies, as the heatmap does; `jobs.fail_unclassified` and the code `unknown` are deleted. Owner ruling 2026-09-30 (degrade, fail if all fail): a Spotify search, detail call or token request that cannot be answered no longer cancels its siblings or fails the job. That album falls back to Deezer and, if Deezer misses it too, is listed under a new fourth unmatched reason, `provider_unavailable` ("Could not be checked"), never as "no match"; each row's text says which provider was down and which had no match. The job fails `spotify_unavailable` (retryable) only when Spotify answered no search and Deezer enriched nothing. Deezer and MusicBrainz 5xx and timeouts raise `ProviderError` (Deezer: the album is listed unavailable; MusicBrainz caches no finding), and a Deezer search body of an unexpected shape reads as a miss. The retry helper treats only network and JSON-decode errors as "unavailable"; `Retry-After` is parsed defensively and `reraise` narrowed. Also fixed: Deezer track with no title key (Codex 4140219711) and a throttled call read as "no match" (Codex 4140219720). README's Unmatched feature list now names four groups. Closes F-B23-16, F-B23-21 and F-B23-22; files F-B23-37 (P3: a Deezer 200 "busy" body, unverified).

Deviation from the brief: a Last.fm 429 stays `lastfm_unavailable` (the brief said `*_rate_limited`); both are retryable and raising from the page fetch would end partial-page tolerance.

Edited existing tests: `test_fetch_recent_tracks_page_404_raises_user_not_found`, `test_fetch_all_cancels_sibling_fetches_when_one_page_raises` (through `_PageFetchLedger` and `_run_fetch_all_with_raising_page`) and `test_page_fetch_reports_a_private_profile_without_retrying` in `test_lastfm_service.py`; `test_classify_exception_to_error_code_spotify_rate_limited` and `test_classify_exception_to_error_code_user_not_found` (typed args) and `test_classify_exception_to_error_code_unclassified_returns_none` (replaced by `..._ignores_message_text`) in `test_orchestrator_helpers.py`; `test_fetch_and_process_unclassified_exception_publishes_unknown` (renamed `..._publishes_internal_error`); `test_user_not_found_crash_publishes_user_not_found` in `test_heatmap.py`; `test_fail_unclassified_keeps_the_raw_text_and_is_retryable` (renamed `test_fail_internal_error_replaces_results_and_is_not_retryable`); `test_search_returns_none_on_non_200_non_429` (500 changed to 404) and `test_search_failure_lines_carry_no_album_or_artist` (expects `ProviderError`) in `test_spotify_service.py`, plus `test_fetch_spotify_album_details_batch_non_200_returns_empty_dict` (500 changed to 400: a 5xx is now retried and reported unanswered); `test_search_failure_lines_carry_no_album_or_artist`, `test_fetch_deezer_album_returns_none_when_album_details_fail` and `..._when_tracks_fail` (renamed `..._raises_unavailable_when_...`) in `test_deezer_service.py`; `test_lookup_failure_lines_carry_no_album_or_artist` in `test_musicbrainz_service.py`; `test_run_spotify_search_phase_all_misses_returns_empty_maps` (unpacks the fourth value) in `test_orchestrator_fetch_spotify.py`; and in `test_routes.py` the shared helper `_seed_every_unmatched_reason` (now seeds a `provider_unavailable` row), used by `test_unmatched_view_row_note_says_what_is_particular_to_the_row`, `test_unmatched_view_names_track_counts_only_on_the_threshold_panel` and `test_unmatched_view_portrait_image_is_not_lazy` (three portraits, not two).

Validation: `pytest -q` -- **2341 passed**.

### 2026-09-30 - Make four gate checks judge what they name

Side task, no batch tag: four frontend-gate checks, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

S4-2: the spotlight photo fade check now keeps the rotation ticking and fails unless a swap fell inside its 1000ms sampling window. S4-5: the unmatched focus-ring check counts only pixels the ring adds (a second shot, still focused, with the ring forced off). S4-6: `_PHOTO_PAINT_JS` intersects every clipping ancestor and flags `clip-path`, and the first photo check now runs the crop judgement too. S4-10: the gate serves threaded, so an idle connection cannot stall a check. The heatmap ring reading is made deterministic (box read before and after the shot, retake on movement, scroll nudge for the tooltip, fonts-and-frames wait) for the 2026-09-29 flake, and the hold check catches only Playwright's `TimeoutError` (Codacy B110). Each changed check was proved on a planted defect, red on the old code and green on the new; a browser test runs the paint probe on a clipping grandparent.

Edited existing test helper: `_crop_overlay_page` in `tests/scripts/dev/test_frontend_gate_spotlight_photo.py` (the first photo check now also reads the paint probe and the new sample shape), used by `test_a_pseudo_element_scrim_and_a_transform_animation_are_reported`, `test_the_opacity_sampler_records_the_artist_and_runs_across_rotation_periods` and `test_the_first_photo_check_also_judges_the_crop`. Filed F-B23-36 (P3: S4-3, S4-4, S4-7, S4-8, S4-9, S4-11, the tooltip note, the flake as fixed by inference).

Validation: `pytest -q` -- **2277 passed**.

### 2026-09-29 - Second architecture review tracked and scheduled

Side task, no batch tag: the second deepening review of the codebase is tracked at `docs/history/reports/architecture-review-20260930-0040.html`, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The review walked the routes, the orchestrator's phase modules, the provider contract, the cache, the worker and the results, spotlight and loading scripts, and checked every candidate in the five earlier architecture reports against the code: four done, three partial, five open, five already planned. Two findings are live defects, confirmed by reading the code: three providers log the album and artist they searched for at ERROR level, against the logging module's own rule; and the album route's single `try` treats an outage in the user or privacy check as a failed registration-year hint and starts the job anyway. Four album filters (`sort_mode`, `release_scope`, `decade`, `limit_results`) are never validated.

Section 3 now says that these seams come before the Spotify import and which work package each one gates. The owner added the report to `docs/history/reports/`; no code changed.

Validation: `pytest -q` -- **2223 passed**.

### 2026-09-29 - The job module gives a job's life one interface over a storage seam

Side task, no batch tag: the job module (`scrobblescope/jobs.py`), a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

A job's rules (one ending, results or an error; the lease renewed only by writes; results and 100% in one write) lived in seven callers of `repositories.py`, and F-B23-22 was the proof: two pipelines, two failure answers. They now live in `jobs.py`: `create`, `advance`, `report_phase`, `record_stat`, `record_unmatched`, `succeed`, `update_result`, `fail`, `fail_unclassified`, `reset`, `mark_interrupted` and the reads, over a `JobStore` seam with one adapter, `MemoryJobStore` (the old dict, lock and TTL). Task 20 adds the Postgres adapter and reruns the same `tests/test_jobs.py` suite through its `STORE_FACTORIES`. `repositories.py` is deleted with no shim and every caller, including the eight frontend-gate modules, is migrated. The progress vocabulary is folded in: five named bands replace the `phase` literals and the `base + int(span * done / total)` arithmetic, and both Last.fm callbacks take three arguments, so `_notify_progress_cb`'s signature sniffing is gone. `job_interrupted` joins `ERROR_CODES`. Percent values are unchanged.

Owner ruling (2026-09-29): seam commits may edit existing tests, and each edited test is named in the commit body; `BATCH23_DEFINITION.md`'s compatibility list, F-B23-1 paragraph and Acceptance bullet are amended to say so (Part A's own line is left as written). Edited existing tests: call sites and patch targets only, plus the assertions dropped or changed, each named in the commit body with where it is still guarded: `test_progress_callback_sends_correct_percentages` (the 100% dict, the error keys and the 0% init dict), `test_happy_path_stores_correct_result_dict` (`succeed` writes the results and 100% as one write) and `test_seed_spotlight_job_seeds_several_artists_and_marks_it_done` (the separate 100% write); the Last.fm progress callback also takes three arguments. `tests/test_repositories.py` keeps only its database-helper tests; its job tests moved to the new `tests/test_jobs.py` (45 tests), and one test was renamed. Not done here: `mark_interrupted` is not wired at startup (Task 20 wires it with the database adapter); `fail_unclassified` keeps F-B23-22 open. Test modules 81 to 82.

Validation: `pytest -q` -- **2254 passed**.

### 2026-09-29 - Refuse a stale or unfinished docsync publication; ignore CRLF in archives

Side task, no batch tag: docsync publication safety and CRLF archive drift, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

An interrupted publication leaves history only in the git-ignored `.docsync.journal` and both modes used to exit 0 (S3-2). New DOC026 makes `--check` exit 1 while the journal exists, and `--fix` replays it first, under the lock, restoring every file to its pre-run bytes; it refuses if a journalled file was edited since. Chose recovery on the next run over reordering the writes, since restoring pre-run bytes and re-planning cannot lose history for any file mix. Publication now compares against the bytes each file had when the plan first read it, so a concurrent edit is refused and nothing is written (S3-3). `ArchiveStore._diff` folds CRLF to LF, so a CRLF checkout of a paginated archive is not drift while a real content change still is (S3-7). Non-UTF-8 documents exit 2 with a diagnostic (S3-1), a path outside the repository is named instead of crashing (S3-4), and an unchecked box whose outcome says resolved or no action is DOC016 (S3-6). Review minors fixed here: a test for the state a real kill leaves (journal and stale lock), the DOC016 and DOC026 catalogue text, and `_snapshot`, so the baseline loop no longer makes the read-coverage test true by construction.

Edited existing tests: `test_close_batch_proves_every_read_source_before_publishing` (also records `Path.read_bytes`, since documents are read as bytes) and `test_stated_catalogue_helper_rejects_a_mismatched_list` (the sentence gains DOC026). Closed F-DOCSYNC-19; filed F-B23-35 (P3, S3-5, S3-8, the `.gitattributes` guard). No new test module.

Validation: `pytest -q` -- **2252 passed**.

### 2026-09-29 - Repo Assist removed; CI job holds no provider secrets

Side task, no batch tag: removing the Repo Assist workflow and CI's provider secrets, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Owner ruling (2026-09-29): Repo Assist is not configured properly and is dropped; CI is robust without it. `repo-assist.md`, `repo-assist.lock.yml`, the README sentence and the Repo Assist assertions in `tests/test_ci_workflows.py` are gone, and the S6-2 hardening (a docsync.toml guard for its PRs) is not built. S6-1 stays: `test.yml` no longer passes LASTFM_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET or SECRET_KEY at job level. No step reads a real key: `conftest.py` and `frontend_gate.py` supply placeholders, and a step that ever needs one takes it in its own `env:`. Proved by running the suite and the frontend gate with the four variables unset. The two comments that said CI passes the keys from repository secrets are corrected.

Edited tests: every test in `tests/test_ci_workflows.py` asserted on the Repo Assist workflow, so the module is rewritten around `test.yml`: `test_test_job_env_passes_no_secret` (job-level env carries no secrets reference) and `test_env_reader_flags_a_secret_and_a_missing_block`. Filed F-B23-32, F-B23-33 and F-B23-34 (P3, S6-3, S6-4, S6-5). Owner action: delete the Repo Assist repository secrets (for example CODEX_API_KEY, COPILOT_GITHUB_TOKEN) in GitHub settings if nothing else uses them.

Validation: `pytest -q` -- **2238 passed**.

### 2026-09-29 - Provider-failure docstring made true; async-thread traceback kept at DEBUG

Side task, no batch tag: the `RedactingFormatter` docstring corrected and `run_async_in_thread`'s traceback moved to DEBUG, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The land review found the docstring still said `run_async_in_thread` writes the api_key in its message; it now names its DEBUG traceback and `get_cached_response`'s debug line as the two remaining sites. Per the owner's Q5 ruling (2026-09-29, "At ERROR, log the exception type only; the full traceback goes to DEBUG"), `run_async_in_thread` keeps its class-only ERROR line and adds a DEBUG line with `exc_info=True`. The caplog test `test_run_async_in_thread_error_line_carries_the_class_never_the_message` now asserts the ERROR record has no exception info or message and a DEBUG record carries the traceback; proven red with the DEBUG line removed.

Validation: `pytest -q` -- **2242 passed**.

### 2026-09-29 - Provider failure lines name the operation, never album, artist or track

Side task, no batch tag: provider failure log lines carry an operation key and an exception class, not names, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Architecture pass 2, B-2: `retry_with_semaphore` was handed a free `error_label` built from album and artist, and logged it and the exception message at ERROR, so Spotify, Deezer and MusicBrainz failures wrote the listener's names (and aiohttp's request URL) into the logs. The helper now owns what a failure line may say: callers pass an operation key (`spotify.search`, `deezer.album_tracks`, `musicbrainz.lookup`, `lastfm.page <n>`) and each line reads `Error in <key>: <ExceptionClass>`, the message dropped. The Spotify 429 warning, both artist-spotlight warnings (`spotify.py`, `routes/api.py`), the registration-year warning in `routes/album_flow.py` and the `_results.py` skip debug line follow the same rule. `api_logging.py`'s docstring names the helper as the enforcement point.

Same class, found on landing: `lastfm.py` logged `body[:200]` on an unexpected status and on invalid JSON, and a recenttracks body carries track, artist and album names; both lines now give status, byte length and content type only. `run_async_in_thread` logged `str(e)` with a traceback at ERROR; it now logs the class only, at ERROR without a traceback.

One caplog test per provider, per helper, per Last.fm line, for `run_async_in_thread`, the `_results` line and the two route lines, each proven red with the old line restored. Edited existing tests, all of which asserted leaked content: the Last.fm page-failure label (`test_lastfm_service.py`), the Last.fm invalid-JSON body quote (same file), the Spotify spotlight network-error message (`test_spotify_service.py`), and the `run_async_in_thread` redaction test (`test_api_logging.py`, which no longer sees a message to redact and now asserts the class line and the absent key).

Known, not fixed: `spotify.py` logs the provider response body on a batch failure (neither a name nor an exception message); the `logging.exception` sites that format only a Last.fm username still write tracebacks that carry `str(exc)` (owner question pending: extend the rule to tracebacks?).

Validation: `pytest -q` -- **2242 passed**.

### 2026-09-29 - Spotify attribution holds in exports and forced colours; each link names its own provider

Side task, no batch tag: keeping the Spotify icon in the saved image and in forced colours, and naming each provider on its own link, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

S2-4 and S2-19: the "Save image" JPEG carried the Spotify icon at about 12px in Firefox (html2canvas paints a raster `<img>` in the clone at half size there; the raster itself was right). `results.js` now awaits `icon.decode()` on each shown icon, draws a raster at three times the box, and in `onclone` swaps the `<img>` for a `<canvas>` at the on-page box size; a failed decode aborts the export with an error toast, so there is no silent success without attribution. S2-11: `results.css` picks the icon file from `prefers-color-scheme` under `forced-colors: active`, not from the saved theme. S2-26: both icon `<img>` tags carry `width="236" height="225"` (the file's viewBox), so the line does not shift when the SVG arrives. S2-15: `results.js` builds one album-link tooltip per provider from the row's `data-provider` (Spotify keeps `album-link-tooltip`, others get `album-link-tooltip-<provider>`), and each link's `aria-describedby` names its own provider. S2-5: `unmatched.html` gives a coverless row with a non-Spotify provider the plain placeholder, with no artist-portrait slot, and the page attribution no longer counts such a row as Spotify content.

Two new frontend-gate checks, `export keeps spotify icon size` (Chromium and Firefox; measures the icon in the exported image at >= 21px) and `spotify icon follows system under forced colors` (Chromium). The gate is now 45 checks (measured after Task 10's check landed). Live probes: with the old `results.js` the export check is red in Firefox (`JPEG export shows the Spotify icon at 12.0x12.3px, below the 21px minimum`) and green in Chromium; with the old `results.css` the forced-colours check is red for both the system-light and system-dark cases; restored, both are green. One new `results_behavior_tests.py` test (`test_tooltip_names_the_provider_each_link_opens`) fails on the old JS, and 3 new tests in `tests/test_routes.py` fail on the old templates. No existing test edited.

Known limits: the Firefox canary now also runs the results-page export check (about 5s more). Forced colours is checked in Chromium only. Legacy unmatched rows with an empty provider still show a Spotify portrait, because they have no provider to exclude; only rows naming another provider get the placeholder.

Validation: `pytest -q` -- **2233 passed**.

### 2026-09-29 - The spotlight holds still while its link has focus or the pointer

Side task, no batch tag: pausing the artist spotlight rotation while its link has focus or the pointer is over it, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The 7s rotation used to rewrite the Spotify link's target while a keyboard user had it focused, and when the next artist had no link the focused link was hidden and focus dropped to `<body>`. `static/js/results-spotlight.js` now skips a tick while the pointer is over the card (`pointerenter`/`pointerleave`) or `card.contains(document.activeElement)`; reading `activeElement` instead of `focusin`/`focusout` with `relatedTarget` gives the same result for moves inside the card and stays right when the window loses focus. `reserveCardHeight` (the height reserve) skips the link while focus is in the card, so its measuring pass never hides or retargets a focused link. Reduced motion is unchanged. New frontend-gate check `check_artist_spotlight_holds_still_while_focused_or_hovered` (Chromium and Firefox) counts ticks in `window.__spotlightTicks`, waits for 3 with no fixed sleep, then asserts focus, href, label and artist are unchanged for keyboard focus and then pointer hover; 4 new tests in `tests/scripts/dev/test_frontend_gate_spotlight_photo.py`, no existing test edited, and a `DEVELOPMENT.md` bullet.

Live probe (R6, code phase): with the pause removed the check went red in Chromium (`spotlight hold (focus): label changed from 'View Godspeed You! Black Emperor on Spotify ...' to 'View Sufjan Stevens ...'`, and the same for pointer); restored, it is green. Mutating `if passed < HOLD_PERIODS` to `if False` fails 2 unit tests. Known limit: the mock gives every candidate a link, so the gate cannot show the no-link-candidate-while-focused variant directly; the pause guards it.

Validation: `pytest -q` -- **2230 passed**.

### 2026-09-29 - User checked before privacy; only a public verdict cached; payload edge cases

Side task, no batch tag: checking the user before privacy, caching only a public verdict and handling Deezer and Last.fm payload edge cases, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

`results_loading` now asks `check_user_exists` first, so a missing user gets "User 'x' was not found on Last.fm." (a 200 re-render of `index.html`, accepted: it matches this route's other form errors) and the privacy check never runs for it. `check_profile_is_public` never caches a private verdict (error 17 in a 200 counts as private), caches only a body with a `recenttracks` dict, and treats a cache hit as public; `check_user_exists` maps error 6 in a 200 to not found and caches only a body with a `user` dict. A new `private_profile` code in `ERROR_CODES` (lastfm, not retryable) is raised by `fetch_once` on a 403 or error 17 without retry, classified through `errors.PRIVATE_PROFILE_MARKER`; the album results page answers it with a 403 and a "make listening public" detail. Browser check: `heatmap.js` and `loading.js` read the server's `retryable` flag and message, keep no code-to-message map, so nothing changed there. `fetch_deezer_album` skips a null or non-text track title; the Deezer fallback tasks run under try/finally `_cancel_and_drain` (no TaskGroup). `_normalise_track_list` turns a lone `track` object into a list before `_is_well_formed_page`, which now refuses any other non-list `track`. A cancelled request logs at DEBUG and is not recorded. New edges `lastfm -> errors` and `_deezer_fallback -> lastfm` are in the SESSION_CONTEXT graph. Closes F-B23-23, F-B23-24 and F-B23-30. Tests added in five existing modules, none edited; mutation-checked. Last.fm errors 10 and 26 remain unverified.

Validation: `pytest -q` -- **2223 passed**.

### 2026-09-29 - Spotlight artist name reads whole at every width; card height fixed

Side task, no batch tag: giving the spotlight artist name a whole line and holding the card height, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

From 1024px to about 1230px the name got a 46-110px column beside the fixed photo and broke inside words (S2-1), and the card changed height between candidates so the sticky rail jumped every 7s (S2-10). `.spotlight-card-content` now wraps and `.spotlight-details` has a flex basis, so the details drop under the photo whenever the card cannot give the name that column; the line-count `min-height` is deleted. `results-spotlight.js` `reserveCardHeight` renders each candidate once, measures the card and holds the tallest as `min-height`; `watchCardLayout` re-runs it when the card width changes and when fonts load. Photo rules and the 4px/8px radius step are unchanged. A new frontend-gate check, `artist spotlight name whole and card height fixed`, runs at 320, 390, 1024, 1180 and 1920px plus a 1024 to 1920 resize and fails on a mid-word break or a card height that varies across candidates. Live probe: with the old CSS the check fails in both browsers (`the name of 'Radiohead' breaks inside the word 'Radiohead'` at 1024px); with the old JS it fails (`the card height changes between candidates`); with `watchCardLayout` removed it fails after the resize. Tests: 7 new in `test_frontend_gate_spotlight_photo.py`, no existing test edited. A name needing more than two lines at the narrowest widths is still clamped (`line-clamp-2`, full name in `title`).

Validation: `pytest -q` -- **2207 passed**.

### 2026-09-29 - Heatmap strip scrolls under a swipe; one owner for the tooltip

Side task, no batch tag: letting a swipe scroll the heatmap strip and giving its tooltip one owner, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The per-cell `touchstart` in `static/js/heatmap.js` is now passive and only records the start point; the single document `touchend` listener decides a tap (moved at most 10 px, same cell, touchend cancelled to suppress emulated mouse events) and hides the tooltip otherwise, so a swipe is never cancelled. One `tooltipOwner` (hover, focus or tap) now owns the tooltip: focus owns it only under `:focus-visible`, scroll hides a hover or tap owner and repositions a focus owner, resize repositions or hides it, Escape hides it, and a handled key that moves nothing re-runs the ring decision. The tooltip is `position: fixed` in `static/css/heatmap.css` so it cannot widen the page. Two new frontend-gate checks cover it (`heatmap touch swipe scrolls and tap shows tooltip`, `heatmap tooltip has one owner`; 41 checks). No test module added or removed.

Validation: `pytest -q` -- **2195 passed**.

### 2026-09-29 - The stale-progress gate check replaces the job inside one page, so it can fail

Side task, no batch tag: making the frontend gate's stale-progress check able to fail, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The `pipeline state machines` check held the old job's first `/progress` request, then opened a new document for the replacement job, so the held response could never reach the guard in `heatmap.js` `pollProgress`; a request that never arrived also passed silently. The check now loads the old job once, holds its first poll (failing explicitly if none arrives), stubs the retry POST with a replacement job id, clicks the page's own Retry button so `currentJobId` changes in the same document, and only then fulfils the held response with stale progress and asserts it is not shown. Live probe: with the guard in `heatmap.js` replaced by `if (false) {`, the gate fails with `stale out-of-order progress response regressed aria-valuenow`; with the guard intact it passes. `heatmap.js` is unchanged. Tests: the replaced-job test is rewritten and a no-request test added.

Validation: `pytest -q` -- **2191 passed**.

### 2026-09-29 - Eleven findings filed from the third review of PR #245

Side task, no batch tag: filing the third review's open findings, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Eleven findings filed from the third review of PR #245: F-B23-21 to F-B23-31. They cover the Last.fm `reraise` breadth, the album pipeline's unclassified fallback (owner decision), the privacy-verdict caching and missing `private_profile` code, the Deezer null title, the mobile heatmap sizing, the unverified spotlight artist name, the two results and unmatched column defects, one cleanup bundle, the single-object Last.fm page, and the tests that survive their defect. F-B23-16 and F-B23-20 gain cross-references. Nothing closed; the archive is untouched. Docs only.

Validation: `pytest -q` -- **2187 passed**.

### 2026-09-29 - README corrected on where the Spotify icon appears

Side task, no batch tag: correcting the README's claim about where the Spotify icon appears, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The README's feature list said Spotify content is attributed "once per list". The icon partial is included twice in `results.html` (the list and the artist spotlight) and once in `unmatched.html`, so the bullet now names the Results and Unmatched pages and the artist spotlight. No code changed.

Validation: `pytest -q` -- **2187 passed**.

### 2026-09-29 - Architecture diagrams re-verified against source

Side task, no batch tag: re-verifying the architecture diagrams against the source, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The runtime diagram gains `heatmap.py` -> `errors.py` and `app.py` -> `api_logging.py`. Both sequence diagrams now draw the private-profile refusal (HTTP 403, Last.fm error 17). The development-cycle page says CI picks browser tests by marker, not folder. The control-plane diagram gains twelve docsync import edges it lacked. SESSION_CONTEXT Sections 3-4 gain `enrichment.py`, `deezer.py` and `orchestrator/_deezer_fallback.py` and lose a `repositories.py` -> domain edge that no import makes. No code changed.

Validation: `pytest -q` -- **2187 passed**.

### 2026-09-29 - DEVELOPMENT.md shows each tool in action

Side task, no batch tag: rewriting DEVELOPMENT.md so each tool is shown running, in plain English, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

DEVELOPMENT.md now opens with what the guide is for and shows each tool (docsync check and fix, the commit preflight, the Tailwind build and drift check, the frontend gate, archives) running, with captured output, and prose cut to plain English. Live counts are elided in quoted output (`<N>`, `<M>`) so no figure goes stale, and the `--fix --test-count N` example names no number. The DOC024 and archive-pagination sentences cite `AGENTS.md` "Doc Sync Rules" and `docs/architecture/documentation-tooling.md`. All declared anchors are kept.

Validation: `pytest -q` -- **2187 passed**.

### 2026-09-29 - README shows the incoming foundation work in plain prose

Side task, no batch tag: rewriting the README for a human reader, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The README now describes the incoming WP-0 work (what a listener notices, what an engineer notices), the September releases and the Spotify export plan. The wording follows the tree: Repo Assist adds missing tests and proposes dependency updates as draft PRs; the Spotify icon appears on Results, Unmatched and the artist spotlight; the gate claim covers only the checks the batch changed; the third review is described as still open on its frontend side. The review-fix commits land in PR #245 itself, so the README names no stacked PR. The retry-helper bullet was rewrapped without changing a word.

Validation: `pytest -q` -- **2187 passed**.

### 2026-09-29 - Bold-label citations resolve and archives age at 90 days

Side task, no batch tag: resolving a citation of a bold label ending in a colon, and ageing archive pages at 90 days, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Controller finding X-1: `declarations._headings` indexed `**Co-author prohibition:** Do NOT ...` in `AGENTS.md` only as "Co-author prohibition:" (colon included), because the label-tail pattern needs whitespace after the colon and the rstrip set had no colon. A citation of "Co-author prohibition" therefore failed DOC010. The heading now also indexes the label with its trailing colon stripped; the three existing forms are unchanged. The DOC010 entry in `docs/architecture/documentation-tooling.md` says so.

Owner ruling 2026-09-29, "update the 365 day cold storage rule to 90 days": `DEFAULT_ARCHIVE_COLD_DAYS` and `[archives] cold_days` in `config/docsync.toml` are now 90, and `documentation-tooling.md` states the default and why (history older than a quarter is archive, not context). `--check` never ages pages, so nothing else moves.

Tests: two new tests in `tests/test_docsync_declarations.py` (the colon label resolves; a non-existent name still reports one DOC010 issue) and `test_default_cold_days_is_ninety` in `tests/test_docsync_archives.py` (91 days ages, 89 does not). Two existing tests were edited for the new default: `test_cutoff_is_strict` (page date moved to exactly 90 days before as-of) and `test_cold_days_is_configurable` (page date moved to 45 days before as-of).

Validation: `pytest -q` -- **2187 passed**.

### 2026-09-29 - Retry-After is capped and the last try never sleeps

Side task, no batch tag: capping the Retry-After sleep and dropping the sleep after the final attempt, a fix from the third review of PR #245, on the review-fix branch stacked on the WP-0 branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Review finding S1-3 (P1): `retry_with_semaphore` slept whatever `Retry-After` a provider sent, up to `retries` times, while the job thread held one of the `MAX_ACTIVE_JOBS` slots. Spotify sends 12-18 hour values under extended rate limits, so three sleeps outlived the 2-hour job record and the slot stayed held. New `config.MAX_RETRY_AFTER_SECONDS` (env, default 30): a larger value logs one WARNING (label, value, cap) and returns `default` at once, no sleep and no more attempts; at or below the cap it sleeps as before. The helper also no longer sleeps after the final attempt, on the Retry-After path or the backoff path. The header parse (S1-4) and a user-facing rate-limited code are separate findings. README and SESSION_CONTEXT name the cap; `.env.example` lists the optional variable.

Tests: six new tests in `tests/test_retry_with_semaphore.py` cover the cap, the value at the cap, the cap read from `utils`, two backoff sleeps for three failures, and no sleep after a rate limit on the final attempt. No existing test was edited.

Validation: `pytest -q` -- **2184 passed**.

### 2026-09-29 - A malformed Last.fm page is retried and counted as dropped

Side task, no batch tag: retrying a malformed 200 page and counting it as dropped, a fix from the third review of PR #245, on the review-fix branch stacked on the WP-0 branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Review finding S1-2 (P1): `fetch_recent_tracks_page_async` returned any body that parsed as JSON as a success, so an error payload served as a 200 on page 2..N was fetched once, never retried and counted as received: the job said `ok` with up to 200 scrobbles missing, and a `[]` body reached the aggregators and crashed them. `fetch_once` now treats a page that fails `_is_well_formed_page` like a non-200 response: one WARNING naming the page and the defect class (never the body), `None`, retried, and dropped and counted in `pages_dropped` if it stays bad. Finding S1-12: page 1 is checked by the same helper in `fetch_all_recent_tracks_async`, replacing the inline check that raised `TypeError` on a scalar body and the weaker second try block. No check was added on `recenttracks.track`: Last.fm can serve one track as an object, a separate matter. README and `top-albums-sequence.md` say a malformed page counts as a failed attempt.

Tests: the two tests that pinned the old contract (`test_fetch_recent_tracks_page_retry_after_malformed_page_reaches_network`, `test_fetch_recent_tracks_page_does_not_cache_a_malformed_page`) now expect `None` and the retry count; new tests cover recovery inside one call, the partial outcome through `fetch_all_recent_tracks_async`, and scalar and list page-1 bodies.

Validation: `pytest -q` -- **2178 passed**.

### 2026-09-29 - Last.fm api_key redacted from every log line

Side task, no batch tag: redacting the Last.fm `api_key` in every log line (review finding S1-1), a fix from the third review of PR #245, on the review-fix branch stacked on the WP-0 branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

aiohttp puts the full request URL, query string included, into `str(exc)`, and four sites logged it: `utils.run_async_in_thread` (message and traceback), the registration-year warning in `routes/album_flow.results_loading`, `utils.retry_with_semaphore`'s connect-timeout error line, and `utils.get_cached_response`'s debug line (the cache key embeds the URL). A POST to `/results_loading` with an unknown username wrote the key twice at production log level. `api_logging.RedactingFormatter` now replaces the value after `api_key=` or `api_key:` with `[redacted]` in any rendered line, traceback included, and `app.py` sets it on both log handlers. The trace hook's query exclusion stays the first layer. The check_* functions, the cache key and the route's missing `exists` check are unchanged. Five new tests in `tests/services/test_api_logging.py` and one in `tests/test_app_factory.py`, which checks both the rotating file handler and the stdout handler.

Validation: `pytest -q` -- **2173 passed**.

### 2026-09-29 - Spotlight box comment and one finding sentence corrected

Side task, no batch tag: two text corrections from the review of the previous commit, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The comment inside `.spotlight-image-box` in `static/css/results.css` now puts each fact at its own width: 7rem below 768px, 9rem from 768px, and the corner 4px below 1024px and 8px from it. It had read as if the box grew at 1024px. F-B23-19 no longer says Spotify often serves 640x427, which had no source; it says the review's case was 640x427. No rule or test changed.

Validation: `pytest -q` -- **2167 passed**.

### 2026-09-29 - Stale dashboards corrected and the review's findings filed

Side task, no batch tag: a documentation truth wave and five new findings from the second code review of PR #245 (Section H, and the findings to file from every section), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

SESSION_CONTEXT's structure list and dependency graph now match the source: the Spotify icon slice of the frontend gate and its edges (from `frontend_gate.py` and `_frontend_gate_results.py`), the results slice's other imports, and the docsync modules `markdown`, `transaction`, `archives`, `closeout` and `findings` with every edge read from each module's own import lines. The control-plane diagram in `docs/architecture/documentation-tooling.md` gains the icon slice's class and the edges from the results slice to it and from the results, theme and layout slices to the colour slice.

Smaller corrections: the README's provider-log sentence names Last.fm's `method` value as the one query parameter a line carries; the `heatmap_task` docstring says a failure is classified before it falls back to `internal_error`; the results spotlight comment says its 8px corner starts at 1024px; DEVELOPMENT.md no longer says "This session". FINDINGS.md: F-B23-9 (open, P1) moved under the P1 heading, and the line-number citations in F-B21-57, F-SWE-3, F-SWE-7 and F-DOCSYNC-14 are now names.

Filed: F-B23-16 (the error classifier's bare substrings), F-B23-17 (a Validation line with no digit passes `--check`), F-B23-18 (unmatched portraits with no link to Spotify, P1), F-B23-19 (letterboxed spotlight photo corners) and F-B23-20 (the spotlight waits for every candidate).

Validation: `pytest -q` -- **2167 passed**.

### 2026-09-29 - Frontend gate checks that could not fail now fail on their defects

Side task, no batch tag: ten frontend-gate checks and tests made to fail on the defects they name (second code review, findings D1 to D10; D1 is the earlier E6), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The inline-mark check (D1) now renders each mark inside two wrappers with different `color` and `--bars-color` and judges the painted fill and stroke, so a comment, a child path, a 3-digit hex or a later stroke rule can no longer hide a colour that ignores its wrapper. The non-square photo check (D2) judges the painted image box against the box that clips it, and fails a transform or clip-path on the image. The overlay check (D3) also reads `::before` and `::after`, and the animation check fails on any named animation or a running transform or filter transition.

The card-hidden check (D4) waits until the mock has seen and answered every candidate before it asserts the card stayed hidden. Both photo checks (D5) and the Spotify icon check (D6) wait for the image to load first, and an icon that never loads is reported by name. The focus-ring shots (D7) park the pointer and let transitions settle. The unmatched placeholder kind (D8) counts only visible nodes, and a missing visible placeholder is a failure. Comments (D9) now say the Deezer row is third by plays and say what the rotation check proves. The rotation test (D10) asserts hydration writes no `image_url` or `spotify_url` into `APP_DATA`.

Also corrected: a test docstring that still said the artwork radius is wrong only below 768px; it now names `ARTWORK_RADIUS_STEP_MIN` (1024px). D7 has no plant that separates old from new (a hover that differs between two shots cannot be reproduced), so it has a green run only. A zero-duration transition is not counted as an animation.

Validation: `pytest -q` -- **2167 passed**.

### 2026-09-29 - Artwork corners, provider names and spotlight name fixed

Side task, no batch tag: review fix wave for the results and unmatched pages (review findings F1, F2, F3 and F7), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

F7: the album artwork corner radius now steps to 8px at 1024px, not 768px. Spotify's rule gives small and medium devices 4px and large devices 8px, and a tablet is medium. This corrects the controller's own Task 7 call (8px from 768px) to Spotify's device classes. The frontend gate now measures the results page at 768, 1023 and 1024px, and it is red with the old step planted back. RECONCILIATION section 18 and DESIGN.md carry the new width and a dated correction note.

F2: a non-Spotify row with no album URL used to show no provider name, so its artwork read as Spotify's. Both pages now name the provider on every non-Spotify row: a link when the row has a URL, the same badge as plain text when it has none. F3: the unmatched banner's exception clause ("except rows that name another provider") is now conditional, so both pages word the same situation the same way.

F1: at 320px a long one-word artist name in the spotlight card was cut mid-word with no ellipsis. The name may now break inside a long word and keeps two lines with an ellipsis. At 1280px the rail is 125px wide, so a long name wraps inside the word there too; short names are unchanged. No gate check was added for it, because the spotlight photo fixtures and the check registry belong to Task 14. A new test module, `tests/scripts/dev/test_frontend_gate_results.py`, covers the changed radius check.

Validation: `pytest -q` -- **2142 passed**.

### 2026-09-29 - Show the whole focus ring on the unmatched album links

Side task, no batch tag: the album title link and the provider badge on the unmatched report now show their whole keyboard focus ring, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The fault came from the controller's keyboard check of the rebuilt page (owner ruling 8). The text column carried `overflow-hidden`, which cut the title's ring to its bottom edge and the badge's to two sides. The class is gone; the table cell's own overflow and padding contain the column, and the title still wraps while the artist line still ends in an ellipsis.

The frontend gate's unmatched check now reaches both links by real Tab presses and judges each ring on painted pixels: a focused screenshot against a blurred one, each side outside the box. A cut ring computes the same outline as a whole one, so no computed style is read. Its fixture gains one Deezer row, still twelve rows, so a badge renders. Live probes: red with the class planted back and red with the clip moved into CSS, green on the fix.

Validation: `pytest -q` -- **2130 passed**.

### 2026-09-29 - docsync refuses a path that leaves the repository by a junction

Side task, no batch tag: docsync's path boundary and its declared-path spelling, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The Task 10 review raised two Minors, and the controller's probe widened the first. On Windows a directory junction is not a symlink to `Path.is_symlink()`, so `resolve_within` walked straight through one, and its containment test ran only when the leaf existed. A new file reached through a junction was accepted and resolved outside the root; the same path with an existing leaf was refused. A publish creating that file would have written outside the repository.

`resolve_within` now refuses a junction wherever it refuses a symlink, and tests containment on the deepest existing ancestor, so a leaf that does not exist yet is no longer a way round. Either change alone closes the probe; a mount point is the same class. `_validate_documents` turns the `ValueError` from `relative_to` into the `DeclarationError` it already raises for a path outside the repository, so the CLI prints a typed diagnostic, not a traceback. `[untracked_essentials]` now refuses a path not written in normalised form, naming the spelling to write, as `[documents]` does, so `./x.json` and `x.json` are no longer reported as two files.

The tests build real junctions with `mklink /J` and remove them with `os.rmdir`. Each change was proved by mutation.
Validation: `pytest -q` -- **2126 passed**.

### 2026-09-29 - Heatmap focus ring paints whole; grid keys leave shortcuts alone

Side task, no batch tag: second code-review findings E1, E2, E3, E4, E5, E7 and E10 on the heatmap grid, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

E1, E4: the cell outline was covered by later cells and clipped by the SVG, yet every computed-style check passed. One ring rect is now painted after every cell and moved to the keyboard-focused one. The SVG may paint past its box into 4px of room #heatmap-grid keeps round it, so the grid does not move: the viewBox, cell size and frame match the old layout at 390px and 1280px. The gate now reads the ring off screenshot pixels (first, interior and last cell, both profiles) instead of computed outline values, and asserts the grid still spans its frame.

E2, E3: a scroll no longer re-shows the hidden tooltip of a clicked cell, and a held Alt, Ctrl, Meta or Shift leaves the arrow, Home and End keys to the browser. E10: the A3 probe now records that its scroll happened.

E5: a breakpoint re-render gives focus back to the same day, and the new gate check `heatmap focus survives breakpoint` covers it. E7: the vacuous HEATMAP_PATH test is gone.

Owner ruling 11 (2026-09-29, "Consider ammending the CI and frontend_gate.toml, test, and files."): both heatmap keyboard-focus checks join `required` in `config/frontend_gate_checks.toml`, so neither can be disabled; the manifest test pins the new set. The gate goes from 38 to 39 checks and 63 to 64 runs.

Live probes: base code, ring painted first, no room in the grid's clip, a clipping SVG, the grid-moving viewBox padding, and each single fix reverted all went red; the fix stayed green.
Validation: `pytest -q` -- **2118 passed**.

### 2026-09-29 - Repo Assist pins the count it measures and skips browser tests

Side task, no batch tag: Repo Assist's rules and file grant, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
Review findings G1-G3: Repo Assist's rules predated the pinned test count and the browser marker, so a PR from it could not pass. Rule 4 now runs `--fix --test-count N` and never edits a count by hand. Owner ruling 11 (2026-09-29, "Consider ammending the CI and frontend_gate.toml, test, and files.") allowed the widened grant: both `allowed-files` lists gain `config/docsync.toml`, and the lock was regenerated with `gh aw compile repo-assist`, not edited.
Rule 5 runs `-m "not browser"` and counts the 43 browser tests by `--collect-only`, so N is still the whole suite. Task 4 audits both requirements files. `test.yml` runs `-m browser` without the directory, so the marker decides what runs; the same 43 tests run either way.
The new `tests/test_ci_workflows.py` checks that the compiled lock grants every file the procedure writes and that the source and the lock agree.
Validation: `pytest -q` -- **2117 passed**.

### 2026-09-29 - docsync refuses declared paths and pin rewrites it cannot trust

Side task, no batch tag: the second-review fix wave for the docsync declarations, the test-count pin writer and the worktree guard (review findings B1-B6, B8, B9 and C1-C5), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
B1, B9: a `[documents]` path must be written in the normalised repository-relative form every reader keys documents by. `./x` or `a//b` is refused with the spelling to write, and an empty value says it is empty.
B2-B4: `--fix --test-count N` parses its rewrite and publishes only the original declarations with `test_count.pinned` changed. Any other result exits 2 and writes nothing.
B5, C3, C1, C5: `[untracked_essentials]` refuses a backslash, any character `str.isprintable()` rejects, an empty path and `.`. A repeated path is reported once, and a directory at the declarations path is an error, not "nothing declared".
C2, C4: WT015's read-failure warning carries the failure class only, never the absolute path or OS text, and points to `doc_state_sync.py --check`. WT004 labels an unsafe base ref once.
B6, B8: the preflight's pin-only exemption decodes `git show` as UTF-8 and fails closed on a blob that is not. DOC025 and the close-out admission refusal name the `--config` file actually read.
`docs/architecture/documentation-tooling.md` is updated to match.
Validation: `pytest -q` -- **2111 passed**.

### 2026-09-29 - Cache only well-formed Last.fm pages; cancel orphaned fetches

Side task, no batch tag: the second code-review findings A1 and A2 (Last.fm page cache and orphaned fetches), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
A1: `fetch_recent_tracks_page_async` cached any 200 that parsed as JSON, so a first page
with no `@attr`, or an error payload served as a 200, was replayed to every retry for
REQUEST_CACHE_TIMEOUT. A new `_is_well_formed_page` predicate (a `recenttracks` mapping with
an integer `@attr.totalPages`) now gates `set_cached_response`. The body is still returned
unchanged.
A2: when one page raised (the mid-job 404 `ValueError`), sibling page fetches stayed
pending on a closing session. `_cancel_and_drain` now cancels and awaits them before the
unwrapped exception leaves, in the `as_completed` path and in `fetch_pages_batch_async`.
Nine tests were added to `tests/services/test_lastfm_service.py`, each proved by mutation.
Validation: `pytest -q` -- **2083 passed**.

### 2026-09-29 - Rebuild the unmatched report rows and show portraits whole

Side task, no batch tag: the owner-delegated audit of the unmatched report and F-B23-12, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
The table loses its fourth "Reason detail" column. A row's note sits under the artist instead:
the shortfall on a threshold row ("3 plays and 1 track short", new `describe_shortfall`), the
reason on a release row, and nothing on a no-match row. At 390px the album title has 144-160px
(it had 51-67px). Headline, panel titles and buttons are sentence case. The subtitle gives the
year and the count, and the attribution is a plain line with 12px text on both pages
(RECONCILIATION section 18). F-B23-12: every cover, portrait and placeholder uses
`.provider-artwork`, so artwork is never cropped and corners are 4px, or 8px from 768px.
F-B23-14: the portrait had never loaded, because it was hidden and `loading="lazy"`. The
attribute is gone. The gate's wide and tall portraits now have URLs of their own and must load
whole, inside their slot. F-B23-15 is open for the owner. Edited tests:
test_group_unmatched_albums_groups_by_reason_code,
test_unmatched_view_success_renders_grouped_reasons.
Validation: `pytest -q` -- **2073 passed**.

### 2026-09-28 - Drop the spotlight's unreachable guards

Side task, no batch tag: removed the spotlight's dead code (`hidePortrait`, three name guards in `hydrateCandidate`, its unused `view` parameter), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
Code-review finding 8. Rotation only renders candidates that already have a confirmed
`image_url`, and `hydrateCandidate` writes only its own index before the array is replaced, so
none of that code could fire. The `hydrateCandidate` docstring now says so. No behaviour change.
Validation: `pytest -q` -- **2055 passed**.

### 2026-09-28 - Report an unreadable declarations file as a warning

Side task, no batch tag: the 2026-09-28 /code-review's finding 5 in the control plane, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
`load_declarations` now converts an unreadable or non-UTF-8 declarations file into a
`DeclarationError` naming the path and the cause, so the worktree guard's WT015 check stays
WARNING-only instead of escaping to the fail-closed WT014 ERROR. WT015's message now says the
declarations file could not be read, keeping the underlying error text, instead of blaming
`[untracked_essentials]` specifically. Finding 6 (a FINDINGS header rewrite conjuring an empty
file) was refuted on reachability: `_read_live_documents` already requires FINDINGS.md before
that code runs, so no fix was made for it.
Validation: `pytest -q` -- **2055 passed**.

### 2026-09-28 - Official Spotify icon on the spotlight, results and unmatched pages

Side task, no batch tag: F-B21-60 part 2, the official Spotify icon and provider attribution, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
The spotlight's Spotify link now shows Spotify's own icon, from
https://developer.spotify.com/images/guidelines/design/2024-spotify-logo-icon.zip,
committed byte-for-byte: Primary_Logo_Black_RGB.svg (SHA-256
5595afea0e6f009b1dd8529511204d0fd5ca035e49c85409d1697063b3c27a05) on the light
theme and Primary_Logo_White_RGB.svg (SHA-256
8929d148f54cede78f0f36ce90df815e5ea5e5559e7faeccad3669302ef2daa1) on the dark
theme. Neither theme's surface is pure white or black, so the green icon is not
allowed. The icon is 24px with 12px of clear space; the link target is 48px.
Results and unmatched lists attribute Spotify once, with the icon; only
non-Spotify rows keep a text badge. No Deezer logo could be taken from Deezer's
own domains, so F-B22-4 stays open for Deezer only. The "Save image" JPEG
dropped the SVG icon (html2canvas 1.4), so the export now swaps in a raster of
the same file. New frontend-gate check "spotlight spotify icon size and link
target", and a JPEG-icon step in "results provider attribution". Edited test:
test_results_complete_links_each_row_to_its_own_provider.
Validation: `pytest -q` -- **2050 passed**.
