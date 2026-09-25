# BATCH23: Spotify listeners import the Extended Streaming History export

**Editorial revision -- 2026-09-23, Codex (GPT-6).** Edited at the owner's
request after the read-only sensibility review. Changes and reasons:

1. Separate pre-job rejection from background failure, so streamed content
   checks do not contradict the synchronous validation promise.
2. Clarify Last.fm compatibility, so additive statistics and shared admission
   can land without weakening existing regression coverage.
3. Define transient listening data versus reusable catalog metadata, so the
   privacy promise agrees with the existing enrichment cache.
4. Clarify the aggregation hand-off, so WP-2 and WP-3 do not partition twice.
5. Strengthen upload lifetime and memory acceptance, so request teardown and
   incoming buffers are covered as well as admitted jobs.
6. Record specialized SDD plans as each WP's implementation authority, with
   statistics semantics settled before WP-6 implementation.
7. Align the linked export outline and README, so older wording does not
   contradict this definition. No runtime code or WP completion changed.

**Status:** Active since 2026-09-21; **WP-0 is next.** Approved 2026-09-13.
The next-package claim must stay on this line: DOC007 reads it here only.
Batch 22 is complete and had to come first: this batch builds on its
provider interface and its corrected release years.
**Branch:** `feat/batch23-wp0-hygiene`. Named by the owner on 2026-09-21 and
declared in PLAYBOOK Section 3; not `test`.
**Baseline:** 1522 tests passing and a frontend gate of 30 checks in 52 runs
at Batch 22's close. Both are the measurement at batch open, not a standing
claim; the latest of each lives in the newest Section 4 entry.
**Scope amended 2026-09-23:** the owner widened WP-0 into three parts
(below). Later owner-approved clarifications are recorded in the affected
work packages and the editorial revision above; no work package is added.
**Planning authority:** this definition owns batch scope, shared contracts
and acceptance. Each WP gets a specialized plan before implementation,
executed through subagent-driven development (SDD). Its approved plan owns
task order, implementation detail and verification commands. Record its
path in the WP when approved; a plan that changes a shared contract or
scope must amend this definition first.
`docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md` is the
cross-WP export outline, not a substitute for those specialized plans.
WP-0 has its own plans: `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`
covers Part A and most of Part B, and
`docs/superpowers/plans/2026-09-21-worker-run-coroutine-wrapper.md` covers
Part A's loop protocol. The rest of Part B and all of Part C run from
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`. It
holds the owner questions, one disposition per finding, and the tasks. Its
control-plane and frontend clusters get follow-on plans once the rulings
are in. This file carries the scope, the intended outcome, the work
packages and their acceptance criteria.

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
normalized `(artist, album)` keys and has no Last.fm dependency. WP-2
produces the pre-threshold album mapping consumed by
`partition_albums_by_threshold`; WP-3 partitions it and hands eligible
albums to the existing machinery.

**Owner rulings, 2026-09-23.** WP-0 prepares the repository for a large
structural feature. It has three parts. Part A is the behaviour-neutral
extractions. Part B reconciles what earlier batches left open. Part C
clears every finding open at P0 or P1, unless the owner rules one out. WP-0's
commits log untagged; one tagged entry closes it. Part C may change
behaviour and edit a test, but only where the finding it fixes requires it.
Part A may not. The reason for each ruling is in WP-0.

**Owner rulings, 2026-09-21.** The branch is `feat/batch23-wp0-hygiene`.
Job admission is folded into WP-4 as one module for all three routes. Under
a finite plan WP-0 counts as the next work package. No worker-count guard is
added: the Dockerfile pins one worker and a partial guard would be its own
wrong green.

**Owner rulings, 2026-09-13.** No Spotify login: it would buy rankings with
no play counts, the last 50 plays, and at most five allowlisted users, and it
was rejected. The entry point stays `/`, with a per-form source switch rather
than a landing page or a third mode tab. Both modes work from either source.
The upload is processed and discarded under the Data handling contract
below, which distinguishes listening history from reusable catalog metadata.
A play counts when `ms_played >= 30000`, is music rather than a podcast or
audiobook, and is not from a private session.

---

## Intended outcome

Batch 23 is complete only when all of these product outcomes hold:

- A Spotify listener can upload their export and get the same album rankings
  and heatmap a Last.fm user gets, with no account and no login.
- The upload and derived listening facts obey the Data handling contract
  below, including disposal, cache restrictions and safe diagnostics.
- Request and zip-directory failures are rejected before a job is created.
  Failures discovered only while reading content terminate the created job
  with a classified error and cleanup; neither path reports success.
- Existing Last.fm request validation, counting, filtering, ranking and
  upload-limit behaviour remains compatible, except for the approved WP-0
  Part C fixes. The shared admission refactor and WP-6's additive statistics,
  aggregation fields and presentation are permitted. Existing Last.fm tests
  remain unmodified except for the documented Part C fixes; new tests cover
  the additions.
- Both sources gain the same new statistics, computed from data the pipeline
  already holds, with no additional API calls.
- The interface reads correctly for both sources: "plays" rather than
  "scrobbles" where the source is an export, and no field that asks a Spotify
  user for a Last.fm username.

## Data handling

This section owns the batch's privacy and persistence contract. The export
outline, specialized WP plans and user-facing copy must follow it.

- The uploaded archive, raw rows and listener-linked facts (play counts,
  listening timestamps, durations actually played and derived aggregates)
  stay in server memory. Do not write them to server disk, a database or
  logs. User-requested CSV/JPEG downloads remain allowed without retained
  server copies. Discard the buffer after parsing or rejection. Parsed
  aggregates and results expire
  under the two-hour job retention policy; polling must not renew it.
- Drop IP address, user agent, username, country and other identifying
  export fields at parse time. Do not retain them in native play records.
- Existing enrichment may query providers using artist and album names and
  cache provider-returned catalog metadata or original-release findings
  under normalized artist/album keys. These shared cache rows must contain
  no listening facts and no link to a listener, upload, session or job.
  This permission does not extend to caching the listener's history.
- Logs may contain error codes and aggregate operational counters, but not
  upload names, row contents, identifying fields, or artist/album/track
  values taken from the upload. Shared enrichment logging and exception
  paths must respect this too; logging an exception must not dump input.
- WP-3/WP-4 verification must exercise the full export-to-enrichment path
  and inspect disk writes, persistence arguments and captured logs. Prove
  both the prohibited-data exclusions and the permitted catalog-cache use.

## Runtime model

1. The form posts a zip and a mode. The upload is size-capped on the request
   class, because CSRF parses the multipart body before any view runs.
2. The route reads only the zip *directory* synchronously -- entry count,
   compression ratio, declared sizes, which entries are audio history -- so
   directory-detectable failures are refused as JSON without starting a job.
3. A job slot is taken, a job is created with `source: "spotify_export"` and
   no username, and a background thread parses the buffer.
4. Parsing streams: a 64 KB chunked incremental decoder feeds
   `JSONDecoder.raw_decode`, counting bytes actually read, so a zip header
   that lies still trips the bomb guard. No entry is ever loaded whole.
   Malformed JSON, corrupt entry data and actual-byte limit violations
   fail this background job; directory inspection cannot prove them absent.
5. Album aggregation produces the pre-threshold mapping specified in WP-2.
   WP-3 applies the existing threshold partition once, then enrichment,
   filtering and results build.
6. The heatmap path mirrors this, anchored at the last play rather than
   today, because an export can lag by up to 30 days.

---

## Work packages

### WP-0 -- Foundation: extractions, reconciliation and findings

**Amended 2026-09-23 by the owner.** WP-0 was first scoped as the
behaviour-neutral extractions alone. The export feature is a large
structural change, and it should start on a clean repository: no stale
record, no open P0 or P1 defect, and no green gate hiding a red. So WP-0 now
has three parts, each with its own acceptance. A commit never mixes parts, so
Part A's parity guarantee stays checkable.

**Logging (owner ruling, 2026-09-23).** Every WP-0 commit logs an
**untagged** PLAYBOOK Section 4 entry directly after the current-batch end
marker. docsync reads a work package as complete on its first tagged
heading, so a tagged entry for work still in progress would name WP-1 as
next. When all three parts are done, one tagged `(Batch 23 WP-0)` entry
records that WP-0 is complete. WP-1 onward log tagged entries as usual.

#### Part A -- Behaviour-neutral extractions

The export path needs three pieces of the Last.fm path that are currently
inline, and the heatmap's zero-fill. Extracting them first keeps the
behaviour change and the structural change in separate commits, as Batch 22
WP-0 did.

- [x] **The shared loop protocol**, done 2026-09-23 as `ad2d078` through
  `54ab72b` (`docs/superpowers/plans/2026-09-21-worker-run-coroutine-wrapper.md`).
  `worker.run_coroutine_in_new_loop` sits beside
  `worker.new_thread_event_loop` and builds on it. Both entry points each make
  one call to it, differing only in the failure reaction they inject. Six new
  tests; the suite went from 1729 to 1735 passed, and no existing test
  changed. Deviations from the definition as first written:
  - It landed in `worker.py`, not in `orchestrator/` as
    `_run_coroutine_in_new_loop`, so the heatmap path shares it.
  - `release_checks` keeps its own long-lived loop, because a one-shot
    wrapper is the wrong shape for a queue drained for the process's lifetime.
  - Its entries are untagged (logging ruling above).
  The plan's Outcome section records the rest.
- [x] Extract `_cap_threshold_exclusions` and `_process_filtered_albums` (the
  tail of `_fetch_and_process`, from `_apply_pre_slice` to `set_job_results`)
  in `orchestrator/`, done 2026-09-23.
- [x] Extract `_zero_fill_daily_counts` from `scrobblescope/heatmap.py` so
  both aggregators share one zero-fill, done 2026-09-23.
- [x] Move `_matches_release_criteria` into `scrobblescope/domain.py`, so the
  album filter and the release-check worker both import it at module level
  and the worker's function-local import goes. Added by the owner on
  2026-09-23 from the 2026-09-21 architecture review's third card; the
  foundation plan's Task 12. Done 2026-09-23.
- **Acceptance:** every existing test passes **unmodified**, including
  `tests/services/test_orchestrator_fetch_and_process.py`. No behaviour
  change ships in Part A.

#### Part B -- Reconcile what earlier batches left open

- [x] **Stale finding records.** F-B20-3, F-B21-10, F-B21-26, F-B21-27,
  F-B21-28 and F-B21-29 still said "resolved locally, pending deploy", but
  `main` has deployed since (PR #238, 2026-09-21). For each one:
  - if its fix is an ancestor of `origin/main`, close it with a canonical
    `resolved` record and a completion date;
  - if the fix is not there, reopen it and say what is missing.
  Done 2026-09-23: all six fix commits are ancestors of `origin/main`; each
  now carries a canonical `resolved` record and completion date in
  `docs/history/findings/FINDINGS_ARCHIVE.md`.
- [x] **The foundation plan's between-batch tasks** land here: Tasks 4-10 of
  `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`. They cover
  the archive page target, the DOC range, findings hygiene (pre-split line
  citations, and the defects the 2026-09-21 probe found), the close-out
  plan's Progress block, the frontend gate's check manifest, the `AGENTS.md`
  pointers and the diagram re-verification. That plan's live-probe standard
  still applies. Done 2026-09-24; each task's completion is recorded in
  PLAYBOOK Section 3 and the plan.
- [x] **Root cleanup.** Move PLAYBOOK.md, FINDINGS.md, AGENT_NOTES.md and
  HANDOFF_PROMPT.md to `docs/agents/`, and `.docsync.toml` and `frontend_gate_checks.toml`
  to `config/`, per the owner rulings of 2026-09-24. Plan:
  `docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`. `AGENTS.md`, `README.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `LICENSE`, `DEVELOPMENT.md`, `DEPLOY.md`,
  `DESIGN.md`, `PRODUCT.md`, `BATCH*_DEFINITION.md`, `fly.toml`, `Dockerfile`, `app.py`,
  `run.py`, `init_db.py`, and the standard Python config files stay at the root.
  Done 2026-09-24, with the 2026-09-25 declared-path review fix recorded as
  F-DOCSYNC-21.
