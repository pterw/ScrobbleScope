<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0003

### 2026-07-24 - PR #162 review response, round 3 (side-task)

- Scope: Copilot round 3 (two comments + one suppressed duplicate).
  One acted on, one declined.
- Plan vs implementation:
  - Acted: both F-B19-6 archive headings moved their portion qualifier
    after the colon to match the `F-<context>-<N>: <title>` format the
    batch itself established (AGENTS.md Finding-Writing Rules).
  - Declined: updating the `BATCH20_DEFINITION.md:107-108` citation
    inside the archived `docs/history/logs/BATCH20_LOG.md` WP-3 entry.
    Rotated log entries are point-in-time records (same principle as
    the round-1 "unpushed" decline, which the reviewer accepted), they
    are machine-rotated content the docsync tooling owns, and the
    filename remains uniquely greppable at its archived location.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds are now in pure-style territory;
  recommend merging PR #162.

### 2026-07-24 - PR #162 review response, round 4 (side-task)

- Scope: Copilot round 4 -- one comment on PLAYBOOK Section 3 batch-state
  wording. Acted on, with a corrected mechanism note.
- Plan vs implementation:
  - Section 3 now uses the parser-recognized marker "Batch 21 is not yet
    defined"; the Section 3 parse verifiably returns the between-batches
    state with that wording in place.
  - Verified the comment's mechanism was doubly off: `BATCH_NEXT_RE`
    does not match "Batch 21 is next" (the attribution came from the
    `last_completed + 1` fallback at `parser.py:198-199`), and the
    wording fix alone cannot change the rendered STATUS -- with the
    close-out entry still inside the CURRENT-BATCH markers,
    `renderer.py:85-86` applies its own `last_completed + 1` fallback.
    Batch 19 precedent shows this is transient: its identically-tagged
    close-out entry rotated out automatically when Batch 20 WP-0 landed,
    and the same will happen at Batch 21 WP-0.
  - Logged the renderer gap as F-DOCSYNC-2 (open P2) rather than
    hand-moving machine-managed marker content or patching docsync code
    inside a docs-only PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner is merging PR #162; Batch 21 opens next.

### 2026-07-24 - Post-merge audit gap fixes (Batch 20 audit follow-up)

- Scope: close gaps found by the owner-requested audit of PR #159 (WP-1
  through WP-5 were executed via Copilot + PR reviews; audit compared the
  merged result against `BATCH20_DEFINITION.md` acceptance criteria).
  Work continues in a `wip/batch-20` worktree off `main` for isolation.
