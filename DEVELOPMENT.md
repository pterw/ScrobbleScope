# ScrobbleScope: Development Methodology

This document explains how ScrobbleScope was built: the orchestration
strategy, the tooling decisions, and the reasoning behind each one. It is
written for anyone who clones this repository and wants to understand why
the project is structured the way it is beyond what `AGENTS.md` prescribes.

---

## The Core Problem: Collaborating With Amnesiac Engineers

ScrobbleScope was built primarily by one developer working with several LLM coding agents -- some within VSCode and others externally -- across large gaps of time.

The bulk of the prototype-to-deployed-app work happened in a compressed Feb-March sprint, with lighter follow-up work in later months. Initially, the project was abandonned due to a thundering herd issue and a large monolithic app.py, this was remedied via flask blueprints and factories, thanks the introduction of a coding agent within VSCode. Later a second, and third coding agent were implemented in the IDE.

This led to the central challenge: at the time of development, LLMs have finite context windows and no
persistent memory. Further, they cannot communicate their work to other agents. Effectively, every session starts from zero. A model that produced
a clean architectural refactor yesterday has no idea it did so today, and a different model is oblivious to changes made by another model.

Left unmanaged, this produces:

- **Drift**: two agents editing related files with different assumptions
  about current state.
- **Regression**: an agent re-implementing something already done, or
  undoing a deliberate decision, because it has no record of why the
  previous state was chosen.
- **Token bloat**: a single "catch-up" file that grows unbounded and
  eventually eats most of the context window before any work is done.
- **Lost reasoning**: a code review tool flagging something as wrong
  because it has no causal knowledge of why the code looks the way it does.

The orchestration system described here was built specifically to address
these failure modes.

---

## The Orchestration Architecture

The external-memory layer consists of five tracked files and two archive
directories. Each has a primary concern, and the design goal is that
canonical facts live in exactly one place.

In practice there is some intentional overlap: `HANDOFF_PROMPT.md` condenses key rules and
procedures from `AGENTS.md` into a cold-start checklist -- it is a
convenience summary for session handoffs, not a second source of truth.

`AGENT_NOTES.md` cross-references `AGENTS.md` for venv rules rather than
restating them. `README.md` is excluded from the agent memory layer; it
exists for *people* to read and is explicitly not used for orchestration.

### `AGENTS.md` -- Rules

Written in imperative, rule-form language. Contains invariants that must
hold across all sessions and all agents: commit format, test quality
standards, what constitutes a side-task vs. batch work, how to bootstrap
a new session, how to run pre-commit and doc sync. It does not contain
current state, nor does it contain history. It is rarely subject to change.

The language is deliberately prescriptive ("Must", "Do not", "Forbidden")
because LLMs handle ambiguity poorly, and incorrect inference can lead to a broken pipeline or a mis-coped commit.

### `HANDOFF_PROMPT.md` -- Bootstrap Procedure

The step-by-step session-start checklist given to any agent beginning
work. Lists which files to read in what order, the validation gates to
run before every commit, commit discipline rules, and the handoff
procedure when leaving work for the next agent. Intended to be passed
verbatim as context when delegating to a new agent session.

### `AGENT_NOTES.md` -- Owner Context

Tracks facts that belong to no other file: owner workflow preferences,
local dev setup (Docker, Postgres, Browser MCP), architectural
constraints discovered during development, and known open issues. Tracked
in git so every agent -- regardless of tool or machine -- reads the same
preferences.

### `PLAYBOOK.md` -- Work Orders

The source of truth for what work is in progress, what is next, and what
was just completed. Structured as:

- **Section 1**: Why the document exists (agent onboarding, not history).
- **Section 2**: Ordered batch table with archive links (completed batches
  only have a row and a `docs/history/` link).
- **Section 3**: Active batch state. Enough detail for an agent to
  continue mid-batch without needing to re-read anything else, saving tokens.
- **Section 4**: Smal current execution log window. Dated entries for the active window only.
  Older entries rotate automatically into the archive.

The batch/work-package (WP) structure is designed to mimic a lightweight sprint system.

Each batch starts with a definition document at the repository root
(`BATCHN_DEFINITION.md`) that specifies acceptance criteria before work begins --
this is the "definition of done" that prevents scope creep mid-batch and gives
a later agent an unambiguous target. At close-out, the definition is archived
under `docs/history/definitions/`.

