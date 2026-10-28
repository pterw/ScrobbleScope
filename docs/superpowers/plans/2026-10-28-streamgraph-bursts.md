# Streamgraph burst layers, hidden-artist tooltip and rocket palette plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The heatmap's streamgraph shows 12 layers -- the 10 artists with the most plays in the
365-day window plus the 2 artists with the biggest short burst -- lists the 3 largest artists still
hidden in "Everything else" under a rule in the week's tooltip, and colours the layers from seaborn's
rocket colormap in a fixed order so touching bands stay apart. Design:
`docs/superpowers/specs/2026-10-28-streamgraph-bursts-design.md` (owner-approved 2026-10-28; owner
rulings B1-B10 and controller rulings G1-G7 are in the workspace `context.md`; the spec and this plan
agree on every point).

**Out of scope.** Rotating burst slots; a separate burst view; the heatmap grid's colours; mobile
streamgraph work (U18); the pause-button placement fix (its own PR); any schema change or new
dependency (R2). The window stays the last 365 days ending today (B2) -- `heatmap.py` already builds
it, and no task touches it.

**Architecture:** Four code tasks and one prototype gate, in rolling waves. Task 1 (server, including
the job store's read view) and Task 2 (palette) touch disjoint files and run in parallel; Task 3
(tooltip) edits the same JS file as Task 2 and so builds on Task 2's patch; Task 4 (browser gate) builds
on both. Every task is one atomic commit with the documentation its change makes untrue (R10), so no
bookkeeping task exists beyond the landing's own.

1. **Selection (server).** One pass in `aggregate_weekly_artist_counts` collects counts and play days
   per artist; the top 10 stay as they are; of the rest, the 2 with the largest 21-day peak become
   layers; the per-week hidden list comes from what is left. `jobs._context_view` passes `hidden`
   through to the browser (G6).
2. **Palette (JS).** `layerColour(rank, theme)` keeps its signature and reads a frozen 12-colour array
   per theme through a fixed permutation.
3. **Tooltip (JS, CSS).** `panelModel` gains `hidden`; `fillStreamPanel` draws a rule and up to three
   rows when it is non-empty.
4. **Gate.** The seeded payload carries 12 layers and hidden artists; one new check proves the rule
   and rows appear only for a week that has hidden artists, and so that `hidden` survives the job store.
5. **Prototype (no commit).** Tasks 1-3's patches, applied in a scratch worktree, render the real
   flounder14 payload; Firefox screenshots in both themes are the owner's sign-off gate before ANY
   landing (G5).

**Simplifications against the spec (B7, G4; the spec has been updated to say the same).**

- **One pass, one function.** Selection and the hidden list need the same per-artist weekly counts, so
  they stay in `aggregate_weekly_artist_counts` -- no new module, no second walk over plays. Three
  module constants (`BURST_LAYERS = 2`, `BURST_WINDOW_DAYS = 21`, `HIDDEN_PER_WEEK = 3`) and one private
  helper (`_peak_in_window`); no parameter nothing uses (`top_n` stays because tests use it).
- **No `burst` flag in the payload.** Nothing renders or reads it, and a layer past index `top_n` is a
  burst layer. Adding it later is one key.
- **Palette in JS, not 12 CSS tokens.** `layerColour(rank, theme)` already lives in JS, the gate and
  tests call it, and README ("The palette has one owner") already makes `heatmap.js` the owner. One
  source, no read-back from CSS.
- **Per-theme sampling windows (owner B9).** Dark samples rocket over 28%-90%, light over 15%-78%: two
  12-colour arrays, one permutation. A single 15%-90% window leaves one end invisible in each theme.
- **The prototype is the real code.** No throwaway page: Tasks 1-3 run as code phases (patches, no
  landing), the patches are applied in a scratch worktree, and only the data loader and the screenshot
  script are scratch. The owner signs off on the code that will land.

**Tech Stack:** Python 3.13 stdlib (`heapq`), pytest, hand-built SVG in `static/js/heatmap.js`, the
Chromium pure-function harness (`tests/frontend/`), Playwright for the browser gate. No new dependency.

## Frozen interfaces

Every task reads this section; nothing in it changes without the controller.

**Payload (`result["weekly_artists"]`, built by `plays.aggregate_weekly_artist_counts`, W = number of
weeks):**

```text
{
  "weeks":   [iso Monday, ...W],                        # unchanged
  "artists": [{"name": str, "counts": [int, ...W]}],    # top 10 by window total, then <= 2 burst
                                                        # layers; <= 12 entries; no "burst" key
  "other":   [int, ...W],                               # unchanged meaning: everything not a layer
  "hidden":  [[{"name": str, "count": int}, ...<=3], ...W]   # per week, largest first, count > 0
}
```

- Layer order in `artists`: the top 10 (window total descending, tie on key), then burst layers (21-day
  peak descending, tie on larger window total, then key). The JS rank of a layer is its index.
- `hidden[t]`: the (up to) 3 artists with the most plays in week `t` among those that are neither a
  layer nor an empty key; count descending, tie on key; a name is the first spelling seen. A week with
  none is `[]`. Empty-key plays stay in `other` and are never named.
- `jobs.context(job_id)["results"]["weekly_artists"]` carries `hidden` when it was stored (a copy the
  caller may mutate) and has no `hidden` key when it was not (a payload stored by an older release).
  A payload without `hidden` still draws: the panel shows no rule.

**JS (`static/js/heatmap.js`, test hooks object):**
`layerColour(rank, theme)` unchanged signature, `rank` 0..11, `theme` `'light' | 'dark'`;
`panelModel(payload, week, hoverId)` returns the existing `{header, side, rows}` plus
`hidden: [{name, count}]` (`[]` when the week has none or the payload has no `hidden`);
`streamPalette` (new hook) is
`{light: [12 hex], dark: [12 hex]}`, the two rows below.

**Palette (G3, B9).** Source: seaborn `v0.13.2`, `seaborn/cm.py`, `_rocket_lut` (256 RGB triples in 0..1),
fetched read-only from
`https://raw.githubusercontent.com/mwaskom/seaborn/v0.13.2/seaborn/cm.py` (no dependency added).
Colour `i` of a window `[lo, hi]` is the LUT linearly interpolated at `(lo + (hi - lo) * i / 11) * 255`,
rounded per channel, `i` = 0..11, dark to light.

| theme | window | step 0 .. step 11 |
|---|---|---|
| light | 15%-78% | `#391a40 #4f1d4c #671f55 #7f1e5a #981b5b #b11759 #c81951 #db2a46 #e9433e #f05f43 #f47a54 #f5946b` |
| dark  | 28%-90% | `#6d1f56 #851e5b #9e1a5b #b61657 #cc1c4f #de2e44 #eb473e #f16445 #f47e57 #f5976e #f6ae87 #f7c5a5` |

Permutation, rank to step: `STREAM_STEPS = [0, 4, 5, 8, 9, 1, 2, 10, 11, 3, 6, 7]`.
Why it holds: `streamOrder` puts the layers, bottom to top, at ranks
`[11, 9, 7, 5, 3, 1, 0, 2, 4, 6, 8, 10]` when the burst layers (ranks 10, 11) have the smaller volumes in
that order. Burst layers are chosen by 21-day peak, not by window total, so the two may swap volumes; then
the chain ends `..., 8, 11` and the closest touching pair is **3** steps apart. Over both cases every
touching pair is **at least 3** steps apart (4 in the first case). "Everything else" keeps its grey token
and sits below the chain.

Contrast of the layer fills against the frame (`#f0ebe0` light, `#1f1b28` dark): light min 1.89 (step
11) max 12.66; dark min 1.59 (step 0) max 10.83. Layer fills stay exempt from the 3:1 non-text floor
(U20, S13/S14) because the panel lists every value as text; the numbers are shown to the owner in the
prototype, not decided silently.

## Global Constraints

Every task's requirements include this section and the workspace `constraints.md` (R1-R13 win where
this section is shorter). The executing agent reads, from the SDD workspace
`C:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/.superpowers/sdd/2026-10-28-streamgraph-bursts/`,
`constraints.md` (rules R1-R13, gates) and `context.md` (owner rulings B1-B10, controller rulings G1-G8).

