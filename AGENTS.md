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
| `docs/agents/HANDOFF_PROMPT.md` | **Session-start procedure** | Post-read verification steps and the end-of-session handoff checklist. Rules (bootstrap order, gates, commit discipline) live in `AGENTS.md`. |
| `docs/agents/AGENT_NOTES.md` | **Owner context** | Owner preferences, local dev setup, architectural constraints, known issues. |
| `.claude/SESSION_CONTEXT.md` | **Dashboard** | Current project state snapshot. No rules, no history. |
| `docs/agents/PLAYBOOK.md` | **Work order** | What to do next, what was just done. Active batch + execution log. |
| `docs/agents/global-rules.md` | **Architectural invariants** | The global business logic rules every code change must hold: single source of truth, SoC/SRP, the rule-of-three duplication buffer, the anti-corruption layer, KISS, network defence, and deterministic diagnostics. Binding, and each rule states how it is checked. |
| `README.md` | **Product docs** | User/developer setup and context. Not for agent orchestration. |
| `docs/history/` | **Archive** | Completed batch definitions (`definitions/`), per-batch execution logs (`logs/`), audits and other dated one-off documents (`reports/`). |
| `docs/AGENT_DOC_MAP.md` | **Orientation** | Which document owns what, how to read an audit or a finding, and the known navigation traps. Optional, and not part of the bootstrap set; written for agents new to this repository. |
| `docs/architecture/documentation-tooling.md` | **Control plane** | How docsync, the commit preflight, the hook installer, the worktree guard, pre-commit, and CI fit together, including the full DOC diagnostic catalogue. Optional and not part of the bootstrap set; read it when a gate fails in a way `AGENTS.md`'s own instructions don't explain, or before changing `scripts/docsync/`, `scripts/dev/docsync_preflight.py`, `scripts/dev/install_docsync_hook.py`, `scripts/dev/_worktree_guard_*`, or `frontend_gate.py`'s own structure. |

**Anti-duplication rule:** Each fact lives in exactly one file. If you need to
reference a fact owned by another file, link to it -- do not copy it.

---

## Agent skills

### Issue tracker

Issues are findings in `docs/agents/FINDINGS.md`, rotating to
`docs/history/findings/FINDINGS_ARCHIVE.md`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context. Domain documentation is the existing document set named in
"Document Roles (SoC contract)" above, not a separate top-level context
document. See `docs/agents/domain.md`.

### UI and accessibility

Units, touch targets, keyboard access, motion and computed-style rules for
templates and static assets. See `docs/agents/ui-accessibility.md`.

### Global rules

The binding architectural invariants every code change must hold. See
`docs/agents/global-rules.md`.

---

## Session Bootstrap (in order)

1. `AGENTS.md` (this file) -- rules, commit format, doc sync policy,
   anti-patterns.
2. `docs/agents/global-rules.md` -- the binding architectural invariants
   every code change must hold, and which rule wins when two conflict.
3. `docs/agents/PLAYBOOK.md` Section 3 (next action) + Section 4 (current-batch log).
4. The batch definition file named in Section 3 (repo root while active;
   under `docs/history/definitions/` once the batch is closed; between
   batches no file exists -- skip this step).
5. `.claude/SESSION_CONTEXT.md` -- current batch, test count, architecture, risks.
6. `docs/agents/AGENT_NOTES.md` -- owner preferences, local dev setup, constraints.
7. Relevant `docs/history/` doc only if the log references one.
8. `docs/agents/FINDINGS.md` -- read on demand only: your task names an F-* ID, you are
   about to raise a defect, or you are reviewing a diff. Raise a known
   defect again only with new evidence. Not mirrored to GitHub: the
   `finding` issues are a frozen 2026-08-22 snapshot. Not part of the bootstrap set.

**Fast-path for Copilot comment jobs:** With no direct review-comment link,
fetch comments first and check for actionable new `@copilot` comments --
stop immediately if none. A single actionable comment scoped to a known
file/section needs only that file plus directly related test/config files.
Actionable means a concrete request, question, or correction addressed to
`@copilot`; praise, status updates, and rejected suggestions are not.

**Fast-path for targeted review-comment jobs:** For a single review comment
or `discussion_r...` URL: fetch that thread first, work from the linked
file/lines, and read only the minimum bootstrap/context files needed. Open
batch definitions or history docs only if the comment depends on them.

