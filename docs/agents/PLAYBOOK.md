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
  Task 8 landed out of order (before Task 5, owner ruling 2026-09-26). Task 5
  has now landed. Write each specialized plan before implementing its cluster. The
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

### 2026-09-26 - A pin-only docsync.toml change is not control-plane

Side task, no batch tag: Task 8 of the control-plane plan, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope and result.** Task 1 (`8f56c17`) put the test-count pin in
  `config/docsync.toml` `[test_count]`, but `scripts/dev/docsync_preflight.py`
  also lists `config/docsync.toml` in `CONTROL_PLANE_FILES`, so every
  ordinary commit that adds a test (and therefore pins a new count) staged a
  "control-plane" file and was refused, forcing `SKIP=doc-state-sync-check`
  on routine commits. Owner ruling, 2026-09-26: keep the pin where it is,
  and change the preflight so a staged `config/docsync.toml` counts as
  control-plane only when something outside `[test_count]` changed.
  `staged_control_plane_paths` (`scripts/dev/docsync_preflight.py`) gained a
  new `_docsync_toml_pin_only_change` helper: it compares the HEAD and index
  blobs of `config/docsync.toml`, each parsed with stdlib `tomllib` and with
  its top-level `test_count` key removed, and treats the change as pin-only
  only when the remainders are equal. It fails closed (treats the change as
  control-plane) when the file is absent at HEAD or the index, either blob
  fails to parse, or either `git show` exits nonzero. The exemption is
  evaluated per path, so a pin-only `config/docsync.toml` staged alongside a
  real control-plane code change still leaves that other path refused.
- **Mutation proof (L14).** In a scratch copy (`git archive $(git stash
  create)`), reverting `staged_control_plane_paths` to its pre-Task-8 body
  made the three tests whose outcome the exemption changes fail
  (`test_docsync_toml_pin_only_change_is_not_control_plane`,
  `test_docsync_toml_test_count_table_added_is_still_pin_only`,
  `test_docsync_toml_pin_only_alongside_other_control_plane_file_is_per_path`);
  the four unchanged-behaviour cases still passed.
- **Live probe** (`/c/ssprobe`, independent clone, deleted afterwards).

  | Probe | Command | Result |
  |---|---|---|
  | Red (BASE preflight) | pin-only edit staged, `docsync_preflight.py --staged` | exit 3, control-plane refusal |
  | Green (task preflight overlaid) | same staged edit | exit 1 (the checker's own doc-drift result), no refusal |
  | Near-miss (task preflight overlaid) | pin edit plus an `[options]` edit staged | exit 3, control-plane refusal |

- **Validation.** `pytest -q` -- **1905 passed**.

### 2026-09-25 - BATCH* discovery becomes case-consistent

Side task, no batch tag: Task 4 of the control-plane plan, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope and result.** `_batch_filename_candidates` (`scripts/docsync/cli.py`)
  replaces every `directory.glob("BATCH...")` call in the module --
  `_check_root_batch_files`, both `LOGS_DIR.glob("BATCH*_LOG.md")` sites
  (`_read_batch_log_lines` and `_managed_archive_paths`), `_archived_definitions`
  and `_read_live_documents` -- with a directory-listing scan matched by the
  same case-insensitive regex glob's candidates were already filtered with
  (`_BATCH_LOG_RE`, `root_definition_pattern`), so batch discovery no longer
  depends on the host filesystem's case sensitivity (F-DOCSYNC-6).
  `git grep -n 'glob("BATCH' -- scripts/docsync` now returns nothing.
  F-DOCSYNC-6's outside-root item was confirmed already fixed:
  `_Files._path`/`_relative` (`scripts/docsync/declarations.py`) already raise
  `DeclarationError` -- caught by `main()`'s `except SyncError` clause, since
  `DeclarationError` subclasses `SyncError` -- with "... resolves outside the
  repository root", instead of letting a bare `ValueError` propagate;
  `docs/agents/FINDINGS.md`'s own F-DOCSYNC-6 entry already names F-DOCSYNC-21
  (`88f0514`) as the fix for this item, and `88f0514`'s `_validate_documents`
  closes the same class of escape for the `[documents]` config roles. This
  finding is now fully resolved (5 of 5 items accounted for); the three
  remaining items are the owner's 2026-09-23 accepted design boundaries and
  stay as documented.
- **Live probe** (`/c/ssprobe`, deleted afterwards). `fsutil file
  setCaseSensitiveInfo` was denied (`0x00000005 Access is denied`) on this
  host, so the brief's "before" red could not be produced under a simulated
  POSIX case-sensitive directory; per the controller, this was tried once and
  not retried another way.

  | Probe | Result |
  |---|---|
  | Before (BASE tree, this NTFS host, lower-case `batch99_definition.md` added) | `--check` passes; `_archived_definitions()` finds it (host-dependent, as expected) |
  | After (task tree, same fixture) | `--check` passes identically; `_archived_definitions()` finds it |
  | Near-miss (correctly-cased `BATCH13_DEFINITION.md`) | Found identically in both trees |
  | Mutation (scratch copy): `_batch_filename_candidates` body swapped for `sorted(directory.glob("BATCH*", case_sensitive=True))` filtered by `name_re`, simulating POSIX | The Step 2 unit test fails, missing `batch24_definition.md` and `Batch25_Definition.md` -- this substitutes for the host-dependent red |

- **Deviation.** The brief's Step 1 instructed `git show 88f0514 --
  scripts/docsync/declarations.py | grep -n "resolves outside"`, expecting
  that literal string in the diff; it is not there. `88f0514` validates the
  `[documents]` config table with different wording ("must be a
  repository-relative path", "must be inside the repository"); the "resolves
  outside the repository root" wording belongs to `_Files._path`/`_relative`,
  added earlier (`54fecbfb`) and already in the tree. Both mechanisms raise
  `DeclarationError` -> exit 2 through the same `except SyncError` path, so
  the finding's outside-root item is still confirmed fixed; this entry cites
  the evidence actually found rather than the brief's unmatched grep. Per the
  controller's task context, both `LOGS_DIR.glob(...)` sites were converted
  (not gated on the live probe, which cannot reproduce a platform mismatch on
  this host) and the Section 3 WP-0 close-out bullet picks up a carried
  review item from Task 3: its tagged entry must carry `**Status:** WP-0
  complete`, or DOC007 blocks the close-out.
- **Validation.** `pytest -q` -- **1898 passed**.
