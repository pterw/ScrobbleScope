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
- **Next action:** PR #172 is merged and no longer a gate. WP-1 is complete
  and awaiting owner review of its single commit. After acceptance, the
  already-queued root-hygiene side task (audience banners, README tree,
  DEPLOY.md) is next by the owner's 2026-08-19 decision. WP-2 follows that
  side task and owns the base shell, error-page pilot, Playwright runtime,
  frontend gate, and compiled-CSS pre-commit hook.
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

### 2026-08-20 - Batch 21 WP-1 test-count authority addendum (side-task)

- Scope: records the post-WP-1 measured suite inventory for docsync's
  same-day source ordering. No runtime implementation changed.
- Plan vs implementation: the new current-batch WP-1 entry remains the owner
  of toolchain evidence. This live addendum supplies its later full-suite
  result because same-date side-task entries take precedence over
  current-batch entries in docsync's authority ordering.
- Deviations: none.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: owner review of the WP-1 commit remains first; the
  root-hygiene side task follows, then WP-2.

### 2026-08-20 - Agent document map added; HANDOFF_PROMPT trimmed (side-task)

- Scope: the owner asked for an instructional that lets an agent other than
  Claude navigate the documentation set -- including the audit and SWE
  documents -- and understand why each document exists. Added
  `docs/AGENT_DOC_MAP.md` and registered it in the `AGENTS.md` Document Roles
  table. Documentation only; no runtime code changed.
- Plan vs implementation: as planned. The map routes rather than summarises.
  It names the owner of each fact and links to it, so it adds no copy that a
  later edit can contradict (`AGENTS.md` Anti-duplication rule). Sections:
  the one-owner rule and why it exists, where to start, the document groups,
  the human-facing documents, how to read an audit, how to read a finding,
  seven navigation traps, the pre-change gates, and the tie-break order when
  two documents disagree. It sits under `docs/` rather than the repository
  root, because a twelfth root Markdown file would worsen the problem the map
  exists to solve, and it is marked optional and outside the bootstrap set so
  it does not inflate the cold-start read. 264 lines, under the 370-line
  largest peer in `docs/`.
- Audit guidance is the part with no prior owner: the charter to report to
  findings to log-entry lifecycle, why a retired charter is kept, why a dated
  report is never edited in place, and that a report is a measurement of one
  day rather than current truth. The SWE report's own "Owner review" section
  is cited as the worked example of an appended correction.
- Owner request mid-task, and the reason it changed shape: delete
  `HANDOFF_PROMPT.md`. That is not a documentation-only delete. The file is
  pinned into the commit gate at `scripts/docsync/cli.py:26` and
  `scripts/docsync/integrity.py:51`. `cli.py:88` loads every
  `LIVE_DOCUMENT_PATHS` entry through `_read_lines`, which raises `SyncError`
  on a missing file and maps to exit 2, and the `doc-state-sync-check` hook
  runs `--check` with `always_run: true`. Deleting the file alone would fail
  every commit in the repository until `cli.py`, `integrity.py`,
  `tests/conftest.py:149` and four assertions in
  `tests/test_docsync_integrity.py` changed with it. The owner chose to trim
  the file instead of deleting it.
- Trim: `HANDOFF_PROMPT.md` went from 66 to 46 lines. Removed three sections
  that carried no requirement of their own and only named an `AGENTS.md`
  section: validation gates, commit discipline, and anti-patterns. Every
  subject those sections named survives in the new opening paragraph, checked
  against the removed text one item at a time per Anti-Pattern 12. The two
  unique parts are untouched: the post-read verification and the handoff
  checklist. Section numbers were replaced with names, so no later edit can
  leave a stale "Section 4)" citation behind. `DEVELOPMENT.md:74-78` already
  claimed the file held only those two things, so the trim closes an existing
  drift rather than creating one.
