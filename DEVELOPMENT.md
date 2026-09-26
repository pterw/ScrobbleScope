# ScrobbleScope: Development Methodology

This document explains how ScrobbleScope was built: the orchestration
strategy, the tooling decisions, and the reasoning behind each one. It is
written for anyone who clones this repository and wants to understand why
the project is structured the way it is beyond what `AGENTS.md` prescribes.
It is explanatory documentation. Operational rules remain owned by
`AGENTS.md`, and nothing here overrides them. One section is an exception:
Frontend Asset Build owns the build and watch commands, and other documents
point to it for them.

---

## The Core Problem: Collaborating With Amnesiac Engineers

ScrobbleScope was built primarily by one developer working with several LLM coding agents -- some within VSCode and others externally -- across large gaps of time.

The bulk of the prototype-to-deployed-app work happened in a compressed
February-March sprint, with lighter follow-up work later. The project had
initially been abandoned after encountering a thundering-herd issue and a
large monolithic `app.py`. Rate-limiter changes addressed the herd behavior,
while the Batch 8 refactor replaced the monolith with Flask Blueprints and an
application factory. Additional coding agents were later integrated into the
IDE.

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

The external-memory layer consists of five core tracked files, the advisory
read-on-demand `docs/agents/FINDINGS.md`, and two archive directories. Each has a primary
concern, and the design goal is that canonical facts live in exactly one
place.

`docs/agents/HANDOFF_PROMPT.md` carries only what is unique to starting and ending a
session. It links to `AGENTS.md` for rules rather than summarising them:
earlier versions did condense the rules into a cold-start checklist, and
every summary eventually drifted from the text it summarised.

`docs/agents/AGENT_NOTES.md` cross-references `AGENTS.md` for venv rules rather than
restating them. `README.md` is excluded from the agent memory layer; it
exists for *people* to read and is explicitly not used for orchestration.

### `AGENTS.md` -- Rules

Written in imperative, rule-form language. Contains invariants that must
hold across all sessions and all agents: commit format, test quality
standards, what constitutes a side-task vs. batch work, how to bootstrap
a new session, how to run pre-commit and doc sync. It does not contain
current state, nor does it contain history. It is rarely subject to change.

The language is deliberately prescriptive ("Must", "Do not", "Forbidden")
because LLMs handle ambiguity poorly, and incorrect inference can lead to a broken pipeline or a mis-scoped commit.

### `docs/agents/HANDOFF_PROMPT.md` -- Session Start and Handoff

Given to any agent beginning work, and intended to be passed verbatim as
context when delegating to a new session. It holds the two things that
belong to no other file: verifying that repository reality matches what
the bootstrap documents claim (branch, recent commits, test count), and
the checklist for handing work to the next session.

The read order, validation gates, and commit discipline it once restated
now live only in `AGENTS.md`. Each restatement had drifted from the
canonical text -- in one case a copy silently outlived the rule it
described -- so the copies were replaced with pointers.

### `docs/agents/AGENT_NOTES.md` -- Owner Context

Tracks facts that belong to no other file: owner workflow preferences,
local dev setup (Docker, Postgres, Browser MCP), architectural
constraints discovered during development, and known open issues. Tracked
in git so every agent -- regardless of tool or machine -- reads the same
preferences.

### `docs/agents/PLAYBOOK.md` -- Work Orders

The source of truth for what work is in progress, what is next, and what
was just completed. Structured as:

- **Section 1**: Why the document exists (agent onboarding, not history).
- **Section 2**: Ordered batch table with archive links (completed batches
  only have a row and a `docs/history/` link).
- **Section 3**: Active batch state. Enough detail for an agent to
  continue mid-batch without needing to re-read anything else, saving tokens.
- **Section 4**: Small current execution-log window. Dated entries for the active window only.
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
one file and understand the current runtime state without parsing
`docs/agents/PLAYBOOK.md` or running tests.

