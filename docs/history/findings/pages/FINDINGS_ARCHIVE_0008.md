<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0008

### F-DOCSYNC-16: docsync silently ignores an `allow_after` marker that matches no line -- RESOLVED

`check_retired` (`scripts/docsync/declarations.py`) compares a raw file line
against a declared `allow_after` marker with `line.strip() == marker.strip()`
-- exact equality, no prefix match -- and when nothing matches, `exempt_from`
simply stays `None`: the declaration silently loses its whole history
exemption for that file, with no warning that the marker itself is dead. The
three `[[retired]]` declarations in `.docsync.toml` that predate this finding
all declared `[retired.allow_after] "PLAYBOOK.md" = "## 4. Execution log"`,
but the real `docs/agents/PLAYBOOK.md` heading is `## 4. Execution log (for agent
handoff)`, so none of the three matched anything. Reproduced directly against
`check_retired` with the real heading text: a claim placed below the heading
was still reported, not exempted (confirmed 2026-09-24, Task 5's live probe
for the new fourth declaration that task added).

**Impact was latent, not live.** No dated Section 4 entry restated
`limit_results ... thresholds disclosure`, `fonts self-hosted under
static/fonts/` or a bare `DOC001-DOC011`, so `--check` on the real corpus
never actually exercised the mismatch before it was caught. It would have
surfaced as a false-positive DOC011 the day a dated entry legitimately quoted
one of those retired phrases as history.

**The three markers are corrected in `.docsync.toml`** (2026-09-24, Task 5
fix round) to the real heading text, matching the fourth declaration that
task added, which used the correct text from the start. That corrects this
one instance; the finding stays open because the mechanism -- a declared
`allow_after` marker can silently match nothing, for any file, and nobody is
told -- is still unchecked, so the next marker written this way fails the
same way undetected.

**Fix shape, not yet built:** a declaration check that errors when an
`allow_after` marker matches no line in its named file (a new check; not
built here).

- [x] **Status:** RESOLVED
  **Completed:** 2026-10-31
  `check_retired` now reports DOC011 for an `allow_after` marker that matches no line of its
  file, naming the file and the marker; covered by
  `test_an_allow_after_marker_matching_no_line_is_reported` (a dead marker flagged, the
  matching one clean).
  Source: Batch 23 WP-0 foundation Task 5 live
  probe, 2026-09-24.

### F-B23-17: a Section 4 Validation line with no number passes --check -- RESOLVED

Two landings on 2026-09-29 committed the entry template's placeholder,
`` Validation: `pytest -q` -- **N passed**. ``, with the letter N in place of the count
(36ade83 and 95973fd; filled in by 931828d). `doc_state_sync.py --check` exited 0 on both.
DOC012 (`scripts/docsync/integrity.py`, `_check_unbolded_test_counts` and
`_unpaired_result_issue`) looks only for digits: `_EXPLICIT_CLAIM_RE`, `TEST_COUNT_RE`,
`_UNPAIRED_RESULT_RE` and `_UNBOLDED_COUNT_RE` all need one, so an entry whose only count is
a letter records nothing and raises nothing. With the count pinned in
`config/docsync.toml`, Section 4 is not re-scanned for the number, so the dashboards stay
right; what is lost is the entry's own evidence, silently. Fix: DOC012 flags a
Validation-trigger line whose bold count holds no digit.

- [x] **Status:** RESOLVED
  **Completed:** 2026-10-31
  `_check_unbolded_test_counts` now raises DOC012 for a `` `pytest -q` `` line whose bold count
  has no digit (`_PLACEHOLDER_CLAIM_RE`); covered by
  `test_doc012_flags_a_validation_count_with_no_digit` (`**N passed**` flagged, a digit count clean).
  Source: controller check of the 36ade83 and 95973fd landings
  and the Task 9 sdd-reviewer, 2026-09-29.

### F-B23-65: a job slot leaks when `jobs.create` raises during admission -- RESOLVED

`admit()` in `scrobblescope/routes/admission.py` takes a job slot with `_routes.acquire_job_slot()` (line 44) and then calls `jobs.create(params)` (line 47), outside its `try` (lines 49-54). Only a `start_job_thread` failure is caught: that path logs, deletes the job and returns `Refused.START_FAILED`, and `start_job_thread` has already released the slot (`scrobblescope/worker.py`). If `jobs.create` raises, nothing releases the slot, so the semaphore stays one short for the life of the process, and enough such failures would make the app refuse every job as at capacity until it restarts. What can raise there: `jobs.create` (`scrobblescope/jobs.py`, line 187) calls `_now()`, `uuid4()`, `_initial_progress()` and `_store.insert(...)`. With the in-memory store `insert` is a dict write under a lock, so in practice only something like `MemoryError` reaches the slot; `_store` is a protocol, though, so another store's `insert` could raise. What would close it: acquire the slot and create the job under one `try` that releases the slot on any exception, with a test that makes `jobs.create` raise and asserts the slot count is unchanged.

