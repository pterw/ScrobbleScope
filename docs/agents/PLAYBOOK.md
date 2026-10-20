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
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

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

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. That branch merged into `main` as PR #245 on 2026-09-30 and `origin/test` is
  deleted, so side-task PRs branch from `main` and run the guard against its default
  base. The owner names the branch WP-1 opens.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). The WP-0 close-out below is what remains of WP-0. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.
- **What PR #245 ships (owner ruling 2026-09-29):** the WP-0 foundation and
  every fix from the three reviews, including the job module with its storage
  seam, typed provider failures and provider failure logs that carry no
  listener data. Moved to the follow-up PR: job persistence, the Last.fm
  scrobble seams, the album request module, one album-metadata encoding, the
  statistics module and the tooling package.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam and typed provider failures, job persistence
  (gates WP-3), an album request module (gates WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (gates WP-2), one album-metadata
  encoding (gates WP-3), a statistics module (gates WP-6), and provider
  failure logs that carry no listener data. Which of these #245 ships is
  in the "What PR #245 ships" bullet above; the rest wait for the follow-up
  PR.

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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-10-20 - The dashboard names the tranche and its date

Side task, no batch tag: the session dashboard names the side-task tranche and carries today's date, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the dashboard must say what PLAYBOOK Section 3 says, so a new session is not misled about what comes before WP-1.

A freshness audit found `.claude/SESSION_CONTEXT.md` still reading `Last updated: 2026-09-30` although this branch changed it on 2026-10-20, and its `Batch 23 status` row silent on the tranche of side-task PRs that PLAYBOOK Section 3 describes. The date is now 2026-10-20 and the row gains one sentence naming the tranche. Nothing else in the row changed; the Tests row and DOCSYNC STATUS block are untouched. No deviations; no existing test edited.

Validation: `pytest -q` -- **2568 passed**.

### 2026-10-20 - The gate keeps the index card centred at 1080p

Side task, no batch tag: the frontend gate fails when the index card is pinned under the header at 1080p, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the owner saw the index card stop being centred once the separate Albums field made it taller ("the index card isn't properly centered"); the gate should catch that.

What changed: `_form_centring_failures` in `scripts/dev/_frontend_gate_layout.py`, called from `check_large_display_scale_parity` for the 1080p window (1920x945, default state). `positionForm` places the card at `max(0.25rem, (available - height) / 2 - 2.5rem)`, so while the centring term governs the space below the card exceeds the space above by 2 x 2.5rem = 5rem; the check holds that to 2px (rect rounding) and names a card sitting on the 0.25rem clamp as pinned. `_wide_layout_failures` could not see it because it mirrors the clamp in its expected value. Three unit tests in `tests/scripts/dev/test_frontend_gate_layout.py` cover the healthy, pinned and off-centre cases.

Deviations: the brief said the two spaces should be "within one 2.5rem lift of each other"; the rule makes the correct difference 5rem (the lift applies once above and the centring halves the rest), so the tolerance is derived from that. No existing test edited.

Validation: `pytest -q` -- **2568 passed**.

### 2026-10-20 - The Results control is named as on the index card

Side task, no batch tag: the Results page's unmatched control takes the index card's wording, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the two controls should read the same ("Yes that looks good to me", 2026-10-20, on renaming the Results control to match).

What changed: in `templates/results.html` the Sort leaderboard card's control reads "Unmatched albums" with "Hide" then "Include" (Include selected on an include run) and the help "Hide removes the unmatched listens so the leaderboard can be ranked by listening time."; ids, name and values (`results_albums_all` = all, `results_albums_matched` = matched) are unchanged, so `results.js` is untouched apart from three comments. The include gate check, the results-behavior fixture, three comments in `results.js` and `results.css`, README, DESIGN.md, F-B23-43's prose and RECONCILIATION (section 22, ledger rows) follow.

Deviations: none. Edited existing tests: `test_results_include_run_marks_unmatched_rows_and_locks_listening_time`, `test_results_include_run_offers_the_albums_control_for_one_album` and `test_results_plain_run_renders_none_of_the_include_elements` (new copy; the first also asserts the Hide-then-Include order).

Validation: `pytest -q` -- **2564 passed**.

### 2026-10-20 - The unmatched choice joins the Show row

Side task, no batch tag: the index card's unmatched choice moves into the Show row and is renamed, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the separate Albums field made the index card tall and pinned it under the header, so tuck the choice under Show, split the row evenly and make the toggle clearer (rulings 2026-10-20, verbatim in `docs/design/RECONCILIATION.md` section 22).

What changed: `templates/index.html` puts the Show select and the unmatched choice in one `.field-pair` (equal halves from 860px, stacked below, `static/css/index.css`). The label reads "Unmatched albums", the options "Hide" (value 0, default) and "Include" (value 1); ids, name and values are unchanged. The help "Albums Spotify and Deezer can't find, ranked by play count." is rendered `hidden` and `syncUnmatchedLock` in `static/js/index.js` shows it only while Include is chosen. At 1920x945 the default card measures 611px (it was 719px, pinned under the header). The forms gate asserts the help is hidden under Hide and on screen with its exact text under Include, and measures its 7:1 contrast with Include chosen. README, DESIGN.md, three docstrings, a test comment and RECONCILIATION (new section 22, ledger row) follow the code. The Results control keeps its wording until the next commit.

Deviations: none. Edited existing tests: `test_index_albums_control_is_a_pair_of_native_radios` (new copy, hidden help, the shared row) and the docstring of `test_results_loading_passes_the_include_flag_to_the_job_thread`.

Validation: `pytest -q` -- **2564 passed**.
