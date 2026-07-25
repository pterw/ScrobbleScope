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

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `BATCH21_DEFINITION.md` |

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
- **Next action:** Batch 21 WP-1 (Tailwind + daisyUI toolchain and theme
  tokens; no template changes).
- Batch 21 WP status: WP-0 done. WP-1 through WP-8 not yet started.
- **Perf note (measured 2026-05-16):** Heatmap fetch for `flounder14`
  (103 pages) took 10.9s. `lastfm.py` already uses `limit=200` and concurrent
  `as_completed` fetching. 10.9s is the rate-limit floor (103 pages /
  10 req/s = 10.3s minimum). No further optimization without heatmap-specific
  caching or rate-limit risk. Documented in FINDINGS.md F-B18-11.
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

### 2026-07-24 - Batch 20 complete; definition archived, log purged (Batch 20 close-out)

- Scope: Batch 20 WP-8 close-out per the AGENTS.md procedure.
- Plan vs implementation:
  - `doc_state_sync.py --fix --keep-non-current 0` purged the 4 rotated
    non-current side-task entries into the monolith archive.
  - `git mv BATCH20_DEFINITION.md docs/history/definitions/` and marked
    the archived definition header Complete.
  - PLAYBOOK Section 2: Batch 20 row now links to the archived
    definition. Section 3: Batch 20 marked complete; Batch 21 (UI
    overhaul) flagged as next, awaiting the owner's in-progress UI
    proposal.
  - `.claude/SESSION_CONTEXT.md` Section 1: Batch 20 row set to
    Complete (all 9 WPs); Batch 21 row set to next-batch status. The
    "22 test modules" wording was already correct from earlier WPs.
- Deviations: none. Batch ran WP-0..WP-5 via Copilot PRs (#153/#155/
  #156/#159), then a post-merge audit follow-up commit plus WP-6, WP-7,
  and this close-out on `wip/batch-20` in a worktree.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with only the
  expected `BATCH21_DEFINITION.md` root warning remaining.
- Forward guidance: next batch is Batch 21 (UI overhaul); expand
  `BATCH21_DEFINITION.md` into WPs once the owner's proposal lands.
  `wip/batch-20` holds four unpushed commits awaiting owner review and
  push/PR instruction.

### 2026-07-24 - PR #162 review response (side-task)

- Scope: address the Copilot review on PR #162 (Batch 20 completion).
  All six comments (four inline + two suppressed low-confidence) were
  valid doc-consistency catches; five acted on fully, one partially.
- Plan vs implementation:
  - `FINDINGS.md`: header status updated to Batch 20 complete / Batch 21
    next; `Source:` added to F-B20-4 and F-B18-11; `Status:` lines added
    to all P2, Info, and feature items; shipped F-FEATURE-2 rotated to
    the archive with a cross-reference note.
  - `AGENTS.md` Finding-Writing Rules: rotation rule clarified --
    standing design-decision Info items (F-LOAD-3..5) keep their F-IDs
    in the active file and rotate only when superseded. This is the
    partial decline: archiving them would contradict the Batch 20
    definition's WP-6 intent.
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: header claim narrowed
    to ID/history preservation (bodies may be condensed at rotation).
  - `PLAYBOOK.md` Section 3: "unpushed pending owner instruction"
    replaced with "submitted as PR #162" (the Section 4 close-out entry
    keeps the original wording as a point-in-time record).
  - `AGENT_NOTES.md`: stale "Batch 20 is now active" block updated to
    complete/archived status with Batch 21 next.
  - `BATCH21_DEFINITION.md`: baseline refreshed 389 -> 390.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: batched reply posted on PR #162; awaiting merge.
  Batch 21 scope expansion remains next once the owner's UI proposal
  lands.

### 2026-07-24 - PR #162 review response, round 2 (side-task)

- Scope: address Copilot's second review round on PR #162 (four inline
  comments + one suppressed). All five verified valid; all acted on.
- Plan vs implementation:
  - `FINDINGS.md` F-MAS-4: `except Exception` count updated 14 -> 17
    (verified by grep; Copilot's per-file breakdown was exact) with the
    recount date noted.
  - `FINDINGS.md` deferred-block pointer corrected: detailed bodies live
    in pre-Batch-20 FINDINGS.md via git history (before `494f2c7`), not
    under `docs/history/` as previously claimed.
  - `FINDINGS.md` F-FEATURE-2 cross-reference recast as a direct
    sentence (grammar).
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: F-FEATURE-2 heading
    suffix normalized to `-- RESOLVED (shipped in Batches 18/19)` per
    the AGENTS.md suffix rule.
  - Archived `BATCH20_DEFINITION.md` header relabeled `Baseline:` ->
    `Final count:` so it no longer conflicts with the definition's
    unchanged 389-baseline plan text.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: PR #162 ready for merge; Batch 21 definition draft
  sits uncommitted in the worktree awaiting owner approval.

### 2026-07-24 - PR #162 review response, round 3 (side-task)

- Scope: Copilot round 3 (two comments + one suppressed duplicate).
  One acted on, one declined.
- Plan vs implementation:
  - Acted: both F-B19-6 archive headings moved their portion qualifier
    after the colon to match the `F-<context>-<N>: <title>` format the
    batch itself established (AGENTS.md Finding-Writing Rules).
  - Declined: updating the `BATCH20_DEFINITION.md:107-108` citation
    inside the archived `docs/history/logs/BATCH20_LOG.md` WP-3 entry.
    Rotated log entries are point-in-time records (same principle as
    the round-1 "unpushed" decline, which the reviewer accepted), they
    are machine-rotated content the docsync tooling owns, and the
    filename remains uniquely greppable at its archived location.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds are now in pure-style territory;
  recommend merging PR #162.