Agents write the narrative entry; `doc_state_sync.py` performs the
mechanical rotation, dedup, and status-block refresh. The behavioral rule
for what an agent must check before appending a new entry lives in
`AGENTS.md` ("Before writing to Section 4") -- this file only explains
why the split exists: see "`doc_state_sync.py`: Why a Script, Not a
Prompt" below.

### `.claude/SESSION_CONTEXT.md` -- Dashboard

A machine-managed snapshot: current test count, branch, known risks,
module structure, dependency graph, architecture overview. It is not
a rules file and not a history file. It exists so a new agent session can read
one file and understand the current runtime state without parsing PLAYBOOK.md
or running tests.

This file lives in `.claude/` and is committed to the repo (tracked via
an explicit `.gitignore` exception: `.claude/*` + `!.claude/SESSION_CONTEXT.md`).
It is the shared cross-agent dashboard -- all agents bootstrap from it.
A reference snapshot (showing what the file looks like) is kept at
`docs/history/SESSION_CONTEXT_REFERENCE.md` for readers curious about
the format.

**Why committed?** Because every agent used in development needs to start from an identical state. Leaving it uncommitted caused
drift: agents would start sessions with stale branch, test count, and batch
status.

Crucially, CI does not depend on it. If the file is absent, `doc_state_sync.py`
skips SESSION_CONTEXT operations gracefully via `_read_lines_optional()`.
The machine-managed `DOCSYNC:STATUS` block is a derived view (rebuilt from
PLAYBOOK truth by `--fix`), which means forgetting to update it manually
is self-correcting.

### `docs/history/` -- The Archive

Contains completed batch definitions, per-batch logs, audits, old changelogs, etc.
Once a batch is done, its definition moves here. Entries in PLAYBOOK Section 4 rotate
here automatically when the window overflows. Nothing is deleted -- the
archive exists because LLM agents benefit from being able to grep past
decisions without loading them into the active context.

The archive is organized into subdirectories:
- `docs/history/definitions/`: archived batch definition files (`BATCHN_DEFINITION.md`)
- `docs/history/logs/`: per-batch execution logs rotated from PLAYBOOK Section 4
- `docs/logarchive/`: auto-managed monolith archive for non-batch (side-task) entries

Other notable documents:
- `AUDIT_*.md` / `BUGFIX_*.md`: external review findings and responses

---

## `doc_state_sync.py`: Why a Script, Not a Prompt

The doc synchronization tool is the most non-obvious part of the
infrastructure. In sum, as of development, you cannot ask an LLM
to reliably rotate 50-line Markdown sections between files without
eventually introducing content corruption, duplicate entries, or broken
marker placement.

The problem surfaced during early PLAYBOOK maintenance: as Section 4
grew, agents would trim it differently each session -- sometimes removing
entries that should have been archived, sometimes duplicating content,
sometimes moving entries across the `<!-- DOCSYNC -->` boundary markers
in ways that broke the rotation policy. The markers themselves were
introduced to make the boundary explicit, but LLMs would occasionally
edit them out or misplace them.

`doc_state_sync.py` makes the rotation deterministic:

1. **Parses** Section 4 of PLAYBOOK.md into typed `Entry` dataclasses
   (date, title, content lines, SHA-256 fingerprint of the full block).
2. **Partitions** entries into current-batch (inside the DOCSYNC markers)
   and non-current (outside) buckets.
3. **Enforces** the keep policy: non-current entries beyond the configured
   keep limit are moved to the archive file, never deleted.
4. **Deduplicates** the archive by fingerprint -- the same entry content
   can never appear twice, even if an agent manually copied an entry.
5. **Rebuilds** the managed `<!-- DOCSYNC:STATUS-START/END -->` block in
   `SESSION_CONTEXT.md` from PLAYBOOK truth, so the two files are always
   consistent without manual editing.
6. **Cross-validates** test counts and stale header phrases across both
   files and prints warnings (non-blocking) for human review.

The script runs as a pre-commit hook (`doc-state-sync-check` in
`.pre-commit-config.yaml`) in `--check` mode. This means any commit that
leaves PLAYBOOK and SESSION_CONTEXT out of sync is rejected at the gate,
before it reaches CI.

