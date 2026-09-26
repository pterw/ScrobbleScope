# Batch 23 WP-0 frontend plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear the frontend cluster of `BATCH23_DEFINITION.md` WP-0's "After this plan" item 2 --
F-B21-18, F-B21-14, F-B21-22, F-B21-23 and F-B21-60 part 1 -- so the Spotify export batch starts with
no open frontend defect in this set and no green frontend-gate check hiding a red one. This is item 2
of "After this plan" in `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`. **This
plan must land before WP-5**, which rebuilds the index form and is the next JavaScript-heavy page
F-B21-18's harness is meant to guard.

**Architecture:** Five tasks. Task 1 builds the Chromium unit harness for `heatmap.js`'s pure
functions first (Q14 answer a), so Task 2's edit to the same region lands with coverage already in
place. Tasks 2-5 each fix one finding and land one live-probed frontend-gate check for it, **each in
its own new slice module** (`scripts/dev/_frontend_gate_<check>.py`) with its own test file, so no two
tasks' code phases share a file except the one-line registration each makes in
`scripts/dev/frontend_gate.py` itself (a landing rule in Global Constraints covers that one file).

Real dependency, not a file-touch coincidence: Task 2 is `After: 1` because both edit the same
`heatmap.js` region the harness instruments -- Task 1's tests must still pass after Task 2's edit,
and the two are easiest to review as a pair. Task 3, Task 4 and Task 5 are each `After: none`: nothing
in this plan's fixes reads, calls, or depends on another task's code, and each now owns a slice module
and test file no other task touches.

Confirmed still open against the current tree: all five findings (`docs/agents/FINDINGS.md`
F-B21-14, -18, -22, -23, -60) carry no resolved record and no fix commit exists for any of them --
none is "already fixed," so every task below is a real fix, not a citation.

**Tech Stack:** Python 3.13 stdlib, pytest, Playwright (the frontend gate's pinned Chromium and
Firefox), vanilla ES5 in `static/js/` (no Node, no `package.json`), Jinja2 templates, hand-authored
CSS compiled by the existing Tailwind pipeline. No new dependency.

## Global Constraints

Every task's requirements include this section.

- **Qualified interpreter only.** This is a linked worktree; the venv lives in the primary checkout.
  Use `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"` and its sibling
  `pytest.exe` / `pre-commit.exe`. Never bare `pip`, never a second venv. Quote every path.
- **No new dependency, no version change** without owner approval (`AGENTS.md` "Environment Setup").
- **Logging.** Every commit logs an **untagged** `docs/agents/PLAYBOOK.md` Section 4 entry, placed
  directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker. No `WP-<digit>` token in the
  heading. Body opens with "Side task, no batch tag: ... part of Batch 23 WP-0 Part C." Never move
  entries across the markers by hand.
- **Section 3 stays true.** Keep `**Next action:** WP-0 is next.` exactly (DOC007 reads it). Update
  only the progress sentence under "the frontend plan" in Section 3's order list.
- **Behaviour and test changes are scoped to the finding.** A task may change behaviour and edit an
  existing test only where the finding it fixes requires it (Task 5 does, for the spotlight fallback
  and route context -- see Task 5 Step 5, which names both edits). The commit body names every changed
  assertion by test id. A commit never mixes this plan's work with any other plan's.
- **Every change to a check is accepted only on a live probe: red on the planted defect, green on its
  near miss.** For a `frontend_gate.py` slice check, use the mutation-proof method
  `docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md` "Slice protocol" step 9 already
  established: copy the untracked slice module to a scratch path outside the repo, apply the task's
  one-line reversion, run the gate, confirm the named FAIL, restore, confirm `diff` reports nothing.
  For Task 1's harness (not a `frontend_gate.py` check -- see Task 1), revert the JS fix in a scratch
  copy of `heatmap.js` instead and confirm the harness test fails naming the wrong value. Every scratch
  copy is made outside the repository (`git archive HEAD | tar -x -C <scratch dir>`, or a plain file
  copy for a single module) and deleted once the probe is recorded -- never left as an untracked file
  inside the worktree.
- **Bookkeeping is a landing's job, never a task's `Touches:`.** `docs/agents/PLAYBOOK.md`,
  `.claude/SESSION_CONTEXT.md`, `docs/agents/FINDINGS.md` and its archive, `config/docsync.toml`'s
  `[test_count]` pin, and this plan's own checkboxes are all bookkeeping.
- **Shared file: `scripts/dev/frontend_gate.py`.** Every task that adds a check (2, 3, 4 and 5) inserts
  one `CHECKS` tuple entry and one facade-import line, naming its own new slice module. This is the
  only file more than one task's `Touches:` names. **Landing rule for this file: on a conflict in the
  `CHECKS` tuple or an import block, keep both entries, ordered by task number** -- never drop one
  side to resolve it; a landing that finds a real semantic conflict (not just adjacent lines) undoes
  its apply and returns NEEDS_CONTEXT instead. No task edits `config/frontend_gate_checks.toml` --
  new checks are neither required nor disabled there, so they need no entry.
- **Shared file: `.github/workflows/test.yml`.** Task 1 edits the "Run Tests with Coverage" and "Run
  frontend gate" steps only (see Task 1 Step 3). `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`
  Task 4 edits this same file's "Security audit (pip-audit)" step, the last step, a disjoint region.
  If the two plans' code phases overlap in time, keep both changes -- there is no line-level overlap
  between them, and neither reorders a step the other one touches.
