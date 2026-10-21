# UI consistency, round 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The Results table's play count is set in the heatmap's figure face (Gotham, weight 400), and a frontend-gate check keeps it there at every gate profile.

**Architecture:** Two tasks on `feat/ui-consistency`, each its own atomic commit. Task 1 is CSS only (one rule in `static/css/results.css`) plus the override record in `docs/design/RECONCILIATION.md`. Task 2 adds a small gate slice, `scripts/dev/_frontend_gate_figures.py`, that reads the computed font of a Results play count and of a heatmap KPI value in a real browser and requires them to match, with its unit tests. The design is `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` ("UI PR (#7)"); the tranche order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` ("P7"). Later rounds come from the owner's annotated screenshots and get their own plans.

**Tech Stack:** hand-written CSS (no Tailwind rebuild: `results.css` is not compiled), Python 3.13, Playwright (Chromium) through `scripts/dev/frontend_gate.py`, pytest, pre-commit, docsync (`scripts/doc_state_sync.py`).

## Global Constraints

- Every commit is atomic and carries its own untagged PLAYBOOK Section 4 entry, placed directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` line (AGENTS.md "Side-Task Handling"). Entry headings are dated the day the commit is made.
- Commit procedure, every commit, in this order (AGENTS.md "Commit Rules"): write the Section 4 entry; `pytest -q` and measure N; `doc_state_sync.py --fix --test-count N` (bare `--fix` when N is unchanged); stage by name, never `git add -A` or `git add .`; `pre-commit run --all-files` and re-stage anything a hook rewrote; `doc_state_sync.py --check` exits 0; commit.
- Commit subject `<type>(<scope>): <Capitalised imperative>`, at most 72 characters; body explains why. No `Co-authored-by` trailer.
- From the linked worktree `C:/ssw/ui`, every Python command uses the primary checkout's interpreter: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"` (and `pre-commit.exe`, `ruff.exe` beside it).
- Markdown is ASCII only (`--`, never an em dash). Cite code by name, not line number.
- New tests assert intended behaviour, not the code as written, and each comes with mutation evidence: the planted defect named and the test shown failing.
- `WT003 feat/ui-consistency` and `WT010` are expected advisories from the `worktree-alignment` hook; the hook still passes.
- Do not push. The controller pushes and opens the PR.
- The plan file itself is the first commit of the branch, made by the controller before Task 1 (tranche master plan, Global Constraints).
- Spec, verbatim: "Round 1, CSS only: the results table's play count uses the figure face (`--font-figure`, Gotham, weight 400 -- never bold, as the heatmap KPI rule records). A frontend-gate check asserts the intended behaviour: the computed font of a results play count equals that of a heatmap KPI value, at every viewport the gate runs."
- Spec, verbatim: "Standing rules: use controls the shipped UI already has; text contrast aims at 7:1 in both themes with 4.5:1 as the floor; mobile is the breakpoint of concern. Template changes wait for #6, which edits the same templates." Round 1 is CSS only, with one controller-ruled exception (Revision 2, 2026-10-20): if Gotham's four digits do not fit the 390px cell at full size, Task 1 Step 5b adds a `data-digits` attribute to the play-count element in `templates/results.html` and `static/js/results.js` (a one-attribute edit that PR #6 will merge around). If they fit, no template and no script is edited.
- `docs/agents/ui-accessibility.md` item 1: font size, line height and any width that holds text stay rem; this plan changes no size. Item 6: assert what the browser computed, in every state a script can reach (here: on load and after the sort is switched, which rebuilds the cell in `results.js`).
- `docs/design/` is a frozen snapshot guarded by `tests/test_design_snapshot.py`; only `docs/design/RECONCILIATION.md` and `docs/design/designsystemaudit.md` are repository-owned. This plan edits `RECONCILIATION.md` only.
- Hosting cost ceiling (spec): nothing here keeps the production database awake, adds a machine or adds a service. Nothing does: CSS and a test-time gate check.
- Browser gates run one at a time on the owner's machine. Run the live probes and the full gate sequentially, never beside another browser run.
- The `BATCH23_DEFINITION.md` amendment for this PR: none. The master plan's "Must cover" for P7 names no amendment, and no Batch 23 work package assumes the Results play count's typeface.

## Assumptions checked against `C:/ssw/kb` (include-unmatched head, 5dde407)

| Assumption (from the dispatch and the master plan) | Held? |
|---|---|
| `static/css/heatmap.css` `.heatmap-kpi-value` sets `font-family: var(--font-figure)`, `font-weight: var(--font-weight-normal)` | Held |
| `static/css/results.css` `.metric-value` carries the play count | Did not hold as named. There is no `.metric-value` rule. The play count is `.metric-val-plays`, a second class on `.metric-value` (`templates/results.html`, and `results.js` `renderMetric` rebuilds it with the same two classes). `.metric-val-plays` is set in `var(--font-serif)` with no `font-weight`, so it inherits |
| The play count is a `<span>` inside `td.metric-value-cell` | Held. Plays mode renders `.metric-val-plays`; playtime mode renders `.metric-val-playtime` (mono-narrow) in the same cell and stays as it is |
| `--font-figure` and `--font-weight-normal` reach the Results page | Held. Both are in the `@theme static` block of `tailwind.src.css`, so they are emitted into `tailwind.css`, which `results.html` loads before `results.css` |
| The gate registry is `config/frontend_gate_checks.toml` and lists the checks | Did not hold. That file holds only `required` and `disabled` name lists. The registry is the `CHECKS` tuple in `scripts/dev/frontend_gate.py`: `(name, function, viewports, group)` |
| "At every profile" | The gate has three profiles in `VIEWPORTS`: `desktop` (1280x720), `mobile` (390x844, touch), `wide touch` (1280x800, touch). Firefox runs only the `STATIC_ASSETS` group as a canary, so a `LAYOUT_PIPELINE` check runs in Chromium only |
| The design wants play counts in the figure face | Held. `DESIGN.md` "Figure Numerals" names play counts and hours listened (`gotham`), and the Role Segregation Rule says Gotham gets the numbers. `docs/design/designsystemaudit.md` first raised D-17 (serif figures on Results) as a question for the owner, then withdrew it ("No ruling needed") after an owner clarification that the Results serif was an intentional aesthetic choice; the spec's UI section (2026-10-20) reverses that clarification |
| The snapshot describes the Results play value | `docs/design/components/data/AlbumRow.d.ts` says "Mono value -- play count". The repository already overrides that (serif); this PR overrides it again, so it is recorded in RECONCILIATION |
| Gate seeding patterns | Held. `jobs.create` plus `jobs.succeed` for a Results list (`check_results_interactions`) and a minimal heatmap result dict (`check_heatmap_export_header_matches_page`) |
| The Results side-rail stat values (`#stat-total-albums`, `#stat-scrobbles`, the unmatched count) are serif utility classes in `results.html` | Held. They are numbers too, but they live in the template, which this PR does not edit (owner question 3) |

Not measured by this plan's author (the fonts come from Adobe Fonts over the network and `C:/ssw/kb` is read-only): whether Gotham as served has tabular figures; whether Gotham's digits fit the mobile metric column; whether weight or face changes a row's height. Task 1 Step 2 measures all three before any CSS changes; a stop rule returns to the controller. Tabular figures are decided by `DESIGN.md` (Figure Numerals are "tabular"), so Task 1 sets `font-variant-numeric: tabular-nums` and only records what the kit does with it. See "Owner questions".

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `static/css/results.css` | `.metric-val-plays` takes the figure face at weight 400 | 1 |
| `docs/design/RECONCILIATION.md` | New section 22 and one row in the Section 1 override table | 1 |
| `scripts/dev/_frontend_gate_figures.py` (new) | The check, its in-page probes and its pure judging functions | 2 |
| `tests/scripts/dev/test_frontend_gate_figures.py` (new) | Unit tests for the judging functions and the check's flow | 2 |
| `scripts/dev/frontend_gate.py` | Import and register the check in `CHECKS` | 2 |
| `.claude/SESSION_CONTEXT.md`, `docs/architecture/documentation-tooling.md`, `DEVELOPMENT.md` | Document the new module | 2 |
| `docs/agents/PLAYBOOK.md` | One Section 4 entry per task | 1, 2 |

---

