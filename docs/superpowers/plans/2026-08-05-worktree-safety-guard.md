# Worktree Safety Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only, cross-agent bootstrap guard that detects stale or
wrong worktree lineage and resolves the repository's sole allowed virtualenv
without mutating Git or installing packages.

**Architecture:** Keep classification and Git/environment discovery in
`scripts/dev/worktree_guard.py` and use
`scripts/dev/check_worktree_alignment.py` as a thin CLI. It compares the
PLAYBOOK branch with refreshed `origin/main`, distinguishes rebase artifacts
from true divergence, and reports the linked worktree's allowed environment.

**Tech Stack:** Python 3.13 standard library, dataclasses, pathlib, argparse,
subprocess Git commands, pytest, pre-commit, GitHub Actions unit tests.

## Global Constraints

- Execute
  `docs/superpowers/plans/2026-08-05-docsync-content-integrity.md` first and
  start this plan only after its final commit is clean and zero commits behind
  `origin/main`.
- The guard must never fetch, reset, rebase, switch, push, delete, create a
  worktree, activate a virtualenv, or install a package.
- Any reset, rebase, or force-push remains owner-authorized under AGENTS.md.
- Default base ref is exactly `origin/main`.
- Callers using the default base refresh it with `git fetch --prune origin`.
  Callers selecting another base must refresh or otherwise verify that exact
  local ref; diagnostic guidance names the display-safe selected ref without
  constructing a shell command. Offline callers use `--offline` and receive
  final informational WT013 local-ref-only context on every result, including
  error results.
- Ahead-only active branches pass. Behind-only, wrong-branch, detached-local,
  missing-base, identical-tree divergence, and true divergence states fail.
- Detached recognized CI exits 0 with an explicit skip. Live worktree topology
  is not a CI gate; the guard's unit tests are.
- Dirty state warns but does not fail an otherwise aligned branch; every
  history-repair message says not to proceed until the tree is reconciled.
- A linked worktree may reuse only the primary checkout's `.venv`. A different
  linked-root `.venv` is an error; no fallback creates or installs anything.
- Diagnostics use stable codes and deterministic ordering.
- Before each commit, follow `AGENTS.md` Commit Rules and Side-Task Handling,
  including docsync fix, full pytest, all hooks, final docsync check, and
  explicit path staging.

Until Task 2 ships the guard's executable-path report, resolve the existing
Windows virtualenv in every fresh PowerShell process with:

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pythonExe = Join-Path $primaryCheckout '.venv\Scripts\python.exe'
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
$preCommitExe = Join-Path $primaryCheckout '.venv\Scripts\pre-commit.exe'
```

---

## File Map

- Create `scripts/dev/_worktree_guard_types.py`: immutable public guard values.
- Create `scripts/dev/worktree_guard.py`: parsing, classification, Git
  discovery, CI detection, and virtualenv resolution.
- Create `scripts/dev/check_worktree_alignment.py`: thin CLI and exit status.
- Create `tests/scripts/dev/test_worktree_guard.py`: parser, lineage, and mocked-Git cases.
- Create `tests/scripts/dev/test_worktree_guard_venv.py`: virtualenv cases split
  to satisfy the repository's peer-size gate.
- Modify `AGENTS.md:27-147` and `HANDOFF_PROMPT.md:9-27`: canonical bootstrap
  gate and pointer without a copied decision table.
- Modify `DEVELOPMENT.md:224-260` and `FINDINGS.md:27-80`: shipped human
  rationale and resolved worktree findings.
- Modify `PLAYBOOK.md:68-230` and `.claude/SESSION_CONTEXT.md:7-40`: execution
  evidence, measured count, and F-SWE-1 next action.

---

### Task 1: Build and test the pure worktree classifier

**Files:**

- Create: `scripts/dev/worktree_guard.py`
- Create: `scripts/dev/_worktree_guard_types.py`
- Create: `tests/scripts/dev/test_worktree_guard.py`
- Create: `tests/scripts/dev/test_worktree_guard_venv.py`
- Modify: `PLAYBOOK.md:68-230`
- Modify: `.claude/SESSION_CONTEXT.md:7-40`

**Interfaces:**

- Consumes: PLAYBOOK Section 3 text and immutable values collected later by
  the CLI integration.
- Produces:

```python
Severity = Literal["INFO", "WARNING", "ERROR"]


