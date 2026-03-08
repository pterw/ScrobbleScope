# Agent Notes

Project-specific context for all agents working on ScrobbleScope.
Rules live in `AGENTS.md`. Work orders live in `PLAYBOOK.md`.
This file contains preferences, local dev setup, and discovered constraints
that agents need but that do not belong in either of those files.

---

## Owner Preferences

- Commits staged incrementally -- specific files by name, never `git add -A`.
- Each WP commit is reviewed individually before push. Wait for explicit push instruction.
- No co-author trailers in commit messages.
- Concise responses; no emojis unless asked.
- Pause after each WP commit for owner review.
- Pause and notify owner if Docker config or external MCP setup is needed.
- Always explain why in log entries and inline comments -- not just what.
- Owner tests locally in Firefox (+ Responsive Design Mode for mobile)
  between WPs before approving the next one.
- Software principles enforced: DRY, SoC, SRP, KISS, Dependency Inversion,
  Composition over Inheritance, Clean Architecture, Boy Scout Rule, Least
  Knowledge Principle, Fail Fast. Not aspirational -- mandatory.
- Testing pyramid: unit tests (mocked, base), integration tests (routes,
  middle), E2E (owner-driven, top). Every test must fail if the function
  under test is deleted.

---

## Local Dev Setup

**One-command startup (app + Postgres cache):**
```
python scripts/dev/dev_start.py
```
This checks and starts the `ss-postgres` Docker container, then launches Flask.

**Manual fallback:**
```
docker start ss-postgres
python app.py
```

**Verify app is up (from a script, not by starting a new process):**
```
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').status)"
```

**Local Postgres cache:**
- Container: `ss-postgres`, volume: `ss-postgres-data`
- Connection: `postgresql://postgres:postgres@localhost:5432/scrobblescope`
- `DATABASE_URL` is in `.env` (gitignored); Flask reads it automatically.
- `init_db.py` has no `load_dotenv()` -- set `DATABASE_URL` in shell manually before running it.
- Schema: `spotify_cache` (PK: artist_norm + album_norm; TTL 30 days)

**Browser MCP (Docker-based):**
- Deployed site: `https://scrobblescope.fly.dev` -- reachable directly.
- Local app: use `http://host.docker.internal:5000/` (not `localhost`).

---

## Architectural Constraints

- `MAX_ACTIVE_JOBS` (default 10) caps concurrent background jobs via `worker.py`.
- `_GlobalThrottle` in `utils.py` caps aggregate API throughput across all threads.
- `_cache_lock` in `utils.py` guards `REQUEST_CACHE` thread safety.
- `_PLAYTIME_ALBUM_CAP = 500` in `orchestrator.py` limits Spotify fetch for playtime sort.
- **Single worker, multiple threads:** Gunicorn runs `--workers 1 --threads 4`.
  Multiple workers would break the in-process `JOBS` dict. This is intentional.
- **Windows asyncio:** `background_task()` in `orchestrator.py` explicitly uses
  `asyncio.ProactorEventLoop()` on `sys.platform == "win32"`. Required because
  Werkzeug's debug reloader leaves `SelectorEventLoop` in background threads on
  Windows, causing asyncpg startup failures. The guard is Windows-only.
- **In-memory `REQUEST_CACHE`** avoids re-fetching Last.fm for same-user/year
  re-searches with different filters. Clears on Fly.io machine sleep. By design.
- **Spotify cache TTL:** cache hits do not refresh `updated_at`; albums expire
  30 days from last Spotify fetch regardless of access frequency (ToS compliant).
- **CSRF:** `CSRFProtect` is active on all POST routes including `/results_loading`.
  Disabled only in `tests/conftest.py`. Token is a hidden form field:
  `<input name="csrf_token" value="...">`.

---

## Venv and Pip Rules

- The ONLY virtualenv is `.venv/` in the repo root.
- Local dev (Windows): always use `.venv/Scripts/pip`, never bare `pip`.
- Local dev (Linux): always use `.venv/bin/pip`.
- CI (GitHub Actions): bare `pip` is correct -- the runner manages its own environment.
- All packages pinned with `==` in both `requirements.txt` and `requirements-dev.txt`.
- Never install packages not in requirements files without explicit owner approval.
- Never start a Flask server process via the Bash tool -- the owner runs the app.

---

## Heatmap Feature (Batch 18 -- iteration 1)

- **Design doc:** see `BATCH18_DEFINITION.md` (repo root while active, then
  `docs/history/definitions/` after close-out).
- **Key decisions:** username-only input (last 365 days), pill tabs on index.html,
  all states on one page (no navigation), GitHub-style 7x52 SVG grid, rocket_r
  palette, log-adjusted intensity, no heatmap-specific caching (REQUEST_CACHE
  covers Last.fm pages), no new Python dependencies, no matplotlib/seaborn.
- **Cache note:** heatmap uses different `from`/`to` timestamps than album
  search, producing different REQUEST_CACHE keys. No interference.
- **Windows asyncio:** heatmap_task must use same ProactorEventLoop guard as
  orchestrator.py background_task. See AGENT_NOTES Architectural Constraints.
- **Feature may span multiple batches.** Iteration 1 = working end-to-end.
  Follow-up: orchestrator split, export, date range, summary stats.

---

## Known Open Issues / Future Candidates

- Flask-Talisman (CSP) was attempted in Batch 17 WP-5 and dropped (YAGNI).
  The templates use inline styles (SVG logo `<defs><style>`, Bootstrap progress
  bar `style="width: 0%"`, album cover fallback) that would need refactoring
  before a strict CSP is viable. See PLAYBOOK WP-5 entry for details.
- Scaling path if needed: Celery/Redis RQ -- out of scope until features complete.
- Orchestrator monolith split: deferred until heatmap exists alongside album
  pipeline. Natural SoC cleanup candidate for a follow-up batch.
- Cache + bounded semaphore load testing: per `load-test-findings.md`.
