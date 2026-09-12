# Handoff -- ScrobbleScope Batch 21, WP-7 refinement + F-B21-51 slice 1

Written 2026-09-11 by the outgoing agent. Save location: OS temp, per the
`handoff` skill. This document does not restate rules or plans; it names the
artifacts that own them and the state you are inheriting.

---

## 0. Read this first

**Branch `test` is 10 commits ahead of `origin/main`. HEAD is `57d1474`.**

**Three work items are uncommitted: one STAGED, two UNSTAGED.** That is the
single most important fact here. Section 3 covers all three.

Nothing is pushed. No history was rewritten.

---

## 1. Environment -- reproduce this exactly

| Thing | Value |
| --- | --- |
| Linked worktree (work here) | `c:\Users\peter\.config\superpowers\worktrees\ScrobbleScope\batch-21\impeccable-init` |
| Primary checkout (owns the ONLY `.venv`) | `C:\Users\peter\Python Projects\ScrobbleScope` |
| Qualified python | `C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe` |
| Qualified pytest | `...\Scripts\pytest.exe` |
| Qualified pre-commit | `...\Scripts\pre-commit.exe` |

**Never create a second virtualenv.** A linked worktree reuses the primary
checkout's `.venv`.

**Git hooks call bare `pre-commit`.** If it is not on `PATH`, `git commit` is
refused with "`pre-commit` not found". Prepend it for the commit only:

```powershell
$env:PATH = 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts;' + $env:PATH
git commit ...
```

**Never `--no-verify`** (AGENTS.md Anti-Pattern Registry item 7).

### The terminal is unstable -- use this pattern

In this session the terminal wedged repeatedly: queued commands, output capture
failures, and one lingering multi-line continuation prompt after a malformed
quote. Two habits keep you moving:

1. **Long commands: run them detached, then poll a file.** A foreground
   `Start-Sleep` does not consume wall-clock before the tool returns, so you
   cannot "wait" for a slow command that way.

```powershell
$p = Start-Process -FilePath $py -ArgumentList 'scripts/dev/frontend_gate.py' `
     -WorkingDirectory (Get-Location).Path `
     -RedirectStandardOutput "$env:TEMP\gate_out.txt" `
     -RedirectStandardError  "$env:TEMP\gate_err.txt" -NoNewWindow -PassThru
$p.Id
# then, in a later call:
Get-Content "$env:TEMP\gate_out.txt" -Tail 20
```

2. **If output is missing, treat it as missing.** Do not assume a command
   succeeded because you expected it to.

If the prompt shows `>>`, press Ctrl+C or open a fresh terminal.

---

## 2. Start sequence -- identical to the outgoing agent's

1. Read `AGENTS.md` **in full**. It is the ruleset.
2. Read `docs/design/designsystemaudit.md` **sequentially, all 1048 lines**.
   It is self-correcting: several later sections supersede earlier claims
   (D-17, D-25, D-26, the `.dark-mode` "dead" claim, D-34). Read it at least
   twice before acting on it. Do not edit it; it is a dated record.
3. Bootstrap set in the canonical order AGENTS.md gives: `PLAYBOOK.md`
   Sections 3-4, `BATCH21_DEFINITION.md`, `.claude/SESSION_CONTEXT.md`
   Sections 1-2, `AGENT_NOTES.md`.
4. Worktree guard -- the **only** command where bare `python` is allowed,
   because the primary paths are not known until it prints them:

```powershell
python scripts/dev/check_worktree_alignment.py
```

   Expect exit 0. `WT010` (dirty worktree) is a warning, and the tree IS dirty
   by design right now.
5. From then on, use the qualified paths above. Baseline: `pytest -q` must be
   **1020 passed**.
6. `python scripts/doc_state_sync.py --check` must exit 0 with only the
   expected root-`BATCH21_DEFINITION.md` warning.

---

## 3. THE IMMEDIATE TASK -- commit the staged work

`git status` shows exactly this staged set, nothing unstaged:

```
M  .claude/SESSION_CONTEXT.md
M  FINDINGS.md
M  PLAYBOOK.md
M  docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
A  scripts/dev/_frontend_gate_colour.py           (new, 129 lines)
M  scripts/dev/frontend_gate.py
A  tests/scripts/dev/test_frontend_gate_colour.py (new, 191 lines)
```

480 insertions, 140 deletions.

**All gates were observed green on exactly this staged state:**

- `pytest -q` -> **1020 passed**
- `pre-commit run --all-files` -> **10 / 10 Passed, no files modified**
- `doc_state_sync.py --check` -> passed (expected root-BATCH warning only)
- Frontend gate -> `26 checks passed in 47 runs across chromium, firefox ...
  profiles: desktop, mobile, wide touch`

That work is **F-B21-51 slice 1**: the pure colour/contrast maths moved out of
`frontend_gate.py` into `scripts/dev/_frontend_gate_colour.py`, re-exported
through the gate as a facade, with 29 parity tests. Its PLAYBOOK entry is
already written (untagged side-task entry at the top of the non-current list,
directly after `<!-- DOCSYNC:CURRENT-BATCH-END -->`).

Commit it, then **pause for owner review** (AGENTS.md commit discipline). No
push without explicit instruction.

**Suggested message** (Conventional Commits, imperative, no trailing period):

```
refactor(gate): Extract the colour maths as F-B21-51 slice 1
```

### 3.1 A SECOND work item is unstaged -- the architecture diagrams

Do not lose this. It is a separate work item with its own staged/unstaged split:

```
 M docs/ARCHITECTURE.md
 M docs/architecture/development-cycle.md
 M docs/architecture/documentation-tooling.md
 M docs/architecture/heatmap-sequence.md
 M docs/architecture/runtime-system.md
 M docs/architecture/top-albums-sequence.md
