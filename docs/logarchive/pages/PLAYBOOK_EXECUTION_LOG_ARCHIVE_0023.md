<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0023

### 2026-09-24 - The loading page looks up its error source label in a Map

Side task, no batch tag: close Codacy's object-injection flag on the loading
page's error source label, part of Batch 23 WP-0 Part C. Untagged by owner
ruling 2026-09-23 until the whole of WP-0 lands.

- **Why.** Codacy's check failed on PR #241 with one high issue, "Variable
  Assigned to Object Injection Sink", at `static/js/loading.js`'s
  `const label = ERROR_SOURCE_LABELS[source];`. It is not exploitable: the
  server sends only `lastfm`, `spotify` or `internal`
  (`scrobblescope/errors.py`), and the label goes into `textContent`. But an
  object-literal lookup resolves inherited keys, so a source of
  `constructor` would have printed `Source: function Object() ...`.
- **Change.** `ERROR_SOURCE_LABELS` is a `Map`, read with `.get(source)`.
  An unknown or inherited key finds nothing, so the source line stays
  hidden. The failure call that passes no source is unchanged:
  `Map.get(undefined)` is `undefined`, as the object lookup was. The JSDoc
  says why it is a Map. Nothing else changed; the reconcile plan's Task 7
  code block keeps the object form it shipped with, as a record.
- **Found by** the cloud session, which could not run the frontend gate
  (no Playwright browsers in its sandbox), so the change was made locally.
- **Also corrected:** the heading of the cloud-handoff entry below carried
  a `WP-<digit>` token, against the untagged-entry rule; it now reads
  without one.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. The frontend
  gate ran, since `static/` changed.

### 2026-09-24 - The Batch 23 foundation work gets a handoff a cloud session can run from

Side task, no batch tag: session handoff for Batch 23 WP-0, which moves to a
cloud session. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Why.** The owner is moving the work to a cloud session, which has only
  the repository. The local sessions kept their working state outside Git:
  the SDD ledgers and workspace constraints (`.superpowers/sdd/`, ignored),
  the four agent definitions (user-level, `~/.claude/agents/`), and the
  owner's working agreements (session memory). The gate commands were also
  Windows paths.
- **Added.** `docs/history/reports/HANDOFF_2026-09-24.md`, the new entry
  point: state, Linux setup, how the subagent loop runs without the plugin
  scripts, next steps with Task 5's owner ruling, rulings in force, open
  items and traps. `.superpowers/cloud-kit/constraints.md` is the Linux form
  of the workspace constraints (gates on `.venv/bin`, Lessons L1-L10).
  `.superpowers/cloud-kit/agents/` holds the four agent definitions,
  copied unchanged. `.superpowers/sdd/.gitignore` is now tracked, so a
  fresh clone keeps new SDD workspaces out of Git.
- **Not added.** The root `CLAUDE.md` stays git-ignored, as `.gitignore`
  records; the cloud session's first prompt names the handoff instead. The
  SDD helper scripts stay out too (vendored skills are local harness state
  per `.gitignore`); the handoff gives their plain `git` and `awk` forms.
- **Section 3** points its handoff bullet at the new file.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-24 - The owner's live check closes the logging task

Side task, no batch tag: a Section 3 correction, part of Batch 23 WP-0 Part
C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **What.** The reconcile plan's Task 13 (F-B23-6) landed as `433120c` and
  its fix round as `e7e076b`. Its Step 5, the owner's live check against
  the real providers, was left to the owner. The owner ran a job with
  `DEBUG_MODE=1` on 2026-09-24 and confirmed the log: per-call DEBUG lines
  such as `MusicBrainz GET /ws/2/release-group/ -> 200 in 133ms` and
  `Spotify GET /v1/search -> 200 in 241ms`, INFO summaries, and no query
  value. Section 3 and the plan's Step 5 now record it done.
- **Observation for a later task.** The owner's log shows one
  `Spotify: 1 calls` INFO summary per Spotify search, each from its own
  runner thread. So that path builds one session per call, and the
  per-session summary becomes one INFO line per album rather than one per
  job. It may also mean connections are not reused there. Not fixed here.
