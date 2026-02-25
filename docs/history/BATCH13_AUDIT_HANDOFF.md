# Agent Hand-Off Prompt -- BATCH13 Pre-Approval Audit

You are picking up a pre-batch audit task on **ScrobbleScope**, a Flask +
Python 3.13 web app (Last.fm scrobbles + Spotify enrichment). Your job is to
audit **BATCH13_PROPOSAL.md** for technical accuracy before the owner approves
it for execution. This is NOT an implementation task -- read, verify, report.

---

## 1. Orientation (read these first, in order)

1. `AGENTS.md` -- project rules, commit format, doc sync, test quality rules.
2. `.claude/SESSION_CONTEXT.md` -- current project state snapshot (260 tests,
   no active batch). If absent, use PLAYBOOK.md Section 3 as source of truth.
3. `PLAYBOOK.md` Section 3 (no active batch) + Section 4 (execution log).
4. `BATCH13_PROPOSAL.md` -- **the document being audited**. Read it in full
   before starting any verification work.

---

## 2. Environment

- **OS:** Windows 11. PowerShell terminals.
- **Python:** 3.13.3, venv-based.
- **Branch:** `wip/pc-snapshot` (HEAD: `f4e3e4c`).
- **Remote:** `origin/wip/pc-snapshot` is in sync.

**Critical:** bare `pytest` and `pre-commit` are NOT on PATH. Always use:

```powershell
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m pre_commit run --all-files
.\venv\Scripts\python.exe scripts/doc_state_sync.py --fix
```

The app runs locally without Postgres (`DATABASE_URL` not set -- in-memory
cache only).

---

## 3. Pre-work checklist

Before starting verification:

1. `.\venv\Scripts\python.exe -m pytest -q` -- must show **260 passed**. This
   confirms the codebase the proposal targets is in the expected state.
2. `.\venv\Scripts\python.exe -m pre_commit run --all-files` -- must pass.
3. Confirm you are on branch `wip/pc-snapshot`.

---

## 4. Audit work packages (strict order)

Complete each WP fully before starting the next. Record all findings --
including "confirmed correct" verdicts -- in the report (see WP-4).

---

### WP-1: Verify line references and code structure in `orchestrator.py`

**Goal:** Confirm every line number cited in the proposal matches the actual
code and that the proposed extraction boundaries are clean.

**Key files:** `scrobblescope/orchestrator.py`

**Critical details:**

Check each reference from the proposal:

| Proposal claim | What to verify |
|---|---|
| `_fetch_spotify_misses()` at L192-387 | Function def at L192; closing bracket at L387 |
| Search phase at L219-290 | Locate the search loop; note actual start/end |
| Batch-detail phase at L292-385 | Locate the batch loop; note actual start/end |
| Token-acquisition block at L199-217 | Locate the early-exit block; note actual end |
| `_fetch_and_process()` at L579-808 | Function def at L579; closing bracket at L808 |
| `_record_lastfm_stats` replaces L632-642 | Locate the stat-recording block |
| `_apply_pre_slice` replaces L664-711 | Locate the two pre-slice if-blocks |
| `_detect_spotify_total_failure` replaces L739-747 | Locate the unmatched-check block |
| `_apply_post_slice` replaces L759-768 | Locate the post-slice truncation block |
| `_classify_exception_to_error_code` replaces L783-793 | Locate the exception-to-code mapping |

For each, record: actual line range, whether the proposal boundary is exact or
off-by-N, and whether any inline closure or captured variable was overlooked.

Verify no name collision: none of the 7 proposed new private functions
(`_run_spotify_search_phase`, `_run_spotify_batch_detail_phase`,
`_record_lastfm_stats`, `_apply_pre_slice`, `_detect_spotify_total_failure`,
`_apply_post_slice`, `_classify_exception_to_error_code`) already exist in
`orchestrator.py` or any other module.

---

### WP-2: Verify test coverage claims for WP-2 through WP-4

**Goal:** Confirm the proposal's assertions that no existing tests require
modification after extracting the private helpers.

**Key files:** `tests/services/test_orchestrator_service.py`,
`tests/helpers.py`, `tests/conftest.py`

