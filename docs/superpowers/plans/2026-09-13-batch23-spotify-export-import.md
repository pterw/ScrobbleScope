# Batch 23 export outline: Spotify listeners import Extended Streaming History

Approved by the owner on 2026-09-13. This is the cross-WP design outline;
`BATCH23_DEFINITION.md` owns current scope, shared contracts and acceptance,
and PLAYBOOK Section 3 owns current status and execution order. Each WP
gets a specialized plan implemented through SDD. Those plans refine this
outline within the definition's contracts; its phase numbers are not WP
execution order. The definition's editorial revision records the
2026-09-23 consistency edits by Codex (GPT-6).

## Context

ScrobbleScope only works for Last.fm users. Spotify's Web API cannot give
lifetime listening history: `recently-played` returns the last 50 plays, and
"top items" are ranked lists with no counts or dates. stats.fm gets lifetime
data from Spotify's own data export (account Privacy page, "Extended streaming
history", delivered in up to 30 days as a zip of JSON files, one row per
stream since the account opened). stats.fm can also record new plays after a
Spotify login, but that path is closed to ScrobbleScope: since May 2025 full
API access is for registered businesses with 250k+ monthly users, and
development-mode apps are capped at 5 allowlisted users (Feb-Mar 2026).

So the feature is an upload of that export. It needs no user login, because
the enrichment step already uses app-only credentials. A live probe on
2026-09-13 confirmed those still get HTTP 200 from `/v1/albums?ids=`,
`/v1/albums/{id}` and `/v1/search`.

**Owner decisions:**
- Direction A: no Spotify login. Ship the export upload, then add new stats
  that need no new API calls, for both Last.fm and Spotify users.
  - A login would give only rankings with no play counts, the last 50 plays
    and saved albums, and at most 5 allowlisted users. It was rejected.
- Entry: `/` stays the form, with a per-form "Last.fm | Spotify file" switch.
  A separate `/spotify` page explains the export.
- Both modes: album results and heatmap.
- Process and discard under `BATCH23_DEFINITION.md` "Data handling", the
  single owner of transient-history, catalog-cache and diagnostic rules.
- A play is `ms_played >= 30000`, music only, and not in a private session.
- The upload is the zip exactly as Spotify sends it.

**Verified constraints:**
- Fly VM is shared-cpu-2x with 512 MB (`fly.toml`); gunicorn runs 1 worker
  and 4 threads.
- Werkzeug's `default_stream_factory` spools uploads over 500 KB to a
  temporary file, which breaks "never on disk".
- `CSRFProtect` (`app.py`) parses the multipart body before the view runs, so
  the size cap has to live on the request class, not in the view.
- Everything after aggregation (`partition_albums_by_threshold`,
  `process_albums`, the cache, results and the unmatched page) reads only
  normalised `(artist, album)` keys and has no Last.fm dependency.

## Phase 1: Parser and aggregators, pure (new `scrobblescope/spotify_export.py`)

- **`ExportLimits`** (starting values, tuned by the memory step in
  Verification):
  - upload 40 MB
  - at most 500 zip entries
  - at most 64 MB uncompressed per entry and 400 MB in total
  - compression ratio at most 100
  - a single JSON object at most 64 KB
- **`ExportError(code)`** raises the error codes listed in Phase 5.
- **`open_export(buffer, limits)`** checks only the zip directory:
  - the zip magic bytes, and whether `ZipFile` opens
  - the entry count
  - which entries are `Streaming_History_Audio_*.json`: matched on the base
    name, with any folder allowed and `__MACOSX` and `._*` skipped
  - no encrypted entries, and only the stored or deflate methods
  - the declared compression ratio and declared total size
- **`_iter_json_array`** is a stdlib streaming array reader:
  - it reads 64 KB chunks through an incremental UTF-8 decoder into
    `JSONDecoder.raw_decode`
  - it counts the bytes actually read, so a zip header that lies still trips
    `export_zip_bomb`
  - never call `json.load` on a whole entry
- **`iter_plays`** yields `Play(ended_at: tz-aware UTC, artist, album, track,
  ms_played)`:
  - it applies the play rule and skips podcast episodes and audiobooks
  - it keeps skip counters
  - the private fields are never copied
