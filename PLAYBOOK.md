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
| 21 | UI overhaul -- Tailwind + daisyUI migration | `BATCH21_DEFINITION.md` | active -- Section 4 |

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

- **Batch 18 is complete.** All 5 WPs done. Definition archived:
  `docs/history/definitions/BATCH18_DEFINITION.md`.
- **Batch 19 is complete.** All 5 WPs done plus owner-review follow-up.
  Definition archived: `docs/history/definitions/BATCH19_DEFINITION.md`.
  PR #152 (Batches 18 + 19) merged to `main`.
- **Batch 20 is complete.** All 9 WPs done (WP-0 through WP-5 via PR #159
  on `file-hygeine`; audit gap-fix follow-up, WP-6, WP-7, and WP-8 on
  `wip/batch-20`, submitted as PR #162). Definition archived:
  `docs/history/definitions/BATCH20_DEFINITION.md`.
- **Batch 21 is active.** Definition: `BATCH21_DEFINITION.md` (repo
  root). Scope: UI overhaul -- Bootstrap 5.1.3 -> Tailwind v4 (standalone
  CLI) + daisyUI v5, warm heatmap-derived themes propagated app-wide,
  page-by-page strangler migration. Expanded from the owner's Claude
  Design audit (UI Audit v3); four owner decisions locked in the
  definition. Branch: `wip/batch-21` (worktree off `main`).
- **Next action:** merge PR #169, then execute the full F-SWE-1 principles
  audit, then proceed to Batch 21 WP-1. The canonical repository-integrity gate
  and read-only worktree guard passed final combined-branch
  remediation, and F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2 are resolved. Three
  guard files now exceed their directory peer caps after review remediation --
  accepted as a deviation and tracked as F-WORKTREE-4 in FINDINGS.md, not
  silently. Review remediation is complete through round 5: the test count
  derives from one total ordering, the guard discovers the main working tree
  from Git rather than inferring it, the base ref is untouched between
  batches, an ambiguous count authority no longer switches DOC006 off, and
  the design documents describe the checks that shipped. Before
  merging, confirm a Quality Gate run exists for the current head -- none was
  created for `8463ca4` despite a delivered push event, and that gap is what
  `workflow_dispatch` now exists to cover on future heads.
- Batch 21 WP status: WP-0 done. WP-1 through WP-8 not yet started.
- **Perf note:** heatmap fetch speed is rate-limit bound; measurement and
  rationale live in FINDINGS.md F-B18-11 (single source).
- **Last.timer note (checked 2026-05-19):** the referenced project uses
  aggregate `user.gettopartists`/`user.gettoptracks` calls with page fan-out,
  not exact per-scrobble recent-track timestamps. Useful for future perf
  research, but not a drop-in heatmap speedup. See FINDINGS.md F-B19-3.
- Future feature candidates (confirmed by owner roadmap):
  - **Top songs** (future): rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).

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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-07-24 - Batch 21 opened: UI overhaul definition committed (Batch 21 WP-0)

- Scope: opened Batch 21 (UI overhaul -- Tailwind + daisyUI migration)
  on `wip/batch-21`, a worktree off `main` at the PR #162 merge.
- Plan vs implementation:
  - `BATCH21_DEFINITION.md` expanded from the stub into the full 9-WP
    definition derived from the owner's Claude Design audit (UI Audit
    v3): toolchain (WP-1), base shell + error-page pilot (WP-2), index
    (WP-3), unified loading (WP-4), results leaderboard (WP-5), heatmap
    seam removal (WP-6), unmatched + reason_code backend fix (WP-7),
    sweep + close-out (WP-8). Strangler migration, page by page.
  - Four owner decisions locked in the definition: rotating loading
    messages cut; welcome modal deleted; `limit_results` kept inside the
    thresholds disclosure; fonts self-hosted under `static/fonts/`.
  - Agent verification recorded in the definition: the unmatched
    reason-string grouping bug is live; `--bs-primary` never overridden;
    `bootstrap.Popover` in `index.js` is a third Bootstrap JS consumer
    the audit missed; `--bars-color` must be aliased in both themes.
  - PLAYBOOK Section 2 row title updated; Section 3 marks Batch 21
    active with next action WP-1; SESSION_CONTEXT rows updated.
  - Toolchain mechanics locked after an owner-relayed Opus 5 review:
    CLI binary in gitignored `scripts/bin/` with `.gitkeep`; auto-fetch
    at a pinned version via a new `scripts/dev/tailwind_build.py` (not
    `dev_start.py` -- app startup never needs the toolchain); WP-8 adds
    a rebuild-and-diff pre-commit hook for compiled-CSS drift; WP-8
    owner E2E explicitly opens the downloaded save-as-image file.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0 (expected
  root warning for the now-active `BATCH21_DEFINITION.md`).
- Forward guidance: WP-1 sets up the Tailwind v4 standalone CLI +
  daisyUI v5 bundled plugin, defines both themes from the audit token
  sheet, and commits the compiled CSS. No template changes until WP-2.

<!-- DOCSYNC:CURRENT-BATCH-END -->

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
