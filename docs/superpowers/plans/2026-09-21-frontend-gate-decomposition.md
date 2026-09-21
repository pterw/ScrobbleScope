# Frontend Gate Decomposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `scripts/dev/frontend_gate.py` (4,361 lines) into focused
`_frontend_gate_*` siblings behind a stable facade, per F-B21-51, with no
change in what the gate checks or how CI runs it.

**Architecture:** `frontend_gate.py` stays the only entry point. It keeps the
import bootstrap, the check registry (`CHECKS`), the runner and the CLI, and
imports every check from the sibling that owns it. Each slice moves one
concern verbatim, re-exports its public names through the facade, moves the
tests of what it moved, and proves with a deliberate mutation that the
browser gate still executes the moved code. Two guard tests written first
make the known traps fail loudly instead of passing silently.

**Tech Stack:** Python 3.13, Playwright (sync API, Chromium + Firefox),
Flask/werkzeug, pytest, ruff.

## Global Constraints

- **Scope:** a side task. No `(Batch N WP-X)` tag. Each commit's PLAYBOOK
  Section 4 entry goes directly after `<!-- DOCSYNC:CURRENT-BATCH-END -->`
  (AGENTS.md "Side-Task Handling").
- **Branch:** the branch PLAYBOOK Section 3 names for side tasks. At the time
  of writing that is `feat/batch22-enrichment`. The worktree guard refuses a
  commit on any other branch (WT003). Changing the branch is the owner's
  decision, never the executor's.
- **One commit per task.** The owner waived the per-commit review pause for
  side tasks on 2026-09-21. Do not push without an explicit owner
  instruction.
- **Behaviour-neutral.** Code moves verbatim. The only edits allowed inside
  moved code are import lines. Task 2 is the one exception: it deletes code
  and says exactly what.
- **The gate result must not change.** Every task ends with
  `[frontend_gate] 30 checks passed in 52 runs across chromium, firefox`
  (Task 2 Part B does not change the count, because no check is removed).
- **Commit format:** Conventional Commits, imperative, subject at most 72
  characters, body explains why (AGENTS.md "Commit Rules"). No
  `Co-authored-by` trailer.
- **Hooks:** never `--no-verify`. If the commit preflight refuses a
  control-plane change, the escape is `SKIP=doc-state-sync-check`, and only
  for that hook.
- **Staging:** stage paths by name. Never `git add -A` or `git add .`. The
  tree has untracked files that belong to other work.
- **Python:** `.venv/Scripts/python.exe` from this worktree (Windows). The
  plan writes `$PY` for it.
- **Docs are read by other agents.** Write in an impersonal voice and plain
  English. Cite names, not line numbers.
- **Global rules** (`docs/agents/global-rules.md`) apply. Rule 3: a helper
  moves into the shared module only when two or more slices read it.
  Otherwise it moves with its single owner.

---

## The four traps this plan closes

Each one would let a slice pass every check while being wrong.

1. **A test patch that stops reaching the code.**
   - `patch("scripts.dev.frontend_gate.create_app")` rebinds a name in the
     facade's namespace.
   - Once `serve_app` lives in `_frontend_gate_runtime`, it looks up
     `create_app` there, and the patch no longer reaches it.
   - The test then boots a real app and may still pass. About 20 patch sites
     are affected.
   - Closed by the patch-target guard (Task 1) and by moving each test with
     its subject.
2. **A patched constant that the check no longer sees.**
   - `patch("scripts.dev.frontend_gate.MIGRATED_PAGES", ("/",))` rebinds the
     facade's name.
   - A sibling that did `from ... import MIGRATED_PAGES` keeps its own
     binding, so the patch never reaches it.
   - Closed the same way as trap 1: patch the module that reads the name.
3. **Shared inventories that must stay one object.**
   - `serve_app` appends the loading page to `MIGRATED_PAGES` and `ALL_PAGES`
     and fills `GATE_JOB_IDS` in place. Every other module has to see those
     same objects.
   - `from ... import` keeps the identity, but rebinding any of them
     anywhere would split them.
   - Closed by an identity test in Task 3 that every slice extends.
4. **Import order against `scrobblescope.config`.**
   - `config.py` reads `LASTFM_API_KEY`, `SPOTIFY_CLIENT_ID` and
     `SPOTIFY_CLIENT_SECRET` from the environment once, when it is first
     imported.
   - The facade sets placeholder keys before importing `app`, because CI's
     secrets arrive empty and CI runs in production mode (F-SWE-4).
   - A sibling that imports `scrobblescope.repositories` and is imported
     above that bootstrap would freeze `None` into config, and the gate
     would refuse to start in CI only.
   - Closed by a subprocess test in Task 1. The facade also keeps the
     bootstrap above every sibling import permanently.

## What CI needs

CI does not need rewriting.
- `.github/workflows/test.yml` runs `python scripts/dev/frontend_gate.py`
  once.
- The facade's `CHECKS` imports every check from whichever module owns it,
  so that one command drives Playwright through every decomposed part.
  `_frontend_gate_results.py` already works this way today.
- What could go wrong is a moved check that drops out of `CHECKS`. It would
  stop running without an error, because `PLANNED_RUNS` is derived from
  `CHECKS`.
- Task 1's registry test closes that: every `check_*` defined in any
  `_frontend_gate_*.py` must be registered exactly once. The test runs in
  the pytest step of the same workflow.
- Each slice's mutation step proves locally that the gate executes the moved
  module.

## Function relevance (checked 2026-09-21, before planning)

- **Dead:** `_computed_shadow` has no caller in the gate, the siblings,
  `scripts/` or `tests/`. Task 2 deletes it rather than moving it.
- **Vestigial:** the Bootstrap CDN fixture.
  - Affected: `_bootstrap_fixture`, `FIXTURE_DIR`, the cdnjs-Bootstrap
    branch of `install_cdn_routes`, `scripts/dev/fixtures/`, and the
    `--live-fonts` flag, which only switches that route.
  - No template requests cdnjs Bootstrap any more; the only cdnjs asset is
    `html2canvas`, which the route passes through.
  - `check_stylesheet_isolation` reads link hrefs, not stylesheet bodies, so
    it would still catch a page that reintroduced Bootstrap.
  - Task 2 Part B removes this chain, subject to the owner's confirmation.
- **Still relevant, deliberately:**
  - `LEGACY_PAGES`: empty, and its comment says why it stays declared.
  - `BOOTSTRAP_MARKER`: the isolation check uses it to detect a regression.
  - The `localhost:8400` abort: it blocks the Impeccable Live developer
    overlay.
- **Selectors:** all 25 id selectors and every class selector the gate uses
  still match `templates/`, `static/js/` or `static/css/`.
  - The one apparent miss, `#mode-tab-`, is a prefix completed at run time
    (`#mode-tab-{mode}`).
- **Overlapping tests:** eight colour tests in `test_frontend_gate.py` cover
  the same functions as `test_frontend_gate_colour.py`.
  - Some carry assertions the other file lacks: the exact failure message,
    the 1920px floor, and the root-20px case.
  - Task 2 moves them verbatim into the colour test file. Merging them is
    out of scope.

## File structure (end state)

| Module | Owns | Approx. lines |
| --- | --- | --- |
| `frontend_gate.py` | Facade: `sys.path`/env bootstrap, viewports, `CHECKS`, groups, runner, CLI, re-exports | ~450 |
| `_frontend_gate_shared.py` | Page inventories (`MIGRATED_PAGES`, `ALL_PAGES`, `LEGACY_PAGES`, `ERROR_PAGE_PATH`), `GATE_JOB_IDS`, `TOGGLE_TIMEOUT_MS`, `_reach_state` | ~110 |
| `_frontend_gate_assets.py` | Stylesheet isolation | ~50 |
| `_frontend_gate_unmatched.py` | The unmatched report check and its width sweep | ~480 |
| `_frontend_gate_forms.py` | Validation, private profile, validator outage and races, year warning, initial visibility | ~420 |
| `_frontend_gate_theme.py` | Theme tokens, divider contrast, persistence, blocked storage, mark, entrance motion, heatmap theme checks | ~720 |
| `_frontend_gate_layout.py` | Fonts, text scaling, touch targets, scale parity and its measurement helpers, empty states | ~1,150 |
| `_frontend_gate_pipeline.py` | Loading composition, progress state machines, spotlight rotation | ~830 |
| `_frontend_gate_runtime.py` | Playwright loading, browser launch, `serve_app`, CDN route policy | ~200 |
| `_frontend_gate_colour.py` | Unchanged (landed 2026-09-11) | 191 |
| `_frontend_gate_results.py` | Unchanged | 497 |

This departs from the 2026-09-11 design in F-B21-51 in two ways, and Task 1
records both in the finding:
- **A shared module is added.** Four slices read the page inventories, and
  two read `_reach_state`. Without a shared module, the siblings would import
  them from the facade while the facade imports the siblings, which is a
  circular import.
- **The `frontend_gate_checks.toml` registry is deferred.** It is a separate
  change of representation, not a move, and it would double the parity
  surface of every slice.

**Facade re-export policy:**
- The facade imports and re-exports every public (no leading underscore)
  name a slice moves; `CHECKS` needs every `check_*` anyway.
- It also re-exports the three private runtime names that external scripts
  import: `_launch_browser`, `_load_playwright` and `serve_app`.
- Other private helpers stay private to their module. Their tests import
  them from there.

## Commands used throughout

```bash
PY=.venv/Scripts/python.exe
# Collected test names; snapshot before a slice, compare after (see protocol).
$PY -m pytest --collect-only -q tests | grep -v test_each_patch_targets   | sed 's/.*:://' | sort > "$SCRATCH/tests_before.txt"
# Gate unit tests only (fast).
$PY -m pytest -q tests/scripts/dev -k frontend_gate
# The browser gate.
$PY scripts/dev/frontend_gate.py
# Undefined or unused names after a move.
.venv/Scripts/ruff check scripts/dev tests/scripts/dev
# Full pre-commit sequence (AGENTS.md "Commit Rules").
$PY scripts/doc_state_sync.py --fix
$PY -m pytest -q
.venv/Scripts/pre-commit run --all-files
$PY scripts/doc_state_sync.py --check
```

## Slice protocol (Tasks 3-10 follow it; each task lists its specifics)

