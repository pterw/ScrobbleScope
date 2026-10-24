# UI Consistency Round 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Commit the four UI changes the owner accepted in live mode on 2026-10-22 (Orpheus Pro as the display serif, the heatmap preview card and lede, the Results stat values in Gotham) and two more from the round's backlog (S2: no arrows on the two unmatched-report links; L1: no "Opening your results..." line under a finished run), each with tests that assert the intended behaviour.

**Architecture:** One side-task branch, `feat/ui-consistency-round-2`, cut from `main` at 14b7d70, opened as a draft PR. Task 0 commits this plan; Tasks 1-5 are one atomic commit each, with an untagged PLAYBOOK Section 4 entry. The accepted design changes already exist as patches (`task-1-wip.patch`, `task-2-wip.patch`, `task-3-wip.patch` in `.superpowers/sdd/2026-10-22-ui-round-2/`); a task applies its patch only after its new tests are proven red without it. Tasks run as parallel code phases in detached worktrees and land one at a time.

**Tech Stack:** Flask + Jinja templates, Tailwind v4 (`scripts/dev/tailwind_build.py`), vanilla JS, pytest, Playwright Chromium (`tests/frontend/` harness and `scripts/dev/frontend_gate.py`), docsync.

**Owner rulings this plan carries (verbatim where quoted):**
- 2026-10-22, on the live session: "The current UI changes are good." On I1: "Change to Orpheus Pro. This should replace the serif font globally, so Instrument Serif as a fallback to Orpheus Pro." On S1: "For each span||stat, use Gotham Book." (Top Artist, a name, included.)
- 2026-10-22, backlog: S2 "The arrows should go" ("view breakdown ->" and "Open unmatched report ->"); L1 "Opening your results..." "can go -- it repeats what is stated above it".
- 2026-10-22, tests: "For the UI, the tests will have to change. They always need to test for intended behaviour, not if the code works as written." Standing: "a false green is worse than a true red."
- 2026-10-23: "the focus will be on folding in S2 and L1 with the uncommited current changes. Live work is to be deferred to a different session for later." / "I took a look with the Orpheus Pro changes and they are good ... Likewise with the Results and error pages so no issues." / "I would suggest having a draft PR with the same PR body as per the template and land commits there at the moment."

**Out of scope (later live session):** I2, I3/H3, I4, I5, H1, L2 from `.superpowers/sdd/2026-10-22-ui-round-2/backlog.md`.

## Global Constraints

- Work in the main worktree `C:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init` (MAIN) on `feat/ui-consistency-round-2`, or in a detached code-phase worktree `C:/ssw/u<N>`. `PY` = `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"`.
- The workspace `constraints.md` (`.superpowers/sdd/2026-10-22-ui-round-2/constraints.md`) is binding: logging (R1), commit procedure (R3), staging (R8), environment (R9), tests (R10), docs (R12), the suite gate's `--ignore` of the owner's untracked test module (R14), the WIP patches (R15).
- Side-task logging: every commit adds one dated entry `### 2026-10-23 - <title>` directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker line, no `(Batch N WP-X)` tag, ending `` Validation: `pytest -q` -- **N passed**. ``.
- Commit messages: Conventional Commits, imperative subject <= 72 characters, body says why. No attribution line.
- Never `--no-verify`, `--amend`, rebase, reset, `sed -i`, or `git checkout`/`git restore` of a file holding uncommitted work.
- Tests assert intended behaviour. Each new or edited test is proven red against the tree without the change (and by each planted defect listed), then green; quote both lines in the report.
- The WIP patches' copy, faces and values are the owner's; do not reword or restyle them.
- ASCII only in Markdown and commit messages. Cite functions by name, not line number. Grep before claiming anything does not exist.
- Line numbers in sweeper hit lists are as of origin/main 14b7d70 and drift once earlier tasks land: re-grep each hit before editing.

---

### Task 0: Commit this plan and point Section 3 at it

Wave 0, serial, in MAIN.

**Files:**
- Create: `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md` (this plan, with the review fixes the dispatch names)
- Modify: `docs/agents/PLAYBOOK.md` (Section 3, Section 4)