- [ ] **PLAYBOOK Section 3 states only the current work order.** Its Batch
  21 narrative is no longer the work order. Delete each paragraph only after
  confirming a log, a definition or a finding already holds its facts. A fact
  held nowhere else moves there first.
- [x] **Owed from Batch 22, owner actions:** a live run with
  `MUSICBRAINZ_CONTACT` set, and restoring the Spotify credentials that were
  disabled to test the Deezer fallback. An agent cannot do either. WP-0
  records the outcome of each, or the owner's deferral. Both are done,
  recorded 2026-09-23 in PLAYBOOK Section 3; the reconcile plan's Q0 answer
  holds the evidence.
- [x] **File the docsync gap this amendment exposed.** A work package cannot
  be marked "in progress": it reads as complete on its first tagged entry.
  Filed at P1, it joins Part C's set. Done 2026-09-23, as F-DOCSYNC-15.
- The Batch 21 frontend and accessibility audit stays in WP-7, by the
  2026-09-13 ruling. Part B does not move it.
- **Acceptance:**
  - No open finding says "pending deploy".
  - Each foundation plan task meets that plan's acceptance, with its
    live-probe table where the plan asks for one.
  - Every task in the root-cleanup plan meets that plan's acceptance, with its live-probe
    table where the plan asks for one.
  - Section 3 describes only current work.
  - Each Batch 22 owner item has a recorded outcome or deferral.

