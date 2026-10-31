<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0007

### F-B23-62: a MusicBrainz 429 is cached as a final "no match" -- RESOLVED

`lookup_original_release.search_once` (`scrobblescope/musicbrainz.py`) retries a 503 (fixed 1s sleep) and other 5xx, but a 429 reaches the `status != 200` branch and returns `(None, None, True)`, which `release_checks` caches as a terminal "no match". Any album that meets a rate-limit response during a release check is recorded as having no original release until the cache row expires.

Fix direction: treat 429 and 503 alike, wait the `Retry-After` header (bounded) or a short default and retry; when retries run out, report the service unavailable and cache nothing.

- [x] **Status:** resolved
**Completed:** 2026-10-25
Resolved by treating a 429 like a 503: wait the bounded `Retry-After` or a
short default and retry, and when retries run out report the service
unavailable and cache nothing. Fixed by `5d9e561a`.
Source: owner's real runs, 2026-10-25

### F-B23-63: MusicBrainz request starts are exactly 1.000s apart -- RESOLVED

`_MUSICBRAINZ_THROTTLE` (`scrobblescope/utils.py`) is built from `MUSICBRAINZ_REQUESTS_PER_SECOND`, read in `scrobblescope/config.py` as `int(... "1")`, so `_min_interval` is `1.0 / 1` and requests start exactly 1.000s apart, the edge of MusicBrainz's published limit; clock jitter or a second process tips it into a 429 (F-B23-62). Release checks run in the background, so extra spacing costs the user nothing.

Fix direction: space request starts 1.1s apart, with the setting no longer an integer.

- [x] **Status:** resolved
**Completed:** 2026-10-25
Resolved by spacing request starts 1.1 seconds apart
(`MUSICBRAINZ_MIN_INTERVAL_SECONDS`, no longer an integer request rate).
Fixed by `2b7e95ad`.
Source: owner's real runs, 2026-10-25

### F-B23-26: the artist spotlight can show another artist's photo and link under the Last.fm name -- RESOLVED

`scrobblescope/spotify.py` `_request_spotlight_artist` asks Spotify for `limit: 1` and returns `items[0]` with no name check, and neither `static/js/results-spotlight.js` `hydrateCandidate` nor `static/js/unmatched.js` `fetchArtistImage` compares `data.name` with the requested artist. A Last.fm artist Spotify does not know (a local band, a misspelling) gets the closest other artist: the card shows that photo with the alt text "Photograph of <Last.fm name>" and a link to the other artist's page. With the album-cover fallback gone, this is the only photo source, and the card treats the result as a confirmed photo. Reproduced with the API mocked to return a different name; how often it happens against the live API is unmeasured. Fix: the route returns the hit only when `normalize_name` of its name equals that of the requested artist, else null `image_url` and `spotify_url`.

- [x] **Status:** resolved
**Completed:** 2026-10-25
Resolved by `_request_spotlight_artist` accepting a name-search hit only when
`normalize_name` of its name equals that of the requested artist, so a
different artist's photo and link no longer reach the card, which stays hidden
for that artist. Fixed by `7aeafa90`.
Source: third review of PR #245 (2026-09-29), S2-12.

### F-B23-57: CI downloads Playwright's Ubuntu packages from a slow mirror on every run -- RESOLVED

Evidence (2026-10-22): in PR #265's CI run, step "Install Playwright browser" fetched 53.7 MB of Ubuntu packages at 43.5 kB/s from the runner's Azure mirror and took 20 min 32 s. The apt index (12.5 MB in 16 s) and the four browser downloads (14 s together) were fast, so the package download was the whole stall. PR #266's first attempt stalled in the same step and was cancelled and re-run.

Fix: the packages `playwright install --with-deps` downloads are kept in the Actions cache, keyed by runner image and `requirements-dev.txt`, with a restore key that reuses the previous image's packages. They are restored before the install, copied into apt's archive directory, copied back after the install and saved by a step right after it, so a failed later step cannot prevent the save. The apt index and the browser downloads are unchanged; `apt-get autoclean` bounds the cache.

Not covered: a cache miss on a slow mirror still waits, once per runner image or dependency change, and a run cancelled inside the install saves nothing, so the next run waits again. On an exact key hit nothing is re-saved, so a package newer than the cached copy downloads on every run until the runner image or `requirements-dev.txt` changes the key. A cache saved by a pull-request run is scoped to that PR's branch; other branches see it only after a push-to-main run saves one.

- [x] **Status:** resolved
**Completed:** 2026-10-22
Source: PR #265 and #266 CI runs and controller log analysis, 2026-10-22.

### F-B23-50: `/heatmap_data` answered an album job with a 500, and `/api/unmatched` answered a heatmap job as valid -- RESOLVED

