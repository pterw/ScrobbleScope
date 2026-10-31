<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0022

### 2026-09-23 - The export contracts are made consistent

Side task, no batch tag: a definition edit within Batch 23, made before
WP-1. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Author.** Codex (GPT-6) made these edits at the owner's request, after
  a read-only review of `BATCH23_DEFINITION.md` and the current execution
  path. The definition's header lists all seven changes and why.
- **The definition** gains a "Data handling" section as the one owner of
  the privacy contract. It separates listening history, which stays in
  memory, from reusable catalog metadata, which the existing enrichment
  cache may keep. It also makes these changes:
  - It separates failures refused before a job exists from content
    failures that end a running job.
  - WP-2 now hands WP-3 a pre-threshold album mapping, and WP-3
    partitions it once.
  - The memory acceptance measures the whole process, not only admitted
    buffers.
  - WP-6 must settle a statistics contract before it is implemented.
  - Each WP gets its own SDD plan, and that plan owns the task order.
- **The export outline**
  (`docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md`)
  and `README.md` now point at the definition instead of repeating the
  older privacy and aggregation wording. The outline's stale
  `routes.py` and `orchestrator.py` paths are updated.
- **Also corrected:** Section 3 still called Batch 23 "queued" and "not
  started", and named the outline as its plan. That bullet now says the
  batch is active and calls the file its cross-WP outline. A sweep found no
  other copy of the replaced wording outside dated history.
- **No effect on WP-0.** The WP-0 plans, their order and the next action
  (reconcile Task 12) are unchanged.
- **Scope:** documentation only. No code, test or gate changed.

Validation: `pytest -q` -- **1746 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The release-window rule gets a task of its own

Side task, no batch tag: a planning change within Batch 23 WP-0. Untagged
by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Filed F-B23-5 at P2, and the owner added it to WP-0 Part C
  (2026-09-23).** `release_checks._window_end` restates the scope table
  that foundation Task 12 moved to `domain._matches_release_criteria`, so
  the release-window rule has two copies. They already differ at the
  edges: an unparseable decade excludes every album in the filter but
  gives the worker no window.
- **Plan:** the reconcile plan gains Task 12, the last task of Stage 2 and
  before Stage 3. It pins both consumers' current outputs with parity tests
  first, then derives both from one `domain.release_window`. Changing the
  unparseable-decade behaviour needs an owner ruling before dispatch. The
  definition's Part C now lists F-B23-5 as the fourth owner-added P2, and
  the plan's disposition table has its row.
- **Also corrected:** the plan's Acceptance said only Tasks 4 and 6 edit
  an existing test. Task 11 replaced one too, so it now says 4, 6 and 11.
- **Scope:** documentation only. No code, test or gate changed.

Validation: `pytest -q` -- **1746 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Release checks run without the cache DB

Side task, no batch tag: fixes F-B22-8, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 11 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/release_checks.py`'s `run_release_checks` no longer
  returns early when `_get_db_connection()` finds no cache: it logs
  "Release checks running without the cache DB: findings will not be
  saved." and runs the job's candidates against MusicBrainz regardless,
  guarding the three uses of `conn` (`_lookup_cached`, `_check_candidate`'s
  persist, and the `finally` close) with `if conn`. Everything else is
  unchanged: the job still ends `done`, the per-result outcomes are the
  same, and the shared one-request-per-second limiter still paces the
  requests. `tests/services/test_release_checks.py` replaces
  `test_run_release_checks_marks_skipped_without_a_db_connection` with
  `test_run_release_checks_runs_without_a_db_connection` (asserts the
  lookup runs, nothing is persisted, and the result still moves out) and
  adds
  `test_run_release_checks_without_a_db_connection_survives_a_lookup_error`
  (a MusicBrainz failure with no connection still ends `done`).
  `test_run_release_checks_closes_the_connection_when_a_lookup_raises`
  passes unchanged, proving the connected path still closes.
- **F-B22-8 is resolved.** `run_release_checks` runs its candidates
  without a cache connection and skips only the cache read, the persist
  and the close.
- **Deviation from the brief (controller-directed).** F-B23-3's status
  paragraph is rewritten: it stays open (P2), now says F-B22-7 and
  F-B22-8 have both landed (reconcile Tasks 4-6 and 11) and are to be
  reassessed against the code they left, and drops the "keep it out of
  their commits" sentence now that both have landed.
- **Forward guidance:** Stage 2 is complete. Next is Stage 3, this plan's
  Task 10.

Validation: `pytest -q` -- **1746 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The capacity refusal states the configured cap

Side task, no batch tag: fixes F-LOAD-1, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 9 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/routes/__init__.py` gains `_capacity_message()`,
  which returns `f"Too many requests in progress: all {MAX_ACTIVE_JOBS}
  search slots are busy. Please try again in a moment."`, reading
  `MAX_ACTIVE_JOBS` from `scrobblescope.config` rather than a literal.
  `scrobblescope/routes/album_flow.py`'s and
  `scrobblescope/routes/heatmap_flow.py`'s refusal strings now both read
  `_routes._capacity_message()` through the existing `_routes` module
  reference. There is no occupancy counter: the message only renders after
  `acquire_job_slot()` has just failed, when every slot is already taken, so
  a count would always read cap/cap. Two new tests in `tests/test_routes.py`
  cover it: `test_album_capacity_refusal_states_the_configured_cap` and
  `test_heatmap_capacity_refusal_states_the_configured_cap`, both patching
  `MAX_ACTIVE_JOBS` to a distinctive value and asserting the refusal names
  it.