- **Test-count mechanism.** Use whatever `doc_state_sync.py` exposes when this plan runs. The
  control-plane plan's Task 1 (F-DOCSYNC-11/-12/-13) is expected to have landed `--fix --test-count N`,
  which pins `N` in `config/docsync.toml`'s `[test_count]` table and writes all four count sites in one
  command. If it has not landed yet, hand-edit the three count sites `doc_state_sync.py --fix` does not
  yet cover: `.claude/SESSION_CONTEXT.md`'s `Tests` row and its `## 6. Test structure (N tests)`
  heading, and the `FINDINGS.md` header count.
- **Commit procedure, in order** (`AGENTS.md` "Commit Rules"):
  1. write the Section 4 entry (Validation line quoted after step 2);
  2. run the full suite to read `N`:
     `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider`,
     quoted as `` Validation: `pytest -q` -- **N passed**; the untracked mutation-runner tests were
     excluded. ``
  3. pin the count (test-count mechanism above);
  4. stage the changed paths by name -- never `git add -A` or `git add .`;
  5. `pre-commit run --all-files`;
  6. `frontend_gate.py` -- every task in this plan touches `static/`, `templates/` or
     `scripts/dev/_frontend_gate_*`, so this step always runs, not conditionally;
  7. `doc_state_sync.py --check`, which must exit 0; the only acceptable warning is the root
     `BATCH23_DEFINITION.md` one.
- **Resolving a finding.** Replace its `Status:` line with the canonical record:
  ```
  - [x] **Status:** resolved
  **Completed:** <YYYY-MM-DD, the commit's date>
  <What fixed it, naming the function.>
  ```
  `--fix` rotates the checked record into `docs/history/findings/FINDINGS_ARCHIVE.md`; stage both
  files. A finding only partly addressed (Task 5, F-B21-60) keeps its existing `Status:` line and
  gains a dated note instead of a resolved record. Never write "resolved" about a finding in prose
  unless its own record is checked (DOC023).
- **Commit discipline.** Conventional Commits, imperative mood, no trailing period, subject 72
  characters or fewer. ASCII only (`--`, not an em dash). Never `--no-verify`. No `Co-authored-by`
  trailer and no other attribution line (repository convention, `AGENTS.md` "Commit Rules").

---

### Task 1: A Chromium unit harness for `heatmap.js`'s pure functions (F-B21-18)

**Touches:** `static/js/heatmap.js`; `pyproject.toml`; `.github/workflows/test.yml`; create
`tests/frontend/__init__.py` and `tests/frontend/test_heatmap_pure_functions.py`.
**After:** none.

Scope is exactly Q14 answer a (`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`,
"Owner answers, 2026-09-23"): `rocketColor`, `countToNorm` and the export header
(`exportHeaderModel` + `exportHeaderLayout`). F-B21-18's own finding text scopes the seam to include
`computeStreak` too, but Q14 answer a is the owner ruling that defers `computeStreak` to WP-6 -- do
not touch it here; cite Q14 in the commit, not F-B21-18's `Status:` line.

**This task was re-probed for this revision** (see `harness-probe.md` next to the review this plan
responded to): the original Step 1 placed the new hook inside the existing `DOMContentLoaded`
listener, mirroring `window.__scrobbleHeatmapDrawnHeader`. That does not work for this harness --
`page.set_content()` leaves `document.readyState` at `"complete"` before `page.add_script_tag()` ever
runs the file, so `DOMContentLoaded` has already fired and never fires again, and a hook assigned only
inside that listener stays `undefined`. The revised Step 1 below (module top level, not inside the
listener) was verified end to end: 13 failed with the old placement (`window.__scrobbleHeatmapTestHooks`
undefined), 13 passed with the placement below, against the pinned repo Playwright/Chromium in a
scratch copy outside the repository. The implementer redoes this same probe once against the real
worktree change before committing (Step 7).

