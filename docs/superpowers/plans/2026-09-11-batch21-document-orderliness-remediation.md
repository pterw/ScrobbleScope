# Batch 21 Document Orderliness Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository also requires a pause for owner review after each commit.

**Goal:** Remove the document-level defects that an exhaustive traversal of the Batch 21 design-system plan surfaced, so the live documents name themselves correctly and a bootstrap reader can see the commit debt.

**Architecture:** Four side-task commits, no work packages. Each task edits a live document and is proved by the same three gates the repository already runs (`pytest -q`, `pre-commit run --all-files`, `doc_state_sync.py --check`) plus one target-specific grep. Dated Section 4 log entries are never rewritten; the plan's own Progress section stays the owner of its status.

**Tech Stack:** Markdown documents, `scripts/doc_state_sync.py` (DOCSYNC marker and integrity management), pre-commit, pytest. No application code changes.

## Global Constraints

Copied verbatim from the repository ruleset. Every task's requirements include this section.

- Test baseline: `pytest -q` must report **1020 passed**. A different number is a failure to investigate, not a new baseline.
- `pre-commit run --all-files` must pass, all 10 hooks, with **no files modified**. A hook that modifies a file reports `Failed`; re-stage and re-run until a run modifies nothing.
- `python scripts/doc_state_sync.py --check` must exit **0**, with only the expected root-`BATCH21_DEFINITION.md` warning. Any `DOC` integrity error is a blocker.
- Never `git add -A` or `git add .`. Stage named paths only.
- Never commit with `--no-verify`.
- Commit format: Conventional Commits, imperative mood, subject at most 72 characters, no trailing period. No `Co-authored-by` trailer of any kind.
- ASCII only in documents: no smart quotes, no em dash -- write `--`.
- Do not push. Do not rewrite history. Pause after each commit for owner review.
- Do **not** edit `docs/design/designsystemaudit.md`. It is a dated, self-correcting record whose later sections supersede its earlier ones.
- Do **not** renumber WP-7 or WP-8. `DOC007` in `scripts/docsync/integrity.py` reads the WP headings and other documents cite them.
- Do **not** rewrite `PLAYBOOK.md` lines 882, 904 and 1016. They sit inside dated Section 4 log entries, which AGENTS.md treats as point-in-time records that stay as written.
- Side-task (untagged) entries go **immediately after** the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker in `PLAYBOOK.md` Section 4, at the top of the non-current list. That marker sits at the top level of Section 4, currently line 878. The identical string inside backticks near the top of Section 4 is an example in the "How to read dated entries" list and is **not** the insertion point. Batch entries are tagged `(Batch N WP-X)`; these are not.
- The only virtualenv is `.venv/` in the primary checkout at `C:\Users\peter\Python Projects\ScrobbleScope`. From this linked worktree, run Python, pytest and pre-commit through that qualified path.

## Why this scope, and what it excludes

A `deeper-reading` run traversed `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` exhaustively on 2026-09-11: 70 of 70 canonical chunks, 192 byte-anchored assertions, one recorded failure and its recovery. Its findings identified exactly two live document defects:

1. **The plan contradicts its own location.** Three passages name `implementation_plan.md`, a path that no longer exists. Section 7 of the traversal findings.
2. **The commit debt is invisible to bootstrap.** The three owed commits are recorded only in the plan's Progress section, not in `PLAYBOOK.md` Section 3, so an agent that bootstraps from `AGENTS.md` alone never learns of them. Section 10 of the traversal findings.

**Explicitly not in this plan.** The traversal also produced work items that already have owners, and this plan must not duplicate them:

| Item | Owner |
| --- | --- |
| Committing the staged F-B21-51 slice-1 set | The plan's Progress section, "Where to pick up" item 1, in its recorded order |
| Committing the architecture-diagram rebuild | The plan's Progress section, "Where to pick up" item 2 |
| Reconciling `DESIGN.md`, `RECONCILIATION.md`, the approved spec and `AGENT_DOC_MAP.md` to the audit | The plan's Phase 2, already scoped there |
| The fate of `docs/superpowers/plans/gemini_implementation_plan_unverified.md` | Open owner decision 2; do not decide it here |
| The expiry of the second theme write and the Bootstrap layer | The plan's Phase 4 (WP-8) |

---

### Task 1: Make the plan document name itself by its real path

