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
  remain untagged by the owner's 2026-09-23 ruling in the definition. It runs
  after the tranche, before WP-1 (owner ruling 2026-10-22).
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. The include-unmatched
  control (PR #1) and backend hygiene (PR #2) are done. The album request module
  is done (PR #3, branch refactor/album-request-module, plan
  `docs/superpowers/plans/2026-10-20-album-request-module.md`); normalized
  Last.fm scrobbles with one album aggregate is done (PR #4, branch
  refactor/lastfm-scrobbles, plan
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); one album-metadata
  encoding is done (PR #5, branch refactor/metadata-encoding, plan
  `docs/superpowers/plans/2026-10-20-metadata-encoding.md`); the statistics
  module is done (PR #6, branch refactor/statistics-module, plan
  `docs/superpowers/plans/2026-10-20-statistics-module.md`). Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #7, UI consistency, finished round 1 (plan
  `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`); further rounds
  wait for the owner's screenshots, each with its own plan. A side-task PR of
  cheap fixes from the 2026-10-21 architecture review and the logging audit
  is done (branch `fix/pre-batch23-side-tasks`, plan
  `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md`), and so is a
  CI change that keeps Playwright's Ubuntu packages in the Actions cache
  (branch `ci/playwright-apt-cache`, plan
  `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md`). UI
  consistency round 2 is done (PR #268, branch `feat/ui-consistency-round-2`,
  plan `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md`). Its
  backlog runs now on `feat/ui-round-2-backlog`: the owner settles each item
  in a live session and the accepted changes landed as they were made (PR
  #269). All fourteen tasks of the plan
  `docs/superpowers/plans/2026-10-25-ui-round-2-backlog.md` have landed on
  the same branch (the documentation, the gates that hold the accepted
  changes, the F-B23-46 ranking rule and the stale-copy sweep), followed by a
  test consolidation under the owner's lean-suite ruling. PR #269 merged
  into `main` (merge commit `997f7584`) and is deployed. The album-matching,
  cache re-verification and MusicBrainz fixes are on `fix/album-matching`
  (PR #270, plan `docs/superpowers/plans/2026-10-25-album-matching.md`),
  based on `main`: every plan task has landed there and the six findings it
  files are closed. PR #270 merged into `main` (merge commit `4a2d2406`) and is deployed. The documentation refresh merges last.
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

### 2026-10-27 - Record new frontend-gate flake sightings

Side task, no batch tag: adding the gate failures seen during the UI audit v6 PR to F-B23-58, on `feat/ui-audit-v6`, a branch off `main`.

This is new evidence for an existing finding, not a new finding. F-B23-58 asked for new sightings with their timing before any fix. Three kinds were appended from the plan's gate logs: three `net::ERR_NO_BUFFER_SPACE` sightings (a grep of every gate log finds exactly three), `shell text scaling [mobile]` (`shell.css`) and two code-phase `large display scale parity [desktop]` runs (`index.css` in `task-sg8-code-3`, `static/js/theme.js` in `task-row5-code-1`), each failing after an asset failed to load (all passed on the next run); one `cached heatmap restoration painted the loading panel before its result` (passed on the next run); and a non-failing `Job context not found` log line noted as noise. The finding's status box and fix shape are unchanged.

Deviations: the brief called the second `ERR_NO_BUFFER_SPACE` sighting "index.css, 72 large-display checks"; the log shows 72 `large display scale parity [desktop]` failures, each carrying the `index.css` error, so the entry says that. No code changed.

Existing tests edited, by name: none.

Validation: `pytest -q` -- **3023 passed**.

### 2026-10-27 - Parse the canvas font string without a regex

Side task, no batch tag: replacing the `_FONT_SHORTHAND` regular expression in the frontend gate's theme check with plain token parsing, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (U34: "I agree with (b), because a quick fix now is worth it over forgetting it"). Codacy flagged `_FONT_SHORTHAND` (`scripts/dev/_frontend_gate_theme.py`) as an inefficient regular expression. It measured linear, so the flag was a false positive, but plain parsing clears the check for good. `_split_canvas_font` now walks the whitespace tokens up to the first size token (`<n>px`, with an optional `/line-height`), keeping the last weight token (`bold` is 700, `normal` is 400); `_is_size_token` is the new helper and the `re` import is gone. Behaviour is identical on 22 compared inputs and a 400k-string fuzz; the one difference is that size digits are ASCII-only (the old `\d` also took Unicode digits, which `ctx.font` never emits). The parametrized weight cases (`bold`, `normal`, `italic 600` with a line-height, `bold 600`, a string with no size token) close the gap row 1 recorded under R1-F5.

Deviations: none.

Existing tests edited, by name: `tests/scripts/dev/test_frontend_gate_theme.py::test_a_saved_headline_drawn_at_another_weight_is_reported` (extended with a drawn-weight parameter and five cases)

Validation: `pytest -q` -- **3023 passed**.

### 2026-10-27 - Lift the home pause button to the footer's gap

Side task, no batch tag: lifting the home page's "Pause animations" button to the footer button's gap, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (U30: "maybe raise it up by a touch in the index card -- to match the distance from the bottom of the page as is in the results page"). At 860px and wider the home button sat flush with the window bottom (0px); the footer button on the other pages sits 24px above the page foot (`.page-footer-extras` padding-bottom, 1.5rem). `static/css/index.css` now gives `.index-grid .index-hero` a 1.5rem bottom padding, so the button's bottom edge is 24.00px above the viewport foot in both modes at the six desktop sizes, in Firefox and Chromium, centring unchanged. The extra 24px made 1280x720 scroll by 12-13px, so a `@media (max-height: 760px)` rule takes 1rem back from the hero's top padding; windows taller than 760px are unchanged. The layout gate reads the shown button's gap and the footer row's computed padding-bottom and fails when they differ by more than 1px (`_home_pause_failures` in `scripts/dev/_frontend_gate_layout.py`).

Deviations: the gate compares the gap with the footer row's computed padding-bottom, not a seeded results page (a seeded results page agrees to within 1px, measured); 1.5rem is written in both `shell.css` and `index.css` (no shared token, `shell.css` was outside the task), and the gate's equality check fails if either changes alone; the `max-height: 760px` top-padding give-back goes beyond "raise the button". Real laptop windows near 650px tall already scrolled before this change and still do.

Existing tests edited, by name: `tests/scripts/dev/test_frontend_gate_layout.py::test_the_home_page_must_not_scroll_vertically_in_either_mode` (two parametrized cases: gap 0 fails, 24.9 passes) and its `PAUSE_OK` fixture.

Validation: `pytest -q` -- **3018 passed**.

### 2026-10-27 - Make "Pause animations" stop every animation

Side task, no batch tag: making "Pause animations" stop every auto-moving thing, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (U29: "clicking pause animation doesn't stop the top artist carousel"; U31: the loading page's pinwheel should stop too; U33: the unmatched page's button does not pause the header). Row 3's control set `data-motion="still"` but only the header bars honoured it. Now the results spotlight's interval callback in `static/js/results-spotlight.js` returns early while `<html data-motion>` is `still`, so a page loaded paused never advances and Play resumes at the next period from the card shown. In `static/css/shell.css` the still rule also covers `.ss-pinwheel svg > g` and `> g > g`, so the pinwheel rests (drawn artwork, no transform, as reduced motion does) and the phase line still shows progress as text. U31 supersedes row 3's pinwheel exemption. No live doc called the pinwheel exempt, so no doc prose changed.

Reproduction: the header bars were already stopping on the results page at the base commit (Firefox and Chromium: `animation-name` none after the click and after a reload with the stored choice), so the first bar report did not reproduce and the bar rule is unchanged. U33 (unmatched page) was reproduced with a real click on a seeded page at 390, 900, 1280 and 1920px in both browsers and also works (bars `ss-bar-pulse` x5 before, `none` x5 after; the controller repeated it on the owner's server), so no code fix; the likeliest cause is a carried-over paused state or a cached stylesheet. A click check was added anyway. The bar rule and the pulse rule have equal specificity and the pause wins by source order only; the new checks guard that.

Deviations: none from the owner rulings. Checks: `_paused_motion_failures` and `_unmatched_pause_failures` in `scripts/dev/_frontend_gate_pipeline.py` (bars and pinwheel rest while paused; the unmatched button click rests the bars), `_pause_hold_failures` in `scripts/dev/_frontend_gate_spotlight_photo.py` (stored pause before load: artist unchanged over 3 periods and bars rest, then Play resumes), and `test_pause_animations_holds_the_rotation_and_play_resumes_it` in `scripts/dev/results_behavior_tests.py`.

Existing tests edited, by name: `tests/scripts/dev/test_frontend_gate_spotlight_photo.py::test_the_hold_check_focuses_then_hovers_and_counts_the_periods` (the check gained a paused phase) and `test_a_timed_out_hold_wait_is_judged_by_the_tick_count` (now three tick failures plus a "did not resume").

Validation: `pytest -q` -- **3016 passed**.
