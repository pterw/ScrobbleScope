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

### 2026-08-01 - PR #165 round 7 + review-loop pattern sweep (side-task)

- Scope: owner asked for the round-7 findings to be verified but not
  fixed until a sweep across every review round on PRs #163/#164/#165
  identified why fixes keep producing new findings. Corpus: ~40
  findings over 12 rounds.
- Round 7 findings (all three valid):
  - `AGENTS.md` close-out step 3 said "add a row" to PLAYBOOK Section 2,
    but the active batch already has one -- following it literally
    duplicates the row. Now says repoint the existing row, add only if
    absent.
  - The sufficiency gate required agreement with "the batch definition"
    while bootstrap step 3 states no definition exists between batches,
    so the gate was unsatisfiable in that state. Both states now
    stated.
  - `docs/SWE_AUDIT_CHARTER.md` labelled its differential baseline
    "Open findings" while including F-DOCSYNC-4, resolved earlier in
    this same PR. Relabelled as already-tracked regardless of status,
    with an instruction to check each `Status:` line.
- Sweep results -- four recurring classes, now in the Anti-Pattern
  Registry. Two were already logged; two are new:
  - *Fixing the instance instead of the class* (logged previously): the
    dominant cause. Rounds 6 and 7 findings were created almost
    entirely by rounds 5 and 6 fixes.
  - *Lossy or contradictory consolidation* (new): collapsing duplicated
    rules to one owner while leaving copies, dropping a specific
    prohibition (the `git add -A` ban nearly vanished this way), or
    contradicting another section of the same file.
  - *Assertions over sets, ranges, and citations* (new): "all seven CSS
    files", "F-DOCSYNC-1 through F-DOCSYNC-4", citing a gitignored
    file, citing an anti-pattern that does not cover the case.
  - *Happy-path-only procedures* (new): steps that break in an edge
    state -- row already present, no definition between batches, gate
    ordered before the work it validates.
- Why the loop exists, and the structural fix: the validation gates
  check mechanics only -- nothing verifies that one document still
  agrees with another, so each fix's damage is discoverable only by the
  next review round. Added a "Pre-push self-review" block to Commit
  Rules: read changed files whole rather than as diffs, run the
  blast-radius greps, walk procedures through edge states, and prefer
  deletion to addition because every added sentence is new surface area.
- Deviations: none. The new checklist caught its own first violation --
  the draft cited registry entries by number, which the same registry
  forbids; now cited by name.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the honest test is round 8. If it finds fresh
  self-inflicted drift, the checklist is not enough and the next step is
  mechanical enforcement (a consistency-lint hook) rather than more
  prose.

### 2026-08-01 - PR #165 review round 6; self-inflicted-drift anti-pattern (side-task)

- Scope: round 6 returned three suppressed comments, zero visible. All
  three verified valid -- and all three were created by round 5's own
  fixes, which is the finding that matters more than the fixes.
- Plan vs implementation:
  - Acted: `AGENTS.md` Side-Task Handling and `HANDOFF_PROMPT.md` both
    cited "Commit Rules step 4" for the documentation requirement; the
    round-5 reorder moved it to step 1. Repointed **by name** ("the
    documentation step", "Missing log entries") rather than by number,
    so a future reorder cannot re-stale them.
  - Acted: `AGENT_NOTES.md` load-testing bullet still asserted the
    per-job guarantee and single-throttle model that round 5 corrected
    in `config.py`. Rewritten to match and to point at `config.py` as
    the single owner of the rationale.
  - Declined (precedent): PLAYBOOK Section 4 entries at :163 and :262
    also contain "step 3/4/6" references that no longer match the
    current numbering. They are dated point-in-time records of what was
    true when written; retro-editing rotated log content was declined
    and accepted in PR #162 round 3 and PR #163 round 3.
  - Root-cause fix: new Anti-Pattern Registry entry 11, "Fixing the
    instance instead of the class" -- requires a blast-radius grep
    before the gates (references to anything renumbered/renamed, and
    sibling copies of any corrected claim), and prefers name-based
    cross-references over numeric ones.
  - Swept beyond the three findings: verified the remaining numeric
    references (`AGENTS.md` close-out step 2, charter bootstrap step 1)
    still resolve correctly, and that the `req/s` claims in F-B18-11 and
    F-B18-10 are accurate because the heatmap and album pipelines are
    both Last.fm-only.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply.

### 2026-08-01 - PR #165 Copilot review round 5 (side-task)

- Scope: round 5 returned "not ready to approve" with four suppressed
  comments and zero visible ones. All four verified valid against the
  code; all four acted on.
- Plan vs implementation:
  - `config.py`: the MAX_ACTIVE_JOBS rationale claimed "one global
    10 req/s API throttle". Wrong -- `utils.py:81-82` builds separate
    `_LASTFM_THROTTLE` and `_SPOTIFY_THROTTLE`. Comment now names the
    Last.fm scrobble-fetch phase as the binding constraint.
  - `AGENTS.md` commit procedure: the docsync `--check` gate sat at
    step 3 while the PLAYBOOK update was step 4, so the gate ran before
    the documentation it validates (and `pre-commit` carries the
    `doc-state-sync-check` hook). Reordered: write docs, `--fix`, then
    the three gates on the final state. This matches what sessions
    already do in practice; only the written rule was wrong. Fixed a
    duplicate step number introduced by the renumber.
  - `FINDINGS.md` F-DATA-1 open question 2 proposed grouping
    `spotify_cache` by `artist_norm + album_norm` -- which is the
    primary key (`init_db.py:42`), so every group holds exactly one row
    and the upsert has already overwritten any rival date. Replaced
    with the two methods that can actually work (re-run the Spotify
    search and compare against the earliest fresh candidate, or
    cross-check MusicBrainz).
  - `docs/SWE_AUDIT_CHARTER.md`: prescribed commit subject was a noun
    phrase, violating the imperative-subject rule the charter tells
    executors to follow. Now imperative.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply. PR #165 remains merge-ready pending the next
  auto-review.
