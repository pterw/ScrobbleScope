# PLAYBOOK Execution Log Archive

Purpose:
- Store dated execution-log entries rotated out of `PLAYBOOK.md` section 10.
- Keep entries in reverse-chronological order (newest first).

Read helpers:
- `Get-Content docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "<keyword>" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

### 2026-03-03 - Add local DB setup and init_db.py caveat to env docs

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added local Postgres DB setup details and `init_db.py` load_dotenv caveat
to AGENTS.md Environment Setup and SESSION_CONTEXT Section 8. These facts apply to
all agents (Gemini CLI, Copilot, Codex, Claude Code) running local DB tests.

**Why:** `init_db.py` has no `load_dotenv()` call. Any agent running it will get
"DATABASE_URL not set" unless the env var is set directly in the shell. Absent from
canonical docs, every agent would hit this silently and assume cache is unavailable.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

### 2026-03-03 - Add browser MCP environment note to SESSION_CONTEXT

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added one line to SESSION_CONTEXT Section 8 (Environment notes) documenting
that the browser MCP accesses the local Flask app via `http://host.docker.internal:5000/`
rather than `localhost`, because the MCP browser runs inside a Docker container.

**Why:** This is a runtime fact that future agent sessions need to reproduce local
browser testing correctly. Absent from SESSION_CONTEXT, an agent would attempt
`localhost` and get a connection refused error with no clear diagnosis path.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

### 2026-03-02 - Session findings and handoff notes (side-task)

**Scope:** Observations from Batch 15 WP-1 execution session, documented for
next-agent orientation.

**Findings:**
1. **docsync `--fix` SESSION_CONTEXT write bug (fixed):** `cli.py` computed the
   correct STATUS block but never wrote it. Fixed in commit `67fa1dc`. AGENTS.md
   cross-validation section updated to reflect corrected behavior.
2. **Deviation tag routing:** Headings with non-standard tags like
   `(Batch 15 WP-1 deviation)` do NOT match `ENTRY_BATCH_RE` regex
   (`\(Batch\s+(\d+)\s+WP-\d+\)`). They are routed outside CURRENT-BATCH
   markers as untagged entries. This is correct behavior -- use standard
   `(Batch N WP-X)` tags only for entries that should stay inside markers.
3. **Mid-batch handoff discipline (added):** AGENTS.md now requires PLAYBOOK
   Section 3 to reflect true state at all times, not just after commits.
4. **SESSION_CONTEXT Section 7 is stale:** Shows 307 tests across old counts.
   Actual: 311 tests across 18 files. WP-2 will fix this.
5. **README.md is stale:** Says 257 tests, lists incomplete pre-commit hooks,
   project structure test section outdated. WP-2 will fix this.
6. **HANDOFF_PROMPT.md is stale:** References deleted branch, old audit, old
   tasks. WP-5 will replace it; interim handoff written for this transition.

**Forward guidance:**
- Next agent should start with WP-2 per BATCH15_DEFINITION.md execution order.
- Always use standard `(Batch N WP-X)` tags for batch log entries.
- Run `doc_state_sync.py --fix` after every PLAYBOOK Section 4 edit.

### 2026-03-02 - Fix docsync --fix not writing SESSION_CONTEXT STATUS block (Batch 15 WP-1 deviation)

**Scope:** `scripts/docsync/cli.py`, `tests/test_docsync_cli.py`, `AGENTS.md`.

**Plan vs implementation:**
- Planned: during WP-1 execution, discovered that `doc_state_sync.py --fix`
  computes the correct STATUS block for SESSION_CONTEXT but never writes it
  to disk. AGENTS.md line 138-139 claimed the script "Refreshes the
  machine-managed DOCSYNC:STATUS block" but the code only warned on staleness
  without writing. This was a bug, not a design choice.
- Implemented: modified `cli.py` so `--fix` writes the refreshed STATUS block
  to SESSION_CONTEXT when stale. `--check` continues to warn-only (does not
  fail) because SESSION_CONTEXT is gitignored and should not block commits.
  Updated AGENTS.md cross-validation section to reflect corrected behavior.
  Added 1 new test (`test_fix_refreshes_session_context_status_block`) and
  updated the stale-warning assertion text in existing test.

**Deviations:**
- This fix was not in the Batch 15 definition. It was discovered during WP-1
  when the agent attempted to run `--fix` and found SESSION_CONTEXT unchanged.
  The fix is scoped to the bug and does not change any other docsync behavior.

**Validation:**
- `pytest tests/test_docsync_cli.py -v` (**19 passed**)
- `pytest -q` (**311 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --fix` (wrote SESSION_CONTEXT)
- `python scripts/doc_state_sync.py --check` (pass, no stale warning)
- `pre-commit run --all-files` (pass, all 8 hooks)

**Forward guidance:**
- After any PLAYBOOK Section 4 edit, run `doc_state_sync.py --fix` and verify
  SESSION_CONTEXT STATUS block was updated. The script now handles this
  automatically.

### 2026-02-27 - Revalidate audit findings and prepare next-agent packet (side-task)

**Scope:** `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md`,
`tests/test_docsync_logic.py` (format-only), repo-wide quality gates.

**Plan vs implementation:**
- Planned: verify previously reported findings against current branch state,
  refresh stale assertions, and produce implementation-ready guidance for the
  next agent handoff.
- Implemented: re-ran full validations, updated stale test baseline and
  resolved-item status in the audit report, and added a scoped next-agent
  implementation packet with acceptance criteria.

**Deviations:**
- No behavioral code changes were required; only audit/report updates plus
  formatter-normalized whitespace in `tests/test_docsync_logic.py`.

**Validation:**
- `pre-commit run --all-files` (pass)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Execute the next-agent packet in commit-sized slices: test-module split,
  low-risk orchestrator extraction, then CI/session policy wording alignment.

### 2026-02-27 - Harden docsync non-happy-path coverage + path guidance (side-task)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`AGENTS.md`, `PLAYBOOK.md`.

**Plan vs implementation:**
- Planned: enforce anti-happy-path discipline for docsync archive-link and
  migration handling, and remove path ambiguity between untagged archive,
  per-batch logs, and definitions.
- Implemented: added adversarial tests for `docs/logarchive` link validation
  (exists/missing) and for `--split-archive` missing-input failure (`exit 2`),
  plus explicit archive/log/definition lookup guidance in AGENTS and PLAYBOOK.

**Deviations:**
- One assertion was adjusted to be path-separator-agnostic on Windows
  (`PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` substring) after first run exposed
  slash-vs-backslash brittleness.

**Validation:**
- `pytest -q tests/test_docsync_logic.py tests/test_docsync_cli.py`
  (**57 passed**)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Keep new docsync tests behavior-focused (real inputs + failure paths), not
  mock-call-only checks, when adding future archive-routing rules.

### 2026-02-27 - Migrate monolith archive path to docs/logarchive (side-task)

**Scope:** `scripts/docsync` path canonicalization, pointer compatibility docs,
doc references, regression validation.

**Plan vs implementation:**
- Planned: stop using the legacy history monolith paths
  (`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
  `docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`) as the
  canonical monolith location and move to a dedicated `docs/logarchive/`
  folder with clear pointers from legacy paths.
