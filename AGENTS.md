# AGENTS.md: Rules for AI Agents

ScrobbleScope: Flask + Python 3.13, Last.fm scrobbles + Spotify enrichment,
asyncpg/Postgres cache, pytest. This file is the stable repository ruleset
for GitHub Copilot and other repo-aware agents. The doc files listed below
serve as external memory shared across sessions.

---

## Document Roles (SoC contract)

| File | Role | Contains |
|------|------|----------|
| `AGENTS.md` (this file) | **Rules** | How agents must behave. Stable; rarely changes. |
| `HANDOFF_PROMPT.md` | **Session-start procedure** | Post-read verification steps and the end-of-session handoff checklist. Rules (bootstrap order, gates, commit discipline) live in `AGENTS.md`. |
| `AGENT_NOTES.md` | **Owner context** | Owner preferences, local dev setup, architectural constraints, known issues. |
| `.claude/SESSION_CONTEXT.md` | **Dashboard** | Current project state snapshot. No rules, no history. |
| `PLAYBOOK.md` | **Work order** | What to do next, what was just done. Active batch + execution log. |
| `README.md` | **Product docs** | User/developer setup and context. Not for agent orchestration. |
| `docs/history/` | **Archive** | Completed batch definitions (`definitions/`), per-batch execution logs (`logs/`), audit reports. |

**Anti-duplication rule:** Each fact lives in exactly one file. If you need to
reference a fact owned by another file, link to it -- do not copy it.

---

## Session Bootstrap (in order)

**Fast-path for Copilot comment jobs:** When no direct review-comment link is
supplied, first fetch comments and determine whether any new `@copilot`
comments are actionable. If none are actionable, stop immediately without
running full bootstrap. If a single actionable comment is scoped to a known
file/section, read only that target file plus any directly related test or
config file needed to validate the change.
Actionable means a concrete request, question, or correction addressed to
`@copilot`; praise, status updates, and threads where the author rejected the
suggestion are non-actionable.

**Fast-path for targeted review-comment jobs:** If the prompt links to a
single review comment or `discussion_r...` URL, fetch that thread first and
work from the linked file/lines before opening broader bootstrap docs. Read
only the minimum bootstrap/context files needed to answer that thread. Open
batch definitions or archive/history docs only when the linked comment
explicitly depends on batch-acceptance or historical context.

1. `AGENTS.md` (this file) -- rules, commit format, doc sync policy,
   anti-patterns.
2. `PLAYBOOK.md` Section 3 (next action) + Section 4 (current-batch log).
3. The batch definition file named in Section 3 (repo root while active;
   under `docs/history/definitions/` once the batch is closed; between
   batches no file exists -- skip this step).
4. `.claude/SESSION_CONTEXT.md` -- current batch, test count, architecture, risks.
5. `AGENT_NOTES.md` -- owner preferences, local dev setup, constraints.
6. Relevant `docs/history/` doc only if the log references one.
7. `FINDINGS.md` -- read on demand only: when PLAYBOOK Section 4 or your
   task explicitly references an F-* finding ID or an open P0/P1 item.
   Not part of the mandatory bootstrap set.

This list is the single canonical bootstrap order; `HANDOFF_PROMPT.md` links
here and adds only the post-read verification steps.

Bootstrap is complete when the sources agree. During an active batch that
means PLAYBOOK Section 3, the batch definition, and SESSION_CONTEXT
Section 1 all agree on the current batch and next WP. Between batches no
definition exists, so the gate is PLAYBOOK Section 3 and SESSION_CONTEXT
Section 1 agreeing that the last batch is closed and none is open.
If two bootstrap files conflict, follow the stricter safety rule and pause
only when the conflict affects the next action.

**Token discipline for bootstrap:**
- Always read Sections 1-2 of `.claude/SESSION_CONTEXT.md`; Sections 3-5 only if structure, dependency, or architecture detail is needed.
- Read only Sections 3-4 of `PLAYBOOK.md` by default.
- Open archive files only when Section 4 links to one for the task at hand.
- Do not paste long historical logs into prompts; link files instead.
- When citing repository files in chat, use full filesystem paths. For tool
  inputs, follow the tool's required path format (absolute or repository-relative).