This file lives in `.claude/` and is committed to the repo (tracked via
an explicit `.gitignore` exception: `.claude/*` + `!.claude/SESSION_CONTEXT.md`).
It is the shared cross-agent dashboard -- all agents bootstrap from it.
A reference snapshot (showing what the file looks like) is kept at
`docs/history/reports/SESSION_CONTEXT_REFERENCE.md` for readers curious about
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
- `docs/history/findings/`: resolved findings rotated out of `docs/agents/FINDINGS.md`
- `docs/history/reports/`: the dated one-off documents -- audits, changelogs,
  refactor plans, the worker ADR, and the SESSION_CONTEXT format snapshot
- `docs/logarchive/`: auto-managed monolith archive for non-batch (side-task) entries

The other subdirectories hold structured series that a tool or a documented
procedure writes into; `reports/` holds everything written once about one
topic. Its documents are point-in-time records and are
not revised to match later reorganisations, so paths cited *inside* them may
name a pre-2026-08-14 layout. `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
stays at the top level on purpose: it is a tombstone whose job is to resolve
references to that legacy path.

Other notable documents:
- `reports/AUDIT_*.md` / `reports/BUGFIX_*.md`: external review findings and responses

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

1. **Parses** Section 4 of `docs/agents/PLAYBOOK.md` into typed `Entry` dataclasses
   (date, title, content lines, SHA-256 fingerprint of the full block).
2. **Partitions** entries into current-batch (inside the DOCSYNC markers)
   and non-current (outside) buckets.
3. **Enforces** the keep policy: non-current entries beyond the configured
   keep limit are moved to the archive file, never deleted.
4. **Deduplicates** the archive by fingerprint -- the same entry content
   can never appear twice, even if an agent manually copied an entry.
5. **Rebuilds** the managed `<!-- DOCSYNC:STATUS-START/END -->` block in
   `SESSION_CONTEXT.md` from PLAYBOOK truth, so the two files are always
   consistent without manual editing. Which count wins is a rule, so it is
   owned by `AGENTS.md` ("Integrity diagnostics"); conflicting named
   dashboard, status, or test inventory counts are blocking integrity errors.
6. **Enforces** live-document integrity: dead concrete references, active
   definition metadata, archive prologue drift, and session contradictions
   produce stable blocking diagnostics. `--fix` first writes only
   deterministic output, then revalidates the final disk state; it does not
   guess at semantic repairs.

The script runs as a pre-commit hook (`doc-state-sync-check` in
`.pre-commit-config.yaml`) in `--check` mode, through
`scripts/dev/docsync_preflight.py --worktree`, which also refuses a commit
that stages the docsync control plane itself. This means any commit that
leaves deterministic drift or a proven live-document contradiction is rejected
at the gate, before it reaches CI.

**Package structure.** The script was originally a monolithic 600-line file.
Batch 14 decomposed it into a proper Python package (`scripts/docsync/`) with
separate modules for parsing (`parser.py`), rendering (`renderer.py`),
rotation/dedup logic (`logic.py`), live-document integrity (`integrity.py`),
the CLI entrypoint (`cli.py`), and typed dataclass models (`models.py`); the
root `scripts/doc_state_sync.py` is now a thin wrapper that delegates into the
package. This made each concern independently testable.

Batch 22 added six more modules, because the same discipline was extended to
the things a batch close-out has to get right: `declarations.py` (the
declared-duplicate and retired-claim checker, `[[value]]` / `[[anchor]]` /
`[[retired]]`, reading its facts from `config/docsync.toml` rather than
hard-coding them), `closeout.py` (the six close-out signals a managed batch must satisfy),
`archives.py` (bounded paginated archives), `findings.py` (finding lifecycle
and rotation), `transaction.py` (crash-safe publication), and `markdown.py`
(the shared fenced-block scanner that keeps a quoted example from parsing as
real content).

Twelve modules, and sixteen test files in `tests/`
(`test_docsync_archives.py`, `test_docsync_archive_split.py`,
`test_docsync_cli.py`, `test_docsync_closeout.py`,
`test_docsync_declarations.py`, `test_docsync_findings.py`,
`test_docsync_integrity.py`, `test_docsync_log_merging.py`,
`test_docsync_markdown.py`, `test_docsync_parser.py`,
`test_docsync_renderer.py`, `test_docsync_section3_parsing.py`,
`test_docsync_sync_integration.py`, `test_docsync_test_count.py`,
`test_docsync_transaction.py`, `test_docsync_wp_numbers.py`), plus
`tests/scripts/dev/test_docsync_preflight.py` and `test_docsync_hook.py` for
the two entry points that live under `scripts/dev/`. Run
`pytest tests/test_docsync_*.py -q` for the current measured count rather than
preserving a number here that will drift as edge-case coverage grows.

**Publication is crash-safe, and that is not incidental.** Reading PLAYBOOK
Section 4 and writing it back is a read-modify-write across several files, and
a half-finished write would leave the corpus in a state no later agent could
reason about: some entries rotated, others not, with the archive index
disagreeing with the pages beside it. So every mutating mode (`--fix`,
`--close-batch`, `--split-archive`, `--paginate-archives`, `--cold-storage`)
publishes through `scripts/docsync/transaction.py`:

1. An exclusive lock (`.docsync.lock`) makes the run single-writer.
2. Every file it read is proved still byte-identical to what it read, so a
   concurrent edit is a refusal rather than a silent clobber.
3. The before-image of every path is journalled (`.docsync.journal`) *before*
   the first write lands.
4. Each write goes to a same-directory staging file (`.docsync-stage`) and
   lands via `os.replace`, which is atomic on one filesystem.
5. A run killed between two writes leaves the journal behind; the next
   publication replays it against the on-disk state, or refuses if a
   journalled file matches neither the before-image nor the interrupted
   content. It never guesses which side of that disagreement is the history
   worth keeping.

The property this buys is narrower than "the tool is transactional" and it is
worth stating precisely: a crash can lose the whole run, but it cannot leave a
partially-published corpus. That is the guarantee the journal, the lock and the
staged rename exist to provide.

**Archives are bounded, and their ordering is deliberate.** `archives.py` caps
a page at 500 lines by default and paginates an archive that outgrows it into
numbered, immutable pages, keeping a flattened index so every page stays
searchable Markdown. Page `0001` holds the *oldest* content -- version 1
numbered pages in reading order, which put the newest entries on the oldest
page, and reversing that is what `4b36d6a` fixed. Cold migration never reads
the system clock: it happens only under an explicit `--cold-storage --as-of
<ISO date>`, because a check that aged files using today's date would make the
same commit produce different results on different days.

The full module-by-module treatment, the DOC diagnostic catalogue,
and the commit-preflight and hook-installer design live in
`docs/architecture/documentation-tooling.md`. That file is the owner; this
section is the methodology narrative around it and deliberately does not
restate the catalogue.

**The rotation is a mechanism because agents could not be trusted with it.**
This is the origin of the whole package, and it is worth recording in the
engineering terms rather than the motivational ones. Rotating a section between
two Markdown files is a read-modify-write over documents that must stay
byte-consistent with each other, and it was performed by hand three times. Each
attempt produced a distinct failure: an entry archived that should have stayed,
an entry duplicated across the boundary, and a stale remark left in place after
the text it described had moved. All three are silent -- the document still
renders, so nothing tells the reader it is now wrong.

The response was to stop asking for care and build the three pieces that make
the operation deterministic instead: a **parser** that reads the section into
typed entries, a **renderer** that emits the result, and **rotation** that
decides what moves. Those are the load-bearing parts of the package, and they
exist precisely because the task is one an LLM is not reliable at over many
sessions. The hooks and the diagnostics came later, once there was a mechanism
worth guarding.

**"ACID" is a shorthand here, not a claim.** The publication path is usually
described as ACID-like, and it is worth being exact about how far that carries,
because overclaiming it would be its own kind of stale remark:

- **Atomicity** is real. A publication commits or does not, via the staged
  rename, and a crash cannot leave a partially-written corpus.
- **Consistency** is real, and enforced by a declarative rules engine rather
  than by hand. The invariant checks are the C in the analogy.
- **Isolation** is partially accurate. The exclusive lock makes the run
  single-writer, but it is filesystem-, not database-, scoped: it does not
  coordinate across machines and does not serialise readers.
- **Durability** is accurate within filesystem semantics. The journal is on
  disk and survives the process, but it is not an fsync-per-write guarantee
  against power loss.

So the precise description is an **atomic file-transaction and invariant
enforcement system**: atomic batch publishing, strict mechanistic invariant
checking, exclusive write locks, and persistent on-disk recovery state, instead
of uncoordinated script overwrites. The acronym is useful because it
communicates the design intent in one word to a reader who already knows what
those properties cost; it stops being useful the moment it is read as a
database guarantee.

**What else the package carries.** Three pieces are what turn the mechanism
into a workflow, and all three were built in the docsync close-out work:

- **The commit preflight** (`scripts/dev/docsync_preflight.py`). It validates
  the *commit candidate* rather than the working tree, so a commit cannot carry
  a broken document set past the gate, and it is deliberately the first hook in
  `.pre-commit-config.yaml` so nothing downstream can rewrite the files it just
  validated.
- **The hook installer** (`scripts/dev/install_docsync_hook.py`). Docsync has
  to run before any other hook can touch a candidate, which pre-commit's own
  dispatch does not give you; the installer generates a wrapper that enforces
  the ordering and refuses to overwrite a hook it did not write. It is
  **opt-in and not installed in this repository** -- running it for real is an
  owner action.
- **The CLI surface** (`scripts/doc_state_sync.py`). `--check` and `--fix` are
  the daily pair; `--close-batch`, `--split-archive`, `--paginate-archives` and
  `--cold-storage --as-of` are the maintenance modes, each of which publishes
  through the transaction above.

**SESSION_CONTEXT.md is optional in CI.**

The file is committed to the repo and is normally present in GitHub Actions (with a standard
`actions/checkout@v4` workspace). `doc_state_sync.py` still treats it as
optional via `_read_lines_optional()`: if the file is missing (for
example, in a sparse checkout or custom workflow), all operations that
depend on it are silently skipped. Tests still pass; the PLAYBOOK rotation
still occurs. See commit `05c7b19` on `main` for the original change.

### Worktrees, rebase merges, and branch lineage

ScrobbleScope uses linked Git worktrees so a long-running batch can remain
isolated from the owner's main checkout. A linked worktree has its own checked
out branch and working directory, but it shares the repository's object store
and other common Git data. Updating `main` therefore does not move the batch
branch automatically.

That distinction matters after a GitHub rebase merge. GitHub recreates the
source commits on `main` with new commit identities, while the source branch
continues to point at the pre-merge commits. Git can then report the branch as
both ahead and behind even when its tree is byte-identical to `main`. This
happened after PRs #163, #165, and #168. On two of those cycles, the stale
branch contributed to a phantom or reverse-direction follow-up PR.

Ignored local state is separate too. The repository's sole `.venv` normally
lives in the primary checkout and is not copied into linked worktrees. A
fresh shell in a linked worktree therefore cannot rely on bare `pytest` or a
relative `.venv` path, which is why `AGENTS.md` directs those commands at the
qualified executable from the primary checkout. A second environment inside
the worktree would reintroduce the package-version drift that policy exists
to prevent.

That creates a deliberate bootstrap asymmetry. The guard must run before the
primary checkout paths are known, so the canonical AGENTS procedure permits
system Python only for that first, standard-library-only launch. The paths it
reports then identify the existing environment used for later Python, pytest,
and pre-commit commands. This paragraph explains the design; operational
authority remains exclusively in `AGENTS.md`.

The safe diagnosis compares both commit ancestry and tree identity. A clean,
content-identical divergence is normally a rebase-merge artifact; a divergence
with different trees is real work and must not receive the same reset remedy.
Realignment is intentionally never automatic because resetting and
force-pushing rewrite branch history and require explicit owner approval.

The shipped remediation keeps two safeguards separate. Deterministic drift
inside live operational documents is a blocking extension of
`doc_state_sync.py`, which runs locally and in CI. The read-only worktree
alignment guard handles local bootstrap and post-rebase checks, and reports
the allowed shared virtualenv path without creating or modifying an
environment. It is not a CI topology gate: detached recognized CI reports an
explicit skip, while the existing test workflow exercises the guard's state
decisions. The detailed design lives in
`docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
Operational behavior is owned by `AGENTS.md` and the guard itself --
`scripts/dev/check_worktree_alignment.py` is the CLI entry point, and the
checks live across `scripts/dev/_worktree_guard_*.py` (inspection, lineage,
diagnostics, runner, venv, types) behind the `scripts/dev/worktree_guard.py`
facade. Each `WT000`-`WT014` code names its own remediation. This section is
human methodology documentation only.

