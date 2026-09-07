# ScrobbleScope Session Context

Last updated: 2026-09-05

---

## 1. Current state

| Item | Value |
|------|-------|
| Branch | `wip/batch-21` |
| Tests | **894 passing** across 40 test modules |
| Coverage | 89% (2026-08-20 run, `pytest --cov=scrobblescope`) |
| Pre-commit | All hooks pass |
| Batches 0-20 | **All complete.** PLAYBOOK Section 2 has the index: title, definition and log per batch. |
| Batch 21 status | **Active.** WP-0 through WP-4 are done. Owner-review remediation Task 2 merged as PR #224; Task 3 (final `3fr 4fr` split, `28rem` form cap, raised divider contrast, ruled header clamps) is implemented and gate-validated (complete Chromium+Firefox matrix). Task 3 review fix round 1/5 (F-B21-40, index well divider) and fix round 2/5 (hero fills its padded column in every state) are landed. Tasks 4-6 (loading-progress alignment, unmatched no-data surface, accessibility pass) remain open. WP-6 is absorbed into WP-3; WP-7 and WP-8 keep their numbers. Adobe Fonts kit `rwy8ghw` remains active. Definition: `BATCH21_DEFINITION.md`. See PLAYBOOK Sections 3-4 for the work order and history. |
| Known open risk | `RotatingFileHandler` throws `PermissionError: [WinError 32]` on Windows when multiple Flask processes hold the log file open (Werkzeug debug reloader). Cosmetic -- Flask continues to serve. Linux/Fly.io unaffected. |

**Key runtime facts:**
- `MAX_ACTIVE_JOBS` (default 5 since 2026-07-31; was 10) caps concurrent
  background jobs via `worker.py`.
- `_GlobalThrottle` in `utils.py` caps aggregate API throughput across all threads.
- `_cache_lock` in `utils.py` guards `REQUEST_CACHE` thread safety.
- `_PLAYTIME_ALBUM_CAP = 500` in `orchestrator.py` limits Spotify fetch for playtime sort.
- Cold-start validated 2026-02-19 (both app + DB auto-wake on demand).
- DB cache validated working locally 2026-03-03: `verdict=PASS`, `db_cache_lookup_hits=44`,
  elapsed ~1.05s. Requires `ss-postgres` Docker container running and `DATABASE_URL` in `.env`.
- Heatmap fetch speed is rate-limit bound; measurement and rationale live in
  FINDINGS.md F-B18-11 (single source).

---

## 2. Execution status (machine-managed)

`PLAYBOOK.md` is the source of truth. Block below managed by `doc_state_sync.py`.

<!-- DOCSYNC:STATUS-START -->
- Source of truth: `PLAYBOOK.md` (Section 3 and Section 4).
- Current batch: Batch 21.
- Current-batch entries in active log block: 7.
- Completed work packages in current-batch entries: WP-0, WP-1, WP-2, WP-3, WP-4.
- Next expected work package: WP-5.
- Latest validated test count: **894 passed**.
- Newest current-batch entry: 2026-08-27 - Unified loading and recent-result recovery completed (Batch 21 WP-4).
<!-- DOCSYNC:STATUS-END -->

---

## 3. Project structure

