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
- **Next action:** execute the amended F-SWE-1 principles audit against the
  current `main`, then proceed to Batch 21 WP-1. **PR #171 merged to `main`
  on 2026-08-19** (`bb187ae`, rebase merge) with zero unresolved review
  threads after eight rounds; `wip/batch-21` was realigned to it.
  `docs/SWE_AUDIT_CHARTER.md` and `BATCH21_DEFINITION.md` were both amended
  the same day by a preflight review -- the charter could not work as the
  gate its position implies, and the batch gate could not fail on frontend
  work. Read the charter before executing: the audit now blocks WP-1 on P0
  findings and on correctness defects in modules Batch 21 modifies, and the
  report must state that verdict explicitly.
  Earlier context, still true: PR #169 merged 2026-08-08 shipping the
  repository-integrity gate and read-only worktree guard, resolving
  F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2; three guard files exceed their
  directory peer caps, accepted as a deviation and tracked as F-WORKTREE-4,
  not silently. PR #170 merged 2026-08-12 (`5b060a2`), settling the guard and
  docsync sources the audit reads.
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
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --all-files` --
  all hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  root BATCH warning.
- Forward guidance: execute the amended charter against current `main` and
  publish the migration verdict before WP-1 starts. The verified root-hygiene
  plan (audience banners, README tree, DEPLOY.md) is deferred until after
  WP-1 by owner decision; its line numbers will need re-checking.

### 2026-08-19 - PR #171 round-8 thread fixed: push authorization in the cycle diagram (side-task)

- Scope: one unresolved Codex thread on `docs/architecture/development-cycle.md`,
  raised again by an owner-side human peer on the grounds that this diagram
  purports to govern agents. Checked against the ruleset before editing. Valid.
- Verification: the diagram had a single unconditional edge,
  `Authorize -->|Review-fix commit on an open PR| PR`. `AGENTS.md:234-242`
  grants that standing exception to Claude Code and Codex sessions only and
  says in terms that it does not extend to GitHub Copilot task sessions or
  their subagents, Jules, or any other agent. An agent reading the canonical
  diagram would therefore push a review-fix commit that the ruleset requires
  it to pause on.
- Plan vs implementation: the decision node now carries three edges instead of
  two. WP and batch commits pause in any session; the direct path is labelled
  Claude Code or Codex only; every other agent routes to the same pause. Added
  prose naming `AGENTS.md` as the owner of the rule, and recording the three
  actions that always need explicit instruction whatever the session --
  force-pushes, history rewrites, and anything targeting `main` -- plus the
  Copilot platform-tool requirement at `AGENTS.md:243-244`, neither of which
  the diagram had carried.
- Deviations: none. No code changed.
- Validation: the edited diagram was validated before it was written --
  `valid = true`, type `flowchart`. `pytest -q` -- **590 passed**.
  `doc_state_sync.py --check` -- exit 0 with the expected root BATCH warning.
- Forward guidance: next action unchanged -- the F-SWE-1 audit, then WP-1. A
  preflight amendment to the charter and the Batch 21 WP gates is agreed and
  pending; see the owner decisions recorded with it.

### 2026-08-19 - PR #171 round-7 threads fixed (side-task)

- Scope: the three unresolved Codex threads left on `3d15849` after the
  diagram audit. All three are P2 and all three were checked against the
  source before any edit. All three are correct.
- Verification and fixes:
  - `top-albums-sequence.md` drew `Close connection` unconditionally, but
    `process_albums` closes inside `if conn` (`orchestrator.py:603-604`), so
    the no-connection branch never closes anything. Wrapped in an `opt DB
    connected` block.
  - The same diagram claimed the browser never posts `results_complete` on an
    error payload. `loading.js:209-229` shows only the retryable branch stays
    on the page; a non-retryable error waits three seconds and calls
    `redirectToResults()`, which does post. Split the branch by `retryable`
    and routed the non-retryable case to the processing-error page.
  - `FINDINGS.md` F-B21-1 stated `MAX_ACTIVE_JOBS` is 5 as an absolute.
    `config.py:31` reads it from the environment with 5 as the default, and
    the literal contradicted F-LOAD-1 in the same file. Reworded to name 5 as
    the default and tie the failure count to configured capacity.
- Deviations: none. No code changed; F-B21-1 stays open and unfixed, because
  it is a code change for a code batch.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --files` on both
  edited files -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected root BATCH warning. The edited Mermaid diagram was validated
  through the Mermaid Chart validator: `valid = true`, type `sequence`.
- Forward guidance: the next action is unchanged -- the F-SWE-1 audit, then
  Batch 21 WP-1.

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