- **Qualified interpreter only.** The interpreter is
  `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe` and its sibling
  `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe`. Quote every path (it has
  spaces); never bare `python`, never a second venv. Every command below is written out in full.
- **No new dependency, no schema change** (R2). Palette values are frozen above and typed into the
  source; the seaborn fetch and any derivation script are scratch (R8), never committed.
- **Tests (B8, R9).** Test intended behaviour only, not that code runs. One test per behaviour,
  near-duplicates parametrized, an existing test edited before a new one is added. Docstrings in the
  repository form: one line, then `GIVEN:`, `WHEN:`, `THEN:`. Every new or edited test is proven red
  against BASE and then green, both lines quoted in the report. A silent green is worse than a false
  red: a test that cannot fail when the behaviour is deleted is not written. No `mutate.py`, no
  wording pins. Write exactly the tests each task names, no more.
- **Bookkeeping is a landing concern.** No task's `Touches:` includes `docs/agents/PLAYBOOK.md`,
  `.claude/SESSION_CONTEXT.md`, `docs/agents/FINDINGS.md`, the archives, this plan's boxes, or the
  `[test_count]` pin. A landing follows R1 (Section 4 entry), R3 (gates, `--fix --test-count N`),
  R4/R5 (Validation line, commit message), ticks that task's boxes, and runs the gates in
  `constraints.md`.
- **Docs follow the code (R10).** Each task fixes in its own commit the prose it makes untrue, and
  updates `Last updated:` in every doc it changes. `docs/design/reference/audit-review.md` and other
  point-in-time records are left alone.
- **Frontend (R13).** No daisyUI class words in JS comments (Tailwind scans `static/js`); browser gates
  only through `with_browser_lock.py`; the owner browses with Firefox, so say if a CSS feature used is
  Chromium-only (none is planned); report min and max of any new colour pairing in both themes.
- **ASCII only** in every file and commit message (R7).
- **Over-building is the failure to avoid.** Each task ends with a "Do not" list; it is part of the
  requirement. No new module, option, flag, helper, constant or test beyond what the task names.

### How the steps run without our tooling (manual equivalents)

- **Code phase** (Tasks 1-4; "Mode: code" in the Dispatch table): create a detached scratch worktree at
  BASE: `git worktree add --detach C:/ssw/t<N> e1ea6008f8c7699793a435e06d1b55ce1e5401e2`, work only
  there, never commit, stage the changed files by name (`git add <path> ...`, never `git add -A` or
  `git add .`), and write the patch from the staged state:
  `git diff --cached --binary e1ea6008f8c7699793a435e06d1b55ce1e5401e2 > C:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init/.superpowers/sdd/2026-10-28-streamgraph-bursts/task-<N>-code.patch`.
  A task that is "After" another first applies that task's patch: `git apply --index <that patch>`.