1. Snapshot the collected test names (the command in "Commands used
   throughout"; `$SCRATCH` is any scratch directory outside the repository)
   and note the gate's summary line.
2. Write the slice's parity test file (code given in the task) and run it.
   It must fail with `ModuleNotFoundError` for the new module.
3. Create the module with the header given in the task. Cut the listed
   definitions from `frontend_gate.py` **verbatim**, in their original
   order, including their `#:` comment blocks, and paste them below the
   header.
4. In `frontend_gate.py`, add the facade import given in the task, placed
   **below** the environment bootstrap and alphabetically among the other
   `scripts.dev._frontend_gate_*` imports. Delete now-unused imports that
   ruff reports as `F401`.
5. Run `ruff check`. An `F821 undefined name` means the header is missing an
   import; add it to the module header. Do not change moved code.
6. Move the listed tests out of `tests/scripts/dev/test_frontend_gate.py`
   into the slice's test file, verbatim, with any module-level helper they
   use. Remove imports ruff then reports unused, in both files. Retarget their patches:
   `scripts.dev.frontend_gate.X` becomes `scripts.dev._frontend_gate_<slice>.X`,
   and `patch.object(frontend_gate, ...)` becomes
   `patch.object(_frontend_gate_<slice>, ...)`.
7. Run the gate unit tests. The parity tests, the moved tests and the
   patch-target guard must pass. A guard failure names a test that still
   patches the facade for a name the facade no longer reads; move that test
   too.
8. Re-run the snapshot into `tests_after.txt`, then
   `comm -23 "$SCRATCH/tests_before.txt" "$SCRATCH/tests_after.txt"`.
   Expected: empty. Every test name collected before is still collected,
   whichever file it now lives in. Patch-guard cases are excluded because
   their ids name the file, which is what moves.
9. **Mutation proof.** Copy the slice module to
   `$SCRATCH/<module>.bak`, apply the task's one-line mutation, run the gate,
   and confirm the named FAIL line. Restore with
   `cp "$SCRATCH/<module>.bak" scripts/dev/<module>.py`, then confirm
   `diff` between the two reports nothing. (The module is untracked until
   the commit, so `git checkout` cannot restore it.)
10. Run the full gate and confirm the unchanged summary line.
11. Docs, in the same commit:
    - `.claude/SESSION_CONTEXT.md`: add the module to the `scripts/dev/` tree
      and its import line to the import graph block (both hand-maintained;
      follow the `_frontend_gate_colour.py` lines).
    - PLAYBOOK Section 4: a short dated side-task entry directly after
      `<!-- DOCSYNC:CURRENT-BATCH-END -->`.
12. Run the full pre-commit sequence, stage by name, and commit.

---

### Task 1: Revise F-B21-51, refresh PLAYBOOK Section 3, pin the invariants

**Files:**
- Modify: `FINDINGS.md` (the F-B21-51 section)
- Modify: `PLAYBOOK.md` (Section 3 bullets and a Section 4 side-task entry)
- Create: `tests/scripts/dev/gate_parity.py`
- Create: `tests/scripts/dev/test_frontend_gate_split.py`

**Interfaces:**
- Produces:
  - `gate_parity.defined_names(module) -> set[str]`
  - `gate_parity.names_read_in_functions(module) -> set[str]`
  - `gate_parity.gate_modules() -> list[ModuleType]`
  - The test file `test_frontend_gate_split.py`, which later slices extend
    with nothing: it discovers new modules and test files by glob.

- [x] **Step 1: Write the shared test helpers**

`tests/scripts/dev/gate_parity.py`:

```python
"""Source-level facts about the frontend gate modules, for split parity tests.

F-B21-51 splits `scripts/dev/frontend_gate.py` into `_frontend_gate_*`
siblings. A move that forgets a name, or a test patch left aimed at a module
that no longer reads the name, both pass on the happy path. These helpers read
the modules' source so the parity tests can assert what each module *defines*
and *reads*, rather than what it happens to import.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from types import ModuleType

GATE_DIR = Path(__file__).resolve().parents[3] / "scripts" / "dev"


def _tree(module: ModuleType) -> ast.Module:
    """Parse the module's own source file."""
    return ast.parse(Path(inspect.getfile(module)).read_text(encoding="utf-8"))


def defined_names(module: ModuleType) -> set[str]:
    """Top-level names the module defines itself; imported names excluded."""
    names: set[str] = set()
    for node in _tree(module).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def names_read_in_functions(module: ModuleType) -> set[str]:
    """Every bare name the module's functions look up when they run.

    This is exactly the set a `patch("<module>.<name>")` can affect: a name
    read at call time through the module's globals.
    """
    names: set[str] = set()
    for node in ast.walk(_tree(module)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load):
                    names.add(inner.id)
    return names


def gate_modules() -> list[ModuleType]:
    """The facade plus every `_frontend_gate_*` sibling, imported."""
    stems = ["frontend_gate"] + sorted(
        path.stem for path in GATE_DIR.glob("_frontend_gate_*.py")
    )
    return [importlib.import_module(f"scripts.dev.{stem}") for stem in stems]
```

- [x] **Step 2: Write the three guard tests**

`tests/scripts/dev/test_frontend_gate_split.py`:

```python
"""Invariants the frontend gate split must keep (F-B21-51).

Three ways a split can pass every existing check while being wrong:

1. A moved check drops out of `CHECKS`. Nothing fails, because the planned
   run count is derived from the same tuple; the check just stops running in
   CI.
2. A test keeps patching `frontend_gate.X` after the code that reads `X`
   moved. The patch lands in a namespace nobody reads, and the test runs
   against the real object.
3. A sibling imports `scrobblescope` above the facade's environment
   bootstrap, and `scrobblescope.config` freezes empty provider keys, so the
   gate refuses to start in CI's production mode only.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.dev import frontend_gate
from tests.scripts.dev.gate_parity import (
    defined_names,
    gate_modules,
    names_read_in_functions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_DIR = Path(__file__).resolve().parent

_PATCH_STRING = re.compile(
    r'patch\(\s*"scripts\.dev\.(?P<module>\w+)\.(?P<name>\w+)"', re.MULTILINE
)
_PATCH_OBJECT = re.compile(
    r'patch\.object\(\s*(?P<module>_?frontend_gate\w*)\s*,\s*"(?P<name>\w+)"',
    re.MULTILINE,
)


def _module_for_test_file(path: Path) -> str:
    """test_frontend_gate.py -> frontend_gate; test_frontend_gate_x.py -> _frontend_gate_x."""
    stem = path.stem.removeprefix("test_")
    return stem if stem == "frontend_gate" else f"_{stem}"


def _patch_targets() -> list[tuple[str, str, str]]:
    """(test file, module, name) for every gate patch in the gate test files."""
    targets = []
    for path in sorted(TEST_DIR.glob("test_frontend_gate*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in (_PATCH_STRING, _PATCH_OBJECT):
            for match in pattern.finditer(text):
                targets.append((path.name, match["module"], match["name"]))
    return targets


def test_every_check_in_every_gate_module_is_registered_once() -> None:
    registered = [entry[1] for entry in frontend_gate.CHECKS]
    assert len(registered) == len(set(registered)), "a check is registered twice"
    defined = {
        getattr(module, name)
        for module in gate_modules()
        for name in defined_names(module)
        if name.startswith("check_") and callable(getattr(module, name))
    }
    missing = sorted(check.__name__ for check in defined - set(registered))
    assert not missing, f"defined but never run by the gate: {missing}"


def test_the_patch_target_scan_finds_the_known_patches() -> None:
    # Guards the guard: if the regexes stop matching, the next test passes
    # vacuously over an empty list.
    names = {name for _file, _module, name in _patch_targets()}
    assert {"create_app", "make_server", "CHECKS", "run_checks"} <= names


@pytest.mark.parametrize(
    ("test_file", "module", "name"),
    _patch_targets(),
    ids=lambda value: str(value),
)
def test_each_patch_targets_the_module_that_reads_the_name(
    test_file: str, module: str, name: str
) -> None:
    expected = _module_for_test_file(Path(test_file))
    assert module == expected, (
        f"{test_file} patches {module}.{name}; tests patch only the module "
        f"they cover ({expected}). Move the test beside its subject."
    )
    owner = importlib.import_module(f"scripts.dev.{module}")
    assert name in names_read_in_functions(owner), (
        f"{test_file} patches {module}.{name}, but no function in {module} "
        f"reads {name}, so the patch reaches nothing."
    )


def test_the_gate_sets_provider_keys_before_config_reads_them() -> None:
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            "LASTFM_API_KEY",
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET",
            "SECRET_KEY",
            "DEBUG_MODE",
        }
    }
    code = (
        "import scripts.dev.frontend_gate\n"
        "from scrobblescope import config\n"
        "print('KEY=' + str(config.LASTFM_API_KEY))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "KEY=frontend-gate-placeholder" in result.stdout
```

- [x] **Step 3: Run the guards; they pass on the unsplit gate**

Run: `$PY -m pytest -q tests/scripts/dev/test_frontend_gate_split.py`
Expected: all PASS. The registry test finds 30 checks. The patch-target
test is parametrized over every patch in `test_frontend_gate.py`, all of
which target `frontend_gate` today.

- [x] **Step 4: Prove each guard can fail, then revert each change**

The guards must be shown to fail on a real defect:
1. Comment out the `("fonts", check_fonts, ...)` entry in `CHECKS`. The
   registry test must FAIL with `defined but never run by the gate:
   ['check_fonts']`. Revert.
2. In `test_frontend_gate.py`, change one
   `patch("scripts.dev.frontend_gate.create_app")` to
   `patch("scripts.dev.frontend_gate.GATE_SECRET_KEY")`. The patch test must
   FAIL with `no function in frontend_gate reads GATE_SECRET_KEY`. Revert.
3. In `frontend_gate.py`, temporarily add
   `import scrobblescope.repositories  # noqa: E402, F401` directly above
   the `if not os.environ.get("SECRET_KEY"):` block. The subprocess test
   must FAIL: `KEY=` is followed by `None`. Revert.

Confirm with `git diff --stat` that only the two new test files and the doc
edits remain.

- [x] **Step 5: Revise F-B21-51**

Replace the F-B21-51 section, from its heading down to its `Source:` line,
with the text below. Keep the heading unchanged. Do not write "resolved" or
"closed" about any *other* finding in this text: DOC023 reads those words as
a lifecycle claim.

```markdown
### F-B21-51: frontend_gate.py is nine times its largest sibling

`scripts/dev/frontend_gate.py` is 4,361 lines (2026-09-21). The largest other
module in `scripts/dev/` is `_frontend_gate_results.py` at 497, and the
largest unrelated one is `tailwind_build.py` at 404. AGENTS.md "Proposal and
Design Rules" item 3 compares against the largest peer rather than a line
threshold, and this is roughly ten times it. One module owns the import
bootstrap, the server fixture, CDN route policy, browser lifecycle, 27 check
implementations, their measurement helpers, the registry and the CLI.

Status: open. Rescoped 2026-09-21 from a batch work package to an
owner-approved side task, because pairing it with the routes and
orchestrator split made that batch far larger than planned. Plan of record:
`docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md`, one
commit per slice.

**Design, agreed 2026-09-11 and amended 2026-09-21.** `frontend_gate.py`
stays the only entry point and a stable facade, following `worktree_guard.py`,
with the `_frontend_gate_*` sibling convention `_frontend_gate_results.py`
set. Slice order: shared, assets, unmatched, forms, theme, layout, pipeline,
runtime.

| Module | Owns |
| --- | --- |
| `frontend_gate.py` | Facade: `sys.path` and environment bootstrap, viewports, `CHECKS`, groups, runner, CLI, re-exports |
| `_frontend_gate_shared.py` | Page inventories, `GATE_JOB_IDS`, `TOGGLE_TIMEOUT_MS`, `_reach_state` |
| `_frontend_gate_assets.py` | Stylesheet isolation |
| `_frontend_gate_unmatched.py` | The unmatched report check and its width sweep |
| `_frontend_gate_forms.py` | Validation, private profile, validator outage and races, year warning, initial visibility |
| `_frontend_gate_theme.py` | Theme tokens, divider contrast, persistence, blocked storage, mark, entrance motion, heatmap theme checks |
| `_frontend_gate_layout.py` | Fonts, text scaling, touch targets, scale parity, empty states |
| `_frontend_gate_pipeline.py` | Loading composition, progress state machines, spotlight |
| `_frontend_gate_runtime.py` | Playwright loading, browser launch, `serve_app`, CDN route policy |
| `_frontend_gate_colour.py` | Pure colour and contrast maths -- landed 2026-09-11 |

Two amendments to the 2026-09-11 design. A shared module is added, because
four slices read the page inventories and two read `_reach_state`; importing
them back from the facade would be circular. The `frontend_gate_checks.toml`
registry is deferred: it changes representation rather than location, and
folding it into each move would double every slice's parity surface. It
remains a candidate once the split has landed.

**Traps the plan closes.** A test patch aimed at the facade stops reaching
code that moved, and a patched constant stops reaching a sibling that
imported it; both still pass. `serve_app` mutates `MIGRATED_PAGES`,
`ALL_PAGES` and `GATE_JOB_IDS` in place, so every module must share those
objects. `scrobblescope.config` reads the provider keys at first import, so
no sibling may import `scrobblescope` above the facade's environment
bootstrap. `tests/scripts/dev/test_frontend_gate_split.py` pins the registry,
the patch targets and the import order.

**Slice 1 landed 2026-09-11.** The seven pure helpers moved to
`_frontend_gate_colour.py` and are re-exported by the facade, pinned by the
parity tests in `tests/scripts/dev/test_frontend_gate_colour.py`. They went
first because they take no `page`, so the browser gate was not needed to
prove the move.

Source: PR #227 commit-range audit, 2026-09-09.
```

- [x] **Step 6: Refresh PLAYBOOK Section 3 and add the Section 4 entry**

Section 3 still describes PR #235 as open and the MusicBrainz contact as
local-only. Replace those two bullets with:

```markdown
- **PR #235 merged `test` into `main`** on 2026-09-21, and **PR #237** then
  carried the eleven between-batch commits into `test`. **PR #238**
  (`test` -> `main`) carries them on to `main`; a merge to `main` deploys to
  Fly.io through Fly's GitHub integration, not a repository workflow.
- **`MUSICBRAINZ_CONTACT` is set on Fly.io** (2026-09-21, the project's
  GitHub URL), as well as in the local `.env`.
- **Side task in progress: the frontend gate split (F-B21-51).** Plan of
  record: `docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md`.
```

Section 4 entry, directly after `<!-- DOCSYNC:CURRENT-BATCH-END -->`:

```markdown
### 2026-09-21 - Frontend gate split: invariants pinned first (F-B21-51)

Side task, no batch tag, owner-approved 2026-09-21. F-B21-51 is rescoped from
a batch work package to a side task with a written plan, and amended: a shared
module is added and the TOML registry is deferred. Before any code moves,
`tests/scripts/dev/test_frontend_gate_split.py` pins three invariants that
would otherwise fail silently: every defined check is registered, every test
patch targets a module that reads the name, and the facade's environment
bootstrap precedes any `scrobblescope` import. Each guard was shown to fail on
a deliberate defect before being kept.
```

- [x] **Step 7: Full sequence and commit**

Run the full pre-commit sequence (see "Commands used throughout"). Then:

```bash
git add FINDINGS.md PLAYBOOK.md .claude/SESSION_CONTEXT.md \
  tests/scripts/dev/gate_parity.py tests/scripts/dev/test_frontend_gate_split.py \
  docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md
git commit -m "test(gate): Pin the invariants the frontend gate split must keep" \
  -m "F-B21-51 is rescoped to a side task with a plan of record. Three ways
the split could pass every check while being wrong are now tests: a check
dropped from the registry, a test patch left aimed at a namespace nobody
reads, and a sibling importing scrobblescope before the environment
bootstrap. Each guard was shown to fail on a deliberate defect."
```

---

### Task 2: Delete what is no longer relevant before moving anything

Part A is certain. Part B needs the owner's confirmation, which is asked for
when this plan is handed over. **If the owner keeps the Bootstrap fixture,
skip Part B entirely**, and in Task 10 move `FIXTURE_DIR`,
`_bootstrap_fixture` and their test with the runtime.

**Files:**
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate_colour.py`
- Delete (Part B): `scripts/dev/fixtures/bootstrap_fixture.css`,
  `scripts/dev/fixtures/README.md`

**Interfaces:**
- Produces:
  - Part B: `install_cdn_routes(page, live_fonts: bool = False) -> None`
    keeps its name and signature. Its only remaining job is the
    `localhost:8400` abort, which `live_fonts=True` skips. That keeps
    `--live-fonts` meaningful for a local run with the overlay.
  - `FIXTURE_DIR` and `_bootstrap_fixture` no longer exist.

- [x] **Step 1 (Part A): Confirm `_computed_shadow` is unused, then delete it**

Run: `grep -rn "_computed_shadow" scripts tests`
Expected: exactly one match, its own `def` line. Delete the function (the
`def _computed_shadow(page, value: str) -> str:` block, 13 lines).

- [x] **Step 2 (Part A): Move the eight colour tests to the file that covers colour**

Move these tests verbatim from `test_frontend_gate.py` to the end of
`test_frontend_gate_colour.py`, under a comment line
`# Carried from test_frontend_gate.py when the colour tests were collected here.`:
- `test_parse_rgb_string_reads_rgb_and_rgba_forms`
- `test_composite_over_blends_by_alpha`
- `test_relative_luminance_orders_black_grey_white`
- `test_contrast_ratio_is_symmetric_and_maximal_for_black_on_white`
- `test_worst_divider_contrast_is_the_minimum_across_surfaces`
- `test_divider_contrast_failure_boundary_is_exactly_3_to_1`
- `test_divider_contrast_failure_names_the_token_it_checks`
- `test_clamp_px_resolves_floor_preferred_and_ceiling`

Remove the colour names from `test_frontend_gate.py`'s import block that
are now unused (`ruff check` reports them).

- [x] **Step 3 (Part B): Strip the Bootstrap route from `install_cdn_routes`**

Replace the body of `install_cdn_routes` below its docstring with:

```python
    if live_fonts:
        return
    page.route("http://localhost:8400/**", lambda route: route.abort())
```

Rewrite its docstring to:

```python
    """Keep developer-only origins out of the gate's pages.

    Impeccable Live is a developer overlay injected into base.html while
    visual review is active; the gate must stay independent of it, so its
    origin is aborted. ``live_fonts`` skips that for a local calibration run.

    The Adobe Fonts kit always loads from its real origin: its families are
    licensed web fonts, and re-hosting or synthesizing them would misdeclare
    licensed typefaces (owner ruling 2026-09-07, no exceptions per family).
    A stall there costs the page its webfonts, never the gate its pass,
    because check_fonts reports misses as advisory WARN lines.

    The cdnjs Bootstrap fixture this used to serve was removed on 2026-09-21:
    no template requests Bootstrap, and check_stylesheet_isolation reads link
    hrefs, so it still catches a page that reintroduces it.
    """
```

Delete `FIXTURE_DIR` with its `#:` comment and `_bootstrap_fixture`. If no
other function uses `functools.cache`, delete that import too; ruff reports
it.

Update the `--live-fonts` help text to:
`"let the Impeccable Live developer overlay load (local visual review only)"`.

- [x] **Step 4 (Part B): Update the tests**

- In `test_install_cdn_routes_fulfills_bootstrap_and_passes_the_kit`, rename
  the test to `test_install_cdn_routes_aborts_only_the_overlay_origin`.
  Replace its body with this assertion set, keeping the docstring style:

```python
def test_install_cdn_routes_aborts_only_the_overlay_origin() -> None:
    """Only the developer overlay's origin is routed; everything else is untouched."""
    page = MagicMock()
    frontend_gate.install_cdn_routes(page)
    assert page.route.call_count == 1
    pattern, handler = page.route.call_args.args
    assert pattern == "http://localhost:8400/**"
    route = MagicMock()
    handler(route)
    route.abort.assert_called_once_with()
```

- Delete `test_bootstrap_fixture_is_lazy_cached_and_retries_failed_reads`.
- `test_install_cdn_routes_respects_live_fonts_flag` and
  `test_main_preserves_route_policy_through_real_runner` stay. Run them. If
  either asserts on the Bootstrap route, change that assertion to the
  `localhost:8400` route, not to nothing.

- [x] **Step 5 (Part B): Delete the fixture directory and repoint live docs**

```bash
git rm scripts/dev/fixtures/bootstrap_fixture.css scripts/dev/fixtures/README.md
grep -rn "bootstrap_fixture\|fixtures/README" --include=*.md --include=*.py . \
  | grep -vE "/(history|superpowers|\.superpowers|logarchive|graphify-out|\.venv)/"
```

Expected: no matches, or only matches in the files this task already edits.
Repoint any live document (not history) that describes the fixture.

- [x] **Step 6: Verify**

- Gate unit tests: PASS.
- The protocol's name comparison lists exactly two names:
  `test_bootstrap_fixture_is_lazy_cached_and_retries_failed_reads` (deleted)
  and `test_install_cdn_routes_fulfills_bootstrap_and_passes_the_kit`
  (renamed). If Part B was skipped, it lists nothing.
- Gate summary line unchanged. Stylesheet isolation still passes on every
  page, which proves no page needed the fixture.

- [x] **Step 7: PLAYBOOK Section 4 entry, full sequence, commit**

```markdown
### 2026-09-21 - Frontend gate: dead code removed before the split (F-B21-51)

Side task, no batch tag. `_computed_shadow` had no caller anywhere and is
deleted rather than moved. The cdnjs Bootstrap fixture is removed: no template
requests Bootstrap, and the isolation check reads hrefs, so it still catches a
regression; `install_cdn_routes` keeps only the Impeccable Live overlay abort.
Eight colour tests moved verbatim into the colour test file.
```

```bash
git add scripts/dev/frontend_gate.py tests/scripts/dev/test_frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_colour.py PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Delete dead helpers before the split moves them" \
  -m "Moving code nobody calls would carry it into a new module with a fresh
look of relevance. _computed_shadow had no caller. The Bootstrap CDN fixture
served a stylesheet no template requests any more; the isolation check reads
hrefs, so a reintroduced Bootstrap link still fails it."
```

(The `git rm` in Step 5 already staged the fixture deletions.)

---

### Task 3: Shared slice

**Files:**
- Create: `scripts/dev/_frontend_gate_shared.py`
- Create: `tests/scripts/dev/test_frontend_gate_shared.py`
- Modify: `scripts/dev/frontend_gate.py`

**Interfaces:**
- Produces (every later slice imports these from
  `scripts.dev._frontend_gate_shared`):
  - `ERROR_PAGE_PATH: str`
  - `MIGRATED_PAGES: list[str]`
  - `LEGACY_PAGES: list[str]`
  - `ALL_PAGES: list[str]`
  - `GATE_JOB_IDS: dict[str, str]`
  - `TOGGLE_TIMEOUT_MS: int`
  - `_reach_state(page, actions) -> None`

**Definitions to move, in file order:** `TOGGLE_TIMEOUT_MS`,
`ERROR_PAGE_PATH`, `MIGRATED_PAGES`, `GATE_JOB_IDS`, `LEGACY_PAGES`,
`ALL_PAGES`, `_reach_state`, each with its `#:` comment block.
`BOOTSTRAP_MARKER`, `TAILWIND_MARKER` and `_SERVE_APP_LOCK` sit among them
and do **not** move now: the markers go with assets, and the lock goes with
runtime.

- [x] **Step 1: Record the collection count and gate line**

- [x] **Step 2: Write the failing parity test**

`tests/scripts/dev/test_frontend_gate_shared.py`:

```python
"""Parity tests for the shared slice of the frontend gate (F-B21-51).

The inventories here are mutated in place by `serve_app` (the loading page is
appended for the duration of a run), so every module must hold the *same*
objects. A rebinding anywhere would leave one module checking a list the
fixture never extended.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_shared, frontend_gate
from tests.scripts.dev.gate_parity import defined_names, gate_modules

MOVED = (
    "TOGGLE_TIMEOUT_MS",
    "ERROR_PAGE_PATH",
    "MIGRATED_PAGES",
    "GATE_JOB_IDS",
    "LEGACY_PAGES",
    "ALL_PAGES",
    "_reach_state",
)
SHARED_OBJECTS = ("MIGRATED_PAGES", "ALL_PAGES", "GATE_JOB_IDS")


@pytest.mark.parametrize("name", MOVED)
def test_the_shared_module_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_shared)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", SHARED_OBJECTS)
def test_every_module_holding_an_inventory_holds_the_same_object(name: str) -> None:
    original = getattr(_frontend_gate_shared, name)
    for module in gate_modules():
        if hasattr(module, name):
            assert getattr(module, name) is original, module.__name__


def test_reach_state_clicks_and_selects_with_the_toggle_budget() -> None:
    page = MagicMock()
    target = page.locator.return_value.first
    _frontend_gate_shared._reach_state(
        page, (("click", "#a"), ("select", "#b", "decade"))
    )
    target.click.assert_called_once_with(
        timeout=_frontend_gate_shared.TOGGLE_TIMEOUT_MS
    )
    target.select_option.assert_called_once_with(
        "decade", timeout=_frontend_gate_shared.TOGGLE_TIMEOUT_MS
    )
    assert [c.args[0] for c in page.locator.call_args_list] == ["#a", "#b"]


def test_reach_state_refuses_an_unknown_action() -> None:
    with pytest.raises(ValueError, match="unknown touch-target action 'hover'"):
        _frontend_gate_shared._reach_state(MagicMock(), (("hover", "#a"),))
```

Run: `$PY -m pytest -q tests/scripts/dev/test_frontend_gate_shared.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'scripts.dev._frontend_gate_shared'`.

- [x] **Step 3: Create the module**

Header of `scripts/dev/_frontend_gate_shared.py`, followed by the moved
definitions:

```python
"""State and helpers more than one frontend gate slice reads.

F-B21-51 splits the gate by concern. What lives here is what two or more
slices read, so each slice can import it without importing the facade that
imports them (a cycle). The page inventories and `GATE_JOB_IDS` are mutated in
place by `serve_app` for the length of a run; importing them by name keeps
every module on the same objects, and nothing may rebind them.
"""

from __future__ import annotations
```

- [x] **Step 4: Facade import**

In `frontend_gate.py`, below the environment bootstrap, with the other
sibling imports:

```python
from scripts.dev._frontend_gate_shared import (  # noqa: E402
    ALL_PAGES,
    ERROR_PAGE_PATH,
    GATE_JOB_IDS,
    LEGACY_PAGES,
    MIGRATED_PAGES,
    TOGGLE_TIMEOUT_MS,
    _reach_state,
)
```

If ruff reports any of these as `F401` (unused in the facade), keep the
import and add `F401` to its `noqa`, with the reason on the line above:
`# Re-exported: the facade keeps the public names stable (F-B21-51).`

- [x] **Step 5: Ruff, tests, count, gate**

There are no tests to move: the one patch of `MIGRATED_PAGES` targets
`check_theme_persistence`, which still lives in the facade and reads the
facade's binding. Task 7 moves it.
- Expected: the parity and guard tests PASS.
- Expected: the name comparison in protocol step 8 is empty.

- [x] **Step 6: Mutation proof**

Make `raise RuntimeError("mutation probe")` the first statement of
`_reach_state`. The gate must print `raised RuntimeError: mutation probe`
for `touch targets` and for the form checks that drive a state, such as
`validation feedback`. That shows both callers reach the shared object
through the facade's import. Restore it as the protocol describes.

- [x] **Step 7: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_shared.py # page inventories and helpers two or more slices read`
- Import-graph line:
  `dev/_frontend_gate_shared.py <- (leaf; standard library only)`
- Add `dev/_frontend_gate_shared` to the `dev/frontend_gate.py` line.
- Section 4 entry heading:
  `### 2026-09-21 - Frontend gate split: shared slice (F-B21-51)`, with 2-4
  sentences on what moved and the identity invariant.

```bash
git add scripts/dev/_frontend_gate_shared.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_shared.py PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move what several slices read into a shared module" \
  -m "Four slices read the page inventories and two read _reach_state.
Leaving them in the facade would make every sibling import the module that
imports it. serve_app mutates the inventories in place, so a test now pins
that every module holds the same objects."
```

---

### Task 4: Assets slice

**Files:**
- Create: `scripts/dev/_frontend_gate_assets.py`
- Create: `tests/scripts/dev/test_frontend_gate_assets.py`
- Modify: `scripts/dev/frontend_gate.py`

**Interfaces:**
- Consumes: `ALL_PAGES` from `_frontend_gate_shared`.
- Produces: `check_stylesheet_isolation(page, base_url: str) -> list[str]`,
  plus the constants `BOOTSTRAP_MARKER` and `TAILWIND_MARKER`.

**Definitions to move:** `BOOTSTRAP_MARKER`, `TAILWIND_MARKER`,
`_stylesheet_hrefs`, `check_stylesheet_isolation`.

- [x] **Step 1: Record the count and gate line**

- [x] **Step 2: Failing parity test**

`tests/scripts/dev/test_frontend_gate_assets.py`:

```python
"""Parity and behaviour tests for the assets slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_assets, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

MOVED = (
    "BOOTSTRAP_MARKER",
    "TAILWIND_MARKER",
    "_stylesheet_hrefs",
    "check_stylesheet_isolation",
)
REEXPORTED = ("BOOTSTRAP_MARKER", "TAILWIND_MARKER", "check_stylesheet_isolation")


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_assets)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_assets, name)


def _page_with(hrefs: list[str]) -> MagicMock:
    page = MagicMock()
    page.eval_on_selector_all.return_value = hrefs
    return page


@pytest.mark.parametrize(
    ("hrefs", "count"),
    [
        ([], 0),
        (["/static/css/tailwind.css", "https://cdnjs.cloudflare.com/x/bootstrap.min.css"], 2),
    ],
)
def test_isolation_fails_unless_exactly_one_framework_sheet(hrefs, count) -> None:
    with patch("scripts.dev._frontend_gate_assets.ALL_PAGES", ["/"]):
        failures = _frontend_gate_assets.check_stylesheet_isolation(
            _page_with(hrefs), "http://127.0.0.1:0"
        )
    assert failures == [
        f"/ loads {count} framework stylesheets, expected exactly 1: {hrefs}"
    ]


def test_isolation_passes_one_tailwind_sheet_beside_other_css() -> None:
    hrefs = ["/static/css/tailwind.css", "https://use.typekit.net/rwy8ghw.css"]
    with patch("scripts.dev._frontend_gate_assets.ALL_PAGES", ["/"]):
        assert (
            _frontend_gate_assets.check_stylesheet_isolation(
                _page_with(hrefs), "http://127.0.0.1:0"
            )
            == []
        )
```

Expected: FAIL, `ModuleNotFoundError`.

- [x] **Step 3: Module header**

```python
"""Stylesheet isolation: each page loads exactly one framework stylesheet.

A slice of the frontend gate (F-B21-51). Bootstrap and daisyUI both claim
.btn, .card and .modal, and Tailwind's preflight would reset a Bootstrap page,
so two framework sheets on one page is a collision, not a style choice.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_shared import ALL_PAGES
```

- [x] **Step 4: Facade import**

```python
from scripts.dev._frontend_gate_assets import (  # noqa: E402, F401
    BOOTSTRAP_MARKER,
    TAILWIND_MARKER,
    check_stylesheet_isolation,
)
```

- [x] **Step 5: Ruff, tests, name comparison, gate**

- [x] **Step 6: Mutation proof**

Insert `return ["mutation probe"]` as the first statement of
`check_stylesheet_isolation`. The gate must print
`[frontend_gate] FAIL chromium: stylesheet isolation [desktop]: mutation probe`
and the same line for `firefox`, which proves the Firefox canary group also
reaches the moved module. Revert.

- [x] **Step 7: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_assets.py # stylesheet isolation`
- Import-graph line:
  `dev/_frontend_gate_assets.py <- dev/_frontend_gate_shared`
- Section 4 entry:
  `### 2026-09-21 - Frontend gate split: assets slice (F-B21-51)`

```bash
git add scripts/dev/_frontend_gate_assets.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_assets.py PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move stylesheet isolation into its own slice" \
  -m "The smallest browser-coupled slice goes first, so the pattern (move
verbatim, re-export, move tests, prove the gate runs the new module with a
deliberate failure) is shown on a check that fits on one screen."
```

---

### Task 5: Unmatched slice

**Files:**
- Create: `scripts/dev/_frontend_gate_unmatched.py`
- Create: `tests/scripts/dev/test_frontend_gate_unmatched.py`
- Modify: `scripts/dev/frontend_gate.py`

**Interfaces:**
- Consumes: `add_job_unmatched`, `create_job`, `delete_job` from
  `scrobblescope.repositories`.
- Produces: `check_unmatched_report(page, base_url: str) -> list[str]`,
  plus the constants `UNMATCHED_TWO_PANEL_MIN`, `UNMATCHED_SWEEP_WIDTHS` and
  `UNMATCHED_MIN_TITLE_WIDTH`.

**Definitions to move:** `UNMATCHED_TWO_PANEL_MIN`,
`UNMATCHED_SWEEP_WIDTHS`, `UNMATCHED_MIN_TITLE_WIDTH`,
`_unmatched_panel_width_sweep`, `check_unmatched_report`.

- [x] **Step 1: Record the count and gate line**

- [x] **Step 2: Failing parity test**

`tests/scripts/dev/test_frontend_gate_unmatched.py`:

```python
"""Parity and behaviour tests for the unmatched slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_unmatched, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

MOVED = (
    "UNMATCHED_TWO_PANEL_MIN",
    "UNMATCHED_SWEEP_WIDTHS",
    "UNMATCHED_MIN_TITLE_WIDTH",
    "_unmatched_panel_width_sweep",
    "check_unmatched_report",
)
REEXPORTED = (
    "UNMATCHED_TWO_PANEL_MIN",
    "UNMATCHED_SWEEP_WIDTHS",
    "UNMATCHED_MIN_TITLE_WIDTH",
    "check_unmatched_report",
)


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_unmatched)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_unmatched, name)


def _sweeping_page(columns: int, title_width: float) -> MagicMock:
    """A page whose layout never changes, whatever width it is given."""
    page = MagicMock()
    page.viewport_size = {"width": 1280, "height": 800}

    def evaluate(script, *_args):
        if "gridTemplateColumns" in script:
            return {"columns": columns, "titles": [title_width, 200.0]}
        return None

    page.evaluate.side_effect = evaluate
    return page


def test_sweep_reports_wrong_columns_and_a_starved_title_then_restores() -> None:
    page = _sweeping_page(columns=2, title_width=20.0)
    failures = _frontend_gate_unmatched._unmatched_panel_width_sweep(page)
    widths = _frontend_gate_unmatched.UNMATCHED_SWEEP_WIDTHS
    below = [w for w in widths if w < _frontend_gate_unmatched.UNMATCHED_TWO_PANEL_MIN]
    assert sum("panel columns, expected 1" in f for f in failures) == len(below)
    assert sum("album title" in f and "20px wide" in f for f in failures) == len(widths)
    assert page.set_viewport_size.call_args.args[0] == {"width": 1280, "height": 800}


def test_sweep_restores_the_viewport_when_measurement_raises() -> None:
    page = _sweeping_page(columns=2, title_width=200.0)
    page.evaluate.side_effect = RuntimeError("page crashed")
    with pytest.raises(RuntimeError):
        _frontend_gate_unmatched._unmatched_panel_width_sweep(page)
    assert page.set_viewport_size.call_args.args[0] == {"width": 1280, "height": 800}
```

Expected: FAIL, `ModuleNotFoundError`.

- [x] **Step 3: Module header**

```python
"""The unmatched report check: populated contract, disclosure, and width sweep.

A slice of the frontend gate (F-B21-51). The sweep exists because none of the
gate's viewport profiles lands between 1024px and the two-panel breakpoint,
which is how a 20-36px album title shipped at 1024px (owner ruling
2026-09-13).
"""

from __future__ import annotations

import json

from scrobblescope.repositories import add_job_unmatched, create_job, delete_job
```

If ruff reports another undefined name (F821), add its import here.

- [x] **Step 4: Facade import**

```python
from scripts.dev._frontend_gate_unmatched import (  # noqa: E402, F401
    UNMATCHED_MIN_TITLE_WIDTH,
    UNMATCHED_SWEEP_WIDTHS,
    UNMATCHED_TWO_PANEL_MIN,
    check_unmatched_report,
)
```

Delete `json` from the facade's imports if ruff reports it unused.

- [x] **Step 5: Ruff, tests, name comparison, gate**

- [x] **Step 6: Mutation proof**

Set `UNMATCHED_MIN_TITLE_WIDTH = 960`. The gate must print
`FAIL chromium: unmatched report [...]: unmatched album title at ...px is ...px wide, expected at least 960px`
lines. Revert.

- [x] **Step 7: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_unmatched.py # unmatched report contract and width sweep`
- Import-graph line:
  `dev/_frontend_gate_unmatched.py <- repositories`
- Section 4 entry:
  `### 2026-09-21 - Frontend gate split: unmatched slice (F-B21-51)`

```bash
git add scripts/dev/_frontend_gate_unmatched.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_unmatched.py PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move the unmatched report check into its own slice" \
  -m "The largest single check (422 lines) and its breakpoint sweep move
together with their constants. The sweep gains its first unit tests,
including that it restores the viewport when measurement raises."
```

---

### Task 6: Forms slice

**Files:**
- Create: `scripts/dev/_frontend_gate_forms.py`
- Create: `tests/scripts/dev/test_frontend_gate_forms.py`
- Modify: `scripts/dev/frontend_gate.py`

**Interfaces:**
- Consumes: `_reach_state` from `_frontend_gate_shared`.
- Produces, each with the signature `(page, base_url: str) -> list[str]`:
  - `check_validation_feedback`
  - `check_private_profile_is_blocked`
  - `check_validator_outage_is_recoverable`
  - `check_stale_validator_failure_is_discarded`
  - `check_current_validator_failure_replaces_old_verdict`
  - `check_true_warning_survives`
  - `check_initial_visibility`
- Also produces the constant `HIDDEN_ON_LOAD`.

**Definitions to move, in file order:**
- `HIDDEN_ON_LOAD`
- `check_validation_feedback`
- `check_private_profile_is_blocked`
- `check_validator_outage_is_recoverable`
- `_collecting_handler`
- `check_stale_validator_failure_is_discarded`
- `check_current_validator_failure_replaces_old_verdict`
- `check_true_warning_survives`
- `_year_warning`
- `check_initial_visibility`

- [x] **Step 1: Record the count and gate line**

- [x] **Step 2: Failing parity test**

`tests/scripts/dev/test_frontend_gate_forms.py`:

```python
"""Parity and behaviour tests for the forms slice of the frontend gate."""

from __future__ import annotations

import inspect

import pytest

from scripts.dev import _frontend_gate_forms, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_validation_feedback",
    "check_private_profile_is_blocked",
    "check_validator_outage_is_recoverable",
    "check_stale_validator_failure_is_discarded",
    "check_current_validator_failure_replaces_old_verdict",
    "check_true_warning_survives",
    "check_initial_visibility",
)
MOVED = (*CHECKS, "HIDDEN_ON_LOAD", "_collecting_handler", "_year_warning")
REEXPORTED = (*CHECKS, "HIDDEN_ON_LOAD")


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_forms)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_forms, name)


def test_collecting_handler_takes_exactly_one_parameter_and_appends() -> None:
    # Playwright passes (route, request) to a two-parameter handler, which
    # overwrote a defaulted `pending` list with the request object in CI.
    sink: list = []
    handler = _frontend_gate_forms._collecting_handler(sink)
    assert len(inspect.signature(handler).parameters) == 1
    handler("route-1")
    handler("route-2")
    assert sink == ["route-1", "route-2"]


def test_collecting_handlers_do_not_share_a_sink() -> None:
    first, second = [], []
    _frontend_gate_forms._collecting_handler(first)("a")
    _frontend_gate_forms._collecting_handler(second)("b")
    assert (first, second) == (["a"], ["b"])
```

Expected: FAIL, `ModuleNotFoundError`.

- [x] **Step 3: Module header**

```python
"""Form checks: validation feedback, validator failures and races, visibility.

A slice of the frontend gate (F-B21-51). These checks drive the index form
through real clicks and intercepted validator requests, because the failure
they guard against is a stale or lost verdict that only a real request order
can produce.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_shared import _reach_state
```

- [x] **Step 4: Facade import**

```python
from scripts.dev._frontend_gate_forms import (  # noqa: E402, F401
    HIDDEN_ON_LOAD,
    check_current_validator_failure_replaces_old_verdict,
    check_initial_visibility,
    check_private_profile_is_blocked,
    check_stale_validator_failure_is_discarded,
    check_true_warning_survives,
    check_validation_feedback,
    check_validator_outage_is_recoverable,
)
```

- [x] **Step 5: Ruff, tests, name comparison, gate**

No existing unit test covers a forms function, so there are no tests to
move. The patch-target guard confirms that.

- [x] **Step 6: Mutation proof**

Add `"#year"` to the `"/"` tuple in `HIDDEN_ON_LOAD`. The year field is
visible on load, so the gate must print a
`FAIL chromium: initial visibility [desktop]: ...#year...` line. Revert.

- [x] **Step 7: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_forms.py # form validation, validator races, initial visibility`
- Import-graph line:
  `dev/_frontend_gate_forms.py <- dev/_frontend_gate_shared`
- Section 4 entry:
  `### 2026-09-21 - Frontend gate split: forms slice (F-B21-51)`

```bash
git add scripts/dev/_frontend_gate_forms.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_forms.py PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move the form and validator checks into a slice" \
  -m "Seven checks share one subject, the index form and its validator
request order. _collecting_handler gains the regression test its docstring
describes: one parameter, so Playwright cannot overwrite its sink."
```

---

### Task 7: Theme slice

**Files:**
- Create: `scripts/dev/_frontend_gate_theme.py`
- Create: `tests/scripts/dev/test_frontend_gate_theme.py`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate.py` (tests move out)

**Interfaces:**
- Consumes:
  - From `_frontend_gate_colour`: `_divider_contrast_failure`,
    `_is_forbidden_surface`, `_worst_divider_contrast`.
  - From `scrobblescope.repositories`: `create_job`, `delete_job`,
    `set_job_progress`, `set_job_results`.
  - From `_frontend_gate_shared`: `MIGRATED_PAGES`, `TOGGLE_TIMEOUT_MS`.
- Produces, each with the signature `(page, base_url: str) -> list[str]`:
  - `check_divider_contrast`
  - `check_theme_tokens`
  - `check_index_design_tokens`
  - `check_theme_persistence`
  - `check_index_entrance_motion`
  - `check_mark_follows_theme`
  - `check_theme_survives_blocked_storage`
  - `check_heatmap_zero_cells_follow_theme`
  - `check_heatmap_export_header_matches_page`
- Also produces the constants `THEME_EXPRESSION`, `SET_THEME_EXPRESSION`
  and `FORBIDDEN_SURFACES`.

**Definitions to move, in file order:**
- `THEME_EXPRESSION`, `SET_THEME_EXPRESSION` (from the constants block near
  the top)
- `FORBIDDEN_SURFACES`
- `_computed_colour`
- `check_divider_contrast`
- `check_theme_tokens`
- `check_index_design_tokens`
- `check_theme_persistence`
- `check_index_entrance_motion`
- `check_mark_follows_theme`
- `_BLOCK_STORAGE`
- `check_theme_survives_blocked_storage`
- `check_heatmap_zero_cells_follow_theme`
- `check_heatmap_export_header_matches_page`

**Tests to move** from `test_frontend_gate.py`:
- `test_blocked_storage_probe_closes_context_when_page_creation_fails`
- `test_theme_persistence_check_restores_the_saved_preference`. Retarget its
  `patch("scripts.dev.frontend_gate.MIGRATED_PAGES", ("/",))` to
  `patch("scripts.dev._frontend_gate_theme.MIGRATED_PAGES", ("/",))`. This is
  trap 2: the check reads the theme module's binding.

- [x] **Step 1: Record the count and gate line**

- [x] **Step 2: Failing parity test**

`tests/scripts/dev/test_frontend_gate_theme.py` (the moved tests are
appended below this in Step 6):

```python
"""Parity and behaviour tests for the theme slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_theme, frontend_gate
from scripts.dev._frontend_gate_theme import (
    check_theme_persistence,
    check_theme_survives_blocked_storage,
)
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_divider_contrast",
    "check_theme_tokens",
    "check_index_design_tokens",
    "check_theme_persistence",
    "check_index_entrance_motion",
    "check_mark_follows_theme",
    "check_theme_survives_blocked_storage",
    "check_heatmap_zero_cells_follow_theme",
    "check_heatmap_export_header_matches_page",
)
CONSTANTS = ("THEME_EXPRESSION", "SET_THEME_EXPRESSION", "FORBIDDEN_SURFACES")
MOVED = (*CHECKS, *CONSTANTS, "_computed_colour", "_BLOCK_STORAGE")
REEXPORTED = (*CHECKS, *CONSTANTS)


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_theme)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_theme, name)
```

Expected: FAIL, `ModuleNotFoundError`. The two imported checks are what the
moved tests call. If ruff flags `MagicMock` or `patch` as unused before
Step 6, the moved tests will use them.

- [x] **Step 3: Module header**

```python
"""Theme checks: tokens, divider contrast, persistence, motion, and the mark.

A slice of the frontend gate (F-B21-51). Every check here reads computed
values -- a resolved token, a composited contrast ratio, a stored preference
after reload -- because a class name or a declared value passes against a
stylesheet the browser never applied.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_colour import (
    _divider_contrast_failure,
    _is_forbidden_surface,
    _worst_divider_contrast,
)
from scripts.dev._frontend_gate_shared import MIGRATED_PAGES, TOGGLE_TIMEOUT_MS
from scrobblescope.repositories import (
    create_job,
    delete_job,
    set_job_progress,
    set_job_results,
)
```

- [x] **Step 4: Facade import**

```python
from scripts.dev._frontend_gate_theme import (  # noqa: E402, F401
    FORBIDDEN_SURFACES,
    SET_THEME_EXPRESSION,
    THEME_EXPRESSION,
    check_divider_contrast,
    check_heatmap_export_header_matches_page,
    check_heatmap_zero_cells_follow_theme,
    check_index_design_tokens,
    check_index_entrance_motion,
    check_mark_follows_theme,
    check_theme_persistence,
    check_theme_survives_blocked_storage,
    check_theme_tokens,
)
```

The facade's colour import keeps its existing names, and
`test_frontend_gate_colour.py` still pins them, even though no facade
function reads them any more. Keep that block, and make its `noqa` include
`F401`.

- [x] **Step 5: Ruff**

- [x] **Step 6: Move the two tests and retarget the patch**

Remove `check_theme_persistence` and
`check_theme_survives_blocked_storage` from `test_frontend_gate.py`'s
import block.

- [x] **Step 7: Tests, name comparison, gate**

- [x] **Step 8: Mutation proof**

Insert `return ["mutation probe"]` first in `check_mark_follows_theme`. Expected:
`FAIL chromium: mark follows theme [desktop]: mutation probe` and the same
for `firefox`, because that check is in the static-assets canary group.
Revert.

- [x] **Step 9: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_theme.py # theme tokens, contrast, persistence, motion, mark`
- Import-graph line:
  `dev/_frontend_gate_theme.py <- dev/_frontend_gate_colour, dev/_frontend_gate_shared; repositories`
- Section 4 entry:
  `### 2026-09-21 - Frontend gate split: theme slice (F-B21-51)`. Name the
  retargeted `MIGRATED_PAGES` patch as an instance of trap 2.

```bash
git add scripts/dev/_frontend_gate_theme.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_theme.py tests/scripts/dev/test_frontend_gate.py \
  PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move the theme and motion checks into a slice" \
  -m "Nine checks that read computed theme values move with their
expressions. The persistence test's MIGRATED_PAGES patch now targets the
theme module, the namespace the check actually reads; aimed at the facade it
would have run against every page and still passed."
```

---

### Task 8: Layout slice

**Files:**
- Create: `scripts/dev/_frontend_gate_layout.py`
- Create: `tests/scripts/dev/test_frontend_gate_layout.py`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate.py` (tests move out)

**Interfaces:**
- Consumes:
  - `_clamp_px` from `_frontend_gate_colour`.
  - From `_frontend_gate_shared`: `ALL_PAGES`, `MIGRATED_PAGES`,
    `TOGGLE_TIMEOUT_MS`, `_reach_state`.
- Produces, each with the signature `(page, base_url: str) -> list[str]`:
  - `check_touch_targets`
  - `check_fonts`
  - `check_body_font`
  - `check_shell_scales_with_text`
  - `check_large_display_scale_parity`
  - `check_destination_empty_states`
- Also produces the constants `MIN_TOUCH_TARGET_PX`, `INTERACTIVE_SELECTOR`,
  `TOUCH_TARGET_STATES`, `DEFAULT_STATES`, `REQUIRED_FONT_FAMILIES` and
  `FONTS_READY_EXPRESSION`.

**Definitions to move, in file order:**
- Constants: `FONTS_READY_EXPRESSION`, `REQUIRED_FONT_FAMILIES`,
  `MIN_TOUCH_TARGET_PX`, `INTERACTIVE_SELECTOR`, `TOUCH_TARGET_STATES`,
  `DEFAULT_STATES`.
- Checks and helpers:
  - `check_touch_targets`, `_small_targets`
  - `check_fonts`, `check_body_font`, `check_shell_scales_with_text`
  - `_measure_scale_dimensions`, `_measure_wide_layout`,
    `_measure_zoom_and_transform`, `_measure_fixed_state`,
    `_measure_mobile_headers`, `_measure_enlarged_root`
  - `check_large_display_scale_parity`
  - `_composition_bounds_failures`, `_expected_scaled_dimension`,
    `_scale_dimension_failures`, `_wide_layout_failures`,
    `_header_geometry_failures`, `_scale_mechanism_failures`,
    `_touch_minimum_failures`, `_mobile_header_failures`,
    `_state_dimension_failures`, `_headline_wrap_failures`
  - `_check_desktop_scale_bounds`
  - `check_destination_empty_states`

**Tests to move** from `test_frontend_gate.py`, with the helper
`_healthy_mobile_header`:
- `test_text_scaling_check_restores_the_page_root`
- all seven `test_mobile_header_failures_*`
- `test_state_dimension_failures_reports_only_material_fixed_viewport_changes`
- `test_desktop_scale_bounds_reports_wrapped_headlines_and_closes_context`
- `test_scaled_dimensions_preserve_mark_column_ratio_and_fixed_borders`
- `test_wide_layout_reports_gutter_card_and_mark_regressions`
- `test_header_geometry_retains_clamps_gaps_and_wrap_thresholds`
- `test_scale_mechanism_rejects_zoom_and_transform_independently`
- `test_enlarged_root_probe_restores_sizing_when_measurement_raises`
- `test_composition_bounds_detects_mobile_and_cap_drift`

`test_the_touch_profiles_really_carry_a_coarse_pointer` stays: it tests
`VIEWPORTS`, which remains in the facade. Move their imports
(`_check_desktop_scale_bounds`, `_headline_wrap_failures`,
`_state_dimension_failures`, `_touch_minimum_failures`,
`check_shell_scales_with_text`, and any others ruff reports) to import from
`_frontend_gate_layout`.

- [x] **Step 1: Record the count and gate line**

- [x] **Step 2: Failing parity test**

`tests/scripts/dev/test_frontend_gate_layout.py` (moved tests are appended
in Step 6):

```python
"""Parity and behaviour tests for the layout slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_layout, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_touch_targets",
    "check_fonts",
    "check_body_font",
    "check_shell_scales_with_text",
    "check_large_display_scale_parity",
    "check_destination_empty_states",
)
CONSTANTS = (
    "FONTS_READY_EXPRESSION",
    "REQUIRED_FONT_FAMILIES",
    "MIN_TOUCH_TARGET_PX",
    "INTERACTIVE_SELECTOR",
    "TOUCH_TARGET_STATES",
    "DEFAULT_STATES",
)
HELPERS = (
    "_small_targets",
    "_measure_scale_dimensions",
    "_measure_wide_layout",
    "_measure_zoom_and_transform",
    "_measure_fixed_state",
    "_measure_mobile_headers",
    "_measure_enlarged_root",
    "_composition_bounds_failures",
    "_expected_scaled_dimension",
    "_scale_dimension_failures",
    "_wide_layout_failures",
    "_header_geometry_failures",
    "_scale_mechanism_failures",
    "_touch_minimum_failures",
    "_mobile_header_failures",
    "_state_dimension_failures",
    "_headline_wrap_failures",
    "_check_desktop_scale_bounds",
)
REEXPORTED = (*CHECKS, *CONSTANTS)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS, *HELPERS))
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_layout)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_layout, name)
```

Expected: FAIL, `ModuleNotFoundError`.

- [x] **Step 3: Module header**

```python
"""Layout checks: fonts, text scaling, touch targets, and large-display parity.

A slice of the frontend gate (F-B21-51). The scale-parity check measures in
separate helpers and judges in pure `*_failures` functions, so the judgements
can be unit-tested without a browser and the measurements stay thin.
Composition must reach its proportions through layout, never CSS `zoom` or
`transform`, which would satisfy a pixel check while breaking the type scale.
"""

from __future__ import annotations

import sys

from scripts.dev._frontend_gate_colour import _clamp_px
from scripts.dev._frontend_gate_shared import (
    ALL_PAGES,
    MIGRATED_PAGES,
    TOGGLE_TIMEOUT_MS,
    _reach_state,
)
```

- [x] **Step 4: Facade import**

```python
from scripts.dev._frontend_gate_layout import (  # noqa: E402, F401
    DEFAULT_STATES,
    FONTS_READY_EXPRESSION,
    INTERACTIVE_SELECTOR,
    MIN_TOUCH_TARGET_PX,
    REQUIRED_FONT_FAMILIES,
    TOUCH_TARGET_STATES,
    check_body_font,
    check_destination_empty_states,
    check_fonts,
    check_large_display_scale_parity,
    check_shell_scales_with_text,
    check_touch_targets,
)
```

- [x] **Step 5: Ruff**

- [x] **Step 6: Move the tests listed above and retarget their patches**

- [x] **Step 7: Tests, name comparison, gate**

- [x] **Step 8: Mutation proof**

Insert `return ["mutation probe"]` first in `check_touch_targets`. Expected:
`FAIL chromium: touch targets [mobile]: mutation probe` and
`FAIL chromium: touch targets [wide touch]: mutation probe`. Revert.

- [x] **Step 9: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_layout.py # fonts, text scaling, touch targets, scale parity`
- Import-graph line:
  `dev/_frontend_gate_layout.py <- dev/_frontend_gate_colour, dev/_frontend_gate_shared`
- Section 4 entry:
  `### 2026-09-21 - Frontend gate split: layout slice (F-B21-51)`

```bash
git add scripts/dev/_frontend_gate_layout.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_layout.py tests/scripts/dev/test_frontend_gate.py \
  PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move the layout and scale checks into a slice" \
  -m "The scale-parity check and its eighteen measurement and judgement
helpers move with their unit tests. It remains the largest slice; the split
isolates it rather than shrinking it, and check_large_display_scale_parity's
own complexity is a separate question."
```

---

### Task 9: Pipeline slice

**Files:**
- Create: `scripts/dev/_frontend_gate_pipeline.py`
- Create: `tests/scripts/dev/test_frontend_gate_pipeline.py`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate.py` (tests move out)

**Interfaces:**
- Consumes:
  - From `scrobblescope.repositories`: `create_job`, `delete_job`,
    `get_job_context`, `get_job_progress`, `reset_job_state`,
    `set_job_error`, `set_job_progress`, `set_job_results`, `set_job_stat`.
  - From `_frontend_gate_shared`: `GATE_JOB_IDS`, `MIGRATED_PAGES`.
- Produces, each with the signature `(page, base_url: str) -> list[str]`:
  - `check_loading_composition`
  - `check_pipeline_state_machines`
  - `check_artist_spotlight_rotation`
- Also produces the progress constants: `ALBUM_PROGRESS_TRACK`,
  `ALBUM_PROGRESS_BAR`, `ALBUM_PROGRESS_TEXT`, `HEATMAP_PROGRESS_TRACK`,
  `HEATMAP_PROGRESS_BAR`, `HEATMAP_PROGRESS_TEXT`, `FETCHING_SCROBBLES`,
  `COUNTING_SCROBBLES`, `PAGE_23_OF_102`, `PAGE_90_OF_100`.

**Definitions to move, in file order:**
- the ten progress constants
- `check_loading_composition`
- `_parse_matrix_scalex`
- `_assert_loading_progress_state`
- `_exercise_loading_progress_phases`
- `_check_phase_repository_isolation`
- `_exercise_counted_progress`
- `_exercise_album_progress`
- `_exercise_heatmap_progress`
- `_exercise_replaced_job_progress`
- `_exercise_pipeline_state_machines`
- `check_pipeline_state_machines`
- `check_artist_spotlight_rotation`

**Tests to move:**
- `test_pipeline_state_machine_uses_a_disposable_page`. Retarget its
  `reset_job_state`, `set_job_progress` and
  `_exercise_pipeline_state_machines` patches to `_frontend_gate_pipeline`.
- `test_parse_matrix_scalex_recovers_scale_and_handles_boundaries`
- `test_assert_loading_progress_state_reports_mismatches`
- `test_phase_repository_probe_checks_real_isolation_and_invalid_views`.
  Retarget its `get_job_progress` and `get_job_context` patches.
- `test_replaced_job_probe_reports_stale_delivery_and_cleans_up`. Retarget
  its `create_job`, `set_job_progress` and `delete_job` patches.
- `test_counted_sequence_updates_real_storage_and_detects_stale_text`

- [x] **Step 1: Record the count and gate line**

- [x] **Step 2: Failing parity test**

`tests/scripts/dev/test_frontend_gate_pipeline.py`:

```python
"""Parity and behaviour tests for the pipeline slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.dev import _frontend_gate_pipeline, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_loading_composition",
    "check_pipeline_state_machines",
    "check_artist_spotlight_rotation",
)
CONSTANTS = (
    "ALBUM_PROGRESS_TRACK",
    "ALBUM_PROGRESS_BAR",
    "ALBUM_PROGRESS_TEXT",
    "HEATMAP_PROGRESS_TRACK",
    "HEATMAP_PROGRESS_BAR",
    "HEATMAP_PROGRESS_TEXT",
    "FETCHING_SCROBBLES",
    "COUNTING_SCROBBLES",
    "PAGE_23_OF_102",
    "PAGE_90_OF_100",
)
HELPERS = (
    "_parse_matrix_scalex",
    "_assert_loading_progress_state",
    "_exercise_loading_progress_phases",
    "_check_phase_repository_isolation",
    "_exercise_counted_progress",
    "_exercise_album_progress",
    "_exercise_heatmap_progress",
    "_exercise_replaced_job_progress",
    "_exercise_pipeline_state_machines",
)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS, *HELPERS))
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_pipeline)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS))
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_pipeline, name)
```

Expected: FAIL, `ModuleNotFoundError`.

- [x] **Step 3: Module header**

```python
"""Pipeline checks: loading composition, progress state machines, spotlight.

A slice of the frontend gate (F-B21-51). The state-machine checks write real
job state through `scrobblescope.repositories` and watch the page follow it,
because the defects they guard -- a stale message outliving its phase, a
replaced job still delivering progress -- exist only in that interaction.
"""