---

## GitHub Copilot Environment Notes

- Work from the fresh repository clone provided by the Copilot task
  environment; do not assume access to the owner's interactive shell.
- Use GitHub-provided tooling for PR creation, review replies, workflow
  inspection, and progress reporting when those tools are available.
- Do not push with `git push` or `gh pr create` from the shell when the
  Copilot environment exposes dedicated progress or PR tools instead.
- For CI, build, test, or workflow failures, inspect GitHub Actions runs
  and job logs before concluding that CI details are unavailable.
- Treat this `AGENTS.md` file as the authoritative ruleset for repository
  task sessions. Do not read `.github/agents/`; those files may target
  other agent types and can conflict with this ruleset. If you suspect
  drift between the two locations, pause and ask the owner to reconcile
  them instead of trying to merge rule sources yourself.

---

## Environment Setup

```bash
# The ONLY virtualenv is .venv/ in the repo root.
# Never use venv/, bare pip, or python -m pip without the qualified path.
#
# Activate (for interactive use):
# Windows:  .venv\Scripts\activate
# Linux:    source .venv/bin/activate
#
# Install deps (always use the qualified pip path, never bare pip):
# Windows:  .venv\Scripts\pip install -r requirements-dev.txt
# Linux:    .venv/bin/pip install -r requirements-dev.txt
```

All packages in `requirements.txt` and `requirements-dev.txt` are pinned
with `==`. Do not add `>=` or unversioned entries. If a new package is
needed for a WP, propose it to the owner and wait for explicit approval
before running any pip command.

**Note:** The qualified-path rule (`.venv/Scripts/pip`) applies to **local
development only**. In GitHub Actions (CI), the runner manages its own Python
environment and bare `pip install` is correct -- do not add `.venv/` paths
to the workflow file. In GitHub Copilot task sessions, avoid ad-hoc package
installs unless the task requires them and the owner has approved the change.

API keys in `.env` (git-ignored). Template: `.env.example`.
Required: `LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
`SECRET_KEY` (min 16 chars; startup refuses weak values in production).
Optional: `DATABASE_URL` (Postgres; enables persistent Spotify metadata cache).
Local dev connection string: `postgresql://postgres:postgres@localhost:5432/scrobblescope`
(requires a running Postgres instance; see Docker setup in `AGENT_NOTES.md` Local Dev Setup).
Run `python init_db.py` once to create the schema. **Caveat:** `init_db.py` has no
`load_dotenv()` call -- set `DATABASE_URL` directly in the shell before running it;
the Flask app reads `.env` automatically via `load_dotenv()` at startup.

For local development with the Postgres cache, use `python scripts/dev/dev_start.py`
instead of `python app.py` directly. This script checks and starts the `ss-postgres`
Docker container if needed, then launches Flask in one command.

---

## Pre-Work Checklist

1. `pytest -q` passes (baseline count is in SESSION_CONTEXT Section 1).
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
Documentation is written first, then validated -- a gate that runs before
the doc update cannot check it, and `pre-commit` includes the
`doc-state-sync-check` hook.

1. Update PLAYBOOK Section 3 + Section 4. Batch log entries carry a
   `(Batch N WP-X)` tag in the heading; side-task entries are untagged
   (see Side-Task Handling).
2. `python scripts/doc_state_sync.py --fix` -- rotates and refreshes the
   managed blocks from the text you just wrote.
3. `pytest -q` -- all tests pass.
4. `pre-commit run --all-files` -- all hooks pass.
5. `python scripts/doc_state_sync.py --check` -- exits 0 on the final
   state (the root `BATCHN_DEFINITION.md` warning is expected while a
   batch is active).
6. Stage specific paths by name. **Never `git add -A` or `git add .`**,
   not even when every changed file belongs to this work package -- the
   prohibition is on the command, because it silently picks up whatever
   else is in the tree. Stage only files changed for this work package,
   and stage `.claude/SESSION_CONTEXT.md` together with PLAYBOOK whenever
   it changed -- do not leave it modified and unstaged.
