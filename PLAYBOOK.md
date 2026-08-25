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
- **Next action:** **WP-4 is next.** It migrates `loading.html` to the
  unified wait panel. `templates/partials/_loading.html` already exists and
  is framework-neutral -- WP-3 built it a work package early -- so WP-4
  consumes that partial rather than writing one. Before the frontend gate
  can see the page, WP-4 needs a GET route for it: `LEGACY_PAGES` in
  `scripts/dev/frontend_gate.py` is empty because `loading.html`,
  `results.html` and `unmatched.html` render only from a POST with session
  state, so no browser check has ever reached them.
  **WP-3 is complete**, recorded in Section 4 below and open as **PR #218**,
  which is not merged. It rebuilt `index.html` on Tailwind, deleted the
  welcome modal and the `bootstrap.Popover` hints, absorbed WP-6, and grew
  the frontend gate from four checks at one desktop viewport to nine across
  three device profiles. Codex raised twenty-seven comments on it; every
  one was valid and all twenty-seven were answered.
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
- Batch 21 WP status: WP-0, WP-1, WP-2 and WP-3 done; WP-3 is open as
  PR #218 and not merged. WP-6 is absorbed into WP-3 and ships no commit
  of its own. WP-4, WP-5, WP-7 and WP-8 not yet started.
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

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-08-25 - PR #218 review rounds one to ten applied (side-task)

- Scope: answered every Codex comment on PR #218 while WP-3 sat open and
  unmerged. Thirty-four comments across PR #216 and #218 in total -- seven
  on #216 and twenty-seven on #218 -- and all valid.
  One was declined on its premise -- it said the closed thresholds disclosure
  gave its controls zero-sized boxes, and deleting their sizing turns the gate
  red, so they were being measured -- and its remedy was applied anyway.