from __future__ import annotations

import re

from scripts.dev._frontend_gate_shared import GATE_JOB_IDS, MIGRATED_PAGES
from scrobblescope.repositories import (
    create_job,
    delete_job,
    get_job_context,
    get_job_progress,
    reset_job_state,
    set_job_error,
    set_job_progress,
    set_job_results,
    set_job_stat,
)
```

- [x] **Step 4: Facade import**

```python
from scripts.dev._frontend_gate_pipeline import (  # noqa: E402, F401
    ALBUM_PROGRESS_BAR,
    ALBUM_PROGRESS_TEXT,
    ALBUM_PROGRESS_TRACK,
    COUNTING_SCROBBLES,
    FETCHING_SCROBBLES,
    HEATMAP_PROGRESS_BAR,
    HEATMAP_PROGRESS_TEXT,
    HEATMAP_PROGRESS_TRACK,
    PAGE_23_OF_102,
    PAGE_90_OF_100,
    check_artist_spotlight_rotation,
    check_loading_composition,
    check_pipeline_state_machines,
)
```

Then delete from the facade whichever `scrobblescope.repositories` imports
ruff now reports unused. The runtime still needs `create_job`,
`delete_job` and `set_job_progress` until Task 10.

- [x] **Step 5: Ruff**

- [x] **Step 6: Move the tests listed above and retarget their patches**

- [x] **Step 7: Tests, name comparison, gate**

- [x] **Step 8: Mutation proof**

Insert `return ["mutation probe"]` first in `check_pipeline_state_machines`.
Expected: `FAIL chromium: pipeline state machines [desktop]: mutation probe`.
Revert.

- [x] **Step 9: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_pipeline.py # loading composition, progress state machines, spotlight`
- Import-graph line:
  `dev/_frontend_gate_pipeline.py <- dev/_frontend_gate_shared; repositories`
