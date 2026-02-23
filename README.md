# ScrobbleScope -- Your Last.fm Listening Habits Visualized

[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)](https://github.com/pterw/ScrobbleScope)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-257_passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ScrobbleScope is a web application for Last.fm users who want deeper insight into their listening habits. It fetches your scrobble history for a chosen year, filters and ranks albums by play count or total listening time, and enriches each album with Spotify metadata (release dates, artwork, track runtimes). The primary use case is building Album of the Year (AOTY) lists, but it works equally well for exploring your musical journey across any year of scrobbling.

## Table of Contents

* [Features](#features)
* [Screenshots](#screenshots)
* [Tech Stack](#tech-stack)
* [Architecture](#architecture)
* [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Setup](#setup)
    * [Running the App](#running-the-app)
    * [Running Tests](#running-tests)
* [Project Structure](#project-structure)
* [Deployment](#deployment)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Acknowledgements](#acknowledgements)
* [Author & Contact](#author--contact)

## Features

* **Last.fm Integration:** Fetches your full listening history for a specified year via paginated `user.getrecenttracks` calls with granular per-page progress feedback.
* **Spotify Enrichment:** Searches each album on Spotify and fetches release dates, cover art, and individual track runtimes for playtime sorting.
* **Flexible Filtering:**
    * Filter albums by listening year.
    * Filter by release date: same year, previous year, specific decade, or a custom release year.
    * Configurable album thresholds (minimum track plays and minimum unique tracks). Defaults: 10 plays, 3 unique tracks.
* **Dual Sort Modes:**
    * Sort by **total track play count**.
    * Sort by **total listening time** (computed from Spotify track runtimes).
* **Responsive UI:**
    * Dynamic form -- options appear based on your selections.
    * Light / Dark mode toggle (persisted via `localStorage`), available on every page.
    * Responsive layout with mobile-optimized playtime abbreviations and table formatting.
    * Back-to-top button on results page.
* **Data Export:**
    * Export filtered album list to `.csv`.
    * Save a full-width snapshot of the results table as a `.jpeg` image (correct in both light and dark mode, full table captured even on mobile viewports).
* **Unmatched Album Insights:**
    * Quick modal listing albums that did not match your filters.
    * Dedicated detail page categorizing exclusion reasons with sticky navigation.
* **Username Pre-Validation:** Real-time Last.fm username check on blur, with personalized minimum listening year derived from the user's registration date.
* **Live Progress Feedback:**
    * Per-page Last.fm fetch progress (5--20%), per-album Spotify search progress (20--40%), per-batch enrichment progress (40--60%), and result-building phase (60--100%).
    * Rotating messages and live stats (scrobble count, albums found, Spotify matches) during processing.
    * Clear error classification with retry UX for transient upstream failures.
* **Onboarding:** First-visit welcome modal with an "Info" button for returning users; contextual tooltip icons on form fields.

## Screenshots

**1. Main Input Form (Dark Mode)**

*Configure your search with listening year, release date filters, decade selection, and custom thresholds.*

![ScrobbleScope Input Form - Dark Mode](docs/images/index_dark_thresholds_decade.png)

**2. Results Page (Light Mode)**

*Filtered and sorted albums with cover art, artist, play count, and release date. Export buttons and unmatched-album access visible.*

![ScrobbleScope Results - Light Mode](docs/images/results_light_playcount.png)

**3. Quick Unmatched Modal (Dark Mode)**

*Albums that did not meet filter criteria, accessible directly from the results page.*

![ScrobbleScope Results with Unmatched Modal - Dark Mode](docs/images/results_dark_modal.png)

**4. Detailed Unmatched Report (Dark Mode)**

*Comprehensive exclusion report grouped by reason, with filter summary context.*

![ScrobbleScope Detailed Unmatched Report - Dark Mode](docs/images/unmatched_dark_top.png)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, Flask 3.1, Gunicorn |
| Frontend | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 |
| APIs | Last.fm (`user.getrecenttracks`, `user.getinfo`), Spotify (search, album details) |
| Async HTTP | `aiohttp`, `aiolimiter` (per-loop rate limiters with jitter retry) |
| Database | PostgreSQL via `asyncpg` (optional -- Spotify metadata cache) |
| Security | Flask-WTF `CSRFProtect`, `\|tojson` XSS bridge, `escapeHtml()`, startup secret guard |
| Testing | pytest (257 tests), ~72% coverage |
| CI/CD | GitHub Actions (pre-commit, flake8, pytest + coverage gate) |
| Deployment | Fly.io (shared-cpu-2x @ 512 MB, Postgres add-on) |
| Code Quality | pre-commit (black, isort, autoflake, flake8, trailing whitespace, doc-state-sync) |

## Architecture

```
User submits form (index.html)
  -> POST /results_loading (routes.py)
    -> Creates job (UUID in JOBS dict, thread-safe)
    -> start_job_thread(background_task, ...) [worker.py]
    -> Renders loading.html with job_id

background_task (orchestrator.py, daemon Thread):
  -> asyncio event loop -> _fetch_and_process(...)
    1. Fetch Last.fm scrobbles (paginated, async, per-page progress)
    2. Group into albums, filter by thresholds
    3. process_albums (5-phase cache flow):
       a: DB connect + batch lookup (30-day TTL)
       b: Partition cache hits / misses
       c: Spotify search + detail fetch for misses (per-album progress)
       d: DB batch persist (conn.close() in finally)
       e: Build results -> set_job_results()

loading.js polls GET /progress?job_id=...
  -> 100% + no error -> POST /results_complete -> renders results.html
  -> error + retryable -> show Retry button
```

**Key design decisions:**

* **Per-job state isolation:** UUID-keyed `JOBS` dict with `threading.Lock`. Progress, results, and unmatched data are scoped per job. Jobs expire after 2 hours.
* **Bounded concurrency:** `MAX_ACTIVE_JOBS` (default 10) caps background jobs via `BoundedSemaphore`. Excess requests are rejected before job creation.
* **Two-tier caching:** In-memory `REQUEST_CACHE` (1-hour TTL, thread-safe via `_cache_lock`) for Last.fm responses; persistent Postgres `spotify_cache` (30-day TTL) for Spotify metadata.
* **Data normalization:** Artist and album names are cleaned of punctuation and common suffixes ("deluxe edition", "remastered") for robust Last.fm-to-Spotify matching.
* **Global rate limiting:** `_GlobalThrottle` in `utils.py` caps aggregate API throughput across all threads.
* **Acyclic module graph:** Leaf modules (`config`, `domain`, `errors`) have no internal imports. `orchestrator.py` sits at the top; `routes.py` imports only what it needs. See `AGENTS.md` for the full dependency graph.

## Getting Started

### Prerequisites

* Python 3.13+
* pip
* Git
* A [Last.fm API account](https://www.last.fm/api/account/create) (for `LASTFM_API_KEY`)
* A [Spotify Developer app](https://developer.spotify.com/dashboard) (for `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pterw/ScrobbleScope.git
    cd ScrobbleScope
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    ```
    * Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
    * Windows (Command Prompt): `venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`

    *(PowerShell may require: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*

3.  **Install dependencies:**
    ```bash
    pip install -r requirements-dev.txt   # includes runtime + pytest + pre-commit + lint
    ```
    Runtime-only (no dev tools):
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**

    Create a `.env` file in the project root (git-ignored). See `.env.example` for the template.

    ```env
    LASTFM_API_KEY="your_lastfm_api_key_here"
    SPOTIFY_CLIENT_ID="your_spotify_client_id_here"
    SPOTIFY_CLIENT_SECRET="your_spotify_client_secret_here"

    # Required in production (startup fails without a strong value).
    # Generate: python -c "import os; print(os.urandom(32).hex())"
    # For local dev, set DEBUG_MODE=1 to suppress the check.
    SECRET_KEY="your_random_secret_key_here"

    # Optional: persistent Spotify metadata cache (Postgres)
    # DATABASE_URL="postgresql://..."

    # Optional tuning
    # DB_CONNECT_MAX_ATTEMPTS="3"
    # DB_CONNECT_BASE_DELAY_SECONDS="0.25"
    # MAX_CONCURRENT_LASTFM="10"
    # SPOTIFY_SEARCH_CONCURRENCY="10"
    # SPOTIFY_REQUESTS_PER_SECOND="10"
    # MAX_ACTIVE_JOBS="10"
    # METADATA_CACHE_TTL_DAYS="30"
    # DEBUG_MODE="1"
    ```

### Running the App

```bash
python app.py
```

Or use the convenience launcher (also opens your browser):

```bash
python run.py
```

The app will be available at `http://127.0.0.1:5000/`.

**Optional -- initialize Postgres schema** (only if using `DATABASE_URL` locally):

```bash
python init_db.py
```

### Running Tests

```bash
pytest -q                                   # quick summary
pytest --cov=scrobblescope --cov-report=term # with coverage
pre-commit run --all-files                  # lint + formatting + doc sync
```

## Project Structure

```
.
|-- app.py                         # Flask app factory, logging, secret validation
|-- run.py                         # Convenience launcher (opens browser)
|-- init_db.py                     # Postgres schema init (Fly.io release_command)
|-- fly.toml                       # Fly.io deployment config
|-- Dockerfile
|-- requirements.txt               # Runtime dependencies
|-- requirements-dev.txt           # Dev/test/tooling (includes requirements.txt)
|-- pyproject.toml                 # Tool config (isort, pytest, pyright)
|-- AGENTS.md                      # AI agent bootstrap and contribution rules
|-- PLAYBOOK.md                    # Active handoff playbook (agent orchestration)
|-- scrobblescope/
|   |-- __init__.py
|   |-- config.py                  # Env var reads, API keys, concurrency constants
|   |-- errors.py                  # SpotifyUnavailableError, ERROR_CODES
|   |-- domain.py                  # normalize_name, normalize_track_name
|   |-- utils.py                   # Rate limiters, session pooling, request cache
|   |-- repositories.py            # JOBS dict, jobs_lock, job state CRUD
|   |-- worker.py                  # BoundedSemaphore, job slot management
|   |-- cache.py                   # asyncpg helpers (retry/backoff, batch ops)
|   |-- lastfm.py                  # Last.fm HTTP client (pure I/O, no state)
|   |-- spotify.py                 # Spotify HTTP client (search, batch details)
|   |-- orchestrator.py            # Pipeline: fetch -> process -> results
|   `-- routes.py                  # Flask Blueprint, route + error handlers
|-- templates/
|   |-- base.html                  # Master template (nav, dark-mode toggle)
|   |-- index.html                 # Input form
|   |-- loading.html               # Progress polling page
|   |-- results.html               # Filtered album results
|   |-- unmatched.html             # Detailed exclusion report
|   |-- error.html                 # Error display
|   `-- inline/
|       `-- scrobble_scope_inline.svg  # Animated logo
|-- static/
|   |-- css/
|   |   |-- global.css             # Shared variables, dark-mode, toggle
|   |   |-- index.css
|   |   |-- loading.css
|   |   |-- results.css
|   |   |-- error.css
|   |   `-- unmatched.css
|   |-- js/
|   |   |-- theme.js               # Dark-mode init + toggle logic
|   |   |-- index.js               # Form validation, dynamic options
|   |   |-- loading.js             # Progress polling, rotating messages
|   |   |-- results.js             # CSV/JPEG export, modal, back-to-top
|   |   |-- error.js               # (stub -- logic moved to theme.js)
|   |   `-- unmatched.js           # (stub -- logic moved to theme.js)
|   `-- images/                    # Favicons (SVG, PNG, ICO)
|-- scripts/
|   |-- smoke_cache_check.py       # Deployed cache verification tool
|   `-- doc_state_sync.py          # PLAYBOOK/SESSION_CONTEXT sync utility
|-- tests/
|   |-- conftest.py                # Shared fixtures
|   |-- helpers.py                 # Test utilities
|   |-- test_app_factory.py        # App creation, secret validation (6)
|   |-- test_doc_state_sync.py     # Doc sync script tests (81)
|   |-- test_domain.py             # Name normalization (13)
|   |-- test_repositories.py       # Job state CRUD (18)
|   |-- test_utils.py              # Rate limiters, caching, formatting (34)
|   |-- test_routes.py             # Route handlers + helpers (50)
|   `-- services/
|       |-- test_lastfm_service.py     # Last.fm client + progress (9)
|       |-- test_lastfm_logic.py       # Album aggregation logic (7)
|       |-- test_spotify_service.py    # Spotify client + token mgmt (10)
|       `-- test_orchestrator_service.py  # Pipeline + result building (29)
|-- docs/
|   |-- images/                    # Screenshots for README
|   `-- history/                   # Archived batch defs, audits, changelogs
|-- .github/
|   `-- workflows/
|       `-- test.yml               # CI: pre-commit + flake8 + pytest/coverage
|-- CONTRIBUTING.md
|-- CODE_OF_CONDUCT.md
|-- LICENSE
`-- README.md
```

## Deployment

ScrobbleScope is deployed on [Fly.io](https://fly.io) with a PostgreSQL add-on for persistent Spotify metadata caching.

```bash
fly auth login
fly launch --internal-port 8080
fly secrets set LASTFM_API_KEY=... SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=... SECRET_KEY=...
fly deploy
```

`init_db.py` runs automatically as a `release_command` before each deploy to ensure the schema is up to date (idempotent). See [DEPLOY.md](DEPLOY.md) for details.

**Cache smoke test** (verify Postgres cache on a deployed instance):

```bash
python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev \
    --username flounder14 --year 2025 --runs 2
```

`Run 2` should show `cache_hits > 0` and `verdict=PASS`.

## Roadmap

ScrobbleScope is post-refactor and actively maintained. Core architecture is stable; current focus is feature expansion and QA hardening.

**Upcoming features:**

* [ ] **Top songs:** Rank most-played tracks for a year (Last.fm + optional Spotify enrichment). Separate task type with its own loading/results flow.
* [ ] **Listening heatmap:** Calendar-style scrobble density map (Last.fm only, lightweight).
* [ ] Cross-browser QA testing.

**UI polish (lower priority):**

* [ ] Updated header SVG logo.
* [ ] Animated SVG on loading page during Last.fm fetch phase.
* [ ] More dynamic progress bar.
* [ ] Improved unmatched albums page layout.

**Recently completed:**

* [x] Granular per-page and per-album progress feedback across the full pipeline.
* [x] Responsive table formatting with mobile playtime abbreviations.
* [x] Full-width JPEG export that captures the complete table on mobile.
* [x] CSS variable consolidation (semantic `--surface-color`, `--border-color`, etc.).
* [x] `orchestrator.py` decomposition into named helpers (thin orchestrator pattern).
* [x] Theme CSS/JS consolidation (dark-mode logic deduplicated into `global.css` + `theme.js`).
* [x] Backend SoC: `lastfm.py` is now a pure HTTP client; all business logic in `orchestrator.py`.
* [x] Route helper extraction (`_get_validated_job_context`, `_get_filter_description`).
* [x] Global rate throttle, playtime album cap, bounded job concurrency.
* [x] Persistent Postgres metadata cache with retry/backoff for Fly scale-to-zero.
* [x] CSRF protection, startup secret guard, server-side registration year validation.
* [x] 257 tests across 10 test files, ~72% coverage.

## Contributing

Feedback and suggestions are welcome! If you encounter bugs or have ideas, please [open an issue](https://github.com/pterw/ScrobbleScope/issues).

For code contributions, see [CONTRIBUTING.md](CONTRIBUTING.md). All participants are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

MIT License -- see [LICENSE](LICENSE) for details.

## Acknowledgements

* [Last.fm](https://www.last.fm/) for tracking all the music we listen to
* [Spotify](https://developer.spotify.com/) for the metadata API
* [Bootstrap](https://getbootstrap.com/) for responsive UI components
* [Flask](https://flask.palletsprojects.com/) and the Flask community
* The maintainers of the Python libraries used in this project

---

## Author & Contact

**Peter Wiercioch** (pterw)

* **GitHub:** [pterw](https://github.com/pterw)
* **Portfolio:** [peterwiercioch.com](https://peterwiercioch.com/) -- photography, writing, vector illustration, and graphic design
* **LinkedIn:** [pter-w](https://www.linkedin.com/in/pter-w/)
* **Email:** hello@peterwiercioch.com

