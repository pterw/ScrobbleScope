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

- **"Wordmark" and "logo" mean the SVG logotype, not the UI type stack.** The
  owner uses the two words interchangeably for the ScrobbleScope mark, and
  counts only the letterforms as the logo -- the five bars beside them are a
  visualiser, not part of it. So "the wordmark font" means Oblong Regular,
  the face inside the SVG, and never Instrument Serif or any Adobe kit family
  used for page type. Getting this wrong sends you to the wrong file.
- **The Adobe kit is what keeps this UI from looking generated.** The owner is
  explicit that Gotham, Oblong Regular, Akzidenz-Grotesk Next and Input Mono
  are the reason the interface does not read as default AI output, and that
  Claude Design's own output trends that way and still shows traces of it.
  See https://impeccable.style/slop for the look being avoided: cream-and-
  terracotta serif pairings, Inter or Space Grotesk as the safe face, emoji
  section markers, everything centred, uniform rounded cards. When proposing
  UI, do not reach for those defaults, and do not substitute a "safer" common
  face for a kit family. The owner accepts the Instrument Serif hero layout as
  AI-flavoured but fine; that is a judgement already made, not an opening.
- **The wordmark typeface is Oblong Regular, by WAPType.** Free, and licensed
  so this project can host it. The owner recovered this on 2026-08-25 after
  about three hours: the original was set in Illustrator and converted to
  paths, so the wordmark and the pinwheel `S` on the loading page are outline
  geometry with no font reference left in them. Nothing in the repository
  recorded which face they came from, and nothing could have.
  Write it down rather than re-deriving it. It is what makes the letterforms
  editable again, and it is the precondition for splitting the mark into a
  live text element plus the bar visualiser, instead of one frozen outline.
  The owner has judged that split **not worth doing yet** -- it is recorded
  as an option, not as planned work. Do not start it without a ruling.
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

## This repository is also a template being extracted

**Owner intent, stated 2026-08-25.** The long-term goal is to lift the
workflow out of ScrobbleScope and reuse it when building any app, at least
any data-visualisation or full-stack one: the guards, `scripts/docsync/`,
`scripts/dev/frontend_gate.py`, `AGENTS.md`, the PLAYBOOK and FINDINGS
discipline, and the batch and work-package structure. That is why the tooling
is larger than the application it checks, and why hardening has been
progressive rather than a one-off.

**What this changes about how you write tooling here.** Treat every check as
something that will run in a repository that is not this one:

- **Keep repository facts out of the mechanism.** A check reads its facts from
  a declarations file; it does not hard-code them. `scripts/docsync/
  declarations.py` and `.docsync.toml` are the worked example -- the module
  carries no ScrobbleScope value at all.
- **Name assumptions and make them switchable.** An assumption that is true
  here becomes doctrine the moment the tool is lifted. DOC011 treats
  `~~struck-through text~~` as retired, which is true in this corpus and is a
  convention rather than a rule of Markdown; it is a declared option for that
  reason, and the owner caught it by reading the check against this intent.
- **Prefer the standard library.** `tomllib`, `re`, `pathlib`. A dependency is
  a thing the next repository has to agree to.
- **Fail with a path, a line and a remediation**, because the reader will not
  be the person who wrote the check.

**What is already extractable, and what is not.** `scripts/docsync/` is close:
its integrity checks are generic apart from the document names in
`_LIVE_DOCUMENT_PATHS`. `scripts/dev/frontend_gate.py` is generic in structure
-- serve, drive a browser, run checks per device profile -- and specific in
its checks, which is the right split. The batch and work-package vocabulary in
`AGENTS.md` is portable. What is not portable: `.docsync.toml`, the design
system under `docs/design/`, and every path constant naming a ScrobbleScope
file.

**Do not start the extraction as a side task.** It is a batch of its own, and
the owner has not scheduled it. Until then, the constraint is only that new
tooling is written so the extraction stays cheap.

---

## Venv and Pip Rules

Owned by `AGENTS.md`: Environment Setup, plus the Anti-Pattern Registry
entries "Wrong venv or bare pip" and "Background server processes".