**A second problem, found on the same review pass: CI would collect this harness where it cannot
run.** `.github/workflows/test.yml`'s "Run Tests with Coverage" step (`pytest --cov=scrobblescope
--cov-report=xml --cov-fail-under=70`) runs *before* "Install Playwright browser" -- deliberately,
per that step's own "Last on purpose" comment, since starting a browser costs more than every cheaper
gate. `pyproject.toml` has `testpaths = ["tests"]`, so the coverage step would collect
`tests/frontend/` on a runner with no Chromium yet and fail outright; silently skipping it there is
not acceptable either, since a green run that tested nothing is worse than a red one. Step 3 below
fixes this with a pytest marker, not a workflow reorder (the step order stays exactly as it is, since
starting the browser earlier just to satisfy one new test module would slow every other run for a
gate this small).

- [ ] **Step 1: Expose the seam at the module's top level, not inside `DOMContentLoaded`.**
  `rocketColor`, `countToNorm`, `exportHeaderModel` and `exportHeaderLayout` are pure functions
  declared in the IIFE's outer scope and need nothing from the DOM to be callable, so nothing stops
  the hook running the moment the script executes. Add, directly above the existing
  `document.addEventListener('DOMContentLoaded', function () { ... });` block (immediately after
  `initPreviewRamp`'s declaration):
  ```javascript
  // Module top level, not inside DOMContentLoaded: a harness that loads this
  // file via page.add_script_tag() after the document has already reached
  // "complete" never sees a later DOMContentLoaded fire. These four
  // functions are pure, so the seam is safe to expose immediately.
  window.__scrobbleHeatmapTestHooks = {
    rocketColor: rocketColor,
    countToNorm: countToNorm,
    exportHeaderModel: exportHeaderModel,
    exportHeaderLayout: exportHeaderLayout,
  };
  ```
  No Node, no `package.json`, no build step.

- [ ] **Step 2: Build the harness fixture.** New files `tests/frontend/__init__.py` (empty) and
  `tests/frontend/test_heatmap_pure_functions.py`. Reuse `_load_playwright` from
  `scripts.dev._frontend_gate_runtime` rather than importing `playwright.sync_api` a second way. This
  harness never boots the Flask app: `page.set_content("<!doctype html><html><body></body></html>")`
  then `page.add_script_tag(path=str(REPO_ROOT / "static" / "js" / "heatmap.js"))` is enough to load
  the pure functions, where `REPO_ROOT = Path(__file__).resolve().parents[2]`. A module-scoped fixture
  launches Chromium headless once and yields one page built this way.

  For any test that needs DOM elements present (`exportHeaderModel` reads
  `.heatmap-head__titles .eyebrow`), inject them with
  `page.evaluate("() => { document.body.insertAdjacentHTML('beforeend', '<...>'); }")`, never a second
  `page.set_content()` call on the same page -- re-setting content after the script has run is an
  unnecessary risk to the already-installed hook and adds nothing a DOM insert does not.

- [ ] **Step 3: Register a `browser` pytest marker and wire CI around it.** `pyproject.toml` has no
  `markers` list today. Add one to `[tool.pytest.ini_options]`:
  ```toml
  markers = [
      "browser: needs a real browser binary (Playwright Chromium/Firefox); deselected by CI's coverage step with -m \"not browser\", run explicitly in \"Run frontend gate\" after the browser install.",
  ]
  ```
  Mark the harness module with it, at the top of `tests/frontend/test_heatmap_pure_functions.py`:
  ```python
  pytestmark = pytest.mark.browser
  ```
  In `.github/workflows/test.yml`, change the "Run Tests with Coverage" step's command to deselect it:
  ```yaml
  - name: Run Tests with Coverage
    run: |
      pytest -m "not browser" --cov=scrobblescope --cov-report=xml --cov-fail-under=70
  ```
  and add one line to the existing "Run frontend gate" step (after "Install Playwright browser," so
  Chromium exists by the time it runs), ahead of the two commands already there -- it is the cheapest
  of the three, so it fails fastest if it fails:
  ```yaml
  - name: Run frontend gate
    if: ${{ github.event_name != 'pull_request' || (github.head_ref != 'fly.io-deploy' && github.head_ref != 'flyio-deploy') }}
    run: |
      python -m pytest -m browser tests/frontend -q
      python scripts/dev/results_behavior_tests.py
      python scripts/dev/frontend_gate.py
  ```
  The workflow's step order is unchanged -- both edits are inside steps that already exist, in their
  existing positions. Locally, the repository's own `pytest -q` commit-procedure command (Global
  Constraints) carries no `-m` filter, so `tests/frontend` is still collected and run on every
  commit; if Chromium is missing on that machine, `sync_playwright().chromium.launch()` raises, and
  the harness fails loudly rather than skipping.

  Probed cheaply (`--collect-only` never launches a browser, so no `git archive`/Chromium needed) in
  `harness-probe.md`'s "CI collection" section: `pytest -m "not browser" --collect-only -q
  tests/frontend` collects 0 (2 deselected); `pytest -m "browser" --collect-only -q tests/frontend`
  collects both. The implementer repeats this collection check against the real worktree change
  before committing, alongside Step 7's mutation probe.

- [ ] **Step 4: Write the failing tests.**
  ```python
  @pytest.mark.parametrize(
      ("t", "expected"),
      [
          (0, "rgb(3,5,26)"),          # ROCKET_STOPS[0], t clamped to 0
          (1, "rgb(249,213,118)"),     # ROCKET_STOPS[-1], t clamped to 1
          (0.5, "rgb(166,44,92)"),     # ROCKET_STOPS[3], an exact stop
          (-1, "rgb(3,5,26)"),         # clamps low
          (2, "rgb(249,213,118)"),     # clamps high
      ],
  )
  def test_rocket_color(js_page, t, expected):
      assert js_page.evaluate(
          "(t) => window.__scrobbleHeatmapTestHooks.rocketColor(t)", t
      ) == expected

  @pytest.mark.parametrize(
      ("count", "max_count", "expected"),
      [(0, 100, 0), (100, 100, 1), (-5, 100, 0), (5, 0, 0)],  # the two guard clauses, then the ends
  )
  def test_count_to_norm(js_page, count, max_count, expected):
      assert js_page.evaluate(
          "(a) => window.__scrobbleHeatmapTestHooks.countToNorm(a[0], a[1])",
          [count, max_count],
      ) == expected

  def test_export_header_model_uppercases_only_when_the_css_says_to(js_page):
      js_page.evaluate(
          """() => document.body.insertAdjacentHTML('beforeend',
              '<div class="heatmap-head__titles">' +
              '<span class="eyebrow" style="text-transform:uppercase">test eyebrow</span>' +
              '</div>')"""
      )
      model = js_page.evaluate("() => window.__scrobbleHeatmapTestHooks.exportHeaderModel()")
      assert model["eyebrow"] == "TEST EYEBROW"
  ```
  `exportHeaderLayout` needs its own block: it takes a canvas 2D context as its first argument, and
  `KPI_LABEL_FONT`/`KPI_VALUE_FONT` name custom fonts (`"input-mono-narrow"`, `"gotham"`) this
  CSS-less harness never loads, so a real `canvas.getContext('2d')` would fall back to whatever the
  host OS resolves the generic `monospace`/`sans-serif` families to -- an environment-dependent
  number, not a repository fact (confirmed in the probe: the real-font path measured `columns === 2`
  at `gridWidth = 340` on this Windows/Chromium combination, not the `1` an earlier draft of this
  plan asserted, and there is no guarantee a Linux CI runner agrees). Pass a stub `ctx` instead --
  `exportHeaderLayout` only ever calls `ctx.measureText(text).width` and sets `ctx.font`, both of
  which the stub controls exactly:
  ```python
  STUB_CTX_JS = "({ font: '', measureText(text) { return { width: text.length * 7 }; } })"
  ITEMS_JS = """[
      {label: 'DAILY AVERAGE', sub: 'PER DAY', value: '12.3'},
      {label: 'BEST DAY', sub: 'PEAK', value: '88'},
      {label: 'STREAK', sub: 'DAYS', value: '14'},
      {label: 'TOTAL', sub: 'SCROBBLES', value: '4,491'},
  ]"""

  @pytest.mark.parametrize(("grid_width", "expected_columns"), [(1280, 4), (340, 2), (150, 1)])
  def test_export_header_layout_columns(js_page, grid_width, expected_columns):
      columns = js_page.evaluate(
          f"(w) => window.__scrobbleHeatmapTestHooks.exportHeaderLayout({STUB_CTX_JS}, w, {ITEMS_JS}).columns",
          grid_width,
      )
      assert columns == expected_columns
  ```
  These three widths are exact under the function's own arithmetic
  (`needed = widest + EXPORT_KPI_GUTTER`, `EXPORT_KPI_GUTTER = 14`, widest label at 7px/char is
  `"DAILY AVERAGE".length * 7 = 91`, so `needed = 105`): `1280/4 = 320 >= 105` stays at 4 columns;
  `340/4 = 85 < 105` drops to 2, and `340/2 = 170 >= 105` stops there; `150/4 = 37.5 < 105` drops to 2,
  and `150/2 = 75 < 105` drops again to 1. Verified in the probe (`harness-probe.md`): all three pass.

- [ ] **Step 5: Run them to verify they fail** with
  `window.__scrobbleHeatmapTestHooks is undefined` before Step 1 is applied.

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/frontend -q`

