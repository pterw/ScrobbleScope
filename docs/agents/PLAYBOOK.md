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

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. Next
  action: execute these two plans, then the WP-0 close-out. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.

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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-26 - Drop a work-package token from a log heading

Side task, no batch tag: rename a log heading that carried a work-package
token, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23
until the whole of WP-0 lands.

- **Scope and result.** The previous entry's heading carried a `WP-0` token,
  which the owner ruling keeps out of headings until WP-0 closes;
  `--check` passed and treated it as untagged, so this fixes the
  convention, not a docsync failure.

Validation: `pytest -q` -- **1926 passed**.

### 2026-09-26 - Plan the frontend and test-infrastructure work

Side task, no batch tag: plan the WP-0 frontend and test-infrastructure work,
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **Scope and result.** Two follow-on plans drafted and reviewed against the
  code, then revised. `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md`
  covers the frontend cluster: F-B21-18's Chromium harness for `heatmap.js`,
  F-B21-14, F-B21-22, F-B21-23, and F-B21-60 part 1.
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md` covers
  the test-infrastructure and dependency cluster: F-LOAD-2, F-MAS-1, F-B21-3's
  remainder, and adding `requirements-dev.txt` to the CI pip-audit step. Both
  drafts passed a read-only review against the code, then were revised.
- **Findings the reviews caught.** The frontend harness's test hooks sat
  inside a `DOMContentLoaded` listener and could never be reached (proven
  red/green in a scratch copy); CI's pytest step runs before the browser
  install, so the harness is marked `browser` and runs in the frontend-gate
  step instead. The test-infrastructure integration test's fixture was dated
  2030 and below the play threshold, so it never reached Spotify.

Validation: `pytest -q` -- **1926 passed**.

### 2026-09-26 - Correct the dashboard's test-module count

Side task, no batch tag: follow-up on the Task 7 fix round's CR8, part of
Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of
WP-0 lands.

- **Scope and result.** The prior CR8 fix corrected `docs/agents/FINDINGS.md`'s
  hand-maintained header (72 -> 73 tracked test modules) but left
  `.claude/SESSION_CONTEXT.md`'s own copy of the same figure stale, because
  `--fix` only rewrites the test-*count* digit there, never the module-count
  digit (`AGENTS.md` anti-pattern 10: re-measure rather than copy a number
  forward). Re-measured
  (`git ls-tree -r --name-only HEAD tests | grep -c '/test_[^/]*\.py$'` -> 73,
  unchanged) and corrected SESSION_CONTEXT's Section 1 Tests row from 72 to
  73, leaving its test count exactly as `--fix` last wrote it (1926).
  `git grep -n -i "tracked test module" -- ':!docs/history' ':!docs/logarchive'
  ':!docs/superpowers/plans'` found no other live-doc copy showing a stale
  figure: `tests/test_docsync_cli.py` and `tests/test_docsync_test_count.py`
  only quote fixture text (68), not a live claim.

Validation: `pytest -q` -- **1926 passed**.

### 2026-09-26 - Keep the essentials warning from failing the worktree guard

Side task, no batch tag: fix round on Task 7's code review, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **CR1.** `essentials_diagnostics` (`scripts/dev/_worktree_guard_essentials.py`)
  now catches `DeclarationError` from `load_untracked_essentials_config` and
  returns a single WARNING `WT015` naming `config/docsync.toml` and quoting
  the parse error, instead of letting it escape to `inspect_worktree`'s
  fail-closed `except Exception` and collapse the whole result to ERROR
  `WT014`.
- **CR2.** `collect_declaration_issues`
  (`scripts/docsync/declarations.py`) now also calls
  `_untracked_essentials_config`, so `doc_state_sync --check` and pre-commit
  refuse a malformed `[untracked_essentials]` table the same way they refuse
  a bad `[archives]` or `[closeout]` table.
- **CR3.** `_inspect_worktree`
  (`scripts/dev/_worktree_guard_inspection.py`) now runs the essentials
  check on the detached-HEAD return path and the PLAYBOOK-parse-failure
  return path too, so `WT015` fires in a detached scratch worktree (the
  parallel workflow's `git worktree add --detach`) and not only on the
  fully-resolved path.
- **CR7.** `WT015` raises the code count to sixteen: updated the "eleven of
  the fifteen codes" text in `scripts/dev/check_worktree_alignment.py`,
  `.pre-commit-config.yaml` and `tests/scripts/dev/test_worktree_guard_cli_e2e.py`
  to sixteen, adding `WT015` where the non-error codes are listed.
  `docs/agents/FINDINGS.md`'s note quoting a reviewer's past correction is
  left as a point-in-time record.
- **CR8.** The tree now has 73 tracked `test_*.py` modules; `FINDINGS.md`'s
  hand-maintained header corrected from 72 to 73.

Validation: `pytest -q` -- **1926 passed**.