#### Part C -- Clear every open P0 and P1 finding

The set is every finding open at P0 or P1 in `docs/agents/FINDINGS.md` on 2026-09-23,
plus the docsync gap Part B files (F-DOCSYNC-15). That is 38 IDs plus one,
listed so that a finding filed later does not silently join, and a listed one
does not silently leave:

- **P0 (4):** F-B21-26, F-B21-27, F-B21-28, F-B21-29.
- **P1 (34):** F-B18-11, F-B20-3, F-B21-3, F-B21-4, F-B21-6, F-B21-9,
  F-B21-10, F-B21-14, F-B21-15, F-B21-18, F-B21-19, F-B21-20, F-B21-22,
  F-B21-23, F-B21-24, F-B21-25, F-B21-48, F-B21-53, F-B21-60, F-DOCSYNC-6,
  F-DOCSYNC-7, F-DOCSYNC-11, F-DOCSYNC-12, F-DOCSYNC-13, F-LOAD-1, F-LOAD-2,
  F-MAS-1, F-MAS-2, F-MAS-3, F-STYLE-1, F-STYLE-2, F-SWE-5, F-WORKTREE-3,
  F-WORKTREE-4.

A finding leaves the set in one of three ways, and only these:

1. **Fixed.** It carries a canonical resolved record with a completion date
   (`docs/agents/issue-tracker.md`).
