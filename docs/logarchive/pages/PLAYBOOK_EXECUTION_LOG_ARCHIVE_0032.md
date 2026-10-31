<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0032

### 2026-10-23 - Plan UI consistency round 2

Side task, no batch tag: committing the plan for UI consistency round 2 and pointing Section 3 at it, on `feat/ui-consistency-round-2`, a branch off `main`.

Owner intent (2026-10-23): "the focus will be on folding in S2 and L1 with the uncommited current changes. Live work is to be deferred to a different session for later." On the Orpheus Pro change: "I took a look with the Orpheus Pro changes and they are good ... Likewise with the Results and error pages so no issues." And: "I would suggest having a draft PR with the same PR body as per the template and land commits there at the moment."

What changed: `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md` holds the plan: Task 1 makes Orpheus Pro the display serif (I1), Task 2 sets the Results stat values in the figure face (S1), Task 3 rewrites the heatmap preview and lede to match the grid (H2, H4), Task 4 drops the arrows from the two unmatched-report links (S2), Task 5 drops the redundant redirect line from a finished run (L1). The first three apply the changes the owner accepted in live mode on 2026-10-22, each only after its new tests are proven red. The plan carries the controller's rulings on its brief review (the unmatched-link test scoped past the site header, the `_Page` fake taught the stat read, a pure headline-font judge, and others). Section 3's "Before WP-1" bullet now says the pre-Batch-23 side-task PR and the Playwright package cache are done and that round 2 runs now; the other backlog items wait for a later live session.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2969 passed**.

### 2026-10-22 - F-B23-57 says what a cancelled run leaves behind

Side task, no batch tag: correcting one sentence of the archived F-B23-57 record, on `ci/playwright-apt-cache`, a branch off `main`.

Owner intent: the finding must not promise more than the cache delivers.

What changed: the "Not covered" text of F-B23-57 in `docs/history/findings/FINDINGS_ARCHIVE.md` said a cache miss on a slow mirror waits once per runner image or dependency change. The save step runs after the install, so a run cancelled inside the install saves nothing and the next run waits again; the sentence now says so. Nothing else in the record or the archive changed.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2969 passed**.

### 2026-10-22 - CI keeps Playwright's Ubuntu packages between runs

Side task, no batch tag: caching the Ubuntu packages Playwright's browser install downloads, on `ci/playwright-apt-cache`, a branch off `main`.

Owner intent: a slow Ubuntu mirror must not stall the Quality Gate again, so the packages are kept in the Actions cache.

What changed: `.github/workflows/test.yml` gains three steps around "Install Playwright browser": "Read the runner image version" (for the cache key), "Restore Playwright system packages" (`actions/cache/restore@v6`) before it and "Save Playwright system packages" (`actions/cache/save@v6`, only on an exact-key miss) right after it, so a later failed step cannot prevent the save. The install step copies the cached packages into apt's archive directory first and back after, then runs `apt-get autoclean` to bound the cache. `tests/test_ci_workflows.py` gains a structural test of the step order, ids, key, paths, the save condition and the two copies, proven red against the unchanged workflow and against nine planted defects. F-B23-57 is filed as resolved in `docs/agents/FINDINGS.md`; its not-covered paragraph names a cache miss on a slow mirror, a newer package re-downloading until the key changes, and the pull-request cache scope.

Deviations: none. Edited existing tests: none (one test added to `tests/test_ci_workflows.py`).

Validation: `pytest -q` -- **2969 passed**.

### 2026-10-22 - Plan the CI package cache

Side task, no batch tag: planning a CI cache for Playwright's Ubuntu packages, on `ci/playwright-apt-cache`, a branch off `main`.

Owner intent: a slow Ubuntu mirror must not stall the Quality Gate again ("Yes, on the lasting fix. Worth doing"), so the packages `playwright install --with-deps` downloads are to be kept in the Actions cache.

What changed: the plan `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md` is committed, and Section 3 names the branch and plan in the "Before WP-1" bullet. The plan carries every fix from its review: the cache is restored before the install and saved by its own step right after it (so a failed or cancelled later step cannot stop it filling), and its structural test asserts the direction of the seed and the copy-back on non-comment lines, proven against nine planted defects in scratch.

Deviations: the plan uses `actions/cache/restore` and `actions/cache/save`, sub-actions of the `actions/cache@v6` already pinned (controller ruling). Edited existing tests: none.

Validation: `pytest -q` -- **2968 passed**.

### 2026-10-22 - Two of the new review findings say what the code does

Side task, no batch tag: correcting two claims in the new review findings, on `docs/architecture-review-2026-10-21`, a branch cut from the head of `fix/job-endpoint-modes`.

Owner intent: the findings must say what the code does, so the two claims the review of the previous commit found wrong are corrected.

What changed: `docs/agents/FINDINGS.md` only. F-B23-51 no longer says a Deezer outage hides the Last.fm page-loss detail on the loading page (the Deezer writer is guarded by a read of the existing value; only the Spotify writers overwrite it there, while Results keeps just the generic Last.fm sentence whenever any provider sentence is present). F-B23-52 no longer says the three writers use "the same keys": it now lists the keys all three share and the keys each adds, including that the Deezer literal also carries `album_image` and `spotify_id` (both None), as read from `partition_albums_by_threshold`, `_results.py` and `_deezer_fallback.py`.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2968 passed**.

### 2026-10-22 - The 2026-10-21 architecture review is tracked with one finding per open item

Side task, no batch tag: tracking the architecture review report and filing its open items as findings, on `docs/architecture-review-2026-10-21`, a branch cut from the head of `fix/job-endpoint-modes` (PR 3 of three stacked side-task PRs).

Owner intent: the review's open items must not live only in an untracked page, so the report is committed beside the other reports and each carried-over candidate becomes a finding with a timing.

What changed: `docs/history/reports/architecture-review-2026-10-21.html` is a byte-for-byte copy (`cmp` clean, 57166 bytes) of the owner's untracked file; the original stays where it was. `docs/agents/FINDINGS.md` gains F-B23-51 to F-B23-56 under "P2 -- Scaling roadmap", all open P2: 51 a Last.fm page-loss detail lost when a provider also fails (candidate 1, D2), 52 the unmatched-album record built as a dict literal in three places (candidate 2), 53 the mode rule written inline at five call sites (candidate 3), 54 the results page's two keyword blocks (candidate 4), 55 the orchestrator facade's re-export block (candidate 5), 56 three browser pollers (candidate 6). Each was re-checked at e94b6e8 by `git grep`. Changes since the triage at eb0db9e: `partial_data_warning` has six writers, one guarded, so "four of five unguarded" is five of six; the five mode checks are `_get_validated_job_context`, `_latest_heatmap_job`, `release_checks`, `heatmap_data` and `unmatched_data`, two of them added by F-B23-50; `_render_results_page` now carries `play_stats` in both keyword blocks (PR #262); `orchestrator/__init__.py` is 725 lines, not 738 (PR #261); `heatmap.js` polling is unchanged, so F-B23-56 has no conflict to wait for. F-B23-50 is closed by the previous PR and F-B23-49 stays unused.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2968 passed**.

### 2026-10-22 - Two job endpoints refuse the other mode's job

Side task, no batch tag: making `/heatmap_data` and `/api/unmatched` refuse a job of the other mode, on `fix/job-endpoint-modes`, a branch cut from the head of `fix/pre-batch23-side-tasks` (PR 2 of three stacked side-task PRs).

Owner intent: every job endpoint answers a job that is not its own the way it answers a missing job, and "a wrong implementation must not pass".

What changed: `heatmap_data` spreads `ctx["results"]` into its answer, and an album job's results are a list of rows, so a finished album job id raised `TypeError` and answered 500 (a running one answered 202, a failed one 200); `unmatched_data` answered a heatmap job with 200 and a report (F-B23-50, 2026-10-21 architecture review D1 and D3). `heatmap_data` now returns the missing-job 404 unless the job's mode is heatmap; `unmatched_data` reads `jobs.context` once and returns its missing-job 404 unless the job exists and its mode is album. Both are allowlists, so a job of any third mode is refused. `/progress` stays shared by both modes (`static/js/heatmap.js` polls it). F-B23-50 is filed as resolved. F-B22-3's body named `jobs.unmatched` as an endpoint read; it now names `jobs.progress` and `jobs.context`.

