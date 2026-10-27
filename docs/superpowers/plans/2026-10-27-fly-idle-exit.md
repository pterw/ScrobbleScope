# Fly Idle Exit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The web app (Fly app `scrobblescope`) stops itself, with exit code 0, after `IDLE_EXIT_MINUTES` minutes with no HTTP request and no running work, and Fly starts it again on the next request; the cache database (Fly app `scrobblescope-db`) is not touched and stays on.

**Architecture:** One new stdlib module, `scrobblescope/idle_exit.py`, holds a watchdog thread that takes one decision per step against an injected clock and an injected exit action. "Active work" is one function, `has_active_work()`, built from two small seams: the number of held job slots (`worker.py`) and the correction worker's pending queue (`release_checks.py`). `create_app` starts the watchdog only when `IDLE_EXIT_MINUTES` is a positive integer. `fly.toml` turns Fly's own autostop off and keeps autostart on.

**Tech Stack:** Python 3.13 stdlib (`threading`, `time`, `os`, `signal`, `logging`), Flask hooks, gunicorn (`--workers 1 --threads 4`), pytest, Fly.io.

**Branch:** `feat/fly-idle-exit`, cut from `origin/main` at `394dbcb8`. The worktree guard (`python scripts/dev/check_worktree_alignment.py`) reports WT003 for any branch other than the active Batch 23 branch. It is advisory, and changing branches is the owner's decision; this plan records it and does not work round it.

## Why the app stops itself (verified facts, not assumptions)

- A job runs in a daemon thread inside the gunicorn worker (`worker.start_job_thread`) and does not depend on the browser connection. Fly's autostop docs do not say whether work with no inbound connection counts as load, and say "you can code your app to exit when idle". So the app decides when it is idle.
- The web machine's restart policy is `on-failure` (max 10): exit code 0 leaves the machine stopped, and the service's autostart brings it back on the next request.
- Fly pricing the owner agreed to (cost ceiling: under five dollars a month): shared-cpu-2x 512 MB about $3.89 to $4.04 a month running all day. The saving comes from stopped hours.

## Where work can run with no HTTP request (the audit this plan rests on)

Grep of `scrobblescope/` for `Thread(`, `acquire_job_slot`, `start_job_thread`, `enqueue_release_check`, `Timer(` and `schedule` found exactly these:

| Work | Where it runs | Visible from |
|---|---|---|
| Album job, heatmap job, Spotify-export job | A daemon thread from `worker.start_job_thread`, started by `routes/admission.py` `admit` after `acquire_job_slot`. The slot is released only in `worker.run_coroutine_in_new_loop`'s `finally` (and in the two entry points' "job gone" early returns). | **The held slot count.** One number covers all three kinds, because every kind is admitted through `admit`. Scanning the job store is redundant: a job in the store can be a finished one waiting for its TTL. |
| Release checks (MusicBrainz corrections) | One daemon thread `release-checks` (`release_checks._worker_loop`) draining `_JOB_QUEUE`. It keeps working **after** the album job succeeded and released its slot. | **Not visible today.** Smallest change: `release_checks.has_pending_checks()`, true while `_JOB_QUEUE.unfinished_tasks` is above 0 (counts queued and running jobs; `put` raises it, `task_done` lowers it after the job runs). No gap: `orchestrator/__init__.py` calls `enqueue_release_check` while the job still holds its slot. |
| `utils.run_async_in_thread` (Last.fm precheck, Spotify export fetch) | A thread that the calling request thread joins, bounded by `LASTFM_PRECHECK_TIMEOUT_SECONDS` (default 5). | The HTTP request that is waiting for it (the request hooks, below). |
| Cache cleanup (`cache.cleanup_stale_metadata`) | Inside `AlbumCache.lookup`, on a job thread. | The held slot. |

No other background thread, timer or scheduler exists. If the executor of Task 1 finds one the grep above missed, stop and return NEEDS_CONTEXT.

## Frozen design

