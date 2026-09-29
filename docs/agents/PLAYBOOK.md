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

### 2026-09-29 - Last.fm api_key redacted from every log line

Side task, no batch tag: redacting the Last.fm `api_key` in every log line (review finding S1-1), a fix from the third review of PR #245, on the review-fix branch stacked on the WP-0 branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

aiohttp puts the full request URL, query string included, into `str(exc)`, and four sites logged it: `utils.run_async_in_thread` (message and traceback), the registration-year warning in `routes/album_flow.results_loading`, `utils.retry_with_semaphore`'s connect-timeout error line, and `utils.get_cached_response`'s debug line (the cache key embeds the URL). A POST to `/results_loading` with an unknown username wrote the key twice at production log level. `api_logging.RedactingFormatter` now replaces the value after `api_key=` or `api_key:` with `[redacted]` in any rendered line, traceback included, and `app.py` sets it on both log handlers. The trace hook's query exclusion stays the first layer. The check_* functions, the cache key and the route's missing `exists` check are unchanged. Five new tests in `tests/services/test_api_logging.py` and one in `tests/test_app_factory.py`.

Validation: `pytest -q` -- **2173 passed**.

### 2026-09-29 - Spotlight box comment and one finding sentence corrected

Side task, no batch tag: two text corrections from the review of the previous commit, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The comment inside `.spotlight-image-box` in `static/css/results.css` now puts each fact at its own width: 7rem below 768px, 9rem from 768px, and the corner 4px below 1024px and 8px from it. It had read as if the box grew at 1024px. F-B23-19 no longer says Spotify often serves 640x427, which had no source; it says the review's case was 640x427. No rule or test changed.

Validation: `pytest -q` -- **2167 passed**.

### 2026-09-29 - Stale dashboards corrected and the review's findings filed

Side task, no batch tag: a documentation truth wave and five new findings from the second code review of PR #245 (Section H, and the findings to file from every section), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

SESSION_CONTEXT's structure list and dependency graph now match the source: the Spotify icon slice of the frontend gate and its edges (from `frontend_gate.py` and `_frontend_gate_results.py`), the results slice's other imports, and the docsync modules `markdown`, `transaction`, `archives`, `closeout` and `findings` with every edge read from each module's own import lines. The control-plane diagram in `docs/architecture/documentation-tooling.md` gains the icon slice's class and the edges from the results slice to it and from the results, theme and layout slices to the colour slice.

Smaller corrections: the README's provider-log sentence names Last.fm's `method` value as the one query parameter a line carries; the `heatmap_task` docstring says a failure is classified before it falls back to `internal_error`; the results spotlight comment says its 8px corner starts at 1024px; DEVELOPMENT.md no longer says "This session". FINDINGS.md: F-B23-9 (open, P1) moved under the P1 heading, and the line-number citations in F-B21-57, F-SWE-3, F-SWE-7 and F-DOCSYNC-14 are now names.

Filed: F-B23-16 (the error classifier's bare substrings), F-B23-17 (a Validation line with no digit passes `--check`), F-B23-18 (unmatched portraits with no link to Spotify, P1), F-B23-19 (letterboxed spotlight photo corners) and F-B23-20 (the spotlight waits for every candidate).

Validation: `pytest -q` -- **2167 passed**.

### 2026-09-29 - Frontend gate checks that could not fail now fail on their defects

Side task, no batch tag: ten frontend-gate checks and tests made to fail on the defects they name (second code review, findings D1 to D10; D1 is the earlier E6), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The inline-mark check (D1) now renders each mark inside two wrappers with different `color` and `--bars-color` and judges the painted fill and stroke, so a comment, a child path, a 3-digit hex or a later stroke rule can no longer hide a colour that ignores its wrapper. The non-square photo check (D2) judges the painted image box against the box that clips it, and fails a transform or clip-path on the image. The overlay check (D3) also reads `::before` and `::after`, and the animation check fails on any named animation or a running transform or filter transition.

The card-hidden check (D4) waits until the mock has seen and answered every candidate before it asserts the card stayed hidden. Both photo checks (D5) and the Spotify icon check (D6) wait for the image to load first, and an icon that never loads is reported by name. The focus-ring shots (D7) park the pointer and let transitions settle. The unmatched placeholder kind (D8) counts only visible nodes, and a missing visible placeholder is a failure. Comments (D9) now say the Deezer row is third by plays and say what the rotation check proves. The rotation test (D10) asserts hydration writes no `image_url` or `spotify_url` into `APP_DATA`.

Also corrected: a test docstring that still said the artwork radius is wrong only below 768px; it now names `ARTWORK_RADIUS_STEP_MIN` (1024px). D7 has no plant that separates old from new (a hover that differs between two shots cannot be reproduced), so it has a green run only. A zero-duration transition is not counted as an animation.

Validation: `pytest -q` -- **2167 passed**.