The plan is untracked, so correcting its content and leaving it uncommitted would fix nothing observable. This task therefore commits the plan as part of the fix, which also discharges "Where to pick up" item 3 in its own Progress section. Record that as a deviation in the log entry.

**Files:**
- Modify: `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md:24-25` (Progress "State" line)
- Modify: same file `:307` (Root artifact table row)
- Modify: same file `:759-760` (open owner decision 1)
- Modify: same file `:790-791` (Verification section, last bullet)
- Modify: same file `:62-64` ("Where to pick up" item 3)
- Modify: `PLAYBOOK.md` Section 4, inserting the side-task entry directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker
- Stage also: `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md` (this plan)
- Test: no new test file. The guard is a grep, plus the repository's existing doc gates.

**Interfaces:**
- Consumes: nothing from an earlier task.
- Produces: the committed path `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`, which Task 3's report cites and Task 3's PLAYBOOK bullet links.

- [ ] **Step 1: Write the failing check**

A gate that can never fail is not a gate. This one names a literal that currently exists in exactly the three places being fixed, and must exist in none of them afterwards. Run:

```powershell
Select-String -LiteralPath 'docs\superpowers\plans\2026-09-11-batch21-design-system-reconciliation.md' -Pattern '`implementation_plan\.md`' -Encoding UTF8 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }
```

- [ ] **Step 2: Run it and confirm it fails**

Expected: **3 matches**, at lines 307, 759 and 791. If you see a different count, stop and read the file before editing: the plan may have moved on, and this plan's line numbers are a hint, not an authority.

- [ ] **Step 3: Fix the Progress "State" line**

Replace lines 24-25:

```
**State: Phase 1 complete and committed. Phases 2-5 not started. Three work
items are uncommitted.** Nothing is pushed.
```

with:

```
**State: Phase 1 complete and committed. Phases 2-5 not started. Uncommitted
work: the staged F-B21-51 slice-1 gate refactor; the architecture-diagram
rebuild; and this plan's own move into `docs/superpowers/plans/` together with
the document-orderliness remediation plan, until that remediation is
committed.** Nothing is pushed.
```

The count is deliberately replaced by a list. A number goes stale the next time a work item appears, and AGENTS.md's Anti-Pattern Registry item 13 records a claim that depended on set membership surviving several sweeps because the wording was never re-expanded.

- [ ] **Step 4: Fix the Root artifact table row**

Replace line 307 entirely:

```
| `implementation_plan.md` (this file) | A working plan, not a governed document. Decide before the first commit whether to keep it (then add it to the doc map) or remove it, so it does not become another undeclared root file. `docs/superpowers/plans/gemini_implementation_plan_unverified.md` is already untracked in this worktree and is a prior, unverified attempt at the WP-7 extension; resolve its fate in the same decision. |
```

with:

```
| `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` (this file) | Kept, and moved here from the repository root on 2026-09-11. It is a working plan, not a governed document, so it needs no doc-map entry; its move is the commit owed under "Where to pick up" above. `docs/superpowers/plans/gemini_implementation_plan_unverified.md` is already untracked in this worktree and is a prior, unverified attempt at the WP-7 extension; resolve its fate in the same decision. |
```

- [ ] **Step 5: Fix the open owner decision**

Replace lines 759-760:

```
1. **Would `implementation_plan.md` be kept or removed?** It is a working
   artifact, not a governed document.
```

with:

```
1. **Would `implementation_plan.md` be kept or removed?** Settled 2026-09-11:
   kept, and moved to
   `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`.
   It is a working artifact, not a governed document, so it needs no doc-map
   entry. Recorded here rather than deleted and renumbered, so the numbering of
   the decisions below stays stable for anything that cites them.
```

- [ ] **Step 6: Fix the Verification bullet**

Replace lines 790-791:

```
- No production file, test, or governed document was edited while producing
  this plan. The only file created is `implementation_plan.md`.
```

with:

```
- No production file, test, or governed document was edited while producing
  this plan. The only file created was `implementation_plan.md`, which was
  moved to
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`
  on 2026-09-11.
