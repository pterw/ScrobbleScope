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
  it task by task, then write the frontend plan. Tasks 1-4 have landed, and
  Task 8 landed out of order (before Task 5, owner ruling 2026-09-26). Tasks 5
  and 6 have now landed. Write each specialized plan before implementing its cluster. The
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

### 2026-09-26 - Past-tense the F-WORKTREE-3 note; test a guard error path

Side task, no batch tag: fix round on Task 5 of the control-plane plan, part
of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole
of WP-0 lands.

- **Scope and result.** `docs/agents/FINDINGS.md`'s F-WORKTREE-6 entry
  described F-WORKTREE-3's three open items in the present tense; two of
  those items were fixed by the worktree-guard Task 5 commit and
  F-WORKTREE-3 itself has since been archived. The sentence now reads in the
  past tense ("When this was filed, F-WORKTREE-3's open items were ...") and
  notes the archival. A repo-wide grep for other present-tense "F-WORKTREE-3
  is open" claims outside `docs/history/` and `docs/logarchive/` found none:
  the remaining hits are frozen planning/audit-scope snapshots (a completed
  plan's task list, a batch definition's frozen finding inventory, an
  audit-scope note) or PLAYBOOK's own past-tense execution-log entries, none
  of which claim F-WORKTREE-3 is currently open.
  `tests/scripts/dev/test_worktree_guard_topology.py` gained
  `test_detached_local_status_call_failure_raises_guard_error`, covering the
  detached, non-CI branch's status-call failure path
  (`scripts/dev/_worktree_guard_inspection.py`): a nonzero `status
  --porcelain` result now raises `GuardError`, proven through the public
  `inspect_worktree(..., debug=True)` boundary the same way the existing
  detached-branch tests do.
- **Mutation proof (L14).** In a scratch copy (`git archive $(git stash
  create)`), removing the `detached_status_result.returncode != 0` check
  made only the new test FAIL (`DID NOT RAISE <class
  'scripts.dev._worktree_guard_types.GuardError'>`); the other 8 tests in
  the file still passed.
- **Validation.** `pytest -q` -- **1911 passed**.

### 2026-09-26 - Stage before running pre-commit in the commit procedure

Side task, no batch tag: Task 6 of the control-plane plan, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope and result.** `AGENTS.md`'s "Commit Rules" > "Procedure before
  every commit" ran `pre-commit run --all-files` (step 4) before "Stage
  specific paths by name" (step 6): the `tailwind-css-drift` hook rebuilds
  `static/css/tailwind.css` from source and diffs it against the index, so
  an unstaged, correctly rebuilt CSS change read as drift for the same
  reason a genuinely stale build would (F-B21-20). The two steps are
  swapped: staging is now step 4 and `pre-commit run --all-files` is step 5,
  with `--check` moved to step 6 and Commit to step 7. The staging step now
  says why staging must happen first (F-B21-20), and the pre-commit step
  notes that a hook rewriting a file leaves the tree ahead of the index
  again, so the touched paths need re-staging before `--check`.
- **Step 2 sweep.** `git grep -n "step 4\|step 6\|procedure.*step" -- '*.md'
  ':!docs/history' ':!docs/logarchive'` finds no live document citing the
  old step numbers of this procedure by number: the one non-plan,
  non-archive hit outside this task's own files is
  `.superpowers/cloud-kit/agents/gate-runner.md`'s own "Step 4 --
  postflight" heading (its own numbering, not a citation of AGENTS.md).
- **Live probe** (`/c/ssprobe6`, independent clone at BASE `4ece23a`,
  deleted afterwards; run by a probe-only dispatch and spot-checked by the
  controller, recorded in `task-6-probe-report.md`).

  | Case | Result | Exit |
  |---|---|---|
  | Red (old order): correct rebuild, left unstaged | `tailwind-css-drift` Failed | 1 |
  | Green (new order): correct rebuild, staged first | `tailwind-css-drift` Passed | 0 |
  | Near-miss: stale build (not rebuilt), staged anyway | `tailwind-css-drift` Failed | 1 |

  A correct rebuild passes under the new order and fails under the old one;
  a genuinely stale build still correctly fails either way.
- F-B21-20 is resolved.
- **Validation.** `pytest -q` -- **1910 passed**.

### 2026-09-26 - Two worktree-guard bugs are fixed

