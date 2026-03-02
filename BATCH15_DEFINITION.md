# BATCH15: Alignment, Hardening, and Handoff

**Status:** In Progress
**Branch:** `wip/pc-snapshot`
**Baseline:** 310 tests passing

---

## Context

The repo has version drift (Dockerfile/CI on Python 3.11, local dev on 3.13),
stale doc counts (README says 257 tests), and a stale handoff prompt referencing
a deleted branch. The docsync parser silently swallows malformed `### ` headings,
risking data loss during rotation. The renderer and logic modules lack adversarial
tests. AGENTS.md has no explicit rules preventing SoC/DRY violations or monolith
creation by future agents.

---

## 1. Scope and goals

**Primary goals:**
- Align Python version across Dockerfile, CI, and documentation (3.13)
- Add CI triggers for working branches so every push is checked
- Fix all stale counts and references in README and SESSION_CONTEXT
- Harden docsync parser against malformed agent output (silent data loss)
- Add negative/adversarial tests for docsync renderer and logic
- Replace the stale HANDOFF_PROMPT.md with a minimal, stable cross-agent template
- Add explicit proposal discipline and anti-pattern rules to AGENTS.md

**Out of scope:**
- Feature work (top songs, heatmap) -- owner-defined scope required
- Orchestrator modularization -- premature until second pipeline exists
- Coverage increase beyond current ~72%
- Fly.io dashboard configuration (auto-deploy toggle) -- not a repo change
- `pyproject.toml` python-requires pin -- low priority

---

## 2. Work Packages

### WP-1 (P0): Align Python version, CI triggers, and deploy wording

**Goal:** Eliminate the Python 3.11 vs 3.13 mismatch across Dockerfile, CI, and
docs. Add CI push triggers for `wip/**` branches. Fix ambiguous deploy wording.
Fix the BATCH14_DEFINITION.md header.

**Files:**
- `Dockerfile` -- `python:3.11-slim` to `python:3.13-slim`
- `.github/workflows/test.yml` -- `python-version: '3.11'` to `'3.13'`; add
  `wip/**` to push branches; remove `workflow_dispatch`
- `DEVELOPMENT.md` -- Release row: `flyctl deploy (manual, after PR merge to main)`
- `docs/history/definitions/BATCH14_DEFINITION.md` -- header fix

**Acceptance criteria:**
- Dockerfile specifies `python:3.13-slim`
- CI specifies `python-version: '3.13'` and triggers on push to `main` + `wip/**`
- DEVELOPMENT.md Release row contains "manual"
- BATCH14_DEFINITION.md header matches convention
- `pytest -q` passes (310 passed)
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `fix(infra): align Python version to 3.13, add wip branch CI triggers, clarify manual deploy`

---

### WP-2 (P0): Fix stale counts and references in README and SESSION_CONTEXT

**Goal:** Make bootstrap documents match reality so agents start from accurate state.

**Files:**
- `README.md` -- test count 257 to 310; pre-commit hook list to all 8; project
  structure test section to reflect post-Batch-13/14 splits (18 test files)
- `.claude/SESSION_CONTEXT.md` -- Section 2: 307 to 310; Section 7: test table
  to match actual 310 tests across 18 files

**Acceptance criteria:**
- README test references all say 310
- README Code Quality lists all 8 hooks
- README Project Structure test listing matches actual file layout
- SESSION_CONTEXT Section 2 says `**310 passing**`
- SESSION_CONTEXT Section 7 table sums to 310 with 18 files
- `pytest -q` passes (310 passed)
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `docs: update test count to 310, list all 8 pre-commit hooks, fix project structure`

---

### WP-3 (P1): Reject malformed `### ` headings in docsync parser

**Goal:** Make `_parse_entries()` raise `SyncError` for any bare `### ` line in
Section 4 that does not match `ENTRY_HEADING_RE`, closing the silent data loss gap.

**Files:**
- `scripts/docsync/parser.py` -- validation pass in `_parse_entries()`: any line
  matching `r"^###\s+"` not at a collected heading index raises `SyncError`.
  Exclude lines inside fenced code blocks.
- `tests/test_docsync_parser.py` -- 3 new tests:
  - `test_malformed_h3_raises_sync_error`
  - `test_h3_missing_dash_raises_sync_error`
  - `test_h3_inside_code_block_not_rejected`