- [x] **Step 1:** Copy `.superpowers/sdd/2026-10-22-ui-round-2/plan-draft.md` to `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md`, applying the review fixes named in the dispatch.
- [x] **Step 2:** PLAYBOOK Section 3, "Before WP-1" bullet: replace the sentence that begins "A side-task PR of cheap fixes from the 2026-10-21 architecture review and the logging audit runs next" (it ends "the documentation refresh merges last.") with: "A side-task PR of cheap fixes from the 2026-10-21 architecture review and the logging audit is done (branch `fix/pre-batch23-side-tasks`, plan `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md`), and so is a CI change that keeps Playwright's Ubuntu packages in the Actions cache (branch `ci/playwright-apt-cache`, plan `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md`). UI consistency round 2 runs now (branch `feat/ui-consistency-round-2`, plan `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md`): the four changes the owner accepted in live mode, the two unmatched-report arrows and the loading page's redundant redirect line; the round's other backlog items wait for a later live session. The documentation refresh merges last." Leave every other sentence, and "**Next action:** WP-0 is next.", unchanged.
- [x] **Step 3:** Section 4 entry `### 2026-10-23 - Plan UI consistency round 2` (scope, the owner's 2026-10-23 rulings above, what the plan holds, deviations none, edited existing tests none).
- [x] **Step 4:** `git add docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md` before `--fix`: DOC001 resolves Section 3's backticked paths through the index, so an unstaged plan file fails it.
- [x] **Step 5:** Commit procedure (R3; the browser gates are not needed for a docs-only commit); message `docs(plan): Plan UI consistency round 2`.

---

### Task 1: Orpheus Pro becomes the display serif (I1)

Wave 1, code phase in `C:/ssw/u1`, then landing.

**Touches:**
- `static/css/tailwind.src.css`, `static/css/tailwind.css`, `static/css/index.css` (from `task-1-wip.patch`)
- `static/js/heatmap.js` (the export header's headline font only)
- `scripts/dev/_frontend_gate_layout.py` (`REQUIRED_FONT_FAMILIES`)
- `scripts/dev/_frontend_gate_theme.py` (`check_heatmap_export_header_matches_page`, and the new `headline_font_failures`)
- `tests/scripts/dev/test_tailwind_build_cli.py` (`test_theme_source_locks_the_batch_21_design_tokens`)
- `tests/scripts/dev/test_frontend_gate_layout.py` (one new test)
- `tests/scripts/dev/test_frontend_gate_theme.py` (new tests only; add `headline_font_failures` and `_plain_family` to its `MOVED` name list if it still keeps one for module-level names -- check)
- `DESIGN.md`, `docs/design/RECONCILIATION.md`, `README.md`, `docs/agents/AGENT_NOTES.md`

**Interfaces:**
- Produces: `--font-serif: "orpheuspro", "instrument-serif", "corporate-a", Georgia, serif;` and the DESIGN.md Role Segregation Rule sentence "Gotham gets the numbers, Orpheus Pro gets the words." (Task 2 appends to it).
- Produces: `drawnHeader.headlineFont` in `static/js/heatmap.js` (the canvas font string the export headline was drawn with), read by `check_heatmap_export_header_matches_page`.

Sweeper hits at origin/main (live) this task owns: `DESIGN.md:36`, `:42`, `:148`, `:157`, `:158`, `:165`, `:242`; `docs/design/RECONCILIATION.md:179`; `README.md:178`; `docs/agents/AGENT_NOTES.md:99`, `:109`; `scripts/dev/_frontend_gate_layout.py:27`; `static/css/tailwind.css:7`, `static/css/tailwind.src.css:24` (the WIP patch); `static/js/heatmap.js:615`; `tests/scripts/dev/test_tailwind_build_cli.py:163`. Leave, by ruling: `docs/design/README.md:89`, `:98`, `docs/design/reference/design-system-readme.md:40`, `docs/design/tokens/fonts.css:15`, `docs/design/tokens/typography.css:4`, `:15` (verbatim snapshot, R12; RECONCILIATION records the override); `tests/scripts/dev/test_frontend_gate_figures.py:19`, `:110` (a sample of a wrong, non-figure face; any serif stack serves); every point-in-time hit.

- [x] **Step 1: Edit the token lock test (red first).** In `test_theme_source_locks_the_batch_21_design_tokens`, replace the line `'--font-serif: "instrument-serif", "corporate-a", Georgia, serif;',` with `'--font-serif: "orpheuspro", "instrument-serif", "corporate-a", Georgia, serif;',`.

- [x] **Step 2: Add the kit-coverage test** to `tests/scripts/dev/test_frontend_gate_layout.py` (add `import re` and `from pathlib import Path` if absent; import `REQUIRED_FONT_FAMILIES` from `scripts.dev._frontend_gate_layout`):

```python
SOURCE_CSS = Path(__file__).resolve().parents[3] / "static" / "css" / "tailwind.src.css"


def test_the_kit_check_loads_the_first_face_of_every_font_token() -> None:
    """Every --font-* token's first family is one check_fonts asks the kit for.

    check_fonts can only warn about a family it loads. A token whose primary
    face is missing from REQUIRED_FONT_FAMILIES renders in its fallback with
    no warning at all -- which is what a new display serif would do if the
    list kept naming only the old one.
    """
    source = SOURCE_CSS.read_text(encoding="utf-8")
    first_faces = re.findall(r'--font-[a-z-]+:\s*"([^"]+)"', source)
    assert len(first_faces) == 5, first_faces
    assert sorted(set(first_faces) - set(REQUIRED_FONT_FAMILIES)) == []
```

(Check `parents[3]` resolves to the repository root; the five tokens are `--font-sans`, `--font-serif`, `--font-figure`, `--font-mono`, `--font-mono-narrow`; `--font-weight-*` values are unquoted and do not match.)

- [x] **Step 3: Extend the export header check.** In `check_heatmap_export_header_matches_page`, the `page.evaluate` also returns the page headline's computed family and the drawn headline's family with the leading size dropped:

```js
pageHeadlineFont: headline ? getComputedStyle(headline).fontFamily : null,
drawnHeadlineFont: model?.headlineFont
    ? model.headlineFont.replace(/^\s*[\d.]+px\s+/, '') : null,
```

and, in the same module, a pure judge (unit-tested, so the check stays a thin reader):

```python
def _plain_family(value: str | None) -> str:
    """A font-family list with quotes and spaces removed, for comparison."""
    return (value or "").replace('"', "").replace("'", "").replace(" ", "")


def headline_font_failures(drawn: str | None, page_family: str | None) -> list[str]:
    """Judge the saved image's headline family against the page headline's.

    The canvas names its font in a string of its own, so it kept drawing
    Instrument Serif after the page moved to Orpheus Pro (2026-10-22).
    """
    if not drawn:
        return ["saved heatmap header records no headline font"]
    if _plain_family(drawn) != _plain_family(page_family):
        return [
            f"saved heatmap headline is set in {drawn!r}, "
            f"the page headline in {page_family!r}"
        ]
    return []
```

The check calls `failures.extend(headline_font_failures(state["drawnHeadlineFont"], state["pageHeadlineFont"]))` after the username check.

Add three tests to `tests/scripts/dev/test_frontend_gate_theme.py`: equal families written with different quoting and spacing pass (`headline_font_failures('"orpheuspro", Georgia, serif', "orpheuspro,Georgia,serif") == []`); a different family is reported with both names; a missing drawn font (`None` and `""`) is reported.

- [x] **Step 4: Prove red.** Run `PY -m pytest -q tests/scripts/dev/test_tailwind_build_cli.py tests/scripts/dev/test_frontend_gate_layout.py -p no:cacheprovider`: expect the token lock test FAIL (the source still has the old line) and the kit-coverage test PASS (at BASE, instrument-serif is listed). Run the `frontend-gate` (through the wrapper): expect `check_heatmap_export_header_matches_page` to fail with "saved heatmap header records no headline font" at each profile it runs. Quote the lines.

- [x] **Step 5: Apply the WIP patch.** `git apply .superpowers/sdd/2026-10-22-ui-round-2/task-1-wip.patch` (absolute path from the code-phase worktree). Re-run the two pytest files: the token lock test PASSES and the kit-coverage test now FAILS (`['orpheuspro']` missing). Quote it.

- [x] **Step 6: Add the family to the kit check.** In `REQUIRED_FONT_FAMILIES`, insert `"orpheuspro",` directly before `"instrument-serif",` (keep `akzidenz-grotesk-next-pro` first: `check_body_font` reads index 0; keep `instrument-serif`: it is still the serif's fallback, and its loss should still warn). Re-run: both PASS.

- [x] **Step 7: Make the export follow the token.** In `static/js/heatmap.js`, where the export draws the headline, replace `ctx.font = '26px "instrument-serif", Georgia, serif';` with:

```js
    // The page's display serif, read from its token, so the saved image
    // follows the page instead of naming a family of its own (it drew
    // Instrument Serif after the page moved to Orpheus Pro, 2026-10-22).
    ctx.font = '26px ' + getComputedStyle(document.documentElement)
      .getPropertyValue('--font-serif').trim();
    var headlineFont = ctx.font;
```

and record it: `drawnHeader = { headline: header.headline, eyebrow: header.eyebrow, headlineFont: headlineFont };`. Run the `frontend-gate`: PASS. Planted defects, each run through the gate and reverted from a copy: (a) the old hard-coded string back -> the check fails naming `instrument-serif` against `orpheuspro`; (b) `ctx.font = '26px ' + ''` (an invalid font the canvas ignores) -> fails; (c) `headlineFont` dropped from `drawnHeader` -> "records no headline font".

- [x] **Step 8: Docs (R12).**
  - `DESIGN.md` frontmatter: `display` and `headline` `fontFamily: "orpheuspro, instrument-serif, Georgia, serif"`; `display` `letterSpacing: "0"`.
  - `DESIGN.md` Typography: `**Display Font:** \`orpheuspro\` (Orpheus Pro; \`instrument-serif\`, then Georgia, serif, as fallback)`. Hierarchy: Display reads `(400 weight, \`2rem\` to \`3rem\`, line-height \`1.05\`, tracking \`0\`; the empty-state titles keep \`-0.01em\`): Editorial hero phrases and main page banners (\`orpheuspro\`).`; Headline ends `(\`orpheuspro\`).` Role Segregation Rule: "Gotham gets the numbers, Orpheus Pro gets the words." Do's: "**Do** use \`orpheuspro\` strictly for display words and \`gotham\` strictly for display numbers."
  - `docs/design/RECONCILIATION.md`: the role-map row becomes `| \`--font-serif\` | orpheuspro, then instrument-serif | display words, 22px+ | orpheuspro 400 / 700 + italic 400; instrument-serif 400 + italic |`, and a new section `## 27. Orpheus Pro is the display serif, 2026-10-22` after section 26: the owner's words (I1 ruling above), the token, the hero's tracking 0, the export headline reading the token, and that `README.md`'s "Gotham gets the numbers, Instrument Serif gets the words" is overridden here. Section 27 also says the type mapping now departs from the snapshot README. In section 4 ("The type mapping"), the sentence "The repo takes the README families unchanged." becomes "The repo takes the README families, with one change: Orpheus Pro leads the serif token (section 27).".
  - `README.md` Typography row: `Adobe Fonts: Akzidenz-Grotesk Next, Orpheus Pro (Instrument Serif as its fallback), Gotham, Input Mono, Input Mono Narrow`.
  - `docs/agents/AGENT_NOTES.md`: "never Instrument Serif or any Adobe kit family" -> "never Orpheus Pro, Instrument Serif or any Adobe kit family"; "The owner accepts the Instrument Serif hero layout as AI-flavoured but fine" -> "The owner accepts the serif hero layout (Instrument Serif until 2026-10-22, Orpheus Pro since) as AI-flavoured but fine".

- [x] **Step 9:** Landing: Section 4 entry `### 2026-10-23 - Orpheus Pro becomes the display serif` (edited existing tests: `test_theme_source_locks_the_batch_21_design_tokens`); commit procedure with `frontend-gate`; message `feat(ui): Make Orpheus Pro the display serif`.

---

### Task 2: Results stat values take the figure face (S1)

Wave 2, code phase in `C:/ssw/u2` with Task 1's and Task 4's patches staged, then landing after Tasks 1 and 4.

**Touches:**
- `templates/results.html` (the four stat values only; from `task-2-wip.patch`, applied with `git apply -3`: Task 4 changes the "view breakdown" context line of its hunk), `static/css/results.css` (from `task-2-wip.patch`)
- `scripts/dev/_frontend_gate_figures.py`
- `tests/scripts/dev/test_frontend_gate_figures.py` (new tests, and the `_Page` fake)
- `DESIGN.md` (Role Segregation Rule, Do's), `docs/design/RECONCILIATION.md`

**Interfaces:**
- Consumes: Task 1's Role Segregation Rule sentence "Gotham gets the numbers, Orpheus Pro gets the words." and RECONCILIATION section 27.
- Produces: `stat_value_face_failures(stats: dict, kpi: dict) -> list[str]` and `STAT_VALUES_SELECTOR = ".results-stat-value > span"` in `_frontend_gate_figures.py`.

Sweeper hits: `docs/design/RECONCILIATION.md` section 26's deferral sentence (left as written; section 28 completes it); DESIGN.md Role Segregation Rule and Do's line (after Task 1's wording).

- [x] **Step 1: Write the judge's tests** in `tests/scripts/dev/test_frontend_gate_figures.py` (reuse its `FIGURE`, `SERIF` and `_reading`):

```python
def test_four_figure_face_stat_values_pass() -> None:
    assert figures.stat_value_face_failures(_reading(count=4), _reading()) == []


def test_a_serif_stat_value_is_reported_by_its_position() -> None:
    stats = _reading(count=4)
    stats["faces"][1] = {"family": SERIF, "weight": "400"}  # the top artist
    failures = figures.stat_value_face_failures(stats, _reading())
    assert len(failures) == 1
    assert "stat value 2" in failures[0] and "instrument-serif" in failures[0]


def test_a_bold_stat_value_is_reported() -> None:
    stats = _reading(count=4)
    stats["faces"][3] = {"family": FIGURE, "weight": "700"}
    failures = figures.stat_value_face_failures(stats, _reading())
    assert failures == [
        f"results stat value 4 is set in {FIGURE!r} at weight 700, "
        f"expected {FIGURE!r} at weight 400"
    ]


def test_a_stat_row_missing_a_value_is_reported() -> None:
    failures = figures.stat_value_face_failures(_reading(count=3), _reading())
    assert failures == ["results stat row renders 3 values, expected 4"]


def test_stat_values_are_not_passed_against_a_reference_off_the_token() -> None:
    kpi = _reading()
    kpi["faces"] = [{"family": SERIF, "weight": "400"}]
    failures = figures.stat_value_face_failures(_reading(family=SERIF, count=4), kpi)
    assert len(failures) == 1 and "heatmap KPI value" in failures[0]
```

One check-level test, so the stat read is wired into the check and not only judged in isolation:

```python
def test_a_serif_stat_value_fails_the_whole_check() -> None:
    """The stat read is wired into the check, not only judged in isolation."""
    stats = _reading(count=4)
    stats["faces"][1] = {"family": SERIF, "weight": "400"}
    page = _Page(_reading(), [_reading(), _reading()], stats=stats)
    failures = figures.check_results_play_count_uses_the_figure_face(page, "http://gate")
    assert any("results stat value 2" in failure for failure in failures)
```

(Adapt the `_Page(...)` call to how the file's existing check-level tests build one -- the play readings list, any `fit` -- and say so in the report; the assertion stays. Its red: before the call is wired in, `failures` holds no stat line.)

Run them: FAIL (`AttributeError: ... stat_value_face_failures`). Quote it.

- [x] **Step 2: Write the judge.** Factor the reference check out of `figure_face_failures` into `_reference_failures(kpi: dict) -> list[str]` (the "no KPI value" and "heatmap KPI value is set in ..." messages, unchanged), call it from `figure_face_failures` (its tests stay green), and add:

```python
#: The four Results stat values: total albums, top artist, scrobbles, unmatched.
STAT_VALUES_SELECTOR = ".results-stat-value > span"
STAT_VALUE_COUNT = 4


def stat_value_face_failures(stats: dict, kpi: dict) -> list[str]:
    """Judge the Results stat row, a `FACE_JS` reading, against the KPI one.

    The owner's live pick (2026-10-22): every stat value, the top artist's
    name included, is set like a heatmap KPI value -- the figure face at
    Book weight.
    """
    failures = _reference_failures(kpi)
    if failures:
        return failures
    if len(stats["faces"]) != STAT_VALUE_COUNT:
        return [
            f"results stat row renders {len(stats['faces'])} values, "
            f"expected {STAT_VALUE_COUNT}"
        ]
    reference = kpi["faces"][0]
    return [
        f"results stat value {position} is set in {face['family']!r} at weight "
        f"{face['weight']}, expected {reference['family']!r} at weight {FIGURE_WEIGHT}"
        for position, face in enumerate(stats["faces"], 1)
        if face["family"] != reference["family"] or face["weight"] != FIGURE_WEIGHT
    ]
```

Call it in `check_results_play_count_uses_the_figure_face` right after the "on load" play-count reading: `failures.extend(stat_value_face_failures(page.evaluate(FACE_JS, [STAT_VALUES_SELECTOR, FIGURE_FONT_PROPERTY]), kpi))`. Update the module and check docstrings to say the check also reads the stat row (the registered name "results play count figure face" and the function name stay, so no registration test changes). Unit tests PASS.

- [x] **Step 2a: Teach the `_Page` fake the stat read.** Give the `_Page` fake in `tests/scripts/dev/test_frontend_gate_figures.py` a `stats` constructor argument (default `_reading(count=4)`) that its `evaluate` returns when the selector is `figures.STAT_VALUES_SELECTOR`, before the play-reading branch. Run the file: the four tests that failed for the stat read (`test_the_check_passes_when_both_reads_agree_and_cleans_up`, `test_a_cell_rebuilt_by_a_sort_switch_is_judged_again`, `test_at_the_mobile_profile_a_spilling_count_fails_on_load_and_after_a_switch`, `test_at_a_desktop_width_the_fit_is_not_judged`) pass again with no edit to their own bodies.

- [x] **Step 3: Prove the gate red.** Run the `frontend-gate` without the WIP patch: the check fails at each profile with four "results stat value N is set in 'orpheuspro,...' " lines. Quote one profile's lines.

- [x] **Step 4: Apply the WIP patch** with `git apply -3 .superpowers/sdd/2026-10-22-ui-round-2/task-2-wip.patch`. Run the `frontend-gate`: PASS. Planted defects through the gate, each reverted from a copy: (a) an inline `style="font-family: var(--font-serif)"` on `#stat-top-artist` -> one failure naming stat value 2; (b) `font-weight: var(--font-weight-bold)` in the `.results-stat-value > span` rule -> four weight-700 failures; (c) the `font-family` declaration deleted from the `.results-stat-value > span` rule -> four failures.

- [x] **Step 5: Docs (R12).** `DESIGN.md` Role Segregation Rule: after "Gotham gets the numbers, Orpheus Pro gets the words." add "One exception, the owner's choice (2026-10-22): the Results stat row sets all four values in Gotham Book with tabular figures, the Top Artist name included, so the row reads as one set of readouts." Do's line: append "(the Results stat row's Top Artist name is the one exception)". `docs/design/RECONCILIATION.md`: new section `## 28. The Results stat row is all figure face, 2026-10-22` after section 27: the owner's words ("For each span||stat, use Gotham Book."), the rule in `static/css/results.css` (`.results-stat-value > span`: `--font-figure`, `--font-weight-normal`, tabular figures, size unchanged), that it overrides the snapshot's serif stat values, and that it carries out the move section 26 deferred ("The side rail's stat values are still serif utility classes ... belongs to a later round"); section 26 itself stays as written (a dated record).

- [x] **Step 6:** Landing: Section 4 entry `### 2026-10-23 - Results stat values take the figure face` (edited existing tests: the `_Page` fake in `tests/scripts/dev/test_frontend_gate_figures.py` (answers the stat selector); no test body changed); commit procedure with `frontend-gate` and `results-behavior`; message `feat(ui): Set the Results stat values in the figure face`.

---

### Task 3: The heatmap copy says what the grid draws (H2, H4)

Wave 1, code phase in `C:/ssw/u3`, then landing.

**Touches:**
- `templates/index.html` (heatmap-mode lede), `templates/partials/_heatmap_form.html` (preview card), `static/css/heatmap.css` (from `task-3-wip.patch`)
- `tests/frontend/test_heatmap_pure_functions.py` (new tests only)

**Interfaces:**
- Produces: module helpers `_text(fragment: str) -> str`, `_heatmap_lede() -> str` and `_preview_text() -> str` in `tests/frontend/test_heatmap_pure_functions.py` (Task 5 adds tests to the same file and does not use them).

Verified fact: in `static/js/heatmap.js` (`rocketColor`, `countToNorm`) more plays render BRIGHTER (cream-gold), fewer near-black, zero days `--heatmap-empty`; the old lede ("The darker the square, the more you played") and preview ("darker means more") were backwards.

- [x] **Step 1: Write the tests** (add `import re`; `REPO_ROOT` comes from `tests.frontend.conftest`):

```python
INDEX_HTML = REPO_ROOT / "templates" / "index.html"
HEATMAP_FORM_HTML = REPO_ROOT / "templates" / "partials" / "_heatmap_form.html"


def _text(fragment: str) -> str:
    """The words of an HTML fragment: tags dropped, whitespace collapsed."""
    return " ".join(re.sub(r"<[^>]+>", " ", fragment).split())


def _heatmap_lede() -> str:
    """The heatmap-mode lede on the index page (the paragraph under its eyebrow)."""
    source = INDEX_HTML.read_text(encoding="utf-8")
    match = re.search(
        r'Listening heatmap</p>\s*<p class="index-hero__lede">(.*?)</p>', source, re.S
    )
    assert match, "index.html has no heatmap-mode lede under its eyebrow"
    return _text(match.group(1))


def _preview_text() -> str:
    """The words of the heatmap mode's preview card, up to its ramp."""
    source = HEATMAP_FORM_HTML.read_text(encoding="utf-8")
    match = re.search(r'<div class="hm-preview">(.*?)<span class="hm-preview__ramp"', source, re.S)
    assert match, "_heatmap_form.html has no preview card"
    return _text(match.group(1))


#: Relative luminance (WCAG) of the colour the grid gives a quiet day and of
#: the window's busiest day.
SHADE_LUMINANCE_JS = """([quiet, busiest]) => {
    const hooks = window.__scrobbleHeatmapTestHooks;
    const luminance = (css) => {
        const [r, g, b] = css.match(/\\d+/g).map(Number).map((v) => v / 255)
            .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    return [quiet, busiest].map((n) => luminance(hooks.rocketColor(hooks.countToNorm(n, busiest))));
}"""


def test_the_heatmap_copy_names_the_shade_the_grid_draws(js_page):
    """
    GIVEN the colours the grid gives a quiet day and the window's busiest day
    WHEN the index lede and the preview card describe the shading
    THEN both name the direction the grid really draws -- "brighter" when the
         busiest day is the lighter colour, "darker" when it is the darker one
         -- and never the opposite word. The old copy said darker meant more
         while rocketColor drew more plays brighter, and nothing caught it.

    Mutation: swap the word in either copy, or reverse ROCKET_STOPS, and this
    fails.
    """
    quiet, busiest = js_page.evaluate(SHADE_LUMINANCE_JS, [1, 100])
    assert quiet != busiest
    true_word, false_word = ("brighter", "darker") if busiest > quiet else ("darker", "brighter")
    for name, copy in (("heatmap lede", _heatmap_lede()), ("preview card", _preview_text())):
        assert true_word in copy.lower(), f"{name} does not say {true_word}: {copy!r}"
        assert false_word not in copy.lower(), f"{name} says {false_word}: {copy!r}"


def test_the_preview_card_promises_only_figures_the_result_shows(js_page):
    """
    GIVEN the KPI labels a heatmap result renders
    WHEN the mode's preview card says what a run produces
    THEN it names each of them, and no streak the result does not show (the
         old card promised a longest streak; the result shows the current one).
    """
    labels = [
        block["label"].lower()
        for block in js_page.evaluate(RENDER_KPIS_JS, _published(KPI_CASES[0]))
    ]
    preview = _preview_text().lower()
    assert labels, "the KPI row rendered no blocks"
    assert [label for label in labels if label not in preview] == []
    assert "longest" not in preview
```

(Place them after `test_kpi_blocks_render_the_published_figures_and_compute_nothing`, so `RENDER_KPIS_JS`, `_published` and `KPI_CASES` are defined above them. Check the lede regex against the real markup and adjust only the pattern if the eyebrow markup differs; say so in the report.)

- [x] **Step 2: Prove red.** `PY -m pytest -q tests/frontend/test_heatmap_pure_functions.py -k "shade_the_grid or promises_only" -p no:cacheprovider`: both FAIL against BASE (the lede and preview say "darker"; the preview lacks "current streak" and says "longest"). Quote the lines.

- [x] **Step 3: Apply the WIP patch** `task-3-wip.patch`. Re-run: both PASS. Planted defects, each reverted from a copy: (a) the preview's "Brighter squares" -> "Darker squares"; (b) the lede's "brighter for more plays" -> "darker for more plays"; (c) `ROCKET_STOPS` reversed in `static/js/heatmap.js` (temporary; the file is not in this task's Touches and must be byte-identical afterwards); (d) "current streak" -> "longest streak" in the Totals line; (e) "daily average" dropped from the Totals line. Each must fail one of the two tests.

- [x] **Step 4:** Landing: Section 4 entry `### 2026-10-23 - The heatmap copy says what the grid draws` (edited existing tests: none); commit procedure with `frontend-gate`; message `feat(ui): Rewrite the heatmap preview and lede to match the grid`.

---

### Task 4: The unmatched-report links lose their arrows (S2)

Wave 1, code phase in `C:/ssw/u4`, then landing.

**Touches:** `templates/results.html` (the two links to the unmatched report only), `tests/test_routes.py` (one new test).

**Interfaces:** Produces the link texts "view breakdown" and "Open unmatched report" (Task 2's WIP hunk carries the first one as a context line).

Sweeper hits (live): `templates/results.html:104` (`view breakdown →`), `templates/results.html:396` (`Open unmatched report →`). No doc or test quotes either text.

- [x] **Step 1: Write the test** in `tests/test_routes.py`, next to the other `_render_results` tests:

```python
def test_results_links_to_the_unmatched_report_read_as_words_alone(client):
    """
    GIVEN a completed album job
    WHEN the results page renders
    THEN its two links to the unmatched report -- under the Unmatched figure
         and in the side rail -- read "view breakdown" and "Open unmatched
         report", with no arrow glyph or entity after them (owner,
         2026-10-22: "The arrows should go").
    """
    page = _render_results(client, [_provider_row("spotify")])
    # The site header links to the unmatched report on every page; only the
    # Results page's own two links are under test.
    body = page.split("</header>", 1)[1]
    links = re.findall(r'<a [^>]*href="/unmatched"[^>]*>(.*?)</a>', body, re.S)
    texts = [" ".join(re.sub(r"<[^>]+>", " ", text).split()) for text in links]
    assert texts == ["view breakdown", "Open unmatched report"]
```

(Check that `url_for('main.unmatched_page')` renders `href="/unmatched"`; if it carries a query string, match `href="/unmatched[^"]*"` and say so. `templates/base.html` closes its site header with the only `</header>` on the page; check that is still true.)

- [x] **Step 2: Prove red.** `PY -m pytest -q tests/test_routes.py -k read_as_words_alone -p no:cacheprovider`: FAIL (`['view breakdown →', 'Open unmatched report →']`). Quote it.

- [x] **Step 3: Remove the arrows.** `templates/results.html`: `view breakdown →</a>` -> `view breakdown</a>`; the side-rail link's text `Open unmatched report →` -> `Open unmatched report`. Re-run: PASS. Planted defects, each reverted: (a) `&rarr;` after either text; (b) the arrow in its own `<span aria-hidden="true">` -> both fail.

- [x] **Step 4:** Landing: Section 4 entry `### 2026-10-23 - The unmatched-report links lose their arrows` (edited existing tests: none); commit procedure with `frontend-gate` and `results-behavior`; message `feat(ui): Drop the arrows from the unmatched-report links`.

---

### Task 5: A finished run opens its results without a second line (L1)

Wave 2, code phase in `C:/ssw/u5` with Task 3's patch staged, then landing after Task 3.

**Touches:** `static/js/loading.js` (`scheduleResultsRedirect` and its success-path call), `tests/frontend/test_heatmap_pure_functions.py` (new tests; the existing `test_a_failed_album_run_is_announced_once_by_the_alert` reads its markup from the new shared constant).

**Interfaces:** Consumes nothing from Task 3; its patch is staged only because both edit the same test module.

Sweeper hits (live): `static/js/loading.js:186`. `docs/design/designsystemaudit.md:984` is a dated audit (point-in-time): leave it.

- [x] **Step 1: Share the markup.** Move the album loading markup string out of `test_a_failed_album_run_is_announced_once_by_the_alert` into a module constant `ALBUM_LOADING_MARKUP` above it, unchanged, and pass the constant to `page.set_content` (an edit of an existing test: name it in the report and the Section 4 entry). Add:

```python
def _run_album_loading(js_browser, answer):
    """Run loading.js against one /progress answer with timers recorded, not run.

    Returns the details line, the phase line and the delays loading.js asked
    for. Recording setTimeout keeps the redirect from navigating away and
    shows the reading delay it scheduled.
    """
    page = js_browser.new_page()
    try:
        page.set_content(ALBUM_LOADING_MARKUP)
        page.evaluate(
            """(answer) => {
              window.SCROBBLE = {job_id: 'abc'};
              window.__delays = [];
              window.setTimeout = (fn, ms) => { window.__delays.push(ms); return 0; };
              window.fetch = () => Promise.resolve({json: () => Promise.resolve(answer)});
            }""",
            answer,
        )
        page.add_script_tag(path=str(LOADING_PROGRESS_JS))
        page.add_script_tag(path=str(LOADING_JS))
        page.wait_for_function("() => window.__delays.includes(3000)", timeout=5000)
        return (
            page.locator("#step-details").text_content(),
            page.locator("#step-text").text_content(),
            page.evaluate("() => window.__delays"),
        )
    finally:
        page.close()


def test_a_finished_album_run_opens_its_results_without_a_second_line(js_browser):
    """
    GIVEN a /progress answer for a finished run (100%, no error)
    WHEN loading.js renders it
    THEN the phase line says the run is done, the details line under it stays
         empty -- "Opening your results..." repeated what the phase line says
         (owner, 2026-10-22) -- and the results page still opens after the
         three-second reading delay.
    """
    done = "Done! Found 21 albums matching your criteria."
    details, phase, delays = _run_album_loading(
        js_browser, {"progress": 100, "message": done}
    )
    assert details == ""
    assert phase == done
    assert 3000 in delays


def test_a_failed_run_with_no_retry_still_says_the_results_page_opens(js_browser):
    """
    GIVEN a /progress answer for a failure that cannot be retried
    WHEN loading.js renders it
    THEN the details line still says the results page is opening, and the
         redirect waits the same three seconds: only the finished run's line
         was redundant.
    """
    details, _, delays = _run_album_loading(
        js_browser,
        {"error": True, "retryable": False, "progress": 40, "message": "Last.fm failed."},
    )
    assert details == "Opening the results page\u2026"
    assert 3000 in delays
```

(Check how `loading-progress.js` renders a payload without a `phase` key; if the phase line does not take the message, assert what the page really shows a reader for a finished run and say so in the report. Do not stub `ScrobbleProgress`.)

- [x] **Step 2: Prove red.** `PY -m pytest -q tests/frontend/test_heatmap_pure_functions.py -k "album_run or failed_run" -p no:cacheprovider`: the finished-run test FAILS (`'Opening your results…' == ''`); the no-retry test and the existing alert test PASS. Quote the lines.

- [x] **Step 3: Drop the line.** In `static/js/loading.js`:

```js
/**
 * Keep the three-second reading delay, then open the results page. A message,
 * when given, says why the page is moving on.
 */
function scheduleResultsRedirect(message) {
  if (message && stepDetails) stepDetails.textContent = message;
  setTimeout(redirectToResults, 3000);
}
```

and on the success path, replace `if (!errorDetected) scheduleResultsRedirect('Opening your results\u2026');` with:

```js
    // The phase line already says the run is done; a second line saying the
    // results are opening only repeated it (owner, 2026-10-22).
    if (!errorDetected) scheduleResultsRedirect();
```

Re-run: all three PASS. Planted defects, each reverted from a copy: (a) the old success call back -> the finished-run test fails; (b) `scheduleResultsRedirect` ignores its message -> the no-retry test fails; (c) the `setTimeout` line dropped -> both new tests fail (the wait times out).

- [x] **Step 4:** Landing: Section 4 entry `### 2026-10-23 - A finished run opens its results without a second line` (edited existing tests: `test_a_failed_album_run_is_announced_once_by_the_alert`, markup moved to `ALBUM_LOADING_MARKUP` unchanged); commit procedure with `frontend-gate`; message `feat(ui): Drop the redundant redirect line from a finished run`.

---

## Dispatch

| Wave | Tasks | Agents at peak |
|---|---|---|
| 0 | Task 0 (serial, MAIN), then its review; push, draft PR | 1 |
| 1 | code phases T1 (`C:/ssw/u1`), T3 (`u3`), T4 (`u4`), all at the Task 0 commit | 3 + their reviews |
| 2 | code phases T2 (`u2`: T1 and T4 patches staged), T5 (`u5`: T3 patch staged) | 2 + reviews |

Landings in MAIN, one at a time: T1, T3, T4, T2, T5. Each landing is followed by a `gate-runner` on the landed commit, then the controller pushes and starts a `ci-watcher`; the PR body's State table and "Validation at this head" are updated in the same step. A code-phase review may overlap the next landing; a gate-runner never overlaps a landing.

## Final checks (controller)

- [ ] `sweeper` at the final head for `instrument-serif`, `darker`, `longest streak`, `Opening your results`, `→` in `templates/`: only the hits this plan leaves by ruling, plus the fallback it keeps on purpose: the `--font-serif` token in `static/css/tailwind.src.css` and `static/css/tailwind.css`, `REQUIRED_FONT_FAMILIES`, `DESIGN.md`'s fallback mentions and the RECONCILIATION row.
- [ ] `gate-runner` ALL_PASS at the final head (every gate).
- [ ] CI green for the final head; `gh pr checks`; the PR stays draft until the owner says otherwise.

## Self-review

- Coverage: I1 -> Task 1; S1 -> Task 2; H2 + H4 -> Task 3; S2 -> Task 4; L1 -> Task 5; the handoff's follow-ups (DESIGN.md Typography and the Role Segregation exception, `REQUIRED_FONT_FAMILIES`, the serif-family and old-copy assertions, the colour-direction test) each sit in a task. The export canvas font is a sweeper find, folded into Task 1 because "This should replace the serif font globally".
- Names used across tasks: `REQUIRED_FONT_FAMILIES`, `drawnHeader.headlineFont`, `stat_value_face_failures`, `_reference_failures`, `STAT_VALUES_SELECTOR`, `ALBUM_LOADING_MARKUP`, `_run_album_loading`.
- Every new test fails against the tree without its change and for at least two other ways of breaking it (the planted defects listed in each task).

## Outcome (2026-10-24)

| Task | Commit | Landing extras |
|---|---|---|
| 0 | `626340e` | none |
| 3 | `a657d6e` | L3-1: the shade clause must say "more", never "fewer" or "less" |
| 4 | `0878dd1` | none |
| 5 | `b7a0722` | L5-1 (ASCII escape); L5-2 (the 3000 ms callback is `window.redirectToResults`); L5-3 (shade-test docstring) |
| 1 | `ff91283` | L1-1 (whole-list font comparison tests); L1-2 (wraps); L1-3 (`document.fonts.ready` awaited before the release-check check's first measurement; cause unproven); L1-4 (two corrections to Task 5's entry) |
| 2 | `e27450b` | L2-1..L2-4 (the DESIGN.md sentence moved to the end of the paragraph; the wrong-count test parametrised over 0, 3 and 5; `_reference_failures(kpi, subject)` owns the empty-KPI message; the serif-stat test asserts the exact line), plus one extra test, `test_stat_values_without_a_heatmap_reference_are_reported` (a planted L2-3 wording defect turned no existing test red); L2-3 also moved the KPI reference check ahead of the "no play count" check in `figure_face_failures` (messages unchanged; with both faults at once the reference one is reported) |
| F-B23-58 | `5858fa9` | filed for the frontend gate's intermittent failures |

### Deviations

- Landing order was T3, T4, T5, T1, T2 (controller ruling: land as accepted, T2 after T1 and T4, T5 after T3), not the plan's T1, T3, T4, T2, T5.
- The owner's untracked plan `docs/superpowers/plans/2026-10-01-f-swe-7-utils-split.md` failed DOC010 in this worktree and was parked outside it for the round's commits (owner ruling 2026-10-23), restored afterwards.
- The sweeper found the heatmap export's hard-coded `instrument-serif`, folded into Task 1.
- F-B23-58 filed for intermittent gate failures.
