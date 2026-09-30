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

### 2026-09-30 - Make four gate checks judge what they name

Side task, no batch tag: four frontend-gate checks, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

S4-2: the spotlight photo fade check now keeps the rotation ticking and fails unless a swap fell inside its 1000ms sampling window. S4-5: the unmatched focus-ring check counts only pixels the ring adds (a second shot, still focused, with the ring forced off). S4-6: `_PHOTO_PAINT_JS` intersects every clipping ancestor and flags `clip-path`, and the first photo check now runs the crop judgement too. S4-10: the gate serves threaded, so an idle connection cannot stall a check. The heatmap ring reading is made deterministic (box read before and after the shot, retake on movement, scroll nudge for the tooltip, fonts-and-frames wait) for the 2026-09-29 flake, and the hold check catches only Playwright's `TimeoutError` (Codacy B110). Each changed check was proved on a planted defect, red on the old code and green on the new; a browser test runs the paint probe on a clipping grandparent.

Edited existing test helper: `_crop_overlay_page` in `tests/scripts/dev/test_frontend_gate_spotlight_photo.py` (the first photo check now also reads the paint probe and the new sample shape), used by `test_a_pseudo_element_scrim_and_a_transform_animation_are_reported`, `test_the_opacity_sampler_records_the_artist_and_runs_across_rotation_periods` and `test_the_first_photo_check_also_judges_the_crop`. Filed F-B23-36 (P3: S4-3, S4-4, S4-7, S4-8, S4-9, S4-11, the tooltip note, the flake as fixed by inference).

Validation: `pytest -q` -- **2277 passed**.

### 2026-09-29 - The job module gives a job's life one interface over a storage seam

Side task, no batch tag: the job module (`scrobblescope/jobs.py`), a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

A job's rules (one ending, results or an error; the lease renewed only by writes; results and 100% in one write) lived in seven callers of `repositories.py`, and F-B23-22 was the proof: two pipelines, two failure answers. They now live in `jobs.py`: `create`, `advance`, `report_phase`, `record_stat`, `record_unmatched`, `succeed`, `update_result`, `fail`, `fail_unclassified`, `reset`, `mark_interrupted` and the reads, over a `JobStore` seam with one adapter, `MemoryJobStore` (the old dict, lock and TTL). Task 20 adds the Postgres adapter and reruns the same `tests/test_jobs.py` suite through its `STORE_FACTORIES`. `repositories.py` is deleted with no shim and every caller, including the eight frontend-gate modules, is migrated. The progress vocabulary is folded in: five named bands replace the `phase` literals and the `base + int(span * done / total)` arithmetic, and both Last.fm callbacks take three arguments, so `_notify_progress_cb`'s signature sniffing is gone. `job_interrupted` joins `ERROR_CODES`. Percent values are unchanged.

Owner ruling (2026-09-29): seam commits may edit existing tests, and each edited test is named in the commit body; `BATCH23_DEFINITION.md`'s compatibility list, F-B23-1 paragraph and Acceptance bullet are amended to say so (Part A's own line is left as written). Edited existing tests: call sites and patch targets only, plus the assertions dropped or changed, each named in the commit body with where it is still guarded: `test_progress_callback_sends_correct_percentages` (the 100% dict, the error keys and the 0% init dict), `test_happy_path_stores_correct_result_dict` (`succeed` writes the results and 100% as one write) and `test_seed_spotlight_job_seeds_several_artists_and_marks_it_done` (the separate 100% write); the Last.fm progress callback also takes three arguments. `tests/test_repositories.py` keeps only its database-helper tests; its job tests moved to the new `tests/test_jobs.py` (45 tests), and one test was renamed. Not done here: `mark_interrupted` is not wired at startup (Task 20 wires it with the database adapter); `fail_unclassified` keeps F-B23-22 open. Test modules 81 to 82.

Validation: `pytest -q` -- **2254 passed**.

### 2026-09-29 - Refuse a stale or unfinished docsync publication; ignore CRLF in archives

Side task, no batch tag: docsync publication safety and CRLF archive drift, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

An interrupted publication leaves history only in the git-ignored `.docsync.journal` and both modes used to exit 0 (S3-2). New DOC026 makes `--check` exit 1 while the journal exists, and `--fix` replays it first, under the lock, restoring every file to its pre-run bytes; it refuses if a journalled file was edited since. Chose recovery on the next run over reordering the writes, since restoring pre-run bytes and re-planning cannot lose history for any file mix. Publication now compares against the bytes each file had when the plan first read it, so a concurrent edit is refused and nothing is written (S3-3). `ArchiveStore._diff` folds CRLF to LF, so a CRLF checkout of a paginated archive is not drift while a real content change still is (S3-7). Non-UTF-8 documents exit 2 with a diagnostic (S3-1), a path outside the repository is named instead of crashing (S3-4), and an unchecked box whose outcome says resolved or no action is DOC016 (S3-6). Review minors fixed here: a test for the state a real kill leaves (journal and stale lock), the DOC016 and DOC026 catalogue text, and `_snapshot`, so the baseline loop no longer makes the read-coverage test true by construction.

Edited existing tests: `test_close_batch_proves_every_read_source_before_publishing` (also records `Path.read_bytes`, since documents are read as bytes) and `test_stated_catalogue_helper_rejects_a_mismatched_list` (the sentence gains DOC026). Closed F-DOCSYNC-19; filed F-B23-35 (P3, S3-5, S3-8, the `.gitattributes` guard). No new test module.

Validation: `pytest -q` -- **2252 passed**.

### 2026-09-29 - Repo Assist removed; CI job holds no provider secrets

Side task, no batch tag: removing the Repo Assist workflow and CI's provider secrets, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Owner ruling (2026-09-29): Repo Assist is not configured properly and is dropped; CI is robust without it. `repo-assist.md`, `repo-assist.lock.yml`, the README sentence and the Repo Assist assertions in `tests/test_ci_workflows.py` are gone, and the S6-2 hardening (a docsync.toml guard for its PRs) is not built. S6-1 stays: `test.yml` no longer passes LASTFM_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET or SECRET_KEY at job level. No step reads a real key: `conftest.py` and `frontend_gate.py` supply placeholders, and a step that ever needs one takes it in its own `env:`. Proved by running the suite and the frontend gate with the four variables unset. The two comments that said CI passes the keys from repository secrets are corrected.

Edited tests: every test in `tests/test_ci_workflows.py` asserted on the Repo Assist workflow, so the module is rewritten around `test.yml`: `test_test_job_env_passes_no_secret` (job-level env carries no secrets reference) and `test_env_reader_flags_a_secret_and_a_missing_block`. Filed F-B23-32, F-B23-33 and F-B23-34 (P3, S6-3, S6-4, S6-5). Owner action: delete the Repo Assist repository secrets (for example CODEX_API_KEY, COPILOT_GITHUB_TOKEN) in GitHub settings if nothing else uses them.

Validation: `pytest -q` -- **2238 passed**.