MM PLAYBOOK.md                        <- commit B's entry staged, the diagram
MM docs/logarchive/...                <- entry and its rotation unstaged
```

`git status` shows `MM` on `PLAYBOOK.md` because its diagram-work log entry was
written after commit B was staged. Committing the INDEX therefore commits commit
B without that entry, which is correct; stage `PLAYBOOK.md` again for the
diagram commit.

What was rebuilt, and why:

- `docs/ARCHITECTURE.md` said **"Last verified against the tree on 2026-08-15"**
  and now says 2026-09-11, with its source references extended.
- `runtime-system.md`: `spotlight.py` and `unmatched.py` were **missing
  entirely**, as were the canonical routes and JSON APIs. Added both modules and
  their edges, route and API nodes, a `Theme` node for the `data-theme` plus
  `.dark-mode` dual write, and prose for three silent-failure facts: one
  framework stylesheet per page, the theme dual write whose observer WP-8 must
  move in the same change, and the `_MAX_ALBUM_CAP` cost boundary plus
  partition-before-Spotify.
- `documentation-tooling.md`: `docsync.declarations` and `.docsync.toml` were
  absent, so nothing showed how a declared fact reaches integrity checking. Also
  added `FINDINGS.md` and its rotation, `docs/agents/`, `docs/history/`, the
  index, the ten pre-commit hooks, and the frontend-gate toolchain.
- `development-cycle.md`: an annotation read **"Current Batch 21 order: F-SWE-1
  audit, then WP-1"**, false since WP-2. Replaced with the side-task path, the
  session-close handoff, and a pointer that the active order lives in PLAYBOOK
  Section 3.
- `top-albums-sequence.md`: added the threshold partition and its persistence
  before Spotify, corrected the cap to `_MAX_ALBUM_CAP` for every sort mode, and
  named the reason order on `/unmatched`.
- `heatmap-sequence.md`: added canonical `/heatmap` against transient
  `/loading`, and the cached-saved-job path.

**Observed on this work:** `pytest -q` 1020 passed; `doc_state_sync.py --check`
exit 0; all six files ASCII-only; Mermaid block balance `opens == ends` in each
file (28/28, 15/15).

**A near-miss worth knowing.** The first draft put a `;` inside a mermaid
`Note over` statement in `heatmap-sequence.md`. The Mermaid instruction file
records exactly that as a parse failure which shipped once before, escaped as
`&#59;` rather than removed. It was caught by checking every file for a `;`
inside a fence, not by looking at the diff. **There is no Mermaid MCP tool
reachable in this environment**, so validation was structural, not a render; a
renderer pass is still worth doing, and `.mmd` files stay the authoring surface
and must not be committed.

### 3.2 THE PLAN is now tracked, and it tracks itself

The plan moved out of the repository root and into the plans directory:

```
docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md
```

It was `implementation_plan.md`, untracked, at the root. It is worth keeping: it
carries the audit's repo-side disposition table -- what is actionable here versus
what belongs to the external design project -- and the reasoning behind each
phase. **Read its `## Progress` section first**; it owns the status and says
where to resume. Nothing else in the repository restates it.

What that section contains, so you know what you are inheriting:

- A per-phase state table (0 done, 1 done and committed, 2-5 not started) with
  the evidence for each.
- The three commits this plan produced.
- The uncommitted work, **in the order it should be committed**.
- A numbered pick-up list, starting with the spec-versus-ruling conflict.
- **Four recorded deviations** between the plan as written and what Phase 1
  actually did. The first matters most: the plan said to rebuild the report as
  stacked full-width sections, and Phase 1 **refined** the side-by-side layout
  instead, because the owner's ruling superseded that step and three
  frontend-gate assertions defend the shipped arrangement. The plan text was
  corrected, but the deviation is recorded so nobody reads the corrected version
  as a faithful account of what happened.

