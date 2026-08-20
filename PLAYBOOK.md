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
  Batch 21 WP-1. PR #169 merged to `main` on 2026-08-08 and the Quality Gate
  is green for `5bc6294`, so the canonical repository-integrity gate and
  read-only worktree guard are shipped and
  F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2 are resolved. Three guard files
  exceed their directory peer caps after review remediation -- accepted as a
  deviation and tracked as F-WORKTREE-4 in FINDINGS.md, not silently. Review
  remediation ran to round 6: rounds 2 through 5 landed before the merge, and
  round 6 was reviewed after the final push, so its four findings reached
  `main` unaddressed. **PR #170 remediated them and merged 2026-08-12**
  (`5b060a2`), so the guard and docsync sources the audit reads are settled.
  Three of its review threads remain open, two of them independent reports of
  F-WORKTREE-5.
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

### 2026-08-15 - PR #171 round-6 threads fixed and all five diagrams audited (side-task)

- Scope: the two unresolved Codex threads on `00c0adb`, both on the Top Albums
  sequence. A prior GLM-5.2 session had left uncommitted diagram edits and a
  list of findings, then stopped before it finished. I checked the two threads
  and every edit that session made against the code, then audited all five
  diagrams with three independent verification agents.
- Verification of the two threads: both are correct. `fetch_top_albums_async`
  groups, normalizes, and thresholds the albums before it returns
  (`orchestrator.py:112-116`), so all of that runs before the empty-result
  check at `orchestrator.py:784`. `process_albums` writes to the cache only
  under `if conn and new_metadata_rows` (`orchestrator.py:591`).
- Verification of the prior session: three of its six edits were wrong. It put
  the hit/miss partition inside the DB-connected branch, but the code
  partitions with or without a connection (`orchestrator.py:567`). It drew
  `cleanup_expired_cache()` as a call to `repositories.py`, but that helper
  comes from `utils.py` (`orchestrator.py:40`). It put the total Spotify match
  failure after the store step, but the check runs first
  (`orchestrator.py:824` before `orchestrator.py:842`).
- Plan vs implementation:
  - Top Albums sequence: rewrote the background-task block and the browser
    block. Grouping now sits before every downstream branch. Persistence is
    conditional and records `db_cache_persisted`. The partition sits outside
    the DB branch. New: the connection close and its `finally` ordering
    against `SpotifyUnavailableError`, the `get_job_context` read behind the
    total-match-failure check, the six `results_complete` outcomes, the
    `/progress` 404, and the two unhandled-exception states.
  - Heatmap sequence: added the housekeeping calls, the page-count stats, the
    5% and 80% progress writes, and the unhandled-exception path. Rebuilt the
    render block: the client requests `/heatmap_data` only at 100%, so the 202
    is a narrow race that restarts polling, not a peer alternative.
  - Development cycle: split the merged fast path so the actionability stop
    applies to comment jobs only, added the push-authorization gate that
    `AGENTS.md` requires between commit and PR, and dropped the E2E claim that
    no rule file makes.
  - Runtime diagram and `docs/ARCHITECTURE.md`: named the eight nodes that
    import `config.py`, corrected the arrow-semantics paragraph, and repointed
    the module-graph reference to SESSION_CONTEXT Section 4 alone.
  - Both structural diagrams passed their audit with no change to the graphs.
- Deviations: the prior session said the fix needed a full rewrite of the
  parallel block. It did not. The corrections are local, but they reach more
  branches than that session touched. The audit also found a real code gap and
  it is recorded as F-B21-1 rather than fixed here: `background_task` and
  `heatmap_task` build the event loop outside the `try`, so a failure there
  leaks a job slot. No production code changed in this commit.
- Validation: all four changed diagrams pass Mermaid validation, checked
  against the exact text now in the files. `pytest -q` -- **590 passed**, 3
  known warnings. `pre-commit run --all-files` -- all hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: push, then reply to the two threads and resolve them.
  PR #171 stays open until the owner says otherwise.

### 2026-08-15 - PR #171 round-5 review threads remediated (side-task)

- Scope: three new Codex threads on `37ca4a9` -- one on the development-cycle
  diagram and two on the Top Albums sequence. All three were verified against
  the code before any edit and all three were valid.