---

## Frontend Asset Build

Batch 21 migrated the interface to the Tailwind CSS standalone CLI and daisyUI
bundles without a Node project; that migration is complete. The source of truth
is `static/css/tailwind.src.css`; production
serves the committed `static/css/tailwind.css`, so app startup never downloads
or compiles frontend tooling.

One-shot build, required before committing a source or template change:

```bash
python scripts/dev/tailwind_build.py
```

Watch during local UI work:

```bash
python scripts/dev/tailwind_build.py --watch
```

The script selects the pinned executable for the host and stores it with
`daisyui.mjs` and `daisyui-theme.mjs` under gitignored `scripts/bin/`. It
verifies all three files against their pinned SHA-256 values on every run. A
missing or invalid file is fetched once and verified before atomic replacement;
an invalid replacement stops the build.

These commands are written in primary-checkout form. In a linked worktree, run
them with the qualified Python path printed by
`scripts/dev/check_worktree_alignment.py`, as required by `AGENTS.md`. Run the
one-shot command after stopping watch mode and commit both source and generated
CSS. CI runs the same one-shot path on Linux and rejects generated-file drift.

---

## Frontend Browser Gate

`python scripts/dev/results_behavior_tests.py` runs six isolated Chromium
tests against the production Results scripts, using a controlled clock and
no Flask server or external services. They cover Spotlight rotation and late
hydration, reduced motion, leaderboard state, and tooltip timing and keyboard
access. These browser tests run in CI after browser installation and before
the full-page gate; they are separate from the Python `pytest` test count.
Sampling itself lives in `scrobblescope/spotlight.py` and is covered by the
Results route regression in `tests/test_routes.py`.

