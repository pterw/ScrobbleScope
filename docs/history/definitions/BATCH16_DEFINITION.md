# BATCH16: Script Hygiene, Local Dev Hardening, and Integration Testing

**Status:** In Progress
**Branch:** `wip/pc-snapshot`
**Baseline:** 320 tests passing

---

## Context

The local development environment requires several manual steps before agents can
run the app with the Postgres cache and exercise integration test scripts. The
primary smoke test script (`scripts/smoke_cache_check.py`) fails with HTTP 400
locally because it POSTs to `/results_loading` without a CSRF token (Flask-WTF
rejects unauthenticated POSTs). No script exists to observe the app's behavior
under concurrent user load, which is critical for validating the `MAX_ACTIVE_JOBS`
semaphore and worker queue ahead of horizontal scaling. Scripts live at the top
level of `scripts/` with no organizational structure, making the directory harder
to navigate as more tooling is added.

The purpose of this batch is to:
1. Organize scripts into purpose-scoped subdirectories (extending the pattern
   already established by `scripts/docsync/`).
2. Fix the CSRF bug blocking smoke tests and refactor for SoC/DRY -- shared HTTP
   client logic extracted so both smoke and concurrency scripts share one
   implementation with no duplication.
3. Add a one-command local dev startup helper so any agent can bring up Flask with
   the Postgres cache without manual Docker steps.
4. Add a concurrent-user test script to surface job-queue, semaphore, and
   cache-interaction behavior under load -- the primary signal for horizontal
   scaling readiness and edge-case discovery.
5. Add automated unit tests for all new and refactored scripts.

**Audit note (2026-03-03):** This definition was reviewed by a second agent
(GitHub Copilot / Claude Opus 4.6). The CSRF analysis was confirmed accurate.
The verdict stat key was corrected from `cache_hits` to `db_cache_lookup_hits`
(the DB-specific counter, more precise for cache validation). Size caps were
removed per owner instruction -- SoC/DRY compliance is the governing constraint.

---

## 1. Scope and goals

**Primary goals:**
- Create `scripts/testing/` subdirectory; move `smoke_cache_check.py` there
- Create `scripts/dev/` subdirectory for local dev utilities
- Extract shared HTTP concerns (`fetch_csrf_token`, `submit_job`,
  `poll_until_complete`) into `scripts/testing/_http_client.py` to eliminate
  duplication between scripts
- Fix the CSRF bug in `smoke_cache_check.py` so it runs without disabling CSRF
  protection; update verdict branch to use `db_cache_lookup_hits` (DB-specific
  cache hit counter)
- Add comprehensive docstrings and inline comments to all new and refactored
  functions
- Add `scripts/dev/dev_start.py`: checks and starts `ss-postgres` Docker container,
  then execs Flask -- one command for a fully working local dev environment with
  cache
- Add `scripts/testing/concurrent_users_test.py`: fires N simultaneous requests,
  reports per-thread outcome and aggregate results against the semaphore limit
- Add unit tests for `_http_client.py`, `smoke_cache_check.py`, and
  `concurrent_users_test.py` using mocked sessions (no live server required)
- Update README local dev section; update SESSION_CONTEXT and AGENTS.md references

**Out of scope:**
- Moving or modifying `scripts/doc_state_sync.py` or the `scripts/docsync/`
  package -- do NOT touch either
- Feature work (top songs, heatmap) -- owner-defined scope required
- TTL expiry smoke testing -- requires DB timestamp manipulation; future batch
  candidate
- Fly.io / production deployment changes
- Coverage increase beyond what the new tests naturally provide

---

## 2. Work Packages

### WP-0 (P0): Migrate scripts into purpose-scoped subdirectories

**Goal:** Establish `scripts/testing/` and `scripts/dev/` as the canonical homes
for integration test scripts and local dev utilities. Move `smoke_cache_check.py`
to `scripts/testing/`. No logic changes in this WP -- migration only.

