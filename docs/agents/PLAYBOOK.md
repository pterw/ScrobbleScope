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
  runs next (branch `fix/pre-batch23-side-tasks`, plan
  `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md`); the
  documentation refresh merges last.
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