- **`aggregate_albums(plays, year)`** builds the pre-threshold album mapping
  in `BATCH23_DEFINITION.md` WP-2, not the full return tuple of
  `fetch_top_albums_async`:
  - key: `normalize_name` from `scrobblescope/domain.py`
  - values: `play_count`, `track_counts` keyed by `normalize_track_name`,
    `original_artist`, `original_album`
  - aggregation stats accompany the mapping; the specialized plan follows
    WP-2's distinction between row/skip counts and accepted plays
  - the job hand-off applies threshold partitioning once and records the
    resulting eligible/excluded counters
- **`aggregate_daily_counts_from_plays(plays, today)`** is a sibling of
  `_aggregate_daily_counts`, not a reuse of it:
  - it anchors the window at `min(today, last play)`, because an export can
    lag by up to 30 days
  - move the zero-fill loop in `scrobblescope/heatmap.py` into
    `_zero_fill_daily_counts` so both functions share it; Last.fm behaviour
    stays the same

**Tests** go in `tests/test_spotify_export.py`, using zips built in memory:
- a nested folder, with Video and `__MACOSX` entries ignored
- rows at 29999 ms and at 30000 ms
- podcast, audiobook, private-session and null-metadata rows
- plays at `2023-12-31T23:59:59Z` and `2024-01-01T00:00:00Z`, with tz-aware
  assertions
- an array that breaks across chunk boundaries
- a real deflate bomb, and a zip header that lies about sizes
- files that are not zips, empty zips and truncated JSON
- aggregator output fed into `partition_albums_by_threshold`

Mutation-check every limit.

## Phase 2: Hand-off to the worker; preserve existing Last.fm behaviour

- **Pure extractions**, landed in Batch 23 WP-0 Part A (2026-09-23), with no
  test changed:
  - `orchestrator._cap_threshold_exclusions`
  - `orchestrator._process_filtered_albums`: the tail of `_fetch_and_process`,
    from `_apply_pre_slice` through the release-check hand-off and the "Done"
    progress, so the export task gets both without a copy
  - `worker.run_coroutine_in_new_loop`: the run-and-close wrapper. It landed
    in `worker.py`, not `orchestrator/`, so the heatmap path shares it
  - `heatmap._zero_fill_daily_counts`
- **New `scrobblescope/export_jobs.py`:**
  - `export_album_task` parses in `asyncio.to_thread` and closes the buffer.
    It then runs `partition_albums_by_threshold`, `set_job_stat`,
    `add_job_unmatched` and `_process_filtered_albums`, and maps
    `ExportError` to `set_job_error`.
  - `export_heatmap_task` mirrors `_fetch_and_process_heatmap` from
    aggregation onward, with `source: "spotify_export"` and
    `username: None`.
  - A `BoundedSemaphore(2)` limits concurrent parsing; whole-process memory
    acceptance is owned by `BATCH23_DEFINITION.md` "Batch acceptance".
- **Tests** go in `tests/services/test_export_jobs.py`:
  - `process_albums` receives the aggregate
  - `fetch_all_recent_tracks_async` is never called (patch it to raise)
  - errors reach the job, and the buffer is closed

## Phase 3: Routes and upload handling

- **`POST /spotify_export_loading`** takes multipart fields `export_file` and
  `mode`, plus the existing album fields, which go through the existing
  validators.
  - It runs `open_export` synchronously. That only reads the zip directory, so
    directory-detectable errors come back immediately as 400 JSON.
    Content failures discovered during streaming terminate the created job,
    as required by `BATCH23_DEFINITION.md` "Runtime model".
  - It then uses WP-4's shared admission module to reserve capacity, create
    the job with `source: "spotify_export"` and `username: None`, and start
    the task, with rollback on failure.
  - Admission uses `start_job_thread(export_*_task, (job_id, upload, ...))`,
    handing over the request's own buffer. The route returns 202
    `{job_id, redirect}` after that succeeds.
    (Amended 2026-09-23: this read `BytesIO(data)`, which copies the upload
    and holds it twice. See "Upload ownership and the waiting bound" below.)
