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
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
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

### 2026-09-30 - MusicBrainz dates the unmatched rows on Results

Side task, no batch tag: MusicBrainz dates the unmatched rows on Results, on the include-unmatched branch (a small PR off main after the cover-washes PR). The commit landed on 2026-10-01; the entry keeps the day of the work.

Owner intent: an included unmatched album gets its release year once MusicBrainz finds it, without the list moving.

What changed: the page script (`static/js/results-release-checks.js`) fills the "unknown" cell of an unmatched row with YYYY-MM and puts the full date in the cell's `data-export` for a confirmed or moved-out finding; a moved-out row also gets the note. The worker and `/api/release_checks` already stored and served the outcome and the date for an unmatched row; new tests pin that, and the rank order. A new frontend-gate check, "include results page" (`scripts/dev/_frontend_gate_include.py`, desktop and mobile), seeds a real include job and asserts the marker and "unknown" text at 7:1 in both themes, the Albums control's option and selected text at 7:1 and its selected boundary at 3:1 against the track and against the card, Matched only (unmatched rows hidden, ranks 01..03, Listening Time enabled), the Sort leaderboard's unselected hover at 7:1, the selected option's forced-colours border equal to `Highlight`, and no horizontal overflow at 390 and 1280. A new behaviour-script test pins the fill. DESIGN.md's segmented-control track line now states the code: the page canvas fill, a 1px hairline border, the 8px radius and 3px padding at scale 1 (the old line also said a 999px pill and 4px padding, which the code never had). The architecture pages name the new gate module and the fill.

Fix (review fold-in, Minor 1): a cached finding and a fresh lookup now reach the same outcome for a result row. `_resolve_cached` stored confirmed for any cached date on the premise that a result is in the list because of that date, which does not hold for an included unmatched row; it would have shown a 1999 date as confirmed in a 2025 run. One function, `_result_outcome(original_release, params)` (unavailable, confirmed or moved out through `_matches_window`), now serves `_check_candidate` and `_resolve_cached`; a cached moved-out row raises the moved-out count as a fresh one does. Mutation: making `_resolve_cached` store confirmed unconditionally again fails `test_a_cached_finding_gives_an_unmatched_row_the_outcome_a_lookup_would[out_of_window]` (`assert 'confirmed' == 'moved_out'`); restored, 55 passed. No exception text reaches a log line. The architecture page's `_frontend_gate_layout` line was reflowed (Minor 4).

Deviations: DESIGN.md also corrected the track's radius and padding, as above. The `tr[hidden]` rule in `static/css/results.css` looks redundant (the rows are hidden by the `[hidden]` rule in the compiled sheet); it is not touched here and is filed as a finding by the controller.

Known limits: this entry replaces the wording Task B's entry carries. The Albums control's option and selected text and the Sort leaderboard's unselected hover at 7:1 in both themes, and the selected option's forced-colours `Highlight` border, are now asserted on the rendered include page by the gate. The remaining limit: the gate seeds the page and does not render a live MusicBrainz pass (the behaviour script and pytest cover the fill and the worker).

Edited existing tests: test_run_release_checks_records_the_date_from_a_cached_finding (its cached date moved from 1977-02-04 to 2025-01-15, inside the job's 2025 window, so the cached finding is still confirmed under the one outcome rule).

Validation: `pytest -q` -- **2555 passed**.

### 2026-09-30 - Results list unmatched albums when the listener asks

Side task, no batch tag: unmatched albums on the Results page, an "Albums" control that hides them and one lifted look for every segmented control, on the include-unmatched branch (a small PR off main after the cover-washes PR). The commit landed on 2026-10-01; the entry keeps the day of the work.

Owner intent: an include run shows the albums Spotify and Deezer could not match, marked, and the listener can hide them to rank by listening time.

What changed: an include run merges the job's unmatched entries into the results (`merge_unmatched_rows`); each row has plain rank and title, the cover wash, a Not Found or Unavailable marker, an "unknown" release (the page script's `??` fallback was needed by that empty cell) and a play-count metric. Total Albums reads "listed" and Scrobbles sums every row. The Sort leaderboard card gains an "Albums" segmented control (All / Matched only, `name="results_albums"`) that hides the rows, renumbers, recounts and enables Listening Time. `.seg` and `.seg__option` moved to `static/css/shell.css`. The shared look is lifted per the owner rulings "The 4.5 is a floor not a goal" and "Precisely use what exists; segmented control": option text takes the body token (8.71 light, 10.61 dark on the track), the selected chip keeps its soft fill, gains a 1px primary border (6.06 / 8.14) and takes base-content text (14.81 / 13.04), and an unselected option deepens to base-content on hover (review fold-in, was primary at 6.06). Results' Sort leaderboard buttons take the same tokens through `aria-pressed`, which the template now renders. The frontend gate gains `seg_contrast_*` (text 7:1, boundary 3:1, both themes, four controls) and `seg_hover_failures` (hovered unselected option and the chip, 7:1, on the index Rank by control). `static/css/tailwind.css` was rebuilt by the drift hook. RECONCILIATION Section 21 and two ledger rows record the overrides; Section 20 notes that Section 21 moves the Results help to the same token; DESIGN.md and README follow.

