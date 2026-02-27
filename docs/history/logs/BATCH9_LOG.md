# Batch 9 Execution Log

Archived entries for Batch 9 work packages.

### 2026-02-20 - README refreshed (Batch 9 completions and roadmap)
- Scope: `README.md`.
- Changes:
  - Python badge updated from `3.9+` to `3.13+`.
  - Removed stale playtime-sorting caveat from Features section.
  - Tech Stack: `Python 3.x` -> `Python 3.13`; added `Flask-WTF` to Core Python
    Libraries bullet.
  - Key Implementation Highlights: added three bullets (Bounded Job Concurrency,
    CSRF Protection, Startup Secret Guard).
  - Project File Structure: added `worker.py`, `test_app_factory.py`,
    `test_utils.py`, `scripts/doc_state_sync.py`.
  - Current Status checklist: added six new `[x]` items for WP-1 through WP-6
    outcomes.
  - Added "Confirmed upcoming features" subsection (top songs, listening heatmap).
  - Added "UI enrichments (planned, lower priority)" subsection.
- Commit: `14f251a` docs: refresh README for Batch 9 completions and roadmap.
- Forward guidance: README is now accurate as of WP-6 completion. Next step is WP-7.

### 2026-02-20 - Comprehensive repo audit completed + Batch 9 remediation plan authored
- Scope: full-codebase audit (backend Python, frontend templates/JS/CSS, tests/CI/config/docs), plus operational handoff planning.
- Plan vs implementation:
  - Performed a severity-ranked audit focused on security, reliability, correctness, and optimization pathways.
  - Identified concrete high/medium/low findings with file-level references.
  - Authored actionable execution plan for next agent:
    - `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`
    - Includes WP-1..WP-8, acceptance criteria, and execution order.
  - Updated this playbook and session context to treat Batch 9 as the active next execution track.
- Validation:
  - `venv\Scripts\python -m pytest tests --cov=scrobblescope --cov-report=term-missing -q`: **66 passed**, overall coverage **72%**.
  - Coverage highlighted lower-tested hotspots used to seed Batch 9 work-package ordering (`lastfm.py`, `utils.py`, `spotify.py`, portions of `orchestrator.py`).
- Forward guidance:
  - Execute WP-1 and WP-2 first (highest reliability risk reduction).
  - Keep documentation synchronized after each work package per Section 8.

### 2026-02-20 - Batch 9 WP-8 completed (CI, lint, dependency hygiene)
- Scope: `.pre-commit-config.yaml`, `requirements.txt`, `requirements-dev.txt` (new), `.gitignore`, `.github/workflows/test.yml`.
- Plan vs implementation:
  - Fixed `check-yaml` pre-commit hook: changed `files: ^.*\.py$` to `files: ^.*\.(yaml|yml)$` so the hook validates YAML files rather than Python files. Removed `.github` from the global `exclude` pattern so `.github/workflows/test.yml` is now reachable by `check-yaml`.
  - Split runtime vs dev dependencies: moved `pre-commit`, `pytest`, `pytest-asyncio`, `pytest-cov` from `requirements.txt` into new `requirements-dev.txt`. Added `flake8` explicitly to `requirements-dev.txt`. `requirements-dev.txt` includes `-r requirements.txt` so a single install covers everything for dev.
  - Added `.coverage` to `.gitignore` (coverage artifact from pytest-cov runs).
  - Updated `.github/workflows/test.yml`: install step now uses `requirements-dev.txt`; removed redundant `pip install pre-commit` and `pip install flake8` lines (covered by requirements-dev.txt); added `--cov=scrobblescope --cov-fail-under=70` to pytest invocation.
- Deviations and why:
  - Coverage threshold set at 70% (current measured: ~72%) to provide a realistic floor without false-failing immediately; can be tightened once new feature coverage is added.
  - `flake8` added explicitly to `requirements-dev.txt` so the direct `flake8 --config .flake8` CI step can rely on it rather than pre-commit's isolated env.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (check yaml now runs against .yaml/.yml files and passes for `.pre-commit-config.yaml` and `.github/workflows/test.yml`).
  - `venv\Scripts\python -m pytest tests -q`: 94 passed (no regressions).
- Forward guidance:
  - Batch 9 remediation complete. Next tracks are product feature batches: **Top songs** (rank most-played tracks per year) and **Listening heatmap** (scrobble density calendar, Last.fm-only).
  - Coverage gate starts at 70%; aim to raise the threshold incrementally as new features gain test coverage.

