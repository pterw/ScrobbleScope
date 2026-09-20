# BATCH22: Enrichment providers and original release years

**Status:** Active. WP-0 through WP-3 are complete and WP-4 is in progress: Task 10 landed the release-check endpoint and Task 11 remains. **WP-5 is the next batch work package** once WP-4 closes. Owner-approved 2026-09-13.
**Branch:** `feat/batch22-enrichment` (worktree off `test`).
**Baseline:** 1034 tests passing at batch open; the frontend gate runs 28
checks in 50 runs.
**Plan of record:**
`docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md` carries
every task, its tests and its exact commands. This file carries the scope,
the intended outcome, the work packages and their acceptance criteria.

---

## Context

Two defects sit under the same code.

**One provider answers for every album.** The Spotify app is in Development
Mode. Spotify removed Get Several Albums for such apps in February 2026 and
postponed the removal for existing apps with no new date, which is the only
reason the pipeline works (FINDINGS F-B21-59). The single-album fallback
landed on 2026-09-13, but every album still depends on one company's
postponement.

**Release years are wrong for reissues.** Spotify and Deezer both date a
remaster by its reissue: Deezer dates The Beatles' White Album 2015-12-24.
MusicBrainz carries the original on the release group, and returned
1977-02-04 for *Rumours*. The year filters mean the original year, so today
the app keeps remasters in the wrong year and drops the originals.

**Owner rulings, 2026-09-13.** Deezer is a fallback behind Spotify, not a
replacement. The release-year correction uses progressive disclosure: results
render at once, corrections land live, a corrected row stays in place with a
marker, and the list re-sorts only on reload. This batch comes before Batch
23, the Spotify export import, which builds on it.

---

## Intended outcome

Batch 22 is complete only when all of these product outcomes hold:

- Album enrichment no longer has Spotify as its only provider. Spotify stays
  first, and Deezer receives only albums Spotify could not enrich.
- Provider identity, provider album ID and provider URL travel with metadata
  through the cache, results, unmatched report and CSV export.
- Release filters use an album's original release date when a cached
  MusicBrainz correction exists, while retaining the provider's reissue date
  for explanation and attribution.
- Slow MusicBrainz work never delays the first results render. A bounded,
  process-wide worker persists corrections, and the page discloses them live
  without moving rows under the reader.
- Missing credentials, provider errors, cache failures and "checked, nothing
  found" outcomes degrade to explicit fallback or skipped states instead of
  blocking the job or repeating the same lookup indefinitely.

## Runtime model

1. Last.fm aggregation produces normalized album keys and listening totals.
2. The metadata cache returns provider-neutral album records. Spotify enriches
   remaining keys first; Deezer receives only the misses.
3. Results are filtered and rendered immediately. Any correction already in
   `original_release_cache` replaces the provider date for filtering and
   display, while the provider date remains available separately.
4. One capped MusicBrainz worker per process checks uncached albums at no more
   than one request per second, using a contact-bearing User-Agent. Both a
   match and a confirmed miss are cached.
5. The results page polls job-scoped release-check state. Corrected rows gain
   an in-place marker; albums that now belong in the filter are announced with
   a reload action. The open page never re-sorts itself.

The provider contract and original-release cache are separate concerns:
Spotify or Deezer describes the provider's album, while MusicBrainz may only
correct its release chronology.

---

## Work packages

### ~~WP-0 -- Module split, behaviour-neutral~~ -- **DONE**

`orchestrator.py` is 1,035 lines and `routes.py` is 985, against 361 for the
largest other module in their directories. AGENTS.md "Proposal and Design
Rules" item 3 compares a file to its largest peer, and F-B21-51 filed the
same complaint about `frontend_gate.py` at 9x.

- `routes.py` became a package of blueprints registered by `create_app`:
  pages, album flow, heatmap flow, JSON API. The rest of this batch adds a
  route and an endpoint, so the split comes first.
- `orchestrator.py` split by phase: search, details, cache, results.
- **Both retain a facade.** Tests patch `scrobblescope.routes.X` and
  `scrobblescope.orchestrator.X` by name, and the precedent is
  `worktree_guard.py` and `_frontend_gate_results.py`.
- **Delivered scope:** the routes and orchestrator packages retain their
  public facade imports and existing endpoint names.
- **Acceptance:** every existing test passes **unmodified**. That is the
  proof the split changed nothing. No behaviour change ships in this WP.

### ~~WP-1 -- The provider contract~~ -- **DONE**

An `AlbumMetadata` value object, cache columns that any provider can fill,
and the Spotify calls moved behind the contract. `init_db.py` needed explicit
`ALTER TABLE` statements because `CREATE TABLE IF NOT EXISTS` never alters an
existing table, and `spotify_id` was `NOT NULL` at batch open.

- [x] Task 1: add the immutable, provider-neutral album metadata value object.
- [x] Task 2: migrate existing cache rows and add provider fields plus the
  separate `original_release_cache`, including a durable negative result.