- **Fix-round note.** The fix-round implementer for `e7e076b` stopped at a
  rate limit after its edits and before its gates. The controller read the
  diff, ran `--fix`, the suite, pre-commit and `--check`, repeated the
  scratch-copy mutation proof, and committed. That fix round has no
  independent re-review yet.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-24 - The release-check finish line names both corrections

Side task, no batch tag: fix round 1 on Task 13 (F-B23-6), part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **What the review caught.** `run_release_checks`'s finish line (the entry
  below, from `433120c`) logged `state["moved_out"]` alone as "corrected".
  That hid `state["moved_in"]` -- an excluded album whose original release
  MusicBrainz found to fall back inside the window, just as real a finding
  as a moved-out result, and the whole reason this task exists is so the
  owner can see what MusicBrainz found.
- **Fix.** `scrobblescope/release_checks.py`'s finish line now names both
  counts: `"{checked} checked, {moved_out} moved out, {moved_in} moved in"`.
  No artist or album names, as before.
- **Test.** `tests/services/test_release_checks.py`'s finish-line test
  (its own new test from `433120c`, so changing it is in scope) is renamed
  `test_run_release_checks_logs_its_finish_with_moved_out_and_moved_in_counts`
  and now drives a job with two results that move out and one exclusion
  that moves in, asserting `2 moved out` and `1 moved in` -- distinct,
  non-zero counts, so a swap of the two would fail the test.
- **New test: a logging failure never fails a request.**
  `tests/services/test_api_logging.py` gains
  `test_a_recording_failure_never_fails_the_request`: with `_record`
  monkeypatched to raise, a real request through `create_optimized_session()`
  against a local `TestServer` still returns its response normally, and an
  explicit `close()` afterwards still does not raise. Proved to actually
  exercise the callbacks' `try/except` (not just the happy path): archived
  `HEAD` to a scratch directory outside the repo
  (`git archive HEAD | tar -x`), removed the `try/except` from
  `_on_request_start`/`_on_request_end`/`_on_request_exception` there, and
  reran the same test against that mutated copy with `PYTHONPATH` pointed
  at it -- it failed (`RuntimeError: boom` reaching the caller through
  `session.get(...)`). Scratch directory deleted afterward; nothing in the
  repository was touched by the mutation.