7. Commit after each WP (do not batch multiple WPs into one commit).
   Do not push without explicit owner instruction. Pause after each commit
   for owner review.
   **Standing exception -- Claude Code and Codex sessions only (granted
   2026-07-31):** commits that respond to review feedback on an
   already-open PR may be pushed without asking each time, followed by one
   batched reply per review round. This covers review-fix commits only.
   Batch and WP commits still pause for owner review, and force-pushes,
   history rewrites, and anything targeting `main` always require explicit
   instruction. The exception does **not** extend to GitHub Copilot task
   sessions or their subagents, Jules, or any other agent -- those follow
   the unmodified rule above.
   When authorized to push in a GitHub Copilot session, use the platform
   progress/reporting tool; do not push directly with shell `git`/`gh`.

**Pre-push self-review.** The validation gates check mechanics (tests,
formatting, docsync markers); nothing in the toolchain checks whether one
document now contradicts another. That gap is what turns a single review
comment into a chain of rounds, each fixing damage from the last. Before
pushing, spend the two minutes these four checks cost:

1. Read each changed file **whole**, not as a diff -- contradictions hide
   in the unchanged text next to the edit.
2. Run the blast-radius greps described in the Anti-Pattern Registry
   under "Fixing the instance instead of the class", "Lossy or
   contradictory consolidation", and "Assertions over sets, ranges, and
   citations": citations of anything renumbered or renamed, sibling
   copies of any corrected claim, and every set or range the change
   asserts.
3. Walk any procedure touched through its edge states, per
   "Happy-path-only procedures".
4. Prefer deletion to addition. Every added sentence is new surface area
   that a later change can contradict; collapsing a duplicate to a
   pointer removes surface area permanently.

**Co-author prohibition:** Do NOT add `Co-authored-by` trailers or any co-author
metadata to commits. This repo uses multi-agent orchestration; attribution is
managed by the owner, not by individual agents.

---

## Side-Task Handling

Not all work is batch work (e.g., a leap-year bugfix, a dark-mode polish commit).
Non-batch changes follow the commit rules above unchanged -- including the
documentation step, which puts the dated Section 4 entry in the *same*
commit as the change ("Missing log entries" in the Anti-Pattern Registry).
Side-tasks differ only in where that entry goes and how it is tagged:

