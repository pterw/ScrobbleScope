# SWE Principles Audit Charter

**Status:** Chartered 2026-07-31. Amended 2026-08-19 (preflight review before
Batch 21 WP-1). Execution pending. Tracked as FINDINGS.md F-SWE-1.
**Executor contract:** any dedicated, single-purpose agent session (Claude,
Codex, or equivalent) can run this cold. The judgment is front-loaded into
this charter; the executor's job is careful reading, evidence gathering,
and honest grading -- not scope invention.

---

## 1. Bootstrap

Follow `AGENTS.md` "Session Bootstrap" first -- that list names itself as
the first file to read. This charter is the work order; PLAYBOOK Section 3
status does not change while the audit runs (it is a read-only side-task).

## 2. Scope

**In scope.** The 13 graded modules below. The list is closed -- do not add to
it and do not drop from it. A fourteenth file, `scrobblescope/__init__.py`, is
listed for completeness and is not graded.

| Module | Graded |
|---|---|
| `app.py` | yes |
| `scrobblescope/cache.py` | yes |
| `scrobblescope/config.py` | yes |
| `scrobblescope/domain.py` | yes |
| `scrobblescope/errors.py` | yes |
| `scrobblescope/heatmap.py` | yes |
| `scrobblescope/lastfm.py` | yes |
| `scrobblescope/orchestrator.py` | yes |
| `scrobblescope/repositories.py` | yes |
| `scrobblescope/routes.py` | yes |
| `scrobblescope/spotify.py` | yes |
| `scrobblescope/utils.py` | yes |
| `scrobblescope/worker.py` | yes |
| `scrobblescope/__init__.py` | **no -- empty file, see rule below** |

**Empty-module rule:** a module with no statements other than a docstring gets
no matrix row. It is listed above so its absence from the matrix is a recorded
decision, not an oversight. Confirm it is still empty at audit time; if it has
gained content, grade it and say so in the report.

**Explicitly OUT of scope, each for a stated reason:**

- `static/js/` and all templates and CSS -- Batch 21 rewrites them. Auditing
  them now wastes the work. This exclusion is paid for by the WP-8 frontend
  audit that `BATCH21_DEFINITION.md` now requires; it is no longer optional.
- `scripts/docsync/` -- carries the freshest dedicated audits and is not on the
  Batch 21 migration path. Its known boundaries are already tracked as
  F-DOCSYNC-6 and F-DOCSYNC-7 in `FINDINGS.md`.
- `scripts/dev/` -- the worktree-guard family, shipped and reviewed through
  PR #169 and PR #170. Its size problems are already tracked as F-WORKTREE-3
  and F-WORKTREE-4. Named here because the earlier charter left it neither in
  nor out.
- Tests are read for evidence (vacuity, coverage) but are not graded cells.
  Section 5 says where that evidence lands.
- **No code changes of any kind.** This is a read-only audit. Findings become
  F-SWE-N entries; fixes are future batch work.

**Matrix size:** 13 graded modules x the principle count in `AGENT_NOTES.md`.
That count is ten at this writing, giving 130 cells -- confirm it at audit time
per Section 3 and use the live product, not the number written here. There is
no permission to cut coverage. If the audit cannot fit a single session, split
it across sessions and say so in the report -- do not drop modules. A report
covering fewer cells than that product, without saying so, implies coverage it
does not have.

## 2a. Provenance (record before grading, publish in the report)

The report must open with a provenance block. Fill it from live commands, not
from this charter:

```bash
git rev-parse --abbrev-ref HEAD          # audited branch
git rev-parse HEAD                       # exact SHA graded
git status --porcelain                   # must be empty before grading starts
git ls-files 'scrobblescope/*.py' app.py # confirm the module list above
```

A grade is a claim about one tree. **Grade a clean worktree only.** If
`git status --porcelain` is not empty, stop and reconcile before grading: a SHA
cannot reproduce uncommitted content, so a matrix built over a dirty tree is
unfalsifiable however carefully its cells cite lines. Recording the dirt is not
a substitute for removing it.