- **F-LOAD-1 is resolved.** Both refusals read
  `routes._capacity_message()`, which states the configured
  `MAX_ACTIVE_JOBS`.
- **Deviation from the brief.** The brief's Step 5 dependency-graph line
  for `routes/__init__.py` omitted `domain`, which the module has imported
  (`format_album_key`) since `d20a7924`. The `config` edge from this task
  is added alongside the missing `domain` edge in the same edit, so the
  line now reads `routes/__init__.py <- config, domain, lastfm,
  repositories, spotify, unmatched, utils, worker; ...`. No other
  dependency-graph line was touched.
- **Forward guidance:** next is reconcile Task 11 (F-B22-8, release checks
  run without the cache DB).

Validation: `pytest -q` -- **1745 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The year gate reads the UTC calendar

Side task, no batch tag: fixes F-B21-6, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 8 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/routes/__init__.py` gains `_current_year()`, which
  returns `datetime.now(timezone.utc).year`; `inject_current_year` now
  returns `{"current_year": _current_year()}` instead of reading the host's
  local clock. `scrobblescope/routes/album_flow.py`'s two `datetime.now().year`
  sites -- the results-page year fallback and the submit-path validation
  gate -- now read `_routes._current_year()` through the existing `_routes`
  module reference, and the file's now-unused `datetime` import is removed.
  Two new tests in `tests/test_routes.py` cover it:
  `test_current_year_reads_the_utc_calendar` (the helper itself, against a
  clock stub whose local and UTC readings disagree) and
  `test_results_loading_year_gate_uses_the_utc_year` (the submit-path gate's
  upper bound comes from `routes._current_year()`).
- **F-B21-6 is resolved.** Every year gate reads `routes._current_year()`,
  which uses `datetime.now(timezone.utc)`, so the gate and the orchestrator's
  UTC-built fetch window can no longer disagree around New Year.
- **Forward guidance:** next is reconcile Task 9 (F-LOAD-1, the capacity
  refusal states the configured cap).

Validation: `pytest -q` -- **1743 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The frontend gate's one-off touch-target failure is filed

Side task, no batch tag: a finding filed during Batch 23 WP-0. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Filed F-B23-4 at P2, non-blocking (owner ruling, 2026-09-23).** After
  reconcile Task 7 committed, the independent gate run's frontend gate
  failed once in `check_touch_targets`: two `.btn` controls on the 404 page
  measured 40px high in the wide-touch profile. The same tree then passed
  three times. The finding records why only that profile can fail (at
  1280px only `error.css`'s `any-pointer: coarse` rule gives `.btn` its
  44px) and that the check measures with nothing waiting for that rule.
- **Scope:** documentation only. No code, test or gate changed. WP-0 Part C
  clears P0 and P1 findings, so a P2 finding stays out of WP-0.
- **Forward guidance:** until F-B23-4 is fixed, re-run a frontend-gate
  failure once before acting on it when the implementer's own runs were
  green. Next is reconcile Task 8 (F-B21-6).

Validation: `pytest -q` -- **1741 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Both pipelines end a crash as internal_error

Side task, no batch tag: fixes F-SWE-5, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 7 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/errors.py` gains an `internal_error` entry
  (`source: "internal"`, `retryable: False`). `heatmap.py`'s
  `_report_heatmap_failure` now publishes it instead of borrowing
  `lastfm_unavailable`. `orchestrator/__init__.py` gains
  `_report_album_failure`, called from `background_task`'s `on_run_error`
  in place of a bare `logging.exception`, so the album pipeline now
  publishes a terminal state on an unhandled crash instead of leaving the
  job stuck. `static/js/loading.js`'s `showFailure` now looks up the source
  label in an `ERROR_SOURCE_LABELS` map and hides the source line for any
  source not in it (`internal` included), instead of defaulting every
  unrecognized source to "Spotify". `scripts/dev/_frontend_gate_pipeline.py`
  pins both: the album rate-limit failure still names `Source: Last.fm`,
  and a probed `internal` failure hides the source line.