- [ ] **Step 6: Apply Step 1 and run again.** Expected: pass, 13 of 13.

- [ ] **Step 7: Live probe, twice.** First, the mutation proof: in a scratch copy outside the
  repository (`git archive HEAD | tar -x -C <scratch dir>`), change `ROCKET_STOPS[0].r` from `3` to
  `4` in the scratch `heatmap.js` and re-run the scratch copy's tests; confirm
  `test_rocket_color[0-rgb(3,5,26)]` fails naming `rgb(4,5,26)`. Second, the collection proof from
  Step 3: run `pytest -m "not browser" --collect-only -q tests/frontend` against the real worktree
  and confirm it collects 0; run `pytest -m "browser" --collect-only -q tests/frontend` and confirm
  it collects all of them. Delete the scratch copy once confirmed. (Both repeat, on the real worktree
  change, the same probes already recorded in `harness-probe.md` for this plan's Critical,
  Important-2 and CI-collection findings.)

- [ ] **Step 8: Resolve F-B21-18 and commit.** The module count rises by one (`tests/frontend`).
  Canonical reason: "rocketColor, countToNorm and the export header layout are exercised by a
  Chromium harness (tests/frontend/test_heatmap_pure_functions.py) through
  window.__scrobbleHeatmapTestHooks, exposed at the module's top level; computeStreak is WP-6's per
  Q14 answer a; the harness carries a browser pytest marker so CI's pre-browser coverage step
  deselects it and the post-browser frontend-gate step runs it instead."
  ```bash
  git commit -m "test(heatmap): Add a Chromium harness for the pure-function seam"
  ```

### Task 2: Focusable, labelled heatmap cells (F-B21-14)

**Touches:** `static/js/heatmap.js`; `static/css/heatmap.css`; `scripts/dev/frontend_gate.py`; create
`scripts/dev/_frontend_gate_heatmap_access.py` and `tests/scripts/dev/test_frontend_gate_heatmap_access.py`.
**After:** 1 (same `heatmap.js` region; the harness proves the sibling pure functions stay correct
while this task edits nearby code).