**Critical details:**

1. **Mock patch targets** -- The proposal claims "all existing patches target
   module-level names that remain unchanged." Verify:
   - Search `test_orchestrator_service.py` for every `patch(` call. Confirm
     each patched path (`scrobblescope.orchestrator.search_for_spotify_album_id`,
     `scrobblescope.orchestrator.fetch_spotify_album_details_batch`, etc.)
     targets a name that will survive the WP-2/WP-3 extractions unchanged.
   - Any patch on a currently-inline block (rather than a module-level import)
     would NOT survive extraction and would need updating. Flag any such cases.

2. **Test split table** -- The proposal lists approximate line ranges for each
   of the four new test files. Verify the named test functions exist in
   `test_orchestrator_service.py` and fall roughly within the stated ranges:
   - `test_process_albums_cache_hit_skips_spotify` (stated ~L22)
   - `test_cleanup_stale_metadata_issues_delete` (stated ~L532)
   - `test_fetch_and_process_cache_hit_does_not_precheck_spotify` (stated ~L422)
   - `test_matches_release_criteria_adversarial` (stated ~L861)
   - Flag any test function the proposal assigns to the wrong split file.

3. **Shared test infrastructure** -- Verify `tests/helpers.py` exports exactly
   the names the proposal requires: `TEST_JOB_PARAMS`, `VALID_FORM_DATA`,
   `NoopAsyncContext`, `make_response_context`.

4. **worker.py WP-1 testability** -- The proposal patches `_JOB_SEMAPHORE` to
   create isolated semaphore state. Verify `_JOB_SEMAPHORE` is a
   module-level name in `worker.py` that is patchable via
   `unittest.mock.patch('scrobblescope.worker._JOB_SEMAPHORE', ...)`.

---

### WP-3: Verify WP-5 DRY retry extraction design

**Goal:** Confirm the proposed `retry_with_semaphore` utility is compatible
with the actual retry loops in `lastfm.py` and `spotify.py`.

**Key files:** `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`

**Critical details:**

1. **`lastfm.py` return protocol** -- Locate the `fetch_once()` inner function in
   `fetch_recent_tracks_page_async`. Confirm it returns a 2-tuple
   `(data, retry_after)` (not a 3-tuple), and that `data is not None` is the
   success condition. Confirm `ValueError` is re-raised bare (not wrapped).

2. **`spotify.py` return protocol** -- Locate `search_once()` in
   `search_for_spotify_album_id` and the batch attempt function in
   `fetch_spotify_album_details_batch`. Confirm both return a 3-tuple
   `(result, retry_after, done)` with an explicit `done` flag.

3. **Jitter formula** -- The proposal states the jitter is
   `(abs(hash((artist, album, attempt))) % 200) / 1000.0`. Locate this
   expression in `spotify.py` and confirm it is exact.

4. **Backoff values** -- Proposal states lastfm uses
   `min(0.25 * (attempt + 1), 1.0)` and spotify uses a fixed `1.0`. Verify
   both against the actual code.

5. **Import path** -- Confirm `utils.py` is already imported in both
   `lastfm.py` and `spotify.py` (i.e., adding `retry_with_semaphore` there
   does not introduce a new dependency for either caller).

---

### WP-4: Check convention compliance and write audit report

**Goal:** Verify the proposal follows project conventions, flag any risks or
omissions, and write a findings report.

**Key files:** `BATCH13_PROPOSAL.md`, `AGENTS.md`

**Critical details:**

1. **Acceptance criteria completeness** -- For each WP, confirm every acceptance
   criterion is objectively verifiable (measurable by pytest count, grep, or
   diff -- not subjective).

2. **Doc sync step** -- Confirm the validation checklist in the proposal
   includes `doc_state_sync.py --fix` and the PLAYBOOK/SESSION_CONTEXT update
   steps per AGENTS.md conventions.

3. **Commit message examples** -- The proposal lists four example commit
   messages. Verify each conforms to Conventional Commits format (max 72-char
   subject, imperative mood, no trailing period).

4. **WP ordering** -- Confirm the stated dependency `WP-3 → WP-4` (test split
   must follow source extraction) is correctly reflected throughout. Confirm
   WP-5 is correctly stated as independent.