**Acceptance criteria:**
- `_parse_entries()` raises `SyncError` for bare malformed `### ` lines
- Lines inside fenced code blocks are not falsely rejected
- `pytest tests/test_docsync_parser.py -v` passes with 35 total tests
- `pytest -q` passes (313 passed)
- `python scripts/doc_state_sync.py --check` passes
- `pre-commit run --all-files` passes

**Net tests:** +3
**Commit:** `fix(docsync): reject malformed ### headings in _parse_entries to prevent silent data loss`

---

### WP-4 (P1): Add negative and boundary tests for docsync renderer and logic

**Goal:** Close the adversarial test gap in renderer and logic modules.

**Files:**
- `tests/test_docsync_renderer.py` -- 4 new tests:
  - `test_build_status_block_contradictory_state`
  - `test_build_status_block_zero_batch_number`
  - `test_render_section4_empty_entry_lines`
  - `test_render_archive_empty_prefix`
- `tests/test_docsync_logic.py` -- 2 new tests:
  - `test_dedup_sorted_same_fingerprint_keeps_newest`
  - `test_parse_active_batch_state_conflicting_signals`

**Acceptance criteria:**
- `pytest tests/test_docsync_renderer.py tests/test_docsync_logic.py -v` passes
  with 6 new tests
- `pytest -q` passes (319 passed)
- `pre-commit run --all-files` passes
- No source code changes -- tests only

**Net tests:** +6
**Commit:** `test(docsync): add 6 negative and boundary tests for renderer and logic modules`

---

### WP-5 (P1): Replace HANDOFF_PROMPT.md with minimal stable template

**Goal:** Create a handoff prompt that works across Claude Code, Copilot, Codex,
and Gemini without per-session edits. No branch names, no commit SHAs, no dates.

**Files:**
- `HANDOFF_PROMPT.md` -- full rewrite, under 60 lines

**Acceptance criteria:**
- No branch names, commit SHAs, or date-specific references
- Under 60 lines
- References only AGENTS.md and PLAYBOOK.md as bootstrap
- Contains explicit anti-pattern list
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `docs(handoff): replace stale handoff prompt with minimal stable cross-agent template`

---

### WP-6 (P2): Add proposal discipline and anti-pattern rules to AGENTS.md

**Goal:** Codify the patterns that prevent SoC/DRY violations, monolith creation,
test bloat, and undocumented refactoring.

**Files:**
- `AGENTS.md` -- two new sections after Batch Close-Out Procedure:
  - `## Proposal and Design Rules` (4 rules)
  - `## Anti-Pattern Registry` (3 items)

**Acceptance criteria:**
- AGENTS.md contains both new sections with numbered rules
- `pre-commit run --all-files` passes
- `python scripts/doc_state_sync.py --check` passes

**Net tests:** +0
**Commit:** `docs(agents): add proposal discipline rules and anti-pattern registry`

---

## 3. Summary Table

| WP | Priority | Deliverable | Net tests |
|----|----------|-------------|-----------|
| WP-1 | P0 | Python 3.13 + CI wip triggers + deploy wording + BATCH14 header | +0 |
| WP-2 | P0 | README 310 tests + 8 hooks, SESSION_CONTEXT Section 2+7 | +0 |
| WP-3 | P1 | `_parse_entries()` rejects malformed `### ` headings + 3 tests | +3 |
| WP-4 | P1 | 6 negative/boundary tests for renderer and logic | +6 |
| WP-5 | P1 | Minimal stable HANDOFF_PROMPT.md (< 60 lines) | +0 |
| WP-6 | P2 | AGENTS.md proposal rules + anti-pattern registry | +0 |

**Total after Batch 15:** 310 + 9 = **319 tests passing**

---

## 4. Execution order

1. WP-1 (unblocks CI confidence)
2. WP-2 (unblocks accurate bootstrap docs)
3. WP-3 (code change, unblocks WP-4)
4. WP-4 (tests for docsync stack including WP-3 behavior)
5. WP-5 (requires aligned docs from WP-1/2)
6. WP-6 (codifies patterns, last because it's additive)

---

## 5. Verification (per WP)

```bash
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

---

## 6. Deferred

- **Fly.io dashboard auto-deploy config**: Not a repo change.
- **Feature work (top songs, heatmap)**: Owner-defined scope required.
- **Orchestrator modularization**: Premature until second pipeline.
- **Cold-start DB machine guarantee**: Separate investigation.
- **Cost analysis (always-on vs sleep)**: Separate investigation.
