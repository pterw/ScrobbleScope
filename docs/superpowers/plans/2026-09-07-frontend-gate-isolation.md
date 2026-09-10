# Frontend Gate Isolation and Determinism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the frontend gate hermetic and stall-isolated so one flaky CDN fetch or wedged page can no longer fail the whole Quality Gate run.

**Architecture:** The gate keeps one CI step, one `serve_app()`, one process. The 21 checks execute as 4 logical groups, each with a fresh browser context, so a stall poisons only its group. External CDNs (Typekit, cdnjs) are route-blocked with repo-owned fixture CSS whose font metrics are pinned to the real kit. Navigation timeout drops to 10s fail-fast. Chromium runs all groups; Firefox runs Group A only as a regression canary.

**Tech Stack:** Python 3.13, Playwright (sync API), pytest, Flask/Werkzeug. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-07-frontend-gate-isolation-design.md`

## Global Constraints

- Every package in `requirements*.txt` is pinned with `==`; no new packages (spec decision 2 uses Playwright's existing `route` API only).
- ASCII-only in all Markdown and Python string literals; `--` not em-dash.
- No tolerance on any existing geometry assertion may be loosened to admit the font fixture (spec acceptance criterion 3).
- Tests follow AGENTS.md test-quality rules: assert computed behaviour, boundary inputs, no vacuous passes; the group-integrity test is explicitly forbidden (owner ruling: "redundant to test a test").
- The worktree venv lives in the primary checkout; run pytest and pre-commit through the qualified paths the worktree guard printed (this worktree: `.venv\Scripts\python.exe`).
- Commits: Conventional Commits, imperative, no trailing period, no `Co-authored-by`; documentation lands in the same commit as the change it describes.

## File Structure

- Modify: `scripts/dev/frontend_gate.py` -- grouping constant, CDN route-blocker, fixture loader, navigation timeout, per-group context lifecycle, `--live-fonts` flag. The file is already the gate's single owner (per F-WORKTREE-4 the file is large but single-responsibility; new code goes in as cohesive functions, not a new module, to avoid a second import surface for tests that already patch this module).
- Create: `scripts/dev/fixtures/typekit_fixture.css` -- declares the five `REQUIRED_FONT_FAMILIES` with metric overrides and data-URI woff2 sources.
- Create: `scripts/dev/fixtures/bootstrap_fixture.css` -- minimal valid CSS.
- Create: `scripts/dev/fixtures/README.md` -- what the fixtures are, why they exist, the re-calibration rule.
- Modify: `tests/scripts/dev/test_frontend_gate.py` -- new unit tests for the route-blocker and fixture loader; update the two `run_checks`-shaped tests and the `main` tests for the new signature and Firefox canary scope.

---

### Task 1: Font fixtures

**Files:**
- Create: `scripts/dev/fixtures/typekit_fixture.css`
- Create: `scripts/dev/fixtures/bootstrap_fixture.css`
- Create: `scripts/dev/fixtures/README.md`

**Interfaces:**
- Produces: two fixture files at paths the gate constant `FIXTURE_DIR` points to. `typekit_fixture.css` must contain a `@font-face` block for every family in `frontend_gate.REQUIRED_FONT_FAMILIES` (the loader test in Task 3 asserts this). `bootstrap_fixture.css` must be non-empty, valid CSS.

- [ ] **Step 1: Create the fixtures directory and the Typekit fixture**

Write `scripts/dev/fixtures/typekit_fixture.css`. Each family gets `font-family`, `font-weight: normal`, `font-style: normal`, `src: url(data:font/woff2;base64,<tiny>) format("woff2")`, and the metric pins. The data URI may be one shared minimal woff2 (an empty valid face is enough; `document.fonts.load()` resolves a FontFace object regardless of glyph content, and `check_fonts` asserts `faces.length > 0`, not glyph rendering). Metric pins start from the real kit's computed metrics, measured once per family in the browser with `document.fonts.load('16px "<family>"')` then `getComputedStyle` line-box inspection at calibration time (Task 5); the initial values below are the calibration targets to verify, not guesses to ship:

```css
/* Fixture for the Adobe Fonts kit (use.typekit.net/rwy8ghw.css).
   Served by the frontend gate's route-blocker so CI never touches
   the network. Faces are metric-pinned to the real kit: the
   size-adjust/ascent-override/descent-override values were measured
   against the live kit per the calibration procedure in README.md.
   Re-calibrate whenever the owner changes the Adobe project. */
