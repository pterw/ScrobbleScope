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

### 2026-07-31 - DEVELOPMENT.md: correct HANDOFF_PROMPT description (side-task)

- Scope: DEVELOPMENT.md described `HANDOFF_PROMPT.md` as a condensed
  checklist of rules, gates, read order, and commit discipline. That was
  accurate until this branch, which reduced the file to post-read
  verification plus the handoff checklist and replaced everything else
  with pointers. The description was left describing the architecture
  this PR removed.
- Plan vs implementation: two passages corrected -- the architecture
  overview and the per-file section, which was also retitled from
  "Bootstrap Procedure" to "Session Start and Handoff" to match what the
  file now contains. Both now state why the summaries were removed
  (each restatement drifted from its source), which is the reasoning the
  rest of the document uses.
- Deviations: scope-limited on purpose. Only the passages this branch
  made wrong were touched. DEVELOPMENT.md has other known staleness --
  the `gemini-pr-triage` skill is now `pr-bot-triage`, the
  review-suggestions section predates repo-aware review tooling, and the
  closing paragraph needs a rewrite -- all deferred to a post-merge
  documentation pass, per the same in-scope test applied to
  `concurrent_users_test.py` in review round 1.
- Note: this class of staleness is invisible to diff-scoped review.
  Copilot reported "13/13 changed files" across four rounds and
  DEVELOPMENT.md was never among them, so a file made wrong by the diff
  but not part of it cannot be flagged. Worth remembering when relying on
  automated review for consistency.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the post-merge pass should reframe the review section
  around how the tooling changed rather than around rejection, and
  `README.md:492` must move with it -- it currently promises a section on
  suggestions "evaluated and rejected".

### 2026-07-31 - Push rule: standing exception for review-fix commits (side-task)

- Scope: owner-directed policy change, not a review finding. During PR
  #165 triage the owner granted a standing authorization to push
  review-driven commits without asking per round, on the reasoning that
  the agent reaches the diminishing-returns point on its own and a
  per-round approval round-trip only stalls the loop.
- Plan vs implementation: encoded in AGENTS.md Commit Rules step 6 rather
  than left as an agent-side preference, because AGENTS.md is the rules
  SSOT and a spoken rule that contradicts the written one is exactly the
  defect this PR spent four rounds removing. Scoped per owner: **Claude
  Code and Codex sessions only.** GitHub Copilot task sessions and their
  subagents, Jules, and any other agent follow the unmodified rule --
  the owner does not extend equal trust to agents of varying quality
  that it cannot inspect per-invocation. Step 6 already carried a
  Copilot-specific clause, so per-agent scoping had precedent.
- Deviations: the exception is deliberately narrow. Review-fix commits on
  an open PR only; batch and WP commits still pause, and force-pushes,
  history rewrites, and anything touching `main` still require explicit
  instruction.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: if the agent roster changes, this clause names
  specific agents and will need revisiting -- it is an allowlist, not a
  capability test.

### 2026-07-31 - PR #165 Copilot review round 4 (side-task)

- Scope: zero visible comments, two suppressed, both valid and both real
  defects rather than the judgement-call trade-offs round 3 predicted.
  The convergence call made after round 3 was wrong; recorded here
  because the wrong prediction is the useful part. Tally 18/18.
- Plan vs implementation:
  - **A rule was silently deleted by this PR, and round 1 removed the
    last copy.** The prohibition on `git add -A` / `git add .` lived in
    two places before this branch: AGENT_NOTES.md Owner Preferences and
    the old HANDOFF_PROMPT anti-pattern list. The PR's HANDOFF_PROMPT
    rewrite dropped its copy, and the round-1 dedup replaced the
    AGENT_NOTES copy with a pointer to AGENTS.md Commit Rules -- which
    never contained the prohibition. Step 5 only said "stage only files
    changed for this work package", which `git add -A` can satisfy when
    every changed file happens to belong to the WP. Restored explicitly
    in Commit Rules step 5, the canonical location the pointer targets.
  - Lesson: verifying that a pointer's target "covers it in substance"
    is not enough. Round 1 checked AGENTS.md:167 and accepted a
    paraphrase as equivalent when it dropped a prohibition. Before
    deleting a rule copy, diff the *specific obligations*, not the topic.
  - `scripts/testing/concurrent_users_test.py` promised queuing in three
    places. `acquire_job_slot()` uses `acquire(blocking=False)` and both
    call sites (`routes.py:460`, `routes.py:570`) return an error
    immediately, so excess submissions are rejected and never queued.
    Round 1 edited one of those lines for the cap change without
    questioning the surrounding claim. Now describes rejection, matching
    README's "capacity rejections" wording.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: do not call convergence from the *shape* of a round's
  findings. Rounds 2 and 3 returned zero visible comments and were still
  productive; round 4 found a deleted rule. Stop when a round returns
  nothing, not when the findings look minor.

### 2026-07-31 - PR #165 Copilot review round 3 (side-task)

- Scope: round 3 again returned zero visible comments and three
  suppressed ones. Two acted on in full, one acted on in part.
  Suppressed-block tally now 16/16 across #163, #164, and #165.
- Plan vs implementation:
  - `docs/SWE_AUDIT_CHARTER.md` Section 3 copied the ten principle names
    from AGENT_NOTES.md and **had already drifted**: the copy dropped the
    definitions for Dependency Inversion, Least Knowledge, and Fail Fast,
    and truncated SRP from "single responsibility per module/function".
    This is the rare case where the drift was demonstrable rather than
    hypothetical, so the copy is gone. The section now points at
    AGENT_NOTES.md and keeps only the two audit-specific methods (Clean
    Architecture via the SESSION_CONTEXT Section 4 acyclic graph, Boy
    Scout via git history).
  - `docs/SWE_AUDIT_CHARTER.md` Section 6 restated side-task entry
    placement that AGENTS.md Side-Task Handling owns -- and round 2 had
    just renumbered that section, so the charter was already a rewrite
    away from being wrong. Delegated.
  - `HANDOFF_PROMPT.md` Section 1 restated the bootstrap-conflict rule
    verbatim from AGENTS.md:64-65 inside a paragraph that claims rules
    "are not restated here". Removed.
- Deviations: **partially declined** the reviewer's request to also strip
  "Do not push without owner instruction" from the charter's commit step.
  Verified AGENTS.md:171 owns it, so the SSOT argument is technically
  right, but that line sits at the point of action for a cold-start
  executor (the charter is written so Codex can run it without prior
  context) and a push is not reversible. Deliberate safety redundancy is
  worth one line. Removed the same sentence from HANDOFF_PROMPT Section 1
  by contrast, because there the reader is being sent to AGENTS.md in the
  very same paragraph, so the copy buys nothing.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: watch for diminishing returns. Rounds 1-3 were all
  genuine, but the remaining duplication is increasingly load-bearing
  context for cold-start executors; judge each on whether the copy can
  drift *and* whether losing it costs a reader who cannot see the source.
  Batch 21 WP-1 remains the next action.