Its log entry is written and unstaged, and it needs its own commit. Resolve
`docs/superpowers/plans/gemini_implementation_plan_unverified.md` in the same
commit: it is untracked, superseded by this plan, and still in the directory.

---

## 4. What commit A already did (HEAD `57d1474`)

`fix(ui): Refine the unmatched report disclosure` -- the WP-7 refinement the
owner asked for: disclosure step 50 -> 25, back-to-top now collapses its panel,
one `applyVisibleCount(count, isCollapsed)` writer replacing three copies of the
state machine, and the reason detail wraps instead of truncating. Plus two
`daisyui`-skill-driven refinements: the panel album count moved off `primary` to
`base-content` (colour rule 10, `primary` once per page), and the panel header
takes Results' scale-aware padding.

It also landed a rebuilt `static/css/tailwind.css` that drops a **stale
`.collapse` utility no source produces**. That drift entered with the previous
commit `72615ed`, not with the change.

---

## 5. Findings you must log / not re-discover

These cost real time. They are the doc-sync and CI machinery doing its job:
**treat every red gate as the first source of truth.**

### 5.1 DoSync integrity codes, and how they bit

| Code | What it enforces | What happened |
| --- | --- | --- |
| **DOC008** | `FINDINGS.md`'s header count line must equal the newest full-suite `pytest -q` result | The header said `990 tests across 41 test modules` while the suite was 1020. **Only the TEST count is validated; the module count is not**, and the module figure had independently drifted by two (header said 41, measured 43 `test_*.py` files). |
| **DOC006** | Every named session current-test field agrees with the log | `SESSION_CONTEXT.md` has **TWO** such fields: the Section 1 row `\| Tests \| **N passing** across M test modules \|` **and** the Section 6 heading `## 6. Test structure (N tests)`. Fixing one and missing the other leaves `--check` red. |
| **DOC001** | A backticked `` `path.md` `` reference must resolve in `git ls-files` | An **ignored** or **untracked** path can never resolve. Stage a new document BEFORE linking to it. Schematic tokens containing `< > * ? [ ] { } %`, `BATCHN`, or `path/to/` are exempt. |

### 5.2 The `ruff` F401 trap -- this broke the build

`ruff --fix` **stripped four of seven names from the facade import** in
`frontend_gate.py` as "unused", because nothing inside that module used them any
more. But they are re-exports, and an existing test imports them:

```
ImportError: cannot import name '_composite_over' from 'scripts.dev.frontend_gate'
```

`pytest` could not even collect. Fixed by marking the import block:

```python
from scripts.dev._frontend_gate_colour import (  # noqa: E402, F401
    _clamp_px, _composite_over, _contrast_ratio, _divider_contrast_failure,
    _parse_rgb_string, _relative_luminance, _worst_divider_contrast,
)
```

**Any future facade `_frontend_gate_*` extraction needs the same suppression**,
or the split silently breaks its callers. F-B21-51 records this.

### 5.3 A verification failure worth copying

An earlier grep for existing imports of the moved helpers passed a **nonexistent
path** alongside the real one. The error aborted the pipeline, the pattern
reported "no matches", and the outgoing agent concluded no test pinned them.
Wrong: `tests/scripts/dev/test_frontend_gate.py` imported all seven on one line.
**Grep one path per call, or verify the files exist first.** This is F-B21-51's
own warning that existing tests are not evidence a split is safe.

### 5.4 Pre-commit's stash/restore cycle

`pre-commit run --all-files` stashes unstaged files, runs hooks, restores, and
**hooks that modify files report `Failed`** even when the modification is a
benign auto-fix. Two consequences:

- Re-stage after any modifying hook and run the hooks again; only a run with no
  modifications is evidence.
- `docs/AGENT_DOC_MAP.md` warns this cycle has reverted files nobody edited. It
  produced 5.2 live.

### 5.5 F-B21-20 -- the Tailwind drift hook's staging order

`tailwind-css-drift` rebuilds `static/css/tailwind.css` and diffs it against the
**index**, so it fails before staging and passes at commit time for the same
reason a stale output fails. It also surfaced real drift (the `.collapse` rule).
record which order you used; do not silently reorder the repository procedure.

---

## 6. Skills to load

Invoke these before acting. `using-superpowers` is the gate: it requires
invoking relevant skills before any response, including clarifying questions.

