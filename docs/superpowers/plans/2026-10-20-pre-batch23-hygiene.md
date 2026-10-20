# Pre-Batch-23 hygiene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear four small backend and tooling items before the seam PRs start: a test that every static file a page loads exists, `page_motion.js` named with hyphens, ruff targeting Python 3.13, and `requests` out of the production requirements.

**Architecture:** Four independent tasks on `chore/pre-batch23-hygiene`, each its own atomic commit (Task 3 is two). No runtime behaviour changes. The design is `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` (PR #2 in its table); the tranche order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.

**Tech Stack:** Python 3.13, Flask/Jinja2 templates, pytest, ruff 0.16.6, pre-commit, docsync (`scripts/doc_state_sync.py`).

## Global Constraints

- Every commit is atomic and carries its own untagged PLAYBOOK Section 4 entry, placed directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` line (AGENTS.md "Side-Task Handling").
- Commit procedure, every commit, in this order (AGENTS.md "Commit Rules"): write the Section 4 entry; `pytest -q` and measure N; `doc_state_sync.py --fix --test-count N` (bare `--fix` when N is unchanged); stage by name, never `git add -A` or `git add .`; `pre-commit run --all-files` and re-stage anything a hook rewrote; `doc_state_sync.py --check` exits 0; commit.
- Commit subject `<type>(<scope>): <Capitalised imperative>`, at most 72 characters; body explains why. No `Co-authored-by` trailer.
- From the linked worktree `C:/ssw/hyg`, every Python command uses the primary checkout's interpreter: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"` (and `pre-commit.exe`, `ruff.exe` beside it).
- Markdown is ASCII only (`--`, never an em dash). Cite code by name, not line number.
- New tests assert intended behaviour, not the code as written, and each comes with mutation evidence: the planted defect named and the test shown failing.
- `WT003 chore/pre-batch23-hygiene` and `WT010` are expected advisories from the `worktree-alignment` hook; the hook still passes.
- Do not push. The controller pushes and opens the PR (Task 5).

---

### Task 1: Every local script and stylesheet a page loads exists

**Files:**
- Modify: `tests/test_template_shell.py` (new test after `test_a_migrated_page_loads_no_bootstrap_javascript`)
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)

**Interfaces:**
- Consumes: the module's existing `app` fixture, `TEMPLATE_CONTEXT`, `render_template`, `re`, `Path`.
- Produces: `test_every_local_script_and_stylesheet_a_page_loads_exists` -- Task 2 relies on it to prove the rename.

Why: nothing fails today if a template names a static file that does not exist. A browser shows a silent 404 and the frontend gate prints it only as an advisory beside a FAIL. Task 2 renames a script, so this guard comes first.

- [ ] **Step 1: Write the test**

Add below `test_a_migrated_page_loads_no_bootstrap_javascript`:

```python
STATIC_ROOT = Path(__file__).resolve().parents[1] / "static"


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_local_script_and_stylesheet_a_page_loads_exists(app, template):
    """A page must never ask for a static file the repository does not ship.

    A missing script or stylesheet fails silently in the browser: the page
    renders, the request 404s, and the behaviour or styling it carried is
    simply absent. Renaming a file without updating every template that loads
    it is the usual way this happens.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    references = re.findall(r'<script[^>]+src="([^"]+)"', html) + re.findall(
        r'<link[^>]+href="([^"]+)"', html
    )
    local = [ref.split("?", 1)[0] for ref in references if ref.startswith("/static/")]
    missing = [ref for ref in local if not (STATIC_ROOT / ref[len("/static/") :]).is_file()]

    assert local, f"{template} loads no local static file; the pattern is wrong"
    assert not missing, f"{template} loads files the repository lacks: {missing}"
```

If `STATIC_ROOT` would duplicate an existing module constant, reuse that constant instead.

