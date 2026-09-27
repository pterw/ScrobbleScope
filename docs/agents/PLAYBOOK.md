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
  2, 3 and 4 have landed. Next
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

### 2026-09-27 - File the carried close-out findings and amend Part C

Side task, no batch tag: filed two carried findings, amended
`BATCH23_DEFINITION.md`, and fixed three rule/record docs, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- Filed `F-DOCSYNC-23` (the tracked test-module count is hand-maintained and
  unchecked) and `F-B23-10` (three frontend-gate failures were gate defects,
  each green on an immediate rerun), both P2, in `docs/agents/FINDINGS.md`.
  Re-measured the module count now: `git ls-tree -r --name-only HEAD tests |
  grep -c '/test_[^/]*\.py$'` gives 78, matching both `.claude/
  SESSION_CONTEXT.md` and the `FINDINGS.md` header -- both sites are right
  today, so no correction was needed.
- `BATCH23_DEFINITION.md`: recorded the three approved WP-0 follow-on plan
  paths as executed; recorded F-B21-60's Spotify-icon/attribution part as
  remaining, unscheduled work (it stays in Part C's set and open); added
  `scripts/dev/results_behavior_tests.py` to Part C's acceptance gate list.
- `AGENTS.md` Batch Close-Out Procedure step 5 now says to run `pytest -q`
  before `--fix --test-count N`, since no earlier close-out step measured
  the count.
- `.superpowers/cloud-kit/constraints.md` (tracked, generic): brought its R5
  commit procedure, R6 expected warnings and R7 docsync-control-plane
  exemption in line with the control-plane workspace's later rulings.
- `docs/history/findings/FINDINGS_ARCHIVE.md` F-B21-3: reworded the
  pip-audit recount from "found 0 vulnerabilities in 0 packages" to
  "reported no known vulnerabilities".

Validation: `pytest -q` -- **1993 passed**.

### 2026-09-27 - Close out the test-infrastructure plan's carried test minors

Side task, no batch tag: closed the carried test minors from
`docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md` Task 1,
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- `tests/test_pipeline_integration.py`: the /progress poll loop and the
  background-thread join each had their own 10s deadline, so a genuine
  hang could take up to 20s to fail. `_JOB_TIMEOUT_SECONDS` (now 30, still
  bounded) is one `time.monotonic()` deadline computed once; `join()`
  spends only what is left of it. `created_threads[0]` assumed the first
  captured `background_task` thread was this job's; the test now asserts
  `len(created_threads) == 1`, naming the count, before using it.
- `tests/test_provider_fixtures.py`'s
  `test_lastfm_fixture_flows_through_fetch_top_albums` docstring claimed a
  fixture missing `name` would fail the test, but
  `scrobblescope/orchestrator/__init__.py` reads `t.get("name", "...")`, so
  a missing name still yields an eligible album. The docstring now names
  only the fields the test actually catches.

Validation: `pytest -q` -- **1993 passed**.

### 2026-09-27 - Close out the control-plane plan's carried code items

Side task, no batch tag: closed the carried docsync code items from
`docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md` (all eight
tasks landed), part of Batch 23 WP-0 Part C. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- m1: `docsync.logic` and `docsync.integrity` each carried a deferred,
  module-bottom import of one name from the other, guarded by a "would
  deadlock" comment -- a same-module import cycle broken only by import
  order. `SESSION_CURRENT_COUNT_RES` moved to `docsync.parser`, the leaf
  module both already import at top level (still importable from
  `docsync.integrity`, which re-exports it); `integrity.py`'s three names
  from `logic.py` moved to its top imports now that nothing in `logic.py`
  needs anything from `integrity.py`. Both deadlock comments are gone.
- m4: `WP_COMPLETE_STATUS_RE` (`scripts/docsync/parser.py`) had no end
  anchor, so `**Status:** WP-4 complete (pending review)` counted as WP-4
  done. Anchored: the line may close with an optional `.` and trailing
  whitespace only.
- CR5: `[untracked_essentials]` paths were not contained to the repository
  root. `declarations._validate_untracked_essentials` now rejects an
  absolute path (POSIX or Windows drive form) or a `..` segment; the
  worktree guard's directory diagnostic renders the declared path with
  `repr()` rather than echoing it raw.
- CR10: a declared `[untracked_essentials]` path that exists as a directory
  read as "missing". `essentials_diagnostics` now distinguishes missing from
  "exists but is not a file" (a new WT015 WARNING).
- CR9: `_validate_test_count`, `_validate_untracked_essentials` and
  `_validate_closeout` each hand-wrote the same is-a-table-plus-unknown-key
  check. Extracted one `_validated_table` helper (Rule of Three); every
  existing error message stays byte-identical.
- CR4 (ruled, no code change): WT015 fires in every checkout because
  `skills-lock.json` is truly absent; the warning is true, and where the
  file lives is the owner's decision.
- CR6 (ruled, no code change): the import-time `sys.path` insert in
  `_worktree_guard_essentials.py` is the control-plane plan's
  pre-accepted deviation, the same shape as `scripts/doc_state_sync.py`.
- m6 (ruled, no code change): the hand-maintained module count is filed as
  a finding in the close-out docs commit, not built here.

Validation: `pytest -q` -- **1993 passed**.

### 2026-09-27 - Audit the dev requirements too (CI input gap)

Side task, no batch tag: closed the scope item "add requirements-dev.txt
to the CI audit's inputs", part of Batch 23 WP-0 Part C. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands.

The "Security audit (pip-audit)" step in `.github/workflows/test.yml`
passed `inputs: requirements.txt` only, so a vulnerable pin anywhere in
`requirements-dev.txt` was never flagged. `pypa/gh-action-pip-audit@v1.1.0`
documents `inputs:` as a whitespace-separated list (its own README example:
`inputs: requirements.txt dev-requirements.txt`), so the step now reads
`inputs: requirements.txt requirements-dev.txt`.

Live probe in a scratch copy: pinning `virtualenv==20.26.5` in a scratch
`requirements-dev.txt` made `pip-audit -r requirements.txt -r <scratch>`
report PYSEC-2024-187 (exit 1); reverting to the real, pinned
`virtualenv==20.36.1` made the advisory disappear (exit 0, "No known
vulnerabilities found"), confirming the dev file is now audited.

Validation: `pytest -q` -- **1978 passed**.
