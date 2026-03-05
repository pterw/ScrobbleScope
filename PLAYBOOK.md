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
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 17 is active.** Branch: `wip/batch-17`. Definition: `BATCH17_DEFINITION.md`.
- **Next action:** All WPs complete or resolved. Batch 17 ready for close-out.
- WP status:
  - WP-1: HANDOFF_PROMPT.md fixes -- **done**
  - WP-2: CI/CD improvements (rename, remove dup flake8, caching, artifact, pip-audit, dependabot) -- **done**
  - WP-3: PR template -- **done**
  - WP-4: SESSION_CONTEXT.md cleanup + cross-reference updates -- **done**
  - WP-5: Flask-Talisman security headers -- **DROPPED** (YAGNI; CSP broke inline
    styles in SVG logo, Bootstrap progress bar, and album cover fallback; fixing
    requires template refactor outside batch scope; reverted cleanly to WP-4 state)
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

### 2026-03-04 - Batch 17 WP-0: definition committed (Batch 17 WP-0)

- **Batch 17 started.** Branch `wip/batch-17` created from `main`.
- Definition committed: `BATCH17_DEFINITION.md` (5 WPs: HANDOFF_PROMPT fix, CI/CD,
  PR template, SESSION_CONTEXT cleanup, Flask-Talisman security headers).
- Baseline: **350 tests passing**, branch clean, all hooks green.
- Next: WP-1 -- fix 3 problems in HANDOFF_PROMPT.md.

### 2026-03-04 - Batch 17 WP-1: HANDOFF_PROMPT.md fixes (Batch 17 WP-1)

- Applied 3 targeted edits to `HANDOFF_PROMPT.md` per definition Section 2 WP-1.
- Edit 1 (Section 1 step 3): replaced "Active batch: file is at the repo root"
  with "Active batch: definition file is at repo root" and added "Between batches:
  no definition file exists yet -- skip this step."
- Edit 2 (Section 5): added introductory sentence "After your code changes are
  committed (following AGENTS.md commit rules and side-task handling), document
  completion:" before the 5-step numbered list. List unchanged.
- Edit 3 (Section 1): added step 5 for `MEMORY.md` (root) after SESSION_CONTEXT
  step; updated "all four files" to "all five files".
- **Deviation:** `HANDOFF_PROMPT.md` was in `.gitignore` (line 45) with no git
  history. The WP definition specified a commit including it. Because the file's
  purpose is cross-agent bootstrapping -- it must be accessible on any clone or
  to any agent (Copilot, Gemini, Codex) -- gitignoring it defeats its purpose.
  Owner confirmed: remove from `.gitignore` and commit. `.gitignore` updated with
  a comment explaining the distinction: HANDOFF_PROMPT.md is committed (shared
  procedure); MEMORY.md (root) stays local-only (machine-specific state).
- `AGENTS.md` unchanged. **350 tests passing**, all hooks green.
- Next: WP-2 -- CI/CD pipeline improvements.

### 2026-03-04 - Batch 17 WP-2: CI/CD pipeline improvements (Batch 17 WP-2)

- Renamed workflow `name:` from `"CI Pipeline"` to `"Quality Gate"` and job id
  from `test` to `quality-gate`. Name change is a breaking change if branch
  protection rules reference the old check name -- no branch protection rules
  are currently configured so there is no impact. Documented in definition.
- Removed standalone "Lint code with flake8" step. Pre-commit runs flake8 with
  identical `.flake8` config in the preceding step; the standalone step was a
  pure duplicate adding ~20s per run with identical output.
- Added pip caching to `setup-python` step (`cache: 'pip'`,
  `cache-dependency-path: requirements-dev.txt`). Cache key hashes the dev
  requirements file and invalidates automatically when dependencies change,
  eliminating a full reinstall on every unchanged run.
- Added `Upload coverage report` step (actions/upload-artifact@v4, 14-day
  retention). `coverage.xml` was already generated by pytest but silently
  discarded; this makes it available for review after each run.
- Added `Security audit (pip-audit)` step (pypa/gh-action-pip-audit@v1.1.0,
  `continue-on-error: true`). Informational only -- findings do not block
  builds; review manually when step shows warnings.
- Created `.github/dependabot.yml`: weekly pip + github-actions updates,
  5-PR cap for pip and 3 for actions. Dependabot PRs go through the same
  Quality Gate as any other PR.
