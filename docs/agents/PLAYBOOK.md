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
  Branch: `feat/batch23-wp0-hygiene`. That branch merged into `main` as PR #245 on 2026-09-30 and `origin/test` is
  deleted, so side-task PRs branch from `main` and run the guard against its default
  base. The owner names the branch WP-1 opens.
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
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). The WP-0 close-out below is what remains of WP-0. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #7, UI consistency, is under way on `feat/ui-consistency`; round 1's
  plan is `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.
- **What PR #245 ships (owner ruling 2026-09-29):** the WP-0 foundation and
  every fix from the three reviews, including the job module with its storage
  seam, typed provider failures and provider failure logs that carry no
  listener data. Moved to the follow-up PR: job persistence, the Last.fm
  scrobble seams, the album request module, one album-metadata encoding, the
  statistics module and the tooling package.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam and typed provider failures, job persistence
  (gates WP-3), an album request module (gates WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (gates WP-2), one album-metadata
  encoding (gates WP-3), a statistics module (gates WP-6), and provider
  failure logs that carry no listener data. Which of these #245 ships is
  in the "What PR #245 ships" bullet above; the rest wait for the follow-up
  PR.

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

### 2026-10-20 - The figure font constant stops looking like a password

Side task, no batch tag: rename the figure-face gate's `FIGURE_TOKEN` constant, on `feat/ui-consistency`, a branch off `main`.

Owner intent: PR #260 must pass Codacy without suppressing a scanner.

What changed: Codacy's Bandit check (B105, hardcoded password) read `FIGURE_TOKEN = "--font-figure"` in `scripts/dev/_frontend_gate_figures.py` as a credential because the name contains TOKEN. The value is a CSS custom-property name, so the constant is now `FIGURE_FONT_PROPERTY`; its four uses follow. Behaviour and messages are unchanged. The plan under `docs/superpowers/plans/` keeps the old name as an archival record.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2607 passed**.

Side task, no batch tag: correct the figure-face gate module's ledger citation and the FINDINGS test-module count, on `feat/ui-consistency`, a branch off `main`.

Owner intent: the gate's own prose and the project's counts must be true for what the branch ships.

What changed: the docstring of `scripts/dev/_frontend_gate_figures.py` now cites `docs/design/RECONCILIATION.md` section 26 (the play-count override; Task 1 renumbered it because sections 22 to 25 exist) instead of 22, and states the "cannot drift to the wrong face together" clause once instead of twice. The `docs/agents/FINDINGS.md` header now says 87 tracked test modules, the measured `git ls-files tests | grep -c '/test_[^/]*\.py$'`; the earlier commit added a module and left 86 there.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2607 passed**.

### 2026-10-20 - The gate holds the Results play count to the figure face

Side task, no batch tag: add a frontend-gate check that the Results play count wears the heatmap's figure face, on `feat/ui-consistency`, a branch off `main`.

Owner intent (tranche design, "UI PR (#7)"): a frontend-gate check asserts that the computed font of a results play count equals that of a heatmap KPI value, at every viewport the gate runs.

What changed: new `scripts/dev/_frontend_gate_figures.py` (`check_results_play_count_uses_the_figure_face`, registered in `scripts/dev/frontend_gate.py` as "results play count figure face" for the desktop, mobile and wide-touch profiles, Chromium only) and `tests/scripts/dev/test_frontend_gate_figures.py` (16 tests). Why: the serif count shipped beside a Gotham KPI and nothing could see it. The check reads the computed family and weight of every play count, on load and after the sort is switched (results.js rebuilds the cell), and requires them to equal the heatmap KPI value's; it also requires that KPI value to be the `--font-figure` token at weight 400, so the pair cannot drift to the wrong face together; an empty selection fails instead of passing. At the mobile profile only it also requires the seeded four-digit count to keep its right edge inside its cell (the guard for Task 1's narrow-screen sizing). The module is documented in SESSION_CONTEXT (tree and import lines), `docs/architecture/documentation-tooling.md` (count fifteen, list, Mermaid) and DEVELOPMENT.md.

Mutation (unit, scratch copy, each planted defect failed its named tests): weight branch deleted -> `test_a_bold_play_count_fails_even_in_the_right_face`; family branch -> serif, one-wrong-among-many and rebuilt-cell tests; reference early return -> the two reference tests; both empty-selection returns -> `test_no_kpi_and_no_play_count_each_fail_rather_than_pass_vacuously`; second face call -> `test_a_cell_rebuilt_by_a_sort_switch_is_judged_again`; `>` to `<` -> three fit tests; `if narrow:` guards -> `test_at_a_desktop_width_the_fit_is_not_judged`; second fit call and `jobs.delete(heatmap_job)` -> their named tests.

Live probe (scratch tree, real Chromium; the worktree CSS untouched): old face planted -> at every profile `play count on load is set in 'instrument-serif,corporate-a,Georgia,serif', the heatmap KPI value in 'gotham,ff-din-paneuropean,ui-sans-serif,sans-serif'` and the same `after switching sort`; bold planted -> `play count on load has font weight 700, the heatmap KPI value 400` (and after switching sort) at every profile; the `data-digits="4"` rule removed -> `[mobile] play count 8080 on load ends 10.0px past the cell it sits in` and the same after switching sort, desktop and wide touch PASS. The worktree passes at all three profiles.

Deviations: none in the code. The check adds 3 planned runs (Firefox runs only the assets canary). The Mermaid block was edited by one node line and one class-list entry in the file's existing pattern; no external validator was run.

Edited existing tests: none.

Validation: `pytest -q` -- **2607 passed**. Gate: `[frontend_gate] 48 checks passed in 78 runs across chromium, firefox (static assets & tokens canary on firefox); profiles: desktop, mobile, wide touch`.

### 2026-10-20 - The Results play count is set in the figure face

Side task, no batch tag: set the Results table's play count in the figure face, on `feat/ui-consistency`, a branch off `main`.

Owner intent (tranche design, "UI PR (#7)"): "the results table's play count uses the figure face (`--font-figure`, Gotham, weight 400 -- never bold, as the heatmap KPI rule records)"; `DESIGN.md` gives play counts to the Figure Numerals.

What changed: `.metric-val-plays` in `static/css/results.css` takes `--font-figure` at `--font-weight-normal` with `font-variant-numeric: tabular-nums` (set because `DESIGN.md` decides tabular Figure Numerals); size, line height, colour and letter-spacing are untouched. `docs/design/RECONCILIATION.md` gains a Section 1 row and section 26 recording the override of the snapshot's "mono value". Measured with a scratch script at all three gate profiles, both themes: Gotham served (one face fetched; 357.9px against 321.6px for the fallback); before, every play count computed `instrument-serif`, after, `gotham` at weight 400, colour equal row by row, size equal, every row height unchanged (81.2px desktop and wide touch, 73px mobile). Gotham has `tnum` (default 1111 vs 0000 = 34.4 vs 68.6px, with tabular-nums both 57.6px). Four digits did not fit at full size on mobile: 8080 measured 54px against a 44px room (407: 40.5px, fits), so Step 5b applied by the controller's ruling (one-attribute template edit): the plays span carries `data-digits` (`templates/results.html`, rebuilt by `renderMetric` in `static/js/results.js` on a sort switch), and under 768px only, a 4-digit count is set at 1.093rem and a 5-digit one at 0.874rem (widest digit d = 0.6003em, room R = 44px, S(n) = floor((R - 2) / (n * d) / 16)), 6 or more at the 0.75rem floor. After: 8080 and 88888 measure 41.95px in 44px; 888888 measures 43.2px in 44px at the floor (fits, but with under the 2px spare, so fit is not promised for six digits). Desktop and wide touch widths and sizes, and mobile rows of one to three digits, are identical to the full-size measurement.

Deviations: the master plan named `.metric-value`; the rule is `.metric-val-plays`. The plan numbered the RECONCILIATION section 22, but sections 22 to 25 already exist, so the override is section 26 (row, CSS comment and prose follow). Section 26 includes the plan's conditional narrow-screens paragraph, because Step 5b applied.

Edited existing tests: none. New test: `test_each_play_count_states_how_many_digits_it_has` in `tests/test_routes.py`; with the template's `data-digits` planted as a constant `"4"` in a scratch copy it failed on the 407 assertion, and it passes on the real template.

Validation: `pytest -q` -- **2591 passed**.

### 2026-10-20 - The UI consistency round 1 plan opens its branch

Side task, no batch tag: add the approved UI consistency round 1 plan, on `feat/ui-consistency`, a branch off `main`.

Owner intent (2026-10-20): "All plans should stay for archival purposes", so every PR plan is its branch's first commit.

What changed: `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md` is added, and PLAYBOOK Section 3's "Before WP-1" bullet gains one sentence naming PR #7 and the plan. The plan passed a brief review (plan-review.md), three fix rounds, and two re-reviews (plan-rereview-1.md, plan-rereview-2.md); the last approved it.

Deviations: the plan is committed as approved. The one commit-time fix (plan-rereview-2 Minor 1, Step 5b item 4 must say to replace the single line and keep the `else` braces) was already present in the approved draft, so no further wording change was made. No DOC-driven wording change was needed. No test was edited.

Validation: `pytest -q` -- **2590 passed**.