Deviations: the behaviour script loads no stylesheet, so Results colour ratios are held in the frontend gate and the script holds the JS state; the marker and "unknown" facts are pinned by the route tests against the real template. The dating of "unknown" releases is not shipped here.

Known limits: the behaviour script's `include_run` fixture seeds a Top Artist the real page would not start with, and the toast text, the restored title after un-hide and the Top Artist update have assertions but no planted defect; the Results "Albums" control's contrast and the forced-colours `Highlight` border are not gated; no frontend-gate check renders a real include Results page yet.

Edited existing tests: test_results_include_run_marks_unmatched_rows_and_locks_listening_time (assertions).

Validation: `pytest -q` -- **2547 passed**.

### 2026-09-30 - The index card can include unmatched albums

Side task, no batch tag: the index card's "Include unmatched albums" switch and the sort lock, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: a quick toggle on the index card for the Last.fm albums Spotify and Deezer could not match, which blocks switching between play time and play count.

What changed: a native checkbox Switch between "Rank by" and "Show"; while it is on, Play time is disabled (dimmed, visible) and Play count is selected. The form field `include_unmatched=1` is stored as a job param (default False); an include run posted with `sort_by=playtime` is stored as play count, the same rule without scripts. The loading page lists "unmatched albums included". The off track is outlined in the muted text colour and the knob has a dark edge (`rgba(20, 16, 24, 0.75)`), because the kit's border-toned track measured 1.3:1 against the card. A frontend-gate check drives the switch by keyboard, reads its name and description, checks the track border under forced colours, and holds the track border and knob boundary at 3:1 in both themes, on and off (measured: track border 5.39:1 to 7.54:1 against the card; knob boundary, the stronger of edge and knob against the track, 4.98:1 at the lowest, dark on).

Deviations: the brief edited `docs/design/README.md` and two component prompts; the design-snapshot test forbids that, so the overrides are `docs/design/RECONCILIATION.md` Section 20 (after the cover-washes Section 19) and a ledger row, and DESIGN.md. Help text keeps the card's `.field__help` colour (5.5:1), pending the owner's design-system ruling. F-B23-39 gains one evidence sentence (three overlapping gate runs on this machine hit `ERR_NO_BUFFER_SPACE`).

Edited existing tests: none (four new tests in tests/test_routes.py).

Validation: `pytest -q` -- **2532 passed**.

### 2026-10-01 - The ring check waits out animations before reading pixels

Side task, no batch tag: the heatmap focus-ring check waits for running animations to finish before it reads the cell's geometry and takes its screenshot, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: the previous step's reproduction showed 8 of 20 last-cell screenshots landing while `#heatmap-result` was still crossfading in (opacity changed between the read before and the read after the shot), and a reading taken mid-animation is invalid by construction. PR #252 applied the same reasoning to every other check that slept through a transition; the ring check still waited only for fonts and two frames.

Change: `_ring_shot` in `scripts/dev/_frontend_gate_heatmap_access.py` calls `wait_for_settled` (`scripts/dev/_frontend_gate_shared.py`, bounded, raises when the page never settles) at the start of each attempt, after the tooltip nudge and before `_LAYOUT_SETTLED_JS` and the geometry read. This removes a confounder; it is not claimed as the fix for F-B23-39, whose status stays open.

Evidence: a new test records the order of the wait and the geometry reads over a two-attempt run; with the call removed it fails (`assert 0 == 2` on the wait count). The existing ring-page helper answers the settle script with an empty result so the real `wait_for_settled` can run against it. The 20-run reproduction (the check alone, fresh desktop context each, `reduced_motion="no-preference"`) passed 20 of 20, with `container.opacity` 1 and nothing changed during the shot on all 80 shots read (4 per run). A ring forced to `visibility=hidden` still fails with `ring.visibility=hidden` in the evidence.

Validation: `pytest -q` -- **2528 passed**.
