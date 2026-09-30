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
  (see Section 4). Next action: the WP-0 close-out below. The
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
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam, typed provider failures and job persistence
  (before WP-3), an album request module (before WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (before WP-2), one album-metadata
  encoding (before WP-3), a statistics module (before WP-6), and provider
  failure logs that carry no listener data. WP-1 does not start until they
  are scheduled.

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

### 2026-09-30 - Second architecture review tracked and scheduled

Side task, no batch tag: the second deepening review of the codebase is tracked at `docs/history/reports/architecture-review-20260930-0040.html`, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The review walked the routes, the orchestrator's phase modules, the provider contract, the cache, the worker and the results, spotlight and loading scripts, and checked every candidate in the five earlier architecture reports against the code: four done, three partial, five open, five already planned. Two findings are live defects, confirmed by reading the code: three providers log the album and artist they searched for at ERROR level, against the logging module's own rule; and the album route's single `try` treats an outage in the user or privacy check as a failed registration-year hint and starts the job anyway. Four album filters (`sort_mode`, `release_scope`, `decade`, `limit_results`) are never validated.

Section 3 now says that these seams come before the Spotify import and which work package each one gates. The owner added the report to `docs/history/reports/`; no code changed.

Validation: `pytest -q` -- **2223 passed**.

### 2026-09-29 - User checked before privacy; only a public verdict cached; payload edge cases

Side task, no batch tag: checking the user before privacy, caching only a public verdict and handling Deezer and Last.fm payload edge cases, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

`results_loading` now asks `check_user_exists` first, so a missing user gets "User 'x' was not found on Last.fm." (a 200 re-render of `index.html`, accepted: it matches this route's other form errors) and the privacy check never runs for it. `check_profile_is_public` never caches a private verdict (error 17 in a 200 counts as private), caches only a body with a `recenttracks` dict, and treats a cache hit as public; `check_user_exists` maps error 6 in a 200 to not found and caches only a body with a `user` dict. A new `private_profile` code in `ERROR_CODES` (lastfm, not retryable) is raised by `fetch_once` on a 403 or error 17 without retry, classified through `errors.PRIVATE_PROFILE_MARKER`; the album results page answers it with a 403 and a "make listening public" detail. Browser check: `heatmap.js` and `loading.js` read the server's `retryable` flag and message, keep no code-to-message map, so nothing changed there. `fetch_deezer_album` skips a null or non-text track title; the Deezer fallback tasks run under try/finally `_cancel_and_drain` (no TaskGroup). `_normalise_track_list` turns a lone `track` object into a list before `_is_well_formed_page`, which now refuses any other non-list `track`. A cancelled request logs at DEBUG and is not recorded. New edges `lastfm -> errors` and `_deezer_fallback -> lastfm` are in the SESSION_CONTEXT graph. Closes F-B23-23, F-B23-24 and F-B23-30. Tests added in five existing modules, none edited; mutation-checked. Last.fm errors 10 and 26 remain unverified.

Validation: `pytest -q` -- **2223 passed**.

### 2026-09-29 - Spotlight artist name reads whole at every width; card height fixed

Side task, no batch tag: giving the spotlight artist name a whole line and holding the card height, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

From 1024px to about 1230px the name got a 46-110px column beside the fixed photo and broke inside words (S2-1), and the card changed height between candidates so the sticky rail jumped every 7s (S2-10). `.spotlight-card-content` now wraps and `.spotlight-details` has a flex basis, so the details drop under the photo whenever the card cannot give the name that column; the line-count `min-height` is deleted. `results-spotlight.js` `reserveCardHeight` renders each candidate once, measures the card and holds the tallest as `min-height`; `watchCardLayout` re-runs it when the card width changes and when fonts load. Photo rules and the 4px/8px radius step are unchanged. A new frontend-gate check, `artist spotlight name whole and card height fixed`, runs at 320, 390, 1024, 1180 and 1920px plus a 1024 to 1920 resize and fails on a mid-word break or a card height that varies across candidates. Live probe: with the old CSS the check fails in both browsers (`the name of 'Radiohead' breaks inside the word 'Radiohead'` at 1024px); with the old JS it fails (`the card height changes between candidates`); with `watchCardLayout` removed it fails after the resize. Tests: 7 new in `test_frontend_gate_spotlight_photo.py`, no existing test edited. A name needing more than two lines at the narrowest widths is still clamped (`line-clamp-2`, full name in `title`).

Validation: `pytest -q` -- **2207 passed**.

### 2026-09-29 - Heatmap strip scrolls under a swipe; one owner for the tooltip

Side task, no batch tag: letting a swipe scroll the heatmap strip and giving its tooltip one owner, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The per-cell `touchstart` in `static/js/heatmap.js` is now passive and only records the start point; the single document `touchend` listener decides a tap (moved at most 10 px, same cell, touchend cancelled to suppress emulated mouse events) and hides the tooltip otherwise, so a swipe is never cancelled. One `tooltipOwner` (hover, focus or tap) now owns the tooltip: focus owns it only under `:focus-visible`, scroll hides a hover or tap owner and repositions a focus owner, resize repositions or hides it, Escape hides it, and a handled key that moves nothing re-runs the ring decision. The tooltip is `position: fixed` in `static/css/heatmap.css` so it cannot widen the page. Two new frontend-gate checks cover it (`heatmap touch swipe scrolls and tap shows tooltip`, `heatmap tooltip has one owner`; 41 checks). No test module added or removed.

Validation: `pytest -q` -- **2195 passed**.
