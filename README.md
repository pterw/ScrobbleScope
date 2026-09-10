# ScrobbleScope -- Your Last.fm Listening Habits Visualized

[![Quality Gate](https://github.com/pterw/ScrobbleScope/actions/workflows/test.yml/badge.svg)](https://github.com/pterw/ScrobbleScope/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
- [Key Implementation Highlights](#key-implementation-highlights)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Running the App](#running-the-app)
  - [Local Development with DB Cache](#local-development-with-db-cache)
  - [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Current Status & Roadmap](#current-status--roadmap)
- [Contributing](#contributing)
- [Development Methodology](#development-methodology)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Author & Contact](#author--contact)

## Features

### Top Albums

- Fetch scrobbles for a listening year and enrich albums with Spotify release
  dates, artwork, and track runtimes.
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

| Layer | Technology |
| --- | --- |
| Backend | Python 3.13, Flask, Gunicorn |
| Frontend | Jinja templates, CSS, JavaScript, Tailwind CSS 4 and daisyUI 5; the populated Unmatched report still uses Bootstrap during migration |
| Typography | Adobe Fonts: Akzidenz Grotesk, Instrument Serif, Gotham, Input Mono, Input Mono Narrow |
| APIs | Last.fm history and profile data; Spotify album and artist metadata |
| Async HTTP | `aiohttp`, `aiolimiter`, shared throttling and retry helpers |
| Database | Optional PostgreSQL cache through `asyncpg` |
| Validation | pytest, Playwright browser checks, Ruff, pre-commit, documentation and generated-CSS checks |
| CI | GitHub Actions Quality Gate, coverage threshold, and an advisory dependency audit |
| Hosting | Fly.io configuration in [fly.toml](fly.toml) and [Dockerfile](Dockerfile) |

Exact dependency versions live in [requirements.txt](requirements.txt) and
[requirements-dev.txt](requirements-dev.txt). The CI badge links to current
results rather than a manually maintained test or coverage count.

## Architecture

Flask starts a bounded background job for each accepted search. The browser
polls progress; completed results stay in job-scoped memory. Album processing
can reuse Spotify metadata from PostgreSQL, while Heatmap aggregates Last.fm
history directly.

```mermaid
graph LR
    A[Browser] -->|POST /results_loading or /heatmap_loading| B[routes.py]
    A -.->|GET /progress| B
    B --> C[repositories.py]
    B --> D[worker.py]
    D -.->|injected task| E[orchestrator.py]
    D -.->|injected task| F[heatmap.py]
    E --> G[lastfm.py]
    E --> H[spotify.py]
    E --> I[cache.py]
    F --> G
    I --> J[(PostgreSQL)]
```

Dotted task edges represent runtime dispatch, not imports: `worker.py` runs
callables supplied by the routes. See [the architecture guide](docs/ARCHITECTURE.md)
for the dependency graph and detailed pipeline sequences.

## Key Implementation Highlights

- **Job isolation:** UUID-keyed state and a lock keep searches separate. A
  bounded semaphore limits active jobs; configuration lives in
  [scrobblescope/config.py](scrobblescope/config.py).
- **Caching:** In-memory request caching reduces repeated HTTP work.
  PostgreSQL optionally stores Spotify album metadata between runs and
  application restarts; it does not persist the browser's result jobs.
- **Matching:** Artist, album, and track names are normalized before matching
  Last.fm scrobbles to Spotify metadata.
- **Request protection:** Flask-WTF protects POST requests, Jinja's `tojson`
  filter carries template data into JavaScript, and Results renders dynamic
  text with DOM text nodes.
- **Secret validation:** Production startup rejects missing, short, or known
  placeholder `SECRET_KEY` values. Development mode logs a warning instead.
- **Canonical navigation:** `/heatmap`, `/results`, and `/unmatched` recover
  session-associated runs. Explicit job IDs and legacy completion routes
  remain supported; `/api/unmatched` is the separate JSON endpoint.

## Getting Started

### Prerequisites

- Python 3.13 and Git.
- A [Last.fm API key](https://www.last.fm/api/account/create).
- A [Spotify Developer app](https://developer.spotify.com/dashboard) for album
  and artist enrichment.
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
   without PostgreSQL. Never commit `.env` or reuse its secret in a public
   example.

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

Use [the architecture guide](docs/ARCHITECTURE.md) for module relationships and
[the development guide](DEVELOPMENT.md) for tooling. This overview deliberately
omits per-file test counts and generated or machine-local files.

## Deployment

The repository includes a Fly.io configuration and Dockerfile. The configured
release command runs `init_db.py` before deployment to initialize the cache
schema. Credentials are supplied through deployment secrets.

See [DEPLOY.md](DEPLOY.md) for the deployment procedure, configuration location,
and validation checklist. Changes to the repository are not automatically a
release of the live site.

## Current Status & Roadmap

The UI migration is in progress. Home, Heatmap, loading, Results, error, and
empty-state pages use the new Tailwind/daisyUI presentation. The populated
Unmatched report still uses Bootstrap; its rebuild and stable exclusion-reason
codes remain planned work, followed by the final migration and accessibility
sweep.

[PLAYBOOK.md](PLAYBOOK.md#3-active-batch--next-action) owns the current work
order. [FINDINGS.md](FINDINGS.md) records known limitations and deferred work;
[GitHub issues](https://github.com/pterw/ScrobbleScope/issues) are the public
place to propose or discuss changes.

## Contributing

Bug reports and suggestions are welcome through
[GitHub issues](https://github.com/pterw/ScrobbleScope/issues).
For code contributions, see [CONTRIBUTING.md](CONTRIBUTING.md), and follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Development Methodology

ScrobbleScope uses a shared-document workflow for human and AI-assisted
contributions. [DEVELOPMENT.md](DEVELOPMENT.md) explains the approach and its
tradeoffs. Repository rules live in [AGENTS.md](AGENTS.md); the README remains
a guide to the product and local setup.

## License

MIT License -- see [LICENSE](LICENSE).

## Acknowledgements

- [Last.fm](https://www.last.fm/) for listening history.
- [Spotify](https://developer.spotify.com/) for music metadata.
- [Flask](https://flask.palletsprojects.com/), [Tailwind CSS](https://tailwindcss.com/),
  [daisyUI](https://daisyui.com/), and Bootstrap for the application UI foundations.
- The maintainers of the Python libraries and developer tools used here.

## Author & Contact

**Peter Wiercioch** (pterw)

- **GitHub:** [pterw](https://github.com/pterw)
- **Portfolio:** [peterwiercioch.com](https://peterwiercioch.com/)
- **LinkedIn:** [pter-w](https://www.linkedin.com/in/pter-w/)
- **Email:** hello@peterwiercioch.com