### Task 1: The Results play count takes the figure face

**Touches:** `static/css/results.css`, `docs/design/RECONCILIATION.md`, `docs/agents/PLAYBOOK.md`; only if Step 5b applies: `templates/results.html`, `static/js/results.js`, `tests/test_routes.py`
**After:** none (branches from `main` once PR #256 has merged)

**Files:**
- Modify: `static/css/results.css` (`.metric-val-plays` and the comment above it)
- Modify: `docs/design/RECONCILIATION.md` (Section 1 table row; new section 22 at the end)
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)
- Only if Step 5b applies: Modify `templates/results.html` (the play-count `<span>`), `static/js/results.js` (`renderMetric`), `tests/test_routes.py` (one new test after `test_results_complete_with_results_renders_data`)
- Scratch only, never committed: `.superpowers/sdd/2026-10-20-ui-consistency-round-1/measure/measure_plays.py` and its outputs

**Interfaces:**
- Consumes: `--font-figure` and `--font-weight-normal` (tokens in `tailwind.src.css`).
- Produces: `.metric-val-plays` computes to the same `font-family` and `font-weight` as `.heatmap-kpi-value`. Task 2's check asserts exactly that.

Why: `DESIGN.md` gives play counts to Gotham, and the heatmap already does; Results sets the same kind of number in the serif. One number, one face. The change is one rule: size, line height, colour and letter-spacing stay, so contrast is unchanged. Four-digit counts are rare, but Gotham's digits are wider than the serif's and the mobile metric column is about 44px wide; the owner's ruling (via the controller, 2026-10-20) is neither to widen the column nor to shrink every row: measure first, and only if four digits do not fit at full size, give rows of four or more digits a smaller size on screens under 768px (Step 5b), leaving every other row and every desktop row at full size.

- [ ] **Step 1: Write the measuring script (scratch, not in the repository)**

Create `.superpowers/sdd/2026-10-20-ui-consistency-round-1/measure/measure_plays.py`. It serves the real app, seeds a Results job, and reports per gate profile: the play counts' computed face and colour, each row's height, how wide each count is against the room its cell gives it, and whether Gotham's digits are tabular.

```python
"""Measure the Results play count at every gate profile.

Scratch tool: lives in the SDD workspace, never in the repository. Run from
the worktree with the primary checkout's interpreter; prints JSON.
"""

import json
import sys

sys.path.insert(0, "C:/ssw/ui")

from scripts.dev import frontend_gate as fg  # noqa: E402
from scrobblescope import jobs  # noqa: E402

# 888888 and 88888 are measured for Step 5b's sizes; 8080, 407 and 12 are the
# values the gate check will seed.
COUNTS = (888888, 88888, 8080, 407, 12)

PROBE = """async () => {
    const loaded = await document.fonts.load('400 24px "gotham"');
    await document.fonts.ready;
    const widthOf = (text, numeric, family = '"gotham", sans-serif') => {
        const probe = document.createElement('span');
        probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;'
            + 'font:400 24px ' + family + ';font-variant-numeric:' + numeric;
        probe.textContent = text;
        document.body.appendChild(probe);
        const width = probe.getBoundingClientRect().width;
        probe.remove();
        return width;
    };
    const sample = 'Hamburgefonstiv 0123456789';
    const gothamWidth = widthOf(sample, 'normal');
    const fallbackWidth = widthOf(sample, 'normal', 'sans-serif');
    // The widest digit's advance, in em, with tabular figures on. All ten are
    // measured because the shrink sizes in Step 5b are derived from the widest.
    const digitEm = Math.max(...'0123456789'.split('').map(
        d => widthOf(d, 'tabular-nums') / 24));
    const plays = [...document.querySelectorAll('.metric-val-plays')];
    return {
        digitEm,
        // document.fonts.check() is true for a family with no declared face,
        // so it proves nothing. Served means: a face was fetched for the
        // family AND text set in it measures differently from the fallback.
        gothamServed: loaded.length > 0 && gothamWidth !== fallbackWidth,
        gothamFacesFetched: loaded.length,
        gothamWidth,
        fallbackWidth,
        tabular: {
            defaultOneVsZero: [widthOf('1111', 'normal'), widthOf('0000', 'normal')],
            tnumOneVsZero: [widthOf('1111', 'tabular-nums'), widthOf('0000', 'tabular-nums')],
        },
        rows: plays.map(node => {
            const style = getComputedStyle(node);
            const cell = node.closest('td');
            const cellStyle = getComputedStyle(cell);
            return {
                text: node.textContent.trim(),
                family: style.fontFamily,
                weight: style.fontWeight,
                size: style.fontSize,
                colour: style.color,
                width: node.getBoundingClientRect().width,
                room: cell.clientWidth - parseFloat(cellStyle.paddingLeft)
                    - parseFloat(cellStyle.paddingRight),
                rowHeight: node.closest('tr').getBoundingClientRect().height,
            };
        }),
    };
}"""

rows = [
    {
        "artist": f"Artist {n}",
        "album": f"Album {n}",
        "play_count": n,
        "play_time_seconds": 60,
        "play_time": "1m",
        "release_date": "2025-01-02",
    }
    for n in COUNTS
]

report = {}
with fg.serve_app() as base_url, fg._load_playwright()() as playwright:
    browser = fg._launch_browser(playwright, "chromium")
    job_id = jobs.create({"username": "gate", "year": 2025, "sort_mode": "playcount"})
    jobs.succeed(job_id, rows, "Done")
    try:
        for name, spec in fg.VIEWPORTS.items():
            context = browser.new_context(**spec)
            page = context.new_page()
            page.set_default_navigation_timeout(fg.NAVIGATION_TIMEOUT_MS)
            fg.install_cdn_routes(page)
            page.route("**/api/artist_spotlight?*", lambda route: route.fulfill(json={}))
            page.goto(f"{base_url}/results?job_id={job_id}", wait_until="load")
            report[name] = {}
            for theme in ("light", "dark"):
                page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
                report[name][theme] = page.evaluate(PROBE)
            context.close()
    finally:
        jobs.delete(job_id)
        browser.close()

print(json.dumps(report, indent=2))
```

- [ ] **Step 2: Measure the unchanged tree, then apply the stop rules**

Run from `C:/ssw/ui`:
`"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" ".superpowers/sdd/2026-10-20-ui-consistency-round-1/measure/measure_plays.py" > ".superpowers/sdd/2026-10-20-ui-consistency-round-1/measure/before.json"`
Expected: exit 0, `before.json` holds `desktop`, `mobile` and `wide touch`, each with `light` and `dark`; every row's `family` starts with `instrument-serif` (or `"instrument-serif"`).

