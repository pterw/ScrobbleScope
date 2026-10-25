# Album Matching, Cache Re-verification and MusicBrainz Headroom Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop Spotify album search from returning a different album than the one asked for, clear the wrong matches already in the production cache without a manual step and without a mass re-search, stop a MusicBrainz 429 being cached as "no match", and give the MusicBrainz request spacing headroom.

**Architecture:** One stacked branch, `fix/album-matching`, cut from PR #269's head `b6feb138` (draft PR on top of #269). Task 1 files the findings; Tasks 2-10 are one atomic commit each, Task 11 closes the findings; each has an untagged PLAYBOOK Section 4 entry. The one matching rule is "equal `normalize_name` pair", already Deezer's rule; Spotify search and the cache re-verify adopt it, and `normalize_name` is corrected so an album whose title normalizes to nothing ("?", "EP") keeps an identity of its own.

**Tech Stack:** Python, aiohttp, asyncpg (Postgres cache, schema applied by `init_db.py` as the Fly release command), pytest with fakes (`tests/fake_postgres.py`), docsync.

**Owner rulings this plan carries** (R1-R5 from the brief; R6 and RB1-RB7 from the plan review, 2026-10-25):
- R1 Spotify album search applies Deezer's rule: walk the returned candidates, accept only an exact `normalize_name` match, otherwise a miss and the Deezer fallback runs. "Yes, fully."
- R2 Wrong matches already in the production cache are cleared by re-verify on read, with no manual DB step and no mass purge. RB1 fixes how (below).
- R3 MusicBrainz request starts about 1.1s apart.
- R4 A MusicBrainz 429 is treated like a 503; RB5 fixes the wait.
- R5 This is its own PR, stacked on #269.
- R6 D6 (F-B23-26, the artist spotlight's unchecked `items[0]`) is in scope. RB2: the owner confirmed.
- RB1 Old cached Spotify rows (NULL provider names): look up the cached Spotify ID. On first use, fetch the album by that ID, store its names, keep the row if they pass the exact-match rule, otherwise search again and overwrite. No mass re-search.
- RB3 Collaborations: a Spotify album matches when any one credited artist equals the Last.fm artist under `normalize_name`; an "A & B" Last.fm artist that misses falls to Deezer. D2 therefore stays possible: build metadata per key, log the shared ID, never drop a key.
- RB4 Search breadth: the album search asks Spotify for 5 candidates; the spotlight's artist search asks for 5 and applies the name check. (One request either way; the exact-match rule means extra candidates cannot add a false match. Spotify's February 2026 changelog caps Search at 10, F-B21-59, so 5 is inside it.)
- RB5 MusicBrainz 503 and 429 are both rate-limit answers: wait the `Retry-After` when present, otherwise exponential backoff with jitter, through `retry_with_semaphore` as the Last.fm and Spotify GET paths do; never a cached "no match".
- RB6 The MusicBrainz rate setting becomes a float minimum interval in seconds, default 1.1; if the old `MUSICBRAINZ_REQUESTS_PER_SECOND` is set in the environment, log a warning that it is ignored (the owner checks Fly secrets).
- RB7 Edition edge: an empty-normalizing title compares raw case-folded titles exactly, so "EP (Remastered)" against "EP" fails closed (Deezer fallback, then unmatched). Accepted as rare.

## The defects, verified in the source at `b6feb138`

- **D1** `spotify.py` `search_for_spotify_album_id` sends `limit: 3` and returns `items[0].get("id")` with no artist or title check. `deezer.py` `search_deezer_album` accepts a candidate only when `normalize_name(candidate_artist, candidate_title) == normalize_name(artist, album)`. An album Spotify lacks gets another album (Xiu Xiu "A Promise" got Captain Beefheart's "Safe As Milk", 1967); a sibling ranked higher wins ("audio stars" got "audio stars 2"; "Basspunk" got "Basspunk 2"; bassvictim's "?" got "Forever"). The wrong track list matches no scrobble, so `_results.py` sums `play_time_seconds` to 0 ("0 secs").
- **D2** `orchestrator/_search.py` `_run_spotify_search_phase` writes `spotify_id_to_key[spotify_id] = key` and `spotify_id_to_original_data[spotify_id] = data`: a second key with the same ID overwrites the first silently, and the loser falls to Deezer.
- **D3** `domain.py` `normalize_name` replaces ASCII punctuation with spaces and strips the album edition words (`deluxe, edition, remastered, version, expanded, anniversary, special, bonus, tracks, ep, remaster`) from the album only. An album "?" or "EP" normalizes to `""`. Exact matching on `""` would accept any other empty-normalizing title by that artist, and two such albums by one artist share one key everywhere the key is used.
- **D4** `musicbrainz.py` `lookup_original_release.search_once` retries 503 (`_RATE_LIMIT_STATUS`, fixed 1s) and other 5xx; a 429 reaches `status != 200` and returns `(None, None, True)`, a terminal "no match" that `release_checks` caches.
- **D5** `utils.py` `_MUSICBRAINZ_THROTTLE = _GlobalThrottle(MUSICBRAINZ_REQUESTS_PER_SECOND)` with `MUSICBRAINZ_REQUESTS_PER_SECOND = int(... "1")` in `config.py`: `_min_interval = 1.0 / 1`, request starts exactly 1.000s apart.
- **D6** (F-B23-26) `spotify.py` `_request_spotlight_artist` searches `artist:<name>` with `limit: 1` and returns `items[0]` unchecked. (The `artist_id` path names an explicit ID and needs no name check.)