- Implemented: switched docsync `ARCHIVE_PATH` to
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, copied canonical
  archive content there, converted both legacy monolith files into pointer
  documents, and added `docs/logarchive/README.md` lookup guidance.

**Deviations:**
- Historical documents under `docs/history/definitions/` and batch logs were
  left unchanged to preserve historical wording; compatibility pointers prevent
  breakage for legacy references.

**Validation:**
- `python scripts/doc_state_sync.py --fix`
- `python scripts/doc_state_sync.py --check`
- `pytest -q tests/test_docsync_cli.py tests/test_docsync_logic.py`
  `tests/test_docsync_parser.py tests/test_docsync_renderer.py` (**103 passed**)
- `pytest -q` (**307 passed**, 3 deprecation warnings from aiohttp connector)

**Forward guidance:**
- Use `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for untagged archive
  search and keep per-batch logs under `docs/history/logs/` as the tagged route.

### 2026-02-27 - Branch hygiene cleanup after main diff review (side-task)

**Scope:** orchestration hygiene (`.gitignore`, PLAYBOOK state consistency,
root audit-file placement), docsync warning cleanup.

**Plan vs implementation:**
- Planned: remove non-actionable docsync warning noise and align tracked state
  with the "local-only" `.claude/SESSION_CONTEXT.md` policy.
- Implemented: scoped `BATCH*_AUDIT*.md` ignore rule to repo root only,
  moved `BATCH14_PROPOSAL_AUDIT1.md` from root into `docs/history/`, and
  recorded the side-task in Section 4.

**Deviations:**
- `git mv` could not be used for `BATCH14_PROPOSAL_AUDIT1.md` because the file
  was not under version control; file-system move was used instead.

**Validation:**
- Ran `python scripts/doc_state_sync.py --fix` and
  `python scripts/doc_state_sync.py --check` after edits.

**Forward guidance:**
- Keep root-only draft/audit patterns scoped with leading `/` in `.gitignore`
  so archive destinations under `docs/history/` remain trackable.

### 2026-02-26 - Remediate docsync audit findings (side-task)

**Scope:** `scripts/docsync/` (cli, parser, renderer, logic),
test suite (parser, renderer, logic), `AGENTS.md`.

**Changes:**
- Fixed unconditional PLAYBOOK/ARCHIVE writes in --fix mode (F1).
- Consolidated SyncError import to top-level in cli.py (F11).
- Defined TEST_COUNT_RE once in parser.py (F2).
- Extracted _dedup_sorted() helper in logic.py (F3).
- Tightened ENTRY_BATCH_RE to require (Batch N WP-X) format (F6).
- Added duplicate-marker detection in _find_marker_pair (F7).
- Added sentinel -1 comment (F5).
- Removed dead stale-phrase detection + 3 tests (F8).
- Fixed misleading docstring (9a), weak assertion (9b).
- Added 4 tests: duplicate headings (9c), adversarial regex (9d),
  duplicate markers (F7), file-order dependency (9e).

**Test count:** **307 passed** (net +1: -3 removed, +4 added).
**Validation:** `pytest -q` 307 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - Post-batch test suite audit (doc hygiene)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`tests/test_docsync_parser.py`; deleted `tests/test_docsync_models.py`.

**Changes:**
- Fixed `test_deduplication_across_archive`: was passing vacuously -- tagged
  entry routed to `batch_log_updates`, bypassing monolith dedup entirely;
  rewrite uses untagged entry and asserts `batch_log_updates == {}`.
- Dropped `test_current_entry_count_mismatch_warns`: near-duplicate of
  `test_mismatched_counts_warns` (identical `_cross_validate` code path).
- Rewrote `test_section4_historical_count_ignored`: old version had no
  CURRENT-BATCH markers so `_latest_test_count_from_entries` returned None
  vacuously; new version confirms below-end-marker counts are ignored while
  inside-marker count is used for comparison.
- Removed unused `LOGS_DIR` name import from `test_docsync_cli.py`.
- Merged 5 `_fingerprint`/`_extract_entry_batch` tests from misnamed
  `test_docsync_models.py` into `test_docsync_parser.py`; deleted old file.
- Added `TestSplitArchiveMode.test_split_archive_routes_tagged_entry` for
  the previously uncovered `--split-archive` CLI branch.

**Test count:** **306 passed** (net zero: -6 removed, +6 added).
**Validation:** `pytest -q` 306 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - fix(doc-sync): remediate SESSION_CONTEXT staleness in _cross_validate and _build_status_block (side-task)

- Scope: `scripts/docsync/logic.py`, `scripts/docsync/renderer.py`, `scripts/docsync/cli.py`,
  `tests/test_docsync_logic.py` (+6 tests: 4 TestLatestTestCount + 2 rewritten + 1 renamed),
  `tests/test_docsync_renderer.py` (+2 TestBuildStatusBlock count tests),
  `tests/test_docsync_cli.py` (1 test updated).
- Problem: Two root causes for SESSION_CONTEXT staleness: (1) `_cross_validate` scanned
  PLAYBOOK Section 3 for `**N passed**` counts, but agents write test counts in Section 4
  log entry Validation fields — Section 3 is narrative prose. `playbook_counts` was always
  empty so the mismatch warning never fired. (2) `_build_status_block` did not include the
  test count in the STATUS block output, forcing agents to check stale manual rows.
  Additionally, `_cross_validate` was called with `result.session_lines` (post-sync), which
  already had the correct count injected by `_build_status_block`, laundering mismatch away.
- Fix: Added `_latest_test_count_from_entries(playbook_lines)` to `logic.py` — parses
  Section 4 current-batch entries newest-first and returns the first `**N passed**` count.
  Updated `_cross_validate` to call this function (scalar comparison) instead of scanning
  Section 3. Added `_TEST_COUNT_RE` to `renderer.py`; `_build_status_block` now emits
  `"- Latest validated test count: **N passed**."` using the most-recent entry body count.
  Fixed `cli.py` to call `_cross_validate(playbook_lines, session_lines)` (original, pre-sync
  lines) so the STATUS block update cannot launder a pre-existing mismatch.
- Deviations: None. All changes additive; no logic in `_sync` was touched.
- Validation: **294 passed** (+6 vs WP-2 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - docs(audit): add BATCH14 pre-approval audit report and apply corrections to proposal (side-task)

- Scope: `BATCH14_PROPOSAL.md`, `docs/history/BATCH14_AUDIT_2026-02-25.md`.
- Purpose: Pre-batch audit of BATCH14_PROPOSAL.md before owner sign-off. Verified
  all five structural checks (WP-1 naming conventions, WP-2 package extraction
  symmetry, WP-3 feature isolation, WP-4 test distribution, WP-5 AGENTS.md
  close-out / MEMORY.md hallucination check). All five checks confirmed correct.
- Correction: "~450-line" description for `doc_state_sync.py` corrected to "~679-line"
  in two places (Current state table and WP-2 goal). Actual measured line count: 679.
- Verdict: APPROVED WITH CORRECTIONS.
- Validation: 288 passed (unchanged -- audit makes no code changes), all 8 pre-commit
  hooks passed.

### 2026-02-25 - test(worker): assert daemon=True via Thread patch, expand docstrings (side-task)

- Scope: `tests/test_worker.py`.
- Problem: `test_start_job_thread_creates_daemon_thread` only asserted the target
  was called; it never verified `threading.Thread` was constructed with `daemon=True`,
  despite the test name and docstring claiming otherwise. Tests 1–4 had minimal
  single-line docstrings inconsistent with the GIVEN/WHEN/THEN standard.
- Fix: Introduced `DummyThread` class, patched at `scrobblescope.worker.threading.Thread`;
  asserts `daemon=True` and target invocation. Dropped `*args` from `DummyThread.__init__`
  (Pylance hint; Thread is called with keyword args only). Expanded tests 1–4 docstrings
  to GIVEN/WHEN/THEN inline format.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - test(retry): use public semaphore API in semaphore-gates test (side-task)

- Scope: `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer flagged `sem._value == 0` as a private implementation detail
  of `asyncio.Semaphore`, suppressed with `# noqa: SLF001`, making the assertion
  brittle across Python versions.