The commands in this file are written in their primary-checkout form. From a
linked worktree, convert each one per the rule in `AGENTS.md` Session
Bootstrap.

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

## Batch 21 Tooling Map (WP-1 through WP-8)

Written 2026-08-14, before WP-1 started. Everything below was verified
against the live machine and repository on that date rather than carried
forward from an earlier note; re-verify before relying on it, because the
skill and MCP inventory is per-machine and moves independently of this repo.

**How this keys against the definition.** `BATCH21_DEFINITION.md` has no
per-WP acceptance criteria. It carries one batch-level list of 9 criteria;
the three repository gates and owner visual review run at every WP, while
the repository-owned frontend gate joins them from WP-2 onward. So the map
keys on the WP and names the batch-level criteria each one serves. Do not go
looking for per-WP criteria; there are none by design.

### Skills: four separate sources, and the names collide

1. **superpowers plugin v4.3.1** -- 14 skills, including
   `systematic-debugging`, `test-driven-development`,
   `verification-before-completion`, `writing-plans`, `executing-plans`,
   `subagent-driven-development`, `using-git-worktrees`.
2. **`.agents/skills/`** -- 20 vendored from `obra/superpowers` and
   `mattpocock/skills`, gitignored (see the reason in `.gitignore`).
   Overlapping but *differently named* equivalents: `tdd`,
   `diagnosing-bugs`, `code-review`, `domain-modeling`, `handoff`,
   `improve-codebase-architecture`, `resolving-merge-conflicts`.
3. **User-level `~/.claude/skills/`** -- `pr-bot-triage`, `review-claudemd`,
   `scrobblescope-bootstrap`. `scrobblescope-bootstrap` is the session-start
   one for this repo; `pr-bot-triage` is the PR review-comment triage skill.
4. **Other installed plugins** -- `frontend-design`, `code-review`,
   `code-simplifier`, `github`, `playwright`, `figma`, `mattpocock-skills`,
   `claude-md-management`, `atomic-agents`, `episodic-memory`,
   `superpowers-chrome`, `adobe-for-creativity`.

The collision matters: `tdd` (source 2) and `test-driven-development`
(source 1) are different files from different upstreams. Name the one you
mean.

Skill definitions are deliberately not tracked in this repository -- they
are per-machine harness state, and `.gitignore` records the reason for each
ignored path. Do not add them, and do not create a `docs/skills/` tree.

### MCP servers

Usable now: GitKraken (git, PR and issue operations), two independent
Playwright providers (the Docker gateway and the `playwright` plugin),
`superpowers-chrome` (CDP), Mermaid Chart
(`validate_and_render_mermaid_diagram` -- the tool
`.github/instructions/mermaid.instructions.md` Rules 1-2 map onto outside
VS Code), Figma, Notion, Adobe, Canva, Google Workspace, monday.com,
episodic-memory.

Needing interactive OAuth and therefore unusable in a headless or cron run:
Atlassian Rovo, Microsoft 365, Vercel, ZipRecruiter.

### Per-WP map

| WP | Tooling that serves it | Batch criteria |
|---|---|---|
| WP-1 toolchain + themes | Bespoke Python only. No installed skill covers pinned-binary fetch with per-platform SHA-256 verification, and `frontend-design` authors UI rather than build plumbing. Treat WP-1 as unassisted work | 2, 3, 9 |
| WP-2 base shell + `error.html` pilot | `frontend-design`; repository-owned `playwright==1.62.0` + Chromium power `scripts/dev/frontend_gate.py`, independent of MCP. The one-stylesheet-per-page rule becomes an enforced check rather than a stated deliverable. The drift hook also lands here after WP-1 records its CI-fetch decision | 1, 3, 4 |
| WP-3 index page | `frontend-design`; Playwright for decade pills, the thresholds disclosure, and the CSS-only hints that replace `bootstrap.Popover` | 1, 4, 8 |
| WP-4 unified loading | Playwright for progress polling against a live job; the shared Jinja2 partial is exercised from both `loading.html` and the heatmap panel | 5 |
| WP-5 results leaderboard | Playwright, driven directly -- see gap 1. The JPEG export must be checked in both themes at mobile and desktop, and the `data-export` CSV precision fix needs a real DOM walk | 5, 7 |
| WP-6 heatmap seam removal | Playwright plus visual review; `--bars-color` aliasing is the thing to assert in both themes | 2, 3, 8 |
| WP-7 `reason_code` (only backend WP) | `test-driven-development` or `tdd`, and `systematic-debugging` or `diagnosing-bugs`. The test count moves again here, so update the inventory sites listed in `AGENTS.md` in the same commit | 6, 9 |
| WP-8 sweep + close-out | `verification-before-completion` before any done claim; `pr-bot-triage` for review rounds. Gap 4 lands here as a recorded decision, not as tooling; gaps 2 and 3 moved to WP-2 | 1, 9 |

