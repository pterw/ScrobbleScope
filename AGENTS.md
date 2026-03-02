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
| `docs/history/` | **Archive** | Completed batch definitions (`definitions/`), per-batch execution logs (`logs/`), audit reports. |

**Anti-duplication rule:** Each fact lives in exactly one file. If you need to
reference a fact owned by another file, link to it -- do not copy it.

---

## Session Bootstrap (in order)

1. `.claude/SESSION_CONTEXT.md` -- current batch, test count, architecture, risks.
2. `PLAYBOOK.md` Section 3 (next action) + Section 4 (current-batch log).
3. Relevant `docs/history/` doc if the log references one.

If SESSION_CONTEXT Section 2 and PLAYBOOK Section 3 agree on the current batch
and next WP, you have enough context to start.

**Token discipline for bootstrap:**
- Read only Sections 2-5 of `.claude/SESSION_CONTEXT.md` and Sections 3-4 of `PLAYBOOK.md` by default.
- Open archive files only when Section 4 links to one for the task at hand.
- Do not paste long historical logs into prompts; link files instead.

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
2. Add a dated entry in PLAYBOOK Section 4 **after** the
   `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, using the same log format
   but **without** a `(Batch N WP-X)` suffix in the heading.
   Placing it outside the current-batch markers avoids the batch-aware
   filter that would treat untagged entries as stale when tagged entries
   exist. Entries after the end marker are subject to the standard
   `--keep-non-current` rotation policy (default: keep 4).
3. Run `doc_state_sync.py --fix`.
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

### What `doc_state_sync.py` does and why it exists

`scripts/doc_state_sync.py` is a deterministic sync tool that keeps
PLAYBOOK, SESSION_CONTEXT, and the archive file consistent so that every
agent starts from identical state. It:

1. **Rotates** overflow dated entries from PLAYBOOK Section 4 into
   per-batch log files (`docs/history/logs/BATCHN_LOG.md`) when the entry
   carries a `(Batch N WP-X)` tag, or into the monolith archive
   (`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`) for untagged
   side-task entries.
2. **Deduplicates** archive entries by SHA-256 fingerprint (same content
   is never stored twice).
3. **Refreshes** the machine-managed `DOCSYNC:STATUS` block in
   SESSION_CONTEXT from PLAYBOOK truth (Section 3 + Section 4).
4. **Cross-validates** content across files (test counts, stale headers).

**Lookup map (avoid path confusion):**
- Untagged side-task archive: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- Tagged per-batch logs: `docs/history/logs/BATCHN_LOG.md`
- Batch definitions: `docs/history/definitions/BATCHN_DEFINITION.md`

Without this script, agents would drift: one might update PLAYBOOK but
forget SESSION_CONTEXT, or manually move entries and break marker order.

### How to run

After any change to PLAYBOOK Section 4 or SESSION_CONTEXT managed blocks:

```bash
python scripts/doc_state_sync.py --fix
pre-commit run --all-files
```

At batch close-out (all WPs done):

```bash
python scripts/doc_state_sync.py --fix --keep-non-current 0
```

Modes: `--check` (read-only, exit 1 on drift), `--fix` (write updates), or
`--split-archive` (one-time migration: partition the monolith archive into
per-batch log files; run once after upgrading to per-batch routing).
The `--check` mode also runs as a pre-commit hook (`doc-state-sync-check`).

### Cross-validation warnings

The script prints `WARNING:` lines to stderr for cross-file inconsistencies.
These are **non-blocking** -- they never cause `--check` or `--fix` to fail.

`SESSION_CONTEXT.md` is treated as a local dashboard. `--check` warns on
stderr when the STATUS block is stale but does not fail (SESSION_CONTEXT is
gitignored and should not block commits). `--fix` writes the refreshed STATUS
block to disk so the next agent session starts with accurate state.

**Real issues** (act on these):
- "Test count mismatch" where SESSION_CONTEXT Section 2 and the most-recent
  current-batch log entry in PLAYBOOK Section 4 disagree on the **current**
  test count. Fix whichever file is stale. The scan reads `**N passed**`
  or `**N tests passing**` (bold-wrapped only) from the newest Section 4
  entry inside the `DOCSYNC:CURRENT-BATCH-START/END` markers. Historical
  entries outside those markers are not scanned.
- "Broken archive link" when a `docs/history/*.md` or
   `docs/logarchive/*.md` path in PLAYBOOK does
  not exist on disk.

### What to update after a WP or side-task commit

- PLAYBOOK Section 3 (status) + Section 4 (dated log entry -- inside markers
  for batch work, after end marker for side-tasks; see Side-Task Handling).
- SESSION_CONTEXT Section 2 (test count, batch status row) if changed.
- SESSION_CONTEXT Section 4 (project structure) and Section 5 (dependency
  graph) if modules are added, removed, renamed, or dependencies change.
- `README.md` for user/developer-visible setup or behavior changes.
- `docs/history/<TOPIC>_<DATE>.md` for significant findings or audits.

**Mid-batch handoff discipline:** PLAYBOOK Section 3 must reflect the true
state of every WP at all times -- not just after commits. If a deviation fix
is discovered and implemented during a WP, mark it in Section 3 immediately
(before committing) so any agent arriving mid-batch sees accurate state. The
log entry in Section 4 provides detail; Section 3 provides the at-a-glance
status. Both must agree.

---

## Batch Close-Out Procedure

When all WPs in the active batch are committed and validated:

1. **Run final sync:** `python scripts/doc_state_sync.py --fix --keep-non-current 0`
   (purges old non-current entries from PLAYBOOK Section 4 to keep it lean).
2. **Archive the definition file:** rename `BATCHN_PROPOSAL.md` (or equivalent)
   to `docs/history/definitions/BATCHN_DEFINITION.md` using `git mv`.
3. **Update PLAYBOOK Section 2** table: add a row for the batch linking to
   `docs/history/definitions/BATCHN_DEFINITION.md`.
4. **Update SESSION_CONTEXT** Section 2 batch status row: `**Complete**. All N WPs done.
   Definition: docs/history/definitions/BATCHN_DEFINITION.md.`
5. **Run `--fix` again** to refresh the STATUS block.
6. **Verify clean:** `python scripts/doc_state_sync.py --check` must exit 0 with no
   "Broken archive link" warnings (the two expected root BATCH file warnings disappear
   once the proposal is archived in step 2).
7. **Commit:** `chore(close-out): Batch N complete; archive definition and purge log`.

---

## Proposal and Design Rules

1. **Definition before execution:** Every batch must have a definition file
   (`BATCHN_DEFINITION.md` or equivalent) with acceptance criteria written
   and committed before any WP work begins. Retroactive definitions are a
   deviation and must be logged.
2. **Scope discipline:** Do not add work packages mid-batch unless the owner
   approves. Discovered issues that are out of scope become deviation notes
   in the log entry, not new WPs. If a fix is urgent and small (under ~20
   lines of code change), treat it as a deviation within the current WP; if
   it is larger, log it as a future-batch candidate.
3. **Size limits on new files:** No new file should be larger than the
   largest peer in its directory. If a new module or test file exceeds this
   threshold, split it before committing.
4. **Refactor requires parity tests:** Do not restructure existing code
   (rename, move, split, merge modules) without first verifying that
   existing tests cover the affected paths. If coverage is insufficient,
   add tests in a preceding WP.

---

## Anti-Pattern Registry

Patterns that have caused regressions or quality issues in past batches.
Agents must check their work against this list before committing.

1. **Test bloat without value:** Adding tests that duplicate existing
   coverage or that pass vacuously (test succeeds even if the function
   under test is deleted). Every new test must exercise a unique code path
   or boundary condition not covered by any existing test.
2. **Undocumented SoC violations:** Importing a leaf module into a
   higher-level module without updating the dependency graph in
   SESSION_CONTEXT Section 5. Any new cross-module import must be reflected
   in the documented acyclic dependency graph.
3. **Silent doc staleness:** Committing code changes that affect test count,
   module structure, or dependency graph without updating the corresponding
   documentation (README project structure, SESSION_CONTEXT Sections 4-5,
   PLAYBOOK Section 3). Every code commit must include any doc updates
   needed to keep bootstrap files accurate.

---

## Markdown Authoring Rules

- ASCII-only characters (no smart quotes, no em-dash -- use `--`).
- ISO dates: `YYYY-MM-DD`.
- Log entries must include: scope, plan vs implementation, deviations,
  validation results (test count), and forward guidance.
- Do not manually move entries across DOCSYNC markers; use `doc_state_sync.py`.