Q8 answer a: focusable, labelled cells that reuse the tooltip text. The ramp itself is not touched
(F-B21-14's own text: the ramp is sound; the defect is that nothing but a mouse hover reaches a cell).
The new check lives in its own slice module, not in `_frontend_gate_pipeline.py`, so this task's code
phase shares no file with Task 5's beyond the one-line registration in `frontend_gate.py` (Global
Constraints' landing rule covers that).

- [ ] **Step 1: Extract the tooltip text into a shared helper**, so the accessible name and the mouse
  tooltip can never drift. In `heatmap.js`, add:
  ```javascript
  function cellAccessibleLabel(date, count) {
    var countStr = count === 0
      ? 'No scrobbles'
      : count + ' scrobble' + (count !== 1 ? 's' : '');
    return formatDateLong(date) + ' -- ' + countStr;
  }
  ```
  Replace `showTooltip`'s inline `dateStr`/`countStr` construction and its `tooltip.textContent` line
  with `tooltip.textContent = cellAccessibleLabel(cd.date, cd.count);`.

- [ ] **Step 2: Make every cell focusable and labelled.** In both `renderHeatmap`'s and
  `renderHeatmapMobile`'s grid-cell loops, immediately after `rect.setAttribute('class',
  'heatmap-cell');`, add:
  ```javascript
  rect.setAttribute('tabindex', '0');
  rect.setAttribute('role', 'img');
  rect.setAttribute('aria-label', cellAccessibleLabel(d, count));
  ```

- [ ] **Step 3: Wire keyboard focus to the same tooltip a mouse gets.** In `initTooltips`, alongside
  the existing `mouseenter`/`mouseleave`/`touchstart` listeners on each `cd.el`, add:
  ```javascript
  cd.el.addEventListener('focus', function () { showTooltip(cd, {clientX: 0, clientY: 0}); });
  cd.el.addEventListener('blur', hideTooltip);
  ```
  (The `aria-label` already carries the text to a screen reader that never paints the tooltip; this
  gives a sighted keyboard user the same visible cue a mouse gets.)

- [ ] **Step 4: Add the focus ring.** `static/css/heatmap.css` has no `.heatmap-cell` rule today; a
  bare SVG `<rect>`'s user-agent focus outline is inconsistent across browsers. Add:
  ```css
  .heatmap-cell:focus-visible {
    outline: 2px solid var(--shell-accent);
    outline-offset: 1px;
  }
  ```

- [ ] **Step 5: New slice module and check.** Create `scripts/dev/_frontend_gate_heatmap_access.py`,
  following the header/docstring convention of the other `_frontend_gate_*.py` slices, importing
  `create_job`, `set_job_progress` (and whatever job-repository helpers it needs) directly from
  `scrobblescope.repositories`, and `MIGRATED_PAGES`/`GATE_JOB_IDS` from
  `scripts.dev._frontend_gate_shared` -- not from `_frontend_gate_pipeline.py`, so this module has no
  import-time dependency on the file Task 5 also touches. Add `check_heatmap_cells_are_keyboard_accessible`,
  seeded the way `_frontend_gate_pipeline.py`'s `check_artist_spotlight_rotation` already seeds a job
  (`create_job`, then `set_job_progress` with a fixed, small `daily_counts` map so one exact date and
  count are known), navigated to `/heatmap`. It: presses Tab from the grid's container until a
  `.heatmap-cell` is `document.activeElement`; asserts that element's `aria-label` equals the exact
  string `cellAccessibleLabel` produces for the seeded date/count it lands on; asserts
  `getComputedStyle(document.activeElement).outlineStyle !== 'none'`. Create
  `tests/scripts/dev/test_frontend_gate_heatmap_access.py` for the module's own unit-testable pieces
  (following the pattern of the other slices' test files). In `scripts/dev/frontend_gate.py`, add
  `"heatmap cells keyboard access"` to `CHECKS`, `LAYOUT_PIPELINE` group, and add
  `check_heatmap_cells_are_keyboard_accessible` in a new
  `from scripts.dev._frontend_gate_heatmap_access import (...)` import line, alphabetically among the
  other `_frontend_gate_*` imports.

- [ ] **Step 6: Run the new check and the full gate.** Confirm both pass.

- [ ] **Step 7: Live probe.** In a scratch copy of `_frontend_gate_heatmap_access.py` and a scratch
  copy of `heatmap.js` (outside the repository), comment out the `tabindex`/`role`/`aria-label` lines
  added in Step 2. Run the gate against the scratch pair; confirm the new check fails naming the
  missing focusable cell or the empty label. Delete both scratch copies once confirmed.

- [ ] **Step 8: Resolve F-B21-14 and commit.** Canonical reason: "heatmap cells carry tabindex,
  role=img and an aria-label built by the same cellAccessibleLabel helper the mouse tooltip uses;
  check_heatmap_cells_are_keyboard_accessible (its own slice module) proves it live."
  ```bash
  git commit -m "fix(heatmap): Make grid cells reachable and labelled for keyboard users"
  ```

### Task 3: A two-state toggle that reattaches to the system (F-B21-22)

**Touches:** `static/js/theme.js`; `scripts/dev/frontend_gate.py`; `scripts/dev/_frontend_gate_theme.py`;
`tests/scripts/dev/test_frontend_gate_theme.py`.
**After:** none.

Q9 answer b. `templates/base.html`'s pre-paint script already treats `saved === null` as "follow the
system" (`dark = saved === 'true' || (saved !== 'false' && matchMedia(...).matches)`); it needs no
change. The defect is entirely that `theme.js` never lets `saved` become `null` again once a choice is
made. No other task in this plan touches `_frontend_gate_theme.py`, so this task's edit to it needs no
new slice module.

- [ ] **Step 1: Clear the key when the choice matches the system.** In `theme.js`'s `darkSwitch`
  `'change'` listener, replace the unconditional `localStorage.setItem('darkMode', this.checked);`
  with:
  ```javascript
  darkSwitch.addEventListener('change', function () {
      applyTheme(this.checked);
      var systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      try {
          if (this.checked === systemDark) {
              localStorage.removeItem('darkMode');
          } else {
              localStorage.setItem('darkMode', this.checked);
          }
      } catch (error) {
          // Storage can throw in private mode. The theme still applies for
          // this page view; it just will not survive a reload.
      }
  });
  ```

- [ ] **Step 2: New gate check.** In `_frontend_gate_theme.py`, add `check_theme_reattaches_to_system`.
  Open a browser context with `color_scheme="dark"` (the same `browser.new_context(color_scheme=...)`
  pattern the module already uses). Load a migrated page; click `[data-theme-toggle]` once to force
  light -- diverging from the emulated dark system -- and confirm after a reload that the page is
  still light and `localStorage.getItem('darkMode') === 'false'`. Click the toggle again, back to
  dark, now matching the emulated system, and confirm `localStorage.getItem('darkMode') === null`
  immediately after the click, then reload and confirm the page still resolves dark (from the system
  query alone, with no stored key). Register `"theme reattaches to system"` in `CHECKS`,
  `THEME_MOTION` group, beside `"theme persistence"`; add the check's name to the facade's
  `_frontend_gate_theme` import block.

- [ ] **Step 3: Run the new check and the full gate.** Confirm both pass.

- [ ] **Step 4: Live probe.** In a scratch copy of `theme.js` (outside the repository), revert Step 1
  to the unconditional `setItem`. Run the new check against it; confirm it fails naming the stale
  `'true'`/`'false'` value still in `localStorage` after the matching click. Delete the scratch copy
  once confirmed.

- [ ] **Step 5: Resolve F-B21-22 and commit.** Canonical reason: "the toggle's change handler clears
  darkMode when the chosen state matches the system query, so the pre-paint script's existing
  saved === null branch reattaches to the system; check_theme_reattaches_to_system proves it live."
  ```bash
  git commit -m "fix(theme): Let a matching toggle choice reattach to the system"
  ```

### Task 4: The inline marks colour themselves, with no per-wrapper CSS list (F-B21-23)

**Touches:** `templates/inline/scrobble_scope_inline.svg`;
`templates/inline/scrobble_scope_lockup_inline.svg`; `static/css/shell.css`;
`scripts/dev/frontend_gate.py`; `scripts/dev/_frontend_gate_assets.py`;
`tests/scripts/dev/test_frontend_gate_assets.py`.
**After:** none.

The finding's own blocker is gone: `static/css/tailwind.src.css` defines
`--bars-color: var(--color-primary)`, and `--shell-accent` in `shell.css` already equals
`--color-primary` in both themes (`#6a4baf` light, `#b39dde` dark). The "two different dark values"
F-B21-23 cites was global.css's retired `.dark-mode` token (gone since WP-8). Unifying the asset needs
no value decision. No other task in this plan touches `_frontend_gate_assets.py`, so this task's edit
to it needs no new slice module.