- What changed, beyond the individual fixes:
  - **Touch sizing and the 1rem input size moved off the width query** onto
    `@media (any-pointer: coarse), (max-width: 859.98px)`. A tablet in
    landscape is wide and touched. The two rules were corrected one round
    apart, which is the lesson: a rule moved for a newly understood condition
    is not done until every rule sharing that condition moves with it.
  - **The frontend gate gained a third device profile**, a wide touch screen,
    and `run_checks` now takes a page factory because touch emulation belongs
    to a browser context.
  - **The export header is measured rather than fixed**, after the file it
    produced was opened and looked at.
  - **A `/validate_user` reply is discarded when the field has moved on.**
    The submit guard added earlier in the series had turned a cosmetic stale
    message into a block that no blur clears.
  - **Round six found two blind spots in DOC009 and DOC011 themselves**, one
    day old. DOC009 accepted a file after its first match, so `index.css`
    could state the breakpoint once and contradict it in either of its other
    two media queries; it reads every occurrence now, and a site may declare
    `expect` so two notations of one fact -- `859.98px` and `860` -- can
    differ without the check going blind. DOC011 searched line by line and
    could never match a phrase that wrapped, which in Markdown that wraps at
    about 76 columns is the likely shape rather than an edge case; it matches
    the joined document now and maps back to the starting line, with the
    history and strikethrough exemptions applied after that mapping.
  - **Round seven found the same two blind spots one level further out.**
    DOC010 also searched line by line, and `PLAYBOOK.md` already carried a
    citation of `AGENTS.md` "UI and Accessibility Rules" across two lines, so
    that heading could have moved with the gate green. DOC009 shared the
    shape, quietly: a file that states a value more than once satisfied the
    check on the unwrapped copy while a drifted wrapped one went unread. Both
    read the joined document now. `_joined_text` strips each line before
    joining, without which a correct wrapped citation resolves to a heading
    name with five spaces in the middle of it.
  - **The anchor scan is every Markdown tree**, not the trees someone
    remembered. It had missed `docs/SWE_AUDIT_CHARTER.md`, which cites
    `AGENTS.md` and was never read. Three exemptions are declared with it:
    `docs/history` and `docs/logarchive`, because a dated record is accurate
    at write time and renaming one heading would otherwise turn 70 archived
    files red with no fix but editing history; and `CLAUDE.md`, because it is
    gitignored, so scanning it made the gate's answer depend on which machine
    ran it.
  - **Widening the scan found a checker defect before it found a document
    defect.** The design contract labels some sections as list items, and the
    bold-label pattern insisted the asterisks start the line, so the WP-3
    plan's citation of "Responsive" resolved nowhere. Fixing that first was
    the difference between the widening finding a defect and the widening
    crying wolf.
  - **A year warning that is still true survives a username edit.**
    `clearRegistrationState()` had reset the minimum and the hint and left the
    message naming the previous account's join year. Clearing the message
    outright is the obvious fix and is wrong: "Year cannot be in the future"
    is about the year, not the account. The handler re-derives instead, and a
    ninth gate check holds the half a reader would not notice was broken.
  - **A failing validator no longer locks the form it serves.**
    `/validate_user` answers an outage with 503 and `valid: false`, which both
    blur handlers read as a verdict about the username. Trying again was the
    one thing the message asked for that could not work. Reported against the
    heatmap form, which refuses at its own submit guard; the index form has
    the same defect through native validation, because only the heatmap form
    carries `novalidate`. One comment, two forms.
  - **A declaration with nothing to scan is refused.** `scan` was optional, so
    an anchor carrying only `target` and `pattern` validated, visited no
    documents, and DOC010 reported clean while checking no citations at all.
    That is the same silent end state as the misspelled key closed the round
    before, reached without a typo -- the earlier fix stopped at the way the
    fault had been reported rather than at the condition behind it.
  - **The heatmap window is declared against one source.** DOC009 watched
    two copies of it and there are seven. The backend was not one of the two,
    and it wrote `timedelta(days=364)` for an inclusive range, so it could not
    have been compared with them anyway. A change there would have fetched one
    interval while the page displayed and averaged another, gate green.
    `HEATMAP_WINDOW_DAYS` is the source now and the fetch subtracts one from
    it. `static/js/loading.js` is deliberately excluded and the declaration
    says why: its 365 is the length of a calendar year, leap-aware, for a
    different average. That is the same trap as reading an ordinary max-width
    as a breakpoint.
  - **A declared container is checked for what it holds.** `scan = [1]` is a
    list, so the shallow check passed it and the integer reached the glob
    matcher as a `TypeError`. Round eight was the third round on this module
    and each one sat one level further in than the last: wrapped text, then
    missing and misspelled keys, then the contents of a container.
  - **A malformed declarations file is refused, not ignored.** Reading a
    required key straight out of the mapping raised a bare `KeyError`, so an
    anchor with no `target` ended the run in a traceback and exit 1. Looking
    for the siblings found four more, and all four are worse because they are
    silent: a misspelled key, a list written as a bare string, a misspelled
    table, and a misspelled option. Each leaves a check quietly not checking
    while the gate stays green. Every declaration is now held to a declared
    schema, so an unknown key is an error rather than a shrug.
  - **A bad declarations file is reported rather than thrown.** Malformed
    TOML, or a declaration holding an invalid regex, raised
    `DeclarationError` straight through both CLI paths, which catch
    `SyncError` and exit 2. The run ended in a traceback and exit 1 instead.
    It is a `SyncError` now, keeping the distinct class its docstring asks
    for so the reader is not sent to edit the wrong file.
- Two findings came out of reading the comments as a set rather than one at a
  time: `F-B21-17`, that six of nineteen were one fact written twice, and
  `F-B21-18`, that 2,344 lines of JavaScript have no runner. `F-B21-17` was
  then built and closed the same day; see the DOC009 entry below.
- Deviations: none against a plan, because there was none -- this is review
  remediation. Each round was answered in one batched PR comment rather than
  per comment, per the `pr-bot-triage` skill.
- Validation: `pytest -q` -- **798 passed**, 3 warnings. All 11 pre-commit
  hooks pass with an identical `git write-tree` either side.
  `doc_state_sync.py --check` exits 0. The frontend gate reports 10 checks
  in 15 runs across desktop, mobile and wide touch. Every fix was reproduced
  against the running page before it was written and re-measured after.
