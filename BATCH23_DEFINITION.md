# BATCH23: Spotify listeners import the Extended Streaming History export

**Status:** Approved by the owner on 2026-09-13, **not started**. Batch 22 is
complete and had to come first: this batch builds on its provider interface
and its corrected release years.
**Branch:** not yet named. PLAYBOOK Section 3 names it before the first
commit, or the worktree guard raises WT003. Not `test`.
**Baseline:** 1522 tests passing and a frontend gate of 30 checks in 52 runs
at Batch 22's close. Both are the measurement at batch open, not a standing
claim; the latest of each lives in the newest Section 4 entry.
**Plan of record:**
`docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md` carries
every task, its tests and its exact commands. This file carries the scope,
the intended outcome, the work packages and their acceptance criteria.

---

## Context

**ScrobbleScope only works for Last.fm users.** Spotify's Web API cannot
supply lifetime listening history: `recently-played` returns the last 50
plays, and "top items" are ranked lists with no counts and no dates. Since
May 2025 full API access is for registered businesses with 250,000+ monthly
users, and development-mode apps are capped at five allowlisted users.

The data does exist, and Spotify gives it to the listener rather than to the
app: the **Extended Streaming History** export, requested from the account's
privacy page and delivered within 30 days as a zip of JSON, one row per
stream since the account opened. So the feature is an upload, not a login.

**What makes it feasible without a second pipeline:** everything after
aggregation -- `partition_albums_by_threshold`, `process_albums`, the
metadata cache, the results page and the unmatched report -- reads only
normalized `(artist, album)` keys and has no Last.fm dependency. An export
aggregator that produces the same shape as `fetch_top_albums_async` reaches
the same machinery unchanged.

**Owner rulings, 2026-09-13.** No Spotify login: it would buy rankings with
no play counts, the last 50 plays, and at most five allowlisted users, and it
was rejected. The entry point stays `/`, with a per-form source switch rather
than a landing page or a third mode tab. Both modes work from either source.
The upload is processed and discarded: nothing is written to disk or
Postgres, and IP address, user agent, username and country are dropped at
parse time. A play counts when `ms_played >= 30000`, is music rather than a
podcast or audiobook, and is not from a private session.

---

## Intended outcome

Batch 23 is complete only when all of these product outcomes hold:

- A Spotify listener can upload their export and get the same album rankings
  and heatmap a Last.fm user gets, with no account and no login.
- Nothing from the upload reaches disk, the database or the logs. The parsed
  aggregate expires with the two-hour job TTL like every other result.
- A malformed, hostile or wrong-kind file is refused with a message that says
  what to do next, before any job is created.
- The Last.fm path is untouched. Its routes, its validation, its upload
  limits and its tests behave exactly as they did before.
- Both sources gain the same new statistics, computed from data the pipeline
  already holds, with no additional API calls.
- The interface reads correctly for both sources: "plays" rather than
  "scrobbles" where the source is an export, and no field that asks a Spotify
  user for a Last.fm username.

## Runtime model

1. The form posts a zip and a mode. The upload is size-capped on the request
   class, because CSRF parses the multipart body before any view runs.
2. The route reads only the zip *directory* synchronously -- entry count,
   compression ratio, declared sizes, which entries are audio history -- so a
   structurally wrong file is refused as JSON without starting a job.
3. A job slot is taken, a job is created with `source: "spotify_export"` and
   no username, and a background thread parses the buffer.
4. Parsing streams: a 64 KB chunked incremental decoder feeds
   `JSONDecoder.raw_decode`, counting bytes actually read, so a zip header
   that lies still trips the bomb guard. No entry is ever loaded whole.
5. Aggregation produces exactly the dict the Last.fm path produces, and the
   job continues through the existing threshold partition, enrichment,
   filtering and results build.
6. The heatmap path mirrors this, anchored at the last play rather than
   today, because an export can lag by up to 30 days.

---

## Work packages

### WP-0 -- Behaviour-neutral extractions

The export path needs three pieces of the Last.fm path that are currently
inline, and the heatmap's zero-fill. Extracting them first keeps the
behaviour change and the structural change in separate commits, as Batch 22
WP-0 did.

- [ ] Extract `_cap_threshold_exclusions`, `_process_filtered_albums` (the
  tail of `_fetch_and_process`, from `_apply_pre_slice` to `set_job_results`)
  and `_run_coroutine_in_new_loop` (the Proactor boilerplate) in
  `orchestrator/`.