**Package structure (Batch 14 refactor).** The script was originally a
monolithic 600-line file. Batch 14 decomposed it into a proper Python
package (`scripts/docsync/`) with separate modules for parsing (`parser.py`),
rendering (`renderer.py`), rotation/dedup logic (`logic.py`), the CLI
entrypoint (`cli.py`), and typed dataclass models (`models.py`); the root
`scripts/doc_state_sync.py` is now a thin wrapper that delegates into the
package. This made each concern independently testable -- 116 docsync tests
(across `tests/test_docsync_parser.py`, `tests/test_docsync_logic.py`,
`tests/test_docsync_renderer.py`, and `tests/test_docsync_cli.py`) now cover
rotation, dedup, cross-validation, and CLI modes.

That count has grown since the original Batch 14 refactor as later batches added edge-case coverage;
run `pytest tests/test_docsync_*.py -q` to confirm the current number rather
than trusting any figure quoted here, since it will drift as new tests are
added.

**SESSION_CONTEXT.md is optional in CI.**

The file is committed to the repo and is normally present in GitHub Actions (with a standard
`actions/checkout@v4` workspace). `doc_state_sync.py` still treats it as
optional via `_read_lines_optional()`: if the file is missing (for
example, in a sparse checkout or custom workflow), all operations that
depend on it are silently skipped. Tests still pass; the PLAYBOOK rotation
still occurs. See commit `05c7b19` on `main` for the original change.

---

## The Batch Structure as a Lightweight SDLC

The repository uses batches and work packages as a lightweight delivery model. It maps reasonably well to familiar software-process concepts:

| SDLC concept | ScrobbleScope equivalent |
|---|---|
| Sprint / milestone | Batch (e.g., Batch 7: Persistent metadata layer) |
| Definition of done | `docs/history/definitions/BATCHN_DEFINITION.md` acceptance criteria |
| Stand-up / status | SESSION_CONTEXT Section 1 (current state table) |
| CI gate | GitHub Actions Quality Gate |
| Code review | PR review plus automated review feedback |
| Release | `flyctl deploy` (manual, after PR merge to `main`) |

The key difference from a human SDLC is that the "team members" have
amnesia between sessions and cannot communicate with one another as of development. This forced an unusually rigorous documentation
discipline -- not because good documentation is a virtue in the abstract,
but because undocumented decisions would lead to a future agent/session
re-opening a solved problem or refactoring a prior agent's functioning code.

---

## How This Differs From Typical Agentic Coding / AIDD

As of development, most AI-driven-development (AIDD) workflows treat the agent's context
window, or at best a single running conversation/log, as the entire
memory of the project.

A prompt like "continue where you left off" or "here's the chat history" works fine within one session but does not
survive a tool switch (Claude Code to Copilot to Gemini CLI), a context
compaction, or a multi-day or week gap; exactly the conditions this project
runs under with five+ different agent tools. The typical failure mode in
that model is that state lives implicitly in conversation history: whoever
has the longest, most recent transcript "knows" the project, and anyone
else has to either read that transcript in full (token-expensive and lossy)
or start over.

ScrobbleScope's orchestration layer inverts that assumption: state is never
allowed to live only in a conversation. It is externalized into a small,
strictly-scoped set of files (`AGENTS.md`, `HANDOFF_PROMPT.md`,
`AGENT_NOTES.md`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, plus the
`docs/history/` archive) with each file assigned exactly one concern, so
that any agent -- regardless of vendor or context length -- can bootstrap
full working context from a fixed, small reading list rather than from
transcript archaeology. A few concrete departures from typical agentic
practice follow from this:

- **Deterministic tooling over prompted discipline for the parts that must
  never fail.** Section rotation, archive deduplication, and cross-file
  consistency checks are done by `doc_state_sync.py`, a plain Python script
  with its own comprehensive test suite, not by asking the agent to "keep the
  files tidy." Typical AIDD setups rely on the agent itself to remember and
  re-apply formatting/bookkeeping conventions every session; here rotation
  and archive drift are enforced by the `doc-state-sync-check` pre-commit
  hook, while cross-file consistency problems are reported as warnings for
  the agent to resolve.
- **A definition-of-done written before work starts, not inferred after.**
  Each batch's root `BATCHN_DEFINITION.md` is committed before its WPs begin,
  then moved under `docs/history/definitions/` at close-out, so an agent
  resuming mid-batch (or a human auditing it later) has an unambiguous target
  instead of having to reconstruct intent from commit messages or transcripts.
