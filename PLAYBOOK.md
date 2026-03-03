# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 16 is active.** Script Hygiene, Local Dev Hardening, and Integration
  Testing. Definition: `BATCH16_DEFINITION.md`.
  - WP-0: migrate `smoke_cache_check.py` to `scripts/testing/`; create `scripts/dev/`. **Done.**
  - WP-1: extract `_http_client.py`; fix CSRF; update verdict to `db_cache_lookup_hits`; docstrings. **Done.**
  - WP-2: 13 unit tests for `_http_client` + `smoke_cache_check`. **Done.**
  - WP-3: `scripts/dev/dev_start.py` Docker+Flask startup helper. **Done.**
  - WP-4: `concurrent_users_test.py` + 6 unit tests. **Next.**
  - WP-5: README local dev section + SESSION_CONTEXT final sync. **Pending.**
- **Batch 15 is complete.** All 6 WPs done.
  Definition: `docs/history/definitions/BATCH15_DEFINITION.md`.
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days
    (Last.fm-only, lighter background task).

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-03-03 - WP-3: add dev_start.py Docker+Flask startup helper (Batch 16 WP-3)

**Scope:** Provide a single-command local dev startup helper that checks and
starts the `ss-postgres` Docker container then replaces the current process
with Flask. Eliminates the need to consult MEMORY.md or SESSION_CONTEXT for
manual Docker steps. Update AGENTS.md and SESSION_CONTEXT to reference the
script as the primary local dev startup method.

**Plan:** Per BATCH16_DEFINITION WP-3: `scripts/dev/dev_start.py` with three
functions (`check_container_status`, `start_container`, `main`) and comprehensive
docstrings. AGENTS.md Environment Setup: add `dev_start.py` sentence after the
`init_db.py` caveat. SESSION_CONTEXT Section 8: replace manual Docker step with
one-command startup reference.

**Implementation:** Created `scripts/dev/dev_start.py` (135 lines): module-level
docstring with usage + prerequisites; `check_container_status` uses
`docker inspect --format={{.State.Status}}` and returns `None` for absent
containers; `start_container` calls `docker start` and raises `RuntimeError` on
non-zero exit; `main` branches on status (running / exited+paused / None /
unexpected) with all output prefixed `[dev_start]`; `os.execvp` replaces the
process with Flask with inline comments on why execvp over subprocess.

**Deviations:** None.

**Validation:** `pytest -q` -- **333 passed**. `pre-commit run --all-files` -- all
hooks pass. Manual acceptance test: (1) container running -> prints "already running",
continues; (2) container exited -> starts container, prints "started ss-postgres",
continues; (3) absent container name -> prints error with instructions, exits 1.

**Forward guidance:** WP-4 is next: `scripts/testing/concurrent_users_test.py` +
6 unit tests. Depends on `_http_client.py` from WP-1 (already available).

### 2026-03-03 - WP-2: add 13 unit tests for _http_client and smoke_cache_check (Batch 16 WP-2)

**Scope:** Add automated regression coverage for the HTTP client and smoke-test
logic added in WP-1. All tests use mocked sessions; no live server required.

**Plan:** Per BATCH16_DEFINITION WP-2: create `tests/scripts/testing/` (mirrors
`scripts/testing/` source tree, per owner SoC directive) with 13 unit tests across
8 functions: `fetch_csrf_token` (2), `submit_job` (3), `poll_until_complete` (3),
`run_once` (1), `print_run_summary` (1), `build_parser` (1), verdict logic (2).

**Implementation:** Created `tests/scripts/__init__.py`, `tests/scripts/testing/__init__.py`,
and `tests/scripts/testing/test_smoke_cache_check.py` (13 tests). Fixed a correctness
gap in `smoke_cache_check.py`: when executed directly (`python scripts/testing/...`)
the script failed with `ModuleNotFoundError: No module named 'scripts'` because Python
adds the script directory, not the repo root, to sys.path. Added a `sys.path.insert`
guard (6 lines) at module level to insert `_REPO_ROOT` when missing; pytest is
unaffected (its `pythonpath="."` already covers this). Test folder placement in
`tests/scripts/testing/` deviates from the definition's `tests/test_smoke_cache_check.py`
per owner instruction to apply SoC.

**Deviations:** (1) Test file placed in `tests/scripts/testing/` instead of
`tests/test_smoke_cache_check.py` -- per owner SoC directive. (2) `smoke_cache_check.py`
received a `sys.path` fix so the direct `python scripts/testing/smoke_cache_check.py`
invocation works; WP-1 acceptance criteria required this but it was missed.

**Validation:** `pytest -q` -- **333 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0. Live smoke test:
`verdict=PASS`, `db_cache_lookup_hits=388` on run 2, elapsed delta ~18s (warm cache
~6x faster than cold fetch).

**Forward guidance:** WP-3 is next: `scripts/dev/dev_start.py` Docker+Flask startup
helper. Standalone -- no dependencies on WP-2.