- [ ] Extract `_zero_fill_daily_counts` from `scrobblescope/heatmap.py` so
  both aggregators share one zero-fill.
- **Acceptance:** every existing test passes **unmodified**, including
  `tests/services/test_orchestrator_fetch_and_process.py`. No behaviour
  change ships in this work package.

### WP-1 -- Export error codes

Everything downstream raises these, so they land first.

- [ ] Add seven codes to `scrobblescope/errors.py` with
  `source: "spotify_export"`, none retryable: not a zip, no audio history
  files, too large, zip bomb, malformed JSON, no plays in the year, no plays
  in the window.
- [ ] Add `{limit}` and `{year}` formatting to the message builder.
- **Acceptance:** a test asserts every code has a message, and that the two
  formatted codes render with their value substituted.

### WP-2 -- The parser and aggregators, pure

A new `scrobblescope/spotify_export.py`, with no Flask and no I/O beyond the
buffer it is handed.

- [ ] `ExportLimits` with the declared caps: upload size, entry count,
  uncompressed size per entry and in total, compression ratio, and the size
  of a single JSON object.
- [ ] `open_export` validates the zip directory only: magic bytes, entry
  count, which entries are `Streaming_History_Audio_*.json` (any folder,
  `__MACOSX` and `._*` skipped), no encryption, stored or deflate only, and
  the declared ratio and total.
- [ ] `_iter_json_array` streams with an incremental UTF-8 decoder and
  `JSONDecoder.raw_decode`, counting bytes actually read. Never `json.load`
  on a whole entry.
- [ ] `iter_plays` yields tz-aware UTC plays, applies the play rule, skips
  podcasts and audiobooks, keeps skip counters, and never copies a private
  field.
- [ ] `aggregate_albums` returns exactly the shape `fetch_top_albums_async`
  returns, keyed by `normalize_name`, plus stats with the same keys as the
  Last.fm stats.
- [ ] `aggregate_daily_counts_from_plays` anchors its window at
  `min(today, last play)` and reuses WP-0's zero-fill.
- **Acceptance:** zips built in memory cover a nested folder, ignored Video
  and `__MACOSX` entries, the 29999/30000 ms boundary, podcast, audiobook,
  private-session and null-metadata rows, a year boundary asserted tz-aware,
  an array broken across chunk boundaries, a real deflate bomb, a lying zip
  header, non-zips, empty zips and truncated JSON. Every limit is
  mutation-checked. The aggregator's output feeds
  `partition_albums_by_threshold` unchanged.

### WP-3 -- Job hand-off

A new `scrobblescope/export_jobs.py`, so the parser never knows about jobs
and the orchestrator never knows about zips.

- [ ] `export_album_task` parses in `asyncio.to_thread`, closes the buffer,
  then runs the existing threshold partition, stats, unmatched records and
  `_process_filtered_albums`, mapping `ExportError` to `set_job_error`.
- [ ] `export_heatmap_task` mirrors `_fetch_and_process_heatmap` from
  aggregation onward, with `source: "spotify_export"` and `username: None`.
- [ ] A `BoundedSemaphore(2)` around parsing caps peak memory.
- **Acceptance:** `process_albums` receives the aggregate;
  `fetch_all_recent_tracks_async` is never called, proven by patching it to
  raise; an error reaches the job; the buffer is closed on every path.

### WP-4 -- Routes and upload handling

- [ ] `POST /spotify_export_loading` takes the file and mode plus the
  existing album fields through the existing validators, runs `open_export`
  synchronously, takes a job slot, creates the job and starts the thread,
  returning 202 with the job id and redirect.
- [ ] `UploadAwareRequest` in `create_app` applies the upload cap and returns
  `BytesIO` from `_get_file_stream` **only** for that endpoint, so nothing is
  spooled to disk and every other endpoint defers to `super()`.
- [ ] A 413 handler, and CSRF failures answering in JSON on the upload path.
- [ ] `_extract_job_params` gains `source`; render helpers branch on it and
  never put a placeholder in `username`, because error messages format it.
- [ ] `static/js/loading.js` offers "Upload again" rather than Retry for this
  source, because a file cannot be re-POSTed.
- **Acceptance:** a multipart success; a 413 on this endpoint while a large
  Last.fm POST is unaffected; CSRF answered as JSON; each synchronous error
  code; the thread started with the expected arguments; and a test proving
  the stream is `BytesIO` and never `SpooledTemporaryFile`.

### WP-5 -- The interface