**Staleness warning:** Batch 21 WP-7 modifies `routes.py` and `orchestrator.py`.
Grades for those two modules expire when WP-7 lands. Say so in the report next
to their rows rather than leaving a reader to discover it.

## 3. The mandated principles (grade each)

The canonical list and its definitions live in `AGENT_NOTES.md` Owner
Preferences. Grade every principle named there, using that wording --
do not keep a second copy in this file.

**Count check:** that list currently names ten principles, and this charter's
cell arithmetic assumes ten. Count them at audit time. If the count has
changed, the matrix width changes with it -- report the new count and the new
cell total rather than forcing ten.

Two need audit-specific method:

- **Clean Architecture:** check dependencies against the acyclic graph
  in SESSION_CONTEXT Section 4.
- **Boy Scout Rule:** assess over a fixed window -- commits to each module
  since the 2026-02 audits, that is
  `git log -p --since=2026-03-01 -- <module>`. Read the patches, not the
  subject lines: this principle is about what each change left behind, which a
  list of commits cannot show. Judge whether touched code was left cleaner,
  not whether the module is clean in absolute terms. Without a window this
  principle grades the whole history of the file, which is not what it means.

## 4. Differential baseline (do NOT re-report)

Re-reporting a known item is audit failure, not thoroughness. The baseline is
not a list to memorise -- it is a corpus to read:

1. **All of `FINDINGS.md`.** Every open item, whatever its severity.
2. **All of `docs/history/findings/FINDINGS_ARCHIVE.md`.** Resolved and
   no-action items stay part of the baseline and must not be re-raised.
3. **Every report under `docs/history/reports/`** dated 2026-02 or later.
   As of this amendment that includes `AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md`
   (lines 113-136 list prior runtime SoC/DRY/code-smell findings),
   `ROUTES_SOC_AUDIT_2026-02-21.md` (Section 4 "What was NOT changed"
   documents deliberate declines -- respect them),
   `TEST_QUALITY_AUDIT_2026-02-21.md`, `GUARD_HARDENING_2026-08-11.md`, and
   `REPOSITORY_SYNTHESIS_2026-08-11.md`. List the directory rather than
   trusting this sentence to stay current.

Read the corpus by listing those locations, not by matching the ID list an
earlier version of this charter carried. That list was closed and had already
gone stale: it omitted F-B21-1, F-DATA-1, F-WORKTREE-3/4/5, F-DOCSYNC-6/7 and
F-AUDIT-1, several of which sit in modules this audit grades.

**Standing design decisions are choices, not findings:** F-LOAD-3/4/5 and the
`AGENT_NOTES.md` Architectural Constraints -- in-memory REQUEST_CACHE,
single-worker JOBS dict, TTL-on-write cache, ProactorEventLoop guard.

The audit's value is NET-NEW findings and a defensible per-module grade,
not volume.

## 5. Method

1. Read the baseline corpus in Section 4 first.
2. Record the provenance block from Section 2a.
3. Discover hotspots live rather than trusting written counts. The previous
   version of this charter hardcoded line numbers and an exception count that
   had already drifted; `AGENTS.md` anti-pattern 10 forbids repeating a number
   without re-measuring it. Use symbol-based discovery:

   Run both commands in Section 5c and record each command with its output in
   the report. The known-largest functions are `_fetch_and_process` in
   `orchestrator.py`, `results_loading` in `routes.py`, and
   `_fetch_and_process_heatmap` in `heatmap.py` -- locate them by name, never
   by line number. F-MAS-4 tracks the broad-catch count; the audit grades
   whether each catch is justified, which F-MAS-4 never did.
4. Fill the matrix -- 13 graded modules by the live principle count from
   Section 3. Grade A/B/C/D per cell with a
   one-line evidence citation (`file:line`). "Not applicable" is a valid cell
   value (for example, Composition over Inheritance in a module with no
   classes) -- grade what exists, and say why it does not apply.
5. Apply the rubric in Section 5a. Every C or D cell either maps to an
   existing finding or becomes a net-new one, per Section 5b.