- Deviations: two stale claims corrected in the same commit, both left behind
  by the 2026-08-20 audit commits. `BATCH21_DEFINITION.md:3` still read that
  the F-SWE-1 audit "comes next" after PR #170; the audit ran on 2026-08-20.
  The `README.md` documentation tree still described
  `docs/SWE_AUDIT_CHARTER.md` as "Standing audit scope and method"; the
  charter is retired. The same tree gained a row for the new map, because it
  enumerates the contents of `docs/`.
- Validation: `pytest -q` **590 passed** (unchanged; no code touched);
  `pre-commit run --all-files` all hooks passed;
  `python scripts/doc_state_sync.py --check` exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning. Every tracked Markdown file
  was checksummed before and after the pre-commit run and compared, because
  that hook has twice reverted files nobody edited, once into a commit.
- Forward guidance: unchanged. The F-SWE-2 fix is still the next action. It
  is a code commit and it moves the test count off 590.
- **Later same-day test-count addendum:** the F-SWE-2 current-batch entry above
  records the subsequent code change and owns its implementation details. Its
  full-suite result was `pytest -q` -- **591 passed**. The earlier 590 result
  in this entry remains point-in-time evidence; this pointer supplies the
  later same-date count to docsync's live-side-first authority order.

### 2026-08-20 - F-SWE-1 SWE principles audit executed (side-task)

- Scope: executed `docs/SWE_AUDIT_CHARTER.md` against `1994673`, whose
  runtime code is byte-identical to `main` at `bb187ae` -- the five commits
  between them are documentation only. Read-only audit; all 130 cells
  (13 graded modules x 10 principles) filled in one session. Report:
  `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`.
- **Verdict: migration blocked by F-SWE-2**, per charter Section 6 -- a
  net-new correctness defect in `orchestrator.py`, which WP-7 modifies.
  `orchestrator.py:70-71` builds the listening-year window from naive
  datetimes, so the window shifts by the local offset of the host: measured
  at five hours on this machine. It is the same defect F-B19-6 fixed in
  `heatmap.py`; `git show --stat ccb000f` confirms that fix touched heatmap
  and its tests only, and the twin was never revisited. Production is
  unaffected because the Fly.io container runs UTC. Every non-UTC host is
  affected, including local dev, so local checks of album results have been
  running against a shifted window.
- **Owner decisions, same day.** F-SWE-2: fix, do not waive -- it lands as
  its own commit before WP-1 and moves the test count. F-SWE-3: rescoped
  from P1 to P2, and the audit was partly wrong. It filed the
  `No Spotify match` reason as a user-facing mislabelling; that framing does
  not hold, because thousands of Last.fm-scrobbled albums genuinely have no
  Spotify release, so the label is accurate for the ordinary case. What
  survives is narrower and independent of labelling: `spotify.py:67-68`
  marks every non-200, non-429 response terminal, so a 500 ends the attempt
  loop after one try while `SPOTIFY_SEARCH_RETRIES` is 3. The related UI
  need -- the unmatched modal and page should say plainly that an album had
  no Spotify match -- is already WP-7 scope
  (`BATCH21_DEFINITION.md:297-308`), not new work.
- Grades: 74 A, 28 B, 8 C, 2 D, 18 N/A. The weakest principle is Fail Fast,
  holding five of the eight C grades and only two A grades across 13
  modules. The failures share one shape: the code catches a problem and
  discards what the problem was.
- Six net-new findings, F-SWE-2 to F-SWE-7. Every one of the ten C and D
  cells carries a disposition; two map to open F-B20-2 rather than becoming
  new entries. Each finding was verified by running the code, not by reading
  it -- the TTL renewal, the Spotify retry bypass, the unreachable API-key
  check and the heatmap misattribution were each reproduced.
- Test vacuity: measured, not judged. Each of the 81 top-level functions in
  the graded modules was replaced in turn with a raise, in a copy of the
  tree outside the repository, and the 237 runtime tests were run against
  each mutation. Every deletion was caught, so there is no vacuity finding.
- Broad catches: all 17 were read in context and judged, which F-MAS-4 never
  did. Fifteen are justified. The two that are not are both in F-SWE-5, and
  both are catches that report a cause they never established.