Run `python -m playwright install chromium firefox` once after installing the
pinned development requirements, then `python scripts/dev/frontend_gate.py`.
Use the qualified primary-checkout Python path in a linked worktree. The gate
starts and stops its own loopback Flask server. Chromium runs the complete
matrix; Firefox runs the static-assets and theme-token canary. UI changes
also receive focused Firefox checks and owner visual review. `--headed`
shows the diagnostic browser windows.

**What makes it a gate rather than a screenshot run.** Three properties are
worth naming, because each closes a way a visual check can pass while the page
is wrong:

- **It serves the real application, on a port it owns.** The gate binds
  `127.0.0.1` on port `0`, so the OS assigns an ephemeral port, and shuts the
  server down in a `finally`. No separately running app is required, and two
  concurrent runs cannot collide on a fixed port.
- **It asserts computed values, not class names.** A probe checking a
  `className` passes against a stylesheet that was never applied, so checks read
  `getComputedStyle` and real geometry instead. The colour maths lives in
  `_frontend_gate_colour.py` as pure functions with no page attached: WCAG
  relative luminance and alpha-composited contrast, used to prove a translucent
  divider token still clears 3:1 against *every* surface it can sit on rather
  than the one it happened to be sampled over.
- **It measures the interface at the sizes a reader actually uses.** Viewport
  profiles cover mobile, 1080p, 1440p and 4K, plus a wide screen with a coarse
  pointer -- because width alone does not imply a mouse: a tablet in landscape
  and a touch laptop are both wide and both touched. Touch targets on
  coarse-pointer profiles must measure at least 44px on their smaller side, and
  desktop composition has to reach its proportions through layout rather than a
  CSS `zoom` or `transform`, which would satisfy a pixel check while breaking
  the type scale.