`heatmap_data` (`scrobblescope/routes/heatmap_flow.py`) spreads `ctx["results"]` into its answer (`{"ready": True, **ctx["results"]}`), and an album job's results are a list of rows, so an album job id raised `TypeError` and answered 500 once the job finished; a running album job answered 202 and a failed one answered 200 with the error body. `unmatched_data` (`scrobblescope/routes/api.py`) read `jobs.unmatched(job_id)` and answered a heatmap job with 200 and an empty report. Fixed: both endpoints now refuse a job whose mode is not their own with the same 404 a missing job gets (the album pages and the release-check endpoint already followed that rule), and `unmatched_data` reads `jobs.context` once so the mode and the report come from one record. `/progress` stays shared by both modes on purpose, because `static/js/heatmap.js` polls it. The same mode check now appears inline at five code sites (the album pages' shared `_get_validated_job_context`, `_latest_heatmap_job`, `api.release_checks`, and these two), and F-B23-53's job read seam owns folding them into one.

- [x] **Status:** resolved
- **Completed:** 2026-10-22
- Source: the 2026-10-21 architecture review (defects D1 and D3), re-checked 2026-10-21.

### F-B23-48: `test_unmatched_view_coverless_rows_wear_their_albums_wash` compared whole pages that carry a timestamped CSRF token -- RESOLVED

The test asserted that two `POST /unmatched_view` pages were byte-identical, but `templates/base.html` renders `<meta name="csrf-token" content="{{ csrf_token() }}">` and Flask-WTF signs that token with a timestamp, so two renders that straddle a second boundary differ there with no defect in the code. It failed this way in PR #262 CI on 2026-10-21 and passed on re-run; it was the only whole-page equality assertion in `tests/`. Fixed: the test now takes each page's own token from its csrf-token meta tag, replaces every occurrence of it in that page with a fixed placeholder, and asserts the two masked pages are equal, so only the clock-dependent part is excluded and row order or any other render nondeterminism still fails.

- [x] **Status:** resolved
- **Completed:** 2026-10-22
- Source: PR #262 CI run and controller diagnosis, 2026-10-21.

### F-B23-3: the album pipeline runs the cache connection protocol itself -- RESOLVED

`orchestrator.process_albums` opens the cache connection, holds it across
provider work, and closes it in a `finally`. Meanwhile
`orchestrator/_cache.py` owns the cache-failure policy, including writing job
warnings through the facade. So understanding what "the cache is optional"
means takes both modules. It also makes the connection-closure test in
`tests/services/test_orchestrator_process_albums.py` configure the provider
machinery.

The fix is for the existing cache module to own the operation's lifetime and
its failure classification, while job messages and enrichment decisions stay
with the caller. There is one concrete adapter, so no generic cache-backend
layer. Metadata and release-check cache policy stay separate.

- [x] **Status:** resolved
**Completed:** 2026-10-21
By refactor(cache): Let the cache own its
connection and failures -- `cache.AlbumCache` and `open_album_cache` own the
connection lifetime and what a database error means (including a failing
`close()`, which no longer fails a job); `process_albums` manages no
connection and `orchestrator/_cache.py` only reports to the job; the
correction worker keeps its own policy, as the finding asked. No performance
gain is claimed.
Source: card 03 of
`docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-2: Last.fm's payload shape travels into both calculations -- RESOLVED

`lastfm.py` returns raw JSON pages. `orchestrator.fetch_top_albums_async`
then reads `recenttracks`, `track`, `album.#text`, `artist.#text` and
`date.uts` itself, and `heatmap._aggregate_daily_counts` reads `recenttracks`
and `date.uts`. A change to Last.fm's payload therefore reaches two
calculations, and WP-6's first-listen and busiest-hour statistics would add
more of the same reads. Global Rule 4 puts that translation inside the
provider module.

The fix is to have `lastfm.py` translate the payload into native listening
facts, keeping completeness explicit. Two differences must survive:
- the heatmap counts dated rows even without album metadata, while album
  aggregation needs artist, album and track;
- the Spotify-export rules (30 seconds, private sessions) must not be imposed
  on Last.fm.

It cannot land inside Batch 23 as-is: `tests/test_heatmap.py` feeds
`_aggregate_daily_counts` raw pages, and Batch 23 keeps the Last.fm path's
tests unmodified. It is separate from F-B22-7, which translates Spotify's
metadata payload.