- Fix: Replaced with `sem.locked()`, the public equivalent (stable since Python 3.4).
  Updated comment; noqa suppression removed. Confirmed only occurrence in suite.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - fix(utils): support constant backoff value in retry_with_semaphore (side-task)

- Scope: `scrobblescope/utils.py`, `scrobblescope/spotify.py`,
  `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer 1 flagged that `backoff` only accepted a callable, requiring
  `backoff=lambda _a: 1` for constant delays. Updating call sites to use a plain
  float was not possible without a utility change.
- Fix: Added `callable(backoff)` guard at line 341 of `utils.py`; updated docstring
  type annotation. Simplified `spotify.py` search call site to `backoff=1`. Added
  `test_constant_float_backoff_accepted` to `test_retry_with_semaphore.py`.
- Validation: 288 passed (+1 vs Batch 13 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - test(orchestrator): use standard asyncio import in fetch_spotify tests (side-task)

- Scope: `tests/services/test_orchestrator_fetch_spotify.py`.
- Problem: Reviewer 2 flagged two `__import__("asyncio").Semaphore(5)` usages
  bypassing Pylance type resolution; root cause was missing top-level `import asyncio`.
- Fix: Added `import asyncio` to stdlib imports block; replaced both
  `__import__("asyncio").Semaphore(5)` occurrences with `asyncio.Semaphore(5)`.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-24 - docs(audit): BATCH13 pre-approval audit report (side-task)

- Scope: `BATCH13_PROPOSAL.md`, `docs/history/BATCH13_AUDIT_2026-02-23.md`.
- Problem: BATCH13 proposal required independent technical verification before
  owner approval. Line references, test coverage claims, retry extraction
  design, and convention compliance needed validation against actual codebase.
- Fix: Completed 4-WP audit. Found 5 discrepancies: `_apply_pre_slice` line
  start off by 2 (L664 -> L666), `_JOB_SEMAPHORE` variable name incorrect
  (actual: `_active_jobs_semaphore`), batch retry missing jitter declaration,
  batch backoff incorrectly stated as fixed 1.0 (actual: `2**attempt`
  exponential). Applied all corrections to the proposal. Created audit report.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed. No source
  code changes -- audit only.

### 2026-02-23 - chore(merge): integrate main into wip/pc-snapshot (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py` (merge
  resolution only -- no net change from branch perspective).
- Problem: `main` had one commit ahead (`05c7b19`) that was already
  cherry-picked into `wip/pc-snapshot` as part of `4e4c9a1`. The branch
  needed to formally integrate `main` before PR #36 could merge cleanly.