- **350 tests passing**, all hooks green.
- Next: WP-3 -- PR template.

### 2026-03-04 - Batch 17 WP-2 addendum: pre-commit hook improvements (Batch 17 WP-2)

- **Widened scope of `trailing-whitespace` and `end-of-file-fixer`** from
  `^.*\.py$` to `^.*\.(py|md|yaml|yml|txt)$`. These hooks were silently
  skipping all markdown, YAML, and text files; the project has substantial
  `.md` doc content that was unchecked. Auto-fixed on first run: trailing
  space in `.pre-commit-config.yaml`; missing final newline in `README.md`
  and `requirements.txt`.
- **Added `check-merge-conflict`**: catches `<<<<<<<` conflict markers left
  in files before they reach a commit. Uses the same `pre-commit-hooks`
  repo already pinned at v5.0.0 -- no new dependency.
- **Added `detect-private-key`**: defense-in-depth catch for accidentally
  staged API keys or secrets. Relevant given this project handles
  `LASTFM_API_KEY`, `SPOTIFY_CLIENT_SECRET`, and `SECRET_KEY`. `.env` is
  already gitignored; this catches inline leakage. Same repo, no new dep.
- **350 tests passing**, all hooks green.
- Next: WP-3 -- PR template.

### 2026-03-04 - Batch 17 WP-3: PR template (Batch 17 WP-3)

- Created `.github/PULL_REQUEST_TEMPLATE.md` with Summary section and a
  6-item validation checklist. The checklist mirrors existing requirements
  from `AGENTS.md` and `HANDOFF_PROMPT.md` -- no new requirements added.
- Checklist items: pytest pass + test count update, pre-commit pass,
  doc_state_sync --check, PLAYBOOK Section 3 state, PLAYBOOK Section 4
  log entry (with batch-vs-side-task placement reminder), and scope gate.
- "SESSION_CONTEXT Section 1" in the checklist reflects post-WP-4
  numbering; after WP-4 removes the product context section and renumbers,
  Section 1 will be the current state table (currently Section 2).
- **350 tests passing**, all hooks green.
- Next: WP-4 -- SESSION_CONTEXT.md cleanup + cross-reference updates.

### 2026-03-04 - Batch 17 WP-4: SESSION_CONTEXT cleanup + cross-reference updates (Batch 17 WP-4)

- **Deleted SESSION_CONTEXT Section 1 "What is ScrobbleScope?"** (product
  description: app summary, upcoming features, stack, deployment). This
  content already exists in full in README.md. An agent state dashboard
  should contain runtime facts only; the section added 15 lines of
  overhead to every bootstrap read with no information gain for agents.
- **Renumbered sections** -1: Section 2 -> 1, 3 -> 2, 4 -> 3, 5 -> 4,
  6 -> 5, 7 -> 6, 8 -> 7. All internal heading numbers updated.
- **Fixed staleness in new Section 1** (was Section 2): Branch updated
  to `wip/batch-17`; Batch 17 row added as `**Active**`. app.py line
  count updated from ~142 to ~152 (actual: 151 lines).
- **Updated Section 7 env notes**: dev_start.py description now notes
  `--workers 1 --threads 4` (Gunicorn production config via Dockerfile).
  Pre-commit hook list updated to include check-merge-conflict and
  detect-private-key (added in WP-2 addendum).
- **AGENTS.md**: updated all SESSION_CONTEXT section number references
  (Section 2 -> 1, Section 4 -> 3, Section 5 -> 4, Sections 2-5 -> 1-4,
  Sections 4-5 -> 3-4, Section 8 -> 7). 8 references updated across
  bootstrap, pre-work checklist, side-task handling, doc sync, and
  anti-pattern registry sections.
- **HANDOFF_PROMPT.md**: updated 2 section number references -- step 4
  bootstrap instruction (Sections 2/3/4-5 -> 1/2/3-4) and the
  "agree on what is next" sentence (Section 3 -> Section 2).
- **Note:** DEVELOPMENT.md line 174 had a stale "SESSION_CONTEXT Section 2"
  reference; out of scope for this WP (definition lists AGENTS.md and
  HANDOFF_PROMPT.md only). Subsequently fixed in a side-task (see logarchive).
- **350 tests passing**, all hooks green.
- Next: WP-5 -- Flask-Talisman security headers.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-03-05 - side-task: PR review fixes (CI cache, DEVELOPMENT.md, README, doc tidiness)

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