- [ ] **Step 2: Run it; it passes on the current tree**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest tests/test_template_shell.py -k every_local_script -q -p no:cacheprovider`
Expected: PASS for every template.

- [ ] **Step 3: Mutation evidence**

Temporarily change `templates/base.html`'s `filename='js/page_motion.js'` to `filename='js/page_motionX.js'`, re-run Step 2's command, and record that every template FAILS with `page_motionX.js` in the message. Restore the file (`git checkout -- templates/base.html`) and confirm Step 2 passes again.

- [ ] **Step 4: Section 4 entry, gates, commit**

Entry heading: `### 2026-10-20 - A page never loads a static file the repository lacks`. Body: scope, why (silent 404s; the rename in the next commit), the mutation evidence, Validation `pytest -q` N.
Commit: `test(templates): Check every static file a page loads exists`.

---

### Task 2: Name `page_motion.js` with hyphens

**Files:**
- Rename: `static/js/page_motion.js` -> `static/js/page-motion.js` (`git mv`)
- Modify: `templates/base.html` (its one `url_for` reference)
- Modify: `.claude/SESSION_CONTEXT.md` Section 3 (the `js/` tree line names `page_motion`)
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)

**Interfaces:**
- Consumes: Task 1's test.
- Produces: nothing new.

Why: files served as URLs conventionally use hyphens, and `page_motion.js` was the only script name in `static/js/` with an underscore (owner ruling 2026-10-20: "What is best practice here?" -> hyphens). `docs/design/designsystemaudit.md` and dated plans and logs keep the old name: they are point-in-time records.

- [ ] **Step 1: Rename without updating the template; the guard fails**

Run: `git mv static/js/page_motion.js static/js/page-motion.js`, then Task 1's test command.
Expected: FAIL for every template, naming `/static/js/page_motion.js`.

- [ ] **Step 2: Update the reference**

In `templates/base.html` change `filename='js/page_motion.js'` to `filename='js/page-motion.js'`. In `.claude/SESSION_CONTEXT.md` Section 3, change `page_motion` to `page-motion` in the `js/` line.

- [ ] **Step 3: Run the guard and the sweep**

Run Task 1's test command. Expected: PASS.
Run: `git grep -n "page_motion" -- ':!docs/history' ':!docs/logarchive' ':!docs/superpowers' ':!docs/design/designsystemaudit.md'`
Expected: no output.

- [ ] **Step 4: Frontend gate**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/frontend_gate.py`
Expected: last line `[frontend_gate] N checks passed ...`, and no load-fault line naming `page-motion.js`.

- [ ] **Step 5: Section 4 entry, gates, commit**

Entry heading: `### 2026-10-20 - page-motion.js is named like the other scripts`. Commit: `refactor(static): Name page-motion.js with hyphens`.

---

### Task 3: Ruff targets Python 3.13 (two commits)

**Files (commit 3a):**
- Modify: `scrobblescope/heatmap.py`, `scrobblescope/lastfm.py`, `scrobblescope/orchestrator/__init__.py`, `scrobblescope/routes/__init__.py`, `scrobblescope/spotify.py`, `scripts/dev/graphify_refresh.py`, `tests/services/test_lastfm_logic.py`, `tests/test_heatmap.py` (whatever `ruff --fix` touches for UP017 and UP041; the list measured on 2026-10-20 at a7bf909)

**Files (commit 3b):**
- Modify: `pyproject.toml` (`[tool.ruff]`)
- Modify: `scripts/dev/docsync_preflight.py`, `scripts/dev/frontend_gate.py`, `scripts/docsync/cli.py`, `scripts/docsync/declarations.py` (import order only; plus one `noqa` in `docsync_preflight.py`)

**Interfaces:** none.

Why: `pyproject.toml` sets no `target-version`, so ruff's modernising rules (UP) and its import sorter judge the code against an older Python than the 3.13 the Dockerfile and CI run. Measured at a7bf909 with `--target-version py313`: 21 UP017 (`timezone.utc` -> `datetime.UTC`), 1 UP041 (`asyncio.TimeoutError` -> `TimeoutError`, the same class since 3.11), 4 I001 (`tomllib` becomes standard library, so it moves into the stdlib import group), 1 UP036 (an outdated version block). No behaviour changes; the existing suite covers every touched path.