@dataclasses.dataclass(frozen=True)
class Diagnostic:
    severity: Severity
    code: str
    subject: str
    message: str
    remediation: str | None = None


@dataclasses.dataclass(frozen=True)
class BatchBranch:
    active_batch: int | None
    expected_branch: str | None


@dataclasses.dataclass(frozen=True)
class LineageSnapshot:
    active_batch: int | None
    expected_branch: str | None
    actual_branch: str | None
    base_ref: str
    behind: int
    ahead: int
    head_tree: str | None
    base_tree: str | None
    dirty: bool
    detached: bool
    recognized_ci: bool


@dataclasses.dataclass(frozen=True)
class VenvPaths:
    root: Path
    python: Path
    pytest: Path
    pre_commit: Path


def parse_batch_branch(playbook_text: str) -> BatchBranch:
    """Return the Task 1 active-batch branch parse."""
    """Parse active batch and its stable branch from PLAYBOOK Section 3."""


def classify_lineage(snapshot: LineageSnapshot) -> list[Diagnostic]:
    """Return the Task 1 deterministic lineage classification."""
    """Classify branch ancestry without running or mutating Git."""


def resolve_venv(
    *, repo_root: Path, git_dir: Path, common_dir: Path, os_name: str
) -> tuple[VenvPaths | None, list[Diagnostic]]:
    """Resolve the sole allowed environment for a normal or linked checkout."""
```

- Stable codes: `WT001` not a repository, `WT002` active branch metadata
  missing, `WT003` wrong branch, `WT004` identical-tree rebase artifact,
  `WT005` true divergence, `WT006` behind base, `WT007` missing base,
  `WT008` forbidden secondary virtualenv, `WT009` missing required virtualenv,
  `WT010` dirty-tree warning, `WT011` detached-CI skip, and `WT012` detached
  local checkout. `WT013` is the final informational offline qualifier.
  `WT000` is an informational successful summary, not an error.

- [ ] **Step 1: Write failing PLAYBOOK parser tests**

Create `tests/scripts/dev/test_worktree_guard.py` with:

```python
from scripts.dev.worktree_guard import BatchBranch, parse_batch_branch


def test_parse_active_batch_branch_from_section_three_only():
    playbook = """# PLAYBOOK

## 3. Active batch + next action

- **Batch 21 is active.** Definition: `BATCH21_DEFINITION.md`.
  Branch: `wip/batch-21` (worktree off `main`).

## 4. Execution log

### 2026-08-01 - Historical
Branch: `stale/review-branch`.
"""
    assert parse_batch_branch(playbook) == BatchBranch(21, "wip/batch-21")


def test_between_batches_has_no_expected_branch():
    playbook = """# PLAYBOOK

## 3. Active batch + next action

- **Batch 21 is complete.**
- **Batch 22 is not yet defined.**

## 4. Execution log
"""
    assert parse_batch_branch(playbook) == BatchBranch(None, None)


def test_active_batch_without_branch_is_explicitly_missing():
    playbook = """# PLAYBOOK

## 3. Active batch + next action

- **Batch 21 is active.**

## 4. Execution log
"""
    assert parse_batch_branch(playbook) == BatchBranch(21, None)
```

Add adversarial cases for a Branch line only in Section 4, two Branch lines in
Section 3, and a missing Section 3 heading. Duplicate/malformed active state
must raise `GuardError` rather than silently choosing one.

- [ ] **Step 2: Run parser tests and verify red state**

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/scripts/dev/test_worktree_guard.py -q
```