Stylesheet isolation is asserted per page -- exactly one framework stylesheet,
because daisyUI, Tailwind v4 and a legacy Bootstrap file all claim `.btn`,
`.card` and `.modal`, and loading two would let one silently win.
CI runs the browser gate after installing both browsers. `docs/agents/ui-accessibility.md`
owns the unit, touch-target, motion and keyboard rules the checks enforce.

---

## This Repository Is Also a Template Being Extracted

**Owner intent, stated 2026-08-25.** The long-term goal is to lift this
workflow out of ScrobbleScope and reuse it when building any application -- at
least any data-visualisation or full-stack one. That is *why* the tooling is
larger than the application it checks, and why the hardening has been
progressive rather than a one-off: `scripts/docsync/`, the worktree guard,
the frontend gate, `AGENTS.md`, the PLAYBOOK and FINDINGS discipline, and the
batch and work-package structure are all intended to leave with the template.

So the repository has three separable systems, and it is worth being precise
about what each one is, because they are at very different levels of maturity
and the difference matters to anyone planning to lift them.

**1. The documentation control plane (`scripts/docsync/`).** The most portable
of the three, and the closest to finished. Its integrity checks are generic
apart from the document names in `LIVE_DOCUMENT_RELATIVE_PATHS`, and its facts live in
`config/docsync.toml` rather than in the code -- `declarations.py` carries no
ScrobbleScope value at all. It publishes atomically, diagnoses with typed codes
and a remediation, and runs from a pre-commit hook and from CI.