- [ ] **Step 1 (3a): Apply the alias fixes**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/ruff.exe" check --target-version py313 --select UP017,UP041 --fix .`
Then `git diff --stat` and confirm only the files listed under 3a changed. These edits are valid under the current configuration too, so the ordinary hooks run.

- [ ] **Step 2 (3a): Suite, entry, gates, commit**

Run the suite; it must pass with the same N. Entry heading: `### 2026-10-20 - Python 3.13 spellings for UTC and timeouts`. Commit: `refactor(py313): Use datetime.UTC and the builtin TimeoutError`.

- [ ] **Step 3 (3b): Set the target**

In `pyproject.toml` under `[tool.ruff]`, after `line-length = 88`, add:

```toml
# The Dockerfile and CI run Python 3.13. Without a target, ruff judges the
# code against an older default, so its modernising rules (UP) miss 3.13
# idioms and its import sorter files tomllib as third-party.
target-version = "py313"
```

- [ ] **Step 4 (3b): Import order, and keep the version guard**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/ruff.exe" check --select I001 --fix scripts/dev/docsync_preflight.py scripts/dev/frontend_gate.py scripts/docsync/cli.py scripts/docsync/declarations.py`

In `scripts/dev/docsync_preflight.py`, the `if sys.version_info < (3, 12):` block is a deliberate refusal (its comment explains it, and the control plane is being shaped to run in other repositories). Keep it and append to that line: `  # noqa: UP036 -- a refusal for an extracted copy run on older Python, not dead code`. If the line exceeds 88 characters, put the reason in the comment above and keep the trailing marker as `# noqa: UP036`.

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/ruff.exe" check .` -- expected: `All checks passed!`. Run `ruff format --check .` -- expected: no file would be reformatted.

- [ ] **Step 5 (3b): Entry, gates, commit through the named escape**

This commit stages `scripts/docsync/` and `scripts/dev/docsync_preflight.py`, which the docsync preflight refuses (exit 3) by design. The documented escape skips that one hook (docs/architecture/documentation-tooling.md "The commit preflight and the opt-in hook installer"):
1. Section 4 entry, heading `### 2026-10-20 - Ruff judges the code as Python 3.13`; say the change is lint-only, name the four control-plane files and why the escape was used.
2. Suite, `--fix`, stage by name, `pre-commit run --all-files` (the docsync hook will report the refusal; every other hook must pass).
3. `SKIP=doc-state-sync-check git commit` with subject `chore(lint): Target Python 3.13 in ruff`.
4. Immediately run `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check`; expected exit 0. Quote it in the report. Never `--no-verify`.

---

### Task 4: Runtime code imports only what the production image installs

**Files:**
- Create: `tests/test_requirements_split.py`
- Modify: `requirements.txt` (remove `requests`, `urllib3`, `charset-normalizer`, `certifi`)
- Modify: `requirements-dev.txt` (add those four, same pins, alphabetical within its list)
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)

**Interfaces:** none.

Why: the Dockerfile installs `requirements.txt` only. `requests` is imported only by `scripts/testing/` (measured: `_http_client.py`, `concurrent_users_test.py`, `smoke_cache_check.py`), and among production packages `urllib3`, `charset-normalizer` and `certifi` are required by `requests` alone (`importlib.metadata.requires`). `idna` stays: `yarl`, which `aiohttp` needs, requires it. Owner, 2026-10-20: "Sure, if it's cheap and you think it would be wise." The image gets smaller and the guard below keeps it honest.

- [ ] **Step 1: Write the test**

