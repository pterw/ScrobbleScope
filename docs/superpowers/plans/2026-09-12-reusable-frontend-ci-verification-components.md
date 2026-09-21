# Reusable Frontend CI Verification Components Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Status:** Deferred candidate. Do not execute until the owner has accepted the
final Unmatched presentation and the Batch 21 frontend migration is closed.

**Goal:** Decompose the 4,008-line frontend gate into reusable browser-runner,
probe and reporting components that retain ScrobbleScope's current visual
contracts and produce deterministic CI evidence.

**Architecture:** Preserve `scripts/dev/frontend_gate.py` as the command-line
facade while extracting a small runner core, browser/server adapters,
page-specific probe modules and machine-readable reporting. Reuse begins
inside this repository; publication as an external package requires a later
consumer and is not part of this plan.

**Tech Stack:** Python 3.13, Playwright 1.62.0, Flask/Werkzeug test server,
pytest, GitHub Actions.

## Global Constraints

- Stabilize Unmatched first. Its final accepted checks are input to this plan,
  not a moving target during extraction.
- Add no dependency and do not create a Node project.
- Preserve the existing Chromium full pass, Firefox canary, viewport profiles,
  check names, planned-run count, failure text and process exit codes.
- The first extraction commits change structure only. New reporting behavior
  lands after parity is proven.
- Browser checks assert computed behavior and reachable states, not class names
  or DOM presence alone.
- Keep ScrobbleScope fixtures and selectors outside the reusable runner core.
- A component is reusable only when a unit test can run it with a fake browser
  or reporter without starting the Flask application.

---

## File Structure

- `scripts/dev/frontend_gate.py` -- stable CLI facade and compatibility
  re-exports during migration.
- `scripts/dev/ui_verify/models.py` -- immutable `ViewportSpec`, `CheckSpec`,
  `CheckResult` and `RunSummary` records.
- `scripts/dev/ui_verify/runner.py` -- check scheduling, browser/profile matrix,
  exception isolation and stable result ordering.
- `scripts/dev/ui_verify/browser.py` -- Playwright loading and browser launch.
- `scripts/dev/ui_verify/server.py` -- application fixture lifecycle and CDN
  route interception.
- `scripts/dev/ui_verify/reporters.py` -- console and JSON result rendering.
- `scripts/dev/ui_verify/checks/` -- cohesive check families: shell/theme,
  accessibility, scale/layout, loading/jobs, Results and Unmatched.
- `tests/scripts/dev/ui_verify/` -- component tests mirroring those
  responsibilities.

## Interfaces

```python
from dataclasses import dataclass
from typing import Callable, Mapping


@dataclass(frozen=True)
class ViewportSpec:
    name: str
    width: int
    height: int
    device_scale_factor: float = 1.0
    has_touch: bool = False


@dataclass(frozen=True)
class CheckSpec:
    name: str
    callback: Callable
    profiles: tuple[str, ...]
    group: str


@dataclass(frozen=True)
class CheckResult:
    browser: str
    profile: str
    check: str
    failures: tuple[str, ...]
    duration_ms: int


@dataclass(frozen=True)
class RunSummary:
    results: tuple[CheckResult, ...]
    planned_runs: int

    @property
    def passed(self) -> bool: ...


def run_matrix(
    *,
    playwright,
    base_url: str,
    browsers: tuple[str, ...],
    viewports: Mapping[str, ViewportSpec],
    checks: tuple[CheckSpec, ...],
    browser_groups: Mapping[str, tuple[str, ...]],
    headed: bool,
) -> RunSummary: ...
```

---

### Task 1: Freeze CLI and run-matrix behavior

**Files:**

- Create: `tests/scripts/dev/ui_verify/test_compatibility.py`
- Modify: none
- Test: `tests/scripts/dev/ui_verify/test_compatibility.py`

- [ ] **Step 1: Record the current observable contract**

Test Chromium/Firefox launch order, browser close-on-error, Firefox canary
groups, viewport ordering, one failed check not suppressing later checks,
`PLANNED_RUNS`, success text, failure text and exit codes 0/1/2.

- [ ] **Step 2: Run the compatibility tests**

