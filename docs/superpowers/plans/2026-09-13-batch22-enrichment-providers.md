# Batch 22 (queued): Enrichment providers and original release years

> **For Claude:** REQUIRED SUB-SKILL: use superpowers:executing-plans to
> implement this plan task by task.

Status: approved by the owner on 2026-09-13. Batch opened as
`BATCH22_DEFINITION.md` (repo root); branch `feat/batch22-enrichment`. Batch
23 is the Spotify export import
(`docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md`), which
builds on the work here.

## Progress

Executed task by task via `superpowers:executing-plans`. Full detail per task
lives in PLAYBOOK Section 4; this section tracks status only.

- **Task 1 (AlbumMetadata value object): done, 2026-09-13.**
  `scrobblescope/enrichment.py`, `tests/services/test_enrichment.py`.
  1037 passed.
- **Task 2 (cache columns for any provider): done, 2026-09-13.**
  `init_db.py`, `scrobblescope/cache.py`, `scrobblescope/config.py`,
  `tests/test_cache_schema.py`, `tests/services/test_cache.py`. 1049
  passed. `_batch_persist_metadata`'s row tuple grew to up to 9 elements
  with the last 3 optional (defaults keep today's 6-element caller
  behaviour-identical); full reasoning in PLAYBOOK's 2026-09-13 Section 4
  entry for this task. Owner-verified against real Postgres (Docker
  `ss-postgres`) on localhost: no regressions.
- **Task 3 (Spotify calls behind `spotify.enrich_albums`): done, 2026-09-13.**
  `scrobblescope/spotify.py` (new `enrich_albums`), `scrobblescope/orchestrator/__init__.py`
  (facade import only -- the real pipeline path is untouched, per Task 5),
  `tests/services/test_spotify_service.py`, `tests/services/test_orchestrator_fetch_spotify.py`.
  1054 passed; frontend gate 28/28. Folded in a real type fix caught by the
  owner's editor: `AlbumMetadata.image_url` (Task 1) was typed `str` but
  should be `str | None` -- an album can have no cover art. **Phase 1
  complete.**
- **Task 4 (Deezer client): done, 2026-09-13.** `scrobblescope/deezer.py`
  (new), `scrobblescope/utils.py` (`get_deezer_limiter`),
  `scrobblescope/config.py` (`DEEZER_REQUESTS_PER_SECOND`,
  `DEEZER_SEARCH_RETRIES`, `DEEZER_DETAIL_RETRIES`),
  `tests/services/test_deezer_service.py` (7 tests). 1061 passed. Not
  wired into any caller yet.