- Fix: `git merge origin/main --no-edit`; ort strategy resolved cleanly
  (identical content on both sides for the two touched files). Merge commit
  `d98c90b` amended to conventional format.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-23 - fix/docs: cherry-pick SESSION_CONTEXT optional + DEVELOPMENT.md (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py`,
  `DEVELOPMENT.md`, `docs/history/SESSION_CONTEXT_REFERENCE.md`, `README.md`.
- Problem: (1) CI failed on `main` when `.claude/SESSION_CONTEXT.md` was
  absent (gitignored). The script called `_read_lines()` unconditionally,
  raising `SyncError`. (2) No documentation existed for the multi-agent
  orchestration methodology implemented during this sprint.
- Fix:
  (1) Cherry-picked commit `05c7b19` from `main`: added `_read_lines_optional()`
  returning `None` when the file is absent; gated all SESSION_CONTEXT
  operations in `_sync()`, `_cross_validate()`, and `main()` behind
  presence check; `SyncResult.session_lines` typed as `list[str] | None`;\
  renamed `test_missing_session_context_raises` to `_succeeds`; added
  `TestMissingSessionContext` class (3 regression tests).
  (2) Created `DEVELOPMENT.md` explaining the orchestration architecture,
  why `doc_state_sync.py` is a deterministic script, the batch/WP SDLC
  mapping, review-rejection rationale, and what failed before the current
  system stabilized. Created `docs/history/SESSION_CONTEXT_REFERENCE.md`
  as a tracked reference snapshot of the gitignored live file. Linked
  both from `README.md` (new "Development Methodology" section in ToC).
- Validation: **260 tests passing** (3 new from cherry-pick),
  pre-commit all 8 hooks passed.

### 2026-02-23 - chore/docs: repo hygiene and README rewrite (side-task)

- Scope: root directory, `.gitignore`, `README.md`, `.claude/`.
- Problem: (1) Root directory cluttered with completed batch definitions
  (`BATCH12_PROPOSAL.md`, `BATCH8_REFACTOR_PLAN.md`) and an obsolete
  playbook compatibility shim (`EXECUTION_PLAYBOOK_2026-02-11.md`).
  (2) `.claude/` tracked in git (agent-local state, stale `BATCH3_CONTEXT.md`,
  machine-specific `settings.local.json`). (3) `README.md` outdated --
  "work in progress" status badge, 30+ completed checkbox items, missing
  Architecture/Deployment sections, stale Tech Stack section.
- Fix:
  (1) `git mv` both batch definitions to `docs/history/`. `git rm`
  the playbook shim. Deleted untracked stale files (`backup.py`,
  `Backup_batch`, empty `app/` directory).
  (2) Added `.claude/` to `.gitignore`, `git rm --cached` all 3 tracked files,
  deleted stale `BATCH3_CONTEXT.md` locally.
  (3) Comprehensive README rewrite: active status badge + test count badge,
  new Architecture section with pipeline diagram + design decisions, Tech
  Stack table, Deployment section with Fly.io commands + smoke test,
  condensed Roadmap (upcoming + recent completions only), accurate Project
  Structure tree with per-file annotations and test counts, Running Tests
  section, trimmed Contributing/License/Acknowledgements.
- Validation: **257 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-22 - fix(app): guard sys.stderr.reconfigure with isinstance check

- Scope: `app.py`.
- Problem: Pyright/Pylance reported "Cannot access attribute reconfigure for
  class TextIO" because `sys.stderr` is typed as `TextIO`, which lacks
  `reconfigure`. The method exists at runtime on `io.TextIOWrapper`.
- Fix: Added `import io` and wrapped the call in
  `if isinstance(sys.stderr, io.TextIOWrapper):` -- a type-narrowing guard
  that satisfies both the type checker and runtime safety.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all hooks passed.

### 2026-02-22 - refactor(routes,lastfm): SoC/DRY cleanup from third-party audit

- Scope: `scrobblescope/routes.py`, `scrobblescope/lastfm.py`,
  `scrobblescope/orchestrator.py`, `tests/services/test_lastfm_logic.py`.
- Problem: Three findings from a third-party structural audit:
  (1) SoC -- `get_filter_description` was a public helper placed between HTTP
  handlers; lacked `_` prefix used by the other private helpers.
  (2) DRY -- `/results_complete` and `/unmatched_view` duplicated ~10 lines
  of identical `job_id`/`job_context` guard logic.
  (3) SoC -- `fetch_top_albums_async` in `lastfm.py` imported `set_job_stat`
  from `repositories.py` and made 5 direct job-state mutations. An API client
  module should return pure data, not mutate application state. `spotify.py`
  already follows this pattern correctly.
- Fix:
  (1) Renamed to `_get_filter_description` and hoisted above HTTP handlers,
  below `_group_unmatched_by_reason`.
  (2) Extracted `_get_validated_job_context(missing_id_message, expired_error,
  expired_message, expired_details)` returning `(job_id, job_context, None)`
  or `(None, None, error_response)`.
  (3) Removed `job_id` param and `set_job_stat` import from
  `fetch_top_albums_async`. Stats now returned in `fetch_metadata["stats"]`
  dict. `orchestrator._fetch_and_process` extracts and records them.
  Partial-data warning also moved to `fetch_metadata` return path.
- Deviations: Audit claimed ~15-20 lines of duplication; actual overlap was
  ~10 lines. Error titles intentionally differ between routes, so
  `expired_error` was parameterized rather than hardcoded.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-22 - fix(types): resolve 10 Pylance type errors in production code

- Scope: `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`,
  `scrobblescope/utils.py`.
- Problem: Pylance reported 10 type errors across 3 production files:
  (1) `lastfm.py` (7): `metadata` dict inferred as `dict[str, str | int]`
  caused arithmetic and nested-dict assignment failures; `albums` defaultdict
  inferred heterogeneous union on all value accesses.
  (2) `spotify.py` (2): `SPOTIFY_CLIENT_ID/SECRET` typed `str | None` from
  `os.getenv()` but `aiohttp.BasicAuth` requires `str`.
  (3) `utils.py` (1): `loop` assigned inside `try:` block, referenced in
  `finally:` -- possibly unbound if `new_event_loop()` raises.
- Fix: Annotated `metadata: dict[str, Any]` and
  `albums: defaultdict[str, dict[str, Any]]` in lastfm.py; added assert
  guards for Spotify credentials in spotify.py; initialized `loop = None`
  with `if loop is not None:` guard in utils.py.
- Test file type errors (25 across 3 files) assessed as low-impact
  mock-related noise -- deferred.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-21 - refactor/fix: Gemini audit remediation (non-normalization track)

- Scope: `scrobblescope/orchestrator.py`, `scrobblescope/cache.py`,
  `scrobblescope/routes.py`, `scrobblescope/domain.py`,
  new `scrobblescope/errors.py`, `scrobblescope/repositories.py`,
  `tests/services/test_orchestrator_service.py` (+4 tests),
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md` (new doc).
- Problem: A second Gemini Pro audit pass identified four issues beyond the previously
  fixed normalization bugs. Three were confirmed real against the live codebase:
  1. Late slicing: `limit_results` applied after Spotify calls in `_fetch_and_process`.
     For playcount sort the ranking is fully known from Last.fm data; pre-slicing
     to the requested limit eliminates unnecessary Spotify searches on cache misses.
     (Playtime sort cannot be pre-sliced -- ranking requires track duration data.)
  2. Indefinite DB growth: `_batch_lookup_metadata` filtered stale rows at read time
     but no DELETE ever ran. Stale rows accumulated in `spotify_cache` indefinitely.
  3. ERROR_CODES + SpotifyUnavailableError in `domain.py`: a SoC violation -- domain
     logic should not own user-facing message strings or retryability flags.
  A fourth SoC issue not in the original report was also fixed: duplicate release_scope
  -> human-text translation in `routes.py` (inline block in `unmatched_view`
  duplicating `get_filter_description`). A fifth issue (empty-result hallucination)
  was assessed and deferred as near-false-alarm -- the trigger conditions require
  zero cache hits AND every album absent from Spotify, which is extremely unlikely.
- Plan vs implementation: all four confirmed issues fixed as described in
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **114 passed** (110 pre-existing + 4 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - Import graph: `errors.py` is a leaf module (no package imports). Acyclic structure
    preserved. `domain.py` now contains only normalization logic.
- Forward guidance: next sub-track is "sycophantic test coverage" audit (owner to
  elaborate scope). Feature work (top songs, heatmap) blocked until owner assigns a
  future batch number and defines scope. `_cleanup_stale_metadata` is opportunistic and non-fatal;
  monitor logs for "Stale cache cleanup" entries to confirm it fires in production.
  The playtime late-slicing limitation is documented inline in `_fetch_and_process`.

### 2026-02-21 - fix(domain): fix normalization bugs silently excluding non-Latin albums

- Scope: `scrobblescope/domain.py`, `tests/test_domain.py` (9 new tests),
  `tests/services/test_lastfm_logic.py` (new file, 7 tests),
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md` (new doc).
- Problem: A third-party static analysis review (Gemini Pro) identified four
  defects in `domain.py` and a coverage gap in `lastfm.py`. All four were
  confirmed against the live codebase and three had measurable production impact:
  1. `normalize_track_name` used `NFKD + encode("ascii","ignore")`, stripping all
     non-Latin characters to `""`. Any album with Japanese/Cyrillic/etc. track names
     had `len(track_counts) == 1` regardless of distinct tracks played, silently
     failing the `min_tracks` filter and disappearing from results without an
     unmatched entry or any log warning.
  2. `normalize_name` applied its `album_metadata_words` set to the artist string as
     well as the album string, corrupting proper nouns like "New Edition" -> "new"
     and reducing artists named "Special", "Bonus", or "EP" to an empty string.
     Two artists with all-metadata-word names could collide on the same dict key.
  3. `normalize_track_name` used a 13-character hardcoded list while `normalize_name`
     used `str.maketrans(string.punctuation, ...)` covering all 32 ASCII punctuation
     characters. Characters like `&` were inconsistently handled.
  4. `fetch_top_albums_async` (aggregation, timestamp filtering, min_plays/min_tracks)
     had zero test coverage despite being the core business logic function.
- Plan vs implementation: all four defects addressed as described in
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md`. No scope additions or removals.
- Deviations: none.
- Validation:
  - `pytest -q`: **110 passed** (94 pre-existing + 9 new domain tests + 7 new logic tests).
  - `pre-commit run --all-files`: all hooks passed (black reformatted test_domain.py
    on first pass; clean on second).
  - Owner live test: Japanese-title 2025 album (betcover!!) now appears in results
    for listening year 2025 with "Same as release year" filter. Previously absent with
    no unmatched entry. Second validation: same artist's 2021 album (10 unique tracks,
    68 plays) also appeared correctly.
  - "New Edition" self-titled album test: artist key now "new edition" (not "new");
    album deduplication with "(Deluxe Edition)" suffix confirmed still working.
- Forward guidance: no schema, API contract, or route changes. No migration needed.
  The new `test_lastfm_logic.py` file should be extended if `fetch_top_albums_async`
  logic changes (e.g., top-songs feature). Pre-Batch-10 housekeeping is ongoing;
  Batch 10 scope remains TBD by owner.

### 2026-02-20 - fix(tooling): remove transient rotated field from SESSION_CONTEXT status block
- Scope: `scripts/doc_state_sync.py`, `AGENTS.md`.
- Problem: `_build_status_block` wrote `rotated=N` into the managed SESSION_CONTEXT
  block based on the current run's rotation count. The subsequent `--check` always
  recomputed `rotated=0` from the now-clean playbook, causing permanent drift after
  any `--fix --keep-non-current N` run. The workaround required a two-pass sequence.
- Fix: Removed the `Rotated to archive in latest sync run` line from `_build_status_block`.
  The count is still reported on stdout; it is no longer written to a file that `--check`
  re-derives. `--fix --keep-non-current 0` is now a single idempotent command.
- Updated `AGENTS.md` to document the one-pass rotation pattern for agent handoff.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: tooling is stable. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - docs: rotate 4 stale non-current Section 10 entries to archive
- Scope: `PLAYBOOK.md`, `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, `.claude/SESSION_CONTEXT.md`.
- Problem: Four pre-Batch-9 entries (2026-02-19 x2, 2026-02-14 x2) had accumulated
  below `CURRENT-BATCH-END` as `kept_non_current=4` with `rotated=0`, creating
  visible bloat in Section 10.
- Fix: Ran `python scripts/doc_state_sync.py --fix --keep-non-current 0` to flush
  all non-current entries to the archive. Section 10 now contains only active-batch
  entries.
- Deviations: none (purely mechanical doc maintenance).
- Validation:
  - `python scripts/doc_state_sync.py --check`: passed.
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: run `--fix --keep-non-current 0` at each batch boundary to keep
  Section 10 clean.

### 2026-02-20 - WP-7: frontend safety — showToast DOM construction + non-200 fetch guard
- Scope: `static/js/results.js`.
- Problem 1: `showToast` built its HTML via a template-literal string injected with
  `insertAdjacentHTML`. The `message` argument was interpolated without escaping,
  creating an HTML injection pathway if any caller passed server-sourced content.
- Problem 2: `fetchUnmatchedAlbums` piped `fetch()` directly to `.json()` without
  checking `response.ok`. A non-200 response (404, 500, etc.) would be silently
  treated as valid data, surfacing as "No unmatched albums found" instead of an
  error.
- Fix:
  - Rewrote `showToast` to build the toast element tree with `document.createElement`
    / `textContent` / `setAttribute`; eliminated `insertAdjacentHTML` and the unused
    `toastId`. Message content is now set via `.textContent` (XSS-safe).
  - Added `response.ok` guard before `response.json()` in `fetchUnmatchedAlbums`;
    throws `Error("Server error: <status>")` on non-2xx, which the existing `.catch`
    handler surfaces to the user.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: WP-7 complete. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - P1 refactor: extract VALID_FORM_DATA and csrf_app_client fixture
- Scope: `tests/helpers.py`, `tests/conftest.py`, `tests/test_routes.py`.
- Problem: `VALID_FORM_DATA` (the flounder14/2025 form dict for `/results_loading`
  tests) was copy-pasted verbatim 7 times across `test_routes.py`. The 5-line
  CSRF-enabled app + test-client setup was repeated in every CSRF test function.
- Fix:
  - Added `VALID_FORM_DATA` constant to `tests/helpers.py`.
  - Added `csrf_app_client` pytest fixture to `tests/conftest.py`; it creates a
    CSRF-enabled app client (WTF_CSRF_ENABLED not disabled) for CSRF enforcement
    tests.
  - Updated `tests/test_routes.py`: removed `from app import create_app` (now
    unused); imported `VALID_FORM_DATA` from `tests.helpers`; replaced all 7
    inline form dicts with `VALID_FORM_DATA` (or `{**VALID_FORM_DATA, "year": "X"}`
    for year-override cases); replaced all 6 CSRF test inline app setups with the
    `csrf_app_client` fixture parameter.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; pure refactor, no behaviour
    change).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - P1 perf: remove O(n) cache-size scan from cleanup_expired_cache
- Scope: `scrobblescope/utils.py`.
- Problem: `cache_size_mb = sum(len(str(v)) for v in REQUEST_CACHE.values()) / ...`
  ran inside `_cache_lock` on every cleanup call, even when debug logging was
  disabled. This O(n) string-serialization of all cached values held the lock
  unnecessarily and added CPU overhead proportional to cache size.
- Fix: removed the `cache_size_mb` line and simplified the debug log to
  `f"Cache status: {cache_count} entries"`. Count-only logging is sufficient
  for operational visibility; size estimation is not a runtime requirement.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; no test needed for log format).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next P1 item is test boilerplate extraction in
  `test_routes.py` (VALID_FORM_DATA + csrf_app_client fixture).

### 2026-02-20 - P0 fix: delete orphan JOBS entry on thread-start failure
- Scope: `scrobblescope/repositories.py`, `scrobblescope/routes.py`,
  `tests/test_repositories.py`, `tests/test_routes.py`.
- Problem: `create_job()` was called before `start_job_thread()`; on thread-start
  failure the semaphore slot was correctly released by `worker.py`, but the
  `JOBS[job_id]` entry persisted as an orphan until the 2-hour TTL cleanup.
- Fix:
  - Added `delete_job(job_id)` to `repositories.py`:
    `with jobs_lock: JOBS.pop(job_id, None)`.
  - Imported `delete_job` in `routes.py`; called it in the `except` block after
    thread-start failure, before returning the error page.
  - Added 2 tests to `test_repositories.py`:
    `test_delete_job_removes_existing_job`,
    `test_delete_job_on_missing_job_is_noop`.
  - Strengthened existing `test_results_loading_thread_start_failure_renders_error`
    to assert `mock_delete_job.assert_called_once()`.
- Validation:
  - `pytest -q`: **94 passed** (92 pre-existing + 2 new).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: The known orphan-job open risk (SESSION_CONTEXT.md Section 2)
  is now closed. Remaining P1 items: cache_size_mb in `cleanup_expired_cache`,
  and test boilerplate extraction in `test_routes.py`. Next required work package
  is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - doc_state_sync maintenance (remove volatile Last sync commit field)
- Scope: `scripts/doc_state_sync.py`, `.claude/SESSION_CONTEXT.md`.
- Issue: `doc-state-sync-check` pre-commit hook was failing on PR merge to main.
  Root cause: `_build_status_block()` called `git rev-parse --short HEAD` to write
  `Last sync commit: <hash>` into SESSION_CONTEXT.md. On `--check`, the command
  returned the NEW merge commit hash, which did not match the stored hash, causing
  drift detection failure on every merge.
- Fix: Removed `_git_head_short()` function, `subprocess` import, and the
  `Last sync commit` line from `_build_status_block`. The `--check` now validates
  only stable content-level fields (batch number, WP numbers, entry count, newest
  heading). Ran `--fix` to drop the stale `Last sync commit` line from
  SESSION_CONTEXT.md.
- Commit: `cdedd65` fix: remove Last sync commit from doc_state_sync status block.
- Forward guidance: The doc-state-sync-check hook will no longer false-positive on
  merge commits. SESSION_CONTEXT DOCSYNC block is validated on content only.

### 2026-02-20 - WP-6 completed (remove artificial orchestration sleeps)
- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Removed all 5 `await asyncio.sleep(0.5)` calls from `_fetch_and_process`. The
    calls were added as a progress-pacing mechanism but served no functional purpose
    and added a fixed 2.5 s latency overhead to every job.
  - All `set_job_progress` calls and their messages are preserved at the same
    progress values (0, 5, 20, 30, 40, 60, 80, 90, 100), so the loading-page
    progress sequence is unchanged from the user's perspective.
  - `asyncio` import retained: `asyncio.Semaphore`, `asyncio.gather`,
    `asyncio.new_event_loop`, and `asyncio.set_event_loop` are still used.
  - Removed two dead `patch("asyncio.sleep", new_callable=AsyncMock)` lines from
    `test_fetch_and_process_cache_hit_does_not_precheck_spotify` and
    `test_fetch_and_process_sets_spotify_error_from_process_albums` in
    `tests/services/test_orchestrator_service.py`. Those patches were no-ops after
    the sleep removals.
- Deviations and why: none. "Gate with debug-only UX flag" option was not needed;
  the plain removal is simpler and all test coverage is already progress-message
  based, not timing based.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (no count change; two dead patches removed,
    no new tests needed).
- Forward guidance: Next work package is WP-7 (frontend safety and resilience
  polish).

### 2026-02-20 - WP-5 completed (enforce registration-year validation server-side)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added a registration-year guard in `results_loading` immediately after the
    `2002..current_year` bounds check. The guard calls `check_user_exists(username)`
    via `run_async_in_thread` (same helper used by `validate_user`). The result is
    already cached from the blur-validation step, so the call is typically free.
  - If `registered_year` is present and `year < registered_year`, the route
    re-renders `index.html` with an explicit error message citing the registration
    year and the earliest valid year.
  - If the check raises (Last.fm unavailable, network error, etc.), a `WARNING`
    is logged and the route proceeds without blocking the user (fail-open policy).
  - If `registered_year` is `None` (not returned by Last.fm), the check is skipped
    and the route proceeds normally.
  - Updated four existing `results_loading` tests that reach the guard to patch
    `scrobblescope.routes.run_async_in_thread` with a neutral result
    (`{"exists": True, "registered_year": None}`) to avoid live network calls.
  - Added four new tests to `tests/test_routes.py`:
    - `test_results_loading_year_below_registration_year_rejected`
    - `test_results_loading_year_at_registration_year_allowed`
    - `test_results_loading_registration_check_unavailable_proceeds`
    - `test_results_loading_no_registered_year_proceeds`
- Deviations and why: none. Fail-open on service unavailability was the intended
  design from the WP-5 spec (client-side validation already covered the common
  case; server-side guard adds defense-in-depth without blocking on transient errors).
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (88 pre-existing + 4 new).
- Forward guidance: Next work package is WP-6 (remove or gate artificial
  orchestration sleeps).

### 2026-02-20 - WP-4 completed (harden app secret and startup safety)
- Scope: `app.py`, `tests/conftest.py`, `tests/test_app_factory.py` (new), `.env.example`, `README.md`.
- Plan vs implementation:
  - Added `_KNOWN_WEAK_SECRETS = frozenset({"dev", "changeme_in_production", ""})` and `_MIN_SECRET_LENGTH = 16` constants in `app.py`.
  - Added `_validate_secret_key(secret_key: str, is_dev_mode: bool) -> None` in `app.py`. Logic: if key is falsy, in weak set, or shorter than 16 chars -> "weak". In production (`debug_mode=False`): raises `RuntimeError("Refusing to start: ...")`. In dev mode (`DEBUG_MODE=1`): logs `WARNING "SECRET_KEY is missing or insecure. ..."`.
  - Updated `create_app()` to read `_raw_secret = os.getenv("SECRET_KEY", "")`, call `_validate_secret_key(_raw_secret, debug_mode)`, then set `application.secret_key = _raw_secret or "dev"`. "dev" is the dev-mode fallback; in production, `_validate_secret_key` raises before it can be used.
  - `tests/conftest.py` updated: added `import os` + `os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")` before `from app import create_app`. This seeds the guard before `app.py`'s module-level `create_app()` call (which runs at import time).
  - New `tests/test_app_factory.py` with 7 tests: production-fail on missing/dev/changeme/too-short keys; dev-mode warning; strong-key success in both modes.
  - `.env.example` `SECRET_KEY` comment updated to say "REQUIRED in production. Startup fails if missing or set to placeholder."
  - `README.md` setup step 4 comment updated from "Recommended" to "Required in production" with note that `DEBUG_MODE=1` suppresses the check for local dev.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black reformatted `app.py` quote style on first run; clean on second).
  - `pytest -q`: **88 passed** (81 pre-existing + 7 new).