```bash
pytest tests/scripts/dev/test_frontend_gate.py tests/scripts/dev/ui_verify/test_compatibility.py -q
```

Expected: PASS against the monolithic facade.

- [ ] **Step 3: Commit the compatibility boundary**

```bash
git add tests/scripts/dev/ui_verify/test_compatibility.py
git commit -m "test(frontend): Pin frontend gate CLI behavior"
```

### Task 2: Extract immutable check models and the matrix runner

**Files:**

- Create: `scripts/dev/ui_verify/__init__.py`
- Create: `scripts/dev/ui_verify/models.py`
- Create: `scripts/dev/ui_verify/runner.py`
- Create: `tests/scripts/dev/ui_verify/test_runner.py`
- Modify: `scripts/dev/frontend_gate.py`

- [ ] **Step 1: Write failing runner tests**

Use fake browsers/pages and two checks to prove deterministic matrix order,
group filtering, exception-to-failure conversion, duration capture and planned
run calculation.

- [ ] **Step 2: Implement the interfaces above**

The runner receives every dependency. It must not import Flask, application
routes, ScrobbleScope job state or concrete Playwright browser engines.

- [ ] **Step 3: Adapt the facade without changing output**

Translate the existing `VIEWPORTS`, `CHECKS` and browser-group maps into typed
records. Keep compatibility names re-exported from `frontend_gate.py`.

- [ ] **Step 4: Run runner and facade tests**

```bash
pytest tests/scripts/dev/ui_verify/test_runner.py tests/scripts/dev/test_frontend_gate.py -q
```

- [ ] **Step 5: Commit the runner extraction**

```bash
git add scripts/dev/ui_verify/__init__.py scripts/dev/ui_verify/models.py scripts/dev/ui_verify/runner.py scripts/dev/frontend_gate.py tests/scripts/dev/ui_verify/test_runner.py
git commit -m "refactor(frontend): Extract the verification runner"
```

### Task 3: Extract browser and server adapters

**Files:**

- Create: `scripts/dev/ui_verify/browser.py`
- Create: `scripts/dev/ui_verify/server.py`
- Create: `tests/scripts/dev/ui_verify/test_browser.py`
- Create: `tests/scripts/dev/ui_verify/test_server.py`
- Modify: `scripts/dev/frontend_gate.py`

- [ ] **Step 1: Move existing failure-path tests before implementation**

Cover missing Playwright, missing browser binaries, headed propagation,
server-start failure, guaranteed shutdown, job cleanup and immutable global
fixture collections.

- [ ] **Step 2: Extract adapters**

Move `_load_playwright()` and `_launch_browser()` into `browser.py`. Move
`serve_app()`, CDN routing and fixture lifecycle into `server.py`. Inject the
application factory and job cleanup callbacks so the adapter core does not
import ScrobbleScope.

- [ ] **Step 3: Keep facade aliases and rerun tests**

```bash
pytest tests/scripts/dev/ui_verify/test_browser.py tests/scripts/dev/ui_verify/test_server.py tests/scripts/dev/test_frontend_gate.py -q
```

- [ ] **Step 4: Commit the adapters**

```bash
git add scripts/dev/ui_verify/browser.py scripts/dev/ui_verify/server.py scripts/dev/frontend_gate.py tests/scripts/dev/ui_verify/test_browser.py tests/scripts/dev/ui_verify/test_server.py
git commit -m "refactor(frontend): Extract browser and server adapters"
```

### Task 4: Extract cohesive check families

**Files:**

- Create: `scripts/dev/ui_verify/checks/__init__.py`
- Create: `scripts/dev/ui_verify/checks/shell_theme.py`
- Create: `scripts/dev/ui_verify/checks/accessibility.py`
- Create: `scripts/dev/ui_verify/checks/scale_layout.py`
- Create: `scripts/dev/ui_verify/checks/loading_jobs.py`
- Create: `scripts/dev/ui_verify/checks/results.py`
- Create: `scripts/dev/ui_verify/checks/unmatched.py`
- Create: matching tests under `tests/scripts/dev/ui_verify/checks/`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `scripts/dev/_frontend_gate_colour.py`
- Modify: `scripts/dev/_frontend_gate_results.py`

