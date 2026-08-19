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

**In scope.** Exactly these 13 modules. The list is closed. Do not add to it,
and do not drop from it.

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

**Matrix size:** 13 modules x 10 principles = **130 cells**. There is no
permission to cut coverage. If the audit cannot fit a single session, split it
across sessions and say so in the report -- do not drop modules. A report that
silently covers less than 130 cells implies coverage it does not have.

## 2a. Provenance (record before grading, publish in the report)

The report must open with a provenance block. Fill it from live commands, not
from this charter:

```bash
git rev-parse --abbrev-ref HEAD          # audited branch
git rev-parse HEAD                       # exact SHA graded
git status --porcelain                   # must be empty, or list what is dirty
git ls-files 'scrobblescope/*.py' app.py # confirm the module list above
```

A grade is a claim about one tree. Without the SHA the matrix cannot be
rechecked, and every cell becomes unfalsifiable.

**Staleness warning:** Batch 21 WP-7 modifies `routes.py` and `orchestrator.py`.
Grades for those two modules expire when WP-7 lands. Say so in the report next
to their rows rather than leaving a reader to discover it.

## 3. The ten principles (grade each)

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
  since the 2026-02 audits, that is `git log --since=2026-03-01 -- <module>`.
  Judge whether touched code was left cleaner, not whether the module is
  clean in absolute terms. Without a window this principle grades the whole
  history of the file, which is not what it means.

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

   ```bash
   # longest functions, by definition, across the in-scope set
   git ls-files 'scrobblescope/*.py' app.py | xargs awk '/^(async )?def |^class /{...}'
   # broad catches, with their real locations
   git grep -n "except Exception" -- 'scrobblescope/*.py' app.py
   ```

   Record the command and its output in the report. The known-largest
   functions are `_fetch_and_process` in `orchestrator.py`, `results_loading`
   in `routes.py`, and `_fetch_and_process_heatmap` in `heatmap.py` -- locate
   them by name, not by line number. F-MAS-4 tracks the broad-catch count; the
   audit grades whether each catch is justified, which F-MAS-4 never did.
4. Fill the 13-module x 10-principle matrix. Grade A/B/C/D per cell with a
   one-line evidence citation (`file:line`). "Not applicable" is a valid cell
   value (for example, Composition over Inheritance in a module with no
   classes) -- grade what exists, and say why it does not apply.
5. Apply the rubric in Section 5a. Every C or D cell either maps to an
   existing finding or becomes a net-new one, per Section 5b.
6. Answer two summary questions in prose: (a) which principle is weakest
   repo-wide and what single change would most improve it; (b) has code
   quality drifted since the 2026-02 audits, held, or improved -- with
   evidence, and reckoning with `REPOSITORY_SYNTHESIS_2026-08-11.md` rather
   than treating February as the last word.
7. Collect test-vacuity evidence while reading. Tests are not graded cells,
   but `AGENT_NOTES.md` mandates that every test must fail if the function
   under test is deleted. Any test that would survive deletion of its subject
   is a net-new finding in its own right, filed against the module it covers.

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

The B/C line is the judgment call this rubric exists to constrain: **B is an
exception, C is a pattern.** If you can point at one place, it is B. If you
would have to point at several, or at the way the module is laid out, it is C.
When genuinely torn, grade C and let the finding be closed as no-action --
an over-raised finding is cheap to decline, an under-raised one is invisible.

## 5b. What happens to a C or D cell

Each C or D cell resolves exactly one of three ways:

1. **Maps to an open finding.** Cite the F-ID. No new entry.
2. **Maps to a finding that is resolved or no-action.** Do **not** cite it as
   live evidence, and do **not** re-raise it. Instead write a net-new finding
   that says the earlier fix did not hold, and cite the old F-ID as history.
   A `Status: resolved` finding cannot be the standing explanation for a
   present-tense defect.
3. **Nothing covers it.** Write a net-new F-SWE-N finding per `AGENTS.md`
   Finding-Writing Rules (heading, one-sentence problem, `Status:`, and
   `Source: SWE_PRINCIPLES_AUDIT`).

## 6. What blocks the migration

This audit is read-only, but it is not consequence-free. It runs immediately
before Batch 21 WP-1, and finishing it is not the same as passing it.

Classify every net-new finding, then apply this policy:

| Finding | Effect on WP-1 |
|---|---|
| **P0** by the FINDINGS.md severity key | **Stop.** Fix before WP-1 begins. |
| Correctness defect in a module any Batch 21 WP modifies -- currently `routes.py` and `orchestrator.py` via WP-7 | **Stop.** Fix or get an explicit owner waiver before WP-1 begins. |
| P1 in a module Batch 21 does not touch | Record and continue. |
| P2 and below | Backlog. |

"Correctness defect" means the module can produce a wrong result, lose data,
leak a resource, or fail to release one -- not that it is untidy. The test is
mechanical on purpose: severity, plus whether the module appears in a WP's
file list. Neither half requires interpretation.

The report must state the verdict in one line near the top: **migration may
proceed**, or **migration is blocked by `<F-IDs>`**. A report that finds blocking
defects and does not say so has failed its main job.

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
sessions and complete all 130 cells** -- record in the report which session
covered which modules. Coverage is not negotiable; session count is.

The earlier version of this charter permitted cutting modules to fit. That
permission is withdrawn: it let a "comprehensive" audit ship incomplete while
still reading as complete, and it handed a scope decision to the executor that
this charter is supposed to have already made.