- Commit: `eb13a27` feat: refuse startup on weak SECRET_KEY in production.
- Forward guidance: Next work package is WP-5 (enforce registration-year validation server-side).

### 2026-02-20 - WP-1 correctness fix (slot leak on Thread.start failure)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Issue: WP-1 post-audit check found that `acquire_job_slot()` in `results_loading` was not guarded against failure of `Thread.__init__` or `Thread.start()`. If either raises (e.g. `OSError` under OS-level thread exhaustion), the slot is permanently consumed because `background_task`'s `finally` block never runs. This violates WP-1's acceptance criterion "no leaked active slots after worker exceptions."
- Fix:
  - Added `release_job_slot` to imports in `routes.py`.
  - Wrapped `threading.Thread(...)` and `task_thread.start()` in try/except; on exception: `release_job_slot()`, `logging.exception(...)`, return `index.html` with error message.
  - Added `test_results_loading_thread_start_failure_releases_slot`: patches `Thread` to raise `OSError`, asserts slot is released and index re-rendered.
- Validation:
  - `pre-commit run --all-files`: all hooks passed.
  - `pytest -q`: 77 passed.
- Also: added "callers must not mutate" to `get_cached_response` docstring (latent mutable-reference risk; no active bug since no caller mutates the returned object).

### 2026-02-20 - worker.py architectural decision + product roadmap + CSRF coverage expansion