Read `before.json` and apply these rules before editing any CSS:
1. If `gothamServed` is `false` in any profile (no face was fetched for the family, or text set in it measures the same as in the plain `sans-serif` fallback), the Adobe Fonts kit did not serve Gotham (offline, or the kit's domain lock). Every measurement below is then of the fallback face and means nothing. Stop and report `NEEDS_CONTEXT: Gotham not served`, quoting `gothamFacesFetched`, `gothamWidth` and `fallbackWidth`; the controller fixes the network or the kit and re-dispatches.
2. Tabular figures: `DESIGN.md` already decides them (Figure Numerals are "tabular"), so Step 3 sets `font-variant-numeric: tabular-nums` whatever is measured. Record, for the entry only: whether `defaultOneVsZero` widths differ (proportional digits by default) and whether `tnumOneVsZero` widths are then equal (the served face has `tnum`) or still differ (it has none, and the declaration changes nothing).
3. Record the `rowHeight` values and each row's `width` and `room` for the serif face, per profile. These are the baseline Step 5 compares with.

- [ ] **Step 3: Change the rule**

In `static/css/results.css`, replace the comment and the `.metric-val-plays` rule (the `.metric-val-playtime` rule and the `@media (min-width: 768px)` block after it stay exactly as they are):

```css
/* Table metric values: plays use the figure face (Gotham, Book weight --
   the same rule as .heatmap-kpi-value in heatmap.css, "never at bold,
   geometric numerals blob at 700"), playtime keeps mono-narrow. Size, line
   height, colour and spacing are unchanged. Tabular figures keep a
   right-aligned column of counts stacked (DESIGN.md, Figure Numerals).
   docs/design/RECONCILIATION.md
   section 22 records the override of the snapshot's "mono value". */
.metric-val-plays {
    font-family: var(--font-figure);
    font-weight: var(--font-weight-normal);
    font-variant-numeric: tabular-nums;
    font-size: calc(1.40625rem * var(--results-scale));
    line-height: 1.25;
    color: var(--color-base-content);
    letter-spacing: normal;
}
```

- [ ] **Step 4: Record the override in RECONCILIATION**

Add one row to the Section 1 table (after the "Results: unmatched albums" row, keeping the `| Point | README says | This repo does | Why |` shape):

```markdown
| Results: play count face | `AlbumRow.d.ts`: "Mono value -- play count" | The Results table's play count is set in `--font-figure` (Gotham) at weight 400, like a heatmap KPI value; listening time stays mono-narrow | Owner ruling 2026-10-20 (tranche design, "UI PR (#7)"), Section 22 |
```

Append at the end of the file:

```markdown
---

## 22. Frozen-snapshot override: the Results play count is a figure, 2026-10-20

Owner ruling, 2026-10-20 (the pre-Batch-23 tranche design, "UI PR (#7)"): the
Results table's play count uses the figure face, "--font-figure, Gotham,
weight 400 -- never bold, as the heatmap KPI rule records".

The snapshot is frozen, so its words stay as they are and this section
overrides them. `docs/design/components/data/AlbumRow.d.ts` calls the row's
metric a "Mono value -- play count (\"247\") or play time (\"18h 42m\")".
Before this ruling the repository set the play count in the serif.
`docs/design/designsystemaudit.md` first asked for an owner ruling on that
(D-17), then withdrew the question after an owner clarification that the
Results serif was an intentional aesthetic choice. The 2026-10-20 ruling
reverses that clarification: `DESIGN.md` names play counts among the Figure
Numerals, and "Gotham gets the numbers". So `.metric-val-plays` takes
`--font-figure` at `--font-weight-normal`, as `.heatmap-kpi-value` does, and
sets `font-variant-numeric: tabular-nums` because `DESIGN.md` calls the Figure
Numerals tabular and the column is right-aligned. A frontend
gate check (`check_results_play_count_uses_the_figure_face`) holds the two
equal at every gate profile.

What does not change. Listening time stays `--font-mono-narrow`: it is a
duration, not a magnitude. The line height, colour and letter-spacing of the play count are
untouched, and so is its size on every row at 768px and up and on rows of one
to three digits below it, so its contrast is what it was. The side rail's
stat values are still serif utility classes in `results.html`; moving them is
a template change and belongs to a later round.

*Include the next paragraph, word for word with the measured numbers, only if
Task 1 Step 5b applied.*

**Narrow screens and long counts.** Gotham's digits are wider than the serif's
and the mobile metric column is 3.75rem. Owner direction, 2026-10-20: a
four-digit count is a rare edge case, so the column does not widen and every
row does not shrink. On screens under 768px a play count of four digits is set
at S4 rem, one of five at S5 rem and one of six or more at 0.75rem (the
small-text floor; fit is not promised for them), each derived from the
measured width of Gotham's tabular digits so the count keeps at least 2px
inside its cell. The element carries `data-digits`, rendered by the template
and rebuilt by `results.js` on a sort switch, and the rules are in a
`max-width: 767.98px` media query only. Every other row, and every row at
768px and up, keeps the full size. The gate check holds a four-digit count
inside its cell at the mobile profile.
```

- [ ] **Step 5: Measure again, compare, and apply the stop rules**

Run the Step 2 command with output to `after.json`.
Expected: exit 0; every row's `family` starts with `gotham`, every `weight` is `400`, every `colour` equals the same row's `colour` in `before.json` (the rule never sets colour, so this only confirms nothing else moved; the contrast evidence is the gate's own contrast checks in Step 6), and `size` is equal.

Stop rules (each ends the task with a report, not a guess; the controller takes the question to the owner and re-dispatches):
1. Any `rowHeight` differs from `before.json` by more than 0.5px: `NEEDS_CONTEXT: row height changed`, with the before and after table.
2. A seeded row of one to three digits (407, 12) has `width` greater than `room` at any profile: stop and return `NEEDS_CONTEXT: play count overflows its cell` with the widths; short counts must fit at full size.

The four-digit row (8080) decides Step 5b. Read its `width` and `room` at the `mobile` profile (390px; the cell is 3.75rem wide less 0.5rem of padding on each side, 1rem in all) in `after.json`:
- If `width` is at most `room` minus 2 (it fits at full size with 2px to spare): Step 5b does not apply. Nothing more changes. Record the widths in the entry and go to Step 6.
- Otherwise Step 5b applies.

- [ ] **Step 5b: Only if four digits do not fit at full size -- smaller size for longer counts, mobile only**

Controller ruling (2026-10-20, answering the owner's "a four-digit playcount is a rare occurrence ... what would you judge is best given it is an edge-case?"): neither widen the column nor shrink every row. Rows of four or more digits get a smaller size on screens under 768px only; every other row, and every row at 768px and up, keeps the full size; the column keeps its width.

1. Size each digit count from the measurement. With `d` = the largest `digitEm` in `after.json` and `R` = the `room` (px) of the `mobile` profile, the size for an `n`-digit count is `S(n) = floor((R - 2) / (n * d) / 16, to 3 decimals)` rem. This leaves at least 2px spare. Worked arithmetic with illustrative values, to show the formula and not to be copied: `d = 0.62`, `R = 44` gives `S(4) = 42 / 2.48 / 16 = 1.058` rem and `S(5) = 42 / 3.1 / 16 = 0.846` rem. Use your measured `d` and `R`.
2. Floor: a play count is a figure, not small print, so no size below `0.75rem` (12px, the repository's small-text floor, `docs/design/RECONCILIATION.md` section 1). Counts of six or more digits (100,000 plays of one album) cannot fit the column at a legible size; they take `0.75rem` and the entry says that fit is not promised for them. If `S(4)` or `S(5)` comes out below `0.75rem`, stop and return `NEEDS_CONTEXT: play count digits too wide for the column` with `d` and `R`.
3. `templates/results.html`: give the plays span the digit count, as its last attribute, and leave the playtime span alone:

```html
<span class="metric-value metric-val-plays" data-digits="{{ album.play_count|string|length }}">
```

4. `static/js/results.js`, `renderMetric`: the sort switch rebuilds the cell, so the rebuilt span must carry the attribute too. Replace the single line `value.textContent = row.dataset.playCount || '0';` (inside the existing `else` branch; keep that `else {` and its closing `}`) with the three lines below, shown here inside the branch for context:

```js
        } else {
            const plays = row.dataset.playCount || '0';
            value.textContent = plays;
            value.dataset.digits = String(plays.length);
        }
```

5. `static/css/results.css`, directly after the existing `@media (min-width: 768px)` block that follows `.metric-val-playtime`, add (substituting your S(4), S(5); the `0.75rem` line is the floor):

```css
/* Longer play counts take a smaller figure on narrow screens only, sized from
   the measured width of Gotham's tabular digits so the count keeps at least
   2px inside the 3.75rem metric column. Rows of one to three digits and every
   row at 768px and up keep the full size (RECONCILIATION section 22). */
@media (max-width: 767.98px) {
    .metric-val-plays[data-digits="4"] {
        font-size: calc(S4rem * var(--results-scale));
    }

    .metric-val-plays[data-digits="5"] {
        font-size: calc(S5rem * var(--results-scale));
    }

    .metric-val-plays[data-digits="6"],
    .metric-val-plays[data-digits="7"] {
        font-size: calc(0.75rem * var(--results-scale));
    }
}
```

where `S4rem` and `S5rem` stand for your two computed numbers followed by `rem` (for example `1.058rem`); write the numbers into the file, not the names.

6. Test, in `tests/test_routes.py` after `test_results_complete_with_results_renders_data`:

```python
def test_each_play_count_states_how_many_digits_it_has(client):
    """The narrow-screen sizing keys on the digit count, so a count must
    carry its own length, whatever it is."""
    job_id = jobs.create({"username": "flounder14", "year": 2025, "sort_mode": "playcount"})
    jobs.succeed(
        job_id,
        [
            {"artist": "A", "album": "Four", "play_count": 8080, "play_time": "1m",
             "play_time_seconds": 60, "release_date": "2025-02-07"},
            {"artist": "B", "album": "Three", "play_count": 407, "play_time": "1m",
             "play_time_seconds": 60, "release_date": "2025-02-07"},
        ],
        "Done!",
    )

    html = client.post("/results_complete", data={"job_id": job_id}).get_data(as_text=True)

    assert re.search(r'data-digits="4">\s*8080\s*</span>', html)
    assert re.search(r'data-digits="3">\s*407\s*</span>', html)
```

(`tests/test_routes.py` already imports `re` or the line `import re` is added at its top if not.) Mutation proof (the template edit above is not committed until Step 7, so never restore with `git checkout`, which would revert it to HEAD and discard `data-digits`): first save the edited file with `cp templates/results.html /tmp/results.html.keep`; change the template to `data-digits="4"` literally; the 407 assertion fails. Restore with `cp /tmp/results.html.keep templates/results.html`, then confirm with `git diff --stat templates/results.html` that the diff is non-empty and `grep -c 'data-digits="{{ album.play_count|string|length }}"' templates/results.html` prints 1.

- [ ] **Step 5c: Measure again with Step 5b applied**

Run the Step 2 command with output to `after2.json`. Expected: at `mobile`, the 8080 and 88888 rows have `width` at most `room` minus 2; at `desktop` and `wide touch` every row's `size` and `width` equal `after.json`'s (full size); at `mobile` rows of one to three digits keep the full `size`; every `rowHeight` equals `before.json`'s within 0.5px. Anything else: stop and return the table.

- [ ] **Step 6: Gates that see the page**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/frontend_gate.py`
Expected: last line `[frontend_gate] N checks passed in M runs ...` and exit 0, with the Results contrast, export and interaction checks green. Quote that line in the report. (This is the full gate, about 2.5 minutes; run it alone.)

Run the sweep: `git grep -n "metric-val-plays\|serif values" -- ':!docs/history' ':!docs/logarchive' ':!docs/superpowers'`
Expected: hits only in `static/css/results.css`, `static/js/results.js`, `templates/results.html` (class names, unchanged) and `docs/design/designsystemaudit.md` (a dated register; its D-17 text stays as a point-in-time record, RECONCILIATION section 22 supersedes it). The "serif values" comment above `.results-stat-label` describes the side-rail stats and stays.

- [ ] **Step 7: Section 4 entry, gates, commit**

Entry heading: `### <date> - The Results play count is set in the figure face`. Body: scope (one CSS rule and the override record); owner intent (the tranche design's UI PR, `DESIGN.md` Figure Numerals); what changed; the Step 2 and Step 5 measurements summarised (face, weight, colour equal, row heights, the widest seeded count against its room per profile, the tabular finding, and that `tabular-nums` was set because `DESIGN.md` decides it); whether Step 5b applied and, if so, the measured 888888 width against its room at the 0.75rem floor (it is expected to overshoot; the floor is not a fit), `d`, `R`, S(4), S(5) and the Step 5c table (and that it added a one-attribute template edit by the controller's ruling); deviations (the master plan named `.metric-value`; the rule is `.metric-val-plays`); validation: the quoted frontend-gate line and `pytest -q` N.
Commit: `style(results): Set the play count in the figure face`. (Stage `templates/results.html`, `static/js/results.js` and `tests/test_routes.py` too when Step 5b applied; a new test changes N, so use `--fix --test-count N`.)

---

### Task 2: The gate holds the play count to the heatmap's figure face

**Touches:** `scripts/dev/_frontend_gate_figures.py` (new), `tests/scripts/dev/test_frontend_gate_figures.py` (new), `scripts/dev/frontend_gate.py`, `.claude/SESSION_CONTEXT.md`, `docs/architecture/documentation-tooling.md`, `DEVELOPMENT.md`, `docs/agents/PLAYBOOK.md`
**After:** Task 1 (the check is green only once the CSS, and Step 5b if it applied, has landed; Step 8 plants defects on top of it)

**Files:**
- Create: `scripts/dev/_frontend_gate_figures.py`
- Create: `tests/scripts/dev/test_frontend_gate_figures.py`
- Modify: `scripts/dev/frontend_gate.py` (import list; one `CHECKS` entry)
- Modify: `.claude/SESSION_CONTEXT.md` (Section 3 tree line; Section 4 import lines)
- Modify: `docs/architecture/documentation-tooling.md` (the sibling count and list; the Mermaid block)
- Modify: `DEVELOPMENT.md` (one paragraph in the frontend-gate tour)
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)

**Interfaces:**
- Consumes: `scrobblescope.jobs` (`create`, `succeed`, `delete`); `scripts.dev.frontend_gate` constants `DESKTOP`, `MOBILE`, `TOUCH_WIDE`, `LAYOUT_PIPELINE` for registration; the Task 1 CSS.
- Produces, all in `scripts/dev/_frontend_gate_figures.py`:
  - `FIGURE_TOKEN = "--font-figure"`, `FIGURE_WEIGHT = "400"`, `PLAYS_SELECTOR`, `KPI_SELECTOR`, `FOUR_DIGIT_SELECTOR`, `MOBILE_BELOW_PX = 768`, `FIT_TOLERANCE_PX = 0.5`
  - `FIT_JS` (takes a selector, returns `null` or `{"text": str, "right": float, "limit": float}`: the first match's right edge and the right edge of its cell's content box)
  - `count_fit_failures(reading: dict | None, when: str) -> list[str]`
  - `FACE_JS` (takes `[selector, token]`, returns `{"token": str, "faces": [{"family": str, "weight": str}, ...]}`)
  - `figure_face_failures(plays: dict, kpi: dict, when: str) -> list[str]`
  - `check_results_play_count_uses_the_figure_face(page, base_url: str) -> list[str]`, registered as the `CHECKS` entry `"results play count figure face"`, profiles `(DESKTOP, MOBILE, TOUCH_WIDE)`, group `LAYOUT_PIPELINE`.

Why: nothing enforces which face a number wears. The serif play count shipped beside a Gotham KPI and no check could say so. The check asserts the intended behaviour, that the two are the same face and weight, not that a stylesheet contains a string. It also reads the heatmap value against the `--font-figure` token, so the reference cannot drift to the wrong face together with the play count and still pass. At the mobile profile only (width under 768px) it also requires the seeded four-digit count to keep its right edge inside its cell, on load and after a sort switch: that is the guard for Task 1's narrow-screen sizing (controller ruling, 2026-10-20), narrowly scoped to the one count, and it passes trivially when full size already fits. It runs in Chromium at all three profiles (`LAYOUT_PIPELINE`; Firefox runs only the assets canary), adding 3 planned runs. Computed `font-family` is the declared stack, not the face the browser drew; `check_fonts` already reports, as advisory, a kit family that served no face, and this check does not duplicate it.

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/dev/test_frontend_gate_figures.py`:

```python
"""Behaviour tests for the figure-face slice of the frontend gate.

The intended behaviour: a Results play count is set in the same face and
weight as a heatmap KPI value, and that reference is itself the figure face.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_figures as figures
from scripts.dev import frontend_gate
from tests.scripts.dev.gate_parity import defined_names

CHECK = "check_results_play_count_uses_the_figure_face"
FIGURE = "gotham,ff-din-paneuropean,ui-sans-serif,sans-serif"
SERIF = "instrument-serif,corporate-a,Georgia,serif"


def _reading(family: str = FIGURE, weight: str = "400", count: int = 3) -> dict:
    """A FACE_JS reading of `count` elements, with the token the page defines."""
    return {
        "token": FIGURE,
        "faces": [{"family": family, "weight": weight}] * count,
    }


def test_the_slice_defines_the_check_and_it_is_registered_for_every_profile() -> None:
    assert CHECK in defined_names(figures)
    assert CHECK not in defined_names(frontend_gate)
    entry = next(
        entry for entry in frontend_gate.CHECKS if entry[1] is getattr(figures, CHECK)
    )
    assert entry[0] == "results play count figure face"
    assert set(entry[2]) == {
        frontend_gate.DESKTOP,
        frontend_gate.MOBILE,
        frontend_gate.TOUCH_WIDE,
    }
    assert getattr(frontend_gate, CHECK) is getattr(figures, CHECK)


def test_a_play_count_in_the_kpi_face_and_weight_passes() -> None:
    assert figures.figure_face_failures(_reading(), _reading(count=4), "on load") == []


def test_a_serif_play_count_fails_naming_both_faces() -> None:
    """The defect the change removes: the count still set in the serif."""
    failures = figures.figure_face_failures(
        _reading(family=SERIF), _reading(count=4), "on load"
    )
    assert failures == [
        f"play count on load is set in {SERIF!r}, the heatmap KPI value in {FIGURE!r}"
    ]


def test_a_bold_play_count_fails_even_in_the_right_face() -> None:
    """Gotham is never bold: the kit's 700 blobs the numerals."""
    failures = figures.figure_face_failures(
        _reading(weight="700"), _reading(count=4), "on load"
    )
    assert failures == [
        "play count on load has font weight 700, the heatmap KPI value 400"
    ]


def test_a_reference_that_left_the_figure_face_fails_instead_of_agreeing() -> None:
    """Both elements drifting to the serif together must not pass."""
    failures = figures.figure_face_failures(
        _reading(family=SERIF), _reading(family=SERIF, count=4), "on load"
    )
    assert failures == [
        f"heatmap KPI value is set in {SERIF!r} at weight 400, expected the "
        f"figure face {FIGURE!r} at weight 400"
    ]


def test_a_reference_in_a_bold_weight_fails_instead_of_agreeing() -> None:
    failures = figures.figure_face_failures(
        _reading(weight="700"), _reading(weight="700", count=4), "on load"
    )
    assert len(failures) == 1
    assert failures[0].startswith("heatmap KPI value is set in")


def test_no_kpi_and_no_play_count_each_fail_rather_than_pass_vacuously() -> None:
    """A selector that matches nothing must not read as 'all equal'."""
    nothing = _reading(count=0)
    assert figures.figure_face_failures(_reading(), nothing, "on load") == [
        "heatmap renders no KPI value to compare the play count with"
    ]
    assert figures.figure_face_failures(nothing, _reading(), "on load") == [
        "results table renders no play count on load"
    ]


def test_one_wrong_face_among_many_rows_is_reported_once() -> None:
    plays = {
        "token": FIGURE,
        "faces": [
            {"family": FIGURE, "weight": "400"},
            {"family": SERIF, "weight": "400"},
            {"family": SERIF, "weight": "400"},
        ],
    }
    failures = figures.figure_face_failures(plays, _reading(count=4), "on load")
    assert len(failures) == 1
    assert "instrument-serif" in failures[0]


def test_a_four_digit_count_inside_its_cell_passes() -> None:
    reading = {"text": "8080", "right": 300.0, "limit": 302.0}
    assert figures.count_fit_failures(reading, "on load") == []
    edge = {"text": "8080", "right": 302.4, "limit": 302.0}
    assert figures.count_fit_failures(edge, "on load") == []


def test_a_four_digit_count_past_its_cell_fails_with_the_overshoot() -> None:
    """The defect the narrow-screen sizing prevents: Gotham's digits running
    out of the 3.75rem column into the release date."""
    reading = {"text": "8080", "right": 305.0, "limit": 302.0}
    assert figures.count_fit_failures(reading, "on load") == [
        "play count 8080 on load ends 3.0px past the cell it sits in"
    ]


def test_a_missing_four_digit_count_fails_rather_than_passes() -> None:
    assert figures.count_fit_failures(None, "on load") == [
        "results table renders no four-digit play count on load"
    ]


class _Page:
    """A page stand-in: answers the face probe and records navigation."""

    def __init__(self, kpi, plays, goto_fails=None, width=1280, fit=None):
        self.viewport_size = {"width": width, "height": 800}
        self.fit = fit or {"text": "8080", "right": 300.0, "limit": 302.0}
        self.kpi = kpi
        self.plays = list(plays)
        self.goto_fails = goto_fails
        self.visited = []
        self.clicked = []
        self.routes = []
        self.unrouted = []

    def route(self, pattern, handler):
        self.routes.append(pattern)

    def unroute(self, pattern, handler=None):
        self.unrouted.append(pattern)

    def goto(self, url, **kwargs):
        if self.goto_fails and self.goto_fails in url:
            raise TimeoutError("navigation stalled")
        self.visited.append(url.split("?")[0].rsplit("/", 1)[-1])

    def wait_for_selector(self, selector, **kwargs):
        self.visited.append(f"wait:{selector}")

    def evaluate(self, script, arg=None):
        if script == figures.FACE_JS:
            return self.kpi if arg[0] == figures.KPI_SELECTOR else self.plays.pop(0)
        if script == figures.FIT_JS:
            return self.fit
        return None

    def locator(self, selector):
        node = MagicMock()
        node.click.side_effect = lambda **kwargs: self.clicked.append(selector)
        return node


def _run(page):
    with patch.object(figures, "jobs") as jobs:
        jobs.create.side_effect = ["results-job", "heatmap-job"]
        failures = getattr(figures, CHECK)(page, "http://gate")
    return failures, jobs


def test_the_check_passes_when_both_reads_agree_and_cleans_up() -> None:
    page = _Page(_reading(count=4), [_reading(), _reading()])
    failures, jobs = _run(page)
    assert failures == []
    assert page.visited == [
        "heatmap",
        f"wait:{figures.KPI_SELECTOR}",
        "results",
    ]
    assert page.clicked == ["#toggle-sort-playtime", "#toggle-sort-plays"]
    jobs.delete.assert_any_call("results-job")
    jobs.delete.assert_any_call("heatmap-job")
    assert page.unrouted == page.routes


def test_a_cell_rebuilt_by_a_sort_switch_is_judged_again() -> None:
    """results.js rebuilds the cell on a sort switch; the rebuilt one must
    wear the face too."""
    page = _Page(_reading(count=4), [_reading(), _reading(family=SERIF)])
    failures, _ = _run(page)
    assert failures == [
        f"play count after switching sort is set in {SERIF!r}, "
        f"the heatmap KPI value in {FIGURE!r}"
    ]


_SPILLS = {"text": "8080", "right": 306.0, "limit": 302.0}


def test_at_the_mobile_profile_a_spilling_count_fails_on_load_and_after_a_switch() -> None:
    page = _Page(
        _reading(count=4), [_reading(), _reading()], width=390, fit=_SPILLS
    )
    failures, _ = _run(page)
    assert failures == [
        "play count 8080 on load ends 4.0px past the cell it sits in",
        "play count 8080 after switching sort ends 4.0px past the cell it sits in",
    ]


def test_at_a_desktop_width_the_fit_is_not_judged() -> None:
    """The narrow-screen sizing is mobile only; wide rows keep the full size."""
    page = _Page(
        _reading(count=4), [_reading(), _reading()], width=1280, fit=_SPILLS
    )
    failures, _ = _run(page)
    assert failures == []


def test_both_jobs_are_deleted_even_when_a_page_never_loads() -> None:
    page = _Page(_reading(count=4), [], goto_fails="/results")
    with patch.object(figures, "jobs") as jobs:
        jobs.create.side_effect = ["results-job", "heatmap-job"]
        with pytest.raises(TimeoutError):
            getattr(figures, CHECK)(page, "http://gate")
    jobs.delete.assert_any_call("results-job")
    jobs.delete.assert_any_call("heatmap-job")
```

- [ ] **Step 2: Run the tests; they fail**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest tests/scripts/dev/test_frontend_gate_figures.py -q -p no:cacheprovider`
Expected: collection ERROR, `ImportError: cannot import name '_frontend_gate_figures'`.

- [ ] **Step 3: Write the module**

Create `scripts/dev/_frontend_gate_figures.py`:

```python
"""The Results play count wears the heatmap's figure face.

A slice of the frontend gate (F-B21-51). The design gives numbers to Gotham,
the figure face (`--font-figure`), at Book weight and never bold, and the
heatmap's KPI values wear it. The Results table set its play count in the
serif beside them, and nothing could say so. This check reads what the browser
computed for a play count and for a KPI value, at every gate profile, and
requires the same family and weight. It also reads the KPI value against the
`--font-figure` token, so the pair cannot drift to the wrong face together,
so the pair cannot drift together. At the mobile profile it also requires a
four-digit count to stay inside its cell, the guard for the narrow-screen
sizing in results.css (docs/design/RECONCILIATION.md section 22).

Computed `font-family` is the declared stack, not the face drawn. A kit family
that served no face is `check_fonts`' advisory, not this check's concern.
"""

from __future__ import annotations

from scrobblescope import jobs

#: The token the heatmap KPI value and the play count both resolve through.
FIGURE_TOKEN = "--font-figure"

#: Book. The kit serves 300, 400 and 700; the KPI rule records why not 700.
FIGURE_WEIGHT = "400"

PLAYS_SELECTOR = "#results-table tbody tr .metric-val-plays"
KPI_SELECTOR = ".heatmap-kpi-value"

#: The seeded four-digit count's element, found by the row's own play count so
#: the check does not depend on the `data-digits` hook it guards.
FOUR_DIGIT_SELECTOR = (
    '#results-table tbody tr[data-play-count="8080"] .metric-val-plays'
)

#: Below this window width the Results page is on its narrow-screen layout.
MOBILE_BELOW_PX = 768

#: Sub-pixel rounding in a text box's edge is not an overflow.
FIT_TOLERANCE_PX = 0.5

#: Takes [selector, token]. Quotes and spaces are stripped from the family so
#: a stack compares however the engine spells it.
FACE_JS = """([selector, token]) => {
    const plain = value => value.replaceAll('"', '').replaceAll(' ', '');
    return {
        token: plain(getComputedStyle(document.documentElement)
            .getPropertyValue(token).trim()),
        faces: [...document.querySelectorAll(selector)].map(node => {
            const style = getComputedStyle(node);
            return {family: plain(style.fontFamily), weight: style.fontWeight};
        }),
    };
}"""

#: Play counts to seed: one four-digit count (the edge case the narrow-screen
#: sizing exists for), then shorter ones.
PLAY_COUNTS = (8080, 407, 12)

#: The smallest result the heatmap page renders KPI values from.
_HEATMAP_RESULT = {
    "username": "frontend-gate",
    "from_date": "2025-01-01",
    "to_date": "2025-01-05",
    "total_scrobbles": 4,
    "max_count": 4,
    "daily_counts": {"2025-01-01": 4, "2025-01-02": 0},
}


def figure_face_failures(plays: dict, kpi: dict, when: str) -> list[str]:
    """Judge a play-count reading against a KPI reading, both from `FACE_JS`.

    `when` names the state the play count was read in ("on load", "after
    switching sort"). The KPI value is the reference, so it must itself be the
    figure face at the figure weight.
    """
    if not kpi["faces"]:
        return ["heatmap renders no KPI value to compare the play count with"]
    if not plays["faces"]:
        return [f"results table renders no play count {when}"]
    reference = kpi["faces"][0]
    if reference["family"] != kpi["token"] or reference["weight"] != FIGURE_WEIGHT:
        return [
            f"heatmap KPI value is set in {reference['family']!r} at weight "
            f"{reference['weight']}, expected the figure face {kpi['token']!r} "
            f"at weight {FIGURE_WEIGHT}"
        ]
    failures = []
    seen = set()
    for face in plays["faces"]:
        key = (face["family"], face["weight"])
        if key in seen:
            continue
        seen.add(key)
        if face["family"] != reference["family"]:
            failures.append(
                f"play count {when} is set in {face['family']!r}, "
                f"the heatmap KPI value in {reference['family']!r}"
            )
        if face["weight"] != reference["weight"]:
            failures.append(
                f"play count {when} has font weight {face['weight']}, "
                f"the heatmap KPI value {reference['weight']}"
            )
    return failures


#: Takes a selector; reads the first match's right edge against the right
#: edge of its cell's content box (the cell's padding is room the text may not
#: use).
FIT_JS = """selector => {
    const node = document.querySelector(selector);
    if (!node) return null;
    const cell = node.closest('td');
    const style = getComputedStyle(cell);
    return {
        text: node.textContent.trim(),
        right: node.getBoundingClientRect().right,
        limit: cell.getBoundingClientRect().right
            - Number.parseFloat(style.paddingRight),
    };
}"""


def count_fit_failures(reading: dict | None, when: str) -> list[str]:
    """Judge a `FIT_JS` reading: the count's right edge stays in its cell."""
    if reading is None:
        return [f"results table renders no four-digit play count {when}"]
    overshoot = reading["right"] - reading["limit"]
    if overshoot > FIT_TOLERANCE_PX:
        return [
            f"play count {reading['text']} {when} ends {overshoot:.1f}px past "
            "the cell it sits in"
        ]
    return []


def _results_row(index: int, plays: int) -> dict:
    return {
        "artist": f"Artist {index}",
        "album": f"Album {index}",
        "play_count": plays,
        "play_time_seconds": 60,
        "play_time": "1m",
        "release_date": "2025-01-02",
    }


def check_results_play_count_uses_the_figure_face(page, base_url: str) -> list[str]:
    """A Results play count is set like a heatmap KPI value.

    At the mobile profile the four-digit count must also stay inside its cell.

    Reads the heatmap's KPI value first, then the Results page on load and
    again after the sort is switched to listening time and back, which makes
    results.js rebuild the cell (docs/agents/ui-accessibility.md item 6).
    """
    spotlight = "**/api/artist_spotlight?*"
    results_job = jobs.create(
        {"username": "gate", "year": 2025, "sort_mode": "playcount"}
    )
    heatmap_job = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    try:
        jobs.succeed(
            results_job,
            [_results_row(i, plays) for i, plays in enumerate(PLAY_COUNTS, 1)],
            "Done",
        )
        jobs.succeed(heatmap_job, _HEATMAP_RESULT, "Done")
        page.route(spotlight, lambda route: route.fulfill(json={}))

        page.goto(f"{base_url}/heatmap?job_id={heatmap_job}", wait_until="load")
        page.wait_for_selector(KPI_SELECTOR, state="visible")
        kpi = page.evaluate(FACE_JS, [KPI_SELECTOR, FIGURE_TOKEN])

        page.goto(f"{base_url}/results?job_id={results_job}", wait_until="load")
        page.evaluate("async () => { await document.fonts.ready; }")
        narrow = page.viewport_size["width"] < MOBILE_BELOW_PX
        failures = figure_face_failures(
            page.evaluate(FACE_JS, [PLAYS_SELECTOR, FIGURE_TOKEN]), kpi, "on load"
        )
        if narrow:
            failures.extend(
                count_fit_failures(page.evaluate(FIT_JS, FOUR_DIGIT_SELECTOR), "on load")
            )

        page.locator("#toggle-sort-playtime").click()
        page.locator("#toggle-sort-plays").click()
        failures.extend(
            figure_face_failures(
                page.evaluate(FACE_JS, [PLAYS_SELECTOR, FIGURE_TOKEN]),
                kpi,
                "after switching sort",
            )
        )
        if narrow:
            failures.extend(
                count_fit_failures(
                    page.evaluate(FIT_JS, FOUR_DIGIT_SELECTOR), "after switching sort"
                )
            )
        return failures
    finally:
        try:
            page.unroute(spotlight)
        finally:
            jobs.delete(results_job)
            jobs.delete(heatmap_job)
```

- [ ] **Step 4: Register the check**

In `scripts/dev/frontend_gate.py`, add to the re-export imports, between the `_frontend_gate_colour` block and the `_frontend_gate_forms` block:

```python
from scripts.dev._frontend_gate_figures import (  # noqa: E402, F401
    check_results_play_count_uses_the_figure_face,
)
```

and add to `CHECKS`, directly after the `"results provider attribution"` entry:

```python
    (
        "results play count figure face",
        check_results_play_count_uses_the_figure_face,
        (DESKTOP, MOBILE, TOUCH_WIDE),
        LAYOUT_PIPELINE,
    ),
```

- [ ] **Step 5: Run the unit tests and the split invariants**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest tests/scripts/dev/test_frontend_gate_figures.py tests/scripts/dev/test_frontend_gate_split.py tests/scripts/dev/test_frontend_gate.py tests/scripts/dev/test_frontend_gate_manifest.py -q -p no:cacheprovider`
Expected: all PASS. `test_every_check_in_every_gate_module_is_registered_once` proves the registration. (`test_each_patch_targets_the_module_that_reads_the_name` scans only `patch.object(<gate module>, ...)` and `patch("scripts.dev.X.name")` forms, so it does not scan this file's `patch.object(figures, "jobs")`; the `jobs` name is read inside the check function, which is what makes that patch effective.)

- [ ] **Step 6: Make the scratch tree; mutation evidence, unit level**

Every planted defect in this task, here and in Step 8, goes into a scratch copy of the repository, never into the worktree, so a restore can never leave a defect behind. The new files are not committed yet, so the copy is the last commit plus the working files:

```bash
SCRATCH="C:/ssw/ui-probe"
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
git archive HEAD | tar -x -C "$SCRATCH"
cp scripts/dev/_frontend_gate_figures.py scripts/dev/frontend_gate.py "$SCRATCH/scripts/dev/"
cp tests/scripts/dev/test_frontend_gate_figures.py "$SCRATCH/tests/scripts/dev/"
```

For each row of the table: edit the scratch copy of `scripts/dev/_frontend_gate_figures.py` (`$SCRATCH/scripts/dev/_frontend_gate_figures.py`), run Step 5's first command from inside `$SCRATCH` (`cd "$SCRATCH"` first, then the same pytest command), record the failing test names, then restore the scratch copy with `cp scripts/dev/_frontend_gate_figures.py "$SCRATCH/scripts/dev/"` run from the worktree. Every row must fail; a row that passes means the test does not defend its defect.

| Planted defect | Expected failing test |
|---|---|
| Delete the `face["weight"] != reference["weight"]` branch (weight never compared) | `test_a_bold_play_count_fails_even_in_the_right_face` |
| Delete the `face["family"] != reference["family"]` branch (face never compared) | `test_a_serif_play_count_fails_naming_both_faces`, `test_a_cell_rebuilt_by_a_sort_switch_is_judged_again` |
| Delete the `reference["family"] != kpi["token"] or ...` early return (reference unchecked) | `test_a_reference_that_left_the_figure_face_fails_instead_of_agreeing`, `test_a_reference_in_a_bold_weight_fails_instead_of_agreeing` |
| Delete both `if not ...["faces"]` early returns (empty selection passes) | `test_no_kpi_and_no_play_count_each_fail_rather_than_pass_vacuously` |
| Delete the second `figure_face_failures` call after the sort switch | `test_a_cell_rebuilt_by_a_sort_switch_is_judged_again` |
| Change `>` to `<` in `count_fit_failures` | `test_a_four_digit_count_past_its_cell_fails_with_the_overshoot`, `test_at_the_mobile_profile_a_spilling_count_fails_on_load_and_after_a_switch` |
| Delete the `if narrow:` guards (fit judged at every width) | `test_at_a_desktop_width_the_fit_is_not_judged` |
| Delete the second (`after switching sort`) fit call | `test_at_the_mobile_profile_a_spilling_count_fails_on_load_and_after_a_switch` |
| Delete the `jobs.delete(heatmap_job)` line | `test_both_jobs_are_deleted_even_when_a_page_never_loads` |

- [ ] **Step 7: The check passes live, at every profile**

Create `.superpowers/sdd/2026-10-20-ui-consistency-round-1/measure/probe_figures.py` (scratch workspace file, never committed). It takes the repository root to test as its one argument, so the same script probes the worktree and the scratch tree:

```python
"""Run only the figure-face check at every gate profile, in Chromium."""

import sys

sys.path.insert(0, sys.argv[1])

from scripts.dev import frontend_gate as fg  # noqa: E402

with fg.serve_app() as base_url, fg._load_playwright()() as playwright:
    browser = fg._launch_browser(playwright, "chromium")
    try:
        for name, spec in fg.VIEWPORTS.items():
            context = browser.new_context(**spec)
            page = context.new_page()
            page.set_default_navigation_timeout(fg.NAVIGATION_TIMEOUT_MS)
            fg.install_cdn_routes(page)
            failures = fg.check_results_play_count_uses_the_figure_face(page, base_url)
            print(f"[{name}] {failures if failures else 'PASS'}")
            context.close()
    finally:
        browser.close()
```

Run it against the worktree: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" ".superpowers/sdd/2026-10-20-ui-consistency-round-1/measure/probe_figures.py" C:/ssw/ui`
Expected, three lines: `[desktop] PASS`, `[mobile] PASS`, `[wide touch] PASS`.

- [ ] **Step 8: Live probe, plant the old font, quote the FAIL**

This proves the gate sees the defect in a real browser, not only in the unit tests' stand-in page. All three plantings go into the scratch tree from Step 6 (`$SCRATCH`, whose `static/css/results.css` is the committed Task 1 rule). After each, run the Step 7 command with `C:/ssw/ui-probe` as the argument, quote the output, and restore with `cp static/css/results.css "$SCRATCH/static/css/results.css"` from the worktree. The worktree's CSS is never touched.

1. Old face: in `$SCRATCH/static/css/results.css` change `.metric-val-plays`'s `font-family: var(--font-figure);` to `font-family: var(--font-serif);`.
   Expected, for each of the three profiles, one line of the form `[desktop] ["play count on load is set in 'instrument-serif,corporate-a,Georgia,serif', the heatmap KPI value in 'gotham,ff-din-paneuropean,ui-sans-serif,sans-serif'", "play count after switching sort is set in 'instrument-serif,...", ...]` -- the same failure on load and after switching sort. (The exact spelling of the stack depends on the engine; quote what it printed.)
2. Bold: restore, then change `font-weight: var(--font-weight-normal);` to `font-weight: var(--font-weight-bold);` in the scratch CSS.
   Expected: `play count on load has font weight 700, the heatmap KPI value 400` (and the same after switching sort) at every profile.
3. Long count not shrunk (the guard for Task 1 Step 5b): restore, then in the scratch CSS remove the `.metric-val-plays[data-digits="4"] { ... }` rule. If Step 5b did not apply (four digits fit at full size), plant instead `@media (max-width: 767.98px) { .metric-val-plays { font-size: 2rem; } }` at the end of the scratch CSS.
   Expected: `[mobile]` reports `play count 8080 on load ends N.Npx past the cell it sits in` and the same `after switching sort`; `[desktop]` and `[wide touch]` still PASS. Quote the `[mobile]` line.

Then run the Step 7 command against the worktree once more (`C:/ssw/ui`): three PASS lines. Remove the scratch tree: `rm -rf C:/ssw/ui-probe`. `git status --short` in the worktree must list only this task's intended files.

- [ ] **Step 9: Documentation, same commit**

1. `.claude/SESSION_CONTEXT.md` Section 3 tree: add, after the `_frontend_gate_colour.py` line, `    _frontend_gate_figures.py # Results play count wears the heatmap KPI's figure face; a 4-digit count fits its cell on mobile`. Section 4: add the line `dev/_frontend_gate_figures.py <- jobs` after the `_frontend_gate_colour` line, and add `dev/_frontend_gate_figures` after `dev/_frontend_gate_colour` in the `dev/frontend_gate.py <-` line.
2. `docs/architecture/documentation-tooling.md`: in the "`dev/frontend_gate.py` is the browser gate" paragraph change "across fourteen `_frontend_gate_*` siblings" to "fifteen" and add `` `_frontend_gate_figures`, `` after `` `_frontend_gate_colour`, `` in the list. In the Mermaid block add the line `    FG --> FGFG[_frontend_gate_figures]` after `    FG --> FGSI[_frontend_gate_spotify_icon]`, and add `FGFG` after `FGSI` in the `class D,CLI,...` tool line. The module imports no gate sibling, so it gets no other edge. Validate the block with the Mermaid validator (`mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`, or the repository's validator named in `.github/instructions/mermaid.instructions.md`) before committing, and update the file's "Last verified" date only if the file carries one.
3. `DEVELOPMENT.md`: after the paragraph beginning "`_frontend_gate_spotify_icon.py` adds the official Spotify icon check", add: "`_frontend_gate_figures.py` adds the figure-face check: a Results play count must compute to the same font family and weight as a heatmap KPI value at the desktop, mobile and wide-touch profiles, that value must itself be the `--font-figure` token at weight 400, and at the mobile profile a four-digit count must stay inside its table cell." Do not add machine-checked numbers. (The documentation PR, #8, also edits this file's history; the two edits are in different paragraphs.)
4. Sweep for any other document that enumerates the gate siblings: `git grep -n "_frontend_gate_colour" -- ':!docs/history' ':!docs/logarchive' ':!docs/superpowers'`. Every live document listed must now also name `_frontend_gate_figures`; add it where it does not, and list any point-in-time file left alone.

- [ ] **Step 10: Gates and commit**

Run the full gate once more: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/frontend_gate.py`
Expected: last line `[frontend_gate] N checks passed in M runs ...` where N is one more than before Task 2 and M is three more; exit 0. Quote it.
Entry heading: `### <date> - The gate holds the Results play count to the figure face`. Body: scope; why (the serif count shipped beside a Gotham KPI and nothing could see it); the check's assertions (same family, same weight, the reference is the figure token, the rebuilt cell too); the Step 6 mutation table results; the Step 8 live probe output quoted (the FAIL lines for the old face, the bold weight and the unshrunk long count); that the check runs in Chromium only (Firefox runs the assets canary) and adds 3 planned runs; validation `pytest -q` N and the quoted gate line.
Commit: `test(gate): Check the Results play count wears the figure face`.

---

## Self-Review

1. **Spec coverage.** The play count in `--font-figure` at weight 400, CSS only: Task 1. A gate check that the computed font of a Results play count equals a heatmap KPI value's at every viewport the gate runs: Task 2 (`DESKTOP`, `MOBILE`, `TOUCH_WIDE`, which are all of `VIEWPORTS`). Contrast unchanged: Task 1 Step 6 runs the gate's contrast checks (the rule sets no colour). Live probe with the old font planted and the FAIL quoted: Task 2 Step 8 (all plantings in the scratch tree). Measure nothing you cannot: Task 1 Steps 2 and 5, with stop rules. No gap found.
2. **Placeholder scan.** No TBD or TODO. The conditional paths (the stop rules in Task 1) each name the exact report to send. Entry headings use `<date>` for the commit's own date, which the implementer fills in at commit time as AGENTS.md requires.
3. **Type consistency.** `FACE_JS` returns `{token, faces}` and `figure_face_failures(plays, kpi, when)` reads exactly those keys; the test stand-in `_Page.evaluate` dispatches on `figures.FACE_JS`; the check's name, `check_results_play_count_uses_the_figure_face`, is the same in the module, the registration, the test constant `CHECK` and RECONCILIATION section 22; the registered name `"results play count figure face"` is the one the registration test asserts.
4. **Not measured, stated.** Whether the Adobe kit serves Gotham with tabular figures, whether the digits fit the mobile column, and whether row height moves are unmeasured by the plan's author; Task 1 measures them before any CSS change and stops on the cases that need the owner.

## Owner questions

None remaining. The mobile-column question (formerly 2) was answered by the controller on the owner's instruction on 2026-10-20 and is built into Task 1 Step 5b; tabular figures and the side-rail numbers were withdrawn in Revision 1.

## Revision 1 (2026-10-20)

Findings of `plan-review.md` (verdict Needs fixes, 5 Important) and the controller's rulings, and what changed:

- **Important 1, fit check outside the spec and in conflict with Q2(c).** Removed `FIT_JS`, `cell_fit_failures`, `FIT_TOLERANCE_PX`, their tests, the mutation row and every mention in the module docstring, check docstring and docs text. The check now asserts face and weight only. Overflow is owned by Task 1's measurement: a four-digit count overflowing at the 390px profile is a stop rule that returns to the controller (owner question 2, asked before dispatch).
- **Important 2, restore of an untracked file.** Step 6 now builds a scratch tree with `git archive HEAD` plus the working files at `C:/ssw/ui-probe`, mutates and restores only there (restore by `cp` from the worktree).
- **Important 3, overflow planting that could not fail under fixed layout.** The overflow planting is deleted along with the fit check. Question 2 now records that a width fix must target `th:nth-child(3), td:nth-child(3)` together, after the existing rule. Both remaining live plantings (old face, bold) are made in the scratch tree, never the worktree (controller ruling 2); the probe script takes the repository root as an argument.
- **Important 4, `document.fonts.check` cannot fail.** Task 1's probe now reports `gothamServed`: a face was fetched by `document.fonts.load` AND a sample string set in Gotham measures differently from plain `sans-serif`; the stop rule uses it and quotes the numbers. The check itself uses `wait_until="load"` (Minor 1).
- **Important 5, D-17 misstated.** RECONCILIATION section 22 and the Assumptions table now say the audit raised D-17, withdrew it on an owner clarification that the serif was intentional, and that the 2026-10-20 ruling reverses that clarification.
- **Controller ruling 5, tabular figures.** Decided by `DESIGN.md`: Task 1's rule adds `font-variant-numeric: tabular-nums`, with the measurement recorded only for the entry. Old questions 1 and 3 dropped.
- **Minor 1:** `wait_until="load"` in the check. **Minor 2:** Q2 is asked before dispatch, not "if it happens". **Minor 3:** sweep list no longer names `results_behavior_tests.py`. **Minor 4:** the false claim about the patch-scan test is replaced by what is true. **Minor 5:** the redundant `_Page.route` paragraph is deleted. **Minor 6:** Step 5's colour comparison is described as a no-movement confirmation; contrast evidence is the gate's contrast checks.

## Revision 2 (2026-10-20)

Controller ruling on the former question 2 (owner asked the controller to judge it: "A four-digit playcount is a rare occurence ... what would you judge is best given it is an edge-case?"): neither widen the column nor shrink every row.

- **Task 1** now measures Gotham's widest tabular digit (`digitEm`) in the probe, with six-, five-, four-, three- and two-digit rows. Step 5 branches on the four-digit row at the 390px profile: fits with 2px spare, nothing more changes; otherwise **Step 5b** adds `data-digits="{{ album.play_count|string|length }}"` to the plays span in `templates/results.html`, sets the same attribute in `results.js` `renderMetric` (without it a sort switch would lose the shrink), and adds mobile-only `[data-digits="4"]`, `"5"` and `"6"/"7"` font-size rules inside `@media (max-width: 767.98px)` in `results.css`. The sizes follow the formula `floor((R - 2) / (n * d) / 16)` rem from the measured digit width and room; a `0.75rem` floor stops the task rather than render small print. Desktop and wide-touch rows, and all one- to three-digit rows, keep full size; the column keeps its width. A `tests/test_routes.py` test and its mutation proof cover the template attribute; Step 5c re-measures. The Global Constraints and Task 1's header record the template and script edit as the one exception to "CSS only" (PR #6 edits the same template; the edit is one attribute).
- **Task 2** gains a narrowly scoped fit check: `FIT_JS`, `count_fit_failures`, `FOUR_DIGIT_SELECTOR` (the seeded 8080 row, found by its own `data-play-count`, so the check does not lean on the hook it guards), run only when the window is under 768px, on load and after a sort switch. This reverses Revision 1's removal of the fit assertion, by ruling, but only for this one count at mobile width. New unit tests, three mutation rows, and a third live plant in the scratch tree: remove the `[data-digits="4"]` rule (or, if Step 5b did not apply, force a 2rem mobile size) and quote the `[mobile]` FAIL.
- **RECONCILIATION section 22** records the rule (conditional paragraph, included only when Step 5b applied) and its "what does not change" sentence now says size is untouched on every row at 768px and up and on one- to three-digit rows below it.
- **Owner questions:** Q2 removed (answered); none remain.

## Revision 3 (2026-10-20)

- **Important (plan-rereview-2):** Task 1 Step 5b item 6 mutation proof no longer restores with `git checkout -- templates/results.html` (the template edit is uncommitted until Step 7, so that would discard `data-digits`). It now saves the file with `cp templates/results.html /tmp/results.html.keep`, plants the defect, restores with `cp /tmp/results.html.keep templates/results.html`, and confirms with `git diff --stat templates/results.html` and a `grep -c` for the attribute. No other `git checkout --` restore exists in the plan (Task 2 uses scratch copies).
- **Minor 1:** Step 5b item 4 now says to replace the single line `value.textContent = row.dataset.playCount || '0';` inside the existing `else`, keeping its braces.
- **Minor 2:** Step 7 entry text now records the measured 888888 width against its room at the 0.75rem floor, noting the expected overshoot.
- **Minor 3:** Step 5 padding wording now says 0.5rem on each side, 1rem in all.
