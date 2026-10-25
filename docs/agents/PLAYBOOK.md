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

### 2026-10-25 - Keep an identity for albums that normalize to nothing

Side task, no batch tag: give an album whose title normalizes to nothing its own identity, on `fix/album-matching`, stacked on PR #269.

Owner intent: albums named "?" or "EP" keyed as an empty album half in `normalize_name`, so any two such albums by one artist collided. `scrobblescope/domain.py::normalize_name` now falls back, when the cleaned and edition-stripped album is empty, to the raw text (NFKC, lowercase, whitespace collapsed) with "|" written as "%7c", so the key still splits cleanly in `format_album_key`. The artist half and every non-empty album key are unchanged. Docstrings of `normalize_name` and `format_album_key` say so. Cover wash for such albums changes (accepted). Added tests in `tests/test_domain.py`: `test_normalize_name_empty_remainder_keeps_distinct_pipe_free_identity`, `test_normalize_name_nonempty_remainder_keys_unchanged` (4 params) and `test_format_album_key_round_trips_empty_remainder_titles` (2 params).

Deviations: none. Edited existing tests: `tests/test_domain.py::test_normalize_name_ep_preserved_in_artist_stripped_from_album` (the album half is now "ep", not empty; it still asserts that an artist named EP is kept and an album EP is stripped of the edition word, and its docstring was corrected).

Validation: `pytest -q` -- **2883 passed**.

### 2026-10-25 - File the album-matching findings

Side task, no batch tag: file the five album-matching findings that the plan's later commits cite, on `fix/album-matching`, based on `main`.

Owner intent: the plan (`docs/superpowers/plans/2026-10-25-album-matching.md`) fixes problems the owner's real runs showed on 2026-10-25, and each later commit needs an open finding to close. `docs/agents/FINDINGS.md` now holds F-B23-59 (Spotify album search takes the first result unchecked), F-B23-60 (two albums sharing a Spotify ID overwrite each other; still reachable through collaboration albums), F-B23-61 (an album named "?" or "EP" normalizes to an empty key), F-B23-62 (a MusicBrainz 429 is cached as a final "no match", the P2 that corrupts a cache) and F-B23-63 (MusicBrainz request starts exactly 1.000s apart, P3). The artist spotlight's unchecked first result stays F-B23-26, open. Each names its function and one real case. Only `docs/agents/FINDINGS.md` and this log changed; no code or test.

Deviations: F-B23-64 was already taken (filed on PR #269), so the plan's IDs 59 to 63 were confirmed free in both the active file and the archive; F-B23-26 was not edited because the plan does not change its fix. Edited existing tests: none by this commit; the plan's later commits edit these existing tests, each named in its own entry: `tests/test_domain.py::test_normalize_name_ep_preserved_in_artist_stripped_from_album` (Task 2), `test_lookup_raises_when_musicbrainz_stays_throttled_not_no_match` (now `musicbrainz_unavailable`, response `headers = {}`) and the 503 retry tests that assert a fixed sleep, all in `tests/services/test_musicbrainz_service.py` (Task 3), and the search fakes in `tests/services/test_spotify_service.py` (Task 7).

Validation: `pytest -q` -- **2876 passed**.

### 2026-10-25 - Plan album matching and cache re-verification

Side task, no batch tag: committed the plan for the album-matching fixes, on `fix/album-matching`, a branch stacked on `feat/ui-round-2-backlog` (PR #269).

Owner intent: the owner's real runs on 2026-10-25 showed albums with plays but "0 secs" of listening time, which the session traced to Spotify album search accepting its first result unchecked, a second album silently taking a shared Spotify ID, and album names such as "?" and "EP" normalizing to nothing; and asked for MusicBrainz headroom ("since release checks run in the background it costs nothing") and rate-limit retries. `docs/superpowers/plans/2026-10-25-album-matching.md` (written by a plan-writer agent, reviewed three times, both findings of the last review checked by the controller): Spotify search takes the exact-match rule Deezer already uses over five candidates, any credited artist counts, a shared ID gives every request its own metadata, an empty-normalizing title keeps its raw identity, cached Spotify matches are re-verified on read by looking up their cached ID (two new nullable cache columns through `init_db.py`), MusicBrainz waits about 1.1s between request starts and treats 429 and 503 alike (Retry-After, else exponential backoff with jitter, never a cached "no match"), and F-B23-26 (the artist spotlight's unchecked first result) is fixed the same way. Deviations: none. Edited existing tests: none by this commit; the plan names each later edit. Validation: `pytest -q` -- **2994 passed**.

### 2026-10-25 - UI round 2 backlog: Section 3 marks plan A finished

Side task, no batch tag: make PLAYBOOK Section 3 agree with Section 4 about plan A, on `feat/ui-round-2-backlog`, a branch off `main`.

Owner intent: Section 3 and Section 4 must agree (AGENTS.md "Mid-batch handoff discipline"). Codex review round 1 on PR #269 (P1) found the Section 3 bullet still saying the PR is a draft with Task 12 and the final gates outstanding, while Section 4 records Task 12 done and the final verification gate passed at 4ef0e0af. The bullet now says PR #269 is out of draft, all fourteen tasks have landed, the final gate passed and the PR merges once its review is clean.

Deviations: this is the one exception to leaving Section 3 alone for this branch, by controller ruling; only that bullet's sentences changed. Edited existing tests: none.

Validation: `pytest -q` -- **2876 passed**.
