# AGENTS.md: Instructions for AI Agents

ScrobbleScope is a Flask web app that fetches a user's Last.fm scrobbles for a
given year, enriches album data with Spotify metadata, and presents filterable
top-album rankings. Built on Python 3.13, aiohttp/aiolimiter, Flask-WTF, asyncpg
(Postgres), and pytest.

---

## Session Bootstrap (required, in order)

1. `.claude/SESSION_CONTEXT.md` -- current batch, test count, architecture snapshot,
   risk notes, and env notes. Read this first to orient fast.
2. `PLAYBOOK.md` -- batch ordering, acceptance criteria, active execution log (Section
   9 = next action, Section 10 = current-batch log).
3. `README.md` -- product context and setup when needed.
4. Relevant `docs/history/` doc if the PLAYBOOK Section 10 log references one for the
   current work package.

SESSION_CONTEXT Section 2 has the current test count and batch status. PLAYBOOK
Section 9 is the source of truth for what to do next. If those two agree, you have
enough context to start without reading anything else.

---

## Environment Setup

```bash
pip install -r requirements-dev.txt   # runtime + pytest/pre-commit/lint
```

API keys go in `.env` (git-ignored). Template: `.env.example`.
Required keys: `LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
`SECRET_KEY` (min 16 chars; startup refuses weak values in production).
Optional: `DATABASE_URL` (Postgres; enables persistent Spotify metadata cache).

---

## Pre-Work Checklist

Before touching any file, confirm:

1. `pytest -q` passes (note the baseline count from SESSION_CONTEXT).
2. `pre-commit run --all-files` passes.
3. The batch/work-package you are implementing matches PLAYBOOK Section 9.

---

## Commit Rules

All commits must follow Conventional Commits with imperative-mood subject:

```
<type>(<scope>): <subject>   # max 72 chars, imperative, no trailing period
<blank line>
<body>                        # explain WHY; wrap at 72 chars
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`

**Subject rules:**
- Imperative: "Add", "Fix", "Extract", "Remove" -- NOT "Added", "Fixes"
- No period at the end
- Max 72 characters

**Procedure before every commit:**
1. `pytest -q` -- all tests must pass
2. `pre-commit run --all-files` -- all hooks must pass (black, isort, autoflake,
   flake8, trim-whitespace, fix-end-of-files, check-yaml, doc-state-sync-check)
3. Stage only the files changed for this work package
4. Commit and push after each completed work package (do not batch multiple WPs
   into one commit unless they are inseparable)

---

## Test Quality Rules

Tests must challenge real behaviour, not just confirm mocks were called.

**Forbidden patterns (sycophantic tests):**
- Mock-call-only: `mock_fn.assert_called_once()` with no argument check and no
  state assertion. Replace with a state diff (e.g., snapshot `JOBS.keys()` before
  and after).
- Return-value-only: asserting on what a function returns when the real consumer
  reads from shared state (e.g., `JOBS` dict). Assert on the shared state too.
- Vacuous (no assertion): a test that passes if the function under test is deleted.
  Every test must have at least one meaningful assertion.
- Near-duplicate: two tests that cover the same code path with no unique regression
  protection. Merge or remove the weaker one.
- Happy-path only: new helpers extracted from production code must have at least one
  adversarial test that triggers the non-happy path (error branch, fallback value,
  filter firing, etc.).

**Good patterns:**
- Assert on JOBS/shared-state side-effects, not just return values.
- Use `caplog` to verify warning/error log lines for failure paths.
- Use boundary inputs (zero, None, empty, missing keys) to hit fallback branches.
- Import helpers directly in tests to document their contract independently of the
  HTTP routing layer.

---

## Doc Sync Rules

After any change to PLAYBOOK Section 10 or SESSION_CONTEXT managed blocks, run:

```bash
python scripts/doc_state_sync.py --fix
```

Then re-run pre-commit (the `doc-state-sync-check` hook validates the sync).

**At batch close-out** (all WPs done, moving to between-batch state), clear the
`<!-- DOCSYNC:CURRENT-BATCH-START -->` block and rotate entries:

```bash
python scripts/doc_state_sync.py --fix --keep-non-current 0
```

Then manually move the `<!-- DOCSYNC:CURRENT-BATCH-START -->` marker to just above
`<!-- DOCSYNC:CURRENT-BATCH-END -->` (leaving the block empty). The script treats an
empty current-batch block as a valid between-batch state.

---

## Required Doc Updates

After any behavior, config, or process-contract change, update all applicable docs in
the same work package commit (or a separate docs commit in the same WP):

- `PLAYBOOK.md` Section 9 (status) + Section 10 (log entry inside CURRENT-BATCH
  markers) for any batch work.
- `.claude/SESSION_CONTEXT.md` Section 2 (test count, batch status row) + Section 8
  (test table) + Section 9 (env note).
- `README.md` for user/developer-visible setup or behavior changes.
- A `docs/history/<TOPIC>_<DATE>.md` file for any significant finding or audit.

Run `python scripts/doc_state_sync.py --fix` after any Section 10 edit, then verify
`pre-commit run --all-files` is clean before committing.

---

## Markdown Authoring Rules

- ASCII-only characters (no smart quotes, no em-dash -- use `--`).
- ISO dates: `YYYY-MM-DD`.
- Execution log entries must include: scope, plan vs implementation, deviations,
  validation results (test count), and forward guidance.
- Do not manually move entries across DOCSYNC markers; use `doc_state_sync.py`.
