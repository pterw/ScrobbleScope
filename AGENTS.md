# AGENTS.md: Rules for AI Agents

ScrobbleScope: Flask + Python 3.13, Last.fm scrobbles + Spotify enrichment,
asyncpg/Postgres cache, pytest. Multi-agent orchestration -- these doc files
are external memory shared across agents.

---

## Document Roles (SoC contract)

| File | Role | Contains |
|------|------|----------|
| `AGENTS.md` (this file) | **Rules** | How agents must behave. Stable; rarely changes. |
| `.claude/SESSION_CONTEXT.md` | **Dashboard** | Current project state snapshot. No rules, no history. |
| `PLAYBOOK.md` | **Work order** | What to do next, what was just done. Active batch + execution log. |
| `README.md` | **Product docs** | User/developer setup and context. Not for agent orchestration. |
| `docs/history/` | **Archive** | Completed batch definitions, rotated execution logs, audit reports. |

**Anti-duplication rule:** Each fact lives in exactly one file. If you need to
reference a fact owned by another file, link to it -- do not copy it.

---

## Session Bootstrap (in order)

1. `.claude/SESSION_CONTEXT.md` -- current batch, test count, architecture, risks.
2. `PLAYBOOK.md` Section 3 (next action) + Section 4 (current-batch log).
3. Relevant `docs/history/` doc if the log references one.

If SESSION_CONTEXT Section 2 and PLAYBOOK Section 3 agree on the current batch
and next WP, you have enough context to start.

---

## Environment Setup

```bash
pip install -r requirements-dev.txt   # runtime + pytest/pre-commit/lint
```

API keys in `.env` (git-ignored). Template: `.env.example`.
Required: `LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
`SECRET_KEY` (min 16 chars; startup refuses weak values in production).
Optional: `DATABASE_URL` (Postgres; enables persistent Spotify metadata cache).

---

## Pre-Work Checklist

1. `pytest -q` passes (baseline count is in SESSION_CONTEXT Section 2).
2. `pre-commit run --all-files` passes.
3. The work you are implementing matches PLAYBOOK Section 3.

---

## Commit Rules

Conventional Commits, imperative mood, no trailing period:

```
<type>(<scope>): <subject>        # max 72 chars
                                  # blank line
<body>                            # explain WHY; wrap at 72 chars
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`

**Subject:** imperative ("Add", "Fix", "Extract") -- NOT "Added", "Fixes".

**Procedure before every commit:**
1. `pytest -q` -- all tests pass.
2. `pre-commit run --all-files` -- all hooks pass.
3. Stage only files changed for this work package.
4. Commit and push after each WP (do not batch multiple WPs into one commit).

**Co-author prohibition:** Do NOT add `Co-authored-by` trailers or any co-author
metadata to commits. This repo uses multi-agent orchestration; attribution is
managed by the owner, not by individual agents.

---

## Side-Task Handling

Not all work is batch work (e.g., a leap-year bugfix, a dark-mode polish commit).
For non-batch changes:

1. Commit normally following the commit rules above.
2. Add a dated entry in PLAYBOOK Section 4 (inside the CURRENT-BATCH markers)
   using the same format but **without** a `(Batch N WP-X)` suffix in the heading.
3. Run `doc_state_sync.py --fix`. Untagged entries rotate to the archive normally.
4. Update SESSION_CONTEXT Section 2 if the change affects test count or project state.

---

## Test Quality Rules

Tests must challenge real behaviour, not just confirm mocks were called.

**Forbidden patterns:**
- Mock-call-only with no argument check and no state assertion.
- Return-value-only when the real consumer reads shared state (`JOBS` dict).
- Vacuous: passes if the function under test is deleted.
- Near-duplicate: same code path, no unique regression protection.
- Happy-path only: new helpers must have at least one adversarial test.

**Good patterns:**
- Assert on shared-state side-effects, not just return values.
- `caplog` for warning/error log lines on failure paths.
- Boundary inputs (zero, None, empty, missing keys) to hit fallback branches.

---

## Doc Sync Rules

After any change to PLAYBOOK Section 4 or SESSION_CONTEXT managed blocks:

```bash
python scripts/doc_state_sync.py --fix
pre-commit run --all-files
```

At batch close-out (all WPs done):

```bash
python scripts/doc_state_sync.py --fix --keep-non-current 0
```

**What to update after a WP or side-task commit:**
- PLAYBOOK Section 3 (status) + Section 4 (dated log entry inside markers).
- SESSION_CONTEXT Section 2 (test count, batch status row) if changed.
- `README.md` for user/developer-visible setup or behavior changes.
- `docs/history/<TOPIC>_<DATE>.md` for significant findings or audits.

---

## Markdown Authoring Rules

- ASCII-only characters (no smart quotes, no em-dash -- use `--`).
- ISO dates: `YYYY-MM-DD`.
- Log entries must include: scope, plan vs implementation, deviations,
  validation results (test count), and forward guidance.
- Do not manually move entries across DOCSYNC markers; use `doc_state_sync.py`.