- [ ] A two-option segmented control at the top of each form card, "Your
  listening history": Last.fm or Spotify file, reusing the existing `.seg`
  pattern. Last.fm keeps the username field and its blur validation; Spotify
  shows a `.zip` input, a link to the explainer, and the privacy line.
- [ ] `GET /spotify`, a new explainer page: what the export is, why there is
  no login, how to request it, what counts as listened, the privacy promise,
  and how the results differ from Last.fm.
- [ ] One file reference across both modes, the source choice remembered in
  `localStorage` and the file never remembered, and `/?source=spotify`
  preselection.
- [ ] Upload through XHR with a progress bar, with size and extension checked
  in the browser first and `/validate_user` skipped for this source.
- [ ] Wording by source across results, unmatched, loading and the heatmap
  partials: "plays" rather than "scrobbles", the results heading naming the
  Spotify history, and export filenames carrying the source.
- **Acceptance:** the frontend gate covers arrow-key switching in the radio
  group, the right field per source, the file carrying across mode tabs,
  `/?source=spotify` preselection, an upload with a synthetic zip, the
  hidden-Retry state, a 360px layout, and `/spotify` rendering without
  horizontal scroll in both themes. Only declared spacing steps are used.

### WP-6 -- New statistics for both sources

Every statistic is computed from data the pipeline already holds, so no
additional API call is made and Last.fm and Spotify users get the same thing.

- [ ] Per album: completion ("9 of 12 tracks"), the most-played track shown
  with its original name, and the first listen that year. Both aggregators
  keep one original track name per normalized key.
- [ ] Per year: the age of the music as a decade breakdown, and hours
  listened.
- [ ] Heatmap: longest and current streak, busiest weekday and busiest hour,
  stated as UTC, with both aggregators feeding one pure helper so the two
  sources cannot disagree.
- [ ] The results rows, a year-summary block, the heatmap result partial, and
  three new CSV columns.
- **Acceptance:** pure-function tests per statistic with tz-aware timestamps
  and the edge cases that break naive implementations -- an album with no
  durations, a single-day streak, a tie for most played. Route tests check
  the rendered values, and the gate pins the new blocks at 390px and 1280px.

### WP-7 -- Documentation, the deferred audit, and close-out

- [ ] README, the runtime architecture view and the design reconciliation
  record the second source, the data-handling guarantees and the new
  statistics.
- [ ] **The Batch 21 frontend and accessibility audit runs here** (owner
  ruling, 2026-09-13): keyboard traversal of every page, focus visibility,
  label associations, contrast in both themes and tap-target size, over the
  final interface. Results are filed as `F-SWE-N` or `F-AUDIT-N`. **This
  batch does not close until it has run.**
- [ ] The complete test, frontend, pre-commit and docsync gates, then the
  standard close-out procedure.

---

## Batch acceptance

- A real export produces album results and a heatmap that a Last.fm user
  would recognise, and the owner's own export cross-checks against their
  Last.fm results for one year within the differences the two sources
  explain.
- No upload reaches disk, the database or the logs, and a test enforces each.
- Every structural failure mode is refused before a job exists, with a
  message naming the next action.
- The Last.fm path's tests pass unmodified throughout the batch.
- Peak memory is measured, not assumed: `tracemalloc` and VmHWM on the real
  export, locally and on Fly, then three concurrent uploads without an OOM,
  with the upload cap and the parse semaphore set from those numbers.
- The deferred frontend and accessibility audit has run and its findings are
  filed.
- The full Python suite, the two-browser frontend gate, the pre-commit suite
  and `doc_state_sync.py --check` all pass on the final documented state.

---

## Out of scope

- Any Spotify login. Apps without extended access serve at most five
  allowlisted users, and the owner rejected the path.
- Deduplicating duplicate rows across export files. They are counted in v1,
  and the decision is recorded rather than silently taken.
- Storing any part of an upload for later reuse, including as a cache of the
  listener's own history.

## Constraints

- **Memory is the binding constraint.** The Fly machine is shared-cpu-2x with
  512 MB and gunicorn runs one worker with four threads. Streaming parsing,
  the parse semaphore and a measured upload cap are what keep it inside that.
- **Never create a new Spotify Client ID.** A new one loses the postponement
  F-B21-59 records, and this source raises traffic through the same
  enrichment path.
- Werkzeug spools uploads over 500 KB to a temporary file by default, which
  breaks the never-on-disk guarantee; the request class is where that is
  overridden.
- Standard library only for the new parsing code; no new dependency.