- [x] **Status:** resolved
**Completed:** 2026-10-20
By refactor(lastfm): Hand callers scrobbles, not pages -- lastfm.fetch_scrobbles returns plays.Play records and both calculations read them; the two differences listed above are pinned in tests/test_lastfm_job_results.py and tests/test_plays.py, and the Spotify-export rules stay out of plays.py.
Source: card 02 of `docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-40: the Last.fm username appears in log lines, beside the listener's scrobble total -- RESOLVED

`lastfm.py` ("Profile of %s is private", "User %s not found"), `orchestrator/__init__.py` (`_fetch_and_process` and `_report_album_failure`), `heatmap.py` ("Heatmap ready for %s: %s scrobbles" and `_report_heatmap_failure`), `routes/heatmap_flow.py` and `routes/album_flow.py` write the Last.fm username into ERROR, WARNING and INFO lines, and the heatmap line pairs it with the listener's scrobble total. `log_failure`'s docstring and BATCH23's Data handling section say listener-linked facts stay out of logs. Ask the owner whether a public Last.fm handle counts; if it does, log the job id instead. The scrobble-total line is the clearer one to drop first, before the export path shares this code.

- [x] **Status:** resolved
**Completed:** 2026-10-20
The commit that logs a job id in place of a Last.fm username: the scrobble-total line is gone, and the request-cache hit line no longer writes the cache key (which embeds the name). The route pre-check lines left with PR #3's shared pre-check.
Source: review 4 of PR #245 (backend), R4-backend-9.

### F-SWE-3: a Spotify server error bypasses the configured retries -- RESOLVED

`search_for_spotify_album_id` (`spotify.py`, its inner `search_once`) returns
`(None, None, True)` for every non-200, non-429
response, and `is_done=lambda t: t[2]` treats that `True` as terminal. When
filed, a 500 or 503 therefore ended the attempt loop after one try, while
`SPOTIFY_SEARCH_RETRIES` is set to 3 -- verified by running it then. The
retries only ever fired for 429; a 5xx is retried now (see the resolution
below). `fetch_spotify_album_details_batch` has the same
shape in the `fetch_once` inside it.

The consequence is narrow: an album that _is_ on Spotify can be recorded as
unmatched when a second attempt would have found it.

**Rescoped by the owner, 2026-08-20, and the correction is worth keeping.**
The audit first filed this as a user-facing mislabelling -- `search_once`'s final branch
returns the same value for a genuine empty result, so
`_run_spotify_search_phase` (`orchestrator.py` at the time, now
`scrobblescope/orchestrator/_search.py`) records the album with the reason
`No Spotify match`, and the report treated that label as wrong. It is not.
Thousands of Last.fm-scrobbled albums genuinely have no Spotify release, so
the label is accurate for the ordinary case and what the user sees is
correct. What survives is the defect above -- configured retries that never
run -- which is a smaller thing than the audit claimed. Severity drops from
P1 to P2 and the finding moved from the P1 section to this one.

The related UI need -- the unmatched modal and page should say plainly that
an album had no Spotify match -- is already Batch 21 WP-7 scope
(the `WP-7 -- Unmatched page + reason_code` section of
`docs/history/definitions/BATCH21_DEFINITION.md`: the `no_spotify_match` reason code and the reason
panels with human copy). It is not extra work and is not tracked here.
- [x] **Status:** resolved
**Completed:** 2026-09-30
A Spotify 5xx is retried, not ended after one try: `search_for_spotify_album_id`, `fetch_spotify_album_details_single` and `fetch_spotify_album_details_batch` return an unanswered result for a 5xx, `retry_with_semaphore` retries it up to the configured count, and the call raises `ProviderError` (`spotify_unavailable`) once the retries are spent, so the album is listed unavailable rather than lost as a miss. The prose above describes the code as it was when filed.
Source: SWE_PRINCIPLES_AUDIT, rescoped by owner review.

### F-B23-29: small cleanups the third review of PR #245 found, none changing behaviour a user sees -- RESOLVED

One bundle, to be taken opportunistically. The frontend items (S2-18, S2-20, S2-21, S2-22, most of S2-23, the Codacy const arrows and the Task 9-11 review minors) landed with F-B23-27 and F-B23-28; what is left:

- `tests/test_routes.py` has duplicate helpers and row factories (Rule of Three: the helpers may wait) (S1-15).
- S2-23 leftovers: the `#heatmap-grid` ring-room CSS and padding subtraction in `renderHeatmapMobile`, with its false "sized to what is left inside it" comment (they belong to F-B23-25's layout fix); the server-rendered spotlight card body and the `top_artist_*` route variables in `routes/album_flow.py`, dead because JS overwrites them; the badge markup copied four times (Rule of Three: the CSS is one rule now, the markup is still two copies per page); a `sr-only` re-implementation; the theme not following the system setting live. The five photo preloads are recorded on F-B23-20.
- `scripts/dev/_frontend_gate_layout.py` comments cite "Step 5", a label no tracked file defines.

- [x] **Status:** resolved
**Completed:** 2026-09-30
Closed in part: the frontend items, the S2-23 comment and the provider-badge CSS landed with 5aeac2a7 (fix(ui)), and the failure-rule items with 7ce59bf0. The items no commit did, including the hand-written visually-hidden (sr-only) pattern, are filed as F-B23-38.

### F-B23-27: a long artist credit paints over the plays and date columns on the Results page from 768px -- RESOLVED

