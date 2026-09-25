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
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Execute
  it task by task, then write the frontend plan. Write each specialized
  plan before implementing its cluster. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry. Earlier WP-0 commits remain untagged by the owner's
  2026-09-23 ruling in the definition.
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

### 2026-09-25 - The control-plane plan is written and reviewed

Side task, no batch tag: adds WP-0 Part C's first follow-on plan.

- **Scope and result.** The plan covers F-DOCSYNC-6, -7, -11, -12, -13, -15
  and -22, F-MAS-3, F-WORKTREE-3, F-B21-20 and F-B21-25 items 1-2, in seven
  tasks. Two read-only reviews checked it against the code. The first found
  that the draft kept the pinned test count in the SESSION_CONTEXT STATUS
  block, which is rendered output. It also found that the draft claimed the
  commit procedure already passes `--test-count`, which it does not. Both
  are fixed.
- **Owner rulings.** The plan records three: the pin lives in
  `config/docsync.toml`; a new warning, DOC025, fires only when one newest
  entry disagrees with the pin; and a dirty tree adds WT010 only on a local
  detached checkout.
- **Deviations.** The plan is 1834 lines, above the review's estimate. The
  pin redesign and DOC025 added test bodies that the length rule does not
  allow cutting.
- **Validation.** `pytest -q` -- **1873 passed** with the owner's untracked
  mutation tests excluded. Docsync check and pre-commit pass.
- **Forward guidance.** Task 1 reorders the commit procedure so the suite
  is measured before `--fix --test-count N`.

### 2026-09-25 - Owner rulings: no GitHub mirror, and F-DOCSYNC-22 joins Part C

Side task, no batch tag: records two owner rulings given on 2026-09-25.

- **Scope and result.** F-DOCSYNC-22 is filed at P1: a count corrected in an
  older same-date side-task entry stays shadowed until the entry is moved. It
  was found in root-cleanup Task 6's fix round 1 (`c959237`) and held until now
  as a candidate in a gitignored SDD ledger. The owner amended Part C's set to
  include it, in the definition and in the reconcile plan's control-plane
  follow-on, where it joins the F-DOCSYNC-11, -12 and -13 task. The owner also
  ruled that findings are not mirrored to GitHub. F-B21-9 closes as no action
  and rotates to the archive. `AGENTS.md` and `docs/agents/issue-tracker.md`
  now say the `finding` issues are a frozen snapshot.
- **Deviations.** None. The Q15 row of the reconcile plan's rulings table and
  its triage table are point-in-time records and stay as written. The
  follow-on list carries the change.
- **Validation.** `pytest -q` -- **1873 passed** with the owner's untracked
  mutation tests excluded. Docsync check and pre-commit pass.
- **Forward guidance.** The control-plane plan's count task must test a
  corrected count in an older same-date entry.

### 2026-09-25 - Section 3 states the live WP-0 work order

Side task, no batch tag: Batch 23 WP-0 Part B's final documentation cleanup.

- **Scope and result.** Section 3 now names the active batch, the next work
  package, Part C's three follow-on plans, and the close-out gate. The
  paragraph-to-owner crosswalk is
  `docs/history/reports/BATCH23_WP0_SECTION3_CROSSWALK_2026-09-25.md`.
  The 2026-09-24 handoff is marked as a historical snapshot so its old
  root-cleanup resume point cannot be mistaken for the current order. The
  Batch 23 definition marks Part B's Section 3 cleanup done.
- **History retained.** PR #234 merged the Batch 22 branch through
  `f6d5926` as `88f6e27` on 2026-09-20; PR #236 later merged eight more
  commits as `fc9098d`. The old Section 3 attached 05:06 to `f6d5926`;
  Git dates that commit at 05:01 and the PR #234 merge at 05:06. This
  post-close-out chronology was not otherwise owned by a dated record.
  The old Section 3 also recorded the owner's 2026-09-21 setting of
  `MUSICBRAINZ_CONTACT` on Fly.io and in the local `.env` to the project's
  GitHub URL; this is retained as a point-in-time report, not a current
  configuration check.
- **Validation.** `pytest -q` -- **1873 passed** with the owner's untracked
  mutation tests excluded. Pre-commit and docsync check pass with the four
  standing DOC024 warnings and the expected active-definition warning.
- **Forward guidance.** Write and execute the control-plane, frontend, and
  test-infrastructure follow-on plans in the reconcile plan's order. Review
  the remaining Part C findings before the single tagged WP-0 close-out.

### 2026-09-25 - The Batch 23 review reconciles completed records

Side task, no batch tag: the completed-work review compared the Batch 23
definition, the reconcile plan and the root-cleanup plan with the current
tree. The report is
`docs/history/reports/BATCH23_WP0_COMPLETED_WORK_REVIEW_2026-09-25.md`.

- **Scope and fix.** F-B23-8 records that the definition pointed six rotated
  findings at the active file and left two completed Part B bullets unchecked.
  It now points to the archive and checks the foundation and root-cleanup
  bullets. The Section 3 cleanup bullet stays unchecked; Parts B and C are
  not complete, so no tagged batch entry was written.
- **Validation.** `pytest -q` -- **1873 passed** with the untracked mutation
  tests excluded. The frontend gate passed 30 checks in 52 Chromium and
  Firefox runs. Pre-commit and docsync check exited 0, with the standing
  DOC024 warnings and expected active-definition warning.
- **Forward guidance.** Return to the uncompleted Section 3 cleanup and
  Part C follow-on plans before closing the work package. The report notes
  the shared provider-log privacy work required before export integration.