This is the single canonical bootstrap order (`docs/agents/HANDOFF_PROMPT.md` adds only
post-read verification and the edge cases below). Bootstrap is complete when
the sources agree: during an active batch, PLAYBOOK Section 3, the batch
definition, and SESSION_CONTEXT Section 1 agree on the current batch and
next WP; between batches, PLAYBOOK Section 3 and SESSION_CONTEXT Section 1
agree the last batch is closed and none is open. If two bootstrap files
conflict, follow the stricter safety rule and pause only if the conflict
affects the next action.
When network access is available, run `git fetch --prune origin` then
`python scripts/dev/check_worktree_alignment.py`; offline, add `--offline`
and treat its base result as local-ref-only. Stop on a nonzero exit and
follow the guard's remediation (it is read-only) and the owner-authorization
rule before any history rewrite; add `--debug` only to diagnose the guard
itself. See `docs/agents/HANDOFF_PROMPT.md` "Bootstrap edge cases" for the
expected-not-a-fault states, the WT004 remediation, the stdlib-only
exception, and the command-conversion rule.

**Token discipline for bootstrap:**
- Always read Sections 1-2 of `.claude/SESSION_CONTEXT.md`; later sections only if structure, dependency, architecture, test-inventory, or environment detail is needed.
- Read only Sections 3-4 of `docs/agents/PLAYBOOK.md` by default.
- Open archive files only when Section 4 links to one for the task at hand.
- Do not paste long historical logs into prompts; link files instead.
- When citing repository files in chat, use full filesystem paths. For tool
  inputs, follow the tool's required path format (absolute or repository-relative).

---

## Environment Setup

The only virtualenv is `.venv/` in the primary checkout. Never use `venv/`,
bare `pip`, or `python -m pip` without the qualified path -- a linked
worktree reuses the primary checkout's `.venv` and never creates a second
one; after the bootstrap guard succeeds, use its qualified Python, pytest,
and pre-commit paths for every later command there.

```bash
# Windows:  .venv\Scripts\activate            .venv\Scripts\pip install -r requirements-dev.txt
# Linux:    source .venv/bin/activate         .venv/bin/pip install -r requirements-dev.txt
```

All packages in `requirements.txt`/`requirements-dev.txt` are pinned with
`==`; propose a new one to the owner and wait for approval (Copilot task
sessions too) before installing it. **CI exception:** local-development
only -- a CI runner manages its own Python and bare `pip install` is
correct there.

API keys live in `.env` (git-ignored; template `.env.example`). Required:
`LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SECRET_KEY`
(min 16 chars; startup refuses weak values in production). Optional:
`DATABASE_URL` (Postgres cache) -- see `docs/agents/AGENT_NOTES.md` Local Dev Setup for
the connection string, the Docker container, the `init_db.py` caveat, and
`dev_start.py`.

---

## Pre-Work Checklist

1. The worktree guard in Session Bootstrap exits 0.
2. `pytest -q` passes (baseline count is in SESSION_CONTEXT Section 1).
3. `pre-commit run --all-files` passes.
4. The work you are implementing matches PLAYBOOK Section 3.

---

## Commit Rules

Conventional Commits, imperative mood, no trailing period:

```
<type>(<scope>): <subject>        # max 72 chars
                                  # blank line
<body>                            # explain WHY; wrap at 72 chars
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`.
**Subject:** imperative ("Add", "Fix", "Extract") -- NOT "Added", "Fixes".

**Procedure before every commit** (documentation is written first, then
validated -- a gate that runs before the doc update cannot check it, and
`pre-commit` includes the `doc-state-sync-check` hook):

1. Update PLAYBOOK Section 3 + Section 4. Batch log entries carry a
   `(Batch N WP-X)` tag in the heading; side-task entries are untagged
   (see Side-Task Handling). A tagged heading identifies which work package
   an entry belongs to; only an explicit `**Status:** WP-N complete` line in
   the entry body marks that package done (F-DOCSYNC-15). A multi-commit
   work package's earlier commits carry the tag without that line.
2. `pytest -q` -- all tests pass; measure and note N.
3. `python scripts/doc_state_sync.py --fix --test-count N` -- rotates and
   refreshes the managed blocks from the text you just wrote, and pins N
   in `config/docsync.toml`. Bare `--fix` remains documented for a commit
   that does not change the count.