- **`UploadAwareRequest`**, set in `app.py` `create_app`, applies only when the
  endpoint is `main.spotify_export_loading`:
  - `max_content_length = EXPORT_MAX_UPLOAD_BYTES`
  - `_get_file_stream` returns `BytesIO`, so nothing is spooled to disk
  - every other endpoint defers to `super()`, so the Last.fm forms are
    unaffected
- **Error handling:** add `errorhandler(413)`, and make `handle_csrf_error`
  return JSON for the upload path.
- **Identity:** `_extract_job_params` gains `source`. Render helpers branch on
  `source` and never put a fake name in `username`, because error messages
  format `{username}`.
- **Retry:** `static/js/loading.js` hides Retry for `spotify_export` and shows
  "Upload again", because a file cannot be re-POSTed.
- **Tests** go in `tests/test_routes_spotify_export.py`:
  - multipart success
  - a 413 on this endpoint, while a large Last.fm POST is unaffected
  - CSRF JSON, using `csrf_app_client`
  - the synchronous error codes
  - `start_job_thread` arguments
  - the file stream is `BytesIO`, never `SpooledTemporaryFile`

### Upload ownership and the waiting bound (owner ruling, 2026-09-23)

Adopted from card 04 of `docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`.
The privacy and memory guarantees were spread across four places: the request class, the route's
directory check, the thread hand-off and the parser. Each place was correct on its own, and no single
owner guaranteed the whole. This section gives the upload one owner at every moment. It is a design
rule for WP-2 to WP-4, not a new module or framework.

- **One owner at a time.** The buffer is the `BytesIO` that `UploadAwareRequest` creates, and it is
  never copied.
  - The route owns it until `start_job_thread` succeeds, and it closes the buffer on every refusal:
    an invalid directory, admission refused, or a failed thread start.
  - From a successful start on, the export task owns it and closes it on every path, success and
    failure alike.
  - Request teardown must no longer close a successfully transferred
    buffer. References needed for hand-off do not confer cleanup ownership;
    the WP-3/WP-4 plans specify the transfer without copying the buffer.
- **The lifecycle lives in `spotify_export.py`**, as one small type that owns the buffer, the
  directory inspection, the streamed read and `close()`, usable as a context manager. It knows nothing
  of Flask or jobs. Job admission stays in WP-4's admission module, and parse concurrency stays with
  the parse semaphore.
- **The waiting bound.** `BoundedSemaphore(2)` bounds how many parses *run*, not how many buffers
  *wait* for a permit. With `MAX_ACTIVE_JOBS` at 5, five uploads could sit in memory at once on a
  512 MB machine. So admission also caps export jobs in flight -- admitted, with the buffer not yet
  closed -- at `EXPORT_MAX_IN_FLIGHT`, and refuses the next export upload with 429.
  - Last.fm jobs never count against it.
  - This bounds admitted upload buffers only. Receiving multipart requests
    and retained results also use memory; follow the whole-process
    measurement required by `BATCH23_DEFINITION.md` "Batch acceptance".
  - Verification step 3 sets the in-flight cap, the upload cap and the semaphore together, from
    the same measurement.
- **Tests (WP-3 and WP-4):**
  - the buffer is closed after each refusal path, after a parser failure and after success;
  - with `EXPORT_MAX_IN_FLIGHT` export jobs in flight, the next export upload gets a 429 and no job
    is created, while a Last.fm job is still admitted if shared capacity remains;
  - no second copy of the upload exists: the task receives the request's own buffer object;
  - a delayed task still reads the transferred buffer after response and
    request teardown, then closes it on completion.

## Phase 4: UI (`templates/index.html`, `templates/partials/_heatmap_form.html`, `static/js/index.js`, `static/js/heatmap.js`)

- **Entry point:** the same index page and form cards; the page layout does not
  change. Only the first field of each form (the Last.fm username) depends on
  the source, so only that field switches.
  - There is no landing page at `/`: it would cost Last.fm users a click on
    every visit and break `/?mode=` links.
  - There is no third mode tab: source and mode are independent choices.