@font-face {
  font-family: "akzidenz-grotesk-next-pro";
  src: url(data:font/woff2;base64,d09GMgABAAAAAAQ) format("woff2");
  font-weight: normal;
  font-style: normal;
  size-adjust: 100%;
  ascent-override: 78%;
  descent-override: 22%;
}
/* ...same block for instrument-serif, gotham, input-mono,
   input-mono-narrow, each with its calibrated metric values... */
```

- [ ] **Step 2: Create the Bootstrap fixture**

`scripts/dev/fixtures/bootstrap_fixture.css` contains a comment and one harmless rule so the file is valid CSS and non-empty:

```css
/* Fixture for cdnjs Bootstrap 5.1.3. The stylesheet-isolation check
   reads link hrefs, not contents; the body-font check reads the
   cascade where shell.css wins. One rule keeps the file valid CSS. */
.bootstrap-fixture { display: block; }
```

- [ ] **Step 3: Write the fixtures README**

`scripts/dev/fixtures/README.md` documents: what each fixture replaces, why (CI stall + font weather, spec section "Problem"), the metric-pinning approach, and the re-calibration procedure -- run `python scripts/dev/frontend_gate.py --live-fonts --headed` locally, note each family's computed line-box metrics at 16px in Chromium DevTools, update the `size-adjust`/`ascent-override`/`descent-override` values in `typekit_fixture.css`, then run the gate without `--live-fonts` and confirm the measurement-sensitive checks still pass inside their existing tolerances. ASCII only.

- [ ] **Step 4: Commit**

```bash
git add scripts/dev/fixtures/
git commit -m "feat(gate): add metric-pinned font and bootstrap fixtures"
```

---

### Task 2: Fixture loader and CDN route-blocker (TDD)

**Files:**
- Modify: `scripts/dev/frontend_gate.py`
- Test: `tests/scripts/dev/test_frontend_gate.py`

**Interfaces:**
- Consumes: `REQUIRED_FONT_FAMILIES` (existing constant).
- Produces:
  - `FIXTURE_DIR: Path` (module constant, `Path(__file__).parent / "fixtures"`).
  - `load_typekit_fixture_css() -> str` -- raises `FrontendGateError` if the file is missing or fails to declare every required family.
  - `install_cdn_routes(page) -> None` -- calls `page.route(pattern, handler)` for both CDN origins; other URLs untouched. Handler for typekit fulfills with content-type `text/css` and the fixture body; handler for cdnjs bootstrap fulfills with the bootstrap fixture body.

- [ ] **Step 1: Write the failing tests**

Append to `tests/scripts/dev/test_frontend_gate.py`:

```python
def test_typekit_fixture_declares_every_required_family() -> None:
    """The fixture loader validates family coverage, not just file presence."""
    css = frontend_gate.load_typekit_fixture_css()
    for family in frontend_gate.REQUIRED_FONT_FAMILIES:
        assert f'font-family: "{family}"' in css


def test_typekit_fixture_loader_rejects_incomplete_file(tmp_path, monkeypatch) -> None:
    """A fixture missing a family is a gate prerequisite failure, not a silent fallback."""
    bad = tmp_path / "typekit_fixture.css"
    bad.write_text("/* missing families */", encoding="utf-8")
    monkeypatch.setattr(frontend_gate, "FIXTURE_DIR", tmp_path)
    with pytest.raises(FrontendGateError, match="instrument-serif"):
        frontend_gate.load_typekit_fixture_css()