4. Stage specific paths by name. **Never `git add -A` or `git add .`** --
   the prohibition is on the command, since it silently picks up whatever
   else is in the tree, even when every changed file belongs to this WP.
   Stage `.claude/SESSION_CONTEXT.md` together with PLAYBOOK whenever it
   changed; do not leave it modified and unstaged. Staging now, before
   `pre-commit run --all-files`, is required: the `tailwind-css-drift` hook
   rebuilds the compiled stylesheet and diffs it against the index, so an
   unstaged source edit always reads as drift whether or not the rebuild is
   correct (F-B21-20).
5. `pre-commit run --all-files` -- all hooks pass. A hook that rewrites a
   file, for example `tailwind-css-drift` itself or an auto-formatter,
   leaves the working tree ahead of the index again; re-stage the paths it
   touched before the next step.
6. `python scripts/doc_state_sync.py --check` -- exits 0 on the final
   state (the root `BATCHN_DEFINITION.md` warning is expected while a
   batch is active).
7. Commit after each WP (never batch multiple into one commit). Do not push
   without explicit owner instruction; pause after each commit for review.
   **Standing exception (Claude Code and Codex only, granted 2026-07-31):**
   review-fix commits on an already-open PR may be pushed without asking
   each time, with one batched reply per review round. Batch/WP commits
   still pause for review, and force-pushes, history rewrites, and anything
   targeting `main` always need explicit instruction. Copilot sessions,
   their subagents, Jules, and any other agent follow the unmodified rule
   and use the platform progress/reporting tool instead of shell `git`/`gh`.

**Pre-push self-review.** The validation gates check mechanics (tests,
formatting, docsync markers), not whether one document now contradicts
another -- that gap is what turns one review comment into a chain of rounds.
Before pushing:

1. Read each changed file **whole**, not as a diff -- contradictions hide in
   the unchanged text next to the edit.
2. Grep for the patterns in "Fixing the instance instead of the class",
   "Lossy or contradictory consolidation", and "Assertions over sets,
   ranges, and citations": stale citations, sibling copies of a corrected
   claim, every set or range the change asserts.
3. Scope that sweep to `git diff origin/main...HEAD` -- the branch's
   cumulative state, not just this round's commits -- so it narrows further
   each round until it finds nothing. A recorded deviation does not
   discharge it: grep the vocabulary of the property being deviated
   **from** and repoint or delete every affirmative claim (Section 4
   entries are point-in-time and stay as written).
4. Walk any touched procedure through its edge states, per
   "Happy-path-only procedures"; prefer deletion to addition -- a pointer
   removes surface area permanently, an added sentence is more to contradict.

**Co-author prohibition:** Do NOT add `Co-authored-by` trailers or co-author
metadata -- multi-agent orchestration means attribution is managed by the
owner, not by individual agents.

---

## Side-Task Handling

Not all work is batch work (e.g., a leap-year bugfix, a dark-mode polish
commit); non-batch changes follow the commit rules above unchanged,
including the documentation step landing in the *same* commit ("Missing
log entries" in the Anti-Pattern Registry). Side-tasks differ only in
where that entry goes and how it is tagged:

1. Add the dated entry in PLAYBOOK Section 4 **directly after** the
   `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker (top of the non-current
   list), using the same format but **without** a `(Batch N WP-X)` suffix --
   top placement keeps it out of the staleness filter and out of the next
   `--fix` run's rotation (`--keep-non-current`, default 4), which would
   otherwise archive a bottom-appended entry as oldest.
2. Run `doc_state_sync.py --fix --test-count N` (N =
   the just-measured `pytest -q` result) when the count changed, bare `--fix` otherwise;
   update SESSION_CONTEXT Section 1's batch-status row by hand if project state changed --
   the test-count field is rendered, never hand-edited.

---

## Test Quality Rules

**Forbidden patterns** (tests must challenge real behaviour, not just
confirm mocks were called):
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

`scripts/doc_state_sync.py` keeps PLAYBOOK, SESSION_CONTEXT, and the archive
consistent so every agent starts from identical state. It rotates overflow
dated entries from PLAYBOOK Section 4 into per-batch log files
(`docs/history/logs/BATCHN_LOG.md`, tagged entries) or the monolith archive
(`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, untagged side-task
entries); deduplicates archive entries by SHA-256 fingerprint; refreshes the
managed `DOCSYNC:STATUS` block in SESSION_CONTEXT from PLAYBOOK truth; and
validates the live document corpus through `docsync.integrity`, which
returns typed DOC diagnostic issues; error-severity ones block, and warnings
print without changing the exit code (full catalogue:
`docs/architecture/documentation-tooling.md`). Add a declaration
in `config/docsync.toml` when a fact starts living in two places, not after it
drifts (`F-B21-17` is the tally that motivated this).