- Section 4 entry:
  `### 2026-09-21 - Frontend gate split: pipeline slice (F-B21-51)`

```bash
git add scripts/dev/_frontend_gate_pipeline.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_pipeline.py tests/scripts/dev/test_frontend_gate.py \
  PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move the loading and pipeline checks into a slice" \
  -m "The progress state machines move with the ten constants that name
their phases. Five moved tests patched repository functions through the
facade; they now patch the pipeline module, which is where the calls resolve."
```

---

### Task 10: Runtime slice

**Files:**
- Create: `scripts/dev/_frontend_gate_runtime.py`
- Create: `tests/scripts/dev/test_frontend_gate_runtime.py`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate.py` (tests move out)

**Interfaces:**
- Consumes:
  - `create_app` from `app`.
  - `make_server` from `werkzeug.serving`.
  - From `scrobblescope.repositories`: `create_job`, `delete_job`,
    `set_job_progress`.
  - From `_frontend_gate_shared`: `ALL_PAGES`, `GATE_JOB_IDS`,
    `MIGRATED_PAGES`.
- Produces:
  - `FrontendGateError`
  - `SETUP_COMMAND: str`
  - `_load_playwright()`
  - `_launch_browser(playwright, browser_name: str, *, headless: bool = True)`
  - `serve_app() -> ContextManager[str]`
  - `install_cdn_routes(page, live_fonts: bool = False) -> None`
  - If Task 2 Part B was skipped, also `FIXTURE_DIR` and `_bootstrap_fixture`.

**Definitions to move, in file order:**
- `SETUP_COMMAND`
- `_bootstrap_fixture` and `FIXTURE_DIR` (only if Part B was skipped)
- `install_cdn_routes`
- `_SERVE_APP_LOCK`
- `FrontendGateError`
- `_load_playwright`
- `_launch_browser`
- `serve_app`

**What stays in the facade, and why.** `REPO_ROOT`, the `sys.path` insert,
`GATE_SECRET_KEY` and the environment bootstrap all stay:
- They must run before any sibling is imported (trap 4).
- The facade is the entry point `python scripts/dev/frontend_gate.py` runs.
- `BROWSER_NAMES`, `NAVIGATION_TIMEOUT_MS`, the viewports, the registry and
  the CLI stay too, because `main` and `run_checks` read them.

**Tests to move:**
- `test_a_missing_playwright_package_names_the_setup_command`
- `test_a_missing_browser_binary_names_the_setup_command`
- `test_the_server_shuts_down_when_a_check_raises`
- `test_the_server_reports_the_port_the_os_actually_assigned`
- `test_server_setup_failure_restores_jobs_and_page_inventories`
- `test_install_cdn_routes_aborts_only_the_overlay_origin` (or its Part-B-
  skipped original)
- `test_install_cdn_routes_respects_live_fonts_flag`

Retarget every `make_server`, `create_app`, `create_job`, `set_job_progress`
and `delete_job` patch in them to `_frontend_gate_runtime`. Tests that call
`main(` or `run_checks(` stay in `test_frontend_gate.py`; their
`patch.object(frontend_gate, "_launch_browser" | "_load_playwright" | "serve_app" | "run_checks")`
remain correct, because `main` reads those names through the facade's
globals.

- [x] **Step 1: Record the count and gate line**

- [x] **Step 2: Failing parity test**

`tests/scripts/dev/test_frontend_gate_runtime.py`:

```python
"""Parity and behaviour tests for the runtime slice of the frontend gate."""

from __future__ import annotations

from contextlib import nullcontext
from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.dev import _frontend_gate_runtime, frontend_gate
from scripts.dev._frontend_gate_runtime import (
    SETUP_COMMAND,
    FrontendGateError,
    _launch_browser,
    _load_playwright,
    serve_app,
)
from tests.scripts.dev.gate_parity import defined_names

MOVED = (
    "SETUP_COMMAND",
    "install_cdn_routes",
    "_SERVE_APP_LOCK",
    "FrontendGateError",
    "_load_playwright",
    "_launch_browser",
    "serve_app",
)
REEXPORTED = (
    "SETUP_COMMAND",
    "install_cdn_routes",
    "FrontendGateError",
    "_load_playwright",
    "_launch_browser",
    "serve_app",
)


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_runtime)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_runtime, name)