Side task, no batch tag: Task 5 of the control-plane plan, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope and result.** `classify_lineage`'s (`scripts/dev/
  _worktree_guard_lineage.py`) detached branch returned before either dirty
  check, so a detached, dirty, non-CI worktree reported WT012 alone; it now
  builds `issues` and appends the dirty diagnostic when `snapshot.dirty` is
  true, the same pattern the non-detached path already used.
  `missing_base_remediation` (`scripts/dev/_worktree_guard_diagnostics.py`)
  branched on and interpolated its already-labelled parameter, so an unsafe
  base ref's remediation always fell into the "local ref" branch and doubled
  the placeholder text; it now branches on the raw `base_ref` and computes
  `label = base_ref_label(base_ref)` only at the point each branch's message
  substitutes it, and `missing_base_diagnostic` now passes the raw ref
  instead of the label (F-WORKTREE-3).
- **Controller ruling after the code phase (2026-09-26).** Bug 1's classifier
  fix alone was unreachable through the real CLI: the detached, non-CI
  branch of `inspect_worktree` (`scripts/dev/_worktree_guard_inspection.py`)
  built its `LineageSnapshot` with `dirty` hard-coded `False` and returned
  before any status check. That branch now measures dirtiness with the same
  `("status", "--porcelain")` call the attached path uses (the
  recognized-CI detached branch keeps `dirty=False` and makes no extra git
  call, owner ruling Q2: WT011 alone on CI).
  `tests/scripts/dev/test_worktree_guard_topology.py::
  test_detached_checkout_stops_before_local_topology_checks` now expects the
  local case's last git call to be `("status", "--porcelain")` instead of
  `symbolic-ref`; the CI cases are unchanged. One inspection-level test,
  `test_detached_dirty_local_reports_wt012_and_wt010`, covers detached,
  dirty, non-CI end to end (`WT012` and `WT010`).
- **Mutation proof (L14).** In a scratch copy (`git archive $(git stash
  create)`), reverting the inspection-layer fix made
  `test_detached_checkout_stops_before_local_topology_checks[local]` and
  `test_detached_dirty_local_reports_wt012_and_wt010` both FAIL (last call
  stayed `symbolic-ref`; codes stayed `['WT012']`); the CI-branch cases were
  unaffected. Reverting `classify_lineage`'s WT012 branch made
  `test_detached_and_dirty_reports_both_wt012_and_wt010` FAIL while
  `test_detached_ci_dirty_still_only_reports_wt011` still passed. Reverting
  `missing_base_remediation`/`missing_base_diagnostic` made
  `test_missing_base_remediation_matches_selected_ref[unsafe-remote-like]`
  FAIL while the two pre-existing parametrize cases still passed.
- **Live probe** (`/c/ssprobe`, independent clone, deleted afterwards).

  | Probe | State | Result |
  |---|---|---|
  | Red | BASE, detached + dirty | `WT012` alone |
  | Green | this task's tree, detached + dirty | `WT012` and `WT010` |
  | Near-miss | this task's tree, detached + clean | `WT012` alone |

- F-WORKTREE-3 is now fully resolved (3 of 3 items accounted for); the
  between-batch ancestry skip remains the owner's 2026-09-23 accepted design
  boundary.
- **Validation.** `pytest -q` -- **1910 passed**.

### 2026-09-26 - Test the staged-deletion case of the docsync.toml exemption

Side task, no batch tag: fix round on Task 8 of the control-plane plan, part
of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole
of WP-0 lands.

- **Scope and result.** `_docsync_toml_pin_only_change`
  (`scripts/dev/docsync_preflight.py`) fails closed when `config/docsync.toml`
  is absent from the index (a staged deletion or rename-away): `git show
  :config/docsync.toml` exits nonzero, so the function returns `False` and
  the path counts as control-plane. No test covered that branch.
  `test_docsync_toml_absent_from_index_is_control_plane`
  (`tests/scripts/dev/test_docsync_preflight.py`) now does, with a valid
  HEAD blob and a nonzero-exit index lookup.
- **Mutation proof (L14).** In a scratch copy (`git archive HEAD`), inverting
  `index_result.returncode != 0` to `== 0` made the new test FAIL
  (`assert [] == ['config/docsync.toml']`); restoring the check made it PASS.
- **Validation.** `pytest -q` -- **1906 passed**.