### How to run

```bash
python scripts/doc_state_sync.py --fix          # after any Section 4 / SESSION_CONTEXT edit
python scripts/doc_state_sync.py --fix --test-count N   # after measuring the suite; pins N and writes all four count sites
pre-commit run --all-files
python scripts/doc_state_sync.py --fix --keep-non-current 0   # at batch close-out
```

Modes: `--check` (read-only; also the `doc-state-sync-check` pre-commit
hook), `--fix` (write updates), `--split-archive` (one-time migration into
per-batch log files). Exit codes: 0 clean; 1 drift or an integrity error;
2 malformed input or an invocation error. A commit staging docsync
control-plane code is refused; the one escape is
`SKIP=doc-state-sync-check git commit`, never `--no-verify` -- see
`docs/architecture/documentation-tooling.md`. A staged `config/docsync.toml`
whose only change is the `[test_count]` pin is not control-plane (owner
ruling 2026-09-26), so an ordinary `--fix --test-count N` commit runs every
hook.

Three further operator modes -- `--close-batch`, `--paginate-archives` and
`--cold-storage` -- are documented in `docs/architecture/documentation-tooling.md`
under "CLI surface added by the close-out and bounded-archives plan"; see
that heading for what each does.

### Integrity diagnostics

A proven defect prints as a stable `ERROR DOC...` diagnostic and exits 1 on
both modes; `--fix` writes deterministic output first, then revalidates the
final disk state rather than guessing how to repair a semantic reference.
`.claude/SESSION_CONTEXT.md`'s managed block is deterministic sync output,
so stale content there is blocking; an absent file skips dependent checks.
The DOC diagnostic catalogue and owning modules are in
`docs/architecture/documentation-tooling.md`; each WT code is defined by
the guard module that owns its check, spread across
`scripts/dev/_worktree_guard_*.py` -- grep for the code, not a module.
**Which test count is authoritative.** `--fix --test-count N` is how a measured count
enters the corpus: it pins `N` in `config/docsync.toml`'s `[test_count]` table and writes
the SESSION_CONTEXT STATUS block, the Section 1 `Tests` row, the Section 6 heading and the
FINDINGS.md header from the same number, in one command. Once a count is pinned, it stays
authoritative across every later `--fix` (with no `--test-count`) and `--check` --
Section 4 prose is not re-scanned for it, so a same-date tie or an out-of-position
correction (F-DOCSYNC-11, F-DOCSYNC-22) can never shadow the true count again. `--check`
prints a non-blocking DOC025 warning if the single newest dated log entry disagrees with
the pin. A repository with no pin falls back to the newest full-suite `pytest -q` result
found in the log, exactly as before.

### What to update after a WP or side-task commit

Before appending a new dated entry, search
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
`docs/history/logs/*.md` (`rg -n "^### 20"`) to avoid re-describing a
recorded decision or a date collision. Then update:

- PLAYBOOK Section 3 + Section 4 (inside markers for batch work, after the
  end marker for side-tasks; see Side-Task Handling).
- SESSION_CONTEXT Section 1's batch-status row by hand if changed (the test-count field is
  rendered by `--fix --test-count N`, never hand-edited), and
  Sections 3-4 (structure, dependency graph) if modules change.
- `README.md` for user/developer-visible changes (a batch's dedicated
  README WP may absorb updates from earlier WPs instead).
- `docs/history/reports/<TOPIC>_<DATE>.md` for significant findings or audits.

**Mid-batch handoff discipline:** PLAYBOOK Section 3 must reflect the true
state of every WP at all times -- mark a mid-WP deviation fix there before
committing, so a mid-batch arrival sees accurate state; Section 4 gives
detail, Section 3 the at-a-glance status, and both must agree.

