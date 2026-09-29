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

### 2026-09-29 - Bold-label citations resolve and archives age at 90 days

Side task, no batch tag: resolving a citation of a bold label ending in a colon, and ageing archive pages at 90 days, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Controller finding X-1: `declarations._headings` indexed `**Co-author prohibition:** Do NOT ...` in `AGENTS.md` only as "Co-author prohibition:" (colon included), because the label-tail pattern needs whitespace after the colon and the rstrip set had no colon. A citation of "Co-author prohibition" therefore failed DOC010. The heading now also indexes the label with its trailing colon stripped; the three existing forms are unchanged. The DOC010 entry in `docs/architecture/documentation-tooling.md` says so.

Owner ruling 2026-09-29, "update the 365 day cold storage rule to 90 days": `DEFAULT_ARCHIVE_COLD_DAYS` and `[archives] cold_days` in `config/docsync.toml` are now 90, and `documentation-tooling.md` states the default and why (history older than a quarter is archive, not context). `--check` never ages pages, so nothing else moves.

Tests: two new tests in `tests/test_docsync_declarations.py` (the colon label resolves; a non-existent name still reports one DOC010 issue) and `test_default_cold_days_is_ninety` in `tests/test_docsync_archives.py` (91 days ages, 89 does not). Two existing tests were edited for the new default: `test_cutoff_is_strict` (page date moved to exactly 90 days before as-of) and `test_cold_days_is_configurable` (page date moved to 45 days before as-of).

Validation: `pytest -q` -- **2187 passed**.

### 2026-09-29 - Retry-After is capped and the last try never sleeps

Side task, no batch tag: capping the Retry-After sleep and dropping the sleep after the final attempt, a fix from the third review of PR #245, on the review-fix branch stacked on the WP-0 branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Review finding S1-3 (P1): `retry_with_semaphore` slept whatever `Retry-After` a provider sent, up to `retries` times, while the job thread held one of the `MAX_ACTIVE_JOBS` slots. Spotify sends 12-18 hour values under extended rate limits, so three sleeps outlived the 2-hour job record and the slot stayed held. New `config.MAX_RETRY_AFTER_SECONDS` (env, default 30): a larger value logs one WARNING (label, value, cap) and returns `default` at once, no sleep and no more attempts; at or below the cap it sleeps as before. The helper also no longer sleeps after the final attempt, on the Retry-After path or the backoff path. The header parse (S1-4) and a user-facing rate-limited code are separate findings. README and SESSION_CONTEXT name the cap; `.env.example` lists the optional variable.

Tests: six new tests in `tests/test_retry_with_semaphore.py` cover the cap, the value at the cap, the cap read from `utils`, two backoff sleeps for three failures, and no sleep after a rate limit on the final attempt. No existing test was edited.

Validation: `pytest -q` -- **2184 passed**.

### 2026-09-29 - A malformed Last.fm page is retried and counted as dropped

Side task, no batch tag: retrying a malformed 200 page and counting it as dropped, a fix from the third review of PR #245, on the review-fix branch stacked on the WP-0 branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Review finding S1-2 (P1): `fetch_recent_tracks_page_async` returned any body that parsed as JSON as a success, so an error payload served as a 200 on page 2..N was fetched once, never retried and counted as received: the job said `ok` with up to 200 scrobbles missing, and a `[]` body reached the aggregators and crashed them. `fetch_once` now treats a page that fails `_is_well_formed_page` like a non-200 response: one WARNING naming the page and the defect class (never the body), `None`, retried, and dropped and counted in `pages_dropped` if it stays bad. Finding S1-12: page 1 is checked by the same helper in `fetch_all_recent_tracks_async`, replacing the inline check that raised `TypeError` on a scalar body and the weaker second try block. No check was added on `recenttracks.track`: Last.fm can serve one track as an object, a separate matter. README and `top-albums-sequence.md` say a malformed page counts as a failed attempt.

Tests: the two tests that pinned the old contract (`test_fetch_recent_tracks_page_retry_after_malformed_page_reaches_network`, `test_fetch_recent_tracks_page_does_not_cache_a_malformed_page`) now expect `None` and the retry count; new tests cover recovery inside one call, the partial outcome through `fetch_all_recent_tracks_async`, and scalar and list page-1 bodies.

Validation: `pytest -q` -- **2178 passed**.

### 2026-09-29 - Last.fm api_key redacted from every log line

Side task, no batch tag: redacting the Last.fm `api_key` in every log line (review finding S1-1), a fix from the third review of PR #245, on the review-fix branch stacked on the WP-0 branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

aiohttp puts the full request URL, query string included, into `str(exc)`, and four sites logged it: `utils.run_async_in_thread` (message and traceback), the registration-year warning in `routes/album_flow.results_loading`, `utils.retry_with_semaphore`'s connect-timeout error line, and `utils.get_cached_response`'s debug line (the cache key embeds the URL). A POST to `/results_loading` with an unknown username wrote the key twice at production log level. `api_logging.RedactingFormatter` now replaces the value after `api_key=` or `api_key:` with `[redacted]` in any rendered line, traceback included, and `app.py` sets it on both log handlers. The trace hook's query exclusion stays the first layer. The check_* functions, the cache key and the route's missing `exists` check are unchanged. Five new tests in `tests/services/test_api_logging.py` and one in `tests/test_app_factory.py`, which checks both the rotating file handler and the stdout handler.

Validation: `pytest -q` -- **2173 passed**.