| Skill | Why, for this repo |
| --- | --- |
| `using-superpowers` | The invocation discipline itself |
| `executing-plans` | `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` is the active plan; read its Progress section, stop on blockers, verify each step |
| `using-git-worktrees` | Step 0 confirms the linked worktree; do not create another |
| `scrobblescope-bootstrap` | Canonical read order; the pytest count must match `SESSION_CONTEXT` |
| `setup-matt-pocock-skills` | **Already run.** Output: `docs/agents/issue-tracker.md` (issues are findings in `FINDINGS.md`) and `docs/agents/domain.md` |
| `frontend-design` | Its Phase 1 design annex lives in the plan at `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` |
| `tailwind-design-system` | Tailwind v4 CSS-first; the repo's shipped tokens outrank its starter theme |
| `daisyui` | Colour rule 10 (`primary` once per page) and usage rules 2/7. Drove two changes in commit A |
| `agent-browser` | Optional, for driving a real browser by hand |

---

## 7. Vision tests -- Playwright browser against port 5000

The owner asks for visual verification through a real browser on the running app.

**Launch it:**

```powershell
# starts the ss-postgres container if needed, then Flask on 5000
& 'C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe' scripts/dev/dev_start.py
```

or `python app.py` directly. Then drive `http://127.0.0.1:5000/` with a
Playwright browser and inspect the rendered pages: `/`, `/results?job_id=...`,
`/heatmap`, `/unmatched?job_id=...`, `/loading`, and the error page.

**Caution, and it is a repo rule:** AGENTS.md Anti-Pattern Registry item 5 says
the owner runs the app on **5000 in their own terminal** and forbids competing
for that port. Confirm 5000 is free before you bind it.

**The automated gate does NOT use 5000.** `scripts/dev/frontend_gate.py` starts
its own Flask app on an **ephemeral loopback port** and shuts it down in a
`finally`. It owns its server lifecycle. If you start a server, you own stopping
it; never leave one listening past the task.

Both engines matter: the gate runs **chromium fully** and uses **firefox as a
static-assets-and-tokens canary** (`BROWSER_SCOPES` in `frontend_gate.py`).

---

## 8. What comes after the commit

`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` is
the plan, and its **Progress** section owns the status. Its phases:

- **Phase 2 -- document reconciliation.** Two live conflicts:
  1. `docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`
     still says **"stacked, full-width reason sections"**. The owner overruled
     that on 2026-09-11 in favour of **side-by-side**, and the shipped page is
     side-by-side. `PLAYBOOK.md` Section 3 was already corrected to say so, so
     the spec is now the only stale voice.
  2. `docs/design/RECONCILIATION.md` is stale in two places: D-15 (the heatmap
     gap is 2px, not 3px) and D-16 (both index grid bands ship, not just one).
  Also `DESIGN.md`'s four wrong claims, and the token-name corrections the audit
  records.
- **Phase 3 -- the audit's incidental defects:** the two `font-weight: 500`s in
  `static/css/shell.css:575,610`; the dead `is-ready` in `page_motion.js`; the
  undefined `--ss-shadow-card` in `heatmap.css`; the 140 ms and 0.25s/150 ms
  coupling pairs.
- **Phase 4 -- WP-8 core.** Retire `global.css` and the `.dark-mode` write.
  **TRAP:** `heatmap.js`'s `initDarkModeObserver()` observes `document.body` for
  `class` and must move to `data-theme` on `documentElement` **in the same
  change**, or zero-count heatmap cells silently keep the old theme's colour and
  no gate watches it.
- **Phase 5 -- WP-8 close-out**, including the mandated frontend and
  accessibility audit and the deterministic Bootstrap-removal grep.

---

## 9. Key artifact map

| Fact | Owner |
| --- | --- |
| Rules, commit format, anti-patterns | `AGENTS.md` |
| Next action, execution log | `PLAYBOOK.md` Sections 3-4 |
| Batch scope, WPs, acceptance criteria | `BATCH21_DEFINITION.md` |
| Test count, structure, dependency graph | `.claude/SESSION_CONTEXT.md` |
| Design system, code-derived and shipped | `DESIGN.md` |
| Audit of the design handoff against the code | `docs/design/designsystemaudit.md` (do not edit) |
| Repo overrides of the design handoff | `docs/design/RECONCILIATION.md` |
| Open defects and their status | `FINDINGS.md` (F-B21-51 is yours) |
| The plan for what remains, and its progress | `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` |
| Doc navigation and known traps | `docs/AGENT_DOC_MAP.md` |
| Declared duplicated facts (DOC009-011) | `.docsync.toml` |

---

## 10. One-line summary

Two commits are owed, in this order. First commit the staged F-B21-51 slice-1
work (all four gates were observed green on exactly that state). Then commit the
unstaged architecture-diagram rebuild, re-staging `PLAYBOOK.md` so its diagram
entry travels with it. Then reconcile the spec-versus-ruling layout conflict
before touching WP-8.

Two habits from this session will save you a round: keep `# noqa: F401` on any
facade re-export, or the next `ruff --fix` breaks collection again; and re-run
the hooks after any hook that modified a file, because a modifying hook reports
`Failed` and only an unmodified run is evidence.