- **"Nested gate-run" / gate-runner** means: run the commands of the `Gates` block in `constraints.md`
  that the task's "Gates" line lists, each exactly as written there, from the worktree root, and quote
  the last line of each. In a code phase run only the focused test files, `pre-commit run --files
  <changed files>` and, for `static/` changes, the frontend gate; the three `suite-*` shards run at
  landing. Hook complaints about the scratch worktree (R12) are quoted, not fixed.
- **`nested_verdicts`** (our reviewer plumbing): none. Do not look for it.
- **Landing** (serial, in `C:/ssw/u7` on `feat/streamgraph-bursts`): `git apply --check --index <patch>`
  then `git apply --index <patch>` (a failed check stops the landing: report it, do not use `-3`), re-run
  the focused tests, then the steps in "Dispatch".
- Commands used by tasks (copy exactly; `<files>` are the task's changed files):
  - Focused pytest: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider <test paths> [-k "<expr>"]`
  - Pre-commit on files: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe" run --files <files>`
  - Frontend gate: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" C:/ssw/tools/with_browser_lock.py "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/frontend_gate.py`
    (a `[browser-lock] waiting` line is normal: wait; never delete `C:/ssw/.browser-gate.lock`).

---

### Task 1: Twelve layers and the hidden-artist list from one pass (server)

**Touches:**
- Modify: `scrobblescope/plays.py` (`aggregate_weekly_artist_counts`, new constants and helper)
- Modify: `scrobblescope/jobs.py` (`_context_view`, only the `weekly_artists` copy)
- Modify: `tests/test_plays.py` (the aggregate tests, around `aggregate_weekly_artist_counts`)
- Modify: `tests/test_jobs.py` (`test_context_isolates_dict_results_from_callers`)
- Modify: `README.md` (lines 156-157 the streamgraph bullet's "ten most played artists" sentence; line
  369 the `plays.py` row; lines 487-488 "for the ten most played artists")
- Modify: `docs/architecture/heatmap-sequence.md` (line 83 "the top 10 artists")

**After:** none (Wave 1). **Mode:** code. **Interfaces:** produces the payload in "Frozen interfaces";
consumed by Tasks 3 and 4 only through that shape. **Gates:** focused tests, pre-commit on the changed
files (no `static/` change, so no browser gate).

**Behaviour.**

`aggregate_weekly_artist_counts` keeps its window, week grid, artist key and top-`top_n` ranking.

```python
BURST_LAYERS = 2        # layers added past top_n for short-lived listening
BURST_WINDOW_DAYS = 21  # a burst is the most plays on this many consecutive days
HIDDEN_PER_WEEK = 3     # artists named per week from what "Everything else" holds


def _peak_in_window(days: list[int]) -> int:
    """Return the most plays on any BURST_WINDOW_DAYS consecutive days.

    *days* are the play dates as ordinals; one sorted walk with two pointers
    per artist, never artists x days.
    """
    days = sorted(days)
    peak = start = 0
    for end, day in enumerate(days):
        while day - days[start] >= BURST_WINDOW_DAYS:
            start += 1
        peak = max(peak, end - start + 1)
    return peak
```

In the loop over plays, also `days_by_key.setdefault(key, []).append(day.toordinal())` (after the
empty-key `continue`). After `ranked`: `rest = ranked[top_n:]`;
`bursts = sorted(rest, key=lambda k: (-_peak_in_window(days_by_key[k]), -sum(by_key[k]), k))[:BURST_LAYERS]`;
layers are `ranked[:top_n] + bursts`; `hidden_keys` are the keys in `rest` not in `bursts`; `other` folds
exactly the `hidden_keys` counts (as today's loop folds `ranked[top_n:]`); per week,
`heapq.nsmallest(HIDDEN_PER_WEEK, ((-by_key[k][t], k) for k in hidden_keys if by_key[k][t]))` gives
`hidden[t]` as `[{"name": names[k], "count": -n}, ...]`. Return `hidden` in the dict. Update the
docstring (it says "every artist beyond *top_n*" and must say layers are the top *top_n* plus the burst
layers, and that `hidden` is per week).

`jobs._context_view`: in the existing `weekly_artists` copy, keep the three keys as they are and add

```python
            if "hidden" in weekly:
                results["weekly_artists"]["hidden"] = [
                    [dict(entry) for entry in week] for week in weekly["hidden"]
                ]
```

directly after the dict is assigned, so `hidden` is copied when stored and stays absent when not.

**Tests (behaviours and cases; counts of candidate artists are stated so the two burst slots are always
contested; all aggregate tests in `tests/test_plays.py`, in the class of the existing aggregate tests):**

| # | Behaviour | Cases | Proves red because |
|---|---|---|---|
| a | A burst that runs from a Wednesday into the next Tuesday outranks a hotter single week | `top_n=1`; T 20 plays in a week of its own; X 8 plays Wed-Sun then 7 plays Mon-Tue (peak 15); Y 10 plays in a week of its own; Z 9 plays in a week of its own. Layers `[T, X, Y]`; X's `counts` are zero outside its two weeks; `hidden` is `[]` in every week except Z's, where it is exactly `[{"name": "Z", "count": 9}]` | BASE has no burst layers (artists is `[T]`) and no `hidden` |
| b | The burst window is 21 consecutive days, inclusive | `top_n=1`; T large; three candidates: X with two 6-play clumps, R 8 plays on one day, S 7 plays on one day. Parametrize the gap between X's clumps: 20 days (X peak 12: layers `[T, X, R]`, S hidden) versus 21 days (X peak 6: layers `[T, R, S]`, X hidden) | BASE has no bursts; a `> 21` or per-week defect flips a case |
| c | Burst ties break on larger window total, then key | `top_n=1`; T large; three candidates P, Q, R with the same peak 5 on one day; Q also has 2 plays 40 days later (total 7), P and R total 5. Layers `[T, Q, P]`, R hidden | BASE has no bursts |
| d | Fewer than 12 artists give fewer layers and an empty tail | 11 artists with distinct totals, default `top_n`: 11 layers, `other` all zero, every `hidden[t] == []` | BASE has 10 layers |
| e | The 3 hidden artists per week, largest first, tie on key, fewer when fewer, never a layer | `top_n=1`; T 30 plays; burst layers BurstX (12 plays) and BurstY (11) in week 1 with counts higher than any hidden artist's that week; week 1 hidden candidates A 4, B 3, C 3, D 2 (cap 3, tie B before C); week 2 candidates E 2, A 1 (fewer than 3); week 3 only T (empty). Assert the whole list: `hidden == [[A4, B3, C3], [E2, A1], []]` | BASE has no `hidden` key; a hidden list that includes a layer fails on week 1 |
| f | Empty-key plays are counted in `other` and never named in `hidden` | extend the existing parametrized `test_artists_without_a_key_land_in_other` (`""`, `"!!!"`) with `result["hidden"] == [[]]` | BASE has no `hidden` key |
| g | The job store hands out `hidden` as a copy and leaves it absent when it was not stored | edit `test_context_isolates_dict_results_from_callers` in `tests/test_jobs.py`: parametrize `hidden` over `None` (absent) and `[[{"name": "Suki", "count": 2}]]`; in the stored `weekly_artists` set `hidden` only when not `None`; after the existing mutations also mutate the returned `hidden` (append an empty week, set the first entry's `count` to 999); the fresh read equals the stored dict exactly (with `hidden`, or without the key) | BASE drops `hidden`: the present case fails on the exact-dict assert (and on the mutation line, a `KeyError`); the absent case is green at BASE by design and guards "absent stays absent" |

Edit, do not add: `test_artists_beyond_top_n_fold_into_other_and_stray_plays_are_ignored` (with
`top_n=2` the third and fourth artists are now burst layers): rewrite its data as `"AAABBCDE"` so `A`
and `B` are layers, `C` and `D` bursts (tie on peak and total, then key), `E` joins `other` and shows in
`hidden` as `[[{"name": "E", "count": 1}]]`; keep the stray-play assertion. The other existing aggregate
tests (`columns follow the Monday grid`, `group by key and rank by total`, `each week adds up to the
daily counts`) stay as they are and must stay green: they are the "top 10 unchanged" evidence. Convert
the docstrings of the tests this task adds or edits to the GIVEN/WHEN/THEN form; leave the untouched
ones.

One example (a), the others follow the same shape:

```python
def test_a_burst_across_a_monday_is_one_burst_not_two_weeks(self):
    """A Wednesday-to-Tuesday run outranks a hotter single week.
    GIVEN: top_n=1; X plays 8 times Wed-Sun and 7 times the next Mon-Tue,
        Y 10 times in one week, Z 9 times in one week, T 20 times overall
    WHEN: the weekly counts are aggregated
    THEN: the layers are T, X, Y (X's peak is 15 over 21 days, a per-week
        peak would have kept Y and Z) and X counts nothing outside its two weeks
    """
```

- [ ] **Step 1: Write tests a-g and the edit, run them against BASE.**
  `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider tests/test_plays.py tests/test_jobs.py -k "weekly or aggregate or artists or context_isolates_dict"`
  Quote the red lines (expected: assertion failures on missing `hidden` and absent burst layers, a
  `KeyError` on `hidden` in the jobs test; not import errors).
- [ ] **Step 2: Implement** `_peak_in_window`, the constants, the single pass, the docstring, and the
  `_context_view` change.
- [ ] **Step 3: Same command, green.** Quote it. Also run `tests/test_heatmap.py` and the whole of
  `tests/test_jobs.py` and `tests/test_plays.py`.
- [ ] **Step 4: Docs.** README lines 156-157 ("weekly plays for the ten most played artists, with every
  other artist in one "Everything else" layer" becomes: for the twelve layers -- the ten most played
  artists and the two with the biggest short burst -- with every other artist in one "Everything else"
  layer); lines 369 and 487-488 ("top ten" / "ten most played" become "top ten plus two burst"); the
  sequence diagram line 83 ("top 10 artists ... the rest counted as other" becomes "top 10 artists plus
  the 2 biggest 21-day bursts and the 3 largest hidden artists per week, the rest counted as other").
  `Last updated:` in both files. Leave README line 523 (the unrelated spotlight sample).
- [ ] **Step 5: Pre-commit on the changed files**, stage by name, write the patch (see "manual
  equivalents").

**Do not:** add a `burst` key; add a parameter to `aggregate_weekly_artist_counts`; add any helper,
module or constant beyond the three constants and `_peak_in_window`; touch `heatmap.py`; write tests
beyond a-g and the one edit; paste the full test bodies into docs.

**Resolves:** no finding. Commit subject: `feat(heatmap): Add burst layers and hidden artists to weeks`.
Draft body: the owner's Cameron Winter case (206 plays, rank 17, mostly 11-17 October) vanished into
"Everything else"; layers are now the top 10 plus the 2 biggest 21-day bursts (B4), each week names the
3 largest artists still hidden (B6), and the job store passes the list to the browser. Section 4 entry:
deviations (no `burst` flag), the edited tests by name (including `test_context_isolates_dict_results_from_callers`),
the Validation line.

---

### Task 2: Rocket palette in a fixed order for twelve layers

**Touches:**
- Modify: `static/js/heatmap.js` (the `STREAM_RAMP` / `STREAM_LIGHT_SCALE` constants near line 157,
  `layerColour` near line 278, `streamPayloadValid`'s `> STREAM_RAMP.length` cap near line 297, the
  test hooks object near line 2579)
- Modify: `tests/frontend/test_heatmap_pure_functions.py` (`test_layer_colour_follows_the_ramp_and_light_is_rescaled_not_clamped`;
  the `_eleven_artists` case of `test_stream_payload_valid`)
- Modify: `DESIGN.md` (line 137, the "Stream Layers" bullet)

**After:** none (Wave 1). **Mode:** code. **Interfaces:** consumes "Palette" in Frozen interfaces;
produces `layerColour(rank, theme)` for ranks 0..11 and the `streamPalette` hook. The palette ORDER is
checked by the Task 2 scratch diff and the owner's prototype screenshots, not by a committed test.
**Gates:** focused tests, pre-commit on the changed files, frontend gate.

**Behaviour.** Replace `STREAM_RAMP` and `STREAM_LIGHT_SCALE` with `STREAM_PALETTE = {light: [...],
dark: [...]}` (the two rows of the frozen table, typed exactly) and `STREAM_STEPS = [0, 4, 5, 8, 9, 1, 2,
10, 11, 3, 6, 7]`; `layerColour(rank, theme)` returns `STREAM_PALETTE[theme][STREAM_STEPS[rank]]`. The
payload validity cap becomes `STREAM_STEPS.length` (12; it duplicates the server's `top_n` plus
`BURST_LAYERS`, so add one comment saying so). Export `streamPalette: STREAM_PALETTE` in the hooks
object (no `streamSteps` hook: nothing reads it). Remove no other use of `rocketColor` (the grid and legend keep it).
A one-line comment names seaborn v0.13.2 `_rocket_lut` and the two sampling windows.

**Tests:**

| # | Behaviour | Cases | Proves red because |
|---|---|---|---|
| a | Twelve layers get twelve distinct colours of the theme's palette, and layers that touch in the stack are at least 3 steps apart | edit the existing `layerColour` test (rename it `test_layer_colour_gives_touching_layers_distinct_palette_steps`), parametrized over theme (`light`, `dark`) and over two volume lists: `[120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10]` and the same with the last two swapped (`..., 30, 10, 20`). In one `js_page.evaluate`, for each case: `order = hooks.streamOrder(volumes)`; `steps = order.map(rank => hooks.streamPalette[theme].indexOf(hooks.layerColour(rank, theme)))`; return `steps`. Assert `sorted(steps) == list(range(12))` (every colour found, all distinct) and `min(abs(a - b) for a, b in zip(steps, steps[1:])) >= 3` | BASE has no `streamPalette` hook (the evaluate fails) and only 10 ramp stops |
| b | A payload may carry 12 layers, not 13 | edit `test_stream_payload_valid`: `_eleven_artists` becomes `_thirteen_artists` (invalid); add a `twelve-artists` valid case | BASE rejects 11, so the twelve case is red |

- [ ] **Step 1: Write the tests, run red against BASE.**
  `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider tests/frontend/test_heatmap_pure_functions.py -k "layer_colour or stream_payload_valid"`
- [ ] **Step 2: Implement** as above. Scratch check (not committed, in `<scratchpad>/sgb-2/`): fetch
  `cm.py` with the URL in "Palette" (`curl`, bounded with `--max-time 40`), re-derive both rows with the
  recipe and diff against the typed hexes; quote "0 differences".
- [ ] **Step 3: Green** (same command), then the whole file (`tests/frontend/test_heatmap_pure_functions.py`).
- [ ] **Step 4: Docs.** `DESIGN.md` line 137: the layers use 12 steps of seaborn's `rocket` colormap
  (v0.13.2), light sampled over 15%-78% and dark over 28%-90%, assigned by a fixed permutation so
  touching layers are at least 3 steps apart; keep the "Everything else", gridline, label and outline
  colours and the U20 exemption sentence. Do not touch README (its "one owner" paragraph is about the
  grid ramp and stays true). `Last updated:`.
- [ ] **Step 5: Frontend gate** (changes `static/`): the `[stream colours]` lines print min and max per
  theme; quote them (expected: light 1.89 / 12.66, dark 1.59 / 10.83). Pre-commit on the changed files,
  stage by name, write the patch.

**Do not:** add CSS tokens or a read-back from CSS; add a second permutation or a helper that builds the
palette; change `rocketColor`, the grid ramp or the legend; add tests beyond a-b; say "at least 4" anywhere.

**Resolves:** no finding. Commit subject: `feat(heatmap): Colour stream layers from the rocket map`.
Body: the Tailwind-step ramp left both ends unused and had room for ten layers; twelve layers need
twelve steps (B1, B3), sampled per theme so neither end vanishes (B9). Section 4 entry: the contrast min
and max, deviations (JS array rather than tokens; per-theme windows), the edited tests by name.

---

### Task 3: Hidden artists under a rule in the tooltip

**Touches:**
- Modify: `static/js/heatmap.js` (`streamPayloadValid` end of function, `panelModel`, `fillStreamPanel`)
- Modify: `static/css/heatmap.css` (the `.stream-panel-row` rule block near line 484, a rule style)
- Modify: `tests/frontend/test_heatmap_pure_functions.py` (the `panelModel` and `streamPayloadValid` tests)
- Modify: `README.md` (the streamgraph bullet, after line 161's last sentence)
- Modify: `DESIGN.md` (the "Scrubber panel" bullet under "Heatmap Streamgraph")

**After:** Task 2 (same JS file and test file). **Mode:** code, in a worktree with Task 2's patch applied
and staged (`git apply --index`); make Task 3's edits without staging them and write its patch with
`git diff --binary > <workspace>/task-3-code.patch` (only Task 3's hunks; the patch applies on BASE plus
Task 2's patch, which `git apply --check --index` confirms at landing). **Interfaces:** consumes `payload.hidden` from "Frozen interfaces"; produces
`panelModel(...).hidden`. **Gates:** focused tests, pre-commit on the changed files, frontend gate.

**Behaviour.**

- `streamPayloadValid`: `hidden`, when present, is an array of `numCols` arrays, each entry an object
  `{name: string, count: number}` with a positive integer count; absent is valid; anything else makes
  the stream draw nothing (the existing fail-closed rule). No upper bound on a week's length (the server
  owns the 3).
- `panelModel`: adds `hidden: payload.hidden ? payload.hidden[week] : []`. The existing `rows` are
  unchanged (layers top-down, then "Everything else").
- `fillStreamPanel`: after the rows, if `model.hidden.length`, append an `<hr class="stream-panel-rule">`
  and one `<div class="stream-panel-hidden">` per entry holding an empty 12px spacer span (owner B10),
  the name span and the count span, reusing the row classes' grid so names and counts align with the
  rows above. No `data-rank` on hidden rows (they are not layers and never hovered), no indentation, no
  new horizontal space: the panel's `max-width`, ellipsis and side choice apply as they do to the other
  rows.
- CSS: the hidden rows share the `.stream-panel-row` declarations (group the selector); the rule is a
  1px `var(--stream-line)` top border with the panel's row gap above and below, no extra token.

**Tests:**

| # | Behaviour | Cases | Proves red because |
|---|---|---|---|
| a | The model lists a week's hidden artists, and none when the week or the payload has none | parametrized: week with 3 entries, week with `[]`, payload without `hidden` (older stored result); assert `model["hidden"]` equals the entries / `[]` / `[]` | BASE model has no `hidden` |
| b | A malformed `hidden` makes the payload invalid; an absent one does not | extend `test_stream_payload_valid`: wrong number of weeks, a non-string name, a zero count, a non-numeric count (invalid); absent (valid; already a case) | BASE ignores `hidden`: the invalid cases return true |

The rule and the rows themselves are DOM output: Task 4's browser check proves them; no jsdom test
reaching for markup.

- [ ] **Step 1: Write tests a-b, run red against BASE+Task 2**
  (`"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider tests/frontend/test_heatmap_pure_functions.py -k "panel_model or stream_payload_valid"`).
- [ ] **Step 2: Implement** `streamPayloadValid`, `panelModel`, `fillStreamPanel`, the CSS.
- [ ] **Step 3: Green**, then the whole test file.
- [ ] **Step 4: Docs.** README: append to the streamgraph bullet that a week with artists hidden in
  "Everything else" lists the three largest under a rule; `DESIGN.md` "Scrubber panel": same sentence,
  plus "no indentation" and that the rule only appears when hidden artists exist. `Last updated:`.
- [ ] **Step 5: Frontend gate** (changes `static/`); expected: green on the existing checks (seeded
  payloads have no `hidden` yet, so the panel is unchanged). Pre-commit on the changed files, write the
  patch.

**Do not:** add a jsdom/DOM test; add a CSS token, class beyond `stream-panel-rule` and
`stream-panel-hidden`, or a swatch colour for hidden rows; bound the hidden list in JS; add tests beyond
a-b.

**Resolves:** no finding. Commit subject: `feat(heatmap): List hidden artists under a rule in the tooltip`.
Body: the owner asked for no indentation and a divider that appears only when extra artists do (B6),
with a blank swatch-width spacer so names align (B10). Section 4 entry: the edited tests by name.

---

### Task 4: Browser gate for twelve layers and the hidden rows

**Touches:**
- Modify: `scripts/dev/_frontend_gate_stream.py` (`_ARTIST_COUNT`, `_weekly_artists`, its two
  "ten artists" docstrings near lines 44 and 70, the panel row readers, one new check)
- Modify: `scripts/dev/frontend_gate.py` (import and register the new check beside lines 173-181 and
  304-347)

**After:** Tasks 1, 2 and 3 (the check proves their behaviour and reads `hidden` through
`jobs._context_view`; its code phase starts with all three patches
applied and staged, Task 1, 2 then Task 3, with `git apply --index`; make Task 4's edits unstaged and write
its patch with `git diff --binary > <workspace>/task-4-code.patch`). **Mode:** code. **Interfaces:** consumes the JS
DOM contract from Task 3 (`hr.stream-panel-rule`, `.stream-panel-hidden`) and the Task 1 job-store
contract. **Gates:** pre-commit on the changed files, frontend gate.

**Behaviour.**

- `_ARTIST_COUNT = 12`: the seeded payload has 12 layers (the last two are sparse, nonzero in a few
  weeks only, like bursts) and a `hidden` list per week: three entries in some weeks, `[]` in others.
  Fixed literal values: the two extra artists are `Burst 1` (counts 40, 30, 20 in weeks 5-7) and
  `Burst 2` (counts 25, 35, 15 in weeks 5-7), `0` in every other week; `hidden` is
  `[{"name": "Hidden A", "count": 9}, {"name": "Hidden B", "count": 6}, {"name": "Hidden C", "count": 4}]`
  in every week whose index `t` has `t % 3 == 0`, and `[]` in all other weeks.
  The seed goes through `jobs.succeed` and is read back by `jobs.context`, so a hidden row on screen
  proves `hidden` survives the job store. The existing `reading["layers"] != _ARTIST_COUNT + 1` check,
  the row readers and the keyboard walk keep working: hidden rows have no `.stream-panel-row` class, so
  they are not layer rows. The hover readers that bound rows to the grid (`rowsOutside`) also read
  `.stream-panel-hidden` rows, so the taller panel (12 layers + "Everything else" + rule + 3 rows) is
  proven inside the visible box at the gate's panel viewport.
- New check `check_stream_panel_rule_and_hidden_rows_follow_the_week`: GIVEN the seeded 12-layer job;
  WHEN the pointer is on a week with hidden artists, then on a week without; THEN the first panel holds
  one `hr.stream-panel-rule` followed by exactly the seeded names and counts in order, in the same
  column as the layer names (no indentation: equal `left` of the name spans), and the second holds no
  rule and no hidden rows. Reuse `_hover`, `_open_heatmap` and the failure-list style of the neighbouring
  checks; no new helper unless two checks use it.

- [ ] **Step 1: Extend the seed and add the check; prove it red.** With the full patch stack applied,
  temporarily delete the hidden block (the `if (model.hidden.length) {...}` branch) in
  `fillStreamPanel`, run the frontend gate and quote the failing line of the new check, then restore the
  block by re-applying the original text you saved before deleting it, with the editor (never
  `git checkout` or `git restore`, R6); the tree must equal the stack plus your own edits before Step 2.
- [ ] **Step 2: Green** with the full patch stack: frontend gate (command in "manual equivalents");
  quote the last line and the `[stream colours]` lines. If the panel overflows at the gate's viewport
  with 16 rows plus the rule, stop and report it (the prototype screenshots show it first); do not shrink the check.
- [ ] **Step 3: Docs.** None are made untrue; say so in the report.
- [ ] **Step 4: Pre-commit on the changed files**, stage the two files by name, write the patch.

**Do not:** add a new helper, a new seed function, or a second new check; weaken an existing check to
make room; add JS or CSS changes (those belong to Tasks 2-3).

**Resolves:** no finding. Commit subject: `test(frontend): Check hidden-artist rows follow the week`.

---

### Task 0: Prototype on the real payload and the owner's sign-off (no commit)

**Touches:** nothing tracked. Scratch only, under `<scratchpad>/sgb-proto/` (R8), plus a detached
worktree `C:/ssw/proto` at BASE (removed afterwards).

**After:** the code phases of Tasks 1, 2 and 3 have produced patches (they are not landed).
**Interfaces:** consumes the three patches; produces screenshots and a signed-off verdict. **Gates:**
none; this is a visual and data check for the owner.

**Why this shape (G5).** The prototype renders the real code-phase patches on flounder14's real data and
is the owner's sign-off gate before ANY landing. Simplest faithful render: the real page with the real
code, no new page, flag or route in the app.

- [ ] **Step 1: Build the scratch worktree** `git worktree add --detach C:/ssw/proto e1ea6008f8c7699793a435e06d1b55ce1e5401e2`,
  then `git apply --index` Task 1, 2, 3 patches in that order (a clean apply is itself the check).
- [ ] **Step 2: Load the payload.** A scratch script in `<scratchpad>/sgb-proto/` (run with the
  qualified interpreter, from `C:/ssw/proto`, `LASTFM_API_KEY` read from the primary checkout's
  `C:/Users/peter/Python Projects/ScrobbleScope/.env` and never printed, written or committed) builds the window like `scrobblescope/heatmap.py` does (`to_date` = today UTC,
  `from_date = to_date - timedelta(days=HEATMAP_WINDOW_DAYS - 1)`, `Window(start=datetime.combine(from_date,
  time.min, tzinfo=UTC), end=now)`), awaits `fetch_scrobbles("flounder14", window)` (module
  `scrobblescope.lastfm`), calls the patched `aggregate_weekly_artist_counts` and `aggregate_daily_counts`
  and writes the results to a JSON file next to the script (real user data: never in the repository).
  Seed it as a job exactly like `scripts/dev/_frontend_gate_stream.py::_seed_job` (copy its shape, with
  the loaded `daily_counts` and `weekly_artists` in place of the synthetic ones), then print as text,
  read back from `jobs.context(job_id)["results"]["weekly_artists"]` (not from the aggregate, so the
  job-store pass-through is exercised): the layer names, and `hidden` for the weeks `2026-10-05` and
  `2026-10-12` (11 October is a Sunday, so the 11-17 October listening spans both weeks). Cameron Winter
  must be a burst layer, and `hidden` for those weeks must not repeat any layer name.
- [ ] **Step 3: Screenshot, Firefox, light and dark.** A second scratch script starts the app with
  `serve_app()` from `scripts/dev/_frontend_gate_runtime.py` (a context manager yielding the base URL),
  seeds the job, opens `/heatmap` in Playwright Firefox through
  `C:/ssw/tools/with_browser_lock.py`, and saves PNGs to `<scratchpad>/sgb-proto/` at a desktop width
  where the panel fits: (a) the whole chart at rest; (b) the tooltip on the weeks of 2026-10-05 and
  2026-10-12 showing the rule and hidden rows; (c) the tooltip on a week with no hidden artists (no
  rule); (d) the tooltip on the first column and on the last (week of 2026-10-26, partial: the window
  ends Wednesday 28 October) for the side choice. Include the busiest week, which has the most rows, to
  show the panel fits. Re-renders need no network.
- [ ] **Step 4: Save and stop.** Save the screenshots to `<scratchpad>/sgb-proto/` (the named folder) and
  STOP: the executing agent does not present or judge them. The owner reviews the screenshots, the
  contrast table from "Palette" and any overflow. Landings (Tasks 1-4) start only after the owner approves;
  a rejected palette or window changes only "Frozen interfaces" and Tasks 2 and 4's data, not the
  structure.
- [ ] **Step 5: Clean up, after the owner's verdict,** the worktree (`git worktree remove --force C:/ssw/proto`) and the scratch
  directory.

**Do not:** commit anything; add a route, query flag or page to the app; write a reusable tool; store the
payload or any screenshot in the repository.

**Resolves:** the owner's sign-off gate (G2, G5). The report records the verdict and the screenshot
paths; the final `docs(plan)` commit ticks this task's boxes.

---

## Dispatch

**Waves (code phases run in the `C:/ssw/t<N>` scratch worktrees at BASE `e1ea6008`, landings serial in
`C:/ssw/u7`):**

| Wave | Tasks (mode) | Files (pairwise disjoint) | Peak agents |
|---|---|---|---|
| 1 | 1 (`code`), 2 (`code`) | `plays.py`, `jobs.py`, `tests/test_plays.py`, `tests/test_jobs.py`, `README.md`, `heatmap-sequence.md` / `heatmap.js`, `tests/frontend/test_heatmap_pure_functions.py`, `DESIGN.md` | 2 implementers + 2 nested gate-runs |
| 2 | 3 (`code`, on Task 2's patch) | `heatmap.js`, `heatmap.css`, the frontend test file, `README.md`, `DESIGN.md` | 1 + 1 |
| 3 | 4 (`code`, on Tasks 1-3), 0 (prototype, on Tasks 1-3) | `_frontend_gate_stream.py`, `frontend_gate.py` / scratch only | 2 + 1 nested |

Task 3's README hunk (after line 161) does not overlap Task 1's (lines 156-157, 369, 487-488), and its
`DESIGN.md` hunk (Scrubber panel) does not overlap Task 2's (line 137); each landing starts with
`git apply --check --index <PATCH>`, and a failure there is NEEDS_CONTEXT, not a reason to use `-3`.

**Sign-off gate (G5):** no patch is landed before the owner approves Task 0's screenshots. Waves 1-3
produce patches only.

**Landing order (serial, after the owner's sign-off on Task 0):** 1, 2, 3, 4. Each landing: apply the
patch, re-run the focused tests, Section 4 entry (R1), the three `suite-*` shards and N (R3),
`doc_state_sync.py --fix --test-count N`, stage by name, `pre-commit`, `docsync-check`, commit (R4,
R5), tick that task's boxes. (Manual equivalent: run each command of the `Gates` block in
`constraints.md`, in its order, exactly as written there.) Landing 1 changes no `static/`, so no browser
gate; landings 2, 3 and 4 run `frontend-gate` through the lock.

**Gates per task:** all three `suite-*` shards, `pre-commit` and `docsync-check` for every commit;
`frontend-gate` for Tasks 2, 3, 4; `results-behavior` is not triggered by any task (no
`templates/results.html`, `static/js/results.js` or `scripts/dev/results_behavior_tests.py` change) and
runs once at the final head.

**Final gate run:** on the head after Task 4 run every command of the `Gates` block, including
`frontend-gate` and `results-behavior` (a `gate-runner` agent does this in our setup; you run the
commands). Then the `docs(plan): Record streamgraph bursts execution` commit (house style 89d8d887)
carrying the plan's Execution record and ticking Task 0's boxes; then the controller pushes and watches
`quality-gate`.

**Branch hygiene (context):** after #279 merges, this branch takes `main` in a reviewed merge commit,
never a rebase.

## Execution record

(Filled by the final `docs(plan)` commit: per task the landing SHA, N passed, the gate-run log
directories, the contrast numbers, the owner's sign-off date and any deviation.)
