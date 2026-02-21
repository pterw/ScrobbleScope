# ScrobbleScope - Your Last.fm Listening Habits Visualized

[![Status](https://img.shields.io/badge/status-work_in_progress-yellow.svg)](https://github.com/pterw/ScrobbleScope)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ScrobbleScope is a web application designed for Last.fm users to get a deeper insight into their music listening habits. It fetches your track scrobbles for a selected year, processes them with various filters, and enriches album data with metadata from the Spotify API. The primary goal is to help you visualize your top albums, especially for creating your Album of the Year (AOTY) lists, creating top listening charts, or simply exploring your musical journey through your years of scrobbling.

This project was initially built to identify top albums released in a specific year that were also listened to in that same year but has since been refactored into a more feature-rich web app.

## Table of Contents

* [Features](#features)
* [Screenshots](#screenshots)
* [Tech Stack & Implementation Details](#tech-stack--implementation-details)
    * [Core Technologies](#core-technologies)
    * [Key Implementation Highlights](#key-implementation-highlights)
* [Getting Started](#getting-started-work-in-progress)
    * [Prerequisites](#prerequisites)
    * [Setup](#setup)
    * [Project File Structure](#project-file-structure)
* [Current Status & Future Plans](#current-status--future-plans)
* [Contributing](#contributing)
* [License](#license)
* [Acknowledgements](#acknowledgements)
* [Author & Contact](#author--contact)

## Features

* **Last.fm Integration:** Fetches your listening history for a specified year.
* **Spotify Metadata:** Enriches album data with release dates, cover art, and track runtimes from Spotify.
* **Flexible Filtering:**
    * Filter albums by listening year.
    * Filter albums by their release date:
        * Same as the listening year.
        * Previous year.
        * Specific decades.
        * Custom specific release year.
    * Define album listening thresholds (minimum track plays and minimum unique tracks per album). Set your own values—defaults are 10 plays and 3 unique tracks if you don't specify.
* **Advanced Sorting:**
    * Sort your top albums by **total track play count**.
    * Sort by **total listening time** (calculated from the runtime of tracks you've listened to).
* **Dynamic UI:**
    * User-friendly interface with options that appear dynamically based on your selections.
    * Light and Dark mode support for comfortable viewing (toggle available on all pages).
    * Responsive design for usability on various devices. *(Note: Ongoing improvements for mobile responsiveness).*
* **Data Export:**
    * Export your filtered album list to a `.csv` file.
    * Save a snapshot of your results table as a `.jpeg` image.
* **Unmatched Album Insights:**
    * View a quick list of albums that were in your listening history but didn't match your selected filters via a modal.
    * Access a detailed report categorizing why albums were excluded (sticky navigation bar for easy access on this page).
* **Username Pre-Validation:** Real-time username validation on blur before submitting the form, catching typos early.
* **User Feedback:**
    * Loading indicators with progress updates during data fetching and processing.
    * Clear error messages and redirection for invalid inputs or API issues.
    * Rotating messages on the loading screen keep long fetches engaging.

## Screenshots

Here's a few screenshots of ScrobbleScope in action:

**1. Main Input Form (Dark Mode)**

*Configure your search with various listening and release date filters. Options for decades and custom thresholds (shown with defaults selected) appear dynamically based on user choices.*

![ScrobbleScope Input Form - Dark Mode](docs/images/index_dark_thresholds_decade.png) 

**2. Results Page - Album List (Light Mode)**

*View your filtered and sorted albums, here shown sorted by play count. Includes album art, artist, play count, and release date. Buttons for data export and accessing unmatched albums are visible.*

![ScrobbleScope Results - Light Mode](docs/images/results_light_playcount.png) 

**3. Results Page - Quick Unmatched Modal (Dark Mode)**

*Easily access a quick view of albums that didn't meet your filter criteria directly from the results page, shown here in dark mode.*

![ScrobbleScope Results with Unmatched Modal - Dark Mode](docs/images/results_dark_modal.png) 

**4. Detailed Unmatched Albums Report (Dark Mode)**

*Get a comprehensive list of albums that were excluded, categorized by the reason for exclusion. The filter summary at the top provides context for the excluded items.*
![ScrobbleScope Detailed Unmatched Report - Dark Mode](docs/images/unmatched_dark_top.png)

## Tech Stack & Implementation Details

ScrobbleScope is built with a focus on asynchronous operations for API interactions and a clean user experience.

### Core Technologies:

* **Backend:** Python 3.13, Flask
* **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 for responsive layout & components.
* **APIs:**
    * Last.fm API: `user.getrecenttracks` is used to gather scrobbles, paginated until the specified year's cutoff.
    * Spotify API: Used to search each album and fetch `release_date` for filtering, as well as artwork and track runtimes.
* **Core Python Libraries:**
    * `aiohttp` & `aiolimiter`: For asynchronous API calls. Rate limits are managed (Last.fm: 10 req/s, Spotify: 10 req/s) with built-in retry handling; Spotify retries include jitter. Concurrency and rate defaults are configurable via environment variables.
    * `asyncpg`: For persistent Postgres-backed Spotify metadata caching on deployed environments.
    * `Flask-WTF`: CSRF protection on all mutating POST routes via `CSRFProtect`.
    * `python-dotenv`: For managing API keys and configuration from a `.env` file (which also controls an optional `DEBUG_MODE`).
    * `Jinja2`: For server-side HTML templating.
    * `Flask`: Micro web framework.

### Key Implementation Highlights:

* **Configuration:** API credentials and an optional `DEBUG_MODE` are controlled via a `.env` file. Concurrency, rate-limit defaults, and DB wake-up tolerance can be tuned via environment variables (`MAX_CONCURRENT_LASTFM`, `SPOTIFY_SEARCH_CONCURRENCY`, `SPOTIFY_REQUESTS_PER_SECOND`, `DB_CONNECT_MAX_ATTEMPTS`, `DB_CONNECT_BASE_DELAY_SECONDS`, etc.).
* **Per-Job State Isolation:** Each search request creates a unique job (UUID-keyed, in-memory `JOBS` dict with thread-safe locking). Progress, results, and unmatched data are scoped per job, preventing cross-user state collisions on concurrent requests. Jobs expire after 2 hours.
* **Data Normalization:** Artist and album names are cleaned of punctuation and common suffixes (e.g., "deluxe edition", "remastered") for more robust matching between Last.fm data and Spotify search queries.
* **Caching:**
    * In-memory request cache (`REQUEST_CACHE` in `utils.py`, 1-hour TTL) to reduce repeated Last.fm fetches during active sessions.
    * Persistent Postgres metadata cache (`spotify_cache`) for Spotify album metadata across deploys/restarts, with configurable TTL via `METADATA_CACHE_TTL_DAYS` (default 30 days).
* **Security:** Template variables are injected into JavaScript via Jinja2's `|tojson` filter to prevent XSS. Dynamic content in the unmatched album modal is escaped with `escapeHtml()` before rendering.
* **Bounded Job Concurrency:** `MAX_ACTIVE_JOBS` (default 10, env-tunable) caps simultaneous background jobs via a `BoundedSemaphore` in `scrobblescope/worker.py`. Requests beyond the cap are rejected at the route before any job is created, and the concurrency slot is always released -- even on thread-start failure.
* **CSRF Protection:** All mutating POST routes (`/results_loading`, `/results_complete`, `/unmatched_view`, `/reset_progress`) are protected via Flask-WTF `CSRFProtect`. Form submissions include a hidden `csrf_token` input; programmatic POSTs from `loading.js` read a `<meta name="csrf-token">` tag and inject the token into both form bodies and the `X-CSRFToken` header.
* **Startup Secret Guard:** `create_app()` refuses to start in production when `SECRET_KEY` is absent, shorter than 16 characters, or set to a known-weak placeholder. `DEBUG_MODE=1` downgrades the failure to a logged warning for local development.
* **Styling & UX:**
    * **Dark Mode:** A toggle switch allows users to switch themes, with preferences persisted via `localStorage`. CSS custom properties (`--var`) are used for dynamic color adjustments.
    * **Animations:** Subtle fade-in animations are used for the logo, progress bar elements, and result cards to enhance visual feedback. The main logo is an animated SVG emulating a waveform.
    * **Accessibility:** Efforts have been made to improve accessibility, such as using `aria-labels` on SVGs and interactive elements.
    * **Favicon:** Multi-format icon (SVG with PNG & ICO fallbacks) ensures consistent branding.
    * **Static Assets:** CSS and JavaScript moved to /static for easier maintenance.
    * **Rotating loading messages:** Keeps users informed while data is being fetched.
    * **Personalized Loading Stats:** Live stats (scrobble count, albums found, Spotify matches) shown during processing.
    * **Onboarding:** First-visit welcome modal with "Info" button for returning users; contextual tooltip icons on form fields.
    * **Clickable Album Links:** Album names in results link directly to their Spotify page.

## Getting Started (Work in Progress)

This project is currently a work in progress. However, if you wish to run it locally:

### Prerequisites:

* Python (3.9+ recommended)
* Pip (Python package installer)
* Git

### Setup:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pterw/ScrobbleScope.git
    cd ScrobbleScope
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    Activate it:
    * Windows (Command Prompt): `venv\Scripts\activate`
    * Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
        *(If script execution is disabled, you may need to run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*
    * macOS/Linux (bash/zsh): `source venv/bin/activate`
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    * Create a `.env` file in the root directory of the project.
    * Add your API keys to this file. **Do NOT commit this file to Git.**
        ```env
        LASTFM_API_KEY="your_lastfm_api_key_here"
        SPOTIFY_CLIENT_ID="your_spotify_client_id_here"
        SPOTIFY_CLIENT_SECRET="your_spotify_client_secret_here"
        # Required in production (startup fails without a strong value)
        # Generate: python -c "import os; print(os.urandom(32).hex())"
        # For local dev without this set, run with DEBUG_MODE=1 to suppress the check.
        SECRET_KEY="your_random_secret_key_here"
        # Optional (required for persistent Spotify metadata cache)
        # DATABASE_URL="postgresql://..."
        # Optional DB wake-up retry tuning
        # DB_CONNECT_MAX_ATTEMPTS="3"
        # DB_CONNECT_BASE_DELAY_SECONDS="0.25"
        # Optional: For enabling more verbose logging
        # DEBUG_MODE="1"
        ```
5.  **Run the application (recommended):**
    ```bash
    python app.py
    ```
    Optional convenience launcher (opens browser too):
    ```bash
    python run.py
    ```
    The application should then be accessible at `http://127.0.0.1:5000/`.

6.  **Optional: initialize Postgres schema (only if using `DATABASE_URL` locally):**
    ```bash
    python init_db.py
    ```

### Cache smoke test (deployed instance):

To verify warm-cache behavior on Fly.io (example target: `flounder14`, listening year `2025`), run:

```bash
python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2
```

What to look for:
* `db_cache_enabled=True` indicates the app connected to Postgres for this run.
* `Run 2` should report `cache_hits > 0` once metadata has been persisted.
* `db_cache_persisted` should be non-zero on initial misses; `db_cache_lookup_hits` should grow on repeat runs.
* `Run 2` elapsed time should usually be lower than `Run 1`.
* The script prints `verdict=PASS` when the second run observes DB cache hits.
* If Fly Postgres uses `FLY_SCALE_TO_ZERO`, the first run after idle can be slower while the DB wakes up.

### Project File Structure:

```
.
|-- app.py                       # Flask app factory + logging config
|-- run.py                       # Optional local launcher (opens browser)
|-- init_db.py                   # Postgres schema setup (Fly release_command)
|-- fly.toml                     # Fly.io deployment config
|-- requirements.txt
|-- PLAYBOOK.md                   # Source-of-truth active handoff playbook
|-- EXECUTION_PLAYBOOK_2026-02-11.md  # Legacy shim; points to PLAYBOOK.md
|-- scrobblescope/
|   |-- config.py
|   |-- domain.py
|   |-- utils.py
|   |-- repositories.py
|   |-- worker.py
|   |-- cache.py
|   |-- lastfm.py
|   |-- spotify.py
|   |-- orchestrator.py
|   `-- routes.py
|-- templates/
|-- static/
|-- scripts/
|   |-- smoke_cache_check.py
|   `-- doc_state_sync.py
|-- tests/
|   |-- conftest.py
|   |-- helpers.py
|   |-- test_app_factory.py
|   |-- test_domain.py
|   |-- test_repositories.py
|   |-- test_routes.py
|   |-- test_utils.py
|   `-- services/
|-- docs/
|   |-- images/
|   `-- history/
|       |-- PLAYBOOK_EXECUTION_LOG_ARCHIVE.md  # Rotated dated playbook entries
|       `-- ...                                # Audits/changelogs/refactor notes
|-- README.md
|-- CONTRIBUTING.md
`-- CODE_OF_CONDUCT.md
```

## Current Status & Future Plans

ScrobbleScope is post-refactor and actively maintained. Core architecture and infra work are complete; the current focus is QA hardening and iterative UX improvements.

**Key areas for improvement and upcoming features:**

* [x] Refine and thoroughly test the playtime sorting calculation.
* [x] Fully implement and test custom album threshold filtering functionality.
* [x] Enhance the `loading.html` page with rotating messages during loading.
* [x] Implement working pre-commit specs and GitHub actions for CI pipeline.
* [x] Further optimize performance for users with very large listening histories.
* [x] Improve responsive design, especially for mobile devices (ongoing polish).
* [x] Write more comprehensive backend function docstrings and comments in `app.py`.
* [ ] Conduct thorough QA testing across different browsers and use cases.
* [x] Improve the landing page (`index.html`) copy to be more descriptive for new users.
* [x] Deploy to Fly.io (ephemeral VM, shared-cpu-2x @ 512MB).
* ~~[ ] Implement planned log rotation for `app_debug.log` to `oldlogs/`.~~
* [x] Used RotatingFileHandler and start-up banner to delineate session logs, logsize = 1MB max.
* [x] Per-job state isolation for concurrent user safety.
* [x] Username pre-validation endpoint (`/validate_user`).
* [x] XSS-safe template data injection (`|tojson` bridge, `escapeHtml()`).
* [x] Loop-scoped rate limiters (fix `AsyncLimiter` reuse-across-loops warning).
* [x] Implement proper upstream failure classification and retry UX.
* [x] Personalized minimum listening year from Last.fm registration date.
* [x] Remove nested thread pattern in background task execution.
* [x] Persistent metadata layer (Postgres) to reduce repeated Spotify lookups across cold starts.
* [x] Modularize API calls into service modules (`lastfm.py`, `spotify.py`, `cache.py`, `orchestrator.py`).
* [x] Use Flask Blueprints to organize routes.
* [x] Consolidate helper functions into `utils.py`.
* [x] Move background processing to `orchestrator.py`.
* [x] Separate configuration into `config.py` for cleaner imports.
* [x] Optimize network usage via batching or parallel requests.
* [x] Create master HTML templates to reduce duplication.
* [x] Expand unit test coverage (async pipelines, error states, job isolation).
* [x] Add DB wake-up retry/backoff hardening for Fly Postgres scale-to-zero behavior.
* [x] Bounded background job concurrency with graceful capacity rejection (`MAX_ACTIVE_JOBS`, `scrobblescope/worker.py`).
* [x] Thread-safe in-memory request cache (`_cache_lock` in `utils.py`).
* [x] CSRF protection on all mutating POST routes (Flask-WTF `CSRFProtect`).
* [x] Hardened secret key: startup refuses weak or missing `SECRET_KEY` in production.
* [x] Server-side registration year validation (defense-in-depth; rejects year before user's Last.fm join date).
* [x] Removed artificial orchestration delays (2.5 s of fixed `asyncio.sleep` overhead eliminated).

**Confirmed upcoming features (planned, not yet started):**

* [ ] **Top songs:** Rank a user's most-played tracks for a given year (Last.fm + optional Spotify enrichment). Separate background task type with its own loading/results flow.
* [ ] **Listening heatmap:** Calendar-style scrobble density map for the last 365 days. Last.fm API only (no Spotify), lightweight background task.

**UI enrichments (planned, lower priority):**

* [ ] Replace top header logo with updated SVG.
* [ ] Animated SVG on loading page during Last.fm fetch phase (before Spotify progress bar appears).
* [ ] More dynamic loading progress bar.
* [ ] Personalized loading stats (e.g. average scrobble count per year alongside live fetch counts).
* [ ] Lock dark mode toggle to bottom of viewport (non-scrolling).
* [ ] Improved unmatched albums page (`unmatched.html`).

## Contributing
While this is currently a personal project, feedback and suggestions are welcome! If you encounter any issues or have ideas for improvement, please feel free to open an issue in this repository.

If you're considering making code contributions, please see our [Contributing Guidelines (CONTRIBUTING.md)](CONTRIBUTING.md) for more information on how to get started.

All contributors and participants in the ScrobbleScope project are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

* Last.fm for tracking all the music we listen to
* Spotify for letting me use their API
* Bootstrap for the clean front end
* Flask & the Flask community
* Contributors to the Python libraries used in this project.

---

## Author & Contact

Peter Wiercioch (pterw)

* **GitHub:** [pterw](https://github.com/pterw)
* **Creative Portfolio:** [peterwiercioch.com](https://peterwiercioch.com/)
  * *(Showcasing photography, writing, vector illustration, and graphic design)*
* **LinkedIn:** https://www.linkedin.com/in/pter-w/
* **Email:** hello@peterwiercioch.com

Feel free to reach out if you have any questions or feedback about ScrobbleScope, or to connect regarding other creative or technical projects!

