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

### 2026-09-30 - Coverless albums get a deterministic two-tone wash

Side task, no batch tag: a missing album cover is drawn as a muted two-tone wash instead of a flat bordered box. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Why: owner, 2026-09-30, on the Unmatched page's empty cover boxes: "it should have some sort of gradient pattern". The design system already says covers are "muted two-tone washes" (`docs/design/README.md`, `AlbumRow.prompt.md`); the code never drew them. Owner ruling, same day: Last.fm images are not trusted, so there is no image fallback of any kind.

What: eight pairs of `--ss-wash-N-a`/`-b` tokens in both themes of `static/css/tailwind.src.css` (compiled `tailwind.css` rebuilt), painted by `.cover-wash-N` in `static/css/results.css` (one shared rule set, forced colours drop the gradient and keep the border). `cover_wash_index` in `scrobblescope/domain.py` picks the pair from `zlib.crc32` of the normalised artist and album, so it is the same in every process (`hash()` is salted); the `cover_wash` template filter in `scrobblescope/routes/__init__.py` writes the classes. All four Unmatched placeholders and the Results image fallback use it; a portrait slot drops its wash once the photograph loads. No network call is added. A cover still loading wears its wash too: the cover `<img>` carries the same classes, so the wash shows until the picture paints and behind transparent pixels. The initials stay, in `--color-base-content`: 10.12:1 to 13.41:1 on every light stop and 10.72:1 to 14.04:1 on every dark stop (owner, 2026-09-30: "The 4.5 is a floor not a goal", so 7:1 is the line). RECONCILIATION section 19 records the palette and supersedes the snapshot README's sentence about Last.fm art replacing the washes (the snapshot is guarded and cannot be edited).

A test ties `COVER_WASH_COUNT` to the `.cover-wash-N` rules in `results.css` and to both stops in both theme blocks of `tailwind.src.css`.

Gate: `_cover_wash_page_failures` in `scripts/dev/_frontend_gate_unmatched.py` reads the coverless placeholders in both themes (two different gradient colours) and under forced colours (a painted border), and reads the tokens of all `COVER_WASH_COUNT` pairs in each theme, not the nodes on the page (the initials at 7:1 or better on both stops of every pair, whether or not the pair is on the fixture page, the failure naming the wash, the stop and the ratio; a colour it cannot parse fails loudly). Its fixture's Deezer row now has no cover so a coverless other-provider row is on the page. Live probe: a planted flat background, a planted `border: 0` and a planted pale light-theme stop on wash 0, a pair that is not on the fixture page, each failed the gate; restored, it passed.

Validation: `pytest -q` -- **2513 passed**.

### 2026-09-30 - Frontend-gate checks wait for transitions instead of sleeping

Side task, no batch tag: frontend-gate checks wait for the browser to finish a transition instead of sleeping a fixed time, a fix for the gate flakes seen after PR #245 and PR #251 merged, on its own branch off `main`. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Cause: `index design tokens` added `is-valid`, slept a fixed 250 ms and read `borderColor`, while `static/css/index.css` gives the field a 200 ms border-color transition (PR #251 CI: `rgb(113, 207, 152)`, expected `rgb(111, 207, 151)`). That left 50 ms of slack, so a loaded runner read mid-transition. The heatmap-access checks had the same shape in 16 fixed sleeps.

Fix: `scripts/dev/_frontend_gate_shared.py` gains `wait_for_settled` (two frames, then every running finite CSS transition and animation under the element or document finishes, then two frames; a bounded wait that raises, so the check fails with a message) and `wait_for_scroll_past`. Every sleep that waited for a transition, paint, scroll or focus to settle now calls one of them: 1 in `_frontend_gate_layout.py`, 1 in `_frontend_gate_results.py`, 3 in `_frontend_gate_theme.py` and 16 in `_frontend_gate_heatmap_access.py` (a debounce-bound resize wait passes `after_timer_ms=100`, which outlasts the page's 100 ms resize timer). Fixed waits that remain each carry a comment: the negative waits (nothing more may happen) and the poll intervals of bounded wait-for-state loops. Each converted check still fails on its planted defect, and three tests in `tests/scripts/dev/test_frontend_gate_shared.py` drive the helper in a real Chromium page: a 60 s animation fails at the 300 ms bound with its message, a 150 ms one returns, a missing element is named.

One more flake the load runs exposed: `pipeline state machines` read `window.__scrobbleGateFastRedirect` on a loading page the gate's own timers redirect within about 100 ms of load, so a loaded machine could destroy the evaluate mid-call ("Execution context was destroyed"). The read now follows the redirect; the init script runs on every document, so the flag is set there too. The cause is by elimination (the only evaluate in that check on a page that navigates itself), not reproduced.

Validation: `pytest -q` -- **2496 passed**.

### 2026-09-30 - A flaky spotlight height test made deterministic

Side task, no batch tag: a test-only fix after PR #245 merged, on its own branch off `main`. `scripts/dev/results_behavior_tests.py::test_a_remeasure_under_focus_ignores_a_link_the_candidate_lacks` failed on Linux CI in 3 of about 6 runs (including the push to `main` after the merge) with `'116px' != '134px'`, and never in local whole-file runs.

Root cause: the test page aborts every request, and the test's own markup gives the spotlight `<img>` no size, so the aborted load fails at a moment no test controls; a failed image with alt text is an 18px line, so a height read that lands after the failure measures 134px and one that lands before measures 116px. Reproduced locally in fresh browser processes with the same message (8 of 100 runs, and 6 of 60 in a second count; 0 of 200 and 0 of 60 with the fix); the image's `offsetHeight` was 18 exactly in the reads that gave 134px. Test defect, not product: the production card holds its photo in the fixed-size `.spotlight-image-box`, so a failed photo adds no line.

Fix: the test's `LINK_LAYOUT_MARKUP` takes the photo out of the layout (`#spotlight-artist-img{display:none}`), with a comment saying why; the test is about the link's layout, not the photo. No product code changed, no test added or removed.

Validation: `pytest -q` -- **2493 passed**.

### 2026-09-30 - A rejected Spotify token is refreshed once, not once per call

Side task, no batch tag: single-flight Spotify token replacement, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Source: Codex comment 4146610714 on #245. N concurrent 401s (or concurrent fetches on an expired cache) each expired the cache and requested a token, up to one request per in-flight call. `fetch_spotify_access_token` now takes a lock held per running event loop (jobs run one loop per thread) and re-checks the cache inside it, so one expiry or rejection costs one token request per loop. The limit the Task 30 entry records as accepted (concurrent first 401s refetch) is now fixed; that dated entry is untouched.

Review fixes in the same commit: the per-loop dict is a `WeakKeyDictionary`, but a contended `asyncio.Lock` holds its loop strongly, so weak keys alone kept every contended loop alive (confirmed on Python 3.13); the getter now drops entries of closed loops, under one module-level `threading.Lock` held only for the prune, lookup and insert (never across an await), because every job thread shares that dict and an unguarded prune could raise `RuntimeError` or `KeyError` into a token fetch. A failed token request is shared: calls already waiting when it failed return no token instead of each issuing a request in turn (a per-loop failure count, so another job's failure cannot poison this one); a call that starts later tries again.

Files: `scrobblescope/spotify.py`, `tests/services/test_spotify_service.py`, `docs/architecture/top-albums-sequence.md`. No new module or import outside stdlib `weakref`; the dependency graph is unchanged.

Validation: `pytest -q` -- **2493 passed**.