- Tasks 5-11 (Phase 2 cont'd, Phase 3), Phase 4: not started. Next: Task 5,
  wire the Deezer fallback into the orchestrator.

**Goal:** album enrichment no longer depends on one API, and a release filter
uses an album's original release year rather than a reissue year.

**Architecture:** album metadata moves behind a small provider contract.
Spotify stays first; Deezer answers when Spotify cannot. A separate
MusicBrainz step corrects release years. It is slow by rule (1 request per
second), so results render first and the page shows corrections as they land.

**Tech stack:** Python 3.13, aiohttp, aiolimiter, asyncpg, Flask, vanilla JS.
No new dependency.

---

## Context

- **Spotify is a single point of failure.** The app is a Development Mode app.
  Spotify removed Get Several Albums for Development Mode in February 2026 and
  postponed the removal for existing apps with no new date (FINDINGS
  F-B21-59). The batch call already falls back to single-album calls, but
  every album still depends on one provider's exemption.
- **Release years are wrong for reissues.** Spotify and Deezer both date a
  remaster by its reissue. Deezer dates The Beatles' White Album 2015-12-24.
  MusicBrainz's release group carries `first-release-date`, the original:
  *Rumours* returns 1977-02-04. The year filters mean the original year, so
  today they silently drop reissued albums and keep remasters in the wrong
  year.
- **Owner rulings, 2026-09-13:**
  - Deezer is a fallback behind Spotify, not a replacement.
  - Release-year correction runs with progressive disclosure: results render
    at once, checks land live, a corrected row stays in place with a marker,
    and the list only re-sorts on reload.
  - This batch comes before the Spotify export import.

## Verified facts (probes and code, 2026-09-13)

- **Deezer** needs no key. Plain search works; the filtered form does not:
  `q=artist:"Fleetwood Mac" album:"Rumours"` returns a tribute single first,
  while `q=Fleetwood Mac Rumours` returns the real album first. Matching must
  therefore compare normalised artist and title.
- **Deezer `/album/{id}` lists at most 25 tracks** (the White Album reports
  `nb_tracks` 30 and lists 25). Track lengths come from
  `/album/{id}/tracks?limit=500`, whose items carry `duration` in seconds.
- **Deezer reports errors with HTTP 200** and a body of
  `{"error": {"type": ..., "message": ..., "code": N}}`; 800 is "no data", 4
  is the quota error. Rate limit: 50 requests per 5 seconds.
- **MusicBrainz** allows 1 request per second per IP, requires a User-Agent
  with contact details, and answers 503 above the limit. A release-group
  search returns `id`, `title`, `score`, `first-release-date` and
  `artist-credit` in one call.
- **The cache table is created only by `init_db.py`**, run as the Fly
  `release_command`. There is no migrations directory, and
  `CREATE TABLE IF NOT EXISTS` never alters an existing table, so new columns
  need explicit `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. `spotify_id` is
  `NOT NULL` today, which a Deezer-only row cannot satisfy.
- **No JSON endpoint returns a job's album results**, so the live update needs
  a new one. `repositories.py` has no helper that updates a single result.
- `_matches_release_criteria` takes the year from `release_date.split("-")[0]`,
  so "YYYY", "YYYY-MM" and "YYYY-MM-DD" all work.

---

## Phase 1: The provider contract (no behaviour change)

### Task 1: Album metadata value object

**Files:**
- Create: `scrobblescope/enrichment.py`
- Test: `tests/services/test_enrichment.py`

**Step 1: Write the failing test**

```python
from scrobblescope.enrichment import AlbumMetadata


def test_album_metadata_carries_its_provider_and_url():
    meta = AlbumMetadata(
        provider="deezer",
        album_id="6237061",
        url="https://www.deezer.com/album/6237061",
        release_date="1977-02-04",
        image_url="https://cdn.example/cover.jpg",
        track_durations={"dreams": 260},
    )
    assert meta.provider == "deezer"
    assert meta.as_cache_row_fields() == (
        "deezer",
        "6237061",
        "https://www.deezer.com/album/6237061",
        "1977-02-04",
        "https://cdn.example/cover.jpg",
        {"dreams": 260},
    )
```

**Step 2:** `pytest tests/services/test_enrichment.py -v` — expect
`ModuleNotFoundError`.

**Step 3:** implement `AlbumMetadata` as a frozen dataclass with those fields
and `as_cache_row_fields()`. Document that `track_durations` holds seconds
keyed by `normalize_track_name`, the shape `_build_results` already reads.

**Step 4:** rerun — expect PASS.

**Step 5:** commit `feat(enrichment): Add the album metadata value object`.

### Task 2: Cache columns for any provider

**Files:**
- Modify: `init_db.py`, `scrobblescope/cache.py`
- Test: `tests/test_cache_schema.py` (new), `tests/services/test_cache.py` if present

**Step 1:** write a test that reads `init_db.py` and asserts every statement
needed: `ALTER TABLE spotify_cache ADD COLUMN IF NOT EXISTS provider TEXT`,
the same for `provider_album_id` and `provider_url`, and
`ALTER COLUMN spotify_id DROP NOT NULL`. Assert the new
`original_release_cache` table statement too:

```sql
CREATE TABLE IF NOT EXISTS original_release_cache (
    artist_norm       TEXT NOT NULL,
    album_norm        TEXT NOT NULL,
    mb_release_group  TEXT,
    original_release  TEXT,
    checked_at        TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (artist_norm, album_norm)
)
```

A row with a null `mb_release_group` records "checked, nothing found", so the
same album is not searched again on every job.

**Step 2:** run — expect FAIL.

**Step 3:** add the statements. Keep `spotify_id` for rows Spotify wrote, and
backfill `provider='spotify'` and `provider_album_id=spotify_id` in the same
script. This table keeps its name: renaming it needs a deploy-time copy, which
buys nothing.

**Step 4:** extend `_batch_lookup_metadata` and `_batch_persist_metadata` in
`scrobblescope/cache.py` to carry the three new columns, and add
`_batch_lookup_original_release(conn, keys)` and
`_batch_persist_original_release(conn, rows)` against the new table with their
own TTL (`ORIGINAL_RELEASE_TTL_DAYS`, default 365, in `config.py`). Original
dates do not change; the TTL only guards against a bad match.

**Step 5:** rerun the cache tests — expect PASS. Commit.

### Task 3: Move the Spotify calls behind the contract

**Files:**
- Modify: `scrobblescope/spotify.py`, `scrobblescope/orchestrator.py`
- Test: `tests/services/test_spotify_service.py`,
  `tests/services/test_orchestrator_fetch_spotify.py`

**Step 1:** write a test that `spotify.enrich_albums(session, misses, token)`
returns `{key: AlbumMetadata}` for the albums it matched, and a set of the keys
it could not match.

**Step 2:** run — expect FAIL.

**Step 3:** implement `enrich_albums` as a thin wrapper over the existing
search and detail phases. The provider modules own their own retry, limiter and
matching; the orchestrator only calls `enrich_albums`.

**Step 4:** rerun the suite. `_run_spotify_search_phase` and
`_run_spotify_batch_detail_phase` keep their tests; this task adds a seam, it
does not rewrite them.

**Step 5:** commit.

---

## Phase 2: Deezer as the fallback

### Task 4: Deezer client

**Files:**
- Create: `scrobblescope/deezer.py`
- Modify: `scrobblescope/utils.py` (add `get_deezer_limiter`, 10 requests/s,
  same `_GlobalThrottle` plus per-loop `AsyncLimiter` pattern as Spotify),
  `scrobblescope/config.py` (`DEEZER_REQUESTS_PER_SECOND`, retries)
- Test: `tests/services/test_deezer_service.py`

**Step 1: Write the failing tests.** Use `make_response_context` and
`NoopAsyncContext` from `tests/helpers.py`, as the Spotify tests do.

1. **Matching.** Given a search body whose first item is
   `{"title": "Rumours", "artist": {"name": "Grey Orton"}, "record_type": "single"}`
   and whose third is the real album, `search_deezer_album` returns the third
   album's id. The choice compares `normalize_name(artist, title)` with the
   key, so punctuation and "Deluxe Edition" suffixes behave as they do for
   Last.fm names.
2. **No match.** With no candidate matching the key, it returns None. It never
   returns "the first result" as a guess.
3. **Errors arrive as HTTP 200.** A body of `{"error": {"code": 800}}` returns
   None. A body of `{"error": {"code": 4}}` (quota) retries after a wait and
   then succeeds.
4. **Track lengths come from the tracks endpoint.** `fetch_deezer_album`
   requests `/album/{id}` and `/album/{id}/tracks?limit=500`, and returns an
   `AlbumMetadata` whose `track_durations` holds every track, not the 25 the
   album endpoint lists. Pin this with a 30-track fixture.

**Step 2:** run — expect FAIL.

**Step 3:** implement. The search query is the plain `f"{artist} {album}"`, no
`artist:` or `album:` fields. `AlbumMetadata` gets `provider="deezer"`,
`url=album["link"]`, `image_url=album["cover_xl"]`, and durations keyed by
`normalize_track_name`.

**Step 4:** rerun — expect PASS. **Step 5:** commit.

### Task 5: Wire the fallback into the orchestrator

**Files:**
- Modify: `scrobblescope/orchestrator.py`, `scrobblescope/unmatched.py`
- Test: `tests/services/test_orchestrator_process_albums.py`

**Step 1: Write the failing tests.**

1. Spotify matches every album: Deezer is never called (patch it to raise).
2. Spotify misses two albums: Deezer is asked for exactly those two, and a
   Deezer match lands in the results with `provider == "deezer"` and a Deezer
   `album_url`.
3. Neither provider matches: one unmatched entry per album, with
   `reason_code == "no_spotify_match"` (the stored code stays, so old jobs and
   the unmatched page keep working) and the reason text "No match on Spotify
   or Deezer".
4. Spotify has no token and the cache is empty: Deezer enriches everything and
   the job succeeds. `SpotifyUnavailableError` is raised only when Deezer also
   fails.
5. The cache row for a Deezer album round-trips: `provider`,
   `provider_album_id` and `provider_url` are persisted and read back.

**Step 2:** run — expect FAIL.

**Step 3:** implement. Keep the phase order: Spotify search, Spotify details,
then one Deezer pass over what is left, then the unmatched writes.
`_detect_spotify_total_failure` becomes `_detect_enrichment_total_failure`
and fires only when both providers came back empty.

**Step 4:** rerun — expect PASS. **Step 5:** commit.

### Task 6: Show the album's own provider

**Files:**
- Modify: `templates/results.html`, `templates/unmatched.html`,
  `static/js/results.js`, `scrobblescope/orchestrator.py` (`_build_results`)
- Test: `tests/test_routes.py`, `scripts/dev/frontend_gate.py`

Each result gains `provider` and `album_url`. Links use `album_url` instead of
building a Spotify URL from `spotify_id`, which stays for old jobs. The CSV
export gains a provider column. The frontend gate checks that a Deezer-sourced
row links to deezer.com and a Spotify-sourced row to open.spotify.com.

**Attribution is a blocker for this task:** read
https://developers.deezer.com/guidelines before shipping, and record what it
requires next to the artwork and the link. FINDINGS F-B21-60 already owns the
same question for Spotify.

---

## Phase 3: Original release years

### Task 7: MusicBrainz client

**Files:**
- Create: `scrobblescope/musicbrainz.py`
- Modify: `scrobblescope/utils.py` (`get_musicbrainz_limiter`, 1 request/s
  process-wide), `scrobblescope/config.py`
  (`MUSICBRAINZ_CONTACT`, `MUSICBRAINZ_CHECKS_PER_JOB` default 60,
  `MUSICBRAINZ_ENABLED` default True)
- Test: `tests/services/test_musicbrainz_service.py`

**Step 1: Write the failing tests.**

1. **Query building.** `_build_release_group_query("Fleetwood Mac", "Rumours")`
   produces `releasegroup:"Rumours" AND artist:"Fleetwood Mac"`, and a title
   holding a quote or a Lucene operator is escaped rather than passed through.
2. **Match rules.** A candidate is accepted only when its `score` is at least
   90 **and** its normalised title and artist credit match the key. A
   high-scoring wrong artist is rejected.
3. **Return shape.** `lookup_original_release` returns
   `(mb_release_group_id, "1977-02-04")`, or `(None, None)` when nothing
   matches. Both outcomes are cacheable.
4. **Rate limit.** A 503 waits and retries; the limiter is asked for every
   call.
5. **User-Agent.** Every request carries
   `ScrobbleScope/<version> ( <MUSICBRAINZ_CONTACT> )`. With no contact
   configured, the client is disabled and returns `(None, None)` without a
   request: MusicBrainz blocks anonymous clients.

**Step 2:** run — expect FAIL. **Step 3:** implement. **Step 4:** rerun.
**Step 5:** commit.

### Task 8: Apply cached corrections before results render

**Files:**
- Modify: `scrobblescope/orchestrator.py` (`process_albums`, `_build_results`)
- Test: `tests/services/test_orchestrator_helpers.py`

A correction already in `original_release_cache` costs nothing, so it applies
during the normal run: `_build_results` uses the original date for
`_matches_release_criteria` and for display, and keeps the provider date in
`provider_release_date`. Tests:

1. A cached original of 1977 against a provider date of 2011, with the "2011"
   filter, sends the album to the unmatched page with the reason "First
   released in 1977, not 2011".
2. The same pairing with the "1977" filter keeps the album in the results and
   displays 1977.
3. With no cached original, behaviour is exactly as today.

### Task 9: The correction worker

**Files:**
- Create: `scrobblescope/release_checks.py`
- Modify: `scrobblescope/orchestrator.py` (start the worker after
  `set_job_results`), `scrobblescope/repositories.py` (add
  `update_job_result(job_id, album_key, fields)` and
  `set_job_release_check(job_id, state)` under `jobs_lock`)
- Test: `tests/services/test_release_checks.py`, `tests/test_repositories.py`

**Design:**
- One worker thread for the whole process, with its own event loop and a FIFO
  queue of job ids. MusicBrainz allows 1 request/s per IP, so more threads
  would only queue behind the limiter.
- Candidates per job, capped at `MUSICBRAINZ_CHECKS_PER_JOB`, and skipping
  anything already cached:
  1. results, in rank order (a correction can move one out);
  2. albums the release filter excluded whose provider year is **later** than
     the target window (a correction can move one in). An original date is
     never later than the provider's, so nothing else can change.
- Each result gains `release_check`: `unchecked`, `confirmed`, `moved_out`, or
  `unavailable`. Moved-in albums are counted, not inserted.
- The job's `progress.stats.release_check` holds
  `{status, checked, total, moved_out, moved_in}`, with `status` one of
  `running`, `done`, `skipped`.
- Every finding is written to `original_release_cache`, including "nothing
  found", so later jobs skip it.
- The worker stops early when the job is gone (`JOB_TTL_SECONDS`, 2 hours).

**Tests:** the candidate list and its order; the cap; the cache short-circuit;
`moved_out` marking the result without removing it from the list; the stats
shape; a job deleted mid-run stopping the worker; and a
`MUSICBRAINZ_ENABLED=False` run marking the status `skipped` and making no
request.

### Task 10: The results JSON endpoint

**Files:**
- Modify: `scrobblescope/routes.py`
- Test: `tests/test_routes.py`

`GET /api/release_checks?job_id=` returns
`{"status": ..., "checked": n, "total": n, "moved_in": n,
"albums": [{"key": "artist|album", "original_release_date": "1977-02-04",
"state": "moved_out"}]}`. It reuses `_get_validated_job_context` for ownership
and mode checks, returns 404 for an unknown job, and lists only albums whose
state has changed from `unchecked`.

### Task 11: Live disclosure on the results page

**Files:**
- Modify: `templates/results.html` (a `data-album-key` attribute per row and a
  status line under the table header), `static/js/results.js` (or a new
  `static/js/results-release-checks.js`, matching the spotlight split),
  `static/css/results.css`
- Test: `scripts/dev/frontend_gate.py`, `tests/test_template_shell.py`

**Behaviour (owner ruling):**
- A quiet status line reads "Checking original release years: 14 of 60". It
  disappears when the status is `done` with nothing to report.
- Polling every 2 seconds while `status` is `running`, paused while the tab is
  hidden, and stopped on `done`, on `skipped`, or after a failed request.
- A `moved_out` row stays in place, muted, showing the original year and a
  note: "First released 1977", with a link to its entry on the unmatched page.
- Rows never move or re-sort while the page is open. Moved-in albums show one
  line: "2 albums first released in 2025 were found. Reload to include them."
- Reduced motion changes nothing here; there is no animation to suppress.

**Gate checks:** every row's top stays where it was after a marker is applied
(no layout shift); the status line renders at 390px and 1280px without
overflow; the muted row keeps a contrast ratio above the design system's floor;
polling stops once the status is `done`.

---

## Phase 4: Documentation and renumbering

- Rename the export plan to
  `docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md` and
  update every reference to it (PLAYBOOK Section 3, FINDINGS F-B21-59 and
  F-B21-60).
- Record in `docs/design/RECONCILIATION.md` that a release year shown next to
  an album may now come from MusicBrainz rather than the provider.
- A PLAYBOOK Section 4 entry per phase, following the existing format.
- `README.md`: the new environment variables, and that MusicBrainz needs a
  contact address.

## Verification

1. `pytest -q`, `python scripts/doc_state_sync.py --check`, pre-commit, and the
   two-engine frontend gate.
2. **Provider fallback, seen to work:** run a job with
   `SPOTIFY_CLIENT_ID` set to an invalid value. Every album must still get a
   release date and cover art through Deezer, and the results page must link to
   deezer.com.
3. **Correction, seen to work:** search a year in which a well-known reissue
   charts (for example a 2011 remaster of a 1977 album). Confirm the row is
   marked during the live pass and is absent after a reload, and that the
   unmatched page explains why.
4. **Rate limits:** log MusicBrainz request timestamps for one job and confirm
   at least 1 second between calls and no 503. Confirm Deezer stays under 50
   requests per 5 seconds.
5. **Cache:** run `init_db.py` against a copy of the production schema, then
   confirm that Deezer rows persist and reload, and that a second search of the
   same albums makes no provider call.
6. **Deploy:** `init_db.py` runs as the Fly release command, so the schema
   change ships with the deploy. Confirm on staging before production.

## Risks

- **MusicBrainz matching.** A wrong match dates an album wrongly, which is
  worse than no correction. The score floor plus the normalised comparison is
  the guard, and every accepted match stores its release-group id so a bad one
  can be traced.
- **Deezer terms are non-commercial.** This is fine while the app is free and
  carries no advertising. Record that constraint in the README; it binds any
  future change.
- **Correction latency.** At 1 request per second a 60-album pass takes about a
  minute, and most readers will have left. That is why findings go to the
  cache: the second visitor to the same album pays nothing.
- **Two providers, two sets of brand rules.** F-B21-60 covers Spotify;
  Task 6 must not ship before Deezer's rules are read and recorded.