```

- [ ] **Step 7: Re-run the guard and sweep the repository**

Re-run Step 1's command. Expected: **0 matches**.

Then sweep the whole repository, because AGENTS.md's item 11 requires repointing every copy rather than fixing the reported instance:

```powershell
git grep -n 'implementation_plan' -- '*.md'
Select-String -Path 'PLAYBOOK.md' -Pattern 'implementation_plan' -Encoding UTF8 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }
```

Expected: hits only inside dated Section 4 entries, `docs/history/` records, or `docs/logarchive/` records -- including this task's own log entry, which quotes the old name as history. Verify each remaining hit individually and confirm it is inside a dated region. **Do not edit `PLAYBOOK.md` lines 882, 904 or 1016.** They are point-in-time records of what the document said that day, and AGENTS.md keeps those as written.

- [ ] **Step 8: Discharge "Where to pick up" item 3**

Replace lines 62-64 of the design-system plan:

```
3. Commit this plan's move. Decide the fate of
   `docs/superpowers/plans/gemini_implementation_plan_unverified.md` at the same
   time -- it is untracked, superseded, and still in the directory.
```

with:

```
3. Commit this plan's move. **Discharged 2026-09-11** by the
   document-orderliness remediation commit, which staged this file. The fate of
   `docs/superpowers/plans/gemini_implementation_plan_unverified.md` is still
   open: it remains untracked, superseded, and in the directory.
```

- [ ] **Step 9: Write the Section 4 log entry**

Insert this entry in `PLAYBOOK.md` **immediately after** the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, at the top of the non-current list. It is a side-task entry, so it carries **no** `(Batch N WP-X)` tag:

```
### 2026-09-11 - Design-system plan corrected to name its own path

- Scope: the Batch 21 design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`)
  still described itself by its pre-move repository-root name in three places,
  and its Progress "State" line counted its uncommitted work items rather than
  naming them. Both defects came from an exhaustive traversal of the plan; the
  evidence is `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- Plan vs implementation: all four edits landed as written. The State line now
  lists the uncommitted items instead of counting them, because a count goes
  stale the next time one appears (Anti-Pattern Registry item 13). The
  open-decision entry was rewritten in place rather than deleted, so the
  numbering of the decisions below it stays stable for any citation.
- Deviation: this commit stages the plan itself, discharging that plan's own
  "Where to pick up" item 3, which its Progress had recorded as a separate
  commit. A content correction to an untracked file is observable only once the
  file is committed, so the reorder is recorded rather than silent.
- Validation: `pytest -q` -- 1020 passed. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0,
  with the expected root `BATCH21_DEFINITION.md` warning. The target guard fell
  from 3 matches to 0.
- Forward guidance: the three dated references to the old root name in this
  file's Section 4 stay as written. They record what the document said on the
  day it was written, and editing them would falsify a dated record.
```

- [ ] **Step 10: Run the gates**

In this order, and do not advance past a failure:

```powershell
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Expected: `--fix` refreshes the managed block, `pytest -q` reports **1020 passed**, the hooks report 10 passed with no files modified, and `--check` exits 0 with only the root-`BATCH21_DEFINITION.md` warning. If a hook modifies a file, re-stage that file and run the hooks again until a run modifies nothing.

- [ ] **Step 11: Commit**

Stage named paths only:

```powershell
git add docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md
git add docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md
git add PLAYBOOK.md
git status --short
git commit -m "docs(plan): Name the plan's own path and list its uncommitted work"
```

If `.claude/SESSION_CONTEXT.md` changed, stage it in the same commit. If `git status --short` shows anything else staged, stop and unstage it: the staged F-B21-51 set belongs to the previous session's work item, not this one.

**Pause for owner review before Task 2.**

---

### Task 2: Record the traversal durably

The traversal's requested deliverable currently lives only at `scratch/deeper-reading-batch21-plan/deliverables/PLAN_TRAVERSAL_FINDINGS.md`, inside an untracked directory. A findings record that no commit contains is not orderly, and `docs/history/reports/` is this repository's declared home for significant findings and audits.

**Files:**
- Create: `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`
- Modify: `PLAYBOOK.md` Section 4, inserting the side-task entry directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker
- Read (source, not modified): `scratch/deeper-reading-batch21-plan/deliverables/PLAN_TRAVERSAL_FINDINGS.md`
- Test: no new test file. The guards are `git ls-files --error-unmatch`, a non-ASCII byte count, and `doc_state_sync.py --check`.

**Interfaces:**
- Consumes: the committed plan path from Task 1.
- Produces: the committed path `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`, which Task 3's PLAYBOOK bullet links.

- [ ] **Step 1: Write the failing check**

```powershell
git ls-files --error-unmatch docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md
```

