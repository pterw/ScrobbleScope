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

### 2026-08-03 - PR #168 Copilot review round 1 (side-task)

- Scope: assessed both Copilot review comments on PR #168; both were
  technically valid and addressed.
- Plan vs implementation:
  - Replaced the canonical `Registry entries 4 and 5` example in
    `AGENTS.md` with symbolic placeholders. The numeric example matched
    the expanded sweep it was explaining, so the rule created its own
    violation and made the related no-current-hits claim false.
  - Corrected the prior side-task's forward guidance. The branch was
    level with `main` immediately after realignment, but applying the
    review-fix commit left it directly based on `main` and one commit
    ahead, not equal to it.
- Deviations: none. Dated point-in-time log references remain unchanged
  under the canonical rule's explicit historical-record exception.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: wait for the next PR #168 review round before WP-1.

### 2026-08-02 - Post-merge branch realign; PR #166 review fixes (side-task)

- Scope: PR #165 was rebase-merged (main tip `458f9ad`). The rebase
  produced the usual 23/23 ahead-behind artifact with an identical tree,
  and PR #166 was opened from it in the reverse direction
  (`main` -> `wip/batch-21`); #167 was opened from a separate Copilot
  branch to fix review comments. The owner closed both.
- Plan vs implementation:
  - `wip/batch-21` reset to `origin/main` and force-pushed with lease;
    ahead-behind is 0/0. Commit history on `main` is intact -- all 23
    commits landed individually. The apparent bunching is rebase
    rewriting committer dates while author dates stay distinct.
  - Reapplied the three valid PR #166 findings here so they arrive
    validated and on one lineage: the `MAX_ACTIVE_JOBS` comment no
    longer claims arrival-order serialization (`threading.Lock` gives no
    FIFO guarantee -- it now says each throttle serializes reservations
    behind a shared lock with no ordering guarantee); the canonical
    numeric-citation sweep covers plural and alternate forms, since a
    pattern written as `Registry #\d` cannot match
    `Registry entries 4 and 5`; and the round-9 entry's "returns
    nothing" claim is qualified to exclude dated point-in-time records,
    which legitimately contain such citations.
  - Third occurrence of a countermeasure scoped to the instance that
    prompted it rather than the class. The rule now says explicitly to
    match plural and alternate forms.
- Deviations: none. PR #167 additionally proposed merging #166; that was
  wrong -- #166 pointed `main` at `wip/batch-21`, so merging it would
  have produced the merge commit the rebase-merge workflow exists to
  avoid.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: branch is directly based on `main`, with this one
  review-fix commit ahead, and is ready for WP-1 after PR review.

### 2026-08-01 - PR #165 round 9; new rules are not retroactive (side-task)

- Scope: three suppressed comments, all valid -- numeric citations into
  ordered lists (`Anti-Pattern Registry entries 4 and 5`, two
  `acceptance criterion 8` references) that the registry's own
  name-based citation rule prohibits.
- Cause, established from history rather than assumed: the citations
  were written in the SSOT pass and the FINDINGS refresh; the rule
  banning them was written two commits later. Nothing swept the
  existing corpus against the new rule, so the rule shipped with a
  backlog of its own violations. The pre-push checklist greps the blast
  radius of *the change*; when the change is a rule, the blast radius is
  the whole repository, and that leap was never made.
- Plan vs implementation: all three citations repointed by name. A
  repo-wide sweep for `entries N`, `Registry #N`, `criterion N`,
  `step N`, `rule N`, `item N` across every canonical doc returns no
  matches outside dated point-in-time log records, which stay as
  written. The lesson was folded into the existing blast-radius
  anti-pattern as one sentence rather than becoming a fifteenth
  registry entry -- see the verbosity note below.
- Deliberate non-action: folded into an existing entry rather than added
  as a fifteenth, because rule text has begun causing findings as well
  as preventing them -- the registry grew long enough to need numbers,
  and the numbers became the defect.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: merge rather than iterate further.

### 2026-08-01 - PR #165 round 8; over-broad claims narrowed (side-task)

- Scope: three suppressed comments, all valid, all fixed.
- Plan vs implementation:
  - The Section 2 note claimed close-out entries for *each* batch live
    in the monolith archive. False: `BATCH18_LOG.md` holds its own
    close-out because that heading carried a `(Batch 18 WP-5)` tag;
    only the `(Batch N close-out)` spelling misroutes. Narrowed here
    and in F-DOCSYNC-3, which carried the same over-broad framing.
  - The Section 2 subsection heading still read "Completed batches
    (definitions archived)" while the table lists the active batch with
    a root definition. Retitled to cover both.
  - `AGENT_NOTES.md` asserted a batch was active and where its
    definition sits in the same breath as declaring that the file does
    not track batch state -- self-contradictory, and false between
    batches. Reduced to the pointer alone.
  - Anti-Pattern Registry, assertions entry: broadened from the one
    phrasing that had failed before (`all N`, ranges) to the full
    quantifier vocabulary, since the narrow sweep is what let "each
    batch" through.
- Assessment of the review loop: none of these three were caused by the
  previous round's fixes -- the fix-causes-finding chain that drove
  rounds 5 through 7 did not repeat. What remains is pre-existing
  over-broad wording in text the sweep touched. On that basis the
  pre-push checklist is working and mechanical enforcement is not yet
  warranted; a consistency-lint hook stays a docsync-WP candidate rather
  than scope creep into this PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: findings have narrowed to wording precision rather
  than correctness; this is the diminishing-returns point. Recommend
  merging rather than requesting another round.
