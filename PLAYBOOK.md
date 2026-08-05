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
- **Next action:** execute the full F-SWE-1 principles audit, then proceed to
  Batch 21 WP-1. The peer-sized read-only worktree guard and canonical
  bootstrap gate passed final review plus POSIX CI remediation, and
  F-WORKTREE-1/F-WORKTREE-2 are resolved.
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
    8,754-byte pre-existing peer caps; every new test file is below the
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