---

## Batch Close-Out Procedure

When all WPs in the active batch are committed and validated:

1. **Run final sync:** `python scripts/doc_state_sync.py --fix --keep-non-current 0`
   (purges old non-current entries from PLAYBOOK Section 4 to keep it lean).
2. **Archive the definition file:** rename `BATCHN_PROPOSAL.md` (or equivalent)
   to `docs/history/definitions/BATCHN_DEFINITION.md` using `git mv`.
3. **Update PLAYBOOK Section 2** table: repoint the active batch's existing
   row (Definition cell currently the root file, Log cell `active --
   Section 4`) at `docs/history/definitions/BATCHN_DEFINITION.md` and
   `docs/history/logs/BATCHN_LOG.md`; add a new row only if the batch has none.
4. **Update SESSION_CONTEXT** Section 1 batch status row: `**Complete**. All N WPs done. Definition: docs/history/definitions/BATCHN_DEFINITION.md.`
5. **Run `--fix --test-count N`** (N = the
   just-measured `pytest -q` result) if the count changed since step 1's sync, bare `--fix`
   otherwise, to refresh the STATUS block.
6. **Verify clean:** `python scripts/doc_state_sync.py --check` exits 0 with
   no integrity errors (the root BATCH file warning disappears once step 2
   archives the definition).
7. **Commit:** `chore(close-out): Batch N complete; archive definition and purge log`.

---

## Proposal and Design Rules

1. **Definition before execution:** every batch needs a definition file
   (`BATCHN_DEFINITION.md` or equivalent) with acceptance criteria, written
   and committed before any WP begins; a retroactive one is a logged deviation.
2. **Scope discipline:** do not add work packages mid-batch without owner
   approval. Out-of-scope issues become deviation notes in the log entry,
   not new WPs -- an urgent small fix (under ~20 lines) is a deviation
   within the current WP; a larger one is a future-batch candidate.
3. **Size limits on new files:** the rule is against god files, not line
   counts -- a large file whose job is large is fine. Compare scope creep
   against the largest peer in its directory (the check, not a threshold);
   split only when genuinely outgrown, otherwise record it in the log entry
   (`F-WORKTREE-4`, `F-MAS-3`).
4. **Refactor requires parity tests:** do not restructure existing code
   (rename, move, split, merge) without first verifying tests cover the
   affected paths; add tests in a preceding WP if coverage is insufficient.
5. **Docstrings and comments:** every function has a comprehensive
   docstring; inline comments explain the why, not the what. SoC/DRY
   constrains file content, not line count.

---

## Anti-Pattern Registry

Patterns that have caused regressions or quality issues in past batches.
Agents must check their work against this list before committing.

1. **Test bloat without value:** a test that duplicates existing coverage or
   passes vacuously (succeeds even if the function under test is deleted).
   Every new test must exercise a unique code path or boundary condition.
2. **Undocumented SoC violations:** importing a leaf module into a
   higher-level one without updating the SESSION_CONTEXT Section 4
   dependency graph; every new cross-module import must be reflected there.
3. **Silent doc staleness:** committing code that changes test count,
   module structure, or the dependency graph without updating the matching
   docs (README, SESSION_CONTEXT Sections 3-4, PLAYBOOK Section 3).
4. **Wrong venv or bare pip (incident 2026-03-04):** `venv/` instead of
   `.venv/`, or bare `pip install` without the qualified path (Environment
   Setup), can silently install into the wrong environment.
5. **A server you start is yours to stop.** Serving is normal here
   (`scripts/dev/frontend_gate.py` starts the real app every run): bind
   loopback, ask the OS for a port instead of 5000, and shut down in a
   `finally`; never leave one running past the task, since the owner runs
   the app on 5000 in their own terminal.
