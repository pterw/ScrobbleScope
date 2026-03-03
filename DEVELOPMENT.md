# ScrobbleScope: Development Methodology

This document explains how ScrobbleScope was built -- the orchestration
strategy, the tooling decisions, and the reasoning behind each one. It is
written for anyone who clones this repository and wants to understand why
the project is structured the way it is beyond what `AGENTS.md` prescribes.

---

## The Core Problem: Collaborating With Amnesiac Engineers

ScrobbleScope was built primarily by a single developer using multiple LLM
code agents (Claude Sonnet and Claude Opus via VS Code Copilo + Claude Code, Gemini Code Review via GitHub PRs, GPT-5.3 Codex) as the development team. The project went from a fragile prototype to a deployed, tested, multi-module application in roughly 7--10
days of active development.

The central challenge is that LLMs have finite context windows and no
persistent memory. Every session starts from zero. A model that produced
a clean architectural refactor yesterday has no idea it did so today. Left
unmanaged, this produces:

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

Five files constitute the external-memory layer. Each owns exactly one
concern; no fact is duplicated across them.

### `AGENTS.md` -- Rules

Written in imperative, rule-form language. Contains invariants that must
hold across all sessions and all agents: commit format, test quality
standards, what constitutes a side-task vs. batch work, how to bootstrap
a new session, how to run pre-commit and doc sync. It does not contain
current state; it does not contain history. It changes rarely.

The language is deliberately prescriptive ("Must", "Do not", "Forbidden")
because LLMs handle ambiguity poorly when the cost of a wrong inference
is a broken pipeline or a mis-scoped commit.

### `PLAYBOOK.md` -- Work Orders

The source of truth for what work is in progress, what is next, and what
was just completed. Structured as:

- **Section 1**: Why the document exists (agent onboarding, not history).
- **Section 2**: Ordered batch table with archive links (completed batches
  only have a row and a `docs/history/` link -- no content).
- **Section 3**: Active batch state. Enough detail for an agent to
  continue mid-batch without needing to re-read anything else.
- **Section 4**: Execution log. Dated entries for the active window only.
  Older entries rotate automatically into the archive.

The batch/work-package (WP) structure is a lightweight sprint system.
Each batch has a definition document (`docs/history/BATCHN_DEFINITION.md`)
that specifies acceptance criteria before work begins -- this is the
"definition of done" that prevents scope creep mid-batch and gives a
later agent an unambiguous target.

### `.claude/SESSION_CONTEXT.md` -- Dashboard

A machine-managed snapshot: current test count, branch, known risks,
module structure, dependency graph, architecture overview. It is not
a rules file and not a history file. It exists so a new agent session
can read one file and understand the current runtime state without
parsing PLAYBOOK.md or running tests.

This file lives in `.claude/` and is committed to the repo (tracked via
an explicit `.gitignore` exception: `.claude/*` + `!.claude/SESSION_CONTEXT.md`).
It is the shared cross-agent dashboard -- all agents bootstrap from it.
A reference snapshot (showing what the file looks like) is kept at
`docs/history/SESSION_CONTEXT_REFERENCE.md` for readers curious about
the format.

**Why committed?** Because every agent (Copilot, Claude Code, Gemini CLI,
Codex) needs to start from identical state. Leaving it uncommitted caused
drift: agents would start sessions with stale branch, test count, and batch
status. CI does not depend on it -- if the file is absent, `doc_state_sync.py`
skips SESSION_CONTEXT operations gracefully via `_read_lines_optional()`.
The machine-managed `DOCSYNC:STATUS` block is a derived view (rebuilt from
PLAYBOOK truth by `--fix`), which means forgetting to update it manually
is self-correcting.

### `docs/history/` -- The Archive

Completed batch definitions, audit reports, changelogs, ADRs. Once a batch
is done, its definition moves here. Entries in PLAYBOOK Section 4 rotate
here automatically when the window overflows. Nothing is deleted -- the
archive exists because LLM agents benefit from being able to grep past
decisions without loading them into the active context.

Specific documents worth noting:
- `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`: auto-managed rotated execution log
- `BATCHN_DEFINITION.md`: acceptance criteria written before work started
- `AUDIT_*.md` / `BUGFIX_*.md`: external review findings and responses

---

## `doc_state_sync.py`: Why a Script, Not a Prompt

The doc synchronization tool is the most non-obvious part of the
infrastructure. The short answer for why it exists: you cannot ask an LLM
to reliably rotate 50-line Markdown sections between files without
eventually introducing content corruption, duplicate entries, or broken
marker placement. The long answer follows.

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

**SESSION_CONTEXT.md is optional in CI.** The file is gitignored and
absent in GitHub Actions. `doc_state_sync.py` handles this gracefully
via `_read_lines_optional()`: if the file is missing, all operations that
depend on it are silently skipped. Tests still pass; the PLAYBOOK rotation
still occurs. See commit `05c7b19` on `main` for the fix.

---

## The Batch Structure as a Lightweight SDLC

Looking back, the batch system maps onto a conventional software process:

| SDLC concept | ScrobbleScope equivalent |
|---|---|
| Sprint / milestone | Batch (e.g., Batch 7: Persistent metadata layer) |
| Definition of done | `docs/history/BATCHN_DEFINITION.md` acceptance criteria |
| Stand-up / status | SESSION_CONTEXT Section 2 (current state table) |
| Retrospective / ADR | `docs/history/AUDIT_*.md`, `BUGFIX_*.md` |
| CI gate | GitHub Actions: pre-commit + flake8 + pytest + coverage |
| Code review | Gemini (automated, on PR) + manual review of suggestions |
| Release | `flyctl deploy` (manual, after PR merge to `main`) |

The key difference from a human SDLC is that the "team members" have
amnesia between sessions. This forced an unusually rigorous documentation
discipline -- not because good documentation is a virtue in the abstract,
but because the cost of an undocumented decision was a future agent
re-opening a solved problem.

---

## On Rejecting Code Review Suggestions

Not every review suggestion improves the codebase. Two patterns emerged:

**Pattern 1: Correct in isolation, wrong in context.**

An automated code review (Gemini, Batch 12 post-audit) flagged the
`getComputedStyle` call in `results.js` as potentially redundant. In
isolation, that is a reasonable observation. In context: the call existed
specifically to patch a dark-mode rendering issue with the `html2canvas`
JPEG export -- removing it causes the exported image to render with the
wrong background color in dark mode. The reviewer had no access to the
git history of that bug, the session logs where the fix was developed, or
the test case that validated the behavior.

Resolution: the suggestion was rejected with a documented reason in the
session log. The code was left unchanged.

**Pattern 2: Review tool vs. review context.**

Automated tools review code as a snapshot. They do not know:
- Which bugs were deliberately fixed with what appears to be a workaround.
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

1. Read the relevant `docs/history/BATCHN_DEFINITION.md` to see what the
   acceptance criteria were before work started.
2. Search `PLAYBOOK.md` Section 4 and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for dated entries
   covering the relevant date range.
3. Check `docs/history/AUDIT_*.md` for any third-party review findings
   that influenced the current structure.
4. `AGENTS.md` explains how future development sessions should be started
   and what rules govern commits, tests, and documentation.

`.claude/SESSION_CONTEXT.md` is the current-state snapshot for an active
development session. It is gitignored but a reference copy of its format
and structure is at `docs/history/SESSION_CONTEXT_REFERENCE.md`.