- **`GET /spotify` explainer** (new `templates/spotify_export.html`, a route in
  the `scrobblescope/routes/` package) covers:
  - what the export is, and why there is no Spotify login
  - how to request it: Account, Privacy settings, "Extended streaming history"
    (not "Account data"), then an email that can take up to 30 days
  - what counts as listened
  - the privacy promise
  - how results differ from Last.fm

  It ends with two links, "I have my file" (`/?source=spotify`) and "Show my
  heatmap" (`/?source=spotify&mode=heatmap`). The Spotify field links to it
  ("Don't have it yet?"), and the hero carries a small secondary link, "Use a
  Spotify data export instead".
- **Source switch:** add a two-option segmented radio group at the top of each
  form card, labelled "Your listening history", with options "Last.fm" and
  "Spotify file". It reuses the `.seg` / `.seg__radio` / `.seg__option`
  pattern that "Rank by" already uses.
  - **Last.fm selected:** the current username field and its blur validation.
  - **Spotify file selected:**
    - a `.zip` file input, labelled "Your Spotify data file"
    - a short "Don't have it yet? How to get your Spotify data" link to
      `/spotify`
    - privacy copy follows `BATCH23_DEFINITION.md` "Data handling";
      private sessions, podcasts and plays under 30 seconds are left out
  - The "Listening year" hint reads `2008–{{ current_year }}` for Spotify, since
    there is no join-year lookup.
- **One file for both modes:** page JS keeps a single `File` reference, so a
  file picked in Top albums still shows as selected under Heatmap. Remember
  the source choice in `localStorage`, but never the file.
- **Deep link:** `/?source=spotify` (optionally with `&mode=heatmap`)
  preselects the source, the same way `initial_mode` works today.
- **Hero copy:** "Last.fm album filtering" becomes "Album filtering",
  "Every day you scrobbled" becomes "Every day you listened", and
  "Personalized scrobble stats" becomes "Personalized listening stats".
- **Copy rule:** say "what counts as listened", never "thresholds".
- **Upload script:** use XHR for an upload progress bar, check the size and
  extension in the browser first, and skip `/validate_user` for this source.
  The heatmap form already submits through `fetch`; switch its endpoint and
  body.
- **Wording by source** in `results.html`, `unmatched.html`, `loading.html`,
  `partials/_heatmap_result.html` and `_heatmap_loading_details.html`:
  - the results heading becomes "Top albums from your Spotify history"
  - say "plays", not "scrobbles"
  - export filenames become `scrobblescope_spotify_<year>` in `results.js`
    and `heatmap.js`
- **Frontend gate:** add arrow-key switching in the source radio group, the
  right field for each source, the file carrying across mode tabs,
  `/?source=spotify` preselection, the upload flow with a synthetic zip, the
  hidden-Retry state, a 360 px layout, and `/spotify` rendering with no
  horizontal scroll in both themes.
- **Spacing rule:** use only the declared spacing steps; the template-shell
  guard fails otherwise.

## Phase 5: Error codes (`scrobblescope/errors.py`, `source: "spotify_export"`, not retryable)

| Code | Message |
| --- | --- |
| `export_not_zip` | Upload my_spotify_data.zip exactly as Spotify sent it. |
| `export_no_audio_history` | No Streaming_History_Audio files; request Extended streaming history, not Account data. |
| `export_too_large` | The file is larger than {limit} MB (413). |
| `export_zip_bomb` | The zip expands to more data than a streaming history should. |
| `export_malformed_json` | A history file couldn't be read; download the export again. |
| `export_no_plays_in_year` | No music plays found in {year} in this export. |
| `export_no_plays_in_window` | No music plays in the year before the export's last play. |

Add `{limit}` and `{year}` formatting. A test checks that every code has a
message.

## Phase 6: New stats for both sources, with no new API calls

This ships after Phases 1-5. Every stat is computed from data the pipeline
already holds, so Last.fm and Spotify users get the same thing.

