# AGENTS.md: Instructions for AI Agents

This document provides instructions for interacting with the ScrobbleScope repository.

## Project Overview

ScrobbleScope is a Python-based Flask web application that allows users to visualize their Last.fm listening history. It fetches "scrobbles" for a given year, enriches the data with album metadata from the Spotify API, and displays the results in a filterable and sortable format.

## Tech Stack

* **Backend**: Python 3.11, Flask
* **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
* **APIs**: Last.fm and Spotify
* **Asynchronous Operations**: `aiohttp` and `aiolimiter` for handling API calls.
* **Dependency Management**: `pip` and `requirements.txt`.
* **Testing & Linting**: `pytest`, `pre-commit`, `black`, `isort`, `flake8`.

## Environment Setup

To work with this project, you must set up a local development environment.

1.  **Virtual Environment**: Always work within a Python virtual environment.
    ```bash
    python -m venv venv
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
    ```

## Network Access

This application **requires an active internet connection** to make API calls to the Last.fm and Spotify services. The environment you are in has this capability.

## Running the Application

You can run the application using either `run.py` or `app.py`.

* Start the server and automatically open a browser:
  ```bash
  python run.py
  ```

* Or start the server directly:
  ```bash
  python app.py
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

* `app.py`: The main Flask application file containing all routes and core logic.
* `requirements.txt`: A list of all Python dependencies.
* `.env`: **(You must create this)** Stores the API keys and secrets. It is ignored by git.
* `static/`: Contains all static assets (CSS, JavaScript, images).
* `templates/`: Contains all Jinja2 HTML templates for the application.
* `.pre-commit-config.yaml`: Configuration for the pre-commit hooks.
* `tests/`: Contains all unit tests.

## Commit Message Style

Write commit messages as a single short imperative sentence, e.g., `Add unit tests`.

## Pull Request Summaries

Keep PR descriptions concise. Summarize the main changes and mention any testing done.