- **Sibling text.** The `433120c` dated entry below keeps its "Reading
  `corrected`" bullet as a record of what that commit actually shipped; this
  entry states the change instead. The reconcile plan's Task 13 spec text
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`)
  updated its "checked and corrected" line to name both counts. The
  resolved F-B23-6 record's reason line ("start, finish and skip") never
  claimed "corrected" and needed no change.

Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-24 - Every provider call is logged, and the release worker says what it did

Side task, no batch tag: implements the reconcile plan's Task 13 (F-B23-6),
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **New module `scrobblescope/api_logging.py`** (leaf: standard library plus
  `aiohttp`): a host-to-provider map (`ws.audioscrobbler.com` -> Last.fm,
  `api.spotify.com`/`accounts.spotify.com` -> Spotify, `api.deezer.com` ->
  Deezer, `musicbrainz.org` -> MusicBrainz; any other host is named by its
  hostname), the `aiohttp.TraceConfig` callbacks that log every call, and a
  per-session tally that logs one INFO summary per called provider on
  close (for example `Spotify: 3 calls in 0.2s -- 2x200, 1x404`). Levels
  per the owner's ruling: 429/5xx at WARNING (naming `Retry-After` when the
  response has one), other non-2xx at INFO, a timeout or connection error
  at WARNING (naming the exception class), 2xx at DEBUG. A line never
  carries the query string -- only the path -- except Last.fm's `method`
  value, named because the bare path (`/2.0/`) does not say which call it
  was. Every callback catches its own errors so a logging failure can never
  fail the request it describes.
- **`utils.create_optimized_session`** attaches a fresh trace config (one
  per session: `aiohttp.ClientSession` freezes whatever `TraceConfig` it is
  given at construction, so a shared module-level one could not accept new
  sessions' callbacks) and wraps the returned session's `close()` so the
  summary logs the first time it closes. Not a `ClientSession` subclass:
  aiohttp 3.14 fires a `DeprecationWarning` at class-definition time for
  any subclass of it (`__init_subclass__` in `aiohttp.client`), which would
  have shown up as a warning on every test that imports this module.
  Rebinding `close` on the session instance reaches the same one place --
  `__aexit__` and every explicit `await session.close()` both call
  `session.close()` -- without subclassing. The function's name, signature
  and return type (an `aiohttp.ClientSession`, used as `async with`) are
  unchanged, so no caller and no existing test needed touching; every
  existing provider test mocks `session.get`, so the hook never fires in
  them.
- **`release_checks.py`'s three worker lines** (INFO, counts only, no
  artist or album names): `run_release_checks` logs its candidate count
  when it starts and, in its `finally` block, the checked and corrected
  counts when it finishes; `enqueue_release_check` logs which setting is
  missing -- `MUSICBRAINZ_ENABLED` or `MUSICBRAINZ_CONTACT` -- when it
  skips.
- **Reading "corrected"** (not defined further by the brief): the finish
  line reports `state["moved_out"]`, the count of results the worker
  actually rewrote in place, not `moved_out + moved_in` -- a moved-in
  candidate is only tallied on the job's stats, never applied to a result
  (`_check_candidate`'s own comment: "move-ins are counted on the job's
  stats, not inserted"). Flagged here in case the owner intended the wider
  count.
- **Privacy proof.** The adversarial test (a query holding
  `api_key=SECRET-KEY` and `artist=Radiohead`) was run red first: with
  `_call_outcome_line` temporarily logging the full URL instead of
  `url.path`, both the pure-function test and the end-to-end
  `TestServer`-backed test failed on the planted leak, then passed again
  once reverted. `tests/services/test_api_logging.py` drives a real
  session from `create_optimized_session()` against a local
  `aiohttp.test_utils.TestServer` (part of `aiohttp`; no new dependency)
  for the end-to-end cases, and tests the host map and the Last.fm
  `method` exception as pure functions of a `yarl.URL` -- the TestServer's
  host is always `127.0.0.1`, which only exercises the unknown-host
  fallback branch. `tests/services/test_release_checks.py` gained four
  tests for the three worker lines and the two skip reasons.
- **Docs.** `.claude/SESSION_CONTEXT.md` Section 3 lists the new module;
  Section 4 gains the `utils -> api_logging` edge (`AGENTS.md`
  Anti-Pattern 2). `FINDINGS.md` resolves F-B23-6 (rotated to
  `docs/history/findings/FINDINGS_ARCHIVE.md` by `--fix`).
- **Not run:** Step 5, the owner's live check with a real Last.fm run under
  `DEBUG_MODE=1` and without it -- it needs the owner's username and API
  quota. Left unticked in the reconcile plan; the owner records the outcome
  here when it runs.

Validation: `pytest -q` -- **1820 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

Forward guidance: the reconcile plan's Task 13 (its whole Stage 4) is done.
Next is the foundation plan's Task 5, per Section 3's order list -- Step 5
above is still owed from the owner.

### 2026-09-24 - Provider call logging joins the reconcile plan as its Task 13

Side task, no batch tag: files F-B23-6 and writes the task that fixes it,
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **Why.** Testing Batch 22's MusicBrainz corrections, the owner still saw
  no MusicBrainz line in the log. At source: the release-check worker logs
  nothing on success, `enqueue_release_check` skips silently without
  `MUSICBRAINZ_CONTACT`, and `musicbrainz.py` and `deezer.py` have no log
  call at all.
- **Owner rulings, 2026-09-24.** Scope: all four providers, plus the three
  release-worker lines the plan's "After this plan" section held (moved into
  the task, with a pointer left behind). Levels: 429 and 5xx at WARNING with
  `Retry-After`, other non-2xx at INFO, timeouts and connection errors at
  WARNING, 2xx at DEBUG, and one INFO summary per provider per session.
- **Recorded:** F-B23-6 (P2, owner-added) in `FINDINGS.md`; a Part C bullet
  in `BATCH23_DEFINITION.md`; the reconcile plan's disposition row, its
  Stage 4 and Task 13, and its stage count and order list; PLAYBOOK Section
  3's order list, which runs Task 13 before the foundation plan's Task 5.
- **Design constraint carried into the task:** no query string in any log
  line, because it carries Last.fm's API key and the search terms the
  definition's Data handling section keeps out of logs. The one exception
  is Last.fm's `method` value.
- Validation: `pytest -q` -- **1802 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-23 - The DOC024 wiring gets a test, and its severity gets stated truly

Side task, no batch tag: fix round 1 on the archive page target task --
add CLI-level test coverage for the `cli.py` splice that actually surfaces
DOC024 to `--check`/`--fix`, and correct two overclaims the original commit
left standing, part of Batch 23 WP-0 Part B. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- **CLI-level test for DOC024** (`tests/test_docsync_cli.py`,
  `TestArchivePageTargetDiagnosticsThroughTheCli`): a real `--check` and
  `--fix` run over a fixture corpus with an unpaginated managed archive over
  the page target asserts `"WARNING DOC024"` in stderr, naming the archive,
  with exit 0. Every prior DOC024 test only called
  `ArchiveStore.page_target_issues` directly, so none of them exercised
  `cli._archive_page_target_issues`'s splice into `_collect_issues`
  (`scripts/docsync/cli.py`) -- the wiring that actually makes DOC024
  visible to an operator. Proved by temporarily removing that splice: both
  new tests failed red (`WARNING DOC024` absent from stderr, exit code
  still 0 -- a silent regression, not a crash), then passed green again
  once restored.
- **Two new unit tests** (`tests/test_docsync_archives.py`): an undated
  entry placed on the writable tail page produces no never-ageing warning
  (the guard clause was previously only inferred, never asserted); and an
  unpaginated archive at exactly `max_lines` does not warn while one line
  over does, measured the same way the check does
  (`len(flattened.splitlines())`).
- **`AGENTS.md`'s DOC001-DOC024 sentence** overclaimed that every code
  "block[s] rather than warn[s]" -- false for DOC024 (100% warning) and for
  DOC023's grandfathered-finding count. Reworded to
  "error-severity ones block, and warnings print without changing the exit
  code," keeping the exact substring `returns typed DOC001-DOC024 issues`
  that `STATED_RANGE_RE` reads, and without enumerating the warning codes
  (the catalogue owns them).
- **`docs/architecture/documentation-tooling.md`**: the catalogue's lead
  paragraph made the same overclaim ("exits 1", full stop) -- corrected to
  "exits 1 on any error-severity [issue]; a warning ... prints and leaves
  the exit code alone." The DOC024 paragraph now states the full
  never-ageing condition (finalized, non-oversized, hot page of a paginated
  archive) instead of dropping the non-oversized/hot qualifiers, and the
  DOC020 cold-rule sentence is anchored to `--as-of` ("more than
  `cold_days` days before `--as-of`") instead of the looser "older than
  `cold_days`".

Validation: `pytest -q` -- **1802 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The archive page target gets a reader

Side task, no batch tag: warn when a managed archive outgrows its page
target or a paginated page can never age, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 4.** `ArchiveStore.page_target_issues`
  (`scripts/docsync/archives.py`) is a new DOC024 diagnostic, warning
  severity only, so `--check` still exits 0. It fires on two conditions: an
  unpaginated (legacy monolith) archive whose logical text has outgrown
  `[archives] max_lines`, naming `--paginate-archives`; and a paginated
  archive's finalized, non-oversized, hot page whose entries are not all
  dated, since `_age` requires every entry on such a page to carry a date
  before the cutoff and a page with even one undated entry can never
  satisfy that rule. `cli.py`'s `_collect_issues` folds these in for every
  path `_managed_archive_paths()` names.
- **The real corpus warns four times, not once**, correcting the brief's
  prediction: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (10451
  lines), `docs/history/findings/FINDINGS_ARCHIVE.md` (2277),
  `docs/history/logs/BATCH22_LOG.md` (989) and
  `docs/history/logs/BATCH21_LOG.md` (750) each exceed the 500-line target
  and are still unpaginated monoliths; `--check` on this worktree exits 0
  and prints all four.
- **`docs/architecture/documentation-tooling.md`** now names DOC024 in the
  renamed DOC001-DOC024 catalogue, and its cold-rule sentence states what
  `_age` actually checks -- every entry on a finalized, non-oversized, hot
  page dated before the cutoff -- rather than "365 days" alone.
- **`AGENTS.md`'s stated `DOC001-DOC023` range** (the sentence
  `test_stated_docsync_range_matches_the_highest_code_raised` reads) was
  bumped to `DOC001-DOC024` in the same commit: adding the `"DOC024"`
  literal to `archives.py` made that test fail, and the smallest fix was
  the one sentence the test reads. The rest of the range wording is left
  to Task 5, which owns it.
- **Live probe** (`/c/ssprobe`, `git archive HEAD` from this worktree,
  deleted after):

  | probe | expected | exit | codes |
  | --- | --- | --- | --- |
  | faithful copy, `--check` | same summary as this worktree | 0 | DOC024 x4 (same paths), root-BATCH warning |
  | red: `--check` (the corpus already carries the four oversized monoliths; nothing further to plant) | fires | 0 | DOC024 x4 |
  | near-miss: `--paginate-archives`, then `--check` | no oversize warning anywhere; `FINDINGS_ARCHIVE_0001.md` (28/28 entries undated) and `FINDINGS_ARCHIVE_0002.md` (9/16 undated) each warn once as never-ageing; no log page warns | 0 | DOC024 x2 |

Validation: `pytest -q` -- **1798 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The owner's rulings land in their findings

Side task, no batch tag: write the owner's 2026-09-23 WP-0 rulings into
FINDINGS.md and docs/design/RECONCILIATION.md, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the reconcile plan's Stage 3 Task 10.** Step 1b recorded
  `F-B21-53` no action (Q10 = b): the light card is delineated by its border,
  not lifted by its fill. `docs/design/README.md` was not edited -- it
  already reads "borders do the work" (line ~107) and "Edge, not elevation"
  (line ~254), and a sweep found no other live elevation claim about cards;
  `static/css/shell.css:566`'s "elevated paper pill" is the theme toggle, not
  a card, and was left alone.
- **Step 2 wrote six no-action records**, each replacing its free-prose
  `Status:` line with the canonical `- [x] **Status:** no action` /
  `**Completed:** 2026-09-23` / reason form: `F-B21-15` (no scheduled
  `GET /heatmap/<username>` route), `F-STYLE-1` and `F-STYLE-2` (guidance
  that cannot become a gate; the docstring convention stays undecided),
  `F-WORKTREE-4` (the owner's 2026-09-21 ruling, written in canonical form),
  `F-B21-24` (Tasks 2-5 shipped; Task 6 runs as Batch 23 WP-7's audit) and
  `F-MAS-2` (absorbed into `F-B21-18`; a pointer line was added under
  "Deferred / future-batch candidates" so the old id stays resolvable).
- **Step 3 re-graded `F-B21-48` and `F-B18-11`** to P2 -- a persistent
  scrobble cache is a feature, not a defect -- and moved both under "P2 --
  Scaling roadmap". The Codex/Copilot session-entry-point item, F-B21-25's
  third "Remaining" item, was filed as the new finding `F-B21-63` (the next
  free `F-B21-` number) under P2; F-B21-25's own "Remaining" paragraph now
  points at it instead of restating it.
- **Step 4 split the partly-ruled findings.** `F-B21-4` closes no action:
  items 1, 2 and 4 are settled (citing `templates/index.html` `.index-grid`,
  RECONCILIATION's loading-signal override, and RECONCILIATION section 16),
  and item 3 folds into Batch 23 WP-6 (Q13 = a). `F-B21-19` closes no
  action per Q12 = a: `docs/design/RECONCILIATION.md` section 1 gained an
  owner-approved override row for the width-driven mobile heatmap grid, and
  day detail (hover reveals what was played) is named a future feature since
  the payload holds only `daily_counts`. `F-DOCSYNC-6` and `F-WORKTREE-3`
  each gained a dated line: the boundary/ancestry items are no action, the
  mechanical bugs stay open for the control-plane plan. RECONCILIATION
  section 9's `F-B21-4` bullet and section 7's lead-in were reworded so
  neither sibling claim still reads as pending.
- **No test changed.** The task is documentation only; the test count stays
  at the baseline.

Validation: `pytest -q` -- **1793 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

Forward guidance: the reconcile plan's Stage 3 Task 10 (Part B) has landed,
completing every task in
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`. The
next step is the foundation plan's Tasks 4-10, per Section 3's order list.