`templates/results.html` `.album-info` is a flex item without `min-width: 0`, so its `truncate` artist span never shrinks: at 1024px an artist credit of about 65 characters runs from x 192 to 674 while its cell ends at 324, painting over the plays and release-date columns with no ellipsis. The same happens at 768, 1280 and 1920px, and on `main`. `static/css/results.css` fixes only widths below 768px, and `unmatched.css` already carries the `min-width: 0` rule for the unmatched table. Fix: `.results-table .album-info { min-width: 0 }` in `results.css` (Tailwind's `min-w-0` is dead under this theme, F-B21-52).

- [x] **Status:** resolved
  **Completed:** 2026-09-30
  `.results-table .album-info { min-width: 0 }` in `results.css`; the gate's artist-credit check failed before it (207-286px past the cell at 768, 1024, 1280 and 1920px) and passes after.
  Source: third review of PR #245 (2026-09-29), S2-13.

### F-B23-28: the unmatched threshold column clips "1234 plays" below 768px -- RESOLVED

`static/css/unmatched.css` sets the below-threshold column to 4.75rem in the `max-width: 767.98px` block, with `.unmatched-threshold { white-space: nowrap }` and `overflow: hidden` on `td`. From 320 to 767px "1234 plays" is cut by 8px ("1234 play") and "150 plays" loses about 1px of the "s"; from 768px the column is 104px and nothing clips. The CSS comment says the width "holds either", which is false. Reproduced in Chromium and Firefox; `main` clips the same. Fix: let `.unmatched-threshold` wrap (`white-space: normal; overflow-wrap: anywhere`) or widen the phone column to about 5.5rem, and add a four-digit case to the gate's seed.

- [x] **Status:** resolved
  **Completed:** 2026-09-30
  Below 768px the threshold figures wrap (`white-space: normal; overflow-wrap: anywhere`, scoped to the panel so it beats the later nowrap rule), the "holds either" comment is rewritten, and the gate's seed row carries 1234 plays; the check failed on "1234 plays / 2 tracks" before the fix. A widened 5.5rem column was tried and dropped: the album title fell under the gate's width floors.
  Source: third review of PR #245 (2026-09-29), S2-14.

### F-B23-31: tests that stay green when the defect they exist for is planted back -- RESOLVED

Five tests were shown to survive the mutation they are meant to catch, each with the reviewer's proposed fix:

- Spotlight seed fallback (S1-7): restoring the deleted album-cover fallback in `spotlight.select_spotlight_artists` keeps the suite and the gate green. Add a route test that every spotlight seed `image_url` is empty.
- Span start (S1-8): the mutants `span_s = entry["span_end"]` and dropping the span-start update both survive `tests/services/test_api_logging.py`. Use a non-zero clock start, and record the later-starting call first.
- Cancel loop (S1-9): removing the cancel loop in `lastfm.fetch_all_recent_tracks_async` passes after 60s in `tests/services/test_lastfm_service.py` (`_PageFetchLedger`), and no per-test timeout exists. Count `CancelledError`, assert four, and wrap in `asyncio.timeout(2)`; the reviewer ran this: 2 passed in 0.13s at HEAD, 2 failed on the mutant.
- Fixture URL (S1-10): in `tests/test_provider_fixtures.py` the fixture's `external_urls.spotify` equals the code's fallback URL, so a typo in the key name passes. Give the fixture a distinct URL, and adopt `SPOTIFY_ALBUM_DETAILS_MOCK` for the two inline copies in `tests/test_orchestrator_process_albums.py` that escape the drift test.
- Frontend harness (S2-24): `tests/frontend/test_heatmap_pure_functions.py` asserts only `exportHeaderLayout(...).columns`, `exportHeaderModel().eyebrow` and `rocketColor` at exact stops; ten mutations survive (`Math.round` to `Math.floor`, `beside` forced false, the legend offset dropped, the headline dropped, and others). Assert whole layout objects for one beside and one stacked case, a `rocketColor` value between two stops, and the headline and legend.

- [x] **Status:** resolved
  **Completed:** 2026-09-30
  Each of the five tests now fails on the mutant it exists for (recorded per item in the Section 4 entry of 2026-09-30, Tests that fail on the defect they guard), and two review gaps closed with them: the private-profile 403 route branch and the spotlight `keepLink` re-measure guard in the frontend gate.
  Source: third review of PR #245 (2026-09-29), S1-7, S1-8, S1-9, S1-10 and S2-24.

### F-B23-22: the album pipeline answers an unclassified exception with `unknown`, retryable, and the heatmap with `internal_error`, though the docstrings claim parity -- RESOLVED

`scrobblescope/orchestrator/__init__.py` `_fetch_and_process` ends its except branch with `error_code="unknown"` (not a member of `ERROR_CODES`), retryable, carrying the raw exception text; `heatmap.py` `heatmap_task` publishes `internal_error`. The docstrings of `errors.classify_exception_to_error_code`, `heatmap.heatmap_task` and `_report_album_failure`, and the archived closure of F-SWE-5, all say the two pipelines answer alike. The album behaviour predates PR #245; the docstrings were written by it. Owner decision: make the album fallback `internal_error` (which flips `retryable` to false and stops showing raw text to the user), or keep the split and reword the docstrings to say so. Either way a test is missing: the mutant `error_code = None` in that branch survives the full suite, so a test must assert the published code and the retryable flag for an unclassified exception in the album pipeline.

- [x] **Status:** resolved
  **Completed:** 2026-09-30
  Both pipelines classify by type and publish `internal_error` (not retryable, no exception text) for an exception nothing classifies; `unknown` and `jobs.fail_unclassified` are deleted, and the `error_code = None` mutant now fails a test.
  Source: third review of PR #245 (2026-09-29), S1-5.

### F-B23-21: `reraise=(ValueError,)` in the Last.fm page fetch ends the job on any ValueError, skipping every retry -- RESOLVED

`scrobblescope/services/lastfm.py` `fetch_recent_tracks_page_async` passes `reraise=(ValueError,)` to `retry_with_semaphore` so that the 404 "user not found" it raises as a `ValueError` is not retried. That tuple matches every `ValueError` subclass, so a non-integer or HTTP-date `Retry-After` (the header parse raises `ValueError`) and a non-UTF-8 error body (`UnicodeDecodeError`) also skip all three attempts and end the whole job: `internal_error` in the heatmap, the raw exception text in the album pipeline. The mechanism was reproduced in the review; no live trigger has been seen. The fix is the typed not-found exception that F-B23-16 already proposes, with `reraise` narrowed to it, plus a defensive `Retry-After` parse and `text(errors="replace")` on the error body. This is the same typed exception as F-B23-16, so land them together.

- [x] **Status:** resolved
  **Completed:** 2026-09-30
  The Last.fm 404 is the typed `UserNotFoundError` and `reraise` is narrowed to it and `PrivateProfileError`; `Retry-After` is parsed defensively (a bad value is retried) and both error-body reads use `text(errors="replace")`.
  Source: third review of PR #245 (2026-09-29), S1-4.

### F-B23-16: the error classifier matches bare substrings -- RESOLVED

`scrobblescope/errors.py` `classify_exception_to_error_code` answers `user_not_found` for any
exception message that contains both "not found" and "user", in any case, and
`spotify_rate_limited` or `lastfm_rate_limited` for any message holding "Too Many
Requests". Both pipelines call it on every unhandled exception before falling back to
`internal_error`: the album pipeline (`orchestrator/__init__.py`, `_fetch_and_process`)
and, since this branch, the heatmap pipeline (`heatmap.py`, `_report_heatmap_failure`). No
current raise site produces a colliding message, so nothing is misreported today; an
unrelated exception whose text happens to hold both words would be blamed on the user. The
fix is a typed exception for the Last.fm 404 (and the rate limits), classified by type, which
is larger than a fix-wave change. The same typed exception is the fix for F-B23-21
(`reraise=(ValueError,)` in the Last.fm page fetch), so the two land together.

- [x] **Status:** resolved
  **Completed:** 2026-09-30
  Errors are classified by exception type (`UserNotFoundError`, `PrivateProfileError`, `ProviderError`, `SpotifyUnavailableError`); the message-substring branches are deleted and a test holds an unrelated exception whose text reads "user not found" to `internal_error`.
  Source: second /code-review of PR #245, Section A, finding A3, 2026-09-29.

### F-DOCSYNC-19: `--check` has no diagnostic for an interrupted publication -- RESOLVED

Transactional publication recovers a crash mid-publish by replaying its
journal against the on-disk state on the next writer, but a read-only
`--check` run gives no signal that a journal is present and an earlier
publish was interrupted -- recovery exists, a diagnostic does not.
- [x] **Status:** resolved
  **Completed:** 2026-09-29
  `--check` reports DOC026 while `.docsync.journal` exists and `--fix` replays it first (S3-2, third review of PR #245).
  Source: `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md` DoD row 29, GPT Sol Max review.

### F-B23-23: the Last.fm privacy check caches verdicts it should not, and a private profile met inside a job is reported as an outage -- RESOLVED

`lastfm.check_profile_is_public` caches the private verdict for `REQUEST_CACHE_TIMEOUT` (3600s), so a user told to make the profile public and try again is refused from the cache for an hour. The mirror case: a cached public verdict lets a profile that has since gone private start a job, and the job fails as `lastfm_unavailable`, retryable, for the rest of the hour. `check_user_exists` caches any 200 body, so error 6 ("user not found") is cached as `exists=True`. Inside a job, `fetch_once`'s non-200 branch retries a 403 (Last.fm error 17) three times and reports "Last.fm unavailable, try again", and `ERROR_CODES` has no `private_profile` code. Invalid-key errors 10 and 26 may behave the same (unverified). The 403-in-job part is plausible rather than reproduced; the caching parts were reproduced. Fix shape: cache only a well-formed public answer, and add a `private_profile` code that a 403 or error 17 maps to without retry.

- [x] **Status:** resolved
**Completed:** 2026-09-29

Resolved in Task 13: `check_profile_is_public` caches only a well-formed public answer (a private verdict, or error 17 in a 200, is never cached), `check_user_exists` no longer caches error 6 as existing, and `fetch_once` raises without retry on a 403 or error 17, which the new `private_profile` code (not retryable) reports. Errors 10 and 26 stay unverified.

### F-B23-24: a null Deezer track title raises TypeError outside the retry wrapper and fails the job, orphaning sibling requests -- RESOLVED

`scrobblescope/deezer.py` `fetch_deezer_album` normalises track titles after the retried request returns, so a null `title` raises `TypeError` outside `retry_with_semaphore`. In `orchestrator/_deezer_fallback.py` `_run_deezer_fallback_phase` the bare `as_completed` loop lets that exception end the phase and the job (`unknown`), and four sibling tasks are left running. The cancel-and-drain fix from this branch covers two of the five fan-outs, not this one, nor the search and details phases. Mechanism reproduced; no live trigger seen; identical on `main`. Fix: tolerate a null title inside the wrapper (skip the track) and give the remaining fan-outs the same cancel-and-drain. Do not adopt `asyncio.TaskGroup` for it before F-B23-16 lands: an `ExceptionGroup`'s text defeats the substring classifier.

- [x] **Status:** resolved
**Completed:** 2026-09-29

Resolved in Task 13: `fetch_deezer_album` skips a track whose title is null or not text, and the Deezer fallback fan-out is wrapped in try/finally `cancel_and_drain` (public in `utils` since Task 15a; it was a private `lastfm` helper), so no sibling request is left running. The search fan-out already drained; the details fan-out and `spotify._fetch_album_details_one_by_one` gained the same try/finally in Task 15a, each with a test, so no fan-out is left without it.

### F-B23-30: a Last.fm page whose `recenttracks.track` is a single object would be read as a list of dict keys -- RESOLVED

Last.fm is known to serve a single-item collection as a bare object rather than a one-element list in some of its JSON responses. `lastfm._is_well_formed_page` does not check `recenttracks.track`, and both aggregators, `heatmap._aggregate_daily_counts` and `orchestrator.fetch_top_albums_async`, iterate it as a list, so a one-track page would be read as a sequence of dict keys. Not confirmed against the live API (found while fixing the well-formed-page check, Task 2). Fix: normalise a lone object into a one-item list at the anti-corruption layer in `lastfm.py`, and check `track` in the predicate so a page with any other shape is refused and retried.

- [x] **Status:** resolved
**Completed:** 2026-09-29

Resolved in Task 13: `lastfm._normalise_track_list` turns a lone `track` object into a one-item list, and `_is_well_formed_page` refuses any other non-list `track`, so the page is retried.

### F-B23-14: the unmatched report's artist portraits never loaded, and the gate's check passed by a fixture coincidence -- RESOLVED

The portrait `<img>` in `templates/unmatched.html` started hidden and
`loading="lazy"`. A hidden lazy image is never fetched: the browser waits for
it to come near the viewport, and an element with no box never does. Its
`load` event is what revealed it (`static/js/unmatched.js`), so no artist
portrait ever appeared. The controller measured this in Chromium and Firefox,
with a portrait URL of its own as in production, and it never loaded. A live
probe in Task 7 confirmed it in Chromium: with `loading="lazy"` restored, both
gate portraits report naturalWidth 0. `check_unmatched_report` passed anyway:
its fixture gave the portrait the same data URI as the covers already on the
page, and Chromium serves that from the document's image list whatever
`loading` says.

- [x] **Status:** resolved
**Completed:** 2026-09-29
The `loading` attribute is removed; `unmatched.js` already holds the request back with an IntersectionObserver. The gate now serves a wide (300x200) and a tall (200x300) portrait, each at a URL no other image uses. For each it asserts: loaded (naturalWidth > 0); shown, with the fallback hidden; its content box within 3% of the natural ratio; inside its slot; and the right `data-portrait`. It also checks one spotlight request per artist. Live probes: `loading="lazy"` fails, `loading="eager"` passes, and `object-fit: cover` at 100% x 100% fails. Route test: `test_unmatched_view_portrait_image_is_not_lazy`. Source: controller audit of the unmatched page, 2026-09-28 (Task 7).

### F-B23-12: remaining Spotify artwork display breaches outside the spotlight -- RESOLVED

Two more breaches of Spotify's "Using our content" guidelines, in the same
class as F-B21-60 part 1:

(a) **Crop.** The unmatched report crops Spotify artist portraits:
`.unmatched-artist-image { object-fit: cover }` in `static/css/unmatched.css`
crops the non-square photos fetched from `/api/artist_spotlight`
(`static/js/unmatched.js`). This breaks "Don't crop the artwork" the same
way F-B21-60's spotlight did.

(b) **Corner radius.** Row artwork uses 8px corners at every width, where
Spotify asks for 4px on small and medium devices.

Fix shape: `contain` on a surface-token letterbox for the unmatched
portraits, 4px/8px corners applied per breakpoint for row artwork, and a
gate check like `check_artist_spotlight_photo_not_cropped_when_non_square`.

- [x] **Status:** resolved
**Completed:** 2026-09-29
Every cover, artist portrait and placeholder on the results and unmatched pages now uses `.provider-artwork` (`static/css/results.css`). It sets `object-fit: contain` on the surface token, and the portrait is sized at its own proportions, so nothing is cropped, as Spotify's design page requires ("Don't crop the artwork in any way."). The corner radius is `--artwork-radius`: 4px, and 8px from 768px. Spotify's page says: "Artwork corners must be rounded to create optical blending with nearby UI elements. Small & medium devices should use a 4px corner radius, whereas large devices should use a 8px corner radius." The controller fetched both rules from https://developer.spotify.com/documentation/design ("Using our content") on 2026-09-29. The frontend gate asserts the radius of every artwork kind at 320, 390, 1024, 1279 and 1280px, and of the results row covers at 390 and 1280px. It also asserts that each portrait is drawn at its natural proportions inside its slot. Source: Task 1 review, 2026-09-28; fixed in Task 7.

### F-B21-60: the artist spotlight card breaks Spotify's content guidelines -- RESOLVED

Spotify's design guidelines ("Using our content",
https://developer.spotify.com/documentation/design#using-our-content) forbid
cropping artwork, putting images or text over it, animating it, and using
Spotify metadata without the Spotify logo or icon and a link back to Spotify.
The results page's artist spotlight (`templates/results.html`
`artist-spotlight-card`, `static/css/results.css` `.spotlight-card-bleed`,
`static/js/results-spotlight.js`) breaks these rules. The app uses the Web API
under Spotify's terms, so this is a compliance defect, not a taste question.

- **Crop:** Spotify artist photos are square, but the card is short and wide.
  `object-cover` cuts off the top and bottom.
- **Overlay:** `.spotlight-scrim-top` and `.spotlight-scrim-bottom` put
  gradients and text (the "Artist Spotlight" title, rank, name and play time)
  over the photo.
- **Animation:** every 7 seconds `renderCandidate` fades the whole card,
  photo included, to 15% opacity and swaps the artist.
- **Album art fallback:** with no artist photo, the card shows the first
  album's cover, cropped and overlaid (`spotlight_fallback_img`).
- **Attribution:** the app shows no Spotify logo or icon anywhere. The
  spotlight's link to Spotify is a plain arrow, shown only after hydration.
  Results rows already link each album to Spotify, but carry no Spotify icon.

Owner ruling, 2026-09-13, on the redesign:
- Show the artist photo whole, square, with 4px corners at small sizes and
  8px at large sizes. Nothing is drawn on top of it.
- Put the name, rank and play time beside or below the photo.
- Change artists without animating the photo. An instant swap is acceptable;
  reduced motion keeps the first artist, as today.
- **There is no text-only card and no album-art fallback.** A candidate with
  no Spotify artist photo is skipped in the rotation. If no candidate has a
  photo, the card is not shown at all. That includes the server render: do
  not render the card until an artist photo is known.
- Add the official Spotify icon, 21px or larger, linking to the artist on
  Spotify. Use Spotify's asset as supplied, not a redrawn glyph.
- Add the same icon next to the album links on results rows, or once as
  attribution for the list, whichever the guidelines' placement rules allow.
- Batch 22 adds Deezer as a fallback provider, so a row's artwork and link may
  come from either service. The attribution follows the album's own provider,
  under that provider's rules.

To check during the fix:
- whether the JPEG export captures Spotify artwork in a way the same rules
  forbid
- the gap where titles shown next to Spotify artwork are Last.fm spellings,
  not Spotify's metadata

Tests: route tests assert that the card is absent when no candidate has a photo
and that `spotlight_fallback_img` is gone. The frontend gate checks the photo
at its natural aspect ratio, no element overlapping the photo, no opacity
change on the photo during rotation, and the icon's rendered size and link
target.

**Partial progress, 2026-09-13 (Batch 22 WP-2 Task 6):** results and
unmatched rows now link to the album's own provider (`album_url`, not a
Spotify URL reconstructed from `spotify_id`) and carry a small text
attribution link naming that provider. This closes the "results rows carry
no Spotify icon" gap in substance but not to the letter -- it is a text
label, not either provider's official logo asset, so the ruling below is
still open. The artist spotlight card is unchanged: still cropped, still
overlaid, still animated. See F-B22-4 for the logo-asset gap.