**2. The worktree guard (`scripts/dev/_worktree_guard_*.py`).** Structurally
complete: a public facade (`worktree_guard.py`), a thin CLI entry point, and
the checks spread across six modules by concern -- inspection, lineage,
diagnostics, runner, venv, types. It reports `WT000`-`WT014`, each code naming
its own remediation. It runs as an advisory pre-commit hook rather than a gate,
and deliberately so: `WT003` fires for any branch the active batch does not
name and `WT004` for the identical-tree divergence a rebase merge always
leaves, so gating on it would refuse every commit on a feature branch.

**3. The frontend gate (`scripts/dev/frontend_gate.py`).** Generic in
structure -- serve the app, drive a browser, run checks per device profile --
and specific in its checks, which is the right split and the part that stays
behind. The decomposition split (F-B21-51) has landed: the facade stays
under the decomposition plan's 700-line threshold
(`docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md`), and the
checks are grouped by concern across ten `_frontend_gate_*` siblings --
eight own a concern (`_frontend_gate_assets`, `_frontend_gate_forms`,
`_frontend_gate_layout`, `_frontend_gate_pipeline`, `_frontend_gate_results`,
`_frontend_gate_runtime`, `_frontend_gate_theme`, `_frontend_gate_unmatched`),
one holds pure colour maths (`_frontend_gate_colour`), and one holds shared
state rather than a concern of its own (`_frontend_gate_shared`, the page
inventories and other objects several slices read). The
`frontend_gate_checks.toml` registry F-B21-51 proposed has also landed
(foundation plan Task 8): a manifest under `config/`
(`config/frontend_gate_checks.toml`) selects which of `CHECKS`
run, by name, refusing an unknown name or a disabled required check before
a browser launches.

Two things that are *not* portable and should not try to be: the design system
under `docs/design/`, and every path constant that names a ScrobbleScope file.

**`config/docsync.toml` was written for extraction, and it is the clearest example of
how far that has gone and how far it has not.** The file exists as a separate
declaration layer specifically so a second repository can supply its own
without touching the mechanism: the checks read what to verify from it rather
than knowing it. That split is real and it works -- `declarations.py` contains
no ScrobbleScope value at all, which is what makes the module liftable.