6. **Naive-tz vacuous datetime tests (PR #152, F-B19-6):** a datetime test
   built with the same tz-awareness pattern as the code under test compares
   the code against itself, not an invariant -- use explicit `tzinfo=` and
   assert on a date that would shift under a naive read. Canonical:
   `tests/test_heatmap.py::TestAggregateDailyCounts::test_utc_decode_invariant_against_local_tz_drift`.
7. **Skipping hooks:** Never commit with `--no-verify`. Fix the failing
   hook instead.
8. **Stale PLAYBOOK Section 3:** not reflecting the true state of every WP
   at all times (see Doc Sync Rules, mid-batch handoff discipline).
9. **Missing log entries:** a WP or side-task commit without its dated
   PLAYBOOK Section 4 entry.
10. **Stale dashboard figures (coverage incident 2026-07-28):** quoting a
    canonical number (coverage, test count, module count) without
    re-measuring. Re-run the measuring command before repeating a number.
11. **Fixing the instance instead of the class:** repairing the reported
    symptom while its siblings survive untouched -- renumbering without
    repointing citations, or correcting one copy of a fact while duplicates
    remain. Grep for the other copies before the gates run: after
    renumbering or renaming, repoint every citation by **name**, not number
    (hits inside dated Section 4 entries are point-in-time and stay as
    written); after correcting a factual claim, grep its distinctive phrase
    and fix every copy in the same commit, or delete the copies and link to
    the single owner (Anti-duplication rule); after changing a signature,
    derivation, or ordering, grep the **concept**, not the literal string --
    the same fact recurs as code, prose, a worked example, or a second
    tabulation. A fix that leaves siblings behind is half a fix, and a new
    rule is not retroactive on its own: sweep the whole corpus against it in
    the same commit, or record the remaining backlog explicitly.
12. **Lossy or contradictory consolidation:** collapsing a duplicated rule
    to one owner, but (a) leaving copies in place while the new text claims
    they were removed, (b) dropping a prohibition, or (c) writing text that
    contradicts another section of the same file -- re-read the **whole**
    destination file, not the diff, and compare removed text against the
    new pointer.
13. **Assertions over sets, ranges, and citations:** stating a property of
    a group without checking each member. Universal quantifiers -- `all`,
    `each`, `every`, `both`, `none`, `always`, `never`, `X through Y` -- are
    highest-risk: expand and verify member by member, or rewrite the claim
    so it does not depend on membership; grep the whole vocabulary, not
    just the phrasing that failed last time.
14. **Happy-path-only procedures:** a numbered procedure that only works
    in one state. Walk every procedure through its edge states -- active
    batch vs. between batches, first run vs. re-run, item present vs.
    absent -- before committing it.
15. **Trusting an architecture diagram without checking source
    (F-B21-61):** `docs/architecture/*.md` diagrams are hand-maintained and
    drift after a module split or rename (three went stale after Batch 22
    WP-0); `docs/ARCHITECTURE.md`'s rule is that code wins when they
    disagree, so verify against current source before citing one -- its own
    "Last verified" date is as stale-prone as the diagram.

---

## Finding-Writing Rules

Findings live in `docs/agents/FINDINGS.md` (active) and rotate to
`docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out or a
findings-cleanup WP; nothing is deleted, so the archive preserves grep
history.

1. **F-ID format:** every item heading is `F-<context>-<N>: <title>`.
   Context is a batch tag (`B18`, `B19`, `B20`, ...) or one of these
   complete source tags -- extend the list here, never leave a tag
   undocumented: `MAS`, `DOCSYNC`, `AUDIT`, `LOAD`, `SWE`, `WORKTREE`,
   `DATA`, `STYLE`, `FEATURE`. No bare-numbered items in `docs/agents/FINDINGS.md`.
2. **Required fields:** the F-ID heading, a one-sentence problem statement,
   a `Status:` line, and a `Source:` line when a named audit or session
   produced it.
3. **Rotation:** resolved and closed no-action items move to the archive
   with their original F-ID and a `-- RESOLVED` / `-- NO ACTION` suffix;
   standing design-decision Info items stay active and rotate only when
   superseded.
4. **Cross-references:** a promoted or absorbed finding keeps a one-line
   pointer in "Deferred / future-batch candidates" (e.g. `F-B18-1 --
   promoted to F-B20-2`) so the old ID stays resolvable.

---

## Markdown Authoring Rules

- ASCII-only characters (no smart quotes, no em-dash -- use `--`).
- ISO dates: `YYYY-MM-DD`.
- Write plain English: short sentences, active voice, one idea each. A later
  agent pays to read every word. Log entries must cover scope, plan vs
  implementation, deviations, validation results (test count), and forward
  guidance -- that is what to cover, not how much to write.
- Do not manually move entries across DOCSYNC markers; use `doc_state_sync.py`.