### Verified gaps

1. **No `webapp-testing` skill exists on this machine** -- not in any of the
   four sources above. That does not block the permanent automated gate:
   WP-2 adds pinned Python Playwright + Chromium as a repository dependency.
   WP-5's exploratory JPEG-export E2E and WP-8's owner E2E remain direct
   Playwright MCP runs on top of that deterministic gate.
2. **The pre-commit top-level exclude covers 13 directories**, among them
   `docs/`, `static/` and `templates/`. The `tailwind-css-drift` hook on
   `static/css/tailwind.css` would therefore never run as an ordinary
   file-scoped hook. It must follow the `doc-state-sync-check` pattern
   (`always_run: true`, `pass_filenames: false`) -- the only hook that
   currently sees excluded paths -- or the exclude must be narrowed.
   The hook moved from WP-8 to WP-2 on 2026-08-19: WP-2 is the first WP
   whose templates consume the compiled CSS, so waiting for WP-8 left six
   work packages able to ship drifted output.
3. **CI has no Node and no Tailwind binary.** `.github/workflows/test.yml`
   is Python-only. The drift hook (now WP-2) requires the fetch to work
   headless on Linux, so either CI fetches and caches the pinned binary or
   the hook is local-only. Decide this at WP-1, because that is where the
   pinned versions and digests are chosen. WP-1 now carries an explicit
   criterion to write that decision down; before 2026-08-19 nothing did,
   which is how the hook came to be specified against an open question.
   WP-2's Python Playwright plan does not add a Node project: CI installs
   the pinned Python dependency and its matching Chromium build through
   `python -m playwright`, then runs the repository gate.
   **Disposition (2026-08-20):** WP-1 decided it -- CI fetches. The gate
   caches `scripts/bin/` by runner OS, architecture, and build-script hash,
   then rebuilds the CSS and fails on drift (`.github/workflows/test.yml`,
   steps "Cache pinned Tailwind assets" and "Verify committed Tailwind
   CSS"). There is still no Node; the standalone CLI needs none. The hook
   is not local-only, and `test.yml` is no longer Python-only.
4. **No CSS, JS or HTML hooks at all.** `trailing-whitespace` and
   `end-of-file-fixer` are scoped to `py|md|yaml|yml|txt`, and `static/`
   and `templates/` are excluded by the top-level rule regardless -- so the
   files eight work packages spend their time rewriting are unreachable by
   two independent mechanisms. Nothing formats or lints them.
   **Disposition (2026-08-19):** this gap is closed by decision, not by
   tooling. Batch 21 adds the generated-CSS drift hook (WP-2) and the
   frontend gate (WP-2 onward), keeps owner Firefox review, and does not
   add general CSS/JS/HTML linting unless a real regression demonstrates
   the need. WP-8 records that decision and its reason. Do not read this
   gap as an open commitment to add linters.
5. **`workflow_dispatch` is now usable.** The comment in `test.yml` notes
   it only becomes usable once on the default branch; the PR #170 merge put
   it there, confirmed present on `origin/main`.
6. **pip-audit is `continue-on-error: true`** -- advisory, and will not fail
   the Quality Gate.
7. **`skills-lock.json` names 22 skills; `.agents/skills/` holds 20.** The
   two absent are `systematic-debugging` and `test-driven-development` --
   both supplied by the superpowers plugin instead, so this is lockfile
   bookkeeping drift rather than a lost capability. Worth knowing before
   anyone "fixes" it by reinstalling.

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