```
app.py                      # create_app() factory (~150 lines)
scrobblescope/
  config.py                 # env var reads, API keys, concurrency constants
  errors.py                 # SpotifyUnavailableError, ERROR_CODES
  domain.py                 # normalize_name, normalize_track_name
  utils.py                  # rate limiters, session pooling, request caching
  repositories.py           # JOBS dict, jobs_lock, job state CRUD
  worker.py                 # semaphore, acquire/release_job_slot, start_job_thread
  cache.py                  # asyncpg DB helpers (retry/backoff, batch lookup/persist)
  lastfm.py                 # check_user_exists, fetch_recent_tracks (pure HTTP client)
  spotify.py                # fetch_spotify_access_token, search, batch details
  orchestrator.py           # process_albums, _fetch_and_process, background_task, fetch_top_albums_async
  heatmap.py                # heatmap_task, _fetch_and_process_heatmap, _aggregate_daily_counts
  routes.py                 # Flask Blueprint, all route + error handlers
templates/                  # base, index, loading, results, unmatched, error
  inline/                   # scrobblescope_pinwheel.svg, scrobble_scope_inline.svg (wordmark), scrobble_scope_lockup_inline.svg (header)
  partials/                 # _loading.html (framework-neutral wait panel), _heatmap_form.html, _heatmap_result.html
static/
  css/                      # global, index, loading, results, unmatched, error, empty, heatmap, shell, tailwind.src.css, tailwind.css (11 files)
  js/                       # theme, index, loading, results, unmatched, heatmap (6 files)
scripts/
  bin/                       # gitignored verified Tailwind/daisyUI artifact cache
  doc_state_sync.py         # thin entry point for deterministic documentation sync
  dev/
    dev_start.py            # Postgres container check plus Flask launch
    tailwind_build.py       # verified standalone Tailwind + daisyUI frontend builder
    frontend_gate.py        # browser checks Chromium and Firefox run against the live app
    _worktree_guard_types.py # immutable public diagnostic value types
    _worktree_guard_diagnostics.py # stable construction, offline, WT014
    _worktree_guard_lineage.py # PLAYBOOK parsing and pure classification
    _worktree_guard_runner.py # sanitized Git runner and discovery parsing
    _worktree_guard_inspection.py # read-only collection orchestration
    _worktree_guard_venv.py # primary environment topology and tool paths
    worktree_guard.py       # stable public re-export facade
    check_worktree_alignment.py # thin read-only bootstrap CLI
  docsync/
    __init__.py             # package inventory and entry-point map
    models.py               # typed sync results, entries, issues, and SyncError
    parser.py               # Markdown sections, markers, entries, and batch state
    renderer.py             # managed status, PLAYBOOK, and archive rendering
    logic.py                # rotation, deduplication, and authoritative test count
    declarations.py         # declared DOC009-DOC011 value, anchor, and retired-claim checks
    integrity.py            # live-document semantic integrity diagnostics
    cli.py                  # file I/O, final-state enforcement, and exit codes
  testing/
    _http_client.py         # shared HTTP helper for the manual test scripts
    smoke_cache_check.py    # DB cache smoke verification
    concurrent_users_test.py # manual concurrency probe
```

---

## 4. Module dependency graph (acyclic)

```
errors.py        <- (leaf)
domain.py        <- (leaf)
config.py        <- (leaf)
utils.py         <- config
cache.py         <- config
worker.py        <- config
repositories.py  <- config, errors
lastfm.py        <- config, utils
spotify.py       <- config, utils
orchestrator.py  <- cache, config, domain, errors, lastfm, repositories, spotify, utils, worker
heatmap.py       <- lastfm, repositories, utils, worker
routes.py        <- heatmap, lastfm, orchestrator, repositories, utils, worker
app.py           <- routes (Blueprint); config (ensure_api_keys, __main__ only)

docsync/__init__.py  <- (leaf)
docsync/models.py    <- (leaf)
docsync/parser.py    <- docsync/models
docsync/renderer.py  <- docsync/models, docsync/parser
docsync/logic.py     <- docsync/models, docsync/parser, docsync/renderer
docsync/declarations.py <- docsync/models
docsync/integrity.py <- docsync/declarations, docsync/logic, docsync/models, docsync/parser, docsync/renderer
docsync/cli.py       <- docsync/integrity, docsync/logic, docsync/models
doc_state_sync.py    <- docsync/cli
dev/_worktree_guard_types.py <- (leaf; standard library only)
dev/_worktree_guard_diagnostics.py <- dev/_worktree_guard_types
dev/_worktree_guard_lineage.py <- dev/_worktree_guard_diagnostics, dev/_worktree_guard_types
dev/_worktree_guard_runner.py <- dev/_worktree_guard_types
dev/_worktree_guard_venv.py <- dev/_worktree_guard_diagnostics, dev/_worktree_guard_types
dev/_worktree_guard_inspection.py <- dev/_worktree_guard_diagnostics, dev/_worktree_guard_lineage, dev/_worktree_guard_runner, dev/_worktree_guard_types, dev/_worktree_guard_venv
dev/worktree_guard.py <- dev/_worktree_guard_diagnostics, dev/_worktree_guard_inspection, dev/_worktree_guard_lineage, dev/_worktree_guard_runner, dev/_worktree_guard_types, dev/_worktree_guard_venv
dev/check_worktree_alignment.py <- dev/worktree_guard
dev/dev_start.py <- (leaf; standard library only)
dev/tailwind_build.py <- (leaf; standard library only)
dev/frontend_gate.py <- app.py (create_app); werkzeug.serving; playwright (imported late)
```