2. **Confirmed already fixed.** Part B closes a stale record with evidence.
   That counts here.
3. **Ruled out by the owner.** The ruling and its date go into the finding,
   and the finding is recorded as `no action` or re-graded to P2.

Rules for the work:

- **Owner rulings are asked once, in one batch.** Some findings name an owner
  decision in their Status line. The plan collects all of those questions
  before its first task.
- **Dependencies still need approval.** A fix that needs a new or changed
  dependency still needs the owner's approval first (`AGENTS.md` "Environment
  Setup").
- **Part C may change behaviour.** It may edit an existing test only where
  the finding it fixes requires it. Each fix is its own commit, never mixed
  with Part A, and its commit body names every assertion it changed.
- **F-SWE-5 lands before WP-3.** WP-3's export tasks publish job errors
  through the same terminal states.

Two P2 findings sit under this batch's own code and are not in the set: the
owner ruled the set at P0 and P1. The plan asks the owner about both:

- **F-SWE-6:** reading a job renews its expiry, which contradicts this
  batch's promise that the parsed aggregate expires with the two-hour job TTL.
- **F-B22-7:** the provider adapter is bypassed on the live path. The
  foundation plan's Definition of Done wants it fixed ahead of WP-3.

The owner added both to the set on 2026-09-23 (Q1 and Q2), and added a third
P2 the same day:

- **F-B22-8:** release checks skip the whole job when the cache DB is down.
  Checks are to run without the cache, skipping only persistence. It affects
  local development only, since the Fly.io database wakes with the app.

Later the same day the owner added a fourth P2:

- **F-B23-5:** the release-window rule is written twice, once for the album
  filter and once for the correction worker. It gets one owner in
  `domain.py`.

On 2026-09-24 the owner added a fifth P2:

- **F-B23-6:** provider calls leave no trace in the log. Every provider call
  is to log its status in one format, with no query string, and the release
  worker is to log its start, finish and skip.

- **Acceptance:**
  - Each ID in the set is checked, member by member, and has left it in one of
    the three ways.
  - The full test suite, the frontend gate, pre-commit and
    `doc_state_sync.py --check` pass on the final tree.
  - Every edited existing test is named in its commit body.

**WP-0 acceptance:** Parts A, B and C each meet their own acceptance. Then
one tagged `(Batch 23 WP-0)` Section 4 entry records WP-0 complete.

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
- [ ] `aggregate_albums` produces an unpartitioned album mapping keyed by
  `normalize_name`, with `play_count`, `track_counts`, `original_artist`
  and `original_album`, plus aggregation stats. It does not reproduce
  `fetch_top_albums_async`'s full return tuple of eligible albums,
  exclusions and fetch metadata. WP-3 owns threshold partitioning and its
  post-partition counters. The specialized plans pin this hand-off and
  keep source-specific row/skip counters distinct from accepted play counts.
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
- [ ] A `BoundedSemaphore(2)` limits concurrent parses. Whole-process memory
  acceptance is specified under Batch acceptance.
- [ ] **The upload has one owner at every moment** (owner ruling,
  2026-09-23). The task receives the request's own buffer, never a copy,
  owns it from a successful thread start on, and closes it on every path.
  The export plan's "Upload ownership and the waiting bound" section holds
  the rule.