- **Per album**, added to each result in `_build_results`
  (`scrobblescope/orchestrator/_results.py`):
  - **Completion ("9 of 12 tracks"):** the tracks in `track_counts` that are
    also in the cached `track_durations`, over `len(track_durations)`.
  - **Most-played track:** the largest value in `track_counts`, shown with its
    original name. Aggregation has to keep one original track name per
    normalised key, in both the Last.fm and the export aggregator.
  - **First listen that year:** aggregation keeps the earliest timestamp per
    album, alongside `play_count`.
- **Year summary:** WP-6's specialized plan settles the population and
  calculation point under the definition's Statistics contract; do not
  infer whole-year coverage from an already filtered or sliced result list.
  - **Age of the music:** plays weighted by listening year minus release year,
    as a decade breakdown ("62% of plays were albums from before 2010"). Use
    `release_date` and its precision.
  - **Hours listened:** the plan specifies the duration basis and coverage.
    Existing `play_time_seconds` is a catalog-duration estimate; do not
    silently present it as measured listening time from the export.
- **Heatmap extras** in `scrobblescope/heatmap.py`, from the same timestamps:
  - longest streak of days with any listening, and the current streak
  - busiest weekday and busiest hour (UTC; say so in the UI)
  - both aggregators feed one pure helper, so the two sources match
- **UI:** completion and most-played track on each results row; a small year
  summary block on `results.html`; streak and busiest-day stats on
  `partials/_heatmap_result.html`.
  - Design and copy go through the design review the batch already uses.
  - Numbers stay in the existing figure typeface.
- **CSV export:** `results.js` gains completion, most-played track and first
  listen columns.
- **Tests:** pure-function tests for each stat, with tz-aware timestamps and
  edge cases (an album with no durations, a single-day streak, a tie for most
  played). Route tests check the rendered values, and the frontend gate pins
  that the new blocks render without overflow at 390px and 1280px.

## Verification

1. `pytest -q`, `doc_state_sync.py --check`, pre-commit, and the frontend gate.
2. **Local end to end:** a `scripts/dev/make_synthetic_export.py` zip (20 files
   of 15k rows, with podcasts, private-session rows and a nested folder),
   uploaded through the browser in both modes. Check the results, unmatched
   and heatmap pages.
3. **Memory:** execute `BATCH23_DEFINITION.md` "Batch acceptance"'s
   whole-process measurement and overload checks. Set the request cap,
   parse semaphore and export in-flight cap from that evidence. Any hosting
   capacity increase remains an owner decision.
4. **Cross-check:** the owner's Spotify export against their Last.fm results
   for one year. Expect small differences, because `ts` is the stream end time
   and offline plays carry sync time.
5. **Docs:** a PLAYBOOK entry and FINDINGS for the new source, the
   data-handling guarantees, and the risks below.
6. **The deferred Batch 21 audit, in this batch's close-out** (owner ruling,
   2026-09-13). Batch 21 WP-8 charters a frontend and accessibility pass over
   the migrated `static/js/`, templates and `tailwind.src.css`: the mandated
   principles where they apply, plus keyboard traversal of every page, focus
   visibility, label associations, contrast in both themes and tap-target
   size. It runs here, after this batch's UI lands, so it is done once over
   the final interface. File results as F-SWE-N or F-AUDIT-N. This batch does
   not close until it has run.

## Risks

- **Memory:** 512 MB total. Mitigated by the parse semaphore, streaming parsing,
  a measured upload cap, and the in-flight bound on export jobs waiting for a
  parse permit.
- **Spotify API:** the Feb 2026 changelog lists "Get Several Albums" as removed
  and caps search at 10 results. Both work for this app today, and this
  source raises traffic through `process_albums`. The app is a Development Mode
  app whose endpoint removals Spotify postponed with no new date. FINDINGS
  F-B21-59's single-album fallback landed on 2026-09-13, and Batch 22 adds
  Deezer behind Spotify before this batch opens.
  Never create a new Spotify Client ID for this work: a new one gets the
  removals at once.
- **Privacy:** `BATCH23_DEFINITION.md` "Data handling" owns the contract
  and the required end-to-end checks. Shared provider code is in scope.
- **Data quirks:** duplicate rows across files are counted, not deduplicated,
  in v1.