1. **When it exits.** `IDLE_EXIT_MINUTES` unset, empty, `0`, negative or not an integer: nothing starts (a non-integer or negative value logs one warning). A positive integer: the watchdog checks every 30 seconds (`IDLE_CHECK_INTERVAL_SECONDS`, a module constant, not an option). A step does this, in order: if `has_active_work()` is true, record "now" as the last activity and do not exit; else if `clock() - last_activity >= idle_seconds`, log one line, run the exit action, and never run it again. So the idle window restarts when a job finishes: a job that ends at minute 19 does not let the app exit at minute 20.
2. **What counts as a request.** Any request through the Flask app: progress polls and `/static/` files included. The hook records the time in `before_request` and again in `teardown_request` (teardown also runs for a request that raised), with the monotonic clock, so a request that outlasts the window renews the timer when it ends (only a request's start and end touch the timer; requests are bounded, e.g. the 5 s precheck, so this is a known limit, not a gap).
3. **Start of the timer.** The timer starts when `IdleWatch` is built, which is at process start; a machine woken by a deploy with no traffic exits after the same window. Only the DB cache persists; in-memory jobs are lost on exit (already true on every deploy). **Behaviour change (owner ruling R-1/R-4):** in-memory job results used to live for `JOB_TTL_SECONDS` (2 hours); now they live only until the next idle exit, 20 idle minutes at the earliest. A revisit to a vanished job shows the existing "Your results have expired, run a new search" page (no crash), and the DB cache makes the new search fast. The in-memory `REQUEST_CACHE` and the Spotify token state clear on each exit too.
4. **The exit action.** Default `stop_gunicorn()`: `os.kill(os.getppid(), signal.SIGTERM)`. The gunicorn master imports `app:app` in the worker (no `--preload`), so the thread runs in the worker and its parent is the master. SIGTERM makes the master shut down gracefully (it signals the worker, waits up to `--graceful-timeout`, 30 s by default, then exits with status 0: `Arbiter.handle_term` raises `StopIteration`, `run()` calls `halt()`, whose exit status defaults to 0). Daemon threads do not hold the shutdown. **Rejected alternative:** `os._exit(0)` from the worker would not work, because the gunicorn master sees a worker exit that is not a boot error and respawns the worker, so the container never exits; do not "simplify" to it. Because the signal goes to the parent, `IDLE_EXIT_MINUTES` is a production (gunicorn) setting only: outside gunicorn (e.g. `python app.py`) the parent is not a gunicorn master, so DEPLOY.md says not to set it locally. Controller step C2 proves the exit code with a probe BEFORE Task 1, and the Adoption section proves it again on Fly.
5. **Fly config.** `fly.toml` `[http_service]`: `auto_stop_machines = 'off'`, `auto_start_machines = true`, `min_machines_running` removed (the default 0), and `[env] IDLE_EXIT_MINUTES = "20"`. The release command (`python init_db.py`) is unaffected. Fly's `off` is the documented spelling for the string values `'off'`, `'stop'`, `'suspend'`.
6. **Testability.** The clock, the work check and the exit action are constructor arguments; `step()` is one decision; `run(sleep)` takes an injected sleep. Tests use a fake clock, never sleep for real, and never send a signal.

## Global Constraints

- Work on `feat/fly-idle-exit`, in MAIN (`C:/ssw/u2`). `PY` = `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"`; use `"$PY" -m pytest`, never bare `pytest` or `pip`.
- No new dependency (stdlib only): slim image, wheels only, one gunicorn worker, 512 MB, cost under $5 a month. No new option beyond `IDLE_EXIT_MINUTES`.
- KISS (owner ruling 2026-10-24): no pasted implementation code in this plan; tasks of about 5 minutes; low cyclomatic complexity; every loop linear.
- Lean suite (AGENTS.md "Test Quality Rules"): few tests, each named for the behaviour it guards, each failing if the code under test is deleted; no test pins wording or a constant equal to the code's own value. The five behaviours: idle exits, active work blocks exit, a recent request blocks exit, unset env starts nothing, the exit action runs once.
- Logs name operations and counts, never an album, artist or track name. The idle-exit log line names the idle minutes only.
- No module reads another package's underscore name (`tests/test_module_boundaries.py`): `idle_exit.py` calls only the public seams `worker.active_job_slots` and `release_checks.has_pending_checks`.
- Tailwind and static rules: this change touches no template, stylesheet or static file, so `tailwind-css-drift` and the frontend gate must pass unchanged.
- Commit procedure (AGENTS.md "Commit Rules"), per task: write the PLAYBOOK Section 4 side-task entry first (`### 2026-10-27 - <title>` directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, no `(Batch N WP-X)` tag, naming the existing tests it edits or "none", ending with the measured `pytest -q` count); `pytest -q`; `"$PY" scripts/doc_state_sync.py --fix --test-count N`; stage files by name, never `git add -A`; `pre-commit run --all-files`; `"$PY" scripts/doc_state_sync.py --check`. Conventional Commits, subject at most 72 characters, body says why, never `--no-verify`, never `--amend`, never push without the owner's say-so, no attribution line unless the dispatch gives one.
- ASCII only in Markdown and commit messages. Cite functions by name, not line number. Grep before claiming anything does not exist.

## Interfaces (frozen; later tasks use these names exactly)

- `scrobblescope/worker.py`: `active_job_slots() -> int` -- the number of job slots held right now, `MAX_ACTIVE_JOBS` minus the semaphore's free count; 0 when no job runs.
- `scrobblescope/release_checks.py`: `has_pending_checks() -> bool` -- true while a release-check job is queued or running.
- `scrobblescope/idle_exit.py`:
  - `IDLE_CHECK_INTERVAL_SECONDS = 30`
  - `has_active_work() -> bool` -- `worker.active_job_slots() > 0 or release_checks.has_pending_checks()`
  - `stop_gunicorn() -> None` -- sends SIGTERM to the parent process (the gunicorn master)
  - `class IdleWatch(idle_seconds, *, clock=time.monotonic, work=has_active_work, exit_action=stop_gunicorn)` with `touch() -> None`, `step() -> bool` (True once the exit action has run), `run(sleep=time.sleep) -> None` (loop: `step()`, stop when it returns True, else `sleep(IDLE_CHECK_INTERVAL_SECONDS)`), `attach(app) -> None` (registers `before_request` and `teardown_request` hooks that call `touch`), `start() -> threading.Thread` (a daemon thread named `idle-exit` running `run()`).
  - `watch_from_env(environ=os.environ) -> IdleWatch | None` -- None unless `IDLE_EXIT_MINUTES` is a positive integer; otherwise `IdleWatch(minutes * 60)`.

---

## Tasks

### Task 1: Two seams that make all background work visible

**Wave:** 1. **Touches:** `scrobblescope/worker.py`, `scrobblescope/release_checks.py`, `tests/test_worker.py`, `tests/services/test_release_checks.py`, `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `config/docsync.toml` (the last three are the per-commit bookkeeping, written by the implementer). **After:** C2 (the probe passed). **Mode:** serial.

**Behaviour.** Add `worker.active_job_slots()` and `release_checks.has_pending_checks()` exactly as frozen above. The first reads the semaphore's free count (`_active_jobs_semaphore._value`, read inside `worker.py` itself, so the module-boundaries test is not touched); the suite's `tests/conftest.py` already swaps in a fresh semaphore per test, which is why a counter variable is not used. The second reads `_JOB_QUEUE.unfinished_tasks`. Neither changes any existing behaviour. Add the one-line mention to the `worker.py` and `release_checks.py` module docstrings only if they list their public functions (read them; add nothing otherwise).

**Interfaces.** Produces: `active_job_slots() -> int`, `has_pending_checks() -> bool`. Consumes: nothing.

**Acceptance (2 new tests, in existing modules; no new test module).**
- `tests/test_worker.py`: with no slot held `active_job_slots()` is 0; after `acquire_job_slot()` it is 1; after `release_job_slot()` it is 0 again. Planted defect: return a constant 0.
- `tests/services/test_release_checks.py`: with `_JOB_QUEUE` replaced (`monkeypatch.setattr(release_checks, "_JOB_QUEUE", queue.Queue())`), `has_pending_checks()` is False when empty, True after a `put`, still True after `get()` without `task_done()` (a job running), False after `task_done()`. Planted defect: use `qsize()` instead of `unfinished_tasks` (the "running" step then fails).

- [ ] **Step 1:** Write both tests; run `"$PY" -m pytest tests/test_worker.py tests/services/test_release_checks.py -q -k "active_job_slots or pending_checks"` and see them fail (AttributeError: the functions do not exist).
- [ ] **Step 2:** Add the two functions; rerun the same command; see them pass. Apply each planted defect once, see the matching test fail, revert.
- [ ] **Step 3:** Run `"$PY" -m pytest tests/test_worker.py tests/services/test_release_checks.py tests/test_module_boundaries.py -q`.
- [ ] **Step 4:** Commit per the Global Constraints procedure. Subject: `feat(runtime): Expose held job slots and pending release checks`. Body: the idle watchdog needs one place to ask whether any background work is running; the correction worker outlives the slot of the job that queued it.

---

### Task 2: The idle watchdog module

**Wave:** 2. **Touches:** `scrobblescope/idle_exit.py` (create), `tests/test_idle_exit.py` (create), `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `config/docsync.toml` (per-commit bookkeeping, written by the implementer). **After:** 1. **Mode:** serial.

**Behaviour.** Create `scrobblescope/idle_exit.py` with the interfaces frozen above and the decision order in "Frozen design" item 1. The module docstring states the one-line dependency note the other modules carry (`idle_exit <- worker, release_checks`) and why the app stops itself (Fly's autostop cannot see work with no inbound connection). `step()` logs one INFO line when it exits: `Idle for <N> minutes with no active work; stopping the server` (N is `idle_seconds // 60`). `watch_from_env` logs one warning for a value that is set but not a positive integer, and returns None for it. Cyclomatic complexity of `step` stays at 4 or below; `run` is a simple loop. Do not add a lock: `touch` assigns one float, which is atomic under the GIL, and `step` is the only reader.

**Interfaces.** Produces: everything under `scrobblescope/idle_exit.py` in the Interfaces section. Consumes: `worker.active_job_slots`, `release_checks.has_pending_checks` (Task 1).

**Tests (`tests/test_idle_exit.py`, a fake clock object with an `advance(seconds)` method and a recording exit action; no real sleep, no real signal).**
1. `test_exits_once_after_the_idle_window_with_no_work` -- `IdleWatch(600, clock=fake, work=lambda: False, exit_action=record)`; `run(sleep=lambda s: fake.advance(s))` returns, `record` was called exactly once, and the fake clock reads at least 600. Then call `step()` twice more: it returns True and `record` is still called once. Planted defects: never exit (the loop never returns, so the test uses a sleep that raises after 100 calls); exit without remembering (the count reaches 3).
2. `test_active_work_blocks_exit_and_restarts_the_window` -- `work` is a mutable flag. Advance past the window with work true: `step()` is False, no exit. Set work false and call `step()` at once: still no exit (the window restarted when work was last seen). Advance by the window: exit. Planted defects: ignore `work`; do not touch on active work (exit fires one step after work ends).
3. `test_a_recent_request_blocks_exit` -- a bare Flask app, `IdleWatch(...).attach(app)`, a route and the test client. Advance to just under the window, make a request to the route and then to `/static/missing.css` (a 404 still passes through the hooks), advance to just under the window again: `step()` is False; advance by the window: True. Planted defects: `attach` registers nothing (the `step()` after the requests exits); `attach` registers only `before_request` and the test makes its last request a slow one that advances the clock inside the view (the teardown renewal is lost).
4. `test_unset_or_invalid_idle_minutes_starts_nothing` -- parametrized over `{}`, `{"IDLE_EXIT_MINUTES": ""}`, `"0"`, `"-5"`, `"abc"`: `watch_from_env` returns None, and a `caplog` warning is logged for `"abc"` and `"-5"` only (unset, empty and `"0"` mean "off" and stay silent). One further case, `"20"`, returns an `IdleWatch` (not None); the 1200-second window is not asserted, because that would pin the code's own constant. Planted defects: treat `"0"` as valid; return a watch for an unset variable.
5. `test_has_active_work_sees_a_held_slot_and_a_pending_check` -- parametrized over (slot held, queue busy, neither): with the real seams (acquire a slot through `worker.acquire_job_slot()` and release it in a `finally`; replace `release_checks._JOB_QUEUE` with a fresh queue holding one item), `has_active_work()` is True, True, False. Planted defect: drop the `release_checks` half (the queue case fails) or the slot half.

- [ ] **Step 1:** Write `tests/test_idle_exit.py` with the five tests; run `"$PY" -m pytest tests/test_idle_exit.py -q`; see an ImportError (no module).
- [ ] **Step 2:** Create `scrobblescope/idle_exit.py`; run the same command until the five pass.
- [ ] **Step 3:** Apply each planted defect once, see the named test fail, revert. Run `"$PY" -m pytest tests/test_idle_exit.py tests/test_module_boundaries.py -q`.
- [ ] **Step 4:** Commit per the Global Constraints procedure. This commit adds a test module: run `--fix --test-count N` with the measured N (the module count site changes too). Subject: `feat(runtime): Add the idle watchdog behind IDLE_EXIT_MINUTES`. Body: Fly's autostop cannot see background jobs, so the app exits itself only when no request and no work has been seen for the window.

---

### Task 3: Start the watchdog from the app factory

**Wave:** 3. **Touches:** `app.py` (`create_app`), `tests/test_app_factory.py`, `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `config/docsync.toml` (per-commit bookkeeping, written by the implementer). **After:** 2. **Mode:** serial.

**Behaviour.** In `create_app`, after the blueprint is registered, import `watch_from_env` from `scrobblescope.idle_exit` inside the function (the same deferred-import convention as the blueprint and `ensure_api_keys`: `config` reads the environment on first import, and `load_dotenv` must have run), call `watch_from_env(os.environ)`, and when it returns a watch call `watch.attach(application)` and `watch.start()`. Nothing else in `app.py` changes. Production calls `create_app` once, at module level (`app = create_app()` for `gunicorn app:app`), in the worker, so one thread starts. The test suite never sets `IDLE_EXIT_MINUTES` (confirm: `grep -rn IDLE_EXIT tests` shows only this task's test), so no test or CI run starts a watchdog or exits.

**Interfaces.** Consumes: `watch_from_env`, `IdleWatch.attach`, `IdleWatch.start` (Task 2). Produces: nothing new.

**Test (one, in `tests/test_app_factory.py`).** `test_create_app_starts_the_idle_watch_only_when_the_env_var_is_set` -- parametrized over `("20", 1)` and `(None, 0)`: `patch.dict(os.environ, ...)` (removing the key for None), `patch("scrobblescope.idle_exit.IdleWatch.start")` so no thread starts, call `create_app()`, assert `start` was called that many times. Planted defects: call `start` unconditionally; call `watch_from_env` but never `start`.

- [ ] **Step 1:** Write the test; run `"$PY" -m pytest tests/test_app_factory.py -q -k idle_watch`; see the `"20"` case fail (start not called).
- [ ] **Step 2:** Edit `create_app`; rerun; see both cases pass; apply each planted defect once, see it fail, revert.
- [ ] **Step 3:** Run `"$PY" -m pytest tests/test_app_factory.py tests/test_idle_exit.py -q`.
- [ ] **Step 4:** Commit per the Global Constraints procedure. Subject: `feat(app): Start the idle watchdog from create_app`. Body: the watchdog is off unless IDLE_EXIT_MINUTES is a positive integer, so local runs, tests and CI never exit.

---

### Task 4: Fly config, the exit-code probe, and the docs

**Wave:** 4. **Touches:** `fly.toml`, `DEPLOY.md`, `docs/architecture/runtime-system.md`, `.claude/SESSION_CONTEXT.md`, `README.md` (the hosting row only), `docs/agents/AGENT_NOTES.md` (only if its line about the machine sleeping needs the new cause), `docs/agents/PLAYBOOK.md`, `config/docsync.toml` (rewritten by `--fix`). **After:** 3 (the C2 probe has already run, before Task 1). **Mode:** serial, controller only (see "Controller steps"). No agent edits `fly.toml`.

**Behaviour.** Do the Controller steps below, in order, and commit once. Subject: `chore(deploy): Let the app machine stop itself when idle`. Body: Fly's autostop cannot see background jobs, so autostop is off and the app exits with code 0 after 20 idle minutes; the next request starts the machine; the DB app is untouched.

**Acceptance.**
- `fly.toml` `[http_service]` has `auto_stop_machines = 'off'`, `auto_start_machines = true`, no `min_machines_running`, and `[env]` has `IDLE_EXIT_MINUTES = "20"`; `[deploy]`, `[build]` and `[[vm]]` are unchanged (`git diff fly.toml` shows only those lines).
- The C2 probe printed `EXIT=0` before Task 1 and its line is quoted in the PLAYBOOK entry.
- `"$PY" scripts/doc_state_sync.py --check` exits 0, and a sweep finds no live document still saying the app is always on.

---

## Controller steps (edits only the controller makes)

These touch the deploy config and the docs, so the controller does them, in MAIN. **C2 runs first, before Task 1**; C1 and C3-C7 run after Task 3 is landed and green.

- [ ] **C1: edit `fly.toml`.** In `[http_service]` change `auto_stop_machines = 'stop'` to `'off'`, keep `auto_start_machines = true`, delete the `min_machines_running = 1` line, keep `processes = ['app']`. Add an `[env]` table: `IDLE_EXIT_MINUTES = "20"`. Add a short comment above `[http_service]`: the app stops itself when idle (see DEPLOY.md "Idle exit").
- [ ] **C2: prove the exit code, BEFORE Task 1 (needs no repo code; needs Docker; if Docker is unavailable record that in the PLAYBOOK entry and rely on Adoption step A2).** In the session scratchpad (not the repo), write `probe.py`: a WSGI app `def app(environ, start_response)` plus a module-level daemon thread that sleeps 2 seconds then calls `os.kill(os.getppid(), signal.SIGTERM)`, the same call `stop_gunicorn` makes. Run under Git Bash with `MSYS_NO_PATHCONV=1` set (otherwise `-w /p` and `:/p` are rewritten to Windows paths) and the scratchpad given as a Windows-style path in `-v`. The `sh -c` body is in SINGLE quotes, so `$?` is expanded inside the container and not by the host shell:
  `MSYS_NO_PATHCONV=1 docker run --rm -v <scratchpad>:/p -w /p python:3.13-slim sh -c 'pip install -q gunicorn && gunicorn --bind 127.0.0.1:8080 --workers 1 --threads 4 probe:app; echo EXIT=$?'`
  Expected: gunicorn logs "Handling signal: term" and "Shutting down: Master", and the last line is `EXIT=0`. Quote that line in the PLAYBOOK entry of the Task 1 commit (or Task 4's). A non-zero value stops the plan before any code is written: return to the owner, because Fly would then restart the machine and the design fails.
- [ ] **C3: DEPLOY.md.** Add a section "## Idle exit" after "MusicBrainz contact": what `IDLE_EXIT_MINUTES` does and its default in `fly.toml`; that Fly's own autostop is off on purpose and why (background jobs with no inbound connection); that the machine stops with exit code 0 and the next request starts it, with a cold start of a few seconds; that in-memory jobs and results are lost on exit (the DB cache stays), so the results lifetime changes from `JOB_TTL_SECONDS` (2 hours) to the 20 idle minutes before the machine stops, and a revisit then shows the existing "Your results have expired, run a new search" page (the in-memory request cache and Spotify token state clear too); that `IDLE_EXIT_MINUTES` is production-only (it signals the gunicorn master; do not set it for `python app.py`); that `scrobblescope-db` is a separate app and is not affected; how to turn the feature off locally or on Fly (unset or `0`, and restore `auto_stop_machines = 'stop'` only if the owner wants Fly's autostop back); rollback (below).
- [ ] **C4: architecture and context docs.** `docs/architecture/runtime-system.md`: add `idle_exit.py` as a node (edges to `worker.py` and `release_checks.py`, and from `app.py`), one bullet under the design decisions ("The app stops itself when idle: one watchdog thread, exit code 0, Fly restarts it on demand"), and update the "eleven of the nodes import config" sentence only if `idle_exit.py` imports `config` (it does not; leave it). `.claude/SESSION_CONTEXT.md` Section 4: add `idle_exit.py` to the module tree and `idle_exit.py <- release_checks, worker` to the import graph, and update the Section 1 batch-status row if project state changed (the test-count field is rendered, never hand-edited). `README.md` hosting row: add that the app machine stops when idle. `AGENT_NOTES.md`: read the line beginning "re-searches with different filters. Clears on Fly.io machine sleep"; if it implies the machine only sleeps on Fly's schedule, say it also exits after 20 idle minutes.
- [ ] **C5: sweep.** Use the `sweeper` agent (or `grep -rn`) for `min_machines_running`, `auto_stop_machines`, `always on`, `shared-cpu` and `machine sleep` in live (not `docs/history`, not `docs/logarchive`) documents; fix each sibling copy that now says the old thing. Point-in-time records stay.
- [ ] **C6: PLAYBOOK Section 4 entry** (side-task form, directly after `<!-- DOCSYNC:CURRENT-BATCH-END -->`): `### 2026-10-27 - Let the app machine stop itself when idle`. It lists the files, the C2 probe line, "edited existing tests: none", and ends with the measured count.
- [ ] **C7: gates and commit.** `"$PY" -m pytest -q` (note N), `"$PY" scripts/doc_state_sync.py --fix --test-count N`, stage `fly.toml DEPLOY.md docs/architecture/runtime-system.md .claude/SESSION_CONTEXT.md README.md docs/agents/PLAYBOOK.md config/docsync.toml` plus any other file the sweep changed, by name; `pre-commit run --all-files`; `"$PY" scripts/doc_state_sync.py --check`; then commit with the Task 4 subject. Do not push; the owner decides when to push and deploy.

---

## Dispatch

Tasks 1-3 are serial implementer commits: each implementer writes the PLAYBOOK Section 4 entry, runs `doc_state_sync.py --fix --test-count N` and stages SESSION_CONTEXT and `config/docsync.toml`, as AGENTS.md requires for every commit (owner ruling R-3). `fly.toml`, DEPLOY.md and the architecture docs stay controller steps (Task 4). All four tasks touch the same few files in a line, so they run serially: no parallel code phase is worth its overhead for about twenty minutes of work.

| Wave | Tasks | Mode | Agents at peak |
|---|---|---|---|
| 0 | C2 probe (before any code) | controller | 0 |
| 1 | Task 1 | serial | 1 + review |
| 2 | Task 2 (After 1) | serial | 1 + review |
| 3 | Task 3 (After 2) | serial | 1 + review |
| 4 | Task 4 and the Controller steps (After 3) | controller | 0 |

Peak agents: 1 implementer, plus one reviewer. File check: Task 1 `worker.py`, `release_checks.py`, `test_worker.py`, `test_release_checks.py`; Task 2 `idle_exit.py`, `test_idle_exit.py` (both new); Task 3 `app.py`, `test_app_factory.py`; Task 4 config and docs. No code file appears in two tasks; only the per-commit bookkeeping files (PLAYBOOK, SESSION_CONTEXT, `config/docsync.toml`) recur, and the tasks are serial.

Landing order: 1, 2, 3, 4. Each landing is followed by the Gates below on the landed commit. Task 3 must land after Task 2 (it imports it) and Task 4 last, so a deploy never carries `IDLE_EXIT_MINUTES` in `fly.toml` for an image that does not read it.

### Gates

Run in this order after each landing, from MAIN. `PY` is the primary checkout's interpreter.

- `name`: worktree guard
  `run`: `"$PY" scripts/dev/check_worktree_alignment.py`
  `pass`: exit 0, or exit nonzero with only WT003 (advisory, owner decision; see Branch)
  `quote`: the full output when it is nonzero
  `when`: before Task 1 and after Task 4
- `name`: focused tests
  `run`: the task's own command (Tasks 1-3 name them)
  `pass`: exit 0, 0 failed
  `quote`: the pytest summary line
  `when`: every task, before the full suite
- `name`: full suite
  `run`: `"$PY" -m pytest -q`
  `pass`: exit 0, 0 failed, and the count rose by the number of new test cases the task added (parametrized cases count one each; measure it, do not predict it)
  `quote`: the last line (`N passed`)
  `when`: every task, once, on the final tree
- `name`: pre-commit
  `run`: `pre-commit run --all-files`
  `pass`: every hook Passed (re-stage anything a hook rewrote, then rerun)
  `quote`: the names of any hook that failed
  `when`: every task, after staging
- `name`: docsync
  `run`: `"$PY" scripts/doc_state_sync.py --check`
  `pass`: exit 0 (the root `BATCH23_DEFINITION.md` warning is expected)
  `quote`: any `ERROR DOC...` line
  `when`: every task, last gate before the commit
- `name`: exit-code probe
  `run`: Controller step C2
  `pass`: the last line is `EXIT=0`
  `quote`: that line
  `when`: once, before Task 1 (a non-zero exit stops the plan)

## Adoption (after merge and deploy; the owner or the controller runs these)

`fly deploy` is manual (`DEVELOPMENT.md` "Release"). Cold start after a stop is a few seconds (the Python process boots and imports the app); the first request after a stop is slow, then normal.

- [ ] **A1: deploy.** `fly deploy -a scrobblescope`. The release command runs `python init_db.py` as before.
- [ ] **A2: it stops.** Wait about 21 minutes without opening the site. `fly status -a scrobblescope` shows the machine `stopped`. `fly machine status <machine-id> -a scrobblescope` shows the last event with exit code 0 and no restart (an `on-failure` policy restarts only a nonzero exit). If the machine shows `started` again or an exit code other than 0, stop and roll back.
- [ ] **A3: one request starts it.** `curl -sS -o /dev/null -w "%{http_code} %{time_total}\n" https://scrobblescope.fly.dev/` returns 200 (slower the first time). `fly status -a scrobblescope` shows `started`.
- [ ] **A4: the DB stays on.** `fly status -a scrobblescope-db` shows its machine `started` through steps A2 and A3.
- [ ] **A5: a job survives a closed tab.** Start one album search on the live site, close the tab at once, wait longer than the job takes plus a minute, and keep the idle window in mind: the job must keep the machine alive (a held slot). `fly logs -a scrobblescope` contains the job's `Persisted ... rows to DB cache` line, and the machine is not `stopped` before that line appears. After the line and the release checks end, the machine stops 20 minutes later (A2 again).
- [ ] **A6: cost.** After a week, `fly dashboard` (billing) is on track for under $5 a month.

## Rollback

Revert the `fly.toml` change (restore `auto_stop_machines = 'stop'`, `min_machines_running = 1`, and delete the `[env]` `IDLE_EXIT_MINUTES` line), then `fly deploy -a scrobblescope`. The Python code can stay: with `IDLE_EXIT_MINUTES` unset or `"0"` nothing starts. `fly.toml` `[env]` is the only place the variable is set, so reverting that file is the whole rollback; no secret and no DB change is involved.

## Self-review

- Spec coverage: behaviour 1 -> Tasks 2, 3 (watchdog, env gate, exit 0) and C2/A2 (the exit code is proved twice); behaviour 2 -> Task 1 (the seams) and Task 2 (`has_active_work`), with the audit table showing every place work can run; behaviour 3 -> Task 2 test 3; behaviour 4 -> Frozen design item 3; behaviour 5 -> C1 and A2/A3; behaviour 6 -> Task 2's constructor arguments and tests; docs -> C3-C6; adoption and rollback -> their sections.
- Names consistent across tasks: `active_job_slots`, `has_pending_checks`, `has_active_work`, `stop_gunicorn`, `IdleWatch` (`touch`, `step`, `run`, `attach`, `start`), `watch_from_env`, `IDLE_CHECK_INTERVAL_SECONDS`, `IDLE_EXIT_MINUTES`.
- Placeholder scan: none; the one value the executor measures (the test count) is measured by command.
- Behaviour change the owner should know (recorded in DEPLOY.md by C3): job results are in memory, so a Results page left untouched for 20 minutes loses its job (the TTL used to be 2 hours). The Results page polls `/api/release_checks` while corrections run, which counts as requests. After the idle exit, a revisit shows the existing expiry page and needs a fresh search, which the DB cache makes fast.
- Known limits (not fixed): a request in flight longer than the window does not block exit, since only its start and end touch the timer (requests are bounded, so this is theoretical); and bots or uptime probes hitting any URL (`/static/` included) reset the timer by design and can keep the machine awake, which A6 would show as cost above the estimate.
