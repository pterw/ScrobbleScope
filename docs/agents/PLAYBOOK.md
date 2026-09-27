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
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). Next action: the close-out code
  review of the whole branch, then the WP-0 close-out below. The
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

### 2026-09-27 - Heatmap keyboard and screen-reader access follow-up

Side task, no batch tag: give the heatmap grid a roving tabindex (one Tab
stop, arrow keys move it) in place of every cell carrying tabindex="0",
change the SVG's role from "img" to "group" so a cell's own role="img" +
aria-label survives in the accessibility tree, and stop a focus-triggered
scroll from hiding the tooltip it just showed, part of Batch 23 WP-0 Part
C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Validation: `pytest -q` -- **1999 passed**.

### 2026-09-27 - Artist spotlight photo shown whole, swaps stay in sync, hydrate requests time out

Side task, no batch tag: fixed the artist spotlight card's non-square photo
crop, the stale-photo-under-a-new-name swap on rotation, and the missing
hydrate-request timeout (now covering the image preload too, not just the
fetch), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23
until the whole of WP-0 lands.

Validation: `pytest -q` -- **1999 passed**.

### 2026-09-27 - Docsync CLI and declarations edge cases

Side task, no batch tag: fix docsync's `--test-count 0` acceptance, the
pin-rewrite regexes' heading-comment and blank-line misses, and add a
`C:foo` CR5 case plus a control-character rejection for
`[untracked_essentials]` paths, part of Batch 23 WP-0 Part C. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands.

Validation: `pytest -q` -- **1999 passed**.

### 2026-09-27 - Bring prose and diagrams in line with the three follow-on plans

Side task, no batch tag: a documentation-only sweep so README.md,
DEVELOPMENT.md, every `docs/architecture/*.md` Mermaid diagram,
`.claude/SESSION_CONTEXT.md` and `docs/agents/PLAYBOOK.md` match the code the
control-plane, frontend and test-infrastructure plans changed
(`f8fb8e9^..HEAD`), part of Batch 23 WP-0 Part C. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- `docs/architecture/documentation-tooling.md`: added the two new frontend
  gate slices (`_frontend_gate_heatmap_access`, `_frontend_gate_spotlight_photo`)
  to the Mermaid diagram and its facade-sibling count (twelve, ten own a
  concern); added a `_worktree_guard_essentials` node/edges (WT015) and the
  seventh guard-module count; added `config/docsync.toml`'s `[test_count]`
  pin and `[untracked_essentials]` table to the TOML node; documented WT015
  and the `docsync.logic`/`docsync.integrity` deferred-import removal (CO1).
- `docs/architecture/development-cycle.md`: the "Run full validation gates"
  node now names `--test-count N`, the `tests/frontend` browser marker and
  `results_behavior_tests.py`; added a CI paragraph naming the docsync
  preflight, `pytest -m "not browser"`, the browser-marked suite and
  `frontend_gate.py`, and `pip-audit` against both requirements files.
- `README.md`: "Running Tests" now names the `browser` marker and the local
  Chromium requirement.
- `DEVELOPMENT.md`: the frontend-gate facade's sibling count and the
  worktree guard's module/WT-code counts (seven modules, `WT000`-`WT015`);
  named this session's four new gate checks; added the `tests/frontend`
  marker, its CI split and the wider `pip-audit` scope to the Frontend
  Browser Gate section.
- `.claude/SESSION_CONTEXT.md`: added the two new gate slices and
  `_worktree_guard_essentials.py` to Section 3's structure listing and their
  edges to Section 4's dependency graph; noted `tests/frontend/` and
  `tests/fixtures/` in Section 6; bumped the "Last updated" date.
- `docs/agents/PLAYBOOK.md` Section 3: the frontend and test-infrastructure
  plans are both fully executed; the next action is the close-out code
  review, then the WP-0 close-out. `**Next action:** WP-0 is next.` is
  unchanged.
- `docs/ARCHITECTURE.md`: bumped the "last verified" date after checking
  every diagram against the current tree.
- Checked and found already accurate, no change made: `AGENTS.md`,
  `docs/architecture/runtime-system.md` (spotlight fallback prose already
  fixed by Task 5), `docs/architecture/{heatmap,top-albums}-sequence.md`,
  `docs/agents/ui-accessibility.md`, `docs/agents/AGENT_NOTES.md`, the three
  plan files' checkboxes (already all ticked), `docs/design/*.md` (dated
  audit/reconciliation documents, out of the live-prescriptive-doc scope).

Validation: `pytest -q` -- **1993 passed**.