**Files:**
- `scripts/testing/` -- create directory with `__init__.py` (empty; marks as
  importable package for test tooling)
- `scripts/testing/smoke_cache_check.py` -- moved from `scripts/smoke_cache_check.py`
  via `git mv`; no content changes
- `scripts/dev/` -- create directory with `__init__.py` (empty)
- `AGENTS.md` -- update any path references to `scripts/smoke_cache_check.py`
- `.claude/SESSION_CONTEXT.md` -- update any path references in Section 8

**Note:** `memory/MEMORY.md` (Claude Code external agent memory) is updated
alongside each WP by the executing Claude Code agent. It is not a repo file and
cannot be updated by other agents; it is excluded from formal acceptance criteria.

**Acceptance criteria:**
- `scripts/testing/smoke_cache_check.py` exists; `scripts/smoke_cache_check.py`
  is removed
- `git mv` used (preserves history)
- `pytest -q` passes (320 passed -- no test changes)
- `pre-commit run --all-files` passes
- All doc path references updated to new location

**Net tests:** +0
**Commit:** `refactor(scripts): migrate smoke_cache_check to scripts/testing/, create dev folder`

---

### WP-1 (P0): Extract _http_client.py and fix CSRF in smoke_cache_check.py

**Goal:** Split the HTTP-layer concerns out of `smoke_cache_check.py` into a shared
module `scripts/testing/_http_client.py`. Fix the CSRF token bug that prevents local
execution without disabling CSRF protection. Update the verdict branch to use
`db_cache_lookup_hits` (the DB-specific Postgres cache hit counter) rather than the
broader `cache_hits` key -- `db_cache_lookup_hits` is the correct signal for
validating whether the Postgres cache layer is functioning. Add comprehensive
docstrings to all functions in both files.

The leading underscore on `_http_client.py` marks it as an internal module -- not
intended to be executed directly, only imported by scripts in `scripts/testing/`.

**Files:**
- `scripts/testing/_http_client.py` -- new shared HTTP module containing:
  - Module-level docstring: explains the module's role as the shared transport
    layer for all testing scripts; notes it is internal (not a runnable script)
  - `fetch_csrf_token(session, base_url) -> str`:
    GETs the index page and extracts the CSRF token from the hidden form field
    (`<input name="csrf_token" value="...">`). The `requests.Session` object
    persists the session cookie, which Flask-WTF ties to the token server-side.
    Raises `RuntimeError` if the field is absent from the response HTML.
    Comprehensive docstring: purpose, parameters, return value, exceptions, note
    on session cookie persistence.
  - `submit_job(session, base_url, username, year, sort_by, release_scope,
    min_plays, min_tracks) -> str`:
    Calls `fetch_csrf_token`, then POSTs to `/results_loading` with the token
    included in form data. Extracts `job_id` from the `window.SCROBBLE` JS
    payload in the loading page HTML. Raises `RuntimeError` if the SCROBBLE
    payload is absent or has no `job_id` key.
    Comprehensive docstring: purpose, parameters, return value, exceptions, note
    on CSRF flow.
  - `poll_until_complete(session, base_url, job_id, timeout_seconds,
    poll_interval) -> dict`:
    Polls `/progress` until `progress >= 100` or timeout. Returns the final
    progress payload dict. Raises `RuntimeError` on unexpected HTTP status.
    Raises `TimeoutError` when the deadline is exceeded.
    Comprehensive docstring: purpose, parameters, return value, exceptions.
  - Inline comments on non-obvious logic (regex extraction, timeout arithmetic)

