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

### 2026-09-30 - Provider refusals read as outages; an all-miss run finishes

Side task, no batch tag: provider refusals read as outages and an all-miss run finishing, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Refusals: a Spotify 400 or 403, a 401 that a freshly fetched token does not cure, and a Deezer HTTP 429 (with its Retry-After) or 403 are "could not answer" (`ProviderError`), never "answered, no match"; a genuine empty search and an album-details 404 stay answers. Spotify tokens are cached with a 60 s margin, a 401 drops the cached token once and retries once, and every call adopts a valid cached token before its first request, so a refresh is paid once per job (the batch one-by-one fallback is handed the refreshed token too). An in-job Last.fm 403 reads the body: only error 17 raises `PrivateProfileError`; any other 403 logs the status and error number (no body, no username) and follows the existing unavailable path. Last.fm's error-code page names no HTTP status per error code, so "403 means private" was never documented.

Per-job breaker: `SpotifyBreaker` in `spotify.py`, carried in a `ContextVar` set by `spotify_job_breaker()` around the Spotify phases of `_fetch_spotify_misses`, so signatures are unchanged and a concurrent job has its own. It trips on a Retry-After above the cap, on three refusals in a row with no answer between, or on a second 401 after a fresh token. It is checked at each function's entry and again inside every attempt, right after the semaphore and the rate limiter are held and immediately before the request: at entry alone every queued task had already passed the check before the first 429 came back (a reviewer's run sent 100 of 100 requests). A tripped breaker ends the retry loop at once and the call is unanswered without a request; Deezer still runs. A refusal logs one WARNING per kind per job (operation and status) and one summary line when the job's block ends; the retry helper no longer logs it as an ERROR. Concurrent first 401s can fetch the token up to the number of in-flight calls times (no lock); accepted, bounded by the search concurrency.

All-miss run: owner ruling 2026-09-30, "Finish, show Unmatched": a run where every album is "no match" on both providers succeeds with no albums and each album listed as `no_spotify_match`. `_detect_enrichment_total_failure`, its call and its seven tests are gone; the outage rule in `_fetch_spotify_misses` (Spotify answered nothing and Deezer enriched nothing) is unchanged, and "Spotify said no match for every album, Deezer could not answer for any" now has an end-to-end test (it succeeds; each album is listed unavailable). `top-albums-sequence.md` no longer draws the removed branch. The Results-page copy for this outcome is the frontend task's.

Smaller: `jobs.succeed` and `jobs.fail` refuse a second ending and log it (`start` and `reset` reopen a job); `jobs.exists` replaces a `context(...) is None` probe in `release_checks`; a Deezer `/tracks` call that ends in a terminal error makes the album a miss (not persisted with empty durations), while a body of JSON null keeps it with no durations; the `worker.py` docstring says what each caller publishes. `spotify_rate_limited`, `lastfm_rate_limited` and `job_interrupted` remain valid codes that no pipeline publishes (`spotify_rate_limited` is only a per-call code, `lastfm_rate_limited` is never raised, `jobs.mark_interrupted` has no caller); none is deleted, the UI maps them.

Bookkeeping: F-SWE-3 (a Spotify 5xx "ends the attempt loop after one try") is closed, since a 5xx is retried and raised as `ProviderError`; F-B23-40 files the Last.fm username in log lines.

Edited existing tests: `test_page_fetch_reports_a_private_profile_without_retrying`, `test_succeed_clears_an_earlier_failure`, `test_fail_internal_error_replaces_results_and_is_not_retryable`, `test_fetch_spotify_album_details_batch_non_200_returns_empty_dict`, `test_fetch_spotify_access_token_refreshes_expired_token` and `test_fetch_deezer_album_keeps_the_album_when_the_track_list_is_unreadable` (a JSON-null case added). Removed with the function: the seven `test_detect_enrichment_total_failure_*` tests.

Validation: `pytest -q` -- **2462 passed**.

### 2026-09-30 - Diagrams and README checked against what the PR ships

Side task, no batch tag: the pre-merge pass over the diagrams and README, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Diagrams: every module-level import in `scrobblescope/`, `scripts/docsync/`, the worktree guard and the frontend-gate slices was read by an `ast` walk and compared with the drawn edges; the call paths of both sequence diagrams were read against `orchestrator/`, `heatmap.py` and `routes/`. `runtime-system.md` gained two missing edges (`lastfm.py` to `errors.py`, `cache.py` to `utils.py`) and `delete` in the `jobs.py` interface list. `top-albums-sequence.md` no longer shows `enqueue_release_check` as a `jobs.py` call (it is `release_checks.py`) and records the below-threshold exclusions only after the Last.fm failure check, as `_fetch_job_albums` does. `heatmap-sequence.md`, `development-cycle.md` and `documentation-tooling.md` needed no change. "Last verified" in `docs/ARCHITECTURE.md` is now 2026-09-30.