- Verification:
  - `AGENTS.md` L29-44 defines the review-comment fast path (fetch the thread
    first, stop if not actionable, else read only the scoped files), but the
    development-cycle diagram routed every review finding through the full
    bootstrap gates. The diagram and the rules it documents were written in
    the same PR and disagreed.
  - `_fetch_and_process()` stores an empty result, marks progress 100%, and
    returns before pre-slicing, cache access, or Spotify enrichment when
    `filtered_albums` is empty. The Top Albums sequence sent every successful
    page fetch into those stages.
  - `process_albums()` catches `_batch_lookup_metadata()` exceptions, records
    `db_cache_warning`, treats every album as a miss, and continues to Spotify
    (possibly persisting via the open connection). The diagram's connected
    path presented lookup as unconditional and its unavailable path said
    persistence was skipped.
- Plan vs implementation: the development-cycle diagram now branches on
  review-finding/comment-job before full bootstrap (fetch thread, stop if not
  actionable, else read scoped files); the Top Albums sequence now stops after
  an empty filtered set and adds a fail-open cache-lookup-error continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the empty-filtered-set and fail-open lookup
  paths.
- Validation: both updated diagrams pass Mermaid validation and open in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this remediation, then resolve the three
  threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 final four review threads remediated (side-task)

- Scope: the four remaining unresolved review threads on `e73540d` -- two
  Codex path-repointing reports and two Codex Top Albums sequence reports.
  All four were verified against the code and the moved files before any
  edit and all four were valid.
- Verification:
  - `docs/superpowers/plans/2026-08-11-pr-170-remediation.md` still cited
    `docs/history/GUARD_HARDENING_2026-08-11.md` and
    `docs/history/REPOSITORY_SYNTHESIS_2026-08-11.md`, both moved to
    `docs/history/reports/` by commit `5865c55`. The links resolved to
    nonexistent files.
  - `docs/history/definitions/BATCH9_DEFINITION.md` pointed twice to
    `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`, and
    `BATCH10_DEFINITION_2026-02-21.md` pointed to the old
    `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md` and
    `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md` paths. All three reports
    now live under `docs/history/reports/`. These are definition-to-report
    references, not exempt point-in-time citations, so they must be repointed.
  - `_fetch_and_process()` returns immediately after `set_job_error` when
    `fetch_metadata["status"] == "error"`, while a `partial` status records
    `partial_data_warning` and continues. The diagram drew an unconditional
    transition from page fetching into grouping.
  - `_fetch_spotify_misses()` raises `SpotifyUnavailableError` when token
    acquisition fails with no cache hits, caught in `_fetch_and_process` as
    `set_job_error("spotify_unavailable"); return []` -- no merge or store.
    The diagram's no-cache-hits branch rejoined the unconditional merge/store
    steps.
- Plan vs implementation: repointed the four report paths in the remediation
  plan and the two batch definitions; the Top Albums sequence now branches on
  Last.fm status (terminal error vs partial-success-with-warning) and
  terminates after the no-cache-hits token failure while retaining the
  cached-success continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the Last.fm error/partial paths and the
  no-cache-hits token failure.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve the
  four threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 final two Codex threads remediated (side-task)

- Scope: the two remaining unresolved Codex threads on `3508c48`, both on the
  Top Albums sequence diagram. Both were verified against the code before any
  edit and both were valid.
- Verification:
  - `_get_db_connection()` returns `None` when `DATABASE_URL` is unset,
    asyncpg is unavailable, or connection attempts fail; `process_albums`
    then sets a `db_cache_warning` stat and skips lookup, cleanup, and
    persistence, so every album becomes a miss. The diagram presented those
    three cache operations as unconditional.
  - `_fetch_spotify_misses()` sets `partial_data_warning` and returns without
    searching when Spotify token acquisition fails and cache hits exist, so
    the pipeline completes successfully with cached albums only; it raises
    `SpotifyUnavailableError` only when no cache hits exist. The diagram sent
    every miss through search and grouped the token failure with the terminal
    path.
- Plan vs implementation: the Top Albums sequence now branches on DB
  availability before the cache lookup and branches the Spotify token-fetch
  failure into a success-with-warning path (cached albums only) versus the
  terminal `spotify_unavailable` path.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the DB-disabled fallback and the partial-cache
  continuation.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview; the tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve both
  threads. PR #171 remains unmerged pending separate owner instruction.