- `scripts/testing/smoke_cache_check.py` -- refactored to import from
  `_http_client`:
  - Remove `start_job()` and `poll_job()` (replaced by `_http_client` equivalents)
  - `run_once()` calls `_http_client.submit_job()` and
    `_http_client.poll_until_complete()`
  - `JOB_JSON_RE` regex constant moved to `_http_client.py` where it is used
  - Verdict branch updated: `second.stats.get("db_cache_lookup_hits", 0) > 0`
    (was `cache_hits`; `db_cache_lookup_hits` is the Postgres-specific counter
    and the correct signal for DB cache validation)
  - Retain `RunResult` dataclass, `print_run_summary()`, `build_parser()`,
    `main()`
  - Comprehensive docstrings on all retained functions

**Acceptance criteria:**
- `python scripts/testing/smoke_cache_check.py --base-url http://localhost:5000/
  --username <user> --year <year> --runs 2` completes without HTTP 400 when Flask
  runs with standard CSRF protection enabled (no `WTF_CSRF_ENABLED=False` in
  `.env`)
- Run 2 shows `db_cache_lookup_hits > 0` when Postgres cache is populated
- Verdict branch reads `db_cache_lookup_hits` (confirmed by grep)
- All functions in both files have comprehensive docstrings
- `pytest -q` passes (320 passed -- tests in WP-2)
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `refactor(testing): extract _http_client, fix CSRF, update verdict key, add docstrings`

---

### WP-2 (P1): Unit tests for _http_client.py and smoke_cache_check.py

**Goal:** Add automated regression coverage for the refactored HTTP client and
smoke-test logic. All tests use mocked `requests.Session`; no live server is
required. Tests must challenge real behaviour -- each test must fail if the
function under test is deleted (no vacuous tests per AGENTS.md).

**Files:**
- `tests/test_smoke_cache_check.py` -- new test file

**Tests to include:**

*_http_client -- fetch_csrf_token:*
- `test_fetch_csrf_token_returns_token_from_html` -- mock GET returns HTML
  containing `<input name="csrf_token" value="abc123">`; assert `"abc123"` returned
- `test_fetch_csrf_token_raises_when_field_absent` -- mock GET returns HTML with
  no csrf_token input field; assert `RuntimeError` raised

*_http_client -- submit_job:*
- `test_submit_job_returns_job_id` -- mock GET (CSRF) returning token HTML, mock
  POST returning HTML with valid `window.SCROBBLE = {"job_id": "xyz"}` payload;
  assert `"xyz"` returned
- `test_submit_job_raises_when_scrobble_absent` -- POST response HTML has no
  `window.SCROBBLE` block; assert `RuntimeError`
- `test_submit_job_raises_when_job_id_absent` -- `window.SCROBBLE` present but
  payload has no `job_id` key; assert `RuntimeError`

*_http_client -- poll_until_complete:*
- `test_poll_returns_on_progress_100` -- first poll returns `{"progress": 100}`;
  assert payload returned immediately without further calls
- `test_poll_raises_on_unexpected_status` -- mock response returns HTTP 500;
  assert `RuntimeError`
- `test_poll_raises_timeout_when_deadline_exceeded` -- mock always returns
  `{"progress": 50}`; timeout set to a small value; assert `TimeoutError` raised

*smoke_cache_check -- run_once:*
- `test_run_once_raises_on_job_error` -- progress payload contains
  `"error": true`; assert `RuntimeError` with error detail in message

*smoke_cache_check -- print_run_summary:*
- `test_print_run_summary_includes_key_fields` -- call with a `RunResult`;
  assert `db_cache_lookup_hits`, `elapsed`, and `job_id` appear in captured stdout

*smoke_cache_check -- build_parser:*
- `test_build_parser_defaults` -- parse empty `[]`; assert `base_url`, `username`,
  and `runs` match documented defaults

*smoke_cache_check -- verdict logic:*
- `test_main_verdict_pass_when_db_cache_hits_on_run_2` -- mock two runs where
  run 2 stats contain `db_cache_lookup_hits > 0`; assert `"verdict=PASS"` in
  captured stdout
- `test_main_verdict_inconclusive_when_no_db_cache_hits` -- run 2 stats contain
  `db_cache_lookup_hits == 0`; assert `"verdict=INCONCLUSIVE"` in captured stdout