- [x] **Status:** RESOLVED
**Completed:** 2026-10-31
`admit()` now wraps `jobs.create` in its own `try` and releases the slot with `release_job_slot()` before re-raising, so a failed create no longer holds a slot; `tests/test_admission.py::test_a_create_failure_frees_the_slot_once_and_propagates` proves the release count is one and the same error propagates. Source: review of the Fly idle-exit plan (reviewer note), 2026-10-27.

### F-B23-37: Deezer may answer a busy service with an HTTP 200 error body that `_deezer_request` reads as a terminal miss -- RESOLVED

`scrobblescope/deezer.py` `_deezer_request` retries only error code 4 (quota) from a 200 body carrying `{"error": {"code": N}}`; every other code is a terminal miss, so the album is recorded as having no match on Deezer. The Task 18 review recalled that Deezer signals "service busy" with code 700 in such a body, which would be an outage read as "no match". UNVERIFIED: the code and its meaning come from memory and were not read at Deezer's documentation. Verify against Deezer's documented error codes before any fix; if 700 (or another code) means "try later", treat it as not-done so the retry helper raises `deezer_unavailable`, and add a test.

- [x] **Status:** resolved
**Completed:** 2026-10-31
Code 700 (SERVICE_BUSY in Deezer's documented error table, read by the owner on 2026-10-31) is now retried like an HTTP 5xx and raised as `deezer_unavailable`, on branch `fix/deezer-service-busy`. Source: Task 18 review (2026-09-30), Minor 2.

### F-B23-33: /api/artist_spotlight splices a raw artist_id into a Spotify path -- RESOLVED

`routes/api.py` passes `request.args["artist_id"]` unvalidated into `https://api.spotify.com/v1/artists/{artist_id}` (`spotify.py`), so `../` segments make the server call any GET route under the app's token, though no client sends the parameter.

- [x] **Status:** resolved
**Completed:** 2026-10-31
Source: third review of PR #245 (2026-09-29), S6-4. Resolved by the owner-directed fix on `fix/spotify-artist-id`: `_request_spotlight_artist` now takes the by-ID path only for a 22-character base-62 ID; a malformed one is ignored and the name fallback runs.

### F-OPS-1: Akamai blocked the app machine's egress address, so every Deezer call returned 403 -- RESOLVED

Every Deezer call from the production machine got HTTP 403 from Akamai, because the machine's outbound IPv4 address was blocked.

Symptom: the Results page said "Deezer could not be reached for some albums" on every production run. Fly logs on machine `807339f1595248` showed `Deezer: 51 calls over 5.0s (1.1s in calls) -- 51x403` and, after a redeploy, `Deezer: 72 calls over 7.2s (4.2s in calls) -- 72x403`. Local runs were fine.

Diagnosis: the same request from the machine got 403 from `AkamaiGHost` for any User-Agent and any client (urllib and aiohttp). From the owner's PC (AS577 Bell Canada) it got 200. The machine's egress was `185.156.47.129` (AS60068 Datacamp, Toronto). Fly's default egress is the host's address and can change. api.deezer.com has no AAAA record, so Deezer traffic is IPv4 only.

Tried: a static egress IP (`209.71.99.215`, $3.60/month) made Deezer return 200 and was released on the owner's word. A restart and a `fly deploy` did not help: the machine id, host and IP stayed the same, because a deploy updates the machine in place.

Fix applied: `fly machine clone 807339f1595248 --region yyz` made `8e762ec1ed4538` with egress `185.156.47.130` (same /24), and Deezer answered 200. The old machine was destroyed. So Akamai blocked one address, not the range. The clone kept `IDLE_EXIT_MINUTES=20`, autostop off, autostart on, restart on-failure. The fix was operational: no code change resolved the block.

Unknown: why Akamai blocked `185.156.47.129`; and why the machine was recreated at 2026-10-27T17:49:55Z, about four minutes after the first idle exit stopped the old one at 17:45:54Z.

MusicBrainz 503s the same day (`87 calls ... 60x200, 27x503`) were MusicBrainz-side: 12 requests at 1.1s spacing from the owner's PC got 4x503, from Fly 2x503, at the same moment. MusicBrainz answers a rate limit or busy state with 503, not 429 (an older convention). The client treats 429 and 503 alike (`_RATE_LIMIT_STATUS` in `scrobblescope/musicbrainz.py`) and retries.

Code changes that came with it: a Deezer 403 is now one request, raised as `deezer_unavailable`; MusicBrainz request starts are spaced 1.2s.

Recurrence risk: any move of the machine to another host changes the egress IP, and the idle exit (PR #276) makes stop and start frequent. The remedy is the `DEPLOY.md` section "Deezer blocks the machine's egress address". The finding is resolved because the incident is over; the risk is carried as a possible issue in `AGENTS.md` and `DEPLOY.md`, not as an open finding. Out of scope: a per-job Deezer circuit breaker, Spotify 403 handling, the static egress IP.

RESOLVED 2026-10-28 by an operational fix (machine clone), with code follow-ups in this PR.

- [x] **Status:** RESOLVED
- **Completed:** 2026-10-28

Source: production incident, 2026-10-28 (owner session).

### F-B18-12: mode pills differ in width (no `min-width` on `.mode-pill`) -- RESOLVED

The "Album Filtering" pill is wider than "Heatmap" due to different text
lengths and no `min-width` constraint. Owner flagged this after testing.
CSS fix: add `min-width` to `.mode-pill` in `heatmap.css` so both pills
are the same width. To be fixed in a Phase 2 WP.

RESOLVED 2026-08-25 by Batch 21 WP-3. They are equal-width `<button>`
elements in a two-column grid, which also closes the `span[role="button"]`
item in F-B21-5.

- [x] **Status:** RESOLVED
- **Completed:** 2026-08-25

Source: `FINDINGS.md` before `494f2c7` ("pill tabs mismatched in width");
the RESOLVED paragraph is the pointer bullet's own text, moved here.

### F-B23-59: Spotify album search takes the first result without checking the artist or title -- RESOLVED

`search_for_spotify_album_id` (`scrobblescope/spotify.py`) sends `limit: 3` and returns `items[0].get("id")` with no artist or title check, where `search_deezer_album` (`scrobblescope/deezer.py`) accepts a candidate only when `normalize_name` of its artist and title equals that of the request. Real cases from the owner's runs: an album Spotify lacks got another album (Xiu Xiu "A Promise" got Captain Beefheart's "Safe As Milk", 1967), and a sibling ranked higher won ("audio stars" got "audio stars 2", "Basspunk" got "Basspunk 2", bassvictim's "?" got "Forever"). The wrong track list matches no scrobble, so `aggregate_albums` totals 0 seconds and the album shows "0 secs".

Fix direction: ask for five candidates and accept one only when any credited artist and the title both equal the request under `normalize_name`; no match falls to Deezer.

- [x] **Status:** resolved
**Completed:** 2026-10-25
Resolved by `search_for_spotify_album_id` asking Spotify for five candidates and
accepting one only when the title and one credited artist both equal the
request under `normalize_name` (`matching_credit`); no match falls to Deezer.
Fixed by `2561e4cd`. A wrong match already in the cache clears on read: the
provider's own names are stored (`f546a0bf`), `AlbumCache.lookup` drops a row
naming another album as a miss (`4892ca8a`), and an older row without names is
checked once by its cached Spotify ID, kept and stamped if it fits, otherwise
a miss (`1cc4d33d`).
Source: owner's real runs, 2026-10-25

### F-B23-60: two albums that resolve to one Spotify ID overwrite each other in the search phase -- RESOLVED

`_run_spotify_search_phase` (`scrobblescope/orchestrator/_search.py`) writes `spotify_id_to_key[spotify_id] = key` and `spotify_id_to_original_data[spotify_id] = data`, so a second key with the same ID replaces the first silently and the loser falls to Deezer. It stays reachable once D1 is fixed: a collaboration album credited to [A, B] matches key (A, title) and key (B, title), so a Last.fm library that holds scrobbles under both artist names sends two keys to one ID.

Fix direction: log one warning (operation and count only) when an ID is shared, never drop a key, and build the metadata once per requesting key so each key's stored provider artist is the credit that matched it.

- [x] **Status:** resolved
**Completed:** 2026-10-25
Resolved by building the metadata once per requesting key, so two keys
sharing a Spotify ID each get their own metadata and the stored provider
artist is the credit that matched that key. Fixed by `3c2694c3`.
Source: owner's real runs, 2026-10-25

### F-B23-61: an album named "?" or "EP" normalizes to an empty key -- RESOLVED

`normalize_name` (`scrobblescope/domain.py`) replaces ASCII punctuation with spaces and strips the album edition words (including "ep") from the album only, so the albums "?" and "EP" both normalize to `""`. Matching on `""` would accept any other empty-normalizing title by that artist, and two such albums by one artist share one key in the cache, the grouping and the wire key. Real case: bassvictim's "?" (see F-B23-59).

Fix direction: when the cleaned album text is empty, key on the title's NFKC-lowercased text with whitespace collapsed and `|` written `%7c`; every existing non-empty key stays unchanged, and rows stored under the empty key age out by the TTL.

- [x] **Status:** resolved
**Completed:** 2026-10-25
Resolved by `normalize_name` keying an empty-normalizing album on its
NFKC-lowercased title; every existing non-empty key is unchanged, and rows
stored under the empty key age out by the TTL. Fixed by `0237a840`.
Source: owner's real runs, 2026-10-25
