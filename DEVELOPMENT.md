# Developing ScrobbleScope

This page takes you from a fresh clone to a passing test run, then shows each development tool running with a short excerpt of its real output. It is explanatory and grants no agent authority: `AGENTS.md` owns the rules that agents and contributors follow, and nothing here overrides it. For what the product does, read the [README](README.md). For how the code is built, read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). For deploying, read [DEPLOY.md](DEPLOY.md).

Every output block below was captured from a real run on 2026-10-31 at the commit this page was written against. Lines cut for length are marked `...`. Counts and timings change from run to run, so treat them as examples. The suite counts are written as `<N>` because `config/docsync.toml` pins the real number.

## Why the tooling exists

One developer builds ScrobbleScope with LLM coding agents. An agent keeps no memory between sessions and cannot see what another agent did, so decisions, state and rules live in tracked files. Scripts and hooks check those files, because nobody keeps them tidy by hand.

The tools on this page are the checks behind that rule:

- `scripts/doc_state_sync.py` rotates and validates the state documents.
- `scripts/dev/check_worktree_alignment.py` checks the git worktree.
- `scripts/dev/tailwind_build.py` builds the committed stylesheet.
- `scripts/dev/frontend_gate.py` drives a real browser against the app.
- `pre-commit` runs the docsync, worktree and Tailwind drift checks, plus `ruff` and file-hygiene hooks, before each commit.

`docs/architecture/development-cycle.md` describes the cycle these tools serve.

## Set up