**Acceptance criteria:**
- `pytest tests/test_smoke_cache_check.py -v` passes all 13 tests
- `pytest -q` passes (333 passed)
- Each test fails if the function under test is deleted (no vacuous tests)
- `pre-commit run --all-files` passes

**Net tests:** +13
**Commit:** `test(testing): add 13 unit tests for _http_client and smoke_cache_check modules`

---

### WP-3 (P0): Add scripts/dev/dev_start.py Docker+Flask startup helper

**Goal:** Provide a single entry point that any agent can run to bring up the full
local development environment (Postgres cache + Flask) without manual Docker steps.
Removes the need for agents to consult MEMORY.md or SESSION_CONTEXT for Docker
start procedures. Establishes `scripts/dev/` as the home for future dev utilities
(DB migration helpers, seed scripts, etc.) that upcoming feature work will need.

**Files:**
- `scripts/dev/dev_start.py` -- new script:
  - Module-level docstring: purpose (one-command local dev startup with DB),
    usage (`python scripts/dev/dev_start.py`), prerequisites (container must
    already exist; this script starts/checks only, does not create), note that
    this is local dev only and has no effect on Fly.io deployment
  - `check_container_status(container_name: str) -> str | None`:
    Runs `docker inspect --format={{.State.Status}} <name>`. Returns the status
    string (`"running"`, `"exited"`, `"paused"`) or `None` if the container does
    not exist. Raises `RuntimeError` if docker itself is not found on PATH.
    Comprehensive docstring: purpose, parameters, return value, possible status
    strings, None sentinel meaning, exception.
  - `start_container(container_name: str) -> None`:
    Runs `docker start <name>`. Raises `RuntimeError` on non-zero exit code.
    Comprehensive docstring.
  - `main() -> None`:
    Calls `check_container_status`; if `"running"` prints and continues; if
    `"exited"` or `"paused"` calls `start_container` then continues; if `None`
    prints a clear error with the `docker run` command location and calls
    `sys.exit(1)`. Then calls `os.execvp("python", ["python", "app.py"])` to
    replace the current process with Flask (inherits current env; `load_dotenv()`
    in Flask startup picks up `DATABASE_URL` from `.env` automatically).
    All status lines prefixed `[dev_start]` for grep-ability.
    Comprehensive docstring.
  - Inline comments on `os.execvp` usage (why execvp over subprocess: cleaner
    signal handling, Flask becomes the process rather than a child)
- `AGENTS.md` -- update Environment Setup: "For local dev with Postgres cache,
  use `python scripts/dev/dev_start.py` instead of `python app.py` directly."
- `.claude/SESSION_CONTEXT.md` -- update Section 8: replace manual Docker start
  step with `python scripts/dev/dev_start.py` reference

**Test exemption rationale:** `dev_start.py` is not tested with unit tests in this
WP. The script's logic is three-step subprocess orchestration: check Docker status,
conditionally start the container, exec Flask. Mocking `subprocess.run` and
`os.execvp` would require more test scaffolding than the script's logic warrants.
The script is validated by manual execution during this WP. If it grows beyond its
current single-responsibility, unit tests should be added in a future WP.
Per AGENTS.md "new helpers must have at least one adversarial test" -- this script
is a dev utility (not a production helper) and is explicitly deferred.

**Acceptance criteria:**
- `python scripts/dev/dev_start.py` when `ss-postgres` is stopped: starts the
  container, prints `[dev_start] started ss-postgres`, then launches Flask
- `python scripts/dev/dev_start.py` when `ss-postgres` is running: skips start,
  prints `[dev_start] ss-postgres already running`, then launches Flask
- `python scripts/dev/dev_start.py` when `ss-postgres` does not exist: prints
  error with instructions, exits 1
- `pytest -q` passes (333 passed -- no new tests this WP)
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `feat(dev): add dev_start.py to check and start Postgres container before Flask`