- Scope: Documentation updates only (`.claude/SESSION_CONTEXT.md`, `EXECUTION_PLAYBOOK_2026-02-11.md`). No runtime code changes yet.
- Decisions made:
  - **Product roadmap confirmed:** Two additional background task types are planned -- "top songs" (Last.fm + possibly Spotify, separate background task/results flow) and "listening heatmap" (Last.fm only, last 365 days, lighter task). This means the `results_loading` acquire->Thread->release pattern will be needed by at least 3 routes.
  - **worker.py chosen as home for concurrency lifecycle:** With multiple background task types incoming, keeping the semaphore and thread-start boilerplate in `repositories.py` would require each new route to duplicate the `acquire -> try Thread.start -> except release` block. A new `scrobblescope/worker.py` leaf module (imports `config` only) will own `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread(target, args=())`. `repositories.py` becomes pure job state CRUD. `start_job_thread()` encapsulates the full try/start/except/release pattern for all callers.
  - **Refactor must precede the 3-commit save-state:** WP-1 originally placed the semaphore in `repositories.py`. The worker.py refactor corrects this before committing; the WP-1 commit will reflect the final architecture.
- CSRF test coverage expansion (also completed this session, before context compaction):
  - Initial WP-3 implementation added 2 CSRF tests covering only `/results_loading`.
  - Expanded to 6 total CSRF tests covering all 4 POST routes:
    - `test_csrf_rejects_post_without_token` (-> `/results_loading` 400)
    - `test_csrf_accepts_post_with_valid_token` (-> `/results_loading` 200)
    - `test_csrf_rejects_results_complete_without_token` (-> 400)
    - `test_csrf_rejects_unmatched_view_without_token` (-> 400)
    - `test_csrf_rejects_reset_progress_without_token` (-> 400)
    - `test_csrf_accepts_reset_progress_with_header_token` (-> `/reset_progress` XHR path with `X-CSRFToken` header, 200)
  - Total tests after expansion: **81 passing**.
