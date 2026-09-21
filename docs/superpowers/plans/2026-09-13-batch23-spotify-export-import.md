# Batch 23 (queued): Spotify listeners import the Extended Streaming History export

Status: approved by the owner on 2026-09-13, **not started**. Build begins
after Batch 22 (enrichment providers,
`docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`), on its
own branch; PLAYBOOK Section 3 must name that branch first, or the worktree
guard raises WT003. Promote this file to a root `BATCH23_DEFINITION.md` when
the batch opens. Batch 22 comes first by owner ruling on 2026-09-13: this
batch then builds on the provider interface and on corrected release years.

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
- Process and discard: nothing is written to disk or Postgres, and IP address,
  user agent, username and country are dropped at parse time.
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
- **`aggregate_albums(plays, year)`** builds exactly the dict that
  `fetch_top_albums_async` in `scrobblescope/orchestrator.py` builds:
  - key: `normalize_name` from `scrobblescope/domain.py`
  - values: `play_count`, `track_counts` keyed by `normalize_track_name`,
    `original_artist`, `original_album`
  - it also returns stats with the same keys as the Last.fm stats
    (`total_scrobbles`, `unique_albums`), plus `rows_read` and the skip
    counters
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

## Phase 2: Hand-off to the worker; the Last.fm path unchanged

- **Pure extractions in `orchestrator.py`:**
  - `_cap_threshold_exclusions`
  - `_process_filtered_albums`: the tail of `_fetch_and_process`, from
    `_apply_pre_slice` to `set_job_results`
  - `_run_coroutine_in_new_loop`: the Proactor boilerplate
  - `tests/services/test_orchestrator_fetch_and_process.py` must pass
    unmodified
- **New `scrobblescope/export_jobs.py`:**
  - `export_album_task` parses in `asyncio.to_thread` and closes the buffer.
    It then runs `partition_albums_by_threshold`, `set_job_stat`,
    `add_job_unmatched` and `_process_filtered_albums`, and maps
    `ExportError` to `set_job_error`.
  - `export_heatmap_task` mirrors `_fetch_and_process_heatmap` from
    aggregation onward, with `source: "spotify_export"` and
    `username: None`.
  - A `BoundedSemaphore(2)` around parsing caps peak memory.
- **Tests** go in `tests/services/test_export_jobs.py`:
  - `process_albums` receives the aggregate
  - `fetch_all_recent_tracks_async` is never called (patch it to raise)
  - errors reach the job, and the buffer is closed

## Phase 3: Routes and upload handling

- **`POST /spotify_export_loading`** takes multipart fields `export_file` and
  `mode`, plus the existing album fields, which go through the existing
  validators.
  - It runs `open_export` synchronously. That only reads the zip directory, so
    structural errors come back immediately as 400 JSON.
  - It then calls `acquire_job_slot` and
    `create_job({"source": "spotify_export", "username": None, ...})`.
  - It starts `start_job_thread(export_*_task, (job_id, BytesIO(data), ...))`
    and returns 202 `{job_id, redirect}`.
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

## Phase 4: UI (`templates/index.html`, `templates/partials/_heatmap_form.html`, `static/js/index.js`, `static/js/heatmap.js`)

- **Entry point:** the same index page and form cards; the page layout does not
  change. Only the first field of each form (the Last.fm username) depends on
  the source, so only that field switches.
  - There is no landing page at `/`: it would cost Last.fm users a click on
    every visit and break `/?mode=` links.
  - There is no third mode tab: source and mode are independent choices.
- **`GET /spotify` explainer** (new `templates/spotify_export.html`, a route in
  `scrobblescope/routes.py`) covers:
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
    - a privacy line: the file is read once and never saved; private sessions,
      podcasts and plays under 30 seconds are left out
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
  (`scrobblescope/orchestrator.py`):
  - **Completion ("9 of 12 tracks"):** the tracks in `track_counts` that are
    also in the cached `track_durations`, over `len(track_durations)`.
  - **Most-played track:** the largest value in `track_counts`, shown with its
    original name. Aggregation has to keep one original track name per
    normalised key, in both the Last.fm and the export aggregator.
  - **First listen that year:** aggregation keeps the earliest timestamp per
    album, alongside `play_count`.
- **Year summary**, computed once after `_build_results`:
  - **Age of the music:** plays weighted by listening year minus release year,
    as a decade breakdown ("62% of plays were albums from before 2010"). Use
    `release_date` and its precision.
  - **Hours listened:** the sum of `play_time_seconds`, already computed.
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
3. **Memory:** measure `tracemalloc` peak and VmHWM parsing the owner's real
   export, locally and on Fly (`fly ssh console`). Then run 3 uploads at once
   and watch for OOM. Set `EXPORT_MAX_UPLOAD_BYTES` and the parse semaphore
   from those numbers; the fallback is scaling to 1 GB.
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

- **Memory:** 512 MB total. Mitigated by the parse semaphore, streaming parsing
  and a measured cap.
- **Spotify API:** the Feb 2026 changelog lists "Get Several Albums" as removed
  and caps search at 10 results. Both work for this app today, and this
  source raises traffic through `process_albums`. The app is a Development Mode
  app whose endpoint removals Spotify postponed with no new date. FINDINGS
  F-B21-59's single-album fallback landed on 2026-09-13, and Batch 22 adds
  Deezer behind Spotify before this batch opens.
  Never create a new Spotify Client ID for this work: a new one gets the
  removals at once.
- **Privacy:**
  - uploads stay in memory, and a test enforces it
  - never log file names, rows or IPs
  - aggregates expire with the 2-hour job TTL
- **Data quirks:** duplicate rows across files are counted, not deduplicated,
  in v1.
