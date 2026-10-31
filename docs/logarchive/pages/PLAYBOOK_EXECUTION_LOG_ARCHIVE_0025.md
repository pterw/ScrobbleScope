<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0025

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
