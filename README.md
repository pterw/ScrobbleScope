<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/scrobble_scope_lockup_dark.svg">
    <img alt="ScrobbleScope" src="docs/assets/scrobble_scope_lockup_light.svg" width="420">
  </picture>
</h1>

Last updated: 2026-10-31

<p align="center"><strong>Your Last.fm listening habits, visualized.</strong></p>

[![Quality Gate](https://github.com/pterw/ScrobbleScope/actions/workflows/test.yml/badge.svg)](https://github.com/pterw/ScrobbleScope/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000.svg)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-4-38bdf8.svg)](https://tailwindcss.com/)
[![daisyUI](https://img.shields.io/badge/daisyUI-5-5a0ef8.svg)](https://daisyui.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-metadata%20cache-336791.svg)](https://www.postgresql.org/)
[![Deployed on Fly.io](https://img.shields.io/badge/deployed-fly.io-8b5cf6.svg)](https://scrobblescope.fly.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Try it live ->](https://scrobblescope.fly.dev)**

ScrobbleScope reads a public Last.fm listening history and turns it into three
views: a ranking of the albums you played most, a heatmap of every day of the
last year, and a streamgraph of your top artists week by week. Use it to build
an Album of the Year list, to compare albums by listening time, or to see when
you listen.

A search is not a database query. Last.fm stores individual plays, not albums,
so an album does not exist upstream: the app builds it by grouping a year of
plays on a normalized artist and album name, then applying the thresholds you
chose. The same plays give a different album list for different thresholds.

The app runs on one small Fly.io machine, so it keeps a bounded set of
background jobs and holds job state in memory, with no queue broker. Below are
the pipelines, what happens when a provider fails, the cache, the cost ceiling
and the stack. The details are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[DEPLOY.md](DEPLOY.md) and [DEVELOPMENT.md](DEVELOPMENT.md).

<table>
  <tr>
    <td><img src="docs/images/results_light_top_albums.png" alt="Top Albums results for flounder14, ranked by track plays, with the Artist Spotlight beside the list" width="400"></td>
    <td><img src="docs/images/unmatched_light_reasons.png" alt="The Unmatched report, grouping the albums left out of the results by reason" width="400"></td>
  </tr>
  <tr>
    <td><img src="docs/images/listening_light_export.jpg" alt="The saved heatmap and streamgraph for flounder14: a year of daily plays above weekly plays for the top ten artists" width="400"></td>
    <td><img src="docs/images/loading_light_albums.png" alt="The loading page while Last.fm pages arrive, with a progress bar and the search settings" width="400"></td>
  </tr>
</table>

## Architecture

Both forms start the same way. The form is checked first: Last.fm is asked
whether the user exists and whether their recent listening is public, and a
refusal costs no job. Then the app takes one of five job slots without waiting
(if none is free the request is refused, not queued) and starts a background
thread with its own asyncio event loop. The browser polls progress until the job
finishes.

```mermaid
flowchart TB
    subgraph Albums["Top Albums form: username, year, filters"]
        direction TB
        F1[Form] -->|POST| S1{{Take a job slot, or refuse}}
        S1 --> J1[Background job thread]
        J1 --> Fetch1["Last.fm: pages of the year's plays, throttled"]
        Fetch1 --> Group[Group plays into albums]
        Group --> Cache[(Metadata cache)]
        Cache -->|miss| Providers["Spotify, then Deezer"]
        Cache -->|hit| Results[[Top Albums results]]
        Providers --> Results
        Results -.->|after the page is shown| MB["MusicBrainz original release dates"]
    end

    subgraph Listening["Listening form: username only"]
        direction TB
        F2[Form] -->|POST| S2{{Take a job slot, or refuse}}
        S2 --> J2[Background job thread]
        J2 --> Fetch2["Last.fm: pages of the last 365 days, throttled"]
        Fetch2 --> Daily["Daily counts, UTC"]
        Fetch2 --> Weekly["Weekly counts, top 10 artists"]
        Daily --> Heat[[Heatmap]]
        Weekly --> Stream[[Streamgraph]]
    end
```

### Top Albums

The job fetches the year's plays from Last.fm, 200 per page. Page one goes
first and the rest fan out under a concurrency limit and a rate limit of 10
requests a second. Plays are grouped into albums, and albums below your minimum
plays or unique tracks go straight to the Unmatched report without reaching a
provider. At most 500 albums continue.

Each remaining album gets its metadata (release date, cover art, track
lengths). The cache answers first. For a miss, Spotify answers when its title
and credited artist match exactly; Deezer answers for what Spotify cannot match
or detail. An album that neither provider knows is listed in the Unmatched report
with the reason, and the "Include" choice keeps it in the ranking by play count
only.

Both providers date a remaster by its reissue, so a separate worker corrects
release years to the original through MusicBrainz. MusicBrainz allows about one
request a second, so the app starts requests at least 1.2s apart and does this
after the results are on screen. A corrected row is marked in place and nothing
re-sorts while you read.

### Heatmap

The Listening form needs only a username and starts its own job, separate from
a Top Albums search, with its own Last.fm fetch. It reads the last 365 days of
Last.fm plays (UTC), counts plays per day, and fills every day in the window,
with zero for a quiet day. It also computes the current streak, best day, daily
average and total. No Spotify, no Deezer and no database cache are involved.

The chart is hand-built SVG: no charting library and no canvas on the page.
Cell colour comes from a seven-stop ramp on a log scale of the daily count.
Narrow screens get a separate grid with larger cells, since a 53-week grid does
not fit a phone.

### Streamgraph

The streamgraph comes from the same job as the heatmap, with no extra Last.fm
call. The server counts plays per calendar week for the ten most played artists
in the window and groups every other play as "other". The browser stacks the
layers and draws smooth SVG paths, with the largest artist in the middle and a
faint halo showing the remaining plays. Hover, drag or use the arrow keys to
read a week. It shows on wide screens; narrow screens show the grid alone.

## Graceful degradation

The rule is that a provider that cannot answer is never read as "no match". A
"no match" is an answer. An outage is not. Each case has its own outcome that
the page can show:

- **Spotify fails for an album**: that album goes to Deezer and the page says
  so. If Spotify refuses repeatedly, a per-job breaker stops sending it
  requests and the rest go to Deezer.
- **Spotify removes an endpoint**: the batch details call answers 403, 404 or
  410, and the app falls back to one request per album.
- **Deezer cannot be read for an album**: it is listed as "could not be
  checked", not "no match".
- **A Last.fm page fails after its retries**: the run finishes and says how many
  pages were lost and that the results may be incomplete.
- **Last.fm is down at the start**: the form shows a retryable "try again"
  message and no job starts.
- **MusicBrainz or its contact setting is missing**: the results stay as they
  are and the page says the corrections were skipped.
- **The database is unreachable**: the run succeeds with every album treated as
  a miss, and the loading stats show a cache warning.
- **A bug no code classifies**: the page says the search stopped on our side
  and shows no exception text. Errors are classified by type, never by message.

Provider calls retry with backoff, honour `Retry-After` up to 30s, and ask the
rate limiter again on every attempt. Logs never carry a listener's artist,
album or track name, and the Last.fm API key is redacted from every line.

## The metadata cache

The cache is a PostgreSQL table of album metadata: cover art, release date,
track lengths, and the provider's album id and link. It never holds a listening
fact, so one row serves every user. The key is the normalized artist and album
name that every provider match and correction also uses. A second table holds
MusicBrainz findings, including "checked, nothing found".

On a run, one query looks up every album key at once (a single round trip, using
`unnest` arrays rather than a query per album). A hit supplies metadata with no
provider call. Misses go through Spotify and Deezer, and one upsert writes the
new metadata back. Rows older than 30 days are ignored and removed, and a hit
does not renew its row. If every album hits, the run makes no Spotify or Deezer
call. The Heatmap never touches the cache.

Measured on 2026-10-31, with the app on a development machine, a local
PostgreSQL database and the live providers, for the Last.fm user `flounder14`
and the listening year 2025 with default options: three cold runs (cache table
emptied) took a median of 42.2s, and three warm runs took a median of 13.9s,
about three times faster. A cold run made 260 Spotify and 26 Deezer calls; a
warm run made 5 of each, because 243 of the 248 albums were hits. The remaining
time is mostly Last.fm: a warm run still fetches all 102 Last.fm pages of the
year. This is one machine on one day, not a guarantee, and provider latency
moves the numbers.

The app still runs without a database (a blank `DATABASE_URL` is a supported
setting), but then every search does every lookup live.

## Built for under $5 a month

The constraint is that the machine and the cache together stay under $5
a month on Fly.io. That is a ceiling, not a measured bill. It shaped the
engineering in these ways:

- **Slim image**: the Docker image starts from `python:3.13-slim` and installs
  only the runtime dependencies. The compiled stylesheet is committed, so the
  image needs no Node and no CSS build.
- **One worker, four threads, 512 MB**: the machine is a shared-CPU instance
  with 512 MB. Job state lives in one process's memory, so there is one
  Gunicorn worker; threads suit the I/O-bound work. Five job slots came from a
  load test where 2, 3 and 5 concurrent users ran clean and 10 never finished.
- **Scale to zero**: a watchdog thread stops the machine after 20 minutes with
  no request, no running job and no pending release check. The next request
  starts it again.
- **Fly's autostop is off**: a background job holds no inbound connection, and
  Fly's docs do not say whether that counts as load.
- **Lost state on exit**: results and the in-memory request cache are gone
  after a stop. A revisit shows "We couldn't find your results" rather than an
  error.
- **A durable cache in a separate app**: the Postgres cache is its own Fly app,
  so it survives the web machine stopping. The connection code retries with
  backoff, which tolerates a database that is still waking up.
- **Schema init as the release command**: the release command runs
  `init_db.py`, which creates the cache tables idempotently with retries. If it
  exits with an error, Fly rolls the deploy back.
- **Rate limits as a budget**: one machine shares every provider's limit across
  all jobs, so each provider has a process-wide throttle plus a per-job
  limiter. That is why corrections run after the results, not before.

Merging to `main` deploys to Fly.io. See [DEPLOY.md](DEPLOY.md) for the
commands, the MusicBrainz contact, the idle exit and the Deezer egress
incident.

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Backend | Python 3.13, Flask, Gunicorn | An application factory builds the app. One worker with four threads fits in-memory job state on a 512 MB machine |
| Background work | `threading` and `asyncio` | Each search runs on its own thread with its own event loop, so a slow provider never blocks a request |
| HTTP clients | `aiohttp`, `aiolimiter` | One pooled session per run, with a rate limiter and a retry helper per provider |
| Database | PostgreSQL through `asyncpg`, hand-written SQL | Batch reads and writes run as single statements using `unnest` |
| Frontend | Jinja templates, vanilla JavaScript, Tailwind CSS 4, daisyUI 5 | No framework and no JS build step; the compiled stylesheet is committed and a pre-commit hook fails on drift |
| Charts | Hand-built SVG | The heatmap and streamgraph are drawn as SVG by the app's own code, with no charting library |
| Data | Last.fm, Spotify, Deezer, MusicBrainz | Last.fm for history; Spotify then Deezer for album metadata; MusicBrainz for original release dates |
| Tests | pytest, Playwright, Ruff, pre-commit | Unit, service and route tests, plus a browser gate that serves the app and drives Chromium, with Firefox running only the static-assets checks |
| CI | GitHub Actions | The Quality Gate runs the suite with a coverage floor, linters, the documentation checks and an advisory dependency audit |
| Hosting | Fly.io | See the cost section above |

Every dependency is pinned with `==` in [requirements.txt](requirements.txt) and
[requirements-dev.txt](requirements-dev.txt), so a fresh checkout resolves to
the versions CI ran.

## How the repository stays honest

The Quality Gate runs on every pull request and on pushes to `main`. A
documentation-only pull request skips the browser job. Each commit runs
pre-commit, including a documentation integrity check that refuses documents
that contradict each other or the code. The browser gate serves the real app and
measures the real interface at phone, laptop and 4K sizes. The README carries
no test or coverage number on purpose: a number typed into a document is wrong
the next time anyone commits. [DEVELOPMENT.md](DEVELOPMENT.md) shows each tool
running.

## Getting started

### Prerequisites

- Python 3.13 and Git.
- A [Last.fm API key](https://www.last.fm/api/account/create).
- A [Spotify Developer app](https://developer.spotify.com/dashboard) for album
  and artist enrichment. Deezer needs no key; its terms permit non-commercial
  use only.
- Optionally, a contact (email or URL) for [MusicBrainz](https://musicbrainz.org/).
  Its policy requires one in every request's User-Agent, so without
  `MUSICBRAINZ_CONTACT` the correction pass stays off.
- Docker, only for the local PostgreSQL cache.

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/pterw/ScrobbleScope.git
   cd ScrobbleScope
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv .venv
   ```

   Use `.\.venv\Scripts\Activate.ps1` in PowerShell, `.venv\Scripts\activate` in
   Command Prompt, or `source .venv/bin/activate` on macOS or Linux. Linked Git
   worktrees reuse this environment; see
   [AGENTS.md](AGENTS.md#session-bootstrap-in-order).

3. Install dependencies (use `requirements.txt` for a runtime-only install):

   ```bash
   pip install -r requirements-dev.txt
   ```

4. Copy [.env.example](.env.example) to `.env`, add your API credentials and
   replace the placeholder secret. Generate one with:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Set `DEBUG_MODE=1` for local development and leave `DATABASE_URL` blank to
   run without PostgreSQL. Rate limits, retry counts, caps and cache lifetimes
   have defaults in [scrobblescope/config.py](scrobblescope/config.py); set one
   in `.env` only to override it.

### Run the app

```bash
python app.py
```

Open `http://127.0.0.1:5000/`. The compiled stylesheet is committed, so running
the app needs no Node project.

### Run with the local cache

Create the container once:

```bash
docker run -d --name ss-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=scrobblescope -p 5432:5432 -v ss-postgres-data:/var/lib/postgresql/data postgres:17
```

Set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scrobblescope`
in `.env`. Then create the tables once. `init_db.py` does not read `.env`, so
pass the URL through the shell:

```bash
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/scrobblescope" python init_db.py
```

On Windows PowerShell, set `$env:DATABASE_URL` to the same value first. After
that, `python scripts/dev/dev_start.py` starts the container if it is stopped
and launches Flask.

### Run the tests

```bash
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

`pytest -q` includes browser tests under `tests/frontend/`, so a local run needs
the Playwright Chromium build. DEVELOPMENT.md covers browser setup, the
frontend gate and the other tools.

## Where to go next

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): modules, request flow and the
  sequence diagrams.
- [DEPLOY.md](DEPLOY.md): Fly.io deployment, the idle exit and the Deezer
  egress incident.
- [DEVELOPMENT.md](DEVELOPMENT.md): how the project is built and which tools
  guard it.
- [CONTRIBUTING.md](CONTRIBUTING.md) and the
  [Code of Conduct](CODE_OF_CONDUCT.md): sending a change.
- [GitHub issues](https://github.com/pterw/ScrobbleScope/issues): bug reports
  and suggestions.

## Known limitations

- A result set lives in server memory for 2 hours after its last write, and
  sooner when the machine stops from idleness. It does not survive a restart or
  a deploy. The metadata cache is the only durable store.
- Ranking by listening time depends on track durations a provider supplied; an
  album with none is left out, and a note says how many.
- The Heatmap covers the last 365 days in UTC, including today, and takes as
  long as Last.fm's rate limit allows.
- Deezer's terms permit non-commercial use only.

## License

MIT License -- see [LICENSE](LICENSE).

## Acknowledgements

- [Last.fm](https://www.last.fm/) for listening history.
- [Spotify](https://developer.spotify.com/) and [Deezer](https://developers.deezer.com/)
  for album metadata, and [MusicBrainz](https://musicbrainz.org/) for original
  release dates.
- [Flask](https://flask.palletsprojects.com/), [Tailwind CSS](https://tailwindcss.com/)
  and [daisyUI](https://daisyui.com/) for the application foundations.
- The maintainers of the Python libraries and developer tools used here.

## Author and contact

**Peter Wiercioch** (pterw)

- **GitHub**: [pterw](https://github.com/pterw)
- **Portfolio**: [peterwiercioch.com](https://peterwiercioch.com/)
- **LinkedIn**: [pter-w](https://www.linkedin.com/in/pter-w/)
- **Email**: hello@peterwiercioch.com
