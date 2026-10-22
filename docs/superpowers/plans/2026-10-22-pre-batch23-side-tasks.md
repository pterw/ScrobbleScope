# Pre-Batch-23 Side Tasks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the cheap fixes and filings queued for the pre-Batch-23 tranche: the F-B22-3 re-point, a validated Last.fm pre-check timeout, two logging-stream fixes, a flaky route test, wrong-mode refusals on two job endpoints, and the 2026-10-21 architecture review tracked with one finding per open item.

**Architecture:** One side-task branch, `fix/pre-batch23-side-tasks`, cut from `main` at 61fb4fc. Eight tasks, each one atomic commit with its own untagged PLAYBOOK Section 4 entry. Behaviour changes are test-first with a planted-defect (mutation) proof. No new module, no new dependency, no template or CSS change.

**Tech Stack:** Python 3.13, Flask, pytest, subprocess-based import tests, docsync (`scripts/doc_state_sync.py`).

**Owner rulings this plan carries (verbatim where quoted):**
- 2026-10-21, on the queued items: "RE: recommendations, yes. Sounds good." (Q1: keep the capability model for Last.fm jobs and re-point F-B22-3 to Batch 23 WP-3, session-binding export jobs; Q4: no concurrency cap, add `LASTFM_PRECHECK_TIMEOUT_SECONDS` to `.env.example` and validate it is greater than 0.)
- 2026-10-21, logging: "I think skpping ANSI altogether might be worthwhile. Severity-based noise filtering is already in place, and would need zero new maintenance or test surfaces." (So `os.system("")` goes and no colour is added.)
- 2026-10-21, architecture review: "Cheap fixes first -- anything else that comes before the scope in the tranche should be filed as a potential finding/candidate. Goal is to finish the tranch and avoid scope creep".
- 2026-10-22: the side-task PR runs next; the Batch 23 WP-0 close-out runs "After the tranche, before WP-1".
- Standing: "tests assert intended behaviour, not the code as written; a false green is worse than a true red."

## Global Constraints

