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
  in a live session, the accepted changes land as they are made, and a plan
  written afterwards covers their documentation, gates and the album-search
  fix the session found. The documentation refresh merges last.
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

### 2026-10-25 - UI round 2 backlog: the loading page's stats, Back and entrance

Side task, no batch tag: relabelled the loading page's last two stats, took the finished page out of history and gave the stats an entrance, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: "Albums passing" and "Spotify matched" are unclear and showed the same number (backlog L2); one should be "Cache hits" and the other must not duplicate it (2026-10-25); Back from the results should not land on the loading page; the stats should not just appear. The old pair duplicated because "matched" counted every album given metadata from the cache, Spotify or Deezer, and Spotify search accepted its first result, so nearly all of them matched (that search defect is for the plan). `scrobblescope/orchestrator/__init__.py` records `albums_to_search` (the cache misses) beside `cache_hits` at the cache split; together they make up the albums that passed the thresholds. `templates/loading.html` and `static/js/loading.js` show "Cache hits" and "Albums to search" (first "Albums searched"; renamed because the figure is known before the search ends) and drop the separate "albums loaded from cache" line. `redirectToResults` uses `location.replace`, so Back from the results reaches the form instead of a finished loading page that sent the listener forward again. `static/css/loading.css`: each stat rises 0.375rem and fades in over 360ms as its first figure arrives, 50ms apart when they arrive together; reduced motion shows them at once. The backend still records `albums_passing_filter` and `spotify_matched` for other readers. Deviations: landed before its plan. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: the expanded form keeps clear of the header

Side task, no batch tag: stopped the fully expanded index form pressing its mode switch against the header, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: "the card itself is in the middle ... the mode tabs however, aren't accounted for" (backlog I4, 2026-10-25, from a 1920x1063 screenshot with every option open). `positionForm` in `static/js/index.js` always lifted the centred composition 2.5rem, so with everything open it hit its 0.25rem floor: 4px above the switch, 47px below the card. The lift now gives way first, never taking the gap above the switch below 1.5rem: measured 24px above and 27px below at 1920x1063 expanded, 24px and 63px at 1440x900; collapsed forms are unchanged (115px and 195px at 1920x1063). A window too short for the expanded form still scrolls with the 0.25rem floor; whether to raise it is open for the owner. The function's comment avoids the word daisyUI uses for its tab component, because Tailwind scans `static/js` for class names and that word generated daisyUI's tab styles into the compiled stylesheet. Deviations: landed before its plan; DESIGN.md's Fixed Composition Rule still describes the fixed lift, for the plan's docs task. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: one selected-option look

Side task, no batch tag: gave the mode switch and every segmented control one selected-option look, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: drop the segments' strong outline and keep the controls consistent, "so long as it is WCAG 2.x compliant" (2026-10-24/25, decided in the live session after trying a solid fill, which read as busy). The controller measured the mode switch's old look as failing WCAG 1.4.11: its soft tint is 1.11:1 light and 1.28:1 dark against the track, and its violet label only a hue shift from the grey one. `static/css/shell.css`: a new `--shell-selected-outline` token per theme (`#7d61b7` light, 4.60:1 against the track; `#8373a3` dark, 4.58:1), the primary mixed toward the page ground until it clears 4.5:1 as the owner asked; the checked `.seg__option` and the pressed `.metric-toggle-btn` take the soft tint, that 1px outline and primary text (5.47:1 light, 6.38:1 dark on the tint). `static/css/index.css`: `.mode-pill.active` takes the same three, with a `Highlight` border under forced colours. This covers the index's Rank by and Unmatched albums controls and the Results page's Unmatched albums control and Sort leaderboard buttons. Deviations: landed before its plan (see the entry below); `docs/design/RECONCILIATION.md` section 20 and DESIGN.md's Segmented Controls still give the old outline's figures, for the plan's docs task. Edited existing tests: none. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: the index hero

Side task, no batch tag: landed the index hero changes the owner accepted in the round 2 backlog's live session, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: the `§ 01/02/03` lists "feel generic and AI-directed" and should earn their place (backlog I3, H3); the album lede was "lacking" (I2); the heatmap headline "one grid." was "bland" (H1), and the owner later ruled out a comma followed by a one-word punch and "this past year" (the heatmap counts back 365 days from today). `templates/index.html`: both mark lists become a three-column strip, each item a serif term with a line icon (calendar, clock, document; grid, sliders, document) over one plain description; the album lede and both headlines take the accepted copy. `static/css/index.css`: the strip's rules replace the numbered-list rules, the strip sits 0.5rem under the lede, the ledes widen to 48ch with `text-wrap: pretty`, and where the hero column is narrow (windows up to about 1180px) each strip item becomes a row because terms wrapped there. That is a container query on the strip's wrapper in `em` of the term size, not a second viewport breakpoint: docsync's "single 860px breakpoint" declaration (DOC009) holds. The strip stays hidden below 860px (owner ruling). `static/js/heatmap.js`: one comment no longer calls the lists "§". Deviations: the changes landed before their plan, at the owner's request, so the session's state is safe; the plan follows. Edited existing tests: `tests/test_routes.py` `INDEX_HEADLINE` marks the index by `id="index-grid"` instead of headline copy the owner still revises. Validation: `pytest -q` -- **2994 passed**.