def test_the_environment_bootstrap_stays_in_the_facade() -> None:
    # Trap 4: the bootstrap must run before any sibling imports scrobblescope.
    assert "GATE_SECRET_KEY" in defined_names(frontend_gate)
    assert "REPO_ROOT" in defined_names(frontend_gate)
```

Expected: FAIL, `ModuleNotFoundError`. The imported names are what the
moved tests call. Keep whichever imports the moved tests use; ruff reports
the rest.

- [x] **Step 3: Module header**

```python
"""Gate runtime: Playwright loading, browser launch, the served app, routes.

A slice of the frontend gate (F-B21-51). `serve_app` binds the real Flask
app to port 0 on loopback and extends the shared page inventories with a
seeded loading page for the length of a run, restoring them in a `finally`.
The environment this relies on (a throwaway SECRET_KEY, placeholder provider
keys) is set by the facade before any sibling is imported, because
`scrobblescope.config` reads those keys once, at first import.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from werkzeug.serving import make_server

from app import create_app
from scripts.dev._frontend_gate_shared import ALL_PAGES, GATE_JOB_IDS, MIGRATED_PAGES
from scrobblescope.repositories import create_job, delete_job, set_job_progress
```

If Part B was skipped, add `from functools import cache` and
`from pathlib import Path`.

- [x] **Step 4: Facade import**

```python
from scripts.dev._frontend_gate_runtime import (  # noqa: E402, F401
    SETUP_COMMAND,
    FrontendGateError,
    _launch_browser,
    _load_playwright,
    install_cdn_routes,
    serve_app,
)
```

Delete the facade's `from app import create_app`,
`from werkzeug.serving import make_server`, the remaining
`scrobblescope.repositories` imports, and `threading`, `contextmanager` and
`Iterator`, whichever ruff reports unused. Keep the comment that explains
why the environment bootstrap precedes the imports, and extend it with one
sentence: `Every sibling is imported below this line for the same reason.`

- [x] **Step 5: Ruff**

- [x] **Step 6: Move the tests listed above and retarget their patches**

- [x] **Step 7: Tests, name comparison, gate**

Also run the gate as CI does, from a clean environment, and confirm it still
boots in production mode with no provider keys set:

```bash
env -u LASTFM_API_KEY -u SPOTIFY_CLIENT_ID -u SPOTIFY_CLIENT_SECRET \
  -u SECRET_KEY -u DEBUG_MODE $PY scripts/dev/frontend_gate.py
```

Expected: the same summary line. The trap-4 subprocess test covers the same
thing in pytest.

- [x] **Step 8: Mutation proof**

In `_launch_browser`, change `headless=headless` to
`headless=headless, nonexistent_option=True`. Expected: the gate prints
`[frontend_gate] FAIL chromium: raised FrontendGateError: chromium is not available to Playwright...`
and the same for `firefox`. Revert.

- [x] **Step 9: Docs and commit**

- SESSION_CONTEXT tree line:
  `_frontend_gate_runtime.py # Playwright loading, browser launch, served app, route policy`
- Import-graph line:
  `dev/_frontend_gate_runtime.py <- dev/_frontend_gate_shared; app.py (create_app); repositories; werkzeug.serving; playwright (imported late)`
- Rewrite the `dev/frontend_gate.py` line to list only the siblings, because
  it no longer imports `app`, `repositories` or `werkzeug` itself.
- Section 4 entry:
  `### 2026-09-21 - Frontend gate split: runtime slice (F-B21-51)`

```bash
git add scripts/dev/_frontend_gate_runtime.py scripts/dev/frontend_gate.py \
  tests/scripts/dev/test_frontend_gate_runtime.py tests/scripts/dev/test_frontend_gate.py \
  PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "refactor(gate): Move the server and browser runtime into a slice" \
  -m "Last because it carried most of the patch targets. serve_app,
browser launch and route policy move; the environment bootstrap stays in the
facade, above every sibling import, because scrobblescope.config reads the
provider keys once at first import and CI boots in production mode."
```

---

### Task 11: Close out F-B21-51 and reconcile the docs

**Files:**
- Modify: `FINDINGS.md`
- Modify: `DEVELOPMENT.md` (the frontend gate paragraph in the extraction
  section)
- Modify: `docs/architecture/documentation-tooling.md` (the gate diagram
  and its paragraph)
- Modify: `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

- [x] **Step 1: Measure the end state**

```bash
wc -l scripts/dev/frontend_gate.py scripts/dev/_frontend_gate_*.py
$PY scripts/dev/frontend_gate.py
```

Record every module's line count and the summary line. The facade should be
roughly 450 lines. If it is above 700, find what was not moved before
closing, and do not close the finding.

- [x] **Step 2: Architecture doc**

In `docs/architecture/documentation-tooling.md`, add one node per new slice
to the gate diagram, each with an edge from `FG`, following the existing
`FG --> FGR[_frontend_gate_results]` style. Add an edge from each slice
that imports `_frontend_gate_shared` to a `FGS[_frontend_gate_shared]`
node. Rewrite the paragraph beginning "`dev/frontend_gate.py` is the browser
gate and a stable facade" so it lists the siblings and says the TOML
registry is deferred.

Validate the Mermaid block by rendering it (the Mermaid validation tool, or
the repository's usual preview). A diagram that fails to parse is a defect.

- [x] **Step 3: DEVELOPMENT.md**

Rewrite the paragraph that begins "**3. The frontend gate
(`scripts/dev/frontend_gate.py`).**" so it no longer says the facade is
"still the bulk of the code" or that the plan is "deliberately parked".
State that the split has landed, with the measured facade size, and that
the checks are grouped by concern in nine siblings.

- [x] **Step 4: Resolve the finding**

In F-B21-51, replace the `Status:` line with the lifecycle record:

```markdown
- [x] **Status:** resolved
**Completed:** <YYYY-MM-DD of this commit>
```

Add one paragraph with the measured end state (Step 1) and the ten slice
commits by short SHA (`git log --oneline --grep "F-B21-51"` plus the
subjects). Then run `$PY scripts/doc_state_sync.py --fix`, which rotates it
to the archive with the `-- RESOLVED` suffix. This is dev tooling that never
deploys, so DOC014's pending-deploy block does not apply. If `--check`
reports otherwise, read the diagnostic before changing anything.

- [x] **Step 5: PLAYBOOK Section 3 and Section 4**

- In Section 3, change the "Side task in progress" bullet to a completed
  one.
- Section 4 entry:
  `### <date> - Frontend gate split complete (F-B21-51)`, with the
  measurements.

- [x] **Step 6: Pre-push self-review (AGENTS.md "Commit Rules")**

- Read every file this plan changed **whole**.
- Grep the branch's cumulative diff for stale claims about the gate's
  structure:

```bash
git diff origin/main...HEAD --stat
grep -rnE "frontend_gate\.py.{0,40}(lines|bulk|parked|nine times|ten times)" \
  --include=*.md . | grep -vE "/(history|superpowers|\.superpowers|logarchive|graphify-out)/"
```

Every live claim must match the measured end state. Section 4 entries are
point-in-time and stay as written.

- [x] **Step 7: Full sequence and commit**

```bash
git add FINDINGS.md docs/history/findings/FINDINGS_ARCHIVE.md DEVELOPMENT.md \
  docs/architecture/documentation-tooling.md PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "docs(gate): Close F-B21-51 now the frontend gate split has landed" \
  -m "The gate is a facade over nine concern-owned siblings. The docs
described the split as parked and the facade as the bulk of the code; both
now state the measured end state. The TOML registry stays a candidate."
```

- [x] **Step 8: Hand over**

Report to the owner:
- the per-module line counts;
- the unchanged gate summary line;
- the collection count, before and after;
- that CI's workflow file was not changed, and why (see "What CI needs").

Pushing and the PR are the owner's call.

## Execution record (2026-09-21)

One commit per task, oldest first:

- Task 1: `a06f6c2` -- test(gate): Pin the invariants the frontend gate
  split must keep.
- Task 2: `30310c2` -- refactor(gate): Delete dead helpers before the
  split moves them.
- Task 3 (shared slice): `04882a2` -- refactor(gate): Move what several
  slices read into a shared module.
- Task 4 (assets slice): `7a7b599` -- refactor(gate): Move stylesheet
  isolation into its own slice.
- Task 5 (unmatched slice): `6f1186f` -- refactor(gate): Move the
  unmatched report check into its own slice.
- Task 6 (forms slice): `06a9ae7` -- refactor(gate): Move the form and
  validator checks into a slice.
- Task 7 (theme slice): `bfc8749` -- refactor(gate): Move the theme and
  motion checks into a slice.
- Task 8 (layout slice): `e172b3e` -- refactor(gate): Move the layout and
  scale checks into a slice.
- Task 9 (pipeline slice): `2887c23` -- refactor(gate): Move the loading
  and pipeline checks into a slice.
- Task 10 (runtime slice): `839fa3e` -- refactor(gate): Move the server
  and browser runtime into a slice.
- Task 11 (this task): docs(gate): Close F-B21-51 now the frontend gate
  split has landed.

**Deviations from the plan text:**

- Task 1: PLAYBOOK Section 3's bullet states PR #238 merged. That is
  fact-checked against the live PR state, not copied from the plan text,
  which predated the merge.
- Task 2: `test_main_preserves_route_policy_through_real_runner`'s call
  count changed from 4 to 2 and gained an explicit `localhost:8400`
  pattern assertion, beyond what the plan's test body specified. A second
  stale `bootstrap_fixture` mention, in the `LEGACY_PAGES` comment, was
  also repointed; the plan named only the first.
- Task 8: two `.docsync.toml` site entries -- the 860px breakpoint's
  `matchMedia` expression and the 44px touch-target constant -- were
  retargeted to `_frontend_gate_layout.py` (DOC009), committed with
  `SKIP=doc-state-sync-check` per the escape hatch, since the control-plane
  preflight refuses a `.docsync.toml` change otherwise.
  `TOGGLE_TIMEOUT_MS` was dropped from the layout module's header import as
  unused, which the plan's header listing did not anticipate.
- Task 10: four `frontend_gate.create_job`/`frontend_gate.delete_job`
  attribute calls in `test_frontend_gate_pipeline.py` (an earlier slice's
  test file) were retargeted to `_frontend_gate_pipeline.create_job`/
  `_frontend_gate_pipeline.delete_job`, discovered only because the
  runtime slice removed the facade's own import of those names.
- The facade ended at 535 lines (Step 1's measurement), above the plan's
  roughly-450 estimate and under its 700-line threshold.
- Every task's `doc_state_sync.py --fix` rotated an older Section 4 entry
  out of `PLAYBOOK.md` into `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`;
  each rotation was staged and committed together with that task's own
  commit, not as a separate change.
- CI's workflow file (`.github/workflows/test.yml`) was not changed across
  any task. It runs `python scripts/dev/frontend_gate.py` once regardless
  of how the checks are split across modules, and the registry-completeness
  test (Task 1) guards against a moved check silently dropping out of
  `CHECKS`.