6. Answer two summary questions in prose: (a) which principle is weakest
   **across the audited runtime modules** -- not repo-wide, because this audit
   deliberately excludes the frontend, both script directories, and tests as
   graded subjects, and cannot support a conclusion about code it never read;
   name the single change that would most improve it. (b) Has code quality
   drifted since the 2026-02 audits, held, or improved -- with evidence, and
   reckoning with `REPOSITORY_SYNTHESIS_2026-08-11.md` rather than treating
   February as the last word. Scope this answer the same way.
7. Collect test-vacuity evidence while reading. Tests are not graded cells,
   but `AGENT_NOTES.md` mandates that every test must fail if the function
   under test is deleted. Any test that would survive deletion of its subject
   is a net-new finding in its own right, filed against the module it covers.

## 5c. Discovery commands

These sit at the left margin deliberately. A shell heredoc ends only when its
terminator starts at column 0, so if these were indented inside the numbered
list above, copying them would fail with `IndentationError`. Run them as they
appear, from the repository root, and paste the real output into the report.

Longest function definitions, parsed with `ast` rather than a regex -- a
line-matching pattern miscounts decorators, nested definitions and multi-line
signatures, and the count is the entire point:

```bash
python - <<'EOF'
import ast, subprocess
files = subprocess.run(["git", "ls-files", "scrobblescope/*.py", "app.py"],
                       capture_output=True, text=True).stdout.split()
rows = []
for path in files:
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rows.append((node.end_lineno - node.lineno + 1, path, node.lineno, node.name))
print(f"{len(files)} files, {len(rows)} function definitions")
for length, path, line, name in sorted(rows, reverse=True)[:15]:
    print(f"{length:4d}  {path}:{line}  {name}")
EOF
```

Broad exception catches, with their real locations:

```bash
git grep -n "except Exception" -- 'scrobblescope/*.py' app.py
```

Both were run on 2026-08-19 against `bb187ae` and worked as written. The first
reported 14 files and 99 function definitions, with the three known hotspots at
151, 112 and 109 lines. The superseded version of this charter called them
"~153", "~115" and "~111" -- a live demonstration of why anti-pattern 10
forbids repeating a measured number without re-measuring it. Do not trust the
figures in this paragraph either; they are here to show the drift, not to save
you the run.

## 5a. Grading rubric

Grades are not vibes. A cell's grade is determined by what the evidence shows,
and the C boundary matters most because it is the finding threshold.

| Grade | Meaning | Test to apply |
|---|---|---|
| **A** | The principle is upheld throughout the module. | No counter-example found after reading the module whole. |
| **B** | Upheld, with a local exception that is deliberate or harmless. | A counter-example exists, but it is contained, documented, or cheaper than the fix. State it; do not raise a finding. |
| **C** | Violated in a way that costs real maintainability now. | A counter-example a maintainer would have to work around. **Becomes a finding.** |
| **D** | Violated structurally; the module is organised against the principle. | The violation is the module's shape, not an instance in it. **Becomes a finding.** |
| **N/A** | The principle has no purchase on this module. | Say why in one line (for example: no classes, so Composition over Inheritance cannot apply). |

The B/C line is the judgment call this rubric exists to constrain, and it turns
on **cost, not count**. One occurrence can be C: a single leaked resource or a
single silently wrong result earns C on its own. Five occurrences can stay B if
each is contained and none costs a maintainer anything today. Ask what the
violation costs right now -- if the answer is "nothing, and it is written
down", that is B; if a maintainer has to work around it, that is C.

When genuinely torn, say so in the cell and grade the lower severity. Do not
raise a finding to be safe. Section 4 states that this audit's value is net-new
findings and not volume, and a speculative finding costs a reviewer as much
attention as a real one while teaching the next reader to skim the list.

## 5b. What happens to a C or D cell

Each C or D cell resolves exactly one of these four ways:

1. **Maps to an open finding.** Cite the F-ID. No new entry.
2. **Maps to a finding marked resolved.** The defect has recurred, so the
   earlier fix did not hold. Write a net-new finding saying exactly that and
   cite the old F-ID as history. A `Status: resolved` finding can never be the
   live explanation for a present-tense defect.
