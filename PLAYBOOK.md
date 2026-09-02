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
- **Next action:** **WP-4 is complete. Owner-review remediation is planned,
  not implemented; begin it before WP-5.** The index does not grow with the
  window on large displays. Measurement on 2026-09-01 named the cause: the
  scale formula divides window height by the 1080px design viewport instead of
  by the composition's own height, and an unconditional `min()` then lets
  browser chrome discard the width term on every real window. Chromium and
  Firefox measured identically, so this is not engine-specific; the browser
  gate missed it because it measures panel dimensions no window has. Work from
  `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`,
  which supersedes the earlier remediation plan. It restores the design
  snapshot first, then fixes the gate geometry and the scale in one commit,
  then widens, then does progress, empty state and accessibility.
  WP-4 migrated `loading.html` to the shared determinate wait panel, completed
  both polling state machines, and added browser-session recovery for the
  latest album and heatmap jobs at clean destination routes. The owner
  completed the first Impeccable Live annotation pass and paused for the day;
  resume that review before WP-5 begins.
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
- Batch 21 WP status: WP-0 through WP-4 are done. WP-6 is absorbed into WP-3
  and ships no commit of its own. WP-5 is next; WP-7 and WP-8 are not done.
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

<!-- DOCSYNC:CURRENT-BATCH-END -->

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