- **Automated review suggestions are logged and adjudicated, not
  auto-applied.** Section "On Rejecting Code Review Suggestions" below is
  the direct consequence: a review tool (or agent) that only sees the
  current diff, with no causal history, will sometimes recommend reverting
  a deliberate fix. Preserving the reasoning in `PLAYBOOK.md`/`docs/history/`
  means the next agent (or reviewer) doesn't repeat the same wrong
  suggestion, which a purely conversational workflow has no mechanism to
  prevent.
- **Cost is paid up front in documentation discipline, not deferred as
  cleanup.** A typical single-agent AIDD loop optimizes for shipping the
  current change quickly and treats documentation as optional follow-up.
  Because this project is designed for hand-offs between independent agent
  sessions with no shared memory, skipping the doc update is not a
  shortcut -- it directly causes the next session to redo or undo work.

---

## On Rejecting Code Review Suggestions

Not every review suggestion improves the codebase. Two patterns emerged:

**Pattern 1: Correct in isolation, wrong in context.**

An automated code review (Gemini Code Review, Batch 12 post-audit) flagged the
`getComputedStyle` call in `results.js` as potentially redundant.

In isolation, that is a reasonable observation. In context: the call existed
specifically to patch a dark-mode rendering issue with the `html2canvas`
JPEG export -- removing it causes the exported image to render with the
wrong background color in dark mode.

The reviewer had no access to the git history of that bug, the session logs where the fix was developed, or the test case that validated the behavior.

*Resolution:* the suggestion was rejected with a documented reason in the session log. The code was left unchanged.

**Pattern 2: Review tool vs. review context.**

Automated tools review code as a snapshot. They do not know:
- Which bugs were deliberately fixed with what appears to be a workawwwwwwwwwwwwwwwwwwwwwwround.
- Which "magic numbers" are environment-specific constants that cannot be
  parameterized without breaking the Fly.io deploy pipeline.
- Which test patterns look vacuous but exist as regression guards for a
  specific production failure.

The response to all of these was the same: the suggestion is logged,
evaluated against causal knowledge from the session history, and either
acted on or rejected with explicit reasoning preserved in PLAYBOOK Section
4 or `docs/history/`. This keeps the audit trail honest without accepting
every automated suggestion blindly.

---

## What Did Not Work Initially

A short list of things that failed before the current approach stabilized:

- **Single long context file**: early sessions used a single STATUS.md file
  that grew to ~400 lines. By mid-session it consumed most of the available
  context budget, leaving little room for code. The split into PLAYBOOK
  (detailed), SESSION_CONTEXT (summary), and archive (historical) solved this.
- **Unpinned agent instructions**: without AGENTS.md, agents would
  occasionally commit without running tests, use the wrong commit format,
  or write "Added X" instead of "Add X" in subject lines. Prescriptive rules
  in AGENTS.md made these reproducible.
- **Manual archive management**: before `doc_state_sync.py`, agents would
  sometimes trim Section 4 entries by hand in ways that introduced duplicate
  content or moved entries across the DOCSYNC boundary incorrectly. The
  pre-commit hook now catches this class of error before it lands.
- **Nested thread pattern** (Batch 3): the original background task spawned
  a thread that spawned another thread to run the asyncio event loop. This
  produced unpredictable behavior under load. Removed in Batch 3 after a
  dedicated batch definition was written with explicit acceptance criteria.

---

## How to Read the Orchestration Files

If you have cloned this repository and want to understand any decision:

1. Read the relevant `docs/history/definitions/BATCHN_DEFINITION.md` to see what the
   acceptance criteria were before work started.
2. Search `PLAYBOOK.md` Section 4 and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for dated entries
   covering the relevant date range.
3. Search `docs/history/logs/` and `docs/logarchive/` for older dated entries.
4. `AGENTS.md` explains how future development sessions should be started
   and what rules govern commits, tests, and documentation.

`.claude/SESSION_CONTEXT.md` is the current-state snapshot for an active
development session. It is committed and shared across all agents (tracked
via `.gitignore` exception). A reference copy of its format and structure
is at `docs/history/SESSION_CONTEXT_REFERENCE.md`.

In sum, bootstrapping agents with the template prompt and orienting them allows agents to be orienteded on where the project stands and the following task. Writing batch definitons with WPs is imperative for their orientation. While this method may consume tokens, it has provent to be an effective cross-session and cross-stae external memory managment tool. Every decision, deviation, and implementation is logged and detailed, and this allows anyone to understand the "why" behind changes.