- [ ] **Step 1: Colour the assets themselves.** In both
  `templates/inline/scrobble_scope_inline.svg` and `scrobble_scope_lockup_inline.svg`:
  - Change the embedded `<style>` block's `.cls-1 { fill: none; stroke: #6a4baf; ... }` so `stroke` is
    `var(--bars-color)`. Keep `fill: none` and the rest of the block unchanged.
  - Add `fill="currentColor"` to the root `<svg>` element. `#tagline` and `#logo-text`'s letterform
    `<path>` elements carry no fill rule of their own today and will inherit this; `.cls-1`'s own
    `fill: none` keeps the bar paths from picking it up too.

- [ ] **Step 2: Collapse the per-wrapper CSS list.** In `static/css/shell.css`, delete the two rules
  ```css
  .site-header__mark svg .cls-1,
  .index-hero__mark svg .cls-1 {
      stroke: var(--shell-accent);
  }

  .site-header__mark svg #logo-text path,
  .index-hero__mark svg #logo-text path {
      fill: var(--shell-ink);
  }
  ```
  and the "Every wrapper listed here has to be listed" comment above them, replacing all of it with:
  ```css
  /* The asset colours itself now (fill="currentColor", stroke: var(--bars-color)
     baked into the SVG, F-B21-23). Nothing needs naming here: any wrapper that
     sets color gets a correct mark. */
  .ss-mark {
      color: var(--shell-ink);
  }
  ```
  `check_mark_follows_theme` in `_frontend_gate_theme.py` reads computed `stroke`/`fill` off
  `svg .cls-1` / `svg #logo-text path` already and needs no change -- it was asserting the right
  outcome all along, against a mechanism this task simplifies.

- [ ] **Step 3: New gate check, on the assets themselves.** In `_frontend_gate_assets.py` (the module
  that already audits which stylesheet a page loads), add `check_inline_marks_need_no_wrapper_list`.
  This is an asset-content fact, not a rendered one: read both SVG template files directly off disk
  (`Path(...).read_text()`, not a live page) and assert each contains `fill="currentColor"` on its
  root element, `stroke: var(--bars-color)` in its `<style>` block, and no literal hex colour anywhere
  in the file (a simple `#[0-9a-fA-F]{6}` search). Register `"inline marks need no wrapper list"` in
  `CHECKS`, `STATIC_ASSETS` group, beside `"stylesheet isolation"`; add the check's name to the
  facade's `_frontend_gate_assets` import block.

- [ ] **Step 4: Run the new check, `check_mark_follows_theme`, and the full gate.** Confirm all pass.

