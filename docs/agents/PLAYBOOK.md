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

### 2026-10-20 - The tooling diagram draws the include check's imports

Side task, no batch tag: the tooling diagram draws the include check's imports and the hover note is made true, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the records must say what the code and the probes showed.

What changed: in `docs/architecture/documentation-tooling.md` the node `FGINC[_frontend_gate_include]` had no import edges and was missing from the `tool` class list; it now has `FGINC --> FGC` and `FGINC --> FGS` and is in the list. SESSION_CONTEXT Section 4 already lists both imports for the module. The entry "Hover selectors use one :not() list" said the hover check "exercises both selectors"; its probe showed otherwise, so that sentence now says the check guards the hovered ink's contrast, not that the hover rule applies. The Mermaid validator was not run; the controller validates the diagram.

Deviations: none. Documentation only; no test edited.

Validation: `pytest -q` -- **2564 passed**.

### 2026-10-20 - Retry keeps the listener's Albums choice

Side task, no batch tag: Retry on the loading page keeps the Albums choice, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: a retried search must repeat the listener's search exactly (owner ruling 2026-09-30: fix a found defect now rather than later).

What changed: an "All albums" run that failed retryably offered Retry, and `retryCurrentSearch()` in `static/js/loading.js` rebuilt the POST from `window.SCROBBLE`, which `templates/loading.html` fills from a hand-written `scrobble-config` block. Neither carried `include_unmatched`, so Retry silently re-ran the search as "Matched only". The block now has `"include_unmatched": include_unmatched|default(false)` (the route already passed it; the default keeps templates rendered without it working) and the script posts `include_unmatched=1` when it is true, nothing otherwise, as the index form does. New `tests/test_loading_retry_contract.py` derives the fields `results_loading` reads from `request.form` (an `ast` walk) and asserts each is a key of the config block and is posted by `retryCurrentSearch()`; it failed on the old tree naming `include_unmatched`, and deleting another field's `createHiddenInput` line makes it fail naming that field.

Deviations: none. No existing test edited.

Validation: `pytest -q` -- **2564 passed**.

### 2026-10-20 - The hover checks wait for transitions, not a timer

Side task, no batch tag: the segmented-control colour checks wait for the browser to finish their transitions instead of sleeping, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: no fixed-timer guesses in the frontend gate (PR #252 removed the others).

What changed: `seg_contrast_failures` and `seg_hover_failures` in `scripts/dev/_frontend_gate_colour.py` each did `page.wait_for_timeout(350)` before reading a colour that takes a 0.2s transition. Both now call `wait_for_settled` from `scripts/dev/_frontend_gate_shared.py`: the theme switch waits on the control's track, the hover waits on the hovered option. That adds an import of `_frontend_gate_shared` into `_frontend_gate_colour`, so the diagram in `docs/architecture/documentation-tooling.md` gains `FGC --> FGS` and its node label no longer says "pure maths, no page"; SESSION_CONTEXT Section 4's dependency graph gains the same edge and its file note; the module docstring and the DEVELOPMENT.md sentence that called the module pure colour maths now say it also holds the segmented-control checks. The Mermaid validator was not run; the controller validates the diagram.

Deviations: none. No test edited. Probe: a hover rule planted at `#999` fails the gate ("hovered unselected option text on track is 2.66:1, under 7.0:1"); breaking the selector alone (`.seg__optionX`) does not, because the unhovered ink already clears 7:1, so the check guards the hover ink, not the selector.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - Hover selectors use one :not() list

Side task, no batch tag: the two chained `:not()` hover selectors in `static/css/shell.css` become one `:not()` list each, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: clear the Codacy findings on PR #256 at the cause.

What changed: Codacy (Stylelint `selector-not-notation`, "Expected complex :not() pseudo-class notation", 2 minor) flagged `.seg__radio:not(:disabled):not(:checked) + .seg__option:hover` and `.metric-toggle-btn:not(:disabled):not([aria-pressed="true"]):hover`, the only chained `:not()` selectors in the app's own stylesheets. They are now `.seg__radio:not(:disabled, :checked) + .seg__option:hover` and `.metric-toggle-btn:not(:disabled, [aria-pressed="true"]):hover`. In Selectors Level 4 `:not(A, B)` matches exactly what `:not(A):not(B)` matches, so behaviour is unchanged (Chromium 88+, Firefox 84+, Safari 9+). The frontend gate's segmented-control hover check (`seg_hover_failures` in `scripts/dev/_frontend_gate_colour.py`) guards the hovered ink's contrast, not that the hover rule applies: with the selector broken the gate still passed, because the unhovered ink already clears 7:1, while a planted low-contrast hover colour fails it ("hovered unselected option text on track is 2.66:1, under 7.0:1"). No test, gate module or document quoted the old text.

Deviations: none. No test edited.

Validation: `pytest -q` -- **2561 passed**.
