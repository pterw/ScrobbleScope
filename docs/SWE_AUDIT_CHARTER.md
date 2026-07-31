# SWE Principles Audit Charter

**Status:** Chartered 2026-07-31, execution pending. Tracked as FINDINGS.md
F-SWE-1.
**Executor contract:** any dedicated, single-purpose agent session (Claude,
Codex, or equivalent) can run this cold. The judgment is front-loaded into
this charter; the executor's job is careful reading, evidence gathering,
and honest grading -- not scope invention.

---

## 1. Bootstrap

Follow `AGENTS.md` "Session Bootstrap" first (it is step 1 of its own
order). This charter is the work order; PLAYBOOK Section 3 status does not
change while the audit runs (it is a read-only side-task).

## 2. Scope

**In scope (Python only):**

- `scrobblescope/` -- all 13 modules (~3,100 LOC)
- `app.py` (~150 LOC)
- `scripts/docsync/` -- parser/renderer/logic/cli/models (~1,000 LOC)

**Explicitly OUT of scope:**

- `static/js/` (~1,860 LOC) and all templates/CSS -- Batch 21 rewrites
  them; auditing them before it ships wastes the work. A follow-up
  charter can add them post-Batch-21.
- Tests are read for evidence (vacuity, coverage) but are not graded
  cells in the matrix.
- **No code changes of any kind.** This is a read-only audit. Findings
  become F-SWE-N entries; fixes are future batch work.

## 3. The ten principles (grade each)

The canonical list and its definitions live in `AGENT_NOTES.md` Owner
Preferences. Grade every principle named there, using that wording --
do not keep a second copy in this file. Two need audit-specific method:

- **Clean Architecture:** check dependencies against the acyclic graph
  in SESSION_CONTEXT Section 4.
- **Boy Scout Rule:** assess via git history of the files each change
  touched.

## 4. Differential baseline (do NOT re-report)

These are already found, tracked, or deliberately declined. Re-reporting
any of them is audit failure, not thoroughness:

- Open findings: F-MAS-1 through F-MAS-8, F-B20-2 (orchestrator
  decomposition -- the single biggest known SoC/SRP item), F-DOCSYNC-1
  through F-DOCSYNC-4, F-B18-2/3/4/5/10 (deferred block), F-LOAD-1/2.
- `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md` (lines 113-136
  list the prior runtime SoC/DRY/code-smell findings).
- `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md` -- Section 4 "What was
  NOT changed" documents deliberate declines; respect them.
- `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md`.
- Standing design decisions (F-LOAD-3/4/5, AGENT_NOTES.md Architectural
  Constraints): in-memory REQUEST_CACHE, single-worker JOBS dict,
  TTL-on-write cache, ProactorEventLoop guard. These are choices, not
  findings.

The audit's value is NET-NEW findings and a defensible per-module grade,
not volume.

## 5. Method

1. Read the baseline documents in Section 4 first.
2. Examine pre-identified hotspots before anything else:
   - `orchestrator.py:719` `_fetch_and_process` (~153 lines)
   - `routes.py:405` `results_loading` (~115 lines)
   - `heatmap.py:89` `_fetch_and_process_heatmap` (~111 lines)
   - the 17 `except Exception` sites (routes 5, orchestrator 4, cache 2,
     lastfm 2, utils 2, heatmap 1, worker 1) -- F-MAS-4 tracks the
     count; the audit grades whether each catch is justified, which
     F-MAS-4 never did.
3. Fill a 10-principle x module grading matrix. Grade A/B/C/D per cell
   with a one-line evidence citation (`file:line`). "Not applicable"
   is a valid cell value (e.g., Composition over Inheritance in a
   module with no classes) -- grade what exists.
4. For every C or D cell, either map it to an existing finding (cite the
   F-ID, no new entry) or write a net-new F-SWE-N finding per AGENTS.md
   Finding-Writing Rules (heading, one-sentence problem, Status, Source:
   `SWE_PRINCIPLES_AUDIT`).
5. Answer two summary questions in prose: (a) which principle is weakest
   repo-wide and what single change would most improve it; (b) has code
   quality drifted since the 2026-02 audits, held, or improved --
   with evidence.

## 6. Output contract

- Report: `docs/history/SWE_PRINCIPLES_AUDIT_<YYYY-MM-DD>.md` -- the
  matrix, per-cell evidence, the two prose answers, and a net-new
  findings list.
- FINDINGS.md: append net-new F-SWE-N entries (start at F-SWE-2;
  F-SWE-1 is this charter's tracking entry). Update F-SWE-1 to
  `Status: resolved -- report at <path>`.
- PLAYBOOK Section 4: one dated side-task entry, placed and tagged per
  AGENTS.md Side-Task Handling.
- Validation gates per AGENTS.md Commit Rules (docs-only change; all
  three commands must still pass).
- Commit subject: `docs(audit): SWE principles audit report + F-SWE
  findings`. Do not push without owner instruction.

## 7. Budget guidance

Target a single focused session. If module coverage must be cut to fit,
cut `scripts/docsync/` first (it has the freshest dedicated audit) and
name every skipped module in the report's scope section. A report that
does not list what it skipped implies coverage it does not have, which
defeats the purpose of the audit.
