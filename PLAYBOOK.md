# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 15 is active.** Alignment, Hardening, and Handoff.
  Definition: `BATCH15_DEFINITION.md` (repo root, active).
- **Current mode:** Batch 15 execution.
  - WP-1: align Python version to 3.13 in Dockerfile + CI, fix deploy wording. **Done.**
    - Deviation: docsync `--fix` SESSION_CONTEXT write bug discovered and fixed (+1 test, 311 total). **Done.**
  - WP-2: fix stale counts in README and SESSION_CONTEXT.
  - WP-3: reject malformed `### ` headings in docsync parser + 3 tests.
  - WP-4: add 6 negative/boundary tests for docsync renderer and logic.
  - WP-5: replace HANDOFF_PROMPT.md with minimal stable cross-agent template.
  - WP-6: add proposal discipline and anti-pattern rules to AGENTS.md.
- **Batch 14 is complete.** All 5 WPs done + staleness fix side-task.
  Definition: `docs/history/definitions/BATCH14_DEFINITION.md`.
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days
    (Last.fm-only, lighter background task).
- Do not start feature work (top songs, heatmap) until owner defines scope
  and assigns a batch number.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-03-02 - Align Python version, CI triggers, and deploy wording (Batch 15 WP-1)

**Scope:** `Dockerfile`, `.github/workflows/test.yml`, `DEVELOPMENT.md`,
`docs/history/definitions/BATCH14_DEFINITION.md`, `BATCH15_DEFINITION.md`.

**Plan vs implementation:**
- Planned: align Python 3.11 in Dockerfile/CI to 3.13; fix deploy wording
  ambiguity in DEVELOPMENT.md; fix BATCH14_DEFINITION.md header.
- Implemented: all planned changes plus two additional fixes discovered
  during execution: added `wip/**` push triggers to CI so every commit on
  working branches is validated, and created `BATCH15_DEFINITION.md` (which
  should have existed before WP-1 began).

**Deviations:**
- BATCH15_DEFINITION.md was created after WP-1 commit instead of before it.
  This violated the convention that definition files precede work. The CI
  trigger addition (`wip/**`) was not in the original WP-1 scope but was
  required to meet the owner's requirement that every push triggers CI.
- PLAYBOOK Section 3+4 were not updated with WP-1 commit. This log entry
  corrects that omission retroactively.

**Validation:**
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `pre-commit run --all-files` (pass, all 8 hooks)
- `python scripts/doc_state_sync.py --check` (pass)
- CI triggered on push to `wip/pc-snapshot` after `wip/**` trigger added

**Forward guidance:**
- Push each WP commit individually so CI validates each one separately.
- Update PLAYBOOK Section 3+4 and run `doc_state_sync.py --fix` before
  every commit, not after.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-03-02 - Session findings and handoff notes (side-task)

**Scope:** Observations from Batch 15 WP-1 execution session, documented for
next-agent orientation.

**Findings:**
1. **docsync `--fix` SESSION_CONTEXT write bug (fixed):** `cli.py` computed the
   correct STATUS block but never wrote it. Fixed in commit `67fa1dc`. AGENTS.md
   cross-validation section updated to reflect corrected behavior.
2. **Deviation tag routing:** Headings with non-standard tags like
   `(Batch 15 WP-1 deviation)` do NOT match `ENTRY_BATCH_RE` regex
   (`\(Batch\s+(\d+)\s+WP-\d+\)`). They are routed outside CURRENT-BATCH
   markers as untagged entries. This is correct behavior -- use standard
   `(Batch N WP-X)` tags only for entries that should stay inside markers.
3. **Mid-batch handoff discipline (added):** AGENTS.md now requires PLAYBOOK
   Section 3 to reflect true state at all times, not just after commits.
4. **SESSION_CONTEXT Section 7 is stale:** Shows 307 tests across old counts.
   Actual: 311 tests across 18 files. WP-2 will fix this.
5. **README.md is stale:** Says 257 tests, lists incomplete pre-commit hooks,
   project structure test section outdated. WP-2 will fix this.
