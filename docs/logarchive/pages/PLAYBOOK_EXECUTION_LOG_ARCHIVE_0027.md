<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0027

### 2026-09-26 - A Chromium harness for heatmap.js's pure-function seam

Side task, no batch tag: added a Chromium harness for heatmap.js's pure-function seam, part of
Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

rocketColor, countToNorm and the export header layout are exercised by a Chromium harness
(tests/frontend/test_heatmap_pure_functions.py) through window.__scrobbleHeatmapTestHooks,
exposed at the module's top level only when window.__scrobbleHeatmapTestMode is set before the
script runs -- the guarded seam F-B21-18 asked for, so no production page load exposes the hook;
computeStreak is WP-6's per Q14 answer a; the harness carries a browser pytest marker so CI's
pre-browser coverage step deselects it and the post-browser frontend-gate step runs it instead.

Fix round 1 (code review): added interior countToNorm cases so a linear count/maxCount cannot
pass; a negative exportHeaderModel case (no text-transform leaves the text as written) with the
model tests cleaning up their own DOM inserts; a test that a second page never setting the flag
never sees the hooks; reused _launch_browser for the setup-guidance path; and corrected the
seam's stale "these four functions are pure" comment (exportHeaderModel reads the DOM). Filed the
harness scope's two residual F-B21-18 items (the 53x7 export contract deviation, the duplicated
username validators) as F-B23-9, joining WP-0 Part C's set by controller ruling 2026-09-26
(BATCH23_DEFINITION.md Part C); F-B21-18's archived record now points to it.

Validation: `pytest -q` -- **1963 passed**.

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
