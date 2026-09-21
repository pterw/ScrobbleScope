# ScrobbleScope -- Your Last.fm Listening Habits Visualized

[![Quality Gate](https://github.com/pterw/ScrobbleScope/actions/workflows/test.yml/badge.svg)](https://github.com/pterw/ScrobbleScope/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000.svg)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-4-38bdf8.svg)](https://tailwindcss.com/)
[![daisyUI](https://img.shields.io/badge/daisyUI-5-5a0ef8.svg)](https://daisyui.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-optional%20cache-336791.svg)](https://www.postgresql.org/)
[![Deployed on Fly.io](https://img.shields.io/badge/deployed-fly.io-8b5cf6.svg)](https://scrobblescope.fly.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

The Quality Gate badge tracks real gates rather than a snapshot of them: it
runs the Python suite, a coverage floor, Ruff, the documentation-integrity
checks and the browser gate on every push. Nothing on this page carries a
hand-maintained test or coverage number, because a number typed into a README
is wrong the next time anybody commits.

**[Try it live ->](https://scrobblescope.fly.dev)**

ScrobbleScope turns your public Last.fm listening history into album rankings
and a daily listening heatmap. Use it to build an Album of the Year list,
compare albums by listening time, or explore your listening patterns.

Choose **Top Albums** or **Heatmap** on Home. The shared navigation provides
Home, Heatmap, Results, and Unmatched; report destinations recover your latest
available run in the same browser session.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
  - [A search is an ETL pass over an event stream, not a query](#a-search-is-an-etl-pass-over-an-event-stream-not-a-query)
  - [How a search runs, end to end](#how-a-search-runs-end-to-end)
  - [The shared infrastructure in `utils.py`](#the-shared-infrastructure-in-utilspy)
  - [What each module owns](#what-each-module-owns)
- [Key Implementation Highlights](#key-implementation-highlights)
- [Owned Interface Components](#owned-interface-components)
  - [The heatmap is a hand-built SVG](#the-heatmap-is-a-hand-built-svg)
  - [The pinwheel is an owned component](#the-pinwheel-is-an-owned-component)
  - [The results export renders desktop on purpose](#the-results-export-renders-desktop-on-purpose)
  - [The artist spotlight is sampled, and never empty](#the-artist-spotlight-is-sampled-and-never-empty)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Running the App](#running-the-app)
  - [Local Development with DB Cache](#local-development-with-db-cache)
  - [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Current Status & Roadmap](#current-status--roadmap)
  - [What shipped most recently](#what-shipped-most-recently)
  - [Next: importing a Spotify listening history](#next-importing-a-spotify-listening-history)
  - [Known limitations](#known-limitations)
- [Contributing](#contributing)
- [Development Methodology](#development-methodology)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Author & Contact](#author--contact)

## Features

### Top Albums

- Fetch scrobbles for a listening year and enrich albums with release dates,
  artwork, and track runtimes from Spotify, falling back to Deezer for
  whatever Spotify cannot match or detail. Each album links to its own
  provider's page and carries a small attribution badge naming it.
- Include all release years, the listening year, the previous year, a decade,
  or a specific release year.
- Choose minimum track plays and unique tracks per album; the defaults are
  10 plays and 3 unique tracks. Limit the number of albums returned.
- Switch the leaderboard between track plays and estimated listening time
  without submitting another search. Listening time depends on available
  Spotify track durations.
- Explore Artist Spotlight, which samples up to five artists from the ten
  highest-scrobbled artists across your filtered results.
- Open an album on Spotify from its title; a delayed tooltip explains the link.
- Export CSV with the current ordering and full release dates, or save the
  complete leaderboard as a JPEG, including from a mobile viewport.
- Open the Unmatched report to inspect available exclusion reasons, such as
  release filters and missing Spotify matches. Albums dropped by the minimum
  listening thresholds are not retained as a separate near-miss list.

### Scrobble Heatmap

- Display the last 365 days of daily scrobbles, aggregated in UTC. Heatmap uses
  Last.fm only and needs no listening-year selection.
- Read a seven-row weekly calendar on desktop or a sequential grid with larger
  cells on narrow screens. Hover or tap a cell for its date and play count.
- See total scrobbles, daily average, best day, and current streak.
- Compare activity through the seven-stop `rocket_r` palette. Empty days remain
  distinct from the surrounding frame in both themes.
- Save the heatmap as a JPEG. This export uses a separate canvas layout rather
  than an exact screenshot of the page.

### Shared experience

- Light and dark themes, with the selection stored in the browser.
- Responsive typography and layouts, keyboard-accessible controls, and
  reduced-motion support for the page transitions and animated marks.
- A navbar that scrolls with the document; Results keeps its sorting controls
  and Top shortcut in the desktop side rail.
- Username validation, registration-year hints, and a public-listening-history
  check before processing starts.
- An animated pinwheel, a slim progress bar, and live operation labels with
  counts when the pipeline provides them. Album processing also shows pipeline
  statistics; Heatmap avoids repeating the same counts in a second panel.
- Recovery of recent results through the clean report routes. In-memory runs
  expire after two idle hours and do not survive an application restart.

## Tech Stack

| Layer | Technology | What it does here |
| --- | --- | --- |
| Backend | Python 3.13, Flask, Gunicorn | An application factory builds the app; Gunicorn serves it with one worker and four threads, because job state lives in that process's memory |
| Background work | `threading`, `asyncio` | Each search runs on a daemon thread with its own event loop, so a slow provider never blocks a request |
| Frontend | Jinja templates, vanilla JavaScript, Tailwind CSS 4, daisyUI 5 | No frontend framework and no build step to run the app: the compiled stylesheet is committed |
| Typography | Adobe Fonts: Akzidenz-Grotesk Next, Instrument Serif, Gotham, Input Mono, Input Mono Narrow | Loaded from a kit in the page shell; the wordmark itself is outline geometry in an inline SVG |
| Music data | Last.fm, Spotify, Deezer, MusicBrainz | Last.fm supplies listening history; Spotify then Deezer supply album metadata; MusicBrainz corrects release years |
| Async HTTP | `aiohttp`, `aiolimiter` | One pooled session per pipeline run, with a process-wide rate limiter and a retry helper per provider |
| Database | PostgreSQL through `asyncpg`, optional | Caches album metadata and original-release findings between runs; the app works without it |
| Validation | pytest, Playwright, Ruff, pre-commit | Unit, service and route tests, plus a real-browser gate that serves the app and drives Chromium and Firefox |
| Documentation checks | A typed integrity gate over the repository's own documents | Blocks a commit whose documents contradict each other or the code |
| CI | GitHub Actions | The Quality Gate runs the suite with a coverage floor, the linters, the documentation checks and an advisory dependency audit |
| Hosting | Fly.io ([fly.toml](fly.toml), [Dockerfile](Dockerfile)) | A single small shared-CPU machine; the release command initializes the cache schema |

Exact pinned versions are in [requirements.txt](requirements.txt) and
[requirements-dev.txt](requirements-dev.txt); every dependency is pinned with
`==` so a fresh checkout resolves to the versions CI ran.

## Architecture

ScrobbleScope is a Flask and Jinja monolith with two background pipelines,
in-memory job state, and an optional PostgreSQL cache. There is no queue
broker, no worker fleet and no client-side framework. That is a deliberate
fit to the workload: a search is one user's minute-long burst of rate-limited
API calls, and the machine it runs on is a single small Fly.io instance.

Flask accepts a search and starts a bounded background job for it; the
browser polls progress while the job runs, and a completed job's results
stay in server memory for the life of that run. A Top Albums job pulls a
year of scrobbles from Last.fm, then enriches each album with a release
date, artwork, and track runtimes: Spotify answers first, and Deezer
covers whatever Spotify cannot match or detail, so one provider's outage
no longer empties a result. Both providers date a remaster by its reissue,
so a separate MusicBrainz pass corrects release years to the original --
slowly, at one request per second, and therefore after the results are
already on screen rather than before. A Heatmap job aggregates Last.fm
history directly and skips enrichment. An optional PostgreSQL cache
remembers provider metadata and every correction across restarts, so the
same album is never re-fetched once any user has searched for it.

```mermaid
flowchart TB
    Form["Home form<br/>username, year, filters"] -->|POST| Flask[Flask route]
    Flask -->|take a slot, or refuse| Slot{{Job semaphore}}
    Slot -->|slot taken| Job[Background job thread]

    Job --> Scrobbles[Fetch a year of scrobbles<br/>Last.fm, paged and throttled]
    Scrobbles --> Group[Group into albums<br/>on normalized names]
    Group --> Threshold{Meets your play and<br/>track minimums?}
    Threshold -->|no| Unmatched[[Unmatched report]]
    Threshold -->|yes| Cache[(Metadata cache<br/>PostgreSQL, optional)]
    Cache -->|miss| Spotify[Spotify]
    Spotify -->|no match or no detail| Deezer[Deezer]
    Spotify -->|match| Build
    Deezer -->|match| Build[Build, filter and rank results]
    Deezer -->|no match| Unmatched
    Cache -->|hit| Build
    Build --> Results[[Results page]]

    Build -.->|queued, never awaited| Checks[Correction worker<br/>1 request per second]
    Checks -.-> MusicBrainz[MusicBrainz<br/>original release date]
    MusicBrainz -.-> Cache
    Checks -.->|marks rows in place| Results

    Browser([Your browser]) -.->|polls progress, then corrections| Flask
```

Dotted edges are the fallback path, the correction pass that runs after the
results are on screen, and the browser's progress polling -- none of them the
primary request flow.

### A search is an ETL pass over an event stream, not a query

This framing matters more than it sounds, because it is the reason the
codebase does not look like a CRUD app.

Last.fm stores **scrobbles**: an unbounded event stream of individual track
timestamps. It has no concept of the album a listener played. An "album" does
not exist upstream to be fetched -- it is *produced*, by grouping the stream on
a normalized `(artist, album)` key, then partitioning and threshold-gating the
groups on criteria the user chose. The same stream yields different album sets
depending on those thresholds, so the album is a function of the query rather
than a row in a table.

That has three consequences visible throughout the architecture:

- **Identity is resolved, not looked up.** Two providers name the same album
  differently, and Last.fm's own spelling varies. The normalized key is the
  join, so album identity is computed once and reused by the cache, every
  provider match, and every live correction.
- **PostgreSQL is a cache, not the domain's home.** It is a read-through layer
  with a 30-day TTL, and its purpose is to protect upstream rate limits and cut
  latency, not to hold the model. The application is correct with the database
  absent; `DATABASE_URL` blank is a supported configuration, and a search
  simply does every lookup live.
- **A job is a pipeline stage, not a transaction.** Progress is published per
  phase, failures are classified per provider, and the correction pass is
  queued after the results are already on screen rather than awaited. Holding a
  result set behind a one-request-per-second lookup would make the page slower
  than the API it is waiting on.

### How a search runs, end to end

1. **The form posts to Flask.** The username has already been checked while
   you typed: a small endpoint confirms the account exists, reports the year
   it was registered, and refuses a profile whose recent listening is private,
   because the pipeline cannot read one.
2. **A job slot is taken before a job exists.** A semaphore caps how many
   searches run at once. If every slot is busy the request is refused
   immediately rather than queued behind a minute of work, and the job is
   never created. The job gets a UUID, an entry in the in-memory store, and a
   daemon thread with its own asyncio event loop.
3. **Last.fm pages in.** The scrobbles for the chosen year arrive page by
   page, concurrently but under a global throttle, and are grouped into
   albums by normalized artist and album name. Every counter the loading page
   shows is published from here as the job's progress.
4. **The cheap exclusions happen before any money is spent.** Albums under
   your minimum play count or unique-track count are partitioned out and
   written straight to the unmatched report, and a hard cap of 500 albums
   applies to every sort mode. Neither ever reaches a metadata provider.
5. **The cache answers first.** Each remaining album is looked up in
   PostgreSQL by its normalized key. A hit is free and does not renew its own
   expiry, so a cached album is refetched 30 days after it was fetched rather
   than 30 days after it was last read.
6. **Spotify enriches the misses, then Deezer enriches Spotify's misses.**
   Both return the same provider-neutral record -- provider name, album id,
   album URL, release date, artwork, track durations -- so nothing downstream
   knows which one answered. Deezer needs no key. An album neither provider
   can identify produces exactly one unmatched entry, not two.
7. **Results are built, filtered and stored.** Release-year filtering,
   sorting by play count or estimated listening time, and the artist
   spotlight sample all happen here. Any original-release correction already
   in the cache is applied at this point, so it costs nothing and is visible
   in the first render.
8. **The page renders, and the corrections keep arriving.** A single
   process-wide worker asks MusicBrainz for the original release date of each
   album the cache does not know yet, at one request per second, capped per
   job. The results page polls for its findings and marks corrected rows in
   place. Nothing re-sorts while you are reading; albums that now qualify are
   announced with a reload link. Every finding is written to the cache,
   including "checked, nothing found", so the next search skips it.

A job's results live in memory for two idle hours and do not survive a
restart. Only the metadata cache is durable, and it holds facts about albums
-- never anything about you.

### The shared infrastructure in `utils.py`

Most of what makes the pipelines survive a bad provider day lives in one
module, so the clients stay thin:

- **A two-level rate limiter per provider.** A process-wide throttle
  serializes reservations across threads, and a per-event-loop limiter shapes
  the burst inside one job. Both are needed: the throttle alone cannot pace a
  burst, and the limiter alone would let four threads each run at the full
  rate. Last.fm and Spotify are held at 10 requests a second, Deezer at 10,
  MusicBrainz at 1 -- which is MusicBrainz's published limit per IP, and the
  reason the correction pass cannot be made faster.
- **A retry helper that understands the provider.** It honours `Retry-After`,
  backs off with jitter, asks the limiter again on every attempt rather than
  only the first, and can hold a semaphore for the duration.
- **One pooled `aiohttp` session per run**, with connection limits, timeouts
  and a shared header set, instead of a session per call.
- **A short-lived in-memory response cache**, so re-running the same year with
  different thresholds does not refetch a year of scrobbles.
- **`run_async_in_thread`**, which lets a synchronous Flask view await a
  coroutine on a private event loop without touching the request thread's
  state, and the duration formatters the results page and its CSV share.

### What each module owns

| Module | Responsibility |
| --- | --- |
| `app.py` | The application factory: configuration, CSRF, logging, blueprint registration, secret validation |
| `routes/` | One blueprint split by concern -- the home page, the album flow, the heatmap flow, and the small JSON endpoints. Handlers parse the request, start or read a job, and render |
| `worker.py` | The concurrency boundary: the job semaphore and thread startup. It runs a callable given to it and imports neither pipeline |
| `repositories.py` | The in-memory job store and every read and write to it, each under one lock |
| `orchestrator/` | The album pipeline, split by phase: search, details, cache, Deezer fallback, results |
| `heatmap.py` | The second pipeline: daily aggregation in UTC over the last 365 days, with no enrichment step |
| `lastfm.py`, `spotify.py`, `deezer.py`, `musicbrainz.py` | One module per external API, each owning that provider's quirks and nothing else |
| `enrichment.py` | The provider-neutral album record both metadata providers return |
| `release_checks.py` | The correction worker: one thread, a FIFO queue of jobs, and the rules for which albums are worth a lookup |
| `cache.py` | Every asyncpg call, with batch lookups, batch writes and connection retry |
| `domain.py` | Name normalization -- the keys everything else joins on |
| `unmatched.py` | The stable exclusion reason codes and the threshold partition |
| `spotlight.py` | Artist sampling for the results side rail |
| `utils.py` | The shared limiters, sessions, retries, caches and formatters described above |
| `errors.py` | Classified, user-facing error codes with their retryability |

## Key Implementation Highlights

- **Job isolation.** Every search is a UUID-keyed entry in one dictionary,
  and every read and write to it happens under a single lock. A bounded
  semaphore caps how many run at once; the cap is 5, chosen because a load
  test at 10 never completed while 2, 3 and 5 all ran clean.
- **Two caches, for two different problems.** An in-memory response cache
  removes repeated HTTP work inside a session. The optional PostgreSQL cache
  remembers album metadata and original-release findings across restarts and
  across users. Neither stores a result set: those are ephemeral by design.
- **The cache talks to Postgres in arrays, not rows.** A job's albums are
  looked up and written in single statements built on `unnest($1::text[], ...)`,
  so five hundred albums cost one round trip rather than five hundred. This is
  a hand-written primitive layer rather than an ORM saving records one at a
  time, and it is the reason a cold cache does not dominate a run.
- **A stale schema names itself.** A missing column or table answers with a
  PostgreSQL SQLSTATE (`42703`, `42P01`), and the cache reads that code
  specifically instead of treating every failure as network turbulence. The
  difference matters: an unmigrated database and a dropped connection look
  identical to a generic handler, and the first one needs a migration rather
  than a retry. Startup prints the exact `init_db.py` command to run.
- **A provider endpoint that disappears degrades instead of failing.** Spotify
  removed Get Several Albums for Development Mode apps, which answers with
  `403`, `404` or `410`. The batch fetch recognises those three statuses and
  falls back to one request per album, gathered concurrently, so album details
  keep arriving under the same rate limit instead of emptying the result.
- **Normalization is the join key.** Artist, album and track names are
  normalized once -- Unicode-normalized, punctuation flattened, release-noise
  words such as "deluxe" and "remastered" dropped from album titles only, so
  a band called New Edition survives. Every cache row, every provider match
  and every live correction is keyed on that pair.
- **Matching compares identity, not score.** Deezer's filtered search ranks a
  tribute single above the real album, and MusicBrainz will happily return a
  high-scoring wrong artist, so both clients require the normalized artist and
  title to match before accepting a candidate.
- **The provider's date is kept even when it is corrected.** A corrected album
  carries the original release date for filtering and display and the
  provider's own date beside it, because the latter is still right for the
  page the row links to.
- **Failure is a state, not an exception.** Missing credentials, provider
  errors, an unreachable cache and "checked, nothing found" each have an
  explicit outcome that the page can render. A correction pass that cannot run
  reports `skipped`; an album MusicBrainz cannot date is recorded as such so
  nobody looks it up again.
- **Request protection.** Flask-WTF protects every POST. Template data reaches
  JavaScript through Jinja's `tojson` filter as JSON in a script tag, and the
  results page builds dynamic text with DOM text nodes rather than HTML
  strings.
- **Secret validation.** Production startup rejects a missing, short or known
  placeholder `SECRET_KEY`. Development logs a warning instead of refusing to
  start.
- **Canonical navigation.** `/heatmap`, `/results` and `/unmatched` recover
  the latest run for the current browser session, so a reader who closes a tab
  can come back. Explicit job IDs still work, and the JSON endpoints
  (`/progress`, `/api/unmatched`, `/api/release_checks`,
  `/api/artist_spotlight`) are separate from the pages.

## Owned Interface Components

Three of the interface elements are built from scratch rather than pulled from
a library. That is not minimalism for its own sake: each one is a place where a
charting or animation dependency would have cost more than it saved, and each
had to satisfy a constraint a generic library does not know about.

### The heatmap is a hand-built SVG

There is no charting library and no `<canvas>` on the page. `static/js/heatmap.js`
constructs the grid as SVG nodes with `createElementNS`: a Monday-first weekly
calendar on desktop (`mondayIndex` normalises `getDay()` so week one does not
depend on the locale), 7 rows of days against 53 week columns, with month
labels tracking the column offsets. Narrow screens get a **separate sequential
grid** with larger cells rather than a squeezed copy of the weekly one, because
a 53-week grid is roughly 880px and cannot be made to work in a phone column.

Cell intensity is log-normalised, not linear:

```js
Math.log10(count + 1) / Math.log10(maxCount + 1)
```

A heavy listener's year is dominated by a handful of huge days. On a linear
scale almost every cell lands in the first stop of the ramp and the map reads
as blank. The logarithm is what makes the mid-range visible.

The colour comes from a seven-stop ramp (`ROCKET_STOPS`, sampled from
matplotlib's `rocket_r`) interpolated by `rocketColor(t)`. Two details are
load-bearing:

- **Zero-count cells are repainted from the active theme.** A cell carries its
  colour as an SVG `fill` *presentation attribute*, and a presentation
  attribute does not resolve a CSS custom property -- so the token is read and
  resolved in JavaScript before being assigned. Without that, the grid keeps
  its light-theme empties on a dark page, which is exactly the failure the
  browser gate later grew a check for.
- **The palette has one owner.** `heatmap.js` holds all seven stops;
  `tailwind.src.css` and `heatmap.css` derive from them rather than
  re-declaring them, so the tab accent and the grid cannot disagree.

The JPEG export is not a screenshot. The live SVG is cloned, given explicit
pixel dimensions, serialised to a data URI and drawn into a canvas at 2x
(`EXPORT_SCALE`), with a header laid out from named geometry constants. Two
problems this solves: an SVG carries no stylesheet, so the fonts and tokens
have to be inlined; and the export header is *read from the page* rather than
written into the export code, so the image cannot state something the page
does not.

### The pinwheel is an owned component

`scrobblescope_pinwheel.svg` with its animation in `shell.css` -- an inline
vector mark rather than a loader GIF or a JavaScript animation library, so it
inherits theme tokens, respects `prefers-reduced-motion`, and stays crisp at
any density.

### The results export renders desktop on purpose

The JPEG export of the results table forces the **desktop** markup visible
inside the clone (`html2canvas`'s `onclone` hook swaps the `.desktop-val` and
`.mobile-val` families), at `scale: 3`. A phone therefore produces a
desktop-faithful image. That is intentional: a table of album rows is far more
readable at full width, and an export is something a person keeps or shares
rather than reads in place.

Two constraints are handled explicitly. `html2canvas` 1.4 cannot parse the
`color()` function that `color-mix()` emits, so the page surface is rasterised
to an `rgb()` string first. And the CSV export reads a `data-export` attribute
rather than the cell's text, because the table rounds and the file should not.

### The artist spotlight is sampled, and never empty

`spotlight.py` aggregates the results by artist, ranks by play count and play
time, takes the top ten, and samples **five** -- seeded on the job id, so
re-running the same search does not reshuffle the panel under the user while a
fresh search does. It issues a separate request scoped to that sample, and if
any single image fails to load the album artwork already on the page is the
fallback, so the panel has no empty state to design for.

## Getting Started

### Prerequisites

- Python 3.13 and Git.
- A [Last.fm API key](https://www.last.fm/api/account/create).
- A [Spotify Developer app](https://developer.spotify.com/dashboard) for album
  and artist enrichment. Deezer, the fallback provider, needs no key; its
  terms permit non-commercial use only, which binds any future change to how
  this app is run.
- Optionally, a contact for [MusicBrainz](https://musicbrainz.org/), which
  corrects a reissue date to the album's original release date. Its policy
  requires a contact -- an email address or a URL -- in every request's
  User-Agent, so without `MUSICBRAINZ_CONTACT` the correction pass stays off
  and everything else behaves exactly as before.
- Docker only if you want the optional local PostgreSQL cache.

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/pterw/ScrobbleScope.git
   cd ScrobbleScope
   ```

2. Create the primary checkout's virtual environment:

   ```bash
   python -m venv .venv
   ```

   Activate it with `.\.venv\Scripts\Activate.ps1` in PowerShell,
   `.venv\Scripts\activate` in Command Prompt, or
   `source .venv/bin/activate` on macOS/Linux.

   Linked Git worktrees reuse this primary environment. Follow the worktree
   check in [AGENTS.md](AGENTS.md#session-bootstrap-in-order) to locate it;
   do not create a second environment in a linked worktree.

3. Install dependencies using the environment's pip:

   ```powershell
   # Windows
   .\.venv\Scripts\pip.exe install -r requirements-dev.txt
   ```

   ```bash
   # macOS/Linux
   .venv/bin/pip install -r requirements-dev.txt
   ```

   For a runtime-only installation, substitute `requirements.txt`.

4. Copy [.env.example](.env.example) to `.env`, fill in your API credentials,
   and replace the placeholder secret. Generate a secret in the activated
   environment with:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Set `DEBUG_MODE=1` for local development. Leave `DATABASE_URL` blank to run
   without PostgreSQL. Set `MUSICBRAINZ_CONTACT` to an email address or a
   URL you can be reached at to enable original-release corrections. Never commit `.env` or
   reuse its secret in a public example.

   The tuning variables -- per-provider rate limits and retry counts, the
   per-job correction cap, and the cache TTLs -- are read from the environment
   as well. [scrobblescope/config.py](scrobblescope/config.py) owns every name
   and its default; set one in `.env` only to override it.

### Running the App

Commands below assume the primary environment is activated. In a linked
worktree, use its qualified Python and tool paths as described in `AGENTS.md`.

```bash
python app.py
```

Open `http://127.0.0.1:5000/`. Alternatively, `python run.py` starts the app
and opens the browser.

The compiled stylesheet is already committed, so running the app requires no
Node project or frontend build. For CSS or template changes, use the
[frontend asset build procedure](DEVELOPMENT.md#frontend-asset-build).

### Local Development with DB Cache

Start Docker and create the local container once:

```bash
docker run -d --name ss-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=scrobblescope -p 5432:5432 -v ss-postgres-data:/var/lib/postgresql/data postgres:17
```

Set this value in `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scrobblescope
```

Initialize the schema once. `init_db.py` does not load `.env`, so pass the
connection string through the shell as well:

```powershell
# Windows PowerShell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/scrobblescope"
python init_db.py
```

```bash
# macOS/Linux
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/scrobblescope" python init_db.py
```

For subsequent starts:

```bash
python scripts/dev/dev_start.py
```

The helper starts the existing `ss-postgres` container if needed and then
launches Flask. [scripts/testing](scripts/testing) contains cache smoke checks
and concurrent-request probes for a running local instance.

### Running Tests

```bash
pytest -q
pytest --cov=scrobblescope --cov-report=term
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Browser setup and execution are documented in the
[frontend browser gate procedure](DEVELOPMENT.md#frontend-browser-gate).
The automated gate runs the complete Chromium matrix and a Firefox static
asset canary. Cross-browser visual review remains part of UI acceptance.

## Project Structure

```text
app.py                  Flask application factory and startup configuration
run.py                  Browser-launching development wrapper
init_db.py              PostgreSQL schema initialization
scrobblescope/          Routes, jobs, pipelines, API clients, cache and Spotlight
templates/              Page templates, empty states, shared partials and SVGs
static/css/             Theme source, generated Tailwind CSS and page styles
static/js/              Forms, progress, navigation, results, Spotlight and Heatmap
scripts/dev/            Local startup, asset builds, browser gate and worktree checks
scripts/testing/        Cache and concurrency probes
scripts/docsync/        Documentation synchronization and integrity checks
tests/                  Unit, service, route and tooling regression tests
docs/architecture/      Detailed request and dependency diagrams
docs/design/            Design snapshot and recorded implementation overrides
.github/workflows/      CI configuration
```

The `tests/` tree mirrors the package: `tests/services/` covers the API
clients and the pipeline phases, `tests/scripts/dev/` covers the developer
tooling itself, and the rest covers routes, templates and repositories. The
listing above omits generated and machine-local files -- the compiled
stylesheet's inputs, the browser binaries the gate downloads, and the local
virtual environment.

## Deployment

The repository includes a Fly.io configuration and Dockerfile. The configured
release command runs `init_db.py` before deployment to initialize the cache
schema. Credentials are supplied through deployment secrets.

See [DEPLOY.md](DEPLOY.md) for the deployment procedure, configuration location,
and validation checklist. Changes to the repository are not automatically a
release of the live site.

## Current Status & Roadmap

### What shipped most recently

**The interface is entirely Tailwind and daisyUI.** Home, Heatmap, loading,
Results, the Unmatched report, the error page and every empty state render on
it. Bootstrap is gone -- the framework, the legacy `global.css` and the
`.dark-mode` compatibility class -- and one theme signal remains, `data-theme`
on the root element, so one observer can follow it.

**The Unmatched report groups on reason codes, not prose.** A group no longer
splits apart because two albums were released in different years. Three
reasons ship today: albums you played in the selected year that fell under
your minimum play or unique-track count, albums outside the release window,
and albums neither metadata provider could identify. Each gets its own panel;
panels sit side by side on a wide screen and stack on a narrow one, and long
lists start at ten rows and open 25 at a time.

**Album enrichment no longer depends on one company.** Spotify answers first
and Deezer answers for whatever Spotify cannot match or detail, so a single
provider's outage no longer empties a result. Each row links to the provider
that actually answered for it and names it. This mattered more than it
sounds: Spotify withdrew the batch-album endpoint from development-mode apps
in February 2026 and postponed the removal for existing apps with no new
date, which is the only reason the old single-provider pipeline still worked.

**Release years are corrected to the original.** Spotify and Deezer both date
a remaster by its reissue, while a year filter means the year the album first
came out -- so a 2011 remaster of a 1977 album used to sit in 2011 and the
original was dropped. MusicBrainz carries the original on the release group,
and a background pass now applies it. It is slow by rule, one request per
second, so it never delays a result: the page renders, corrections land while
you read, and a corrected row stays where it is, marked, showing the year the
album first came out. Nothing re-sorts under you; albums that now qualify are
announced with a reload link. Every finding is cached, including "checked,
nothing found", so the next reader pays nothing for it.

### Next: importing a Spotify listening history

ScrobbleScope only works for Last.fm users today, and the next body of work
changes that. Spotify's API cannot supply lifetime history -- it returns the
last 50 plays and unranked "top items" with no counts or dates -- and full
API access has been restricted to registered businesses since May 2025, with
development-mode apps capped at five allowlisted users. A login would
therefore buy almost nothing, and it was rejected.

Instead, Spotify listeners will upload the **Extended Streaming History**
export they can request from their account's privacy page: a zip of JSON,
one row per stream since the account opened. The design is already settled:

- **No login, and nothing stored.** The upload is parsed in memory and
  discarded. IP address, user agent, username and country are dropped at
  parse time, and nothing is written to disk or to PostgreSQL.
- **One switch on the existing form**, with a separate page explaining how to
  request the export. Both album rankings and the heatmap work from either
  source.
- **A play counts when it ran 30 seconds or longer**, is music rather than a
  podcast, and is not from a private session.
- **Everything after aggregation is already source-agnostic**, because the
  pipeline joins on normalized artist and album names and has no Last.fm
  dependency past that point. That is what makes this feasible without a
  second pipeline.

The same work adds statistics that need no new API calls, for both kinds of
user: album completion ("9 of 12 tracks"), your most-played track on each
album and when you first heard it that year, a breakdown of how old the music
you listened to was, hours listened, and longest and current listening
streaks with your busiest weekday and hour.

### Known limitations

- A result set lives in server memory for two idle hours and does not survive
  a restart or a redeploy. The metadata cache is the only durable store.
- Estimated listening time depends on track durations a provider supplied;
  an album with none is ranked by play count only.
- The heatmap covers the last 365 days in UTC, including today. It is bounded
  by Last.fm's rate limit rather than by anything in this application, which
  is why it takes as long as it does.
- The correction pass is disabled unless a MusicBrainz contact is configured,
  because MusicBrainz's policy requires one in every request's User-Agent.
- Deezer's terms permit non-commercial use only. That binds any future change
  to how this application is run, not just to the code.

[GitHub issues](https://github.com/pterw/ScrobbleScope/issues) are the public
place to propose or discuss changes.

## Contributing

Bug reports and suggestions are welcome through
[GitHub issues](https://github.com/pterw/ScrobbleScope/issues).
For code contributions, see [CONTRIBUTING.md](CONTRIBUTING.md), and follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Development Methodology

ScrobbleScope is built in numbered batches of work packages, each with written
acceptance criteria agreed before any code is written, and each landing with
its own log entry explaining what was planned, what was actually built, and
where the two differed. Human and AI-assisted contributions share that same
paperwork.

The repository checks its own documentation the way it checks its code. A
typed integrity gate runs on every commit: it refuses a document set that
contradicts itself, a citation that no longer resolves, a claim the code has
outgrown, or a batch closed without the steps its own procedure requires.
That is unusual enough to be worth saying plainly -- it exists because this
project is developed across many short sessions, and a document that quietly
went stale costs more than a failing test.

**The tooling is larger than the application on purpose.** Rotation,
deduplication and cross-file consistency are *mechanisms* rather than rules an
agent is trusted to follow, because they were left unfollowed three times and
each lapse left a stale claim in the corpus. Around that sit a browser gate
that serves the real application across its viewport profiles in CI, and a
worktree guard whose diagnostics are typed rather than prose. None of it is
in-house for its own sake; each piece replaced a class of failure that review
alone had already failed to catch.

**It is also built to be lifted.** The guards, the documentation package, the
browser gate and the batch discipline are intended to leave this repository and
serve the next one, which is why the checks read their facts from a
declarations file instead of hard-coding them, prefer the standard library,
and fail with a path, a line and a remediation. That extraction is a scheduled
body of work rather than a side effect, and it is deliberately unfinished --
parts of it still name ScrobbleScope files, and making the rest generic before
there is a second consumer would buy abstraction rather than reuse.
[DEVELOPMENT.md](DEVELOPMENT.md) reports which parts are generic today, which
are still tied to this repository, and why.

[DEVELOPMENT.md](DEVELOPMENT.md) covers the tooling and its tradeoffs;
[CONTRIBUTING.md](CONTRIBUTING.md) covers sending a change.

## License

MIT License -- see [LICENSE](LICENSE).

## Acknowledgements

- [Last.fm](https://www.last.fm/) for listening history.
- [Spotify](https://developer.spotify.com/) for music metadata.
- [Deezer](https://developers.deezer.com/) for fallback music metadata.
- [Flask](https://flask.palletsprojects.com/), [Tailwind CSS](https://tailwindcss.com/),
  and [daisyUI](https://daisyui.com/) for the application UI foundations, and
  Bootstrap, which carried the interface before the Tailwind migration.
- The maintainers of the Python libraries and developer tools used here.

## Author & Contact

**Peter Wiercioch** (pterw)

- **GitHub:** [pterw](https://github.com/pterw)
- **Portfolio:** [peterwiercioch.com](https://peterwiercioch.com/)
- **LinkedIn:** [pter-w](https://www.linkedin.com/in/pter-w/)
- **Email:** hello@peterwiercioch.com