- Plan vs implementation:
  - `README.md`: deleted the "Doc-State Sync Tooling" bullet from Key
    Implementation Highlights (WP-1 acceptance item; the WP-1 log entry
    claimed removal but no commit ever removed it). Fixed the Project
    Structure tree so the agent-docs cluster is a comment row instead of
    a fake directory nesting five root-level files, and moved `AGENTS.md`
    and `PLAYBOOK.md` into that cluster. Added the missing prose note that
    `BATCHN_DEFINITION.md` sits at the root only while a batch is active.
  - `DEVELOPMENT.md`: corrected the `scrobblescope-bootstrap` description
    to the skill's actual read order (AGENTS.md -> PLAYBOOK 3-4 -> active
    batch definition -> SESSION_CONTEXT 1-2 -> AGENT_NOTES, then git/test
    verification) replacing the inaccurate SESSION_CONTEXT-first
    early-stop description.
  - `BATCH20_DEFINITION.md` header: refreshed stale status ("awaiting
    owner audit"), branch, and 389 baseline (390 since the WP-5 deviation).
  - `PLAYBOOK.md` Section 3 + `.claude/SESSION_CONTEXT.md` Section 1:
    branch updated from merged `file-hygeine` to `wip/batch-20`.
- Deviations: Getting Started length (WP-3 target ~95-100 lines, actual
  155 after review iterations added a full `docker run` block and 3-OS
  schema-init instructions) left as-is pending owner decision:
  re-compress vs accept the expanded setup detail.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-6 (FINDINGS.md cleanup and archive) is next.

### 2026-07-24 - README CSRF and UX cleanup (side-task)

- Scope: PR-review-comment-driven fixes to `README.md` and `AGENTS.md`.
- Plan vs implementation:
  - `README.md`: updated CSRF description to document three distinct injection
    mechanisms -- form-submit body token (`/results_loading`, `/results_complete`,
    `/unmatched_view`), header-only fetch (`/reset_progress`), and both body and
    header (`/heatmap_loading`). Added `/unmatched_view` to the form-submit route
    list after reviewer confirmed the hidden `csrf_token` input at
    `templates/results.html:177-178`.
  - `README.md`: removed three duplicate UX entries from the Styling & UX details
    block (rotating messages, personalized stats, onboarding) that were already
    covered in the Features section above.
  - `AGENTS.md`: removed a non-ASCII section symbol (replaced with plain text
    "Section") to comply with the ASCII-only markdown authoring rule.
- Deviations: none -- all changes are documentation-only PR review responses
  outside Batch 20 WPs; Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --check` -- exit 0.
- Forward guidance: Batch 20 WP-6 (FINDINGS.md cleanup) is still the next
  work package.

### 2026-07-24 - DEVELOPMENT.md file-count follow-up

- Scope: side-task follow-up to close the missed Batch 20 WP-5 documentation
  requirement in `DEVELOPMENT.md` by acknowledging `FINDINGS.md` as the sixth
  advisory, read-on-demand file in the external-memory description.
- Plan vs implementation:
  - Reworded the file-count paragraph to distinguish the five core tracked
    files from advisory `FINDINGS.md`, while keeping the archive-directory
    count unchanged.
  - Kept the wording explicit so IDE-based agents (for example Claude Code
    and Codex in VS Code) do not misread `FINDINGS.md` as part of the
    mandatory bootstrap set.
- Deviations: none -- this closes a missed WP-5 acceptance item flagged in PR
  review and leaves Batch 20 WP-6 as the next unstarted work package.
- Validation: `.venv/bin/pytest -q` -- **390 passed**. `.venv/bin/pre-commit
  run --all-files` -- all hooks pass. `.venv/bin/python scripts/doc_state_sync.py
  --check` -- exit 0 with the two expected root-BATCH warnings.
- Forward guidance: WP-6 still cleans up and archives `FINDINGS.md`.

### 2026-07-24 - Restore out-of-scope README edits (side-task)

- Scope: revert the Features-section rewrite and the Acknowledgements removal
  made in PR #159 outside Batch 20 WP-1 through WP-3; keep Screenshots removal
  as intentional.
- Plan vs implementation:
  - `README.md`: restored the original flat-list Features section (removed the
    "As mentioned above" intro and the `<details>` wrapper added out-of-scope).
  - `README.md`: restored the Acknowledgements section before Author & Contact.
  - `README.md`: updated Table of Contents to re-include only the
    Acknowledgements link.
- Deviations: none -- pure restoration of pre-PR content flagged by code review
  at PR #159 discussion_r3644787390.
- Validation: `pre-commit run --all-files` -- pass. `pytest -q` -- not
  applicable (documentation-only change). `python scripts/doc_state_sync.py
  --check` -- pass.
- Forward guidance: Features and Acknowledgements now match the intended PR
  state, with Screenshots intentionally removed; any future changes to those
  sections require an explicit batch WP or deviation log entry.

### 2026-07-24 - Copilot comment-job bootstrap trim (side-task)

- Scope: reduce unnecessary bootstrap for Copilot PR comment/review-comment
  jobs after the `copilot` Actions run failed in request processing with a
  monthly-quota error before reaching the linked review thread.
- Plan vs implementation:
  - `AGENTS.md`: added a targeted review-comment fast-path for prompts that
    link to a single `discussion_r...` thread, limiting reads to the linked
    file/lines plus only the bootstrap context that thread actually needs.
  - `HANDOFF_PROMPT.md`: removed the unconditional "read all bootstrap
    files" mandate for comment jobs and aligned the startup procedure with
    the lighter fast-path in `AGENTS.md`.
- Deviations: none -- this is a side-task CI reliability fix outside Batch 20;
  Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --fix` -- no changes.
  `python scripts/doc_state_sync.py --check` -- pass, with the two expected
  active-root-BATCH warnings. `pytest -q` and `pre-commit run --all-files`
  could not run in this sandbox because the repo-local `.venv` and those
  executables are not present here.
- Forward guidance: if future comment jobs still hit quota, inspect whether
  the prompt is fetching full PR comment lists when a direct review-comment
  URL is already supplied.

### 2026-07-22 - Link-preview image + Open Graph meta tags (side-task)

- Scope: LinkedIn (and Slack/Discord/etc.) show no image when the app URL
  is shared, since no og:image or companion meta tags existed.
- Plan vs implementation:
  - New `static/images/social-card.png` (1200x630, standard OG/Twitter
    card size): dark gradient background, the real favicon.svg pinwheel
    mark, wordmark, and tagline. Generated by rendering an HTML page that
    embeds the actual favicon.svg markup (not a hand-approximated
    redraw) and screenshotting it at 2x via the Chrome DevTools Protocol
    browser tool, then downsampled with Pillow (already pinned in
    requirements.txt; no new dependency).
  - `templates/base.html`: added `og:type`, `og:site_name`, `og:title`,
    `og:description`, `og:image` (+width/height), `og:url`, and the
    `twitter:card`/`title`/`description`/`image` equivalents. Title and
    description are Jinja blocks (`og_title`, `og_description`) so child
    templates can override per-page; default to the existing site title
    and meta-description text. `og:image` uses
    `url_for(..., _external=True)` so it resolves to an absolute URL
    against whatever host serves the request (required -- OG scrapers
    reject relative image URLs).
- Deviations: none. Out of scope for the active Batch 20 (file-hygiene,
  no production-code changes per `BATCH20_DEFINITION.md`), so logged as
  a side-task per `AGENTS.md` Side-Task Handling rather than a Batch 20 WP.
- Validation: `pytest -q` -- **389 passed**, no change (docs/template/asset
  only, no Python logic touched). `pre-commit run --files templates/base.html
  static/images/social-card.png` -- doc-state-sync-check passed (only
  applicable hook). Verified rendered output via Flask test client: all
  12 meta tags present, `og:image` resolves to an absolute URL.
- Forward guidance: none pending. Owner should verify the card renders
  correctly on LinkedIn's actual link-preview (some platforms cache
  previews aggressively per-URL; may need LinkedIn's Post Inspector to
  force a re-scrape after first deploy).

