# BATCH22: Enrichment providers and original release years

**Status:** Active. Owner-approved 2026-09-13.
**Branch:** `feat/batch22-enrichment` (worktree off `test`).
**Baseline:** 1034 tests passing at batch open; the frontend gate runs 28
checks in 50 runs.
**Plan of record:**
`docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md` carries
every task, its tests and its exact commands. This file carries the scope,
the work packages and their acceptance criteria.

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

## Work packages

### WP-0 -- Module split, behaviour-neutral

`orchestrator.py` is 1,035 lines and `routes.py` is 985, against 361 for the
largest other module in their directories. AGENTS.md "Proposal and Design
Rules" item 3 compares a file to its largest peer, and F-B21-51 filed the
same complaint about `frontend_gate.py` at 9x.

- `routes.py` becomes a package of blueprints registered by `create_app`:
  pages, album flow, heatmap flow, JSON API. The rest of this batch adds a
  route and an endpoint, so the split comes first.
- `orchestrator.py` splits by phase: search, details, cache, results.
- **Both keep a facade.** Tests patch `scrobblescope.routes.X` and
  `scrobblescope.orchestrator.X` by name, and the precedent is
  `worktree_guard.py` and `_frontend_gate_results.py`.
- **Acceptance:** every existing test passes **unmodified**. That is the
  proof the split changed nothing. No behaviour change ships in this WP.

### WP-1 -- The provider contract

An `AlbumMetadata` value object, cache columns that any provider can fill,
and the Spotify calls moved behind the contract. `init_db.py` gains
`ALTER TABLE` statements: `CREATE TABLE IF NOT EXISTS` never alters an
existing table, and `spotify_id` is `NOT NULL` today.

- **Acceptance:** a Spotify-sourced result is byte-identical to today's, and
  the cache round-trips a row with its provider recorded.

### WP-2 -- Deezer as the fallback

A Deezer client and its wiring behind Spotify. Matching compares normalised
artist and title: the filtered search ranks a tribute single above the real
album. Track lengths come from `/album/{id}/tracks`, because the album
endpoint lists only 25. Errors arrive as HTTP 200 with an error body.

- **Acceptance:** with an invalid Spotify key, a job still returns release
  dates, art and links through Deezer. Deezer is never called when Spotify
  matched. An album neither provider matches produces one unmatched entry.
- **Blocker before it ships:** read Deezer's developer guidelines and record
  what they require for attribution and artwork. Their terms are
  non-commercial only; record that constraint in the README.

### WP-3 -- Original release years, backend

A MusicBrainz client at one request per second with a contact User-Agent, a
cache table of its own, cached corrections applied before results render, and
a single process-wide worker that corrects a capped set per job.

- **Acceptance:** a cached original of 1977 against a provider date of 2011
  moves the album out of a 2011 filter with the reason naming both dates. A
  job with the client disabled records `skipped` and makes no request.

### WP-4 -- Progressive disclosure, frontend

`GET /api/release_checks`, a status line, and per-row markers. A corrected
row stays in place, muted, showing the original year. Rows never move while
the page is open; moved-in albums are announced with a reload link.

- **Acceptance:** the gate proves no row moves when a marker lands, polling
  stops when the status is done, and the page holds at 390px and 1280px.

### WP-5 -- Docs and close-out

README (the new environment variables, the MusicBrainz contact, the Deezer
constraint), `docs/architecture/runtime-system.md` (a release year may now
come from MusicBrainz), a PLAYBOOK entry per WP, then the standard close-out.

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