6. **HANDOFF_PROMPT.md is stale:** References deleted branch, old audit, old
   tasks. WP-5 will replace it; interim handoff written for this transition.

**Forward guidance:**
- Next agent should start with WP-2 per BATCH15_DEFINITION.md execution order.
- Always use standard `(Batch N WP-X)` tags for batch log entries.
- Run `doc_state_sync.py --fix` after every PLAYBOOK Section 4 edit.

### 2026-03-02 - Fix docsync --fix not writing SESSION_CONTEXT STATUS block (Batch 15 WP-1 deviation)

**Scope:** `scripts/docsync/cli.py`, `tests/test_docsync_cli.py`, `AGENTS.md`.

**Plan vs implementation:**
- Planned: during WP-1 execution, discovered that `doc_state_sync.py --fix`
  computes the correct STATUS block for SESSION_CONTEXT but never writes it
  to disk. AGENTS.md line 138-139 claimed the script "Refreshes the
  machine-managed DOCSYNC:STATUS block" but the code only warned on staleness
  without writing. This was a bug, not a design choice.
- Implemented: modified `cli.py` so `--fix` writes the refreshed STATUS block
  to SESSION_CONTEXT when stale. `--check` continues to warn-only (does not
  fail) because SESSION_CONTEXT is gitignored and should not block commits.
  Updated AGENTS.md cross-validation section to reflect corrected behavior.
  Added 1 new test (`test_fix_refreshes_session_context_status_block`) and
  updated the stale-warning assertion text in existing test.

**Deviations:**
- This fix was not in the Batch 15 definition. It was discovered during WP-1
  when the agent attempted to run `--fix` and found SESSION_CONTEXT unchanged.
  The fix is scoped to the bug and does not change any other docsync behavior.

**Validation:**
- `pytest tests/test_docsync_cli.py -v` (**19 passed**)
- `pytest -q` (**311 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --fix` (wrote SESSION_CONTEXT)
- `python scripts/doc_state_sync.py --check` (pass, no stale warning)
- `pre-commit run --all-files` (pass, all 8 hooks)

**Forward guidance:**
- After any PLAYBOOK Section 4 edit, run `doc_state_sync.py --fix` and verify
  SESSION_CONTEXT STATUS block was updated. The script now handles this
  automatically.

### 2026-02-27 - Revalidate audit findings and prepare next-agent packet (side-task)

**Scope:** `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md`,
`tests/test_docsync_logic.py` (format-only), repo-wide quality gates.

**Plan vs implementation:**
- Planned: verify previously reported findings against current branch state,
  refresh stale assertions, and produce implementation-ready guidance for the
  next agent handoff.
- Implemented: re-ran full validations, updated stale test baseline and
  resolved-item status in the audit report, and added a scoped next-agent
  implementation packet with acceptance criteria.

**Deviations:**
- No behavioral code changes were required; only audit/report updates plus
  formatter-normalized whitespace in `tests/test_docsync_logic.py`.

**Validation:**
- `pre-commit run --all-files` (pass)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Execute the next-agent packet in commit-sized slices: test-module split,
  low-risk orchestrator extraction, then CI/session policy wording alignment.

### 2026-02-27 - Harden docsync non-happy-path coverage + path guidance (side-task)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`AGENTS.md`, `PLAYBOOK.md`.

**Plan vs implementation:**
- Planned: enforce anti-happy-path discipline for docsync archive-link and
  migration handling, and remove path ambiguity between untagged archive,
  per-batch logs, and definitions.
- Implemented: added adversarial tests for `docs/logarchive` link validation
  (exists/missing) and for `--split-archive` missing-input failure (`exit 2`),
  plus explicit archive/log/definition lookup guidance in AGENTS and PLAYBOOK.

**Deviations:**
- One assertion was adjusted to be path-separator-agnostic on Windows
  (`PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` substring) after first run exposed
  slash-vs-backslash brittleness.

**Validation:**
- `pytest -q tests/test_docsync_logic.py tests/test_docsync_cli.py`
  (**57 passed**)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Keep new docsync tests behavior-focused (real inputs + failure paths), not
  mock-call-only checks, when adding future archive-routing rules.