**Partial progress, 2026-09-26 (Batch 23 WP-0 Task 5):** crop, overlay,
animation and the server- and client-side album-art fallback are fixed. The
photo is shown whole and square (4px corners at small sizes, 8px at large),
nothing draws on top of it, artist changes swap instantly with no fade, and
a candidate with no Spotify-confirmed photo is dropped from rotation --
`scrobblescope/spotlight.py` no longer seeds `image_url` from an album cover,
and `results-spotlight.js` no longer falls back to that seed either. If no
candidate has a confirmed photo, the card stays hidden. The Spotify icon and
provider-attribution bullets stay open under this same finding; the logo
asset gap is tracked separately as F-B22-4.

**Partial progress, 2026-09-27 (Batch 23 WP-0 fix wave, Group B):** the
photo box's `object-fit` is `contain`, not `cover` -- a non-square Spotify
photo is shown whole, letterboxed on the card's own surface token, instead
of cropped to fill the square box. Every confirmed candidate's photo is now
preloaded and cached before the rotation ever reveals anything, and a swap
sets the visible `<img>`'s src and alt together with the text, synchronously
-- no stale photo under a new artist's name. Each hydrate request -- the
fetch, its json body and the image preload together -- is bounded by one
8-second timeout; a request or a photo that never answers within that budget
is dropped like an unconfirmed candidate rather than keeping the whole card
hidden. The Spotify icon and provider-attribution bullets stay open under
this same finding; the logo asset gap is still tracked as F-B22-4.

