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
- **PR #227 review remediation:** the owner-requested package is implemented
  and validated. Audit and remaining scope:
  `docs/history/reports/PR227_REVIEW_2026-09-07.md`. Deployed-header comparison
  and optional card-shadow polish remain the next owner-design follow-up.
- **PR #223 side-task:** merged as `123b127`; this worktree is synchronized.
  Remaining issue #222 targets stay open.
- **Planning follow-up:** the original owner-review plan remains historical
  evidence; the superseding plan below is canonical. Task 2 now implements
  the two-engine runner and explicit CSS composition dimensions. Its rendered
  expanded-state guard, complete validation, and PR #224 review remediation
  passed.
- **Remediation plan:** **Tasks 1-5 are complete and validated locally.
  Task 6 (accessibility pass) is next.** Work from
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
  Owner visual refinements vertically centre the desktop form composition,
  unify single-row mobile navigation with the theme control below page content,
  widen the desktop Heatmap result, and return its username to the neutral headline
  treatment (F-B21-44 through F-B21-46). Task 6 (accessibility pass) is next.
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
- **Next action:** Begin WP-7 (unmatched page + reason_code) -- WP-0 through WP-5 are done. WP-6 is absorbed into WP-3
  and ships no commit of its own. WP-7 is next; WP-8 follows it.
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

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-07 - Remediate PR 227 and simplify frontend checks

- Owner requested one review-remediation package. The full comment inventory,
  body exclusions, repeated claims and individual dispositions are in
  `docs/history/reports/PR227_REVIEW_2026-09-07.md`.
- Extracted gate measurement/comparison/profile responsibilities, shared phase
  probes and lazy generic CDN fixture loading; preserved the live-fonts option.
  Existing thresholds and the Chromium matrix / Firefox static canary remain.
- Separated spotlight aggregation from routes, shared Spotify payload parsing,
  separated heatmap validation/dispatch, and extracted the Last.fm job stage.
  Existing job-state, empty/error, fallback and sampling behavior stays covered.
- Split results spotlight hydration/rotation from exports; use DOM text nodes
  for metrics/toasts and supported metric-toggle font weights. CSV follows the
  current rank/metric with full ISO dates while display stays month precision.
  JPEG background comes from the active theme; browser checks decode actual
  downloads in both themes at mobile and desktop widths.
- Reconciled implemented route TODOs, corrected explicit 404/500 badges (the
  remainder of F-B21-10 stays open), and disabled checkout credential persistence.
- Review caught invalid JSON in the extracted stale-response fixture. A failing
  regression test proved it; structured JSON serialization restored the check.
- Validation: `pytest -q` -- **962 passed**, zero warnings. The frontend gate
  passed 25 checks in 45 runs across Chromium and the Firefox static canary.
  Both theme exports decode to nonblank 3600px-wide JPEGs. All pre-commit
  hooks and `doc_state_sync.py --check` pass. No push or deployment. Header
  alignment and optional white-card shadow remain a separate design follow-up.

### 2026-09-07 - Qlty adopted; first triage closes the workflow-permission gap (side-task)

- Scope: the owner added qlty (`.qlty/qlty.toml`, uncommitted by owner
  choice) as a fourth static-analysis layer alongside ruff, bandit-class
  SAST, and the existing gates. This entry records the config tuning,
  the first triage, and the two fixes it produced.
- Plan vs implementation: no plan -- owner-directed tooling adoption and
  triage. Config tuning: scratch/, scripts/bin/, generated tailwind.css,
  and graphify-out/ excluded (metrics went from 68 to 18 files); the
  flake8 plugin removed (ruff replaced it; two plugins would report one
  rule surface in two vocabularies); tests/ added to test_patterns.
- Triage of the first `qlty check` (88 findings): ~60 are bandit B101
  "use of assert" in tests -- noise, asserts are the point of tests;
  2 are real (zizmor on the workflow, fixed here); 1 is a false positive
  recorded with a nosec (bandit B311, fixed here); the cognitive-
  complexity pair (frontend_gate.py check_large_display_scale_parity,
  spotify.py fetch_spotify_artist_spotlight) is known owned debt that
  matches F-B20-2/F-SWE-7/issue #222 and stays batch-scoped, not
  gate-blocking.