- [ ] **Step 2: Run it and confirm it fails**

Expected: a non-zero exit and `did not match any file(s) known to git`. The report does not exist, and an untracked document cannot satisfy a citation.

- [ ] **Step 3: Create the report**

Copy the traversal findings, then adapt them. Do **not** re-author the findings from memory: the source file is complete and its chunk-ordinal citations are the run's proof.

```powershell
Copy-Item 'scratch\deeper-reading-batch21-plan\deliverables\PLAN_TRAVERSAL_FINDINGS.md' 'docs\history\reports\BATCH21_PLAN_TRAVERSAL_2026-09-11.md'
```

Then make exactly four adaptations, and no others:

1. **Replace the opening block** (the source line, the coverage paragraph and the machine-proof pointer) with this provenance header:

```
# Batch 21 design-system plan: exhaustive traversal findings

Recorded 2026-09-11 for the repository's own record. The traversal itself was
run with the `deeper-reading` skill against
`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`
(sha256 `3988998c93bb3005cfe3c183b82043cc4f1325bb361a306e1f618edb58b1ee18`,
57062 bytes).

Coverage: 70 of 70 canonical chunks, 192 byte-anchored assertions, one recorded
failure and its recovery. The machine proof (chunk manifest, evidence ledger,
run ledger, rendered traversal report) lives in the untracked run root
`scratch/deeper-reading-batch21-plan/`; it is not committed, and this report is
the durable summary of it.
```

2. **Rename the section headings** so they read as a historical record rather than a live briefing, and change any sentence describing the plan in the present tense as a work order into the past tense of what was found. The findings themselves keep their content and their chunk ordinals.
3. **Drop the final "Coverage note" section**, because its content now appears in the provenance header above.
4. **Keep every chunk-ordinal citation** (`[2]`, `[8]`, `[43]`, and the rest). They are what makes the record checkable against the run root.

- [ ] **Step 4: Confirm the report is ASCII-only**

```powershell
$b = [System.IO.File]::ReadAllBytes('docs\history\reports\BATCH21_PLAN_TRAVERSAL_2026-09-11.md'); "non_ascii_bytes=$(($b | Where-Object { $_ -gt 127 } | Measure-Object).Count) total_bytes=$($b.Length)"
```

Expected: `non_ascii_bytes=0`. If it is not zero, find the character and replace it: this repository is ASCII-only, and an em dash or a smart quote is the usual cause.

- [ ] **Step 5: Stage the report, then re-run the guard**

```powershell
git add docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md
git ls-files --error-unmatch docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md
```

Expected: PASS, exit 0. Staging before linking is required by AGENTS.md: `doc_state_sync.py`'s `DOC001` resolves backticked paths through `git ls-files`, so an unstaged document cannot satisfy a citation.

- [ ] **Step 6: Write the Section 4 log entry**

Insert this entry in `PLAYBOOK.md` immediately after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, untagged:

```
### 2026-09-11 - Exhaustive plan traversal recorded

- Scope: an exhaustive traversal of the Batch 21 design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`)
  was run with the `deeper-reading` skill on 2026-09-11. Its findings are
  recorded at `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- Plan vs implementation: 70 of 70 canonical chunks carried a byte-anchored
  evidence verdict, 192 assertions in total, with zero `non_match` verdicts and
  70 ordered `chunk_verified` events. One assertion failed its span check on the
  first attempt and was repaired by re-quoting it from the chunk; the failure,
  its diagnosed cause and the recovery are recorded in the report and in the
  run root's failure ledger.
- Deviation: none. The report is a durable copy of a working artifact, not new
  analysis.
- Validation: `pytest -q` -- 1020 passed. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0.
  The report is ASCII-only, measured at 0 bytes above 0x7F.
- Forward guidance: the machine proof stays in `scratch/`, which is untracked.
  If the run root is deleted, the report remains the record and its chunk
  ordinals stop being checkable against the manifest. Delete it only knowingly.
```

- [ ] **Step 7: Run the gates**