- **Two architecture diagrams updated in the same commit:**
  `docs/architecture/heatmap-sequence.md`'s `opt Unhandled exception
  anywhere above` block now draws `set_job_error(internal_error)`, with its
  closing prose split to say the inner, status-based Last.fm path still
  emits `lastfm_unavailable` while the outer backstop publishes
  `internal_error`. `docs/architecture/top-albums-sequence.md`'s `opt
  Exception escaping that handler` block now draws
  `set_job_error(internal_error)` and its note says the pipeline publishes
  a terminal state, so a polling page stops instead of waiting forever.
- **Tests added, three in total, none replaced:**
  `TestErrorCode.test_internal_error_exists` and
  `TestHeatmapTask.test_unhandled_crash_publishes_internal_error`
  (`tests/test_heatmap.py`), and
  `test_background_task_crash_publishes_internal_error`
  (`tests/services/test_orchestrator_fetch_and_process.py`). No existing
  test changed.
- **This resolves F-SWE-5.** Both entry points now publish `internal_error`
  from their outer handler, so a fault that is ours is no longer reported
  as a Last.fm outage, and the album pipeline no longer leaves a polling
  page waiting on a job that would never finish.
- **Bookkeeping:** the reconcile plan's Task 7 steps are ticked. Section 3's
  order list now records Task 7 landed alongside Tasks 3-6 in Stage 2.

Validation: `pytest -q` -- **1741 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The unused enrich_albums is retired

Side task, no batch tag: fixes F-B22-7, part 3 of 3, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 6 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/spotify.py`'s `enrich_albums` is deleted: after Task 5,
  the live path already does everything it did, through
  `_run_spotify_search_phase` and `_run_spotify_batch_detail_phase`, with the
  per-phase progress the loading page shows that `enrich_albums` never had.
  `scrobblescope/orchestrator/__init__.py` drops its import and its
  `__all__` entry; `album_metadata_from_details` keeps both, since
  `_details.py` still calls it through the facade. `git grep -n
  "enrich_albums" -- '*.py'` now returns nothing.
- **Tests removed, five in total, none replaced:**
  `test_enrich_albums_empty_misses_makes_no_request`,
  `test_enrich_albums_returns_matched_and_unmatched`,
  `test_enrich_albums_marks_unmatched_when_detail_lookup_misses` and
  `test_enrich_albums_handles_missing_cover_art`
  (`tests/services/test_spotify_service.py`, with their banner comment and
  the `enrich_albums` import), and
  `test_enrich_albums_is_exposed_on_the_orchestrator_facade`
  (`tests/services/test_orchestrator_fetch_spotify.py`, with both of its
  `enrich_albums` imports).
- **This resolves F-B22-7.** The Spotify payload is translated only in
  `spotify.album_metadata_from_details`; every metadata row is built by
  `AlbumMetadata.as_cache_row`, whose Deezer rows no longer carry an id in
  `spotify_id` (Task 4); the unused `enrich_albums` and its tests are gone.
- **Bookkeeping:** the reconcile plan's Task 6 steps are ticked. Section 3's
  order list now records Task 6 landed alongside Tasks 3-5 in Stage 2.

Validation: `pytest -q` -- **1738 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The Spotify payload is translated once, in spotify.py