- Forward guidance: the merge is the owner's and is being held while rounds
  still return findings. Codex reacts to the PR summary with a thumbs-up when
  it has nothing to say and comments when it does, so that reaction is the
  signal to stop, not a quiet round.
  Rounds four and five found defects that earlier fixes in the series had
  introduced, which reads as approaching diminishing returns. Round six then
  found two holes in code that was one day old, which corrects that reading:
  yield tracks new surface area, not elapsed rounds. Expect a round on
  whatever `F-B21-18` builds.
  Both round-six holes were of a kind a check's own tests cannot find, because
  the tests were written from the same understanding as the code. That is the
  argument for keeping a reviewer on tooling and not only on features.

### 2026-08-25 - DOC009 to DOC011: facts written down more than once (side-task)

- Scope: closed the buildable half of `F-B21-17`. Three declared integrity
  checks in a new `scripts/docsync/declarations.py`, driven by a new
  `.docsync.toml` at the repository root. No new dependency; the declarations
  are TOML read with `tomllib` from the standard library.
- Why: six of the nineteen Codex comments across PR #216 and PR #218 were not
  logic defects. They were one fact recorded in several places where the
  copies had drifted. The clinching case was a cross-reference that named its
  target by heading, exactly as `F-STYLE-1` asks, and broke in the same commit
  that moved the heading. A written rule cannot catch that; only something
  that resolves the reference can.
- Plan vs implementation: DOC009 compares a value across its sites, DOC010
  resolves a citation shape against the document it names, DOC011 keeps a
  retired claim out of anything that still prescribes. Four behaviours were
  added after the first run reported false positives on real documents, and
  each is a property of how this repository actually writes: bold lead-ins
  count as citable places, a heading cited without its trailing parenthetical
  resolves, a label's trailing sentence is not part of its name, and
  struck-through text is already marked as not current.
- What the first run found, before any test was written:
  - **`static/css/shell.css` used `max-width: 860px`** where every other
    stylesheet uses `859.98px`. Both the mobile and the desktop rules
    therefore applied at exactly 860px. Fixed.
  - **`AGENTS.md` described the integrity codes as DOC001-DOC006**, four
    checks after that stopped being true. Fixed, and the line now says when
    it went stale, because that is the same class the new checks exist for.
  - Two stale citations, one of them inside the finding that proposed the
    check.
- Deviations: the declarations file is at the repository root as
  `.docsync.toml` rather than under `docs/`. It is configuration, it sits
  beside `.pre-commit-config.yaml` and `.gitattributes`, and keeping the
  repository-specific half out of `scripts/docsync/` is what lets that
  package be lifted into another repository unchanged.
- Validation: `pytest -q` -- **771 passed**, 3 warnings, 22 of them new. All
  11 pre-commit hooks pass with an identical `git write-tree` either side.
  Each of the three checks was proved against the real defect it was built
  for, by restoring that defect and watching the check name it. Five
  mutations of the module each killed exactly one test and no others.
  `doc_state_sync.py --check` exits 0. The frontend gate is unaffected and
  still reports 8 checks in 13 runs.
- Forward guidance: add a declaration when a fact starts living in two
  places, not after it drifts. `F-B21-18` is the other half and is not
  started -- 2,344 lines of JavaScript with no runner, to be reached through
  a guarded seam onto the Chromium the frontend gate already pays for, not
  through npm.

### 2026-08-24 - F-B21-13 docsync bootstrap gate remediated (side-task)

- Scope: closed `F-B21-13` with DOC007 and DOC008 on
  `wip/f-b21-13-docsync-gate`, branched from `origin/main` at `658bdb2`;
  WP-3 remains on `wip/batch-21`.
- DOC007 now has one next-WP calculation. The managed SESSION_CONTEXT
  renderer owns `_next_wp_number()`, the integrity check calls that helper,
  and the CLI supplies the active definition's finite plan. Absorbed,
  dropped and merged WP headings are skipped; a fully completed plan
  terminates with no next package instead of looping forever, while any stale
  numeric next-WP claim left at close-out is blocking. The definition Status
  line, PLAYBOOK Section 3's actual Next action bullet, and SESSION_CONTEXT
  Section 1's sole active Batch status row are checked for the same active
  batch and next WP. Historical claims outside the bullet and earlier claims
  superseded inside it cannot steal the comparison.