```powershell
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Expected: **1020 passed**; 10 hooks passed with no files modified; `--check` exits 0 with only the root-`BATCH21_DEFINITION.md` warning.

- [ ] **Step 8: Commit**

```powershell
git add docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md
git add PLAYBOOK.md
git status --short
git commit -m "docs(report): Record the exhaustive traversal of the design-system plan"
```

**Pause for owner review before Task 3.**

---

### Task 3: Make PLAYBOOK Section 3 carry the owed work

This is the second live defect. The three owed commits are recorded only in the design-system plan's Progress section. An agent that bootstraps from `AGENTS.md` reaches the specification conflict (Section 3 already carries it) but never learns that commits are owed before Phase 2. Section 3 is the section `AGENTS.md`'s bootstrap gate reads first, so that is where the debt has to be visible.

**Files:**
- Modify: `PLAYBOOK.md` Section 3, appending two bullets immediately after the "Next action:" bullet, which ends with the words `WP-8 starts only on owner direction.`
- Modify: `PLAYBOOK.md` Section 4, inserting the side-task entry directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker
- Test: no new test file. The guard is a grep, plus `doc_state_sync.py --check`.

**Interfaces:**
- Consumes: the committed report path from Task 2, and the discharged work item from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing check**

```powershell
Select-String -LiteralPath 'PLAYBOOK.md' -Pattern 'Owed before Phase 2' -Encoding UTF8 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }
```

- [ ] **Step 2: Run it and confirm it fails**

Expected: **0 matches**.

- [ ] **Step 3: Append the two bullets to Section 3**

Insert directly after the line ending `WP-8 starts only on owner direction.`:

```

- **Owed before Phase 2:** the commits owed before Phase 2 are recorded only in
  the design-system plan's Progress section
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`):
  the staged F-B21-51 slice-1 gate refactor, and the architecture-diagram
  rebuild. That plan's own move was committed on 2026-09-11 together with
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`.
  An agent that bootstraps from this section reaches the specification conflict
  above but not the commit debt.
- **Traversal record:** the design-system plan was traversed exhaustively on
  2026-09-11; the findings are
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
```

The bullets name the owed commits rather than counting them. A count in this section goes stale the next time a work item appears, which is the same defect Task 1 fixed in the plan.

- [ ] **Step 4: Re-run the guard**

```powershell
Select-String -LiteralPath 'PLAYBOOK.md' -Pattern 'Owed before Phase 2' -Encoding UTF8 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }
```

Expected: **1 match**.

- [ ] **Step 5: Write the Section 4 log entry**

Insert this entry in `PLAYBOOK.md` immediately after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, untagged:

```
### 2026-09-11 - Section 3 now carries the commit debt

- Scope: the commits owed before Phase 2 were recorded only in the
  design-system plan's Progress section, so the bootstrap path in `AGENTS.md`
  reached the specification conflict but not the commit debt. Section 3 now
  names them, and points at the traversal record.
- Plan vs implementation: both bullets landed as written, inserted directly
  after the existing "Next action:" bullet.
- Deviation: none. Section 3 gains a statement of existing state; no new work
  is created and no WP is added.
- Validation: `pytest -q` -- 1020 passed. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0
  with the expected root `BATCH21_DEFINITION.md` warning.
- Forward guidance: keep Section 3's bullets free of counts. Name each owed
  item, so the next addition cannot make the section silently wrong.
```

- [ ] **Step 6: Run the gates**

```powershell
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Expected: `--fix` refreshes the managed STATUS block in `.claude/SESSION_CONTEXT.md` from the Section 3 text just written; **1020 passed**; 10 hooks passed with no files modified; `--check` exits 0.

- [ ] **Step 7: Commit**

```powershell
git add PLAYBOOK.md
git add .claude/SESSION_CONTEXT.md
git status --short
git commit -m "docs(playbook): Surface the owed commits in the next-action section"
```

Stage `.claude/SESSION_CONTEXT.md` only if `--fix` changed it. AGENTS.md requires staging it together with PLAYBOOK whenever it changed, never leaving it modified and unstaged.

**Pause for owner review before Task 4.**

---

### Task 4 (owner-gated): Ignore the agent-session analysis trees

This is the only task that does not come from the traversal. It is included because the three tasks above add files to `scratch/`, and today nothing keeps that directory out of a commit except the repository's ban on `git add -A`. If the owner would rather leave the trees visible, drop this task: Tasks 1 to 3 stand alone.

**Files:**
- Modify: `.gitignore`, inserting a block immediately after the `.agents/` entry
- Test: no new test file. The guard is a `git status` sweep.

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

- [ ] **Step 1: Write the failing check**