## Probe answers (from the source, not guessed)

**Does the album cache store the provider's own artist and title? No.** `init_db.py` creates `spotify_cache(artist_norm, album_norm, spotify_id, release_date, album_image_url, track_durations, created_at, updated_at)` and adds `provider`, `provider_album_id`, `provider_url`. `enrichment.py` `AlbumMetadata` has `provider, album_id, url, release_date, image_url, track_durations`. `cache.py` `batch_persist_metadata` writes those and nothing else. `artist_norm, album_norm` are the *request's* key (the Last.fm names), not the provider's, so a wrong match stored under "xiu xiu|a promise" is indistinguishable from a right one. R2 therefore needs a schema change:
- `init_db.py` adds two nullable columns with `ALTER TABLE spotify_cache ADD COLUMN IF NOT EXISTS provider_artist TEXT, ADD COLUMN IF NOT EXISTS provider_title TEXT` (idempotent, no table rewrite). It ships through the existing Fly `release_command` (`python init_db.py`, in `fly.toml`), which runs after build and before traffic, so the columns exist before any new code reads them. The schema change ships through `init_db.py` only; no manual DB step. `cache.py` already treats an undefined column (SQLSTATE 42703) as a stale schema and fails open (`schema_is_out_of_date`), so a new image meeting an old schema degrades to "no cache", not an error. An old machine's INSERT omits the new columns (nullable, so fine); an old machine overwriting a good row leaves NULL names (re-stamped once, harmless).
- Memory (1 worker x 4 threads, 512 MB): no new in-memory structure beyond the rows a lookup already holds; two short text columns per row.
- **A cached row is in one of three states** for its key (RB1), decided by `AlbumMetadata.match_for(key)`: `fits` (any non-Spotify row, or a Spotify row whose two names are present and `normalize_name(provider_artist, provider_title) == key`), `wrong` (names present and they do not equal the key), `unstamped` (a Spotify row with a NULL name: every row written before the columns exist).
  - `wrong` is a miss: dropped by `AlbumCache.lookup`, searched again, overwritten by the existing upsert (Task 9).
  - `unstamped` is not a miss and not searched. The cached ID is known, so the job fetches that album by ID, builds its names, and either keeps the row (names fit: the stamped row is persisted, ID unchanged) or drops it to a miss (names do not fit, or Spotify has no such album any more) (Task 10). No mass re-search: a verified row is never fetched again, and a job with N unstamped rows costs `ceil(N/20)` detail calls (Spotify's Get Several Albums takes at most 20 IDs; the existing caller `_details.py` slices in 20s), not N searches.
  - **Which Spotify endpoint (F-B21-59):** Task 10 calls the existing `fetch_spotify_album_details_batch` (Get Several Albums, at most 20 IDs per call; the helper's docstring says "up to 50" but Spotify refuses more than 20 with a 400, which the helper turns into `unanswered`, so the caller must slice in 20s). That endpoint may be removed for this app without notice; the helper already answers a 403, 404 or 410 by falling back to `GET /v1/albums/{id}` one ID at a time and reporting it through `on_fallback`. So the plan adds no new endpoint and works whether or not Get Several Albums still exists. It never uses Search for stamping.
  - Only Spotify rows need names. A Deezer row is correct by construction (Deezer accepts a candidate only on an exact key match), so it is `fits` without names.
  - Residual: an album that failed the check and that Deezer cannot match either is not persisted, so its old row stays unread until the TTL (`METADATA_CACHE_TTL_DAYS = 30`, `cleanup_stale_metadata`) removes it, and each job that asks for it re-searches it. Bounded by the TTL; a `wrong` row is dropped before any use.
  - A details body whose credits do not contain the key's artist (so `matching_credit` is `None`) leaves the names NULL: the row is `unstamped`, which Task 10 sends to a miss and a search. That can only happen when the details artists differ from the search item's, which is rare and accepted; Task 7 logs one count line for it.

**How D3 is resolved without corrupting existing keys.** Frozen rule, written once in `domain.normalize_name` (the single owner): *the key's album half is the cleaned, edition-word-stripped text when that is non-empty (every existing non-empty key is unchanged); when it is empty, it is the title's NFKC-lowercased text with whitespace collapsed and every `|` written `%7c`.* A title of "?" keys as `?`, "EP" as `ep`, "!!!" as `!!!`; none is empty, none contains a pipe (so `format_album_key`'s split stays unambiguous), two different such titles by one artist get two keys. Only keys that were `""` change, and a row stored under `album_norm = ''` is simply never read again and ages out by the TTL (the same for `original_release_cache` rows, 365 days; no migration). Every site that needs the rule gets it by calling `normalize_name`, with no copy of it: Spotify search matching (Task 7), Deezer search matching (`deezer.py`, unchanged code), MusicBrainz candidate matching (`musicbrainz.py` `_is_matching_candidate`, unchanged), the cache key and its re-verify (`cache.py`, `enrichment.py`), the result grouping (`plays.py` `aggregate_albums`), the results rows and the unmatched keys (`_results.py`, `_deezer_fallback.py`), the wire key (`domain.format_album_key`, `release_checks.py`, `routes/api.py`) and the cover wash (`cover_wash_index`: an album "?" gets a different wash than before; accepted). Known fail-closed edge (RB7): a provider title such as "EP (Remastered)" strips to empty and keys on its raw text, so it does not equal the request "EP"; it is a miss, not a wrong match, and the reverse holds too.

**What D2 does (corrected).** D2 stays reachable through the real search. Under the multi-artist rule (RB3) a collaboration album with credits [A, B] equals key (A, title) and key (B, title); if Last.fm holds scrobbles of that album under both artist names, two different keys resolve to one Spotify ID, and the later used to overwrite the earlier. Behaviour: log one warning (operation and count only, no album or artist names: the logging rules forbid them), never drop a key, and build the metadata **once per requesting key** (`album_metadata_from_details(spotify_id, details, key)` per key), so each key's stored `provider_artist` is the credit that matched *its own* key and `match_for(its own key)` is `fits`. Filing one metadata object under two keys is wrong: the second key would read back `wrong` and be re-searched and re-persisted forever. The search phase returns the extra requests in a new fifth element; the detail phase files metadata under each.

**Other decisions the implementers must not reopen:**
- Multi-artist albums (RB3): a Spotify candidate matches when `normalize_name(credited_artist, title)` equals the key for *any one* of its credited artists (Deezer sees only the primary artist; Spotify lists all). The artist that matched is the one stored in `provider_artist`.
- Search breadth (RB4): the album search and the spotlight's artist-name search both ask for `limit: 5`.
- Spotlight, artist half (accepted): the name check compares `normalize_name(x, "")[0]`. An artist whose name is punctuation only ("!!!") normalizes to `""`; when the requested name normalizes to `""` the spotlight returns `None` (fail closed) rather than accept any other such artist. The same artist-half limit exists for albums and is accepted: the artist half of `normalize_name` is unchanged.
- MusicBrainz 503 and 429 share one branch (RB5, owner-confirmed): when `Retry-After` is present wait it (`parse_retry_after`); when absent, exponential backoff with jitter (`2 ** attempt` seconds plus a small deterministic jitter, as the Spotify GET paths in `spotify.py` do) through `retry_with_semaphore`; a `Retry-After` above `MAX_RETRY_AFTER_SECONDS` raises `musicbrainz_rate_limited` (already that helper's behaviour); exhausted retries raise the helper's `ProviderError`; none is ever cached.
- `MUSICBRAINZ_REQUESTS_PER_SECOND` (int) is replaced by `MUSICBRAINZ_MIN_INTERVAL_SECONDS` (float, default `1.1`) (RB6). At BASE the old name appears only in `config.py` and `utils.py` (grep: no test, README, `.env.example` or `fly.toml` names it). Setting the old name in the environment logs one warning that it is ignored.
- Unanswered stamping (decision for review, flagged in the report): when Spotify cannot answer the stamping call (no token, the job breaker tripped, an ID in `unanswered`), the unstamped row is kept for this job and not persisted, the same as today's behaviour; the next job tries again. It is never dropped on an outage.

## Global Constraints

- Work on `fix/album-matching` (the controller creates it from `b6feb138`), in MAIN or a detached code-phase worktree. `PY` = `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"`.
- The workspace `constraints.md` binds logging, commit procedure, staging, environment, tests, docs and the shared-files rule, and was rewritten for this plan.
- Side-task logging: every commit adds one dated entry `### <date> - <title>` after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker line, no `(Batch N WP-X)` tag, ending `` Validation: `pytest -q` -- **N passed**. ``.
- Every PLAYBOOK entry names the existing tests its commit edits ("edited existing tests: <names>" or "none").
- No new `test_*.py` module: every task extends an existing module (this plan, constraints R3).
- Commit messages: Conventional Commits, imperative subject <= 72 characters, body says why. No attribution line unless the dispatch gives one.
- Never `--no-verify`, `--amend`, rebase, reset, `sed -i`, or `git checkout`/`git restore` of a file holding uncommitted work.
- Tests assert intended behaviour with fakes for every API and for Postgres; nothing calls a live service. Each new test is proven red against the tree without the change (and by each planted defect its task lists), then green. A test names the behaviour it guards.
- Logs name operations and counts, never an album, artist or track name (AGENTS.md logging rules).
- Docs follow the code: grep `README.md`, `docs/agents/`, `ARCHITECTURE`-style docs and `DESIGN.md` for prose the change makes untrue ("first result", "limit", the 1 req/s figure) and fix it in the same commit; point-in-time records stay.
- ASCII only in Markdown and commit messages. Cite functions by name, not line number. Grep before claiming anything does not exist.

## Real cases the regression tests reuse

Xiu Xiu / "A Promise" against a Spotify answer of Captain Beefheart / "Safe As Milk"; "audio stars" against ["audio stars 2", "audio stars"]; bassvictim "Basspunk" against ["Basspunk 2", "Basspunk"]; bassvictim "?" against ["Forever", "?"] and against ["Forever"] alone (miss); gapyear "EP" against "EP" (must still match). All through fakes of the HTTP response or of the search function.

---

### Task 1: File the findings and open the log

Wave 0, serial, in MAIN. **Touches:** `docs/agents/FINDINGS.md`, `docs/agents/PLAYBOOK.md`. **After:** the plan commit (the controller's first commit). **Mode:** serial.

**Interfaces:**
- Produces: five open findings the later tasks cite, with the next free IDs (re-grep `^### F-B23-` first; at `b6feb138` the highest is F-B23-58): F-B23-59 (D1), F-B23-60 (D2), F-B23-61 (D3), F-B23-62 (D4), F-B23-63 (D5). D6 stays F-B23-26.

- [ ] **Step 1:** Add the five findings to the active section of `docs/agents/FINDINGS.md`, each with an `F-B23-<N>: <title>` heading, one problem sentence with the file and function, the real case, the fix direction, a `- [ ] **Status:** open (P2)` line and `Source: owner's real runs, 2026-10-25`. D4 is the P2 that corrupts a cache; D5 is P3. D2's text says it stays reachable through collaboration albums. Follow AGENTS.md "Finding-Writing Rules" (ASCII, required fields).
- [ ] **Step 2:** Update F-B23-26's text only if it names a fix that this plan changes (it does not); leave it open.
- [ ] **Step 3:** PLAYBOOK Section 3 gets one sentence pointing at the plan and branch (follow how earlier side-task plans were pointed at); Section 4 entry `Plan album matching and cache re-verification` (scope, the owner's rulings above, deviations none). Its "edited existing tests" field reads: none by this commit; the plan's later commits edit these existing tests, each named in its own entry: `tests/test_domain.py::test_normalize_name_ep_preserved_in_artist_stripped_from_album` (Task 2), `test_lookup_raises_when_musicbrainz_stays_throttled_not_no_match` (now `musicbrainz_unavailable`, response `headers = {}`) and the 503 retry tests that assert a fixed sleep, all in `tests/services/test_musicbrainz_service.py` (Task 3), and the search fakes in `tests/services/test_spotify_service.py` (Task 7).
- [ ] **Step 4:** Commit procedure (`pytest -q`, `doc_state_sync.py --fix --test-count N`, stage by name, `pre-commit`, `--check`); message `docs(findings): File the album-matching findings`.

Acceptance:
- `doc_state_sync.py --check` exits 0 and the five headings match `^### F-B23-\d+: `.
- Each finding names the function it is about and one real case.
- No code, test or other tracked file changes.

---

### Task 2: An empty-normalizing album keeps an identity (D3)

Wave 1, code phase. **Touches:** `scrobblescope/domain.py` (`normalize_name`, and the docstring of `format_album_key`), `tests/test_domain.py`. **After:** 1. **Mode:** code + land.

**Interfaces:**
- Produces: `normalize_name(artist, album)` returns the frozen rule above. The artist half is unchanged. Edition-word stripping is unchanged for every title that leaves a non-empty remainder.
- Consumes: nothing. Every other module takes the new behaviour through the call it already makes.

**Edited existing test (name it in the PLAYBOOK entry):** `tests/test_domain.py::test_normalize_name_ep_preserved_in_artist_stripped_from_album` asserts `album == ""` for ("EP", "EP"). Change its expected album half to `"ep"` and fix its docstring (the artist keeps `ep` and the album now keys on its own text). Then `grep -n '""' tests/test_domain.py` and grep `tests` for other assertions that pin an empty album key; if one lives in another file, stop and return NEEDS_CONTEXT (that file is not in this task's Touches, and the wave rule forbids a second owner).

Acceptance:
- `normalize_name("bassvictim", "?")` and `normalize_name("bassvictim", "!")` are different, both non-empty, and neither contains `|`; `normalize_name("gapyear", "EP")` has a non-empty album half; `normalize_name("a", "||")` has no `|` in either half.
- A title with a non-empty remainder keys exactly as before (parametrised over "OK Computer (Deluxe Edition)", "Basspunk 2", a Japanese title, an artist "New Edition").
- `format_album_key` round-trips: splitting the wire key on its single `|` returns the two halves for "?" and "EP".
- Planted defects the tests must catch: always return the raw text (breaks the unchanged-keys test); fall back to `""` again; fall back without the pipe escape.

---

### Task 3: A MusicBrainz 429 or 503 waits and retries (D4, R4, RB5)

Wave 1, code phase. **Touches:** `scrobblescope/musicbrainz.py` (`lookup_original_release.search_once`, `_RATE_LIMIT_STATUS`), `tests/services/test_musicbrainz_service.py` (including the edit to the existing `test_lookup_raises_when_musicbrainz_stays_throttled_not_no_match`). **After:** 1. **Mode:** code + land.

**Interfaces:**
- A 429 or 503 answer returns the retry shape `(None, retry_after, False)` with `retry_after = parse_retry_after(response.headers.get("Retry-After"), default=None)`. With a header, `retry_with_semaphore` sleeps it (jitter added by the helper's `jitter` argument, which this call now passes). With no header the shape carries `None`, so the helper's `backoff` runs: change the call's `backoff=1` to an exponential callable (`2 ** attempt` plus a small deterministic jitter), as the Spotify GET paths do. Other 5xx keep their retry; a non-200, non-rate-limit 4xx stays a definite no-match.
- A `Retry-After` over the cap raises `ProviderError` (`musicbrainz_rate_limited`) via the existing `provider_failure("musicbrainz")`. Exhausted retries (RB8): with a `Retry-After` header on the last answer, `musicbrainz_rate_limited`; with no header (`retry_after` is `None`, so the helper takes its `unavailable` path), `musicbrainz_unavailable`. Neither is cached. `release_checks` declines to cache a raised error (its tests cover it; drive it here).

**Edited existing tests (name them in the PLAYBOOK entry):** `test_lookup_raises_when_musicbrainz_stays_throttled_not_no_match` (`tests/services/test_musicbrainz_service.py`, about lines 380-404) answers a header-less 503 on every attempt and asserts `musicbrainz_rate_limited`; it now asserts `musicbrainz_unavailable` (update its docstring), and its `AsyncMock` response gets `headers = {}` so `response.headers.get(...)` is not an un-awaited coroutine that warns. Do not change the code back to `rate_limited`: that loses RB5/RB8. Also `test_lookup_retries_on_503_then_succeeds` and any other 503 test in that file currently assume a fixed one-second wait. Grep `503` and `sleep` in that file and edit each assertion that pins the old fixed sleep to the new rule (header honoured, else exponential), keeping what it meant.

Acceptance:
- A fake session answering 429 once with `Retry-After: 2` then 200 with a trusted match returns the match, and the patched sleep was awaited with the header's seconds (plus jitter, asserted as a bound).
- A 429 and a 503 with no header each retry with a growing wait (the second sleep is longer than the first, jitter bounded), then succeed.
- A fake answering 429 with `Retry-After` on every attempt raises `ProviderError` `musicbrainz_rate_limited`; one answering 429 or 503 with no header on every attempt raises `musicbrainz_unavailable`. In both, the caller records nothing in the original-release cache (drive `release_checks` with the same fake: the cache write is not called).
- A 429 with `Retry-After` above the cap raises at once without sleeping; a 404 still returns `(None, None)`.
- Planted defects: treat 429 as terminal no-match (the old behaviour); ignore the header; fixed one-second wait with no header.

---

### Task 4: MusicBrainz requests start 1.1s apart (D5, R3, RB6)

Wave 1, code phase. **Touches:** `scrobblescope/config.py`, `scrobblescope/utils.py` (`_GlobalThrottle`, `get_musicbrainz_limiter`), `tests/test_utils.py`, `tests/test_config.py` if it names the old setting. **After:** 1. **Mode:** code + land.

**Interfaces:**
- Produces: `MUSICBRAINZ_MIN_INTERVAL_SECONDS` (float, env override, default `1.1`) replacing `MUSICBRAINZ_REQUESTS_PER_SECOND`. The global throttle takes its spacing from it (a minimum interval, not an integer rate). The throttle is the enforcing limit; the per-loop `AsyncLimiter` behind it may stay as it is (it never binds beyond the throttle), so no test pins it.
- If `MUSICBRAINZ_REQUESTS_PER_SECOND` is set in the environment, `config.py` logs one warning that it is ignored and names the new variable (the owner checks Fly secrets).
- Other providers' throttles keep their integer rates and their behaviour.

Acceptance:
- With a controlled clock, two consecutive `next_wait()` calls on the MusicBrainz throttle schedule starts at least 1.1s apart (not 1.0).
- The Spotify, Deezer and Last.fm throttles' spacing is unchanged (assert one of them).
- Setting the env var to `2.0` yields 2.0s spacing; setting the old variable logs the ignored-setting warning once and changes nothing; the module docstring/comments no longer say "1 request per second" as the enforced figure (the policy figure stays quoted as the source's limit).
- Planted defect: leave the throttle at 1.0.

---

### Task 5: The artist spotlight checks the name Spotify returns (D6, R6, RB4)

Wave 1, code phase. **Touches:** `scrobblescope/spotify.py` (`_request_spotlight_artist` only), `tests/services/test_spotify_service.py` (spotlight tests only). **After:** 1. **Mode:** code + land.

**Interfaces:**
- On the name-search path, `_request_spotlight_artist` asks for `limit: 5`, walks the returned artists in order and returns the first whose `normalize_name(hit_name, "")[0] == normalize_name(artist_name, "")[0]`; if none, or if the requested name normalizes to `""`, it returns `None`, so `/api/artist_spotlight` (`routes/api.py`, unchanged) answers its existing null-image payload. The `artist_id` path is unchanged.

Acceptance:
- A fake search answering only different artists for "ear" returns `None`; the route test (if one exists for the empty payload) still passes.
- A fake answering ["ear-something", "ear"] returns the second; the same artist with different casing or punctuation ("Beyonce" vs "BEYONCE") returns the hit.
- A requested name of "!!!" returns `None` even when the fake answers an artist named "???".
- The `artist_id` path still returns the hit whatever its name.
- Planted defects: return `items[0]` unchecked; compare case-sensitively; stop at the first candidate.

---

### Task 6: The cache stores the provider's own names and can say whether a row fits a key (R2, RB1 schema)

Wave 1, code phase. **Touches:** `init_db.py`, `scrobblescope/enrichment.py`, `scrobblescope/cache.py` (`batch_lookup_metadata`, `batch_persist_metadata`), `tests/test_cache_schema.py`, `tests/test_init_db.py` if it lists statements, `tests/fake_postgres.py` (`METADATA_FIELDS`), `tests/services/test_enrichment.py`, `tests/services/test_cache.py`, `tests/album_metadata.py` if it builds `AlbumMetadata`, `tests/test_album_cache_parity.py` (the stored-row shape only). **After:** 1. **Mode:** code + land. Also run `tests/test_module_boundaries.py`.

**Interfaces:**
- `init_db.py`: the `ALTER TABLE ... ADD COLUMN IF NOT EXISTS provider_artist TEXT, ... provider_title TEXT` statement above, idempotent.
- `AlbumMetadata` gains `provider_artist: str | None = None` and `provider_title: str | None = None` (defaults keep every existing constructor call valid; the dataclass stays frozen).
- `AlbumMetadata.from_row` reads the two columns with `.get` (absent or NULL gives `None`).
- `AlbumMetadata.match_for(key) -> str`, returning one of three module constants `MATCH_FITS`, `MATCH_WRONG`, `MATCH_UNSTAMPED`: any provider other than `"spotify"` is `MATCH_FITS`; a Spotify row with either name `None` is `MATCH_UNSTAMPED`; otherwise `MATCH_FITS` when `normalize_name(provider_artist, provider_title) == key`, else `MATCH_WRONG`. (The one place the re-verify rule lives; Tasks 9 and 10 call it.)
- `batch_persist_metadata` writes the two columns; `batch_lookup_metadata` selects them. A parity test pins a stored row's shape; update it for the two new fields only (a one-field shape change in an existing test, name it in the PLAYBOOK entry).

Acceptance:
- `init_db.py` source contains the idempotent `ADD COLUMN IF NOT EXISTS` for both columns (`test_cache_schema.py` pattern); the whole-schema retry tests still pass.
- Persist then lookup through the fake database returns the two names; a row written without them (a pre-migration row from the fake) reads back with `None`.
- `match_for`: a Spotify row with names "Captain Beefheart"/"Safe As Milk" is `MATCH_WRONG` for the Xiu Xiu key; with matching names it is `MATCH_FITS`; with NULL names it is `MATCH_UNSTAMPED`; a Deezer row is `MATCH_FITS` without names.
- Planted defects: `match_for` returns fits for NULL names; it returns unstamped for a wrong pair; the persist drops a name column.

---

### Task 7: Spotify album search accepts only an exact match (D1, R1, RB3, RB4)

Wave 2, code phase. **Touches:** `scrobblescope/spotify.py` (`search_for_spotify_album_id`, `album_metadata_from_details`), `scrobblescope/orchestrator/_details.py` (the one call to `album_metadata_from_details`), `tests/services/test_spotify_service.py`, `tests/services/test_orchestrator_fetch_spotify.py` only where its fake of `album_metadata_from_details` needs the new argument. **After:** 2, 5, 6 (Task 2 for the key rule, Task 5 for `spotify.py`, Task 6 for the new fields). **Mode:** code + land.

**Interfaces:**
- `search_for_spotify_album_id(session, artist, album, token, semaphore=None)` keeps its signature and sends `limit: 5` (RB4); it walks `albums.items` in order and returns the ID of the first item for which some credited artist `a` has `normalize_name(a, item["name"]) == normalize_name(artist, album)`; if none, it returns `None` (a miss, which the search phase already sends to Deezer). Missing or non-text `name`/`artists` fields make a candidate not match, never raise.
- A pure helper in `spotify.py` (name it `matching_credit(item, key)`) returns the credited artist name that matched or `None`; the search and the metadata builder both use it.
- `album_metadata_from_details(spotify_id, details, key=None)`: when `key` is given, sets `provider_artist` to `matching_credit(details, key)` and `provider_title` to `details["name"]`; with no `key`, or no match, both stay `None` (unstamped, fail closed). `_details.py` passes the key it holds for the ID. When the key is given and no credit matches, log one count line (operation only, no names).

**Edited existing tests (name them in the PLAYBOOK entry).** These fake Spotify search bodies carry only an `id`, so after this task they are misses. Each gains `name` and `artists` matching the request the test makes:
- `tests/services/test_spotify_service.py`: `test_search_for_spotify_album_id_retries_429_then_returns_id`, `test_search_succeeds_on_first_try`, `test_search_retries_a_malformed_retry_after`, and the helper `_ok_search(spotify_id)`. The helper gains `artist` and `album` parameters (defaulting to the request most callers make) and returns `{"albums": {"items": [{"id": ..., "name": album, "artists": [{"name": artist}]}]}}`; grep every `_ok_search(` caller (the 401 retry tests, the breaker tests, the token tests) and pass the request's own names where it differs. The 429-retry and 401-retry tests must still assert what they meant: the retried 200 body needs the matching names too.
- `tests/services/test_orchestrator_fetch_spotify.py`: the fake of `album_metadata_from_details` takes the third argument (`key`).
- Any other test file that fails because its search fake lacks names: stop and return NEEDS_CONTEXT (not in Touches).

Acceptance:
- Xiu Xiu / "A Promise" against a fake answering only Captain Beefheart / "Safe As Milk": returns `None`.
- "audio stars" against ["audio stars 2", "audio stars"] returns the second ID; "Basspunk" against ["Basspunk 2", "Basspunk"] the second; bassvictim "?" against ["Forever"] returns `None` and against ["Forever", "?"] the second; gapyear "EP" against "EP" returns that ID; the request carries `limit` 5.
- A collaboration album whose second credited artist is the Last.fm artist matches; `album_metadata_from_details(id, details, key)` stores that artist as `provider_artist`.
- Planted defects: return `items[0]` (the old behaviour); compare title only; stop at the first non-matching candidate; leave `limit` at 3.

---

### Task 8: Requests sharing a Spotify ID each get their own metadata (D2, RB3)

Wave 3, code phase. **Touches:** `scrobblescope/orchestrator/_search.py`, `scrobblescope/orchestrator/_details.py`, `scrobblescope/orchestrator/__init__.py` (the one unpacking of the search phase's return), `tests/services/test_orchestrator_fetch_spotify.py` (the only test file that unpacks `_run_spotify_search_phase`: `grep -n "_run_spotify_search_phase" tests` at BASE). **After:** 7. **Mode:** code + land.

**Interfaces:**
- `_run_spotify_search_phase` returns a fifth element `shared_id_requests: {spotify_id: [(key, data), ...]}` holding every request after the first for an ID it already mapped; the first four elements keep their meaning. On a collision it logs one warning with the count (no names). Existing tests that unpack the 4-tuple are edited to the 5-tuple (edited existing tests, named in the PLAYBOOK entry).
- `_run_spotify_batch_detail_phase` takes the extra mapping (default empty). For the first key and for **each** extra key it calls `album_metadata_from_details(spotify_id, details, key)` separately, so every key's metadata carries the credit that matched that key, and files each under its own key in `cache_hits` and `new_metadata`. `detail_unavailable_keys` includes the extras of an unanswered ID.

Acceptance:
- A fake search returning the same ID for two different keys: both keys end in `cache_hits` and `new_metadata`, and one warning is logged naming no album.
- Collaboration case: details credit [A, B] for keys (A, title) and (B, title): both stored metadata rows have `match_for(own key) == MATCH_FITS`, with `provider_artist` A and B respectively (a naive "file one object under both keys" fails this).
- Distinct IDs behave exactly as before (the existing tests pass with the 5-tuple).
- A shared ID whose details are unanswered puts both keys in `detail_unavailable_keys`.
- Planted defects: keep the overwrite; file only the first key; file the first key's metadata under every key.

---

### Task 9: A cached Spotify match whose names do not fit the key is a miss (R2, RB1)

Wave 3, code phase. **Touches:** `scrobblescope/cache.py` (`AlbumCache.lookup`), `tests/services/test_cache.py`, `tests/test_album_cache_parity.py` (adds new cases only). **After:** 6, 7 (the new writer must stamp names before the filter can pass anything). **Mode:** code + land.

**Interfaces:**
- `AlbumCache.lookup(keys)` drops every returned entry whose `metadata.match_for(key)` is `MATCH_WRONG`, so the caller sees a miss, and logs one line with the count dropped (no names). `MATCH_FITS` and `MATCH_UNSTAMPED` entries are returned as before (Task 10 handles the unstamped ones). `lookup_failed` and the fail-open behaviour are unchanged. The dropped album is searched again and persisted over the old row by the existing upsert.

Acceptance:
- Through `fake_postgres`: a row stored under "xiu xiu|a promise" with provider names Captain Beefheart / "Safe As Milk" is absent from `lookup`'s result; the same row with Xiu Xiu / "A Promise" is present.
- A pre-migration Spotify row (NULL names) is still returned (not dropped here); a Deezer row (no names) is present.
- End to end (`process_albums` with fakes): the wrong-named key is searched again and the new metadata, with names, is persisted over the row; the dropped hit is not counted in `db_cache_lookup_hits`.
- Planted defects: skip the filter; drop `MATCH_UNSTAMPED` rows too; drop Deezer rows.

---

### Task 10: An old cached Spotify row is checked by its cached ID once (RB1)

Wave 4, code phase. **Touches:** `scrobblescope/orchestrator/_cache.py` (`_lookup_cached_metadata` and one new helper, `_stamp_unstamped_spotify_rows`), `tests/services/test_orchestrator_process_albums.py`, and any other test file whose seeded cached Spotify row now counts as unstamped and so reaches the new detail call (grep `process_albums`, `_lookup_cached_metadata`, `open_album_cache` in `tests` at the task's start and name each file in the code report; no other task is in Wave 4, so there is no second owner). **After:** 6, 7, 9 (and 8 for the wave order). **Mode:** code + land.

**Interfaces:**
- `_stamp_unstamped_spotify_rows(album_cache, job_id, cached_metadata)` takes the lookup's result and returns it with each `MATCH_UNSTAMPED` entry replaced or removed. It is called inside `_lookup_cached_metadata` after the lookup and before the hit-count stat, so dropped rows are not counted as hits. For the unstamped entries only it (a) fetches a Spotify token; (b) under `spotify_job_breaker` fetches details for the cached IDs (`metadata.album_id`) with `fetch_spotify_album_details_batch` (Get Several Albums; the helper is called once per chunk of at most 20 cached IDs, a module constant `_STAMP_BATCH_SIZE = 20` in `_cache.py` equal to `batch_size` in `_details.py`, which is not touched; falling back to `GET /v1/albums/{id}` on 403, 404 or 410; F-B21-59; never Search); (c) per entry builds `album_metadata_from_details(id, details, key)`: if its `match_for(key)` is `MATCH_FITS`, the stamped metadata replaces the entry and is persisted through `album_cache.persist` (an upsert; ID unchanged); otherwise (names do not fit, no matching credit, or Spotify answered without the album) the entry is removed, so the key is a miss, searched and overwritten like a `MATCH_WRONG` one.
- Reach the providers through the live `scrobblescope.orchestrator` namespace exactly as `_details.py` does, so tests patch one place.
- Fail open: no token, a tripped breaker, an ID in the result's `unanswered`, or a persist failure leaves the unstamped entry in place for this job (a non-fatal log line with counts only). One log line states the counts kept, stamped, dropped and unanswered.
- A job with no unstamped rows makes no Spotify call and fetches no token.

Acceptance:
- An unstamped Spotify row whose fake details credit the key's artist and title is kept (same ID), returned with names, and persisted with them; a second `_lookup_cached_metadata` over the persisted row makes no Spotify call.
- An unstamped row whose details credit Captain Beefheart / "Safe As Milk" for the Xiu Xiu key is removed from the result (a miss) and counted in neither `db_cache_lookup_hits` nor kept; a row whose details come back empty is removed likewise.
- Call count: 120 unstamped rows cause 6 batch-detail calls and zero search calls. The fake records each call's ID list and the test asserts no call carries more than 20 IDs (a fake that accepts 50 must not let an oversized batch pass); 21 rows cause 2 calls (20 and 1).
- Details unanswered, or no token: the rows stay in the result unchanged and nothing is persisted.
- Planted defects: keep a row whose names do not fit; drop every unstamped row (the mass re-search); call search instead of details; send all IDs in one call (or chunks of 50).

---

### Task 11: Close the findings and sweep the prose

Wave 5, serial, in MAIN. **Touches:** `docs/agents/FINDINGS.md`, `docs/agents/PLAYBOOK.md`, any doc a sweep shows still describes the old behaviour. **After:** 2-10. **Mode:** serial.

- [ ] **Step 1:** `sweeper` at HEAD for "first result", "items[0]", "REQUESTS_PER_SECOND" with MUSICBRAINZ, "1 request per second" and "`album_norm`" empty-key prose in tracked non-historical docs; fix each live hit.
- [ ] **Step 2:** Mark F-B23-26, F-B23-59..63 resolved with the commit that fixed each (the convention the archive uses for `-- RESOLVED`; docsync rotates them).
- [ ] **Step 3:** PLAYBOOK Section 3 sentence updated to "done"; one Section 4 entry for this step (edited existing tests: none).
- [ ] **Step 4:** Commit procedure; message `docs(findings): Close the album-matching findings`.

Acceptance:
- `doc_state_sync.py --check` exits 0.
- A final grep finds no live doc stating that Spotify search takes the first result or that MusicBrainz runs at exactly 1 req/s.
- All six findings read resolved with a commit reference.

---

## Dispatch

Landing writes the shared bookkeeping (PLAYBOOK, FINDINGS, SESSION_CONTEXT, `--fix`); code phases never do. No task adds or changes a gate-deciding script (no verdict script, no `frontend_gate` check, no `docsync` file), so no planted-defect JSON is needed and no task must land alone for that reason. Task 1 and Task 11 are serial in MAIN. Sizing: Task 6 (many files) and Task 10 are the largest; if a code phase reports it cannot finish in one pass, split it at the file boundary it names.

| Wave | Tasks | Mode | Agents at peak |
|---|---|---|---|
| 0 | Task 1 | serial | 1 |
| 1 | Tasks 2, 3, 4, 5, 6 (disjoint files) | code phases, parallel | 5 + reviews |
| 2 | Task 7 (After 2, 5, 6: patches staged in its worktree) | code phase | 1 + review |
| 3 | Tasks 8, 9 (disjoint files; both After 7, Task 9 also After 6) | code phases, parallel | 2 + reviews |
| 4 | Task 10 (After 6, 7, 9) | code phase | 1 + review |
| 5 | Task 11 | serial | 1 |

Per-wave file check (re-done after the fix round): W1 domain+test_domain / musicbrainz+test_musicbrainz_service / config+utils+test_utils(+test_config) / spotify(spotlight)+test_spotify_service / init_db+enrichment+cache+fake_postgres+test_cache_schema+test_init_db+test_enrichment+test_cache+album_metadata+test_album_cache_parity: disjoint. W2 one task. W3 _search+_details+__init__+test_orchestrator_fetch_spotify (T8) vs cache+test_cache+test_album_cache_parity (T9): disjoint. W4 one task. A file touched in two waves (`spotify.py`, `test_spotify_service.py`: T5 then T7; `cache.py`, `test_cache.py`, `test_album_cache_parity.py`: T6 then T9; `_details.py`, `test_orchestrator_fetch_spotify.py`: T7 then T8) is always ordered by After.

Landings in MAIN, one at a time: 2, 3, 4, 5, 6, 7, then 8 and 9 (either order), then 10, then 11. Task 9 must land after Task 7 and Task 7 after Task 6, so a deploy never reads names that nothing writes; Task 10 lands last of the code so the stamping a deploy runs already finds the filter and the writer in place. Each landing is followed by a `gate-runner` on the landed commit, then the controller pushes and starts a `ci-watcher`.

Deploy note: the Fly release command runs `init_db.py` before traffic, so Task 6's columns exist before the new code serves. Merge order on Fly is the branch's order; no manual DB step. The PR is stacked on #269 (base branch `feat/ui-round-2-backlog`); the `Quality Gate` workflow runs for a pull request against that base, which the controller confirms on the first push.

## Final checks (controller)

- [ ] `gate-runner` ALL_PASS at the final head, including the `frontend-gate` (Task 2 changes `cover_wash_index` output for "?" and "EP" titles).
- [ ] `sweeper` for `items[0]` in `scrobblescope/` (only the F-B23-26 id path may remain, and the Spotify album search must not).
- [ ] Each PLAYBOOK entry's "edited existing tests" field matches the diff: Task 2 (`test_normalize_name_ep_preserved_in_artist_stripped_from_album`), Task 3 (the 503 retry tests), Task 6 (the parity shape), Task 7 (`_ok_search` and the inline search bodies, the fetch-spotify fake), Task 8 (the 4-tuple unpackings), Task 10 (the seeded-row tests it names).
- [ ] CI green for the final head; the PR stays draft until the owner says otherwise.

## Self-review

- Coverage: D1 -> Task 7; D2 -> Task 8; D3 -> Task 2; D4 -> Task 3; D5 -> Task 4; D6 -> Task 5; R2/RB1 -> Tasks 6, 9, 10; findings -> Tasks 1, 11; PLAYBOOK entries -> every task's landing.
- Names used across tasks: `normalize_name`, `provider_artist`, `provider_title`, `AlbumMetadata.match_for`, `MATCH_FITS`, `MATCH_WRONG`, `MATCH_UNSTAMPED`, `matching_credit`, `shared_id_requests`, `_stamp_unstamped_spotify_rows`, `MUSICBRAINZ_MIN_INTERVAL_SECONDS`.
- One task per file per wave (see the Dispatch check). `enrichment.py` only Task 6; `_cache.py` only Task 10.
- Every new test names a planted defect it must catch.
