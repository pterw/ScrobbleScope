# AGENTS.md: Instructions for AI Agents

This document provides instructions for interacting with the ScrobbleScope repository.

## Project Overview

ScrobbleScope is a Python-based Flask web application that allows users to visualize their Last.fm listening history. It fetches "scrobbles" for a given year, enriches the data with album metadata from the Spotify API, and displays the results in a filterable and sortable format.

## Required Session Bootstrap

Before making changes, read these files in order:

1. `.claude/SESSION_CONTEXT.md`
2. `PLAYBOOK.md`
3. `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md` (when Batch 9 is active)
4. `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (when the active playbook context is not sufficient)
5. `README.md`

The playbook is the source of truth for batch sequencing and completion status.

## Tech Stack

* **Backend**: Python 3.9+ (tested on Python 3.13.x), Flask
* **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
* **APIs**: Last.fm and Spotify
* **Asynchronous Operations**: `aiohttp` and `aiolimiter` for handling API calls.
* **Persistent Cache**: Postgres via `asyncpg` (optional locally, enabled in deploy)
* **Dependency Management**: `pip` and `requirements.txt`.
* **Testing & Linting**: `pytest`, `pre-commit`, `black`, `isort`, `flake8`.

## Environment Setup

To work with this project, you must set up a local development environment.

1.  **Virtual Environment**: Always work within a Python virtual environment.
    ```bash
    python -m venv venv
    ```
    Activate it:
    ```bash
    # Windows PowerShell
    .\venv\Scripts\Activate.ps1
    # macOS/Linux (bash/zsh)
    source venv/bin/activate
    ```

2.  **Install Dependencies**: Install all required packages from `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

3.  **API Keys & Secrets**: The application requires API keys to function. **You have access to these keys as environment variables.** Use `.env.example` as a template and create a `.env` file in the project root. Fill in the following keys; the application will not run without this file.
    ```env
    LASTFM_API_KEY="your_lastfm_api_key_here"
    SPOTIFY_CLIENT_ID="your_spotify_client_id_here"
    SPOTIFY_CLIENT_SECRET="your_spotify_client_secret_here"
    SECRET_KEY="a_random_secret_key_for_flask_sessions"
    # Optional locally, required for persistent deployed metadata cache
    # DATABASE_URL="postgresql://..."
    ```

## Network Access

This application **requires an active internet connection** to make API calls to the Last.fm and Spotify services. The environment you are in has this capability.

## Running the Application

You can run the application using either `run.py` or `app.py`.

* Recommended:
  ```bash
  python app.py
  ```

* Optional launcher (starts server and opens browser):
  ```bash
  python run.py
  ```

* Optional local DB schema init (only when using `DATABASE_URL`):
  ```bash
  python init_db.py
  ```
  The application will be available at `http://127.0.0.1:5000/`.

## Testing and Code Quality

This repository uses `pre-commit` hooks to enforce code style and quality. It also uses `pytest` for unit testing.

1.  **Run Pre-Commit Checks**: Before committing any changes, run the pre-commit hooks against all files. This ensures consistency with formatting (`black`), import sorting (`isort`), and other checks.
    ```bash
    pre-commit run --all-files
    ```
    If any checks fail, you must fix the reported issues and stage the files again before committing.

2.  **Run Tests**: Use `pytest` to run the test suite. The tests are located in the `tests/` directory.
    ```bash
    pytest
    ```

The CI pipeline defined in `.github/workflows/test.yml` runs these same checks. Ensure they pass locally before submitting a Pull Request.

## Key File Structure

* `app.py`: Thin Flask app factory entrypoint (`create_app()` + module-level `app` for Gunicorn).
* `init_db.py`: Postgres schema initializer used by Fly release command.
* `scrobblescope/`: Core modular application package (routes, orchestration, services, cache, repositories, domain/config).
* `requirements.txt`: A list of all Python dependencies.
* `.env`: **(You must create this)** Stores the API keys and secrets. It is ignored by git.
* `static/`: Contains all static assets (CSS, JavaScript, images).
* `templates/`: Contains all Jinja2 HTML templates for the application.
* `.pre-commit-config.yaml`: Configuration for the pre-commit hooks.
* `tests/`: Contains all unit tests.
* `docs/history/`: Historical audits, changelogs, and remediation plans.

## Commit Message Style

Use Conventional Commits with an imperative subject, for example:

```text
feat: add unit tests for route validation
fix: reject invalid registration year server-side
docs: update PLAYBOOK and session context after WP-5
```

Use a body when context is needed (why, impact, and scope).

## Markdown Authoring Rules

- Use ASCII-only characters in markdown files.
- Use ISO dates in logs: `YYYY-MM-DD`.
- Execution-log updates must include: scope, plan vs implementation, deviations (if any), validation, and forward guidance.
- If requirements are ambiguous, ask clarifying questions before updating process/state docs.
- Keep only the active log window in `PLAYBOOK.md`; rotate older dated entries into `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Use deterministic tooling for rotation/sync:
  - `python scripts/doc_state_sync.py --fix` after editing playbook/session state.
  - `python scripts/doc_state_sync.py --check` before commit.

## Required Documentation Updates

After any behavior, config, or process-contract change, update all applicable docs in the same work package:

- `PLAYBOOK.md` for active execution contract and batch log updates.
- `.claude/SESSION_CONTEXT.md` for current-state snapshot and risks.
- `README.md` for user/developer-facing setup or behavior changes.

## Pull Request Summaries

Keep PR descriptions concise. Summarize the main changes and mention any testing done.
