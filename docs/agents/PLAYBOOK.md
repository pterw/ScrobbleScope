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

### 2026-10-20 - Hover selectors use one :not() list

Side task, no batch tag: the two chained `:not()` hover selectors in `static/css/shell.css` become one `:not()` list each, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: clear the Codacy findings on PR #256 at the cause.

What changed: Codacy (Stylelint `selector-not-notation`, "Expected complex :not() pseudo-class notation", 2 minor) flagged `.seg__radio:not(:disabled):not(:checked) + .seg__option:hover` and `.metric-toggle-btn:not(:disabled):not([aria-pressed="true"]):hover`, the only chained `:not()` selectors in the app's own stylesheets. They are now `.seg__radio:not(:disabled, :checked) + .seg__option:hover` and `.metric-toggle-btn:not(:disabled, [aria-pressed="true"]):hover`. In Selectors Level 4 `:not(A, B)` matches exactly what `:not(A):not(B)` matches, so behaviour is unchanged (Chromium 88+, Firefox 84+, Safari 9+). The frontend gate's segmented-control hover check (`seg_hover_failures` in `scripts/dev/_frontend_gate_colour.py`) exercises both selectors. No test, gate module or document quoted the old text.

Deviations: none. No test edited.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - The Albums help no longer sits on a line break

Side task, no batch tag: the index card's Albums help is reworded so it sits clear of a line break, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: PR #256 must pass CI at the root cause, not by loosening the gate.

What changed: CI run 39482227535 (Linux Chromium) failed the large display scale parity check on the index page: "form composition height is 961.6px at 1440p, expected proportional 984.1px" and "form height is 873.3px at 1440p, expected proportional 895.8px". The old help, "All albums keeps the ones Spotify and Deezer can't find, ranked by play count only.", overflowed one line by about 6%: measured locally it wraps to 2 lines at 1080p (last-line slack 407.3px of 432.3px) and 2 lines at 1440p (496px of 526.4px). Font size and column both scale with `--index-scale`, but rasterization differs by pixel size and platform, so in CI the sentence fit one line at 1440p and stayed at two at 1080p; the 1440p form was one help line (21.97px) shorter, and the check correctly reported it. The help now reads "Adds the albums Spotify and Deezer can't find, ranked by play count.": one line with 69.7px slack of 432.3px at 1080p and 85.4px of 526.4px at 1440p (about 16% both). `templates/index.html`, the pinned sentence in `scripts/dev/_frontend_gate_forms.py` and the quoted copy in `docs/design/RECONCILIATION.md` follow. The hazard class is filed as F-B23-44 (a gate check for wrap-boundary slack).

Deviations: the frontend gate and results-behavior script were not run here (another browser gate may be running; the controller runs them and CI verifies).

Edited existing check: the `UNMATCHED_HELP` constant read by the Albums help check in `scripts/dev/_frontend_gate_forms.py`.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - The redundant tr[hidden] rule is filed

Side task, no batch tag: the `tr[hidden]` rule in `static/css/results.css` is filed as F-B23-43, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: keep the findings list true to what the earlier entry promised.

What changed: the 2026-09-30 entry "MusicBrainz dates the unmatched rows on Results" said the rule "is filed as a finding by the controller", and it was not. F-B23-43 now names both rules (the one in `results.css` and the `[hidden]` rule with `!important` in the compiled `tailwind.css`) and says deleting the first needs a gate or behaviour assertion first.

Deviations: none. No code change, no test edited.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - The production database sleeps after an idle hour again

Side task, no batch tag: the production database (`scrobblescope-db`) is set to stop after an idle hour again, and PLAYBOOK Section 3 names the work before WP-1, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: keep the Fly bill inside the $5 a month Fly waives for a personal organisation.

What changed: on 2026-10-01 `FLY_SCALE_TO_ZERO` was removed from the `scrobblescope-db` machine so the database stayed on. On 2026-10-20 the owner's Fly cost explorer showed $4.90 for 1-20 October ($0.24 a day), which projects past the waiver, so the controller restored `FLY_SCALE_TO_ZERO=1h` with `fly machine update` (machine healthy 3/3, app answered 200). The app holds no connection pool -- `cache.py` opens and closes a connection per use -- so the database can reach zero connections and stop. The release-command retry in `init_db.py` (PR #255) covers a deploy that finds it asleep, and the cache is optional at runtime, so a cold database costs the first job its cache, not its result. No repository file states the always-on setting, so none changes. Section 3 gains a bullet naming the side-task tranche before WP-1 and why job persistence waits: a database-backed job store would keep the database awake, which the hosting cost ceiling does not allow.

Deviations: none. No code change, no test edited.

Validation: `pytest -q` -- **2561 passed**.