```powershell
git status --porcelain --untracked-files=all | Select-String '^\?\? (\.agent/|\.impeccable/|\.qlty/|scratch/)' | Measure-Object | Select-Object -ExpandProperty Count
```

- [ ] **Step 2: Run it and confirm it fails**

Expected: a large non-zero count -- over 500 at the time of writing, of which `scratch/` alone is over 480.

- [ ] **Step 3: Add the ignore block**

Insert immediately after the `.agents/` line:

```
# Agent-session analysis scratch and tool state. Untracked by intent: the
# impeccable skill's workflow copies and live session logs, the qlty analyser's
# cache and results, and the deeper-reading traversal run root (source
# manifest, chunk evidence, rendered traversal report). None of it is project
# state, but left unignored it put 500-odd untracked paths in every
# `git status`, and the only thing keeping it out of a commit was the ban on
# `git add -A`. The singular `.agent/` is deliberate: `.agents/` above is the
# vendored skill pack, a different directory.
.agent/
.impeccable/
.qlty/
scratch/
```

- [ ] **Step 4: Re-run the guard**

Re-run Step 1's command. Expected: **0**.

- [ ] **Step 5: Confirm nothing else moved**

```powershell
git status --short
```

Expected: the same tracked modifications and the same staged set as before this task, minus the now-ignored untracked trees. If a tracked file has disappeared from the list, stop: an ignore pattern matched something it should not have.

- [ ] **Step 6: Write the Section 4 log entry**

Insert this entry in `PLAYBOOK.md` immediately after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, untagged, and state in it that the task was owner-gated and taken:

```
### 2026-09-11 - Agent-session analysis trees ignored

- Scope: `.agent/`, `.impeccable/`, `.qlty/` and `scratch/` were untracked and
  also unignored, so every `git status` carried 500-odd paths and the only
  guard against sweeping them into a commit was the ban on `git add -A`.
- Plan vs implementation: the four patterns landed with a comment recording why
  each is untracked, and why the singular `.agent/` is deliberate beside the
  vendored `.agents/`.
- Deviation: the owner was offered this task as optional because it does not
  come from the traversal; it was taken.
- Validation: `pytest -q` -- 1020 passed. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0.
  The untracked sweep fell from 500-odd to 0, and the tracked file list was
  unchanged.
- Forward guidance: the traversal run root now lives under an ignored path. Its
  report was committed first, so the record survives even if the run root is
  deleted.
```

- [ ] **Step 7: Run the gates and commit**

```powershell
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
git add .gitignore
git add PLAYBOOK.md
git status --short
git commit -m "chore(repo): Ignore agent-session analysis trees"
```

**Pause for owner review. This is the final task.**

---

## Self-review

**1. Spec coverage.** Every finding the traversal produced that has this plan as its owner is covered:

| Traversal finding | Task |
| --- | --- |
| Section 7 -- the plan contradicts its own location (three stale self-references) | Task 1 |
| Section 10 -- the commit debt is invisible to bootstrap | Task 3 |
| The traversal's findings exist only in an untracked scratch directory | Task 2 |
| (Not from the traversal) 500-odd untracked analysis paths | Task 4, owner-gated |
| Sections 1 to 6 and 8 to 9 -- findings that describe the plan's content, not a document defect | Not a defect. Section 1 and 2 are the plan's own documented design; Sections 3 to 6 and 8 to 9 are its substance, and the plan owns them under Phase 2 and Phase 4 |
| The unresolvable `scratchpad/ds-push/` citation in `docs/design/designsystemaudit.md` | **Deliberately not fixed.** The audit is a dated record that must not be edited. Task 2's report and Task 3's bullet point readers at the audit as a record rather than treating its citations as live |

**2. Placeholder scan.** No "TBD", no "add appropriate handling", no "similar to Task N". Every edit carries its exact old text and its exact replacement text. Every command carries its expected result. The two places a whole document is not reproduced inline are deliberate: Task 2 tells the implementer to copy a named existing file and lists the four adaptations, because reproducing a 13 KB report inside the plan would be a second copy free to drift.

**3. Consistency.** Paths appear in the same form everywhere: `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` (the design-system plan), `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md` (this plan), `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md` (the report), `scratch/deeper-reading-batch21-plan/` (the run root). Task 2 precedes Task 3 because Task 3 links the report, and `DOC001` will not resolve an unstaged path. Task 1 precedes Task 2 because the report cites the plan's committed path.





