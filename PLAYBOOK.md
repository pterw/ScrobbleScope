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
- **Next action:** WP-1 is complete and awaiting owner review of its single
  commit. The root-hygiene side task is **closed**: the owner rejected the
  audience-banner scheme on 2026-08-20, and the config-file verdict landed in
  `DEPLOY.md`. **WP-2 is next.** It owns the base shell, error-page pilot,
  Playwright runtime, frontend gate, and compiled-CSS pre-commit hook, and it
  closes the three seams filed as F-B21-2.
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
- Batch 21 WP status: WP-0 and WP-1 done. WP-2 through WP-8 not yet started.
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

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-08-21 - Size rule restated as intent in AGENTS.md (side-task)

- Scope: rewrote Proposal and Design Rules item 3 in `AGENTS.md`. One rule, no
  other rule touched, no code touched. Owner-authorised.
- Plan vs implementation: the rule read "No new file should be larger than the
  largest peer in its directory", which is the proxy metric rather than the
  intent, and it is the example `CLAUDE.md` had been carrying as the model for
  the planned trim. It now states the intent: the rule is against god files,
  not line counts; a file large because its job is large is fine; the peer
  comparison is the check you run when you notice scope creep, not a threshold
  to clear. Owner's framing, given 2026-08-21.
- This also resolved a contradiction inside the same list. Item 5 already said
  "SoC/DRY is the constraint on file content, not line count", which item 3
  denied. They now agree.
- Checked before writing, not after: `F-WORKTREE-4` and `F-MAS-3` are the only
  other places that restate the cap, and both already carry the correct
  reading -- "the rule exists to prevent unmaintainable monoliths" and "size
  was never the defect". Neither was edited; item 3 now cites both.
- Deviations: one, and it matters. The rewrite grew the item from three lines
  to eight, so every `AGENTS.md` line citation past it moved by five. This is
  the same drift that made `F-STYLE-1` cite 254, 262 and 550 when the real
  lines were 255, 263 and 551. One live citation was affected --
  `docs/design/RECONCILIATION.md` pointed at the ASCII rule by line. It now
  names the section instead, and `CLAUDE.md` records the rule: cite
  `AGENTS.md` by section or rule name, never by line.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; no Python
  touched. `doc_state_sync.py --check` exits 0. `pre-commit run --all-files`
  passes.
- Forward guidance: WP-2 is still next. When the wider `AGENTS.md` trim
  happens, do it this way -- one rule at a time, intent replacing the proxy
  metric, and re-grep line citations afterwards because they will move.

### 2026-08-21 - Front-end design handoff imported to docs/design (side-task)

- Scope: imported the owner's Claude Design project
  (`7d95e96a-613b-4017-9dd7-8b74d2db9535`) into `docs/design/`, recorded where
  it diverges from the batch contract, and filed two findings. No runtime code
  changed. WP-2 keeps its own reserved commit.
- Plan vs implementation: the source project holds 207 files; 61 are imported
  verbatim through the design MCP -- the canonical `README.md`, 10 token files,
  24 components as `.prompt.md` plus `.d.ts`, and two subordinate references.
  The import is a curated subset and says so; everything else stays reachable
  through the MCP, and `RECONCILIATION.md` section 2 tables what was left
  behind and why. Claude added a 62nd file,
  `RECONCILIATION.md`, because a verbatim snapshot states the Adobe Typekit
  stack and the `.dark` marker as fact and the owner has overridden both;
  without an override list a later agent reading only the specification would
  implement the wrong thing. `docs/AGENT_DOC_MAP.md` gains a row so the tree is
  discoverable.
- Owner decisions, all made this session: (1) the type stack stays self-hosted,
  so `BATCH21_DEFINITION.md:155-158` decision 4 stands and kit `rwy8ghw` is not
  adopted; (2) `docs/design/README.md` is canonical and is the default over
  both files in `reference/`, but it does not automatically retire an audit
  finding; (3) curated text-only import; (4) import only, one commit.
