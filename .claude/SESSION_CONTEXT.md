# ScrobbleScope Session Context

Last updated: 2026-08-23

---

## 1. Current state

| Item | Value |
|------|-------|
| Branch | `wip/batch-21` |
| Tests | **666 passing** across 39 test modules |
| Coverage | 89% (2026-08-20 run, `pytest --cov=scrobblescope`) |
| Pre-commit | All hooks pass |
| Batch 13 status | **Complete**. All 5 WPs done. Definition: `docs/history/definitions/BATCH13_DEFINITION.md`. |
| Batch 14 status | **Complete**. All 5 WPs done. Definition: `docs/history/definitions/BATCH14_DEFINITION.md`. |
| Batch 15 status | **Complete**. All 6 WPs done. Definition: `docs/history/definitions/BATCH15_DEFINITION.md`. |
| Batch 16 status | **Complete**. All 6 WPs done. Definition: `docs/history/definitions/BATCH16_DEFINITION.md`. |
| Batch 17 status | **Complete**. All 4 WPs done (WP-5 dropped). Definition: `docs/history/definitions/BATCH17_DEFINITION.md`. |
| Batch 18 status | **Complete**. All 5 WPs done. Definition: `docs/history/definitions/BATCH18_DEFINITION.md`. |
| Batch 19 status | **Complete**. All 5 WPs done plus owner-review follow-up. Definition: `docs/history/definitions/BATCH19_DEFINITION.md`. PR #152 merged to `main`. |
| Batch 20 status | **Complete**. All 9 WPs done. Definition: `docs/history/definitions/BATCH20_DEFINITION.md`. |
| Batch 21 status | **Active.** UI overhaul: Tailwind + daisyUI migration, warm theme propagation. WP-0, WP-1 and WP-2 are done. WP-2 landed the base shell, the `error.html` pilot, the `tailwind-css-drift` pre-commit hook and `scripts/dev/frontend_gate.py` (Playwright, pinned `playwright==1.62.0`); it closed F-B21-2, F-B21-7 and F-AUDIT-1 and filed F-B21-10 and F-B21-11. The type stack is Adobe Fonts kit `rwy8ghw`, reversing the self-hosted ruling on 2026-08-22. **Do not push the WP-2 gate commit alone** -- the Quality Gate runs on push to `wip/**` and the frontend gate fails until the shell commit lands with it. The root-hygiene side task closed 2026-08-20 (the owner rejected the audience-banner scheme). The front-end design handoff was imported to `docs/design/` on 2026-08-21; `docs/design/README.md` is the canonical design spec and `docs/design/RECONCILIATION.md` is the repo's override list. **WP-3 is next.** The repository-integrity gate and split worktree guard shipped via PR #169 (merged 2026-08-08), F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2 are resolved. PR #170 merged 2026-08-12 (`5b060a2`), remediating the four round-6 findings that had merged unaddressed. The F-SWE-1 audit ran 2026-08-20 and blocked migration on F-SWE-2 (report: `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`); the charter is retired. F-SWE-2 was resolved 2026-08-20 in its standalone prerequisite commit. Definition: `BATCH21_DEFINITION.md`. |
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
- Current-batch entries in active log block: 5.
- Completed work packages in current-batch entries: WP-0, WP-1, WP-2.
- Next expected work package: WP-3.
- Latest validated test count: **666 passed**.
- Newest current-batch entry: 2026-08-23 - Base shell, error-page pilot, and two new gates (Batch 21 WP-2).
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
  inline/                   # scrobblescope_pinwheel.svg, scrobble_scope_inline.svg (wordmark)
static/
  css/                      # global, index, loading, results, unmatched, error, heatmap, tailwind.src.css, tailwind.css (9 files)
  js/                       # theme, index, loading, results, unmatched, error, heatmap (7 files)
scripts/
  bin/                       # gitignored verified Tailwind/daisyUI artifact cache
  doc_state_sync.py         # thin entry point for deterministic documentation sync
  dev/
    dev_start.py            # Postgres container check plus Flask launch
    tailwind_build.py       # verified standalone Tailwind + daisyUI frontend builder
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
docsync/integrity.py <- docsync/logic, docsync/models, docsync/parser, docsync/renderer
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
  -> 100% + no error -> POST /results_complete -> renders results.html
  -> error + retryable -> show Retry button
```

---

## 6. Test structure (666 tests)

| File | Count |
|------|-------|
| scripts/dev/test_dev_start.py | 11 |
| scripts/dev/test_frontend_gate.py | 7 |
| scripts/dev/test_tailwind_build.py | 37 |
| scripts/dev/test_tailwind_build_cli.py | 11 |
| scripts/dev/test_worktree_guard.py | 23 |
| scripts/dev/test_worktree_guard_base_ref.py | 6 |
| scripts/dev/test_worktree_guard_cli.py | 5 |
| scripts/dev/test_worktree_guard_cli_e2e.py | 11 |
| scripts/dev/test_worktree_guard_inspection.py | 14 |
| scripts/dev/test_worktree_guard_playbook.py | 15 |
| scripts/dev/test_worktree_guard_runner.py | 4 |
| scripts/dev/test_worktree_guard_severity.py | 15 |
| scripts/dev/test_worktree_guard_subject.py | 20 |
| scripts/dev/test_worktree_guard_topology.py | 7 |
| scripts/dev/test_worktree_guard_venv.py | 13 |
| scripts/testing/test_concurrent_users_test.py | 6 |
| scripts/testing/test_smoke_cache_check.py | 13 |
| services/test_lastfm_logic.py | 8 |
| services/test_lastfm_service.py | 9 |
| services/test_orchestrator_fetch_and_process.py | 10 |
| services/test_orchestrator_fetch_spotify.py | 8 |
| services/test_orchestrator_helpers.py | 18 |
| services/test_orchestrator_process_albums.py | 7 |
| services/test_spotify_service.py | 10 |
| test_app_factory.py | 6 |
| test_docsync_cli.py | 23 |
| test_docsync_integrity.py | 61 |
| test_docsync_logic.py | 32 |
| test_docsync_parser.py | 35 |
| test_docsync_renderer.py | 25 |
| test_docsync_test_count.py | 8 |
| test_domain.py | 13 |
| test_heatmap.py | 20 |
| test_repositories.py | 20 |
| test_retry_with_semaphore.py | 8 |
| test_routes.py | 67 |
| test_template_shell.py | 20 |
| test_utils.py | 34 |
| test_worker.py | 6 |

---

## 7. Environment notes

- Python 3.13.3, Windows 11, venv.
- Pre-commit: black, isort, autoflake, flake8, trailing whitespace, end-of-file, check yaml, check-merge-conflict, detect-private-key, doc-state-sync-check.
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