- [x] **Status:** resolved
**Completed:** 2026-09-28
Part 2 landed: Spotify's official icon, supplied as a file and not redrawn
(black on the light theme, white on the dark theme), is 24px and links to
the artist from the spotlight. Results and unmatched lists attribute
Spotify once. The JPEG export keeps the icon. The export check is done.
The Last.fm-title gap is F-B23-11. Deezer's logo remains under F-B22-4.
Source: Spotify API review, 2026-09-13.

### F-B21-23: the inline marks diverge from the design contract on colour -- RESOLVED

`docs/design/README.md` "Assets" specifies the two inline variants as
**theme-reactive: text `currentColor`, bars `var(--bars-color)`**. Neither
shipped asset does it. `templates/inline/scrobble_scope_lockup_inline.svg` and
`scrobble_scope_inline.svg` contain zero occurrences of `currentColor`; the
letterforms carry no fill rule at all and the bars are pinned by an embedded
`<style>` to a literal `#6a4baf`.

This is the real cause of F-B21-21, which was fixed at the symptom. Because
the asset does not react to anything, every wrapper that displays it has to be
named explicitly in a stylesheet, and the index hero was the wrapper somebody
forgot. The list will need extending again for every mark WP-4 through WP-8
adds, and the gate check added with F-B21-21 exists only to catch that.

