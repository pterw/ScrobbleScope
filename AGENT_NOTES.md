# Agent Notes

Project-specific context for all agents working on ScrobbleScope.
Rules live in `AGENTS.md`. Work orders live in `PLAYBOOK.md`.
This file contains preferences, local dev setup, and discovered constraints
that agents need but that do not belong in either of those files.

**Batch state:** owned by `PLAYBOOK.md` Section 3 -- this file does not
track it.

---

## Owner Preferences

- Commit mechanics: owned by `AGENTS.md` Commit Rules -- read them there.
- Concise responses; no emojis unless asked.
- Pause and notify owner if Docker config or external MCP setup is needed.
- Always explain why in log entries and inline comments -- not just what.
- Owner tests locally in Firefox (+ Responsive Design Mode for mobile)
  between WPs before approving the next one.
- Software principles enforced -- not aspirational, mandatory: DRY (don't
  repeat yourself), SoC (separation of concerns), SRP (single
  responsibility per module/function), KISS (keep it simple), Dependency
  Inversion (depend on abstractions, not concretions), Composition over
  Inheritance, Clean Architecture (dependencies point inward, see
  SESSION_CONTEXT Section 4), Boy Scout Rule (leave touched code cleaner
  than found), Least Knowledge / Law of Demeter (talk only to immediate
  collaborators), Fail Fast (validate early, raise loudly).
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

- Runtime concurrency constants (`MAX_ACTIVE_JOBS`, `_GlobalThrottle`,
  `_cache_lock`, `_PLAYTIME_ALBUM_CAP`): see SESSION_CONTEXT Section 1
  "Key runtime facts" (single source; do not restate values here).
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

Owned by `AGENTS.md` (Environment Setup + Anti-Pattern Registry entries 4
and 5) -- read them there.

---

## GitHub CLI Authentication

`gh` reads `GH_TOKEN` from the environment automatically. The owner stores a
fine-grained PAT in `.env` (gitignored) so agents can open PRs and read review
comments without the owner pasting the token into chat each session.

To use it in a session without exporting it permanently, source it from `.env`
inside PowerShell:

```powershell
$line = Get-Content .env | Where-Object { $_ -match '^GH_TOKEN=' } | Select-Object -First 1
$env:GH_TOKEN = $line.Substring($line.IndexOf('=') + 1).Trim().Trim('"')
gh auth status
```

Then `gh pr ...` commands work for the rest of the session. The token is held
only in the current process environment and is gone when the shell exits.

**Rules:**
- Never paste the token value into chat, commit it, or screenshot it.
- Rotate every 90 days. Revoke immediately if exposed.
- Required permissions for this repo's workflow: Contents r/w, Pull requests
  r/w, Metadata r (auto). Add Workflows r/w only if reviewer feedback may
  ask for CI changes; add Issues r/w only if reviewers comment via issues.
- Fine-grained PAT scoped to `pterw/ScrobbleScope` only is preferred over a
  classic PAT (smaller blast radius if leaked).
- If `gh auth status` returns 401, the token is invalid or expired -- generate
  a fresh one, update `.env`, and re-source. Do not retry the same token.

---

## Heatmap Feature Notes (shipped -- Batches 18/19)

- **Definitions (archived):** `docs/history/definitions/BATCH18_DEFINITION.md`
  (core feature) and `docs/history/definitions/BATCH19_DEFINITION.md`
  (polish; closed out 2026-05-19, PR #152 merged).
- **Key decisions:** username-only input (last 365 days), pill tabs on index.html,
  all states on one page (no navigation), GitHub-style 7x52 SVG grid, rocket_r
  palette, log-adjusted intensity, no heatmap-specific caching (REQUEST_CACHE
  covers Last.fm pages), no new Python dependencies, no matplotlib/seaborn.
- **Cache note:** heatmap uses different `from`/`to` timestamps than album
  search, producing different REQUEST_CACHE keys. No interference.
- **Windows asyncio:** heatmap_task must use the same ProactorEventLoop guard
  as orchestrator.py background_task. See Architectural Constraints above.
- **Perf:** fetch speed is rate-limit bound; the measurement and rationale
  live in FINDINGS.md F-B18-11 (single source).
- **Follow-up candidates:** export, date range, summary stats (future
  batches; the orchestrator split is tracked as FINDINGS F-B20-2).

---

## Known Open Issues / Future Candidates

- Flask-Talisman (CSP) was attempted in Batch 17 WP-5 and dropped (YAGNI).
  Templates use inline styles that would need refactoring before a strict
  CSP is viable. Details: `docs/history/logs/BATCH17_LOG.md` and
  `docs/history/definitions/BATCH17_DEFINITION.md`.
- Scaling path if needed: Celery/Redis RQ -- out of scope until features
  complete (FINDINGS F-MAS-6).
- Orchestrator monolith split: precondition met (heatmap shipped as the
  second pipeline); tracked as FINDINGS F-B20-2 (open P1).
- Load testing (2026-03-04): 2/3/5 concurrent users ran clean; the 10-user
  run never completed. Each API has its own global throttle and neither
  does per-job accounting, so N jobs sharing the Last.fm phase average
  ~10/N req/s rather than each being guaranteed it -- see the
  `MAX_ACTIVE_JOBS` comment in `scrobblescope/config.py` for the full
  rationale. Conclusions also in FINDINGS F-LOAD-1..5; the raw run data
  is agent-side memory, not in the repo.