### 2026-09-23 - The release-window rule gets one owner

Side task, no batch tag: fixes F-B23-5, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Task 12 of the reconcile plan**
  (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`) is
  done. `scrobblescope/domain.py` gains `release_window(release_scope, year,
  decade=None, release_year=None)`, which returns the inclusive `(first,
  last)` years a scope accepts, `None` when every year qualifies, and raises
  `ValueError` when a companion parameter is present but unparseable.
  `domain._matches_release_criteria` (the album filter) and
  `release_checks._window_end` (the correction worker) both derive from it
  now instead of each restating the same scope table; neither's name,
  signature or import path changed, so every test that used them passed
  unmodified.
- **The two divergences named in the finding are kept, per owner ruling
  2026-09-23 (KEEP PARITY).** An unparseable `decade` (the route does not
  validate it) still makes `_matches_release_criteria` return `False` and
  `_window_end` return `None`; the only change is that the warning now
  names the bad decade instead of the release date. `_window_end` still
  accepts `year` as a string; the filter is still only ever called with an
  `int`.
- **Parity tests pin both consumers' outputs first.**
  `tests/services/test_orchestrator_helpers.py` gains
  `test_matches_release_criteria_parity_before_release_window`, a
  parametrized test covering the four bounded scopes plus every divergence
  the finding names; `tests/services/test_release_checks.py` gains
  `test_window_end_parity_before_release_window`, the same coverage for
  `_window_end`. Both were checked against the pre-refactor functions (the
  finding's own known-bad decade warning reproduced) before the refactor
  landed, and both still pass against the derived code -- the net held.
  `test_window_end_per_release_scope` and
  `test_window_end_returns_none_on_unusable_inputs` pass unmodified.
- **Direct coverage for `release_window`** also lands in
  `tests/services/test_orchestrator_helpers.py`:
  `test_release_window_per_scope` (the four bounded scopes),
  `test_release_window_unbounded_returns_none` (`"all"`, an unrecognized
  scope, and a falsy companion) and
  `test_release_window_unparseable_decade_raises` (the adversarial case).
- **Deviation from the brief.** The brief's Files list names only
  `tests/services/test_orchestrator_helpers.py` and
  `tests/services/test_release_checks.py` as test files to touch, append
  only, and does not mention `tests/test_domain.py`. `release_window`'s own
  tests (Step 2) are therefore appended to
  `tests/services/test_orchestrator_helpers.py` -- the file that already
  hosts `_matches_release_criteria`'s adversarial coverage -- rather than
  added to a new or different test module.
- **Documents.** `.claude/SESSION_CONTEXT.md` Section 3's `domain.py`
  summary line now lists all five module-level functions:
  `normalize_name, format_album_key, normalize_track_name,
  _matches_release_criteria, release_window`.
  `docs/architecture/runtime-system.md`'s runtime-system prose named
  `_matches_release_criteria` as what the worker and the album filter both
  read from `domain.py`; it now names `release_window`, since that is the
  rule's one owner. A sweep for `_window_end` and "release window" across
  live prose found nothing else naming the old, two-copy shape.
- **F-B23-5 is resolved.** `domain.release_window` is the rule's one
  owner; the album filter and the worker's window end both derive from it.
- **Forward guidance:** Stage 2 is complete. Next is Stage 3, this plan's
  Task 10.

Validation: `pytest -q` -- **1793 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.