- DOC008 applies `latest_test_count_authority()` to the FINDINGS.md header
  with findings-specific remediation. Authority includes live entries, the
  side-task archive and per-batch logs; a same-date tie between batch logs is
  resolved by numeric batch chronology rather than filename insertion order.
- Review remediation also repaired two misleading DOC007 fixtures so their
  asserted WP ranges really sit inside the current-batch markers, and made
  DOC008's error invariant say the header count "must agree" instead of
  claiming that a detected mismatch already agrees. Every new edge case was
  observed failing before its minimal fix.
- Deviations: the owner authorized expanding the original PR file set on
  2026-08-24 after the audit proved DOC007 and the renderer computed different
  next-WP values. The expansion is limited to the renderer/sync/CLI data path
  and its directly related docsync tests; no unrelated refactor was taken.
- Validation: `pytest -q` -- **717 passed**, 3 warnings (was 682; 35 new
  tests across the docsync integrity, renderer, logic, CLI and count suites).
  The focused docsync suite is **219 passed**.
- Forward guidance: WP-3 should still update the definition Status line as
  an explicit task. The gate proves agreement; it does not replace writing
  the canonical status correctly.

### 2026-08-23 - PR #216 review round three applied (side-task)

- Scope: two review comments on `e9bac27`, both real rendering defects in
  WP-2's own shell commit. Both were verified in a browser before any edit.
- **The header wordmark ignored `prefers-reduced-motion`.** The lockup
  carried five SMIL `<animate>` elements with `repeatCount="indefinite"`.
  No CSS can pause SMIL, so the media query in `shell.css` never reached
  them. WP-2 made the exposure much worse: the mark moved from per-page
  hero content that scrolls away into a fixed header that is on every page
  and never leaves the viewport. `docs/design/README.md` already prescribed
  the remedy and says the SMIL must be stripped and the bars animated from
  CSS. Done, with the keyframes taken from `docs/design/tokens/base.css`.
- **A wrong assumption was caught by measuring.** The origin looked like it
  needed a 7-unit correction, because this lockup's viewBox starts at y=7
  where the full mark starts at y=0. It does not: `view-box` resolves
  `transform-origin` in the SVG user coordinate system, not from the
  viewBox corner. At `scaleY(3)` the proposed 56.5px slid each bar bottom
  8.4px and the canonical 63.5px held it to 0.2px. Under the shipped 1.10
  scale the gap is under half a pixel, so eyeballing would have missed it.
- **The back-to-top control lost its layout.** `base.html` used to wrap the
  theme toggle and `page_footer_extra` together in `.page-footer-bar`. WP-2
  moved the toggle into the header and removed the wrapper with it, but
  `results.html` still fills that block and `#back-to-top` has no CSS of its
  own anywhere. Centring, gap, padding and entrance all came from the
  wrapper, so the control shipped bare and left-aligned. Restored in
  `shell.css` rather than `global.css`, which only reaches unmigrated pages.
- Both guards were proven able to fail. Putting one `<animate>` back fails
  five tests, reflowing the wrapper onto three lines fails four, and
  dropping the reduced-motion `opacity: 1` fails one.
- Deviations: the frontend gate gained no reduced-motion check. Its checks
  take a page rather than a browser, so a second context needs a signature
  change, and that is a refactor rather than a review fix. The template
  tests cover the markup and the CSS; the computed behaviour was verified
  by hand this round.
- Findings: `F-B21-5` updated rather than closed. The header instance is
  resolved; the pinwheel and the index hero wordmark still carry SMIL and
  belong to WP-3.
- Validation: `pytest -q` -- **682 passed**, 3 warnings. All 11 pre-commit
  hooks pass. The frontend gate reports `5 checks passed`.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: strip the SMIL from the remaining two assets the same
  way. Do not reach for `svg.pauseAnimations()` -- the CSS route is what the
  design contract asks for and it needs no JavaScript.