Doing what the contract says removes the class. Give the letterforms
`fill="currentColor"` and the bars `stroke: var(--bars-color)`, then any
wrapper that sets `color` and defines that token gets a correct mark with no
selector naming it. The per-wrapper list in `shell.css` collapses to nothing.

Two reasons it was not done in the F-B21-21 fix. The assets are shared with the
four Bootstrap pages, which currently colour them through `global.css`
`.dark-mode`, and those pages render only from a POST with session state, so no
gate can show the result. And `--bars-color` is a `global.css` token while the
migrated pages use `--shell-accent`; the two carry different dark values
(`#9370DB` against `#b39dde`), so unifying the asset means first deciding which
value wins.

- [x] **Status:** resolved
**Completed:** 2026-09-27
The inline marks carry fill=currentColor and stroke: var(--bars-color)
themselves; shell.css's five-rule per-wrapper list collapses to one color
declaration on .ss-mark; check_inline_marks_need_no_wrapper_list reads the
assets directly.
Source: F-B21-21 follow-up, 2026-08-26.

### F-B21-14: the heatmap has no path to its data that is not colour -- RESOLVED

Every value in the grid is encoded once, as a fill. The only way to read a
day is a mouse hover: the cells are `<rect>` elements with no `tabindex`, so
a keyboard reader cannot reach any of them, and there is no table view.