1. Add the dated entry in PLAYBOOK Section 4 **after** the
   `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, using the same log format
   but **without** a `(Batch N WP-X)` suffix in the heading.
   Placing it outside the current-batch markers avoids the batch-aware
   filter that would treat untagged entries as stale when tagged entries
   exist. Entries after the end marker are subject to the standard
   `--keep-non-current` rotation policy (default: keep 4).
   **Insert the new entry directly after the end marker** (top of the
   non-current list), not at the bottom. The list is ordered newest-first
   and rotation keeps the first `--keep-non-current` entries positionally,
   rotating the rest -- once the window is at capacity, a bottom-appended
   entry is treated as oldest and archived by the very next `--fix` run
   instead of staying in the active window (below capacity it is
   retained, but top placement is still correct).
2. Run `doc_state_sync.py --fix`.
3. Update SESSION_CONTEXT Section 1 if the change affects test count or project state.

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

`SESSION_CONTEXT.md` is committed and shared across all agents. `--check` warns on
stderr when the STATUS block is stale but does not fail. `--fix` writes the refreshed
STATUS block to disk; commit the result so the next agent session starts with accurate
state.

Root `BATCHN_DEFINITION.md` warnings are expected while a batch is active
and PLAYBOOK Section 3 points to that root definition. Treat them as a
reminder that the definition must be archived at close-out, not as a blocker
during active work. After close-out, the root warning should disappear.

**Real issues** (act on these):
- "Test count mismatch" where SESSION_CONTEXT Section 1 and the most-recent
  current-batch log entry in PLAYBOOK Section 4 disagree on the **current**
  test count. Fix whichever file is stale. The scan reads `**N passed**`
  or `**N tests passing**` (bold-wrapped only) from the newest Section 4
  entry inside the `DOCSYNC:CURRENT-BATCH-START/END` markers. Historical
  entries outside those markers are not scanned.
- "Broken archive link" when a markdown file path under `docs/history/` or
   `docs/logarchive/` in PLAYBOOK does
  not exist on disk.

### Before writing to Section 4

Before appending a new dated entry to PLAYBOOK Section 4, search the existing
archive to avoid re-describing an already-recorded decision and to prevent
title/date collisions:

```bash
rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
rg -n "^### 20" docs/history/logs/*.md
```

### What to update after a WP or side-task commit

- PLAYBOOK Section 3 (status) + Section 4 (dated log entry -- inside markers
  for batch work, after end marker for side-tasks; see Side-Task Handling).
- SESSION_CONTEXT Section 1 (test count, batch status row) if changed.
- SESSION_CONTEXT Section 3 (project structure) and Section 4 (dependency
  graph) if modules are added, removed, renamed, or dependencies change.
- `README.md` for user/developer-visible setup or behavior changes.
  **Exception:** If the active batch definition includes a dedicated README
  WP (e.g., WP-5), README updates may be deferred to that WP to avoid
  churn from intermediate WPs that change paths or structure.
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
3. **Update PLAYBOOK Section 2** table: the active batch already has a row
   (its Definition cell points at the root file and its Log cell reads
   `active -- Section 4`). Repoint that existing row at
   `docs/history/definitions/BATCHN_DEFINITION.md` and fill the Log cell
   with `docs/history/logs/BATCHN_LOG.md`. Add a new row only if the batch
   has none.
4. **Update SESSION_CONTEXT** Section 1 batch status row: `**Complete**. All N WPs done.
   Definition: docs/history/definitions/BATCHN_DEFINITION.md.`
5. **Run `--fix` again** to refresh the STATUS block.
6. **Verify clean:** `python scripts/doc_state_sync.py --check` must exit 0 with no
   "Broken archive link" warnings (the two expected root BATCH file warnings disappear
   once the definition file has been archived by the step above).
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
5. **Docstrings and comments:** every function has a comprehensive
   docstring; inline comments explain non-obvious logic (the why, not the
   what). SoC/DRY is the constraint on file content, not line count.

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
   SESSION_CONTEXT Section 4. Any new cross-module import must be reflected
   in the documented acyclic dependency graph.
3. **Silent doc staleness:** Committing code changes that affect test count,
   module structure, or dependency graph without updating the corresponding
   documentation (README project structure, SESSION_CONTEXT Sections 3-4,
   PLAYBOOK Section 3). Every code commit must include any doc updates
   needed to keep bootstrap files accurate.
4. **Wrong venv or bare pip (incident 2026-03-04):** Using `venv/` instead
   of `.venv/`, or running bare `pip install` without the explicit
   `.venv/Scripts/pip` path, can silently install into the wrong environment
   or drain the active venv. This happened in Batch 17 and caused a full
   package reinstall with version drift. Always use `.venv/Scripts/pip`
   (Windows) or `.venv/bin/pip` (Linux) explicitly.
5. **Background server processes:** Starting `python app.py` or any Flask
   server in a background Bash process and not cleaning it up blocks the
   owner's terminal. Never start a server via the Bash tool. The owner runs
   the app in their own terminal. To probe a running server use
   `python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').status)"`.
6. **Naive-tz vacuous datetime tests (PR #152, F-B19-6):** A datetime test
   that builds its inputs with the same tz-awareness pattern (naive vs
   aware) as the code under test compares the code against itself, not
   against an invariant -- it passes even if the code silently regresses
   to a naive-tz day-shift bug. Build test inputs with explicit `tzinfo=`
   and assert on a date that would shift under a naive interpretation.
   Canonical example: `tests/test_heatmap.py::TestAggregateDailyCounts::`
   `test_utc_decode_invariant_against_local_tz_drift`.
7. **Skipping hooks:** Never commit with `--no-verify`. Fix the failing
   hook instead.
8. **Stale PLAYBOOK Section 3:** Section 3 not reflecting the true state
   of every WP at all times (see Doc Sync Rules, mid-batch handoff
   discipline).
9. **Missing log entries:** a WP or side-task commit without its dated
   PLAYBOOK Section 4 entry.
10. **Stale dashboard figures (coverage incident 2026-07-28):** quoting a
    canonical number (coverage, test count, module count) from docs
    without re-measuring. The "~72%" coverage figure survived five months
    of doc passes while the real figure was 89%. Re-run the measuring
    command before repeating a number in any doc.
11. **Fixing the instance instead of the class:** repairing the reported
    symptom while its siblings survive untouched. Two forms recur:
    renumbering or renaming something without updating the prose that
    cites the old number or name, and correcting a factual claim in one
    file while identical copies remain elsewhere. This is the single
    largest source of repeat review rounds in this repository -- a
    documentation PR needed several extra rounds because each round's
    findings were produced by the previous round's own fixes. Every edit
    requires a blast-radius grep before the validation gates:
    - after renumbering or renaming, run
      `rg -n "step \d|Registry #\d|rule \d|criterion \d"` across the
      docs and repoint each hit by **name**, not number -- a name
      cannot go stale when the list reorders;
    - after correcting a factual claim, grep its distinctive phrase
      repo-wide and fix every copy in the same commit, or delete the
      copies and link to the single owner (Anti-duplication rule).
    A fix that leaves siblings behind is half a fix and costs another
    review round.
12. **Lossy or contradictory consolidation:** collapsing a duplicated
    rule to a single owner, but (a) leaving the copies in place while
    the new text claims they were removed, (b) dropping a specific
    prohibition during the collapse -- a bulk-staging ban was nearly
    lost this way, because the canonical text said which files to stage
    but not which command never to use -- or (c) writing canonical text
    that contradicts another section of the same file, as when a
    "document before committing" rule was added while Side-Task
    Handling still instructed agents to commit first. When
    consolidating: re-read the **whole** destination file rather than
    the diff, and compare the removed text against the new pointer to
    confirm no requirement was silently dropped.
13. **Assertions over sets, ranges, and citations:** stating a property
    of a group without checking each member. Real examples from this
    repository: a claim that a variable is read across all seven page
    CSS files when one of them does not use it; a differential baseline
    headed "Open findings" that listed an ID already marked resolved; a
    cross-reference to an anti-pattern that does not cover the case
    being argued; and a citation naming a gitignored file no
    contributor can open. Ranges (`X through Y`) and "all N" phrasings
    are the highest-risk constructions here: expand them and verify
    member by member, or rewrite the claim so it does not depend on the
    membership.
14. **Happy-path-only procedures:** a numbered procedure that only
    works in one state. Examples that reached the canonical docs: a
    close-out step saying "add a row" for a table row that already
    exists, a bootstrap sufficiency gate requiring a batch definition
    file that by design does not exist between batches, and a
    validation gate ordered before the work it validates. Walk every
    procedure through its edge states -- active batch vs between
    batches, first run vs re-run, item present vs absent -- before
    committing it.

---

## Finding-Writing Rules

Findings live in `FINDINGS.md` (active) and rotate to
`docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out or during a
dedicated findings-cleanup WP. Nothing is deleted -- the archive preserves
grep history.

1. **F-ID format:** every item heading is `F-<context>-<N>: <title>`.
   Context is a batch tag (`B18`, `B19`, `B20`, ...) or a source tag
   (`MAS` for MULTI_AGENT_SWEEP, `DOCSYNC`, `AUDIT`, `LOAD` for the
   load-testing session); `FEATURE` covers feature-prep notes. No
   bare-numbered items in FINDINGS.md.
2. **Required fields:** the F-ID heading, a one-sentence problem statement,
   a `Status:` line, and a `Source:` line when the finding came from a
   named audit or session.
3. **Rotation:** resolved and closed no-action items move to the archive
   with their original F-ID and a `-- RESOLVED` / `-- NO ACTION` suffix.
   Standing design-decision Info items (documentation of deliberate,
   still-current choices) keep their F-IDs in the active file and rotate
   only when superseded.
4. **Cross-references:** promoted or absorbed findings keep a one-line
   pointer in the "Deferred / future-batch candidates" block (for
   example, `F-B18-1 -- promoted to F-B20-2`) so old IDs stay resolvable.

---

## Markdown Authoring Rules

- ASCII-only characters (no smart quotes, no em-dash -- use `--`).
- ISO dates: `YYYY-MM-DD`.
- Log entries must include: scope, plan vs implementation, deviations,
  validation results (test count), and forward guidance.
- Do not manually move entries across DOCSYNC markers; use `doc_state_sync.py`.
