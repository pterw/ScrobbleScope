# UI Round 2 Backlog Follow-Through Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use
> checkbox (`- [ ]`) syntax.

**Goal:** Make the docs, the gates and one finding (F-B23-46) say and hold what PR #269 already
ships, so no shipped UI behaviour is held up by a stale document or an unguarded regression.

**Architecture:** Little new product code: one colour token, the F-B23-46 rule and a one-line note.
Six commits on this branch (`50211a7`, `f2bec89`, `2609f1f`, `4c0c744`, `922700f`, `b6feb13`) changed
the hero, the selected-option look, the form placement, the loading page and one gate floor. This plan
(1) corrects the docs those commits left stale, (2) adds the gates and tests that fail if each shipped
behaviour regresses, (3) strengthens the selected outline so every boundary gate holds 4.5:1 (RA2), and
(4) implements the owner's F-B23-46 rule on both the client and the server path.

**Tech Stack:** Flask/Jinja templates, plain CSS and JS (`static/`), Playwright-driven frontend gate
(`scripts/dev/_frontend_gate_*.py`), pytest.

**Branch:** `feat/ui-round-2-backlog` (PR #269). The album-matching, cache and MusicBrainz fixes are
NOT in this plan (separate stacked PR, owner ruling R8).

## Owner rulings (fixed, not open)

- **R1** Selected option, every control (index mode switch, Rank by, Unmatched albums on index and
  Results, Results Sort leaderboard): soft tint, primary text, 1px outline from
  `--shell-selected-outline`. The token's values are set by RA2 (below), which replaces the values
  R1 first gave.
- **R2** Selected-option text is held at 4.5:1 (owner exception to the 7:1 aim, "Keep primary, lower
  the gate"); unselected option text stays 7:1 on the segmented controls (RA1 is the one exception).
  Already in `b6feb13`; not revisited here.
- **R3** Short windows: the expanded form's top floor stays 0.25rem. The graduated lift (never below
  1.5rem above the mode switch when there is room) stays.
- **R4** The hero strip stays hidden below 860px.
- **R5** Loading page labels are "Cache hits" and "Albums to search"; Back from the results reaches
  the form (`location.replace`).
- **R6** F-B23-46 (owner, 2026-10-25): when the Results page ranks by listening time, albums with no
  listening time (none or zero) are dropped from the ranking with ranks renumbered, and they come back
  when ranking by track plays; same rule server-side and client-side, so a run started in playtime
  mode and a page switched to it show the same leaderboard. RA3 and RA5 settle the header and the
  server half.
- **R7** One 860px viewport breakpoint (docsync DOC009); component-width layouts use container
  queries, as the strip does.
- **R8** Matching, cache and MusicBrainz fixes are out of scope.
- **RA1** (2026-10-25, "Keep muted, gate at 4.5") The mode switch's unselected label keeps
  `--ss-text-muted` (5.17:1 light, 5.82:1 dark on its track). The gate holds that one cell (its
  unselected text and its hover) at 4.5:1, a second owner exception. The segmented controls'
  unselected text stays 7:1.
- **RA2** (2026-10-25, "One stronger outline") `--shell-selected-outline` becomes `#775ab5` light and
  `#8a79ab` dark. Measured: light 5.01 track / 4.51 sunken / 5.01 card / 4.76 results surface; dark
  5.00 / 4.57 / 4.63 / 4.80. One token; every selected-option boundary gate (index and Results, both
  themes) holds 4.5:1. Replaces the first R1 values (`#7d61b7` / `#8373a3`) and the earlier idea of
  keeping the include gate at 3:1.
- **RA3 / RA5** (2026-10-25, "Header unchanged + a note"; confirmed: "a run with listening-time mode
  renders the zero time hidden so yes switching to track plays brings them back") Total Albums, Top
  artist and Scrobbles keep describing the whole result under listening-time ranking. A short note
  states how many albums with no listening time are hidden; the toast names the count. The server
  renders those rows hidden in a run started in playtime mode, so switching to track plays restores
  them. No new per-row data interface.
- **RA4** (2026-10-25, "goal is to be AA compliant throughout which it should be. AAA is a bit too
  challenging throughout.") New gate lines in this plan hold 4.5:1 for text and 3:1 for non-text unless
  a ruling above sets more; existing 7:1 gates are not lowered unless a ruling names the cell (only RA1
  does).

## Global constraints (every task)

- One concern per commit, exactly the brief's scope. Docs follow code: prose a change makes untrue is
  fixed in the same commit, except point-in-time records (`docs/history/`, `docs/logarchive/`,
  `docs/superpowers/`, dated PLAYBOOK Section 4 entries) and the frozen design snapshot
  (`docs/design/README.md`, `reference/`, `tokens/`, `components/`); overrides of the snapshot go in
  `docs/design/RECONCILIATION.md`.
- Tests assert intended behaviour, not the code as written. No wording-only pins, nothing that passes
  if the function under test is deleted (AGENTS.md Test Quality Rules). Every new or edited test is
  proved RED first (against the unchanged code, or by a named planted defect restored byte-identical
  afterwards), then GREEN. Quote each FAIL and PASS line. Where a task adds a gate check, a persistent
  stub-page test drives the check function and asserts its failure line, so a later change that stops
  calling the helper fails a test, not just a hand-run proof.
- Shared bookkeeping is written only by a LANDING, never by a code phase: `docs/agents/PLAYBOOK.md`
  (Section 4 entry for the task, directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker line,
  untagged side task, heading `### <date> - UI round 2 backlog: <topic>`), `docs/logarchive/`,
  `docs/agents/FINDINGS.md`, `docs/history/findings/FINDINGS_ARCHIVE.md`, `config/docsync.toml`
  (`[test_count]` pin only), `.claude/SESSION_CONTEXT.md`, and `doc_state_sync.py --fix`. Commit
  procedure is AGENTS.md "Commit Rules" (entry, `pytest -q` count N, `--fix --test-count N`, stage by
  name, pre-commit, `--check`, commit).
- Do not stage `config/docsync.toml` outside `[test_count]`, `scripts/docsync/`,
  `scripts/doc_state_sync.py` or `scripts/dev/docsync_preflight.py`; no task here needs to.
- Docsync-watched phrases survive any rewrite: DESIGN.md keeps "below `860px`"; RECONCILIATION keeps
  "hero and form use `1.075`".
- ASCII only in hand-written files except where a file already holds the character. Keep line
  endings. Edit with the Edit tool; never `sed -i`; never `git checkout -- <file>` over uncommitted
  work (copy aside to undo a planted defect).
- Tailwind scans `static/js` for class names: a comment must not contain the word daisyUI uses for
  its tab component.
- The compiled stylesheet is rebuilt by the `tailwind-css-drift` hook; stage source edits before
  `pre-commit` and re-stage what hooks rewrite.
- Browser gates run only through the lock wrapper with the absolute venv interpreter:
  `python C:/ssw/tools/with_browser_lock.py <absolute venv python> scripts/dev/frontend_gate.py` (and
  the same for `scripts/dev/results_behavior_tests.py`). A relative interpreter path resolved to the
  wrong Python on 2026-10-25. Expected advisory lines: `[ERROR] Failed to fetch Spotify token`,
  `loaded no faces from the kit`.
- The full-suite command ignores the owner's untracked `tests/scripts/dev/test_mutation_test.py`
  (`--ignore=tests/scripts/dev/test_mutation_test.py`); see the workspace `constraints.md` Gates.

## Frozen interfaces (shared between tasks; do not rename)

| Name | Where | Value / shape |
|---|---|---|
| `--shell-selected-outline` | `static/css/shell.css` (light and dark blocks) | `#775ab5` light, `#8a79ab` dark (RA2); `index.css` and the other rules only reference the variable |
| `SEG_BOUNDARY_FLOOR` | `scripts/dev/_frontend_gate_colour.py` | `4.5` (was `3.0`); the outline against the track |
| `INCLUDE_BOUNDARY_FLOOR` | `scripts/dev/_frontend_gate_include.py` | `4.5` (was `3.0`); the outline against the Results card (dark 4.63 with the RA2 token). Lands in the same commit as the token, because the old dark token is 4.24 on the card |
| spec key `unselected_floor` | the dict `seg_contrast_failures` and `seg_hover_failures` take | optional float; default `SEG_TEXT_FLOOR` (7.0); lowers one control's floor for its unselected option text and its unselected-hover cell. Added by T8 (not T1) |
| `MODE_SWITCH_SEG` | `scripts/dev/_frontend_gate_forms.py` | `{"track": ".mode-tabs", "selected": ".mode-pill.active", "unselected": ".mode-pill:not(.active)", "unselected_floor": 4.5}` |
| `EXPANDED_GAP_FLOOR_REM` | `scripts/dev/_frontend_gate_layout.py` | `1.5` (mirrors `positionForm` in `static/js/index.js`) |
| `SHORT_WINDOW_TOP_REM` | same | `0.25` (R3) |
| `_expanded_placement_failures(label, measured)` | same | pure; `measured` keys `rootFontSize`, `gapAboveSwitch` (px, header bottom to `.mode-tabs` top), `formInnerTop`, `wellTop`; returns `list[str]` |
| `STRIP_ROW_QUERY_EM` | same | `26` (mirrors `@container (width < 26em)` in `static/css/index.css`; the em is the strip wrap's computed font size, `1.25rem * --index-scale`) |
| `_strip_layout_failures(mode, width, measured)` | same | pure; `measured` keys `containerWidth`, `wrapFontPx` (the wrap's computed font size, the query's em), `itemTops` (list of 3), `itemLefts` (list of 3), `termHeights`, `termLineHeight`, `displayed` (bool); returns `list[str]` |
| strip selectors | `templates/index.html` | wrap `.index-hero__marks-wrap`, lists `[data-mode-marks="album"|"heatmap"]` (`.is-active` is shown), items `li`, terms `.index-hero__strip-term` |
| stat names / ids / labels | orchestrator, `templates/loading.html` | `cache_hits`, `albums_to_search`; `#stat-cache-hits` "Cache hits", `#stat-to-search` "Albums to search" |
| listening-time rule predicate | results page, client and server | a row is dropped from the ranking iff the ranking metric is listening time and `Number(data-play-time-seconds)` is not > 0 (server: `play_time_seconds` missing, None or <= 0). A dropped row carries `hidden` and has an empty `data-rank` and an empty visible rank cell; the remaining rows are ranked 1..n on `data-rank` and the visible rank cell. Unmatched rows hidden by Hide stay hidden whatever the metric. Nothing new is added per row |
| hidden-count note | `templates/results.html` (element added by T7b, server state set by T10), `static/js/results.js` | `#playtime-hidden-note` (carries `hidden` when not applicable) containing `#playtime-hidden-count` whose text is the integer N = rows dropped by the rule and not already hidden by Hide. Shown only while ranking by listening time and N > 0 |
| header figures | Total Albums, Top artist, Scrobbles | describe the whole result under either metric (RA3); the rule changes none of them, client or server |
| listening-time toast | `static/js/results.js` | the existing sentence, plus the count N when N > 0 (the integer appears in the text); unchanged when N = 0 and unchanged on switching to plays |

## Dispatch

Controller dispatches each wave's tasks in parallel (MODE code, detached scratch worktrees, patch plus
code report), then lands the patches serially in the order below (MODE land, one commit each, each
followed by the controller's gate-runner). A task with `After:` gets those tasks' patches staged in its
worktree first.

| Wave | Tasks (parallel) | Peak agents |
|---|---|---|
| 1 | T1 outline token and boundary floors, T2 loading-stats orchestrator tests, T3 loading page JS tests, T4 DESIGN.md | 4 |
| 2 | T5 RECONCILIATION.md, T6 expanded-placement gate, T7 client listening-time rule | 3 |
| 3 | T7b hidden-count note and toast, T8 mode-switch gate, T9 hero-strip gate | 3 |
| 4 | T10 server listening-time rule | 1 |
| 5 | T11 two-path agreement test, T11b DESIGN.md rule paragraph and finding closure | 2 |
| 6 | T12 stale-copy sweep (serial) | 1 |

**Peak agents: 4** (wave 1).

**Landing order:** T1, T2, T3, T4, T5, T6, T7, T7b, T8, T9, T10, T11, T11b, T12. T8 and T9 are
independent of each other and of T7b; any of the three may land first. A landing never overlaps another
landing or a gate-run.

**Gate-deciding scripts (each lands alone: its own commit, no other task's change in it, and the
controller's full gate-runner passes on it before the next landing):** T1 (`_frontend_gate_colour.py`,
`_frontend_gate_include.py`, with the token), T6 and T9 (`_frontend_gate_layout.py`), T7 and T7b
(`scripts/dev/results_behavior_tests.py`), T8 (`_frontend_gate_forms.py`, `_frontend_gate_colour.py`).
T10 and T11 edit no gate script.

**File-per-wave check (re-run after every edit to this plan):**

| File | Tasks (wave) |
|---|---|
| `static/css/shell.css`, `_frontend_gate_include.py` | T1 (1) |
| `_frontend_gate_colour.py`, `tests/scripts/dev/test_frontend_gate_colour.py` | T1 (1), T8 (3) |
| `_frontend_gate_forms.py`, `test_frontend_gate_forms.py` | T8 (3) |
| `_frontend_gate_layout.py`, `test_frontend_gate_layout.py` | T6 (2), T9 (3) |
| `static/js/results.js`, `scripts/dev/results_behavior_tests.py` | T7 (2), T7b (3) |
| `templates/results.html` | T7b (3), T10 (4) |
| `album_flow.py`, `tests/test_routes.py` | T10 (4) |
| `DESIGN.md` | T4 (1), T11b (5) |
| `docs/design/RECONCILIATION.md` | T5 (2) |
| `tests/services/test_orchestrator_process_albums.py`, `..._fetch_and_process.py` | T2 (1) |
| `tests/frontend/test_heatmap_pure_functions.py` | T3 (1) |
| `tests/scripts/dev/test_frontend_gate_include.py` (new), the agreement test (new) | T1 (1), T11 (5) |

No file is touched by two tasks of one wave.

**Tests per task** are named in each task. A code phase runs only those files plus any that import a
module it changes (`git grep -l "import <module>\|from <module>" tests/`); the gate-runner runs the
full suite and the browser gates at landing.

## Open questions

None. The former Q1 (mode switch label), Q2 (do dropped rows come back) and Q3 (header figures) are
settled by RA1, RA5 and RA3.

---

## Task 1: One stronger outline, held at 4.5:1 in every boundary gate

**Wave:** 1 | **After:** none | **Mode:** code | **Gate-deciding scripts: lands alone**

**Touches:**
- `static/css/shell.css`
- `scripts/dev/_frontend_gate_colour.py`
- `scripts/dev/_frontend_gate_include.py`
- `tests/scripts/dev/test_frontend_gate_colour.py`
- `tests/scripts/dev/test_frontend_gate_include.py` (new; no test file covers the include gate today)

**Behaviour.** Set `--shell-selected-outline` to `#775ab5` (light) and `#8a79ab` (dark) in `shell.css`
and rewrite the comment above it (it describes a 87% / 71% mix at 4.60 / 4.58; say the values are the
primary mixed toward the ground until every surface a selected option sits on clears 4.5:1, RA2).
`SEG_BOUNDARY_FLOOR` and `INCLUDE_BOUNDARY_FLOOR` both become 4.5; update the constant comments, the
`seg_contrast_failures` docstring ("a 3:1 chip boundary") and the `card_boundary_failures` docstring
("at 3:1 against the card"). The token and both floors land in one commit: with the old dark token the
card boundary is 4.24:1 and a 4.5 floor would fail. Other rules that read the variable
(`index.css` `.mode-pill.active`, `shell.css` selected rules) need no edit. The unselected text floors
(7:1) and the selected-text floor (4.5) are untouched; `unselected_floor` is T8's.

**Tests** (run `test_frontend_gate_colour.py`, `test_frontend_gate_include.py`,
`test_frontend_gate_split.py`): stub pages whose `evaluate` returns canned paints per theme (patch
`wait_for_settled` / `_set_theme` as the neighbours do), asserting on the returned failure lines.
- [ ] `seg_contrast_failures`: outline at 5.00 dark and 5.01 light passes; 4.49 fails in each theme
      alone, and the message names the cell, the theme and "4.5:1".
- [ ] An outline at 3.5 (above the old floor) fails: guards the floor value, not just the comparison.
- [ ] `card_boundary_failures`: 4.63 on the card passes in dark; 4.49 fails and 3.5 fails, and the
      message names the card and "4.5:1".
- [ ] Selected text at 4.49 fails and at 4.5 passes (the R2 floor is not loosened by this task).

RED/GREEN for the token (code phase, through the wrapper): with only the two floors raised and the old
dark token, `frontend-gate` must report the card boundary at 4.24:1 under 4.5:1; with the RA2 values it
passes. Planted defects (restore each; show PASS): `SEG_BOUNDARY_FLOOR` back to 3.0;
`INCLUDE_BOUNDARY_FLOOR` back to 3.0.

**Acceptance:** the four checks; the token RED then GREEN in the browser gate; `pre-commit run --files`
on the five files; every selected-boundary gate (index and Results, both themes) passes at >= 4.5 in
the landing's gate-runner.

---

## Task 2: Prove the loading stats add up at the orchestrator

**Wave:** 1 | **After:** none | **Mode:** code

**Touches:**
- `tests/services/test_orchestrator_process_albums.py`
- `tests/services/test_orchestrator_fetch_and_process.py`

**Behaviour.** `process_albums` records `cache_hits` and `albums_to_search` at the cache split; their
sum is the number of albums that passed the thresholds, whatever the search later finds. Threshold
filtering happens upstream of `process_albums`, so the sum is proved at both levels: at `process_albums`
(its input is the threshold-passed set) and once through the caller. Test through the job store the way
the file's neighbours do (`jobs.create`, then read the recorded stats), not by mocking `record_stat`.

**Tests** (run both files):
- [ ] `process_albums`, mixed run (some cached, some missing): `cache_hits == hits`,
      `albums_to_search == misses`, sum == input size.
- [ ] A missed album that ends unmatched still counts in `albums_to_search` (the figure is known before
      the search; unmatched does not subtract).
- [ ] All cached: `albums_to_search == 0` and the sum still holds. Database unavailable: `cache_hits ==
      0`, `albums_to_search ==` all.
- [ ] Through `fetch_and_process_albums` (in `..._fetch_and_process.py`, beside
      `test_fetch_and_process_retains_all_below_threshold_albums`): with one album under the
      thresholds, `cache_hits + albums_to_search` equals the albums that passed, not the albums
      fetched.

RED by planted defect in `scrobblescope/orchestrator/__init__.py` (not a Touches file; the brief names
it, restore byte-identical and prove `git diff --quiet`): record `len(cache_misses) + 1`, then drop the
`albums_to_search` line; each must fail a named test.

**Acceptance:** all new tests pass; each planted defect turns at least one test red; no source file
changes in the patch.

---

## Task 3: Hold the loading page's stats and Back behaviour in a test

**Wave:** 1 | **After:** none | **Mode:** code

**Touches:**
- `tests/frontend/test_heatmap_pure_functions.py` (its loading-page section, using `js_browser`,
  `ALBUM_LOADING_MARKUP`, `LOADING_JS`)

**Behaviour.** Extend the loading markup in that section with the two stat tiles and the stats
container (ids frozen above, `hidden` class as in `templates/loading.html`), then:
- [ ] A `/progress` answer carrying `cache_hits: 12, albums_to_search: 30` reveals both tiles showing
      "12" and "30"; an answer carrying `cache_hits` but not `albums_to_search` shows the first tile
      and leaves the second hidden (one test: the positive and the negative together, so it fails if
      either tile reads the wrong key).
- [ ] The finished run's redirect replaces the loading entry in history: after the scheduled redirect
      runs, the page is at `/results` and `history.length` is unchanged (serve `/results` with
      `page.route`, load the loading page from a routed URL rather than `set_content` so history is
      real). `location.assign` must fail this test.
- [ ] Label wording ("Cache hits", "Albums to search") is not pinned here; a wording-only assertion
      fails the Test Quality Rules. The behaviour guarded is which figure fills which tile.

Planted defects: `window.location.assign('/results')` back in `redirectToResults` (in
`static/js/loading.js`, restored byte-identical); read `stats.cache_hits` from the wrong tile.

**Acceptance:** tests green; both planted defects red; only the test file in the patch.

---

## Task 4: DESIGN.md says what ships

**Wave:** 1 | **After:** none | **Mode:** code

**Touches:**
- `DESIGN.md`

**Behaviour.** Correct, in place:
- Segmented Controls & Mode Tabs: the selected option is soft tint, primary text (5.47:1 light, 6.38:1
  dark on the tint, held at the 4.5:1 AA floor by owner exception, R2) and a 1px outline from
  `--shell-selected-outline` (`#775ab5` 5.01:1 light, `#8a79ab` 5.00:1 dark against the track, and at
  least 4.5:1 on every surface a selected option sits on, RA2; `Highlight` under forced colours).
  Delete "primary border 6.06:1 / 8.14:1" and "base-content ink 14.81:1 / 13.04:1 ... keeps on hover"
  (stale since `f2bec89`). Unselected option text stays the body token (8.71:1 / 10.61:1); unselected
  hover keeps the base-content deepening. State that the index mode switch shares this look except its
  unselected label, which is the muted token (5.17:1 light, 5.82:1 dark; hover is the primary colour),
  held at 4.5:1 by the second owner exception (RA1). State the AA goal (RA4) where the file speaks of
  the 7:1 aim.
- The Fixed Composition Rule: the lift is up to 2.5rem and gives way first, never taking the gap above
  the mode switch under 1.5rem; a form too tall for that falls back to plain centring; the floor under
  the header stays 0.25rem; a window too short for the expanded form scrolls. Line 174's "positioned up
  to 2.5rem above centre" matches.
- The index hero: a three-column strip per mode (serif term with a line icon over one plain
  description, hairline rules), one container query (the strip turns into rows when its column is
  narrower than 26 term widths) and hidden below `860px`; the lede is `48ch`, wrapped `pretty`. Keep
  the existing "below `860px`" phrasing for docsync.
- The loading stats: Pages fetched and Scrobbles, then Cache hits and Albums to search (together the
  albums that passed the thresholds); each rises into place on arrival; the finished page replaces
  itself so Back reaches the form.
- No `§` marks, "Albums passing", "Spotify matched", "40ch" anywhere in the file.

**Tests:** none to write. Run `tests/test_design_snapshot.py` and `tests/test_docsync_*.py` files that
read DESIGN.md (`git grep -l "DESIGN.md" tests/`).

**Acceptance:** [ ] `grep -nE "6\.06|8\.14|14\.81|13\.04|40ch|§|Albums passing|Spotify matched"
DESIGN.md` has no hit that states a current outline or ink figure (6.06 / 8.14 may appear only as the
mode switch's primary hover text, if stated, recomputed); [ ] every figure is recomputed from the tokens
(`#6a4baf`, `#775ab5`, `#8a79ab` etc.), not copied; [ ] `python scripts/doc_state_sync.py --check`
exits 0 on the tree.

---

## Task 5: RECONCILIATION.md records the overrides

**Wave:** 2 | **After:** T4 | **Mode:** code

**Touches:**
- `docs/design/RECONCILIATION.md`

**Behaviour.**
- Section 20 ("The shared look is lifted") and the table row "Segmented control look": mark the
  primary-border and base-content-ink figures as superseded and state the shipped look in place (see
  T4's figures); keep the owner quotes ("The 4.5 is a floor not a goal", "Precisely use what exists;
  segmented control").
- Table row "Heatmap H1 copy": now "Your 365 days *mapped by day.*"; add rows for the album headline
  and lede copy that `50211a7` changed.
- New section 29 (heading style of sections 26-28, dated 2026-10-25): the hero strip replaces the kit's
  mono "capability marks" (what the snapshot specifies, what ships, owner ruling "keep the mobile cut"
  = R4, the container query and why it is not a second breakpoint, R7); the expanded-form placement
  (R3, with the measured 24px / 27px at 1920x1063); the loading stats (R5); the selected-option look
  (R1, R2) with the two owner exceptions: selected text at 4.5:1 and the mode switch's muted label at
  4.5:1 (RA1, quoted "Keep muted, gate at 4.5"); the outline token raised to `#775ab5` / `#8a79ab`
  so every selected-option boundary gate, including the Results card (4.63:1 dark), holds 4.5:1 (RA2,
  quoted "One stronger outline"); and the owner's AA goal (RA4, quoted). Add the section's row to the
  top table.

**Tests:** run the docsync tests that read this file (`git grep -l "RECONCILIATION" tests/`).

**Acceptance:** [ ] no live statement of 6.06/8.14 as the current outline, nor of `#7d61b7` /
`#8373a3` as the current token; [ ] "hero and form use `1.075`" intact; [ ] section 29 cites the
commit hashes and the owner quotes verbatim; [ ] `doc_state_sync.py --check` exits 0.

---

## Task 6: Gate the expanded-form placement

**Wave:** 2 | **After:** none | **Mode:** code | **Gate-deciding script: lands alone**

**Touches:**
- `scripts/dev/_frontend_gate_layout.py`
- `tests/scripts/dev/test_frontend_gate_layout.py`

**Behaviour.** Add the pure helper `_expanded_placement_failures` and call it from
`check_large_display_scale_parity` for: 1920x1063 with the decade scope chosen and thresholds open (the
owner's "every option open") where `gapAboveSwitch` must be >= `EXPANDED_GAP_FLOOR_REM` rem (1px
tolerance); and a short window (1920x700, same state) where the form's top falls to exactly
`SHORT_WINDOW_TOP_REM` rem below the well top (R3: the floor is not raised). The collapsed placement is
unchanged: keep `_form_centring_failures` as is and re-run it at 1920x1063, and fix its docstring and
comment, which still describe `max(0.25rem, (available - height)/2 - 2.5rem)`, to describe the
graduated lift (collapsed forms keep the full 2.5rem lift). Add the new helper's name to `HELPERS` in
the test module (the parity test requires it).

**Tests** (run `tests/scripts/dev/test_frontend_gate_layout.py`, `test_frontend_gate_manifest.py`,
`test_frontend_gate_split.py`):
- [ ] gap 24px at root 16 passes; gap 4px fails; gap exactly 24px passes and 22.9px fails (inclusive
      floor with tolerance).
- [ ] short window: top == 4px passes, top 24px fails (the floor was raised).
- [ ] the collapsed state with the 2.5rem lift passes; a collapsed form lifted by only 1.5rem fails.
- [ ] wiring: a stub-page test drives the function that calls the helper (mirror how the neighbouring
      tests drive `_form_centring_failures`' caller) with a page whose measure returns a 4px gap at
      1920x1063 and asserts the returned failure line names that viewport; it fails if the call or
      the measure is removed.

Planted defect for the browser proof (run `frontend-gate` through the wrapper): in
`static/js/index.js` copy aside, restore the pre-`2609f1f` `top = Math.max(0.25 * rem, (available -
height) / 2 - 2.5 * rem)`; the gate must report the 4px gap at 1920x1063; restore, gate green.

**Acceptance:** the four checks; the planted defect red then green in the browser gate; helper listed
in `HELPERS`.

---

## Task 7: Client listening-time rule (F-B23-46, client half)

**Wave:** 2 | **After:** none | **Mode:** code | **Gate-deciding script: lands alone**

**Touches:**
- `static/js/results.js`
- `scripts/dev/results_behavior_tests.py`

**Behaviour.** `setLeaderboardMetric('playtime')` drops every row the predicate (frozen above) names:
`hidden`, empty `data-rank` and rank cell, out of the ranking, the rest renumbered 1..n on `data-rank`
and the visible rank cell, off the CSV (the exporter already skips `tr.hidden`).
`setLeaderboardMetric('plays')` brings them back, ranked with the rest by play count. Hidden state is
one decision per row (unmatched-and-Hide OR dropped by the rule), so switching metric never reveals a
row Hide is hiding and never hides a row Hide shows. The header figures are untouched (RA3). The note
and the toast count are T7b's; the toast text is unchanged here.

**Edited existing test (name it in the entry):**
`test_sort_updates_order_ranks_metrics_and_accessibility` in `results_behavior_tests.py` encodes the
old behaviour (a durationless row "C" ranked 3rd in listening time with metric "0"); it becomes the
R6 behaviour (C hidden and unranked in the playtime ranking, the visible ranks read from visible rows
only and equal `["1","2"]`, back at rank 3 on plays).

**Tests** (run `scripts/dev/results_behavior_tests.py` through the wrapper):
- [ ] playtime: durationless rows (empty, "0", missing attribute) hidden, with empty rank, and not
      ranked; plays: all back, ranked by plays.
- [ ] Hide interaction: with unmatched rows hidden, round-tripping plays -> playtime -> plays leaves
      unmatched rows hidden and matched durationless rows restored.
- [ ] CSV export while ranked by listening time lists only the ranked rows with ranks 1..n.
- [ ] Header figures: Total Albums, Top artist and Scrobbles read the same text before switching, in
      listening-time ranking and after switching back (the rule changes none of them).

Planted defects (restore byte-identical): skip the renumber after the rule; set `hidden` without
clearing it on the way back to plays; let the rule override Hide.

**Acceptance:** the four checks; each planted defect red; the edited test named in the report.

---

## Task 7b: Hidden-count note and toast count

**Wave:** 3 | **After:** T7 | **Mode:** code | **Gate-deciding script: lands alone**

**Touches:**
- `static/js/results.js`
- `templates/results.html`
- `scripts/dev/results_behavior_tests.py`

**Behaviour.** Add the hidden-count note (frozen above) to `results.html` in its hidden state, in the
results header beside the figures it qualifies (the implementer picks the spot that causes no layout
move on load; the server shows it from the first paint on a playtime-started run in T10, and on a
client switch it follows the listener's own click). `results.js` keeps it in step: on listening-time
ranking with N > 0 it is shown with N in `#playtime-hidden-count`; on plays, or N = 0, it carries
`hidden`. N excludes rows Hide already hides. The toast on switching to listening time gains the count
when N > 0 (frozen above). If the harness page in `results_behavior_tests.py` is a hand-written
fixture rather than the real template, the fixture gains the same two elements in the same file.

**Edited existing tests:** `git grep -n "Leaderboard ranked by" scripts tests`; name any test whose
assertion on the toast the count changes (none expected: the sentence is kept).

**Tests** (run `scripts/dev/results_behavior_tests.py` through the wrapper):
- [ ] Two durationless rows: switching to listening time shows the note with count "2" and a toast
      that contains "2"; switching to plays hides the note and the toast has no count.
- [ ] No durationless rows: the note stays hidden and the toast is the plain sentence.
- [ ] A durationless unmatched row hidden by Hide is not counted (N excludes it).
No wording is pinned; the assertions read the count's integer and the `hidden` state.

Planted defects: count includes Hide-hidden rows; note not hidden on plays; toast omits the count.

**Acceptance:** the three checks; each planted defect red; `pre-commit` clean.

---

## Task 8: Gate the mode switch like the segmented controls

**Wave:** 3 | **After:** T1 | **Mode:** code | **Gate-deciding scripts: lands alone**

**Touches:**
- `scripts/dev/_frontend_gate_colour.py`
- `scripts/dev/_frontend_gate_forms.py`
- `tests/scripts/dev/test_frontend_gate_colour.py`
- `tests/scripts/dev/test_frontend_gate_forms.py`

**Behaviour.** In `_frontend_gate_colour.py`, `seg_contrast_failures` and `seg_hover_failures` accept
the optional spec key `unselected_floor` (frozen above; default `SEG_TEXT_FLOOR`); it replaces the
floor for the unselected option text and the unselected-hover cell only, so the owner exception (RA1)
is one named key, not a second code path. In `_frontend_gate_forms.py` add `MODE_SWITCH_SEG` (frozen
above) and measure it on the index page in both themes and for both selected states (Top albums
selected as loaded; Heatmap after clicking `#mode-tab-heatmap`, restored afterwards), label "Mode
switch", with `seg_contrast_failures` (option text, selected text, chip boundary) and
`seg_hover_failures` (unselected hover, selected-chip hover). Boundary and selected-text floors are
the shared ones (4.5); the unselected label and its hover are held at 4.5 through the spec key (the
muted label measures 5.17 / 5.82, the primary hover about 6.06 / 8.14). If a measured cell is under 4.5
return NEEDS_CONTEXT with the figure; do not lower the key.

**Tests** (run the colour and forms test files):
- [ ] `unselected_floor: 4.5` accepts unselected text at 5.17 that the default rejects, in the option
      text cell and in the hover cell; omitting the key keeps 7.0 (stub pages).
- [ ] the spec's selectors are the ones `templates/index.html` renders (read the template, assert each
      selector matches the expected node count: guards a renamed class).
- [ ] the gate function lists "Mode switch" failures when the selected outline is below 4.5 (stub
      page).

Planted defects: ignore `unselected_floor` in `seg_contrast_failures`; ignore it in
`seg_hover_failures`; browser gate: in `static/css/index.css` copy aside, restore `border-color:
transparent` on `.mode-pill.active`, the gate must fail "chip boundary on track ... under 4.5:1";
restore.

**Acceptance:** the three checks; the planted defects red then green; `pre-commit` clean.

---

## Task 9: Gate the hero strip

**Wave:** 3 | **After:** T6 | **Mode:** code | **Gate-deciding script: lands alone**

**Touches:**
- `scripts/dev/_frontend_gate_layout.py`
- `tests/scripts/dev/test_frontend_gate_layout.py`

**Behaviour.** Add `STRIP_ROW_QUERY_EM` and the pure helper `_strip_layout_failures`, called from
`_check_desktop_scale_bounds` beside `_headline_wrap_failures` for both modes at the gate's desktop
widths (1200, 1500, 1920, 2560 at the existing 900px height) plus 900 and 1100 (a narrow column), and
at 859 and 390 for the hidden check. The measure reads `wrapFontPx` as the strip wrap's computed font
size (the em of the container query), not the term's. Rules: at >= 860 the active list is displayed,
and its columns are three (item tops equal, lefts strictly increasing) when `containerWidth >=
STRIP_ROW_QUERY_EM * wrapFontPx`, rows (tops strictly increasing, lefts equal) otherwise; no
`.index-hero__strip-term` wraps (height <= 1.2 * line height) in either layout at any checked width;
below 860 the lists are not displayed. Add the helper to `HELPERS`.

**Tests** (run the three layout/manifest/split test files):
- [ ] three equal tops at wide width pass; a wrapped term (height 2 lines) fails and names the mode and
      width; rows when wide enough for columns fail; columns when narrow fail.
- [ ] hidden below 860 passes; displayed at 859 fails.
- [ ] boundary: `containerWidth` exactly `26 * wrapFontPx` is columns.
- [ ] wiring: a stub-page test drives `_check_desktop_scale_bounds` (as the neighbouring headline-wrap
      wiring test does) with a measure returning a wrapped term and asserts the failure line; it fails
      if the call is removed.

Planted defects (browser gate): remove the `@container` block (narrow widths fail); delete the
`max-width: 859.98px` `display: none` for `.index-hero__marks` (the 390/859 check fails); restore.

**Acceptance:** the four checks; both planted defects red then green; helper in `HELPERS`.

---

## Task 10: Server listening-time rule (F-B23-46, server half)

**Wave:** 4 | **After:** T7b | **Mode:** code

**Touches:**
- `scrobblescope/routes/album_flow.py`
- `templates/results.html`
- `tests/test_routes.py`

**Behaviour.** For a run in listening-time mode the results page keeps every row in the HTML. Rows the
predicate names carry `hidden` and an empty `data-rank` and rank cell; the others are ranked with a
counter that skips them (`data-rank` and the visible rank text). The header figures (Total Albums, Top
artist, Scrobbles through `album_play_statistics`) are built from the whole result, not from the
ranked rows (RA3), so `play_stats` and `album_list|length` describe every row. The hidden-count note
(T7b's element) is rendered shown, with N, when N > 0. The "no matches" page is kept for a playtime
run in which no row is ranked (every album durationless), as today. `_filter_results_for_display`
stops dropping rows: replace it with a helper that marks them (implementer's name; the template
receives the full list plus what it needs to mark rows). Every other sort mode renders as today. The
client script takes over on load: it must find the server's hidden rows consistent with the predicate.
A playtime run stores `include_unmatched=False` (the form), so N never overlaps Hide.

**Edited existing tests (name each in the entry and say why):**
- `test_filter_results_for_display_removes_zero_playtime_when_sorting_by_playtime` and
  `test_filter_results_for_display_keeps_zero_playtime_for_non_playtime_sort` (the helper no longer
  removes rows; rewrite them against the marking helper, same business rule, same three
  durationless forms).
- `test_scrobbles_figure_leaves_out_albums_a_playtime_ranking_drops` (test_routes.py): the dropped
  album is now in the HTML as a hidden row and the Scrobbles figure counts it (90, not 50); retitle
  it for the whole-result figure.
- Run `git grep -n "playtime" tests/test_routes.py` and `git grep -n "not in .*decode" tests/test_routes.py`
  and name any further test asserting a dropped album is absent from the page.

**Tests** (run `tests/test_routes.py`):
- [ ] A seeded playtime job with two timed and two durationless albums: the HTML holds four rows, the
      two durationless carry `hidden`, the visible ranks are 1 and 2, Total Albums reads 4 and
      Scrobbles is the sum of all four, and the note is shown with count 2.
- [ ] The same job in play-count mode: four rows, none hidden, ranks 1..4, the note hidden.
- [ ] A playtime job where every album is durationless renders the no-matches page.
- [ ] An album with `play_time_seconds` missing, None and 0 are all treated as durationless.

Planted defects: rank by `loop.index` again; drop the `hidden` marker; build `play_stats` from the
ranked rows only.

**Acceptance:** the four checks; defects red; edited tests named.

---

## Task 11: Both paths agree

**Wave:** 5 | **After:** T10 | **Mode:** code

**Touches:**
- `tests/frontend/test_results_ranking_agreement.py` (new)

**Behaviour.** One fixture (the same seeded job params: four albums, two with listening time, one with
seconds 0, one without the key) is rendered twice by the Flask test client: as a playtime run and as a
play-count run. Each HTML is loaded into the `js_browser` harness (static scripts served from disk with
`page.route`, spotlight and other network calls aborted); the play-count page is switched to listening
time through the real toggle button. If the harness cannot load the Flask HTML, return NEEDS_CONTEXT
with the obstacle; do not weaken the test into a markup check.
- [ ] The two pages show the same visible `(album, rank)` sequence, the same Total Albums, Top artist
      and Scrobbles text (whole-result figures, RA3) and the same hidden-count note (integer).
- [ ] Switching the playtime-started page to track plays brings all four albums back, ranked by plays
      (needs T10), and switching it back reproduces the first list.
- [ ] CSV export from both pages produces the same rows.

Planted defects (restore): server renders the durationless rows without `hidden`; client skips the
renumber; each turns an agreement test red.

**Acceptance:** the three tests green; each defect red.

---

## Task 11b: Document the rule; close F-B23-46

**Wave:** 5 | **After:** T4, T10 | **Mode:** code (the landing closes the finding)

**Touches:**
- `DESIGN.md`

**Behaviour.** DESIGN.md gains a short paragraph in Components (a "Results Row: Listening-Time
Ranking" bullet beside the unmatched variant): the rule, that ranks renumber, that the header figures
keep describing the whole result, that a note and the toast state how many albums are hidden, that the
albums return under track plays, and that the same rule runs on the server and in the browser.

**Landing closes F-B23-46:** move its entry from `docs/agents/FINDINGS.md` to
`docs/history/findings/FINDINGS_ARCHIVE.md` with the `-- RESOLVED` suffix, Status line naming the
commits of T7, T7b and T10 and the owner's 2026-10-25 rule and rulings RA3 and RA5 (AGENTS.md
Finding-Writing Rules 3), and run `doc_state_sync.py --fix` to stage what rotates.

**Acceptance:** DESIGN.md paragraph present; `--check` exits 0 after the finding moves.

---

## Task 12: Sweep for stale copies

**Wave:** 6 | **After:** T1-T11b | **Mode:** serial

**Touches:**
- `docs/architecture/top-albums-sequence.md` (the cache-split step names `albums_to_search` beside
  `cache_hits`; verify the diagram node text against the code, it is a checked claim)
- any live file the sweep finds (named in the report before editing; point-in-time files excluded)

**Behaviour.** Dispatch the sweeper over tracked files at HEAD for: `5\.47` described as failing,
`6\.06`, `8\.14`, `14\.81`, `13\.04`, `7d61b7`, `8373a3`, `4\.60`, `4\.58`, `4\.24`, `40ch`, `§ ?0`,
`Albums passing`, `Spotify matched`, `albums_passing_filter` shown on the loading page, `stat-albums`,
`stat-spotify`, `stat-cache\b`, `location.assign\('/results'\)`, `Your last 365 days`,
`any year or decade`, `2\.5rem above centre`, "3:1" beside the selected outline, "7:1" beside the
selected text or the mode switch label, and "dropped" / "no listening time" beside the header figures.
Classify each hit live or point-in-time; fix the live ones (`DESIGN.md`,
`docs/design/RECONCILIATION.md` outside quoted history, `DEVELOPMENT.md`, code comments and docstrings,
`docs/architecture/`). Known live copies at plan time: `docs/design/RECONCILIATION.md` rows 38 and 45
and section 20 (T5), `DESIGN.md` lines 174, 181 and 226 (T4), the `shell.css` token comment (T1), the
`_form_centring_failures` docstring (T6). Known point-in-time, leave alone:
`docs/design/designsystemaudit.md`, `docs/history/`, `docs/logarchive/`, dated PLAYBOOK entries,
`docs/superpowers/`.

**Acceptance:** [ ] every remaining hit is listed in the entry as point-in-time; [ ] `--check` exits 0;
[ ] the final full gates (suite, `frontend-gate`, `results-behavior`, `pre-commit`, `docsync-check`)
pass on the branch head before the controller pushes.