### 2026-02-19 - Batch 9 WP-3 completed (CSRF protection for mutating POST routes)
- Scope: `requirements.txt`, `app.py`, `templates/index.html`, `templates/results.html`, `templates/loading.html`, `static/js/loading.js`, `tests/conftest.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added `Flask-WTF>=1.2.0` to `requirements.txt` (installed v1.2.2).
  - Added `CSRFProtect` to `app.py`: `csrf = CSRFProtect()` at module level, `csrf.init_app(application)` in `create_app()`, plus a `CSRFError` handler that returns a 400 with the `error.html` template and a user-facing message.
  - Added `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` inside the `<form>` element in `templates/index.html` and `templates/results.html` (unmatched_view form).
  - Added `<meta name="csrf-token" content="{{ csrf_token() }}">` to the `head_extra` block in `templates/loading.html`.
  - Updated `static/js/loading.js`:
    - Added `const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';` near the top (after the `window.SCROBBLE` destructure).
    - Prepended `form.appendChild(createHiddenInput('csrf_token', csrfToken));` as the first hidden input in both `redirectToResults()` and `retryCurrentSearch()`.
    - Added `'X-CSRFToken': csrfToken` to the headers of the `fetch('/reset_progress', ...)` call in the error handler.
  - Updated `tests/conftest.py`: added `application.config["WTF_CSRF_ENABLED"] = False` so all existing tests continue to pass without supplying tokens.
  - Added two CSRF tests to `tests/test_routes.py`:
    - `test_csrf_rejects_post_without_token`: creates a CSRF-enabled app client, POSTs without a token, asserts 400.
    - `test_csrf_accepts_post_with_valid_token`: GETs `/` to capture the token from the rendered HTML, POSTs with it, asserts 200 and `window.SCROBBLE` in response.
- Deviations and why: none.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8, trim, end-of-file).
  - `pytest -q`: 76 passed (2 new tests added).
- Forward guidance:
  - WP-4 (secret hardening) is the next work package.
  - The `WTF_CSRF_ENABLED = False` fixture override is intentional and standard; it must remain in `conftest.py` to keep all POST route tests free of token boilerplate.
  - Flask-WTF validates the token from `request.form['csrf_token']` for form POSTs and from `X-CSRFToken` header for XHR/fetch POSTs. Both paths are now covered.

### 2026-02-19 - Batch 9 WP-2 completed (thread-safe REQUEST_CACHE)
- Scope: `scrobblescope/utils.py`, `tests/test_utils.py` (new file).
- Plan vs implementation:
  - Added `_cache_lock = threading.Lock()` to guard all `REQUEST_CACHE` access in `utils.py`.
  - Wrapped `get_cached_response` in `_cache_lock` to eliminate TOCTOU between `key in REQUEST_CACHE` and `REQUEST_CACHE[key]`.
  - Wrapped `set_cached_response` in `_cache_lock` for atomic writes.
  - Wrapped the full iterate-and-pop sequence in `cleanup_expired_cache` in `_cache_lock` to prevent `RuntimeError: dictionary changed size during iteration`. Cache count and size captured inside the lock; logging calls happen outside to minimize hold time.
  - Created `tests/test_utils.py` (6 tests): cache hit, absent miss, expired miss, overwrite, cleanup correctness, and a concurrent-write-plus-cleanup stress test with 6 threads.
- Deviations and why: none.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: 74 passed (6 new tests in `test_utils.py`).
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (black auto-reformatted `utils.py` on first run; re-run confirmed clean).
- Forward guidance:
  - WP-3 (CSRF protection for mutating POST routes) is the next work package.
  - `_cache_lock` is importable from `scrobblescope.utils` if future tests or modules need to inspect or clear the cache safely.

### 2026-02-19 - Batch 9 WP-1 completed (bound background job concurrency)
- Scope: `scrobblescope/config.py`, `scrobblescope/repositories.py`, `scrobblescope/routes.py`, `scrobblescope/orchestrator.py`, `tests/test_routes.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Added `MAX_ACTIVE_JOBS = int(os.getenv("MAX_ACTIVE_JOBS", "10"))` to `config.py`.
  - Added `_active_jobs_semaphore = threading.BoundedSemaphore(MAX_ACTIVE_JOBS)` to `repositories.py`.
  - Added `acquire_job_slot()` (non-blocking acquire, returns bool) and `release_job_slot()` (safe release with over-release guard) to `repositories.py`.
  - In `routes.py` `results_loading`: capacity check runs after `cleanup_expired_jobs()` and before `create_job()`; if at capacity, re-renders `index.html` with a retryable error message (no thread spawned, no job created).
  - In `orchestrator.py` `background_task`: `release_job_slot()` called in the `finally` block after `loop.close()`, guaranteeing release on all termination paths (success, handled exception, unhandled exception).
- Deviations and why:
  - Default of 10 (not lower) chosen to match existing concurrency constants and be tunable via `MAX_ACTIVE_JOBS` env var without code changes.
  - Capacity rejection renders `index.html` (same as other input validation errors) rather than a JSON 503, keeping the UX flow consistent with the existing form-submission error pattern.
- Additions beyond plan: none.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: 68 passed (2 new tests added: capacity-rejection route test + release-on-exception orchestrator test).
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8, trim, end-of-file).
- Forward guidance:
  - WP-2 (make `REQUEST_CACHE` thread-safe) is the next work package.
  - The `_active_jobs_semaphore` is process-global; it resets on restart. Under Fly.io single-VM deployment this is correct behavior.
  - If the operator wants to verify slot release under real traffic, check logs for `release_job_slot called with no matching acquire` warning (should never appear in normal operation).