- Implementation:
  - `.github/workflows/test.yml`: added a job-level `permissions:
    contents: read` block. The job only reads the checkout and uploads a
    coverage artifact; without the block the runner's default token
    permissions are broader than any step needs and every third-party
    action inherits them (zizmor excessive-permissions and artipacked).
  - `scrobblescope/routes.py`: `# nosec B311` with justification on the
    `random.Random(str(job_id)).sample(...)` spotlight selection. The
    seed makes the sample deterministic per job (asserted by
    test_results_page_samples_five_unique_artists_from_aggregate_top_ten);
    cryptographic unpredictability would defeat the intent.
- Deviations: none.
- Validation: `qlty check` -- 88 -> 86 findings. The excessive-permissions
  finding is gone; the B311 finding is suppressed (the nosec must sit on
  the same line as the call -- a preceding comment line is ignored by
  bandit, which the first attempt got wrong and the re-run caught).
  Remaining: one zizmor artipacked medium on the checkout step (line 34)
  -- zizmor flags any cache/artifact-adjacent job; with the permissions
  block in place the token is already contents-read only, so the
  practical exposure is closed and the residual finding is a
  scanner-pattern advisory, not an open hole. The rest are the recorded
  noise classes. `pytest -q` -- **938 passed**, zero warnings. All
  pre-commit hooks pass.
- Forward guidance: the meta-lesson is recorded here because it
  generalizes -- each gate only checks what it was built to check, and
  no gate checked the checkers' blind spots. Workflow files had no
  linter, the codebase had no SAST, structure had no complexity metric;
  qlty closes exactly those three. The complexity refactor and the
  bandit B101 test-path suppression are future-batch candidates, not
  scheduled work. WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - Clean uninterrupted frontend gate run achieved (side-task)

- Scope: closed the deviation recorded in the two 2026-09-07 entries above
  -- no clean uninterrupted `frontend_gate.py` run had been achieved
  locally -- and updated the spec status line for the implemented design.
- Plan vs implementation: Task 6 Step 3 of
  `docs/superpowers/plans/2026-09-07-frontend-gate-isolation.md`. One run,
  qualified venv path, no interference.
- Result: the run completed all four groups across both engines with 261
  page loads, zero timeouts, zero errors, and zero font warnings (the kit
  served live). The only failures were the 7 large-display-scale-parity
  assertions at 4K (deltas ~1 percent: 770.0 vs 780.4px form width,
  774.4 vs 781.6px hero height, 77.2 vs 78.2px headline line-height, and
  related), which are the same failure family the owner already accepted
  in the gate-isolation entry above. The isolation mechanics work as
  designed: every check ran and reported; nothing cascaded.
- Deviations: none beyond the already-recorded 4K parity pair.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (unchanged; no
  code changed in this entry). Spec status line updated to record the
  owner-ruled licensing amendment (Typekit fixture withdrawn).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - Gate isolation, license-safe CDN routing, paper-cream tokens, and results polish (side-task)

- Scope: made the frontend gate stall-tolerant (grouped checks, fresh
  contexts, fail-fast navigation), resolved the PR #227 Quality Gate
  failures, applied the owner's paper-cream surface palette, and landed
  the owner-annotated results-page polish.
- Plan vs implementation: followed
  `docs/superpowers/plans/2026-09-07-frontend-gate-isolation.md` with one
  fundamental amendment. The metric-pinned font fixture (plan Tasks 1 and
  5) was abandoned at the owner's licensing ruling: the kit families
  (Gotham, Akzidenz-Grotesk Next Pro) are commercial web fonts and must
  never be re-hosted, embedded, or synthesized in the repo. The kit loads
  from the real Typekit origin on every gate run; only the generic cdnjs
  Bootstrap stylesheet is served from a repo fixture. The gate is
  therefore not fully hermetic -- accepted trade-off for license safety,
  recorded in `scripts/dev/fixtures/README.md`.
