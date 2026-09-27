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
  frontend plan: Tasks 1, 2, 3, 4 and 5 have landed. Test-infrastructure plan: Tasks 1,
  2 and 3 have landed. Next
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

### 2026-09-27 - Let the inline marks colour themselves

Side task, no batch tag: fixed F-B21-23, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Both inline mark SVGs now carry fill="currentColor" and stroke: var(--bars-color)
in their own <style> block, so shell.css's five-rule per-wrapper CSS list
(F-B21-21's fix) collapses to one `.ss-mark { color: var(--shell-ink); }`
declaration. `check_inline_marks_need_no_wrapper_list` in
scripts/dev/_frontend_gate_assets.py reads both SVG templates off disk and
fails on a missing fill/stroke rule or any literal hex colour.
`tests/test_template_shell.py::test_migrated_wordmarks_use_theme_ink_for_letterforms`
was rewritten (controller ruling, task-4-context.md, widening this task's
Touches) to assert the new mechanism instead of the deleted per-wrapper
selectors, keeping its name and docstring intent.

Validation: `pytest -q` -- **1978 passed**.

### 2026-09-27 - Heatmap grid cells are keyboard-focusable and labelled

Side task, no batch tag: heatmap grid cells carry tabindex, role=img and an
aria-label built by the same cellAccessibleLabel helper the mouse tooltip
uses, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until
the whole of WP-0 lands.

Extracted `cellAccessibleLabel` in `static/js/heatmap.js` so the tooltip and
each cell's `aria-label` share one source of truth, made every `.heatmap-cell`
focusable with a visible `:focus-visible` ring, and added
`check_heatmap_cells_are_keyboard_accessible` (its own frontend-gate slice,
`scripts/dev/_frontend_gate_heatmap_access.py`) to prove it live. Resolves
F-B21-14.

Fix round 1: the check now asserts the reached cell's own `tabindex="0"`
attribute and that every `.heatmap-cell` in the grid carries it (naming the
count missing), and asserts the authored focus ring by its four computed
properties -- `outline-width: 2px`, `outline-style: solid`,
`outline-offset: 1px`, and `outline-color` equal to `--shell-accent`'s
computed colour read via a probe element -- rather than the generic
`outlineStyle !== 'none'` a bare UA default outline also satisfied.

Validation: `pytest -q` -- **1978 passed**.

### 2026-09-27 - Move four dev-only pins out of the production install

Side task, no batch tag: move four dev-only pins out of the production install, part of
Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
`virtualenv==20.36.1`, `distlib==0.3.9`, `filelock==3.20.3` and `platformdirs==4.3.6`
moved from `requirements.txt` to `requirements-dev.txt` (F-B21-3 remainder); nothing in
`scrobblescope/` imports them (`git grep` confirmed no hits). A live `pip-audit` recount
on 2026-09-27 found 0 vulnerabilities in 0 packages against `requirements.txt` alone, 0
against both files together.
Validation: `pytest -q` -- **1965 passed**.

### 2026-09-27 - A two-state toggle that reattaches to the system

Side task, no batch tag: fixed the theme toggle so a choice matching the system preference
clears the stored value and lets the page reattach to the system, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands. `theme.js`'s
`darkSwitch` `change` listener now computes the system's preferred scheme via
`matchMedia('(prefers-color-scheme: dark)')` and calls `localStorage.removeItem('darkMode')`
when the chosen state matches it, instead of always writing the choice; `base.html`'s
pre-paint script already treats a missing key as "follow the system", so no change was
needed there. `scripts/dev/_frontend_gate_theme.py` adds
`check_theme_reattaches_to_system` (registered in `frontend_gate.py`'s `CHECKS` tuple,
`THEME_MOTION` group, beside "theme persistence"), which forces the toggle away from an
emulated dark system, confirms the choice persists across a reload, then flips it back to
match the system and confirms `localStorage.getItem('darkMode')` clears immediately and the
page still resolves dark from the system query alone after a reload. Resolves F-B21-22.

Validation: `pytest -q` -- **1965 passed**.