---

## 5. Architecture overview

Compact bootstrap summary. Full diagrams, with both pipelines and every edge
verified against source, are indexed by `docs/ARCHITECTURE.md` -- keep detail
in its focused owner files rather than growing a second copy here.

```
User submits form (index.html)
  -> POST /results_loading (routes.py)
    -> cleanup_expired_jobs()
    -> acquire_job_slot() [worker.py] -- BEFORE create_job; on failure the
       request is rejected and no job is created
    -> create_job(params) -> UUID in JOBS dict
    -> start_job_thread(background_task, args=(...)) [worker.py]
       -- worker runs an injected callable; it does not import orchestrator
       -- on failure, start_job_thread releases the slot before re-raising,
         then the route deletes the newly created job
    -> Renders loading.html with job_id

background_task (orchestrator.py, daemon Thread):
  -> asyncio event loop -> _fetch_and_process(...)
    -> Fetch Last.fm scrobbles (paginated, async)
    -> Group into albums, filter by thresholds
    -> process_albums (5-phase cache flow):
      1: DB connect + batch lookup (30-day TTL)
      2: Partition cache_hits / cache_misses
      3: Spotify fetch for misses only
      4: DB batch persist + conn.close() in finally
      5: Build results -> set_job_results()

loading.js polls GET /progress?job_id=...
  -> 100% + no error -> GET /results?job_id=... -> renders results.html
  -> error + retryable -> show Retry button
```

---

## 6. Test structure (894 tests)

The per-file breakdown used to live here as a 40-row table. It was
removed on 2026-08-26: nothing read it, only the total is gated, and it
drifted three times during Batch 21 -- each drift a false fact in the document
agents bootstrap from. Derive it instead, which cannot go stale:

```
pytest --collect-only -q tests | grep "::" | cut -d: -f1 | sort | uniq -c | sort -rn
```

The total above is machine-managed. Section 2's STATUS block is the authority
and `doc_state_sync.py --fix` writes it; see PLAYBOOK Section 4.

Layout: `tests/` mirrors the package, with `tests/scripts/dev/` covering the
developer tooling and `tests/services/` the Last.fm and Spotify paths.

---

## 7. Environment notes

- Python 3.13.3, Windows 11, venv.
- Pre-commit: black, isort, autoflake, flake8, trailing whitespace, end-of-file, check yaml, check-merge-conflict, detect-private-key, doc-state-sync-check, tailwind-css-drift.
- pytest in `pyproject.toml` sets only `pythonpath = "."`; no `asyncio_mode` key is
  configured anywhere, so pytest-asyncio's own default applies.
- API keys in `.env` (git-ignored); template: `.env.example`.
- Gunicorn compat: `app = create_app()` at module level in `app.py`.
- worker.py ADR archived at `docs/history/reports/WORKER_ADR_2026-02-20.md`.
- Browser MCP runs in Docker: use `http://host.docker.internal:5000/` for local app access (not `localhost`).
- Local Postgres cache: Docker container `ss-postgres`, volume `ss-postgres-data`.
  Connection: `postgresql://postgres:postgres@localhost:5432/scrobblescope`.
  **One-command startup:** `python scripts/dev/dev_start.py` -- checks/starts container, then launches Flask (`--workers 1 --threads 4` in production via Dockerfile).
  Manual fallback: `docker start ss-postgres` then `python app.py`.
  Check status: `docker ps --filter name=ss-postgres`.
  `init_db.py` has no `load_dotenv()` -- set DATABASE_URL in shell before running it.
- Windows asyncio: `background_task()` in `orchestrator.py` explicitly uses
  `asyncio.ProactorEventLoop()` on `sys.platform == "win32"`. This is required
  because Werkzeug's debug reloader leaves `SelectorEventLoop` as the thread-local
  policy in background threads on Windows; asyncpg sends incorrect PostgreSQL
  startup bytes with `SelectorEventLoop`, causing the `invalid length of startup
  packet` error. The guard is Windows-only; Fly.io (Linux) is unaffected.