- Work only in the worktree `C:/ssw/side` on branch `fix/pre-batch23-side-tasks`. From a linked worktree use the primary checkout's tools: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"` (written `PY` below), and its `pytest.exe` / `pre-commit.exe` beside it.
- Side-task logging (AGENTS.md "Side-Task Handling"): every commit adds one dated entry `### 2026-10-22 - <title>` directly after `<!-- DOCSYNC:CURRENT-BATCH-END -->` in `docs/agents/PLAYBOOK.md` Section 4, with no `(Batch N WP-X)` tag. The entry covers scope, owner intent, what changed, deviations, edited existing tests (by name, or "none"), and `Validation: \`pytest -q\` -- **N passed**.` Never hand-move entries across DOCSYNC markers.
- **Commit procedure (every task):** (1) Section 4 entry written; (2) `PY -m pytest -q`, note N; (3) `PY scripts/doc_state_sync.py --fix --test-count N`; (4) stage the named paths only (never `git add -A` or `git add .`), including `.claude/SESSION_CONTEXT.md`, `docs/agents/FINDINGS.md`, `config/docsync.toml`, `docs/history/findings/FINDINGS_ARCHIVE.md` and `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` whenever `--fix` changed them; (5) `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/ruff.exe" format <new or edited .py files>`, then `pre-commit run --all-files` (re-stage anything a hook rewrote); (6) `PY scripts/doc_state_sync.py --check` exits 0 (the root `BATCH23_DEFINITION.md` warning is expected); (7) `git commit`. The frontend gate (`PY C:/ssw/tools/with_browser_lock.py PY scripts/dev/frontend_gate.py`) runs before the commits of Tasks 3, 4 and 6 (Tasks 3 and 4 edit `app.py`, which the gate's server imports) and the final gate-runner pass; the other tasks touch no served page or asset.
- Commit messages: Conventional Commits, imperative subject, at most 72 characters, body explains why. No `Co-authored-by`, no "Generated with" line, whatever a harness suggests.
- Never `--no-verify`. Never `git commit --amend`, `rebase` or `reset`: fix a mistake with a follow-up commit. Never `sed -i`. Never `git checkout` a file holding uncommitted work. The one sanctioned hook escape is `SKIP=doc-state-sync-check git commit`, and only for a commit that stages docsync control-plane code (none here).
- Tests assert intended behaviour. Every new test is proven red first: either against the unfixed code (test-first) or by a planted defect that is then reverted. Record each proof (command, the failing line) in the task report.
- Findings: format and status rules are `docs/agents/issue-tracker.md` and AGENTS.md "Finding-Writing Rules". A resolved finding carries `- [x] **Status:** resolved` and a `**Completed:** 2026-10-22` line (DOC023); `--fix` rotates it to `docs/history/findings/FINDINGS_ARCHIVE.md`. An open finding's body must not contain the unnegated words "resolved" or "no action" (DOC023 reads them as a terminal outcome); write "fixed by F-B23-50" or "closed" instead where a body refers to a resolved finding. Reserved ids: F-B23-48, F-B23-50, F-B23-51 .. F-B23-56. F-B23-49 was reserved for PR #262 and never used; do not use it.
- ASCII only in Markdown (`--`, straight quotes). Cite functions by name, not line number.
- Grep before claiming anything does not exist.
- Count of tracked test modules, when a doc states it: `git ls-files tests | grep -c '/test_[^/]*\.py$'` (100 at 61fb4fc; Task 2 adds `tests/test_config.py`, making 101). SESSION_CONTEXT's Tests row and the FINDINGS header hold that count by hand.

---

### Task 0: Commit this plan and point Section 3 at it

**Files:**
- Create: `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md` (this plan, with any review fixes the dispatch names)
- Modify: `docs/agents/PLAYBOOK.md` (Section 3, Section 4)

- [ ] **Step 1:** Copy the plan file into place, applying the review fixes named in the dispatch.
- [ ] **Step 2:** In PLAYBOOK Section 3, "Before WP-1" bullet: after the sentence about PR #7's further rounds, add: "A side-task PR of cheap fixes from the 2026-10-21 architecture review and the logging audit runs next (branch `fix/pre-batch23-side-tasks`, plan `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md`); the documentation refresh merges last." In the "WP-0 close-out" bullet, add a final sentence: "It runs after the tranche, before WP-1 (owner ruling 2026-10-22)." Leave "**Next action:** WP-0 is next." unchanged: DOC007 reads the definition's next-package line, and WP-0 is still the next work package.
- [ ] **Step 3:** Section 4 entry `### 2026-10-22 - Plan the pre-Batch-23 side tasks`.
- [ ] **Step 4:** `git add docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md` before `--fix`: DOC001 resolves Section 3's backticked paths through `git ls-files` (the index), so an unstaged plan file fails it.
- [ ] **Step 5:** Commit procedure; message `docs(plan): Plan the pre-Batch-23 side tasks`.

---

### Task 1: Re-point F-B22-3 to Batch 23 WP-3

**Files:**
- Modify: `docs/agents/FINDINGS.md` (F-B22-3)
- Modify: `scrobblescope/routes/api.py` (`release_checks` docstring, the `/api/release_checks` endpoint -- the function whose docstring says "F-B22-3 records that as an open question for the owner")
- Modify: `BATCH23_DEFINITION.md` (header amendment line, WP-3 checklist)
- Modify: `docs/agents/PLAYBOOK.md` (Section 4)

Live hits for `F-B22-3` at 61fb4fc (sweeper): `docs/agents/FINDINGS.md` (the heading), `scrobblescope/routes/api.py` (the docstring above). The hits in `tests/test_docsync_cli.py` and `tests/test_docsync_findings.py` are synthetic fixture ids, not this finding: leave them. `docs/history/logs/BATCH22_LOG.md` and `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` are point-in-time: leave them.

- [ ] **Step 1:** FINDINGS F-B22-3: keep the body; append one paragraph: "Owner ruling 2026-10-21 (Q1): Last.fm jobs keep the capability model -- the 128-bit job ID is the bearer token, and their results are public listening data. Export jobs from Batch 23 hold an uploaded private history, so WP-3 binds them to the session that created them. Re-pointed to Batch 23 WP-3." Replace the status line with `Status: open (P2), re-pointed to Batch 23 WP-3 (owner ruling 2026-10-21). Source: Graphify bot review, PR #232, 2026-09-14.` Keep the existing status-line shape (this finding does not use the checkbox form; do not convert it). The new paragraph and status line must not contain the unnegated words "resolved" or "no action" (DOC023; see Global Constraints).
- [ ] **Step 2:** `api.py` docstring: replace "F-B22-3 records that as an open question for the owner rather than a decision taken in this endpoint alone." with "That is the owner's ruling for Last.fm jobs (F-B22-3, 2026-10-21); Batch 23 WP-3 binds export jobs to their session." Docstring only; no code change.
- [ ] **Step 3:** `BATCH23_DEFINITION.md`: in the header's amendment list, after the last "**Scope amended 2026-10-20**" paragraph, add `**Scope amended 2026-10-21** (owner ruling on F-B22-3): export jobs are bound to the session that created them (WP-3). Last.fm jobs keep the job ID as their capability. No work package is added.` In WP-3, after the "The export job reaches the cache only through `process_albums`" item, add a checklist item: `- [ ] **Export jobs belong to their session** (amended 2026-10-21, F-B22-3). An export job's id is recorded in the creating session, and every endpoint that reads a job (progress, results, unmatched, heatmap data, release checks) refuses an export job whose id is not that session's, with the same 404 a missing job gets. Last.fm jobs are unchanged. Acceptance adds: an export job's id read from a second client session gets 404 on each of those endpoints.`
- [ ] **Step 4:** Run `PY scripts/doc_state_sync.py --check` before the commit procedure; a DOC error here means a declared citation moved -- report it, do not work around it.
- [ ] **Step 5:** Section 4 entry `### 2026-10-22 - F-B22-3 moves to Batch 23 WP-3`; commit procedure; message `docs(findings): Re-point F-B22-3 to Batch 23 WP-3`.

---

### Task 2: Validate the Last.fm pre-check timeout

**Files:**
- Modify: `scrobblescope/config.py`
- Create: `tests/test_config.py`
- Modify: `.env.example`, `.claude/SESSION_CONTEXT.md` (Key runtime facts bullet for `LASTFM_PRECHECK_TIMEOUT_SECONDS`), `docs/agents/PLAYBOOK.md`

**Interfaces:**
- Produces: `scrobblescope.config._positive_seconds(name: str, default: str) -> float`; `config.LASTFM_PRECHECK_TIMEOUT_SECONDS` is its result. `scrobblescope/routes/__init__.py` imports the constant unchanged.

Why: a zero or negative value makes every pre-check time out at once, so every form submission is refused "try again"; `nan` never compares greater than the elapsed time and `inf` removes the bound. Fail fast at startup with the variable's name instead.

- [ ] **Step 1: Write the failing tests** in `tests/test_config.py`:

```python
"""Tests for scrobblescope.config: environment values read at import."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scrobblescope import config

REPO_ROOT = Path(__file__).resolve().parents[1]
NAME = "LASTFM_PRECHECK_TIMEOUT_SECONDS"


def test_positive_seconds_uses_the_default_when_unset(monkeypatch):
    """An unset variable takes the default."""
    monkeypatch.delenv(NAME, raising=False)
    assert config._positive_seconds(NAME, "5") == 5.0


def test_positive_seconds_treats_a_blank_value_as_unset(monkeypatch):
    """`NAME=` in a .env file means "not set", as for MUSICBRAINZ_CONTACT."""
    monkeypatch.setenv(NAME, "  ")
    assert config._positive_seconds(NAME, "5") == 5.0


def test_positive_seconds_reads_a_fractional_override(monkeypatch):
    """An override is read as a float, so sub-second budgets work."""
    monkeypatch.setenv(NAME, "2.5")
    assert config._positive_seconds(NAME, "5") == 2.5


@pytest.mark.parametrize("raw", ["0", "-1", "nan", "inf", "-inf", "five"])
def test_positive_seconds_refuses_a_value_that_cannot_bound_a_wait(monkeypatch, raw):
    """Zero, negative, non-finite and non-numeric values all refuse, naming the variable."""
    monkeypatch.setenv(NAME, raw)
    with pytest.raises(ValueError) as excinfo:
        config._positive_seconds(NAME, "5")
    assert NAME in str(excinfo.value)
    assert repr(raw) in str(excinfo.value)


def _import_config_in_child(value):
    """Import scrobblescope.config in a fresh interpreter with NAME=value."""
    env = {**os.environ, NAME: value}
    return subprocess.run(
        [
            sys.executable,
            "-c",
            f"from scrobblescope import config; print(config.{NAME})",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_the_precheck_timeout_is_read_through_the_validator():
    """The module constant itself refuses a bad value at import and reads a good one."""
    refused = _import_config_in_child("0")
    assert refused.returncode != 0
    assert NAME in refused.stderr

    accepted = _import_config_in_child("0.25")
    assert accepted.returncode == 0, accepted.stderr
    assert accepted.stdout.strip() == "0.25"
```

- [ ] **Step 2: Run to verify it fails.** `PY -m pytest tests/test_config.py -q`. Expected: every test fails (`AttributeError: module 'scrobblescope.config' has no attribute '_positive_seconds'`; the child-process test fails because "0" is accepted, exit 0).
- [ ] **Step 3: Implement** in `scrobblescope/config.py`: add `import math` beside `import os`, and above the pre-check comment block:

```python
def _positive_seconds(name, default):
    """Return the environment variable *name* as a positive number of seconds.

    A blank or unset variable takes *default*. Zero, a negative number, a
    non-finite value or text that is not a number raises ``ValueError``
    naming the variable: such a value cannot bound a wait (zero refuses every
    lookup at once, ``nan`` and ``inf`` never time out), so startup refuses it
    rather than serve a form that can never pass, or never stops waiting.
    """
    raw = os.getenv(name, "").strip() or default
    try:
        value = float(raw)
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive number of seconds; got {raw!r}.")
    return value
```

and replace the `LASTFM_PRECHECK_TIMEOUT_SECONDS = float(...)` assignment with `LASTFM_PRECHECK_TIMEOUT_SECONDS = _positive_seconds("LASTFM_PRECHECK_TIMEOUT_SECONDS", "5")`. Keep the comment above it and add one sentence: "It must be a positive number; startup refuses anything else."

- [ ] **Step 4: Run to verify it passes.** `PY -m pytest tests/test_config.py tests/test_precheck.py tests/test_precheck_routes.py -q`. Expected: all pass.
- [ ] **Step 5: Planted defects** (each reverted after it fails; copy `config.py` aside first, never `git checkout` it): (a) `value <= 0` -> `value < 0`: the `"0"` case and the child-process test fail. (b) drop `not math.isfinite(value) or`: the `nan`, `inf` and `five` cases fail. (c) assign `LASTFM_PRECHECK_TIMEOUT_SECONDS = float(os.getenv(...))` again: the child-process test fails.
- [ ] **Step 6: `.env.example`:** after the `# MAX_RETRY_AFTER_SECONDS=30` line add:

```
# Longest, in seconds, one Last.fm pre-check lookup (user exists, profile public) may take;
# a positive number, or startup refuses.
# LASTFM_PRECHECK_TIMEOUT_SECONDS=5
```

- [ ] **Step 7: SESSION_CONTEXT** Key runtime facts, the `LASTFM_PRECHECK_TIMEOUT_SECONDS` bullet: add "It must be positive and finite; startup refuses any other value (`config._positive_seconds`)."
- [ ] **Step 8:** Section 4 entry `### 2026-10-22 - The Last.fm pre-check timeout must be a positive number`; commit procedure (N rises by 10 (measure it); module count becomes 101 -- update SESSION_CONTEXT's Tests row and the FINDINGS header by hand if `--fix` does not); message `fix(config): Refuse a pre-check timeout that cannot bound a wait`.

---

### Task 3: Stop running a shell command at import

**Files:**
- Modify: `app.py` (delete the `os.system("")` call and its comment)
- Modify: `tests/test_app_factory.py`
- Modify: `docs/agents/PLAYBOOK.md`

Why: nothing in the application emits ANSI escape codes (no `\x1b` or `\033` in `app.py` or `scrobblescope/`), so the call enables nothing; on Linux it spawns `/bin/sh` every time the module is imported. The owner ruled against adding colour.

**Interfaces:**
- Produces: `tests/test_app_factory.py::_import_app_in_child(tmp_path, *, prelude="", epilogue="", extra_env=None)`, reused by Task 4.

- [ ] **Step 1: Write the failing test** at the end of `tests/test_app_factory.py` (add `import os`, `import subprocess`, `import sys` and `from pathlib import Path` to its imports if missing):

```python
REPO_ROOT = Path(__file__).resolve().parents[1]


def _import_app_in_child(tmp_path, *, prelude="", epilogue="", extra_env=None):
    """Import ``app`` in a fresh interpreter and return the completed process.

    Module-level start-up work (stream setup, logging handlers) runs only at
    first import, so it can only be observed in a new process. The child runs
    in *tmp_path* so its ``logs/`` directory lands there, with DEBUG_MODE=1 so
    a missing SECRET_KEY or API key warns instead of refusing to start.
    """
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "DEBUG_MODE": "1"}
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, "-c", f"{prelude}\nimport app\n{epilogue}"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        timeout=120,
    )


def test_importing_the_app_runs_no_shell_command(tmp_path):
    """Importing the app calls no `os.system`."""
    prelude = (
        "import os\n"
        "calls = []\n"
        "os.system = lambda command: calls.append(command) or 0"
    )
    result = _import_app_in_child(
        tmp_path, prelude=prelude, epilogue="print('SHELL_CALLS', calls)"
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert b"SHELL_CALLS []" in result.stdout
```

- [ ] **Step 2: Run to verify it fails.** `PY -m pytest tests/test_app_factory.py::test_importing_the_app_runs_no_shell_command -q`. Expected: FAIL, stdout holds `SHELL_CALLS ['']`.
- [ ] **Step 3: Implement:** delete the two lines `# Enable ANSI escape codes on Windows cmd` and `os.system("")` from `app.py`. Keep `import os` (still used).
- [ ] **Step 4: Run to verify it passes**, then `PY -m pytest tests/test_app_factory.py -q`.
- [ ] **Step 5: Planted defect:** re-add `os.system("")` after the stderr block; the test fails; revert.
- [ ] **Step 6:** Frontend gate (Global Constraints), then Section 4 entry `### 2026-10-22 - Importing the app no longer runs a shell command` (cite the owner's no-colour ruling); commit procedure; message `fix(app): Drop the shell call that enabled unused ANSI codes`.

---

### Task 4: Write log lines to stdout as UTF-8

**Files:**
- Modify: `app.py` (the stream setup block before the logging configuration)
- Modify: `tests/test_app_factory.py`
- Modify: `docs/agents/PLAYBOOK.md`

**Interfaces:**
- Consumes: `_import_app_in_child` from Task 3.

Why: `logging.StreamHandler(sys.stdout)` is the canonical production log channel (the file handler is ephemeral on Fly.io), but only `sys.stderr` is reconfigured to UTF-8. On a console whose code page lacks a character -- a Windows terminal and a non-Latin artist name -- the handler raises `UnicodeEncodeError` inside logging and the line is lost.

- [ ] **Step 1: Write the failing test** in `tests/test_app_factory.py`:

```python
def test_a_log_line_reaches_stdout_whole_on_a_narrow_console(tmp_path):
    """A line with characters the console's code page lacks still reaches stdout intact."""
    probe = "probe \u5742\u672c\u9f8d\u4e00 \u2192 done"
    result = _import_app_in_child(
        tmp_path,
        extra_env={"PYTHONIOENCODING": "cp1252"},
        epilogue=f"import logging\nlogging.warning({probe!r})",
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert probe in result.stdout.decode("utf-8")
    assert b"Logging error" not in result.stderr
```

- [ ] **Step 2: Run to verify it fails.** Expected: FAIL, the probe is missing from stdout and stderr holds `--- Logging error ---` with `UnicodeEncodeError`.
- [ ] **Step 3: Implement:** replace

```python
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")
```

with

```python
# stdout carries the production log stream and stderr carries tracebacks.
# A Windows console defaults to a legacy code page, where a listener's
# non-Latin artist name raised UnicodeEncodeError inside logging and the line
# was lost, so both write UTF-8 whatever the console's encoding.
for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        _stream.reconfigure(encoding="utf-8")
```

- [ ] **Step 4: Run to verify it passes**, then `PY -m pytest tests/test_app_factory.py -q`.
- [ ] **Step 5: Planted defects:** (a) iterate over `(sys.stderr,)` only: the test fails. (b) `_stream.reconfigure(errors="replace")` with no encoding: the test fails (the probe arrives as `?`). Revert each.
- [ ] **Step 6:** Frontend gate (Global Constraints), then Section 4 entry `### 2026-10-22 - Log lines reach stdout as UTF-8`; commit procedure; message `fix(app): Write stdout as UTF-8 like stderr`.

---

### Task 5: Make the coverless-wash route test independent of the clock (F-B23-48)

**Files:**
- Modify: `tests/test_routes.py` (`test_unmatched_view_coverless_rows_wear_their_albums_wash`)
- Modify: `docs/agents/FINDINGS.md` (file F-B23-48 as resolved), `docs/agents/PLAYBOOK.md`
- Modify, whenever `--fix` changed them: `docs/history/findings/FINDINGS_ARCHIVE.md`, `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

Root cause (2026-10-21, PR #262 CI flake): the test asserts the two `POST /unmatched_view` pages are byte-identical, but `templates/base.html` renders `<meta name="csrf-token" content="{{ csrf_token() }}">`, and Flask-WTF signs that token with a timestamp. Two renders that straddle a second boundary differ there, so the test fails now and then with no defect in the code. The only whole-page equality assertion in `tests/` is this one (`grep -rnE "_html == .*\.data\.decode" tests`).

- [ ] **Step 1: Prove the flake.** Write a throwaway proof under `<scratchpad>/side-t5/` (never committed, never inside `C:/ssw/side`): run it with cwd `C:/ssw/side` and `PYTHONPATH` set to it; it builds its own app with `from app import create_app`, sets `app.config["TESTING"] = True`, uses `app.test_client()`, recreates the job and rows as the test does, and patches `itsdangerous.timed.TimestampSigner.get_timestamp` with an incrementing counter (`itertools.count(1000)`), not a two-value list, so each render signs a different second; it fails on `assert first_html == second.data.decode("utf-8")`. Record the failing line in the report.
- [ ] **Step 2: Fix the assertion.** Replace

```python
    first = client.post("/unmatched_view", data={"job_id": job_id})
    second = client.post("/unmatched_view", data={"job_id": job_id})
    assert first.status_code == 200
    first_html = first.data.decode("utf-8")
    assert first_html == second.data.decode("utf-8")
```

with

```python
    first = client.post("/unmatched_view", data={"job_id": job_id})
    second = client.post("/unmatched_view", data={"job_id": job_id})
    assert first.status_code == 200
    assert second.status_code == 200
    first_html = first.data.decode("utf-8")
    second_html = second.data.decode("utf-8")
    # The pages also carry base.html's CSRF meta token, which is signed with
    # a timestamp, so two renders a second apart differ there by design.
    # The repeat this test is about is each row's artwork classes.
    for title in rows:
        assert _artwork_classes_in_row(second_html, title) == (
            _artwork_classes_in_row(first_html, title)
        ), title
```

and update the docstring's THEN clause to "... and the second render gives every row the same artwork classes as the first."

- [ ] **Step 3:** Re-run the Step 1 throwaway against the fixed body: it passes. Run `PY -m pytest tests/test_routes.py -q -k coverless`.
- [ ] **Step 4: Planted defect:** make the `cover_wash` template filter (grep `cover_wash` in `scrobblescope/`) return a class drawn from `random.randrange(6)` on each call; the fixed test still fails (the repeat or the expected-pick assertion). Revert.
- [ ] **Step 5:** File F-B23-48 in FINDINGS as resolved: title "`test_unmatched_view_coverless_rows_wear_their_albums_wash` compared whole pages that carry a timestamped CSRF token"; body: the root cause above, where it failed (PR #262 CI, 2026-10-21, passed on re-run), the fix; `- [x] **Status:** resolved`; `**Completed:** 2026-10-22`; `Source: PR #262 CI run and controller diagnosis, 2026-10-21.`
- [ ] **Step 6:** Section 4 entry `### 2026-10-22 - The coverless-wash route test no longer reads the clock` (edited existing test: name it); commit procedure; message `test(routes): Compare row artwork, not whole pages with a CSRF token`.

---

### Task 6: Refuse a job of the other mode on two JSON endpoints (F-B23-50)

**Files:**
- Modify: `scrobblescope/routes/heatmap_flow.py` (`heatmap_data`)
- Modify: `scrobblescope/routes/api.py` (`unmatched_data`)
- Modify: `tests/test_routes.py`
- Modify: `docs/agents/FINDINGS.md` (file F-B23-50 as resolved), `docs/agents/PLAYBOOK.md`
- Modify, whenever `--fix` changed them: `docs/history/findings/FINDINGS_ARCHIVE.md`, `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

Why: `heatmap_data` spreads `ctx["results"]` into its answer (`{"ready": True, **ctx["results"]}`); an album job's results are a list of rows, so an album job id there raises `TypeError` and answers 500 (2026-10-21 architecture review, defect D1). `unmatched_data` answers a heatmap job with 200 and an empty report (part of D3). The album pages and the release-check endpoint already answer a wrong-mode job with the same 404 a missing job gets; these two endpoints follow that rule. `/progress` stays shared by both modes: `static/js/heatmap.js` polls it.

- [ ] **Step 1: Write the failing tests** in `tests/test_routes.py`, after `test_heatmap_data_expired_job`:

```python
@pytest.mark.parametrize("state", ["running", "finished", "failed"])
def test_heatmap_data_refuses_an_album_job(client, state):
    """An album job's id gets the missing-job 404 in every state, never a 500."""
    job_id = jobs.create(TEST_JOB_PARAMS)
    if state == "finished":
        jobs.succeed(job_id, [{"artist": "Radiohead", "album": "Kid A"}], "Done!")
    elif state == "failed":
        jobs.fail(job_id, "lastfm_rate_limited")

    response = client.get(f"/heatmap_data?job_id={job_id}")
    assert response.status_code == 404
    assert response.get_json() == {
        "error": True,
        "message": "Job not found or expired.",
    }
```

and after `test_unmatched_api_returns_data`:

```python
def test_unmatched_api_refuses_a_heatmap_job(client):
    """A heatmap job's id gets the missing-job 404, not an unmatched report."""
    job_id = jobs.create(HEATMAP_JOB_PARAMS)
    jobs.record_unmatched(
        job_id,
        "artist::album_key",
        {"artist": "Radiohead", "album": "OK Computer", "reason": "x"},
    )

    response = client.get(f"/api/unmatched?job_id={job_id}")
    assert response.status_code == 404
    assert response.get_json() == {"count": 0, "data": {}, "error": "Job not found."}
```

(The heatmap job is given one unmatched entry so the unfixed endpoint answers 200 with a count of 1, not an empty report the assertion could confuse with a refusal.)

- [ ] **Step 2: Run to verify they fail.** `PY -m pytest tests/test_routes.py -q -k "refuses_an_album_job or refuses_a_heatmap_job"`. Expected: `running` fails with 202, `failed` with 200, and `finished` raises `TypeError` out of `client.get` (TESTING propagates it); the unmatched test fails with 200.
- [ ] **Step 3: Implement** `heatmap_data`: directly after the `if ctx is None:` block add

```python
    if ctx.get("params", {}).get("mode") != jobs.MODE_HEATMAP:
        # An album job's results are a list of rows, not the mapping this
        # answer spreads, so a wrong-mode id is refused the way a missing
        # job is -- the same rule the album pages and release checks follow.
        return (
            jsonify({"error": True, "message": "Job not found or expired."}),
            404,
        )
```

and `unmatched_data`: replace the `jobs.unmatched(job_id)` read and its `None` check with

```python
    job_context = jobs.context(job_id)
    if (
        job_context is None
        or job_context.get("params", {}).get("mode") != jobs.MODE_ALBUM
    ):
        # A heatmap job has no unmatched report: refuse it as a missing job,
        # in one read so the mode and the report come from the same record.
        return jsonify({"count": 0, "data": {}, "error": "Job not found."}), 404

    unmatched_data = job_context["unmatched"]
```

keeping the final `return jsonify({"count": len(unmatched_data), "data": unmatched_data})`.

- [ ] **Step 4: Run to verify they pass**, then the full `tests/test_routes.py` and `tests/test_heatmap.py`.
- [ ] **Step 5: Planted defects:** (a) in `heatmap_data`, move the mode check after the `if ctx["results"] is not None` branch: `finished` raises `TypeError`, `failed` gets 200 and `running` gets 202. (b) guard only `if ctx["results"] is not None and isinstance(ctx["results"], list)`: the `running` and `failed` cases fail. (c) delete the `unmatched_data` mode clause: the unmatched test fails. Revert each.
- [ ] **Step 6:** File F-B23-50 in FINDINGS as resolved: title "`/heatmap_data` answered an album job with a 500, and `/api/unmatched` answered a heatmap job as valid"; body: both behaviours, the fix, that `/progress` is shared on purpose, that the same mode check now appears inline in five places (the album pages' `_get_validated_job_context`, `_latest_heatmap_job`, `api.release_checks`, and these two) and F-B23-53's job read seam owns folding them into one; `- [x] **Status:** resolved`; `**Completed:** 2026-10-22`; `Source: docs/history/reports/architecture-review-2026-10-21.html (D1, D3), re-checked 2026-10-21.`
- [ ] **Step 7:** Frontend gate, then Section 4 entry `### 2026-10-22 - Two job endpoints refuse the other mode's job`; commit procedure; message `fix(routes): Refuse other-mode jobs on heatmap_data and api/unmatched`.

---

### Task 7: Track the 2026-10-21 architecture review and file its open items

**Files:**
- Create: `docs/history/reports/architecture-review-2026-10-21.html` (a byte-for-byte copy of the owner's untracked `C:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/docs/superpowers/plans/architecture-review-2026-10-21.html`, 57166 bytes, ASCII; copy with `cp`, leave the original where it is)
- Modify: `docs/agents/FINDINGS.md` (F-B23-51 .. F-B23-56), `docs/agents/PLAYBOOK.md`

Source of each finding: the review page, and the controller's triage `C:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/.superpowers/sdd/2026-10-20-pre-batch23-tranche/architecture-review-2026-10-21-triage.md` (read both). The triage re-checked every claim at `main` eb0db9e; re-check each one you file at 61fb4fc (`git grep`), and record anything PRs #261-#263 changed. Every finding is open, P2, and F-B23-51 .. F-B23-56 each use the canonical open record `- [ ] **Status:** open (P2). Source: ...` as their last line, with `Source: docs/history/reports/architecture-review-2026-10-21.html, triaged 2026-10-21.` and a "When" line giving its timing; file them under "P2 -- Scaling roadmap" in id order.

- [ ] **Step 1:** Copy the report into place; confirm `cmp` reports no difference.
- [ ] **Step 2:** F-B23-51 (D2): "A Last.fm page-loss detail is lost when a provider also fails" -- `jobs.record_stat` overwrites, four of five writers are unguarded, and the "3 of 12 pages (25%)" detail survives on neither the loading page nor Results (the Results notice keeps only a generic Last.fm sentence). Fix shape: the review's candidate 1, one record of a run's completeness (facts, rendered once). When: its own PR before Batch 23 WP-3, because the export path adds another writer.
- [ ] **Step 3:** F-B23-52 (candidate 2): one `UnmatchedAlbum` record with a constructor per reason, replacing the dict literals the `record_unmatched` writers build. When: before Batch 23 WP-5 (per-source wording) and WP-6.
- [ ] **Step 4:** F-B23-53 (candidate 3): one job read seam that owns the mode and payload rule once. Name the five inline mode checks F-B23-50 lists as its call sites. When: before Batch 23 WP-3 adds a third job kind.
- [ ] **Step 5:** F-B23-54 (candidate 4): one view model per page (results, unmatched), so the empty and filled `render_template` keyword blocks in `_render_results_page` cannot drift. When: with Batch 23 WP-5's results work.
- [ ] **Step 6:** F-B23-55 (candidate 5): phase collaborators passed as parameters, retiring the facade re-export block in `orchestrator/__init__.py`; many `mock.patch` targets, so parity tests come first. When: the owner's decision, its own PR, possibly after Batch 23.
- [ ] **Step 7:** F-B23-56 (candidate 6): one browser poller for `static/js/loading.js`, `heatmap.js` and `results-release-checks.js` (the third occurrence, so global-rules Rule 3 allows the abstraction). When: its own frontend PR; PR #262 has merged, so no `heatmap.js` conflict remains.
- [ ] **Step 8:** Section 4 entry `### 2026-10-22 - The 2026-10-21 architecture review is tracked with one finding per open item`; commit procedure; message `docs(findings): Track the 2026-10-21 review and file its open items`.

---

## Final checks (controller)

- gate-runner ALL_PASS at the final head (full suite, `scripts/dev/results_behavior_tests.py`, frontend gate under the browser lock, pre-commit, `doc_state_sync.py --check`).
- Whole-branch review (sdd-reviewer) of `61fb4fc..HEAD` against this plan.
- PR body from `.github/PULL_REQUEST_TEMPLATE.md` (State table, Validation at this head), no attribution line.

## Self-review

- Coverage: (a) Task 1; (b) Task 2; (c) Task 3; (d) Task 4; (e) Task 5; (g) and (h) Task 6; (i) Task 7. Plan commit: Task 0. Item (f), the PR template's State section, shipped as PR #263 and is not in this plan.
- Names: `_positive_seconds`, `_import_app_in_child`, `HEATMAP_JOB_PARAMS` (defined at the top of `tests/test_routes.py`), `TEST_JOB_PARAMS` (`tests/helpers.py`), `jobs.MODE_ALBUM` / `jobs.MODE_HEATMAP`, `jobs.context`, `jobs.succeed(job_id, results, message)`, `jobs.fail(job_id, code)`, `jobs.record_unmatched(job_id, key, payload)` -- each checked at 61fb4fc.