Follow [Getting Started in the README](README.md#getting-started) for the prerequisites, the clone, the virtual environment, the install and the Last.fm and Spotify credentials. Install `requirements-dev.txt` instead of `requirements.txt`, because it adds the test and lint tools. This section covers what a contributor needs on top.

A linked git worktree reuses the primary checkout's `.venv`, so never create a second one. `AGENTS.md` ("Environment Setup" and "Session Bootstrap (in order)") explains how to find the qualified Python path from a worktree. Every pinned package is listed in `requirements.txt` or `requirements-dev.txt`; ask the owner before you add one.

Copy `.env.example` to `.env` and fill in the provider keys. The tests need no real keys, because `tests/conftest.py` supplies placeholders. Install the browsers once if you plan to run the browser tests or the frontend gate:

```bash
python -m playwright install chromium firefox
```

### Start the app

`python app.py` starts the app on `http://127.0.0.1:5000/` with the Flask debug server. This page does not show its output, because the port is fixed and a second copy would collide with a running one. The command is:

```bash
python app.py
```

To check that the app boots without taking port 5000, serve it on a port the operating system picks. Paste this into a Python session started in the repository root, with the provider keys and `SECRET_KEY` set in your environment or `.env`:

```python
import threading, urllib.request
from werkzeug.serving import make_server
from app import create_app
srv = make_server("127.0.0.1", 0, create_app())
threading.Thread(target=srv.serve_forever, daemon=True).start()
try:
    print(urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}/").status)
finally:
    srv.shutdown()
```

The block binds loopback only, requests the home page once and stops the server in the `finally` clause. A healthy start ends like this. The `debug mode` value follows `DEBUG_MODE` in your `.env`; this capture ran with `DEBUG_MODE` unset, so it printed `False`, and `DEBUG_MODE=1` prints `True`:

```text
... [INFO] ScrobbleScope starting up, debug mode: False
... [INFO] Serving index.html as the homepage.
200
```

### Run with the database cache

The Postgres cache turns on when `DATABASE_URL` is set in `.env`. Without it the app runs and treats every album as a cache miss. [docs/agents/AGENT_NOTES.md](docs/agents/AGENT_NOTES.md) holds the local container name, volume and connection string. With the `ss-postgres` container created, one command starts the container and then the app:

```bash
python scripts/dev/dev_start.py
```

The script has no `--help`: running it launches the app on port 5000, so this page shows the command only. `init_db.py` creates the cache tables. It is the release command on Fly.io, and it does nothing when `DATABASE_URL` is unset:

```text
$ python init_db.py
DATABASE_URL not set <em dash> skipping schema init (local dev mode)
```

The real line has an em dash where this page shows `<em dash>`, because the page is ASCII only.

No database was reachable for the captures on this page, so none of them exercise the cache. The cache behaviour is described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run the tests

`pytest` collects `tests/` (set in `pyproject.toml`). Test files are named `test_<module>.py` after the module they cover. `tests/services/` covers the provider clients, `tests/scripts/` covers the scripts under `scripts/`, and `tests/frontend/` covers browser-side functions. Tests marked `browser` need a Playwright browser. They live in `tests/frontend/` and in `tests/scripts/dev/` (`test_frontend_gate_shared.py` and `test_frontend_gate_spotlight_photo.py`). Every other test needs no browser.

CI runs the unmarked tests with a coverage floor of 70 percent. Run the same selection locally:

```bash
python -m pytest -m "not browser" -q
```

```text
...
<N> passed, <N> deselected in 168.50s (0:02:48)
```

The deselected tests are the `browser` ones. Run them on their own, after you install the browsers:

```bash
python -m pytest -m browser -q
```

```text
<N> passed, <N> deselected in 24.83s
```

A plain `python -m pytest -q` runs both groups. To run part of the suite, name the files. The docsync tests are a good example, because they cover the tooling in the next sections:

```bash
python -m pytest tests/test_docsync_*.py -q
```

```text
.................................................................        [100%]
<N> passed in 58.45s
```

Tests name the behaviour they guard and must fail if that behaviour regresses. `AGENTS.md` ("Test Quality Rules") has the full list.

## Run the checks before you commit

`pre-commit` runs the formatting, lint and consistency hooks listed in `.pre-commit-config.yaml`. Run all of them against the whole tree:

```bash
pre-commit run --all-files
```

```text
doc-state-sync-check.....................................................Passed
ruff check...............................................................Passed
ruff format..............................................................Passed
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check for merge conflicts................................................Passed
detect private key.......................................................Passed
tailwind-css-drift.......................................................Passed
worktree-alignment.......................................................Passed
```

The last hook runs the worktree guard in advisory mode. It can print `ERROR WT003` or `WARNING WT010` lines under its `Passed` line and the commit still goes ahead (see "Check the worktree" below). The hooks skip generated and prose paths such as `static/` and `templates/`.

### Keep the documents in sync

`scripts/doc_state_sync.py` keeps `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md` and the archives consistent. The declared values, the pinned test count and the retired claims live in `config/docsync.toml`. `--check` reads and reports; it never writes:

```bash
python scripts/doc_state_sync.py --check
```

```text
WARNING: Root BATCH file detected: BATCH23_DEFINITION.md should be archived under docs/history/definitions/.
...
doc_state_sync check passed (current_batch_entries=0, kept_non_current=4, rotated=0).
```

The `WARNING` lines are informational and the exit code is 0. The `...` stands for two `WARNING DOC024` lines about the findings archive pages. An `ERROR DOC...` line is a proven defect and exits 1. `docs/architecture/documentation-tooling.md` lists every code.

After you measure the suite, pin the count and let the script write every site that repeats it. Running it with the count that is already pinned changes nothing:

```bash
python scripts/doc_state_sync.py --fix --test-count N
```

```text
doc_state_sync --fix found no changes.
doc_state_sync summary (current_batch_entries=0, kept_non_current=4, rotated=0).
```

Replace `N` with the total from your own `python -m pytest -q` run. Do not run `--paginate-archives` or `--cold-storage` casually: they rewrite archive pages. `AGENTS.md` ("Doc Sync Rules") describes every mode.

The commit hook runs a preflight over what you stage. It refuses a commit that stages the docsync code itself, with exit 3, so a change to the tooling cannot validate itself:

```bash
python scripts/dev/docsync_preflight.py --worktree
```

```text
doc_state_sync check passed (current_batch_entries=0, kept_non_current=4, rotated=0).
```

Use `--staged` instead of `--worktree` to check only the index. The one escape is `SKIP=doc-state-sync-check git commit`, never `--no-verify`. A separate installer, `python scripts/dev/install_docsync_hook.py`, adds a git hook; it defaults to `--check` and is not installed in this repository:

```text
core.hooksPath: (unset; using the common .git/hooks directory)
...
Existing hook file: unknown
...
```

`Existing hook file: unknown` means a hook file already sits at the target path and this installer did not write it, for example one from the `pre-commit` framework. The `...` lines are the resolved paths and the list of worktrees the hook directory affects.

### Commit

The commit procedure is in `AGENTS.md` ("Commit Rules" and "What to update after a WP or side-task commit"). In short: write the log entry first, then run the gates, then commit with a Conventional Commits subject of at most 72 characters. This page does not copy the rules, so they stay in one place.

### Check the worktree

`scripts/dev/check_worktree_alignment.py` is read-only. It checks that the branch, its base and its lineage are safe to work on, and it prints a typed `WT` code for each problem. Run it before you start work and add `--offline` when you have no network:

```bash
python scripts/dev/check_worktree_alignment.py --base-ref main --offline
```

```text
ERROR WT012 detached HEAD -- local work requires a named branch before lineage can be checked.
Remediation: Stop and ask the owner which existing branch should be used; this guard does not switch or create branches.
INFO WT013 main -- offline mode; any base comparison is local-ref-only and freshness was not verified.
```

This capture came from a detached scratch worktree, so the guard exits 1: that is its verdict, not a crash. On a named branch the `WT012` line does not appear. While a batch is active, `WT003` fires on any branch other than the batch's named branch (`scripts/dev/_worktree_guard_lineage.py`), so a side-task branch cut from `main` prints `ERROR WT003` and the guard exits 1. The guard warns with `WT010` when the worktree has uncommitted or untracked files. The pre-commit hook runs the guard in advisory mode, so it still passes. Each `Remediation:` line says what to do. The guard never changes your tree.

## Frontend asset build

The interface uses the Tailwind CSS standalone command-line binary and the daisyUI bundles, with no Node project. The source is `static/css/tailwind.src.css`. Production serves the committed `static/css/tailwind.css`, so the app never downloads or compiles anything at startup. This section owns the build and watch commands; other documents point here.

Build once before you commit any stylesheet source or template change, or watch while you work on the interface:

```bash
python scripts/dev/tailwind_build.py
python scripts/dev/tailwind_build.py --watch
```

The script stores the pinned executable for your host, `daisyui.mjs` and `daisyui-theme.mjs` under the gitignored `scripts/bin/`. It checks each file against a pinned SHA-256 value on every run and fetches a missing or invalid file once. The first run prints three `fetching` lines while it downloads. Stop watch mode before you run the one-shot build, and commit the source together with the generated CSS.

`--check` rebuilds the stylesheet and exits 1 if the result differs from the committed file. The `tailwind-css-drift` hook and CI run it:

```bash
python scripts/dev/tailwind_build.py --check
```

```text
[tailwind_build] building static\css\tailwind.css
Done in 170ms
```

Exit 0 means the committed CSS matches its source. On drift, the command prints the differing lines and an `ERROR` line that tells you to run the build without `--check` and commit the result. Editing the generated CSS by hand does not help, because the check rebuilds it.

## Frontend browser gate

The `browser` tests, the Results behavior tests and the full-page gate drive a real browser. Run one of them at a time on a machine, because concurrent Playwright runs can fail with network buffer errors (`ERR_NO_BUFFER_SPACE`).

`scripts/dev/results_behavior_tests.py` runs isolated Chromium tests against the Results page scripts. It uses a controlled clock and no Flask server. It covers Artist Spotlight rotation, tooltips, keyboard access and reduced motion. CI runs it in the `browser` job, and it is separate from the `pytest` count:

```bash
python scripts/dev/results_behavior_tests.py
```

```text
test_tooltip_waits_and_cancels_short_hover (__main__.ResultsBehaviorTests.test_tooltip_waits_and_cancels_short_hover)
A short hover never reveals the hint; a sustained hover does. ... ok
----------------------------------------------------------------------
Ran 28 tests in 6.855s

OK
```

`scripts/dev/frontend_gate.py` is the full-page gate. It starts the real Flask app on `127.0.0.1` with port `0`, so the operating system picks a free port, and it stops the server in a `finally` block. Chromium runs every check; Firefox runs the static-assets and theme-token canary. The check list is `config/frontend_gate_checks.toml`, and the checks live in `scripts/dev/_frontend_gate_*.py`. Use `--headed` to watch the browser windows.

```bash
python scripts/dev/frontend_gate.py
```

```text
[frontend_gate] 58 of 58 checks selected; disabled: none
...
[frontend_gate] 58 checks passed in 89 runs across chromium, firefox (static assets & tokens canary on firefox); profiles: desktop, mobile, wide touch
```

The run exited 0. Flask log lines fill the middle; ignore them, including `Failed to fetch Spotify token`, which the app logs when Spotify rejects the placeholder credentials the gate uses. Only the `checks selected` line, the `FAIL` lines and the exit code report the result. The first line comes before any browser starts, and it refuses a manifest that names an unknown check or disables a required one.

The gate asserts computed values rather than class names. It reads `getComputedStyle` and real geometry, checks contrast on every surface a token can sit on, and measures the page at mobile, 1080p, 1440p and 4K sizes plus a wide touch screen. A failure names the browser, the check, the profile and the measured value against its limit, for example `FAIL chromium: divider contrast [desktop]: ... composites to 1.00:1 ..., expected at least 3:1`. Fix the value in the source CSS, rebuild with `tailwind_build.py`, and run the gate again. `docs/agents/ui-accessibility.md` owns the unit, touch-target, motion and keyboard rules these checks enforce.

## Continuous integration

The workflow is `.github/workflows/test.yml`, named Quality Gate. It runs on pushes to `main` and `wip/**`, on every pull request, and on manual dispatch. Four jobs run, and the last one is the single required check:

1. `changes` classifies the pull request. It is docs-only when every changed path is under `docs/` or `.superpowers/`, ends in `.md`, or is `config/docsync.toml`. Any git failure counts as not docs-only.
2. `checks` installs `requirements-dev.txt`, runs the docsync preflight, `pre-commit run --all-files`, and `pytest -m "not browser"` with the 70 percent coverage floor. An advisory `pip-audit` step scans both requirements files and does not fail the job.
3. `browser` installs Chromium and Firefox, then runs `pytest -m browser -q`, `scripts/dev/results_behavior_tests.py` and `scripts/dev/frontend_gate.py`, in that order. It is skipped for a docs-only pull request.
4. `quality-gate` aggregates the other three and passes when `changes` and `checks` succeeded and `browser` succeeded or was skipped for a docs-only change.

The path rules and the aggregation rule live in `scripts/dev/ci_jobs.py`, and `tests/test_ci_workflows.py` covers the workflow. You can ask the classifier directly. It reads NUL-separated paths from standard input, in a POSIX shell:

```bash
printf 'docs/ARCHITECTURE.md\0README.md\0' | python scripts/dev/ci_jobs.py docs-only
printf 'docs/ARCHITECTURE.md\0static/js/heatmap.js\0' | python scripts/dev/ci_jobs.py docs-only
```

```text
true
false
```

Merging a pull request to `main` deploys the app to Fly.io. The trigger is configured outside this repository, so the workflow file does not show it. [DEPLOY.md](DEPLOY.md) covers the release command, the machine settings and recovery steps.

## Probe a running instance

Two scripts under `scripts/testing/` drive a live instance over HTTP. `smoke_cache_check.py` runs one or more identical searches (`--runs`) and reports whether a later run found album metadata in the Postgres cache. `concurrent_users_test.py` fires simultaneous searches (`--concurrency`, default 3) and reports each outcome against the job-slot limit. Both call real providers through the instance, so this page shows their usage text only:

```bash
python scripts/testing/smoke_cache_check.py --help
```

```text
usage: smoke_cache_check.py [-h] [--base-url BASE_URL] [--username USERNAME]
                            [--year YEAR] [--sort-by {playcount,playtime}]
...
```

Point `--base-url` at a local instance, never at production without the owner's approval.

## Troubleshooting

- **`ERROR WT012 detached HEAD`**: you are on a detached checkout. Create or switch to a named branch with the owner's direction, as the remediation line says. The guard never switches branches for you.
- **`ERROR WT003` or `WARNING WT010` from `pre-commit`**: the `worktree-alignment` hook is advisory and still reports `Passed`. `WT003` means a batch is active and your branch is not the batch's branch. Read the `Remediation:` line, and treat the code as a prompt to check your branch, not as a failed commit.
- **The first `tailwind_build.py` run prints `fetching` lines**: it is downloading the pinned binary and the two daisyUI files into `scripts/bin/`. Later runs reuse them.
- **A frontend gate log shows `Failed to fetch Spotify token`**: the gate runs with placeholder credentials, so Spotify rejects the token request. Only `FAIL` lines and the exit code are results.
- **A browser test or the gate cannot launch a browser**: run `python -m playwright install chromium firefox`, and run one browser job at a time.
- **`python init_db.py` prints `skipping schema init`**: `DATABASE_URL` is unset. `init_db.py` does not read `.env`; export the variable in your shell first.
- **The app refuses to start in production mode**: `SECRET_KEY` is weak or a provider key is missing. Development mode only warns.
- **`doc_state_sync.py --check` prints `WARNING DOC024` or a root `BATCH` file warning**: both are informational on this tree and leave the exit code at 0.
- **A hook rewrote a file during `pre-commit`**: `ruff format` and `end-of-file-fixer` fix files in place and exit 1. Stage the fixed files and commit again.