- [ ] **Step 1: Move one check family at a time**

For each family, first move its existing unit tests to the matching test
module, then move the complete helper/check responsibility. Do not split a
probe's measurement from its failure evaluator merely to reduce file length.

- [ ] **Step 2: Preserve selector and state ownership**

Page-specific selectors, mocked routes and job fixtures stay in the Results,
Unmatched or loading/jobs modules. Colour arithmetic remains one shared helper
module. Generic runner modules must contain no page route or selector literal.

- [ ] **Step 3: Run focused tests after every family move**

```bash
pytest tests/scripts/dev/test_frontend_gate.py tests/scripts/dev/test_frontend_gate_colour.py tests/scripts/dev/ui_verify -q
```

- [ ] **Step 4: Run the live two-engine gate after every page-family move**

```bash
python scripts/dev/frontend_gate.py
```

Expected: the same check count, run count, browser coverage and failures as the
pre-move facade.

- [ ] **Step 5: Commit each independently reviewable family**

Use one commit per cohesive family, for example:

```bash
git commit -m "refactor(frontend): Extract Unmatched verification checks"
```

### Task 5: Add deterministic CI reports

**Files:**

- Create: `scripts/dev/ui_verify/reporters.py`
- Create: `tests/scripts/dev/ui_verify/test_reporters.py`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `.github/workflows/test.yml`

- [ ] **Step 1: Write reporter tests**

Prove console output remains byte-for-byte compatible. Prove JSON output uses
stable ordering and contains schema version, browser, profile, check, duration,
failures, planned runs and overall pass state.

- [ ] **Step 2: Add an optional report argument**

Expose:

```bash
python scripts/dev/frontend_gate.py --report-json artifacts/frontend-gate.json
```

The file is written on pass, check failure and infrastructure failure. A report
write error is an infrastructure failure and returns exit code 2.

- [ ] **Step 3: Upload the report in CI**

Keep the existing blocking command. Add artifact upload with
`if: always()` so failed browser runs retain evidence. Do not weaken branch
protection or convert the frontend gate to advisory.

- [ ] **Step 4: Run reporter, CLI and workflow tests**

```bash
pytest tests/scripts/dev/ui_verify/test_reporters.py tests/scripts/dev/test_frontend_gate.py -q
python scripts/dev/frontend_gate.py --report-json artifacts/frontend-gate.json
```

- [ ] **Step 5: Commit CI reporting**

Stage `.github/workflows/test.yml` along with the reporter, facade and tests,
then commit:

```bash
git commit -m "feat(ci): Publish frontend verification evidence"
```

### Task 6: Remove compatibility aliases and verify the complete gate

**Files:**

- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate.py`
- Modify: `PLAYBOOK.md`
- Modify: `.claude/SESSION_CONTEXT.md` through docsync if the test count changes

- [ ] **Step 1: Find remaining private facade consumers**

```bash
rg -n "frontend_gate\.(_|check_)|from scripts\.dev\.frontend_gate import" scripts tests
```

Move imports to their owning component. Retain only public CLI-facing names
needed by repository callers.

- [ ] **Step 2: Run the complete ordered validation**

```bash
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/dev/tailwind_build.py --check
python scripts/dev/frontend_gate.py --report-json artifacts/frontend-gate.json
python scripts/doc_state_sync.py --check
git diff --check
```

- [ ] **Step 3: Compare current evidence with the baseline**

Confirm the browser/profile matrix, check names, planned runs, console result
and exit status match the Task 1 characterization. Read every cumulative
changed file whole before publication.

- [ ] **Step 4: Record and commit completion**

Update PLAYBOOK Sections 3-4, sync, stage named paths and commit:

```bash
git commit -m "refactor(frontend): Complete verification component split"
```

## Plan Self-Review

- The plan begins only after the UI being measured is stable.
- The reusable runner contains no ScrobbleScope routes, selectors or job state.
- Page checks remain product-specific and retain computed-style and reachable-
  state coverage.
- The CLI stays compatible throughout extraction.
- CI gains durable evidence without weakening the blocking gate.
- External package publication is excluded until a second consumer proves the
  abstraction.

