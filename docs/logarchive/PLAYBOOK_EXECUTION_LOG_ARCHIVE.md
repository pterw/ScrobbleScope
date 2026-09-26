# PLAYBOOK Execution Log Archive

Purpose:
- Store dated execution-log entries rotated out of PLAYBOOK Section 4.
- Keep entries in reverse-chronological order (newest first).

Read helpers:
- `Get-Content docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "<keyword>" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

### 2026-09-26 - Bootstrap fast-paths move below the list; skills-lock.json gets a warn-only manifest

Side task, no batch tag: bootstrap fast-path reorder and the skills-lock.json
untracked-essentials warning, part of Batch 23 WP-0 Part C. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope and result.** `AGENTS.md`'s "Session Bootstrap (in order)" moved
  its two fast-path paragraphs below the numbered bootstrap list, so a skim
  finds the obligation before the exemption (F-B21-25 item 1). A new
  `docsync.declarations.UntrackedEssentialsConfig` /
  `load_untracked_essentials_config` reads a `[untracked_essentials]` table
  from `config/docsync.toml`, which now declares `paths = ["skills-lock.json"]`.
  A new `scripts/dev/_worktree_guard_essentials.py::essentials_diagnostics`
  raises `WT015` at WARNING severity for each declared, gitignored path that
  is missing, silent when present or undeclared; it is wired into
  `inspect_worktree` and re-exported from `scripts/dev/worktree_guard.py`
  (F-B21-25 item 2, partial -- the findings/issues sync stays out per owner
  ruling 2026-09-25). `scripts/dev/_worktree_guard_essentials.py` imports the
  bare `docsync.declarations` name after inserting `scripts/` onto
  `sys.path`, mirroring `scripts/doc_state_sync.py`'s existing convention,
  rather than the brief's `scripts.docsync.declarations` path: that path
  loads under pytest's own `sys.path` setup but double-loads the module
  under two names elsewhere, and `check_worktree_alignment.py` / the
  pre-commit hook only put the repository root on `sys.path`, not `scripts/`.
  Also folded a literal duplication (carried Minor from Task 8's review):
  `scripts/dev/docsync_preflight.py`'s `CONTROL_PLANE_FILES` tuple now
  references `DOCSYNC_TOML_PATH` instead of repeating the `"config/docsync.toml"`
  literal; no behavior change.
- **Mutation proof (L14).** In a scratch copy, deleting
  `diagnostics.extend(essentials_diagnostics(resolved_root))` made the wiring
  test fail (`AssertionError: assert 'WT015' in ['WT000']`); mutating
  `essentials_diagnostics`'s `for relative in config.paths:` to iterate an
  empty tuple made `test_a_missing_declared_path_warns` fail
  (`assert [] == [('WT015', 'WARNING')]`).
- **Live probe.** In an independent clone, a fresh checkout (no
  `skills-lock.json`) printed `WARNING WT015 skills-lock.json -- declared
  untracked-essential file is missing.` at exit 0 (WARNING never blocks);
  creating an empty `skills-lock.json` silenced it, still exit 0.
- **After this task:** `skills-lock.json` remains absent from this worktree,
  so `WT015` now prints on every guard run here, including in pre-commit
  output below -- the intended warning, not a defect (constraints.md R5).
- **Validation.** `pytest -q` -- **1919 passed**.

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

### 2026-09-25 - A work package closes only on an explicit completion line

Side task, no batch tag: Task 3 of the control-plane plan, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope and result.** `_collect_wp_numbers` (`scripts/docsync/parser.py`)
  no longer reads a `(Batch N WP-X)` heading tag alone as completing that
  package (F-DOCSYNC-15, Q4 = a): it now scans each entry's body for an
  explicit `**Status:** WP-N complete` line
  (`WP_COMPLETE_STATUS_RE`, case- and spacing-tolerant) and collects only
  the numbers that line names. `renderer._next_wp_number` and
  `renderer._build_status_block` are unaffected by signature, only by the
  set of numbers `_collect_wp_numbers` now returns; `integrity._computed_next_wp`
  reaches the same change through `_next_wp_number`. A regression test
  reproducing `docs/history/logs/BATCH22_LOG.md`'s three-commit shape
  (`tests/test_docsync_sync_integration.py::
  test_three_tagged_commits_do_not_claim_the_package_done_until_the_last`)
  proves the STATUS block reads "none" complete after the first two tagged
  commits and "WP-4" only once the third carries the completion line.
  Existing fixtures that relied on a bare heading tag reading as complete
  were updated to carry the explicit line: `tests/test_docsync_wp_numbers.py`
  (`TestCollectWpNumbers::test_multiple_wp_tags`, plus five new cases);
  `tests/test_docsync_integrity.py` (`_valid_inputs`'s base WP-0 entry, and
  the fixtures built by `test_doc007_completed_wp_summary_does_not_steal_the_claim`,
  `test_doc007_gap_in_completed_wps_picks_lowest_missing`,
  `test_doc007_absorbed_wp_is_not_demanded`,
  `test_doc007_all_planned_wps_reject_stale_numeric_claims`);
  `tests/test_docsync_sync_integration.py::TestSyncIntegration::
  test_session_status_uses_active_definition_plan`;
  `tests/test_docsync_cli.py::TestMainArgs::
  test_fix_renders_next_wp_from_active_definition_plan`; and
  `tests/test_docsync_renderer.py` (`TestBuildStatusBlock::test_entries_with_wp_gap`,
  `test_planned_wp_gap_skips_absorbed_number`,
  `test_all_planned_wps_complete_renders_no_next_package`,
  `test_preflight_only_plan_can_complete_at_wp_zero`,
  `test_authoritative_count_shows_count`;
  `TestBuildStatusBlockBoundary::test_zero_batch_number`;
  `TestNextWpNumberCountsWpZero::test_wp_zero_done_moves_to_wp_one`,
  `test_legacy_rule_without_a_plan_still_starts_at_one`) -- named in the
  brief's file list only as `renderer.py`'s production code, not its test
  file, and found by re-grepping `_collect_wp_numbers`/`_next_wp_number`/
  `_build_status_block` usage across `tests/` (L15) after the brief's own
  three named test files first came back green. AGENTS.md's commit-procedure
  bullet 1 now states the same rule (F-DOCSYNC-15 closed; see
  `docs/agents/FINDINGS.md`'s archive).
- **Deviation.** `_valid_inputs`'s base fixture in `tests/test_docsync_integrity.py`
  grew by two lines to mark its WP-0 entry complete, which shifted the
  hard-coded insertion indices several other tests in the same file used
  (`playbook_lines[14:14]` etc.) and the absolute line numbers two DOC001
  tests asserted (`test_definition_label_outside_section_3_is_not_exempt`,
  `test_playbook_reference_after_dated_entry_keeps_original_line_number`,
  now 22 instead of 20); all were updated in place, none weakened. The
  brief's own Step 6 regression test, as written, passed unchanged with the
  Step 3 fix reverted (all three commits share the same heading tag, so the
  old heading-only rule also read the final state as WP-4 complete); it was
  rewritten to assert the intermediate state (after only the first two
  commits, before the completion line lands) so the test actually fails
  without the fix (L14, mutation-proved in a `git stash create` scratch copy).
- **Validation.** `pytest -q` -- **1897 passed**.

### 2026-09-25 - The count wrapper's tests are repointed, then the file is split

Side task, no batch tag: Task 2 of the control-plane plan, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope and result.** The eight `TestLatestTestCount` call sites in
  `tests/test_docsync_logic.py` now call
  `latest_test_count_authority(...).count` directly instead of the removed
  `_latest_test_count_from_entries` wrapper (`scripts/docsync/logic.py`),
  proving parity before the file moved (Rule 4). `tests/test_docsync_logic.py`
  (886 lines) is then split along its seven seams: `TestCollectWpNumbers` ->
  `tests/test_docsync_wp_numbers.py`; `TestLatestTestCount` plus the two
  module-level unbold-authority tests, `TestRewriteRecordedCounts` and
  `TestResolvedTestCountAuthority` (Task 1's own additions) -> consolidated
  into the existing `tests/test_docsync_test_count.py`; `TestSyncIntegration`
  -> `tests/test_docsync_sync_integration.py`; `TestMergeEntriesIntoLog` ->
  `tests/test_docsync_log_merging.py`; `TestSplitArchive` and
  `TestDedupSorted` -> `tests/test_docsync_archive_split.py`;
  `TestParseActiveBatchStateConflicting` ->
  `tests/test_docsync_section3_parsing.py`. The three module-level helpers
  `_playbook`, `_playbook_with_entry` and `_playbook_two_same_date_entries`
  moved with `TestResolvedTestCountAuthority`; the first was renamed
  `_authority_playbook` in its new home to avoid colliding with
  `tests/test_docsync_test_count.py`'s own pre-existing `_playbook` helper.
  `tests/test_docsync_logic.py` is deleted. Collected node IDs (path-stripped)
  are identical before and after the split, 50 of them, and the full suite
  count is unchanged. Closes F-DOCSYNC-7, F-MAS-3.
- **Deviation.** The brief's own commit subject was 82 characters; shortened
  per constraints.md R8. The `_playbook` name collision above is not named in
  the brief; renaming the incoming helper was the smallest fix that kept both
  sets of tests passing (no shared helper module, no duplication).
  `DEVELOPMENT.md`'s docsync test-file list named `test_docsync_logic.py`;
  replacing it with the five new files also required correcting the list's
  own "twelve matching" count to "sixteen" to stay internally consistent.
- **Validation.** `pytest -q` -- **1891 passed**.

### 2026-09-25 - An explicit test count pins config/docsync.toml

Side task, no batch tag: Task 1 of the control-plane plan, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope and result.** `--fix --test-count N` now pins `N` in
  `config/docsync.toml`'s new `[test_count]` table
  (`declarations.TestCountConfig`, `load_test_count_config`) and writes the
  SESSION_CONTEXT STATUS block, the Section 1 `Tests` row, the Section 6
  heading and the FINDINGS.md header from that one number in one pass
  (`renderer.rewrite_recorded_counts`, `cli._rewrite_findings_header_count`,
  `cli._rewrite_test_count_pin`). `logic.resolved_test_count_authority`
  (explicit > pinned > `latest_test_count_authority` cold-start fallback) is
  now the one function every DOC005/006/008 check and the STATUS render go
  through, so a same-date tie or an out-of-position correction
  (F-DOCSYNC-11, F-DOCSYNC-22) can never shadow a pinned count again.
  `latest_test_count_authority` itself is unchanged and still the cold-start
  path. A new warning, DOC025 (`logic._newest_dated_test_count`), fires only
  when exactly one Section 4 entry carries the newest date and disagrees
  with the pin; a same-date tie or no pin stays silent, and it never blocks
  (Q1 ruling). Closes F-DOCSYNC-11, -12, -13, -22.
- **Deviation.** `FINDINGS_HEADER_COUNT_RE` (`scripts/docsync/integrity.py`)
  required bare "test modules.", but the repository's real FINDINGS.md
  header reads "... tracked test modules.", so DOC008 never checked it and
  `--fix --test-count N` never rewrote it. Fixed in this commit (an
  under-20-line regex change, AGENTS.md "Proposal and Design Rules" item 2):
  the pattern now accepts an optional "tracked " before "test modules.",
  every existing fixture wording still matches, and a new regression test
  (`tests/test_docsync_cli.py::TestTestCountPin::
  test_findings_header_count_regex_matches_the_real_tracked_wording`) proves
  both legs -- DOC008 fires on a drifted real-wording header, and
  `_rewrite_findings_header_count` rewrites it -- against the regex reverted
  (mutation proof in `task-1-report.md`). No new finding ID; fixed in the
  same commit that built the mechanism. Also tightened
  `test_negative_test_count_returns_2` to assert the Step 14 CLI guard's own
  message text, isolating it from `declarations._positive_int`'s
  independent downstream rejection of the same value (mutation-proved: the
  test now fails if only the CLI guard is removed).
- **Validation.** `pytest -q` -- **1891 passed**.
- **Step 19 live probe** (full detail and every command in
  `.superpowers/sdd/2026-09-25-batch23-wp0-control-plane/task-1-audit.md`
  Section 4, gathered by the audit dispatch at `/c/ssprobe`):

  | # | Probe | Corpus | Steps | Exit | Codes |
  |---|---|---|---|---|---|
  | 1 | Red, prior behaviour | `f8fb8e9` (no Task 1 code) | Insert same-date pair (window entry 1850, side-task entry 1849, both 2026-09-25) -> bare `--fix` -> `--check` | 1 | `ERROR DOC006` (STATUS block rewritten to the wrong tie-break winner 1849) |
  | 2 | Red, planted | task tree, pinned=1873 (clean) | Hand-edit Section 1 Tests row to 1874, leave the pin at 1873 | 1 | `ERROR DOC005`, `ERROR DOC006` |
  | 3 | Green, real workflow | task tree, fresh | New dated entry **999 passed** -> `--fix --test-count 999` -> `--check` | 0 | Pin=999; STATUS/Section 1/Section 6 all show 999 |
  | 4 | Near-miss green | same tree | Bare `--fix` again -> `--check` | 0 | No changes found; pin and all sites unchanged at 999 |
  | 5 | DOC025 (warning only) | same tree, pinned=999 | Add a strictly-newer sole entry (2026-09-26, **1000 passed**) -> bare `--fix` -> `--check` | 0 | `WARNING DOC025` printed, pin stays at 999, exit 0 |
- **Forward guidance.** Task 2 repoints `TestLatestTestCount`'s callers and
  splits `tests/test_docsync_logic.py` along F-MAS-3's seven concerns.

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

### 2026-09-25 - Empty release checks log their finish

Side task, no batch tag: the Batch 23 WP-0 reconciliation review found that
`run_release_checks` logged a start for zero candidates and then returned
without the finish line Task 13 promises. The normal disabled path still logs
its skip at enqueue; this change addresses only the empty done path.

- **Scope and fix.** F-B23-7 records the gap. The zero-candidate branch
  writes the same finish fields as a processed pass, before returning.
  The existing `test_run_release_checks_finishes_without_a_db_trip_when_nothing_qualifies`
  now asserts the start and finish lines as well as the done state.
- **Validation.** The new finish assertion failed before the fix and passed
  after. `pytest -q` -- **1873 passed** with the untracked mutation-test
  file excluded. Pre-commit and docsync checks pass on the documented tree.
- **Forward guidance.** The remaining WP-0 review corrections are document
  state and citation work. WP-0 itself remains open.

### 2026-09-25 - Docsync refuses ambiguous document paths

Side task, no batch tag: the completed Batch 23 WP-0 root-cleanup audit found
that two `[documents]` roles could name one file and leave another unscanned
while `--check` passed. An outside path crashed after a read; an outside
`--config` worked for `--check` but could not enter a write transaction.

- **Scope and fix.** F-DOCSYNC-21 records the reproduced cases. Validate all
  five live document paths for containment and distinctness before any corpus
  read. Require an explicit config path inside the repository, preserving the
  publication transaction's source-snapshot boundary. Clarify the CLI help
  and documentation. F-DOCSYNC-6 retains only its case-glob item.
- **Validation.** The new path tests failed before the fix and passed after.
  A live duplicate-path `--check` probe exited 2 with the two roles named;
  an outside-config probe exited 2 before a read. The valid corpus's
  `--check` exited 0. `pytest -q` -- **1873 passed** with the owner's
  untracked mutation-test file excluded; that file adds 46 local tests and is
  not part of this commit. Pre-commit and final docsync checks passed.
- **Forward guidance.** The root-cleanup plan's path resolver now has the
  same containment rule in check and write modes. Continue the WP-0 review
  side task, then return to the remaining Part B and Part C work.

### 2026-09-24 - Docsync diagnostics name the declared document path

Side task, no batch tag: the root-cleanup plan's Task 8, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands. The last task of the root-cleanup plan.

- **What changed.** `scripts/docsync/integrity.py`: `_active_definition_reference`,
  `_unpaired_result_issue`, `_check_unbolded_test_counts`,
  `_check_section3_next_wp` and `_check_findings_header_count` each gain a
  `playbook_relative_path`/`findings_relative_path` keyword (default: today's
  literal), and every diagnostic they build prints it instead of the bare
  root name; `collect_integrity_issues` threads its own two matching keyword
  arguments (already present since Task 2) into all five, and its own two
  direct DOC002 sites do the same. `scripts/docsync/closeout.py`:
  `_admission_issue` and `_claim_issues` gain the same
  `playbook_relative_path` keyword; `collect_transition_issues` threads it
  through. `scripts/docsync/cli.py`'s `_close_batch` passes
  `documents.playbook` into `collect_transition_issues`, and its
  `SyncError` message ("... has no batch index row for batch ...") now
  names `documents.playbook` instead of a bare `PLAYBOOK.md`.
  `scripts/docsync/findings.py`: `_lifecycle_issues`, `_duplicate_issues`,
  `collect_rot_issues` and `plan_findings` gain an `active_path` keyword
  (default: `ACTIVE_PATH`); `collect_integrity_issues`'s call into
  `findings_module.collect_rot_issues` and `cli.py`'s `_Corpus.rotation`
  (via a new `self.findings_relative_path`) both pass their declared path.
  `ARCHIVE_PATH` (the findings archive, never moved) is untouched. Grepped
  `scripts/docsync/` afterwards: no `"PLAYBOOK.md"` or `"FINDINGS.md"`
  literal remains as a diagnostic location, only default keyword values,
  the `LIVE_DOCUMENT_RELATIVE_PATHS`/`DocumentsConfig` constants (Task 2's
  scope) and prose in a docstring/comment.
- **Tests.** `tests/test_docsync_integrity.py`: two DOC002 tests (the
  `_active_definition_reference` direct site and `collect_integrity_issues`'s
  candidate-mismatch site), one DOC007 test (`_check_section3_next_wp`), one
  parametrized DOC012 test covering `_check_unbolded_test_counts`'s three
  internal branches including `_unpaired_result_issue`, and one DOC008 test,
  all via a new `_inputs_with_document_paths` fixture helper. One pre-existing
  test, `test_definition_line_skip_is_honoured_under_an_overridden_playbook_path`
  (written for Task 2, its own docstring naming Task 8 as the task that would
  thread the DOC002 diagnostic's path further), asserted the stale bare
  `"PLAYBOOK.md"` literal for that DOC002 diagnostic under an overridden
  playbook path; updated to the declared path (deviation, precedence rule
  "brief and reality disagree": the test exercises exactly the mechanism
  this task changes). `tests/test_docsync_closeout.py`: one test each for
  `_claim_issues` and the admission-boundary refusal via
  `collect_transition_issues`. `tests/test_docsync_findings.py`: one test
  per DOC013, DOC014, DOC015, DOC016, DOC017, DOC018 and DOC023, all via
  `plan_findings`/`collect_rot_issues`'s new `active_path` keyword. Every
  new test failed before the change (RED: a `TypeError` for the unknown
  keyword, or the stale-literal path for the one DOC008 fixture that
  predates the keyword) and passes after it.
- **Live probe**, `/c/ssprobe`, from `git archive $(git stash create)` with
  this task's changes in the tree (L18):
  - DOC007: edited `docs/agents/PLAYBOOK.md` Section 3's `**Next action:**`
    line to claim a WP that disagrees with the definition -- red, DOC007
    printed `docs/agents/PLAYBOOK.md:<line>`.
  - DOC002: pointed Section 3's `Definition:` reference at a missing file
    -- red, DOC002 printed `docs/agents/PLAYBOOK.md` as its location.
  - Reset both edits -- green, `--check` exited 0 (the standing DOC024/root
    BATCH warnings from section 2b aside).
- **Deviations:**
  - `docs/agents/PLAYBOOK.md`'s own Section 3 completion sentence for this
    task avoids backticking the pre-move `PLAYBOOK.md`/`FINDINGS.md` names:
    a backtick-wrapped `.md` name that does not resolve from the repository
    root fails DOC001 (L20), the same lesson Task 6 recorded.

Validation: `pytest -q` -- **1866 passed**.

### 2026-09-24 - The four agent documents move to docs/agents/

Side task, no batch tag: the root-cleanup plan's Task 6, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **What changed.** `PLAYBOOK.md`, `FINDINGS.md`, `AGENT_NOTES.md` and
  `HANDOFF_PROMPT.md` move to `docs/agents/` (`git mv`). `config/docsync.toml`
  gains a `[documents]` table declaring the four new paths; its
  `AGENT_NOTES.md` value-site and all four `[retired.allow_after]` keys
  (and the comment above the fourth) now read `docs/agents/PLAYBOOK.md`.
  `scripts/docsync/cli.py` reads and writes every document through a new
  `_documents()`/`_declarations_path()` pair instead of the deleted
  `PLAYBOOK_PATH`/`FINDINGS_PATH` constants (`_Corpus.__init__`,
  `_read_live_documents`, `_drift_updates`, `_candidate_live_documents`,
  `_collect_issues` and `_close_batch`'s two `collect_integrity_issues`
  calls). `scripts/dev/_worktree_guard_inspection.py` reads
  `docs/agents/PLAYBOOK.md`; `_worktree_guard_diagnostics.py`'s
  `metadata_unavailable_diagnostic` label follows.
  `scripts/docsync/renderer.py` drops the path from `_build_status_block`
  and `SIDE_ARCHIVE_PREFIX` entirely (owner ruling: no document path in
  generated text) -- `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`'s
  prologue matches by hand where `--fix` did not rewrite it.
  `.pre-commit-config.yaml`'s top-level exclude changes `docs` to
  `docs(?!/agents/)` (owner-approved 2026-09-24), keeping `docs/agents/`
  under `trailing-whitespace`, `end-of-file-fixer`, `check-merge-conflict`
  and `detect-private-key`. Every live present-tense citation of the four
  names is repointed: `AGENTS.md`, `docs/agents/domain.md`,
  `docs/agents/global-rules.md`, `docs/agents/issue-tracker.md`,
  `docs/agents/AGENT_NOTES.md`, `docs/agents/FINDINGS.md`,
  `docs/agents/PLAYBOOK.md` Section 3, `DEVELOPMENT.md`, `PRODUCT.md`,
  `docs/ARCHITECTURE.md`, `docs/architecture/documentation-tooling.md`
  (including the mermaid node labels), `docs/architecture/development-cycle.md`,
  `docs/AGENT_DOC_MAP.md`, `docs/design/RECONCILIATION.md:667`,
  `docs/SWE_AUDIT_CHARTER.md` (9), `BATCH23_DEFINITION.md` (2 present-tense
  pointers), `.claude/SESSION_CONTEXT.md`,
  `.superpowers/cloud-kit/constraints.md` (including its literal
  `grep ... PLAYBOOK.md` command), `docs/history/reports/HANDOFF_2026-09-24.md`
  (sections 2/3/8 only; its section 6 narrative of past rulings is left as
  written, point-in-time), `.gitignore`'s committed-files comment,
  `scripts/dev/graphify_refresh.py`, `scripts/dev/install_docsync_hook.py`
  (two comments) and `scripts/docsync/declarations.py`'s `DocumentsConfig`
  docstring (its field defaults stay bare, by Task 2's design).
- **Tests.** `tests/scripts/dev/test_worktree_guard_playbook.py`
  (`test_the_repository_playbook_parses`, Step 1) reads the new path.
  `tests/scripts/dev/worktree_guard_fakes.py`'s `repository()` fixture, and
  `test_worktree_guard_base_ref.py`, `test_worktree_guard_inspection.py`,
  `test_worktree_guard_subject.py` and `test_worktree_guard_topology.py`'s
  own `PLAYBOOK.md`-writing helpers, all write to
  `repo/docs/agents/PLAYBOOK.md` (a named, load-bearing edit: reverting the
  guard's own code fix and re-running the six worktree-guard test files
  reproduces 29 failures; restoring the fix returns all 74 to green).
  `tests/conftest.py`'s `sync_env` no longer monkeypatches the deleted
  `PLAYBOOK_PATH` (the fixture writes no `[documents]` table, so the
  default relative name still resolves). `tests/test_docsync_renderer.py`'s
  `test_declared_batch_with_no_entries_renders_as_open` and
  `test_between_batches_block_carries_the_count` copy the status-block line
  by value; both updated to the new text (RED before, GREEN after).
- **Live probe**, `/c/ssprobe`, from `git archive $(git stash create)` with
  this task's changes in the tree (L18):
  - Pre-commit exclude: planted `<<<<<<< HEAD` (with a simulated merge
    state, since `check-merge-conflict` only scans when `MERGE_HEAD` and
    `MERGE_MSG` exist) in `docs/agents/PLAYBOOK.md` -- red,
    `check-merge-conflict` failed; the same marker in
    `docs/history/reports/` -- green, passed.
  - `[retired.allow_after]`: none of the four declarations' retired claims
    are still live in the current corpus, so a bare key revert alone proved
    nothing; planted one claim below the Section 4 heading, then reverted
    the fonts-retirement key to `PLAYBOOK.md` -- red, DOC011 fired as a
    false positive; restored the key -- green.
  - Worktree guard: reverted `_worktree_guard_inspection.py`'s literal to
    `PLAYBOOK.md` -- red, WT002 "PLAYBOOK.md could not be read"; restored
    -- green, Section 3 read (the corpus's own WT003/WT007/WT009 branch,
    remote and venv gaps are unrelated to the PLAYBOOK read).
  - DOC001 sweep: left one bare `` `PLAYBOOK.md` `` citation in `AGENTS.md`
    -- red, DOC001 named it; restored to `` `docs/agents/PLAYBOOK.md` `` --
    green.
  - `[documents]` honoured: set `playbook = "docs/agents/NOWHERE.md"` --
    red, `--check` failed naming the missing file; restored -- green.
- **Deviations:**
  - `_Corpus.read_paths()` gained the declarations file as a source (a new
    `_declarations_path()` helper): `_documents()` now reads
    `config/docsync.toml` during `_Corpus.__init__`, which
    `test_close_batch_proves_every_read_source_before_publishing` (not
    named in the brief) proved must be in the publish-time read set, or a
    concurrent edit to the declarations file would go unnoticed.
  - `.gitignore`'s `docs/agents/*` carve-out did not list the four moved
    files; a plain `git add` (not `git mv`) silently dropped them, caught
    by the Step 9 probe corpus. Added the four negations beside the
    existing four.
  - `BATCH23_DEFINITION.md`'s "Move ... to `docs/agents/`" bullet keeps the
    pre-move names unbackticked: still `.md` files, but no longer DOC001
    citations. A backtick-wrapped `.md` name after the move is a dead
    reference DOC001 rightly flags, unlike Task 5's `.docsync.toml`
    precedent this bullet otherwise mirrors (a `.toml` name the check never
    matches).
- **Fix round 1** (review): the "every live present-tense citation" claim
  above missed two sites invisible to `doc_state_sync.py --check` (inside a
  Python docstring/comment, not scanned Markdown):
  `scripts/dev/frontend_gate.py`'s `_load_check_manifest` docstring still
  cited `AGENT_NOTES.md`, and `scripts/dev/_worktree_guard_inspection.py`'s
  `OSError`-branch `detail` literal still read "PLAYBOOK.md could not be
  read." three lines below this task's own `playbook_path` fix. Both
  repointed to `docs/agents/`. Added
  `test_unreadable_playbook_names_the_moved_path_in_the_detail` (new,
  RED before the fix, GREEN after) since the diagnostic's literal text was
  previously untested.

Validation: `pytest -q` -- **1850 passed**.

### 2026-09-24 - The Repo Assist workflow points at the moved documents

Side task, no batch tag: the root-cleanup plan's Task 7, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **What changed.** `.github/workflows/repo-assist.md`'s two `allowed-files`
  lists (`create-pull-request` and `push-to-pull-request-branch`) now name
  `docs/agents/PLAYBOOK.md` and `docs/agents/FINDINGS.md` in place of the root
  paths. The "Repository Rules" prose's grant (rule 3, "anything under
  `scripts/` or `docs/` other than...") now permits exactly those two paths
  alongside the log files, agreeing with the allowed-files lists. Every other
  prose mention of the two names (the frontmatter description, rules 2 and 4,
  and Task 11's mirror-hygiene step) is repointed the same way; the last one
  is not among the brief's cited line ranges but carries the same root path
  (L15). `AGENT_NOTES.md` and `HANDOFF_PROMPT.md` are not named anywhere in
  the workflow source, so nothing else needed a change.
- **Recompiled** with `gh aw compile repo-assist` (installed `gh-aw`
  v0.89.21, the version that produced the previous lock file). The compile
  touched no tracked file besides `repo-assist.md` and `repo-assist.lock.yml`,
  and asked for no `--approve`. The lock diff is the metadata hash pair plus
  the six path-copy lines the brief names (two header-comment lines, two
  `WORKFLOW_DESCRIPTION` copies, and the `GH_AW_SAFE_OUTPUTS_CONFIG` /
  `GH_AW_SAFE_OUTPUTS_HANDLER_CONFIG` `allowed_files` arrays) -- never
  hand-edited.
- **Tests.** None; this task touches no test-bearing code path.
- **Gates.** `pytest -q`, `pre-commit run --all-files` and
  `doc_state_sync.py --check` all pass; the frontend gate's `when` condition
  (a changed path under `static/`, `templates/` or
  `scripts/dev/_frontend_gate_`) does not match, so it is skipped.

Validation: `pytest -q` -- **1849 passed**.

### 2026-09-24 - The docsync declarations file moves under config/

Side task, no batch tag: the root-cleanup plan's Task 5, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **What changed.** `.docsync.toml` moves to `config/docsync.toml`
  (`git mv`). `scripts/docsync/declarations.py`'s `DECLARATIONS_FILENAME`
  and its `_TOP_LEVEL_SCHEMA` comment follow the move.
  `scripts/dev/docsync_preflight.py`'s `CONTROL_PLANE_FILES` entry and its
  exact-match comment now name `config/docsync.toml`, and no longer
  recognize the retired root name. `scripts/docsync/findings.py`'s DOC023
  remediation and `scripts/docsync/closeout.py`'s DOC019 remediation now
  interpolate `DECLARATIONS_FILENAME` so a future move cannot strand them;
  the comments in `scripts/docsync/archives.py` and two in
  `scripts/docsync/integrity.py` name the new path. Every live
  present-tense citation of the old path is corrected: `AGENTS.md`,
  `AGENT_NOTES.md` (3), `DEVELOPMENT.md` (4), `docs/ARCHITECTURE.md`,
  `docs/agents/global-rules.md`, `docs/architecture/documentation-tooling.md`
  (7, including the mermaid node label and the sentence that said the file
  sits "at the repository root"), `.pre-commit-config.yaml` (comment),
  `.superpowers/cloud-kit/constraints.md` (R7), `scrobblescope/heatmap.py`
  (comment), `static/css/tailwind.src.css` (comment), and `FINDINGS.md`'s
  three open, present-tense mentions (F-B21-17's remaining-work note and
  F-DOCSYNC-9's two `[[diagram]]` mentions). Left as written, by the
  brief's own rule: `BATCH23_DEFINITION.md` (states the move itself),
  `FINDINGS.md`'s two mentions of the F-DOCSYNC-16 fix round (a dated past
  edit), and every `docs/superpowers/plans/*.md` / `docs/superpowers/
  specs/*.md` document (plans and specs of completed or historical work).
- **Tests.** Every declarations-writing fixture is repointed at the
  `DECLARATIONS_FILENAME` symbol rather than the literal name, with its
  parent directory created first: `tests/conftest.py` (`sync_env`),
  `tests/test_docsync_cli.py` (`_make_corpus`'s base dict and six override
  call sites -- `_write` already creates parent directories), `tests/
  test_docsync_declarations.py` (`TestDocumentsConfig`'s three writers, and
  four more writers found only by re-grepping at this task's own HEAD --
  `test_a_malformed_declarations_file_is_a_declaration_error`,
  `test_an_unknown_table_name_is_refused`, `test_a_misspelled_option_is_
  refused`, `test_a_top_level_declaration_collection_must_be_a_list` --
  plus four prose docstrings/comments reworded to say "declarations file"),
  `tests/test_docsync_integrity.py` (`_write_closeout_boundary` and
  `test_doc023_honours_the_repositorys_grandfather_list`, plus two prose
  docstrings), `tests/scripts/dev/test_docsync_preflight.py`
  (`test_staged_preflight_against_real_docsync_checker`'s writer and its
  `git add` list). `test_control_plane_prefix_matching`'s parametrize list
  now asserts `config/docsync.toml` is control-plane and the retired
  `.docsync.toml` is not. `tests/test_template_shell.py`'s `.docsync.toml`
  comment is repointed. No suite count change beyond the one new
  parametrize row. Edited for reasons other than the move: none.
- **Frontend gate ran locally** (the `static/css/tailwind.src.css` comment
  edit; `python scripts/dev/tailwind_build.py --check` shows no drift), its
  last line: `[frontend_gate] 30 checks passed in 52 runs across chromium,
  firefox (static assets & tokens canary on firefox); profiles: desktop,
  mobile, wide touch`.
- **Live probe**, throwaway corpus at `/c/ssprobe` (deleted afterwards),
  built from `git archive $(git stash create)` (Lesson L18: this task's
  probe step runs before its commit, so HEAD was still BASE):

  | Probe | Expected | Exit |
  |---|---|---|
  | Faithful copy: `doc_state_sync.py --check` in the corpus | byte-identical to the same command in the worktree (both pending the count refresh this entry makes) | 1 (identical both sides) |
  | Declared check is live: append `[nonsense]` to `config/docsync.toml`, `--check` | refuses the unknown table, naming `config/docsync.toml`; reset | 2 |
  | Red: edit a comment in `config/docsync.toml`, stage it, `docsync_preflight.py --staged` | control-plane refusal naming `config/docsync.toml`; reset | 3 |
  | Near-miss green: stage a root `.docsync.toml` with any content, same command | no control-plane refusal -- the checker runs (a `.venv` junction was needed for the probe's own precondition; the run then hit the same pending DOC006/DOC008 as the faithful-copy row, not a control-plane one) | 1 (no EXIT_CONTROL_PLANE_REJECTED) |

Validation: `pytest -q` -- **1849 passed**.

### 2026-09-24 - The check manifest moves under config/

Side task, no batch tag: the root-cleanup plan's Task 4, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **What changed.** `frontend_gate_checks.toml` moves to
  `config/frontend_gate_checks.toml` (`git mv`), the same commit as the
  constant update (the riskiest single step in this plan by import-time
  coupling). `scripts/dev/frontend_gate.py`'s `CHECK_MANIFEST_PATH`, the
  comment above it, and the missing-manifest `FrontendGateError` message
  ("Restore config/frontend_gate_checks.toml.") all follow the move. The
  manifest's own header comment, and the two live documents that called it
  "root-level" (`DEVELOPMENT.md`, `docs/architecture/documentation-tooling.md`),
  now say it sits under `config/`, naming the docsync declarations file
  without a path until Task 5 moves it.
- **Tests.** None added (R3): the manifest-specific tests build their own
  `tmp_path` manifest. All twelve `tests/scripts/dev/test_frontend_gate_*.py`
  modules still collect and pass (316 tests).
- **Frontend gate ran locally** on this commit (plan Step 3), its last
  line: `[frontend_gate] 30 checks passed in 52 runs across chromium,
  firefox (static assets & tokens canary on firefox); profiles: desktop,
  mobile, wide touch`.
- **Live probe**, throwaway corpus at `/c/ssprobe` (deleted afterwards),
  built from `git archive $(git stash create)` (Lesson L18: this task's
  probe step runs before its commit, so HEAD was still BASE):

  | Probe | Expected | Exit |
  |---|---|---|
  | Red: remove `config/frontend_gate_checks.toml`, commit, then `python -c "from scripts.dev import frontend_gate"` | prints `[frontend_gate] ERROR: check manifest missing at .../config/frontend_gate_checks.toml. Restore config/frontend_gate_checks.toml.` (`FrontendGateError` converted to `SystemExit`) | 1 |
  | Near-miss green: restore the file with a trailing blank line added (still valid TOML), same import | imports silently | 0 |

Validation: `pytest -q` -- **1848 passed**.

### 2026-09-24 - A --config override lets every check read a different declarations file

Side task, no batch tag: the root-cleanup plan's Task 3, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **What changed.** `scripts/docsync/cli.py` gains a `--config PATH`
  argument and a module-level `CONFIG_PATH`, set by `main()` for the length
  of one invocation and restored in a `finally`. Every declarations read in
  `cli.py` -- the four `load_archive_config`/`load_closeout_config` call
  sites and both `collect_integrity_issues` calls -- now forwards it.
  `declarations.load_declarations` refuses an explicit `config_path` that is
  not a file (a mistyped `--config` no longer means "run every check with
  nothing declared, and pass"), and its TOML-decode error names the file
  actually read. `collect_declaration_issues` takes the same kwarg, and its
  unknown-table error names `config_path` when one was given, the repository
  default otherwise. `integrity.collect_integrity_issues` gains and forwards
  the same kwarg to its three reads. `docs/architecture/documentation-tooling.md`'s
  CLI-surface section documents `--config` as an option, not a mode.
- **Tests.** Six new tests: `tests/test_docsync_declarations.py::
  TestExplicitConfigPath` (three) and `tests/test_docsync_cli.py::
  TestConfigOverride` (three). Each proved by scratch-copy mutation
  (`git stash create`, never the real tree): reverting the explicit-missing-
  path refusal alone fails `test_explicit_missing_path_is_refused`; giving
  `--config` a non-`None` default alone fails
  `test_config_flag_defaults_to_none`; reverting `collect_declaration_issues`'s
  `config_path` forwarding alone fails
  `test_config_selects_the_declarations_file_every_check_reads`; reverting
  the `finally` restore alone fails
  `test_main_restores_config_path_after_the_run`.
- **Live probe**, throwaway corpus at `/c/ssprobe` (deleted afterwards):

  | Probe | Expected | Exit |
  |---|---|---|
  | Faithful copy: `--check` on the probe corpus | Same summary as the real tree (DOC024 x4, root-BATCH warning) | 0 |
  | Red 1: `--check` alone vs `--check --config alt.toml`, where `alt.toml` is a copy of the declarations file plus `[nonsense]` | Plain `--check` unaffected; `--config alt.toml` refused, naming `alt.toml`'s unknown table | 0 then 2 |
  | Red 2: `--check --config nowhere.toml` | Refused, naming `nowhere.toml` | 2 |
  | Near-miss green: `--check --config alt.toml`, `alt.toml` an unchanged copy | Identical summary to plain `--check` | 0 |

- **Deviations:** the probe corpus was built from `git archive $(git stash
  create)` rather than the plan's literal `git archive HEAD`. This task's
  own Step 5 (probe) runs before Step 6 (commit), so `HEAD` at probe time
  was still BASE and had no `--config` to probe; `git stash create` (Lesson
  L9/L18) captured the uncommitted implementation instead.

Validation: `pytest -q` -- **1848 passed**.

### 2026-09-24 - The handoff catches up with the root cleanup's first three tasks

Side task, no batch tag: the sixth (cloud) session's handoff revision,
part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **What changed.** `docs/history/reports/HANDOFF_2026-09-24.md` records
  root-cleanup Tasks 0-2 done and Task 3 next, with the two notes Task 3's
  brief needs that the plan lacks. It also drops three claims the merge of
  `main` made false: that PR #242 was still to be merged in, that the guard
  fails against `origin/main`, and that pre-commit always prints WT005.
  Section 8 gains two traps from this session: a plan's own heading can
  break R1, and an adapted test can stop testing the change.
- **Task 2's fix round.** The owner waived its re-review. The controller
  verified it by mutation in a scratch copy instead: reverting the
  scan-source comparison alone fails only
  `test_playbook_entry_block_reference_is_blanked_under_an_overridden_playbook_path`,
  and reverting the definition-line comparison alone fails only
  `test_definition_line_skip_is_honoured_under_an_overridden_playbook_path`.
- **Deviations:** none. Docs only.

Validation: `pytest -q` -- **1842 passed**.

### 2026-09-24 - The documents-table tests prove the playbook override

Side task, no batch tag: fix round 1 on the root-cleanup plan's Task 2, part
of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole
of WP-0 lands.

- **Finding.** The earlier Task 2 entry's claim -- that
  `test_collect_integrity_issues_scans_under_an_overridden_playbook_path`
  "exercises the actual kwarg-driven behaviour" of `collect_integrity_issues`
  -- was false for the `playbook_relative_path` half of it. The review proved
  by scratch-copy mutation (`git archive HEAD`, never the real tree) that
  reverting either `path == playbook_relative_path` comparison in
  `collect_integrity_issues` (`scripts/docsync/integrity.py` ~992, ~997)
  back to the hardcoded `path == "PLAYBOOK.md"` leaves that test green: its
  fixture has no dated Section 4 entry to blank and no active-batch
  definition line, so both comparisons are inert for it. Only
  `documents_to_scan = set(document_paths)` was actually covered. The
  production code itself was already correct; this is a test-coverage and
  documentation-truth gap.
- **Fix.** That test's docstring is corrected to claim only what it proves
  (the `document_paths`/scan-set substitution) and now names the two tests
  below for the other two comparisons. Two new tests added to
  `tests/test_docsync_integrity.py`:
  - `test_playbook_entry_block_reference_is_blanked_under_an_overridden_
    playbook_path` makes the scan-source comparison (~992) load-bearing:
    a dead reference inside a dated Section 4 entry is blanked and not
    reported, the same reference in Section 3 is reported, both under an
    overridden `playbook_relative_path`; mirrors
    `test_playbook_reference_after_dated_entry_keeps_original_line_number`
    and `test_definition_label_outside_section_3_is_not_exempt`.
  - `test_definition_line_skip_is_honoured_under_an_overridden_playbook_path`
    makes the definition-line skip (~997) load-bearing: an untracked active
    definition reference reports DOC002 once and not also DOC001, under the
    override; mirrors `test_untracked_active_definition_is_blocking`.
- **Mutation proof** (scratch copy under this session's scratchpad, `git
  archive HEAD | tar -x`, the new test file copied in; the real working
  tree was never edited, staged or reverted, per Lesson L9):
  - Reverting the scan-source comparison alone ->
    `test_playbook_entry_block_reference_is_blanked_under_an_overridden_
    playbook_path` fails: `AssertionError: ... Left contains one more item:
    ('DOC001', 'docs/agents/PLAYBOOK.md', 9)` (the entry-block reference is
    no longer blanked). The other two new/adjacent tests still pass.
  - Restoring that comparison and reverting the definition-line skip alone
    -> `test_definition_line_skip_is_honoured_under_an_overridden_playbook_
    path` fails: `AssertionError: ... Left contains one more item:
    ('DOC001', 'docs/agents/PLAYBOOK.md', 5)` (the untracked definition
    reference is now double-reported). The other two tests still pass.
- **Validation:** `pytest -q` -- **1842 passed** (+2: the two new tests
  above; module count unchanged at 68). `pre-commit run --all-files`
  passed clean, worktree-alignment printing only `WARNING WT010` and
  `INFO WT000`. `doc_state_sync.py --check` exited 0 with the standing
  DOC024 warnings (L7); this commit touches only test and doc files, so
  no `scripts/docsync/` control-plane file is staged and the preflight
  does not refuse it -- committed without `SKIP=doc-state-sync-check`.

### 2026-09-24 - A declared [documents] table for docsync's own live documents

Side task, no batch tag: Task 2 of the root-cleanup plan, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope.** Task 2 of the root-cleanup plan
  (`docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`):
  `declarations.DocumentsConfig` (fields `playbook`, `findings`,
  `agent_notes`, `handoff_prompt`, each defaulting to today's literal) and
  `declarations.load_documents_config` read an optional `[documents]` table
  from `.docsync.toml`, refusing an unknown key or a non-string value.
  `integrity.resolved_live_document_paths(documents)` mirrors
  `LIVE_DOCUMENT_RELATIVE_PATHS`'s shape and order from a `DocumentsConfig`.
  `collect_integrity_issues` gains three optional kwargs --
  `document_paths`, `playbook_relative_path`, `findings_relative_path` --
  each defaulting to today's literal, so DOC001's scan set and the two
  `path == "PLAYBOOK.md"` comparisons and the two `FINDINGS.md` lookups
  (the header-count and DOC023 checks) can be pointed at a declared path.
  No file moves in this task: every default stays today's literal, and the
  fourteen `PLAYBOOK.md`/twelve `FINDINGS.md` diagnostic path labels are
  left unchanged (Task 8 threads the declared path into them, owner ruling
  2026-09-24). `load_declarations`/`load_archive_config`/
  `load_closeout_config`/`load_findings_config` gained a `config_path`
  keyword so a caller can point at a throwaway `.docsync.toml` directly.
- **TDD.** `tests/test_docsync_declarations.py::TestDocumentsConfig` (4
  tests) and three new tests in `tests/test_docsync_integrity.py` were
  written first and confirmed RED (`ImportError`/`TypeError` -- see the
  report). One deviation from the brief's literal third integrity test:
  `collect_integrity_issues` scans the document named
  `playbook_relative_path` from the *structural* `playbook_lines` argument
  via `_playbook_lines_without_entry_blocks` (`scripts/docsync/integrity.py`),
  which requires `playbook_lines` to carry real `## 3. Active batch` and
  `## 4. Execution log` headings (`_find_section`,
  `scripts/docsync/parser.py`) or it raises `SyncError` uncaught -- a
  pre-existing requirement this task's kwargs do not touch. The brief's
  bare one-line `playbook_lines` hits that unrelated `SyncError` instead of
  proving the DOC001 rescan, so the test gives `playbook_lines` the
  minimal real structure instead (same assertion, `repo_root=tmp_path`
  in place of `Path(".")` so the test does not depend on this
  repository's own `.docsync.toml`). Recorded here rather than left as a
  silent difference from the brief's pasted code block.
- **Live probe** (throwaway corpora under this session's scratchpad,
  `git init` + `git add -A` + commit in each so `git ls-files` resolves;
  `git archive <sha>` for the pre-task state, `git archive $(git stash
  create)` for this task's tree, per Lesson L9):
  - Baseline (BASE `e48d08e`, `[documents]` appended to `.docsync.toml`):
    `python scripts/doc_state_sync.py --check` -> exit 2,
    `doc_state_sync failed: .docsync.toml has an unknown table
    'documents'. Known tables: anchor, archives, closeout, findings,
    options, retired, value.`
  - Red (this task's tree, `[documents]\nnotebook = "x.md"` appended):
    `python scripts/doc_state_sync.py --check` -> exit 2,
    `doc_state_sync failed: [documents] has an unknown key 'notebook'.
    Known keys: agent_notes, findings, handoff_prompt, playbook.`
  - Near-miss green (reset, then `[documents]\nplaybook = "PLAYBOOK.md"`
    appended): `python scripts/doc_state_sync.py --check` -> exit 0, the
    same summary line as the unmodified corpus's own `--check`.
- **Validation:** `pytest -q` -- **1840 passed** (+7: `TestDocumentsConfig`'s
  4 tests and 3 new tests in `tests/test_docsync_integrity.py`; module count
  unchanged at 68). `ruff check`/`ruff format` auto-fixed one lint issue and
  reformatted two files on the first `pre-commit run --all-files`; the
  second run passed every hook clean, worktree-alignment printing only
  `WARNING WT010` (dirty tree) and `INFO WT000` (R6). `doc_state_sync.py
  --check` exited 0 with the standing DOC024 warnings (L7); this task
  touches `scripts/docsync/`, so the commit uses `SKIP=doc-state-sync-check`
  (R7), never `--no-verify`.

### 2026-09-24 - The handoff stops calling the approved plan a draft

Side task, no batch tag: fix round 1 on the root-cleanup plan's Task 1,
part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **Finding.** The task review found
  `docs/history/reports/HANDOFF_2026-09-24.md`'s revision note still saying
  the root-cleanup plan "is committed as a draft", against its own section
  5 item 5, which Task 1 updated to say the owner approved it. The note is
  now past tense and points at section 5 item 5. A grep for other "draft"
  claims about the plan in the handoff, the cloud-kit constraints,
  SESSION_CONTEXT, AGENT_NOTES, the batch definition and PLAYBOOK Section 3
  found none.
- **Deviations:** the review's minor finding stays open: one line of Task
  1's commit body is 73 characters, one over the 72-character wrap. Fixing
  it would mean amending that commit, a history rewrite, so it stays as
  written.

Validation: `pytest -q` -- **1833 passed**.

### 2026-09-24 - The root cleanup joins the reconcile work

Side task, no batch tag: the root-cleanup task joins WP-0 Part B, part of
Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of
WP-0 lands.

- **Scope.** Task 1 of the root-cleanup plan
  (`docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`): record
  the scope change before any file moves (Proposal Rule 1). `BATCH23_DEFINITION.md`
  Part B gains a "Root cleanup" bullet naming the plan and the acceptance
  criterion it must meet. PLAYBOOK Section 3's "Next action" item 3 now
  names the root-cleanup plan's path and states Task 0 and Task 1 done,
  Tasks 2-8 remaining, instead of describing the plan as a draft.
- **Plan bookkeeping.** The plan's own status paragraph and "Revisions
  applied" section are deleted: the plan is committed in its approved form
  in this same commit. Task 1's four step checkboxes are ticked.
- **Sibling sweep.** `docs/history/reports/HANDOFF_2026-09-24.md` section 3
  no longer cites the plan's deleted "Revisions applied" section; it now
  points at the plan's task list and its "verification standard for
  control-plane tasks". Section 5 item 5 no longer cites the deleted status
  paragraph; it points at this handoff's section 6, which records the
  owner's rulings.
- **Validation:** `pytest -q` -- **1833 passed**. `pre-commit run --all-files`
  passed (worktree-alignment printed only the expected WT000/WT010 noise).
  `doc_state_sync.py --check` exited 0 with the standing DOC024 warnings
  (L7).

### 2026-09-24 - main is merged in before the root cleanup

Side task, no batch tag: Task 0 of the root-cleanup plan, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope.** A normal merge commit brings `origin/main` (`707eed6`, PR #242)
  into this branch before any file moves, so the Repo Assist workflow and
  its Section 4 entry move with the documents. Arrived cleanly:
  `.github/workflows/repo-assist.md`, `.github/workflows/repo-assist.lock.yml`,
  `.github/aw/actions-lock.json` and `.gitattributes`.
  `.github/copilot-instructions.md` needed nothing: its one line was already
  byte-identical on both sides.
- **Conflicts.** `git merge-tree` named exactly the two files the plan
  predicted, `PLAYBOOK.md` and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. `main` changed only
  Section 4 in both: it added the Repo Assist entry and rotated "The
  release-check finish line names both corrections" into the archive. This
  branch had already rotated that entry, byte-identical, so the archive
  resolves to this branch's side. In Section 4 every entry from both sides
  survives, text unchanged: the Repo Assist entry went in by commit time,
  between "The root-cleanup plan is drafted and the handoff readied for a
  cloud session" and "The architecture diagrams are re-verified against
  source". `--fix` then rotated those last two into the archive, where each
  appears once.
- **Section 3.** Item 3 records the owner's approval ("follow active
  plans", 2026-09-24) and Task 0 done. The plan's own status paragraph still
  reads "awaiting review and owner approval" until Task 1 deletes it, as
  that task specifies. Task 0's plan checkboxes are ticked, and
  `docs/history/reports/HANDOFF_2026-09-24.md` section 5 item 5 now says
  the plan is approved and Task 0 done.
- **Deviations:** Task 0 Step 3 says to append its sentence to item 3. Item
  3's last sentence said the plan awaited approval, so that sentence is
  replaced rather than left to contradict the new one.

Validation: `pytest -q` -- **1833 passed**.

### 2026-09-24 - README and DEVELOPMENT.md catch up with the code

Side task, no batch tag: the owner found `README.md` and `DEVELOPMENT.md`
stale and asked for the wordmark at the top of the README. Not WP-0 work.

- **How.** Two read-only audits, one per file, checked every claim against
  source; the controller verified each finding at source before fixing it.
  The audits were light, so the controller also spot-checked what landed
  since each file's last edit. An independent review approved the result;
  its one wording fix (the `config.py` row claimed "every" tuning value) is
  applied.
- **README.md.** The heading is now the ScrobbleScope lockup, served
  through `<picture>` so GitHub picks the light or dark variant, with the
  proposition as a line below it: design rule 6 (`docs/design/README.md`)
  puts the lockup, not the tagline mark, where the proposition is stated in
  text, and the tagline ("your top albums by year") names only half the app.
  The two variants, `docs/assets/scrobble_scope_lockup_light.svg` and
  `..._dark.svg`, are generated from
  `templates/inline/scrobble_scope_lockup_inline.svg` with the
  `text-strong` and `color-primary` tokens of each theme baked in, since
  GitHub applies none of the site's CSS; each says so in a comment. Also:
  the module table gains `api_logging.py` and `config.py` and `domain.py`'s
  row names the release-window rule; the tuning-variable sentence names the
  concurrency limits and the active-job cap; the DEPLOY.md pointer no longer
  promises a validation checklist that file does not have; and "What shipped
  most recently" adds the identifiable User-Agent and provider-call logging,
  both on `main` since PR #241.
- **DEVELOPMENT.md.** `_LIVE_DOCUMENT_PATHS` (two sites) is
  `LIVE_DOCUMENT_RELATIVE_PATHS` since the rename, and `AGENT_NOTES.md`
  carried the same stale name, fixed too; the worktree guard has six
  modules, not seven; the pre-commit section names the hook's real entry
  point, `scripts/dev/docsync_preflight.py --worktree`.
- **Deviations:** the first cut of the SVGs was invalid XML (a `--` inside
  a comment) and two of the controller's own README claims failed
  verification (that `config.py` holds every environment variable, and
  that no log line carries a name -- `musicbrainz.py`'s retry label does,
  an open handoff item); all three are fixed before this commit. The
  wordmark was checked by rendering both variants as standalone images on
  GitHub's light and dark backgrounds; the frontend gate does not apply (no
  `static/` or `templates/` change).

Validation: `pytest -q` -- **1833 passed**.

### 2026-09-24 - The root-cleanup plan is revised and its open points ruled

Side task, no batch tag: revising the root-cleanup plan, part of Batch 23
WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope.** The plan's eight "Revisions pending" items, plus what a
  source-verified pre-flight found, applied to its task bodies. Nothing in
  the plan has run. Fifth session, the first run of the plan in a cloud
  sandbox.
- **How.** Three read-only research passes at `85f47a0` (production code,
  tests, the inventory's currency including PR #242's files), controller
  probes in scratch copies, then two independent review rounds. Round 1
  found two Critical defects in the revision itself: the proposed pre-commit
  exclude `docs/(?!agents/)` would have un-excluded all of `docs/` (the
  pattern's `/` sits outside the group), and a proposed test assumed the
  `sync_env` corpus passes `--check` (it exits 1, DOC005). Both are fixed;
  round 2 approved, and its three minors are fixed here. A two-axis code
  review (standards, spec) at the owner's request then found no hard
  violation and no missing or wrong item; its one duplicated fact (task
  status copied into the cloud-kit constraints header) is now a pointer.
- **What the plan now carries.** Task 0 merges `origin/main` (conflicts
  only in this file and the log archive, re-verified). Task 3 refuses a
  `--config` naming a missing file, which would otherwise mean "nothing
  declared" and pass. Task 5 repoints the test fixtures that write the
  declarations file (a probe of the draft failed 25 tests) and sweeps its
  live citations by grep, since DOC001 checks backticked `.md` references
  and not `.toml`. Task 6 names the `cli.py` path sites, the tests that
  copy the status line, and the DOC004 contract between
  `SIDE_ARCHIVE_PREFIX` and the log archive's prologue. Task 8 covers
  fourteen `PLAYBOOK.md` and twelve `FINDINGS.md` diagnostic labels. The
  plan's "Revisions applied" section maps every item.
- **Owner rulings, 2026-09-24:** the pre-commit `exclude` becomes
  `docs(?!/agents/)`, so the moved documents stay under the file hooks; the
  `FINDINGS.md` labels join Task 8; generated docsync text names no document
  path instead of hard-coding one; writers may run in parallel on disjoint
  files. `docs/history/reports/HANDOFF_2026-09-24.md` sections 4 and 6
  record them.
- **Also changed.** Section 3's order list records this state (cloud-kit
  R2; Task 1 replaces that text on approval). The handoff gains the
  shallow-clone trap: this session's clone was shallow and 20 commits
  behind, so the guard printed WT005 against `origin/test` until
  `git fetch --unshallow`. `.superpowers/cloud-kit/constraints.md` now
  names both plans and points at SESSION_CONTEXT for the baseline instead
  of copying a count.
- **Deviations:** none. Docs only; no test added or changed.

Validation: `pytest -q` -- **1833 passed**. `pre-commit run --all-files`
and `doc_state_sync.py --check` pass; the frontend gate does not apply (no
`static/`, `templates/` or gate path changed).

### 2026-09-24 - The root-cleanup plan is drafted and the handoff readied for a cloud session

Side task, no batch tag: drafting the root-cleanup plan and revising the
session handoff, part of Batch 23 WP-0 Part B. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- **Owner rulings, 2026-09-24.** The root is cleaned up: `PLAYBOOK.md`,
  `FINDINGS.md`, `AGENT_NOTES.md` and `HANDOFF_PROMPT.md` move to
  `docs/agents/`; `.docsync.toml` and `frontend_gate_checks.toml` move to
  `config/`, each tool with one constant default path, docsync with a
  `--config` override and its document paths declared in its config. Human
  and Impeccable documents stay at the root. It runs after foundation Task
  10 as a new WP-0 Part B task; `origin/main` (PR #242) is merged into this
  branch first; the docsync diagnostics that print `PLAYBOOK.md` are fixed
  in the same plan. `docs/history/reports/HANDOFF_2026-09-24.md` section 6
  holds the full list.
- **What landed.** A read-only research pass listed every place that
  resolves one of the six moving paths, committed as
  `docs/history/reports/ROOT_CLEANUP_INVENTORY_2026-09-24.md` (point-in-time,
  read at `b1b8c0c`). A plan drafted from it,
  `docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`, is
  committed as a draft and marked not approved. A read-only plan review
  found that the draft's Task 7 misreads a merged PR #242, that two DOC002
  label sites and one `renderer.py` citation were unnamed, and that the
  label count was ten, not twelve. Its claim that merging `main` would
  conflict in `AGENTS.md`, `FINDINGS.md` and other files was checked with
  `git merge-tree` and is wrong: only `PLAYBOOK.md` Section 4 and the log
  archive conflict. Every accepted item, and the owner's rulings, are in
  the plan's "Revisions pending" section; nothing in the plan has run.
- **Handoff.** `docs/history/reports/HANDOFF_2026-09-24.md` is revised for a
  cloud session: sections 1, 3, 5, 6 and 8 record Tasks 8-10 done, PR #242
  merged, the root-cleanup rulings, the Repo Assist scope, and three new
  traps (the owner's own changes appearing mid-task, the push permission
  workflow files need, and compiling gh-aw workflows).
- **Deviations:** none. Docs only.

Validation: `pytest -q` -- **1833 passed**.

### 2026-09-24 - Repo Assist runs daily, scoped to tests and dependency proposals

Side task, no batch tag: adding the Repo Assist agentic workflow (gh-aw),
requested by the owner 2026-09-24. It lands on its own branch from `main`
(owner ruling, same day) so Batch 23 WP-0's branch stays clean; a scheduled
workflow runs only from the default branch.

- **What it is.** `.github/workflows/repo-assist.md` is the source and
  `repo-assist.lock.yml` its compiled Actions workflow (gh-aw v0.89.21;
  recompile with `gh aw compile repo-assist` after any edit, since the lock
  records a hash of the source). It came from
  `githubnext/agentics/workflows/repo-assist.md` (pinned by its `source:`
  line). `.github/aw/actions-lock.json` pins the actions the lock uses, and
  `.gitattributes` marks lock files as generated.
- **Scoped to this repository by owner request.** The upstream template runs
  ten tasks. Enabled here: Testing Improvements, pinned-dependency proposals,
  maintaining its own draft PRs, and a monthly activity issue that also lists
  GitHub `finding` issues whose record `FINDINGS.md` has already settled.
  Disabled: issue labelling, triage and fixing (the 43 open issues are the
  unmaintained `FINDINGS.md` mirror, and `FINDINGS.md` wins), coding,
  documentation, performance and "take the repository forward" work, and
  release preparation. Its prompt binds it to `AGENTS.md`: a Section 4 entry
  in the same commit, the gates before any PR, no dependency change without
  the owner's approval, no edits to batch files, `scripts/`, `docs/` or
  `.github/`.
- **Guardrails.** One draft PR per run and none while three are open;
  `allowed-files` limits PRs to tests, the two requirements files and the
  Section 4 documents; a change to a file gh-aw protects (its documented
  list: package manifests, CI configuration, agent instruction files) is
  opened with a review request rather than silently. The repository is public, so `min-integrity: approved`
  lets it act only on content from the owner and collaborators or items
  carrying its own `repo-assist` label. Network: PyPI and GitHub only.
- **Secrets the owner sets** (repository secrets, never committed):
  `CODEX_API_KEY` or `OPENAI_API_KEY` for the codex engine, and
  `GH_AW_CI_TRIGGER_TOKEN`, a fine-grained PAT with Contents read and write,
  so `test.yml` runs on its PRs (GitHub starts no workflow for a push made
  with the built-in token). The workflow file's own comments say the same.
- **Deviations:** the upstream `update-docs` workflow was added and then
  dropped by owner ruling (it would open a documentation PR on every push to
  `main`, against docsync's single-owner rules). `.github/skills/` from
  `gh aw` stays untracked: skill definitions are not tracked here
  (`AGENT_NOTES.md`). The prompt keeps the template's emoji disclosure lines
  as the template wrote them; they only shape generated GitHub content, not
  repository documents.

Validation: `pytest -q` -- **1821 passed**; no test or application change.

**Follow-up (2026-09-24).** The owner added one line to the top of
`.github/copilot-instructions.md` and asked for it to be tracked with this
change: GitHub's coding agents are to follow `AGENTS.md` and its bootstrap,
not duplicate its rules, and use the existing Graphify guidance for
architecture questions. Its one curly apostrophe became a straight one
(`AGENTS.md` Markdown Authoring Rules: ASCII only); the file's older
non-ASCII characters, in its Mermaid section, are untouched.
Validation: `pytest -q` -- **1821 passed**; docs only.

**Review fix round (2026-09-24).** A `/code-review` of this PR found four
defects the workflow inherited from the upstream template; each was checked
against the gh-aw docs and the compiled lock before fixing. (1) The prompt
never gave `notes.json`'s exact shape, which the memory validation script
enforces key by key, so a guessed file would be rejected: the prompt now
gives the initial document and every entry's keys. (2) The validator failed
on a missing `notes.json`, so a correct do-nothing run on a fresh memory
branch would fail: a missing file is now valid. (3) Task 11 closes last
month's activity issue, but `update-issue` allowed only the body: it now
also allows the status. (4) The open-PR cap searched titles for
`"[repo-assist]"`, which GitHub's search reads as plain words, so it also
counted human PRs mentioning "repo assist": it now matches the literal
title prefix, as the task-weighting step already did. Recompiled with
`gh aw compile repo-assist --approve`, the approval covering the reviewed
validation-script change.
Validation: `pytest -q` -- **1821 passed**; no test or application change.

### 2026-09-24 - The architecture diagrams are re-verified against source

Side task, no batch tag: walking every `docs/architecture/*.md` diagram
against current source, part of Batch 23 WP-0 Part B. Untagged by owner
ruling 2026-09-23 until the whole of WP-0 lands.

- **Step 1:** `runtime-system.md` gained `api_logging.py` as a runtime node
  (`Utils --> ApiLogging`), a sixth "Five things" bullet on the shared
  `aiohttp.TraceConfig` trace hook and per-provider call summary (F-B23-6,
  `433120c`/`e7e076b`/`5bfb997`), and its `config.py` importer count
  corrected from ten to eleven: `routes/__init__.py`'s module-level
  `MAX_ACTIVE_JOBS` import (landed at `e552956`, before this diagram's own
  last edit, and missed until now) joins the list, and `app.py` is renamed
  the twelfth (deferred-only) importer.
- **Step 2:** `top-albums-sequence.md`, `heatmap-sequence.md`,
  `development-cycle.md` and `documentation-tooling.md` needed no change.
  Walked against `de8c2d8` (`domain.release_window`), `4cbb9b1` (release
  checks run without the cache, guarded per use rather than skipped),
  `e552956` (the capacity message), `82557fd` (the UTC year gate), the
  logging commits above, the `_frontend_gate_*` slice split, `a25d187`
  (the check manifest), `a87e6058` (ruff BLE gate on broad catches),
  `c611f721` (`_validate_api_keys` in `create_app`) and `bd7ffef0` (the
  `.githooks/` CRLF rule) -- each fact these four files already state
  still matches current source.
- **Step 3:** `docs/ARCHITECTURE.md`'s "Last verified" date moved from
  2026-09-20 to 2026-09-24, after every file above was walked.

No test changes; no count site changes (R3).

Validation: `pytest -q` -- **1833 passed**.

### 2026-09-24 - AGENTS.md points at the full docsync CLI and records the installer decision

Side task, no batch tag: `AGENTS.md` pointers and the installer decision,
part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **Step 1:** `AGENTS.md` "Doc Sync Rules" -> "How to run" now points at
  `docs/architecture/documentation-tooling.md` "CLI surface added by the
  close-out and bounded-archives plan" for `--close-batch`,
  `--paginate-archives` and `--cold-storage`, without restating the modes.
- **Step 2:** `AGENTS.md` "Agent skills" gained a "Global rules" pointer to
  `docs/agents/global-rules.md`, in the same shape as its three siblings.
- **Step 3:** `AGENT_NOTES.md` "Architectural Constraints" records the
  installer decision: no live `--install --yes` has run in this repository,
  and either install order fails loudly rather than silently. Wrapper
  first, then `pre-commit install`, moves the wrapper to `pre-commit.legacy`
  and re-enters it through `hook_impl.py`'s `_run_legacy`; the wrapper's own
  non-recursive delegation to `python -m pre_commit hook-impl` then
  inherits `PRE_COMMIT_RUNNING_LEGACY` and hits pre-commit's own "installed
  in migration mode" `SystemExit` on every future commit -- confirmed
  against `install_uninstall.py` and `hook_impl.py` in the installed
  `pre_commit` package, matching the plan's "Errors in the earlier draft".
  `pre-commit install` first, then the wrapper, fails the other way:
  pre-commit's own generated hook file carries no `GENERATED_MARKER`, so
  `install_docsync_hook.py`'s `classify_existing_hook` reads it as
  `"unknown"` and `install()` refuses to overwrite it (exit 2). The wired
  path already runs the checker without the wrapper: `doc-state-sync-check`
  is first in `.pre-commit-config.yaml`, and CI's own explicit preflight
  step backs it up.
- **Step 4:** `AGENTS.md` measures **487** lines (`wc -l AGENTS.md`),
  under the 500-line limit.

No test changes; no count site changes (R3).

Validation: `pytest -q` -- **1833 passed**.

**Follow-up (2026-09-24, owner change).** The owner added one line to the
top of `.github/copilot-instructions.md` and asked for it to be committed:
GitHub's coding agents are to follow `AGENTS.md` and its bootstrap, not
duplicate its rules, and use the existing Graphify guidance for
architecture questions. It is the agent-facing counterpart of this entry's
pointers. The same line, with its curly apostrophe straightened (`AGENTS.md`
Markdown Authoring Rules: ASCII only), is also on PR #242
(`chore/repo-assist-workflow`); the two copies are byte-identical, so the
branches merge cleanly. Docs only.

### 2026-09-24 - The frontend gate selects checks from a manifest

Side task, no batch tag: adding `frontend_gate_checks.toml` so the frontend
gate selects which checks run by name, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Steps 1-2: manifest and selection.** `frontend_gate_checks.toml` (root)
  declares `required` (the four load-bearing checks) and `disabled` (empty
  today). `scripts/dev/frontend_gate.py` loads it with `tomllib` at import,
  validates every named check against `CHECKS`, and refuses -- with a clean
  `[frontend_gate] ERROR:` line, before `main` ever runs -- an unknown name
  or a required check disabled. Selection is by name only: `CHECKS` stays
  the full registry, so the three existing tests in
  `tests/scripts/dev/test_frontend_gate.py` that patch it directly are
  unmodified. `run_checks` and `PLANNED_RUNS` filter by the disabled-name
  set, and the startup line states the enabled count and names every
  disabled check. New test module
  `tests/scripts/dev/test_frontend_gate_manifest.py` (8 tests).
- **Deviation from the brief:** Step 1 says disabling `divider contrast`
  lowers the planned run count by one; measured, it drops by **two** -- the
  check runs on one profile (DESKTOP) but belongs to the `STATIC_ASSETS`
  group, which Firefox also runs as its canary. The test asserts the drop
  is 2, with a comment saying why.
- **Step 3: live probe**, throwaway corpus at `/c/ssprobe` (`git ls-files`
  plus the two new files, since the change is uncommitted), deleted after.

  | probe | expected | exit | evidence |
  |---|---|---|---|
  | faithful copy | same selection as the worktree | 0 | `30 of 30 checks selected; disabled: none`, `PLANNED_RUNS 52` |
  | red: required check disabled | refused before a browser launches | 1 | `[frontend_gate] ERROR: check manifest ... disables required check(s) stylesheet isolation ...`; no launch line in the output |
  | red: unknown name (typo) | refused, not ignored | 1 | `[frontend_gate] ERROR: check manifest ... names 'divider kontrast', which is not a check in CHECKS ...`; no launch line in the output |
  | near-miss green | committed manifest, `disabled = []` | 0 | the worktree's own `frontend` gate run below |

- **Step 4:** `documentation-tooling.md` records the manifest as landed and
  states the decomposition's goal was isolating what executes, not
  shrinking `_frontend_gate_layout.py`.

`frontend` gate run locally (this task changes the gate itself, so its
near-miss green is that run; section 2b's path-prefix `when` condition does
not match `frontend_gate.py`, so it is not implied by other changed paths):
`30 checks passed in 52 runs across chromium, firefox (static assets &
tokens canary on firefox); profiles: desktop, mobile, wide touch`.

Validation: `pytest -q` -- **1833 passed**.

**Fix round 1 (2026-09-24, review finding).** `DEVELOPMENT.md` still stated
the exact fact Step 4 reversed: "the `frontend_gate_checks.toml` registry
stays a deferred candidate" (line 539), next to a stale facade line count
("535 lines", line 532; actual 619 at `a25d187`) -- a live architecture
document, not a dated log, so it is not point-in-time and it directly
contradicted the sentence this same commit wrote into
`documentation-tooling.md`. Fixed: `DEVELOPMENT.md` now says the manifest
landed too, in the same words `documentation-tooling.md` uses, and states
the facade's size only as "under the decomposition plan's 700-line
threshold" rather than restating an exact count -- a second copy of a
number is exactly what went stale here. A second copy of the same stale
count turned up on re-sweep: this Section 3's own "Side task complete: the
frontend gate split (F-B21-51)" bullet also said "measures 535 lines";
fixed the same way. Re-swept the whole tree for both claims, every spelling
(`git grep -n "deferred candidate"`, `git grep -n "535 lines"`,
`git grep -n "frontend_gate_checks.toml"`): every remaining hit is inside a
dated log entry, an archived finding, or the decomposition plan's own dated
worked example -- point-in-time and exempted, consistent with the review's
own sweep.

Validation: `pytest -q` -- **1833 passed**; no test added, docs only.

### 2026-09-24 - The docsync close-out plan's Progress block is closed

Side task, no batch tag: closing the docsync close-out plan's Progress
block, part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23
until the whole of WP-0 lands.

- **Progress block closed.** Task 4 (`491e61a4` code, `3d8a42a5` docs) and
  the final whole-branch review (engine reviewed alone as `a07f5761`; DOC023
  built as `fa923305`/`28a8527`/`fcfe8d4e`) are ticked, both reaching `test`
  through PR #233 (`2ccf0ddb`) and PR #234 (`88f6e27`). New deviation
  bullets record the review split, DOC023's id-allowlist departure, and
  where the ledger's untriaged Minors went.
- **Owner ruling 2026-09-24 widened this task**: the docsync close-out
  ledger's final review never worked its own carried-over triage list of
  "minor (deferred)" items from Tasks 1, 2, 3 and 4a. Checked individually
  against the code and tests at HEAD: two were already fixed (the
  `run_docsync_check` uncaught `OSError`, and `CONTROL_PLANE_FILES`'
  exact-vs-prefix filename matching -- both folded into `491e61a4`'s fix
  round); three from Task 1 are too terse in the record to check and are
  marked not reproducible; the remaining eleven are still true and filed as
  one finding, F-DOCSYNC-20 (foundation plan DoD row 32).

Validation: `pytest -q` -- **1825 passed**.

**Follow-up (2026-09-24).** The owner ruled one of F-DOCSYNC-20's eleven
items intended behaviour: `--cold-storage` may repaginate a never-paginated
monolith. The item is dropped from the finding, which says why, and ten
remain; the finding stays open at P2. `docs/history/reports/HANDOFF_2026-09-24.md`
had not caught up with this task: sections 1, 3 and 5 now record Task 7 done
and Tasks 8-10 next, section 6 carries both 2026-09-24 rulings, and its Task
11 line no longer cites an untracked workspace file.
Validation: `pytest -q` -- **1825 passed**; docs only.

### 2026-09-24 - Findings hygiene repoints pre-split citations and files four defects

Side task, no batch tag: findings hygiene, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Step 1: pre-split citations repointed by name.** `FINDINGS.md`'s
  F-SWE-3 and `docs/history/findings/FINDINGS_ARCHIVE.md`'s F-B21-6,
  F-SWE-5 (two citations) and F-SWE-2 (context.md's "second `:70-71`
  citation") each named their `orchestrator.py:NNN` line by the function
  it pointed at (`_run_spotify_search_phase`, `fetch_top_albums_async`,
  `background_task`'s outer handler, `_fetch_and_process`'s inner
  handler), confirmed by reading `scrobblescope/orchestrator.py` at the
  commit nearest each finding's date (`bb8681b` for the three 2026-08-20
  SWE-audit findings, `319134e` for F-B21-6, filed 2026-08-22), and naming
  the module both as it was (`orchestrator.py`) and as it is now
  (`scrobblescope/orchestrator/__init__.py` or `_search.py`). No resolved
  record's account of what was wrong or how it closed changed, only its
  citation.
- **The broader `git grep -n "orchestrator\.py:\|routes\.py:"` over the
  live corpus** found 100 hits in 14 files beyond the findings files. Left
  as written, point-in-time: five files under `docs/history/reports/` and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (named exemptions);
  `docs/history/definitions/BATCH21_DEFINITION.md` (same archive tier as
  `logs/` and `reports/` per `AGENTS.md`'s `docs/history/` table row); and
  five `docs/superpowers/plans/*.md` files, including this plan's own
  Task 6 text, which quotes the citations as the problem statement rather
  than reporting current code. `.codacy.yml`, `docs/SWE_AUDIT_CHARTER.md`
  and `scripts/dev/_frontend_gate_shared.py` were checked and carry none
  of these citations under this grep's pattern; their stale `routes.py`
  citations (a different spelling) stay deferred to WP-0 close-out,
  unedited, per context.md.
- **Step 2: four findings filed**, IDs taken as the next free number per
  tag across both files. `F-DOCSYNC-17` (opening-state defect, resolved
  `aad26e5`, foundation Task 3) and `F-DOCSYNC-18` (archive page target
  had no reader and the cold rule's all-dated condition was undocumented,
  resolved `d499e3a`, foundation Task 4) filed resolved in `FINDINGS.md`'s
  "Resolved this batch" section, each with its `**Completed:**` line.
  `F-DOCSYNC-19` (`--check` has no diagnostic for an interrupted
  publication; DoD row 29) and `F-WORKTREE-6` (the worktree guard's
  `--base-ref` defaults to `origin/main` rather than a fact PLAYBOOK
  declares, sharper since PR #241: WT006 then WT005 against `origin/main`
  with an empty merge-base diff, `docs/history/reports/HANDOFF_2026-09-24.md`
  section 2) filed open (P2) under P2 -- Scaling roadmap. Checked
  F-WORKTREE-6 against F-WORKTREE-3 first: its three open items (the
  between-batch ancestry skip, WT010 missing on a dirty detached worktree,
  the doubled base-ref label) are a different defect, so this is a
  separate finding.
- **Owner ruling, 2026-09-24 (mid-task):** the foundation plan's Task 11
  (F-SWE-5) is recorded done, not left unticked -- F-SWE-5 was resolved by
  the reconcile plan's Task 7 (`ffbee0e`) before this plan reached Task 11.
  Task 11's five step boxes are ticked and a done-by-reference line added
  under its heading; nothing else in Task 11 changed. This supersedes
  context.md's original "do NOT edit Task 11" note.
- **Step 3.** `doc_state_sync.py --fix` then `--check`, both at exit 0.
- **Deviations:** none from the brief's Step 1/2 text; the point-in-time
  scope for `docs/history/definitions/` and `docs/superpowers/plans/` is
  this task's own reading of context.md's "list any hit you leave, with
  the reason" allowance, not an enumerated exemption -- reasons are above.
- Validation: `pytest -q` -- **1825 passed**. No test added; the three R3
  count sites are unchanged.
- **Next:** the foundation plan's Task 7.

**Follow-up (2026-09-24).** `docs/history/reports/HANDOFF_2026-09-24.md` had
not caught up with this task: its Section 1 WP-0 status bullet still read
"Tasks 4 and 5 done; Tasks 6-10 remain," Section 5 item 2 still described
Task 6 as upcoming work with a pre-flight instruction, Section 3's reading
order still pointed a cold session at "Task 6 onward," and Section 6 named
no ruling for Task 11. All four now record Task 6 done (Section 5 item 2
points at this entry), Section 3 points at Task 7 onward, and Section 6
carries the Task 11 (F-SWE-5) done-by-`ffbee0e` ruling beside the other
2026-09-24 rulings. Validation: `pytest -q` -- **1825 passed**; no test
changes, so the three R3 count sites are unaffected.

**Correction (2026-09-24).** The task review reproduced the broader sweep
above as 95-98 hits in 12 files, not 100 in 14; the categorization of what
was left as point-in-time is unchanged.

### 2026-09-24 - The provider summary states its span and its time in calls

Side task, no batch tag: the provider summary log line states its span
alongside its time in calls, part of Batch 23 WP-0 Part C. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands. It follows up
F-B23-6's provider-call logging (Task 13); ruled by the owner 2026-09-24,
source `docs/history/reports/HANDOFF_2026-09-24.md` section 5 item 1.

- **Scope.** `scrobblescope/api_logging.py`'s per-session summary read
  `MusicBrainz: 17 calls in 2.6s -- 16x200, 1x503`; the `2.6s` is the sum of
  per-call durations, not how long the provider was being called. Read
  naively it says MusicBrainz ran faster than its 1 request per second,
  which the owner did. MusicBrainz is compliant: the global throttle in
  `scrobblescope/utils.py` spaces request starts one second apart, and the
  owner's log timestamps confirm it. The line now states both:
  `MusicBrainz: 17 calls over 12.1s (2.6s in calls) -- 16x200, 1x503`.
  `_record` gains the earliest call start and latest call end seen per
  provider (`span_start`, `span_end`); `_on_request_end` and
  `_on_request_exception` each read `time.monotonic()` once per end event
  and pass that one reading to both the per-call line and the tally, so the
  per-call milliseconds and the summary's figures never drift apart. Counts
  and outcomes are unchanged; the line still never carries a query string,
  a name, a body or a header.
- **Two existing tests changed** (`tests/services/test_api_logging.py`):
  `test_closing_the_session_logs_one_summary_per_provider`'s
  `message.startswith(...)` assertion moved from `"127.0.0.1: 3 calls in"`
  to `"127.0.0.1: 3 calls over"`, plus a new regex asserting the full shape
  (span, in-calls, outcomes); `test_a_session_that_made_no_calls_logs_no_summary`'s
  filter string moved from `"calls in"` to `"calls over"`, since every
  summary line now carries the new wording and the old filter would have
  passed vacuously.
- **New tests:** span is not the sum of per-call durations (the owner's
  case, driven deterministically through `_record`/`_emit_summaries` against
  a stand-in session object); overlapping calls make time-in-calls exceed
  the span; an exception ending after the last success extends the span and
  is counted under its class name; and one end-to-end test against the real
  session and trace hook, asserting only a lower bound on the span (no
  upper bound -- timing-based upper bounds flake).
- **Deviations:** none.
- Validation: `pytest -q` -- **1825 passed**.
- **Next:** the foundation plan's Task 6.

**Fix round 1 (2026-09-24, review finding).** The review's one Important
issue: `docs/history/reports/HANDOFF_2026-09-24.md` section 2's setup
block still read `# expect 1821 passed`, a second copy of the test count
inside the very file this task's commit had already updated, contradicting
section 1's `**1825 passed**` two screens above it. Fixed by removing the
second copy rather than restating it: the comment now reads `# expect the
count section 1 records`, so there is exactly one number in the file to
keep current. Grepped the whole file again for `1821`/`1825`: the only
remaining hit is section 1's own count. No test changes; no other count
site affected.

- Validation: `pytest -q` -- **1825 passed**.

### 2026-09-24 - The handoff schedules a truer provider summary line

Side task, no batch tag: a handoff revision, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Why.** The owner read `MusicBrainz: 17 calls in 2.6s` as MusicBrainz
  running faster than its 1 request per second. The calls were compliant:
  their log timestamps are one second apart, as the global throttle in
  `scrobblescope/utils.py` enforces. The summary's time is the sum of
  per-call durations, not the session's span.
- **Change.** `docs/history/reports/HANDOFF_2026-09-24.md` section 5 now
  opens with a side task, ruled by the owner on 2026-09-24 to run before
  foundation Task 6: the summary states both the span and the time in calls.
  Section 7 withdraws the per-album Spotify item (the owner's log lines came
  from `/api/artist_spotlight` and the token fetch, not the album fetch). It
  also notes that `scrobblescope/musicbrainz.py` puts album and artist names
  in its retry log label, for the WP-3/WP-4 Data handling check.
- **Section 3** names the side task as next, before Task 6.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-24 - The cloud handoff is revised after the first cloud session

Side task, no batch tag: revise the session handoff at the end of the first
cloud session, part of Batch 23 WP-0 Part B. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- **Scope.** Documentation only. `docs/history/reports/HANDOFF_2026-09-24.md`
  is revised in place rather than superseded by a second file with the same
  date, so Section 3, the cloud kit and this log keep one entry point.
  `.superpowers/cloud-kit/constraints.md` gains Lessons L11-L13 and a header
  that names Tasks 6-10. Section 3's handoff bullet says the file was
  revised.
- **What the handoff now records.** Foundation Task 5 is done (`9ea79f5`,
  `aa6a867`, `e913f89`, `4ae0dc3`, three review rounds, the last approved
  with no findings). PR #241 merged into `main` as `92f7d6a`, and no PR is
  open for the branch. Three cloud-sandbox limits: the Tailwind artifacts
  must be fetched with `curl` (Python 3.13 rejects the proxy CA), the
  frontend gate cannot run, and Codacy's API is blocked. The guard fails
  against `origin/main` since the merge (WT006 while the branch has nothing
  past it, WT005 once it does) with an empty merge-base diff, so it runs
  with `--base-ref origin/test`. The owner's Task 5 rulings and the
  push rule (hold until a review is recorded clean).
- **Lessons.** L11: check a task's plan checkboxes before recording it done;
  the owner caught Task 5's. L12: ask the first review to sweep the whole
  task range for stale copies of every changed fact; Task 5 needed three
  rounds without it. L13: every code a gate-runner summary quotes must be
  found in its logs.
- **Deviations.** None. No code or test changed. The first commit said the
  guard reads WT006 against `origin/main`; its own pre-commit run printed
  WT005, because the branch had moved past the merge. Both statements now
  name both codes.
- **Validation:** `pytest -q` -- **1821 passed**. `pre-commit run --all-files`
  and `doc_state_sync.py --check` pass, with the expected WT005, DOC024 and
  root-BATCH warnings.
- **Next.** Foundation Task 6, findings hygiene, from the handoff's section 5.

### 2026-09-24 - Stop stating a DOC code range the catalogue owns

Side task, no batch tag: replace every live prose statement of a `DOC001-DOC0NN`
range with wording that states no range, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 5.** Six live sites stated a stale
  contiguous range (`AGENTS.md` x3, `DEVELOPMENT.md`, and
  `docs/architecture/documentation-tooling.md` x2, one of them the heading).
  Both `DOC001-DOC023` and `DOC001-DOC024` are false today: DOC021 and DOC022
  are reserved by
  `docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
  but not raised, so no contiguous span from `DOC001` is true. Each site now
  says "the DOC diagnostic catalogue" (owner: `documentation-tooling.md`)
  instead of restating a range; the catalogue's own heading is renamed
  "The DOC code catalogue" and its one explicit list reads "`DOC001`-`DOC020`,
  `DOC023` and `DOC024` issues". `FINDINGS.md`'s F-B21-61 note ("a new
  invariant for this finding starts at DOC023") is repointed at the catalogue,
  since DOC023 is itself now taken (the finding-lifecycle grandfathered-finding
  count, `scripts/docsync/findings.py`).
- **Tests repointed, controller ruling 2026-09-24 (the one sanctioned
  existing-test edit).** `tests/test_docsync_integrity.py::
  test_stated_docsync_range_matches_the_highest_code_raised` and
  `test_stated_range_helper_rejects_a_stale_range` read `AGENTS.md`'s stated
  range, which no longer exists. Both are renamed
  (`test_stated_docsync_catalogue_matches_the_codes_raised`,
  `test_stated_catalogue_helper_rejects_a_mismatched_list`) and repointed at
  `documentation-tooling.md`'s explicit list; their helpers become
  `CATALOGUE_SENTENCE_RE`, `_stated_codes`, `_raised_codes` and
  `_catalogue_matches_raised_codes`. The comparison is now set equality
  (parsing "DOC0AA-DOC0BB" spans and single codes) rather than a maximum, so
  a listed-but-unraised code (DOC021) is caught, which comparing only the
  upper bound could not catch. The proof test mutates the real catalogue
  sentence in place (drop DOC024; add DOC021) rather than a synthetic
  fixture, so it exercises the same parsing the corpus test relies on.
- **`.docsync.toml`** gains a fourth `[[retired]]` declaration, modelled on
  its "the docsync integrity range ends at DOC011" sibling: it matches the
  bare literal `DOC001-DOC023` or `DOC001-DOC024`, either spelling
  (contiguous or backtick-split), needs no verb-prefix guard because the
  valid list never contains either substring, and leaves `DOC001-DOC020`
  alone.
- **Discovered and filed as F-DOCSYNC-16.** The three pre-existing
  `[[retired]]` declarations' `allow_after` marker for `PLAYBOOK.md` was the
  literal string `"## 4. Execution log"`, but `check_retired` compares a raw
  line by exact equality and the real heading is `"## 4. Execution log (for
  agent handoff)"` -- confirmed by reproducing the mismatch directly against
  `check_retired`. Their Section 4 exemption was therefore non-functional
  against the live document, latent only because no dated entry restated one
  of their three retired phrases. This task's own new declaration used the
  full, correct heading text from the start so it was not affected.
- **Live probe** (`/tmp/ssprobe`, `git archive` of `git stash create`,
  deleted after):

  | probe | expected | got |
  | --- | --- | --- |
  | faithful copy `--check` | same summary as the worktree | match, exit 0 |
  | red: add "the DOC001-DOC023 catalogue" to `AGENTS.md` | DOC011, exit 1 | DOC011, exit 1 |
  | red: add `` returns typed `DOC001`-`DOC024` issues `` to `DEVELOPMENT.md` | DOC011, exit 1 | DOC011, exit 1 |
  | near-miss: same text struck through in `AGENTS.md` | silent, exit 0 | silent, exit 0 |
  | near-miss: same text in a dated Section 4 entry below the marker | silent, exit 0 | silent, exit 0 |
  | near-miss: "DOC001-DOC020" in `AGENTS.md` prose | silent, exit 0 | silent, exit 0 |
  | mutate `documentation-tooling.md`'s list to drop DOC024 | corpus test red | red |
  | mutate `documentation-tooling.md`'s list to add DOC021 | corpus test red | red |

- Validation: `pytest -q` -- **1821 passed**. No test added or removed, so
  the three R3 count sites are unchanged.

**Fix round (2026-09-24, review finding).** The review's one Important
issue: the three pre-existing `allow_after` markers were left broken
next to the fourth, freshly-corrected one in the same commit and same
file, instead of being corrected outright (Anti-Pattern 11). Owner ruling:
correct all three in `.docsync.toml` (touching nothing else in those
declarations); reword F-DOCSYNC-16 to name the mechanism gap -- docsync
silently ignores an `allow_after` marker that matches no line, rather than
erroring -- and record that the three markers are corrected in this fix
commit; drop its priority to P2 (the fix shape becomes a future check that
errors on a dead marker, not built here); status stays open.

- **`.docsync.toml`:** all three `[retired.allow_after] "PLAYBOOK.md" =
  "## 4. Execution log"` lines corrected to `"## 4. Execution log (for
  agent handoff)"`, the real heading, matching the fourth declaration this
  task already added. Nothing else in the three declarations changed.
- **`FINDINGS.md`:** F-DOCSYNC-16 retitled "docsync silently ignores an
  `allow_after` marker that matches no line," its body names the general
  mechanism gap ahead of the specific instance, records that the three
  markers are now corrected, keeps the reproduction evidence, and states
  the not-yet-built fix shape (a declaration check erroring on a dead
  marker). Priority dropped P1 -> P2; status line unchanged (`open`).
- **Live probe, reproduced in a fresh `/tmp/ssprobe`** (`git archive
  9ea79f5`, `git init`, deleted after): a dated Section 4 entry quoting
  "limit_results goes inside the thresholds disclosure" gives `ERROR
  DOC011`, exit 1, with the unfixed markers; correcting all three markers on
  that same scratch tree makes it silent, exit 0; and `--check` on the
  unmodified corpus (no injected quote) is byte-identical before and after
  the marker fix -- same four DOC024 + root-BATCH warnings, exit 0.

  | probe | expected | got |
  | --- | --- | --- |
  | unfixed markers, dated entry quoting the retired `limit_results` phrase | DOC011, exit 1 | DOC011, exit 1 |
  | corrected markers, same quote | silent, exit 0 | silent, exit 0 |
  | corrected markers, unmodified corpus vs. before | identical `--check` output | identical |

- Validation: `pytest -q` -- **1821 passed** (unchanged; no test touched
  in the fix round).

**Fix round 2 (2026-09-24, re-review + owner catch).** Two Important issues
and one owner catch, all in the same commit (`aa6a867` -> next): the
`.docsync.toml` comment above the fourth declaration's `allow_after` still
described the three siblings' pre-fix state in the present tense, false as
of `aa6a867` -- rewritten to state only what is true now (the exemption
needs the real heading text; F-DOCSYNC-16 records the silent-ignore
mechanism), with no other live present-tense claim found by corpus grep.
F-DOCSYNC-16 carried its new P2 priority but was still filed under the
`## P1 -- Next batch candidates` heading -- moved, unchanged, to the top of
`## P2 -- Scaling roadmap`. Owner catch: this task's own Step 1-6 checkboxes
in the foundation plan were never ticked in the first commit -- ticked now,
nothing else in the plan changed.

- Validation: `pytest -q` -- **1821 passed** (unchanged; no test touched).

**Fix round 3 (2026-09-24, re-review).** `DEVELOPMENT.md:559`'s portability
ties table still quoted the pre-fix `allow_after` marker literal as a
worked example; corrected to the real heading text, the only change in
that row.

### 2026-09-24 - The loading page looks up its error source label in a Map

Side task, no batch tag: close Codacy's object-injection flag on the loading
page's error source label, part of Batch 23 WP-0 Part C. Untagged by owner
ruling 2026-09-23 until the whole of WP-0 lands.

- **Why.** Codacy's check failed on PR #241 with one high issue, "Variable
  Assigned to Object Injection Sink", at `static/js/loading.js`'s
  `const label = ERROR_SOURCE_LABELS[source];`. It is not exploitable: the
  server sends only `lastfm`, `spotify` or `internal`
  (`scrobblescope/errors.py`), and the label goes into `textContent`. But an
  object-literal lookup resolves inherited keys, so a source of
  `constructor` would have printed `Source: function Object() ...`.
- **Change.** `ERROR_SOURCE_LABELS` is a `Map`, read with `.get(source)`.
  An unknown or inherited key finds nothing, so the source line stays
  hidden. The failure call that passes no source is unchanged:
  `Map.get(undefined)` is `undefined`, as the object lookup was. The JSDoc
  says why it is a Map. Nothing else changed; the reconcile plan's Task 7
  code block keeps the object form it shipped with, as a record.
- **Found by** the cloud session, which could not run the frontend gate
  (no Playwright browsers in its sandbox), so the change was made locally.
- **Also corrected:** the heading of the cloud-handoff entry below carried
  a `WP-<digit>` token, against the untagged-entry rule; it now reads
  without one.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. The frontend
  gate ran, since `static/` changed.

### 2026-09-24 - The Batch 23 foundation work gets a handoff a cloud session can run from

Side task, no batch tag: session handoff for Batch 23 WP-0, which moves to a
cloud session. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Why.** The owner is moving the work to a cloud session, which has only
  the repository. The local sessions kept their working state outside Git:
  the SDD ledgers and workspace constraints (`.superpowers/sdd/`, ignored),
  the four agent definitions (user-level, `~/.claude/agents/`), and the
  owner's working agreements (session memory). The gate commands were also
  Windows paths.
- **Added.** `docs/history/reports/HANDOFF_2026-09-24.md`, the new entry
  point: state, Linux setup, how the subagent loop runs without the plugin
  scripts, next steps with Task 5's owner ruling, rulings in force, open
  items and traps. `.superpowers/cloud-kit/constraints.md` is the Linux form
  of the workspace constraints (gates on `.venv/bin`, Lessons L1-L10).
  `.superpowers/cloud-kit/agents/` holds the four agent definitions,
  copied unchanged. `.superpowers/sdd/.gitignore` is now tracked, so a
  fresh clone keeps new SDD workspaces out of Git.
- **Not added.** The root `CLAUDE.md` stays git-ignored, as `.gitignore`
  records; the cloud session's first prompt names the handoff instead. The
  SDD helper scripts stay out too (vendored skills are local harness state
  per `.gitignore`); the handoff gives their plain `git` and `awk` forms.
- **Section 3** points its handoff bullet at the new file.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-24 - The owner's live check closes the logging task

Side task, no batch tag: a Section 3 correction, part of Batch 23 WP-0 Part
C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **What.** The reconcile plan's Task 13 (F-B23-6) landed as `433120c` and
  its fix round as `e7e076b`. Its Step 5, the owner's live check against
  the real providers, was left to the owner. The owner ran a job with
  `DEBUG_MODE=1` on 2026-09-24 and confirmed the log: per-call DEBUG lines
  such as `MusicBrainz GET /ws/2/release-group/ -> 200 in 133ms` and
  `Spotify GET /v1/search -> 200 in 241ms`, INFO summaries, and no query
  value. Section 3 and the plan's Step 5 now record it done.
- **Observation for a later task.** The owner's log shows one
  `Spotify: 1 calls` INFO summary per Spotify search, each from its own
  runner thread. So that path builds one session per call, and the
  per-session summary becomes one INFO line per album rather than one per
  job. It may also mean connections are not reused there. Not fixed here.
- **Fix-round note.** The fix-round implementer for `e7e076b` stopped at a
  rate limit after its edits and before its gates. The controller read the
  diff, ran `--fix`, the suite, pre-commit and `--check`, repeated the
  scratch-copy mutation proof, and committed. That fix round has no
  independent re-review yet.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-24 - The release-check finish line names both corrections

Side task, no batch tag: fix round 1 on Task 13 (F-B23-6), part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **What the review caught.** `run_release_checks`'s finish line (the entry
  below, from `433120c`) logged `state["moved_out"]` alone as "corrected".
  That hid `state["moved_in"]` -- an excluded album whose original release
  MusicBrainz found to fall back inside the window, just as real a finding
  as a moved-out result, and the whole reason this task exists is so the
  owner can see what MusicBrainz found.
- **Fix.** `scrobblescope/release_checks.py`'s finish line now names both
  counts: `"{checked} checked, {moved_out} moved out, {moved_in} moved in"`.
  No artist or album names, as before.
- **Test.** `tests/services/test_release_checks.py`'s finish-line test
  (its own new test from `433120c`, so changing it is in scope) is renamed
  `test_run_release_checks_logs_its_finish_with_moved_out_and_moved_in_counts`
  and now drives a job with two results that move out and one exclusion
  that moves in, asserting `2 moved out` and `1 moved in` -- distinct,
  non-zero counts, so a swap of the two would fail the test.
- **New test: a logging failure never fails a request.**
  `tests/services/test_api_logging.py` gains
  `test_a_recording_failure_never_fails_the_request`: with `_record`
  monkeypatched to raise, a real request through `create_optimized_session()`
  against a local `TestServer` still returns its response normally, and an
  explicit `close()` afterwards still does not raise. Proved to actually
  exercise the callbacks' `try/except` (not just the happy path): archived
  `HEAD` to a scratch directory outside the repo
  (`git archive HEAD | tar -x`), removed the `try/except` from
  `_on_request_start`/`_on_request_end`/`_on_request_exception` there, and
  reran the same test against that mutated copy with `PYTHONPATH` pointed
  at it -- it failed (`RuntimeError: boom` reaching the caller through
  `session.get(...)`). Scratch directory deleted afterward; nothing in the
  repository was touched by the mutation.
- **Sibling text.** The `433120c` dated entry below keeps its "Reading
  `corrected`" bullet as a record of what that commit actually shipped; this
  entry states the change instead. The reconcile plan's Task 13 spec text
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`)
  updated its "checked and corrected" line to name both counts. The
  resolved F-B23-6 record's reason line ("start, finish and skip") never
  claimed "corrected" and needed no change.

Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-24 - Every provider call is logged, and the release worker says what it did

Side task, no batch tag: implements the reconcile plan's Task 13 (F-B23-6),
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **New module `scrobblescope/api_logging.py`** (leaf: standard library plus
  `aiohttp`): a host-to-provider map (`ws.audioscrobbler.com` -> Last.fm,
  `api.spotify.com`/`accounts.spotify.com` -> Spotify, `api.deezer.com` ->
  Deezer, `musicbrainz.org` -> MusicBrainz; any other host is named by its
  hostname), the `aiohttp.TraceConfig` callbacks that log every call, and a
  per-session tally that logs one INFO summary per called provider on
  close (for example `Spotify: 3 calls in 0.2s -- 2x200, 1x404`). Levels
  per the owner's ruling: 429/5xx at WARNING (naming `Retry-After` when the
  response has one), other non-2xx at INFO, a timeout or connection error
  at WARNING (naming the exception class), 2xx at DEBUG. A line never
  carries the query string -- only the path -- except Last.fm's `method`
  value, named because the bare path (`/2.0/`) does not say which call it
  was. Every callback catches its own errors so a logging failure can never
  fail the request it describes.
- **`utils.create_optimized_session`** attaches a fresh trace config (one
  per session: `aiohttp.ClientSession` freezes whatever `TraceConfig` it is
  given at construction, so a shared module-level one could not accept new
  sessions' callbacks) and wraps the returned session's `close()` so the
  summary logs the first time it closes. Not a `ClientSession` subclass:
  aiohttp 3.14 fires a `DeprecationWarning` at class-definition time for
  any subclass of it (`__init_subclass__` in `aiohttp.client`), which would
  have shown up as a warning on every test that imports this module.
  Rebinding `close` on the session instance reaches the same one place --
  `__aexit__` and every explicit `await session.close()` both call
  `session.close()` -- without subclassing. The function's name, signature
  and return type (an `aiohttp.ClientSession`, used as `async with`) are
  unchanged, so no caller and no existing test needed touching; every
  existing provider test mocks `session.get`, so the hook never fires in
  them.
- **`release_checks.py`'s three worker lines** (INFO, counts only, no
  artist or album names): `run_release_checks` logs its candidate count
  when it starts and, in its `finally` block, the checked and corrected
  counts when it finishes; `enqueue_release_check` logs which setting is
  missing -- `MUSICBRAINZ_ENABLED` or `MUSICBRAINZ_CONTACT` -- when it
  skips.
- **Reading "corrected"** (not defined further by the brief): the finish
  line reports `state["moved_out"]`, the count of results the worker
  actually rewrote in place, not `moved_out + moved_in` -- a moved-in
  candidate is only tallied on the job's stats, never applied to a result
  (`_check_candidate`'s own comment: "move-ins are counted on the job's
  stats, not inserted"). Flagged here in case the owner intended the wider
  count.
- **Privacy proof.** The adversarial test (a query holding
  `api_key=SECRET-KEY` and `artist=Radiohead`) was run red first: with
  `_call_outcome_line` temporarily logging the full URL instead of
  `url.path`, both the pure-function test and the end-to-end
  `TestServer`-backed test failed on the planted leak, then passed again
  once reverted. `tests/services/test_api_logging.py` drives a real
  session from `create_optimized_session()` against a local
  `aiohttp.test_utils.TestServer` (part of `aiohttp`; no new dependency)
  for the end-to-end cases, and tests the host map and the Last.fm
  `method` exception as pure functions of a `yarl.URL` -- the TestServer's
  host is always `127.0.0.1`, which only exercises the unknown-host
  fallback branch. `tests/services/test_release_checks.py` gained four
  tests for the three worker lines and the two skip reasons.
- **Docs.** `.claude/SESSION_CONTEXT.md` Section 3 lists the new module;
  Section 4 gains the `utils -> api_logging` edge (`AGENTS.md`
  Anti-Pattern 2). `FINDINGS.md` resolves F-B23-6 (rotated to
  `docs/history/findings/FINDINGS_ARCHIVE.md` by `--fix`).
- **Not run:** Step 5, the owner's live check with a real Last.fm run under
  `DEBUG_MODE=1` and without it -- it needs the owner's username and API
  quota. Left unticked in the reconcile plan; the owner records the outcome
  here when it runs.

Validation: `pytest -q` -- **1820 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

Forward guidance: the reconcile plan's Task 13 (its whole Stage 4) is done.
Next is the foundation plan's Task 5, per Section 3's order list -- Step 5
above is still owed from the owner.

### 2026-09-24 - Provider call logging joins the reconcile plan as its Task 13

Side task, no batch tag: files F-B23-6 and writes the task that fixes it,
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **Why.** Testing Batch 22's MusicBrainz corrections, the owner still saw
  no MusicBrainz line in the log. At source: the release-check worker logs
  nothing on success, `enqueue_release_check` skips silently without
  `MUSICBRAINZ_CONTACT`, and `musicbrainz.py` and `deezer.py` have no log
  call at all.
- **Owner rulings, 2026-09-24.** Scope: all four providers, plus the three
  release-worker lines the plan's "After this plan" section held (moved into
  the task, with a pointer left behind). Levels: 429 and 5xx at WARNING with
  `Retry-After`, other non-2xx at INFO, timeouts and connection errors at
  WARNING, 2xx at DEBUG, and one INFO summary per provider per session.
- **Recorded:** F-B23-6 (P2, owner-added) in `FINDINGS.md`; a Part C bullet
  in `BATCH23_DEFINITION.md`; the reconcile plan's disposition row, its
  Stage 4 and Task 13, and its stage count and order list; PLAYBOOK Section
  3's order list, which runs Task 13 before the foundation plan's Task 5.
- **Design constraint carried into the task:** no query string in any log
  line, because it carries Last.fm's API key and the search terms the
  definition's Data handling section keeps out of logs. The one exception
  is Last.fm's `method` value.
- Validation: `pytest -q` -- **1802 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-23 - The DOC024 wiring gets a test, and its severity gets stated truly

Side task, no batch tag: fix round 1 on the archive page target task --
add CLI-level test coverage for the `cli.py` splice that actually surfaces
DOC024 to `--check`/`--fix`, and correct two overclaims the original commit
left standing, part of Batch 23 WP-0 Part B. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- **CLI-level test for DOC024** (`tests/test_docsync_cli.py`,
  `TestArchivePageTargetDiagnosticsThroughTheCli`): a real `--check` and
  `--fix` run over a fixture corpus with an unpaginated managed archive over
  the page target asserts `"WARNING DOC024"` in stderr, naming the archive,
  with exit 0. Every prior DOC024 test only called
  `ArchiveStore.page_target_issues` directly, so none of them exercised
  `cli._archive_page_target_issues`'s splice into `_collect_issues`
  (`scripts/docsync/cli.py`) -- the wiring that actually makes DOC024
  visible to an operator. Proved by temporarily removing that splice: both
  new tests failed red (`WARNING DOC024` absent from stderr, exit code
  still 0 -- a silent regression, not a crash), then passed green again
  once restored.
- **Two new unit tests** (`tests/test_docsync_archives.py`): an undated
  entry placed on the writable tail page produces no never-ageing warning
  (the guard clause was previously only inferred, never asserted); and an
  unpaginated archive at exactly `max_lines` does not warn while one line
  over does, measured the same way the check does
  (`len(flattened.splitlines())`).
- **`AGENTS.md`'s DOC001-DOC024 sentence** overclaimed that every code
  "block[s] rather than warn[s]" -- false for DOC024 (100% warning) and for
  DOC023's grandfathered-finding count. Reworded to
  "error-severity ones block, and warnings print without changing the exit
  code," keeping the exact substring `returns typed DOC001-DOC024 issues`
  that `STATED_RANGE_RE` reads, and without enumerating the warning codes
  (the catalogue owns them).
- **`docs/architecture/documentation-tooling.md`**: the catalogue's lead
  paragraph made the same overclaim ("exits 1", full stop) -- corrected to
  "exits 1 on any error-severity [issue]; a warning ... prints and leaves
  the exit code alone." The DOC024 paragraph now states the full
  never-ageing condition (finalized, non-oversized, hot page of a paginated
  archive) instead of dropping the non-oversized/hot qualifiers, and the
  DOC020 cold-rule sentence is anchored to `--as-of` ("more than
  `cold_days` days before `--as-of`") instead of the looser "older than
  `cold_days`".

Validation: `pytest -q` -- **1802 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The archive page target gets a reader

Side task, no batch tag: warn when a managed archive outgrows its page
target or a paginated page can never age, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 4.** `ArchiveStore.page_target_issues`
  (`scripts/docsync/archives.py`) is a new DOC024 diagnostic, warning
  severity only, so `--check` still exits 0. It fires on two conditions: an
  unpaginated (legacy monolith) archive whose logical text has outgrown
  `[archives] max_lines`, naming `--paginate-archives`; and a paginated
  archive's finalized, non-oversized, hot page whose entries are not all
  dated, since `_age` requires every entry on such a page to carry a date
  before the cutoff and a page with even one undated entry can never
  satisfy that rule. `cli.py`'s `_collect_issues` folds these in for every
  path `_managed_archive_paths()` names.
- **The real corpus warns four times, not once**, correcting the brief's
  prediction: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (10451
  lines), `docs/history/findings/FINDINGS_ARCHIVE.md` (2277),
  `docs/history/logs/BATCH22_LOG.md` (989) and
  `docs/history/logs/BATCH21_LOG.md` (750) each exceed the 500-line target
  and are still unpaginated monoliths; `--check` on this worktree exits 0
  and prints all four.
- **`docs/architecture/documentation-tooling.md`** now names DOC024 in the
  renamed DOC001-DOC024 catalogue, and its cold-rule sentence states what
  `_age` actually checks -- every entry on a finalized, non-oversized, hot
  page dated before the cutoff -- rather than "365 days" alone.
- **`AGENTS.md`'s stated `DOC001-DOC023` range** (the sentence
  `test_stated_docsync_range_matches_the_highest_code_raised` reads) was
  bumped to `DOC001-DOC024` in the same commit: adding the `"DOC024"`
  literal to `archives.py` made that test fail, and the smallest fix was
  the one sentence the test reads. The rest of the range wording is left
  to Task 5, which owns it.
- **Live probe** (`/c/ssprobe`, `git archive HEAD` from this worktree,
  deleted after):

  | probe | expected | exit | codes |
  | --- | --- | --- | --- |
  | faithful copy, `--check` | same summary as this worktree | 0 | DOC024 x4 (same paths), root-BATCH warning |
  | red: `--check` (the corpus already carries the four oversized monoliths; nothing further to plant) | fires | 0 | DOC024 x4 |
  | near-miss: `--paginate-archives`, then `--check` | no oversize warning anywhere; `FINDINGS_ARCHIVE_0001.md` (28/28 entries undated) and `FINDINGS_ARCHIVE_0002.md` (9/16 undated) each warn once as never-ageing; no log page warns | 0 | DOC024 x2 |

Validation: `pytest -q` -- **1798 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The owner's rulings land in their findings

Side task, no batch tag: write the owner's 2026-09-23 WP-0 rulings into
FINDINGS.md and docs/design/RECONCILIATION.md, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the reconcile plan's Stage 3 Task 10.** Step 1b recorded
  `F-B21-53` no action (Q10 = b): the light card is delineated by its border,
  not lifted by its fill. `docs/design/README.md` was not edited -- it
  already reads "borders do the work" (line ~107) and "Edge, not elevation"
  (line ~254), and a sweep found no other live elevation claim about cards;
  `static/css/shell.css:566`'s "elevated paper pill" is the theme toggle, not
  a card, and was left alone.
- **Step 2 wrote six no-action records**, each replacing its free-prose
  `Status:` line with the canonical `- [x] **Status:** no action` /
  `**Completed:** 2026-09-23` / reason form: `F-B21-15` (no scheduled
  `GET /heatmap/<username>` route), `F-STYLE-1` and `F-STYLE-2` (guidance
  that cannot become a gate; the docstring convention stays undecided),
  `F-WORKTREE-4` (the owner's 2026-09-21 ruling, written in canonical form),
  `F-B21-24` (Tasks 2-5 shipped; Task 6 runs as Batch 23 WP-7's audit) and
  `F-MAS-2` (absorbed into `F-B21-18`; a pointer line was added under
  "Deferred / future-batch candidates" so the old id stays resolvable).
- **Step 3 re-graded `F-B21-48` and `F-B18-11`** to P2 -- a persistent
  scrobble cache is a feature, not a defect -- and moved both under "P2 --
  Scaling roadmap". The Codex/Copilot session-entry-point item, F-B21-25's
  third "Remaining" item, was filed as the new finding `F-B21-63` (the next
  free `F-B21-` number) under P2; F-B21-25's own "Remaining" paragraph now
  points at it instead of restating it.
- **Step 4 split the partly-ruled findings.** `F-B21-4` closes no action:
  items 1, 2 and 4 are settled (citing `templates/index.html` `.index-grid`,
  RECONCILIATION's loading-signal override, and RECONCILIATION section 16),
  and item 3 folds into Batch 23 WP-6 (Q13 = a). `F-B21-19` closes no
  action per Q12 = a: `docs/design/RECONCILIATION.md` section 1 gained an
  owner-approved override row for the width-driven mobile heatmap grid, and
  day detail (hover reveals what was played) is named a future feature since
  the payload holds only `daily_counts`. `F-DOCSYNC-6` and `F-WORKTREE-3`
  each gained a dated line: the boundary/ancestry items are no action, the
  mechanical bugs stay open for the control-plane plan. RECONCILIATION
  section 9's `F-B21-4` bullet and section 7's lead-in were reworded so
  neither sibling claim still reads as pending.
- **No test changed.** The task is documentation only; the test count stays
  at the baseline.

Validation: `pytest -q` -- **1793 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

Forward guidance: the reconcile plan's Stage 3 Task 10 (Part B) has landed,
completing every task in
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`. The
next step is the foundation plan's Tasks 4-10, per Section 3's order list.

### 2026-09-23 - The release-window rule gets one owner

Side task, no batch tag: fixes F-B23-5, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 12 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/domain.py` gains `release_window(release_scope, year,
  decade=None, release_year=None)`, which returns the inclusive `(first,
  last)` years a scope accepts, `None` when every year qualifies, and raises
  `ValueError` when a companion parameter is present but unparseable.
  `domain._matches_release_criteria` (the album filter) and
  `release_checks._window_end` (the correction worker) both derive from it
  now instead of each restating the same scope table; neither's name,
  signature or import path changed, so every test that used them passed
  unmodified.
- **The two divergences named in the finding are kept, per owner ruling
  2026-09-23 (KEEP PARITY).** An unparseable `decade` (the route does not
  validate it) still makes `_matches_release_criteria` return `False` and
  `_window_end` return `None`; the only change is that the warning now
  names the bad decade instead of the release date. `_window_end` still
  accepts `year` as a string; the filter is still only ever called with an
  `int`.
- **Parity tests pin both consumers' outputs first.**
  `tests/services/test_orchestrator_helpers.py` gains
  `test_matches_release_criteria_parity_before_release_window`, a
  parametrized test covering the four bounded scopes plus every divergence
  the finding names; `tests/services/test_release_checks.py` gains
  `test_window_end_parity_before_release_window`, the same coverage for
  `_window_end`. Both were checked against the pre-refactor functions (the
  finding's own known-bad decade warning reproduced) before the refactor
  landed, and both still pass against the derived code -- the net held.
  `test_window_end_per_release_scope` and
  `test_window_end_returns_none_on_unusable_inputs` pass unmodified.
- **Direct coverage for `release_window`** also lands in
  `tests/services/test_orchestrator_helpers.py`:
  `test_release_window_per_scope` (the four bounded scopes),
  `test_release_window_unbounded_returns_none` (`"all"`, an unrecognized
  scope, and a falsy companion) and
  `test_release_window_unparseable_decade_raises` (the adversarial case).
- **Deviation from the brief.** The brief's Files list names only
  `tests/services/test_orchestrator_helpers.py` and
  `tests/services/test_release_checks.py` as test files to touch, append
  only, and does not mention `tests/test_domain.py`. `release_window`'s own
  tests (Step 2) are therefore appended to
  `tests/services/test_orchestrator_helpers.py` -- the file that already
  hosts `_matches_release_criteria`'s adversarial coverage -- rather than
  added to a new or different test module.
- **Documents.** `.claude/SESSION_CONTEXT.md` Section 3's `domain.py`
  summary line now lists all five module-level functions:
  `normalize_name, format_album_key, normalize_track_name,
  _matches_release_criteria, release_window`.
  `docs/architecture/runtime-system.md`'s runtime-system prose named
  `_matches_release_criteria` as what the worker and the album filter both
  read from `domain.py`; it now names `release_window`, since that is the
  rule's one owner. A sweep for `_window_end` and "release window" across
  live prose found nothing else naming the old, two-copy shape.
- **F-B23-5 is resolved.** `domain.release_window` is the rule's one
  owner; the album filter and the worker's window end both derive from it.
- **Forward guidance:** Stage 2 is complete. Next is Stage 3, this plan's
  Task 10.

Validation: `pytest -q` -- **1793 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The export contracts are made consistent

Side task, no batch tag: a definition edit within Batch 23, made before
WP-1. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Author.** Codex (GPT-6) made these edits at the owner's request, after
  a read-only review of `BATCH23_DEFINITION.md` and the current execution
  path. The definition's header lists all seven changes and why.
- **The definition** gains a "Data handling" section as the one owner of
  the privacy contract. It separates listening history, which stays in
  memory, from reusable catalog metadata, which the existing enrichment
  cache may keep. It also makes these changes:
  - It separates failures refused before a job exists from content
    failures that end a running job.
  - WP-2 now hands WP-3 a pre-threshold album mapping, and WP-3
    partitions it once.
  - The memory acceptance measures the whole process, not only admitted
    buffers.
  - WP-6 must settle a statistics contract before it is implemented.
  - Each WP gets its own SDD plan, and that plan owns the task order.
- **The export outline**
  (`docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md`)
  and `README.md` now point at the definition instead of repeating the
  older privacy and aggregation wording. The outline's stale
  `routes.py` and `orchestrator.py` paths are updated.
- **Also corrected:** Section 3 still called Batch 23 "queued" and "not
  started", and named the outline as its plan. That bullet now says the
  batch is active and calls the file its cross-WP outline. A sweep found no
  other copy of the replaced wording outside dated history.
- **No effect on WP-0.** The WP-0 plans, their order and the next action
  (reconcile Task 12) are unchanged.
- **Scope:** documentation only. No code, test or gate changed.

Validation: `pytest -q` -- **1746 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The release-window rule gets a task of its own

Side task, no batch tag: a planning change within Batch 23 WP-0. Untagged
by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Filed F-B23-5 at P2, and the owner added it to WP-0 Part C
  (2026-09-23).** `release_checks._window_end` restates the scope table
  that foundation Task 12 moved to `domain._matches_release_criteria`, so
  the release-window rule has two copies. They already differ at the
  edges: an unparseable decade excludes every album in the filter but
  gives the worker no window.
- **Plan:** the reconcile plan gains Task 12, the last task of Stage 2 and
  before Stage 3. It pins both consumers' current outputs with parity tests
  first, then derives both from one `domain.release_window`. Changing the
  unparseable-decade behaviour needs an owner ruling before dispatch. The
  definition's Part C now lists F-B23-5 as the fourth owner-added P2, and
  the plan's disposition table has its row.
- **Also corrected:** the plan's Acceptance said only Tasks 4 and 6 edit
  an existing test. Task 11 replaced one too, so it now says 4, 6 and 11.
- **Scope:** documentation only. No code, test or gate changed.

Validation: `pytest -q` -- **1746 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Release checks run without the cache DB

Side task, no batch tag: fixes F-B22-8, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 11 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/release_checks.py`'s `run_release_checks` no longer
  returns early when `_get_db_connection()` finds no cache: it logs
  "Release checks running without the cache DB: findings will not be
  saved." and runs the job's candidates against MusicBrainz regardless,
  guarding the three uses of `conn` (`_lookup_cached`, `_check_candidate`'s
  persist, and the `finally` close) with `if conn`. Everything else is
  unchanged: the job still ends `done`, the per-result outcomes are the
  same, and the shared one-request-per-second limiter still paces the
  requests. `tests/services/test_release_checks.py` replaces
  `test_run_release_checks_marks_skipped_without_a_db_connection` with
  `test_run_release_checks_runs_without_a_db_connection` (asserts the
  lookup runs, nothing is persisted, and the result still moves out) and
  adds
  `test_run_release_checks_without_a_db_connection_survives_a_lookup_error`
  (a MusicBrainz failure with no connection still ends `done`).
  `test_run_release_checks_closes_the_connection_when_a_lookup_raises`
  passes unchanged, proving the connected path still closes.
- **F-B22-8 is resolved.** `run_release_checks` runs its candidates
  without a cache connection and skips only the cache read, the persist
  and the close.
- **Deviation from the brief (controller-directed).** F-B23-3's status
  paragraph is rewritten: it stays open (P2), now says F-B22-7 and
  F-B22-8 have both landed (reconcile Tasks 4-6 and 11) and are to be
  reassessed against the code they left, and drops the "keep it out of
  their commits" sentence now that both have landed.
- **Forward guidance:** Stage 2 is complete. Next is Stage 3, this plan's
  Task 10.

Validation: `pytest -q` -- **1746 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The capacity refusal states the configured cap

Side task, no batch tag: fixes F-LOAD-1, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 9 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/routes/__init__.py` gains `_capacity_message()`,
  which returns `f"Too many requests in progress: all {MAX_ACTIVE_JOBS}
  search slots are busy. Please try again in a moment."`, reading
  `MAX_ACTIVE_JOBS` from `scrobblescope.config` rather than a literal.
  `scrobblescope/routes/album_flow.py`'s and
  `scrobblescope/routes/heatmap_flow.py`'s refusal strings now both read
  `_routes._capacity_message()` through the existing `_routes` module
  reference. There is no occupancy counter: the message only renders after
  `acquire_job_slot()` has just failed, when every slot is already taken, so
  a count would always read cap/cap. Two new tests in `tests/test_routes.py`
  cover it: `test_album_capacity_refusal_states_the_configured_cap` and
  `test_heatmap_capacity_refusal_states_the_configured_cap`, both patching
  `MAX_ACTIVE_JOBS` to a distinctive value and asserting the refusal names
  it.
- **F-LOAD-1 is resolved.** Both refusals read
  `routes._capacity_message()`, which states the configured
  `MAX_ACTIVE_JOBS`.
- **Deviation from the brief.** The brief's Step 5 dependency-graph line
  for `routes/__init__.py` omitted `domain`, which the module has imported
  (`format_album_key`) since `d20a7924`. The `config` edge from this task
  is added alongside the missing `domain` edge in the same edit, so the
  line now reads `routes/__init__.py <- config, domain, lastfm,
  repositories, spotify, unmatched, utils, worker; ...`. No other
  dependency-graph line was touched.
- **Forward guidance:** next is reconcile Task 11 (F-B22-8, release checks
  run without the cache DB).

Validation: `pytest -q` -- **1745 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The year gate reads the UTC calendar

Side task, no batch tag: fixes F-B21-6, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 8 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/routes/__init__.py` gains `_current_year()`, which
  returns `datetime.now(timezone.utc).year`; `inject_current_year` now
  returns `{"current_year": _current_year()}` instead of reading the host's
  local clock. `scrobblescope/routes/album_flow.py`'s two `datetime.now().year`
  sites -- the results-page year fallback and the submit-path validation
  gate -- now read `_routes._current_year()` through the existing `_routes`
  module reference, and the file's now-unused `datetime` import is removed.
  Two new tests in `tests/test_routes.py` cover it:
  `test_current_year_reads_the_utc_calendar` (the helper itself, against a
  clock stub whose local and UTC readings disagree) and
  `test_results_loading_year_gate_uses_the_utc_year` (the submit-path gate's
  upper bound comes from `routes._current_year()`).
- **F-B21-6 is resolved.** Every year gate reads `routes._current_year()`,
  which uses `datetime.now(timezone.utc)`, so the gate and the orchestrator's
  UTC-built fetch window can no longer disagree around New Year.
- **Forward guidance:** next is reconcile Task 9 (F-LOAD-1, the capacity
  refusal states the configured cap).

Validation: `pytest -q` -- **1743 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The frontend gate's one-off touch-target failure is filed

Side task, no batch tag: a finding filed during Batch 23 WP-0. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Filed F-B23-4 at P2, non-blocking (owner ruling, 2026-09-23).** After
  reconcile Task 7 committed, the independent gate run's frontend gate
  failed once in `check_touch_targets`: two `.btn` controls on the 404 page
  measured 40px high in the wide-touch profile. The same tree then passed
  three times. The finding records why only that profile can fail (at
  1280px only `error.css`'s `any-pointer: coarse` rule gives `.btn` its
  44px) and that the check measures with nothing waiting for that rule.
- **Scope:** documentation only. No code, test or gate changed. WP-0 Part C
  clears P0 and P1 findings, so a P2 finding stays out of WP-0.
- **Forward guidance:** until F-B23-4 is fixed, re-run a frontend-gate
  failure once before acting on it when the implementer's own runs were
  green. Next is reconcile Task 8 (F-B21-6).

Validation: `pytest -q` -- **1741 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Both pipelines end a crash as internal_error

Side task, no batch tag: fixes F-SWE-5, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 7 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/errors.py` gains an `internal_error` entry
  (`source: "internal"`, `retryable: False`). `heatmap.py`'s
  `_report_heatmap_failure` now publishes it instead of borrowing
  `lastfm_unavailable`. `orchestrator/__init__.py` gains
  `_report_album_failure`, called from `background_task`'s `on_run_error`
  in place of a bare `logging.exception`, so the album pipeline now
  publishes a terminal state on an unhandled crash instead of leaving the
  job stuck. `static/js/loading.js`'s `showFailure` now looks up the source
  label in an `ERROR_SOURCE_LABELS` map and hides the source line for any
  source not in it (`internal` included), instead of defaulting every
  unrecognized source to "Spotify". `scripts/dev/_frontend_gate_pipeline.py`
  pins both: the album rate-limit failure still names `Source: Last.fm`,
  and a probed `internal` failure hides the source line.
- **Two architecture diagrams updated in the same commit:**
  `docs/architecture/heatmap-sequence.md`'s `opt Unhandled exception
  anywhere above` block now draws `set_job_error(internal_error)`, with its
  closing prose split to say the inner, status-based Last.fm path still
  emits `lastfm_unavailable` while the outer backstop publishes
  `internal_error`. `docs/architecture/top-albums-sequence.md`'s `opt
  Exception escaping that handler` block now draws
  `set_job_error(internal_error)` and its note says the pipeline publishes
  a terminal state, so a polling page stops instead of waiting forever.
- **Tests added, three in total, none replaced:**
  `TestErrorCode.test_internal_error_exists` and
  `TestHeatmapTask.test_unhandled_crash_publishes_internal_error`
  (`tests/test_heatmap.py`), and
  `test_background_task_crash_publishes_internal_error`
  (`tests/services/test_orchestrator_fetch_and_process.py`). No existing
  test changed.
- **This resolves F-SWE-5.** Both entry points now publish `internal_error`
  from their outer handler, so a fault that is ours is no longer reported
  as a Last.fm outage, and the album pipeline no longer leaves a polling
  page waiting on a job that would never finish.
- **Bookkeeping:** the reconcile plan's Task 7 steps are ticked. Section 3's
  order list now records Task 7 landed alongside Tasks 3-6 in Stage 2.

Validation: `pytest -q` -- **1741 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The unused enrich_albums is retired

Side task, no batch tag: fixes F-B22-7, part 3 of 3, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 6 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/spotify.py`'s `enrich_albums` is deleted: after Task 5,
  the live path already does everything it did, through
  `_run_spotify_search_phase` and `_run_spotify_batch_detail_phase`, with the
  per-phase progress the loading page shows that `enrich_albums` never had.
  `scrobblescope/orchestrator/__init__.py` drops its import and its
  `__all__` entry; `album_metadata_from_details` keeps both, since
  `_details.py` still calls it through the facade. `git grep -n
  "enrich_albums" -- '*.py'` now returns nothing.
- **Tests removed, five in total, none replaced:**
  `test_enrich_albums_empty_misses_makes_no_request`,
  `test_enrich_albums_returns_matched_and_unmatched`,
  `test_enrich_albums_marks_unmatched_when_detail_lookup_misses` and
  `test_enrich_albums_handles_missing_cover_art`
  (`tests/services/test_spotify_service.py`, with their banner comment and
  the `enrich_albums` import), and
  `test_enrich_albums_is_exposed_on_the_orchestrator_facade`
  (`tests/services/test_orchestrator_fetch_spotify.py`, with both of its
  `enrich_albums` imports).
- **This resolves F-B22-7.** The Spotify payload is translated only in
  `spotify.album_metadata_from_details`; every metadata row is built by
  `AlbumMetadata.as_cache_row`, whose Deezer rows no longer carry an id in
  `spotify_id` (Task 4); the unused `enrich_albums` and its tests are gone.
- **Bookkeeping:** the reconcile plan's Task 6 steps are ticked. Section 3's
  order list now records Task 6 landed alongside Tasks 3-5 in Stage 2.

Validation: `pytest -q` -- **1738 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The Spotify payload is translated once, in spotify.py

Side task, no batch tag: fixes F-B22-7, part 2 of 3, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 5 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/spotify.py` gains `album_metadata_from_details`, the
  one place the application reads a Spotify album object into the provider
  contract; `enrich_albums` now calls it instead of building `AlbumMetadata`
  inline. It is re-exported on the orchestrator facade
  (`scrobblescope/orchestrator/__init__.py`).
- **The detail phase files, it no longer parses.**
  `scrobblescope/orchestrator/_details.py`'s "Extract cacheable fields" loop
  now calls `_orchestrator.album_metadata_from_details` and appends
  `metadata.as_cache_row(...)` (Task 4's contract) instead of building the
  row by hand; its now-unused `normalize_track_name` import is dropped, and
  the module docstring names the new cross-cutting dependency.
  `scrobblescope/orchestrator/_deezer_fallback.py`'s inline 9-tuple is
  replaced the same way. Since Task 4, that tuple was already identical to
  what `as_cache_row` writes, so the Deezer row is unchanged in shape.
  `provider_url` for a Spotify row now holds the album's Spotify URL instead
  of `NULL`, since the 9-tuple form carries it; `_batch_persist_metadata`
  still accepts 6-tuples.
- **Tests added, four in total:**
  `test_album_metadata_from_details_translates_one_payload` and the
  parametrized `test_album_metadata_from_details_degrades_field_by_field`
  (`tests/services/test_spotify_service.py`, two cases: no `images` key and
  an empty list), and `test_process_albums_persists_a_spotify_row_through_the_contract`
  (`tests/services/test_orchestrator_process_albums.py`), which pins the
  live Spotify path's persisted row as the provider contract's nine-element
  form. No existing test changed.
- **Bookkeeping:** the reconcile plan's Task 5 steps are ticked. Section 3's
  order list now records Task 5 landed alongside Tasks 3 and 4 in Stage 2.

Validation: `pytest -q` -- **1743 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - A Deezer id no longer lands in the Spotify column

Side task, no batch tag: fixes F-B22-7, part 1 of 3, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 4 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `AlbumMetadata.as_cache_row` (`scrobblescope/enrichment.py`) now
  writes `album_id` into the `spotify_id` column (tuple index 2) only when
  `provider == "spotify"`; every other provider writes `None` there, matching
  what the live Deezer fallback has always written at that column. F-B22-7 is
  not resolved by this task -- Tasks 5 and 6 complete it.
- **Two existing assertions changed**, both in
  `tests/services/test_enrichment.py`, because the finding requires it:
  `test_album_metadata_carries_its_provider_and_url`'s expected tuple pinned
  the Deezer album id at index 2, and
  `test_cache_row_matches_what_the_persistence_layer_unpacks` asserted
  `row[2] == meta.album_id` for a Deezer row -- both pinned the pre-fix
  (wrong) value the method wrote before this change. A new test,
  `test_cache_row_puts_a_spotify_album_id_in_the_spotify_column`, pins the
  Spotify case.
- **Bookkeeping:** the reconcile plan's Task 4 steps are ticked. Section 3's
  order list now records Task 4 landed alongside Task 3 in Stage 2.

Validation: `pytest -q` -- **1739 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Reading a job no longer renews its lease

Side task, no batch tag: fixes F-SWE-6, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 3 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done, for the owner's Q1 = a: reads never renew a job's lease.
  `get_job_progress`, `get_job_unmatched` and `get_job_context`
  (`scrobblescope/repositories.py`) no longer write `updated_at`;
  `cleanup_expired_jobs` still reaps on that field, but only a writer now
  renews it. A polled job -- an open results tab, or the release-check
  worker's `get_job_context` existence check -- expires `JOB_TTL_SECONDS`
  after its last write, not its last read.
- **Test added:** `test_reading_a_job_does_not_renew_its_lease`, parametrized
  over the three getters (`tests/test_repositories.py`). No existing test
  asserted the old renewal, so none changed.
- **`scrobblescope/config.py`:** a new comment above `JOB_TTL_SECONDS` states
  the reads-never-renew contract.
- **F-SWE-6 resolved**, with the canonical record and a completion date;
  `doc_state_sync.py --fix` rotated it into
  `docs/history/findings/FINDINGS_ARCHIVE.md`.
- **Bookkeeping:** the reconcile plan's Task 3 steps are ticked. Section 3's
  order list now records Stage 2 as started, with Task 3 landed.
- **Fix round 1:** F-SWE-5's body still called F-SWE-6 out as compounding
  it ("a polled job never expires"), which this task's own fix made false.
  Reworded to the past tense: F-SWE-6 used to compound it; since it was
  settled, the stuck job now expires `JOB_TTL_SECONDS` after its last write.
  The reconcile plan's Step 5 sweep is re-run with wrapped-line variants; no
  other sibling copy survives outside `BATCH23_DEFINITION.md`'s historical
  before/after narrative and `README.md`'s unrelated metadata-cache TTL
  sentence, both out of this task's scope. No test added.

Validation: `pytest -q` -- **1739 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The work-package state gap is filed as F-DOCSYNC-15

Side task, no batch tag: files the docsync work-package state gap this
amendment exposed, part of Batch 23 WP-0 Part B. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- **Task 2 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scripts/docsync/parser.py` `_collect_wp_numbers` counts every
  `WP-<n>` token in a current-batch entry heading as a completed work
  package, so the first commit of a multi-commit work package already makes
  the dashboard name the next one -- verified directly before filing:
  `docs/history/logs/BATCH22_LOG.md` carries three `(Batch 22 WP-4)` entries
  dated 2026-09-20, all landed before WP-4 was actually done, and
  `_collect_wp_numbers` regex-matches `WP-(\d+)` against each entry heading
  with no completion check at all.
- **Filed as F-DOCSYNC-15** under `FINDINGS.md` "P1 -- Next batch
  candidates", status open (P1), unchecked. The body records the owner's Q4
  fix shape (2026-09-23): a work package closes only on an entry carrying an
  explicit `**Status:** WP-N complete` line, which the control-plane
  follow-on plan implements.
- **Bookkeeping:** `BATCH23_DEFINITION.md` WP-0 Part B's "File the docsync
  gap this amendment exposed" checkbox is ticked (done 2026-09-23, as
  F-DOCSYNC-15); its Part C set now names F-DOCSYNC-15 alongside the "38 IDs
  plus one" count. The reconcile plan's Task 2 steps are ticked. Section 3's
  order list now records Stage 1 (Tasks 1 and 2) as complete.
- No code changed; no test added.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Export upload ownership, three depth findings, and a template fix

Side task, no batch tag: records owner rulings on the 2026-09-23
architecture-depth proposal, part of Batch 23 WP-0. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands. No code changed. With Task 12's
fix round (`972264f`) reviewed clean, Part A -- the loop protocol, the
three extractions and the release-window leaf -- is complete.

- **The proposal is now tracked** as
  `docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`, renamed from
  the owner's "ScrobbleScope - further architectural depth.html" to the
  reports folder's topic-and-date form. An older `.htm` draft beside it stays
  untracked. DOC001 checks only `.md` references and skips paths containing
  spaces, so the rename is a naming convention, not a gate fix.
- **Card 04 amends the export plan now.** The upload has one owner at every
  moment and is never copied: the route owns it until the thread starts and
  closes it on every refusal, and the task owns it after that. Admission
  also caps export jobs in flight at `EXPORT_MAX_IN_FLIGHT`, because the
  parse semaphore bounds running parses, not buffers waiting for a permit.
  The export plan's new "Upload ownership and the waiting bound" section
  holds the rule, and the definition's WP-3 and WP-4 checkboxes and
  acceptance carry it. The plan's Phase 2 now records the Part A
  extractions as landed, under their real names.
- **Cards 01-03 are filed at P2** as F-B23-1 (album calculation returns its
  whole answer), F-B23-2 (Last.fm translates its own payload) and F-B23-3
  (the cache module owns its connection). F-B23-1 is timed by the owner:
  after WP-0's provider repairs and before WP-6's design, with any move into
  Batch 23 needing its own scope amendment. The definition's WP-6 names that
  decision point.
- **The reconcile plan's finding template is corrected.** It put the reason
  on the status line (`resolved -- <reason>`). The gate accepts only a bare
  `resolved` or `no action`, and Task 1's implementer found this by running
  `--fix`. The template, Task 1 Step 3's record of what ran, and Task 10
  Step 2's no-action form now follow the archive's order: status,
  completion date, then the reason on its own line.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Close six stale pending-deploy findings

Side task, no batch tag: close the six finding records that still said "resolved locally, pending
deploy", part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope: the reconcile plan's Stage 1 Task 1.** F-B20-3, F-B21-10, F-B21-26, F-B21-27, F-B21-28 and
  F-B21-29 all said "resolved locally, pending deploy" although their fixes were already on
  `origin/main`. `git fetch origin` ran first, then `git merge-base --is-ancestor` confirmed all seven
  named fix commits (`85e7511`, `079c2b0c`, `b1fdb121`, `ee5ee4eb`, `47321b23`, `df28c06d`, `8b37566a`)
  are ancestors of `origin/main`; none printed STOP, so all six records were written.
- **Plan vs implementation: one deviation, forced by the gate.** The brief's canonical Status line put
  the "fixed by \`<sha>\` ... confirmed an ancestor of \`origin/main\`" text on the checked `**Status:**`
  line itself. `scripts/docsync/findings.py`'s DOC014/DOC015 checks require that line's value to
  normalize to the bare word `resolved` (or `no action`); anything else is rejected, and the word
  "deployed" inside the brief's sentence also trips DOC014's pending-qualifier scan, which is why the
  first `--fix` run failed with six errors naming exactly these findings. Every already-archived finding
  in `docs/history/findings/FINDINGS_ARCHIVE.md` uses the bare form for the same reason. Each of the six
  now reads `- [x] **Status:** resolved` / `**Completed:** <date>`, followed immediately by a new prose
  line carrying the brief's exact sentence (the sha(s), "deployed with it", "confirmed an ancestor of
  \`origin/main\` on 2026-09-23") -- that line sits outside the lifecycle record the gate parses, so its
  wording is unconstrained. The rest of each body (the "Was recorded as" and "Source" lines) was kept
  unchanged, per the brief. F-B21-28 and F-B21-29 each have two fix commits in the brief's table, so
  their new prose line names both ("fixed by \`X\`, completed by \`Y\`, and deployed with it"); the
  completion date used is the later commit's date in both cases, as directed. F-B20-3's new prose line
  uses the brief's supplied reason text (Bootstrap and both CDN providers retired by \`85e7511\`, Batch 21
  WP-8) in place of the generic "fixed by" clause. Completion dates came from
  `git log --ancestry-path --merges --reverse --format=%cs "<sha>..origin/main"`, falling back to the fix
  commit's own date when no merge commit exists on that path: 2026-09-19 (F-B20-3), 2026-09-10 (F-B21-10,
  using `079c2b0c`), 2026-09-10 (F-B21-26 and F-B21-28, using `b1fdb121`), and 2026-09-07 (F-B21-27 and
  F-B21-29, using `ee5ee4eb` and `8b37566a` respectively).
  `doc_state_sync.py --fix` then rotated all six resolved records into
  `docs/history/findings/FINDINGS_ARCHIVE.md`, which emptied the `## P0 -- Fix before next deploy`
  section (F-B21-26, F-B21-27, F-B21-28 and F-B21-29 were its only members); a line was added under
  that heading, rather than deleting it, because other documents cite the severity levels.
  `BATCH23_DEFINITION.md` WP-0 Part B's "Stale finding records" checkbox and the reconcile plan's Task 1
  step boxes are ticked, and Section 3's numbered order list now notes Stage 1 Task 1 landed, keeping
  "WP-0 is next." exactly.
- **No test changed.** The task is documentation only; `git diff --stat tests/` is empty, so the test
  count stays at the baseline.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner tests were excluded, since
they are not repository state.

Forward guidance: the reconcile plan's Stage 1 Task 1 (Part B) has landed; Stage 1 Task 2 (the docsync
work-package gap) is still open. The next steps are the rest of Stage 1, then Stage 2 (Part C, including
Task 11 for F-B22-8), then Stage 3, then the foundation plan's Tasks 4-10, per Section 3's order list.

### 2026-09-23 - The release-window rule gets a leaf home

Side task, no batch tag: move `_matches_release_criteria` into `scrobblescope/domain.py`, part of
Batch 23 WP-0 Part A. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 12** (review A card 3, added to Part A on 2026-09-23). The rule
  had two consumers -- the album filter in `orchestrator/_results.py` and the correction worker's
  `release_checks._matches_window` -- and lived in `orchestrator`, which imports `release_checks` at
  module level, so the worker could only reach the rule through a function-local import. That was the
  one documented exception in the SESSION_CONTEXT Section 4 dependency graph.
- **Plan vs implementation: matched exactly, no deviation.** `domain.py` gained the function verbatim
  (body and docstring unchanged) plus `import logging`, placed after `normalize_track_name`.
  `orchestrator/_results.py` deletes the definition and extends its existing `from scrobblescope.domain
  import normalize_name` line to also import `_matches_release_criteria`, so the facade's re-export
  (`scrobblescope.orchestrator._matches_release_criteria`) and `orchestrator/_results
  ._matches_release_criteria` both still resolve unchanged. `release_checks.py` imports the rule from
  `domain` at module level, next to `normalize_name`, and `_matches_window` lost its function-local
  import and cycle-explaining docstring in favour of one sentence naming the shared home. Both import
  orders (`release_checks` before `orchestrator` and the reverse) were run directly and succeeded, since
  the change is specifically about import order. `.claude/SESSION_CONTEXT.md` Section 4 dropped the
  `; orchestrator (facade, DEFERRED -- see note)` qualifier from the `release_checks.py` line and the
  "The one deferred edge" paragraph; a repo-wide check confirmed nothing else cited it. No new edge was
  added: both consumers already import `domain`. `docs/architecture/runtime-system.md`'s
  correction-worker bullet now says the worker and the album filter both read the rule from
  `domain.py`, instead of describing the function-local import.
  `BATCH23_DEFINITION.md` WP-0 Part A and the foundation plan's Task 12 checkboxes are ticked, and
  Section 3's numbered order list marks this step done, keeping "WP-0 is next." exactly.
- **No test changed.** `git diff --stat tests/` is empty; the task is behaviour-neutral and adds no
  test, so the test count stays at the baseline.
- **Fix round 1 (review finding, Important).** The Mermaid diagram in
  `docs/architecture/runtime-system.md` still drew `ReleaseChecks -.->|imported inside a function|
  Album`, an edge the move made false: `release_checks.py` no longer imports anything from
  `orchestrator` at all. Deleted that one line; `ReleaseChecks --> Domain` already carries the real
  dependency, so nothing replaces it. `Album` stays referenced by several other edges, so no node was
  orphaned. A repo-wide grep for the same edge in any other wording found none. The diagram was
  validated with the Mermaid Chart MCP tool (`valid: true`, `diagramType: flowchart`) after the edit.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner tests were excluded, since
they are not repository state.

Forward guidance: WP-0 Part A's foundation-plan tasks (2 and 12) are both done. The next steps are the
reconcile plan's Stage 1 through Stage 3 (Task 11 included), then the foundation plan's Tasks 4-10, per
Section 3's order list.

### 2026-09-23 - Owner rulings: the release-window leaf and F-B22-8

Side task, no batch tag: records three owner rulings, part of Batch 23 WP-0.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands. No code
changed.

- **Q0 is settled: the Batch 22 MusicBrainz check is done.** The worker logs
  nothing on success, so the logs could not answer it. `original_release_cache`
  could. It held 121 rows, and 60 were written within a minute of each of the
  owner's two runs with Postgres up (06:04 and 16:34 local). Section 3's
  Batch 22 bullet and the definition's Part B box now record both owner items
  as done. The reconcile plan's Task 1 Step 5 is marked as taken over by this
  commit, because Section 3 must stay true at every commit.
- **Review A card 3 joins Part A** as the foundation plan's Task 12. It moves
  `_matches_release_criteria` into `domain.py`, which deletes the one deferred
  edge in the import graph. It is numbered 12, not 2b, because `task-brief`
  would pull a "Task 2b" heading into Task 2's brief. The rest of the
  2026-09-21 review was already dispositioned in the foundation plan's DoD.
- **F-B22-8 is filed and joins Part C at P2.** With the cache DB down,
  `run_release_checks` skips the whole job. The owner ruled that checks run
  regardless, with only persistence skipped. It is P2 because only local
  development reaches the branch: on Fly.io the database wakes with the app.
  The reconcile plan's Task 11 fixes it; one existing test that asserts the
  skip is replaced there, as Part C allows.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The remaining shared extractions

Side task, no batch tag: extract the three remaining shared steps, part of
Batch 23 WP-0 Part A. Untagged by owner ruling 2026-09-23 until the whole
of WP-0 lands.

- **What moved, verbatim (controller ruling R12).** In
  `scrobblescope/orchestrator/__init__.py`: `_cap_threshold_exclusions(threshold_exclusions)`
  is the tie-break-commented cap block from `fetch_top_albums_async`, returning the
  (possibly capped) dict; `total_below_threshold` is still computed from the
  uncapped dict before the call. `_process_filtered_albums(job_id, filtered_albums,
  year, sort_mode, release_scope, decade, release_year, limit_results,
  overall_start_time)` is the tail of `_fetch_and_process`, from the
  `_apply_pre_slice` call through `enqueue_release_check` and `return results`;
  `_fetch_and_process` keeps its outer `try`/`except`, `overall_start_time`, and the
  "Processing your albums..." progress call, and now ends with
  `return await _process_filtered_albums(...)`. In `scrobblescope/heatmap.py`:
  `_zero_fill_daily_counts(counts, from_date, to_date)` is Phase 2 of
  `_aggregate_daily_counts`, which now returns its result.
- Each new function's docstring names the Batch 23 Spotify-export path as its
  second caller.
- No test written or modified: `tests/services/test_orchestrator_fetch_and_process.py`
  and `tests/test_heatmap.py` pass unmodified, and `git diff --stat tests/` was
  empty after each of the three moves.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Session handoff written

Side task, no batch tag: session close for Batch 23 WP-0, by owner request
ahead of a context reset. It adds `docs/history/reports/HANDOFF_2026-09-23.md`
and points Section 3's handoff bullet at it. No code changed, and no task
started.

- **What the handoff records:**
  - the state of WP-0 and the gate results;
  - the four commit ranges of 2026-09-23;
  - the next steps, in the order Section 3 owns;
  - the WP-0-specific rules;
  - the untracked artifacts a cold agent needs: the triage reports, the
    reusable kit for subagent-driven work, and the stale foundation ledger;
  - the traps hit this session.
- **New evidence on Q0.** The owner's second run had Postgres up and still
  logged no MusicBrainz line. That proves nothing: the release-check worker
  logs nothing on a successful run, and the primary checkout sets no
  `MUSICBRAINZ_CONTACT`. The handoff's section 6 says how to settle it.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Owner answers to the reconcile-and-clear plan

Side task, no batch tag: records the owner's answers to Q0-Q16 of
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`,
part of Batch 23 WP-0. No code changed, and no task started: the session
ends here for a context reset, by owner instruction.

- **Every question takes its recommended answer, except three.**
  - **Q0:** no MusicBrainz lines in the log. This is expected, not a result.
    `release_checks._run_release_checks` skips when the cache database is
    down, and Postgres was down on purpose for that run.
    `enqueue_release_check` skips silently when `MUSICBRAINZ_CONTACT` is
    unset. The Batch 22 MusicBrainz check stays owed until a run with
    `ss-postgres` up. The silent skip gets a `logging.info` line in the
    test-infrastructure plan.
  - **Q10 = b:** the UI stays as it is. F-B21-53 becomes no action in Task
    10, and leaves the frontend plan.
  - **Q16 = a:** all the listed rule-outs are approved.
- **What this settles.** Q1 and Q2 confirm Stage 2's Tasks 3-9 as written:
  F-SWE-6 and F-B22-7 join the set.

Next, in order:
1. Part A: the foundation plan's Task 2, by subagent-driven development.
2. This plan's Tasks 1-10.
3. The foundation plan's Tasks 4-10.
4. The three follow-on plans.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Plan of record for reconciling and clearing findings

Side task, no batch tag: planning for Batch 23 WP-0 Parts B and C. It adds
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md` and
points the definition and Section 3 at it. No code changed.

- **Evidence.** Four read-only triage passes checked all 38 IDs in Part C's
  set against `167e650`. Results:
  - six records are already fixed on `main`;
  - several findings are partly fixed (F-B21-3, F-B21-4, F-B21-24,
    F-STYLE-2);
  - three findings share one mechanism (F-DOCSYNC-11, -12, -13);
  - two are one defect (F-B21-18 and F-MAS-2).
  The controller re-ran the load-bearing checks, including the ancestry of
  all seven fix commits.
- **F-B22-7 is wider than filed.** The orchestrator parses Spotify's album
  JSON itself, against global rule 4, and `enrich_albums` has no production
  caller either. `as_cache_row` would also write a Deezer id into
  `spotify_id` if anything called it, and its own tests pin that wrong value.
- **Triage missed one defect.** `loading.js` `showFailure` labels every
  non-Last.fm source "Spotify". F-SWE-5's `internal_error` source would show
  that label, and so would WP-1's export source. Task 7 fixes it and pins it
  in the gate.
- **F-LOAD-1 needs no occupancy counter.** The refusal only appears when
  every slot is full, so a count would always read cap/cap. The fix states
  the configured cap instead.
- **The plan's shape.**
  - Stages 1 and 2 are written in full: records, then the five pipeline
    fixes.
  - Stage 3 records the owner's rulings.
  - The control-plane and frontend clusters get follow-on plans once the
    rulings land.
  - Owner questions Q0-Q16 are batched in the plan, each with a
    recommendation.

Deviation: none. The owner asked for the plan and for a view on F-SWE-6;
that view is in the plan's "Controller's view on F-SWE-6".

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Batch 23 definition: the foundation package widened

Side task, no batch tag: this is a definition amendment, not work-package
work. It follows the owner's rulings of 2026-09-23. It lands after the
worker run-coroutine wrapper plan, all four tasks of which are done
(`ad2d078`..`54ab72b`).

- `BATCH23_DEFINITION.md` WP-0 now has three parts:
  - Part A: the behaviour-neutral extractions, with the loop protocol ticked
    and its deviations recorded.
  - Part B: reconciling what earlier batches left open. This covers six
    findings still marked "pending deploy" after `main` deployed, the
    foundation plan's Tasks 4-10, a Section 3 pruned to the current work
    order, the owed Batch 22 owner checks, and a new docsync finding.
  - Part C: fixing every finding open at P0 or P1 unless the owner rules one
    out. That is 38 IDs, listed in the definition and checked one by one
    against `FINDINGS.md`.
- Owner rulings, each with its reason in the definition:
  - WP-0 logs untagged until one tagged entry closes it, because docsync
    reads a work package as complete on its first tagged heading.
  - Part A keeps strict test parity.
  - Part C may change behaviour, and may edit a test only where its finding
    requires it. The batch acceptance and the intended outcome's "Last.fm
    path is untouched" line are amended to match.
  - F-SWE-5 lands before WP-3.
- Section 3's Next action now describes the widened WP-0 and the logging
  rule. The old line saying WP-0 work logs tagged entries contradicted the
  ruling.
- Plan bookkeeping:
  - The wrapper plan's steps are ticked, and it gains an Outcome section.
  - The foundation plan records that its Tracks 2 and 3 fold into WP-0, and
    its superseded Track 1 logging line is struck through.

Deviation: none from the rulings. Proposal Rule 2 is met, because the owner
added the scope, and Rule 1 is met, because the amendment lands before any
Part B or Part C work. Part C and the uncovered parts of Part B still need a
plan of record.

Forward guidance:
- Part A's three extractions can proceed now under the foundation plan's
  Task 2.
- Before Part C starts, collect every owner-gated question in the set in a
  single batch.
- Raise F-SWE-6 and F-B22-7 with the owner. They are P2, outside the set,
  but under this batch's code.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 4 of 4

Side task, no batch tag: Task 4 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- Documentation only, no code changed. `.claude/SESSION_CONTEXT.md` Section 3's
  `worker.py` structure line now names `run_coroutine_in_new_loop` alongside
  the functions it already listed; Section 4's dependency graph needed no
  change, since `worker.py`'s dependencies are unchanged.
- Both sequence diagrams that described the build-run-close-release
  protocol are now corrected. `docs/architecture/top-albums-sequence.md`
  owned a now-inaccurate claim in two places: its intro paragraph and a
  sequence Note both said the protocol -- event-loop setup inside the
  `try` that `finally` guards -- lived directly in `background_task`. Both
  now say the protocol lives in `worker.run_coroutine_in_new_loop`, which
  `background_task` calls, supplying only the reaction to a failed run.
  `docs/architecture/heatmap-sequence.md` carried the identical stale Note
  for `heatmap_task`; added in review fix round 1 after the first pass
  missed it as a sibling of the top-albums file, it now attributes the
  same `finally` to `worker.run_coroutine_in_new_loop`, called from
  `heatmap_task`, which injects `_report_heatmap_failure` as its
  `on_run_error`. Neither file carries a "Last verified" date to update.
- `docs/architecture/runtime-system.md` was read in full; it does not
  describe the build-run-close-release protocol anywhere (its `worker.py`
  node label and prose stay at the module level), so it needed no edit.
- `AGENT_NOTES.md`'s Windows-asyncio bullet still holds: it names
  `worker.new_thread_event_loop` as the seam every background thread builds
  its loop through, which is still true and unrelated to which function owns
  the run-close-release wrapping, so it was left alone.

Deviations: none from the brief. Review fix round 1 extended the
correction from `top-albums-sequence.md` to its sibling
`heatmap-sequence.md`, which the brief's Files list had not predicted as a
hit but which Step 1/Step 3 cover on their own terms.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 3 of 4

Side task, no batch tag: Task 3 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- `heatmap_task` in `scrobblescope/heatmap.py` now delegates its
  build-run-close-release protocol to `worker.run_coroutine_in_new_loop`,
  added in Task 1, instead of carrying its own `loop = None` / `try` /
  `except Exception` / nested `finally` block. `make_loop` and
  `release_slot` are passed explicitly as `new_thread_event_loop` and
  `release_job_slot` rather than left to the helper's own defaults,
  because the existing tests patch `scrobblescope.heatmap.release_job_slot`
  and `scrobblescope.heatmap.set_job_error`. The failure reaction moved into
  a new named module-private helper, `_report_heatmap_failure(job_id,
  username)`, placed immediately above `heatmap_task`; it keeps the
  `lastfm_unavailable` error code deliberately, since `F-SWE-5` records that
  code as wrong for a fault that is not the user's, and changing it is a
  separate, now one-line, commit. The import at the top of the module gains
  `run_coroutine_in_new_loop` alongside the two names it already carried.
- No test was written or edited: the four existing guard tests in
  `tests/test_heatmap.py::TestHeatmapTask`
  (`test_release_job_slot_called_on_success`,
  `test_release_job_slot_called_on_exception`,
  `test_release_job_slot_called_when_event_loop_setup_raises`,
  `test_release_job_slot_called_when_loop_close_raises`) are the acceptance
  criterion and pass unmodified, including the one that asserts a
  `loop.close()` failure still propagates out of `heatmap_task` while the
  slot is released.
- `background_task` and `heatmap_task` now share exactly one protocol; the
  only remaining difference between the two entry points is the injected
  `on_run_error` (silent logging for the album path, versus logging plus a
  published terminal job error for the heatmap path) -- the remaining half
  of `F-SWE-5`.

Deviations: none from the brief.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 2 of 4

Side task, no batch tag: Task 2 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- `background_task` in `scrobblescope/orchestrator/__init__.py` now
  delegates its build-run-close-release protocol to
  `worker.run_coroutine_in_new_loop`, added in Task 1, instead of carrying
  its own `loop = None` / `try` / `except Exception` / nested `finally`
  block. `make_loop` and `release_slot` are passed explicitly as
  `new_thread_event_loop` and `release_job_slot` rather than left to the
  helper's own defaults, because the existing tests patch
  `scrobblescope.orchestrator.release_job_slot`, and a default taken from
  the helper's module would move that patch target without failing.
  `on_run_error` reproduces the prior log line exactly. The import at the
  top of the module gains `run_coroutine_in_new_loop` alongside the two
  names it already carried.
- No test was written or edited: the four existing guard tests in
  `tests/services/test_orchestrator_fetch_and_process.py`
  (`test_background_task_runs_single_event_loop`,
  `test_background_task_releases_slot_on_exception`,
  `test_background_task_releases_slot_when_event_loop_setup_raises`,
  `test_background_task_releases_slot_when_loop_close_raises`) are the
  acceptance criterion and pass unmodified, including the one that asserts
  a `loop.close()` failure still propagates out of `background_task` while
  the slot is released.

Deviations: none from the brief.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Worker run-coroutine wrapper: Task 1 of 4

Side task, no batch tag: Task 1 of 4 of the worker run-coroutine wrapper
plan, part of Batch 23 WP-0. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands, so the dashboard keeps naming WP-0 as next.

- Added `run_coroutine_in_new_loop(coroutine, *, make_loop=new_thread_event_loop,
  release_slot=release_job_slot, on_run_error=None)` to the end of
  `scrobblescope/worker.py`, after `new_thread_event_loop`. It builds the loop
  inside the `try` so a setup failure still reaches the `finally` that
  releases the concurrency slot; closes a coroutine that never got a loop, so
  a setup failure does not leak an unstarted coroutine; never swallows a
  `loop.close()` failure; and routes a run failure through the caller's
  `on_run_error`, which stays `None`-safe (silent) by default. Tasks 2 and 3
  will point the album and heatmap entry points at it.
- Six unit tests appended to `tests/test_worker.py`, each with an in-function
  import of the helper (matching this repository's existing convention, e.g.
  `tests/test_heatmap.py`), so a pre-implementation run fails once per test
  rather than once per file. Covered: one loop built, run once, closed, and
  the slot released; a run failure reaching a supplied `on_run_error` while
  the loop still closes; a run failure staying silent with no policy given;
  the slot released when loop construction itself fails; the coroutine closed
  when the loop is never built (the regression the old inline code could not
  hit, since it used to build the coroutine and the loop in the same line);
  and a `loop.close()` failure propagating, never routed through
  `on_run_error`, with the slot still released.
- Verified the mutation-kill property directly: with the helper's body
  replaced by `raise NotImplementedError`, all six new tests failed; restored,
  all six passed again.

Deviations: none from the brief. The brief's baseline count (1,717) was
already stale at dispatch; this entry measures and quotes the current count
per controller ruling, and the two other count sites it names.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-21 - Batch 23 opened on feat/batch23-wp0-hygiene

Side task, no batch tag: this entry records the opening itself and is not
WP work, so it does not count as WP-0 being done. Task 3b of the Batch 23
WP-0 foundation plan, done under the owner's instruction that the opening be
explicit rather than silent.

- Section 3 now declares `**Batch 23 is active.**` with its definition and
  its branch, and names WP-0 as next. The Section 2 index gains the Batch 23
  row, SESSION_CONTEXT Section 1 marks Batch 23 active, and the
  `FINDINGS.md` header no longer says no batch is active.
- The definition records the branch, the status and the 2026-09-21 owner
  rulings, and folds job admission into WP-4 with its own acceptance
  clause. WP-0's wrapper bullet names where the wrapper lands.
- The first `--fix` rendered `Current batch: Batch 23.` and
  `Next expected work package: WP-0.`, which confirms the D1 fix on the
  real corpus.

Deviations. The Batch 22 bullet's `Branch:` label was reworded, because
the worktree guard refuses two Branch values in Section 3. Once the batch
was active, the guard compared ancestry and reported WT005 against its
default `origin/main`, which carries merges of `test` the branch does not.
Against `origin/test`, the branch's parent, it exits 0, and the trees of
`e6ce9d7` and `origin/main` are identical. `HANDOFF_PROMPT.md` now carries
that edge case, and its WT004 premise that `main` only squashes or rebases
was corrected against the live rulesets, which allow all three merge
methods. No history was changed.

Live check (throwaway copy of this working tree): a false `WP-3 is next`
went red with DOC007 in Section 3, on the dashboard and in the definition.
The definition leg only went red once its claim was moved onto the
`**Status:**` line itself.

Validation: `pytest -q` -- **1729 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-21 - Docsync renders an opened batch before its first entry

Side task, no batch tag: Task 3 of the Batch 23 WP-0 foundation plan, the
fix for audit defect D1 and its sibling D2, plus O1. Commit made with
`SKIP=doc-state-sync-check`, because it changes `scripts/docsync/`; the
checker was run directly at exit 0 first.

- D1: `_build_status_block` now branches on the batch Section 3 declares,
  not on whether entries exist, and `_computed_next_wp` no longer returns
  nothing for an empty current-batch block. An opened batch with nothing
  logged renders as that batch, and a false next-package claim raises
  DOC007. The between-batches block now carries the count line too.
- D2: under a finite plan, WP-0 is a real package (owner ruling), so a
  plan with nothing done names WP-0. The no-plan rule is unchanged.
- O1: DOC012 names an entry whose `pytest -q` and bold count are not
  directly paired, since the authority skips it. The pattern is shared
  as `logic.FULL_SUITE_RESULT_RE`. The pairing is bounded at 80
  characters so prose citing another entry's count is not a claim.
  `AGENTS.md` now states the one readable form and both plans point there.

Deviation: two lines of the shared CLI fixture in
`tests/test_docsync_cli.py` wrote the colon form, which the authority read
only through its legacy fallback; they now use the canonical form. No
other existing test changed. 44 archived entries use an unpaired form;
DOC012 reads only live entries, so they are left as written.

Live probe (throwaway corpus from HEAD plus the changed modules):

| Probe | Expected | Observed |
| --- | --- | --- |
| opened batch, no entries: block | Batch 23, WP-0 next | Batch 23, WP-0 next |
| opened batch, Section 3 claims WP-3 | DOC007 | exit 1, DOC007 |
| opened batch, dashboard claims WP-3 | DOC007 | exit 1, DOC007 |
| `pytest -q` (qualifier) -- bold count | DOC012 | exit 1, DOC012 |
| `pytest -q`: bold count | DOC012 | exit 1, DOC012 |
| opened batch, true "WP-0 is next" | green | exit 0 |
| real corpus between batches | green, count shown | exit 0, count shown |
| targeted `pytest -q tests/...` run | no DOC012 | no DOC012 |
| prose citing another entry's count | no DOC012 | no DOC012 |
| canonical form | no DOC012 | no DOC012 |

The original 18 planted-defect probes were re-run on the changed code:
18 of 18 red.

Validation: `pytest -q` -- **1729 passed**, 12 of them new; the untracked
mutation-runner tests were excluded, since they are not repository state.

### 2026-09-21 - Batch 23 WP-0 foundation plan committed

Side task, no batch tag. Scope: commit
`docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`, which
replaces an earlier draft that put 22 tasks and two behaviour changes under
WP-0. WP-0 keeps its definition's scope: the loop-protocol plan plus the
three original extractions. Control-plane fixes run as side tasks, led by
the fix for audit defect D1, which must land before the batch opens.
F-SWE-5 follows WP-0 as its own commit. Every change to a check is
accepted only on a live probe: red on the planted defect, green on its
near miss.

Owner rulings, 2026-09-21, recorded in the plan: Batch 23's branch is
`feat/batch23-wp0-hygiene`, opened by the plan's Task 3b after the D1 fix;
no worker-count guard (delegated, declined: the Dockerfile pins one worker
and a partial guard is its own wrong green); WP-0 counts as "next" under a
finite plan; job admission is folded into Batch 23 WP-4. Section 3 is
deliberately unchanged here: opening the batch before the D1 fix would
produce the defect's state.

Validation: `pytest -q` -- **1717 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-21 - Docsync live-probe audit recorded

Side task, no batch tag. Scope: record the formal conclusion of the live
probe run earlier today as
`docs/history/reports/DOCSYNC_LIVE_PROBE_AUDIT_2026-09-21.md`. No code
changed.

Verdict: conditionally fit. All 21 implemented codes fired on their own
planted defect (26 of 26 red probes), all 8 near-miss controls stayed
green, and `--fix`, the exit codes and the preflight behaved as documented.
Blocking defect D1: a batch declared open with no logged work package reads
as "between batches" and DOC007 is silent on a false next-package claim; it
must be fixed before Batch 23 opens. D2: WP-0 is never "next" under a finite
plan; the owner ruled that it counts. The report states what was not probed.

Validation: `pytest -q` -- **1717 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-21 - Worker loop-protocol plan committed; docsync probed live

Side task, no batch tag. Scope: commit the plan of record for Batch 23
WP-0's loop-protocol extraction,
`docs/superpowers/plans/2026-09-21-worker-run-coroutine-wrapper.md`, and
verify the docsync gate by live probe rather than by its unit tests.

The plan was checked against source before committing and four statements
were corrected: `tests/test_worker.py` has nine existing tests, not four;
its in-function imports make six failures, not six errors; the untracked
set is larger than the eight paths it named; and its commit blocks now run
`--fix` before pytest and pre-commit, as "Commit Rules" orders. Its code,
tests and parity argument are unchanged. The expanded WP-0 foundation plan
was rewritten in the working tree and is deliberately not in this commit.

Live probe: a throwaway corpus built from `git archive HEAD` plus a scratch
`git init`, with one planted defect per code, run through the real CLI.
Every implemented code (DOC001-DOC020, DOC023) went red on its own defect
and raised only that code; six near misses (struck-through or fenced
retired claims, a fenced missing path, `Status: not closed.`, a canonical
resolved finding, a valid citation) stayed green. `--fix` repaired a
tampered managed block and rotated a resolved finding, and refused to write
a rotting finding's record or a hand-authored count. The preflight returned
3 on a staged `scripts/docsync/` edit, 0 on an ordinary one, and passed the
checker's 1 through.

One defect found: in a batch Section 3 declares active but with no tagged
Section 4 entry yet, the status block renders "none (between batches)" and
DOC007 is silent on a false next-work-package claim. Both are correct once
one entry exists. That is the state Batch 23 enters when its branch is
named, so the fix is scheduled to land first; it is not yet filed in
`FINDINGS.md`.

Validation: `pytest -q` -- **1717 passed**, across 66 tracked test modules;
the untracked mutation-runner tests were excluded, since they are not
repository state. The dashboard and the findings header are updated from
1555 across 58 to match.

### 2026-09-21 - Frontend gate split complete (F-B21-51)

Side task, no batch tag. Task 11 closes out the split: `frontend_gate.py`
measures 535 lines, under the plan's 700-line threshold and above its
roughly-450 estimate. The ten `_frontend_gate_*` siblings measure
`_frontend_gate_assets` 49, `_frontend_gate_colour` 191,
`_frontend_gate_forms` 434, `_frontend_gate_layout` 1,176,
`_frontend_gate_pipeline` 854, `_frontend_gate_results` 497,
`_frontend_gate_runtime` 156, `_frontend_gate_shared` 71,
`_frontend_gate_theme` 749, `_frontend_gate_unmatched` 490. The gate
summary is unchanged: `[frontend_gate] 30 checks passed in 52 runs across
chromium, firefox`. F-B21-51 is resolved; `docs/architecture/
documentation-tooling.md`, `DEVELOPMENT.md`, `FINDINGS.md` and this file
are reconciled to the measured end state. The `frontend_gate_checks.toml`
registry stays a deferred candidate.

### 2026-09-21 - Frontend gate split: runtime slice (F-B21-51)

Side task, no batch tag, last of the split. `_frontend_gate_runtime.py` now
owns `SETUP_COMMAND`, `install_cdn_routes`, `_SERVE_APP_LOCK`,
`FrontendGateError`, `_load_playwright`, `_launch_browser` and `serve_app`,
moved verbatim with the `app`, `werkzeug.serving` and
`scrobblescope.repositories` imports they need. The facade no longer imports
`create_app`, `make_server` or the repository job functions directly; it
re-exports the six public names through the new sibling instead.
`REPO_ROOT`, the `sys.path` insert, `GATE_SECRET_KEY` and the environment
bootstrap stay in the facade, above every sibling import, because
`scrobblescope.config` reads the provider keys once at first import and the
gate boots in CI's production mode with no secrets set. The facade's
bootstrap comment now says so explicitly.

Seven tests moved out of `test_frontend_gate.py` into
`test_frontend_gate_runtime.py`, retargeting their `make_server` and
`create_app` patches to `_frontend_gate_runtime`, and their
`frontend_gate.install_cdn_routes` attribute calls to
`_frontend_gate_runtime.install_cdn_routes`. `test_headed_reaches_the_browser_launch`,
`test_launch_is_headless_by_default` and the tests that call `main(` or
`run_checks(` stayed in `test_frontend_gate.py`, unchanged, because they
reach `_launch_browser` and `serve_app` through the facade's re-export or
`patch.object(frontend_gate, ...)`, which still resolves.

Removing the facade's `create_job`/`delete_job` import broke two tests in
`test_frontend_gate_pipeline.py` (an earlier slice) that called
`frontend_gate.create_job`/`frontend_gate.delete_job` by attribute access --
a name the facade no longer defines. `_frontend_gate_pipeline` already
imports both from `scrobblescope.repositories` for its own checks, so those
four call sites were retargeted to `_frontend_gate_pipeline.create_job`/
`_frontend_gate_pipeline.delete_job` rather than restoring the facade
import.

### 2026-09-21 - Frontend gate split: pipeline slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_pipeline.py` now owns the three
checks that write real job state through `scrobblescope.repositories` and
watch the page follow it -- `check_loading_composition`,
`check_pipeline_state_machines`, `check_artist_spotlight_rotation` -- plus
their nine helpers (`_parse_matrix_scalex`, `_assert_loading_progress_state`,
`_exercise_loading_progress_phases`, `_check_phase_repository_isolation`,
`_exercise_counted_progress`, `_exercise_album_progress`,
`_exercise_heatmap_progress`, `_exercise_replaced_job_progress`,
`_exercise_pipeline_state_machines`) and the ten progress constants
(`ALBUM_PROGRESS_TRACK`, `ALBUM_PROGRESS_BAR`, `ALBUM_PROGRESS_TEXT`,
`HEATMAP_PROGRESS_TRACK`, `HEATMAP_PROGRESS_BAR`, `HEATMAP_PROGRESS_TEXT`,
`FETCHING_SCROBBLES`, `COUNTING_SCROBBLES`, `PAGE_23_OF_102`,
`PAGE_90_OF_100`), moved verbatim. `serve_app` stays behind in the facade, so
the facade keeps `create_job`, `delete_job` and `set_job_progress`; the other
six repository imports (`get_job_context`, `get_job_progress`,
`reset_job_state`, `set_job_error`, `set_job_results`, `set_job_stat`) moved
with the code that reads them.

Six tests moved out of `test_frontend_gate.py`, retargeting their patches of
`reset_job_state`, `set_job_progress`, `create_job`, `delete_job`,
`get_job_progress` and `get_job_context`, and of
`_exercise_pipeline_state_machines`, to `_frontend_gate_pipeline`. Two moved
tests also called `_check_phase_repository_isolation`,
`_exercise_replaced_job_progress`, `_exercise_counted_progress` and
`get_job_progress` through `frontend_gate.<name>` attribute access -- names
the facade no longer defines -- and were retargeted the same way.
`serve_app`'s own tests kept patching `frontend_gate.create_job`,
`frontend_gate.set_job_progress` and `frontend_gate.delete_job`, since those
three still resolve there.

### 2026-09-21 - Frontend gate split: layout slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_layout.py` now owns the six checks
that measure fonts, text scaling, touch targets and large-display
composition -- `check_touch_targets`, `check_fonts`, `check_body_font`,
`check_shell_scales_with_text`, `check_large_display_scale_parity`,
`check_destination_empty_states` -- plus their eighteen measurement and
judgement helpers and the `FONTS_READY_EXPRESSION`, `REQUIRED_FONT_FAMILIES`,
`MIN_TOUCH_TARGET_PX`, `INTERACTIVE_SELECTOR`, `TOUCH_TARGET_STATES` and
`DEFAULT_STATES` constants, moved verbatim and importing `_clamp_px` from the
colour slice and the page inventories and `_reach_state` from the shared
module. It is the largest slice at roughly 1,150 lines; the split isolates it
rather than shrinking it, and `check_large_display_scale_parity`'s own
complexity is a separate question. The definitions were not contiguous in the
facade: `check_loading_composition` stayed behind between
`check_shell_scales_with_text` and the scale-parity measurement helpers.

Sixteen tests and the `_healthy_mobile_header` helper moved out of
`test_frontend_gate.py`. Several of the moved tests called private helpers
through `frontend_gate._mobile_header_failures`, `frontend_gate.
_expected_scaled_dimension`, `frontend_gate._scale_dimension_failures`,
`frontend_gate._wide_layout_failures`, `frontend_gate._header_geometry_failures`,
`frontend_gate._scale_mechanism_failures`, `frontend_gate._measure_enlarged_root`
and `frontend_gate._composition_bounds_failures` -- private names the facade
never re-exports, so those references were retargeted to
`_frontend_gate_layout` alongside the patch-target guard's own findings.
`test_the_touch_profiles_really_carry_a_coarse_pointer` stayed in
`test_frontend_gate.py`: it tests `VIEWPORTS`, which remains in the facade.

### 2026-09-21 - Frontend gate split: theme slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_theme.py` now owns the nine checks
that read computed theme values -- `check_divider_contrast`,
`check_theme_tokens`, `check_index_design_tokens`, `check_theme_persistence`,
`check_index_entrance_motion`, `check_mark_follows_theme`,
`check_theme_survives_blocked_storage`, `check_heatmap_zero_cells_follow_theme`,
`check_heatmap_export_header_matches_page` -- plus their private helper
`_computed_colour`, the `_BLOCK_STORAGE` init script, and the
`THEME_EXPRESSION`, `SET_THEME_EXPRESSION` and `FORBIDDEN_SURFACES`
constants, moved verbatim and importing the divider-contrast helpers from
the colour slice and the page inventories from the shared module. The
definitions were not contiguous in the facade; `check_touch_targets`,
`_small_targets`, `check_fonts`, `check_body_font`,
`check_shell_scales_with_text` and `check_loading_composition` stayed behind
between them.

This is the first slice to move existing tests rather than write new ones
against moved code alone: `test_blocked_storage_probe_closes_context_when_page_creation_fails`
and `test_theme_persistence_check_restores_the_saved_preference` moved out of
`test_frontend_gate.py`. The persistence test's `MIGRATED_PAGES` patch is an
instance of trap 2 (constraints.md): it targeted
`scripts.dev.frontend_gate.MIGRATED_PAGES`, which rebinds the facade's name,
not the theme module's own `from ... import MIGRATED_PAGES` binding that
`check_theme_persistence` actually reads. Pointing the patch back at the
facade to check whether the retarget is load-bearing showed the test still
passes: the mocked page is not path-aware, so the check silently runs
against the real `MIGRATED_PAGES` tuple instead of `("/",)` and reports no
failures either way. The retarget to `scripts.dev._frontend_gate_theme.MIGRATED_PAGES`
is still correct -- it is what makes the test actually exercise a single
page the way its docstring describes -- but it is not what makes the test
fail if omitted; the patch-target guard is what would have caught the
mis-target here, not this test's own assertions.

A mutation probe returning `["mutation probe"]` first in
`check_mark_follows_theme` produced the expected
`FAIL chromium: mark follows theme [desktop]: mutation probe` and the
matching `[firefox]` line, because that check is in the static-assets
canary group that runs on both browsers, then was reverted. The gate's
summary line is unchanged at 30 checks across both browsers.

### 2026-09-21 - Frontend gate split: forms slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_forms.py` now owns the index form's
seven checks -- `check_validation_feedback`, `check_private_profile_is_blocked`,
`check_validator_outage_is_recoverable`, `check_stale_validator_failure_is_discarded`,
`check_current_validator_failure_replaces_old_verdict`,
`check_true_warning_survives`, `check_initial_visibility` -- plus their
private helpers `_collecting_handler` and `_year_warning`, and the
`HIDDEN_ON_LOAD` constant, moved verbatim and importing `_reach_state` from
the shared module. The definitions were not contiguous in the facade;
`check_index_entrance_motion`, `check_mark_follows_theme` and
`check_theme_survives_blocked_storage` stayed behind between them.
`_collecting_handler` gains the regression test its docstring describes: a
one-parameter handler so Playwright cannot overwrite its sink with the
request object, and that two handlers do not share one. A mutation probe
that added `"#year"` to `HIDDEN_ON_LOAD`'s `"/"` tuple produced the expected
`FAIL chromium: initial visibility [desktop]: /: #year should start hidden
but computes display: block` line (and the matching `[mobile]` line), then
was reverted. The gate's summary line is unchanged at 30 checks across both
browsers.

### 2026-09-21 - Frontend gate split: unmatched slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_unmatched.py` now owns the largest
single check, `check_unmatched_report` (422 lines), its breakpoint sweep
`_unmatched_panel_width_sweep`, and their constants
(`UNMATCHED_TWO_PANEL_MIN`, `UNMATCHED_SWEEP_WIDTHS`,
`UNMATCHED_MIN_TITLE_WIDTH`), moved verbatim and importing
`add_job_unmatched`, `create_job` and `delete_job` from
`scrobblescope.repositories`. The sweep gains its first unit tests: that it
reports a wrong column count and a starved album title at each swept width,
and that it restores the viewport through its `finally` block both on a
normal return and when a page measurement raises. A mutation probe that
widened `UNMATCHED_MIN_TITLE_WIDTH` to 960 produced the expected FAIL lines
on chromium at all three profiles. The gate's summary line is unchanged at
30 checks across both browsers.

### 2026-09-21 - Frontend gate split: assets slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_assets.py` now owns stylesheet
isolation: `BOOTSTRAP_MARKER`, `TAILWIND_MARKER`, `_stylesheet_hrefs` and
`check_stylesheet_isolation`, moved verbatim and importing `ALL_PAGES` from
the shared module. This is the first browser-coupled slice, so it sets the
pattern the rest of the split follows: move verbatim, re-export through the
facade, and prove the gate still reaches the moved code. A mutation probe in
`check_stylesheet_isolation` produced the expected FAIL on both chromium and
firefox, confirming the Firefox canary group also reaches the moved module.
The gate's summary line is unchanged at 30 checks across both browsers.

### 2026-09-21 - Frontend gate split: shared slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_shared.py` now owns the page
inventories (`MIGRATED_PAGES`, `LEGACY_PAGES`, `ALL_PAGES`,
`ERROR_PAGE_PATH`), `GATE_JOB_IDS` and `_reach_state`, moved verbatim so every
later slice can import them without importing the facade that imports them.
`serve_app` still lives in the facade but now mutates the shared module's
`MIGRATED_PAGES`, `ALL_PAGES` and `GATE_JOB_IDS` in place through a `from ...
import` binding, never rebinding them; a new parity test pins that every
module holding one of those names holds the same object. A mutation probe in
`_reach_state` produced the expected FAIL on both the touch-target and
form-validation checks, confirming both reach the shared code through the
facade's re-export.

### 2026-09-21 - Frontend gate: dead code removed before the split (F-B21-51)

Side task, no batch tag. `_computed_shadow` had no caller anywhere and is
deleted rather than moved. The cdnjs Bootstrap fixture is removed: no template
requests Bootstrap, and the isolation check reads hrefs, so it still catches a
regression; `install_cdn_routes` keeps only the Impeccable Live overlay abort.
Eight colour tests moved verbatim into the colour test file.

### 2026-09-21 - Frontend gate split: invariants pinned first (F-B21-51)

Side task, no batch tag, owner-approved 2026-09-21. F-B21-51 is rescoped from
a batch work package to a side task with a written plan, and amended: a shared
module is added and the TOML registry is deferred. Before any code moves,
`tests/scripts/dev/test_frontend_gate_split.py` pins three invariants that
would otherwise fail silently: every defined check is registered, every test
patch targets a module that reads the name, and the facade's environment
bootstrap precedes any `scrobblescope` import. Each guard was shown to fail on
a deliberate defect before being kept.

### 2026-09-21 - No `assert` guards runtime code any more (F-B22-2)

Side task, no batch tag. Preparation for closing PR #235's review threads,
which the owner named as the next step: two of its Codacy threads (HIGH
RISK) are this finding, and the honest reply is the fix, not a pointer.
Control-plane change (`scripts/docsync/findings.py`), committed with
`SKIP=doc-state-sync-check` and `doc_state_sync.py --check` run directly.

**Plan vs implementation.** The finding's fix shape was a conditional raise
at each of six sites. Applied as written, three of those raises could never
fire, so each invariant was placed where it actually holds instead:

- **`routes/album_flow.py`, three `assert job_context is not None`:
  deleted.** `_get_validated_job_context` returns an error before it can
  return a missing context, so they only narrowed types. Three copies of an
  unreachable raise is dead code, and Rule 3 says the third copy is where
  the invariant belongs in one place -- which it already is.
- **`scripts/docsync/findings.py` `_build`: invariant by construction.**
  `_parse` already has each heading's match; it now passes it in instead of
  `_build` re-matching `block[0]` and asserting.
- **`spotify.py` token fetch: a behaviour change, deliberately.** Missing or
  empty credentials now log and return None, which is the function's
  existing failure answer, so the album pipeline falls back to Deezer and
  the spotlight keeps its artwork. The `assert` raised past that fallback
  and failed the whole job; an empty string also slipped past `is not None`.
  The old test expected `AssertionError`; it is replaced by three cases
  (id missing, secret missing, id empty) asserting None, no HTTP call and
  an error log. Red before the change.

**The gate.** Ruff `S101` is selected, with `tests/**` exempt (all 2,630
current hits are there). Proven red on a probe file. Production code now
holds zero `assert` statements, and the affected suites pass under
`python -O`.

**Validation:** `pytest -q` -- **1555 passed**. `pre-commit run --all-files`
with `SKIP=doc-state-sync-check` -- every other hook passes.
`doc_state_sync.py --check` run directly -- exit 0.

**Forward guidance:** PR #235's threads can now be answered with fixes for
every true claim. The fixes live on this branch, so they reach `main` in the
follow-up PR the owner plans after #235 merges.

### 2026-09-21 - DOC023 reads a legacy "Status: closed" as a claim

Side task, no batch tag, owner-approved on 2026-09-21 with one condition:
it must not start flagging findings that merely mention a closed batch, work
package or PR. Control-plane change, committed with the documented escape
`SKIP=doc-state-sync-check` and `doc_state_sync.py --check` run by hand on
the final tree.

**Why.** F-B21-13's prose said "Status: closed." for four weeks while the
finding sat active. DOC023 recognises only `resolved` and `no action`, the
rotation vocabulary, so the word the author actually used was invisible to
it. That is the one real pattern miss the morning's findings pass found.

**Plan vs implementation.** Measured before designing: matching "closed" on
any body line fired on two findings, one of them F-B21-25, whose status is
"partly closed" -- a false positive even on the status line. So the rule is
narrow: `_LEGACY_CLOSED_STATUS_RE` in `scripts/docsync/findings.py` matches a
capitalised `Status` label (plain, bold, or after a sentence ends) whose value
*opens* with "closed". Rotation vocabulary is unchanged: "closed" is a way to
detect the claim, not an outcome a record may state, so the remedy is still a
`resolved` record. `docs/architecture/documentation-tooling.md` records the
rule beside DOC023.

**Tests.** Ten in `tests/test_docsync_findings.py`. Four claim shapes, red
before the pattern existed. Six non-claims, which pass before and after:
"partly closed", "not closed", "closes at", and "closed" in ordinary prose
about a batch, a work package and a PR. On the live corpus the check stays
clean: F-B21-25 is not flagged.

**Validation:** `pytest -q` -- **1553 passed**. `pre-commit run --all-files`
with `SKIP=doc-state-sync-check` -- every other hook passes.
`doc_state_sync.py --check` run directly -- exit 0.

**Forward guidance:** other pre-lifecycle spellings ("fixed", "done") were
measured and left out: on status lines they appeared only qualified ("the
scope itself is fixed", "closes at WP-8"). Add one only with a measured
instance, the same way.

### 2026-09-21 - Broad catches judged one by one, then gated (F-MAS-4)

Side task, no batch tag, owner-approved on 2026-09-21 because the count only
grows: F-MAS-4 recorded 14, then 17; it was 25.

**Plan vs implementation.** The finding offered "narrow or add structured
logging". Narrowing all 25 was rejected after reading them: most guard the
optional DB cache or decorative enrichment, where fail-open is the
documented design (`docs/agents/global-rules.md` Rule 6), and swapping
`Exception` for guessed asyncpg or aiohttp types would turn a failure the job
tolerates today into a crashed job. So each site was judged, and the growth
was made impossible to miss instead:

- **Narrowed (1):** `lastfm.py`'s JSON guard, to `aiohttp.ContentTypeError`
  and `ValueError`. It wrapped the cache write too and labelled *every*
  failure "Invalid JSON". Anything else now reaches `retry_with_semaphore`,
  which retries it exactly as before. Tests first: two pin the parse
  failures that must stay handled, and one red test showed a non-parse
  error being misreported.
- **Logged with a traceback (12):** eleven already re-raised or called
  `logging.exception`; `run_async_in_thread` hand-built the same output with
  `traceback.format_exc()` and now calls `logging.exception`.
- **Justified (12):** the DB-cache, correction-cache, close-in-finally and
  optional-enrichment catches each carry a one-line reason above the
  `except` and `# noqa: BLE001`. The three degradation warnings and the
  retry helper now log the exception's class, which they omitted, so a
  programming error cannot pass for a network blip.
- **The gate:** Ruff's `BLE` rules are on in `pyproject.toml`. A handler
  catching bare `Exception` must re-raise, log a traceback, or say why.
  Proven red with a probe file. The five hits outside `scrobblescope/`
  (`init_db.py`, two scripts, two thread-collecting tests) are deliberate
  report-everything boundaries and carry reasons too.

**Deviation: one stale docstring.** `run_async_in_thread` said it was "used
only by `/validate_user`"; it also serves both start routes' Last.fm checks
and `/api/artist_spotlight`. Corrected while the function was open.

**Validation:** `pytest -q` -- **1543 passed**. `pre-commit run --all-files` --
all hooks pass, including the new rule. `doc_state_sync.py --check` exit 0.

**Forward guidance:** a new broad catch now needs a reason in the diff, which
is where a reviewer can disagree with it. `docs/SWE_AUDIT_CHARTER.md` notes
that F-MAS-4 counted catches without judging them; this pass judged them.

### 2026-09-21 - Production refuses to start without its API keys (F-SWE-4)

Side task, no batch tag, owner-approved on 2026-09-21. F-SWE-4: production
starts through `gunicorn app:app`, which imports `app.py` and never runs its
`__main__` block, so `ensure_api_keys()` there never fired. A deployment
missing a key served pages and reported every search as an upstream outage.

**Plan vs implementation.** The finding called it one line. It was not: an
unconditional call in `create_app()` makes every environment without the
keys fail at import, and three do -- the test suite and the frontend gate both
import `app`, and CI's repository secrets arrive empty when unavailable. A
simulated secret-less CI run confirmed it (whole suite fails at collection).
So the fix follows the precedent beside it: `_validate_api_keys` mirrors
`_validate_secret_key` (refuse in production, warn in dev mode) and is called
from `create_app()`, and `tests/conftest.py` and `scripts/dev/frontend_gate.py`
supply placeholder keys exactly as they already supply `SECRET_KEY`. The
`__main__` checks in `app.py` and `run.py` stay: they fail fast for a local
run, which dev mode would otherwise only warn about.

**Tests.** Four in `tests/test_app_factory.py`, red before the helper existed:
production refuses, dev warns, a complete set passes, and `create_app()`
itself refuses -- the regression the finding describes. The full suite passes
normally and again with `DEBUG_MODE=0` and every key plus `SECRET_KEY`
empty, which is CI without secrets.

**Deviation: two siblings of the previous commit, found here.** The
`runtime-system.md` prose listed `config.py`'s importers by line number, and
the event-loop commit had shifted three of them (`worker.py`,
`release_checks.py`, `orchestrator/__init__.py`). Rewritten to name modules
rather than lines, recomputed with an `ast` walk -- still ten nodes -- per
AGENTS.md anti-pattern 11's rule to cite by name. README's `worker.py` row
also still read as though the module held only the semaphore; it now names
the event loop. F-B22-2 gained a note: the `spotify.py` asserts are now
reachable only in dev mode.

**Validation:** `pytest -q` -- **1540 passed**. `pre-commit run --all-files` --
all hooks pass. `doc_state_sync.py --check` exit 0. Frontend gate passed.

**Forward guidance:** F-B22-2 still wants its six `assert`s replaced; the
startup check narrows one pair, it does not fix them.

### 2026-09-21 - One event-loop helper for every background thread (F-B20-2)

Side task, no batch tag, owner-approved on 2026-09-21 on condition that it
is non-breaking. F-B20-2 asked for the orchestrator split, which Batch 22
WP-0 delivered, and for shared event-loop setup. That setup had since
reached a third copy -- `orchestrator.background_task`, `heatmap.heatmap_task`
and `release_checks._worker_loop` each built a `ProactorEventLoop` on Windows
and a default loop elsewhere -- which is the point `docs/agents/global-rules.md`
Rule 3 says to extract.

**Plan vs implementation.** New `worker.new_thread_event_loop()` creates the
loop, installs it, and returns it; the three call sites now call it. It
lives in `worker.py` because that module already owns background-thread
execution and both job modules import it; `utils.py` was rejected, since
F-SWE-7 records it as already holding five unrelated concerns. The one new
import edge, `release_checks -> worker`, is drawn in
`docs/architecture/runtime-system.md` (re-verified against the `ast` import
graph: no missing or extra edge) and listed in SESSION_CONTEXT Section 4.

**The behaviour worth preserving, and how it was kept.** Before, a failure in
`asyncio.set_event_loop` still closed the loop, because the loop was
assigned before the call and the caller's `finally` closed it. The helper
cannot return a loop it failed to install, so it closes the loop itself
before re-raising. Test-first: three new tests in `tests/test_worker.py`
(default loop off Windows, Proactor on Windows, close-on-install-failure),
red before the helper existed. The existing slot-release parity tests for
both job entry points -- crash, loop-setup failure, loop-close failure --
pass unmodified, as does the whole suite.

**Only part of F-B20-2's list was extracted, deliberately.** Progress mapping
and error guards have two occurrences, album and heatmap, so Rule 3 says
leave them. F-B20-2 is resolved with that reasoning written into it.

**Deviation: Batch 23's definition and plan were amended by one clause.**
`BATCH23_DEFINITION.md` WP-0 plans `_run_coroutine_in_new_loop`, described
as "the Proactor boilerplate". The Proactor choice is now shared, so both
documents describe that item as the run-and-close wrapper built on
`worker.new_thread_event_loop`. Scope is unchanged; the owner should know the
approved definition moved. `AGENT_NOTES.md` and SESSION_CONTEXT Section 7
each restated the Proactor rationale; both now point at the helper's
docstring, which owns it.

**Validation:** `pytest -q` -- **1536 passed**. `pre-commit run --all-files` --
all hooks pass. `doc_state_sync.py --check` exit 0. `ruff check` clean.

**Forward guidance:** F-SWE-7 (`utils.py`) is the sibling split, and wants a
work package of its own. Batch 23 WP-0's export wrapper should call
`new_thread_event_loop` rather than add a fourth platform branch.

### 2026-09-21 - Between-batch verification: findings, MusicBrainz policy, one diagram

Side task, no batch tag. The owner is using the gap before Batch 23 to close
findings and verify earlier agent work against its sources. Scope was three
checks and the fixes they produced.

**Six findings rotated that had been finished for weeks or months.** None
carried a lifecycle record, so rotation could not see them, and DOC023 could
not flag them because their prose still said "open" or "in progress" -- stale
text rather than a missed pattern. Each was verified against git and source
before its box was checked, with the landing date as its completion date:
F-DOCSYNC-1 (`fd39c89`, 2026-02-26 -- seven months), F-B21-8 (`20dfe0d`),
F-B21-13 (`8ed1650`), F-B21-12 (`c7bfaec`), F-B20-4 (`9152fd3`), and F-B21-50
as no action by owner ruling. F-B21-13 is the one real pattern miss: its
prose said "closed", a word DOC023 does not read.

**F-B20-3 gained its record but stays active.** Bootstrap is gone on this
branch (`85e7511`), but `origin/main` is what Fly.io deploys and still loads
it, so it reads "resolved locally, pending deploy" like the five Batch 21
findings in the same state (F-B21-10, -26, -27, -28, -29). DOC014 is right
to hold all six until `main` advances; they are not stuck.

**F-STYLE-2 narrowed, and `.flake8` deleted.** Ruff (`c7bfaec`) settled the
line length at 88; the orphaned `.flake8` still claimed 120 and nothing read
it. What remains open is only the docstring convention.

**MusicBrainz: the code is right and its stated reason was wrong.** Checked
against the upstream API and rate-limiting pages, including the raw wiki
text. `client=` is required only on POST (data submission); this app sends
GET searches, so omitting it is correct. The User-Agent format, the 1 req/s
per IP limit, the 503 on throttling, `fmt=json`, and the `releasegroup` and
`artist` search fields all match. But the code, its docs and its tests said
MusicBrainz "blocks
anonymous clients outright" and that a contact-less request "would only
guarantee a rejected request". Upstream, "anonymous" is a named list of
library defaults (blank, `Java`, `Python-urllib`, ...) that share a throttled
pool; the contact is a policy requirement, and breaking it risks throttling
or a block. The design -- stay disabled without a contact -- is unchanged;
the reason is corrected in `musicbrainz.py`, `release_checks.py`,
`config.py`, `.env.example`, `DEPLOY.md`, `README.md` and four test
docstrings, which also now say an email or a URL is accepted. The Batch 22
plan keeps its wording as a historical record.

**Architecture diagrams, verified mechanically.** `runtime-system.md` was
compared with the module import graph extracted by `ast`: no missing edge, no
extra edge, the three deferred imports drawn dotted, and all ten `config.py`
importers at their cited lines. `heatmap-sequence.md` matches `heatmap_task`
and `/heatmap_data`. `top-albums-sequence.md` had one false paragraph: it said
`background_task`'s `finally` "is not reached if the event-loop setup above it
fails". The setup is inside the `try`, so the release is unconditional -- and
the diagram's own note near its end already said so. Rewritten.

**Deviation: a real test-isolation defect, surfaced by configuring the
contact.** The first full run after the owner set `MUSICBRAINZ_CONTACT` failed
`test_enqueue_release_check_queues_jobs_in_order` intermittently. A probe
plugin showed why: `app.py` loads the developer's `.env`, so every unpatched
happy-path pipeline test now enqueued its job and started the **real**
`release-checks` thread (the first was a test in
`tests/services/test_orchestrator_fetch_and_process.py`), which drained the
shared queue the order test reads and
could reach musicbrainz.org and the local Postgres. No real call went out in
the probed run; nothing stopped one either. CI never saw it because it has no
`.env`. Fixed in `tests/conftest.py` beside the existing `SECRET_KEY` guard:
`MUSICBRAINZ_CONTACT` is forced empty before `app` is imported, which
`load_dotenv` will not override. Re-probed: no worker, no queue residue, no
MusicBrainz attempt. Regression test
`test_session_starts_with_no_musicbrainz_contact` fails with that line removed
on a machine that has a contact configured -- which is the only machine the
defect exists on. Otherwise no runtime behaviour changed; the one string a
test matches (`MUSICBRAINZ_CONTACT`) is still in the error message.

**Validation:** `pytest -q` -- **1533 passed**. `pre-commit run --all-files` --
all hooks pass. `doc_state_sync.py --check` exit 0. Frontend gate: 30 checks
passed in 52 runs across chromium and firefox.

**Forward guidance:** the owner approved four follow-ups in the same session,
each its own commit: the shared event-loop runner F-B20-2 now warrants, the
startup key check F-SWE-4 describes, the F-MAS-4 broad-catch remediation, and
DOC023 reading a legacy status line that opens with "closed".

### 2026-09-20 - Working tree reconciled for the deferred audit

Side task, no batch tag. The SWE audit's charter requires a clean worktree
before grading -- "a SHA cannot reproduce uncommitted content, so a matrix
built over a dirty tree is unfalsifiable however carefully its cells cite
lines" -- and the tree had two modified tracked files and sixteen untracked
paths. Reconciled, one class at a time, and three of the classes turned out to
be defects rather than clutter.

**The graphify refresh tooling is now adopted, and it was broken as written.**
`AGENT_NOTES.md` carries a new section describing a threshold-gated local graph
refresh: two `.githooks` scripts calling `scripts/dev/graphify_refresh.py`,
which rebuilds only after 5 commits or 25 changed files have accumulated. Its
tests pass (20) and it is standard-library only, as its own comment explains
(hooks do not inherit an activated virtualenv). But the section also states the
hook files "must keep LF endings: a CRLF `post-commit` fails under Git for
Windows' `sh`", and **both hook files were CRLF on disk**. `.gitattributes`
had rules for two CSS files and `docs/design/**`, nothing for `.githooks/`.
Committing them as they stood would have shipped a hook that fails for any
clone whose `core.autocrlf` rewrites it, while the document beside it promised
otherwise. Fixed at the root rather than the instance: a `.githooks/* text
eol=lf` rule, so the working copy is correct whatever a clone's autocrlf is,
plus a conversion of both files to LF. This is the same shape as F-B21-61 --
a written claim that nothing enforced.

**And a second half of the same defect, found after the first commit.** Both
hooks were staged as mode `100644`, not `100755`. Git does not run a hook file
that is not executable -- on Linux and macOS it reports "ignored because it's
not set as executable" and continues -- so the feature would have worked on
this Windows checkout, where the exec bit is meaningless, and silently done
nothing on Linux or in CI. `core.fileMode` is `false` in this clone, which is
exactly why git recorded 100644 and could not report the difference. Fixed with
`git update-index --chmod=+x`, which writes the mode into the index directly
rather than relying on a filesystem bit Windows does not have. Both files keep
their original blob SHAs, so only the mode changed. This is the CRLF defect
again in a different register: a repository-level property that a
Windows-only clone cannot notice it is violating.

**`AGENT_NOTES.md` also removed three stale blocks**, which is why it was
modified at all: the "Heatmap Feature Notes (shipped -- Batches 18/19)" and
"Batch 21 Tooling Map" sections both describe work that has since closed (the
tooling map says of itself "Written 2026-08-14, before WP-1 started"), and a
gap item about `skills-lock.json` was removed because that file is gitignored
and so cannot be part of the corpus a reader can check. A new
`HEATMAP_WINDOW_DAYS` constraint was added, pointing at the single source in
`scrobblescope/heatmap.py`.

**`requirements-dev.txt` was reverted, not committed.** It carried a local
addition of `cosmic-ray==8.7.0`, which exists to serve the mutation-test runner
that F-SWE-8 records as unadopted -- "the code stays out of the corpus until
then". Shipping its dependency while its tool stays untracked would be the
inconsistent half of that decision.

**Junk removed and ignored, each for a stated reason:** `nul` deleted (a
Windows reserved device name, so `del` and `Remove-Item` both fail on it and
`Test-Path` reports false while the directory entry is real; removed through
the `\\?\` extended-length prefix). `coverage.xml` ignored as the XML form of
the already-ignored `.coverage`; `/tmp/` ignored as agent probe scratch;
`.codex/` and `.continue/` ignored as per-machine harness config, which
`.codex/hooks.json` proves by naming an absolute path under one user's home.

**Deliberately left untracked:** `scripts/dev/mutation_test.py`,
`scripts/dev/mutation_scope.toml` and `tests/scripts/dev/test_mutation_test.py`,
because F-SWE-8 says not to stage them as part of another task's commit. They
are pending work with their own work package, and gitignoring them would
misdescribe them as not-repository-state. They are not graded modules, so their
presence does not invalidate a grade of `scrobblescope/`.

**Still awaiting an owner decision, not committed or deleted:**
`docs/2026-09-14-open-code-review-audit.md` (315 KB at the `docs/` root),
`docs/history/reports/CONTROL_PLANE_AUDIT_2026-09-15.md` (which cites it as
"the dated code-review advisory at the repository's docs root"),
`docs/history/reports/Architecture Review -- ScrobbleScope Control Plane &
Strangler.html`, `docs/superpowers/plans/plan.md` (a Batch 21 traversal plan)
and `progress_copy.md` (an SDD ledger for the close-out plan, whose own first
line names its source plan). All five are audit or planning evidence rather
than code; four belong under `docs/history/` by AGENTS.md's own archive
convention if they are kept. Moving or deleting 315 KB of someone else's audit
evidence is not a call this side task should make.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. The graphify unit's own
suite: 20 passed.

**One figure worth knowing about, found while measuring the above.** pytest
collects from `tests/` on disk, not from `git ls-files`, so the recorded count
of 1532 includes tests that live in files no clone will ever have: 20 in
`tests/scripts/dev/test_graphify_refresh.py` (now committed, so those become
real) and **46 in `tests/scripts/dev/test_mutation_test.py`**, which F-SWE-8
keeps out of the corpus. A tracked-only checkout therefore measured 1466
before this commit and measures 1532 only because of two untracked files. That
does not make the number wrong as measured, but it does mean it is not
reproducible from the SHA alone -- which is the same objection the audit's
charter raises about grading a dirty tree, applied to the test count. The 46
will keep inflating it until either the runner is adopted or the file is moved
somewhere pytest does not collect.

**Forward guidance:** the audit precondition is now met for the tracked corpus
-- no tracked file is modified. The three untracked mutation files are the
recorded exception, by F-SWE-8's own instruction. The five decision-pending
documents are the last thing between this tree and an empty `git status`, and
until they are resolved the count above keeps its 46-test caveat.

### 2026-09-20 - Architecture diagrams reconciled against the import graph

Side task, no batch tag. Two of the five architecture diagrams were stale, and
verifying them produced a scope problem for the deferred SWE audit that is
worth recording before anyone starts it.

**How the staleness was found.** Not by reading the diagrams against memory,
which is how they went stale, but by extracting the real module-level import
graph with `ast` and comparing edge by edge. That is the check F-B21-61 says
does not exist, and it took one script to demonstrate the need for it.

**`runtime-system.md` had seven missing edges and a wrong count.** Ground truth:
`Routes -> SpotifyClient` (`routes/api.py:22`, `routes/__init__.py:31`),
`Routes -> Domain` (`api.py:15`, `__init__.py:28`), `ReleaseChecks -> Utils`
(`release_checks.py:62`), `Spotlight -> Utils` (`spotlight.py:5`), and
`SpotifyClient -> Domain` (`spotify.py:14`), `DeezerClient -> Domain`
(`deezer.py:17`), `MusicBrainzClient -> Domain` (`musicbrainz.py:23`) were all
real imports absent from the drawing. The prose claimed eight nodes import
`config.py`; the true count is ten, and the list omitted `deezer.py`,
`musicbrainz.py` and `release_checks.py` -- the three modules Batch 22 added.
`App --> Routes` was drawn solid but is deferred inside `create_app`
(`app.py:143`), and the entrypoint's `config` import (`app.py:155`) is deferred
inside `__main__`. Fixed, with import lines cited so the list can be re-checked
rather than trusted.

**A second defect in the same file:** five bullets sat under the heading "Three
things this view deliberately makes visible". Batch 22 added three bullets and
nobody moved the count.

**`top-albums-sequence.md` was materially wrong, not merely incomplete.** A
search for `Deezer|MusicBrainz|release_check|provider|enrich` matched only its
own title: the entire Batch 22 enrichment path was undocumented. Worse, the
existing branch was incorrect independent of that omission -- it drew the
no-cache-hits case as an immediate `raise SpotifyUnavailableError`, while
`_fetch_spotify_misses` (`orchestrator/__init__.py:162`) tries Deezer for every
remaining miss first and raises only on three conditions together: no token,
nothing cached beforehand, and Deezer matching nothing. Persistence was drawn
inside the Spotify branch when it actually happens in the caller after the
Deezer pass returns, which is one row set for both providers rather than one per
provider. The correction worker -- enqueued at
`orchestrator/__init__.py:612`, immediately after `set_job_results` at `:600`
and only on the happy path -- was absent entirely, so it now has its own
lifeline and block.

**Validated structurally, not by eye.** A checker counts `alt`/`opt`/`loop`/
`par`/`subgraph`/`box` against `end` per fence and reports the final depth; all
six mermaid blocks in the repository return to zero, so the edits parse.
`docs/ARCHITECTURE.md`'s "Last verified" date moved to 2026-09-20 and its
section 3 description now names the Deezer fallback and the correction pass.

**Forward guidance, and the reason this matters more than two diagrams.** The
deferred SWE audit's charter (`docs/SWE_AUDIT_CHARTER.md`, retired after its
2026-08-20 execution) is no longer executable as written, because its closed
scope table names thirteen modules that no longer exist in that shape:

- It lists `scrobblescope/orchestrator.py` and `scrobblescope/routes.py`, which
  are packages since Batch 22 WP-0 -- 6 and 5 files respectively.
- It omits `deezer.py`, `enrichment.py`, `musicbrainz.py`, `release_checks.py`,
  `spotlight.py` and `unmatched.py` entirely. `git ls-files 'scrobblescope/*.py'
  app.py` returns **29** files, not the charter's 14.
- Its stated hotspots have moved. It names `_fetch_and_process` (was 151 lines)
  and `results_loading` (was 112). The largest function now is
  **`_render_results_page` at `routes/album_flow.py:126`, 142 lines**, which
  postdates the charter and is in neither list; `_fetch_and_process_heatmap`
  (141) and `_fetch_and_process` (133, now `orchestrator/__init__.py:502`)
  follow it.

The principle count is unchanged at ten (DRY, SoC, SRP, KISS, Dependency
Inversion, Composition over Inheritance, Clean Architecture, Boy Scout Rule,
Law of Demeter, Fail Fast), so the matrix is ten principles against the real
module list -- roughly 280 cells, not the charter's 130. A re-audit therefore
needs its own charter with a current, closed scope table before grading starts;
the retired one is evidence, not a work order. The charter's own Section 2a also
requires a clean worktree, and `AGENT_NOTES.md` plus `requirements-dev.txt` are
currently modified with untracked tooling alongside them, so that is a
precondition rather than a formality.

### 2026-09-20 - README engineering depth and the control-plane narrative

Side task, no batch tag, following the earlier reconciliation in this session.
That pass fixed stale *facts*; this one fixed a missing *argument*. The
architecture's real depth was documented nowhere, and DEVELOPMENT.md had been
stale for weeks about a control plane that is now the largest body of code in
the repository.

**README gained the engineering case, because its audience is developers and
recruiters rather than end users.** Two new pieces:

- **"A search is an ETL pass over an event stream, not a query."** Last.fm
  stores scrobbles -- an unbounded stream of track timestamps -- and has no
  concept of the album a listener played. An album is *produced* by grouping on
  a normalized key and threshold-gating on user criteria, so it is a function
  of the query, not a row. That is why the codebase does not look like CRUD,
  and it is the frame the rest of the architecture reads against.
- **"Owned Interface Components."** The heatmap as a hand-built SVG
  (`createElementNS`, Monday-first via `mondayIndex`, 7 rows against 53 week
  columns, a separate sequential mobile grid because 880px cannot fit a phone
  column), and the log-normalised intensity
  `Math.log10(count + 1) / Math.log10(maxCount + 1)` that keeps a heavy
  listener's mid-range visible on a linear ramp. Plus the theme-resolved
  zero-count cells (an SVG `fill` presentation attribute does not resolve a
  custom property), the 2x cloned-SVG export, the owned pinwheel, the
  deliberately desktop-faithful results export, and the sampled spotlight.

**DEVELOPMENT.md gained two arguments it was missing.** First, *why* the
rotation is a mechanism: it was done by hand three times and failed three
distinct ways -- an entry archived that should have stayed, an entry duplicated
across the boundary, a stale remark left behind -- all silent, because the
document still renders. The parser, renderer and rotation exist because that
task is one an LLM is not reliable at across sessions. Second, the ACID framing
stated honestly: atomicity is real, consistency is real (the invariant checks
are the C), isolation is partial (filesystem-scoped lock, no cross-machine
coordination, readers not serialised), durability is within filesystem
semantics. The precise description is an atomic file-transaction and invariant
enforcement system; the acronym is useful shorthand and stops being useful the
moment it is read as a database guarantee.

**The `.docsync.toml` extraction story is now written down**, which was the
largest gap. The declaration layer exists specifically so a second repository
supplies its own config without touching the mechanism -- and `declarations.py`
carries no ScrobbleScope value at all. What remains tied is enumerated as a
table rather than asserted: document paths, the scanned corpus and its
`allow_files` list, `[retired.allow_after] "PLAYBOOK.md"`, `[closeout]
admit_from_batch = 22`, the design-token `[[value]]` entries, and
`_LIVE_DOCUMENT_PATHS` in `integrity.py` (verified at line 100). The section
also records why finishing it now would cost more than it saves: the remaining
modules are the largest in the package, and making them generic before there is
a second consumer buys indirection rather than reuse.

**Also added:** the three pieces that make the package a workflow rather than
a mechanism -- the commit preflight, the opt-in hook installer (not installed
here), and the CLI surface. README's methodology section now says the tooling
is larger than the application on purpose and points at DEVELOPMENT.md for the
honest extraction state.

**Deviations:** one, self-inflicted and caught. Authoring the console section
introduced a zero-width space (U+200B) into DEVELOPMENT.md, violating the
ASCII-only authoring rule. Found by scanning for non-ASCII code points rather
than by eye, removed with a targeted rewrite, and re-verified clean. No other
document or file carried one.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. Non-ASCII scan of
README.md and DEVELOPMENT.md: none.

**Forward guidance:** DEVELOPMENT.md is still the narrative and
`docs/architecture/documentation-tooling.md` still owns the DOC001-DOC023
catalogue; the split was preserved rather than duplicated. The deferred plans
are unchanged and stay deferred.

### 2026-09-20 - DEVELOPMENT.md and README.md reconciled with the control plane

Side task, no batch tag. Two documents described a repository that no longer
exists, and one gate comment described a migration that had already finished.

**DEVELOPMENT.md was materially stale.** Its docsync section said the package
had "Six focused modules" and listed six test files. It has **twelve** modules
(`declarations`, `closeout`, `archives`, `findings`, `transaction`, `markdown`
were added by Batch 22) and twelve matching test files in `tests/`. The
worktree section named only `check_worktree_alignment.py` and a spec document,
omitting the seven `_worktree_guard_*.py` modules and the `WT000`-`WT014`
codes. The gate section stopped at "starts and stops its own loopback server"
and never named `port 0`, the `finally`, the 44px touch target, the 3:1
composited-contrast check, the viewport profiles or stylesheet isolation. Two
lines were also written in the present tense of a batch that has closed
("Batch 21 uses...", "The active batch definition owns...").

**README lacked four architectural facts** it should carry at product level:
the cache talks to Postgres in arrays via `unnest($1::text[], ...)` rather than
row by row; a stale schema identifies itself by SQLSTATE (`42703`, `42P01`)
instead of being mistaken for network turbulence; Spotify's removed batch
endpoint answers `403`/`404`/`410` and degrades to one request per album; and
the opening prose said the badge "is the live state", which read awkwardly.

**A new DEVELOPMENT.md section records the extraction intent** owner-stated
2026-08-25 and owned by `AGENT_NOTES.md`: this repository is also a template
being extracted, and the three control-plane components are at very different
maturity. The section states that honestly rather than aspirationally -- the
worktree guard is structurally complete, docsync is close, and the frontend
gate is the least extracted, with its decomposition plan deliberately parked.
It also records the standing constraint: do not start the extraction as a side
task; write new tooling so it stays cheap.

**A real defect was found and fixed in the process.**
`frontend_gate.py:209-215` carried a comment describing "the job-backed
Results and Unmatched templates" as still on Bootstrap, directly above an
already-empty `LEGACY_PAGES`. There is no residual Bootstrap: every template
carries an opt-out note, `static/css/` has no Bootstrap file, and README
already said "Bootstrap is gone". The only Bootstrap left is a test fixture
that proves a page *would* collide if it loaded both frameworks. A reader
trusting the comment would have concluded two page families were unmigrated.
This is anti-pattern 15 in miniature -- the comment had drifted from the code
beneath it, and only reading the source surfaced it.

**Deviations: none.** No production behaviour changed beyond the comment fix.
`docs/architecture/documentation-tooling.md` remains the owner of the control
plane; DEVELOPMENT.md links to it rather than restating the DOC catalogue, per
Rule 1.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. `ruff check` clean.

**Forward guidance:** the extraction plans
(`docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
and `.../2026-09-12-reusable-frontend-ci-verification-components.md`) both
carry "do not execute until" conditions and neither is scheduled. The frontend
plan's stated line count for `frontend_gate.py` (4,008) is now 4,353, so
re-measure before relying on its inventory. PR #235's summary was completed in
the same session and its review threads are adjudicated in
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`.

### 2026-09-20 - PR #234 advisory verification

Side task, no batch tag. PRs #233 and #234 merged with their review threads
deliberately unaddressed, so adjudicating them was the other half of the
pre-integration task. The question was not "are they open" but "are they
true".

**Method.** Read all threads from the GitHub API (35 review comments on #233,
22 on #234, plus issue comments and reviews), then checked each substantive
claim against on-disk code by grepping the tree, reading the cited function,
or running the cited gate. Nothing was accepted on the strength of a bot's own
summary.

**Result: four refuted, one partly true, one by design, one out of scope.**
Refuted: the DOC023 negation false positive (already handled by
`_NEGATED_OUTCOME_RE`); the `_TERMINAL_SUFFIXES` escaping gap (`re.escape` is
already there, line 354); the `newest == 0` blank-line nitpick (the guard is
deliberate, and `495e9c2` already fixed the real case); and the claim that
DOC023 is documented as both blocking and non-blocking (the catalogue states
the blocking and grandfathered-warning roles as two populations, and the code
implements exactly that). By design: hard-failing a stale archive index
(`DOC020`) is Rule 7's refusal to guess which side of a disagreement is the
history worth keeping. Out of scope by owner ruling: complexity and coupling
advisories, recorded in the report so nobody re-adjudicates them.

**One refuted claim surfaced a real defect.** Graphify rated
"`AlbumMetadata` cache-row method renamed and now requires extra arguments" as
high risk. Nothing calls the method, so nothing broke -- but a repo-wide search
found `as_cache_row` at its definition and in its own test only, while both
production sites build the row tuple inline (`_details.py:137` as six elements,
`_deezer_fallback.py:83` as nine). The persistence order therefore has two
owners, and a test asserts the copy nothing writes. Filed as F-B22-7 rather
than fixed: retiring the method or rerouting a builder is a choice between two
working shapes with a Batch 22 test contract around one of them.

**A vacuity guard earned its place.** The first run of the DOC023 probe used an
`##` heading, which `FINDING_HEADING_RE` does not match, so no finding parsed
and every case read "blocks = False". The output looked like a clean refutation
of the whole claim. Adding a guard that reports `VACUOUS PROBE` when no case
parses caught it; the corrected run is live on 6 of 14 cases with every
expectation met. Recorded because "the gate stayed silent" and "the gate was
never reached" are the same output and different facts.

**Deviations: none.** No production behaviour changed. The two findings are
records, not repairs, and the report is
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`.

**Validation:** `pytest -q` -- **1532 passed**, unchanged (no runtime code
touched). `doc_state_sync.py --check` exit 0.

**Forward guidance:** the residual DOC023 false positive ("No action needed
yet." blocks) is deliberate and filed as F-DOCSYNC-14; widening the negation
window would buy silence on two phrases and pay for it by missing real
completion claims, which is the failure the gate exists to prevent. Do not
"fix" it without reading that entry.

### 2026-09-20 - Outbound request identity and the MusicBrainz contact

Side task, no batch tag. Scope was the pre-integration task for `test` into
`main`: API endpoint-fetching compliance, the MusicBrainz HTTP contact, and
agent access to the key documents. PR #236 was opened for the branch.

**Three findings, each verified before repair.** First, no provider request
carried a User-Agent at all: the string `User-Agent` appeared in exactly one
file under `scrobblescope/` (`musicbrainz.py`), and `create_optimized_session`
passed no headers, so every Last.fm, Spotify and Deezer request went out as
aiohttp's default `Python/3.13 aiohttp/3.14.3`. Last.fm's API introduction
asks for "an identifiable User-Agent header on all requests" and warns an
account "may be suspended if your application is continuously making several
calls per second", so this was a compliance gap rather than a style one.
Second, `_musicbrainz_headers` interpolated an unset contact as the literal
string `None`, producing `ScrobbleScope/1.0 ( None )`; the guard in
`lookup_original_release` kept it off the wire, but the helper is reachable
directly and the header's whole purpose is to name a client that can be
contacted. Third, `MUSICBRAINZ_CONTACT` is absent from this worktree's `.env`,
so the correction pass is inert here: a read-only probe returned `(None, None)`
with zero HTTP calls.

**Plan vs implementation: matched.** `APP_VERSION` and `APP_USER_AGENT` moved
into `config.py` as the single owner of the application's own name, and
`create_optimized_session` now sends that User-Agent as a session default.
`musicbrainz.py` dropped its private `_APP_VERSION` copy and composes its
contact-bearing header on the shared identity, so the application cannot name
itself two different ways. Before adding the session default, aiohttp's merge
semantics were measured against the pinned 3.14.3, because the change rests on
them: a per-request `headers=` dict merges with the session default rather than
replacing the header set, so MusicBrainz's own User-Agent still wins and is not
clobbered. `_musicbrainz_headers` now raises when no contact is configured
instead of rendering `None`.

**Deviations: none.** No new dependency, no new module, and no new import edge:
the graph stays `utils.py <- config` and `musicbrainz.py <- config, domain,
utils`, so SESSION_CONTEXT Section 4 needed no change, and `.docsync.toml`
declares nothing about environment variables or User-Agent.

**Agent access to the key documents verified**: all 15 documents in the
bootstrap and orientation set resolve and are readable, including both optional
ones (`docs/AGENT_DOC_MAP.md`, `docs/architecture/documentation-tooling.md`)
and the handoff report. The worktree guard also exits 0 on this branch; its
`WARNING WT010` and `INFO WT000` are the expected states for a development
branch in a linked worktree, not failures.

**Validation:** `pytest -q` -- **1532 passed**, three more than the previous
1529: `test_create_optimized_session_sends_shared_user_agent`,
`test_musicbrainz_headers_refuses_a_missing_contact`, and
`test_musicbrainz_headers_is_derived_from_the_shared_identity`. `ruff check`
and `ruff format --check` are clean on all five touched files.

**Forward guidance:** the code defect is closed, and `MUSICBRAINZ_CONTACT` is
not a secret -- it is a contact string that travels in the User-Agent header,
so setting it is a config change rather than a credential decision. It is
unset here and was absent from DEPLOY.md's own instructions, which is why the
deployed app runs the correction pass off; DEPLOY.md now documents it. The
`main` branch was deliberately not touched -- `test` is the integration branch
and `main` is the stable Fly.io deployment.

### 2026-09-20 - Session close-out and handoff

Side task, no batch tag. The session closed under a token budget, so this
entry records the state rather than the reasoning; the entries below carry
the reasoning.

**Pushed.** Seven commits are on `origin/feat/batch22-enrichment`, from
`3707d6a` to `e57e894`: the work-package tag repair, Batch 22 WP-4 (the
release-check endpoint and its live disclosure), the colour-serialization
class fix, the Batch 22 close-out, the Batch 23 definition with six
corroborated proposals, and the cache repair with the findings rotation. The
branch is **not merged** into `test`; opening a pull request is an owner
decision and has not been taken.

**Handoff written for a new agent**, deliberately assuming no familiarity
with this repository and no particular tooling:
`docs/history/reports/HANDOFF_2026-09-20.md`. It carries the reading order,
the environment, the five ways this repository will refuse a commit and why,
the database-migration fact that hid a dead cache for a whole batch, what
Batch 23 is, and the open items with their findings.

**The owner's inline questions in `FINDINGS.md` are resolved** and have been
removed. They were written after Batch 21 closed, asking why nothing had
rotated; the answer was that no finding carried the lifecycle record rotation
requires, and the rotation in the entry below is the answer in effect. Two of
the removed lines were not questions and were restored: an owner ruling that
the GitHub-to-findings sync must run in both directions, now recorded inside
F-B21-9, and a wrapped line of F-LOAD-2's own prose that a regex mistook for
an annotation because it began with a slash.

Validation: `pytest -q` -- **1529 passed**. `doc_state_sync.py --check` exit
0, its only warning the root definition waiting for Batch 23 to open.

Next action for whoever arrives: read the handoff, then decide the pull
request and whether to open Batch 23.

### 2026-09-20 - The cache was inert, and the findings backlog now rotates

Side task, no batch tag, on the owner's instruction to close Batch 22's
remaining cache and findings work now rather than carry it into Batch 23.
Investigated through `superpowers:systematic-debugging`.

**The metadata cache had been inert since Batch 22 shipped.** The owner's
local database still held the pre-Batch-22 schema: `spotify_cache` had no
`provider`, `provider_album_id` or `provider_url` columns, `spotify_id` was
still `NOT NULL`, and `original_release_cache` did not exist at all. Read
against it, `_batch_lookup_metadata` raised `UndefinedColumnError` and
`_batch_lookup_original_release` raised `UndefinedTableError` -- measured, not
inferred.

The consequence was not an outage, which is why nobody caught it. Both reads
are wrapped, so every job degraded to a cache-less run and carried on: 3,628
usable rows went unread on every search, every album was re-fetched from
Spotify or Deezer, and every MusicBrainz correction was paid for at one
request per second and then discarded. The owner's 2026-09-20 run reads
exactly that way -- `Cache partition: 0 hits, 366 misses` -- and the database
being down at the time hid the second fault behind the first.

`init_db.py` is idempotent and is what fixes it. Run against the live
database: the three columns exist, `spotify_id` is nullable,
`original_release_cache` exists, and all **3,628** existing rows were
backfilled to `provider = 'spotify'` with `provider_album_id = spotify_id`.
Then, against that live database rather than a mock, Batch 22's cache
acceptance criteria were exercised for the first time: a Deezer-only row with
no Spotify id round-trips; a legacy six-tuple caller still writes a row that
reads back as Spotify; a pre-existing row is readable through the cache API
after the backfill; and both a correction and a "checked, nothing found" row
round-trip through `original_release_cache`. The probe rows were deleted
afterwards.

**The class fix, because the instance was a one-line command.** A missing
column is not a transient failure: it never heals, and every read until
someone notices misses a cache that is sitting right there. The code reported
it in the same words as a dropped connection. `scrobblescope/cache.py` gains
`schema_is_out_of_date`, matching PostgreSQL SQLSTATEs 42703 and 42P01 --
matched on the SQLSTATE rather than the asyncpg exception class, because
asyncpg is an optional import here and a SQLSTATE is the stable half of the
contract -- and a single remediation string naming `init_db.py`. Both cache
readers and the correction worker's persist path now say which kind of
failure they hit. Seven tests cover it, including that a transient failure
must **not** tell the reader to run a migration.

This is the same shape as the DOC013-DOC018 gate that had never fired once:
a subsystem reporting success while doing nothing. It is worth naming as a
class -- a failure that degrades silently needs a diagnostic that
distinguishes "will heal" from "will never heal", or it is indistinguishable
from working.

**The findings backlog rotates again.** 85 findings, 83 with no lifecycle
record, so nothing had rotated at either batch close-out -- the owner's
question in `FINDINGS.md` had the right instinct. The owner ruled on
2026-09-20 that a prior session's record may be transcribed, since the
authors are earlier agent sessions and the standing warning confuses a reader
more than an archived finding would.

Each of the 23 grandfathered findings was given the record its own author's
words support, and the distinctions were kept:

- **16 were terminal** and are now in `docs/history/findings/FINDINGS_ARCHIVE.md`
  under their original ids with the `-- RESOLVED` suffix. Where the author
  wrote a date it is theirs; where they wrote none, the completion date is
  the day of the evidence they cite, which is an inference and is recorded
  here as one.
- **5 say "resolved locally, deploy before the next production release"** and
  are NOT checked. The lifecycle gate treats a pending deploy as not-yet
  terminal and it is right to: the fix is in the tree, not in front of a
  user. They keep an unchecked record and stay active.
- **2 were never resolved at all** -- F-B21-9 was deferred by owner decision
  and F-B21-53 is open for the general card token. Reading either as finished
  because the word "resolved" appears in its prose is exactly the mistake
  DOC023 exists to prevent.
- **F-B21-1 was verified in source rather than taken on trust**: loop
  construction now sits inside the `try` in both `background_task` and
  `heatmap_task`, with `release_job_slot()` in the `finally`.

`[findings] grandfathered` in `.docsync.toml` is now `[]`, and **DOC023's
standing warning is gone**. The list stays declared so a repository adopting
this gate starts strict with somewhere to put its own history. Active
findings: 72, down from 85.

Validation: `pytest -q` -- **1529 passed** (was 1522; +7 for the schema
diagnostic). `pre-commit run --all-files` -- all hooks pass.
`doc_state_sync.py --check` exit 0, and its only remaining warning is the
root definition for Batch 23, which is expected while that file waits at the
root. `.docsync.toml` is control-plane, so this commit uses the sanctioned
`SKIP=doc-state-sync-check`, with `--check` run directly first.

Forward guidance: the five "pending deploy" findings resolve themselves the
next time production ships, and their records are the checklist. Nothing
about this change requires a deploy of its own -- but the schema migration
does need running wherever else this app has a database, which on Fly.io
happens automatically, since `init_db.py` is the release command.

### 2026-09-20 - Batch 23 defined, and six owner proposals corroborated

Side task, no batch tag: the owner proposed a different MusicBrainz lookup
strategy, a move from threads to `asyncio` inside Flask, server-sent events
in place of polling, a narrowed Lucene query, and a test-count fix, and asked
for each to be corroborated rather than taken. Nothing in this entry changes
runtime behaviour. `BATCH23_DEFINITION.md` is written but Batch 23 is **not
open**: its branch is unnamed, and naming it is an owner decision.

**Threads cannot run coroutines -- half right, and the half that is wrong
matters.** Measured directly: `threading.Thread(target=an_async_def)` never
runs the coroutine and raises no error, only a "was never awaited" warning,
which is worse than a crash. A thread that creates its own event loop and
calls `run_until_complete` runs it correctly, and that is what
`scrobblescope/release_checks.py` already does. The proposed remedy --
dropping `threading` for `asyncio.create_task()` inside Flask -- cannot work
here: a probe route asked for a running loop and got "no running event loop".
Flask under a WSGI server has no persistent loop to attach a long-lived task
to, so the thread-owns-a-loop pattern is the remedy, not the problem.

**The Gunicorn race condition does not exist today, by configuration.**
`Dockerfile` runs `--workers 1 --threads 4`. One worker means one `JOBS`
dict, one semaphore and one process-wide MusicBrainz limiter.
`AGENT_NOTES.md` already records that a second worker would break the job
store; it would break the rate limiter too, which is the sharper consequence
since MusicBrainz blocks by IP.

**Server-sent events would take the whole thread pool.** Four threads, and an
SSE response holds its thread for the life of the connection: four readers
with a results page open would leave nothing for the home page. Filed as
F-B22-6.

**The MusicBrainz proposal: the exact path is real, the ISRC path is not.**
Probed live against five albums at one request per second.
`GET /ws/2/url?resource=<spotify album url>&inc=release-rels` returns a "free
streaming" relation to a **release** when an editor has mapped that album;
a second request on the release yields the release group's
`first-release-date`. Two requests, exact, no scoring. It answered two cases
today's search path did not -- one where the top candidate scored 100 with no
date at all. It was unmapped for one of the five. Note for the implementer:
`inc=release-groups` on that endpoint returns nothing, and
`inc=release-group-rels` returned zero relations; the include is
`release-rels`.

The ISRC path costs more and is worth less. `GET /v1/albums/{id}` returns
simplified track objects carrying **no** `external_ids`, confirmed by reading
the keys off a live response, so every ISRC needs an extra Spotify request;
and `/ws/2/isrc/{isrc}` returns recordings, whose earliest release group may
be a single rather than the album. Dating an album by its lead single is a
worse answer than no correction.

Also measured: `AND type:album` would exclude EPs, which this application
ranks alongside albums -- `normalize_name` strips "ep" from titles for
exactly that reason -- and the release-group search field is `primarytype`,
not `type`.

All of it is F-B22-5, with the measurements, and the recommendation is to
keep the one-request search as the primary and spend the second request only
where it buys something: no candidate, or a candidate with no date, and a
Spotify id present. **The correction cache must stay keyed on
`(artist_norm, album_norm)`, never on a Spotify id.** The owner's own
2026-09-20 run had Deezer rescue 9 of the 10 albums Spotify could not enrich,
and those albums have no Spotify id at all.

**That run also settles what Deezer is for.** The log shows 356 of 366 albums
matched on Spotify, then 9 of the remaining 10 matched on Deezer, with the
database cache down and every lookup live. Deezer is not only an outage
fallback; it answers for albums Spotify does not carry. The README's
description was written for the outage case and now says both.

**The test count.** `--fix` cannot publish a measured count and `--check`
refuses a hand-written one, because `latest_test_count_authority` parses the
number out of prose in dated entries and DOC005/DOC006/DOC008 recompute that
parse. Rule 7 is why the tool does not simply run pytest: it may rewrite only
what it can derive from facts a human authored, and measuring the world is
not that. Filed as F-DOCSYNC-13 with a proposed shape -- an authored
measurement passed in, written by `--fix` into all four sites -- for the
owner to rule on.

**Batch 23's definition** is derived from the approved plan, in this
repository's own work-package form: WP-0 behaviour-neutral extractions, WP-1
error codes, WP-2 the pure parser and aggregators, WP-3 the job hand-off,
WP-4 routes and upload handling, WP-5 the interface, WP-6 the new statistics
for both sources, WP-7 documentation, the deferred Batch 21 accessibility
audit and close-out. The audit is inside WP-7 because the owner ruled on
2026-09-13 that this batch cannot close without it.

**A wording trap worth knowing.** Section 3's "Batch 23 is not yet defined"
has to sit on one line: the state parser reads Section 3 line by line, and
wrapping that sentence across two lines made the gate infer an active batch
and demand a definition declaration. The same class of defect, in the other
direction, was fixed during the docsync close-out.

Validation: `pytest -q` -- **1522 passed**, unchanged (no runtime code was
touched). `doc_state_sync.py --check` exit 0, with the expected DOC023
warning and the root-definition warning that is normal for a batch with a
definition at the root. The live probes were read-only: Spotify with the
app's own credentials, MusicBrainz with a contact-bearing User-Agent at one
request per second.

### 2026-09-20 - Batch 22 work-package tags, and the docsync side task closed

Side task, no batch tag: bookkeeping repair found while orienting for WP-4,
plus the close-out of the docsync work the entry below tracks. No code
changed and no batch scope moved. The unrelated in-flight Batch 22 edits in
this worktree (the mutation runner, `graphify_refresh.py`, `AGENT_NOTES.md`,
`requirements-dev.txt`) were neither staged nor reverted.

**PR #234 merged** as `88f6e27` into `test`, so the docsync close-out side
task is finished and `feat/batch22-enrichment` is now fully contained in
`origin/test`. The gitignored `CLAUDE.md` section that tracked it asked to be
deleted on that merge, and was.

**The defect: six current-batch entries carried the wrong work-package tag.**
Every entry from Task 5 onward was headed `(Batch 22 WP-1)`, including the
Task 6 work that belongs to WP-2 and the Tasks 7-8 work that belongs to WP-3.
That tag is not decoration: `ENTRY_BATCH_RE` in `scripts/docsync/parser.py`
parses it, and the managed STATUS block in `.claude/SESSION_CONTEXT.md` is
derived from what it finds. The dashboard therefore read "WP-0, WP-1, WP-3"
and never named WP-2 at all -- a cold-resume reader would have seen the
Deezer fallback as work nobody had done. Retagged against the definition's
own task-to-WP map: Tasks 5-6 and both README passes to WP-2, Tasks 7-8 to
WP-3. Tasks 1-3 were already correct.

**Why this overrides the note that left the tags alone.** The Task 8 entry
above recorded a decision to keep its WP-1 heading as "its historical commit
record". That reasoning treats the tag as prose. It is an index key, and the
scope to fix it across six entries is exactly what that session said it
lacked. The superseding note now sits in that entry. The declines recorded in
F-DOCSYNC-3 are a different case and still stand: they cover content the tool
has already rotated into an archive, not live entries that have not rotated
yet.

**Also repaired:** `BATCH22_DEFINITION.md` still showed Task 9 unchecked while
its own header and Section 3 both said Tasks 7-9 were complete; the WP-3
heading now carries the struck-through DONE form its three siblings use.
F-B21-60 and F-B22-4 cited "Batch 22 WP-1 Task 6" in three places and now cite
WP-2.

**Known remaining instance, recorded rather than fixed:** F-DOCSYNC-12's
`Source:` line reads "Batch 22 WP-1, DB-connect-timeout side task". A side
task has no work package, so the right correction is not a different number,
and inventing one would trade a visible error for an invisible one.

**Two findings filed.** F-SWE-8 records the mutation-test runner's
disposition -- built, never adopted, four defects on first use, uncommitted,
its own future work package. It lived only in the gitignored `CLAUDE.md`, so
deleting that section would have erased it from the corpus entirely.
F-DOCSYNC-3 gains a second instance: Batch 22's Task 4 entry was headed
`(Batch 22 WP-1, Phase 2 begins)`, and the trailing clause inside the
parentheses made the heading unparseable as batch-tagged, so rotation sent it
to the monolith archive instead of a per-batch log. The defect is wider than
the `(Batch N close-out)` suffix the finding first described, and the tool
says nothing when it happens.

Validation: `pytest -q` -- **1497 passed**, unchanged (documentation only).
`doc_state_sync.py --check` exit 0, with the expected DOC023 grandfather
warning and the root `BATCH22_DEFINITION.md` warning. The frontend gate was
not rerun: nothing under `templates/` or `static/` changed, so the last
recorded result stands.

Forward guidance: Batch 22 WP-4 is next -- Task 10, the job-scoped
`GET /api/release_checks` endpoint, then Task 11's live disclosure. Two gaps
between the plan text and the code as built land on Task 10. The plan says
the endpoint reuses `_get_validated_job_context`, which renders `error.html`
and returns HTML; its JSON neighbours return JSON error bodies, so a
JSON-shaped validation path is needed. The plan's payload also carries
`original_release_date` per album, but Task 9's worker writes only
`{"release_check": ...}` through `update_job_result`, so the corrected date
never reaches the result and the worker has to write it.

### 2026-09-20 - Docsync review round, DOC023, and PR #234

Side task, no batch tag: close-out of
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`. Not Batch 22
scope. The unrelated in-flight Batch 22 edits in this worktree were neither
staged nor reverted. Ledger:
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.

The whole-branch review had to be split: `/ultrareview` caps at 500 files and
8,000 lines against the working tree, and this work package was 52 files and
12,403 lines. The engine commit was reviewed alone from a temporary branch.
Every reported finding across ultrareview, Codacy, Graphify and qlty was
reproduced or refuted before being acted on -- roughly twenty reports produced
eight real defects. Refutations included a "high" that was an artifact of
where the review scope was cut and healed by the next commit, and three qlty
correctness items that were analyzer flow-model false positives.

Defects fixed, each with a regression test proven to fail without its fix:
archive pages were packed in reading order while every producer prepends, so
one rotated entry repacked the whole archive and returned cold pages to hot;
`--close-batch` restated the closure date from the clock; findings rotated to
the bottom of an archive whose prologue says newest first; the hook installer
resolved a relative `core.hooksPath` against cwd and wrote through a
pre-existing symlink onto its target; close-out `assert`s guarded a publish
and vanish under `python -O`; the preflight re-encoded a text-mode tar payload
and extracted unfiltered below Python 3.12.

DOC023 closes the finding-rot hole: all 83 findings lacked the canonical
`- [ ] **Status:**` record, so DOC013-DOC018 had never fired once. It blocks a
finding whose prose claims a terminal outcome without that record. The
boundary is an explicit id allowlist in `[findings] grandfathered`, not the
batch number the plan specified -- 32 of 83 ids are source-tagged and carry no
batch to compare, so a boundary would grandfather them by accident and let a
new finding escape by choosing a tag. 23 ids are grandfathered and reported as
one warning carrying a count derived from the file on every run.
`docs/agents/global-rules.md` was also added to Session Bootstrap, which it was
missing from despite being binding.

Validation: `pytest -q` -- **1497 passed**; `doc_state_sync.py --check` exit 0;
`frontend_gate.py` exit 0; `AGENTS.md` 473 lines against its 500 cap. Eighteen
commits on `feat/batch22-enrichment`, nothing unpushed, open as PR #234 into
`test`.

### 2026-09-19 - Docsync close-out plan Tasks 3 and 4, and a control-plane code review

Side task, no batch tag: continuation of the entries below on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope. Nothing
is committed; the whole plan remains working-tree-only by owner constraint,
and the unrelated in-flight Batch 22 edits in this worktree were neither
staged nor reverted.

Task 3 (CLI integration and multi-signal close-out) landed in six slices:
the two strict configuration tables, the definition-side close-out record,
the gate wiring, `--close-batch`, the archive maintenance modes, and DOC020.
Its review found one Important defect -- the `expected` map passed to
`transaction.publish` did not cover every path the plan had READ, so a
concurrent edit by another agent could publish a decision made about
different content. Fix round 1 made `_Corpus.read_paths()` the single source
of truth for that, so a document added to the corpus later inherits the
protection instead of needing a second hand-maintained list.

Task 4 was split into a code half and a documentation half. The code half
added `scripts/dev/docsync_preflight.py` and
`scripts/dev/install_docsync_hook.py`, moved the docsync hook to first
position in `.pre-commit-config.yaml`, and added an explicit CI preflight
step. Its review found that the control-plane refusal existed only in
`--staged` while the pre-commit entry runs `--worktree`, which is the path
that actually executes on every local commit; fix round 1 closed that.
The documentation half brought `AGENTS.md` from 728 to 498 lines by
compressing, relocating the DOC catalogue to
`docs/architecture/documentation-tooling.md` and the bootstrap edge cases to
`HANDOFF_PROMPT.md`, and relocating the `UI and Accessibility Rules` that an
in-flight Batch 22 edit had deleted into `docs/agents/ui-accessibility.md`.
That single deletion was the root cause of all three live gate errors, which
are now repaired.

Owner rulings taken during the session, both recorded in the plan ledger: the
commit preflight refuses any commit that modifies the docsync control plane,
and the one named escape is `SKIP=doc-state-sync-check git commit` rather
than `--no-verify`, so the absolute prohibition on `--no-verify` in
`AGENTS.md` anti-pattern 7 stands unchanged; and the architectural invariants
the owner supplied are now a binding document at
`docs/agents/global-rules.md`, carrying an explicit precedence order for when
two rules conflict.

An owner-requested code review of the control plane followed, and its
findings were fixed rather than filed. `--split-archive` had been writing
directly to disk with no lock, no journal and no staleness check, which
contradicted the atomicity guarantee every other writing mode honours; it now
publishes through the same transaction. The batch-definition regex that had
been constructed five times across three modules is now
`parser.root_definition_pattern`. The live-document path list, which the tool
had duplicated between `cli.py` and `integrity.py` without the declaration it
would demand of any other repository, now has one owner. On the application
side, `update_job_result` no longer normalizes every result inside the
process-global lock -- the key is attached once where results are built --
and `run_release_checks` was decomposed into three named units with its
existing tests passing unmodified as parity evidence.

Validation, run fresh in the controller session rather than taken from any
subagent's report: the two preflight and hook suites were 76 passing, the
release-check suite 23 passing unmodified before and after its refactor, and
`ruff check` plus `ruff format --check` were clean across the touched files.
`scripts/doc_state_sync.py --check` now exits 0, leaving only the expected
root `BATCH22_DEFINITION.md` warning. Validation: `pytest -q` -- **1470 passed**.

Deviations worth the next reader's attention. `AGENTS.md` landed at 498 lines
rather than the ~420 target: every remaining line is a distinct rule or
procedure, and further cuts would have removed prohibitions rather than
narrative. Two documents under `docs/agents/` were staged, against the
plan's own no-staging rule and at the owner's explicit instruction, because
DOC001 reads `git ls-files` and an untracked file can never satisfy a
reference to it.

Forward guidance, in the owner's stated order: build the DOC023 invariant
that stops resolved findings rotting in free prose, then run the final
whole-branch review, then land the work as a sequence of atomic commits
rather than one large one. The triage list for that review is every finding
marked deferred in
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`, which
remains the authoritative ledger for this plan.

### 2026-09-16 - Docsync close-out plan Task 2 closed out

Side task, no batch tag: continuation of the 2026-09-15 entry below on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope; nothing
here touches live `FINDINGS.md`, the archive files, or the docsync CLI.

Task 2's fix round 1 (resumed 2026-09-15 with a fresh implementer, since
the original handle was unavailable) addressed all 3 Important findings
recorded in `docs/history/reports/DOCSYNC_CLOSEOUT_TASK2_REVIEW_2026-09-15.md`:
a missing index no longer deletes existing pages (`_load` now rejects
orphans before returning an empty layout); a page's silently-discarded
prologue/missing header now raises `SyncError` instead of being dropped;
`page_path` now resolves beside `index_path` instead of always under the
store root. Each fix is covered by a regression test whose own docstring
names the finding it reproduces.

This session had no subagent-dispatch tool available, so the required
scoped re-review was performed by the controller directly instead of a
dispatched reviewer -- a disclosed deviation from
`superpowers:subagent-driven-development`, consistent with how Task 1's
own fix round 1 was handled for the same reason. The re-review checked
each fix against the review report's findings and the design spec's own
language (not just that tests pass), and swept for the same defect class
elsewhere in the module (`_diff`, the other `_reject_orphans` call site)
before concluding no sibling instance existed. Full re-review detail is in
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.

Validation, run fresh: the archive suite alone was 43 passing, and the
full docsync suite (markdown/declarations/integrity/logic/parser/findings/
archives/transaction) was 355 passing; `ruff check` on all Task 1/2-owned
files was clean. Validation: `pytest -q` -- **1302 passed** (up from 1298;
the delta is this shared worktree's own concurrent, uncommitted growth in
`archives.py`/`test_docsync_archives.py`, not a regression -- see the
out-of-band fix entries above for the same observation applied to
`logic.py`).

Task 2 is complete: 3/3 Important findings addressed, 0 new
Critical/Important breakage. 7 Minor findings (recorded in the review
report) remain deferred, unchanged, to the final whole-branch review's
triage. Next step: Task 3 (CLI integration and multi-signal close-out).

### 2026-09-15 - Docsync close-out plan Task 2 review recorded

Side task, no batch tag: control-plane work on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope; nothing
here touches live `FINDINGS.md`, the archive files, or the docsync CLI.

Task 1 (shared Markdown scanner, DOC010-DOC012 repairs) is complete and
reviewed clean. Task 2 (finding lifecycle + bounded archives + recoverable
publish: `findings.py`, `archives.py`, `transaction.py`, DOC013-DOC018) is
implemented and controller-verified green (93/93 new suites, 351/351 full
docsync suite, Ruff clean), but its task review returned Needs fixes: 3
Important findings, all in `archives.py`, all silent history-loss/
misplacement paths with no diagnostic (a missing index deletes every
managed page; page prologue content is silently discarded; `page_path`
writes to the wrong directory when an index does not sit at the store
root). Plus 7 Minor findings, logged for the final whole-branch review.
Full detail: `docs/history/reports/DOCSYNC_CLOSEOUT_TASK2_REVIEW_2026-09-15.md`.

Validation: `pytest -q` -- **1298 passed** (unchanged; this side task adds
one documentation file and a PLAYBOOK entry only, no application or docsync
source). Tasks 3-4 of the plan are not started. Next step: resume the SDD
fix loop on Task 2's three Important findings.

### 2026-09-14 - Mutation testing scoped to hermetic modules

Side task, no batch tag: owner-directed tooling, outside Batch 22's scope and
its definition.

Scope: `scripts/dev/mutation_scope.toml` (new),
`scripts/dev/mutation_test.py` (new),
`tests/scripts/dev/test_mutation_test.py` (new), `AGENTS.md`. Motivation was
`cosmic-ray==8.7.0` sitting in `requirements-dev.txt` with no caller; the
decision was to give it a defined home rather than delete it, because a
47-mutant module costs minutes here and the repo already mutation-tests by hand
(the Batch 21 plans call it "mutests").

Implementation:
- `mutation_scope.toml` is the allowlist of modules cleared for mutation
  testing, each with the tests that cover it: `domain.py`, `enrichment.py`,
  `unmatched.py`, `worker.py`, `spotlight.py`, `orchestrator/_results.py`,
  `scripts/dev/graphify_refresh.py`. The file carries its exclusion list and
  the reason per entry, so a gap is not read as an oversight: `utils.py` and
  `repositories.py` are time- and loop-dependent, and the network and DB
  modules are not hermetic at all.
- `mutation_test.py` drives cosmic-ray for one allowlisted module and refuses
  every other path by exact normalized comparison. It builds the cosmic-ray
  config in a temporary directory, runs init/baseline/exec, and reports caught,
  survivors and unknown. Two guards protect the checkout: it refuses to start
  while the module has uncommitted changes unless `--allow-dirty`, and it
  compares the module's SHA-256 before and after so a mutant left on disk is an
  error, not a clean verdict.
- `AGENTS.md` gains a "Mutation testing (on demand, never a gate)" subsection
  under Test Quality Rules: the allowlist rule, the pre-refactor trigger, the
  survivor-is-not-a-defect warning, and that no hook and no workflow calls it.

Deviations and repairs found on the way:
- `doc_state_sync.py --check` was already failing on four integrity errors
  before this task, all fallout from the removal of the "UI and Accessibility
  Rules" section from `AGENTS.md`: DOC009 for the declared 44px touch minimum,
  and DOC010 twice for citations of a heading that no longer existed. The
  section is restored in condensed form, with items 1 and 2 keeping the numbers
  two other documents cite. That removal was mid-edit, not part of this task;
  the repair is recorded here because it shares the commit.
- `AGENT_NOTES.md` was also failing DOC009 on its declared heatmap-window site,
  and had trailing whitespace at what was line 314. Both repaired.
- `requirements-dev.txt`'s `cosmic-ray==8.7.0` line was uncommitted and
  unreferenced; this entry is the first record of an owner decision to keep it.

Validation: `pytest -q` -- **1153 passed**, up from 1108 with the 45 new tests.
`ruff check` and `ruff format --check` clean on both new files.
`doc_state_sync.py --check` passed with only the expected root-BATCH warning.
`mutation_test.py --list` prints the seven scoped modules, and `--init-only` on
`scrobblescope/unmatched.py` reports 47 mutants in about a second.

Forward guidance: the post-`exec` outcome mapping in `classify()` was written
against cosmic-ray 8.7.0's session schema. Which modules qualify, the refusals,
and the config shape are all covered by tests, but the mapping from a completed
session record to killed/survived is not yet exercised end to end, so a first
full run should be checked with `--raw` before its numbers are quoted. An
unrecognised record is reported as unknown rather than guessed, which is what
makes that check cheap.

### 2026-09-14 - DB connect timeout (found while localhost-testing the Deezer fallback)

Scope: `scrobblescope/cache.py`, `tests/test_repositories.py`. Owner-found
during manual localhost verification of Task 5's Spotify-fails-to-Deezer
fallback (an invalid `SPOTIFY_CLIENT_ID`, per the plan's own verification
step 2): the browser sat at "Preparing 129 albums for Spotify lookup..."
for three minutes with no server-log output at all, for two different
Last.fm usernames. The owner had *paused* (not stopped) the local
`ss-postgres` Docker container, which answers no SYN-ACK at all rather than
refusing the connection -- unlike the ordinary "DB is down" case the
existing retry/backoff (2026-02-14, `DB_CONNECT_MAX_ATTEMPTS`,
`DB_CONNECT_BASE_DELAY_SECONDS`) was built to smooth over.
`_get_db_connection` is the first thing `process_albums` does, before any
further progress update, so the whole stall was silent and looked
identical to a hang. Root cause: `asyncpg.connect(dsn)` carried no
explicit `timeout`, so each of the 3 default attempts ran out asyncpg's own
60s default -- 3 x 60s = 180s, matching the observed 3 minutes exactly.

Fix: a new `DB_CONNECT_TIMEOUT_SECONDS` env knob (default 5), passed as
`asyncpg.connect(dsn, timeout=connect_timeout_seconds)`, following the same
env-tunable pattern as the two existing retry knobs. Worst case with
defaults is now ~3 x 5s plus the existing sub-second backoff, not 180s. Not
part of any Batch 22 WP-1 task's file list (Task 7 already landed and
committed separately as `8eb3c2a`); a small, unrelated robustness fix,
logged here per Side-Task Handling rather than folded into a task entry.

`tests/test_repositories.py`: `asyncpg.connect` is asserted to receive the
configured `timeout=` kwarg, and a `TimeoutError` from `asyncpg.connect` is
asserted to be treated as an ordinary connect failure (retried, then
`None` with a `db-down` log line) rather than needing special handling.

Validation: `pytest -q` -- **1081 passed** (was 1079; +2 new). Not yet
verified live against a paused container (that reproduction is the owner's
local setup); the two new tests cover the mechanism directly.

`doc_state_sync.py --check` initially failed DOC006/DOC008 after this
entry rotated to the top of the log: `.claude/SESSION_CONTEXT.md`'s
Section 1 dashboard row and Section 6 heading, and `FINDINGS.md`'s header
line, all carried a hand-written "1036" test count untouched since
2026-09-11 -- separate from the `DOCSYNC:STATUS` managed block, which
`--fix` had correctly kept current all along. Corrected both to **1081**
and the module count to the re-measured **48** (was 43); `--check` passes
clean. Left as found and not swept here (a bigger doc pass, out of this
side-task's scope): `FINDINGS.md`'s own "Batch 21 is active" status line,
stale since the same 2026-09-11 date -- Batch 21 closed and Batch 22 is
now active per PLAYBOOK Section 3.

**Addendum, same day:** the underlying gap is recorded as **F-DOCSYNC-12**
-- `--fix` only ever rewrites the STATUS block's own count line, never the
other two fields DOC006 checks (the Section 1 row, the Section 6 heading)
or the FINDINGS header DOC008 checks, so all three can drift indefinitely
until something trips the check and a human corrects them by hand, as
happened here.

### 2026-09-13 - Deezer client (Batch 22 WP-1, Phase 2 begins)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 2 Task 4. No behaviour change -- `scrobblescope/deezer.py` is new and
unused by any caller; Task 5 wires it in as the Spotify-miss fallback.

Plan vs implementation: matched. `search_deezer_album(session, artist,
album)` queries the plain `f"{artist} {album}"` (the filtered
`artist:"..." album:"..."` form favors tribute/cover results per the
plan's probe) and accepts a candidate only when
`normalize_name(candidate_artist, candidate_title)` equals the key built
from the caller's own `artist`/`album` -- never "the first result" as a
guess. `fetch_deezer_album(session, album_id)` calls `/album/{id}` for
metadata and `/album/{id}/tracks?limit=500` for every track's duration,
since `/album/{id}` alone caps at 25 tracks regardless of `nb_tracks`
(pinned with a 30-track fixture). Both share `_fetch_deezer_json`, which
treats Deezer's HTTP-200-with-body errors correctly: code 800 ("no data")
is a terminal miss: `None`; code 4 (quota) retries after a 1s wait via
`retry_with_semaphore`'s existing retry-after path, the same mechanism
Spotify's 429 handling already uses.

`scrobblescope/utils.py` adds `get_deezer_limiter()` (10 req/s, the
existing `_GlobalThrottle` + per-loop `AsyncLimiter` pattern, mirroring
`get_spotify_limiter`); `scrobblescope/config.py` adds
`DEEZER_REQUESTS_PER_SECOND` (default 10 -- Deezer's stated 50 req/5s),
`DEEZER_SEARCH_RETRIES`, `DEEZER_DETAIL_RETRIES` (default 3, matching
Spotify's retry defaults).

Validation: `pytest -q` from the worktree cwd -- **1061 passed** (1054 + 7
new in `tests/services/test_deezer_service.py`: candidate-matching,
no-match, the two HTTP-200-error-code cases, the 25-vs-30-track pagination
case, and two adversarial "the second request never succeeds" cases for
`fetch_deezer_album`, added beyond the plan's own four because a helper
this new needs at least one failure-path test per AGENTS.md's Test
Quality Rules. Task 5 (wire the fallback into the orchestrator) is next.

### 2026-09-13 - PR #232 merged to `test`; branch reset, SHAs remapped

Owner rebase-merged PR #232 into `test` (mergeCommit `812cdde`). GitHub
rebased rather than merge-committed, so every commit on the PR got a new
SHA: `e8de45c`->`d29cc5e`, `85d458f`->`a124b52`, `c5c52fb`->`735c05d`,
`594c705`->`87f3822`, `05a0ff5`->`812cdde`. **Every one of those five old
hashes is quoted earlier in this file, in FINDINGS.md, and in the Claude
project memory for this repo; none of them resolve on this branch
anymore.** Content is unchanged -- `git show <new-sha>` reproduces the
same diff as the corresponding old one -- only the identifier changed.

`feat/batch22-enrichment` (worktree and `origin`) was hard-reset to
`origin/test`'s tip and force-pushed to drop the now-orphaned pre-rebase
commits, per owner direction (reset in place, not a fresh branch --
`AskUserQuestion`, 2026-09-13). PLAYBOOK Section 3's branch name is
unchanged; WP-1 continues on `feat/batch22-enrichment`. Verified after
reset: `pytest -q` -- **1036 passed**; worktree-alignment guard passed (0
behind, 21 ahead of `origin/main`).

A second Graphify review landed on `05a0ff5` (2026-09-14 01:29 UTC, before
the merge) claiming 5 endpoints were "removed" from `scrobblescope/routes.py`
-- a stale-baseline false positive (its own index was "15 commit(s) behind
this PR's base"): the file no longer exists post-WP-0, and all five
endpoints are present, unmoved in content, in `routes/api.py` and
`routes/heatmap_flow.py`. No action taken; not filed as a finding since
it is a bot-indexing artifact, not a repo issue.

### 2026-09-13 - PR #232 bot review triage (Codacy + Graphify)

Triaged both bot reviews on PR #232 (WP-0 + F-B22-1 + AGENTS.md cleanup)
per `/pr-bot-triage`. Codacy (2026-09-13 21:49 UTC, 3 alerts) and Graphify
(2026-09-14 01:08 UTC, 5 inline coupling-delta comments + 5 "worth a look"
escalate findings from the check run) both reviewed the same branch tip.

Acted: `scrobblescope/lastfm.py:68`'s unreachable `return` after
`resp.raise_for_status()` deleted (Codacy, confirmed real -- the call
always raises for any status reaching that branch, so the line never ran).

Deferred, filed as findings: the three `assert job_context is not None`
sites in `album_flow.py` moved verbatim from pre-split `routes.py`
(F-B22-2 -- real hardening gap, `python -O` strips asserts, but out of
WP-0's behaviour-neutral scope); the job-ID-as-bearer-token design across
`/progress`, `/api/unmatched`, and `/heatmap_data` (F-B22-3 -- owner
judgment call, not a demonstrated bug).

Declined, false positives (verified against source, not fixed): Codacy's
XSS claim on `_get_filter_description`'s f-string returns (no `|safe` in
`results.html`/`unmatched.html`; Jinja2 autoescapes regardless of how the
Python string was built). Graphify's two "job slot leak on failed thread
startup" escalate findings (`worker.py`'s `start_job_thread` already calls
`release_job_slot()` in its own `except` before re-raising -- confirmed by
reading `worker.py:31-42`). Graphify's "`check_user_exists` now raises
instead of returning a fallback" escalate finding (that is the PR's own
intentional F-B22-1 fix, not a new regression). Graphify's five inline
"health regression" coupling-delta comments (expected structural churn
from WP-0's module split; the tool's own gate marked the run PASS with no
blocking health regressions).

Verification: `pytest -q` -- **1036 passed**; `doc_state_sync.py --check` and
`pre-commit run` both pass.

### 2026-09-13 - Fixed a broken batch-reference edit; graphify agent sections

Two unrelated uncommitted changes found sitting in the worktree during a
pre-clear sweep, neither written by this session:

1. **`docs/agents/domain.md` had a broken edit**, from an unknown earlier
   process: `BATCH21_DEFINITION.md` had been changed to `BATCH2_DEFINITION.md`
   -- a dropped digit, not a real batch. Fixed to `BATCHN_DEFINITION.md`
   (the file named in PLAYBOOK Section 3), matching the same generalization
   already applied to `docs/architecture/documentation-tooling.md` and
   `docs/ARCHITECTURE.md` earlier today, so it cannot go stale the same way
   again.
2. **Graphify's own tooling had added a `## graphify` section to `AGENTS.md`
   and `.github/copilot-instructions.md`**, matching one already present
   (and already noted, this session) in the gitignored `CLAUDE.md`. Kept:
   the content is operational and non-duplicative with anything already in
   `AGENTS.md`, and reaching every agent's own instructions file (Claude,
   Copilot, and via `AGENTS.md`, everyone else) is exactly the "reach every
   agent" pattern this session's earlier `AGENTS.md` edits argued for. Not
   independently trimmed -- reads as graphify's own multi-agent install
   pattern, not this session's prose.

Validation: `pytest -q` -- **1036 passed** (unchanged).
`python scripts/doc_state_sync.py --check` passes.

### 2026-09-13 - AGENTS.md trimmed, three stale architecture diagrams fixed

Side-task, owner direction after reviewing WP-0. Two parts:

1. **AGENTS.md trimmed.** The Anti-Pattern Registry (items 1-14) carried
   multi-paragraph rationale and worked-incident narratives per item; cut to
   the actionable rule plus its "how to apply" technique where one existed
   (items 11-14 kept their sub-bullets; anecdotal colour and specific past
   numbers were cut). Added item 15, the diagram-trust rule (see below), so
   it reaches every agent working this repo, not only Claude Code sessions
   with the `scrobblescope-bootstrap` skill installed -- this repo is
   multi-agent orchestrated (Codex, Copilot, and as of today DeepSeek).
   Added `docs/architecture/documentation-tooling.md` to the Document Roles
   table as an on-demand "control plane" reference (docsync, worktree
   guard, pre-commit, CI), explicitly kept out of the mandatory bootstrap
   set per the existing token-discipline principle -- it is useful when a
   gate fails unexplainably or before touching that tooling's own source,
   not for ordinary batch work.
2. **Fixed the three architecture diagrams WP-0 left stale**
   (`docs/architecture/runtime-system.md`, `top-albums-sequence.md`,
   `heatmap-sequence.md`), plus `documentation-tooling.md`'s own stale
   `BATCH21_DEFINITION.md` reference (generalized to `BATCHN_DEFINITION.md`
   so it does not go stale again next batch) and `docs/ARCHITECTURE.md`'s
   verification date and batch-scope citation. Fixed by priority: the
   full-stack runtime diagram first (broadest orientation value), then the
   control-plane diagram (has real drift, is itself the doc AGENTS.md now
   points agents at), then the two pipeline sequence diagrams (narrower
   scope, `orchestrator.py`/`routes.py` participant labels only -- the
   sequence of calls itself did not change, since WP-0 was behaviour-neutral).
   `docs/AGENT_DOC_MAP.md` already states "code wins over diagrams"
   (`docs/ARCHITECTURE.md` line 5); it was not itself edited.

Deviation not addressed here: `docs/superpowers/plans/` citations of the old
module paths are dated plan documents and stay as written, per the
dated-entry exemption. `README.md` still owes its Batch 22 pass to WP-5, as
recorded in WP-0's own log entry.

Validation: `python scripts/doc_state_sync.py --check` passes.

### 2026-09-13 - Username validation no longer fails open (F-B22-1)

Side-task, found during owner manual testing of WP-0's running app.
`check_user_exists` (`scrobblescope/lastfm.py`) swallowed every exception --
timeout, Last.fm rate limit, malformed body, any non-200/404 status -- and
returned `exists: True`. `/validate_user` and `_validate_heatmap_user` read
that as a verified account, so a transient Last.fm failure showed a green
checkmark for arbitrary, unregistered usernames. Fixed by letting the
exception propagate; every caller already had its own try/except, so
`/validate_user` and `_validate_heatmap_user` now correctly answer 503
"Validation service unavailable" instead, and `results_loading` (which
already tolerated this check failing) is unaffected. Two regression tests
added in `tests/services/test_lastfm_service.py`. Finding: F-B22-1,
`FINDINGS.md` "Resolved this batch". `pytest -q` -- **1036 passed**.

### 2026-09-13 - Batch 21 closed (WP-8 complete)

- Owner end-to-end pass in Firefox: **done**, 2026-09-13, on the running app
  at 4b4965b. It covered every page in both themes and the saved images from
  results and from the heatmap.
- Two defects the pass found, both fixed before close-out:
  - The saved heatmap drew its own header, "LISTENING HEATMAP . LAST 365
    DAYS" over "A year of <name>" in italic accent, while the page had moved
    to the possessive headline in plain ink. `renderHeadline`'s docstring
    still described the old wording, which is how the two drifted.
  - The saved legend was a bare gradient: nothing in the file said which end
    meant more listening.
  Both are `4b4965b`. The export now reads the page's headline, eyebrow and
  legend captions, and the gate saves a real image and compares what the
  canvas drew.
- WP-8's other deliverables landed in `85e7511`, recorded in the entry above.
- The frontend and accessibility audit WP-8 charters is **not** part of this
  close-out. The owner moved it to Batch 23's close-out on 2026-09-13 so it
  runs once over the final UI; `BATCH21_DEFINITION.md` WP-8 carries the
  ruling and Batch 23's plan carries the obligation.
- Validation at close: `pytest -q` -- **1034 passed**;
  `python scripts/dev/frontend_gate.py` -- **28 checks passed in 50 runs**
  across chromium and firefox; `doc_state_sync.py --check` exit 0;
  pre-commit passed. CI passed on `85e7511`
  (run 34778729537).
- Next: Batch 22, enrichment providers. It opens on its own branch, which
  PLAYBOOK Section 3 must name before any commit, or the worktree guard
  raises WT003.

### 2026-09-13 - Legacy framework stack retired (Batch 21 WP-8 sweep)

- Scope: the WP-8 sweep, run before the backend batches on the owner's ruling
  of 2026-09-13. The frontend and accessibility audit is not here; it moved to
  Batch 23's close-out so it runs once over the final UI.
- Removed: the default-on `legacy_css` block and the `bootstrap_js` block in
  `templates/base.html`, the eight per-page opt-outs that answered them, and
  `static/css/global.css`. WP-8's deterministic check,
  `git grep -nE "bootstrap|data-bs-|bs-(toggle|target|dismiss)" -- templates static`,
  now returns nothing. No other stylesheet is unreferenced: every file in
  `static/css/` is loaded by a template or compiled by the build.
- The theme is written once. `static/js/theme.js` no longer writes
  `.dark-mode` on `<body>`; `data-theme` on the root element is the only
  signal.
- **A regression the sweep would have shipped.** `static/js/heatmap.js`
  observed `<body>` for that class to repaint zero-count cells, because a cell
  carries its colour as an SVG `fill` attribute and a presentation attribute
  does not resolve a custom property. Retiring the class silently froze the
  cells at their light colour on a dark page, and the whole gate stayed green:
  every other theme check reads CSS. `docs/architecture/runtime-system.md` had
  recorded this dependency and named the fix; reading it is what caught this.
- Guards added, each seen to fail first: the gate's
  `check_heatmap_zero_cells_follow_theme` toggles the theme and compares each
  zero cell against `--heatmap-empty` (it failed with `#c8bfad` in both themes
  before the observer moved), and two tests in `tests/test_template_shell.py`
  pin the retired stack and the single theme write.
- Linting disposition recorded: `BATCH21_DEFINITION.md` WP-8 carries the
  decision, and the `AGENT_NOTES.md` gap entry now points at it instead of
  reading as an open commitment.
- Docs: README's status section, `docs/architecture/runtime-system.md` (both
  bullets this change falsified), and the `tests/test_template_shell.py`
  docstring.
- Validation: `pytest -q` -- **1034 passed**. `python scripts/dev/frontend_gate.py`
  -- **27 checks passed in 49 runs** across chromium and firefox.
- Forward guidance: what remains before Batch 21 closes is the owner's
  end-to-end pass in Firefox, including the saved image in both themes, and
  the close-out commit. Batch 22 opens on its own branch, named in Section 3
  first.

### 2026-09-12 - Documentation reconciled to the shipped unmatched page

- Scope: the documentation-first step the owner chose before the WP-7 table
  repair. Corrected claims that contradicted the shipped unmatched page, by class
  rather than by instance, using two subagents on disjoint file sets.
- The approved spec: its Outcome and Verification paragraphs still described
  full-width stacking, and the second credited the frontend gate with proving
  it; its disclosure paragraph described one button and no step. All now state
  side-by-side panels, the 25-row step and the collapsing back-to-top control.
- `PLAYBOOK.md` Section 3 carried two stale live test counts, 1022 and "the
  925-test suite"; the second now defers to the next-action bullet. Its conflict
  note pointed at the one spec sentence already corrected, not at the two stale
  sites; it now records the conflict as closed.
- `BATCH21_DEFINITION.md`: the stacked-layout prescription, "is next" for shipped
  work, "two reason cards" where three ship, and a false claim that
  `unmatched.css` hardcodes `--header-bg: #6a4baf`. `README.md`: two passages
  telling readers the unmatched report still runs Bootstrap. `FINDINGS.md`:
  F-B20-4's stale status, and F-B21-52's grep instruction, which could not find
  whole-number dead steps.
- `docs/design/RECONCILIATION.md`: section 11 still said `results.css` and
  `unmatched.css` were unconverted to rem; sections 13 to 15 record the frozen
  snapshot's 1180px measure, card styling and two-state expander as overrides,
  since `docs/design/` is byte-frozen apart from that file.
- Plans under `docs/superpowers/plans/`: normative "must report 1020 passed"
  baselines now defer to SESSION_CONTEXT Section 1; the WP-7 plans and the
  unverified gemini plan carry supersession records for the side-by-side ruling
  and the 25-row step. Dated log excerpts inside them were left as records.
- Deviation: F-DOCSYNC-11 filed. Same-date precedence ranks this morning's live
  side-task entry above the WP-7 entry written after it, so the WP-7 entry's
  count could not become authoritative and DOC006 and DOC008 failed. This entry
  carries the working tree's full-suite result instead.
- Validation: `pytest -q` -- **1028 passed**, on the working tree that also holds
  the WP-7 table repair and the F-B21-52 guard.
- Forward guidance: dated Section 4 entries and log excerpts quoted inside plans
  are point-in-time records and stay as written.

### 2026-09-12 - Planning records preserved, and the ignored scratch root cleaned

- Scope: preserve the untracked planning record ahead of Phase 2 in
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`,
  and empty the `scratch/` root. No product code changed in this entry.
- Committed: the four untracked plans under `docs/superpowers/plans/`, plus the
  Progress corrections on the reconciliation plan itself. Keeping
  `gemini_implementation_plan_unverified.md` here closes that plan's open
  question 2 in favour of keeping.
- Deviation, owner-directed: live mode was repaired mid-session, then reverted.
  The skill's pinned engine `0.1.0` is quarantined by Windows Defender; the
  published `0.1.2` release is not, and its hash matches the release's own
  `.sha256` sidecar. The two template edits made under live are reverted, and
  the helper, poll and session are stopped and discarded.
- Cleaned, owner-directed: `scratch/` held 499 files and 31.05 MB of session
  debris and is empty now. The `deeper-reading-batch21-plan/` run root went
  with it. The durable summary of that run is the tracked
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`, which states in
  its own text that the run root is untracked and is not committed.
- Validation: `pytest -q` -- **1026 passed**; `pre-commit run --all-files` with
  every hook passing; `doc_state_sync.py --check` exit 0, with the root
  `BATCH21_DEFINITION.md` warning expected while Batch 21 is active.
- Owner rulings recorded: the eyebrow labels are intended; any reference
  placing an eyebrow above its headline is stale; headline emphasis stays and
  is scoped to the index hero and `results.html`.
- Forward guidance: begin Phase 2 at step 11 (`DESIGN.md`), not at the
  spec-versus-ruling conflict, which is already closed.
  `static/js/heatmap.js:176` is the one stale eyebrow-above comment and is
  corrected inside that unit. Two harness notes: this shell runs with
  `$ErrorActionPreference=Stop`, so a tool that writes to stderr looks like a
  hard failure until that is set to `Continue`; and the git `pre-commit` hook
  resolves `pre-commit` from `PATH`, so the primary venv must be on `PATH` or
  every commit is blocked.

### 2026-09-11 - Artwork restored in the below-threshold panel

- Scope: a review observation that the artwork container is excluded for
  `below_threshold` items, contradicting the spec's "consistent 40px mobile or
  44px desktop artwork" and breaking the side-by-side rhythm.
- Root cause, verified: `templates/unmatched.html` wrapped the whole artwork block
  in `{% if reason_key != 'below_threshold' %}`. The stylesheet was correct all
  along -- `.unmatched-artwork` is 2.5rem, and 2.75rem at >=768px. The guard
  conflated "these albums have no album image" (true: they are partitioned before
  Spotify) with "these rows get no artwork"; the block's fallback branch needs only
  the artist name, which the payload carries (`unmatched.py:79-80`).
- Plan vs implementation: a below-threshold branch now renders the sized monogram
  placeholder. Variant chosen by the owner: no `data-artist-image`, so the panel
  adds no network call and partitioned albums stay at zero cost. The change is
  additive -- nine lines above the existing guard, nothing removed.
- Why no gate caught it: `frontend_gate.py` asserted the cover on `rows[0]` of ONE
  group, the release_scope panel. It now asserts a sized `.unmatched-artwork` in
  EVERY `.unmatched-group`, which is the class fix rather than the instance.
- Evidence, both guards proved to fail before passing: with the new branch removed,
  `tests/test_routes.py::test_unmatched_view_renders_artwork_in_every_reason_group`
  fails, and the frontend gate reports "unmatched group 0 renders no artwork
  container" for desktop and mobile. Restored, the test passes and the gate reports
  26 checks passed in 47 runs. `pytest -q` -- **1026 passed**.
- Deviation: none. This is a defect the PR review round surfaced and fixed inside
  the same round.

### 2026-09-11 - Deterministic tie-breaks on the three cap-path sorts


- Scope: a PR review comment on `scrobblescope/orchestrator.py:131` and `:703`
  asked for a stable tie-breaker on the sorts that choose albums for the
  `_MAX_ALBUM_CAP` safety cap, so tied play counts cannot let insertion order
  decide which albums are kept.
- Plan vs implementation: all three cap-path sorts now order by descending play
  count and then by normalized key. The reviewer named two; the third is the
  playcount pre-slice in the same function, added as the same class. The
  now-unused `cast` import was removed.
- Evidence: the fix's failure mode was OBSERVED, not assumed. With the three keys
  reverted to `reverse=True`, all three new tests fail; restored, all three pass.
  `pytest -q` -- **1025 passed**, up from 1022 with the three new tests.
- Deviation: none in scope, and one correction to record. The determinism the
  reviewer worried about was not reachable before this change: the cap's input is
  built by iterating page results in order, `partition_albums_by_threshold`
  preserves that order, and the sort is stable. So this makes the guarantee
  structural instead of inherited from a four-link chain nothing pinned, rather
  than fixing a live bug. Recorded so a later reader does not overstate it.
- Forward guidance: two same-class sibling sorts remain at `orchestrator.py:538`
  and `:540`, in `_build_results`' user-visible ordering. They were NOT fixed
  here: the review did not name them, their input order derives from `cache_hits`
  and was not established as nondeterministic, and every further site costs its
  own fixture and its own claim. Bounded deliberately rather than chased -- the
  same reasoning that parked the dated-record policy sites. A future pass wanting
  the class closed should do all remaining sites in one edit.

### 2026-09-11 - Approved spec reconciled with the owner's side-by-side ruling


- Scope: the approved spec
  `docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`
  still directed "stacked, full-width reason sections" while the owner ruled
  side-by-side on 2026-09-11 and both the shipped page and three frontend-gate
  assertions implement side-by-side. A PR review comment raised it; it was the
  last stale voice on that conflict.
- Plan vs implementation: the directive now reads as side-by-side panels and
  records the supersession, the owner's words and the date. The rest of the spec
  is unchanged and still accurate.
- Deviation: none. This is the reconciliation the design-system plan's Phase 2
  named ("Record that the owner superseded its ... line with the side-by-side
  ruling"); it sits outside the document-orderliness series' declared scope and is
  logged here rather than folded silently into that series.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0 with
  only the expected root `BATCH21_DEFINITION.md` warning.
- Forward guidance: the design-system plan's Phase 2 still lists this edit among
  its work. It is now done, so that entry can be retired when Phase 2 runs;
  `RECONCILIATION.md` gains a pointer to the same ruling in that pass.

### 2026-09-11 - Two siblings closed, and the dated-record policy scoped


- Scope: the scoped re-review of the fix wave `50cffdd` ruled that two
  same-class siblings belonged to that wave, and the owner directed it be
  extended by one follow-up commit. Three document edits: a rationale reworded
  in a dated entry, the work order's retired provenance pin, and the policy
  clause in the side-task archive.
- Owner ruling on the policy fork: a dated entry's recorded measurements are
  frozen -- a test count, a date, an observed result stands as written, because
  editing one falsifies the record rather than correcting it -- while its
  rationale prose may be corrected when it is shown false. `50cffdd` had
  replaced the archive's rationale with an absolute clause that condemned that
  wave's own edit of a dated entry, so it contradicted itself; the clause is
  now scoped to the ruling.
- Sibling (a), precision rather than retraction: the re-review classified the
  stale-range bullet in the dated entry "Architecture rebuild landed, and its
  stale docsync range corrected" as the same falsified claim finding 2
  corrected. The controller disproved that on authorship timing: the rebuilt
  `docs/architecture/documentation-tooling.md` was authored at 2026-09-11
  23:15:13, and `501a7b6` corrected the range in `AGENTS.md` at 2026-09-12
  00:57:38, one hour forty-two minutes later, so at write time the document
  agreed with the range's authority. The dated records finding 2 left alone are
  the opposite case: DOC012's 2026-08-26 enforcement had already made them
  stale on their own dates. The sentence is true as written, so nothing was
  retracted; it now reads "It matched `AGENTS.md` when written", which removes
  the ambiguity about what "correct" meant.
- Sibling (b): the work order's Task 2 Step 3 still reproduced the retired
  sha256 and byte-count pin for a plan revision that was never committed, so no
  contributor could check it. It now names `c277728`, the commit that published
  that plan, and records that the traversal bound the pre-publication revision
  -- the precedent the traversal report already sets.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (3), recorded as the actual set: `PLAYBOOK.md` (this entry
  and the sibling (a) reword), the work order
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`,
  and `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which carries the
  scoped policy clause and the rotation this entry forced -- the oldest
  non-current entry, the one sibling (a) lives in, moved into the archive, so
  the correction travels with it. docsync demanded no further path: this entry
  carries the 1022 claim the corpus already held, so `FINDINGS.md` and
  `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: a future agent correcting a dated entry changes rationale
  only, and leaves every measured figure, date and observed result as written.
  One absolute statement of the old form survives, in this file's entry "Task 8:
  the guard's own spelling, a false rationale, a live count", which gives the
  same reason as "editing one falsifies the record rather than correcting it".
  That entry is a dated record of the wave's own reasoning, so it was left as
  written; a pass that wants one form in the corpus should scope it by the same
  ruling.

### 2026-09-11 - Task 8: the guard's own spelling, a false rationale, a live count

- Scope: the six items of the final whole-branch review of this series -- three
  Important findings and three one-line recommendations, all of them documents
  except one test assertion. No application behaviour changed. One gate
  behaviour moved: Guard A's pattern now blocks on a second spelling of the
  retired range. The review's verdict was "ready to merge with fixes" over the
  23 commits from `b5b2c89` to `0c87eaa`.
- Important 1: Guard A's pattern -- the `[[retired]]` declaration named "the
  docsync integrity range ends at DOC011", at `.docsync.toml:616` -- could not
  match the spelling of the instance it was built for. The declaration was
  written for `docs/architecture/documentation-tooling.md:93`'s backtick-split
  `` `DOC001`-`DOC011` ``, and the pattern required the contiguous literal. The
  pattern now reads `(?:reports|returns|states).{0,40}DOC001`?-`?DOC011`, so
  both spellings match and nothing else does. The declaration's comment claimed
  the pattern "requires the literal `DOC001-DOC011` phrase", which the widening
  falsifies; it now names both spellings and says why the backticks are
  optional.
- NO LIVE RED STATE WAS AVAILABLE for that widening, and none was manufactured
  to produce one. Task 6 corrected the backtick-split instance in `cc987f5`,
  before Task 7 designed the guard, so at calibration time the only surviving
  example of the defect was the plain form inside a plan's spent before-block --
  which is why the pattern was fitted to the wrong spelling. The evidence is a
  five-case probe rather than a red-then-green cycle. Measured through
  `docsync.declarations._declared_matches`, old pattern then new: backtick-split
  `` It reports typed `DOC001`-`DOC011` issues `` False then True; the plain
  `It reports typed DOC001-DOC011 issues` True then True; a corrected
  `` `DOC001`-`DOC012` `` line False then False; the true
  "**DOC009 to DOC011 are declared, not hard-coded.**" False then False; and a
  past-tense record naming the old range False then False.
- Important 2: the entry named "DocSync integrity range corrected to DOC012"
  justified leaving two dated records alone by saying they "were correct when
  written", and the ledger falsified it: DOC012 has been enforced since
  2026-08-26 (`1c78aa0`), so `docs/history/reports/GRAPHIFY_AUDIT_2026-09-04.md`
  and the archive entry that carries the same range already stated a retired
  range on their own dates. The decision to leave them stands. The reason is now
  the policy -- a dated record is a point-in-time entry, so editing one falsifies
  the record rather than correcting it -- which holds whether or not the range
  it states was stale on the day it was written.
- Important 3: `PLAYBOOK.md:189`, in Section 3's live next-action bullet, read
  **1020 passed** while the suite is 1022. A live bootstrap field that no gate
  reads, which is why it drifted: DOC006 and DOC008 cover the named
  SESSION_CONTEXT fields and the `FINDINGS.md` header, and DOC012 reads only
  below the execution-log heading. It now reads **1022 passed** with the
  measurement date beside it.
- The three recommendations. The traversal report's provenance header no longer
  pins the traversed revision by sha256 and byte count: that revision was never
  committed, so no contributor could ever check the pin, which is the
  unreachable-citation shape Anti-Pattern 11 names. It now records that the
  traversal bound the pre-publication revision that `c277728` published. The
  facade test at `tests/scripts/dev/test_frontend_gate_colour.py:194` asserts
  `is` identity rather than `callable()`, so a facade exporting an unrelated
  function of the same name fails it; the test is parametrized, so extending it
  added no test function and the suite count did not move. And the
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`
  work order gained a section after its task list naming Task 6 and Task 7 as
  the owner-directed additions, so it stops understating the series.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning. The probe
  above was re-run after the widening, with the pattern read back from
  `.docsync.toml`, and returned the new column unchanged.
- Committed paths (6), recorded as the actual set: `.docsync.toml` (the widened
  pattern and the comment above it), `PLAYBOOK.md` (this entry and the Section 3
  count), `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`,
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`,
  `tests/scripts/dev/test_frontend_gate_colour.py`, and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which this entry's arrival
  pushed over the four-entry window: the reworded Important 2 rationale rides in
  the rotated entry, so the correction is preserved in the archive rather than in
  Section 4. docsync demanded no further path: this entry carries the 1022 claim
  the corpus already held, so `FINDINGS.md` and `.claude/SESSION_CONTEXT.md`
  needed no change.
- Forward guidance: Guard A now covers both spellings of the retired range, so
  the live coverage gap it had is closed -- but it still matches *wording*, and
  a document stating a fresh-phrased range behind the code passes it; Guard B is
  the check for that, and the two do not subsume each other. Two residuals the
  review did not name are reported rather than fixed here, because the brief
  scoped this wave to its six items: the Task 6 entry named "Architecture rebuild
  landed, and its stale docsync range corrected" still carries the same "correct
  when written" rationale about a document, and the work order's Task 2 Step 3
  still reproduces the report's old provenance pin in its instruction block.

### 2026-09-11 - The docsync code range is guarded, and its stale copy removed

- Scope, four parts in one owner-directed task: declare the retired DOC011
  range in `.docsync.toml` and remove the one live site it exposed; add a
  derived test comparing the range `AGENTS.md` states with the highest code the
  package raises; close the design-system plan's commit table; record it here.
  No application behaviour changed, and the docsync gate gained one check.
- Two guards, because there are two failure modes and neither subsumes the
  other. Guard A is a `[[retired]]` declaration whose pattern matches the
  PRESCRIPTIVE phrasing, so a stale range re-appearing in any live document
  blocks. The pattern was widened during review from the `typed` form alone to
  any of the three present-tense verbs it lists, which is what caught Task 5's
  preamble in the remediation plan; a still wider form had been measured and
  rejected for flagging true sentences instead. It catches stale
  *wording* only: a document stating a range merely behind the code, in fresh
  wording, passes it. Guard B is
  `test_stated_docsync_range_matches_the_highest_code_raised`, which asserts
  through a shared `_ranges_agree` predicate that `AGENTS.md`'s stated upper
  bound equals the highest code literal in
  `scripts/docsync/*.py`; it catches a documented range that is behind the
  code. Guard B is the one that would have caught the original drift, and it
  already catches a `DOC013` added without the documentation following -- a
  case Guard A cannot see, because such a document quotes no retired range.
- Red state observed before the fix. With the declaration in place and the plan
  untouched, `doc_state_sync.py --check` exited 1 with ERROR DOC011 against
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md:602`,
  the spent before-block of Task 5's Step 3. The narrow pattern matched exactly
  one live site, which is what its calibration predicted; a broader form had
  been measured and rejected for flagging true sentences instead. Replacing that
  block with a note naming the commit that applied the correction, `501a7b6`,
  and quoting neither wording, returned `--check` to exit 0. Widening the
  pattern during review put it back to exit 1 with a second live diagnostic, on
  Task 5's preamble in the same plan; a past-tense rewrite of that sentence
  cleared it, and `--check` returned to exit 0 again.
- Guard B's mutation proof, `test_stated_range_helper_rejects_a_stale_range`,
  asserts both failure modes through the same `_ranges_agree` predicate the
  corpus test uses: a fixture document still stating the retired range beside a
  source raising `DOC012`, and the real `AGENTS.md` beside a source raising
  `DOC013`. Without them the corpus test would still pass if both helpers
  returned one constant. The fixture is assembled at runtime, because a literal
  copy of the retired range sits outside the declaration's `scan` list by file
  type alone, and widening that list would otherwise make guard A fail on the
  fixture that proves it works.
- The design-system plan's commit table gained three rows -- `c277728`,
  `95e0896`, `cc987f5` -- the commits its own progress section already tracked
  as dischargeable items. Rows for commits that merely touch that plan were not
  added, so the table stays bounded to its window.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning. The two
  new tests are why the count moved from 1020, so `.claude/SESSION_CONTEXT.md`
  Section 1 and the `FINDINGS.md` header moved with it.
- Committed paths, in `d41f05c` (8): `PLAYBOOK.md` (this entry), `.docsync.toml`,
  `tests/test_docsync_integrity.py`, both plan documents
  (`docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`,
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`),
  `.claude/SESSION_CONTEXT.md`, `FINDINGS.md`, and the rotation this entry
  forced in `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. The review round
  that widened the pattern committed six of those same paths -- this entry,
  `.docsync.toml`, `tests/test_docsync_integrity.py`, `FINDINGS.md` and both
  plans -- and its `--fix` run rotated nothing. The three
  untracked plan and design files owned by other efforts stayed untracked.
- Forward guidance, all of it still open. Guard B compares the upper bound
  only, so the lower bound the same sentence states is unchecked, and the
  retired-range pattern assumes the range is stated in the present tense. Guard
  B's literal scan covers `scripts/docsync/*.py` alone, so a code first raised in
  another module would need that glob widened. Nothing in the toolchain parses
  Mermaid, so a diagram's labels stay unchecked prose. `F-B21-57` records a
  latent index shadowing in `check_retired`, where a declaration-shaped
  diagnostic survives on statement order alone. The `--fix` run rotated the
  oldest non-current entry into the archive to hold the window at four.

### 2026-09-11 - Task 6 review fixes: diagram claims and the handoff list

- Scope: the five findings of the Task 6 review of `cc987f5` and `29486d8`, all
  documentation, none touching behaviour or a gate. (1) The design-system plan's
  handoff list still presented three landed commits as staged or unstaged,
  contradicting its State line twenty lines above. (2) A Mermaid node in
  `docs/architecture/documentation-tooling.md` named pre-commit's code checks
  `ruff, flake8, bandit`, when this repository runs ruff alone. (3) The Task 6
  entry immediately below counted "the four citing edits" over a list of three.
  (4) That entry cited "the six architecture documents above" without naming one
  of them. (5) The same tooling document put pip-audit before the frontend gate
  in CI and omitted CI's deliberate `worktree-alignment` skip.
- Toolchain evidence, read from the configuration rather than assumed:
  `.pre-commit-config.yaml` defines ten hooks -- ruff-check, ruff-format,
  trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict,
  detect-private-key, doc-state-sync-check, tailwind-css-drift and
  worktree-alignment -- and its own comment records that ruff replaces black,
  isort, autoflake and flake8. Neither flake8 nor bandit is pinned in
  `requirements-dev.txt`, defined as a hook, or named in a workflow step; the
  surviving mentions are prose records and one comment in
  `scrobblescope/spotlight.py`. The node now reads `ruff check, ruff format`.
- CI order, read from `.github/workflows/test.yml`: pre-commit with
  `SKIP: worktree-alignment`, then pytest with coverage, then the Playwright
  install, then the frontend gate, then advisory pip-audit last. The prose now
  states that order and the skip.
- The contradicted list, repaired with discharge markers rather than a retitle:
  each of its three items names the commit that discharged it, which is what
  "Where to pick up" already does. A retitle alone would have left "Unstaged:"
  standing with no outcome beside it, the defect the Task 3 review raised for
  the sibling Section 3 bullet.
- Validation: `pytest -q` -- **1020 passed**; `pre-commit run --all-files` --
  all 10 hooks passed with no files modified; `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (4), recorded as the actual set: `PLAYBOOK.md` (this entry),
  `docs/architecture/documentation-tooling.md`, the design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`),
  and the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the Section 3
  commit-debt entry out of the active window.
- Forward guidance: nothing checks a diagram against the workflow it describes,
  so an edit to the hook set or to the CI step order has to move both this
  document's Mermaid node and its CI sentence by hand.

### 2026-09-11 - Architecture rebuild landed, and its stale docsync range corrected

- Scope, three parts in one owner-directed task: correct the stale integrity
  range in the rebuilt `docs/architecture/documentation-tooling.md`; commit the
  owed architecture-diagram rebuild, unstaged in this worktree since 2026-09-11;
  and sweep the two documents that still tracked that rebuild as uncommitted
  work, so nothing claims owed work that has landed.
- Owner direction, outside the remediation plan: this task is not one of the
  plan's WPs, and the plan excluded the rebuild as owed work owned by another
  document. Landing it had to precede the docsync-range guard, because that
  guard cannot ship while a live stale instance exists, and the instance lived
  inside this uncommitted work -- correcting the line alone would have dragged
  52 unstaged lines into a guard commit. Owner ruling, 2026-09-11.
- The stale range: the rebuilt `documentation-tooling.md:93` read "reports typed
  `DOC001`-`DOC011` issues". It matched `AGENTS.md` when written and a later
  correction made it stale: `501a7b6` corrected the same range in `AGENTS.md`, and this
  file had not yet entered the repository. The sweep measured the class in four
  spellings (`DOC001-DOC011`, `` `DOC001`-`DOC011` ``, `DOC001 to DOC008`, and
  the short form `DOC009-011`); this was the only live statement of the range
  with a wrong upper bound, and every other hit is true as written, a quotation
  of the old text, or a dated record.
- Deviation, forced by commit identity: the brief staged the plan's State line
  and Section 3's owed-work bullet in the same commit as the rebuild, each
  citing the rebuild's SHA. A commit cannot cite its own SHA, because the
  citation is part of the tree that SHA hashes. The rebuild therefore landed as
  the first commit of this task, and the citing edits -- the plan's State line,
  its previously-owed item 2, and Section 3's bullet -- landed in the
  immediately following commit, which names the rebuild. No brief text was
  reworded; only the commit boundary moved.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  10 hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0
  with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (9), recorded as the actual set: the six architecture
  documents -- `docs/ARCHITECTURE.md`,
  `docs/architecture/development-cycle.md`,
  `docs/architecture/documentation-tooling.md`,
  `docs/architecture/heatmap-sequence.md`,
  `docs/architecture/runtime-system.md`,
  `docs/architecture/top-albums-sequence.md` -- this entry in `PLAYBOOK.md`, the
  design-system plan whose owed-work notes this task discharged
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`),
  and the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change. The nine
  paths span two commits, per the deviation above; the six architecture
  documents and this entry are in the first.
- Forward guidance: the rebuild is the last owed commit before Phase 2, so
  Section 3 now reads "none". The docsync-range guard can land unexempted,
  because no live stale instance remains in the corpus.

### 2026-09-11 - DocSync integrity range corrected to DOC012

- Scope: `AGENTS.md` stated the integrity range as `DOC001-DOC011`, while
  `scripts/docsync/integrity.py` defines and raises `DOC012` -- a pass claim in
  the log must carry the bold form the count authority reads. The range drifted
  for the same reason it drifted the first time: nothing in the corpus asserts
  that the stated range equals the codes the code raises.
- Plan vs implementation: both `AGENTS.md` edits landed as written. The list
  item now reads `DOC001-DOC012`, and its parenthetical records the second
  drift, so the sentence that already held the first instance of this class now
  holds both. The added paragraph sits after the DOC009 to DOC011 bullet list
  and records that DOC012 is implemented directly rather than declared, which
  keeps the paragraph above it -- "DOC009 to DOC011 are declared, not
  hard-coded" -- true as written.
- Sweep, per Anti-Pattern 11: exactly one live document stated the range
  wrongly, and it is the one corrected here. Left deliberately, with reasons:
  `FINDINGS.md` records that `AGENTS.md` *used to* say `DOC001-DOC006` and
  remains true as history; the dated records in
  `docs/history/reports/GRAPHIFY_AUDIT_2026-09-04.md` and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` are exempt by policy -- a
  dated record's recorded measurements are frozen, because editing one
  falsifies the record rather than correcting it, and that holds whether or
  not the range it states was already stale on the day it was written, while
  its rationale prose may be corrected when it is shown false, as this wave's
  own edit of a dated entry did; and three sites that describe
  the declared mechanism rather than the range -- the WP-3 plan's "DOC009 to
  DOC011 exist and are declared", the comment at
  `scripts/docsync/integrity.py:1017`, and the `declarations.py` line in
  `.claude/SESSION_CONTEXT.md` -- all remain true, because DOC012 is
  implemented in `integrity.py` and is not declared.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning. The
  guard, `Select-String -LiteralPath 'AGENTS.md' -Pattern 'DOC001-DOC012'`,
  returned 0 matches before the edit and 1 after.
- Committed paths (3), recorded as the actual set: `AGENTS.md`, this entry in
  `PLAYBOOK.md`, and the rotation it forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the
  exhaustive-traversal entry out of the active window. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: the range is still unchecked. A guard asserting that the
  stated range equals the codes the code raises would have caught both drifts,
  and remains the fix for the class rather than for this instance.

### 2026-09-11 - Agent-session analysis trees ignored

- Scope: `.agent/`, `.impeccable/`, `.qlty/` and `scratch/` were untracked and
  also unignored, so every `git status` carried 500-odd paths and the only
  guard against sweeping them into a commit was the ban on `git add -A`.
- Plan vs implementation: the four patterns landed with a comment recording why
  each is untracked, and why the singular `.agent/` is deliberate beside the
  vendored `.agents/`.
- Deviation: the owner was offered this task as optional because it does not
  come from the traversal; it was taken.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0.
  The untracked sweep fell from 500-odd to 0, and the tracked file list was
  unchanged.
- Committed paths (3), recorded as the actual set: `.gitignore`, this entry in
  `PLAYBOOK.md`, and the rotation it forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the Task 1
  and Task 1b review-repair entry out of the active window. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: the traversal run root now lives under an ignored path. Its
  report was committed first, so the record survives even if the run root is
  deleted.

### 2026-09-11 - Section 3 now carries the commit debt

- Scope: the commits owed before Phase 2 were recorded only in the design-system
  plan's Progress section, so an agent bootstrapping from `AGENTS.md` reached the
  specification conflict Section 3 already carries but never learned that
  commits were owed. Section 3 now names the debt, points at the traversal
  record, and the remediation plan's Task 3 Step 3 was corrected so it stops
  instructing the stale wording.
- Plan vs implementation: both Section 3 bullets landed as written, inserted
  directly after the existing "Next action:" bullet. The bullets name the
  outstanding architecture-diagram rebuild and record the two already-landed
  commits, `95e0896` for the F-B21-51 slice-1 refactor and `c277728` for that
  plan's own move. The traversal-record citation resolves because Task 2
  committed the report.
- Deviation, controller-directed: the brief's Section 3 bullet text was written
  before `95e0896` and `c277728` landed, so it still described the F-B21-51
  slice-1 refactor as staged and the design-system plan's own move as
  uncommitted. Following it verbatim would have written a false statement into
  the live bootstrap section, so the corrected wording was used, and the same
  correction was applied to the remediation plan's Task 3 Step 3 so the plan no
  longer mandates the stale text. Nothing else in that plan changed.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  10 hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0
  with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (3), recorded as the actual set rather than a smaller claimed
  one: `PLAYBOOK.md`, the remediation plan whose Task 3 Step 3 this commit
  corrected
  (`docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`),
  and the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the
  design-system plan's own path-correction entry out of the active window.
  docsync demanded no further path: this entry carries the 1020 claim the corpus
  already held, so `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no
  change.
- Forward guidance: keep Section 3's bullets free of counts. Name each owed
  item, so the next addition cannot make the section silently wrong.

### 2026-09-11 - Traversal record tense repaired after the Task 2 review

- Scope: the review of Task 2's commit `106f941` found two tense defects in
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`, both of one
  class. Its Section 7 asserted as current three passages of the design-system
  plan that `c277728` and `9cb3662` had already rewritten, and its Section 9
  past-tensed the heatmap-fill limitation the plan still states.
- Plan vs implementation: both edits landed as written. Section 7's framing
  sentence and its closing narration now report what the traversal found at the
  revision it bound, plus the one controller-authorised sentence naming
  `c277728` and `9cb3662` and recording that the finding no longer holds at
  HEAD. Section 9's limitation is present-tense again, matching the plan and
  the report's own Section 8. The three quoted passages, every chunk ordinal
  and the provenance header are unchanged.
- Deviation: none. No other section of the record was touched.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0,
  with the expected root `BATCH21_DEFINITION.md` warning.
- Forward guidance: the report records a traversal bound to the plan's
  pre-repair revision, so its findings describe that revision and not HEAD. A
  reader who needs current state must re-check the plan; Section 7 now names the
  two commits that answered it.

### 2026-09-11 - Exhaustive plan traversal recorded

- Scope: an exhaustive traversal of the Batch 21 design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`)
  was run with the `deeper-reading` skill on 2026-09-11. Its findings are
  recorded at `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- Plan vs implementation: 70 of 70 canonical chunks carried a byte-anchored
  evidence verdict, 192 assertions in total, with zero `non_match` verdicts and
  70 ordered `chunk_verified` events. One assertion failed its span check on the
  first attempt and was repaired by re-quoting it from the chunk; the failure,
  its diagnosed cause and the recovery are recorded in the report and in the
  run root's failure ledger.
- Deviation: none. The report is a durable copy of a working artifact, not new
  analysis.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0.
  The report is ASCII-only, measured at 0 bytes above 0x7F.
- Committed paths (3), recorded as the actual set: the report
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`, `PLAYBOOK.md`, and
  the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the
  architecture-diagrams entry out of the active window. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: the machine proof stays in `scratch/`, which is untracked.
  If the run root is deleted, the report remains the record and its chunk
  ordinals stop being checkable against the manifest. Delete it only knowingly.

### 2026-09-11 - Document repairs from the Task 1 and Task 1b reviews

- Scope: two task reviews of the document-orderliness remediation found
  defects that are all documentation, and the owner approved repairing them in
  one pass rather than two fix loops, because none of them touches the code
  committed in `95e0896`. Four families: (1) the design-system plan's Progress
  section contradicted itself, still naming work that `95e0896` and `c277728`
  had discharged; (2) the remediation plan's own defects -- Task 1's guard
  expectation, Task 1's impossible staging step, Task 4's unbolded validation
  template, and a new Task 5 for the undocumented `DOC012` range; (3) two
  `PLAYBOOK.md` entries that denied behaviour their own commits had landed;
  (4) `.claude/SESSION_CONTEXT.md` Sections 3 and 4, which never listed
  `scripts/dev/_frontend_gate_colour.py`.
- Plan vs implementation: every quoted replacement landed as written, with one
  word corrected. The brief's replacement State line read "the six documents
  under `docs/architecture/`"; that directory holds five files, all modified,
  so the line names `docs/ARCHITECTURE.md` and the five documents under
  `docs/architecture/`, the same five-file scope this file's architecture entry
  and the plan already state.
- Deviation, owner-approved: this commit edits dated Section 4 entries
  committed earlier the same day -- the F-B21-51 slice-1 entry's "no behaviour
  change" claim, and WP-7's scope list. Both were wrong as written, and
  AGENTS.md keeps dated entries as point-in-time records, so the correction is
  recorded here rather than made quietly.
- Deviation, consequential: inserting Task 5 falsified two statements in that
  plan, and this commit repoints both -- the Architecture line's task count,
  and Task 4's "This is the final task" pause line, which now reads "before
  Task 5".
- Validation: `pytest -q` -- **1020 passed**; `pre-commit run --all-files` --
  all 10 hooks passed with no files modified; `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (5), recorded as the actual set rather than a smaller
  claimed one: the two plans
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`
  and `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`),
  `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, and the rotation this entry
  forced in `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved
  the F-B21-51 slice-1 entry out of the active window and carried its
  correction with it. docsync demanded no further path: these entries keep the
  1020 claim the corpus already carried, so `FINDINGS.md`'s header needed no
  change.
- Forward guidance: three residual defects in the remediation plan stay,
  because this task's owner-ruled scope capped it at the reviewed findings.
  Task 1's Step 1 still says the literal "must exist in none of them afterwards"
  beside the sentence added here, which says the compliant end state is 2
  matches; Task 4 still says "Tasks 1 to 3 stand alone" without mentioning
  Task 5; and Global Constraints and Task 1's Step 7 still cite `PLAYBOOK.md`
  lines 882, 904 and 1016, which were already stale at HEAD -- the two
  `implementation_plan` references they intend sat 27 lines lower, at 909 and
  931 -- and this commit moved the marker itself from 878 to 880. Repoint those
  citations by name in that plan's next pass: a line number cannot survive the
  next entry inserted above the marker.

### 2026-09-11 - Design-system plan corrected to name its own path

- Scope: the Batch 21 design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`)
  still described itself by its pre-move repository-root name in three places,
  and its Progress "State" line counted its uncommitted work items rather than
  naming them. Both defects came from an exhaustive traversal of the plan; the
  evidence is `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- Plan vs implementation: all four edits landed as written. The State line now
  lists the uncommitted items instead of counting them, because a count goes
  stale the next time one appears (Anti-Pattern Registry item 13). The
  open-decision entry was rewritten in place rather than deleted, so the
  numbering of the decisions below it stays stable for any citation.
- Deviation: this commit stages the plan itself, discharging that plan's own
  "Where to pick up" item 3, which its Progress had recorded as a separate
  commit. A content correction to an untracked file is observable only once the
  file is committed, so the reorder is recorded rather than silent.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0,
  with the expected root `BATCH21_DEFINITION.md` warning. The target guard fell
  from 3 matches to 2; the two survivors name the old root path
  as history beside the new one.
- Forward guidance: the three dated references to the old root name stay as
  written -- two in this file's Section 4, one in the archive after this run's
  rotation. They record what the document said on the day it was written, and
  editing them would falsify a dated record.

### 2026-09-11 - Implementation plan moved into the plans directory and given progress tracking

- Scope: the root-level `implementation_plan.md` became
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`.
  Documentation only; no code, test, or generated asset changed.
- Why: the plan was untracked and sat at the repository root, so nothing
  guaranteed it survived a session boundary, and it recorded no state at all. A
  reader could not tell which phases were done, what Phase 1 had actually
  changed, or where to resume. The plans directory is where every other plan
  lives, and the document is worth keeping: it carries the audit's repo-side
  disposition table and the reasoning behind each phase.
- Added a **Progress** section that owns the status: a per-phase state table,
  the commits landed, the uncommitted work in the order it should be committed,
  a numbered pick-up list, and the four deviations between the plan as written
  and what Phase 1 actually did. The most important of those is recorded plainly
  -- the layout was refined rather than rebuilt, because the owner's side-by-side
  ruling superseded the plan's stacked step and three frontend-gate assertions
  defend the shipped arrangement.
- The step list now points at that section instead of repeating status, so the
  two cannot disagree.
- Validation: `doc_state_sync.py --check` -- exit 0. The file now lives inside
  `docs/`, so the DOC001 path, DOC010 anchor and DOC011 retired-claim scans cover
  it; it passes all three.
- Forward guidance: the untracked
  `docs/superpowers/plans/gemini_implementation_plan_unverified.md` sits in the
  same directory and is still undecided. Resolve it when this move is committed.

### 2026-09-11 - Architecture diagrams rebuilt against the shipped system

- Scope: `docs/ARCHITECTURE.md` and the five owners under `docs/architecture/`.
  Documentation only; no code, test, or generated asset changed. This entry is
  unstaged on purpose -- it belongs with its own commit, not with the gate-slice
  commit staged ahead of it.
- Trigger: the index read "Last verified against the tree on 2026-08-15", so the
  whole set predated the later half of the Tailwind migration.
- `runtime-system.md`: `spotlight.py` and `unmatched.py` were missing entirely,
  as were the canonical routes and the JSON APIs. Added both modules and their
  import edges, route and API nodes, a `Theme` node for the `data-theme` plus
  `.dark-mode` dual write, and prose for three silent-failure facts -- one
  framework stylesheet per page, the theme dual write whose observer WP-8 must
  move in the same change, and the `_MAX_ALBUM_CAP` plus
  partition-before-Spotify cost boundary.
- `documentation-tooling.md`: `docsync.declarations` and `.docsync.toml` were
  absent, so the diagram showed no route by which a declared fact reaches
  integrity checking. Also added `FINDINGS.md` and its rotation, `docs/agents/`,
  `docs/history/`, the `ARCHITECTURE.md` index, the ten pre-commit hooks, and the
  frontend-gate toolchain with its facade and two extracted modules. The prose
  now names the DOC codes that actually bite.
- `development-cycle.md`: an annotation read "Current Batch 21 order: F-SWE-1
  audit, then WP-1", which stopped being true at WP-2. Replaced with the
  side-task path, the session-close handoff, and a pointer that the active order
  lives in PLAYBOOK Section 3 rather than in a diagram. The validation gate now
  names docsync `--check` and the frontend gate.
- `top-albums-sequence.md`: added the threshold partition and its persistence
  before Spotify, corrected the cap line to `_MAX_ALBUM_CAP` for every sort
  mode, and named the reason order on `/unmatched`.
- `heatmap-sequence.md`: added the canonical `/heatmap` page against the
  transient `/loading`, and the cached-saved-job path that keeps the loading
  panel hidden and fades the result in directly.
- Deviation, caught in this pass: the first draft put a `;` inside a mermaid
  `Note over` statement, which the Mermaid instruction file records as a parse
  failure that has shipped once already. Replaced with a full stop. Every file
  was then re-checked: no semicolon inside any fenced block, and every block
  opener has a matching `end`.
- Validation: `pytest -q` -- **1020 passed**; `doc_state_sync.py --check` -- exit
  0 with only the expected root BATCH warning; all six files ASCII-only; Mermaid
  block balance `opens == ends` in each file, 28/28 and 15/15 in the two
  sequences.
- Forward guidance: no Mermaid tooling was reachable in the session that made
  these edits, so validation was structural rather than a render. A renderer
  pass is still worth doing, and `.mmd` files remain the authoring surface.

### 2026-09-11 - Frontend gate: colour maths extracted as F-B21-51 slice 1

- Scope: `scripts/dev/_frontend_gate_colour.py` (new),
  `scripts/dev/frontend_gate.py`, `tests/scripts/dev/test_frontend_gate_colour.py`
  (new), and `FINDINGS.md`. The seven helpers moved unchanged and new tests
  were added. The same commit also lands Batch 21 WP-7's two gate assertions --
  the `data-step` 25 check and the back-to-top collapse check -- which are
  recorded in the WP-7 entry titled "Unmatched disclosure refined: 25-row step
  and collapse on return".
- F-B21-51 records that the gate is roughly ten times its largest sibling --
  4,073 lines against `tailwind_build.py` at 404 -- and prescribes a split along
  the existing check groups while `frontend_gate.py` stays a facade. This is its
  first slice. The finding now also carries the agreed module map and the
  `frontend_gate_checks.toml` registry design.
- The seven pure helpers -- `_parse_rgb_string`, `_composite_over`,
  `_relative_luminance`, `_contrast_ratio`, `_clamp_px`,
  `_worst_divider_contrast`, `_divider_contrast_failure` -- moved to the new
  module and are re-exported through the gate, so no caller has to know. That
  follows `_frontend_gate_results.py` for the module shape and
  `worktree_guard.py` for the stable facade.
- They were chosen first because they take no `page`. The browser gate is the
  artefact being moved, so it cannot be the thing that verifies its own
  refactor; these are provable with pytest alone.
- Parity: 29 tests, three of which a careless rewrite would fail -- the
  `clamp()` `vw` term must not scale with the root font size while the rem
  bounds must; worst-contrast must be the minimum across the surface list; and
  every moved name must still resolve through `frontend_gate`.
- Deviation, recorded: this commit also carries the browser assertions added
  for the WP-7 disclosure refinement (`data-step` must be 25, and back-to-top
  must collapse the panel to 10 rows with `aria-expanded="false"`). They live in
  `frontend_gate.py`'s unmatched check and belong to that work package, but the
  file is touched by both changes and separating them inside one file would need
  partial staging that the gate itself cannot verify. Flagged so the pairing is
  a recorded choice rather than a later discovery.
- Validation: `pytest -q` -- **1020 passed** (991 before the split, plus 29);
  the two-engine frontend gate -- 26 checks passed in 47 runs across chromium
  and firefox; all pre-commit hooks passed.
- Forward guidance: the remaining groups are the browser-coupled ones and still
  need the gate runnable to prove parity.

### 2026-09-11 - Agent-skills scaffolding configured; issues recorded as FINDINGS.md

- Scope: a new `## Agent skills` section in `AGENTS.md`, a narrowed
  `docs/agents/` rule in `.gitignore`, and two new files,
  `docs/agents/issue-tracker.md` and `docs/agents/domain.md`. No production
  code, test, or other document changed.
- Context: the owner ran the setup-matt-pocock-skills skill. The skill assumes a
  root context file plus a decision-record directory, and keeps its vendor
  templates under `docs/agents/`. This repo already owns that ground in the
  "Document Roles (SoC contract)" table and the anti-duplication rule, so
  `domain.md` points at those owners instead of seeding a second rule source.
- Owner decision: issues are findings. `issue-tracker.md` records `FINDINGS.md`
  as the tracker and links to `AGENTS.md` "Finding-Writing Rules" for the format
  rather than restating it. The `triage` skill is not installed, so no label
  vocabulary is written.
- Deviation, recorded rather than silent: `docs/agents/` was already gitignored,
  and its comment said adoption "belongs in its own commit". This is that
  commit, and the change is narrow -- `docs/agents/*` still hides the vendor
  seed templates, and only the two repo-authored files are trackable.
  Un-ignoring the templates would put a layout this repo rejects back into the
  repository as a second source of truth.
- Implementation note: docsync's DOC001 resolves backticked `.md` references
  against `git ls-files`, so an ignored path can never resolve and the two files
  must be staged before `AGENTS.md` links to them. Neither file names a literal
  root context path.
- Validation: `pytest -q` -- **990 passed**; `pre-commit run --all-files` -- all
  hooks passed; `doc_state_sync.py --check` -- exit 0 with only the expected
  root `BATCH21_DEFINITION.md` warning.
- Forward guidance: the design-system plan at `implementation_plan.md`
  (untracked) consumes these files. Its Phase 1 needs revision, because the
  owner's layout ruling for the unmatched report is side-by-side rather than
  stacked; Section 3 carries the refinement still owed.

### 2026-09-10 - Add isolated Results script regression coverage

- Scope: owner-requested coverage review and tests for Spotlight and leaderboard
  interactions. Sampling is server-owned and already covered by the route test.
- Implementation: six isolated Chromium tests run unmodified production scripts
  with a controlled clock. Cover rotation wraparound, late and failed hydration,
  reduced motion, numeric sorting with absent metrics, ranks and accessible
  selection, and hover delay/cancellation plus keyboard tooltip dismissal.
  CI runs this suite after installing browsers and before the frontend gate.
- Validation: six browser tests passed; `pytest -q`: **974 passed**;
  all pre-commit hooks passed. Documentation integrity and whitespace checks
  passed after the final log update.
  No application changes or dependency additions. Owner authorized committing
  this coverage and the README refresh together; pushing is not part of this step.
- **Later same-day test-count addendum:** the WP-7 current-batch entry above
  records the subsequent code change and owns its implementation details. Its
  full-suite result is `pytest -q` -- **986 passed**. The earlier 974 result
  in this entry remains point-in-time evidence; this pointer supplies the
  later same-date count to docsync's live-side-first authority order.

### 2026-09-10 - Refresh the product README against the current implementation

- Scope: owner-requested README refresh while the owner handles PR #227
  integration. No application changes or Git history operations.
- Implementation: describe current navigation, Results/Spotlight, Heatmap
  statistics and export limits, progress UI, and the remaining Bootstrap
  Unmatched report. Replace stale test/coverage figures with the live CI badge;
  shorten the file inventory and link to maintained architecture and work orders.
  Correct virtualenv installs and the init_db.py environment requirement.
- Related pointers: DEVELOPMENT now accurately distinguishes the Chromium
  matrix from the Firefox canary; CONTRIBUTING delegates setup to README.
- Validation: source-checked against templates, routes, frontend scripts,
  dependency pins, workflow configuration and deployment files. All 42 local
  Markdown links and anchors, pre-commit hooks, documentation integrity and
  whitespace checks passed.
  Owner subsequently authorized committing this refresh with the Results tests.

### 2026-09-10 - Refine Heatmap contrast and Results interaction motion

- Scope: owner follow-up on Heatmap styling, duplicate Results Top control,
  delayed Spotify hints, sorting motion and page-loading jank.
- Implementation: owner-refined sunken light-mode Heatmap frame with darker
  warm-neutral empty cells (`#c8bfad`); uppercase Input Mono
  Narrow toolbar with primary New search; supporting label grows from 12px
  to 15px in Input Mono. Results retains only the side-rail Top control.
  Spotify links reveal a shared hint after 450ms hover, immediately on focus,
  and dismiss on Escape, blur or scrolling. Ranking changes interpolate row
  positions for 280ms, with immediate reduced-motion updates. Export clones
  clear transient row animations.
- Diagnosis: delayed page_motion.js reproduced a visible-to-transparent flash
  in Chromium and Firefox before DOM readiness. CSS now starts entry at first
  styled paint; the delayed-script probe no longer reproduces the opacity dip.
  The initial header clarification was interpreted as viewport-fixed. The
  owner's later screenshot identified that persistent visibility as the
  unwanted behavior. The header now occupies document flow and scrolls out of
  view; duplicate body clearance is removed and the sticky rail uses its own gap.
- Export inspection: Heatmap uses a separate hand-drawn canvas with older
  headline/layout rules. That visual mismatch remains; the working export is
  preserved in this pass. Results export is unchanged apart from suppressing
  temporary row motion in its clone.
- Validation: `pytest -q` -- **974 passed**. The full frontend gate passed
  25 checks in 45 runs. Additional Chromium and Firefox probes covered hover
  delay, dismissal, rapid sorting, reduced motion, scroll stability, header
  scroll-away, both-theme empty-cell fills and responsive Heatmap geometry.
  Firefox CSV/JPEG checks passed at desktop and mobile widths in both themes.
  Evidence: `scratch/pressure-verify-final.txt`, `scratch/pressure-extra-final.txt`
  and screenshots. Final staged validation passes every hook, including
  generated-CSS drift and documentation sync. Owner visual
  review approved the result and authorized a safe push to PR #227. The pre-push
  sweep reconciled stale design overrides with the shipped composition. This
  remains an owner-directed side-task, not a new work package.

### 2026-09-09 - Refine Results consistency and restore navigation continuity

- Scope: owner-requested UI consistency and remediation of local Heatmap
  edits. Preserve the larger headline, sans preview labels and tighter loading
  parameters; correct the undefined legend font token. Remove the intentional
  duplicate Heatmap counter rail and its unused hydration and layout checks.
- Implementation: Results panels use an equal sRGB page/sunken mix. Sort and
  outside-filter headings use smaller uppercase sans type than Spotlight,
  centred without changing text colours. Sort labels use weight 400. The
  three toolbar actions use uppercase Input Mono Narrow with one larger gap
  step; New search retains the theme primary fill. Secondary Results actions
  and Heatmap result buttons share sans type and control fill, retaining
  proportional Results dimensions.
- Index follow-up: measured form placement lifts the composition up to 2.5rem
  from centre, bounded by 0.25rem of header clearance. Reclaiming excess
  vertical well padding removes the decade-state scrollbar at 1920x900 and
  1536x730 in both engines, with thresholds collapsed and scale unchanged.
  Mobile retains its existing padding. `scratch/index-offset-evidence.json`
  records five desktop window sizes per engine.
- Motion: browser samples confirmed existing entrances and a fixed header.
  Shared keyframes make page entry independent of first-paint timing; normal
  internal links fade content out before navigation, and Back restores it.
  Reduced motion remains immediate. Heatmap loader/result stages overlap
  during their existing opacity handoff. The header remains independently fixed.
- Export: the browser resolves the mixed surface to RGB in the JPEG clone
  because html2canvas cannot parse modern computed colour functions. The live
  page retains its theme-derived mix. Export clones suppress entry animation.
- Validation: `pytest -q` -- **974 passed**. Focused Chromium and Firefox
  probes cover desktop/mobile, both themes, scaling, header scroll position,
  button and heading consistency, navigation, Back and Heatmap completion.
  Evidence: `scratch/ui-consistency-evidence.json` and accompanying screenshots.
  Full frontend gate: 25 checks passed in 45 runs. Additional Firefox checks
  pass for both-theme desktop/mobile exports and the complete layout/state
  matrix. All hooks pass except committed-CSS drift: the regenerated file
  intentionally differs from the index while this work remains unstaged.
  A second build produces identical bytes. Docsync and whitespace checks
  pass. No commit or push.
- Deviation: an editing helper briefly misdecoded existing UTF-8 punctuation.
  Tests caught it; original bytes were restored before the passing suite.
- Forward guidance: owner visual review before publication. WP-7 remains
  next batch work; Task 6 stays deferred until Bootstrap removal.

### 2026-09-09 - Complete Results scaling and warm the shared canvas

- Owner direction: keep the deployed Results aesthetic, warm the page/navbar
  subtly, keep the header fixed on every screen size, and defer
  Task 6 until Bootstrap is fully removed. The canonical remediation plan
  records the timing; WP-7's backend-first contract and final page migration
  remain unchanged.
- Owner typography refinement: Track Plays table numerals are 25% larger;
  Listening Time retains its existing size, including after switching modes.
- Owner follow-up: Results stat rail, table, empty-state panel and sidebar
  cards use `--ss-surface-sunken`; table hover uses the card token for a
  visible state change. Buttons retain their control surfaces.
- Implementation: shared light canvas is `#faf7f0`; DOC009 guards the Tailwind,
  legacy-page and navbar copies. Results uses measured numeric scaling across
  named spacing tokens, typography, artwork and controls. F-B21-55 records the
  fixed Firefox arithmetic failure and incomplete geometry scaling. Mobile
  table headings wrap within their columns. The mobile gate verifies both fixed positioning and matching body padding.
- Evidence: `scratch/fixed-results-measurements.json` and paired Chromium /
  Firefox screenshots. Both engines agree on 20% growth between 1200px and
  1920px. Fourteen viewport samples (320-2560px) have no horizontal overflow;
  the shared header remains at top 0 after scrolling at every width. Index, Results and
  Unmatched bodies and navbars all compute to the warm canvas. Dark token values are unchanged; Results panels now consume the sunken token. The Results gate checks growth ratios and
  mobile recovery using rendered values.
- Publication validation: fresh `pytest -q` -- **975 passed**. Full frontend
  gate: 25 checks passed in 45 runs across Chromium and the Firefox canary.
  The prior loading-pipeline navigation race did not reproduce. The separate
  Results probe covered both engines at seven widths; the final surface and
  metric-toggle checks covered both themes and desktop/mobile respectively.
  All pre-commit hooks pass, including generated-CSS drift; docsync and
  whitespace checks pass. Read-only review found no material code issue and
  corrected active document contradictions; exhaustive historical-document
  coverage was interrupted by reviewer usage limits. Owner authorized commit
  and push; local tool artifacts remain outside the published changes.

### 2026-09-09 - Triage PR 227 assertions and deleted TODOs; fix job-page statuses

- Scope: owner requested top-priority fixes only and logging of other review
  comments. Read live review threads, complete review bodies including the
  low-confidence block, current source, and the TODO add/remove commits.
- Plan vs implementation: fixed F-B21-49 with explicit HTTP/badge pairs at
  its four source branches. Missing IDs return 400; unavailable jobs 404;
  pending results 202; processing failures use their classified status.
  Saved empty-state recovery stays 200. Strengthened five existing tests and
  added thirteen route cases. The tests failed before the source fix.
- Disposition: F-B21-54 records test-scanner noise. F-B21-50 now distinguishes
  implemented notes from deferred unmatched redesign / POST retirement.
  F-B21-51 no longer incorrectly claims there are no gate infrastructure tests.
  Detailed evidence and remaining finding owners:
  `docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md`.
- Validation: `pytest -q` -- **975 passed**. Route suite: 18 failed / 89 passed
  before, 107 passed after. Focused read-only review found no regression.
  Docsync and `git diff --check` pass. Hooks pass after formatting except the
  existing `tailwind-css-drift` failure described below.
- Deviations: the pre-work hooks rebuilt already-dirty `tailwind.css` for the
  owner's existing results markup; its index comparison fails until that
  separate styling work is staged. No source CSS/template changes were made
  here. The known Windows log-rotation lock appeared in red-test diagnostics.
- Forward guidance: keep this status fix separate from existing styling.
  Published PR `a53e412` lacks the earlier local remediation; no commit,
  push or review reply was made. Task 6 and WP-7 remain next.

### 2026-09-09 - Audit PR 227 for regression and bloat; ignore gate artifacts (side-task)

- Scope: the owner asked which commits after `b987e48` carry value and which
  are bloat, and whether the 15 route TODOs were implemented. Owner chose the
  hygiene-only remedy: no history rewrite and no gate split.
- Premise correction recorded before any change: `b987e48` is not a baseline
  to restore toward. `main` merged into this branch at `ebc5145`, *after*
  `b987e48`, so reverting toward it would discard PRs #225 and #226. PR content
  was therefore measured against `origin/main`.
- Size of the PR, since three different questions give three different answers
  and the first is the one that misleads. `b987e48..HEAD` is +4524/-1848 over
  62 files, but it hides everything that arrived through the `ebc5145` merge
  and must not be quoted. `origin/main..HEAD` is +8458/-2293 over 76 files.
  Summing each of the 34 non-merge commits' own diffs gives the real churn:
  **+13802/-5450 over 86 distinct files**, so netting the endpoints conceals
  8,501 touched lines. The largest single contributor is `frontend_gate.py`:
  20 commits and 3,158 gross lines to land a net +791 while chasing the CI
  stall. Quote the churn figure when judging review effort and the endpoint
  diff when judging the delivered change.
- Three bloat suspicions were tested and **disproved**, so nothing was
  reverted: (1) the 486/484-line `global.css` diff is a whole-file CRLF-to-LF
  conversion in `d41db1f` with about five semantic lines, and `global.css` was
  the only CRLF outlier in `static/**` and `templates/**`, so the conversion
  normalized it; (2) `typekit_fixture.css` was added then deleted under the
  owner's 2026-09-07 font-licensing ruling, recorded in
  `scripts/dev/fixtures/README.md`; (3) the ruff migration touched about
  fifteen test files but only reflowed `assert` formatting, weakening no
  assertion. `ipinfo` and `cachetools` removal was confirmed against zero
  imports repo-wide.
- Security and hardening in the range were confirmed genuine and kept:
  `innerHTML` sinks in `static/js` fall 5 (main) to 4 (`b987e48`) to 1 (HEAD,
  `heatmap.js` only); least-privilege `contents: read`;
  `persist-credentials: false`; 18 vulnerable pins upgraded to a zero-finding
  `pip-audit`; aiohttp 3.14 deprecations replaced with stdlib `base64`; CI
  actions moved off the deprecated Node 20 runtime.
- TODO verification: 13 of 15 described already-implemented behaviour
  (`/unmatched` GET route, `unmatched_empty.html`, `index.js` blur validation,
  `heatmap.js` `retryable` branching), so removing them was correct. Two were
  genuine and are now **F-B21-49**.
- Implementation: added root-anchored `.gitignore` entries for
  `/gate_out*.txt` and `/gate_summary.txt` (about 3 MB of untracked console
  captures) plus `*.new` and `*_backup.toml` migration scaffolding, verified
  against `git ls-files` so no tracked file became hidden; deleted the
  untracked zero-byte `.github/workflows/workflow1`, which would have been an
  invalid workflow had it ever been committed.
- Deviations: three findings were filed rather than fixed, because each needs
  an owner ruling or parity tests this side-task does not carry. **F-B21-49**
  (four `error.html` callers return HTTP 200 while painting a 400 badge;
  measured, not read) needs the owner to choose 404 or 410 for expired jobs.
  **F-B21-50** records the net-zero TODO churn that cost eight Qlty rounds
  (15 distinct `routes.py` line numbers, each republished 8 times: 120 comment
  bodies). **F-B21-51** sizes `frontend_gate.py` at 3,756 lines against its
  largest sibling's 404, and defers the split because gate infrastructure has
  no parity tests (AGENTS.md Proposal and Design Rules item 4). F-B21-10's
  status line now points at F-B21-49 for its call-site half.
- One claim in the review commit's own subject was checked and does not hold as
  written: "simplify frontend checks". The gate plus helper grew from 2,965
  lines in 49 functions on `main` to 3,879 in 78 at HEAD, about 222 of those
  lines added by that very commit, with its test file going 966 to 1,328. What
  did improve is unit size -- the longest function fell 485 to 271. Recorded in
  F-B21-51 so a later reader does not inherit "simplified" as fact.
- Validation: `pytest -q` -- **962 passed**. All pre-commit hooks and
  `doc_state_sync.py --check` pass. The committed tree was verified clean by
  stashing the unrelated results-scaling work in progress; the earlier
  `tailwind-css-drift` failure belonged to that work, not to any PR commit.
- Forward guidance: the PR #227 body still needs writing before merge. Task 6
  (accessibility pass) and WP-7 remain the next batch work.

### 2026-09-07 - Remediate PR 227 and simplify frontend checks

- Owner requested one review-remediation package. The full comment inventory,
  body exclusions, repeated claims and individual dispositions are in
  `docs/history/reports/PR227_REVIEW_2026-09-07.md`.
- Extracted gate measurement/comparison/profile responsibilities, shared phase
  probes and lazy generic CDN fixture loading; preserved the live-fonts option.
  Existing thresholds and the Chromium matrix / Firefox static canary remain.
- Separated spotlight aggregation from routes, shared Spotify payload parsing,
  separated heatmap validation/dispatch, and extracted the Last.fm job stage.
  Existing job-state, empty/error, fallback and sampling behavior stays covered.
- Split results spotlight hydration/rotation from exports; use DOM text nodes
  for metrics/toasts and supported metric-toggle font weights. CSV follows the
  current rank/metric with full ISO dates while display stays month precision.
  JPEG background comes from the active theme; browser checks decode actual
  downloads in both themes at mobile and desktop widths.
- Reconciled implemented route TODOs, corrected explicit 404/500 badges (the
  remainder of F-B21-10 stays open), and disabled checkout credential persistence.
- Review caught invalid JSON in the extracted stale-response fixture. A failing
  regression test proved it; structured JSON serialization restored the check.
- Validation: `pytest -q` -- **962 passed**, zero warnings. The frontend gate
  passed 25 checks in 45 runs across Chromium and the Firefox static canary.
  Both theme exports decode to nonblank 3600px-wide JPEGs. All pre-commit
  hooks and `doc_state_sync.py --check` pass. No push or deployment. Header
  alignment and optional white-card shadow remain a separate design follow-up.

### 2026-09-07 - Qlty adopted; first triage closes the workflow-permission gap (side-task)

- Scope: the owner added qlty (`.qlty/qlty.toml`, uncommitted by owner
  choice) as a fourth static-analysis layer alongside ruff, bandit-class
  SAST, and the existing gates. This entry records the config tuning,
  the first triage, and the two fixes it produced.
- Plan vs implementation: no plan -- owner-directed tooling adoption and
  triage. Config tuning: scratch/, scripts/bin/, generated tailwind.css,
  and graphify-out/ excluded (metrics went from 68 to 18 files); the
  flake8 plugin removed (ruff replaced it; two plugins would report one
  rule surface in two vocabularies); tests/ added to test_patterns.
- Triage of the first `qlty check` (88 findings): ~60 are bandit B101
  "use of assert" in tests -- noise, asserts are the point of tests;
  2 are real (zizmor on the workflow, fixed here); 1 is a false positive
  recorded with a nosec (bandit B311, fixed here); the cognitive-
  complexity pair (frontend_gate.py check_large_display_scale_parity,
  spotify.py fetch_spotify_artist_spotlight) is known owned debt that
  matches F-B20-2/F-SWE-7/issue #222 and stays batch-scoped, not
  gate-blocking.
- Implementation:
  - `.github/workflows/test.yml`: added a job-level `permissions:
    contents: read` block. The job only reads the checkout and uploads a
    coverage artifact; without the block the runner's default token
    permissions are broader than any step needs and every third-party
    action inherits them (zizmor excessive-permissions and artipacked).
  - `scrobblescope/routes.py`: `# nosec B311` with justification on the
    `random.Random(str(job_id)).sample(...)` spotlight selection. The
    seed makes the sample deterministic per job (asserted by
    test_results_page_samples_five_unique_artists_from_aggregate_top_ten);
    cryptographic unpredictability would defeat the intent.
- Deviations: none.
- Validation: `qlty check` -- 88 -> 86 findings. The excessive-permissions
  finding is gone; the B311 finding is suppressed (the nosec must sit on
  the same line as the call -- a preceding comment line is ignored by
  bandit, which the first attempt got wrong and the re-run caught).
  Remaining: one zizmor artipacked medium on the checkout step (line 34)
  -- zizmor flags any cache/artifact-adjacent job; with the permissions
  block in place the token is already contents-read only, so the
  practical exposure is closed and the residual finding is a
  scanner-pattern advisory, not an open hole. The rest are the recorded
  noise classes. `pytest -q` -- **938 passed**, zero warnings. All
  pre-commit hooks pass.
- Forward guidance: the meta-lesson is recorded here because it
  generalizes -- each gate only checks what it was built to check, and
  no gate checked the checkers' blind spots. Workflow files had no
  linter, the codebase had no SAST, structure had no complexity metric;
  qlty closes exactly those three. The complexity refactor and the
  bandit B101 test-path suppression are future-batch candidates, not
  scheduled work. WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - Clean uninterrupted frontend gate run achieved (side-task)

- Scope: closed the deviation recorded in the two 2026-09-07 entries above
  -- no clean uninterrupted `frontend_gate.py` run had been achieved
  locally -- and updated the spec status line for the implemented design.
- Plan vs implementation: Task 6 Step 3 of
  `docs/superpowers/plans/2026-09-07-frontend-gate-isolation.md`. One run,
  qualified venv path, no interference.
- Result: the run completed all four groups across both engines with 261
  page loads, zero timeouts, zero errors, and zero font warnings (the kit
  served live). The only failures were the 7 large-display-scale-parity
  assertions at 4K (deltas ~1 percent: 770.0 vs 780.4px form width,
  774.4 vs 781.6px hero height, 77.2 vs 78.2px headline line-height, and
  related), which are the same failure family the owner already accepted
  in the gate-isolation entry above. The isolation mechanics work as
  designed: every check ran and reported; nothing cascaded.
- Deviations: none beyond the already-recorded 4K parity pair.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (unchanged; no
  code changed in this entry). Spec status line updated to record the
  owner-ruled licensing amendment (Typekit fixture withdrawn).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - Gate isolation, license-safe CDN routing, paper-cream tokens, and results polish (side-task)

- Scope: made the frontend gate stall-tolerant (grouped checks, fresh
  contexts, fail-fast navigation), resolved the PR #227 Quality Gate
  failures, applied the owner's paper-cream surface palette, and landed
  the owner-annotated results-page polish.
- Plan vs implementation: followed
  `docs/superpowers/plans/2026-09-07-frontend-gate-isolation.md` with one
  fundamental amendment. The metric-pinned font fixture (plan Tasks 1 and
  5) was abandoned at the owner's licensing ruling: the kit families
  (Gotham, Akzidenz-Grotesk Next Pro) are commercial web fonts and must
  never be re-hosted, embedded, or synthesized in the repo. The kit loads
  from the real Typekit origin on every gate run; only the generic cdnjs
  Bootstrap stylesheet is served from a repo fixture. The gate is
  therefore not fully hermetic -- accepted trade-off for license safety,
  recorded in `scripts/dev/fixtures/README.md`.
- Implementation:
  - Gate grouping: `CHECKS` entries gained a group field; groups derive
    from the tuple at call time (no second declared copy, no group
    integrity test per the owner's "redundant to test a test" ruling).
    Each group opens a fresh browser context, so a wedged page poisons
    only its group -- the 2026-09-07 CI run had cascaded one navigation
    timeout through every later check on a shared page.
  - Firefox is a canary: it runs only the static-assets group (the
    2026-09-01 remediation plan measured engine agreement within 0.1px,
    so a full second pass doubles the stall surface for near-zero
    signal). Chromium runs everything.
  - Fail-fast navigation: 10s page-level timeout (the context-level
    kwarg does not exist in Playwright -- caught by a local run, not by
    unit tests).
  - Fonts advisory: `check_fonts` reports missing faces as WARN lines
    and returns no failures (owner ruling: a font-supply problem is not
    a UI defect).
  - License posture: no Adobe family is copied, embedded, synthesized,
    or re-hosted anywhere; a synthetic TTF generator briefly existed in
    untracked scratch and was destroyed before any commit.
  - Paper-cream surfaces: `--ss-surface-card` #fcfbf8 -> #f7f3ea
    (halfway to the sunken tone; cards had become indiscernible from
    the page and pure white read as harsh). `global.css` mirrors follow.
    The imported design snapshot keeps `#ffffff` by contract; the
    override is recorded in `docs/design/RECONCILIATION.md` section 12.
  - Theme pill: the active Light choice dropped its #ffffff background
    (introduced in `14215d6`) for `--shell-surface` elevation with a
    stronger border/shadow.
  - Heatmap preview: bullets at color-mix(body 55%, muted); copy
    rewritten (7x52 grid, totals/streak, best-day highlight).
  - Index: `--index-scale-cap` 2.15 -> 1.75 (owner ruling: the lockup
    dominated beyond 1440p and the right-hanging void grew faster than
    content).
  - Card surfaces, final ruling (revising the paper-cream line above,
    same day): #f7f3ea was too warm and #fcfbf8 read cold, so the owner
    split the surfaces. `--ss-surface-card` -> #f9f7f1 (midpoint of the
    two; general cards), mirrored in `global.css`, and a new
    `--ss-surface-card-standout` (#ffffff light / #181520 dark) paints
    the index card alone pure white as a standout; `.ss-card` and
    `.hint__body` in `index.css` read the standout token. DESIGN.md
    header and the token test follow. RECONCILIATION.md section 12
    records the full trial -> reversal -> split sequence.
  - Results StatBlock typography (owner ruling): numerals and labels
    back to Instrument Serif with labels at 11px/xs serif in
    `--ss-text-body` (not muted); the sans-numeral line below is
    superseded by this.
  - Results polish (owner-annotated screenshot): action-row gap 8 -> 12px;
    filter-bar values to input-mono; row hover at full sunken strength;
    sort-toggle weight 500.
- Deviations: superseded by the 2026-09-07 stale-gate-cap entry below.
  The 4K parity failures recorded here were later root-caused to the
  gate's expected-scale cap lagging the CSS `--index-scale-cap` change
  in this same entry, not to font metrics. Owner confirmed the form card
  does not scroll the page at 1080p/92dpi with bookmarks extended.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (final
  consolidated run for this entry; the standout token added one
  parametrized test to the shell suite). Full suite green before commit;
  pre-commit hooks (black auto-fix included) enforced on every commit in
  the series. The gate itself was exercised repeatedly during
  development; the remaining parity pair is recorded above rather than
  hidden.
- Forward guidance: WP-7 (unmatched page + reason_code) remains next;
  the heatmap form lacks validation-on-blur and private-account gating
  (owner-noted), candidate for WP-7 or a scoped side-task.

### 2026-09-07 - Stale gate scale-cap corrected; 4K parity failures resolved (side-task)

- Scope: root-caused and fixed the 7 large-display-scale-parity failures
  at 4K recorded in the two 2026-09-07 entries above.
- Plan vs implementation: no plan -- a defect found while reviewing the
  gate's measurement model with the owner. Verification first: the CSS
  computes scale `clamp(min, slope, 1.75)` from the owner's 1.75 ruling
  in `static/css/index.css` line 26, giving 440px x 1.75 = 770.0px form
  width at 4K -- exactly what the gate measured. The gate's
  `expected_scales` formula still capped at the old 2.15, expecting
  780.4px. The 0.9866 ratio reproduces every width/height/cap delta;
  1440p is unaffected because its slope term (1.308) sits below the cap.
  The `headline lineHeight` delta is the only member of the old
  attribution that font metrics could explain; the rest were this cap.
- Implementation: `scripts/dev/frontend_gate.py` outer scale cap
  2.15 -> 1.75 with a comment pinning it to `--index-scale-cap` so the
  next cap change does not repeat the drift. No tolerance changed.
- Deviations: the original attribution ("real kit's tall Instrument
  Serif metrics are not present") was wrong for 6 of the 7 failures and
  is corrected in that entry. The gate's measurement model was the
  question the owner asked; the answer exposed the defect.
- Validation: gate unit module 47 passed. Full gate run: **24 checks
  passed in 43 runs**, exit 0, zero failures, zero timeouts, zero font
  warnings. `pytest -q` -- **938 passed**, 5 warnings. All pre-commit
  hooks pass; `doc_state_sync.py --check` exits 0 (expected root BATCH
  warning).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.
  The gate cap and the CSS token are one fact in two places; a future
  sweep could have the gate read the value, but no further work is
  scheduled now.

### 2026-09-07 - Remove the dead pypdf/pdf2image/pillow cluster (side-task)

- Scope: executed the removal half of F-B21-3's recorded shape. The
  2026-09-07 pip-audit run found 120 advisories in 13 packages; these
  three carried ~65 of them and nothing imports any of them.
- Plan vs implementation: no plan -- owner-directed side-task executing
  F-B21-3's suggestion. Verification before removal: `pip show` metadata
  (pypdf Required-by: nothing; pdf2image Required-by: nothing; pillow
  Required-by: pdf2image only) plus a repo-wide grep for imports across
  scrobblescope/, scripts/, tests/, app.py, templates/, static/js/, the
  Dockerfile and the deployment docs -- zero hits. The JPEG export is
  client-side html2canvas (static/js/results.js), as F-B21-3 already
  recorded; the prior archive log confirms the owner was asked about
  this cluster before and confirmed it serves nothing.
- Deviations: none for the approved scope. Two further dead packages
  were found during verification -- `ipinfo` (Required-by: nothing) and
  `cachetools` (Required-by: ipinfo only) -- but they were not in the
  approved removal list, so they stay pending an owner ruling. The
  owner's correction on `virtualenv` was accepted: it is a real
  dependency of pre-commit (pip show pre-commit: Requires ... virtualenv)
  and stays; `filelock` stays with it. The stdlib `venv` module, not the
  virtualenv package, creates .venv -- the two were conflated in the
  first proposal.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (unchanged; the
  packages were unimported). All pre-commit hooks pass.
- Forward guidance: commit 2 upgrades the vulnerable runtime packages
  (aiohttp, requests, urllib3, werkzeug, flask, python-dotenv, idna,
  click, pytest, virtualenv, filelock). Owner ruling pending on
  ipinfo/cachetools.

### 2026-09-07 - Upgrade vulnerable packages; audit now reports zero (side-task)

- Scope: executed the upgrade half of F-B21-3's recorded shape, plus the
  owner's two rulings from the removal entry: ipinfo and cachetools are
  removed (both dead -- ipinfo Required-by nothing, cachetools required
  only by ipinfo, zero imports), and pip-audit is pinned in
  requirements-dev.txt so the audit is repeatable locally.
- Plan vs implementation: no plan -- owner-directed side-task. Fix
  versions from the audit's own fix_versions, not guesses: aiohttp
  3.11.10 -> 3.14.3, requests 2.32.3 -> 2.33.0, urllib3 2.2.3 -> 2.7.0,
  werkzeug 3.1.3 -> 3.1.6, flask 3.1.0 -> 3.1.3, python-dotenv
  1.1.0 -> 1.2.2, idna 3.10 -> 3.15, click 8.1.8 -> 8.3.3, pytest
  9.0.2 -> 9.0.3, virtualenv 20.28.0 -> 20.36.1, filelock
  3.16.1 -> 3.20.3.
- Deviations: aiohttp 3.14.3 requires aiohappyeyeballs>=2.5.0, so its
  whole dependency family moved with it (aiohappyeyeballs 2.4.4 ->
  2.7.1, aiosignal 1.3.2 -> 1.4.0, frozenlist 1.5.0 -> 1.8.0, multidict
  6.1.0 -> 6.7.1, propcache 0.2.1 -> 0.5.2, yarl 1.18.3 -> 1.24.5) --
  the first install attempt failed with ResolutionImpossible until the
  family was upgraded together. The pinned-requirements discipline
  (AGENTS.md: all ==) is preserved; every new pin is exact.
- Validation: `pytest -q` -- **938 passed**, 7 warnings (two new
  warnings are aiohttp 3.14 deprecation notices, cosmetic). All
  pre-commit hooks pass. Full frontend gate -- **24 checks passed in 43
  runs**, exit 0, zero failures: the aiohttp jump is clean in a live
  browser. `pip-audit` re-run: **0 packages with vulnerabilities, 0
  advisories** (was 13 packages / 120).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.
  F-B21-3's remaining suggestion -- splitting runtime from developer
  requirements -- is still open and unruled. The two new aiohttp
  deprecation warnings are cosmetic; a future sweep could silence them
  at the call sites.

### 2026-09-07 - Fix the B023 route-handler regression the ruff migration introduced (side-task)

- Scope: repaired the two validator checks the ruff migration broke in
  CI (run on `c7bfaec`: "validator race" and "validator network failure"
  both raised `AttributeError: 'Request' object has no attribute
  'append'`), plus three Pylance type errors the owner surfaced while
  reviewing the same file.
- Plan vs implementation: no plan -- regression repair on the open PR.
  Root cause of the CI failures: the B023 fix used a default-argument
  binding (`lambda route, pending=pending: ...`), but Playwright inspects
  the handler's parameter count -- two parameters means it is called with
  (route, request), so the request object overrode the `pending` default
  at call time. The fix is a handler factory (`_collecting_handler`)
  whose closure binds the list with a single visible parameter,
  satisfying both Playwright's contract and bugbear B023. Lesson
  recorded: a lint-driven rewrite of a framework callback must be
  validated against the framework's calling convention, not only the
  linter.
- Implementation:
  - `scripts/dev/frontend_gate.py`: `_collecting_handler` factory used by
    both validator checks; `spotlight_requests` bound before its poll
    loop (possibly-unbound read after a possibly-zero-iteration loop);
    `CHECK_GROUPS` built through an honestly-typed list accumulator with
    a final comprehension producing the declared tuple shape; the
    summary line reads the firefox canary through `groups_for()` instead
    of subscripting `BROWSER_SCOPES` values, whose `None` sentinel for
    chromium's full pass makes direct subscripting a type error. The
    chromium-full-pass / firefox-canary design is unchanged.
- Deviations: none. No check semantics, tolerance, or grouping changed.
- Validation: full gate run -- **24 checks passed in 43 runs**, exit 0,
  zero failures (the two validator checks pass in a live browser), zero
  timeouts, zero font warnings. `pytest -q` -- **938 passed**, 5
  warnings. All pre-commit hooks pass. `doc_state_sync.py --check`
  exits 0 (expected root BATCH warning).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - CI action bumps and ruff lint/format migration (side-task)

- Scope: cleared the Node.js 20 deprecation warning on the Quality Gate
  (the run on `d41db1f` flagged checkout/cache/setup-python/upload-artifact
  as forced onto Node 24) and modernized the Python toolchain by replacing
  black + isort + autoflake + flake8 with ruff, per owner request.
- Plan vs implementation: no plan -- owner-directed side-task. Action
  versions were fetched from each repo's latest release, not guessed:
  checkout v4 -> v7, setup-python v5 -> v7, cache v4 -> v6,
  upload-artifact v4 -> v7. Ruff pinned to 0.16.6 (latest at adoption),
  wired through `astral-sh/ruff-pre-commit` v0.16.6 with `ruff-check
  --fix` and `ruff-format` hooks.
- Implementation:
  - `.github/workflows/test.yml`: the four action bumps. No other step
    changed.
  - `pyproject.toml`: `[tool.ruff]` config replaces `[tool.isort]`.
    select = E,W,F,I,UP,B (pycodestyle, pyflakes, isort, pyupgrade,
    bugbear). Ignored: E203/E501 (black-compatible formatter artifacts
    flake8's default ignores already excluded) and E741 (same default
    ignore set). E402 exempted per-file for `app.py` only -- it must call
    `load_dotenv()` before imports that read env at import time. The
    pre-commit exclude list is mirrored in `extend-exclude` (plus
    `scratch/`, untracked).
  - `.pre-commit-config.yaml`: four tool repos replaced by one ruff repo.
  - `requirements-dev.txt`: `flake8==7.3.0` -> `ruff==0.16.6`.
  - Code fixes ruff surfaced (all real, none cosmetic-only): B904
    exception chaining in `dev_start.py` (3) and `docsync/declarations.py`
    (3); B023 loop-variable binding in two `frontend_gate.py` route
    lambdas; B007 unused loop variables renamed in `orchestrator.py` and
    `docsync/declarations.py`; B905 `zip(strict=True)` in
    `docsync/logic.py` and `test_template_shell.py`; E402 mid-file import
    moved to the top of `test_routes.py`; plus 66 safe autofixes (unused
    imports, import sorting, pyupgrade rewrites) and 9 files reformatted
    by ruff-format (black-equivalent; the visible deltas are implicit
    string-concat joins and assert-message placement).
  - Docs: README (Code Quality row, structure comments), CONTRIBUTING
    (code-style section), SESSION_CONTEXT pre-commit line.
- Deviations: none. No tolerance, test, or behaviour changed; the 938
  count is unchanged because ruff's fixes touch no tested path.
- Validation: `ruff check .` -- all checks passed. `ruff format --check`
  -- clean. `pytest -q` -- **938 passed**, 5 warnings. All pre-commit
  hooks pass (ruff check, ruff format, and the 8 surviving hooks).
  `doc_state_sync.py --check` exits 0 (expected root BATCH warning).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.
  The Quality Gate run on this push should show no Node 20 warning.

### 2026-09-07 - Fix the three CI Quality Gate failures left by the Task-3/4 merge (side-task)

- Scope: diagnosed and fixed the three assertion families failing the
  `quality-gate` run on PR #227 (form centring, theme-toggle height, mobile
  body offset), all of them inherited from the `ebc5145` merge that took
  `test`'s pre-remediation CSS while keeping main's post-remediation gate.
- Plan vs implementation: as planned, after measurement overruled the
  owner's initial 0.5rem-shift hypothesis. The gate reported a constant
  80.0px top/bottom gutter imbalance at every window size, which is
  2 x 40px: the stale `top: -2.5rem` nudge (introduced in `f0acf4d`)
  fighting the `margin-block: auto` centre. Deleting the nudge shifts the
  form down 2.5rem, not 0.5rem, and lets the auto margins centre it -- the
  direction the owner pointed at, with the magnitude measurement dictates.
- Implementation:
  - `static/css/index.css`: removed the `position: relative; top: -2.5rem`
    nudge from the desktop `.index-form__inner` rule; `margin-block: auto`
    now does the centring alone. The nudge contradicted the F-B21-44
    "vertically centre the desktop form composition" owner refinement it
    sat next to -- it predates the flex-centring rule and was superseded,
    not removed, when that rule landed on main.
  - `static/css/shell.css`: reverted the theme-toggle padding from
    `0.25rem` (introduced in `14215d6`) to the ruled `0.2rem`, restoring
    the 8.4px chrome the gate's toggle-height curve adds to the
    theme-choice clamp (46.0 -> 44.4px at 1080p; 50.0 -> 48.4px at 1440p).
    Added a comment pinning the coupling so the next padding tweak does
    not silently break the gate.
  - `scripts/dev/frontend_gate.py`: the `bodyPaddingTop == headerHeight`
    mobile check encoded the fixed-header design that main's CSS still
    has; the merged redesign moved the header in-flow (`position:
    relative`) and dropped body padding, so the equality was false by
    construction. Replaced it with the invariant that design actually
    promises -- the first content pixel sits at or below the header's
    bottom edge -- measured as `contentTop >= headerBottom - 0.5`.
    Extracted the whole mobile-header assertion set into
    `_mobile_header_failures(width, header)` so each invariant has a
    unit-level seam, per the AGENTS.md helper-testing rules.
  - `static/css/tailwind.css`: rebuilt via `scripts/dev/tailwind_build.py`.
  - `tests/scripts/dev/test_frontend_gate.py`: added 7 unit tests for
    `_mobile_header_failures`, one per invariant, each with boundary
    cases (43.9 vs 44.0, 799.0 vs 799.6, 75.0 vs 75.6). Mutation-verified:
    all 6 guard-block removals are killed by the suite (no vacuous tests).
- Deviations: no clean uninterrupted `frontend_gate.py` run was achieved
  locally -- run 2 failed on a firefox theme-click timeout, run 3 on a
  pipeline state-machine timeout, run 4 on a port collision, and run 5
  was interrupted mid-flight. Runs 2-4 each failed on exactly one flaky
  timeout with the three CI families gone, but a single fully green run
  is still owed to the gate; CI's Linux runner provides the authoritative
  verdict for this push.
- Validation: `pytest -q` -- **932 passed**, 5 warnings (was 925; +7
  helper unit tests). `python scripts/doc_state_sync.py --check` exits 0
  (expected root BATCH warning). `pre-commit run --all-files` -- all 12
  hooks pass, including `tailwind-css-drift` on the rebuilt stylesheet.
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.

### 2026-09-06 - Rotate five Artist Spotlight candidates from the aggregate top ten (side-task)

- Scope: corrected the Results Artist Spotlight contract without changing
  album enrichment, Heatmap polling, the database schema, or CSS rules.
- Implementation:
  - Aggregate filtered albums by artist scrobbles, take the top ten, and select
    five unique candidates with a stable job-ID seed.
  - Render the first fallback immediately, hydrate the five artist profiles
    concurrently through the existing endpoint, and rotate locally every seven
    seconds. Reduced-motion readers keep one static candidate.
  - Removed metric sorting's competing top-album mutation and the album-ID
    fallback link. Candidate-slot, active-index, and image-revision guards keep
    late requests from replacing the active card.
  - Added a real-browser gate for five unique post-render requests and a card
    index change. The check failed when the production interval was disabled
    and passed after restoration in Chromium and Firefox.
- Follow-up: F-B21-48 records the separately scoped persistent Last.fm event
  cache. Current page-response caching is process-local, exact-range, and one
  hour only.
- Validation: `pytest -q` -- **925 passed**, 5 warnings. The latest route regression and
  frontend-gate unit subset passes 36 tests. Python/JavaScript syntax and
  docsync checks pass. The revised late-response browser harness still needs a
  clean full frontend-gate run.

### 2026-09-06 - UI copy clarity, heatmap eyebrow, and graceful page-load fade (side-task)

- Scope: applied /clarify and /audit workflows to the home → results flow; fixed heatmap partial eyebrow; added universal graceful page-load fade.
- Implementation:
  - Updated `templates/partials/_heatmap_result.html`: eyebrow changed from `"Listening heatmap"` to `"Last.fm scrobble heatmap"` to match the index hero copy style.
  - Updated `templates/index.html`: album mode lede rewritten to cut "specialized data visualization", "Enrich your scrobbles with Spotify metadata", and "isolate custom release eras" — replaced with a plain workflow description ("Choose a listening year and a release window…"). Heatmap lede: removed unexplained "rocket scale" jargon; replaced with a direct description of colour = intensity and tap-to-see interaction.
  - Added universal page-load fade to `static/css/shell.css` (`body { opacity: 0 }` + `body.is-ready { opacity: 1; transition: 220ms ease }`) and added the matching `DOMContentLoaded` trigger in `templates/base.html` (sequenced after the existing theme-before-paint inline script so dark/light theme commits before opacity resolves).
- Validation: `pytest -q` -- **924 passed**, 5 warnings.



- Scope: audited docsync tooling files (`scripts/docsync/*.py`, `.docsync.toml`) to verify DOC001-DOC011 integrity checks fire appropriately; identified and remediated three control-plane defects (F-DOCSYNC-8, F-DOCSYNC-9, F-DOCSYNC-10).
- Implementation:
  - F-DOCSYNC-8: Fixed TOML array-of-tables scoping defect in `.docsync.toml` where inserting `[[value]]` for `the wide-desktop scale cap` on 2026-08-28 detached the remaining 9 sites of `the single 860px breakpoint`. Reordered all 14 breakpoint sites contiguously (including missing frontend files `loading.css`, `empty.css`, and `theme.js`), added explicit `expect` values (`"860"` or `"859.98"`) to every site, cleanly separated the scale baseline and cap declarations, and added an architectural warning comment. Completed `expect` attributes on all 11 Adobe Fonts kit sites (`"rwy8ghw"`) and all 15 heatmap window sites (`"365"`).
  - F-DOCSYNC-9: Hardened `scripts/docsync/declarations.py:check_values` to retain `(rel_path, expect)` in `captured` when a declaration declares uniform expected values, eliminating the blind spot where partially annotated declarations skipped consistency checking between unannotated and expected sites. Added 2 regression unit tests in `tests/test_docsync_declarations.py`.
  - F-DOCSYNC-10: Hardened `scripts/docsync/integrity.py:_check_section3_next_wp` to inspect Section 3 for unlabelled `NEXT_WP_CLAIM_RE` matches when `claimed is None`, preventing silent bypass of DOC007 next-action integrity checks. Enforced canonical `- **Next action:**` bullet label in `PLAYBOOK.md` Section 3. Added regression test `test_doc007_section3_unlabelled_claim_blocks` in `tests/test_docsync_integrity.py`.
  - Updated `tests/scripts/dev/test_worktree_guard_playbook.py` `test_the_repository_playbook_parses` to reflect the active authorized worktree branch `test`.
- Validation: `pytest -q` -- **918 passed**, 5 warnings. All 296 docsync tests pass. `python scripts/doc_state_sync.py --check` exits 0 with no integrity errors.
- Forward guidance: resume owner-review remediation Task 6 (accessibility pass) per `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md` before WP-5 begins.

### 2026-09-05 - Add resilient Typekit fallback font stacks, consolidate single-row mobile navigation, and configure editor (side-task)

- Scope: resolved unknown at-rule IDE lint warning on `@custom-variant` in `static/css/tailwind.src.css`, verified Typekit web font integration, reinforced design token font stacks with resilient Typekit fallbacks (`aktiv-grotesk`, `corporate-a`, `ff-din-paneuropean`, `orator-std`), and consolidated mobile header navigation to a unified single-row bar.
- Implementation:
  - Added `.vscode/settings.json` configuring `"css.lint.unknownAtRules": "ignore"` and created `.vscode/tailwind-css-data.json` declaring Tailwind v4 at-rules (`@custom-variant`, `@theme`, `@source`, `@utility`, `@plugin`). Kept git status clean as `.vscode/` is in `.gitignore`.
  - Verified live Adobe Typekit kit (`rwy8ghw`) served by `templates/base.html` and expanded font stacks in `static/css/tailwind.src.css` and `static/css/global.css`: `--font-sans` now includes `"aktiv-grotesk"`, `--font-serif` includes `"corporate-a"`, `--font-figure` includes `"ff-din-paneuropean"` (FF DIN), and `--font-mono` / `--font-mono-narrow` include `"orator-std"`.
  - Consolidated mobile header navigation in `static/css/shell.css` from a dual-row 2x2 grid (`--shell-height: 6.5rem`) to a unified single-row 4-column stack (`--shell-height: 4.25rem`, `grid-template-columns: repeat(4, minmax(0, 1fr))`). Provenance & design rationale: opting for a one-stack bar rather than dual-row saves ~36px of vertical fold space on compact mobile viewports (320px–390px), avoids visual crowding now that the theme toggle sits below page content (F-B21-45), comfortably fits all 4 short route labels ("Index", "Heatmap", "Results", "Unmatched") at compliant >=44px tap targets, and unifies the shell height floor with desktop (`4.25rem`).
  - Synchronized `scripts/dev/frontend_gate.py` (`check_shell_scales_with_text` and `check_large_display_scale_parity` row count assertion to 1 row), updated design token regression lock in `tests/scripts/dev/test_tailwind_build_cli.py`, and rebuilt `static/css/tailwind.css` cleanly.
- Validation: `pytest -q` -- **914 passed**, 5 warnings. `python scripts/dev/tailwind_build.py --check` and `pre-commit run --all-files` passed cleanly with 0 drift and all hooks green.

### 2026-09-05 - Harden and polish frontend interfaces, align legacy Bootstrap styles, and mute index divider seam (side-task)

- Scope: executed comprehensive frontend hardening (/harden) and polish (/polish) passes across the application, aligned legacy Bootstrap pages (`results.html`, `unmatched.html`) with the Tailwind design system, and muted the index vertical dividing seam.
- Implementation:
  - Added `@media (prefers-reduced-motion: reduce)` overrides to `static/css/global.css` for card and SVG entrance animations (`opacity: 1 !important`, `animation: none !important`) and collapsed button transitions (`0.01ms !important`).
  - Added form submission resilience and double-submit guards to `static/js/index.js` (disabling `#submit-btn` and setting `aria-busy="true"`, with `pageshow` restoration) and `static/js/heatmap.js` (disabling `#heatmap-submit-btn` during active jobs).
  - Wired accessibility and defensive attributes: added `maxlength="100"` to Last.fm username inputs on both modes, bound `aria-describedby="year-hint"` to `#year`, and dynamically synchronized `role="alert"`, `aria-invalid="true"`, and `aria-describedby` across inline error and warning states in `static/js/index.js`.
  - Hardened layout against text overflow in `static/css/results.css` (`flex-shrink: 0` on `.album-cover`, `min-width: 0` and `overflow-wrap: break-word` on `.album-title` and `.album-info`), `templates/results.html` (descriptive `alt="{{ album.album }} cover"` on cover art), and `static/css/unmatched.css` (`overflow-wrap: break-word` on table cells).
  - Reskinned Bootstrap pages in `static/css/global.css`, `static/css/results.css`, and `static/css/unmatched.css`: styled `.btn` variants with mono-narrow typography, uppercase tracking, 0.625rem radius, and brand purple accents (`--shell-accent`); applied Adobe Typekit serif to display headings (`h1`, `h2`); aligned dark palette variables to authentic warm obsidian (`#0e0c12`, `#181520`, `#1f1b29`, `#2a2434`, `#1a1622`).
  - Polished design system tokens and anti-patterns: eliminated resting drop shadows on `.album-cover`, `.reason-section`, and `.action-buttons` in favor of structural hairline borders; enforced the No-Medium Rule on `.album-link` (`font-weight: 400`); replaced inline style on cover placeholder with `.album-cover-placeholder`; promoted results heading to semantic `<h1>`; aligned `.reason-count` to pill radius and 0.75rem mono label.
  - Themed browser surfaces: added custom `::selection` background (`--info-bg` / `--ss-accent-soft`) and subtle hairline `scrollbar-color` across stylesheets.
  - Muted the index vertical dividing seam (`--ss-border-divider`) by ~8% towards adjoining surfaces (`#8a867e` light, `#68646f` dark) while strictly maintaining >= 3.0:1 WCAG non-text contrast against both adjoining surfaces (`check_divider_contrast`); synchronized `static/css/tailwind.src.css`, `static/css/tailwind.css`, `.docsync.toml`, and `tests/test_template_shell.py`.
- Validation: `pytest -q` -- **914 passed**, 5 warnings. `python scripts/dev/tailwind_build.py --check` and `python scripts/doc_state_sync.py --check` pass. Live browser execution verified in Chromium and Firefox with 0 console errors and clean contrast checks.

### 2026-09-05 - Soften high-res desktop scale slope, standardize unmatched empty state, and polish warm light surface

- Scope: owner review of 1440p desktop render identified excessive vertical growth in the index card composition. Standardized the `/unmatched` empty state to match `/results` and `/heatmap`, unified the light-mode surface on warm `#fcfbf8`, and elevated the semantic heatmap headline.
- Plan vs implementation:
  - Added `@media (min-width: 1920px)` in `static/css/index.css` applying a softened slope curve `0.35 + 0.65 * (W / 1920)` above 1080p, reducing 1440p card height from 907px to 828px and 4K card height from 1358px to 1121px while strictly maintaining 1080p scale at 1.075.
  - Standardized `/unmatched` empty state via `templates/unmatched_empty.html` with `.empty-page` and `.empty-state` centered typography, purple signal bar, and primary action button; updated `scrobblescope/routes.py` and test suites.
  - Replaced stark `#ffffff` with warm `#fcfbf8` across `--ss-surface-card` in `static/css/tailwind.src.css` and rebuilt `static/css/tailwind.css`.
  - Promoted heatmap result headline to semantic `<h1>` in `templates/partials/_heatmap_result.html` and elevated desktop font size to `clamp(1.625rem, 3.75vw, 2.5rem)` (40px) while preserving neutral weight and color for usernames.
  - Updated `scripts/dev/frontend_gate.py` scale parity calculations to reflect softened curve and column-tracking wordmark geometry.
- Validation: `pytest -q` -- **914 passed**, 5 warnings. `python scripts/dev/frontend_gate.py` passed all 23 checks in 64 runs across Chromium and Firefox (desktop, mobile, wide touch). `python scripts/dev/tailwind_build.py --check` and `python scripts/doc_state_sync.py --check` pass.

### 2026-09-05 - Move the mobile theme control below page content (side-task)

- Scope: owner review found that the compact horizontal Light/Dark control sat
  midway across the two navigation rows. Its boxes did not intersect, but the
  control visually competed with both rows and made the header read as
  overlapping.
- Implementation: retain one checkbox and label, then move their actions
  wrapper between the desktop header and a mobile slot after page content via
  the existing `859.98px` breakpoint. The four-link grid now uses the full
  mobile header width. Selector scope follows the wrapper so the hidden input,
  selected state, and focus ring survive relocation on migrated and legacy
  pages.
- TDD evidence: the new rendered check failed in Chromium and Firefox at both
  390px and 320px because the control remained in the header and above page
  content. The focused gate passes after relocation and also checks the 44px
  target, two-row navigation, overflow, and body offset.
- Findings: F-B21-45 now records the owner correction and final placement.
- Validation: `pytest -q` -- **904 passed**, 5 warnings. Focused shell and gate
  tests -- **129 passed**. The complete frontend gate reports `23 checks passed
  in 64 runs across chromium, firefox`; JavaScript syntax and diff checks pass.
  All pre-commit hooks pass, including `doc-state-sync-check`; the alignment
  hook reports the expected WT003/WT010 state on the owner-authorized stacked
  Task 4 branch.
- Forward guidance: complete Task 4 review, then proceed to Task 5.

### 2026-09-05 - Refine desktop scale and mobile navigation (side-task)

- Scope: address the owner's final Task 3/4 visual comparison. The 28rem form
  felt slightly too large, its top-anchored composition accumulated much more
  space beneath the card on a realistic 1440p window than at 1080p, the mobile
  header hid report destinations behind horizontal scrolling, and the desktop
  Heatmap result remained at the snapshot's undersized 1100px measure. The
  Heatmap username also carried an unwanted purple italic accent.
- Implementation: refine the form base cap to `27.5rem` and centre its complete
  composition vertically in the available desktop well. Auto margins collapse
  when expanded rows need the space, preserving top padding and natural
  document scroll without state-dependent scaling. Mobile navigation now uses
  two directly visible rows beside a compact theme control. The desktop
  Heatmap stage uses `84vw`, capped at `120rem`, while the username inherits
  the headline's neutral serif treatment.
- TDD evidence: before the CSS changes, both engines measured unequal form
  composition gutters at every realistic desktop profile; 390px and 320px
  headers required horizontal navigation scrolling and exposed only one row;
  and a 1920x945 Heatmap result occupied 57.3% of the viewport with 16.6px
  rendered cells. The extended gate now asserts balanced vertical gutters,
  unchanged expanded-state geometry, two directly visible mobile nav rows,
  a centred Heatmap frame occupying at least 70% of the viewport, 22px-32px
  rendered cells, and a neutral username. The complete frontend gate passes
  all 23 checks in 64 runs across Chromium and Firefox.
- Findings: F-B21-44 records the desktop Heatmap scale and username treatment;
  F-B21-45 records mobile navigation overflow; F-B21-46 records the desktop
  form's top-heavy placement and cap refinement.
- Forward guidance: complete Task 4 review, then proceed to Task 5.

### 2026-09-05 - Remove the cached Heatmap loading flash (side-task)

- Scope: address the owner-observed flash when the Heatmap header link restores
  an already-complete saved job. The client exposed the loading panel before
  its first progress response, then immediately replaced it with cached data.
- Implementation: keep saved-job loading hidden through the first progress and
  data requests. Reveal it only when the response shows ongoing work, a retry,
  or an error; otherwise fade the complete result in directly. Normal Heatmap
  submissions and their polling lifecycle remain distinct and unchanged.
- TDD evidence: the new mutation observer failed against the prior client in
  Chromium and Firefox even though the final result DOM was correct. It starts
  before production `DOMContentLoaded` handlers, so it records the transient
  loading paint rather than sampling only the settled page.
- Findings: F-B21-43 records the defect and its resolution.
- Validation: `pytest -q` -- **904 passed**, 5 warnings. Focused frontend and
  route tests -- **120 passed**. The complete frontend gate reports `23 checks
  passed in 64 runs across chromium, firefox`; JavaScript syntax and diff checks
  pass. Final hooks and docsync follow before commit.
- Forward guidance: complete Task 4 review, then proceed to Task 5.

### 2026-09-05 - Pin index state geometry and normalize its fades (side-task)

- Scope: address owner review after Task 3. The state-sensitive height
  denominator made a fixed 1920x945 window shrink the 481.6px form to 390.5px
  for a release field, 357.8px for thresholds, and 325.2px when both were
  open; the hero and every scale-authored dimension changed with it. Mode-copy
  motion also ran sequential 110ms and 180ms animations while page entrance
  took 1.2s after a 0.2s delay and Heatmap stage fades took 300ms.
- Implementation: removed the three reachable-state height overrides. The
  fixed window alone now selects `--index-scale`; opening rows adds natural
  document height. A stable root scrollbar gutter prevents Firefox's first
  scrollbar from shifting the 3fr/4fr columns. Both hero descriptions reserve
  one overlaid grid track, expose the active copy with `aria-hidden`, and
  crossfade concurrently. Index entrance, hero copy, and Heatmap stage opacity
  changes now use one 180ms duration with an immediate reduced-motion state.
- TDD evidence: the pre-fix browser run failed in both engines and reported
  every changed form, hero, type, spacing, and control dimension plus the
  expanded state's missing document scroll. The permanent gate now drives six
  states at the realistic 1920x945 content box and compares representative
  rendered dimensions. An adversarial unit test proves material and missing
  measurements fail; a route test pins the stable hero-copy structure.
- Review cleanup: replaced the one implicit string concatenation called out on
  PR #225 and corrected Task 3's stale illustrative commit ID from `c1f10e6`
  to the actual `8b37566`.
- Findings: F-B21-41 records the state-dependent resize and F-B21-42 records
  the inconsistent motion. F-B21-38 now identifies its state-sensitive
  implementation as superseded.
- Validation after stacking on the Task 4 branch: `pytest -q` -- **904 passed**,
  5 warnings. The complete frontend gate reports `23 checks passed in 64 runs
  across chromium, firefox`; hooks and final docsync follow before commit.
- Forward guidance: correct the cached-Heatmap restoration flash on PR #226
  with the loading-progress work, then complete Task 4 review.

### 2026-09-05 - Close out the Task 4 session and stack its PR (side-task)

- Scope: session close-out after Task 4's implementation pass. Corrected the
  dangling pre-amend commit reference (`21b5198` -> `e0219b2`) in Section 3,
  in the Task 4 entry's forward guidance, and in the plan's Task 4 checkpoint
  -- a commit cannot contain its own SHA, so SHA references land after the
  commit they name. Added the dated handoff document
  `docs/superpowers/handoffs/2026-09-05-batch21-task-4-review-handoff.md`.
- Plan vs implementation: as intended by the owner's close-out instruction.
  Task 4's commit and this handoff are published on the stacked branch
  `wip/batch-21-task-4` (base `wip/batch-21`) so PR #225 stays scoped to
  Task 3; local `wip/batch-21` is intentionally ahead of its origin until
  PR #225 merges and the WT004 realign ritual runs.
- Deviations: none of record; the implementer's amend-within-its-own-pass
  produced the dangling SHA this entry corrects.
- Validation: `pytest -q` -- **902 passed** (unchanged by this docs-only
  commit). `pre-commit run --all-files` -- all hooks pass.
  `doc_state_sync.py --check` -- exit 0 (expected root-definition warning).
- Forward guidance: the next session reviews Task 4 (SDD task review, then
  fix loop if needed), then Tasks 5 and 6 per the plan; the handoff doc is
  the map. PR #225 (Task 3) remains draft awaiting owner review.

### 2026-09-05 - Align loading signals with pipeline phases (side-task)

- Scope: Task 4 of the Batch 21 owner-review remediation plan. Align visible
  loading progress with pipeline phases for both Top Albums and Heatmap clients,
  eliminate overlapping interval polls and stale out-of-order response application
  (F-B21-33), decouple received vs attempted Last.fm counts, and implement loading
  composition corrections (F-B21-36).
- Plan vs implementation:
  - Repository layer: Added `_UNSET` sentinel to `set_job_progress` for `phase`,
    allowing progress/message updates without clobbering an active phase; updated
    `set_job_error` to clear `phase=None`; isolated phase dicts in
    `get_job_progress` and `get_job_context` via `copy.deepcopy` to prevent caller
    or internal mutations from leaking across boundaries.
  - Route layer: `/progress` returns `phase` when present in progress dictionary.
  - Orchestrator and services: Emitted explicit `lastfm_fetch`, `spotify_search`,
    and `spotify_details` phases with unit, current, total counts in `orchestrator.py`
    and `heatmap.py`. Updated `lastfm.py` to decouple received vs attempted pages via
    `pages_received`. Cleared `phase=None` on uncounted states (initialization,
    counting, filtering, error, 100% completion).
  - Browser helper (`static/js/loading-progress.js`): Non-module global
    `window.ScrobbleProgress` providing `displayPercent(payload)`, `label(payload)`,
    and `update(options)`. Manages instant bar reset on phase change, ARIA attributes
    (`aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext`), and
    formatted phase lines.
  - Polling clients: Integrated `ScrobbleProgress` into `loading.js` and `heatmap.js`.
    Added `pollInFlight`, `pollSeq`, and `latestAppliedPollSeq` to drop out-of-order or
    stale responses and prevent overlapping interval fetches.
  - Loading composition: Removed duplicate phase sentence `<p class="heatmap-loading__detail">`
    and `<li>rocket scale</li>` in `_heatmap_loading_details.html`. Styled stat items in
    flex container with centering, 18rem max-width, and divider rules
    (`:not(.hidden) ~ :not(.hidden)`). Added `@keyframes wait-fade-in` (200ms ease-out)
    with `@media (prefers-reduced-motion: reduce)` cancellation restoring `opacity: 1`.
  - Frontend gate: Added unit tests for new gate helpers (`_parse_matrix_scalex`,
    `_assert_loading_progress_state`) in `test_frontend_gate.py`. Implemented
    `_exercise_loading_progress_phases` testing sequential frames, zero totals,
    100% phase without result navigation, flex centering, and stale response rejection
    across Chromium and Firefox.
- Deviations: none. All requirements from the task brief implemented strictly.
- Validation: `pytest -q` -- **902 passed**, 5 warnings (8 new tests across
  test_repositories, test_routes, test_orchestrator, test_heatmap, test_lastfm_service,
  test_frontend_gate). Frontend gate: `23 checks passed in 64 runs across chromium,
  firefox`. Prohibited animation sweep (`rg -n 'transition:\s*(width|height|padding|margin|max-width)' static\css static\js`)
  returned 0 matches.
- Forward guidance: Task 4 implemented and validated locally in commit e0219b2;
  awaiting task review (spec and quality review is pending as the next action,
  followed by Task 5 per the plan order).

### 2026-09-05 - Remediate Task 3 review feedback, fill the hero to its column (side-task)

- Scope: fix round 2/5 for Task 3 owner-review feedback (not a FINDINGS
  entry -- rendered-evidence feedback, not a review finding): "scale the
  wordmark and hero up to the edge". `.index-hero__inner`'s width (and the
  matching `.index-hero__mark` cap) were bound to `calc(35rem *
  var(--index-scale))`, which the owner's measured evidence showed
  rendering narrower than the padded hero column in every state -- most
  visibly in the height-guard-driven expanded state (decade selected,
  thresholds open), where the hero visibly shrank as the form grew.
- Plan vs implementation: replaced the `35rem * scale` basis on both
  `.index-hero__inner` (`width: 100%`) and `.index-hero__mark` (`max-width:
  100%`) inside the existing `@media (min-width: 1200px)` block, so hero
  content (wordmark, headline, lede, capability marks) fills to the
  padding edge in every state. The two rules stay identical twins, as they
  were before this change (both previously read the same `35rem * scale`
  value), so wordmark width keeps tracking hero-inner width exactly with no
  separate rule needed. Nothing below 1200px, the hero's own padding
  (`3.5rem * scale`), the lede's `38ch` measure, the form side (3fr 4fr
  split, 28rem cap, height bounds), the header clamps, or either divider
  token was touched, per the owner's explicit "do not touch" list.
- TDD evidence: extended `check_large_display_scale_parity` in
  `scripts/dev/frontend_gate.py` (`measure_wide_layout` and
  `measure_compact_height`) to read the hero's own padding, its column
  width, `.index-hero__inner`'s rendered width, and `.index-hero__mark`'s
  rendered width, then assert hero-inner fills its padded column (within
  1px) and mark tracks inner (within 1px), across all four real windows
  (1080p, 1200p measured, 1440p, 4K) plus the driven decade+thresholds
  expanded state. A genuine RED run against the pre-fix CSS produced
  exactly 5 failures: hero inner at 602.0px against a 702.4px column
  (1080p and 1200p measured, same viewport width), 802.7px against 936.6px
  (1440p), 1204.0px against 1404.9px (4K), and 400.3px against 742.8px in
  the expanded state -- confirming the owner's diagnosis empirically (my
  own hand-derivation independently produced the same 602.0px and 702.4px
  figures before the browser run). No "mark not tracking inner" failures
  appeared even pre-fix, because the two rules were already numerically
  identical. Applying the CSS fix produced GREEN in both engines
  individually, then a full gate GREEN: `23 checks passed in 64 runs across
  chromium, firefox` (check count unchanged; this extends two existing
  measurement helpers rather than adding a new check).
- Validation: full-suite `pytest -q` -- **894 passed**, 5 warnings
  (unchanged; this is a gate-level browser-measurement change with no new
  pytest-collected unit test, since no new Python helper function was
  introduced -- the assertions read directly from browser-measured
  rectangles already exposed by the existing helpers). All pre-commit
  hooks and `doc_state_sync.py --check` passed on the final document
  state.
- Forward guidance: Task 3's remaining review rounds (3/5 through 5/5) and
  the seven parked Minor findings proceed separately; Task 4 remains the
  next batch-order item once Task 3's review is fully closed.

### 2026-09-05 - Remediate Task 3 review finding, raise the index well divider (side-task)

- Scope: fix round 1/5 for the Task 3 owner-review finding "the index
  page's own dividers were not raised, and the new check cannot see them".
  `.index-form`'s `border-left` drew from the shared, still-opaque
  `--ss-border-default` (measured ~1.12:1 light, ~1.18:1 dark against its
  adjoining surfaces), which Task 3's `--shell-border` fix never touched.
  Owner ruling: add a dedicated index-only divider token rather than
  restyling the other 14 `--ss-border-default` uses in `index.css`.
- Plan vs implementation: added `--ss-border-divider` (`#858179` light,
  `#6e6a75` dark) to both daisyUI theme blocks in
  `static/css/tailwind.src.css`, applied only to `.index-form`'s
  `border-left` in `static/css/index.css`, and regenerated
  `static/css/tailwind.css` with the qualified `tailwind_build.py` (this
  time producing a genuine 3-line diff, since the token is new -- unlike
  Task 3, where the same build produced no drift). `check_divider_contrast`
  in `scripts/dev/frontend_gate.py` now also reads `.index-form`'s real
  rendered `border-left-color` against `--color-base-100` and
  `--ss-surface-sunken` in both themes and engines, reusing the existing
  minimum-across-surfaces helper. `_divider_contrast_failure` gained a
  `token` parameter (default `--shell-border`, preserving every existing
  call site) so the new failure message names `--ss-border-divider`
  instead of misattributing it.
- TDD evidence: a genuine RED run against the pre-fix CSS (extended gate
  assertion in place, `.index-form` still on `--ss-border-default`)
  produced exactly 4 failures -- index divider light/dark in both
  Chromium and Firefox, reporting `1.12:1` and `1.18:1`, matching the
  reviewer's hand-computed ratios exactly. Applying the CSS fix produced a
  genuine GREEN run: `23 checks passed in 64 runs across chromium,
  firefox` (check count unchanged; this extends an existing check rather
  than adding a new one).
- Measured divider contrast (both engines agreed): light vs page
  3.65:1, vs sunken well 3.26:1 (binding); dark vs page 3.69:1, vs sunken
  well 3.37:1 (binding). Both clear the 3:1 floor with comparable headroom
  to Task 3's shell-border ratios.
- Test additions: `--ss-border-divider` added to `INDEX_TOKENS` in
  `tests/test_template_shell.py` (covered by the existing parametrized
  token-build test, no new test function needed). One new adversarial unit
  test in `tests/scripts/dev/test_frontend_gate.py` asserting
  `_divider_contrast_failure`'s `token` parameter is honoured and that the
  default stays `--shell-border` for existing callers. A new
  `.docsync.toml` pair of `[[value]]` declarations pins the token's light
  and dark values across `tailwind.src.css` (both theme blocks) and
  `tests/test_template_shell.py`.
- Validation: full-suite `pytest -q` -- **894 passed**, 5 warnings (892
  baseline plus the 2 new tests above). The complete frontend gate passed
  23 checks in 64 runs across Chromium and Firefox. All pre-commit hooks
  and `doc_state_sync.py --check` passed on the final document state.
- Forward guidance: FINDINGS.md F-B21-40 records this defect and its
  resolution. Task 3's broader remaining review rounds (2/5 through 5/5)
  and the seven parked Minor findings are unaffected and proceed
  separately; Task 4 remains the next batch-order item once Task 3's
  review is fully closed.

### 2026-09-05 - Implement remediation Task 3, widen composition and raise divider contrast (side-task)

- Scope: land the final desktop index composition and divider-contrast fix
  from the canonical remediation plan. Widen `static/css/index.css`'s
  `min-width: 1200px` split from `3fr 5fr` to `3fr 4fr` and raise the form's
  unscaled base cap from `23.75rem` to `28rem` (both scaled by the shared
  `--index-scale` factor). Raise `static/css/shell.css`'s `--shell-border`
  alpha in both themes so the composited divider clears 3:1 against every
  adjacent surface, and apply the recorded header ruling: a
  `--shell-height: clamp(4.25rem, 2.96875vw, 4.75rem)` bar, a shared
  `--shell-control-gap: 0.75rem` token on `.site-header` and
  `.site-header__nav`, and matching size clamps on the nav link and theme
  controls.
- Plan vs implementation: `check_large_display_scale_parity` in
  `scripts/dev/frontend_gate.py` gained a divider-contrast check (the
  composited colour, not the token string), ruled header-geometry
  assertions at real 1080p/1440p windows, and zoom/transform prohibitions on
  the form wrapper; the retuned split and form-cap assertions replaced the
  Task 2 originals in place, matching the plan's instruction not to leave
  the old assertions standing. A genuine RED run against the pre-fix CSS
  produced 28 failures (14 per engine, both Chromium and Firefox): divider
  contrast (1.27:1 light, 1.40:1 dark), the 5:3 split, the 23.75rem-based
  form cap at 1080p/1440p/4K, the unruled 76px header bar and 48px/116px
  nav-link geometry, the 48.4px theme control, and mismatched header/nav
  gap tokens. Applying the CSS produced a genuine GREEN run: `23 checks
  passed in 64 runs across chromium, firefox`. Mutation-checks confirmed the
  zoom and transform prohibitions are load-bearing: temporarily adding
  `zoom: 1.1` and then `transform: scale(1.1)` to `.index-form__inner` each
  reproduced the gate failure; both were reverted before commit.
- Measured divider contrast: light `rgba(26, 24, 32, 0.5)` composites to
  3.23:1 against the light surface token (worst adjacent case, up from
  1.27:1); dark `rgba(241, 237, 228, 0.4)` composites to 3.42:1 (up from
  1.40:1). Both clear the 3:1 floor with headroom.
- Test additions: 7 adversarial unit tests in
  `tests/scripts/dev/test_frontend_gate.py` for the new colour-math helpers
  (`_parse_rgb_string`, `_composite_over`, `_relative_luminance`,
  `_contrast_ratio`, `_worst_divider_contrast`, `_divider_contrast_failure`,
  `_clamp_px`), including an exact-3.0-passes/2.9999-fails boundary case;
  the existing wrapped-headline test was updated for the new per-width
  `_headline_wrap_failures(probe, width)` signature (1200, 1500, 1920,
  2560px, both modes). 4 source-level tests were added to
  `tests/test_template_shell.py` for the shared control-gap token, the
  `--shell-height` clamp, the nav-link/theme-control size clamps, and the
  new divider alphas.
- Deviations: a background gate run was started immediately after the CSS
  was already in its final (GREEN) state, before any genuine RED evidence
  had been captured -- a TDD-ordering slip. Corrected before proceeding:
  `git stash push --keep-index` reverted only the two CSS files to their
  pre-fix state while keeping the new gate assertions in the working tree,
  the RED run above was captured against that state, then `git stash pop`
  restored the GREEN CSS and the gate was re-run clean. No code was
  rewritten; only the evidence-capture order was corrected.
- Validation: `pytest -q tests/scripts/dev/test_frontend_gate.py` --
  **31 passed**; `pytest -q tests/test_template_shell.py` -- **93 passed**;
  full-suite `pytest -q` -- **892 passed**, 5 warnings (881 baseline plus
  the 11 new tests above). The complete frontend gate passed 23 checks in
  64 runs across Chromium and Firefox. All pre-commit hooks and
  `doc_state_sync.py --check` passed on the final document state.
- Forward guidance: Task 4 (align visible loading progress with pipeline
  phases) is next per the canonical plan. Tasks 5 and 6 remain open. PR #224
  (Task 2) merged; PLAYBOOK Section 3 corrected the stale "awaits owner
  review" framing.

### 2026-09-05 - Close PR #224 complexity follow-up (side-task)

- Scope: address Qlty's fresh analysis of the first Task 2 review-fix commit.
  The shared font expression and browser closure findings cleared, while the
  desktop-boundary helper remained one point over its complexity threshold.
- Review remediation: extracted the headline-wrap branch into a focused helper
  and exercised that helper directly through the existing adversarial boundary
  test. This removes nested control flow from the browser orchestration without
  changing its rendered assertions.
- Validation: focused frontend-gate tests passed **24 tests**; `pytest -q` --
  **881 passed**, 5 warnings. The complete gate passed 22 checks in 62 runs
  across Chromium and Firefox. All pre-commit hooks and docsync passed on the
  final document state.
- Forward guidance: await the refreshed Qlty and Quality Gate checks on PR
  #224. Task 3 remains next after owner review.

### 2026-09-05 - Remediate PR #224 Task 2 review (side-task)

- Scope: restore Task 2's original authored form geometry, harden its browser
  gate, and reconcile live status documents found during owner and bot review.
  Task 3's `3fr 4fr` split and `28rem` base form cap remain untouched.
- Review dispositions: restored the three `0.25rem` gap bases and scaled `9rem`
  mode-tab minimum; added an adversarial wrapped-headline helper test; shared
  the repeated font-ready expression; removed the late-bound browser closure;
  reduced the flagged helper complexity; and repaired the DOCSYNC marker plus
  stale Task 2/two-engine claims. F-B21-39 owns the defect record.
- Declined bot findings: the sixteen Bandit B101 comments target pytest
  assertions, where assertion rewriting is the test framework's contract.
  Graphify's missing-selector and unscaled-headline claims do not match current
  source, and failure when either required browser is unavailable is explicit
  Task 2 acceptance behavior.
- Validation: focused frontend-gate tests passed **24 tests**; `pytest -q` --
  **881 passed**, 5 warnings. The complete gate passed 22 checks in 62 runs
  across Chromium and Firefox. All pre-commit hooks and docsync passed on the
  final document state.
- Forward guidance: Task 2 awaits owner review on PR #224. Task 3 remains the
  next implementation task and owns the final split and form cap.

### 2026-09-05 - Implement layout-aware desktop scaling, Task 2 (side-task)

- Scope: complete Chromium and Firefox gate lifecycle, realistic window
  profiles, and explicit CSS composition dimensions. Task 3's final split and
  base form width are unchanged. Adobe remains the font provider.
- Plan vs implementation: the initial complete gate failed on the old scale
  path in both engines. The first replacement run exposed contracted touch
  inputs and an expanded form taller than the plan's 673px baseline.
  F-B21-38 owns the measured boundary and expanded-state correction.
- Deviations: scale hero gutters with the complete composition and retain
  readable type and coarse-pointer lower bounds below the reference width.
  The entire two-engine gate should take roughly twice its former wall time.
- Validation: the complete two-engine gate passed in isolation -- 22 checks
  in 62 runs across Chromium and Firefox -- after one Chromium pipeline
  timeout and one Firefox socket-in-use failure that appeared only while
  unrelated browser work ran concurrently and never reproduced cleanly.
  Rendered geometry and screenshots were recaptured for both engines at
  1080p, 1440p, the 1200px boundary, mobile, and the 1920x900 expanded fit;
  wrappers compute `transform: none` and `zoom: 1` everywhere. The focused
  runner suite passed 23 tests; full pytest was **880 passed**, 5 warnings.
  All pre-commit hooks and docsync passed. The final gate and suite ran at
  close of this entry.
- Landing: committed as `ac6b1b1`, pushed to `origin/wip/batch-21`, and
  opened as PR #224 with owner authorization on 2026-09-05. All nine Task 2
  plan steps are checked off in the canonical plan.
- Forward guidance: Task 2 awaits PR review and merge. Task 3 is next, as
  its own commit and review cycle. Do not start WP-5 until Task 3 lands.
- After any edit here, run `python scripts/doc_state_sync.py --fix`.

### 2026-09-04 - Preserve owner-plan provenance and late review decisions (side-task)

- Scope: track the original September 1 owner-review proposal with an explicit
  historical/non-executable banner, and identify its superseding execution
  plan. Ignore generated `graphify-out/` while preserving and querying it
  locally. Planning documents remain tracked rather than ignored.
- Review corrections: pin the remaining captured snapshot kit URL; express the
  planned natural-height guard in rem and require enlarged-root browser checks;
  record Adobe Fonts ownership and the loading screenshot corrections.
  F-B21-34 and F-B21-35 record plan/config fixes; F-B21-36 remains implementation
  work. F-B21-37 records PR #223's completed documentation repair.
- Plan vs implementation: no production scaling or loading behavior changed.
  The old proposal stays intact below its supersession notice, including old
  instructions. The active plan owns execution and the owner rulings win.
- Deviations: defer the unfinished Task 2 test-first changes from this commit;
  preserve and restore them locally after validation. The owner approved this
  documentation commit; no push is requested. `.impeccable/` and `PRODUCT.md`
  remain untracked and preserved.
- Validation: `pytest -q`: **872 passed**, 5 warnings on the commit candidate
  with the unfinished tests shelved. Run hooks and docsync before commit.
  No production UI changed; PR #223 already passed both browser gates.
- Forward guidance: resume Task 2 of the canonical scaling/remediation plan
  before WP-5. Query the local graph as navigation, then verify current source.
  On 2026-09-04, headed Chrome at DPR 1 measured 2560x1305 content inside
  2560x1392 outer bounds on the 2560x1440 monitor; the second 1920x1200 monitor
  measured 1920x1065 content inside 1920x1152 outer bounds. Other panel profiles
  remain derived rather than physically measured. Both browsers must execute
  the full gate. Late PR #221 threads 3938613706 and 3938613711 have local fixes
  recorded here; reply/resolve only after these fixes are published. PR #223
  is merged; issue #222 stays open for its remaining complexity targets.

### 2026-09-04 - Review three complexity extractions in PR #223 (side-task)

- Scope: split loading progress error/poll/redirect handling, index filter-label
  selection, and optional semaphore/retry timing into focused helpers.
- Plan vs implementation: this is partial issue #222 remediation, not closure
  of its full complexity inventory. Existing behavior and public contracts stay
  unchanged. Added purpose comments to the extracted JavaScript helpers.
- Deviations: the initial PR body described only loading.js and incorrectly
  closed the broader issue. Correct the title/body before merge. The original
  Copilot commits carry prohibited co-author trailers; use a clean squash
  message at integration rather than rewrite the author's branch.
- Validation: `pytest -q`: **872 passed**, 5 warnings. The complete Firefox
  gate passed 22 checks in 31 runs locally; Chromium passed the same 22 checks
  in 31 runs in PR CI. Final pre-commit and docsync checks run before commit.
- Forward guidance: resume the owner-review scaling plan before WP-5. These
  extractions do not implement its loading-count or layout corrections.

### 2026-09-04 - Clear PR #221 plan-review follow-ups (side-task)

- Scope: corrected the execution plan and repository-authored Markdown before
  the owner-authorized PR merge. Production scaling remains Task 2.
- Review dispositions: reaffirmed accurate visible phase counts after checking
  the September 1 owner-remediation plan and obtaining the owner's ruling;
  required
  nested phase-copy isolation through both repository readers, and normalized
  the batch definition, reconciliation and Graphify report to ASCII. Filed
  F-B21-31 and F-B21-32 with the evidence and implementation boundary. The
  polling audit reproduced stale heatmap responses and found received-page
  counts sourced from attempts; F-B21-33 remains open for Task 4. Sharing a
  renderer must preserve the different album and heatmap pipeline state.
- Plan vs implementation: verified completed snapshot work is marked without
  rerunning historical failing steps. The touch-declaration deadlock stays
  deferred until its minimum changes. The header advisory confused 1440p with
  a 1440px width: 2.96875vw reaches 76px at 2560px, as intended.
- Deviations: no production scope added. The broad README refresh stays in
  WP-8; Firefox setup documentation will change with Task 2. Preserve and query
  the local Graphify data; no ignore rule, graph rebuild or plugin update is
  part of this review fix. Older fixed-form and hero-only rulings remain dated
  history and are superseded by the final complete-composition direction.
- Validation: `pytest -q` -- **872 passed**, 5 warnings. The frontend gate
  reports 22 checks passed in 31 runs. All 12 pre-commit hooks and docsync
  pass; the snapshot remains byte-identical and WT000 confirms alignment.
- Forward guidance: refresh the PR body, post one batched review disposition,
  and resolve only addressed threads. The owner authorized merging once review
  is clear, then continuing Task 2 in this same worktree before WP-5.

### 2026-09-04 - Reconcile PR #221 review with final scale direction (side-task)

- Scope: documentation and one provenance test. Audited all nine unresolved
  inline threads on PR #221 plus Graphify's earlier review-body advisory against
  the current files, the stashed scale checkpoints, and the owner's final
  direction. No production CSS, JavaScript, template or browser-gate behavior
  changed in this review-fix commit.
- Owner direction: the earlier hero-only zoom and fixed 600px form rulings are
  superseded. Hero, wordmark, form, type, controls and spacing grow together
  through explicit layout values from 1080p through the 4K ceiling. CSS zoom,
  browser zoom and visual scale transforms are forbidden; the header remains an
  independently sized shell. The plan now treats its untracked predecessor as
  outcome evidence, not executable mechanism.
- Review remediation: Task 2 now retires zoom-property assertions in favor of
  rendered rectangles and ratios, uses realistic window content boxes, runs the
  complete gate in Chromium and Firefox locally and in CI, migrates the root
  `.docsync.toml` declarations when the JavaScript constants disappear, and
  keeps the generic docsync implementation repository-independent. Task 3 uses
  the 3:4 split and a proportional 28rem base form cap, keeps controls in that
  same scale relationship, implements the already-ruled header clamps, and
  mutation-checks that zoom and transform scaling stay absent.
- Snapshot and command guards: `tests/test_design_snapshot.py` now hashes one
  deterministic manifest of all 61 imported design paths and bytes while
  excluding repository-owned `RECONCILIATION.md`; edits, additions, deletions
  and renames all invalidate it. Repository-relative POSIX path sorting keeps
  the aggregate order identical on Windows and Linux. Its pytest assertion
  carries an explicit B101 suppression. The historical restore instruction now
  uses `git restore` instead of a PowerShell pipeline that could concatenate
  lines.
- Test-count check: the observed 871/872 discrepancy crossed two different
  commits while another process advanced the branch. The current tree and all
  live records agree on 872. Docsync validates the latest recorded `pytest -q`
  result but deliberately does not execute pytest, so no same-revision docsync
  defect was reproduced. A future generic control-plane hardening would guard
  that HEAD did not change across a validation run, not encode a
  ScrobbleScope-specific test-count rule.
- Stash audit: `checkpoint/pr220-deferred-loading-progress-build` and
  `checkpoint/pr220-scale-isolated-gates` confirm the complete-composition
  relationship and a wider form, but both use the rejected CSS-zoom mechanism
  and the old 1080px height denominator. Neither stash was applied or changed.
- Validation: the focused snapshot test passes, and a temporary 62nd imported
  file made it fail before removal and a clean rerun. `pytest -q` reports
  **872 passed**, 5 warnings. The frontend gate reports 22 checks passed in 31
  runs across desktop, mobile and wide touch. All 12 pre-commit hooks,
  `doc_state_sync.py --check`, `git diff --check`, and the worktree guard pass;
  WT010 is the expected dirty-tree warning and WT000 confirms branch alignment.

### 2026-09-04 - Graphify knowledge-graph build and audit published (side-task)

- Scope: built a graphify knowledge graph over the worktree corpus (301
  files, ~375k words) and published the report at
  `docs/history/reports/GRAPHIFY_AUDIT_2026-09-04.md`. The graph reflects
  `wip/batch-21` at `ee285ac`, not `origin/main` -- a provenance block in
  the report head says so, so an agent bootstrapping from `origin/main`
  knows the docs-layer nodes describe unmerged work. The graph itself
  stays untracked in `graphify-out/`; the report is the tracked record.
  Built so agents can understand the repository faster at bootstrap.
- Build shape: 3,103 nodes, 5,896 edges, 248 communities (2,387 AST from
  code + 739 semantic from docs). Semantic extraction ran as 18 subagent
  chunks after two full-size chunks repeatedly failed on provider stream
  errors; smaller chunks succeeded. Top 15 communities were named from
  their top node labels; the long tail keeps default names.
- Verification notes are in the report head. Two of its own suggestions
  were traced and disproved as extraction artifacts: the `_reach_state()`
  "bridge" rests on one INFERRED exception-as-callee edge, and the `patch`
  node's 133 INFERRED edges are `unittest.mock.patch` test wiring. The
  verified-genuine findings are the `create_app()` hub bridging factory,
  gate, config and shell-test communities, and the Batch 11-13 log edges
  into the `orchestrator.py` and `utils.py` functions those batches
  shipped.
- Corpus exclusion recorded in the report:
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` was excluded from
  semantic extraction as too large to parse; its durable content is
  represented by the batch definitions and per-batch logs, which were
  extracted.
- Plan vs implementation: no production code changed. This is a read-only
  research artifact plus its publication commit. The pipeline integration
  question (docsync declarations pinning graph facts, automated rebuilds)
  is deferred to the future extraction batch described in `AGENT_NOTES.md`;
  nothing was wired into any gate.
- Deviations: none.
- Validation: `pytest -q` -- **872 passed**. All 12 pre-commit hooks pass.
  Worktree guard exits 0. `doc_state_sync.py --check` exits 0.
- Forward guidance: future agents can query the graph with
  `graphify query "<question>"` from the worktree; `graphify --update`
  re-extracts only changed files. Read the report head before trusting any
  "surprising connection" it suggests -- two of five were artifacts.

### 2026-09-02 - Remediate PR #221 review round one (side-task)

- Scope: documentation and tests. Six bot findings on PR #221, from Codex, qlty
  and Graphify. All six were verified against the code before any edit; none was
  a hallucinated line range.
- Gate assertions: the remediation plan told an executor to add gate checks
  without retiring the ones they contradict, so its own Task 2 Step 5 could not
  pass. `check_large_display_scale_parity` still required the form composition
  to carry `zoom`, treated the input and mode-tab heights as scalable, and
  derived the form width from the superseded `23.75rem` cap times a scale the
  form no longer carries. Task 2 Step 2 now names all four assertions to retire
  and why.
- Sweep beyond the reported instance: the same defect class appeared twice more
  in the plan and neither was reported. Task 3 Step 1 added a `3fr 4fr` split
  check alongside the existing 5:3 assertion instead of retuning it, and did so
  through `grid_left` and `grid_right` keys that `measure_wide_layout` does not
  return. Both expected-FAIL messages also named stale figures. Fixed together,
  per `AGENTS.md` Anti-Pattern 11.
- Step numbering was left alone deliberately. This plan cites its own
  "Task 2 Step 6", so the retirement instructions extend Step 2 in place rather
  than inserting a step and breaking that citation.
- Plan vs implementation: no implementation. No production code, CSS or gate
  code changed in this commit; the plan describes the gate edits for Task 2.
- Deviations: none.
- Validation: **872 passed**. All 12 pre-commit hooks pass. Worktree guard
  exits 0. `doc_state_sync.py --check` exits 0.
- Forward guidance: three findings from the same round remain -- the `clamp()`
  floor, the acceptance contradiction, and the snapshot digest set. They are
  separate commits because each is independently revertable.

### 2026-09-02 - Record the header, H1 and browser-baseline rulings (side-task)

- Scope: documentation only. Three owner rulings and one measured defect class,
  added to the remediation plan before its Task 2 begins.
- Header: it scales with the viewport, and the baseline is the 1440p rendering
  rather than the 1080p one, so the header becomes smaller at 1080p than it is
  today. Floor is 44px on the smaller side, because a strict viewport fraction
  takes the 48px link to 36px at 1080p, under the minimum in `AGENTS.md` "UI
  and Accessibility Rules" item 2 and reversing the 48px desktop target from
  F-B21-29. The header keeps its own sizing and stays outside the composition
  scale.
- H1: it must not wrap at any desktop width, not only when maximised. The cause
  is that the composition scale is floored at its base and can only grow, so a
  narrowing hero column starves the headline. The remedy is a lower bound on
  the composition scale, not a fluid headline, because the annotation requires
  the logo-to-H1 ratio to stay fixed and scaling the composition preserves it.
- Browser baseline: a default fresh Chrome install, maximised, no extensions,
  no bookmarks bar, 100% zoom. Measure it with `channel="chrome"` and a fresh
  temporary profile; do not measure the owner's daily profile and do not infer
  a chrome height from whether a bookmarks bar is showing.
- Defect class worth naming: three declarations in this page read as responsive
  and are pinned where it matters. The composition's `min()` discards the width
  term, the header's `7.25vw` saturates near 1600px, and the H1's `6vw`
  saturates near 700px. Compute where a `clamp()` or `min()` saturates before
  trusting it.
- Form card width: the `28rem` cap is superseded. The owner widened the card in
  Chrome DevTools, source untouched, and ruled the wider card the better
  default. The card widens past `28rem` and then locks, still never zoomed; the
  controls do not inherit that width. The card caps at `37.5rem` (600px),
  the value the owner reached in DevTools. It locks at 1920px, so 1080p and
  1440p both render a 600px card -- the same visual size on both. Whether to pair fields at
  the wider card is open and needs an owner ruling.
- Correction: `docs/design/RECONCILIATION.md` still carried the disproved
  Firefox premise and cited the superseded plan. The earlier commit corrected
  `FINDINGS.md` and `BATCH21_DEFINITION.md` and missed this third copy --
  Anti-Pattern 11 in the same session that quoted it. Swept and fixed here.
- Plan vs implementation: no implementation. No production code, CSS or gate
  code changed.
- Deviations: none.
- Validation: **872 passed**. All 12 pre-commit hooks pass. Worktree guard
  exits 0. `doc_state_sync.py --check` exits 0.
- Forward guidance: Task 2 is next and must take two measurements before it
  writes any number -- the fresh-Chrome window geometry, and the largest
  composition scale at which the H1 holds one line at the 1200px breakpoint.

### 2026-09-01 - Diagnose the large-display scale defect and supersede its plan (side-task)

- Scope: documentation only. No production code, CSS or gate code changed.
  Measured the large-display scale defect, replaced the remediation plan that
  rested on a disproved premise, and corrected every live document that
  repeated it.
- Cause found: `syncWideDesktopScale` divides window height by the 1080px
  design viewport instead of by the composition's own 673px height. The
  `min()` is unconditional, so browser chrome -- which costs 130-330px of
  height and almost no width -- makes the height term win on every real
  window and the width term is discarded.
- Why no gate caught it: `check_large_display_scale_parity` measures
  1920x1080, 2560x1440 and 3840x2160. `page.set_viewport_size` sets the
  content box to exactly those numbers, so the gate tests a geometry no
  maximised browser reports. The gate saw 33% growth; the owner saw 2.9%.
- Premise disproved: the superseded plan gated acceptance on Firefox.
  Chromium and Firefox measured the same composition width to within 0.1px at
  four window sizes, so the defect is engine-independent. Playwright's Firefox
  build is installed and launches at version 153.0, so dual-engine checks are
  available without a download; the owner adopted them for the scale check.
- Plan vs implementation: no implementation. The plan at
  `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`
  supersedes `docs/superpowers/plans/2026-09-01-owner-review-remediation.md`,
  whose Task 1 rested on four claims measurement disproved. Its Task 1 is
  already complete: it landed as `eeaa1a8` on this branch, unpushed, from a
  concurrent session. Work starts at Task 2.
- Deviations: none. The branch was moved from `wip/batch-21-owner-review` to
  `wip/batch-21` on the owner's ruling, because PLAYBOOK Section 3 names the
  latter and the guard raised WT003. Local `wip/batch-21` was reset to
  `origin/main`; `aadf2b7` is unchanged on `origin/wip/batch-21` and its
  content is already in `origin/main`. A later push needs
  `--force-with-lease` and a separate owner ruling.
- Validation: **872 passed**. All 12 pre-commit hooks pass. Worktree guard exits 0.
  `doc_state_sync.py --check` exits 0.
- Forward guidance: start at Task 2, which fixes the gate geometry and the
  scale together because the gate change alone turns the suite red. Two owner
  rulings are recorded in the plan and must not be re-derived: the hero scales
  proportionally while the form widens and then locks, never zoomed; and
  ultrawide is out of scope. The nested-card slider and any widening past
  `28rem` stay behind a fresh owner review.

### 2026-09-01 - Restore design snapshot provenance and re-home overrides (side-task)

- Scope: restore `docs/design/README.md` to its verbatim import at `b4e23bf` and
  move the seven decisions its edits carried into `docs/design/RECONCILIATION.md`
  as override rows, so the snapshot can disagree with the implementation again.
- Decisions re-homed: header pills are production navigation, loading progress is
  a hairline with pinwheel status, heatmap H1 and mode card copy are owner
  changes, release filter label is WP-4 scoping, runs expire after two idle
  hours, form help affordance is no `?` control.
- Defect being prevented: three `.docsync.toml` declarations (44px touch target,
  Adobe Fonts kit, heatmap window) had snapshot sites with no `expect` value,
  allowing docsync to satisfy drift by editing the import instead of the code.
  Added explicit `expect` values to close that deadlock. Sites without capturing
  groups remain unmatched and satisfied by agreement; sites with groups now
  demand the expected value.
- Validation: snapshot test created and passes at the restored digest. `pytest
  -q` -- **871 passed**. `pre-commit run --all-files` -- all 12 hooks pass.
  `doc_state_sync.py --check` -- exit 0. No drift in binary files or structure.
- Deviations: none.

### 2026-09-01 - Owner-review remediation consolidated (side-task)

- Scope: consolidate the owner-review remediation in one plan and correct the
  active Batch 21 records that described unshipped index behavior as present.
- Evidence: `BATCH21_DEFINITION.md` and `docs/design/RECONCILIATION.md`
  claimed that the form filled its well, while current `static/css/index.css`
  retains its `23.75rem` cap. `FINDINGS.md` also marked the broader refinement
  resolved even though the owner-confirmed remaining work has not shipped.
- Disposition: the **Owner Review Remediation Implementation Plan** (2026-09-01)
  is the sole comprehensive future-work specification. It treats the source
  scale formula as unproven because owner Firefox evidence does not show the
  intended rendered scaling, and adds the required 1080p test of the 1440p
  header-density candidate. Active records refer to it without claiming its
  changes are implemented. Dated history remains unchanged.
- Follow-up: the final annotation review confirmed that the intended shared
  scaling is not implemented. The plan and active Batch 21 records now state
  that source code is not acceptance evidence; Firefox rendering must prove
  the composition before the work can be marked complete. No product code,
  staging, commit, or push occurred in this planning pass.

### 2026-08-29 - Unmatched zero state corrected (side-task)

- Scope: remove the contradiction where the unmatched page says albums were
  excluded and immediately reports a total of zero.
- Implementation: use the existing `total_count` condition in the template.
  A zero count now states that there are no unmatched albums to review while
  retaining the search settings and results navigation. The populated report,
  reason tables, and filter facts are unchanged.
- TDD: the route-backed zero-payload render test failed against the prior
  claim and now protects the empty copy, omitted populated-report copy, and
  results navigation. The populated report test remains green.
- Validation: focused route and template checks -- **91 passed**. Full
  `pytest -q` -- **871 passed**, 5 existing warnings. `doc_state_sync.py
  --check` and all pre-commit hooks pass.
- Forward guidance: this is not a data-pipeline fix. Keep `/unmatched` and
  `/api/unmatched` semantics unchanged for WP-7's separate backend work.

### 2026-08-29 - Wide index form and shell rhythm corrected (side-task)

- Scope: correct the wide form that grows beyond its shared composition and
  give the desktop navigation breathable, uniform control spacing.
- Implementation: wide layouts no longer remove the form's 23.75rem cap, so
  the existing 1.075-to-2.15 composition scale controls the card and its
  fields together. The well's inline padding is symmetric and the form stays
  centred. Desktop shell height is 4.75rem; page links and the theme control
  are 48px tall with one 0.75rem sibling gap. Mobile retains its compact
  shell rules.
- TDD and validation: the rendered frontend check failed before the CSS
  change: 1920px, 2560px, and 3840px form widths were 1099px, 1499px, and
  2299px instead of the shared-scale caps, and their gutters were unequal.
  It now reports 22 checks passed in 31 runs across desktop, mobile, and wide
  touch. Full `pytest -q` -- **870 passed**, 5 existing warnings.
- Forward guidance: keep the header outside the wide composition scale; it
  must remain an independently readable global control strip.

### 2026-08-28 - Cached Heatmap loading handoff clarified (side-task)

- Scope: repair the owner-reported cached Heatmap result snap, redundant
  loading signals, and misleading normal-state return control without
  changing worker cancellation semantics.
- Implementation: the backend still reports real progress, but phase text now
  says `Reading your Last.fm history...` while `Pages fetched` owns its only
  visible fraction. Both fills use `scaleX` rather than layout-width
  animation. The Heatmap renders its complete DOM, then lets the loader paint
  for two frames before one 300ms root opacity handoff. Reduced motion skips
  that handoff. Both workflows now say `Cancel and return home`; each only
  navigates home.
- TDD and validation: the new service and browser-gate assertions failed
  before the implementation because both workflows still emitted counted
  phase text, used a layout fill, lacked the named return control, and the
  cached result had no root-handoff state. Focused tests -- **17 passed**.
  Full `pytest -q` -- **870 passed**, 5 existing warnings. The frontend gate
  reports 22 checks passed in 31 runs, including the warm-cache handoff.
- Forward guidance: deploy this with the existing private-profile and index
  motion fixes. It deliberately does not claim or implement worker
  cancellation.

### 2026-08-28 - Index page-entry fade restored (side-task)

- Scope: restore the Home destination entrance lost when the Tailwind index
  stopped loading the legacy page stylesheet.
- Implementation: the complete index composition now fades from opacity zero
  over 1.2 seconds after a 0.2-second delay. It does not move or resize, and
  the existing light/dark mode transition is unchanged. Reduced-motion readers
  receive the visible final state without an animation.
- Validation: full `pytest -q` -- **870 passed**, 5 existing warnings. The
  frontend gate reports 22 checks passed in 31 runs, including the
  computed-style check in standard and reduced-motion modes.

### 2026-08-28 - Private Last.fm profiles are blocked before jobs start (side-task)

- Scope: stop index submissions for profiles that hide their recent listening,
  rather than reporting a misleading empty result after a job starts.
- Implementation: preflight `user.getrecenttracks` with a one-item request;
  Last.fm's 403/error-17 verdict blocks both index modes in the browser and
  both loading routes on the server. Public accounts with an empty history
  remain eligible.
- Validation: focused service and route tests -- **92 passed**, 5 existing
  warnings. Full `pytest -q` -- **870 passed**, 5 existing warnings. The
  frontend gate reports 21 checks passed in 30 runs, including both forms
  against the same private-profile response.

### 2026-08-28 - Index entrance-motion regression filed (side-task)

- Scope: compared the deployed index, the locally served primary checkout,
  the active PR #220 worktree, source history, computed browser styles, and
  production asset identities after the owner reported a large regression.
- Finding: filed F-B21-26 as P0. The Tailwind index opts out of `global.css`,
  which owned the old card and logo entrance fades, and no Tailwind-owned
  page-entry replacement exists. PR #220's mode-copy cross-fade is separate
  and does not restore the page-entry behaviour.
- Deployment and font disposition: production serves the `1bf888f`
  `origin/main` assets from PR #218, not PR #220. The local server also ran
  the stale primary checkout. Deployed Adobe faces loaded successfully; the
  visible type-scale difference remains F-B21-24 and is corrected in the
  undeployed PR #220 calibration.
- Implementation: documentation only. No application code or deployment was
  changed; F-B21-26 owns the required motion restoration and browser check.

### 2026-08-28 - PR #220 timer-probe review remediated (side-task)

- Scope: audited the frontend pipeline probe after browser evidence showed its
  timeout patch was installed as an unevaluated arrow expression.
- Reproduction: invoking the same body as an IIFE sets a page marker. A page
  init script survives later navigations, so installing it on the shared
  profile page can also alter unrelated checks.
- Implementation: the pipeline state-machine check now runs on a disposable
  page, installs and verifies the invoked timeout patch there, and closes the
  page on both success and failure. The profile page remains clean for the
  later scale checks.
- Validation: focused frontend-gate unit tests -- **15 passed**. Full
  `pytest -q` -- **865 passed**, 3 warnings. The frontend gate reports
  20 checks passed in 29 runs across desktop, mobile, and wide touch.
  All pre-commit hooks and `doc_state_sync.py --check` pass.

### 2026-08-28 - Index width, scale, and small-text refinement (side-task)

- Scope: applied the owner-review amendment to the migrated Home composition
  without changing its content order, navigation, mode transition, or mobile
  layout.
- Implementation: desktop widths from 1200px use a `3fr 4fr` split, a 28rem
  form cap, and the existing shared `1.075` scale. A compact-height desktop
  rule reduces only the form column's outer padding. The small-label floor is
  12px, phrase-length capability text uses 0.04em tracking, and the light
  muted token is `#6c6676` in both framework paths.
- Contract: component sizes remain equal at 1920x1080, 2560x1440, and
  3840x2160; larger canvases change placement, not scale. The imported design
  snapshot remains untouched, with the amendment recorded in
  `docs/design/RECONCILIATION.md` and F-B21-24 resolved.
- Validation: focused template and build tests -- 100 passed. Full `pytest -q`
  -- **864 passed**, 3 warnings. The frontend gate reports 20 checks passed in
  29 runs across desktop, mobile, and wide touch. `doc_state_sync.py --check`
  passes.

### 2026-08-28 - Wide index gap tightened (side-task)

- Scope: corrected the oversized visual void between the scaled hero lockup
  and the form that remained after the proportional large-display repair.
- Implementation: the 1200px-and-wider composition now uses `3fr 5fr` rather
  than `3fr 4fr`. The shared viewport scale and the form's fixed physical
  gutters remain unchanged, so the lockup retains its 1080p, 1440p, and 4K
  scale while the form moves closer to it.
- Reproduction and validation: the browser gate first rejected the prior 4:3
  application-to-hero split, then passed with the new 5:3 split. A rendered
  1920x1080 inspection confirms the reduced visual gap without compressing
  the wordmark or removing header navigation.

### 2026-08-28 - Proportional large-display scale restored (side-task)

- Scope: corrected the index scale regression reported from 2560x1440 local
  browser captures. The previous rule retained a fixed `1.075` zoom and a
  28rem form cap at every desktop size, leaving a large inactive canvas on
  high-resolution displays.
- Implementation: at 1200px and wider, the hero and form calculate one shared
  CSS-viewport factor: `1.075 × max(1, min(viewportWidth / 1920,
  viewportHeight / 1080))`, capped at `2.15`. The form now fills the right
  well to its existing 2.75rem / 3.5rem physical gutters. Navigation remains
  shell-sized; compact-height and mobile rules are unchanged.
- Reproduction and validation: the large-display browser check initially
  failed at 1440p and 4K because both compositions remained at `1.075` and
  the form missed its fixed gutters. It now passes at 1920x1080, 2560x1440,
  and 3840x2160. Browser inspection at 2560x1440 confirmed the `1.433` scale,
  an 803px wordmark, the fixed form gutters, and all four navigation links.
  The full suite reports **865 passed**, 3 warnings, and the frontend gate
  reports 20 checks passed in 29 runs across desktop, mobile, and wide touch.

### 2026-08-27 - PR #220 Graphify findings audited and gate cleanup hardened (side-task)

- Scope: checked every open Codex and Graphify review thread on PR #220
  against current source, callers, tests, Git history, and browser behaviour.
- Review disposition: the five Codex findings are already addressed. The
  thirteen inline Graphify coupling notices are duplicated metrics rather
  than defects. Graphify's missing `logging` import, advisory-exit, result
  redirect, and unmatched-route claims are disproved or deliberate contracts.
  Two cleanup findings were valid: failed frontend-gate setup could leak its
  temporary jobs and routes, and a failed blocked-storage probe could leave
  its browser context open. Concurrent in-process gate contexts could also
  overwrite the shared fixture state.
- Implementation: `serve_app` now serialises its temporary global fixture,
  restores prior state, and cleans jobs, routes, sockets, and threads even
  when application or server setup fails. The blocked-storage context now
  enters its cleanup boundary before either probe setup call.
- Validation: focused frontend-gate unit tests -- 14 passed. `pytest -q` --
  **864 passed**, 3 warnings. The frontend gate reports 20 checks passed in
  29 runs across desktop, mobile, and wide touch.

### 2026-08-27 - Fresh heatmap starts separated from saved destinations (side-task)

- Scope: made Home's Heatmap selector start a new run while the header Heatmap
  and Results destinations continue to reopen the latest valid browser-session
  jobs. Added dedicated empty pages for those two destinations.
- Plan vs implementation: `/?mode=heatmap` now opens a fresh form without
  deleting the saved heatmap pointer. A successful start promotes the URL to
  `/heatmap`. Clean `/heatmap` and `/results` visits resume valid jobs or render
  `heatmap_empty.html` and `results_empty.html`; job access now runs expiry
  cleanup so the documented two-hour idle limit is enforced.
- UX and responsive behavior: the empty pages use one centered, shadow-free
  message group with a route-specific action. The Heatmap state retains a
  short rocket-scale gradient. Mobile actions keep the 44px touch minimum;
  large displays keep the established CSS-pixel scale instead of inflating
  controls independently.
- Deviations: the index selector does not clear the cached job. It ignores the
  pointer for the fresh form, because deletion would also remove the latest
  result that the header destination promises to restore. During live review,
  two stale Flask processes were found on port 5000; both were stopped and one
  current no-reload server was started from this worktree.
- Validation: the TDD red run reported 6 failed and 5 passed. `pytest -q` --
  **862 passed**, 3 warnings. The frontend gate reports 20 checks
  passed in 29 runs across desktop, mobile, and wide touch. Impeccable Detect
  reported no regex findings but was degraded because its optional HTML parser
  modules are unavailable; browser-computed checks provide the stronger UI
  evidence for this change.

### 2026-08-27 - Index mode-copy transition made interruptible (side-task)

- Scope: refined only the index hero copy swap between Top albums and Heatmap.
  The wordmark, shared capability line, form layout, routes, and pipeline
  behaviour are unchanged.
- Implementation: replaced the fixed-delay class swap with cancellable Web
  Animations. The current copy exits in 110 ms, the selected copy enters in
  180 ms, and a new click cancels stale motion before it can win. Reduced-motion
  users and browsers without Web Animations receive an immediate swap.
- Visual evidence: the live browser held the wordmark at `(56, 124)` through
  both modes. A rapid album-heatmap-album sequence settled on the album URL,
  selected tab, copy, opacity, and visibility together.
- Validation: `pytest -q` -- **840 passed**, 3 warnings. Frontend gate --
  19 checks passed in 27 runs across desktop, mobile, and wide touch. All
  pre-commit hooks passed, including compiled-CSS drift and worktree alignment;
  `doc_state_sync.py --check` passed with only the expected active-root warning.

### 2026-08-26 - Canonical page navigation and routes added (side-task)

- Scope: implemented the owner-requested navigation prerequisite before the
  WP-4 loading rebuild. The shared header now offers Home, Results, Heatmap,
  and Unmatched in Input Mono Narrow, plus the segmented Light/Dark control.
  Loading stays transient and has no navigation pill.
- Plan vs implementation: added canonical `GET /loading`, `/results`,
  `/heatmap`, and `/unmatched` routes. New album jobs redirect to the loading
  URL and the loading script opens the results URL at completion. The old
  completion and unmatched POST routes remain compatibility shims during the
  strangler. Unmatched JSON moved to `GET /api/unmatched` so the page owns
  `/unmatched`.
- Deviations: direct Results and Unmatched visits without a job now render a
  friendly pre-search state with a Home action. Heatmap already falls back to
  its form. The owner renamed the prototype's Index pill to Home and removed
  Loading from the destination set.
- Validation: `pytest -q` **833 passed**, 3 warnings. The frontend gate
  reports 17 checks passed in 25 runs across desktop, mobile, and wide touch.
  JavaScript syntax checks and `doc_state_sync.py --check` pass.
- Forward guidance: WP-4 still owns the unified loading-page rebuild and the
  two pipeline state-machine checks in `BATCH21_DEFINITION.md`. Keep the
  canonical route and compatibility shims until the strangler retires them.

### 2026-08-26 - PR #220 review applied, and the theme fallback proved (side-task)

- Scope: remediated the three Codex comments on PR #220. All three were
  verified against the code before any fix; all three were valid.
- **The missing log entry** is the entry below this one, covering `9330ac8`,
  `ebb542b` and `6f8ff98`.
- **The `FINDINGS.md` header** attributed F-B21-21 and F-B21-22 to both WP-3
  and the owner review while omitting F-B21-23 and F-B21-24. Corrected in
  `12cfe25`.
- **`check_mark_follows_theme` was weak in two ways**, and both are closed. A
  part whose selector stopped matching read as null and was skipped, so
  re-cutting the asset would have retired the check silently. And the test
  was only that light differs from dark, so a wrapper wired to the wrong but
  theme-varying token passed. It now compares each mark against the resolved
  `--shell-ink` and `--shell-accent` for that theme, read through a probe
  element so the browser normalises `#1a1820` and `rgb(26, 24, 32)` to the
  same string. Mutation-checked: pointing the letterforms at
  `var(--shell-accent)` -- a wrong value that does vary by theme, which the
  old check accepted -- fails four times with the token named.
- **The uncommitted `base.html` theme fallback is real, and is now proved.**
  It was written on 2026-08-26 at 00:08 and left uncommitted when that
  session hit its spend limit mid-verification. Its own mutation check had
  passed on both the new and the reverted code, so it proved nothing: the
  harness never made storage actually throw. Rerun with `localStorage`
  genuinely throwing, the shipped version renders `light` on a dark system
  when site data is blocked, and the fix corrects it. A sixteenth gate check,
  `check_theme_survives_blocked_storage`, holds it; reverting the fix fails
  it by name. The check opens its own browser context, because blocked
  storage is installed as an init script and cannot be removed from the
  shared page afterwards.
- This does **not** close F-B21-22. A stored `'false'` still outranks the
  system preference forever; that needs the third state and an owner ruling.
- **A fourth comment arrived on the sweep after `3526edd`, and it was
  right.** The `worktree-alignment` hook shipped gating, documented as
  erroring only on WT002, WT007 and WT014. Eleven of the fifteen codes are
  errors: WT001, WT002, WT003, WT004, WT005, WT006, WT007, WT008, WT012,
  WT014, and WT009 inside a linked worktree. WT003 fires for any branch the
  active batch does not name and WT004 for the identical-tree divergence a
  rebase merge always leaves, so the gating version would have refused every
  commit on a feature branch and every commit after a merge until the branch
  was realigned. The claim came from grepping two of the guard's six modules
  and generalising -- the incomplete sweep the Anti-Pattern Registry names,
  committed inside a finding about mechanisms that hold in one place only.
- **The owner ruled the hook advisory on 2026-08-26.** The guard gained
  `--advisory`, which prints every diagnostic and always exits 0, and the
  hook uses it. The problem being solved was that the guard's output was
  invisible unless somebody ran it, not that commits needed a new gate. A
  test asserts `--advisory` exits 0 on an ERROR while the same run without
  the flag still exits 1; removing the short-circuit fails it.
- **F-B21-18 is scheduled**, by owner ruling the same day: the JavaScript
  unit-test seam becomes a work package of its own, sequenced before WP-5 and
  not folded into WP-4, scoped to the pure-function half on the existing
  Chromium. WP-5 and WP-7 are the remaining JavaScript-heavy pages, so a seam
  before WP-5 still guards work this batch does. The number it takes needs
  settling against DOC007 and the absorbed WP-6 before its first commit.
- **DOC012 is new, and it exists because this entry nearly lied.** The count
  authority reads `**823 passed**` and nothing else: written without the
  asterisks, the entry records nothing, an older entry stays authoritative,
  and `--check` exits 0 with every dashboard holding the previous number.
  That happened here -- the count was written unbolded, the figure did not
  move, and the gate stayed green. The owner ruled that bolding the line was
  the wrong fix, because the next agent will make the same mistake. DOC012
  now fails an execution-log entry that claims a pass result with no bold
  count anywhere in it. It is scoped per entry, not per line, so a subset
  claim beside a bold figure -- WP-1's "(35 passed)" for the toolchain
  module -- stays prose and history is not rewritten. Mutation-checked in
  both directions: neutering the check fails the first test, dropping the
  entry-scoping fails the second.
- Validation: `pytest -q` -- **826 passed**, all 12 hooks, docsync exit 0,
  frontend gate 17 checks in 25 runs. The suite grew by four: the
  `--advisory` exit contract and three DOC012 cases.

### 2026-08-26 - Deployed-merge review: wordmark theme fix and doc trim (side-task)

- Scope: the owner reviewed the deployed PR #218 merge and found two defects.
  This entry covers `9330ac8`, `ebb542b` and `6f8ff98`, which shipped without
  one. A PR #220 reviewer raised the omission; the entry is written here
  rather than by amending pushed commits.
- `9330ac8` trimmed the documents a session bootstraps from. SESSION_CONTEXT
  lost 35 lines: eight "Batch N complete" rows that restated the Section 2
  index one batch at a time, and a per-file test table that duplicated forty
  counts from the suite while only the total was gated. It had drifted three
  times during Batch 21, each drift a false fact in a bootstrap document, so
  the command that derives it replaced the table. Two `AGENTS.md` rules were
  restated as intent. AGENT_NOTES gained the wordmark typeface, Oblong
  Regular by WAPType, which took the owner about three hours to recover
  because the mark was converted to paths and no font reference survives in
  the asset. F-B21-21 and F-B21-22 were filed.
- `ebb542b` fixed F-B21-21. The index hero mark shipped with pure black
  letterforms on the `#0e0c12` dark page. Both wrappers include the same
  asset; it pins its own stroke and gives the letterforms no fill rule, so
  any wrapper `shell.css` does not name renders fixed-purple bars and
  user-agent black text, and only `.site-header__mark` was named. The gate
  gained its first check that reads a colour off an inline SVG.
- `6f8ff98` filed F-B21-23 and F-B21-24. F-B21-23 records that the assets
  diverge from the design contract, which specifies `currentColor`
  letterforms and `var(--bars-color)` bars; that divergence is the real
  cause of F-B21-21, which was fixed at the symptom. F-B21-24 rules that the
  index not growing past about 1400px is the contract working as written.
- Validation at the time: 822 tests, all hooks, docsync exit 0, and the
  Quality Gate green on `6f8ff98`.

### 2026-08-26 - Session-time enforcement added after the worktree retirement (side-task)

- Scope: the batch-21 worktree was retired on 2026-08-26. Reviewing how that
  went found that every gate in this repository runs at commit time and
  nothing runs at session time. Filed as F-B21-25 and partly closed here.
- What happened, from the branch reflog. `wip/batch21-doc-trim` was created
  from `origin/main` at 2026-08-25 21:57, took three commits, and was renamed
  to `wip/batch-21` at 2026-08-26 00:07. The rename only succeeds when the
  retained branch of that name is already deleted, and the push four seconds
  later replaced the remote. None of the three commits carried a Section 4
  entry, because the session treated the branch as a quick documentation trim
  rather than batch work, and nothing told it otherwise. A PR #220 reviewer
  raised it; the entry two above this one now covers that work.
- What changed:
  - **`worktree-alignment` is now a pre-commit hook.** The guard already
    exited 1 on an ERROR diagnostic and 0 otherwise, so it was built to gate
    and was simply never wired to one. Only WT002, WT007 and WT014 are
    errors; WT004 and WT010 are not, so the identical-tree state a rebase
    merge always leaves, and a dirty tree, both still commit. It runs verbose
    so branch lineage is visible on a passing run.
  - **The stray `venv/` is deleted.** It carried black 25.1.0 against the
    24.3.0 this repository pins, and two entries in the local permission
    allowlist had been authorising it. Both entries are removed. It came from
    the Batch 12/13 convention, which spelled the directory without the dot;
    the archived definitions still show that spelling, so reading one can
    recreate it. `resolve_venv()` looks only for `.venv` and cannot see a
    second one.
  - **A `SessionStart` hook** injects branch, working-tree state, guard codes
    and the machine-managed status block into every new Claude Code session,
    with the reminder that a tracked-file commit needs its Section 4 entry in
    the same commit. It is local to this machine and does not help Codex or
    Copilot, which is recorded in the finding.
  - **The `FINDINGS.md` header is corrected.** It attributed F-B21-21 and
    F-B21-22 to both WP-3 and the owner review, and omitted F-B21-23 and
    F-B21-24. Raised on PR #220.
- Not done, and deliberately: a manifest of untracked-but-essential files
  (`skills-lock.json` is still missing), and two structural defects in
  `AGENTS.md` -- the fast-paths that authorise skipping bootstrap sit above
  the numbered list, and the file carries origin narrative that serves the
  editor rather than the reader. Both edit `AGENTS.md` and need an owner
  ruling first.
- **The first push went red, and the hook was the cause.** `12cfe25` failed
  the Quality Gate with `ERROR WT007 origin/main -- comparison base ref is
  missing`. `actions/checkout` makes a shallow single-branch clone, so
  `origin/main` does not exist on a runner and the guard fails closed on a
  base ref that is legitimately absent. `WARNING WT009` also fired for the
  `.venv` CI does not use. The step now sets `SKIP: worktree-alignment`,
  with the reason at the step: the guard measures developer worktree
  lineage, and a runner has no worktree topology to protect. Fetching the
  base ref would have silenced WT007 and left the check measuring nothing.
- The lesson is the one this entry is about, applied to its own author. A
  check was added without asking where it runs, and its assumptions held on
  one machine only. Local verification passed and proved nothing about CI.
- Validation: 822 tests, all 12 hooks locally, docsync `--check` exit 0,
  guard exit 0, and the Quality Gate green after the skip landed.

### 2026-08-25 - PR #218 review rounds and post-completion pass applied (side-task)

- Scope: remediated every Codex comment on PR #218 while WP-3 sat open and
  unmerged. Thirty-seven comments across PR #216 and #218 in total -- seven
  on #216 and thirty on #218. Thirty-six were valid; all were actioned.
  All twelve rounds were answered and all thirty threads were resolved. On
  2026-08-25 the owner authorized batched review replies and resolution of
  threads whose fixes are present at the pushed head; GitHub owns the
  resulting live state.
  One was declined on its premise -- it said the closed thresholds disclosure
  gave its controls zero-sized boxes, and deleting their sizing turns the gate
  red, so they were being measured -- and its remedy was applied anyway.
- What changed, beyond the individual fixes:
  - **Touch sizing and the 1rem input size moved off the width query** onto
    `@media (any-pointer: coarse), (max-width: 859.98px)`. A tablet in
    landscape is wide and touched. The two rules were corrected one round
    apart, which is the lesson: a rule moved for a newly understood condition
    is not done until every rule sharing that condition moves with it.
  - **The frontend gate gained a third device profile**, a wide touch screen,
    and `run_checks` now takes a page factory because touch emulation belongs
    to a browser context.
  - **The export header is measured rather than fixed**, after the file it
    produced was opened and looked at.
  - **A `/validate_user` reply is discarded when the field has moved on.**
    The submit guard added earlier in the series had turned a cosmetic stale
    message into a block that no blur clears.
  - **Round six found two blind spots in DOC009 and DOC011 themselves**, one
    day old. DOC009 accepted a file after its first match, so `index.css`
    could state the breakpoint once and contradict it in either of its other
    two media queries; it reads every occurrence now, and a site may declare
    `expect` so two notations of one fact -- `859.98px` and `860` -- can
    differ without the check going blind. DOC011 searched line by line and
    could never match a phrase that wrapped, which in Markdown that wraps at
    about 76 columns is the likely shape rather than an edge case; it matches
    the joined document now and maps back to the starting line, with the
    history and strikethrough exemptions applied after that mapping.
  - **Round seven found the same two blind spots one level further out.**
    DOC010 also searched line by line, and `PLAYBOOK.md` already carried a
    citation of `AGENTS.md` "UI and Accessibility Rules" across two lines, so
    that heading could have moved with the gate green. DOC009 shared the
    shape, quietly: a file that states a value more than once satisfied the
    check on the unwrapped copy while a drifted wrapped one went unread. Both
    read the joined document now. `_joined_text` strips each line before
    joining, without which a correct wrapped citation resolves to a heading
    name with five spaces in the middle of it.
  - **The anchor scan is every Markdown tree**, not the trees someone
    remembered. It had missed `docs/SWE_AUDIT_CHARTER.md`, which cites
    `AGENTS.md` and was never read. Three exemptions are declared with it:
    `docs/history` and `docs/logarchive`, because a dated record is accurate
    at write time and renaming one heading would otherwise turn 70 archived
    files red with no fix but editing history; and `CLAUDE.md`, because it is
    gitignored, so scanning it made the gate's answer depend on which machine
    ran it.
  - **Widening the scan found a checker defect before it found a document
    defect.** The design contract labels some sections as list items, and the
    bold-label pattern insisted the asterisks start the line, so the WP-3
    plan's citation of "Responsive" resolved nowhere. Fixing that first was
    the difference between the widening finding a defect and the widening
    crying wolf.
  - **A year warning that is still true survives a username edit.**
    `clearRegistrationState()` had reset the minimum and the hint and left the
    message naming the previous account's join year. Clearing the message
    outright is the obvious fix and is wrong: "Year cannot be in the future"
    is about the year, not the account. The handler re-derives instead, and a
    ninth gate check holds the half a reader would not notice was broken.
  - **A failing validator no longer locks the form it serves.**
    `/validate_user` answers an outage with 503 and `valid: false`, which both
    blur handlers read as a verdict about the username. Trying again was the
    one thing the message asked for that could not work. Reported against the
    heatmap form, which refuses at its own submit guard; the index form has
    the same defect through native validation, because only the heatmap form
    carries `novalidate`. One comment, two forms.
  - **A declaration with nothing to scan is refused.** `scan` was optional, so
    an anchor carrying only `target` and `pattern` validated, visited no
    documents, and DOC010 reported clean while checking no citations at all.
    That is the same silent end state as the misspelled key closed the round
    before, reached without a typo -- the earlier fix stopped at the way the
    fault had been reported rather than at the condition behind it.
  - **A nonempty scan must resolve to work.** Round eleven found named files
    and globs that resolved nowhere were silently skipped. The sibling sweep
    also found a third route to the same clean no-op: `allow_files` could
    exempt every resolved path. DOC010 and DOC011 now fail loudly for all
    three, rather than validating only the list container.
  - **Declared regexes carry semantic contracts.** A syntactically valid
    anchor with no heading capture crashed at its first match. Anchor patterns
    now require exactly the heading plus optional item captures, validate a
    participating heading and numeric item, and value patterns reject extra,
    missing, optional-empty and empty captures before those assumptions can
    turn into a crash or a false agreement.
  - **Top-level declaration collections validate before iteration.** Round
    twelve found that `value = 1`, `anchor = 1` and `retired = 1` reached their
    collectors as integers and raised `TypeError` before the per-declaration
    schema could report malformed input. All three outer collections now fail
    once at the wiring boundary. The raw collector calls predated round eleven,
    so this was backlog in the new module rather than a regression from that
    round; the earlier class sweep still stopped one boundary too low.
  - **The heatmap window declaration covers the class, not the remembered
    instances.** Its runtime, product, owner, architecture and canonical-design
    copies are now sites. `HEATMAP_WINDOW_DAYS` remains the source and the
    inclusive fetch subtracts one from it. `static/js/loading.js` is
    deliberately excluded because its number is the leap-aware length of a
    calendar year for a different average. The same census widened the older
    breakpoint, touch-target and Adobe-kit declarations across their runtime,
    owner and canonical-design copies, and removed redundant literals where
    the adjacent code already owns the value.
  - **A declared container is checked for what it holds.** `scan = [1]` is a
    list, so the shallow check passed it and the integer reached the glob
    matcher as a `TypeError`. Round eight was the third round on this module
    and each one sat one level further in than the last: wrapped text, then
    missing and misspelled keys, then the contents of a container.
  - **A malformed declarations file is refused, not ignored.** Reading a
    required key straight out of the mapping raised a bare `KeyError`, so an
    anchor with no `target` ended the run in a traceback and exit 1. Looking
    for the siblings found four more, and all four are worse because they are
    silent: a misspelled key, a list written as a bare string, a misspelled
    table, and a misspelled option. Each leaves a check quietly not checking
    while the gate stays green. Every declaration is now held to a declared
    schema, so an unknown key is an error rather than a shrug.
  - **A bad declarations file is reported rather than thrown.** Malformed
    TOML, or a declaration holding an invalid regex, raised
    `DeclarationError` straight through both CLI paths, which catch
    `SyncError` and exit 2. The run ended in a traceback and exit 1 instead.
    It is a `SyncError` now, keeping the distinct class its docstring asks
    for so the reader is not sent to edit the wrong file.
  - **The validators identify requests, not only values.** The first sweep
    found that the album validator discarded stale replies but not stale
    failures. Copying the heatmap sibling's value guard closed A-then-B and
    still failed A-then-B-then-A, where the oldest and newest requests carry
    identical text. Both state machines now use request generations, and the
    browser check holds that ABA sequence. A second check holds the current
    failure path: a network outage replaces an older red invalid verdict with
    an outage message while leaving server-side submission available.
  - **The independent visual sweep closed six contract slips.** Keyboard focus
    opens both ambiguous-field hints without breaking tap; valid usernames use
    the canonical good colour; selected controls and hints raise their shadows
    in dark mode; the lone 6px radius moved onto the 8px ladder step; and both
    text-holding header heights scale in rem. Three browser checks exercise the
    rendered states at both sides of the breakpoint.
- **The final gate found its own procedure contradiction.** The Tailwind drift
  hook compares the generated working file with the index, so a correct
  source-and-output edit cannot pass before staging even though `AGENTS.md`
  requires pre-commit before staging. `F-B21-20` records the owner decision;
  this review validates an exact-name staged candidate and restores the index.
- Two findings came out of reading the comments as a set rather than one at a
  time: `F-B21-17`, that six of nineteen were one fact written twice, and
  `F-B21-18`, that browser JavaScript has no unit runner. `F-B21-17` was
  then built and closed the same day; see the DOC009 entry below.
- Deviations: none against a plan, because there was none -- this is review
  remediation. The canonical mobile-strip, layout-independent export and
  day-detail gaps and the gate-order contradiction were not improvised during
  review; `F-B21-18`, `F-B21-19` and `F-B21-20` record them for an owner ruling
  and a bounded implementation.
- Post-completion review: the root-font mutation was reproduced at `20px`
  instead of the original `17px`, and the theme-persistence check also left
  its saved choice behind. Both now restore state in `finally`. Two earlier
  Graphify findings were also real: declaration paths could traverse outside
  the repository, while joined-document matching had lost the original
  per-line `^`/`$` behavior in DOC009, DOC010 and DOC011. Root confinement and
  a shared dual-representation matcher close those classes. Four claims were
  rejected: F-B21-4's do-not-close instruction does not govern F-B21-5; the
  validator state is reached without aborting; claimed profiles are the only
  planned runs; and `run_checks` deliberately takes a page factory because
  touch capability belongs to the browser context. No Page-object caller
  remains, and Graphify's reproducer passed an integer instead of either valid
  interface. Its duplicated coupling comments supplied counts but no defect;
  the cohesive functions remain in place rather than undergoing a risky late
  refactor.
- The final Graphify pass found one more real boundary defect among four false
  alarms. `_Files` resolved `nested/../PLAYBOOK.md` to the right filesystem
  path but used the unnormalized spelling to look up live documents and its
  cache, so a declaration could grade stale disk instead of the document this
  run had just rendered. Both lookups now use the confined repository-relative
  key. The import, page-factory, generated tab and pruned-utility claims were
  disproved by execution, current callers and source census.
- Validation: `pytest -q` -- **822 passed**, 3 warnings. The declaration seam
  is **71 passed** and `pytest --collect-only` confirms 822 tests across 40
  files. The frontend gate reports **15 checks in 23 runs** across desktop,
  mobile and wide touch. All 11 pre-commit hooks pass.
  `doc_state_sync.py --check` exits 0 with only the expected active-batch
  root-definition warning. Every behavioral fix was red before it was written
  and re-measured after.
- Review completion: `77bb001` closed the original twelve Codex rounds. Both
  Quality Gate runs passed, all thirty threads were resolved, and the Codex
  connector recorded a thumbs-up at 2026-08-25 19:17:45 UTC. `bd49cdb` then
  recorded the documentation-only handoff. The final follow-ups own the five
  developer-gate hardening classes above. PR #218 is the completed WP-3
  integration branch; WP-4 starts from its merged result. The owner selected
  a rebase merge so the individual commit history remains visible without
  adding a merge commit.
- Forward guidance: a quiet round was not treated as completion. The recorded
  thumbs-up was. Rounds four and five found defects that earlier fixes in the
  series had introduced. Round six then found two holes in one-day-old code,
  so review yield tracked new surface area rather than elapsed rounds. Expect
  a fresh review of whatever `F-B21-18` builds. Both round-six holes were of a
  kind a check's own tests cannot find because the tests were written from the
  same understanding as the code. Keep an independent reviewer on tooling as
  well as features.

### 2026-08-25 - DOC009 to DOC011: facts written down more than once (side-task)

- Scope: closed the buildable half of `F-B21-17`. Three declared integrity
  checks in a new `scripts/docsync/declarations.py`, driven by a new
  `.docsync.toml` at the repository root. No new dependency; the declarations
  are TOML read with `tomllib` from the standard library.
- Why: six of the nineteen Codex comments across PR #216 and PR #218 were not
  logic defects. They were one fact recorded in several places where the
  copies had drifted. The clinching case was a cross-reference that named its
  target by heading, exactly as `F-STYLE-1` asks, and broke in the same commit
  that moved the heading. A written rule cannot catch that; only something
  that resolves the reference can.
- Plan vs implementation: DOC009 compares a value across its sites, DOC010
  resolves a citation shape against the document it names, DOC011 keeps a
  retired claim out of anything that still prescribes. Four behaviours were
  added after the first run reported false positives on real documents, and
  each is a property of how this repository actually writes: bold lead-ins
  count as citable places, a heading cited without its trailing parenthetical
  resolves, a label's trailing sentence is not part of its name, and
  struck-through text is already marked as not current.
- What the first run found, before any test was written:
  - **`static/css/shell.css` used `max-width: 860px`** where every other
    stylesheet uses `859.98px`. Both the mobile and the desktop rules
    therefore applied at exactly 860px. Fixed.
  - **`AGENTS.md` described the integrity codes as DOC001-DOC006**, four
    checks after that stopped being true. Fixed, and the line now says when
    it went stale, because that is the same class the new checks exist for.
  - Two stale citations, one of them inside the finding that proposed the
    check.
- Deviations: the declarations file is at the repository root as
  `.docsync.toml` rather than under `docs/`. It is configuration, it sits
  beside `.pre-commit-config.yaml` and `.gitattributes`, and keeping the
  repository-specific half out of `scripts/docsync/` is what lets that
  package be lifted into another repository unchanged.
- Validation: `pytest -q` -- **771 passed**, 3 warnings, 22 of them new. All
  11 pre-commit hooks pass with an identical `git write-tree` either side.
  Each of the three checks was proved against the real defect it was built
  for, by restoring that defect and watching the check name it. Five
  mutations of the module each killed exactly one test and no others.
  `doc_state_sync.py --check` exits 0. The frontend gate is unaffected and
  still reports 8 checks in 13 runs.
- Forward guidance: add a declaration when a fact starts living in two
  places, not after it drifts. `F-B21-18` is the other half and is not
  started -- browser JavaScript with no unit runner, to be reached through
  a guarded seam onto the Chromium the frontend gate already pays for, not
  through npm.

### 2026-08-24 - F-B21-13 docsync bootstrap gate remediated (side-task)

- Scope: closed `F-B21-13` with DOC007 and DOC008 on
  `wip/f-b21-13-docsync-gate`, branched from `origin/main` at `658bdb2`;
  WP-3 remains on `wip/batch-21`.
- DOC007 now has one next-WP calculation. The managed SESSION_CONTEXT
  renderer owns `_next_wp_number()`, the integrity check calls that helper,
  and the CLI supplies the active definition's finite plan. Absorbed,
  dropped and merged WP headings are skipped; a fully completed plan
  terminates with no next package instead of looping forever, while any stale
  numeric next-WP claim left at close-out is blocking. The definition Status
  line, PLAYBOOK Section 3's actual Next action bullet, and SESSION_CONTEXT
  Section 1's sole active Batch status row are checked for the same active
  batch and next WP. Historical claims outside the bullet and earlier claims
  superseded inside it cannot steal the comparison.
- DOC008 applies `latest_test_count_authority()` to the FINDINGS.md header
  with findings-specific remediation. Authority includes live entries, the
  side-task archive and per-batch logs; a same-date tie between batch logs is
  resolved by numeric batch chronology rather than filename insertion order.
- Review remediation also repaired two misleading DOC007 fixtures so their
  asserted WP ranges really sit inside the current-batch markers, and made
  DOC008's error invariant say the header count "must agree" instead of
  claiming that a detected mismatch already agrees. Every new edge case was
  observed failing before its minimal fix.
- Deviations: the owner authorized expanding the original PR file set on
  2026-08-24 after the audit proved DOC007 and the renderer computed different
  next-WP values. The expansion is limited to the renderer/sync/CLI data path
  and its directly related docsync tests; no unrelated refactor was taken.
- Validation: `pytest -q` -- **717 passed**, 3 warnings (was 682; 35 new
  tests across the docsync integrity, renderer, logic, CLI and count suites).
  The focused docsync suite is **219 passed**.
- Forward guidance: WP-3 should still update the definition Status line as
  an explicit task. The gate proves agreement; it does not replace writing
  the canonical status correctly.

### 2026-08-23 - PR #216 review round three applied (side-task)

- Scope: two review comments on `e9bac27`, both real rendering defects in
  WP-2's own shell commit. Both were verified in a browser before any edit.
- **The header wordmark ignored `prefers-reduced-motion`.** The lockup
  carried five SMIL `<animate>` elements with `repeatCount="indefinite"`.
  No CSS can pause SMIL, so the media query in `shell.css` never reached
  them. WP-2 made the exposure much worse: the mark moved from per-page
  hero content that scrolls away into a fixed header that is on every page
  and never leaves the viewport. `docs/design/README.md` already prescribed
  the remedy and says the SMIL must be stripped and the bars animated from
  CSS. Done, with the keyframes taken from `docs/design/tokens/base.css`.
- **A wrong assumption was caught by measuring.** The origin looked like it
  needed a 7-unit correction, because this lockup's viewBox starts at y=7
  where the full mark starts at y=0. It does not: `view-box` resolves
  `transform-origin` in the SVG user coordinate system, not from the
  viewBox corner. At `scaleY(3)` the proposed 56.5px slid each bar bottom
  8.4px and the canonical 63.5px held it to 0.2px. Under the shipped 1.10
  scale the gap is under half a pixel, so eyeballing would have missed it.
- **The back-to-top control lost its layout.** `base.html` used to wrap the
  theme toggle and `page_footer_extra` together in `.page-footer-bar`. WP-2
  moved the toggle into the header and removed the wrapper with it, but
  `results.html` still fills that block and `#back-to-top` has no CSS of its
  own anywhere. Centring, gap, padding and entrance all came from the
  wrapper, so the control shipped bare and left-aligned. Restored in
  `shell.css` rather than `global.css`, which only reaches unmigrated pages.
- Both guards were proven able to fail. Putting one `<animate>` back fails
  five tests, reflowing the wrapper onto three lines fails four, and
  dropping the reduced-motion `opacity: 1` fails one.
- Deviations: the frontend gate gained no reduced-motion check. Its checks
  take a page rather than a browser, so a second context needs a signature
  change, and that is a refactor rather than a review fix. The template
  tests cover the markup and the CSS; the computed behaviour was verified
  by hand this round.
- Findings: `F-B21-5` updated rather than closed. The header instance is
  resolved; the pinwheel and the index hero wordmark still carry SMIL and
  belong to WP-3.
- Validation: `pytest -q` -- **682 passed**, 3 warnings. All 11 pre-commit
  hooks pass. The frontend gate reports `5 checks passed`.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: strip the SMIL from the remaining two assets the same
  way. Do not reach for `svg.pauseAnimations()` -- the CSS route is what the
  design contract asks for and it needs no JavaScript.

### 2026-08-23 - PR #216 review round two applied (side-task)

- Scope: two review comments on `4105aef`, both documentation. Both were
  verified against the files and both were valid.
- **The batch definition still said WP-2 was next.** PLAYBOOK Section 3 and
  `SESSION_CONTEXT.md` Section 1 both said WP-3. `AGENTS.md` makes those
  three agreeing the condition for bootstrap to complete, so the next agent
  would have stopped on the disagreement. `git log -S` puts the line's last
  edit in `7c00754`, the WP-1 commit. WP-1's plan listed updating it as a
  task and WP-2's did not.
- **The findings header still published 666 tests.** The round-one commit
  moved PLAYBOOK and SESSION_CONTEXT to 671 and left that copy behind. It is
  the instance-not-class anti-pattern `AGENTS.md` names, committed inside the
  commit that was fixing stale documentation.
- Every other `666` in a tracked document was checked rather than assumed.
  The remaining three are dated log entries that were accurate when written,
  so they stay.
- **`F-B21-13` filed for the class.** Neither line is read by any gate.
  `doc_state_sync.py` derives the next work package from PLAYBOOK and never
  reads the batch definition, and the test-count enforcement in
  `scripts/docsync/integrity.py` covers SESSION_CONTEXT only. The definition
  status line has now gone stale twice -- PR #170 corrected it once for
  WP-1 -- which is the point at which `AGENTS.md` prefers a mechanical check
  over another written rule.
- Deviations: the gate was not extended in this round. It is a change to the
  integrity checks every work package depends on, and scope discipline puts
  that in a finding rather than in an open UI PR.
- Validation: `pytest -q` -- **671 passed**, 3 warnings. All 11 pre-commit
  hooks pass. `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: WP-3 should carry updating the definition status line as
  an explicit task, the way WP-1 did, until `F-B21-13` closes.

### 2026-08-23 - PR #216 review round one applied (side-task)

- Scope: three review comments Codex left on `45fbbe8`. All three were
  verified against the code and all three were valid. None was declined.
- **Tailwind was pruning tokens the handwritten CSS reads.** Tailwind v4
  emits a theme variable only when a generated utility uses it.
  `static/css/error.css` reads `--font-figure`, `--font-weight-bold`,
  `--spacing-8`, `--radius-sm` and `--radius-lg` directly, no utility used
  them, and none reached `static/css/tailwind.css`. An undefined `var()`
  with no fallback voids the whole declaration, so the error page shipped
  with no card rounding and no page padding, and its status number took
  neither the bold weight nor the Gotham face. Nothing failed and nothing
  logged. `@theme static` fixes it and adds 16 declarations to the compiled
  file. A browser now reports 14px card rounding and 32px 16px page
  padding.
- **No page set `font-family` on `body`.** Neither `global.css` nor
  `shell.css` carried one, so the four unmigrated pages downloaded the
  Adobe kit and then rendered in the Bootstrap system stack. The batch
  definition lists the body font as a WP-2 deliverable, so this was a
  missed one rather than a new idea. The declaration went into `shell.css`
  behind a new `--shell-font-sans` token, because an unmigrated page never
  loads the compiled stylesheet and `var(--font-sans)` resolves to nothing
  there.
- **`SESSION_CONTEXT.md` sections 3 and 4 were stale.** They said 9 css and
  7 js files, still listed a deleted `error.js`, and omitted `shell.css`,
  `frontend_gate.py` and the lockup SVG. Real counts are 10 and 6.
- Two gaps closed while in the same files. `tests/test_template_shell.py`
  gains a test that renders each page, reads back the stylesheets it loads,
  and asserts every `var()` without a fallback resolves in one of them.
  Nothing checked that invariant before. The gate gains a fifth check for
  the body font, reading computed style rather than stylesheet text,
  because the failure is a cascade one and only a browser can settle it.
- Deviations: the dependency graph also gained `dev/tailwind_build.py`,
  which WP-1 added and never recorded. It was a one-line omission in the
  block being corrected, so leaving it was worse than fixing it.
- Both fixes were proven able to fail. Reverting `@theme static` fails two
  tests, and removing the body declaration fails the gate on `/` and names
  the system stack it fell back to.
- Validation: `pytest -q` -- **671 passed**, 3 warnings. All 11 pre-commit
  hooks pass. The frontend gate reports `5 checks passed`.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: the compiled stylesheet is 1,650 lines now, so every
  line citation into it is stale again. Cite the block, not the number.

### 2026-08-23 - Node 20 CI deprecation filed as F-B21-12 (side-task)

- Scope: recorded a warning the Quality Gate has started printing. No
  workflow change, no dependency change, no code change.
- Plan vs implementation: `F-B21-12` filed. Four pinned actions in
  `.github/workflows/test.yml` -- `actions/cache`, `actions/checkout`,
  `actions/setup-python` and `actions/upload-artifact` -- target Node 20,
  which GitHub deprecated. Runs are forced onto Node 24 and pass, so nothing
  is broken today.
- Why file it: all four sit in one file and fail together on the day the
  forced fallback is withdrawn. That break would land on whichever work
  package is open, would look unrelated to its diff, and would block every
  PR at once. The finding says to bump them in their own commit and to read
  each action's releases rather than guess the major that carries the new
  runtime.
- Deviations: none.
- Validation: `pytest -q` -- **666 passed**. All 11 pre-commit hooks pass.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: not urgent, but the deadline belongs to GitHub rather
  than to this repository. Do it as a standalone commit, not folded into a
  UI work package, because every other work package depends on that gate.

### 2026-08-22 - Tailwind citations renamed after the rescope (side-task)

- Scope: 13 line citations in `FINDINGS.md` and
  `docs/design/RECONCILIATION.md`. No code changed.
- Codex caught this on PR #173. It is correct.
- The `source(none)` comment moved `tailwind.src.css` down five lines. The
  rescope cut `tailwind.css` from 2,289 lines to 1,576. Every citation into
  either file broke at once. `:root:not([data-theme])` moved from 2042
  to 1335.
- The citations now name the block or the declaration: the two
  `@plugin "daisyui-theme.mjs"` blocks, `--spacing-*`, `--radius-*`,
  `--font-sans`, `--font-mono`, `--font-weight-medium`,
  `@custom-variant dark`, `prefersdark: true`. Named anchors do not drift.
- Checked the citations Codex did not flag. `heatmap.js:14-22`,
  `heatmap.js:25-26`, `theme.js:17`, `base.html:26` and `index.css:158` all
  still resolve. Those files did not change.
- This is `F-STYLE-1` happening again. The rule already exists for
  `AGENTS.md`. It applies to every file. Cite a name, not a number.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**.

### 2026-08-22 - Open findings mirrored to GitHub issues (side-task)

- Scope: created issues #174-#215. Rephrased two rules in `AGENTS.md`. Filed
  `F-B21-9`. No code changed.
- Why: Codex raised `F-B21-7` on PR #173 although the PR body listed it.
  Reviewers do not read `FINDINGS.md`. Issues are cheaper to search.
- 42 open findings are now mirrored: 28 P1, 10 P2, 3 Info, 1 Feature. Seven
  resolved findings were skipped. Labels are `finding` plus the severity.
- Each issue body says `FINDINGS.md` is the source of truth and that the
  issue is a read-only mirror. Nothing writes back to the file.
- `AGENTS.md` changes are rephrases, not additions. Bootstrap item 7 already
  said "read on demand"; it now names the three reasons to open the file and
  says a recorded defect is known and owned. The Markdown log-entry bullet
  now also asks for plain English. No new rule was added.
- `F-B21-9` records the gap. The mirror is manual and will drift. The owner
  accepted that on 2026-08-22 and asked for it to be written down rather
  than built now. A sync script is code and needs its own work package.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**.

### 2026-08-22 - PR #173 review answered, two import defects fixed (side-task)

- Scope: moved `docs/design/styles.css`. Fixed one claim in
  `docs/design/RECONCILIATION.md`. No code changed.
- Codex raised four threads. All four are correct. Claude disputed none.
- `styles.css` went into `docs/design/tokens/`. It belongs one level up.
  The file imports `tokens/fonts.css`. From inside `tokens/` that path does
  not exist. So the entry point loaded no tokens.
- The source project keeps `styles.css` at its root. `DesignSync list_files`
  confirms this. `git mv` fixes the path. The content does not change.
- `RECONCILIATION.md` said every colour in the README tables matches the
  theme. That is wrong. Three tokens match: `--surface-page`, `--text-strong`
  and `--accent`. Four are absent. Dark `--surface-sunken` is `#181520`, not
  `#1a1622`. The status colours are still Bootstrap's.
- A per-token table now replaces the claim.
- This is the second false claim of this shape in that file. `F-B21-8`
  records the first. Both came from a spot check.
- The other two threads repeat `F-B21-7`. Codex found them on its own. They
  stay with WP-2. WP-2 owns that code next.
- Checked this pass: only `RECONCILIATION.md` changed under `docs/design/`.
  The imported files match `fa56cd6`. Claude's Markdown has no non-ASCII.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**. It inherits `F-B21-7` and `F-B21-8`.

### 2026-08-22 - Tailwind source scope corrected after PR #173 went red (side-task)

- Scope: `static/css/tailwind.src.css` (one directive plus a comment), the
  regenerated `static/css/tailwind.css`, `FINDINGS.md` (`F-B21-8`), and the
  false claim in `docs/design/RECONCILIATION.md` section 2. Owner chose the
  fix and the recording from two options each.
- Trigger: PR #173's Quality Gate failed on "Verify committed Tailwind CSS".
  Not a flake. The rebuild added 30 lines the committed file did not have.
- Cause: `@source` **adds** to Tailwind v4's automatic detection instead of
  replacing it, so the whole repository was scanned, not just `templates/`
  and `static/js/`. The extractor turns bare words in Markdown into class
  candidates, so prose compiled into utilities -- `.contents`, `.isolate`,
  `.flex`, `.border`, `.relative`, `.sticky`, `.truncate`, `.italic`.
- The design import did not create this; it exposed it. The committed
  baseline was already contaminated. Scoping the scan removed **713 of 2,289
  lines, 31% of the stylesheet**.
- Fix: `@import "tailwindcss" source(none)`. Rejected alternatives, both
  offered to the owner: regenerate as-is, which would couple the design
  documentation to production CSS permanently; and `@source not "../../docs"`,
  which fixes only `docs/` and leaves `tests/`, `scripts/` and the root
  Markdown feeding the scanner.
- Verified rather than assumed: both theme blocks survive (`--color-base-100`
  is `#faf8f3` light and `#0e0c12` dark, and `data-theme` still appears three
  times), and a second consecutive build reproduces the first byte for byte.
- Deviations: two `@source not` directives are now unreachable and were left
  in place deliberately, as protection if `source(none)` is ever removed.
  Recorded in `F-B21-8`.
- **Process failure worth naming.** Last session's check,
  `git diff --exit-code -- static/css/tailwind.css`, was reported as proof
  that `docs/design/` was outside Tailwind's scope. It proves only that the
  file was not hand-edited. The build has to actually run. `F-B21-8` records
  that nothing local runs it, which is what WP-2's `tailwind-css-drift` hook
  closes.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
  `doc_state_sync.py --check` exits 0. `pre-commit run --all-files` passes.
  Quality Gate re-run on PR #173.
- Forward guidance: **WP-2 is next** and should treat `F-B21-7` and `F-B21-8`
  as its own, since the drift hook it adds runs both code paths.

### 2026-08-22 - Two WP-1 review items filed as F-B21-6 and F-B21-7 (side-task)

- Scope: `FINDINGS.md` only -- two new findings plus the stale status header.
  No code changed. Filed before opening the Batch 21 PR so the branch is
  self-describing rather than leaving a reviewer to rediscover them.
- Both items came out of the five-agent WP-1 review on 2026-08-20 and were
  carried in local notes, unfiled, ever since. Each was re-verified against
  the code before filing; neither was taken on the review's word.
- `F-B21-6`: `routes.py:135,302,436` use naive `datetime.now()`. Line 436
  gates the requested year against host-local time while
  `orchestrator.py:70-71` builds the fetch window in UTC, so gate and window
  disagree by the host offset near New Year. They agreed before F-SWE-2,
  which fixed the window and left the gate. Production runs UTC, so this is
  a developer-host defect.
- `F-B21-7`: two defects in the WP-1 toolchain. The one test naming the
  integrity property patches both `required_artifacts` and `ensure_artifact`,
  so no integrity code runs. **Verified by mutation:** deleting
  `bin_dir=bin_dir` from `tailwind_build.py:293` leaves the full suite at
  633 passed. The review had claimed only the 35 toolchain tests stay green;
  the real blast is the whole suite. Separately,
  `http.client.IncompleteRead` subclasses `HTTPException`, not `OSError`, so
  it escapes both handlers as a raw traceback -- confirmed from the MRO --
  and a cleanly truncated download surfaces as `SHA-256 mismatch`, which
  reads as tampering rather than a network fault.
- Deviations: none. The mutation was reverted with `git checkout --` and the
  working tree confirmed clean before anything was staged.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; the only
  Python touched was the mutation, which was reverted.
  `doc_state_sync.py --check` exits 0. `pre-commit run --all-files` passes.
- Forward guidance: **WP-2 is next.** It should absorb `F-B21-7`, because the
  `tailwind-css-drift` hook it adds runs the same code path. `F-B21-6` is
  independent of the UI batch and needs no WP of its own.

### 2026-08-21 - SESSION_CONTEXT batch status row resynced (side-task)

- Scope: `.claude/SESSION_CONTEXT.md` Section 1 only -- the Batch 21 status
  row and the "Last updated" date. No code, no gate, no Section 3 change.
- Why: the row still read "the owner-approved root-hygiene side task is next,
  then WP-2". That side task closed on 2026-08-20, and two further side tasks
  landed on 2026-08-21. PLAYBOOK Section 3 was correct throughout; only the
  snapshot was stale.
- Three earlier commits caused the drift. Each updated PLAYBOOK and left this
  row alone. `AGENTS.md` "What to update after a WP or side-task commit"
  requires SESSION_CONTEXT Section 1 to move when the batch status changes.
- Not a gate failure, and nothing would have caught it. `doc_state_sync.py`
  manages the STATUS block in Section 2, which was correct the whole time.
  Section 1 prose is hand-maintained and unchecked.
- The row now also names `docs/design/README.md` as the canonical design spec
  and `docs/design/RECONCILIATION.md` as the override list, so a bootstrapping
  agent finds the design tree from the state snapshot.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; no Python
  touched. `doc_state_sync.py --check` exits 0. `pre-commit run --all-files`
  passes.
- Forward guidance: **WP-2 is next**, unchanged. Section 1's batch row is the
  first thing a bootstrapping agent reads for state. Update it in the same
  commit as the PLAYBOOK entry, never afterwards.

### 2026-08-21 - Size rule restated as intent in AGENTS.md (side-task)

- Scope: rewrote Proposal and Design Rules item 3 in `AGENTS.md`. One rule, no
  other rule touched, no code touched. Owner-authorised.
- Plan vs implementation: the rule read "No new file should be larger than the
  largest peer in its directory", which is the proxy metric rather than the
  intent, and it is the example `CLAUDE.md` had been carrying as the model for
  the planned trim. It now states the intent: the rule is against god files,
  not line counts; a file large because its job is large is fine; the peer
  comparison is the check you run when you notice scope creep, not a threshold
  to clear. Owner's framing, given 2026-08-21.
- This also resolved a contradiction inside the same list. Item 5 already said
  "SoC/DRY is the constraint on file content, not line count", which item 3
  denied. They now agree.
- Checked before writing, not after: `F-WORKTREE-4` and `F-MAS-3` are the only
  other places that restate the cap, and both already carry the correct
  reading -- "the rule exists to prevent unmaintainable monoliths" and "size
  was never the defect". Neither was edited; item 3 now cites both.
- Deviations: one, and it matters. The rewrite grew the item from three lines
  to eight, so every `AGENTS.md` line citation past it moved by five. This is
  the same drift that made `F-STYLE-1` cite 254, 262 and 550 when the real
  lines were 255, 263 and 551. One live citation was affected --
  `docs/design/RECONCILIATION.md` pointed at the ASCII rule by line. It now
  names the section instead, and `CLAUDE.md` records the rule: cite
  `AGENTS.md` by section or rule name, never by line.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; no Python
  touched. `doc_state_sync.py --check` exits 0. `pre-commit run --all-files`
  passes.
- Forward guidance: WP-2 is still next. When the wider `AGENTS.md` trim
  happens, do it this way -- one rule at a time, intent replacing the proxy
  metric, and re-grep line citations afterwards because they will move.

### 2026-08-21 - Front-end design handoff imported to docs/design (side-task)

- Scope: imported the owner's Claude Design project
  (`7d95e96a-613b-4017-9dd7-8b74d2db9535`) into `docs/design/`, recorded where
  it diverges from the batch contract, and filed two findings. No runtime code
  changed. WP-2 keeps its own reserved commit.
- Plan vs implementation: the source project holds 207 files; 61 are imported
  verbatim through the design MCP -- the canonical `README.md`, 10 token files,
  24 components as `.prompt.md` plus `.d.ts`, and two subordinate references.
  The import is a curated subset and says so; everything else stays reachable
  through the MCP, and `RECONCILIATION.md` section 2 tables what was left
  behind and why. Claude added a 62nd file,
  `RECONCILIATION.md`, because a verbatim snapshot states the Adobe Typekit
  stack and the `.dark` marker as fact and the owner has overridden both;
  without an override list a later agent reading only the specification would
  implement the wrong thing. `docs/AGENT_DOC_MAP.md` gains a row so the tree is
  discoverable.
- Owner decisions, all made this session: (1) the type stack stays self-hosted,
  so `BATCH21_DEFINITION.md:155-158` decision 4 stands and kit `rwy8ghw` is not
  adopted; (2) `docs/design/README.md` is canonical and is the default over
  both files in `reference/`, but it does not automatically retire an audit
  finding; (3) curated text-only import; (4) import only, one commit.
- Deviations: none against the approved plan, but two of its assumptions were
  corrected by evidence found while importing. The plan treated the mobile
  input size as a live conflict; it is not -- the canonical bundle's own
  `components/forms/Input.prompt.md` mandates 16px or larger on mobile, which
  matches the shipped override at `static/css/index.css:158`. `F-B21-5` records
  it as settled rather than open. The plan also assumed the component layer
  followed the Adobe stack; it does not -- `Button.d.ts` and `Input.d.ts` name
  JetBrains Mono, so the self-hosted mapping agrees with most of the bundle.
- Verified against code, not accepted from the documents: the seven `rocket_r`
  stops in `static/js/heatmap.js:14-22` match the specification exactly; every
  hex value in both colour tables matches `static/css/tailwind.src.css:69-137`;
  the three accessibility defects in `F-B21-5` were each confirmed at the line
  cited. The unmatched-grouping bug the design review names was already in the
  batch contract at `BATCH21_DEFINITION.md:25-27` and is not filed again.
- `docs/` is excluded from every pre-commit hook by `.pre-commit-config.yaml:2`
  and sits outside Tailwind's `@source` scope, so the import cannot rewrite the
  specification's Unicode or move `static/css/tailwind.css`. Both were checked.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; this commit
  touches no Python.
- Forward guidance: WP-2 is still next and its scope is unchanged. Before
  starting it, read `docs/design/RECONCILIATION.md` section 5 -- the theme
  marker resolves to `data-theme="dark"` on `<html>` at `templates/base.html:2`,
  which satisfies daisyUI, the WP-2 contract and the specification at once.
  WP-3 must measure label and hint widths at 9-11px: there is no narrow
  JetBrains Mono, so the clipping regression the specification warns about is
  live here rather than avoided. `F-B21-4` must not be closed by ruling on all
  four screens at once; each is decided at the WP that builds it.

### 2026-08-21 - Dependency advisories filed as F-B21-3 (side-task)

- Scope: filed one finding from the first Quality Gate run that exercised the
  Tailwind steps. No runtime code and no dependency changed.
- Plan vs implementation: pushing `bc9ba80` ran the gate for the first time
  since WP-1 landed. It passed, and "Verify committed Tailwind CSS" succeeded
  on Linux, so the committed digest reproduces in CI and the WP-1 platform
  detection works there. The same run's `pip-audit` step reported 115
  advisories across 12 packages and exited 1 without failing the gate, which
  is its documented `continue-on-error` disposition. Investigation found six
  packages in `requirements.txt` that nothing imports, including a
  `pypdf`/`pdf2image`/`pillow` cluster. The owner asked whether those served
  the JPEG export; they do not. That export is client-side `html2canvas` in
  `static/js/results.js:178-266`. All six unimported packages entered in the
  initial `0ea2313` commit rather than with a feature. The owner has poppler
  installed locally, so `pdf2image` can run on the development machine, but
  not in production: the `Dockerfile` is a bare `python:3.13-slim` with no
  system-package installs.
- Deviations: none. No dependency was upgraded or removed. Dependency changes
  are code and belong in a code batch, not a docs commit.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Quality Gate run
  32444711411 passed in 1m12s.
- Forward guidance: WP-2 is next. `F-B21-3` records a suggested shape --
  split runtime from developer requirements, drop unimported packages, then
  upgrade the outbound HTTP libraries -- but the owner has not ruled on it.

### 2026-08-20 - F-B21-2 deferred to the locked WP-2 remedy (side-task)

- Scope: corrected one finding that prescribed a fix competing with an
  owner-locked decision. No runtime code changed.
- Plan vs implementation: `F-B21-2` was filed from the WP-1 review without
  reading `BATCH21_DEFINITION.md:186-204`, which already prescribes WP-2's
  remedies. It told a reader to layer Bootstrap; the locked decision instead
  moves the Bootstrap link into a per-page block so each template loads
  exactly one framework stylesheet, removing the collision rather than
  re-ordering it. The finding now defers to the definition and says so. Its
  `data-theme` seam likewise points at the locked `theme.js` dual-write. The
  defect descriptions are kept, because they record why those decisions
  matter; only the competing prescription is gone.
- Deviations: none. The batch definition was not edited. A finding must not
  outrank the batch contract, so the finding moved.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next and closes `F-B21-2`. Check a finding against
  the active batch definition before filing a remedy in it.

### 2026-08-20 - README roadmap reconciled with FINDINGS (side-task)

- Scope: removed one stale roadmap item that contradicted an open finding, and
  retitled the finding it pointed at. No runtime code changed.
- Plan vs implementation: the README roadmap still asked a reader to
  consolidate Bootstrap onto one CDN provider. `F-B20-3` already records that
  remedy as dead, because Batch 21 removes Bootstrap at WP-8 and resolves the
  split by elimination. Two live documents disagreed, and the README is the one
  a newcomer reads first. The roadmap line now names the real disposition.
  `F-B20-3`'s heading described the dead remedy rather than the defect; it now
  reads "Bootstrap loads from two CDN providers". Every citation of it is by
  F-ID, so no reference breaks.
- Deviations: none. Three other roadmap items were checked and left alone.
  The integration test (`F-LOAD-2`) and the `ENTRY_BATCH_RE` tightening
  (`F-DOCSYNC-1`) have not been done, so their unchecked boxes are correct.
  `tests/test_routes.py` reaches the three endpoints only under mocks, and no
  test covers the whole chain. `parser.py:37` is unchanged.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next. Note `F-DOCSYNC-1` may overstate the problem
  -- the current regex already requires the parenthesised `(Batch N WP-N)`
  form, so a failing test should justify the change before anyone makes it.

### 2026-08-20 - Root hygiene: config verdict recorded, banners withdrawn (side-task)

- Scope: recorded the root config-file verdict in the document that owns
  deploys, and corrected one false self-description. No runtime code changed.
- Plan vs implementation: the owner rejected the audience-banner scheme in the
  local root-hygiene plan. Its two-label vocabulary restated what the
  `AGENTS.md` Document Roles table and `docs/AGENT_DOC_MAP.md` already own,
  and its rule that no file claims both audiences is false for files that are
  both. `DEVELOPMENT.md` was the worked example: it called itself explanatory
  documentation only while owning the Frontend Asset Build commands that other
  documents cite. That sentence is narrowed rather than banner-stamped.
  `DEPLOY.md` gains "Where the config lives"; `fly.toml` gains a pointer
  comment above its empty `[build]`; the README tree names the co-location
  instead of leaving `Dockerfile` uncommented.
- Deviations: the banner steps, the `AGENTS.md` audience rule, and the README
  audience split are **withdrawn, not deferred**. Verification also corrected
  an earlier claim that the banner would strand agents:
  `BATCH21_DEFINITION.md:448-450` already binds WP-2 through WP-7 to run
  `tailwind_build.py`, so no agent depended on `DEVELOPMENT.md` for the
  obligation. Only the fuller procedure, including watch mode and the worktree
  caveat, lives there.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next. Nothing from this side task blocks it.

### 2026-08-20 - Batch 21 WP-1 test-count authority addendum (side-task)

- Scope: records the post-WP-1 measured suite inventory for docsync's
  same-day source ordering. No runtime implementation changed.
- Plan vs implementation: the new current-batch WP-1 entry remains the owner
  of toolchain evidence. This live addendum supplies its later full-suite
  result because same-date side-task entries take precedence over
  current-batch entries in docsync's authority ordering.
- Deviations: none.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: owner review of the WP-1 commit remains first; the
  root-hygiene side task follows, then WP-2.

### 2026-08-20 - Agent document map added; HANDOFF_PROMPT trimmed (side-task)

- Scope: the owner asked for an instructional that lets an agent other than
  Claude navigate the documentation set -- including the audit and SWE
  documents -- and understand why each document exists. Added
  `docs/AGENT_DOC_MAP.md` and registered it in the `AGENTS.md` Document Roles
  table. Documentation only; no runtime code changed.
- Plan vs implementation: as planned. The map routes rather than summarises.
  It names the owner of each fact and links to it, so it adds no copy that a
  later edit can contradict (`AGENTS.md` Anti-duplication rule). Sections:
  the one-owner rule and why it exists, where to start, the document groups,
  the human-facing documents, how to read an audit, how to read a finding,
  seven navigation traps, the pre-change gates, and the tie-break order when
  two documents disagree. It sits under `docs/` rather than the repository
  root, because a twelfth root Markdown file would worsen the problem the map
  exists to solve, and it is marked optional and outside the bootstrap set so
  it does not inflate the cold-start read. 264 lines, under the 370-line
  largest peer in `docs/`.
- Audit guidance is the part with no prior owner: the charter to report to
  findings to log-entry lifecycle, why a retired charter is kept, why a dated
  report is never edited in place, and that a report is a measurement of one
  day rather than current truth. The SWE report's own "Owner review" section
  is cited as the worked example of an appended correction.
- Owner request mid-task, and the reason it changed shape: delete
  `HANDOFF_PROMPT.md`. That is not a documentation-only delete. The file is
  pinned into the commit gate at `scripts/docsync/cli.py:26` and
  `scripts/docsync/integrity.py:51`. `cli.py:88` loads every
  `LIVE_DOCUMENT_PATHS` entry through `_read_lines`, which raises `SyncError`
  on a missing file and maps to exit 2, and the `doc-state-sync-check` hook
  runs `--check` with `always_run: true`. Deleting the file alone would fail
  every commit in the repository until `cli.py`, `integrity.py`,
  `tests/conftest.py:149` and four assertions in
  `tests/test_docsync_integrity.py` changed with it. The owner chose to trim
  the file instead of deleting it.
- Trim: `HANDOFF_PROMPT.md` went from 66 to 46 lines. Removed three sections
  that carried no requirement of their own and only named an `AGENTS.md`
  section: validation gates, commit discipline, and anti-patterns. Every
  subject those sections named survives in the new opening paragraph, checked
  against the removed text one item at a time per Anti-Pattern 12. The two
  unique parts are untouched: the post-read verification and the handoff
  checklist. Section numbers were replaced with names, so no later edit can
  leave a stale "Section 4)" citation behind. `DEVELOPMENT.md:74-78` already
  claimed the file held only those two things, so the trim closes an existing
  drift rather than creating one.
- Deviations: two stale claims corrected in the same commit, both left behind
  by the 2026-08-20 audit commits. `BATCH21_DEFINITION.md:3` still read that
  the F-SWE-1 audit "comes next" after PR #170; the audit ran on 2026-08-20.
  The `README.md` documentation tree still described
  `docs/SWE_AUDIT_CHARTER.md` as "Standing audit scope and method"; the
  charter is retired. The same tree gained a row for the new map, because it
  enumerates the contents of `docs/`.
- Validation: `pytest -q` **590 passed** (unchanged; no code touched);
  `pre-commit run --all-files` all hooks passed;
  `python scripts/doc_state_sync.py --check` exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning. Every tracked Markdown file
  was checksummed before and after the pre-commit run and compared, because
  that hook has twice reverted files nobody edited, once into a commit.
- Forward guidance: unchanged. The F-SWE-2 fix is still the next action. It
  is a code commit and it moves the test count off 590.
- **Later same-day test-count addendum:** the F-SWE-2 current-batch entry above
  records the subsequent code change and owns its implementation details. Its
  full-suite result was `pytest -q` -- **591 passed**. The earlier 590 result
  in this entry remains point-in-time evidence; this pointer supplies the
  later same-date count to docsync's live-side-first authority order.

### 2026-08-20 - F-SWE-1 SWE principles audit executed (side-task)

- Scope: executed `docs/SWE_AUDIT_CHARTER.md` against `1994673`, whose
  runtime code is byte-identical to `main` at `bb187ae` -- the five commits
  between them are documentation only. Read-only audit; all 130 cells
  (13 graded modules x 10 principles) filled in one session. Report:
  `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`.
- **Verdict: migration blocked by F-SWE-2**, per charter Section 6 -- a
  net-new correctness defect in `orchestrator.py`, which WP-7 modifies.
  `orchestrator.py:70-71` builds the listening-year window from naive
  datetimes, so the window shifts by the local offset of the host: measured
  at five hours on this machine. It is the same defect F-B19-6 fixed in
  `heatmap.py`; `git show --stat ccb000f` confirms that fix touched heatmap
  and its tests only, and the twin was never revisited. Production is
  unaffected because the Fly.io container runs UTC. Every non-UTC host is
  affected, including local dev, so local checks of album results have been
  running against a shifted window.
- **Owner decisions, same day.** F-SWE-2: fix, do not waive -- it lands as
  its own commit before WP-1 and moves the test count. F-SWE-3: rescoped
  from P1 to P2, and the audit was partly wrong. It filed the
  `No Spotify match` reason as a user-facing mislabelling; that framing does
  not hold, because thousands of Last.fm-scrobbled albums genuinely have no
  Spotify release, so the label is accurate for the ordinary case. What
  survives is narrower and independent of labelling: `spotify.py:67-68`
  marks every non-200, non-429 response terminal, so a 500 ends the attempt
  loop after one try while `SPOTIFY_SEARCH_RETRIES` is 3. The related UI
  need -- the unmatched modal and page should say plainly that an album had
  no Spotify match -- is already WP-7 scope
  (`BATCH21_DEFINITION.md:297-308`), not new work.
- Grades: 74 A, 28 B, 8 C, 2 D, 18 N/A. The weakest principle is Fail Fast,
  holding five of the eight C grades and only two A grades across 13
  modules. The failures share one shape: the code catches a problem and
  discards what the problem was.
- Six net-new findings, F-SWE-2 to F-SWE-7. Every one of the ten C and D
  cells carries a disposition; two map to open F-B20-2 rather than becoming
  new entries. Each finding was verified by running the code, not by reading
  it -- the TTL renewal, the Spotify retry bypass, the unreachable API-key
  check and the heatmap misattribution were each reproduced.
- Test vacuity: measured, not judged. Each of the 81 top-level functions in
  the graded modules was replaced in turn with a raise, in a copy of the
  tree outside the repository, and the 237 runtime tests were run against
  each mutation. Every deletion was caught, so there is no vacuity finding.
- Broad catches: all 17 were read in context and judged, which F-MAS-4 never
  did. Fifteen are justified. The two that are not are both in F-SWE-5, and
  both are catches that report a cause they never established.
- F-B21-1 keeps its recorded P1 disposition. The gate covers net-new
  findings only, so the audit did not re-triage it and it does not block
  WP-1.
- Deviations: F-SWE-1 moved from the P1 section to Resolved this batch, and
  F-SWE-3 from P1 to P2 -- the charter asked for neither move, but leaving
  either where it was would have made the section heading false.
- **Tooling hazard hit twice, worth recording.** `pre-commit run --all-files`
  stashes unstaged changes and restores them afterwards. That cycle reverted
  files nobody had edited: first `docs/architecture/development-cycle.md`
  and `top-albums-sequence.md` back to a pre-PR-#171 state, then `PLAYBOOK.md`
  itself back to a pre-PR-#170 state, dropping this very entry. Every hook
  reported `Passed`. The first was caught at staging because AGENTS.md
  requires staging by name; the second reached commit `a34c57f` and was
  repaired in the follow-up commit. Check `git status` before and against
  after every `--all-files` run, and compare file mtimes against the files
  you actually edited.
- Validation: `pytest -q` -- 590 passed, unchanged, as expected for a
  docs-only change. `pre-commit run --all-files` and
  `doc_state_sync.py --check` both pass, the latter with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: apply the F-SWE-2 fix as its own commit, then WP-1. Root
  hygiene stays deferred until after WP-1.

### 2026-08-19 - Batch 21 preflight: F-SWE-1 charter and WP gates amended (side-task)

- Scope: owner preflight review before WP-1, raised as six criticisms of
  `docs/SWE_AUDIT_CHARTER.md` and an eight-row table of weak WP gates. Two
  verification agents checked every claim against the files before any edit.
  All six charter criticisms held. Two of the batch claims did not.
- Verification of the owner report:
  - Confirmed: the charter named five docsync modules when the directory has
    seven (`integrity.py`, 474 lines, unnamed) and its LOC figure was stale
    for the five it did name; the differential baseline was a closed ID list
    omitting F-B21-1, F-DATA-1, F-WORKTREE-3/4/5, F-DOCSYNC-6/7 and never
    referenced `FINDINGS_ARCHIVE.md`; A/B/C/D was defined nowhere in the
    repository; the matrix was 190-210 cells with explicit permission to cut
    modules; no severity or stop condition existed anywhere, so finishing the
    audit was the same as passing it; and the post-Batch-21 frontend audit
    was permissive ("can"), not required.
  - Corrected: the excluded set is a proper subset of what Batch 21 rewrites,
    not equal to it -- WP-7 modifies `routes.py` and `orchestrator.py`, which
    are in scope, so those grades also expire at WP-7. The charter never
    addressed that; it now does.
  - Refuted: the claimed AGENT_NOTES-versus-definition contradiction over the
    drift hook. `AGENT_NOTES.md` requires the CI-fetch *decision* at WP-1;
    the definition deferred the *hook* to WP-8. Both could hold. The real
    defect was quieter -- no WP-1 criterion required the decision to be
    recorded, so nothing enforced it.
- Root cause neither side had named: the batch validation gate is three
  Python commands, and pre-commit excludes `static/` and `templates/`. A work
  package could rewrite every template and stylesheet with a fully green
  gate, in a batch that is nothing but template and stylesheet rewriting.
- Plan vs implementation:
  - Charter: 13 graded modules enumerated by name (130 cells, `__init__.py`
    excluded by a stated empty-module rule); docsync and `scripts/dev/`
    excluded with reasons rather than left ambiguous; provenance block
    naming branch, SHA and clean state; symbol-based hotspot discovery
    replacing hardcoded line numbers and counts; baseline widened to the
    whole finding corpus plus the archive and every report from 2026-02 on;
    A/B/C/D rubric with the B/C line defined as exception-versus-pattern;
    Boy Scout window fixed at commits since the February audits; a
    resolved-finding branch for C/D cells; a migration-blocking severity
    policy with a one-line verdict required in the report; an instruction to
    retire the charter at close. The budget escape hatch is withdrawn.
  - Batch 21: new `scripts/dev/frontend_gate.py` added as a fourth gate
    command at WP-2 and grown one page per WP, covering stylesheet
    isolation, computed theme tokens in both themes, theme persistence,
    self-hosted font loading, CSV/JPEG export assertions, and headline
    wrapping. The `tailwind-css-drift` hook moved from WP-8 to WP-2, with
    the `always_run` / `pass_filenames` requirement that AGENT_NOTES gap 2
    had already identified and the definition had not carried. Targeted
    criteria added to WP-3 (keyboard and touch reachability for the CSS-only
    hints, label associations, validation parity), WP-4 (both state machines
    including retryable and non-retryable failures), WP-7 (split into a
    backend contract commit and a UI commit), and WP-8 (required frontend
    and accessibility audit, deterministic Bootstrap-removal grep, recorded
    lint disposition). Browser floor documented; `.dark-mode` retirement
    given an owner; criterion 9 reconciled with the per-WP docsync check.
  - FINDINGS.md: F-STYLE-1 (prose legibility, explicitly never a gate) and
    F-STYLE-2 (docstring convention, the black/flake8 line-length
    disagreement, and the unwritten Ruff plan) added. F-SWE-1 corrected --
    it claimed the charter scoped "Python only until Batch 21 ships", a
    commitment the charter never made.
  - AGENTS.md: the F-ID source-tag list named five tags while nine are in
    use. `SWE`, `WORKTREE`, `DATA` and `STYLE` added, and the list is now
    declared complete so the next coined tag gets documented.
- Deviations: the drift hook landed at WP-2 rather than the WP-1 the owner
  proposed. WP-1 changes no template, so nothing consumes the compiled CSS
  until WP-2; WP-2 is the first point where drift can ship.
- Independent review of the amended charter, same day, and the fixes it drove:
  - The migration gate did not say whether it covered existing findings. Read
    the wide way, F-B21-1 blocks WP-1 today -- a resource-release defect in
    `orchestrator.py`, which WP-7 modifies. The gate is now scoped to net-new
    findings in terms, F-B21-1 is named as the case that forces the
    distinction, and an audit that thinks an existing finding should block
    must recommend rather than act.
  - The A/B/C/D rubric graded by frequency ("one place is B, several is C")
    while its own table graded by cost. One leak can be C; five contained
    exceptions can stay B. Rewritten to grade cost, not count. The
    "when torn, over-raise" instruction is deleted -- it contradicted
    Section 4's rule that the audit's value is not volume.
  - Resolved and no-action findings shared one rule. Split: a recurred
    resolved defect earns a new finding; an unchanged no-action rationale
    does not; materially changed assumptions do, explaining the delta.
  - Provenance permitted grading a dirty tree, which no SHA can reproduce.
    A clean worktree is now required before grading starts.
  - The hotspot command was `awk '...{...}'` -- a placeholder that could not
    run, and a poor Python parser besides. Replaced with a tested `ast`
    script in a new Section 5c, deliberately at the left margin: a heredoc
    terminator indented inside the numbered list fails with
    `IndentationError`, which was verified rather than assumed.
  - Boy Scout used `git log`, which lists commits without showing what they
    left behind. Now `git log -p`, with an instruction to read the patches.
  - "Weakest principle repo-wide" overclaimed: the audit excludes the
    frontend, both script directories, and tests as graded subjects. Scoped
    to the audited runtime modules.
  - Cell arithmetic hardcoded 130 in three places while Section 3 allowed the
    principle count to change. All three now derive from the live count.
  - One review point was stale, not wrong: the claim that WP-8 defines no
    frontend principles audit. It does, in this commit's parent -- the
    reviewer was reading `origin/main`, because the amendment is committed
    locally and deliberately unpushed.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --all-files` --
  all hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  root BATCH warning.
- Forward guidance: execute the amended charter against current `main` and
  publish the migration verdict before WP-1 starts. The verified root-hygiene
  plan (audience banners, README tree, DEPLOY.md) is deferred until after
  WP-1 by owner decision; its line numbers will need re-checking.

### 2026-08-19 - PR #171 round-8 thread fixed: push authorization in the cycle diagram (side-task)

- Scope: one unresolved Codex thread on `docs/architecture/development-cycle.md`,
  raised again by an owner-side human peer on the grounds that this diagram
  purports to govern agents. Checked against the ruleset before editing. Valid.
- Verification: the diagram had a single unconditional edge,
  `Authorize -->|Review-fix commit on an open PR| PR`. `AGENTS.md:234-242`
  grants that standing exception to Claude Code and Codex sessions only and
  says in terms that it does not extend to GitHub Copilot task sessions or
  their subagents, Jules, or any other agent. An agent reading the canonical
  diagram would therefore push a review-fix commit that the ruleset requires
  it to pause on.
- Plan vs implementation: the decision node now carries three edges instead of
  two. WP and batch commits pause in any session; the direct path is labelled
  Claude Code or Codex only; every other agent routes to the same pause. Added
  prose naming `AGENTS.md` as the owner of the rule, and recording the three
  actions that always need explicit instruction whatever the session --
  force-pushes, history rewrites, and anything targeting `main` -- plus the
  Copilot platform-tool requirement at `AGENTS.md:243-244`, neither of which
  the diagram had carried.
- Deviations: none. No code changed.
- Validation: the edited diagram was validated before it was written --
  `valid = true`, type `flowchart`. `pytest -q` -- **590 passed**.
  `doc_state_sync.py --check` -- exit 0 with the expected root BATCH warning.
- Forward guidance: next action unchanged -- the F-SWE-1 audit, then WP-1. A
  preflight amendment to the charter and the Batch 21 WP gates is agreed and
  pending; see the owner decisions recorded with it.

### 2026-08-19 - PR #171 round-7 threads fixed (side-task)

- Scope: the three unresolved Codex threads left on `3d15849` after the
  diagram audit. All three are P2 and all three were checked against the
  source before any edit. All three are correct.
- Verification and fixes:
  - `top-albums-sequence.md` drew `Close connection` unconditionally, but
    `process_albums` closes inside `if conn` (`orchestrator.py:603-604`), so
    the no-connection branch never closes anything. Wrapped in an `opt DB
    connected` block.
  - The same diagram claimed the browser never posts `results_complete` on an
    error payload. `loading.js:209-229` shows only the retryable branch stays
    on the page; a non-retryable error waits three seconds and calls
    `redirectToResults()`, which does post. Split the branch by `retryable`
    and routed the non-retryable case to the processing-error page.
  - `FINDINGS.md` F-B21-1 stated `MAX_ACTIVE_JOBS` is 5 as an absolute.
    `config.py:31` reads it from the environment with 5 as the default, and
    the literal contradicted F-LOAD-1 in the same file. Reworded to name 5 as
    the default and tie the failure count to configured capacity.
- Deviations: none. No code changed; F-B21-1 stays open and unfixed, because
  it is a code change for a code batch.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --files` on both
  edited files -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected root BATCH warning. The edited Mermaid diagram was validated
  through the Mermaid Chart validator: `valid = true`, type `sequence`.
- Forward guidance: the next action is unchanged -- the F-SWE-1 audit, then
  Batch 21 WP-1.

### 2026-08-15 - PR #171 round-6 threads fixed and all five diagrams audited (side-task)

- Scope: the two unresolved Codex threads on `00c0adb`, both on the Top Albums
  sequence. A prior GLM-5.2 session had left uncommitted diagram edits and a
  list of findings, then stopped before it finished. I checked the two threads
  and every edit that session made against the code, then audited all five
  diagrams with three independent verification agents.
- Verification of the two threads: both are correct. `fetch_top_albums_async`
  groups, normalizes, and thresholds the albums before it returns
  (`orchestrator.py:112-116`), so all of that runs before the empty-result
  check at `orchestrator.py:784`. `process_albums` writes to the cache only
  under `if conn and new_metadata_rows` (`orchestrator.py:591`).
- Verification of the prior session: three of its six edits were wrong. It put
  the hit/miss partition inside the DB-connected branch, but the code
  partitions with or without a connection (`orchestrator.py:567`). It drew
  `cleanup_expired_cache()` as a call to `repositories.py`, but that helper
  comes from `utils.py` (`orchestrator.py:40`). It put the total Spotify match
  failure after the store step, but the check runs first
  (`orchestrator.py:824` before `orchestrator.py:842`).
- Plan vs implementation:
  - Top Albums sequence: rewrote the background-task block and the browser
    block. Grouping now sits before every downstream branch. Persistence is
    conditional and records `db_cache_persisted`. The partition sits outside
    the DB branch. New: the connection close and its `finally` ordering
    against `SpotifyUnavailableError`, the `get_job_context` read behind the
    total-match-failure check, the six `results_complete` outcomes, the
    `/progress` 404, and the two unhandled-exception states.
  - Heatmap sequence: added the housekeeping calls, the page-count stats, the
    5% and 80% progress writes, and the unhandled-exception path. Rebuilt the
    render block: the client requests `/heatmap_data` only at 100%, so the 202
    is a narrow race that restarts polling, not a peer alternative.
  - Development cycle: split the merged fast path so the actionability stop
    applies to comment jobs only, added the push-authorization gate that
    `AGENTS.md` requires between commit and PR, and dropped the E2E claim that
    no rule file makes.
  - Runtime diagram and `docs/ARCHITECTURE.md`: named the eight nodes that
    import `config.py`, corrected the arrow-semantics paragraph, and repointed
    the module-graph reference to SESSION_CONTEXT Section 4 alone.
  - Both structural diagrams passed their audit with no change to the graphs.
- Deviations: the prior session said the fix needed a full rewrite of the
  parallel block. It did not. The corrections are local, but they reach more
  branches than that session touched. The audit also found a real code gap and
  it is recorded as F-B21-1 rather than fixed here: `background_task` and
  `heatmap_task` build the event loop outside the `try`, so a failure there
  leaks a job slot. No production code changed in this commit.
- Validation: all four changed diagrams pass Mermaid validation, checked
  against the exact text now in the files. `pytest -q` -- **590 passed**, 3
  known warnings. `pre-commit run --all-files` -- all hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: push, then reply to the two threads and resolve them.
  PR #171 stays open until the owner says otherwise.

### 2026-08-15 - PR #171 round-5 review threads remediated (side-task)

- Scope: three new Codex threads on `37ca4a9` -- one on the development-cycle
  diagram and two on the Top Albums sequence. All three were verified against
  the code before any edit and all three were valid.
- Verification:
  - `AGENTS.md` L29-44 defines the review-comment fast path (fetch the thread
    first, stop if not actionable, else read only the scoped files), but the
    development-cycle diagram routed every review finding through the full
    bootstrap gates. The diagram and the rules it documents were written in
    the same PR and disagreed.
  - `_fetch_and_process()` stores an empty result, marks progress 100%, and
    returns before pre-slicing, cache access, or Spotify enrichment when
    `filtered_albums` is empty. The Top Albums sequence sent every successful
    page fetch into those stages.
  - `process_albums()` catches `_batch_lookup_metadata()` exceptions, records
    `db_cache_warning`, treats every album as a miss, and continues to Spotify
    (possibly persisting via the open connection). The diagram's connected
    path presented lookup as unconditional and its unavailable path said
    persistence was skipped.
- Plan vs implementation: the development-cycle diagram now branches on
  review-finding/comment-job before full bootstrap (fetch thread, stop if not
  actionable, else read scoped files); the Top Albums sequence now stops after
  an empty filtered set and adds a fail-open cache-lookup-error continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the empty-filtered-set and fail-open lookup
  paths.
- Validation: both updated diagrams pass Mermaid validation and open in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this remediation, then resolve the three
  threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 final four review threads remediated (side-task)

- Scope: the four remaining unresolved review threads on `e73540d` -- two
  Codex path-repointing reports and two Codex Top Albums sequence reports.
  All four were verified against the code and the moved files before any
  edit and all four were valid.
- Verification:
  - `docs/superpowers/plans/2026-08-11-pr-170-remediation.md` still cited
    `docs/history/GUARD_HARDENING_2026-08-11.md` and
    `docs/history/REPOSITORY_SYNTHESIS_2026-08-11.md`, both moved to
    `docs/history/reports/` by commit `5865c55`. The links resolved to
    nonexistent files.
  - `docs/history/definitions/BATCH9_DEFINITION.md` pointed twice to
    `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`, and
    `BATCH10_DEFINITION_2026-02-21.md` pointed to the old
    `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md` and
    `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md` paths. All three reports
    now live under `docs/history/reports/`. These are definition-to-report
    references, not exempt point-in-time citations, so they must be repointed.
  - `_fetch_and_process()` returns immediately after `set_job_error` when
    `fetch_metadata["status"] == "error"`, while a `partial` status records
    `partial_data_warning` and continues. The diagram drew an unconditional
    transition from page fetching into grouping.
  - `_fetch_spotify_misses()` raises `SpotifyUnavailableError` when token
    acquisition fails with no cache hits, caught in `_fetch_and_process` as
    `set_job_error("spotify_unavailable"); return []` -- no merge or store.
    The diagram's no-cache-hits branch rejoined the unconditional merge/store
    steps.
- Plan vs implementation: repointed the four report paths in the remediation
  plan and the two batch definitions; the Top Albums sequence now branches on
  Last.fm status (terminal error vs partial-success-with-warning) and
  terminates after the no-cache-hits token failure while retaining the
  cached-success continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the Last.fm error/partial paths and the
  no-cache-hits token failure.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve the
  four threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 final two Codex threads remediated (side-task)

- Scope: the two remaining unresolved Codex threads on `3508c48`, both on the
  Top Albums sequence diagram. Both were verified against the code before any
  edit and both were valid.
- Verification:
  - `_get_db_connection()` returns `None` when `DATABASE_URL` is unset,
    asyncpg is unavailable, or connection attempts fail; `process_albums`
    then sets a `db_cache_warning` stat and skips lookup, cleanup, and
    persistence, so every album becomes a miss. The diagram presented those
    three cache operations as unconditional.
  - `_fetch_spotify_misses()` sets `partial_data_warning` and returns without
    searching when Spotify token acquisition fails and cache hits exist, so
    the pipeline completes successfully with cached albums only; it raises
    `SpotifyUnavailableError` only when no cache hits exist. The diagram sent
    every miss through search and grouped the token failure with the terminal
    path.
- Plan vs implementation: the Top Albums sequence now branches on DB
  availability before the cache lookup and branches the Spotify token-fetch
  failure into a success-with-warning path (cached albums only) versus the
  terminal `spotify_unavailable` path.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the DB-disabled fallback and the partial-cache
  continuation.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview; the tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve both
  threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 post-push review round remediated (side-task)

- Scope: two new visible Codex threads and all five suppressed Copilot
  comments on commit `11c9885`. The seven reports described six distinct
  defects because both reviewers found the omitted heatmap admission check.
  An independent review found one adjacent README polling claim during the
  required sibling sweep.
- Verification and loop check:
  - `routes.py` confirms that heatmap requests reject a missing username,
    unavailable validation service, and unknown user before cleanup or slot
    acquisition. `loading.js` and `heatmap.js` confirm that both browsers poll
    while their background tasks run. `docsync.logic` confirms tagged entries
    rotate to per-batch logs while untagged entries rotate to the side archive.
  - Git blame assigns all three affected diagram owners to the preceding
    review-fix commit. The omitted validation and rotation branch plus both
    serialized pollers are therefore self-inflicted extraction defects, not
    newly reached backlog. The older date headers became stale when this PR
    later changed the live dashboard and findings state without refreshing
    them. README's claim that `heatmap.js` polls `/heatmap_data` predated this
    review round; the script and Batch 18 records show that it polls
    `/progress` and fetches `/heatmap_data` only after completion.
- Plan vs implementation:
  - The tooling graph now distinguishes tagged rotation into
    `docs/history/logs/` from untagged rotation into `docs/logarchive/`.
  - The heatmap sequence now shows required-input and Last.fm user-existence
    validation, including terminal 400, 404, and 503 responses before job
    admission.
  - Both request sequences now use Mermaid parallel blocks for background
    processing and progress polling. SESSION_CONTEXT and FINDINGS carry the
    current 2026-08-15 update date.
  - README now distinguishes heatmap progress polling from the completed-data
    fetch.
- Deviations: no production behavior changed and no tests were added. Existing
  tests already cover heatmap validation responses and task lifecycle behavior.
- Validation: all three edited diagrams passed Mermaid validation and opened
  in preview; each tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass.
- Closure boundary: the pushed remediation commit and its passing Quality Gate
  define done for PR #171. Do not start another patch-review-patch cycle from
  later automated comments; a future agent may scrutinize them during a
  separately scoped deep sweep, but they are not automatic blockers for this
  documentation PR. Do not merge PR #171 without separate owner instruction.
- Forward guidance:
  - Execute the already-chartered Python-only F-SWE-1 audit, then start Batch
    21 WP-1. Keep architecture streamlining found by that audit separate from
    the frontend strangler unless it directly blocks a named WP acceptance
    criterion.
  - At WP-1, decide how CI obtains and caches the pinned, digest-verified
    standalone Tailwind and daisyUI artifacts. At WP-8, make the CSS drift hook
    `always_run` with no filenames or narrow the top-level pre-commit exclude;
    otherwise it cannot see `static/`. Add focused CSS, JS, and HTML checks
    before close-out because those paths currently have no lint coverage.
  - Treat `ruff` as an optional, separately measured Python-tooling migration,
    not a frontend prerequisite. It overlaps Black, isort, autoflake, and
    flake8, would require owner-approved dependency changes, and should land
    only with explicit parity criteria after the F-SWE-1 findings are known.

### 2026-08-15 - PR #171 review findings verified and remediated (side-task)

- Scope: all eight unresolved Codex and Copilot threads on PR #171, checked
  against the current code, tests, repository rules, and sibling documentation
  before any edit. A separate two-axis review found no additional verified
  spec or standards defect in the cumulative `origin/main...HEAD` diff.
- Plan vs implementation:
  - Seven factual comments were confirmed: partial heatmap data is successful
    with a warning; cache hits still write JOBS state; both task entry points
    release their slot unconditionally; `start_job_thread` releases the slot
    before re-raising while the route deletes the new job; README's dotted-edge
    legend omitted dispatch; and `orchestrator.py` was not the import-graph top.
  - The eighth comment was also confirmed against the complete new-file rule:
    the 499-line `docs/ARCHITECTURE.md` exceeded its existing `docs/` peer cap.
    It is now a 49-line index preserving all five section anchors. Five focused
    files under `docs/architecture/` own one diagram each and are 47-101 lines.
  - README, SESSION_CONTEXT, and the Mermaid instruction now point to the
    focused owners without duplicating diagrams. Gitignored `.mmd` sources were
    used for validation and preview only.
- Deviations: no production behavior changed and no tests were added; existing
  regression tests already cover partial-data continuation, startup slot
  release, and unconditional task cleanup.
- Validation: all six published diagrams passed Mermaid validation and opened
  in preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit
  run --all-files` -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0
  with the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit the review remediation, push only with owner
  authorization, then post one batched reply and resolve the eight threads.

### 2026-08-14 - F-DATA-1 filed under P2; stale skill name corrected (side-task)

- Closes the two items the previous entry left as forward guidance.
- `F-DATA-1` self-labelled `Status: open (P2)` while sitting as the last
  entry under the P1 heading. Fixed by moving the `## P2` heading above it
  rather than relocating a 65-line block -- same result, far less churn, and
  the finding's own text is untouched.
- `DEVELOPMENT.md` still named the PR triage skill `gemini-pr-triage`; it was
  renamed `pr-bot-triage`. Real drift, not a snapshot, so it is corrected
  rather than preserved.
- **Scoping correction from the owner, recorded because an agent got it
  wrong today:** `DEVELOPMENT.md` is not an agent document. It is absent from
  docsync's live-document set and from the AGENTS.md bootstrap reading list,
  and belongs with `README.md` as human-facing methodology writing. A line
  added to `AGENT_NOTES.md` earlier the same day pointed agents at it for the
  skills-are-local decision; that line now states the decision directly
  instead. Batch definitions may still direct an agent to *write* a build
  step into it -- writing to it is in scope, treating it as a source of
  operating rules is not.
- Plan vs implementation: these two were dropped from the Phase 5 scope
  reduction and then reinstated by the owner, since both sit in working
  documents rather than in the archive the reduction was about.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0. `check_worktree_alignment.py`
  -- exit 0. Verified exactly one `## P2` heading remains and that `F-MAS-4`
  is still the last P1 entry.
- Forward guidance: nothing outstanding from the remediation. Next is the
  F-SWE-1 audit, then Batch 21 WP-1.

### 2026-08-14 - Batch 21 tooling mapped to its work packages (side-task)

- Scope: `AGENT_NOTES.md` gains a map from the installed skills and MCP
  servers to WP-1 through WP-8, written before WP-1 rather than discovered
  during it. Every entry was verified against the live machine and repository
  on the day rather than carried forward from the plan's older table.
- Structural fact recorded so nobody hunts for what is not there:
  `BATCH21_DEFINITION.md` has **no per-WP acceptance criteria**. It carries
  one batch-level list of 9 plus a per-WP validation gate that every WP runs
  identically, so the map keys on the WP and names the criteria each serves.
- Four separate skill sources are installed and their names collide -- `tdd`
  and `test-driven-development` are different files from different upstreams,
  as are `diagnosing-bugs` and `systematic-debugging`. The map says which
  source each comes from, because naming the wrong one loads the wrong file.
- Seven gaps recorded, all verified. Three of them converge on WP-8 and one
  of those has to be decided at WP-1: the pre-commit top-level exclude covers
  13 directories including `static/` and `templates/`, so the planned
  `tailwind-css-drift` hook could never fire as a file-scoped hook and must
  use the `always_run` pattern; CI has no Node and no Tailwind binary, so the
  headless-Linux fetch is unsolved; and no CSS, JS or HTML hook exists at all,
  leaving the files eight WPs rewrite unreachable by two mechanisms at once.
- Two plan claims were corrected against the live state. The exclude covers
  **13** directories, not the 12 the plan's Phase 6 still said -- an earlier
  phase had already found 13 and the later section was never updated. And the
  `skills-lock.json` drift (22 locked, 20 present) is bookkeeping only: both
  absent skills are supplied by the superpowers plugin, so it is not the
  capability gap it looks like.
- One claim was verified rather than assumed after a false negative:
  `workflow_dispatch` is on `origin/main` and usable. An initial check
  reported it missing, which turned out to be Git Bash rewriting the
  `rev:path` argument on Windows rather than anything about the repository.
- Plan vs implementation: as planned, with the MCP inventory re-enumerated
  live as the plan instructed rather than copied.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0 (expected root warning for the
  active `BATCH21_DEFINITION.md`). `check_worktree_alignment.py` -- exit 0.
- Forward guidance: this closes the post-merge remediation. Next is the
  F-SWE-1 principles audit per `docs/SWE_AUDIT_CHARTER.md`, whose report
  belongs under `docs/history/reports/`, then Batch 21 WP-1. The three open
  PR #170 review threads and the four ruleset settings remain owner-side.

### 2026-08-14 - docs/history one-off documents collected under reports/ (side-task)

- Scope: the 26 loose files at the top of `docs/history/`, which had grown
  into a flat pile beside the three organised subdirectories. Organisation
  only -- the owner scoped this to moving files, not revising them.
- 25 moved into `docs/history/reports/` with `git mv`. Not one of their
  bodies was edited.
- `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` deliberately stayed at the
  top level. It is the Batch 14 "Moved:" tombstone whose only purpose is to
  resolve references to that legacy path, so relocating it would defeat it.
  `FINDINGS.md:115` records the same disposition.
- One folder rather than a split by kind. Three Markdown links exist between
  these files, and they connect an audit, a changelog, a performance summary
  and a refactor plan -- four different kinds. Any by-kind split breaks all
  three and forces edits to files that were explicitly out of scope. A single
  folder keeps every relative link resolving untouched.
- References repointed in the live documents only: `AGENTS.md`,
  `DEVELOPMENT.md`, `FINDINGS.md`, `.claude/SESSION_CONTEXT.md` and
  `docs/SWE_AUDIT_CHARTER.md`. Two of those are forward-looking and mattered
  most: `FINDINGS.md` F-SWE-1 and the charter's output contract both name
  where the pending SWE principles audit must write its report, and both now
  name `reports/`. `AGENTS.md` documentation-touch rule likewise.
- Dated records were left as written, including the ones that now cite a
  path that moved: the archived batch definitions and logs,
  `docs/logarchive/`, the superseded plan under `docs/superpowers/plans/`,
  and PLAYBOOK Section 4's own earlier entries. A point-in-time record
  rewritten to match a later reorganisation stops being a record. This is
  the same reasoning already applied to `SESSION_CONTEXT_REFERENCE.md`.
- Consequence, stated so it is not later mistaken for rot: paths cited inside
  `docs/history/reports/*` and inside the dated archives may name the
  pre-2026-08-14 flat layout. `DEVELOPMENT.md` now says so where it describes
  the archive.
- `DOC001` scans only the live documents, so the archive's internal citations
  never entered the gate; the repointing above was still required because
  five of the moved paths were cited from documents it does scan.
- Plan vs implementation: reduced on owner direction. The planned content
  remediation -- linking the two orphans, repointing three dangling
  `EXECUTION_PLAYBOOK_2026-02-11.md` cites, annotating seven dead `app.py`
  line references in `PERFORMANCE_TIMING.md`, a completion note on
  `BATCH8_REFACTOR_PLAN.md`, collapsing the overlapping 2026-01-04
  performance documents, and a `docs/history/README.md` index -- was dropped
  as out of scope for an organisation pass.
- Deviations: none beyond that reduction.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0 (expected root warning for the
  active `BATCH21_DEFINITION.md`). `check_worktree_alignment.py` -- exit 0.
  Every repointed path was confirmed to resolve on disk.
- Forward guidance: `FINDINGS.md` F-DATA-1 still sits under the P1 heading
  while labelling itself P2, and `DEVELOPMENT.md` still calls the
  `pr-bot-triage` skill by its old `gemini-pr-triage` name. Both were part of
  the dropped remediation and remain open.

### 2026-08-14 - F-WORKTREE-5 closed: count branch candidates before filtering (side-task)

- Scope: the last open guard defect, reported independently by Codex in PR
  #170 round 5 and by Copilot in round 6, and left open across both.
- Defect: `parse_batch_branch` filtered candidates through
  `is_display_safe_ref` and only then counted them. Because that allowlist is
  deliberately narrower than Git's ref rule, a rejected candidate can still
  name a real branch, so a Section 3 declaring two branches -- one of them
  non-ASCII -- had one side discarded and reported the survivor as expected.
  The predicate decides whether a value may be rendered, not whether it exists.
- TDD: the regression test failed first with `DID NOT RAISE`, using
  `wip/b\xe4tch-21` as the second value -- Git accepts non-ASCII letters in a
  ref name, and the escape keeps the test source ASCII. Then counted distinct
  candidates before any filtering and moved the display-safety filter after
  the conflict check, where it only decides what may be rendered.
- Anti-vacuity: both orderings are load-bearing. Deleting the
  count-before-filter fails the new test; deleting the display-safety filter
  fails three cases of
  `test_a_branch_value_cannot_repaint_the_diagnostic_line`.
- Also corrected the stale justifying comment in the source, and added a
  correction note to `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`,
  whose Step 3 still prescribed the defective ordering in prose. Leaving that
  in place would have let the plan teach the defect back into the code.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `check_worktree_alignment.py` -- exit 0.
- Forward guidance: F-WORKTREE-5's two PR #170 threads can now be answered and
  resolved. F-WORKTREE-3 and F-WORKTREE-4 remain open by decision.

### 2026-08-14 - architecture diagrams corrected and given one owner (side-task)

- Scope: newly integrated Mermaid material that contradicted the code, plus
  the three older diagram copies that disagreed with it and each other.
- The central defect, in both sequence diagrams: `create_job` was drawn with
  no preceding `acquire_job_slot`. The real order is the reverse
  (`routes.py:460` then `:478`, and `:570` then `:582`) and is a fail-fast:
  the slot is taken first and the request rejected outright if none is free.
  An agent reconciling code to the diagram would allocate a `JOBS` entry and
  then reject, leaking an orphan job on every throttled call until TTL expiry.
  README already stated the correct order, so the repository contradicted
  itself. The same inversion was present in the synthesis document.
- Nine further defects, each verified against source: `worker.py` drawn as
  importing `orchestrator` and `heatmap` when both import *it* (the dispatch
  is real but runtime-only, through a callable `routes.py` injects); a
  `cache.py -> utils.py` edge that does not exist in any form; the cache
  hit/miss partition attributed to `cache.py` when it happens in
  `orchestrator.py:561-578`, and cannot happen in `cache.py`, which never sees
  the full candidate set; expiry cleanup drawn as cache-internal when the
  orchestrator calls it; `start_job_thread` given the wrong signature; the
  heatmap response typed as a rendered page rather than JSON 202; and missing
  `routes -> orchestrator`, `routes -> heatmap`, `routes -> utils` and
  `repositories -> errors` edges.
- Ownership after this change: `README.md` keeps one high-level diagram and
  now declares its arrow semantics, which was the root defect the wrong
  diagrams shared -- a dependency edge and a control-flow edge were drawn
  identically and read as the same claim. `docs/ARCHITECTURE.md` owns every
  detailed diagram. SESSION_CONTEXT Section 5 keeps a corrected compact
  summary and points there for detail. The synthesis Section 5 diagrams were
  removed with a note recording why, and its Section 6 tooling diagram
  migrated with one edge corrected: `doc_state_sync.py` imports only
  `docsync.cli`, so the fan-out had been attributed one level too high.
- Renamed the incoming doc from a dated filename to `docs/ARCHITECTURE.md`.
  It is a living reference, and `docs/` root holds durable documents while
  `docs/history/` holds dated ones; a date in the name would have become
  false at the first correction.
- Every diagram was validated before being written, per
  `.github/instructions/mermaid.instructions.md` Rule 1. This caught a real
  parse failure: a `;` inside a sequence-diagram message terminates the
  statement. The incoming document had escaped it as `&#59;&#59;`, which
  parsed but rendered as visible garbage and dropped a `%`. Removed the
  semicolon rather than escaping it.
- Now tracked, with the disposition rule recorded in the previous entry:
  `docs/ARCHITECTURE.md`, the two `.github` instruction files (converted to
  ASCII, with a ScrobbleScope scoping section reconciling their `.mmd` rule
  against this repository's tracked-Markdown layout), the corrected synthesis,
  and the PR #170 remediation plan under a superseded header naming the four
  ways it must not be executed.
- Plan vs implementation: the plan called for deleting `sequenceDiagram.mmd`
  as a duplicate. Kept instead and moved to `diagrams/`, with `*.mmd`
  gitignored -- deleting the only `.mmd` would contradict Rule 5 of the
  instruction file being tracked in the same change.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed**. All six diagrams return
  `valid: true` from the Mermaid validator. `doc_state_sync.py --check` --
  passed with the expected root-BATCH warning.
- Forward guidance: `docs/history/` still needs an index and its dead
  references repointed, and `AGENT_NOTES.md` still needs the tooling map.

### 2026-08-14 - dependency-graph and pytest-config claims corrected (side-task)

- Scope: four documentation claims that contradict the code, plus the
  ordering statements left stale by the PR #170 merge.
- Dependency graph, SESSION_CONTEXT Section 4. `heatmap.py <- config` was
  false -- `heatmap.py` imports lastfm, repositories, utils and worker, and
  reaches config only transitively through those. The same wrong chain was
  repeated in the `heatmap.py` module docstring, so fixing one source alone
  would have left the other. `app.py <- routes` omitted the `config` edge at
  `app.py:143` (`ensure_api_keys`), which exists only under the `__main__`
  guard; recorded with that scope rather than as an unconditional import.
  Added `dev/dev_start.py`, documented in Section 3 but absent from the
  graph. Every other edge was re-derived from the imports and is correct.
- Pytest config, SESSION_CONTEXT Section 7. The claimed
  `asyncio_mode = "strict"` is not configured anywhere: `pyproject.toml`
  contains only `pythonpath = "."`, and no `pytest.ini`, `setup.cfg` or
  `tox.ini` exists. `git log -S` shows the key was never in the file, so
  this was wrong when written rather than drift. The same sentence appears
  in `docs/history/SESSION_CONTEXT_REFERENCE.md`, which is left as written:
  that file is a labelled 2026-02-23 snapshot of SESSION_CONTEXT.md, and a
  snapshot that silently corrects its original stops being a snapshot.
- Ordering. PR #170 merged, so PLAYBOOK Section 3, BATCH21_DEFINITION,
  SESSION_CONTEXT Section 1 and FINDINGS all still said it must land first.
  All four now name the merge and give the F-SWE-1 audit as the next action.
  The batch-open baseline in BATCH21_DEFINITION gained its date so the 390
  is not misread as current.
- README cross-reference. "See `AGENTS.md` for the full dependency graph"
  pointed at a file that has no graph; repointed to SESSION_CONTEXT
  Section 4, which is where it lives.
- AGENTS.md gained a note that WT004 after a merge is expected and routine,
  with the tree-equality precondition that separates it from a real
  divergence. Without it the guard's stop-and-escalate remediation reads as
  alarming for what is now a per-merge occurrence.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0.
  `doc_state_sync.py --check` -- passed with the expected root-BATCH warning.
- Forward guidance: the architecture diagrams still contradict the code they
  describe, most seriously by drawing `create_job` with no preceding
  `acquire_job_slot`. That is the next side-task, followed by F-WORKTREE-5.

### 2026-08-14 - post-merge realignment and untracked-artifact disposition (side-task)

- Scope: restore a green bootstrap after PR #170 merged, and give every
  untracked path an explicit disposition. Two gates were failing at once.
- Gate 1, the worktree guard. `main` requires linear history and its ruleset
  permits only squash and rebase merges, so the merge rebased the branch and
  left `wip/batch-21` 9/9 diverged from `origin/main` with byte-identical
  trees (`dedd776` both) -- `ERROR WT004`, exit 1. Verified the two tree
  hashes matched and `git diff HEAD origin/main` was empty, then reset the
  branch onto `origin/main` and force-pushed with lease under the owner
  approval the guard's remediation requires. No file changed; only the
  commit objects the branch points at. This state will recur after every
  merge, since it follows from the ruleset rather than from any mistake.
- Gate 2, the integrity gate. The `setup-matt-pocock-skills` skill had
  appended an `## Agent skills` section to `AGENTS.md` pointing at a new
  untracked `docs/agents/`, which produced three `DOC001` errors and would
  have failed `pre-commit` and CI. Reverted. The skill followed its own
  file-selection rule (no `CLAUDE.md` exists, so `AGENTS.md` was its
  fallback); the mismatch is that it treats `AGENTS.md` as an appendable
  conventions file while this repository treats it as a governed ruleset.
- Disposition: untracked files went from 73 to 5, all five of which are
  slated for tracking in later side-tasks. Ignored with recorded reasons:
  `.agents/` and `skills-lock.json` (vendored from two upstream skill
  repositories, already drifting -- the lock names 22 skills, the tree holds
  20); `docs/agents/` (unedited vendor templates describing a layout this
  repository does not use); and `*.mmd` (Mermaid authoring scratch, kept
  separate so no diagram has a second copy free to drift).
- Note for future audits: `git status` collapses directories, so the set
  read as 8 paths and was actually 73 files. Use `-uall`. Separately,
  `git check-ignore -v <path>/` reports a spurious match against a blank
  `.gitignore` line for any path given a trailing slash -- a nonexistent
  directory and a fully tracked one both "match" it.
- Plan vs implementation: as planned. `sequenceDiagram.mmd` was slated for
  deletion as a duplicate; kept instead and moved to
  `diagrams/top-albums-sequence.mmd`, because
  `.github/instructions/mermaid.instructions.md` requires diagrams be
  written to `.mmd` files. Ignoring the pattern satisfies both that rule and
  single-source-of-truth.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0
  (WT010 only). `doc_state_sync.py --check` -- passed with the expected
  root-BATCH warning.
- Forward guidance: the four documents still describe PR #170 as pending;
  correcting them is the next side-task. Then the architecture diagrams,
  which contradict the code they describe, and F-WORKTREE-5, which two
  reviewers filed independently and which still has two open threads.

### 2026-08-12 - PR #170 round 6; reviewed, cross-references repointed (side-task)

- Scope: two visible review comments and four suppressed Copilot comments
  against the round-5 head `d8d3e0d`; one visible finding was already
  recorded, the other was a doc-currency correction.
- The F-WORKTREE-5 restatement (Copilot `r3766306027`). Valid mechanism:
  `parse_batch_branch` filters candidates through `is_display_safe_ref`
  before counting them, so a Section 3 naming one display-safe and one
  display-unsafe branch resolves to the safe one instead of raising the
  conflict error. Already recorded in the exact head being reviewed --
  `d8d3e0d` created F-WORKTREE-5 with the fix prescribed (count candidates
  before filtering). Reversing a deliberate round-2 ordering decision in a
  review round was declined then and still is; the finding stays the owner
  of that decision. Acknowledged on the thread rather than patched.
- The hardening-doc cross-references (Codex `r3766308198`). Verified valid
  against the live tree: the dated-entries pointer claimed all three
  `2026-08-11` entries lived in PLAYBOOK Section 4, but the round-1 and
  PR #169 round-6 entries had rotated to the monolith archive, and the
  open-gap list omitted F-WORKTREE-5, which `d8d3e0d` had just added.
  Repointed the pointer at the live plus archive locations and added
  F-WORKTREE-5 to the gap list, with the recorded-in commit named.
- Suppressed comments: the plan-doc observation (the Step 3 snippet
  prescribes filter-before-count) is a true statement about a historical
  implementation plan and is left as written -- the plan documents the
  as-shipped ordering and F-WORKTREE-5 carries the forward fix; the README
  badge claim (588 vs 589) was already resolved on the reviewed head, which
  shows 589.
- Plan vs implementation: doc-only change; no code and no test changed.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `doc_state_sync.py --check` -- passed with
  the expected root-BATCH warning.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1.
  F-WORKTREE-5 remains the owner's call to reverse or leave.

### 2026-08-12 - PR #170 round 5; a normalizer undid the check above it (side-task)

- Scope: three findings on the round-4 head, two acted on and one recorded.
- The one that mattered. `actual_branch` was normalized with a bare
  `strip()`, which removes Unicode whitespace, and Python counts U+00A0 as
  whitespace while Git accepts it in a ref name. So `wip/batch-21` plus a
  trailing U+00A0 -- a genuinely different ref -- folded onto the expected
  branch, matched the comparison, and produced no wrong-branch verdict at
  all. On a clean checkout that is an exit-zero run reporting alignment while
  HEAD sits on another branch. Round 4 had just closed the display half of
  this class; the normalizer one line above quietly reopened the identity
  half.
- Worth recording because the first reproduction attempt said the bug was not
  there. On this host the locale codec is cp1252, so the UTF-8 bytes arrive
  mojibaked as a non-whitespace character that survives `strip()` and trips
  the comparison by accident. Under a UTF-8 locale -- Linux, and therefore CI
  -- the decode is clean and the fold happens. A Windows-only check would
  have cleared it.
- Plan vs implementation: only Git's record terminator is trimmed now. Git
  rejects CR and LF inside a ref name, so trimming exactly those cannot
  damage a legitimate value, while every other codepoint reaches the
  comparison and the render check intact.
- The second finding was a stale count in a place the round-4 sweep did not
  know existed: the README project-structure tree carries its own per-file
  test inventory, separate from the SESSION_CONTEXT table. That sweep was
  scoped to the literal total and missed it. All 35 rows were checked this
  time, not just the row reported; one was wrong.
- Deviations: the third finding is real and not fixed. Section 3 candidates
  are filtered for display safety before the conflict check, so a document
  naming one safe and one unsafe branch resolves instead of failing closed.
  Reversing that needs its own reasoning rather than a review-round patch,
  and the round-2 justification for it is itself wrong, so it is recorded as
  F-WORKTREE-5 rather than patched here.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Re-verified end to end under a UTF-8 locale against a real trailing-U+00A0
  branch: WT003 now fires where the run previously reported the wrong branch
  as aligned.
- Forward guidance: unchanged -- land PR #170, then F-SWE-1, then Batch 21
  WP-1.

### 2026-08-12 - PR #170 round 4; the third rendered ref answered to no rule (side-task)

- Scope: one finding, reported independently by both reviewers against the
  current head, and confirmed from the code before either review was read.
  `actual_branch` was the last of the three refs these diagnostics render that
  no rule governed.
- Why it outranks its predecessors. The previous two rounds closed this class
  for the ref that comes from PLAYBOOK prose; this one comes from
  `git symbolic-ref --quiet --short HEAD`, so the attacker surface is a branch
  name rather than a document. Enumerating every `issue()` call in
  `scripts/dev/` by walking the syntax tree -- rather than trusting either
  review's list -- gives six codes that print it: WT000, WT003, WT004, WT005,
  WT006 and WT010. The dangerous one is WT000, which is only reached when the
  run is otherwise clean: between batches with no dirty files the guard exits
  zero and prints a subject the branch name controls, on the line the design
  document says a less capable agent may stop on.
- What Git actually permits, established with `git check-ref-format` and real
  branches in a disposable repository rather than assumed: ESC, DEL, CR, LF
  and the ASCII space are all rejected, so a fixture built from them describes
  a checkout that cannot exist. U+00A0, U+2028, U+202E, U+200B, U+3000 and
  U+0085 are accepted, and `symbolic-ref` returns them verbatim.
- A second, narrower fact decided the fixture. `run_git` calls
  `subprocess.run(..., text=True)` with no encoding, so Git output is decoded
  with the locale codec. Under cp1252 U+00A0 survives and pads the line while
  U+2028 arrives mangled; under a UTF-8 locale U+2028 survives and splits the
  diagnostic into two. Only U+00A0 asserts the same thing on both, so it is
  the payload the tests use.
- Plan vs implementation: `branch_label` joins `base_ref_label` in the
  diagnostics module, so all three rendered refs now answer to
  `is_display_safe_ref`. The four render sites call it; the wrong-branch
  comparison keeps the raw Git value, because labelling there would compare a
  display string against a branch name. Labelling happens at render time, not
  collection time -- the snapshot goes on naming whatever Git reported.
- Deviations: the predicate had no direct test, and a mutation matrix showed
  three of its four clauses were vacuous -- deleting the `..` rule, the `//`
  rule, or the trailing `/`, `.` and `.lock` rule each left the whole suite
  green. That is why this change adds predicate tests it did not strictly
  need: without them the new docstring's claim that those boundaries are
  covered would have been false. Every clause now fails at least one test,
  and each member of the suffix tuple fails exactly one.
- `_worktree_guard_inspection.py` remains over its directory peer cap
  (F-WORKTREE-4, accepted); this change is net zero lines there and adds no
  new deviation.
- Validation: `pytest -q` -- **588 passed** with the 3 existing
  aiohttp/Python 3.13 warnings, up 12 in one existing file, so the module
  count stays 35. All 10 pre-commit hooks pass. `doc_state_sync.py --check`
  -- exit 0 with the expected root-BATCH warning. Verified end to end
  afterwards: a real branch carrying U+00A0 was created in a scratch
  repository and the shipped CLI rendered `unnamed branch` and `worktree`,
  with no payload byte anywhere in its output.
- Forward guidance: this clears the last open PR #170 item. Land the PR, then
  F-SWE-1, then Batch 21 WP-1.

### 2026-08-12 - PR #170 round 3; the gate was ordered behind what it gates (side-task)

- Scope: two document defects found by an independent clean-room audit of the
  live repository, both still live on the current head. Neither changes code
  and neither moves the test count.
- The first is the wider one. PLAYBOOK Section 3 opened with the F-SWE-1 audit
  as the next action while its own closing sentence said PR #170 must land
  before that audit begins. Section 3 is the canonical bootstrap instruction,
  so an agent reading it top-down would start the audit against the guard and
  docsync sources this PR still changes. SESSION_CONTEXT Section 1 and
  FINDINGS already carried the correct order; `BATCH21_DEFINITION.md` carried
  a third one, naming WP-1 as next with no mention of either gate. All three
  now agree.
- The second is a false statement in the round-2 entry below. "Four cases were
  added and three trimmed" is a net increase of one, which cannot explain an
  unchanged count, and it does not describe what happened: the change swapped
  a single parametrized case for another -- the DEL payload for the U+00A0
  one -- leaving six test functions and fourteen cases on either side.
  Corrected in place rather than annotated. A dated entry is a point-in-time
  record, but that protects a claim which was accurate when written and later
  went stale; it does not preserve one that was wrong at the time. That
  distinction is the same one already applied to archived citations.
- Deviations: none.
- Validation: `pytest -q` -- **576 passed** with the 3 existing aiohttp/Python
  3.13 warnings; no test changed. All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
- Forward guidance: the remaining PR #170 item is the `actual_branch` display
  gap both reviewers reported against this head. It lands next, then the PR,
  then F-SWE-1, then Batch 21 WP-1.

### 2026-08-11 - PR #170 round 2; a denylist next door to an allowlist (side-task)

- Scope: six findings from a dispatched adversarial review of the round-1
  commit -- one blocking, four should-fix, one nit. All six were reproduced
  independently before any code changed. All six were valid.
- The blocking finding: the round-1 class `[^\x00-\x20\x7f-\x9f`]+` is an
  ASCII denylist, so everything from U+00A0 upward passed. Reproduced through
  the real parser: U+00A0, U+3000, U+2000, U+202E and U+200B all resolved to
  an `expected_branch`. A value padded with U+00A0 renders in WT003 exactly
  as one padded with the ASCII space that class excluded -- the same attack
  round 1 claimed to have closed, in a different codepoint. U+200B is worse
  than cosmetic: it renders as nothing, so WT003 demands a move to the branch
  already checked out, with no exit from that state.
- Root cause, and the part worth keeping: the guard already had the right
  control. `_SAFE_BASE_REF_RE` in `_worktree_guard_diagnostics.py` is an
  allowlist, and `base_ref_label` applies it to the other ref these same
  diagnostics interpolate. Round 1 wrote a second, weaker, differently shaped
  check in another module instead of reusing it. Two values reaching one
  rendered line answered to two rules, and only one of them had been thought
  through. This is a DRY failure that produced a security defect, not a
  style complaint.
- Plan vs implementation: the shared rule is now `is_display_safe_ref`,
  extracted from the body of `base_ref_label` so both call sites share one
  definition rather than one copying the other. `BRANCH_RE` returns to
  delimiting a candidate; `parse_batch_branch` discards candidates that fail
  the predicate before the duplicate check, so an unusable value never
  becomes a branch. No dependency-graph change: lineage already imported from
  diagnostics.
- Corrections to the round-1 entry below, which stands as written because
  dated entries are point-in-time records. Two claims in it are false. The
  class was never "what Git actually permits in a ref name": Git rejects
  `..`, `^`, `:`, `?`, `*`, `[`, `\`, `@{`, a `.lock` suffix and a trailing
  `/`, all of which that class accepted, and Git accepts non-ASCII names the
  new alphabet rejects. The current alphabet is deliberately narrower than
  Git's rule because the property enforced is display safety, not ref
  validity. Separately, "all four documented Section 3 branch styles" names a
  set that does not exist; the suite pins three, and the fourth shape the
  pattern admits is documented nowhere.
- Deviations: replacing the denylist with one shared allowlist collapsed the
  test distinctions round 1 had established. Under a single control, DEL is
  indistinguishable from the escape sequence, and U+3000, U+202E and U+200B
  from U+00A0 -- every mutation that leaks one leaks its whole group. Adding
  a case per vector would have reinstated the near-duplicate rule breach the
  review had just cleared, so the parametrization keeps one representative
  per boundary the allowlist draws and names the rest in the docstring. The
  line-break case now carries no other rejected character, which is the fix
  the review asked for and which round 1 documented as a knowing breach
  rather than repairing.
- Validation: `pytest -q` -- **576 passed** with the 3 existing
  aiohttp/Python 3.13 warnings; the count is unchanged because the
  parametrization swapped one case for another -- the DEL payload was
  replaced by the U+00A0 one -- and no test function was added or removed.
  All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Every previously bypassing codepoint was re-run against the shipped parser
  and now resolves to no branch, while `wip/batch-21` still resolves and the
  live PLAYBOOK still parses.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  narrative of this remediation, including why each round produced the next,
  is written up in `docs/history/GUARD_HARDENING_2026-08-11.md` rather than
  as new rules, since three rounds of evidence is a thin basis for amending
  a ruleset every agent follows.

### 2026-08-11 - PR #170 round 1; the forgery class was wider than the line break (side-task)

- Scope: three findings from two independent reviewers on the open PR -- two
  from Copilot review `4902230481`, raised against the current head rather
  than an earlier one, and one from Codex (`r3754609766`). All three were
  reproduced before any code changed, and all three were valid.
- The fix shipped earlier the same day was incomplete. Excluding CR and LF
  stopped a forged *second line*, but WT003 renders the captured value into a
  terminal, and an escape sequence repaints the existing line without ever
  needing one: `ESC[2J ESC[H` clears the screen and redraws a clean verdict.
  DEL erases what was already written, and padding spaces push a fake result
  across the visible line. Reproduced directly: the previous pattern returned
  an `expected_branch` still carrying a raw `\x1b`. The commit message claimed
  PLAYBOOK prose could no longer forge guard output, and that claim was
  broader than the fix behind it.
- Plan vs implementation: rather than enumerate control characters, the value
  is now restricted to what Git actually permits in a ref name -- no control
  characters, no DEL or C1 range, no spaces. That subsumes the line-break case
  instead of sitting beside it, and every rejection still fails closed to
  WT002. Verified against all four documented Section 3 branch styles and the
  live PLAYBOOK, so the narrowing costs no legitimate form.
- The second finding was a test-quality defect in the same commit. The three
  parametrized line endings were near-duplicates: `parse_batch_branch` splits
  and rejoins the section, so LF, CRLF, and CR arrive at the pattern already
  normalized to LF, and deleting `\r` from the pattern left all three green.
  That is the prohibited near-duplicate pattern, shipped in the very change
  that added an adversarial test. Replaced with one parser-level line-break
  case plus three cases that survive normalization.
- The third finding was a blast-radius miss in the previous commit, and the
  more instructive one. Step 3 of the guard implementation plan still
  prescribed the original `[^`]+` value class as a normative instruction, so
  the plan remained a working recipe for rebuilding the vulnerability the
  production fix had just closed. The earlier commit had edited that same
  plan file -- for the `debug` parameter -- without sweeping it for the
  pattern actually being changed. The snippet now carries the shipped class
  plus a note saying why it must not be relaxed, so the reason travels with
  the instruction rather than living only in production code.
- Deviations: the first attempt at the DEL case did not isolate what it
  claimed. Its payload also contained spaces, so the space rule blocked it and
  a mutant permitting DEL still passed. Found by running a mutation matrix
  over the exclusion ranges rather than by rereading the test, and corrected
  by removing the spaces from that payload. Recorded because it is the same
  defect class the finding reported, reintroduced while fixing it.
- Validation: `pytest -q` -- **576 passed** with the 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Each new case was
  mutation-checked: permitting the space boundary leaks only the padding case,
  permitting the DEL/C1 range leaks only the DEL case, and the previously
  shipped pattern leaks all three non-newline cases. The retained line-break
  case adds no unique range coverage and is kept only as the single
  parser-level case the review asked for.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  lesson generalizes the one recorded below: a fix aimed at the reported
  instance rather than the class leaves the class open, and here the reported
  instance was a line break while the class was anything a terminal
  interprets.

### 2026-08-11 - PR #169 round 6 landed after the merge; the guard could be made to lie (side-task)

- Scope: four findings from Copilot review `4877974867`'s successor,
  `4888134055`. The review was submitted 2026-08-08 04:38 UTC against head
  `6ed9d7c`; the PR merged at 07:57 UTC with no commit in between. All four
  were re-verified as still live on `main` before any work started -- the
  merged head is tree-identical to `main`, so nothing had superseded them.
- Why one of them mattered more than its "suppressed" label suggested:
  `BRANCH_RE` captured `[^`]+`, a negated class that matches newlines, while
  Section 3 is parsed as one newline-joined block. A backticked Branch value
  spanning lines was therefore captured whole, and WT003 prints that value
  verbatim. Ordinary PLAYBOOK prose could forge a second diagnostic line in
  the guard's own output -- the output the design document says a less
  capable agent can stop safely on, knowing only the exit status and the
  remediation text. Reproduced before fixing, for all three line endings.
- Plan vs implementation: the label and value are now pinned to one line
  (`[ \t]*` for the separator, `[^`\r\n]+` for the value). A rejected value
  leaves no branch to resolve, which `classify_lineage` already reports as
  WT002 -- so the fix fails closed rather than silently skipping the branch
  comparison. That mattered to the choice: making malformed metadata mean
  "no branch declared" would have repeated round 4's defect, where an
  ambiguous state switched a check off instead of blocking on it.
- The other three were documentation currency: the `inspect_worktree`
  interface in the guard plan omitted the shipped keyword-only `debug`
  parameter, and SESSION_CONTEXT and FINDINGS both carried a
  `Last updated: 2026-08-06` that predated their own 2026-08-07 content.
  PLAYBOOK Section 3 was additionally stale on its own terms: it still
  directed the reader to merge PR #169, three days after the merge, and
  carried a pre-merge caveat about a missing Quality Gate run that now
  exists and is green for `5bc6294`.
- Deviations, recorded rather than taken silently:
  - **`wip/batch-21` was realigned with an owner-authorized force-push.**
    It sat 39 ahead / 39 behind `origin/main` with an identical tree -- the
    WT004 rebase-merge artifact this guard was built to catch, and the first
    live instance of it. `git cherry` confirmed zero commits without an
    equivalent patch on `main`, so the reset was lossless. Done before any
    work so the Pre-Work Checklist could pass honestly rather than be waived.
  - The session ran in a linked worktree under `.claude/worktrees/`, already
    covered by the `.claude/*` ignore rule, reusing the primary checkout's
    sole `.venv` through the qualified paths the guard printed. This is the
    first live exercise of the F-WORKTREE-2 path: the guard reported WT000
    and resolved all three tools from the primary checkout.
- Validation: `pytest -q` -- **575 passed** with the 3 existing
  aiohttp/Python 3.13 warnings (572 before; the three new cases are the
  line-ending variants). All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Mutation-checked: the new test was watched failing on all three variants
  before the pattern was narrowed, and the existing bold-label and
  prose-tolerance cases still pass, so the pattern was not over-narrowed.
- Submitted as PR #170 against `main` after owner instruction to push and
  open one. Both Quality Gate triggers fired on the new head, `push` and
  `pull_request` -- the dropped-dispatch gap recorded against `8463ca4` did
  not recur.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  process lesson is narrower than round 5's: every remediation round here is
  triggered by a push, so a review submitted after the final push falls
  outside all of them and reaches the merge unswept. This entry records the
  gap; it does not create a rule, because round 5 established that a rule
  living in a dated entry has no force. Whether the pre-merge check belongs
  in the canonical ruleset is an owner decision, still open.

### 2026-08-07 - PR #169 round 5; contradicting a claim is itself a change (side-task)

- Scope: five suppressed findings, all valid, all self-inflicted. Four were
  caused by round 4 recording F-WORKTREE-4 without sweeping for the claims
  that finding contradicts; the fifth by round 4 repointing a resolver name at
  one site while an identical literal sat 300 lines earlier in the same file.
- Root cause, and the reason it recurs: the pre-push sweep had no pinned base,
  so each round swept only its own commits and inherited nothing. Round 2
  diagnosed this and fixed it by sweeping `git diff origin/main...HEAD`, but
  recorded the fix only in a dated log entry, which this repository treats as
  non-normative. Rounds 3 and 4 duly regressed. Both rules are now in the
  pre-push checklist rather than in a log entry: pin the sweep base to the
  branch, and treat recording a deviation as a change whose blast radius must
  be swept -- grepping the vocabulary of the property being deviated from, not
  the words of the new finding, which appear nowhere else.
- Plan vs implementation: five affirmative peer-cap claims repointed across
  the plan, the spec, and FINDINGS; the DOC003 description corrected to
  describe the check that shipped rather than a bare regex the implementation
  deliberately avoids; the interface inventory repointed to the authority API.
- Deviations, logged rather than silently taken:
  - **Round 3 shipped without a Section 4 entry.** Commits `14b3eac` and
    `1c783a9` carried no dated log entry, breaching the missing-log-entries
    anti-pattern in the very PR that ships a documentation-integrity gate.
    Recorded here retroactively rather than back-dated: round 3 fixed seven
    findings across the plan, the spec, AGENTS, and FINDINGS, and narrowed
    F-WORKTREE-3 after re-verifying its remaining clauses.
  - `_latest_test_count_from_entries` is left in place though no production
    caller remains, because deleting it rewrites eight test call sites --
    a refactor, not a review fix. Tracked as F-DOCSYNC-7.
- Peer-agent correction: a concurrent session had staged a partial fix that
  introduced two new false statements -- a docstring naming `_build_candidates`,
  which exists nowhere in the repository, and an attribution of the
  `_cross_validate` removal to round 2 when `a3c923f` did it in round 1. Both
  corrected here. Worth recording because it is the same defect class the
  round was fixing, produced independently by a different writer.
- Validation: `pytest -q` -- **572 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning.
- Forward guidance: merge. Round 5 was entirely documentation currency, and
  the remaining backlog is scoped as a hygiene batch rather than another round.

### 2026-08-07 - PR #169 round 4; the integrity gate could be switched off (side-task)

- Scope: eight findings from review round 4 -- one visible, seven suppressed.
  Six valid and fixed, one declined as an accepted deviation, one refuted.
- The material defect was self-inflicted by round 2. Making ambiguity an
  explicit state fixed the renderer but left `None` meaning two things at the
  integrity boundary, and DOC006 skips its comparison on `None`. Reproduced
  before fixing: with an unambiguous authority a stale dashboard value raises
  DOC006; with an ambiguous newest entry the same stale value passes and the
  gate exits 0. Writing one ambiguous log entry therefore disabled the check
  that exists to catch exactly that state.
- Plan vs implementation: the resolver now returns `TestCountAuthority`
  (count plus whether the newest entry was ambiguous) so the reason travels
  with the value instead of each consumer re-deriving it. DOC006 treats an
  ambiguous authority beside a named numeric field as blocking. Its
  remediation no longer names PLAYBOOK unconditionally, because the authority
  may be a rotated archive entry, and says to record an unambiguous result
  when there is no number to agree with. The status block distinguishes "no
  bold count" from "several counts without a `pytest -q` result", which sends
  the reader to the entry that caused it rather than to a missing number.
- Deliberate non-action: three guard files now exceed their directory peer
  caps (256/236 for the collector, 270/184 and 192/184 for two guard test
  modules). All were compliant before the review rounds and crossed while
  fixing confirmed defects. Splitting them was declined -- the rule prevents
  unmaintainable monoliths and none of these approaches that -- and recorded
  as F-WORKTREE-4 rather than left implicit, since Section 3 had described
  the guard as peer-sized and that had stopped being true.
- Refuted: the review claimed the SESSION_CONTEXT per-file table sums to 573
  against a stated 568. It sums to 568 across 35 rows, verified two ways and
  reconciled row-by-row against `pytest --collect-only` with no drift. First
  incorrect finding in four rounds; the others were all valid.
- Validation: `pytest -q` -- **572 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Both new behaviours were
  mutation-checked: neutralizing the ambiguity branch in the gate and in the
  renderer each fails its own regression.
- Forward guidance: merge. Four rounds in, the findings are now generated by
  the previous round's fixes rather than by the original work, and this round
  produced the first refuted item -- both are diminishing-returns signals.

### 2026-08-07 - PR #169 round 2; ordering, discovery, and a diff-derived sweep (side-task)

- Scope: thirteen findings from Copilot review 4877974867 -- one visible,
  twelve suppressed, all verified valid. Eleven were caused by the previous
  round's own fixes, so the round was treated as a remediation of that
  remediation rather than as new review traffic.
- Cause, established before fixing: the round-1 checklist was generated from
  the reviewers' findings, which by construction described the pre-change
  tree. Nothing was ever swept against the branch's own diff, so every
  citation that round 1 invalidated survived. Three local patches to one
  ordering question produced three interacting defects for the same reason.
- Plan vs implementation:
  - Test-count authority. Three findings were one defect: authority was
    decided by scanning three sources independently and reconciling the
    winners, so each rule was restated per source and their interactions were
    never modelled. Replaced by one total ordering -- clamped date, then
    source precedence -- walked once. Ambiguity became an explicit state
    rather than `None`, so it suppresses older candidates instead of falling
    through to them; a live side-task entry now outranks a same-date archived
    one; and the legacy sole-bold-count pass walks the same ordering, so such
    a count survives rotation. Heading dates are clamped to a running minimum
    within each source because position, not the date, is the authority on
    recency there -- which is what the existing append-convention tests
    already pinned.
  - Guard discovery. `--git-common-dir` names shared Git metadata, not a
    checkout, so deriving the primary root from its parent is wrong under
    `git clone --separate-git-dir`; the collector now asks Git directly with
    `worktree list --porcelain`. On POSIX a file without an execute bit is
    not a runnable tool, but existence was the whole test, so WT000 could
    advertise unusable paths; the doubles hid it by building tools with
    `touch()`. The base ref is no longer consulted at all between batches,
    where the contract says ancestry is not enforced.
  - Citation sweep, derived from `git diff origin/main...HEAD` rather than
    from the findings list. That derivation is what found the class the
    findings only sampled: nineteen further copies of the broken
    primary-checkout derivation sat in per-step snippets across both
    implementation plans, and the documented `resolve_venv` signature had
    drifted from production. Also repointed the WT-code location claim, both
    test inventories, and F-MAS-3.
- Deviations: added `workflow_dispatch` to `.github/workflows/test.yml` (two
  lines, urgent, logged here rather than deferred). GitHub created no Quality
  Gate run for the push of `8463ca4` although the push event was delivered
  and recorded, Actions was enabled, the workflow was active, its triggers
  matched, no path filter or skip-ci marker applied, and Copilot's own
  workflow ran on that same SHA eight seconds later. Evidence points to a
  one-off dispatch drop rather than a configuration fault, so the trigger is
  a durable escape hatch, not the fix. It cannot help this PR -- GitHub
  resolves dispatchable workflows from the default branch -- so the unblock
  is this push itself, which re-arms both `push` and `synchronize`.
- Numbers were re-measured from a live collection run, not transcribed: the
  README tree and the SESSION_CONTEXT table were regenerated mechanically
  from `pytest --collect-only`. A host-dependent skip introduced during this
  round was removed rather than kept, because it made the canonical test
  count differ between Windows and Ubuntu CI and would have desynchronized
  the documents permanently.
- Validation: `pytest -q` -- **568 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Coverage 89% via
  `pytest --cov=scrobblescope`.
- Forward guidance: the review-fix loop on this PR is at the point where
  findings come from the fixes rather than from the original work, so merge
  rather than iterate. Confirm a Quality Gate run exists for the new head
  before merging; if none appears, close and reopen the PR to fire
  `pull_request` again.

### 2026-08-06 - PR #169 review remediation: guard and integrity defects (side-task)

- Scope: fixed every defect confirmed by the PR #169 review round -- three
  GitHub Copilot comments plus an independent audit of the guard subsystem,
  the docsync integrity subsystem, and the canonical document corpus.
- Plan vs implementation:
  - Worktree guard. Lineage verdicts named PLAYBOOK's expected branch while
    the ancestry counts and tree identities were measured from HEAD, so
    WT004's lease-protected force-push guidance could point at a branch the
    guard never inspected; they now name the checked-out branch. Branch state
    is classified before base-ref collection, so a missing `origin/main` no
    longer masks the wrong-checkout finding and no longer errors between
    batches. Section 3 parsing accepts ordinary prose and the bold
    `**Branch:**` style instead of failing closed on them. WT008 stops naming
    a primary environment that does not exist, WT009 warns rather than blocks
    in an ordinary checkout so a fresh clone can reach Environment Setup, and
    WT002 no longer republishes raw `OSError` text or absolute paths. A
    `--debug` flag separates a guard defect from an environment failure.
  - Docsync. The documented close-out command `--fix --keep-non-current 0`
    left the repository unrepairable: the authoritative count was read after
    rotation had emptied the live window, so a superseded value was written
    and then failed DOC006, with `--fix` reporting no changes and still
    exiting 1. The count is now derived from the pre-rotation document and
    from rotated archive entries, so retention settings cannot change it.
    DOC001 was narrowed to repository-relative references and now skips fenced
    blocks; DOC003 requires a backticked all-hexadecimal token and reports the
    violation that actually occurred; DOC002 names the competing declarations;
    generated per-batch logs are no longer reported as dead links.
  - Documents. The new qualified-tool rule shipped with eighteen pre-existing
    violations in its own corpus, now covered by one conversion rule rather
    than eighteen rewrites. Corrected references to the removed
    cross-validation, restored AGENTS ownership of the test-count rule,
    documented exit code 2 and the guard's non-blocking edge states, and
    removed a restatement and a normative claim that crossed document roles.
- Deviations: `_cross_validate` and its thirteen tests were removed rather
  than repaired -- the function lost its only production caller when the CLI
  moved to the integrity layer, and both checks it performed are now enforced
  more strictly by DOC006 and DOC001. This also reduces
  `tests/test_docsync_logic.py` from 904 to 725 lines against F-MAS-3. No
  dependency, installation, destructive Git action, history rewrite, or push
  beyond the standing review-fix authorization was required.
- Validation: `pytest -q` -- **561 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Mutation-checked: the guard
  suite now fails when the diagnostic subject is wrong, where previously both
  the defect and its fix left it fully green. The close-out command was
  rehearsed end to end on a throwaway clone -- exit 1 with a corrupted count
  before, exit 0 with the correct count after. Every guard production file is
  at or below the measured 236-line peer cap.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep. After the rebase merge,
  expect the tree-identical ahead/behind artifact on `wip/batch-21` and use
  the guard's WT004 output as the first live confirmation of that path.

### 2026-08-05 - Combined integrity and guard final-review fixes (side-task)

- Scope: resolved the four final combined-branch review blockers in the
  docsync integrity gate and read-only worktree guard tests.
- Plan vs implementation:
  - Replaced Windows-separator literals with host-rendered `Path` expectations
    while retaining explicit Windows/POSIX selection, symlink reuse, and the
    simulated POSIX inspection boundary.
  - Added optional SESSION_CONTEXT DOC001 scanning with original line numbers;
    absent-session behavior, schematic exclusions, and deterministic ordering
    remain unchanged.
  - Made the Section 3 declaration the sole normalized tracked root candidate
    for the exact current batch token, covering duplicates, `BATCH210`, root
    `BATCH21.md`, subdirectories, generic templates, untracked supplied content,
    and between-batches state.
  - Sanitized every tracked-file Git failure to one stable invocation error;
    CLI exit 2 contains no stderr, traceback, credential, path, or command text.
  - Marked the approved design implemented and aligned both implementation
    plans with the verified final contracts.
- Deviations: none. No dependency, installation, destructive Git action,
  environment creation, history rewrite, push, or DEVELOPMENT workflow change
  was required.
- Validation: platform-path RED -- 1 expected failure; behavioral RED -- 5
  expected failures; focused GREEN -- **68 passed**; complete docsync suite --
  **164 passed**; complete guard suite -- **84 passed**; full `pytest -q` --
  **521 passed** with 3 existing aiohttp/Python 3.13 warnings. Production and
  guard-test files remain within their measured peer caps.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard POSIX fixture remediation (side-task)

- Scope: corrected the final-review test fixture so host-neutral guard tests
  exercise the virtualenv layout selected on Windows and POSIX runners.
- Plan vs implementation:
  - Made the shared repository fixture derive its default tool layout from the
    host OS and removed sibling `Scripts/*.exe` assumptions from inspection and
    topology tests. Direct resolver tests retain explicit Windows, POSIX,
    primary-only, missing-tool, and symlink cases.
  - Added an optional `os_name` inspection boundary whose default remains
    host-derived, then drove the public inspection-to-virtualenv path with a
    deterministic simulated POSIX linked-worktree acceptance test.
  - Updated the authoritative plan interface and fixture/topology expectations;
    the stable `scripts.dev.worktree_guard` facade exports are unchanged.
- Deviations: none. No new file, dependency, Git mutation, environment creation,
  package installation, amend, or push was required.
- Validation: simulated-POSIX RED -- 1 expected failure; focused GREEN -- **1
  passed**; all shared-fixture consumers -- **46 passed**; complete guard suite
  -- **84 passed**; full `pytest -q` -- **513 passed** with 3 existing
  aiohttp/Python 3.13 warnings. All hooks and final docsync checks pass. File
  caps, facade smoke, and live online/offline guard acceptance remain green.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard final-review remediation (side-task)

- Scope: resolved all five final plan-review findings without changing the
  guard's read-only Git contract, selected-base behavior, or public facade.
- Plan vs implementation:
  - Split the 522-line `worktree_guard.py` into a 50-line stable facade plus
    diagnostics, inspection, lineage, runner/discovery, types, and virtualenv
    modules. Every guard production file is at or below the measured 236-line and
    8,754-byte pre-existing peer caps; every new test file is at or below the
    measured 184-line and 6,615-byte test peer caps.
  - Added ERROR WT014 for unexpected inspection/runtime failures, suppressed
    subprocess exception chains, caught generic `OSError`, kept explicit
    offline WT013 final, and added a second fail-closed CLI boundary. Output
    contains neither traceback nor sensitive command/URL text.
  - Added exact `(code, severity)` coverage for WT000 through WT014 and real
    inspection-through-CLI blocking, warning-only, success, detached-CI, and
    offline-failure paths. A temporary WT006 severity downgrade produced three
    expected failures and changed both blocking CLI exits from 1 to 0.
  - Clarified the sole initial stdlib-only guard-launch exception, retained
    DEVELOPMENT as human-only rationale, and refreshed the authoritative plan
    file map and reproducible split-suite RED/GREEN commands. Aligned the design
    spec's failure contract and split test map, then refreshed README and
    SESSION_CONTEXT structure, dependency, and test inventories from the
    measured final state.
- Deviations: the final review required a plan-wide SRP split after Task 2 had
  shipped; the facade preserves every accepted import and behavior. No
  destructive Git action, environment creation, dependency install, or push
  was performed.
- Validation: pre-split facade parity -- **55 passed**; new RED suite -- 11
  expected failures and 23 passes; minimal GREEN -- **34 passed**; post-split
  original parity -- **55 passed** with 2 new cases deselected; complete focused
  suite -- **83 passed**; severity mutation restore -- **26 passed**. Full
  `pytest -q` -- **512 passed** with 3 existing aiohttp/Python
  3.13 warnings. Pre-commit and final docsync gates pass. Dirty offline live
  acceptance reports WT010, WT000 (0 behind/12 ahead, linked primary tools),
  then final WT013.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep. Use the stable
  `scripts.dev.worktree_guard` facade for all imports.

### 2026-08-05 - Worktree guard default remediation compatibility (side-task)

- Scope: restored the established WT007 operator guidance for the canonical
  `origin/main` base without changing the review-approved behavior for custom
  or local refs.
- Plan vs implementation:
  - Added an exact regression that failed against the neutralized default
    wording and protects both the explicit `git fetch --prune origin` action
    and the offline local-ref fallback.
  - Added one exact-default branch to missing-base remediation. Custom
    `upstream/trunk` and local `main` retain their selected-ref-specific,
    command-neutral guidance; WT013 ordering and exit behavior are unchanged.
- Deviations: none; this is a compatibility correction only, with no Git
  command, collector sequence, diagnostic code, or dependency change.
- Validation: focused guard suite -- **55 passed**. `pytest -q` -- **484
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard review remediation (side-task)

- Scope: corrected the two Task 2 review findings without changing the
  guard's read-only architecture or Git command sequence.
- Plan vs implementation:
  - Added final informational WT013 to every offline result, after state and
    environment diagnostics. WT000 remains success-only; offline lineage and
    virtualenv errors now retain explicit local-ref-only context.
  - Replaced hard-coded origin recovery prose with selected-base guidance.
    WT004 names the display-safe comparison ref, while WT007 uses neutral
    selected-ref or local-ref wording and never constructs a shell command.
  - Added exact inspection and CLI regressions for error-path WT013 ordering,
    custom `upstream/trunk` guidance, and the local-only `main` edge.
- Deviations: added stable code WT013 and corrected the approved plan's
  detached-CI wording so WT011 remains its only topology diagnostic while
  explicit offline mode can add the independent qualifier. Custom-base tests
  live in a new peer-sized file rather than overgrowing an existing peer.
- Validation: focused guard suite -- **54 passed**. `pytest -q` -- **483
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Read-only worktree bootstrap guard (side-task)

- Scope: completed the repository-integrity worktree safeguard before the
  F-SWE-1 audit and Batch 21 WP-1.
- Plan vs implementation:
  - Added sanitized, injectable Git collection for repository topology,
    PLAYBOOK branch metadata, base ancestry, dirty state, and tree identity.
    Missing repositories/refs, wrong or detached local branches, behind-only
    branches, and both forms of divergence fail without changing Git.
  - Added a thin CLI with stable diagnostic rendering, explicit offline
    labeling, recognized detached-CI skip behavior, and qualified primary
    checkout Python, pytest, and pre-commit paths for linked worktrees.
  - Made the read-only command a canonical post-document bootstrap gate;
    HANDOFF points to that owner, while DEVELOPMENT records only the human
    rationale and the deliberate separation from CI topology enforcement.
  - Exercised the live linked worktree offline: WT010 identified the
    intentional dirty candidate, WT000 reported 0 behind/9 ahead, and all
    three tools resolved under the primary checkout's existing `.venv`.
- Deviations: split collector acceptance across peer-sized inspection,
  topology, runner, and CLI files instead of expanding the existing classifier
  file past its directory peers; no dependencies, environment creation,
  package installs, or Git mutation.
- Validation: focused guard suite -- **49 passed**. `pytest -q` -- **478
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree classifier review remediation (side-task)

- Scope: resolved the first review round for Task 1 without expanding the
  pure classifier into Task 2's Git discovery or bootstrap integration.
- Plan vs implementation:
  - Restored Steps 2, 4, and 6 of the authoritative plan to run only the
    parser/lineage test file that exists at those stages; Step 10 onward keeps
    both focused paths after the venv test file is created.
  - Added parameterized both-sided-divergence coverage for a missing head tree,
    missing base tree, and both trees missing. Every unavailable-tree state now
    asserts WT005, while only two present matching IDs assert WT004.
  - Replaced remediation-fragment checks with the full mandated WT004 and WT005
    strings, protecting dirty reconciliation, refreshed-base/tree verification,
    owner authorization, force-push-with-lease boundaries, and the explicit
    prohibition on reset, rebase, or force-push for true divergence.
  - Mutation verification weakened both remediation constants and treated two
    missing IDs as equal; the strengthened suite produced five expected
    failures before the original correct behavior was restored.
- Deviations: none; production behavior was already correct, so this round
  strengthens regression protection and repairs plan execution order only.
- Validation: parser/lineage suite -- **23 passed**; complete focused guard
  suite -- **30 passed**. `pytest -q` -- **459 passed** with 3 existing
  aiohttp/Python 3.13 warnings. Final hooks and docsync gates pass.
- Forward guidance: proceed to Task 2's read-only CLI and bootstrap wiring;
  F-WORKTREE-1 and F-WORKTREE-2 remain open until its live linked-worktree
  acceptance passes.

### 2026-08-05 - Pure worktree safety classification (side-task)

- Scope: implemented the pure, read-only classification layer for the
  worktree-safety guard without wiring it into bootstrap or running Git.
- Plan vs implementation:
  - Added strict PLAYBOOK Section 3 parsing that ignores historical log text,
    preserves missing active-branch metadata, and rejects missing, duplicate,
    or malformed active state rather than guessing.
  - Added deterministic lineage diagnostics for detached CI/local states,
    missing or wrong active branches, dirty trees, behind-only state, and both
    content-identical rebase artifacts and true divergence. Remediation is
    diagnostic only and performs no repository mutation.
  - Added platform-aware environment resolution for ordinary and linked
    checkouts. Linked worktrees reuse the primary checkout `.venv`; distinct
    secondary environments and missing required tools fail with actionable
    diagnostics, while a symlink/junction alias to the primary environment is
    accepted.
  - Corrected two plan-interface contradictions while preserving its safety
    policy: lineage snapshots now carry the parsed active-batch discriminator,
    and the WT005 test verifies that remediation explicitly prohibits reset
    without contradicting the mandated `do not reset` wording.
  - Split immutable value types and virtualenv tests into focused peer-sized
    files to satisfy the repository's new-file size gate; the public imports
    and focused test command remain explicit in the corrected plan.
- Deviations: specification-preserving interface/test corrections only; no
  dependencies, package installs, Git commands, automatic repairs, or
  bootstrap enforcement were added.
- Validation: focused worktree-guard suite -- **27 passed**. `pytest -q` --
  **456 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: Task 2 must add the thin read-only CLI, canonical bootstrap
  rule, and real linked-worktree acceptance before F-WORKTREE-1 and
  F-WORKTREE-2 can close. The pure classifier is testable but is not yet a
  mandatory bootstrap command.

### 2026-08-05 - Docsync content-integrity plan final remediation (side-task)

- Scope: closed the plan-wide final review findings without changing the
  approved deterministic-only enforcement architecture.
- Plan vs implementation:
  - Made the newest live full-suite `pytest -q` validation in PLAYBOOK the
    authoritative test count, including side-task entries outside the
    current-batch markers; the renderer and DOC006 now share that result and
    reject conflicting named SESSION_CONTEXT count fields.
  - Tightened active-definition matching to a complete numeric batch token
    and limited DOC001's exemption to the exact Section 3 declaration.
  - Converted Git invocation `OSError` failures to sanitized `SyncError`
    diagnostics so the CLI returns 2 without a traceback, preserved analyzer
    input immutability, and strengthened the two-reference regression.
  - Refreshed the docsync package/dependency inventory and all measured test
    counts; DEVELOPMENT remains explanatory human documentation only.
- Deviations: none; no dependencies, semantic auto-fixes, or Git history
  changes.
- Validation: focused docsync suite -- **156 passed**. `pytest -q` --
  **429 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.

### 2026-08-05 - Docsync integrity review remediation (side-task)

- Scope: addressed the first Task 2 review round without changing the
  approved enforcement design.
- Plan vs implementation:
  - Added CLI regression coverage proving `--fix` returns 1 with DOC001 for
    an unresolved dead live reference and emits no stale DOC005 after it
    repairs the session block.
  - Moved resolved F-DOCSYNC-5 out of the active P0 section, leaving only the
    two worktree safeguards as open P0 gates.
  - Corrected the Task 2 focused-suite record to the measured post-remediation
    count.
- Deviations: none.
- Validation: specified docsync suite -- **112 passed**. `pytest -q` --
  **420 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.

### 2026-08-05 - Docsync content-integrity enforcement (side-task)

- Scope: wired the reviewed pure live-document integrity analyzer into the
  local and CI docsync gate, closing F-DOCSYNC-5 before Batch 21 WP-1.
- Plan vs implementation:
  - Made the side-task archive prologue renderer-owned, so `--check` detects
    a stale prefix and `--fix` restores it without changing dated entries.
  - Added stable blocking `ERROR DOC...` CLI diagnostics for live integrity
    defects. `--fix` writes deterministic output first and revalidates the
    final on-disk state; unresolved semantic defects still exit 1.
  - Retained missing optional SESSION_CONTEXT support and the existing root
    BATCH-file warnings, while removing legacy warning-only CLI validation.
- Deviations: none.
- Validation: targeted docsync suite -- **111 passed**. `pytest -q` --
  **419 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the separate read-only worktree-safety guard;
  F-WORKTREE-1 and F-WORKTREE-2 remain the P0 gate before Batch 21 WP-1.

### 2026-08-05 - Docsync integrity analyzer review remediation (side-task)

- Scope: corrected two review findings in the pure analyzer before its
  deferred CLI/CI wiring task.
- Plan vs implementation:
  - Active definitions now require both supplied live-document content and a
    tracked path; an untracked declaration reports DOC002 at its Section 3
    declaration line rather than being masked by the DOC001 exemption.
  - Replaced ignored dated Section 4 entry lines with blank placeholders, so
    later PLAYBOOK diagnostics retain their original file line numbers.
  - Added separate regression tests that first reproduced both defects.
- Deviations: none; integration remains intentionally out of scope.
- Validation: `pytest -q` -- **415 passed** with 3 existing aiohttp/Python
  3.13 warnings. Final hook and docsync gates pass.
- Forward guidance: Task 2 can consume the corrected pure analyzer without
  reimplementing its active-definition or PLAYBOOK source-location rules.

### 2026-08-05 - Docsync live-document integrity analyzer (side-task)

- Scope: added the pure live-document integrity analyzer for the P0
  repository-content safeguard; enforcement is intentionally deferred to the
  next ordered task.
- Plan vs implementation:
  - Added deterministic `IntegrityIssue` diagnostics DOC001 through DOC006
    for dead concrete references, active-definition drift, volatile Branch
    metadata, archive-prologue drift, stale managed session content, and
    contradictory current test counts.
  - Added adversarial pure-unit coverage for literal-reference extraction,
    tracked-path normalization, active-definition metadata, archive/session
    comparison, and deterministic ordering. The analyzer is not yet wired
    into the docsync hook or CI gate, so F-DOCSYNC-5 remains open.
- Deviations: none; CLI integration and severity changes remain the next task.
- Validation: `pytest -q` -- **413 passed** with 3 existing aiohttp/Python
  3.13 warnings. Final hook and docsync gates pass.
- Forward guidance: integrate the pure analyzer without duplicating its
  parsing or changing the established sync behavior before enforcement.

### 2026-08-05 - P0 integrity/worktree implementation plans (side-task)

- Scope: translated the owner-approved repository-integrity/worktree-safety
  specification into executable, test-first implementation plans.
- Plan vs implementation:
  - Split the two independent safeguards into ordered plans so each produces
    a reviewable, independently testable result: CI-blocking docsync content
    integrity first, then local worktree lineage and shared-virtualenv safety.
  - Mapped exact files, interfaces, diagnostic codes, adversarial tests,
    canonical documentation ownership, fault-injection evidence, validation
    gates, and commit boundaries. Each code step includes concrete signatures
    or snippets rather than delegating design decisions to the executor.
  - Self-reviewed both plans against every approved-spec section, checked type
    and diagnostic-name consistency, removed placeholders, balanced Markdown
    code fences, and kept the second plan smaller than its peer per the new-file
    size rule.
- Deviations: the single specification becomes two sequential plans because
  repository-content integrity and local Git topology are independent failure
  domains. Scope and execution order are unchanged.
- Validation: plan self-review -- pass. `pytest -q` -- **390 passed** with 3
  existing aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all
  10 hooks pass. Final `doc_state_sync.py --check` -- exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: choose Subagent-Driven execution (recommended) or Inline
  Execution. Complete both plans before F-SWE-1; Batch 21 WP-1 remains gated.

### 2026-08-05 - Repository-integrity and worktree-guard design (side-task)

- Scope: investigated why canonical documentation drift and repeated
  post-rebase worktree divergence survived green local and CI gates, then
  captured the owner-approved remediation as a written design.
- Plan vs implementation:
  - Realigned the clean, tree-identical `wip/batch-21` branch from the
    post-PR-#168 3/3 divergence to `origin/main` and force-pushed with lease
    after explicit owner authorization.
  - Split the remediation into a blocking repository-content integrity layer
    inside docsync and a separate read-only local worktree alignment guard;
    detached CI runs the former and unit-tests the latter, but does not
    pretend to validate local worktree topology.
  - Logged F-WORKTREE-1 and F-WORKTREE-2, and reopened F-DOCSYNC-5 as P0
    items until mechanical prevention lands. The second worktree finding was
    reproduced during validation: a linked root has no gitignored `.venv`, so
    the test gate must reuse the qualified environment under the primary
    checkout. Updated DEVELOPMENT.md with the human-readable incidents and
    design rationale while preserving AGENTS.md as the future owner of
    agent-facing rules.
  - Wrote the approved design at
    `docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
- Deviations: implementation is deliberately deferred until the owner reviews
  the written specification, as required by the selected design workflow.
- Validation: written-spec self-review -- pass. Qualified shared-venv
  `pytest -q` -- **390 passed** with 3 existing aiohttp/Python 3.13 warnings.
  `pre-commit run --all-files` -- all 10 hooks pass. Final
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: review the written specification. After approval, create
  the implementation plan, land both P0 safeguards, then execute the full
  F-SWE-1 sweep; Batch 21 WP-1 remains gated behind the remediation.

### 2026-08-03 - PR #168 pre-merge canonical-doc audit (side-task)

- Scope: audited the PR head against the canonical documentation and
  handoff rules before rebase merge; found and fixed two P1 operational
  documentation defects that could misdirect the next agent.
- Plan vs implementation:
  - Removed the superseded `fa61716` fork point from the active Batch 21
    definition. Branch lineage is volatile during review-remediation
    rebases, so the definition now delegates that state to PLAYBOOK
    Section 4 instead of pinning another copy.
  - Corrected the live side-task archive header from obsolete PLAYBOOK
    Section 10 to Section 4 and repointed all three read helpers from the
    `docs/history/` tombstone to `docs/logarchive/`.
  - Recorded the resolved P1 issue as FINDINGS.md F-DOCSYNC-5 under the
    repository's source-tag nomenclature and refreshed the file's
    last-updated date.
  - Replaced the SWE audit charter's fixed F-DOCSYNC numeric range with
    a FINDINGS-owned category pointer so new or resolved F-DOCSYNC items
    remain in the do-not-re-report baseline.
- Deviations: none. PR #168 contains no runtime behavior change, and no
  GitHub thread or PR state was changed.
- Validation: targeted documentation regression check -- pass.
  `pytest -q` -- **390 passed** with 3 existing aiohttp/Python 3.13
  warnings. `pre-commit run --all-files` -- all 10 hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: after PR #168 merges, realign `wip/batch-21` with
  `main`, then continue Batch 21 WP-1. F-SWE-1 remains a separate,
  chartered audit whose execution is still pending.

### 2026-08-03 - PR #168 Copilot review round 1 (side-task)

- Scope: assessed both Copilot review comments on PR #168; both were
  technically valid and addressed.
- Plan vs implementation:
  - Replaced the canonical `Registry entries 4 and 5` example in
    `AGENTS.md` with symbolic placeholders. The numeric example matched
    the expanded sweep it was explaining, so the rule created its own
    violation and made the related no-current-hits claim false.
  - Corrected the prior side-task's forward guidance. The branch was
    level with `main` immediately after realignment, but applying the
    review-fix commit left it directly based on `main` and one commit
    ahead, not equal to it.
- Deviations: none. Dated point-in-time log references remain unchanged
  under the canonical rule's explicit historical-record exception.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: wait for the next PR #168 review round before WP-1.

### 2026-08-02 - Post-merge branch realign; PR #166 review fixes (side-task)

- Scope: PR #165 was rebase-merged (main tip `458f9ad`). The rebase
  produced the usual 23/23 ahead-behind artifact with an identical tree,
  and PR #166 was opened from it in the reverse direction
  (`main` -> `wip/batch-21`); #167 was opened from a separate Copilot
  branch to fix review comments. The owner closed both.
- Plan vs implementation:
  - `wip/batch-21` reset to `origin/main` and force-pushed with lease;
    ahead-behind is 0/0. Commit history on `main` is intact -- all 23
    commits landed individually. The apparent bunching is rebase
    rewriting committer dates while author dates stay distinct.
  - Reapplied the three valid PR #166 findings here so they arrive
    validated and on one lineage: the `MAX_ACTIVE_JOBS` comment no
    longer claims arrival-order serialization (`threading.Lock` gives no
    FIFO guarantee -- it now says each throttle serializes reservations
    behind a shared lock with no ordering guarantee); the canonical
    numeric-citation sweep covers plural and alternate forms, since a
    pattern written as `Registry #\d` cannot match
    `Registry entries 4 and 5`; and the round-9 entry's "returns
    nothing" claim is qualified to exclude dated point-in-time records,
    which legitimately contain such citations.
  - Third occurrence of a countermeasure scoped to the instance that
    prompted it rather than the class. The rule now says explicitly to
    match plural and alternate forms.
- Deviations: none. PR #167 additionally proposed merging #166; that was
  wrong -- #166 pointed `main` at `wip/batch-21`, so merging it would
  have produced the merge commit the rebase-merge workflow exists to
  avoid.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: branch is directly based on `main`, with this one
  review-fix commit ahead, and is ready for WP-1 after PR review.

### 2026-08-01 - PR #165 round 9; new rules are not retroactive (side-task)

- Scope: three suppressed comments, all valid -- numeric citations into
  ordered lists (`Anti-Pattern Registry entries 4 and 5`, two
  `acceptance criterion 8` references) that the registry's own
  name-based citation rule prohibits.
- Cause, established from history rather than assumed: the citations
  were written in the SSOT pass and the FINDINGS refresh; the rule
  banning them was written two commits later. Nothing swept the
  existing corpus against the new rule, so the rule shipped with a
  backlog of its own violations. The pre-push checklist greps the blast
  radius of *the change*; when the change is a rule, the blast radius is
  the whole repository, and that leap was never made.
- Plan vs implementation: all three citations repointed by name. A
  repo-wide sweep for `entries N`, `Registry #N`, `criterion N`,
  `step N`, `rule N`, `item N` across every canonical doc returns no
  matches outside dated point-in-time log records, which stay as
  written. The lesson was folded into the existing blast-radius
  anti-pattern as one sentence rather than becoming a fifteenth
  registry entry -- see the verbosity note below.
- Deliberate non-action: folded into an existing entry rather than added
  as a fifteenth, because rule text has begun causing findings as well
  as preventing them -- the registry grew long enough to need numbers,
  and the numbers became the defect.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: merge rather than iterate further.

### 2026-08-01 - PR #165 round 8; over-broad claims narrowed (side-task)

- Scope: three suppressed comments, all valid, all fixed.
- Plan vs implementation:
  - The Section 2 note claimed close-out entries for *each* batch live
    in the monolith archive. False: `BATCH18_LOG.md` holds its own
    close-out because that heading carried a `(Batch 18 WP-5)` tag;
    only the `(Batch N close-out)` spelling misroutes. Narrowed here
    and in F-DOCSYNC-3, which carried the same over-broad framing.
  - The Section 2 subsection heading still read "Completed batches
    (definitions archived)" while the table lists the active batch with
    a root definition. Retitled to cover both.
  - `AGENT_NOTES.md` asserted a batch was active and where its
    definition sits in the same breath as declaring that the file does
    not track batch state -- self-contradictory, and false between
    batches. Reduced to the pointer alone.
  - Anti-Pattern Registry, assertions entry: broadened from the one
    phrasing that had failed before (`all N`, ranges) to the full
    quantifier vocabulary, since the narrow sweep is what let "each
    batch" through.
- Assessment of the review loop: none of these three were caused by the
  previous round's fixes -- the fix-causes-finding chain that drove
  rounds 5 through 7 did not repeat. What remains is pre-existing
  over-broad wording in text the sweep touched. On that basis the
  pre-push checklist is working and mechanical enforcement is not yet
  warranted; a consistency-lint hook stays a docsync-WP candidate rather
  than scope creep into this PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: findings have narrowed to wording precision rather
  than correctness; this is the diminishing-returns point. Recommend
  merging rather than requesting another round.

### 2026-08-01 - PR #165 round 7 + review-loop pattern sweep (side-task)

- Scope: owner asked for the round-7 findings to be verified but not
  fixed until a sweep across every review round on PRs #163/#164/#165
  identified why fixes keep producing new findings. Corpus: ~40
  findings over 12 rounds.
- Round 7 findings (all three valid):
  - `AGENTS.md` close-out step 3 said "add a row" to PLAYBOOK Section 2,
    but the active batch already has one -- following it literally
    duplicates the row. Now says repoint the existing row, add only if
    absent.
  - The sufficiency gate required agreement with "the batch definition"
    while bootstrap step 3 states no definition exists between batches,
    so the gate was unsatisfiable in that state. Both states now
    stated.
  - `docs/SWE_AUDIT_CHARTER.md` labelled its differential baseline
    "Open findings" while including F-DOCSYNC-4, resolved earlier in
    this same PR. Relabelled as already-tracked regardless of status,
    with an instruction to check each `Status:` line.
- Sweep results -- four recurring classes, now in the Anti-Pattern
  Registry. Two were already logged; two are new:
  - *Fixing the instance instead of the class* (logged previously): the
    dominant cause. Rounds 6 and 7 findings were created almost
    entirely by rounds 5 and 6 fixes.
  - *Lossy or contradictory consolidation* (new): collapsing duplicated
    rules to one owner while leaving copies, dropping a specific
    prohibition (the `git add -A` ban nearly vanished this way), or
    contradicting another section of the same file.
  - *Assertions over sets, ranges, and citations* (new): "all seven CSS
    files", "F-DOCSYNC-1 through F-DOCSYNC-4", citing a gitignored
    file, citing an anti-pattern that does not cover the case.
  - *Happy-path-only procedures* (new): steps that break in an edge
    state -- row already present, no definition between batches, gate
    ordered before the work it validates.
- Why the loop exists, and the structural fix: the validation gates
  check mechanics only -- nothing verifies that one document still
  agrees with another, so each fix's damage is discoverable only by the
  next review round. Added a "Pre-push self-review" block to Commit
  Rules: read changed files whole rather than as diffs, run the
  blast-radius greps, walk procedures through edge states, and prefer
  deletion to addition because every added sentence is new surface area.
- Deviations: none. The new checklist caught its own first violation --
  the draft cited registry entries by number, which the same registry
  forbids; now cited by name.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the honest test is round 8. If it finds fresh
  self-inflicted drift, the checklist is not enough and the next step is
  mechanical enforcement (a consistency-lint hook) rather than more
  prose.

### 2026-08-01 - PR #165 review round 6; self-inflicted-drift anti-pattern (side-task)

- Scope: round 6 returned three suppressed comments, zero visible. All
  three verified valid -- and all three were created by round 5's own
  fixes, which is the finding that matters more than the fixes.
- Plan vs implementation:
  - Acted: `AGENTS.md` Side-Task Handling and `HANDOFF_PROMPT.md` both
    cited "Commit Rules step 4" for the documentation requirement; the
    round-5 reorder moved it to step 1. Repointed **by name** ("the
    documentation step", "Missing log entries") rather than by number,
    so a future reorder cannot re-stale them.
  - Acted: `AGENT_NOTES.md` load-testing bullet still asserted the
    per-job guarantee and single-throttle model that round 5 corrected
    in `config.py`. Rewritten to match and to point at `config.py` as
    the single owner of the rationale.
  - Declined (precedent): PLAYBOOK Section 4 entries at :163 and :262
    also contain "step 3/4/6" references that no longer match the
    current numbering. They are dated point-in-time records of what was
    true when written; retro-editing rotated log content was declined
    and accepted in PR #162 round 3 and PR #163 round 3.
  - Root-cause fix: new Anti-Pattern Registry entry 11, "Fixing the
    instance instead of the class" -- requires a blast-radius grep
    before the gates (references to anything renumbered/renamed, and
    sibling copies of any corrected claim), and prefers name-based
    cross-references over numeric ones.
  - Swept beyond the three findings: verified the remaining numeric
    references (`AGENTS.md` close-out step 2, charter bootstrap step 1)
    still resolve correctly, and that the `req/s` claims in F-B18-11 and
    F-B18-10 are accurate because the heatmap and album pipelines are
    both Last.fm-only.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply.

### 2026-08-01 - PR #165 Copilot review round 5 (side-task)

- Scope: round 5 returned "not ready to approve" with four suppressed
  comments and zero visible ones. All four verified valid against the
  code; all four acted on.
- Plan vs implementation:
  - `config.py`: the MAX_ACTIVE_JOBS rationale claimed "one global
    10 req/s API throttle". Wrong -- `utils.py:81-82` builds separate
    `_LASTFM_THROTTLE` and `_SPOTIFY_THROTTLE`. Comment now names the
    Last.fm scrobble-fetch phase as the binding constraint.
  - `AGENTS.md` commit procedure: the docsync `--check` gate sat at
    step 3 while the PLAYBOOK update was step 4, so the gate ran before
    the documentation it validates (and `pre-commit` carries the
    `doc-state-sync-check` hook). Reordered: write docs, `--fix`, then
    the three gates on the final state. This matches what sessions
    already do in practice; only the written rule was wrong. Fixed a
    duplicate step number introduced by the renumber.
  - `FINDINGS.md` F-DATA-1 open question 2 proposed grouping
    `spotify_cache` by `artist_norm + album_norm` -- which is the
    primary key (`init_db.py:42`), so every group holds exactly one row
    and the upsert has already overwritten any rival date. Replaced
    with the two methods that can actually work (re-run the Spotify
    search and compare against the earliest fresh candidate, or
    cross-check MusicBrainz).
  - `docs/SWE_AUDIT_CHARTER.md`: prescribed commit subject was a noun
    phrase, violating the imperative-subject rule the charter tells
    executors to follow. Now imperative.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply. PR #165 remains merge-ready pending the next
  auto-review.

### 2026-07-31 - FINDINGS: record reissue cache-key collapse (side-task)

- Scope: capture a data-quality mechanism found while discussing the
  DEVELOPMENT.md rewrite, before the reasoning was lost to chat. No code
  change -- this is a finding, not a fix.
- Plan vs implementation: added `F-DATA-1` under P2.
  `normalize_name()` strips `deluxe`/`edition`/`remastered` and eight
  more words, so a reissue and its original normalize identically; since
  the `spotify_cache` PK is `artist_norm + album_norm`, they share one
  row and whichever populated it first serves its `release_date` for 30
  days. Owner observed this with Viagra Boys "viagr aboys" (2025)
  surfacing under 2026 via the JP deluxe released 2026-01-09, on an
  account that never played it.
- The finding records why the collapse is nonetheless correct (Last.fm
  scrobbles the same record under inconsistent album strings; keying
  editions apart would split one album into several leaderboard rows
  with divided playcounts), the candidate fix (decouple counting from
  dating -- keep the collapse for aggregation, take the *earliest*
  candidate release date when resolving the year, no schema change), the
  rejected boolean discriminator and why, three questions answerable by
  querying the cache, and the note that Spotify exposes no
  original-release-date field at all.
- Deviations: earlier in the session an agent claim that release-date
  drift was a systemic risk was walked back. The owner has ~14 years of
  scrobbles and one recalled instance; the claim had been reasoned from
  a plausible mechanism rather than measured. Filed P2 with low user
  impact stated explicitly, and `release_scope: all` already bypasses
  date filtering. Recording the correction so the finding is not read as
  more urgent than the evidence supports.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: question 2 (which other albums) is a cache query, not
  an investigation -- run it before designing any fix. Sequenced behind
  Batch 21, the F-B20-2 orchestrator split, and the test/docstring pass
  per owner priority.

### 2026-07-31 - DEVELOPMENT.md: correct HANDOFF_PROMPT description (side-task)

- Scope: DEVELOPMENT.md described `HANDOFF_PROMPT.md` as a condensed
  checklist of rules, gates, read order, and commit discipline. That was
  accurate until this branch, which reduced the file to post-read
  verification plus the handoff checklist and replaced everything else
  with pointers. The description was left describing the architecture
  this PR removed.
- Plan vs implementation: two passages corrected -- the architecture
  overview and the per-file section, which was also retitled from
  "Bootstrap Procedure" to "Session Start and Handoff" to match what the
  file now contains. Both now state why the summaries were removed
  (each restatement drifted from its source), which is the reasoning the
  rest of the document uses.
- Deviations: scope-limited on purpose. Only the passages this branch
  made wrong were touched. DEVELOPMENT.md has other known staleness --
  the `gemini-pr-triage` skill is now `pr-bot-triage`, the
  review-suggestions section predates repo-aware review tooling, and the
  closing paragraph needs a rewrite -- all deferred to a post-merge
  documentation pass, per the same in-scope test applied to
  `concurrent_users_test.py` in review round 1.
- Note: this class of staleness is invisible to diff-scoped review.
  Copilot reported "13/13 changed files" across four rounds and
  DEVELOPMENT.md was never among them, so a file made wrong by the diff
  but not part of it cannot be flagged. Worth remembering when relying on
  automated review for consistency.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the post-merge pass should reframe the review section
  around how the tooling changed rather than around rejection, and
  `README.md:492` must move with it -- it currently promises a section on
  suggestions "evaluated and rejected".

### 2026-07-31 - Push rule: standing exception for review-fix commits (side-task)

- Scope: owner-directed policy change, not a review finding. During PR
  #165 triage the owner granted a standing authorization to push
  review-driven commits without asking per round, on the reasoning that
  the agent reaches the diminishing-returns point on its own and a
  per-round approval round-trip only stalls the loop.
- Plan vs implementation: encoded in AGENTS.md Commit Rules step 6 rather
  than left as an agent-side preference, because AGENTS.md is the rules
  SSOT and a spoken rule that contradicts the written one is exactly the
  defect this PR spent four rounds removing. Scoped per owner: **Claude
  Code and Codex sessions only.** GitHub Copilot task sessions and their
  subagents, Jules, and any other agent follow the unmodified rule --
  the owner does not extend equal trust to agents of varying quality
  that it cannot inspect per-invocation. Step 6 already carried a
  Copilot-specific clause, so per-agent scoping had precedent.
- Deviations: the exception is deliberately narrow. Review-fix commits on
  an open PR only; batch and WP commits still pause, and force-pushes,
  history rewrites, and anything touching `main` still require explicit
  instruction.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: if the agent roster changes, this clause names
  specific agents and will need revisiting -- it is an allowlist, not a
  capability test.

### 2026-07-31 - PR #165 Copilot review round 4 (side-task)

- Scope: zero visible comments, two suppressed, both valid and both real
  defects rather than the judgement-call trade-offs round 3 predicted.
  The convergence call made after round 3 was wrong; recorded here
  because the wrong prediction is the useful part. Tally 18/18.
- Plan vs implementation:
  - **A rule was silently deleted by this PR, and round 1 removed the
    last copy.** The prohibition on `git add -A` / `git add .` lived in
    two places before this branch: AGENT_NOTES.md Owner Preferences and
    the old HANDOFF_PROMPT anti-pattern list. The PR's HANDOFF_PROMPT
    rewrite dropped its copy, and the round-1 dedup replaced the
    AGENT_NOTES copy with a pointer to AGENTS.md Commit Rules -- which
    never contained the prohibition. Step 5 only said "stage only files
    changed for this work package", which `git add -A` can satisfy when
    every changed file happens to belong to the WP. Restored explicitly
    in Commit Rules step 5, the canonical location the pointer targets.
  - Lesson: verifying that a pointer's target "covers it in substance"
    is not enough. Round 1 checked AGENTS.md:167 and accepted a
    paraphrase as equivalent when it dropped a prohibition. Before
    deleting a rule copy, diff the *specific obligations*, not the topic.
  - `scripts/testing/concurrent_users_test.py` promised queuing in three
    places. `acquire_job_slot()` uses `acquire(blocking=False)` and both
    call sites (`routes.py:460`, `routes.py:570`) return an error
    immediately, so excess submissions are rejected and never queued.
    Round 1 edited one of those lines for the cap change without
    questioning the surrounding claim. Now describes rejection, matching
    README's "capacity rejections" wording.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: do not call convergence from the *shape* of a round's
  findings. Rounds 2 and 3 returned zero visible comments and were still
  productive; round 4 found a deleted rule. Stop when a round returns
  nothing, not when the findings look minor.

### 2026-07-31 - PR #165 Copilot review round 3 (side-task)

- Scope: round 3 again returned zero visible comments and three
  suppressed ones. Two acted on in full, one acted on in part.
  Suppressed-block tally now 16/16 across #163, #164, and #165.
- Plan vs implementation:
  - `docs/SWE_AUDIT_CHARTER.md` Section 3 copied the ten principle names
    from AGENT_NOTES.md and **had already drifted**: the copy dropped the
    definitions for Dependency Inversion, Least Knowledge, and Fail Fast,
    and truncated SRP from "single responsibility per module/function".
    This is the rare case where the drift was demonstrable rather than
    hypothetical, so the copy is gone. The section now points at
    AGENT_NOTES.md and keeps only the two audit-specific methods (Clean
    Architecture via the SESSION_CONTEXT Section 4 acyclic graph, Boy
    Scout via git history).
  - `docs/SWE_AUDIT_CHARTER.md` Section 6 restated side-task entry
    placement that AGENTS.md Side-Task Handling owns -- and round 2 had
    just renumbered that section, so the charter was already a rewrite
    away from being wrong. Delegated.
  - `HANDOFF_PROMPT.md` Section 1 restated the bootstrap-conflict rule
    verbatim from AGENTS.md:64-65 inside a paragraph that claims rules
    "are not restated here". Removed.
- Deviations: **partially declined** the reviewer's request to also strip
  "Do not push without owner instruction" from the charter's commit step.
  Verified AGENTS.md:171 owns it, so the SSOT argument is technically
  right, but that line sits at the point of action for a cold-start
  executor (the charter is written so Codex can run it without prior
  context) and a push is not reversible. Deliberate safety redundancy is
  worth one line. Removed the same sentence from HANDOFF_PROMPT Section 1
  by contrast, because there the reader is being sent to AGENTS.md in the
  very same paragraph, so the copy buys nothing.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: watch for diminishing returns. Rounds 1-3 were all
  genuine, but the remaining duplication is increasingly load-bearing
  context for cold-start executors; judge each on whether the copy can
  drift *and* whether losing it costs a reader who cannot see the source.
  Batch 21 WP-1 remains the next action.

### 2026-07-31 - PR #165 Copilot review round 2 (side-task)

- Scope: round 2 returned **zero visible comments and five suppressed
  ones**. All five were valid. The suppressed-block hit rate is now 13/13
  across PRs #163, #164, and #165 while the visible stream has gone dry
  twice; treat that block as the primary signal, not an appendix.
- Plan vs implementation:
  - `AGENTS.md` Side-Task Handling read as an ordered procedure whose
    step 1 was "commit" and step 2 "add the log entry", contradicting
    Commit Rules step 4 and Anti-Pattern Registry #9, which require the
    entry to be in the same commit. Since AGENTS.md is now the rules
    SSOT, an internal contradiction there is load-bearing. Reworded so
    side-tasks inherit the commit rules unchanged and differ only in
    entry placement and tagging; the remaining steps renumbered.
  - `HANDOFF_PROMPT.md` Section 5 told agents to document completion
    *after* committing and to commit the docs separately -- the same
    conflict, one level down. Now states that docs land in the commit.
  - Resolution was evidence-based, not a judgement call: registry #9
    forbids a commit without its entry, and all four recent side-task
    commits (`2559f39`, `2b9b095`, `98cc50c`, `900d0e6`) bundle
    PLAYBOOK + archive with the change. Docs were wrong; practice was
    right.
  - `FINDINGS.md` F-LOAD-1 proposed an "N/5 slots in use" hint, which
    hard-codes a value that is env-configurable. This PR had changed it
    from "N/10" -- swapping one literal for another. Now specifies
    reading the cap from `MAX_ACTIVE_JOBS` at render time.
  - `.claude/SESSION_CONTEXT.md` header said 2026-07-28 while the body
    recorded a 2026-07-31 runtime change. Header updated.
  - `docs/SWE_AUDIT_CHARTER.md` cited "AGENTS.md registry #10" for
    silent scope reduction; #10 is about re-measuring canonical figures
    and says nothing about audit coverage. The charter was added in this
    PR, so this was a sourcing error at write time, not staleness --
    corrected rather than left as a point-in-time record. Now states the
    requirement directly.
- Deviations: round 1 split its fixes across two commits, and `07c4f5b`
  therefore landed without its own Section 4 entry -- a violation of
  Anti-Pattern Registry #9, the rule this round clarifies. Not rewritten:
  both commits were already pushed and history rewrites need owner
  instruction. Round 2 is a single commit. Standing lesson: this repo's
  #9 outranks the generic "prefer small atomic commits" heuristic, and
  the one-commit-per-review-round precedent from PR #163 was correct.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: Batch 21 WP-1 remains the next action. `gh` writes
  are still unavailable this session, so the round-2 reply is unposted.

### 2026-07-31 - PR #165 Copilot review round 1 (side-task)

- Scope: triaged the five comments on PR #165 (four inline, one inside
  the suppressed low-confidence block). All five were valid; none were
  declined. Two themes: an overstated concurrency claim and three
  leftover copies of rules AGENTS.md now owns.
- Plan vs implementation:
  - `config.py`: the MAX_ACTIVE_JOBS rationale claimed a cap of 5 "keeps
    >=2 req/s per job". `_GlobalThrottle.next_wait()` (utils.py) advances
    a single next-allowed timestamp under one lock, serializing callers
    in arrival order with no per-job accounting, so a busy job can take
    more slots than an idle one. Reworded as an average, matching the
    "~10/N req/s" framing already used in AGENT_NOTES.md.
  - `scripts/testing/concurrent_users_test.py`: module docstring and
    `build_parser()` still said the default was 10 and told operators to
    set `--concurrency` above 10. Both now say 5. A repo-wide sweep found
    no other live stale reference; remaining "default 10" hits are all
    under `docs/history/` and stay as written (point-in-time records).
  - `AGENT_NOTES.md`: the Owner Preferences commit-mechanics bullet and
    the Venv "In short:" line each pointed at AGENTS.md and then restated
    its content anyway. Both reduced to pointers after verifying AGENTS.md
    genuinely carries every rule involved.
  - `HANDOFF_PROMPT.md`: Section 2 restated the full three-command gate
    and the root-BATCH warning, contradicting the Document Roles contract
    added by this same PR, which assigns gates to AGENTS.md. Collapsed to
    a pointer matching the wording Sections 3 and 4 already use.
- Deviations: none. No test changes -- all five edits are comment or
  documentation text with no behavior change.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the suppressed-comment block again held a real
  finding (8/8 across PRs #163/#164/#165), so keep expanding it. Batch 21
  WP-1 remains the next action.

### 2026-07-31 - WP-1 token values pinned in the definition (side-task)

- Scope: make WP-1 executor-agnostic. The definition referenced "the
  audit token sheet" but only carried headline values; the full sheet
  lived in the Claude Design project and one agent's session notes,
  blocking a cold-start executor (e.g. a Codex session) from
  implementing WP-1 faithfully.
- Plan vs implementation: the WP-1 theme bullet now pins the complete
  sheet -- all eight colors (light bg/bg-2/ink/primary, dark
  bg/surface/text/primary), the three-family type system with sizes,
  the 4px spacing ladder, and the radius set. Values transcribed from
  "ScrobbleScope UI Audit v3" section "A starter palette and type
  system you can ship today" (2026-07-28 fetch).
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 can now be executed by any agent from the
  definition alone; compiled CSS remains the WP-1 deliverable.

### 2026-07-31 - Owner-preferences commit-rule dedup (side-task)

- Scope: final SSOT sweep found AGENT_NOTES.md Owner Preferences still
  restating three commit-mechanics rules AGENTS.md now owns
  (incremental staging, no co-author trailers, push/pause discipline).
- Plan vs implementation: the four bullets collapsed into one pointer at
  AGENTS.md Commit Rules; preference-only items (concise responses,
  Docker/MCP pause, explain-why, Firefox testing, principles, testing
  pyramid) stay -- they are owner context, not rules.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: hygiene plan complete (6 commits); Batch 21 WP-1 is
  next. SSOT sweep contract now holds: commit-rule keywords, venv rules,
  the heatmap perf figure, and batch state each have exactly one owner.

### 2026-07-31 - SWE-principles audit charter (side-task)

- Scope: charter the owner-requested audit of the ten mandated software
  principles so a dedicated single-purpose session (Claude or Codex) can
  execute it cold, without this session's context.
- Plan vs implementation: new `docs/SWE_AUDIT_CHARTER.md` front-loads
  all judgment -- Python-only scope (JS/templates excluded until
  Batch 21 ships them), a do-not-re-report differential baseline
  (F-MAS-*, F-B20-2, prior 2026-02 audits, standing design decisions),
  pre-identified hotspots (the three ~110-150 line functions and the 17
  `except Exception` sites), a 10-principle x module grading matrix
  with per-cell evidence, and a strict output contract (a dated
  SWE_PRINCIPLES_AUDIT report under the history archive plus net-new
  F-SWE-N findings only; read-only, no code changes). Tracked as
  F-SWE-1.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: execution is decoupled -- run whenever convenient
  (Codex costs no Claude tokens). Batch 21 WP-1 is unblocked and next.

### 2026-07-31 - MAX_ACTIVE_JOBS default 10 -> 5 (side-task)

- Scope: owner decision. The 2026-03-04 load test ran 2/3/5 concurrent
  users clean while the 10-user run never completed; all jobs share the
  global 10 req/s API throttle, so 10 slots starve each job below
  1 req/s on the single small Fly.io machine.
- Plan vs implementation: `scrobblescope/config.py` default changed to
  `"5"` with a rationale comment (still env-overridable); README (three
  mentions), SESSION_CONTEXT key-runtime-facts line, and FINDINGS
  F-LOAD-1 phrasing updated to match. `fly.toml` sets no
  `MAX_ACTIVE_JOBS` override, so the new default takes effect on next
  deploy.
- Deviations: pre-change scouting claimed no test depends on the
  default (capacity tests inject their own semaphores) -- true for
  assertions but not for shared state. Route tests that mock
  start_job_thread acquire a real slot that is never released, and the
  session's accumulated leaks crossed the new cap of 5, failing
  `test_heatmap_loading_json_body` with a real 429. Fixed properly: a
  new autouse `fresh_job_slots` fixture in `tests/conftest.py` resets
  the semaphore per test, removing the hidden inter-test ordering
  coupling the lower cap exposed.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner can observe the 5-slot cap locally; the
  "N/5 slots in use" occupancy hint remains open as F-LOAD-1.

### 2026-07-31 - FINDINGS refresh: batch-closure pointers, F-DOCSYNC-4, F-SWE-1 (side-task)

- Scope: owner-flagged staleness in FINDINGS.md -- open P1 items that
  Batch 21's definition already promises to close carried no pointer,
  and F-B20-4 paraphrased the whole definition.
- Plan vs implementation:
  - F-B20-3: remedy rewritten -- the 5.1->5.3 CDN-consolidation path is
    dead; Batch 21 resolves the split by eliminating Bootstrap (closes
    at WP-8). F-AUDIT-1: closes at Batch 21 WP-2 via acceptance
    criterion 8. F-B18-12 deferred-block line marked as in-batch scope
    (WP-6). F-B20-4 compressed to a pointer at `BATCH21_DEFINITION.md`.
    F-FEATURE-2 line reformatted as a greppable cross-ref bullet.
  - New F-DOCSYNC-4 (resolved): per-batch logs were undiscoverable until
    the Section 2 Log column landed; records the tombstone disposition.
  - New F-SWE-1 (open P1): SWE-principles audit chartered via
    `docs/SWE_AUDIT_CHARTER.md` (next commit), executable cold by a
    dedicated Claude or Codex session; closes by pointing at the report.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: F-LOAD-1's "N/10" phrasing updates with the
  MAX_ACTIVE_JOBS default change (next commit); charter follows.

### 2026-07-31 - PLAYBOOK Section 2 log column; tombstone disposition (side-task)

- Scope: the 18 per-batch logs under `docs/history/logs/` were referenced
  from no working doc (Section 2 had no Log column), making batch history
  discoverable only via a directory glob.
- Plan vs implementation: Section 2 table gained a Log column linking
  `BATCH3_LOG.md` through `BATCH20_LOG.md` (batches 0-2 predate per-batch
  logging); a note under the table points close-out-entry seekers at the
  monolith archive per F-DOCSYNC-3. AGENTS.md Batch Close-Out step 3 now
  requires filling the Log column at close-out so the column cannot go
  stale. Investigated the two 300-byte `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  files under `docs/history/` and `docs/history/logs/`: they are
  deliberate "Moved:" tombstones from the Batch 14 restructure kept for
  backward references -- retained, disposition recorded in F-DOCSYNC-4.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: hygiene commits 3-5 follow (FINDINGS refresh,
  MAX_ACTIVE_JOBS 5, SWE audit charter).

### 2026-07-31 - Bootstrap-doc SSOT pass: single-source rules and state (side-task)

- Scope: owner-requested hygiene sweep before Batch 21 WP-1. Exploration
  confirmed AGENTS.md and HANDOFF_PROMPT.md contradicted each other
  (bootstrap order, sufficiency gate, pre-commit gate, ownership map),
  commit discipline existed in 3-4 copies, the heatmap perf measurement
  in 4 copies, and AGENT_NOTES.md carried live batch state under a
  shipped-feature heading plus Batch 19 residue and a pointer to a
  non-repo file.
- Plan vs implementation:
  - AGENTS.md is now the single owner of rules: canonical 7-step
    bootstrap order (AGENTS.md itself is step 1), the stricter 3-way
    sufficiency gate, a 6-step pre-commit procedure including the
    doc_state_sync --check gate, the conflict-resolution rule, and four
    new anti-patterns (never --no-verify; stale Section 3; missing log
    entries; stale dashboard figures -- the ~72% coverage figure
    survived five months while reality was 89%). Docstring mandate moved
    into Proposal and Design Rules.
  - HANDOFF_PROMPT.md reduced to what it uniquely owns: post-read
    verification (git status/log + pytest count reconciliation) and the
    end-of-session handoff checklist; all rule sections now link to
    AGENTS.md instead of restating.
  - AGENT_NOTES.md: batch state moved out (PLAYBOOK Section 3 declared
    the single source); Heatmap section retitled shipped and trimmed of
    Batch 19 residue; venv rules and runtime constants replaced with
    links to their owners; load-test pointer now inlines the conclusion
    (2/3/5 clean, 10 never completed) and flags the raw data as
    agent-side; Talisman note repointed to the archived Batch 17 log;
    orchestrator-split note repointed to F-B20-2; the ten software
    principles expanded from bare acronyms.
  - SESSION_CONTEXT: Section 3 now lists all 7 CSS / 7 JS files and the
    template set (Batch 21 touches exactly these); heatmap perf trimmed
    to an F-B18-11 pointer here and in PLAYBOOK Section 3 -- F-B18-11 is
    the only full copy of the measurement.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: commits 2-5 of the approved hygiene plan follow
  (PLAYBOOK log column, FINDINGS refresh, MAX_ACTIVE_JOBS 5, SWE audit
  charter); then Batch 21 WP-1.

### 2026-07-29 - PR #164 phantom cleanup + review response (side-task)

- Scope: PR #163 was rebase-merged, leaving `wip/batch-21` "8 ahead /
  8 behind" (identical content, different SHAs -- normal rebase-merge
  artifact). The owner opened PR #164 from the stale branch; Copilot
  re-reviewed the phantom diff and left three NEW valid comments that
  four prior rounds missed. PR #164 closed with explanation; branch
  force-pushed to match `main`; all three fixes applied here.
- Plan vs implementation:
  - WP-4: leaving the loading page is now a plain "Back home" link with
    no `/reset_progress` call -- the endpoint clears stored job state
    only (`routes.py:227-238`); the daemon worker keeps its slot and
    rewrites the job afterward, so a "Cancel" label would be misleading
    and the reset racy.
  - WP-1: digest verification extended to cached artifacts (verify on
    every use, refetch once on mismatch, fail closed) -- gitignored
    `scripts/bin/` persists between runs, so download-time-only checks
    leave a bypass.
  - AGENTS.md: rotation note qualified -- bottom-appended entries are
    archived on the next `--fix` only once the non-current window is at
    capacity; placement rule unchanged.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 next on the realigned branch; open a fresh PR
  for the next review cycle when WP work lands.

### 2026-07-29 - PR #163 review response, round 4 (side-task)

- Scope: Copilot round 4 -- one suppressed comment. Verified valid and
  acted on.
- Plan vs implementation: the archived coverage-refresh entry cited
  "the CLAUDE.md canonical command", but CLAUDE.md is gitignored
  (`.gitignore:49`) and repo-invisible; the command is documented at
  README.md "Running Tests". Reference corrected in the monolith
  archive entry.
- Deviations: none. Distinction from the PR #162 round-3 decline on
  editing rotated entries: that citation was accurate at write time and
  went stale (point-in-time record, left alone); this one was
  repo-invisible at write time -- a sourcing error that defeats the
  record's verifiability, so it is corrected rather than preserved.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds have reached citation polish;
  recommend merging or pausing auto-review re-requests. WP-1 next.

### 2026-07-28 - PR #163 review response, round 3 (side-task)

- Scope: Copilot round 3 -- three suppressed low-confidence comments.
  Two acted on, one deferred to FINDINGS with a decline on the PR.
- Plan vs implementation:
  - Acted: `global.css` joins the WP-2 legacy per-page stack -- verified
    it carries Bootstrap-coupled `.card`/`.card-body`/`.modal-*` rules
    (`global.css:141-199`) that would restyle daisyUI components if it
    stayed in `base.html`; token/wordmark/shell concerns redistributed
    (daisyUI themes + `shell.css`).
  - Acted: WP-8 drift hook diff scoped with a pathspec
    (`git diff --exit-code -- static/css/tailwind.css`) so unrelated
    dirty files or rewrites from earlier hooks in the same run cannot
    produce false drift failures.
  - Deferred: retagging the Batch 20 close-out entry in the monolith
    archive. The routing claim is correct, but it is consistent tool
    behavior (`(Batch N close-out)` is not parser-recognized;
    BATCH19_LOG.md lacks its close-out too), and hand-editing
    machine-rotated archive content in a docs PR was declined and
    accepted in PR #162 round 3. Logged as F-DOCSYNC-3 (open P2) for a
    docsync WP alongside F-DOCSYNC-1/2.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 remains next; batched reply posted on PR #163.

### 2026-07-28 - PR #163 review response, round 2 (side-task)

- Scope: Copilot round 2 -- no new top-level comments, four suppressed
  low-confidence comments. All four verified valid (same pattern as
  PR #162: the suppression filter is too conservative); all acted on.
- Plan vs implementation:
  - Stale bootstrap docs: AGENT_NOTES.md still called Batch 21 a TBD
    stub with "no WP work until scope lands"; FINDINGS.md header said
    scope pending; README roadmap listed scoping as open. All three now
    reflect the active batch (the definition's own Status line already
    carried Active from WP-0).
  - Compiled-CSS drift window: validation gate now requires any WP
    touching templates or `tailwind.src.css` (WP-2..WP-7) to rebuild
    and commit `tailwind.css` in the same commit; the drift hook
    deliberately stays in WP-8 (moving it to WP-1 would front-load the
    headless-CI fetch problem before any template exists to protect).
  - Stack-restriction conflict: `toast` + `alert` added to the
    permitted daisyUI set for the WP-5 toast rewrite.
  - `--bars-color` inventory corrected: six of seven page CSS files
    (`unmatched.css` hardcodes its own `--header-bg`), pinwheel via
    `var()`; the wordmark hardcodes `#6a4baf` and only the dark-mode
    override (`global.css:49-50`) uses the variable, so light-mode
    wordmark recoloring is explicit migration work.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 remains next; batched reply posted on PR #163.

### 2026-07-28 - PR #163 review response (side-task)

- Scope: address the Copilot auto-review on PR #163 (Batch 21 open +
  doc refreshes). Five inline comments, all on `BATCH21_DEFINITION.md`;
  all five verified valid against the code and acted on.
- Plan vs implementation:
  - WP-1: per-platform SHA-256 digests committed alongside pinned
    versions; `tailwind_build.py` must verify every downloaded artifact
    before executing it (pin-only trusts the release asset at fetch
    time, and the WP-8 CI hook executes that binary headless).
  - WP-1: daisyUI standalone needs both `daisyui.mjs` and
    `daisyui-theme.mjs`; the component bundle alone cannot register the
    two custom `@plugin` themes.
  - WP-2: explicit coexistence isolation -- one framework stylesheet
    per template via the per-page block, shared shell styled by a
    framework-neutral `shell.css` absorbed at WP-8. Rejected daisyUI
    prefix alternative (WP-8 removal churn) with reasoning recorded.
  - WP-5: dropped "CSV walker untouched" -- `results.js` exports
    rendered cell text, so `MMM YY` display dates would truncate CSV
    release dates; date cells keep ISO in `data-export`, walker
    prefers it.
  - WP-7 + acceptance criterion 6: `below_min_plays`/`below_min_tracks`
    removed from the reason-code set -- `fetch_top_albums_async` drops
    threshold failures before the pipeline (`orchestrator.py:112-116`),
    and near-miss retention is explicitly Batch 22+. Two reason cards,
    not three; out-of-scope entry cross-references the deferred codes.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 implementation must honor the amended digest
  and dual-plugin-file requirements; batched reply posted on PR #163.

### 2026-07-28 - Side-task entry placement rule in AGENTS.md (side-task)

- Scope: document the doc_state_sync rotation gotcha discovered during
  the coverage-figure refresh so any agent places side-task entries
  correctly on the first try.
- Plan vs implementation: AGENTS.md Side-Task Handling step 2 now
  states that new entries must be inserted directly after the
  CURRENT-BATCH-END marker (top of the non-current list). The list is
  ordered newest-first; rotation keeps the first `--keep-non-current`
  entries positionally and rotates the rest, so a bottom-appended entry
  is treated as oldest and archived by the next `--fix` run instead of
  staying in the active window.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: next work remains Batch 21 WP-1 (Tailwind + daisyUI
  toolchain).

### 2026-07-28 - Coverage figure refresh in SESSION_CONTEXT (side-task)

- Scope: replace the stale coverage figure in SESSION_CONTEXT Section 1.
  The row still carried ~72% from the 2026-02-20 audit run; coverage has
  not been re-measured in a canonical doc since.
- Plan vs implementation: ran the canonical coverage command documented
  in README.md "Running Tests"
  (`pytest --cov=scrobblescope --cov-report=term`) on `wip/batch-21`
  (equal to `main` + WP-0, which touched no Python). Result: 89% total
  (1260 stmts, 134 miss). Lowest modules: `lastfm.py` 77%, `utils.py`
  81%, `orchestrator.py` 85%; four modules at 100%. Updated the
  Section 1 Coverage row with the new figure, measurement date, and
  scope (`--cov=scrobblescope`).
- Deviations: none. The owner's `main` checkout keeps the old figure
  until this branch merges; no fix applied there by design.
- Addendum (same day, owner-requested): the README tech-stack Testing
  row also said ~72%; updated to 89% in a follow-up commit.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: next work remains Batch 21 WP-1 (Tailwind + daisyUI
  toolchain). Re-measure coverage at future batch close-outs so the
  Section 1 row does not go stale again.

### 2026-07-24 - Batch 20 complete; definition archived, log purged (Batch 20 close-out)

- Scope: Batch 20 WP-8 close-out per the AGENTS.md procedure.
- Plan vs implementation:
  - `doc_state_sync.py --fix --keep-non-current 0` purged the 4 rotated
    non-current side-task entries into the monolith archive.
  - `git mv BATCH20_DEFINITION.md docs/history/definitions/` and marked
    the archived definition header Complete.
  - PLAYBOOK Section 2: Batch 20 row now links to the archived
    definition. Section 3: Batch 20 marked complete; Batch 21 (UI
    overhaul) flagged as next, awaiting the owner's in-progress UI
    proposal.
  - `.claude/SESSION_CONTEXT.md` Section 1: Batch 20 row set to
    Complete (all 9 WPs); Batch 21 row set to next-batch status. The
    "22 test modules" wording was already correct from earlier WPs.
- Deviations: none. Batch ran WP-0..WP-5 via Copilot PRs (#153/#155/
  #156/#159), then a post-merge audit follow-up commit plus WP-6, WP-7,
  and this close-out on `wip/batch-20` in a worktree.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with only the
  expected `BATCH21_DEFINITION.md` root warning remaining.
- Forward guidance: next batch is Batch 21 (UI overhaul); expand
  `BATCH21_DEFINITION.md` into WPs once the owner's proposal lands.
  `wip/batch-20` holds four unpushed commits awaiting owner review and
  push/PR instruction.

### 2026-07-24 - PR #162 review response (side-task)

- Scope: address the Copilot review on PR #162 (Batch 20 completion).
  All six comments (four inline + two suppressed low-confidence) were
  valid doc-consistency catches; five acted on fully, one partially.
- Plan vs implementation:
  - `FINDINGS.md`: header status updated to Batch 20 complete / Batch 21
    next; `Source:` added to F-B20-4 and F-B18-11; `Status:` lines added
    to all P2, Info, and feature items; shipped F-FEATURE-2 rotated to
    the archive with a cross-reference note.
  - `AGENTS.md` Finding-Writing Rules: rotation rule clarified --
    standing design-decision Info items (F-LOAD-3..5) keep their F-IDs
    in the active file and rotate only when superseded. This is the
    partial decline: archiving them would contradict the Batch 20
    definition's WP-6 intent.
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: header claim narrowed
    to ID/history preservation (bodies may be condensed at rotation).
  - `PLAYBOOK.md` Section 3: "unpushed pending owner instruction"
    replaced with "submitted as PR #162" (the Section 4 close-out entry
    keeps the original wording as a point-in-time record).
  - `AGENT_NOTES.md`: stale "Batch 20 is now active" block updated to
    complete/archived status with Batch 21 next.
  - `BATCH21_DEFINITION.md`: baseline refreshed 389 -> 390.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: batched reply posted on PR #162; awaiting merge.
  Batch 21 scope expansion remains next once the owner's UI proposal
  lands.

### 2026-07-24 - PR #162 review response, round 2 (side-task)

- Scope: address Copilot's second review round on PR #162 (four inline
  comments + one suppressed). All five verified valid; all acted on.
- Plan vs implementation:
  - `FINDINGS.md` F-MAS-4: `except Exception` count updated 14 -> 17
    (verified by grep; Copilot's per-file breakdown was exact) with the
    recount date noted.
  - `FINDINGS.md` deferred-block pointer corrected: detailed bodies live
    in pre-Batch-20 FINDINGS.md via git history (before `494f2c7`), not
    under `docs/history/` as previously claimed.
  - `FINDINGS.md` F-FEATURE-2 cross-reference recast as a direct
    sentence (grammar).
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: F-FEATURE-2 heading
    suffix normalized to `-- RESOLVED (shipped in Batches 18/19)` per
    the AGENTS.md suffix rule.
  - Archived `BATCH20_DEFINITION.md` header relabeled `Baseline:` ->
    `Final count:` so it no longer conflicts with the definition's
    unchanged 389-baseline plan text.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: PR #162 ready for merge; Batch 21 definition draft
  sits uncommitted in the worktree awaiting owner approval.

### 2026-07-24 - PR #162 review response, round 3 (side-task)

- Scope: Copilot round 3 (two comments + one suppressed duplicate).
  One acted on, one declined.
- Plan vs implementation:
  - Acted: both F-B19-6 archive headings moved their portion qualifier
    after the colon to match the `F-<context>-<N>: <title>` format the
    batch itself established (AGENTS.md Finding-Writing Rules).
  - Declined: updating the `BATCH20_DEFINITION.md:107-108` citation
    inside the archived `docs/history/logs/BATCH20_LOG.md` WP-3 entry.
    Rotated log entries are point-in-time records (same principle as
    the round-1 "unpushed" decline, which the reviewer accepted), they
    are machine-rotated content the docsync tooling owns, and the
    filename remains uniquely greppable at its archived location.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds are now in pure-style territory;
  recommend merging PR #162.

### 2026-07-24 - PR #162 review response, round 4 (side-task)

- Scope: Copilot round 4 -- one comment on PLAYBOOK Section 3 batch-state
  wording. Acted on, with a corrected mechanism note.
- Plan vs implementation:
  - Section 3 now uses the parser-recognized marker "Batch 21 is not yet
    defined"; the Section 3 parse verifiably returns the between-batches
    state with that wording in place.
  - Verified the comment's mechanism was doubly off: `BATCH_NEXT_RE`
    does not match "Batch 21 is next" (the attribution came from the
    `last_completed + 1` fallback at `parser.py:198-199`), and the
    wording fix alone cannot change the rendered STATUS -- with the
    close-out entry still inside the CURRENT-BATCH markers,
    `renderer.py:85-86` applies its own `last_completed + 1` fallback.
    Batch 19 precedent shows this is transient: its identically-tagged
    close-out entry rotated out automatically when Batch 20 WP-0 landed,
    and the same will happen at Batch 21 WP-0.
  - Logged the renderer gap as F-DOCSYNC-2 (open P2) rather than
    hand-moving machine-managed marker content or patching docsync code
    inside a docs-only PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner is merging PR #162; Batch 21 opens next.

### 2026-07-24 - Post-merge audit gap fixes (Batch 20 audit follow-up)

- Scope: close gaps found by the owner-requested audit of PR #159 (WP-1
  through WP-5 were executed via Copilot + PR reviews; audit compared the
  merged result against `BATCH20_DEFINITION.md` acceptance criteria).
  Work continues in a `wip/batch-20` worktree off `main` for isolation.
- Plan vs implementation:
  - `README.md`: deleted the "Doc-State Sync Tooling" bullet from Key
    Implementation Highlights (WP-1 acceptance item; the WP-1 log entry
    claimed removal but no commit ever removed it). Fixed the Project
    Structure tree so the agent-docs cluster is a comment row instead of
    a fake directory nesting five root-level files, and moved `AGENTS.md`
    and `PLAYBOOK.md` into that cluster. Added the missing prose note that
    `BATCHN_DEFINITION.md` sits at the root only while a batch is active.
  - `DEVELOPMENT.md`: corrected the `scrobblescope-bootstrap` description
    to the skill's actual read order (AGENTS.md -> PLAYBOOK 3-4 -> active
    batch definition -> SESSION_CONTEXT 1-2 -> AGENT_NOTES, then git/test
    verification) replacing the inaccurate SESSION_CONTEXT-first
    early-stop description.
  - `BATCH20_DEFINITION.md` header: refreshed stale status ("awaiting
    owner audit"), branch, and 389 baseline (390 since the WP-5 deviation).
  - `PLAYBOOK.md` Section 3 + `.claude/SESSION_CONTEXT.md` Section 1:
    branch updated from merged `file-hygeine` to `wip/batch-20`.
- Deviations: Getting Started length (WP-3 target ~95-100 lines, actual
  155 after review iterations added a full `docker run` block and 3-OS
  schema-init instructions) left as-is pending owner decision:
  re-compress vs accept the expanded setup detail.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-6 (FINDINGS.md cleanup and archive) is next.

### 2026-07-24 - README CSRF and UX cleanup (side-task)

- Scope: PR-review-comment-driven fixes to `README.md` and `AGENTS.md`.
- Plan vs implementation:
  - `README.md`: updated CSRF description to document three distinct injection
    mechanisms -- form-submit body token (`/results_loading`, `/results_complete`,
    `/unmatched_view`), header-only fetch (`/reset_progress`), and both body and
    header (`/heatmap_loading`). Added `/unmatched_view` to the form-submit route
    list after reviewer confirmed the hidden `csrf_token` input at
    `templates/results.html:177-178`.
  - `README.md`: removed three duplicate UX entries from the Styling & UX details
    block (rotating messages, personalized stats, onboarding) that were already
    covered in the Features section above.
  - `AGENTS.md`: removed a non-ASCII section symbol (replaced with plain text
    "Section") to comply with the ASCII-only markdown authoring rule.
- Deviations: none -- all changes are documentation-only PR review responses
  outside Batch 20 WPs; Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --check` -- exit 0.
- Forward guidance: Batch 20 WP-6 (FINDINGS.md cleanup) is still the next
  work package.

### 2026-07-24 - DEVELOPMENT.md file-count follow-up

- Scope: side-task follow-up to close the missed Batch 20 WP-5 documentation
  requirement in `DEVELOPMENT.md` by acknowledging `FINDINGS.md` as the sixth
  advisory, read-on-demand file in the external-memory description.
- Plan vs implementation:
  - Reworded the file-count paragraph to distinguish the five core tracked
    files from advisory `FINDINGS.md`, while keeping the archive-directory
    count unchanged.
  - Kept the wording explicit so IDE-based agents (for example Claude Code
    and Codex in VS Code) do not misread `FINDINGS.md` as part of the
    mandatory bootstrap set.
- Deviations: none -- this closes a missed WP-5 acceptance item flagged in PR
  review and leaves Batch 20 WP-6 as the next unstarted work package.
- Validation: `.venv/bin/pytest -q` -- **390 passed**. `.venv/bin/pre-commit
  run --all-files` -- all hooks pass. `.venv/bin/python scripts/doc_state_sync.py
  --check` -- exit 0 with the two expected root-BATCH warnings.
- Forward guidance: WP-6 still cleans up and archives `FINDINGS.md`.

### 2026-07-24 - Restore out-of-scope README edits (side-task)

- Scope: revert the Features-section rewrite and the Acknowledgements removal
  made in PR #159 outside Batch 20 WP-1 through WP-3; keep Screenshots removal
  as intentional.
- Plan vs implementation:
  - `README.md`: restored the original flat-list Features section (removed the
    "As mentioned above" intro and the `<details>` wrapper added out-of-scope).
  - `README.md`: restored the Acknowledgements section before Author & Contact.
  - `README.md`: updated Table of Contents to re-include only the
    Acknowledgements link.
- Deviations: none -- pure restoration of pre-PR content flagged by code review
  at PR #159 discussion_r3644787390.
- Validation: `pre-commit run --all-files` -- pass. `pytest -q` -- not
  applicable (documentation-only change). `python scripts/doc_state_sync.py
  --check` -- pass.
- Forward guidance: Features and Acknowledgements now match the intended PR
  state, with Screenshots intentionally removed; any future changes to those
  sections require an explicit batch WP or deviation log entry.

### 2026-07-24 - Copilot comment-job bootstrap trim (side-task)

- Scope: reduce unnecessary bootstrap for Copilot PR comment/review-comment
  jobs after the `copilot` Actions run failed in request processing with a
  monthly-quota error before reaching the linked review thread.
- Plan vs implementation:
  - `AGENTS.md`: added a targeted review-comment fast-path for prompts that
    link to a single `discussion_r...` thread, limiting reads to the linked
    file/lines plus only the bootstrap context that thread actually needs.
  - `HANDOFF_PROMPT.md`: removed the unconditional "read all bootstrap
    files" mandate for comment jobs and aligned the startup procedure with
    the lighter fast-path in `AGENTS.md`.
- Deviations: none -- this is a side-task CI reliability fix outside Batch 20;
  Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --fix` -- no changes.
  `python scripts/doc_state_sync.py --check` -- pass, with the two expected
  active-root-BATCH warnings. `pytest -q` and `pre-commit run --all-files`
  could not run in this sandbox because the repo-local `.venv` and those
  executables are not present here.
- Forward guidance: if future comment jobs still hit quota, inspect whether
  the prompt is fetching full PR comment lists when a direct review-comment
  URL is already supplied.

### 2026-07-22 - Link-preview image + Open Graph meta tags (side-task)

- Scope: LinkedIn (and Slack/Discord/etc.) show no image when the app URL
  is shared, since no og:image or companion meta tags existed.
- Plan vs implementation:
  - New `static/images/social-card.png` (1200x630, standard OG/Twitter
    card size): dark gradient background, the real favicon.svg pinwheel
    mark, wordmark, and tagline. Generated by rendering an HTML page that
    embeds the actual favicon.svg markup (not a hand-approximated
    redraw) and screenshotting it at 2x via the Chrome DevTools Protocol
    browser tool, then downsampled with Pillow (already pinned in
    requirements.txt; no new dependency).
  - `templates/base.html`: added `og:type`, `og:site_name`, `og:title`,
    `og:description`, `og:image` (+width/height), `og:url`, and the
    `twitter:card`/`title`/`description`/`image` equivalents. Title and
    description are Jinja blocks (`og_title`, `og_description`) so child
    templates can override per-page; default to the existing site title
    and meta-description text. `og:image` uses
    `url_for(..., _external=True)` so it resolves to an absolute URL
    against whatever host serves the request (required -- OG scrapers
    reject relative image URLs).
- Deviations: none. Out of scope for the active Batch 20 (file-hygiene,
  no production-code changes per `BATCH20_DEFINITION.md`), so logged as
  a side-task per `AGENTS.md` Side-Task Handling rather than a Batch 20 WP.
- Validation: `pytest -q` -- **389 passed**, no change (docs/template/asset
  only, no Python logic touched). `pre-commit run --files templates/base.html
  static/images/social-card.png` -- doc-state-sync-check passed (only
  applicable hook). Verified rendered output via Flask test client: all
  12 meta tags present, `og:image` resolves to an absolute URL.
- Forward guidance: none pending. Owner should verify the card renders
  correctly on LinkedIn's actual link-preview (some platforms cache
  previews aggressively per-URL; may need LinkedIn's Post Inspector to
  force a re-scrape after first deploy).

### 2026-05-19 - Batch 19 close-out (Batch 19 close-out)

- Scope: archived the Batch 19 definition, refreshed README for the PR to
  main, and finalized PLAYBOOK + SESSION_CONTEXT to reflect Batch 19 complete.
- Plan vs implementation:
  - `git mv BATCH19_DEFINITION.md docs/history/definitions/BATCH19_DEFINITION.md`.
  - PLAYBOOK Section 2 table now links to the archived definition.
  - PLAYBOOK Section 3 marks Batch 19 complete; next action is the
    `feat/heatmap` PR to `main`.
  - SESSION_CONTEXT Batch 19 row flipped to **Complete**.
  - README bumped to 387 tests, "Top Albums" mode rename in the intro,
    framed heatmap result + KPIs + desktop calendar vs. mobile activity
    strip described, `.venv/` venv guidance aligned with AGENTS.md, and
    heatmap roadmap line updated to cover both Batch 18 and Batch 19.
- Deviations: owner kept screenshots as "coming soon" placeholders since
  the saved ones in `docs/images/` no longer reflect the current UI.
  Owner will refresh them out of band.
- Validation: `pytest -q` passed with **387 passed** and 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` passed all 10
  hooks. `python scripts/doc_state_sync.py --check` exited 0 with the
  expected root warning gone after archiving the definition.
- Forward guidance: open the PR for `feat/heatmap` -> `main`, address any
  reviewer comments, merge, and deploy. Batch 20 (heavy UI refactor) is
  to be scoped later and is explicitly out of this PR.

### 2026-05-19 - PR #152 Gemini Code Review fixes (side-task)

- Scope: addressed three substantive Gemini Code Review comments on the
  open `feat/heatmap` PR.  Deferred three "broad except Exception"
  comments to the future error-handling batch (already tracked as
  FINDINGS.md P1 item 9).
- Plan vs implementation:
  - **Commit `ccb000f`** -- `fix(heatmap): use UTC for scrobble
    timestamps and fetch window`. Brought `heatmap.py` in line with
    `lastfm.py:31`'s established UTC convention. Updated every UTS-
    building call site in `tests/test_heatmap.py` to `tzinfo=timezone.utc`
    so the boundary tests are not vacuous against tz bugs. Added a new
    adversarial test (`test_utc_decode_invariant_against_local_tz_drift`)
    that pins a UTS at 23:30 UTC and asserts the bucket lands on the UTC
    day, not the local-tz day.
  - **Commit `01a7904`** -- `fix(repositories): isolate nested
    daily_counts in get_job_context`. Explicit
    `dict(results["daily_counts"])` after the outer shallow copy.
    Chosen over `copy.deepcopy` for the polling hot path. Closes
    F-B18-8. New regression test in `test_repositories.py`.
  - **Commit `53919c2`** -- `fix(heatmap): keep streak alive when today
    has no scrobble yet`. Stepping back one day when today is zero
    matches GitHub-contributions/Duolingo convention and was the
    pattern Gemini suggested.
  - FINDINGS.md gained F-B19-6 (naive-tz vacuous-test anti-pattern,
    forward-TODO for AGENTS.md update) and a resolved entry for F-B18-8.
- Deviations: declined Gemini's three "narrow the bare
  `except Exception`" comments. Those are all instances of FINDINGS.md
  P1 item 9 (14 sites total); narrowing 3 of 14 piecemeal without a
  test matrix per error class is a regression risk that violates
  AGENTS.md scope discipline. Belongs in the dedicated error-handling
  batch the FINDINGS entry already calls for.
- Validation: `pytest -q` passes with **389 passed** and 3 existing
  aiohttp/Python 3.13 warnings (387 -> 389; +1 UTC adversarial test,
  +1 nested-copy regression test). `pre-commit run --all-files` passes
  all 10 hooks. `node --check static/js/heatmap.js` clean.
- Forward guidance: push the three fix commits + this log entry,
  reply to Gemini via `gh pr review` declining the broad-Exception
  comments with a FINDINGS-item-9 pointer, and wait for re-review.

### 2026-05-16 - Remove dependabot.yml (side-task)

- Removed `.github/dependabot.yml`: all packages are pinned with `==` so
  dependabot can only open PRs that break the pinning policy. Pure noise for
  this project. No functional change.
- **385 tests passing**, all hooks green.

### 2026-05-16 - README update: heatmap feature + stale data

- Added heatmap feature description to intro paragraph (was album-only).
- Added Scrobble Heatmap bullet to Features section (grid, palette, tooltips,
  dark mode, responsive, pinwheel spinner).
- Updated project structure: heatmap.py, heatmap.css, heatmap.js,
  scrobblescope_pinwheel.svg, test_heatmap.py all added; stale test counts
  corrected (test_repositories.py 18->19, test_routes.py 50->65).
- Updated tech stack table: test count 350/23 -> 385/24; APIs note that
  heatmap uses Last.fm only (no Spotify).
- Roadmap: checked off heatmap (Batch 18 Phase 1 complete, Phase 2 in progress);
  corrected "350 tests / 23 files" to "385 / 24".
- Test badge: 350 -> 385.

### 2026-03-05 - Post-Batch-17 doc staleness fix

- PLAYBOOK Section 3 still said "Batch 17 is active" and listed all WP
  statuses after the close-out commit (743f8ae). Updated to "Between batches"
  with heatmap feature noted as next action on branch `feat/heatmap`.
- SESSION_CONTEXT Section 1 branch updated from `wip/batch-17` to
  `feat/heatmap`; date bumped to 2026-03-05.
- STATUS block refreshed by `doc_state_sync --fix`.
- Batch 17 log entries remain inside CURRENT-BATCH markers per docsync
  design -- they will auto-rotate to `BATCH17_LOG.md` when the next batch
  is declared active in Section 3.
- **350 tests passing**, all hooks green.

### 2026-03-05 - side-task: PR review fixes (CI cache, DEVELOPMENT.md, README, doc tidiness, SDLC table)

- **`.github/workflows/test.yml`**: fixed `cache-dependency-path` from
  `requirements-dev.txt` to `requirements*.txt`. The dev file starts with
  `-r requirements.txt` but pip's cache key computation does not follow
  transitive includes; changes to `requirements.txt` alone would not
  invalidate the cache. Fix ensures both files are hashed for the key.
- **`DEVELOPMENT.md`**: corrected the SESSION_CONTEXT.md CI presence
  claim. Previous text said the file is "absent in GitHub Actions" --
  inaccurate since SESSION_CONTEXT.md is now committed and a standard
  `actions/checkout@v4` includes it. Updated to say "normally present;
  `_read_lines_optional()` is a fallback for edge cases (sparse checkout
  or custom workflow)."
- **`README.md`**: three stale items corrected from Batch 17 changes:
  (1) CI/CD table row updated -- standalone flake8 removed in WP-2; pip-audit
  added in WP-2; description now reads "Quality Gate (pre-commit, pytest +
  coverage gate, pip-audit)"; (2) Code Quality row: added
  check-merge-conflict and detect-private-key (added in WP-2 addendum);
  (3) Local Dev section: SESSION_CONTEXT.md Section 8 ref (broken after
  WP-4 renumbering + Docker setup moved to AGENT_NOTES.md) -> AGENT_NOTES.md.
- **`BATCH17_DEFINITION.md`**: removed duplicate `---` separator between
  "## 6. Deferred" and "## Supplementary Info" (double rule was redundant).
- **`PLAYBOOK.md` WP-4 note**: updated "Candidate for a future cleanup
  pass" -> "Subsequently fixed in a side-task (see logarchive)" so PR
  reviewers do not see the WP-4 note as an open item that is also fixed
  in the same PR diff.
- **`DEVELOPMENT.md` SDLC table**: CI gate row updated from stale
  "GitHub Actions: pre-commit + flake8 + pytest + coverage" to "Quality
  Gate (pre-commit, pytest + coverage gate, pip-audit)" to match the
  README change and the WP-2 workflow rename.
- **350 tests passing**, all hooks green.

### 2026-03-05 - side-task: doc accuracy fixes (AGENTS.md, HANDOFF_PROMPT.md)

- **AGENTS.md**: "these doc files" -> "the doc files listed below" (dangling pronoun
  with no referent; table follows the section break, not the sentence).
- **HANDOFF_PROMPT.md**: SESSION_CONTEXT step 4 now reads "Sections 3-5" instead of
  "Sections 3-4". Section 5 is the dedicated Architecture overview; "Sections 3-4"
  would have left agents one section short when looking for architecture detail.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: requirements pinning + venv/agent safety rules

- **Pin previously unpinned packages**: `asyncpg>=0.29.0` -> `==0.31.0` and
  `Flask-WTF>=1.2.0` -> `==1.2.2` in `requirements.txt`. All five packages in
  `requirements-dev.txt` pinned to exact installed versions (flake8==7.3.0,
  pre-commit==4.5.1, pytest==9.0.2, pytest-asyncio==1.3.0, pytest-cov==7.0.0).
  Eliminates version drift on venv reinstall.
- **Incident root cause (2026-03-04):** Prior agent session ran
  `source venv/Scripts/activate && pip install flask-talisman` targeting the
  wrong `venv/` directory instead of `.venv/`. The `.venv/` was subsequently
  found empty (likely drained by the same session); reinstall from requirements
  files brought packages back at new versions for previously unpinned entries.
  Multiple background `python app.py` processes were also started via Bash tool
  and not cleaned up, blocking the owner terminal. User touched zero code.
- **AGENTS.md updated**: Environment Setup section corrected (`venv/` -> `.venv/`,
  bare `pip` -> `.venv/Scripts/pip`, added pinning requirement). Anti-Pattern
  Registry entries 4 and 5 added (wrong venv / bare pip, background server
  processes).
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: gunicorn threading + dark mode browser preference

- **Gunicorn threading**: added `--threads 4` to Dockerfile CMD. Single sync worker
  was serializing all HTTP requests in production; threads allow concurrent request
  handling while keeping JOBS dict in shared process memory.
- **Dark mode fix**: `theme.js` now falls back to `window.matchMedia('(prefers-color-scheme: dark)')`
  when no localStorage preference is saved. First-visit users with browser dark mode
  enabled will see dark theme automatically. Explicit toggle still overrides.
- Load test findings (local, 1-5 concurrent users) documented in agent memory.
  Spotify cache TTL verified correct (ToS compliant). No upstream 429s at 2-5 users.

### 2026-03-04 - side-task: log rotation fix

- **Log rotation**: changed `RotatingFileHandler` to 2MB files / 10 backups (was 1MB / 5).
  Small files stay granular and parseable; 10 backups cover a full load test session.
  No production impact -- file is ephemeral on Fly.io; stdout is the prod log channel.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: PR code review fixes

- **theme.js**: `var` -> `const` for `saved` and `prefersDark` (neither reassigned;
  aligns with `const`/`let` convention in all other JS files).
- **Dockerfile**: added comment explaining `--workers 1 --threads 4` rationale for
  Fly.io deployment (shared-cpu-2x / 512MB, JOBS dict requires single process).
- **350 tests passing**, all hooks green.

### 2026-03-03 - Review-driven fixes: barrier safety, session cleanup, Docker error handling, dev_start tests

**Scope:** Side-task -- address Co-Pilot code review findings from PR #56, add
subprocess timeout guards, and add the deferred `dev_start.py` unit tests (now
warranted by increased error-handling complexity).

**Fixes applied:**
1. `concurrent_users_test.py` -- moved `barrier.wait()` inside `try` block so
   `BrokenBarrierError` is captured and a `ConcurrentResult` is always appended
   (docstring guarantee upheld).
2. `concurrent_users_test.py` -- track sessions in a list, call `session.close()`
   after `join()` to prevent connection/socket leaks.
3. `dev_start.py` -- `check_container_status()` now distinguishes "No such object"
   (returns `None`) from Docker daemon errors (raises `RuntimeError` with actionable
   message) and unexpected errors (raises with stderr details).
4. `dev_start.py` -- added `timeout=10` to `docker inspect` and `timeout=30` to
   `docker start` subprocess calls; catches `subprocess.TimeoutExpired` and raises
   `RuntimeError` with clear messaging.

**New tests:** 11 unit tests in `tests/scripts/dev/test_dev_start.py` covering
`check_container_status` (6 paths: running, absent, docker-not-found, timeout,
daemon-not-running, unexpected error), `start_container` (success, failure, timeout),
`main` (absent container exit, exited container start+exec).

**Validation:** `pytest -q` -- **350 passed**. `pre-commit run --all-files` -- all
hooks pass.

### 2026-03-03 - Fix Windows asyncpg startup packet (ProactorEventLoop) (side-task)

**Scope:** Side-task -- two-stage Windows-only cache fix. No code changes for
the Fly.io (Linux) deployment path.

**Errors encountered and resolved (session log):**

1. `.env` typo `DDATABASE_URL` (double-D prefix) -- cache silently disabled.
   Fixed by correcting the typo in `.env`.

2. `os.environ.get("DATABASE_URL")` returned `None` in background worker threads
   on Windows. Werkzeug debug reloader spawns a child process; `load_dotenv()`
   ran in the parent but environment variables were not reliably inherited.
   Fixed in `468b519`: capture `_DATABASE_URL = os.environ.get("DATABASE_URL")`
   at module import time in `cache.py` (runs once after `app.py` calls
   `load_dotenv()`). Also path-anchored `load_dotenv()` in `app.py` so it
   finds `.env` regardless of working directory.

3. `_DATABASE_URL` confirmed set (len=59) but asyncpg still failed silently.
   Docker logs revealed: `invalid length of startup packet` (10 rapid rejections
   -- matching 3 retries x multiple test runs). Root cause: `asyncio.new_event_loop()`
   in a daemon thread under Werkzeug's debug reloader on Windows creates a
   `SelectorEventLoop`, not a `ProactorEventLoop`. asyncpg uses Windows IOCP
   via `ProactorEventLoop`; with `SelectorEventLoop` it sends incorrect startup
   bytes and Postgres rejects the connection immediately.
   Fixed in `97db0c9`: `background_task()` in `orchestrator.py` now calls
   `asyncio.ProactorEventLoop()` when `sys.platform == "win32"`, falling back to
   `asyncio.new_event_loop()` on all other platforms (Linux/Fly.io unchanged).

4. `RotatingFileHandler` fails with `PermissionError: [WinError 32]` when
   multiple Flask processes hold the log file open simultaneously (Werkzeug
   debug reloader + interleaved restarts). Cosmetic only -- Flask continues to
   serve. Not fixed; documented here for future reference.

**Deploy safety:** Fix 3 uses `if sys.platform == "win32":` guard exclusively.
Fly.io (Linux) takes `asyncio.new_event_loop()` unchanged.

**Implementation:**
- `scrobblescope/orchestrator.py` -- `background_task()` updated (`97db0c9`)
- `scrobblescope/cache.py` -- `_DATABASE_URL` captured at module level (`468b519`)
- `app.py` -- path-anchored `load_dotenv()` (`468b519`)
- `tests/test_repositories.py` -- 4 tests updated to patch
  `scrobblescope.cache._DATABASE_URL` directly instead of `os.environ` (`468b519`)

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. Smoke test: `verdict=PASS`, `db_cache_lookup_hits=44`, elapsed ~1.05s
(vs ~6s cold Spotify fetch). Fly.io deploy path confirmed unaffected by guard.

**Forward guidance:** Cache subsystem is fully working locally. WP-2 is next:
13 unit tests for `_http_client` and `smoke_cache_check` in
`tests/test_smoke_cache_check.py`.

### 2026-03-03 - Improve agent orientation docs (side-task)

**Scope:** Side-task -- documentation only, no code changes. Improve agent
bootstrap reliability by fixing stale references and adding missing setup steps.

**Changes:**
- DEVELOPMENT.md: replaced stale "SESSION_CONTEXT is gitignored/ephemeral" text
  (lines 83-93) with accurate description of committed+tracked status, explicit
  `.gitignore` exception, and rationale for sharing across agents.
- AGENTS.md Environment Setup: added venv activation commands (Windows + Linux)
  so agents can run `pytest` and `pre-commit` without trial-and-error.
- AGENTS.md "What to update after a WP": added README deferral exception noting
  that README updates may be batched into a dedicated WP when the batch definition
  specifies one (e.g., Batch 16 WP-5).

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-1 is next. README will be stale during intermediate WPs;
updates deferred to WP-5 per batch definition.

### 2026-03-03 - Batch 16 definition written and activated (Batch 16 activation)

**Scope:** Define Batch 16 and activate it in PLAYBOOK + SESSION_CONTEXT.

**Plan:** Write `BATCH16_DEFINITION.md` incorporating audit corrections (stat key
fix, size caps removed, MEMORY.md references clarified as agent-private). Move to
`docs/history/definitions/`. Activate Batch 16 in PLAYBOOK Section 3. Update
SESSION_CONTEXT Section 2. Update HANDOFF_PROMPT.md and MEMORY.md for handoff.

**Implementation:** Definition written; audit findings applied (verdict key
`cache_hits` corrected to `db_cache_lookup_hits`, size caps removed per owner
instruction, `memory/MEMORY.md` removed from formal acceptance criteria). Definition
placed at `BATCH16_DEFINITION.md` (root; moves to archive at batch close-out). PLAYBOOK and
SESSION_CONTEXT activated. HANDOFF_PROMPT and MEMORY updated for clean handoff.

**Deviations:** None.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-0 is next: create `scripts/testing/` and `scripts/dev/`
directories, move `smoke_cache_check.py` via `git mv`, update AGENTS.md and
SESSION_CONTEXT path references. No logic changes in WP-0.

### 2026-03-03 - Fix SESSION_CONTEXT.md commit convention and stage accumulated changes

**Scope:** Side-task -- documentation and gitignore fix, no code changes.

**What:** SESSION_CONTEXT.md was never staged in the two previous side-task commits
(`c4bf737`, `4f1cf6a`) despite commit messages implying it. SESSION_CONTEXT.md has
been git-tracked since before `edee612` (when `.claude/` was added to .gitignore).
The `.gitignore` entry `.claude/` is misleading -- SESSION_CONTEXT.md is grandfathered
in as a tracked file. Fix: update `.gitignore` to `.claude/*` + `!.claude/SESSION_CONTEXT.md`
so the exception is explicit. Fix AGENTS.md: remove incorrect "SESSION_CONTEXT is
gitignored" language. Stage the accumulated SESSION_CONTEXT.md changes (Batch 15 state
update, Section 8 browser MCP note, Section 8 local Postgres note).

**Why:** SESSION_CONTEXT.md is the shared cross-agent dashboard. All agents (Gemini,
Copilot, Codex, Claude Code) bootstrap from it. Leaving it uncommitted means every agent
starts with stale branch, test count, and batch status. The gitignore fix makes the
tracked-exception visible and prevents future agents from falsely concluding the file
is machine-local.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. BATCH16_PROPOSAL.md written; awaiting owner review.

### 2026-03-03 - Add local DB setup and init_db.py caveat to env docs

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added local Postgres DB setup details and `init_db.py` load_dotenv caveat
to AGENTS.md Environment Setup and SESSION_CONTEXT Section 8. These facts apply to
all agents (Gemini CLI, Copilot, Codex, Claude Code) running local DB tests.

**Why:** `init_db.py` has no `load_dotenv()` call. Any agent running it will get
"DATABASE_URL not set" unless the env var is set directly in the shell. Absent from
canonical docs, every agent would hit this silently and assume cache is unavailable.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

### 2026-03-03 - Add browser MCP environment note to SESSION_CONTEXT

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added one line to SESSION_CONTEXT Section 8 (Environment notes) documenting
that the browser MCP accesses the local Flask app via `http://host.docker.internal:5000/`
rather than `localhost`, because the MCP browser runs inside a Docker container.

**Why:** This is a runtime fact that future agent sessions need to reproduce local
browser testing correctly. Absent from SESSION_CONTEXT, an agent would attempt
`localhost` and get a connection refused error with no clear diagnosis path.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

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

### 2026-02-27 - Migrate monolith archive path to docs/logarchive (side-task)

**Scope:** `scripts/docsync` path canonicalization, pointer compatibility docs,
doc references, regression validation.

**Plan vs implementation:**
- Planned: stop using the legacy history monolith paths
  (`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
  `docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`) as the
  canonical monolith location and move to a dedicated `docs/logarchive/`
  folder with clear pointers from legacy paths.
- Implemented: switched docsync `ARCHIVE_PATH` to
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, copied canonical
  archive content there, converted both legacy monolith files into pointer
  documents, and added `docs/logarchive/README.md` lookup guidance.

**Deviations:**
- Historical documents under `docs/history/definitions/` and batch logs were
  left unchanged to preserve historical wording; compatibility pointers prevent
  breakage for legacy references.

**Validation:**
- `python scripts/doc_state_sync.py --fix`
- `python scripts/doc_state_sync.py --check`
- `pytest -q tests/test_docsync_cli.py tests/test_docsync_logic.py`
  `tests/test_docsync_parser.py tests/test_docsync_renderer.py` (**103 passed**)
- `pytest -q` (**307 passed**, 3 deprecation warnings from aiohttp connector)

**Forward guidance:**
- Use `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for untagged archive
  search and keep per-batch logs under `docs/history/logs/` as the tagged route.

### 2026-02-27 - Branch hygiene cleanup after main diff review (side-task)

**Scope:** orchestration hygiene (`.gitignore`, PLAYBOOK state consistency,
root audit-file placement), docsync warning cleanup.

**Plan vs implementation:**
- Planned: remove non-actionable docsync warning noise and align tracked state
  with the "local-only" `.claude/SESSION_CONTEXT.md` policy.
- Implemented: scoped `BATCH*_AUDIT*.md` ignore rule to repo root only,
  moved `BATCH14_PROPOSAL_AUDIT1.md` from root into `docs/history/`, and
  recorded the side-task in Section 4.

**Deviations:**
- `git mv` could not be used for `BATCH14_PROPOSAL_AUDIT1.md` because the file
  was not under version control; file-system move was used instead.

**Validation:**
- Ran `python scripts/doc_state_sync.py --fix` and
  `python scripts/doc_state_sync.py --check` after edits.

**Forward guidance:**
- Keep root-only draft/audit patterns scoped with leading `/` in `.gitignore`
  so archive destinations under `docs/history/` remain trackable.

### 2026-02-26 - Remediate docsync audit findings (side-task)

**Scope:** `scripts/docsync/` (cli, parser, renderer, logic),
test suite (parser, renderer, logic), `AGENTS.md`.

**Changes:**
- Fixed unconditional PLAYBOOK/ARCHIVE writes in --fix mode (F1).
- Consolidated SyncError import to top-level in cli.py (F11).
- Defined TEST_COUNT_RE once in parser.py (F2).
- Extracted _dedup_sorted() helper in logic.py (F3).
- Tightened ENTRY_BATCH_RE to require (Batch N WP-X) format (F6).
- Added duplicate-marker detection in _find_marker_pair (F7).
- Added sentinel -1 comment (F5).
- Removed dead stale-phrase detection + 3 tests (F8).
- Fixed misleading docstring (9a), weak assertion (9b).
- Added 4 tests: duplicate headings (9c), adversarial regex (9d),
  duplicate markers (F7), file-order dependency (9e).

**Test count:** **307 passed** (net +1: -3 removed, +4 added).
**Validation:** `pytest -q` 307 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - Post-batch test suite audit (doc hygiene)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`tests/test_docsync_parser.py`; deleted `tests/test_docsync_models.py`.

**Changes:**
- Fixed `test_deduplication_across_archive`: was passing vacuously -- tagged
  entry routed to `batch_log_updates`, bypassing monolith dedup entirely;
  rewrite uses untagged entry and asserts `batch_log_updates == {}`.
- Dropped `test_current_entry_count_mismatch_warns`: near-duplicate of
  `test_mismatched_counts_warns` (identical `_cross_validate` code path).
- Rewrote `test_section4_historical_count_ignored`: old version had no
  CURRENT-BATCH markers so `_latest_test_count_from_entries` returned None
  vacuously; new version confirms below-end-marker counts are ignored while
  inside-marker count is used for comparison.
- Removed unused `LOGS_DIR` name import from `test_docsync_cli.py`.
- Merged 5 `_fingerprint`/`_extract_entry_batch` tests from misnamed
  `test_docsync_models.py` into `test_docsync_parser.py`; deleted old file.
- Added `TestSplitArchiveMode.test_split_archive_routes_tagged_entry` for
  the previously uncovered `--split-archive` CLI branch.

**Test count:** **306 passed** (net zero: -6 removed, +6 added).
**Validation:** `pytest -q` 306 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - fix(doc-sync): remediate SESSION_CONTEXT staleness in _cross_validate and _build_status_block (side-task)

- Scope: `scripts/docsync/logic.py`, `scripts/docsync/renderer.py`, `scripts/docsync/cli.py`,
  `tests/test_docsync_logic.py` (+6 tests: 4 TestLatestTestCount + 2 rewritten + 1 renamed),
  `tests/test_docsync_renderer.py` (+2 TestBuildStatusBlock count tests),
  `tests/test_docsync_cli.py` (1 test updated).
- Problem: Two root causes for SESSION_CONTEXT staleness: (1) `_cross_validate` scanned
  PLAYBOOK Section 3 for `**N passed**` counts, but agents write test counts in Section 4
  log entry Validation fields — Section 3 is narrative prose. `playbook_counts` was always
  empty so the mismatch warning never fired. (2) `_build_status_block` did not include the
  test count in the STATUS block output, forcing agents to check stale manual rows.
  Additionally, `_cross_validate` was called with `result.session_lines` (post-sync), which
  already had the correct count injected by `_build_status_block`, laundering mismatch away.
- Fix: Added `_latest_test_count_from_entries(playbook_lines)` to `logic.py` — parses
  Section 4 current-batch entries newest-first and returns the first `**N passed**` count.
  Updated `_cross_validate` to call this function (scalar comparison) instead of scanning
  Section 3. Added `_TEST_COUNT_RE` to `renderer.py`; `_build_status_block` now emits
  `"- Latest validated test count: **N passed**."` using the most-recent entry body count.
  Fixed `cli.py` to call `_cross_validate(playbook_lines, session_lines)` (original, pre-sync
  lines) so the STATUS block update cannot launder a pre-existing mismatch.
- Deviations: None. All changes additive; no logic in `_sync` was touched.
- Validation: **294 passed** (+6 vs WP-2 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - docs(audit): add BATCH14 pre-approval audit report and apply corrections to proposal (side-task)

- Scope: `BATCH14_PROPOSAL.md`, `docs/history/BATCH14_AUDIT_2026-02-25.md`.
- Purpose: Pre-batch audit of BATCH14_PROPOSAL.md before owner sign-off. Verified
  all five structural checks (WP-1 naming conventions, WP-2 package extraction
  symmetry, WP-3 feature isolation, WP-4 test distribution, WP-5 AGENTS.md
  close-out / MEMORY.md hallucination check). All five checks confirmed correct.
- Correction: "~450-line" description for `doc_state_sync.py` corrected to "~679-line"
  in two places (Current state table and WP-2 goal). Actual measured line count: 679.
- Verdict: APPROVED WITH CORRECTIONS.
- Validation: 288 passed (unchanged -- audit makes no code changes), all 8 pre-commit
  hooks passed.

### 2026-02-25 - test(worker): assert daemon=True via Thread patch, expand docstrings (side-task)

- Scope: `tests/test_worker.py`.
- Problem: `test_start_job_thread_creates_daemon_thread` only asserted the target
  was called; it never verified `threading.Thread` was constructed with `daemon=True`,
  despite the test name and docstring claiming otherwise. Tests 1–4 had minimal
  single-line docstrings inconsistent with the GIVEN/WHEN/THEN standard.
- Fix: Introduced `DummyThread` class, patched at `scrobblescope.worker.threading.Thread`;
  asserts `daemon=True` and target invocation. Dropped `*args` from `DummyThread.__init__`
  (Pylance hint; Thread is called with keyword args only). Expanded tests 1–4 docstrings
  to GIVEN/WHEN/THEN inline format.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - test(retry): use public semaphore API in semaphore-gates test (side-task)

- Scope: `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer flagged `sem._value == 0` as a private implementation detail
  of `asyncio.Semaphore`, suppressed with `# noqa: SLF001`, making the assertion
  brittle across Python versions.
- Fix: Replaced with `sem.locked()`, the public equivalent (stable since Python 3.4).
  Updated comment; noqa suppression removed. Confirmed only occurrence in suite.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - fix(utils): support constant backoff value in retry_with_semaphore (side-task)

- Scope: `scrobblescope/utils.py`, `scrobblescope/spotify.py`,
  `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer 1 flagged that `backoff` only accepted a callable, requiring
  `backoff=lambda _a: 1` for constant delays. Updating call sites to use a plain
  float was not possible without a utility change.
- Fix: Added `callable(backoff)` guard at line 341 of `utils.py`; updated docstring
  type annotation. Simplified `spotify.py` search call site to `backoff=1`. Added
  `test_constant_float_backoff_accepted` to `test_retry_with_semaphore.py`.
- Validation: 288 passed (+1 vs Batch 13 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - test(orchestrator): use standard asyncio import in fetch_spotify tests (side-task)

- Scope: `tests/services/test_orchestrator_fetch_spotify.py`.
- Problem: Reviewer 2 flagged two `__import__("asyncio").Semaphore(5)` usages
  bypassing Pylance type resolution; root cause was missing top-level `import asyncio`.
- Fix: Added `import asyncio` to stdlib imports block; replaced both
  `__import__("asyncio").Semaphore(5)` occurrences with `asyncio.Semaphore(5)`.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-24 - docs(audit): BATCH13 pre-approval audit report (side-task)

- Scope: `BATCH13_PROPOSAL.md`, `docs/history/BATCH13_AUDIT_2026-02-23.md`.
- Problem: BATCH13 proposal required independent technical verification before
  owner approval. Line references, test coverage claims, retry extraction
  design, and convention compliance needed validation against actual codebase.
- Fix: Completed 4-WP audit. Found 5 discrepancies: `_apply_pre_slice` line
  start off by 2 (L664 -> L666), `_JOB_SEMAPHORE` variable name incorrect
  (actual: `_active_jobs_semaphore`), batch retry missing jitter declaration,
  batch backoff incorrectly stated as fixed 1.0 (actual: `2**attempt`
  exponential). Applied all corrections to the proposal. Created audit report.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed. No source
  code changes -- audit only.

### 2026-02-23 - chore(merge): integrate main into wip/pc-snapshot (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py` (merge
  resolution only -- no net change from branch perspective).
- Problem: `main` had one commit ahead (`05c7b19`) that was already
  cherry-picked into `wip/pc-snapshot` as part of `4e4c9a1`. The branch
  needed to formally integrate `main` before PR #36 could merge cleanly.
- Fix: `git merge origin/main --no-edit`; ort strategy resolved cleanly
  (identical content on both sides for the two touched files). Merge commit
  `d98c90b` amended to conventional format.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-23 - fix/docs: cherry-pick SESSION_CONTEXT optional + DEVELOPMENT.md (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py`,
  `DEVELOPMENT.md`, `docs/history/SESSION_CONTEXT_REFERENCE.md`, `README.md`.
- Problem: (1) CI failed on `main` when `.claude/SESSION_CONTEXT.md` was
  absent (gitignored). The script called `_read_lines()` unconditionally,
  raising `SyncError`. (2) No documentation existed for the multi-agent
  orchestration methodology implemented during this sprint.
- Fix:
  (1) Cherry-picked commit `05c7b19` from `main`: added `_read_lines_optional()`
  returning `None` when the file is absent; gated all SESSION_CONTEXT
  operations in `_sync()`, `_cross_validate()`, and `main()` behind
  presence check; `SyncResult.session_lines` typed as `list[str] | None`;\
  renamed `test_missing_session_context_raises` to `_succeeds`; added
  `TestMissingSessionContext` class (3 regression tests).
  (2) Created `DEVELOPMENT.md` explaining the orchestration architecture,
  why `doc_state_sync.py` is a deterministic script, the batch/WP SDLC
  mapping, review-rejection rationale, and what failed before the current
  system stabilized. Created `docs/history/SESSION_CONTEXT_REFERENCE.md`
  as a tracked reference snapshot of the gitignored live file. Linked
  both from `README.md` (new "Development Methodology" section in ToC).
- Validation: **260 tests passing** (3 new from cherry-pick),
  pre-commit all 8 hooks passed.

### 2026-02-23 - chore/docs: repo hygiene and README rewrite (side-task)

- Scope: root directory, `.gitignore`, `README.md`, `.claude/`.
- Problem: (1) Root directory cluttered with completed batch definitions
  (`BATCH12_PROPOSAL.md`, `BATCH8_REFACTOR_PLAN.md`) and an obsolete
  playbook compatibility shim (`EXECUTION_PLAYBOOK_2026-02-11.md`).
  (2) `.claude/` tracked in git (agent-local state, stale `BATCH3_CONTEXT.md`,
  machine-specific `settings.local.json`). (3) `README.md` outdated --
  "work in progress" status badge, 30+ completed checkbox items, missing
  Architecture/Deployment sections, stale Tech Stack section.
- Fix:
  (1) `git mv` both batch definitions to `docs/history/`. `git rm`
  the playbook shim. Deleted untracked stale files (`backup.py`,
  `Backup_batch`, empty `app/` directory).
  (2) Added `.claude/` to `.gitignore`, `git rm --cached` all 3 tracked files,
  deleted stale `BATCH3_CONTEXT.md` locally.
  (3) Comprehensive README rewrite: active status badge + test count badge,
  new Architecture section with pipeline diagram + design decisions, Tech
  Stack table, Deployment section with Fly.io commands + smoke test,
  condensed Roadmap (upcoming + recent completions only), accurate Project
  Structure tree with per-file annotations and test counts, Running Tests
  section, trimmed Contributing/License/Acknowledgements.
- Validation: **257 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-22 - fix(app): guard sys.stderr.reconfigure with isinstance check

- Scope: `app.py`.
- Problem: Pyright/Pylance reported "Cannot access attribute reconfigure for
  class TextIO" because `sys.stderr` is typed as `TextIO`, which lacks
  `reconfigure`. The method exists at runtime on `io.TextIOWrapper`.
- Fix: Added `import io` and wrapped the call in
  `if isinstance(sys.stderr, io.TextIOWrapper):` -- a type-narrowing guard
  that satisfies both the type checker and runtime safety.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all hooks passed.

### 2026-02-22 - refactor(routes,lastfm): SoC/DRY cleanup from third-party audit

- Scope: `scrobblescope/routes.py`, `scrobblescope/lastfm.py`,
  `scrobblescope/orchestrator.py`, `tests/services/test_lastfm_logic.py`.
- Problem: Three findings from a third-party structural audit:
  (1) SoC -- `get_filter_description` was a public helper placed between HTTP
  handlers; lacked `_` prefix used by the other private helpers.
  (2) DRY -- `/results_complete` and `/unmatched_view` duplicated ~10 lines
  of identical `job_id`/`job_context` guard logic.
  (3) SoC -- `fetch_top_albums_async` in `lastfm.py` imported `set_job_stat`
  from `repositories.py` and made 5 direct job-state mutations. An API client
  module should return pure data, not mutate application state. `spotify.py`
  already follows this pattern correctly.
- Fix:
  (1) Renamed to `_get_filter_description` and hoisted above HTTP handlers,
  below `_group_unmatched_by_reason`.
  (2) Extracted `_get_validated_job_context(missing_id_message, expired_error,
  expired_message, expired_details)` returning `(job_id, job_context, None)`
  or `(None, None, error_response)`.
  (3) Removed `job_id` param and `set_job_stat` import from
  `fetch_top_albums_async`. Stats now returned in `fetch_metadata["stats"]`
  dict. `orchestrator._fetch_and_process` extracts and records them.
  Partial-data warning also moved to `fetch_metadata` return path.
- Deviations: Audit claimed ~15-20 lines of duplication; actual overlap was
  ~10 lines. Error titles intentionally differ between routes, so
  `expired_error` was parameterized rather than hardcoded.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-22 - fix(types): resolve 10 Pylance type errors in production code

- Scope: `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`,
  `scrobblescope/utils.py`.
- Problem: Pylance reported 10 type errors across 3 production files:
  (1) `lastfm.py` (7): `metadata` dict inferred as `dict[str, str | int]`
  caused arithmetic and nested-dict assignment failures; `albums` defaultdict
  inferred heterogeneous union on all value accesses.
  (2) `spotify.py` (2): `SPOTIFY_CLIENT_ID/SECRET` typed `str | None` from
  `os.getenv()` but `aiohttp.BasicAuth` requires `str`.
  (3) `utils.py` (1): `loop` assigned inside `try:` block, referenced in
  `finally:` -- possibly unbound if `new_event_loop()` raises.
- Fix: Annotated `metadata: dict[str, Any]` and
  `albums: defaultdict[str, dict[str, Any]]` in lastfm.py; added assert
  guards for Spotify credentials in spotify.py; initialized `loop = None`
  with `if loop is not None:` guard in utils.py.
- Test file type errors (25 across 3 files) assessed as low-impact
  mock-related noise -- deferred.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-21 - refactor/fix: Gemini audit remediation (non-normalization track)

- Scope: `scrobblescope/orchestrator.py`, `scrobblescope/cache.py`,
  `scrobblescope/routes.py`, `scrobblescope/domain.py`,
  new `scrobblescope/errors.py`, `scrobblescope/repositories.py`,
  `tests/services/test_orchestrator_service.py` (+4 tests),
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md` (new doc).
- Problem: A second Gemini Pro audit pass identified four issues beyond the previously
  fixed normalization bugs. Three were confirmed real against the live codebase:
  1. Late slicing: `limit_results` applied after Spotify calls in `_fetch_and_process`.
     For playcount sort the ranking is fully known from Last.fm data; pre-slicing
     to the requested limit eliminates unnecessary Spotify searches on cache misses.
     (Playtime sort cannot be pre-sliced -- ranking requires track duration data.)
  2. Indefinite DB growth: `_batch_lookup_metadata` filtered stale rows at read time
     but no DELETE ever ran. Stale rows accumulated in `spotify_cache` indefinitely.
  3. ERROR_CODES + SpotifyUnavailableError in `domain.py`: a SoC violation -- domain
     logic should not own user-facing message strings or retryability flags.
  A fourth SoC issue not in the original report was also fixed: duplicate release_scope
  -> human-text translation in `routes.py` (inline block in `unmatched_view`
  duplicating `get_filter_description`). A fifth issue (empty-result hallucination)
  was assessed and deferred as near-false-alarm -- the trigger conditions require
  zero cache hits AND every album absent from Spotify, which is extremely unlikely.
- Plan vs implementation: all four confirmed issues fixed as described in
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **114 passed** (110 pre-existing + 4 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - Import graph: `errors.py` is a leaf module (no package imports). Acyclic structure
    preserved. `domain.py` now contains only normalization logic.
- Forward guidance: next sub-track is "sycophantic test coverage" audit (owner to
  elaborate scope). Feature work (top songs, heatmap) blocked until owner assigns a
  future batch number and defines scope. `_cleanup_stale_metadata` is opportunistic and non-fatal;
  monitor logs for "Stale cache cleanup" entries to confirm it fires in production.
  The playtime late-slicing limitation is documented inline in `_fetch_and_process`.

### 2026-02-21 - fix(domain): fix normalization bugs silently excluding non-Latin albums

- Scope: `scrobblescope/domain.py`, `tests/test_domain.py` (9 new tests),
  `tests/services/test_lastfm_logic.py` (new file, 7 tests),
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md` (new doc).
- Problem: A third-party static analysis review (Gemini Pro) identified four
  defects in `domain.py` and a coverage gap in `lastfm.py`. All four were
  confirmed against the live codebase and three had measurable production impact:
  1. `normalize_track_name` used `NFKD + encode("ascii","ignore")`, stripping all
     non-Latin characters to `""`. Any album with Japanese/Cyrillic/etc. track names
     had `len(track_counts) == 1` regardless of distinct tracks played, silently
     failing the `min_tracks` filter and disappearing from results without an
     unmatched entry or any log warning.
  2. `normalize_name` applied its `album_metadata_words` set to the artist string as
     well as the album string, corrupting proper nouns like "New Edition" -> "new"
     and reducing artists named "Special", "Bonus", or "EP" to an empty string.
     Two artists with all-metadata-word names could collide on the same dict key.
  3. `normalize_track_name` used a 13-character hardcoded list while `normalize_name`
     used `str.maketrans(string.punctuation, ...)` covering all 32 ASCII punctuation
     characters. Characters like `&` were inconsistently handled.
  4. `fetch_top_albums_async` (aggregation, timestamp filtering, min_plays/min_tracks)
     had zero test coverage despite being the core business logic function.
- Plan vs implementation: all four defects addressed as described in
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md`. No scope additions or removals.
- Deviations: none.
- Validation:
  - `pytest -q`: **110 passed** (94 pre-existing + 9 new domain tests + 7 new logic tests).
  - `pre-commit run --all-files`: all hooks passed (black reformatted test_domain.py
    on first pass; clean on second).
  - Owner live test: Japanese-title 2025 album (betcover!!) now appears in results
    for listening year 2025 with "Same as release year" filter. Previously absent with
    no unmatched entry. Second validation: same artist's 2021 album (10 unique tracks,
    68 plays) also appeared correctly.
  - "New Edition" self-titled album test: artist key now "new edition" (not "new");
    album deduplication with "(Deluxe Edition)" suffix confirmed still working.
- Forward guidance: no schema, API contract, or route changes. No migration needed.
  The new `test_lastfm_logic.py` file should be extended if `fetch_top_albums_async`
  logic changes (e.g., top-songs feature). Pre-Batch-10 housekeeping is ongoing;
  Batch 10 scope remains TBD by owner.

### 2026-02-20 - fix(tooling): remove transient rotated field from SESSION_CONTEXT status block
- Scope: `scripts/doc_state_sync.py`, `AGENTS.md`.
- Problem: `_build_status_block` wrote `rotated=N` into the managed SESSION_CONTEXT
  block based on the current run's rotation count. The subsequent `--check` always
  recomputed `rotated=0` from the now-clean playbook, causing permanent drift after
  any `--fix --keep-non-current N` run. The workaround required a two-pass sequence.
- Fix: Removed the `Rotated to archive in latest sync run` line from `_build_status_block`.
  The count is still reported on stdout; it is no longer written to a file that `--check`
  re-derives. `--fix --keep-non-current 0` is now a single idempotent command.
- Updated `AGENTS.md` to document the one-pass rotation pattern for agent handoff.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: tooling is stable. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - docs: rotate 4 stale non-current Section 10 entries to archive
- Scope: `PLAYBOOK.md`, `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, `.claude/SESSION_CONTEXT.md`.
- Problem: Four pre-Batch-9 entries (2026-02-19 x2, 2026-02-14 x2) had accumulated
  below `CURRENT-BATCH-END` as `kept_non_current=4` with `rotated=0`, creating
  visible bloat in Section 10.
- Fix: Ran `python scripts/doc_state_sync.py --fix --keep-non-current 0` to flush
  all non-current entries to the archive. Section 10 now contains only active-batch
  entries.
- Deviations: none (purely mechanical doc maintenance).
- Validation:
  - `python scripts/doc_state_sync.py --check`: passed.
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: run `--fix --keep-non-current 0` at each batch boundary to keep
  Section 10 clean.

### 2026-02-20 - WP-7: frontend safety — showToast DOM construction + non-200 fetch guard
- Scope: `static/js/results.js`.
- Problem 1: `showToast` built its HTML via a template-literal string injected with
  `insertAdjacentHTML`. The `message` argument was interpolated without escaping,
  creating an HTML injection pathway if any caller passed server-sourced content.
- Problem 2: `fetchUnmatchedAlbums` piped `fetch()` directly to `.json()` without
  checking `response.ok`. A non-200 response (404, 500, etc.) would be silently
  treated as valid data, surfacing as "No unmatched albums found" instead of an
  error.
- Fix:
  - Rewrote `showToast` to build the toast element tree with `document.createElement`
    / `textContent` / `setAttribute`; eliminated `insertAdjacentHTML` and the unused
    `toastId`. Message content is now set via `.textContent` (XSS-safe).
  - Added `response.ok` guard before `response.json()` in `fetchUnmatchedAlbums`;
    throws `Error("Server error: <status>")` on non-2xx, which the existing `.catch`
    handler surfaces to the user.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: WP-7 complete. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - P1 refactor: extract VALID_FORM_DATA and csrf_app_client fixture
- Scope: `tests/helpers.py`, `tests/conftest.py`, `tests/test_routes.py`.
- Problem: `VALID_FORM_DATA` (the flounder14/2025 form dict for `/results_loading`
  tests) was copy-pasted verbatim 7 times across `test_routes.py`. The 5-line
  CSRF-enabled app + test-client setup was repeated in every CSRF test function.
- Fix:
  - Added `VALID_FORM_DATA` constant to `tests/helpers.py`.
  - Added `csrf_app_client` pytest fixture to `tests/conftest.py`; it creates a
    CSRF-enabled app client (WTF_CSRF_ENABLED not disabled) for CSRF enforcement
    tests.
  - Updated `tests/test_routes.py`: removed `from app import create_app` (now
    unused); imported `VALID_FORM_DATA` from `tests.helpers`; replaced all 7
    inline form dicts with `VALID_FORM_DATA` (or `{**VALID_FORM_DATA, "year": "X"}`
    for year-override cases); replaced all 6 CSRF test inline app setups with the
    `csrf_app_client` fixture parameter.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; pure refactor, no behaviour
    change).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - P1 perf: remove O(n) cache-size scan from cleanup_expired_cache
- Scope: `scrobblescope/utils.py`.
- Problem: `cache_size_mb = sum(len(str(v)) for v in REQUEST_CACHE.values()) / ...`
  ran inside `_cache_lock` on every cleanup call, even when debug logging was
  disabled. This O(n) string-serialization of all cached values held the lock
  unnecessarily and added CPU overhead proportional to cache size.
- Fix: removed the `cache_size_mb` line and simplified the debug log to
  `f"Cache status: {cache_count} entries"`. Count-only logging is sufficient
  for operational visibility; size estimation is not a runtime requirement.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; no test needed for log format).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next P1 item is test boilerplate extraction in
  `test_routes.py` (VALID_FORM_DATA + csrf_app_client fixture).

### 2026-02-20 - P0 fix: delete orphan JOBS entry on thread-start failure
- Scope: `scrobblescope/repositories.py`, `scrobblescope/routes.py`,
  `tests/test_repositories.py`, `tests/test_routes.py`.
- Problem: `create_job()` was called before `start_job_thread()`; on thread-start
  failure the semaphore slot was correctly released by `worker.py`, but the
  `JOBS[job_id]` entry persisted as an orphan until the 2-hour TTL cleanup.
- Fix:
  - Added `delete_job(job_id)` to `repositories.py`:
    `with jobs_lock: JOBS.pop(job_id, None)`.
  - Imported `delete_job` in `routes.py`; called it in the `except` block after
    thread-start failure, before returning the error page.
  - Added 2 tests to `test_repositories.py`:
    `test_delete_job_removes_existing_job`,
    `test_delete_job_on_missing_job_is_noop`.
  - Strengthened existing `test_results_loading_thread_start_failure_renders_error`
    to assert `mock_delete_job.assert_called_once()`.
- Validation:
  - `pytest -q`: **94 passed** (92 pre-existing + 2 new).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: The known orphan-job open risk (SESSION_CONTEXT.md Section 2)
  is now closed. Remaining P1 items: cache_size_mb in `cleanup_expired_cache`,
  and test boilerplate extraction in `test_routes.py`. Next required work package
  is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - doc_state_sync maintenance (remove volatile Last sync commit field)
- Scope: `scripts/doc_state_sync.py`, `.claude/SESSION_CONTEXT.md`.
- Issue: `doc-state-sync-check` pre-commit hook was failing on PR merge to main.
  Root cause: `_build_status_block()` called `git rev-parse --short HEAD` to write
  `Last sync commit: <hash>` into SESSION_CONTEXT.md. On `--check`, the command
  returned the NEW merge commit hash, which did not match the stored hash, causing
  drift detection failure on every merge.
- Fix: Removed `_git_head_short()` function, `subprocess` import, and the
  `Last sync commit` line from `_build_status_block`. The `--check` now validates
  only stable content-level fields (batch number, WP numbers, entry count, newest
  heading). Ran `--fix` to drop the stale `Last sync commit` line from
  SESSION_CONTEXT.md.
- Commit: `cdedd65` fix: remove Last sync commit from doc_state_sync status block.
- Forward guidance: The doc-state-sync-check hook will no longer false-positive on
  merge commits. SESSION_CONTEXT DOCSYNC block is validated on content only.

### 2026-02-20 - WP-6 completed (remove artificial orchestration sleeps)
- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Removed all 5 `await asyncio.sleep(0.5)` calls from `_fetch_and_process`. The
    calls were added as a progress-pacing mechanism but served no functional purpose
    and added a fixed 2.5 s latency overhead to every job.
  - All `set_job_progress` calls and their messages are preserved at the same
    progress values (0, 5, 20, 30, 40, 60, 80, 90, 100), so the loading-page
    progress sequence is unchanged from the user's perspective.
  - `asyncio` import retained: `asyncio.Semaphore`, `asyncio.gather`,
    `asyncio.new_event_loop`, and `asyncio.set_event_loop` are still used.
  - Removed two dead `patch("asyncio.sleep", new_callable=AsyncMock)` lines from
    `test_fetch_and_process_cache_hit_does_not_precheck_spotify` and
    `test_fetch_and_process_sets_spotify_error_from_process_albums` in
    `tests/services/test_orchestrator_service.py`. Those patches were no-ops after
    the sleep removals.
- Deviations and why: none. "Gate with debug-only UX flag" option was not needed;
  the plain removal is simpler and all test coverage is already progress-message
  based, not timing based.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (no count change; two dead patches removed,
    no new tests needed).
- Forward guidance: Next work package is WP-7 (frontend safety and resilience
  polish).

### 2026-02-20 - WP-5 completed (enforce registration-year validation server-side)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added a registration-year guard in `results_loading` immediately after the
    `2002..current_year` bounds check. The guard calls `check_user_exists(username)`
    via `run_async_in_thread` (same helper used by `validate_user`). The result is
    already cached from the blur-validation step, so the call is typically free.
  - If `registered_year` is present and `year < registered_year`, the route
    re-renders `index.html` with an explicit error message citing the registration
    year and the earliest valid year.
  - If the check raises (Last.fm unavailable, network error, etc.), a `WARNING`
    is logged and the route proceeds without blocking the user (fail-open policy).
  - If `registered_year` is `None` (not returned by Last.fm), the check is skipped
    and the route proceeds normally.
  - Updated four existing `results_loading` tests that reach the guard to patch
    `scrobblescope.routes.run_async_in_thread` with a neutral result
    (`{"exists": True, "registered_year": None}`) to avoid live network calls.
  - Added four new tests to `tests/test_routes.py`:
    - `test_results_loading_year_below_registration_year_rejected`
    - `test_results_loading_year_at_registration_year_allowed`
    - `test_results_loading_registration_check_unavailable_proceeds`
    - `test_results_loading_no_registered_year_proceeds`
- Deviations and why: none. Fail-open on service unavailability was the intended
  design from the WP-5 spec (client-side validation already covered the common
  case; server-side guard adds defense-in-depth without blocking on transient errors).
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (88 pre-existing + 4 new).
- Forward guidance: Next work package is WP-6 (remove or gate artificial
  orchestration sleeps).

### 2026-02-20 - WP-4 completed (harden app secret and startup safety)
- Scope: `app.py`, `tests/conftest.py`, `tests/test_app_factory.py` (new), `.env.example`, `README.md`.
- Plan vs implementation:
  - Added `_KNOWN_WEAK_SECRETS = frozenset({"dev", "changeme_in_production", ""})` and `_MIN_SECRET_LENGTH = 16` constants in `app.py`.
  - Added `_validate_secret_key(secret_key: str, is_dev_mode: bool) -> None` in `app.py`. Logic: if key is falsy, in weak set, or shorter than 16 chars -> "weak". In production (`debug_mode=False`): raises `RuntimeError("Refusing to start: ...")`. In dev mode (`DEBUG_MODE=1`): logs `WARNING "SECRET_KEY is missing or insecure. ..."`.
  - Updated `create_app()` to read `_raw_secret = os.getenv("SECRET_KEY", "")`, call `_validate_secret_key(_raw_secret, debug_mode)`, then set `application.secret_key = _raw_secret or "dev"`. "dev" is the dev-mode fallback; in production, `_validate_secret_key` raises before it can be used.
  - `tests/conftest.py` updated: added `import os` + `os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")` before `from app import create_app`. This seeds the guard before `app.py`'s module-level `create_app()` call (which runs at import time).
  - New `tests/test_app_factory.py` with 7 tests: production-fail on missing/dev/changeme/too-short keys; dev-mode warning; strong-key success in both modes.
  - `.env.example` `SECRET_KEY` comment updated to say "REQUIRED in production. Startup fails if missing or set to placeholder."
  - `README.md` setup step 4 comment updated from "Recommended" to "Required in production" with note that `DEBUG_MODE=1` suppresses the check for local dev.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black reformatted `app.py` quote style on first run; clean on second).
  - `pytest -q`: **88 passed** (81 pre-existing + 7 new).
- Commit: `eb13a27` feat: refuse startup on weak SECRET_KEY in production.
- Forward guidance: Next work package is WP-5 (enforce registration-year validation server-side).

### 2026-02-20 - WP-1 correctness fix (slot leak on Thread.start failure)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Issue: WP-1 post-audit check found that `acquire_job_slot()` in `results_loading` was not guarded against failure of `Thread.__init__` or `Thread.start()`. If either raises (e.g. `OSError` under OS-level thread exhaustion), the slot is permanently consumed because `background_task`'s `finally` block never runs. This violates WP-1's acceptance criterion "no leaked active slots after worker exceptions."
- Fix:
  - Added `release_job_slot` to imports in `routes.py`.
  - Wrapped `threading.Thread(...)` and `task_thread.start()` in try/except; on exception: `release_job_slot()`, `logging.exception(...)`, return `index.html` with error message.
  - Added `test_results_loading_thread_start_failure_releases_slot`: patches `Thread` to raise `OSError`, asserts slot is released and index re-rendered.
- Validation:
  - `pre-commit run --all-files`: all hooks passed.
  - `pytest -q`: 77 passed.
- Also: added "callers must not mutate" to `get_cached_response` docstring (latent mutable-reference risk; no active bug since no caller mutates the returned object).

### 2026-02-20 - worker.py architectural decision + product roadmap + CSRF coverage expansion

- Scope: Documentation updates only (`.claude/SESSION_CONTEXT.md`, `EXECUTION_PLAYBOOK_2026-02-11.md`). No runtime code changes yet.
- Decisions made:
  - **Product roadmap confirmed:** Two additional background task types are planned -- "top songs" (Last.fm + possibly Spotify, separate background task/results flow) and "listening heatmap" (Last.fm only, last 365 days, lighter task). This means the `results_loading` acquire->Thread->release pattern will be needed by at least 3 routes.
  - **worker.py chosen as home for concurrency lifecycle:** With multiple background task types incoming, keeping the semaphore and thread-start boilerplate in `repositories.py` would require each new route to duplicate the `acquire -> try Thread.start -> except release` block. A new `scrobblescope/worker.py` leaf module (imports `config` only) will own `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread(target, args=())`. `repositories.py` becomes pure job state CRUD. `start_job_thread()` encapsulates the full try/start/except/release pattern for all callers.
  - **Refactor must precede the 3-commit save-state:** WP-1 originally placed the semaphore in `repositories.py`. The worker.py refactor corrects this before committing; the WP-1 commit will reflect the final architecture.
- CSRF test coverage expansion (also completed this session, before context compaction):
  - Initial WP-3 implementation added 2 CSRF tests covering only `/results_loading`.
  - Expanded to 6 total CSRF tests covering all 4 POST routes:
    - `test_csrf_rejects_post_without_token` (-> `/results_loading` 400)
    - `test_csrf_accepts_post_with_valid_token` (-> `/results_loading` 200)
    - `test_csrf_rejects_results_complete_without_token` (-> 400)
    - `test_csrf_rejects_unmatched_view_without_token` (-> 400)
    - `test_csrf_rejects_reset_progress_without_token` (-> 400)
    - `test_csrf_accepts_reset_progress_with_header_token` (-> `/reset_progress` XHR path with `X-CSRFToken` header, 200)
  - Total tests after expansion: **81 passing**.
- Pending implementation (next agent actions in order):
  1. Create `scrobblescope/worker.py` with semaphore, `acquire_job_slot()`, `release_job_slot()`, `start_job_thread()`.
  2. Remove semaphore/slot functions from `scrobblescope/repositories.py`.
  3. Update imports in `routes.py` and `orchestrator.py` to use `worker`.
  4. Update patch targets in `test_routes.py` and `test_orchestrator_service.py` from `scrobblescope.routes.acquire_job_slot` / `scrobblescope.orchestrator.release_job_slot` -> `scrobblescope.worker.*`.
  5. Run `pre-commit run --all-files` and `pytest -q` (must stay at 81 passing).
  6. Make 3 separate commits: WP-1, WP-2, WP-3.
- Validation: N/A (doc-only session-end update).
- Forward guidance:
  - worker.py is a leaf module -- it must NOT import from `repositories`, `routes`, `orchestrator`, or any higher module (would create cycles).
  - `start_job_thread()` should release the slot and raise on `Thread.start()` failure so routes get a clean exception to handle (mirrors the current try/except pattern in `routes.py`).
  - After the 3 commits are made, next work package is WP-4 (harden app secret and startup safety).

### 2026-02-19 - Fly cold-start recovery validation completed (app + Postgres DB)
- Scope: operational validation of deployed services and documentation refresh (`.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`).
- Plan vs implementation:
  - Confirmed both machines were started (`fly status -a scrobblescope`, `fly status -a scrobblescope-db`).
  - Forced cold state by stopping both machines:
    - `fly machine stop 807339f1595248 -a scrobblescope`
    - `fly machine stop 8e7ed9ad205118 -a scrobblescope-db`
  - Verified both reported `State: stopped` via `fly machine status`.
  - Triggered one end-to-end request:
    - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 1 --timeout-seconds 180`
  - Verified smoke run completion and auto-start behavior for both app and DB machines.
  - Rechecked DB health until all checks passed (`pg`, `role`, `vm`).
- Deviations and why:
  - No code changes were required; this was an operational verification step requested by the owner.
- Validation:
  - Smoke output: `elapsed=18.75s`, `db_cache_enabled=True`, `db_cache_lookup_hits=247`, `db_cache_persisted=0`, `spotify_matched=247`, message `Done! Found 57 albums matching your criteria.`
  - Post-run status: app machine `started`, DB machine `started`, DB checks all passing.
- Forward guidance:
  - Keep this cold-start check as a regression smoke pattern after infra/config changes.
  - If cold-start latency grows, tune DB wake-up retry knobs (`DB_CONNECT_MAX_ATTEMPTS`, `DB_CONNECT_BASE_DELAY_SECONDS`) and/or Fly machine warmness settings.

### 2026-02-19 - Context reconciliation completed (docs parity + cache fallback logging classification)
- Scope: `.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`, `scrobblescope/cache.py`, `tests/test_repositories.py`.
- Plan vs implementation:
  - Re-verified playbook/session claims against the active repo for `init_db.py`, thread model, and cache fallback behavior.
  - Refreshed stale status fields (latest commit snapshot, app.py line count, and current runtime notes).
  - Updated `_get_db_connection()` to log explicit fallback categories:
    - `asyncpg-missing`
    - `missing-env-var`
    - `db-down`
  - Extended DB helper tests to assert those log categories are emitted on each path.
- Deviations and why:
  - No keep-alive thread was added to `app.py`; this is intentional because the current architecture uses per-job daemon worker threads from `results_loading` and avoids additional idle background loops.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed** (2 deprecation warnings from aiohttp connector behavior on Python 3.13.3).
- Forward guidance:
  - Keep Section 2 and `.claude/SESSION_CONTEXT.md` synchronized whenever runtime snapshots (line counts, branch/commit status, logging behavior) change.

### 2026-02-14 - Repository hygiene completed (historical docs archive + README refresh)
- Scope: `docs/history/` (new folder), historical markdown moves, `PLAYBOOK.md`, `README.md`.
- Plan vs implementation:
  - Moved historical docs from repo root into `docs/history/`:
    - `AUDIT_2026-01-10.md`
    - `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`
    - `CHANGELOG_2026-01-04.md`
    - `CHANGELOG_2026-02-10.md`
    - `OPTIMIZATION_SUMMARY.md`
    - `PERFORMANCE_TIMING.md`
    - `Refactor_Plan.md`
    - `TEMPLATE_REFACTOR_SUMMARY.md`
  - Updated playbook references to `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`.
  - Refreshed `README.md`:
    - run instructions now show `python app.py` (recommended) and `python run.py` (optional launcher)
    - project structure updated to current modular layout + `docs/history/`
    - roadmap/status text updated to reflect current post-refactor state
- Deviations and why:
  - Keep a shim at `EXECUTION_PLAYBOOK_2026-02-11.md` to preserve a stable handoff entrypoint.
- Forward guidance:
  - Keep new planning/audit/changelog docs in `docs/history/` unless a document is an active operator runbook.
  - Keep playbook and session-context docs at predictable top-level locations for fast bootstrap.

### 2026-02-14 - Cache wake-up hardening completed (DB connect retry/backoff + docs refresh)
- Scope: `scrobblescope/cache.py`, `tests/test_repositories.py`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Added exponential-backoff DB connection retries in `_get_db_connection()` to reduce false cache bypass during Fly Postgres wake-up windows.
  - Added two DB helper tests:
    - retry-then-success path
    - retry-exhaustion path
  - Updated existing connect-failure test to force single-attempt behavior (`DB_CONNECT_MAX_ATTEMPTS=1`) for deterministic assertions.
  - Refreshed handoff docs for the new test count and operational behavior.
- Deviations and why:
  - No orchestration/routing behavior changes were needed; hardening was isolated to cache connection setup and DB helper tests.
- Additions beyond plan:
  - Added env-tunable retry knobs:
    - `DB_CONNECT_MAX_ATTEMPTS` (default `3`)
    - `DB_CONNECT_BASE_DELAY_SECONDS` (default `0.25`)
  - Live Fly verification confirmed:
    - app cache hits persisted after DB stop/start
    - DB app `scrobblescope-db` uses `FLY_SCALE_TO_ZERO=1h`, explaining suspended/stopped state after idle periods.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
  - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`: **PASS** (`db_cache_enabled=True`, `db_cache_lookup_hits=247`).
- Forward guidance:
  - If first-request latency after idle is a concern, either increase retry knobs or adjust/remove DB `FLY_SCALE_TO_ZERO`.
  - Keep periodic smoke checks as operational validation for cache persistence and warm-hit behavior.
  - Resolve DB app staged secrets drift (`fly secrets deploy -a scrobblescope-db`) to avoid config ambiguity.

### 2026-02-14 - Frontend responsiveness polish completed (toggle placement + mobile table scaling)
- Scope: `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`, `static/css/unmatched.css`, `static/css/error.css`, `templates/results.html`.
- Plan vs implementation:
  - Standardized dark-mode toggle to a compact fixed bottom control across all page CSS bundles.
  - Improved `index.html` mobile fit by tightening spacing, typography, and card/logo sizing at mobile breakpoints.
  - Improved `results.html` mobile readability by shrinking table density, making actions stack cleanly, and reducing album-art footprint.
  - Added `results-table` class in template for targeted responsive behavior.
  - Centered decade pills in `index` filter UI.
- Deviations and why:
  - To improve fit on common phones, responsive rules were applied up to `max-width: 767.98px` for index/results rather than only `575.98px`.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - If users still report table crowding on very small devices, next step is card-style row rendering for results instead of a dense 5-column table.
  - Consider extracting shared toggle CSS into one common stylesheet to reduce cross-file duplication.

### 2026-02-14 - Post-Batch-8 hardening completed (low-severity gap closure + test layout split)
- Scope: `tests/test_routes.py`, `tests/conftest.py`, `tests/helpers.py` (new), `tests/services/` (new split files), `EXECUTION_PLAYBOOK_2026-02-11.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Closed previously identified low-severity gaps:
    - Added direct route tests for `/unmatched_view` (missing `job_id`, missing job, success render path).
    - Added explicit tests for app-level 404 and 500 handlers.
  - Reduced test coupling to `conftest.py` internals:
    - Moved shared constants/mock helpers into `tests/helpers.py`.
    - Updated tests to import from `tests.helpers` rather than `conftest`.
  - Split monolithic service test file:
    - Removed `tests/test_services.py`.
    - Added `tests/services/test_lastfm_service.py` (4 tests).
    - Added `tests/services/test_spotify_service.py` (3 tests).
    - Added `tests/services/test_orchestrator_service.py` (10 tests).
- Deviations and why:
  - No runtime code changes were required. This was a test architecture and coverage hardening pass only.
  - Added one extra test category beyond the initial gap list (500 handler integration path) because this was explicitly untested and low effort/high confidence.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **64 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - Subpackage migration should be sequenced **after** the next feature-heavy batch set (Batch 9+) stabilizes, not before. Keep current flat module layout while churn is high; cut to subpackages once contracts settle.
  - Keep route-handler coverage and helper-module pattern as baseline for future test additions.

### 2026-02-13 - Operational config fix (Fly machine autostop)
- Scope: `fly.toml`.
- Issue:
  - Fly log showed autostop with `0 out of 1 machines left running` because `min_machines_running` was set to `0`.
- Change:
  - Updated `[http_service] min_machines_running = 1` to keep one machine warm.
- Notes:
  - This log means capacity scaling, not cache overflow.
  - In-memory caches (`REQUEST_CACHE`, `JOBS`) live in RAM on the app VM and are lost on machine stop/restart.
  - Persistent Spotify metadata cache lives in Fly Postgres (`spotify_cache`) via `DATABASE_URL`.
