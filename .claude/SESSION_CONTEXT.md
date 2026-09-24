# ScrobbleScope Session Context

Last updated: 2026-09-20

---

## 1. Current state

| Item | Value |
|------|-------|
| Branch | See PLAYBOOK Section 3 for the active worktree branch. |
| Tests | **1820 passing** across 67 test modules |
| Coverage | 89% (2026-08-20 run, `pytest --cov=scrobblescope`) |
| Pre-commit | See PLAYBOOK Section 4's latest validation and deviations. |
| Batches 0-20 | **All complete.** PLAYBOOK Section 2 has the index: title, definition and log per batch. |
| Batch 23 status | **Active**. WP-0 is next. Definition: `BATCH23_DEFINITION.md` (repository root). Opened 2026-09-21 on `feat/batch23-wp0-hygiene`: Spotify listeners import their Extended Streaming History export. |
| Batch 22 status | **Complete**. All 6 WPs done. Definition: docs/history/definitions/BATCH22_DEFINITION.md. Opened 2026-09-13 on `feat/batch22-enrichment` and closed 2026-09-20: album enrichment moved behind a provider contract, Deezer answers when Spotify cannot, and MusicBrainz corrects a reissue year to the original while the results page is open. Batch 21 is complete; its definition is at `docs/history/definitions/BATCH21_DEFINITION.md`, and the frontend and accessibility audit it chartered runs at Batch 23's close-out. Adobe Fonts kit `rwy8ghw` remains active. |
| Known open risk | `RotatingFileHandler` throws `PermissionError: [WinError 32]` on Windows when multiple Flask processes hold the log file open (Werkzeug debug reloader). Cosmetic -- Flask continues to serve. Linux/Fly.io unaffected. |

**Key runtime facts:**
- `MAX_ACTIVE_JOBS` (default 5 since 2026-07-31; was 10) caps concurrent
  background jobs via `worker.py`.
- `_GlobalThrottle` in `utils.py` caps aggregate API throughput across all threads.
- `_cache_lock` in `utils.py` guards `REQUEST_CACHE` thread safety.
- `_MAX_ALBUM_CAP = 500` in `orchestrator/__init__.py` limits Spotify fetch across all sort modes.
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
- Current batch: Batch 23.
- Current-batch entries in active log block: 0.
- Completed work packages in current-batch entries: none.
- Next expected work package: WP-0.
- Latest validated test count: **1820 passed**.
- Newest current-batch entry: none.
<!-- DOCSYNC:STATUS-END -->

---

## 3. Project structure