### 2026-03-03 - WP-1: extract _http_client, fix CSRF, update verdict key (Batch 16 WP-1)

**Scope:** Extract shared HTTP transport into `scripts/testing/_http_client.py`;
refactor `smoke_cache_check.py` to import from it; fix CSRF token handling so the
script works without disabling Flask-WTF protection; update verdict branch to use
`db_cache_lookup_hits`; add comprehensive docstrings to all functions.

**Plan:** Per BATCH16_DEFINITION WP-1: create `_http_client.py` with
`fetch_csrf_token()`, `submit_job()`, `poll_until_complete()`. Remove `start_job()`
and `poll_job()` from smoke script; replace with imports. Fix regex: old code used
`window.SCROBBLE = {...}` pattern but the loading template uses a
`<script id="scrobble-config" type="application/json">` tag -- updated to
`SCROBBLE_CONFIG_RE`. Change verdict from `cache_hits` to `db_cache_lookup_hits`.

**Implementation:** Created `_http_client.py` (267 lines) with 3 public functions,
2 compiled regex constants, comprehensive NumPy-style docstrings, and inline
comments on non-obvious logic. Refactored `smoke_cache_check.py` (276 lines):
removed `start_job`, `poll_job`, `JOB_JSON_RE`, `json`, `re` imports; added import
from `_http_client`; verdict branch now reads `db_cache_lookup_hits` (lines 259-260);
all retained functions have comprehensive docstrings.

**Deviations:** Discovered the existing `JOB_JSON_RE` regex
(`window.SCROBBLE = {...}`) would not match the actual loading template, which uses
`JSON.parse(document.getElementById('scrobble-config').textContent)`. Replaced with
`SCROBBLE_CONFIG_RE` targeting the `<script id="scrobble-config">` tag. This is a
correctness fix, not a scope addition.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-2 is next: add 13 unit tests for `_http_client` and
`smoke_cache_check` in `tests/test_smoke_cache_check.py`.

### 2026-03-03 - WP-0: migrate smoke_cache_check to scripts/testing/ (Batch 16 WP-0)

**Scope:** Create `scripts/testing/` and `scripts/dev/` directories with `__init__.py`;
move `smoke_cache_check.py` via `git mv`; update README.md tree and command references.

**Plan:** Per BATCH16_DEFINITION WP-0: create directories, `git mv`, update doc path
references. No logic changes.

**Implementation:** Created `scripts/testing/__init__.py` and `scripts/dev/__init__.py`.
`git mv scripts/smoke_cache_check.py scripts/testing/smoke_cache_check.py`. Fixed
README.md project tree (corrected broken nesting where docsync children appeared under
testing/) and updated smoke test command path. Replaced hardcoded username with
placeholder `YOUR_USERNAME` in README. No references found in AGENTS.md or
SESSION_CONTEXT.md requiring update.

**Deviations:** README tree structure from prior edit was malformed (docsync sub-items
nested under testing/ instead of docsync/) -- corrected in this WP.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-1 is next: extract `_http_client.py` from
`smoke_cache_check.py`, fix CSRF token handling, update verdict key to
`db_cache_lookup_hits`, add comprehensive docstrings.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-03-03 - Fix Windows asyncpg startup packet (ProactorEventLoop) (side-task)

**Scope:** Side-task -- two-stage Windows-only cache fix. No code changes for
the Fly.io (Linux) deployment path.

**Errors encountered and resolved (session log):**

1. `.env` typo `DDATABASE_URL` (double-D prefix) -- cache silently disabled.
   Fixed by correcting the typo in `.env`.

2. `os.environ.get("DATABASE_URL")` returned `None` in background worker threads
   on Windows. Werkzeug debug reloader spawns a child process; `load_dotenv()`
   ran in the parent but environment variables were not reliably inherited.
   Fixed in `468b519`: capture `_DATABASE_URL = os.environ.get("DATABASE_URL")`
   at module import time in `cache.py` (runs once after `app.py` calls
   `load_dotenv()`). Also path-anchored `load_dotenv()` in `app.py` so it
   finds `.env` regardless of working directory.

3. `_DATABASE_URL` confirmed set (len=59) but asyncpg still failed silently.
   Docker logs revealed: `invalid length of startup packet` (10 rapid rejections
   -- matching 3 retries x multiple test runs). Root cause: `asyncio.new_event_loop()`
   in a daemon thread under Werkzeug's debug reloader on Windows creates a
   `SelectorEventLoop`, not a `ProactorEventLoop`. asyncpg uses Windows IOCP
   via `ProactorEventLoop`; with `SelectorEventLoop` it sends incorrect startup
   bytes and Postgres rejects the connection immediately.
   Fixed in `97db0c9`: `background_task()` in `orchestrator.py` now calls
   `asyncio.ProactorEventLoop()` when `sys.platform == "win32"`, falling back to
   `asyncio.new_event_loop()` on all other platforms (Linux/Fly.io unchanged).

