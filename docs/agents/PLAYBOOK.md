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
  it task by task, then write the frontend plan. Tasks 1-4 have landed. Write
  each specialized plan before implementing its cluster. The
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