README: the section on the foundation work describes what the PR ships, in plain prose with no ids or pointers (provider throttling no longer read as "no match", names out of provider failure lines, the fourth Unmatched group, the keyboard heatmap, the spotlight pause, the job module, Repo Assist removed); it says in one sentence that job persistence and the Last.fm restructuring come next. The bare worktree-guard bullet has a body, "Three reasons have shipped" says a fourth comes with this work, and the work-package wording elsewhere in the page is plain.

Dashboard: SESSION_CONTEXT Sections 3 and 4 were compared with source; the `utils.py` line names `log_failure` and `cancel_and_drain`, and "Last updated" is 2026-09-30. The `_search` and `_details` edges the task-18 review flagged were already correct. DEVELOPMENT.md: `--check`, the preflight, the worktree guard and `tailwind_build.py --check` were run and behave as written; the planted-defect demonstrations are scratch-copy runs and were not repeated.

Validation: `pytest -q` -- **2424 passed**.

### 2026-09-30 - Doc and hygiene findings from the third review cleared

Side task, no batch tag: the doc and hygiene findings, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Code: `cli._snapshot` (the staleness baseline of `--close-batch`) raises `SyncError` on an unreadable file, like `_read_text`, instead of a bare `OSError` traceback. The orphaned gh-aw lock file `.github/aw/actions-lock.json` and its `.gitattributes` line are deleted. Comments only: "for every miss" in the `orchestrator/__init__.py` docstring, and two over-long comment blocks in `tests/test_pipeline_integration.py` rewrapped.

Docs: how an album gets its release date is explained once, in `docs/architecture/runtime-system.md` (it now also holds the old "displayed release year" bullet and names `process_albums` and `_persist_new_metadata`); `_build_results` links to it; the README keeps its own plain summary (owner rule: no pointers in the README). `docs/design/RECONCILIATION.md` still retells the release-date rationale; it is a dated design record, seen and left. The release-scope table is written once, in `domain.release_window`'s docstring, which names the wording sites and says its list is not exhaustive; `_get_user_friendly_reason` and `_get_filter_description` say "wording only" and link to it. The finished plan `docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md` (about line 27) says a commit on another branch is refused by the worktree guard; it was seen and left as point-in-time. The ignored local `CLAUDE.md` of the batch worktree was corrected (the guard reports WT003 but the hook is advisory); it is not in the commit.

Bookkeeping: the log archive's heading date is corrected to 2026-09-29 (no DOC025); F-B23-33's problem statement is one sentence; F-B23-29 is closed and its leftovers are F-B23-38; F-B23-39 records the gate's intermittent failures.

New test: `test_snapshot_raises_sync_error_for_an_unreadable_file` (in `TestPublicationSafety`); no existing test was edited or moved.

Validation: `pytest -q` -- **2424 passed**.

### 2026-09-30 - Small frontend findings from the third review cleared

Side task, no batch tag: small frontend findings F-B23-27, F-B23-28 and the frontend part of F-B23-29, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Layout: long artist credits shrink inside their Results cell (`.album-info { min-width: 0 }`); the below-threshold figures wrap below 768px instead of clipping "1234 plays"; four unmatched panels stack in two columns, the release-scope panel spanning the right column and the first, third and fourth panels down the left (a new gate check, `four_panel_stack_failures`, holds the stacking; screenshots at 1280px and 1920px checked).

Behaviour: Escape closes hover and tap heatmap tooltips, and the keyboard tooltip follows a scroll at once (no animation-frame lag); a reduced-motion or single-candidate spotlight card reserves no height, and a rotating one measures without a link it does not own; `pointerenter` needed no seed (Chromium fires it after a layout change; the test says Chromium only, as the behaviour runner drives no other engine). Markup and style: axis labels are `aria-hidden`; one 12px `.provider-badge` rule in the narrow face (gate judge `provider_badge_failures`); `default('', true)` on two data attributes; results.js block-level functions are `const` arrows; dead `content` lookup, `img` reset, per-call `reducedMotion` read and `formatDurationMobile` removed; unresolvable comments rewritten.

Tests: three gate tests that launch Chromium (`test_the_layout_check_keeps_the_rotation_going_and_sees_every_width`, `test_the_hold_check_focuses_then_hovers_and_counts_the_periods`, `test_the_opacity_sampler_records_the_artist_and_runs_across_rotation_periods`) were unmarked and would have failed CI's `-m "not browser"` coverage step; they carry `@pytest.mark.browser` (with Playwright made to raise, `-m "not browser"` ran 3 failures before and none after). The stale "43 tests" comment in `test.yml` holds no number now.

Edited existing tests: `test_unmatched_view_renders_artwork_in_every_reason_group` (fourth reason, order pinned); `test_reduced_motion_keeps_first_confirmed_artist_after_failed_hydration` and the `spotlight()` helper in `results_behavior_tests.py`; `test_the_layout_probe_reads_words_by_the_lines_their_characters_sit_on` (deleted, replaced by a Chromium test of the probe); the `keepRotating` text assertions in three spotlight-photo gate tests (now run the mock in Chromium); `test_a_badge_with_no_narrow_token_to_compare_fails` (pins the message). The gate's `check_unmatched_report` seed carries four digits of plays and its threshold expectation changed with it.

Validation: `pytest -q` -- **2423 passed**.