The ramp itself is sound. Measured in OKLab, `rocket_r` runs strictly
monotonic in lightness from 0.13 to 0.884 in steps of 0.107 to 0.144 -- a
reader who cannot separate the hues can still separate the values, which is
what a sequential ramp has to do. The `dataviz` skill's validator fails it,
but that validator is scoped to categorical palettes by its own footer, and
lightness monotonicity is the right test here.

The defect is at the ends, against their own surface. `#f9d576` sits at
1.34:1 on the light frame and `#03051a` at 1.12:1 on the dark one, so the
busiest and quietest days both disappear into the background they are drawn
on. The ramp is fixed by the design contract, so the fix is relief and not
re-tinting: make the cells focusable and give each an accessible name, or
ship a table view, or both.

**Owner ruled this critical on 2026-08-24**, while noting that a sighted
mouse user sees no problem. Both halves of that are the finding: it is
severe for the readers it affects and invisible to everyone else, which is
why no review caught it and no gate can.

- [x] **Status:** resolved
**Completed:** 2026-09-27
Heatmap cells carry a roving tabindex (one cell reachable by Tab at a
time, moved by the arrow keys or by any other focus, including a mouse
click), role=img and an aria-label built by the same cellAccessibleLabel
helper the mouse tooltip uses. The SVG itself carries role=group, not
role=img, so a cell's own role and label are not pruned as presentational
children of an image. check_heatmap_cells_are_keyboard_accessible (its
own slice module) proves it live, through the browser's own accessibility
tree.
Source: Batch 21 WP-3, `dataviz` skill pass, 2026-08-24; keyboard-model
and accessibility-tree follow-up, 2026-09-27.