- **Acceptance:** `process_albums` receives the aggregate;
  `fetch_all_recent_tracks_async` is never called, proven by patching it to
  raise; an error reaches the job; the buffer is closed on every path,
  parser failure and success included; the object the task closes is the
  one the request created. A delayed task must still read that buffer after
  the response finishes and request teardown runs. The WP-3/WP-4 plans
  specify how successful hand-off removes request-side cleanup ownership,
  and how failure leaves cleanup with the route.

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
- [ ] One admission module owns starting a job: it takes the job slot,
  creates the job state and starts the thread, and on a failed start
  restores the slot and removes the orphaned job. The album, heatmap and
  export routes all call it; each route keeps its own request parsing,
  session and HTTP response. The export route is the third caller, which is
  what makes the extraction worth doing here (owner ruling, 2026-09-21).
- [ ] **Bound export jobs waiting to parse** (owner ruling, 2026-09-23). The
  parse semaphore limits running parses, not buffers waiting for a permit.
  So admission caps export jobs in flight at `EXPORT_MAX_IN_FLIGHT`, sized
  from the batch's memory measurement, and refuses the next export upload
  with 429. Last.fm jobs do not count against it. The route closes the
  buffer on every refusal.
- **Acceptance:** a multipart success; a 413 on this endpoint while a large
  Last.fm POST is unaffected; CSRF answered as JSON; each synchronous error
  code; the thread started with the expected arguments; and a test proving
  the stream is `BytesIO` and never `SpooledTemporaryFile`. For admission:
  a failed thread start leaves no slot held and no orphaned job, tested for
  each of the three routes. For the waiting bound: with
  `EXPORT_MAX_IN_FLIGHT` export jobs in flight, the next export upload gets
  429 and creates no job while a Last.fm job is still admitted when the
  shared job limit has spare capacity. The buffer is closed after every
  refusal. Memory acceptance includes receiving and rejected requests,
  not only jobs counted by the export admission limit (Batch acceptance).

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

**Decision point before WP-6's detailed design (owner, 2026-09-23).**
F-B23-1 proposes that the album calculation return its whole answer --
rows, exclusions and the new statistics -- instead of writing exclusions
into the job as a side effect. That is where WP-6's per-album statistics
would live. Settle it after WP-0's provider repairs and before this work
package is designed. Scheduling it inside Batch 23 needs an explicit scope
amendment, and a migration that keeps the Last.fm path's tests unmodified.

**Statistics contract before implementation.** The specialized plan names
which population each summary covers (all accepted plays, eligible albums
or displayed rows), its duration basis, missing-data policy and tie rules.
It also defines current-streak behaviour relative to each source's window.
Labels and CSV values must agree with those choices. Preserve timestamps,
original track names and any bounded intermediate counts needed for the
statistics before aggregation discards them; do not retain raw history or
silently change existing ranking and percentage semantics.

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
- The Data handling contract passes end-to-end checks, including the shared
  enrichment path and failure logging.
- Request/directory failures create no job. Content failures found during
  parsing terminate the job with the classified error, release capacity
  and discard the buffer. Both paths give an actionable message.
- The Last.fm path's tests pass unmodified throughout the batch. The one
  exception is an assertion that a WP-0 Part C finding fix must change; that
  commit's body names it (owner ruling, 2026-09-23).
- Peak memory is measured, not assumed: `tracemalloc` and process peak RSS
  (VmHWM on Fly/Linux) on the real export, locally and on Fly. Include the
  receiving multipart requests, admitted/waiting buffers, parser working
  data, retained job aggregates/results and normal enrichment workload.
  Tune the request cap, `EXPORT_MAX_IN_FLIGHT` and parse semaphore together
  before WP-4 acceptance, and repeat with three concurrent upload attempts
  at batch close-out. Excess attempts may receive the specified 429; no
  attempt may cause an OOM. An admitted-buffer bound is not a whole-process
  memory bound.
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
- Persisting or caching uploaded history or listener-linked derived facts.
  The Data handling section owns the permitted shared catalog-cache use.

## Constraints

- **Memory is the binding constraint.** The Fly machine is shared-cpu-2x with
  512 MB and gunicorn runs one worker with four threads. Size the request,
  admission and parsing limits using the whole-process Batch acceptance
  measurement; streaming alone does not establish the memory bound.
- **Never create a new Spotify Client ID.** A new one loses the postponement
  F-B21-59 records, and this source raises traffic through the same
  enrichment path.
- Werkzeug spools uploads over 500 KB to a temporary file by default, which
  breaks the never-on-disk guarantee; the request class is where that is
  overridden.
- Standard library only for the new parsing code; no new dependency.
