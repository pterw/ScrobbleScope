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

### 2026-10-27 - Move the home page keys to the left column

Side task, no batch tag: UI audit v6 row 10, moving the home page keys to the left column, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 10): the right column holds controls only. The heatmap preview card inside the form stack and the album "Only plays inside this calendar year are counted." hint explained the mode in the form. `templates/index.html` now has an `.index-hero__keys` wrapper under the strip with two keys, `data-mode-key="album"` (rows Year, Plays, Tracks; "How an album makes the list") and `data-mode-key="heatmap"` (the old card markup, `.hm-preview*` names kept as hooks). `static/js/heatmap.js` `switchModeHero` crossfades the keys with the strip through one mechanism (the inactive key gets `aria-hidden="true"` and `visibility:hidden`). `static/js/index.js` `updateKeyCounts` makes the album key's two numbers follow the steppers (singular at 1) and runs in the initial-state sync too, so restored form values show. `static/css/index.css` holds the `.index-key*` rules in `--index-scale` units; `static/css/heatmap.css` lost the card, key and facts rules. `_heatmap_form.html` lost the card. The mode switch moves the tabs 0px (row 2's floor). Contrast (computed, both themes): min 5.17:1 (labels), max 10.61:1; no new colour token. No Chromium-only CSS.

Deviations: (U21) supersedes brief item 6: below 860px both keys are hidden like the strip, and the year hint stays in the form as `field__help--phone` (shown below 860px, hidden from 860px up). (U22) the album key also ends with the 1px `--ss-border-divider` rule at the strip's width, like the heatmap key; the rule sits on each key, which stretch to the taller one, so it lands at the same y in both modes. The keys use a new attribute `data-mode-key`, not `data-mode-marks`, so the gate's `[data-mode-marks="{mode}"].is-active` locator keeps selecting only the strip.

Existing tests edited, by name: `tests/frontend/test_heatmap_pure_functions.py::_preview_text` (helper; reads the heatmap key from `templates/index.html`) and the `MODE_SWITCH` constant in `tests/scripts/dev/test_frontend_gate_layout.py` (new fields). Added: `test_the_form_stack_holds_no_key_and_each_mode_shows_its_own` (parametrized) and `test_a_phone_hides_the_keys_and_keeps_the_year_hint`, over new checks in `scripts/dev/_frontend_gate_layout.py` (`_home_key_failures`, `_phone_home_failures`, `_restored_key_text`).

Validation: `pytest -q` -- **3007 passed**.

### 2026-10-27 - Keep the home form centred without the jump

Side task, no batch tag: UI audit v6 row 2, keeping the home form centred without the jump, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 2): the form stack re-centred instantly on every height change, so the tabs jumped when the mode, the release scope or the thresholds changed. `static/css/index.css` gives `.index-form__inner` `min-height: var(--index-card-min, auto)`. `static/js/index.js` `syncFormMinHeight` measures the inner's height in the default album state (scope same/previous/all, thresholds closed) on load, after `document.fonts.ready`, after a resize that changes the resolved `max-width` and across the 860px breakpoint, and sets the floor only on desktop, so the Heatmap tab sits where the Album tab did. `playFlip` glides the remaining shift over 220ms (`translateY` to none, `cubic-bezier(.16, 1, .3, 1)`), skipped under reduced motion; it is triggered by the scope `change`, and by one capture-phase click listener for `.mode-pill` and `.disclosure__summary`. A page loaded in Heatmap mode re-measures the floor on its first switch to the album state. `scripts/dev/_frontend_gate_layout.py` gains `_measure_mode_switch_shift`, `_measure_heatmap_first_shift` and `_mode_switch_failures`, called from `check_large_display_scale_parity` at 1920x1063 (1px tolerance). No template or `heatmap.js` change; Firefox and Chromium both measured 0px; no new colour pairing.