---

### WP-4 (P1): Add scripts/testing/concurrent_users_test.py and unit tests

**Goal:** Provide an observable end-to-end test of concurrent job submission against
the `MAX_ACTIVE_JOBS` semaphore and worker queue. Surfaces edge-cases in caching
under simultaneous load -- the primary signal for horizontal scaling readiness. The
project has no CI integration tests against a live DB; these scripts are the only
way to validate end-to-end cache behavior under concurrent access.

**Files:**
- `scripts/testing/concurrent_users_test.py` -- new script:
  - Module-level docstring: purpose (observe concurrency and semaphore behavior
    under load; not a pass/fail test but an observability and edge-case
    discovery tool), usage, note that results vary by machine and network
    conditions, reference to `MAX_ACTIVE_JOBS` in `scrobblescope/config.py`
  - `ConcurrentResult` dataclass: fields `thread_index: int`, `http_status:
    int | None`, `job_id: str | None`, `elapsed_seconds: float`,
    `final_state: str | None`, `error: str | None`; comprehensive docstring
    explaining each field
  - `run_thread(session, base_url, username, year, sort_by, release_scope,
    min_plays, min_tracks, timeout_seconds, poll_interval, thread_index,
    results, barrier) -> None`:
    Uses a `threading.Barrier` so all threads begin submission at the same
    instant (maximises chance of hitting semaphore limit). Calls
    `_http_client.submit_job` then `_http_client.poll_until_complete`. Catches
    all exceptions into `ConcurrentResult.error` so one failing thread does not
    abort the test. Appends result to shared `results` list.
    Comprehensive docstring: why Barrier, thread-safety note on list.append,
    exception handling rationale.
  - `print_thread_result(result: ConcurrentResult) -> None`:
    Prints one grep-friendly result line per thread with `[thread-N]` prefix.
    Comprehensive docstring.
  - `print_aggregate(results: list[ConcurrentResult]) -> None`:
    Prints summary: N submitted, N completed, N failed, elapsed range.
    Comprehensive docstring.
  - `build_parser() -> argparse.ArgumentParser`:
    Args: `--concurrency` (default 3), `--base-url`, `--username`, `--year`,
    `--min-plays`, `--min-tracks`, `--timeout-seconds`, `--poll-interval`.
    Comprehensive docstring.
  - `main() -> None`:
    Creates one `requests.Session` per thread (sessions are not thread-safe for
    concurrent use). Starts threads with a shared `Barrier`. Joins all threads.
    Prints per-thread results then aggregate. Comprehensive docstring.
  - Imports `submit_job` and `poll_until_complete` from `_http_client`
  - Does not import from `scrobblescope/` package (standalone tool)
  - Inline comments on Barrier usage, one-session-per-thread rationale

- `tests/test_concurrent_users_test.py` -- new test file:
  - `test_concurrent_result_dataclass_fields` -- instantiate `ConcurrentResult`
    with known values; assert all fields accessible and types are as declared
  - `test_run_thread_records_success` -- mock `submit_job` returning `"job-1"` and
    `poll_until_complete` returning `{"progress": 100, "status": "done"}`; assert
    result has `job_id == "job-1"`, `error is None`, `elapsed_seconds > 0`
  - `test_run_thread_records_error_on_exception` -- mock `submit_job` raising
    `RuntimeError("connection refused")`; assert `result.error` contains
    `"connection refused"` and script does not raise
  - `test_print_aggregate_counts` -- build list of 3 `ConcurrentResult` objects
    (2 with `error is None`, 1 with `error` set); assert captured stdout contains
    count indicating 2 completed and 1 failed
  - `test_build_parser_concurrency_default` -- parse `[]`; assert
    `args.concurrency == 3`
  - `test_main_launches_correct_thread_count` -- patch `threading.Thread` and
    `requests.Session`; call `main()` with `--concurrency 3`; assert `Thread`
    was instantiated 3 times