What remains tied is the *content* of those declarations, and it is worth
enumerating rather than summarising, because "still has semantic ties" is easy
to say and hard to act on:

| Tie | Where | Why it is repository-specific |
|---|---|---|
| Document paths | `[[value.sites]]` and `[[anchor]]` entries | They name `docs/design/README.md`, `docs/design/RECONCILIATION.md`, `docs/history/definitions/BATCH21_DEFINITION.md`, `docs/architecture/documentation-tooling.md`, `docs/agents/ui-accessibility.md` |
| Scanned corpus | `scan = ["*.md", "docs/**/*.md", ".claude/SESSION_CONTEXT.md"]` and its `allow_files` list | The document inventory a repository has is a policy choice, not a universal |
| Section anchors | `[retired.allow_after] "docs/agents/PLAYBOOK.md" = "## 4. Execution log (for agent handoff)"` | PLAYBOOK and its section names are this workflow's vocabulary |
| Batch vocabulary | `[closeout] admit_from_batch = 22` | Batching is the portable idea; *which* batch is the local fact |
| Design tokens | the `[[value]]` entries for the page background and muted text | These are ScrobbleScope's visual system, and one of them straddles source CSS, a legacy shell bridge and exact tests |
| Live-document list | `LIVE_DOCUMENT_RELATIVE_PATHS` in `integrity.py` | The module's own remaining repository knowledge; the short list AGENT_NOTES names as the last thing to move |

The pattern is consistent: **the mechanism is generic and the facts are
local**, which is the intended end state. The unfinished half is that those
local facts currently live *inside this repository's config* rather than in a
config a second repository would write for itself. That is what the deferred
kernel plan addresses, and it is why the plan's constraint is that the new
kernel modules "must not contain `ScrobbleScope`, `docs/agents/PLAYBOOK.md`, `Batch`, `WP`,
or `docs/superpowers/` policy literals".

**Why this is deliberately unfinished.** Two reasons, both of which are
engineering rather than scheduling. First, some of it is *not* extractable
without loss: `config/docsync.toml`, the design system and the path constants encode
this repository's own rules, and the honest description of a control plane for
a repository is that it must know which documents that repository owns. Forcing
genericity before there is a second consumer produces configuration indirection
with no second consumer to justify it. Second, the parts still worth
simplifying -- `integrity.py`, `declarations.py`, `cli.py` -- are the largest
modules in the package, and restructuring them while Batch 22's checks are
still settling would trade a working control plane for a tidier unfinished one.
The plan says so itself: "Refactor by responsibility, not line count."

What is *not* deferred is the constraint on new work, and that one binds every
commit: write new checks so they read their facts from the declarations layer,
name an assumption and make it switchable instead of letting it harden into
doctrine, prefer the standard library, and fail with a path, a line and a
remediation. The extraction stays cheap because nothing new makes it worse.

**The standing constraint until the extraction is scheduled.** It is a batch of
its own and has not been scheduled, so it must not be started as a side task.
What binds in the meantime is narrower and more useful: write new tooling so
the extraction stays cheap -- keep repository facts in the declarations file
rather than in the mechanism, name an assumption and make it switchable rather
than letting it harden into doctrine, prefer the standard library so the next
repository does not have to agree to a new dependency, and fail with a path, a
line and a remediation, because the reader will not be the person who wrote
the check.