- [x] Task 3: place Spotify enrichment behind the provider contract without
  changing its result shape or selection behavior.
- **Acceptance:** a Spotify-sourced result is byte-identical to today's, and
  the cache round-trips a row with its provider recorded.

### ~~WP-2 -- Deezer as the fallback~~ -- **DONE**

A Deezer client and its wiring behind Spotify. Matching compares normalised
artist and title: the filtered search ranks a tribute single above the real
album. Track lengths come from `/album/{id}/tracks`, because the album
endpoint lists only 25. Errors arrive as HTTP 200 with an error body.

- [x] Task 4: implement the rate-limited Deezer client, including normalized
  identity checks, paginated tracks and HTTP-200 error payload handling.
- [x] Task 5: invoke Deezer only for Spotify misses, then create exactly one
  unmatched record only after both providers fail.
- [x] Task 6: carry the album's own provider URL through results, unmatched
  output and CSV, with visible provider attribution.
- **Acceptance:** with an invalid Spotify key, a job still returns release
  dates, art and links through Deezer. Deezer is never called when Spotify
  matched. An album neither provider matches produces one unmatched entry.
- **Blocker before it ships:** read Deezer's developer guidelines and record
  what they require for attribution and artwork. Their terms are
  non-commercial only; record that constraint in the README.
- **Accepted interim deviation:** Task 6 shipped text attribution. Official
  Spotify and Deezer logo assets remain tracked by F-B21-60 and F-B22-4.

### ~~WP-3 -- Original release years, backend~~ -- **DONE**

A MusicBrainz client at one request per second with a contact User-Agent, a
cache table of its own, cached corrections applied before results render, and
a single process-wide worker that corrects a capped set per job.

- [x] Task 7: implement the MusicBrainz release-group lookup with normalized
  artist/title matching, bounded retries and a contact-bearing User-Agent.
- [x] Task 8: apply cached original dates before release filtering and display,
  while preserving the provider date as `provider_release_date`.
- [x] Task 9: run one capped correction worker per process, persist both
  matches and confirmed misses, and expose `pending`, `running`, `done` or
  `skipped` state without delaying the album job.
- **Acceptance:** a cached original of 1977 against a provider date of 2011
  moves the album out of a 2011 filter with the reason naming both dates. A
  1977 filter keeps it and displays 1977. With no correction, provider behavior
  is unchanged. A job with the client disabled records `skipped` and makes no
  request.

### WP-4 -- Progressive disclosure, frontend

`GET /api/release_checks`, a status line, and per-row markers. A corrected
row stays in place, muted, showing the original year. Rows never move while
the page is open; moved-in albums are announced with a reload link.

- [x] Task 10: add the job-scoped release-check JSON endpoint.
- [ ] Task 11: poll that endpoint, stop in a terminal state and disclose
  corrections without mutating the live sort order.
- **Acceptance:** the gate proves no row moves when a marker lands, polling
  stops when the status is done or skipped, moved-in albums receive a reload
  action, and the page holds at 390px and 1280px.

### WP-5 -- Docs and close-out

README (the new environment variables, the MusicBrainz contact, the Deezer
constraint), `docs/architecture/runtime-system.md` (a release year may now
come from MusicBrainz), a PLAYBOOK entry per WP, then the standard close-out.

- [ ] Document every new environment variable and the MusicBrainz contact
  requirement.
- [ ] Record the Deezer non-commercial constraint and the runtime provider /
  correction data flow without duplicating source code.
- [ ] Run the complete test, frontend, pre-commit and docsync gates, archive
  this definition and close the batch through the standard procedure.

---

## Batch acceptance

- Spotify success does not call Deezer; Spotify failure allows Deezer to
  produce a fully attributed result.
- Metadata cache reads and writes round-trip either provider without requiring
  a Spotify ID, and existing Spotify cache rows remain valid.
- A cached 1977 original against a 2011 provider date drives both the filter
  decision and displayed date, with the 2011 date retained separately.
- MusicBrainz is disabled without a configured contact, respects the global
  one-request-per-second limit when enabled, and never blocks initial results.
- Live corrections are job-scoped, stop polling at a terminal state, remain
  accessible, and never reorder the open result list.
- The full Python suite, two-browser frontend gate, pre-commit suite and
  `doc_state_sync.py --check` all pass on the final documented state.

---

## Out of scope

- The Spotify export import. That is Batch 23.
- The artist spotlight redesign (F-B21-60). Attribution rules touch it, so
  WP-2 records what Deezer requires, and the redesign stays its own work.
- Any Spotify login. Apps without extended access serve at most 5 allowlisted
  users.

## Constraints

- **Never create a new Spotify app or Client ID**, and do not rotate the
  secret without cause: a new one loses the postponement F-B21-59 records.
- MusicBrainz blocks anonymous clients. With no contact configured, the
  client stays disabled rather than guessing.
- Standard library only for the new code; no new dependency.
