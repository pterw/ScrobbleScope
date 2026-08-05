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
- **Next action:** finish the read-only worktree-safety guard CLI and canonical
  bootstrap gate before the full F-SWE-1 sweep and Batch 21 WP-1. The pure
  classifier is implemented and tested; F-WORKTREE-1 and F-WORKTREE-2 remain
  open until the executable gate validates the live linked worktree.
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

### 2026-08-05 - Worktree classifier review remediation (side-task)

- Scope: resolved the first review round for Task 1 without expanding the
  pure classifier into Task 2's Git discovery or bootstrap integration.
- Plan vs implementation:
  - Restored Steps 2, 4, and 6 of the authoritative plan to run only the
    parser/lineage test file that exists at those stages; Step 10 onward keeps
    both focused paths after the venv test file is created.
  - Added parameterized both-sided-divergence coverage for a missing head tree,
    missing base tree, and both trees missing. Every unavailable-tree state now
    asserts WT005, while only two present matching IDs assert WT004.
  - Replaced remediation-fragment checks with the full mandated WT004 and WT005
    strings, protecting dirty reconciliation, refreshed-base/tree verification,
    owner authorization, force-push-with-lease boundaries, and the explicit
    prohibition on reset, rebase, or force-push for true divergence.
  - Mutation verification weakened both remediation constants and treated two
    missing IDs as equal; the strengthened suite produced five expected
    failures before the original correct behavior was restored.
- Deviations: none; production behavior was already correct, so this round
  strengthens regression protection and repairs plan execution order only.
- Validation: parser/lineage suite -- **23 passed**; complete focused guard
  suite -- **30 passed**. `pytest -q` -- **459 passed** with 3 existing
  aiohttp/Python 3.13 warnings. Final hooks and docsync gates pass.
- Forward guidance: proceed to Task 2's read-only CLI and bootstrap wiring;
  F-WORKTREE-1 and F-WORKTREE-2 remain open until its live linked-worktree
  acceptance passes.

### 2026-08-05 - Pure worktree safety classification (side-task)

- Scope: implemented the pure, read-only classification layer for the
  worktree-safety guard without wiring it into bootstrap or running Git.
- Plan vs implementation:
  - Added strict PLAYBOOK Section 3 parsing that ignores historical log text,
    preserves missing active-branch metadata, and rejects missing, duplicate,
    or malformed active state rather than guessing.
  - Added deterministic lineage diagnostics for detached CI/local states,
    missing or wrong active branches, dirty trees, behind-only state, and both
    content-identical rebase artifacts and true divergence. Remediation is
    diagnostic only and performs no repository mutation.
  - Added platform-aware environment resolution for ordinary and linked
    checkouts. Linked worktrees reuse the primary checkout `.venv`; distinct
    secondary environments and missing required tools fail with actionable
    diagnostics, while a symlink/junction alias to the primary environment is
    accepted.
  - Corrected two plan-interface contradictions while preserving its safety
    policy: lineage snapshots now carry the parsed active-batch discriminator,
    and the WT005 test verifies that remediation explicitly prohibits reset
    without contradicting the mandated `do not reset` wording.
  - Split immutable value types and virtualenv tests into focused peer-sized
    files to satisfy the repository's new-file size gate; the public imports
    and focused test command remain explicit in the corrected plan.
- Deviations: specification-preserving interface/test corrections only; no
  dependencies, package installs, Git commands, automatic repairs, or
  bootstrap enforcement were added.
- Validation: focused worktree-guard suite -- **27 passed**. `pytest -q` --
  **456 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: Task 2 must add the thin read-only CLI, canonical bootstrap
  rule, and real linked-worktree acceptance before F-WORKTREE-1 and
  F-WORKTREE-2 can close. The pure classifier is testable but is not yet a
  mandatory bootstrap command.

### 2026-08-05 - Docsync content-integrity plan final remediation (side-task)

- Scope: closed the plan-wide final review findings without changing the
  approved deterministic-only enforcement architecture.
- Plan vs implementation:
  - Made the newest live full-suite `pytest -q` validation in PLAYBOOK the
    authoritative test count, including side-task entries outside the
    current-batch markers; the renderer and DOC006 now share that result and
    reject conflicting named SESSION_CONTEXT count fields.
  - Tightened active-definition matching to a complete numeric batch token
    and limited DOC001's exemption to the exact Section 3 declaration.
  - Converted Git invocation `OSError` failures to sanitized `SyncError`
    diagnostics so the CLI returns 2 without a traceback, preserved analyzer
    input immutability, and strengthened the two-reference regression.
  - Refreshed the docsync package/dependency inventory and all measured test
    counts; DEVELOPMENT remains explanatory human documentation only.
- Deviations: none; no dependencies, semantic auto-fixes, or Git history
  changes.
- Validation: focused docsync suite -- **156 passed**. `pytest -q` --
  **429 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.

### 2026-08-05 - Docsync integrity review remediation (side-task)

- Scope: addressed the first Task 2 review round without changing the
  approved enforcement design.
- Plan vs implementation:
  - Added CLI regression coverage proving `--fix` returns 1 with DOC001 for
    an unresolved dead live reference and emits no stale DOC005 after it
    repairs the session block.
  - Moved resolved F-DOCSYNC-5 out of the active P0 section, leaving only the
    two worktree safeguards as open P0 gates.
  - Corrected the Task 2 focused-suite record to the measured post-remediation
    count.
- Deviations: none.
- Validation: specified docsync suite -- **112 passed**. `pytest -q` --
  **420 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.