```python
"""The production image installs requirements.txt and nothing else.

The Dockerfile runs ``pip install -r requirements.txt``. Any third-party
module the running app imports must therefore come from a distribution that
file pins; a module only requirements-dev.txt provides would import fine in
development and CI, then fail on Fly.io at startup.
"""

from __future__ import annotations

import ast
import re
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: What runs in the production image: the package plus the three entry
#: points the Dockerfile and fly.toml invoke.
RUNTIME_FILES = [
    ROOT / "app.py",
    ROOT / "run.py",
    ROOT / "init_db.py",
    *sorted((ROOT / "scrobblescope").rglob("*.py")),
]

FIRST_PARTY = {"scrobblescope", "app", "run", "init_db"}


def _pinned(requirements: Path) -> set[str]:
    """Return the normalised distribution names a requirements file pins."""
    names = set()
    for raw in requirements.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[=<>!~\[; ]", line, maxsplit=1)[0]
        names.add(name.lower().replace("_", "-"))
    return names


def _third_party_imports(path: Path) -> set[str]:
    """Return the top-level third-party module names a file imports."""
    modules = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])
    return {
        m for m in modules if m not in sys.stdlib_module_names and m not in FIRST_PARTY
    }


def test_runtime_code_imports_only_what_requirements_txt_installs():
    """Every third-party import in runtime code resolves to a production pin."""
    production = _pinned(ROOT / "requirements.txt")
    distributions = packages_distributions()
    unpinned = []
    for path in RUNTIME_FILES:
        for module in sorted(_third_party_imports(path)):
            owners = {
                d.lower().replace("_", "-") for d in distributions.get(module, [])
            }
            if not owners & production:
                unpinned.append(f"{path.relative_to(ROOT)} imports {module}")

    assert not unpinned, (
        "runtime code imports modules requirements.txt does not install: "
        f"{unpinned}"
    )
```

- [ ] **Step 2: Run it on the unchanged requirements; it passes**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest tests/test_requirements_split.py -q -p no:cacheprovider`
Expected: PASS. If it FAILS before any change, stop and report the listed imports: that is a real defect to raise, not to silence.

- [ ] **Step 3: Mutation evidence**

In a scratch copy only (never the worktree a gate may be using): add `import requests` to `scrobblescope/config.py`, move the four pins, and run the test -- expected FAIL naming `scrobblescope/config.py imports requests`. Record the output. Discard the scratch copy.

- [ ] **Step 4: Move the pins**

Remove `certifi==2024.12.14`, `charset-normalizer==3.4.0`, `requests==2.33.0` and `urllib3==2.7.0` from `requirements.txt`; add the same four lines to `requirements-dev.txt` after its `-r requirements.txt` line, keeping that file's existing order convention. Keep `idna==3.15` in `requirements.txt`.

- [ ] **Step 5: Run the test and the suite**

Expected: the new test PASSES; the suite passes (N rises by 1).

- [ ] **Step 6: Section 4 entry, gates, commit**

Entry heading: `### 2026-10-20 - The production image no longer installs requests`. Body: why, the measured users, why `idna` stays, the mutation evidence, and that CI's pip-audit still reads both files. Commit: `chore(deps): Move requests and its own dependencies to dev`.

---

### Task 5: Point Section 3 at the tranche, push, PR (controller)

Runs after the include-unmatched PR merges (it adds the Section 3 bullet this task extends).

- [ ] **Step 1:** `git fetch origin` and `git merge --no-ff origin/main` into `chore/pre-batch23-hygiene`; resolve bookkeeping conflicts by keeping every dated entry from both sides, then `--fix --test-count N`.
- [ ] **Step 2:** In PLAYBOOK Section 3's "Before WP-1" bullet, add one sentence naming the spec and this plan set by path: `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`. In `.claude/SESSION_CONTEXT.md` Section 1's Batch 23 row, add one sentence: the side-task tranche before WP-1 and the spec's path. One Section 4 entry. Commit: `docs(playbook): Point Section 3 at the pre-Batch-23 tranche plan`.
- [ ] **Step 3:** Gate-runner on the final head (all gates), grep every log, then push, open the PR against `main`, and dispatch the CI watcher.

---

## Measured facts this plan rests on (2026-10-20, a7bf909)

- `pytest -q` collects 2534 tests; 59 carry the `browser` marker; CI's coverage step runs the other 2475 and its frontend-gate step runs the 59. The pinned count (`config/docsync.toml` `[test_count]`) therefore includes the browser-marked tests. The documentation PR states this where tests are explained; this plan records it only.
- Pre-commit takes about 9 seconds on this tree; the frontend gate about 2.5 minutes.
