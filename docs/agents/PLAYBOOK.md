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

### 2026-09-30 - Findings, dashboards and README made true for the merge

Side task, no batch tag: findings, dashboards and README made true for the merge, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Findings: F-B22-3, F-B21-61, F-MAS-5 and F-B18-2 named the removed job store (`repositories.py`, `create_job`, `cleanup_expired_jobs`, the `JOBS` dict); they now name `scrobblescope/jobs.py` (`jobs.create`, `jobs.expire_stale`, `MemoryJobStore`) by function. F-SWE-3 was already archived by the Task 30 landing; its archived body now says the one-try loop was how it stood when filed, and that a 5xx is retried now. `BATCH23_DEFINITION.md` WP-3 maps `ExportError` to a classified code through `jobs.fail` (the `set_job_results` at line 220 is a done, dated item and stays). F-B23-41 now records that the Results partial-notice link's ring and 44px are asserted only by a CSS-text test and the gate measures no such link.

Merge cut: PLAYBOOK Section 3 has a bullet stating what PR #245 ships and what moved to the follow-up PR (owner ruling 2026-09-29); the "next action" sentence that pointed at a finished review wave is reworded, and the seams bullet names only the work package each seam gates and points at that bullet for what ships. `**Next action:** WP-0 is next.` and the `**Branch:**` line are untouched. SESSION_CONTEXT Section 1 agrees.

Dashboards: SESSION_CONTEXT Section 3 no longer lists `global.css` (10 css files), and lists `results-release-checks.js`, the empty-state and two partial templates, and four `scripts/dev` files, with their edges in Section 4. `docs/architecture/top-albums-sequence.md` says once that every partial-data warning (token, search, details, Deezer fallback) also records its source through `jobs.record_partial_source`, and draws it at the token and Last.fm sites, and `runtime-system.md` lists it in the `jobs.py` interface. README: the `BATCH23_DEFINITION.md` link is gone (the rule is said in a sentence), the commit figure is the measured one (about 130 commits, 24 to 30 September), and the paragraph is rewrapped to 80 columns.

Code: the `heatmap_task` and `_report_album_failure` docstrings now say the album backstop always publishes `internal_error` while the heatmap classifies first. `.results-partial-notice__link` drops `white-space: nowrap` so the link wraps at 320px; confirmed at 320px by a Playwright measure of the notice with the shipped markup (page scrollWidth 320, no horizontal overflow), since the frontend gate renders no partial notice; the frontend gate and `results_behavior_tests.py` pass.

Known limit: an album-details 404 between Spotify refusals does not reset the per-job "three consecutive refusals" count; only a 200 does.

Validation: `pytest -q` -- **2487 passed**.

### 2026-09-30 - Partial runs disclosed on Results; forms gate waits for requests

Side task, no batch tag: partial runs disclosed on Results and a forms gate that waits for requests, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Results: a run degraded by dropped Last.fm pages or a Spotify/Deezer outage says so in one `role="status"` line above the stat block and table. The orchestrator now records the kind as data beside the sentence (`jobs.record_partial_source`, stat `partial_data_sources`, values `lastfm` and `provider`), and `_partial_run_notice` in `routes/album_flow.py` reads that, never the wording. Last.fm's own sentence is shown as written; the provider case is reworded for the results page. The link to Unmatched appears only when an album is filed as `provider_unavailable` ("could not be checked"), not for any unmatched album. The link has the focus ring and, under `any-pointer: coarse`, a 44px height. The loading page's `#partial-warning` is `role="status"`.

Announcements: `.wait-panel__error` (shared by both loading pages) is `role="alert"`, chosen over keeping the text in a live region because the heatmap page clears its phase line on error. On the album loading page `showFailure` also empties the polite phase line, so a failure is read out once.

Forms gate: the sleep-then-count waits are a bounded poll on the request count (`_wait_for_held`: 5 s bound, 150 ms settle so a surplus request is still caught), and the 503 check and the network-failure check wait, bounded, for the page's message instead of a fixed 100 ms. The remaining 100 ms wait is a negative proof (the verdict must not change). `record_load_faults` in `frontend_gate.py` prints app stylesheets, scripts and fonts that failed to load beside any FAIL (advisory; it never changes pass or fail). Live probes: with the debounce raised to 1200 ms the old module failed three checks and the new one none; with the message written 600 ms late the check passes, and with the wait removed it fails.

Smaller: both privacy route tests assert the real message; the CI no-secrets guard reads the whole workflow; comments that cited review ids or described the spotlight wrongly say the reason in words. `routes/album_flow.py` now imports `unmatched` (SESSION_CONTEXT dependency graph updated). The Task 30 breaker test also asserts that every album still went to Deezer after the breaker tripped.

Bookkeeping: F-B23-41 (row links under 44px, the gate measures no populated row) and F-B23-42 (spotlight rotation has no pause control for touch or keyboard readers) are filed; F-B23-39 names the forms gate's sleep against the 300 ms debounce as the cause of its "held 0" flake.

Edited existing tests: `test_results_loading_private_profile_does_not_start_a_job`, `test_results_loading_existing_private_user_is_refused_after_the_exists_check`, `test_test_job_env_passes_no_secret`, `test_deezer_throttling_degrades_and_records_the_album_as_unavailable`, `test_spotify_search_outage_degrades_to_deezer_and_lists_the_rest_as_unavailable`, `test_a_spotify_detail_outage_for_a_matched_album_is_unavailable_not_no_match`, `test_one_over_cap_retry_after_stops_the_jobs_remaining_spotify_searches` and `test_process_albums_partial_cache_token_failure_uses_cached_results` (each also asserts the recorded kind, the breaker test also that Deezer was asked for every album).

Validation: `pytest -q` -- **2487 passed**.