Expected: import fails because `scripts.dev.worktree_guard` does not exist.

- [ ] **Step 3: Implement strict Section 3 parsing**

Use dedicated, anchored regexes without importing private docsync functions:

```python
SECTION_3_RE = re.compile(r"^##\s*3\.?\s*Active\s+batch\b.*$", re.IGNORECASE)
GENERIC_SECTION_RE = re.compile(r"^##\s+")
ACTIVE_BATCH_RE = re.compile(
    r"\bBatch\s+(\d+)\s+is\s+(?:active|current|in[\s-]?progress)\b",
    re.IGNORECASE,
)
BRANCH_RE = re.compile(r"\bBranch:\s*`([^`]+)`", re.IGNORECASE)
```

Slice only Section 3. Return `(None, None)` when no batch is active. When one
batch is active, preserve `None` for a missing branch so the classifier can
emit `WT002`. Raise `GuardError` for duplicate active batches, duplicate
branches, or a missing Section 3.

- [ ] **Step 4: Run parser tests and verify green state**

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$pytestExe = Join-Path (Split-Path -Parent $commonGitDir) '.venv\Scripts\pytest.exe'
& $pytestExe tests/scripts/dev/test_worktree_guard.py -q
```

Expected: parser cases pass and ignore dated Section 4 branch text.

- [ ] **Step 5: Write failing lineage-classification tests**

Create a `_snapshot()` test helper with explicit safe defaults, then cover the
decision table member by member:

```python
def _snapshot(**overrides):
    values = {
        "active_batch": 21,
        "expected_branch": "wip/batch-21",
        "actual_branch": "wip/batch-21",
        "base_ref": "origin/main",
        "behind": 0,
        "ahead": 0,
        "head_tree": "tree-a",
        "base_tree": "tree-a",
        "dirty": False,
        "detached": False,
        "recognized_ci": False,
    }
    values.update(overrides)
    return LineageSnapshot(**values)


def test_ahead_only_active_branch_passes():
    issues = classify_lineage(_snapshot(ahead=3))
    assert not [issue for issue in issues if issue.severity == "ERROR"]


def test_identical_tree_divergence_is_rebase_artifact():
    issues = classify_lineage(_snapshot(behind=3, ahead=3))
    assert [issue.code for issue in issues if issue.severity == "ERROR"] == [
        "WT004"
    ]
    assert "owner approval" in issues[0].remediation
    assert "force-push with lease" in issues[0].remediation


def test_different_tree_divergence_explicitly_prohibits_reset():
    issues = classify_lineage(
        _snapshot(behind=2, ahead=1, base_tree="tree-b")
    )
    error = next(issue for issue in issues if issue.code == "WT005")
    remediation = error.remediation or ""
    assert "do not reset" in remediation.lower()
    assert "git reset" not in remediation.lower()


def test_detached_ci_skips_and_detached_local_fails():
    ci = classify_lineage(
        _snapshot(actual_branch=None, detached=True, recognized_ci=True)
    )
    local = classify_lineage(
        _snapshot(actual_branch=None, detached=True, recognized_ci=False)
    )
    assert [issue.code for issue in ci] == ["WT011"]
    assert [issue.code for issue in local if issue.severity == "ERROR"] == [
        "WT012"
    ]
```

Add distinct cases for 0/0, behind-only, wrong branch, between batches, dirty
aligned state, and dirty identical-tree divergence. Assert deterministic code
order and that dirty state does not erase the lineage error.

- [ ] **Step 6: Run classifier tests and verify red state**

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$pytestExe = Join-Path (Split-Path -Parent $commonGitDir) '.venv\Scripts\pytest.exe'
& $pytestExe tests/scripts/dev/test_worktree_guard.py -q
```

Expected: parser tests stay green; classifier cases fail because
`classify_lineage()` is absent.

- [ ] **Step 7: Implement lineage classification**

Apply checks in this fixed order: detached CI/local, missing expected branch
for an active batch, wrong actual branch, dirty warning, behind-only, then
both-sided divergence. For both-sided divergence, emit `WT004` only when both
tree IDs exist and match; otherwise emit `WT005`. Ahead-only and 0/0 return
no error. Between batches skip expected-branch and ancestry enforcement after
basic diagnostics.

For the default base, the `WT004` remediation must say:

```text
Stop. Reconcile any dirty files, refresh origin/main, verify the trees again,
obtain the explicit owner approval required by AGENTS.md, then realign the
named branch and use force-push with lease. This guard performs none of those
actions.
```

For any caller-selected base, keep the same safety requirements but replace
`origin/main` with the display-safe selected ref. Never prescribe the origin
remote for a different base or construct a fetch command from caller input.

The `WT005` remediation must say:

```text
Stop and inspect the commit graph and tree diff. This is not the
content-identical rebase-merge case; do not reset, rebase, or force-push from
this diagnostic.
```

- [ ] **Step 8: Write failing virtualenv resolution tests**

Use real temporary directories, not mocked existence checks:

```python
def _create_windows_tools(venv_root: Path) -> None:
    scripts = venv_root / "Scripts"
    scripts.mkdir(parents=True)
    for name in ("python.exe", "pytest.exe", "pre-commit.exe"):
        (scripts / name).touch()


def test_linked_worktree_reuses_primary_checkout_venv(tmp_path):
    primary = tmp_path / "primary"
    linked = tmp_path / "linked"
    common_dir = primary / ".git"
    git_dir = common_dir / "worktrees" / "linked"
    linked.mkdir()
    git_dir.mkdir(parents=True)
    _create_windows_tools(primary / ".venv")
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common_dir,
        os_name="nt",
    )
    assert paths is not None
    assert paths.root == primary / ".venv"
    assert not [issue for issue in issues if issue.severity == "ERROR"]


def test_distinct_linked_root_venv_is_rejected(tmp_path):
    primary = tmp_path / "primary"
    linked = tmp_path / "linked"
    common_dir = primary / ".git"
    git_dir = common_dir / "worktrees" / "linked"
    git_dir.mkdir(parents=True)
    _create_windows_tools(primary / ".venv")
    _create_windows_tools(linked / ".venv")
    paths, issues = resolve_venv(
        repo_root=linked,
        git_dir=git_dir,
        common_dir=common_dir,
        os_name="nt",
    )
    assert paths is None
    assert [issue.code for issue in issues if issue.severity == "ERROR"] == [
        "WT008"
    ]
```

Add ordinary-checkout Windows, linked POSIX, missing primary environment,
missing one required executable, and a linked-root symlink/junction resolving
to the primary environment.

- [ ] **Step 9: Implement platform-aware virtualenv resolution**

Treat a checkout as linked when `git_dir.resolve() != common_dir.resolve()`.
For an ordinary checkout, candidate root is `repo_root / ".venv"`. For a
linked checkout, primary root is `common_dir.resolve().parent` and candidate
is `primary_root / ".venv"`.

Use these exact relative executables:

```python
WINDOWS_TOOLS = {
    "python": Path("Scripts/python.exe"),
    "pytest": Path("Scripts/pytest.exe"),
    "pre_commit": Path("Scripts/pre-commit.exe"),
}
POSIX_TOOLS = {
    "python": Path("bin/python"),
    "pytest": Path("bin/pytest"),
    "pre_commit": Path("bin/pre-commit"),
}
```

If a linked-root `.venv` exists and does not resolve to the primary candidate,
emit `WT008`. If any required candidate executable is absent, emit `WT009`
listing each missing repository-relative tool path and the AGENTS.md setup
section. Never call pip or create directories.

- [ ] **Step 10: Run all pure guard tests**

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/scripts/dev/test_worktree_guard.py tests/scripts/dev/test_worktree_guard_venv.py -q
```

Expected: every parser, lineage, and virtualenv case passes.

- [ ] **Step 11: Log, synchronize, validate, and commit Task 1**

Add a dated side-task entry stating that the pure classifier is testable but
not yet a mandatory bootstrap command, so F-WORKTREE-1 and F-WORKTREE-2 remain
open. Run the full AGENTS.md commit procedure, stage only named paths and
docsync-managed outputs, then commit:

```powershell
git commit -m "feat(dev): add worktree safety classification" -m "Classify active-branch ancestry, distinguish content-identical rebase`nartifacts from true divergence, and resolve the sole allowed virtualenv`nwithout allowing the diagnostic layer to mutate repository state."
```

---

### Task 2: Add the read-only CLI and canonical bootstrap gate

**Files:**

- Modify: `scripts/dev/worktree_guard.py`
- Create: `scripts/dev/check_worktree_alignment.py`
- Modify: `tests/scripts/dev/test_worktree_guard.py`
- Modify: `AGENTS.md:27-147`
- Modify: `HANDOFF_PROMPT.md:9-27`
- Modify: `DEVELOPMENT.md:224-260`
- Modify: `FINDINGS.md:27-80`
- Modify: `PLAYBOOK.md:68-230`
- Modify: `.claude/SESSION_CONTEXT.md:7-40`

**Interfaces:**

- Consumes: Task 1's parser, classifier, diagnostic, and virtualenv resolver.
- Exact consumed signatures:

```python
def parse_batch_branch(playbook_text: str) -> BatchBranch:


def classify_lineage(snapshot: LineageSnapshot) -> list[Diagnostic]:


def resolve_venv(
    *, repo_root: Path, git_dir: Path, common_dir: Path, os_name: str
) -> tuple[VenvPaths | None, list[Diagnostic]]:
    """Return the Task 1 environment resolution and diagnostics."""
```

- Produces:

```python
@dataclasses.dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def inspect_worktree(
    repo_root: Path,
    *,
    base_ref: str = "origin/main",
    offline: bool = False,
    environ: Mapping[str, str] = os.environ,
    runner: Callable[[Path, tuple[str, ...]], CommandResult] = run_git,
) -> list[Diagnostic]:
    """Collect and classify local worktree state without mutation."""


def main(argv: Sequence[str] | None = None) -> int:
    """Print worktree diagnostics and return nonzero when errors exist."""
```

- [ ] **Step 1: Write failing mocked-Git inspection tests**

Create a deterministic fake runner keyed by exact argument tuples:

```python
class FakeGit:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, cwd, args):
        self.calls.append((cwd, args))
        return self.responses[args]


def _ok(stdout=""):
    return CommandResult(0, stdout, "")
```

Add integration cases for this exact local command sequence:

```text
rev-parse --show-toplevel
rev-parse --git-dir
rev-parse --git-common-dir
symbolic-ref --quiet --short HEAD
rev-parse --verify origin/main^{commit}
rev-list --left-right --count origin/main...HEAD
status --porcelain
rev-parse HEAD^{tree}
rev-parse origin/main^{tree}
```

Assert the tree commands are called only for both-sided divergence. Assert no
command contains `fetch`, `reset`, `rebase`, `switch`, `checkout`, `push`,
`clean`, or `worktree remove`. Add missing-repository, missing-base,
ahead-only, identical divergence, different divergence, detached CI, detached
local, dirty, normal checkout, and linked checkout response maps.

- [ ] **Step 2: Run the inspection tests and verify red state**

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/scripts/dev/test_worktree_guard.py tests/scripts/dev/test_worktree_guard_venv.py -q
```

Expected: Task 1 tests pass; inspection tests fail because `CommandResult`,
`run_git()`, and `inspect_worktree()` do not exist.

- [ ] **Step 3: Implement sanitized local Git discovery**

Implement `run_git()` with `subprocess.run(["git", *args], cwd=repo_root,
capture_output=True, text=True, timeout=10, check=False)`. Catch
`FileNotFoundError` and `TimeoutExpired` and convert them to `GuardError`
without including environment variables or remote URLs.

Resolve relative `--git-dir` and `--git-common-dir` output against the
top-level path returned by Git before comparing paths or locating `.venv`;
do not resolve them against the process's original working directory.

`inspect_worktree()` must:

1. Resolve repository root, Git dir, and common dir.
2. Parse PLAYBOOK from the resolved repository root.
3. Detect recognized CI when `CI` or `GITHUB_ACTIONS` is one of
   `1`, `true`, or `yes` case-insensitively.
4. Detect detached HEAD from `symbolic-ref` return code 1; return WT011 as the
   only topology diagnostic in recognized CI (plus WT013 when explicitly
   offline).
5. Verify the selected `{base_ref}^{commit}` before ancestry (default:
   `origin/main`).
6. Parse `rev-list` as `behind, ahead` because the selected base is the left
   side of the comparison.
7. Read dirty state.
8. Read tree IDs only when both counts are nonzero.
9. Call `classify_lineage()` and `resolve_venv()`.
10. Add WT000 with branch, base ref, counts, checkout kind, and qualified
    Python/pytest/pre-commit paths when no error prevents a summary.
11. Append informational WT013 with a local-ref-only sentence to every result
    when `offline=True`; do not overload success-only WT000.

- [ ] **Step 4: Add the thin CLI and output tests**

Create `scripts/dev/check_worktree_alignment.py` with a comprehensive module
docstring, insert the repository root into `sys.path`, parse `--offline` and
`--base-ref` (default `origin/main`), call `inspect_worktree()`, and render:

```python
def _render(diagnostic: Diagnostic) -> str:
    line = (
        f"{diagnostic.severity} {diagnostic.code} "
        f"{diagnostic.subject} -- {diagnostic.message}"
    )
    if diagnostic.remediation:
        line += f"\nRemediation: {diagnostic.remediation}"
    return line


def main(argv=None) -> int:
    args = _parse_args(argv)
    diagnostics = inspect_worktree(
        Path.cwd(), base_ref=args.base_ref, offline=args.offline
    )
    for diagnostic in diagnostics:
        print(_render(diagnostic))
    return 1 if any(d.severity == "ERROR" for d in diagnostics) else 0
```

Test `main(["--offline"])` with a patched `inspect_worktree()` and `capsys`.
Require exact
`ERROR WT004 wip/batch-21 -- branch and origin/main are 3/3 diverged but tree-identical.`
plus a separate `Remediation:` line and exit 1.
Require WT000/WT011 paths to exit 0. Verify `--base-ref upstream/trunk` passes
that exact ref into inspection without changing the default. Offline output
includes WT013 after any state diagnostics and preserves the exit status
derived from errors.

- [ ] **Step 5: Run all guard tests and verify green state**

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
& $pytestExe tests/scripts/dev/test_worktree_guard.py tests/scripts/dev/test_worktree_guard_venv.py -q
```

Expected: all pure, mocked-Git, CLI output, no-mutation, and virtualenv tests
pass.

- [ ] **Step 6: Make the bootstrap requirement canonical**

In `AGENTS.md` Session Bootstrap, add one post-document gate before baseline
tests:

```text
When network access is available, refresh the comparison ref with
`git fetch --prune origin`, then run
`python scripts/dev/check_worktree_alignment.py`. Offline sessions run the
same command with `--offline` and must treat its base result as local-ref-only.
Stop on a nonzero exit. The guard is read-only; follow its remediation and the
existing owner-authorization rule before any history rewrite.
```

In AGENTS Environment Setup, state that a linked worktree reuses the primary
checkout `.venv`; never create a second environment. Tell agents to use the
qualified Python, pytest, and pre-commit paths printed by the guard. In the
Pre-Work Checklist, require a green guard result without restating its state
table.

In `HANDOFF_PROMPT.md`, replace the ad-hoc branch confirmation sentence with a
pointer to the AGENTS worktree gate, then retain `git status` and
`git log --oneline -5` as human-readable evidence. Do not copy command,
decision table, or remediation prose into HANDOFF.

- [ ] **Step 7: Update human documentation and close findings**

In `DEVELOPMENT.md`, change "approved remediation" and "will run" to shipped
present tense. Explain that the guard reports the primary environment but is
not a CI topology gate. End by pointing operational behavior to AGENTS and the
script; do not make DEVELOPMENT agent-bearing.

In `FINDINGS.md`, mark F-WORKTREE-1 resolved only after the live linked
worktree exercise in Step 8 passes. Mark F-WORKTREE-2 resolved only when the
reported pytest/pre-commit paths equal the primary checkout's existing
`.venv`. Keep both active until normal batch-close rotation. Keep F-SWE-1 open
and make it the next action in PLAYBOOK Section 3.

Add the final side-task entry, record deviations and exact measured test count,
refresh SESSION_CONTEXT Section 1, and run docsync fix.

- [ ] **Step 8: Exercise the real aligned linked worktree**

First require a clean Task 2 candidate state after staging is undone or after
the implementation commit; because dirty state intentionally warns, use the
post-commit invocation as the acceptance result. Before committing, run the
offline diagnostic to validate discovery without mutating refs:

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pythonExe = Join-Path $primaryCheckout '.venv\Scripts\python.exe'
& $pythonExe scripts/dev/check_worktree_alignment.py --offline
```

Expected before commit: exit 0, WT010 warning for the intentional dirty tree,
zero behind, an ahead count matching local commits, linked-worktree
classification, and qualified tools under the primary checkout.

After the commit and a successful `git fetch --prune origin`, rerun without
`--offline`:

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pythonExe = Join-Path $primaryCheckout '.venv\Scripts\python.exe'
git fetch --prune origin
& $pythonExe scripts/dev/check_worktree_alignment.py
```

Expected after commit: exit 0, no WT010, zero behind, ahead-only or 0/0,
correct branch `wip/batch-21`, and primary-checkout virtualenv paths. If it
fails, do not change Git history; fix the guard or escalate the actual state.

- [ ] **Step 9: Run canonical gates and commit Task 2**

Before commit, run:

```powershell
$commonGitDir = (Resolve-Path (git rev-parse --git-common-dir)).Path
$primaryCheckout = Split-Path -Parent $commonGitDir
$pythonExe = Join-Path $primaryCheckout '.venv\Scripts\python.exe'
$pytestExe = Join-Path $primaryCheckout '.venv\Scripts\pytest.exe'
$preCommitExe = Join-Path $primaryCheckout '.venv\Scripts\pre-commit.exe'
& $pythonExe scripts/doc_state_sync.py --fix
& $pytestExe -q
& $preCommitExe run --all-files
& $pythonExe scripts/doc_state_sync.py --check
```

Copy the exact passing count into the three live state documents, rerun the
sequence, read each changed file whole, perform blast-radius greps, stage
explicit paths, and commit:

```powershell
git commit -m "fix(worktree): enforce safe post-merge bootstrap" -m "Add a read-only guard for wrong, behind, and rebase-diverged branches,`nreport the sole allowed virtualenv from linked worktrees, and make the`ncross-agent bootstrap stop safely before duplicate work or phantom PRs."
```

- [ ] **Step 10: Complete post-commit acceptance**

Run the clean online guard invocation from Step 8, full pytest, pre-commit,
and docsync check once more. Confirm F-DOCSYNC-5, F-WORKTREE-1, and
F-WORKTREE-2 are resolved, F-SWE-1 is still open and next, the branch is zero
behind `origin/main`, and no implementation commit was pushed without owner
authorization.