### 2026-05-19 - Batch 19 close-out (Batch 19 close-out)

- Scope: archived the Batch 19 definition, refreshed README for the PR to
  main, and finalized PLAYBOOK + SESSION_CONTEXT to reflect Batch 19 complete.
- Plan vs implementation:
  - `git mv BATCH19_DEFINITION.md docs/history/definitions/BATCH19_DEFINITION.md`.
  - PLAYBOOK Section 2 table now links to the archived definition.
  - PLAYBOOK Section 3 marks Batch 19 complete; next action is the
    `feat/heatmap` PR to `main`.
  - SESSION_CONTEXT Batch 19 row flipped to **Complete**.
  - README bumped to 387 tests, "Top Albums" mode rename in the intro,
    framed heatmap result + KPIs + desktop calendar vs. mobile activity
    strip described, `.venv/` venv guidance aligned with AGENTS.md, and
    heatmap roadmap line updated to cover both Batch 18 and Batch 19.
- Deviations: owner kept screenshots as "coming soon" placeholders since
  the saved ones in `docs/images/` no longer reflect the current UI.
  Owner will refresh them out of band.
- Validation: `pytest -q` passed with **387 passed** and 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` passed all 10
  hooks. `python scripts/doc_state_sync.py --check` exited 0 with the
  expected root warning gone after archiving the definition.
- Forward guidance: open the PR for `feat/heatmap` -> `main`, address any
  reviewer comments, merge, and deploy. Batch 20 (heavy UI refactor) is
  to be scoped later and is explicitly out of this PR.

### 2026-05-19 - PR #152 Gemini Code Review fixes (side-task)

- Scope: addressed three substantive Gemini Code Review comments on the
  open `feat/heatmap` PR.  Deferred three "broad except Exception"
  comments to the future error-handling batch (already tracked as
  FINDINGS.md P1 item 9).
- Plan vs implementation:
  - **Commit `ccb000f`** -- `fix(heatmap): use UTC for scrobble
    timestamps and fetch window`. Brought `heatmap.py` in line with
    `lastfm.py:31`'s established UTC convention. Updated every UTS-
    building call site in `tests/test_heatmap.py` to `tzinfo=timezone.utc`
    so the boundary tests are not vacuous against tz bugs. Added a new
    adversarial test (`test_utc_decode_invariant_against_local_tz_drift`)
    that pins a UTS at 23:30 UTC and asserts the bucket lands on the UTC
    day, not the local-tz day.
  - **Commit `01a7904`** -- `fix(repositories): isolate nested
    daily_counts in get_job_context`. Explicit
    `dict(results["daily_counts"])` after the outer shallow copy.
    Chosen over `copy.deepcopy` for the polling hot path. Closes
    F-B18-8. New regression test in `test_repositories.py`.
  - **Commit `53919c2`** -- `fix(heatmap): keep streak alive when today
    has no scrobble yet`. Stepping back one day when today is zero
    matches GitHub-contributions/Duolingo convention and was the
    pattern Gemini suggested.
  - FINDINGS.md gained F-B19-6 (naive-tz vacuous-test anti-pattern,
    forward-TODO for AGENTS.md update) and a resolved entry for F-B18-8.
- Deviations: declined Gemini's three "narrow the bare
  `except Exception`" comments. Those are all instances of FINDINGS.md
  P1 item 9 (14 sites total); narrowing 3 of 14 piecemeal without a
  test matrix per error class is a regression risk that violates
  AGENTS.md scope discipline. Belongs in the dedicated error-handling
  batch the FINDINGS entry already calls for.
- Validation: `pytest -q` passes with **389 passed** and 3 existing
  aiohttp/Python 3.13 warnings (387 -> 389; +1 UTC adversarial test,
  +1 nested-copy regression test). `pre-commit run --all-files` passes
  all 10 hooks. `node --check static/js/heatmap.js` clean.
- Forward guidance: push the three fix commits + this log entry,
  reply to Gemini via `gh pr review` declining the broad-Exception
  comments with a FINDINGS-item-9 pointer, and wait for re-review.

### 2026-05-16 - Remove dependabot.yml (side-task)

- Removed `.github/dependabot.yml`: all packages are pinned with `==` so
  dependabot can only open PRs that break the pinning policy. Pure noise for
  this project. No functional change.
- **385 tests passing**, all hooks green.

### 2026-05-16 - README update: heatmap feature + stale data

- Added heatmap feature description to intro paragraph (was album-only).
- Added Scrobble Heatmap bullet to Features section (grid, palette, tooltips,
  dark mode, responsive, pinwheel spinner).
- Updated project structure: heatmap.py, heatmap.css, heatmap.js,
  scrobblescope_pinwheel.svg, test_heatmap.py all added; stale test counts
  corrected (test_repositories.py 18->19, test_routes.py 50->65).
- Updated tech stack table: test count 350/23 -> 385/24; APIs note that
  heatmap uses Last.fm only (no Spotify).
- Roadmap: checked off heatmap (Batch 18 Phase 1 complete, Phase 2 in progress);
  corrected "350 tests / 23 files" to "385 / 24".
- Test badge: 350 -> 385.

### 2026-03-05 - Post-Batch-17 doc staleness fix

- PLAYBOOK Section 3 still said "Batch 17 is active" and listed all WP
  statuses after the close-out commit (743f8ae). Updated to "Between batches"
  with heatmap feature noted as next action on branch `feat/heatmap`.
- SESSION_CONTEXT Section 1 branch updated from `wip/batch-17` to
  `feat/heatmap`; date bumped to 2026-03-05.
- STATUS block refreshed by `doc_state_sync --fix`.
- Batch 17 log entries remain inside CURRENT-BATCH markers per docsync
  design -- they will auto-rotate to `BATCH17_LOG.md` when the next batch
  is declared active in Section 3.
- **350 tests passing**, all hooks green.

### 2026-03-05 - side-task: PR review fixes (CI cache, DEVELOPMENT.md, README, doc tidiness, SDLC table)

- **`.github/workflows/test.yml`**: fixed `cache-dependency-path` from
  `requirements-dev.txt` to `requirements*.txt`. The dev file starts with
  `-r requirements.txt` but pip's cache key computation does not follow
  transitive includes; changes to `requirements.txt` alone would not
  invalidate the cache. Fix ensures both files are hashed for the key.
- **`DEVELOPMENT.md`**: corrected the SESSION_CONTEXT.md CI presence
  claim. Previous text said the file is "absent in GitHub Actions" --
  inaccurate since SESSION_CONTEXT.md is now committed and a standard
  `actions/checkout@v4` includes it. Updated to say "normally present;
  `_read_lines_optional()` is a fallback for edge cases (sparse checkout
  or custom workflow)."
- **`README.md`**: three stale items corrected from Batch 17 changes:
  (1) CI/CD table row updated -- standalone flake8 removed in WP-2; pip-audit
  added in WP-2; description now reads "Quality Gate (pre-commit, pytest +
  coverage gate, pip-audit)"; (2) Code Quality row: added
  check-merge-conflict and detect-private-key (added in WP-2 addendum);
  (3) Local Dev section: SESSION_CONTEXT.md Section 8 ref (broken after
  WP-4 renumbering + Docker setup moved to AGENT_NOTES.md) -> AGENT_NOTES.md.
- **`BATCH17_DEFINITION.md`**: removed duplicate `---` separator between
  "## 6. Deferred" and "## Supplementary Info" (double rule was redundant).
- **`PLAYBOOK.md` WP-4 note**: updated "Candidate for a future cleanup
  pass" -> "Subsequently fixed in a side-task (see logarchive)" so PR
  reviewers do not see the WP-4 note as an open item that is also fixed
  in the same PR diff.
- **`DEVELOPMENT.md` SDLC table**: CI gate row updated from stale
  "GitHub Actions: pre-commit + flake8 + pytest + coverage" to "Quality
  Gate (pre-commit, pytest + coverage gate, pip-audit)" to match the
  README change and the WP-2 workflow rename.
- **350 tests passing**, all hooks green.

### 2026-03-05 - side-task: doc accuracy fixes (AGENTS.md, HANDOFF_PROMPT.md)

- **AGENTS.md**: "these doc files" -> "the doc files listed below" (dangling pronoun
  with no referent; table follows the section break, not the sentence).
- **HANDOFF_PROMPT.md**: SESSION_CONTEXT step 4 now reads "Sections 3-5" instead of
  "Sections 3-4". Section 5 is the dedicated Architecture overview; "Sections 3-4"
  would have left agents one section short when looking for architecture detail.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: requirements pinning + venv/agent safety rules

- **Pin previously unpinned packages**: `asyncpg>=0.29.0` -> `==0.31.0` and
  `Flask-WTF>=1.2.0` -> `==1.2.2` in `requirements.txt`. All five packages in
  `requirements-dev.txt` pinned to exact installed versions (flake8==7.3.0,
  pre-commit==4.5.1, pytest==9.0.2, pytest-asyncio==1.3.0, pytest-cov==7.0.0).
  Eliminates version drift on venv reinstall.
- **Incident root cause (2026-03-04):** Prior agent session ran
  `source venv/Scripts/activate && pip install flask-talisman` targeting the
  wrong `venv/` directory instead of `.venv/`. The `.venv/` was subsequently
  found empty (likely drained by the same session); reinstall from requirements
  files brought packages back at new versions for previously unpinned entries.
  Multiple background `python app.py` processes were also started via Bash tool
  and not cleaned up, blocking the owner terminal. User touched zero code.
- **AGENTS.md updated**: Environment Setup section corrected (`venv/` -> `.venv/`,
  bare `pip` -> `.venv/Scripts/pip`, added pinning requirement). Anti-Pattern
  Registry entries 4 and 5 added (wrong venv / bare pip, background server
  processes).
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: gunicorn threading + dark mode browser preference

- **Gunicorn threading**: added `--threads 4` to Dockerfile CMD. Single sync worker
  was serializing all HTTP requests in production; threads allow concurrent request
  handling while keeping JOBS dict in shared process memory.
- **Dark mode fix**: `theme.js` now falls back to `window.matchMedia('(prefers-color-scheme: dark)')`
  when no localStorage preference is saved. First-visit users with browser dark mode
  enabled will see dark theme automatically. Explicit toggle still overrides.
- Load test findings (local, 1-5 concurrent users) documented in agent memory.
  Spotify cache TTL verified correct (ToS compliant). No upstream 429s at 2-5 users.

### 2026-03-04 - side-task: log rotation fix

- **Log rotation**: changed `RotatingFileHandler` to 2MB files / 10 backups (was 1MB / 5).
  Small files stay granular and parseable; 10 backups cover a full load test session.
  No production impact -- file is ephemeral on Fly.io; stdout is the prod log channel.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: PR code review fixes

- **theme.js**: `var` -> `const` for `saved` and `prefersDark` (neither reassigned;
  aligns with `const`/`let` convention in all other JS files).
- **Dockerfile**: added comment explaining `--workers 1 --threads 4` rationale for
  Fly.io deployment (shared-cpu-2x / 512MB, JOBS dict requires single process).
- **350 tests passing**, all hooks green.

### 2026-03-03 - Review-driven fixes: barrier safety, session cleanup, Docker error handling, dev_start tests

**Scope:** Side-task -- address Co-Pilot code review findings from PR #56, add
subprocess timeout guards, and add the deferred `dev_start.py` unit tests (now
warranted by increased error-handling complexity).

**Fixes applied:**
1. `concurrent_users_test.py` -- moved `barrier.wait()` inside `try` block so
   `BrokenBarrierError` is captured and a `ConcurrentResult` is always appended
   (docstring guarantee upheld).
2. `concurrent_users_test.py` -- track sessions in a list, call `session.close()`
   after `join()` to prevent connection/socket leaks.
3. `dev_start.py` -- `check_container_status()` now distinguishes "No such object"
   (returns `None`) from Docker daemon errors (raises `RuntimeError` with actionable
   message) and unexpected errors (raises with stderr details).
4. `dev_start.py` -- added `timeout=10` to `docker inspect` and `timeout=30` to
   `docker start` subprocess calls; catches `subprocess.TimeoutExpired` and raises
   `RuntimeError` with clear messaging.

**New tests:** 11 unit tests in `tests/scripts/dev/test_dev_start.py` covering
`check_container_status` (6 paths: running, absent, docker-not-found, timeout,
daemon-not-running, unexpected error), `start_container` (success, failure, timeout),
`main` (absent container exit, exited container start+exec).

**Validation:** `pytest -q` -- **350 passed**. `pre-commit run --all-files` -- all
hooks pass.

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
