# Docsync Content Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make deterministic defects in ScrobbleScope's live operational
documentation fail the existing pre-commit and GitHub Actions quality gate.

**Architecture:** Add a focused integrity analyzer beside the existing
docsync parser/renderer/logic modules. Keep issue discovery independent from
CLI printing, make the side-task archive prologue renderer-owned, and have
`docsync.cli` evaluate the final on-disk state after `--fix`. The existing
always-run pre-commit hook remains the sole local/CI entry point.

**Tech Stack:** Python 3.13 standard library, dataclasses, pathlib, regex,
subprocess Git queries, pytest, pre-commit, GitHub Actions.

## Global Constraints

- Use no new dependency and run no package-install command.
- Preserve `.claude/SESSION_CONTEXT.md` optionality: skip checks that require
  it when it is absent; when present, include it in live DOC001 scanning.
- Exclude dated PLAYBOOK entries and archived history from live-state checks.
- Exempt schematic Markdown paths containing glob syntax,
  `<placeholder>` tokens, or canonical `BATCHN_*` forms.
- `--fix` may normalize only deterministic managed content; it must never
  guess a semantic prose correction.
- Diagnostics must include a stable code, severity, repository-relative path
  and line when available, invariant, and exact remediation.
- `--check` returns 1 for drift or integrity errors and 2 for malformed input
  or invocation errors.
- Follow TDD; every test must fail if the behavior it protects is removed.
- Before each commit, follow `AGENTS.md` Commit Rules and Side-Task Handling,
  including a dated PLAYBOOK entry, docsync fix, full pytest, all hooks,
  final docsync check, and explicit path staging.
- Execute this plan before
  `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`.
- Until the worktree guard exists, resolve the sole Windows virtualenv in
  each fresh PowerShell process with:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pythonExe = Join-Path $primaryCheckout '.venv\Scripts\python.exe'
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
$preCommitExe = Join-Path $primaryCheckout '.venv\Scripts\pre-commit.exe'
```

---

## File Map

- Create `scripts/docsync/integrity.py`: issue discovery, concrete Markdown
  reference extraction, active-definition validation, archive/session checks,
  tracked-path collection, and deterministic ordering.
- Create `tests/test_docsync_integrity.py`: focused adversarial tests for the
  new module; do not add to oversized `tests/test_docsync_logic.py`.
- Modify `scripts/docsync/models.py:8-41`: add the immutable issue value type.
- Modify `scripts/docsync/renderer.py:1-65`: own and render the canonical
  side-task archive prologue without changing per-batch log prefixes.
- Modify `scripts/docsync/logic.py:111-275`: route only the monolith archive
  through the canonical side-archive renderer; retain existing cross-validator
  compatibility until CLI integration is complete.
- Modify `scripts/docsync/cli.py:1-247`: load the live corpus and tracked paths,
  render issues once, block errors, and revalidate final `--fix` state.
- Modify `tests/conftest.py:72-147`: make the docsync fixture a valid minimal
  live corpus with a stable active definition and deterministic tracked paths.
- Modify `tests/test_docsync_cli.py:32-171`: convert stale-session and mismatch
  expectations from warning-only to blocking, then add archive/link regression
  coverage.
- Modify `tests/test_docsync_renderer.py`: prove monolith canonicalization does
  not alter generic per-batch prefix rendering.
- Modify `scripts/docsync/__init__.py`: include `integrity` in the package map.
- Modify `AGENTS.md`, `DEVELOPMENT.md`, `FINDINGS.md`, `PLAYBOOK.md`, and
  `.claude/SESSION_CONTEXT.md`: describe the shipped gate, close F-DOCSYNC-5,
  log each implementation phase, and record the measured final test count.

---

### Task 1: Add the pure integrity analyzer

**Files:**

- Create: `scripts/docsync/integrity.py`
- Create: `tests/test_docsync_integrity.py`
- Modify: `scripts/docsync/models.py:8-41`
- Modify: `scripts/docsync/renderer.py:1-65`
- Modify: `scripts/docsync/__init__.py:1-3`
- Modify: `PLAYBOOK.md:68-190`
- Modify: `.claude/SESSION_CONTEXT.md:7-40`

**Interfaces:**

- Consumes: `_find_section`, `_parse_active_batch_state`, `SECTION_3_RE`,
  `SECTION_4_RE`, and `_latest_test_count_from_entries` from existing docsync
  modules.
- Produces:

```python
@dataclasses.dataclass(frozen=True)
class IntegrityIssue:
    code: str
    severity: Literal["error", "warning"]
    path: str
    line: int | None
    invariant: str
    remediation: str