- F-B21-1 keeps its recorded P1 disposition. The gate covers net-new
  findings only, so the audit did not re-triage it and it does not block
  WP-1.
- Deviations: F-SWE-1 moved from the P1 section to Resolved this batch, and
  F-SWE-3 from P1 to P2 -- the charter asked for neither move, but leaving
  either where it was would have made the section heading false.
- **Tooling hazard hit twice, worth recording.** `pre-commit run --all-files`
  stashes unstaged changes and restores them afterwards. That cycle reverted
  files nobody had edited: first `docs/architecture/development-cycle.md`
  and `top-albums-sequence.md` back to a pre-PR-#171 state, then `PLAYBOOK.md`
  itself back to a pre-PR-#170 state, dropping this very entry. Every hook
  reported `Passed`. The first was caught at staging because AGENTS.md
  requires staging by name; the second reached commit `a34c57f` and was
  repaired in the follow-up commit. Check `git status` before and against
  after every `--all-files` run, and compare file mtimes against the files
  you actually edited.
- Validation: `pytest -q` -- 590 passed, unchanged, as expected for a
  docs-only change. `pre-commit run --all-files` and
  `doc_state_sync.py --check` both pass, the latter with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: apply the F-SWE-2 fix as its own commit, then WP-1. Root
  hygiene stays deferred until after WP-1.

### 2026-08-19 - Batch 21 preflight: F-SWE-1 charter and WP gates amended (side-task)

- Scope: owner preflight review before WP-1, raised as six criticisms of
  `docs/SWE_AUDIT_CHARTER.md` and an eight-row table of weak WP gates. Two
  verification agents checked every claim against the files before any edit.
  All six charter criticisms held. Two of the batch claims did not.
- Verification of the owner report:
  - Confirmed: the charter named five docsync modules when the directory has
    seven (`integrity.py`, 474 lines, unnamed) and its LOC figure was stale
    for the five it did name; the differential baseline was a closed ID list
    omitting F-B21-1, F-DATA-1, F-WORKTREE-3/4/5, F-DOCSYNC-6/7 and never
    referenced `FINDINGS_ARCHIVE.md`; A/B/C/D was defined nowhere in the
    repository; the matrix was 190-210 cells with explicit permission to cut
    modules; no severity or stop condition existed anywhere, so finishing the
    audit was the same as passing it; and the post-Batch-21 frontend audit
    was permissive ("can"), not required.
  - Corrected: the excluded set is a proper subset of what Batch 21 rewrites,
    not equal to it -- WP-7 modifies `routes.py` and `orchestrator.py`, which
    are in scope, so those grades also expire at WP-7. The charter never
    addressed that; it now does.
  - Refuted: the claimed AGENT_NOTES-versus-definition contradiction over the
    drift hook. `AGENT_NOTES.md` requires the CI-fetch *decision* at WP-1;
    the definition deferred the *hook* to WP-8. Both could hold. The real
    defect was quieter -- no WP-1 criterion required the decision to be
    recorded, so nothing enforced it.
- Root cause neither side had named: the batch validation gate is three
  Python commands, and pre-commit excludes `static/` and `templates/`. A work
  package could rewrite every template and stylesheet with a fully green
  gate, in a batch that is nothing but template and stylesheet rewriting.