3. **Maps to a finding marked no-action.** Resolved and no-action are not the
   same case and do not share a rule. Check whether the recorded rationale
   still holds:
   - **Still applies** -- do not re-raise. Note the F-ID in the cell and move
     on. An unchanged condition that was deliberately accepted is not a
     finding just because an audit walked past it again.
   - **Assumptions have materially changed** -- write a net-new finding that
     explains the delta (what the rationale assumed, what is now true) and
     cite the old F-ID.
4. **Nothing covers it.** Write a net-new F-SWE-N finding per `AGENTS.md`
   Finding-Writing Rules (heading, one-sentence problem, `Status:`, and
   `Source: SWE_PRINCIPLES_AUDIT`).

## 6. What blocks the migration

This audit is read-only, but it is not consequence-free. It runs immediately
before Batch 21 WP-1, and finishing it is not the same as passing it.

**This gate applies only to net-new findings produced by this audit.** Existing
findings retain their recorded severity and disposition unless the owner
reclassifies them. That boundary is deliberate, and F-B21-1 is the case that
proves it needs stating: a leaked job slot is a resource-release defect in
`orchestrator.py` and `heatmap.py`, and WP-7 modifies `orchestrator.py`, so
reading this gate as covering existing findings would block WP-1 today. The
owner triaged that item as a P1 next-batch candidate with more context than
this audit has. An audit does not silently re-triage decisions already made.

Classify every net-new finding, then apply this policy:

| Net-new finding | Effect on WP-1 |
|---|---|
| **P0** by the FINDINGS.md severity key | **Stop.** Fix before WP-1 begins. |
| Correctness defect in a module any Batch 21 WP modifies -- currently `routes.py` and `orchestrator.py` via WP-7 | **Stop.** Fix, or obtain an explicit owner waiver, before WP-1 begins. |
| P1 maintainability, not correctness, in a module Batch 21 modifies | **Record and continue**, and name it in the verdict line. WP-7 touches that code anyway, so it is cheapest to fix there -- reference it from the WP-7 commit. |
| P1 in a module Batch 21 does not touch | Record and continue. |
| P2 and below | Backlog. |

"Correctness defect" means the module can produce a wrong result, lose data,
leak a resource, or fail to release one -- not that it is untidy. The test is
mechanical on purpose: severity, plus whether the module appears in a WP's
file list. Neither half requires interpretation.

The report must state the verdict in one line near the top: **migration may
proceed**, or **migration is blocked by `<F-IDs>`**. A report that finds blocking
defects and does not say so has failed its main job.

If the audit concludes that an *existing* finding should block WP-1 -- F-B21-1
or any other -- it does not act on that conclusion. It records the
recommendation in the verdict section, with its reasoning, and leaves the
decision to the owner.

## 7. Output contract

- Report: `docs/history/reports/SWE_PRINCIPLES_AUDIT_<YYYY-MM-DD>.md` -- the
  provenance block, the migration verdict, the matrix, per-cell evidence, the
  two prose answers, and a net-new findings list.
- FINDINGS.md: append net-new F-SWE-N entries (start at F-SWE-2;
  F-SWE-1 is this charter's tracking entry). Update F-SWE-1 to
  `Status: resolved -- report at <path>`.
- **Retire this charter in the same commit.** Change the Status line at the
  top of this file to `Executed <date>, report at <path>`. Leaving it as
  "execution pending" makes this file false the moment F-SWE-1 closes.
- PLAYBOOK Section 4: one dated side-task entry, placed and tagged per
  AGENTS.md Side-Task Handling.
- Validation gates per AGENTS.md Commit Rules (docs-only change; all
  three commands must still pass).
- Commit subject: `docs(audit): add SWE principles audit report and
  F-SWE findings` (imperative mood per AGENTS.md Commit Rules).
  Do not push without owner instruction.

## 8. Budget guidance

Target a single focused session. If the work does not fit, **split it across
sessions and complete every cell** -- 13 graded modules by the live principle
count -- and record in the report which session covered which modules.
Coverage is not negotiable; session count is.

The earlier version of this charter permitted cutting modules to fit. That
permission is withdrawn: it let a "comprehensive" audit ship incomplete while
still reading as complete, and it handed a scope decision to the executor that
this charter is supposed to have already made.