Deviations: the plan's planted defect (a) predicted `running` gets 202 when the mode check moves after the results branch; it passes (404) instead, and the defect is caught by `finished` and `failed`. Beyond the plan, per the code review: `test_unmatched_api_unknown_job` (the rewritten unknown-job branch had no test) and one other-mode case per endpoint (the guards are allowlists). Edited existing tests: none. Tests added: `test_heatmap_data_refuses_an_album_job` (running, finished, failed), `test_heatmap_data_refuses_a_job_of_another_mode`, `test_unmatched_api_refuses_a_heatmap_job`, `test_unmatched_api_unknown_job`, `test_unmatched_api_refuses_a_job_of_another_mode`.

Mutations, each proven red then reverted: mode check after the results branch (`finished` TypeError, `failed` 200 not 404); results-type guard instead of the mode check (`running`, `finished`, `failed` fail); `unmatched_data` mode clause deleted (heatmap job gets 200); `job_context is None or` removed (the unknown job raises AttributeError); `unmatched_data` denylist `== MODE_HEATMAP` (the other-mode job gets 200); `heatmap_data` denylist `== MODE_ALBUM` (the other-mode job gets 200). The frontend gate passed.

Validation: `pytest -q` -- **2968 passed**.

### 2026-10-22 - The coverless-wash route test no longer reads the clock

Side task, no batch tag: making a flaky route test independent of the clock, on `fix/job-endpoint-modes`, a branch cut from the head of `fix/pre-batch23-side-tasks` (PR 2 of three stacked side-task PRs).

Owner intent: a test that fails now and then with no defect in the code teaches the team to ignore red, and "a false green is worse than a true red", so the fix must not weaken what the test guards.

