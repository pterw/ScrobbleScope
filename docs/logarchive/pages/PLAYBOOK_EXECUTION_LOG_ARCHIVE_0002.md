<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0002

### 2026-03-03 - Batch 16 definition written and activated (Batch 16 activation)

**Scope:** Define Batch 16 and activate it in PLAYBOOK + SESSION_CONTEXT.

**Plan:** Write `BATCH16_DEFINITION.md` incorporating audit corrections (stat key
fix, size caps removed, MEMORY.md references clarified as agent-private). Move to
`docs/history/definitions/`. Activate Batch 16 in PLAYBOOK Section 3. Update
SESSION_CONTEXT Section 2. Update HANDOFF_PROMPT.md and MEMORY.md for handoff.

**Implementation:** Definition written; audit findings applied (verdict key
`cache_hits` corrected to `db_cache_lookup_hits`, size caps removed per owner
instruction, `memory/MEMORY.md` removed from formal acceptance criteria). Definition
placed at `BATCH16_DEFINITION.md` (root; moves to archive at batch close-out). PLAYBOOK and
SESSION_CONTEXT activated. HANDOFF_PROMPT and MEMORY updated for clean handoff.

**Deviations:** None.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-0 is next: create `scripts/testing/` and `scripts/dev/`
directories, move `smoke_cache_check.py` via `git mv`, update AGENTS.md and
SESSION_CONTEXT path references. No logic changes in WP-0.

### 2026-03-03 - Fix SESSION_CONTEXT.md commit convention and stage accumulated changes

**Scope:** Side-task -- documentation and gitignore fix, no code changes.

**What:** SESSION_CONTEXT.md was never staged in the two previous side-task commits
(`c4bf737`, `4f1cf6a`) despite commit messages implying it. SESSION_CONTEXT.md has
been git-tracked since before `edee612` (when `.claude/` was added to .gitignore).
The `.gitignore` entry `.claude/` is misleading -- SESSION_CONTEXT.md is grandfathered
in as a tracked file. Fix: update `.gitignore` to `.claude/*` + `!.claude/SESSION_CONTEXT.md`
so the exception is explicit. Fix AGENTS.md: remove incorrect "SESSION_CONTEXT is
gitignored" language. Stage the accumulated SESSION_CONTEXT.md changes (Batch 15 state
update, Section 8 browser MCP note, Section 8 local Postgres note).

**Why:** SESSION_CONTEXT.md is the shared cross-agent dashboard. All agents (Gemini,
Copilot, Codex, Claude Code) bootstrap from it. Leaving it uncommitted means every agent
starts with stale branch, test count, and batch status. The gitignore fix makes the
tracked-exception visible and prevents future agents from falsely concluding the file
is machine-local.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. BATCH16_PROPOSAL.md written; awaiting owner review.

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
