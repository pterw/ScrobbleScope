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
  it task by task, then write the frontend plan. Task 1 has landed. Write
  each specialized plan before implementing its cluster. The
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