Deviations: (R2-F1) the `min-height` rule sits inside the existing `min-width: 860px` block, so phones never pad the heatmap form to the album height. (R2-F3) the FLIP triggers are the scope `change` plus the capture-phase click listener (instead of editing `heatmap.js`), and the floor is re-measured in `playFlip`'s frame callback so the tab, scope and disclosure paths all work after a Heatmap-first load.

Existing tests edited, by name, in `tests/scripts/dev/test_frontend_gate_layout.py`: the helper `_run_large_display_check` (stubs the two new measurements). Added: `test_mode_switch_must_stay_put_when_the_mode_changes` and the parametrized `test_large_display_check_reports_a_mode_switch_that_moves` (album-first, heatmap-first).

Validation: `pytest -q` -- **2992 passed**.

### 2026-10-27 - Drop the sort-change toast

Side task, no batch tag: UI audit v6 row 9, dropping the sort-change toast, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 9): switching the leaderboard between play count and play time no longer raises a toast. The hidden-album count already shows in `#playtime-hidden-note`, so the toast repeated the page. `setLeaderboardMetric` in `static/js/results.js` loses its `showToast` block, the `hiddenCount` string built only for it, the now-unused `showNotification` parameter and an unused `dropped` binding; its three callers (the plays and playtime buttons, `setUnmatchedHidden`) are updated. `showToast` stays for the CSV, image export and error callers. No CSS and no new colour pairing.

Deviations: none.

Existing tests edited, by name, in `scripts/dev/results_behavior_tests.py`: `test_hidden_note_and_toast_carry_the_count_of_dropped_albums` (renamed `test_sort_switch_shows_the_count_in_the_note_and_no_toast`, extended to assert no toast, the subtitle and the column header), `test_hidden_note_stays_hidden_when_every_album_has_a_listening_time` (asserts no toast) and `test_hidden_note_counts_only_rows_the_ranking_alone_drops` (tuple unpack only).

Validation: `pytest -q` -- **2986 passed**.

### 2026-10-27 - Add a pause-animations footer control

Side task, no batch tag: UI audit v6 row 3, a pause-animations footer control, on `feat/ui-audit-v6`, a branch off `main`.

Owner intent (design README row 3): the header mark's bar animation can be paused (WCAG 2.2.2). A `.motion-toggle` button is the first child of `.page-footer-extras` in `templates/base.html` and reads "Pause animations" / "Play animations" with `aria-pressed`. `static/js/theme.js` toggles `data-motion="still"` on `<html>`, syncs the label from that attribute on load and persists the choice in localStorage `ss-motion` (write and remove in a try). The pre-paint script in `base.html` reads `ss-motion` in its own try so a paused page never flashes the animation. `static/css/shell.css` sets `animation: none` on the header mark's bars under `[data-motion="still"]`; the loading-page pinwheel is untouched. Under `prefers-reduced-motion` the bars are already still and the button keeps showing the stored state. The `.page-footer-extras:empty` rule is removed because the wrapper now always holds the button. The focus ring is 2px solid `--shell-accent` with offset 2px, as the header toggle. Contrast: rest text 5.17:1 light and 5.82:1 dark, focus ring 6.06:1 light and 8.14:1 dark (min 5.17, max 8.14); nothing is Chromium-only.

Deviations: (R3-F1) the README hover colour `--rocket-5` (#f0903a) is 2.24:1 on the light footer (#faf7f0), under the 4.5:1 contrast floor, so the contrast floor governs: light hover uses `--shell-accent` (#6a4baf, 6.06:1) and dark keeps `--rocket-5` (8.11:1). The header comment of `static/js/theme.js` also names the new toggle (R3-F2).

Existing tests edited, by name: `test_every_page_wraps_its_footer_extras` (the button opens the wrapper) and `test_every_page_sets_the_theme_before_first_paint` (runs the inline script in node with fake storage; skips when node is missing) in `tests/test_template_shell.py`.

Validation: `pytest -q` -- **2986 passed**.