- Pending implementation (next agent actions in order):
  1. Create `scrobblescope/worker.py` with semaphore, `acquire_job_slot()`, `release_job_slot()`, `start_job_thread()`.
  2. Remove semaphore/slot functions from `scrobblescope/repositories.py`.
  3. Update imports in `routes.py` and `orchestrator.py` to use `worker`.
  4. Update patch targets in `test_routes.py` and `test_orchestrator_service.py` from `scrobblescope.routes.acquire_job_slot` / `scrobblescope.orchestrator.release_job_slot` -> `scrobblescope.worker.*`.
  5. Run `pre-commit run --all-files` and `pytest -q` (must stay at 81 passing).
  6. Make 3 separate commits: WP-1, WP-2, WP-3.
- Validation: N/A (doc-only session-end update).
- Forward guidance:
  - worker.py is a leaf module -- it must NOT import from `repositories`, `routes`, `orchestrator`, or any higher module (would create cycles).
  - `start_job_thread()` should release the slot and raise on `Thread.start()` failure so routes get a clean exception to handle (mirrors the current try/except pattern in `routes.py`).
  - After the 3 commits are made, next work package is WP-4 (harden app secret and startup safety).

### 2026-02-19 - Fly cold-start recovery validation completed (app + Postgres DB)
- Scope: operational validation of deployed services and documentation refresh (`.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`).
- Plan vs implementation:
  - Confirmed both machines were started (`fly status -a scrobblescope`, `fly status -a scrobblescope-db`).
  - Forced cold state by stopping both machines:
    - `fly machine stop 807339f1595248 -a scrobblescope`
    - `fly machine stop 8e7ed9ad205118 -a scrobblescope-db`
  - Verified both reported `State: stopped` via `fly machine status`.
  - Triggered one end-to-end request:
    - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 1 --timeout-seconds 180`
  - Verified smoke run completion and auto-start behavior for both app and DB machines.
  - Rechecked DB health until all checks passed (`pg`, `role`, `vm`).
- Deviations and why:
  - No code changes were required; this was an operational verification step requested by the owner.
- Validation:
  - Smoke output: `elapsed=18.75s`, `db_cache_enabled=True`, `db_cache_lookup_hits=247`, `db_cache_persisted=0`, `spotify_matched=247`, message `Done! Found 57 albums matching your criteria.`
  - Post-run status: app machine `started`, DB machine `started`, DB checks all passing.
- Forward guidance:
  - Keep this cold-start check as a regression smoke pattern after infra/config changes.
  - If cold-start latency grows, tune DB wake-up retry knobs (`DB_CONNECT_MAX_ATTEMPTS`, `DB_CONNECT_BASE_DELAY_SECONDS`) and/or Fly machine warmness settings.

### 2026-02-19 - Context reconciliation completed (docs parity + cache fallback logging classification)
- Scope: `.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`, `scrobblescope/cache.py`, `tests/test_repositories.py`.
- Plan vs implementation:
  - Re-verified playbook/session claims against the active repo for `init_db.py`, thread model, and cache fallback behavior.
  - Refreshed stale status fields (latest commit snapshot, app.py line count, and current runtime notes).
  - Updated `_get_db_connection()` to log explicit fallback categories:
    - `asyncpg-missing`
    - `missing-env-var`
    - `db-down`
  - Extended DB helper tests to assert those log categories are emitted on each path.
- Deviations and why:
  - No keep-alive thread was added to `app.py`; this is intentional because the current architecture uses per-job daemon worker threads from `results_loading` and avoids additional idle background loops.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed** (2 deprecation warnings from aiohttp connector behavior on Python 3.13.3).
- Forward guidance:
  - Keep Section 2 and `.claude/SESSION_CONTEXT.md` synchronized whenever runtime snapshots (line counts, branch/commit status, logging behavior) change.

### 2026-02-14 - Repository hygiene completed (historical docs archive + README refresh)
- Scope: `docs/history/` (new folder), historical markdown moves, `PLAYBOOK.md`, `README.md`.
- Plan vs implementation:
  - Moved historical docs from repo root into `docs/history/`:
    - `AUDIT_2026-01-10.md`
    - `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`
    - `CHANGELOG_2026-01-04.md`
    - `CHANGELOG_2026-02-10.md`
    - `OPTIMIZATION_SUMMARY.md`
    - `PERFORMANCE_TIMING.md`
    - `Refactor_Plan.md`
    - `TEMPLATE_REFACTOR_SUMMARY.md`
  - Updated playbook references to `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`.
  - Refreshed `README.md`:
    - run instructions now show `python app.py` (recommended) and `python run.py` (optional launcher)
    - project structure updated to current modular layout + `docs/history/`
    - roadmap/status text updated to reflect current post-refactor state
- Deviations and why:
  - Keep a shim at `EXECUTION_PLAYBOOK_2026-02-11.md` to preserve a stable handoff entrypoint.
- Forward guidance:
  - Keep new planning/audit/changelog docs in `docs/history/` unless a document is an active operator runbook.
  - Keep playbook and session-context docs at predictable top-level locations for fast bootstrap.

### 2026-02-14 - Cache wake-up hardening completed (DB connect retry/backoff + docs refresh)
- Scope: `scrobblescope/cache.py`, `tests/test_repositories.py`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Added exponential-backoff DB connection retries in `_get_db_connection()` to reduce false cache bypass during Fly Postgres wake-up windows.
  - Added two DB helper tests:
    - retry-then-success path
    - retry-exhaustion path
  - Updated existing connect-failure test to force single-attempt behavior (`DB_CONNECT_MAX_ATTEMPTS=1`) for deterministic assertions.
  - Refreshed handoff docs for the new test count and operational behavior.
- Deviations and why:
  - No orchestration/routing behavior changes were needed; hardening was isolated to cache connection setup and DB helper tests.
- Additions beyond plan:
  - Added env-tunable retry knobs:
    - `DB_CONNECT_MAX_ATTEMPTS` (default `3`)
    - `DB_CONNECT_BASE_DELAY_SECONDS` (default `0.25`)
  - Live Fly verification confirmed:
    - app cache hits persisted after DB stop/start
    - DB app `scrobblescope-db` uses `FLY_SCALE_TO_ZERO=1h`, explaining suspended/stopped state after idle periods.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
  - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`: **PASS** (`db_cache_enabled=True`, `db_cache_lookup_hits=247`).