Side task, no batch tag: fixes F-B22-7, part 2 of 3, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 5 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/spotify.py` gains `album_metadata_from_details`, the
  one place the application reads a Spotify album object into the provider
  contract; `enrich_albums` now calls it instead of building `AlbumMetadata`
  inline. It is re-exported on the orchestrator facade
  (`scrobblescope/orchestrator/__init__.py`).
- **The detail phase files, it no longer parses.**
  `scrobblescope/orchestrator/_details.py`'s "Extract cacheable fields" loop
  now calls `_orchestrator.album_metadata_from_details` and appends
  `metadata.as_cache_row(...)` (Task 4's contract) instead of building the
  row by hand; its now-unused `normalize_track_name` import is dropped, and
  the module docstring names the new cross-cutting dependency.
  `scrobblescope/orchestrator/_deezer_fallback.py`'s inline 9-tuple is
  replaced the same way. Since Task 4, that tuple was already identical to
  what `as_cache_row` writes, so the Deezer row is unchanged in shape.
  `provider_url` for a Spotify row now holds the album's Spotify URL instead
  of `NULL`, since the 9-tuple form carries it; `_batch_persist_metadata`
  still accepts 6-tuples.
- **Tests added, four in total:**
  `test_album_metadata_from_details_translates_one_payload` and the
  parametrized `test_album_metadata_from_details_degrades_field_by_field`
  (`tests/services/test_spotify_service.py`, two cases: no `images` key and
  an empty list), and `test_process_albums_persists_a_spotify_row_through_the_contract`
  (`tests/services/test_orchestrator_process_albums.py`), which pins the
  live Spotify path's persisted row as the provider contract's nine-element
  form. No existing test changed.
- **Bookkeeping:** the reconcile plan's Task 5 steps are ticked. Section 3's
  order list now records Task 5 landed alongside Tasks 3 and 4 in Stage 2.

Validation: `pytest -q` -- **1743 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - A Deezer id no longer lands in the Spotify column

Side task, no batch tag: fixes F-B22-7, part 1 of 3, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 4 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `AlbumMetadata.as_cache_row` (`scrobblescope/enrichment.py`) now
  writes `album_id` into the `spotify_id` column (tuple index 2) only when
  `provider == "spotify"`; every other provider writes `None` there, matching
  what the live Deezer fallback has always written at that column. F-B22-7 is
  not resolved by this task -- Tasks 5 and 6 complete it.
- **Two existing assertions changed**, both in
  `tests/services/test_enrichment.py`, because the finding requires it:
  `test_album_metadata_carries_its_provider_and_url`'s expected tuple pinned
  the Deezer album id at index 2, and
  `test_cache_row_matches_what_the_persistence_layer_unpacks` asserted
  `row[2] == meta.album_id` for a Deezer row -- both pinned the pre-fix
  (wrong) value the method wrote before this change. A new test,
  `test_cache_row_puts_a_spotify_album_id_in_the_spotify_column`, pins the
  Spotify case.
- **Bookkeeping:** the reconcile plan's Task 4 steps are ticked. Section 3's
  order list now records Task 4 landed alongside Task 3 in Stage 2.

Validation: `pytest -q` -- **1739 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Reading a job no longer renews its lease

Side task, no batch tag: fixes F-SWE-6, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 3 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done, for the owner's Q1 = a: reads never renew a job's lease.
  `get_job_progress`, `get_job_unmatched` and `get_job_context`
  (`scrobblescope/repositories.py`) no longer write `updated_at`;
  `cleanup_expired_jobs` still reaps on that field, but only a writer now
  renews it. A polled job -- an open results tab, or the release-check
  worker's `get_job_context` existence check -- expires `JOB_TTL_SECONDS`
  after its last write, not its last read.
- **Test added:** `test_reading_a_job_does_not_renew_its_lease`, parametrized
  over the three getters (`tests/test_repositories.py`). No existing test
  asserted the old renewal, so none changed.
- **`scrobblescope/config.py`:** a new comment above `JOB_TTL_SECONDS` states
  the reads-never-renew contract.
- **F-SWE-6 resolved**, with the canonical record and a completion date;
  `doc_state_sync.py --fix` rotated it into
  `docs/history/findings/FINDINGS_ARCHIVE.md`.
- **Bookkeeping:** the reconcile plan's Task 3 steps are ticked. Section 3's
  order list now records Stage 2 as started, with Task 3 landed.
- **Fix round 1:** F-SWE-5's body still called F-SWE-6 out as compounding
  it ("a polled job never expires"), which this task's own fix made false.
  Reworded to the past tense: F-SWE-6 used to compound it; since it was
  settled, the stuck job now expires `JOB_TTL_SECONDS` after its last write.
  The reconcile plan's Step 5 sweep is re-run with wrapped-line variants; no
  other sibling copy survives outside `BATCH23_DEFINITION.md`'s historical
  before/after narrative and `README.md`'s unrelated metadata-cache TTL
  sentence, both out of this task's scope. No test added.

Validation: `pytest -q` -- **1739 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The work-package state gap is filed as F-DOCSYNC-15

Side task, no batch tag: files the docsync work-package state gap this
amendment exposed, part of Batch 23 WP-0 Part B. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- **Task 2 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scripts/docsync/parser.py` `_collect_wp_numbers` counts every
  `WP-<n>` token in a current-batch entry heading as a completed work
  package, so the first commit of a multi-commit work package already makes
  the dashboard name the next one -- verified directly before filing:
  `docs/history/logs/BATCH22_LOG.md` carries three `(Batch 22 WP-4)` entries
  dated 2026-09-20, all landed before WP-4 was actually done, and
  `_collect_wp_numbers` regex-matches `WP-(\d+)` against each entry heading
  with no completion check at all.
