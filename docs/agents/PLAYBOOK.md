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
  cache re-verification and MusicBrainz fixes run now on `fix/album-matching`
  (PR #270, plan `docs/superpowers/plans/2026-10-25-album-matching.md`),
  based on `main`. The documentation refresh merges last.
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

### 2026-10-25 - Give requests sharing a Spotify ID their own metadata

Side task, no batch tag: two requests that resolve to one Spotify ID each get their own metadata (D2, RB3), on `fix/album-matching`, stacked on PR #269.

Owner intent: a collaboration credited under two artists produced two keys mapped to one Spotify ID; the second overwrote the first in the ID-to-key map, so the loser fell to Deezer. `_run_spotify_search_phase` now returns a fifth element, `shared_id_requests` (the extra requests after the first for a mapped ID), and logs one count-only warning. `_run_spotify_batch_detail_phase` takes it and builds metadata per key with `album_metadata_from_details(spotify_id, details, key)`, filing each in `cache_hits` and `new_metadata` so each stored credit matches its own key; when an ID is unanswered, the extras join `detail_unavailable_keys`. `_fetch_spotify_misses` unpacks five values and passes the mapping. One fix round after review added a test guarding the `_fetch_spotify_misses` wiring and a privacy assertion on the warning (no names, no key parts). Recorded, not fixed: the warning fires once per extra request, which no three-key case pins.

Deviations: none. Task 9 (`AlbumCache.lookup` drops a mismatched row) landed first; the files are disjoint and the patch applied cleanly on it. Findings are not closed here; Task 11 closes them.

Edited existing tests: `test_run_spotify_search_phase_all_misses_returns_empty_maps` (also asserts `shared_id_requests == {}`) and `test_spotify_search_unanswered_album_does_not_cancel_its_siblings` (unpacks five values). New: `test_two_requests_sharing_a_spotify_id_each_get_their_own_metadata`, `test_unanswered_details_for_a_shared_spotify_id_mark_every_key`, `test_fetch_spotify_misses_credits_every_key_sharing_a_spotify_id`.

Validation: `pytest -q` -- **2932 passed**.

### 2026-10-25 - Treat a cached row naming another album as a miss

Side task, no batch tag: `AlbumCache.lookup` drops a cached Spotify row whose stored provider names do not fit its key (R2, RB1), on `fix/album-matching`, stacked on PR #269.

Owner intent: a row stored under "xiu xiu|a promise" could hold another album's ID (the old unchecked search), and until now it was served for 30 days. `lookup` now drops every hit whose `match_for(key)` is `MATCH_WRONG` and logs one INFO line with the count only, so the album is searched again and the existing upsert overwrites the row with stamped names. `MATCH_FITS` and `MATCH_UNSTAMPED` rows (including pre-migration Spotify rows with NULL names, and Deezer rows) are returned as before; `lookup_failed` and the fail-open path are unchanged. A dropped hit is not counted in `db_cache_lookup_hits`.

Deviations: none. Landed before Task 8 (disjoint files: Task 8 touches the orchestrator search and details modules; Task 8 was still in review).

Edited existing tests: none. The `_spotify` helper in `tests/test_album_cache_parity.py` gained an optional `credit` argument (details carry name and artists); no existing test changed. New: `test_a_spotify_row_naming_another_album_is_a_miss` (parametrized) in `tests/services/test_cache.py` and `test_a_cached_row_naming_another_album_is_searched_again_and_overwritten` in `tests/test_album_cache_parity.py`.

Validation: `pytest -q` -- **2929 passed**.

### 2026-10-25 - Accept only an exact album match in Spotify search

Side task, no batch tag: Spotify search accepts only a hit whose credited artist and title match the request (D1, RB3, RB4), on `fix/album-matching`, stacked on PR #269.

Owner intent: `search_for_spotify_album_id` took `items[0]` unchecked, so a missing album got another album (wrong track list, "0 secs"). It now asks for 5 hits (`limit` 5) and returns the first whose credited artist and title normalize to the request key; otherwise None. New pure `matching_credit(item, key)` does the comparison (a non-dict hit or non-text field returns None, never raises). `album_metadata_from_details` takes `key` (default None) and stamps `provider_artist` and `provider_title` from the credit that matched, else leaves both None and, given a key, logs one warning line with no names; `orchestrator/_details.py` passes the key. Fix round 1: review found that comparing the title alone went unnoticed, so the exact-match test gains a same-title, different-artist case. The sequence-diagram and README wording for the search step follow in Task 11 (RB13, RB14); F-B23-59 is closed by Task 11, not here.

Deviations: none.

Edited existing tests: `test_search_for_spotify_album_id_retries_429_then_returns_id`, `test_search_succeeds_on_first_try` and `test_search_retries_a_malformed_retry_after` (their fake bodies gain the name and artists a real hit carries), and the helper `_ok_search` (now takes artist and album; callers pass the request's own names: `test_search_401_drops_the_cached_token_and_retries_once_with_a_fresh_one`, the newer-cached-token 401 test, `test_an_answer_between_refusals_keeps_the_breaker_closed`, `test_a_call_given_a_stale_token_sends_the_valid_cached_one_first`, `test_an_expired_cached_token_is_not_adopted`, `test_concurrent_rejections_of_one_token_cost_one_token_request`).

Validation: `pytest -q` -- **2924 passed**.

### 2026-10-25 - Store the provider's own names and add match_for

Side task, no batch tag: store the artist and title the provider returned beside each cached album, and add `AlbumMetadata.match_for(key)`, on `fix/album-matching`, stacked on PR #269.

Owner intent: the cache keyed rows by the request's names, so a wrong Spotify match was indistinguishable from a right one. `spotify_cache` gains nullable `provider_artist` and `provider_title`; `AlbumMetadata` carries them (default None, still frozen), `from_row` reads them, `batch_lookup_metadata` selects them and `batch_persist_metadata` writes them (new array params $10 and $11, existing indexes unchanged). `match_for(key)` is the single re-verify rule (`MATCH_FITS`, `MATCH_WRONG`, `MATCH_UNSTAMPED`) for later tasks; `enrichment.py` now imports `normalize_name` from `domain`. The schema ships through `init_db.py` (the Fly release command) with no manual DB step, no data migration and no purge. Old rows read as unstamped (Spotify) or fits (Deezer). No behaviour change yet: nothing calls `match_for`, and `album_metadata_from_details` still leaves the names None (Tasks 7 and 10 fill them).

Deviations: the two columns are folded into the existing `ALTER TABLE spotify_cache ... ADD COLUMN IF NOT EXISTS` statement rather than a separate one (idempotent, judged so by review; keeps the statement count so `tests/test_init_db.py` needed no edit). Fix round 1: review found that dropping a name column from the upsert's `DO UPDATE SET` list left every test green; the persist-SQL test now requires both `EXCLUDED` assignments (the fake Postgres has no ON CONFLICT handling, so a round trip is not possible).

Edited existing tests: `test_album_metadata_holds_album_facts_only` (field-set pin gains the two names), `test_batch_lookup_metadata_returns_albums_with_their_provider_columns` (row, expected and SQL carry the names), `test_batch_persist_metadata_writes_a_spotify_id_to_both_columns` (asserts the two name arrays and the two `EXCLUDED` assignments), `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` (the stored-row shape in the parity test gains the two None fields).

Validation: `pytest -q` -- **2914 passed**.