- Forward guidance:
  - If first-request latency after idle is a concern, either increase retry knobs or adjust/remove DB `FLY_SCALE_TO_ZERO`.
  - Keep periodic smoke checks as operational validation for cache persistence and warm-hit behavior.
  - Resolve DB app staged secrets drift (`fly secrets deploy -a scrobblescope-db`) to avoid config ambiguity.

### 2026-02-14 - Frontend responsiveness polish completed (toggle placement + mobile table scaling)
- Scope: `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`, `static/css/unmatched.css`, `static/css/error.css`, `templates/results.html`.
- Plan vs implementation:
  - Standardized dark-mode toggle to a compact fixed bottom control across all page CSS bundles.
  - Improved `index.html` mobile fit by tightening spacing, typography, and card/logo sizing at mobile breakpoints.
  - Improved `results.html` mobile readability by shrinking table density, making actions stack cleanly, and reducing album-art footprint.
  - Added `results-table` class in template for targeted responsive behavior.
  - Centered decade pills in `index` filter UI.
- Deviations and why:
  - To improve fit on common phones, responsive rules were applied up to `max-width: 767.98px` for index/results rather than only `575.98px`.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - If users still report table crowding on very small devices, next step is card-style row rendering for results instead of a dense 5-column table.
  - Consider extracting shared toggle CSS into one common stylesheet to reduce cross-file duplication.

### 2026-02-14 - Post-Batch-8 hardening completed (low-severity gap closure + test layout split)
- Scope: `tests/test_routes.py`, `tests/conftest.py`, `tests/helpers.py` (new), `tests/services/` (new split files), `EXECUTION_PLAYBOOK_2026-02-11.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Closed previously identified low-severity gaps:
    - Added direct route tests for `/unmatched_view` (missing `job_id`, missing job, success render path).
    - Added explicit tests for app-level 404 and 500 handlers.
  - Reduced test coupling to `conftest.py` internals:
    - Moved shared constants/mock helpers into `tests/helpers.py`.
    - Updated tests to import from `tests.helpers` rather than `conftest`.
  - Split monolithic service test file:
    - Removed `tests/test_services.py`.
    - Added `tests/services/test_lastfm_service.py` (4 tests).
    - Added `tests/services/test_spotify_service.py` (3 tests).
    - Added `tests/services/test_orchestrator_service.py` (10 tests).
- Deviations and why:
  - No runtime code changes were required. This was a test architecture and coverage hardening pass only.
  - Added one extra test category beyond the initial gap list (500 handler integration path) because this was explicitly untested and low effort/high confidence.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **64 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - Subpackage migration should be sequenced **after** the next feature-heavy batch set (Batch 9+) stabilizes, not before. Keep current flat module layout while churn is high; cut to subpackages once contracts settle.
  - Keep route-handler coverage and helper-module pattern as baseline for future test additions.

### 2026-02-13 - Operational config fix (Fly machine autostop)
- Scope: `fly.toml`.
- Issue:
  - Fly log showed autostop with `0 out of 1 machines left running` because `min_machines_running` was set to `0`.
- Change:
  - Updated `[http_service] min_machines_running = 1` to keep one machine warm.
- Notes:
  - This log means capacity scaling, not cache overflow.
  - In-memory caches (`REQUEST_CACHE`, `JOBS`) live in RAM on the app VM and are lost on machine stop/restart.
  - Persistent Spotify metadata cache lives in Fly Postgres (`spotify_cache`) via `DATABASE_URL`.