- Plan vs implementation:
  - Charter: 13 graded modules enumerated by name (130 cells, `__init__.py`
    excluded by a stated empty-module rule); docsync and `scripts/dev/`
    excluded with reasons rather than left ambiguous; provenance block
    naming branch, SHA and clean state; symbol-based hotspot discovery
    replacing hardcoded line numbers and counts; baseline widened to the
    whole finding corpus plus the archive and every report from 2026-02 on;
    A/B/C/D rubric with the B/C line defined as exception-versus-pattern;
    Boy Scout window fixed at commits since the February audits; a
    resolved-finding branch for C/D cells; a migration-blocking severity
    policy with a one-line verdict required in the report; an instruction to
    retire the charter at close. The budget escape hatch is withdrawn.
  - Batch 21: new `scripts/dev/frontend_gate.py` added as a fourth gate
    command at WP-2 and grown one page per WP, covering stylesheet
    isolation, computed theme tokens in both themes, theme persistence,
    self-hosted font loading, CSV/JPEG export assertions, and headline
    wrapping. The `tailwind-css-drift` hook moved from WP-8 to WP-2, with
    the `always_run` / `pass_filenames` requirement that AGENT_NOTES gap 2
    had already identified and the definition had not carried. Targeted
    criteria added to WP-3 (keyboard and touch reachability for the CSS-only
    hints, label associations, validation parity), WP-4 (both state machines
    including retryable and non-retryable failures), WP-7 (split into a
    backend contract commit and a UI commit), and WP-8 (required frontend
    and accessibility audit, deterministic Bootstrap-removal grep, recorded
    lint disposition). Browser floor documented; `.dark-mode` retirement
    given an owner; criterion 9 reconciled with the per-WP docsync check.
  - FINDINGS.md: F-STYLE-1 (prose legibility, explicitly never a gate) and
    F-STYLE-2 (docstring convention, the black/flake8 line-length
    disagreement, and the unwritten Ruff plan) added. F-SWE-1 corrected --
    it claimed the charter scoped "Python only until Batch 21 ships", a
    commitment the charter never made.
  - AGENTS.md: the F-ID source-tag list named five tags while nine are in
    use. `SWE`, `WORKTREE`, `DATA` and `STYLE` added, and the list is now
    declared complete so the next coined tag gets documented.
- Deviations: the drift hook landed at WP-2 rather than the WP-1 the owner
  proposed. WP-1 changes no template, so nothing consumes the compiled CSS
  until WP-2; WP-2 is the first point where drift can ship.
- Independent review of the amended charter, same day, and the fixes it drove:
  - The migration gate did not say whether it covered existing findings. Read
    the wide way, F-B21-1 blocks WP-1 today -- a resource-release defect in
    `orchestrator.py`, which WP-7 modifies. The gate is now scoped to net-new
    findings in terms, F-B21-1 is named as the case that forces the
    distinction, and an audit that thinks an existing finding should block
    must recommend rather than act.
  - The A/B/C/D rubric graded by frequency ("one place is B, several is C")
    while its own table graded by cost. One leak can be C; five contained
    exceptions can stay B. Rewritten to grade cost, not count. The
    "when torn, over-raise" instruction is deleted -- it contradicted
    Section 4's rule that the audit's value is not volume.
  - Resolved and no-action findings shared one rule. Split: a recurred
    resolved defect earns a new finding; an unchanged no-action rationale
    does not; materially changed assumptions do, explaining the delta.
  - Provenance permitted grading a dirty tree, which no SHA can reproduce.
    A clean worktree is now required before grading starts.
  - The hotspot command was `awk '...{...}'` -- a placeholder that could not
    run, and a poor Python parser besides. Replaced with a tested `ast`
    script in a new Section 5c, deliberately at the left margin: a heredoc
    terminator indented inside the numbered list fails with
    `IndentationError`, which was verified rather than assumed.
  - Boy Scout used `git log`, which lists commits without showing what they
    left behind. Now `git log -p`, with an instruction to read the patches.
  - "Weakest principle repo-wide" overclaimed: the audit excludes the
    frontend, both script directories, and tests as graded subjects. Scoped
    to the audited runtime modules.
  - Cell arithmetic hardcoded 130 in three places while Section 3 allowed the
    principle count to change. All three now derive from the live count.
  - One review point was stale, not wrong: the claim that WP-8 defines no
    frontend principles audit. It does, in this commit's parent -- the
    reviewer was reading `origin/main`, because the amendment is committed
    locally and deliberately unpushed.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --all-files` --
  all hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  root BATCH warning.
- Forward guidance: execute the amended charter against current `main` and
  publish the migration verdict before WP-1 starts. The verified root-hygiene
  plan (audience banners, README tree, DEPLOY.md) is deferred until after
  WP-1 by owner decision; its line numbers will need re-checking.