```
app.py                      # create_app() factory and startup checks
scrobblescope/
  config.py                 # env var reads, API keys, concurrency constants
  errors.py                 # SpotifyUnavailableError, ERROR_CODES
  domain.py                 # normalize_name, format_album_key, normalize_track_name, _matches_release_criteria, release_window
  api_logging.py            # provider-call trace hook, host-to-provider map, per-session tally and summary
  utils.py                  # rate limiters, session pooling, request caching
  repositories.py           # JOBS dict, jobs_lock, job state CRUD
  worker.py                 # semaphore, acquire/release_job_slot, start_job_thread, run_coroutine_in_new_loop
  cache.py                  # asyncpg DB helpers (retry/backoff, batch lookup/persist)
  lastfm.py                 # check_user_exists, fetch_recent_tracks (pure HTTP client)
  spotify.py                # fetch_spotify_access_token, search, batch details
  musicbrainz.py            # lookup_original_release (release-group first-release-date)
  release_checks.py         # correction worker: one thread, FIFO job queue, live original-release lookups
  orchestrator/
    __init__.py              # facade + pipeline glue: process_albums, _fetch_and_process, background_task, fetch_top_albums_async
    _search.py               # Spotify parallel-search phase
    _details.py              # Spotify batch-detail phase
    _cache.py                # DB metadata cache lookup/persist phase
    _results.py              # release-filter + sort + proportion phase (_build_results)
  heatmap.py                # heatmap_task, _fetch_and_process_heatmap, _aggregate_daily_counts
  spotlight.py              # pure artist aggregation and stable sample selection
  unmatched.py              # stable reason codes, category metadata, deterministic grouping
  routes/
    __init__.py              # facade: Blueprint bp, shared job-context helpers, error handlers
    pages.py                  # home page
    album_flow.py             # loading/results/unmatched pages + results_loading
    heatmap_flow.py           # heatmap page + heatmap_loading/heatmap_data
    api.py                    # validate_user, csrf-token, progress, unmatched JSON, release_checks JSON, artist_spotlight
templates/                  # base, index, loading, results, unmatched, error
  inline/                   # scrobblescope_pinwheel.svg, scrobble_scope_inline.svg (wordmark), scrobble_scope_lockup_inline.svg (header)
  partials/                 # _loading.html (framework-neutral wait panel), _heatmap_form.html, _heatmap_result.html
static/
  css/                      # global, index, loading, results, unmatched, error, empty, heatmap, shell, tailwind.src.css, tailwind.css (11 files)
  js/                       # theme, page_motion, index, loading, loading-progress, results, results-spotlight, unmatched, heatmap
scripts/
  bin/                       # gitignored verified Tailwind/daisyUI artifact cache
  doc_state_sync.py         # thin entry point for deterministic documentation sync
  dev/
    dev_start.py            # Postgres container check plus Flask launch
    tailwind_build.py       # verified standalone Tailwind + daisyUI frontend builder
    frontend_gate.py        # full Chromium checks and Firefox static-assets canary
    _frontend_gate_assets.py # stylesheet isolation
    _frontend_gate_colour.py # pure colour and contrast maths, re-exported by the gate
    _frontend_gate_forms.py # form validation, validator races, initial visibility
    _frontend_gate_layout.py # fonts, text scaling, touch targets, scale parity
    _frontend_gate_pipeline.py # loading composition, progress state machines, spotlight
    _frontend_gate_results.py # results controls and decoded CSV/JPEG export checks
    _frontend_gate_runtime.py # Playwright loading, browser launch, served app, route policy
    _frontend_gate_shared.py # page inventories and helpers two or more slices read
    _frontend_gate_theme.py # theme tokens, contrast, persistence, motion, mark
    _frontend_gate_unmatched.py # unmatched report contract and width sweep
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
api_logging.py   <- (leaf; standard library + aiohttp)
utils.py         <- api_logging, config
cache.py         <- config
worker.py        <- config
repositories.py  <- config, domain, errors
lastfm.py        <- config, utils
spotify.py       <- config, utils
unmatched.py     <- (leaf)
musicbrainz.py   <- config, domain, utils
release_checks.py <- cache, config, domain, musicbrainz, repositories, unmatched, utils, worker
orchestrator/__init__.py  <- cache, config, domain, errors, lastfm, release_checks, repositories, spotify, unmatched, utils, worker; orchestrator/_search, orchestrator/_details, orchestrator/_cache, orchestrator/_results (imported last, for re-export)
orchestrator/_search.py   <- config, domain, unmatched; orchestrator (facade, for patchable cross-cutting calls)
orchestrator/_details.py  <- config, domain; orchestrator (facade)
orchestrator/_cache.py    <- orchestrator (facade)
orchestrator/_results.py  <- domain, unmatched, utils; orchestrator (facade)
heatmap.py       <- lastfm, repositories, utils, worker
spotlight.py     <- utils
routes/__init__.py     <- config, domain, lastfm, repositories, spotify, unmatched, utils, worker; routes/album_flow, routes/api, routes/heatmap_flow, routes/pages (imported last, for re-export)
routes/pages.py         <- routes (facade)
routes/album_flow.py    <- orchestrator, repositories, spotlight; routes (facade)
routes/heatmap_flow.py  <- heatmap, repositories; routes (facade)
routes/api.py           <- domain, release_checks, repositories, spotify, utils; routes (facade)
app.py           <- routes (Blueprint); config (ensure_api_keys) -- both deferred into functions

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
dev/_frontend_gate_assets.py <- dev/_frontend_gate_shared
dev/_frontend_gate_colour.py <- (leaf; standard library only)
dev/_frontend_gate_forms.py <- dev/_frontend_gate_shared
dev/_frontend_gate_layout.py <- dev/_frontend_gate_colour, dev/_frontend_gate_shared
dev/_frontend_gate_pipeline.py <- dev/_frontend_gate_shared; repositories
dev/_frontend_gate_results.py <- repositories
dev/_frontend_gate_runtime.py <- dev/_frontend_gate_shared; app.py (create_app); repositories; werkzeug.serving; playwright (imported late)
dev/_frontend_gate_shared.py <- (leaf; standard library only)
dev/_frontend_gate_theme.py <- dev/_frontend_gate_colour, dev/_frontend_gate_shared; repositories
dev/_frontend_gate_unmatched.py <- repositories
dev/frontend_gate.py <- dev/_frontend_gate_assets, dev/_frontend_gate_colour, dev/_frontend_gate_forms, dev/_frontend_gate_layout, dev/_frontend_gate_pipeline, dev/_frontend_gate_results, dev/_frontend_gate_runtime, dev/_frontend_gate_shared, dev/_frontend_gate_theme, dev/_frontend_gate_unmatched
```

