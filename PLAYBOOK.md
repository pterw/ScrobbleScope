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
  - WP-1: extract `_http_client.py`; fix CSRF; update verdict to `db_cache_lookup_hits`; docstrings. **Next.**
  - WP-2: 13 unit tests for `_http_client` + `smoke_cache_check`. **Pending.**
  - WP-3: `scripts/dev/dev_start.py` Docker+Flask startup helper. **Pending.**
  - WP-4: `concurrent_users_test.py` + 6 unit tests. **Pending.**
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

### 2026-03-03 - Add local DB setup and init_db.py caveat to env docs

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added local Postgres DB setup details and `init_db.py` load_dotenv caveat
to AGENTS.md Environment Setup and SESSION_CONTEXT Section 8. These facts apply to
all agents (Gemini CLI, Copilot, Codex, Claude Code) running local DB tests.

**Why:** `init_db.py` has no `load_dotenv()` call. Any agent running it will get
"DATABASE_URL not set" unless the env var is set directly in the shell. Absent from
canonical docs, every agent would hit this silently and assume cache is unavailable.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.
