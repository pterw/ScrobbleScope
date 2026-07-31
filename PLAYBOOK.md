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

Close-out entries for each batch currently live in the monolith archive,
not the per-batch log (see FINDINGS F-DOCSYNC-3).

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

### 2026-07-31 - MAX_ACTIVE_JOBS default 10 -> 5 (side-task)

- Scope: owner decision. The 2026-03-04 load test ran 2/3/5 concurrent
  users clean while the 10-user run never completed; all jobs share the
  global 10 req/s API throttle, so 10 slots starve each job below
  1 req/s on the single small Fly.io machine.
- Plan vs implementation: `scrobblescope/config.py` default changed to
  `"5"` with a rationale comment (still env-overridable); README (three
  mentions), SESSION_CONTEXT key-runtime-facts line, and FINDINGS
  F-LOAD-1 phrasing updated to match. `fly.toml` sets no
  `MAX_ACTIVE_JOBS` override, so the new default takes effect on next
  deploy.
- Deviations: pre-change scouting claimed no test depends on the
  default (capacity tests inject their own semaphores) -- true for
  assertions but not for shared state. Route tests that mock
  start_job_thread acquire a real slot that is never released, and the
  session's accumulated leaks crossed the new cap of 5, failing
  `test_heatmap_loading_json_body` with a real 429. Fixed properly: a
  new autouse `fresh_job_slots` fixture in `tests/conftest.py` resets
  the semaphore per test, removing the hidden inter-test ordering
  coupling the lower cap exposed.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner can observe the 5-slot cap locally; the
  "N/5 slots in use" occupancy hint remains open as F-LOAD-1.

### 2026-07-31 - FINDINGS refresh: batch-closure pointers, F-DOCSYNC-4, F-SWE-1 (side-task)

- Scope: owner-flagged staleness in FINDINGS.md -- open P1 items that
  Batch 21's definition already promises to close carried no pointer,
  and F-B20-4 paraphrased the whole definition.
- Plan vs implementation:
  - F-B20-3: remedy rewritten -- the 5.1->5.3 CDN-consolidation path is
    dead; Batch 21 resolves the split by eliminating Bootstrap (closes
    at WP-8). F-AUDIT-1: closes at Batch 21 WP-2 via acceptance
    criterion 8. F-B18-12 deferred-block line marked as in-batch scope
    (WP-6). F-B20-4 compressed to a pointer at `BATCH21_DEFINITION.md`.
    F-FEATURE-2 line reformatted as a greppable cross-ref bullet.
  - New F-DOCSYNC-4 (resolved): per-batch logs were undiscoverable until
    the Section 2 Log column landed; records the tombstone disposition.
  - New F-SWE-1 (open P1): SWE-principles audit chartered via
    `docs/SWE_AUDIT_CHARTER.md` (next commit), executable cold by a
    dedicated Claude or Codex session; closes by pointing at the report.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: F-LOAD-1's "N/10" phrasing updates with the
  MAX_ACTIVE_JOBS default change (next commit); charter follows.

### 2026-07-31 - PLAYBOOK Section 2 log column; tombstone disposition (side-task)

- Scope: the 18 per-batch logs under `docs/history/logs/` were referenced
  from no working doc (Section 2 had no Log column), making batch history
  discoverable only via a directory glob.
- Plan vs implementation: Section 2 table gained a Log column linking
  `BATCH3_LOG.md` through `BATCH20_LOG.md` (batches 0-2 predate per-batch
  logging); a note under the table points close-out-entry seekers at the
  monolith archive per F-DOCSYNC-3. AGENTS.md Batch Close-Out step 3 now
  requires filling the Log column at close-out so the column cannot go
  stale. Investigated the two 300-byte `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  files under `docs/history/` and `docs/history/logs/`: they are
  deliberate "Moved:" tombstones from the Batch 14 restructure kept for
  backward references -- retained, disposition recorded in F-DOCSYNC-4.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: hygiene commits 3-5 follow (FINDINGS refresh,
  MAX_ACTIVE_JOBS 5, SWE audit charter).

### 2026-07-31 - Bootstrap-doc SSOT pass: single-source rules and state (side-task)

- Scope: owner-requested hygiene sweep before Batch 21 WP-1. Exploration
  confirmed AGENTS.md and HANDOFF_PROMPT.md contradicted each other
  (bootstrap order, sufficiency gate, pre-commit gate, ownership map),
  commit discipline existed in 3-4 copies, the heatmap perf measurement
  in 4 copies, and AGENT_NOTES.md carried live batch state under a
  shipped-feature heading plus Batch 19 residue and a pointer to a
  non-repo file.
- Plan vs implementation:
  - AGENTS.md is now the single owner of rules: canonical 7-step
    bootstrap order (AGENTS.md itself is step 1), the stricter 3-way
    sufficiency gate, a 6-step pre-commit procedure including the
    doc_state_sync --check gate, the conflict-resolution rule, and four
    new anti-patterns (never --no-verify; stale Section 3; missing log
    entries; stale dashboard figures -- the ~72% coverage figure
    survived five months while reality was 89%). Docstring mandate moved
    into Proposal and Design Rules.
  - HANDOFF_PROMPT.md reduced to what it uniquely owns: post-read
    verification (git status/log + pytest count reconciliation) and the
    end-of-session handoff checklist; all rule sections now link to
    AGENTS.md instead of restating.
  - AGENT_NOTES.md: batch state moved out (PLAYBOOK Section 3 declared
    the single source); Heatmap section retitled shipped and trimmed of
    Batch 19 residue; venv rules and runtime constants replaced with
    links to their owners; load-test pointer now inlines the conclusion
    (2/3/5 clean, 10 never completed) and flags the raw data as
    agent-side; Talisman note repointed to the archived Batch 17 log;
    orchestrator-split note repointed to F-B20-2; the ten software
    principles expanded from bare acronyms.
  - SESSION_CONTEXT: Section 3 now lists all 7 CSS / 7 JS files and the
    template set (Batch 21 touches exactly these); heatmap perf trimmed
    to an F-B18-11 pointer here and in PLAYBOOK Section 3 -- F-B18-11 is
    the only full copy of the measurement.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: commits 2-5 of the approved hygiene plan follow
  (PLAYBOOK log column, FINDINGS refresh, MAX_ACTIVE_JOBS 5, SWE audit
  charter); then Batch 21 WP-1.
