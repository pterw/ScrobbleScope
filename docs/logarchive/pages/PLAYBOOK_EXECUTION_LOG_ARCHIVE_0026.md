<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0026

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