4. `RotatingFileHandler` fails with `PermissionError: [WinError 32]` when
   multiple Flask processes hold the log file open simultaneously (Werkzeug
   debug reloader + interleaved restarts). Cosmetic only -- Flask continues to
   serve. Not fixed; documented here for future reference.

**Deploy safety:** Fix 3 uses `if sys.platform == "win32":` guard exclusively.
Fly.io (Linux) takes `asyncio.new_event_loop()` unchanged.

**Implementation:**
- `scrobblescope/orchestrator.py` -- `background_task()` updated (`97db0c9`)
- `scrobblescope/cache.py` -- `_DATABASE_URL` captured at module level (`468b519`)
- `app.py` -- path-anchored `load_dotenv()` (`468b519`)
- `tests/test_repositories.py` -- 4 tests updated to patch
  `scrobblescope.cache._DATABASE_URL` directly instead of `os.environ` (`468b519`)

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. Smoke test: `verdict=PASS`, `db_cache_lookup_hits=44`, elapsed ~1.05s
(vs ~6s cold Spotify fetch). Fly.io deploy path confirmed unaffected by guard.

**Forward guidance:** Cache subsystem is fully working locally. WP-2 is next:
13 unit tests for `_http_client` and `smoke_cache_check` in
`tests/test_smoke_cache_check.py`.

### 2026-03-03 - Improve agent orientation docs (side-task)

**Scope:** Side-task -- documentation only, no code changes. Improve agent
bootstrap reliability by fixing stale references and adding missing setup steps.

**Changes:**
- DEVELOPMENT.md: replaced stale "SESSION_CONTEXT is gitignored/ephemeral" text
  (lines 83-93) with accurate description of committed+tracked status, explicit
  `.gitignore` exception, and rationale for sharing across agents.
- AGENTS.md Environment Setup: added venv activation commands (Windows + Linux)
  so agents can run `pytest` and `pre-commit` without trial-and-error.
- AGENTS.md "What to update after a WP": added README deferral exception noting
  that README updates may be batched into a dedicated WP when the batch definition
  specifies one (e.g., Batch 16 WP-5).

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-1 is next. README will be stale during intermediate WPs;
updates deferred to WP-5 per batch definition.

### 2026-03-03 - Batch 16 definition written and activated (Batch 16 activation)

**Scope:** Define Batch 16 and activate it in PLAYBOOK + SESSION_CONTEXT.

**Plan:** Write `BATCH16_DEFINITION.md` incorporating audit corrections (stat key
fix, size caps removed, MEMORY.md references clarified as agent-private). Move to
`docs/history/definitions/`. Activate Batch 16 in PLAYBOOK Section 3. Update
SESSION_CONTEXT Section 2. Update HANDOFF_PROMPT.md and MEMORY.md for handoff.

**Implementation:** Definition written; audit findings applied (verdict key
`cache_hits` corrected to `db_cache_lookup_hits`, size caps removed per owner
instruction, `memory/MEMORY.md` removed from formal acceptance criteria). Definition
placed at `BATCH16_DEFINITION.md` (root; moves to archive at batch close-out). PLAYBOOK and
SESSION_CONTEXT activated. HANDOFF_PROMPT and MEMORY updated for clean handoff.

**Deviations:** None.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-0 is next: create `scripts/testing/` and `scripts/dev/`
directories, move `smoke_cache_check.py` via `git mv`, update AGENTS.md and
SESSION_CONTEXT path references. No logic changes in WP-0.

### 2026-03-03 - Fix SESSION_CONTEXT.md commit convention and stage accumulated changes

**Scope:** Side-task -- documentation and gitignore fix, no code changes.

**What:** SESSION_CONTEXT.md was never staged in the two previous side-task commits
(`c4bf737`, `4f1cf6a`) despite commit messages implying it. SESSION_CONTEXT.md has
been git-tracked since before `edee612` (when `.claude/` was added to .gitignore).
The `.gitignore` entry `.claude/` is misleading -- SESSION_CONTEXT.md is grandfathered
in as a tracked file. Fix: update `.gitignore` to `.claude/*` + `!.claude/SESSION_CONTEXT.md`
so the exception is explicit. Fix AGENTS.md: remove incorrect "SESSION_CONTEXT is
gitignored" language. Stage the accumulated SESSION_CONTEXT.md changes (Batch 15 state
update, Section 8 browser MCP note, Section 8 local Postgres note).

**Why:** SESSION_CONTEXT.md is the shared cross-agent dashboard. All agents (Gemini,
Copilot, Codex, Claude Code) bootstrap from it. Leaving it uncommitted means every agent
starts with stale branch, test count, and batch status. The gitignore fix makes the
tracked-exception visible and prevents future agents from falsely concluding the file
is machine-local.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. BATCH16_PROPOSAL.md written; awaiting owner review.
