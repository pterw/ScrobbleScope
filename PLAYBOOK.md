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
  definition. Branch: `test` (worktree off `main`; remediated from `wip/batch-21` per owner authorization 2026-09-06).
- **Results refinement:** proportional scaling and the warm shared canvas are
  included in the review follow-up; F-B21-55 and Section 4 record evidence.
  The current owner consistency pass adds midpoint surfaces, matched sidebar
  headings and action buttons, removes redundant Heatmap loading counters,
  and repairs page/handoff motion. The index form sits up to 2.5rem higher;
  the decade-filter state fits shorter desktop windows without changing scale.
  The 2026-09-10 follow-up refines Heatmap contrast and toolbar type, adds
  delayed Spotify link hints and animated ranking changes, and fixes a
  reproduced first-paint flash. The header now scrolls out of view in document
  flow, following the owner's screenshot clarification. Final validation passed;
  owner visual review is approved and the reviewed changes are authorized for PR #227.
- **PR #227 priority triage:** F-B21-49 is resolved in the review follow-up.
  Review comments including assertions and all 15 deleted route TODOs were
  checked; F-B21-54 records remaining scanner noise. Evidence:
  `docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md`.
  The owner authorized publishing the pending review commits and approved
  refinements on `test`. WP-7 retains scope; Task 6 timing follows the
  canonical remediation plan.
- **PR #227 review remediation:** the owner-requested package is implemented
  and validated. Audit and remaining scope:
  `docs/history/reports/PR227_REVIEW_2026-09-07.md`. The latest Section 4 entry
  records subsequent owner-approved header and surface refinements.
- **PR #223 side-task:** merged as `123b127`; this worktree is synchronized.
  Remaining issue #222 targets stay open.
- **Planning follow-up:** the original owner-review plan remains historical
  evidence; the superseding plan below is canonical. Task 2 now implements
  the two-engine runner and explicit CSS composition dimensions. Its rendered
  expanded-state guard, complete validation, and PR #224 review remediation
  passed.
- **Remediation plan:** **Tasks 1-5 are complete and validated locally.
  Task 6 (accessibility pass) is deferred until Bootstrap is fully removed.** Work from
  `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`.
  Task 1 is complete. Task 2 replaces the engine-independent height-denominator
  defect with layout-aware CSS and a complete real-window gate in Chromium
  and Firefox; it merged as PR #224. Task 3 landed the final `3fr 4fr` split,
  owner-refined `27.5rem` form base cap, raised `--shell-border` contrast to
  >= 3:1 in both themes, and applied the ruled header clamps (`--shell-height`,
  `--shell-control-gap`, nav-link/theme-control sizing). Review remediation pins that
  composition across every reachable form state and uses one fast hero/page
  fade timing (F-B21-41, F-B21-42). Task 4 aligned visible
  loading progress with pipeline phases across Top Albums and Heatmap,
  eliminated overlapping interval polls and stale responses (F-B21-33), decoupled
  received vs attempted Last.fm counts, corrected loading composition
  (F-B21-36), and added real-browser phase checks to the gate. Its review fix
  keeps the loader hidden when a saved Heatmap job is already cached and fades
  the result in directly (F-B21-43). Task 5 added the dedicated unmatched
  no-data surface (`templates/unmatched_empty.html`), wired clean session
  recovery and eviction on `/unmatched`, mutest-verified failure paths, and
  extended `frontend_gate.py` with card, shadow, and action assertions.
  Owner visual refinements bias the desktop form above centre,
  unify single-row mobile navigation with the theme control below page content,
  widen the desktop Heatmap result, and return its username to the neutral headline
  treatment (F-B21-44 through F-B21-46). Task 6 follows Bootstrap removal; see the canonical remediation plan.
  WP-4 migrated `loading.html` to the shared determinate wait panel, completed
  both polling state machines, and added browser-session recovery for the
  latest album and heatmap jobs at clean destination routes.
  The original twelve-round Codex review closed at `77bb001`: all thirty threads
  were resolved, both Quality Gate runs passed, and the Codex connector
  recorded a thumbs-up. Three later Graphify passes produced advisory findings.
  Codex confirmed five defect classes: the root-font and saved-theme checks
  leaked state, declaration paths could escape the repository, and joining
  documents for wrapped regex matches lost the original per-line semantics;
  equivalent spellings of one repository path could also bypass a live
  in-memory document and read stale disk. All five are hardened at shared
  seams with regression tests. The remaining claims were disproved against
  section boundaries, source contracts, tests and live browser execution.
  GitHub remains the source of truth for the PR's integration state.
  `templates/partials/_loading.html` already exists and is framework-neutral
  -- WP-3 built it a work package early -- so WP-4 consumes that partial
  rather than writing one. `GET /loading` supplies the route the gate needs;
  its job fixture, composition check, and two-pipeline state-machine check
  landed in WP-4.
  **WP-3 is complete.** It rebuilt `index.html` on Tailwind, deleted the
  welcome modal and the `bootstrap.Popover` hints, absorbed WP-6, and grew
  the frontend gate from four checks at one desktop viewport into a
  multi-profile regression suite. Codex raised thirty comments across twelve
  rounds; twenty-nine were valid, and one sizing premise was disproved but
  received its conservative remedy. All were actioned.
  Earlier context, still true: WP-2 **merged as PR #216** on 2026-08-24
  (`658bdb2`, rebase merge). It shipped the base shell, the `error.html`
  pilot, the Playwright runtime, the frontend gate and the compiled-CSS
  pre-commit hook, closing F-B21-2, F-B21-7 and F-AUDIT-1 and filing
  F-B21-10, F-B21-11 and F-B21-12. Codex raised seven comments across three
  rounds; every one was valid and all seven were fixed before the merge.
  Round three took the SMIL out of the header wordmark and gave the
  back-to-top control its wrapper back. PR #217 merged the same day
  (`8ed1650`), adding the DOC007 and DOC008 checks that close F-B21-13.
  `pip-audit` still reports its advisories without failing the gate, by
  design (F-B21-3). The root-hygiene side task is **closed**: the owner
  rejected the audience-banner scheme on 2026-08-20, and the config-file
  verdict landed in `DEPLOY.md`.
  Earlier context, still true: **PR #171 merged to `main` on 2026-08-19**
  (`bb187ae`, rebase merge) with zero unresolved review threads after eight
  rounds; `wip/batch-21` was realigned to it. `BATCH21_DEFINITION.md` was
  amended the same day so the batch gate can fail on frontend work.
  PR #169 merged 2026-08-08 shipping the
  repository-integrity gate and read-only worktree guard, resolving
  F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2; three guard files exceed their
  directory peer caps, accepted as a deviation and tracked as F-WORKTREE-4,
  not silently. PR #170 merged 2026-08-12 (`5b060a2`), settling the guard and
  docsync sources the audit reads.