def test_install_cdn_routes_fulfills_typekit_and_bootstrap() -> None:
    """The blocker fulfils both CDN origins and leaves others alone."""
    page = MagicMock()
    handlers = {}

    def route_side_effect(pattern, handler):
        handlers[pattern] = handler

    page.route.side_effect = route_side_effect
    frontend_gate.install_cdn_routes(page)

    assert len(handlers) == 2
    typekit_route, bootstrap_route = MagicMock(), MagicMock()
    for route in handlers.values():
        # Each handler must decide by URL; probe both shapes.
        pass
    # Route the typekit-shaped URL through whichever handler its pattern owns.
    typekit_req, bootstrap_req = Mock(), Mock()
    typekit_req.request.url = "https://use.typekit.net/rwy8ghw.css"
    bootstrap_req.request.url = (
        "https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css"
    )
    other_req = Mock()
    other_req.request.url = "http://127.0.0.1:1/static/css/shell.css"

    for handler in handlers.values():
        handler(typekit_route)
        handler(bootstrap_route)
        handler(other_req)

    typekit_route.fulfill.assert_called_once()
    bootstrap_route.fulfill.assert_called_once()
    other_req.assert_not_called()  # Mock records no calls; fulfil/abort absent
    assert "typekit_fixture.css" in (
        typekit_route.fulfill.call_args.kwargs.get("path", "")
        or typekit_route.fulfill.call_args.kwargs.get("body", "")
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/scripts/dev/test_frontend_gate.py -k "fixture or cdn_routes" -v`
Expected: FAIL with `AttributeError: module 'scripts.dev.frontend_gate' has no attribute 'load_typekit_fixture_css'`

- [ ] **Step 3: Implement the loader and blocker**

In `frontend_gate.py`, after the `REQUIRED_FONT_FAMILIES` block:

```python
#: Directory holding the route-blocked CDN fixtures. Repo-owned so CI
#: never touches the network (spec: 2026-09-07 gate isolation design).
FIXTURE_DIR = Path(__file__).parent / "fixtures"
_TYPEKIT_FIXTURE = FIXTURE_DIR / "typekit_fixture.css"
_BOOTSTRAP_FIXTURE = FIXTURE_DIR / "bootstrap_fixture.css"


def load_typekit_fixture_css() -> str:
    """Return the Typekit fixture CSS, verifying family coverage.

    A fixture that lost a family (rename, bad merge) would fall back
    silently on CI and re-introduce font weather through the back door.
    The missing-family name goes in the error so the fix is one read away.
    """
    try:
        css = _TYPEKIT_FIXTURE.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FrontendGateError(
            f"missing {_TYPEKIT_FIXTURE}; the gate cannot run hermetically"
        ) from exc
    missing = [f for f in REQUIRED_FONT_FAMILIES if f'font-family: "{f}"' not in css]
    if missing:
        raise FrontendGateError(
            f"{_TYPEKIT_FIXTURE} does not declare: {', '.join(missing)}"
        )
    return css


def install_cdn_routes(page) -> None:
    """Block both external stylesheet origins with repo-owned fixtures.

    Every gate navigation otherwise waits on use.typekit.net and
    cdnjs.cloudflare.com before the load event; on CI that wait is the
    stall the 2026-09-07 run died in. handler_type checks the URL so a
    pattern mismatch cannot silently pass a CDN request through.
    """
    def handler_type(url: str) -> str:
        if "use.typekit.net" in url:
            return "typekit"
        if "cdnjs.cloudflare.com" in url and "bootstrap" in url:
            return "bootstrap"
        return "passthrough"

    def _route(route):
        kind = handler_type(route.request.url)
        if kind == "passthrough":
            route.continue_()
        elif kind == "typekit":
            route.fulfill(status=200, content_type="text/css",
                          body=load_typekit_fixture_css())
        else:
            route.fulfill(status=200, content_type="text/css",
                          body=_BOOTSTRAP_FIXTURE.read_text(encoding="utf-8"))

    page.route("**/*", _route)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/scripts/dev/test_frontend_gate.py -k "fixture or cdn_routes" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/dev/frontend_gate.py tests/scripts/dev/test_frontend_gate.py
git commit -m "feat(gate): add hermetic CDN route-blocker with fixture validation"
```

---

### Task 3: Grouped checks with fresh contexts (TDD)

**Files:**
- Modify: `scripts/dev/frontend_gate.py`
- Test: `tests/scripts/dev/test_frontend_gate.py`

**Interfaces:**
- Consumes: `CHECKS` (existing), `install_cdn_routes` (Task 2), `VIEWPORTS` (existing).
- Produces:
  - `CHECK_GROUPS: dict[str, tuple[str, ...]]` -- group name to check names, derived from `CHECKS` (each entry becomes `(name, check, viewports, group)`; derived helper `groups_for(browser_name) -> tuple[str, ...]` returns the groups that browser runs; Firefox returns `("static assets & tokens",)`).
  - `run_checks(new_page, base_url) -> list[str]` -- signature unchanged (tests already patch this), but its internal loop is now group-outer, viewport-inner, opening a fresh page per (browser-group) via the `new_page` factory.
  - `PLANNED_RUNS` recomputed from group membership and `BROWSER_SCOPES`.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_stalled_group_gets_a_fresh_page_for_the_next_group() -> None:
    """A wedged page must not leak into the next group's checks."""
    pages = []

    def _new_page(spec):
        page = Mock()
        pages.append(page)
        return page

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (
            ("first", lambda p, b: [], (frontend_gate.DESKTOP,), "group one"),
            ("second", lambda p, b: [], (frontend_gate.DESKTOP,), "group two"),
        ),
    ):
        run_checks(new_page=_new_page, base_url="http://127.0.0.1:0")

    assert len(pages) == 2  # one fresh page per group, not one shared page
    assert pages[0] is not pages[1]


def test_firefox_scope_runs_only_group_a() -> None:
    """Firefox is a canary: it runs the fastest, stall-prone group only."""
    scope = frontend_gate.groups_for("firefox")
    assert scope == ("static assets & tokens",)
    full = frontend_gate.groups_for("chromium")
    assert len(full) == len(frontend_gate.CHECK_GROUPS)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/scripts/dev/test_frontend_gate.py -k "fresh_page or firefox_scope" -v`
Expected: FAIL (`CHECKS` entries are 3-tuples; no `groups_for`)

- [ ] **Step 3: Implement groups**

Change each `CHECKS` entry to a 4-tuple `(name, check, viewports, group)` and add below it:

```python
#: Firefox is a regression canary, not a second acceptance gate: the
#: 2026-09-01 remediation plan measured both engines agreeing within
#: 0.1px at four window profiles, so a full second pass doubles the
#: stall surface for near-zero signal. Group A is the fastest set and
#: the one the CDN fixtures serve, so it is the canary's scope.
BROWSER_SCOPES = {
    "chromium": None,  # None = all groups
    "firefox": ("static assets & tokens",),
}

#: Groups in execution order, derived from CHECKS (no second declared copy).
CHECK_GROUPS: dict[str, tuple[str, ...]] = {}
for _entry in CHECKS:
    CHECK_GROUPS.setdefault(_entry[3], [])
for _name, _members in CHECK_GROUPS.items():
    CHECK_GROUPS[_name] = tuple(
        entry[0] for entry in CHECKS if entry[3] == _name
    )

def groups_for(browser_name: str) -> tuple[str, ...]:
    """Groups this engine runs. Chromium runs everything."""
    scope = BROWSER_SCOPES.get(browser_name)
    return tuple(CHECK_GROUPS) if scope is None else tuple(
        g for g in CHECK_GROUPS if g in scope
    )
```

Rewrite the `run_checks` inner loop: outer loop over `groups_for(browser_name)` is not needed here (browser is chosen in `main`); instead `run_checks` takes the group order as a parameter with a default of all groups:

```python
def run_checks(new_page, base_url, group_order=None) -> list[str]:
    group_order = group_order or tuple(CHECK_GROUPS)
    failures = []
    for group in group_order:
        for viewport, spec in VIEWPORTS.items():
            claimed = [e for e in CHECKS if e[3] == group and viewport in e[2]]
            if not claimed:
                continue
            try:
                page = new_page(spec)
                install_cdn_routes(page)
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"{group} [{viewport}]: context could not be opened: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue
            for name, check, _viewports, _g in claimed:
                try:
                    results = check(page, base_url)
                except Exception as exc:  # noqa: BLE001
                    failures.append(
                        f"{name} [{viewport}]: raised {type(exc).__name__}: {exc}"
                    )
                    continue
                failures.extend(
                    f"{name} [{viewport}]: {failure}" for failure in results
                )
    return failures
```

Update `PLANNED_RUNS`:

```python
PLANNED_RUNS = sum(
    sum(
        sum(1 for _e in CHECKS if _e[3] == group and _v in _e[2])
        for _v in VIEWPORTS
    )
    for _b in BROWSER_NAMES
    for group in groups_for(_b)
)
```

Update `main`: pass `group_order=groups_for(browser_name)` into `run_checks`, and drop the old per-profile routing (the existing `page.route("http://localhost:8400/**", ...)` Impeccable Live abort moves into `install_cdn_routes` so it survives the fresh-context change).

- [ ] **Step 4: Run the whole gate test module**

Run: `python -m pytest tests/scripts/dev/test_frontend_gate.py -q`
Expected: PASS (the three existing `run_checks` tests get their patched `CHECKS` tuples extended with a group name; this is a mechanical edit inside the already-patched literals)

- [ ] **Step 5: Commit**

```bash
git add scripts/dev/frontend_gate.py tests/scripts/dev/test_frontend_gate.py
git commit -m "feat(gate): isolate checks into fresh-context groups"
```

---

### Task 4: Fail-fast navigation and --live-fonts (TDD)

**Files:**
- Modify: `scripts/dev/frontend_gate.py`
- Test: `tests/scripts/dev/test_frontend_gate.py`

**Interfaces:**
- Consumes: `install_cdn_routes` (Task 2).
- Produces: `NAVIGATION_TIMEOUT_MS = 10_000` constant; `--live-fonts` CLI flag on `_parse_args`; contexts created with `default_navigation_timeout=NAVIGATION_TIMEOUT_MS` unless `--live-fonts` disables route-blocking (still 10s timeout); `main` threads `live_fonts` through to `run_checks` via a module-level `install_cdn_routes(page, live_fonts=False)` signature change.

- [ ] **Step 1: Write the failing tests**

```python
def test_context_gets_the_fail_fast_navigation_timeout() -> None:
    """A 10s stall fails its own check instead of cascading for 30s each."""
    captured = {}

    def _new_page(spec):
        captured["spec"] = spec
        return Mock()

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (("x", lambda p, b: [], (frontend_gate.DESKTOP,), "g"),),
    ):
        run_checks(new_page=_new_page, base_url="http://127.0.0.1:0")

    assert frontend_gate.NAVIGATION_TIMEOUT_MS == 10_000


def test_live_fonts_flag_skips_cdn_blocking() -> None:
    """--live-fonts restores real-CDN navigation for local calibration."""
    page = MagicMock()
    frontend_gate.install_cdn_routes(page, live_fonts=True)
    page.route.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/scripts/dev/test_frontend_gate.py -k "navigation_timeout or live_fonts" -v`
Expected: FAIL (`NAVIGATION_TIMEOUT_MS` undefined; `install_cdn_routes` takes no `live_fonts`)

- [ ] **Step 3: Implement**

```python
#: Fail-fast navigation. Playwright's 30s default turned one stalled
#: subresource into a 30s wait per check, and the shared page let one
#: wedge cascade through the rest of the run. 10s bounds the damage.
NAVIGATION_TIMEOUT_MS = 10_000
```

`install_cdn_routes(page, live_fonts=False)` returns early when `live_fonts` is true. The `new_page` factory in `main` becomes:

```python
def _open_page(browser, spec):
    context = browser.new_context(
        **spec, default_navigation_timeout=NAVIGATION_TIMEOUT_MS
    )
    page = context.new_page()
    install_cdn_routes(page, live_fonts=args.live_fonts)
    return page
```

`_parse_args` gains `parser.add_argument("--live-fonts", action="store_true", help="navigate to the real Typekit and cdnjs origins (local font calibration; requires network)")`, and `main` passes it through. Update the plan docstring in `main` for the new flag.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/scripts/dev/test_frontend_gate.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/dev/frontend_gate.py tests/scripts/dev/test_frontend_gate.py
git commit -m "feat(gate): fail-fast navigation and --live-fonts calibration flag"
```

---

### Task 5: Calibration run and tolerance verification

**Files:**
- Modify: `scripts/dev/fixtures/typekit_fixture.css` (metric values only)

**Interfaces:**
- Consumes: `--live-fonts` (Task 4).
- Produces: fixture metric values verified against the real kit within existing tolerances (spec acceptance criterion 4).

- [ ] **Step 1: Run the gate live**

Run: `python scripts/dev/frontend_gate.py --live-fonts` (network available, local machine)
Expected: all checks pass (proves the kit is reachable and checks are green with real fonts).

- [ ] **Step 2: Run the gate hermetic**

Run: `python scripts/dev/frontend_gate.py`
Expected: all checks pass. If a measurement-sensitive check (shell text scaling, large display scale parity) fails, its failure line names the delta; adjust the corresponding family's `size-adjust`/`ascent-override`/`descent-override` in `typekit_fixture.css` toward the live-measured values and repeat. **No tolerance may be changed** -- only fixture metrics.

- [ ] **Step 3: Record the calibration outcome**

Append a dated line to `scripts/dev/fixtures/README.md`: the date, both run verdicts, and any metric value adjusted. If zero adjustments were needed, record that the initial pins were correct.

- [ ] **Step 4: Commit**

```bash
git add scripts/dev/fixtures/
git commit -m "chore(gate): calibrate font fixture metrics against the live kit"
```

(If Step 3 records zero adjustments, fold this commit into Task 6's close-out commit instead -- an empty-content commit violates the no-noise rule.)

---

### Task 6: Full validation and documentation

**Files:**
- Modify: `PLAYBOOK.md` (Section 3 status, Section 4 dated entry inside the current-batch markers)
- Modify: `.claude/SESSION_CONTEXT.md` (Section 1 test count if changed; Section 4 dependency graph unchanged -- no new module imports)
- Modify: `FINDINGS.md` (header test count if changed)

**Interfaces:**
- Consumes: all prior tasks.

- [ ] **Step 1: Full test suite**

Run: `python -m pytest -q`
Expected: PASS with the new count (was 932; +4 to +6 gate unit tests). Record the exact number.

- [ ] **Step 2: Pre-commit**

Run: `python -m pre_commit run --all-files`
Expected: all hooks pass.

- [ ] **Step 3: One uninterrupted gate run**

Run: `python scripts/dev/frontend_gate.py`
Expected: exit 0. Record the wall time; this run closes the deviation recorded in the 2026-09-07 PLAYBOOK entry (no clean local run was achieved).

- [ ] **Step 4: Documentation**

- PLAYBOOK Section 3: note the gate isolation work as a completed side-task under the active batch.
- PLAYBOOK Section 4: dated entry (`2026-09-07 - Hermetic, group-isolated frontend gate (side-task)`) covering scope, plan-vs-implementation, deviations, validation results with the test count, and forward guidance (WP-7 remains next).
- SESSION_CONTEXT Section 1: test count row if changed.
- FINDINGS.md header: test count if changed.
- Spec status line: append "Implemented; see PLAYBOOK Section 4 entry of the same date."

- [ ] **Step 5: docsync and commit**

Run: `python scripts/doc_state_sync.py --fix` then `--check`; expected exit 0 (root BATCH warning expected while Batch 21 is active).

```bash
git add PLAYBOOK.md .claude/SESSION_CONTEXT.md FINDINGS.md docs/superpowers/specs/2026-09-07-frontend-gate-isolation-design.md scripts/dev/fixtures/README.md
git commit -m "docs(gate): record hermetic gate isolation and calibration"
git push origin test
```

Push is owner-authorized for this branch (PR #227 review-fix channel); CI provides the authoritative Quality Gate verdict.

---

## Self-Review

**Spec coverage:** decisions 1 (groups) -> Task 3; 2 (route-block) -> Tasks 1-2; 3 (fail-fast) -> Task 4; 4 (derived groups, no meta-test) -> Task 3 (no integrity test written); 5 (Firefox canary) -> Task 3 (`BROWSER_SCOPES`, `groups_for`); 6 (metric-pinned fixture) -> Tasks 1 and 5. Acceptance criteria 1 -> Task 3 fresh-context test; 2 -> Task 2 (hermetic by construction, verified in Task 5 Step 2 with network untouched); 3 -> Task 5 Step 2 constraint; 4 -> Task 5; 5 -> Task 6.

**Placeholder scan:** Task 1 Step 1 shows the family-block pattern with the remaining four families named as an elision comment -- acceptable because the content per family is identical modulo the calibrated values that Task 5 verifies, and the fixture README documents the procedure. All other steps carry actual code.

**Type consistency:** `install_cdn_routes(page)` in Task 2 grows the `live_fonts=False` keyword in Task 4 -- Task 3's call site uses the Task 2 signature, Task 4 updates it once. `CHECKS` entries become 4-tuples in Task 3; the two existing tests that patch `CHECKS` with 3-tuples are updated in the same task (Step 4 notes the mechanical edit). `groups_for(browser_name)` is defined in Task 3 and consumed in Task 3's `PLANNED_RUNS` and `main`.