- [ ] **Step 5: Live probe.** In scratch copies outside the repository, put a literal hex colour back
  in one SVG's `<style>` block. Run the new check; confirm it names that file. Separately, in a
  scratch copy of `shell.css`, remove the `.ss-mark { color: ... }` rule added in Step 2 and confirm
  `check_mark_follows_theme` now fails (the letterforms lose their `currentColor` source) -- this
  proves the new rule is load-bearing, not redundant with something else. Delete both scratch copies
  once confirmed.

- [ ] **Step 6: Resolve F-B21-23 and commit.** Canonical reason: "the inline marks carry
  fill=currentColor and stroke: var(--bars-color) themselves; shell.css's five-rule per-wrapper list
  collapses to one color declaration on .ss-mark; check_inline_marks_need_no_wrapper_list reads the
  assets directly."
  ```bash
  git commit -m "fix(assets): Let the inline marks colour themselves"
  ```

### Task 5: The artist spotlight stops cropping, overlaying, animating and faking a photo (F-B21-60 part 1)

**Touches:** `templates/results.html`; `static/css/results.css`; `static/js/results-spotlight.js`;
`scrobblescope/routes/album_flow.py`; `tests/test_routes.py`; `scripts/dev/frontend_gate.py`; create
`scripts/dev/_frontend_gate_spotlight_photo.py` and `tests/scripts/dev/test_frontend_gate_spotlight_photo.py`.
**After:** none. The pre-existing `check_artist_spotlight_rotation` in `_frontend_gate_pipeline.py`
is a different check testing a different property (that hydration replaces a stale response, not
photo geometry); this task never reads, calls or edits it, and adds its own new check in its own new
module instead, seeding its own job the same way `check_artist_spotlight_rotation` does. Nothing in
this task depends on Task 2's code or shares a file with it beyond the one-line registration in
`frontend_gate.py`, covered by the landing rule in Global Constraints.

Q11 answer a, part 1 only: crop, overlay, animation and fallback fixes. **No Spotify icon and no
provider-attribution work here** -- no asset was supplied, and F-B21-60's icon and attribution bullets
stay open under the same finding ID (F-B22-4 already tracks the logo-asset gap separately).