- **Next action:** the WP-7 refinement the owner asked for is implemented and
  verified, so the earlier note that this work was cut off before completion is
  discharged. The disclosure step is 25 (was 50), and the back-to-top control
  now collapses its panel as well as scrolling. `pytest -q` -- **1020 passed**;
  the two-engine frontend gate -- 26 checks passed in 47 runs across chromium
  and firefox.
  One conflict is still open and belongs to the documentation pass: the approved
  spec `docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`
  still says "stacked, full-width reason sections", while the owner ruled
  side-by-side on 2026-09-11 and the shipped page is side-by-side. Correct the
  spec and this bullet before beginning WP-8, or an agent following them will
  rebuild the rejected layout. WP-8 starts only on owner direction.

- **Owed before Phase 2:** the commits owed before Phase 2 are recorded only in
  the design-system plan's Progress section
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`):
  the architecture-diagram rebuild. The F-B21-51 slice-1 refactor landed as
  `95e0896` and that plan's own move as `c277728`. An agent that bootstraps from
  this section reaches the specification conflict above but not the commit debt.
- **Traversal record:** the design-system plan was traversed exhaustively on
  2026-09-11; the findings are
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- **Results follow-up:** F-B21-47 is implemented on `test`; the 925-test suite
  and focused frontend-gate unit coverage pass. F-B21-48 records the separate
  persistent Last.fm scrobble-cache candidate; it does not expand this
  frontend change.
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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

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

### 2026-08-20 - F-SWE-2 UTC album-year window fixed (Batch 21 WP-0)

- Scope: cleared the only F-SWE-1 migration blocker in the standalone
  prerequisite after WP-0 and before WP-1. No Tailwind or WP-1 work started.
- Plan vs implementation: as planned. `orchestrator.py` now imports
  `timezone` and passes `tzinfo=timezone.utc` to both listening-year boundary
  constructors. The regression drives the public `fetch_top_albums_async`
  workflow, simulates UTC-5 semantics only for naive constructors, and checks
  the literal UTC epoch values sent to the mocked Last.fm boundary. Existing
  mock track fixtures now construct their UTS values in explicit UTC too.
- TDD red evidence: before the production fix,
  `pytest -q tests/services/test_lastfm_logic.py::test_fetch_top_albums_uses_utc_year_window_on_non_utc_host`
  failed twice with the same boundary shift:

  ```text
  AssertionError: expected await not found.
  Expected: mock('testuser', 1704067200, 1735689599, progress_cb=None)
    Actual: mock('testuser', 1704085200, 1735707599, progress_cb=None)
  ```

  After the fix, the targeted test passed, and the complete test module passed
  with 8 tests.
- Deviations: no implementation deviation. Pre-push whole-file review corrected
  the README test badge and module inventory plus two forward-looking WP-7
  claims that still described WP-7 as the first test-count change. The same-day
  docsync source order gives live side-task entries precedence over
  current-batch entries, so the document-map entry below carries a later-count
  addendum that points back to this entry. Its original 590-test completion
  result stays unchanged.
  F-SWE-3 remains P2, F-B21-1 remains P1 without blocking WP-1, and root
  hygiene remains deferred until after WP-1.
- Validation: `pytest -q` -- **591 passed**, 3 warnings.
  `pre-commit run --all-files` -- all hooks pass; all tracked Markdown hashes
  match before and after the hook. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: F-SWE-2 is resolved. WP-1 is next; pause for owner review
  of this commit before starting it.

### 2026-08-20 - PR #172 frontend-gate contract made executable (Batch 21 WP-0)

- Scope: addressed the two actionable P1 review threads on the active Batch 21
  definition before WP-1. This is design and state documentation only; no
  frontend runtime or WP-1 work started.
- Verification of the review findings: criterion 9 required the frontend gate
  at every WP while the validation section created it at WP-2, making WP-1
  impossible to complete. The planned Python script also had no declared
  Playwright package, browser provisioning, CI setup, or callable bridge to
  the machine-local MCP providers.
- Plan vs implementation: owner-approved as designed. The three existing
  repository gates remain mandatory at every WP and the frontend gate starts
  at WP-2. That WP pins `playwright==1.62.0` in `requirements-dev.txt`, installs
  its matching Chromium build explicitly on the developer machine and Linux
  CI, runs the repository gate in the Quality Gate, and documents setup in
  README and DEVELOPMENT when the runtime lands. The script owns an ephemeral
  loopback Flask server and always tears it down; missing tooling fails with an
  actionable command rather than downloading silently. No Node project,
  pytest plugin, or MCP dependency is introduced.
- Review disposition outside this commit: the nuanced F-SWE-3 thread received
  the owner-approved ROI explanation and was resolved without expanding WP-7.
  F-SWE-3 remains open at P2; operational Spotify failures do not become an
  unmatched-page `reason_code`.
- Deviations: none. The active definition is the canonical design document, so
  no duplicate `docs/superpowers/specs/` file was created.
- Validation: qualified `pytest -q` -- **591 passed**, 3 warnings; all
  pre-commit hooks passed; tracked-Markdown MD5 manifests were identical
  before and after the hook run; `doc_state_sync.py --check` passed with only
  the expected active-batch root-definition warning.
- Forward guidance: land PR #172, then start WP-1. The Playwright dependency,
  browser download, workflow change, gate implementation, tests, README, and
  DEVELOPMENT updates all land together at WP-2.

### 2026-08-20 - Tailwind and daisyUI toolchain completed (Batch 21 WP-1)

- Scope: added the Node-free pinned Tailwind/daisyUI toolchain, themes,
  committed compiled CSS, and Linux CI rebuild. No templates changed and
  `scripts/dev/dev_start.py` remains unchanged.
- Plan vs implementation: Tailwind v4.3.3 and daisyUI v5.7.19 pin seven
  platform assets -- Windows x64, macOS x64 and arm64, Linux x64 and arm64
  for glibc and musl -- plus `daisyui.mjs` and `daisyui-theme.mjs`. Every
  artifact is SHA-256-verified on every use; one verified atomic replacement
  follows an invalid cache entry. The source restricts daisyUI to button,
  card, modal, toggle, input, select, tab, toast, and alert; it locks the
  reviewed light/dark palette, type scale, 4px spacing ladder, 8/14/999px
  radii, and both `--bars-color` aliases. CI caches `scripts/bin/` by runner
  OS, architecture, and build-script hash.
- TDD evidence: initial collection failed for the missing
  `scripts.dev.tailwind_build` module; cache tests first failed on the absent
  cache interface; source-contract tests first failed on absent
  `static/css/tailwind.src.css`. Focused green commands were
  `pytest tests/scripts/dev/test_tailwind_build.py -q`,
  `pytest tests/scripts/dev/test_tailwind_build_cli.py -q`, and
  `pytest tests/scripts/dev/test_tailwind_build.py tests/scripts/dev/test_tailwind_build_cli.py -q`
  (35 passed).
- Reproducibility: Windows and the `python:3.13-slim` headless glibc-Linux
  probe both produced SHA-256
  `481230ebf858f2fe3b0497c7247be3532917e1c6432cd2bde0940721e81d1b09`.
  The Quality Gate is configured to rebuild with the same Linux x64 asset.
  It has not run yet, because the branch is unpushed.
- Documentation: DEVELOPMENT owns commands; README links rather than copying;
  BATCH21_DEFINITION owns the CI decision; exact pins and digests live in code.
- Deviations: owner-approved fail-closed hardening distinguishes only `None`
  as omitted, so explicit empty platform values cannot probe the live host,
  with deterministic `required_artifacts()` matrix coverage. Same-date
  live-side precedence also required this minimal pointer addendum and the
  deterministic rotation of one older non-current entry; point-in-time history
  was not rewritten. For the four final-review peer-size findings, the owner
  ruled that the cap is flexible when it prevents only files that are
  tremendously out of place or becoming god-files. The plan remains one
  reviewed execution contract, generated `tailwind.css` is indivisible, the
  builder owns one cohesive standard-library toolchain responsibility, and its
  tests stay beside that public seam. None is a god-file or out of place, so
  no split was made and `AGENTS.md` remains unchanged. Final review also
  found both musl pins unreachable: `platform.libc_ver()` reports nothing on
  musl and `libc` on some glibc hosts, so the plan's direct
  `platform.libc_ver()[0]` check gave way to `_normalize_libc()` and
  `_detect_libc()`, which probes for the musl loader. Verified in Docker on
  `python:3.13-alpine` and `python:3.13-slim`. The plan keeps its original
  code listing as the reviewed design.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. All pre-commit hooks
  passed; tracked-Markdown manifests were identical before and after the hook;
  `doc_state_sync.py --fix` exited 0 with the expected active root-definition
  warning for `BATCH21_DEFINITION.md`.
- Forward guidance: owner review first; the root-hygiene side task is next;
  WP-2 follows it. WP-2 keeps the cache, removes the direct CI build step only
  when its drift hook lands, and adds the first Tailwind-consuming template.

### 2026-08-23 - Base shell, error-page pilot, and two new gates (Batch 21 WP-2)

- Scope: the first Tailwind template. Added the standing header bar, moved
  Bootstrap and `global.css` into a per-page block, migrated `error.html`,
  and built the two gates that protect the rest of the migration.
- Plan vs implementation: the plan is
  `docs/superpowers/plans/2026-08-22-batch21-wp2-base-shell.md`, 13 tasks in
  five commits. All 13 landed.
  - The Adobe Fonts reversal was recorded first, then the theme tokens moved
    to kit `rwy8ghw`. `--font-weight-medium` and `--font-weight-semibold`
    were deleted: the kit serves 300, 400 and 700 only, so those two tokens
    could only ever produce a synthesized fake weight.
  - `tailwind-css-drift` rebuilds and diffs on every commit. It sets
    `always_run` and `pass_filenames: false` because the top-level exclude
    filters out `static/`, so a filename-driven hook would never run on the
    one file it exists to check.
  - `scripts/dev/frontend_gate.py` serves the app on a loopback port it owns
    and drives Chromium. Four checks: exactly one framework stylesheet per
    page, `--bars-color` equal to the theme primary with no cool grey left,
    the theme surviving a reload, and all five kit families resolving as
    loaded faces.
  - `base.html` sets `data-theme` before first paint, links the kit, and
    carries the header bar. `theme.js` dual-writes `data-theme` and
    `.dark-mode` until WP-8 retires the second write.
- Deviations, each owner-approved or recorded here:
  - **The legacy CSS block defaults ON.** The plan left it empty and had each
    unmigrated page opt in. The owner inverted it on 2026-08-23, so a
    forgotten template keeps its theme and only a migrated page opts out.
    Forgetting is now safe instead of silently broken.
  - **`templates/inline/scrobble_scope_lockup_inline.svg` is new.** The
    design system reserves the lockup for the header and keeps the full mark
    with tagline for social use. No lockup asset was imported, so this one is
    derived from the existing wordmark by removing the tagline group and
    tightening the viewBox. The letterform paths are unchanged.
  - **`tests/test_template_shell.py` is new and not in the plan.** The plan
    says nothing in `pytest` catches a missed legacy block. Twenty tests now
    do, across all five templates. Emptying the block in `base.html` fails
    eight of them.
  - **The direct CI Tailwind build step was removed** rather than kept beside
    the hook, which is what the batch definition's CI decision says. A digest
    print survives as a separate diagnostic step, because the hook proves
    only that the committed file matches a rebuild on that runner and says
    nothing about Windows against Linux.
  - **`tests/conftest.py` was fixed alongside the gate.** Both used
    `os.environ.setdefault` for `SECRET_KEY`. Actions sets that variable to
    an empty string when the secret is missing, and empty is present, so
    `setdefault` does nothing and the app refuses to boot.
  - **The gate's theme-persistence check runs on a migrated page**, not the
    index, because the welcome modal's backdrop covers the header there.
    Filed as `F-B21-11`; WP-3 deletes that modal.
- Findings: `F-B21-2` and `F-B21-7` resolved, and `F-AUDIT-1` resolved by the
  44px header targets. `F-B21-10` filed -- every error page reports 400
  whatever the real status, and the fix lives in files WP-7 reserves.
  `F-B21-11` filed. Neither is mirrored to a GitHub issue; `F-B21-9` records
  that the mirror is manual.
- Known gap, recorded rather than fixed: the gate's four browser checks have
  no unit coverage, though its runtime does. A check that quietly stops
  asserting looks exactly like a check that passes, so this is worth closing
  with one stub-page assertion each in a later work package.
- Validation: `pytest -q` -- **666 passed**, 3 warnings. All 11 pre-commit
  hooks pass, and `git write-tree` is identical before and after. The
  frontend gate reports `4 checks passed`, and it was proven able to fail:
  it reported ten real failures before the shell landed.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: owner visual review of the error page in both themes
  before WP-3. Do not push the gate commit on its own -- the workflow runs on
  push to `wip/**`, and the gate fails until the shell commit lands with it.
  WP-3 takes the index page, deletes the welcome modal, and adds its page to
  `MIGRATED_PAGES` in the gate.

### 2026-08-25 - Index page migrated to Tailwind (Batch 21 WP-3)

- Scope: rebuilt `index.html` on Tailwind and daisyUI, deleted the welcome
  modal and the `bootstrap.Popover` hints, extracted three Jinja partials,
  and moved the index into every frontend-gate check. WP-6 is absorbed here
  (owner, 2026-08-23): the heatmap has no page of its own, so its form,
  loading panel and result frame all live on this page.
- Plan vs implementation: the plan is
  `docs/superpowers/plans/2026-08-23-batch21-wp3-index-page.md`, 16 tasks in
  six commits. All 16 landed, in eleven commits rather than six -- five
  unplanned ones came out of owner visual review and two Codex review
  rounds. That plan's Progress section carries the commit table.
- Deviations, fifteen in total and all listed in the plan. The ones that
  change a contract:
  - **WP-6 absorbed into WP-3.** Its stub heading must keep the words
    "absorbed into" verbatim; `WP_SKIPPED_RE` in DOC007 recognises that
    phrasing and two others, and nothing else.
  - **`limit_results` stays a visible field**, reversing definition
    decision 3. Owner ruled that how many albums you list is not part of
    what counts as listened.
  - **The type stack is Adobe Fonts**, not self-hosted; that reversal
    predates this WP and is recorded in `docs/design/RECONCILIATION.md`.
  - **`/validate_user` is kept** against the design README's simpler
    "more than two characters" rule, because the definition requires
    validation parity.
  - **The heatmap geometry ruling is Claude's**, not the owner's: 14px
    cell, 2px gap desktop and 1px mobile, radius 2px, `--heatmap-empty`
    `#e8e2d6` / `#262230`. It resolves `RECONCILIATION.md` section 7.
  - **The index is full bleed and the hero scales past 1500px**, both past
    the design's stated 560px mark and 42px headline. Owner ruled both
    after seeing 538px of dead space at 1600, 2000 and 2560 alike.
  - **`Save image` is a new feature the plan never scoped**, about 120
    lines drawing a canvas by hand. Owner approved it knowing the labels
    inside the serialized SVG fall back to a plain monospace stack.
  - **Stylesheet units moved to rem** for type and spacing, px kept for
    thin detail. Owner rule, 2026-08-25; `AGENTS.md` "UI and
    Accessibility Rules" item 1 carries it and `RECONCILIATION.md`
    section 11 records why it overrides the design snapshot.
  - **`error.css` and `shell.css` were edited**, though the plan assigns
    them to WP-8 and WP-2. The touch-target check found 40px buttons on
    the error page, and `shell.css` loads on every page so leaving it in
    px put px spacing around rem type on the migrated one.
- The plan's one predicted red never happened. `check_stylesheet_isolation`
  counts framework stylesheets rather than naming which framework a page
  should carry, so a page that swaps one for the other stays green.
- Gates grew with the work. The frontend gate went from four checks at a
  single desktop viewport to eight across three device profiles -- a 1280
  mouse, a 390 touch phone and a 1280 touch screen. Two checks are new:
  touch targets, which drives the page into five states before measuring
  because most controls start hidden, and initial visibility, which asserts
  computed display rather than a class name. A third, validation feedback,
  was added after review found a defect no gate could see.
- Reviews: Codex raised twelve comments across three rounds on PR #218.
  Every one was valid. One was declined on its premise -- it claimed the
  closed thresholds disclosure gave its controls zero-sized boxes, and
  deleting their sizing turns the gate red, so the controls were being
  measured -- and its remedy was applied anyway as insurance.
- Findings: `F-B21-11` and `F-B18-12` resolved. `F-B21-5` updated; its SMIL
  and mode-pill items are resolved. `F-B21-4` item 1 is decided and the
  finding stays open for items 2 to 4. Five filed: `F-B21-14` through
  `F-B21-18`.
- Validation: `pytest -q` -- **749 passed**, 3 warnings. All 11 pre-commit
  hooks pass with an identical `git write-tree` either side. The frontend
  gate reports `8 checks passed in 13 runs across desktop, mobile, wide
  touch`, and every new check was proved able to fail by mutation.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: WP-4 takes `loading.html`. It needs a GET route before
  the gate can see the page it migrates -- `LEGACY_PAGES` is empty because
  the three remaining templates render only from a POST with session state.
  `templates/partials/_loading.html` already exists and is framework-neutral,
  built a work package early; WP-4 consumes it rather than writing one.
  `F-B21-17` proposes the deterministic drift check that would have caught a
  third of this batch's review comments, and the owner approved building it
  after this work package closes.

### 2026-08-27 - Unified loading and recent-result recovery completed (Batch 21 WP-4)

- Scope: migrated the album loading route to Tailwind and the shared wait
  panel, completed the shared polling hairline, and made Results, Unmatched,
  and Heatmap recover the latest valid run at their clean routes.
- Plan vs implementation: the album and heatmap clients now share the same
  pinwheel, three-pixel determinate hairline, and backend-owned phase copy.
  The browser gate creates real album and heatmap jobs and drives each client
  through success, retryable failure, and terminal failure.
- Owner-review refinements: grouped Home with Heatmap and Results with
  Unmatched; renamed Album release filter to Release filter; removed redundant
  form-help icons; tightened the empty state; removed selected-control shadows;
  kept index mode copy on a quick cross-fade; and scaled the loading cluster
  up and down as one composition. The compact shell wordmark now returns when
  Heatmap loading or results replace the landing hero. The album wait screen
  no longer repeats the pinwheel's loading cue as a heading. At desktop widths,
  the hero and form now scale up together by 7.5%; tablet and mobile keep the
  existing composition. Both landing modes now place their mono descriptor
  below the serif heading, matching the Heatmap result hierarchy.
- Backend hardening: Heatmap stores its payload before exposing 100% progress,
  reports live page/scrobble/day facts to the loading view, and refreshes an
  expired AJAX request token once before retrying. A real browser run completed
  from the form through polling to a 365-day result.
- Deviations: the owner reversed the old no-progress-bar rule in favour of one
  slim hairline below the pinwheel. Destination routes no longer carry job IDs;
  separate browser-session pointers recover album and heatmap jobs instead.
  Jobs expire after two idle hours, and access refreshes that window. Explicit
  job IDs remain compatibility inputs during the strangler.
- Validation: `pytest -q` -- **840 passed**, 3 warnings. The frontend gate
  reports `19 checks passed in 27 runs across desktop, mobile, wide touch`,
  including exact 1080p-to-4K component-scale parity.
  JavaScript syntax checks, all pre-commit hooks, and
  `doc_state_sync.py --check` pass.
- Forward guidance: owner review is paused after the first annotation pass.
  Resume minor Firefox and Impeccable Live refinements at 1080p and 1440p
  before WP-5. Keep the latest-run session contract when the Results and
  Unmatched templates migrate; do not reintroduce query strings into the
  header pills.

### 2026-09-06 - Dedicated unmatched empty state unified and verified (Batch 21 WP-4)

- Scope: completed Task 5 of `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`, routing `/unmatched` with absent or expired jobs to a dedicated borderless empty state matching Results and Heatmap.
- Implementation:
  - Created `templates/unmatched_empty.html` using the shared `.empty-page` and `.empty-state` structure, purple indicator bar, Task 5 Step 3 spec copy ("Run an album search to find albums that need a review."), and action link to `/`.
  - In `scrobblescope/routes.py` `_render_unmatched_page`, routed absent and expired saved jobs to `unmatched_empty.html` (with expired message and session pointer eviction via `_get_validated_job_context`) instead of the generic `_render_no_job_state` error card. Valid populated runs and valid 0-row runs remain on `unmatched.html`.
  - Added route test in `tests/test_routes.py` verifying that an expired `latest_album_job_id` returns 200, `data-empty-state="unmatched"`, pops the session key, and renders no error code. Mutest verified: bypassing the handler caused immediate RED (`AssertionError`), confirmed GREEN on restoration.
  - Extended `scripts/dev/frontend_gate.py` `check_destination_empty_states` to assert `/unmatched` contains no `.card`, no box shadow on `.empty-state`, and a visible, usable Home action link.
- Validation: `pytest -q` -- **915 passed**, 5 warnings. `python scripts/dev/frontend_gate.py` passed all 23 checks in 64 runs across Chromium and Firefox. All pre-commit hooks and `doc_state_sync.py --check` pass.
- Forward guidance: proceed to Task 6 (accessibility pass).

### 2026-09-06 - Results leaderboard rebuild and interactive polish completed (Batch 21 WP-5)
- Scope: migrated `templates/results.html` and `static/js/results.js` to Tailwind CSS v4 and daisyUI, implementing the canonical Results Leaderboard with single column layout, sticky side-rail, Top Artist Spotlight with gradient scrim, Instrument Serif play counts, larger artwork, in-flow shell header, and modal removal.
- Implementation:
  - Replaced legacy Bootstrap container/table markup in `templates/results.html` with responsive Tailwind semantic structure:
    - Clean editorial headline with exactly one purple italic accent on `username` and min-height reserve; eliminated eyebrow kicker above `<h1>`, placing a clean subtitle descriptor below.
    - Touch-accessible action buttons (>= 44px targets) with navbar-style rounded rectangles (`rounded-[var(--radius-field,8px)]`), normal sentence-case, sans-serif typography (`font-sans text-sm font-normal`), and subtle unified card fills. Single desktop flex row with masthead.
    - Compact symmetrical `StatBlock` mini-table with structural hairline dividers, centered values, and micro-labels (`10px` uppercase).
    - Active filter tags relocated below the stats card directly above the leaderboard grid with high-contrast borders and surfaces.
    - Two-column desktop layout (`lg:grid lg:grid-cols-12 lg:gap-8`):
      - Left column (`lg:col-span-8`): Semantic `<table>` (`#results-table`) styled as an editorial chart with transparent `<thead>`, clear mono rank numerals with hover glow (`--rocket-5`), enlarged artwork covers, Spotify links, and scaled Instrument Serif play counts / monospace durations. Full ISO date day precision preserved in `data-export`.
      - Right column (`lg:col-span-4`): Sticky side rail with full runway alongside rows 01-14+; interactive segmented toggle (`[ Track Plays ] [ Listening Time ]`) for bidirectional client-side re-sorting with responsive duration strings (`.desktop-val` vs `.mobile-val`), Top Artist Spotlight card with ~16:10 photograph container, bottom gradient scrim overlay, artist name headline, and Spotify link; and Audit & Discovery card linking to `/unmatched`.
    - Removed duplicate `#rail-back-to-top` button from sidebar, preserving the canonical centered `#back-to-top` footer button.
    - Converted `.site-header` in `static/css/shell.css` from `position: fixed` to `position: relative` (in-flow) and removed `padding-top` on `body`, reclaiming vertical viewport height.
    - Removed `#unmatched-modal` and wired all unmatched actions to `/unmatched`.
  - Backend & hydration:
    - Added `fetch_spotify_artist_spotlight` in `scrobblescope/spotify.py` and exposed `GET /api/artist_spotlight` route in `scrobblescope/routes.py` with comprehensive unit and fallback tests in `tests/test_routes.py`.
    - Added progressive client hydration in `static/js/results.js` (`loadArtistSpotlight`) to dynamically update the spotlight image.
    - Computed and passed `has_durations` from `scrobblescope/routes.py` to enable the Listening Time sort toggle, with template fallback.
    - Updated row `data-` attributes on leaderboard `<tr>` (`data-play-time`, `data-play-time-mobile`, `data-play-time-seconds`).
  - Added interactive toggle, glow, and spotlight styles to `static/css/results.css`.
  - Added `results.html` to `MIGRATED` set in `tests/test_template_shell.py` and rebuilt `static/css/tailwind.css`.
- Validation: `pytest -q` -- **922 passed**, 5 warnings. `python scripts/dev/frontend_gate.py` passed all 23 checks in 64 runs across Chromium and Firefox. All 12 pre-commit hooks and `doc_state_sync.py --check` pass.
- Forward guidance: proceed to WP-7 (unmatched page + reason_code backend fix).

### 2026-09-10 - Unmatched page reconciled after review (Batch 21 WP-7)

- Scope: completed the local WP-7 implementation, review reconciliation, and
  owner-approved post-commit cover-containment follow-up. The backend contract,
  backend finding fix, UI rebuild, and final rendering fix remain distinct
  rollback units.
- Implementation:
  - Backend contract (`feat(unmatched): Add stable reason_code to the unmatched contract`, committed as `b3e3e96`):
    - Added `scrobblescope/unmatched.py` defining canonical reason constants
      `REASON_RELEASE_SCOPE` and `REASON_NO_SPOTIFY_MATCH`, human category metadata
      (title, description, badge, fix hint), and pure grouping helper
      `group_unmatched_albums` with deterministic sorting and fallback for legacy jobs.
    - Updated `scrobblescope/orchestrator.py` search and release phases to record
      stable `reason_code` alongside prose reasons on unmatched items.
    - Updated `scrobblescope/routes.py` `_render_unmatched_page` to group by
      `reason_code` and pass `reason_metadata` and `reason_counts` to template.
    - Added unit and adversarial mutation tests in `tests/test_unmatched.py`,
      `tests/services/test_orchestrator_fetch_spotify.py`,
      `tests/services/test_orchestrator_helpers.py`,
      `tests/services/test_orchestrator_fetch_and_process.py`, `tests/test_heatmap.py`,
      and `tests/test_routes.py`.
  - Frontend rebuild (`feat(ui): rebuild unmatched page on tailwind`):
    - Rebuilt `templates/unmatched.html` opting out of legacy CSS; added masthead
      with editorial headline, purple italic username, and >= 44px navigation
      actions; summary pill bar; Screen 5 reason cards grid with category badges,
      Instrument Serif/Gotham counts, semantic table with numbered rows,
      `unmatched-overflow` client expander for groups with > 10 albums, and
      single-line 9px uppercase mono-narrow tracking fix line.
    - Preserved existing pipeline data on each audit row: cover artwork,
      Spotify destination, and Last.fm play count. Rows without cached album
      artwork progressively reuse `/api/artist_spotlight`; intersection-based
      loading and a per-artist request cache avoid eager or duplicate calls.
    - Post-commit rendering review replaced undeclared `w-10`/`h-10` and
      `md:w-11`/`md:h-11` utilities with the explicit fixed-size containment
      pattern used by `results.css`. Covers, portraits, and fallbacks now hold
      the design-prescribed 40px mobile / 44px desktop square at 4px radius.
    - Replaced `static/css/unmatched.css` with token-based rules for min-height,
      surface cards (`--ss-surface-card`), borders, and coarse pointer touch targets.
    - Implemented keyboard-accessible expander toggle and lazy artist-portrait
      hydration in `static/js/unmatched.js`.
    - Completely removed `bootstrap.bundle.min.js` and legacy Bootstrap dependencies.
    - Added `unmatched.html` to `MIGRATED` in `tests/test_template_shell.py`,
      `"/unmatched"` to `MIGRATED_PAGES`, and a populated-report browser check
      in `scripts/dev/frontend_gate.py`. The check drives both expander states
      and verifies Spotify, play-count, artist-portrait hydration through the
      existing full-stack route, and computed type-role output.
    - Corrected category badge and table cell padding to whole scale steps (`py-1`,
      `py-2`), resolving the `F-B21-52` fractional Tailwind spacing trap on this page.
    - Recompiled `static/css/tailwind.css`.
- Deviations discovered while the backend work was still in progress:
  - **F-B21-56:** the first backend commit left Spotify total-failure detection
    coupled to the old English reason. The local follow-up checks
    `REASON_NO_SPOTIFY_MATCH`, retaining prose only as a legacy-job fallback.
  - **F-B21-1:** review of the touched worker boundary confirmed that event-loop
    setup could leak an acquired job slot. The local follow-up moves setup into
    `try...finally` in both album and heatmap workers and nests cleanup so a
    `loop.close()` failure cannot skip `release_job_slot()`. Both sequence
    diagrams and adversarial tests move with the fix. This intentionally
    supersedes the plan's original claim that `heatmap.py` would stay untouched.
  - **Audit-row enrichment:** the frontend preparation retains cover artwork,
    Spotify IDs, and play counts already available at both unmatched producer
    sites. When cached album artwork is absent, the browser progressively uses
    the existing `/api/artist_spotlight` route. The permanent browser gate and
    producer tests own that expanded presentation contract.
  - **Commit boundary:** the fixes above are backend changes discovered after
    the backend commit. The owner authorized staging and committing on
    2026-09-10; the non-rewrite path keeps them in a separate fix commit before
    the independently revertible UI commit. The fix is `ba5f9fe`.
  - **Rendered cover containment:** visual review after `968eaa0` showed album
    art expanding to the table's intrinsic width. `tailwind.src.css` disables
    dynamic spacing and declares no steps 10 or 11, so those template utilities
    emitted no rules. A computed-style regression check reproduced 302x152px,
    and the Results-pattern fixed geometry restores 44x44px on desktop.
- Validation: `pytest -q` -- **986 passed**, 2 warnings across 41 test modules.
  `scripts/dev/frontend_gate.py` passed all 26 checks in 46 runs
  across Chromium and the Firefox static-assets canary. The populated-report
  check covers both expander states, 44px cover containment, and computed type
  roles. Its focused Chromium loop failed at 302x152px before the remedy and
  passed afterward; a 2000x1000 rendered capture confirms the repaired page.
  Targeted WP-7 coverage passed 345 tests; `node --check
  static/js/unmatched.js` passed. All 10 pre-commit hooks and
  `doc_state_sync.py --check` pass.
- Forward guidance: the owner approved the rendering remedy and authorized
  publication on 2026-09-10. Push to
  `origin/test`, verify the remote ref, and do not begin WP-8 without direction.

### 2026-09-11 - PR #231 Linux cleanup tests made portable (Batch 21 WP-7)

- Scope: diagnosed the failed Quality Gate on PR #231 and repaired the two
  worker-cleanup tests without changing production behavior or UI rendering.
- Root cause: GitHub Actions checked the PR merge commit on Ubuntu, where
  `asyncio.ProactorEventLoop` is absent. Both new cleanup tests patched that
  Windows-only attribute unconditionally, so pytest stopped with two
  `AttributeError` failures after pre-commit had passed.
- Implementation: both tests now use `patch(..., create=True)` for the
  platform-specific loop class. Their mocked `run_until_complete` also closes
  the produced coroutine, eliminating the resource warnings from the cleanup
  path under test.
- Pre-commit audit: the hook suite is behaving as configured. It checks Python
  lint/format, document state, generated Tailwind drift, and worktree alignment;
  it does not run pytest or emulate Linux APIs. Adding the local Windows suite
  to pre-commit would still miss this defect, so the repair belongs at the
  cross-platform test seam rather than as a new hook.
- Validation: the two focused tests pass both normally and after removing
  `asyncio.ProactorEventLoop` from the process; `pytest -q` reports **986
  passed** with no warnings. Final pre-commit, docsync, and remote Quality Gate
  evidence follow before completion is claimed.
- Forward guidance: publish this review-fix commit, confirm PR #231 is green,
  then amend the WP-7 scope and plan for the owner-requested threshold reason
  and horizontal report design before implementation.

### 2026-09-11 - Threshold and horizontal report extension approved (Batch 21 WP-7)

- Scope: amended WP-7 before implementation to retain albums rejected at the
  play/unique-track boundary and restyle unmatched groups as full-width
  horizontal report sections.
- Owner decision: one stable `below_threshold` group covers either failed
  minimum. An album failing both appears once and retains its actual plays,
  unique-track count, and failed-threshold list.
- Design authority: current `results.html`, `results.css`, and computed browser
  behavior win over the dated design snapshot. Unmatched will mirror Results'
  composition, scale, surface, actions, and table rhythm while removing its
  own eyebrow and purple italic username.
- Architecture: partition after Last.fm aggregation and before Spotify. Store
  threshold exclusions through the existing unmatched repository, preserving
  the current Spotify cost boundary and the lazy `/api/artist_spotlight`
  fallback for missing art.
- Documentation: added the approved design and supplemental implementation
  plan, amended the active definition, and retained the original WP-7 plan as
  the record of the completed first pass.
- Validation: documentation gates and implementation evidence follow in the
  commits that execute the extension.
- Forward guidance: execute backend Task 1 first, then the horizontal Results-
  aligned UI task. Keep each as an independently revertible commit.

### 2026-09-11 - Below-threshold albums retained (Batch 21 WP-7)

- Scope: completed backend Task 1 of the approved WP-7 extension without
  changing UI rendering.
- Implementation: Last.fm aggregation now partitions eligible albums from
  exclusions that fail plays, unique tracks, or both. Each excluded album is
  stored once with the `below_threshold` reason code, actual counts, configured
  minimums, and failed-threshold list.
- Pipeline boundary: exclusions are persisted only after a successful Last.fm
  response and before the eligible-empty terminal state. They never enter
  Spotify processing; an all-excluded job completes normally with empty Results
  and a populated unmatched report.
- Validation: focused partition, Last.fm, orchestrator, and route coverage
  passes. `pytest -q` -- **989 passed**. Repository gate evidence is refreshed
  before commit.
- Forward guidance: execute Task 2, using current Results source and computed
  output as the visual authority for the horizontal unmatched report.

### 2026-09-11 - Side-by-side unmatched horizontal reports and 500-album cap unified (Batch 21 WP-7)

- Scope: completed Task 2 of the WP-7 extension. Reconciled two extension documents
  (`2026-09-11-batch21-wp7-threshold-horizontal-report-extension.md` and
  `2026-09-11-unmatched-threshold-horizontal-report-design.md`) against
  `docs/design/designsystemaudit.md` (canonical source of truth) and owner directives.
  Replaced stacked reason sections with responsive side-by-side horizontal report panels
  sorted by unmatched reason, reconciled design tokens against `results.html`, and
  diagnosed and resolved the unbounded 500-album cap defect in `orchestrator.py`.
- Architectural context & plan reconciliation:
  - Spec Reconciliation: The initial design spec proposed full-width stacked reason sections
    ("stacked, full-width reason sections instead of the current three-column card grid").
    The owner explicitly superseded this layout directive: "There should be more than one
    horizontal report; they should be sorted by the unmatched reason. The UI should be like
    results.html, and do considere the designsystemaudit.md as cannonical source of truth.
    They should not be stacked, but side-by-side".
  - Canonical Design System (`docs/design/designsystemaudit.md`): Live styles do not use
    the unmigrated Claude Design token layer (`--surface-page`, `--text-body`, etc., which
    collide with Tailwind v4 namespaces). The live design system uses three layers: daisyUI
    slots, the `--ss-*` extension set, and Tailwind `@theme static`.
- Implementation details:
  - Side-by-Side Responsive Layout: The `.unmatched-groups` container arranges reason reports
    side-by-side in a responsive grid (`grid-cols-1 lg:grid-cols-3` or `lg:grid-cols-2`
    depending on reason count, `gap-6 items-start`). Order is deterministic: `below_threshold`
    -> `release_scope` -> `no_spotify_match`. On desktop (>=1024px), reports sit side-by-side
    sharing identical top offsets; on mobile (<1024px), the grid collapses to a single column
    preventing horizontal page scroll.
  - Results Design Tokens & Typography:
    - Surface: `--results-surface` (`color-mix(in srgb, var(--color-base-100) 50%, var(--ss-surface-sunken))`).
    - Borders & Radius: 1px hairline `var(--ss-border-default)`, `--radius-sm` (8px / 0.5rem) on panels,
      and `--radius-xs` (4px / 0.25rem) on artwork.
    - Artwork Dimensions: 44px desktop (`2.75rem`), 40px mobile (`2.5rem`) with explicit
      containment (`aspect-ratio: 1/1; object-fit: cover`).
    - Typography Roles: Instrument Serif (`font-serif`) for page title, Gotham figure numerals
      (`--font-figure`) for album counts adhering to the Role Segregation Rule (audit L943-L950,
      D-17), Input Mono (`--font-mono-narrow`) for ranks and 9px uppercase fix hints, Akzidenz
      Grotesk (`font-sans`) for table body/labels, and neutral headline username without italics
      or purple accent.
    - Proportional Scaling: `syncResultsScale()` reading `--results-base-rem: 75` on
      `.unmatched-page`, scaling `--results-scale` with window resizing / `ResizeObserver`
      (matching Results dynamic scaling in audit L228-L232).
  - Disclosure & Async House Pattern:
    - Preserved 10-row disclosure with Results-style ghost buttons and album counts.
    - Artist portrait progressive hydration via `/api/artist_spotlight` fallbacks. Hardened
      with post-`await` name verification (`artwork.dataset.artistName?.trim() === artistName`)
      to strictly uphold the house stale-response guard pattern identified in `designsystemaudit.md`
      L1011-L1021.
    - Noted for WP-8: `.dark-mode` class write on `<body>` is actively observed by `heatmap.js`
      (audit L841-L868) and is preserved intact.
  - Backend Safety Cap:
    - Diagnosed defect via `/diagnosing-bugs`: `_PLAYTIME_ALBUM_CAP = 500` was only applied
      when `sort_mode == "playtime"`. In default playcount mode, unbounded thousands of
      albums bypassed slicing, exhausting Spotify API rate limits and freezing the DOM on
      `results.html`.
    - Defined `_MAX_ALBUM_CAP = 500` in `scrobblescope/orchestrator.py` (aliasing
      `_PLAYTIME_ALBUM_CAP`) and enforced it unconditionally in `_apply_pre_slice` across all
      sort modes (`playcount` and `playtime`).
  - Design Snapshot Test: Added `"designsystemaudit.md"` to `REPOSITORY_OWNED_PATHS` in
    `tests/test_design_snapshot.py` to preserve the 61-file design manifest digest.
- Validation:
  - `frontend_gate.py` updated to verify desktop side-by-side layout (`groupTops[0] === groupTops[1]`,
    `gridColumns === 3`) and mobile single-column stacking; passed all 26 checks across 47 runs
    in Chromium and Firefox.
  - `pytest -q` -- **990 passed** (up from 989; added tests for unified `_MAX_ALBUM_CAP` in
    `tests/services/test_orchestrator_helpers.py` and `tests/test_routes.py`).
  - Pre-commit hooks (`ruff check`, `ruff format`, `whitespace`, `tailwind-css-drift`,
    `doc-state-sync-check`, `worktree-alignment`) passed.
- Forward guidance: Batch 21 WP-7 extension is complete and verified across both browser engines.
  Pause for owner review before beginning WP-8.

### 2026-09-11 - Unmatched disclosure refined: 25-row step and collapse on return (Batch 21 WP-7)

- Scope: `templates/unmatched.html`, `static/js/unmatched.js`,
  `static/css/unmatched.css`, the rebuilt `static/css/tailwind.css`,
  `scripts/dev/frontend_gate.py` (the two new assertions, which landed later
  with the F-B21-51 slice-1 commit), and `tests/test_routes.py`. No server-side
  change; the Task 1 contract stands.
- Owner rulings applied, both from the 2026-09-11 review:
  1. a 50-row reveal is too much, so `data-step` and the server-rendered label
     become 25 (the owner allowed 20 or 25; 25 is recorded as the choice);
  2. the back-to-top control now collapses its panel as well as scrolling, so
     the reader is not left above a table they had just padded.
- Implementation: the expander's row visibility, button copy and
  `aria-expanded` were three copies of one state machine spread across two
  handlers. They collapse to a single `applyVisibleCount(count, isCollapsed)`
  writer that both the expander and the back-to-top control call.
- Design refinement, applying the `daisyui` skill's colour rule 10 ("use
  `primary` only for the most important element on the page. Use it only
  once") and its usage rules 2 and 7 (prefer utilities over custom CSS):
  - the panel album count moves off `primary` to `base-content`, matching the
    filter-bar summary count and leaving the page's one primary to the New
    Search action;
  - the panel header takes Results' scale-aware padding,
    `p-4 md:p-[calc(1.25rem*var(--results-scale))]`, so the panel block rhythm
    scales as Results' own surfaces do;
  - the reason-detail cell stops truncating and wraps instead: a side-by-side
    panel is narrower than a full-width row, and an ellipsis there would hide
    the sentence that explains the exclusion.
- The layout is unchanged. The owner ruled side-by-side on 2026-09-11; the
  spec's earlier "stacked, full-width" wording is superseded and is corrected in
  the documentation pass.
- Deviation, resolved rather than carried: the committed `tailwind.css` held a
  stale `.collapse { visibility: collapse; }` utility that no source produces
  (only `border-collapse` appears anywhere). The rebuild drops it, and this
  commit lands the rebuilt file so the drift hook is clean. That rule entered
  with the previous WP-7 commit, not with this change.
- Validation: `pytest -q` -- **1020 passed**; the two-engine frontend gate --
  "26 checks passed in 47 runs across chromium, firefox (static assets & tokens
  canary on firefox); profiles: desktop, mobile, wide touch". Pre-commit runs
  after this entry, per the documentation-first commit order.
- Forward guidance: the panel padding now scales with `--results-scale`, so a
  later edit to that curve moves the panel rhythm with it. WP-8 still owns
  retiring `global.css` and the `.dark-mode` write, with `heatmap.js`'s
  observer moved to `data-theme` in the same change.

<!-- DOCSYNC:CURRENT-BATCH-END -->

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