**Acceptance criteria:**
- `python scripts/testing/concurrent_users_test.py --concurrency 3
  --base-url http://localhost:5000/ --username <user> --year <year>` reports
  results for all 3 threads with `[thread-N]` prefix on each result line
- Output clearly shows completed vs failed threads
- `pytest tests/test_concurrent_users_test.py -v` passes all 6 tests
- `pytest -q` passes (339 passed)
- `pre-commit run --all-files` passes

**Net tests:** +6
**Commit:** `feat(testing): add concurrent_users_test.py and 6 unit tests for concurrency script`

---

### WP-5 (P2): README and documentation updates

**Goal:** Ensure README covers the full local dev workflow with Postgres cache so
any developer or agent reading the README can set up the environment without
consulting internal agent documentation. Remove stale entries now resolved by
earlier WPs.

**Files:**
- `README.md` -- add "Local Development with DB Cache" subsection under the
  existing local dev instructions:
  - Docker prerequisite (container `ss-postgres` must exist; see SESSION_CONTEXT
    Section 8 for the full `docker run` command)
  - `python scripts/dev/dev_start.py` as the single startup command
  - Brief note on `scripts/testing/smoke_cache_check.py` (cache correctness test)
  - Brief note on `scripts/testing/concurrent_users_test.py` (concurrency /
    scaling test)
- `.claude/SESSION_CONTEXT.md` -- verify Section 8 reflects the final state of
  all WP-0 through WP-4 changes (paths, script names, dev_start.py workflow);
  commit if changed

**Acceptance criteria:**
- README local dev section includes `dev_start.py` as the startup command
- README mentions both test scripts with one-line purpose descriptions
- `python scripts/doc_state_sync.py --check` exits 0
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `docs: add local dev DB section to README, update SESSION_CONTEXT for Batch 16 close`

---

## 3. Summary Table

| WP | Priority | Deliverable | Net tests |
|----|----------|-------------|-----------|
| WP-0 | P0 | Move `smoke_cache_check.py` to `scripts/testing/`; create `scripts/dev/` | +0 |
| WP-1 | P0 | Extract `_http_client.py`; fix CSRF; update verdict to `db_cache_lookup_hits`; docstrings | +0 |
| WP-2 | P1 | 13 unit tests for `_http_client` + `smoke_cache_check` | +13 |
| WP-3 | P0 | `scripts/dev/dev_start.py` Docker+Flask startup helper | +0 |
| WP-4 | P1 | `concurrent_users_test.py` + 6 unit tests | +6 |
| WP-5 | P2 | README local dev section + SESSION_CONTEXT final sync | +0 |

**Total after Batch 16:** 320 + 13 + 6 = **339 tests passing**

---

## 4. Execution order

1. WP-0 (migration -- establishes folder structure; all other WPs depend on it)
2. WP-1 (refactor + CSRF fix -- unblocks WP-2 and WP-4)
3. WP-2 (tests for WP-1 deliverables)
4. WP-3 (standalone; no dependencies on other WPs)
5. WP-4 (concurrent script + tests; depends on `_http_client.py` from WP-1)
6. WP-5 (last -- documents completed work)

---

## 5. Verification (per WP)

```bash
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

For WP-1 acceptance: run smoke test against live local app with CSRF enabled.
For WP-4 acceptance: run concurrent test against live local app.

---

## 6. Deferred

- **TTL expiry smoke testing**: verifying cache entries expire after
  `METADATA_CACHE_TTL_DAYS` requires DB timestamp manipulation; future batch
  candidate.
- **dev_start.py unit tests**: deferred per WP-3 rationale; revisit if the
  script grows.
- **smoke_cache_check.py live integration test**: the pytest suite uses mocks;
  live-server validation is covered by manual smoke test runs per the workflow.
- **Feature work (top songs, heatmap)**: owner-defined scope required.
- **Orchestrator modularization**: premature until second pipeline exists.