The two extraction plans and their current status are
`docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
(the docsync kernel) and
`docs/superpowers/plans/2026-09-12-reusable-frontend-ci-verification-components.md`
(the gate components). Both carry explicit "do not execute until" conditions;
neither is current work. Owner intent and the reasoning behind the constraint
are owned by `docs/agents/AGENT_NOTES.md`, which is the authority if this section and that
one ever disagree.

---
## Claude Code Skills (tightly scoped tooling)

Two project-scoped Claude Code (CC) skills provide structured entry points for
common tasks. They are CC-specific; the portable, model-agnostic orchestration
rules live in `AGENTS.md`. The skill definitions themselves are maintained
locally and are not tracked in this repository (`.gitignore` excludes `.claude/`
except `SESSION_CONTEXT.md`); this section documents their purpose for context.

**`scrobblescope-bootstrap`** runs the canonical session bootstrap in a fixed
read order: `AGENTS.md`, then `docs/agents/PLAYBOOK.md` Sections 3-4, the active batch
definition named there, `.claude/SESSION_CONTEXT.md` Sections 1-2, and
`docs/agents/AGENT_NOTES.md`, finishing with a git-state and test-baseline check against
what those files claim. If PLAYBOOK Section 3 and SESSION_CONTEXT Section 1
agree on the current batch and next work package, the agent has enough
context to start. Invoke it at the start of any
substantive session -- new feature work, refactors, or multi-WP batch work.
Skip it when the change is too small to require batch context; the skill
illustrates this with the anti-example "tweak the heatmap pill padding," a
change that needs only the relevant template file, not the full bootstrap chain.

**`pr-bot-triage`** solves the problem of prioritising an incoming batch of
PR review comments before acting on them. It reads each comment and classifies
it as Act (address now -- actionable and in scope), Defer (valid but out of
scope for this session or batch), or Decline (not warranted -- incorrect,
already addressed, or rejected by the PR author). The classification standard
lives in the skill definition itself, keeping CC-specific workflow detail out of
`AGENTS.md`.

Both skills are deliberately scoped to a single agent at a time and are not
designed for parallel sub-agent invocation.

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
compaction, or a multi-day or multi-week gap -- exactly the conditions this project
runs under with five+ different agent tools. The typical failure mode in
that model is that state lives implicitly in conversation history: whoever
has the longest, most recent transcript "knows" the project, and anyone
else has to either read that transcript in full (token-expensive and lossy)
or start over.

ScrobbleScope's orchestration layer inverts that assumption: state is never
allowed to live only in a conversation. It is externalized into a small,
strictly-scoped set of files (`AGENTS.md`, `docs/agents/HANDOFF_PROMPT.md`,
`docs/agents/AGENT_NOTES.md`, `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, plus the
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
  hook. Proven live-document integrity defects are blocking errors; expected
  active-root notices remain warnings.
- **A definition-of-done written before work starts, not inferred after.**
  Each batch's root `BATCHN_DEFINITION.md` is committed before its WPs begin,
  then moved under `docs/history/definitions/` at close-out, so an agent
  resuming mid-batch (or a human auditing it later) has an unambiguous target
  instead of having to reconstruct intent from commit messages or transcripts.
- **Automated review suggestions are logged and adjudicated, not
  auto-applied.** Section "On Rejecting Code Review Suggestions" below is
  the direct consequence: a review tool (or agent) that only sees the
  current diff, with no causal history, will sometimes recommend reverting
  a deliberate fix. Preserving the reasoning in `docs/agents/PLAYBOOK.md`/`docs/history/`
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

Not every review suggestion improves the codebase:

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
  produced unpredictable behavior under load. Removed in Batch 3.

---

## How to Read the Orchestration Files

If you have cloned this repository and want to understand any decision:

1. Read the relevant `docs/history/definitions/BATCHN_DEFINITION.md` to see what the
   acceptance criteria were before work started.
2. Search `docs/agents/PLAYBOOK.md` Section 4 and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for dated entries
   covering the relevant date range.
3. Search `docs/history/logs/` and `docs/logarchive/` for older dated entries.
4. `AGENTS.md` explains how future development sessions should be started
   and what rules govern commits, tests, and documentation.

`.claude/SESSION_CONTEXT.md` is the current-state snapshot for an active
development session. It is committed and shared across all agents (tracked
via `.gitignore` exception). A reference copy of its format and structure
is at `docs/history/reports/SESSION_CONTEXT_REFERENCE.md`.

In sum, bootstrapping agents with the template prompt and repository documents gives each session the current project state and next task. Batch definitions and WPs provide the necessary orientation. Although this method consumes tokens, it has proven effective as a cross-session and cross-agent external-memory system. Logging decisions, deviations, and implementations preserves the reasons behind changes.