- Implementation:
  - Gate grouping: `CHECKS` entries gained a group field; groups derive
    from the tuple at call time (no second declared copy, no group
    integrity test per the owner's "redundant to test a test" ruling).
    Each group opens a fresh browser context, so a wedged page poisons
    only its group -- the 2026-09-07 CI run had cascaded one navigation
    timeout through every later check on a shared page.
  - Firefox is a canary: it runs only the static-assets group (the
    2026-09-01 remediation plan measured engine agreement within 0.1px,
    so a full second pass doubles the stall surface for near-zero
    signal). Chromium runs everything.
  - Fail-fast navigation: 10s page-level timeout (the context-level
    kwarg does not exist in Playwright -- caught by a local run, not by
    unit tests).
  - Fonts advisory: `check_fonts` reports missing faces as WARN lines
    and returns no failures (owner ruling: a font-supply problem is not
    a UI defect).
  - License posture: no Adobe family is copied, embedded, synthesized,
    or re-hosted anywhere; a synthetic TTF generator briefly existed in
    untracked scratch and was destroyed before any commit.
  - Paper-cream surfaces: `--ss-surface-card` #fcfbf8 -> #f7f3ea
    (halfway to the sunken tone; cards had become indiscernible from
    the page and pure white read as harsh). `global.css` mirrors follow.
    The imported design snapshot keeps `#ffffff` by contract; the
    override is recorded in `docs/design/RECONCILIATION.md` section 12.
  - Theme pill: the active Light choice dropped its #ffffff background
    (introduced in `14215d6`) for `--shell-surface` elevation with a
    stronger border/shadow.
  - Heatmap preview: bullets at color-mix(body 55%, muted); copy
    rewritten (7x52 grid, totals/streak, best-day highlight).
  - Index: `--index-scale-cap` 2.15 -> 1.75 (owner ruling: the lockup
    dominated beyond 1440p and the right-hanging void grew faster than
    content).
  - Card surfaces, final ruling (revising the paper-cream line above,
    same day): #f7f3ea was too warm and #fcfbf8 read cold, so the owner
    split the surfaces. `--ss-surface-card` -> #f9f7f1 (midpoint of the
    two; general cards), mirrored in `global.css`, and a new
    `--ss-surface-card-standout` (#ffffff light / #181520 dark) paints
    the index card alone pure white as a standout; `.ss-card` and
    `.hint__body` in `index.css` read the standout token. DESIGN.md
    header and the token test follow. RECONCILIATION.md section 12
    records the full trial -> reversal -> split sequence.
  - Results StatBlock typography (owner ruling): numerals and labels
    back to Instrument Serif with labels at 11px/xs serif in
    `--ss-text-body` (not muted); the sans-numeral line below is
    superseded by this.
  - Results polish (owner-annotated screenshot): action-row gap 8 -> 12px;
    filter-bar values to input-mono; row hover at full sunken strength;
    sort-toggle weight 500.
- Deviations: superseded by the 2026-09-07 stale-gate-cap entry below.
  The 4K parity failures recorded here were later root-caused to the
  gate's expected-scale cap lagging the CSS `--index-scale-cap` change
  in this same entry, not to font metrics. Owner confirmed the form card
  does not scroll the page at 1080p/92dpi with bookmarks extended.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (final
  consolidated run for this entry; the standout token added one
  parametrized test to the shell suite). Full suite green before commit;
  pre-commit hooks (black auto-fix included) enforced on every commit in
  the series. The gate itself was exercised repeatedly during
  development; the remaining parity pair is recorded above rather than
  hidden.
- Forward guidance: WP-7 (unmatched page + reason_code) remains next;
  the heatmap form lacks validation-on-blur and private-account gating
  (owner-noted), candidate for WP-7 or a scoped side-task.