- **Filed as F-DOCSYNC-15** under `FINDINGS.md` "P1 -- Next batch
  candidates", status open (P1), unchecked. The body records the owner's Q4
  fix shape (2026-09-23): a work package closes only on an entry carrying an
  explicit `**Status:** WP-N complete` line, which the control-plane
  follow-on plan implements.
- **Bookkeeping:** `BATCH23_DEFINITION.md` WP-0 Part B's "File the docsync
  gap this amendment exposed" checkbox is ticked (done 2026-09-23, as
  F-DOCSYNC-15); its Part C set now names F-DOCSYNC-15 alongside the "38 IDs
  plus one" count. The reconcile plan's Task 2 steps are ticked. Section 3's
  order list now records Stage 1 (Tasks 1 and 2) as complete.
- No code changed; no test added.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - Export upload ownership, three depth findings, and a template fix

Side task, no batch tag: records owner rulings on the 2026-09-23
architecture-depth proposal, part of Batch 23 WP-0. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands. No code changed. With Task 12's
fix round (`972264f`) reviewed clean, Part A -- the loop protocol, the
three extractions and the release-window leaf -- is complete.

- **The proposal is now tracked** as
  `docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`, renamed from
  the owner's "ScrobbleScope - further architectural depth.html" to the
  reports folder's topic-and-date form. An older `.htm` draft beside it stays
  untracked. DOC001 checks only `.md` references and skips paths containing
  spaces, so the rename is a naming convention, not a gate fix.
- **Card 04 amends the export plan now.** The upload has one owner at every
  moment and is never copied: the route owns it until the thread starts and
  closes it on every refusal, and the task owns it after that. Admission
  also caps export jobs in flight at `EXPORT_MAX_IN_FLIGHT`, because the
  parse semaphore bounds running parses, not buffers waiting for a permit.
  The export plan's new "Upload ownership and the waiting bound" section
  holds the rule, and the definition's WP-3 and WP-4 checkboxes and
  acceptance carry it. The plan's Phase 2 now records the Part A
  extractions as landed, under their real names.
- **Cards 01-03 are filed at P2** as F-B23-1 (album calculation returns its
  whole answer), F-B23-2 (Last.fm translates its own payload) and F-B23-3
  (the cache module owns its connection). F-B23-1 is timed by the owner:
  after WP-0's provider repairs and before WP-6's design, with any move into
  Batch 23 needing its own scope amendment. The definition's WP-6 names that
  decision point.
- **The reconcile plan's finding template is corrected.** It put the reason
  on the status line (`resolved -- <reason>`). The gate accepts only a bare
  `resolved` or `no action`, and Task 1's implementer found this by running
  `--fix`. The template, Task 1 Step 3's record of what ran, and Task 10
  Step 2's no-action form now follow the archive's order: status,
  completion date, then the reason on its own line.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.