What changed: `test_unmatched_view_coverless_rows_wear_their_albums_wash` asserted the two `POST /unmatched_view` pages byte-identical, but `templates/base.html` renders a CSRF meta token that Flask-WTF signs with a timestamp, so renders a second apart differ (PR #262 CI, 2026-10-21; filed and closed as F-B23-48). The test now also asserts the second status, then masks each page's own token (read from its `csrf-token` meta tag, every occurrence replaced by a fixed placeholder) and compares the two pages whole, so row order or any other render nondeterminism still fails. The per-row expected-wash assertions are unchanged. The docstring's THEN clause and Mutation paragraph are updated.

Deviations: the plan's block compared only each row's artwork classes; the code review noted that lets row-order nondeterminism pass, and the controller ruled for the whole-page comparison with only the token masked. Edited existing tests: `test_unmatched_view_coverless_rows_wear_their_albums_wash` (the only edit).

Mutations, each proven red then reverted: reversing the order of the unmatched reasons on every second render fails; `cover_wash_filter` drawing from `random.randrange(6)` fails; leaving the token unmasked fails under a patched `TimestampSigner.get_timestamp` that signs a different second per render, while the masked test passes under that same patch.

Validation: `pytest -q` -- **2961 passed**.

### 2026-10-22 - Log lines reach stdout as UTF-8

Side task, no batch tag: writing stdout as UTF-8 like stderr, on `fix/pre-batch23-side-tasks`, a branch off `main`.

Owner intent: the production log stream must never lose a line because of a listener's artist name.

What changed: the stream setup block in `app.py` reconfigured only `sys.stderr` to UTF-8, while `logging.StreamHandler(sys.stdout)` is the production log channel (the file handler is ephemeral on Fly.io). It now loops over `(sys.stdout, sys.stderr)`. Why: when stdout is a pipe or a file (a redirected log, a process manager) Python uses the locale's code page, where a non-Latin artist name raised `UnicodeEncodeError` inside logging and the line was lost. The plan's wording blamed a Windows console; since PEP 528 a real console writes UTF-8, so the `app.py` comment and the test name say pipe or file under a legacy code page. `tests/test_app_factory.py` gains `test_a_log_line_reaches_stdout_whole_when_its_encoding_is_legacy`, which reuses `_import_app_in_child` with `PYTHONIOENCODING=cp1252`.

Deviations: the test goes beyond the plan's block (owner rule: a wrong implementation must not pass): the child also writes the probe to `sys.stderr`, and the test asserts it arrives intact there, so the stderr half of the fix is pinned too; the test is renamed from `..._on_a_narrow_console` to match the corrected description. Edited existing tests: none.

Mutations, each proven red then reverted: a loop over `(sys.stderr,)` only fails (the probe is missing from stdout, with a Logging error); a loop over `(sys.stdout,)` only fails (the probe is missing from stderr); `reconfigure(errors="replace")` with no encoding fails (the probe arrives as `?`). The frontend gate passed.

Validation: `pytest -q` -- **2961 passed**.

### 2026-10-22 - Importing the app no longer runs a shell command

Side task, no batch tag: removing the `os.system("")` call from `app.py`, on `fix/pre-batch23-side-tasks`, a branch off `main`.

Owner intent: the owner ruled against adding colour to the console output, so nothing may keep a call whose only purpose was to enable it.

What changed: `app.py` loses the `os.system("")` call and its `# Enable ANSI escape codes on Windows cmd` comment (`import os` stays; it is still used). Why: nothing in `app.py` or `scrobblescope/` emits ANSI escape codes, so the call enabled nothing, and on Linux it spawned `/bin/sh` at every first import. `tests/test_app_factory.py` gains `_import_app_in_child(tmp_path, *, prelude="", epilogue="", extra_env=None)` (imports `app` in a fresh interpreter in `tmp_path` with `DEBUG_MODE=1`; Task 4 reuses it) and `test_importing_the_app_runs_no_shell_command`, which stubs `os.system` and records every `subprocess.Popen` construction in the child, then asserts both lists are empty. Two controller strengthenings of the plan's text after code review: (1) the plan's test stubbed only `os.system`, so `subprocess.run("", shell=True)` and `os.popen("")` left it green; recording `Popen` (which `subprocess.run`, `subprocess.call` and `os.popen` all construct) makes the test name true; (2) the helper prepends `REPO_ROOT` to an inherited `PYTHONPATH` (`os.pathsep.join`) instead of replacing it, with its signature unchanged.

Deviations: `ruff format` collapsed the plan's `prelude` string layout; the Popen recording and the `PYTHONPATH` join go beyond the plan's test block. Edited existing tests: none.

Mutations, each proven red then reverted: `os.system("")` re-added -> `SYSTEM_CALLS ['']`, test fails; `subprocess.run("", shell=True)` added -> `POPEN_CALLS [('',)]`, fails; `os.popen("").close()` added -> `POPEN_CALLS [('',)]`, fails. Test-first red against the unfixed `app.py`: `SHELL_CALLS ['']` (code phase). The frontend gate passed (48 checks, 78 runs).

Validation: `pytest -q` -- **2960 passed**.

### 2026-10-22 - The Last.fm pre-check timeout must be a positive number

Side task, no batch tag: validating `LASTFM_PRECHECK_TIMEOUT_SECONDS` at startup, on `fix/pre-batch23-side-tasks`, a branch off `main`.

Owner intent: a bad timeout value should stop startup with the variable's name, not ship a form that can never pass or never stops waiting.

What changed: `scrobblescope/config.py` gains `_positive_seconds(name, default)`, and `LASTFM_PRECHECK_TIMEOUT_SECONDS` is read through it. A blank or unset variable takes the default 5; zero, a negative number, `nan`, `inf` or text that is not a number raises `ValueError` naming the variable and the value at import. Why: zero makes every pre-check time out at once, so every form submission is refused "try again", and `nan` never compares greater than the elapsed time while `inf` removes the bound. `.env.example` documents the variable; SESSION_CONTEXT's Key runtime facts bullet states the rule. New `tests/test_config.py` (11 tests): the unset, blank and fractional-override cases, the default the caller passes (a `"7"` default, so a function that hard-codes 5 fails), six refused values each checked for the variable's name and the quoted value, and a child-process import test that checks the module constant itself refuses `0` (stderr names the variable and `ValueError`) and accepts `0.25`. The code-phase review's two minor findings were folded into these new tests (the caller-default test and the `ValueError` assertion); its third, a child-process check of `nan` and `inf`, is deferred because the wiring is shared with the `0` case. Test-module count 100 -> 101.

Deviations: `ruff format` wrapped the constant's assignment over three lines; the two test additions above go beyond the plan's test block. Edited existing tests: none (the module is new).

Mutations, each proven red then reverted: `value <= 0` -> `value < 0` fails the `0` case and the child-process test; dropping `not math.isfinite(value) or` fails the `nan`, `inf` and `five` cases; the constant back to a bare `float(os.getenv(...))` fails the child-process test; `or default` -> `or "5"` fails the caller-default test.

Validation: `pytest -q` -- **2959 passed**.

### 2026-10-22 - F-B22-3 moves to Batch 23 WP-3

Side task, no batch tag: re-pointing finding F-B22-3 to Batch 23 WP-3, on `fix/pre-batch23-side-tasks`, a branch off `main`.

Owner intent: ruling 2026-10-21 (Q1) -- Last.fm jobs keep the job ID as their capability, and export jobs, which hold an uploaded private history, are bound to the session that created them.

What changed: `docs/agents/FINDINGS.md` F-B22-3 gains the ruling paragraph and a status line that names WP-3 (still open, P2; its shape is unchanged). The `release_checks` docstring in `scrobblescope/routes/api.py` now states the ruling instead of calling it an open question (docstring only, no code change). `BATCH23_DEFINITION.md` gets a `Scope amended 2026-10-21` header line and a WP-3 checklist item, "Export jobs belong to their session", with its acceptance. No work package is added. This lets WP-3 implement the binding without re-asking the owner.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2948 passed**.

### 2026-10-22 - Plan the pre-Batch-23 side tasks

Side task, no batch tag: the plan for the pre-Batch-23 side-task PR, on `fix/pre-batch23-side-tasks`, a branch off `main`.

Owner intent: "Cheap fixes first -- anything else that comes before the scope in the tranche should be filed as a potential finding/candidate. Goal is to finish the tranch and avoid scope creep"; on 2026-10-22 the side-task PR runs next and the Batch 23 WP-0 close-out runs "After the tranche, before WP-1".

What changed: `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md` is committed with every fix its brief review asked for (one Important, twelve Minor: the Task 0 staging order for DOC001, corrected predictions for the planted defects, the archives in the staging lists, the canonical open-finding record, a self-contained Task 5 proof, ruff-formatted code blocks, and the frontend gate before Tasks 3, 4 and 6). PLAYBOOK Section 3 names the PR in the "Before WP-1" bullet and says the WP-0 close-out runs after the tranche, before WP-1; "Next action: WP-0 is next." is unchanged because WP-0 is still the next work package.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2948 passed**.

### 2026-10-21 - The PR template branch takes main after PRs #5 and #6

Side task, no batch tag: merge of `origin/main` (3ddc650, PRs #261 and #262) into `chore/pr-template`, on `chore/pr-template`, a branch off `main`.

Owner intent: PR #263 merges into a `main` that already carries PRs #5 and #6, with its bookkeeping true against them.

What changed: one merge commit (`git merge --no-ff`). PRs #5 and #6 bring the album cache, the plays module and the statistics module with their tests and docs; this branch's own change (the PR template's State and Validation sections, AGENTS.md's no-attribution rule for PR bodies) is untouched and still applies. Conflicts: PLAYBOOK Section 4 and the Section 4 logarchive only. Section 4 keeps this branch's two entries and main's four, newest first after the marker line; the `Make the #4 docs` entry, which main rotated into the logarchive, stays there once, so its Section 4 heading and stray Validation line are dropped. The logarchive keeps main's additions, this branch having added none. Measured count 2948 across 100 test modules, equal to main's: this branch adds no test.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2948 passed**.

### 2026-10-21 - No attribution line in a PR body either

Side task, no batch tag: AGENTS.md's co-author prohibition extended to pull request bodies, on `chore/pr-template`, a branch off `main`.

Owner intent: "make sure no attribution trailers are in any PR body".

What changed: AGENTS.md Commit Rules "Co-author prohibition" now forbids any attribution line (such as a "Generated with" footer) in a commit message or a pull request body, whatever a harness suggests, and points a PR body at `.github/PULL_REQUEST_TEMPLATE.md`. The bold label is unchanged, so the docsync citations and `tests/test_docsync_declarations.py` still find it. The sweeper found no other live copy of the rule: the cloud-kit implementer files cover implementer commits only and stay.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2847 passed**.

### 2026-10-21 - The PR template asks for state and validation

Side task, no batch tag: the PR template gains State and Validation sections, on `chore/pr-template`, a branch off `main`.

Owner intent: "The state format is good, I think the State section and table is worth incorporating into the pull request template which exists in this repo."

What changed: `.github/PULL_REQUEST_TEMPLATE.md` now runs Summary (names the plan file for a tranche or batch PR), State (a Task / What / Commits / Review table for a multi-task PR, kept true at every push), Validation at this head (head SHA, gates and results, CI run), the unchanged six-box Checklist with a note to tick gate boxes only once CI and the final gate pass at the head that leaves draft, and a closing comment forbidding attribution lines. The comments are HTML so GitHub hides them. Template only, so a PR opened from it starts with the right shape.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2847 passed**.

### 2026-10-21 - The statistics module branch takes main after PR #5

Side task, no batch tag: merge of `origin/main` (d1c775d, PR #261, one album-metadata encoding) into `refactor/statistics-module`, on `refactor/statistics-module`, a branch off `main`.

Owner intent: PR #6 merges into a `main` that already carries PR #5, with both PRs' bookkeeping and docs true for the merged tree.

What changed: one merge commit (`git merge --no-ff`). PR #5 brings `AlbumCache` / `open_album_cache` in `cache.py`, `AlbumMetadata.from_row`, the slimmed `orchestrator/_cache.py`, `tests/fake_postgres.py`, `tests/test_album_cache_parity.py` and the metadata-encoding plan; PR #6 brings `listening_stats.py` and its importers. No code or test file conflicted (the two PRs touched different code files). Conflicts were in bookkeeping only. PLAYBOOK Section 3, "Before WP-1" bullet: PR #5's wording is the base, and it now also says the statistics module is done (PR #6, branch `refactor/statistics-module`, plan `docs/superpowers/plans/2026-10-20-statistics-module.md`), so no seam of the four remains; the job persistence and design sentences are kept. PLAYBOOK Section 4: every dated entry of both sides is kept whole, then `--fix` rotated the oldest five into the logarchive as it does on every commit (no entry dropped). `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`: both sides' rotated entries kept, each with its own Validation line. `.claude/SESSION_CONTEXT.md`, `docs/agents/FINDINGS.md`, `config/docsync.toml`: the count lines (Tests row, Section 6 title, status line, FINDINGS header, `[test_count]` pin) were re-measured, not hand-merged; the module count is 100 (`git ls-files tests | grep -c '/test_[^/]*\.py$'`, PR #5 adds `test_album_cache_parity.py`). The module-list and dependency-graph lines of both sides merged cleanly and were re-checked against the imports of `cache.py`, `orchestrator/__init__.py`, `orchestrator/_cache.py` and `heatmap.py`. `BATCH23_DEFINITION.md`, `FINDINGS_ARCHIVE.md` and the architecture diagrams merged without conflict (union of both PRs' edits).

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2948 passed**.

### 2026-10-21 - Keep the WP-6 streak bullet true

Side task, no batch tag: reword WP-6's heatmap checklist bullet in `BATCH23_DEFINITION.md` so it agrees with the "The module exists" paragraph, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the definition must not list as future work what the statistics module already does.

What changed: the bullet "Heatmap: longest and current streak ..." named the current streak and "one pure helper" as work to do, while the paragraph added in the WP-6 amendment says both exist. It now lists the longest streak, busiest weekday and busiest hour as WP-6's, added to `listening_stats.py`, and says the current streak and the helper already exist. Nothing else in the definition changed.

Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - Say what the #6 tests and diagram prove

Side task, no batch tag: make a test docstring, a sequence diagram and two module docstrings say only what is true, on `refactor/statistics-module`, a branch off `main`.

Owner intent: nothing the close-out wrote should claim more than was proven or draw a step out of order.

What changed: `test_scrobbles_stat_prints_the_figures_it_is_handed` now says its mutation was planted in `data-plays-listed` and in `data-plays-matched` and that the visible Scrobbles text is asserted but was not planted; the dated entry "A test pins that the page prints the Scrobbles figure it is handed" is point-in-time and unedited, but its Proof names the same two attributes only, so the visible text was never mutation-tested. `docs/architecture/heatmap-sequence.md` drew `heatmap_statistics` before the local `total`, `max_count` and `active_days` step, while `heatmap.py` runs the local step first; the two messages swap places (lines 83 and 85 trade). `listening_stats.py`'s module docstring now also names the four `scripts/dev/_frontend_gate_*` importers, and `heatmap.py`'s module docstring says the job result carries the statistics and not only the daily counts.

Recorded, no change: the test pins the filled render block only, the no-matches block also passes `play_stats` and is not pinned (brief asked for one test); the `HEATMAP_WINDOW_DAYS` comment in `heatmap.py` keeps one over-long line, outside this brief.

Deviations: none. Edited existing tests: `test_scrobbles_stat_prints_the_figures_it_is_handed` (docstring only). Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - WP-6 builds on the statistics module

Side task, no batch tag: amend WP-6 in `BATCH23_DEFINITION.md` for the statistics module and mark that seam done in Section 3, on `refactor/statistics-module`, a branch off `main`.

Owner intent: WP-6 must start from the module that exists, not plan to create it.

What changed: WP-6 gains a paragraph after "Statistics contract before implementation" saying `scrobblescope/listening_stats.py` is the pure helper WP-6 extends, what it already computes and publishes with a population, that the JS and template render published values and compute none, and that include-unmatched albums count in plays listed and in no duration figure. Section 3's "Before WP-1" bullet now says the statistics module is done (PR #6, branch and plan named) and one seam, album-metadata encoding, remains; the "under way" sentence is deleted. Nothing else in Section 3 changed. The Batch 23 row of `.claude/SESSION_CONTEXT.md` names no tranche PR, so it is unchanged.

Reconciled: PR #4's WP-2 amendment (the parser yields `plays.Play`; `plays.aggregate_albums` and `plays.aggregate_daily_counts` feed both sources) makes no sentence of the new paragraph untrue, so it needed no correction.

Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - Make the #6 docs true for the merge

Side task, no batch tag: close out PR #6 by making its diagram and plan text true, on `refactor/statistics-module`, a branch off `main`.

Owner intent: nothing the statistics module touches should describe a step or a name that is no longer so.

What changed: `docs/architecture/heatmap-sequence.md` drew `heatmap_statistics` twice (lines 83 and 85); it is now one `Heatmap->>Heatmap` message carrying its figures, and the local step Task 4 removed (`total`, `max_count` and `active_days` computed in `heatmap.py`, `total_scrobbles` and `active_days` recorded as stats) is drawn again as one message after the Note. In the statistics-module plan, "Albums control" is now "Unmatched albums control" (line 22) and the worktree `C:/ssw/stm` is `C:/ssw/st` (line 50), as constraints L2 asks. `top-albums-sequence.md` is left to the documentation PR.

Recorded, no change: the UTC-day test's remaining gap (a host-zone read that skips `astimezone`) has no code path, because the only timestamp-to-date reads are `listening_stats.utc_date` (`astimezone(UTC)`) and `plays.py`'s `play.played_at.date()`, and `Play` requires a UTC `played_at`. Task 5's Minor 2 (a missing `data-plays-*` attribute would render NaN) needs no guard, because the server always renders both. The `config/docsync.toml` window comment stays: the daily average still divides by `len(daily_counts)`, the zero-filled `HEATMAP_WINDOW_DAYS` window, so it is true.

Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - Place the cache close where the code closes it

Side task, no batch tag: two doc truths from the close-out review (SESSION_CONTEXT Section 5, PLAYBOOK Section 3), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: docs follow the code.

What changed and why: SESSION_CONTEXT Section 5 put the `async with open_album_cache()` close under phase 4, but in `process_albums` the block ends after phase 4b (the original-release lookup) and before phase 5, so item 4 now says the persist is followed by the original-release lookup and the connection closes after that (review Minor 4). In PLAYBOOK Section 3 the "Before WP-1" bullet had one 83-column line; it is re-wrapped near 80 columns, words unchanged (review Minor 2). Review Minor 1 is recorded here and not repaired: the body of `c006554` said "a test docstring" without naming the file, which is `tests/services/test_orchestrator_process_albums.py`; history is not rewritten.

Deviations: none.

Edited existing tests: none.

Validation: `pytest -q` -- **2897 passed**.

### 2026-10-21 - Pin the classic link when external_urls is null

Side task, no batch tag: pin the null `external_urls` guard of `album_metadata_from_details` with a test, on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: a claim in a document is backed by a test that fails without it.

What changed and why: `dfd22dc`'s fallback also guards a payload whose `external_urls` is `null` (`(details.get("external_urls") or {})`) and its entry says "missing or null", but no case passed `{"external_urls": None}`; the old `None` parameter became `details = {}`, the missing key. The parametrized test now takes the whole details payload and gains a `null-object` case (expected: `https://open.spotify.com/album/sp3`). With the guard replaced by `details.get("external_urls", {})` the new case fails with `AttributeError: 'NoneType' object has no attribute 'get'` and the other five pass; restored, all six pass. Review of close-out, Minor 3. No production code changed.

Deviations: none.

Edited existing tests: `test_album_metadata_from_details_keeps_the_classic_link` in `tests/services/test_spotify_service.py` (parameters now carry the details payload; 5 cases became 6).

Validation: `pytest -q` -- **2897 passed**.

### 2026-10-21 - Make the #5 docs true for the merge

Side task, no batch tag: close-out of PR #5, making the docs true for the merge (PLAYBOOK Section 3, the plan's citations, a test docstring, two architecture files, F-B23-47), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: docs follow the code, and nothing a reader needs lives only in an untracked workspace.

What changed and why: PLAYBOOK Section 3's "Before WP-1" bullet now says one album-metadata encoding is done (PR #5) and only the statistics module remains. The committed plan cited the untracked `constraints.md` R9 in three places (the global constraint, Step 6, the mutation step); the citation is dropped and the rule stays inline, with no other plan text changed. The docstring of `test_process_albums_conn_always_closed` said the connection closes "in the finally block"; Task 4 moved the close into `open_album_cache`'s context manager, so it now says so. `top-albums-sequence.md` drew the stale-row cleanup as a separate `Orch->>Cache` call, but `AlbumCache.lookup` runs `cleanup_stale_metadata` itself, so that one message is now `Cache->>Cache: Clean stale rows inside lookup (both lookup outcomes)` (line 111, for the controller to render). One prose line in `runtime-system.md` was re-wrapped. F-B23-47 is filed: `test_job_threads_can_share_the_token_state_dict_without_error` failed once beside other test files in Task 2's run, a switch-interval thread race that is flaky by design and unrelated to the diff (open, P3, no fix in this PR).

Plan-mandated defects, recorded here and not edited in the plan: the brief's mutation row 7 named `test_a_failing_cache_statement_never_fails_the_search[write]`, which checks only `db_cache_warning` and cannot catch the plant, so Task 4 added `test_a_failed_persist_is_reported_as_a_warning_not_as_persisted_rows`; and Step 7's parity-proof command diffed against 2847cd5, before Task 1's fix round c6769b7, so it reported differences in `tests/fake_postgres.py` that came from c6769b7, not from Task 3 or 4.

Deviations: `top-albums-sequence.md` line 101's Note ("No lookup, cleanup, or persistence") is left as drawn, since the brief limits the redraw to the one message.

Edited existing tests: `tests/services/test_orchestrator_process_albums.py` (one docstring line, no code).

Validation: `pytest -q` -- **2896 passed**.

### 2026-10-21 - A live Spotify album keeps its link when Spotify sends none

Side task, no batch tag: restore the classic album link for a Spotify album whose details carry no link (`album_metadata_from_details`), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: a refactor PR must not change behaviour nobody asked it to change.

What changed and why: before this PR a Spotify album whose details payload had `external_urls.spotify` null or `""` still got `https://open.spotify.com/album/<id>`, rebuilt by `_results._album_url`. Task 3 deleted that rebuild, so such an album got `album_url` null (task 3 review, Minor 1). `album_metadata_from_details` now falls back to the canonical URL when `external_urls` is missing or null, or when `spotify` is missing, null or empty; a link Spotify sends is kept as sent.

Deviations: none.

Edited existing tests: none. Added `test_album_metadata_from_details_keeps_the_classic_link` (5 cases) in `tests/services/test_spotify_service.py`; with the fallback removed, 4 of the 5 fail, and with it restored all pass.

Validation: `pytest -q` -- **2896 passed**.

### 2026-10-21 - A test pins that the page prints the Scrobbles figure it is handed

Side task, no batch tag: pin that `results.html` prints the Scrobbles figures the route hands it, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the page must show the figure Python decided, and a template that quietly re-adds the rows must fail a test.

What changed: `data` and `play_stats` both come from `filtered_results`, so a template summing `data` for the two `data-plays-*` attributes passed every earlier route test. `test_scrobbles_stat_prints_the_figures_it_is_handed` patches `album_play_statistics` to return 777 listed and 555 matched over one 50-play row and asserts both attributes and the visible figure carry the handed values. Test only; no production code.

Proof: a Jinja sum over `data` planted (scratch copy of `results.html`, restored) in `data-plays-listed` failed on 50 vs 777, and in `data-plays-matched` on 50 vs 555.

Deviations: none. Edited existing tests: none. Validation: `pytest -q` -- **2898 passed**.

### 2026-10-21 - The KPI test catches a recomputed average

Side task, no batch tag: make the KPI "published figures" test fail if the browser recomputes any figure, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the page must show the figure the server decided, and the test that says so must be able to fail when it does not.

What changed: `test_kpi_blocks_render_the_published_figures_and_compute_nothing` published a daily average of 0.04, which a browser recompute from the same counts also formats as "0.0", so a recomputed average passed. It now publishes 12.3 over counts that give 0.3, and the counts (`2026-03-09: 2`, `2026-03-10: 1`) give a total of 3, a best day of 2 on Mar 9 and a streak of 2, each different from the published 14, 9 on Mar 5 and 7. Only the test's data, assertions and docstring changed; no production code.

Proof: a recompute planted in `renderKpis` (scratch copy of `heatmap.js`, restored) for each of total, average, best day and streak failed the test on that block (3 vs 14, 0.3 vs 12.3, 2 / MAR 9 vs 9 / MAR 5, 2 vs 7).

Deviations: none. Edited existing tests: `test_kpi_blocks_render_the_published_figures_and_compute_nothing`. Validation: `pytest -q` -- **2897 passed**.

### 2026-10-21 - The Scrobbles figure comes from Python

Side task, no batch tag: compute the Results Scrobbles figure in `listening_stats` and make the page and `results.js` read it, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the Scrobbles number is a domain figure whose population (every listed row, or matched rows only) should be named in Python, not re-added in Jinja and again in the browser.

What changed: `_render_results_page` calls `album_play_statistics(filtered_results)` after the display filters and passes `play_stats` to both `render_template("results.html", ...)` blocks (the no-matches block and the filled block, per L6; the blocks are not merged). The template reads it in both states, so both blocks carry it. `results.html` drops the Jinja `sum` (`total_scrobbles`) and the `stat-scrobbles` span now carries `data-plays-listed` and `data-plays-matched`; `setUnmatchedHidden` in `results.js` drops its reduce over `data-play-count` and shows the matched or listed figure for Hide or Include. The figure is computed from the rows the page lists, not at job completion, because the playtime ranking drops rows after the job ends. Two copies of the sum are gone (Jinja and `results.js`). The displayed number is unchanged: Task 1's `test_scrobbles_figure_*` tests pass unmodified.

Docs: `runtime-system.md` gains the edge `Routes --> Stats` (node and class entry came from Task 4); `top-albums-sequence.md` states nothing about how the stat block is computed, so it is unchanged; `SESSION_CONTEXT.md` Section 4 lists `listening_stats` among the imports of `routes/album_flow.py`.

Deviations: none. Edited existing tests and fixtures: `TEMPLATE_CONTEXT["results.html"]` and `_results_html` in `tests/test_template_shell.py` gain `play_stats` (Jinja raises on the missing name); `include_run` in `scripts/dev/results_behavior_tests.py` builds the fixture span from the rows it renders (protecting `test_hiding_every_row_clears_the_top_artist_and_including_restores_it`, whose all-unmatched rows must read 0 under Hide and 80 under Include).

New tests: `test_scrobbles_stat_publishes_both_populations_for_the_albums_control`, `test_scrobbles_stat_on_a_run_without_unmatched_rows_has_equal_figures` (`tests/test_routes.py`) and `test_scrobbles_stat_shows_the_published_figures_not_a_sum_of_rows` (`results_behavior_tests.py`). Mutations shown failing: template shows `plays_matched` (the new publish test and Task 1's include test fail), stats from `results_data` (`test_scrobbles_figure_leaves_out_albums_a_playtime_ranking_drops` reads 90), reduce restored in `results.js` (behaviour test reads 120, not 999), matched forced to 0 without unmatched rows (the equal-figures test fails).

Validation: `pytest -q` -- **2897 passed**.

### 2026-10-21 - The heatmap KPIs come from Python

Side task, no batch tag: publish the heatmap KPI statistics from `listening_stats` and make the browser render them, on `refactor/statistics-module`, a branch off `main`.

Owner intent: a domain rule (streak, best day, average) belongs in Python with its population stated, and the browser only formats what the server decided.

What changed: `_fetch_and_process_heatmap` now takes the window end from `utc_date(now)`, calls `heatmap_statistics(daily_counts, to_date)` and stores the result under the new key `statistics` (`total_plays`, `daily_average`, `best_day`, `current_streak`, each `{"value", "population"}`) in the same `jobs.succeed` write; `total_scrobbles`, `max_count` and `daily_counts` stay, since the grid, its colour scale and the SVG label read them. In `static/js/heatmap.js` the browser's `computeStreak`, `WINDOW_DAYS` and the best-day reduce are deleted; `kpiModel(statistics)` formats the published figures and `renderKpis(data)` renders them, logging to the console and leaving the row empty if a payload carries no statistics (a server bug, not something to recompute around). The eight hand-seeded gate payloads (`_frontend_gate_heatmap_access.py` x4 payloads, `_frontend_gate_theme.py` x2, `_frontend_gate_pipeline.py`, `_frontend_gate_figures.py`) now seed `statistics` through `heatmap_statistics`; the access module's comment names `HEATMAP_WINDOW_DAYS` in heatmap.py. The HEATMAP_WINDOW_DAYS comment, the runtime and sequence diagrams and SESSION_CONTEXT's dependency lines follow the code. `jobs._context_view` deep-copies only `daily_counts`, so `statistics` is returned by reference (nothing in this PR mutates it).

Visible change (empty-window ruling, controller, 2026-10-21): a window with no plays has no best day. Before, the BEST DAY block showed 0 with the window's last day as its label; now it shows 0 with no date line, the same way a zero total or streak shows `0` and a block with no sub-label omits that line. A new case `a_window_with_no_plays_has_no_best_day` in `tests/fixtures/heatmap_kpi_cases.json` pins it (expected text measured from the rendering: `0`, `0.0`, `0`, no date, `0`). The job itself still fails a zero-scrobble range with `no_scrobbles_in_range` before storing, so only a payload built by hand reaches this rendering today.

Deviations: `test_statistics_reach_the_browser_through_heatmap_data` is synchronous and drives the task with `asyncio.run`, because the `client` fixture keeps its request context open and an async test errors at teardown with `LookupError` on `flask.app_ctx`; the gate modules that import `datetime` as a module use `datetime.date.fromisoformat` rather than a second `date` import that their `date: str` parameters would shadow; the test-seam comment above `__scrobbleHeatmapTestHooks` already said the functions touch only the row they are handed, which stays true, so it is unchanged.

Edited existing tests: `test_happy_path_stores_correct_result_dict` (asserts the published statistics), `test_kpi_blocks_show_what_the_window_holds` (feeds the published statistics through the new `_published` helper and no longer names `computeStreak` in its docstring) and `test_the_published_figures_are_the_ones_the_pinned_kpis_show` (a null best-day date reads as the empty label the new case expects).

Mutations (copy aside, file restored): a streak that starts at yesterday fails `test_happy_path_stores_correct_result_dict`, `test_statistics_reach_the_browser_through_heatmap_data`, the `streak_ends_today`, `a_gap_ends_the_streak`, `average_is_over_every_day_of_the_window`, `average_shows_one_decimal_and_thousands_separator` and `a_streak_stops_at_the_first_day_of_the_window` cases in both tables; a browser-side streak assignment in `kpiModel` fails `test_kpi_blocks_render_the_published_figures_and_compute_nothing`; deleting `"statistics": statistics,` fails the happy-path test and the heatmap_data test with `KeyError: 'statistics'`; a `/heatmap_data` response built from named keys fails only the heatmap_data test; removing the `best.date ?` guard fails `test_a_window_with_no_best_day_shows_no_date` and the new table case; `>=` in `best_day` fails the new case in both tables. Gates: `frontend_gate.py` 48 checks passed (the gate was not run under the mutations: it seeds its own payloads, so the code-side mutations are not expected to reach it), `results_behavior_tests.py` 18 tests OK.

Validation: `pytest -q` -- **2895 passed**.

### 2026-10-21 - The statistics tests pin the sentences and the UTC day

Side task, no batch tag: make the listening statistics tests fail on a false population sentence, a system-zone date and an unsorted best day, on `refactor/statistics-module`, a branch off `main`.

Owner intent: tests assert intended behaviour, not the code as written, so a wrong module must not pass them.

What changed: in `tests/test_listening_stats.py` the album population test now asserts both published sentences whole (before, rewording the matched sentence to "include-unmatched are counted", or dropping only "(unmatched)", still passed because the word also sits in "include-unmatched"; swapping the two sentences failed only the distinctness check), and the heatmap population test asserts all four sentences whole instead of "not blank and distinct". A new `TestUtcDate` test gives `utc_date` a datetime subclass whose `astimezone()` with no argument answers in Tokyo, so a conversion that uses the host zone returns 2 March instead of 1 March on any host; a UTC host (CI) hid that defect before, since the system zone there is UTC. It does not use `time.tzset`. A new `TestBestDay` test lists the later tied day first, so dropping `sorted()` returns the later day. Mutations (copy-aside, module restored): rewording, dropping "(unmatched)", swapping the album sentences, swapping two heatmap sentences, `astimezone()` with no argument (also with `TZ=UTC0`) and dropping `sorted()` each fail one or more tests; restored, 33 pass. The 24-row mutation table of Task 2 was not re-run: no test it relies on was weakened, the two edited tests only got stricter.

Deviations: none. Edited existing tests: `TestHeatmapStatistics::test_every_figure_states_its_population` and `TestAlbumPlayStatistics::test_each_figure_says_what_it_leaves_out`.

Validation: `pytest -q` -- **2890 passed**.

### 2026-10-21 - The two-quiet-days KPI case catches a lenient streak

Side task, no batch tag: make the shared KPI fixture's two-quiet-days case fail a lenient streak, on `refactor/statistics-module`, a branch off `main`.

Owner intent: a test must fail when the rule it names is broken, so the streak case cannot pass for a port that forgives two quiet days.

What changed: in `tests/fixtures/heatmap_kpi_cases.json` the case `two_quiet_days_make_the_streak_zero` gains a play at day offset 2 (days 0 and 1 stay empty). Before, the only play sat at offset 5, so a streak that ended two days back still found nothing and returned 0; now it finds the offset-2 play and returns 1, and the case fails. The expected values were measured with the JS harness on unchanged `heatmap.js` (scrobbles 5, best day MAR 5 with 4, streak 0). Planting "forgive two quiet days" in `heatmap.js` failed the JS case; the same plant in `scrobblescope/listening_stats.py` failed the Python case. The test-seam comment in `static/js/heatmap.js` called the hooked functions side-effect free, but `renderKpisInto` sets `kpiRow`; it now says they touch only the row they are handed. No empty-window case is added: the JS and Python empty-window outputs differ and that choice belongs to Task 4.

Deviations: none. Edited existing tests: `test_kpi_blocks_show_what_the_window_holds[two_quiet_days_make_the_streak_zero]` and `test_the_published_figures_are_the_ones_the_pinned_kpis_show[two_quiet_days_make_the_streak_zero]` (data only).

Validation: `pytest -q` -- **2888 passed**.

### 2026-10-21 - The window declaration drops two heatmap.js sites

Side task, no batch tag: retire two docsync value sites that name `static/js/heatmap.js`'s window code, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the 365-day window declaration must stop guarding text that the next commit deletes, so the statistics move is not blocked by a stale pattern (seam B-4).

What changed: `config/docsync.toml` loses the `WINDOW_DAYS = (\d+)` site and the `whole (\d+)-day window` site, both in `static/js/heatmap.js`. Task 4 removes that text because the browser stops dividing by a window length; the average now divides by the zero-filled window in Python. A declaration whose pattern no longer matches fails DOC009, so the sites go first, in their own commit. The Python constant (`HEATMAP_WINDOW_DAYS`), the exported caption (`LAST (\d+) DAYS`) and all copy sites stay guarded. A staged `config/docsync.toml` change outside `[test_count]` is control-plane, so the commit used the documented escape: `--check` exit 0, `SKIP=doc-state-sync-check git commit`, `--check` again. Never `--no-verify`.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2888 passed**.

### 2026-10-21 - Listening statistics have one module

Side task, no batch tag: the pure listening statistics module and its tests, on `refactor/statistics-module`, a branch off `main`.

Owner intent: the streak, best-day, average and plays figures get one home with ordinary pytest coverage and a stated population each (seam B-4), before the heatmap and the Results page are wired to it.

What changed: `scrobblescope/listening_stats.py` (new, standard library only, no clock, no I/O) holds `utc_date` (refuses a naive datetime), `current_streak`, `best_day`, `daily_average`, `heatmap_statistics` and `album_play_statistics`; the two aggregates return `{name: {"value", "population"}}`. UTC is by construction: day keys are the ISO dates the pipeline already attributed in UTC and `today` is passed in. `tests/test_listening_stats.py` (new, 31 tests) covers each rule and runs the eight pinned KPI cases from `tests/fixtures/heatmap_kpi_cases.json` through `heatmap_statistics`, so the Python rules match what readers saw. Nothing imports the module yet; the heatmap and the Results page move onto it in the next commits. `.claude/SESSION_CONTEXT.md` Sections 3 and 4 list the module.

Mutation evidence, each planted in a scratch copy of the module and restored: 24 planted defects (local-day `utc_date`, naive datetime accepted, no yesterday step, two quiet days forgiven, `streak + 1`, a missing day read as a play, indexing instead of `.get`, last-day and `>=` best day, a zero best day, unguarded empty mapping, average over play days, rounded average, no empty guard, streak anchored on the first day, a blank and a shared population, a `"None"` date, `plays_matched` ignoring unmatched rows or minus a fixed 1, `rows[0]`, indexed `play_count`, identical populations) each failed the test the plan names for it. One planted defect was too weak: removing only the parenthesised `(unmatched)` from the matched population still passed, because the sentence also says `include-unmatched`; removing the whole unmatched clause fails `test_each_figure_says_what_it_leaves_out`.

Deviations: none. Edited existing tests: none.

Validation: `pytest -q` -- **2888 passed**.

### 2026-10-21 - The heatmap KPIs and the Scrobbles figure are pinned before they move

Side task, no batch tag: parity tests for the heatmap KPI blocks and the Results Scrobbles figure, on `refactor/statistics-module`, a branch off `main`.

Owner intent: a refactor starts from parity tests, so the next two commits can move the streak, best-day, average and Scrobbles rules out of the browser and Jinja provably unchanged (seam B-4).

What changed: `tests/fixtures/heatmap_kpi_cases.json` holds eight 365-day windows ending 2026-03-10 (streak ends today, streak may end yesterday, a gap ends it, two quiet days make it zero, a tie for best day goes to the earlier day, the average is over every day, one decimal with a thousands separator, a streak stops at the window's first day), each with the KPI text worked out by hand. `tests/helpers.py` gains `load_kpi_cases`, `kpi_window`, `kpi_payload` and `expected_kpi_blocks`. `static/js/heatmap.js` gains the test-seam hook `renderKpisInto(row, data)`, present only when `window.__scrobbleHeatmapTestMode` is set, so a real page is unchanged. `tests/frontend/test_heatmap_pure_functions.py` runs each case through it (8 tests). `tests/test_routes.py` gains two tests: Scrobbles is the plays of every album the page lists (120 matched, 200 with unmatched rows), and a playtime ranking leaves out an album with no listening time (50). SESSION_CONTEXT Section 6 names the new fixture.

Mutation evidence, each planted in the working file and restored: `while (dailyCounts[isoDate(d)])` to `while (false)` failed `streak_ends_today`, `streak_may_end_yesterday`, `a_gap_ends_the_streak`, `average_is_over_every_day_of_the_window`, `average_shows_one_decimal_and_thousands_separator` and `a_streak_stops_at_the_first_day_of_the_window`; `>=` to `>` in the best-day reduce failed `a_tie_for_best_day_goes_to_the_earlier_day`, `average_is_over_every_day_of_the_window` and `a_streak_stops_at_the_first_day_of_the_window`; `sum(attribute='play_count')` to `sum(attribute='play_time_seconds')` in `results.html` failed both route tests.

Deviations: none. Edited existing tests: none (the module docstring of `tests/frontend/test_heatmap_pure_functions.py` changed, no test).

Validation: `pytest -q` -- **2857 passed**.

### 2026-10-21 - The statistics module plan opens its branch

Side task, no batch tag: the approved statistics module plan, committed as the branch's first commit, on `refactor/statistics-module`, a branch off `main`.

Owner intent: "All plans should stay for archival purposes" (2026-10-20), so every PR's plan is its branch's first commit.

What changed: `docs/superpowers/plans/2026-10-20-statistics-module.md` is added (six tasks: pin the heatmap KPIs and the Scrobbles figure, the pure `listening_stats` module, retire two docsync sites, publish the heatmap statistics, compute the Scrobbles figure in Python, amend WP-6). PLAYBOOK Section 3's "Before WP-1" bullet gains one sentence naming PR #6, its branch and the plan. The plan passed the brief review (`plan-review.md`), two fix rounds and two re-reviews (`plan-rereview-1.md`, `plan-rereview-2.md`; approved); owner Q1 is approved ("Yes, that sounds good."): the Scrobbles figure is computed at render time in the Results route. It was then drift-reviewed against `eb0db9e` (`main` after PRs #256-#260) and the fixes were folded in as its Revision 3. Structural: S1, the publication test in Task 4 Step 1 now patches `fetch_scrobbles` and uses `_fetch`, `_play` and `UTC` (the page-layer patch target and helpers are gone); S2, Task 5 Step 3 builds the `include_run` span from the rows rendered, so `test_hiding_every_row_clears_the_top_artist_and_including_restores_it` keeps passing; S3, `scripts/dev/_frontend_gate_figures.py` (`_HEATMAP_RESULT`) joins Task 4's Touches, Step 5 and the Section 4 line, making eight gate payloads, not seven. Renames (7): `plays.aggregate_daily_counts`, `_play`/`_fetch`, `fetch_scrobbles`, `UTC` for `timezone.utc` in Task 2, the `heatmap` docstring dependency line, the SESSION_CONTEXT current-text quotes, and the `listening_stats` docstring wording. Cosmetic (9, C1-C9; C3 and C7 needed no change): helper imports, the `HEATMAP_WINDOW_DAYS` comment, the `class` line, the sequence-diagram anchor, Hide/Include wording, entry headings take the commit date, Task 6's moot conflict note, and one `_context_view` sentence for Task 4's commit body. The "unverified until #4 merges" rows of the PR #4 table are rewritten as checked.

Deviations: the drift review said `test_utc_midnight_decides...` has three `timezone.utc` uses; the plan has two (`NEW_YORK` is a fixed offset), so two were changed. No DOC citation error needed a wording change in the plan. Edited existing tests: none.

Validation: `pytest -q` -- **2847 passed**.

### 2026-10-21 - The cache owns its connection and its failures

Side task, no batch tag: Task 4 of PR #5, the cache owns its connection and its failures (`AlbumCache`, `open_album_cache`, `process_albums`, `orchestrator/_cache.py`, the facade's imports), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent (the spec's hosting ceiling): a missing or sleeping database degrades to provider calls and never fails a job.

Why (F-B23-3): `process_albums` opened the connection, held it across provider work and closed it in a `finally` that did not guard `close()`, while `orchestrator/_cache.py` owned the failure policy, so understanding "the cache is optional" took two modules and a failing `close()` failed a job whose results were built. The connection-closure test also had to configure the provider machinery.

What changed: `cache.AlbumCache(conn)` has `enabled`, `lookup_failed`, `persist_failed`, `lookup`, `persist`, `lookup_original_releases` and `close`; `open_album_cache()` connects through `get_db_connection` and closes when its block ends however it ends. `process_albums` wraps Phases 1 to 4b in `async with open_album_cache()`, and `_lookup_cached_metadata` and `_persist_new_metadata` take the cache and turn its flags into the same job stats and log lines as before (every log line is kept word for word). The facade no longer imports `get_db_connection` or the four batch functions, so tests patch them at `scrobblescope.cache.<name>`. `_lookup_cached_original_release` is gone (its body is `AlbumCache.lookup_original_releases`). A new boundary test pins that only `cache.py` names the metadata read, write and cleanup functions and holds the one INSERT into `spotify_cache`. Docs: SESSION_CONTEXT Sections 3 to 5, `runtime-system.md` (one node and the release-date bullet), `top-albums-sequence.md` (four messages and one note, commas only), `BATCH23_DEFINITION.md` (the PR #5 amendment of WP-3's metadata shape: Data handling and a WP-3 bullet), and F-B23-3 marked resolved.

Deviations: a failing `close()` is now logged by exception class and swallowed, the one behaviour change. `_lookup_cached_original_release` is deleted and its two tests moved to `tests/services/test_cache.py`. Mutation row 7 of the brief (record `db_cache_persisted` after a failed persist) is not caught by `test_a_failing_cache_statement_never_fails_the_search[write]`, which checks only `db_cache_warning`, so a test was added, `test_a_failed_persist_is_reported_as_a_warning_not_as_persisted_rows` in `test_orchestrator_process_albums.py`; Task 1's parity file stays untouched. The re-point script printed 46, 2, 2 and 3 replacements, and `ruff format` then reflowed the lines the longer patch strings overran. The Mermaid validator was not available to the implementer, so the controller renders the two diagram files (`runtime-system.md` flowchart node, `top-albums-sequence.md` sequence).

Hosting evidence: `tests/test_album_cache_parity.py` and `tests/fake_postgres.py` are unchanged by this task and pass (one connection, one close, the same statement sequence, under every injected failure), and the diff of `scrobblescope/` adds no `.execute(`, `.fetch(` or `asyncpg.connect(` line.

Edited existing tests: `tests/services/test_orchestrator_process_albums.py` (patch strings, and two direct `_lookup_cached_metadata` calls now wrap `AlbumCache`), `tests/services/test_orchestrator_fetch_spotify.py` and `tests/test_pipeline_integration.py` (patch strings only), `tests/services/test_orchestrator_helpers.py` (two tests moved to `test_cache.py`), `tests/services/test_failure_logging.py` (four sites re-pointed at `AlbumCache`).

Mutation evidence (each planted in a file kept aside, restored byte for byte, then re-run green): (1) `AlbumCache.close` without its `try`/`except` -> `test_a_failing_close_is_logged_by_class_and_never_raised` (RuntimeError) and `test_process_albums_survives_a_connection_that_fails_to_close` fail; (2) `open_album_cache` without `try`/`finally` -> `test_the_connection_closes_once_however_the_block_ends[True]` (`(1, 0) == (1, 1)`) and `test_the_connection_is_closed_once_when_no_provider_can_answer` fail; (3) `persist` guard without `self._conn is None` -> `test_a_cache_with_no_database_does_nothing_and_fails_nothing` fails; (4) `lookup` without `try`/`except` -> `test_a_failing_cache_statement_never_fails_the_search[read]` fails; (5) a reconnect in `lookup`'s `except` -> the same test fails on `(2, 1) == (1, 1)`; (6) `release_checks.py` importing `batch_persist_metadata` -> `test_only_the_cache_module_reads_or_writes_the_metadata_table` fails; (7) `db_cache_persisted` recorded after a failed persist -> `test_a_failed_persist_is_reported_as_a_warning_not_as_persisted_rows` fails; (8) a bare write in `persist` -> `test_a_failed_read_is_a_miss_and_a_failed_write_is_not_an_error` and `test_a_failing_cache_statement_never_fails_the_search[write]` fail; (9) `lookup` returning `{}` -> `test_what_persist_writes_lookup_reads_back` fails; (10) Task 3's row 3 re-planted (`if metadata is not None:` removed) -> `test_a_stored_row_naming_no_provider_album_is_a_miss_not_an_album` fails.

Validation: `pytest -q` -- **2891 passed**.

### 2026-10-21 - Album metadata is one record from provider to results

Side task, no batch tag: Task 3 of PR #5, album metadata stored and read as one record from provider to results (cache, the three orchestrator phases, the results builder and seven test files), on `refactor/metadata-encoding`, a branch off `main`.

Owner intent: card B-5 and the Task 27 brief say it in one line: one `AlbumMetadata.from_row` replaces the repair code, and `_album_provider` and `_album_url` are deleted.

Why (B-5): after the providers an album was re-encoded as a nine-tuple for the database, as a 4-key or 7-key dict for the results and as a 7-key dict from cache reads; two functions in `_results.py` existed only to repair what the shortest of them lacked, and `batch_persist_metadata` kept a six-tuple branch that only a test reached. There is now one record, and one place a stored row is read (`AlbumMetadata.from_row`) and one statement that writes `spotify_cache` (`batch_persist_metadata`).

What changed: `batch_lookup_metadata` returns `{key: AlbumMetadata}` (a row naming no provider album is left out, so it is a miss) and `batch_persist_metadata` takes `{key: AlbumMetadata}`, with the same SQL and the same single statement. `_run_spotify_batch_detail_phase`, `_run_deezer_fallback_phase` and `_fetch_spotify_misses` return `{key: AlbumMetadata}`; `cache_hits[key]["cached"]` holds an `AlbumMetadata` for hits and live fetches alike; `_persist_new_metadata` takes that dict. Deleted: `AlbumMetadata.as_cache_row`, `_album_provider`, `_album_url`, the `len(r) > 6` branches and both inline `cached` dicts. New: `tests/album_metadata.py` (builders `spotify_metadata`, `deezer_metadata`). Docs: `cache.py` now imports `enrichment` (SESSION_CONTEXT module graph and the `Cache --> Enrichment` edge in `runtime-system.md`; the Mermaid validator tool was not available to this implementer, so the edge was checked by hand against the neighbouring edges, and the "eleven nodes import config" count was re-checked with an `ast` walk: this change adds no `config` import, so it stands); F-B23-32 now names `AlbumMetadata.from_row` as the one place a cached link enters.

Deviations: a live Spotify result now shows the link Spotify returned in `external_urls.spotify` rather than a rebuilt classic link (the same string in practice). A stored row naming no provider album is a miss. `cache_hits[key]["cached"]` keeps its key name though it now also holds live fetches. The first view of a search now renders the provider-supplied URL (`external_urls.spotify`) where it used to render a constructed one, so F-B23-32's exposure to unchecked provider URLs widens slightly (the finding is edited in this commit; its status stays open). Beyond the brief's edit list: `test_run_spotify_batch_detail_phase_empty_id_list_skips_api_call` asserted `result == []` and now asserts `result == {}` (the return type changed), and the docstring of `test_an_older_spotify_row_is_a_spotify_album_with_the_classic_link` no longer names the two deleted functions (the sweep greps for them). The sweep regex also matches the brief-named test `test_a_cached_album_with_no_link_has_a_null_album_url` (substring `_album_url`); that is the only hit.

Task 1's `tests/test_album_cache_parity.py` and `tests/fake_postgres.py` are unchanged and pass: this is the parity proof, and the statement sequence and connection count are as before.

Edited existing tests: `tests/services/test_enrichment.py` (two `as_cache_row` tests deleted, replaced by Task 1's stored-column tests and the persist tests below), `tests/services/test_cache.py` (four tests replaced by five; the six-tuple test is deleted because no caller builds a six-tuple, its legacy-row rule now lives in `from_row`), `tests/test_repositories.py`, `tests/services/test_orchestrator_process_albums.py` (four fixtures, three persist assertions), `tests/services/test_orchestrator_helpers.py` (three fixtures, one new test), `tests/services/test_orchestrator_fetch_spotify.py` (return type of the phases), `tests/services/test_failure_logging.py` (one argument).

Mutation evidence (each planted in a file kept aside, restored byte for byte, then re-run green): (1) `spotify_ids` from `album_id` -> `test_batch_persist_metadata_writes_a_deezer_album_without_a_spotify_id` and `test_a_deezer_album_is_stored_without_a_spotify_id_and_a_repeat_search_matches_it` fail; (2) `provider_album_ids` and `provider_urls` swapped -> `test_batch_persist_metadata_writes_a_spotify_id_to_both_columns` and `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` fail; (3) `if metadata is not None:` removed -> `test_a_row_naming_no_provider_album_is_a_cache_miss` fails; (4) result `album_url` from `image_url` -> `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` fails; (5) `or None` dropped -> `test_a_cached_album_with_no_link_has_a_null_album_url` fails; (6) `new_metadata[key] = metadata` deleted -> the Spotify parity test fails (the repeat search finds nothing stored); (7) `new_metadata.update(deezer_metadata)` deleted -> the Deezer parity test and `test_spotify_search_outage_degrades_to_deezer_and_lists_the_rest_as_unavailable` fail; (8) provider columns dropped from the `from_row` input -> `test_batch_lookup_metadata_returns_albums_with_their_provider_columns` fails; (9) `provider_url` dropped from the SELECT -> the same test fails on its SQL assertion; (10) `{**r, "provider": r["provider"]}` -> `test_batch_lookup_metadata_reads_a_pre_provider_row_as_a_spotify_album` fails (`KeyError: 'provider'`).

Validation: `pytest -q` -- **2879 passed**.