- Deviations: none against the approved plan, but two of its assumptions were
  corrected by evidence found while importing. The plan treated the mobile
  input size as a live conflict; it is not -- the canonical bundle's own
  `components/forms/Input.prompt.md` mandates 16px or larger on mobile, which
  matches the shipped override at `static/css/index.css:158`. `F-B21-5` records
  it as settled rather than open. The plan also assumed the component layer
  followed the Adobe stack; it does not -- `Button.d.ts` and `Input.d.ts` name
  JetBrains Mono, so the self-hosted mapping agrees with most of the bundle.
- Verified against code, not accepted from the documents: the seven `rocket_r`
  stops in `static/js/heatmap.js:14-22` match the specification exactly; every
  hex value in both colour tables matches `static/css/tailwind.src.css:69-137`;
  the three accessibility defects in `F-B21-5` were each confirmed at the line
  cited. The unmatched-grouping bug the design review names was already in the
  batch contract at `BATCH21_DEFINITION.md:25-27` and is not filed again.
- `docs/` is excluded from every pre-commit hook by `.pre-commit-config.yaml:2`
  and sits outside Tailwind's `@source` scope, so the import cannot rewrite the
  specification's Unicode or move `static/css/tailwind.css`. Both were checked.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; this commit
  touches no Python.
- Forward guidance: WP-2 is still next and its scope is unchanged. Before
  starting it, read `docs/design/RECONCILIATION.md` section 5 -- the theme
  marker resolves to `data-theme="dark"` on `<html>` at `templates/base.html:2`,
  which satisfies daisyUI, the WP-2 contract and the specification at once.
  WP-3 must measure label and hint widths at 9-11px: there is no narrow
  JetBrains Mono, so the clipping regression the specification warns about is
  live here rather than avoided. `F-B21-4` must not be closed by ruling on all
  four screens at once; each is decided at the WP that builds it.

### 2026-08-21 - Dependency advisories filed as F-B21-3 (side-task)

- Scope: filed one finding from the first Quality Gate run that exercised the
  Tailwind steps. No runtime code and no dependency changed.
- Plan vs implementation: pushing `bc9ba80` ran the gate for the first time
  since WP-1 landed. It passed, and "Verify committed Tailwind CSS" succeeded
  on Linux, so the committed digest reproduces in CI and the WP-1 platform
  detection works there. The same run's `pip-audit` step reported 115
  advisories across 12 packages and exited 1 without failing the gate, which
  is its documented `continue-on-error` disposition. Investigation found six
  packages in `requirements.txt` that nothing imports, including a
  `pypdf`/`pdf2image`/`pillow` cluster. The owner asked whether those served
  the JPEG export; they do not. That export is client-side `html2canvas` in
  `static/js/results.js:178-266`. All six unimported packages entered in the
  initial `0ea2313` commit rather than with a feature. The owner has poppler
  installed locally, so `pdf2image` can run on the development machine, but
  not in production: the `Dockerfile` is a bare `python:3.13-slim` with no
  system-package installs.
- Deviations: none. No dependency was upgraded or removed. Dependency changes
  are code and belong in a code batch, not a docs commit.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Quality Gate run
  32444711411 passed in 1m12s.
- Forward guidance: WP-2 is next. `F-B21-3` records a suggested shape --
  split runtime from developer requirements, drop unimported packages, then
  upgrade the outbound HTTP libraries -- but the owner has not ruled on it.

### 2026-08-20 - F-B21-2 deferred to the locked WP-2 remedy (side-task)

- Scope: corrected one finding that prescribed a fix competing with an
  owner-locked decision. No runtime code changed.
- Plan vs implementation: `F-B21-2` was filed from the WP-1 review without
  reading `BATCH21_DEFINITION.md:186-204`, which already prescribes WP-2's
  remedies. It told a reader to layer Bootstrap; the locked decision instead
  moves the Bootstrap link into a per-page block so each template loads
  exactly one framework stylesheet, removing the collision rather than
  re-ordering it. The finding now defers to the definition and says so. Its
  `data-theme` seam likewise points at the locked `theme.js` dual-write. The
  defect descriptions are kept, because they record why those decisions
  matter; only the competing prescription is gone.
- Deviations: none. The batch definition was not edited. A finding must not
  outrank the batch contract, so the finding moved.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next and closes `F-B21-2`. Check a finding against
  the active batch definition before filing a remedy in it.
