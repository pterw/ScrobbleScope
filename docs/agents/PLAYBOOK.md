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
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
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
  (see Section 4). Next action: the WP-0 close-out below. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam, typed provider failures and job persistence
  (before WP-3), an album request module (before WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (before WP-2), one album-metadata
  encoding (before WP-3), a statistics module (before WP-6), and provider
  failure logs that carry no listener data. WP-1 does not start until they
  are scheduled.

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