---

## 5. Architecture overview

Compact bootstrap summary. Full diagrams, with both pipelines and every edge
verified against source, are indexed by `docs/ARCHITECTURE.md` -- keep detail
in its focused owner files rather than growing a second copy here.

```
User submits form (index.html)
  -> POST /results_loading (routes/album_flow.py)
    -> cleanup_expired_jobs()
    -> acquire_job_slot() [worker.py] -- BEFORE create_job; on failure the
       request is rejected and no job is created
    -> create_job(params) -> UUID in JOBS dict
    -> start_job_thread(background_task, args=(...)) [worker.py]
       -- worker runs an injected callable; it does not import orchestrator
       -- on failure, start_job_thread releases the slot before re-raising,
         then the route deletes the newly created job
    -> Renders loading.html with job_id

background_task (orchestrator/__init__.py, daemon Thread):
  -> asyncio event loop -> _fetch_and_process(...)
    -> Fetch Last.fm scrobbles (paginated, async)
    -> Group into albums, filter by thresholds
    -> process_albums (5-phase cache flow; phases 1/4 in orchestrator/_cache.py,
       phase 3's search+detail steps in orchestrator/_search.py and
       orchestrator/_details.py, phase 5 in orchestrator/_results.py):
      1: DB connect + batch lookup (30-day TTL)
      2: Partition cache_hits / cache_misses
      3: Spotify fetch for misses only, then Deezer for Spotify's misses
      4: DB batch persist + conn.close() in finally
      5: Build results (cached original-release dates applied here)
         -> set_job_results() -> enqueue_release_check(job_id)

release_checks.py (one process-wide daemon thread, own loop, FIFO job queue):
  -> MusicBrainz at 1 req/s, capped per job, both hits and misses cached
  -> marks each result in place and publishes progress.stats.release_check

loading.js polls GET /progress?job_id=...
  -> 100% + no error -> GET /results?job_id=... -> renders results.html
  -> error + retryable -> show Retry button

results-release-checks.js polls GET /api/release_checks?job_id=...
  -> marks corrected rows in place; never reorders the open list
  -> stops on any status that is not pending or running
```

---

## 6. Test structure (1820 tests)

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
- Pre-commit: ruff check + ruff format, trailing whitespace, end-of-file, check yaml, check-merge-conflict, detect-private-key, doc-state-sync-check, tailwind-css-drift.
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
- Windows asyncio: every background thread (the album and heatmap jobs and the
  release-check worker) builds its loop through `worker.new_thread_event_loop`,
  which uses `asyncio.ProactorEventLoop()` on Windows so asyncpg does not
  mis-negotiate Postgres under Werkzeug's reloader. Its docstring owns the
  reason. Windows-only; Fly.io (Linux) is unaffected.