def collect_tracked_paths(
    repo_root: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> frozenset[str]:
    """Return the Task 1 implementation's normalized tracked paths."""
    """Return normalized repository-relative paths from git ls-files."""


def collect_integrity_issues(
    *,
    repo_root: Path,
    live_documents: Mapping[str, list[str]],
    playbook_lines: list[str],
    archive_lines: list[str],
    session_lines: list[str] | None,
    expected_session_lines: list[str] | None,
    tracked_paths: frozenset[str],
) -> list[IntegrityIssue]:
    """Return deterministic live-document integrity issues."""
```

- Stable codes: `DOC001` dead concrete Markdown reference, `DOC002` active
  definition missing/mismatched, `DOC003` invalid or volatile Branch metadata,
  `DOC004` noncanonical archive prologue, `DOC005` stale managed session block,
  and `DOC006` current test-count contradiction.

- [ ] **Step 1: Write failing issue-model and reference tests**

Create `tests/test_docsync_integrity.py` with a fixture that supplies a valid
Batch 21 definition, canonical live documents, and a tracked-path set. Start
with these exact behavioral cases:

```python
from pathlib import Path

from docsync.integrity import collect_integrity_issues
from docsync.renderer import SIDE_ARCHIVE_PREFIX


def _valid_inputs(tmp_path: Path) -> dict[str, object]:
    definition = [
        "# BATCH21",
        "",
        "**Branch:** `wip/batch-21` (lineage lives in PLAYBOOK Section 4).",
    ]
    playbook = [
        "# PLAYBOOK",
        "",
        "## 3. Active batch + next action",
        "",
        "- **Batch 21 is active.** Definition: `BATCH21_DEFINITION.md`.",
        "  Branch: `wip/batch-21`.",
        "",
        "## 4. Execution log",
        "",
        "<!-- DOCSYNC:CURRENT-BATCH-START -->",
        "",
        "### 2026-08-05 - Current work (Batch 21 WP-0)",
        "",
        "Validation: **390 passed**.",
        "",
        "<!-- DOCSYNC:CURRENT-BATCH-END -->",
    ]
    live_documents = {
        "AGENTS.md": ["See `FINDINGS.md`."],
        "HANDOFF_PROMPT.md": ["Read `AGENTS.md`."],
        "AGENT_NOTES.md": ["Rules: `AGENTS.md`."],
        "PLAYBOOK.md": playbook,
        "FINDINGS.md": ["Archive: `docs/history/findings/FINDINGS_ARCHIVE.md`."],
        "BATCH21_DEFINITION.md": definition,
    }
    tracked = frozenset(
        {
            "AGENTS.md",
            "HANDOFF_PROMPT.md",
            "AGENT_NOTES.md",
            "PLAYBOOK.md",
            "FINDINGS.md",
            "BATCH21_DEFINITION.md",
            "docs/history/findings/FINDINGS_ARCHIVE.md",
        }
    )
    return {
        "repo_root": tmp_path,
        "live_documents": live_documents,
        "playbook_lines": playbook,
        "archive_lines": list(SIDE_ARCHIVE_PREFIX),
        "session_lines": None,
        "expected_session_lines": None,
        "tracked_paths": tracked,
    }


def test_dead_concrete_live_reference_is_error(tmp_path):
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = ["See `docs/missing.md`."]
    issues = collect_integrity_issues(**inputs)
    assert [(i.code, i.path, i.line) for i in issues] == [
        ("DOC001", "AGENTS.md", 1)
    ]
    assert "tracked file" in issues[0].remediation


def test_schematic_and_historical_references_are_ignored(tmp_path):
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = [
        "Use `BATCHN_DEFINITION.md`, `docs/history/logs/*.md`, and ",
        "`docs/history/SWE_<date>.md` as documented patterns.",
    ]
    inputs["playbook_lines"].extend(
        ["", "### 2026-01-01 - Old entry", "", "`docs/deleted-old-file.md`"]
    )
    assert collect_integrity_issues(**inputs) == []
```

Add separate tests for Markdown link syntax, Windows backslash normalization,
`?` and bracket globs, two broken references on one line, and deterministic
`(path, line, code)` ordering.

- [ ] **Step 2: Run the reference tests and verify red state**

Run:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/test_docsync_integrity.py -q
```

Expected: collection fails because `docsync.integrity` and
`IntegrityIssue` do not exist. Use the actual primary-checkout path reported by
the current approved worktree procedure; do not create a second `.venv`.

- [ ] **Step 3: Add the issue model and concrete-reference engine**

In `scripts/docsync/models.py`, add the exact frozen value object:

```python
from typing import Literal


@dataclasses.dataclass(frozen=True)
class IntegrityIssue:
    """One deterministic repository-integrity diagnostic."""

    code: str
    severity: Literal["error", "warning"]
    path: str
    line: int | None
    invariant: str
    remediation: str
```

In `scripts/docsync/renderer.py`, add this exact tuple before
`_render_archive()`. Task 1 supplies the value for pure comparison; Task 2
makes monolith rendering consume it.

```python
SIDE_ARCHIVE_PREFIX = (
    "# PLAYBOOK Execution Log Archive",
    "",
    "Purpose:",
    "- Store dated execution-log entries rotated out of `PLAYBOOK.md` Section 4.",
    "- Keep entries in reverse-chronological order (newest first).",
    "",
    "Read helpers:",
    "- `Get-Content docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`",
    '- `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`',
    '- `rg -n "<keyword>" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`',
)
```

In `scripts/docsync/integrity.py`, implement concrete Markdown reference
extraction with these boundaries:

```python
BACKTICK_MD_RE = re.compile(r"`([^`\n]+\.md)`")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s#]+\.md)(?:#[^)]+)?\)")
SCHEMATIC_RE = re.compile(r"[<*?\[\]]|\bBATCHN_", re.IGNORECASE)


def _normalize_reference(raw: str) -> str:
    return raw.strip().replace("\\", "/").removeprefix("./")


def _concrete_references(lines: list[str]) -> list[tuple[int, str]]:
    references: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        for pattern in (BACKTICK_MD_RE, MARKDOWN_LINK_RE):
            for match in pattern.finditer(line):
                reference = _normalize_reference(match.group(1))
                if not SCHEMATIC_RE.search(reference):
                    references.append((line_number, reference))
    return references
```

Call
`_find_section(playbook_lines, SECTION_4_RE, "PLAYBOOK section 4")`, then
use `_parse_entries(section_4_lines)` to remove dated Section 4 entry blocks
before checking PLAYBOOK. Check only the six live documents named in the
approved spec plus the active definition; do not scan `DEVELOPMENT.md` or any
archive body.

Implement `collect_tracked_paths()` with
`git ls-files -z --cached --others --exclude-standard` rejected: only
`git ls-files -z` is valid because an untracked file must not satisfy the
gate. Normalize its NUL-separated output to forward slashes. Raise
`SyncError` on Git failure with one stable invocation message; do not expose
stderr, command, path, token, credential, or traceback content.

- [ ] **Step 4: Run reference tests and verify green state**

Run:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/test_docsync_integrity.py -q
```

Expected: all reference extraction, schematic exclusion, historical
exclusion, tracked-path, and ordering tests pass.

- [ ] **Step 5: Write failing active-definition, archive, and session tests**

Add these independently adversarial cases to
`tests/test_docsync_integrity.py`:

```python
def test_active_definition_sha_is_blocking(tmp_path):
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["BATCH21_DEFINITION.md"] = [
        "# BATCH21",
        "**Branch:** `wip/batch-21` off `fa61716`.",
    ]
    issues = collect_integrity_issues(**inputs)
    assert [i.code for i in issues] == ["DOC003"]
    assert "PLAYBOOK Section 4" in issues[0].remediation


def test_active_definition_reference_must_match_batch(tmp_path):
    inputs = _valid_inputs(tmp_path)
    inputs["playbook_lines"][4] = (
        "- **Batch 21 is active.** Definition: `BATCH20_DEFINITION.md`."
    )
    inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
    issues = collect_integrity_issues(**inputs)
    assert [i.code for i in issues] == ["DOC002"]


def test_noncanonical_archive_prefix_is_blocking(tmp_path):
    inputs = _valid_inputs(tmp_path)
    inputs["archive_lines"] = [
        "# PLAYBOOK Execution Log Archive",
        "",
        "Purpose: old Section 10 path",
    ]
    issues = collect_integrity_issues(**inputs)
    assert [i.code for i in issues] == ["DOC004"]


def test_present_stale_session_block_is_blocking(tmp_path):
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = ["stale"]
    inputs["expected_session_lines"] = ["fresh"]
    issues = collect_integrity_issues(**inputs)
    assert [i.code for i in issues] == ["DOC005"]


def test_absent_session_skips_session_integrity(tmp_path):
    inputs = _valid_inputs(tmp_path)
    inputs["session_lines"] = None
    inputs["expected_session_lines"] = None
    assert collect_integrity_issues(**inputs) == []
```

Also cover a missing Branch field, duplicate Branch fields, absent or duplicate
tracked root candidates, exact `BATCH21` versus `BATCH210` tokens, subdirectory
and generic-template exclusions, an untracked supplied definition,
between-batches behavior, a dead optional-session reference, absent session,
matching and mismatching current test counts, and a count in only one source.

- [ ] **Step 6: Run the new tests and verify the failures are specific**

Run:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/test_docsync_integrity.py -q
```

Expected: new cases fail because `DOC002` through `DOC006` are not emitted;
the already-green reference cases remain green.

- [ ] **Step 7: Implement active-definition, archive, and session invariants**

Use the existing Section 3 parser to determine `current_batch`. Within the
Section 3 slice, require exactly one concrete root Markdown path immediately
after `Definition:`. Enumerate normalized tracked root candidates with exact
`^BATCH<current>(?:_[^/]+)?\.md$` matching; the declared path must be that sole
candidate. This accepts `BATCH21.md`, `BATCH21_DEFINITION.md`, and an
owner-approved suffix while excluding `BATCH210*`, subdirectories, generic
`BATCHN_*` templates, and untracked supplied content. Between batches, skip
the root-candidate check.

Read the resolved definition from `live_documents`, require exactly one line
matching `^\*\*Branch:\*\*`, and reject
`\b[0-9a-fA-F]{7,40}\b` on that line. Compare the archive prefix before its
first dated entry with `SIDE_ARCHIVE_PREFIX` from `docsync.renderer`. When
session lines exist, scan them for DOC001 with original source lines, compare
them to the expected rendered session, and use `latest_test_count_authority()`
to produce `DOC006`. Resolve the authority through that function rather than
the bare-count wrapper: it reports whether the newest count-bearing entry was
ambiguous, and an ambiguous authority beside any named numeric session field
is itself blocking. Treating ambiguity as "no count to compare against" lets a
stale dashboard pass the gate while the managed block renders as unknown.
Otherwise `DOC006` fires only when both sources contain a current count and
disagree.

Return `sorted(issues, key=lambda i: (i.path, i.line or 0, i.code))`.

- [ ] **Step 8: Run focused and existing docsync tests**

Run:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/test_docsync_integrity.py tests/test_docsync_logic.py -q
```

Expected: all tests pass; existing `_cross_validate` behavior remains intact
until Task 2 changes CLI severity.

- [ ] **Step 9: Log, synchronize, validate, and commit Task 1**

Add a dated side-task entry directly after
`<!-- DOCSYNC:CURRENT-BATCH-END -->` stating that the pure analyzer exists but
is not yet wired into the hook, so F-DOCSYNC-5 remains open. Run the full
AGENTS.md commit procedure with the shared `.venv`, stage only the named files
plus docsync-managed outputs, then commit:

```powershell
git commit -m "feat(docsync): add live-document integrity analysis" -m "Model deterministic integrity issues and detect dead live references,`nvolatile active-definition metadata, archive drift, and session`ncontradictions before wiring enforcement into the existing gate."
```

---

### Task 2: Wire blocking integrity into docsync and CI

**Files:**

- Modify: `scripts/docsync/renderer.py:56`
- Modify: `scripts/docsync/logic.py:111-275`
- Modify: `scripts/docsync/cli.py:1-247`
- Modify: `tests/conftest.py:72-147`
- Modify: `tests/test_docsync_cli.py:32-171`
- Modify: `tests/test_docsync_renderer.py`
- Modify: `AGENTS.md:269-355`
- Modify: `DEVELOPMENT.md:162-255`
- Modify: `FINDINGS.md:27-70`
- Modify: `PLAYBOOK.md:68-210`
- Modify: `.claude/SESSION_CONTEXT.md:7-40`

**Interfaces:**

- Consumes: `IntegrityIssue`, `collect_tracked_paths()`, and
  `collect_integrity_issues()` from Task 1.
- Exact consumed signatures:

```python
def collect_tracked_paths(
    repo_root: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> frozenset[str]:


def collect_integrity_issues(
    *,
    repo_root: Path,
    live_documents: Mapping[str, list[str]],
    playbook_lines: list[str],
    archive_lines: list[str],
    session_lines: list[str] | None,
    expected_session_lines: list[str] | None,
    tracked_paths: frozenset[str],
) -> list[IntegrityIssue]:
    """Return the Task 1 implementation's ordered integrity issues."""
```

- Produces:

```python
SIDE_ARCHIVE_PREFIX: tuple[str, ...]


def _render_side_archive(entries: list[Entry]) -> list[str]:
    """Render the monolith side-task archive with its canonical prologue."""


def _format_issue(issue: IntegrityIssue) -> str:
    """Render one stable, repository-relative diagnostic."""
```

- [ ] **Step 1: Write failing renderer and CLI enforcement tests**

Add renderer tests proving that `_render_side_archive()` always emits this
exact prologue and `_render_archive(custom_prefix, entries)` still preserves a
per-batch log prefix:

```python
SIDE_ARCHIVE_PREFIX = (
    "# PLAYBOOK Execution Log Archive",
    "",
    "Purpose:",
    "- Store dated execution-log entries rotated out of `PLAYBOOK.md` Section 4.",
    "- Keep entries in reverse-chronological order (newest first).",
    "",
    "Read helpers:",
    "- `Get-Content docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`",
    '- `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`',
    '- `rg -n "<keyword>" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`',
)
```

Update `sync_env` so its PLAYBOOK Section 3 names
`BATCH11_DEFINITION.md` and branch `wip/batch-11`, create that definition with
a stable Branch line, create minimal AGENTS/HANDOFF/AGENT_NOTES/FINDINGS files,
use the canonical archive prefix, and monkeypatch CLI tracked-path loading to
return every fixture file.

Change/add CLI expectations:

```python
def test_check_fails_on_stale_session_context(sync_env, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
    assert cli_mod.main() == 1
    captured = capsys.readouterr()
    assert "ERROR DOC005" in captured.err


def test_fix_revalidates_and_clears_fixable_session_error(
    sync_env, monkeypatch, capsys
):
    monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
    assert cli_mod.main() == 0
    monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
    assert cli_mod.main() == 0


def test_check_fails_on_dead_live_reference(sync_env, monkeypatch, capsys):
    agents = sync_env / "AGENTS.md"
    agents.write_text("See `docs/missing.md`.\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
    assert cli_mod.main() == 1
    assert "ERROR DOC001 AGENTS.md:1" in capsys.readouterr().err


def test_fix_normalizes_archive_then_passes(sync_env, monkeypatch):
    archive = sync_env / "docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
    archive.write_text("# stale prefix\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
    assert cli_mod.main() == 0
    monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
    assert cli_mod.main() == 0
```

Retain and update missing-SESSION tests so both modes still pass without
creating the file.

- [ ] **Step 2: Run targeted tests and verify red state**

Run:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/test_docsync_renderer.py tests/test_docsync_cli.py -q
```

Expected: canonical renderer and blocking exit-code assertions fail while
existing rotation and optional-session tests remain diagnostic.

- [ ] **Step 3: Make the monolith prefix renderer-owned**

Add `SIDE_ARCHIVE_PREFIX` and `_render_side_archive()` to renderer. In
`_sync()` and `_split_archive()`, render the monolith with
`_render_side_archive()` instead of preserving `archive_prefix`; retain
`_render_archive(prefix, entries)` for per-batch logs. Remove only the now
unused monolith-prefix variables.

This makes a stale archive prefix appear as normal deterministic sync drift:
`--check` sees a changed archive, and `--fix` writes the canonical prologue
without altering dated entries.

- [ ] **Step 4: Restructure CLI around final-state integrity**

Add repository and live-document path constants:

```python
REPO_ROOT = Path(".")
LIVE_DOCUMENT_PATHS = (
    Path("AGENTS.md"),
    Path("HANDOFF_PROMPT.md"),
    Path("AGENT_NOTES.md"),
    PLAYBOOK_PATH,
    Path("FINDINGS.md"),
)
```

After parsing mode arguments, load sync input, compute `result`, and collect
issues against current files for `--check`. Print each issue as:

```python
def _format_issue(issue: IntegrityIssue) -> str:
    location = issue.path
    if issue.line is not None:
        location = f"{location}:{issue.line}"
    return (
        f"{issue.severity.upper()} {issue.code} {location} -- "
        f"{issue.invariant}\nRemediation: {issue.remediation}"
    )
```

For `--check`, return 1 if managed output differs or any issue severity is
`error`. Continue printing `_check_root_batch_files()` output as `WARNING`.

For `--fix`, write deterministic sync outputs first, then re-read PLAYBOOK,
archive, and optional SESSION_CONTEXT, recompute `_sync()`, reload live
documents/tracked paths, and collect issues on that final state. Return 1 if
any error remains; return 0 only when the final disk state is clean. Do not
print a stale pre-fix error after it was successfully repaired.

Stop calling `_cross_validate()` from CLI because Task 1 now owns those live
checks and their blocking codes. Keep the helper callable for its existing
direct unit tests; removing it is outside this P0 remediation.

- [ ] **Step 5: Run targeted tests and verify green state**

Run:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/test_docsync_integrity.py tests/test_docsync_renderer.py tests/test_docsync_cli.py tests/test_docsync_logic.py -q
```

Expected: all docsync tests pass. Confirm the stale-session check is now
blocking, `--fix` clears fixable drift, semantic errors remain blocking, and
SESSION_CONTEXT absence remains supported.

- [ ] **Step 6: Update canonical and human documentation**

In `AGENTS.md` Doc Sync Rules, replace the statement that all
cross-validation warnings are non-blocking with the exact split: proven live
integrity defects are errors and fail check/fix, expected active-root notices
remain warnings, and missing optional SESSION_CONTEXT skips dependent checks.
Do not duplicate the issue-code table there; point to the command output.

In `DEVELOPMENT.md`, change the approved/future wording to shipped behavior,
explain final-state revalidation, and retain its explicit human-only role.

In `FINDINGS.md`, set F-DOCSYNC-5 to resolved with the measured commit/test
evidence; do not move it to the archive outside batch close-out or a dedicated
cleanup WP. Leave F-WORKTREE-1 and F-WORKTREE-2 open P0.

Update PLAYBOOK Section 3 so the worktree guard plan is next, add the dated
Task 2 side-task entry directly after the marker, and update SESSION_CONTEXT
Section 1 with the measured test count and remaining P0 gate. Run
`doc_state_sync.py --fix`.

- [ ] **Step 7: Run the blocking CLI regression directly**

Run the deliberately stale fixture through the real CLI entry path:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/test_docsync_cli.py::TestMainArgs::test_check_fails_on_dead_live_reference -q
```

Expected: PASS because the fixture observes CLI exit 1 and `ERROR DOC001`.
This is the deliberate stale fixture required by the specification without
temporarily mutating a real canonical file.

- [ ] **Step 8: Run full gates and commit Task 2**

Run the canonical procedure in order with the shared primary-checkout
executables:

```powershell
$primaryCheckout = (git worktree list --porcelain |
  Select-String '^worktree ' | Select-Object -First 1).Line.Substring(9)
$pythonExe = Join-Path $primaryCheckout '.venv\Scripts\python.exe'
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
$preCommitExe = Join-Path $primaryCheckout '.venv\Scripts\pre-commit.exe'
& $pythonExe scripts/doc_state_sync.py --fix
& $pytestExe -q
& $preCommitExe run --all-files
& $pythonExe scripts/doc_state_sync.py --check
```

Copy the exact final passing count into PLAYBOOK, FINDINGS, and
SESSION_CONTEXT before the final rerun. Read every changed file whole, perform
the AGENTS.md blast-radius greps, stage explicit paths only, and commit:

```powershell
git commit -m "fix(docsync): block canonical documentation drift" -m "Promote provable live-document contradictions to deterministic failures,`nnormalize the side-task archive prologue, and revalidate final on-disk`nstate so the existing local and CI hook cannot report a false green."
```

- [ ] **Step 9: Verify Task 2 commit state**

Require a clean worktree, `origin/main...HEAD` showing zero behind, final
docsync exit 0, and the full suite passing. Do not push unless the owner has
authorized publishing the implementation commits.
