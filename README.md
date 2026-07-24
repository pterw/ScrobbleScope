# ScrobbleScope -- Your Last.fm Listening Habits Visualized

[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)](https://github.com/pterw/ScrobbleScope)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-389_passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Try it live →](https://scrobblescope.fly.dev)**

ScrobbleScope is a web application for Last.fm users who want deeper insight into their listening habits. It offers two features on a single page, switchable via pill tabs:

* **Top Albums** -- fetches your scrobble history for a chosen year, filters and ranks albums by play count or total listening time, and enriches each album with Spotify metadata (release dates, artwork, track runtimes). The primary use case is building Album of the Year (AOTY) lists.
* **Scrobble Heatmap** -- renders a calendar-style grid of your daily listening density for the last 365 days. On desktop it reads as a GitHub-style 7x52 weeks-by-days calendar; on narrow viewports it falls back to a sequential activity strip with larger tap targets. No year picker needed; the grid is always current.

This project was initially built to identify top albums released in a specific year that were also listened to in that same year but has since been refactored into a more feature-rich web app, and is continuously maintained.

## Table of Contents

* [Features](#features)
* [Tech Stack](#tech-stack)
* [Architecture](#architecture)
* [Key Implementation Highlights](#key-implementation-highlights)
* [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Setup](#setup)
    * [Running the App](#running-the-app)
    * [Running Tests](#running-tests)
* [Project Structure](#project-structure)
* [Deployment](#deployment)
* [Current Status & Roadmap](#current-status--roadmap)
* [Contributing](#contributing)
* [Development Methodology](#development-methodology)
* [License](#license)
* [Author & Contact](#author--contact)

---

## Features

As mentioned above, ScrobbleScope currently offers two workflows on one page:

- **Top Albums** -- fetch a user's scrobbles for a chosen year, filter albums by
  release rules and listening thresholds, then rank them by play count or total
  listening time with Spotify metadata enrichment.
- **Scrobble Heatmap** -- render the last 365 days of listening activity as a
  calendar-style density view with KPIs, tooltips, and a mobile-friendly
  fallback layout.

A list of detailed features and explanations can be found below:
<details><summary><h4>Detailed Features </h4></summary>

* **Last.fm Integration:** Fetches your full listening history for a specified year via paginated `user.getrecenttracks` calls with granular per-page progress feedback.
* **Spotify Enrichment:** Searches each album on Spotify and fetches release dates, cover art, and individual track runtimes for playtime sorting.
* **Flexible Filtering:**
    * Filter albums by listening year.
    * Filter by release date: same year, previous year, specific decade, or a custom release year.
    * Configurable album thresholds (minimum track plays and minimum unique tracks per album). Set your own values -- defaults are 10 plays and 3 unique tracks if you don't specify.
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
* **Scrobble Heatmap:**
    * GitHub/Last.fm-Labs-style 7x52 calendar grid on desktop (one cell per day, last 365 days); sequential activity strip on narrow viewports (cells scale to viewport width with tap-friendly targets).
    * Result rendered as a self-contained artifact: warm cream / inky purple-dark frame, accent-coloured headline, four KPI stats (Total Scrobbles, Best Day, Active Days, Current Streak), top-right legend.
    * rocket_r colour palette (near-black → deep purple → red → orange → cream); log-adjusted intensity so sparse and heavy listeners both get readable gradients.
    * Zero-scrobble days rendered as muted cells so grid structure stays visible.
    * Hover/tap tooltip: day label + scrobble count ("Sunday 1 March 2026 -- 34 scrobbles").
    * Dark mode aware; responsive SVG scales to any viewport width and re-renders on breakpoint crossing.
    * Animated breathing/expanding pinwheel spinner + live page-fetch progress during data load.

 </details>

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, Flask 3.1, Gunicorn |
| Frontend | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 |
| APIs | Last.fm (`user.getrecenttracks`, `user.getinfo`), Spotify (search, album details) -- heatmap uses Last.fm only |
| Async HTTP | `aiohttp`, `aiolimiter` (per-loop rate limiters with jitter retry) |
| Database | PostgreSQL via `asyncpg` (optional -- Spotify metadata cache) |
| Security | Flask-WTF `CSRFProtect`, `\|tojson` XSS bridge, `escapeHtml()`, startup secret guard |
| Testing | pytest (389 tests across 24 files), ~72% coverage |
| CI/CD | GitHub Actions Quality Gate (pre-commit, pytest + coverage gate, pip-audit) |
| Deployment | Fly.io (shared-cpu-2x @ 512 MB, Postgres add-on) |
| Code Quality | pre-commit (black, isort, autoflake, flake8, trailing whitespace, fix end-of-files, check yaml, check-merge-conflict, detect-private-key, doc-state-sync) |

## Architecture

```mermaid
graph LR
    A[Browser] -->|POST /results_loading| B[routes.py]
    A -->|POST /heatmap_loading| B
    A -.->|GET /progress| B
    A -.->|GET /heatmap_data| B
    B --> C[repositories.py]
    B --> D[worker.py]
    D --> E[orchestrator.py]
    D --> F[heatmap.py]
    E --> G[lastfm.py]
    E --> H[spotify.py]
    E --> I[cache.py]
    F --> G
    I --> J[(PostgreSQL)]
```

<details>
<summary>Detailed request flow</summary>

```text
Top Albums
  index.html
    -> POST /results_loading
    -> create job + acquire worker slot
    -> start background_task(...) in a daemon thread
    -> loading.html polls GET /progress
    -> POST /results_complete renders results.html
    -> optional POST /unmatched_view renders unmatched.html

  orchestrator.background_task
    -> fetch Last.fm pages
    -> group + threshold albums
    -> enrich misses from Spotify
    -> optionally read/write Postgres cache
    -> persist results into JOBS

Heatmap
  index.html
    -> POST /heatmap_loading
    -> create job + acquire worker slot
    -> start heatmap_task(...) in a daemon thread
    -> heatmap.js polls GET /heatmap_data
    -> render SVG heatmap from stored daily_counts

  heatmap.heatmap_task
    -> fetch Last.fm pages for the last 365 days
    -> aggregate daily counts in UTC
    -> persist totals, max_count, and daily_counts into JOBS
```

</details>

**Key design decisions:**

* **Per-job state isolation:** UUID-keyed `JOBS` dict with `threading.Lock`. Progress, results, and unmatched data are scoped per job. Jobs expire after 2 hours.
* **Bounded concurrency:** `MAX_ACTIVE_JOBS` (default 10) caps background jobs via `BoundedSemaphore`. Excess requests are rejected before job creation.
* **Data normalization:** Artist and album names are cleaned of punctuation and common suffixes ("deluxe edition", "remastered") for robust Last.fm-to-Spotify matching.
* **Global rate limiting:** `_GlobalThrottle` in `utils.py` caps aggregate API throughput across all threads.
* **Acyclic module graph:** Leaf modules (`config`, `domain`, `errors`) have no internal imports. `orchestrator.py` sits at the top; `routes.py` imports only what it needs. See `AGENTS.md` for the full dependency graph.

## Key Implementation Highlights

* **Configuration:** API credentials and an optional `DEBUG_MODE` are controlled via a `.env` file. Concurrency, rate-limit defaults, and DB wake-up tolerance can be tuned via environment variables (`MAX_CONCURRENT_LASTFM`, `SPOTIFY_SEARCH_CONCURRENCY`, `SPOTIFY_REQUESTS_PER_SECOND`, `DB_CONNECT_MAX_ATTEMPTS`, `DB_CONNECT_BASE_DELAY_SECONDS`, etc.).
* **Caching:**
    * In-memory request cache (`REQUEST_CACHE` in `utils.py`, 1-hour TTL) to reduce repeated Last.fm fetches during active sessions.
    * Persistent Postgres metadata cache (`spotify_cache`) for Spotify album metadata across deploys/restarts, with configurable TTL via `METADATA_CACHE_TTL_DAYS` (default 30 days).
* **Security:** Template variables are injected into JavaScript via Jinja2's `|tojson` filter to prevent XSS. Dynamic content in the unmatched album modal is escaped with `escapeHtml()` before rendering.
* **CSRF Protection:** All mutating POST routes (`/results_loading`, `/results_complete`, `/unmatched_view`, `/reset_progress`) are protected via Flask-WTF `CSRFProtect`. Form submissions include a hidden `csrf_token` input; programmatic POSTs from `loading.js` read a `<meta name="csrf-token">` tag and inject the token into both form bodies and the `X-CSRFToken` header.
* **Doc-State Sync Tooling:** A modular Python package (`scripts/docsync/`) keeps orchestration docs (PLAYBOOK, SESSION_CONTEXT, archive) consistent across agent handoffs. Deterministic rotation, SHA-256 dedup, and cross-validation replace manual copy-paste that drifted in earlier sessions. See [DEVELOPMENT.md](DEVELOPMENT.md) for rationale.
* **Startup Secret Guard:** `create_app()` refuses to start in production when `SECRET_KEY` is absent, shorter than 16 characters, or set to a known-weak placeholder. `DEBUG_MODE=1` downgrades the failure to a logged warning for local development.
* **Route Helpers (SoC):** Business logic and data transforms are extracted from Flask route handlers into named module-level helpers (`_check_user_exists`, `_extract_job_params`, `_filter_results_for_display`, `_group_unmatched_by_reason`) so route handlers stay thin and helpers can be unit-tested independently.
<details>
<summary><strong>Styling & UX</summary></strong></summary>

   * **Dark Mode:** A toggle switch allows users to switch themes, with preferences persisted via `localStorage`. CSS custom properties (`--var`) are used for dynamic color adjustments.
   * **Animations:** Subtle fade-in animations are used for the logo, progress bar elements, and result cards to enhance visual feedback. Header logo features an animated SVG waveform, & the heatmap feat. uses a custom breathing SVG pinwheel animation while loading.
   * **Accessibility:** `aria-labels` on SVGs and interactive elements; semantic form markup.
   * **Favicon:** Multi-format icon (SVG with PNG & ICO fallbacks) ensures consistent branding.
   * **Static Assets:** CSS and JavaScript served from `/static` for cacheability and clean separation.
   * **Rotating loading messages:** Keeps users informed while data is being fetched.
   * **Personalized Loading Stats:** Live stats (scrobble count, albums found, Spotify matches) shown during processing.
   * **Onboarding:** First-visit welcome modal with "Info" button for returning users; contextual tooltip icons on form fields.
   * **Clickable Album Links:** Album names in results link directly to their Spotify page.

</details>

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
    python -m venv .venv
    ```
    * Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
    * Windows (Command Prompt): `.venv\Scripts\activate`
    * macOS/Linux: `source .venv/bin/activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements-dev.txt
    ```
    Runtime-only install (no dev tools):
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**

    Create a `.env` file in the project root (git-ignored). See `.env.example` for the template.

    ```env
    LASTFM_API_KEY="your_lastfm_api_key_here"
    SPOTIFY_CLIENT_ID="your_spotify_client_id_here"
    SPOTIFY_CLIENT_SECRET="your_spotify_client_secret_here"
    SECRET_KEY="your_random_secret_key_here"

    # Required in production (startup fails without a strong value).
    # Generate: python -c "import os; print(os.urandom(32).hex())"
    # For local dev, set DEBUG_MODE=1 to suppress the check.

    # Optional local Postgres cache
    # DATABASE_URL="postgresql://postgres:postgres@localhost:5432/scrobblescope"

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

Quick start:

```bash
python app.py
```

Browser-launching wrapper:

```bash
python run.py
```

The app will be available at `http://127.0.0.1:5000/`.

**Optional -- initialize Postgres schema** (only if using `DATABASE_URL` locally):

```bash
python init_db.py
```

### Local Development with DB Cache

To run the app locally with the persistent Postgres metadata cache enabled:

* Docker must installed and running.
* The `ss-postgres` container must exist (created once via `docker run`; see `AGENT_NOTES.md` Local Dev Setup section for the full command).
* `DATABASE_URL` should point at your local Postgres instance, for example:
  ```env
  DATABASE_URL="******localhost:5432/scrobblescope"
  ```
* If you run `init_db.py`, export `DATABASE_URL` in your shell first.

**One-command startup:**

```bash
python scripts/dev/dev_start.py
```

This checks whether `ss-postgres` is running, starts it if needed, then launches Flask.
`load_dotenv()` in the Flask startup picks up `DATABASE_URL` from `.env` automatically.

**Cache smoke test** (verify Postgres cache on a deployed instance):

```bash
python scripts/testing/smoke_cache_check.py --base-url https://scrobblescope.fly.dev \
    --username YOUR_USERNAME --year 2025 --runs 2
```

What to look for:
* `db_cache_enabled=True` indicates the app connected to Postgres for this run.
* `Run 2` should report `cache_hits > 0` once metadata has been persisted.
* `db_cache_persisted` should be non-zero on initial misses; `db_cache_lookup_hits` should grow on repeat runs.
* `Run 2` elapsed time should usually be lower than `Run 1`.
* The script prints `verdict=PASS` when the second run observes DB cache hits.
* If Fly Postgres uses `FLY_SCALE_TO_ZERO`, the first run after idle can be slower while the DB wakes up.

**Observe concurrent-user behavior** (fires N simultaneous job submissions):

```bash
python scripts/testing/concurrent_users_test.py \
    --concurrency 3 --base-url http://localhost:5000/ --username YOUR_USERNAME --year 2024
```

Reports per-thread outcome and aggregate statistics.
Set `--concurrency` above `MAX_ACTIVE_JOBS` (default 10) to observe semaphore-limit and queuing behavior.

### Running Tests

```bash
pytest -q
pytest --cov=scrobblescope --cov-report=term
pre-commit run --all-files
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
|   |-- orchestrator.py            # Album pipeline: fetch -> process -> results
|   |-- heatmap.py                 # Heatmap pipeline: fetch -> aggregate daily counts
|   `-- routes.py                  # Flask Blueprint, route + error handlers
|-- templates/
|   |-- base.html                  # Master template (nav, dark-mode toggle)
|   |-- index.html                 # Input form
|   |-- loading.html               # Progress polling page
|   |-- results.html               # Filtered album results
|   |-- unmatched.html             # Detailed exclusion report
|   |-- error.html                 # Error display
|   `-- inline/
|       |-- scrobble_scope_inline.svg  # Animated logo
|       `-- scrobblescope_pinwheel.svg # Animated heatmap loading spinner
|-- static/
|   |-- css/
|   |   |-- global.css             # Shared variables, dark-mode, toggle
|   |   |-- index.css
|   |   |-- loading.css
|   |   |-- results.css
|   |   |-- error.css
|   |   |-- unmatched.css
|   |   `-- heatmap.css            # Pill tabs, heatmap form, loading, result, tooltips
|   |-- js/
|   |   |-- theme.js               # Dark-mode init + toggle logic
|   |   |-- index.js               # Form validation, dynamic options
|   |   |-- loading.js             # Progress polling, rotating messages
|   |   |-- results.js             # CSV/JPEG export, modal, back-to-top
|   |   |-- error.js               # (stub -- logic moved to theme.js)
|   |   |-- unmatched.js           # (stub -- logic moved to theme.js)
|   |   `-- heatmap.js             # Pill switching, AJAX, polling, SVG grid, tooltips
|   `-- images/                    # Favicons (SVG, PNG, ICO)
|-- scripts/
|   |-- doc_state_sync.py          # PLAYBOOK/SESSION_CONTEXT sync (entry point)
|   |-- docsync/                   # Docsync package (parser, renderer, logic, CLI)
|   |   |-- cli.py                 # --check / --fix / --split-archive modes
|   |   |-- parser.py              # Section 4 entry parser + heading validation
|   |   |-- renderer.py            # STATUS block + archive rendering
|   |   |-- logic.py               # Rotation, dedup, cross-validation
|   |   `-- models.py              # Entry + BatchState dataclasses
|   |-- dev/
|   |   `-- dev_start.py           # One-command local dev startup (Postgres + Flask)
|   `-- testing/
|       |-- _http_client.py        # Shared HTTP transport (CSRF, submit, poll)
|       |-- smoke_cache_check.py   # Cache correctness smoke test (2-run DB hit check)
|       `-- concurrent_users_test.py  # Concurrent load observation (N threads, semaphore)
|-- tests/
|   |-- conftest.py                # Shared fixtures
|   |-- helpers.py                 # Test utilities
|   |-- test_app_factory.py        # App creation, secret validation (6)
|   |-- test_docsync_cli.py        # Docsync CLI + --fix/--check modes (19)
|   |-- test_docsync_logic.py      # Docsync archive rotation + dedup (41)
|   |-- test_docsync_parser.py     # Docsync PLAYBOOK parser (35)
|   |-- test_docsync_renderer.py   # Docsync status block renderer (21)
|   |-- test_domain.py             # Name normalization (13)
|   |-- test_heatmap.py             # Heatmap aggregation + task lifecycle (20)
|   |-- test_repositories.py       # Job state CRUD (20)
|   |-- test_retry_with_semaphore.py  # Retry + semaphore logic (8)
|   |-- test_routes.py             # Route handlers + helpers (67)
|   |-- test_utils.py              # Rate limiters, caching, formatting (34)
|   |-- test_worker.py             # Job slot + thread management (6)
|   |-- scripts/dev/
|   |   `-- test_dev_start.py              # Docker startup helper unit tests (11)
|   |-- scripts/testing/
|   |   |-- test_smoke_cache_check.py       # HTTP client + smoke test unit tests (13)
|   |   `-- test_concurrent_users_test.py   # Concurrency script unit tests (6)
|   `-- services/
|       |-- test_lastfm_logic.py       # Album aggregation logic (7)
|       |-- test_lastfm_service.py     # Last.fm client + progress (9)
|       |-- test_orchestrator_fetch_and_process.py  # Fetch pipeline (10)
|       |-- test_orchestrator_fetch_spotify.py      # Spotify fetch (8)
|       |-- test_orchestrator_helpers.py            # Result helpers (18)
|       |-- test_orchestrator_process_albums.py     # Album processing (7)
|       `-- test_spotify_service.py    # Spotify client + token mgmt (10)
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

## Current Status & Roadmap

ScrobbleScope is post-refactor and actively maintained. Core architecture and infra work are complete; the current focus is feature expansion and QA hardening.

**Planned Upcoming Work:**

* [ ] **Top songs:** Rank a user's most-played tracks for a given year (Last.fm + optional Spotify enrichment). Separate background task type with its own loading/results flow.
* [x] **Scrobble heatmap:** GitHub/Last.fm-Labs-style calendar grid showing daily listening density for the last 365 days. Last.fm API only (no Spotify). Vanilla SVG, rocket_r palette, hover/tap tooltips, dark mode, responsive. (Batch 18 end-to-end pipeline complete; Batch 19 added the framed result artifact, four KPI stats, accent-coloured headline, "Top Albums" pill rename, breathing-pinwheel loading polish, and a sequential mobile activity strip.)
* [ ] Decompose `scrobblescope/orchestrator.py` into smaller pipeline-focused modules.
* [ ] Add an integration test that exercises `/results_loading -> /progress -> /results_complete`.
* [ ] Consolidate Bootsrap CDN usage to asingle provider across templates.
* [ ] Improve the unmatched albums page (`unmatched.html`).
* [ ] Scope the next UI overhaul, consider tailwind + daisyUI

**Ongoing code quality tracking**

* [ ] Separation-of-concerns review: front-end JS and back-end route/service layers.
* [ ] DRY (Don't Repeat Yourself) violations across templates, JS, and Python modules.
* [ ] Data integrity checks: edge cases in aggregation, filtering, and normalization.
* [ ] Logic flaw review: identify silent failure modes and incorrect assumptions.
* [ ] Performance bottlenecks: profile hot paths under realistic load.
* [ ] General best-practices fixes surfaced by static analysis or audit tooling.

## Contributing

Feedback and suggestions are welcome! If you encounter bugs or have ideas, please [open an issue](https://github.com/pterw/ScrobbleScope/issues).

For code contributions, see [CONTRIBUTING.md](CONTRIBUTING.md). All participants are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development Methodology

ScrobbleScope was built with a shared-document, multi-agent workflow. The short version: repository rules live in `AGENTS.md`, active work lives in `PLAYBOOK.md`, current runtime state lives in `.claude/SESSION_CONTEXT.md`.

[DEVELOPMENT.md](DEVELOPMENT.md) explains the full approach: why external memory files exist, how `doc_state_sync.py` works and why it had to be a deterministic script rather than a prompt, the batch/work-package planning system, how code review suggestions were evaluated and rejected, and what failed before the current system stabilized.

## License

MIT License -- see [LICENSE](LICENSE) for details.

---

## Author & Contact

**Peter Wiercioch** (pterw)

* **GitHub:** [pterw](https://github.com/pterw)
* **Portfolio:** [peterwiercioch.com](https://peterwiercioch.com/)
* **LinkedIn:** [pter-w](https://www.linkedin.com/in/pter-w/)
* **Email:** hello@peterwiercioch.com