- [ ] **Step 1: Fix the crop.** Spotify artist photos are already square (F-B21-60's own text); the
  defect is the wide `.spotlight-card-bleed` frame forcing `object-cover` to cut a square photo's top
  and bottom. In `results.css`, replace the wide-bleed image treatment with a square image box:
  `aspect-ratio: 1 / 1`, sized to the card, `border-radius: 4px` at the mobile/default breakpoint and
  `8px` at `768px` and up (the owner ruling's exact numbers). Restructure `results.html`'s spotlight
  markup so the image sits in that square box and the name/rank/playtime/summary sit in a sibling flex
  column -- beside the image at `768px` and up, below it under that width -- never positioned over the
  photo.

- [ ] **Step 2: Delete the overlay.** Remove `.spotlight-scrim-top`, `.spotlight-scrim-bottom` and
  `.spotlight-scrim-overlay` from `results.css`, and their corresponding `<div>`s from `results.html`.
  Nothing is drawn on top of the photo.

- [ ] **Step 3: Delete the animation.** In `results-spotlight.js` `renderCandidate`, delete the
  `view.content.style.opacity` fade and its `setTimeout`; call `apply()` directly every time,
  regardless of the `animate` argument or `state.reducedMotion`. An instant swap is explicitly
  acceptable per the ruling; reduced motion already keeps the first artist still, by never starting
  the rotation `setInterval` in `startArtistSpotlightRotation` -- that part is unchanged.

- [ ] **Step 4: Delete the album-art fallback, server and client.** In `templates/results.html`,
  delete the `{% set spotlight_fallback_img = ... %}` line and the whole `{% if spotlight_fallback_img
  %}...{% else %}...{% endif %}` branch; the card becomes one shape, given `style="display:none"`
  initially (matching `results-spotlight.js`'s existing `view.card.style.display = ''` reveal
  convention). In `scrobblescope/routes/album_flow.py`, stop computing and passing `top_artist_image`
  to the template (the album-art seed it fed is no longer rendered); `spotlight_artists` itself is
  unchanged -- it still supplies the five-candidate pool the client filters.

  In `results-spotlight.js`, `startArtistSpotlightRotation` changes shape: instead of rendering the
  first candidate immediately and hydrating in the background, it waits for every `hydrateCandidate`
  call (already returns its `fetch` promise, unchanged) to settle via `Promise.all(...)`, then
  filters `state.candidates` down to `c => c.image_url` -- candidates with no confirmed Spotify photo
  are dropped from the rotation entirely, matching the ruling. If the filtered list is empty, return
  without ever calling `renderCandidate` or `view.card.style.display = ''`: the card stays hidden.
  Otherwise, replace `state.candidates` with the filtered list, reset `state.index = 0`, call
  `renderCandidate(view, state, false)` once to reveal it, and start the same `setInterval` rotation
  as today (guarded by the same `reducedMotion`/`length < 2` checks) over the filtered list. `hidePortrait`
  and `.spotlight-no-image` become unused by this path -- delete `hidePortrait`'s call sites that
  existed only for the deleted fallback, and delete `.spotlight-no-image` and
  `.spotlight-card-bleed:has(.spotlight-no-image)` from `results.css`.

- [ ] **Step 5: Update `tests/test_routes.py` -- two tests, named.**
  - **Delete `test_results_page_top_artist_image_from_first_available_album` whole** (its two-album
    fixture, one missing `album_image`, exists solely to assert
    `'src="https://example.com/thebends.jpg"' in html`, the album-art fallback Step 4 removes; there
    is nothing left in this test to keep).
  - **Keep `test_results_page_passes_top_artist_aggregate_stats`, but drop its `top_artist_image`
    assertion and reword its docstring.** Change the docstring from "Results page context includes
    top_artist_name, top_artist_scrobbles, top_artist_album_count, top_artist_image." to the same
    sentence with `top_artist_image` removed, and delete the line
    `assert 'src="https://example.com/okcomputer.jpg"' in html` -- that image now only ever reaches
    the page through client-side hydration this route test does not drive. Keep its
    `data-artist="Radiohead"` and `"350 scrobbles across 2 albums in 2024"` assertions unchanged; they
    do not depend on the fallback. Name both edits in the commit body, per Global Constraints.

- [ ] **Step 6: New slice module and check.** Create `scripts/dev/_frontend_gate_spotlight_photo.py`,
  importing `create_job`, `set_job_progress` from `scrobblescope.repositories` and `MIGRATED_PAGES`
  from `scripts.dev._frontend_gate_shared` directly (not from `_frontend_gate_pipeline.py`). Seed a
  job the same way `_frontend_gate_pipeline.py`'s `check_artist_spotlight_rotation` does (results with
  several artists, so `spotlight_artists` is non-empty) and mock `/api/artist_spotlight` the same way
  that check already does (`page.add_init_script` overriding `window.fetch` for that path). Add
  `check_artist_spotlight_photo_has_no_crop_overlay_or_animation`, asserting: the photo element's
  rendered aspect ratio is within 1% of its `naturalWidth`/`naturalHeight` ratio (no crop); no other
  element's bounding box intersects the photo element's bounding box (no overlay); the photo's
  computed `opacity` never changes across a rotation tick, sped up the same way the existing check
  speeds up its 7s interval (no animation). Add a second check,
  `check_artist_spotlight_card_hidden_with_no_photo`, in the same module: every mocked
  `/api/artist_spotlight` response resolves `image_url: null`, and the card's computed `display`
  stays `none` for the whole run (no card, no fallback). Create
  `tests/scripts/dev/test_frontend_gate_spotlight_photo.py` for the module's own unit-testable pieces.
  In `scripts/dev/frontend_gate.py`, add both check names to `CHECKS`, `LAYOUT_PIPELINE` group, beside
  `"artist spotlight rotation"`, and add both function names in a new
  `from scripts.dev._frontend_gate_spotlight_photo import (...)` import line, alphabetically among the
  other `_frontend_gate_*` imports.

- [ ] **Step 7: Run the new checks and the full gate.** Confirm all pass.

- [ ] **Step 8: Live probe, twice.** In a scratch copy of `results-spotlight.js` (outside the
  repository), reintroduce the opacity fade from Step 3; confirm the opacity assertion fails naming
  the observed change. In a scratch copy of `results.css`, revert the image box to
  `aspect-ratio: 16 / 10`; confirm the crop assertion fails. Delete both scratch copies once confirmed.

- [ ] **Step 9: Update F-B21-60 with a dated note, not a resolved record.** It stays P1, `Status:`
  line unchanged, with a new dated line: crop, overlay, animation and the album-art fallback are
  fixed (this task); the Spotify icon and provider-attribution bullets stay open, no new finding ID
  (F-B22-4 already tracks the logo asset).
  ```bash
  git commit -m "fix(results): Stop cropping, overlaying and faking the artist spotlight photo"
  ```

## Acceptance

- Task 1's harness mechanism (top-level hook, not inside `DOMContentLoaded`) was probed end to end in
  a scratch copy outside the repository before this plan was finalized: red (13 failed,
  `window.__scrobbleHeatmapTestHooks` undefined) on the pre-fix placement, green (13 passed,
  including the deterministic-stub `exportHeaderLayout` cases at 1280/340/150) on the fixed
  placement. Its CI wiring was probed too: `pytest -m "not browser" --collect-only -q tests/frontend`
  collects 0, `pytest -m "browser" --collect-only -q tests/frontend` collects all of them. Details
  and full pass/fail lines are in `harness-probe.md`. Each task still repeats its own live probe at
  dispatch time, on the real worktree change.
- Each task's own live probe holds: red on the reverted defect, green on the shipped fix.
- `pytest -q`, `pre-commit run --all-files`, `frontend_gate.py` and `doc_state_sync.py --check` all
  exit 0 on the final tree, in that order, per the Commit procedure.
- F-B21-14, F-B21-18, F-B21-22 and F-B21-23 carry resolved records; F-B21-60 carries a dated note
  recording partial progress, its icon and attribution bullets still open under the same ID.
- No task in this plan touches `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`'s WP-5
  scope (the index form rebuild); this plan is a precondition for it, not part of it.
- Tasks 2, 3, 4 and 5 each own a slice module and test file no other task touches; the only file more
  than one task's `Touches:` names is `scripts/dev/frontend_gate.py`, covered by the "keep both
  entries" landing rule in Global Constraints. `.github/workflows/test.yml` is touched by this plan
  (Task 1) and separately by the test-infra/deps plan's Task 4, in disjoint steps; Global Constraints'
  "keep both changes" note covers that overlap.

## Open questions

None.