5. Write the audit report to `docs/history/BATCH13_AUDIT_2026-02-23.md`.
   Structure:
   ```
   # BATCH13 Pre-Approval Audit (2026-02-23)
   ## Verdict: [APPROVED / APPROVED WITH CORRECTIONS / NEEDS REWORK]
   ## WP-1 findings (line references)
   ## WP-2 findings (test coverage claims)
   ## WP-3 findings (retry extraction)
   ## WP-4 findings (convention compliance)
   ## Summary of corrections applied
   ```
   For each finding state: claim verified / discrepancy found (with evidence).

6. If any discrepancies were found, apply the corrections directly to
   `BATCH13_PROPOSAL.md` before committing.

---

## 5. Commit and doc-update rules

Follow `AGENTS.md` for all commit formatting (Conventional Commits, type list,
procedure, co-author prohibition).

This audit is a **side-task** (no active batch). Commit rules:
- Commit the audit report and any proposal corrections together as one commit
  after WP-4.
- Log entry goes **after** the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker in
  PLAYBOOK Section 4 (not inside -- see AGENTS.md "Side-Task Handling").
- Update SESSION_CONTEXT.md Section 2 only if the test count changed.
- Run `.\venv\Scripts\python.exe scripts/doc_state_sync.py --fix` after the
  PLAYBOOK entry.
- Do NOT run `--keep-non-current 0`.

Suggested commit message if no corrections needed:
```
docs(audit): add BATCH13 pre-approval audit report
```

Suggested commit message if corrections were applied:
```
docs(audit): add BATCH13 audit report and apply corrections to proposal
```

---

## 6. Behavioral notes from outgoing agent

These are hard-won lessons from prior sessions. Read carefully.

### PowerShell multi-line commit messages

PowerShell mangles multi-line strings in `git commit -m`. Use a temp file:

```powershell
# Write message to file, commit with -F, delete file
Set-Content -Path commit_msg.txt -Value "type(scope): subject`n`nbody text"
git commit -F commit_msg.txt
Remove-Item commit_msg.txt
```

### pre-commit exit code artifact

`pre-commit` may show exit code 1 on first run if `black` or `isort` reformats
a file. This is expected -- it auto-fixes and exits non-zero. **Re-stage the
fixed files and run pre-commit again.** Second run will pass.

### Pylance errors are flaky

VS Code may show Pylance type errors that are not real. Trust `pytest` and
`pre-commit` as ground truth, not Pylance squiggles.

### File edit context matching

When making surgical edits to existing files, include 3-5 lines of unchanged
context before and after your target to ensure a unique match. If a replace
fails, the most common cause is a whitespace, indentation, or content mismatch
from a prior edit in the same session.

### doc_state_sync marker placement

Batch log entries go **inside** DOCSYNC markers; side-task entries go **after**
the end marker. The `--check` pre-commit hook will catch placement errors before
they reach a commit.

---

## 7. Test count tracking

| Checkpoint | Expected count | Notes |
|------------|----------------|-------|
| Pre-work baseline | 260 | Must match; abort if mismatch |
| After audit + report commit | 260 | Audit makes no code changes; count unchanged |

---

## 8. Key file locations for reference

| File | What to know |
|------|-------------|
| `BATCH13_PROPOSAL.md` | The document being audited; edit only to apply corrections |
| `scrobblescope/orchestrator.py` | Primary verification target; ~846 lines |
| `tests/services/test_orchestrator_service.py` | 1,270-line test file the proposal splits |
| `scrobblescope/lastfm.py` | WP-3 retry loop verification |
| `scrobblescope/spotify.py` | WP-3 retry loop verification |
| `tests/helpers.py` | Shared test fixtures; verify exports match proposal claims |
| `docs/history/BATCH13_AUDIT_2026-02-23.md` | Output report; create in WP-4 |

---

## 9. Start

Notify the owner that you are oriented, then begin with the pre-work checklist
(Section 3) and execute WP-1. This is a read-heavy task -- do not modify any
source files until WP-4 (corrections only if discrepancies are found).
